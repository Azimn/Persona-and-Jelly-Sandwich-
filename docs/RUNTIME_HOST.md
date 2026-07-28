# Persistent Host and Room Boundary

The persistent host exists because clock time, files, and objective world facts do not belong inside the organism's cognitive engine.

## Ownership

The host owns:

- wall-clock timestamps
- conversion of elapsed time into bounded ticks
- atomic state-file writes
- the objective room and its occupants
- delivery of objective observations

The organism owns:

- what those observations mean to it
- needs and private pressures
- memory and self-narrative
- relationship change
- selected conduct

The inspector owns nothing. It receives copies and summaries only.

## Files

`subject_state.json` contains the organism's persistent subjective state.

`subject_runtime.json` contains:

- last wall-clock timestamp
- retained fractional seconds
- last inspected organism tick
- total catch-up ticks
- room state
- the most recent catch-up report

Separating these files permits the same organism state to move to a different host without treating host timing or room facts as identity.

## Catch-up policy

Elapsed seconds are converted to ticks using `tick_seconds`. Catch-up is limited by `max_catchup_ticks`.

The cap is intentional. A machine that returns after months should not execute millions of cycles before becoming responsive. Excess ticks are reported as compressed rather than falsely claimed as moment-by-moment lived detail.

The most recent bounded interval is replayed so the resulting sensorium matches the current daypart.

## Room model

The room is deliberately small:

- light
- noise
- temperature
- clutter
- novelty
- occupants
- objects

During unattended ticks, the room applies sensorium without producing fake dialogue. Meaningful changes and person arrivals or departures are delivered as objective `Event` records through the normal organism loop.

## Read-only inspection

`OrganismInspector` can produce:

- a complete debug snapshot
- an away report since the last inspection cursor
- notable first-person experiences
- activity counts
- memories formed
- current activity and active needs
- whether a long absence was compressed

Calling the inspector does not change the organism, room, or clock state. `mark_seen()` moves only the runtime inspection cursor.
