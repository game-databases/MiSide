"""S5 loc-jsonl — AC-9 (split-based counting, verbatim text, skew ledger).

Two fixture levels:
* mini-loc (spec §6): 2 locales x 3 categories — parser math + ledger,
  unit-tier speed;
* mini-root: full synthetic tree incl. the EN/RU spot-check strings and
  Japanese texture-subset skew.

The pinned record shape is ``{category, line_index, text}`` with
``line_index`` zero-based (spec §S5) — asserted structurally.
"""

from __future__ import annotations

import json

import pytest

from conftest import read_jsonl

pytestmark = pytest.mark.integration

RECORD_KEYS = {"category", "line_index", "text"}


def _prep(sb):
    res = sb.run("--from", "env", "--to", "detect")
    assert res.rc == 0, f"detect prep failed: {res.err}"
    res = sb.run("--stage", "loc-jsonl")
    return res


# ------------------------------------------------------- mini-loc (F) -----

class TestMiniLoc:
    def test_split_based_counting_no_trailing_newline(self, make_mini_root):
        sb, man = make_mini_root("loc-miniloc", build_languages_only=True)
        res = _prep(sb)
        assert res.rc == 0, f"loc-jsonl failed:\n{res.err}"
        path = sb.extracted / "localization" / "English" / "Achievements.jsonl"
        rows = read_jsonl(path)
        # File has NO trailing newline; a newline-counter would still be
        # right at this size, so the sharper probe is the trailing-newline
        # file below. Both must equal their true line counts.
        assert [r["text"] for r in rows] == ["Clabber", "Creak in the Dark",
                                             "Dead juice"]
        assert [r["line_index"] for r in rows] == [0, 1, 2]

    def test_trailing_newline_yields_no_phantom_record(self, make_mini_root):
        sb, man = make_mini_root("loc-miniloc-nl", build_languages_only=True)
        _prep(sb)
        rows = read_jsonl(sb.extracted / "localization" / "English" / "Menu.jsonl")
        # Menu.txt ends WITH '\n' — split-based counting must not emit a
        # phantom empty record for the position after it.
        assert len(rows) == 5, f"phantom trailing record: {rows}"
        assert rows[-1]["text"] == "Back"

    def test_record_shape_pinned(self, make_mini_root):
        sb, man = make_mini_root("loc-shape", build_languages_only=True)
        _prep(sb)
        loc = sb.extracted / "localization"
        category_files = [p for p in loc.rglob("*.jsonl")
                          if "_ledger" not in p.parts]
        assert category_files
        for jf in category_files:
            for row in read_jsonl(jf):
                assert set(row) == RECORD_KEYS, (
                    f"{jf.name}: record keys {sorted(row)} != "
                    f"{sorted(RECORD_KEYS)}")

    def test_missing_category_ledgered_not_asserted(self, make_mini_root):
        sb, man = make_mini_root("loc-skew", build_languages_only=True)
        _prep(sb)
        # French lacks Names -> no French/Names.jsonl ...
        assert not (sb.extracted / "localization" / "French" / "Names.jsonl").exists()
        # ... but the delta IS documented in the ledger.
        ledger = sb.extracted / "localization" / "_ledger" / "locale-delta.jsonl"
        assert ledger.exists(), "_ledger/locale-delta.jsonl missing"
        text = ledger.read_text("utf-8", errors="replace").lower()
        assert "french" in text and "names" in text, (
            "ledger must record the French/Names category delta")


# ----------------------------------------------------- mini-root (R) ------

def test_surface_counts_all_locales(make_mini_root):
    sb, man = make_mini_root("loc-surface")
    _prep(sb)
    loc = sb.extracted / "localization"
    files = [p for p in loc.rglob("*.jsonl") if "_ledger" not in p.parts]
    expected = sum(len(c) for c in man["languages"]["locales"].values())
    assert len(files) == expected, (
        f"{len(files)} category JSONLs emitted, manifest says {expected}")


def test_en_achievements_26_records_and_spot_texts(full_run):
    sb, man, _ = full_run("loc-en-ach")
    rows = read_jsonl(sb.extracted / "localization" / "English"
                      / "Achievements.jsonl")
    assert len(rows) == man["en_achievements_lines"] == 26
    assert [r["line_index"] for r in rows] == list(range(26))
    assert rows[25]["text"] == man["en_achievements_last"] == "Pro Gamer"
    assert rows[25]["category"] == "Achievements"


def test_ru_achievements_cyrillic_verbatim(full_run):
    sb, man, _ = full_run("loc-ru")
    rows = read_jsonl(sb.extracted / "localization" / "Russian"
                      / "Achievements.jsonl")
    assert rows[0]["text"] == man["ru_achievements_first"] == "Кислое молоко."


def test_text_byte_verbatim_against_source(full_run):
    """Every emitted text equals its source line exactly — no normalization,
    no whitespace mangling (toolchain.md §4 rule encoded as a check)."""
    sb, man, _ = full_run("loc-verbatim")
    languages = sb.game_root / "Data" / "Languages"
    for locale_dir in languages.iterdir():
        if not locale_dir.is_dir():
            continue
        for txt in locale_dir.glob("*.txt"):
            source_lines = txt.read_bytes().decode("utf-8").splitlines()
            rows = read_jsonl(sb.extracted / "localization" / locale_dir.name
                              / (txt.stem + ".jsonl"))
            assert len(rows) == len(source_lines), \
                f"{locale_dir.name}/{txt.name}: {len(rows)} != {len(source_lines)}"
            for row, line in zip(rows, source_lines):
                assert row["text"] == line, \
                    f"{locale_dir.name}/{txt.name}[{row['line_index']}]: " \
                    f"{row['text']!r} != {line!r}"


def test_japanese_skews_ledgered(make_mini_root):
    sb, man = make_mini_root("loc-ja")
    _prep(sb)
    ledger = sb.extracted / "localization" / "_ledger" / "locale-delta.jsonl"
    text = ledger.read_text("utf-8", errors="replace")
    low = text.lower()
    # Category skew: Japanese has no Names.
    assert "japanese" in low and "names" in low
    # Texture-subset skew: JA 2 png vs EN/RU 4 png (E1: JA 20 vs 26).
    assert "texture" in low or "png" in low


def test_declared_codec_file_recovered_and_stage_exits_zero(make_mini_root):
    """A-S6 ruling (s6-arbiter.mdx item 1, option b strict): a legacy-encoded
    file with a DECLARED codec is recovered when every invalid segment
    round-trips byte-exactly under it — records emit verbatim-recovered and
    the stage exits 0."""
    sb, man = make_mini_root("loc-declared-codec")
    slovak = sb.game_root / "Data" / "Languages" / "Slovak"
    slovak.mkdir(parents=True, exist_ok=True)
    # The DECLARED_CODECS key from the evidence: Slovak/LocationDialogue
    # Location12.txt -> cp1250 (orthography-confirmed recovery).
    texts = ["Zostaň tu.", "Myslím, že som niečo stratila."]
    (slovak / "LocationDialogue Location12.txt").write_bytes(
        ("\n".join(texts) + "\n").encode("cp1250"))
    res = _prep(sb)
    assert res.rc == 0, (
        f"recover-or-mark must not fail the stage:\n{res.err}")
    rows = read_jsonl(sb.extracted / "localization" / "Slovak"
                      / "LocationDialogue Location12.jsonl")
    # Recovered rows are byte-exact under the declared codec — lossless.
    assert [r["text"] for r in rows] == texts
    residue = read_jsonl(sb.extracted / "localization" / "_ledger"
                         / "encoding-residue.jsonl")
    row = next(r for r in residue if r["locale"] == "Slovak")
    assert row["codec"] == "cp1250" and row["codec_round_trip_proven"] is True
    assert row["segments_marked_fffd"] == 0 and row["segments_recovered"] >= 1
    # Healthy locales still emitted alongside.
    assert (sb.extracted / "localization" / "English" / "Menu.jsonl").exists()


def test_undeclared_encoding_marked_fffd_and_stage_exits_zero(make_mini_root):
    """A-S6 ruling: a non-UTF-8 file with NO declared codec is never guessed
    at — every invalid segment becomes one declared U+FFFD, hex+offset are
    ledgered, and the stage still exits 0."""
    sb, man = make_mini_root("loc-undeclared-codec")
    xtest = sb.game_root / "Data" / "Languages" / "XTest"
    xtest.mkdir(parents=True, exist_ok=True)
    (xtest / "Bad.txt").write_bytes(b"Mita\n\xff\xfe glitch\nTail\n")
    res = _prep(sb)
    assert res.rc == 0, f"marked-not-guessed must not fail the stage:\n{res.err}"
    # Parsing continued; the file emitted with U+FFFD per invalid segment.
    rows = read_jsonl(sb.extracted / "localization" / "XTest" / "Bad.jsonl")
    assert [r["text"] for r in rows] == ["Mita", "� glitch", "Tail"]
    assert (sb.extracted / "localization" / "English" / "Menu.jsonl").exists()
    residue = read_jsonl(sb.extracted / "localization" / "_ledger"
                         / "encoding-residue.jsonl")
    row = next(r for r in residue if r["locale"] == "XTest")
    assert row["codec"] is None and row["codec_round_trip_proven"] is False
    assert row["segments_marked_fffd"] == 1
    # Raw bytes hex-encoded into the residue row (evidence, not a guess).
    assert [seg["hex"] for seg in row["segments"]] == ["fffe"]


def test_structural_divergence_after_recovery_exits_three(make_mini_root):
    """A-S6 ruling: exit 3 is RESERVED for unhandled classes — here the
    recovered line count diverges from the clean-sibling category norm
    (the 71-line class), which fails the stage at stage end."""
    sb, man = make_mini_root("loc-divergence")
    xtest = sb.game_root / "Data" / "Languages" / "XTest"
    xtest.mkdir(parents=True, exist_ok=True)
    # Recovers to 2 lines vs the Menu norm of 5 (EN/RU/JA clean siblings).
    (xtest / "Menu.txt").write_bytes(b"Start\n\xff\xfe\n")
    res = _prep(sb)
    assert res.rc == 3, ("structural divergence must exit 3, "
                         f"got {res.rc}:\n{res.err}")
    # Emission still happened (the invariant breach is divergence, not skips).
    assert (sb.extracted / "localization" / "XTest" / "Menu.jsonl").exists()
    report = json.loads((sb.extracted / "census" / "stage-reports"
                         / "loc-jsonl.json").read_text("utf-8"))
    # Exactly the divergence class fired — nothing else failed this run.
    assert {a["error"] for a in report["anomalies"]} \
        == {"structural-divergence-vs-category-norm"}
