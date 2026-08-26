# Open questions / owner gates — MiSide

Queue per promptForDB ("question queue"); work never stops on other lanes
while these wait.

1. **[x] RESOLVED 2026-08-24 — Full game client (appid 2527500).** The owner's
   logged-in Steam client installed the full game on this machine:
   `A:\SteamLibrary\steamapps\common\MiSide\`, StateFlags 4 (fully installed),
   buildId **19029065** (`appmanifest_2527500.acf`). Extraction target = the
   existing install ([data-acquisition.md](../data-acquisition.md)).
   Remaining sub-item, owner-gated only for the *demo/patch-pull* routes:
   SteamGuard for headless DepotDownloader.
2. **[-] DROPPED 2026-08-24 — Demo install confirmation.** No demo install
   exists anywhere (checked all library roots); the steamcmd anonymous attempt
   left a 0-byte skeleton. Moot: extraction runs against the full client. The
   demo returns only as a future diff target (DepotDownloader + owner
   credentials, folded into question 1's SteamGuard sub-item).
3. **[Q] Site placement (D3 gate)** — MiSide is not yet on the domain-doctrine
   roster (would be product #52+). Default while unruled: build locally,
   placement decided at ship time. No owner action needed now.

## Pipeline-spec questions (raised by D1, ruled by orchestrator 2026-08-24)

4. **[A→RULING] Decompiler pick:** pipeline uses **ILSpy CLI** (`ilspycmd`,
   headless batch project export); dnSpyEx stays interactive-only for spot
   checks. Both are local; only one goes in `run_all`.
5. **[A→RULING] Audio/ogv handling:** the client lives on A:\ as a managed
   Steam install — **the install is never mutated** (no moves, no deletes;
   Steam would flag/repair it). Audio+video stay IN PLACE, catalogued with
   paths+bytes into MEDIA-CATALOGUE / media-catalogue.jsonl; the
   [DR-2026-08-18-media-scope] offload drive applies to pack-held copies,
   which we do not create unless the owner later opts in.
6. **[A→STAGED] Texture-family export scope:** decided at art-export build
   time from the first catalogue row counts (per family, not global —
   sprite-vs-texture2d rule already pinned in toolchain.md §5).
7. **[A→RULING] Voice Editor:** treated as a content source row (probe P7):
   its Mono assemblies decompile in the same decompile stage; its voice-line
   data conventions recorded as evidence in PROOF.md.
8. **[A→RULING] Git tracking policy for `extracted/`:** harvest/,
   decompiled/, art/, media/ stay local-only (`.gitignore` already guards);
   datasets, relinks, logic, contracts, PROOF/VALIDATION/EXTRACTION-LOG
   artifacts commit normally ("only derived artifacts travel",
   extraction-host.md). Owner can widen later.

Answered: Q1 (client acquired by install), Q4–Q8 (rulings above).
Open: Q3 (placement, ship time).

## §9 — Infrastructure escalation (2026-08-25, orchestrator)

**C: hit 0 GB free twice within one hour** (was 192 GB free on Aug 24).
Builder B-6 cleared the Windows Update cache (+3.2 GB) and pip cache;
orchestrator moved MiSide's 12 GB art export to `D:\unpacked_game_data\MiSide\art-export\`.
Remaining suspect: concurrent agents' Temp scratch cycling tens of GB.
C: remains critically low (single-digit GB). Owner attention requested —
risk is cross-pack (any agent's writes can fail at any moment). MiSide
mitigation: all heavy outputs now live on D:; pack-local C: footprint ≈ 1.1 GB
(harvest/decompiled/il2cpp, all regenerable).

### §9 update (2026-08-25 16:05) — SECOND disk emergency same day
C: fell to 1.4 GB again within ~6 h of the first triage (was 192 GB on Aug 24).
MiSide moved ALL remaining regenerable outputs to D: (harvest 938 MB,
decompiled 111 MB, il2cpp 64 MB → D:\unpacked_game_data\MiSide\{harvest,
decompiled,il2cpp}; stubs left behind). Pack C: footprint is now site/
node_modules (~1 GB, required for builds) + docs only. The consumption is
NOT from this pack — concurrent agents' temp scratch is cycling tens of GB.
**Without owner action on machine-level temp hygiene, ANY pack's builds can
fail mid-write.**

### §9 update #2 (2026-08-25 ~16:30) — PROCESS-SAFETY INCIDENT
Reviewer R-SB1 disclosed: its first command was `taskkill //IM node.exe`
with a window-title filter (corrected to port-scoped kill afterwards).
Per its own report, port 3111 is confirmed free and one node.exe survives,
but ANY concurrent session's title-less node processes on NE8K may have
been terminated mid-run around 16:00–16:20. Owner should health-check
sibling packs. Ruled process-safety violation logged; briefs now carry an
explicit "never taskkill by image name" clause going forward.
