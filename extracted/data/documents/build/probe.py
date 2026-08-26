#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B-5 probe: read-only measurements feeding DS-5 emit (buildId 19029065).

Everything here re-measures spec claims from repo artifacts before any row
is emitted (arbiter posture: no log trusted). Outputs to stdout only.
"""
import hashlib
import io
import json
import os
import re
import sys

PACK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
EXTRACTED = os.path.join(PACK, "extracted")
MB = os.path.join(EXTRACTED, "harvest", "mb-dump")
LOC = os.path.join(EXTRACTED, "localization")
ART = os.path.join(EXTRACTED, "art", "localization-art")
DEC = os.path.join(EXTRACTED, "decompiled", "main", "Assembly-CSharp")

LOCALES = sorted(d for d in os.listdir(LOC) if os.path.isdir(os.path.join(LOC, d)) and d != "_ledger")
LEVELS = ["level%d" % n for n in range(0, 24)]


def cat(locale, category):
    p = os.path.join(LOC, locale, category + ".jsonl")
    if not os.path.exists(p):
        return None
    rows = {}
    with io.open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            rows[r["line_index"]] = r["text"]
    return rows


print("== locales:", len(LOCALES))

# --- AC-3: Personages x34, lines 1-14 non-empty, U+FFFD -------------------
personages_counts = set()
fffd = []
missing = []
for lc in LOCALES:
    rows = cat(lc, "Personages")
    if rows is None:
        missing.append((lc, "Personages"))
        continue
    personages_counts.add(len(rows))
    for i in range(1, 15):
        t = rows.get(i)
        if t is None or not t.strip():
            missing.append((lc, "Personages:%d" % i))
        if t and "�" in t:
            fffd.append((lc, "Personages", i))
print("Personages record counts across locales:", sorted(personages_counts))
print("Personages gaps:", missing[:10], "total", len(missing))
print("Personages U+FFFD:", fffd)

menu_fffd = []
menu_missing = []
for lc in LOCALES:
    rows = cat(lc, "Menu") or {}
    for i in list(range(83, 96)):
        t = rows.get(i)
        if t is None or not t.strip():
            menu_missing.append((lc, i))
        if t and "�" in t:
            menu_fffd.append((lc, i))
print("Menu 83-95 gaps:", menu_missing[:10], "total", len(menu_missing), "U+FFFD:", len(menu_fffd))

ach = {}
for lc in LOCALES:
    rows = cat(lc, "Achievements") or {}
    ach[lc] = (rows.get(12), rows.get(13))
en12, en13 = ach["English"]
print("Achievements EN 12/13:", repr(en12), "|", repr(en13))
empty_ach = [(lc, v) for lc, v in ach.items() if not v[0] or not v[1]]
print("Achievements 12/13 empty anywhere:", empty_ach)

# --- AC-8: book art per locale ---------------------------------------------
book_cells = {}
for lc in sorted(os.listdir(ART)):
    tex = os.path.join(ART, lc, "Textures")
    found = {}
    if os.path.isdir(tex):
        for root, _dirs, files in os.walk(tex):
            rel = os.path.relpath(root, tex)
            for fn in files:
                stem, ext = os.path.splitext(fn)
                if ext.lower() != ".webp":
                    continue
                key = (rel.replace("\\", "/"), stem)
                found[key] = True
    cells = []
    for sub, stem in [("Location House", "Books"), ("Location House", "Books1"),
                      ("Location House", "Books2"), ("Location House", "Books4"),
                      ("Location19", "Book 1"), ("Location19", "Book 2"),
                      ("Location19", "Book 3"), ("Location19", "Book 4")]:
        cells.append((sub, stem, found.get((sub, stem), False)))
    book_cells[lc] = cells
counts = {lc: sum(1 for c in cells if c[2]) for lc, cells in book_cells.items()}
print("book art cells 8/8 locales:", sum(1 for v in counts.values() if v == 8), "/", len(counts))
bad = {lc: v for lc, v in counts.items() if v != 8}
print("book art deficient locales:", bad)

# sample one locale's exact relative paths
for p in sorted({(c[0] + "/" + c[1]) for c in book_cells["English"] if c[2]}):
    print("  EN book texture:", p)

# --- negative finding re-measures ------------------------------------------
eng_cats = sorted(f[:-6] for f in os.listdir(os.path.join(LOC, "English")) if f.endswith(".jsonl"))
suspect = [c for c in eng_cats if re.match(r"(?i)(note|document|profile)", c)]
print("English category count:", len(eng_cats), "notes/documents/profiles-like:", suspect)

tr = cat("English", "Translation")
print("Translation.jsonl records:", len(tr) if tr else None,
      "values:", sorted(set(tr.values())) if tr else None)

comic = []
for d in sorted(os.listdir(MB)):
    fs = [f for f in os.listdir(os.path.join(MB, d)) if f.startswith("ComicBook")]
    if fs:
        comic.append(d)
print("ComicBook dumps in %d containers:" % len(comic), comic)

# long-Text scan (corpus-wide, Text*.txt only)
long_texts = []
text_files = 0
for d in sorted(os.listdir(MB)):
    dd = os.path.join(MB, d)
    for fn in os.listdir(dd):
        if not fn.startswith("Text"):
            continue
        text_files += 1
        p = os.path.join(dd, fn)
        with io.open(p, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                m = re.match(r"^\tstring m_Text = \"(.*)\"\s*$", line.rstrip("\n"))
                if m and len(m.group(1)) > 60:
                    long_texts.append((d, fn, len(m.group(1))))
                break_outer = False
        # only first m_Text occurrence matters? no - count all
print("Text* dump files scanned:", text_files)
print("long (>60 char) m_Text occurrences:", len(long_texts))

# --- R2: second-profile-registry sweep --------------------------------------
mp = []
for d in sorted(os.listdir(MB)):
    fs = [f for f in os.listdir(os.path.join(MB, d)) if f.startswith("MenuPersonage")]
    if fs:
        mp.append((d, fs))
print("MenuPersonage dumps:", mp)

namesave_classes = set()
if os.path.isdir(DEC):
    for fn in os.listdir(DEC):
        if fn.endswith(".cs"):
            with io.open(os.path.join(DEC, fn), encoding="utf-8", errors="replace") as fh:
                t = fh.read()
            if "nameSave" in t:
                namesave_classes.add(fn[:-3])
            if re.search(r"indexDescriptionStringFile|resourceMita|resourcePlayer", t):
                namesave_classes.add(fn[:-3] + " [registry-field]")
print("classes touching nameSave/resourceMita:", sorted(namesave_classes))

pers_classes = sorted(fn[:-3] for fn in os.listdir(DEC)
                      if fn.endswith(".cs") and re.search(r"(?i)personage|profile", fn))
print("decompiled *Personage*/*Profile* classes:", pers_classes)

# flash-ish literals
lit = json.load(io.open(os.path.join(EXTRACTED, "il2cpp", "stringliteral.json"), encoding="utf-8"))
flashes = [e.get("value") for e in lit if isinstance(e.get("value"), str)
           and e["value"].startswith("/Save")]
print("/Save* literals:", flashes)

# --- dedupe accounting: non-level Unity_Note dumps --------------------------
nonlevel = {}
for d in sorted(os.listdir(MB)):
    if d.startswith("level"):
        continue
    fs = sorted(f for f in os.listdir(os.path.join(MB, d)) if f.startswith("Unity_Note"))
    if fs:
        nonlevel[d] = fs
total_nonlevel = sum(len(v) for v in nonlevel.values())
sig_groups = {}
for d, fs in nonlevel.items():
    for fn in fs:
        with io.open(os.path.join(MB, d, fn), encoding="utf-8") as fh:
            body = fh.read()
        h = hashlib.md5(body.encode("utf-8")).hexdigest()
        sig_groups.setdefault(h, []).append((d, fn))
print("non-level Unity_Note dumps:", total_nonlevel, "in", len(nonlevel), "containers")
print("content-hash groups of non-level note dumps:", len(sig_groups),
      sorted((len(v) for v in sig_groups.values()), reverse=True))
lvl_sigs = {}
for lv in LEVELS:
    ld = os.path.join(MB, lv)
    if not os.path.isdir(ld):
        continue
    for fn in os.listdir(ld):
        if fn.startswith("Unity_Note"):
            with io.open(os.path.join(ld, fn), encoding="utf-8") as fh:
                lvl_sigs.setdefault(hashlib.md5(fh.read().encode("utf-8")).hexdigest(), []).append((lv, fn))
all_sigs = dict(sig_groups)
for h, v in lvl_sigs.items():
    all_sigs.setdefault(h, []).extend(v)
print("distinct content hashes ALL 258 note dumps:", len(all_sigs))
print("nonlevel container counts:", {d: len(v) for d, v in nonlevel.items()})
