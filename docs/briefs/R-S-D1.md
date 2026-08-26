# Brief R-S-D1 — Reviewer: S-D1's pack spec.md (MiSide)

You are a fresh Reviewer subagent launched by the MiSide orchestrator. You
CANNOT spawn other agents. You never run `git` commands. You review; you
edit nothing.

## Read first

1. `C:\_reps\game-databases\FRAMEWORK.md` §4 (template the spec must follow)
   + §7.
2. `C:\_reps\game-databases\_foundation\site-sections.md` (CORE/FIT bar),
   `seo-standard.md`, `localization-architecture.md`, `design-standard.md`,
   `domain-doctrine.md`.
3. The spec's cited inputs: `competitor-research.md`,
   `docs/research/game-research.mdx`, `docs/research/ui-style-scout.mdx`,
   `toolchain.md`, `docs/research/explorer-e1-hands-on.mdx`.
4. SPEC UNDER JUDGMENT: `C:\_reps\game-databases\MiSide\spec.md`.

## Review dimensions

1. **Template conformance:** every FRAMEWORK §4 section present, in order,
   nothing missing.
2. **CORE/FIT honesty:** each section tag justified against site-sections
   rules; flag anything tagged CORE that the bar doesn't support, or FIT
   items silently omitted from non-goals.
3. **Locale table evidence:** re-run the client-dir listing yourself
   (`ls "A:\SteamLibrary\steamapps\common\MiSide\Data\Languages"`) and diff
   against the spec's shipped-locale table — every row must reconcile;
   store-31 cross-check vs competitor-research.md.
4. **Citation integrity:** sample ≥10 citations; do they support the claims?
5. **No invented features / no overreach:** everything traceable to an
   input; tools section is a stub pointing to tools-plan.md (a detailed
   plan here = finding).
6. **Design direction:** references ui-style-scout.mdx without duplicating
   its tables; dual-soul framing preserved.

## Verdict

Write `docs/research/verifications/s-d1-review.mdx`: findings with severity
(blocker/major/minor) + line cites; final line exactly `VERDICT: APPROVE`
or `VERDICT: NEEDS_REVISION — <N findings>`. ≤14 lines total.
