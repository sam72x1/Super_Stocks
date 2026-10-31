# -*- coding: utf-8 -*-
"""📝 `T-W-FAISAL` — نموذجُ W / القاعُ المزدوج بتعريف فيصل على 30 دقيقة و4 ساعات (العقد `T_W_FAISAL_prereg.md` · 2026-10-31).

**قياسٌ فقط · لا تلغرام · لا كرون · لا إنتاج · ولا شيفرةَ نتيجةٍ في هذا الإصدار** (العقد §⑤: القياسُ بأمر «ابن W» بعد القبول).
الأوضاع (`W_MODE`):
    accept          §⑧ القبولُ على وحدات فيصل الخمس (Polygon REST دقيقة · خامّ مسوًّى حتى اللقطة)
    feas_prep       §③ المجتمعُ من صفوف شرائح الجزء ب (BASE2) ‏+ تقسيماتُ الفترة ⟵ out/prep.json.gz
    feas_shard      §③ ملفّاتُ الدقيقة (SHARD · NSHARDS) ⟵ شموعُ 30د للرموز المطلوبة ⟵ out/bars_NN.json.gz
    feas_assemble   §⑨ جدوى العدّ: الأحداثُ لكلّ خليّة · القُمعُ · التغطية — بلا عائد
    --guards        حرّاسٌ اصطناعيّة بلا شبكة (WF1-WF17)
والبصمةُ `CONTRACT_SHA` تُفحص قبل أيّ شبكة ⟵ عدمُ المطابقة خروج 9.
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
    log(f"🧾 الحرّاس: {17 - len(fails)} من 17" + (f" · ساقط: {fails}" if fails else ""))
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
    if not key:
        log("⛔ POLYGON_API_KEY مطلوب")
        return 2
    if mode == "accept":
        return mode_accept(key)
    if mode == "feas_prep":
        return mode_feas_prep(key)
    if mode == "feas_shard":
        return mode_feas_shard(int(os.environ["SHARD"]), int(os.environ["NSHARDS"]))
    log(f"⛔ وضعٌ مجهول: {mode!r}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
