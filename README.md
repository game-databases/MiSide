# MiSide Database — pack

Game database site pack for **MiSide** (AIHASTO, IndieArk/Shochiku — Steam appid
`2527500`, released 2024-12-10; free **Demo** appid `2527520`; soundtrack DLC
`3404450`). Unity engine, single-player narrative horror.

## Status (2026-08-24, orchestrator pass 2)

| Item | State |
|---|---|
| Client (full game) | **installed on this host** — `A:\SteamLibrary\steamapps\common\MiSide\`, buildId 19029065, Unity 2021.3.35f1 IL2CPP (metadata v29) — measured, see [data-acquisition.md](data-acquisition.md) |
| Client (demo 2527520) | dropped for now (no install; anonymous steamcmd blocked); future diff target only |
| Research | T1 done → [toolchain.md](toolchain.md) + [data-acquisition.md](data-acquisition.md); S1 relaunched (game research + competitor inventory) |
| spec.md | draft pending S1 + pipeline spec |
| extracted/ | none yet — hands-on probe agent E1 verifying the toolchain plan against the real client |
| site/ | blocked behind data layer (AGENTS.md rule 8) |

Binding context: repo-root [`AGENTS.md`](../AGENTS.md),
[`_foundation/extraction-doctrine.md`](../_foundation/extraction-doctrine.md),
[`FRAMEWORK.md`](../FRAMEWORK.md) §7 procedure. Site sections floor:
[`_foundation/site-sections.md`](../_foundation/site-sections.md). Locales:
30 store-listed languages — must be re-verified against the client before
spec freeze (FRAMEWORK §2.4).

## Working files

- `docs/TODO.mdx` — master milestone/task list (≤80 points, kept current).
- `docs/progress.html` — live progress page (open locally).
- `docs/questions.md` — open questions / owner gates.
- `data-acquisition.md`, `toolchain.md`, `competitor-research.md`, `spec.md`,
  `tools-plan.md` — pack conventions per AGENTS.md rule 4 (agent-authored).
- Raw client stays off-repo on this host (`D:\Games\MiSideDemo\`, later full
  game); game data never enters git.
