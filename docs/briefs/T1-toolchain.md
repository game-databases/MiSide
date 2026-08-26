# Brief T1 — Unity toolchain scout + acquisition runbook (MiSide)

You are a toolchain research subagent launched by the MiSide orchestrator.
You CANNOT spawn other agents — do all work yourself. Write ONLY inside
`C:\_reps\game-databases\MiSide\` (two deliverables below); read-only
elsewhere in the repo. Never touch other games' directories. Never run git
commands. Never download or execute any extraction on a real game yet — this
pass produces the PLAN files only.

## Read before anything else

1. `C:\_reps\game-databases\AGENTS.md` — IN FULL (binding repo rules).
2. `C:\_reps\game-databases\_foundation\extraction-doctrine.md` — IN FULL.
   Your plan must implement its three layers + PROOF.md + single-entrypoint
   pipeline requirements.
3. `C:\_reps\game-databases\_foundation\extraction-host.md` — IN FULL (we are
   ON NE8K; drive map; where to write; git-over-ssh caveat irrelevant here but
   read it).
4. `C:\_reps\game-databases\tools\README.md` — the tools index (read fully).
5. `C:\_reps\game-databases\game-unpacking-knowledge-base-and-guides\unity\`
   — walk BOTH `works/` and `does-not-work/`; these encode hard-won lessons.
6. `C:\_reps\game-databases\MiSide\README.md`.

## Established facts

Game: **MiSide**, Steam appid 2527500 (full), **2527520** (free Demo),
soundtrack DLC 3404450. Unity engine, Windows-only, released 2024-12-10,
AIHASTO / IndieArk+Shochiku. 30 store locales. A demo install was requested
via the logged-in Steam client → expect it under one of the Steam libraries
(check `/a/SteamLibrary/steamapps/appmanifest_2527520.acf`,
`/d/SteamLibrary/steamapps/`, and
`C:\Program Files (x86)\Steam\steamapps\`) — you may CHECK for it and note
what you find, but do not extract anything yet.

## Deliverable 1 — `toolchain.md` (pack root)

A pinned toolchain plan covering:

1. **Flavor detection first**: exact steps to determine Unity version,
   Mono vs IL2CPP, global-metadata presence, from a fresh install dir
   (`MiSide_Demo.exe`, `MiSide_Demo_Data/`, `il2cpp_data`,
   `GameAssembly.dll`, `globalgamemanagers`, `level0`…). Include what each
   detection result changes downstream.
2. **Raw harvest path** per flavor:
   - Mono → AssetRipper full export + AssetStudioMod spot checks;
   - IL2Cpp → Il2CppDumper / Zygisk-Il2CppDumper / Cpp2IL order of operations
     to get dummy DLLs, then AssetRipper with them.
   Name the local tool dirs under `C:\_reps\game-databases\tools\` you'd use
   and how you'd pin their versions (EXTRACTION-LOG discipline).
3. **Script decompile**: dnSpyEx/ILSpy for Mono assemblies vs decompiled
   IL2CPP output; where class hierarchies + reference graphs come from
   (doctrine: code structure is data too).
4. **Localization tables**: how Unity stores loc (Unity Localization package
   tables vs I2 Localization vs raw assets); the plan to enumerate ALL locale
   tables and emit per-locale JSONL keyed by stable ids; verify the 30 store
   languages against what's actually in the build.
5. **Art export policy**: 2D textures/sprites/UI atlas YES (webp conversion
   plan); audio/video NO (catalogue-only, offload per
   [DR-2026-08-18-media-scope]); 3D models/animations catalogue-only
   (MEDIA-CATALOGUE.md). Name the export/conversion tools present locally.
6. **Known pitfalls** from the knowledge base unity folders that could apply
   here, each cited as `path#heading`.
7. Open risks with concrete probe steps.

## Deliverable 2 — `data-acquisition.md` (pack root)

The acquisition runbook:

1. **Demo (2527520)** — current state of the install request; how to finish
   it if the Steam GUI route stalls; expected install locations on NE8K;
   depot/manifest recording method (buildId pinning into EXTRACTION-LOG.md).
2. **Full game (2527500)** — DepotDownloader command template (from
   `D:\depotdownloader-2.4.6\DepotDownloader.exe`) with placeholders for the
   owner-gated credentials (reference `_foundation/credentials.md` §Steam by
   name only — NEVER copy credential values into your file); target dir
   convention `D:\Games\MiSide\`; disk-space check step.
3. **Storage & git hygiene**: raw client stays off-repo on D:/A:;
   `extracted/` inside the pack holds derived data only; game data never
   enters git (AGENTS rule 5). Note which outputs are heavy enough to need
   the media-offload drive per doctrine.
4. **Update watch**: how a future patch is detected (Steam buildId via
   appmanifest `buildid` / public API) and what reruns ([DR-2026-08-18-pipeline]
   one-command repro requirement — reference the planned `run_all`).

## Rules

- No legality/EULA commentary anywhere (repo rule 2) — provenance facts only.
- MDX-flavored Markdown, tight cross-links, every claim either cites a local
  file path or is marked `[unverified]`.
- Do not invent tool versions — cite what exists in `tools/` (list actual
  directory names); version numbers only if readable from the tool dirs.
- Final message: ≤15 lines — chosen primary path per flavor, top 3 risks,
  both file paths.
