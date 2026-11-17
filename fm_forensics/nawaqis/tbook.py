#!/usr/bin/env python3
"""📗 `T-BOOK` «طلبُ المضارب عند الدعم» (المعلّقات ②-1 · العقد `T_BOOK_prereg.md` · القاعدةُ `FILTER_PROTOCOL.md`).

الأوضاع:
  gate                  — بوّابةُ وحدات الحجم على شاهدَي فيصل (THH 18,440 @1.29 · EHGO 8,113 @1.68 · 11-02…11-06) ⟵ خروج 0 تعبر · 12 لا تعبر.
  shard <k> --dir D     — لإدخالات CURRENT من شرائح T-BASKET تحت D (رموزُ الشريحة k من 40 بالترتيب): المستوى ⟵ الاقتباسات ⟵ الإشارة.
  assemble --dir D      — الإشارات ‏+ الشرائح ⟵ الحكم ⟵ `T_BOOK_RESULT.md` (بحرف FILTER_PROTOCOL).
قراءةٌ فقط · لا تلغرام · لا إنتاج · لا CONFIG.
"""
import datetime as dt
import glob
import gzip
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
import filter_core as FC                                         # noqa: E402

CONTRACT = os.path.join(HERE, "T_BOOK_prereg.md")
CONTRACT_SHA = "78944409f4b966330085b5e8274d822cc684125f19f7bac456ee3ce425a5b11d"
PROTOCOL_SHA = "9887a99f0dee4308ca336812bcc154403f0e9985ef3b3f4690b95d065c59735f"
OUT = os.path.join(HERE, "out")
RESULT = os.path.join(HERE, "T_BOOK_RESULT.md")
BAND = 0.05
USD_MIN = 13_000.0                                               # §① أصغرُ الشاهدَين مقرَّبًا للأسفل
NSESS = 5
SPLIT_DAYS = 45
LOOKBACK_DAYS = 90
MAX_PAGES = 40                                                   # سقفُ صفحات الاقتباس لكلّ جلسة (50,000 للصفحة) ⟵ فوقه None ويُعَدّ
WITNESS = (("THH", 1.29, 18_440), ("EHGO", 1.68, 8_113))
WITNESS_DAYS = ("2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05", "2026-11-06")
WITNESS_TOL = 0.10
RC_OK, RC_KEY, RC_POP, RC_CONTRACT, RC_GATE = 0, 2, 5, 11, 12


def log(m=""):
    print(m, flush=True)


def contracts_ok():
    return (FC.sha_of(CONTRACT) == CONTRACT_SHA) and (FC.sha_of(FC.PROTOCOL) == PROTOCOL_SHA)


def _get(url, tries=4):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "t-book/1"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:                      # noqa: PERF203
            if e.code in (403, 404):
                return None
            time.sleep(2 ** k)
        except Exception:                                        # noqa: BLE001
            time.sleep(2 ** k)
    return None


def ny_ns(day, hhmm):
    """منتصفُ ثانيةٍ بتوقيت نيويورك ⟵ نانوثانية UTC."""
    from zoneinfo import ZoneInfo
    h, m = hhmm
    t = dt.datetime.fromisoformat(day).replace(hour=h, minute=m, tzinfo=ZoneInfo("America/New_York"))
    return int(t.timestamp() * 1_000_000_000)


def quotes_bids(sym, day, key, lo=None, hi=None):
    """اقتباساتُ الجلسة 04:00-20:00 ⟵ [(سعرُ الطلب، حجمُه)] (داخل [lo، hi] إن أُعطيا) · None عند تعذّرٍ أو تجاوز السقف."""
    url = (f"https://api.polygon.io/v3/quotes/{sym}?timestamp.gte={ny_ns(day, (4, 0))}&timestamp.lt={ny_ns(day, (20, 0))}"
           f"&order=asc&sort=timestamp&limit=50000&apiKey={key}")
    out, pages = [], 0
    while url:
        js = _get(url)
        if js is None:
            return None
        for q in js.get("results") or []:
            bp, bs = q.get("bid_price"), q.get("bid_size")
            if bp and bs and bp > 0 and bs > 0 and (lo is None or lo <= bp <= hi):
                out.append((float(bp), float(bs)))
        pages += 1
        nxt = js.get("next_url")
        if nxt and pages >= MAX_PAGES:
            return None
        url = (nxt + f"&apiKey={key}") if nxt else None
    return out


def book_metrics(bids, L, shares_out=None):
    """(نقيّة) اقتباساتُ النطاق [(سعر، حجم)] ⟵ المقاييس والإشارة B بحرف §①."""
    band = [(p, s) for p, s in bids if (1 - BAND) * L <= p <= (1 + BAND) * L]
    if not band:
        return {"n": 0, "max_sh": 0.0, "med_sh": 0.0, "max_usd": 0.0, "max_float": None, "B": False}
    mx = max(s for _p, s in band)
    usd = max(p * s for p, s in band)
    return {"n": len(band), "max_sh": mx, "med_sh": float(statistics.median(s for _p, s in band)), "max_usd": usd,
            "max_float": (mx / shares_out) if shares_out else None, "B": usd >= USD_MIN}


def witness_hit(bids, price, size, tol=WITNESS_TOL):
    """(نقيّة) أكبرُ حجمٍ عند السعر بالضبط ضمن ±tol من الشاهد؟ ⟵ (تعبر، أكبرُ حجم)."""
    at = [s for p, s in bids if abs(p - price) < 1e-9]
    mx = max(at) if at else 0.0
    return (abs(mx - size) <= tol * size, mx)


def mode_gate(key):
    ok_all = True
    for sym, px, size in WITNESS:
        best, any_ok = 0.0, False
        for d in WITNESS_DAYS:
            b = quotes_bids(sym, d, key, px - 1e-6, px + 1e-6) or []
            ok, mx = witness_hit(b, px, size)
            log(f"🔎 {sym} {d}: أكبرُ حجم طلب عند {px} = {mx:,.0f} (الشاهد {size:,})" + (" ✅" if ok else ""))
            best, any_ok = max(best, mx), any_ok or ok
        ok_all = ok_all and any_ok
        log(f"{'✅' if any_ok else '❌'} {sym}: الأكبرُ عبر الجلسات {best:,.0f} مقابل {size:,} (±{WITNESS_TOL:.0%})")
    log(f"🚪 بوّابةُ القبول: {'✅ تعبر' if ok_all else '❌ لا تعبر — توقّفٌ قبل الفلتر'}")
    return RC_OK if ok_all else RC_GATE


def daily_raw(sym, a, b, key):
    js = _get(f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/day/{a}/{b}?adjusted=false&sort=asc&limit=5000&apiKey={key}") or {}
    return js.get("results") or []


def splits_of(sym, key):
    js = _get(f"https://api.polygon.io/v3/reference/splits?ticker={sym}&limit=1000&apiKey={key}") or {}
    return [x.get("execution_date") for x in js.get("results") or [] if x.get("execution_date")]


def shares_out(sym, day, key):
    js = _get(f"https://api.polygon.io/v3/reference/tickers/{sym}?date={day}&apiKey={key}") or {}
    v = (js.get("results") or {}).get("share_class_shares_outstanding")
    return float(v) if v else None


def level_at(sym, d, key, S):
    """§① المستوى `L` بـ`tested_level` بالاسم على الشموع غير المسوّاة حتى `d` · None مع سببه."""
    import pandas as pd
    a = (dt.date.fromisoformat(d) - dt.timedelta(LOOKBACK_DAYS)).isoformat()
    rows = [x for x in daily_raw(sym, a, d, key)
            if dt.datetime.utcfromtimestamp(x["t"] / 1000).date().isoformat() <= d]
    if len(rows) < 10:
        return None, "شموع"
    df = pd.DataFrame({"Open": [x["o"] for x in rows], "High": [x["h"] for x in rows], "Low": [x["l"] for x in rows],
                       "Close": [x["c"] for x in rows], "Volume": [x["v"] for x in rows]})
    try:
        L = S.tested_level(df)
    except Exception:                                            # noqa: BLE001
        return None, "مستوى"
    v = FC.level_value(L)
    return (v, "") if v else (None, "لا مستوى")


def mode_shard(key, k, d_in):
    import market_calendar as MC
    os.environ["FAISAL_ONLY"] = "0"
    import Super_stock as S
    recs, n = FC.load_shards(d_in)
    if n != FC.NSHARDS:
        log(f"⛔ الشرائح {n} لا {FC.NSHARDS} — خروج 5")
        return RC_POP
    cur = FC.current(recs)
    syms = sorted({r["sym"] for r in cur})[k::FC.NSHARDS]
    ents = sorted({(r["sym"], r["d"]) for r in cur if r["sym"] in set(syms)})
    sess_all = _sessions("2022-10-01", "2026-11-16", MC)
    pos = {d: i for i, d in enumerate(sess_all)}
    out, qcache, scache, why = {}, {}, {}, {}
    t0 = time.time()
    for j, (sym, d) in enumerate(ents):
        if sym not in scache:
            scache[sym] = splits_of(sym, key)
        near = [x for x in scache[sym] if 0 <= (dt.date.fromisoformat(d) - dt.date.fromisoformat(x)).days <= SPLIT_DAYS]
        if near:
            out[f"{sym}|{d}"] = None
            why["تقسيم"] = why.get("تقسيم", 0) + 1
            continue
        L, w = level_at(sym, d, key, S)
        if L is None:
            out[f"{sym}|{d}"] = None
            why[w] = why.get(w, 0) + 1
            continue
        i = pos.get(d)
        win = sess_all[max(0, i - NSESS + 1):i + 1] if i is not None else []
        bids, bad = [], False
        for s in win:
            ck = (sym, s)
            if ck not in qcache:
                qcache[ck] = quotes_bids(sym, s, key)
            if qcache[ck] is None:
                bad = True
                break
            bids.extend(qcache[ck])
        if bad or len(win) < NSESS:
            out[f"{sym}|{d}"] = None
            why["اقتباسات"] = why.get("اقتباسات", 0) + 1
            continue
        m = book_metrics(bids, L, shares_out(sym, d, key))
        out[f"{sym}|{d}"] = dict(m, L=L)
        if len(qcache) > 400:
            qcache.clear()
        if j % 20 == 0:
            log(f"T-BOOK شريحة {k}: {j + 1}/{len(ents)} · {round(time.time() - t0)}s")
    os.makedirs(OUT, exist_ok=True)
    with gzip.open(os.path.join(OUT, f"tbook_shard_{k:02d}.json.gz"), "wt", encoding="utf-8") as fh:
        json.dump({"shard": k, "entries": len(ents), "none_why": why, "sig": out}, fh, ensure_ascii=False)
    log(f"📦 شريحة {k}: إدخالات {len(ents)} · محسوبة {sum(1 for v in out.values() if v)} · None {why}")
    return RC_OK


def _sessions(a, b, MC):
    out, d, end = [], dt.date.fromisoformat(a), dt.date.fromisoformat(b)
    while d <= end:
        if d.weekday() < 5 and MC.session_info(d.isoformat()).get("open_ny_min") is not None:
            out.append(d.isoformat())
        d += dt.timedelta(1)
    return out


def terciles(rows, sig_raw, field, arm):
    """وصفٌ: متوسّطُ الفائض لكلّ ثلثٍ من `field` (حدودُ الأثلاث على المحسوب كلِّه)."""
    vals = sorted(v[field] for v in sig_raw.values() if v and v.get(field) is not None)
    if len(vals) < 3:
        return None
    q1, q2 = vals[len(vals) // 3], vals[2 * len(vals) // 3]
    groups = {"منخفض": [], "وسط": [], "مرتفع": []}
    for r in rows:
        v = sig_raw.get(f"{r['sym']}|{r['d']}")
        e = FC.excess(r, arm)
        if not v or v.get(field) is None or e is None:
            continue
        g = "منخفض" if v[field] < q1 else ("وسط" if v[field] < q2 else "مرتفع")
        groups[g].append(e)
    return {g: (len(x), FC._mean(x)) for g, x in groups.items()}


def mode_assemble(d_in):
    import market_calendar as MC
    recs, n = FC.load_shards(d_in)
    if n != FC.NSHARDS:
        log(f"⛔ الشرائح {n} لا {FC.NSHARDS} — خروج 5")
        return RC_POP
    paths = sorted(glob.glob(os.path.join(d_in, "**", "tbook_shard_*.json.gz"), recursive=True))
    if len(paths) != FC.NSHARDS:
        log(f"⛔ شرائحُ T-BOOK {len(paths)} لا {FC.NSHARDS} — خروج 5")
        return RC_POP
    raw, why = {}, {}
    for p in paths:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            js = json.load(fh)
        raw.update(js["sig"])
        for k_, v in (js.get("none_why") or {}).items():
            why[k_] = why.get(k_, 0) + v
    sig = {tuple(k.split("|")): (None if v is None else bool(v["B"])) for k, v in raw.items()}
    last = FC.last_sessions(_sessions("2026-01-01", FC.WIN_END, MC))
    ev = FC.evaluate(recs, sig, last)
    L = ["# 📗 `T-BOOK` «طلبُ المضارب عند الدعم» — النتيجة", "",
         f"> العقد `T_BOOK_prereg.md` · القاعدة `FILTER_PROTOCOL.md` · شرائحُ T-BASKET `{FC.BASKET_RUN}` · الإشارة: أكبرُ قيمة طلبٍ في ±5% من المستوى المختبر "
         f"خلال الجلسات الخمس حتى يوم القرار ‏{USD_MIN:,.0f}$ فأكثر.", "",
         f"- إدخالاتٌ محسوبة {sum(1 for v in raw.values() if v)} · None {sum(1 for v in raw.values() if v is None)} بأسبابها {why}", ""]
    L += FC.report_lines(ev, "الحاكم (بالأضعف)")
    L += ["", "## وصفٌ: الأثلاث (متوسّطُ الفائض · n) — بلا حكم", ""]
    cur = FC.current(recs)
    for field, nm in (("max_usd", "أكبرُ قيمة طلب"), ("med_sh", "وسيطُ حجم الطلب"), ("max_float", "أكبرُ حجم ÷ الأسهم القائمة")):
        for a in FC.ARMS:
            for y in FC.YEARS:
                t = terciles([r for r in cur if r["y"] == y], raw, field, a)
                if t:
                    L.append(f"- {nm} · {a} · {y}: " + " · ".join(f"{g} {FC.pct(m)} (n {c})" for g, (c, m) in t.items()))
    L += ["", "## حدودُ الصدق", "- **NBBO قمّةُ الدفتر لا عمقُه** — أكبرُ «أفضل طلب» ليس أكبرَ طلبٍ في الدفتر ولا هويّةَ للطالب.",
          "- الحجمُ المعروض قد يجمع عدّةَ متداولين عند السعر · والأسهمُ القائمة ليست الفلوت · والحدُّ 13,000$ من شاهدَين في 2026."]
    txt = "\n".join(L) + "\n"
    open(RESULT, "w", encoding="utf-8").write(txt)
    print(txt)
    log(f"⚖️ T-BOOK: {ev['verdict']}")
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
    if mode == "gate":
        return mode_gate(key)
    if mode == "shard":
        return mode_shard(key, int(argv[1]), d_in)
    log("الأوضاع: gate · shard <k> --dir D · assemble --dir D")
    return 1


if __name__ == "__main__":
    sys.exit(main())
