#!/usr/bin/env python3
"""🪜 `T-SUPPORT2` «الدعمُ الثاني» (المعلّقات ②-3 · العقد `T_SUPPORT2_prereg.md`).

  shard <k> --dir D     — لإدخالات CURRENT (رموزُ الشريحة k من 40): المستوى ⟵ الصعود 15% ⟵ الرجوع ±5% ⟵ صفقةُ آلة السلة بالاسم ‏+ ضوابطُها.
  assemble --dir D      — (أ) و(ب) بالأضعف ⟵ `T_SUPPORT2_RESULT.md`.
`D` يحمل شرائحَ T-BASKET وملفَّي `basket-prep` (`basket_rbprep.json.gz` · `basket_extra.json.gz`). قراءةٌ فقط · لا تلغرام · لا إنتاج.
"""
import datetime as dt
import glob
import gzip
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import filter_core as FC                                         # noqa: E402
import tbook as TB                                               # noqa: E402

CONTRACT = os.path.join(HERE, "T_SUPPORT2_prereg.md")
CONTRACT_SHA = "a5ba12d911608ed808b87e18f5fe1a24fe859c735836bba69becb375cc29d98c"
RESULT = os.path.join(HERE, "T_SUPPORT2_RESULT.md")
RISE = 1.15
BAND_HI, BAND_LO = 1.05, 0.95
WIN = 20
WITNESS_D = "2026-10-16"                                         # §② شاهدُ CDT: مستوى آخر أيّام القرار
ARMS = (("orders", None), ("orders", 0.50))
RC_OK, RC_KEY, RC_POP, RC_CONTRACT = 0, 2, 5, 11


def log(m=""):
    print(m, flush=True)


def contracts_ok():
    return FC.sha_of(CONTRACT) == CONTRACT_SHA and FC.sha_of(FC.PROTOCOL) == TB.PROTOCOL_SHA


def second_entry(bars, L, rise=RISE, hi=BAND_HI, lo=BAND_LO):
    """(نقيّة) bars = [(يوم، أعلى، أدنى، إغلاق)] للجلسات العشرين بعد d بترتيبها ⟵ (الحالة، يومُ الصعود، يومُ الرجوع d′).
    الحالة: ok · no_rise · no_return · broke."""
    up = next((i for i, b in enumerate(bars) if b[1] >= rise * L), None)
    if up is None:
        return "no_rise", None, None
    for b in bars[up + 1:]:
        if b[2] <= hi * L:
            return ("ok", bars[up][0], b[0]) if b[3] >= lo * L else ("broke", bars[up][0], b[0])
    return "no_return", bars[up][0], None


def _adj_daily(sym, a, b, key):
    js = TB._get(f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/day/{a}/{b}?adjusted=true&sort=asc&limit=5000&apiKey={key}") or {}
    return [(dt.datetime.utcfromtimestamp(x["t"] / 1000).date().isoformat(), x["o"], x["h"], x["l"], x["c"], x["v"])
            for x in js.get("results") or []]


def _basket_mod():
    return FC._basket()


def mode_shard(key, k, d_in):
    import pandas as pd
    os.environ["FAISAL_ONLY"] = "0"
    import Super_stock as S
    B = _basket_mod()
    recs, n = FC.load_shards(d_in)
    if n != FC.NSHARDS:
        log(f"⛔ الشرائح {n} لا {FC.NSHARDS} — خروج 5")
        return RC_POP
    prep = B._jload(glob.glob(os.path.join(d_in, "**", "basket_rbprep.json.gz"), recursive=True)[0])
    extra = B._jload(glob.glob(os.path.join(d_in, "**", "basket_extra.json.gz"), recursive=True)[0])
    allsess = extra["allsess"]
    pos = {d: i for i, d in enumerate(allsess)}
    cur = FC.current(recs)
    syms = set(sorted({r["sym"] for r in cur})[k::FC.NSHARDS])
    ents = sorted({(r["sym"], r["d"]) for r in cur if r["sym"] in syms})
    if k == 0 and ("CDT", WITNESS_D) not in ents:
        ents.append(("CDT", WITNESS_D))                          # §② الشاهدُ وصفًا (لا يدخل الحكم: ليس إدخالَ CURRENT)
    out, why, fcache, ccache, t0 = {}, {}, {}, {}, time.time()
    dcache = {}
    for j, (sym, d) in enumerate(ents):
        i = pos.get(d)
        if i is None or i + WIN >= len(allsess):
            why["نافذة"] = why.get("نافذة", 0) + 1
            out[f"{sym}|{d}"] = {"st": "window"}
            continue
        win = allsess[i + 1:i + 1 + WIN]
        if sym not in dcache:
            dcache[sym] = _adj_daily(sym, "2022-08-01", "2026-11-16", key)
        rows = dcache[sym]
        hist = [x for x in rows if x[0] <= d and x[0] >= (dt.date.fromisoformat(d) - dt.timedelta(90)).isoformat()]
        L = None
        if len(hist) >= 10:
            df = pd.DataFrame({"Open": [x[1] for x in hist], "High": [x[2] for x in hist], "Low": [x[3] for x in hist],
                               "Close": [x[4] for x in hist], "Volume": [x[5] for x in hist]})
            try:
                L = S.tested_level(df)
            except Exception:                                    # noqa: BLE001
                L = None
        if not L:
            why["لا مستوى"] = why.get("لا مستوى", 0) + 1
            out[f"{sym}|{d}"] = {"st": "no_level"}
            continue
        byday = {x[0]: (x[0], x[2], x[3], x[4]) for x in rows}
        bars = [byday[s] for s in win if s in byday]
        st, d_up, d2 = second_entry(bars, float(L))
        rec = {"st": st, "L": float(L), "up": d_up, "d2": d2}
        if st == "ok":
            i2 = pos.get(d2)
            win2 = allsess[i2 + 1:i2 + 1 + WIN] if i2 is not None else []
            res, tst = B.trade_all(sym, d2, win2, prep["splits"].get(sym), key, list(ARMS), fcache=fcache)
            rec["res"] = {a: ((v or {}).get("r")) for a, v in (res or {}).items()} if res else None
            rec["tst"] = tst
            ctrls = []
            for c in B.ctrl_pick(sym, d2, (extra.get("decs") or {}).get(d2) or {}):
                ck = (c, d2)
                if ck not in ccache:
                    cr, _cst = B.trade_all(c, d2, win2, prep["splits"].get(c), key, list(ARMS), fcache=fcache)
                    ccache[ck] = {a: (v or {}).get("r") for a, v in (cr or {}).items()} if cr else None
                ctrls.append(ccache[ck])
            rec["ctrl"] = ctrls
        why[st] = why.get(st, 0) + 1
        out[f"{sym}|{d}"] = rec
        if j % 20 == 0:
            log(f"T-SUPPORT2 شريحة {k}: {j + 1}/{len(ents)} · {round(time.time() - t0)}s")
    os.makedirs(TB.OUT, exist_ok=True)
    with gzip.open(os.path.join(TB.OUT, f"support2_shard_{k:02d}.json.gz"), "wt", encoding="utf-8") as fh:
        json.dump({"shard": k, "entries": len(ents), "why": why, "sig": out}, fh, ensure_ascii=False)
    log(f"📦 شريحة {k}: إدخالات {len(ents)} · {why}")
    return RC_OK


def evaluate2(recs, raw, last_set=None):
    """(نقيّة عدا البوتستراب) ⟵ {cells, verdict, pooled, last60}: (أ) فائضُ الدخول الثاني · (ب) فائضُه − فائضُ دخول CURRENT الأصليّ."""
    B = _basket_mod()
    orig = {(r["sym"], r["d"]): r for r in FC.current(recs)}
    pts = []
    for k, v in raw.items():
        if not v or v.get("st") != "ok" or not v.get("res"):
            continue
        sym, d = k.split("|")
        if (sym, d) not in orig:                                 # الشاهدُ وصفٌ لا يدخل الحكم
            continue
        pts.append({"sym": sym, "d2": v["d2"], "y": v["d2"][:4], "res": {a: {"r": x} for a, x in v["res"].items() if x is not None},
                    "ctrl": v.get("ctrl") or [], "orig": orig.get((sym, d))})

    def _cell(rows, arm):
        a = [(p["sym"], FC.excess(p, arm)) for p in rows]
        a = [x for x in a if x[1] is not None]
        b = []
        for p in rows:
            e2, e1 = FC.excess(p, arm), (FC.excess(p["orig"], arm) if p.get("orig") else None)
            if e2 is not None and e1 is not None:
                b.append((p["sym"], e2 - e1))
        return {"n_all": len(rows), "coverage": None, "n_true": len(a), "n_false": len(b),
                "a_mean": FC._mean([v for _s, v in a]), "a_ci": B.boot_mean(a) if len(a) >= 2 else None,
                "b_mean": FC._mean([v for _s, v in b]), "b_ci": B.boot_mean(b) if len(b) >= 2 else None,
                "raw_true": FC._mean([float(p["res"][arm]["r"]) for p in rows if arm in p["res"]]),
                "raw_false": FC._mean([float(p["orig"]["res"][arm]["r"]) for p in rows if p.get("orig") and (p["orig"].get("res") or {}).get(arm)]),
                "none": 0}
    cells = {a: {y: _cell([p for p in pts if p["y"] == y], a) for y in FC.YEARS} for a in FC.ARMS}
    verdict = "✅ تعبر"
    for a in FC.ARMS:
        for y in FC.YEARS:
            c = cells[a][y]
            if c["n_true"] < FC.MIN_N or c["n_false"] < FC.MIN_N:
                verdict = "لا قياس"
    if verdict != "لا قياس" and not all((cells[a][y]["a_ci"] or [0])[0] > 0 and (cells[a][y]["b_ci"] or [0])[0] > 0
                                        for a in FC.ARMS for y in FC.YEARS):
        verdict = "❌ لا تعبر"
    pooled = {a: _cell([p for p in pts if p["y"] in FC.YEARS], a) for a in FC.ARMS}
    last = {a: _cell([p for p in pts if last_set and p["d2"] in last_set], a) for a in FC.ARMS} if last_set else None
    return {"cells": cells, "verdict": verdict, "pooled": pooled, "last60": last}


def mode_assemble(d_in):
    import market_calendar as MC
    recs, n = FC.load_shards(d_in)
    paths = sorted(glob.glob(os.path.join(d_in, "**", "support2_shard_*.json.gz"), recursive=True))
    if n != FC.NSHARDS or len(paths) != FC.NSHARDS:
        log(f"⛔ الشرائح {n}/{len(paths)} لا {FC.NSHARDS} — خروج 5")
        return RC_POP
    raw, why = {}, {}
    for p in paths:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            js = json.load(fh)
        raw.update(js["sig"])
        for k_, v in (js.get("why") or {}).items():
            why[k_] = why.get(k_, 0) + v
    ev = evaluate2(recs, raw, FC.last_sessions(TB._sessions("2026-01-01", FC.WIN_END, MC)))
    cdt = {k: v for k, v in raw.items() if k.startswith("CDT|")}
    L = ["# 🪜 `T-SUPPORT2` «الدعمُ الثاني» — النتيجة", "",
         "> العقد `T_SUPPORT2_prereg.md` · آلةُ T-BASKET بالاسم · (أ) فائضُ الدخول الثاني على ضابط الزخم · (ب) فائضُه − فائضُ دخول CURRENT الأصليّ "
         "(في الجدول: «n مع» = (أ) · «n بدون» = أزواجُ (ب) · «r الخام» = الثاني / الأصليّ).", "",
         f"- حالاتُ إدخالات CURRENT: {why}", f"- الشاهد CDT: {cdt or 'ليس بين إدخالات CURRENT'}", ""]
    L += FC.report_lines(ev, "الحاكم (بالأضعف)")
    L += ["", "## حدودُ الصدق", "- الصعودُ والرجوعُ من شموعٍ يوميّة · والعيّنةُ مشروطةٌ بالنجاة 15% أوّلًا · والضابطُ يطابق زخمَ يوم الرجوع لا مسارَ الصعود."]
    txt = "\n".join(L) + "\n"
    open(RESULT, "w", encoding="utf-8").write(txt)
    print(txt)
    log(f"⚖️ T-SUPPORT2: {ev['verdict']}")
    return RC_OK


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not contracts_ok():
        log("⛔ العقد أو البروتوكول لا يطابق بصمتَه — خروج 11 قبل أيّ جلب")
        return RC_CONTRACT
    mode = argv[0] if argv else ""
    d_in = argv[argv.index("--dir") + 1] if "--dir" in argv else "nq_in"
    if mode == "assemble":
        return mode_assemble(d_in)
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log("⛔ بلا مفتاح Polygon — خروج 2")
        return RC_KEY
    if mode == "shard":
        return mode_shard(key, int(argv[1]), d_in)
    log("الأوضاع: shard <k> --dir D · assemble --dir D")
    return 1


if __name__ == "__main__":
    sys.exit(main())
