"""S1 env — workroot venv + pinned install.

E1-proven shape (docs/research/explorer-e1-hands-on.mdx §Step 1):
`python -m venv <workroot>\\venv` then `<venv>\\Scripts\\pip.exe install
--quiet -r pipeline\\requirements.txt`. Idempotent: install is skipped when
`pip freeze` already covers every pin. FAIL-FAST on pip resolution errors.
"""

import sys
import time

from pipeline import common

NAME = "env"


def outputs_present(ctx) -> bool:
    return ctx.venv_python.exists()


def run(ctx):
    started = time.monotonic()
    pins = common.parse_requirements(ctx.requirements)

    created = False
    if not ctx.venv_python.exists():
        proc = common.run_argv([sys.executable, "-m", "venv",
                                common.win(ctx.venv_dir)])
        if proc.returncode != 0:
            raise common.StageFailure(NAME, "python -m venv failed rc=%s:\n%s" % (
                proc.returncode, (proc.stderr or proc.stdout).strip()[-800:]))
        created = True

    freeze = common.run_argv([common.win(ctx.venv_python), "-m", "pip", "freeze"])
    if freeze.returncode != 0:
        raise common.StageFailure(NAME, "pip freeze failed rc=%s" % freeze.returncode)
    have = common.freeze_map(freeze.stdout)
    missing = {k: v for k, v in pins.items() if have.get(k) != v}

    installed = False
    if missing:
        pip_exe = common.win(ctx.venv_pip)
        argv = [pip_exe, "install", "--quiet", "-r", common.win(ctx.requirements)] \
            if ctx.venv_pip.exists() else \
            [common.win(ctx.venv_python), "-m", "pip", "install", "--quiet",
             "-r", common.win(ctx.requirements)]
        proc = common.run_argv(argv)
        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-15:]
            raise common.StageFailure(
                NAME, "pip install failed rc=%s (resolution error):\n%s" % (
                    proc.returncode, "\n".join(tail)))
        installed = True

    ver = common.run_argv([common.win(ctx.venv_python), "--version"])
    common.write_stage_report(ctx, NAME, {
        "status": "ok",
        "venv": str(ctx.venv_dir),
        "created": created,
        "install_ran": installed,
        "freeze_matched_before": not missing,
        "pins": len(pins),
        "python": ver.stdout.strip(),
        "duration_s": round(time.monotonic() - started, 3),
    })
    return {"created": created, "installed": installed}
