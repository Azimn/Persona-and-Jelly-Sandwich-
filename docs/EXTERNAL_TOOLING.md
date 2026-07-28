# External Tooling Boundary

The deployed organism should contain only the functions required for the character to continue existing, interpreting experience, selecting conduct, and changing through consequences.

Preparation, authoring, conversion, repair, visualization, and batch analysis belong outside the minimal runtime.

## Runtime rule

A feature belongs in the engine only when all three are true:

1. The organism must perform it during ordinary existence.
2. It directly affects lived experience, conduct, continuity, or identity.
3. It must function on the lowest supported hardware tier.

Otherwise it should be an external tool, an optional host service, or precompiled data.

## Runtime responsibilities

- persistent identity and authored/earned identity boundaries
- homeostasis and present subjective state
- perception and first-person appraisal
- bounded memory retrieval and consolidation
- relationships, preferences, habits, expectations, commitments, and open loops
- immediate conduct selection
- consequence integration
- evidence-linked self-narrative
- portable save/load and host protocol

## External responsibilities

- processing large chat archives
- researching fictional or historical characters
- generating candidate cartridges
- large-scale memory clustering and duplicate detection
- embeddings and semantic index construction
- dialogue dataset preparation and fine-tuning exports
- visual state and timeline editing
- schema migration and damaged-state repair
- batch simulation and evaluation
- frontier-model-assisted extraction

External systems may propose records. They do not become identity authority. Imported records must preserve source provenance, confidence, uncertainty, and the distinction between objective evidence and interpretation.

## Suggested layout

```text
external_tools/
  chat_importer/
  cartridge_builder/
  memory_editor/
  state_inspector/
  migration_tools/
  dataset_tools/

schemas/
  imported_history.schema.json
  character_source.schema.json
  memory_bundle.schema.json
```

The external tools may use web applications, Python, SQLite, vector databases, or frontier models. Their exported runtime assets must remain compact and platform-neutral.
