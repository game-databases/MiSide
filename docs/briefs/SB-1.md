# Brief SB-1 — Scaffold Builder: MiSide DB site foundation

You are a fresh Site Builder subagent of the MiSide orchestrator. You
CANNOT spawn agents. You never run `git` commands (orchestrator commits).
Write ONLY under `C:\_reps\game-databases\MiSide\site\` and your build-log
block in `docs/research/build-log.mdx`. Data read-only at
`MiSide/extracted/data|relinks/` + `contracts/`; game root NEVER touched.
DISK: C: critically low — keep node_modules install to ONE location
(`site/node_modules`) and clean npm cache after (`npm cache clean --force`).

## Read

1. CONTRACT: `docs/specs/site-scaffold.mdx` — arbiter-approved
   (`verifications/s1b-arbiter.mdx`). Build EXACTLY it: stack pins,
   repo tree §2, locale twin trees §3, kit contract §4 (per-primitive
   stock-vs-rebuilt; AC-S8 exiles hex literals from components),
   routing §5 (+§5.1 dispositions), map module contract §7 (S7
   conjunction gate), sitemap+JSON-LD §10, CWV budgets + CI hook (S10).
2. Tokens source: `docs/research/ui-style-scout.mdx` token table →
   `design/tokens.css` 3 tiers per spec §4.4; font procedure §4.4
   executed against extracted artifacts (name what you found).

## Mission

Implement the complete scaffold: app skeleton, locale routing (pivot EN
bare + `[locale]`), chrome i18n keyed JSON ×34, upgraded kit primitives
(visual/motion layer rebuilt per T2 evidence — Radix behavior untouched),
tokens.css, route table with reserved gates, search-in-place shell,
sitemap/JSON-LD generators, CI hook scripts. Pages themselves are LATER
pieces — stub routes rendering chrome only where the spec says so.
Self-check every executable AC (S1–S14); `next build` must pass; report
CWV-relevant config honestly.

Append "SB-1 build" block to build-log: tree summary, kit components
upgraded (list), font finding, AC scoreboard, deviations.

Final message ≤10 lines.
