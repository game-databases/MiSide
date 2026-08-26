# Brief v-b2b — Verifier B: B-2 build (spec-conformance lens)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file.

## Check

Spec + emitted datasets as in v-b2a; contracts docs
`contracts/dataset-achievements.mdx`, `contracts/dataset-endings.mdx`.

1. Schema conformance per spec (incl. the four-class behavior taxonomy
   correctly applied — 11/15/3 census vs the spec's fence).
2. `#line_index=` grammar honored everywhere (grep for bare `path:N` loc
   cites that F2 banned); branch-ordinal edge ids consistent with the
   declared deviation.
3. Honesty: unverified-behavior marks on exactly the 15 fenced predicates;
   Peaceful stub honest; dead-ref edges ledgered not dropped.
4. Contracts bindable standalone; deviations list (family layout, MDX,
   safe-of-life windows, AC-B2 sweep) each acceptable vs spec intent?

## Deliverable

`docs/research/verifications/b2-vB.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤12 lines.
