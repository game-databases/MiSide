# Brief X-3 — Executor: final resume to completion (MiSide run_all)

You are a fresh Executor subagent launched by the MiSide orchestrator. You
CANNOT spawn agents. You never run `git` write commands. Operate ONLY:
pipeline + shims at `C:\_reps\game-databases\MiSide\`, workroot
`D:\unpacked_game_data\MiSide\work\`, your report file. Game root
`A:\SteamLibrary\...` read-only; abort if any stage attempts writes there.

## Context

S1–S6 green on real data (X-2). Two rulings implemented and verified:
S5 option-b strict codec policy (`docs/research/verifications/s6-arbiter.mdx`,
`f-cw67-vA.mdx`); S7 nuget ilspycmd 11.0.0.9335-rc w/ DOTNET_ROOT-in-code.
All committed.

## Binding resume order (A-S6)

1. Rerun **S5 alone** first (`--stage loc-jsonl` or equivalent): expect
   exit 0, emitted==walked==2,210, residue ledger present.
2. Then `--from decompile --to census` slice: S7 batch over main DummyDlls
   + Voice Editor Managed + `_structure/` graphs, then S8 census +
   EXTRACTION-LOG/PROOF seeding. Long pole: S7 (~tens of minutes).
3. On any FAIL: apply the §7-prescribed fallback once; if it repeats,
   STOP and report — no improvisation.

## Deliverable

Update `C:\_reps\game-databases\MiSide\docs\research\x1-execution-report.mdx`
with a "Round 3" section: per-stage outcomes + wall times, AC scoreboard
(AC-1…16, expected-red where install-gated), census totals vs AC-10/AC-12,
EXTRACTION-LOG pin state (must show healed 0.19.0.1 + ilspycmd channel),
residue summary incl. encoding marks. Final line:
`EXECUTION: COMPLETE — all stages green` or
`EXECUTION: STOPPED — <stage/reason>`. Final message ≤10 lines.
