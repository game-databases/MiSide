# Brief F-VC1 — Site Fixer: VC-1's 8-item fix list (MiSide site/)

You are a fresh Site Fixer subagent of the MiSide orchestrator. You CANNOT
spawn agents. You never run `git`. Touch ONLY `site/` (+ build-log block).
PROCESS SAFETY: never taskkill by image name; port-scoped PID only.
DISK: C: ~2 GB free — NO new installs; work within existing node_modules;
keep any scratch under site/.next or Temp and clean it.

## Read

1. CRITIC REPORT: `docs/research/visual-critic-1.mdx` — the 8 numbered
   fixes in priority order. Implement ALL.
2. Evidence shots: `C:/Users/lineg/AppData/Local/Temp/vc1-miside/`
   (read-only reference).

## The gaps you close (from the critic)

1. **Art-first**: pages render `imgs: []` empty wells. Wire real art:
   the catalogue (`extracted/MEDIA-CATALOGUE.md`) + art export lives at
   `D:\unpacked_game_data\MiSide\art-export\` — select per-entity/home
   images, copy ONLY needed files into `site/public/img/` (disk! keep
   <200 MB total, prefer webp/resize via existing deps if available),
   wire `<img>`/next-image sources from dataset fields.
2. **Search index**: `/search/en.idx.json` must cover ALL entities
   (characters, achievements, endings, cartridges, minigames, documents,
   scenes POIs) with human titles from datasets — typing "mita" MUST hit.
3. **Entity object completion**: real names from datasets (not slugs) in
   h1/title/pills/breadcrumb; data modules (achievements owned, dialogue
   pool, appearances); per-Mita accent re-key from registry palettes
   (enka-standard).
4. **Horror register alive**: route-import CorruptionHover + DialogueBand
   + KeycapKbd onto home/entity/search chrome; verify
   document.getAnimations() > 0 after your changes.
5–8. RU nav collision at 1536px, VT323 mid-chip fallback (subset or swap
   to cyrillic-capable mono for chips), AR dir on `<html>`, de-narration
   of remaining placeholder copy.

Re-run: parity ×34, hex lint, unit tests, curl subset, THEN re-screenshot
your own before/after (web-browse skill) to confirm each critic item.

RESUME NOTE: prior fixer runs died to API errors MID-WORK. The working
tree already holds substantial partial progress (art in public/img,
src/data/art.ts, edits across routes/kit/layouts). AUDIT what exists
FIRST against the 8 items, finish the gaps, do not redo from scratch.

Final message ≤10 lines: per-item done-state + your own re-scores vs the
critic's.
