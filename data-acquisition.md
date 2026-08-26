# MiSide — data acquisition runbook

Status: PLAN (scout T1) with **measured ground truth from 2026-08-24**. The
headline: the full game is already installed on NE8K; the demo is not.

Binding context: [`../AGENTS.md`](../AGENTS.md) rule 5 (game data never enters
git), [`../_foundation/extraction-doctrine.md`](../_foundation/extraction-doctrine.md),
[`../_foundation/extraction-host.md`](../_foundation/extraction-host.md)
(drive map, write targets). No legality commentary anywhere — provenance facts only.

## Current state: full game INSTALLED

Measured 2026-08-24 on NE8K:

| Fact | Value | Source |
|---|---|---|
| App | MiSide full game, appid **2527500** | `A:\SteamLibrary\steamapps\appmanifest_2527500.acf` |
| State | `StateFlags "4"` = fully installed; `SizeOnDisk 4251911821`; `BytesDownloaded 2205630880` | same acf |
| BuildId | **19029065** (`TargetBuildID` matched before completion) | same acf |
| Installed | 2026-08-24 ~17:26 local (`LastUpdated 1787581990`) | same acf + file mtimes |
| Path | `A:\SteamLibrary\steamapps\common\MiSide\` (exe `MiSideFull.exe`, data `MiSideFull_Data/`) | directory listing |
| Flavor | Unity 2021.3.35f1, IL2CPP metadata v29 | [toolchain.md §1](toolchain.md#1-flavor-detection--result-already-pinned) |

Consequence: acquisition of a playable client is **done** for extraction
purposes. The demo route below stays documented as the low-risk diff target.

### Demo (2527520) — current state

- **No install exists.** Checked 2026-08-24: no `appmanifest_2527520.acf` under
  `C:\Program Files (x86)\Steam\steamapps\`, `A:\SteamLibrary\steamapps\`,
  `B:\SteamLibrary\steamapps\`, or `D:\SteamLibrary\steamapps\`
  (`libraryfolders.vdf` lists exactly those three library roots).
- The steamcmd anonymous attempt left only an empty skeleton:
  `D:\Games\MiSideDemo\steamapps\`, 0 bytes — consistent with anonymous login
  being unable to fetch this app ([unverified] root cause; the tool's own note:
  anonymous works only where allowed — [../tools/README.md](../tools/README.md#steam--distribution-clients)).

How to finish it if needed (in order):

1. **Logged-in Steam client** on NE8K → store page → Install → target the
   A: or D: library. This is how the full game landed.
2. **DepotDownloader with the owner account** (template in §Full game below,
   `-app 2527520`). Requires the owner-gated credentials — reference
   [`../_foundation/credentials.md`](../_foundation/credentials.md) §Steam by
   name only; never copy values here or anywhere else.
3. Record result into `extracted/EXTRACTION-LOG.md` (buildId pinning, §Depot
   recording).

### Full game (2527500)

**Default extraction target = the existing install**
`A:\SteamLibrary\steamapps\common\MiSide\`. Do not re-download for the first
extraction pass.

Fresh/reproducible pull template (patch-day rebuilds, fresh-clone repro):

```bat
:: disk check FIRST (see below); then:
D:\depotdownloader-2.4.6\DepotDownloader.exe ^
  -app 2527500 ^
  -os windows -arch x64 ^
  -username <OWNER_STEAM_ACCOUNT> -password <FROM credentials.md §Steam> ^
  -dir D:\Games\MiSide\
```

- `<OWNER_STEAM_ACCOUNT>` / password / SteamGuard handling live in
  [`../_foundation/credentials.md`](../_foundation/credentials.md) §Steam —
  referenced by name, values never enter any repo file (AGENTS.md rule 5).
  SteamGuard interactive prompt may need an owner-present session; that gate is
  already queued in [docs/questions.md](docs/questions.md).
- Depot list for `-depot <id>` narrowing comes from `app_info 2527500` at run
  time (SteamKit PICS via DepotDownloader's own output) — pin the resolved
  depot ids + manifests into EXTRACTION-LOG.md on first use [unverified until
  first run].
- Target dir convention: `D:\Games\MiSide\` (demo: `D:\Games\MiSideDemo\`).

**Disk-space check step** (mandatory before any download/export):

```powershell
Get-Volume | Where-Object DriveLetter | Select DriveLetter,@{n='FreeGB';e={[math]::Round($_.SizeRemaining/1GB,1)}}
```

Measured 2026-08-24: A: 562.8 free · C: 192.3 · D: 315.9 GiB (D: dropped
~328 GiB since the 2026-08-19 drive-map measurement — re-measure every time;
[extraction-host.md §Drive map](../_foundation/extraction-host.md#drive-map)).
A fresh full-game pull (~4.25 GB staged size per acf `BytesToStage`) fits any
drive; bulk export stages go to D:/A:, never C:.

### Depot/manifest recording (buildId pinning)

After ANY acquisition event append to `extracted/EXTRACTION-LOG.md`:

```jsonc
{ "appid": 2527500, "buildid": "<from appmanifest .acf 'buildid'>",
  "targetBuildID": "<'TargetBuildID'>", "installedDepots": {"<depid>": "<manifest id>"},
  "sizeOnDisk": <bytes>, "source": "steamclient|depotdownloader",
  "path": "A:\\SteamLibrary\\steamapps\\common\\MiSide\\" }
```

Source of truth while installed: the appmanifest itself (read-only). For
pre-download checks, `steamcmd.exe +app_info_print 2527500 +quit` from
[`../tools/steamcmd/`](../tools/README.md#steam--distribution-clients) prints
depots/builds without touching the install.

## Storage & git hygiene

- Raw client stays off-repo where it is (`A:\SteamLibrary\steamapps\common\MiSide\`;
  future pulls `D:\Games\MiSide\`) — never copied into the pack, never committed
  (AGENTS.md rule 5; [extraction-host.md](../_foundation/extraction-host.md#which-machine-holds-the-data)).
- Pack `extracted/` holds **derived data only**: JSONL datasets, decompiled
  trees, relinks, catalogues, PROOF/log artifacts.
- Heavy outputs follow [DR-2026-08-18-media-scope]:
  - audio/video → moved to `D:\game-databases-media-offload\` under their
    repo-relative path with reverse-move `MANIFEST.jsonl`;
  - textures and other heavy classes → catalogue-first
    (`extracted/MEDIA-CATALOGUE.md` + `media-catalogue.jsonl`, counts + bytes),
    owner decides offload after review;
  - oversized JSONL datasets get the same catalogue treatment.
- Known heavy classes already visible: per-locale localized art inside
  `Data/Languages/<locale>/Textures/` (777 png + 3 psd across locales) and
  360 MB total under `Data/Languages/` — expect the texture family to be the
  first catalogue row.

## Update watch

1. **Detect**: read `buildid` from
   `A:\SteamLibrary\steamapps\appmanifest_2527500.acf` (local, instant), cross-
   checked against the public keyless API
   `https://store.steampowered.com/api/appdetails?appids=2527500` when online.
   A changed buildId vs `extracted/EXTRACTION-LOG.md` = patch detected.
2. **Pull**: DepotDownloader template above into `D:\Games\MiSide_<buildid>\`
   (keep the previous build until diffing completes), or let the Steam client
   update in place and rely on DepotDownloader for the old-build manifest.
3. **Rerun**: everything downstream is one command against the new tree —
   `./run_all <path-to-game-files>` at the pack root, stages harvest →
   decompile → loc → art → relink → emit, each idempotent and individually
   runnable ([DR-2026-08-18-pipeline]; planned entrypoint, tracked in
   [docs/TODO.mdx](docs/TODO.mdx)). Patch-day sanity checks are part of stage 1:
   Unity version string, metadata version at offset 4, container census —
   [toolchain.md §1](toolchain.md#1-flavor-detection--result-already-pinned).
4. **Same-commit discipline**: a patch rerun updates the entrypoint +
   EXTRACTION-LOG.md in the same commit ([DR-2026-08-18-pipeline]).

## Open items

- Owner gates unchanged from [README.md](README.md): ownership confirmation is
  now moot for the full game (installed via the logged-in client); SteamGuard
  for headless DepotDownloader remains open for the demo/patch-pull routes.
- First DepotDownloader run must record depot ids + manifest ids (placeholder
  above).

## See also

- [toolchain.md](toolchain.md) — flavor verdict + harvest plan
- [README.md](README.md) — pack status table
