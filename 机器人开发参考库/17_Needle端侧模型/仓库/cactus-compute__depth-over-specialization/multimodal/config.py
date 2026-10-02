"""Configuration and model registry for multimodal models."""

from transformers import AutoTokenizer
from .models.text_image import SharedTI, SeparateTI
from .models.text_audio import SharedTA, SeparateTA
from .models.image_audio import SharedIA, SeparateIA
from .models.text_image_audio import SharedTIA, SeparateTIA


# Constants
TOKENIZER = AutoTokenizer.from_pretrained("bert-base-uncased")
VOCAB_SIZE = len(TOKENIZER)
IMAGE_PATCH_SIZE = 16
AUDIO_PATCH_SIZE = (16, 25)
D_MODEL = 256
NHEAD = 8
D_HID = 1024
DROPOUT = 0.2
PROJECTION_DIM = 512
MAX_SEQ_LENGTH = 256
IMAGE_SIZE = 224
N_MELS = 64
N_FRAMES = 1500
SAMPLE_RATE = 16000
N_FFT = 400
HOP_LENGTH = 320
UNIT_SIZE = 2


def _build_kwargs(modalities: str, num_units: int) -> dict:
    """Build model kwargs based on modalities and number of units."""
    kwargs = {
        "d_model": D_MODEL,
        "nhead": NHEAD,
        "d_hid": D_HID,
        "nlayers": UNIT_SIZE * num_units,
        "dropout": DROPOUT,
        "projection_dim": PROJECTION_DIM,
    }

    if "t" in modalities:
        kwargs.update(
            {
                "vocab_size": VOCAB_SIZE,
                "max_seq_length": MAX_SEQ_LENGTH,
            }
        )

    if "i" in modalities:
        kwargs.update(
            {
                "patch_size": IMAGE_PATCH_SIZE,
                "image_size": IMAGE_SIZE,
            }
        )

    if "a" in modalities:
        kwargs.update(
            {
                "audio_patch_size": AUDIO_PATCH_SIZE,
                "n_mels": N_MELS,
                "n_frames": N_FRAMES,
            }
        )

    return kwargs


MODEL_REGISTRY = {}

_configs = [
    ("ti", SharedTI, SeparateTI),
    ("ta", SharedTA, SeparateTA),
    ("ia", SharedIA, SeparateIA),
    ("tia", SharedTIA, SeparateTIA),
]

for modalities, shared_cls, separate_cls in _configs:
    # Shared models: 1u, 2u, 3u
    for units in [1, 2, 3]:
        MODEL_REGISTRY[f"shared_{units}u_{modalities}"] = (
            shared_cls,
            _build_kwargs(modalities, units),
        )

    # Separate models: 2u for ti/ta/ia, 3u for tia
    sep_units = 3 if modalities == "tia" else 2
    MODEL_REGISTRY[f"separate_{sep_units}u_{modalities}"] = (
        separate_cls,
        _build_kwargs(modalities, 1),
    )


def create_model(model_name: str):
    """Create a model from registry."""
    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model: {model_name}")
    model_cls, kwargs = MODEL_REGISTRY[model_name]
    return model_cls(**kwargs)


if __name__ == "__main__":
    for model_name in sorted(MODEL_REGISTRY.keys()):
        model = create_model(model_name)

        total_params = sum(p.numel() for p in model.parameters())

        transformer_params = 0
        if hasattr(model, "transformer"):
            transformer_params += sum(p.numel() for p in model.transformer.parameters())
        if hasattr(model, "text_transformer"):
            transformer_params += sum(
                p.numel() for p in model.text_transformer.parameters()
            )
        if hasattr(model, "image_transformer"):
            transformer_params += sum(
                p.numel() for p in model.image_transformer.parameters()
            )
        if hasattr(model, "audio_transformer"):
            transformer_params += sum(
                p.numel() for p in model.audio_transformer.parameters()
            )

        print(f"{model_name:<20} {transformer_params:>20,} {total_params:>20,}")
