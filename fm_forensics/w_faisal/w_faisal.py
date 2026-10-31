# -*- coding: utf-8 -*-
"""📝 `T-W-FAISAL` — نموذجُ W / القاعُ المزدوج بتعريف فيصل على 30 دقيقة و4 ساعات (العقد `T_W_FAISAL_prereg.md` · 2026-10-31).

**قياسٌ فقط · لا تلغرام · لا كرون · لا إنتاج** · وشيفرةُ النتيجة (§⑤-§⑦) أُضيفت بأمر المالك «ابن W» (2026-10-31) خلف بصمة الملحق 1.
الأوضاع (`W_MODE`):
    accept          §⑧ القبولُ على وحدات فيصل الخمس (Polygon REST دقيقة · خامّ مسوًّى حتى اللقطة)
    feas_prep       §③ المجتمعُ من صفوف شرائح الجزء ب (BASE2) ‏+ تقسيماتُ الفترة ⟵ out/prep.json.gz
    feas_shard      §③ ملفّاتُ الدقيقة (SHARD · NSHARDS) ⟵ شموعُ 30د للرموز المطلوبة ⟵ out/bars_NN.json.gz
    feas_assemble   §⑨ جدوى العدّ: الأحداثُ لكلّ خليّة · القُمعُ · التغطية — بلا عائد
    measure_prep    §⑤ (بأمر «ابن W» · الملحق 1) الأحداثُ ‏+ C1 ‏+ C2 ⟵ مواصفاتُ الصفقات وطلباتُ الاقتباس — بلا عائدٍ يُطبع
    measure_quotes  §⑤ NBBO `/v3/quotes` لشريحة طلبات (SHARD)
    measure_final   §⑤-§⑦ الكلفة ⟵ G50/G100 ⟵ الفروق ⟵ البوتستراب ⟵ الحكمُ بالأضعف · والسلّمُ وصفٌ بجانبه
    --guards        حرّاسٌ اصطناعيّة بلا شبكة (WF1-WF31)
والبصمةُ `CONTRACT_SHA` تُفحص قبل أيّ شبكة ⟵ عدمُ المطابقة خروج 9 · وأوضاعُ القياس تشترط معها `ADDENDUM_SHA`.
"""
import bisect
import datetime as dt
import glob
import gzip
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import time
from zoneinfo import ZoneInfo

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (ROOT, os.path.join(ROOT, "faisal_method_v3")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import chart_id_tv as CID          # noqa: E402  §②-1 التجميعُ بالاسم
import faisal_tool as FT           # noqa: E402  §②-2 المحاورُ · §⑥ C1 · §②-10 الرؤوس
import market_calendar as MC       # noqa: E402

_rb_spec = importlib.util.spec_from_file_location("rebuild_wf", os.path.join(ROOT, "fm_forensics", "rebuild", "rebuild.py"))
RB = importlib.util.module_from_spec(_rb_spec)
_rb_spec.loader.exec_module(RB)    # §③ التقويمُ (`sessions_between`) بالاسم

CONTRACT = os.path.join(HERE, "T_W_FAISAL_prereg.md")
CONTRACT_SHA = "bd6631270813ff6d29551a8bbc6a4aab3e24f63989b5828b420b19670197da1e"   # بصمةُ العقد (WFA1) — عدمُ المطابقة ⟵ خروج 9
SHA_RC = 9
OUT = os.path.join(HERE, "out")
NY = ZoneInfo("America/New_York")

# ── الثوابتُ بوسومها (العقد §②) ─────────────────────────────────────────────────────────────
TOL = 0.03                                         # ②-2 التسامح · engineering («ابدأ بـ3%» بأمر المالك)
NECK_MIN = FT.P("NECK_RISE_MIN_PCT") / 100.0       # ②-2 العنقُ 10% فوق أعلى القاعين · faisal_verbatim (METHOD_BOUNCE_MIN_PCT · IMG_0486)
K = FT.P("SWING_K_30M")                            # ②-2 عرضُ المحور 2 على الفريمين · engineering
SESS_BARS = {"30m": 32, "4h": 5}                   # شموعُ الجلسة الممتدّة لكلّ فريم
SPAN_SESS = 20                                     # ②-2 أقصى فصلٍ · ②-3 نافذةُ التأكيد · ③ الأفق · engineering
POP_WIN = 20                                       # ②-8 BASE2 في [D−20 · D−1] · engineering
NEED_BACK, NEED_FWD = 40, 59                       # ③ شموعُ يومٍ تُحمَّل إن انطلق BASE2 في [اليوم−40 · اليوم+59]
STARTS = {"30m": [240 + 30 * i for i in range(32)], "4h": [240, 330, 570, 810, 1050]}   # ②-1 (04:00…19:30) · (04:00 05:30 09:30 13:30 17:30)
END = 20 * 60
EVAL_FROM, EVAL_TO = "2023-01-03", "2025-12-31"   # ③ ثلاثُ سنوات
BARS_FROM, BARS_TO = "2022-10-03", "2026-01-30"
RB_RUNS = {"bases": 40741993539, "test": 40769876230}   # ②-8 شرائحُ الجزء ب (TRAIN/VAL · TEST)
SEED = 20261031
MIN_PREFIX = "us_stocks_sip/minute_aggs_v1"

# ── §⑧ الوحداتُ الخمس بقراءة العين (2026-10-31) ───────────────────────────────────────────────────
UNITS = [
    {"id": "U1", "sym": "NUWE", "src": "CH_20260918_07_NUWE", "drawn_tf": "4h", "l1": 0.7031, "neck": 0.8298, "l2": 0.7482,
     "owner_l2": 0.6998, "win": ("2026-08-31", "2026-10-16"), "anchor": "2026-09-18"},
    {"id": "U2", "sym": "VEEE", "src": "TG_58045", "drawn_tf": "4h", "l1": 5.40, "neck": 8.76, "l2": 6.18,
     "date_rule": {"from": "2026-04-01", "to": "2026-06-30", "close": (6.75, 6.77), "ah": (6.88, 6.90), "win_from": "2026-05-01"},
     "fallback_win": ("2026-04-15", "2026-06-30")},
    {"id": "U3", "sym": "EZRA", "src": "TG_58046", "drawn_tf": "1D", "l1": 3.22, "neck": 3.994, "l2": 3.030,
     "win": ("2026-06-01", "2026-07-29"), "anchor": "2026-06-30"},
    {"id": "U4", "sym": "DXST", "src": "IMG_0627", "drawn_tf": "30m", "l1": 2.46, "neck": 2.864, "l2": 2.54,
     "win": ("2026-06-01", "2026-07-15"), "anchor": "2026-06-16"},
    {"id": "U5", "sym": "SXTC", "src": "TG_50590", "drawn_tf": "1D", "l1": 1.780, "neck": 2.913, "l2": 2.05,
     "date_rule": {"from": "2026-01-01", "to": "2026-10-30", "low": 1.780, "close": (2.38, 2.42), "peak": 10.400}},
]


def log(m=""):
    print(m, flush=True)


def contract_sha():
    with open(CONTRACT, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def contract_ok():
    return os.path.exists(CONTRACT) and contract_sha() == CONTRACT_SHA


# ── الشموع (§②-1) ────────────────────────────────────────────────────────────────────────
def day_start_utc(day):
    """منتصفُ ليل نيويورك لليوم بثواني epoch (الإزاحةُ ثابتةٌ داخل 04:00-20:00: التوقيتُ الصيفيّ يتبدّل 02:00 الأحد)."""
    y, m, d = (int(x) for x in day.split("-"))
    return int(dt.datetime(y, m, d, tzinfo=NY).timestamp())


def bars_30(minutes):
    """دقائق [(ts بالثواني، o، h، l، c، v)] ليومٍ أو أكثر ⟵ شموعُ 30 دقيقة بـ`chart_id_tv.aggregate` بالاسم (04:00 ⟵ 20:00)."""
    return CID.aggregate(minutes, STARTS["30m"], END)


def bars_4h(b30):
    """شموعُ 4 ساعات من شموع الثلاثين نفسِها (الحدودُ كلُّها على أنصاف الساعات) بـ`chart_id_tv.aggregate` بالاسم."""
    return CID.aggregate(b30, STARTS["4h"], END)


def frame_bars(b30, frame):
    return b30 if frame == "30m" else bars_4h(b30)


def ny_day(ts):
    return dt.datetime.fromtimestamp(int(ts), tz=NY).date().isoformat()


# ── الكاشف (§②-2 · §②-3 · §②-4 · §②-7) — دالّةٌ نقيّة ───────────────────────────────────────
def trend_at(t, iN, N, iP0, P0):
    """§②-3 الترند: الخطُّ من P0 إلى N ممدودًا."""
    return N + (t - iN) * (N - P0) / float(iN - iP0)


def is_hammer(o, h, l, c):
    """§②-9 وسمُ المطرقة (engineering): ذيلٌ سفليٌّ ضعفا الجسم فأكثر ∧ علويٌّ لا يتجاوز الجسم."""
    body = abs(c - o)
    lower = min(o, c) - l
    upper = h - max(o, c)
    return (h - l) > 0 and lower >= 2 * body and upper <= body


def detect(o, h, l, c, sess_bars, tol=TOL, neck_min=NECK_MIN, k=K, span_sess=SPAN_SESS):
    """⟵ (أحداث a · أحداث b · Ms · قُمع). كلُّ W يُقيَّم عند تكوّنه (`i2 + k`) ثمّ يُمسح للأمام حتى 20 جلسة:
    M (إغلاقٌ تحت B) يوقف · السحبُ (low تحت B وإغلاقٌ فوقه) ⟵ b · وأوّلُ إغلاقٍ فوق N والترند ⟵ a."""
    o, h, l, c = (np.asarray(x, dtype=float) for x in (o, h, l, c))
    n = len(c)
    span = span_sess * sess_bars
    fun = {"L2": 0, "no_l1": 0, "tol": 0, "span": 0, "neck": 0, "decline": 0, "W": 0,
           "a": 0, "b": 0, "M": 0, "expired": 0, "trend_binding": 0, "dedup_a": 0, "dedup_b": 0}
    ev_a, ev_b, ms = [], [], []
    if n < 2 * k + 3:
        return ev_a, ev_b, ms, fun
    sw = FT.confirmed_swings(h, l, n - 1, k)
    lows = [(i, p) for i, t, p in sw if t == "L"]
    li = [i for i, _ in lows]
    lp = np.array([p for _, p in lows], dtype=float)
    last = {"a": -1, "b": -1}
    order = ("tol", "span", "neck", "decline")
    for j, (i2, p2) in enumerate(lows):
        fun["L2"] += 1
        lo_j = bisect.bisect_left(li, i2 - span)
        cand = [m for m in range(lo_j, j) if i2 - li[m] >= 2]
        if not cand:
            fun["no_l1"] += 1
            continue
        best, reach = None, -1
        for m in cand:
            i1, p1 = li[m], float(lp[m])
            B = min(p1, p2)
            if abs(p2 - p1) / B > tol:
                reach = max(reach, 0)
                continue
            if float(np.min(l[i1 + 1:i2])) < B:
                reach = max(reach, 1)
                continue
            seg = h[i1 + 1:i2]
            iN = i1 + 1 + int(np.argmax(seg))
            N = float(seg.max())
            if N < max(p1, p2) * (1 + neck_min):
                reach = max(reach, 2)
                continue
            j0 = max(0, i1 - span)
            if j0 >= i1:
                reach = max(reach, 3)
                continue
            pre = h[j0:i1]
            iP0 = j0 + int(np.argmax(pre))
            P0 = float(pre.max())
            if not P0 > N:
                reach = max(reach, 3)
                continue
            reach = 4
            if best is None or N > best["N"] or (N == best["N"] and i1 < best["i1"]):
                best = {"i1": i1, "L1": p1, "i2": i2, "L2": p2, "B": B, "iN": iN, "N": N, "iP0": iP0, "P0": P0}
        if best is None:
            fun[order[reach] if reach < 4 else "decline"] += 1
            continue
        fun["W"] += 1
        B, N = best["B"], best["N"]
        t0, tend = i2 + k, min(n - 1, i2 + span)
        a_t = b_t = m_t = None
        for t in range(t0, tend + 1):
            if c[t] < B:
                m_t = t
                break
            if c[t] > N:
                if c[t] > trend_at(t, best["iN"], N, best["iP0"], best["P0"]):
                    a_t = t
                    break
                fun["trend_binding"] += 1
            if b_t is None and l[t] < B and c[t] > B:
                b_t = t
        w = dict(best, hammer=bool(is_hammer(o[i2], h[i2], l[i2], c[i2])))
        if m_t is not None:
            fun["M"] += 1
            ms.append(dict(w, sig=m_t))
        if b_t is not None:
            if i2 > last["b"]:
                fun["b"] += 1
                ev_b.append(dict(w, sig=b_t, depth=round((B - float(l[b_t])) / B * 100, 2)))
                last["b"] = b_t
            else:
                fun["dedup_b"] += 1
        if a_t is not None:
            if i2 > last["a"]:
                fun["a"] += 1
                ev_a.append(dict(w, sig=a_t))
                last["a"] = a_t
            else:
                fun["dedup_a"] += 1
        if a_t is None and m_t is None:
            fun["expired"] += 1
    return ev_a, ev_b, ms, fun


# ── المجتمع (§②-8) ──────────────────────────────────────────────────────────────────────────
def fires_from_shards(paths):
    """صفوفُ شرائح الجزء ب ⟵ {رمز: [أيّامُ انطلاق BASE2]} — bases: {sym: [[D, BASE2, …]]} · test: [[sym, D, ?, BASE2, …]]."""
    out = {}
    for p in paths:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            sh = json.load(fh)
        rows = sh.get("rows")
        if isinstance(rows, dict):
            for sym, rs in rows.items():
                for r in rs:
                    if r[1]:
                        out.setdefault(sym, set()).add(r[0])
        else:
            for r in rows or []:
                if r[3]:
                    out.setdefault(r[0], set()).add(r[1])
    return {s: sorted(v) for s, v in out.items()}


class Pop:
    """BASE2 في [D−20 · D−1] جلسات (`in_pop`) · و«المطلوب» في [اليوم−40 · اليوم+59] (`needed`)."""

    def __init__(self, fires, sessions):
        self.sess = list(sessions)
        self.idx = {d: i for i, d in enumerate(self.sess)}
        self.fi = {s: sorted(self.idx[d] for d in ds if d in self.idx) for s, ds in fires.items()}

    def _any(self, sym, a, b):
        arr = self.fi.get(sym) or []
        j = bisect.bisect_left(arr, a)
        return j < len(arr) and arr[j] <= b

    def in_pop(self, sym, day):
        i = self.idx.get(day)
        return i is not None and self._any(sym, i - POP_WIN, i - 1)

    def needed(self, day):
        i = self.idx.get(day)
        if i is None:
            return set()
        return {s for s in self.fi if self._any(s, i - NEED_BACK, i + NEED_FWD)}


def split_between(splits_sym, d0, d1):
    """§③ تقسيمٌ تنفيذُه في (d0 · d1] ⟵ الحدثُ يُستبعد."""
    return any(d0 < e <= d1 for e, _, _ in (splits_sym or ()))


def asof_scale(bars, splits_sym, anchor):
    """§③ القبول: شموعٌ خامّة ⟵ مسوّاةٌ بالتقسيمات **حتى المرساة وحدَها** (ما بعد اللقطة لا يُطبَّق) — السعرُ × (from/to) والحجمُ ÷."""
    out = []
    for b in bars:
        day = ny_day(b[0])
        f = 1.0
        for e, fr, to in splits_sym or ():
            if day < e <= anchor and to:
                f *= fr / to
        out.append([b[0], b[1] * f, b[2] * f, b[3] * f, b[4] * f, (b[5] / f) if f else b[5]])
    return out


# ── الشبكة ───────────────────────────────────────────────────────────────────────────────
def _poly(path_or_url, key, params=None, tries=4):
    import requests
    url = path_or_url if path_or_url.startswith("http") else "https://api.polygon.io" + path_or_url
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers={"Authorization": f"Bearer {key}"}, timeout=40)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 * (2 ** i))
                continue
            log(f"   ⛔ {r.status_code} {url[:90]}")
            return None
        except Exception as e:                       # noqa: BLE001
            log(f"   ⛔ {type(e).__name__} {url[:90]}")
            time.sleep(2 * (2 ** i))
    return None


def _paged(path, key, params):
    out, j = [], _poly(path, key, params)
    while j:
        out += j.get("results") or []
        nu = j.get("next_url")
        j = _poly(nu, key) if nu else None
    return out


def minutes_rest(sym, d0, d1, key):
    rows = _paged(f"/v2/aggs/ticker/{sym}/range/1/minute/{d0}/{d1}", key, {"adjusted": "false", "sort": "asc", "limit": 50000})
    return [[int(r["t"]) // 1000, float(r["o"]), float(r["h"]), float(r["l"]), float(r["c"]), float(r.get("v") or 0)] for r in rows]


def splits_rest(key, sym=None, d0=None, d1=None):
    p = {"limit": 1000}
    if sym:
        p["ticker"] = sym
    if d0:
        p["execution_date.gte"], p["execution_date.lte"] = d0, d1
    out = {}
    for r in _paged("/v3/reference/splits", key, p):
        try:
            out.setdefault(str(r["ticker"]).upper(), []).append((str(r["execution_date"]), float(r["split_from"]), float(r["split_to"])))
        except (KeyError, TypeError, ValueError):
            continue
    return out


# ── §⑧ القبول ─────────────────────────────────────────────────────────────────────────────
def match_unit(ev_a, ts, unit, win):
    """§⑧ «مُلتقَطة»: حدثُ (a) شمعتُه داخل النافذة و`L1` ضمن ±3% من القاع الأوّل المرسوم ⟵ أوّلُها أو None."""
    for e in ev_a:
        d = ny_day(ts[e["sig"]])
        if win[0] <= d <= win[1] and abs(e["L1"] - unit["l1"]) / unit["l1"] <= TOL:
            return e
    return None


def diagnose(o, h, l, c, ts, unit, win, sess_bars):
    """§⑧ أوّلُ بندٍ سقطت عليه الوحدة — لكلّ قاعٍ مؤكَّدٍ عند رقم فيصل (±3%) في النافذة: أبعدُ مرحلةٍ بلغها مع أيّ قاعٍ ثانٍ."""
    n = len(c)
    span = SPAN_SESS * sess_bars
    sw = FT.confirmed_swings(np.asarray(h, float), np.asarray(l, float), n - 1, K)
    lows = [(i, p) for i, t, p in sw if t == "L"]
    near = [(i, p) for i, p in lows if win[0] <= ny_day(ts[i]) <= win[1] and abs(p - unit["l1"]) / unit["l1"] <= TOL]
    if not near:
        inwin = [(i, p) for i, p in lows if win[0] <= ny_day(ts[i]) <= win[1]]
        best = min(inwin, key=lambda x: abs(x[1] - unit["l1"]), default=None)
        return {"item": "②قاعٌ عند رقم فيصل", "detail": f"لا قاعَ مؤكَّدًا ضمن ±3% من {unit['l1']} · أقربُ قاعٍ في النافذة "
                + (f"{best[1]:.4f} ({ny_day(ts[best[0]])})" if best else "لا شيء")}
    stages = ["②التسامح", "②R-W-SPAN", "②العنق 10%", "②الهبوطُ السابق", "W"]
    out = None
    for i1, p1 in near:
        for i2, p2 in lows:
            if not (i1 + 2 <= i2 <= i1 + span):
                continue
            B = min(p1, p2)
            gap = abs(p2 - p1) / B
            r, det = 0, f"L1 {p1:.4f} ({ny_day(ts[i1])}) · L2 {p2:.4f} ({ny_day(ts[i2])}) · فرق {gap * 100:.1f}%"
            if gap <= TOL:
                r = 1
                if float(np.min(l[i1 + 1:i2])) >= B:
                    r = 2
                    seg = h[i1 + 1:i2]
                    N = float(np.max(seg))
                    det += f" · العنق {N:.4f} (+{(N / max(p1, p2) - 1) * 100:.1f}%)"
                    if N >= max(p1, p2) * (1 + NECK_MIN):
                        r = 3
                        j0 = max(0, i1 - span)
                        P0 = float(np.max(h[j0:i1])) if j0 < i1 else 0.0
                        det += f" · P0 {P0:.4f}"
                        if P0 > N:
                            r = 4
            if out is None or r > out[0] or (r == out[0] and gap < out[2]):
                out = (r, det, gap)
    if out[0] < 4:
        return {"item": stages[out[0]], "detail": out[1]}
    return {"item": "⑦M أوّلًا أو ③لا إغلاقَ فوق العنق خلال 20 جلسة", "detail": out[1]}


def date_unit(unit, key):
    """§⑧ قاعدةُ التأريخ لـU2/U5 من الشموع اليوميّة الخامّة (المسوّاة حتى كلّ مرشّح) ⟵ (مرساة · نافذة · سبب)."""
    r = unit["date_rule"]
    sym = unit["sym"]
    d = _paged(f"/v2/aggs/ticker/{sym}/range/1/day/{r['from']}/{r['to']}", key, {"adjusted": "false", "sort": "asc", "limit": 50000})
    days = [(ny_day(int(x["t"]) // 1000), float(x["h"]), float(x["l"]), float(x["c"])) for x in d]
    sp = splits_rest(key, sym=sym).get(sym, [])
    sess = RB.sessions_between(r["from"], "2026-12-31", MC)

    def plus(day, k):
        i = bisect.bisect_left(sess, day)
        return sess[min(len(sess) - 1, i + k)]

    def fac(day, anchor):
        f = 1.0
        for e, fr, to in sp:
            if day < e <= anchor and to:
                f *= fr / to
        return f

    if unit["id"] == "U2":
        for dd, _, _, cc in days:
            if r["close"][0] <= cc * fac(dd, dd) <= r["close"][1]:
                mins = minutes_rest(sym, dd, dd, key)
                ah = [m for m in mins if ny_day(m[0]) == dd and 960 <= (m[0] - day_start_utc(dd)) // 60 < END]
                last = ah[-1][4] if ah else None
                if last is not None and r["ah"][0] <= last <= r["ah"][1]:
                    return dd, (r["win_from"], plus(dd, SPAN_SESS)), f"إغلاق {cc} · آخرُ أفتر {last}"
        return None, unit["fallback_win"], "لا تاريخ"
    pk = [x for x in days if abs(x[1] - r["peak"]) / r["peak"] <= 0.01]
    after = [x for x in days if not pk or x[0] > pk[0][0]]
    lo = min(after, key=lambda x: x[2], default=None)
    if not lo or abs(lo[2] * fac(lo[0], lo[0]) - r["low"]) / r["low"] > 0.01:
        return None, None, f"لا قاعَ {r['low']} (±1%) بعد القمّة · أدنى ما بعدها {lo[2] if lo else '—'}"
    for dd, _, _, cc in days:
        if dd > lo[0] and r["close"][0] <= cc * fac(dd, dd) <= r["close"][1]:
            i = bisect.bisect_left(sess, lo[0])
            return dd, (sess[max(0, i - 5)], plus(dd, SPAN_SESS)), f"قاعُ {lo[2]} يومَ {lo[0]} · إغلاق {cc}"
    return None, None, f"قاعُ {lo[2]} يومَ {lo[0]} ولا إغلاقَ 2.38-2.42 بعده"


def mode_accept(key):
    res = []
    for u in UNITS:
        anchor, win, why = u.get("anchor"), u.get("win"), "مؤرَّخةٌ بالصورة"
        if "date_rule" in u:
            anchor, win, why = date_unit(u, key)
            if win is None:
                log(f"⛔ {u['id']} {u['sym']}: {why} ⟵ غيرُ مُلتقَطة (لا تاريخ)")
                res.append({"id": u["id"], "sym": u["sym"], "caught": False, "why": why, "frames": {}})
                continue
        anc = anchor or win[1]
        sess = RB.sessions_between("2025-12-01", "2026-12-31", MC)
        i0 = bisect.bisect_left(sess, win[0])
        fetch_from = sess[max(0, i0 - 2 * SPAN_SESS - 5)]
        mins = minutes_rest(u["sym"], fetch_from, win[1], key)
        sp = splits_rest(key, sym=u["sym"]).get(u["sym"], [])
        mins = asof_scale(mins, sp, anc)
        b30 = bars_30(mins)
        row = {"id": u["id"], "sym": u["sym"], "src": u["src"], "anchor": anchor, "win": list(win), "dating": why,
               "minutes": len(mins), "splits": sp, "frames": {}}
        for fr in ("30m", "4h"):
            bb = frame_bars(b30, fr)
            ts = [b[0] for b in bb]
            o, h, l, c = ([b[x] for b in bb] for x in (1, 2, 3, 4))
            ev_a, ev_b, ms, fun = detect(o, h, l, c, SESS_BARS[fr])
            e = match_unit(ev_a, ts, u, win)
            f = {"bars": len(bb), "caught": e is not None, "funnel": fun}
            if e:
                f.update({"when": dt.datetime.fromtimestamp(ts[e["sig"]], tz=NY).strftime("%Y-%m-%d %H:%M"),
                          "L1": round(e["L1"], 4), "L2": round(e["L2"], 4), "N": round(e["N"], 4),
                          "gap_pct": round(abs(e["L2"] - e["L1"]) / e["B"] * 100, 2), "hammer": e["hammer"]})
            else:
                f["fail"] = diagnose(o, h, l, c, ts, u, win, SESS_BARS[fr])
            sw_b = [x for x in ev_b if win[0] <= ny_day(ts[x["sig"]]) <= win[1]]
            f["sweeps_in_win"] = [(dt.datetime.fromtimestamp(ts[x["sig"]], tz=NY).strftime("%m-%d %H:%M"), round(x["L1"], 4), x["depth"]) for x in sw_b][:5]
            row["frames"][fr] = f
        row["caught"] = any(f["caught"] for f in row["frames"].values())
        res.append(row)
        for fr, f in row["frames"].items():
            if f["caught"]:
                log(f"✅ {u['id']} {u['sym']} {fr}: مُلتقَطة — {f['when']} · L1 {f['L1']} · L2 {f['L2']} · العنق {f['N']} · فرق {f['gap_pct']}%")
            else:
                log(f"❌ {u['id']} {u['sym']} {fr}: لم تُلتقط — {f['fail']['item']} · {f['fail']['detail']}")
    n = sum(1 for r in res if r["caught"])
    log(f"🧾 القبول: {n} من 5 · شرطُ البناء 4 من 5 ⟵ {'يُستوفى' if n >= 4 else 'لا يُستوفى'}")
    os.makedirs(OUT, exist_ok=True)
    blob = {"mode": "accept", "contract_sha": CONTRACT_SHA, "caught": n, "units": res}
    with open(os.path.join(OUT, "accept.json"), "w", encoding="utf-8") as fh:
        json.dump(blob, fh, ensure_ascii=False, indent=1, default=str)
    log("WFOUT " + json.dumps(blob, ensure_ascii=False, default=str))
    return 0


# ── §③/§⑨ الجدوى ──────────────────────────────────────────────────────────────────────────
def _jdump(obj, path):
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, separators=(",", ":"))


def _jload(path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def mode_feas_prep(key):
    paths = sorted(glob.glob(os.path.join(OUT, "rb", "**", "*shard_*.json.gz"), recursive=True))
    fires = fires_from_shards(paths)
    sp = splits_rest(key, d0=BARS_FROM, d1=BARS_TO)
    prep = {"shard_files": len(paths), "fires": fires, "splits": sp,
            "sessions": RB.sessions_between(BARS_FROM, BARS_TO, MC)}
    os.makedirs(OUT, exist_ok=True)
    _jdump(prep, os.path.join(OUT, "prep.json.gz"))
    log(f"⓪ المجتمع: ملفّاتُ شرائح {len(paths)} · رموزٌ بانطلاق BASE2 {len(fires)} · أيّامُ انطلاق {sum(len(v) for v in fires.values())} · "
        f"تقسيماتٌ {sum(len(v) for v in sp.values())} لـ{len(sp)} رمزًا · جلسات {len(prep['sessions'])}")
    return 0 if paths and fires else 2


def read_minutes(path, want, day):
    """ملفُّ دقيقةِ يوم ⟵ {رمز: [[ts، o، h، l، c، v]]} للرموز المطلوبة وحدَها (الترشيحُ قبل التحويل)."""
    import csv
    out = {}
    with gzip.open(path, "rt") as fh:
        rd = csv.reader(fh)
        hd = [x.strip().lower() for x in next(rd)]
        it, io, ih, il, ic, iv, iw = (hd.index(x) for x in ("ticker", "open", "high", "low", "close", "volume", "window_start"))
        for r in rd:
            s = r[it]
            if s not in want:
                continue
            try:
                out.setdefault(s, []).append([int(r[iw]) // 1_000_000_000, float(r[io]), float(r[ih]), float(r[il]),
                                              float(r[ic]), float(r[iv])])
            except (ValueError, IndexError):
                continue
    for v in out.values():
        v.sort()
    return out


def mode_feas_shard(shard, nshards):
    import flatfiles_probe as FP
    import vwap_mom_feas as VF
    prep = _jload(os.path.join(OUT, "prep.json.gz"))
    pop = Pop(prep["fires"], prep["sessions"])
    days = prep["sessions"]
    per = -(-len(days) // nshards)
    mine = days[shard * per:(shard + 1) * per]
    store, missing, cov = {}, [], {"need": 0, "found": 0}
    tmp = tempfile.mkdtemp(prefix="wf_")
    t0 = time.time()
    for n, day in enumerate(mine):
        want = pop.needed(day)
        if not want:
            continue
        path = os.path.join(tmp, "d.csv.gz")
        ok, _ = VF._download(FP, VF._key(MIN_PREFIX, day), path)
        if not ok:
            missing.append(day)
            continue
        mins = read_minutes(path, want, day)
        os.remove(path)
        cov["need"] += len(want)
        cov["found"] += len(mins)
        for s, mm in mins.items():
            b = bars_30(mm)
            if not b:
                continue
            col = store.setdefault(s, [[], [], [], [], [], []])
            for x in b:
                for q in range(6):
                    col[q].append(x[q])
        if n % 10 == 0:
            log(f"shard {shard}: {n + 1}/{len(mine)} {day} · مطلوب {len(want)} · وُجد {len(mins)} · {round(time.time() - t0)}s")
    _jdump({"shard": shard, "days": mine, "missing": missing, "cov": cov, "syms": store}, os.path.join(OUT, f"bars_{shard:02d}.json.gz"))
    log(f"✅ shard {shard}: أيّام {len(mine)} · بلا ملفّ {len(missing)} {missing[:5]} · مطلوب {cov['need']} · وُجد {cov['found']} · رموز {len(store)}")
    return 0 if len(missing) < len(mine) else 2


def mode_feas_assemble():
    prep = _jload(os.path.join(OUT, "prep.json.gz"))
    pop = Pop(prep["fires"], prep["sessions"])
    sp = prep["splits"]
    cols, missing, cov = {}, [], {"need": 0, "found": 0}
    for p in sorted(glob.glob(os.path.join(OUT, "**", "bars_*.json.gz"), recursive=True)):
        sh = _jload(p)
        missing += sh["missing"]
        for k_ in cov:
            cov[k_] += sh["cov"][k_]
        for s, col in sh["syms"].items():
            cols.setdefault(s, []).append(col)
    eval_sess = [d for d in prep["sessions"] if EVAL_FROM <= d <= EVAL_TO]
    years = sorted({d[:4] for d in eval_sess})
    res = {}
    for fr in ("30m", "4h"):
        cell = {a: {"n": 0, "by_year": {y: 0 for y in years}, "syms": set(), "per_day": {}} for a in ("a", "b")}
        fun_tot, xs, outp, ms_in = {}, 0, {"a": 0, "b": 0}, 0
        for s, parts in cols.items():
            ts = [x for c_ in parts for x in c_[0]]
            if not ts:
                continue
            arr = [[x for c_ in parts for x in c_[q]] for q in range(6)]
            order = np.argsort(np.asarray(ts), kind="stable")
            b30 = [[arr[q][i] for q in range(6)] for i in order]
            bb = frame_bars(b30, fr)
            tsb = [b[0] for b in bb]
            ev_a, ev_b, ms, fun = detect([b[1] for b in bb], [b[2] for b in bb], [b[3] for b in bb], [b[4] for b in bb], SESS_BARS[fr])
            for k_, v in fun.items():
                fun_tot[k_] = fun_tot.get(k_, 0) + v
            for e in ms:
                d = ny_day(tsb[e["sig"]])
                if EVAL_FROM <= d <= EVAL_TO and pop.in_pop(s, d):
                    ms_in += 1
            for arm, evs in (("a", ev_a), ("b", ev_b)):
                for e in evs:
                    d = ny_day(tsb[e["sig"]])
                    if not (EVAL_FROM <= d <= EVAL_TO):
                        continue
                    if not pop.in_pop(s, d):
                        outp[arm] += 1
                        continue
                    if split_between(sp.get(s), ny_day(tsb[e["iP0"]]), d):
                        xs += 1
                        continue
                    c_ = cell[arm]
                    c_["n"] += 1
                    c_["by_year"][d[:4]] += 1
                    c_["syms"].add(s)
                    c_["per_day"][d] = c_["per_day"].get(d, 0) + 1
        res[fr] = {"funnel": fun_tot, "excluded_split": xs, "out_of_pop": outp, "M_in_pop": ms_in,
                   "cells": {a: {"n": v["n"], "per_session": round(v["n"] / len(eval_sess), 3), "by_year": v["by_year"],
                                 "unique_syms": len(v["syms"]), "max_day": max(v["per_day"].values(), default=0),
                                 "floor60": v["n"] >= 60} for a, v in cell.items()}}
        log(f"📊 {fr}: a {res[fr]['cells']['a']} · b {res[fr]['cells']['b']}")
        log(f"   القُمع: {fun_tot} · خارج المجتمع {outp} · مستبعَدٌ بتقسيم {xs} · M في المجتمع {ms_in}")
    blob = {"mode": "feas", "contract_sha": CONTRACT_SHA, "eval": [EVAL_FROM, EVAL_TO], "sessions": len(eval_sess),
            "symbols_with_bars": len(cols), "fire_symbols": len(prep["fires"]), "missing_days": sorted(set(missing)),
            "coverage": cov, "frames": res}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "feas.json"), "w", encoding="utf-8") as fh:
        json.dump(blob, fh, ensure_ascii=False, indent=1)
    log("WFOUT " + json.dumps(blob, ensure_ascii=False))
    return 0


# ── §⑤-§⑦ القياس بأمر «ابن W» (2026-10-31) · بتفصيل الملحق 1 ─────────────────────────────────────
ADDENDUM = os.path.join(HERE, "T_W_FAISAL_ADDENDUM_1.md")
ADDENDUM_SHA = "f246feaf86496180fd2094893a7450c9d642084b16a68fdbcc8ac350a94a3cea"   # بصمةُ الملحق 1 (WFA8) — عدمُ المطابقة ⟵ خروج 9 قبل أيّ شبكة
FEAS_N = {"30m|a": 27389, "30m|b": 33415, "4h|a": 12438, "4h|b": 13479}   # الملحق ③-1: الأحداثُ تُعاد وتُطابَق وإلّا خروج 5
FEAS_RC = 5
LEVELS = (1.5, 2.0)                 # §②-6 ‏+50% · ‏+100% من الدخول
S2_PCT = 0.05                       # §②-5 S2 «وقف -5٪» (TG_1978) · وصفيّ
CAND_CAP = 20                       # الملحق ③-7 · engineering
Q_BAND = 0.02                       # §⑥ C2 نقطتان مئويّتان
N_CTRL = 5                          # §⑥ C2 حتى خمسة
BOOT = 2000                         # §⑦
FLOOR = 60                          # §⑦ الأرضيّة
RUNGS = ((50.0, "50%"), (25.0, "25%"), (10.0, "10%"))   # الملحق ① (نصُّ المالك)
QSHARDS = 12
QUOTE_WORKERS = 16
END_4H = {240: 330, 330: 570, 570: 810, 810: 1050, 1050: 1200}
CELLS = ("30m|a", "30m|b", "4h|a", "4h|b")


def addendum_sha():
    with open(ADDENDUM, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def addendum_ok():
    return os.path.exists(ADDENDUM) and addendum_sha() == ADDENDUM_SHA


def rung(N, B):
    """الملحق ①: (العنق − القاع المزدوج) ÷ القاع ⟵ «10%» · «25%» · «50%» (أو None دون 10)."""
    h = (N - B) / B * 100.0
    for thr, name in RUNGS:
        if h >= thr - 1e-9:
            return name
    return None


def dkey(ts):
    """رقمُ يوم نيويورك (epoch-days) لشمعةٍ بين 04:00 و20:00 بتوقيت نيويورك — ثابتٌ صيفًا وشتاءً."""
    return (int(ts) - 18000) // 86400


def dkey_of_day(day):
    y, m, d = (int(x) for x in day.split("-"))
    return (dt.date(y, m, d) - dt.date(1970, 1, 1)).days


def day_of_dkey(k):
    return (dt.date(1970, 1, 1) + dt.timedelta(days=int(k))).isoformat()


_DS = {}


def bar_end(ts, frame):
    """نهايةُ الشمعة (ثوانٍ) — 30د: ‏+30 · 4س: الحدُّ التالي (§②-1)."""
    k = dkey(ts)
    if k not in _DS:
        _DS[k] = day_start_utc(day_of_dkey(k))
    ds = _DS[k]
    m = (int(ts) - ds) // 60
    return ds + 60 * (m + 30 if frame == "30m" else END_4H.get(m, m + 240))


def session_open_s(ts):
    k = dkey(ts)
    if k not in _DS:
        _DS[k] = day_start_utc(day_of_dkey(k))
    return _DS[k] + 240 * 60


def half_spread(bid, ask):
    """الملحق ③-7: bid موجبٌ و ask لا يقلّ عنه ⟵ (ask − bid) ÷ منتصفهما ÷ 2 · وإلّا None."""
    try:
        bid, ask = float(bid), float(ask)
    except (TypeError, ValueError):
        return None
    if not (bid > 0 and ask >= bid):
        return None
    return (ask - bid) / ((ask + bid) / 2.0) / 2.0


class Series:
    """سلسلةُ رمزٍ على فريم: ts · o · h · l · c · dk · وإغلاقُ آخر يومٍ سابق لكلّ شمعة."""

    def __init__(self, bars):
        a = np.asarray(bars, dtype=float) if len(bars) else np.zeros((0, 6))
        self.ts = a[:, 0].astype(np.int64)
        self.o, self.h, self.l, self.c = a[:, 1], a[:, 2], a[:, 3], a[:, 4]
        self.dk = (self.ts - 18000) // 86400
        n = len(self.ts)
        if n:
            chg = np.r_[True, self.dk[1:] != self.dk[:-1]]
            st = np.maximum.accumulate(np.where(chg, np.arange(n), 0))
            self.prev = np.where(st > 0, self.c[np.maximum(st - 1, 0)], np.nan)
            self.prev_dk = np.where(st > 0, self.dk[np.maximum(st - 1, 0)], -1)
        else:
            self.prev = np.zeros(0)
            self.prev_dk = np.zeros(0, dtype=np.int64)

    def day_slice(self, k):
        return int(np.searchsorted(self.dk, k, "left")), int(np.searchsorted(self.dk, k, "right"))


def split_factor(splits_sym, sig_dk, dks):
    """الملحق ③-6: شمعةٌ يومُها في تقسيمٍ (بعد يوم الإشارة) أو بعده ⟵ × to/from (مقياسُ الإشارة)."""
    f = np.ones(len(dks))
    hit = False
    for e, fr, to in splits_sym or ():
        ek = dkey_of_day(e)
        if ek > sig_dk and fr and to:
            m = dks >= ek
            if m.any():
                f[m] *= to / fr
                hit = True
    return f, hit


def q_of(S, i, splits_sym):
    """§⑥ C2: إغلاقُ الشمعة ÷ آخرِ إغلاقٍ في يومٍ سابق − 1 · وتقسيمٌ بينهما ⟵ None."""
    p = S.prev[i]
    if not (p == p and p > 0):
        return None
    d0, d1 = day_of_dkey(S.prev_dk[i]), day_of_dkey(S.dk[i])
    if split_between(splits_sym, d0, d1):
        return None
    return float(S.c[i] / p - 1.0)


def horizon_end(S, entry, sess_dk, sess_pos):
    """الملحق ③-4: آخرُ شمعةٍ في الجلسة العشرين بعد جلسة الدخول ⟵ (الفهرس · مقطوع؟)."""
    si = sess_pos.get(int(S.dk[entry]))
    if si is None:
        return None, True
    j = si + SPAN_SESS
    cut = j >= len(sess_dk)
    hk = sess_dk[min(j, len(sess_dk) - 1)]
    return int(np.searchsorted(S.dk, hk, "right")) - 1, cut


def trade_spec(S, sym, frame, sig, entry, stop_lvl, sess_dk, sess_pos, splits_sym, stop_pct=None):
    """الملحق ③-2…③-6: مواصفةُ صفقةٍ بلا اقتباس — الدخولُ · الوقفان (S1 · S2) · مرشّحو الهدفين — كلُّها بمقياس الإشارة.
    `stop_pct` (ضابطُ C2) ⟵ الوقفُ = الدخولُ × (1 − النسبة) بعد التسوية."""
    if entry >= len(S.ts):
        return None
    hend, cut = horizon_end(S, entry, sess_dk, sess_pos)
    if hend is None or hend < entry:
        return None
    sl = slice(entry, hend + 1)
    f, adj = split_factor(splits_sym, int(S.dk[sig]), S.dk[sl])
    cl = S.c[sl] * f
    op = float(S.o[entry] * f[0])
    if stop_pct is not None:
        stop_lvl = op * (1 - stop_pct)
    s2_lvl = stop_lvl * (1 - S2_PCT)
    b1 = np.nonzero(cl < stop_lvl)[0]
    b2 = np.nonzero(cl < s2_lvl)[0]
    sr = int(b1[0]) if len(b1) else None
    s2r = int(b2[0]) if len(b2) else None
    lim = len(cl) if s2r is None else s2r
    cands = {}
    for lv in LEVELS:
        idx = np.nonzero(cl[:lim] >= lv * op)[0]
        head = [[int(r), float(cl[r]), int(bar_end(S.ts[entry + r], frame))] for r in idx[:CAND_CAP]]
        rest = idx[CAND_CAP:]
        tail = None
        if len(rest):
            r1 = rest[rest < (sr if sr is not None else len(cl))]
            tail = [float(cl[r1].max()) if len(r1) else None, float(cl[rest].max())]
        cands[str(lv)] = {"head": head, "tail": tail}
    return {"sym": sym, "f": frame, "ets": int(S.ts[entry]), "eq": int(S.ts[entry]) + 60, "op": op, "stop": float(stop_lvl),
            "s2": float(s2_lvl), "sr": sr, "s2r": s2r, "n": int(len(cl)), "cut": bool(cut), "adj": bool(adj), "cands": cands}


def stop_of(l, e, arm):
    """الملحق ③-3 S1: (b) low شمعة السحب · وغيرُها أدنى low من L2 إلى شمعة الإشارة (لا شمعة الدخول)."""
    return float(l[e["sig"]]) if arm == "b" else float(np.min(l[e["i2"]:e["sig"] + 1]))


def c1_events(o, h, l, c, sess_bars, k=K, span_sess=SPAN_SESS):
    """§⑥ C1 بتفصيل الملحق ③-8: `faisal_tool.find_w` بالاسم عند تأكّد كلّ قاع · كلُّ W جديد ⟵ أوّلُ إغلاقٍ فوق عنقه خلال 20 جلسةً من L2.
    والسؤالُ بنافذة محاورٍ (‏W_BARS_MAX ‏+ k) — مطابقٌ للحساب الكامل بالبناء (الحرّاس WF22)."""
    o, h, l, c = (np.asarray(x, dtype=float) for x in (o, h, l, c))
    n = len(c)
    span = span_sess * sess_bars
    out, seen, last = [], set(), -1
    if n < 2 * k + 3:
        return out
    sw = FT.confirmed_swings(h, l, n - 1, k)
    si = [x[0] for x in sw]
    wmax = FT.P("W_BARS_MAX")
    for t in sorted({i + k for i, typ, _ in sw if typ == "L" and i + k <= n - 1}):
        a = bisect.bisect_left(si, t - k - wmax - 1)
        b = bisect.bisect_right(si, t - k)
        w = FT.find_w(o, h, l, c, t, k, sw=sw[a:b])
        if not w:
            continue
        key = (w["i1"], w["i2"])
        if key in seen:
            continue
        seen.add(key)
        if w["i2"] <= last:
            continue
        sig = next((x for x in range(w["confirmed_at"], min(n - 1, w["i2"] + span) + 1) if c[x] > w["neckline"]), None)
        if sig is None:
            continue
        out.append({"i1": w["i1"], "i2": w["i2"], "L1": w["low1"], "L2": w["low2"], "B": w["base"], "N": w["neckline"],
                    "iP0": max(0, w["i1"] - (w["i2"] - w["i1"])), "sig": int(sig)})
        last = sig
    return out


def pick_controls(cands, q, ordinal, seed=SEED):
    """§⑥ C2 بتفصيل الملحق ③-9: cands = [(رمز · فهرس · q)] بلا رمز الحدث ⟵ (المختار · تامٌّ في النطاق؟)."""
    cs = sorted(cands, key=lambda x: x[0])
    band = [x for x in cs if abs(x[2] - q) <= Q_BAND + 1e-12]
    if len(band) >= N_CTRL:
        rng = np.random.default_rng([seed, int(ordinal)])
        pick = sorted(rng.choice(len(band), N_CTRL, replace=False).tolist())
        return [band[i] for i in pick], True
    rest = sorted((x for x in cs if abs(x[2] - q) > Q_BAND + 1e-12), key=lambda x: (abs(x[2] - q), x[0]))
    return band + rest[:N_CTRL - len(band)], False


def reached(tr, hs_in, hs_of, level, stop_key, med):
    """الملحق ③-5: هل أُغلق ‏level × الدخولِ الفعليّ بعد كلفة الخروج قبل الوقف؟ ⟵ (0/1 · أُخذ من خارج السقف؟)."""
    eff = tr["op"] * (1 + hs_in)
    sr = tr[stop_key]
    c = tr["cands"][str(level)]
    for r, close, qk in c["head"]:
        if sr is not None and r >= sr:
            break
        hs = hs_of(tr["sym"], qk)
        if close * (1 - (med if hs is None else hs)) >= level * eff:
            return 1, False
    t = c.get("tail")
    if t:
        mx = t[0] if stop_key == "sr" else t[1]
        if mx is not None and mx * (1 - med) >= level * eff:
            return 1, True
    return 0, False


def boot_ci(groups, seed_key, kind):
    """§⑦ بتفصيل الملحق ③-10: بوتستراب عنقوديٌّ بالرمز · groups = {رمز: (مجموعُ أ · عددُ أ · مجموعُ ب · عددُ ب)} ⟵ (نقطة · أدنى · أعلى)."""
    syms = sorted(groups)
    if not syms:
        return None, np.zeros(0)
    A = np.array([groups[s] for s in syms], dtype=float)
    def stat(w):
        if kind == "paired":
            den = (w * A[:, 1]).sum()
            return (w * A[:, 0]).sum() / den if den else np.nan
        da, db = (w * A[:, 1]).sum(), (w * A[:, 3]).sum()
        if not da or not db:
            return np.nan
        return (w * A[:, 0]).sum() / da - (w * A[:, 2]).sum() / db
    pt = stat(np.ones(len(syms)))
    rng = np.random.default_rng([SEED] + list(seed_key))
    vals = []
    for _ in range(BOOT):
        w = np.bincount(rng.integers(0, len(syms), len(syms)), minlength=len(syms)).astype(float)
        vals.append(stat(w))
    vals = np.array([v for v in vals if v == v])
    return pt, vals


def ci_bounds(vals, m_tests):
    if vals is None or not len(vals):
        return float("nan"), float("nan")
    a = 0.05 / max(1, m_tests)
    return float(np.percentile(vals, 100 * a / 2)), float(np.percentile(vals, 100 * (1 - a / 2)))


def verdict(cells, frames=("30m", "4h")):
    """§⑦ بحرفه (الملحق ③-11): F4 ⟵ F3 ⟵ F2 ⟵ F1 · بالأضعف. cells = {خليّة: {n · c1 · c2 · c2_year · g100_c1 · g100_c2}}."""
    meas = {k: v for k, v in cells.items() if v["n"] >= FLOOR}
    if any(not any(k.startswith(f + "|") for k in meas) for f in frames):
        return "F4"
    if any(v["c2"][1] < 0 for v in meas.values()):
        return "F3"
    f1 = all(v["c1"][0] > 0 and v["c2"][0] > 0 and all((v["c2_year"].get(y) or 0) > 0 for y in ("2023", "2024", "2025"))
             and v["g100_c1"] >= 0 and v["g100_c2"] >= 0 for v in meas.values())
    return "F1" if f1 else "F2"


def _load_series(prep_path_glob):
    cols = {}
    for p in sorted(glob.glob(prep_path_glob, recursive=True)):
        sh = _jload(p)
        for s, col in sh["syms"].items():
            cols.setdefault(s, []).append(col)
    out = {}
    for s, parts in cols.items():
        ts = [x for c_ in parts for x in c_[0]]
        if not ts:
            continue
        arr = [[x for c_ in parts for x in c_[q]] for q in range(6)]
        order = np.argsort(np.asarray(ts), kind="stable")
        out[s] = [[arr[q][i] for q in range(6)] for i in order]
    return out


def mode_measure_prep():
    """§⑤ المرحلة 1: الأحداثُ (بالكاشف نفسِه · مطابقةُ الجدوى) ‏+ C1 ‏+ C2 ⟵ مواصفاتُ الصفقات وطلباتُ الاقتباس — **بلا أيّ عائد يُطبع**."""
    prep = _jload(os.path.join(OUT, "prep.json.gz"))
    pop = Pop(prep["fires"], prep["sessions"])
    sp = prep["splits"]
    sess = [d for d in prep["sessions"]]
    sess_dk = [dkey_of_day(d) for d in sess]
    sess_pos = {k: i for i, k in enumerate(sess_dk)}
    raw = _load_series(os.path.join(OUT, "**", "bars_*.json.gz"))
    log(f"📥 رموزٌ بشموع {len(raw)}")
    trades, cnt = [], {}

    def bump(k, v=1):
        cnt[k] = cnt.get(k, 0) + v

    for fr in ("30m", "4h"):
        ser, evs = {}, {"a": [], "b": [], "C1": []}
        for s, b30 in raw.items():
            bb = frame_bars(b30, fr)
            if not bb:
                continue
            S = Series(bb)
            ser[s] = S
            sw = None
            ev_a, ev_b, _ms, _f = detect(S.o, S.h, S.l, S.c, SESS_BARS[fr])
            for arm, lst in (("a", ev_a), ("b", ev_b), ("C1", c1_events(S.o, S.h, S.l, S.c, SESS_BARS[fr]))):
                for e in lst:
                    d = ny_day(S.ts[e["sig"]])
                    if not (EVAL_FROM <= d <= EVAL_TO) or not pop.in_pop(s, d):
                        continue
                    if split_between(sp.get(s), ny_day(S.ts[e["iP0"]]), d):
                        bump(f"{fr}|{arm}|split_excl")
                        continue
                    ent = dict(e, sym=s, day=d, stop=stop_of(S.l, e, arm), arm=arm)
                    if arm != "C1":
                        if sw is None:
                            sw = FT.confirmed_swings(S.h, S.l, len(S.c) - 1, K)
                            swi = [x[0] for x in sw]
                        ent["rung"] = rung(e["N"], e["B"])
                        ent["q"] = q_of(S, e["sig"], sp.get(s))
                        ent["qhold"] = bool(fr == "30m" and arm == "a" and S.l[e["sig"]] > e["N"])
                        ent["sw_cut"] = (bisect.bisect_right(swi, e["i2"]), swi, sw)
                    evs[arm].append(ent)
        for arm in ("a", "b"):
            n_in = len(evs[arm])
            log(f"🔁 {fr}|{arm}: أحداثٌ {n_in} (الجدوى {FEAS_N[fr + '|' + arm]})")
            if n_in != FEAS_N[fr + "|" + arm]:
                log(f"⛔ عددُ الأحداث لا يطابق الجدوى ⟵ خروج {FEAS_RC} بلا رقم (الملحق ③-1)")
                return FEAS_RC
        # C2: المرشّحون يومًا يومًا (§⑥ · الملحق ③-9)
        arm_evs = sorted(evs["a"] + evs["b"], key=lambda e: (e["day"], int(ser[e["sym"]].ts[e["sig"]]), e["sym"], e["arm"]))
        by_day = {}
        for e in arm_evs:
            by_day.setdefault(e["day"], []).append(e)
        syms_by_dk = {}
        for s, S in ser.items():
            for k_ in np.unique(S.dk):
                syms_by_dk.setdefault(int(k_), []).append(s)
        ordinal = 0
        for d, lst in sorted(by_day.items()):
            k_ = dkey_of_day(d)
            slot, qc = {}, {}
            for s in syms_by_dk.get(k_, []):
                if not pop.in_pop(s, d):
                    continue
                S = ser[s]
                a, b = S.day_slice(k_)
                for i in range(a, b):
                    slot.setdefault(int(S.ts[i]), []).append((s, i))
            for e in lst:
                ordinal += 1
                S = ser[e["sym"]]
                tsg = int(S.ts[e["sig"]])
                e["ord"] = ordinal
                if e["q"] is None:
                    e["ctrl"], e["full"] = [], False
                    bump(f"{fr}|q_none")
                    continue
                cands = []
                for s2, i2 in slot.get(tsg, []):
                    if s2 == e["sym"]:
                        continue
                    if (s2, i2) not in qc:
                        qc[(s2, i2)] = q_of(ser[s2], i2, sp.get(s2))
                    q2 = qc[(s2, i2)]
                    if q2 is not None:
                        cands.append((s2, i2, q2))
                e["ctrl"], e["full"] = pick_controls(cands, e["q"], ordinal)
        # مواصفاتُ الصفقات
        for arm in ("a", "b", "C1"):
            for e in evs[arm]:
                S = ser[e["sym"]]
                tr = trade_spec(S, e["sym"], fr, e["sig"], e["sig"] + 1, e["stop"], sess_dk, sess_pos, sp.get(e["sym"]))
                if tr is None:
                    bump(f"{fr}|{arm}|no_entry")
                    continue
                tr.update(arm=arm, year=e["day"][:4], day=e["day"])
                if arm != "C1":
                    pos, swi, sw = e["sw_cut"]
                    hend = e["sig"] + 1 + tr["n"] - 1
                    cut = bisect.bisect_right(swi, hend)
                    tr.update(rung=e["rung"], hammer=bool(e.get("hammer")), qhold=e["qhold"], full=e["full"], ord=e["ord"],
                              heads=int(FT.heads_since_low(sw[pos:cut], e["i2"])))
                    pct = (tr["op"] - tr["stop"]) / tr["op"] if tr["op"] else 0.0
                    ctr = []
                    for s2, i2, q2 in e["ctrl"]:
                        t2 = trade_spec(ser[s2], s2, fr, i2, i2 + 1, 0.0, sess_dk, sess_pos, sp.get(s2), stop_pct=pct)
                        if t2 is None:
                            bump(f"{fr}|ctrl_no_entry")
                            continue
                        t2.update(year=e["day"][:4])
                        ctr.append(t2)
                    tr["ctrl"] = ctr
                    if not ctr:
                        bump(f"{fr}|{arm}|no_ctrl")
                    if not e["full"] and ctr:
                        bump(f"{fr}|{arm}|ctrl_filled_nearest")
                trades.append(tr)
                bump(f"{fr}|{arm}|trades")
    # طلباتُ الاقتباس
    req = set()
    for tr in trades:
        for t in [tr] + tr.get("ctrl", []):
            req.add((t["sym"], t["eq"], session_open_s(t["ets"])))
            for lv in LEVELS:
                for r, _c, qk in t["cands"][str(lv)]["head"]:
                    req.add((t["sym"], qk, session_open_s(qk - 60)))
    req = sorted(req)
    os.makedirs(OUT, exist_ok=True)
    _jdump({"trades": trades, "cnt": cnt}, os.path.join(OUT, "trades.json.gz"))
    for i in range(QSHARDS):
        _jdump(req[i::QSHARDS], os.path.join(OUT, f"qreq_{i:02d}.json.gz"))
    n_ctrl = sum(len(t.get("ctrl", [])) for t in trades)
    log(f"📦 صفقات {len(trades)} · ضوابطُ C2 {n_ctrl} · طلباتُ اقتباسٍ فريدة {len(req)} · عدّادات {json.dumps(cnt, ensure_ascii=False, sort_keys=True)}")
    log("🔒 لا عائدَ في هذه المرحلة (الملحق ③-1).")
    return 0


_TLS = None


def _session():
    import threading
    import requests
    global _TLS
    if _TLS is None:
        _TLS = threading.local()
    if not hasattr(_TLS, "s"):
        _TLS.s = requests.Session()
    return _TLS.s


def fetch_quote(sym, lt_s, gte_s, key, tries=4):
    """الملحق ③-7: آخرُ اقتباسٍ قبل `lt_s` وليس قبل `gte_s` ⟵ (حالة · bid · ask)."""
    url = "https://api.polygon.io/v3/quotes"
    params = {"ticker": sym, "timestamp.lt": int(lt_s) * 1_000_000_000, "timestamp.gte": int(gte_s) * 1_000_000_000,
              "order": "desc", "sort": "timestamp", "limit": 1}
    for i in range(tries):
        try:
            r = _session().get(url, params=params, headers={"Authorization": f"Bearer {key}"}, timeout=30)
        except Exception:                                        # noqa: BLE001
            time.sleep(1 + i)
            continue
        if r.status_code == 200:
            res = (r.json() or {}).get("results") or []
            if not res:
                return ("empty", None, None)
            x = res[0]
            return ("ok", x.get("bid_price"), x.get("ask_price"))
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 * (2 ** i))
            continue
        return (f"http{r.status_code}", None, None)
    return ("failed", None, None)


def mode_measure_quotes(shard, key):
    import concurrent.futures as cf
    req = _jload(os.path.join(OUT, f"qreq_{shard:02d}.json.gz"))
    out, st, t0 = {}, {}, time.time()
    with cf.ThreadPoolExecutor(max_workers=QUOTE_WORKERS) as ex:
        futs = {ex.submit(fetch_quote, s, lt, gte, key): (s, lt) for s, lt, gte in req}
        for n, f in enumerate(cf.as_completed(futs), 1):
            s, lt = futs[f]
            try:
                stt, bid, ask = f.result()
            except Exception:                                    # noqa: BLE001
                stt, bid, ask = "failed", None, None
            st[stt] = st.get(stt, 0) + 1
            out[f"{s}|{lt}"] = [stt, bid, ask]
            if n % 20000 == 0:
                log(f"quotes {shard}: {n}/{len(req)} · {round(time.time() - t0)}s · {st}")
    _jdump(out, os.path.join(OUT, f"quotes_{shard:02d}.json.gz"))
    log(f"✅ quotes {shard}: {len(req)} طلبًا · {st} · {round(time.time() - t0)}s")
    return 0 if len(req) == 0 or st.get("ok", 0) > 0 else 2


def _clean(x):
    if isinstance(x, dict):
        return {str(k): _clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    if isinstance(x, (np.floating, float)):
        return None if x != x else float(x)
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def mode_measure_final():
    """§⑤-§⑦ المرحلة 3: الكلفةُ ⟵ G50/G100 ⟵ الفروقُ أمام C1 وC2 ⟵ البوتستراب ⟵ الحكمُ بالأضعف · والسلّمُ والوصفيُّ بجانبه."""
    blob = _jload(os.path.join(OUT, "trades.json.gz"))
    trades, cnt = blob["trades"], blob["cnt"]
    Q = {}
    for p in sorted(glob.glob(os.path.join(OUT, "**", "quotes_*.json.gz"), recursive=True)):
        Q.update(_jload(p))
    hs_cache = {k: (half_spread(v[1], v[2]) if v[0] == "ok" else None) for k, v in Q.items()}
    groups = {}
    for tr in trades:
        g = f"{tr['f']}|{tr['arm']}"
        groups.setdefault(g, []).append(tr)
        for c in tr.get("ctrl", []):
            groups.setdefault(f"{tr['f']}|C2", []).append(c)
    med, cov = {}, {}
    for g, lst in groups.items():
        vals, need = [], 0
        for t in lst:
            ks = [t["eq"]] + [qk for lv in LEVELS for _r, _c, qk in t["cands"][str(lv)]["head"]]
            for qk in ks:
                need += 1
                v = hs_cache.get(f"{t['sym']}|{qk}")
                if v is not None:
                    vals.append(v)
        med[g] = float(np.median(vals)) if vals else 0.0
        cov[g] = round(len(vals) / need, 4) if need else None

    beyond = {"n": 0}

    def outcome(t, g):
        hs_in = hs_cache.get(f"{t['sym']}|{t['eq']}")
        hs_in = med[g] if hs_in is None else hs_in
        def hs_of(sym, qk):
            return hs_cache.get(f"{sym}|{qk}")
        r = {}
        for lv, name in ((1.5, "g50"), (2.0, "g100")):
            r[name], bc = reached(t, hs_in, hs_of, lv, "sr", med[g])
            beyond["n"] += int(bc)
        r["g50s2"], _ = reached(t, hs_in, hs_of, 1.5, "s2r", med[g])
        return r

    res = {}
    for fr in ("30m", "4h"):
        c1 = [dict(t, **outcome(t, f"{fr}|C1")) for t in groups.get(f"{fr}|C1", [])]
        for arm in ("a", "b"):
            cell = f"{fr}|{arm}"
            ev = []
            for t in groups.get(cell, []):
                o = outcome(t, cell)
                cs = [outcome(c, f"{fr}|C2") for c in t.get("ctrl", [])]
                o["c2g50"] = float(np.mean([x["g50"] for x in cs])) if cs else None
                o["c2g100"] = float(np.mean([x["g100"] for x in cs])) if cs else None
                ev.append(dict(t, **o))
            n = len(ev)
            g50 = float(np.mean([e["g50"] for e in ev])) if ev else None
            g100 = float(np.mean([e["g100"] for e in ev])) if ev else None
            paired = [e for e in ev if e["c2g50"] is not None]
            grp2, grp1 = {}, {}
            for e in paired:
                x = grp2.setdefault(e["sym"], [0.0, 0])
                x[0] += e["g50"] - e["c2g50"]
                x[1] += 1
            for e in ev:
                x = grp1.setdefault(e["sym"], [0.0, 0, 0.0, 0])
                x[0] += e["g50"]
                x[1] += 1
            for t in c1:
                x = grp1.setdefault(t["sym"], [0.0, 0, 0.0, 0])
                x[2] += t["g50"]
                x[3] += 1
            ci = CELLS.index(cell)
            p2, v2 = boot_ci({s: (v[0], v[1], 0, 0) for s, v in grp2.items()}, (ci, 2), "paired")
            p1, v1 = boot_ci({s: tuple(v) for s, v in grp1.items()}, (ci, 1), "unpaired")
            yr = {}
            for y in ("2023", "2024", "2025"):
                py = [e["g50"] - e["c2g50"] for e in paired if e["year"] == y]
                yr[y] = float(np.mean(py)) if py else None
            c1g50 = float(np.mean([t["g50"] for t in c1])) if c1 else None
            c1g100 = float(np.mean([t["g100"] for t in c1])) if c1 else None
            g100_c2 = float(np.mean([e["g100"] - e["c2g100"] for e in paired])) if paired else None
            lad = {}
            for rn in ("10%", "25%", "50%"):
                sub = [e for e in ev if e.get("rung") == rn]
                sp2 = [e for e in sub if e["c2g50"] is not None]
                lad[rn] = {"n": len(sub), "g50": round(float(np.mean([e["g50"] for e in sub])), 4) if sub else None,
                           "g100": round(float(np.mean([e["g100"] for e in sub])), 4) if sub else None,
                           "c2_diff": round(float(np.mean([e["g50"] - e["c2g50"] for e in sp2])), 4) if sp2 else None}
            ham = [e for e in ev if e.get("hammer")]
            qh = [e for e in ev if e.get("qhold")]
            res[cell] = {"n": n, "syms": len({e["sym"] for e in ev}), "g50": g50, "g100": g100, "g50_s2": float(np.mean([e["g50s2"] for e in ev])) if ev else None,
                         "c1_n": len(c1), "c1_g50": c1g50, "c1_g100": c1g100, "c2_paired": len(paired),
                         "c2_g50": float(np.mean([e["c2g50"] for e in paired])) if paired else None,
                         "c1_pt": p1, "c2_pt": p2, "_v1": v1, "_v2": v2, "c2_year": yr,
                         "g100_c1": (g100 - c1g100) if (g100 is not None and c1g100 is not None) else None, "g100_c2": g100_c2,
                         "ladder": lad, "hammer": {"n": len(ham), "g50": float(np.mean([e["g50"] for e in ham])) if ham else None},
                         "qhold": {"n": len(qh), "g50": float(np.mean([e["g50"] for e in qh])) if qh else None},
                         "heads3": round(float(np.mean([e["heads"] >= 3 for e in ev])), 4) if ev else None,
                         "cov_arm": cov.get(cell), "cov_c2": cov.get(f"{fr}|C2"), "cov_c1": cov.get(f"{fr}|C1"),
                         "med_hs": med.get(cell), "cut": sum(e["cut"] for e in ev), "adj": sum(e["adj"] for e in ev),
                         "far": sum(1 for e in ev if not e.get("full"))}
    m = sum(1 for v in res.values() if v["n"] >= FLOOR) * 2
    for cell, v in res.items():
        v["c1"] = ci_bounds(v.pop("_v1"), m) if v.get("c1_pt") is not None else (float("nan"), float("nan"))
        v["c2"] = ci_bounds(v.pop("_v2"), m) if v.get("c2_pt") is not None else (float("nan"), float("nan"))
    vd = verdict({k: {"n": v["n"], "c1": v["c1"], "c2": v["c2"], "c2_year": v["c2_year"],
                      "g100_c1": v["g100_c1"] if v["g100_c1"] is not None else -1, "g100_c2": v["g100_c2"] if v["g100_c2"] is not None else -1}
                  for k, v in res.items()})
    pct = lambda x: "—" if x is None or x != x else f"{100 * x:.2f}%"
    pp = lambda x: "—" if x is None or x != x else f"{100 * x:+.2f}"
    for cell, v in res.items():
        flag = " ⚠️ مقيَّدٌ بالتغطية" if any((v[k] or 0) < 0.8 for k in ("cov_arm", "cov_c2", "cov_c1")) else ""
        log(f"📊 {cell}: n {v['n']} (رموز {v['syms']}) · G50 {pct(v['g50'])} · G100 {pct(v['g100'])} · "
            f"C1 n {v['c1_n']} G50 {pct(v['c1_g50'])} · C2 أزواج {v['c2_paired']} G50 {pct(v['c2_g50'])}{flag}")
        log(f"   الفرق أمام C1 {pp(v['c1_pt'])} نقطة [{pp(v['c1'][0])} · {pp(v['c1'][1])}] · أمام C2 {pp(v['c2_pt'])} [{pp(v['c2'][0])} · {pp(v['c2'][1])}] · "
            f"السنوات أمام C2 {{{', '.join(f'{y}: {pp(x)}' for y, x in v['c2_year'].items())}}} · G100 أمام C1 {pp(v['g100_c1'])} · أمام C2 {pp(v['g100_c2'])}")
        log(f"   🪜 السلّم (وصف): " + " · ".join(f"{rn}: n {x['n']} G50 {pct(x['g50'])} G100 {pct(x['g100'])} أمام C2 {pp(x['c2_diff'])}"
                                         for rn, x in v["ladder"].items()))
        log(f"   وصفيّ: S2 G50 {pct(v['g50_s2'])} · مطرقة n {v['hammer']['n']} G50 {pct(v['hammer']['g50'])} · ربعُ الساعة n {v['qhold']['n']} "
            f"G50 {pct(v['qhold']['g50'])} · 3 رؤوس {pct(v['heads3'])} · تغطيةُ الاقتباس ذراع {v['cov_arm']} · C2 {v['cov_c2']} · C1 {v['cov_c1']} · "
            f"وسيطُ نصف السبريد {v['med_hs']} · أفقٌ مقطوع {v['cut']} · مسوًّى بتقسيم {v['adj']} · ضوابطُ مكمَّلة بالأقرب {v['far']}")
    names = {"F1": "F1 «W فيصل يضيف»", "F2": "F2 «لا فرق»", "F3": "F3 «يضرّ»", "F4": "F4 «لا قياس»"}
    log(f"⚖️ الحكمُ بالأضعف (§⑦): {names[vd]} · بونفيروني على {m} · خارجُ السقف بوسيط الذراع {beyond['n']} · عدّاداتُ التحضير {json.dumps(cnt, ensure_ascii=False, sort_keys=True)}")
    out = {"mode": "measure", "contract_sha": CONTRACT_SHA, "addendum_sha": ADDENDUM_SHA, "verdict": vd, "bonferroni_m": m,
           "beyond_cap": beyond["n"], "cnt": cnt, "cells": res}
    _jd = _clean(out)
    with open(os.path.join(OUT, "measure.json"), "w", encoding="utf-8") as fh:
        json.dump(_jd, fh, ensure_ascii=False, indent=1)
    log("WFOUT " + json.dumps(_jd, ensure_ascii=False))
    return 0


# ── الحرّاس (بلا شبكة) ─────────────────────────────────────────────────────────────────────
def _synth_w(tail_close=6.5, l2=5.05, neck=6.0, p0=10.0, sweep=False, m_first=False, between_low=None, fast=False):
    """W اصطناعيّ (5 شموع/جلسة): هبوطٌ من P0 ⟵ L1 = 5.00 ⟵ العنق ⟵ L2 ⟵ اختراق — الإغلاقاتُ تُبنى والـlow = أدنى (الافتتاح · الإغلاق) − 0.01."""
    cl = list(np.linspace(p0, 5.6, 12)) + [5.3, 5.1, 5.01, 5.2, 5.5, neck - 0.05, neck - 0.01, neck - 0.1, neck - 0.2,
                                           (between_low + 0.01) if between_low else 5.4, neck - 0.3, neck - 0.25, 5.3, l2 + 0.1, l2 + 0.01]
    sweep_i = None
    if fast:
        cl += [6.5, 6.6, 6.7, 6.8]
        o = [cl[0]] + cl[:-1]
        return o, [max(a, b) + 0.01 for a, b in zip(o, cl)], [min(a, b) - 0.01 for a, b in zip(o, cl)], cl
    cl += [l2 + 0.15, l2 + 0.3]
    if m_first:
        cl += [4.8]
    if sweep:
        cl += [l2 + 0.2, 5.02]
        sweep_i = len(cl) - 1
        cl += [5.3]
    cl += [5.6, 5.8, tail_close, tail_close + 0.1, tail_close + 0.2]
    o = [cl[0]] + cl[:-1]
    h = [max(a, b) + 0.01 for a, b in zip(o, cl)]
    lo = [min(a, b) - 0.01 for a, b in zip(o, cl)]
    if sweep_i is not None:
        lo[sweep_i] = 4.95
    return o, h, lo, cl


def guards():
    fails = []

    def g(name, ok, det=""):
        log(("✅ " if ok else "❌ ") + name + (f" · {det}" if det and not ok else ""))
        if not ok:
            fails.append(name)

    # WF1 التجميع: 4س من الثلاثين = 4س من الدقائق مباشرةً (الحدودُ على أنصاف الساعات) بـ`chart_id_tv.aggregate`
    d0 = day_start_utc("2026-06-16")
    rng = np.random.default_rng(1)
    mins = []
    p = 2.5
    for m in range(240, 1200, 1):
        if rng.random() < 0.6:
            p *= 1 + rng.normal(0, 0.003)
            mins.append([d0 + m * 60, p, p * 1.002, p * 0.998, p * 1.0005, float(rng.integers(1, 900))])
    b30 = bars_30(mins)
    direct = CID.aggregate(mins, STARTS["4h"], END)
    via = bars_4h(b30)
    g("WF1 التجميع: 4س من شموع 30د = 4س من الدقائق مباشرةً · وبدايةُ أوّل شمعةٍ 04:00",
      len(via) == len(direct) and all(np.allclose(a, b) for a, b in zip(via, direct)) and (b30[0][0] - d0) // 60 == 240,
      f"{len(via)} {len(direct)}")
    # WF2 W نموذجيّ ⟵ حدثُ a بعد i2+k وعند أوّل إغلاقٍ فوق العنق
    o, h, l, c = _synth_w()
    ea, eb, ms, fun = detect(o, h, l, c, 5)
    first_above = next((t for t in range(len(c)) if ea and t > ea[0]["i2"] + K - 1 and c[t] > ea[0]["N"]), None)
    g("WF2 W نموذجيّ ⟵ حدثُ (a) واحدٌ عند أوّل إغلاقٍ فوق العنق بعد تأكّد L2",
      len(ea) == 1 and ea[0]["sig"] == first_above and abs(ea[0]["L1"] - 5.0) < 1e-9 and not ms, f"{ea} {fun}")
    # WF3 التسامح 3% حدًّا: 2.8% يُقبل و3.4% يُرفض
    ok_in = len(detect(*_synth_w(l2=5.14), 5)[0]) == 1
    ok_out = len(detect(*_synth_w(l2=5.17), 5)[0]) == 0
    g("WF3 التسامح: الثاني فوق الأوّل 2.8% ⟵ W · و3.4% ⟵ لا W (②التسامح)", ok_in and ok_out, f"{ok_in} {ok_out}")
    # WF4 العنقُ دون 10% ⟵ لا W
    g("WF4 العنقُ 10%: عنقٌ 5.45 (+7.9%) ⟵ لا W", len(detect(*_synth_w(neck=5.45, tail_close=5.9), 5)[0]) == 0)
    # WF5 الهبوطُ السابق: P0 تحت العنق ⟵ لا W
    g("WF5 الهبوطُ السابق: قمّةٌ قبل L1 تحت العنق ⟵ لا W", len(detect(*_synth_w(p0=5.9), 5)[0]) == 0)
    # WF6 R-W-SPAN: قاعٌ بين القاعين أدنى من أدناهما ⟵ لا W بذلك الزوج
    ea6 = detect(*_synth_w(between_low=4.8), 5)[0]
    g("WF6 R-W-SPAN: قاعٌ 4.80 بين القاعين ⟵ لا W على (5.00 · 5.05)", not any(abs(e["L1"] - 5.0) < 1e-9 and abs(e["L2"] - 5.05) < 1e-9 for e in ea6), str(ea6)[:80])
    # WF7 M: إغلاقٌ تحت B قبل الاختراق ⟵ M ولا a لذلك الـW
    ea7, eb7, ms7, fun7 = detect(*_synth_w(m_first=True), 5)
    g("WF7 M: إغلاقٌ تحت القاع المزدوج قبل الاختراق ⟵ M يُعدّ ولا (a) على L1=5.00",
      fun7["M"] >= 1 and not any(abs(e["L1"] - 5.0) < 1e-9 and abs(e["L2"] - 5.05) < 1e-9 for e in ea7), f"{fun7}")
    # WF8 السحب: low تحت B وإغلاقٌ فوقه قبل الاختراق ⟵ حدثُ b بعمقه
    ea8, eb8, ms8, fun8 = detect(*_synth_w(sweep=True), 5)
    g("WF8 السحب: low تحت القاع المزدوج وإغلاقٌ فوقه ⟵ حدثُ (b) قبل (a) بعمقه",
      len(eb8) == 1 and len(ea8) == 1 and eb8[0]["sig"] < ea8[0]["sig"] and eb8[0]["depth"] > 0, f"{eb8} {ea8}")
    # WF9 لا نظرَ للأمام: قطعُ الشموع بعد شمعة الإشارة لا يغيّر الحدث
    o, h, l, c = _synth_w()
    ea9 = detect(o, h, l, c, 5)[0]
    t = ea9[0]["sig"]
    cut = detect(o[:t + 1], h[:t + 1], l[:t + 1], c[:t + 1], 5)[0]
    g("WF9 لا نظرَ للأمام: الكشفُ على الشموع حتى شمعة الإشارة وحدَها يعطي الحدثَ نفسَه",
      len(cut) == 1 and cut[0]["sig"] == t and cut[0]["N"] == ea9[0]["N"], f"{cut}")
    # WF10 هويّةُ الترند: بعد iN الترندُ تحت N ⟵ «فوق العنق وتحت الترند» صفرٌ على مشيٍ عشوائيّ
    rng = np.random.default_rng(7)
    tb, tot = 0, 0
    for _ in range(30):
        cc = list(np.exp(np.cumsum(rng.normal(0, 0.03, 600))) * 3)
        oo = [cc[0]] + cc[:-1]
        hh = [max(a, b) * (1 + abs(rng.normal(0, 0.01))) for a, b in zip(oo, cc)]
        ll = [min(a, b) * (1 - abs(rng.normal(0, 0.01))) for a, b in zip(oo, cc)]
        _a, _b, _m, ff = detect(oo, hh, ll, cc, 32)
        tb += ff["trend_binding"]
        tot += ff["W"]
    g("WF10 هويّةُ الترند (§②-3): «إغلاقٌ فوق العنق وتحت الترند» صفرٌ على 30 مشيًا عشوائيًّا · وW وُجد",
      tb == 0 and tot > 0 and trend_at(10, 5, 6.0, 1, 9.0) < 6.0, f"tb={tb} W={tot}")
    # WF11 المجتمع: BASE2 في [D−20 · D−1] حصرًا · و«المطلوب» [اليوم−40 · اليوم+59]
    sess = [f"2023-{m:02d}-{d:02d}" for m in range(1, 7) for d in range(1, 29)]
    pp = Pop({"X": [sess[50]], "Y": [sess[29]]}, sess)
    g("WF11 المجتمع: انطلاقٌ في D−1 يُدخل وفي D نفسِه لا · وD−20 يُدخل وD−21 لا · والمطلوبُ [−40 · +59]",
      pp.in_pop("X", sess[51]) and not pp.in_pop("X", sess[50]) and pp.in_pop("X", sess[70]) and not pp.in_pop("X", sess[71])
      and "X" in pp.needed(sess[90]) and "X" not in pp.needed(sess[91]) and "X" in pp.needed(sess[0]) and "Y" not in pp.needed(sess[89])
      and "Z" in Pop({"Z": [sess[100]]}, sess).needed(sess[41]) and "Z" not in Pop({"Z": [sess[100]]}, sess).needed(sess[40]))
    # WF12 التقسيم: (P0 · الإشارة] يستبعد · وما قبل P0 أو بعد الإشارة لا
    sps = [("2023-03-10", 10.0, 1.0)]
    g("WF12 التقسيم: تنفيذٌ داخل (P0 · الإشارة] ⟵ استبعاد · ويومُ P0 نفسُه أو ما بعد الإشارة لا",
      split_between(sps, "2023-03-01", "2023-03-10") and not split_between(sps, "2023-03-10", "2023-03-20")
      and not split_between(sps, "2023-02-01", "2023-03-09"))
    # WF13 القبول: تسوية «حتى المرساة» — تقسيمٌ بعد اللقطة لا يُطبَّق · وقبلها يُطبَّق
    bb = [[day_start_utc("2026-06-10") + 600 * 60, 0.5, 0.5, 0.5, 0.5, 1000.0]]
    sc_after = asof_scale(bb, [("2026-07-01", 10.0, 1.0)], "2026-06-16")[0][4]
    sc_before = asof_scale(bb, [("2026-06-12", 10.0, 1.0)], "2026-06-16")[0][4]
    g("WF13 القبول: تقسيمٌ بعد المرساة لا يُطبَّق (0.5) · وقبلها يُطبَّق (×10 = 5.0)", sc_after == 0.5 and abs(sc_before - 5.0) < 1e-9)
    # WF14 «مُلتقَطة»: L1 ضمن ±3% من المرسوم وشمعةُ الإشارة داخل النافذة
    u = {"l1": 5.0}
    tsx = [day_start_utc("2026-06-15") + 600 * 60 + 1800 * i for i in range(10)]
    e_ok, e_far = {"sig": 3, "L1": 5.12}, {"sig": 3, "L1": 5.2}
    g("WF14 «مُلتقَطة»: L1 5.12 (+2.4%) داخل النافذة ⟵ نعم · و5.20 (+4%) ⟵ لا · وخارج النافذة ⟵ لا",
      match_unit([e_ok], tsx, u, ("2026-06-15", "2026-06-15")) is not None
      and match_unit([e_far], tsx, u, ("2026-06-15", "2026-06-15")) is None
      and match_unit([e_ok], tsx, u, ("2026-06-16", "2026-06-30")) is None)
    # WF15 لا نظرَ للأمام في L2: صعودٌ فوق العنق في الشمعة التالية مباشرةً ⟵ الإشارةُ لا تسبق تأكّد القاع (i2 + k)
    o15, h15, l15, c15 = _synth_w(fast=True)
    e15 = detect(o15, h15, l15, c15, 5)[0]
    g("WF15 L2 مؤكَّدٌ قبل الإشارة: إغلاقٌ فوق العنق بعد L2 بشمعة ⟵ الإشارةُ عند i2 + k لا قبلها",
      len(e15) == 1 and e15[0]["sig"] == e15[0]["i2"] + K, f"{e15}")
    # WF16 العنقُ «بين» القاعين حصرًا: ذيلٌ علويٌّ طويلٌ على شمعة L1 نفسِها لا يصير عنقًا
    o16, h16, l16, c16 = _synth_w()
    h16[14] = 6.5
    e16 = detect(o16, h16, l16, c16, 5)[0]
    g("WF16 العنقُ أعلى high بين القاعين حصرًا (ذيلُ شمعة L1 لا يُحسب)", len(e16) == 1 and abs(e16[0]["N"] - 6.0) < 1e-9, f"{e16}")
    # WF17 وسمُ المطرقة: ذيلٌ سفليٌّ ضعفا الجسم فأكثر ∧ علويٌّ لا يتجاوز الجسم
    g("WF17 المطرقة: (10 · 10.1 · 9 · 10.05) نعم · (10 · 10.1 · 9.95 · 10.05) لا (الذيلُ = الجسم) · (10 · 11 · 9 · 10.05) لا (علويٌّ طويل)",
      is_hammer(10, 10.1, 9, 10.05) and not is_hammer(10, 10.1, 9.95, 10.05) and not is_hammer(10, 11, 9, 10.05))
    # ── WF18-WF27 (‏«ابن W» · الملحق 1) ──────────────────────────────────────────────────────
    sessq = RB.sessions_between("2024-03-01", "2024-05-31", MC)

    def _bars(closes, opens=None, day0=0, per=32):
        out = []
        for j, cl in enumerate(closes):
            d, i = sessq[day0 + j // per], j % per
            op = (opens[j] if opens else (closes[j - 1] if j else cl))
            out.append([day_start_utc(d) + (240 + 30 * i) * 60, op, max(op, cl) + 0.001, min(op, cl) - 0.001, cl, 100.0])
        return out
    sdk = [dkey_of_day(d) for d in sessq]
    spos = {k_: i for i, k_ in enumerate(sdk)}
    # WF18 q: إغلاقٌ ÷ آخر إغلاقٍ في يومٍ سابق − 1 · وتقسيمٌ بينهما ⟵ None
    S18 = Series(_bars([1.0] * 32 + [1.1] * 32))
    q18 = q_of(S18, 40, None)
    q18x = q_of(S18, 40, [(sessq[1], 10.0, 1.0)])
    g("WF18 q: 1.10 ÷ 1.00 − 1 = 0.10 · وتقسيمٌ في يوم الشمعة ⟵ None", q18 is not None and abs(q18 - 0.1) < 1e-9 and q18x is None, f"{q18} {q18x}")
    # WF19 الهدف بعد الكلفة · الوقفُ أوّلًا · S2
    cl19 = [1.0] * 31 + [1.0, 1.2, 1.3, 1.6] + [1.6] * 40
    S19 = Series(_bars(cl19, opens=[1.0] * len(cl19)))
    tr = trade_spec(S19, "T", "30m", 31, 32, 0.9, sdk, spos, None)
    hs_lo = lambda s, qk: 0.01
    hs_hi = lambda s, qk: 0.06
    r_lo = reached(tr, 0.01, hs_lo, 1.5, "sr", 0.0)[0]
    r_hi = reached(dict(tr, cands={"1.5": {"head": tr["cands"]["1.5"]["head"][:1], "tail": None}, "2.0": tr["cands"]["2.0"]}), 0.01, hs_hi, 1.5, "sr", 0.0)[0]
    cl19b = [1.0] * 31 + [1.0, 0.88, 1.3, 1.6] + [1.6] * 40
    trb = trade_spec(Series(_bars(cl19b, opens=[1.0] * len(cl19b))), "T", "30m", 31, 32, 0.9, sdk, spos, None)
    s1 = reached(trb, 0.0, hs_lo, 1.5, "sr", 0.0)[0]
    s2 = reached(trb, 0.0, hs_lo, 1.5, "s2r", 0.0)[0]
    g("WF19 G50: 1.6 × 0.99 فوق 1.5 × 1.01 ⟵ 1 · وبنصف سبريد 6% ⟵ 0 · وإغلاقُ 0.88 تحت وقف 0.90 قبل الهدف ⟵ S1 صفر وS2 (0.855) واحد",
      r_lo == 1 and r_hi == 0 and s1 == 0 and s2 == 1, f"{r_lo} {r_hi} {s1} {s2}")
    # WF20 التقسيمُ داخل الأفق يُسوّى إلى مقياس الإشارة
    cl20 = [0.2] * 64 + [2.0] * 60
    S20 = Series(_bars(cl20, opens=cl20))
    t_raw = trade_spec(S20, "T", "30m", 31, 32, 0.18, sdk, spos, None)
    t_adj = trade_spec(S20, "T", "30m", 31, 32, 0.18, sdk, spos, [(sessq[2], 10.0, 1.0)])
    g("WF20 تقسيمٌ عكسيٌّ 1:10 يومَ القفزة بعد الإشارة: بلا تسويةٍ «+900%» زائف · وبالتسوية لا هدفَ ولا وقفَ ومُسوًّى",
      t_raw["cands"]["1.5"]["head"] and not t_adj["cands"]["1.5"]["head"] and t_adj["adj"] and not t_raw["adj"]
      and t_adj["sr"] is None and t_adj["s2r"] is None, f"{t_adj['cands']['1.5']} {t_adj['sr']}")
    # WF21 C2: خمسةٌ عشوائيّةٌ حتميّة من النطاق · وإلّا النطاقُ ‏+ الأقرب حتى خمسة
    c8 = [(f"S{i}", i, 0.10 + 0.002 * i) for i in range(8)] + [("FAR", 0, 0.5)]
    p1, f1 = pick_controls(c8, 0.11, 7)
    p2, _ = pick_controls(list(reversed(c8)), 0.11, 7)
    c3 = [("A", 0, 0.11), ("B", 0, 0.12), ("C", 0, 0.125), ("D", 0, 0.16), ("E", 0, 0.20), ("F", 0, 0.40)]
    p3, f3 = pick_controls(c3, 0.11, 7)
    var21 = len({tuple(x[0] for x in pick_controls(c8, 0.11, o_)[0]) for o_ in range(1, 11)})
    g("WF21 C2: ثمانيةٌ في النطاق ⟵ خمسةٌ منه بلا «FAR» وحتميّةٌ بأيّ ترتيب وتتبدّل برقم الحدث · وثلاثةٌ فقط ⟵ الثلاثة ‏+ الأقربُ D وE",
      f1 and len(p1) == 5 and p1 == p2 and all(x[0] != "FAR" for x in p1) and var21 > 1
      and not f3 and [x[0] for x in p3] == ["A", "B", "C", "D", "E"], f"{p1} {p3} var={var21}")
    # WF22 C1: سؤالُ find_w بنافذة المحاور = السؤالُ الكامل (أحداثٌ متطابقة على مساراتٍ عشوائيّة)
    ok22, det22, n22 = True, "", 0
    for sd in (3, 11, 29):
        r_ = np.random.default_rng(sd)
        cc = np.cumprod(1 + r_.normal(0, 0.03, 260)) * 5
        oo = np.r_[cc[0], cc[:-1]]
        hh = np.maximum(oo, cc) * (1 + np.abs(r_.normal(0, 0.01, 260)))
        ll = np.minimum(oo, cc) * (1 - np.abs(r_.normal(0, 0.01, 260)))
        fast = c1_events(oo, hh, ll, cc, 5, span_sess=6)
        swf = FT.confirmed_swings(hh, ll, 259, K)
        ref, seen, last = [], set(), -1
        for t in sorted({i + K for i, ty, _ in swf if ty == "L" and i + K <= 259}):
            w = FT.find_w(oo, hh, ll, cc, t, K)
            if not w or (w["i1"], w["i2"]) in seen:
                continue
            seen.add((w["i1"], w["i2"]))
            if w["i2"] <= last:
                continue
            sg = next((x for x in range(w["confirmed_at"], min(259, w["i2"] + 30) + 1) if cc[x] > w["neckline"]), None)
            if sg is not None:
                ref.append((w["i1"], w["i2"], sg))
                last = sg
        got = [(e["i1"], e["i2"], e["sig"]) for e in fast]
        n22 += len(ref)
        if got != ref:
            ok22, det22 = False, f"{sd}: {got[:3]} {ref[:3]}"
    g("WF22 C1: `find_w` بنافذة المحاور = الحسابُ الكامل على ثلاثة مساراتٍ عشوائيّة (الإشاراتُ نفسُها · وليست فارغة)", ok22 and n22 >= 3, f"{det22} n={n22}")
    # WF23 الحكم: F4 ⟵ F3 ⟵ F2 ⟵ F1
    good = {"n": 100, "c1": (0.01, 0.05), "c2": (0.01, 0.05), "c2_year": {"2023": 0.02, "2024": 0.02, "2025": 0.02}, "g100_c1": 0.0, "g100_c2": 0.01}
    cs_ = {c_: dict(good) for c_ in CELLS}
    v1 = verdict(cs_)
    v2 = verdict(dict(cs_, **{"4h|b": dict(good, c2=(-0.01, 0.03))}))
    v3 = verdict(dict(cs_, **{"4h|b": dict(good, c2=(-0.05, -0.01))}))
    v4 = verdict(dict(cs_, **{"30m|a": dict(good, c2=(-0.05, -0.01)), "4h|a": dict(good, n=59, c2=(-0.05, -0.01)), "4h|b": dict(good, n=10)}))
    v5 = verdict(dict(cs_, **{"30m|a": dict(good, c2_year={"2023": 0.02, "2024": -0.001, "2025": 0.02})}))
    v6 = verdict(dict(cs_, **{"30m|a": dict(good, g100_c1=-0.001)}))
    g("WF23 الحكم: الكلُّ فوق الصفر ⟵ F1 · فاصلٌ يضمّ الصفر ⟵ F2 · فاصلٌ تحت الصفر ⟵ F3 · فريمٌ بلا خليّةٍ مقيسة ⟵ F4 ولو مع F3 في الآخر · سنةٌ سالبة أو G100 سالب ⟵ F2",
      (v1, v2, v3, v4, v5, v6) == ("F1", "F2", "F3", "F4", "F2", "F2"), f"{(v1, v2, v3, v4, v5, v6)}")
    # WF24 البوتستراب: حتميّ · وفرقٌ ثابتٌ 0.1 ⟵ نقطةٌ وفاصلٌ عند 0.1
    gp = {f"S{i}": (0.1 * (i + 1), i + 1, 0, 0) for i in range(30)}
    pa, va = boot_ci(gp, (0, 2), "paired")
    pb, vb = boot_ci(gp, (0, 2), "paired")
    lo24, hi24 = ci_bounds(va, 8)
    gu = {f"S{i}": (i % 2, 1, (i + 1) % 2, 1) for i in range(40)}
    pu, vu = boot_ci(gu, (1, 1), "unpaired")
    g("WF24 البوتستراب: حتميٌّ بالبذرة · فرقٌ ثابت ⟵ (0.1 · 0.1 · 0.1) · وغيرُ المقترن عند الاتّزان ⟵ صفرٌ داخل الفاصل · وبونفيروني على 8 ⟵ الطرفان 0.3125% و99.6875%",
      np.array_equal(va, vb) and abs(pa - 0.1) < 1e-12 and abs(lo24 - 0.1) < 1e-9 and abs(hi24 - 0.1) < 1e-9
      and abs(pu) < 1e-12 and ci_bounds(vu, 8)[0] < 0 < ci_bounds(vu, 8)[1]
      and abs(ci_bounds(np.linspace(0, 1, 100001), 8)[0] - 0.003125) < 1e-6 and abs(ci_bounds(np.linspace(0, 1, 100001), 8)[1] - 0.996875) < 1e-6,
      f"{pa} {lo24} {hi24} {pu} {ci_bounds(np.linspace(0, 1, 100001), 8)}")
    # WF25 نصفُ السبريد
    g("WF25 نصفُ السبريد: (1.00 · 1.02) ⟵ 0.0099 · وbid صفر أو متقاطع أو نصٌّ ⟵ None",
      abs(half_spread(1.00, 1.02) - 0.02 / 1.01 / 2) < 1e-12 and half_spread(0, 1.0) is None and half_spread(1.02, 1.0) is None
      and half_spread("x", 1.0) is None)
    # WF26 يومُ نيويورك ونهايةُ الشمعة صيفًا وشتاءً
    okd = all(dkey(day_start_utc(d) + m * 60) == dkey_of_day(d) for d in ("2026-06-16", "2026-01-15", "2025-11-03", "2025-03-10") for m in (240, 1170, 1199))
    e30 = bar_end(day_start_utc("2026-01-15") + 1170 * 60, "30m") - day_start_utc("2026-01-15")
    e4h = bar_end(day_start_utc("2026-06-16") + 330 * 60, "4h") - day_start_utc("2026-06-16")
    e4l = bar_end(day_start_utc("2026-06-16") + 1050 * 60, "4h") - day_start_utc("2026-06-16")
    g("WF26 يومُ نيويورك من 04:00 إلى 19:59 صيفًا وشتاءً · ونهايةُ 19:30 ⟵ 20:00 · و4س 05:30 ⟵ 09:30 · و17:30 ⟵ 20:00",
      okd and e30 == 1200 * 60 and e4h == 570 * 60 and e4l == 1200 * 60, f"{okd} {e30} {e4h} {e4l}")
    # WF27 السلّم (الملحق ①)
    g("WF27 السلّم: 10% ⟵ «10%» · 24.99% ⟵ «10%» · 25% ⟵ «25%» · 49.99% ⟵ «25%» · 50% ⟵ «50%» · 9.99% ⟵ None",
      rung(1.10, 1.0) == "10%" and rung(1.2499, 1.0) == "10%" and rung(1.25, 1.0) == "25%" and rung(1.4999, 1.0) == "25%"
      and rung(1.5, 1.0) == "50%" and rung(1.0999, 1.0) is None)
    # WF28 الأفق: هدفٌ في الجلسة العشرين بعد جلسة الدخول يُحسب · وفي الحادية والعشرين لا
    def _h28(day_hit):
        cl_ = [1.0] * 32 * 30
        for j in range(32 * day_hit, 32 * day_hit + 32):
            cl_[j] = 1.7
        S_ = Series(_bars(cl_, opens=[1.0] * len(cl_)))
        t_ = trade_spec(S_, "T", "30m", 31, 32, 0.5, sdk, spos, None)
        return reached(t_, 0.0, lambda s_, q_: 0.0, 1.5, "sr", 0.0)[0]
    g("WF28 الأفق 20 جلسةً بعد جلسة الدخول: بلوغٌ في الجلسة 20 ⟵ 1 · وفي 21 ⟵ 0", _h28(21) == 1 and _h28(22) == 0, f"{_h28(21)} {_h28(22)}")
    # WF29 الوقف S1 بلا نظرٍ للأمام
    l29 = np.array([5.0, 4.0, 4.5, 4.4, 4.6, 3.0])
    g("WF29 S1: (a) أدنى low من L2 إلى الإشارة (4.4 لا 3.0 شمعةَ الدخول) · (b) low شمعة السحب",
      stop_of(l29, {"i2": 1, "sig": 4}, "a") == 4.0 and stop_of(l29, {"i2": 2, "sig": 4}, "a") == 4.4
      and stop_of(l29, {"i2": 2, "sig": 4}, "C1") == 4.4 and stop_of(l29, {"i2": 1, "sig": 3}, "b") == 4.4)
    # WF30 وقفُ ضابط C2 بنسبة مسافة وقف الحدث من دخوله هو
    S30 = Series(_bars([2.0] * 64, opens=[2.0] * 64))
    t30 = trade_spec(S30, "T", "30m", 31, 32, 0.0, sdk, spos, None, stop_pct=0.1)
    g("WF30 C2: نسبةُ 10% ⟵ وقفُ الضابط 1.80 من دخوله 2.00 · وS2 = 1.71", abs(t30["stop"] - 1.8) < 1e-12 and abs(t30["s2"] - 1.71) < 1e-12,
      f"{t30['stop']} {t30['s2']}")
    # WF31 السلسلةُ كاملةً على بياناتٍ مصغّرة في مجلّدٍ مؤقّت: عددٌ لا يطابق ⟵ 5 بلا ملفّ · ومطابق ⟵ 0 ثمّ الحكم
    out0, feas0 = OUT, dict(FEAS_N)
    tmp31 = tempfile.mkdtemp(prefix="wf31_")
    ok31, det31 = False, ""
    try:
        globals()["OUT"] = tmp31
        sess31 = RB.sessions_between("2022-12-01", "2023-03-31", MC)
        r31 = np.random.default_rng(31)
        st31 = {}
        for s_ in ("AA", "BB", "CC", "DD", "EE", "FF"):
            col = [[], [], [], [], [], []]
            px = 2.0
            for d_ in sess31:
                for i in range(32):
                    op_ = px
                    px = max(0.05, px * (1 + r31.normal(0, 0.03)))
                    for q_, v_ in enumerate([day_start_utc(d_) + (240 + 30 * i) * 60, op_, max(op_, px) * 1.004, min(op_, px) * 0.996, px, 100.0]):
                        col[q_].append(v_)
            st31[s_] = col
        fires31 = {s_: [d_ for d_ in sess31 if "2023-01-03" <= d_ <= "2023-02-28"][::2] for s_ in st31}
        _jdump({"shard_files": 1, "fires": fires31, "splits": {}, "sessions": RB.sessions_between(BARS_FROM, BARS_TO, MC)},
               os.path.join(tmp31, "prep.json.gz"))
        _jdump({"shard": 0, "days": sess31, "missing": [], "cov": {"need": 1, "found": 1}, "syms": st31}, os.path.join(tmp31, "bars_00.json.gz"))
        import contextlib as _cl
        import io as _io
        import re as _re
        rc_bad = None
        for _ in range(5):
            buf = _io.StringIO()
            with _cl.redirect_stdout(buf):
                rc_ = mode_measure_prep()
            if rc_bad is None:
                rc_bad = (rc_, os.path.exists(os.path.join(tmp31, "trades.json.gz")))
            for m_ in _re.finditer(r"🔁 (\S+): أحداثٌ (\d+)", buf.getvalue()):
                FEAS_N[m_.group(1)] = int(m_.group(2))
            if rc_ == 0:
                break
        for p_ in glob.glob(os.path.join(tmp31, "qreq_*.json.gz")):
            _jdump({f"{a_}|{b_}": ["ok", 1.0, 1.01] for a_, b_, _c in _jload(p_)}, p_.replace("qreq_", "quotes_"))
        buf = _io.StringIO()
        with _cl.redirect_stdout(buf):
            rc_f = mode_measure_final()
        mj = json.load(open(os.path.join(tmp31, "measure.json"), encoding="utf-8"))
        nt = sum(v["n"] for v in mj["cells"].values())
        ok31 = rc_bad == (FEAS_RC, False) and rc_ == 0 and rc_f == 0 and mj["verdict"] in ("F1", "F2", "F3", "F4") and nt > 0 \
            and mj["addendum_sha"] == ADDENDUM_SHA and "WFOUT" in buf.getvalue()
        det31 = f"{rc_bad} {rc_} {rc_f} {mj['verdict']} n={nt}"
    except Exception as ex_:                                     # noqa: BLE001
        det31 = f"{type(ex_).__name__}: {ex_}"
    finally:
        globals()["OUT"] = out0
        FEAS_N.clear()
        FEAS_N.update(feas0)
        import shutil as _sh
        _sh.rmtree(tmp31, ignore_errors=True)
    g("WF31 السلسلة مصغّرةً: عددُ أحداثٍ لا يطابق ⟵ خروج 5 بلا ملفّ صفقات · ومطابقٌ ⟵ تحضيرٌ 0 ثمّ حكمٌ 0 ببصمة الملحق", ok31, det31)
    log(f"🧾 الحرّاس: {31 - len(fails)} من 31" + (f" · ساقط: {fails}" if fails else ""))
    return 0 if not fails else 1


def main():
    if "--guards" in sys.argv:
        return guards()
    if not contract_ok():
        log(f"⛔ بصمةُ العقد لا تطابق `CONTRACT_SHA` ⟵ لا رقمَ قبل العقد (خروج {SHA_RC})")
        return SHA_RC
    mode = (os.environ.get("W_MODE") or "").strip()
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    log(f"📝 T-W-FAISAL · {mode} · العقد {CONTRACT_SHA[:12]} · التسامح {TOL} · العنق {NECK_MIN} · k {K}")
    if mode == "feas_assemble":
        return mode_feas_assemble()
    if mode.startswith("measure"):
        if not addendum_ok():
            log(f"⛔ بصمةُ الملحق 1 لا تطابق `ADDENDUM_SHA` ⟵ لا عائدَ قبل الملحق (خروج {SHA_RC})")
            return SHA_RC
        if mode == "measure_prep":
            return mode_measure_prep()
        if mode == "measure_final":
            return mode_measure_final()
    if not key:
        log("⛔ POLYGON_API_KEY مطلوب")
        return 2
    if mode == "accept":
        return mode_accept(key)
    if mode == "feas_prep":
        return mode_feas_prep(key)
    if mode == "feas_shard":
        return mode_feas_shard(int(os.environ["SHARD"]), int(os.environ["NSHARDS"]))
    if mode == "measure_quotes":
        return mode_measure_quotes(int(os.environ["SHARD"]), key)
    log(f"⛔ وضعٌ مجهول: {mode!r}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
