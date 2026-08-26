# Brief VC-1 — Visual Critic: MiSide DB chrome vs game soul + top competitors

You are the HARSH Visual Critic subagent of the MiSide orchestrator
(promptForDB-mandated side-by-side loop). You CANNOT spawn agents; never
run `git`; never taskkill by image name (port-scoped PID only). Write ONLY
`C:\_reps\game-databases\MiSide\docs\research\visual-critic-1.mdx`.
DISK MINIMAL.

## Render the site yourself

`cd C:\_reps\game-databases\MiSide\site && npx next start -p 4791` in
background; use the `web-browse` skill (stealth headless Chrome) to
screenshot: pivot home `/`, `/ru/`, one entity detail (`/mita/mita-usual`),
search-in-place interaction, ar locale RTL. Kill by PID when done.

## References (side-by-side mandate)

1. GAME SOUL: `MiSide/docs/research/ui-style-scout.mdx` token table +
   motifs; thumbs at `design/refs/screenshots/thumbs/` (READ THUMBS ONLY).
2. COMPETITORS: browse enka.network (Genshin), new-world.guide,
   wikily.gg — screenshot their home/entity chrome for comparison.

## Grade honestly (this is a CRITIC role — praise is not your job)

Per surface, score 0–10 and list CONCRETE defects:
- Soul fidelity: do pills/keycaps/VHS-corruption language actually appear
  as interactions, or is it flat theming? Dual-soul (cozy/horror) readable?
- Typography: Nunito/VT323 hierarchy vs game's actual UI text?
- Layout density & hierarchy vs the three competitors — where do we lose?
- Micro-interactions: hover/corruption effects present? Motion?
- RTL/ar correctness visually; RU typography quality (Cyrillic Nunito).
- CWV feel (LCP impression).

## Verdict

Final section: numbered fix list (max 8, highest-impact first, each with
file hint) + final line exactly `CRITIC: CHROME_PASSES` or
`CRITIC: FIXES_REQUIRED — <N items>`. ≤20 lines body total.
