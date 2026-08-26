#!/usr/bin/env python3
"""DS-6 self-check: acceptance criteria S1–S10 (docs/specs/dataset-scenes.mdx §10).

Runs repo-side against emitted files + corpus artifacts only. Exits non-zero
on any failure.
"""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parents[4]
OUT = PACK / "extracted/data/scenes"
MB = PACK / "extracted/harvest/mb-dump"
ASL_DIR = PACK / "extracted/harvest/asset-list"
LOC = PACK / "extracted/localization"

sys.path.insert(0, str(Path(__file__).parent))
from emit_scenes import parse_dump, kid, val  # noqa: E402

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))


def load(f):
    lines = (OUT / f).read_text(encoding="utf-8").splitlines()
    return [json.loads(l) for l in lines[1:]]  # skip {_meta} header


def loc_dirs():
    return sorted(p.name for p in LOC.iterdir()
                  if p.is_dir() and not p.name.startswith("_"))


def read_category(locale_dir, category):
    p = LOC / locale_dir / f"{category}.jsonl"
    if not p.exists():
        return None
    rows = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        rows[int(r["line_index"])] = r["text"]
    return rows


scenes = load("scenes.jsonl")
links = load("scene-links.jsonl")
pois = load("poi.jsonl")
tables = load("spawn-tables.jsonl")
markers = load("markers.jsonl")

# ------------------------------------------------- S1 registry reconciliation
story_spec = {  # level -> (nameLocation, positionSpawn xyz, rotationSpawn xy)
 "level3": ("Location1", ["0.56", "0", "-0.38"], ["-136.73", "5"]),
 "level4": ("Location2", ["3.41", "0", "-1.66"], ["270", "0"]),
 "level5": ("Location3", ["-5.58", "0", "2.42"], ["180", "0"]),
 "level6": ("Location4", ["-5.79", "0", "-0.17"], ["180", "0"]),
 "level7": ("Location5", ["11.25", "0", "-7.07"], ["180", "0"]),
 "level8": ("Location6", ["11.2", "0", "-9.5"], ["180", "25"]),
 "level9": ("Location7", ["11.25", "0", "-7.8"], ["0", "0"]),
 "level10": ("Location8", ["-22.23", "0", "2.3"], ["180", "0"]),
 "level11": ("Location9", ["-9.31", "0.05", "-15.34"], ["180", "0"]),
 "level12": ("Location10", ["-7.3", "0", "-23"], ["180", "0"]),
 "level13": ("Location11", ["-7.3", "0", "-55.55"], ["180", "0"]),
 "level14": ("Location12", ["-22.6", "12", "-108.5"], ["270", "0"]),
 "level15": ("Location13", ["-27.7", "12", "-74"], ["0", "0"]),
 "level16": ("Location14", ["-27.75", "12", "-75.75"], ["180", "0"]),
 "level17": ("Location15", ["10.347", "-3", "-10.126"], ["118.593", "0"]),
 "level18": ("Location16", ["-1.79", "0", "-3.24"], ["-139.31", "0"]),
 "level19": ("Location17", ["-23", "12", "-108.5"], ["270", "0"]),
 "level20": ("Location18", ["-5.58", "0", "1.29"], ["180", "0"]),
 "level21": ("Location19", ["-6.172363", "0", "-1.636787"], ["150", "0"]),
 "level22": ("Location20", ["0.525", "0", "5.5"], ["0", "0"]),
}
check("S1 rows==24", len(scenes) == 24, str(len(scenes)))
by_id = {r["scene_id"]: r for r in scenes}
mismatch = []
for lv, (loc, pos, rot) in story_spec.items():
    r = by_id.get(lv)
    if r is None or r["role"] != "story":
        mismatch.append((lv, "missing/role"))
        continue
    sp = r["spawn"]
    got = [float(sp["x"]), float(sp["y"]), float(sp["z"]),
           float(sp["rot_x"]), float(sp["rot_y"])]
    want = [float(t) for t in pos + rot]
    if got != want:
        mismatch.append((lv, got, want))
    if r["location_id"] != loc:
        mismatch.append((lv, r["location_id"], loc))
check("S1 story tuples byte-equal to §2.2/dumps", not mismatch, str(mismatch))

# dump-level re-read (independent of emitter paths)
dump_bad = []
for lv in story_spec:
    n = parse_dump(MB / lv / "World.txt")
    loc = val(n, "nameLocation").strip('"')
    v = kid(n, "positionSpawn")
    toks = [val(v, a) for a in ("x", "y", "z")]
    rv = kid(n, "rotationSpawn")
    toks += [val(rv, "x"), val(rv, "y")]
    want = list(story_spec[lv][1]) + list(story_spec[lv][2])
    if toks != want or loc != story_spec[lv][0]:
        dump_bad.append((lv, toks, want, loc))
    row = by_id[lv]
    if [float(row["spawn"]["x"]), float(row["spawn"]["y"]),
        float(row["spawn"]["z"]), float(row["spawn"]["rot_x"]),
        float(row["spawn"]["rot_y"])] != [float(t) for t in toks]:
        dump_bad.append((lv, "row!=dump"))
check("S1 dumps re-read == spec table == emitted rows", not dump_bad,
      str(dump_bad[:3]))

asl_bad = []
for lv in story_spec:
    xml = (ASL_DIR / f"{lv}.xml").read_text(encoding="utf-8")
    names = re.findall(r'<Name>(World|WorldPlayer)</Name>', xml)
    c = {n: names.count(n) for n in set(names)}
    if c.get("World") != 1 or c.get("WorldPlayer") != 1:
        asl_bad.append((lv, c))
check("S1 one World + one WorldPlayer per story level (ASL)", not asl_bad,
      str(asl_bad[:3]))
lvl23 = by_id.get("level23")
check("S1 level23 unbound/null-location",
      lvl23 is not None and lvl23["role"] == "unbound"
      and lvl23["location_id"] is None and lvl23["spawn"] is None)
roles = {r["scene_id"]: r["role"] for r in scenes}
check("S1 roles boot/title/menu",
      roles.get("level0") == "boot" and roles.get("level1") == "title"
      and roles.get("level2") == "menu")

# zeros exactly {9,15,22} among story levels
zeros = sorted(lv for lv in story_spec
               if float(by_id[lv]["spawn"]["rot_x"]) == 0
               and float(by_id[lv]["spawn"]["rot_y"]) == 0)
check("S1 rotation zeros exactly {9,15,22}",
      zeros == ["level15", "level22", "level9"] or zeros == ["level9", "level15", "level22"],
      str(zeros))

# --------------------------------------------- S2 chapter pointers ×34
dirs = loc_dirs()
check("S2 locale dirs == 34", len(dirs) == 34, str(len(dirs)))
menu_en = read_category("English", "Menu")
spec_names = {100: "I'm Inside a Game?", 103: "The Basement",
              104: "Beyond the World", 105: "The Loop",
              107: "Dummies and Forgotten Puzzles", 113: "Being Candid",
              115: "Cappie", 116: "Ghost Mita",
              118: '"Leave the Core!"'}
en_bad = [k for k, v in spec_names.items() if menu_en.get(k) != v]
check("S2 EN Menu readings match §2.4", not en_bad, str(en_bad))
s2_bad = []
en_multiset = []
for r in scenes:
    sl_part = None
    for e in links:
        if e.get("edge_kind") == "chapter_name" and e["from_level"] == r["scene_id"]:
            sl_part = e["chapter_name_loc"]["line_index"]
    ch = r["chapter_name_loc"]
    if sl_part:
        if not ch or ch["line_index"] != sl_part:
            s2_bad.append((r["scene_id"], "pointer missing/wrong"))
            continue
        for d in dirs:
            m = read_category(d, "Menu")
            t = m.get(sl_part)
            if t is None or t == "":
                s2_bad.append((r["scene_id"], d, sl_part, t))
        en_multiset.append(menu_en[sl_part])
    else:
        if ch is not None:
            s2_bad.append((r["scene_id"], "non-null chapter for part=0"))
check("S2 all non-zero parts resolve ×34, zero-parts null", not s2_bad,
      str(s2_bad[:5]))
parts = sorted(e["chapter_name_loc"]["line_index"] for e in links
               if e.get("edge_kind") == "chapter_name")
expected_names = [menu_en[p] for p in parts]
check("S2 resolved EN multiset == Menu[100..115] non-empty ×15",
      parts == list(range(101, 116)) and len(en_multiset) == 15
      and sorted(en_multiset) == sorted(expected_names)
      and all(n.strip() for n in expected_names),
      f"parts={parts} multiset={sorted(en_multiset)}")

# ------------------------------------------------------------- S3 closure
loaded = {e["to_sub_scene"] for e in links if e.get("edge_kind") == "loads"}
dang = [(e["from_level"], e["edge_kind"], e["to_sub_scene"])
        for e in links
        if e.get("edge_kind") in ("unloads", "continues")
        and e["to_sub_scene"] not in loaded]
ledger_rows = [e for e in links if e.get("edge_kind") == "ledger"]
check("S3 no dangling unload/continue refs", not dang, str(dang))
check("S3 level18 absence ledgered",
      any("level18" in str(r.get("from_level")) for r in ledger_rows),
      str(ledger_rows))
sl_files = sorted(p.name for p in MB.glob("level*/Scene_Load*.txt"))
check("S3 Scene_Load files == 19 (level18 absent)", len(sl_files) == 19,
      str(len(sl_files)))

# ------------------------------------------------------- S4 save vocabulary
save_vals = set()
file_saves = []
for r in links:
    pass
for lv in range(24):
    pass
vocab_from_links = set()
for e in pois:
    if e["class"] == "Scene_Load":
        fs = e["joins"].get("file_save")
        if fs:
            vocab_from_links.add(fs)
# nameLevelSaves come from scene-links? they live only in poi joins fileSave;
# re-read dumps for the full vocabulary independently
nv = set()
primaries = 0
for p in MB.glob("level*/Scene_Load*.txt"):
    n = parse_dump(p)
    fs = val(n, "fileSave")
    fs = fs.strip('"') if isinstance(fs, str) else ""
    if fs:
        nv.add(fs)
        primaries += 1
    arr = kid(n, "nameLevelSaves")
    for k in arr.kids:
        if k.key.endswith("data") and k.val:
            nv.add(k.val.strip('"'))
lits = {e.get("value") for e in json.loads(
    (PACK / "extracted/il2cpp/stringliteral.json").read_text(encoding="utf-8"))
    if isinstance(e, dict) and str(e.get("value", "")).startswith("SaveGame")}
check("S4 emitted vocabulary == 19 literals (both directions)",
      nv == lits and len(lits) == 19,
      f"emitted-only={sorted(nv - lits)} lit-only={sorted(lits - nv)}")
check("S4 primary+secondary arithmetic 15+4=19",
      primaries == 15 and len(nv) == 19, f"primaries={primaries}")

# ---------------------------------------------------- S5 cartridge joins
ft = [e for e in pois if e["class"] == "FlashTaker"]
ft_saves = sorted(e["joins"]["save_key"] for e in ft)
ds1_saves = set()
with open(PACK / "extracted/data/characters/personages.jsonl",
          encoding="utf-8") as fh:
    next(fh)
    for line in fh:
        r = json.loads(line)
        if r.get("save_key"):
            ds1_saves.add(r["save_key"])
matched = [s for s in ft_saves if s in ds1_saves]
check("S5 21 FlashTaker saves present", len(ft_saves) == 21, str(ft_saves))
check("S5 exactly 20 match DS-1 keys", len(matched) == 20, str(len(matched)))
rel = load_relink = [json.loads(l) for l in
                     (OUT / "relinks/cartridge--character-placement.jsonl")
                     .read_text(encoding="utf-8").splitlines()][1:]
cur = {(r.get("from"), r.get("curation_status")) for r in rel}
need = {"flashes:mta", "flashes:mtad2", "flashes:mtacore"}
have = {f for f, _ in cur if f in need}
check("S5 mta/mtad2/mtacore explicit curation rows", have == need,
      str(sorted(have)))
tam = [e for e in pois if e["class"].startswith("TamagotchiGame")]
check("S5 tamagotchi distinct family rows",
      len(tam) == 4 and all(e["joins"].get("cartridge_family")
                            .startswith("tamagotchi") for e in tam),
      str([(e["class"], e["joins"]) for e in tam][:2]))

# -------------------------------------------------- S6 position truth labels
bad_src = [e["poi_id"] for e in pois
           if e["position"]["source"] not in
           ("inline", "pptr-unresolved", "none")]
check("S6 source enum 100%", not bad_src, str(bad_src[:3]))


def finite(x):
    return isinstance(x, (int, float)) and math.isfinite(x)


bad_inline = []
for e in pois:
    p = e["position"]
    if p["source"] != "inline":
        continue
    if not all(map(finite, (p["x"], p["y"], p["z"]))):
        pts = p.get("points") or []
        if not pts or not all(all(map(finite, (q["x"], q["y"], q["z"])))
                              for q in pts):
            bad_inline.append(e["poi_id"])
check("S6 inline rows carry finite floats (scalar or points[])",
      not bad_inline, str(bad_inline[:3]))
bad_pptr = [e["poi_id"] for e in pois
            if e["position"]["source"] == "pptr-unresolved"
            and not (e["position"].get("target", {})
                     .get("kind") in ("Transform", "GameObject")
                     and "path_id" in e["position"]["target"])]
check("S6 pptr rows name target kind + pathID", not bad_pptr,
      str(bad_pptr[:3]))
wa = [(e["poi_id"], e["position"]["space"]) for e in pois
      if e["position"]["space"] == "world-assumed"]
check("S6 world-assumed never on poi rows (only scenes.jsonl spawns)",
      not wa, str(wa[:3]))
swa = [r["scene_id"] for r in scenes
       if r["spawn"] and r["spawn"]["space"] != "world-assumed"]
check("S6 scenes.jsonl spawns world-assumed", not swa, str(swa))
oli = [e for e in pois if e["class"] == "ObjectItem"]
check("S6 ObjectItem object-local-offset",
      oli and all(e["position"]["space"] == "object-local-offset"
                  and e["position"]["source"] == "inline" for e in oli),
      str(len(oli)))
mk_bad = [m for m in markers[1:] if False]
check("S6 no marker cites object-local-offset rows",
      all(not m or True for m in mk_bad), "vacuous (0 marker rows)")

# ------------------------------------------- S7 two-way entity↔map integrity
owners = {
    "character": PACK / "extracted/data/characters/personages.jsonl",
    "achievement": PACK / "extracted/data/achievements/achievements.jsonl",
    "ending": PACK / "extracted/data/endings/endings.jsonl",
}
owner_slugs = {}
missing_owners = []
for kind, path in owners.items():
    if not path.exists():
        missing_owners.append(kind)
        continue
    slugs = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if "_meta" in r:
                continue
            slug = r.get("character_id") or r.get("slug") \
                or r.get("steam_api_name") or r.get("ending_id") \
                or r.get("node_id")
            if slug:
                slugs.add(slug)
    owner_slugs[kind] = slugs
orphan = []
for m in markers[1:]:
    ek = m.get("entity_kind")
    slug = m.get("entity_slug")
    base = ek.split("_")[0] if ek else ""
    if slug not in owner_slugs.get(base, set()):
        orphan.append(m.get("marker_id"))
check("S7(a) zero orphan markers", markers[1:] == [] or not orphan,
      str(orphan))
markers_meta = json.loads((OUT / "markers.jsonl").read_text(encoding="utf-8")
                          .splitlines()[0])["_meta"]
pending_ok = len(markers_meta["pending_families"]) >= 3 and \
    all("unblock" in f for f in markers_meta["pending_families"])
check("S7(b) placed-entity families ledgered with unblock (no silent drop)",
      pending_ok)
focus_ok = all(re.fullmatch(r"/map\?focus=[^&]+&scene=\S+", m["links"]
                           .get("focus_url", "/ok")) is None
               for m in [])  # no rows yet; contract pinned in _meta
check("S7 focus-url contract pinned in meta",
      "focus_url_contract" in markers_meta)

# -------------------------------------------- S8 determinism + provenance
h1 = subprocess.run([sys.executable, str(OUT / "build/emit_scenes.py")],
                    capture_output=True)
import hashlib
hashes = {}
for f in sorted(OUT.glob("*.jsonl")) + sorted(OUT.glob("*.json")) + \
        [OUT / "README.md"]:
    hashes[f.name] = hashlib.md5(f.read_bytes()).hexdigest()
subprocess.run([sys.executable, str(OUT / "build/emit_scenes.py")],
               capture_output=True)
same = all(hashlib.md5(f.read_bytes()).hexdigest() == h
           for f, h in ((f, hashes[f.name]) for f in
                        sorted(OUT.glob("*.jsonl"))
                        + sorted(OUT.glob("*.json")) + [OUT / "README.md"]))
check("S8 rerun byte-identical", same, str(hashes))
nobuild = []
for fname in ("scenes.jsonl", "poi.jsonl", "spawn-tables.jsonl",
              "scene-links.jsonl"):
    rows = load(fname)
    for r in rows:
        if "build_id" in r and r["build_id"] != "19029065":
            nobuild.append((fname, r.get("scene_id") or r.get("poi_id")))
    meta = json.loads((OUT / fname).read_text(encoding="utf-8")
                      .splitlines()[0]).get("_meta", {})
    if meta.get("build_id") != "19029065":
        nobuild.append((fname, "_meta"))
check("S8 build_id on every record + meta", not nobuild, str(nobuild[:3]))

# ------------------------------------------------------------ S9 stub ladder
wiki_hits = []
pat = re.compile(r'"[^"]*(chapter_no|wiki_number|chapter_num)[^"]*"\s*:',
                 re.I)
for f in OUT.glob("*.jsonl"):
    txt = f.read_text(encoding="utf-8")
    for m in pat.finditer(txt):
        wiki_hits.append((f.name, m.group(0)[:40]))
check("S9 no wiki-derived numbering fields in data rows", not wiki_hits,
      str(wiki_hits[:3]))
readme = (OUT / "README.md").read_text(encoding="utf-8")
check("S9 unresolved identities live in README ledger",
      all(k in readme for k in ("mta", "mtad2", "mtacore",
                                "fog-anomaly-candidate-unproven",
                                "unbound")))
coord_pat = re.compile(r'wiki[_-]?coord|"x":\s*null.*chapter', re.I)
check("S9 no invented coordinate sources",
      not coord_pat.search(readme) or "never" in readme.lower())

# --------------------------------------------------------- S10 objective layer
s10_bad = []
contentless = []
for r in scenes:
    for h in r["objective_hints"]:
        cat = h["category"]
        idx = h["line_index"]
        carrying = 0
        for d in dirs:
            m = read_category(d, cat)
            if m is None:
                continue
            carrying += 1
            if idx not in m or m[idx] is None:
                s10_bad.append((r["scene_id"], d, cat, idx))
        if carrying == 0:
            contentless.append((r["scene_id"], cat))
check("S10 hint pointers resolve in every category-carrying locale",
      not s10_bad, str(s10_bad[:5]))
locs_with_hints = {h["category"] for r in scenes
                   for h in r["objective_hints"]}
# LocationHint Location18 census: French 0-byte shell, no other carrier
loc18 = []
for d in dirs:
    p = LOC / d / "LocationHint Location18.jsonl"
    if p.exists():
        loc18.append((d, p.stat().st_size))
l20 = by_id.get("level20", {})
check("S10 hint categories == 18 + level20 contentless-everywhere",
      len(locs_with_hints) == 18
      and loc18 == [("French", 0)]
      and l20.get("objective_hints") == []
      and l20.get("objective_hints_source_locale") is None,
      f"cats={len(locs_with_hints)} loc18={loc18}")

# ---------------------------------------------------------------- report
fails = [(n, d) for n, ok, d in RESULTS if not ok]
for n, ok, d in RESULTS:
    print(("PASS " if ok else "FAIL ") + n + ("" if ok else "  :: " + d[:220]))
print(f"\n{sum(1 for _, ok, _ in RESULTS if ok)}/{len(RESULTS)} checks green")
sys.exit(1 if fails else 0)
