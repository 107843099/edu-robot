"""Training script for multimodal encoders."""

import argparse
import json
import math
import os
import random

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from .data.preprocessed_dataset import PreprocessedDataset
from .loss import ContrastiveLoss
from .config import create_model, TOKENIZER, MAX_SEQ_LENGTH


def set_seed(seed):
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def get_worker_init_fn(seed):
    def worker_init_fn(worker_id):
        worker_seed = seed + worker_id
        random.seed(worker_seed)
        torch.manual_seed(worker_seed)

    return worker_init_fn


def collate_fn(batch, tokenizer, max_length):
    result = {}

    if "image" in batch[0]:
        result["image"] = torch.stack([item["image"] for item in batch])

    if "audio" in batch[0]:
        result["audio"] = torch.stack([item["audio"] for item in batch])

    if "caption" in batch[0]:
        tokenized = tokenizer(
            [item["caption"] for item in batch],
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        result["input_ids"] = tokenized["input_ids"]
        result["attention_mask"] = tokenized["attention_mask"]

    return result


def compute_loss(model, batch, modalities, criterion, device):
    embeds = {}

    if "t" in modalities:
        embeds["t"] = model.encode_text(
            batch["input_ids"].to(device), batch["attention_mask"].to(device)
        )

    if "i" in modalities:
        embeds["i"] = model.encode_image(batch["image"].to(device))

    if "a" in modalities:
        embeds["a"] = model.encode_audio(batch["audio"].to(device))

    logit_scale = model.logit_scale.exp()

    if modalities != "tia":
        loss = criterion(embeds[modalities[0]], embeds[modalities[1]], logit_scale)
        return loss

    loss_ti = criterion(embeds["t"], embeds["i"], logit_scale)
    loss_ta = criterion(embeds["t"], embeds["a"], logit_scale)
    loss_ia = criterion(embeds["i"], embeds["a"], logit_scale)

    loss = (loss_ti + loss_ta + loss_ia) / 3

    individual_losses = {
        "loss_ti": loss_ti.item(),
        "loss_ta": loss_ta.item(),
        "loss_ia": loss_ia.item(),
    }

    return loss, individual_losses


def train_epoch(model, dataloader, modalities, criterion, optimizer, scheduler, device):
    model.train()
    total_loss = 0.0

    if modalities == "tia":
        individual_total_losses = {"loss_ti": 0.0, "loss_ta": 0.0, "loss_ia": 0.0}

    pbar = tqdm(dataloader, desc="Training")
    for batch in pbar:
        if modalities == "tia":
            loss, individual_losses = compute_loss(
                model, batch, modalities, criterion, device
            )
            for key, val in individual_losses.items():
                individual_total_losses[key] += val
            pbar.set_postfix(
                {
                    "loss": f"{loss.item():.4f}",
                    "loss_ti": f"{individual_losses['loss_ti']:.4f}",
                    "loss_ta": f"{individual_losses['loss_ta']:.4f}",
                    "loss_ia": f"{individual_losses['loss_ia']:.4f}",
                }
            )
        else:
            loss = compute_loss(model, batch, modalities, criterion, device)
            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()

        with torch.no_grad():
            model.logit_scale.clamp_(0, math.log(100))

        total_loss += loss.item()

    avg_loss = total_loss / len(dataloader)

    if modalities == "tia":
        avg_individual = {
            k: v / len(dataloader) for k, v in individual_total_losses.items()
        }
        return avg_loss, avg_individual

    return avg_loss


def validate(model, dataloader, modalities, criterion, device):
    model.eval()
    total_loss = 0.0

    if modalities == "tia":
        individual_total_losses = {"loss_ti": 0.0, "loss_ta": 0.0, "loss_ia": 0.0}

    pbar = tqdm(dataloader, desc="Validation")
    with torch.no_grad():
        for batch in pbar:
            if modalities == "tia":
                loss, individual_losses = compute_loss(
                    model, batch, modalities, criterion, device
                )
                for key, val in individual_losses.items():
                    individual_total_losses[key] += val
            else:
                loss = compute_loss(model, batch, modalities, criterion, device)

            total_loss += loss.item()
            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

    avg_loss = total_loss / len(dataloader)

    if modalities == "tia":
        avg_individual = {
            k: v / len(dataloader) for k, v in individual_total_losses.items()
        }
        return avg_loss, avg_individual

    return avg_loss


def main(args):
    set_seed(args.seed)

    if args.wandb:
        import wandb

        wandb.init(
            project=args.wandb_project,
            name=args.wandb_run_name,
            config=vars(args),
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    modalities = args.model.split("_")[-1]

    print(f"Device: {device}")
    print(f"Model: {args.model}")

    train_dataset = PreprocessedDataset(root_dir=args.data_dir, split="train")
    val_dataset = PreprocessedDataset(root_dir=args.data_dir, split="val")

    print(f"Train samples: {len(train_dataset)}")
    print(f"Val samples: {len(val_dataset)}")

    loader_kwargs = {
        "batch_size": args.batch_size,
        "num_workers": args.num_workers,
        "collate_fn": lambda b: collate_fn(b, TOKENIZER, MAX_SEQ_LENGTH),
        "pin_memory": True,
        "persistent_workers": args.num_workers > 0,
        "prefetch_factor": 4 if args.num_workers > 0 else None,
        "worker_init_fn": get_worker_init_fn(args.seed),
    }

    train_loader = DataLoader(train_dataset, shuffle=True, **loader_kwargs)
    val_loader = DataLoader(val_dataset, shuffle=False, **loader_kwargs)

    model = create_model(args.model).to(device)
    criterion = ContrastiveLoss()
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=args.lr, weight_decay=args.weight_decay
    )

    total_steps = len(train_loader) * args.epochs
    warmup_steps = int(total_steps * args.warmup_ratio)

    warmup_scheduler = torch.optim.lr_scheduler.LinearLR(
        optimizer, start_factor=0.01, end_factor=1.0, total_iters=warmup_steps
    )
    cosine_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=total_steps - warmup_steps
    )
    scheduler = torch.optim.lr_scheduler.SequentialLR(
        optimizer,
        schedulers=[warmup_scheduler, cosine_scheduler],
        milestones=[warmup_steps],
    )

    print(f"Total training steps: {total_steps} (warmup: {warmup_steps})")

    run_dir = os.path.join(args.output_dir, args.model)
    checkpoint_dir = os.path.join(run_dir, "checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)

    print(f"Output directory: {run_dir}\n")

    with open(os.path.join(run_dir, "config.json"), "w") as f:
        json.dump(vars(args), f, indent=2)

    best_val_loss = float("inf")
    history = []

    for epoch in range(args.epochs):
        print(f"\nEpoch {epoch + 1}/{args.epochs}")

        if modalities == "tia":
            train_loss, train_individual = train_epoch(
                model, train_loader, modalities, criterion, optimizer, scheduler, device
            )
            val_loss, val_individual = validate(
                model, val_loader, modalities, criterion, device
            )

            print(f"Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
            print(
                f"  Train: ti={train_individual['loss_ti']:.4f}, ta={train_individual['loss_ta']:.4f}, ia={train_individual['loss_ia']:.4f}"
            )
            print(
                f"  Val:   ti={val_individual['loss_ti']:.4f}, ta={val_individual['loss_ta']:.4f}, ia={val_individual['loss_ia']:.4f}"
            )

            history_entry = {
                "epoch": epoch + 1,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "lr": optimizer.param_groups[0]["lr"],
            }
            for key, val in train_individual.items():
                history_entry[f"train_{key}"] = val
            for key, val in val_individual.items():
                history_entry[f"val_{key}"] = val

        else:
            train_loss = train_epoch(
                model, train_loader, modalities, criterion, optimizer, scheduler, device
            )
            val_loss = validate(model, val_loader, modalities, criterion, device)

            print(f"Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")

            history_entry = {
                "epoch": epoch + 1,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "lr": optimizer.param_groups[0]["lr"],
            }

        history.append(history_entry)

        if args.wandb:
            wandb.log(history_entry)

        with open(os.path.join(run_dir, "history.json"), "w") as f:
            json.dump(history, f, indent=2)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(
                model.state_dict(), os.path.join(checkpoint_dir, "best_model.pt")
            )
            print(f"Saved best model (val_loss: {best_val_loss:.4f})")

        torch.save(model.state_dict(), os.path.join(checkpoint_dir, "last_model.pt"))

    print(f"\nTraining complete! Best val loss: {best_val_loss:.4f}")
    print(f"Checkpoints saved to: {checkpoint_dir}")

    if args.wandb:
        wandb.finish()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--batch_size", type=int, default=256)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight_decay", type=float, default=0.1)
    parser.add_argument("--warmup_ratio", type=float, default=0.1)
    parser.add_argument("--data_dir", type=str, default="data/preprocessed_coco")
    parser.add_argument("--num_workers", type=int, default=8)
    parser.add_argument("--wandb", action="store_true")
    parser.add_argument("--wandb_project", type=str, default="multimodal-research")
    parser.add_argument("--wandb_run_name", type=str, default=None)
    parser.add_argument("--output_dir", type=str, default="runs")
    parser.add_argument("--seed", type=int, default=0)

    main(parser.parse_args())
