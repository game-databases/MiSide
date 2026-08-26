# Brief R-D-S1 — Reviewer: site-scaffold spec (MiSide)

Fresh Reviewer subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file.

## Read

1. SPEC: `MiSide/docs/specs/site-scaffold.mdx`
2. Bars it must satisfy: `spec.md` (frozen), `design-standard.md` §5,
   `seo-standard.md`, `localization-architecture.md`,
   `[DR-2026-08-24-miside-pack]` ¶3, `docs/research/ui-style-scout.mdx`.
3. Data contracts: `MiSide/contracts/*.mdx` (7) + `extracted/relinks/locale_availability.jsonl`.

## Checks

1. **Locale architecture:** pivot-bare + `[locale]` twin trees per
   [DR-2026-08-20]; all-34-launch decision justified vs staged; RTL +
   alias handling correct (ru-x-prerev→ru, ar-EG→ar); hreflang driven by
   availability ledger not hardcoded.
2. **Stack pins:** versions real and mutually compatible (Next 16.3.2 +
   React 19.2.8 + Tailwind 4 + radix)? graveyardKeeper precedent claim
   accurate?
3. **shadcn upgrade contract:** stock-vs-rebuilt table covers the DR
   mandate (upgraded, not reskinned); T2 motifs mapped to named
   components; nothing rebuilt that Radix should own.
4. **Routing map:** every page-inventory entry from spec.md present? The
   no-page rulings (160 proseless notes, 371 choice nodes) sound?
   Search-in-place per DR?
5. **Map contract:** markers.jsonl no-orphan + position-truth axis bound
   correctly; Leaflet = owned rendering (no embeds)?
6. **ACs S1–S13:** executable? discriminating? Any missing foundation AC
   (e.g. CWV budget, sitemap generation)?

## Verdict

`MiSide/docs/research/verifications/d-s1-review.mdx`; findings w/
severity; final line exactly `VERDICT: APPROVE` or
`VERDICT: NEEDS_REVISION — <N>`. ≤12 lines.
