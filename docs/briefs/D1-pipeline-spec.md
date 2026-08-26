# Brief D1 — PrepareTask Documentator: piece P1 "extraction pipeline run_all" (MiSide)

You are the Documentator subagent launched by the MiSide orchestrator. You
CANNOT spawn other agents — do all work yourself. You never run `git`
commands. You write ONLY `C:\_reps\game-databases\MiSide\docs\specs\pipeline-run_all.mdx`
(read-only everywhere else in the repo; never touch other games' dirs).
You write a SPEC, not code — no implementation in this pass.

## Read before anything else (in full)

1. `C:\_reps\game-databases\AGENTS.md`
2. `C:\_reps\game-databases\_foundation\extraction-doctrine.md` — the three
   mandatory layers, Principle two (PROOF.md), and the
   [DR-2026-08-18-pipeline] single-entrypoint requirements are YOUR outline.
3. `C:\_reps\game-databases\MiSide\toolchain.md` — pinned toolchain plan.
4. `C:\_reps\game-databases\MiSide\data-acquisition.md` — client facts.
5. `C:\_reps\game-databases\MiSide\docs\research\explorer-e1-hands-on.mdx` —
   VERIFIED reality: which commands ran, what broke, exact versions. Your
   spec must follow E1's working invocations, never re-derive them.

## Mission

Write the build-ready spec for piece P1: the pack's extraction pipeline
skeleton + harvest/decompile/loc/art stages, ending at a single
`./run_all <path-to-game-files>` entrypoint at the pack root that satisfies
[DR-2026-08-18-pipeline] (`--help/--list`, idempotent isolated stages,
EXTRACTION-LOG.md pinning). Entity curation/relink/proof are LATER pieces —
spec their boundaries, don't spec their internals ("Non-goals" section).

## Spec must contain

1. **Piece header** — type (feature), affected area (new `pipeline/` tree +
   pack-root entrypoint + `extracted/` outputs), reference counterparts.
2. **Stage table** — every stage: name, inputs, outputs (exact paths under
   `extracted/`), tool invocation copied from E1/toolchain.md verdicts,
   expected runtime, failure behavior. Minimum stages: detect · il2cpp-dump ·
   mono-typed-dump · loc-jsonl · art-export(+MEDIA-CATALOGUE rows) ·
   decompile(main DummyDll via ILSpy/dnSpyEx CLI batch + Voice Editor Managed
   DLLs) · census(PROOF.md source-inventory numbers). Add/remove based on
   evidence, never invention.
3. **File manifest** — every file the CodeWriter will create, one line each,
   with purpose. Python version + venv policy exactly as E1 proved it.
   Windows-first (PowerShell-safe paths; MSYS gotchas noted where real).
4. **Acceptance criteria** — concrete, testable: e.g. "`run_all --list`
   prints N stages"; "re-running any stage twice changes no bytes beyond
   timestamps"; "loc stage emits ≥34 locale dirs × all categories found";
   "census totals reconcile against container byte sums". These become the
   TestWriter's contract — write them as numbered AC IDs.
5. **Test plan sketch** — what the TestWriter should cover per AC
   (smoke runs on tiny fixtures vs full-client runtime budgeting; mark which
   tests may use the real install at A:\ vs synthetic fixture dirs).
6. **Risks & fallbacks** — from E1 findings only.
7. **Open questions** — anything unanswerable from the corpus/docs goes in a
   final section for the orchestrator's question queue (do NOT guess).

## Rules

- MDX-flavored Markdown; anchor cross-links to the docs you cite.
- Every tool claim cites `explorer-e1-hands-on.mdx` or `toolchain.md`;
  anything uncited is `[unverified]`.
- No legality commentary. No invented counts.
- Final message: ≤10 lines — spec path, stage count, AC count, open questions.
