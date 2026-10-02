# -*- coding: utf-8 -*-
"""🔬 `T-HS-FX` — التحقيقُ الجنائيّ في «نموذج الرأس والكتفين» (أمرُ المالك 2026-10-01 «FINAL FORENSIC RESEARCH MISSION»).

• العقد (مدموجٌ قبل أيّ رقم): `hs_forensic/hs_fx_prereg.md` · وثائقُ المصادر: `hs_forensic/*.md` · الكاشف: `head_shoulders.py` **بالاسم**.
• الأوضاع (`HS_FX_MODE`): **verdict** (الحكمُ الآليّ §⑦ من ملفّي main وndq · بلا شبكة) · **main** (POP-BOT كاملًا · المداخل A-E · خطوطُ الأساس الستّة · النظرُ المستقبليّ · إجراءاتُ الشركات · عيّنتا الإعادة
  البصريّة والتدقيق الأعمى) · **ndq** (كونُ ناسداك: C · D · RECON مع BL-A وBL-B) · **sens** (الحساسيّة TRAIN ⟵ VAL ⟵ TEST) ·
  **rx** (`T-HS-RX` · العقد `hs_forensic/hs_rx_prereg.md`: POP-RX = NYSE/AMEX ناقص POP-BOT وناسداك · RECON وRECON-v2 أمام BL-A وBL-B ·
  عيّنةُ أمانةٍ عمياء بمفتاحٍ مختوم).
• القياسُ كلُّه من بار الدخول `e` وسعره `E` **بعد** الكشف السببيّ (`HS.detect`) — ولا يستعمل الكشفُ شيئًا بعد بار الاختراق (§⑨ يتحقّق).
🔒 بحثٌ فقط: **لا تلغرام · لا حالةَ إنتاج · لا مساسَ بالمسح الحيّ** — يكتب `hs_research/forensic/` ويدفعه `git_save`."""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import sys
import time
import zlib

import numpy as np
import pandas as pd

import head_shoulders as HS

TOOL = "T-HS-FX"
FX_DIR = os.path.join(HS.RES_DIR, "forensic")
FX_START = "2016-01-01"
ERAS = (("TRAIN", "2016-07-01", "2017-12-31"), ("VAL", "2018-01-01", "2018-12-31"),
        ("TEST", "2019-01-01", "2021-05-31"), ("SEEN", "2022-01-01", "2099-12-31"))
HZ = (1, 2, 3, 5, 10, 20, 30, 60, 90)
WINS = (30, 60, 90)
N_CTRL = 10
BOOT_B = 2000
BOOT_SEED = 20261002
CONF_ALPHA = 0.05 / 3            # بونفيروني للفرضيّات الثلاث (§⑦)
EXPL_ALPHA = 0.05                # الاستكشافيّ والحساسيّة (§⑧)
MIN_N = 30
SEQ_FAST = 10                    # «BREAKOUT→TARGET» السريع: الهدفُ خلال 10 بارات بلا عودة
SPLIT_PAD = HS.SPLIT_PAD_DAYS
NAMED = ("ASST", "MFI", "NXL", "LTBR", "SMTK")
CASE_MFE, CASE_MAE, CASE_CAP = 5.0, -0.80, 40
REPLAY_N = 10
REPLAY_SEED, NEW_SEED, NEG_SEED, MIX_SEED = 20261002, 20261003, 20261004, 20261005
BLIND_N, BLIND_BARS = 30, 150
OLD_FILE = os.path.join(HS.RES_DIR, "audit_2022_labels_iter2.json")
PX_CUTS = (1.0, 5.0)             # فئاتُ السعر الخامّ: أقلُّ من دولار · 1-5 · 5 فأكثر
SENS_CUT_TRAINVAL = "2019-06-30" # إطارُ الحساسيّة لـTRAIN/VAL (90 جلسةً بعد آخر إشارة VAL)
SENS_CUT_TEST = "2021-10-31"     # وما عبرهما يُختبر في TEST على إطارٍ يكفي 90 جلسةً بعدها
SPLIT_RETRY_PAUSE_S = 0.35       # §⑰ engineering — فاصلُ التمريرة الثانية لتقسيمات ياهو (خنقُ ndq الأولى)
SPLIT_RETRY_COOL_S = 45.0        # §⑰ engineering — تبريدٌ بعد تعذّرٍ متتالٍ
SPLIT_RETRY_STREAK = 15          # §⑰ engineering — طولُ التعذّر المتتالي قبل التبريد
SPLIT_RETRY_BUDGET_S = 75 * 60   # §⑰ engineering — سقفُ زمن التمريرة الثانية (الجوبُ 330 د)
# 🔁 `T-HS-RX` (العقد `hs_forensic/hs_rx_prereg.md` · مدموجٌ قبل أيّ رقمٍ من POP-RX)
RX_Q = 0.2                       # §④ «بنحو خُمس الارتفاع» — القراءةُ التشغيليّة للتدقيق الأعمى حرفًا (engineering · UNVERIFIED · لا ضبط)
RX_ALPHA = 0.05 / 4              # §⑦ بونفيروني على الفرضيّات الأربع ⟵ فاصلُ 98.75%
RX_EXCH = ("N", "A")             # §② NYSE · NYSE American من `otherlisted.txt`
RX_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
RX_SEED_V2, RX_SEED_V1, RX_SEED_NEG, RX_MIX_SEED = 20261006, 20261007, 20261008, 20261009
RX_GATE_RATIO = 2.0              # §⑬ (engineering): قاطعُ هذا الوضع لا يُفتح بالإخفاق (لا احتياطَ ياهو في البحث) · ومهلةُ الجلب الإنتاجيّة باقية
RX_COV_MIN = 0.90                # §⑬ (engineering): شموعٌ لأقلَّ منها من POP-RX ⟵ «جزئيّ» (نظيرُ حدّ مجهول التقسيم في §②)
RX_UNK_MAX = 0.10                # §② حرفًا: مجهولُ التقسيم **فوقه** من إشارات RECON أو RECON-v2 (ALL) ⟵ «جزئيّ»
RX_TV_EXCH = {"N": "NYSE", "A": "AMEX"}   # §⑬: سوقُ الرمز الغائب عن ماسح TradingView من `otherlisted.txt` — لا «NASDAQ:» الافتراضيّ
ALL_ERA = "ALL"                  # §③ مجموعُ الحقب الأربع (التأكيديّ في POP-RX)

P_C = dict(HS.STRICT)                                         # CURRENT
P_B = dict(HS.STRICT, brk_atr=0.0)                            # المدخل B: أوّلُ إغلاقٍ فوق العنق بلا هامش
P_A = dict(HS.STRICT, brk_atr=0.0, brk_mode="high")           # المدخل A: أوّلُ تجاوزٍ بالأعلى
SENS = {
    "k2": dict(HS.STRICT, k=2), "k4": dict(HS.STRICT, k=4), "k5": dict(HS.STRICT, k=5), "k6": dict(HS.STRICT, k=6),
    "st025": dict(HS.STRICT, shoulder_tol=0.25), "st050": dict(HS.STRICT, shoulder_tol=0.5),
    "st075": dict(HS.STRICT, shoulder_tol=0.75), "neckH": dict(HS.STRICT, neck_slope=0.1),
    "headB": dict(HS.STRICT, head_rule="below_shoulders"), "hp000": dict(HS.STRICT, height_min_pct=0.0),
    "hp010": dict(HS.STRICT, height_min_pct=0.10), "pb1": dict(HS.STRICT, prior_bars=1), "pb5": dict(HS.STRICT, prior_bars=5),
    "brk000": dict(HS.STRICT, brk_atr=0.0), "brk025": dict(HS.STRICT, brk_atr=0.25),
}
BRACKETS = {"B1": ("TC", "I2", 60), "B2": ("TC", "I1", 60), "B3": ("T100", "I2", 90)}
EVENT_SET = tuple((tg, st, w) for tg in ("TC", "T100") for st in ("I1", "I2", "I3") for w in WINS)
SEQS = ("BREAKOUT→TARGET", "BREAKOUT→RETEST→TARGET", "BREAKOUT→SIDEWAYS→TARGET", "BREAKOUT→STOP→TARGET",
        "BREAKOUT→FAILURE", "BREAKOUT→NEITHER")


def log(*a):
    print(*a, flush=True)


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ① أدواتٌ نقيّة (تُختبَر بلا شبكة)
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def era_of(d) -> str | None:
    """حقبةُ تاريخ الاختراق (§③) ⟵ TRAIN · VAL · TEST · SEEN · أو None (قبل 2016-07-01)."""
    s = str(d)[:10]
    for name, a, b in ERAS:
        if a <= s <= b:
            return name
    return None


def _first(mask) -> int | None:
    idx = np.flatnonzero(np.asarray(mask, dtype=bool))
    return int(idx[0]) if len(idx) else None


def event_bars(h, c, e: int, target, stop_px, w: int, extra_stop_i=None):
    """(بارُ الهدف · بارُ الإبطال) بعد e (1..w) — الهدفُ **بالأعلى** والإبطالُ **بالإغلاق** · و`extra_stop_i` (فشلُ الاختبار لـI3) بارٌ مطلق ·
    **ونافذةٌ ناقصة (e+w خارج البيانات) ⟵ None** (§⑤ «كلُّ مقياسٍ يشترط اكتمالَ نافذته»)."""
    n = len(c)
    if e + w >= n:
        return None
    hh, cc = np.asarray(h[e + 1:e + w + 1], float), np.asarray(c[e + 1:e + w + 1], float)
    t_t = _first(hh >= target) if target is not None and np.isfinite(target) else None
    t_s = _first(cc < stop_px) if stop_px is not None and np.isfinite(stop_px) else None
    t_t = None if t_t is None else t_t + 1
    t_s = None if t_s is None else t_s + 1
    if extra_stop_i is not None and e < int(extra_stop_i) <= e + w:
        x = int(extra_stop_i) - e
        t_s = x if t_s is None else min(t_s, x)
    return t_t, t_s


def classify(t_t, t_s) -> str:
    """CLEAN (الهدفُ أوّلًا) · DIRTY (إبطالٌ ثمّ هدف — **والتعادلُ في البار نفسِه إبطالٌ أوّلًا**) · STOP · NEITHER."""
    if t_t is not None and (t_s is None or t_t < t_s):
        return "CLEAN"
    if t_t is not None:
        return "DIRTY"
    if t_s is not None:
        return "STOP"
    return "NEITHER"


def seq_label(t_t, t_s, touch_rel) -> str:
    """التسلسل (§⑤ · T-C · I3 · 60): عودةٌ إلى العنق قبل الهدف ⟵ RETEST · هدفٌ نظيفٌ خلال `SEQ_FAST` بلا عودة ⟵ مباشر · وبعدها ⟵ SIDEWAYS."""
    c = classify(t_t, t_s)
    if c == "CLEAN":
        if touch_rel is not None and touch_rel < t_t:
            return "BREAKOUT→RETEST→TARGET"
        return "BREAKOUT→TARGET" if t_t <= SEQ_FAST else "BREAKOUT→SIDEWAYS→TARGET"
    return {"DIRTY": "BREAKOUT→STOP→TARGET", "STOP": "BREAKOUT→FAILURE"}.get(c, "BREAKOUT→NEITHER")


def bracket(o, h, c, e: int, E: float, target, stop_px, w: int) -> dict | None:
    """صفقةُ القوس (§⑤): جنيٌ عند الهدف (`max(Open، الهدف)` أوّلَ بارٍ أعلاه يبلغه) · وقفٌ بالإغلاق تحت المستوى (ذلك الإغلاق) · وإلّا إغلاقُ e+w ·
    **والتعادلُ في البار نفسِه وقف** · نافذةٌ ناقصة أو دخولٌ تالف ⟵ None. ⟵ {why · bars · ret · R}."""
    n = len(c)
    if e + w >= n or not (E is not None and np.isfinite(E) and E > 0):
        return None
    oo = np.asarray(o[e + 1:e + w + 1], float)
    hh = np.asarray(h[e + 1:e + w + 1], float)
    cc = np.asarray(c[e + 1:e + w + 1], float)
    t_t = _first(hh >= target) if target is not None and np.isfinite(target) else None
    t_s = _first(cc < stop_px) if stop_px is not None and np.isfinite(stop_px) else None
    if t_s is not None and (t_t is None or t_s <= t_t):
        px, why, k = float(cc[t_s]), "stop", t_s + 1
    elif t_t is not None:
        px, why, k = float(max(oo[t_t], target)), "target", t_t + 1
    else:
        px, why, k = float(cc[-1]), "time", w
    ret = px / E - 1.0
    risk = (E - stop_px) / E if stop_px is not None and np.isfinite(stop_px) else None
    return {"why": why, "bars": int(k), "ret": float(ret), "R": (float(ret / risk) if risk and risk > 0 else None)}


def rets_at(c, e: int, E: float, hz=HZ) -> dict:
    n = len(c)
    return {f"ret{x}": (float(c[e + x] / E - 1.0) if e + x < n and E > 0 else None) for x in hz}


def excursion(h, l, e: int, E: float, w: int):
    """(MFE · MAE) خلال w بارًا بعد e من الأعلى والأدنى — نافذةٌ ناقصة ⟵ (None, None)."""
    if e + w >= len(h) or not E > 0:
        return None, None
    return float(np.nanmax(h[e + 1:e + w + 1]) / E - 1.0), float(np.nanmin(l[e + 1:e + w + 1]) / E - 1.0)


def split_factor_after(pairs, asof) -> float:
    """عاملُ إلغاء التسوية (السعرُ الخامّ = المسوّى × العامل): حاصلُ نسب ياهو للتقسيمات **بعد** `asof` (صيغةُ `S._pit_split_factor`) ·
    بلا أزواج ⟵ 1.0 (يُعلَن «غيرَ معلوم» حيث يلزم)."""
    f = 1.0
    a = str(asof)[:10]
    for d, r in pairs or []:
        try:
            if str(d)[:10] > a and float(r) > 0:
                f *= float(r)
        except (TypeError, ValueError):
            continue
    return f if f > 0 else 1.0


def px_bucket(raw) -> str | None:
    if raw is None or not np.isfinite(raw):
        return None
    return "lt1" if raw < PX_CUTS[0] else ("1to5" if raw < PX_CUTS[1] else "ge5")


def tercile(x, cuts) -> int | None:
    if x is None or cuts is None or not np.isfinite(x):
        return None
    return 0 if x <= cuts[0] else 1 if x <= cuts[1] else 2


def cuts_of(vals):
    v = np.asarray([x for x in vals if x is not None and np.isfinite(x)], float)
    if len(v) < 3:
        return None
    return float(np.percentile(v, 100 / 3.0)), float(np.percentile(v, 200 / 3.0))


def regime_map(df) -> dict:
    """{يوم: BULL · BEAR · SIDE} من إطار مؤشّر (IWM): صاعد = الإغلاق فوق SMA200 وSMA50 فوق SMA200 · هابط = عكسُهما · وإلّا عرضيّ ·
    وقبل اكتمال 200 جلسة ⟵ غائب (§②)."""
    if df is None or not len(df):
        return {}
    c = df["Close"].astype(float)
    s50, s200 = c.rolling(50).mean(), c.rolling(200).mean()
    out = {}
    for d, x, a, b in zip(df.index, c, s50, s200):
        if not (np.isfinite(a) and np.isfinite(b)):
            continue
        out[str(d)[:10]] = "BULL" if (x > b and a > b) else ("BEAR" if (x < b and a < b) else "SIDE")
    return out


def boot_diff(sig_vals, ctrl_lists, alpha: float = EXPL_ALPHA, b: int = BOOT_B, seed: int = BOOT_SEED) -> dict:
    """**الفرقُ المطابَق** (§⑦): لكلّ إشارةٍ لها ضبط ⟵ قيمتُها − متوسّطُ ضبطها المطابَق · والتقديرُ متوسّطُ هذه الفروق على الإشارات
    (فلا تثقل إشارةٌ لها ضبطٌ أكثر) · والفاصلُ **بوتستراب عنقوديّ** (تُعاد عيّنةُ الإشارات بضبطها = إعادةُ عيّنة الفروق) ⟵
    {diff · lo · hi · n_sig · n_ctrl · mean_sig · mean_ctrl} · وبلا ضبطٍ ⟵ قيمٌ None. للنسب: القيمُ 0/1."""
    pairs = [(float(s), [float(x) for x in cl if x is not None and np.isfinite(x)])
             for s, cl in zip(sig_vals, ctrl_lists) if s is not None and np.isfinite(s)]
    pairs = [(s, cl) for s, cl in pairs if cl]
    out = {"n_sig": len(pairs), "n_ctrl": sum(len(cl) for _s, cl in pairs), "diff": None, "lo": None, "hi": None,
           "mean_sig": None, "mean_ctrl": None}
    if not pairs:
        return out
    sv = np.asarray([s for s, _ in pairs], float)
    cm = np.asarray([float(np.mean(cl)) for _s, cl in pairs], float)
    d = sv - cm
    out["mean_sig"], out["mean_ctrl"], out["diff"] = float(sv.mean()), float(cm.mean()), float(d.mean())
    rng = np.random.default_rng(seed)
    n = len(d)
    ds = np.asarray([d[rng.integers(0, n, n)].mean() for _ in range(b)])
    out["lo"], out["hi"] = float(np.percentile(ds, 100 * alpha / 2)), float(np.percentile(ds, 100 * (1 - alpha / 2)))
    return out


def boot_ci(vals, stat: str = "mean", alpha: float = EXPL_ALPHA, b: int = BOOT_B, seed: int = BOOT_SEED) -> dict:
    """فاصلُ بوتستراب لإحصاءٍ واحد (`mean` · `median` · `rate` للقيم 0/1)."""
    v = np.asarray([x for x in vals if x is not None and np.isfinite(x)], float)
    if not len(v):
        return {"n": 0, "est": None, "lo": None, "hi": None}
    f = np.median if stat == "median" else np.mean
    rng = np.random.default_rng(seed)
    ds = np.asarray([f(v[rng.integers(0, len(v), len(v))]) for _ in range(b)])
    return {"n": int(len(v)), "est": float(f(v)), "lo": float(np.percentile(ds, 100 * alpha / 2)),
            "hi": float(np.percentile(ds, 100 * (1 - alpha / 2)))}


def dist_q(vals) -> dict:
    """`HS.dist` ‏+ المئينان 5 و95 ‏+ نسبةُ الموجب (لا يُخفى شاذّ)."""
    d = HS.dist(vals)
    x = np.asarray([v for v in vals if v is not None and np.isfinite(v)], float)
    if len(x):
        d.update(p5=float(np.percentile(x, 5)), p95=float(np.percentile(x, 95)), win=float(np.mean(x > 0)))
    return d


def profit_factor(rets) -> float | None:
    x = np.asarray([v for v in rets if v is not None and np.isfinite(v)], float)
    neg = -x[x < 0].sum()
    return float(x[x > 0].sum() / neg) if neg > 0 else None


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ② القياسُ لكلّ إشارة ولكلّ حدث ضبط
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def arrays(df) -> dict:
    o, h, l, c, v = HS._arrays(df)
    return {"o": o, "h": h, "l": l, "c": c, "v": v, "atr": HS.atr_np(h, l, c, HS.STRICT["atr_n"]),
            "dates": [str(x)[:10] for x in df.index]}


def measure(A: dict, sig: dict, e: int, E: float, rt: dict = None) -> dict:
    """§⑤ لإشارةٍ مكتشَفة: الأهدافُ T-C/T-100 · الإبطالاتُ I1/I2/I3 · الأحداث لكلّ (هدف × إبطال × نافذة) · التسلسل · العوائد · MFE/MAE · الأقواسُ الثلاثة."""
    o, h, l, c = A["o"], A["h"], A["l"], A["c"]
    tg = {"TC": sig.get("target"), "T100": 2.0 * E}
    st = {"I1": sig["head_px"], "I2": sig["rs_px"], "I3": sig["head_px"]}
    fail_i = (rt or {}).get("fail_i")
    rec = {"e": int(e), "e_date": A["dates"][e], "E": float(E),
           "tgt_pct": (float(tg["TC"] / E - 1.0) if tg["TC"] is not None else None),
           "i1_pct": float(st["I1"] / E - 1.0), "i2_pct": float(st["I2"] / E - 1.0)}
    rec.update(rets_at(c, e, E))
    for w in WINS:
        rec[f"mfe{w}"], rec[f"mae{w}"] = excursion(h, l, e, E, w)
    ev = {}
    for tgk, stk, w in EVENT_SET:
        eb = event_bars(h, c, e, tg[tgk], st[stk], w, extra_stop_i=(fail_i if stk == "I3" else None))
        ev[f"{tgk}|{stk}|{w}"] = None if eb is None else {"cls": classify(*eb), "t_tgt": eb[0], "t_stop": eb[1]}
    rec["ev"] = ev
    k = ev.get("TC|I3|60")
    ti = (rt or {}).get("touch_i")
    touch_rel = (int(ti) - e) if ti is not None and int(ti) > e else None
    rec["seq"] = None if k is None else seq_label(k["t_tgt"], k["t_stop"], touch_rel)
    for bk, (tgk, stk, w) in BRACKETS.items():
        rec[bk] = bracket(o, h, c, e, E, tg[tgk], st[stk], w)
    return rec


def measure_ctrl(A: dict, e: int, E: float, tgt_pct, i1_pct, i2_pct) -> dict:
    """حدثُ ضبطٍ **بقوس الإشارة المطابَقة منسوخًا نسبيًّا** (§⑥): الهدفُ E×(1+هدف%) والوقفان كذلك ⟵ CLEAN لـ(T-C · I2/I1 · 60) والأقواسُ الثلاثة."""
    o, h, c = A["o"], A["h"], A["c"]
    if tgt_pct is None or not E > 0:
        return {}
    t_c, s1, s2 = E * (1 + tgt_pct), E * (1 + i1_pct), E * (1 + i2_pct)
    out = {}
    for name, stp in (("I2", s2), ("I1", s1)):
        eb = event_bars(h, c, e, t_c, stp, 60)
        out[f"clean_{name}"] = None if eb is None else (1.0 if classify(*eb) == "CLEAN" else 0.0)
    out["B1"] = bracket(o, h, c, e, E, t_c, s2, 60)
    out["B2"] = bracket(o, h, c, e, E, t_c, s1, 60)
    out["B3"] = bracket(o, h, c, e, E, 2.0 * E, s2, 90)
    return out


def sig_base(s: dict, A: dict, sp_pairs, sp_dates, regime: dict) -> dict:
    """حقولُ الإشارة الثابتة: الحقبة · الصلاحية (`T-HS`) · العنق · الارتفاع · الزخم · ATR% · السعرُ الخامّ وفئتُه · قيمةُ التداول · نظامُ السوق."""
    b, d = int(s["b_i"]), str(s["b_date"])[:10]
    c, v, atr = A["c"], A["v"], A["atr"]
    E = float(c[b])
    raw = E * split_factor_after(sp_pairs, d) if sp_pairs is not None else None
    lo = max(0, b - 20)
    dv = float(np.nanmedian(c[lo:b] * v[lo:b])) if b > lo and np.isfinite(v[lo:b]).any() else None
    return {"sym": s.get("sym"), "pid": s.get("pid"), "b_date": d, "era": era_of(d), "year": int(d[:4]),
            "ls_date": s.get("ls_date"), "head_date": s.get("head_date"), "rs_date": s.get("rs_date"),
            "split_win": (None if sp_dates is None else HS.split_in_window(sp_dates, str(s["ls_date"])[:10],
                                                                          HS._plus_days(d, SPLIT_PAD))),
            "neck_type": s.get("neck_type"), "compound": bool(s.get("compound")), "quality": s.get("quality"),
            "width": int(s.get("width") or 0), "height": float(s["height"]), "height_pct": float(s["height"] / E) if E > 0 else None,
            "neck_b": float(s["neck_b"]), "target": s.get("target"), "head_px": float(s["head_px"]), "rs_px": float(s["rs_px"]),
            "ls_px": float(s["ls_px"]), "p0_px": s.get("p0_px"), "b_i": b, "ls_i": int(s["ls_i"]), "head_i": int(s["head_i"]),
            "rs_i": int(s["rs_i"]), "p0_i": s.get("p0_i"), "p1_i": s.get("p1_i"), "p2_i": s.get("p2_i"),
            "ret20_prior": (float(c[b] / c[b - 20] - 1.0) if b >= 20 and c[b - 20] > 0 else None),
            "atr_pct": (float(atr[b] / E) if E > 0 and np.isfinite(atr[b]) else None),
            "raw_px": (float(raw) if raw is not None else None), "px_bucket": px_bucket(raw), "dv": dv,
            "regime": (regime or {}).get(d)}


def lookahead(df, s: dict, p: dict) -> dict:
    """§⑨: `detect(df[:b+1])` يُعيد الإشارةَ نفسَها (المعرّف والبار) · وآخرُ محورٍ مستعمل يتأكّد عند ‏≤ b · والكتفُ الأيمن قبل b."""
    b = int(s["b_i"])
    sub = HS.detect(df.iloc[:b + 1], p, sym=s.get("sym", ""))
    ok = any(x["pid"] == s["pid"] and int(x["b_i"]) == b for x in sub)
    piv = [s.get(k) for k in ("p0_i", "ls_i", "p1_i", "head_i", "p2_i") if s.get(k) is not None]
    conf = max(int(i) + int(p["k"]) for i in piv) if piv else None
    info_ok = conf is not None and conf <= b and int(s["rs_i"]) < b
    return {"prefix_ok": bool(ok), "info_ok": bool(info_ok), "max_confirm": conf}


def skeleton_events(df, A: dict, kind: str) -> list:
    """خطّا الأساس البنيويّان (§⑥) — مشيٌ سببيٌّ بالزجزاج نفسِه (`HS.fractal_swings` · `HS.zz_add` · k وATR من STRICT):
    **D** «بلا شرط الرأس»: قاع(كتف) · قمّة P1 · قاعٌ أوسط · قمّة P2 ثمّ الكتفُ الأيمن = أدنى ما بعد P2 — بقواعد CURRENT للعنق والكتفين والارتفاع والاتّجاه
    السابق **والقاعُ الأوسط ليس الأدنى** (يستبعد الرأس والكتفين نفسَه) · **E** «عنقٌ بلا نموذج»: قمّتان متتاليتان فرقُهما ‏≤ 0.1 من المدى بينهما.
    الاختراقُ أوّلُ إغلاقٍ ‏≥ الخطّ ‏+ 0.1 ATR بعد تأكّد القمّة الثانية وخلال صلاحيةٍ كـCURRENT. ⟵ [{b_i · E · height · line}]."""
    p = P_C
    k, swa = int(p["k"]), float(p["swing_atr"])
    h, l, c, a = A["h"], A["l"], A["c"], A["atr"]
    sw = HS.fractal_swings(h, l, k)
    Z, si, out, used = [], 0, [], set()
    n = len(c)
    for t in range(n):
        while si < len(sw) and sw[si][0] + k <= t:
            HS.zz_add(Z, sw[si], a[sw[si][0] + k], swa)
            si += 1
        if len(Z) < 3 or not np.isfinite(a[t]) or a[t] <= 0:
            continue
        j = len(Z) - 1 if Z[-1][1] == "H" else len(Z) - 2
        if j < 2 or Z[j][1] != "H":
            continue
        if kind == "E":
            ha, lm, hb = Z[j - 2], Z[j - 1], Z[j]
            key = (ha[0], hb[0])
            if key in used:
                continue
            rng = max(ha[2], hb[2]) - lm[2]
            if not rng > 0 or abs(hb[2] - ha[2]) > 0.1 * rng or t - hb[0] > 60 or t - hb[0] < 2:
                continue
            line = max(ha[2], hb[2])
            thr = line + p["brk_atr"] * a[t]
            if not c[t] >= thr:
                continue
            xs = np.arange(hb[0] + 1, t)
            if len(xs) and np.any(c[xs] >= line + p["brk_atr"] * a[xs]):
                used.add(key)
                continue
            used.add(key)
            out.append({"b_i": t, "E": float(c[t]), "height": float(rng), "line": float(line)})
            continue
        if j < 4:
            continue
        p0, l1, h1, l2, h2 = Z[j - 4], Z[j - 3], Z[j - 2], Z[j - 1], Z[j]
        if p0[1] != "H" or l1[1] != "L" or l2[1] != "L":
            continue
        key = (l1[0], l2[0])
        if key in used or (t - h2[0]) < 2:
            continue
        seg = l[h2[0] + 1:t]
        if not len(seg) or not np.isfinite(seg).any():
            continue
        rs_i = h2[0] + 1 + int(np.nanargmin(seg))
        rs = float(l[rs_i])
        slope = (h2[2] - h1[2]) / float(h2[0] - h1[0])

        def neck(x, _h1=h1, _s=slope):
            return _h1[2] + _s * (x - _h1[0])
        lo3 = min(l1[2], l2[2], rs)
        height = neck(l2[0]) - lo3
        if not height > 0:
            continue
        if l2[2] < l1[2] and l2[2] < rs:                       # هذا رأسٌ وكتفان ⟵ ليس هذا الخطّ
            continue
        if height < p["height_min_atr"] * a[t] or height < p["height_min_pct"] * abs(c[t]):
            continue
        if abs(l1[2] - rs) > p["shoulder_tol"] * height or abs(h2[2] - h1[2]) > p["neck_slope"] * height:
            continue
        if neck(l1[0]) - l1[2] < p["shoulder_depth"] * height or neck(rs_i) - rs < p["shoulder_depth"] * height:
            continue
        if p0[2] - l1[2] < p["prior_drop"] * height or l1[0] - p0[0] < p["prior_bars"]:
            continue
        d2 = rs_i - l2[0]
        if d2 < 1 or t - rs_i > max(k + 1, p["wait_mult"] * d2):
            continue
        thr = neck(t) + p["brk_atr"] * a[t]
        if not c[t] >= thr:
            continue
        xs = np.arange(h2[0] + 1, t)
        if len(xs) and np.any(c[xs] >= neck(xs) + p["brk_atr"] * a[xs]):
            used.add(key)
            continue
        used.add(key)
        out.append({"b_i": t, "E": float(c[t]), "height": float(height), "line": float(neck(t))})
    return out


def ctrl_base(A: dict, b: int, E: float, height: float, sp_dates, regime: dict, wb: int = None, back: int = 60) -> dict:
    """حقولُ حدث الضبط (مطابقةُ §⑥) ‏+ العوائد عند الآفاق (مستقلّةٌ عن الإشارة) · والصلاحيةُ بنافذة [b − back · b + 45 يومًا]."""
    c, v, atr, dates = A["c"], A["v"], A["atr"], A["dates"]
    d = dates[b]
    d0 = dates[max(0, b - (wb or back))]
    lo = max(0, b - 20)
    dv = float(np.nanmedian(c[lo:b] * v[lo:b])) if b > lo and np.isfinite(v[lo:b]).any() else None
    out = {"b_i": int(b), "b_date": d, "era": era_of(d), "year": int(d[:4]), "E": float(E), "wb": wb,
           "range_pct": (float(height / E) if E > 0 else None),
           "ret20_prior": (float(c[b] / c[b - 20] - 1.0) if b >= 20 and c[b - 20] > 0 else None),
           "atr_pct": (float(atr[b] / E) if E > 0 and np.isfinite(atr[b]) else None), "dv": dv,
           "regime": (regime or {}).get(d),
           "split_win": (None if sp_dates is None else HS.split_in_window(sp_dates, d0, HS._plus_days(d, SPLIT_PAD)))}
    out.update(rets_at(c, b, E))
    for w in WINS:
        out[f"mfe{w}"], out[f"mae{w}"] = excursion(A["h"], A["l"], b, E, w)
    return out


def bl_a(A: dict, s: dict, rec: dict, sp_dates) -> list:
    """BL-A «امتلاكٌ مطابَق» (§⑥): حتى 10 أيّامٍ عشوائيّة من **الرمز والسنة نفسَيهما** (بعيدةً عن الإشارة بأكثر من 5 بارات · بذرة `crc32(pid|A)`) ·
    بقوس الإشارة منسوخًا نسبيًّا · والصلاحيةُ بنافذة [اليوم − 60 بارًا · +45 يومًا]."""
    dates, c = A["dates"], A["c"]
    yr = str(rec["year"])
    b = int(s["b_i"])
    cand = [i for i in range(25, len(dates)) if dates[i][:4] == yr and abs(i - b) > 5 and c[i] > 0]
    if not cand:
        return []
    rng = np.random.default_rng(zlib.crc32(f"{s['pid']}|A".encode("utf-8")))
    pick = sorted(rng.choice(len(cand), size=min(N_CTRL, len(cand)), replace=False))
    out = []
    for j in pick:
        i = cand[int(j)]
        d0 = dates[max(0, i - 60)]
        valid = None if sp_dates is None else not HS.split_in_window(sp_dates, d0, HS._plus_days(dates[i], SPLIT_PAD))
        r = measure_ctrl(A, i, float(c[i]), rec.get("tgt_pct"), rec.get("i1_pct"), rec.get("i2_pct"))
        r.update(rets_at(c, i, float(c[i])))
        r["valid"] = valid
        out.append(r)
    return out


def head_distinct(A: dict, s: dict, q: float = RX_Q) -> dict:
    """`T-HS-RX §④` — تميّزُ الرأس (من القراءة التشغيليّة للتدقيق الأعمى · لا من عائد):
    **HD1** «أدنى بجسمه»: ‏min(Open, Close) لبار الرأس (وبارِه الثاني إن كان مركّبًا `pm_i`) ‏≤ min(LS, RS) − q × الارتفاع ·
    **HD2** «لا قاعَ قبله بمستواه»: أدنى Low في W = (rs_i − ls_i) بارًا قبل الكتف الأيسر **أعلى من** قاع الرأس ‏+ q × الارتفاع —
    وبلا بارٍ قبله لا تتحقّق (مُحافِظ). يقرأ بارات ‏≤ الكتف الأيمن وحدَها (قبل الاختراق) ⟵ القيمُ مع الحكم."""
    o, c, low = A["o"], A["c"], A["l"]
    H = float(s["height"])
    bars = [int(s["head_i"])] + ([int(s["pm_i"])] if s.get("pm_i") is not None else [])
    body = min(min(float(o[i]), float(c[i])) for i in bars)
    shoulders = min(float(s["ls_px"]), float(s["rs_px"]))
    ls_i = int(s["ls_i"])
    w = max(1, int(s["rs_i"]) - ls_i)
    seg = np.asarray(low[max(0, ls_i - w):ls_i], float)
    seg = seg[np.isfinite(seg)]
    prior = float(seg.min()) if len(seg) else None
    return {"hd1": bool(H > 0 and body <= shoulders - q * H),
            "hd2": bool(H > 0 and prior is not None and prior > float(s["head_px"]) + q * H),
            "hd_body_gap": (float((shoulders - body) / H) if H > 0 else None),
            "hd_prior_gap": (float((prior - float(s["head_px"])) / H) if prior is not None and H > 0 else None), "hd_w": int(w)}


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ③ رمزٌ واحد (يُشغَّل في عمليّةٍ مستقلّة)
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def analyze_sym(task) -> dict:
    """(رمز · إطار · أزواجُ التقسيم · تواريخُها · نظامُ السوق · الوضع) ⟵ الإشاراتُ بمداخلها وقياسها ‏+ أحداثُ الضبط ‏+ الهيكلان (main) ‏+ النظرُ المستقبليّ (main)."""
    sym, df, sp_pairs, sp_dates, regime, mode = task
    A = arrays(df)
    out = {"sym": sym, "n": len(df), "first": A["dates"][0] if len(df) else None, "last": A["dates"][-1] if len(df) else None,
           "C": [], "D": [], "A": [], "B": [], "ctrl": [], "skD": [], "skE": [], "err": None}
    try:
        sigs = HS.detect(df, P_C, sym=sym)
        for s in sigs:
            rt = HS.retest_state(df, s, P_C)
            base = sig_base(s, A, sp_pairs, sp_dates, regime)
            rec = dict(base, entry="C", retest=rt["retest"], **measure(A, s, int(s["b_i"]), float(A["c"][s["b_i"]]), rt))
            if mode == "main":
                rec["la"] = lookahead(df, s, P_C)
            rec["blA"] = bl_a(A, s, rec, sp_dates)
            out["C"].append(rec)
            if rt["retest"] == "success" and rt["cont_i"] is not None:
                e = int(rt["cont_i"])
                rec_d = dict(base, entry="D", retest=rt["retest"], **measure(A, s, e, float(A["c"][e]), None))
                if mode == "rx":                                     # T-HS-RX §④/§⑥/§⑨ (main وndq بت-بت)
                    rec_d.update(head_distinct(A, s))
                    rec_d["blA"] = bl_a(A, dict(s, b_i=e, pid=f"{s['pid']}|D"), dict(rec_d, year=int(A["dates"][e][:4])), sp_dates)
                    if rec_d.get("neck_type") == "horizontal" and rec_d["hd1"] and rec_d["hd2"]:
                        rec_d["la"] = lookahead(df, s, P_C)
                out["D"].append(rec_d)
        if mode == "main":
            for s in HS.detect(df, P_B, sym=sym):
                rt = HS.retest_state(df, s, P_B)
                out["B"].append(dict(sig_base(s, A, sp_pairs, sp_dates, regime), entry="B", retest=rt["retest"],
                                     **measure(A, s, int(s["b_i"]), float(A["c"][s["b_i"]]), rt)))
            for s in HS.detect(df, P_A, sym=sym):
                b = int(s["b_i"])
                E = float(max(A["o"][b], s["thr_b"]))
                rt = HS.retest_state(df, s, P_A)
                out["A"].append(dict(sig_base(s, A, sp_pairs, sp_dates, regime), entry="A", retest=rt["retest"],
                                     **measure(A, s, b, E, rt)))
        for ev in HS.control_events(df, sig_bars={int(s["b_i"]) for s in sigs}):
            out["ctrl"].append(dict(ctrl_base(A, int(ev["b_i"]), float(ev["entry"]), float(ev["height"]), sp_dates, regime,
                                              wb=int(ev["wb"])), sym=sym))
        if mode == "main":
            for kind, key in (("D", "skD"), ("E", "skE")):
                for ev in skeleton_events(df, A, kind):
                    out[key].append(dict(ctrl_base(A, int(ev["b_i"]), ev["E"], ev["height"], sp_dates, regime), sym=sym))
    except Exception as e:                                                   # noqa: BLE001
        out["err"] = f"{type(e).__name__}: {e}"
    return out


def sens_sym(task) -> dict:
    """الحساسيّة (§⑧): لكلّ متغيّر ⟵ إشاراتُ الحقب المطلوبة بقياسها (القوسُ الأساسيّ · CLEAN · ret30) على إطارٍ مقصوص."""
    sym, df, sp_dates, variants, eras = task
    A = arrays(df)
    res = {}
    try:
        for name, p in variants.items():
            rows = []
            for s in HS.detect(df, p, sym=sym):
                d = str(s["b_date"])[:10]
                era = era_of(d)
                if era not in eras:
                    continue
                if sp_dates is None or HS.split_in_window(sp_dates, str(s["ls_date"])[:10], HS._plus_days(d, SPLIT_PAD)):
                    continue
                rt = HS.retest_state(df, s, p)
                m = measure(A, s, int(s["b_i"]), float(A["c"][s["b_i"]]), rt)
                ev = m["ev"].get("TC|I2|60")
                rows.append({"pid": s["pid"], "era": era, "B1": (m["B1"] or {}).get("ret"),
                             "clean": (None if ev is None else (1.0 if ev["cls"] == "CLEAN" else 0.0)), "ret30": m.get("ret30")})
            res[name] = rows
    except Exception as e:                                                   # noqa: BLE001
        res["__err__"] = f"{type(e).__name__}: {e}"
    return {"sym": sym, "res": res}


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ④ المطابقةُ والإحصاء (العمليّةُ الرئيسة)
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def valid(r) -> bool:
    return r.get("split_win") is False


def pick(pool: list, key: str, m: int = N_CTRL) -> list:
    if not pool:
        return []
    rng = np.random.default_rng(zlib.crc32(key.encode("utf-8")))
    return [pool[i] for i in rng.choice(len(pool), size=min(m, len(pool)), replace=False)]


def match_controls(sigs: list, pool: list, kind: str) -> dict:
    """{pid: [أحداث ضبط]} — **B**: السنة · نافذةُ العرض · ثلثُ الزخم (`T-HS` نفسُه) · **C**: B ∩ مدى النطاق بين نصف ضعفَي ارتفاع النموذج ·
    **D/E**: السنة · ثلثُ الزخم · **F**: السنة · ثلثُ ATR% · فئةُ السعر الخامّ · ثلثُ قيمة التداول · نظامُ السوق (والرمزُ نفسُه أوّلًا إن وُجد منه ثلاثة)."""
    by_year = {}
    for c in pool:
        if valid(c):
            by_year.setdefault(c["year"], []).append(c)
    out = {}
    for y, ys in by_year.items():
        mc = cuts_of([c.get("ret20_prior") for c in ys])
        ac = cuts_of([c.get("atr_pct") for c in ys])
        dc = cuts_of([c.get("dv") for c in ys])
        strata = {}
        for c in ys:
            if kind in ("B", "C"):
                k = (c.get("wb"), tercile(c.get("ret20_prior"), mc))
            elif kind in ("D", "E"):
                k = (tercile(c.get("ret20_prior"), mc),)
            else:
                k = (tercile(c.get("atr_pct"), ac), px_bucket(c.get("raw_px")) if c.get("raw_px") is not None
                     else c.get("px_bucket"), tercile(c.get("dv"), dc), c.get("regime"))
            strata.setdefault(k, []).append(c)
        for s in sigs:
            if s["year"] != y or not valid(s):
                continue
            if kind in ("B", "C"):
                k = (HS.w_bucket(s["width"]), tercile(s.get("ret20_prior"), mc))
            elif kind in ("D", "E"):
                k = (tercile(s.get("ret20_prior"), mc),)
            else:
                k = (tercile(s.get("atr_pct"), ac), s.get("px_bucket"), tercile(s.get("dv"), dc), s.get("regime"))
            cand = strata.get(k, [])
            if kind == "C":
                hp = s.get("height_pct")
                cand = [c for c in cand if hp and c.get("range_pct") and 0.5 * hp <= c["range_pct"] <= 2.0 * hp]
            if kind == "F":
                same = [c for c in cand if c.get("sym") == s.get("sym")]
                cand = same if len(same) >= 3 else cand
            out[s["pid"] + "|" + s["entry"]] = pick(cand, f"{s['pid']}|{s['entry']}|{kind}")
    return out


def ctrl_outcomes(sig: dict, ctrls: list, frames_arr: dict) -> list:
    """قوسُ الإشارة منسوخًا على كلّ حدث ضبطٍ مطابَق (`measure_ctrl`) ‏+ عوائدُه المحسوبة سلفًا."""
    out = []
    for c in ctrls:
        A = frames_arr.get(c["sym"])
        if A is None:
            continue
        r = measure_ctrl(A, int(c["b_i"]), float(c["E"]), sig.get("tgt_pct"), sig.get("i1_pct"), sig.get("i2_pct"))
        r.update({k: c.get(k) for k in [f"ret{x}" for x in HZ] + [f"mfe{w}" for w in WINS] + [f"mae{w}" for w in WINS]})
        out.append(r)
    return out


def _bget(x, k="ret"):
    return None if not x else x.get(k)


def clean_of(r, key="TC|I2|60"):
    ev = (r.get("ev") or {}).get(key)
    return None if ev is None else (1.0 if ev["cls"] == "CLEAN" else 0.0)


def summarize(recs: list) -> dict:
    """الجداولُ الوصفيّة لمجموعة إشارات (صالحة): العوائدُ لكلّ أفق · MFE/MAE · الأحداثُ لكلّ (هدف × إبطال × نافذة) · الأزمنة · التسلسل · الأقواس."""
    rs = [r for r in recs if valid(r)]
    out = {"n": len(rs), "n_all": len(recs),
           "horizontal": sum(1 for r in rs if r.get("neck_type") == "horizontal"),
           "compound": sum(1 for r in rs if r.get("compound"))}
    for x in HZ:
        vals = [r.get(f"ret{x}") for r in rs]
        out[f"ret{x}"] = dist_q(vals)
        if x in (10, 30, 60):
            out[f"ret{x}_ci_mean"] = boot_ci(vals, "mean")
            out[f"ret{x}_ci_median"] = boot_ci(vals, "median")
    for w in WINS:
        out[f"mfe{w}"] = dist_q([r.get(f"mfe{w}") for r in rs])
        out[f"mae{w}"] = dist_q([r.get(f"mae{w}") for r in rs])
    out["mfe30_ci_median"] = boot_ci([r.get("mfe30") for r in rs], "median")
    out["mae30_ci_median"] = boot_ci([r.get("mae30") for r in rs], "median")
    evs = {}
    for tgk, stk, w in EVENT_SET:
        key = f"{tgk}|{stk}|{w}"
        cl = [(r.get("ev") or {}).get(key) for r in rs]
        cl = [x for x in cl if x is not None]
        cnt = {k: sum(1 for x in cl if x["cls"] == k) for k in ("CLEAN", "DIRTY", "STOP", "NEITHER")}
        n = len(cl)
        evs[key] = {"n": n, **cnt, "clean_rate": (cnt["CLEAN"] / n if n else None),
                    "dirty_hit_rate": ((cnt["CLEAN"] + cnt["DIRTY"]) / n if n else None),
                    "wilson_clean": HS.wilson(cnt["CLEAN"], n),
                    "t_tgt_clean": HS.dist([x["t_tgt"] for x in cl if x["cls"] == "CLEAN"]),
                    "t_stop": HS.dist([x["t_stop"] for x in cl if x["t_stop"] is not None])}
    out["events"] = evs
    sq = [r.get("seq") for r in rs if r.get("seq")]
    out["seq"] = {k: sq.count(k) for k in SEQS}
    out["seq_n"] = len(sq)
    rt = [r.get("retest") for r in rs if r.get("retest")]
    out["retest"] = {k: rt.count(k) for k in sorted(set(rt))}
    for bk in BRACKETS:
        bs = [r.get(bk) for r in rs if r.get(bk)]
        rets = [b["ret"] for b in bs]
        out[bk] = {"n": len(bs), "mean": boot_ci(rets, "mean"), "median": (float(np.median(rets)) if rets else None),
                   "win": (float(np.mean(np.asarray(rets) > 0)) if rets else None), "pf": profit_factor(rets),
                   "meanR": (float(np.mean([b["R"] for b in bs if b.get("R") is not None])) if any(b.get("R") is not None for b in bs) else None),
                   "why": {k: sum(1 for b in bs if b["why"] == k) for k in ("target", "stop", "time")},
                   "dist": dist_q(rets)}
    return out


def compare(sigs: list, matched: dict, frames_arr: dict, alpha: float = EXPL_ALPHA) -> dict:
    """الإشاراتُ مقابل ضبطها المطابَق (§⑥): CLEAN (T-C · I2/I1 · 60) · الأقواسُ الثلاثة · العوائدُ ‏+10/30/60 — فرقٌ ببوتستراب عنقوديّ."""
    rows = []
    for s in sigs:
        if not valid(s):
            continue
        cs = matched.get(s["pid"] + "|" + s["entry"]) or []
        rows.append((s, [c for c in ctrl_outcomes(s, cs, frames_arr)]))
    out = {"n_sig": len(rows), "n_sig_matched": sum(1 for _s, cs in rows if cs)}
    for name, sv, cv in (
            ("clean_I2_60", lambda s: clean_of(s, "TC|I2|60"), lambda c: c.get("clean_I2")),
            ("clean_I1_60", lambda s: clean_of(s, "TC|I1|60"), lambda c: c.get("clean_I1")),
            ("B1", lambda s: _bget(s.get("B1")), lambda c: _bget(c.get("B1"))),
            ("B2", lambda s: _bget(s.get("B2")), lambda c: _bget(c.get("B2"))),
            ("B3", lambda s: _bget(s.get("B3")), lambda c: _bget(c.get("B3"))),
            ("ret10", lambda s: s.get("ret10"), lambda c: c.get("ret10")),
            ("ret30", lambda s: s.get("ret30"), lambda c: c.get("ret30")),
            ("ret60", lambda s: s.get("ret60"), lambda c: c.get("ret60"))):
        out[name] = boot_diff([sv(s) for s, _ in rows], [[cv(c) for c in cs] for _s, cs in rows], alpha=alpha)
    return out


def newcombe_clean(sigs: list, matched: dict, frames_arr: dict) -> dict:
    """Newcombe لفرق نسبتَي CLEAN (‏T-C · I2 · 60) — **ثانويٌّ يتجاهل المطابقة** (§⑦)."""
    k1 = n1 = k2 = n2 = 0
    for s in sigs:
        if not valid(s):
            continue
        x = clean_of(s, "TC|I2|60")
        cs = [c.get("clean_I2") for c in ctrl_outcomes(s, matched.get(s["pid"] + "|" + s["entry"]) or [], frames_arr)]
        cs = [c for c in cs if c is not None]
        if x is None or not cs:
            continue
        k1 += int(x)
        n1 += 1
        k2 += int(sum(cs))
        n2 += len(cs)
    if not n1 or not n2:
        return {"n1": n1, "n2": n2}
    d, lo, hi = HS.newcombe(k1, n1, k2, n2, z=2.394)            # z لـ98.33% ثنائيّ الطرف
    return {"k1": k1, "n1": n1, "k2": k2, "n2": n2, "diff": d, "lo": lo, "hi": hi}


def regime_tables(recs: list) -> dict:
    """الأنظمة (§⑧ · وصفٌ لا تفضيل): السوق · ثلثُ ATR% · فئةُ السعر الخامّ · ثلثُ قيمة التداول ⟵ n · نسبةُ CLEAN · متوسّطُ القوس الأساسيّ · وسيطُ ret30."""
    rs = [r for r in recs if valid(r)]
    ac = cuts_of([r.get("atr_pct") for r in rs])
    dc = cuts_of([r.get("dv") for r in rs])
    groups = {"regime": lambda r: r.get("regime"), "atr": lambda r: tercile(r.get("atr_pct"), ac),
              "px": lambda r: r.get("px_bucket"), "dv": lambda r: tercile(r.get("dv"), dc)}
    out = {"atr_cuts": ac, "dv_cuts": dc}
    for g, f in groups.items():
        d = {}
        for r in rs:
            d.setdefault(str(f(r)), []).append(r)
        out[g] = {k: {"n": len(v), "clean": (lambda cl: (float(np.mean(cl)) if cl else None))(
            [x for x in (clean_of(r) for r in v) if x is not None]),
            "B1_mean": (lambda bs: (float(np.mean(bs)) if bs else None))([_bget(r.get("B1")) for r in v if r.get("B1")]),
            "ret30_med": HS.dist([r.get("ret30") for r in v]).get("median")} for k, v in sorted(d.items())}
    return out


def hypotheses(bot: dict, ndq: dict = None) -> dict:
    """§⑦ على TEST: H1 (CLEAN مقابل BL-B) · H2 (القوس الأساسيّ CURRENT) · H3 (القوس RECON) — بونفيروني 98.33% · n ‏≥ 30 · والأضعف مع POP-NDQ.
    **بلا `ndq` (تشغيلةُ main وحدَها) ⟵ حالةٌ جزئيّة لا حكم** («POP-BOT فوق الصفر — بانتظار POP-NDQ») ولا تسميةَ FX."""
    out = {}
    partial = ndq is None
    for h, key, metric in (("H1", "C", "clean_I2_60"), ("H2", "C", "B1"), ("H3", "RECON", "B1")):
        cb = ((bot or {}).get(key) or {}).get(metric) or {}
        cn = ((ndq or {}).get(key) or {}).get(metric) or {}
        n = cb.get("n_sig") or 0
        bot_up = cb.get("lo") is not None and cb["lo"] > 0
        if n < MIN_N:
            st = "لا قياس"
        elif partial:
            st = "POP-BOT فوق الصفر — بانتظار POP-NDQ" if bot_up else "لا تُدعَم"
        elif bot_up and (cn.get("diff") is not None and cn["diff"] > 0):
            st = "تُدعَم"
        else:
            st = "لا تُدعَم"
        out[h] = {"status": st, "bot": cb, "ndq": cn}
    if partial:
        out["FX"] = None
        return out
    s_ = {k: v["status"] for k, v in out.items()}
    if s_["H1"] == "لا قياس" and s_["H2"] == "لا قياس":
        fx = "FX-4 «لا قياس»"
    elif s_["H3"] == "تُدعَم" and s_["H2"] != "تُدعَم":
        fx = "FX-1 «خطأُ بناء»"
    elif s_["H1"] == "تُدعَم" or s_["H2"] == "تُدعَم":
        fx = "FX-3 «المقياسُ القديم ظلم»"
    else:
        fx = "FX-2 «لا ميزة بأيّ بناء»"
    out["FX"] = fx
    return out


def run_verdict() -> int:
    """§⑦ **الحكمُ الآليّ** (بلا شبكة): يقرأ `fx_bot.json` و`fx_ndq.json` ⟵ `hypotheses` على كتلتَي TEST ⟵ `fx_verdict.json` ·
    وغيابُ أحدهما ⟵ خروج 3 بلا حكم (لا يُقرأ الحاكمُ وحدَه)."""
    paths = {k: os.path.join(FX_DIR, f"fx_{k}.json") for k in ("bot", "ndq")}
    if not all(os.path.exists(v) for v in paths.values()):
        log(f"⛔ لا حكم: ينقص {[k for k, v in paths.items() if not os.path.exists(v)]}")
        return 3
    js = {k: json.load(open(v, encoding="utf-8")) for k, v in paths.items()}
    tb = {k: (js["bot"].get("compare") or {}).get(f"{k}|TEST|BL-B") for k in ("C", "RECON")}
    tn = {k: (js["ndq"].get("compare") or {}).get(f"{k}|TEST|BL-B") for k in ("C", "RECON")}
    hyp = hypotheses(tb, tn)
    out = {"tool": TOOL, "mode": "verdict", "generated": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
           "inputs": {k: js[k].get("generated") for k in js}, "hypotheses": hyp,
           "newcombe_test": (js["bot"].get("compare") or {}).get("newcombe|TEST")}
    path = os.path.join(FX_DIR, "fx_verdict.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=str)
    log(f"⚖️ {hyp['FX']} · " + " · ".join(f"{h}: {hyp[h]['status']}" for h in ("H1", "H2", "H3")))
    _save([path])
    return 0


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ⑤ العيّنات (الإعادةُ البصريّة · التدقيقُ الأعمى) وإجراءاتُ الشركات
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def seg_export(df, r: dict, after: int = 90) -> dict:
    """شموعُ الإعادة البصريّة: من (min(P0 · LS) − 25) حتى e+after ‏+ مؤشّراتُ النموذج نسبيّةً لبداية المقطع (§⑪)."""
    i0 = max(0, min(int(r.get("p0_i") or r["ls_i"]), int(r["ls_i"])) - 25)
    i1 = min(len(df), int(r["e"]) + after + 1)
    seg = df.iloc[i0:i1]
    rel = {k: (int(r[k]) - i0 if r.get(k) is not None else None) for k in ("p0_i", "ls_i", "p1_i", "head_i", "p2_i", "rs_i", "b_i", "e")}
    return {"sym": r["sym"], "pid": r["pid"], "b_date": r["b_date"], "rel": rel,
            "levels": {k: r.get(k) for k in ("neck_b", "target", "head_px", "rs_px", "ls_px", "E")},
            "neck_slope": None, "out": {k: r.get(k) for k in ("mfe30", "mae30", "ret10", "ret30", "ret60", "seq")},
            "B1": r.get("B1"), "bars": [[str(ix)[:10], float(o), float(h), float(l), float(c)] for ix, (o, h, l, c)
                                         in zip(seg.index, seg[["Open", "High", "Low", "Close"]].to_numpy())]}


def blind_bars(df, b: int, n: int = BLIND_BARS) -> list:
    """آخرُ n شمعةً حتى بار القرار **بلا تواريخ ولا رمز** (§⑫) — OHLC وحدَها."""
    seg = df.iloc[max(0, b - n + 1):b + 1]
    return [[float(o), float(h), float(l), float(c)] for o, h, l, c in seg[["Open", "High", "Low", "Close"]].to_numpy()]


def blind_mix(items: list, seed: int = MIX_SEED, prefix: str = "BX"):
    """خلطٌ حتميّ ⟵ (المخطّطات: {معرّف: شموع} · المفتاح: {معرّف: النوع والهويّة}) — **ملفّان منفصلان** · و`prefix` بادئةُ المعرّف (‏RX لـ`T-HS-RX`)."""
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(items))
    charts, key = {}, {}
    for j, i in enumerate(order):
        bid = f"{prefix}{j + 1:02d}"
        charts[bid] = items[int(i)]["bars"]
        key[bid] = {k: v for k, v in items[int(i)].items() if k != "bars"}
    return charts, key


def seal_key(obj) -> tuple:
    """مفتاحُ التدقيق الأعمى **مختومٌ** (§⑫): JSON ⟵ zlib ⟵ base64 — فلا يُقرأ بنظرةٍ عابرة ولا بـgrep قبل دفع الوسوم ·
    و`sha256` النصّ الصريح يُطبع في السجلّ فلا يُعدَّل بعده ⟵ (النصُّ المختوم · البصمة)."""
    import base64
    import hashlib
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return base64.b64encode(zlib.compress(raw, 9)).decode("ascii"), hashlib.sha256(raw).hexdigest()


def open_key(sealed: str):
    """عكسُ `seal_key` ⟵ (المفتاح · البصمة) — يُنادى **بعد** دفع الوسوم وحدَه."""
    import base64
    import hashlib
    raw = zlib.decompress(base64.b64decode(sealed.encode("ascii")))
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()


def corp_classify(maxlog, split_in, corp_in, have_y: bool) -> str:
    """§⑩: بلا مصدرٍ ثانٍ ⟵ UNVERIFIED · تقسيمٌ في النافذة ‏+ فرقُ مصدرين فوق 10% ⟵ SPLIT_ARTIFACT · فرقٌ فوق 10% ⟵ DATA_MISMATCH ·
    حدثُ شركةٍ في النافذة ⟵ CORP_EVENT · وإلّا REAL_MOVE."""
    if not have_y or maxlog is None:
        return "UNVERIFIED"
    big = maxlog > math.log(1.10)
    if split_in and big:
        return "SPLIT_ARTIFACT"
    if big:
        return "DATA_MISMATCH"
    if corp_in:
        return "CORP_EVENT"
    return "REAL_MOVE"


def corp_audit(cases: list, frames: dict, sp_pairs: dict) -> list:
    """ياهو (شموعٌ مسوّاة) مقابل TradingView في نافذة [LS − 30 يومًا · b + 150 يومًا] ‏+ تقسيماتُ ياهو ‏+ SEC (الأسماءُ السابقة · أوّلُ إيداع) ⟵ تصنيف §⑩."""
    import Super_stock as S
    import requests
    out = []
    cik_map = {}
    try:
        cik_map = S.sec_cik_map() or {}
    except Exception:                                                       # noqa: BLE001
        cik_map = {}
    for r in cases:
        sym = r["sym"]
        d0, d1 = HS._plus_days(str(r["ls_date"])[:10], -30), HS._plus_days(r["b_date"], 150)
        res = {"sym": sym, "pid": r["pid"], "b_date": r["b_date"], "mfe30": r.get("mfe30"), "mae30": r.get("mae30"),
               "E": r.get("E"), "raw_px": r.get("raw_px"), "dv": r.get("dv")}
        res["src"] = r.get("src", "fx")
        if sym not in frames:
            res["tv_missing"] = True
            res["class"] = "UNVERIFIED"
            out.append(res)
            continue
        pairs = sp_pairs.get(sym) or []
        res["splits_in_window"] = [(d, rr) for d, rr in pairs if d0 <= str(d)[:10] <= d1]
        res["splits_all"] = pairs[-8:]
        maxlog, have_y = None, False
        try:
            yd = S.yf.download(sym, start=d0, end=HS._plus_days(d1, 1), auto_adjust=False, progress=False, threads=False)
            if yd is not None and len(yd):
                if isinstance(yd.columns, pd.MultiIndex):
                    yd.columns = yd.columns.get_level_values(0)
                ys = yd["Close"].astype(float)
                ys.index = [str(x)[:10] for x in ys.index]
                tv = frames[sym]["Close"].astype(float)
                tv.index = [str(x)[:10] for x in tv.index]
                jj = sorted(set(ys.index) & set(tv.index))
                jj = [d for d in jj if d0 <= d <= d1]
                if jj:
                    lr = np.abs(np.log(np.asarray([tv[d] for d in jj]) / np.asarray([ys[d] for d in jj])))
                    lr = lr[np.isfinite(lr)]
                    if len(lr):
                        maxlog, have_y = float(lr.max()), True
                        res["tv_yh_median_ratio"] = float(np.exp(np.median(np.log(np.asarray([tv[d] for d in jj])
                                                                                 / np.asarray([ys[d] for d in jj])))))
                res["yh_bars"] = len(jj)
        except Exception as e:                                               # noqa: BLE001
            res["yh_err"] = type(e).__name__
        res["tv_yh_maxlog"] = maxlog
        corp_in = False
        cik = cik_map.get(sym.upper())
        res["cik"] = cik
        if cik:
            try:
                js = requests.get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json", headers=S.SEC_UA, timeout=30).json()
                fn = js.get("formerNames") or []
                res["former_names"] = [{"name": x.get("name"), "from": str(x.get("from"))[:10], "to": str(x.get("to"))[:10]} for x in fn]
                corp_in = any(d0 <= str(x.get("to"))[:10] <= d1 for x in fn if x.get("to"))
                rec = (js.get("filings") or {}).get("recent") or {}
                ds = sorted(x for x in (rec.get("filingDate") or []) if x)
                files = (js.get("filings") or {}).get("files") or []
                earliest = min([ds[0]] if ds else [] + [str(f.get("filingFrom"))[:10] for f in files if f.get("filingFrom")]) if (ds or files) else None
                res["sec_earliest"] = earliest
                res["sec_name"] = js.get("name")
                tv_first = str(frames[sym].index[0])[:10]
                res["reuse_suspect"] = bool(earliest and earliest > HS._plus_days(tv_first, 365))
                time.sleep(0.15)
            except Exception as e:                                           # noqa: BLE001
                res["sec_err"] = type(e).__name__
        res["corp_event_in_window"] = corp_in
        res["class"] = corp_classify(maxlog, bool(res["splits_in_window"]), corp_in, have_y)
        out.append(res)
    return out


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ⑥ التشغيل
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _fetch(syms, gate=None, scan=None):
    """شموعُ TradingView اليوميّة من 2016 (جلساتٌ مكتملة) ‏+ أزواجُ تقسيمات ياهو وتواريخُها (بالتوازي · مجهولُ ياهو ⟵ None).
    `gate`/`scan` لوضع `rx` وحدَه (`hs_rx_prereg.md §⑬`) · وغيابُهما ⟵ نداءُ `S.tv_download` السابق بت-بت (الأوضاعُ الأخرى)."""
    import Super_stock as S
    from concurrent.futures import ThreadPoolExecutor
    frames, rep = (S.tv_download(list(syms), FX_START) if gate is None and scan is None
                   else S.tv_download(list(syms), FX_START, scan=scan, gate=gate))
    frames = HS._completed_all(frames, rep)
    log(S._tv_bars_line(rep))

    def _sp(s):
        try:
            x = S._fetch_splits(s)
        except Exception:                                                    # noqa: BLE001
            return s, None
        if x is None:
            return s, None
        try:
            return s, sorted((str(d)[:10], float(v)) for d, v in x.items())
        except Exception:                                                    # noqa: BLE001
            return s, None
    with ThreadPoolExecutor(max_workers=8) as ex:
        sp = dict(ex.map(_sp, sorted(frames)))
    miss = sorted(s for s, v in sp.items() if v is None)
    if miss:
        got = _retry_splits(miss, fetch=_sp, reset=lambda s: S._SPLITS_MEMO.pop(s, None))
        sp.update({s: v for s, v in got.items() if v is not None})
        log(f"🔁 تقسيماتٌ مجهولةٌ بعد الجولة الأولى {len(miss)} ⟵ استُعيد {sum(1 for v in got.values() if v is not None)} · "
            f"بقي مجهولًا {sum(1 for s in miss if sp.get(s) is None)}")
    return frames, rep, sp


def rx_population(text: str = None, exclude=(), with_exch: bool = False) -> list:
    """`T-HS-RX §②` — POP-RX: `otherlisted.txt` (ملفُّ البورصات الأخرى من مصدر كون ناسداك نفسِه) ⟵ البورصة N/A · ETF = N · Test Issue = N ·
    رمزٌ أبجديّ · لا وارنت/حقوق/وحدات (فلاترُ `S.get_universe` حرفًا) ⟵ ناقص `exclude` (POP-BOT ∪ كونُ ناسداك). `text` محقونٌ للاختبار ·
    وتعذّرُ الجلب أو ترويسةٌ غيرُ متوقّعة ⟵ [] (لا قياسَ على كونٍ فارغ) · و`with_exch` ⟵ أزواجُ (رمز · رمزُ البورصة) لخريطة TradingView (§⑬)
    — وغيابُه ⟵ الرموزُ وحدَها كما كانت."""
    if text is None:
        import requests
        import Super_stock as S
        try:
            r = requests.get(RX_URL, headers=S.UA, timeout=40)
            r.raise_for_status()
            text = r.text
        except Exception as e:                                               # noqa: BLE001
            log(f"⛔ تعذّر جلبُ {RX_URL}: {type(e).__name__}")
            return []
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    if not lines:
        return []
    header = lines[0].split("|")
    idx = {name: i for i, name in enumerate(header)}
    if any(k not in idx for k in ("ACT Symbol", "Security Name", "Exchange", "ETF", "Test Issue")):
        log(f"⛔ ترويسةٌ غيرُ متوقّعة: {header[:8]}")
        return []
    ex, out = set(exclude or ()), {}
    for ln in lines[1:]:
        if ln.startswith("File Creation Time"):
            continue
        parts = ln.split("|")
        if len(parts) < len(header):
            continue
        sym = parts[idx["ACT Symbol"]].strip()
        name = parts[idx["Security Name"]].strip().upper()
        if parts[idx["Exchange"]].strip() not in RX_EXCH:
            continue
        if parts[idx["ETF"]].strip() == "Y" or parts[idx["Test Issue"]].strip() == "Y":
            continue
        if not sym.isalpha() or (len(sym) == 5 and sym[-1] in "WRU"):
            continue
        if any(b in name for b in ("WARRANT", "RIGHT", " UNIT", "UNITS")):
            continue
        if sym not in ex:
            out[sym] = parts[idx["Exchange"]].strip()
    return sorted(out.items()) if with_exch else sorted(out)


def rx_tv_snapshot(pairs, tmap) -> tuple:
    """`hs_rx_prereg.md §⑬` — لقطةٌ بشكل ماسح TradingView لـPOP-RX ⟵ ({«EXCH:SYM»: {"name": SYM}} · {رمز: "scan" | "otherlisted"}):
    الماسحُ أوّلًا (`tmap` = `S._tv_ticker_map()`) ثمّ **سوقُ `otherlisted.txt`** للغائب عنه (‏N ⟵ NYSE · A ⟵ AMEX) — **لا «NASDAQ:» الافتراضيّ**
    الذي يناسب كونَ البوت وحدَه. تُحقن في `S.tv_download(scan=…)` فيبقى نداؤه هو."""
    snap, src = {}, {}
    for sym, exch in pairs:
        full = (tmap or {}).get(sym)
        src[sym] = "scan" if full else "otherlisted"
        snap[full or f"{RX_TV_EXCH.get(exch, 'NYSE')}:{sym}"] = {"name": sym}
    return snap, src


def rx_partial(out: dict, cov_min: float = RX_COV_MIN, unk_max: float = RX_UNK_MAX) -> list:
    """`§⑬` و`§②` — أسبابُ «جزئيّ» (تُكتب مع التسمية ولا تغيّرها): شموعٌ لأقلَّ من `cov_min` من POP-RX · ومجهولُ التقسيم **فوق** `unk_max`
    من إشارات RECON أو RECON-v2 في ALL (المقامُ صالحٌ ‏+ مستبعَدٌ ‏+ مجهول كما في `T-HS-FX §⑰`)."""
    why = []
    pop, got = int(out.get("population") or 0), int(out.get("fetched") or 0)
    if pop and got / pop < cov_min:
        why.append(f"التغطية {got}/{pop} = {100 * got / pop:.1f}% دون {100 * cov_min:.0f}%")
    for k, name in (("RECON", "RECON"), ("RECON2", "RECON-v2")):
        e = (out.get("split_exclusion") or {}).get(f"{k}|{ALL_ERA}") or {}
        tot = int(e.get("valid") or 0) + int(e.get("excluded") or 0) + int(e.get("unknown") or 0)
        if tot and int(e.get("unknown") or 0) / tot > unk_max:
            why.append(f"مجهولُ التقسيم في {name} {e.get('unknown')}/{tot} = {100 * int(e.get('unknown')) / tot:.1f}% فوق {100 * unk_max:.0f}%")
    return why


def _retry_splits(miss, fetch, reset=None, sleep=time.sleep, clock=time.monotonic,
                  pause: float = SPLIT_RETRY_PAUSE_S, cool: float = SPLIT_RETRY_COOL_S, streak: int = SPLIT_RETRY_STREAK,
                  budget: float = SPLIT_RETRY_BUDGET_S) -> dict:
    """§⑰ تمريرةٌ ثانيةٌ **متسلسلةٌ بطيئة** لما تعذّرت تقسيماتُه (خنقُ ياهو — عطلٌ مُثبَت في ndq الأولى `36949458245`: 2,045 من 3,368
    مجهولًا = الرموزُ H-Z كلُّها): `reset` تُفرغ ذاكرةَ الرمز (`_SPLITS_MEMO` تخزّن None فلا تُعاد) ثمّ `fetch` بفاصل `pause` · وبعد `streak`
    تعذّرًا متتاليًا تبريدٌ `cool` · وسقفُ زمن `budget` ⟵ {رمز: أزواجٌ أو None} (ما لم يُسأل لا يُدرَج · فيبقى مجهولًا ويُعلَن)."""
    out, fails, t0 = {}, 0, clock()
    for s in miss:
        if clock() - t0 > budget:
            break
        if reset is not None:
            reset(s)
        _s, v = fetch(s)
        out[s] = v
        if v is None:
            fails += 1
            if fails >= streak:
                sleep(cool)
                fails = 0
        else:
            fails = 0
        sleep(pause)
    return out


def _regime():
    """نظامُ السوق من TradingView: AMEX:IWM ثمّ NASDAQ:QQQ (§②) ⟵ ({يوم: نظام} · المصدر)."""
    import Super_stock as S
    import tv_data as TV
    for full in ("AMEX:IWM", "NASDAQ:QQQ"):
        try:
            got = TV.fetch_many([full], interval="1D", n=4000) or {}
            df = S.tv_daily_frame(got.get(full), "2014-01-01")
            if df is not None and len(df) > 250:
                return regime_map(df), full
        except Exception:                                                    # noqa: BLE001
            continue
    return {}, None


def _pool_run(fn, tasks, workers: int = 4):
    """عمليّاتٌ متوازية بسياق **spawn** لا fork: الجلبُ قبلها يفتح خيوطًا (مقابسُ TradingView · ياهو) ونسخُ عمليّةٍ فيها خيطٌ يمسك قفلًا
    قد يُعلّق العاملَ حتى مهلة الجوب — spawn يبدأ نظيفًا (كلفتُه استيرادٌ واحدٌ لكلّ عامل)."""
    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor
    out = []
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn")) as ex:
        for i, r in enumerate(ex.map(fn, tasks, chunksize=4)):
            out.append(r)
            if (i + 1) % 200 == 0:
                log(f"   … {i + 1}/{len(tasks)}")
    return out


def _survivorship(frames: dict, asked: int) -> dict:
    import Super_stock as S
    firsts = sorted(str(df.index[0])[:10] for df in frames.values() if len(df))
    lasts = [str(df.index[-1])[:10] for df in frames.values() if len(df)]
    last_ok = S.last_closed_session() or max(lasts)
    lim = (dt.date.fromisoformat(str(last_ok)[:10]) - dt.timedelta(days=10)).isoformat()
    return {"asked": asked, "with_bars": len(frames),
            "alive_by": {d: sum(1 for f in firsts if f <= d) for d in ("2016-07-01", "2019-01-01", "2022-01-01")},
            "ended_before": lim, "ended": sum(1 for x in lasts if x < lim)}


def _overlap_hist(recs: list) -> dict:
    """ثباتُ الكشف أمام بداية البيانات (§⑧): معرّفاتُ STRICT في `hs_history.csv` (من 2021-06) مقابل إشارات SEEN هنا (من 2016)."""
    p = os.path.join(HS.RES_DIR, "hs_history.csv")
    try:
        h = pd.read_csv(p)
        old = set(h[(h["cfg"] == "STRICT") & (h["b_date"].astype(str) >= "2022-01-01")]["pid"].astype(str))
    except Exception as e:                                                   # noqa: BLE001
        return {"err": type(e).__name__}
    new = {r["pid"] for r in recs if r["era"] == "SEEN"}
    return {"old": len(old), "new": len(new), "both": len(old & new), "only_old": len(old - new), "only_new": len(new - old),
            "jaccard": (len(old & new) / len(old | new) if (old | new) else None)}


def _named_history() -> list:
    """§⑩: صفوفُ STRICT للخمسة المسمّاة من `hs_history.csv` (مصدرُ أسمائهم في أمر المالك) — تُدقَّق ولو لم يُعِد الكاشفُ كشفَها من 2016
    (الزجزاجُ يعتمد على بداية البيانات) · بوسم `src=hs_history` · وتعذّرُ القراءة ⟵ [] يُعلَن."""
    try:
        h = pd.read_csv(os.path.join(HS.RES_DIR, "hs_history.csv"))
        h = h[(h["cfg"] == "STRICT") & (h["sym"].isin(NAMED))]
    except Exception as e:                                                   # noqa: BLE001
        log(f"⚠️ سجلُّ T-HS للمسمّاة تعذّر: {type(e).__name__}")
        return []
    out = []
    for _i, x in h.iterrows():
        out.append({"sym": str(x["sym"]), "pid": str(x["pid"]), "b_date": str(x["b_date"])[:10], "ls_date": str(x["ls_date"])[:10],
                    "mfe30": (float(x["mfe"]) if pd.notna(x.get("mfe")) else None),
                    "mae30": (float(x["mae"]) if pd.notna(x.get("mae")) else None),
                    "E": (float(x["entry"]) if pd.notna(x.get("entry")) else None), "raw_px": None, "dv": None, "src": "hs_history"})
    return out


def _save(files: list):
    import Super_stock as S
    if os.environ.get("HS_FX_SAVE", "1") == "1":
        S.git_save(files)


def _csv_rows(recs: list) -> list:
    """جدولُ كلّ إشارة (§29 من أمر المالك) ⟵ صفوفٌ مسطّحة لـ`TARGET_HIT_ANALYSIS.md`."""
    rows = []
    for r in recs:
        ev = (r.get("ev") or {})
        e1, e2 = ev.get("TC|I1|60") or {}, ev.get("TC|I2|60") or {}
        rows.append({"ticker": r["sym"], "date": r["b_date"], "entry_kind": r["entry"], "era": r["era"], "pid": r["pid"],
                     "pattern_valid": True, "breakout_valid": True, "data_valid": valid(r), "entry": r.get("E"),
                     "neckline": r.get("neck_b"), "target": r.get("target"), "stop_I1": r.get("head_px"), "stop_I2": r.get("rs_px"),
                     "target_pct": r.get("tgt_pct"), "neck_type": r.get("neck_type"), "retest": r.get("retest"),
                     "cls_I1_60": e1.get("cls"), "cls_I2_60": e2.get("cls"), "t_tgt_60": e2.get("t_tgt"), "t_stop_I2_60": e2.get("t_stop"),
                     "t_stop_I1_60": e1.get("t_stop"), "seq": r.get("seq"), "mfe30": r.get("mfe30"), "mae30": r.get("mae30"),
                     "mfe90": r.get("mfe90"), "mae90": r.get("mae90"), **{f"ret{x}": r.get(f"ret{x}") for x in HZ},
                     "B1_ret": _bget(r.get("B1")), "B1_why": _bget(r.get("B1"), "why"), "raw_px": r.get("raw_px"),
                     "regime": r.get("regime"),
                     **({k: r.get(k) for k in ("hd1", "hd2", "hd_body_gap", "hd_prior_gap")} if "hd1" in r else {})})
    return rows


def run_main(mode: str) -> int:
    """main · ndq: الجلبُ ⟵ التحليلُ بالتوازي ⟵ المطابقة ⟵ الجداول ⟵ الفرضيّات ⟵ (main) النظرُ المستقبليّ · إجراءاتُ الشركات · العيّنات ⟵ الحفظ."""
    import Super_stock as S
    t0 = time.time()
    if mode == "ndq":
        pop = list(S.get_universe() or [])
    else:
        pop = HS.load_population()
    log(f"🔬 {TOOL} · وضع {mode} · المجتمع {len(pop)} · من {FX_START} · الحقب {ERAS}")
    frames, rep, sp = _fetch(pop)
    log(f"📊 شموعٌ لـ{len(frames)} من {len(pop)} · تقسيماتٌ مجهولة {sum(1 for v in sp.values() if v is None)}")
    regime, reg_src = _regime()
    log(f"🌐 نظامُ السوق: {reg_src or 'تعذّر'} ({len(regime)} يومًا)")
    tasks = [(s, frames[s], sp.get(s), (None if sp.get(s) is None else sorted({d for d, _r in sp[s]})), regime,
              ("main" if mode == "main" else "ndq")) for s in sorted(frames)]
    res = _pool_run(analyze_sym, tasks)
    errs = [(r["sym"], r["err"]) for r in res if r.get("err")]
    log(f"⚙️ حُلّل {len(res)} رمزًا في {time.time() - t0:.0f}ث · أخطاء {len(errs)} {errs[:5]}")
    allsig = {k: [x for r in res for x in r[k]] for k in ("C", "D", "A", "B")}
    for r in allsig["D"]:
        r["recon"] = r.get("neck_type") == "horizontal"
    allsig["RECON"] = [dict(r, entry="RECON") for r in allsig["D"] if r["recon"]]
    pools = {"B": [x for r in res for x in r["ctrl"]], "D": [x for r in res for x in r["skD"]],
             "E": [x for r in res for x in r["skE"]]}
    for c in pools["B"]:
        pr = sp.get(c["sym"])
        raw = c["E"] * split_factor_after(pr, c["b_date"]) if pr is not None else None
        c["raw_px"], c["px_bucket"] = raw, px_bucket(raw)
    frames_arr = {s: arrays(frames[s]) for s in frames}
    log(f"🎯 إشاراتٌ: C {len(allsig['C'])} · D {len(allsig['D'])} · RECON {len(allsig['RECON'])} · A {len(allsig['A'])} · "
        f"B {len(allsig['B'])} · ضبطُ B {len(pools['B'])} · هيكلُ D {len(pools['D'])} · هيكلُ E {len(pools['E'])}")
    out = {"tool": TOOL, "mode": mode, "generated": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
           "population": len(pop), "fetched": len(frames), "regime_src": reg_src,
           "fetch_report": {k: (v if not isinstance(v, list) else len(v)) for k, v in rep.items()},
           "splits_unknown": sum(1 for v in sp.values() if v is None), "eras": ERAS, "survivorship": _survivorship(frames, len(pop)),
           "errors": errs[:50], "summary": {}, "compare": {}, "regimes": {}, "split_exclusion": {}}
    kinds = ("C", "D", "RECON", "A", "B") if mode == "main" else ("C", "D", "RECON")
    bl_kinds = ("B", "C", "D", "E", "F") if mode == "main" else ("B",)
    for era in [e[0] for e in ERAS]:
        for k in kinds:
            recs = [r for r in allsig[k] if r["era"] == era]
            out["summary"][f"{k}|{era}"] = summarize(recs)
        recsC = [r for r in allsig["C"] if r["era"] == era]
        out["regimes"][era] = regime_tables(recsC)
        exc = [r for r in recsC if r.get("split_win")]
        out["split_exclusion"][era] = {"excluded": len(exc), "unknown": sum(1 for r in recsC if r.get("split_win") is None),
                                       "valid": sum(1 for r in recsC if valid(r)),
                                       "excluded_ret30": HS.dist([r.get("ret30") for r in exc]),
                                       "excluded_clean": (lambda cl: (float(np.mean(cl)) if cl else None))(
                                           [x for x in (clean_of(r) for r in exc) if x is not None])}
    matched = {}
    for bk in bl_kinds:
        pool = pools["B"] if bk in ("B", "C", "F") else pools[bk]
        for k in kinds:
            matched[(bk, k)] = match_controls(allsig[k], pool, bk)
    for era in [e[0] for e in ERAS]:
        alpha = CONF_ALPHA if era == "TEST" else EXPL_ALPHA
        for k in kinds:
            sigs = [r for r in allsig[k] if r["era"] == era]
            for bk in bl_kinds:
                out["compare"][f"{k}|{era}|BL-{bk}"] = compare(sigs, matched[(bk, k)], frames_arr, alpha=alpha)
            a_rows = [(r, [c for c in r.get("blA") or [] if c.get("valid")]) for r in sigs if valid(r)] if k == "C" else []
            if a_rows:
                out["compare"][f"C|{era}|BL-A"] = {
                    "B1": boot_diff([_bget(r.get("B1")) for r, _ in a_rows], [[_bget(c.get("B1")) for c in cs] for _r, cs in a_rows], alpha=alpha),
                    "clean_I2_60": boot_diff([clean_of(r) for r, _ in a_rows], [[c.get("clean_I2") for c in cs] for _r, cs in a_rows], alpha=alpha),
                    "ret30": boot_diff([r.get("ret30") for r, _ in a_rows], [[c.get("ret30") for c in cs] for _r, cs in a_rows], alpha=alpha)}
        out["compare"][f"newcombe|{era}"] = newcombe_clean([r for r in allsig["C"] if r["era"] == era], matched[("B", "C")], frames_arr)
    test = {k: out["compare"].get(f"{k}|TEST|BL-B") for k in ("C", "RECON")}
    out["test_block"] = {"C": test["C"], "RECON": test["RECON"]}
    if mode == "main":
        la = [r.get("la") for r in allsig["C"] if r.get("la")]
        bad = [r["pid"] for r in allsig["C"] if r.get("la") and not (r["la"]["prefix_ok"] and r["la"]["info_ok"])]
        out["lookahead"] = {"checked": len(la), "prefix_ok": sum(1 for x in la if x["prefix_ok"]),
                            "info_ok": sum(1 for x in la if x["info_ok"]), "violations": bad[:100]}
        out["overlap_hist"] = _overlap_hist(allsig["C"])
        cases = [r for r in allsig["C"] if r["sym"] in NAMED and r["era"] == "SEEN"]
        ext = sorted([r for r in allsig["C"] if r.get("mfe30") is not None and (r["mfe30"] >= CASE_MFE or (r.get("mae30") or 0) <= CASE_MAE)],
                     key=lambda r: -max(r["mfe30"], -(r.get("mae30") or 0) * 5))
        seen_c = {r["pid"] for r in cases}
        for r in ext:
            if len(cases) >= CASE_CAP:
                break
            if r["pid"] not in seen_c:
                cases.append(r)
                seen_c.add(r["pid"])
        for row in _named_history():
            if not any(c["sym"] == row["sym"] and c["b_date"] == row["b_date"] for c in cases):
                cases.append(row)
        log(f"🧾 إجراءاتُ الشركات: {len(cases)} حالة (منها من سجلّ T-HS {sum(1 for c in cases if c.get('src') == 'hs_history')})")
        out["corp"] = corp_audit(cases, frames, {s: (sp.get(s) or []) for s in frames})
        seen_v = [r for r in allsig["C"] if r["era"] == "SEEN" and valid(r) and r.get("mfe30") is not None]
        top = sorted(seen_v, key=lambda r: -r["mfe30"])[:REPLAY_N]
        bot = sorted(seen_v, key=lambda r: r.get("mae30") or 0)[:REPLAY_N]
        rnd = pick(seen_v, f"replay|{REPLAY_SEED}", REPLAY_N)
        named = [r for r in seen_v if r["sym"] in NAMED]
        rep_items, have = [], set()
        for tag, grp in (("top", top), ("worst", bot), ("random", rnd), ("named", named)):
            for r in grp:
                if (r["pid"], tag) in have:
                    continue
                have.add((r["pid"], tag))
                rep_items.append(dict(seg_export(frames[r["sym"]], r), tag=tag))
        with open(os.path.join(FX_DIR, "fx_replay.json"), "w", encoding="utf-8") as fh:
            json.dump(rep_items, fh, ensure_ascii=False, default=str)
        old = []
        try:
            old = (json.load(open(OLD_FILE, encoding="utf-8")).get("items") or [])
        except Exception:                                                    # noqa: BLE001
            old = []
        items = []
        for it in old:
            df = frames.get(it["sym"])
            if df is None:
                continue
            ix = [str(x)[:10] for x in df.index]
            if it["b_date"] in ix:
                items.append({"kind": "OLD", "sym": it["sym"], "b_date": it["b_date"], "pid": it["pid"], "detector": True,
                              "bars": blind_bars(df, ix.index(it["b_date"]))})
        tr = [r for r in allsig["C"] if r["era"] == "TRAIN" and valid(r)]
        for r in pick(tr, f"new|{NEW_SEED}", BLIND_N):
            items.append({"kind": "NEW", "sym": r["sym"], "b_date": r["b_date"], "pid": r["pid"], "detector": True,
                          "bars": blind_bars(frames[r["sym"]], int(r["b_i"]))})
        neg = [c for c in pools["B"] if c["era"] == "TRAIN" and valid(c)]
        for c in pick(neg, f"neg|{NEG_SEED}", BLIND_N):
            items.append({"kind": "NEG", "sym": c["sym"], "b_date": c["b_date"], "pid": None, "detector": False,
                          "bars": blind_bars(frames[c["sym"]], int(c["b_i"]))})
        charts, key = blind_mix(items)
        with open(os.path.join(FX_DIR, "fx_blind_charts.json"), "w", encoding="utf-8") as fh:
            json.dump(charts, fh)
        sealed, ksha = seal_key(key)
        with open(os.path.join(FX_DIR, "fx_blind_key.b64"), "w", encoding="utf-8") as fh:
            fh.write(sealed)
        log(f"🔐 مفتاحُ التدقيق الأعمى مختوم · sha256 {ksha} · لا يُفتح قبل دفع الوسوم")
        out["samples"] = {"replay": len(rep_items), "blind": len(items), "key_sha256": ksha,
                          "blind_kinds": {k: sum(1 for x in items if x["kind"] == k) for k in ("OLD", "NEW", "NEG")}}
    out["hypotheses_partial"] = hypotheses({"C": out["compare"].get("C|TEST|BL-B"), "RECON": out["compare"].get("RECON|TEST|BL-B")})
    out["secs"] = round(time.time() - t0, 1)
    tag = "bot" if mode == "main" else "ndq"
    pd.DataFrame(_csv_rows([r for k in kinds for r in allsig[k]])).to_csv(os.path.join(FX_DIR, f"fx_signals_{tag}.csv"), index=False)
    path = os.path.join(FX_DIR, f"fx_{tag}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=str)
    files = [path, os.path.join(FX_DIR, f"fx_signals_{tag}.csv")]
    if mode == "main":
        files += [os.path.join(FX_DIR, x) for x in ("fx_replay.json", "fx_blind_charts.json", "fx_blind_key.b64")]
    log(f"💾 {files} · {out['secs']}ث")
    for k in ("C", "RECON"):
        x = (out["compare"].get(f"{k}|TEST|BL-B") or {})
        log(f"⚖️ TEST {k} مقابل BL-B: n={x.get('n_sig')} · CLEAN {_fmt(x.get('clean_I2_60'))} · القوس {_fmt(x.get('B1'))}")
    _save(files)
    return 0


def bl_a_compare(sigs: list, alpha: float) -> dict:
    """BL-A لأيّ ذراع (`T-HS-RX §⑥`): الفرقُ المطابَق بين الإشارة وأيّامها العشوائيّة الصالحة (`blA`) في CLEAN والقوس وret30 — بحرف كتلة C في `run_main`."""
    rows = [(r, [c for c in r.get("blA") or [] if c.get("valid")]) for r in sigs if valid(r)]
    return {"B1": boot_diff([_bget(r.get("B1")) for r, _ in rows], [[_bget(c.get("B1")) for c in cs] for _r, cs in rows], alpha=alpha),
            "clean_I2_60": boot_diff([clean_of(r) for r, _ in rows], [[c.get("clean_I2") for c in cs] for _r, cs in rows], alpha=alpha),
            "ret30": boot_diff([r.get("ret30") for r, _ in rows], [[c.get("ret30") for c in cs] for _r, cs in rows], alpha=alpha)}


def hypotheses_rx(cmp: dict) -> dict:
    """`T-HS-RX §⑦` على ALL: RX-H1a/H2a (RECON) · RX-H1b/H2b (RECON-v2) — «تُدعَم» = الحدُّ الأدنى (‏98.75%) فوق الصفر أمام BL-B **و** BL-A ·
    و**n ‏≥ 30 أمام كلٍّ منهما** وإلّا «لا قياس» ⟵ التسمية: RX-1 (قوسٌ يُدعَم) · RX-2 (CLEAN وحدَه) · RX-4 (الأربعُ «لا قياس») · وإلّا RX-3 ·
    و`note` يُسمّي الذراعَ غيرَ المقيسة (فلا تُقرأ RX-3 حكمًا على ذراعٍ لم تُقَس)."""
    out = {}
    for h, k, metric in (("RX-H1a", "RECON", "clean_I2_60"), ("RX-H2a", "RECON", "B1"),
                         ("RX-H1b", "RECON2", "clean_I2_60"), ("RX-H2b", "RECON2", "B1")):
        b = ((cmp.get(f"{k}|{ALL_ERA}|BL-B") or {}).get(metric)) or {}
        a = ((cmp.get(f"{k}|{ALL_ERA}|BL-A") or {}).get(metric)) or {}
        if min(b.get("n_sig") or 0, a.get("n_sig") or 0) < MIN_N:
            st = "لا قياس"
        elif b.get("lo") is not None and b["lo"] > 0 and a.get("lo") is not None and a["lo"] > 0:
            st = "تُدعَم"
        else:
            st = "لا تُدعَم"
        out[h] = {"status": st, "BL-B": b, "BL-A": a}
    s_ = {h: v["status"] for h, v in out.items()}
    if "تُدعَم" in (s_["RX-H2a"], s_["RX-H2b"]):
        lab = "RX-1 «البناءُ الأمين يربح»"
    elif "تُدعَم" in (s_["RX-H1a"], s_["RX-H1b"]):
        lab = "RX-2 «يبلغ ولا يربح»"
    elif all(v == "لا قياس" for v in s_.values()):
        lab = "RX-4 «لا قياس»"
    else:
        lab = "RX-3 «لا ميزةَ حتى بالبناء الأمين»"
    out["RX"] = lab
    out["note"] = [arm for arm, hs_ in (("RECON", ("RX-H1a", "RX-H2a")), ("RECON-v2", ("RX-H1b", "RX-H2b")))
                   if all(s_[h] == "لا قياس" for h in hs_)]
    return out


def run_rx() -> int:
    """`T-HS-RX` (العقد `hs_forensic/hs_rx_prereg.md` · مدموجٌ قبل أيّ رقم): POP-RX ⟵ C · RECON · RECON-v2 بقياس `T-HS-FX` نفسِه ⟵ BL-A وBL-B
    لكلّ ذراع (الحقب ‏+ ALL) ⟵ الفرضيّاتُ الأربع ⟵ عيّنةُ الأمانة العمياء (30 v2 ‏+ 30 RECON∖v2 ‏+ 30 ضبط · مفتاحٌ مختوم) ⟵ الحفظ."""
    import Super_stock as S
    t0 = time.time()
    excl = set(HS.load_population()) | set(S.get_universe() or [])
    pairs = rx_population(exclude=excl, with_exch=True)
    pop = [s_ for s_, _e in pairs]
    log(f"🔬 T-HS-RX · POP-RX {len(pop)} رمزًا (المستبعَد POP-BOT ∪ ناسداك {len(excl)}) · من {FX_START} · q={RX_Q}")
    if not pop:
        log("⛔ POP-RX فارغ ⟵ لا قياس")
        return 3
    snap, msrc = rx_tv_snapshot(pairs, S._tv_ticker_map())
    log(f"🗺️ خريطةُ TradingView (§⑬): الماسح {sum(1 for v in msrc.values() if v == 'scan')} · سوقُ otherlisted "
        f"{sum(1 for v in msrc.values() if v == 'otherlisted')} · والقاطعُ لا يُفتح بالإخفاق (نسبة {RX_GATE_RATIO})")
    frames, rep, sp = _fetch(pop, gate=S.TVBarsGate(ratio=RX_GATE_RATIO), scan=lambda *_a, **_k: snap)
    log(f"📊 شموعٌ لـ{len(frames)} من {len(pop)} · تقسيماتٌ مجهولة {sum(1 for v in sp.values() if v is None)}")
    regime, reg_src = _regime()
    tasks = [(s, frames[s], sp.get(s), (None if sp.get(s) is None else sorted({d for d, _r in sp[s]})), regime, "rx")
             for s in sorted(frames)]
    res = _pool_run(analyze_sym, tasks)
    errs = [(r["sym"], r["err"]) for r in res if r.get("err")]
    log(f"⚙️ حُلّل {len(res)} رمزًا في {time.time() - t0:.0f}ث · أخطاء {len(errs)} {errs[:5]}")
    allsig = {"C": [x for r in res for x in r["C"]], "D": [x for r in res for x in r["D"]]}
    allsig["RECON"] = [dict(r, entry="RECON") for r in allsig["D"] if r.get("neck_type") == "horizontal"]
    allsig["RECON2"] = [dict(r, entry="RECON2") for r in allsig["RECON"] if r.get("hd1") and r.get("hd2")]
    pool = [x for r in res for x in r["ctrl"]]
    for c in pool:
        pr = sp.get(c["sym"])
        raw = c["E"] * split_factor_after(pr, c["b_date"]) if pr is not None else None
        c["raw_px"], c["px_bucket"] = raw, px_bucket(raw)
    frames_arr = {s: arrays(frames[s]) for s in frames}
    log(f"🎯 إشاراتٌ: C {len(allsig['C'])} · D {len(allsig['D'])} · RECON {len(allsig['RECON'])} · RECON-v2 {len(allsig['RECON2'])} · "
        f"ضبطُ B {len(pool)}")
    eras = [e[0] for e in ERAS]

    def in_era(r, era):
        return r.get("era") in eras if era == ALL_ERA else r.get("era") == era
    kinds = ("C", "RECON", "RECON2")
    out = {"tool": "T-HS-RX", "mode": "rx", "generated": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", "q": RX_Q,
           "population": len(pop), "excluded": len(excl), "fetched": len(frames), "regime_src": reg_src,
           "fetch_report": {k: (v if not isinstance(v, list) else len(v)) for k, v in rep.items()},
           "splits_unknown": sum(1 for v in sp.values() if v is None), "eras": ERAS, "survivorship": _survivorship(frames, len(pop)),
           "errors": errs[:50], "summary": {}, "compare": {}, "split_exclusion": {},
           "tv_map": {"scan": sum(1 for v in msrc.values() if v == "scan"), "otherlisted": sum(1 for v in msrc.values() if v == "otherlisted")},
           "fetch_lists": {k: [{"sym": x, "map": msrc.get(x)} for x in (rep.get(k) or [])] for k in ("none", "empty", "short")}}
    matched = {k: match_controls(allsig[k], pool, "B") for k in kinds}
    for era in eras + [ALL_ERA]:
        alpha = RX_ALPHA if era == ALL_ERA else EXPL_ALPHA
        for k in kinds:
            sigs = [r for r in allsig[k] if in_era(r, era)]
            out["summary"][f"{k}|{era}"] = summarize(sigs)
            out["compare"][f"{k}|{era}|BL-B"] = compare(sigs, matched[k], frames_arr, alpha=alpha)
            out["compare"][f"{k}|{era}|BL-A"] = bl_a_compare(sigs, alpha)
            out["split_exclusion"][f"{k}|{era}"] = {"valid": sum(1 for r in sigs if valid(r)), "excluded": sum(1 for r in sigs if r.get("split_win")),
                                                    "unknown": sum(1 for r in sigs if r.get("split_win") is None)}
    la = [r.get("la") for r in allsig["RECON2"] if r.get("la")]
    out["lookahead"] = {"checked": len(la), "prefix_ok": sum(1 for x in la if x["prefix_ok"]), "info_ok": sum(1 for x in la if x["info_ok"]),
                        "violations": [r["pid"] for r in allsig["RECON2"] if r.get("la") and not (r["la"]["prefix_ok"] and r["la"]["info_ok"])][:100]}
    out["hypotheses"] = hypotheses_rx(out["compare"])
    out["partial"] = rx_partial(out)
    items = []
    v2 = [r for r in allsig["RECON2"] if valid(r) and in_era(r, ALL_ERA)]
    v1 = [r for r in allsig["RECON"] if valid(r) and in_era(r, ALL_ERA) and not (r.get("hd1") and r.get("hd2"))]
    for tag, grp, seed in (("V2", v2, RX_SEED_V2), ("V1", v1, RX_SEED_V1)):
        for r in pick(grp, f"rx|{tag}|{seed}", BLIND_N):
            items.append({"kind": tag, "sym": r["sym"], "b_date": r["b_date"], "pid": r["pid"], "detector": True,
                          "bars": blind_bars(frames[r["sym"]], int(r["b_i"]))})
    neg = [c for c in pool if valid(c) and in_era(c, ALL_ERA)]
    for c in pick(neg, f"rx|NEG|{RX_SEED_NEG}", BLIND_N):
        items.append({"kind": "NEG", "sym": c["sym"], "b_date": c["b_date"], "pid": None, "detector": False,
                      "bars": blind_bars(frames[c["sym"]], int(c["b_i"]))})
    charts, key = blind_mix(items, seed=RX_MIX_SEED, prefix="RX")
    sealed, ksha = seal_key(key)
    out["samples"] = {"blind": len(items), "key_sha256": ksha, "blind_kinds": {k: sum(1 for x in items if x["kind"] == k) for k in ("V2", "V1", "NEG")}}
    out["secs"] = round(time.time() - t0, 1)
    paths = {k: os.path.join(FX_DIR, f) for k, f in (("json", "fx_rx.json"), ("csv", "fx_signals_rx.csv"),
                                                       ("charts", "fx_rx_blind_charts.json"), ("key", "fx_rx_blind_key.b64"))}
    pd.DataFrame(_csv_rows([r for k in kinds for r in allsig[k]])).to_csv(paths["csv"], index=False)
    with open(paths["charts"], "w", encoding="utf-8") as fh:
        json.dump(charts, fh)
    with open(paths["key"], "w", encoding="utf-8") as fh:
        fh.write(sealed)
    with open(paths["json"], "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=str)
    log(f"🔐 مفتاحُ أمانة RX مختوم · sha256 {ksha} · لا يُفتح قبل دفع الوسوم · العيّنة {out['samples']['blind_kinds']}")
    hyp = out["hypotheses"]
    log(f"⚖️ {hyp['RX']} · " + " · ".join(f"{h}: {hyp[h]['status']}" for h in ("RX-H1a", "RX-H2a", "RX-H1b", "RX-H2b"))
        + (f" · لم يُقَس: {hyp['note']}" if hyp["note"] else "")
        + (f" · ⚠️ جزئيّ: {'؛ '.join(out['partial'])}" if out["partial"] else ""))
    for k in kinds:
        for bk in ("BL-B", "BL-A"):
            x = out["compare"].get(f"{k}|{ALL_ERA}|{bk}") or {}
            log(f"   {k} ⟵ {bk} (ALL): CLEAN {_fmt(x.get('clean_I2_60'))} · القوس {_fmt(x.get('B1'))}")
    log(f"💾 {list(paths.values())} · {out['secs']}ث")
    _save(list(paths.values()))
    return 0


def _fmt(d) -> str:
    if not d or d.get("diff") is None:
        return "—"
    return f"{d['diff']:+.3f} [{d['lo']:+.3f}، {d['hi']:+.3f}] (n={d['n_sig']})"


def run_sens() -> int:
    """§⑧: كلُّ متغيّرٍ على TRAIN ⟵ «واعدٌ» (متوسّطُ القوس أعلى من CURRENT بحدّ بوتستراب 95% فوق الصفر · n ‏≥ 30) ⟵ VAL بالقاعدة نفسِها ⟵
    ما عبرهما يُختبر **مرّةً واحدة** في TEST ويُنشر — ولا يُشحَن شيء."""
    t0 = time.time()
    pop = HS.load_population()
    frames, rep, sp = _fetch(pop)
    variants = dict(SENS, CURRENT=P_C)

    def _cut(d):
        return {s: df[df.index <= pd.Timestamp(d)] for s, df in frames.items() if len(df[df.index <= pd.Timestamp(d)]) > 60}
    f1 = _cut(SENS_CUT_TRAINVAL)
    tasks = [(s, f1[s], (None if sp.get(s) is None else sorted({d for d, _r in sp[s]})), variants, ("TRAIN", "VAL")) for s in sorted(f1)]
    res = _pool_run(sens_sym, tasks)
    rows = {v: [x for r in res for x in r["res"].get(v, [])] for v in variants}
    out = {"tool": TOOL, "mode": "sens", "generated": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
           "variants": {k: {kk: vv for kk, vv in p.items() if HS.STRICT.get(kk) != vv} for k, p in variants.items()}, "log": []}

    def _stage(era):
        st = {}
        base = [x["B1"] for x in rows["CURRENT"] if x["era"] == era and x["B1"] is not None]
        for v in variants:
            xs = [x for x in rows[v] if x["era"] == era]
            b1 = [x["B1"] for x in xs if x["B1"] is not None]
            d = _ind_diff(b1, base)
            cl = [x["clean"] for x in xs if x["clean"] is not None]
            st[v] = {"n": len(b1), "B1_mean": (float(np.mean(b1)) if b1 else None), "clean": (float(np.mean(cl)) if cl else None),
                     "ret30_med": HS.dist([x["ret30"] for x in xs]).get("median"), "vs_current": d,
                     "promising": bool(v != "CURRENT" and len(b1) >= MIN_N and d.get("lo") is not None and d["lo"] > 0)}
        return st
    out["TRAIN"] = _stage("TRAIN")
    out["VAL"] = _stage("VAL")
    passed = [v for v in SENS if out["TRAIN"][v]["promising"] and out["VAL"][v]["promising"]]
    out["passed_train_val"] = passed
    for v in SENS:
        out["log"].append({"experiment": f"sens:{v}", "params": out["variants"][v], "split": "TRAIN→VAL",
                           "train": {k: out["TRAIN"][v].get(k) for k in ("n", "B1_mean", "clean")},
                           "val": {k: out["VAL"][v].get(k) for k in ("n", "B1_mean", "clean")},
                           "selected": v in passed,
                           "reason": ("عبر TRAIN ثمّ VAL" if v in passed else
                                      ("واعدٌ في TRAIN وسقط في VAL" if out["TRAIN"][v]["promising"] else "لم يَعِد في TRAIN"))})
    if passed:
        f2 = _cut(SENS_CUT_TEST)
        vv = dict({v: SENS[v] for v in passed}, CURRENT=P_C)
        tasks = [(s, f2[s], (None if sp.get(s) is None else sorted({d for d, _r in sp[s]})), vv, ("TEST",)) for s in sorted(f2)]
        res2 = _pool_run(sens_sym, tasks)
        rows = {v: [x for r in res2 for x in r["res"].get(v, [])] for v in vv}
        variants = vv
        out["TEST"] = _stage("TEST")
    out["secs"] = round(time.time() - t0, 1)
    path = os.path.join(FX_DIR, "fx_sens.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=str)
    log(f"🧪 الحساسيّة: عبر TRAIN ثمّ VAL: {passed or 'لا شيء'} · {out['secs']}ث")
    _save([path])
    return 0


def _ind_diff(a, b, alpha: float = EXPL_ALPHA, n_b: int = BOOT_B, seed: int = BOOT_SEED) -> dict:
    """فرقُ متوسّطَي عيّنتين مستقلّتين ببوتستراب (الحساسيّة · §⑧)."""
    a = np.asarray([x for x in a if x is not None and np.isfinite(x)], float)
    b = np.asarray([x for x in b if x is not None and np.isfinite(x)], float)
    if not len(a) or not len(b):
        return {"diff": None, "lo": None, "hi": None}
    rng = np.random.default_rng(seed)
    ds = [a[rng.integers(0, len(a), len(a))].mean() - b[rng.integers(0, len(b), len(b))].mean() for _ in range(n_b)]
    return {"diff": float(a.mean() - b.mean()), "lo": float(np.percentile(ds, 100 * alpha / 2)),
            "hi": float(np.percentile(ds, 100 * (1 - alpha / 2)))}


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ⑦ الرسمُ المحلّيّ (الإعادةُ البصريّة · التدقيقُ الأعمى) — Pillow · لا يُدفَع
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def render_bars(bars, path: str, marks: dict = None, lines: dict = None, cut: int = None, title: str = "") -> str:
    """شموعٌ من [[O,H,L,C]] أو [[يوم,O,H,L,C]] ⟵ PNG · `marks` {اسم: (فهرس، سعر)} · `lines` {اسم: (سعر، من فهرس)} · `cut` يقصّ عند بار القرار."""
    from PIL import Image, ImageDraw
    rows = [b[-4:] for b in bars]
    if cut is not None:
        rows = rows[:int(cut) + 1]
    o, h, l, c = (np.asarray([r[i] for r in rows], float) for i in range(4))
    W, Hh, ml, mr, mt, mb = 1100, 600, 50, 120, 30, 30
    lo, hi = float(np.nanmin(l)), float(np.nanmax(h))
    for _k, (y, _i0) in (lines or {}).items():
        if y is not None and np.isfinite(y):
            lo, hi = min(lo, y), max(hi, y)
    rng = (hi - lo) or 1.0
    n = len(rows)
    bw = (W - ml - mr) / float(max(1, n))

    def X(i):
        return ml + (i + 0.5) * bw

    def Y(y):
        return mt + (hi - y) / rng * (Hh - mt - mb)
    im = Image.new("RGB", (W, Hh), (255, 255, 255))
    dr = ImageDraw.Draw(im)
    for i in range(n):
        col = (22, 128, 61) if c[i] >= o[i] else (196, 40, 40)
        dr.line([(X(i), Y(h[i])), (X(i), Y(l[i]))], fill=col, width=1)
        y0, y1 = sorted((Y(o[i]), Y(c[i])))
        dr.rectangle([X(i) - bw * 0.35, y0, X(i) + bw * 0.35, max(y1, y0 + 1)], fill=col)
    pal = [(30, 90, 200), (0, 150, 150), (200, 0, 120), (120, 0, 160), (240, 150, 0), (90, 90, 90)]
    for j, (k, (y, i0)) in enumerate((lines or {}).items()):
        if y is None or not np.isfinite(y):
            continue
        dr.line([(X(i0 or 0), Y(y)), (W - mr, Y(y))], fill=pal[j % len(pal)], width=1)
        dr.text((W - mr + 4, Y(y) - 6), f"{k} {y:.4g}", fill=pal[j % len(pal)])
    for k, (i, y) in (marks or {}).items():
        if i is None or i >= n:
            continue
        yy = y if y is not None else c[i]
        dr.ellipse([X(i) - 5, Y(yy) - 5, X(i) + 5, Y(yy) + 5], outline=(120, 0, 160), width=2)
        dr.text((X(i) - 8, Y(yy) + 8), k, fill=(120, 0, 160))
    for frac in (0.0, 0.5, 1.0):
        y = lo + frac * rng
        dr.text((W - mr + 4, Y(y) + 8), f"{y:.4g}", fill=(150, 150, 150))
    if title:
        dr.text((ml, 8), title[:140], fill=(0, 0, 0))
    im.save(path)
    return path


def main() -> int:
    mode = (os.environ.get("HS_FX_MODE") or "main").strip().lower()
    os.makedirs(FX_DIR, exist_ok=True)
    if mode in ("main", "ndq"):
        return run_main(mode)
    if mode == "sens":
        return run_sens()
    if mode == "verdict":
        return run_verdict()
    if mode == "rx":
        return run_rx()
    log(f"⛔ وضعٌ مجهول: {mode}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
