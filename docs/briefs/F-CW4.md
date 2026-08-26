# Brief F-CW4 — Code Fixer: land the S4 fix set (MiSide run_all)

You are a fresh Fixer subagent launched by the MiSide orchestrator. You
CANNOT spawn other agents. You never run `git` write commands. Touch ONLY:
`C:\_reps\game-databases\MiSide\pipeline\` (not `pipeline/tests/`),
`C:\_reps\game-databases\MiSide\docs\specs\pipeline-run_all.mdx` (errata
only), `C:\_reps\game-databases\MiSide\docs\research\s4-crash-investigation.mdx`
(verifier-flagged corrections only), and the TOOLS DIRECTORY under
`D:\unpacked_game_data\MiSide\work\tools\` (binary installation, no repo
effect).

## Read first

1. `docs/research/s4-crash-investigation.mdx` — RCA + proven fix
   (patched CLI 0.19.0.1 at
   `D:\unpacked_game_data\MiSide\work\is4\src\AssetStudioCLI\bin\Release\net8.0\win-x64\`,
   source patch @ upstream 6b66ec7, cycle-guard visited-set).
2. Verifier findings: `docs/research/verifications/s4-vB.mdx`
   (3 minor defects incl. unpersisted cyclic-tail caveat) and
   `s4-vA.mdx` (execution proof).

## Fix directives

1. **Canonicalize the tool:** copy the patched publish output into
   `D:\unpacked_game_data\MiSide\work\tools\AssetStudioModCLI\` as the
   resolved version (keep stock 0.19.0 dir intact for provenance); make
   the pipeline's tool resolution pick 0.19.0.1 (path/version pin wherever
   the pipeline currently resolves the CLI — likely common.py/env stage).
   Never reference the `is4` scratch clone from pipeline code.
2. **detect.py offset fix:** read Unity version robustly (string at
   offset 48 after NUL padding in this v22 file — implement per
   investigation's errata wording, e.g. skip leading NULs then read ASCII
   token; must yield `2021.3.35f1`, not "").
3. **Probe-path fallback:** wire `--keep-going` semantics into the S4
   measure-first probe path (`mono_typed_dump.py`) so the §7 fallback is
   actually reachable when a container fails.
4. **Persist the cyclic-tail caveat** into pipeline surfaces so it
   survives to PROOF time: EXTRACTION-LOG seeded event + a census residue
   entry (per AC-12's enumerated-residue pattern) describing the
   truncation-on-recursion behavior of 0.19.0.1.
5. **Spec errata section** (`pipeline-run_all.mdx`): one short "Errata
   2026-08-24" block — tool version 0.19.0 → **0.19.0.1 (cycle-guarded
   rebuild of upstream 6b66ec7)** with one-line why (self-recursive
   `ConsoleEditor_HierarchyCase` vs guardless Cecil recursion; stock
   0xC00000FD), typetree claim correction pointer, detect-offset note.
   Touch nothing else in the frozen spec.
6. **Investigation doc corrections** (verifier v-s4b items): recursion-
   warning count ("exactly 1 each" → level15/level17 have 2); matrix row
   r4 note (txt/xml zeros were rerun-into-populated-dir delta-counting;
   disk holds 1542+1).

Smoke: py_compile touched modules; `--list` exit 0; run ONE cheap stage
smoke you know is safe (e.g. detect-only against a sandbox mini-root if
wired, else skip and say so). Final message ≤8 lines: per-directive result.
