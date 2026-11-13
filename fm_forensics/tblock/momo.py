"""🧪 اختبارُ قبول صيغة مومو — الملحق 2 §① و§⓪-أ (قبل أيّ رقم).

صفقاتُ Polygon لـNXXT · SMX · MCGA يومَ 2026-11-10 في الجلسة النظاميّة 09:30:00-15:59:59 نيويورك بالأسعار الخامّة · والاقتباسُ السائد = آخرُ NBBO
بطابعٍ عند الصفقة أو قبلها (أقدمُ من 60 ث أو طرفٌ صفريّ ⟵ «بلا اقتباس» يُعَدّ) · أربعُ قواعد (R-Q · R-QM · R-LR · R-T) × بديلَي الشروط (الكلّ ·
بعد إسقاط شروط الملحق 1 ①) · الفرقُ % لكلّ خليّة · والدرجةُ متوسّطُ |الفرق %| على الخلايا بأساسٍ 10,000 سهمٍ فأكثر · والبوّابةُ §⓪-أ: درجةُ R-T
بالبديل الأقرب فوق 30% ⟵ «🛑 توقّف قبل ②». قراءةٌ وقياسٌ فقط: لا تلغرام · لا كتابةَ حالة · لا إنتاج.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ADDENDUM_2 = os.path.join(HERE, "T_BLOCK_addendum_2.md")
ADDENDUM_2_SHA = "3d948ddc7b79c7ee6b30457913c7d90f8b3017ab7b1c561ef5a9a2397d84f163"
CONTRACT_RC, KEY_RC, DATA_RC = 9, 3, 7
DAY = "2026-11-10"
MOMO = {"NXXT": (548_010, 296_840, 766_420), "SMX": (1_290_000, 1_100_000, 3_690_000), "MCGA": (129_410, 910, 4_580)}
COMP = ("buy", "sell", "neutral")
RULES = ("R-Q", "R-QM", "R-LR", "R-T")
VARIANTS = ("all", "cond")
STALE_NS = 60 * 1_000_000_000
BASE_MIN = 10_000                           # §① خليّةٌ بأساسٍ دون 10,000 سهم تُطبع ولا تدخل الدرجة
ACCEPT_SCORE, ACCEPT_CELL = 10.0, 25.0     # §① «مقبولة» (engineering)
GATE_RT = 30.0                             # §⓪-أ بوّابةُ التوقّف قبل ②
ADDENDUM_3 = os.path.join(HERE, "T_BLOCK_addendum_3.md")
ADDENDUM_3_SHA = "2d5687fcccefbf5a7eba98660b7e916bacce7ad19325f7b1c8cf12704f4706e6"
MOMO_TOTAL = {s: sum(v) for s, v in MOMO.items()}  # الملحق 3 §①: 1,611,270 · 6,080,000 · 134,900
SNAP_ET = {"NXXT": "12:00", "SMX": "11:07", "MCGA": "14:40"}   # الملحق 3 §⓪-3 (الرياض − 8 ساعات · للطباعة وحدَها)
TIE_ORDER = ("R-T", "R-Q", "R-QM", "R-LR")
ADDENDUM_4 = os.path.join(HERE, "T_BLOCK_addendum_4.md")
ADDENDUM_4_SHA = "4885e738c4e84acd753e73da2511615a18d9863d3e13eed7f90839478a96d121"
SET_FILE = os.path.join(HERE, "data", "momo_set_20261113.json")   # الملحق 4 ⓪-3: يُدمج قبل أوّل تشغيل
DAY4 = "2026-11-13"
MIN_CELLS4 = 4                                                     # الملحق 4 §③: «لا قياس» دون 4 خلايا داخلة


def log(*a):
    print(*a, flush=True)


def addendum3_ok():
    if not os.path.exists(ADDENDUM_3):
        return False
    with open(ADDENDUM_3, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest() == ADDENDUM_3_SHA


def addendum4_ok():
    if not os.path.exists(ADDENDUM_4):
        return False
    with open(ADDENDUM_4, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest() == ADDENDUM_4_SHA


def classify_qt(trades, quotes, stale_ns=STALE_NS):
    """الملحق 4 §①: R-Q حيث يوجد اقتباسٌ سائدٌ صالح · وإلّا التيكُ (يرحّل الصفر ويمشي على كلّ الصفقات) ⟵ ([شراء، بيع، محايد]، حجمٌ صُنِّف بالتيك)."""
    out = [0, 0, 0]
    by_tick = 0
    j, q = 0, None
    prev, last_diff, tick_dir = None, None, 0
    for ts, px, sz in trades:
        while j < len(quotes) and quotes[j][0] <= ts:
            q = quotes[j]
            j += 1
        if prev is not None and px != prev:
            last_diff, tick_dir = prev, (1 if px > prev else -1)
        prev = px
        ok = q is not None and ts - q[0] <= stale_ns and q[1] > 0 and q[2] > 0 and q[2] >= q[1]
        if ok:
            out[0 if px >= q[2] else 1 if px <= q[1] else 2] += sz
        else:
            by_tick += sz
            t = tick_dir if last_diff is not None else 0
            out[0 if t > 0 else 1 if t < 0 else 2] += sz
    return out, by_tick


def load_set(path=SET_FILE):
    """الملحق 4 ⓪-3: {رمز: (شراء، بيع، محايد)} من الملفّ المدموج · رمزٌ بلا ثلاثة أعدادٍ صحيحةٍ غيرِ سالبة يُسقط ويُعَدّ ⟵ (المادّة، المُسقَط) أو (None، سبب)."""
    if not os.path.exists(path):
        return None, "الملفّ غائب"
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, ValueError) as e:
        return None, f"تعذّر قراءته: {type(e).__name__}"
    good, dropped = {}, []
    for sym, v in (raw.get("momo") or {}).items():
        try:
            t = tuple(int(x) for x in v)
            if len(t) == 3 and all(x >= 0 for x in t) and isinstance(sym, str) and sym.isupper():
                good[sym] = t
                continue
        except (TypeError, ValueError):
            pass
        dropped.append(sym)
    return good, dropped


def gate4(cells):
    """الملحق 4 §③: الدرجةُ على الخلايا الداخلة ⟵ («لا قياس» دون 4 · «✅ تُبنى ②» عند 30% فأقلّ · وإلّا «🛑 توقّف»، الدرجة، عددُ الخلايا)."""
    xs = [abs(v[2]) for v in cells.values() if v[3] and v[2] is not None]
    if len(xs) < MIN_CELLS4:
        return "⚪ لا قياس", None, len(xs)
    sc = sum(xs) / len(xs)
    return ("✅ تُبنى ② بـR-QT" if sc <= GATE_RT else "🛑 توقّف"), sc, len(xs)


def contract_ok():
    if not os.path.exists(ADDENDUM_2):
        return False
    with open(ADDENDUM_2, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest() == ADDENDUM_2_SHA


# ── نقيّة ────────────────────────────────────────────────────────────────────────────────────────
def classify(trades, quotes, stale_ns=STALE_NS):
    """trades: [(ts، سعر، حجم)] مرتّبةٌ زمنيًّا · quotes: [(ts، bid، ask)] مرتّبة ⟵ {قاعدة: [شراء، بيع، محايد]} و«بلا اقتباس».
    R-Q: ≥ العرض شراء · ≤ الطلب بيع · بينهما محايد · R-QM: فوق المنتصف شراء · تحته بيع · عنده محايد · R-LR: R-QM ثمّ التيك عند المنتصف ·
    R-T: أعلى من آخر سعرٍ مختلف شراء · أدنى بيع · ولا سعرَ مختلفٌ قبلها محايد · وبلا اقتباس في الثلاث الأولى ⟵ محايد."""
    out = {r: [0, 0, 0] for r in RULES}
    noq = 0
    j, q = 0, None
    last_diff = None     # آخرُ سعرٍ مختلف قبل الصفقة (للتيك)
    prev = None
    tick_dir = 0
    for ts, px, sz in trades:
        while j < len(quotes) and quotes[j][0] <= ts:
            q = quotes[j]
            j += 1
        # التيك (بترحيل الصفر)
        if prev is not None and px != prev:
            last_diff, tick_dir = prev, (1 if px > prev else -1)
        prev = px
        t = tick_dir if last_diff is not None else 0
        out["R-T"][0 if t > 0 else 1 if t < 0 else 2] += sz
        ok = q is not None and ts - q[0] <= stale_ns and q[1] > 0 and q[2] > 0 and q[2] >= q[1]
        if not ok:
            noq += sz
            for r in ("R-Q", "R-QM", "R-LR"):
                out[r][2] += sz
            continue
        bid, ask = q[1], q[2]
        out["R-Q"][0 if px >= ask else 1 if px <= bid else 2] += sz
        mid = (bid + ask) / 2.0
        m = 1 if px > mid else -1 if px < mid else 0
        out["R-QM"][0 if m > 0 else 1 if m < 0 else 2] += sz
        lr = m if m != 0 else t
        out["R-LR"][0 if lr > 0 else 1 if lr < 0 else 2] += sz
    return out, noq


def cell_diffs(ours, momo):
    """{(سهم، مكوّن): (نحن، مومو، فرق %، داخلٌ في الدرجة)}."""
    res = {}
    for s, mv in momo.items():
        for k, c in enumerate(COMP):
            o, m = ours.get(s, [0, 0, 0])[k], mv[k]
            res[(s, c)] = (o, m, (o - m) / m * 100.0 if m else None, m >= BASE_MIN)
    return res


def score(cells):
    xs = [abs(v[2]) for v in cells.values() if v[3] and v[2] is not None]
    return (sum(xs) / len(xs)) if xs else None, max(xs) if xs else None


def cut_by_volume(trades, target):
    """الملحق 3 §①: أوّلُ صفقةٍ يبلغ بها التراكميُّ الهدفَ تُحسب كاملةً وما بعدها خارج ⟵ (الصفقاتُ، بلغ؟، الحجم)."""
    cum = 0.0
    for k, (_ts, _px, sz) in enumerate(trades):
        cum += sz
        if cum >= target:
            return trades[:k + 1], True, cum
    return list(trades), False, cum


def gate_any(scores):
    """الملحق 3 §②: {(قاعدة، بديل): درجة} ⟵ (حكم، (قاعدة، بديل، درجة)|None) · أدنى درجة 30% فأقلّ تُبنى بها ② · والتعادلُ بـTIE_ORDER."""
    xs = [(sc, TIE_ORDER.index(r), r, v) for (r, v), sc in scores.items() if sc is not None]
    if not xs:
        return "🛑 توقّف (لا درجة)", None
    sc, _o, r, v = min(xs)
    return ("✅ تُبنى ② بها" if sc <= GATE_RT else "🛑 توقّف"), (r, v, sc)


def gate(rt_scores):
    """§⓪-أ: درجةُ R-T بالبديل الأقرب (الأدنى) ⟵ («مضى»|«توقّف»، الدرجة) · تعذّرٌ ⟵ توقّف."""
    xs = [x for x in rt_scores if x is not None]
    if not xs:
        return "🛑 توقّف (لا درجة)", None
    s = min(xs)
    return ("✅ يمضي ②" if s <= GATE_RT else "🛑 توقّف قبل ②"), s


# ── الجلب ────────────────────────────────────────────────────────────────────────────────────────
def _tb():
    sys.path.insert(0, HERE)
    import tblock as TB
    return TB


def _ns(day, h, m, s, NY):
    return int(dt.datetime.fromisoformat(day).replace(hour=h, minute=m, second=s, tzinfo=NY).timestamp() * 1e9)


def fetch_paged(TB, url, params, key, maxpages=400):
    out = []
    for _ in range(maxpages):
        j = TB.poly_get(url, key, params)
        if j is None:
            return None
        out.extend(j.get("results") or [])
        nxt = j.get("next_url")
        if not nxt:
            return out
        url, params = nxt, None
    return None                                                     # سقفٌ ⟵ تعذّر لا نقص


def fetch_day(TB, sym, day, key, excl, NY):
    a, b = _ns(day, 9, 30, 0, NY), _ns(day, 16, 0, 0, NY)
    tr = fetch_paged(TB, f"https://api.polygon.io/v3/trades/{sym}",
                     {"timestamp.gte": a, "timestamp.lt": b, "limit": 50000, "order": "asc", "sort": "timestamp"}, key)
    qs = fetch_paged(TB, f"https://api.polygon.io/v3/quotes/{sym}",
                     {"timestamp.gte": a - STALE_NS, "timestamp.lt": b, "limit": 50000, "order": "asc", "sort": "timestamp"}, key)
    if tr is None or qs is None:
        return None
    tr.sort(key=lambda x: (int(x.get("sip_timestamp") or 0), int(x.get("sequence_number") or 0)))
    qs.sort(key=lambda x: (int(x.get("sip_timestamp") or 0), int(x.get("sequence_number") or 0)))
    rows = []
    for x in tr:
        try:
            rows.append((int(x["sip_timestamp"]), float(x["price"]), float(x["size"]), [int(c) for c in x.get("conditions") or []]))
        except (KeyError, TypeError, ValueError):
            continue
    quotes = [(int(x.get("sip_timestamp") or 0), float(x.get("bid_price") or 0), float(x.get("ask_price") or 0)) for x in qs]
    return {"all": [(t, p, s) for t, p, s, _c in rows],
            "cond": [(t, p, s) for t, p, s, c in rows if not any(k in excl for k in c)],
            "quotes": quotes, "n_trades": len(rows), "n_quotes": len(quotes)}


def main_set():
    """الملحق 4: R-QT على لقطات 11-13 الجديدة وحدَها · الجلسةُ النظاميّة الكاملة · البديلُ الحاكم «الكلّ»."""
    if not contract_ok() or not addendum4_ok():
        log("⛔ بصمةُ الملحق 2 أو 4 تغيّرت — لا تشغيل")
        return CONTRACT_RC
    mset, dropped = load_set()
    if mset is None:
        log(f"⛔ مادّةُ الملحق 4 ({SET_FILE}): {dropped} — «لا قياس» (تُدمج قبل التشغيل)")
        return DATA_RC
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log("⛔ بلا مفتاح Polygon — لا قياس")
        return KEY_RC
    from zoneinfo import ZoneInfo
    NY = ZoneInfo("America/New_York")
    TB = _tb()
    excl = TB.excluded_conditions(TB.fetch_conditions(key))
    log(f"الملحق 4 · {DAY4} · الرموز {sorted(mset)} · المُسقَط {dropped}")
    ours = {v: {r: {} for r in RULES + ("R-QT",)} for v in VARIANTS}
    tickvol, tot = {v: {} for v in VARIANTS}, {}
    for sym in sorted(mset):
        d = fetch_day(TB, sym, DAY4, key, excl, NY)
        if d is None:
            log(f"⛔ {sym}: تعذّر جلبُ الصفقات أو الاقتباسات — «لا قياس»")
            return DATA_RC
        for v in VARIANTS:
            c, _nq = classify(d[v], d["quotes"])
            for r in RULES:
                ours[v][r][sym] = c[r]
            ours[v]["R-QT"][sym], tickvol[v][sym] = classify_qt(d[v], d["quotes"])
        tot[sym] = sum(sz for _t, _p, sz in d["all"])
        log(f"{sym}: صفقات {d['n_trades']} · اقتباسات {d['n_quotes']} · حجمُنا {tot[sym]:,.0f} مقابل مومو {sum(mset[sym]):,} "
            f"(×{tot[sym] / max(1, sum(mset[sym])):.2f}) · صُنِّف بالتيك {tickvol['all'][sym]:,.0f}")
    log("")
    log("=" * 70)
    log(f"🧪 الملحق 4 — R-QT على لقطات مومو {DAY4} · التشغيلة {os.environ.get('GITHUB_RUN_ID')}")
    res = {}
    for v in VARIANTS:
        for r in ("R-QT",) + RULES:
            cells = cell_diffs(ours[v][r], mset)
            g, sc, n = gate4(cells)
            res[(r, v)] = (g, sc, n, cells)
            cs = " · ".join(f"{s} {c} {o:,.0f}/{m:,.0f} ({'—' if dd is None else f'{dd:+.1f}%'}{'' if inc else ' خارج'})"
                            for (s, c), (o, m, dd, inc) in cells.items())
            log(f"   {r} × {v}{'' if (r, v) == ('R-QT', 'all') else ' (وصف)'}: الدرجة {'—' if sc is None else f'{sc:.1f}%'} · خلايا {n} · {cs}")
    g, sc, n, _c = res[("R-QT", "all")]
    log(f"🚦 بوّابةُ الملحق 4 §③ (R-QT × الكلّ): {g} · الدرجة {'—' if sc is None else f'{sc:.1f}%'} · خلايا {n}")
    print("MOMO4_JSON " + json.dumps({"gate": g, "score": sc, "cells_in": n, "dropped": dropped,
                                      "table": {f"{r}|{v}": [x[0], x[1], x[2], {f"{s}|{c}": list(t) for (s, c), t in x[3].items()}]
                                                for (r, v), x in res.items()},
                                      "tick_volume": tickvol, "total": tot}, ensure_ascii=False))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="check", choices=("check", "run", "cut", "set"))
    a = ap.parse_args(argv)
    if not contract_ok():
        log("⛔ بصمةُ الملحق 2 تغيّرت — لا تشغيل")
        return CONTRACT_RC
    if a.mode == "set":
        return main_set()
    if a.mode == "cut" and not addendum3_ok():
        log("⛔ بصمةُ الملحق 3 تغيّرت — لا تشغيل")
        return CONTRACT_RC
    if a.mode == "check":
        log("✅ الملحق 2 مطابق")
        return 0
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log("⛔ بلا مفتاح Polygon — لا قياس")
        return KEY_RC
    from zoneinfo import ZoneInfo
    NY = ZoneInfo("America/New_York")
    TB = _tb()
    excl = TB.excluded_conditions(TB.fetch_conditions(key))
    log(f"شروطُ الملحق 1 ① المُسقَطة: {len(excl)} · {sorted(excl.items())[:40]}")
    ours = {v: {r: {} for r in RULES} for v in VARIANTS}
    noq = {v: {} for v in VARIANTS}
    cuts = {}
    for sym in MOMO:
        d = fetch_day(TB, sym, DAY, key, excl, NY)
        if d is None:
            log(f"⛔ {sym}: تعذّر جلبُ الصفقات أو الاقتباسات — «لا قياس»")
            return DATA_RC
        log(f"{sym} {DAY}: صفقاتٌ {d['n_trades']} (بعد الإسقاط {len(d['cond'])}) · اقتباساتٌ {d['n_quotes']}")
        for v in VARIANTS:
            if a.mode == "cut":
                d[v], reached, vol = cut_by_volume(d[v], MOMO_TOTAL[sym])
                t_ny = dt.datetime.fromtimestamp(d[v][-1][0] / 1e9, NY) if d[v] else None
                cuts[(sym, v)] = (t_ny, reached, vol, len(d[v]))
            c, nq = classify(d[v], d["quotes"])
            noq[v][sym] = nq
            for r in RULES:
                ours[v][r][sym] = c[r]
    table = {}
    for v in VARIANTS:
        for r in RULES:
            cells = cell_diffs(ours[v][r], MOMO)
            sc, mx = score(cells)
            table[(r, v)] = (sc, mx, cells)
    log("")
    log("=" * 70)
    log(f"🧪 اختبارُ قبول صيغة مومو — الملحق 2 §① · {DAY} · التشغيلة {os.environ.get('GITHUB_RUN_ID')}")
    for (r, v), (sc, mx, cells) in table.items():
        cs = " · ".join(f"{s} {c} {o:,.0f}/{m:,.0f} ({'—' if d is None else f'{d:+.1f}%'}{'' if inc else ' خارج'})"
                        for (s, c), (o, m, d, inc) in cells.items())
        log(f"   {r} × {v}: الدرجة {'—' if sc is None else f'{sc:.1f}%'} · أقصى خليّة {'—' if mx is None else f'{mx:.1f}%'} · {cs}")
    for v in VARIANTS:
        log(f"   بلا اقتباس ({v}): " + " · ".join(f"{s} {n:,.0f}" for s, n in noq[v].items()))
    if a.mode == "cut":
        from zoneinfo import ZoneInfo as _Z
        RY = _Z("Asia/Riyadh")
        for (sym, v), (t_ny, reached, vol, n) in cuts.items():
            sh, sm = map(int, SNAP_ET[sym].split(":"))
            dm = None if t_ny is None else (t_ny.hour * 60 + t_ny.minute) - (sh * 60 + sm)
            log(f"   ✂️ {sym} × {v}: القطع {'—' if t_ny is None else t_ny.strftime('%H:%M:%S')} ET "
                f"({'—' if t_ny is None else t_ny.astimezone(RY).strftime('%H:%M')} الرياض) مقابل اللقطة {SNAP_ET[sym]} ET · "
                f"الفرق {'—' if dm is None else f'{dm:+d}'} د · الحجم {vol:,.0f} من {MOMO_TOTAL[sym]:,} · صفقات {n:,}"
                + ("" if reached else " · ⚠️ لم يبلغ"))
        g3, w3 = gate_any({(r, v): table[(r, v)][0] for (r, v) in table})
        log(f"🚦 بوّابةُ الملحق 3 §②: {g3} · {'—' if w3 is None else f'{w3[0]} × {w3[1]} بدرجة {w3[2]:.1f}%'}")
    best = min(((sc, r, v) for (r, v), (sc, _m, _c) in table.items() if sc is not None), default=(None, None, None))
    acc = best[0] is not None and best[0] <= ACCEPT_SCORE and table[(best[1], best[2])][1] <= ACCEPT_CELL
    g, gs = gate([table[("R-T", v)][0] for v in VARIANTS])
    log(f"⚖️ الأقرب: {best[1]} × {best[2]} بدرجة {'—' if best[0] is None else f'{best[0]:.1f}%'} · {'«مقبولة»' if acc else 'غيرُ «مقبولة»'} (10%/25%)")
    log(f"🚦 بوّابةُ §⓪-أ: درجةُ R-T بالبديل الأقرب {'—' if gs is None else f'{gs:.1f}%'} ⟵ {g}")
    if a.mode == "cut":
        print("MOMO_CUT_JSON " + json.dumps({"gate": g3, "winner": w3, "cuts": {f"{s}|{v}": [None if t is None else t.isoformat(), rc, vol, n]
                                                                            for (s, v), (t, rc, vol, n) in cuts.items()}},
                                            ensure_ascii=False))
    print("MOMO_JSON " + json.dumps({"table": {f"{r}|{v}": [sc, mx, {f"{s}|{c}": list(x) for (s, c), x in cells.items()}]
                                               for (r, v), (sc, mx, cells) in table.items()},
                                     "noq": noq, "best": best, "accepted": acc, "gate": g, "gate_score": gs}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
