# Brief F-CW7 — Code Fixer: implement A-S6's I-4 ruling in S7 (decompile)

You are a fresh Fixer subagent launched by the MiSide orchestrator. You
CANNOT spawn agents. You never run `git` commands. Touch ONLY:
`C:\_reps\game-databases\MiSide\pipeline\` EXCEPT `pipeline/tests/`, plus
the spec errata block in
`C:\_reps\game-databases\MiSide\docs\specs\pipeline-run_all.mdx`.

## Read first

1. RULING: `MiSide/docs/research/verifications/s6-arbiter.mdx` (item 2) —
   riders are binding.
2. EVIDENCE: `MiSide/docs/research/ilspycmd-acquisition.mdx` (channel,
   paths, hashes, DOTNET_ROOT precondition).
3. `pipeline/stages/decompile.py` + common.py `_stage_tool`.

## Implement

1. **DOTNET_ROOT in code, not caller env:** S7 stage wrapper resolves the
   local SDK/runtime under `work\it1-dotnet10\` (make the path resolution
   config-driven per existing tool-path patterns) and injects it into the
   child env for ilspycmd spawns. AC-16 reproducibility = no tribal
   knowledge.
2. **Pins block:** add channel + sha256 for the ilspycmd nupkg
   (`9e33…6816` — full hash from the acquisition doc) alongside version pin
   11.0.0.9335-rc; host-global ilspycmd remains refused.
3. **Zip fallback:** retire or tighten the zip-unzip fallback so it can
   never "succeed" with a CLI-less GUI zip again (validate ilspycmd
   presence post-unpack; else fail with the nuget instruction).
4. **Canonical path:** resolve to `work\tools\ILSpy\` (mirror exists);
   keep `IlSpyCmd` as accepted alternate if trivial.
5. **Spec errata:** extend the existing errata block (+2 lines max): S7
   tool channel correction (nuget dotnet-tool at same pin; pinned zip was
   GUI-only), DOTNET_ROOT precondition.

Smoke: py_compile; `--list` exit 0; run decompile stage alone against ONE
DummyDll from workroot S3 output into a scratch dir — expect exit 0 and a
real .cs tree. Report time + file count. Final message ≤6 lines.
