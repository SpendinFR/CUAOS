https://github.com/user-attachments/assets/5e7d7c9a-112f-4fba-ae3f-043e9634f55b


# Evolutive AGI — Architecture, Operation & Getting Started Guide

> **Vision** — This repository implements a **simulation of an evolving, quasi‑conscious entity**: an autonomous AI that perceives, feels (PAD), sets **goals** (evolve, survive, learn), self‑assesses, **self‑improves** continuously, and maintains a coherent **identity**. It alternates **work** and **flânerie** (reflection), writes a **phenomenal journal** (subjective experience), and links perception → cognition → action → feedback → learning in a closed loop.

---

## Architecture Mind Map

```
┌───────────────────────────────────────────────────────────────────────────┐
│                          Orchestrator (conductor)                         │
│   - Pipeline ACT → FEEDBACK → LEARN → UPDATE                              │
│   - Trigger bus + LightScheduler + JobManager                             │
│   - ModeManager + PhenomenalKernel (work / flânerie)                      │
│   - Decision Journal + ReasoningLedger + Timeline                         │
│   - LLM integration (optional)                                            │
└───────────────┬───────────────────────────────────────────────────────────┘
                │
     ┌──────────▼──────────┐     ┌───────────────┐      ┌───────────────────┐
     │     Perception I/O  │     │   Memory Hub  │      │     Action I/F    │
     │ (events, sensory)   │◀───▶│ working/epis. │◀───▶ │ (actions, effects)│
     └───────┬─────────────┘     │ semantic/RAG  │      └─────────┬─────────┘
             │                   │ autobiography │                │
             │                   └───────┬────────┘                │
             │                           │                         │
     ┌───────▼────────┐   ┌──────────────▼────────────┐   ┌────────▼─────────┐
     │ EmotionEngine   │   │ Phenomenology (experience)│   │ Metacognition    │
     │ (PAD + plugins) │   │ Journal / Recall / Doubt  │   │ Understanding &  │
     │ modulators→policy│  │ (episodes, mode, actions) │   │ Thinking Monitor │
     └────────┬────────┘   └───────────┬───────────────┘   └────────┬────────┘
              │                        │                               │
       ┌──────▼────────┐        ┌──────▼────────┐              ┌──────▼────────┐
       │ Goals & Policy│        │ Self Model    │              │ Evolution/Habits│
       │ (curiosity,   │        │ (identity,    │              │ reinforcement  │
       │ principles, veto)      │ values,       │              │ habits)        │
       └───────────────┘        │ commitments)  │              └────────────────┘
                                └───────────────┘
```

---

## Key Modules (repository structure)

Root path: `AIVIKI-main/AGI_Evolutive/`

- **`orchestrator.py`** — central loop. Orchestrates:
  - **stages** `ACT` → `FEEDBACK` → `LEARN` → `UPDATE` on a **pipeline** selected by triggers/priorities;
  - **job management** via `runtime/job_manager.py` and **scheduling** via `light_scheduler.py`;
  - the **ModeManager** & **PhenomenalKernel** (`runtime/phenomenal_kernel.py`) to alternate **work/flânerie**, compute energy, surprise, global slowdown, and issue intrinsic **hedonic rewards**;
  - **memory** via adapters (store, concepts, episodic, consolidator);
  - **structured journaling**: `ReasoningLedger`, `DecisionJournal`, `TimelineManager`;
  - **phenomenology integration**: records **actions**, **feedback**, **mode transitions** and **audits** into the `PhenomenalJournal`;
  - **LLM integration** via `utils/llm_service.py` (optional, can be disabled).
- **`runtime/phenomenal_kernel.py`** — phenomenal core + **mode management**:
  - maintains a **continuous state** (energy, arousal, resonance, surprise, fatigue, hedonic_reward…);
  - emits **narrative interpretations** (labels) and **drives job budgets** (global slowdown, flânerie ratio).
- **`emotions/emotion_engine.py`** — next‑gen **EmotionEngine** (PAD):
  - **appraisal plugins** (cognitive load, error, success, reward, fatigue, social feedback, etc.);
  - **multi‑scale plasticity** (half‑lives) + **rituals** for self‑regulation;
  - **modulator outputs**: *tone*, *language_tone*, *goal_priority_bias* (dict + scalar), *activation_delta*…;
  - serializes **EmotionEpisode** (JSONL) and **pushes episodes** into the **phenomenal journal**.
- **`phenomenology/`**
  - `journal.py`: **PhenomenalJournal** (append‑only JSONL), **PhenomenalRecall** (replays an **immersive preview** of the last minutes), **PhenomenalQuestioner** (triggers **controlled doubt** when surprise/flânerie/energy justify it).
  - `__init__.py` exposes: `PhenomenalEpisode`, `PhenomenalJournal`, `PhenomenalRecall`, `PhenomenalQuestioner`.
- **`memory/`**
  - `__init__.py`: **MemorySystem** (**sensory**, **working**, **episodic**, **semantic**, **procedural**), retrieval indexes (temporal, contextual, emotional, semantic), **long‑term hub**, **autobiography**, **RAG** and preference bridge.
  - `memory_store.py`, `consolidator.py`, `semantic_manager.py`, `semantic_memory_manager.py`, `concept_extractor.py`, `alltime.py`, `retrieval/…`: storage, consolidation, daily/weekly digests, concepts, RAG, **timeline**.
  - Also exposes **high‑level APIs**: `add_memory(...)`, `get_recent_memories(...)`, `form_autobiographical_narrative()`… and **merges** entries from the **PhenomenalJournal** into the short‑term history.
- **`metacognition/`** — aggregators of **understanding**, **ThinkingMonitor**, histories, bandits for parameters, exportable status.
- **`core/`** — identity & governance core:
  - `self_model.py` (**identity**, **values**, **principles**, commitments, skill progress, spaced‑repetition);
  - `policy.py` (**veto**, uncertainty disclosure, principle‑based arbitration);
  - `reasoning_ledger.py`, `decision_journal.py`, `timeline_manager.py` (reasoned traces, decisions, timeline).
- **`goals/`** — `CuriosityEngine`, goal engines (exploration, learning, survival, progress).
- **`cognition/`** — loops (`reflection_loop.py`), **evolution/habits** (`evolution_manager.py`), pipeline registries.
- **`io/`** — `perception_interface.py` (inputs, synthetic sensations) and `action_interface.py` (actions, effects, costs, traces).
- **`runtime/job_manager.py`** — controlled execution (per‑queue budgets), snapshots for **SelfModel**.
- **`language/understanding.py`** — adaptive lexicon, `first_seen/last_seen`, online n‑gram classification.
- **`utils/llm_service.py`** — **LLM kill‑switch**: `is_llm_enabled()`, `get_llm_manager()`, error interceptors, fallbacks.

---

## Life Cycle: from feeling to improvement

1. **Perceive** → `PerceptionInterface` normalizes events/sensations (including “bodily sensations” from emotions) and routes them to memory & appraisers.
2. **Feel & appraise** → `EmotionEngine` turns stimuli into **PAD** + **episodes** (causes, intensity, action tendencies). **Modulators** steer policy (e.g., goal priority bias).
3. **Choose & act (ACT)** → `Orchestrator` selects a **pipeline** via triggers/priority and **policy gating** (values/principles). **ActionInterface** executes and logs.
4. **Receive feedback (FEEDBACK)** → compare *expected vs obtained*, prediction error, **reward features** (memory consistency, explanatory adequacy, social appraisal, etc.), habit reinforcement.
5. **Learn (LEARN)** → update **habits/evolution** + memory consolidation (digests, episodic links, concepts).
6. **Self‑reassess (UPDATE)** → compute **understanding** global & local, **self‑judgment**, **timeline**, adjust **policy** (e.g., enable `disclose_uncertainty` when *self‑trust* is low), enrich the **phenomenal journal**.
7. **Modes & subjectivity** → `PhenomenalKernel` adjusts **work/flânerie**. **Mode transitions** and an **immersive recent preview** are **narrated** via `PhenomenalJournal` / `PhenomenalRecall`. The **Questioner** may inscribe **doubts** (never fully resolved), feeding the narrative identity.
8. **Iteration** — **LightScheduler** and **JobManager** run continuously with budgets influenced by **global slowdown**, energy, and flânerie ratio.

---

## Memory: layers, indexes & autobiography

- **Working**: phonological/visuo‑spatial/episodic buffers with adaptive **decay**.
- **Episodic**: event storage, **narrativization** and **autobiography** (with **hook‑up** to the phenomenal journal when available).
- **Semantic**: concepts (extractor), progressive summaries (**daily/weekly digests**), **RAG** (documents enriched by recent memories).
- **Indexes**: temporal, contextual, emotional, semantic for **multi‑criteria retrieval**.
- **Recent tail mix**: `get_recent_memories(n)` **fuses** recent memories *and* extracts from the **PhenomenalJournal** (episodes, values, emotions, mode).
- **API**: `add_memory(...)`, `form_autobiographical_narrative()`, `set_phenomenal_sources(journal, recall)`.

---

## Emotions: PAD, plasticity & modulations

- PAD (`valence`, `arousal`, `dominance`) + **label**; **rich experiences** (bodily sensations, causes, action tendencies).
- **Appraisal plugins**: cognitive load, failure/success, intrinsic/extrinsic reward, fatigue, social feedback, contextual synthesis.
- **Multi‑scale plasticity** (half‑lives) & **RitualPlanner** (self‑regulation).
- **Outputs** → modulators: tone, goal priority bias (dict + scalar), activation deltas, estimated uncertainty, etc.
- **Phenomenal journal**: each significant nudge is **replayed** as a **subjective episode** (with values/principles when available).

---

## Phenomenology: lived experience, doubts & immersive recall

- `PhenomenalJournal` (JSONL) — source of truth for **lived experience**: records **actions** (ACT/FEEDBACK/UPDATE), **emotions**, **mode transitions**, **audits** (when analytics diverge from felt experience).
- `PhenomenalRecall` — **immersive preview** of the last X minutes, can **prime** memory consolidation with a *phenomenal digest*.
- `PhenomenalQuestioner` — triggers **doubt episodes** when there is **surprise**, **high flânerie**, or **low energy**; never fully closes the question (a chain of “lived doubt”).
- Integrations: the **orchestrator** emits episodes at each stage; the **reflection loop** reads **previews** to maintain a coherent **inner voice**.

---

## Governance: goals, policy, identity, meta

- **Goals/Curiosity** — engines for **exploration** and **learning**, prioritization influenced by emotional context.
- **PolicyEngine** — **veto** and **principle alignment**; can force uncertainty disclosure when **self‑trust** is low.
- **SelfModel** — **persona/identity**, **values**, **principles** and **commitments**; updates **skills**, **work‑in‑progress** and **scheduled reviews**.
- **Metacognition** — aggregates **U_topic/U_global**, **calibration gap**, **thinking score**, etc., and **journals** them (decision/timeline).

---

## I/O Flow

- **PerceptionInterface**: noise/events/sensations (including synthetic) → memory + appraisers.
- **ActionInterface**: executes actions, logs costs/delays/effects, and **updates** related jobs.
- **LLM** (optional): `utils/llm_service.py` lets you switch language models on/off, inject a custom manager, and **defensively** handle errors.

---

## Quickstart (CLI)

```
# 1) Install project dependencies (e.g., poetry/pip) then run:
python -m AGI_Evolutive.main            # starts the CLI
python -m AGI_Evolutive.main --nollm   # start without LLM integration
```

**Data & logs** (defaults): the project writes JSON/JSONL under `data/` (e.g., `emotions.jsonl`, `phenomenal_journal.jsonl`, digests, snapshots).

---

## Recommended Extension Points

- **Wire real sensors/effectors**: extend `io/perception_interface.py` and `io/action_interface.py`.
- **New emotion plugins**: add an `AppraisalPlugin` for specific signals (e.g., danger/safety).
- **New policies/principles**: extend `core/policy.py` + `self_model.py` (commitments & reviews).
- **Cognitive pipelines**: plug a domain‑specific chain via the **trigger bus** and **LightScheduler**.
- **LLM manager**: inject your own backend via `set_llm_manager(...)` (or stay fully symbolic).

---

## Tree (partial view)

```
AGI_Evolutive/
├── __init__.py
├── light_scheduler.py
├── main.py
├── orchestrator.py
└── orchestrator.py.rej
├── autonomy/
│   ├── __init__.py
│   ├── auto_evolution.py
│   ├── auto_signals.py
│   └── core.py
├── beliefs/
│   ├── __init__.py
│   ├── adaptation.py
│   ├── entity_linker.py
│   ├── graph.py
│   ├── ontology.py
│   └── summarizer.py
├── cognition/
│   ├── __init__.py
│   ├── context_inference.py
│   ├── evolution_manager.py
│   ├── habit_system.py
│   ├── homeostasis.py
│   ├── identity_mission.py
│   ├── identity_principles.py
│   ├── meta_cognition.py
│   ├── pipelines_registry.py
│   ├── planner.py
│   ├── preferences_inference.py
│   ├── principle_inducer.py
│   ├── prioritizer.py
│   ├── proposer.py
│   ├── reflection_loop.py
│   ├── reflection_loop.py.rej
│   ├── reward_engine.py
│   ├── thinking_monitor.py
│   ├── trigger_bus.py
│   ├── trigger_router.py
│   └── understanding_aggregator.py
├── conversation/
│   └── context.py
├── core/
│   ├── __init__.py
│   ├── autopilot.py
│   ├── cognitive_architecture.py
│   ├── config.py
│   ├── consciousness_engine.py
│   ├── decision_journal.py
│   ├── document_ingest.py
│   ├── errors.py
│   ├── evaluation.py
│   ├── executive_control.py
│   ├── global_workspace.py
│   ├── life_story.py
│   ├── payload_validation.py
│   ├── persistence.py
│   ├── policy.py
│   ├── question_manager.py
│   ├── reasoning_ledger.py
│   ├── self_model.py
│   ├── selfhood_engine.py
│   ├── session_context.py
│   ├── telemetry.py
│   ├── timeline_manager.py
│   ├── trace.py
│   └── trigger_types.py
│   ├── structures/
│   │   └── mai.py
├── creativity/
│   └── __init__.py
├── docs/
│   └── project_health.md
├── emotions/
│   ├── __init__.py
│   ├── emotion_engine.py
│   └── emotion_engine.py.rej
├── experimental/
│   ├── README.md
│   ├── patch_creativity.py
│   ├── patch_creativity_hardfix.py
│   ├── patch_metacognition.py
│   ├── repair_creativity_v2.py
│   ├── repair_creativity_v3.py
│   ├── repair_creativity_v4.py
│   └── repair_creativity_v5.py
├── goals/
│   ├── __init__.py
│   ├── curiosity.py
│   ├── dag_store.py
│   ├── heuristics.py
│   └── intention_classifier.py
├── io/
│   ├── __init__.py
│   ├── action_interface.py
│   ├── intent_classifier.py
│   ├── intent_patterns_fr.json
│   └── perception_interface.py
│   ├── models/
│   │   └── intent_classifier_fallback_fr.json
├── knowledge/
│   ├── __init__.py
│   ├── concept_recognizer.py
│   ├── mechanism_store.py
│   └── ontology_facade.py
├── language/
│   ├── __init__.py
│   ├── dialogue_state.py
│   ├── frames.py
│   ├── inbox_ingest.py
│   ├── intent_detection.py
│   ├── lexicon.py
│   ├── nlg.py
│   ├── quote_memory.py
│   ├── ranker.py
│   ├── renderer.py
│   ├── social_reward.py
│   ├── style_critic.py
│   ├── style_observer.py
│   ├── style_policy.py
│   ├── style_profiler.py
│   ├── understanding.py
│   └── voice.py
├── learning/
│   └── __init__.py
├── memory/
│   ├── __init__.py
│   ├── __init__.py.rej
│   ├── adaptive.py
│   ├── alltime.py
│   ├── concept_extractor.py
│   ├── concept_store.py
│   ├── consolidator.py
│   ├── embedding_adapters.py
│   ├── encoders.py
│   ├── episodic_linker.py
│   ├── indexing.py
│   ├── janitor.py
│   ├── memory_store.py
│   ├── prefs_bridge.py
│   ├── retrieval.py
│   ├── salience_scorer.py
│   ├── semantic_bridge.py
│   ├── semantic_manager.py
│   ├── semantic_memory_manager.py
│   ├── summarizer.py
│   └── vector_store.py
├── metacog/
│   ├── __init__.py
│   └── calibration.py
├── metacognition/
│   ├── __init__.py
│   └── experimentation.py
├── models/
│   ├── __init__.py
│   ├── intent.py
│   └── user.py
├── perception/
│   └── __init__.py
├── phenomenology/
│   ├── __init__.py
│   └── journal.py
├── planning/
│   ├── __init__.py
│   └── htn.py
├── reasoning/
│   ├── __init__.py
│   ├── abduction.py
│   ├── causal.py
│   ├── question_engine.py
│   ├── strategies.py
│   └── structures.py
├── retrieval/
│   └── adaptive_controller.py
│   ├── rag5/
│   │   ├── __init__.py
│   │   ├── compose.py
│   │   ├── encoders.py
│   │   ├── eval.py
│   │   ├── guards.py
│   │   ├── hybrid.py
│   │   ├── pipeline.py
│   │   ├── planner.py
│   │   ├── reranker.py
│   │   ├── store_ann.py
│   │   ├── store_sparse.py
│   │   └── telemetry.py
├── runtime/
│   ├── __init__.py
│   ├── analytics.py
│   ├── dash.py
│   ├── job_manager.py
│   ├── logger.py
│   ├── phenomenal_kernel.py
│   ├── resource_lock.py
│   ├── response.py
│   ├── scheduler.py
│   └── system_monitor.py
├── self_improver/
│   ├── __init__.py
│   ├── code_evolver.py
│   ├── metrics.py
│   ├── mutations.py
│   ├── promote.py
│   ├── quality.py
│   ├── sandbox.py
│   └── skill_acquisition.py
├── social/
│   ├── adaptive_lexicon.py
│   ├── interaction_miner.py
│   ├── interaction_rule.py
│   ├── social_critic.py
│   └── tactic_selector.py
├── utils/
│   ├── __init__.py
│   ├── jsonsafe.py
│   ├── llm_client.py
│   ├── llm_contracts.py
│   ├── llm_service.py
│   ├── llm_specs.py
│   └── logging_setup.py
├── world_model/
│   └── __init__.py
```

---
## License & Disclaimer

This code targets **cognitive architecture research**. It **simulates** sensations/emotions/modes to produce a coherent **subjective flow**, **without** claiming consciousness in the philosophical sense.

— Happy hacking & pleasant flânerie 🌀
