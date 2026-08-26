# Brief I-T1 — Investigator: acquire the pinned ilspycmd (MiSide I-4)

You are a fresh Investigator subagent launched by the MiSide orchestrator.
You CANNOT spawn other agents. You never run `git` write commands. Work
under `D:\unpacked_game_data\MiSide\work\` (new subdirs `it1-*`); NEVER
write under `A:\SteamLibrary\...`.

## Read first

1. `MiSide/docs/research/x1-execution-report.mdx` — incident I-4: pinned
   zip has only `ILSpy.exe`, no `ilspycmd.exe`; host global ilspycmd is
   8.2.0.7535 ≠ pin 11.0.0.9335-rc; executor refused substitution.
2. `MiSide/docs/specs/pipeline-run_all.mdx` §2 S7 + §8 (what the pin
   requires: exact version, argv shapes).

## Mission

1. Determine the CORRECT distribution channel for ilspycmd 11.0.0.9335-rc
   (it is almost certainly the dotnet tool on nuget — check
   `dotnet tool search ilspycmd` / nuget.org versions via curl). Confirm
   whether that exact version exists there.
2. Acquire it EXACTLY at the pinned version into
   `D:\unpacked_game_data\MiSide\work\tools\IlSpyCmd\` (local tool
   manifest or direct nupkg extraction — your call; document). If the
   pinned version does not exist anywhere, STOP and report the closest
   legitimate version + evidence (do NOT install a different one).
3. Prove it: run it against ONE DummyDll from the workroot's S3 output
   (`--help` first, then a single-assembly decompile to a scratch dir);
   confirm output looks like C# project/source, note wall time.
4. Check how `pipeline/` resolves ilspycmd (read-only): does it point at a
   path the new install satisfies, or does it need a fixer afterwards?
   Report precisely.

## Deliverable

`MiSide/docs/research/ilspycmd-acquisition.mdx`: channel evidence,
install record (paths, versions, hashes if cheap), proof-run result,
pipeline-resolution verdict, and whether the spec pin text needs errata.
Final line: `ACQUISITION: SOLVED — <version@path>` or
`ACQUISITION: BLOCKED — <why>`. ≤12 lines message.
