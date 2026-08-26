# Brief v-s4a — Verifier A on I-S4: re-execute the evidence (MiSide S4 crash fix)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` read-only. You may run the tools against sandbox copies under
`D:\unpacked_game_data\MiSide\work\` (new subdirs `v-s4a-*`); NEVER write
under `A:\SteamLibrary\...`. You verify; you edit nothing.

## Check

`C:\_reps\game-databases\MiSide\docs\research\s4-crash-investigation.mdx`
claims, with a patched CLI built at
`D:\unpacked_game_data\MiSide\work\is4\src\AssetStudioCLI\bin\Release\net8.0\win-x64\AssetStudioModCLI.exe`
(0.19.0.1 cycle-guard):

1. **Poisoned probe:** re-run the pinned argv with THAT binary on
   `level1` — expect clean completion, typed dump count ≈1542.
2. **Stock still crashes:** same argv with stock 0.19.0 at
   `work\tools\AssetStudioModCLI\...\AssetStudioModCLI.exe` — expect
   0xC00000FD. This proves causality, not coincidence.
3. **Sweep claim spot-check:** re-run ONE mid-size container from the
   investigation's sweep list with the patched binary; confirm 0 failures
   and plausible dump count vs its census row.

Report actual numbers/exit codes per attempt.

## Deliverable

`docs/research/verifications/s4-vA.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤10 lines.
