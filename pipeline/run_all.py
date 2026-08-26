#!/usr/bin/env python3
"""MiSide `run_all` driver — single-entrypoint extraction pipeline (P1).

Contract: docs/specs/pipeline-run_all.mdx. Stdlib argparse; no third-party
imports here (UnityPy/Pillow live in the pack venv and are only ever loaded
inside venv child processes).

Exit codes: 0 ok · 2 usage error · 3 stage failure (failed stage named on
stderr) · 4 missing dependency outputs (run the earlier stage first).
"""

import sys
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[1]
if str(PACK_ROOT) not in sys.path:
    sys.path.insert(0, str(PACK_ROOT))

from pipeline import common  # noqa: E402
from pipeline.stages import STAGES, deps_of, description_of, load_stage, stage_names  # noqa: E402

EXIT_OK, EXIT_USAGE, EXIT_STAGE, EXIT_DEPS = 0, 2, 3, 4

EPILOG = """\
argument semantics:
  <game-root> is the GAME ROOT — the directory holding MiSideFull.exe,
  MiSideFull_Data\\ AND the loose Data\\ tree (the loc store lives there,
  at game root — not inside *_Data). The install itself is never written to.

stage selection:
  (none)                  all eight stages in registry order
  --stage NAME [--stage]  exactly those stages, in registry order
  --from NAME --to NAME   inclusive registry slice
  (--stage does not combine with --from/--to)

per-stage flags:
  --keep-going   S4 mono-typed-dump / S7 decompile: a failed container or
                 assembly is ledgered into census/sweep-attempts.jsonl or the
                 stage report and the run continues, instead of FAIL-FAST.
  --expect-drift S2 detect: accept a container-census total that differs from
                 the previous detect.json (patch-day honesty: confirm the
                 patch first).
  --work-root    tools + venv home; default D:\\unpacked_game_data\\MiSide\\work

exit codes:
  0  ok
  2  usage error (bad flag, unknown/combined stage selector)
  3  stage failure — the failed stage is named on stderr
  4  missing dependency outputs — run the earlier stage first

stages:
%s
""" % ("\n".join("  %-16s %s" % (n, description_of(n))
                for n, _m, _d, _desc in STAGES))


def build_parser():
    import argparse

    parser = argparse.ArgumentParser(
        prog="run_all",
        description="MiSide extraction pipeline (P1): env -> detect -> "
                    "il2cpp-dump -> mono-typed-dump -> loc-jsonl -> art-export "
                    "-> decompile -> census -> logic-layer.",
        epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("game_root", nargs="?", metavar="<game-root>",
                        help="game root: holds MiSideFull.exe, "
                             "MiSideFull_Data\\ AND the loose Data\\ tree")
    parser.add_argument("--list", action="store_true",
                        help="print the stages in execution order and exit; "
                             "touches nothing")
    parser.add_argument("--stage", action="append", metavar="NAME",
                        help="run this stage (repeatable)")
    parser.add_argument("--from", dest="from_stage", metavar="NAME",
                        help="first stage of an inclusive registry slice")
    parser.add_argument("--to", dest="to_stage", metavar="NAME",
                        help="last stage of an inclusive registry slice")
    parser.add_argument("--work-root", dest="work_root", metavar="PATH",
                        default=common.DEFAULT_WORK_ROOT,
                        help="venv + tools home (default: %(default)s)")
    parser.add_argument("--keep-going", action="store_true",
                        help="S4/S7: ledger per-container/per-assembly failures "
                             "and continue instead of FAIL-FAST")
    parser.add_argument("--expect-drift", action="store_true",
                        help="S2: accept a changed container census total")
    return parser


def select_stages(args):
    if args.stage and (args.from_stage or args.to_stage):
        raise common.UsageError("--stage does not combine with --from/--to")
    names = stage_names()
    for s in ([args.from_stage, args.to_stage] +
              list(args.stage or [])):
        if s is not None and s not in names:
            raise common.UsageError(
                "unknown stage %r — valid stages: %s" % (s, ", ".join(names)))
    if args.stage:
        chosen = [s for s in names if s in set(args.stage)]
    elif args.from_stage or args.to_stage:
        start = names.index(args.from_stage) if args.from_stage else 0
        end = names.index(args.to_stage) if args.to_stage else len(names) - 1
        if start > end:
            raise common.UsageError("--from stage comes after --to stage in "
                                    "registry order (%s > %s)" % (args.from_stage,
                                                                  args.to_stage))
        chosen = names[start:end + 1]
    else:
        chosen = list(names)
    return chosen


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # ssh/CRLF-safe
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse already printed its own message
        return EXIT_USAGE if exc.code not in (None, 0) else EXIT_OK

    if args.list:
        for i, name in enumerate(stage_names(), 1):
            print("%d. %-16s %s" % (i, name, description_of(name)))
        return EXIT_OK

    try:
        if not args.game_root:
            raise common.UsageError(
                "missing <game-root> — the directory holding MiSideFull.exe, "
                "MiSideFull_Data\\ and Data\\ (see --help)")
        chosen = select_stages(args)
    except common.UsageError as exc:
        print("usage error: %s" % exc, file=sys.stderr)
        return EXIT_USAGE

    ctx = common.RunContext(
        pack_root=PACK_ROOT,
        game_root=Path(args.game_root),
        work_root=Path(args.work_root),
        keep_going=args.keep_going,
        expect_drift=args.expect_drift)

    # Stale-log defense: pins must agree with pipeline/requirements.txt before
    # anything runs (AC-3).
    try:
        common.stale_log_defense(ctx)
    except common.StageFailure as exc:
        print("stage failed: %s" % exc, file=sys.stderr)
        return EXIT_STAGE

    ran = set()
    total = len(chosen)
    for i, name in enumerate(chosen, 1):
        module = load_stage(name)
        for dep in deps_of(name):
            if dep in ran:
                continue
            if not load_stage(dep).outputs_present(ctx):
                print("missing dependency outputs: '%s' is required by '%s' — "
                      "run the earlier stage first" % (dep, name), file=sys.stderr)
                return EXIT_DEPS
        print("[%d/%d] %s — %s" % (i, total, name, description_of(name)))
        try:
            module.run(ctx)
        except common.MissingDependency as exc:
            print(str(exc), file=sys.stderr)
            return EXIT_DEPS
        except common.StageFailure as exc:
            print("stage failed: %s" % exc, file=sys.stderr)
            return EXIT_STAGE
        except Exception as exc:  # unexpected: still name the failed stage
            import traceback
            traceback.print_exc()
            print("stage failed: %s: %s" % (name, exc), file=sys.stderr)
            return EXIT_STAGE
        ran.add(name)
        print("[%d/%d] %s — ok" % (i, total, name))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
