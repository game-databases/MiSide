# Brief T2-attempt4 — UI style analysis from thumbnails (MiSide)

You are a research subagent relaunched by the MiSide orchestrator (attempt 4;
prior attempts died to API errors during LARGE IMAGE reads — that failure
mode is what this brief is built to avoid). You CANNOT spawn other agents.
No `git` commands. Write ONLY inside `C:\_reps\game-databases\MiSide\`;
read-only elsewhere; never touch other games' dirs.

## Read first

1. `C:\_reps\game-databases\_foundation\design-standard.md` — IN FULL.
2. `C:\_reps\game-databases\FRAMEWORK.md` §2.11 only.
3. `C:\_reps\game-databases\MiSide\docs\briefs\T2-ui-style-scout.md` — the
   ORIGINAL mission (your analysis must still fulfill its Deliverable spec:
   palettes, typography impressions, UI chrome patterns, glitch motifs,
   light-vs-dark recommendation, 6–10 concrete token recommendations,
   anti-genericism check).

## Already done for you

- Screenshots ARE downloaded: `C:\_reps\game-databases\MiSide\design\refs\screenshots\`
  (~21 files: steam-ss*.jpg, demo-d*.jpg, comm*/probe* evidence files).
- Provenance exists: `credits.jsonl` in the same dir. Do NOT re-download.

## CRITICAL — how to avoid dying like attempts 1–3

NEVER Read the full-resolution JPGs directly. Instead:

1. Make thumbnails with the probe venv's Pillow:
   `"D:\unpacked_game_data\MiSide\probe-001\venv\Scripts\python.exe" -c "..."`
   — write ~900px-wide JPEGs to `design\refs\screenshots\thumbs\` (same
   basenames). Verify the thumbs exist and are small before proceeding.
2. Read ONLY the thumbnail files (several per message at most).
3. For precise pixel hex sampling, use PIL programmatically on the ORIGINALS
   (`getpixel` / dominant-color via `Image.quantize`) and print values —
   do not eyeball full-res images in context.

## Deliverable

`C:\_reps\game-databases\MiSide\docs\research\ui-style-scout.mdx` — the full
analysis per the original T2 brief (all six analysis areas + token table +
anti-genericism section), every claim tied to a thumb/original filename;
hexes from actual sampling output, marked `[sampled]`, uncertain ones
`[unverified]`. Also append to `design\refs\screenshots\credits.jsonl` any
file you find there that lacks a row (match by basename).

## Rules

- No legality commentary. MDX style. Final message ≤10 lines.
- If a tool call fails twice, note it and continue with what works — never
  retry into an error loop.
