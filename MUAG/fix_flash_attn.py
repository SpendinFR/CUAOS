"""
Script pour désactiver flash_attn et ajouter pass dans le bloc if
"""
path = 'OmniParser/weights/icon_caption_florence/modeling_florence2.py'

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Détecter if is_flash_attn_2_available():
    if 'if is_flash_attn_2_available():' in line:
        new_lines.append(line)
        # Regarder les lignes suivantes
        j = i + 1
        has_content = False
        while j < len(lines) and (lines[j].startswith('    ') or lines[j].strip() == ''):
            if lines[j].strip() and not lines[j].strip().startswith('#'):
                has_content = True
                break
            j += 1
        
        # Si pas de contenu actif, ajouter pass
        if not has_content:
            new_lines.append('    pass  # flash_attn desactive\n')
            print(f"Ligne {i+1}: Ajoute 'pass' apres if is_flash_attn_2_available()")
    else:
        new_lines.append(line)
    
    i += 1

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"OK: {path} mis a jour")
