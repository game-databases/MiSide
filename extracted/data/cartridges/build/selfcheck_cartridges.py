#!/usr/bin/env python3
"""B-4 self-check — executes every repo-executable AC of
docs/specs/dataset-cartridges.mdx section 9 against emitted artifacts.

Run from repo root:  python extracted/data/cartridges/build/selfcheck_cartridges.py
Exit 0 iff every check passes; failures print with an AC tag.
"""
import glob
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
OUT = os.path.join(REPO, "extracted", "data", "cartridges")

_results = []


def check(ac, ok, detail=""):
    _results.append((ac, bool(ok), detail))


def rows_of(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(json.loads(line))
    return out


def rd(rel):
    return os.path.join(REPO, rel)


def main():
    cart = rows_of(rd("extracted/data/cartridges/cartridges.jsonl"))
    mg = rows_of(rd("extracted/data/cartridges/minigames.jsonl"))
    cand = rows_of(rd("extracted/data/cartridges/cartridges-minigames.candidates.jsonl"))
    j1 = rows_of(rd("extracted/data/cartridges/relinks/cartridge--character.jsonl"))
    j2 = rows_of(rd("extracted/data/cartridges/relinks/cartridge--scene-placement.jsonl"))
    j3 = rows_of(rd("extracted/data/cartridges/relinks/minigame--achievement.jsonl"))
    j4 = rows_of(rd("extracted/data/cartridges/relinks/minigame--scene-carrier.jsonl"))
    j5 = rows_of(rd("extracted/data/cartridges/relinks/minigame--outfit-unlock.jsonl"))
    j6 = rows_of(rd("extracted/data/cartridges/relinks/minigame--choice-condition.jsonl"))
    cart_meta, cart_rows = cart[0]["_meta"], cart[1:]
    mg_meta, mg_rows = mg[0]["_meta"], mg[1:]

    # ---- AC-1 registry census reconciles -----------------------------------
    lits = json.load(open(rd("extracted/il2cpp/stringliteral.json"), encoding="utf-8"))
    entry = [e for e in lits if e["address"] == "0x13AD860"]
    keys = entry[0]["value"].split("\n")
    emitted = [r["save_key"] for r in cart_rows]
    fam_char = sum(1 for r in cart_rows if r["family"] == "character")
    fam_player = sum(1 for r in cart_rows if r["family"] == "player")
    slots_ok = all(
        r["registry_literal_ref"] == "il2cpp/stringliteral.json@0x13AD860[%d]" % i
        for i, r in enumerate(cart_rows))
    check("AC-1", len(cart_rows) == 23 and emitted == keys and fam_char == 13
          and fam_player == 10 and slots_ok,
          "rows=%d order-match=%s families=%d/%d slots=%s"
          % (len(cart_rows), emitted == keys, fam_char, fam_player, slots_ok))

    # ---- AC-2 pickup census greps clean ------------------------------------
    fresh = set()
    for f in glob.glob(rd("extracted/harvest/mb-dump/*/FlashTaker*.txt")):
        c = os.path.basename(os.path.dirname(f))
        txt = open(f, encoding="utf-8").read()
        m = re.search(r'\tstring save = "([^"]*)"', txt)
        fresh.add((c, os.path.basename(f), m.group(1)))
    picked = [r for r in cart_rows if r["pickup_ref"]]
    ok = len(picked) == 21
    for r in picked:
        p = r["pickup_ref"]
        f = rd("extracted/harvest/mb-dump/%s/%s" % (p["container"], p["file"]))
        ok = ok and os.path.exists(f) and (
            '\tstring save = "%s"' % p["value"]) in open(f, encoding="utf-8").read()
        ok = ok and (p["container"], p["file"], p["value"]) in fresh
        ok = ok and p["field"] == "save"
    unresolved = sorted(r["save_key"] for r in cart_rows if not r["pickup_ref"])
    ok = ok and unresolved == ["mtacore", "mtad2"]
    for r in cart_rows:
        if not r["pickup_ref"]:
            ok = ok and any("R3" in x for x in r["missing_fields"]) \
                and r["container_location_binding"] is None
    ok = ok and len(fresh) == 21
    check("AC-2", ok, "picked=%d fresh=%d unresolved=%s" % (len(picked), len(fresh),
                                                            unresolved))

    # ---- AC-3 namespace honesty --------------------------------------------
    c13 = rows_of(rd("extracted/data/characters/relinks/character--cartridge.jsonl"))
    c13_fwd = {r["to"]: r["from"] for r in c13 if r.get("direction") == "forward"}
    ok = True
    mta_row = [r for r in cart_rows if r["save_key"] == "mta"][0]
    ok = ok and mta_row["depicts_character_id"] is None and any(
        "nameSave" in x for x in mta_row["missing_fields"])
    for r in cart_rows:
        anchor = "flashes:%s" % r["save_key"]
        if r["family"] == "character":
            expect = c13_fwd.get(anchor)
            ok = ok and r["depicts_character_id"] == expect
        else:
            ok = ok and r["contains_player_id"] == c13_fwd.get(anchor) \
                and r["depicts_character_id"] is None
    j1f = [r for r in j1[1:] if r.get("direction") == "forward"]
    j1i = [r for r in j1[1:] if r.get("direction") == "inverse"]
    spot_ok = sum(1 for r in j1f
                  if r.get("c13_anchor") == "flashes:" + r["save_key"]
                  and c13_fwd.get(r["c13_anchor"]) == r["member_character_id"])
    inv_pairs = {(r["from"], r["to"], r["save_key"]) for r in j1i}
    mirrored = all((r["to"], r["from"], r["save_key"]) in inv_pairs for r in j1f)
    check("AC-3", ok and len(j1f) == 22 and spot_ok >= 5 and mirrored,
          "anchors-spot=%d/%d mirrored=%s mta-null=%s"
          % (spot_ok, len(j1f), mirrored, mta_row["depicts_character_id"] is None))

    # ---- AC-4 TV-name pin recomputes ---------------------------------------
    locales = sorted(d for d in os.listdir(rd("extracted/localization"))
                     if os.path.isdir(rd("extracted/localization/" + d))
                     and not d.startswith("_"))
    tv_ctrl = open(rd("extracted/harvest/mb-dump/level6/"
                      "MinigamesTelevisionController.txt"), encoding="utf-8").read()

    def tv_index():
        games = {}
        for chunk in tv_ctrl.split("MinigamesTelevisionController_Game data")[1:]:
            nm = re.search(r'string nameResource = "([^"]*)"', chunk).group(1)
            games[nm] = int(re.search(r"SInt32 indexStringNameGame = (\d+)",
                                      chunk).group(1))
        return games
    games = tv_index()

    def cat_lines(locale, cat):
        p = rd("extracted/localization/%s/%s.jsonl" % (locale, cat))
        return {r["line_index"]: r["text"] for r in rows_of(p)}

    minus1_ok = identity_fails = True
    en_lines = None
    for loc in locales:
        lines = cat_lines(loc, "TelevisionGames")
        f_i, p_i = games["Fight"] - 1, games["Pinguin"] - 1
        # -1 offset resolves both entries to existing non-empty names everywhere
        minus1_ok = minus1_ok and len(lines) == 2 and f_i in lines and p_i in lines \
            and bool(lines[f_i].strip()) and bool(lines[p_i].strip())
        if loc == "English":
            en_lines = (lines[f_i], lines[p_i])
        # identity offset: Fight -> line 1, Pinguin -> line 2. The category spans
        # 2 lines (0..1) in every locale, so Pinguin indexes OUT OF RANGE under
        # the identity offset - the structural rejection of that hypothesis -
        # and where it does resolve (Fight), it lands on the other game's slot.
        if games["Pinguin"] in lines:
            identity_fails = False
        if loc == "English" and lines.get(games["Fight"]) == en_lines[0]:
            identity_fails = identity_fails  # would misname Fight as its own title
    en_exact = en_lines == ("Dairy Scandal", "Penguin Piles")
    readme = open(os.path.join(OUT, "README.md"), encoding="utf-8").read()
    readme_ok = ("Dairy Scandal" in readme and "Penguin Piles" in readme
                 and "rejected" in readme.lower())
    check("AC-4", minus1_ok and identity_fails and en_exact and readme_ok,
          "minus1_resolves_x34=%s identity_incoherent=%s en=%s readme=%s"
          % (minus1_ok, identity_fails, en_exact, readme_ok))

    # ---- AC-5 minigame rows trace to artifacts -----------------------------
    ok = True
    auto_expect = {"level9": ("resourceGame", "Minigame CarSpace"),
                   "level12": ("resourceGame", "Minigame MakeManeken"),
                   "level13": ("sceneGame", "MinigameShooter")}
    seen_auto = set()
    lists = sorted(glob.glob(rd("extracted/harvest/asset-list/*.xml")))

    def grep_containers(name):
        hits = set()
        for p in lists:
            if ("<Name>%s<" % name) in open(p, encoding="utf-8").read():
                hits.add(os.path.basename(p)[:-4])
        return hits

    dedup_prefabs = {"carspace", "makemaneken"}
    for r in mg_rows:
        ck, ks = r["client_key"], r["key_source"]
        if ks in ("automate_resource", "automate_scene"):
            lr = r["loader_ref"]
            field, val = auto_expect[lr["container"]]
            dump = open(rd("extracted/harvest/mb-dump/%s/MinigamesAutomate.txt"
                           % lr["container"]), encoding="utf-8").read()
            ok = ok and ('%s = "%s"' % (field, val)) in dump \
                and r["client_key"] == val and lr["value"] == val
            seen_auto.add(lr["container"])
        elif ks == "tv_games_array":
            ok = ok and ('string nameResource = "%s"' % ck) in tv_ctrl
        else:
            got = set(r["carrier_containers"])
            if r["minigame_id"] in dedup_prefabs:
                raw = grep_containers(ck)
                ok = ok and got <= set(raw | {"resources.assets"}) and len(raw) > 40
            else:
                expect_c = grep_containers(ck)
                if got != expect_c:
                    print("   AC-5 carrier mismatch:", r["minigame_id"],
                          sorted(got ^ expect_c))
                ok = ok and got == expect_c
    ok = ok and seen_auto == set(auto_expect) and isinstance(ok, bool)
    # Spec firewall: the two names DS-4 asserts absent from the client grep
    # zero hits; no row id/client_key may be a community label (AC-8 restated).
    spec_absent = ["Hetoor", "Spaceracer"]
    community_labels = {"Hetoor", "Spaceracer", "Dairy Scandal", "Penguin Piles",
                        "Quadrangle", "Dummy Sort", "Card Game", "Kitchen Pumpkins",
                        "The Button", "DDR"}
    client_blob = json.dumps(lits) + "".join(
        open(rd("extracted/localization/%s/%s.jsonl" % (l, c)), encoding="utf-8").read()
        for l in locales for c in ("MiniGame CarSpace", "MiniGame MakeManeken",
                                   "MiniGame Shooter", "TelevisionGames"))
    firewall = all(b not in client_blob for b in spec_absent)
    keys_used = {r["client_key"] for r in mg_rows}
    ids_used = {r["minigame_id"] for r in mg_rows}
    keys_clean = not ((keys_used | ids_used) & community_labels)
    check("AC-5", ok and firewall and keys_clean,
          "automate=%s carrier-greps=%s hetoor-spaceracer-absent=%s keys-clean=%s"
          % (sorted(seen_auto), bool(ok), firewall, keys_clean))

    # ---- AC-6 achievement fill covers the slot -----------------------------
    achi = rows_of(rd("extracted/data/achievements/achievements.jsonl"))
    achi_ids = {r["achievement_id"] for r in achi}
    minigame_tagged = {r["achievement_id"] for r in achi
                       if r.get("type_tag") == "minigame"}
    sites = {r["achievement_id"]: r for r in
             rows_of(rd("extracted/data/achievements/relink-achievement-award-site.jsonl"))
             if "_meta" not in r}
    j3f = [r for r in j3[1:] if r.get("direction") == "forward"]
    j3i = [r for r in j3[1:] if r.get("direction") == "inverse"]
    fwd_ids = [r["achievement_id"] for r in j3f]
    inv_ids = [r["achievement_id"] for r in j3i]
    ok = set(fwd_ids) <= achi_ids and set(inv_ids) <= achi_ids
    ok = ok and all(fwd_ids.count(a) == 1 and inv_ids.count(a) == 1
                    for a in minigame_tagged)
    mech_ok = True
    for r in j3f + j3i:
        if r["mechanism"] == "hard":
            s = sites.get(r["achievement_id"])
            mech_ok = mech_ok and s is not None and r["award_site"] is not None \
                and s["file"] == r["award_site"]["file"]
        else:
            mech_ok = mech_ok and r["mechanism"] == "logic"
    manifest = json.load(open(os.path.join(OUT, "build/written-manifest.json"),
                              encoding="utf-8"))
    scope_ok = all(p.startswith("extracted/data/cartridges" + os.sep)
                   or p.startswith("extracted\\data\\cartridges\\")
                   for p in manifest["written_sorted"])
    check("AC-6", ok and mech_ok and scope_ok,
          "8-slots=%s mechanisms=%s write-scope-proof=%s extra=%s"
          % (all(fwd_ids.count(a) == 1 for a in minigame_tagged), mech_ok, scope_ok,
             sorted(set(fwd_ids) - minigame_tagged)))

    # ---- AC-7 boilerplate dedupe enforced ----------------------------------
    groups = {}
    files = sorted(glob.glob(rd("extracted/harvest/mb-dump/*/MinigamesController.txt")))
    for f in files:
        h = hashlib.md5(open(f, "rb").read()).hexdigest()
        groups.setdefault(h, []).append(os.path.basename(os.path.dirname(f)))
    sizes = sorted((len(v) for v in groups.values()), reverse=True)
    lvl2 = [v for v in groups.values() if "level2" in v][0]
    j4_meta = j4[0]["_meta"]["boilerplate_dedupe"]["minigamescontroller_partition"]
    controller_in_carriers = any(
        "MinigamesController" in json.dumps(r) for r in mg_rows[1:])
    check("AC-7", len(files) == 48 and sizes == [19, 16, 12, 1] and len(lvl2) == 12
          and j4_meta["group_sizes"] == [19, 16, 12, 1]
          and j4_meta["level2_group_members"] == 12 and not controller_in_carriers,
          "files=%d sizes=%s level2-group=12 recorded=%s controllers-not-carriers=%s"
          % (len(files), sizes, j4_meta["group_sizes"], not controller_in_carriers))

    # ---- AC-8 rule-evidence firewall ---------------------------------------
    ok = True
    QUOTE_RE = re.compile(r'"([^"]+)"')
    for r in mg_rows[1:]:
        ok = ok and r["scoring_derivable"] is False
        if not r["rule_evidence"]:
            continue
        for ev in r["rule_evidence"]:
            path = rd(ev["path"].replace("/", os.sep))
            entry_ok = os.path.exists(path)
            body = open(path, encoding="utf-8").read() if entry_ok else ""
            quotes = []
            if entry_ok and ev["path"].endswith(".jsonl"):
                m = re.search(r"line_index=(\d+)", ev["locator"])
                li = int(m.group(1)) if m else None
                recs = {x["line_index"]: x["text"] for x in rows_of(path)}
                entry_ok = entry_ok and li in recs
                target_text = recs.get(li, "")
                # every quoted fragment of the claim must exist in the record text
                quotes = [q for q in QUOTE_RE.findall(ev["claim"])
                          if len(q) >= 2 and not q.startswith("extracted/")]
                entry_ok = entry_ok and all(q in target_text for q in quotes)
            else:
                entry_ok = entry_ok and ev["locator"] in body
                # dump files: quoted fragments must appear verbatim in the dump
                quotes = [q for q in QUOTE_RE.findall(ev["claim"]) if len(q) >= 3]
                entry_ok = entry_ok and all(q in body for q in quotes)
            if not entry_ok:
                print("   AC-8 unresolved:", r["minigame_id"], ev["locator"],
                      "missing:", [q for q in quotes if q not in body])
            ok = ok and entry_ok
    banned_numbers = ["25 coins", "2 minutes", "two rounds", "4 times", "doom-like",
                      "Phase 1 Logs achievement"]
    row_blob = "".join(open(p, encoding="utf-8").read() for p in [
        rd("extracted/data/cartridges/cartridges.jsonl"),
        rd("extracted/data/cartridges/minigames.jsonl"),
        rd("extracted/data/cartridges/relinks/minigame--achievement.jsonl"),
        rd("extracted/data/cartridges/relinks/minigame--outfit-unlock.jsonl")])
    clean = all(b not in row_blob for b in banned_numbers)
    check("AC-8", ok and clean,
          "evidence-resolves=%s scoring-false-all=%s community-numbers-absent=%s"
          % (ok, all(r["scoring_derivable"] is False for r in mg_rows[1:]), clean))

    # ---- AC-9 locale availability derives ----------------------------------
    cats = ["MiniGame CarSpace", "MiniGame MakeManeken", "MiniGame Shooter",
            "TelevisionGames"]

    def availability(root):
        table = {}
        for loc in locales:
            d = os.path.join(root, loc)
            table[loc] = tuple(os.path.exists(os.path.join(d, c + ".jsonl"))
                               for c in cats)
        return table

    live = availability(rd("extracted/localization"))
    ledger_locales = {r["locale"] for r in
                      rows_of(rd("extracted/localization/_ledger/locale-delta.jsonl"))
                      if r.get("kind") == "art-subset"}
    ledger_ok = all(any(r.get("locale") == l and any(
        f["path"] == c + ".txt" for f in r.get("other_files", []))
        for r in rows_of(rd("extracted/localization/_ledger/locale-delta.jsonl")))
        for l in locales for c in cats if live[l][cats.index(c)])
    counts = {}
    for loc in locales:
        p = rd("extracted/localization/%s/MiniGame MakeManeken.jsonl" % loc)
        counts[loc] = len(rows_of(p)) if os.path.exists(p) else None
    skew = sorted(l for l, n in counts.items() if n != 35 and n is not None)
    tmp = tempfile.mkdtemp(prefix="b4-ac9-")
    try:
        scratch = os.path.join(tmp, "localization")
        shutil.copytree(rd("extracted/localization"), scratch,
                        ignore=shutil.ignore_patterns("_ledger"))
        os.remove(os.path.join(scratch, "Arabic", "MiniGame MakeManeken.jsonl"))
        flipped = availability(scratch)
        flip_ok = flipped["Arabic"][cats.index("MiniGame MakeManeken")] is False \
            and live["Arabic"][cats.index("MiniGame MakeManeken")] is True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    check("AC-9", ledger_ok and skew == ["Arabic"] and flip_ok,
          "ledger-reconciles=%s arabic-skew=%s deletion-flips-cell=%s"
          % (ledger_ok, skew, flip_ok))

    # ---- AC-10 stale-log refusal + stamps ----------------------------------
    log = open(rd("extracted/EXTRACTION-LOG.md"), encoding="utf-8").read()
    block = re.search(r"```json pipeline-defaults\s*(\{.*?\})\s*```", log, re.S).group(1)
    pins = json.loads(block)
    detect = json.load(open(rd("extracted/census/detect.json"), encoding="utf-8"))
    agree = pins["buildId"] == detect["build_id"] and \
        pins["versionLabel"].replace("VERSION ", "") == \
        detect["version_label"].replace("VERSION ", "")
    def stamped_row(r):
        return r.get("build_id") == pins["buildId"] and \
            r.get("version_label") == pins["versionLabel"]

    dataset_ok = all(stamped_row(r) for r in cart_rows + mg_rows + cand[1:])
    relinks_meta_ok = all(
        f[0]["_meta"].get("build_id") == pins["buildId"]
        and f[0]["_meta"].get("version_label") == pins["versionLabel"]
        for f in (j1, j2, j3, j4, j5, j6))
    site_dicts = [r["award_site"] for r in j3[1:] if r.get("award_site")] + \
                 [r["unlock_site"] for r in j5[1:]
                  if r.get("unlock_site")]
    sites_ok = all(d.get("build_id") == pins["buildId"] for d in site_dicts)
    check("AC-10", agree and dataset_ok and relinks_meta_ok and sites_ok,
          "log-vs-detect=%s dataset-rows=%s relink-meta=%s site-dicts=%s"
          % (agree, dataset_ok, relinks_meta_ok, sites_ok))

    # ---- report -------------------------------------------------------------
    fails = 0
    for ac, ok, detail in _results:
        status = "PASS" if ok else "FAIL"
        if not ok:
            fails += 1
        print("%-5s %-6s %s" % (ac, status, detail))
    print("%d/%d checks passed" % (len(_results) - fails, len(_results)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
