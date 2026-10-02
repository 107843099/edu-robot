"""Localized Narratives dataset with image, audio, and text."""

import os
import torch
import torchaudio
from torch.utils.data import Dataset
from PIL import Image
import soundfile as sf
from torchvision import transforms
from .localized_narratives import DataLoader


class LocalizedNarrativesDataset(Dataset):
    """Returns preprocessed images, mel spectrograms, and raw captions based on modalities."""

    def __init__(
        self,
        root_dir,
        split,
        modalities="tia",
        image_size=None,
        sample_rate=None,
        n_mels=None,
        n_fft=None,
        hop_length=None,
        max_length=None,
    ):
        self.root_dir = root_dir
        self.split = split
        self.modalities = modalities

        if "i" in modalities:
            self.image_dir = os.path.join(root_dir, f"{split}2017")
            self.transform = transforms.Compose(
                [
                    transforms.Resize((image_size, image_size)),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                    ),
                ]
            )

        if "a" in modalities:
            self.audio_dir = os.path.join(root_dir, "audio", f"coco_{split}")
            self.sample_rate = sample_rate
            self.max_length = max_length
            self.mel_transform = torchaudio.transforms.MelSpectrogram(
                sample_rate=sample_rate,
                n_mels=n_mels,
                n_fft=n_fft,
                hop_length=hop_length,
            )

        loader = DataLoader(root_dir)
        self.annotations = []
        for ann in loader.load_annotations(f"coco_{split}"):
            self.annotations.append(
                {
                    "image_id": ann.image_id,
                    "voice_recording": ann.voice_recording,
                    "caption": ann.caption,
                }
            )

    def __len__(self):
        return len(self.annotations)

    def __getitem__(self, idx):
        annotation = self.annotations[idx]
        result = {}

        if "i" in self.modalities:
            image_path = os.path.join(
                self.image_dir, f"{annotation['image_id'].zfill(12)}.jpg"
            )
            with Image.open(image_path) as img:
                image = img.convert("RGB")
                image = self.transform(image)
            result["image"] = image

        if "a" in self.modalities:
            audio_filename = os.path.basename(annotation["voice_recording"])
            audio_path = os.path.join(self.audio_dir, audio_filename)
            audio, sr = sf.read(audio_path)

            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)

            audio = torch.from_numpy(audio).float()

            if sr != self.sample_rate:
                audio = torchaudio.functional.resample(audio, sr, self.sample_rate)

            mel_spec = self.mel_transform(audio)
            mel_spec = torch.log(mel_spec + 1e-9)
            mel_spec = mel_spec.unsqueeze(0)

            if mel_spec.shape[-1] > self.max_length:
                mel_spec = mel_spec[..., : self.max_length]
            else:
                mel_spec = torch.nn.functional.pad(
                    mel_spec, (0, self.max_length - mel_spec.shape[-1])
                )
            result["audio"] = mel_spec

        if "t" in self.modalities:
            result["caption"] = annotation["caption"]

        return result
