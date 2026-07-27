# Persona and Jelly Sandwich: Digital Organism

This repository joins the Gelatinblob subjective-controller idea to a **small persistent digital organism**, rather than another prompt-driven assistant. The sidecar shapes attention, appraisal, conduct, and expression; the organism supplies continuous embodied life, autobiographical ownership, and change through time.

Its central rule is:

> Every new moment belongs to the same subject who lived through the previous moment, and the previous moment alters the subject who encounters the next one.

```text
something happens to me
        ↓
what do I notice?
        ↓
what does it remind me of?
        ↓
how does it affect my body, needs, relationship, and self-story?
        ↓
what do I want to do?
        ↓
what do I reveal or conceal?
        ↓
what happened because of my action?
        ↓
what has this changed about me?
```

## What changed from the uploaded prototype

The original prototype already supplied first-person event ownership, pressure dynamics, autobiographical memory, associations, consequences, deterministic action selection, private/public separation, and model-independent expression packets.

This fork adds the pieces required for ongoing life:

- **Homeostasis:** energy, fatigue, hunger, thirst, comfort, pain, warmth, restlessness, curiosity, loneliness, safety, focus, and satisfaction change continuously.
- **Sensorium:** light, noise, temperature, novelty, social presence, and clutter alter the organism even when nobody speaks.
- **Autonomous life:** idle time produces selected activities and first-person experiences rather than merely decaying numbers.
- **Preferences:** authored preferences live in the cartridge; additional preferences can be learned from valenced experience.
- **Habits:** simple trigger/action tendencies bias conduct without becoming a second planner.
- **Relationships:** each person has trust, comfort, respect, interest, attachment, affection, safety, familiarity, obligation, and uncertainty.
- **Self-narrative:** repeated experiences can become cautious autobiographical conclusions supported by memory IDs.
- **World consequence separation:** the organism proposes conduct; an external world supplies success, failure, and objective changes.
- **Cartridge ownership:** identity, homeostatic tendencies, sensitivities, preferences, habits, activities, relationship defaults, and dialogue remain outside the generic engine.
- **Portable expression:** an LLM is optional and receives only an approved `ExpressionPacket`.

## Unified causal lifecycle

```text
objective observation or passage of time
        ↓
what is happening to me?
        ↓
homeostasis + sensorium + retrieved history
        ↓
situated appraisal and relationship meaning
        ↓
active needs, pressures, habits, and conflicts
        ↓
candidate conduct and viability forecast
        ↓
host legal-action filter and world resolution
        ↓
observed consequence
        ↓
preference, relationship, memory, and self-narrative update
        ↓
renderer packet and public expression
```

## Architecture boundary

```text
ENGINE
  continuity, homeostasis, perception, appraisal, retrieval,
  habit pressure, action selection, consequence inheritance,
  preference learning, relationship change, self-narrative

CARTRIDGE
  identity, values, sensitivities, setpoints, rates,
  initial preferences, habits, idle activities, dialogue

WORLD / HOST
  observations, available actions, objective outcomes

RENDERER
  wording and performance only
```

The renderer is the voice. It is not the organism and cannot directly rewrite the organism's state.

## Run

```bash
python -m digital_subject.cli demo
pytest -q
```

Python 3.11+ is required because the cartridge loader uses the standard-library TOML parser.

## Design constraints

- Deterministic and replayable
- No mandatory LLM, embeddings, database, or network
- Character-specific material never lives in engine code
- No invented memories
- No direct renderer authority over identity, needs, relationships, or world facts
- Simple enough to port to C99 after the behavior stabilizes

## Project status

This is an executable v0.2 organism core, not a finished human simulation. The next useful work is host integration: a small persistent room/world, real clock catch-up, and an inspector showing what the organism experienced while no user was present.
