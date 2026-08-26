# Brief E1 — hands-on toolchain probe (MiSide)

You are a hands-on Explorer subagent launched by the MiSide orchestrator.
You CANNOT spawn other agents — do all work yourself. You never run `git`
commands. You touch ONLY `C:\_reps\game-databases\MiSide\` (one findings
file) and the scratch root below; read-only elsewhere in the repo. Never
touch other games' directories.

## Read before anything else

1. `C:\_reps\game-databases\AGENTS.md` — IN FULL (binding repo rules).
2. `C:\_reps\game-databases\_foundation\extraction-doctrine.md` — IN FULL.
3. `C:\_reps\game-databases\MiSide\toolchain.md` — IN FULL (the plan you are
   verifying against reality).
4. `C:\_reps\game-databases\MiSide\data-acquisition.md` — IN FULL (client
   facts: path, buildId 19029065).

## Mission

toolchain.md is a PLAN produced without touching the game. Your job is to
make it REAL: execute its §2 primary path end-to-end on the installed full
game at `A:\SteamLibrary\steamapps\common\MiSide\`, record exactly what
works, what breaks, timings, and artifact counts. You are a probe, not a
pipeline: shallow but real runs of each stage, no polishing.

## Scratch root (all binary outputs go here — NEVER into the repo)

`D:\unpacked_game_data\MiSide\probe-001\`

Create subdirs: `tools\`, `il2cpp\`, `assets\`. The ONLY repo file you write
is the deliverable below.

## Steps (adapt as reality dictates; record every deviation)

1. **Python env** — create a venv (`python -m venv`) under
   `D:\unpacked_game_data\MiSide\probe-001\venv\`; `pip install UnityPy Pillow`.
   Record resolved versions (`pip freeze`). Python 3.14 is on PATH — if
   UnityPy fails to install or import on 3.14, say so precisely and try any
   older `py -3.x` launcher present; record which Python actually works.
2. **Il2CppDumper** — unzip
   `C:\_reps\game-databases\tools\Il2CppDumper\release\Il2CppDumper-net6-win-v6.7.46.zip`
   to scratch `tools\Il2CppDumper\`; run it with `GameAssembly.dll` +
   `MiSideFull_Data\il2cpp_data\Metadata\global-metadata.dat`.
   Git-Bash gotcha: run from a directory you cd'd into; prefer PowerShell or
   cmd for Windows exe invocations with backslash paths. Expect `dump.cs`,
   `DummyDll\`, script outputs in the output dir. Record runtime + output
   file counts + any warnings.
3. **Typed MonoBehaviour dump (probe P1)** — unzip
   `C:\_reps\game-databases\tools\AssetStudioMod\release\AssetStudioModCLI_net8_portable.zip`
   to scratch `tools\AssetStudioModCLI\`; run `-m dump -t monoBehaviour
   --assembly-folder <DummyDll>` over `resources.assets` (96 MB) first.
   Verify field trees are non-empty (not stripped); count dumped objects by
   top type; sample one interesting dump verbatim (~30 lines) into your
   findings.
4. **Container census** — list every SerializedFile-class file under
   `MiSideFull_Data\` (globalgamemanagers*, resources.assets,
   sharedassets0–23, level0–23, .resS/.resource siblings) with byte sizes;
   total them. This becomes source-inventory evidence for PROOF.md later.
5. **Localization sanity** — under `MiSideFull_Data\Data\Languages\`: count
   locale dirs, files per dir; head two category files from English + one
   other locale (first ~5 lines each) to confirm line-based plain text;
   count per-locale Textures png totals. No extraction yet.
6. **Probe P2 inventory** — non-standard extensions anywhere under
   `_Data\` and game root that are NOT standard Unity SerializedFile
   families; list them with sizes.
7. **dump.cs recon** — grep dump.cs for: `BinaryWriter|FileStream`
   (custom-container risk), `Achievement`, `Ending`, `Dialogue`,
   `Cartridge`, `Mita`, scene/location class names, and the loc-loader
   class (what joins `Data/Languages/<locale>/<Category>.txt` lines — the
   join-key authority). Report class names + counts found, short verbatim
   snippets for anything surprising.

## Deliverable

`C:\_reps\game-databases\MiSide\docs\research\explorer-e1-hands-on.mdx`

Structure: verdict per step (WORKS / PARTIAL / FAILS + why), exact commands
used, timings, versions pinned (tool zip names, pip freeze), artifact
counts, deviations from toolchain.md, risks discovered, and a closing
"implications for pipeline spec" section. MDX-flavored Markdown. Every
claim either cites a path/command output or is marked `[unverified]`.

## Rules

- No legality/EULA commentary anywhere — provenance facts only.
- Do not modify the game install. Read-only on A:.
- Disk check before big writes: `Get-Volume` free space on D: (need ~10 GB).
- If a stage hard-fails after 2 honest attempts, mark FAILS with the error
  verbatim and move on — blockers are findings, not walls.
- Final message: ≤15 lines — per-step verdict table + deliverable path.
