#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🕵️⏳ `T-PRELINK` — «التنبيه اليوم والانفجار بعد أيام»: ما الذي يميّز تنبيه «هنا الدخول» الذي ينفجر
**لاحقًا**؟ وهل يمكن التمركزُ بين التنبيه والانفجار؟ (العقد `prelink_prereg.md` — مدفوعٌ **قبل أيّ رقم**).

المجتمع: **A** مراسي git الحيّة (`tierlink_probe.anchor_history` بالاسم) · **C** صفوفُ `kasih_rows_{year}.jsonl`
2023-2025 (بالمشطوبين · `V-P6` بت-بت) · الشاهدان `CM` (مطابقُ الزخم بلا مرساة) و`CR` (عشوائيّ).
النتيجةُ الحاكمة `late100_10`: أقصى `high` في الجلسات 1-10 بعد يوم 0 ÷ إغلاقُ يوم 0 − 1 ≥ +100% (العقد §①-4) —
**مسوّاةٌ بالتقسيم** عبر `chart_finder.split_factor` بالاسم على شموع grouped الخام (`adjusted=false`).

🔒 **قراءةٌ/قياسٌ فقط**: لا تلغرام · لا كتابةَ حالة · لا `LOGIC_VERSION` · ولا عتبةَ تتحرّك. الكتابةُ الوحيدة صفوفُ
`prelink_rows_*.jsonl` (artifact) داخل `_dump_rows` وحدَها (`_selfcheck_readonly` يقفلها بالـAST).
الخروج: 0 قياس · 2 بلا مفتاح · 3 تغطيةٌ ناقصة/حارسٌ ساقط · 4 صفرُ مراسٍ · 5 ليست قراءةً فقط.
"""
import ast
import bisect
import collections
import datetime as dt
import json
import math
import os
import random
import statistics
import subprocess
import sys
import time

import numpy as np
import pandas as pd
import requests

import Super_stock as S                                              # noqa: E402
from tierlink_probe import anchor_history, measure, daily_range       # بالاسم (A)
from tier_fwd_report import fetch_day, load_ledger                    # بالاسم (شموعُ دقائق يوم المرساة)
from kasih_scan import NY, wilson, PRICE_LO, PRICE_HI                 # بالاسم
from link100_probe import year_days, z_bonf                           # بالاسم (تقويمٌ · بونفيروني)
import chart_finder as CF                                             # load_all_splits · split_factor بالاسم

API = "https://api.polygon.io"
SINCE = os.environ.get("PRELINK_SINCE") or "2026-08-17"
UNTIL = (os.environ.get("PRELINK_UNTIL") or "").strip()
MAX_ANCHORS = int(os.environ.get("PRELINK_MAX") or "0")
YEARS = [y.strip() for y in (os.environ.get("PRELINK_YEARS") if os.environ.get("PRELINK_YEARS") is not None
                             else "2023,2024,2025").split(",") if y.strip()]
KASIH_DIR = os.environ.get("PRELINK_KASIH_DIR") or "kasih_rows"
TRADES_ON = (os.environ.get("PRELINK_TRADES") or "1").strip() == "1"     # §④-4 (⓪-ب) — «الغ فتح المحاور» ⟵ 0
SEED = 20260925
HORIZONS = (5, 10, 20)
H_GOV = 10                     # الأفقُ الحاكم (العقد §①-4)
LATE_PCT = 100.0               # «انفجارٌ متأخّر» = +100%
SAME_PCT = 50.0                # `same_day` = +50% من سعر الكرت في يومه (T-OPLINK بالاسم)
MIN_N_A, MIN_N_C = 20, 50      # العقد §⑤-3
MIN_HALF = 10
MIN_COVER = 0.80               # V-P4
GROUPED_FROM, GROUPED_TO = "2022-11-01", "2026-02-15"
PX_KEEP = 30.0                 # نحتفظ بصفوف grouped ذات إغلاقٍ ≤ 30$ (الكونُ ≤ 10$ والشاهدُ بخانته)
COST = 0.01                    # انزلاقٌ 1% للطرف (engineering · العقد §⑥)
STOP_BELOW = 0.02              # الوقفُ تحت أدنى يوم 0 بـ2%
POS_DAYS = 10
CADENCE = 0.12
ROWS_PREFIX = "prelink_rows_"
ID_FROM, ID_TO, ID_K50, ID_K100 = "2026-08-18", "2026-09-01", 33, 14   # V-P1 (T-OPLINK/T-TIERLINK)
KASIH_COUNTS = {"2023": 10851, "2024": 14312, "2025": 19037}            # V-P6 (kasih_result.md)
_CALLS = collections.Counter()


def log(msg=""):
    print(msg, flush=True)


# ─────────────────────────── الحارسُ الذاتيّ (V-P5) ───────────────────────────
def _selfcheck_readonly(src=None) -> bool:
    """قراءةٌ فقط بالـAST: صفرُ إرسال/كتابةِ حالة · وكتابةُ الملفّات **داخل `_dump_rows` وحدَها**."""
    try:
        src = src if src is not None else open(__file__, encoding="utf-8").read()
        tree = ast.parse(src)
    except Exception:                                                # noqa: BLE001
        return False
    banned = {"send_telegram", "git_save", "save_watchlist", "save_op_entry_state",
              "record_new_alerts", "save_near_watch", "save_hunter_watch"}
    parents = {}
    for n in ast.walk(tree):
        for ch in ast.iter_child_nodes(n):
            parents[ch] = n
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        fn = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
        if fn in banned:
            return False
        if fn == "open":
            mode = ""
            if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                mode = str(n.args[1].value)
            for kw in n.keywords or []:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = str(kw.value.value)
            if any(c in mode for c in ("w", "a", "x", "+")):
                p = n
                while p in parents and not isinstance(p, ast.FunctionDef):
                    p = parents[p]
                if not (isinstance(p, ast.FunctionDef) and p.name == "_dump_rows"):
                    return False
    return True


def _dump_rows(path, rows):
    """الكتابةُ الوحيدة المسموحة: صفوفُ artifact (لا حالةَ إنتاج)."""
    if not str(os.path.basename(path)).startswith(ROWS_PREFIX):
        return 0
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    return len(rows)


# ─────────────────────────── الجلب ───────────────────────────
def _get(url, params, key, tries=4, timeout=60):
    last = ""
    for i in range(tries):
        try:
            r = requests.get(url, params=dict(params or {}), headers={"Authorization": f"Bearer {key}"},
                             timeout=timeout)
            _CALLS["http"] += 1
            if r.status_code == 200:
                time.sleep(CADENCE)
                return r.json()
            last = f"HTTP {r.status_code}"
            if r.status_code in (401, 403, 404):
                break
        except Exception as e:                                       # noqa: BLE001
            last = type(e).__name__
        time.sleep(2 * (2 ** i))
    _CALLS["fail"] += 1
    _CALLS[f"fail:{last}"] += 1                                      # سببُ الإخفاق يُعَدّ لا يُطوى
    return None


def grouped_day(day, key, get=None):
    """السوقُ كلُّه ليومٍ واحد خامًا ⟵ {رمز: (o,h,l,c,v)} — نسخةٌ محلّيّة مكافئة لـ`link100_probe.grouped_day`."""
    js = (get or _get)(f"{API}/v2/aggs/grouped/locale/us/market/stocks/{day}", {"adjusted": "false"}, key)
    if not js:
        return None
    out = {}
    for b in js.get("results") or []:
        try:
            s = str(b.get("T") or "").strip().upper()
            o, h, lo, c, v = float(b["o"]), float(b["h"]), float(b["l"]), float(b["c"]), float(b.get("v") or 0.0)
        except (TypeError, ValueError, KeyError):
            continue
        if s and c > 0 and h > 0 and lo > 0:
            out[s] = (o, h, lo, c, v)
    return out or None


def ticker_daily_adj(sym, d0, d1, key):
    """شموعٌ يوميّة `adjusted=true` (مسارُ A المرجعيّ لـ`V-P8` — كما `T-OPLINK`)."""
    js = _get(f"{API}/v2/aggs/ticker/{sym}/range/1/day/{d0}/{d1}", {"adjusted": "true", "sort": "asc",
                                                                       "limit": "5000"}, key)
    out = []
    for b in (js or {}).get("results") or []:
        d = dt.datetime.fromtimestamp(b["t"] / 1000, tz=NY).date().isoformat()
        out.append((d, float(b["o"]), float(b["h"]), float(b["l"]), float(b["c"]), float(b.get("v") or 0)))
    return out


# ─────────────────────────── سلاسلُ الأيّام (grouped ⟶ لكلّ رمز) ───────────────────────────
class Series:
    """لكلّ رمز: `idx` (فهرسُ يوم التداول العامّ) وأعمدةُ o/h/l/c/v — مصفوفاتٌ مضغوطة."""

    def __init__(self):
        self.tmp = collections.defaultdict(lambda: ([], [], [], [], [], []))
        self.arr = {}

    def add(self, sym, i, o, h, lo, c, v):
        t = self.tmp[sym]
        t[0].append(i); t[1].append(o); t[2].append(h); t[3].append(lo); t[4].append(c); t[5].append(v)

    def freeze(self):
        for s, t in self.tmp.items():
            self.arr[s] = (np.asarray(t[0], dtype=np.int32), np.asarray(t[1]), np.asarray(t[2]),
                           np.asarray(t[3]), np.asarray(t[4]), np.asarray(t[5]))
        self.tmp = None

    def pos(self, sym, i):
        """موضعُ يوم التداول `i` في مصفوفات الرمز — أو None إن لم يتداول ذلك اليوم."""
        a = self.arr.get(sym)
        if a is None:
            return None
        k = bisect.bisect_left(a[0].tolist(), i) if len(a[0]) < 64 else int(np.searchsorted(a[0], i))
        if k < len(a[0]) and int(a[0][k]) == i:
            return k
        return None


def build_series(days, key, syms_keep=None, get=None):
    """يجلب grouped لكلّ يومٍ في `days` ويبني السلاسل (إغلاقٌ ≤ `PX_KEEP`) · يُرجع (Series, أيّامٌ مجلوبة, ناقصة)."""
    ser, got, miss = Series(), [], []
    for i, day in enumerate(days):
        g = grouped_day(day, key, get=get)
        if g is None:
            miss.append(day)
            continue
        got.append(day)
        for s, (o, h, lo, c, v) in g.items():
            if c <= PX_KEEP or (syms_keep and s in syms_keep):
                ser.add(s, i, o, h, lo, c, v)
        if (i + 1) % 100 == 0:
            log(f"   … grouped {i + 1}/{len(days)} يومًا · رموزٌ {len(ser.tmp):,}")
    ser.freeze()
    return ser, got, miss


def adj_window(ser, sym, i0, splits, back=60, fwd=20, days=None):
    """شموعُ [i0−back, i0+fwd] **مسوّاةً بالتقسيم** إلى يوم النهاية (`split_factor` بالاسم) ⟵ قاموسُ مصفوفات
    + موضعُ يوم 0 + علمُ `split_in_win` (تقسيمٌ داخل [يوم0−1, يوم0+fwd])."""
    a = ser.arr.get(sym)
    if a is None:
        return None
    idx = a[0]
    lo_i, hi_i = i0 - back, i0 + fwd
    k0 = int(np.searchsorted(idx, lo_i))
    k1 = int(np.searchsorted(idx, hi_i, side="right"))
    if k1 <= k0:
        return None
    sub_idx = idx[k0:k1]
    p0 = int(np.searchsorted(sub_idx, i0))
    if p0 >= len(sub_idx) or int(sub_idx[p0]) != i0:
        return None
    end_day = days[min(hi_i, len(days) - 1)]
    fac = np.ones(len(sub_idx))
    sp = splits.get(sym) or []
    if sp:
        for j, gi in enumerate(sub_idx):
            fac[j] = CF.split_factor(sp, days[int(gi)], end_day)
    d0 = days[i0]
    dm1 = days[max(0, i0 - 1)]
    win_split = any(dm1 <= ex <= end_day for ex, _f, _t in sp)
    return {"idx": sub_idx, "o": a[1][k0:k1] * fac, "h": a[2][k0:k1] * fac, "l": a[3][k0:k1] * fac,
            "c": a[4][k0:k1] * fac, "v": a[5][k0:k1] / fac, "p0": p0, "fac0": float(fac[p0]),
            "split_in_win": bool(win_split), "day0": d0}


# ─────────────────────────── النتائج (العقد §①) ───────────────────────────
def outcomes(w, entry_raw, last_gidx, horizons=HORIZONS, late_pct=LATE_PCT, same_pct=SAME_PCT):
    """يومُ 0 = `w['p0']` · الحاكمُ `late100_10` من `close0` · الأفقُ مكتملٌ إن كان `i0+h ≤ last_gidx`."""
    p0 = w["p0"]
    i0 = int(w["idx"][p0])
    c0, l0, h0 = float(w["c"][p0]), float(w["l"][p0]), float(w["h"][p0])
    if c0 <= 0:
        return None
    entry_adj = (entry_raw * w["fac0"]) if entry_raw else None
    same_day = (h0 / entry_adj - 1) * 100 >= same_pct if entry_adj else None
    out = {"close0": c0, "low0": l0, "high0": h0, "entry_adj": entry_adj, "same_day": same_day,
           "split_in_win": w["split_in_win"], "open1": None}
    after_h = w["h"][p0 + 1:]
    after_l = w["l"][p0 + 1:]
    after_c = w["c"][p0 + 1:]
    after_o = w["o"][p0 + 1:]
    after_i = w["idx"][p0 + 1:]
    if len(after_o):
        out["open1"] = float(after_o[0])
    for h in horizons:
        complete = (i0 + h) <= last_gidx
        rows_h = int(np.searchsorted(after_i, i0 + h, side="right"))   # صفوفٌ حتى يوم i0+h
        if not complete:
            out[f"late100_{h}"] = out[f"late50_{h}"] = None
            out[f"mg_{h}"] = None
            continue
        if rows_h == 0:
            mg = -100.0                                             # شُطب/توقّف: لا قمّةَ بعد يوم 0
        else:
            mg = (float(after_h[:rows_h].max()) / c0 - 1) * 100
        out[f"mg_{h}"] = mg
        out[f"late100_{h}"] = mg >= late_pct
        out[f"late50_{h}"] = mg >= 50.0
        out[f"truncated_{h}"] = rows_h < h
    # تفاصيلُ المتأخّر (الأفقُ 20 إن اكتمل وإلّا 10)
    hh = 20 if out.get("late100_20") is not None else (10 if out.get("late100_10") is not None else None)
    if hh:
        rows_h = int(np.searchsorted(after_i, i0 + hh, side="right"))
        if rows_h:
            seg_h, seg_l, seg_c = after_h[:rows_h], after_l[:rows_h], after_c[:rows_h]
            pk = int(np.argmax(seg_h))
            out["days_to_peak"] = int(after_i[pk]) - i0
            out["mdd_before_peak"] = (float(seg_l[:pk + 1].min()) / c0 - 1) * 100
            out["held_low0_to_peak"] = bool((seg_c[:pk] > l0).all()) if pk > 0 else True
    out["cls"] = "same_day" if same_day else ("late" if out.get("late50_10") else ("none" if out.get("late50_10") is False else "؟"))
    return out


# ─────────────────────────── الميزات (العقد §④) ───────────────────────────
def _b(x, edges, labels):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    for e, lab in zip(edges, labels):
        if x < e:
            return lab
    return labels[-1]


def features(w, splits_sym, prior_anchor_gidx=None, days=None):
    """العائلاتُ 1 · 2 · 6 · 7 (من الشموع اليوميّة ≤ يوم 0 · وما قبل المرساة ≤ يوم 0 − 1) — نِسَبٌ وسلال."""
    p0 = w["p0"]
    i0 = int(w["idx"][p0])
    o, h, lo, c, v = (w[k] for k in ("o", "h", "l", "c", "v"))
    pre_h, pre_l, pre_c, pre_v = h[:p0], lo[:p0], c[:p0], v[:p0]
    f, raw = {}, {}
    # ── 1) شمعةُ يوم 0
    rng0 = float(h[p0] - lo[p0])
    close_pos0 = (float(c[p0] - lo[p0]) / rng0) if rng0 > 0 else None
    entry_adj = w.get("entry_adj")
    retreat0 = (float(c[p0]) / entry_adj - 1) * 100 if entry_adj else None
    wick_up0 = (float(h[p0] - max(o[p0], c[p0])) / float(h[p0]) * 100) if h[p0] > 0 else None
    med20 = float(np.median(pre_v[-20:])) if len(pre_v) >= 20 else None
    vol_x0 = (float(v[p0]) / med20) if med20 and med20 > 0 else None
    usd0 = float(c[p0] * v[p0])
    prev_c = float(pre_c[-1]) if len(pre_c) else None
    ret0 = (float(c[p0]) / prev_c - 1) * 100 if prev_c else None
    raw.update(close_pos0=close_pos0, retreat0=retreat0, wick_up0=wick_up0, vol_x0=vol_x0, usd0=usd0, ret0=ret0,
               px0=float(c[p0]))
    f["close_pos0"] = _b(close_pos0, (0.3, 0.7), ("<0.3", "0.3-0.7", "≥0.7"))
    f["retreat0"] = _b(retreat0, (-10, 0), ("<−10%", "−10..0", ">0"))
    f["wick_up0"] = _b(wick_up0, (5, 15), ("<5%", "5-15", "≥15"))
    f["vol_x0"] = _b(vol_x0, (3, 10), ("<3", "3-10", "≥10"))
    f["usd0"] = _b(usd0, (300_000, 1_000_000), ("<300k", "300k-1M", "≥1M"))
    f["above_low0"] = None if w.get("anchor_low_adj") is None else ("نعم" if float(c[p0]) > w["anchor_low_adj"] else "لا")
    f["ret0"] = _b(ret0, (20, 50), ("<+20%", "20-50", "≥50"))
    f["px0"] = _b(float(c[p0]), (1, 3, 10), ("<1$", "1-3", "3-10", ">10"))
    # ── 2) ما قبل المرساة (≤ يوم 0 − 1)
    if len(pre_c) >= 21:
        h20, l20 = float(pre_h[-20:].max()), float(pre_l[-20:].min())
        range20 = (h20 / l20 - 1) * 100 if l20 > 0 else None
        rs = S.rsi(pd.Series(pre_c.astype(float)))
        rsi14 = float(rs.iloc[-1]) if len(rs) >= 15 else None
        rsi_slope5 = float(rs.iloc[-1] - rs.iloc[-6]) if len(rs) >= 21 else None
        vol_dry = (float(pre_v[-5:].mean()) / float(pre_v[-20:].mean())) if pre_v[-20:].mean() > 0 else None
        vx_prev = (float(pre_v[-1]) / float(np.median(pre_v[-20:-5]))) if len(pre_v) >= 21 and np.median(pre_v[-20:-5]) > 0 else None
        ret5_prev = (float(pre_c[-1]) / float(pre_c[-6]) - 1) * 100 if len(pre_c) >= 6 and pre_c[-6] > 0 else None
        l60 = float(pre_l[-60:].min())
        dist_low60 = (float(pre_c[-1]) / l60 - 1) * 100 if l60 > 0 else None
        sweeps = 0
        for j in range(max(10, len(pre_c) - 20), len(pre_c)):
            prev_low10 = float(pre_l[j - 10:j].min())
            if pre_l[j] < prev_low10 and pre_c[j] > prev_low10:
                sweeps += 1
        fails = 0
        for j in range(max(1, len(pre_c) - 60), len(pre_c)):
            if pre_c[j - 1] > 0 and pre_h[j] / pre_c[j - 1] - 1 >= 0.30 and pre_c[j] / pre_c[j - 1] - 1 < 0.10:
                fails += 1
        prior_expl = 0
        for j in range(max(1, len(pre_c) - 60), len(pre_c)):
            if pre_c[j - 1] > 0 and pre_h[j] / pre_c[j - 1] - 1 >= 0.50:
                prior_expl += 1
        raw.update(range20=range20, rsi14=rsi14, rsi_slope5=rsi_slope5, vol_dry=vol_dry, vol_x_prev=vx_prev,
                   ret5_prev=ret5_prev, dist_low60=dist_low60, sweeps20=sweeps, failed_pumps60=fails, prior_expl60=prior_expl)
        f["range20"] = _b(range20, (40, 120), ("<40%", "40-120", "≥120"))
        f["rsi14"] = _b(rsi14, (30, 40, 55), ("<30", "30-40", "40-55", "≥55"))
        f["rsi_slope5"] = _b(rsi_slope5, (-5, 5), ("<−5", "±5", ">+5"))
        f["vol_dry"] = _b(vol_dry, (0.5, 1.5), ("<0.5", "0.5-1.5", "≥1.5"))
        f["vol_x_prev"] = _b(vx_prev, (3,), ("<3", "≥3"))
        f["ret5_prev"] = _b(ret5_prev, (20,), ("≤+20%", ">+20%"))
        f["dist_low60"] = _b(dist_low60, (10, 30), ("<10%", "10-30", "≥30"))
        f["sweeps20"] = _b(sweeps, (1, 3), ("0", "1-2", "≥3"))
        f["failed_pumps60"] = _b(fails, (1, 2), ("0", "1", "≥2"))
        f["prior_expl60"] = _b(prior_expl, (1, 2), ("0", "1", "≥2"))
    # ── 6) البنية (التقسيمات من قائمة السوق)
    d0 = w["day0"]
    rev = [ex for ex, fr, to in (splits_sym or []) if ex <= d0 and fr > to]
    rd = (dt.date.fromisoformat(d0) - dt.date.fromisoformat(max(rev))).days if rev else None
    r365 = sum(1 for ex in rev if (dt.date.fromisoformat(d0) - dt.date.fromisoformat(ex)).days <= 365)
    raw.update(rsplit_days=rd, rsplit_count365=r365)
    f["rsplit_days"] = "لا" if rd is None else _b(rd, (31, 121), ("≤30", "31-120", ">120"))
    f["rsplit_count365"] = _b(r365, (1, 2), ("0", "1", "≥2"))
    # ── 7) تاريخُ الرمز مع المضارب (مراسٍ سابقة في 60 جلسة)
    if prior_anchor_gidx is not None:
        pa = [g for g in prior_anchor_gidx if i0 - 60 <= g < i0]
        n_pa = len(pa)
        dsa = (i0 - max(pa)) if pa else None
        raw.update(prior_anchors60=n_pa, days_since_anchor=dsa)
        f["prior_anchors60"] = _b(n_pa, (1, 2), ("0", "1", "≥2"))
        f["days_since_anchor"] = "لا" if dsa is None else _b(dsa, (6, 21), ("≤5", "6-20", ">20"))
    return f, raw


def cohort_k(w, k, last_gidx, late_pct=LATE_PCT):
    """الفوجُ k (العقد §①-8): لم يبلغ +50% من `close0` في 1..k · ميزاتُ الهدوء ≤ k · النتيجةُ من `close_k` على k+1..k+10."""
    p0 = w["p0"]
    i0 = int(w["idx"][p0])
    idx = w["idx"]
    if (i0 + k + POS_DAYS) > last_gidx:
        return None
    pk = p0 + k
    if pk >= len(idx) or int(idx[pk]) != i0 + k:
        return {"in": False, "why": "شموعٌ ناقصة في 1..k"}
    c0, l0 = float(w["c"][p0]), float(w["l"][p0])
    seg_h = w["h"][p0 + 1:pk + 1]
    if float(seg_h.max()) / c0 - 1 >= 0.50:
        return {"in": False, "why": "انفجر قبل k"}
    seg_c, seg_l, seg_v = w["c"][p0 + 1:pk + 1], w["l"][p0 + 1:pk + 1], w["v"][p0 + 1:pk + 1]
    held = bool((seg_c > l0).all())
    inside = 0
    for j in range(p0 + 1, pk + 1):
        if w["h"][j] <= w["h"][j - 1] and w["l"][j] >= w["l"][j - 1]:
            inside += 1
    vdry = (float(seg_v.mean()) / float(w["v"][p0])) if w["v"][p0] > 0 else None
    ck = float(w["c"][pk])
    after_h = w["h"][pk + 1:]
    after_i = idx[pk + 1:]
    rows_h = int(np.searchsorted(after_i, i0 + k + POS_DAYS, side="right"))
    mg = (float(after_h[:rows_h].max()) / ck - 1) * 100 if rows_h else -100.0
    return {"in": True, "held_low0_k": "نعم" if held else "لا", "inside_k": str(inside),
            "vol_dry_k": _b(vdry, (0.3, 1.0), ("<0.3", "0.3-1", "≥1")),
            "close_k_vs_0": _b((ck / c0 - 1) * 100, (-15, 0), ("<−15%", "−15..0", ">0")),
            "late100_k": mg >= late_pct, "mg_k": mg, "close_k": ck, "low_k": float(min(l0, seg_l.min()))}


# ─────────────────────────── الشواهد (العقد §③) ───────────────────────────
def day_pool(ser, i0, med_cache):
    """مرشّحو الشاهد ليوم i0: كلُّ رمزٍ له شمعةُ يوم 0 وشمعةُ الأمس و20 حجمًا قبلها ⟵ (sym, px_prev, ret0, vol_x0)."""
    pool = []
    for sym, a in ser.arr.items():
        idx = a[0]
        k = int(np.searchsorted(idx, i0))
        if k >= len(idx) or int(idx[k]) != i0 or k < 21 or int(idx[k - 1]) != i0 - 1:
            continue
        pc = float(a[4][k - 1])
        if pc <= 0:
            continue
        key = (sym, k)
        med = med_cache.get(key)
        if med is None:
            med = float(np.median(a[5][k - 20:k]))
            med_cache[key] = med
        if med <= 0:
            continue
        pool.append((sym, pc, (float(a[4][k]) / pc - 1) * 100, float(a[5][k]) / med))
    return pool


def pick_controls(pool, anchor_syms_20, px_prev, ret0, vol_x0, rng):
    """`CM`: خانةُ السعر نفسُها · بلا مرساةٍ في 20 جلسة · أقربُ (ret0, vol_x0) بفرقٍ نسبيّ ≤ 50% · `CR`: عشوائيّ من الكون."""
    def bucket(p):
        return _b(p, (1, 3, 10), ("<1", "1-3", "3-10", ">10"))
    b = bucket(px_prev)
    cands = [(s, r, vx) for (s, pc, r, vx) in pool if s not in anchor_syms_20 and bucket(pc) == b]
    best, best_d = None, None
    if ret0 is not None and vol_x0 is not None:
        for s, r, vx in cands:
            dr = abs(r - ret0) / max(1.0, abs(ret0))
            dv = abs(vx - vol_x0) / max(1.0, abs(vol_x0))
            if dr <= 0.5 and dv <= 0.5:
                d = dr + dv
                if best_d is None or d < best_d or (d == best_d and s < best):
                    best, best_d = s, d
    uni = [s for (s, pc, _r, _vx) in pool if PRICE_LO <= pc <= PRICE_HI and s not in anchor_syms_20]
    cr = rng.choice(uni) if uni else None
    return best, cr


# ─────────────────────────── الحكم (العقد §⑤) ───────────────────────────
def rate(rows, key):
    xs = [r["o"][key] for r in rows if r["o"].get(key) is not None]
    return (sum(1 for x in xs if x), len(xs))


def judge_feat(rows, getf, best, key="late100_10", min_n=MIN_N_A, z=1.96):
    """الشرطان 1-2 (+3): السلّةُ المُعلَنة «الأعلى» مقابل مُكمِّلها بالمقياس `key`."""
    top = [r for r in rows if getf(r) == best and r["o"].get(key) is not None]
    rest = [r for r in rows if getf(r) not in (None, best) and r["o"].get(key) is not None]
    tn, tk = len(top), sum(1 for r in top if r["o"][key])
    rn, rk = len(rest), sum(1 for r in rest if r["o"][key])
    if tn < min_n or rn < min_n:
        return {"n": (tn, rn), "k": (tk, rk), "c3": False, "c1": None, "c2": None, "why": f"لا حكم (n={tn}/{rn} دون {min_n})"}
    pt, pr = tk / tn, rk / rn
    tlo, thi = wilson(tk, tn, z)
    rlo, rhi = wilson(rk, rn, z)
    c1 = (pt >= 2 * pr) if pr > 0 else (tk > 0)
    c2 = tlo > rhi
    return {"n": (tn, rn), "k": (tk, rk), "p": (pt * 100, pr * 100), "ci": ((tlo, thi), (rlo, rhi)),
            "c1": c1, "c2": c2, "c3": True, "why": ("فصل" if (c1 and c2) else "لا فصل")}


def mh_ratio(rows, getf, best, key="late100_10", min_n=20):
    """الشرط 5: نسبةُ Mantel-Haenszel داخل طبقات (ret0 × vol_x0) — وكلُّ طبقةٍ بـn ≥ min_n نسبتُها ≥ 1.5."""
    strata = collections.defaultdict(lambda: [0, 0, 0, 0])            # a, n1, b, n2
    for r in rows:
        if r["o"].get(key) is None:
            continue
        g = getf(r)
        if g is None:
            continue
        st = (r["f"].get("ret0"), r["f"].get("vol_x0"))
        if None in st:
            continue
        cell = strata[st]
        if g == best:
            cell[0] += int(bool(r["o"][key])); cell[1] += 1
        else:
            cell[2] += int(bool(r["o"][key])); cell[3] += 1
    num = den = 0.0
    per, ok_each = {}, True
    for st, (a, n1, b, n2) in strata.items():
        N = n1 + n2
        if n1 == 0 or n2 == 0:
            continue
        num += a * n2 / N
        den += b * n1 / N
        if n1 >= min_n and n2 >= min_n:
            r1, r2 = a / n1, b / n2
            ratio = (r1 / r2) if r2 > 0 else (float("inf") if r1 > 0 else 1.0)
            per[st] = (n1, n2, ratio)
            if ratio < 1.5:
                ok_each = False
    rr = (num / den) if den > 0 else (float("inf") if num > 0 else None)
    return rr, per, (ok_each and rr is not None and rr >= 2.0 and len(per) > 0)


def fmt(v):
    return "—" if v is None else (f"{v:.1f}" if isinstance(v, float) else str(v))


# ─────────────────────────── سياساتُ التمركز (العقد §⑥) ───────────────────────────
def simulate(w, entry_p, stop, target, start_pos, n_days=POS_DAYS, cost=COST):
    """دخولٌ عند `entry_p` (إغلاقُ يوم البدء) · وقفٌ ثابت · هدفٌ أو وقتٌ — R بعد التكلفة (الوقفُ أوّلًا عند التعارض)."""
    e = entry_p * (1 + cost)
    risk = e - stop * (1 - cost)
    if risk <= 0:
        return None
    o, h, lo, c = w["o"], w["h"], w["l"], w["c"]
    end = min(len(c) - 1, start_pos + n_days)
    for j in range(start_pos + 1, end + 1):
        if o[j] <= stop:
            return (o[j] * (1 - cost) - e) / risk
        if lo[j] <= stop:
            return (stop * (1 - cost) - e) / risk
        if h[j] >= target:
            return (target * (1 - cost) - e) / risk
    if end <= start_pos:
        return None
    return (c[end] * (1 - cost) - e) / risk


def boot_ci(xs, n=1000, seed=SEED):
    if not xs:
        return (None, None)
    rng = random.Random(seed)
    ms = []
    for _ in range(n):
        smp = [xs[rng.randrange(len(xs))] for _ in range(len(xs))]
        ms.append(sum(smp) / len(smp))
    ms.sort()
    return (ms[int(0.025 * n)], ms[int(0.975 * n) - 1])


# ─────────────────────────── المجتمعات ───────────────────────────
def load_kasih(year):
    path = os.path.join(KASIH_DIR, f"kasih_rows_{year}.jsonl")
    if not os.path.exists(path):
        alt = f"kasih_rows_{year}.jsonl"
        path = alt if os.path.exists(alt) else path
    rows = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    except OSError:
        return None
    return rows


def day0_of(day, hhmm, days, didx):
    """يومُ 0: يومُ المرساة إن كانت قبل 16:00 نيويورك وإلّا الجلسةُ التالية (العقد §①-2)."""
    if day not in didx:
        nxt = bisect.bisect_left(days, day)
        if nxt >= len(days):
            return None, True
        return days[nxt], True
    i = didx[day]
    if hhmm >= "16:00":
        return (days[i + 1] if i + 1 < len(days) else None), True
    return day, False


def anchors_A(key, until):
    """مراسي A من git (بالاسم) + `same_day` بـ`measure` (شاهدُ الهُويّة V-P1) + سعرُ الكرت `e5`."""
    anchors = {k: v for k, v in anchor_history(since=SINCE).items() if k[0] <= until}
    keys = sorted(anchors)
    if MAX_ANCHORS:
        keys = keys[:MAX_ANCHORS]
    ledger = {(r["date"], r["symbol"]): r for r in load_ledger()}
    out, fails = [], 0
    for n, (day, sym) in enumerate(keys, 1):
        a = anchors[(day, sym)]
        bars = fetch_day(sym, day, key) or []
        _CALLS["minute"] += 1
        if not bars:
            fails += 1
            continue
        dl = daily_range(sym, day, key)
        _CALLS["daily_range"] += 1
        b = ledger.get((day, sym))
        o = measure(a, b, bars, dl)
        if o is None:
            fails += 1
            continue
        t = dt.datetime.fromtimestamp(int(a["anchor_ms"]) / 1000, tz=NY)
        out.append({"sym": sym, "day": day, "hhmm": t.strftime("%H:%M"), "entry": float(o["e5"]),
                    "anchor_low": a.get("anchor_low") or (b or {}).get("anchor_low"),
                    "same_day": bool(o["exploded50"]), "exploded100": bool(o["exploded100"]),
                    "mg_day": o.get("mg_day"), "close_ret": o.get("close_ret"), "tod": ("pre" if t.hour < 9.5 else ("reg" if t.hour < 16 else "after"))})
        if n % 50 == 0:
            log(f"   … A {n}/{len(keys)}")
    return out, len(keys), fails


# ─────────────────────────── الطبقةُ الحاكمة: صفٌّ لكلّ مرساة ───────────────────────────
def build_rows(anch, ser, days, didx, splits, last_gidx, anchors_by_sym, label):
    rows, nobase, incomplete = [], 0, 0
    med_cache, pools, near_cache = {}, {}, {}
    rng = random.Random(SEED)
    for a in anch:
        d0, after = day0_of(a["day"], a["hhmm"], days, didx)
        if d0 is None or d0 not in didx:
            nobase += 1
            continue
        i0 = didx[d0]
        w = adj_window(ser, a["sym"], i0, splits, days=days)
        if w is None:
            nobase += 1
            continue
        alow = a.get("anchor_low")
        w["anchor_low_adj"] = (float(alow) * w["fac0"]) if alow else None
        w["entry_adj"] = float(a["entry"]) * w["fac0"] if a.get("entry") else None
        o = outcomes(w, a.get("entry"), last_gidx)
        if o is None:
            nobase += 1
            continue
        if a.get("same_day") is not None:
            o["same_day"] = bool(a["same_day"])                     # A: بالاسم من measure (V-P1)
            o["cls"] = "same_day" if o["same_day"] else ("late" if o.get("late50_10") else ("none" if o.get("late50_10") is False else "؟"))
        if o.get(f"late100_{H_GOV}") is None:
            incomplete += 1
        f, raw = features(w, splits.get(a["sym"]), anchors_by_sym.get(a["sym"]), days)
        f["tod"] = a.get("tod") or ("after" if a["hhmm"] >= "16:00" else ("pre" if a["hhmm"] < "09:30" else "reg"))
        f["anchor_after16"] = "نعم" if after and a["hhmm"] >= "16:00" else "لا"
        # الشاهدان
        if i0 not in pools:
            pools[i0] = day_pool(ser, i0, med_cache)
        if i0 not in near_cache:
            near_cache[i0] = {s for s, gl in anchors_by_sym.items() if any(i0 - 20 <= g <= i0 for g in gl)}
        px_prev = float(w["c"][w["p0"] - 1]) if w["p0"] > 0 else None
        cm, cr = pick_controls(pools[i0], near_cache[i0], px_prev, raw.get("ret0"), raw.get("vol_x0"), rng)
        ctrl = {}
        for tag, s in (("CM", cm), ("CR", cr)):
            if not s:
                ctrl[tag] = None
                continue
            wc = adj_window(ser, s, i0, splits, days=days)
            oc = outcomes(wc, None, last_gidx) if wc else None
            ctrl[tag] = {"sym": s, "late100_10": (oc or {}).get("late100_10"), "late50_10": (oc or {}).get("late50_10"),
                         "w": wc} if oc else None
        # الأفواج k
        kk = {k: cohort_k(w, k, last_gidx) for k in (1, 2, 3)}
        # سياساتُ التمركز
        pos = {}
        p0 = w["p0"]
        if o.get("late100_10") is not None:
            pos["POS-0"] = simulate(w, o["close0"], o["low0"] * (1 - STOP_BELOW), o["close0"] * 2.0, p0)
            if ctrl.get("CM"):
                wc = ctrl["CM"]["w"]
                pos["C-MOM"] = simulate(wc, float(wc["c"][wc["p0"]]), float(wc["l"][wc["p0"]]) * (1 - STOP_BELOW),
                                        float(wc["c"][wc["p0"]]) * 2.0, wc["p0"])
        for k, ck in kk.items():
            if ck and ck.get("in") and ck.get("held_low0_k") == "نعم":
                pos[f"POS-{k}"] = simulate(w, ck["close_k"], ck["low_k"] * (1 - STOP_BELOW), ck["close_k"] * 2.0, p0 + k)
        for tag in ("CM", "CR"):
            if ctrl.get(tag):
                ctrl[tag].pop("w", None)
        rows.append({"set": label, "sym": a["sym"], "day": a["day"], "day0": d0, "year": d0[:4], "f": f, "raw": raw, "o": o,
                     "ctrl": ctrl, "k": kk, "pos": pos, "a": {k: a.get(k) for k in ("entry", "hhmm", "usd5", "vol_x", "gap_pct", "f2", "f3", "exit", "mg_after", "exploded100", "mg_day", "close_ret")}})
    return rows, nobase, incomplete


# ─────────────────────────── العائلةُ 4/5 (A فقط) ───────────────────────────
def trades_day(sym, day, key, limit=5000):
    d = dt.date.fromisoformat(day)
    t_lt = int(dt.datetime(d.year, d.month, d.day, 16, 0, tzinfo=NY).timestamp() * 1e9)
    t_ge = int(dt.datetime(d.year, d.month, d.day, 9, 30, tzinfo=NY).timestamp() * 1e9)
    js = _get(f"{API}/v3/trades/{sym}", {"timestamp.gte": t_ge, "timestamp.lt": t_lt, "order": "desc", "limit": limit}, key)
    _CALLS["trades"] += 1
    res = list(reversed((js or {}).get("results") or []))
    return [{"price": t.get("price"), "size": t.get("size"), "exchange": t.get("exchange")} for t in res]


def quotes_close(sym, day, key, limit=200):
    d = dt.date.fromisoformat(day)
    t_lt = int(dt.datetime(d.year, d.month, d.day, 16, 0, tzinfo=NY).timestamp() * 1e9)
    t_ge = int(dt.datetime(d.year, d.month, d.day, 15, 55, tzinfo=NY).timestamp() * 1e9)
    js = _get(f"{API}/v3/quotes/{sym}", {"timestamp.gte": t_ge, "timestamp.lt": t_lt, "order": "desc", "limit": limit}, key)
    _CALLS["quotes"] += 1
    return (js or {}).get("results") or []


def flow_features(tr, qs):
    f = {}
    ac = S.acc_components(tr) if tr else None
    ob = S._operator_blocks([(t["price"], t["size"]) for t in tr], int(S.CONFIG.get("OPERATOR_MIN_SHARES", 1000))) if tr else None
    f["aggr_buy0"] = _b((ac or {}).get("aggressive_buy_pct"), (45, 55), ("<45%", "45-55", "≥55")) if ac else None
    f["dark0"] = _b((ac or {}).get("dark_share_pct"), (30, 50), ("<30%", "30-50", "≥50")) if ac else None
    f["bid_block0"] = (None if ob is None else ("نعم" if ob.get("bid_block_shares", 0) >= int(S.CONFIG.get("OPERATOR_MIN_SHARES", 1000)) else "لا"))
    try:
        up = S.uniform_prints([(t["price"], t["size"]) for t in tr]) if tr else {}
    except Exception:                                                # noqa: BLE001
        up = {}
    f["iceberg0"] = None if not tr else ("نعم" if up else "لا")
    sp = ask_thin = None
    if qs:
        q = qs[0]
        b, a_ = q.get("bid_price"), q.get("ask_price")
        if b and a_ and a_ > 0:
            sp = (a_ - b) / a_ * 100
            ask_thin = (a_ * float(q.get("ask_size") or 0) * 100) <= 1000.0   # ask_size بوحدة 100 سهم (round lots)
    f["spread0"] = _b(sp, (2, 5), ("<2%", "2-5", "≥5"))
    f["ask_thin0"] = None if ask_thin is None else ("نعم" if ask_thin else "لا")
    return f


# ─────────────────────────── التنفيذ ───────────────────────────
FEATS_SPEC = [
    # (الاسم · السلّةُ الأعلى المُعلَنة · العائلة)
    ("close_pos0", "≥0.7", 1), ("retreat0", ">0", 1), ("wick_up0", "<5%", 1), ("vol_x0", "≥10", 1), ("usd0", "≥1M", 1),
    ("above_low0", "نعم", 1), ("tod", "pre", 1),
    ("range20", "<40%", 2), ("rsi14", "<30", 2), ("rsi_slope5", ">+5", 2), ("vol_dry", "<0.5", 2), ("vol_x_prev", "≥3", 2),
    ("ret5_prev", ">+20%", 2), ("dist_low60", "<10%", 2), ("sweeps20", "≥3", 2), ("failed_pumps60", "0", 2),
    ("px0", "<1$", 6), ("rsplit_days", "≤30", 6), ("rsplit_count365", "≥2", 6),
    ("prior_anchors60", "≥2", 7), ("days_since_anchor", "≤5", 7), ("prior_expl60", "0", 7),
]
FEATS_A_ONLY = [("float_d", "<4م", 6), ("avail_d", "<20k", 6), ("aggr_buy0", "≥55", 4), ("bid_block0", "نعم", 4),
                ("dark0", "≥50", 4), ("iceberg0", "نعم", 4), ("spread0", "≥5", 4), ("ask_thin0", "نعم", 4),
                ("proxy_in_win", "نعم", 5), ("offering_recent", "نعم", 5)]
COMBOS = [
    ("rsi14<30 ∧ range20<40", lambda f: (f.get("rsi14") == "<30", f.get("range20") == "<40%")),
    ("rsi14<30 ∧ vol_x0≥10", lambda f: (f.get("rsi14") == "<30", f.get("vol_x0") == "≥10")),
    ("above_low0 ∧ close_pos0≥0.7", lambda f: (f.get("above_low0") == "نعم", f.get("close_pos0") == "≥0.7")),
    ("vol_x_prev≥3 ∧ ret5_prev>20", lambda f: (f.get("vol_x_prev") == "≥3", f.get("ret5_prev") == ">+20%")),
    ("px0<1 ∧ rsplit_days≤30", lambda f: (f.get("px0") == "<1$", f.get("rsplit_days") == "≤30")),
    ("prior_anchors60≥2 ∧ above_low0", lambda f: (f.get("prior_anchors60") == "≥2", f.get("above_low0") == "نعم")),
    ("retreat0>0 ∧ usd0≥1M", lambda f: (f.get("retreat0") == ">0", f.get("usd0") == "≥1M")),
    ("dist_low60<10 ∧ rsi14<30", lambda f: (f.get("dist_low60") == "<10%", f.get("rsi14") == "<30")),
    ("sweeps20≥3 ∧ above_low0", lambda f: (f.get("sweeps20") == "≥3", f.get("above_low0") == "نعم")),
    ("rsplit_count365≥2 ∧ vol_x0≥10", lambda f: (f.get("rsplit_count365") == "≥2", f.get("vol_x0") == "≥10")),
]
COMBOS_K = [("held_low0_1 ∧ vol_dry_1<0.3", 1, lambda c: (c.get("held_low0_k") == "نعم", c.get("vol_dry_k") == "<0.3")),
            ("held_low0_2 ∧ inside_2=2", 2, lambda c: (c.get("held_low0_k") == "نعم", c.get("inside_k") == "2"))]
TRIPLE = ("rsi14<30 ∧ above_low0 ∧ held_low0_1", 1,
          lambda f, c: (f.get("rsi14") == "<30", f.get("above_low0") == "نعم", c.get("held_low0_k") == "نعم"))


def _combo_getf(fn):
    def g(r):
        vals = fn(r["f"])
        if any(v is None for v in vals):
            return None
        return "نعم" if all(vals) else "لا"
    return g


def report_set(rows, label, min_n, z, halves=False, years=None):
    """جداولُ الميزات لمجتمعٍ واحد (A أو سنةٍ من C) ⟵ {feat: verdict}."""
    out = {}
    if not rows:
        return out
    cm_rows = [r for r in rows if r["ctrl"].get("CM") and r["ctrl"]["CM"].get("late100_10") is not None]
    cm_rate = (sum(1 for r in cm_rows if r["ctrl"]["CM"]["late100_10"]) / len(cm_rows)) if cm_rows else None
    specs = list(FEATS_SPEC) + ([x for x in FEATS_A_ONLY] if label == "A" else [])
    getters = [(name, best, (lambda r, n=name: r["f"].get(n))) for name, best, _fam in specs]
    getters += [(name, "نعم", _combo_getf(fn)) for name, fn in COMBOS]
    if label == "A":
        getters.append(("owner3", "نعم", lambda r: r["f"].get("owner3")))
    for name, best, getf in getters:
        v = judge_feat(rows, getf, best, min_n=min_n, z=z)
        v["best"] = best
        if v.get("c1") is not None:
            rr, per, c5 = mh_ratio(rows, getf, best)
            v["mh"], v["c5"] = rr, c5
            v["c6"] = (cm_rate is not None and cm_rate > 0 and (v["p"][0] / 100) >= 2 * cm_rate) if v.get("p") else None
            if halves:
                mid = sorted(r["day0"] for r in rows)[len(rows) // 2]
                hs = []
                for sel in (lambda r: r["day0"] < mid, lambda r: r["day0"] >= mid):
                    sub = [r for r in rows if sel(r)]
                    vt = judge_feat(sub, getf, best, min_n=MIN_HALF, z=1.96)
                    hs.append(vt.get("p")[0] > vt.get("p")[1] if vt.get("p") else None)
                v["c4"] = all(h is True for h in hs)
                v["halves"] = hs
        out[name] = v
    # الأفواج k
    for k in (1, 2, 3):
        krows = [r for r in rows if r["k"].get(k) and r["k"][k].get("in")]
        out[f"cohort_{k}_n"] = len(krows)
        if not krows:
            continue
        for fname, best in (("held_low0_k", "نعم"), ("inside_k", str(k)), ("vol_dry_k", "<0.3"), ("close_k_vs_0", ">0")):
            top = [r for r in krows if r["k"][k].get(fname) == best]
            rest = [r for r in krows if r["k"][k].get(fname) not in (None, best)]
            tn, tk = len(top), sum(1 for r in top if r["k"][k]["late100_k"])
            rn, rk = len(rest), sum(1 for r in rest if r["k"][k]["late100_k"])
            vv = {"n": (tn, rn), "k": (tk, rk), "best": best}
            if tn >= min_n and rn >= min_n:
                pt, pr = tk / tn, rk / rn
                tlo, thi = wilson(tk, tn, z); rlo, rhi = wilson(rk, rn, z)
                vv.update(p=(pt * 100, pr * 100), c1=(pt >= 2 * pr if pr > 0 else tk > 0), c2=(tlo > rhi), c3=True)
                # الشرط 5 داخل الفوج بطبقات يوم 0
                rr, per, c5 = mh_ratio([dict(r, o={"late100_10": r["k"][k]["late100_k"]}) for r in krows],
                                       lambda r, fn=fname, kk=k: r["k"][kk].get(fn), best)
                vv.update(mh=rr, c5=c5, c6=(cm_rate is not None and cm_rate > 0 and pt >= 2 * cm_rate))
            else:
                vv.update(c1=None, c2=None, c3=False, why=f"لا حكم (n={tn}/{rn})")
            out[f"{fname}[k={k}]"] = vv
        for cname, kk, fn in COMBOS_K:
            if kk != k:
                continue
            getf = (lambda r, fn=fn, kk=k: (None if any(v is None for v in fn(r["k"][kk])) else ("نعم" if all(fn(r["k"][kk])) else "لا")))
            sub = [dict(r, o={"late100_10": r["k"][k]["late100_k"]}) for r in krows]
            vv = judge_feat(sub, getf, "نعم", min_n=min_n, z=z)
            vv["best"] = "نعم"
            out[f"{cname}[k={k}]"] = vv
    # الثلاثيّة
    name, kk, fn = TRIPLE
    krows = [r for r in rows if r["k"].get(kk) and r["k"][kk].get("in")]
    if krows:
        getf = lambda r: (None if any(v is None for v in fn(r["f"], r["k"][kk])) else ("نعم" if all(fn(r["f"], r["k"][kk])) else "لا"))  # noqa: E731
        sub = [dict(r, o={"late100_10": r["k"][kk]["late100_k"]}) for r in krows]
        vv = judge_feat(sub, getf, "نعم", min_n=min_n, z=z)
        vv["best"] = "نعم"
        out[name] = vv
    out["_cm_rate"] = cm_rate
    return out


def print_verdicts(vd, title):
    log(f"\n{'=' * 78}\n{title}\n{'=' * 78}")
    for name, v in vd.items():
        if name.startswith("_") or name.startswith("cohort_"):
            continue
        if not isinstance(v, dict):
            continue
        if v.get("c1") is None:
            log(f"▶ {name} «{v.get('best')}»: {v.get('why', 'لا حكم')} n={v.get('n')}")
            continue
        p = v["p"]
        flags = f"①{'✅' if v['c1'] else '❌'} ②{'✅' if v['c2'] else '❌'} ③✅ ⑤{'✅' if v.get('c5') else '❌'} ⑥{'✅' if v.get('c6') else '❌'}"
        if "c4" in v:
            flags += f" ④{'✅' if v['c4'] else '❌'}"
        log(f"▶ {name} «{v['best']}»: {p[0]:.1f}% ({v['k'][0]}/{v['n'][0]}) مقابل {p[1]:.1f}% ({v['k'][1]}/{v['n'][1]}) · "
            f"MH {fmt(v.get('mh')) if v.get('mh') not in (None, float('inf')) else '∞'}× · {flags}")


def passes(v, need_c4=False):
    if not isinstance(v, dict) or v.get("c1") is None:
        return False
    ok = v["c1"] and v["c2"] and v.get("c3") and bool(v.get("c5")) and bool(v.get("c6"))
    if need_c4:
        ok = ok and bool(v.get("c4"))
    return ok


def pos_summary(rows, tag):
    xs = [r["pos"][tag] for r in rows if r["pos"].get(tag) is not None]
    if not xs:
        return None
    lo, hi = boot_ci(xs)
    return {"n": len(xs), "mean": sum(xs) / len(xs), "median": statistics.median(xs), "ci": (lo, hi),
            "win": sum(1 for x in xs if x > 0) / len(xs) * 100}


def main() -> int:                                                   # noqa: PLR0911, PLR0912, PLR0915
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        log("⛔ لا POLYGON_API_KEY — خروج 2")
        return 2
    if not _selfcheck_readonly():
        log("⛔ الحارسُ الذاتيّ: الأداةُ ليست قراءةً فقط — خروج 5")
        return 5
    today = dt.datetime.now(NY).date()
    log(f"🕵️⏳ T-PRELINK · العقد prelink_prereg.md · A منذ {SINCE} · C {YEARS or '—'} · بذرة {SEED} · صفقات {'✅' if TRADES_ON else '❌ (الغ فتح المحاور)'}"
        + (f" · 🧪 جدوى: أوّلُ {MAX_ANCHORS} مرساة" if MAX_ANCHORS else ""))
    # ── التقويم + grouped
    years_all = sorted(set(YEARS) | {"2026"} | ({"2022"} if YEARS else set()))
    days = []
    for y in years_all:
        days += year_days(y)
    days = [d for d in days if GROUPED_FROM <= d <= min(GROUPED_TO, (today - dt.timedelta(days=1)).isoformat())]
    if not YEARS:                                                    # A وحدَها: نافذةٌ ضيّقة
        days = [d for d in days if (dt.date.fromisoformat(SINCE) - dt.timedelta(days=120)).isoformat() <= d]
    log(f"📅 أيّامُ التداول المستهدفة {len(days)} ({days[0]} ⟶ {days[-1]})")
    n_sp = CF.load_all_splits("2022-10-01")
    splits = dict(CF._SPLITS_ALL) if n_sp else {}
    log(f"✂️ تقسيماتُ السوق: {n_sp:,} صفًّا في {len(splits):,} رمزًا" + ("" if n_sp else " ⚠️ ناقصة — التسويةُ رمزًا رمزًا غيرُ متاحة"))
    ser, got, miss = build_series(days, key)
    didx = {d: i for i, d in enumerate(days)}
    last_gidx = didx[got[-1]] if got else -1
    in_scope = [d for d in days if any(d.startswith(y) for y in YEARS)] if YEARS else days
    got_scope = [d for d in got if d in set(in_scope)]
    cov = len(got_scope) / len(in_scope) if in_scope else 0
    log(f"📦 grouped: {len(got)}/{len(days)} يومًا (داخلَ السنوات الحاكمة {len(got_scope)}/{len(in_scope)} = {cov * 100:.1f}%) · رموزٌ {len(ser.arr):,} · ناقصة {len(miss)}"
        + (f" (أوّلُها {miss[:5]})" if miss else ""))
    vp7 = cov >= 0.98
    log(f"🔒 V-P7 تغطيةُ grouped ≥98%: {'✅' if vp7 else '⚠️ ناقصة — الحكمُ مقيَّد'}")
    # ── A
    until = UNTIL or days[max(0, last_gidx - H_GOV)]
    a_anch, a_total, a_fail = anchors_A(key, until)
    if a_total == 0:
        log("⛔ صفرُ مرساةٍ في A — خروج 4")
        return 4
    idn = [a for a in a_anch if ID_FROM <= a["day"] <= ID_TO]
    k50, k100 = sum(a["same_day"] for a in idn), sum(a["exploded100"] for a in idn)
    vp1 = (k50, len(idn), k100) == (ID_K50, 321, ID_K100)
    log(f"🔒 V-P1 هُويّةُ A ({ID_FROM}⟶{ID_TO}): exploded50 {k50}/{len(idn)} · exploded100 {k100} — المنشور {ID_K50}/321 · {ID_K100} "
        f"{'✅' if vp1 else ('⚠️ جزئيّ (جدوى)' if MAX_ANCHORS else '⚠️ لا يطابق — يُقرأ الفرق قبل الحكم')}")
    anchors_by_sym_A = collections.defaultdict(list)
    for a in a_anch:
        d0, _ = day0_of(a["day"], a["hhmm"], days, didx)
        if d0 in didx:
            anchors_by_sym_A[a["sym"]].append(didx[d0])
    rows_A, nobase_A, inc_A = build_rows(a_anch, ser, days, didx, splits, last_gidx, anchors_by_sym_A, "A")
    # A: المؤرَّخُ (فلوت/متاح) والعضويّة — بالاسم من T-OPLINK
    try:
        import opentry_link_probe as OPL                            # بالاسم: snapshot_before · dated_values
        commits = {f: OPL._commits(f) for f in OPL.SNAP_FILES}
        cache = {}

        def _load(hsh, f):
            if (hsh, f) not in cache:
                try:
                    cache[(hsh, f)] = json.loads(subprocess.run(["git", "show", f"{hsh}:{f}"], capture_output=True, text=True).stdout)
                except Exception:                                    # noqa: BLE001
                    cache[(hsh, f)] = None
            return cache[(hsh, f)]
        dated_by_day = {}
        for r in rows_A:
            day = r["day"]
            if day not in dated_by_day:
                snaps = {f: OPL.snapshot_before(commits[f], day, (lambda h, f=f: _load(h, f))) for f in OPL.SNAP_FILES}
                dated_by_day[day] = OPL.dated_values(day, snaps)
                hw = snaps["hunter_watchlist.json"][1] or {}
                dated_by_day[day]["__hunter"] = {s.get("symbol") for s in (hw.get("stocks") or [])}
            dv = dated_by_day[day].get(r["sym"]) or {}
            r["f"]["float_d"] = OPL.float_bucket(dv.get("float"))
            r["f"]["avail_d"] = OPL.avail_bucket(dv.get("avail"))
            r["f"]["float_d"] = None if r["f"]["float_d"] == "؟" else r["f"]["float_d"]
            r["f"]["avail_d"] = None if r["f"]["avail_d"] == "؟" else r["f"]["avail_d"]
            r["f"]["hunter_prev"] = "نعم" if r["sym"] in dated_by_day[day]["__hunter"] else "لا"
            fl = OPL.owner_flags(r["f"], dv.get("float"), dv.get("avail"))
            r["f"]["owner3"] = None if any(v is None for v in fl.values()) else ("نعم" if all(fl.values()) else "لا")
    except Exception as e:                                           # noqa: BLE001
        log(f"⚠️ المؤرَّخُ (فلوت/متاح/عضويّة) تعذّر: {type(e).__name__}: {e}")
    # A: العائلة 4 (صفقات/NBBO) — مشروطة
    if TRADES_ON and rows_A:
        for n, r in enumerate(rows_A, 1):
            try:
                tr = trades_day(r["sym"], r["day0"], key)
                qs = quotes_close(r["sym"], r["day0"], key)
                r["f"].update(flow_features(tr, qs))
                for k in (1, 2, 3):
                    ck = r["k"].get(k)
                    if ck and ck.get("in"):
                        dk = days[didx[r["day0"]] + k]
                        trk = trades_day(r["sym"], dk, key, limit=3000)
                        ob = S._operator_blocks([(t["price"], t["size"]) for t in trk], int(S.CONFIG.get("OPERATOR_MIN_SHARES", 1000))) if trk else None
                        ck["bid_block_k"] = None if ob is None else ("نعم" if ob.get("bid_block_shares", 0) >= 1000 else "لا")
            except Exception as e:                                   # noqa: BLE001
                log(f"   ⚠️ صفقات {r['sym']} {r['day0']}: {type(e).__name__}")
            if n % 100 == 0:
                log(f"   … صفقات A {n}/{len(rows_A)}")
    # A: العائلة 5 (SEC معلَنٌ سلفًا) — تُملأ من الإيداعات المخزَّنة بعد نداء sec_recent_filings (بالاسم)
    if rows_A:
        seen = {}
        for r in rows_A:
            sym = r["sym"]
            if sym not in seen:
                try:
                    S.sec_recent_filings(sym)
                except Exception:                                    # noqa: BLE001
                    pass
                seen[sym] = True
                _CALLS["sec"] += 1
            px = (S._SEC_PROXY.get(sym) or {})
            of = (S._SEC_FOUNDING.get(sym) or {})
            d0 = r["day0"]
            r["f"]["proxy_in_win"] = None if not px else ("نعم" if (px.get("date", "") <= d0 and (dt.date.fromisoformat(d0) - dt.date.fromisoformat(px["date"])).days <= 75) else "لا")
            r["f"]["offering_recent"] = None if not of else ("نعم" if (of.get("date", "") <= d0 and (dt.date.fromisoformat(d0) - dt.date.fromisoformat(of["date"])).days <= 60) else "لا")
    covA = len(rows_A) / a_total if a_total else 0
    log(f"🩺 V-P4 تغطيةُ A: صفوفٌ {len(rows_A)} · تعذّر {a_fail} · بلا أساس {nobase_A} · نافذةٌ ناقصة {inc_A} من {a_total} = {covA * 100:.1f}%")
    # V-P8: مسارُ A المرجعيّ (adjusted=true لكلّ رمز) مقابل مسار grouped
    agree = tot8 = 0
    for r in rows_A:
        if r["o"].get("late100_10") is None:
            continue
        d0 = r["day0"]
        bars = ticker_daily_adj(r["sym"], (dt.date.fromisoformat(d0) - dt.timedelta(days=5)).isoformat(),
                                (dt.date.fromisoformat(d0) + dt.timedelta(days=20)).isoformat(), key)
        _CALLS["daily_adj"] += 1
        after = [b for b in bars if b[0] > d0][:10]
        c0 = next((b[4] for b in bars if b[0] == d0), None)
        if c0 and after:
            ref = max(b[2] for b in after) / c0 - 1 >= 1.0
            tot8 += 1
            agree += int(ref == bool(r["o"]["late100_10"]))
            r["o"]["late100_10_ref"] = ref
    vp8 = (agree / tot8 >= 0.95) if tot8 else None
    log(f"🔒 V-P8 شاهدُ الطريقة (grouped مقابل adjusted=true): اتّفاق {agree}/{tot8}" + (f" = {agree / tot8 * 100:.1f}% {'✅' if vp8 else '❌'}" if tot8 else " — لا قياس"))
    # ── C
    rows_C, vp6_ok, cov_C = {}, True, {}
    for y in YEARS:
        kr = load_kasih(y)
        if kr is None:
            log(f"⛔ V-P6: kasih_rows_{y}.jsonl غائب — C {y} «لا قياس»")
            vp6_ok = False
            continue
        ok = len(kr) == KASIH_COUNTS.get(y, -1)
        log(f"🔒 V-P6 هُويّةُ C {y}: صفوفٌ {len(kr):,} — المنشور {KASIH_COUNTS.get(y):,} {'✅' if ok else '❌ لا يطابق'}")
        vp6_ok = vp6_ok and ok
        anch = [{"sym": k["sym"], "day": k["day"], "hhmm": k.get("anchor_ny") or "10:00", "entry": k.get("entry"),
                 "anchor_low": k.get("anchor_low"), "same_day": None, "usd5": k.get("usd5"), "vol_x": k.get("vol_x"),
                 "gap_pct": k.get("gap_pct"), "f2": k.get("f2"), "f3": k.get("f3"), "exit": k.get("exit"), "mg_after": k.get("mg_after")}
                for k in kr]
        if MAX_ANCHORS:
            anch = anch[:MAX_ANCHORS]
        abs_ = collections.defaultdict(list)
        for a in anch:
            d0, _ = day0_of(a["day"], a["hhmm"], days, didx)
            if d0 in didx:
                abs_[a["sym"]].append(didx[d0])
        rc, nb, inc = build_rows(anch, ser, days, didx, splits, last_gidx, abs_, f"C{y}")
        cov_C[y] = len(rc) / len(anch) if anch else 0
        log(f"🩺 V-P4 تغطيةُ C {y}: صفوفٌ {len(rc):,} · بلا أساس {nb:,} · نافذةٌ ناقصة {inc:,} من {len(anch):,} = {cov_C[y] * 100:.1f}%")
        rows_C[y] = rc
    # ── الأساس (§②)
    log(f"\n{'=' * 78}\n📊 §② الأساس — التصنيفُ الثلاثيّ والأفق (المكتملُ وحدَه)\n{'=' * 78}")

    def base_line(rows, tag):
        for h in HORIZONS:
            k, n = rate(rows, f"late100_{h}")
            k5, n5 = rate(rows, f"late50_{h}")
            lo, hi = wilson(k, n) if n else (0, 0)
            log(f"   {tag} · أفق {h}: +100% {k}/{n} = {k / n * 100 if n else 0:.1f}% [{lo:.0f}·{hi:.0f}] · +50% {k5}/{n5} = {k5 / n5 * 100 if n5 else 0:.1f}%")
        cls = collections.Counter(r["o"].get("cls") for r in rows)
        log(f"   {tag} · التصنيف: {dict(cls)}")
        cm = [r for r in rows if r["ctrl"].get("CM") and r["ctrl"]["CM"].get("late100_10") is not None]
        cr = [r for r in rows if r["ctrl"].get("CR") and r["ctrl"]["CR"].get("late100_10") is not None]
        k, n = rate(rows, "late100_10")
        pa = k / n if n else None
        pm = (sum(1 for r in cm if r["ctrl"]["CM"]["late100_10"]) / len(cm)) if cm else None
        pr = (sum(1 for r in cr if r["ctrl"]["CR"]["late100_10"]) / len(cr)) if cr else None
        log(f"   {tag} · الشاهدان (late100_10): CM {fmt(pm * 100 if pm is not None else None)}% (n={len(cm)}) ⇒ {fmt(pa / pm if (pa and pm) else None)}× · "
            f"CR {fmt(pr * 100 if pr is not None else None)}% (n={len(cr)}) ⇒ {fmt(pa / pr if (pa and pr) else None)}×")
        late = [r for r in rows if r["o"].get("late100_10")]
        if late:
            dtp = [r["o"].get("days_to_peak") for r in late if r["o"].get("days_to_peak") is not None]
            mdd = [r["o"].get("mdd_before_peak") for r in late if r["o"].get("mdd_before_peak") is not None]
            held = [r["o"].get("held_low0_to_peak") for r in late if r["o"].get("held_low0_to_peak") is not None]
            rearm = [r for r in late if any(0 < (g - didx.get(r["day0"], 0)) <= (r["o"].get("days_to_peak") or 0)
                                            for g in (anchors_by_sym_A if tag == "A" else {}).get(r["sym"], []))] if tag == "A" else []
            log(f"   {tag} · المتأخّرون (+100%/10): n={len(late)} · وسيطُ الأيّام حتى القمّة {fmt(statistics.median(dtp) if dtp else None)} · "
                f"وسيطُ أقصى الهبوط قبلها {fmt(statistics.median(mdd) if mdd else None)}% · صمد فوق low0 {sum(held)}/{len(held)}"
                + (f" · مرساةٌ جديدة قبل القمّة {len(rearm)}/{len(late)}" if tag == "A" else ""))
        s3 = [r for r in rows if r["f"].get("owner3") is not None]
        if s3:
            k3, n3 = sum(1 for r in s3 if r["f"]["owner3"] == "نعم" and r["o"].get("late100_10")), sum(1 for r in s3 if r["f"]["owner3"] == "نعم")
            log(f"   {tag} · شروطُ المالك الثلاث مجتمعةً (مؤرَّخًا): استوفاها {n3} · انفجر متأخّرًا منها {k3}")
        split_rows = [r for r in rows if r["o"].get("split_in_win")]
        log(f"   {tag} · صفوفٌ بتقسيمٍ داخل النافذة (V-P2): {len(split_rows)}")
    base_line(rows_A, "A")
    for y, rc in rows_C.items():
        base_line(rc, f"C{y}")
    # ── rearmed في C (من صفوف kasih نفسِها)
    for y, rc in rows_C.items():
        abs_ = collections.defaultdict(list)
        for r in rc:
            abs_[r["sym"]].append(didx[r["day0"]])
        late = [r for r in rc if r["o"].get("late100_10")]
        rearm = sum(1 for r in late if any(0 < g - didx[r["day0"]] <= (r["o"].get("days_to_peak") or 0) for g in abs_[r["sym"]]))
        log(f"   C{y} · مرساةٌ جديدة قبل القمّة بين المتأخّرين: {rearm}/{len(late)}")
    # ── الحكم (§⑤)
    n_tests = len(FEATS_SPEC) + len(FEATS_A_ONLY) + len(COMBOS) + len(COMBOS_K) + 1 + 12 + 1
    z = z_bonf(n_tests)
    log(f"\n🧮 تصحيحُ التعدّد: n_tests={n_tests} ⇒ z={z:.2f}")
    vA = report_set(rows_A, "A", MIN_N_A, z, halves=True)
    print_verdicts(vA, "🔗 A — الميزاتُ على late100_10 (العقد §⑤ · السلّةُ المُعلَنة)")
    log(f"   CM معدّلُ الأساس في A: {fmt((vA.get('_cm_rate') or 0) * 100)}%")
    vC = {y: report_set(rc, f"C{y}", MIN_N_C, z) for y, rc in rows_C.items()}
    for y, vd in vC.items():
        print_verdicts(vd, f"🔗 C {y} — الميزاتُ على late100_10")
        log(f"   CM معدّلُ الأساس في C{y}: {fmt((vd.get('_cm_rate') or 0) * 100)}%")
    # الجداولُ الحاكمة بلا تقسيمٍ داخل النافذة (V-P2)
    vA2 = report_set([r for r in rows_A if not r["o"].get("split_in_win")], "A", MIN_N_A, z, halves=True)
    vC2 = {y: report_set([r for r in rc if not r["o"].get("split_in_win")], f"C{y}", MIN_N_C, z) for y, rc in rows_C.items()}
    # ── الخلاصة
    log(f"\n{'=' * 78}\n🏁 الحكم (يُقرأ بالأضعف · مع/بدون صفوف التقسيم)\n{'=' * 78}")
    names = [k for k in vA if not k.startswith("_") and not k.startswith("cohort_")]
    for y in vC:
        names += [k for k in vC[y] if k not in names and not k.startswith("_") and not k.startswith("cohort_")]
    links, momentum_only = [], []
    for name in names:
        pa = passes(vA.get(name), need_c4=True) and passes(vA2.get(name), need_c4=True)
        pc_all = bool(vC) and all(passes(vC[y].get(name)) and passes(vC2[y].get(name)) for y in vC)
        c_meas = bool(vC) and all(isinstance(vC[y].get(name), dict) and vC[y][name].get("c1") is not None for y in vC)
        a_meas = isinstance(vA.get(name), dict) and vA[name].get("c1") is not None
        if pc_all and (pa or not a_meas):
            links.append(name)
        elif c_meas and all((vC[y][name].get("c1") and vC[y][name].get("c2")) for y in vC) and not pc_all:
            momentum_only.append(name)
        status = ("✅ رابط" if name in links else ("🟡 يفصل ويسقط على ⑤/⑥ (زخمٌ/مرساة)" if name in momentum_only
                  else ("🟠 يعبر على A وحدَها — لا C ⇒ قيدُ الإثبات لا رابط" if (pa and not c_meas) else "❌")))
        log(f"   {name}: A {'✅' if pa else ('—' if not a_meas else '❌')} · C {'✅' if pc_all else ('—' if not c_meas else '❌')} ⇒ {status}")
    cov_ok = covA >= MIN_COVER and all(v >= MIN_COVER for v in cov_C.values())
    if not YEARS or not vp6_ok or not rows_C:
        branch = "3 «لا قياس» — C غيرُ متاح أو V-P6 ساقط"
    elif not cov_ok:
        branch = "3 «لا قياس» — التغطية دون 80%"
    elif links:
        branch = f"1 «رابطٌ مقيس» — {links} (قيدَ الإثبات الأماميّ · لا يُشحَن شيء)"
    else:
        branch = "2 «لا رابط» بالمعيار الستّة" + (f" — ويفصل زخمًا/مرساةً لا رابطًا: {momentum_only}" if momentum_only else "")
    log(f"\n🏁 الفرعُ {branch}")
    # ── التمركز (§⑥)
    log(f"\n{'=' * 78}\n💵 §⑥ التمركز — R بعد التكلفة ({COST * 100:.0f}% للطرف · وقفٌ {STOP_BELOW * 100:.0f}% تحت أدنى يوم 0 · خروجٌ بهدف +100% أو بعد {POS_DAYS} جلسات)\n{'=' * 78}")
    pos_ok = {}
    for tag in ("POS-0", "POS-1", "POS-2", "POS-3", "C-MOM"):
        parts = {"A": pos_summary(rows_A, tag)}
        for y, rc in rows_C.items():
            parts[f"C{y}"] = pos_summary(rc, tag)
        line = " · ".join(f"{k}: " + ("—" if v is None else f"{v['mean']:+.3f}R [{v['ci'][0]:+.2f},{v['ci'][1]:+.2f}] وسيط {v['median']:+.2f} ربح {v['win']:.0f}% n={v['n']}") for k, v in parts.items())
        log(f"   {tag}: {line}")
        pos_ok[tag] = all(v is not None and v["mean"] > 0 and v["ci"][0] > 0 for k, v in parts.items() if k.startswith("C")) and bool(rows_C)
    # POS − C-MOM مقترنًا
    diffs = {}
    for y, rc in rows_C.items():
        d = [r["pos"]["POS-0"] - r["pos"]["C-MOM"] for r in rc if r["pos"].get("POS-0") is not None and r["pos"].get("C-MOM") is not None]
        if d:
            lo, hi = boot_ci(d)
            diffs[y] = (sum(d) / len(d), lo, hi, len(d))
            log(f"   POS-0 − C-MOM (C{y}): {sum(d) / len(d):+.3f}R [{lo:+.2f},{hi:+.2f}] n={len(d)}")
    pos_verdict = any(pos_ok.get(t) for t in ("POS-0", "POS-1", "POS-2", "POS-3")) and all(v[1] > 0 for v in diffs.values()) and bool(diffs)
    log(f"\n🏁 التمركزُ بين التنبيه والانفجار: {'ممكنٌ بتوقّعٍ موجبٍ بعد التكلفة ✅' if pos_verdict else 'غيرُ ممكنٍ بهذي السياسات ❌'}"
        + (f" — الأعلى: {max((t for t in pos_ok), key=lambda t: (pos_ok[t], t))}" if pos_ok else ""))
    # ── الصفوف (artifact)
    n_rows = _dump_rows(f"{ROWS_PREFIX}A.jsonl", rows_A)
    for y, rc in rows_C.items():
        n_rows += _dump_rows(f"{ROWS_PREFIX}C_{y}.jsonl", rc)
    log(f"\n📤 صفوفٌ مكتوبة: {n_rows:,} · نداءاتٌ: {dict(_CALLS)}")
    log("⚠️ حدودُ الصدق (العقد §⑨): لمسٌ لا تنفيذ · C تقريبٌ لتنبيهات الإنتاج · A ≈ 6 أسابيع · الفلوت/المتاح/الأحداث/الصفقات A فقط · B فارغة.")
    if not vp6_ok or not cov_ok or (not vp7):
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
