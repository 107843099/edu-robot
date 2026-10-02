"""Preprocess dataset: filter by duration and save preprocessed tensors."""

import os
import json
import torch
import torchaudio
import soundfile as sf
from PIL import Image
from tqdm import tqdm
from torchvision import transforms
from .localized_narratives import DataLoader
from ..config import IMAGE_SIZE, SAMPLE_RATE, N_MELS, N_FFT, HOP_LENGTH, N_FRAMES


def preprocess_split(root_dir, output_dir, split, max_duration=30.0):
    """Filter by duration and save preprocessed tensors."""
    # Setup transforms
    image_transform = transforms.Compose(
        [
            transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    mel_transform = torchaudio.transforms.MelSpectrogram(
        sample_rate=SAMPLE_RATE, n_mels=N_MELS, n_fft=N_FFT, hop_length=HOP_LENGTH
    )

    # Directories
    audio_dir = os.path.join(root_dir, "audio", f"coco_{split}")
    image_dir = os.path.join(root_dir, f"{split}2017")
    output_dir = os.path.join(output_dir, f"{split}_tensors")
    os.makedirs(output_dir, exist_ok=True)

    # Load and filter annotations
    loader = DataLoader(root_dir)
    annotations = list(loader.load_annotations(f"coco_{split}"))
    metadata = []

    for idx, ann in enumerate(tqdm(annotations, desc=f"Processing {split}")):
        try:
            # Check duration
            audio_path = os.path.join(audio_dir, os.path.basename(ann.voice_recording))
            if sf.info(audio_path).duration > max_duration:
                continue

            # Process image
            image_path = os.path.join(image_dir, f"{ann.image_id.zfill(12)}.jpg")
            with Image.open(image_path) as img:
                image = image_transform(img.convert("RGB"))

            # Process audio
            audio, sr = sf.read(audio_path)
            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)
            audio = torch.from_numpy(audio).float()
            if sr != SAMPLE_RATE:
                audio = torchaudio.functional.resample(audio, sr, SAMPLE_RATE)

            mel = mel_transform(audio)
            mel = torch.log(mel + 1e-9).unsqueeze(0)
            if mel.shape[-1] > N_FRAMES:
                mel = mel[..., :N_FRAMES]
            else:
                mel = torch.nn.functional.pad(mel, (0, N_FRAMES - mel.shape[-1]))

            # Save
            tensor_file = os.path.join(output_dir, f"{idx:08d}.pt")
            torch.save(
                {"image": image, "audio": mel, "caption": ann.caption}, tensor_file
            )
            metadata.append({"tensor_file": tensor_file, "caption": ann.caption})

        except Exception as e:
            print(f"\nError: {e}")

    # Save metadata
    with open(
        os.path.join(os.path.dirname(output_dir), f"{split}_metadata.json"), "w"
    ) as f:
        json.dump(metadata, f)

    print(
        f"Saved {len(metadata)}/{len(annotations)} samples ({len(metadata)/len(annotations)*100:.1f}%)"
    )
    return len(metadata)


def create_test_split(output_dir, test_size=1000, seed=0):
    """Split val into val/test after preprocessing."""
    import random
    import shutil

    val_metadata_path = os.path.join(output_dir, "val_metadata.json")
    with open(val_metadata_path, "r") as f:
        val_metadata = json.load(f)

    # Shuffle with seed
    random.seed(seed)
    indices = list(range(len(val_metadata)))
    random.shuffle(indices)

    # Split indices
    test_indices = set(indices[:test_size])

    test_metadata = []
    new_val_metadata = []

    for i, item in enumerate(val_metadata):
        if i in test_indices:
            test_metadata.append(item)
        else:
            new_val_metadata.append(item)

    # Create test directory and copy samples
    test_dir = os.path.join(output_dir, "test_tensors")
    os.makedirs(test_dir, exist_ok=True)

    for i, item in enumerate(tqdm(test_metadata, desc="Creating test split")):
        src = item["tensor_file"]
        dst = os.path.join(test_dir, f"{i:08d}.pt")
        shutil.copy2(src, dst)
        item["tensor_file"] = dst

    # Save metadata
    with open(val_metadata_path, "w") as f:
        json.dump(new_val_metadata, f)

    with open(os.path.join(output_dir, "test_metadata.json"), "w") as f:
        json.dump(test_metadata, f)

    return len(new_val_metadata), len(test_metadata)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--root_dir", default="data/coco")
    parser.add_argument("--output_dir", default="data/preprocessed_coco")
    parser.add_argument("--max_duration", type=float, default=30.0)
    parser.add_argument("--test_size", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    print(
        f"Preprocessing: {args.root_dir} -> {args.output_dir} (max {args.max_duration}s)"
    )
    train_count = preprocess_split(
        args.root_dir, args.output_dir, "train", args.max_duration
    )
    preprocess_split(args.root_dir, args.output_dir, "val", args.max_duration)

    val_count, test_count = create_test_split(
        args.output_dir, args.test_size, args.seed
    )

    print(
        f"\nTotal: {train_count + val_count + test_count} samples (train={train_count}, val={val_count}, test={test_count})"
    )


if __name__ == "__main__":
    main()
