# Brief v-fcw4 — Verifier: F-CW4's six-directive fix set

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git diff` allowed, never write. You verify; you edit nothing.

## Check

Fixer claims: `MiSide/docs/logs/F-CW4.log`. Diff: locate the F-CW4 commit
via `git log --oneline -- MiSide/pipeline | head -3` if already committed,
else working tree.

Per directive, verify in actual text/code:
1. Tool canonicalization: `_stage_tool` resolves
   `AssetStudioModCLI-0.19.0.1` first; hard version check present; zero
   references to `is4` scratch anywhere under `pipeline/`.
2. detect.py regex reader would return `2021.3.35f1` for the documented
   header shape and not regress plain v21-style files (reason through both
   paths).
3. Probe keep-going: probe failure path actually reachable + ledgers row
   replaced in place (not appended) — consistent with S4 write mode.
4. Cyclic-tail caveat: EXTRACTION-LOG event + census AC-12 residue entry
   exist and derive from real ledger data (`recursion_warnings`), not
   hardcoded strings.
5. Spec errata block: exactly one block, evidence-cited, nothing else in
   the frozen spec changed (`git diff` scope).
6. Investigation doc corrections match v-s4b's flagged facts verbatim.

Smoke yourself: py_compile touched modules; `--list` exit 0.

## Deliverable

`docs/research/verifications/f-cw4-vA.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤10 lines.
