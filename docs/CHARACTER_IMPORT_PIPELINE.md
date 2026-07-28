# Character Import Pipeline

Large histories and source corpora are development inputs, not runtime responsibilities.

## Chat-history flow

```text
raw messages
→ speaker and timestamp normalization
→ objective utterance records
→ candidate episodes
→ candidate preferences, commitments, expectations, and relationship changes
→ provenance and confidence
→ human or automated validation
→ portable import bundle
```

The importer must not collapse these layers:

- what was literally said or observed
- what the character may have perceived
- what the character may have inferred
- what later evidence supported or contradicted
- what emotional or habitual residue remained

Every extracted item must retain source message IDs and timestamps when available. Imported interpretations are provisional unless explicitly validated.

## Existing fictional characters

Source analysis must separate:

- foundational canon
- stable dispositions and values
- voice examples for the renderer
- established relationships
- uncertain, contradictory, or adaptation-specific material
- unsupported invention

Pre-instantiation biography belongs in foundational cartridge or biography records. Events occurring after the organism begins belong in lived memory.

## Frontier-model prompt contract

A frontier model may extract and format records, but it must:

- avoid inventing missing events
- keep speakers separate
- preserve uncertainty
- cite source identifiers
- emit schema-valid JSON
- never declare itself the character
- never write directly into live state

See `external_tools/README.md` and the schemas under `schemas/`.
