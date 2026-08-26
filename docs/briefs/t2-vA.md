# Brief t2-vA — Verifier A on T2 UI style scout (evidence lens)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
never run `git`; read-only outside your deliverable. You VERIFY, you edit
nothing.

## CRITICAL — survival rules (3 prior agents died to this)

NEVER Read a full-resolution image. Read ONLY files under
`design/refs/screenshots/thumbs/` (~900 px, safe), ≤4 per message. For any
pixel-level claim, sample programmatically with the probe venv:
`"D:\unpacked_game_data\MiSide\probe-001\venv\Scripts\python.exe" -c "..."`
(`getpixel` / `quantize` on originals or thumbs) and compare printed hexes.

## Check

`C:\_reps\game-databases\MiSide\docs\research\ui-style-scout.mdx` claims
sampled palettes and file-tied motifs. Verify the EVIDENCE:

1. Re-sample ≥8 of its `[sampled]` hexes yourself via PIL on the named
   files (originals preferred). Match = claim holds; mismatch >ΔE-eye =
   FINDING.
2. Open 3–4 thumbs it cites for motifs (pills/chrome, VHS banding,
   cartridge grids, heart wallpaper). Do the named images actually show
   them?
3. `credits.jsonl` in `design/refs/screenshots/` claims 112 rows covering
   every image on disk: spot-check 10 random filenames exist as rows.

## Deliverable

`C:\_reps\game-databases\MiSide\docs\research\verifications\t2-vA.mdx` —
per-check results incl. your sampled-vs-claimed hex table; final line
exactly `VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤12 lines total.
