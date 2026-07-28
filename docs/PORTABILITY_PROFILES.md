# Portability Profiles

The organism must remain portable across devices with radically different resources. Development tools may be powerful; runtime identity must not depend on them.

## Tiny runtime

Targets old PCs, embedded systems, retro-style devices, and small game engines.

Includes deterministic state updates, bounded memories, tag and association retrieval, compact cartridges, host adapters, and template or very small-model expression. It requires no network, embeddings, database server, or frontier model.

## Standard local runtime

Targets ordinary desktops, handheld PCs, and small local servers.

Adds SQLite or equivalent indexed storage, optional embeddings, background clock service, a local inspector, richer consolidation, and an optional Ollama renderer.

## Development workstation

Adds chat import, cartridge authoring, source analysis, timeline editing, batch simulation, evaluation, migration, repair, dataset generation, and frontier-model preparation.

## Asset compilation

Authoring formats are not runtime formats. A tool may consume large JSON files and produce compact assets such as:

```text
CARTRIDGE.BIN
MEMORY.BIN
STATE.BIN
DIALOGUE.BIN
```

Every tier must preserve stable IDs, provenance, identity boundaries, and semantic equivalence. Optional indexes may be rebuilt and must never be the sole location of autobiographical truth.
