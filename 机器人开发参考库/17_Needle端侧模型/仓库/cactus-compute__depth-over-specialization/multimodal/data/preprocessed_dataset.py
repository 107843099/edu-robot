"""Dataset for loading preprocessed tensors."""

import json
import torch
from torch.utils.data import Dataset


class PreprocessedDataset(Dataset):
    """Load preprocessed tensors directly"""

    def __init__(self, root_dir, split):
        self.root_dir = root_dir
        self.split = split

        metadata_file = f"{root_dir}/{split}_metadata.json"
        with open(metadata_file, "r") as f:
            self.metadata = json.load(f)

    def __len__(self):
        return len(self.metadata)

    def __getitem__(self, idx):
        meta = self.metadata[idx]
        data = torch.load(meta["tensor_file"])
        return {
            "image": data["image"],
            "audio": data["audio"],
            "caption": data["caption"],
        }
