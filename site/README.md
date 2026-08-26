# MiSide site — scaffold (SB-1)

Next.js App Router scaffold per
[`docs/specs/site-scaffold.mdx`](../docs/specs/site-scaffold.mdx) (arbiter-approved).
Pages/tools/map artwork are later pieces; this ships the ground they build on.

## Run

```bash
npm install        # ONE node_modules here only (C: disk floor)
npm test           # node --test suites: S6/S7/S12/S13 + locale ledger join
npm run build      # prebuild emits machine plane, then next build (~7k pages)
npm start          # localhost production server
```

## Layout

- `src/app/(pivot)` + `src/app/[locale]` — twin route trees, EN bare paths,
  33 prefixed locales. Every route file is a thin wrapper over
  `src/components/routes/*` (regenerate with `node scripts/gen-routes.mjs`).
- `src/styles/design/tokens.css` — 3 tiers: 14 verbatim T2 §6 rows → shadcn
  semantic bridge → per-entity local overrides. Zero hex literals allowed in
  `src/components/ui|kit` (`node tests/check-hex-literals.mjs`).
- `src/i18n/` — pinned 34-row locale table + keyed chrome ×34
  (`scripts/gen-chrome.mjs`; parity gate `scripts/check-chrome-parity.mjs`).
- `src/data/` — server-only contract readers. `resolveLoc` is ARITHMETIC-FREE.
  Corpus jsonl headers come in two shapes (wrapped `_meta` vs documents-family
  bare) — the reader handles both and tolerates empty-by-contract files.
- `scripts/emit-artifacts.mjs` — machine plane into `public/`: static JSON API,
  search indexes ×34, map registry/markers, llms.txt.
- `ci/github-workflow-ci.yml` — STAGED CI workflow (install at repo-root
  `.github/workflows/`, path-filtered); CWV budgets in `cwv.budgets.json`,
  runner `scripts/check-cwv.mjs` (Lighthouse via npx, not bundled).

## Gates wired as scripts

| Gate | Command |
|---|---|
| Chrome key parity ×34 | `node scripts/check-chrome-parity.mjs` |
| No third-party map embeds | `node scripts/check-no-third-party-maps.mjs` |
| Hex-literal ban in kit | `node tests/check-hex-literals.mjs` |
| Unit suites | `npm test` |
