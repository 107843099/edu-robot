# Multimodal Encoder

Contrastive learning framework for training multimodal encoders that align embeddings across text, image, and audio modalities using Localized Narratives.

## Features

- **4 Modality Combinations**: Text-Image (TI), Text-Audio (TA), Image-Audio (IA), Text-Image-Audio (TIA)
- **2 Architecture Types**: Shared encoder vs. Separate encoders
- **Model Sizes**: 1U, 2U, 3U (where U = 2 transformer layers)
- **Localized Narratives**: Multimodal dataset with images, audio narrations, and captions

## Setup

```bash
source ./setup.sh
```

## Dataset Preparation

Download COCO 2017 images and Localized Narratives annotations:

```bash
python -m multimodal.data.coco
python -m multimodal.data.preprocess
```

This filters samples by duration (max 30s) and creates train/val/test splits:
- **Train**: 92,987 samples
- **Val**: 5,088 samples
- **Test**: 1,000 samples

## Training

Train models:

```bash
./train.sh
```

## Evaluation

Evaluate models on test split:

```bash
./evaluate.sh
```

## Model Configs

**Unit**: 2 transformer layers

**Dual-Modality Architectures (TI/TA/IA):**

```
┌─ Shared 1U (TI/TA/IA) ────────────────────────┐
│  Modality A ─> Embed A ─┐         ┌─> Proj A  │
│  Modality B ─> Embed B ─┴─> Unit ─┴─> Proj B  │
└───────────────────────────────────────────────┘

┌─ Shared 2U (TI/TA/IA) ───────────────────────────────┐
│  Modality A ─> Embed A ─┐                 ┌─> Proj A │
│  Modality B ─> Embed B ─┴─> Unit ─> Unit ─┴─> Proj B │
└──────────────────────────────────────────────────────┘

┌─ Shared 3U (TI/TA/IA) ───────────────────────────────────────┐
│  Modality A ─> Embed A ─┐                         ┌─> Proj A │
│  Modality B ─> Embed B ─┴─> Unit ─> Unit ─> Unit ─┴─> Proj B │
└──────────────────────────────────────────────────────────────┘

┌─ Separate 2U (TI/TA/IA) ───────────────────┐
│  Modality A ─> Embed A ─> Unit A ─> Proj A │
│  Modality B ─> Embed B ─> Unit B ─> Proj B │
└────────────────────────────────────────────┘
```

**Tri-Modality Architectures (TIA):**

```
┌─ Shared 1U (TIA) ───────────────────────┐
│  Text  ─> Embed T ─┐         ┌─> Proj T │
│  Image ─> Embed I ─┼─> Unit ─┼─> Proj I │
│  Audio ─> Embed A ─┘         └─> Proj A │
└─────────────────────────────────────────┘

┌─ Shared 2U (TIA) ───────────────────────────────┐
│  Text  ─> Embed T ─┐                 ┌─> Proj T │
│  Image ─> Embed I ─┼─> Unit ─> Unit ─┼─> Proj I │
│  Audio ─> Embed A ─┘                 └─> Proj A │
└─────────────────────────────────────────────────┘

┌─ Shared 3U (TIA) ───────────────────────────────────────┐
│  Text  ─> Embed T ─┐                         ┌─> Proj T │
│  Image ─> Embed I ─┼─> Unit ─> Unit ─> Unit ─┼─> Proj I │
│  Audio ─> Embed A ─┘                         └─> Proj A │
└─────────────────────────────────────────────────────────┘

┌─ Separate 3U (TIA) ───────────────────┐
│  Text  ─> Embed T ─> Unit T ─> Proj T │
│  Image ─> Embed I ─> Unit I ─> Proj I │
│  Audio ─> Embed A ─> Unit A ─> Proj A │
└───────────────────────────────────────┘
```

Available models (run `python -m multimodal.config` to print parameter counts):

| Model | Modality | Type | Transformer Params | Total Params | Units |
|-------|----------|------|-------------------|--------------|-------|
| `shared_1u_ti` | Text-Image | Shared | 2.1M | 10.4M | 1 |
| `shared_2u_ti` | Text-Image | Shared | 4.2M | 12.5M | 2 |
| `shared_3u_ti` | Text-Image | Shared | 6.3M | 14.6M | 3 |
| `separate_2u_ti` | Text-Image | Separate | 4.2M | 12.5M | 1+1 |
| `shared_1u_ta` | Text-Audio | Shared | 2.1M | 10.3M | 1 |
| `shared_2u_ta` | Text-Audio | Shared | 4.2M | 12.4M | 2 |
| `shared_3u_ta` | Text-Audio | Shared | 6.3M | 14.5M | 3 |
| `separate_2u_ta` | Text-Audio | Separate | 4.2M | 12.4M | 1+1 |
| `shared_1u_ia` | Image-Audio | Shared | 2.1M | 2.7M | 1 |
| `shared_2u_ia` | Image-Audio | Shared | 4.2M | 4.8M | 2 |
| `shared_3u_ia` | Image-Audio | Shared | 6.3M | 6.9M | 3 |
| `separate_2u_ia` | Image-Audio | Separate | 4.2M | 4.8M | 1+1 |
| `shared_1u_tia` | Text-Image-Audio | Shared | 2.1M | 10.6M | 1 |
| `shared_2u_tia` | Text-Image-Audio | Shared | 4.2M | 12.7M | 2 |
| `shared_3u_tia` | Text-Image-Audio | Shared | 6.3M | 14.8M | 3 |
| `separate_3u_tia` | Text-Image-Audio | Separate | 6.3M | 14.8M | 1+1+1 |
