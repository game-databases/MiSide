# Brief I-S4 — Investigator: AssetStudioModCLI 0xC00000FD on MiSide containers

You are a fresh Investigator subagent launched by the MiSide orchestrator.
You CANNOT spawn other agents. You never run `git` write commands. You may
run READ-ONLY diagnostics anywhere, and EXECUTE the external tools against
copies/outputs under `D:\unpacked_game_data\MiSide\work\` or NEW dirs you
create there — NEVER write inside `A:\SteamLibrary\steamapps\common\MiSide\`.

## Read first

1. `MiSide/docs/research/x1-execution-report.mdx` — the incident (probe of
   level1 crashed AssetStudioModCLI 0xC00000FD stack overflow in Cecil
   type-tree recursion, ×2 identical; `--keep-going` fallback failed
   because probe path ignores the flag).
2. `MiSide/docs/specs/pipeline-run_all.mdx` §2 S4 + §7 fallbacks + §8.
3. `MiSide/docs/research/explorer-e1-hands-on.mdx` — E1's successful
   AssetStudioModCLI usage (what worked before, on what inputs).
4. `MiSide/pipeline/stages/mono_typed_dump.py` (read-only).

## Mission — find a WORKING invocation, not opinions

1. Reproduce minimally: run the pinned argv against `level1` alone; confirm
   crash + capture stderr/exit.
2. Hypothesis grid (one variable at a time, log each attempt):
   - Different `-t`/type selection (e.g. drop MonoBehaviour-only filtering,
     narrower/wider sets)
   - Different mode flags (`-m` options in AssetStudioModCLI help)
   - Type-tree related switches (skip/ignore type trees if CLI offers)
   - Container-splitting (feed individual streamed assets vs bundle)
   - Option order (options-after-input pinning interplay)
   Check `AssetStudioModCLI --help` for anything relevant (group/type/
   filter/memory options). Note exact versions (tool + Cecil if visible).
3. For any candidate that completes on level1: verify output shape matches
   what S4 expects (dump dir structure, object count sanity vs census row),
   then try the next-smallest failing container class.
4. Also diagnose the detect Unity-version empty-string read (which file/
   line; what the correct source path/value is — E1 pinned 2021.3.35f1).

## Deliverable

`MiSide/docs/research/s4-crash-investigation.mdx`: reproduction matrix
(argv × result table), root-cause analysis, RECOMMENDED fix as either
(a) corrected pinned invocation + spec errata wording, or (b) code-level
fallback design for the probe path, or both; each with evidence. Final
line: `INVESTIGATION: SOLVED — <one-line fix>` or
`INVESTIGATION: UNSOLVED — <why>`. ≤14 lines total message.
