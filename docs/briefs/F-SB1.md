# Brief F-SB1 — Site Fixer: R-SB1's two blockers + minors (MiSide site/)

You are a fresh Site Fixer subagent of the MiSide orchestrator. You CANNOT
spawn agents. You never run `git` commands. Touch ONLY files under
`C:\_reps\game-databases\MiSide\site\{src,ci,public}` (+ build-log block).
**PROCESS SAFETY: never taskkill by image name — port-scoped only if you
must stop a server you started; prefer letting it exit.** Disk: C: ~2 GB
free — no new installs.

## Read

1. VERDICT: `docs/research/verifications/sb1-review.mdx` — 2 blockers +
   5 minors. Fix ALL.
2. `docs/specs/site-scaffold.mdx` §10 (sitemap contract) as the bar.

## Fixes

1. **BLOCKER canonical:** `src/components/routes/entityView.tsx:157`
   buildEntityMetadata must emit locale-prefixed self-canonicals for
   prefixed locales (`/ru/mita/x` → canonical `/ru/mita/x`; pivot keeps
   bare). Index/home paths already correct — align entity detail to them.
2. **BLOCKER sitemap:** all partitions must emit ABSOLUTE `<loc>` URLs
   (origin from config); robots.txt `Sitemap:` line absolute too.
3. **Minors:** fix `npm test` script form (Node 22-compatible runner
   invocation); `/ru/` trailing-slash canonical; root JSON-LD
   Organization/inLanguage nits; Radix select `dir="rtl"` inside RTL
   pages; remove dead guard block in parity script.
4. Re-run: chrome parity ×34, hex lint, unit tests, curl subset (canonical
   + sitemap checks) — report actual outputs.

Final message ≤8 lines: per-fix result + re-run counts.
