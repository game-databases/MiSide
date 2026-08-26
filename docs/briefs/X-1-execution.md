# Brief X-1 — Executor: first real-install `run_all` execution (MiSide)

You are a fresh Executor subagent launched by the MiSide orchestrator. You
CANNOT spawn other agents. You never run `git` write commands (`git log/diff`
fine). You operate ONLY: the pipeline at
`C:\_reps\game-databases\MiSide\pipeline\` + its shims, workroot
`D:\unpacked_game_data\MiSide\work\`, and your report file. The game root
`A:\SteamLibrary\steamapps\common\MiSide\` is READ-ONLY input — the pipeline
is verified never to write there; if any stage attempts it, abort and report.

## Context

The build wave is fully approved (spec frozen; 4 review rounds; 70-test
suite 66 green black-box; arbiter-cleared). Your job is EXECUTION against
the real client, first time for real data.

## Read first (skim, don't stall)

1. `MiSide/docs/specs/pipeline-run_all.mdx` §2 stage table + §7 risks/
   fallbacks + §8 verify-during-build items.
2. `MiSide/pipeline/README*` / `run_all --help` output.

## Mission

1. Preflight: venv at `D:\unpacked_game_data\MiSide\work\venv` exists with
   pinned deps (C-W1 created it); disk guard per spec; game root present.
   Report anything off before starting.
2. Launch the FULL run detached (nohup … & disown) so it survives you:
   `<shim> run_all --game-root "A:\SteamLibrary\steamapps\common\MiSide"
   D:\unpacked_game_data\MiSide\work` — exact CLI per `--help`.
3. Poll stage reports (`census/stage-reports/*.json`) every few minutes.
   Expected long poles: S3 il2cpp-dump (~minutes), S7 decompile (57
   assemblies — longest), S4 sweep (51 containers). Total budget: hours.
   If a stage FAILS: consult §7 fallbacks; apply the prescribed fallback
   once; if it fails again, STOP and write the incident report — do not
   improvise beyond the spec.
4. While S7 runs, nothing for you to do but wait — do not kill or restart
   healthy stages.
5. On completion (or fatal stop): write
   `C:\_reps\game-databases\MiSide\docs\research\x1-execution-report.mdx`:
   per-stage outcome table w/ wall times, artifact counts vs AC expectations
   (AC-6/7/9/10/13 numbers), EXTRACTION-LOG state, incidents, residue.
   Final line: `EXECUTION: COMPLETE` or `EXECUTION: STOPPED — <stage/reason>`.
   Final message ≤10 lines.

## Rules

- Never modify code/tests to make a stage pass — that's a new finding,
  report it.
- If the run exceeds ~3 h total, write an interim report file and keep
  waiting; the orchestrator polls on cron.
