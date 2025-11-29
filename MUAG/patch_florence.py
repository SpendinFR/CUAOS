"""
Patch modeling_florence2.py pour rendre flash_attn optionnel
"""
import os

path = 'OmniParser/weights/icon_caption_florence/modeling_florence2.py'

if not os.path.exists(path):
    print(f'SKIP: {path} not found')
    exit(0)

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Chercher les imports de flash_attn et les rendre optionnels
old_import = "from flash_attn"
new_import = "try:\n    from flash_attn"

if old_import in content and "try:\n    from flash_attn" not in content:
    # Remplacer tous les imports flash_attn par des imports optionnels
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if 'from flash_attn' in line and 'try:' not in lines[i-1] if i > 0 else True:
            # Ajouter try/except
            new_lines.append('try:')
            new_lines.append('    ' + line)
            new_lines.append('except ImportError:')
            new_lines.append('    pass  # flash_attn not available')
        else:
            new_lines.append(line)
        i += 1
    
    content = '\n'.join(new_lines)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK: modeling_florence2.py patché pour rendre flash_attn optionnel')
else:
    print('SKIP: déjà patché ou pas de flash_attn import')
