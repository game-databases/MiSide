"""S5 loc-jsonl — split-based line parse to per-locale JSONL + skew ledger.

Input `<GAME>\\Data\\Languages\\<locale>\\<Category>.txt` (loose tree at game
root — E1 deviation 1). Emission: one record per line, `{category,
line_index, text}`, `line_index` zero-based — the join key proven end-to-end
by `GlobalLanguage.GetString(name, index)` (E1 §Step 7). Text preserved
verbatim UTF-8; never normalized. Line counting is SPLIT-BASED: category
files carry no trailing newline, so newline counting undercounts by one
(E1 deviation 3).

Legacy-encoded files (incident I-3, arbiter ruling s6-arbiter.mdx item 1):
a non-UTF-8 file is RECOVERED-OR-MARKED, never skipped and never silently
best-effort decoded. ONE codec per file, DECLARED from investigation
evidence (`docs/research/s5-legacy-encoding.mdx`) in DECLARED_CODECS below;
it applies only when EVERY invalid segment of that file round-trips
byte-exactly under it, else every invalid segment becomes one declared
U+FFFD each. Files absent from the declaration map are marked U+FFFD, never
guessed at. Every handled file gets a residue row (per-segment
offset/hex/line_index/recovered-or-FFFD) in `_ledger/encoding-residue.jsonl`
and in the stage report. Exit is **0 when every anomaly is
recovered-or-explicitly-marked**; exit 3 remains for an absent store,
post-recovery control characters, structural divergence from the category
norm (split-line count vs the clean-sibling mode — the 71-line class), a
breach of the mechanical invariant `emitted == walked-txt-count`, and any
other unhandled anomaly class.

Ledger `_ledger/locale-delta.jsonl` documents BOTH halves of R-E1-3:
per-locale present-vs-reference(EN) category sets AND per-locale
Textures/font subsets. Assert-equal is forbidden; the skew ledger is the
deliverable. The reference set derives from EMITTED rows post-policy, so a
reference category recovered under the legacy policy regains its seat and
phantom `extra_vs_reference` rows clear automatically. Ledger write mode:
deterministic full rewrite per run.
"""

import time
from collections import Counter
from pathlib import Path

from pipeline import common

NAME = "loc-jsonl"

REFERENCE_LOCALE = "English"
LEDGER_REL = Path("localization") / "_ledger" / "locale-delta.jsonl"
RESIDUE_LEDGER_REL = Path("localization") / "_ledger" / "encoding-residue.jsonl"

# ONE declared codec per affected file, keyed `<locale>/<file>.txt`. Declared
# FROM EVIDENCE (s5-legacy-encoding.mdx §2 codec verdicts) — never discovered
# at runtime ("no silent best-effort decodes"). Applied only when EVERY
# invalid segment of the file round-trips byte-exactly under it.
DECLARED_CODECS = {
    # Slovak: all 62 invalid segments round-trip under cp1250 and recover
    # correct orthography (`Zostaň tu.` · `Myslím, že som niečo stratila.`);
    # independent confirmation: its own 0xCC recovers to `Ě` exactly where
    # Czech/Hungarian ship that glyph at the same line.
    "Slovak/LocationDialogue Location12.txt": "cp1250",
    # Serbian (Latin): all 13 segments are š/ž/Ž bytes (9a/9e/8e — identical
    # mapping in cp1250); cp1250 declared for vendor consistency with Slovak.
    "Serbian (Latin)/LocationDialogue Location12.txt": "cp1250",
    # Deliberately absent: Croatian/English/Filipino/Indonesia/Vietnamese
    # `LocationDialogue Location12.txt`. Their single stray byte (0xCC, line
    # 58, fleet-corrupted upstream before shipping) round-trips under cp1250
    # but would fabricate a coordinate glyph no corpus evidence justifies —
    # those become declared U+FFFD, the glyph healthy locales already ship
    # verbatim at that line (BG/IT/ES literal U+FFFD).
}
CODEC_BASIS = "declared-evidence:docs/research/s5-legacy-encoding.mdx#2-codec-verdicts"

# Post-recovery control-character gate: these C0/C1 bytes are structural
# (newline/tab) and allowed; anything else in a recovered file exits 3.
RECOVER_CONTROL_EXEMPT = "\t\n\r"


def outputs_present(ctx) -> bool:
    return (ctx.extracted / LEDGER_REL).exists() \
        and (ctx.extracted / "localization").is_dir()


def _utf8_pieces(raw: bytes):
    """Split raw bytes at strict-UTF-8 failures into ordered pieces —
    ('text', str) valid runs and ('bad', offset, bytes) maximal-contiguous
    invalid segments (the evidence §2 isolation method)."""
    pieces, pos = [], 0
    while pos < len(raw):
        try:
            pieces.append(("text", raw[pos:].decode("utf-8")))
            break
        except UnicodeDecodeError as exc:
            lo, hi = pos + exc.start, pos + exc.end
            if lo > pos:
                pieces.append(("text", raw[pos:lo].decode("utf-8")))
            pieces.append(("bad", lo, raw[lo:hi]))
            pos = hi
    merged = []
    for piece in pieces:
        if piece[0] == "bad" and merged and merged[-1][0] == "bad" \
                and merged[-1][1] + len(merged[-1][2]) == piece[1]:
            merged[-1] = ("bad", merged[-1][1], merged[-1][2] + piece[2])
        else:
            merged.append(piece)
    return merged


def _round_trips(chunk: bytes, codec: str) -> bool:
    """Byte round-trip proof: decode→encode must reproduce the bytes."""
    try:
        return chunk.decode(codec).encode(codec) == chunk
    except (UnicodeDecodeError, UnicodeEncodeError, LookupError):
        return False


def parse_category(path: Path, locale: str):
    """Return (records, residue_row_or_None) with split-based counting.

    Clean UTF-8 → (records, None). Legacy-encoded → recover-or-mark under
    the I-3 policy (module docstring): records ALWAYS emit; residue_row
    documents every segment decision for the encoding-residue ledger plus
    the post-recovery gate inputs (line count, control codepoints).
    """
    raw = path.read_bytes()
    category = path.stem
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    else:
        return [{"category": category, "line_index": i, "text": line}
                for i, line in enumerate(text.splitlines())], None

    pieces = _utf8_pieces(raw)
    segments = [(p[1], p[2]) for p in pieces if p[0] == "bad"]
    codec = DECLARED_CODECS.get("%s/%s" % (locale, path.name))
    proven = codec is not None \
        and all(_round_trips(chunk, codec) for _, chunk in segments)

    parts, seg_rows = [], []
    for piece in pieces:
        if piece[0] == "text":
            parts.append(piece[1])
            continue
        off, chunk = piece[1], piece[2]
        if proven:
            recovered = chunk.decode(codec)
            parts.append(recovered)
            seg_rows.append({"offset": off, "hex": chunk.hex(),
                             "line_index": raw[:off].count(b"\n"),
                             "action": "decoded-" + codec,
                             "recovered_text": recovered, "reason": None})
        else:
            parts.append("�")
            seg_rows.append({"offset": off, "hex": chunk.hex(),
                             "line_index": raw[:off].count(b"\n"),
                             "action": "marked-fffd", "recovered_text": None,
                             "reason": "no-declared-codec" if codec is None
                             else "declared-codec-round-trip-failed"})
    text = "".join(parts)
    records = [{"category": category, "line_index": i, "text": line}
               for i, line in enumerate(text.splitlines())]
    residue = {
        "kind": "encoding-residue",
        "id": "I-3:%s/%s" % (locale, category),
        "locale": locale,
        "category": category,
        "file_bytes": len(raw),
        "codec": codec,
        "codec_basis": CODEC_BASIS if proven else None,
        "codec_round_trip_proven": proven,
        "segments_total": len(seg_rows),
        "segments_recovered": sum(1 for s in seg_rows
                                  if s["recovered_text"] is not None),
        "segments_marked_fffd": sum(1 for s in seg_rows
                                    if s["recovered_text"] is None),
        "lines_post_recovery": len(records),
        "control_codepoints": sorted({hex(ord(c)) for c in text
                                      if (ord(c) < 32
                                          and c not in RECOVER_CONTROL_EXEMPT)
                                      or ord(c) == 127}),
        "segments": seg_rows,
    }
    return records, residue


def residue_seeds(loc_report: dict):
    """AC-12 residue-ledger seeds in the census RESIDUE_SEEDS pattern
    (title, id, content) — derived from THIS run's stage report, numbers are
    stage-measured, never copied from a doc."""
    files = loc_report.get("residue_files") or []
    summary = loc_report.get("legacy_encoding") or {}
    if not files:
        return []
    codecs = ", ".join(sorted(summary.get("codecs_applied") or [])) or "(none)"
    text = (
        "%d Data\\Languages .txt file(s) are not valid UTF-8 (incident I-3, "
        "investigated in docs/research/s5-legacy-encoding.mdx): %d legacy "
        "segment(s) round-trip-decoded losslessly under the declared "
        "codec(s) %s; %d unjustifiable byte run(s) — the fleet-corrupted "
        "coordinate strays — emitted as declared U+FFFD, the glyph healthy "
        "locales already ship verbatim at that line. Per-segment "
        "offset/hex/recovered-or-FFFD rows: "
        "localization/_ledger/encoding-residue.jsonl."
        % (summary.get("files_handled", len(files)),
           summary.get("segments_recovered", 0), codecs,
           summary.get("segments_marked_fffd", 0)))
    return [("legacy-encoded loc files recovered-or-marked", "I-3", text)]


def _art_subset(locale_dir: Path) -> dict:
    textures_dir = locale_dir / "Textures"
    ext_counts, tex_bytes = {}, 0
    if textures_dir.is_dir():
        for p in sorted(textures_dir.rglob("*")):
            if p.is_file():
                ext_counts[p.suffix.lower().lstrip(".") or "(none)"] = \
                    ext_counts.get(p.suffix.lower().lstrip(".") or "(none)", 0) + 1
                tex_bytes += p.stat().st_size
    fonts, other = [], []
    for p in sorted(locale_dir.rglob("*")):
        rel = p.relative_to(locale_dir).as_posix()
        if p.is_file() and not rel.startswith("Textures/"):
            entry = {"path": rel, "bytes": p.stat().st_size}
            (fonts if "font" in p.name.lower() else other).append(entry)
    return {"textures_by_ext": dict(sorted(ext_counts.items())),
            "textures_bytes": tex_bytes,
            "font_files": fonts, "other_files": other}


def run(ctx):
    started = time.monotonic()
    loc_root = ctx.game_root / "Data" / "Languages"
    if not loc_root.is_dir():
        raise common.StageFailure(NAME, "loc store absent at %s (FAIL-FAST)" % loc_root)

    out_root = ctx.extracted / "localization"
    common.wipe_tree(out_root)

    locales = sorted(d for d in loc_root.iterdir() if d.is_dir())
    anomalies = []          # UNHANDLED classes only — non-empty ⇒ exit 3
    residue_rows = []
    clean_line_counts = {}  # category → Counter of clean split-line counts
    category_sets = {}
    art_subsets = {}
    files_emitted = 0
    records_emitted = 0
    total_txt = 0

    for locale_dir in locales:
        locale = locale_dir.name
        cat_files = sorted(p for p in locale_dir.iterdir()
                           if p.is_file() and p.suffix.lower() == ".txt")
        total_txt += len(cat_files)
        present = set()
        for cat_file in cat_files:
            try:
                records, residue = parse_category(cat_file, locale)
            except OSError as exc:
                anomalies.append({"locale": locale,
                                  "category": cat_file.stem,
                                  "error": "io-read-unhandled",
                                  "reason": str(exc)})
                continue
            # Recovered-or-marked files emit like any other; the reference
            # set therefore derives from EMITTED rows post-policy.
            common.write_jsonl(out_root / locale / ("%s.jsonl" % cat_file.stem),
                               records)
            present.add(cat_file.stem)
            files_emitted += 1
            records_emitted += len(records)
            if residue is None:
                clean_line_counts.setdefault(
                    cat_file.stem, Counter())[len(records)] += 1
            else:
                residue_rows.append(residue)
        category_sets[locale] = present
        art_subsets[locale] = _art_subset(locale_dir)

    # Post-recovery gates on every handled (legacy-encoded) file: control
    # characters, and structural divergence vs the category norm (modal
    # split-line count among this run's clean same-category parses — the
    # 71-line class). Norm unknown (no clean siblings) ⇒ recorded, not failed.
    def _norm(category):
        counts = clean_line_counts.get(category)
        if not counts:
            return None
        return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]

    for row in residue_rows:
        row["category_norm_lines"] = _norm(row["category"])
        if row["control_codepoints"]:
            anomalies.append({
                "locale": row["locale"], "category": row["category"],
                "error": "post-recovery-control-characters",
                "codepoints": row["control_codepoints"]})
        if row["category_norm_lines"] is not None \
                and row["lines_post_recovery"] != row["category_norm_lines"]:
            anomalies.append({
                "locale": row["locale"], "category": row["category"],
                "error": "structural-divergence-vs-category-norm",
                "lines_post_recovery": row["lines_post_recovery"],
                "category_norm_lines": row["category_norm_lines"]})

    # Mechanical invariant (ruling item 1): emission accounts for every
    # walked txt file — S8 reconciles by construction. A shortfall means a
    # file was neither emitted nor explainably handled: unhandled class.
    if files_emitted != total_txt:
        anomalies.append({"error": "emitted-walked-invariant-breach",
                          "emitted": files_emitted, "walked": total_txt})

    # Ledgers: encoding-residue first-class beside the delta ledger — both
    # deterministic full rewrites.
    residue_rows.sort(key=lambda r: (r["locale"], r["category"]))
    common.write_jsonl(ctx.extracted / RESIDUE_LEDGER_REL, residue_rows)

    # Ledger rows: per-locale present-vs-reference(EN) category set AND the
    # per-locale texture/font subset — both halves of R-E1-3.
    ledger_rows = []
    ref_categories = category_sets.get(REFERENCE_LOCALE)
    for locale in sorted(category_sets):
        present = category_sets[locale]
        has_ref = ref_categories is not None
        ledger_rows.append({
            "kind": "category-set",
            "locale": locale,
            "reference": REFERENCE_LOCALE if has_ref else None,
            "category_count": len(present),
            "reference_category_count": len(ref_categories) if has_ref else None,
            "missing_vs_reference": sorted(ref_categories - present) if has_ref else [],
            "extra_vs_reference": sorted(present - ref_categories) if has_ref
            else sorted(present),
        })
        ledger_rows.append({"kind": "art-subset", "locale": locale,
                            **art_subsets[locale]})

    # Deterministic full rewrite: kind, then locale.
    ledger_rows.sort(key=lambda r: (r["kind"], r["locale"]))
    common.write_jsonl(ctx.extracted / LEDGER_REL, ledger_rows)
    common.write_volatile_fields(ctx)

    art_locales = sum(1 for r in ledger_rows if r["kind"] == "art-subset"
                      and r.get("textures_by_ext"))
    report = {
        "status": "ok-with-unhandled-anomalies" if anomalies else "ok",
        "locales": [d.name for d in locales],
        "locale_count": len(locales),
        "txt_files_seen": total_txt,
        "emitted": files_emitted,
        "categories_parsed": files_emitted,
        "records_emitted": records_emitted,
        "ledger_rows": len(ledger_rows),
        "locales_with_textures": art_locales,
        "legacy_encoding": {
            "policy": "declared-codec-recover-or-mark (s6-arbiter.mdx item 1)",
            "files_handled": len(residue_rows),
            "files_decoded_under_declared_codec":
                sum(1 for r in residue_rows if r["codec_round_trip_proven"]),
            "segments_recovered": sum(r["segments_recovered"]
                                      for r in residue_rows),
            "segments_marked_fffd": sum(r["segments_marked_fffd"]
                                        for r in residue_rows),
            "codecs_applied": sorted({r["codec"] for r in residue_rows
                                      if r["codec_round_trip_proven"]}),
            "residue_ledger": RESIDUE_LEDGER_REL.as_posix(),
        },
        "residue_files": residue_rows,
        "anomalies": anomalies,
        "duration_s": round(time.monotonic() - started, 3),
    }
    common.write_stage_report(ctx, NAME, report)
    common.append_event(ctx, "loc-run", {
        "locales": len(locales), "categories_parsed": files_emitted,
        "records": records_emitted, "anomalies": len(anomalies),
        "legacy_files_handled": len(residue_rows),
        "segments_marked_fffd": report["legacy_encoding"]["segments_marked_fffd"],
    })
    result = {"files": files_emitted, "records": records_emitted,
              "residue_files": len(residue_rows)}
    if anomalies:
        raise common.StageFailure(
            NAME, "%d unhandled loc anomaly class(es); emitted %d of %d "
                  "walked txt — details in census/stage-reports/loc-jsonl.json. "
                  "Exit 3 is reserved for these classes; legacy-encoded files "
                  "recovered-or-marked under the declared-codec policy do not "
                  "fail the stage." % (len(anomalies), files_emitted, total_txt))
    return result
