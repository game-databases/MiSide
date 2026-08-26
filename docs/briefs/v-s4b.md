# Brief v-s4b — Verifier B on I-S4: RCA + patch + doc integrity (no execution)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` read-only. You verify; you edit nothing. You do NOT re-run tools —
that is v-s4a's job. Your lens: reasoning and artifact integrity.

## Check

1. **RCA soundness:** does the investigation's cycle-chain claim hold in
   source? Verify `ConsoleEditor_HierarchyCase` at `dump.cs:99334`
   actually contains `List<ConsoleEditor_HierarchyCase>` (self-referential),
   and inspect the patch diff in
   `D:\unpacked_game_data\MiSide\work\is4\src\` (`git -C ... diff`/status
   there or read modified files) — is the guard a real recursion guard
   (visited-set/depth) rather than a blanket catch that would silently
   drop data? Flag over-broad guards.
2. **E1 correction:** check its typetree-strip claim against E1's own
   wording — is this a genuine correction or a misreading? Which is right?
3. **detect offset diagnosis:** sanity-check the offset-48 vs offset-0
   claim against `globalgamemanagers` bytes (read first 64 bytes, hex)
   and `pipeline/stages/detect.py`.
4. **Caveat honesty:** cyclic field nested-tail-unexpanded — is it
   ledgered visibly (where?) and does it threaten any AC (esp. AC-8
   custom fields)?
5. **Doc integrity:** matrix.jsonl rows ↔ doc table consistency; no
   claims without a matrix row.

## Deliverable

`docs/research/verifications/s4-vB.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤10 lines.
