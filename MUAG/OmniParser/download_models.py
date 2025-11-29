"""
Download OmniParser models from HuggingFace
"""
from huggingface_hub import hf_hub_download
from pathlib import Path

print("Telechargement des modeles OmniParser...")
print("=" * 60)

weights_dir = Path("weights")
weights_dir.mkdir(exist_ok=True)

repo_id = "microsoft/OmniParser-v2.0"

# Liste des fichiers a telecharger
files = [
    "icon_detect/train_args.yaml",
    "icon_detect/model.pt",
    "icon_detect/model.yaml",
    "icon_caption/config.json",
    "icon_caption/generation_config.json",
    "icon_caption/model.safetensors",
]

print(f"\nTelechargement de {len(files)} fichiers depuis {repo_id}...\n")

for file_path in files:
    print(f"  Telechargement: {file_path}")
    try:
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=file_path,
            local_dir=str(weights_dir),
            local_dir_use_symlinks=False
        )
        print(f"  OK: {file_path}")
    except Exception as e:
        print(f"  ERREUR: {e}")

print("\n" + "=" * 60)
print("Telechargement termine!")
print("\nRenommage de icon_caption -> icon_caption_florence...")

# Renommer icon_caption -> icon_caption_florence
import shutil
caption_dir = weights_dir / "icon_caption"
florence_dir = weights_dir / "icon_caption_florence"

if caption_dir.exists():
    if florence_dir.exists():
        shutil.rmtree(florence_dir)
    shutil.move(str(caption_dir), str(florence_dir))
    print(f"OK: Renomme {caption_dir} -> {florence_dir}")
else:
    print(f"ATTENTION: Dossier {caption_dir} non trouve")

print("\n" + "=" * 60)
print("Installation OmniParser complete!")
print("=" * 60)
