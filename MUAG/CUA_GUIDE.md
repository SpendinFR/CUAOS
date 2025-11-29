# 🤖 Agent CUA (Computer Use Agent) - Guide Complet

## 🎯 Qu'est-ce que l'Agent CUA?

L'Agent CUA est un agent **complètement autonome** qui peut accomplir **n'importe quelle tâche** sur votre ordinateur en utilisant la vision et l'action.

**Pas de modules spécifiques** pour Gmail, Amazon, etc. - L'agent s'adapte à TOUT!

## 🔄 Fonctionnement - Boucle Vision-Action

```
1. 👁️  VOIR       → Screenshot de l'écran
2. 🧠  COMPRENDRE  → VLM analyse l'image ("Chrome ouvert, barre recherche visible")
3. 💭  PLANIFIER   → LLM décide la prochaine action ("Cliquer dans la barre")
4. 🎬  AGIR        → PyAutoGUI exécute l'action
5. ✅  VÉRIFIER    → VLM vérifie si la sous-tâche est accomplie
6. 🔁  RÉPÉTER     → Jusqu'à tâche principale terminée
```

## 📋 Exemples d'Utilisation

### Exemple 1: Tâche Simple
```
Tâche: "Ouvre le bloc-notes"

Étape 1: VLM voit le bureau Windows
→ LLM: "Aller au menu démarrer"
→ PyAutoGUI: Clique sur bouton Windows

Étape 2: VLM voit le menu ouvert
→ LLM: "Chercher notepad"
→ PyAutoGUI: Tape "notepad"

Étape 3: VLM voit notepad dans les résultats
→ LLM: "Cliquer sur notepad"
→ PyAutoGUI: Clique

✅ Terminé!
```

### Exemple 2: Shopping Amazon
```
Tâche: "Commande des Nike Jordan à moins de 100€ notées 4.7+"

Étape 1: VLM voit le bureau
→ LLM: "Ouvrir Chrome"
→ PyAutoGUI: launch_app("chrome")

Étape 2: VLM voit Chrome ouvert
→ LLM: "Aller sur amazon.fr"
→ PyAutoGUI: type_text("amazon.fr") + Enter

Étape 3: VLM voit Amazon chargé
→ LLM: "Chercher Nike Jordan"
→ PyAutoGUI: click(barre_recherche) + type_text("Nike Jordan")

Étape 4: VLM voit les résultats
→ LLM: "Filtrer par prix <100€"
→ PyAutoGUI: click(filtre_prix)

Étape 5: VLM voit les résultats filtrés
→ LLM: "Vérifier les notes et choisir"
→ PyAutoGUI: click(produit_4.7_stars)

... et ainsi de suite jusqu'à l'achat!
```

### Exemple 3: Email Gmail
```
Tâche: "Envoie un email à john@example.com avec objet 'Réunion' et texte 'RDV demain'"

Étape 1: Ouvrir Gmail
Étape 2: Cliquer "Nouveau message"
Étape 3: Remplir destinataire
Étape 4: Remplir objet
Étape 5: Remplir message
Étape 6: Cliquer "Envoyer"
✅ Email envoyé!
```

## 🚀 Installation et Configuration

### 1. Modèle VLM (Vision-Language Model)

L'agent CUA a besoin d'un modèle VLM pour "voir" l'écran:

```bash
# Option 1: Qwen2-VL (Recommandé, 7GB)
ollama pull qwen2-vl:7b

# Option 2: LLaVA (Alternative, 4GB)
ollama pull llava:7b

# Option 3: Qwen2-VL 2B (Plus léger, 2GB)
ollama pull qwen2-vl:2b
```

### 2. Configuration dans config.py

```python
# Modèle VLM à utiliser
VLM_MODEL = "qwen2-vl:7b"  # ou "llava:7b"

# Paramètres CUA
CUA_MAX_STEPS = 50  # Limite de sécurité
CUA_STEP_DELAY = 1  # Délai entre les étapes (secondes)
```

## 💻 Utilisation

### Mode 1: Via l'Agent Vocal Principal

```bash
python main.py
```

Puis dites simplement votre tâche complexe:
- "Commande des Nike Jordan sur Amazon à moins de 100 euros"
- "Trouve-moi un vol Paris-Londres pour demain"
- "Envoie un email à Marie avec le sujet Bonjour"

L'agent détectera automatiquement que c'est une tâche complexe et activera le CUA!

### Mode 2: Test Direct (Script de Test)

```bash
# Test interactif
python tests/test_cua.py

# Test CLI avec tâche personnalisée
python tests/test_cua.py "Cherche la météo à Paris sur Google"
```

### Mode 3: Utilisation Programmatique

```python
from actions.cua_agent import CUAAgent

agent = CUAAgent()
result = agent.execute_task(
    "Commande des écouteurs sans fil sur Amazon",
    max_steps=30
)

print(f"Terminé: {result['completed']}")
print(f"Étapes: {result['steps']}")
print(agent.get_summary())
```

## 🎛️ Actions Disponibles

L'agent CUA peut utiliser toutes ces actions:

| Action | Description | Exemple |
|--------|-------------|---------|
| `click(x, y)` | Cliquer à des coordonnées | `click(500, 300)` |
| `type_text("...")` | Taper du texte | `type_text("amazon.fr")` |
| `press_key("...")` | Appuyer sur une touche | `press_key("Enter")` |
| `hotkey("...", "...")` | Raccourci clavier | `hotkey("ctrl", "c")` |
| `launch_app("...")` | Lancer une application | `launch_app("chrome")` |
| `open_url("...")` | Ouvrir une URL | `open_url("google.com")` |
| `scroll(clicks)` | Scroll (+ ou -) | `scroll(-5)` |
| `wait(seconds)` | Attendre | `wait(2)` |

## 🔧 Détection Automatique des Tâches CUA

L'`executeur.py` détecte automatiquement quand utiliser CUA:

**Mots-clés déclencheurs**:
- `commande`, `achète`, `acheter`
- `réserve`, `réserver`
- `envoie un email`, `cherche sur`
- `remplis`, `formulaire`
- `amazon`, `gmail`, `facebook`, etc.

**Exemple**:
```python
# Ceci déclenchera CUA:
"Commande des Nike sur Amazon"

# Ceci utilisera une commande simple:
"Ouvre Chrome"
```

## 📊 Monitoring et Debugging

### Logs Détaillés

L'agent CUA affiche des logs complets:

```
🎯 Tâche CUA: Cherche la météo à Paris sur Google
============================================================

============================================================
🔄 Étape 1/30
============================================================

👁️ Vision: Bureau Windows avec icônes visibles, barre des tâches en bas
🧠 Action planifiée: {'action': 'launch_app', 'params': {'app': 'chrome'}}
  💭 Raison: Ouvrir Chrome pour aller sur Google
  🎬 Exécution: launch_app({'app': 'chrome'})
✅ Résultat: Application lancée: chrome
```

### Historique des Actions

```python
agent = CUAAgent()
result = agent.execute_task("Ma tâche")

# Voir l'historique
for i, action in enumerate(agent.action_history):
    print(f"Étape {i+1}:")
    print(f"  Vision: {action['screen_description']}")
    print(f"  Action: {action['action']}")
    print(f"  Résultat: {action['result']}")
```

### Screenshots Automatiques

Tous les screenshots sont sauvegardés dans `data/screenshots/`:
- `cua_step_1.png`
- `cua_step_2.png`
- etc.

Utile pour débugger et comprendre ce que voit l'agent!

## ⚠️ Limitations et Points d'Attention

### Limitations Actuelles

1. **VLM Requis**: Sans VLM (qwen2-vl, llava), l'agent fonctionne en mode limité
2. **Coordonnées Approximatives**: L'agent devine les coordonnées, peut nécessiter ajustements
3. **Sites Dynamiques**: Les sites avec CAPTCHA ou vérifications complexes peuvent poser problème
4. **Vitesse**: Chaque étape prend 2-5 secondes (vision + planning)

### Sécurité

- ✅ **Limite d'étapes**: Maximum 50 étapes par défaut (configurable)
- ✅ **Screenshots sauvegardés**: Audit complet possible
- ⚠️ **Pas de confirmation automatique**: Pour achats, vérifiez toujours!

### Performance

**RAM**: 8GB minimum, 16GB recommandé (VLM + LLM)
**GPU**: Optionnel mais accélère significativement
**Temps moyen**:
- Tâche simple (3-5 étapes): ~15-30 secondes
- Tâche moyenne (10-15 étapes): ~1-2 minutes
- Tâche complexe (20-30 étapes): ~3-5 minutes

## 🎓 Conseils d'Utilisation

### ✅ Bonnes Pratiques

1. **Soyez Précis**: "Cherche des Nike Jordan noires taille 42" plutôt que "Cherche des chaussures"
2. **Décomposez**: Pour tâches très complexes, divisez en sous-tâches
3. **Vérifiez**: Regardez les screenshots pour comprendre ce que voit l'agent
4. **Patience**: Laissez l'agent faire, ne cliquez pas pendant l'exécution!

### ❌ À Éviter

1. **Tâches Impossibles**: "Deviens riche" 😄
2. **Tâches Ambiguës**: "Fais quelque chose d'intéressant"
3. **Interruptions**: Ne bougez pas la souris pendant l'exécution
4. **CAPTCHA**: L'agent ne peut pas résoudre les CAPTCHA (pour l'instant)

## 🚧 Roadmap

### Version Actuelle (v1.0)
- ✅ Boucle vision-action autonome
- ✅ Support VLM (Qwen2-VL, LLaVA)
- ✅ Actions PyAutoGUI complètes
- ✅ Détection auto de tâches complexes

### Prochaines Versions

**v1.1** (Court terme):
- [ ] Amélioration précision coordonnées (Object Detection)
- [ ] Cache des patterns visuels fréquents
- [ ] Mode "apprentissage" pour sites spécifiques

**v1.2** (Moyen terme):
- [ ] Support multi-fenêtres
- [ ] Gestion des pop-ups et alertes
- [ ] Mode "surveillance" (attend que quelque chose apparaisse)

**v2.0** (Long terme):
- [ ] Résolution de CAPTCHA (via services externes)
- [ ] Mode collaboratif (plusieurs agents)
- [ ] API REST pour contrôle externe

## 📚 Exemples Avancés

### Exemple Complet: Réservation de Vol

```python
from actions.cua_agent import CUAAgent

agent = CUAAgent()

result = agent.execute_task("""
Trouve-moi un vol:
- Départ: Paris CDG
- Arrivée: Londres Heathrow
- Date: 15 janvier 2025
- Prix max: 150€
- Compagnie: Air France ou British Airways

Ne réserve pas, juste trouve les options.
""", max_steps=40)

if result['completed']:
    print("✅ Recherche terminée!")
    print(agent.get_summary())
else:
    print("⚠️ Recherche incomplète, vérifiez les screenshots")
```

## 🆘 Troubleshooting

### Problème: "VLM non disponible"

```bash
# Installer un modèle VLM
ollama pull qwen2-vl:7b

# Vérifier qu'il fonctionne
ollama run qwen2-vl:7b "Décris cette image" < test.png
```

### Problème: L'agent clique au mauvais endroit

- Les coordonnées sont approximatives sans Object Detection
- Solution: Utiliser des modèles VLM plus précis (qwen2-vl:14b si GPU)
- Ou: Ajouter des delays plus longs pour laisser la page charger

### Problème: Tâche ne se termine jamais

- Vérifier la limite `max_steps`
- Peut-être la tâche est trop complexe - décomposez-la
- Regarder les screenshots pour voir où ça bloque

---

## 🎉 Conclusion

L'agent CUA transforme MUAG en un véritable **Computer Use Agent** autonome capable de faire TOUT ce qu'un humain peut faire sur un ordinateur!

Pas de modules spécifiques, juste la **vision + intelligence + action** = Autonomie complète!

**Limites actuelles**: Sites avec CAPTCHA, précision coordonnées
**Potentiel**: Infini! Toute tâche visuelle est possible! 🚀
