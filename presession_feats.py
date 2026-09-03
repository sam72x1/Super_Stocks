# -*- coding: utf-8 -*-
"""🌙⏱️ ميزاتُ ما قبل الجلسة الممتدّة — **مصدرٌ واحد** تقرؤه أداةُ القياس
(`presession_scan.py`) والأداةُ الحيّة (`presession_radar.py`) معًا.

🔒 **ولماذا وحدةٌ ثالثة:** لو نسخت الأداةُ الحيّة حسابَ الميزات لصار على الظاهرة
**قراءتان** فيُقاس شيءٌ ويُرسَل غيرُه — وهو عينُ العيب المدوَّن في `T-VOLBASE`
(«محاكاةُ الإنتاج تشمل ما يفعله المُنادي لا جسمَ الدالّة وحدَه»).

🔒 **نقيّةٌ تمامًا:** بلا شبكةٍ وبلا ملفّاتٍ وبلا استيرادِ `Super_stock` — فتُختبَر
بالورقة، ويستحيل أن يؤخّر حسابُها خيطَ التنبيه.

**عقدُ الشمعة (ثماني خانات):** `(ms, o, h, l, c, v, n, mod)` حيث `n` عددُ الصفقات
و`mod` **دقيقةُ نيويورك** من منتصف الليل (‏04:00 = 240 · 09:30 = 570 · 16:00 = 960
· 20:00 = 1200).
"""
from __future__ import annotations

import statistics

PRE_OPEN = 4 * 60         # 04:00 نيويورك — بدءُ البريماركت
EXT_CLOSE = 20 * 60       # 20:00 نيويورك — نهايةُ الافتر
DECISION_LEAD = 10        # عشرُ دقائقَ قبل الجلسة (نصُّ المالك)
WINDOWS = (10, 30, 60)    # الحاكمةُ 10 · وتراجعٌ مقفولٌ 30 ⟵ 60 ⟵ الجلسة
TOPK = 10                 # سقفُ القائمة (سقفُ النجاح §⑧)
HIT_PCT = 80.0            # رقمُ المالك: «+80% فأكثر»
LABEL_MIN_USD = 20_000.0  # engineering — أرضيةُ تنفيذٍ على نافذة الوسم (العقد §③)
LADDER = (30.0, 50.0, 100.0)   # وصفيّ لا يحكم
ROLL_N = 60               # طولُ الذاكرة المتدحرجة (‏spike60)

# الميزاتُ المرتَّبة تنازليًّا (الأعلى = مرشَّحٌ أقوى) في الترتيب المنفرد `S0`.
FEATS_DESC = ("day_ret", "range_pos", "vwap_rel", "gap_open", "ret_30",
              "vol_share_30", "vol_accel", "usd_day", "n5", "max_volx", "anchor",
              "spt_30", "tx_last5", "hold_vwap", "pre_usd", "pre_ret", "pre_share",
              "post_usd", "post_ret", "post_hi_ret", "post_share",
              "dist_low20", "spike60", "usd_rel20", "down_streak")
FEATS_ASC = ("compress", "gap_min", "price")
BASELINES = {"B1": "usd_day", "B2": "day_ret"}

# 🔴 **مفتاحُ الترتيب الحيّ — مؤقّتٌ ومُعلَنٌ حتى يصدر حكمُ `T-PRESESSION`.**
# قبل الأرقام لا أدّعي أن ترتيبًا يتنبّأ؛ فالمفتاحُ الافتراضيُّ `usd_day` هو
# **خطُّ الأساس `B1` بعينه** (لا اختراعَ ولا معايرة)، ويُبدَّل بسطرٍ واحد بعد الحكم.
# 🔒🔴 **مفاتيحُ هويّة الصفّ — مصدرٌ واحدٌ لا ثلاثة.** كانت مكتوبةً حرفيًّا في
#    ثلاثة ملفّات فتفرّقت: الماسحُ يكتب `sess` · وأداةُ الحكم تقرأ `slot` ·
#    والسجلُّ الأماميُّ يكتب `slot` ⇒ **الحكمُ تخطّى الخلايا الثمانَ كلَّها بصمت**
#    (صنفُ «المفتاح المتخيَّل»، ثالثَ مرّةٍ في هذا الملفّ). ⇒ **الاسمُ من هنا حصرًا.**
ROW_DAY = "day"
ROW_SESS = "sess"
ROW_SYM = "sym"
ROW_WIT = "wit"

# 🔴 **مفتاحُ الترتيب صار لكلّ جلسةٍ مفتاحُها** — بأمر المالك «شغّل البريماركت»
#    (2026-09-03). كان `usd_day` مؤقّتًا مُعلَنًا حتى يصدر الحكم، **وقد صدر ومعه
#    السبب**: `usd_day` هو **الشاهدُ `B1` المقيسُ عند 0.00%** في النافذة الحاكمة
#    (‏`PM · 10د` لسنة التقييم) ⇒ إبقاؤه يعني تصدُّرَ أسماءٍ بسيولةِ مئات الملايين
#    (‏`TSLL` تصدّر أوّلَ قائمةٍ حيّة بـ‏$772 مليونًا).
# 🔑 **والاختيارُ من سنتَي المعايرة وحدهما (2023-2024) لا من سنة التقييم:**
#    `post_hi_ret` **الأوّلُ في السنتين** (‏33.1× ثم 112.5×)، وعلى **2025 خارج
#    العيّنة**: ‏26 إصابةً من 2,500 اسمًا (‏`P@10` = 1.04% · رافعة 77.4×) ومنها
#    **‏26 من 87 منفجرًا (‏`R@10` = 29.9%)**. و`post_ret` تصدّر 2025 (‏1.20%)
#    **ولم يتصدّر 2023** ⇒ اختيارُه بعد رؤية سنة التقييم قرارٌ بعديّ فلم يُختَر.
# 🔒 **والافترُ يبقى على خطّ الأساس:** حقولُ `post_*` **معدومةٌ بالتعريف** في قرار
#    15:50 (هي افترُ اليوم ولم يبدأ) ⇒ الترتيبُ بها يُفرِّغ القائمة؛ وهو صامتٌ
#    أصلًا بأمر المالك (الإرسالُ للبريماركت وحدَه).
RANK_KEY = "usd_day"          # الافترُ · خطُّ الأساس · التوافقُ الخلفيّ
RANK_ASC = False
RANK_BY_SLOT = {"PM": "post_hi_ret"}


def rank_key(slot: str | None = None) -> str:
    """مفتاحُ ترتيبِ الجلسة — **مصدرٌ واحد** يقرؤه الترتيبُ والرسالةُ والسجلّ معًا،
    فلا يُرتَّب بمفتاحٍ ويُقال في الرسالة غيرُه."""
    return RANK_BY_SLOT.get(str(slot or "").strip().upper(), RANK_KEY)

def _r(x, nd=5):
    try:
        if x is None:
            return None
        x = float(x)
        if x != x or x in (float("inf"), float("-inf")):
            return None
        return round(x, nd)
    except (TypeError, ValueError):
        return None


class LookAhead(Exception):
    """`V1` — خرقٌ لقاعدة «لا نظرَ مستقبليّ»: شمعةٌ بعد القرار وصلت إلى حساب ميزة."""


def core_feats(reg: list, pre: list, prev_close: float, cut: int) -> dict | None:
    """ميزاتُ الجلسة النظامية حتى `cut` (دقيقةُ نيويورك، حصريّة) + ميزاتُ البريماركت.
    `reg`/`pre` شموعٌ (ms,o,h,l,c,v,n,mod) **قبل** القرار. يُرجع None بلا آخر سعر."""
    if any(b[7] >= cut for b in reg) or any(b[7] >= cut for b in pre):
        raise LookAhead(f"شمعةٌ ≥ {cut}")
    if not reg or not prev_close or prev_close <= 0:
        return None
    last = reg[-1][4]
    vol_day = sum(b[5] for b in reg)
    usd_day = sum(b[4] * b[5] for b in reg)
    tx_day = sum(b[6] for b in reg)
    hi, lo = max(b[2] for b in reg), min(b[3] for b in reg)
    vwap = (usd_day / vol_day) if vol_day > 0 else None
    t30, t15, t5 = cut - 30, cut - 15, cut - 5
    last30 = [b for b in reg if b[7] >= t30]
    base30 = [b for b in reg if b[7] < t30]
    vol30 = sum(b[5] for b in last30)
    tx30 = sum(b[6] for b in last30)
    v15a = sum(b[5] for b in reg if b[7] >= t15)
    v15b = sum(b[5] for b in reg if t30 <= b[7] < t15)
    n5 = sum(1 for b in reg if b[1] > 0 and (b[4] - b[1]) / b[1] >= 0.05)
    # أقصى قفزةِ حجمٍ عن متوسّط سوابقها (‏≥5 سوابق)
    max_volx, run = 0.0, 0.0
    for i, b in enumerate(reg):
        if i >= 5 and run > 0:
            max_volx = max(max_volx, b[5] / (run / i))
        run += b[5]
    span = reg[-1][7] - reg[0][7] + 1
    tx5 = sum(b[6] for b in reg if b[7] >= t5)
    out = {
        "price": last,
        "day_ret": last / prev_close - 1.0,
        "range_pos": ((last - lo) / (hi - lo)) if hi > lo else 0.5,
        "vwap_rel": (last / vwap - 1.0) if vwap else None,
        "gap_open": reg[0][1] / prev_close - 1.0 if reg[0][1] > 0 else None,
        "ret_30": (last / base30[-1][4] - 1.0) if base30 and base30[-1][4] > 0 else None,
        "vol_share_30": (vol30 / vol_day) if vol_day > 0 else None,
        "vol_accel": (v15a / v15b) if v15b > 0 else None,
        "usd_day": usd_day,
        "n5": n5,
        "max_volx": max_volx if max_volx > 0 else None,
        "spt_30": ((vol30 / tx30) / (vol_day / tx_day))
                  if tx30 > 0 and tx_day > 0 and vol_day > 0 else None,
        "tx_last5": (tx5 / (tx_day / len(reg) * 5.0)) if tx_day > 0 else None,
        "compress": ((max(b[2] for b in last30) - min(b[3] for b in last30)) / (hi - lo))
                    if last30 and hi > lo else None,
        "hold_vwap": (1 if (vwap is not None and last30
                            and min(b[3] for b in last30) >= vwap) else 0),
        "bars_n": len(reg),
        "gap_min": max(0, span - len(reg)),
        "pre_usd": sum(b[4] * b[5] for b in pre),
        "pre_ret": (pre[-1][4] / prev_close - 1.0) if pre else None,
        "pre_share": (sum(b[5] for b in pre) / (sum(b[5] for b in pre) + vol_day))
                     if (pre and (sum(b[5] for b in pre) + vol_day) > 0) else None,
    }
    return out


def post_feats(post: list, reg_close: float, vol_all: float) -> dict:
    """ميزاتُ الافتر (لقرار `PM` من اليوم السابق) — `post` شموعُ 16:00–20:00."""
    if not post or not reg_close or reg_close <= 0:
        return {"post_usd": 0.0, "post_ret": None, "post_hi_ret": None,
                "post_share": None, "post_last": None}
    vp = sum(b[5] for b in post)
    return {"post_usd": sum(b[4] * b[5] for b in post),
            "post_ret": post[-1][4] / reg_close - 1.0,
            "post_hi_ret": max(b[2] for b in post) / reg_close - 1.0,
            "post_share": (vp / vol_all) if vol_all > 0 else None,
            "post_last": post[-1][4]}


def rolling_feats(hist: list, ref: float, usd_today) -> dict:
    """من ملخّصات الأيام السابقة (الأقدم أوّلًا): مسافةُ القاع/القمّة 20 · سلسلةُ
    الهبوط · تاريخُ الرفعات 60 · دولارُ اليوم نسبةً لوسيط 20."""
    if not hist or not ref or ref <= 0:
        return {"hist_n": len(hist or []), "dist_low20": None, "dist_high20": None,
                "down_streak": None, "spike60": None, "days_since_spike": None,
                "usd_rel20": None}
    h20 = hist[-20:]
    lows = [d["lo"] for d in h20 if d.get("lo")]
    highs = [d["hi"] for d in h20 if d.get("hi")]
    usds = [d["usd"] for d in h20 if d.get("usd") is not None]
    streak = 0
    for d in reversed(hist):
        if d.get("ret") is not None and d["ret"] < 0:
            streak += 1
        else:
            break
    spikes = [i for i, d in enumerate(hist[-ROLL_N:]) if (d.get("ret") or 0) >= 0.5]
    med = statistics.median(usds) if usds else None
    return {"hist_n": len(hist),
            "dist_low20": (ref / min(lows) - 1.0) if lows and min(lows) > 0 else None,
            "dist_high20": (ref / max(highs) - 1.0) if highs and max(highs) > 0 else None,
            "down_streak": streak,
            "spike60": len(spikes),
            "days_since_spike": (len(hist[-ROLL_N:]) - 1 - spikes[-1]) if spikes else None,
            "usd_rel20": (usd_today / med) if (med and usd_today is not None) else None}


def order_rows(rows: list, key: str, k: int = TOPK, asc: bool = False) -> list:
    """أعلى `k` صفًّا بالمفتاح — كسرُ التعادل **بالرمز** (حتميّ لا عشوائيّ)،
    والقيمةُ الغائبة لا تُرتَّب (‏«تعذّرٌ ليس صفرًا»)."""
    cand = [r for r in rows if r.get(key) is not None]
    cand.sort(key=lambda r: ((r[key] if asc else -r[key]), r.get("sym") or ""))
    return cand[:k] if k else cand
