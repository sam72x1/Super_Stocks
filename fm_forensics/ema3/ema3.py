#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📈✖️③ `T-EMA3` — تقاطع إيما 9 و15 و16 على 4 ساعات (العقد `T_EMA3_prereg.md` · أمرُ المالك 2026-11-21) — قراءةٌ وتحليلٌ فقط.

  status                    — عدٌّ بلا نتيجة: لقطاتُ «تحت المتابعة» وجلساتُ التأكيد وأعضاؤها (من git وحدَه).
  fetch <part> [--dir D]    — يجلب شموع TradingView (يوميّ و4 ساعات ممتدّة) لمجتمع الجزء ⟵ `ema3_data/<part>/`.
  run <part> --dir D        — يحسب القياسات الثلاثة ⟵ `out/<PART>.json` و`.md` · **مرّةً واحدة** لكلّ جزء · والتأكيدُ بعد الاكتشاف.
  verdict                   — يقرأ الجزأين ويطبع الحكم المكتوب سلفًا (العقد §④).
🔒 لا تلغرام · لا Polygon · لا CONFIG يُسنَد · لا أداةَ ولا عتبةَ تتغيّر.
"""
import bisect
import gzip
import hashlib
import json
import os
import pickle
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CASE31 = os.path.join(ROOT, "fm_forensics", "case31")
for _p in (ROOT, CASE31, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

CONTRACT = os.path.join(HERE, "T_EMA3_prereg.md")
CONTRACT_SHA = "4d15da41bdbf50d073d03775a54e8f1cf3fd7e8339006a6829cef1bccc31310a"                                                  # يُملأ قبل الدمج · فارغٌ أو مخالف ⟵ خروج 11
OUT = os.path.join(HERE, "out")
DATA = os.path.join(ROOT, "ema3_data")
PARTS = {"discover": "DISCOVER", "confirm": "CONFIRM"}

FAST, SLOW = 9, (15, 16)                                           # نصُّ المالك: EMA9 فوق EMA15 وفوق EMA16 معًا
WARMUP = 64                                                        # لا إشارةَ قبل الشمعة 64 (4 × 16) — engineering
COST = 0.018                                                       # كما T-CASE31 وT-ENV-LIMIT
HORIZONS, GOV_H, WIN = (5, 10, 20), 20, 20
TARGETS, STOP, X100 = (0.30, 0.50), -0.10, 1.00
K_MATCH, MOM_S_BARS, MOM_L_SESS = 5, 9, 20                         # ضابطُ الزخم المطابق — engineering
BOOT_N, SEED = 2000, 20261121
MIN_SIG, MIN_DAYS = 100, 20                                        # أرضيّةُ الخليّة الحاكمة لكلّ جزء
D_FROM, D_TO, D_BLIND = "2023-01-01", "2025-12-31", "2026-02-28"   # الاكتشاف: جلساتُ التقاطع · وقصُّ الشموع
C_FROM, SNAP_FROM = "2026-09-30", "2026-09-29"                     # التأكيد: أوّلُ جلسة تقاطع · وأوّلُ لقطة
MEMBER_WIN = 20
BASKET_RUN = "43955351411"
TV_N = {"discover": (1500, 5000), "confirm": (500, 1100)}          # (يوميّ، 4 ساعات)
EARLY_FRAC = 0.25
REC_KEYS = ("r5", "r10", "r20", "tp30", "tp50", "x100")
RC_OK, RC_DATA, RC_ONCE, RC_CLOSED, RC_ORDER, RC_CONTRACT = 0, 5, 7, 8, 9, 11
CLOSED = True                                                      # 🔒 2026-11-21: الحكمُ «لا قياس/لا تعبر» ⟵ الجلبُ والقياسُ يخرجان 8 بلا إقرار `EMA3_REOPEN`


def closed():
    """المحورُ مُغلَقٌ مُنفَّذًا ما لم يُقِرّ المالك بفتحه (`EMA3_REOPEN` = "1" حرفيًّا)."""
    return bool(CLOSED) and os.environ.get("EMA3_REOPEN", "") != "1"


def log(m=""):
    print(m, flush=True)


def sha_of(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def contract_ok():
    try:
        return bool(CONTRACT_SHA) and sha_of(CONTRACT) == CONTRACT_SHA
    except OSError:
        return False


def guard(part, out_dir=None):
    """(نقيّة عدا قراءة الملفّات) ⟵ رمزُ الخروج قبل أيّ عمل: 11 عقدٌ متغيّر · 7 الجزءُ صدر · 9 التأكيدُ قبل الاكتشاف · 0 يمضي."""
    out_dir = OUT if out_dir is None else out_dir
    if part not in PARTS:
        return RC_DATA
    if not contract_ok():
        return RC_CONTRACT
    if os.path.exists(os.path.join(out_dir, PARTS[part] + ".json")):
        return RC_ONCE
    if part == "confirm" and not os.path.exists(os.path.join(out_dir, PARTS["discover"] + ".json")):
        return RC_ORDER
    return RC_OK


# ══ ① التعريف (نقيّة) ════════════════════════════════════════════════════════════════════════════════════════════════════════════
def ema(vals, n):
    """EMA بتعريف TradingView: البذرةُ متوسّطٌ بسيط لأوّل n قيمة · None قبلها."""
    out, k = [None] * len(vals), 2.0 / (n + 1.0)
    if len(vals) < n:
        return out
    e = sum(vals[:n]) / n
    out[n - 1] = e
    for i in range(n, len(vals)):
        e = vals[i] * k + e * (1.0 - k)
        out[i] = e
    return out


def states(closes):
    """⟵ لكلّ شمعة: ‏+1 «فوق» (EMA9 أكبر من EMA15 ومن EMA16) · ‏−1 «تحت» (أصغر من الاثنين) · 0 «وسط» · None قبل اكتمال المتوسّطات."""
    f = ema(closes, FAST)
    sl = [ema(closes, n) for n in SLOW]
    out = []
    for i in range(len(closes)):
        if f[i] is None or any(s[i] is None for s in sl):
            out.append(None)
        elif all(f[i] > s[i] for s in sl):
            out.append(1)
        elif all(f[i] < s[i] for s in sl):
            out.append(-1)
        else:
            out.append(0)
    return out


def fire(st, warmup=WARMUP):
    """⟵ (الإشارات المعدودة، كلُّ التقاطعات، القائمُ لكلّ شمعة): الإشارةُ أوّلُ «فوق» بعد أن كانت آخرُ حالةٍ غير «وسط» «تحت».
    القائم: رقمُ شمعة التقاطع ما لم تمرّ «تحت» بعده · ‏−1 «فوق» بلا تقاطعٍ معلوم · None غيرُ قائم."""
    sigs, crosses, stand_at, armed, stand = [], [], [], False, None
    for i, s in enumerate(st):
        if s == -1:
            armed, stand = True, None
        elif s == 1:
            if armed:
                armed, stand = False, i
                crosses.append(i)
                if i >= warmup:
                    sigs.append(i)
            elif stand is None:
                stand = -1
        stand_at.append(stand if s is not None else None)
    return sigs, crosses, stand_at


# ══ ② العضويّة (نقيّة) ═══════════════════════════════════════════════════════════════════════════════════════════════════════════
def members_discover(entries, sessions):
    """إدخالاتُ CURRENT (رمز، يوم) ⟵ {جلسة: {رموز}}: من الجلسة **التالية** ليوم الإدخال إلى `MEMBER_WIN` جلسةً بعده · داخل [D_FROM، D_TO]."""
    out = {}
    for sym, d in entries:
        i = bisect.bisect_right(sessions, d)                       # أوّلُ جلسةٍ بعد يوم الإدخال
        for day in sessions[i:i + MEMBER_WIN]:
            if D_FROM <= day <= D_TO:
                out.setdefault(day, set()).add(sym.upper())
    return out


def members_confirm(sessions, measured_by_day):
    """{يومُ اللقطة: رموزُها المقيسة} ⟵ {جلسة: {رموز}}: عضويّةُ الجلسة = لقطةُ **الجلسة السابقة** · من `C_FROM`."""
    out = {}
    for i in range(1, len(sessions)):
        day, prev = sessions[i], sessions[i - 1]
        if day >= C_FROM and prev >= SNAP_FROM and measured_by_day.get(prev):
            out[day] = set(measured_by_day[prev])
    return out


def cut_blind(bars, day_of, last_day):
    """يقصّ كلَّ شمعةٍ يومُها بعد `last_day` (الاكتشافُ أعمى عن نافذة التأكيد)."""
    return {s: [b for b in v if day_of(b[0]) <= last_day] for s, v in bars.items()}


# ══ ③ النتيجةُ لكلّ دخول (نقيّة) ══════════════════════════════════════════════════════════════════════════════════════════════════
def outcome(h4, days4, i, drows, ddays):
    """دخولٌ على افتتاح الشمعة i ⟵ {px, D0, r5, r10, r20, tp30, tp50, x100, full} أو None.
    العائد = إغلاقُ يوميّ الجلسة k بعد D0 ÷ الدخول − 1 − الكلفة · واللمسُ على 4 ساعات حتى نهاية الجلسة العشرين · واجتماعُ الهدف والوقف في شمعةٍ وقف."""
    if i < 0 or i >= len(h4):
        return None
    px = h4[i][1]
    if not px or px <= 0:
        return None
    d0 = days4[i]
    j = bisect.bisect_right(ddays, d0)
    res = {"px": px, "D0": d0}
    for k in HORIZONS:
        r = drows[j + k - 1] if j + k - 1 < len(drows) else None
        res[f"r{k}"] = (r[4] / px - 1.0 - COST) if r and r[4] > 0 else None
    full = j + WIN - 1 < len(drows)
    res["full"] = full
    if not full:
        res.update(tp30=None, tp50=None, x100=None)
        return res
    end_day, stop, first = ddays[j + WIN - 1], None, {}
    for m in range(i, len(h4)):
        if days4[m] > end_day:
            break
        hi, lo = h4[m][2], h4[m][3]
        if stop is None and lo <= px * (1.0 + STOP):
            stop = m
        for t in TARGETS + (X100,):
            if t not in first and hi >= px * (1.0 + t):
                first[t] = m
    res["tp30"] = bool(TARGETS[0] in first and (stop is None or first[TARGETS[0]] < stop))
    res["tp50"] = bool(TARGETS[1] in first and (stop is None or first[TARGETS[1]] < stop))
    res["x100"] = bool(X100 in first)
    return res


def momentum(h4, days4, i, drows, ddays):
    """⟵ (تغيّرُ 9 شموع حتى الشمعة السابقة للدخول، إغلاقُها ÷ إغلاق اليوميّ قبل 20 جلسة − 1) أو None."""
    a = i - 1 - MOM_S_BARS
    if a < 0:
        return None
    c1, c0 = h4[i - 1][4], h4[a][4]
    j = bisect.bisect_left(ddays, days4[i]) - MOM_L_SESS
    if j < 0 or c0 <= 0 or c1 <= 0 or drows[j][4] <= 0:
        return None
    return c1 / c0 - 1.0, c1 / drows[j][4] - 1.0


def pct_ranks(vals):
    """{مفتاح: قيمة} ⟵ {مفتاح: رتبةٌ مئويّة في [0، 1]} (المتساوون بمتوسّط رتبهم)."""
    ks = sorted(vals, key=lambda k: (vals[k], k))
    n = len(ks)
    if n <= 1:
        return {k: 0.5 for k in ks}
    out, i = {}, 0
    while i < n:
        j = i
        while j + 1 < n and vals[ks[j + 1]] == vals[ks[i]]:
            j += 1
        r = ((i + j) / 2.0) / (n - 1)
        for q in range(i, j + 1):
            out[ks[q]] = r
        i = j + 1
    return out


def match(sig, mom, pool, k=K_MATCH):
    """أقربُ k من `pool` إلى `sig` بمجموع فرقَي الرتبة المئويّة في بُعدَي الزخم · التساوي بالرمز. `mom` = {رمز: (قصير، طويل)}."""
    if sig not in mom:
        return []
    pool = {s for s in pool if s in mom and s != sig}
    keys = sorted(pool | {sig})
    rs = pct_ranks({s: mom[s][0] for s in keys})
    rl = pct_ranks({s: mom[s][1] for s in keys})
    cand = sorted((abs(rs[s] - rs[sig]) + abs(rl[s] - rl[sig]), s) for s in pool)
    return [s for _d, s in cand[:k]]


# ══ الإحصاء (نقيّة) ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
def boot_ci(pairs, n=BOOT_N, seed=SEED):
    """[(عنقود، قيمة)] ⟵ {n, days, mean, lo, hi}: متوسّطٌ وفاصلُ 95% بإعادة عيّنةٍ عنقوديّة (السحبُ للأيّام لا للصفوف)."""
    import numpy as np
    pairs = [(c, float(v)) for c, v in pairs if v is not None]
    if not pairs:
        return {"n": 0, "days": 0, "mean": None, "lo": None, "hi": None}
    agg = {}
    for c, v in pairs:
        a = agg.setdefault(c, [0.0, 0])
        a[0] += v
        a[1] += 1
    ks = sorted(agg)
    sums, cnts = np.array([agg[k][0] for k in ks]), np.array([agg[k][1] for k in ks], dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(ks), size=(n, len(ks)))
    means = sums[idx].sum(axis=1) / cnts[idx].sum(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return {"n": len(pairs), "days": len(ks), "mean": float(sums.sum() / cnts.sum()), "lo": float(lo), "hi": float(hi)}


def _dist(vals):
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return {"n": 0}
    q = lambda p: vals[min(len(vals) - 1, int(p * (len(vals) - 1) + 0.5))]         # noqa: E731
    return {"n": len(vals), "mean": sum(vals) / len(vals), "median": statistics.median(vals), "q1": q(0.25), "q3": q(0.75),
            "max": vals[-1], "min": vals[0]}


# ══ ③-أ موقعُ التقاطع من الحركة (نقيّة) ══════════════════════════════════════════════════════════════════════════════════════════
def position(ev, h4, days4, crosses, stand_at, ddays):
    """حدثُ ‏+100% (`D` يومُ القرار · `s` بدايةُ الحركة · `p` جلسةُ القمّة · `close_D`) ⟵ {cls, lead?, frac?, after?}."""
    i_d = bisect.bisect_right(days4, ev["D"]) - 1
    a, b = bisect.bisect_left(days4, ev["s"]), bisect.bisect_right(days4, ev["p"]) - 1
    if i_d < max(SLOW) - 1 or a > b:                               # لا متوسّطات عند يوم القرار · أو لا شموعَ أثناء الحركة
        return {"cls": "غير مقيس"}
    ip = max(range(a, b + 1), key=lambda m: (h4[m][2], -m))
    top, base = h4[ip][2], ev["close_D"]
    st = stand_at[i_d]
    if st is not None:
        lead = None
        if st >= 0:
            lead = bisect.bisect_right(ddays, ev["D"]) - bisect.bisect_right(ddays, days4[st])
        return {"cls": "قبل", "lead": lead}
    k = bisect.bisect_right(crosses, i_d)
    nxt = crosses[k] if k < len(crosses) else None
    if nxt is not None and nxt <= ip:
        frac = ((h4[nxt][4] - base) / (top - base)) if top > base else None
        return {"cls": "أثناء", "frac": frac}
    jp = bisect.bisect_right(ddays, ev["p"])
    end_day = ddays[min(len(ddays) - 1, jp + WIN - 1)] if jp < len(ddays) else ev["p"]
    if nxt is not None and days4[nxt] <= end_day:
        return {"cls": "بعد", "after": bisect.bisect_right(ddays, days4[nxt]) - bisect.bisect_right(ddays, ev["p"])}
    return {"cls": "لا تقاطع"}


# ══ الحساب ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def table_b(recs):
    """صفوفُ الإشارات ⟵ (جدولُ ب، الخليّةُ الحاكمة): لكلّ مقياسٍ توزيعُ الإشارة وفرقُها عن كلّ ضابط بفاصله العنقوديّ (نقيّة · حتميّة)."""
    B = {}
    for k in REC_KEYS:
        sv = [(r["D0"], r["sig"][k]) for r in recs if r["sig"][k] is not None]
        cell = {"sig": _dist([v for _c, v in sv]) if k.startswith("r") else {"n": len(sv), "rate": (sum(v for _c, v in sv) / len(sv)) if sv else None}}
        if k.startswith("r") and sv:
            cell["sig"]["win"] = sum(1 for _c, v in sv if v > 0) / len(sv)
        for name in ("same", "match"):
            pr = [(r["D0"], float(r["sig"][k]) - r[name][k]) for r in recs if r["sig"][k] is not None and r[name][k] is not None]
            ci = boot_ci(pr)
            cm = [r[name][k] for r in recs if r["sig"][k] is not None and r[name][k] is not None]
            ci["ctl_mean"] = (sum(cm) / len(cm)) if cm else None
            cell[name] = ci
        B[k] = cell
    g = B[f"r{GOV_H}"]
    enough = all(g[n]["n"] >= MIN_SIG and g[n]["days"] >= MIN_DAYS for n in ("same", "match"))
    gov = {"h": GOV_H, "same": [g["same"]["lo"], g["same"]["hi"]], "match": [g["match"]["lo"], g["match"]["hi"]],
           "n": min(g["same"]["n"], g["match"]["n"]), "days": min(g["same"]["days"], g["match"]["days"]), "enough": enough,
           "pass": bool(enough and g["same"]["lo"] > 0 and g["match"]["lo"] > 0)}
    return B, gov


def measure(bars_h4, bars_d, members, day_of, find_events=None, slot_of=None, keep=False):
    """المجتمع ⟵ القياساتُ الثلاثة (العقد §③). `bars_h4`/`bars_d` = {رمز: [(ts,o,h,l,c,v)]} · `members` = {جلسة: {رموز}}."""
    days = sorted(members)
    if not days:
        return None
    lo, hi = days[0], days[-1]
    P = {}
    for s, h4 in bars_h4.items():
        d = bars_d.get(s)
        if not h4 or not d:
            continue
        days4 = [day_of(b[0]) for b in h4]
        sigs, crosses, stand_at = fire(states([b[4] for b in h4]))
        P[s] = {"h4": h4, "days4": days4, "ix": {b[0]: k for k, b in enumerate(h4)}, "sigs": sigs, "crosses": crosses, "stand": stand_at,
                "drows": d, "ddays": [day_of(b[0]) for b in d], "xdays": {days4[c] for c in crosses}}
    cache = {}

    def oc(s, i):
        if (s, i) not in cache:
            p = P[s]
            cache[(s, i)] = outcome(p["h4"], p["days4"], i, p["drows"], p["ddays"])
        return cache[(s, i)]

    sig_rows, per_day = [], {d: 0 for d in days}
    for s in sorted(P):
        p = P[s]
        for c in p["sigs"]:
            dx = p["days4"][c]
            if dx not in members or s not in members[dx] or c + 1 >= len(p["h4"]):
                continue
            per_day[dx] += 1
            sig_rows.append((p["h4"][c + 1][0], dx, s, c + 1))
    by_t = {}
    for t, dx, s, i in sig_rows:
        by_t.setdefault((t, dx), []).append((s, i))
    keys = REC_KEYS
    recs, no_ctl, no_mom = [], 0, 0
    for (t, dx), group in sorted(by_t.items()):
        pool = {}
        for s in sorted(members[dx]):
            p = P.get(s)
            if p is None or dx in p["xdays"]:
                continue
            j = p["ix"].get(t)
            if j is None or j < WARMUP:
                continue
            pool[s] = j
        mom = {}
        for s, j in list(pool.items()) + group:
            m = momentum(P[s]["h4"], P[s]["days4"], j, P[s]["drows"], P[s]["ddays"])
            if m is not None:
                mom[s] = m
        ctl = {c: oc(c, j) for c, j in pool.items()}
        ctl = {c: v for c, v in ctl.items() if v is not None}
        ctl_mom = [c for c in ctl if c in mom]
        for s, i in group:
            o = oc(s, i)
            if o is None:
                continue
            near = match(s, mom, ctl_mom)
            if not ctl:
                no_ctl += 1
            if s not in mom or not near:
                no_mom += 1
            rec = {"sym": s, "Dx": dx, "D0": o["D0"], "t": t, "sig": {k: o[k] for k in keys}, "n_same": len(ctl), "n_match": len(near), "m": near}
            for name, group_ in (("same", list(ctl)), ("match", near)):
                agg = {}
                for k in keys:
                    v = [float(ctl[c][k]) for c in group_ if ctl[c][k] is not None]
                    agg[k] = (sum(v) / len(v)) if v else None
                rec[name] = agg
            recs.append(rec)
    out = {"pop": {"symbols": len({s for v in members.values() for s in v}), "with_bars": len(P), "days": len(days), "range": [lo, hi],
                   "member_rows": sum(len(v) for v in members.values()),
                   "member_rows_bars": sum(1 for v in members.values() for s in v if s in P)},
           "signals": {"n": len(recs), "no_same_control": no_ctl, "no_match_control": no_mom}}
    B, out["gov"] = table_b(recs)
    out["B"] = B
    if keep:
        out["recs"] = recs
    # ج) العدد
    counted = [per_day[d] for d in days]
    slots = {}
    if slot_of:
        for r in recs:
            k = slot_of(r["t"])
            slots[k] = slots.get(k, 0) + 1
    out["C"] = {"per_day": _dist(counted), "days_zero": sum(1 for v in counted if v == 0), "in_members": sum(counted),
                "x100": B["x100"]["sig"], "x100_same": B["x100"]["same"], "slots": dict(sorted(slots.items()))}
    # أ) موقعُ التقاطع
    A = {"events": 0, "counts": {}, "frac": [], "lead": [], "after": [], "early": 0, "rows": []}
    if find_events is not None:
        for s in sorted(P):
            p = P[s]
            rows = [(p["ddays"][k],) + tuple(b[1:6]) for k, b in enumerate(p["drows"])]
            for ev in find_events(rows, lo, hi):
                if ev["s"] not in members or s not in members[ev["s"]]:
                    continue
                r = position(ev, p["h4"], p["days4"], p["crosses"], p["stand"], p["ddays"])
                A["events"] += 1
                A["counts"][r["cls"]] = A["counts"].get(r["cls"], 0) + 1
                if r["cls"] == "أثناء" and r.get("frac") is not None:
                    A["frac"].append(r["frac"])
                if r["cls"] == "قبل" and r.get("lead") is not None:
                    A["lead"].append(r["lead"])
                if r["cls"] == "بعد":
                    A["after"].append(r["after"])
                if r["cls"] == "قبل" or (r["cls"] == "أثناء" and r.get("frac") is not None and r["frac"] < EARLY_FRAC):
                    A["early"] += 1
                A["rows"].append({"sym": s, "D": ev["D"], "s": ev["s"], "p": ev["p"], **r})
    measured = A["events"] - A["counts"].get("غير مقيس", 0)
    A.update(measured=measured, frac_dist=_dist(A.pop("frac")), lead_dist=_dist(A.pop("lead")), after_dist=_dist(A.pop("after")),
             early_share=(A["early"] / measured) if measured else None)
    fr = [r["frac"] for r in A["rows"] if r["cls"] == "أثناء" and r.get("frac") is not None]
    A["frac_ge50"] = (sum(1 for v in fr if v >= 0.5) / len(fr)) if fr else None
    out["A"] = A
    return out


# ══ الحكم (نقيّة) ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def verdict(disc, conf):
    """الحكمُ المكتوب سلفًا (العقد §④): «تعبر» فقط إن كان الحدُّ الأدنى للفواصل الأربعة أكبرَ من صفر والأرضيّةُ مستوفاة في الجزأين."""
    cells, enough = [], True
    for name, j in (("الاكتشاف", disc), ("التأكيد", conf)):
        g = (j or {}).get("gov") or {}
        enough = enough and bool(g.get("enough"))
        for ctl, lab in (("match", "الزخم المطابق"), ("same", "اليوم نفسه")):
            lo_hi = g.get(ctl) or [None, None]
            cells.append({"part": name, "ctl": lab, "lo": lo_hi[0], "hi": lo_hi[1], "ok": lo_hi[0] is not None and lo_hi[0] > 0})
    if not enough:
        return {"verdict": "لا قياس", "pass": False, "cells": cells}
    ok = all(c["ok"] for c in cells)
    return {"verdict": "تعبر" if ok else "لا تعبر", "pass": ok, "cells": cells}


def predictions(disc, conf):
    """تنبّؤاتُ العقد §⑤ ⟵ [(رمز، نصّ، صدق؟ أو None)]."""
    def a_share(j, cls):
        a = j["A"]
        return (a["counts"].get(cls, 0) / a["measured"]) if a.get("measured") else None

    def both(f):
        v = [f(disc), f(conf)]
        return None if any(x is None for x in v) else all(v)

    def lt(x, y):
        return None if x is None else x < y

    out = [("E1", "«قبل» أقلُّ من 35% من المنفجرين في الجزأين", both(lambda j: lt(a_share(j, "قبل"), 0.35))),
           ("E2", "وسيطُ النسبة المتحقّقة لفئة «أثناء» 30% فأكثر",
            both(lambda j: None if not j["A"]["frac_dist"].get("n") else j["A"]["frac_dist"]["median"] >= 0.30)),
           ("E3", "الحاكمةُ أمام الزخم المطابق تشمل الصفر في الاكتشاف",
            None if disc["gov"]["match"][0] is None else disc["gov"]["match"][0] <= 0 <= disc["gov"]["match"][1]),
           ("E4", "متوسّطُ عائد الإشارة عند 20 جلسة سالبٌ في الجزأين", both(lambda j: lt(j["B"]["r20"]["sig"].get("mean"), 0))),
           ("E5", "‏+30% قبل −10% للإشارة دون 25% في الجزأين", both(lambda j: lt(j["B"]["tp30"]["sig"].get("rate"), 0.25))),
           ("E6", "نسبةُ الانفجار بعد الإشارة لا تتجاوز ضعفَ ضابط اليوم نفسِه",
            both(lambda j: None if j["B"]["x100"]["sig"].get("rate") is None or not j["B"]["x100"]["same"].get("ctl_mean")
                 else j["B"]["x100"]["sig"]["rate"] <= 2 * j["B"]["x100"]["same"]["ctl_mean"])),
           ("E7", "في 2026: 20 إشارةً فأكثر في اليوم وسيطًا",
            None if not conf["C"]["per_day"].get("n") else conf["C"]["per_day"]["median"] >= 20),
           ("E8", "الحكم «لا تعبر»", not verdict(disc, conf)["pass"])]
    return out


# ══ العرض ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _p(v, d=1):
    return "—" if v is None else f"{v * 100:+.{d}f}%"


def _u(v, d=1):
    return "—" if v is None else f"{v * 100:.{d}f}%"


def render(part, j):
    """ملفُّ الجزء ⟵ نصُّ `out/<PART>.md` (حتميّ)."""
    nm = {"discover": "الاكتشاف 2023-2025", "confirm": "التأكيد 2026"}[part]
    pop, B, A, C, g = j["pop"], j["B"], j["A"], j["C"], j["gov"]
    L = [f"# 📈✖️③ `T-EMA3` — {nm}", "",
         f"المجتمع: {pop['symbols']:,} رمزًا ({pop['with_bars']:,} بشموع) · {pop['days']:,} جلسة ({pop['range'][0]} … {pop['range'][1]}) · "
         f"صفوفُ العضويّة {pop['member_rows']:,} (بشموع {pop['member_rows_bars']:,}) · الإشارات {j['signals']['n']:,} "
         f"(بلا ضابط يوم {j['signals']['no_same_control']:,} · بلا ضابط زخم {j['signals']['no_match_control']:,})."]
    f = j.get("fetch") or {}
    if f:
        L.append(f"الجلب (TradingView): الرموز {f.get('symbols', 0):,} · يوميّ {f.get('daily', 0):,} · 4 ساعات {f.get('h4', 0):,} · "
                 f"وسيطُ أوّل شمعة 4 ساعات {f.get('h4_first_median')}.")
    L += ["",
         "## أ) موقعُ التقاطع من الحركة", ""]
    if A["events"]:
        L += [f"المنفجرون ‏+100% داخل العضويّة: {A['events']:,} · المقيس {A['measured']:,}.", "", "| الفئة | العدد | الحصّة من المقيس |", "|---|---|---|"]
        for cls in ("قبل", "أثناء", "بعد", "لا تقاطع", "غير مقيس"):
            n = A["counts"].get(cls, 0)
            L.append(f"| {cls} | {n:,} | {_u(n / A['measured']) if A['measured'] and cls != 'غير مقيس' else '—'} |")
        fd, ld, ad = A["frac_dist"], A["lead_dist"], A["after_dist"]
        L += ["", f"- «أثناء»: نسبةُ الصعود المتحقّقة عند إغلاق شمعة التقاطع — الوسيط {_u(fd.get('median'))} · الربعان {_u(fd.get('q1'))} و{_u(fd.get('q3'))} "
              f"· ومَن تحقّق عنده نصفُ الصعود فأكثر {_u(A['frac_ge50'])} (n={fd.get('n', 0)}).",
              f"- «قبل»: كم جلسةً سبق التقاطعُ يومَ القرار — الوسيط {ld.get('median', '—')} · الربعان {ld.get('q1', '—')} و{ld.get('q3', '—')} (n={ld.get('n', 0)}).",
              f"- «بعد»: كم جلسةً بعد القمّة — الوسيط {ad.get('median', '—')} (n={ad.get('n', 0)}).",
              f"- **قبل أو أثناء وقد تحقّق أقلُّ من ربع الصعود: {_u(A['early_share'])}** ({A['early']:,} من {A['measured']:,})."]
    else:
        L.append("لا منفجرَ داخل العضويّة.")
    L += ["", "## ب) بعد الدخول على افتتاح الشمعة التالية", "",
          "| الأفق | الإشارات | متوسّط العائد بعد الكلفة | الوسيط | الرابحون | الفرق عن الزخم المطابق [95%] | الفرق عن اليوم نفسه [95%] |", "|---|---|---|---|---|---|---|"]
    for k in HORIZONS:
        c = B[f"r{k}"]
        L.append(f"| {k} جلسات | {c['sig'].get('n', 0):,} | {_p(c['sig'].get('mean'))} | {_p(c['sig'].get('median'))} | {_u(c['sig'].get('win'))} | "
                 f"{_p(c['match']['mean'])} [{_p(c['match']['lo'])}، {_p(c['match']['hi'])}] | {_p(c['same']['mean'])} [{_p(c['same']['lo'])}، {_p(c['same']['hi'])}] |")
    L += ["", "| خلال 20 جلسة | الإشارة | ضابط الزخم | الفرق [95%] | ضابط اليوم | الفرق [95%] |", "|---|---|---|---|---|---|"]
    for k, lab in (("tp30", "‏+30% قبل −10%"), ("tp50", "‏+50% قبل −10%"), ("x100", "بلغ ‏+100%")):
        c = B[k]
        L.append(f"| {lab} | {_u(c['sig'].get('rate'))} (n={c['sig'].get('n', 0):,}) | {_u(c['match']['ctl_mean'])} | {_p(c['match']['mean'])} [{_p(c['match']['lo'])}، "
                 f"{_p(c['match']['hi'])}] | {_u(c['same']['ctl_mean'])} | {_p(c['same']['mean'])} [{_p(c['same']['lo'])}، {_p(c['same']['hi'])}] |")
    pd = C["per_day"]
    L += ["", "## ج) العدد", "",
          f"- الإشاراتُ في اليوم داخل العضويّة: المتوسّط {pd.get('mean', 0):.1f} · الوسيط {pd.get('median', 0):g} · الأقصى {pd.get('max', 0):g} · "
          f"أيّامٌ بلا إشارة {C['days_zero']:,} من {pd.get('n', 0):,} · المجموع {C['in_members']:,}.",
          f"- منها في أسهمٍ بلغت ‏+100% خلال 20 جلسة: {_u(C['x100'].get('rate'))} (n={C['x100'].get('n', 0):,}) مقابل ضابط اليوم نفسِه {_u(C['x100_same']['ctl_mean'])}."]
    if C.get("slots"):
        L.append("- شمعةُ الدخول بتوقيت نيويورك: " + " · ".join(f"{k} = {v:,}" for k, v in C["slots"].items()) + ".")
    L += ["", "## الخليّةُ الحاكمة (العائد بعد الكلفة عند 20 جلسة)", "",
          f"- أمام الزخم المطابق: [{_p(g['match'][0])}، {_p(g['match'][1])}] · أمام اليوم نفسِه: [{_p(g['same'][0])}، {_p(g['same'][1])}] · "
          f"n={g['n']:,} · أيّام {g['days']:,} · الأرضيّة {'مستوفاة' if g['enough'] else 'غيرُ مستوفاة'} ⟵ "
          f"**{'الحدّان فوق الصفر' if g['pass'] else ('لا قياس' if not g['enough'] else 'فاصلٌ يلمس الصفر')}**.", ""]
    return "\n".join(L)


def render_verdict(disc, conf):
    v = verdict(disc, conf)
    L = ["# 📈✖️③ `T-EMA3` — الحكم (العقد §④)", "", "| الجزء | الضابط | فاصلُ فرق العائد عند 20 جلسة | فوق الصفر؟ |", "|---|---|---|---|"]
    for c in v["cells"]:
        L.append(f"| {c['part']} | {c['ctl']} | [{_p(c['lo'])}، {_p(c['hi'])}] | {'✅' if c['ok'] else '❌'} |")
    L += ["", f"**الحكم: {v['verdict']}** ⟵ " + ("يُقترح وسمُ عرض «تقاطع إيما» في «تحت المتابعة» ويُنتظر قرارُ المالك · لا شيءَ يُشحن."
                                               if v["pass"] else "يُقفل المحورُ بمفتاح `EMA3_REOPEN` · ولا محاولةَ ثانية."), "",
          "## التنبّؤات المسجَّلة (§⑤)", "", "| # | التنبّؤ | النتيجة |", "|---|---|---|"]
    for k, txt, ok in predictions(disc, conf):
        L.append(f"| `{k}` | {txt} | {'—' if ok is None else ('✅ صدق' if ok else '❌ كذب')} |")
    return "\n".join(L) + "\n"


# ══ الأوضاع ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _dump(part, name, obj):
    d = os.path.join(DATA, part)
    os.makedirs(d, exist_ok=True)
    with gzip.open(os.path.join(d, name), "wb") as fh:
        pickle.dump(obj, fh, protocol=4)


def _load(d_in, name):
    for base, _dirs, files in os.walk(d_in):
        if name in files:
            with gzip.open(os.path.join(base, name), "rb") as fh:
                return pickle.load(fh)
    return None


def confirm_plan():
    """من git وحدَه ⟵ (أيّامُ اللقطات: {يوم: [رموز]}، الرموز)."""
    import datetime as dt
    import case31_build as B
    snaps = B.snapshots("near_watch.json")
    out, day = {}, dt.date.fromisoformat(SNAP_FROM)
    today = dt.datetime.now(dt.timezone.utc).date()
    while day <= today:
        if day.weekday() < 5:
            hit = B.snap_for(snaps, day.isoformat())
            if hit:
                rows = B.measured_rows(B.git_json(hit[1], "near_watch.json"))
                if rows:
                    out[day.isoformat()] = sorted(rows)
        day += dt.timedelta(days=1)
    return out, sorted({s for v in out.values() for s in v})


def mode_status():
    by_day, syms = confirm_plan()
    log(f"📋 T-EMA3 — عدٌّ بلا نتيجة · العقد {'✅' if contract_ok() else '⛔ بصمةٌ مخالفة'}")
    log(f"   لقطاتُ «تحت المتابعة» منذ {SNAP_FROM}: {len(by_day)} يومًا · الرموز {len(syms):,}")
    for d in sorted(by_day):
        log(f"   {d}: {len(by_day[d]):,}")
    for part, nm in PARTS.items():
        log(f"   {nm}.json: {'صدر' if os.path.exists(os.path.join(OUT, nm + '.json')) else 'لم يصدر'}")
    return RC_OK


def mode_fetch(part, d_in=None):
    rc = guard(part)
    if rc:
        log(f"⛔ الحارس — خروج {rc}")
        return rc
    import Super_stock as S
    import tv_data as TV
    import case31_build as B
    plan = {}
    if part == "discover":
        import case31_b as CB
        entries = CB.entries_from_shards(d_in or "basket_slices")
        if not entries:
            log(f"⛔ لا إدخالاتِ CURRENT في الشرائح — خروج {RC_DATA}")
            return RC_DATA
        syms, plan = sorted({s for s, _d in entries}), {"entries": entries}
    else:
        by_day, syms = confirm_plan()
        if not syms:
            log(f"⛔ لا لقطات — خروج {RC_DATA}")
            return RC_DATA
        plan = {"snap_days": by_day}
    n_d, n_h4 = TV_N[part]
    log(f"🧺 {part}: الرموز {len(syms):,}")
    tmap = S._tv_ticker_map() or {}
    bars_d = B.tv_frames(syms + ["AAPL", "MSFT"], tmap, "1D", n_d, False)
    log(f"📺 يوميّ {len(bars_d)}/{len(syms) + 2}")
    bars_h4 = B.tv_frames(syms, tmap, "240", n_h4, True)
    log(f"📺 4 ساعات {len(bars_h4)}/{len(syms)}")
    if part == "discover":
        bars_d, bars_h4 = cut_blind(bars_d, TV.ny_day, D_BLIND), cut_blind(bars_h4, TV.ny_day, D_BLIND)
    plan["sessions"] = sorted({TV.ny_day(b[0]) for s in ("AAPL", "MSFT") for b in bars_d.get(s, [])})
    _dump(part, "plan.pkl.gz", plan)
    _dump(part, "bars_d.pkl.gz", {s: bars_d[s] for s in syms if s in bars_d})
    _dump(part, "bars_h4.pkl.gz", bars_h4)
    first = sorted(TV.ny_day(v[0][0]) for v in bars_h4.values() if v)
    cov = {"part": part, "symbols": len(syms), "daily": sum(1 for s in syms if s in bars_d), "h4": len(bars_h4),
           "h4_first_median": first[len(first) // 2] if first else None,
           "sessions": [plan["sessions"][0], plan["sessions"][-1]] if plan["sessions"] else None, "contract_sha": CONTRACT_SHA}
    _dump(part, "coverage.pkl.gz", cov)
    log("🧾 التغطية: " + json.dumps(cov, ensure_ascii=False))
    return RC_OK


def mode_run(part, d_in):
    rc = guard(part)
    if rc:
        log(f"⛔ الحارس — خروج {rc}")
        return rc
    import tv_data as TV
    import case31 as C31
    plan, bars_d, bars_h4 = _load(d_in, "plan.pkl.gz"), _load(d_in, "bars_d.pkl.gz"), _load(d_in, "bars_h4.pkl.gz")
    if not plan or not bars_d or not bars_h4:
        log(f"⛔ المادّةُ ناقصة — خروج {RC_DATA}")
        return RC_DATA
    memo = {}

    def day_of(ts):
        if ts not in memo:
            memo[ts] = TV.ny_day(ts)
        return memo[ts]

    def slot_of(ts):
        return TV.ny_time(ts).strftime("%H:%M")

    sessions = plan["sessions"]
    if part == "discover":
        bars_d, bars_h4 = cut_blind(bars_d, day_of, D_BLIND), cut_blind(bars_h4, day_of, D_BLIND)
        members = members_discover(plan["entries"], sessions)
    else:
        members = members_confirm(sessions, plan["snap_days"])

    def events(rows, lo, hi):
        return [e for e in C31.find_events(rows, lo, hi, 2.0) if C31.event_class(e) == "x100"]

    res = measure(bars_h4, bars_d, members, day_of, find_events=events, slot_of=slot_of, keep=True)
    if res is None:
        log(f"⛔ لا عضويّة — خروج {RC_DATA}")
        return RC_DATA
    recs = res.pop("recs")
    res.update(part=part, contract_sha=CONTRACT_SHA, fetch=_load(d_in, "coverage.pkl.gz"))
    os.makedirs(OUT, exist_ok=True)
    with gzip.GzipFile(os.path.join(OUT, PARTS[part] + "_rows.json.gz"), "wb", mtime=0) as fh:      # صفوفُ الإشارات: منها يُعاد جدولُ ب والحاكمة
        fh.write(json.dumps(recs, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    md = render(part, res)
    with open(os.path.join(OUT, PARTS[part] + ".json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, sort_keys=True)
    with open(os.path.join(OUT, PARTS[part] + ".md"), "w", encoding="utf-8") as fh:
        fh.write(md)
    log(md)
    if part == "confirm":
        return mode_verdict()
    return RC_OK


def mode_verdict():
    js = []
    for nm in PARTS.values():
        p = os.path.join(OUT, nm + ".json")
        if not os.path.exists(p):
            log(f"⛔ {nm}.json لم يصدر — خروج {RC_ORDER}")
            return RC_ORDER
        with open(p, encoding="utf-8") as fh:
            js.append(json.load(fh))
    md = render_verdict(*js)
    with open(os.path.join(OUT, "VERDICT.md"), "w", encoding="utf-8") as fh:
        fh.write(md)
    log(md)
    return RC_OK


def main(argv):
    if len(argv) < 2:
        log(__doc__)
        return RC_DATA
    mode = argv[1]
    d_in = argv[argv.index("--dir") + 1] if "--dir" in argv else None
    if mode == "status":
        return mode_status()
    if mode == "verdict":
        return mode_verdict()
    if mode in ("fetch", "run") and len(argv) >= 3:
        if closed():
            log(f"🔒 `T-EMA3` مُغلَقٌ مُنفَّذًا (الحكم «لا تعبر» · `T_EMA3_RESULT.md`) — الفتحُ إقرارُ المالك `EMA3_REOPEN=1` · خروج {RC_CLOSED}")
            return RC_CLOSED
        part = argv[2]
        if mode == "fetch":
            return mode_fetch(part, d_in)
        return mode_run(part, d_in or os.path.join(DATA, part))
    log(__doc__)
    return RC_DATA


if __name__ == "__main__":
    sys.exit(main(sys.argv))
