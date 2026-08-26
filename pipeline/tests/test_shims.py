"""AC-16 — both shims reach the same driver with identical results.

cmd is the native-Windows entry (run_all.cmd); the POSIX-sh shim serves
Git Bash / `ssh ne8k`. No .ps1 shim exists by design. Skipped when no bash
is available (non-Git-Bash Windows CI).
"""

from __future__ import annotations

import shutil

import pytest

pytestmark = pytest.mark.unit


def _norm(text: str) -> str:
    return text.replace("\r\n", "\n").strip()


def test_both_shims_exist_and_agree_on_list(make_sandbox):
    if not (shutil.which("bash") or shutil.which("bash.exe")):
        pytest.skip("no bash on PATH — sh-shim equivalence needs Git Bash")
    sb = make_sandbox("shim-agree", stages_will_run=False)
    assert (sb.path / "run_all.cmd").exists(), "run_all.cmd shim missing"
    assert (sb.path / "run_all").exists(), "POSIX run_all shim missing"

    via_cmd = sb.run_shim_cmd("--list")
    assert via_cmd.rc == 0, f"cmd shim failed: {via_cmd.err}"
    via_sh = sb.run_shim_sh("--list")
    assert via_sh.rc == 0, f"sh shim failed: {via_sh.err}"

    assert _norm(via_cmd.out) == _norm(via_sh.out), (
        "shims disagree on --list output:\n"
        f"--- cmd ---\n{via_cmd.out}\n--- sh ---\n{via_sh.out}")


def test_cmd_shim_matches_direct_driver(make_sandbox):
    sb = make_sandbox("shim-direct", stages_will_run=False)
    if not (sb.path / "run_all.cmd").exists():
        pytest.fail("run_all.cmd missing — CodeWriter manifest item")
    direct = sb.run("--list", root=False)
    via_cmd = sb.run_shim_cmd("--list")
    for r in (direct, via_cmd):
        assert r.rc == 0, f"rc={r.rc}: {r.err}"
    assert _norm(direct.out) == _norm(via_cmd.out), \
        ".cmd output differs from direct python invocation"
