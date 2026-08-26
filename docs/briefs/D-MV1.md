# Brief D-MV1 — Documentator: scene-map viewer spec

Documentator subagent of the MiSide orchestrator (PrepareTask step 2 for
the scene-map viewer piece). You CANNOT spawn agents. Never run `git`.
Touch ONLY `docs/specs/map-viewer.mdx`.

## Read

1. `docs/research/map-viewer-scout.mdx` — the Scout's survey (dataset
   shapes, existing markers-v0 assets, competitor borrow/avoid rulings,
   spec skeleton + open questions). Your primary input.
2. `extracted/data/scenes/` spot-checks as needed to pin exact field
   names into the spec (quote real paths/values, never invent).
3. `design/tokens.css` + one built route component — the spec's UI
   requirements must speak the site's token/motion language
   (CorruptionHover/VHS-drift motifs where apt; dark interior-scene soul).

## Write `docs/specs/map-viewer.mdx`

**SEQUENCING LAW (orchestrator-verified against disk):** the Scout's
headline risk is TRUE — `markers.jsonl` ships `row_count: 0` (meta-only;
4 families deferred by the no-orphan rule) and `poi.jsonl` position
census = inline 298 · pptr-unresolved 76 · none 612. A viewer built on
today's artifacts is an empty shell. The spec MUST therefore define a
gating data-side module **M0 — marker/position emission** BEFORE any
viewer module:
(a) resolve or explicitly defer-with-reasons the 76 pptr-unresolved
positions (PIPE S9 dependency named);
(b) emitter schema change for per-instance pins (class-per-level
aggregates carry ONE position slot per class-level);
(c) rerun marker projection to unblock deferred families whose owning
datasets now exist — at minimum `cartridge_item` (25 rows; DS-4
`extracted/data/cartridges/cartridges.jsonl` has landed since B-6).
M0 gets its own ACs; viewer modules depend on them explicitly.

Full piece spec: scope (viewer + entity-page map module, two-way links),
module breakdown, data contract (consume `extracted/data/scenes/`
emitted artifacts — frontend CONSUMES, never derives; name exact files),
interaction list (pan/zoom/filter/deep-link/popovers/mobile), route/
placement plan, acceptance criteria (measurable, each with its proof
method), stub policy where POI metadata is thin (missingdata.md rules),
open questions for the Arbiter. Carry the Scout's open questions forward
with your recommendations.

Constraints inherited: owned implementation only (no embeds/tiles);
art from our corpus export; i18n — every user-facing string flows
through the ×34 locale layer; performance budget consistent with CWV
smoke budgets in the board.

FINAL REPORT ≤10 lines: spec path, section count, open questions raised,
any Scout claim you had to correct.
