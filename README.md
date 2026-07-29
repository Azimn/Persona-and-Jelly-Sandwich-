# Persona and Jelly Sandwich: Digital Organism

This repository joins the Gelatinblob subjective-controller idea to a **small persistent digital organism**, rather than another prompt-driven assistant.

Its central rule is:

> Every new moment belongs to the same subject who lived through the previous moment, and the previous moment alters the subject who encounters the next one.

```text
something happens to me
        ↓
what do I notice?
        ↓
what does it remind me of?
        ↓
how does it affect my body, needs, relationships, expectations, and self-story?
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
- **Sensorium:** light, noise, temperature, novelty, social presence, and clutter affect the organism even when nobody speaks.
- **Autonomous life:** idle time produces selected activities and first-person experiences rather than merely decaying numbers.
- **Preferences and habits:** authored tendencies live in the cartridge, while experience can form additional preferences and behavioral tendencies.
- **Relationships:** trust, comfort, respect, interest, attachment, affection, safety, familiarity, obligation, and uncertainty change independently.
- **Autobiographical memory and self-narrative:** repeated experiences can become cautious conclusions supported by memory IDs.
- **Epistemic continuity:** objective record, perception, interpretation, confidence, evidence, and later revision remain distinct.
- **Expectations and commitments:** predictions, promises, deadlines, confirmation, violation, fulfillment, and failure persist across sessions.
- **World consequence separation:** the organism proposes conduct; an external world supplies objective outcomes.
- **Cartridge ownership:** identity, sensitivities, setpoints, preferences, habits, activities, relationship defaults, and dialogue remain outside the generic engine.
- **Portable expression:** an LLM is optional and receives only an approved expression packet.

## Causal continuity added in v0.5

Earlier continuity records could be inspected but did not necessarily alter behavior. Version 0.5 connects lived history to the existing synthesis path.

```text
past expectations, commitments, and revised interpretations
        ↓
bounded continuity influence
        ↓
existing pressure and concern channels
        ↓
existing engine triage, habits, and conduct selection
        ↓
different conduct for an inspectable reason
```

Continuity may raise or lower existing pressures and concerns, but it cannot select an action directly. The project retains one conduct-selection authority.

Current causal mappings include:

- broken or overdue commitments lower trust and raise fear and anger;
- kept commitments raise trust and attachment and reduce fear;
- approaching commitments create anticipation;
- violated expectations raise fear and prediction instability;
- confirmed expectations raise trust;
- corrected interpretations can reduce arousal and restore self-story stability.

Every individual continuity delta is bounded to `[-0.20, 0.20]`.

See `docs/CAUSAL_CONTINUITY.md` for the authority boundary and required paired-history evaluation method.

## Persistent host

The organism can inhabit a small persistent room and continue living while the application is closed.

- Wall-clock time is converted into bounded organism ticks when the host reopens.
- Fractional elapsed time is retained.
- Long absences are capped and explicitly reported.
- The room owns objective light, noise, temperature, clutter, novelty, objects, and occupants.
- Arrivals, departures, and room changes become objective events experienced by the same subject.
- Subject, host/runtime, and continuity state are stored separately.
- A read-only inspector reports unattended life and open continuity records.

## Architecture boundary

```text
ENGINE
  homeostasis, perception, appraisal, retrieval, pressures,
  habits, conduct selection, consequence inheritance,
  preference learning, relationship change, self-narrative

CONTINUITY
  epistemic records, expectations, commitments, revisions,
  bounded influence through existing engine channels

CARTRIDGE
  identity, values, sensitivities, setpoints, rates,
  initial preferences, habits, idle activities, dialogue

WORLD / HOST
  clock, files, objective facts, observations, legal actions,
  objective outcomes

EXTERNAL TOOLS
  chat-history conversion, character research, cartridge authoring,
  embeddings, batch consolidation, migration, evaluation

INSPECTOR
  read-only visibility into organism, continuity, host, and world

RENDERER
  wording and performance only
```

The renderer is the voice, not the organism. The host owns time and objective facts. External tools may prepare validated assets but cannot silently become identity authority.

## Runtime profiles

The repository supports a layered deployment strategy:

- **Tiny runtime:** deterministic engine, compact state, cartridge, bounded memory, no mandatory model or database.
- **Standard local runtime:** persistent host, continuity, SQLite or optional embeddings, local renderer and inspector.
- **Development workstation:** importers, cartridge builders, batch simulations, frontier-model preparation, migration, and evaluation tools.

See `docs/PORTABILITY_PROFILES.md`, `docs/EXTERNAL_TOOLING.md`, and `docs/CHARACTER_IMPORT_PIPELINE.md`.

## Run

```bash
python -m digital_subject.cli demo
python -m digital_subject.cli init
python -m digital_subject.cli status
python -m digital_subject.cli tick 12
python -m digital_subject.cli room --noise 0.75 --temperature 0.30 --name "Workshop"
python -m digital_subject.cli arrive jay --name "Jay"
python -m digital_subject.cli leave jay --name "Jay"
python -m digital_subject.cli event greeting jay "Jay says hello." --tags jay,contact
```

Python 3.11+ is required.

## Validation

```bash
pytest -q
```

Tests cover the organism loop, persistence, room and clock handling, epistemic separation, belief revision, expectations, commitments, read-only inspection, and paired-history behavioral divergence.

## Design constraints

- Deterministic and replayable
- No mandatory LLM, embeddings, database, or network
- Character-specific material never lives in engine code
- No invented memories
- No direct renderer authority over identity, needs, relationships, continuity, or world facts
- No second planner or competing action selector
- No host or inspector authority to fabricate subjective conclusions
- Simple enough to port to C99 after behavior stabilizes

## Project status

Version 0.5 is an executable persistent-subject runtime in which different lived histories can now produce different conduct through the same bounded synthesis path. The next major work should deepen relationship trajectories and learned predictive models, then run longer paired-history evaluations before committing to a particular game world or embodiment platform.
