"""S7 decompile — AC-11 (assembly trees, Voice Editor set, _structure
graphs, recon anchors, garbage-bodies caveat)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def _prep(sb):
    res = sb.run("--from", "env", "--to", "il2cpp-dump")
    assert res.rc == 0, res.err


def test_main_and_voice_editor_trees_present(full_run):
    sb, man, _ = full_run("decomp-trees")
    dec = sb.extracted / "decompiled"
    main = dec / "main"
    voice = dec / "voice-editor"
    assert main.is_dir(), "decompiled/main/ missing"
    assert voice.is_dir(), "decompiled/voice-editor/ missing"
    # 57 main assemblies (E1 DummyDll count) -> >=57 .csproj project exports.
    projects = list(main.rglob("*.csproj"))
    assert len(projects) >= 57, f"only {len(projects)} main assembly trees"
    # Voice Editor Managed set (3 stub DLLs in the fixture).
    ve_projects = list(voice.rglob("*.csproj")) or list(voice.rglob("*.cs"))
    assert len(ve_projects) >= 3, (
        f"Voice Editor Managed assemblies not decompiled: {len(ve_projects)}")


def test_structure_graphs_emitted(full_run):
    """Doctrine-required: class hierarchy + type reference graphs under
    decompiled/_structure/, derived from dump.cs — mandatory, never skipped."""
    sb, man, _ = full_run("decomp-structure")
    structure = sb.extracted / "decompiled" / "_structure"
    assert structure.is_dir(), "decompiled/_structure/ missing"
    files = [p for p in structure.rglob("*") if p.is_file()]
    assert files, "_structure/ is empty — graphs are a mandatory artifact"


def test_recon_anchors_in_main_tree(full_run):
    """E1 §Step 7 anchors preserved verbatim: GlobalLanguage.GetString and
    the ConsoleInterface loader chain."""
    sb, man, _ = full_run("decomp-anchors")
    main = sb.extracted / "decompiled" / "main"
    blob = "\n".join(p.read_text("utf-8", errors="replace")
                     for p in main.rglob("*.cs"))
    assert "GetString(string _name" in blob, "GlobalLanguage.GetString missing"
    assert "CheckLocalization" in blob, "loader chain anchor missing"
    assert "LocalizationClearText" in blob, "loader chain tail missing"


def test_garbage_bodies_caveat_recorded(full_run):
    """Spec S7: 'bodies are garbage-prone in call-heavy serializers' caveat
    lands in census/stage-reports/decompile.json."""
    sb, man, _ = full_run("decomp-caveat")
    report = sb.extracted / "census" / "stage-reports" / "decompile.json"
    assert report.exists(), "stage report for decompile missing"
    low = report.read_text("utf-8", errors="replace").lower()
    assert "garbage" in low, "bodies-garbage-prone caveat not recorded"
