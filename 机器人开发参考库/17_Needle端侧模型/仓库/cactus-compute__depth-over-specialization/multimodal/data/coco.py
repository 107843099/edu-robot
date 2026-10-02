"""Download COCO 2017 images and Localized Narratives audio."""

import os
import zipfile
import wget
from .localized_narratives import DataLoader


def download_coco():
    """Download and extract COCO 2017 train/val images."""
    output_dir = "data/coco"
    urls = {
        "train2017": "http://images.cocodataset.org/zips/train2017.zip",
        "val2017": "http://images.cocodataset.org/zips/val2017.zip",
    }

    os.makedirs(output_dir, exist_ok=True)

    for split, url in urls.items():
        zip_path = f"{split}.zip"
        extract_path = os.path.join(output_dir, split)

        if os.path.exists(extract_path) and os.listdir(extract_path):
            print(f"Already exists: {split}")
            continue

        if os.path.exists(zip_path):
            print(f"Zip already exists: {split}")
        else:
            print(f"Downloading {split}...")
            wget.download(url, zip_path)
            print()

        print(f"Extracting {split}...")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(output_dir)

        os.remove(zip_path)


def download_audio():
    """Download Localized Narratives audio files."""
    loader = DataLoader("data/coco")

    for split in ["coco_train", "coco_val"]:
        print(f"Downloading audio for {split}...")
        for annotation in loader.load_annotations(split):
            audio_dir = os.path.join("data/coco", "audio", split)
            os.makedirs(audio_dir, exist_ok=True)

            audio_filename = os.path.basename(annotation.voice_recording)
            audio_path = os.path.join(audio_dir, audio_filename)

            if not os.path.exists(audio_path):
                wget.download(annotation.voice_recording_url, audio_path)
            else:
                print(f"Already exists: {audio_filename}")


if __name__ == "__main__":
    download_coco()

    loader = DataLoader("data/coco")
    loader.download_annotations("coco_train")
    loader.download_annotations("coco_val")

    download_audio()
