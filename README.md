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

## What the organism contains

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

## Persistent host added in v0.3

The organism can now inhabit a small persistent room and continue living while the application is closed.

- Wall-clock time is converted into bounded organism ticks when the host reopens.
- Fractional elapsed time is retained instead of discarded.
- Long absences are capped and explicitly reported rather than silently replaying an unbounded number of cycles.
- The room owns objective light, noise, temperature, clutter, novelty, objects, and occupants.
- Day and night can change ambient light and sound without manufacturing conversation.
- Arrivals, departures, and room changes become objective events experienced by the same subject.
- Subject state and host/runtime state are written atomically to separate JSON files.
- A read-only inspector reports what happened while nobody was watching.

## Unified causal lifecycle

```text
objective observation or passage of time
        ↓
host applies objective room and clock state
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
  clock, files, room facts, observations, available actions,
  objective outcomes

INSPECTOR
  read-only visibility into organism, host, and world

RENDERER
  wording and performance only
```

The renderer is the voice. It is not the organism and cannot directly rewrite the organism's state. The host owns time and objective world facts, but it does not author beliefs, memories, or relationships. The inspector has no mutation path.

## Run

In-memory demonstration:

```bash
python -m digital_subject.cli demo
```

Create a persistent subject and room:

```bash
python -m digital_subject.cli init
```

Reopen it, catch up elapsed time, and inspect unattended life:

```bash
python -m digital_subject.cli status
```

Advance explicit simulation time:

```bash
python -m digital_subject.cli tick 12
```

Change the room:

```bash
python -m digital_subject.cli room --noise 0.75 --temperature 0.30 --name "Workshop"
```

Record presence and absence:

```bash
python -m digital_subject.cli arrive jay --name "Jay"
python -m digital_subject.cli leave jay --name "Jay"
```

Deliver an objective interaction and render cartridge-owned expression:

```bash
python -m digital_subject.cli event greeting jay "Jay says hello." --tags jay,contact
```

State defaults to `subject_state.json`; host and room timing defaults to `subject_runtime.json`. Both paths, the tick duration, the catch-up cap, the subject ID, and the cartridge can be changed through CLI options.

Python 3.11+ is required because the cartridge loader uses the standard-library TOML parser.

## Validation

```bash
pytest -q
```

GitHub Actions runs the suite on supported Python versions. Runtime-host tests cover clock catch-up, long-absence bounding, room persistence, objective sensorium application, unattended-life reporting, and read-only inspection.

## Design constraints

- Deterministic and replayable
- No mandatory LLM, embeddings, database, or network
- Character-specific material never lives in engine code
- No invented memories
- No direct renderer authority over identity, needs, relationships, or world facts
- No host or inspector authority to fabricate subjective conclusions
- Simple enough to port to C99 after the behavior stabilizes

## Project status

This is an executable v0.3 organism runtime with continuous internal life, a persistent room, real-time catch-up, and inspection. The next major layer is a host-facing adapter protocol so a game, Telegram bridge, robot, or desktop interface can provide observations and legal actions without becoming the character.
