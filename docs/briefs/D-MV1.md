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
