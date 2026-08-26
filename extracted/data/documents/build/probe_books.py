#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B-5 probe 2: enumerate book-named localized art per locale (read-only)."""
import io
import os

ART = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..",
                                   "extracted", "art", "localization-art"))
res = {}
for lc in sorted(os.listdir(ART)):
    tex = os.path.join(ART, lc, "Textures")
    hits = []
    if os.path.isdir(tex):
        for root, _d, fs in os.walk(tex):
            rel = os.path.relpath(root, tex).replace(os.sep, "/")
            for fn in fs:
                if "book" in fn.lower():
                    hits.append(rel + "/" + fn)
    res[lc] = sorted(hits)
sets = {}
for lc, h in res.items():
    sets.setdefault(tuple(h), []).append(lc)
out = io.StringIO()
for s, lcs in sorted(sets.items(), key=lambda kv: -len(kv[1])):
    out.write("%d locales:\n" % len(lcs))
    for p in s:
        out.write("    %s\n" % p)
    tail = " ..." if len(lcs) > 6 else ""
    out.write("    -> %s%s\n" % (lcs[:6], tail))
print(out.getvalue())
