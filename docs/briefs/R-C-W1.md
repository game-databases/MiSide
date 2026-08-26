# Brief R-C-W1 — Code Reviewer: C-W1's `run_all` implementation (MiSide)

You are a fresh Code Reviewer subagent launched by the MiSide orchestrator.
You CANNOT spawn other agents. You never run `git` write commands (`git
diff`/`log` fine). You review; you fix nothing. Work read-only inside
`C:\_reps\game-databases\MiSide\` plus your verdict file.

## Read first

1. `docs/specs/pipeline-run_all.mdx` — THE contract (§4 manifest = what may
   exist; §5 ACs = behavior; §1 non-goals = what must NOT exist).
2. `docs/research/explorer-e1-hands-on.mdx` — measured tool facts.
3. `docs/questions.md` §4–§8 — binding rulings.
4. The implementation under `pipeline/` (IGNORE `pipeline/tests/` — a
   parallel TestWriter owns it; flag if implementation reads/tests touch
   each other inappropriately).

## Review dimensions

1. **Manifest fidelity:** every §4 file exists and is implemented; NOTHING
   beyond manifest+ACs (speculative config = finding).
2. **Command fidelity:** every external-tool invocation byte-matches the
   E1-proven commands pinned in the spec.
3. **Ruling conformance:** never writes under `<game-root>`; ledger
   artifacts use deterministic full rewrite (S4 write mode), never append;
   exit codes 0/2/4 as specced; tracked-light respected (no code writing
   into commit-intended paths beyond spec).
4. **Idempotency design:** would rerunning each stage really change no
   bytes modulo `census/volatile-fields.json`? Hunt timestamp/ordering/
   dict-order leaks.
5. **Smoke-run yourself:** `--list`, `--help`, and any safe unit path.
   Report actual output. Do NOT run stages that hit the real install or
   take >2 min.
6. **Honesty check:** does the final report in `docs/logs/C-W1.log`
   overclaim vs what the code does?

## Verdict

Write `docs/research/verifications/c-w1-review.mdx`: findings with
file:line, severity (blocker/major/minor), then final line exactly
`VERDICT: APPROVE` or `VERDICT: NEEDS_REVISION — <N findings>`. ≤14 lines
total. Blockers only for contract violations; style nits are minor.
