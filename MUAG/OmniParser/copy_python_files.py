"""
Copy Python files for Florence-2
"""
from huggingface_hub import hf_hub_download
import shutil
from pathlib import Path

repo = 'microsoft/Florence-2-base-ft'
dest = Path('weights/icon_caption_florence')

files = [
    'processing_florence2.py',
    'configuration_florence2.py',
    'modeling_florence2.py',
]

print("Copie des fichiers Python pour Florence-2...")

for f in files:
    try:
        downloaded = hf_hub_download(repo_id=repo, filename=f)
        shutil.copy2(downloaded, dest / f)
        print(f"  OK: {f}")
    except Exception as e:
        print(f"  ERREUR {f}: {e}")

print("\nTermine!")
