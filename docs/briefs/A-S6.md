# Brief A-S6 — Arbiter: I-3 loc-encoding policy + I-4 toolchain errata (MiSide)

You are a FRESH Arbiter subagent launched by the MiSide orchestrator. You
CANNOT spawn agents. `git log/diff` allowed; never write commands. You
rule; you edit nothing.

## Case file

1. INCIDENTS: `MiSide/docs/research/x1-execution-report.mdx` (I-3, I-4).
2. I-3 EVIDENCE: `MiSide/docs/research/s5-legacy-encoding.mdx` (two failure
   classes; proven cp1250 codec for Slovak/Serbian; 5 unrecoverable line-58
   bytes; phantom skew-ledger finding; recommends option b strict).
3. I-4 EVIDENCE: `MiSide/docs/research/ilspycmd-acquisition.mdx` (nuget
   channel proven at exact pin; local-SDK acquisition; DOTNET_ROOT
   precondition; errata owed re zip contents).
4. SPEC: `MiSide/docs/specs/pipeline-run_all.mdx` §2 S5+S7, AC-9, AC-16;
   FRAMEWORK data-completeness doctrine (`_foundation/extraction-doctrine.md`
   Principles).

## Rulings needed

1. **I-3 policy:** adopt option b strict (decode-with-proven-codec → UTF-8
   rows; U+FFFD + residue entries for the unprovable five; exit 0 when
   every anomaly is recovered-or-marked)? Check it against AC-9 math,
   PROOF/residue doctrine, and honesty rules (does U+FFFD marking keep the
   corpus honest?). Or rule otherwise with reasons.
2. **I-4 errata:** approve spec/toolchain errata stating ilspycmd ships as
   a nuget dotnet-tool (exact pin retained), acquired locally per the
   investigation; require the S7 stage wrapper to inject DOTNET_ROOT for
   AC-16 reproducibility?
3. Any blockers before X-3 resumes S7→S8.

## Deliverable

`MiSide/docs/research/verifications/s6-arbiter.mdx`; final line exactly:
`RULING: APPROVED — implement both, then resume X-3` or
`RULING: PARTIAL — <numbered surviving items>`. ≤12 lines.
