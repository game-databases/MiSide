# MiSide — pinned toolchain plan

Status: PLAN (scout T1). Nothing extracted yet. Client facts below were
measured 2026-08-24 on NE8K against the installed full game — see
[data-acquisition.md](data-acquisition.md#current-state-full-game-installed).

Binding context: [`../AGENTS.md`](../AGENTS.md),
[`../_foundation/extraction-doctrine.md`](../_foundation/extraction-doctrine.md),
[`../tools/README.md`](../tools/README.md).

## 1. Flavor detection — result already pinned

| Probe | Result | Consequence |
|---|---|---|
| Engine | Unity — `UnityPlayer.dll`, `baselib.dll`, `*_Data/` layout | Unity tool path |
| Unity version | **2021.3.35f1** (string at head of `MiSideFull_Data/globalgamemanagers`) | Pre-Unity-6 formats; all local tools cover it |
| Scripting backend | **IL2CPP** — `GameAssembly.dll` (22,411,776 B) at game root | Il2CppDumper route; no Mono assemblies in the main game |
| `global-metadata.dat` | Present at `MiSideFull_Data/il2cpp_data/Metadata/global-metadata.dat`, 5,173,460 B | Required input for the dumper |
| Metadata version | **29** (u32 LE at offset 4) | ≤ v31 → off-the-shelf Il2CppDumper works; no Cpp2IL-from-source detour ([pitfall #1](#7-known-pitfalls)) |
| Player data | `globalgamemanagers` (780 KB) + `globalgamemanagers.assets`, `resources.assets` (96 MB), `sharedassets0–23.assets(.resS/.resource)`, `level0–23` | SerializedFile corpus for UnityPy/AssetStudioMod |
| StreamingAssets | Absent | No Addressables catalog; container map lives in `globalgamemanagers` |
| Second app | `Voice Editor/Miside Voice Editor.exe` ships **Mono** assemblies (`Miside Voice Editor_Data/Managed/Assembly-CSharp.dll`) | Free decompile target — see §3 |

### Detection procedure (fresh install / demo / patch day)

Run top-down; stop at the first backend verdict:

1. Game root inventory: `<Game>.exe`, `*_Data/`, presence of `GameAssembly.dll`.
   `GameAssembly.dll` ⇒ IL2CPP; `*_Data/Managed/*.dll` ⇒ Mono. Both can coexist
   when a publisher ships a secondary tool (MiSide's Voice Editor is Mono inside
   an IL2CPP game).
2. IL2CPP: read u32 LE at offset 4 of
   `*_Data/il2cpp_data/Metadata/global-metadata.dat` → metadata version. This one
   number redirects the whole dumper choice
   ([does-not-work/il2cppdumper-new-metadata.md](../game-unpacking-knowledge-base-and-guides/unity/does-not-work/il2cppdumper-new-metadata.md#5-applying-it-to-another-unity-game)).
3. Unity version: leading string of `globalgamemanagers` (or `*_Data/app.info`
   for company/product).
4. Container census: count `resources.assets`, `sharedassetsN.assets`,
   `levelN`, any UnityFS bundles, `.resS` stream siblings — this becomes the
   source inventory of `extracted/PROOF.md`
   ([doctrine §Principle two](../_foundation/extraction-doctrine.md#principle-two-completeness-is-proven-not-claimed)).

What each verdict changes downstream: **IL2CPP** → dummy-DLL step before asset
typing (§2); **Mono** → point tools straight at `Managed/` and skip the dump
step; **metadata >31** → swap Il2CppDumper for Cpp2IL prerelease-21 or
MelonLoader interop ([works/il2cpp-interop-melonloader.md](../game-unpacking-knowledge-base-and-guides/unity/works/il2cpp-interop-melonloader.md#6-applying-it-to-another-unity-game));
**Addressables present** → read the name→asset table from `catalog_*.json`
instead of ResourceManager
([works/unitypy-asset-ripping.md#6-applying-it-to-another-unity-game](../game-unpacking-knowledge-base-and-guides/unity/works/unitypy-asset-ripping.md#6-applying-it-to-another-unity-game)).
MiSide hits none of the three exceptions.

## 2. Raw harvest path

### Primary (IL2CPP, static — matches detected flavor)

1. **Il2CppDumper** — `C:\_reps\game-databases\tools\Il2CppDumper\release\Il2CppDumper-net6-win-v6.7.46.zip`
   (version readable from the artifact name). Inputs:
   `GameAssembly.dll` + `global-metadata.dat`. Outputs: `dump.cs`,
   `DummyDll/`, IDA/Ghidra scripts. Metadata v29 is inside its supported
   ≤ v31 range — the exact failure documented for v38/v39 does not apply here
   ([does-not-work/il2cppdumper-new-metadata.md](../game-unpacking-knowledge-base-and-guides/unity/does-not-work/il2cppdumper-new-metadata.md#1-what-you-tried--why-it-seemed-promising)).
   Git-Bash gotcha: set cwd to the output dir before invoking; MSYS mangles
   path args ([works/unity6-il2cpp-monobehaviour-pipeline.md](../game-unpacking-knowledge-base-and-guides/unity/works/unity6-il2cpp-monobehaviour-pipeline.md#the-pipeline-that-works)).
2. **Typed MonoBehaviour dumps** — `AssetStudioModCLI_net8_portable.zip` from
   `tools\AssetStudioMod\release\` (v0.19.0 per
   [works/unity6-il2cpp-monobehaviour-pipeline.md](../game-unpacking-knowledge-base-and-guides/unity/works/unity6-il2cpp-monobehaviour-pipeline.md#the-pipeline-that-works);
   version not printed by the zip name — confirm at unpack):
   `-m dump -t monoBehaviour --assembly-folder <DummyDll>` for typed text
   dumps, `-m export -t sprite,tex2d` for images,
   `--export-asset-list xml` for the name/pathid/source crosswalk that later
   resolves PPtrs. Text-dump quirks (tab indent, continuation lines, binary
   residue after NUL, array shape) are catalogued and handled in the Lootbound
   parser pattern
   ([works/unity6-il2cpp-monobehaviour-pipeline.md#assetstudiomodcli-text-dump-quirks-all-handled-in-lootboundtoolsparse_dumpspy](../game-unpacking-knowledge-base-and-guides/unity/works/unity6-il2cpp-monobehaviour-pipeline.md#assetstudiomodcli-text-dump-quirks-all-handled-in-lootboundtoolsparse_dumpspy)).
3. **Bulk/batch layer — UnityPy** (`tools\UnityPy\`, source clone; pin the
   installed version into `extracted/EXTRACTION-LOG.md` via `pip freeze`;
   Corepunk used 1.25.2 successfully on newer assets). Programmatic backbone:
   dump the ResourceManager `m_Container` from `globalgamemanagers` once to a
   path→(fileID,pathID) index, group by fileID, load each big file once
   ([works/unitypy-asset-ripping.md#2-general-approach](../game-unpacking-knowledge-base-and-guides/unity/works/unitypy-asset-ripping.md#2-general-approach)).
   Python 3.14.7 is on PATH; UnityPy/Pillow are **not installed yet** (import
   verified failing 2026-08-24) — first pipeline stage creates the pack venv.
4. **Spot checks** — UABEA (`tools\UABEA\release\uabea-windows.zip`) /
   AssetStudioMod GUI for eyeballing individual objects. Interactive use only.

### Secondary (Mono sub-app)

The shipped Voice Editor is Mono: `dnSpyEx` opens
`Voice Editor/Miside Voice Editor_Data/Managed/Assembly-CSharp.dll` directly —
no dump step. Its code names the voice-line/loc file conventions the main game
consumes through `Data/`.

### Not applicable here

- Zygisk-Il2CppDumper / Zygisk-Il2CppFucker (`tools\`) are Android-runtime
  dumpers — wrong platform for this Windows build.
- MelonLoader runtime interop is **not needed** while metadata stays ≤ v31, and
  is **not present locally** — opening that route is a new acquisition plus an
  injection decision; keep it as escalation only (§9).

## 3. Script decompile

- Main game: decompile `DummyDll/` from step 2 with **dnSpyEx**
  (`tools\dnSpyEx\release\dnSpy-net-win64.zip`) or **ILSpy**
  (`tools\ILSpy\release\ILSpy_windows_selfcontained_11.0.0.9335-rc-x64.zip`).
- Expect correct *structure* (fields, offsets, signatures, constants) and
  garbage-prone *bodies* in call-heavy serializers — take structure, get
  semantics from data/runtime instead
  ([does-not-work/decompiler-method-bodies.md#5-applying-it-to-another-unity-game](../game-unpacking-knowledge-base-and-guides/unity/does-not-work/decompiler-method-bodies.md#5-applying-it-to-another-unity-game)).
- Doctrine requires code structure as data: emit class hierarchies +
  reference graphs alongside the raw decompile under `extracted/decompiled/`
  ([doctrine §Logic layer](../_foundation/extraction-doctrine.md#the-three-mandatory-layers)).
  Source: `dump.cs` + DummyDll (main game), `Managed/*.dll` (Voice Editor);
  graph extraction via ILSpy/dnSpyEx project export + a script pass.
- MiSide's gameplay data appears to live largely in Unity assets/SerializedFiles
  rather than a custom binary container [unverified — probe P2], so the
  Corepunk-style custom-container reversal
  ([works/static-container-reversal.md](../game-unpacking-knowledge-base-and-guides/unity/works/static-container-reversal.md))
  is contingency, not baseline.

## 4. Localization

Observed store (2026-08-24): the game ships a **custom loose-file loc system**,
not the Unity Localization package:

```
<Data root>\Data\Languages\<locale>\<Category>.txt   # 34 locale dirs, ~66 files each, 2,210 txt total
<Data root>\Data\Languages\<locale>\Textures\...     # per-locale localized art: 777 png + 3 psd
<Data root>\Data\Languages\<locale>\Font ...         # per-locale font files
```

Locale dirs (34): Arabic, Arabic (Egyptian), Belarusian, Bulgarian,
ChineseSimplified, ChineseTraditional, Croatian, Czech, English, Filipino,
French, German, Hungarian, Indonesia, Italian, Japanese, Kazakh, Korean,
Persian, Polish, Portugues Portugal, Português-Brasil,
Pre-revolutionaryRussian, Romanian, Russian, Serbian (Latin), Slovak,
Spanish (LatinAmerica), Spanish (Spain), Swedish, Thai, Turkish, Ukrainian,
Vietnamese. Files are line-based plain text (e.g. `Achievements.txt` = one
display string per line) — ids must come from **category + line index**, which
makes the decompiled loader the authority for the join key (§3).

Plan:

1. Enumerate ALL categories × locales; emit `extracted/localization/<locale>/<category>.jsonl`
   keyed `{category, line_index, text}` preserving verbatim bytes (UTF-8,
   record odd chars — do not normalize;
   [works/localization-xml.md#5-gotchas--pitfalls](../game-unpacking-knowledge-base-and-guides/unity/works/localization-xml.md#5-gotchas--pitfalls)).
2. Reconcile **34 present vs 30 store-listed** like Corepunk's registered-vs-
   present split — ship the present set, ledger the delta explicitly, never
   paper over it
   ([works/localization-xml.md#the-locale-set](../game-unpacking-knowledge-base-and-guides/unity/works/localization-xml.md#the-locale-set)).
   Store list: Steam appdetails `supported_languages` for 2527500 [probe P4].
3. Per-locale `Textures/` + fonts flow through the art policy (§5); they are
   part of localization, not droppable extras.
4. Probe for a second loc layer inside `resources.assets`/bundles (SharedTableData/
   StringTable-style). If found, recover via id-anchor byte slicing — AssetStudioMod
   renders those managed arrays empty
   ([works/unity6-il2cpp-monobehaviour-pipeline.md#sharedtabledata--stringtable-recovery-unity-localization](../game-unpacking-knowledge-base-and-guides/unity/works/unity6-il2cpp-monobehaviour-pipeline.md#sharedtabledata--stringtable-recovery-unity-localization)).
   `UnityEngine.LocalizationModule.dll` in `ScriptingAssemblies.json` is a stock
  module and is NOT evidence of package usage [unverified — probe P3].
5. Cross-check: resolved English strings appearing inside dumped MonoBehaviours
   confirms/refutes the line-index join hypothesis
   ([works/localization-xml.md#5-gotchas--pitfalls](../game-unpacking-knowledge-base-and-guides/unity/works/localization-xml.md#5-gotchas--pitfalls)).

## 5. Art export policy

Per [DR-2026-08-18-media-scope]
([decision-register](../_foundation/decision-register.md#owner-ruling--videoaudio-offloaded-3d-and-heavy-assets-catalogue-first-dr-2026-08-18-media-scope)):

| Class | Policy | Tooling present locally |
|---|---|---|
| 2D textures/sprites/UI atlases (+ per-locale Textures) | **Export** → PNG (AssetStudioMod `-t sprite,tex2d`; UnityPy `Sprite.image` for atlas sub-rects) → WebP conversion | WebP encode: **Pillow** in the pack venv (planned). `tools\DirectXTex\release\texconv.exe` covers DDS/TIFF/BMP/PNG but has no WebP encoder; `tools\Noesis\` v4.474 for odd-format previews |
| Audio (voice lines, music) | **NO export** — catalogue + offload to `D:\game-database-media-offload\` with reverse-move manifest | catalogue emitted by pipeline; no audio tool in scope ([tools README scope](../tools/README.md#scope)) |
| Video | Same as audio | — |
| 3D models/animations | **Catalogue-first**: counts + bytes into `extracted/MEDIA-CATALOGUE.md` + `media-catalogue.jsonl`; owner decides keep/offload | AssetStudioMod mesh export capable; Noesis for conversion if owner opts in |

Sprite-vs-Texture2D preference is context-dependent (UI icons want Sprite crop;
tile sheets want Texture2D) — bake the rule per asset family, not globally
([works/unitypy-asset-ripping.md#5-gotchas--pitfalls](../game-unpacking-knowledge-base-and-guides/unity/works/unitypy-asset-ripping.md#5-gotchas--pitfalls)).
`Data/Custom/*.png` (character templates) ship loose and copy through verbatim
as raw-layer artifacts.

### Full deconstruction scope (doctrine-required section)

Mapping the three mandatory layers onto MiSide (single-player narrative horror,
Unity 2021.3 IL2CPP):

1. **Data layer** — canonical JSONL per entity type discovered in assets
   (characters/Mitas, items/interactables, achievements, locations/scenes,
   endings, dialogue/dialogue-graph nodes, settings presets), all locales from
   §4, icons/sprites from §5.
2. **Logic layer** — decompiled assemblies under `extracted/decompiled/`
   (+ hierarchy/reference graphs); derived `extracted/logic/`: scene→ending
   conditions, event/trigger branches, achievement unlock predicates, dialogue
   routing, minigame rules — whatever the assemblies actually encode; recorded
   honestly where logic is hardcoded in scene data instead.
3. **Relink layer** — `extracted/relinks/` pairwise matrix, minimum pairs:
   entity↔scene, entity↔dialogue-node, entity↔achievement, entity↔loc-key,
   entity↔icon/texture (incl. per-locale variants), scene↔ending; hard refs
   marked `inferred:false`, derived ones `inferred:true` + method
   ([doctrine §Principle one](../_foundation/extraction-doctrine.md#principle-one-relations-are-the-database)).
4. **Protocol section** — single-player: prove/inventory the surface (Steam
   cloud saves, achievements, telemetry endpoints seen in assemblies) in
   PROOF.md ([doctrine §Protocol layer](../_foundation/extraction-doctrine.md#protocol-layer-clientserver-reconstruction)).

## 6. Version pinning (EXTRACTION-LOG discipline)

Every run records into `extracted/EXTRACTION-LOG.md`: client buildId
(**19029065** for the current install), tool dir + release artifact filename +
any version file (e.g. `tools\AssetRipper\release\compile_time.txt` =
`Sat Apr 25 18:52:46 UTC 2026`), Python env `pip freeze`, and the entrypoint
commit. The planned `run_all` reads its defaults from that log
([DR-2026-08-18-pipeline]).

## 7. Known pitfalls (pre-loaded from the knowledge base)

1. **Metadata-version gate** — always read offset 4 before choosing a dumper;
   tools pinned old fail loudly there, and the fix is a format-current reader.
   [unity/does-not-work/il2cppdumper-new-metadata.md](../game-unpacking-knowledge-base-and-guides/unity/does-not-work/il2cppdumper-new-metadata.md)
2. **No headless AssetRipper** — batch asset work goes through UnityPy/
   AssetStudioModCLI; the GUI Free build also drops loaded collections on
   LoadFolder and exports no MonoBehaviour fields without assemblies.
   [unity/does-not-work/assetripper-gui.md](../game-unpacking-knowledge-base-and-guides/unity/does-not-work/assetripper-gui.md#4-do-this-instead) ·
   [unity/works/unity6-il2cpp-monobehaviour-pipeline.md#tooling-that-does-not-work-here](../game-unpacking-knowledge-base-and-guides/unity/works/unity6-il2cpp-monobehaviour-pipeline.md#tooling-that-does-not-work-here)
3. **Decompiler bodies ≠ wire truth** — structure yes, bodies no; decode
   black-box or go runtime. [unity/does-not-work/decompiler-method-bodies.md](../game-unpacking-knowledge-base-and-guides/unity/does-not-work/decompiler-method-bodies.md)
4. **Registered ≠ present locale sets** — decide the shipped locale set
   deliberately and assert it in validation. [unity/works/localization-xml.md#the-locale-set](../game-unpacking-knowledge-base-and-guides/unity/works/localization-xml.md#the-locale-set)
5. **Loc join keys are per-category puzzles** — expect at least one opaque/
   computed key scheme; resolve it from code, not guesswork.
   [unity/works/localization-xml.md#5-gotchas--pitfalls](../game-unpacking-knowledge-base-and-guides/unity/works/localization-xml.md#5-gotchas--pitfalls)
6. **Sprite vs Texture2D inversion** between icons and tile sheets.
   [unity/works/sprites-minimap.md#5-gotchas--pitfalls](../game-unpacking-knowledge-base-and-guides/unity/works/sprites-minimap.md#5-gotchas--pitfalls)
7. **Container-map hygiene** — lowercased paths, stale refs exist game-side,
   load multi-GB files exactly once. [unity/works/unitypy-asset-ripping.md#5-gotchas--pitfalls](../game-unpacking-knowledge-base-and-guides/unity/works/unitypy-asset-ripping.md#5-gotchas--pitfalls)
8. **MSYS path mangling** when driving Windows exes from Git Bash (cwd trick,
   `MSYS2_ARG_CONV_EXCL='*'`). [unity/works/unity6-il2cpp-monobehaviour-pipeline.md](../game-unpacking-knowledge-base-and-guides/unity/works/unity6-il2cpp-monobehaviour-pipeline.md#the-pipeline-that-works) ·
   [unity/works/runtime-reserialization.md#3c-build-deploy-run](../game-unpacking-knowledge-base-and-guides/unity/works/runtime-reserialization.md#3c-build-deploy-run)

## 8. Open risks → probes

| # | Risk | Probe (cheap first) |
|---|---|---|
| P1 | Gameplay balance/config may sit in serialized MonoBehaviours with stripped type trees | After §2 step 1: AssetStudioMod `-m dump -t monoBehaviour --assembly-folder DummyDll` on `resources.assets`; verify non-empty field trees |
| P2 | Custom binary containers may exist besides Unity assets (save format, minigame data) | Inventory non-standard extensions under `_Data/` + game root; grep `dump.cs` for `BinaryWriter`/`FileStream` writers |
| P3 | Hidden Unity-Localization tables inside assets | Scan `--export-asset-list xml` for SharedTableData/StringTable types; if present, apply id-anchor recovery |
| P4 | Locale-set mismatch vs store's 30 languages | Pull `appdetails` `supported_languages` (public API, keyless) and diff against the 34 dirs |
| P5 | Dialogue/scene graphs may be encoded in scene files (level0–23), not prefabs — heavier parse | Dump one `levelN` first, measure object/type mix before committing to a parser design |
| P6 | Patch changes metadata version (>31) on a future update | Update-watch reruns the §1 detection; bump handled by Cpp2IL prerelease-21 locally (`tools\Cpp2IL\release\prerelease21-*`) |
| P7 | Voice Editor app is itself content (voice-line DB) | Treat its `*_Data` as a second source inventory row in PROOF.md, not just a code source |

## See also

- [data-acquisition.md](data-acquisition.md) — how the client gets/pulls onto disk
- [README.md](README.md) — pack status
- [../game-unpacking-knowledge-base-and-guides/unity/README.md](../game-unpacking-knowledge-base-and-guides/unity/README.md) — works/dead-end index
