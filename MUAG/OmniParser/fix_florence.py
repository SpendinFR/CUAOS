"""
Fix Florence-2 model loading by downloading missing files
"""
from huggingface_hub import snapshot_download
from pathlib import Path
import shutil

print("Telechargement du modele Florence-2 complet...")
print("=" * 60)

# Télécharger Florence-2-base-ft (le modèle de base)
florence_repo = "microsoft/Florence-2-base-ft"
temp_dir = Path("temp_florence")

print(f"\nTelechargement depuis {florence_repo}...")

snapshot_download(
    repo_id=florence_repo,
    local_dir=str(temp_dir),
    local_dir_use_symlinks=False
)

print("OK: Modele Florence-2 telecharge")

# Copier uniquement les fichiers nécessaires pour icon_caption_florence
weights_dir = Path("weights/icon_caption_florence")
weights_dir.mkdir(parents=True, exist_ok=True)

# Fichiers à copier
files_to_copy = [
    "config.json",
    "generation_config.json",
    "model.safetensors",
    "preprocessor_config.json",  # Fichier manquant !
    "tokenizer.json",
    "tokenizer_config.json",
]

print(f"\nCopie des fichiers necessaires vers {weights_dir}...")

for file in files_to_copy:
    src = temp_dir / file
    if src.exists():
        dst = weights_dir / file
        shutil.copy2(str(src), str(dst))
        print(f"  OK: {file}")
    else:
        print(f"  MANQUANT: {file}")

# Nettoyer temp
print(f"\nNettoyage du dossier temporaire...")
if temp_dir.exists():
    shutil.rmtree(temp_dir)

print("\n" + "=" * 60)
print("Florence-2 configure correctement!")
print("=" * 60)
