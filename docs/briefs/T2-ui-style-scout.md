# Brief T2 — game UI style scout / design-token evidence (MiSide)

You are a research subagent launched by the MiSide orchestrator. You CANNOT
spawn other agents — do all work yourself. You never run `git` commands.
Write ONLY inside `C:\_reps\game-databases\MiSide\`; read-only elsewhere in
the repo. Never touch other games' directories.

## Read before anything else

1. `C:\_reps\game-databases\AGENTS.md` — IN FULL.
2. `C:\_reps\game-databases\FRAMEWORK.md` §2.11 (design from the game's own UI)
   and `_foundation/design-standard.md` — IN FULL (dual mandate + §5 feel bar).
3. `C:\_reps\game-databases\MiSide\README.md`.
4. `C:\_reps\game-databases\_foundation\templates\design-tokens.css` if present
   (the shared token system you are producing evidence FOR).

## Mission

FRAMEWORK §2.11: per-game design tokens come from the game's OWN UI. Your job:
collect and analyze visual evidence of MiSide's interface and art direction so
a later builder can write `design/tokens.css` grounded in the real game, not
vibes. MiSide's identity: cozy-anime apartment sim that decays into glitchy
horror; the site must carry BOTH faces (that tension IS the soul per
design-standard §5).

## Evidence to gather

1. **Official screenshots** — Steam store press assets for appid 2527500
   (`https://store.steampowered.com/api/appdetails?appids=2527500` returns
   screenshot URLs; media at `shared.akamai.steamstatic.com` /
   `cdn.akamai.steamstatic.com`). Download 8–15 representative shots to
   `C:\_reps\game-databases\MiSide\design\refs\screenshots\` (descriptive
   filenames). If curl returns blank/incomplete, retry once with an
   AI-crawler User-Agent header (OAI-SearchBot / Claude-User style); one
   attempt per wall, then record the finding and move on.
2. **Community/UI captures** — 3–6 additional shots showing menus/dialogue/
   inventory/cartridge-minigame UI specifically (store shots skew cinematic).
   Community wikis/videos thumbnails are acceptable; record source URL per
   shot in your notes file.
3. **Style analysis** (the deliverable's core):
   - dominant palettes: cozy mode vs horror/glitch mode (hex estimates from
     actual pixels — sample them, don't invent);
   - typography impressions (rounded vs sharp, case usage, any pixel/CRT
     motifs);
   - UI chrome patterns observed (dialogue boxes, choice buttons, inventory
     cells, health/sanity indicators, subtitle style);
   - glitch/error motifs (scanlines, RGB split, corruption overlays,
     windowed pop-ups) usable as site accents;
   - light-vs-dark default recommendation for a database used 8–16h/day;
   - 6–10 concrete token recommendations (CSS custom-property names +
     values): bg layers, text tiers, accent(s), danger/glitch accent,
     success/warm accent, radius family, shadow/glow recipe.
4. **Anti-genericism check**: name what makes a MiSide page INSTANTLY
   recognizable vs a generic dark wiki (per design-standard §5.1 "colour is
   identity") — e.g. Mita-portrait colour keying, cartridge-shaped cards,
   VHS-glitch hover states. Proposals only; the build pipeline decides.

## Deliverables

- `C:\_reps\game-databases\MiSide\docs\research\ui-style-scout.mdx` — the
  analysis above, every claim tied to a downloaded file or URL; uncertain
  claims marked `[unverified]`.
- The screenshot files themselves under `MiSide\design\refs\screenshots\`
  plus a `credits.jsonl` there: one line per file
  `{"file": "...", "source_url": "...", "kind": "steam|community"}`.

## Rules

- No legality commentary anywhere — provenance facts only (repo-plane only;
  nothing user-facing is being authored here).
- MDX-flavored Markdown; tight cross-links between your own headings.
- Do not fabricate hex values — open the actual images (Read tool renders
  images) and sample.
- Final message: ≤12 lines — palette summary, top 3 motif findings,
  deliverable paths, count of shots saved.
