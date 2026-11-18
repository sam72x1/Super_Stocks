#!/usr/bin/env python3
"""⛏️🔗 `T-MINE` — «الرابط المشترك للمنفجرين» (العقد `T_MINE_prereg.md` · أمرُ المالك 2026-11-18 · آخرُ استثناء) — قراءةٌ فقط.

  feat <k> --years 2023,2024 --dir D   — سماتُ إدخالات CURRENT (رموزُ الشريحة k من 40) كما كانت يومَ القرار ‏+ وسمُ «المنفجر».
                                         سنتا التأكيد (2025 · 2026) تُرفضان (خروج 8) ما لم يكن ملفُّ التثبيت ببصمته.
  discover --dir D                     — §③ الاكتشافُ على 2023 و2024 وحدَهما ⟵ جدولُ الرابط المشترك ‏+ أفضلُ 3 توليفات (سطرُ `MINE_FREEZE`).
  confirm --dir D                      — §⑤ التأكيدُ مرّةً واحدة على 2025 ثمّ 2026 بلا تعديل (خروج 7 إن صدر · 9 بلا تثبيتٍ ببصمته).
🔒 لا تلغرام · لا كتابةَ حالة · لا CONFIG يُسنَد · والمادّةُ شرائحُ `T-BASKET` ‏`43955351411` وتحضيرُها (عُشيراتُ الزخم · FINRA · التقسيمات).
"""
import datetime as dt
import glob
import gzip
import itertools
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
NQ = os.path.join(ROOT, "fm_forensics", "nawaqis")
for _p in (ROOT, NQ):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import filter_core as FC                                          # noqa: E402

CONTRACT = os.path.join(HERE, "T_MINE_prereg.md")
CONTRACT_SHA = "96ee3a6d10b7b909eab0468107dcca8ee760ab3b71759646ad0918868d91e51b"
FREEZE = os.path.join(HERE, "data", "mine_freeze.json")
FREEZE_SHA = ""                                                   # §④ يُملأ في PR التثبيت قبل فتح 2025 · فارغٌ ⟵ التأكيدُ مرفوض
RESULT = os.path.join(HERE, "T_MINE_RESULT.md")
OUT = os.path.join(HERE, "out")
DISC_YEARS = ("2023", "2024")                                     # §③
CONF_YEARS = ("2025", "2026")                                     # §⑤
BARS_FROM, BARS_TO = "2020-10-01", "2026-11-16"                   # نافذةُ T-BASKET بحرفها
WIN = 20                                                          # نافذةُ الوسم = نافذةُ صفقة T-BASKET
MIN_N = 30                                                        # §⑦ هندسيٌّ من المالك: 30 حدثًا في السنة
MAX_K = 3                                                         # §⑦ حتى 3 شروط
TOP_N = 3                                                         # §⑦ أفضلُ 3 توليفات
COV_FLOOR = 0.80                                                  # تغطيةُ السمة في كلّ سنة اكتشاف (FILTER_PROTOCOL)
BANDS = ((0, 2), (3, 6), (7, 9))                                  # حُزَمُ عُشير الزخم (ضبطُ الزخم في الاكتشاف)
RC_OK, RC_KEY, RC_POP, RC_ONCE, RC_BLIND, RC_FREEZE, RC_CONTRACT = 0, 2, 5, 7, 8, 9, 11
PROXY_URL = "https://api.polygon.io/v3/reference/tickers/{t}?date={d}&apiKey={k}"


def log(m=""):
    print(m, flush=True)


def contract_ok():
    try:
        return FC.sha_of(CONTRACT) == CONTRACT_SHA
    except OSError:
        return False


def freeze_ok():
    try:
        return bool(FREEZE_SHA) and FC.sha_of(FREEZE) == FREEZE_SHA
    except OSError:
        return False


# ══ مؤشّراتٌ نقيّة (كلُّها حتى الصفّ i = يومُ القرار شاملًا · لا شيءَ بعده) ═══════════════════════════════
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


def ema(xs, n):
    k, out, e = 2.0 / (n + 1), [], None
    for x in xs:
        e = x if e is None else e + k * (x - e)
        out.append(e)
    return out


def _median(xs):
    xs = sorted(xs)
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2.0


def is_hammer(o, h, lo, c):
    body, rng = abs(c - o), h - lo
    if rng <= 0:
        return False
    return (min(o, c) - lo) >= 2 * body and (h - max(o, c)) <= body and (min(o, c) - lo) > 0


def is_doji(o, h, lo, c):
    rng = h - lo
    return rng > 0 and abs(c - o) <= 0.10 * rng


def is_engulf(po, pc, o, c):
    return pc < po and c > o and o <= pc and c >= po


def prior_explosions(closes, upto):
    """عددُ الانفجارات ‏+100% السابقة (تعريفُ `T-FPRINT` بحرفه: إغلاقٌ ‏≥ 2× أدنى إغلاقٍ في العشرين قبله · فاصلُ 40 جلسة)."""
    n, last = 0, -10_000
    for e in range(20, upto + 1):
        if e - last < 40:
            continue
        mn = min(closes[e - 20:e])
        if mn > 0 and closes[e] >= 2 * mn:
            n += 1
            last = e
    return n


def features(O, H, L, C, V, i):
    """(نقيّة) السماتُ الخامّ عند الصفّ i من شموعٍ مسوّاة ⟵ dict أو None إن قلّت الشموع عن 61 صفًّا حتى i."""
    if i < 60 or C[i] <= 0:
        return None
    f = {}
    w10 = range(i - 9, i + 1)
    ham = [j for j in w10 if is_hammer(O[j], H[j], L[j], C[j])]
    eng = [j for j in w10 if is_engulf(O[j - 1], C[j - 1], O[j], C[j])]
    f["hammer_ago"] = (i - ham[-1]) if ham else None
    f["engulf_ago"] = (i - eng[-1]) if eng else None
    f["doji_n10"] = sum(1 for j in w10 if is_doji(O[j], H[j], L[j], C[j]))
    f["doji_last"] = is_doji(O[i], H[i], L[i], C[i])
    f["lwick_max10"] = max((min(O[j], C[j]) - L[j]) / C[j] for j in w10 if C[j] > 0)
    f["uwick_max10"] = max((H[j] - max(O[j], C[j])) / C[j] for j in w10 if C[j] > 0)
    f["uwick_max5"] = max(H[j] / C[j] - 1.0 for j in range(i - 4, i + 1) if C[j] > 0)
    f["reversal3"] = any(C[j] > O[j] and C[j] > H[j - 1] and C[j - 1] < C[j - 2] and C[j - 2] < C[j - 3] for j in range(i - 2, i + 1))
    rng = H[i] - L[i]
    f["green_strong"] = bool(C[i] > O[i] and rng > 0 and (C[i] - L[i]) / rng >= 2.0 / 3.0)
    f["red3"] = bool(C[i] < C[i - 1] < C[i - 2] < C[i - 3])
    f["tight3"] = all(L[j] > 0 and (H[j] - L[j]) / L[j] <= 0.05 for j in range(i - 2, i + 1))
    r = rsi14(C[:i + 1])
    f["rsi"] = r[i]
    rs = [r[j] for j in w10 if r[j] is not None]
    f["rsi_min10"] = min(rs) if rs else None
    # الدايفرجنس القاعيّ بتعريف `T-DIVERGE` (MACD وحدَه): قاعٌ أدنى في العشر الأخيرة عن العشرين قبلها وخطُّ MACD أعلى
    i2 = min(range(i - 9, i + 1), key=lambda j: (L[j], -j))
    i1 = min(range(i - 29, i - 9), key=lambda j: (L[j], -j))
    m = [a - b for a, b in zip(ema(C[:i + 1], 12), ema(C[:i + 1], 26))]
    f["diverge"] = bool(L[i2] < L[i1] and m[i2] > m[i1])
    hi252 = max(H[max(0, i - 251):i + 1])
    f["drop252"] = 1.0 - C[i] / hi252 if hi252 > 0 else None
    lo20 = min(L[i - 19:i + 1])
    f["base_w20"] = (max(H[i - 19:i + 1]) - lo20) / lo20 if lo20 > 0 else None
    lo60 = min(L[i - 59:i + 1])
    f["low_age60"] = i - max(j for j in range(i - 59, i + 1) if L[j] == lo60)
    prior = V[i - 25:i - 5]
    mp = sum(prior) / len(prior)
    f["vdry"] = (sum(V[i - 4:i + 1]) / 5.0) / mp if mp > 0 else None
    med = _median(V[i - 20:i])
    f["vx_d"] = V[i] / med if med > 0 else None
    vx = []
    for j in w10:
        mj = _median(V[j - 20:j])
        if mj > 0:
            vx.append(V[j] / mj)
    f["vx_max10"] = max(vx) if vx else None
    f["usd_med20"] = _median([V[j] * C[j] for j in range(i - 19, i + 1)])
    sw, swr = False, False
    for j in w10:
        p20 = min(L[j - 20:j])
        if p20 > 0 and L[j] <= p20 * 0.98:
            if C[j] > p20:
                sw = True
            if C[i] > p20:
                swr = True
    f["sweep10"], f["sweep_reclaim"] = sw, swr
    ga, gb = False, False
    for j in range(max(1, i - 119), i + 1):
        if H[j] < L[j - 1]:                                       # فجوةٌ هابطة: أعلى اليوم دون أدنى الأمس
            if max(H[j:i + 1]) < L[j - 1] and C[i] < H[j] <= 2.0 * C[i]:
                ga = True
        if L[j] > H[j - 1]:                                       # فجوةٌ صاعدة: أدنى اليوم فوق أعلى الأمس
            if min(L[j:i + 1]) > H[j - 1] and H[j - 1] < C[i]:
                gb = True
    f["gap_above"], f["gap_below"] = ga, gb
    f["gapdn10"] = any(C[j - 1] > 0 and O[j] <= 0.90 * C[j - 1] for j in w10)
    f["gapup10"] = any(C[j - 1] > 0 and O[j] >= 1.10 * C[j - 1] for j in w10)
    f["ret5"] = C[i] / C[i - 5] - 1.0 if C[i - 5] > 0 else None
    f["ret20"] = C[i] / C[i - 20] - 1.0 if C[i - 20] > 0 else None
    f["above_ema20"] = bool(C[i] > ema(C[:i + 1], 20)[i])
    f["price"] = C[i]
    f["n_prior_expl"] = prior_explosions(C, i)
    return f


def exploded_label(H, C, i, pct, win=WIN):
    """«المنفجر» بتعريف البوت الحاليّ (`Super_stock.EXPLODED_PCT` بالاسم · أكبرُ من ‏+100% حصرًا من سعر الترشيح): أعلى High في الجلسات
    [D+1، D+win] مقابل إغلاق D (سعرُ الترشيح) ⟵ (bool، أقصى صعود) · None إن نقصت الجلسات اللاحقة عن win."""
    fut = H[i + 1:i + 1 + win]
    if len(fut) < win or C[i] <= 0:
        return None, None
    mx = max(fut) / C[i] - 1.0
    return bool(mx * 100.0 > pct), round(mx, 6)


def fwd_factor(splits, day):
    """∏(to/from) للتقسيمات المنفّذة **بعد** day ⟵ السعرُ المسوّى × الحاصل = سعرُ يومِه الخامّ · والحجمُ ÷ الحاصل (بلا نظرٍ لتقسيمٍ لاحق)."""
    f = 1.0
    for x, r in splits or []:
        if x > day and r and r > 0:
            f *= float(r)
    return f


def split_feats(splits, d):
    """التقسيماتُ العكسيّة (to/from أصغرُ من 1) المنفّذة في d أو قبله ⟵ (عمرُ آخرها بالأيّام أو None، عددُها في 365 يومًا)."""
    dd = dt.date.fromisoformat(d)
    ages = sorted((dd - dt.date.fromisoformat(x)).days for x, r in (splits or []) if r and r < 1 and x <= d)
    return (ages[0] if ages else None), sum(1 for a in ages if a <= 365)


# ══ الشروطُ الثنائيّة (§② من العقد · الاسمُ ⟵ الدالّة) — «K» مقفلةٌ منفردةً: تدخل التوليفات ولا تُرشَّح وحدَها ═══════
def _lt(k, x):
    return lambda v: None if v.get(k) is None else v[k] < x


def _le(k, x):
    return lambda v: None if v.get(k) is None else v[k] <= x


def _ge(k, x):
    return lambda v: None if v.get(k) is None else v[k] >= x


def _gt(k, x):
    return lambda v: None if v.get(k) is None else v[k] > x


def _b(k):
    return lambda v: None if v.get(k) is None else bool(v[k])


def _ago(k, x):
    return lambda v: None if "price" not in v else (v.get(k) is not None and v[k] <= x)


def _rng(k, a, b):
    return lambda v: None if v.get(k) is None else a <= v[k] < b


def _recover(v):
    if v.get("rsi") is None or v.get("rsi_min10") is None:
        return None
    return v["rsi_min10"] < 30 and v["rsi"] - v["rsi_min10"] >= 10


def _rs_within(days):
    return lambda v: None if "rs_n365" not in v else (v.get("rs_age") is not None and v["rs_age"] <= days)


def _dec(a, b):
    return lambda v: None if v.get("dec") is None else a <= v["dec"] <= b


CONDS = [
    ("C01_hammer10", _ago("hammer_ago", 9)), ("C02_hammer3", _ago("hammer_ago", 2)),
    ("C03_engulf10", _ago("engulf_ago", 9)), ("C04_engulf3", _ago("engulf_ago", 2)),
    ("C05_doji2", _ge("doji_n10", 2)), ("C06_doji_last", _b("doji_last")),
    ("C07_lwick10", _ge("lwick_max10", 0.10)), ("C08_uwick20", _ge("uwick_max10", 0.20)),
    ("C09_reversal3", _b("reversal3")), ("C10_green_strong", _b("green_strong")),
    ("C11_red3", _b("red3")), ("C12_tight3", _b("tight3")),
    ("K13_wick50", _ge("uwick_max5", 0.50)),
    ("R14_rsi_lt30", _lt("rsi", 30)), ("R15_rsi_lt40", _lt("rsi", 40)), ("R16_rsi_gt50", _gt("rsi", 50)),
    ("R17_rsimin_lt27", _lt("rsi_min10", 27)), ("R18_rsi_recover", _recover),
    ("K19_diverge", _b("diverge")),
    ("S20_shortratio_ge40", _ge("short_ratio", 0.40)), ("S21_shortratio_lt15", _lt("short_ratio", 0.15)),
    ("S22_short_le40k", _le("short_vol", 40_000)), ("K23_short_lt10k", _lt("short_vol", 10_000)),
    ("F24_shares_lt2m", _lt("shares", 2e6)), ("K25_shares_le5m", _le("shares", 5e6)),
    ("F26_shares_lt10m", _lt("shares", 10e6)), ("F27_shares_gt50m", _gt("shares", 50e6)),
    ("P28_rs365", _rs_within(365)), ("P29_rs90", _rs_within(90)), ("P30_rs30", _rs_within(30)),
    ("P31_rs_multi", _ge("rs_n365", 2)), ("P32_rs_none", lambda v: None if "rs_n365" not in v else v.get("rs_age") is None),
    ("D33_drop_ge95", _ge("drop252", 0.95)), ("D34_drop_ge90", _ge("drop252", 0.90)), ("D35_drop_lt80", _lt("drop252", 0.80)),
    ("B36_base_le25", _le("base_w20", 0.25)), ("B37_base_le40", _le("base_w20", 0.40)), ("B38_base_ge100", _ge("base_w20", 1.00)),
    ("T39_lowage_ge5", _ge("low_age60", 5)), ("T40_lowage_le1", _le("low_age60", 1)), ("T41_lowage_ge10", _ge("low_age60", 10)),
    ("V42_vdry", _le("vdry", 0.5)), ("V43_vspike_d", _ge("vx_d", 3.0)), ("V44_vspike10", _ge("vx_max10", 3.0)),
    ("V45_usd_lt100k", _lt("usd_med20", 100_000)), ("V46_usd_gt1m", _gt("usd_med20", 1_000_000)),
    ("K47_sweep10", _b("sweep10")), ("K48_sweep_reclaim", _b("sweep_reclaim")),
    ("G49_gap_above", _b("gap_above")), ("G50_gapdn10", _b("gapdn10")), ("G51_gapup10", _b("gapup10")),
    ("K52_gap_below", _b("gap_below")),
    ("M53_ret5_gt20", _gt("ret5", 0.20)), ("M54_ret5_lt_m10", _lt("ret5", -0.10)), ("M55_ret20_lt_m30", _lt("ret20", -0.30)),
    ("K56_above_ema20", _b("above_ema20")),
    ("Q57_px_lt1", _lt("price", 1.0)), ("Q58_px_1_2", _rng("price", 1.0, 2.0)), ("Q59_px_2_5", _rng("price", 2.0, 5.0)),
    ("Q60_px_ge5", _ge("price", 5.0)),
    ("X61_prior_ge2", _ge("n_prior_expl", 2)), ("X62_prior_0", _le("n_prior_expl", 0)),
    ("E63_offer30", _b("offer30")),
    ("M64_dec_top", _dec(8, 9)), ("M65_dec_bot", _dec(0, 1)),
]
NAMES = [n for n, _f in CONDS]
COMBO_ONLY = {n for n in NAMES if n.startswith("K")}


def cond_row(v):
    return [fn(v) for _n, fn in CONDS]


def band_of(dec):
    if dec is None:
        return len(BANDS)
    return next((k for k, (a, b) in enumerate(BANDS) if a <= dec <= b), len(BANDS))


# ══ الاكتشاف (§③) ══════════════════════════════════════════════════════════════════════════════════════
def year_stats(rows):
    """rows = [{x (منفجر 0/1)، band، e0، e50، r0، r50، sym}] لسنةٍ ⟵ المعدّلُ المتوقَّع لكلّ حزمة زخم."""
    tot, hit = {}, {}
    for r in rows:
        tot[r["band"]] = tot.get(r["band"], 0) + 1
        hit[r["band"]] = hit.get(r["band"], 0) + r["x"]
    return {b: hit[b] / tot[b] for b in tot}


def combo_eval(rows, mask, exp):
    """توليفةٌ على سنةٍ: mask[j] ∈ {True، False، None} ⟵ إحصاءاتُها (المجهولُ يسقط من الطرفين)."""
    w = [r for r, m in zip(rows, mask) if m is True]
    wo = [r for r, m in zip(rows, mask) if m is False]
    nw, no = len(w), len(wo)
    if not nw:
        return {"n_with": 0, "n_without": no}
    xw, xo = sum(r["x"] for r in w), sum(r["x"] for r in wo)
    p = sum(exp[r["band"]] for r in w) / nw
    rate = xw / nw
    se = math.sqrt(p * (1 - p) / nw) if 0 < p < 1 else None
    allx = xw + xo

    def _m(k):
        vs = [r[k] for r in w if r[k] is not None]
        return (sum(vs) / len(vs)) if vs else None
    return {"n_with": nw, "n_without": no, "x_with": xw, "x_without": xo, "rate_with": rate, "rate_without": (xo / no) if no else None,
            "exp": p, "adj": rate - p, "z": ((rate - p) / se) if se else None,
            "share_x": (xw / allx) if allx else None, "share_nx": ((nw - xw) / (nw + no - allx)) if (nw + no - allx) else None,
            "e0": _m("e0"), "e50": _m("e50"), "r0": _m("r0"), "r50": _m("r50")}


def and_mask(cols):
    out = []
    for vals in zip(*cols):
        if any(v is False for v in vals):
            out.append(False)
        elif any(v is None for v in vals):
            out.append(None)
        else:
            out.append(True)
    return out


def eligible(st):
    """§③ أهليّةُ توليفةٍ في سنة اكتشاف: 30 «مع» و30 «بدون» · فائضُ انفجارٍ موجب على ضبط الزخم · فائضُ العائد والعائدُ الخامّ موجبان في الذراعين."""
    return (st.get("n_with", 0) >= MIN_N and st.get("n_without", 0) >= MIN_N and st.get("z") is not None and st["adj"] > 0
            and all(st.get(k) is not None and st[k] > 0 for k in ("e0", "e50", "r0", "r50")))


def pick_top(cands, top_n=TOP_N):
    """§④ من مرشَّحين مرتَّبين: تُتخطّى توليفةٌ هي جزءٌ من مثبَّتةٍ أو تحويها أو تشاركها شرطين."""
    top = []
    for c in cands:
        s = set(c["conds"])
        if any(s <= set(t["conds"]) or s >= set(t["conds"]) or len(s & set(t["conds"])) >= 2 for t in top):
            continue
        top.append(c)
        if len(top) == top_n:
            break
    return top


def discover(by_year, cols_by_year, names=None, max_k=MAX_K, top_n=TOP_N):
    """§③-§④ ⟵ (جدولُ المنفردة، المرشَّحون المرتَّبون، عددُ المجرَّب، السماتُ المستبعَدة بالتغطية، الثلاثُ المثبَّتة)."""
    names = names or NAMES
    exp = {y: year_stats(by_year[y]) for y in DISC_YEARS}
    cov = {n: min((sum(1 for v in cols_by_year[y][k] if v is not None) / len(by_year[y])) if by_year[y] else 0.0 for y in DISC_YEARS)
           for k, n in enumerate(names)}
    usable = [k for k, n in enumerate(names) if cov[n] >= COV_FLOOR]
    singles = {names[k]: {y: combo_eval(by_year[y], cols_by_year[y][k], exp[y]) for y in DISC_YEARS} for k in range(len(names))}
    tried, cands = 0, []
    tbits = {y: [sum(1 << j for j, v in enumerate(c) if v is True) for c in cols_by_year[y]] for y in DISC_YEARS}   # تصفيةٌ سريعة بالعدّ وحدَه
    for size in range(1, max_k + 1):
        for combo in itertools.combinations(usable, size):
            if size == 1 and names[combo[0]] in COMBO_ONLY:
                continue
            tried += 1
            sts = {}
            for y in DISC_YEARS:
                bits = tbits[y][combo[0]]
                for k in combo[1:]:
                    bits &= tbits[y][k]
                if bin(bits).count("1") < MIN_N:
                    sts = None
                    break
                mask = cols_by_year[y][combo[0]] if size == 1 else and_mask([cols_by_year[y][k] for k in combo])
                if sum(1 for m in mask if m is True) < MIN_N:
                    sts = None
                    break
                sts[y] = combo_eval(by_year[y], mask, exp[y])
            if not sts or not all(eligible(sts[y]) for y in DISC_YEARS):
                continue
            cands.append({"conds": [names[k] for k in combo], "score": min(sts[y]["z"] for y in DISC_YEARS), "stats": sts})
    cands.sort(key=lambda c: (-c["score"], len(c["conds"]), c["conds"]))
    return singles, cands, tried, {n: round(c, 4) for n, c in cov.items() if c < COV_FLOOR}, pick_top(cands, top_n)


# ══ التأكيد (§⑤) ══════════════════════════════════════════════════════════════════════════════════════
def confirm_cell(rows, mask, boot_mean_fn):
    """سنةُ تأكيدٍ واحدة ⟵ لكلّ ذراع: n · (أ) متوسّطُ الفائض وفاصلُه · العائدُ الخامّ بعد الكلفة."""
    out = {}
    for arm, ek, rk in (("O0", "e0", "r0"), ("O50", "e50", "r50")):
        t = [(r["sym"], r[ek]) for r, m in zip(rows, mask) if m is True and r[ek] is not None]
        raw = [r[rk] for r, m in zip(rows, mask) if m is True and r[rk] is not None]
        out[arm] = {"n": len(t), "a_mean": (sum(v for _s, v in t) / len(t)) if t else None,
                    "a_ci": boot_mean_fn(t) if len(t) >= 2 else None, "raw": (sum(raw) / len(raw)) if raw else None}
    return out


def confirm_verdict(cells):
    """cells[year][arm] ⟵ «✅ تعبر» · «❌ لا تعبر» · «لا قياس» (§⑤: السنتان كلٌّ وحدَها · الذراعان · بالأضعف)."""
    for y in CONF_YEARS:
        for arm in FC.ARMS:
            if (cells.get(y) or {}).get(arm, {}).get("n", 0) < MIN_N:
                return "لا قياس"
    ok = all((cells[y][a].get("a_ci") or [0])[0] > 0 and (cells[y][a].get("raw") or 0) > 0 for y in CONF_YEARS for a in FC.ARMS)
    return "✅ تعبر" if ok else "❌ لا تعبر"


# ══ الرنر ══════════════════════════════════════════════════════════════════════════════════════════════
def _getjson(url, tries=4):
    import urllib.error
    import urllib.request
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "t-mine/1"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:                       # noqa: PERF203
            if e.code in (403, 404):
                return None
            time.sleep(2 ** k)
        except Exception:                                         # noqa: BLE001
            time.sleep(2 ** k)
    return None


def _bars(sym, key):
    js = _getjson(f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/day/{BARS_FROM}/{BARS_TO}?adjusted=true&sort=asc&limit=50000&apiKey={key}") or {}
    return [(dt.datetime.utcfromtimestamp(x["t"] / 1000).date().isoformat(), x["o"], x["h"], x["l"], x["c"], x.get("v") or 0.0)
            for x in js.get("results") or []]


def _load_one(d_in, name):
    ps = glob.glob(os.path.join(d_in, "**", name), recursive=True)
    if not ps:
        return None
    with gzip.open(ps[0], "rt", encoding="utf-8") as fh:
        return json.load(fh)


def mode_feat(key, k, years, d_in):
    if any(y in CONF_YEARS for y in years) and not freeze_ok():
        log(f"⛔ سنواتُ التأكيد {CONF_YEARS} مغلقةٌ قبل ملفّ التثبيت ببصمته (§④) — خروج {RC_BLIND}")
        return RC_BLIND
    recs, n = FC.load_shards(d_in)
    prep, extra = _load_one(d_in, "basket_rbprep.json.gz"), _load_one(d_in, "basket_extra.json.gz")
    if n != FC.NSHARDS or not prep or not extra:
        log(f"⛔ الشرائح {n} لا {FC.NSHARDS} أو غاب التحضير — خروج {RC_POP}")
        return RC_POP
    import Super_stock as S
    pct = float(S.EXPLODED_PCT)
    cur = [r for r in FC.current(recs) if r["y"] in years]
    syms = sorted({r["sym"] for r in FC.current(recs)})[k::FC.NSHARDS]
    by = {}
    for r in cur:
        if r["sym"] in set(syms):
            by.setdefault(r["sym"], []).append(r)
    out, why, t0 = [], {}, time.time()
    for j, sym in enumerate(sorted(by)):
        rows = _bars(sym, key)
        days = [x[0] for x in rows]
        ix = {d: q for q, d in enumerate(days)}
        O, H, Lw, C, V = ([x[q] for x in rows] for q in (1, 2, 3, 4, 5))
        for r in sorted(by[sym], key=lambda z: z["d"]):
            d = r["d"]
            base = {"sym": sym, "d": d, "y": r["y"], "dec": ((extra.get("decs") or {}).get(d) or {}).get(sym),
                    "e0": FC.excess(r, "O0"), "e50": FC.excess(r, "O50"),
                    "r0": ((r.get("res") or {}).get("O0") or {}).get("r"), "r50": ((r.get("res") or {}).get("O50") or {}).get("r")}
            i = ix.get(d)
            f = features(O, H, Lw, C, V, i) if i is not None else None
            if f is None:
                why["لا شمعة أو تاريخٌ قصير"] = why.get("لا شمعة أو تاريخٌ قصير", 0) + 1
                out.append(dict(base, x=None, v=None))
                continue
            x, mx = exploded_label(H, C, i, pct)
            if x is None:
                why["نافذةُ الوسم ناقصة"] = why.get("نافذةُ الوسم ناقصة", 0) + 1
            pd_ = (prep.get("prev_of") or {}).get(d)
            sv = ((prep.get("finra") or {}).get(pd_) or {}).get(sym) if pd_ else None
            sp = (prep.get("splits") or {}).get(sym)
            f["price"] = C[i] * fwd_factor(sp, d)                 # السعرُ الخامّ يومَ القرار لا المسوّى بتقسيمٍ لاحق
            fp = fwd_factor(sp, pd_) if pd_ else 1.0
            rawv = (V[i - 1] / fp) if fp else None
            f["short_vol"] = sv
            f["short_ratio"] = (sv / rawv) if (sv is not None and rawv and rawv > 0) else None
            js = _getjson(PROXY_URL.format(t=sym, d=pd_ or d, k=key)) or {}
            f["shares"] = (js.get("results") or {}).get("share_class_shares_outstanding")
            f["rs_age"], f["rs_n365"] = split_feats((prep.get("splits") or {}).get(sym), d)
            f["offer30"] = r.get("b")
            f["dec"] = base["dec"]
            out.append(dict(base, x=x, mx=mx, v=f))
        if j % 20 == 0:
            log(f"mine feat {k}: {j + 1}/{len(by)} رمزًا · {round(time.time() - t0)}s · إدخالات {len(out)}")
    os.makedirs(OUT, exist_ok=True)
    with gzip.open(os.path.join(OUT, f"mine_feat_{k:02d}.json.gz"), "wt", encoding="utf-8") as fh:
        json.dump({"shard": k, "years": list(years), "why": why, "rows": out}, fh, ensure_ascii=False)
    log(f"📦 mine feat {k}: {len(out)} إدخالًا · {why}")
    return RC_OK


def load_feat(d_in):
    paths = sorted(glob.glob(os.path.join(d_in, "**", "mine_feat_*.json.gz"), recursive=True))
    rows, why = [], {}
    for p in paths:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            js = json.load(fh)
        rows.extend(js["rows"])
        for a, b in (js.get("why") or {}).items():
            why[a] = why.get(a, 0) + b
    return rows, len(paths), why


def prepare(rows, years):
    """⟵ (by_year صفوفٌ موسومة بحزمتها، cols_by_year أعمدةُ الشروط) للإدخالات ذات الوسم والسمات."""
    by, cols = {}, {}
    for y in years:
        rr = [r for r in rows if r["y"] == y and r.get("x") is not None and r.get("v")]
        by[y] = [dict(sym=r["sym"], d=r["d"], x=int(bool(r["x"])), band=band_of(r.get("dec")), e0=r["e0"], e50=r["e50"], r0=r["r0"], r50=r["r50"])
                 for r in rr]
        mat = [cond_row(r["v"]) for r in rr]
        cols[y] = [[m[k] for m in mat] for k in range(len(CONDS))]
    return by, cols


def _p(x, d=1):
    return "—" if x is None else f"{x * 100:.{d}f}%"


def _sp(x):
    return "—" if x is None else f"{x * 100:+.1f}%"


def link_table(singles):
    L = ["| السمة | 2023 عند المنفجرين · عند غيرهم | 2023 الانفجار مع · بدون | 2024 عند المنفجرين · عند غيرهم | 2024 الانفجار مع · بدون | ملاحظة |",
         "|---|---|---|---|---|---|"]
    for n in NAMES:
        cells = []
        for y in DISC_YEARS:
            s = singles[n][y]
            cells += [f"{_p(s.get('share_x'))} · {_p(s.get('share_nx'))} (n {s.get('n_with', 0)})", f"{_p(s.get('rate_with'))} · {_p(s.get('rate_without'))}"]
        L.append(f"| `{n}` | " + " | ".join(cells) + f" | {'مقفلةٌ منفردةً — وصف' if n in COMBO_ONLY else ''} |")
    return L


def mode_discover(d_in):
    rows, n, why = load_feat(d_in)
    if n != FC.NSHARDS:
        log(f"⛔ شرائحُ السمات {n} لا {FC.NSHARDS} — خروج {RC_POP}")
        return RC_POP
    if any(r["y"] not in DISC_YEARS for r in rows):
        log(f"⛔ في المادّة سنةٌ خارج الاكتشاف {DISC_YEARS} — خروج {RC_BLIND}")
        return RC_BLIND
    by, cols = prepare(rows, DISC_YEARS)
    singles, cands, tried, lowcov, top = discover(by, cols)
    log("# ⛏️🔗 T-MINE — الاكتشاف (2023 · 2024)")
    for y in DISC_YEARS:
        allr = [r for r in rows if r["y"] == y]
        log(f"- {y}: إدخالات CURRENT {len(allr)} · موسومةٌ بسماتها {len(by[y])} · منفجرون {sum(r['x'] for r in by[y])} "
            f"({_p(sum(r['x'] for r in by[y]) / len(by[y]) if by[y] else None)})")
    log(f"- غيرُ المحسوب بأسبابه: {why}")
    log(f"- سماتٌ دون تغطية {COV_FLOOR:.0%} (لا تدخل توليفة): {lowcov}")
    log(f"- **التوليفاتُ المجرَّبة: {tried}** · المؤهَّلةُ في السنتين: {len(cands)}")
    log("")
    log("## جدولُ «الرابط المشترك» (الاكتشاف)")
    for ln in link_table(singles):
        log(ln)
    log("")
    log("## أفضلُ 15 مؤهَّلة (بالدرجة = أدنى z في السنتين)")
    for c in cands[:15]:
        s3, s4 = c["stats"]["2023"], c["stats"]["2024"]
        log(f"- {' ∧ '.join(c['conds'])} · z {c['score']:.2f} · 2023: n {s3['n_with']} · انفجار {_p(s3['rate_with'])} مقابل متوقَّع {_p(s3['exp'])} · "
            f"فائض O0 {_sp(s3['e0'])} · 2024: n {s4['n_with']} · {_p(s4['rate_with'])} مقابل {_p(s4['exp'])} · فائض O0 {_sp(s4['e0'])}")
    fz = {"contract_sha": CONTRACT_SHA, "tried": tried, "eligible": len(cands),
          "top": [{"conds": c["conds"], "score": round(c["score"], 6),
                   "stats": {y: {k: (round(v, 6) if isinstance(v, float) else v) for k, v in c["stats"][y].items()} for y in DISC_YEARS}} for c in top]}
    log("")
    log("MINE_FREEZE " + json.dumps(fz, ensure_ascii=False, sort_keys=True))
    log("MINE_SINGLES " + json.dumps({n: {y: {k: (round(v, 6) if isinstance(v, float) else v) for k, v in singles[n][y].items()} for y in DISC_YEARS}
                                      for n in NAMES}, ensure_ascii=False, sort_keys=True))
    return RC_OK


def mode_confirm(d_in):
    if os.path.exists(RESULT):
        log(f"⛔ صدر حكمُ التأكيد سلفًا (`{os.path.basename(RESULT)}`) — مرّةً واحدة (§⑤) · خروج {RC_ONCE}")
        return RC_ONCE
    if not freeze_ok():
        log(f"⛔ ملفُّ التثبيت غائبٌ أو لا يطابق بصمتَه — خروج {RC_FREEZE}")
        return RC_FREEZE
    rows, n, why = load_feat(d_in)
    if n != FC.NSHARDS:
        log(f"⛔ شرائحُ السمات {n} لا {FC.NSHARDS} — خروج {RC_POP}")
        return RC_POP
    fz = json.load(open(FREEZE, encoding="utf-8"))
    B = FC._basket()
    by, cols = prepare(rows, CONF_YEARS)
    idx = {nm: k for k, nm in enumerate(NAMES)}
    log("# ⛏️🔗 T-MINE — التأكيد (2025 ثمّ 2026 · مرّةً واحدة)")
    for y in CONF_YEARS:
        log(f"- {y}: موسومةٌ بسماتها {len(by[y])} · منفجرون {sum(r['x'] for r in by[y])} ({_p(sum(r['x'] for r in by[y]) / len(by[y]) if by[y] else None)})")
    log(f"- غيرُ المحسوب بأسبابه: {why}")
    verdicts = []
    for t in fz["top"]:
        cells, desc = {}, {}
        for y in CONF_YEARS:
            cs = [cols[y][idx[c]] for c in t["conds"]]
            mask = cs[0] if len(cs) == 1 else and_mask(cs)
            cells[y] = confirm_cell(by[y], mask, B.boot_mean)
            desc[y] = combo_eval(by[y], mask, year_stats(by[y])) if by[y] else {}
        v = confirm_verdict(cells)
        verdicts.append(v)
        log("")
        log(f"## {' ∧ '.join(t['conds'])} — **{v}**")
        log("| السنة | الذراع | n مع | (أ) الفائضُ على ضابط الزخم | فاصل 95% | العائدُ بعد الكلفة | الانفجار مع · بدون · المتوقَّع بالزخم |")
        log("|---|---|---|---|---|---|---|")
        for y in CONF_YEARS:
            for arm in FC.ARMS:
                c, s = cells[y][arm], desc[y]
                log(f"| {y} | {arm} | {c['n']} | {_sp(c['a_mean'])} | {FC.ci_txt(c['a_ci'])} | {_sp(c['raw'])} | "
                    f"{_p(s.get('rate_with'))} · {_p(s.get('rate_without'))} · {_p(s.get('exp'))} |")
    log("")
    log("⚖️ T-MINE: " + " · ".join(verdicts))
    return RC_OK


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not contract_ok():
        log(f"⛔ العقد لا يطابق بصمتَه — خروج {RC_CONTRACT} قبل أيّ جلب")
        return RC_CONTRACT
    mode = argv[0] if argv else ""
    d_in = argv[argv.index("--dir") + 1] if "--dir" in argv else "mine_in"
    if mode == "discover":
        return mode_discover(d_in)
    if mode == "confirm":
        return mode_confirm(d_in)
    if mode == "feat":
        key = (os.environ.get("POLYGON_API_KEY") or "").strip()
        if not key:
            log(f"⛔ بلا مفتاح Polygon — خروج {RC_KEY}")
            return RC_KEY
        years = tuple(argv[argv.index("--years") + 1].split(","))
        return mode_feat(key, int(argv[1]), years, d_in)
    log("⛔ feat <k> --years … | discover | confirm")
    return 1


if __name__ == "__main__":
    sys.exit(main())
