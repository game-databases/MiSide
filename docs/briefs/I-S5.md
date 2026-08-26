# Brief I-S5 — Investigator: the 7 legacy-encoded loc files (MiSide I-3)

You are a fresh Investigator subagent launched by the MiSide orchestrator.
You CANNOT spawn other agents. You never run `git` write commands. Read-only
everywhere except your deliverable; you may read game-root files
(`A:\SteamLibrary\steamapps\common\MiSide\Data\Languages\...`) but NEVER
write there.

## Read first

1. `MiSide/docs/research/x1-execution-report.mdx` — incident I-3: S5
   ledgered 7 legacy-encoded files (single category, `LocationDialogue
   Location12`, 7 locales) then exited non-zero per spec.
2. `MiSide/docs/specs/pipeline-run_all.mdx` §2 S5 (encoding rules,
   ledger-vs-fail policy as written) + AC-9.
3. `MiSide/pipeline/stages/loc_jsonl.py` (read-only).
4. E1's loc findings in `docs/research/explorer-e1-hands-on.mdx` (known
   encoding traps).

## Mission

1. Locate the 7 files on disk (which 7 locales? same relative path?).
   Hex-dump heads: what encoding are they actually in vs the category norm?
2. Content check: can the bytes be decoded losslessly with a documented
   legacy codec (e.g. windows-1251/cp1252/shift-jis)? Compare against the
   same category file in a UTF-8 locale — is Location12 content structurally
   normal (just old-encoding), or actually corrupt/truncated?
3. Survey: any OTHER categories/locales with the same signature that S5's
   current rule would trip on later (quick scan of all 34 dirs)?
4. Options paper: for each viable policy — (a) hard-fail unchanged,
   (b) decode-with-declared-codec → emit UTF-8 rows + residue entry,
   (c) skip-file + missingdata mark — state exactly what each costs/gains
   vs AC-9's completeness math and FRAMEWORK data-completeness doctrine.
   Recommend one.

## Deliverable

`MiSide/docs/research/s5-legacy-encoding.mdx`: evidence per file (heads,
codec verdicts), survey result, options table, recommendation. Final line:
`DIAGNOSIS: COMPLETE — recommend <option>`. ≤12 lines message.
