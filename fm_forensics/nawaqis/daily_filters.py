#!/usr/bin/env python3
"""📉📈🧬 فلاترُ الشموع اليوميّة للمعلّقات: ②-4 `T-FPRINT` (`--item fprint`) و②-5 `T-DIVERGE` (`--item diverge`).

  shard <k> --item I --dir D   — إشارةُ البند لإدخالات CURRENT (رموزُ الشريحة k من 40) من شموع Polygon اليوميّة المسوّاة.
  assemble --item I --dir D    — الحكمُ بحرف FILTER_PROTOCOL ⟵ `T_FPRINT_RESULT.md` أو `T_DIVERGE_RESULT.md`.
كلُّ بندٍ يُشغَّل وحدَه وبترتيبه · قراءةٌ فقط · لا تلغرام · لا إنتاج · لا CONFIG.
"""
import datetime as dt
import glob
import gzip
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import filter_core as FC                                         # noqa: E402
import tbook as TB                                               # noqa: E402

ITEMS = {"diverge": ("T_DIVERGE_prereg.md", "e73289d03db2ed37c67b4b8ac0e3985a90a70c1080e6932ba9ec750b7917e33c", "T_DIVERGE_RESULT.md", "📉📈 `T-DIVERGE` «الدايفرجنس القاعيّ»"),
         "fprint": ("T_FPRINT_prereg.md", "5c07898f56f75befec904aa7de27fd489a297617b99b5ec19809879e6bd216d3", "T_FPRINT_RESULT.md", "🧬 `T-FPRINT` «بصمةُ السهم قبل انفجاراته»")}
BARS_FROM = "2019-01-01"
BARS_TO = "2026-11-16"
RC_OK, RC_KEY, RC_POP, RC_CONTRACT = 0, 2, 5, 11


def log(m=""):
    print(m, flush=True)


def contract_ok(item):
    f, sha, _r, _t = ITEMS[item]
    return FC.sha_of(os.path.join(HERE, f)) == sha and FC.sha_of(FC.PROTOCOL) == TB.PROTOCOL_SHA


# ── مؤشّراتٌ نقيّة ───────────────────────────────────────────────────────────────
def ema(xs, n):
    k, out, e = 2.0 / (n + 1), [], None
    for x in xs:
        e = x if e is None else e + k * (x - e)
        out.append(e)
    return out


def macd_line(closes):
    return [a - b for a, b in zip(ema(closes, 12), ema(closes, 26))]


def kdj_j(highs, lows, closes, n=9):
    K, D, out = 50.0, 50.0, []
    for i in range(len(closes)):
        hh, ll = max(highs[max(0, i - n + 1):i + 1]), min(lows[max(0, i - n + 1):i + 1])
        rsv = 50.0 if hh == ll else (closes[i] - ll) / (hh - ll) * 100.0
        K = 2.0 / 3.0 * K + rsv / 3.0
        D = 2.0 / 3.0 * D + K / 3.0
        out.append(3 * K - 2 * D)
    return out


def rsi14(closes, n=14):
    out, ag, al = [None] * len(closes), None, None
    for i in range(1, len(closes)):
        ch = closes[i] - closes[i - 1]
        g, l_ = max(ch, 0.0), max(-ch, 0.0)
        if i <= n:
            ag = (ag or 0.0) + g / n
            al = (al or 0.0) + l_ / n
            if i == n:
                out[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
            continue
        ag = (ag * (n - 1) + g) / n
        al = (al * (n - 1) + l_) / n
        out[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return out


def divergence(highs, lows, closes, i):
    """(نقيّة) ②-5 عند الصفّ i (يوم القرار) ⟵ {V، macd، kdj} أو None إن قلّت الشموع عن 60."""
    if i < 59:
        return None
    w2 = range(i - 9, i + 1)
    w1 = range(i - 29, i - 9)
    i2 = min(w2, key=lambda j: (lows[j], -j))
    i1 = min(w1, key=lambda j: (lows[j], -j))
    lower = lows[i2] < lows[i1]
    m = macd_line(closes[:i + 1])
    kj = kdj_j(highs[:i + 1], lows[:i + 1], closes[:i + 1])
    mac, kd = lower and m[i2] > m[i1], lower and kj[i2] > kj[i1]
    return {"V": bool(mac or kd), "macd": bool(mac), "kdj": bool(kd)}


def _corr(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((x - mb) ** 2 for x in b)
    if va <= 0 or vb <= 0:
        return 0.0
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(va * vb)


def window_feats(highs, lows, closes, vols, rsi, end, n=20):
    s = end - n + 1
    if s < 0 or any(rsi[j] is None for j in range(s, end + 1)) or closes[s] <= 0:
        return None
    mv = sum(vols[s:end + 1]) / n
    lo = min(lows[s:end + 1])
    return {"shape": [math.log(closes[j] / closes[s]) if closes[j] > 0 else 0.0 for j in range(s, end + 1)],
            "width": (max(highs[s:end + 1]) - lo) / lo if lo > 0 else 0.0,
            "vol": [(vols[j] / mv) if mv > 0 else 0.0 for j in range(s, end + 1)],
            "rsi": [rsi[j] for j in range(s, end + 1)]}


def similarity(a, b):
    w = 1.0 - abs(a["width"] - b["width"]) / max(a["width"], b["width"]) if max(a["width"], b["width"]) > 0 else 1.0
    return (_corr(a["shape"], b["shape"]) + _corr(a["vol"], b["vol"]) + _corr(a["rsi"], b["rsi"]) + w) / 4.0


def explosions(closes, upto):
    """(نقيّة) أيّامُ الانفجار E ‏≤ upto: إغلاقٌ ‏≥ 2× أدنى إغلاقٍ في العشرين قبله · فاصلُ 40 جلسة ⟵ [(E، b)]."""
    out, last = [], -10_000
    for e in range(20, upto + 1):
        if e - last < 40:
            continue
        prior = closes[e - 20:e]
        mn = min(prior)
        if mn > 0 and closes[e] >= 2 * mn:
            b = e - 20 + prior.index(mn)
            out.append((e, b))
            last = e
    return out


def fprint(highs, lows, closes, vols, i, thr=0.5):
    """(نقيّة) ②-4 عند الصفّ i ⟵ None خارج المجتمع (انفجاران سابقان فأكثر بـE ‏≤ i−20) · وإلّا {F، score، n_ev}."""
    ev = explosions(closes, i - 20)
    if len(ev) < 2:
        return "out"
    rsi = rsi14(closes[:i + 1])
    cur = window_feats(highs, lows, closes, vols, rsi, i)
    if cur is None:
        return None
    sims = [similarity(cur, p) for _e, b in ev for p in [window_feats(highs, lows, closes, vols, rsi, b)] if p]
    if not sims:
        return None
    sc = max(sims)
    return {"F": sc >= thr, "score": round(sc, 4), "n_ev": len(ev)}


# ── الرنر ───────────────────────────────────────────────────────────────────────
def _bars(sym, key):
    js = TB._get(f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/day/{BARS_FROM}/{BARS_TO}?adjusted=true&sort=asc&limit=50000&apiKey={key}") or {}
    return [(dt.datetime.utcfromtimestamp(x["t"] / 1000).date().isoformat(), x["h"], x["l"], x["c"], x.get("v") or 0.0)
            for x in js.get("results") or []]


def mode_shard(key, k, item, d_in):
    recs, n = FC.load_shards(d_in)
    if n != FC.NSHARDS:
        log(f"⛔ الشرائح {n} لا {FC.NSHARDS} — خروج 5")
        return RC_POP
    cur = FC.current(recs)
    syms = sorted({r["sym"] for r in cur})[k::FC.NSHARDS]
    by = {}
    for r in cur:
        if r["sym"] in set(syms):
            by.setdefault(r["sym"], set()).add(r["d"])
    out, why, t0 = {}, {}, time.time()
    for j, sym in enumerate(sorted(by)):
        rows = _bars(sym, key)
        days = [x[0] for x in rows]
        H, Lw, C, V = [x[1] for x in rows], [x[2] for x in rows], [x[3] for x in rows], [x[4] for x in rows]
        for d in sorted(by[sym]):
            if d not in days:
                out[f"{sym}|{d}"] = None
                why["لا شمعة"] = why.get("لا شمعة", 0) + 1
                continue
            i = days.index(d)
            v = divergence(H, Lw, C, i) if item == "diverge" else fprint(H, Lw, C, V, i)
            if v == "out":
                out[f"{sym}|{d}"] = "out"
                why["خارج المجتمع"] = why.get("خارج المجتمع", 0) + 1
                continue
            out[f"{sym}|{d}"] = v
            if v is None:
                why["شموع"] = why.get("شموع", 0) + 1
        if j % 25 == 0:
            log(f"{item} شريحة {k}: {j + 1}/{len(by)} رمزًا · {round(time.time() - t0)}s")
    os.makedirs(TB.OUT, exist_ok=True)
    with gzip.open(os.path.join(TB.OUT, f"{item}_shard_{k:02d}.json.gz"), "wt", encoding="utf-8") as fh:
        json.dump({"shard": k, "why": why, "sig": out}, fh, ensure_ascii=False)
    log(f"📦 {item} شريحة {k}: {len(out)} إدخالًا · {why}")
    return RC_OK


def mode_assemble(item, d_in):
    import market_calendar as MC
    _f, _s, res_name, title = ITEMS[item]
    recs, n = FC.load_shards(d_in)
    paths = sorted(glob.glob(os.path.join(d_in, "**", f"{item}_shard_*.json.gz"), recursive=True))
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
    fld = "V" if item == "diverge" else "F"
    pop = recs
    if item == "fprint":                                          # المجتمعُ: لرمزه انفجاران سابقان فأكثر
        pop = [r for r in recs if raw.get(f"{r['sym']}|{r['d']}") != "out"]
    sig = {tuple(k.split("|")): (None if (v is None or v == "out") else bool(v[fld])) for k, v in raw.items()}
    ev = FC.evaluate(pop, sig, FC.last_sessions(TB._sessions("2026-01-01", FC.WIN_END, MC)))
    known = [v for v in raw.values() if isinstance(v, dict)]
    L = [f"# {title} — النتيجة", "",
         f"> العقد `{_f}` · القاعدة `FILTER_PROTOCOL.md` · شرائحُ T-BASKET `{FC.BASKET_RUN}`.", "",
         f"- محسوبة {len(known)} · {fld} = True {sum(1 for v in known if v[fld])} · أسبابُ غير المحسوب {why}"]
    if item == "diverge":
        L.append(f"- وصفًا: MACD وحدَه {sum(1 for v in known if v['macd'])} · KDJ وحدَه {sum(1 for v in known if v['kdj'])}")
    else:
        for y in FC.YEARS:
            cy = [r for r in FC.current(recs) if r["y"] == y]
            py = [r for r in FC.current(pop) if r["y"] == y]
            L.append(f"- {y}: المجتمع {len(py)} من {len(cy)} إدخالَ CURRENT ({(len(py) / len(cy) * 100) if cy else 0:.1f}%)")
    L.append("")
    L += FC.report_lines(ev, "الحاكم (بالأضعف)")
    txt = "\n".join(L) + "\n"
    open(os.path.join(HERE, res_name), "w", encoding="utf-8").write(txt)
    print(txt)
    log(f"⚖️ {item}: {ev['verdict']}")
    return RC_OK


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    item = argv[argv.index("--item") + 1] if "--item" in argv else ""
    if item not in ITEMS:
        log("⛔ --item diverge | fprint")
        return 1
    if not contract_ok(item):
        log("⛔ العقد أو البروتوكول لا يطابق بصمتَه — خروج 11 قبل أيّ جلب")
        return RC_CONTRACT
    mode = argv[0] if argv else ""
    d_in = argv[argv.index("--dir") + 1] if "--dir" in argv else "nq_in"
    if mode == "assemble":
        return mode_assemble(item, d_in)
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log("⛔ بلا مفتاح Polygon — خروج 2")
        return RC_KEY
    if mode == "shard":
        return mode_shard(key, int(argv[1]), item, d_in)
    return 1


if __name__ == "__main__":
    sys.exit(main())
