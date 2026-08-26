# Brief F-CW5 — Code Fixer: detect must upsert the full tool-pin block

You are a fresh Fixer subagent launched by the MiSide orchestrator. You
CANNOT spawn agents. You never run `git` commands. Touch ONLY:
`C:\_reps\game-databases\MiSide\pipeline\` EXCEPT `pipeline/tests/`.

## Finding (from F-TW3's heads-up)

The real `D:\unpacked_game_data\MiSide\work\...\EXTRACTION-LOG.md` seeded by
the aborted X-1 run still pins AssetStudioModCLI `0.19.0.0`.
`pipeline/stages/detect.py` `mutate()` upserts only
buildId/unity/metadata/versionLabel — NOT the tool-pin block — and the
stale-log defense compares pipFreeze only. A resumed run would therefore
finish with a stale pin block and false-fail AC-13.

## Fix directive

Make S1/detect's log-seeding logic upsert the ENTIRE pin block from live
resolved tools every run (tool name → resolved version/path), preserving
human-appended sections per the spec's ledger rules. Deterministic rewrite,
not append, consistent with S4 write mode where applicable. Keep it minimal
— no new features beyond making the pin block self-healing.

Smoke: py_compile; `--list` exit 0; if a cheap offline harness exists for
detect seeding, run it; otherwise reason through the upsert path in your
final message. Do NOT touch the live work-root logs (X-2 may be writing).

Final message ≤4 lines.
