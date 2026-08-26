"""S3 il2cpp-dump — AC-7 fixture-tier (artifact shape + headless invariants).

The stub tool emits the five artifact shapes and REFUSES to run unless the
driver already flipped config.json RequireAnyKey to false — so a green run
here proves the headless-config delta ordering, not just presence.
"""

from __future__ import annotations

import json
import time

import pytest

pytestmark = pytest.mark.integration


def _prep(sb):
    res = sb.run("--from", "env", "--to", "detect")
    assert res.rc == 0, f"detect prep failed: {res.err}"


def test_artifact_set_shape(make_mini_root):
    sb, man = make_mini_root("il2-shape")
    _prep(sb)
    t0 = time.monotonic()
    res = sb.run("--stage", "il2cpp-dump")
    wall = time.monotonic() - t0
    assert res.rc == 0, f"il2cpp-dump failed:\n{res.err}"
    il2 = sb.extracted / "il2cpp"
    for name in ("dump.cs", "il2cpp.h", "script.json", "stringliteral.json"):
        assert (il2 / name).exists(), f"missing il2cpp/{name}"
    dummy = il2 / "DummyDll"
    assert dummy.is_dir()
    dlls = list(dummy.glob("*.dll"))
    # E1 ground truth: exactly 57 DummyDlls incl. Assembly-CSharp.dll.
    assert len(dlls) == 57, f"expected 57 DummyDlls, got {len(dlls)}"
    assert (dummy / "Assembly-CSharp.dll").exists()
    dump_cs = (il2 / "dump.cs").read_text("utf-8", errors="replace")
    assert len(dump_cs.splitlines()) >= 50
    assert "GlobalLanguage" in dump_cs
    # Seconds-class runtime expectation (stub is instant; this guards
    # against accidental real-tool/hang invocations in CI).
    assert wall < 60, f"il2cpp-dump took {wall:.1f}s"


def test_headless_config_delta_applied_before_spawn(make_mini_root):
    """E1 deviation 4: stock config waits for a keypress. The driver must
    flip RequireAnyKey false BEFORE invoking the exe; the stub hard-fails
    (exit 97) otherwise."""
    sb, man = make_mini_root("il2-headless")
    _prep(sb)
    res = sb.run("--stage", "il2cpp-dump")
    assert res.rc == 0, (
        f"stub refused to run (exit {res.rc}) — RequireAnyKey was still true "
        f"at spawn time:\n{res.err}")
    cfg = sb.workroot / "tools" / "Il2CppDumper" / "config.json"
    body = cfg.read_text("utf-8").lower()
    assert '"requireanykey"' in body and "true" not in body.partition(
        '"requireanykey"')[2][:40], f"config delta not persisted: {body}"


def test_child_cwd_pinned_to_tool_dir(make_mini_root):
    """§S3: child cwd pinned to the tool dir (E1 invoked it bare from there;
    matching the proven shape costs nothing)."""
    sb, man = make_mini_root("il2-cwd")
    _prep(sb)
    res = sb.run("--stage", "il2cpp-dump")
    assert res.rc == 0, res.err
    calls = sb.stub_calls("il2cpp-dump")
    assert calls, "no stub invocation recorded"
    cwd = calls[0]["cwd"].lower().replace("/", "\\")
    assert cwd.endswith("tools\\il2cppdumper"), \
        f"Il2CppDumper child cwd was {calls[0]['cwd']!r}, expected tool dir"


def test_inputs_passed_as_dll_then_metadata(make_mini_root):
    """Verbatim E1 invocation shape: GameAssembly.dll first, then
    global-metadata.dat, then the output dir."""
    sb, man = make_mini_root("il2-argv")
    _prep(sb)
    res = sb.run("--stage", "il2cpp-dump")
    assert res.rc == 0, res.err
    argv = sb.stub_calls("il2cpp-dump")[0]["argv"]
    assert argv[0].endswith("GameAssembly.dll"), f"argv[0]={argv[0]!r}"
    assert argv[1].endswith("global-metadata.dat"), f"argv[1]={argv[1]!r}"
    assert argv[2].replace("\\", "/").endswith("extracted/il2cpp") or \
        argv[2].endswith("il2cpp"), f"argv[2]={argv[2]!r} (output dir)"
