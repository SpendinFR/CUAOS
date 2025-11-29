"""Script de restauration automatique de cua_agent.py depuis son backup"""
import shutil

# Restaurer depuis backup
src = r"c:\Users\wabad\Downloads\MUAPPG\MUAG\actions\cua_agent.py.backup"
dst = r"c:\Users\wabad\Downloads\MUAPPG\MUAG\actions\cua_agent.py"

shutil.copy2(src, dst)
print(f"✅ Fichier restauré avec succès de {src} vers {dst}")
