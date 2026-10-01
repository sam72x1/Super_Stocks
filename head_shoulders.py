# -*- coding: utf-8 -*-
"""🔎 «نموذج الرأس والكتفين» — كاشفٌ كمّيٌّ **سببيّ** للنموذج المقلوب الصاعد كما في الإنفوغراف الذي تبنّاه فيصل (`TG_50589`)
ومرآتُه للقمّة **للتحقّق البنيويّ وحدَه** (DCOY 2026-09-22 · `CH_20261001_HS_02_DCOY`) — أمرُ المالك 2026-10-01
«FULL AUTONOMOUS MISSION — BUILD: نموذج الرأس والكتفين».

• المصادرُ وأدوارُها (CORE · CONFIRMATION · FILTER · CONTEXT · UNKNOWN): `faisal_batches/2026-10-01_hs/HS_SOURCE_ANALYSIS.md`
• العقدُ قبل أيّ رقم: `hs_prereg.md` · والنتيجة: `hs_result.md`.

⚖️ **السببيّة (لا نظرَ للمستقبل) — مفصولةٌ بالبناء:**
  - المحورُ عند البار `i` يصير معروفًا عند `i + k` وحدَه ⟵ الزجزاجُ يُبنى بترتيب الظهور.
  - الإشارةُ عند بار الاختراق `b` **لا تقرأ إلّا بارات `≤ b`** (`detect` · `_evaluate` · `_finalize`).
  - ما بعد الإشارة (`outcomes` · `retest_state` · `signal_state`) دوالُّ منفصلةٌ تقرأ المستقبلَ **للقياس وحدَه** — و`detect` لا تناديها
    (قفلٌ بالـAST) · وثباتُ الاقتطاع: إشاراتُ `df[:t+1]` = إشاراتُ `df` حتى t (قفلٌ سلوكيّ).
⚠️ **ليس «طريقة فيصل» المثبَتة بأمثلته:** مثالاه الحقيقيّان قمّةٌ للخروج («الثبات فوق سعر الكتف الأيسر») — ومحورُ الخروج مُغلَق
(`TRAIL_REOPEN`) ⇒ لا إشارةَ خروجٍ هنا. 🔒 خارج الجذور والفرز · لا `LOGIC_VERSION` · قراءةٌ/عرضٌ وتنبيه."""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import sys
import zlib

import numpy as np
import pandas as pd

TOOL_NAME = "نموذج الرأس والكتفين"
TOOL_TECH = "head_and_shoulders_detector"

# ── المعاملات (كلُّها `engineering` · لا رقمَ فيها من فيصل — `FAISAL_SOURCE_LEDGER.md §نموذج الرأس والكتفين`) ──────────────
STRICT = {
    "k": 3,                 # نصفُ نافذة المحور (بارات) — يُعرَف المحورُ بعد k بارات
    "atr_n": 14,            # ATR 14 بصيغة `S.atr` نفسِها
    "swing_atr": 1.0,       # عتبةُ انعكاس الزجزاج بوحدات ATR (ما دونها ضجيج)
    "height_min_atr": 1.5,  # ارتفاعُ النموذج (خطُّ العنق عند الرأس − قاعُ الرأس) بوحدات ATR
    "height_min_pct": 0.05, # §⑤-ب ‏+ ارتفاعُه 5% من سعر الإغلاق على الأقلّ — ATR وحدَه يُجيز ضجيجَ سهمٍ شبهِ ساكن (AMCI ‏1.5% · أدنى صحيحٍ 7%)
    "head_min_atr": 0.5,    # الرأسُ أعمقُ من أعلى الكتفين بنصف ATR على الأقلّ
    "shoulder_tol": 1 / 3,  # |الكتف الأيسر − الكتف الأيمن| حتى ثلث الارتفاع (HS-E3 «متقاربان لا متساويان») — §⑤-ب: كان 0.5 فمرّت
                            #   ثمانٍ من إحدى عشرةَ إيجابًا كاذبًا بفرقٍ 0.34-0.47 · وأكبرُ فرقٍ في الصحيحة 0.23
    "shoulder_depth": 0.25, # كلُّ كتفٍ تحت خطّ العنق بربع الارتفاع على الأقلّ
    "neck_slope": 0.5,      # |قمّةُ الارتداد الثانية − الأولى| حتى نصف الارتفاع (أفقيٌّ أو صاعدٌ أو هابط)
    "mid_gap": 0.25,        # الرأسُ المركّب (HS-E8): الارتدادُ الأوسط تحت خطّ العنق بربع الارتفاع على الأقلّ
    "time_sym": 3.0,        # تناظرُ الزمن: max(d1, d2) ÷ min(d1, d2) حتى 3 — **لا «12 شمعة»** (HS-E10)
    "min_span": 10,         # من الكتف الأيسر إلى الأيمن (بارات)
    "max_span": 120,
    "prior_drop": 1.0,      # اتّجاهٌ سابق (HS-E9): هبوطُ ما قبل الكتف الأيسر بارتفاع النموذج على الأقلّ
    "prior_bars": 3,        # §⑤-ب ‏+ والهبوطُ السابق (P0 ⟵ الكتف الأيسر) يمتدّ k بارات على الأقلّ — شمعةُ ارتدادٍ واحدةٌ ليست اتّجاهًا (SCWO)
    "brk_atr": 0.1,         # الاختراقُ = **إغلاقٌ** فوق خطّ العنق بعُشر ATR (اللمسُ ليس اختراقًا)
    "wait_mult": 1.5,       # الاختراقُ خلال 1.5 × (الرأس ⟵ الكتف الأيمن) من الكتف الأيمن وإلّا انتهت صلاحيتُه
    "retest_win": 10,       # إعادةُ الاختبار: عودةٌ إلى خطّ العنق خلال 10 بارات من الاختراق
    "retest_away": 0.25,    # «ابتعادٌ» قبل العودة = قمّةٌ فوق خطّ العنق بربع الارتفاع (بلا ابتعادٍ لا «عودة»)
    "retest_band": 0.10,    # «عودةٌ» = قاعٌ حتى خطّ العنق ‏+ عُشر الارتفاع
    "cont_win": 10,         # «استمرار» = إغلاقٌ فوق أعلى قمّةٍ بين الاختراق والعودة خلال 10 بارات من العودة
    "fail_tol": 0.10,       # «فشل» = إغلاقٌ تحت خطّ العنق بعُشر الارتفاع قبل الاستمرار
    "horizon": 30,          # أفقُ القياس بعد الإشارة (‏+30 جلسة · أعلى ارتفاع · أكبر هبوط · الهدف)
}
LOOSE = dict(STRICT, swing_atr=0.75, height_min_atr=1.0, shoulder_tol=0.75, neck_slope=0.75,
             time_sym=4.0, prior_drop=0.5, brk_atr=0.0)
CONFIGS = {"STRICT": STRICT, "LOOSE": LOOSE}
HORIZONS = (1, 3, 5, 10, 20, 30)
INTRADAY_HORIZONS = (1, 3, 6, 12)          # بارات 5 دقائق = 5 · 15 · 30 · 60 دقيقة
CONTROL_WBS = (15, 30, 60, 100)            # نوافذُ اختراق النطاق المطابِقة لعرض النموذج
CONTROL_PER_SIGNAL = 10
BOOT_B = 2000
BOOT_SEED = 20261001
MIN_N_YEAR = 30
VOL_MULT = 1.5                             # ذراعُ الحجم: حجمُ بار الاختراق ÷ وسيط حجم النموذج
CCI_MIN = 100.0                            # ذراعُ CCI(14)
Q_MIN = 66                                 # ذراعُ الجودة (الثلثُ الأعلى تقريبًا)
SPLIT_PAD_DAYS = 45                        # نافذةُ استبعاد التقسيم بعد الاختراق (أيّامُ تقويم)
DEV_YEAR, VERDICT_YEARS, DESC_YEAR = 2022, (2023, 2024, 2025), 2026
DATA_START = "2021-06-01"
AUDIT_N = 30
AUDIT_SEED = 20261002                       # §⑤-ب: العيّنةُ الثانية (بذرة +1) بعد إصلاح التعريف — والأولى (20261001) دقّتُها 19/30
AUDIT_ITER = 2                             # التكرارُ الثاني والأخير (حدٌّ أقصى مرّتان · العقد §⑤)
AUDIT_MIN_PRECISION = 0.70
SCAN_MIN_COVERAGE = 0.85                   # حارسُ التغطية للمسح الحيّ (كحرّاس الصيّادين)
SCAN_LOOKBACK = 1                          # المسحُ يرى اختراقَ آخر جلسة والتي قبلها (كرونٌ سقط لا يُفوّت)
SCAN_DAYS = 700                            # نافذةُ الشموع الحيّة (أيّامُ تقويم ⟵ ‏≈480 جلسة تكفي أقصى عمرٍ للرأس ‏+ ما قبله)
SCAN_MAX_MSGS = 5                          # حدُّ الرسائل اليوميّ بترتيب الجودة — والباقي سطرٌ واحدٌ بأسمائهم (العقد §⑪)
LOOKBACK = {"1d": 40, "5m": 78}
POP_FILE = "hs_population.json"
RES_DIR = "hs_research"
STATE_FILE = "hs_state.json"
CHART_DIR = os.environ.get("HS_CHART_DIR", ".")    # الشارتُ المُرسَل (لا يُدفَع · `hs_*.png` في .gitignore)
EXCLUDED_HUNTERS = ("control", "envelope")  # عيّناتٌ عشوائيّة · وصيّادُ الظرف صامتٌ بقرار (لم يظهر للمالك)


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ① المؤشّرات والمحاور (نقيّة)
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def atr_np(h, l, c, n: int = 14) -> np.ndarray:
    """ATR بصيغة `S.atr` حرفًا (EMA بمعامل 1/n · `min_periods=n` · `adjust=False`) على مصفوفات."""
    h, l, c = (pd.Series(np.asarray(x, dtype=float)) for x in (h, l, c))
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / n, min_periods=n, adjust=False).mean().to_numpy()


def fsto_np(h, l, c, period: int = 14, k_s: int = 3, d_s: int = 3):
    """FSTO(14,3) بصيغة `S.full_stoch` (نوافذُ متدحرجة تنتهي عند البار ⟵ سببيّة) ⟵ (K, D)."""
    h, l, c = (pd.Series(np.asarray(x, dtype=float)) for x in (h, l, c))
    ll, hh = l.rolling(period).min(), h.rolling(period).max()
    fk = (c - ll) / (hh - ll).replace(0, np.nan) * 100.0
    k = fk.rolling(k_s).mean()
    return k.to_numpy(), k.rolling(d_s).mean().to_numpy()


def cci_at(h, l, c, i: int, period: int = 14):
    """CCI(14) عند البار `i` وحدَه بصيغة `S.cci` (آخر `period` بارات تنتهي عند i ⟵ سببيّ) · None بلا عيّنة."""
    if i < period - 1:
        return None
    tp = (np.asarray(h[i - period + 1:i + 1], float) + np.asarray(l[i - period + 1:i + 1], float)
          + np.asarray(c[i - period + 1:i + 1], float)) / 3.0
    if not np.all(np.isfinite(tp)):
        return None
    md = float(np.mean(np.abs(tp - tp.mean())))
    if not md:
        return None
    return float((tp[-1] - tp.mean()) / (0.015 * md))


def fractal_swings(h, l, k: int):
    """محاورُ فركتاليّة: قاعٌ عند i إن كان **أدنى بصرامة** من k قبله و**لا يعلوه** ما بعده بـk (أوّلُ القاع المسطّح) · والقمّةُ مرآتُه ·
    ⟵ [(i, "L"|"H", السعر)] مرتّبة بـi · **ويُعرَف كلٌّ عند i + k** (يُطبَّق في `detect`)."""
    h = np.asarray(h, dtype=float)
    l = np.asarray(l, dtype=float)
    n = len(h)
    out = []
    for i in range(k, n - k):
        lo, hi = l[i], h[i]
        if np.isfinite(lo) and lo < np.nanmin(l[i - k:i]) and lo <= np.nanmin(l[i + 1:i + k + 1]):
            out.append((i, "L", float(lo)))
        if np.isfinite(hi) and hi > np.nanmax(h[i - k:i]) and hi >= np.nanmax(h[i + 1:i + k + 1]):
            out.append((i, "H", float(hi)))
    return out


def zz_add(Z: list, sw, atr_at: float, swing_atr: float) -> None:
    """زجزاجٌ تزايديّ بعتبة ATR: محورٌ من نوع الأخير ⟵ يحلّ محلَّه إن كان أشدّ تطرّفًا · ومن النوع الآخر ⟵ يُضاف إن بلغ
    الانعكاسُ `swing_atr × ATR` وإلّا فضجيجٌ يُهمَل. ⟵ تسلسلٌ متناوبٌ L/H حتميّ من المحاور الظاهرة وحدَها."""
    if not Z:
        Z.append(sw)
        return
    last = Z[-1]
    if sw[1] == last[1]:
        if (sw[1] == "L" and sw[2] < last[2]) or (sw[1] == "H" and sw[2] > last[2]):
            Z[-1] = sw
        return
    if np.isfinite(atr_at) and abs(sw[2] - last[2]) >= swing_atr * atr_at:
        Z.append(sw)


def structures(Z: list, t: int = None, max_age: int = None) -> list:
    """البُنى المرشّحة **مرساتُها الرأس** (HS-E1): كلُّ قاعٍ في الزجزاج أدنى من كلّ قاعٍ بعده (رأسٌ محتمل) ⟵ الكتفُ الأيسر أحدُ القاعين
    السابقين (Z[j−2] أو Z[j−4] · وقمّةُ الارتداد الأولى P1 = Z[j−1] أو Z[j−3]) وقمّةُ الارتداد الثانية P2 إحدى القمّتين التاليتين
    (Z[j+1] أو Z[j+3]) — **فالتذبذبُ داخل كتفٍ لا يُضيّع
    النموذج** · وما تخطّته البنيةُ من قممٍ وقيعان يُحمَل (`mids` · `lows`) فيُفحص: القممُ المتخطّاة تحت خطّ العنق · والقاعُ المتخطّى
    القريبُ من عمق الرأس = **رأسٌ مركّب** (HS-E8 · «القاع الأول · القاع الثاني»). ترتيبُ المحاولة: الأبسطُ أوّلًا."""
    out = []
    if len(Z) < 5:
        return out
    run_min, cands = math.inf, []
    for j in range(len(Z) - 1, -1, -1):
        if Z[j][1] == "L" and Z[j][2] < run_min:
            run_min = Z[j][2]
            cands.append(j)
    for j in cands:
        if t is not None and max_age is not None and t - Z[j][0] > max_age:
            continue
        if j - 1 < 0 or Z[j - 1][1] != "H":
            continue
        for ls_j in (j - 2, j - 4):
            if ls_j - 1 < 0:
                continue
            for p1_j in ((j - 1,) if ls_j == j - 2 else (j - 1, j - 3)):   # j−3: رأسٌ مركّبٌ أعمقُ قاعيه الثاني
                for p2_j in (j + 1, j + 3):                                 # j+3: رأسٌ مركّبٌ أعمقُ قاعيه الأوّل
                    if p2_j >= len(Z):
                        continue
                    out.append({"p0": Z[ls_j - 1], "ls": Z[ls_j], "p1": Z[p1_j], "head": Z[j], "p2": Z[p2_j],
                                "mids": [Z[x] for x in range(ls_j + 1, p2_j) if Z[x][1] == "H" and x not in (p1_j,)],
                                "lows": [Z[x] for x in range(ls_j + 1, p2_j) if Z[x][1] == "L" and x != j]})
    return out


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ② الكشف (سببيّ: كلُّ قرارٍ عند t لا يقرأ إلّا بارات ≤ t)
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _arrays(df, polarity: str = "inverse"):
    o = df["Open"].to_numpy(dtype=float)
    h = df["High"].to_numpy(dtype=float)
    l = df["Low"].to_numpy(dtype=float)
    c = df["Close"].to_numpy(dtype=float)
    v = df["Volume"].to_numpy(dtype=float) if "Volume" in df else np.full(len(c), np.nan)
    if polarity == "top":                    # المرآة: القمّةُ نموذجٌ مقلوبٌ على السعر السالب
        o, h, l, c = -o, -l, -h, -c
    return o, h, l, c, v


def _neck_fn(p1, p2):
    slope = (p2[2] - p1[2]) / float(p2[0] - p1[0])
    return (lambda x: p1[2] + slope * (x - p1[0])), slope


def _rej(why, rule: str):
    """سببُ الرفض لمن يسأل (`why` قائمة) — وإلّا None كما كان: الرفضُ نفسُه لا يتغيّر بالسؤال عنه."""
    if why is not None:
        why.append(rule)
    return None


def _evaluate(st, t, h, l, c, a, p, session=None, probe: bool = False, expiry: bool = True, why: list = None):
    """هل تكتمل البنيةُ `st` باختراقٍ **مؤكَّدٍ بالإغلاق** عند البار t؟ ⟵ قاموسُ الإشارة أو None. يقرأ بارات ≤ t وحدَها.
    `probe=True` (لدورة الحياة قبل الاختراق): الكتفُ الأيمن يشمل البار t ولا يُشترط الإغلاقُ — ويُشترط **ألّا يكون** قد اخترق
    حتى t · و`expiry=False` يُبقي البنيةَ المنتهيةَ صلاحيتُها (لتُوسَم EXPIRED لا لتُرسَل). و`why` (اختياريّ) يتلقّى اسمَ أوّل قاعدةٍ رفضت."""
    p0, ls, p1, hd, p2 = st["p0"], st["ls"], st["p1"], st["head"], st["p2"]
    P2i = p2[0]
    if p0 is None or (t - P2i) < (1 if probe else 2) or not np.isfinite(a[t]) or a[t] <= 0:
        return _rej(why, "pre")
    neck, slope = _neck_fn(p1, p2)
    at = float(a[t])
    thr_t = neck(t) + p["brk_atr"] * at
    if not probe and not c[t] >= thr_t:                                           # HS-E6 إغلاقٌ لا لمس (رفضٌ رخيص أوّلًا)
        return _rej(why, "close")
    end = t + 1 if probe else t
    seg = l[P2i + 1:end]
    if not len(seg) or not np.isfinite(seg).any():
        return _rej(why, "rs_seg")
    RSi = P2i + 1 + int(np.nanargmin(seg))
    RS = float(l[RSi])
    H, LS = hd[2], ls[2]
    height = neck(hd[0]) - H
    if not (height > 0 and H < LS and H < RS):                                   # HS-E1 الرأسُ الأعمق
        return _rej(why, "head_lowest")
    if np.nanmin(l[ls[0]:P2i + 1]) < H:                                           # لا قاعَ أدنى من الرأس داخل النموذج
        return _rej(why, "head_min")
    if min(LS, RS) - H < p["head_min_atr"] * at:
        return _rej(why, "head_depth")
    if height < p["height_min_atr"] * at:
        return _rej(why, "height_atr")
    if height < p["height_min_pct"] * abs(float(c[t])):                          # §⑤-ب نسبةٌ من السعر (المرآةُ سالبة ⟵ abs)
        return _rej(why, "height_pct")
    if abs(LS - RS) > p["shoulder_tol"] * height:                                 # HS-E3
        return _rej(why, "shoulder_tol")
    if neck(ls[0]) - LS < p["shoulder_depth"] * height or neck(RSi) - RS < p["shoulder_depth"] * height:
        return _rej(why, "shoulder_depth")
    if abs(p2[2] - p1[2]) > p["neck_slope"] * height:                             # HS-E4 أفقيٌّ أو مائل
        return _rej(why, "neck_slope")
    d1, d2 = hd[0] - ls[0], RSi - hd[0]
    if d1 < 1 or d2 < 1 or max(d1, d2) / float(min(d1, d2)) > p["time_sym"]:     # HS-E10 تناظرٌ لا «12 شمعة»
        return _rej(why, "time_sym")
    span = RSi - ls[0]
    if span < p["min_span"] or span > p["max_span"]:
        return _rej(why, "span")
    if p0[2] - LS < p["prior_drop"] * height:                                     # HS-E9 اتّجاهٌ سابق
        return _rej(why, "prior_drop")
    if ls[0] - p0[0] < p["prior_bars"]:                                           # §⑤-ب اتّجاهٌ لا شمعةُ ارتداد
        return _rej(why, "prior_bars")
    expired = t - RSi > max(p["k"] + 1, p["wait_mult"] * d2)
    if expiry and expired:                                                        # انتهت الصلاحية
        return _rej(why, "expired")
    if any(m[2] > neck(m[0]) - p["mid_gap"] * height for m in st.get("mids") or []):  # القممُ المتخطّاة تحت خطّ العنق
        return _rej(why, "mids")
    deep = [x for x in st.get("lows") or [] if x[2] < min(LS, RS) - p["head_min_atr"] * at]  # HS-E8 الرأسُ المركّب
    if session is not None and not (session[p0[0]] == session[t]):               # داخل جلسةٍ واحدة (5 دقائق)
        return _rej(why, "session")
    xs = np.arange(P2i + 1, end)
    if len(xs) and np.any(c[xs] >= neck(xs) + p["brk_atr"] * a[xs]):              # الاختراقُ الأوّل وحدَه
        return _rej(why, "not_first")
    return {"p0_i": p0[0], "p0_px": p0[2], "ls_i": ls[0], "ls_px": LS, "p1_i": p1[0], "p1_px": p1[2],
            "head_i": hd[0], "head_px": H, "p2_i": P2i, "p2_px": p2[2], "rs_i": RSi, "rs_px": RS,
            "pm_i": (deep[0][0] if deep else None), "b_i": int(t), "neck_b": float(neck(t)), "neck_slope": float(slope),
            "thr_b": float(thr_t), "height": float(height), "atr_b": at, "compound": bool(deep),
            "expired": bool(expired), "mids": [(int(m[0]), float(m[2])) for m in st.get("mids") or []]}


def _zigzag_until(sw, a, p, t):
    Z = []
    for s in sw:
        if s[0] + p["k"] <= t:
            zz_add(Z, s, a[s[0] + p["k"]], p["swing_atr"])
    return Z


def _max_age(p) -> int:
    """أقصى عمرٍ للرأس عند الاختراق: الكتفُ الأيمن حتى `max_span` بعد الأيسر ‏+ نافذةُ الانتظار (`wait_mult` × مدّة الجانب الأيمن)."""
    return int((1 + p["wait_mult"]) * p["max_span"]) + p["k"] + 1


def _walk(h, l, a, p, n: int):
    """المشيُ السببيُّ الواحد (`detect` و`explain_miss` معًا): لكلّ بار t ⟵ (t, البنى المرشّحة، الزجزاج) من محاورَ **مؤكَّدةٍ عند t
    وحدَها** (المحورُ عند i يُعرَف عند i + k) — فلا يختلف ما يراه التشخيصُ عمّا رآه الكاشف."""
    sw = fractal_swings(h, l, p["k"])
    Z, si, cand = [], 0, []
    for t in range(n):
        grew = False
        while si < len(sw) and sw[si][0] + p["k"] <= t:
            zz_add(Z, sw[si], a[sw[si][0] + p["k"]], p["swing_atr"])
            si += 1
            grew = True
        if grew:
            cand = structures(Z)
        yield t, cand, Z


def detect(df, p=None, polarity: str = "inverse", sym: str = "", tf: str = "1d", session=None) -> list:
    """كلُّ إشارات النموذج في الإطار — **سببيًّا**: يمشي t بارًا بارًا · والمحورُ يظهر عند i + k · و**إشارةٌ واحدةٌ لكلّ رأس**
    (فالتكوينُ الواحد لا يُرسَل مرّتين بأيّ كتفٍ أو قمّة) ولكلّ بار. `polarity="top"` = المرآة (القمّة) للتحقّق البنيويّ وحدَه.
    `session` (اختياريّ): مصفوفةُ يوم الجلسة لكلّ بار ⟵ النموذجُ كلُّه داخل جلسةٍ واحدة (فريم 5 دقائق)."""
    p = dict(STRICT if p is None else p)
    if df is None or len(df) < 2 * p["k"] + 10:
        return []
    o, h, l, c, v = _arrays(df, polarity)
    a = atr_np(h, l, c, p["atr_n"])
    fk, fd = fsto_np(h, l, c)
    used, sigs = set(), []
    age = _max_age(p)
    for t, cand, _Z in _walk(h, l, a, p, len(c)):
        for st in cand:
            hk = st["head"][0]
            if hk in used or t - hk > age:
                continue
            s = _evaluate(st, t, h, l, c, a, p, session)
            if s is None:
                continue
            used.add(hk)
            sigs.append(_finalize(s, df, o, h, l, c, v, a, fk, fd, p, polarity, sym, tf))
            break
    return sigs


def _finalize(s, df, o, h, l, c, v, a, fk, fd, p, polarity, sym, tf):
    """الإشارةُ بأسعارها الحقيقيّة (المرآةُ تُعكَس) وتواريخِها ومعرّفِها وجودتِها وحقولِ الأذرع — كلُّها من بارات ≤ b."""
    sgn = -1.0 if polarity == "top" else 1.0
    idx = df.index
    b = s["b_i"]

    def d(i):
        return None if i is None else str(idx[i])[:16 if tf != "1d" else 10]
    vol = v[s["ls_i"]:b]
    vr = None
    if len(vol) and np.isfinite(vol).any() and np.isfinite(v[b]):
        med = float(np.nanmedian(vol))
        if med > 0:
            vr = float(v[b] / med)
    kb, db = fk[b], fd[b]
    if polarity == "top":                    # FSTO على المرآة = 100 − FSTO الحقيقيّ
        kb, db = 100.0 - kb, 100.0 - db
    cc = cci_at(h, l, c, b)                  # CCI خطّيّ ⟵ المرآةُ تعكس الإشارة
    out = dict(s)
    out.update({
        "sym": sym, "tf": tf, "polarity": polarity,
        "pid": f"{sym}|{tf}|{polarity}|{d(s['ls_i'])}|{d(s['head_i'])}",
        "p0_date": d(s["p0_i"]), "ls_date": d(s["ls_i"]), "head_date": d(s["head_i"]), "rs_date": d(s["rs_i"]),
        "b_date": d(b), "entry": float(sgn * c[b]), "vol_ratio": vr,
        "fsto_k": (float(kb) if np.isfinite(kb) else None), "fsto_d": (float(db) if np.isfinite(db) else None),
        "cci": (None if cc is None else float(sgn * cc)),
    })
    for f in ("p0_px", "ls_px", "p1_px", "head_px", "p2_px", "rs_px", "neck_b", "thr_b"):
        out[f] = float(sgn * out[f])
    out["mids"] = [(i, float(sgn * px)) for i, px in s.get("mids") or []]
    out["neck_slope"] = float(sgn * out["neck_slope"])
    out["neck_type"] = ("horizontal" if abs(s["p2_px"] - s["p1_px"]) <= 0.1 * s["height"]
                        else ("ascending" if out["neck_slope"] > 0 else "descending"))
    out["target"] = float(out["neck_b"] + sgn * out["height"])               # الحركةُ المقيسة الكلاسيكيّة (نظريّ)
    # «منشأُ الهبوط» (P0 · قاعدةُ فيصل العامّة «منشأُ الهبوط مقاومة/هدف» — EZRA) — **مستنتَجٌ للمقارنة لا هدفُ فيصل للنموذج**
    out["target_p0"] = float(out["p0_px"]) if sgn * (out["p0_px"] - out["entry"]) > 0 else None
    out["quality"] = quality(s, c, a, vr, p)
    out["span"] = int(s["rs_i"] - s["ls_i"])
    out["width"] = int(b - s["ls_i"])
    return out


def quality(s, c, a, vol_ratio, p) -> int:
    """جودةُ التطابق 0-100 — **وصفٌ لا وعد** (متوسّطُ سبعة مكوّناتٍ بين 0 و1 من بارات ≤ b)."""
    h_ = s["height"]
    d1, d2 = s["head_i"] - s["ls_i"], s["rs_i"] - s["head_i"]
    ratio = max(d1, d2) / float(max(1, min(d1, d2)))
    neck_b = s["neck_b"]
    comps = [
        1 - min(1.0, abs(s["ls_px"] - s["rs_px"]) / (p["shoulder_tol"] * h_)),
        1 - min(1.0, (ratio - 1) / max(1e-9, p["time_sym"] - 1)),
        min(1.0, (min(s["ls_px"], s["rs_px"]) - s["head_px"]) / (0.5 * h_)),
        1 - min(1.0, abs(s["p2_px"] - s["p1_px"]) / (p["neck_slope"] * h_)),
        max(0.0, min(1.0, (c[s["b_i"]] - neck_b) / max(1e-9, a[s["b_i"]]))),
        0.5 if vol_ratio is None else min(1.0, vol_ratio / 2.0),
        min(1.0, (s["p0_px"] - s["ls_px"]) / (2.0 * h_)),
    ]
    return int(round(100 * max(0.0, min(1.0, float(np.mean(comps))))))


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ③ ما بعد الإشارة — **يقرأ المستقبل للقياس وحدَه** (لا يناديه `detect`)
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _neck_at(sig, x):
    return sig["neck_b"] + sig["neck_slope"] * (x - sig["b_i"])


def retest_state(df, sig, p=None) -> dict:
    """إعادةُ الاختبار بعد الاختراق (HS-E7 · «اختراق ⟵ عودة لخطّ العنق ⟵ ثبات ⟵ استمرار» بنصّ أمر المالك):
    «ابتعاد» = قمّةٌ فوق خطّ العنق بـ`retest_away` من الارتفاع (بلا ابتعادٍ لا عودة — الحومُ عند الخطّ ليس إعادةَ اختبار) ·
    «عودة» = بعد الابتعاد قاعٌ حتى خطّ العنق ‏+ `retest_band` من الارتفاع خلال `retest_win` من الاختراق · «استمرار» = إغلاقٌ فوق أعلى
    قمّةٍ بين الاختراق والعودة خلال `cont_win` من العودة · «فشل» = إغلاقٌ تحت خطّ العنق بـ`fail_tol` من الارتفاع قبل الاستمرار ⟵
    success · failed_retest (فشلٌ بعد العودة) · failed_breakout (فشلٌ قبلها) · none (ابتعد ولم يعُد = استمرارٌ مباشر) ·
    touch_no_follow (عاد وثبت ولم يواصل) · stalled (حام فوق الخطّ بلا ابتعادٍ ولا فشل) · pending (النافذةُ لم تكتمل)."""
    p = dict(STRICT if p is None else p)
    h = df["High"].to_numpy(dtype=float)
    l = df["Low"].to_numpy(dtype=float)
    c = df["Close"].to_numpy(dtype=float)
    b, ht, n = sig["b_i"], sig["height"], len(c)
    touch = fail = cont = None
    peak = h[b]
    away = b if h[b] >= _neck_at(sig, b) + p["retest_away"] * ht else None
    x = b + 1
    while x < n:
        nk = _neck_at(sig, x)
        if c[x] < nk - p["fail_tol"] * ht:
            fail = x
            break
        if touch is None:
            if x > b + p["retest_win"]:
                break
            if away is not None and l[x] <= nk + p["retest_band"] * ht:
                touch = x
            else:
                peak = max(peak, h[x])
                if away is None and h[x] >= nk + p["retest_away"] * ht:
                    away = x
        else:
            if x > touch + p["cont_win"]:
                break
            if c[x] > peak:
                cont = x
                break
        x += 1
    if fail is not None:
        st = "failed_retest" if touch is not None else "failed_breakout"
    elif cont is not None:
        st = "success"
    elif touch is not None:
        st = "touch_no_follow" if touch + p["cont_win"] < n else "pending"
    elif b + p["retest_win"] < n:
        st = "none" if away is not None else "stalled"
    else:
        st = "pending"
    return {"retest": st, "touch_i": touch, "fail_i": fail, "cont_i": cont, "away_i": away, "peak": float(peak)}


def outcomes(df, sig, p=None, entry_i=None, horizons=HORIZONS, session=None) -> dict:
    """ما حدث بعد الدخول (سعرُ الإغلاق عند `entry_i` · افتراضيًّا بار الاختراق): العائدُ عند كلّ أفق · أعلى ارتفاع (سعرُه وتاريخُه
    وشموعُه) وأكبر هبوط خلال `horizon` · بلوغُ الهدف (تاريخُه وشموعُه) · ومستوى «منشأ الهبوط» · وإبطالٌ (إغلاقٌ تحت قاع الرأس) ·
    و`session` يقصّ على نهاية الجلسة (5 دقائق)."""
    p = dict(STRICT if p is None else p)
    h = df["High"].to_numpy(dtype=float)
    l = df["Low"].to_numpy(dtype=float)
    c = df["Close"].to_numpy(dtype=float)
    idx = df.index
    n = len(c)
    e = sig["b_i"] if entry_i is None else int(entry_i)
    entry = float(c[e])
    end = n
    if session is not None:
        same = np.nonzero(np.asarray(session) == session[e])[0]
        end = int(same[-1]) + 1
    res = {"entry_i": e, "entry_date": str(idx[e])[:16], "entry_px": entry}
    for hz in horizons:
        res[f"ret{hz}"] = (float(c[e + hz] / entry - 1) if e + hz < end else None)
    stop = min(end, e + 1 + p["horizon"])
    if session is not None:
        res["ret_eod"] = float(c[end - 1] / entry - 1) if end - 1 > e else None
    if stop <= e + 1:
        res.update(mfe=None, mae=None, max_high=None, min_low=None, mfe_bars=None, mae_bars=None, mfe_date=None,
                   mae_date=None, target_hit=False, target_bars=None, target_date=None, p0_hit=None, p0_bars=None,
                   invalid_bars=None, complete=False)
        return res
    hw, lw, cw = h[e + 1:stop], l[e + 1:stop], c[e + 1:stop]
    im, il = int(np.nanargmax(hw)), int(np.nanargmin(lw))
    tgt = sig.get("target")
    th = np.nonzero(hw >= tgt)[0] if tgt is not None else np.array([], dtype=int)
    t0 = sig.get("target_p0")
    tp0 = np.nonzero(hw >= t0)[0] if t0 is not None else None
    iv = np.nonzero(cw < sig["head_px"])[0]
    res.update(mfe=float(hw[im] / entry - 1), mae=float(lw[il] / entry - 1), max_high=float(hw[im]), min_low=float(lw[il]),
               mfe_bars=im + 1, mae_bars=il + 1, mfe_date=str(idx[e + 1 + im])[:16], mae_date=str(idx[e + 1 + il])[:16],
               target_hit=bool(len(th)), target_bars=(int(th[0]) + 1 if len(th) else None),
               target_date=(str(idx[e + 1 + int(th[0])])[:16] if len(th) else None),
               p0_hit=(None if tp0 is None else bool(len(tp0))), p0_bars=(int(tp0[0]) + 1 if tp0 is not None and len(tp0) else None),
               invalid_bars=(int(iv[0]) + 1 if len(iv) else None),
               complete=bool(e + p["horizon"] < end))
    return res


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ④ الضبط — اختراقُ نطاقٍ بلا بنية النموذج، مطابَقًا بعرض النافذة والزخم (سببيٌّ عند t)
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def w_bucket(width: int) -> int:
    """عرضُ النموذج (الكتف الأيسر ⟵ الاختراق) ⟵ نافذةُ الضبط المطابِقة."""
    return 15 if width < 20 else 30 if width < 40 else 60 if width < 80 else 100


def control_events(df, sig_bars=(), wbs=CONTROL_WBS) -> list:
    """أحداثُ الضبط: **أوّلُ إغلاقٍ فوق أعلى قمّةٍ في آخر Wb بار** (اختراقُ نطاقٍ عامّ) بلا بنية رأسٍ وكتفين ·
    والمستبعَدُ ما وقع خلال ±Wb من إشارة نموذج · وكلُّ حدثٍ «إشارةٌ» بخطّ عنقٍ أفقيٍّ عند أعلى النطاق وارتفاعِ النطاق
    وهدفٍ مماثلٍ للحركة المقيسة ⟵ فيُقاس بالدالّتين نفسَيهما (`outcomes` · `retest_state`)."""
    h = df["High"].to_numpy(dtype=float)
    l = df["Low"].to_numpy(dtype=float)
    c = df["Close"].to_numpy(dtype=float)
    idx = df.index
    n = len(c)
    sb = np.asarray(sorted(set(int(x) for x in sig_bars)), dtype=int)
    out = []
    for wb in wbs:
        if n <= wb + 21:
            continue
        hh = pd.Series(h).rolling(wb).max().shift(1).to_numpy()
        for t in range(max(wb + 1, 21), n):
            if not (np.isfinite(hh[t]) and np.isfinite(hh[t - 1])) or not (c[t] > hh[t] and c[t - 1] <= hh[t - 1]):
                continue
            if len(sb) and np.any(np.abs(sb - t) <= wb):
                continue
            lo = float(np.nanmin(l[t - wb:t]))
            level = float(hh[t])
            height = level - lo
            if not height > 0 or not c[t - 20] > 0:
                continue
            out.append({"b_i": t, "b_date": str(idx[t])[:10], "wb": wb, "neck_b": level, "neck_slope": 0.0,
                        "height": height, "head_px": lo, "target": level + height, "target_p0": None, "entry": float(c[t]),
                        "ret20_prior": float(c[t] / c[t - 20] - 1)})
    return out


def momentum_tercile(x: float, cuts) -> int:
    return 0 if x <= cuts[0] else 1 if x <= cuts[1] else 2


def sample_controls(sig_pid: str, pool: list, m: int = CONTROL_PER_SIGNAL) -> list:
    """عيّنةٌ حتميّة (بذرةٌ من `crc32(pid)` لا `hash` العشوائيّ) بلا إعادةٍ داخل الإشارة."""
    if not pool:
        return []
    rng = np.random.default_rng(zlib.crc32(sig_pid.encode("utf-8")))
    k = min(m, len(pool))
    return [pool[i] for i in rng.choice(len(pool), size=k, replace=False)]


def boot_median_diff(sig_vals, ctrl_lists, b: int = BOOT_B, seed: int = BOOT_SEED):
    """(الفرقُ المقيس, حدٌّ أدنى 2.5%, أعلى 97.5%) لـ median(الإشارات) − median(ضبطِها المجمَّع) · إعادةُ عيّنةٍ للإشارات مع ضبطها."""
    sv = np.asarray(sig_vals, dtype=float)
    if len(sv) == 0 or not any(len(x) for x in ctrl_lists):
        return None, None, None
    m = max(len(x) for x in ctrl_lists)
    M = np.full((len(sv), m), np.nan)
    for i, cl in enumerate(ctrl_lists):
        M[i, :len(cl)] = cl
    diff = float(np.median(sv) - np.nanmedian(M))
    rng = np.random.default_rng(seed)
    ds = []
    n = len(sv)
    for _ in range(b):
        ix = rng.integers(0, n, n)
        cp = M[ix]
        if not np.isfinite(cp).any():
            continue
        ds.append(np.median(sv[ix]) - np.nanmedian(cp))
    if not ds:
        return diff, None, None
    return diff, float(np.percentile(ds, 2.5)), float(np.percentile(ds, 97.5))


def wilson(k: int, n: int, z: float = 1.96):
    if not n:
        return None, None
    ph = k / n
    den = 1 + z * z / n
    mid = (ph + z * z / (2 * n)) / den
    half = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return max(0.0, mid - half), min(1.0, mid + half)


def dist(vals) -> dict:
    """وسيطٌ ومتوسّطٌ وأقصى وأدنى ومئينات — **فلا يُخفي الشاذُّ المعتاد** (أمرُ «DO NOT HIDE OUTLIERS»)."""
    x = np.asarray([v for v in vals if v is not None and np.isfinite(v)], dtype=float)
    if not len(x):
        return {"n": 0}
    return {"n": int(len(x)), "median": float(np.median(x)), "mean": float(np.mean(x)), "min": float(x.min()),
            "max": float(x.max()), "p10": float(np.percentile(x, 10)), "p25": float(np.percentile(x, 25)),
            "p75": float(np.percentile(x, 75)), "p90": float(np.percentile(x, 90))}


def verdict_branch(per_year: dict, years=VERDICT_YEARS, min_n: int = MIN_N_YEAR) -> tuple:
    """الحكمُ بالأضعف (العقد §⑥): الفرعُ 1 «ميزةٌ مقيسة» = في **كلّ** سنةٍ n ≥ 30 وحدُّ الفاصل الأدنى لفرق الوسيط (ret10) فوق
    الصفر · الفرعُ 2 «لا ميزة على الضبط» = n ≥ 30 في كلّ سنة وسقطت سنةٌ على الأقلّ · الفرعُ 3 «لا قياس» = سنةٌ دون 30."""
    rows = [per_year.get(y) or {} for y in years]
    if any((r.get("n") or 0) < min_n for r in rows):
        return 3, "لا قياس"
    if all((r.get("ci_lo") is not None and r["ci_lo"] > 0) for r in rows):
        return 1, "ميزةٌ مقيسة على الضبط"
    return 2, "لا ميزة على الضبط"


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ⑤ دورةُ الحياة عند آخر بار (للمسح الحيّ وفحص السهم) — من بارات ≤ آخر بار
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
LIFECYCLE = ("FORMING", "COMPLETED", "BREAKOUT_PENDING", "BREAKOUT_CONFIRMED", "RETEST_PENDING", "RETEST_CONFIRMED",
             "NO_RETEST", "RETEST_NO_FOLLOW", "STALLED", "TARGET_REACHED", "FAILED", "EXPIRED", "NONE", "NO_DATA")


def signal_state(df, sig, p=None) -> tuple:
    """حالةُ اختراقٍ مؤكَّد عند آخر بار ⟵ (الحالة, إعادةُ الاختبار). الأحداثُ النهائيّة بالأسبق: بلوغُ الهدف · فشلُ الاختراق/العودة ·
    إبطالٌ (إغلاقٌ تحت قاع الرأس) — والتعادلُ يُقرأ فشلًا (الأحوط)."""
    p = dict(STRICT if p is None else p)
    h = df["High"].to_numpy(dtype=float)
    c = df["Close"].to_numpy(dtype=float)
    n, b = len(c), sig["b_i"]
    rt = retest_state(df, sig, p)
    after = np.arange(b + 1, n)
    t_tgt = next((int(x) for x in after if h[x] >= sig["target"]), None)
    t_inv = next((int(x) for x in after if c[x] < sig["head_px"]), None)
    fails = [x for x in (t_inv, rt["fail_i"]) if x is not None]
    t_fail = min(fails) if fails else None
    if t_fail is not None and (t_tgt is None or t_fail <= t_tgt):
        return "FAILED", rt
    if t_tgt is not None:
        return "TARGET_REACHED", rt
    if b == n - 1:
        return "BREAKOUT_CONFIRMED", rt
    return {"success": "RETEST_CONFIRMED", "none": "NO_RETEST", "touch_no_follow": "RETEST_NO_FOLLOW",
            "stalled": "STALLED"}.get(rt["retest"], "RETEST_PENDING"), rt


def pending_structure(df, p=None, session=None):
    """بنيةٌ قائمةٌ عند آخر بار **بلا اختراقٍ مؤكَّد** ⟵ {الحالة · الكتفان · الرأس · خطُّ العنق الآن · المسافة إليه} أو None:
    FORMING (الكتفُ الأيمن لم يتأكّد بعد k بارات) · COMPLETED (تأكّد والسعرُ تحت خطّ العنق) · BREAKOUT_PENDING (لمسه أو أغلق فوقه
    دون عتبة التأكيد) · EXPIRED (مضت نافذةُ الاختراق بلا اختراق)."""
    p = dict(STRICT if p is None else p)
    if df is None or len(df) < 2 * p["k"] + 10:
        return None
    o, h, l, c, v = _arrays(df)
    a = atr_np(h, l, c, p["atr_n"])
    t = len(c) - 1
    Z = _zigzag_until(fractal_swings(h, l, p["k"]), a, p, t)
    for st in structures(Z, t=t, max_age=_max_age(p)):
        s = _evaluate(st, t, h, l, c, a, p, session=session, probe=True, expiry=False)
        if s is None:
            continue
        neck_now = s["neck_b"]
        if s["expired"]:
            state = "EXPIRED"
        elif h[t] >= neck_now:
            state = "BREAKOUT_PENDING"
        elif s["rs_i"] + p["k"] <= t:
            state = "COMPLETED"
        else:
            state = "FORMING"
        return {"state": state, "ls_px": s["ls_px"], "head_px": s["head_px"], "rs_px": s["rs_px"], "neck_now": float(neck_now),
                "thr_now": s["thr_b"], "dist_pct": float(neck_now / c[t] - 1), "height": s["height"],
                "target": float(neck_now + s["height"]), "ls_i": s["ls_i"], "head_i": s["head_i"], "rs_i": s["rs_i"],
                "p1_i": s["p1_i"], "p2_i": s["p2_i"], "p1_px": s["p1_px"], "p2_px": s["p2_px"], "b_i": t,
                "neck_b": neck_now, "neck_slope": s["neck_slope"], "compound": s["compound"],
                "ls_date": str(df.index[s["ls_i"]])[:16], "head_date": str(df.index[s["head_i"]])[:16]}
    return None


def lifecycle(df, p=None, sym: str = "", tf: str = "1d", lookback: int = None, session=None) -> dict:
    """حالةُ النموذج عند آخر بار: أحدثُ اختراقٍ خلال `lookback` بارًا بحالته ⟵ وإلّا بنيةٌ قائمةٌ بلا اختراق ⟵ وإلّا «لا نموذج»."""
    p = dict(STRICT if p is None else p)
    if df is None or len(df) < 30:
        return {"state": "NO_DATA"}
    lb = LOOKBACK.get(tf, 40) if lookback is None else int(lookback)
    sigs = detect(df, p, sym=sym, tf=tf, session=session)
    n = len(df)
    recent = [s for s in sigs if s["b_i"] >= n - 1 - lb]
    if recent:
        s = recent[-1]
        state, rt = signal_state(df, s, p)
        return {"state": state, "sig": s, "retest": rt, "new": s["b_i"] == n - 1}
    fm = pending_structure(df, p, session=session)
    if fm:
        return {"state": fm["state"], "forming": fm}
    return {"state": "NONE"}


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ⑥ الشارت (Pillow) — للتحقّق البصريّ ولفحص السهم
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def render_chart(df, sig, path: str, title: str = "", pad_before: int = 20, pad_after: int = 30, rt=None,
                 upto: int = None) -> str:
    """شموعٌ ‏+ خطُّ العنق ‏+ LS/H/RS/P1/P2 ‏+ بارُ الاختراق ‏+ إعادةُ الاختبار ‏+ الهدف (بالإنجليزية — Pillow بلا تشكيلٍ عربيّ).
    `upto` يقصّ الرسمَ عند بارٍ بعينه (التدقيقُ الأعمى يقصّ عند الاختراق فلا يرى المُدقِّقُ ما بعده)."""
    from PIL import Image, ImageDraw
    o = df["Open"].to_numpy(dtype=float)
    h = df["High"].to_numpy(dtype=float)
    l = df["Low"].to_numpy(dtype=float)
    c = df["Close"].to_numpy(dtype=float)
    i0 = max(0, min(sig.get("p0_i", sig["ls_i"]), sig["ls_i"]) - pad_before)
    i1 = min(len(c), sig["b_i"] + pad_after + 1)
    if upto is not None:
        i1 = min(i1, int(upto) + 1)
    W, Hh, ml, mr, mt, mb = 1100, 620, 60, 110, 40, 40
    lo, hi = float(np.nanmin(l[i0:i1])), float(np.nanmax(h[i0:i1]))
    show_tgt = sig.get("target") is not None and np.isfinite(sig["target"]) and upto is None
    if show_tgt:
        lo, hi = min(lo, float(sig["target"])), max(hi, float(sig["target"]))
    rng = (hi - lo) or 1.0
    nb = max(1, i1 - i0)
    bw = (W - ml - mr) / float(nb)

    def X(i):
        return ml + (i - i0 + 0.5) * bw

    def Y(y):
        return mt + (hi - y) / rng * (Hh - mt - mb)
    im = Image.new("RGB", (W, Hh), (255, 255, 255))
    dr = ImageDraw.Draw(im)
    for i in range(i0, i1):
        col = (22, 128, 61) if c[i] >= o[i] else (196, 40, 40)
        dr.line([(X(i), Y(h[i])), (X(i), Y(l[i]))], fill=col, width=1)
        y0, y1 = sorted((Y(o[i]), Y(c[i])))
        dr.rectangle([X(i) - bw * 0.35, y0, X(i) + bw * 0.35, max(y1, y0 + 1)], fill=col)
    xa, xb = sig["p1_i"], min(i1 - 1, sig["b_i"] + 5)
    dr.line([(X(xa), Y(_neck_at(sig, xa))), (X(xb), Y(_neck_at(sig, xb)))], fill=(30, 90, 200), width=2)
    for key, lab in (("ls", "LS"), ("head", "H"), ("rs", "RS")):
        i, y = sig[f"{key}_i"], sig[f"{key}_px"]
        dr.ellipse([X(i) - 5, Y(y) - 5, X(i) + 5, Y(y) + 5], outline=(120, 0, 160), width=2)
        dr.text((X(i) - 8, Y(y) + 8), lab, fill=(120, 0, 160))
    for key, lab in (("p1", "P1"), ("p2", "P2")):
        i, y = sig[f"{key}_i"], sig[f"{key}_px"]
        dr.text((X(i) - 8, Y(y) - 16), lab, fill=(30, 90, 200))
    b = sig["b_i"]
    if b < i1:
        dr.line([(X(b), mt), (X(b), Hh - mb)], fill=(240, 150, 0), width=1)
        dr.text((X(b) + 3, mt + 2), "BO", fill=(240, 150, 0))
    if show_tgt:
        dr.line([(X(b), Y(sig["target"])), (W - mr, Y(sig["target"]))], fill=(0, 150, 150), width=1)
        dr.text((W - mr + 4, Y(sig["target"]) - 6), f"TGT {sig['target']:.4g}", fill=(0, 150, 150))
    if rt and rt.get("touch_i") is not None and rt["touch_i"] < i1:
        ti = rt["touch_i"]
        dr.text((X(ti) - 8, Y(l[ti]) + 6), "RT", fill=(200, 0, 120))
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = lo + frac * rng
        dr.text((W - mr + 4, Y(y) - 6), f"{y:.4g}", fill=(90, 90, 90))
    dr.text((ml, 10), (title or f"{sig.get('sym', '')} {sig.get('tf', '')} {sig.get('b_date', '')}")[:120], fill=(0, 0, 0))
    im.save(path)
    return path


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ⑦ المجتمعُ والبيانات
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def build_population(root: str = ".") -> dict:
    """أسهمُ البوت التاريخيّة (العقد §②) = كلُّ رمزٍ **أظهره البوت للمالك** في ملفّات حالته: القائمةُ الأسبوعيّة (الحاليّة · المشطوبة ·
    الارتداد · أرشيفُ الأسابيع) ∪ سجلُّ التنبيهات ∪ متابعةُ الصيّادين وسجلُّ حصادهم **بلا `control` (عيّنةٌ عشوائيّة) ولا `envelope`
    (صامتٌ بقرار)** ∪ «تحت المتابعة» ∪ مراقَبو «هنا الدخول» ∪ سجلُّ رادار الانطلاق ∪ رادارُ الضغط ∪ قائمةُ البري **المُرسَلة وحدَها**
    ⟵ {الرموز · مصادرُ كلّ رمز · عدُّ كلّ مصدر}."""
    src = {}

    def add(s, k):
        s = str(s or "").upper().strip()
        if s:
            src.setdefault(s, set()).add(k)

    def jload(name):
        try:
            with open(os.path.join(root, name), encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:                                                  # noqa: BLE001
            return None

    def jlines(name):
        try:
            with open(os.path.join(root, name), encoding="utf-8") as fh:
                for line in fh:
                    try:
                        yield json.loads(line)
                    except Exception:                                      # noqa: BLE001
                        continue
        except Exception:                                                  # noqa: BLE001
            return
    wl = jload("weekly_watchlist.json") or {}
    for key in ("stocks", "removed", "pullback"):
        for e in wl.get(key) or []:
            add(e.get("symbol"), "watchlist_" + key)
    for w in wl.get("history") or []:
        for e in (w.get("stocks") if isinstance(w, dict) else None) or []:
            add(e.get("symbol"), "watchlist_history")
    for e in ((jload("alerts_history.json") or {}).get("alerts") or []):
        add(e.get("symbol"), "alerts_history")
    for e in ((jload("hunter_watchlist.json") or {}).get("stocks") or []):
        add(e.get("symbol"), "hunter_watchlist")
    for r in jlines("hunter_ledger.jsonl"):
        if r.get("hunter") not in EXCLUDED_HUNTERS:
            add(r.get("symbol"), "hunter_" + str(r.get("hunter")))
    for k in (jload("near_watch.json") or {}):
        add(k, "near_watch")
    for k in (jload("op_entry_state.json") or {}):
        add(str(k).split(":")[-1], "op_entry")
    for e in (jload("ignition_log.json") or []):
        if isinstance(e, dict):
            add(e.get("symbol"), "ignition")
    for r in jlines("press_radar_ledger.jsonl"):
        add(r.get("symbol"), "press_radar")
    for r in jlines("presession_ledger.jsonl"):
        if r.get("sent"):
            add(r.get("sym") or r.get("symbol"), "presession_sent")
    syms = sorted(s for s in src if s.replace(".", "").replace("-", "").isalnum())
    counts = {}
    for s in syms:
        for k in src[s]:
            counts[k] = counts.get(k, 0) + 1
    return {"symbols": syms, "sources": {s: sorted(src[s]) for s in syms}, "source_counts": dict(sorted(counts.items()))}


def git_history_symbols(root: str = ".", files=("weekly_watchlist.json", "alerts_history.json")) -> dict:
    """كلُّ رمزٍ ظهر في **أيّ نسخةٍ** من ملفّات الحالة في تاريخ git (الأرشيفُ داخل الملفّ مقصوصٌ على 26 أسبوعًا · وأوّلُ الأيّام قبله) ⟵
    {رمز: {مصادر}}. يُبنى به **المجتمعُ المجمَّد مرّةً** (`hs_population.json`) — والمسحُ اليوميّ يقرأ المجمَّدَ ‏+ الحاليّ بلا git."""
    import subprocess
    out = {}
    for name in files:
        try:
            revs = subprocess.run(["git", "-C", root, "log", "--format=%H", "--", name], capture_output=True, text=True,
                                  timeout=120).stdout.split()
        except Exception:                                                  # noqa: BLE001
            continue
        if not revs:
            continue
        try:
            pr = subprocess.run(["git", "-C", root, "cat-file", "--batch"],
                                input="".join(f"{r}:{name}\n" for r in revs).encode(), capture_output=True, timeout=900)
        except Exception:                                                  # noqa: BLE001
            continue
        buf, pos = pr.stdout, 0                          # بايتات: الحجمُ في ترويسة git بالبايت لا بالمحرف
        while pos < len(buf):
            nl = buf.find(b"\n", pos)
            if nl < 0:
                break
            head = buf[pos:nl].split()
            if len(head) < 3 or head[1] == b"missing":
                pos = nl + 1
                continue
            size = int(head[2])
            body = buf[nl + 1:nl + 1 + size]
            pos = nl + 1 + size + 1
            try:
                js = json.loads(body.decode("utf-8"))
            except Exception:                                              # noqa: BLE001
                continue
            if name == "weekly_watchlist.json":
                for key in ("stocks", "removed", "pullback"):
                    for e in js.get(key) or []:
                        if isinstance(e, dict) and e.get("symbol"):
                            out.setdefault(str(e["symbol"]).upper(), set()).add("git_watchlist")
            else:
                for e in (js.get("alerts") or []) if isinstance(js, dict) else []:
                    if isinstance(e, dict) and e.get("symbol"):
                        out.setdefault(str(e["symbol"]).upper(), set()).add("git_alerts")
    return out


def freeze_population(root: str = ".") -> dict:
    """المجتمعُ المجمَّد للعقد (`hs_population.json`): الحاليُّ (`build_population`) ∪ كلُّ نسخ القائمة وسجلِّ التنبيهات في git."""
    import subprocess
    cur = build_population(root)
    src = {s: set(v) for s, v in cur["sources"].items()}
    for s, v in git_history_symbols(root).items():
        if s.replace(".", "").replace("-", "").isalnum():
            src.setdefault(s, set()).update(v)
    syms = sorted(src)
    counts = {}
    for s in syms:
        for k in src[s]:
            counts[k] = counts.get(k, 0) + 1
    head = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    return {"frozen_at": dt.date.today().isoformat(), "git_head": head, "n": len(syms),
            "source_counts": dict(sorted(counts.items())), "symbols": syms, "sources": {s: sorted(src[s]) for s in syms}}


def load_population(root: str = ".") -> list:
    with open(os.path.join(root, POP_FILE), encoding="utf-8") as fh:
        return list(json.load(fh)["symbols"])


def scan_population(root: str = ".") -> list:
    """مجتمعُ المسح الحيّ = المجمَّد ∪ الحاليّ (فسهمٌ دخل البوتَ بعد التجميد يُمسَح أيضًا)."""
    try:
        frozen = set(load_population(root))
    except Exception:                                                      # noqa: BLE001
        frozen = set()
    return sorted(frozen | set(build_population(root)["symbols"]))


def _split_dates(sym, fetch=None):
    """تواريخُ التقسيم (أيّ نسبة) من ياهو ⟵ قائمةُ تواريخ · None عند التعذّر (**مجهولٌ لا «لا تقسيم»**)."""
    try:
        if fetch is None:
            import Super_stock as S
            fetch = S._fetch_splits
        sp = fetch(sym)
    except Exception:                                                      # noqa: BLE001
        return None
    if sp is None:
        return None
    try:
        keys = sp.index if hasattr(sp, "index") else [x[0] for x in sp]
        return sorted({str(d)[:10] for d in keys})
    except Exception:                                                      # noqa: BLE001
        return None


def split_in_window(dates, d0: str, d1: str) -> bool:
    return any(d0 <= d <= d1 for d in (dates or []))


def _plus_days(d: str, k: int) -> str:
    return (dt.date.fromisoformat(d[:10]) + dt.timedelta(days=k)).isoformat()


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ⑧ التحليل التاريخيّ (DEV 2022 · الحكم 2023-2025 · 2026 وصفيّ) — كلُّه من `detect` السببيّة ثمّ `outcomes` بعدها
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
ROW_FIELDS = ("pid", "sym", "tf", "p0_date", "ls_date", "head_date", "rs_date", "b_date", "entry", "p0_px", "ls_px", "head_px",
              "rs_px", "p1_px", "p2_px", "neck_b", "neck_type", "height", "target", "target_p0", "quality", "vol_ratio",
              "fsto_k", "fsto_d", "cci", "compound", "span", "width", "b_i", "ls_i", "head_i", "rs_i", "p0_i", "p1_i", "p2_i",
              "neck_slope")


def analyze_symbol(sym: str, df, splits) -> dict:
    """رمزٌ واحد ⟵ إشاراتُ STRICT وLOOSE بنتائجها ‏+ مرشّحو الضبط بنتائجهم · وكلُّ صفٍّ يحمل وسمَ نافذة التقسيم."""
    out = {"sym": sym, "sigs": [], "ctrl": []}
    all_b = set()
    for cfg, p in CONFIGS.items():
        for s in detect(df, p, sym=sym, tf="1d"):
            all_b.add(s["b_i"])
            rt = retest_state(df, s, p)
            row = {k: s.get(k) for k in ROW_FIELDS}
            row["cfg"] = cfg
            row["year"] = int(s["b_date"][:4])
            row["retest"] = rt["retest"]
            row["oc"] = outcomes(df, s, p)
            if rt["retest"] == "success" and rt["cont_i"] is not None:
                row["oc_full"] = outcomes(df, s, p, entry_i=rt["cont_i"])
                row["full_date"] = str(df.index[rt["cont_i"]])[:10]
            row["split_win"] = (None if splits is None else
                                split_in_window(splits, s["ls_date"], _plus_days(s["b_date"], SPLIT_PAD_DAYS)))
            row["ret20_prior"] = (float(df["Close"].iloc[s["b_i"]] / df["Close"].iloc[s["b_i"] - 20] - 1)
                                  if s["b_i"] >= 20 else None)
            out["sigs"].append(row)
    for e in control_events(df, sig_bars=all_b):
        rt = retest_state(df, e, STRICT)
        r = {"sym": sym, "b_date": e["b_date"], "year": int(e["b_date"][:4]), "wb": e["wb"], "entry": e["entry"],
             "ret20_prior": e["ret20_prior"], "retest": rt["retest"], "oc": outcomes(df, e, STRICT)}
        if rt["retest"] == "success" and rt["cont_i"] is not None:
            r["oc_full"] = outcomes(df, e, STRICT, entry_i=rt["cont_i"])
        d0 = str(df.index[max(0, e["b_i"] - e["wb"])])[:10]
        r["split_win"] = None if splits is None else split_in_window(splits, d0, _plus_days(e["b_date"], SPLIT_PAD_DAYS))
        out["ctrl"].append(r)
    return out


ARMS = {
    "STRICT": lambda r: r["cfg"] == "STRICT",
    "LOOSE": lambda r: r["cfg"] == "LOOSE",
    "VOL": lambda r: r["cfg"] == "STRICT" and (r.get("vol_ratio") or 0) >= VOL_MULT,
    "FSTO": lambda r: r["cfg"] == "STRICT" and r.get("fsto_k") is not None and r.get("fsto_d") is not None
                      and r["fsto_k"] > r["fsto_d"],
    "CCI": lambda r: r["cfg"] == "STRICT" and r.get("cci") is not None and r["cci"] > CCI_MIN,
    "FSTO_CCI": lambda r: ARMS["FSTO"](r) and ARMS["CCI"](r),
    "Q": lambda r: r["cfg"] == "STRICT" and (r.get("quality") or 0) >= Q_MIN,
    "FULL": lambda r: r["cfg"] == "STRICT" and r.get("oc_full") is not None,
}


def _usable(r) -> bool:
    """الصفُّ الأوّليّ: بلا تقسيمٍ في نافذته **ومعلومُ التقسيمات** (المجهولُ يُستبعَد ويُعَدّ · فاشلٌ-مغلق)."""
    return r.get("split_win") is False


def _row_year(r, full: bool) -> int:
    """سنةُ الصفّ: سنةُ الاختراق · وللتطابق الكامل سنةُ الاستمرار (لحظةُ معرفته)."""
    return int(((r.get("full_date") if full else None) or r["b_date"])[:4])


def counts_by_year(rows) -> dict:
    """أعدادٌ بلا نتائج (وضعُ التطوير أعمى عن العوائد — العقد §⑤): كلُّ إعدادٍ × سنة ⟵ {الكلّ · الصالح · تقسيمٌ في النافذة · مجهول}."""
    out = {}
    for r in rows:
        y = str(r["year"])
        d = out.setdefault(r["cfg"], {}).setdefault(y, {"all": 0, "usable": 0, "split": 0, "unknown": 0})
        d["all"] += 1
        d["usable" if r.get("split_win") is False else "split" if r.get("split_win") else "unknown"] += 1
    return out


def year_stats(rows, ctrl, arm: str, year: int) -> dict:
    """إحصاءُ ذراعٍ في سنة: التوزيعاتُ لكلّ أفق ‏+ أعلى ارتفاع وأكبر هبوط ‏+ الهدف والفشل وإعادةُ الاختبار ‏+ مقارنةُ الضبط المطابَق."""
    full = arm == "FULL"
    key = "oc_full" if full else "oc"
    S_ = [r for r in rows if ARMS[arm](r) and _usable(r) and _row_year(r, full) == year]
    pool = [c for c in ctrl if _usable(c) and c["year"] == year and (c.get("oc_full") is not None if full else True)]
    out = {"n": len(S_)}
    if not S_:
        return out
    oc = [r[key] for r in S_]
    for hz in HORIZONS:
        out[f"ret{hz}"] = dist([o.get(f"ret{hz}") for o in oc])
    out["mfe"] = dist([o.get("mfe") for o in oc])
    out["mae"] = dist([o.get("mae") for o in oc])
    comp = [o for o in oc if o.get("complete")]
    k = sum(1 for o in comp if o.get("target_hit"))
    out["target_hit"] = {"k": k, "n": len(comp), "rate": (k / len(comp) if comp else None), "wilson": wilson(k, len(comp)),
                         "bars": dist([o.get("target_bars") for o in comp if o.get("target_hit")])}
    p0c = [o for o in comp if o.get("p0_hit") is not None]
    k0 = sum(1 for o in p0c if o.get("p0_hit"))
    out["p0_hit"] = {"k": k0, "n": len(p0c), "rate": (k0 / len(p0c) if p0c else None)}
    out["invalid"] = {"k": sum(1 for o in comp if o.get("invalid_bars")), "n": len(comp)}
    rts = [r["retest"] for r in S_]
    out["retest"] = {x: rts.count(x) for x in sorted(set(rts))}
    fl = sum(1 for x in rts if x in ("failed_breakout", "failed_retest"))
    dec = sum(1 for x in rts if x != "pending")
    out["failure"] = {"k": fl, "n": dec, "rate": (fl / dec if dec else None)}
    ys = [c["ret20_prior"] for c in pool if c.get("ret20_prior") is not None]
    if len(ys) >= 3:
        cuts = (float(np.percentile(ys, 100 / 3.0)), float(np.percentile(ys, 200 / 3.0)))
        strata = {}
        for c_ in pool:
            if c_.get("ret20_prior") is None:
                continue
            strata.setdefault((c_["wb"], momentum_tercile(c_["ret20_prior"], cuts)), []).append(c_)
        sv, cl, mf, mfc = [], [], [], []
        for r in S_:
            if r.get("ret20_prior") is None:
                continue
            pool_s = strata.get((w_bucket(r["width"]), momentum_tercile(r["ret20_prior"], cuts)), [])
            pick = sample_controls(r["pid"] + "|" + arm, pool_s)
            v10 = r[key].get("ret10")
            cv = [p_[key].get("ret10") for p_ in pick if p_[key].get("ret10") is not None]
            if v10 is None or not cv:
                continue
            sv.append(v10)
            cl.append(cv)
            mf.append(r[key].get("mfe"))
            mfc += [p_[key].get("mfe") for p_ in pick if p_[key].get("mfe") is not None]
        diff, lo, hi = boot_median_diff(sv, cl)
        out["control"] = {"n_sig_matched": len(sv), "n_ctrl": sum(len(x) for x in cl),
                          "median_sig": (float(np.median(sv)) if sv else None),
                          "median_ctrl": (float(np.median([x for c__ in cl for x in c__])) if cl else None),
                          "diff": diff, "ci_lo": lo, "ci_hi": hi,
                          "mfe_sig": dist(mf).get("median"), "mfe_ctrl": dist(mfc).get("median")}
        out["ci_lo"] = lo
    return out


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ⑨ التقييمُ الاصطناعيّ (حقيقةٌ أرضيّةٌ معلومة ⟵ الاسترجاعُ والإنذارُ الكاذب) — حتميٌّ بالبذور
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
SYN_IHS = [(0, 1.20), (5, 1.30), (45, 0.80), (55, 0.92), (67, 0.70), (79, 0.92), (89, 0.80), (97, 0.97), (125, 1.20),
           (140, 1.16)]
SYN_IHS_COMPOUND = [(0, 1.20), (5, 1.30), (45, 0.80), (55, 0.92), (63, 0.70), (68, 0.80), (73, 0.71), (83, 0.92),
                    (93, 0.80), (101, 0.97), (130, 1.20), (145, 1.16)]
SYN_IHS_COMPOUND_B = [(0, 1.20), (5, 1.30), (45, 0.80), (55, 0.92), (63, 0.71), (68, 0.80), (73, 0.70), (83, 0.92),
                      (93, 0.80), (101, 0.97), (130, 1.20), (145, 1.16)]
SYN_TOP = [(0, 0.80), (5, 0.70), (45, 1.20), (55, 1.08), (67, 1.30), (79, 1.08), (89, 1.20), (97, 1.03), (125, 0.80),
           (140, 0.84)]
SYN_DB = [(0, 1.20), (5, 1.30), (45, 0.75), (57, 0.90), (69, 0.75), (85, 1.00), (110, 1.15), (125, 1.12)]
SYN_V = [(0, 1.20), (5, 1.30), (60, 0.70), (115, 1.25), (130, 1.22)]


def synth_bars(points, seed: int = 0, noise: float = 0.004, base: float = 10.0, start: str = "2022-01-03"):
    """مسارٌ بنقاطٍ [(بار, سعرٌ نسبيّ)] ‏+ ضجيجٌ حتميّ ⟵ إطارُ OHLCV بشكل ياهو (للأقفال وللتقييم الاصطناعيّ)."""
    rng = np.random.default_rng(seed)
    xs = np.arange(int(points[-1][0]) + 1)
    path = np.interp(xs, [q[0] for q in points], [q[1] for q in points]) * base
    c = path * (1 + rng.normal(0, noise, len(xs)))
    o = np.r_[c[0], c[:-1]]
    hi = np.maximum(o, c) * (1 + np.abs(rng.normal(0, noise, len(xs))))
    lo = np.minimum(o, c) * (1 - np.abs(rng.normal(0, noise, len(xs))))
    v = 1e6 * (1 + rng.random(len(xs)))
    idx = pd.bdate_range(start, periods=len(xs))
    return pd.DataFrame({"Open": o, "High": hi, "Low": lo, "Close": c, "Volume": v}, index=idx)


def synth_walk(n: int, seed: int, sigma: float = 0.02, base: float = 10.0):
    """سيرٌ عشوائيٌّ هندسيّ بلا بنية (للإنذار الكاذب)."""
    rng = np.random.default_rng(seed)
    c = base * np.exp(np.cumsum(rng.normal(0, sigma, n)))
    o = np.r_[c[0], c[:-1]]
    hi = np.maximum(o, c) * (1 + np.abs(rng.normal(0, sigma / 3, n)))
    lo = np.minimum(o, c) * (1 - np.abs(rng.normal(0, sigma / 3, n)))
    idx = pd.bdate_range("2022-01-03", periods=n)
    return pd.DataFrame({"Open": o, "High": hi, "Low": lo, "Close": c, "Volume": 1e6 * (1 + rng.random(n))}, index=idx)


def synthetic_eval(seeds: int = 50) -> dict:
    """الاسترجاعُ على نماذجَ مزروعة (بسيط · مركّب) والإنذارُ الكاذب على ما ليس نموذجًا (قمّة · قاعٌ مزدوج · V · سيرٌ عشوائيّ) —
    **اصطناعيّ** (حقيقةٌ أرضيّة معلومة) لا يُقرأ دقّةً في السوق."""
    res = {}
    for cfg, p in CONFIGS.items():
        r = {}
        for name, pts, hb in (("ihs", SYN_IHS, 67), ("ihs_compound", SYN_IHS_COMPOUND, 63),
                              ("ihs_compound_b", SYN_IHS_COMPOUND_B, 73)):
            r[name] = sum(1 for s in range(seeds) if any(abs(x["head_i"] - hb) <= 5
                                                          for x in detect(synth_bars(pts, seed=s), p))) / float(seeds)
        for name, pts in (("top", SYN_TOP), ("double_bottom", SYN_DB), ("v_shape", SYN_V)):
            r[name] = sum(1 for s in range(seeds) if detect(synth_bars(pts, seed=s), p)) / float(seeds)
        bars = 0
        hits = 0
        for s in range(seeds):
            w = synth_walk(500, seed=10_000 + s)
            hits += len(detect(w, p))
            bars += len(w)
        r["walk_per_1000_bars"] = 1000.0 * hits / bars
        res[cfg] = r
    return res


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ⑩ الرسائل — **بنموذج المالك** (‏§41 من أمره) · أرقامٌ محسوبةٌ فقط · بلا علامات مقارنة في العربيّ
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
STATUS_EN = {s: s.replace("_", " ") for s in LIFECYCLE}
STATUS_AR = {
    "FORMING": "يتكوّن (الكتف الأيمن لم يتأكّد)", "COMPLETED": "اكتمل وينتظر الاختراق",
    "BREAKOUT_PENDING": "لمس خطّ العنق بلا إغلاقٍ مؤكِّد", "BREAKOUT_CONFIRMED": "اختراقٌ مؤكَّد بالإغلاق",
    "RETEST_PENDING": "اخترق وينتظر إعادة الاختبار", "RETEST_CONFIRMED": "اخترق ثمّ عاد لخطّ العنق وواصل",
    "NO_RETEST": "اخترق وواصل بلا عودة", "RETEST_NO_FOLLOW": "عاد لخطّ العنق وثبت ولم يواصل",
    "STALLED": "اخترق وحام فوق خطّ العنق بلا ابتعادٍ ولا استمرار",
    "TARGET_REACHED": "بلغ الهدف النظريّ", "FAILED": "فشل (رجع تحت خطّ العنق أو تحت الرأس)",
    "EXPIRED": "انتهت صلاحيتُه بلا اختراق", "NONE": "لا نموذج", "NO_DATA": "لا بيانات كافية",
}
RETEST_EN = {"success": "SUCCESSFUL", "failed_retest": "FAILED", "failed_breakout": "FAILED (breakout failed first)",
             "none": "NO RETEST", "touch_no_follow": "HELD — NO CONTINUATION", "stalled": "NONE — STALLED",
             "pending": "PENDING"}
TF_EN = {"1d": "1D", "5m": "5M"}


def _px(x) -> str:
    if x is None:
        return "—"
    return f"${x:,.4f}" if abs(x) < 1 else f"${x:,.2f}"


def _pct(x, signed: bool = True) -> str:
    if x is None:
        return "—"
    return (f"{x * 100:+.1f}%" if signed else f"{x * 100:.1f}%")


def history_block(hist: dict) -> list:
    """أسطرُ التاريخ من حكم العقد المجمَّد (`hs_verdict.json` · STRICT · 2023-2025 · الصالحُ وحدَه) — **وغيابُه ⟵ «—» لا رقمٌ مخترَع**."""
    pz = (hist or {}).get("pooled") or {}
    # مصدرُ الأرقام يُسمّى في السطر نفسِه: الحكمُ يوميٌّ 2023-2025 — وفي رسالة 5 دقائق كانت تُقرأ أرقامَ فريمها (عطلٌ مُثبَت
    # 2026-10-01 · فحصُ BNGO 5M `36920024094` · HS42)
    return [f"Historical Sample: {pz.get('n') if pz.get('n') is not None else '—'} (1D · 2023-2025)",
            f"Median +5D: {_pct(pz.get('ret5'))}",
            f"Median Max Run-Up: {_pct(pz.get('mfe'))}",
            f"Median Max Drawdown: {_pct(pz.get('mae'))}",
            f"Target Hit Rate: {_pct(pz.get('target_rate'), False)}"]


def build_alert(sym: str, lc: dict, tf: str = "1d", hist=None, dq_line: str = None) -> str:
    """رسالةُ «🔎 نموذج الرأس والكتفين» لسهمٍ واحد بنموذج المالك (الحقولُ بترتيبه) — وكلُّ رقمٍ محسوبٌ أو «—»."""
    import Super_stock as S
    st = lc.get("state") or "NONE"
    s = lc.get("sig")
    fm = lc.get("forming")
    rt = (lc.get("retest") or {}).get("retest")
    L = [f"🔎 <b>{TOOL_NAME}</b>", "", f"Ticker: ${S.esc(sym)}", f"Timeframe: {TF_EN.get(tf, tf)}",
         f"Status: {STATUS_EN.get(st, st)} — {STATUS_AR.get(st, '')}"]
    if dq_line:
        L.append(S.esc(dq_line))
    if s:
        full = rt == "success"
        L += ["", f"Left Shoulder: {_px(s['ls_px'])}", f"Head: {_px(s['head_px'])}", f"Right Shoulder: {_px(s['rs_px'])}",
              f"Neckline: {_px(s['neck_b'])}", f"Breakout: {_px(s['entry'])} ({s['b_date']})",
              f"Retest: {RETEST_EN.get(rt, 'PENDING')}", f"Target: {_px(s['target'])}",
              "", f"Pattern Quality: {s['quality']}/100", f"Match Type: {'FULL STRATEGY' if full else 'STRUCTURAL'}"]
    elif fm:
        L += ["", f"Left Shoulder: {_px(fm['ls_px'])}", f"Head: {_px(fm['head_px'])}", f"Right Shoulder: {_px(fm['rs_px'])}",
              f"Neckline: {_px(fm['neck_now'])}", "Breakout: —", "Retest: —", f"Target: {_px(fm['target'])}"]
    hb = history_block(hist)
    L += [""] + hb
    L += ["", verdict_line(hist),
          "⚠️ قراءةٌ آليّة لشكلٍ كلاسيكيّ تبنّاه فيصل — أمثلتُه الحقيقيّة للنموذج قمّةٌ يُخرَج عندها لا دخول. ليست توصية."]
    return "\n".join(L)


def verdict_line(hist) -> str:
    """سطرُ الحكم المسجَّل للرسالة والاستعلام معًا: اسمُ الفرع **واتّجاهُ الفرق** عن الضبط لكلّ سنة حكم (‏`telegram.ctrl_diff`) — وغيابُه ⟵
    لا رقمَ مخترَع · وبلا حكمٍ ⟵ «لم يُقَس بعد»."""
    br = (hist or {}).get("branch_text")
    cd = " · ".join(f"{y} {_pct(v)}" for y, v in sorted(((hist or {}).get("ctrl_diff") or {}).items()) if v is not None)
    return ("⚖️ الحكم المسجَّل على أسهم البوت: " + (f"«{br}» (مقابل اختراقاتٍ عاديّةٍ مطابِقة)" if br else "لم يُقَس بعد")
            + (f" · فرقُ وسيط +10 جلسات عن الضبط: {cd}" if br and cd else ""))


def load_hist(root: str = ".") -> dict:
    try:
        with open(os.path.join(root, RES_DIR, "hs_verdict.json"), encoding="utf-8") as fh:
            return (json.load(fh).get("telegram") or {})
    except Exception:                                                      # noqa: BLE001
        return {}


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ⑪ التشغيل (Actions) — dev · verdict · ticker · query · scan
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def log(*a):
    print(*a, flush=True)


def _completed(df, now=None):
    """«الاختراقُ أوّلُ إغلاقٍ» (§③) ⟵ **شمعةُ جلسةٍ لم تُغلَق ليست إغلاقًا**: TradingView يُعيد الجلسةَ الجارية بسعرها اللحظيّ ⟵ تُقصّ كلُّ
    شمعةٍ بعد آخر جلسةٍ نظاميّةٍ مكتملة (`S.last_closed_session` · ساعةُ نيويورك والتقويم وهامشُه) — يوميًّا ودقائقَ (التاريخُ من الفهرس) ·
    وتعذّرُ التقويم أو الإطار ⟵ كما هو (السلوكُ السابق · فاشلٌ-آمن). عطلٌ مُثبَت: تشغيلةُ الحكم الأولى `36911113194` (‏19:04 UTC داخل
    الجلسة) قرأت شمعةَ 2026-10-01 الجارية."""
    import Super_stock as S
    try:
        if df is None or not len(df):
            return df
        exp = S.last_closed_session(now)
        if not exp:
            return df
        return df[pd.DatetimeIndex(df.index).normalize() <= pd.Timestamp(exp)]
    except Exception:                                                      # noqa: BLE001
        return df


def _completed_all(frames: dict, rep: dict = None, now=None) -> dict:
    """`_completed` لكلّ إطار ⟵ والمقصوصُ يُعَدّ في التقرير (`partial_trimmed`) ويُعلَن ولا يُصمت · والفارغُ بعد القصّ يغيب."""
    out, cut = {}, 0
    for s, df in (frames or {}).items():
        d = _completed(df, now)
        if d is not None and df is not None and len(d) < len(df):
            cut += 1
        if d is not None and len(d):
            out[s] = d
    if rep is not None:
        rep["partial_trimmed"] = cut
    return out


def _fetch_daily(syms, start: str = DATA_START):
    """شموعٌ يوميّة من TradingView (مسوّاةٌ بالتقسيم · الجلسةُ النظاميّة) **وحدَه** للتحليل التاريخيّ (لا خلطَ مصادر) ⟵ ({رمز: إطار}, تقرير) ·
    **جلساتٌ مكتملةٌ وحدَها** (`_completed`)."""
    import Super_stock as S
    data, rep = S.tv_download(list(syms), start)
    return _completed_all(data, rep), rep


def _fetch_live(syms, days: int = SCAN_DAYS):
    """شموعٌ يوميّة حيّة من TradingView **مباشرةً** (`S.tv_download` — لا `BARS_SOURCE`: مفتاحُه محصورٌ بعشرة workflows · TVB9) ·
    **جلساتٌ مكتملةٌ وحدَها** (`_completed`: المسحُ والفحصُ اليوميّ لا يقرآن «اختراقًا» على شمعةٍ جارية)."""
    import Super_stock as S
    data, rep = S.tv_download(list(syms), (dt.date.today() - dt.timedelta(days=days)).isoformat())
    return _completed_all(data, rep), rep


def _fetch_intraday(syms, n: int = 5000, extended: bool = False, completed_only: bool = False):
    """شموعُ 5 دقائق من TradingView ⟵ {رمز: إطارٌ بفهرس توقيت نيويورك} · وما تعذّر يغيب · و`completed_only` (البحثُ الوصفيّ) يقصّ
    الجلسةَ الجارية (`_completed`) — وفحصُ السهم 5 دقائق يقرؤها كما هي (قراءةٌ متأخّرة ‏≈15 دقيقة معلنة)."""
    import Super_stock as S
    import tv_data as TV
    tmap = S._tv_ticker_map()
    full = {s: S._tv_full_name(s, tmap) for s in syms}
    got = TV.fetch_many(sorted(set(full.values())), interval="5", n=n, extended=extended, workers=8, retry_pass=True) or {}
    out = {}
    for s in syms:
        b = got.get(full[s])
        if not b:
            continue
        rows = [(TV.ny_time(x[0]).replace(tzinfo=None), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5]))
                for x in b]
        df = pd.DataFrame(rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"]).set_index("Date").sort_index()
        out[s] = df[~df.index.duplicated(keep="last")]
    return _completed_all(out) if completed_only else out


def _session_codes(df) -> np.ndarray:
    return np.asarray([d.toordinal() for d in pd.DatetimeIndex(df.index).date], dtype=int)


def _splits_many(syms, workers: int = 8, fetch=None) -> dict:
    """{رمز: تواريخُ التقسيم أو None} بالتوازي (نداءُ ياهو لكلّ رمز · `_fetch_splits` مخبّأٌ في التشغيلة)."""
    from concurrent.futures import ThreadPoolExecutor
    syms = list(syms)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        vals = list(ex.map(lambda s: _split_dates(s, fetch), syms))
    return dict(zip(syms, vals))


RULE_ORDER = ("pre", "close", "rs_seg", "head_lowest", "head_min", "head_depth", "height_atr", "height_pct", "shoulder_tol",
              "shoulder_depth", "neck_slope", "time_sym", "span", "prior_drop", "prior_bars", "expired", "mids", "session",
              "not_first")                     # ترتيبُ قواعد `_evaluate` نفسُه — «أبعدُ ما بلغته بنيةٌ» يُقرأ عليه


def explain_miss(df, p, polarity: str, session, day_ord: int, top_i: int, win: int = 3) -> dict:
    """لماذا لم يُكتشَف النموذجُ في جلسةٍ بعينها؟ **تشخيصٌ وصفيٌّ لا ضبط** (لا يُغيّر قاعدةً لأجل مثال): يمشي البارات بالترتيب
    السببيّ نفسِه في `detect` ويسأل `_evaluate` كلَّ بنيةٍ رأسُها خلال ±`win` بارات من `top_i` في كلّ بارٍ من الجلسة: أيُّ قاعدةٍ
    رفضتها أوّلًا؟ ⟵ عدُّ الأسباب ‏+ أبعدُ بنيةٍ في ترتيب القواعد (`RULE_ORDER`) بنقاطها الحقيقيّة ‏+ هل كان رأسُ الجلسة محورًا أصلًا."""
    p = dict(STRICT if p is None else p)
    sgn = -1.0 if polarity == "top" else 1.0
    o, h, l, c, v = _arrays(df, polarity)
    a = atr_np(h, l, c, p["atr_n"])
    idx = np.nonzero(np.asarray(session) == day_ord)[0]
    out = {"structures_near_top": 0, "reasons": {}, "head_pivot": False, "closest": None}
    if not len(idx):
        return out
    Z, seen, best = [], set(), None
    for t, cand, Z in _walk(h, l, a, p, int(idx[-1]) + 1):
        if session[t] != day_ord:
            continue
        for st in cand:
            if abs(st["head"][0] - top_i) > win:
                continue
            seen.add((st["ls"][0], st["p1"][0], st["head"][0], st["p2"][0]))
            why = []
            sig = _evaluate(st, t, h, l, c, a, p, session=session, why=why)
            r = "detected" if sig is not None else (why[0] if why else "?")
            out["reasons"][r] = out["reasons"].get(r, 0) + 1
            rank = len(RULE_ORDER) if sig is not None else (RULE_ORDER.index(r) if r in RULE_ORDER else -1)
            if best is None or rank > best[0]:
                best = (rank, r, t, st)
    out["structures_near_top"] = len(seen)
    out["head_pivot"] = any(z[1] == "L" and abs(z[0] - top_i) <= win for z in Z)
    if best is not None:
        _, r, t, st = best
        di = pd.DatetimeIndex(df.index)
        out["closest"] = {"rule": r, "at": str(di[t])[:16],
                          **{f"{k}_px": round(sgn * float(st[k][2]), 4) for k in ("p0", "ls", "p1", "head", "p2")},
                          **{f"{k}_at": str(di[st[k][0]])[:16] for k in ("ls", "head", "p2")}}
    return out


def structural_check(sym: str, day: str, shoulder_px: float, head_px: float, tol: float = 0.10) -> dict:
    """التحقّقُ البنيويّ (العقد §⑦): هل يرى المكتشفُ — بمرآته للقمّة — القمّةَ التي رسمها فيصل في جلسة `day`؟ ⟵ قراءةٌ لا حكم.
    وإن لم يجده: `why_not` لكلٍّ من STRICT وLOOSE (`explain_miss` — أيُّ قاعدةٍ رفضت · تشخيصٌ لا ضبط)."""
    data = _fetch_intraday([sym], extended=True)
    df = data.get(sym)
    if df is None or not len(df):
        return {"sym": sym, "day": day, "status": "لا قياس", "why": "لا شموعَ 5 دقائق من TradingView"}
    days = sorted(set(str(d) for d in pd.DatetimeIndex(df.index).date))
    if day not in days:
        return {"sym": sym, "day": day, "status": "لا قياس", "why": f"الجلسة خارج ما تبلغه الدقائق (أقدمُها {days[0]})"}
    ses = _session_codes(df)
    dord = dt.date.fromisoformat(day).toordinal()
    first_i = int(np.nonzero(ses == dord)[0][0])
    top_i = first_i + int(np.argmax(df["High"].to_numpy()[ses == dord]))
    res = {"sym": sym, "day": day, "session_high": float(df["High"].to_numpy()[ses == dord].max()), "faisal_head": head_px,
           "faisal_shoulder": shoulder_px, "bars_in_session": int((ses == dord).sum())}
    for name, p in (("STRICT", STRICT), ("LOOSE", LOOSE)):
        sigs = detect(df, p, polarity="top", sym=sym, tf="5m", session=ses)
        sday = [s for s in sigs if s["b_date"][:10] == day]
        hit = [s for s in sday if abs(s["head_i"] - top_i) <= 3
               and abs(s["ls_px"] / shoulder_px - 1) <= tol and abs(s["rs_px"] / shoulder_px - 1) <= tol]
        key = "" if name == "STRICT" else "_loose"
        res["status" + key] = "وجده" if hit else "لم يجده"
        res["n_top_signals_day" + key] = len(sday)
        res["signals" + key] = [{k: s[k] for k in ("ls_date", "head_date", "rs_date", "b_date", "ls_px", "head_px", "rs_px",
                                                     "neck_b", "quality")} for s in sday]
        if not hit:
            res["why_not" + key] = explain_miss(df, p, "top", ses, dord, top_i)
    return res


def _audit_pack(rows, data, year: int, seed: int = AUDIT_SEED, n: int = AUDIT_N) -> list:
    """عيّنةُ التدقيق البصريّ (العقد §⑤): عشوائيّةٌ حتميّة من إشارات STRICT الصالحة في `year` ‏+ شموعُها (حتى ‏+30 بعد الاختراق —
    والرسمُ الأعمى يقصّ عند الاختراق)."""
    pool = [r for r in rows if r["cfg"] == "STRICT" and r["year"] == year and _usable(r)]
    if not pool:
        return []
    rng = np.random.default_rng(seed)
    pick = [pool[i] for i in sorted(rng.choice(len(pool), size=min(n, len(pool)), replace=False))]
    out = []
    for r in pick:
        df = data[r["sym"]]
        b = r["b_i"]
        i0, i1 = max(0, min(r["p0_i"], r["ls_i"]) - 25), min(len(df), b + 31)
        seg = df.iloc[i0:i1]
        out.append({"pid": r["pid"], "sym": r["sym"], "b_date": r["b_date"], "offset": i0,
                    "sig": {k: r.get(k) for k in ROW_FIELDS},
                    "bars": [[str(ix)[:10], float(o), float(h), float(l), float(c)] for ix, (o, h, l, c)
                             in zip(seg.index, seg[["Open", "High", "Low", "Close"]].to_numpy())]})
    return out


def _verdict_rows(stats: dict, arm: str) -> dict:
    """مدخلُ قاعدة الحكم لكلّ سنة: **n = الإشاراتُ المطابَقةُ بضبطها** (العيّنةُ التي حُسب عليها الفاصل — لا كلُّ الصالح) وحدُّ الفاصل الأدنى."""
    out = {}
    for y in VERDICT_YEARS:
        st = (stats.get(arm) or {}).get(str(y)) or {}
        out[y] = {"n": (st.get("control") or {}).get("n_sig_matched", 0), "ci_lo": st.get("ci_lo")}
    return out


def run_research(mode: str) -> int:
    """dev: **أعمى عن العوائد** (أعدادٌ ‏+ عيّنةُ التدقيق البصريّ ‏+ التحقّقُ البنيويّ ‏+ التقييمُ الاصطناعيّ) ·
    verdict: 2022-2026 كاملةً ‏+ الحكمُ بالقاعدة المسجَّلة ‏+ 5 دقائق وصفيّة. لا تلغرامَ في الوضعين (سجلٌّ وملفّاتُ `hs_research/`)."""
    import Super_stock as S
    pop = load_population()
    log(f"🔎 {TOOL_NAME} · وضع {mode} · المجتمع {len(pop)} رمزًا (`{POP_FILE}`) · STRICT {json.dumps(STRICT)} · "
        f"LOOSE {json.dumps(LOOSE)}")
    data, rep = _fetch_daily(pop)
    log(S._tv_bars_line(rep))
    log(f"📊 شموعٌ يوميّة من TradingView: {len(data)} من {len(pop)} (تعذّر {len(pop) - len(data)} · يُعلَن ولا يُستبدَل بمصدرٍ آخر)")
    log(f"🕗 جلساتٌ مكتملةٌ وحدَها: قُصّت شمعةُ جلسةٍ جارية من {rep.get('partial_trimmed', 0)} إطارًا (آخرُ جلسةٍ مكتملة "
        f"{S.last_closed_session()})")
    splits = _splits_many(sorted(data))
    sp_unknown = sum(1 for v in splits.values() if v is None)
    log(f"🧾 تقسيماتُ ياهو: معلومةٌ {len(splits) - sp_unknown} · مجهولةٌ {sp_unknown} (صفوفُها خارج الأوّليّ · فاشلٌ-مغلق)")
    rows, ctrl = [], []
    for i, sym in enumerate(sorted(data)):
        r = analyze_symbol(sym, data[sym], splits.get(sym))
        rows += r["sigs"]
        ctrl += r["ctrl"]
        if (i + 1) % 200 == 0:
            log(f"   … {i + 1}/{len(data)} · إشارات {len(rows)} · ضبط {len(ctrl)}")
    os.makedirs(RES_DIR, exist_ok=True)
    res = {"mode": mode, "generated": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", "params": CONFIGS,
           "population": len(pop), "fetched": len(data), "fetch_report": {k: (v if not isinstance(v, list) else len(v))
                                                                          for k, v in rep.items()},
           "splits_unknown_symbols": sp_unknown, "counts": counts_by_year(rows), "n_ctrl": len(ctrl),
           "fetched_symbols": sorted(data)}
    for cfg, ys in res["counts"].items():
        log(f"   {cfg}: " + " · ".join(f"{y}: {d['all']} (صالح {d['usable']} · تقسيم {d['split']} · مجهول {d['unknown']})"
                                       for y, d in sorted(ys.items())))
    res["synthetic"] = synthetic_eval()
    for cfg, r in res["synthetic"].items():
        log(f"🧪 اصطناعيّ {cfg}: استرجاعُ البسيط {_pct(r['ihs'], False)} · المركّب {_pct(r['ihs_compound'], False)}/"
            f"{_pct(r['ihs_compound_b'], False)} · "
            f"إنذارٌ كاذب: قمّة {_pct(r['top'], False)} · قاعٌ مزدوج {_pct(r['double_bottom'], False)} · "
            f"V {_pct(r['v_shape'], False)} · سيرٌ عشوائيّ {r['walk_per_1000_bars']:.2f} لكلّ 1000 شمعة")
    if mode == "dev":
        res["audit"] = _audit_pack(rows, data, DEV_YEAR)
        res["audit_seed"], res["audit_iter"] = AUDIT_SEED, AUDIT_ITER
        res["structural"] = [structural_check("DCOY", "2026-09-22", 5.332, 6.9),
                             structural_check("DRMA", "2026-03-20", 1.668, 1.828, tol=0.05)]
        for x in res["structural"]:
            wn = x.get("why_not") or {}
            log(f"🧭 التحقّق البنيويّ {x['sym']} {x['day']}: {x['status']} (LOOSE {x.get('status_loose', '—')}) · "
                f"{x.get('why', '')} {x.get('n_top_signals_day', '')} · أقربُ رفض: {(wn.get('closest') or {}).get('rule', '—')} · "
                f"بنى قرب القمّة {wn.get('structures_near_top', '—')} · رأسُ الجلسة محور: {wn.get('head_pivot', '—')}")
        log(f"🔍 عيّنةُ التدقيق البصريّ: {len(res['audit'])} إشارة STRICT من {DEV_YEAR} (بذرة {AUDIT_SEED} · التكرار {AUDIT_ITER}) "
            f"— بلا أيّ عائد (أعمى)")
        out = os.path.join(RES_DIR, "dev_2022.json")
        files = [out]
    else:
        years = [DEV_YEAR, *VERDICT_YEARS, DESC_YEAR]
        res["stats"] = {}
        for arm in ARMS:
            res["stats"][arm] = {}
            for y in years:
                st = year_stats(rows, ctrl, arm, y)
                res["stats"][arm][str(y)] = st
                cc = st.get("control") or {}
                log(f"   {arm:8s} {y}: n={st.get('n')} · ret10 وسيط {_pct((st.get('ret10') or {}).get('median'))} · "
                    f"الضبط {_pct(cc.get('median_ctrl'))} · الفرق {_pct(cc.get('diff'))} [{_pct(cc.get('ci_lo'))}، {_pct(cc.get('ci_hi'))}] · "
                    f"أعلى ارتفاع 30 وسيط {_pct((st.get('mfe') or {}).get('median'))} · أكبر هبوط {_pct((st.get('mae') or {}).get('median'))} · "
                    f"الهدف {_pct((st.get('target_hit') or {}).get('rate'), False)} · الفشل {_pct((st.get('failure') or {}).get('rate'), False)}")
        b, txt = verdict_branch(_verdict_rows(res["stats"], "STRICT"))
        res["branch"], res["branch_text"] = b, txt
        res["arms_branch"] = {arm: verdict_branch(_verdict_rows(res["stats"], arm)) for arm in ARMS}
        for arm, (bb, tt) in res["arms_branch"].items():
            log(f"   ذراع {arm}: الفرع {bb} «{tt}» (استكشافيّة — لا تُشحَن)")
        pooled = [r for r in rows if r["cfg"] == "STRICT" and _usable(r) and r["year"] in VERDICT_YEARS]
        oc = [r["oc"] for r in pooled]
        comp = [o for o in oc if o.get("complete")]
        rts = [r["retest"] for r in pooled if r["retest"] != "pending"]
        res["pooled"] = {h_: dist([o.get(h_) for o in oc]) for h_ in [f"ret{x}" for x in HORIZONS] + ["mfe", "mae"]}
        res["telegram"] = {"years": "2023-2025", "branch": b, "branch_text": txt, "pooled": {
            "n": len(pooled), "ret5": res["pooled"]["ret5"].get("median"), "ret10": res["pooled"]["ret10"].get("median"),
            "mfe": res["pooled"]["mfe"].get("median"), "mae": res["pooled"]["mae"].get("median"),
            "target_rate": (sum(1 for o in comp if o.get("target_hit")) / len(comp) if comp else None),
            "fail_rate": (sum(1 for x in rts if x in ("failed_breakout", "failed_retest")) / len(rts) if rts else None)}}
        # اتّجاهُ الفرق لا اسمُ الفرع وحدَه (2026-10-01): «لا ميزة» تشمل «أضعفُ من الضبط» ⟵ فرقُ الوسيط لكلّ سنة حكم يُنقل للرسالة
        res["telegram"]["ctrl_diff"] = {str(y): ((res["stats"]["STRICT"].get(str(y)) or {}).get("control") or {}).get("diff")
                                        for y in VERDICT_YEARS}
        log(f"⚖️ الحكم (STRICT · بالأضعف 2023/2024/2025): الفرع {b} «{txt}»")
        recs = []
        for r in rows:
            rec = {k: r.get(k) for k in ("cfg", "sym", "tf", "pid", "p0_date", "ls_date", "head_date", "rs_date", "b_date",
                                         "entry", "ls_px", "head_px", "rs_px", "neck_b", "neck_type", "target", "target_p0",
                                         "quality", "retest", "full_date", "split_win", "vol_ratio", "fsto_k", "fsto_d", "cci",
                                         "compound", "width")}
            rec["match"] = "FULL STRATEGY" if r.get("oc_full") is not None else "STRUCTURAL"
            for k in ("ret1", "ret3", "ret5", "ret10", "ret20", "ret30", "mfe", "max_high", "mfe_date", "mfe_bars", "mae",
                      "min_low", "mae_date", "target_hit", "target_date", "target_bars", "p0_hit", "invalid_bars", "complete"):
                rec[k] = r["oc"].get(k)
            recs.append(rec)
        pd.DataFrame(recs).to_csv(os.path.join(RES_DIR, "hs_history.csv"), index=False)
        res["intraday"] = intraday_descriptive(pop)
        out = os.path.join(RES_DIR, "hs_verdict.json")
        files = [out, os.path.join(RES_DIR, "hs_history.csv")]
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, default=str)
    log(f"💾 {out}")
    if os.environ.get("HS_SAVE", "1") == "1":
        S.git_save(files)
    return 0


def intraday_descriptive(pop) -> dict:
    """فريمُ 5 دقائق (فريمُ فيصل) — **وصفيٌّ بلا حكم** (العقد §⑧: الدقائقُ أسابيعُ لا سنوات): النموذجُ داخل جلسةٍ واحدة."""
    data = _fetch_intraday(pop, completed_only=True)
    rows = []
    for sym, df in data.items():
        ses = _session_codes(df)
        for s in detect(df, STRICT, sym=sym, tf="5m", session=ses):
            o = outcomes(df, s, STRICT, horizons=INTRADAY_HORIZONS, session=ses)
            rt = retest_state(df, s, STRICT)
            rows.append({"sym": sym, "b": s["b_date"], "retest": rt["retest"],
                         **{k: o.get(k) for k in ("ret1", "ret3", "ret6", "ret12", "ret_eod", "mfe", "mae", "target_hit")}})
    first = min((str(df.index[0])[:10] for df in data.values()), default=None)
    last = max((str(df.index[-1])[:10] for df in data.values()), default=None)
    # تشخيصٌ وصفيّ (2026-10-01): التشغيلةُ الأولى طبعت نافذةً تبدأ 2000-01-03 لشموع «أسابيع» ⟵ يُسمّى كلُّ إطارٍ يبدأ قبل آخر 120 يومًا
    old_first = sorted(((str(df.index[0])[:10], s_) for s_, df in data.items()
                        if last and str(df.index[0])[:10] < (pd.Timestamp(last) - pd.Timedelta(days=120)).isoformat()[:10]))[:10]
    out = {"symbols_with_bars": len(data), "window": [first, last], "window_outliers": old_first, "n": len(rows),
           "ret1": dist([r["ret1"] for r in rows]), "ret3": dist([r["ret3"] for r in rows]), "ret6": dist([r["ret6"] for r in rows]),
           "ret12": dist([r["ret12"] for r in rows]), "ret_eod": dist([r["ret_eod"] for r in rows]),
           "mfe_to_eod": dist([r["mfe"] for r in rows]), "mae_to_eod": dist([r["mae"] for r in rows]),
           "target_hit": (sum(1 for r in rows if r["target_hit"]) / len(rows) if rows else None),
           "retest": {x: sum(1 for r in rows if r["retest"] == x) for x in sorted(set(r["retest"] for r in rows))},
           "verdict": "لا حكم (وصفيّ)"}
    log(f"🕔 5 دقائق (وصفيّ · لا حكم): رموز {len(data)} · نافذة {first} ⟵ {last} · إشارات {len(rows)} · "
        f"وسيط حتى نهاية الجلسة {_pct(out['ret_eod'].get('median'))}")
    return out


def run_ticker(sym: str, tf: str = "1d") -> int:
    """فحصُ سهمٍ عند الطلب ⟵ رسالةٌ بحالته ‏+ شارتُه (للمشرف) — يوميٌّ أو 5 دقائق (5 دقائق: **قراءةٌ متأخّرة ‏≈15 دقيقة** · لا لحظيّ)."""
    import Super_stock as S
    sym = (sym or "").upper().strip()
    ses = None
    if tf == "5m":
        df = _fetch_intraday([sym]).get(sym)
        ses = _session_codes(df) if df is not None and len(df) else None
    else:
        df = (_fetch_live([sym])[0] or {}).get(sym)
    if df is None or not len(df):
        S.send_telegram(f"🔎 <b>{TOOL_NAME}</b>\n\nTicker: ${S.esc(sym)}\nتعذّر جلبُ الشموع.\n\n" + S.FOOTER)
        return 3
    lc = lifecycle(df, sym=sym, tf=tf, session=ses)
    dq = S.dq_disclosure_line(sym, df) if tf == "1d" else None
    msg = build_alert(sym, lc, tf=tf, hist=load_hist(), dq_line=dq)
    log(msg)
    S.send_telegram(msg + "\n\n" + S.FOOTER)
    shape = lc.get("sig") or lc.get("forming")
    if shape:
        try:
            path = render_chart(df, shape, os.path.join(CHART_DIR, f"hs_{sym}.png"),
                                title=f"{sym} {TF_EN.get(tf, tf)} inverse H&S · {lc.get('state')}",
                                rt=lc.get("retest"))
            S.send_telegram_document(path, caption=f"{TOOL_NAME} · ${sym} · {TF_EN.get(tf, tf)}")
        except Exception as e:                                             # noqa: BLE001
            log(f"⚠️ الشارت تعذّر: {type(e).__name__}")
    return 0


def run_query(limit: int = 25) -> int:
    """«أعطني الأسهم التاريخية التي طابقت نموذج الرأس والكتفين» ⟵ أحدثُ الحالات من `hs_history.csv` ‏+ الملفُّ كاملًا (للمشرف)."""
    import Super_stock as S
    path = os.path.join(RES_DIR, "hs_history.csv")
    if not os.path.exists(path):
        S.send_telegram(f"🔎 <b>{TOOL_NAME}</b>\nالسجلُّ التاريخيّ لم يُبنَ بعد (يُبنى بتشغيلة الحكم المسجَّلة).\n\n" + S.FOOTER)
        return 0
    df = pd.read_csv(path)
    d = df[(df["cfg"] == "STRICT") & (df["split_win"].astype(str) == "False")].sort_values("b_date", ascending=False)

    def g(r, k):
        v = r.get(k)
        return None if v is None or (isinstance(v, float) and not np.isfinite(v)) else v
    L = [f"🔎 <b>{TOOL_NAME}</b> — الحالاتُ التاريخيّة على أسهم البوت (أحدث {min(limit, len(d))} من {len(d)})", "",
         "Ticker · Date · TF · Match · Breakout · +5D · +10D · Max Run-Up · Max DD · Target (⏳ = نافذةُ الـ30 جلسة مفتوحة)"]
    for _, r in d.head(limit).iterrows():
        r = r.to_dict()
        # ⏳ نافذةُ الـ30 جلسة لم تكتمل (`complete`) ولم يُبلَغ الهدفُ بعد ⟵ لا يُقرأ «✖️ لم يبلغ» (عطلٌ مُثبَت 2026-10-01: PWCM/LVLU
        # اخترقا 09-30 بلا شمعةٍ بعده ووُسما ✖️ · HS41)
        th = g(r, "target_hit")
        tgt = "✅" if str(th) == "True" else ("—" if th is None else ("✖️" if str(g(r, "complete")) == "True" else "⏳"))
        L.append(f"${S.esc(r['sym'])} · {r['b_date']} · 1D · {r.get('match', 'STRUCTURAL')} · {_px(g(r, 'entry'))} · "
                 f"{_pct(g(r, 'ret5'))} · {_pct(g(r, 'ret10'))} · {_pct(g(r, 'mfe'))} · {_pct(g(r, 'mae'))} · {tgt}")
    hist = load_hist()
    L += [""] + history_block(hist) + ["", verdict_line(hist)]
    S.send_telegram("\n".join(L) + "\n\n" + S.FOOTER)
    S.send_telegram_document(path, caption=f"{TOOL_NAME} — السجلّ التاريخيّ كاملًا (CSV)")
    return 0


def load_state(root: str = ".") -> dict:
    try:
        with open(os.path.join(root, STATE_FILE), encoding="utf-8") as fh:
            st = json.load(fh)
        return st if isinstance(st, dict) else {"sent": {}}
    except Exception:                                                      # noqa: BLE001
        return {"sent": {}}


def scan_universe(hist: dict, state: dict, p=None, lookback: int = SCAN_LOOKBACK) -> list:
    """المسحُ الحيّ على أطرٍ **عبرت بوّابةَ السلامة**: اختراقٌ مؤكَّد في آخر `lookback`+1 جلسة ولم يُرسَل معرّفُه ⟵ [(رمز, دورة الحياة)]
    مرتّبةً بالجودة. لا إرسالَ هنا (نقيّة على الأطر · الحالةُ تُقرأ لا تُكتب)."""
    p = dict(STRICT if p is None else p)
    sent = (state or {}).get("sent") or {}
    out = []
    for sym, df in sorted((hist or {}).items()):
        try:
            sigs = detect(df, p, sym=sym, tf="1d")
        except Exception:                                                  # noqa: BLE001
            continue
        n = len(df)
        for s in sigs:
            if s["b_i"] < n - 1 - lookback or s["pid"] in sent:
                continue
            st, rt = signal_state(df, s, p)
            if st == "FAILED":
                continue
            out.append((sym, {"state": st, "sig": s, "retest": rt, "new": s["b_i"] == n - 1}))
    out.sort(key=lambda x: -x[1]["sig"]["quality"])
    return out


def run_scan(fetch=None) -> int:
    """المسحُ اليوميّ بعد الإغلاق (§40 من أمر المالك · العقد §⑪): أحدثُ الشموع ⟵ حارسُ التغطية ⟵ بوّابةُ السلامة ⟵ الكشف ⟵ دورةُ الحياة ⟵
    الجودة ⟵ تلغرام — رسالةٌ لكلّ نموذجٍ جديد **مرّةً واحدة** (معرّفُه في `hs_state.json` **بعد** الإرسال) حتى `SCAN_MAX_MSGS` بالجودة
    والباقي سطرٌ بأسمائهم · وتعذّرُ البيانات يُعلَن ولا يُقرأ صمتُه «لا نموذج». `fetch` محقونٌ للاختبار."""
    import Super_stock as S
    pop = scan_population()
    hist, rep = (fetch or _fetch_live)(pop)
    hist = hist or {}
    cov = len(hist) / float(len(pop) or 1)
    log(f"🔎 {TOOL_NAME} · مسح · المجتمع {len(pop)} · شموعٌ {len(hist)} ({cov:.1%})")
    if cov < SCAN_MIN_COVERAGE:
        S.send_telegram(f"🔎 <b>{TOOL_NAME}</b>\n⚠️ تعذّر المسح اليوم: شموعٌ لـ{len(hist)} من {len(pop)} سهمًا فقط "
                        f"({cov:.0%}) — لا يُقرأ الصمتُ «لا نموذج».\n\n" + S.FOOTER)
        return 3
    kept = S.dq_filter([{"symbol": s} for s in sorted(hist)], hist, scope="hs_scan")
    ok = {it["symbol"]: hist[it["symbol"]] for it in kept}
    state = load_state()
    found = scan_universe(ok, state)
    log(f"   بعد بوّابة السلامة {len(ok)} (محجوز {len(hist) - len(ok)}) · نماذجُ جديدة {len(found)}")
    hist_stats = load_hist()
    sent = state.setdefault("sent", {})
    for sym, lc in found[:SCAN_MAX_MSGS]:
        msg = build_alert(sym, lc, tf="1d", hist=hist_stats)
        if not S.send_telegram(msg + "\n\n" + S.FOOTER):
            continue
        sent[lc["sig"]["pid"]] = lc["sig"]["b_date"]
        # السجلُّ يُسمّي ما أُرسل (الاختبارُ الطرفيّ `36922279556` عرف LVLU من `hs_state.json` لا من السجلّ · HS43)
        log(f"   📤 أُرسل: ${sym} · {lc['state']} · جودة {lc['sig']['quality']}/100 · اختراق {lc['sig']['b_date']}")
        try:
            path = render_chart(ok[sym], lc["sig"], os.path.join(CHART_DIR, f"hs_{sym}.png"),
                                title=f"{sym} 1D inverse H&S · {lc['state']}",
                                rt=lc.get("retest"))
            S.send_telegram_document(path, caption=f"{TOOL_NAME} · ${sym} · 1D")
        except Exception as e:                                             # noqa: BLE001
            log(f"⚠️ الشارت تعذّر: {type(e).__name__}")
    rest = found[SCAN_MAX_MSGS:]
    if rest:
        line = (f"🔎 <b>{TOOL_NAME}</b>\nنماذجُ أخرى اليوم ({len(rest)}) خارج حدّ {SCAN_MAX_MSGS} رسائل (أدنى جودة): "
                + " · ".join(f"${S.esc(sym)} ({lc['sig']['quality']}/100)" for sym, lc in rest))
        if S.send_telegram(line + "\n\n" + S.FOOTER):
            for sym, lc in rest:
                sent[lc["sig"]["pid"]] = lc["sig"]["b_date"]
            log("   📤 أُرسل سطرُ الباقين: " + " · ".join(f"${sym}" for sym, _ in rest))
    state["last_scan"] = dt.date.today().isoformat()
    with open(STATE_FILE, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=1)
    S.git_save([STATE_FILE])
    return 0


def main() -> int:
    mode = (os.environ.get("HS_MODE") or "").strip().lower()
    if mode in ("dev", "verdict"):
        return run_research(mode)
    if mode == "ticker":
        return run_ticker(os.environ.get("HS_TICKER", ""), (os.environ.get("HS_TF") or "1d").strip().lower())
    if mode == "query":
        return run_query()
    if mode == "scan":
        return run_scan()
    log("⚠️ HS_MODE = dev | verdict | ticker | query | scan")
    return 2


if __name__ == "__main__":
    sys.exit(main())
