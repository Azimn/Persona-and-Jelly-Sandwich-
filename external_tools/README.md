# External Tools and Utilities

This directory is reserved for authoring and maintenance utilities that should not increase the minimal organism runtime.

Planned tools include:

- `chat_importer/`: converts large chat logs into provenance-preserving candidate history records.
- `cartridge_builder/`: prepares character identity, dispositions, relationships, and renderer assets from source material.
- `memory_editor/`: inspects duplicates, contradictions, consolidation, and compression without silently creating lived events.
- `state_inspector/`: presents needs, relationships, expectations, commitments, epistemic revisions, and narrative evidence.
- `migration_tools/`: upgrades old state and cartridge versions.
- `dataset_tools/`: builds renderer and small-model training data.

## Frontier-model extraction guide

Use a capable model as a formatter and analyst, not as identity authority.

```text
You are preparing historical evidence for a persistent digital character.
Do not imitate the character and do not invent missing events.

For each meaningful exchange extract:
- timestamp and source message IDs
- speakers and objective utterances
- candidate perception and interpretation
- relationship effect
- preference evidence
- promise, commitment, or expectation
- unresolved question or open loop
- autobiographical importance
- contradictions
- confidence

Keep objective evidence separate from interpretation.
Return schema-valid JSON.
```

## Existing-character guide

```text
Separate supplied material into:
FOUNDATIONAL CANON
DISPOSITIONS
VOICE EXAMPLES
RELATIONSHIPS
UNCERTAIN OR CONTRADICTORY MATERIAL
UNSUPPORTED INVENTION

Do not turn pre-instantiation source events into newly lived experiences.
Retain citations or source identifiers for every claim.
```

Tools may be web apps or desktop utilities and may use large models. Runtime exports must remain compact, validated, and usable without those tools.
