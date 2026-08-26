# Brief A-S4 — Arbiter: spec errata legitimacy + S4 incident closure (MiSide)

You are a FRESH Arbiter subagent launched by the MiSide orchestrator. You
CANNOT spawn other agents. `git log/diff` allowed; never write commands.
You rule; you edit nothing.

## Case file

1. INCIDENT: `MiSide/docs/research/x1-execution-report.mdx` (S4 fatal,
   0xC00000FD ×2).
2. INVESTIGATION: `MiSide/docs/research/s4-crash-investigation.mdx`
   (+ verifier corrections already applied).
3. VERIFIERS: `docs/research/verifications/s4-vA.mdx` (execution proof:
   stock crashes / patched completes, causality isolated) +
   `s4-vB.mdx` (RCA-in-source PASS).
4. FIX SET: `docs/logs/F-CW4.log` + `docs/research/verifications/f-cw4-vA.mdx`
   (PASS, six directives verified at commit 9211ab5).
5. SPEC ERRATA BLOCK under judgment: `MiSide/docs/specs/pipeline-run_all.mdx`
   "Errata 2026-08-24".

## Mission

1. Is the frozen-spec errata legitimate and minimal — reality beat the
   pinned invocation, evidence chain complete (crash → RCA → patched build
   → execution proof → canonicalization)? Or does it smell like an
   undocumented toolchain swap?
2. Does the caveat-persistence design actually protect AC-12/PROOF from
   silently losing the truncation disclosure?
3. Any surviving blocker before resuming full real-install execution (X-2)?
4. Record as debt or demand now: the stale `0.19.0.0` string at
   `test_install_smoke.py:118` (gated tier).

## Deliverable

`MiSide/docs/research/verifications/s4-arbiter.mdx`; final line exactly:
`RULING: ERRATA_APPROVED — resume real-install execution (X-2)` or
`RULING: FIX_LOOP — <numbered fixes>`. ≤10 lines.
