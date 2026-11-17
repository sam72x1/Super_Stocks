#!/usr/bin/env python3
"""🔣 `T-UNIFORM` «المشتريات الموحّدة» (المعلّقات ②-2 · العقد `T_UNIFORM_prereg.md` · القاعدةُ `FILTER_PROTOCOL.md`).

الأوضاع:
  accept                — بوّابةُ القبول على أمثلة فيصل الثلاثة (ADIL · TRUG · ZCMD) ⟵ خروج 0 تعبر (2 من 3) · 12 لا تعبر.
  shard <k> --dir D     — الإشارةُ U لإدخالات CURRENT (رموزُ الشريحة k من 40).
  assemble --dir D      — الحكمُ بحرف FILTER_PROTOCOL ⟵ `T_UNIFORM_RESULT.md`.
قراءةٌ فقط · لا تلغرام · لا إنتاج · لا CONFIG. المساعداتُ من `tbook.py` بالاسم.
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

CONTRACT = os.path.join(HERE, "T_UNIFORM_prereg.md")
CONTRACT_SHA = "eee2053b24333d695d4a36599f5b899735958497ea7a3fe81433c105dfc7689d"
RESULT = os.path.join(HERE, "T_UNIFORM_RESULT.md")
SIZES = (1, 3, 5, 7, 10)
MIN_LEN = 4
MAX_GAP_NS = 10 * 1_000_000_000
NSESS = 5
MAX_PAGES = 40
SEARCH = ("2024-01-02", "2026-11-13")
ZCMD_DAY = "2026-07-02"
RC_OK, RC_KEY, RC_POP, RC_CONTRACT, RC_GATE = 0, 2, 5, 11, 12


def log(m=""):
    print(m, flush=True)


def contracts_ok():
    return FC.sha_of(CONTRACT) == CONTRACT_SHA and FC.sha_of(FC.PROTOCOL) == TB.PROTOCOL_SHA


def runs(trades, sizes=SIZES, min_len=MIN_LEN, max_gap_ns=MAX_GAP_NS):
    """(نقيّة) الشريطُ [(ns، سعر، حجم)] بترتيبه ⟵ السلاسل [{size، n، t0، t1، prices}]: متتاليةٌ في الشريط بحجمٍ واحدٍ ∈ sizes وفواصلُها ‏≤ max_gap."""
    out, cur = [], []

    def _close():
        if len(cur) >= min_len:
            out.append({"size": int(cur[0][2]), "n": len(cur), "t0": cur[0][0], "t1": cur[-1][0], "prices": sorted({p for _t, p, _s in cur})})
    for t, p, s in trades:
        s = float(s)
        ok = s == int(s) and int(s) in sizes
        if cur and ok and int(s) == int(cur[-1][2]) and t - cur[-1][0] <= max_gap_ns:
            cur.append((t, p, s))
            continue
        _close()
        cur = [(t, p, s)] if ok else []
    _close()
    return out


def trades_day(sym, day, key, a=(4, 0), b=(20, 0)):
    """شريطُ الجلسة [(ns، سعر، حجم)] بترتيبه · None عند تعذّرٍ أو تجاوز السقف."""
    url = (f"https://api.polygon.io/v3/trades/{sym}?timestamp.gte={TB.ny_ns(day, a)}&timestamp.lt={TB.ny_ns(day, b)}"
           f"&order=asc&sort=timestamp&limit=50000&apiKey={key}")
    rows, pages = [], 0
    while url:
        js = TB._get(url)
        if js is None:
            return None
        for x in js.get("results") or []:
            if x.get("price") and x.get("size"):
                rows.append((int(x.get("sip_timestamp") or 0), int(x.get("sequence_number") or 0), float(x["price"]), float(x["size"])))
        pages += 1
        nxt = js.get("next_url")
        if nxt and pages >= MAX_PAGES:
            return None
        url = (nxt + f"&apiKey={key}") if nxt else None
    rows.sort(key=lambda r: (r[0], r[1]))
    return [(t, p, s) for t, _q, p, s in rows]


def adil_pass(rs, day):
    """(نقيّة) سلسلةٌ بحجم 3 كلُّ صفقاتها بين 10:05:00 و10:09:00 نيويورك."""
    lo, hi = TB.ny_ns(day, (10, 5)), TB.ny_ns(day, (10, 9))
    return any(r["size"] == 3 and lo <= r["t0"] and r["t1"] <= hi for r in rs)


def trug_cluster(trades, price=1.30, size=2.0, need=6, span_ns=4_000_000_000):
    """(نقيّة) أوّلُ لحظةٍ يبدأ عندها `need` صفقةٍ بحجم 2 عند 1.30 خلال 4 ثوانٍ · None إن غابت."""
    ts = [t for t, p, s in trades if abs(p - price) < 1e-9 and s == size]
    for i in range(len(ts) - need + 1):
        if ts[i + need - 1] - ts[i] <= span_ns:
            return ts[i]
    return None


def trug_pass(rs, t_cluster, price=1.30, near_ns=2_000_000_000):
    return t_cluster is not None and any(price in r["prices"] and r["t0"] - near_ns <= t_cluster <= r["t1"] + near_ns for r in rs)


def mode_accept(key):
    res = {}
    daily = TB.daily_raw("ADIL", SEARCH[0], SEARCH[1], key)
    cands = [dt.datetime.utcfromtimestamp(x["t"] / 1000).date().isoformat() for x in daily if x["l"] <= 1.77 <= x["h"]]
    a_day = None
    for d in cands:
        w = trades_day("ADIL", d, key, (10, 5), (10, 9)) or []
        if sum(1 for _t, p, s in w if abs(p - 1.77) < 1e-9 and s == 3) >= 4:
            a_day = d
            break
    a_ok = bool(a_day) and adil_pass(runs(trades_day("ADIL", a_day, key) or []), a_day)
    log(f"🔎 ADIL: أيّامٌ مرشّحة {len(cands)} · يومُ المثال {a_day or '—'} · {'✅ يعبر' if a_ok else '❌ لا يعبر'}")
    res["ADIL"] = a_ok
    daily = TB.daily_raw("TRUG", SEARCH[0], SEARCH[1], key)
    cands = [dt.datetime.utcfromtimestamp(x["t"] / 1000).date().isoformat() for x in daily if x["l"] <= 1.30 <= x["h"]]
    t_ok, t_day = False, None
    for d in cands:
        tr = trades_day("TRUG", d, key) or []
        tc = trug_cluster(tr)
        if tc is not None:
            t_day = t_day or d
            if trug_pass(runs(tr), tc):
                t_ok, t_day = True, d
                break
    log(f"🔎 TRUG: أيّامٌ مرشّحة {len(cands)} · أوّلُ يومٍ بعنقود الحجم 2 عند 1.30 {t_day or '—'} · {'✅ يعبر' if t_ok else '❌ لا يعبر'}")
    res["TRUG"] = t_ok
    zr = runs(trades_day("ZCMD", ZCMD_DAY, key) or [])
    res["ZCMD"] = bool(zr)
    log(f"🔎 ZCMD {ZCMD_DAY}: سلاسلُ U {len(zr)} (بالأحجام {sorted({r['size'] for r in zr})}) · {'✅ يعبر' if zr else '❌ لا يعبر'}")
    n = sum(res.values())
    log(f"🚪 القبول: {n} من 3 ⟵ {'✅ يعبر — يُقاس فلترًا' if n >= 2 else '❌ لا يعبر — توقّفٌ ويُبلَغ المالك'}")
    return RC_OK if n >= 2 else RC_GATE


def mode_shard(key, k, d_in):
    import market_calendar as MC
    recs, n = FC.load_shards(d_in)
    if n != FC.NSHARDS:
        log(f"⛔ الشرائح {n} لا {FC.NSHARDS} — خروج 5")
        return RC_POP
    cur = FC.current(recs)
    syms = set(sorted({r["sym"] for r in cur})[k::FC.NSHARDS])
    ents = sorted({(r["sym"], r["d"]) for r in cur if r["sym"] in syms})
    sess = TB._sessions("2022-10-01", "2026-11-16", MC)
    pos = {d: i for i, d in enumerate(sess)}
    out, cache, why, t0 = {}, {}, {}, time.time()
    for j, (sym, d) in enumerate(ents):
        i = pos.get(d)
        win = sess[max(0, i - NSESS + 1):i + 1] if i is not None else []
        found, bad, nruns = False, False, 0
        for s in win:
            if (sym, s) not in cache:
                tr = trades_day(sym, s, key)
                cache[(sym, s)] = None if tr is None else len(runs(tr))
            if cache[(sym, s)] is None:
                bad = True
                break
            nruns += cache[(sym, s)]
        if bad or len(win) < NSESS:
            out[f"{sym}|{d}"] = None
            why["شريط"] = why.get("شريط", 0) + 1
            continue
        found = nruns > 0
        out[f"{sym}|{d}"] = {"U": found, "runs": nruns}
        if j % 20 == 0:
            log(f"T-UNIFORM شريحة {k}: {j + 1}/{len(ents)} · {round(time.time() - t0)}s")
    os.makedirs(TB.OUT, exist_ok=True)
    with gzip.open(os.path.join(TB.OUT, f"uniform_shard_{k:02d}.json.gz"), "wt", encoding="utf-8") as fh:
        json.dump({"shard": k, "entries": len(ents), "none_why": why, "sig": out}, fh, ensure_ascii=False)
    log(f"📦 شريحة {k}: إدخالات {len(ents)} · محسوبة {sum(1 for v in out.values() if v)} · None {why}")
    return RC_OK


def mode_assemble(d_in):
    import market_calendar as MC
    recs, n = FC.load_shards(d_in)
    paths = sorted(glob.glob(os.path.join(d_in, "**", "uniform_shard_*.json.gz"), recursive=True))
    if n != FC.NSHARDS or len(paths) != FC.NSHARDS:
        log(f"⛔ الشرائح {n}/{len(paths)} لا {FC.NSHARDS} — خروج 5")
        return RC_POP
    raw, why = {}, {}
    for p in paths:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            js = json.load(fh)
        raw.update(js["sig"])
        for k_, v in (js.get("none_why") or {}).items():
            why[k_] = why.get(k_, 0) + v
    sig = {tuple(k.split("|")): (None if v is None else bool(v["U"])) for k, v in raw.items()}
    ev = FC.evaluate(recs, sig, FC.last_sessions(TB._sessions("2026-01-01", FC.WIN_END, MC)))
    known = [v for v in raw.values() if v]
    L = ["# 🔣 `T-UNIFORM` «المشتريات الموحّدة» — النتيجة", "",
         f"> العقد `T_UNIFORM_prereg.md` · القاعدة `FILTER_PROTOCOL.md` · شرائحُ T-BASKET `{FC.BASKET_RUN}` · الإشارة: سلسلةُ 4 صفقاتٍ متتاليةٍ فأكثر بحجمٍ ∈ "
         "{1,3,5,7,10} بفواصل ‏≤10 ث في الجلسات الخمس حتى يوم القرار.", "",
         f"- محسوبة {len(known)} · U = True {sum(1 for v in known if v['U'])} ({(sum(1 for v in known if v['U']) / len(known) * 100) if known else 0:.1f}%) · "
         f"None {sum(1 for v in raw.values() if v is None)} بأسبابها {why}", ""]
    L += FC.report_lines(ev, "الحاكم (بالأضعف)")
    L += ["", "## حدودُ الصدق", "- لا هويّةَ للمتداول: السلسلةُ قد تكون صانعَ سوقٍ أو تقسيمَ أمرٍ كبير · وتوقيتُ لقطتَي TRUG/ADIL غيرُ مؤكَّد."]
    txt = "\n".join(L) + "\n"
    open(RESULT, "w", encoding="utf-8").write(txt)
    print(txt)
    log(f"⚖️ T-UNIFORM: {ev['verdict']}")
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
    if mode == "accept":
        return mode_accept(key)
    if mode == "shard":
        return mode_shard(key, int(argv[1]), d_in)
    log("الأوضاع: accept · shard <k> --dir D · assemble --dir D")
    return 1


if __name__ == "__main__":
    sys.exit(main())
