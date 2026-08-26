"""S6 art-export — AC-10 (catalogue reconciliation, media carve-out,
verbatim Custom copies, staged scope recording)."""

from __future__ import annotations

import hashlib
import json

import pytest

pytestmark = pytest.mark.integration


def _prep(sb):
    res = sb.run("--from", "env", "--to", "detect")
    assert res.rc == 0, res.err


def test_catalogue_artifacts_exist(full_run):
    sb, man, _ = full_run("art-exists")
    assert (sb.extracted / "MEDIA-CATALOGUE.md").exists()
    assert (sb.extracted / "media-catalogue.jsonl").exists()
    rows = [json.loads(l) for l in
            (sb.extracted / "media-catalogue.jsonl").read_text("utf-8",
                                                              errors="replace")
            .splitlines() if l.strip()]
    assert rows, "empty media catalogue"


def test_catalogue_reconciles_to_walked_sums(full_run):
    """Numbers in the catalogue must equal an independent walk of the
    fixture root — the §8 rule: totals derived, never copied."""
    sb, man, _ = full_run("art-reconcile")
    md = (sb.extracted / "MEDIA-CATALOGUE.md").read_text("utf-8",
                                                         errors="replace")
    jsonl = (sb.extracted / "media-catalogue.jsonl").read_text("utf-8",
                                                               errors="replace")
    hay = md + jsonl
    for label, count, total in [
        ("ogg", len(man["ogg"]), man["ogg_total"]),
        ("GI", len(man["gi"]), man["gi_total"]),
        ("psd", sum(v["count"] for v in man["languages"]["psd"].values()),
         sum(v["bytes"] for v in man["languages"]["psd"].values())),
    ]:
        assert str(count) in hay, f"catalogue missing {label} count {count}"
        if total is not None:
            assert str(total) in hay, f"catalogue missing {label} bytes {total}"
    # Per-locale art is reported per locale (skew ledger rule — no global
    # aggregate): each locale's own png count must appear.
    for locale, n in man["texture_skew"].items():
        assert str(n) in hay, f"catalogue missing per-locale png count {n} ({locale})"


def test_no_audio_video_bytes_under_extracted(full_run):
    """Media carve-out (R-E1-5, questions.md §5): audio/video stay IN PLACE;
    nothing but catalogue rows may exist under extracted/."""
    sb, man, _ = full_run("art-carveout")
    offenders = [p for p in sb.extracted.rglob("*")
                 if p.suffix.lower() in (".ogg", ".ogv", ".mp4", ".wav")]
    assert not offenders, f"media bytes written under extracted/: {offenders[:5]}"


def test_custom_pngs_copy_through_verbatim(full_run):
    sb, man, _ = full_run("art-custom")
    want = {info["sha256"] for info in man["custom_pngs"].values()}
    found = {hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sb.extracted.rglob("*.png")}
    missing = want - found
    assert not missing, (
        f"{len(missing)}/{len(want)} Data\\Custom PNGs not copied byte-verbatim")


def test_gi_family_catalogued_level3_only(full_run):
    """R-E1-4: catalogue the GI tree, don't chase it."""
    sb, man, _ = full_run("art-gi")
    hay = ((sb.extracted / "MEDIA-CATALOGUE.md").read_text("utf-8",
                                                           errors="replace")
           + (sb.extracted / "media-catalogue.jsonl").read_text("utf-8",
                                                                errors="replace"))
    low = hay.lower()
    assert "gi" in low and "level3" in low, "GI/level3 family not catalogued"


def test_derived_per_family_scope_recorded_in_log(full_run):
    """questions.md §6 STAGED ruling: export-vs-catalogue scope decided per
    family from first-pass rows and recorded in EXTRACTION-LOG.md."""
    sb, man, _ = full_run("art-scope")
    log = (sb.extracted / "EXTRACTION-LOG.md").read_text("utf-8",
                                                         errors="replace")
    assert "scope" in log.lower(), \
        "EXTRACTION-LOG.md must record the derived per-family art scope"
