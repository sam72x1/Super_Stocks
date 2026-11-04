#!/usr/bin/env python3
"""🕯️📅③ `T-DATE-CANDLES` — الملحق 3: القارئ v2 والمعايرة وإعادةُ التشغيل (قراءةٌ فقط · بلا شبكة).

`T_DATE_CANDLES_ADDENDUM_3.md` (مدموجٌ قبل أيّ رقم):
- `pop3`: المجتمعُ = الـ357 المجمَّدة في `data/population2.json` ‏+ صورُ B46 (`SCAN.json` لدفعة `B46_20261104`) بقواعد الملحق 2 §③ ·
  ونسخةُ B46 (`new=D`) لعضوٍ في عنقود الـ357 ⟵ «نسخة» والعضوُ باقٍ (§⑥).
- `cards`: القارئ v2 (`auto_card.CARD_VERSION`) لكلّ عضو ⟵ `data/cards_v2.jsonl` · و`--check` يعيد البناءَ بايتًا.
- `calib_set`: §⑤ — المعروفُ تاريخُه من الـ43 ذو البطاقة الناجحة ⟵ ترتيبٌ بـ`sha256` ⟵ أوّلُ 20 (أو كلُّها) ⟵ `data/calib_set.json`.
- `curve`: نتائجُ `DCC` المحصودة (`data/calib_results.jsonl`) ⟵ المنحنى والاختيار (`select_m`) ⟵ مطبوع.
"""
from __future__ import annotations

import collections
import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
DATA = os.path.join(HERE, "data")
POP2 = os.path.join(DATA, "population2.json")
POP3 = os.path.join(DATA, "population3.json")
CARDS2 = os.path.join(DATA, "cards_v2.jsonl")
CALIB_SET = os.path.join(DATA, "calib_set.json")
CALIB_RES = os.path.join(DATA, "calib_results.jsonl")
B46_SCAN = os.path.join(ROOT, "faisal_method_v41", "final_protocol", "intake", "B46_20261104", "SCAN.json")
GRID = (1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0)   # §⑤
CALIB_N = 20
CALIB_MIN_N = 10
HIT_FRAC = 0.85                                                     # 17 من 20


def _h(x: str) -> str:
    return hashlib.sha256(x.encode()).hexdigest()


def pop3(pop2: dict, recs: dict, inv: dict, disk: dict, b46: list) -> dict:
    """نقيّة: الـ357 كما هي ‏+ أعضاءُ B46 بقواعد `corpus.population` ⟵ {"members", "b46_excluded", "b46_members"}."""
    import corpus as CP                                            # noqa: PLC0415
    in_cluster = {}
    for m in pop2["members"]:
        for f in [m["cluster"]] + list(m.get("members") or []):
            in_cluster[f] = m["file"]
    sub = {f: disk[f] for f in b46 if f in disk}
    ex = [{"file": f, "why": "ليست على القرص"} for f in b46 if f not in disk]
    keep = {}
    for f in sorted(sub):
        r = recs.get(f) or {}
        if r.get("new") == "D" and r.get("dup_of") in in_cluster:
            ex.append({"file": f, "why": f"نسخةٌ لـ{r['dup_of']} في عنقود العضو {in_cluster[r['dup_of']]}"})
            continue
        keep[f] = sub[f]
    p = CP.population(recs, inv, keep, {})
    ex += p["excluded"]
    members = list(pop2["members"]) + [dict(m, b46=True) for m in p["members"]]
    return {"members": members, "b46_members": [m["file"] for m in p["members"]], "b46_excluded": ex,
            "disk": len(disk)}


def calib_set(pop2: dict, cards: dict) -> dict:
    """§⑤: المعروفُ تاريخُه من الـ357 ذو البطاقة الناجحة بالقارئ v2 ⟵ أوّلُ 20 بـ`sha256`."""
    k = [m for m in pop2["members"] if m.get("known") and (cards.get(m["file"]) or {}).get("ok")]
    k = sorted(k, key=lambda m: _h(m["file"]))
    pick = k[:CALIB_N]
    return {"n_known": sum(1 for m in pop2["members"] if m.get("known")), "n_with_card": len(k),
            "set": [{"file": m["file"], "symbol": m["symbol"], "frame": m["frame"], "truth": m["known"]["truth"],
                     "src": m["known"].get("src", "")} for m in pick]}


def curve(rows: list, grid=GRID, key: str = "lv") -> list:
    """نقيّة: [(m، الإصابات، الكاذبة)] — الإصابة `r_true ≤ m` · والكاذبةُ صورةٌ فيها `r_false ≤ m`."""
    out = []
    for m in grid:
        hit = sum(1 for r in rows if r.get(f"{key}_true") and r[f"{key}_true"][0] <= m)
        fal = sum(1 for r in rows if r.get(f"{key}_false") and r[f"{key}_false"][0] <= m)
        out.append((m, hit, fal))
    return out


def select_m(cv: list, n: int):
    """§⑤: أصغرُ `m` يصيب ⌈0.85·N⌉ فأكثر وكاذبتُه صفر ⟵ (m، السبب) · و`N` دون 10 ⟵ (None، «لا معايرة»)
    · ولا `m` ⟵ (1.0، «لا تسامح يحقّق الشرط — m = 1»)."""
    if n < CALIB_MIN_N:
        return None, f"لا معايرة (N = {n} دون {CALIB_MIN_N})"
    need = math.ceil(HIT_FRAC * n)
    for m, hit, fal in cv:
        if hit >= need and fal == 0:
            return m, f"أصغرُ m يصيب {need} من {n} فأكثر بلا كاذبة"
    return 1.0, f"لا m يصيب {need} من {n} بلا كاذبة ⟵ التسامحُ يبقى m = 1"


def _load_b46() -> list:
    d = json.load(open(B46_SCAN, encoding="utf-8"))
    return [os.path.splitext(it["image_id"])[0] for it in d["items"]]


def build():
    """§⑥/§⑤: المجتمعُ 3 ‏+ بطاقاتُ v2 ‏+ مجموعةُ المعايرة — حتميّةٌ من القارئ المختوم والصور والسجلّات."""
    import auto_card as AC                                         # noqa: PLC0415
    import chart_pixels as P                                       # noqa: PLC0415
    import corpus as CP                                            # noqa: PLC0415
    recs, inv, disk = CP.load()
    pop2 = json.load(open(POP2, encoding="utf-8"))
    p3 = pop3(pop2, recs, inv, disk, _load_b46())
    lines, cards = [], {}
    for m in p3["members"]:
        card = AC.build_card(P.load_rgb(CP._ext(os.path.join(ROOT, "faisal_images"), m["file"])), recs[m["file"]]["seen"],
                             version=AC.CARD_V2)
        card.update({"id": m["file"], "symbol": m["symbol"], "frame": m["frame"]})
        cards[m["file"]] = card
        lines.append(json.dumps(card, ensure_ascii=False, sort_keys=True))
    cs = calib_set(pop2, cards)
    return p3, lines, cs, cards


def summary(p3, cards, cs) -> list:
    v1 = {}
    for ln in open(os.path.join(DATA, "cards.jsonl"), encoding="utf-8"):
        if ln.strip():
            c = json.loads(ln)
            v1[c["id"]] = bool(c.get("ok"))
    ok2 = {i for i, c in cards.items() if c.get("ok")}
    in357 = {m["file"] for m in p3["members"] if not m.get("b46")}
    kept = sum(1 for i, ok in v1.items() if ok and i in ok2)
    why = collections.Counter(c.get("why", "") for c in cards.values() if not c.get("ok"))
    return [f"🧮 المجتمع 3: {len(p3['members'])} (الـ357 ‏+ B46 {len(p3['b46_members'])} · B46 المستبعَد {len(p3['b46_excluded'])})",
            f"🃏 بطاقاتُ v2: {len(ok2)} من {len(cards)} · منها في الـ357 {len(ok2 & in357)} (كانت v1 ‏{sum(v1.values())}) · "
            f"بقي من بطاقات v1 الناجحة {kept} من {sum(v1.values())}",
            "   أسبابُ الفشل: " + " · ".join(f"{k} {v}" for k, v in why.most_common()),
            f"🎯 مجموعةُ المعايرة: المعروفُ {cs['n_known']} · ذو بطاقة v2 {cs['n_with_card']} ⟵ N = {len(cs['set'])}"]


def curve_lines(rows: list) -> list:
    n = len(rows)
    L = [f"📈 المنحنى (N = {n}) — مع قيد المستوى (يحكم):", "   m | الإصابات | الكاذبة"]
    cv = curve(rows, key="lv")
    for m, h, f in cv:
        L.append(f"   {m:g} | {h} من {n} | {f}")
    m_star, why = select_m(cv, n)
    L.append(f"⚖️ الاختيار: m* = {m_star} — {why}")
    L.append("   وصفًا بلا قيد المستوى: " + " · ".join(f"{m:g}:{h}/{f}" for m, h, f in curve(rows, key="sh")))
    for r in sorted(rows, key=lambda r: r["id"]):
        L.append(f"   {r['id']} {r['symbol']} {r['frame']} الحقيقة {r['truth']} · r_true "
                 f"{(r.get('lv_true') or ['—'])[0]} · r_false {(r.get('lv_false') or ['—'])[0]}"
                 f" ({(r.get('lv_false') or ['', '—'])[1]})")
    return L


# ── ③ الجدولُ والعدّ (§⑥) ─────────────────────────────────────────────────────────────────────────────────────
MATCH3 = os.path.join(DATA, "match_results_v3.jsonl")
TABLE3 = os.path.join(DATA, "candles_table_v3.tsv")
DERIVED3 = os.path.join(DATA, "candles_derived_v3.tsv")


def table3():
    """§⑥: صفٌّ لكلّ عضوٍ في المجتمع 3 بأعمدة الملحق 2 ‏+ `m` و«عند m = 1» ⟵ (الصفوف، صفوفُ candles المؤهَّلة، التعارض)
    — بتعريفات `results` بالاسم (`recorded` · `side_hit` · `fingerprint`)."""
    import csv as _csv                                             # noqa: PLC0415
    import corpus as CP                                            # noqa: PLC0415
    import f0                                                      # noqa: PLC0415
    import results as RS                                           # noqa: PLC0415
    p3 = json.load(open(POP3, encoding="utf-8"))
    cards = {}
    for ln in open(CARDS2, encoding="utf-8"):
        if ln.strip():
            c = json.loads(ln)
            cards[c["id"]] = c
    res = {}
    for ln in open(MATCH3, encoding="utf-8"):
        if ln.strip():
            r = json.loads(ln)
            res[r["id"]] = r
    recs, _inv, _disk = CP.load()
    rows_t = list(_csv.DictReader(open(os.path.join(ROOT, "faisal_levels_table.tsv"), encoding="utf-8"), delimiter="\t"))
    unit_dates = {(r["symbol"], r["line"]): (("", "") if r["date_source"] == "candles" else (r["date"], r["date_source"]))
                  for r in rows_t}
    mp = list(_csv.DictReader(open(os.path.join(HERE, "data", "image_map.tsv"), encoding="utf-8"), delimiter="\t"))
    mapping_units = collections.defaultdict(list)
    for m in mp:
        if m["confidence"] in f0.MAP_FOUND and m["disk_file"]:
            for u in [x for x in (m.get("units") or "").split(",") if "|" in x]:
                sym, line = u.split("|", 1)
                mapping_units[os.path.splitext(m["disk_file"])[0]].append((sym, line))
    out = []
    for mbr in p3["members"]:
        fid = mbr["file"]
        c = cards.get(fid) or {}
        r = res.get(fid) or {}
        t1 = r.get("top1") or {}
        rd, rs = RS.recorded(fid, recs, mapping_units, unit_dates)
        kt = (mbr.get("known") or {}).get("truth", "")
        lab = r.get("label", "") if c.get("ok") else ""
        hit = RS.side_hit(mbr["frame"], t1.get("end", ""), kt) if (kt and lab in ("واثق", "مرجّح")) else None
        out.append({"file": fid, "symbol": mbr["symbol"], "frame": mbr["frame"], "b46": "1" if mbr.get("b46") else "",
                    "card": "ok" if c.get("ok") else "no", "label": lab or ("—" if not c.get("ok") else "لم يُطابَق"),
                    "last_bar": t1.get("end", ""), "k": t1.get("k", ""), "k_split": t1.get("k_exp", ""),
                    "variant": t1.get("variant", ""), "rms": t1.get("rms", ""), "passers": r.get("passers", ""),
                    "m": r.get("mult", 1.0) if c.get("ok") else "", "label_m1": (r.get("at_m1") or {}).get("label", lab),
                    "recorded_date": rd, "recorded_src": rs, "known_truth": kt,
                    "side_hit": "" if hit is None else ("1" if hit else "0"),
                    "why": c.get("why", "") if not c.get("ok") else r.get("why", "")})
    der, conflict = [], []
    by_unit = collections.defaultdict(list)
    for row in out:
        if row["label"] != "واثق":
            continue
        for u in mapping_units.get(row["file"], []):
            d = unit_dates.get(u)
            if d is not None and not d[0]:
                by_unit[u].append(row)
    for u, rows in sorted(by_unit.items()):
        days = sorted({x["last_bar"][:10] for x in rows})
        if len(days) > 1 and RS.sessions_apart(days[0], days[-1]) > 1:
            conflict.append((u, days))
            continue
        x = sorted(rows, key=lambda x: x["last_bar"])[-1]
        der.append({"symbol": u[0], "line": u[1], "date": x["last_bar"][:10], "method": "candles",
                    "fingerprint": RS.fingerprint(x), "max_diff": x["rms"], "witness": "واثق (تجريبيّ)",
                    "run_id": (res.get(x["file"]) or {}).get("run", "")})
    return p3, out, der, conflict


TCOLS = ["file", "symbol", "frame", "b46", "card", "label", "label_m1", "m", "last_bar", "k", "k_split", "variant", "rms",
         "passers", "recorded_date", "recorded_src", "known_truth", "side_hit", "why"]

def main(argv) -> int:
    import closed                                                  # noqa: PLC0415  🔒 الملحق 5 §⑤
    _rc = closed.gate("v3", argv)
    if _rc is not None:
        return _rc
    mode = argv[1] if len(argv) > 1 else "build"
    if mode in ("table", "table-check"):
        import results as RS                                       # noqa: PLC0415
        p3, out, der, conflict = table3()
        t, d = RS._tsv(out, TCOLS), RS._tsv(der, RS.DCOLS)
        if mode == "table-check":
            same = open(TABLE3, encoding="utf-8").read() == t and open(DERIVED3, encoding="utf-8").read() == d
            print("✅ جدولُ ③ مطابقٌ بايتًا" if same else "❌ جدولُ ③ يختلف")
            return 0 if same else 1
        open(TABLE3, "w", encoding="utf-8").write(t)
        open(DERIVED3, "w", encoding="utf-8").write(d)
        print("\n".join(RS.summary(p3, out, der, conflict)))
        lab1 = collections.Counter(r["label_m1"] for r in out if r["card"] == "ok")
        print("   عند m = 1 على البطاقات نفسِها: " + " · ".join(f"{k} {v}" for k, v in lab1.most_common()))
        return 0
    if mode == "curve":
        rows = {}
        for ln in open(CALIB_RES, encoding="utf-8"):
            if ln.strip():
                r = json.loads(ln)
                rows[r["id"]] = r
        print("\n".join(curve_lines([r for r in rows.values() if "lv_true" in r])))
        return 0
    p3, lines, cs, cards = build()
    body = "\n".join(lines) + "\n"
    pj = json.dumps(p3, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    cj = json.dumps(cs, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if mode == "--check":
        same = all(open(p, encoding="utf-8").read() == b for p, b in ((CARDS2, body), (POP3, pj), (CALIB_SET, cj)))
        print("✅ بطاقاتُ v2 والمجتمعُ 3 ومجموعةُ المعايرة مطابقةٌ بايتًا" if same else "❌ إعادةُ البناء تختلف")
        return 0 if same else 1
    for p, b in ((CARDS2, body), (POP3, pj), (CALIB_SET, cj)):
        open(p, "w", encoding="utf-8").write(b)
    print("\n".join(summary(p3, cards, cs)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
