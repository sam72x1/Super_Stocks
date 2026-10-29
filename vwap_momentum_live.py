"""🟠 «زخم الفيواب» — أداةُ تنبيهٍ حيّة على تلغرام · ⚠️ قيد الإثبات الأماميّ (أمرُ المالك 2026-10-29).

**التعريفُ = الملحق 3** (`vwap_mom_prereg_addendum_3.md` §③ — «الملحق 3 كتعريف نهائي») **بدوالّ الجدوى نفسِها بالاسم** فلا يُعاد
كتابةُ شرطٍ بيدٍ ثانية: الكسرُ الصاعد `V3.break_events` · L `V3.event_liq` · إعادةُ الاختبار `V3.retest_signal` · VWAP والسلال
`V3.vwap_series`/`V3.bucketize` · التراكمُ الدولاريّ `V3.cum_dollar_at` · ① `V4.pct_change`/`V4.ge` · ② `V4.rvol`/`V4.cum_curve`/`V4.curve_at`/
`V4.vol_factor` · تسويةُ إغلاق الأمس `V4.price_factor` · ④ `V4.wire_index`/`V4.catalyst4` · وقبولُ SEC `V3.make_acc_ts`/`V3.sec_index`.
(بُنيت كلُّها لعدّ أحداث يومٍ كامل في الجدوى · وهنا تُغذّى **بالشموع المكتملة حتى لحظة الفحص** وحدَها — والدوالُّ سببيّةٌ بالبناء:
حدثٌ نهايتُه قبل لحظة الفحص لا يتغيّر بشموعٍ بعدها · مقفولٌ في `VWL3`.)

**وقراراتُ المالك 2026-10-29 فوقه:** الحجمُ الدولاريّ التراكميّ حتى الحدث **250 ألفًا** (أدنى درجةٍ مسجّلة) · أرضيّةُ السعر **1.00** ·
RVOL **من 04:00** · الحدثُ المكتشَف بعد إغلاق شمعته بأكثر من **10 دقائق لا يُرسَل ويُسجَّل** · وإعادةُ الاختبار **حتى 3 في اليوم لكلّ لمسةٍ
جديدة** (مثالُ AZTR) · والجلسةُ النظاميّة وحدَها (نايف: «ماهي بري ماركت او افتر»).

**عرضٌ لا إدارة:** EMA9 (على إغلاقات 5 دقائق من بداية الجلسة · العقد §②) · الوقفُ المقترح · سلّمُ الجني — نصوصٌ في الرسالة لا قرار.
**خارج الجذور تمامًا:** لا يمسّ `Super_stock.py` ولا القائمةَ ولا «تحت المتابعة» — يستورد منه `send_telegram`/`git_save` في الوضع الحيّ وحدَه.

الأوضاع (`--mode`): `live` (الإرسالُ لا يقع إلّا بـ`VWL_SEND=1`) · `replay` (آخرُ N جلساتٍ مكتملة صامتةً · بلا تلغرام) ·
`trace` (سهمٌ ويوم: كلُّ لمسةٍ وحدثٍ بشروطه) · `harvest` (حصادُ ما بعد الإغلاق لسجلّ التنبيهات) · `probe` (فحصُ المنافذ الحيّة) ·
و`--pre-open-sleep` لجوبَي الانتظار. **والفشلُ يُعلَن بخروجٍ غير صفريّ لا يُكتَم.**
"""
import argparse
import datetime as dt
import json
import os
import sys
import time

import vwap_mom_feas as V3
import vwap_mom_feas_v4 as V4

# ── الثوابت (كلُّ رقمٍ بوسمه في `FAISAL_SOURCE_LEDGER.md` §«زخم الفيواب الحيّة») ─────────────────────────
NY = V3.NY
D_MIN_LIVE = V3.D_LADDER[0]          # 250,000 — قرارُ المالك 2026-10-29 (أدنى درجةٍ مسجّلة)
PX_MIN = 1.00                        # قرارُ المالك 2026-10-29 («تبقى 1.00») = `prelink_px.PX_MIN` = الملحق 3 ⑤
PX_MAX = V4.PX_MAX                   # 20.0 — الملحق 3 ⑤ (بأمر المالك)
CHG_MIN = V4.CHG_MIN                 # 0.20 — الملحق 3 ① (engineering بأمر المالك)
RVOL_MIN = V4.RVOL_MIN               # 3.0 — الملحق 3 ② (engineering بأمر المالك)
TYPES_OK = V4.TYPES_OK               # CS · ADRC · OS — الملحق 3 ⑤
SPAC_SIC = V4.SPAC_SIC               # 6770 — الملحق 3 ⑤
D_MAX_PER_DAY = 3                    # إعادةُ الاختبار حتى 3 في اليوم — أمرُ المالك 2026-10-29 (مثالُ AZTR «3 مرات»)
FRESH_MAX_S = 600                    # أكثرُ من 10 دقائق بعد إغلاق الشمعة ⟵ لا يُرسَل ويُسجَّل — قرارُ المالك 2026-10-29
LOOP_OFFSET_S = 25                   # الفحصُ بعد حدّ الشمعة بثوانٍ (المزوّدُ ينشر الدقيقة خلال ‏≈2ث — مقيس) — engineering
EMA_N = 9                            # EMA9 على إغلاقات 5 دقائق من بداية الجلسة — العقد §② (`nayef_verbatim` الطول)
LEDGER = "vwap_live_ledger.jsonl"    # سجلُّ الحصاد الإلحاقيّ (يُدفَع) — أمرُ المالك ④
SEG_SPLIT_MIN = 195                  # حدُّ المقطعين (سقفُ جوب GitHub 6 ساعات · كرادار الانطلاق)
PRE_OPEN_LEAD_MIN = 10               # جوبُ النوم يستيقظ قبل الجرس بعشر دقائق
PRE_OPEN_CAP_MIN = 340               # تحت سقف الجوب 360
PRE_OPEN_NEXT_FROM_NY_MIN = 20 * 60   # بعد نهاية الأفتر (20:00 نيويورك) فالجلسةُ المقصودة الغد — كرونُ 02:xx UTC يخدم جلسةَ يومه (engineering)
# ③ L — أمرُ المالك 2026-10-29: تعريفُ 3×3 الصارم هندسيٌّ من عندنا لا من نايف وأسقط مثالَه (AZTR 11:05 بـ2%) ⟵ تعريفان يُقارَنان
#    والإنتاجُ على `L_DEF` · **معايَرٌ على مثال المصدر نفسِه** (حدُّ صدق · لا قياسَ خارج العيّنة) · ورفضُ نمط القروبات كما هو (إغلاقُ الثالثة ≥ الأولى)
L_DEFS = ("strict", "T", "M")        # strict = `V3.liq_ok`/`liq15_ok` كما كانت · T = تسامح 5% مع المتاح · M = وسيطُ الجلسة حتى اللحظة
L_TOL = 0.95                         # «تسامح 5% في مقارنة 3×3» — مثالُ المالك 2026-10-29 (engineering · معايَرٌ على AZTR)
L_DEF_DEFAULT = "T"                  # الإنتاج — يُختار بأثره على الإعادة وAZTR (`vwap_live_acceptance.md` §③)
LAST_CLOSE_LOOKBACK_D = 90           # «اعتمد آخر إغلاق للموقوف» (أمرُ المالك 2026-10-29): آخرُ إغلاقٍ في 90 يومًا قبل اليوم — engineering
FUND_SIC = ("6722", "6726", "6798")  # ⑤ «لا صناديق» بكود SIC (أمرُ المالك 2026-10-29): صناديقُ مفتوحة · مغلقة/وحدات · REIT
FLAT_N, FLAT_PCT = 6, 0.01           # وسمُ «📌 استحواذ نقدي»: مدى آخر 6 شموع 5د حتى 1% من السعر مع 8-K بند 1.01 — engineering (عرضٌ لا رفض)
NEAR_CLOSE_MOD = 15 * 60 + 45        # وسمُ «⏱️ قرب الإغلاق»: إكمالُ الشمعة 15:45 نيويورك فما بعد — أمرُ المالك 2026-10-29 (عرضٌ لا رفض)
WIRE_LIMIT_NOTE = ("مصادرُ الخبر المرئيّة: GlobeNewswire و8-K وحدهما — PRNewswire وBusiness Wire وAccesswire "
                   "غائبةٌ عن أخبار Polygon (قِيست صفرًا) فسهمٌ خبرُه عليها لن يُلتقط")


def log(m=""):
    print(m, flush=True)


# ── دوالُّ نقيّة (بلا شبكة · مقفولةٌ في السويّة) ────────────────────────────────────────────────────────
def ny_parts(ts_ms):
    """طابعُ Polygon (ميلّي ثانية UTC لبداية الدقيقة) ⟵ (يومُ نيويورك، دقيقةُ اليوم)."""
    d = dt.datetime.fromtimestamp(int(ts_ms) / 1000.0, tz=NY)
    return d.date().isoformat(), d.hour * 60 + d.minute


def bars_by_day(results):
    """نتائجُ `/v2/aggs` ⟵ {يوم: [(دقيقة، o، h، l، c، v)] مرتّبة} — صيغةُ `V3` نفسُها."""
    out = {}
    for r in results or ():
        try:
            day, m = ny_parts(r["t"])
            out.setdefault(day, []).append((m, float(r["o"]), float(r["h"]), float(r["l"]), float(r["c"]), float(r.get("v") or 0.0)))
        except (KeyError, TypeError, ValueError):
            continue
    for v in out.values():
        v.sort(key=lambda b: b[0])
    return out


def complete_buckets(bars, op, cl, upto):
    """سلالُ الجلسة النظاميّة **المكتملة** حتى `upto` (دقيقةُ حدٍّ): الدقائقُ قبل upto وحدَها ثمّ السلالُ التي نهايتُها ≤ upto
    ⟵ (b5، b15، دقائقُ النظاميّة) — VWAP من الافتتاح (الملحق 1 · الذراع A)."""
    end = min(cl, upto)
    bb = [b for b in bars if op <= b[0] < end]
    vw = V3.vwap_series(bb)
    b5 = [x for x in V3.bucketize(bb, vw, op, 5, cl) if x["e"] <= upto]
    b15 = [x for x in V3.bucketize(bb, vw, op, 15, cl) if x["e"] <= upto]
    return b5, b15, bb


def _mean(xs):
    return sum(xs) / len(xs)


def _median(xs):
    s_ = sorted(xs)
    n = len(s_)
    return s_[n // 2] if n % 2 else (s_[n // 2 - 1] + s_[n // 2]) / 2.0


def resolve_ldef(v=None):
    """تعريفُ ③ L: المُمرَّر أو `VWL_LDEF` (لوضعي replay/trace) وإلّا `L_DEF_DEFAULT` — وغيرُ المعروف ⟵ الافتراضيّ."""
    v = (v if v is not None else os.environ.get("VWL_LDEF", "")).strip()
    return v if v in L_DEFS else L_DEF_DEFAULT


def liq5(b5, i, ldef):
    """③ L لإكمال 5x3 عند الشمعة i. strict = `V3.liq_ok` بالاسم · T = متوسّطُ دولار الشموع الثلاث ≥ 0.95 × متوسّطِ ما قبلها
    (حتى ثلاث · **المتاحُ** حين يقلّ عن ثلاث · ولا شيءَ قبلها ⟵ لا) · M = متوسّطُ الثلاث ≥ وسيطِ دولار شموع الجلسة حتى i —
    وفي T وM معًا إغلاقُ الثالثة ≥ إغلاقِ الأولى (رفضُ نمط القروبات كما هو)."""
    if ldef == "strict":
        return V3.liq_ok(b5, i)
    if i < 2:
        return False
    hold = [b5[k]["dv"] for k in (i - 2, i - 1, i)]
    keep = b5[i]["c"] >= b5[i - 2]["c"]
    if ldef == "T":
        prior = [b5[k]["dv"] for k in range(max(0, i - 5), i - 2)]
        return bool(prior) and keep and _mean(hold) >= L_TOL * _mean(prior)
    if ldef == "M":
        return keep and _mean(hold) >= _median([b["dv"] for b in b5[:i + 1]])
    raise ValueError(ldef)


def liq15(b15, j, ldef):
    """③ L لإكمال 15x1 عند السلّة j. strict = `V3.liq15_ok` · T = دولارُها ≥ 0.95 × السابقة (ولا سابقةَ ⟵ لا) ·
    M = دولارُها ≥ وسيطِ سلال الجلسة حتى j — وإغلاقُها ≥ افتتاحِها في الثلاثة."""
    if ldef == "strict":
        return V3.liq15_ok(b15, j)
    keep = b15[j]["c"] >= b15[j]["o"]
    if ldef == "T":
        return j >= 1 and keep and b15[j]["dv"] >= L_TOL * b15[j - 1]["dv"]
    if ldef == "M":
        return keep and b15[j]["dv"] >= _median([b["dv"] for b in b15[:j + 1]])
    raise ValueError(ldef)


def event_L(b5, b15, ev, ldef):
    """③ L للحدث = `V3.event_liq` بالتعريف المختار (strict يطابقه بت-بت · `VWL16`)."""
    _e, kind, idx, _k = ev
    return liq5(b5, idx, ldef) if kind == "5x3" else liq15(b15, idx, ldef)


def retest_hold(b5, b15, after_e, ldef, tol=V3.RETEST_TOL):
    """الذراع D = `V3.retest_signal(…, need_liq=True)` حرفيًّا بـL المختار (strict يطابقه بت-بت · `VWL16`): أوّلُ لمسةٍ تبدأ عند
    `after_e` أو بعده (قاعٌ حتى tol × VWAP) ثمّ أبكرُ ثباتٍ بعدها (ثلاثُ إغلاقاتٍ فوقه أو شمعةُ 15 فوقه) يحقّق L."""
    t = next((i for i, b in enumerate(b5) if b["s"] >= after_e and b["vwap"] is not None and b["l"] <= tol * b["vwap"]), None)
    if t is None:
        return None
    te = b5[t]["e"]

    def above(b):
        return b["vwap"] is not None and b["c"] > b["vwap"]
    cands = []
    for i in range(t + 3, len(b5)):
        if all(above(b5[k]) for k in (i - 2, i - 1, i)) and liq5(b5, i, ldef):
            cands.append((b5[i]["e"], "5x3", i))
            break
    for j in range(len(b15)):
        if b15[j]["s"] >= te and above(b15[j]) and liq15(b15, j, ldef):
            cands.append((b15[j]["e"], "15x1", j))
            break
    return min(cands) if cands else None


def is_flat(b5, e, n=FLAT_N, pct=FLAT_PCT):
    """سعرٌ ثابت: مدى (أعلى − أدنى) آخر n شموع 5د المكتملة حتى e لا يتجاوز pct من إغلاق آخرها — وصفٌ للعرض."""
    w = [b for b in b5 if b["e"] <= e][-n:]
    return len(w) == n and (max(b["h"] for b in w) - min(b["l"] for b in w)) <= pct * w[-1]["c"]


def alert_tags(a, b5, detail):
    """وسومُ عرضٍ بلا رفض (أمرُ المالك 2026-10-29): «📌 استحواذ نقدي» = 8-K بند 1.01 في النافذة ∧ سعرٌ ثابت · «⏱️ قرب الإغلاق» = إكمالٌ 15:45 فما بعد."""
    tags = []
    if (detail or {}).get("acq_101") and is_flat(b5, a["e"]):
        tags.append("📌 استحواذ نقدي")
    if a["e"] >= NEAR_CLOSE_MOD:
        tags.append("⏱️ قرب الإغلاق")
    return tags


def ema_last(values, n=EMA_N):
    """EMA بطول n (‏α = 2/(n+1) · بذرتُه أوّلُ قيمة) ⟵ آخرُ قيمةٍ أو None."""
    a, e = 2.0 / (n + 1.0), None
    for x in values:
        e = x if e is None else a * x + (1.0 - a) * e
    return e


def above_run(b5, end_e):
    """عددُ إغلاقات 5 دقائق المتتالية فوق VWAP المنتهية عند نهاية الحدث `end_e`."""
    n = 0
    for b in reversed([x for x in b5 if x["e"] <= end_e]):
        if b["vwap"] is not None and b["c"] > b["vwap"]:
            n += 1
        else:
            break
    return n


def priors_rvol(cur_shares, priors, e):
    """② عند نهاية الحدث `e`: `priors` = [(يومٌ سابق، منحنى أو None، عاملُ تسوية الحجم)] لعشرين جلسة ⟵ `V4.rvol` بالاسم."""
    pri = [(cv is not None, V4.curve_at(cv, e) * vf) for _d, cv, vf in priors]
    return V4.rvol(cur_shares, pri)


def shares_before(bars, e):
    """حجمُ الأسهم من 04:00 حتى ما قبل `e` (نافذةُ `cum_dollar_at` نفسِها · الملحق 3 ②)."""
    return sum(v for m, _o, _h, _l, _c, v in bars if V3.EXT_START <= m < e)


CHECK_ORDER = ("⑤ السعر", "الحجم الدولاري", "① التغيّر", "③ L", "② RVOL", "⑤ النوع", "⑤ SPAC", "④ الخبر")


def check_event(info, b5, b15, ev, bars, priors_fn, cat_of, type_status, spac, d_min, full_info, ldef="strict"):
    """يفحص حدثَ كسرٍ بترتيب `CHECK_ORDER` ويملأ `info` (liq · rvol · cat) ⟵ قائمةُ ما سقط — تقف عند أوّل سقوطٍ ما لم يُطلب `full_info`."""
    why = []

    def fail(tag):
        why.append(tag)
        return not full_info
    e = info["e"]
    if not (PX_MIN <= info["px"] < PX_MAX) and fail("⑤ السعر"):
        return why
    if info["cum_dollar"] < d_min and fail("الحجم الدولاري"):
        return why
    if not V4.ge(info["chg"], CHG_MIN) and fail("① التغيّر"):
        return why
    info["liq"] = event_L(b5, b15, ev, ldef)
    if not info["liq"] and fail("③ L"):
        return why
    info["rvol"] = priors_rvol(shares_before(bars, e), priors_fn(), e)
    if not V4.ge(info["rvol"], RVOL_MIN) and fail("② RVOL" + (" (مجهول)" if info["rvol"] is None else "")):
        return why
    if type_status != "ok" and fail("⑤ النوع" + (" (مجهول)" if type_status == "unknown" else "")):
        return why
    if spac and fail("⑤ " + ("SPAC" if spac is True else str(spac))):   # True ⟵ SPAC · نصٌّ ⟵ وسمُ SIC (صندوق)
        return why
    info["cat"] = cat_of(e)
    if info["cat"].get("C") is not True:
        fail("④ الخبر" + (" (مجهول)" if info["cat"].get("C") is None else ""))
    return why


def evaluate(bars, op, cl, upto, prev_adj, priors_fn, cat_of, type_status, spac, d_min=D_MIN_LIVE, full_info=False, ldef=None):
    """رمزٌ في يوم حتى `upto` ⟵ {"events": [كلُّ كسرٍ A بشروطه]، "alerts": [A الأوّلُ الكامل ثمّ D#1..3]}.

    A كامل = الملحق 3 **في الحدث نفسِه**: الكسرُ (`break_events`) ∧ ⑤ السعرُ في [PX_MIN، PX_MAX) ∧ الحجمُ الدولاريّ التراكميّ من 04:00 ≥ d_min ∧
    ① ‏+20% فأكثر ∧ ③ L ∧ ② RVOL ≥ 3 ∧ النوعُ مقبولٌ وليس SPAC ∧ ④ خبرُ سلكٍ أو 8-K في النافذة — وحدثٌ أبكرُ ناقصٌ لا يحجب لاحقًا كاملًا.
    الفحصُ بترتيب `CHECK_ORDER` ويقف عند أوّل سقوط (الأغلى آخرًا: ② ثمّ ④) ما لم يُطلب `full_info` (وضعُ التتبّع).
    D = بعد أوّل A كامل: لمسةٌ (قاعُ 5د حتى 1.01 × VWAP) ثمّ الثباتُ مع L (`retest_signal` بالاسم) وفي لحظة إكماله ① و⑤ قائمان
    (الملحق 3 §③-⑥) ثمّ تُبحث اللمسةُ التالية بعد إكماله — حتى `D_MAX_PER_DAY` تنبيهًا.
    `priors_fn()` ⟵ أيّامُ ② (يُنادى عند الحاجة وحدَها) · `cat_of(نهاية)` ⟵ `V4.catalyst4` · `type_status` ∈ {ok · excluded · unknown}."""
    ldef = resolve_ldef(ldef)
    b5, b15, _bb = complete_buckets(bars, op, cl, upto)
    events, alerts, first_full = [], [], None
    for ev in V3.break_events(b5, b15):
        e, kind, idx, _k = ev
        bk = b5[idx] if kind == "5x3" else b15[idx]
        px, vwap = bk["c"], bk["vwap"]
        info = {"e": e, "kind": kind, "px": px, "vwap": vwap, "cum_dollar": V3.cum_dollar_at(bars, e),
                "chg": V4.pct_change(px, prev_adj), "liq": None, "rvol": None, "cat": None}
        info["why"] = check_event(info, b5, b15, ev, bars, priors_fn, cat_of, type_status, spac, d_min, full_info, ldef)
        info["full"] = not info["why"]
        events.append(info)
        if info["full"] and first_full is None:
            first_full = info
    if first_full is not None:
        alerts.append(dict(first_full, arm="A", n=1, above=above_run(b5, first_full["e"]),
                           ema9=ema_last([b["c"] for b in b5 if b["e"] <= first_full["e"]])))
        after, n_d = first_full["e"], 0
        while n_d < D_MAX_PER_DAY:
            rt = retest_hold(b5, b15, after, ldef)
            if rt is None:
                break
            re_, rkind, ridx = rt
            rb = b5[ridx] if rkind == "5x3" else b15[ridx]
            rchg = V4.pct_change(rb["c"], prev_adj)
            if PX_MIN <= rb["c"] < PX_MAX and V4.ge(rchg, CHG_MIN):
                n_d += 1
                alerts.append({"e": re_, "kind": rkind, "px": rb["c"], "vwap": rb["vwap"], "cum_dollar": V3.cum_dollar_at(bars, re_),
                               "chg": rchg, "liq": True, "rvol": priors_rvol(shares_before(bars, re_), priors_fn(), re_),
                               "cat": first_full["cat"], "why": [], "full": True, "arm": "D", "n": n_d,
                               "above": above_run(b5, re_), "ema9": ema_last([b["c"] for b in b5 if b["e"] <= re_])})
            after = re_
    return {"events": events, "alerts": alerts}


def is_fresh(event_ts, detected_ts, fresh_max=FRESH_MAX_S):
    """يُرسَل إن اكتُشف خلال `fresh_max` ثانيةً من إغلاق شمعته (قرارُ المالك: أكثرُ من 10 دقائق ⟵ لا يُرسَل ويُسجَّل)."""
    return (detected_ts - event_ts) <= fresh_max


def alert_key(day, sym, arm, n):
    return f"{day}|{sym}|{arm}|{n}"


def used_keys(rows, day):
    """مفاتيحُ التنبيهات المسجَّلة لليوم (المُرسَلةُ والمتأخّرة معًا) — الدِّدوب: A مرّة · D حتى 3."""
    return {r.get("key") for r in rows if r.get("kind") == "alert" and r.get("date") == day and r.get("key")}


def _hm(mod):
    return f"{mod // 60:02d}:{mod % 60:02d}"


def _pct(x):
    return "؟" if x is None else f"{x * 100:+.0f}%"


def news_brief(cat_detail):
    """أحدثُ خبرِ سلكٍ في النافذة ⟵ «العنوان — المصدر — الوقت» · أو 8-K · أو None."""
    w = (cat_detail or {}).get("wire_item")
    if w:
        return f"{w.get('title') or 'بيان صحفي'} — {w.get('wire')} — {w.get('time_ny')} نيويورك"
    s = (cat_detail or {}).get("sec_item")
    if s:
        items = f" (بنود {s['items']})" if s.get("items") else ""
        return f"إيداع 8-K{items} — SEC — {s.get('time_ny')} نيويورك"
    return None


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def build_message(row):
    """كرتُ التنبيه (شكلُ «هنا الدخول» · أسطرٌ قصيرة · بلا علامات مقارنة) — `send_telegram` يُلحق ختمَ الإصدار 🧾."""
    sym, arm = row["sym"], row["arm"]
    head = "🟠 <b>زخم الفيواب</b>" + (f" · إعادة اختبار #{row['n']}" if arm == "D" else " · كسر وثبات")
    rv = row.get("rvol")
    rv_s = "؟" if rv is None else ("∞" if rv == float("inf") else f"{rv:.1f}×")
    ema = row.get("ema9")
    ema_s = "؟" if ema is None else ("فوقه" if row["px"] > ema else "تحته")
    lines = [
        f"{head} · <b>${_esc(sym)}</b> · ${row['px']:.2f} · ‏{_pct(row.get('chg'))} يومه",
        f"RVOL {rv_s} · فيواب ${row['vwap']:.2f} (فوقه {row.get('above', 0)} شموع 5د) · EMA9 {ema_s}",
        f"📰 {_esc(row.get('news') or 'خبرٌ مؤكَّد في النافذة')}",
    ]
    if row.get("tags"):
        lines.append("🏷️ " + " · ".join(row["tags"]))
    ps = str(row.get("prev_src") or "")
    if ps.startswith("last_close "):
        lines.append(f"📎 التغيّرُ عن آخر إغلاق {ps.split(' ', 1)[1]} (لم يتداول بعده)")
    lines += [
        f"🕐 أُغلقت شمعةُ الحدث {_hm(row['e'])} نيويورك",
        "⛔ وقف مقترح: إغلاق شمعة 5د تحت الفيواب",
        "🎯 الجني (نايف): كل 7-10% ربح بيع جزء وارفع وقفك · وأوّل ما يرتفع عن دخولك ارفع وقفك لدخولك",
        f"⚠️ قيد الإثبات الأمامي — الأداة تنبّه ولا تدير صفقة · {WIRE_LIMIT_NOTE}",
    ]
    return "\n".join(("‏" + ln) for ln in lines)


def ledger_row(day, sym, a, detected_ts, sent, reason, mode, sha, news):
    """صفُّ تنبيهٍ إلحاقيّ (مفتاحُه للاتّحاد في `git_save`)."""
    ets = V3.ny_ts(day, a["e"])
    return {"v": 1, "kind": "alert", "key": alert_key(day, sym, a["arm"], a["n"]), "date": day, "sym": sym, "arm": a["arm"],
            "n": a["n"], "event_end_ny": _hm(a["e"]), "event_end_mod": a["e"], "event_ts": ets,
            "detected_ts": round(detected_ts, 1), "latency_s": round(detected_ts - ets, 1), "sent": sent, "reason": reason,
            "px": round(a["px"], 4), "vwap": round(a["vwap"], 4), "chg": None if a["chg"] is None else round(a["chg"], 4),
            "rvol": None if a["rvol"] is None else (None if a["rvol"] == float("inf") else round(a["rvol"], 2)),
            "rvol_inf": a["rvol"] == float("inf"), "cum_dollar": round(a["cum_dollar"]), "candle": a["kind"],
            "above": a.get("above"), "ema9": None if a.get("ema9") is None else round(a["ema9"], 4),
            "news": news, "mode": mode, "sha": sha, "tags": list(a.get("tags") or []), "prev_src": a.get("prev_src"),
            "sic": a.get("sic"), "ldef": a.get("ldef")}


def harvest(bars, op, cl, alert_mod, alert_px):
    """حصادُ ما بعد الإغلاق (عدٌّ لا حكم · أمرُ المالك ④): أعلى سعرٍ بعد التنبيه ووقتُه · أوّلُ إغلاق 5د تحت الفيواب ووقتُه وسعرُه ·
    العائدُ حتى ذلك الخروج (إغلاقُ تلك الشمعة) · والعائدُ حتى إغلاق الجلسة. VWAP من الافتتاح كالتنبيه."""
    b5, _b15, bb = complete_buckets(bars, op, cl, cl)
    after = [b for b in bb if b[0] >= alert_mod]
    hi = max(after, key=lambda b: b[2]) if after else None
    ex = next((b for b in b5 if b["s"] >= alert_mod and b["vwap"] is not None and b["c"] < b["vwap"]), None)
    close_px = bb[-1][4] if bb else None
    r = lambda p: None if (p is None or not alert_px) else round(p / alert_px - 1.0, 4)   # noqa: E731
    return {"max_high": None if hi is None else hi[2], "max_high_ny": None if hi is None else _hm(hi[0]),
            "max_gain": None if hi is None else r(hi[2]),
            "exit_ny": None if ex is None else _hm(ex["e"]), "exit_px": None if ex is None else ex["c"],
            "ret_exit": None if ex is None else r(ex["c"]), "close_px": close_px, "ret_close": r(close_px)}


def prefilter(day_hl, prev_adj_of, types):
    """مرشِّحٌ **أعمّ** من الشروط (لا يُسقط حدثًا ممكنًا): أعلى اليوم حتى الآن ≥ 1.2 × إغلاق الأمس المسوّى (شرطٌ لازمٌ لـ① على أيّ إغلاق 5د) ·
    وأدنى اليوم دون PX_MAX · وأعلاه PX_MIN فأكثر · والنوعُ ليس مستبعَدًا (المجهولُ يبقى ليُسأل عنه) ⟵ مجموعةُ الرموز."""
    out = set()
    for sym, (h, low) in day_hl.items():
        if h is None or low is None or not (low < PX_MAX and h >= PX_MIN):
            continue                                                    # السعرُ والنوعُ أوّلًا: إغلاقُ الموقوف يُجلب لما يلزم وحدَه
        t = types.get(sym)
        if t is not None and t not in TYPES_OK:
            continue
        pa = prev_adj_of(sym)
        if pa and V4.ge(h / pa - 1.0, CHG_MIN):
            out.add(sym)
    return out


def snapshot_hl(tickers):
    """لقطةُ السوق ⟵ ({رمز: (أعلى، أدنى)}، عدّاداتُ الحقول). الأعلى = أكبرُ الموجب من شمعة اليوم · شمعة الدقيقة الأخيرة · آخر صفقة ·
    والأدنى أصغرُه — لأنّ شمعةَ اليوم **فارغةٌ قبل الافتتاح** (مقيس: probe ‏`40858591617` 06:34 نيويورك ⟵ صفرُ رمزٍ بشمعة يوم) ·
    والمرشِّحُ يتراكم عبر الحلقات فرمزٌ بلغ ‏+20% في أيّ فحصٍ يبقى (`mode_live`)."""
    out, diag = {}, {"tickers": 0, "day": 0, "min": 0, "last": 0}
    for t in tickers or ():
        diag["tickers"] += 1
        sym = str(t.get("ticker") or "").upper()
        vals = []
        for key, hk, lk in (("day", "h", "l"), ("min", "h", "l")):
            b = t.get(key) or {}
            try:
                h, lo = float(b.get(hk) or 0), float(b.get(lk) or 0)
            except (TypeError, ValueError):
                h = lo = 0.0
            if h > 0:
                diag[key] += 1
                vals.append((h, lo if lo > 0 else h))
        lt = t.get("lastTrade") or {}
        try:
            p = float(lt.get("p") or 0)
        except (TypeError, ValueError):
            p = 0.0
        if p > 0:
            diag["last"] += 1
            vals.append((p, p))
        if sym and vals:
            out[sym] = (max(v[0] for v in vals), min(v[1] for v in vals))
    return out, diag


def pre_open_target(now_utc, MC, lead=PRE_OPEN_LEAD_MIN, cap=PRE_OPEN_CAP_MIN):
    """(الجلسةُ المقصودة، دقائقُ النوم) لجوب الانتظار — جلسةُ يوم نيويورك كما كانت، **إلّا بعد 20:00 نيويورك** (نهايةُ الأفتر) فجلسةُ الغد:
    كرونُ 02:xx UTC (‏22:xx نيويورك من أمس) ينام لجلسة يومه بدل أن يخرج بلا عمل — وبه لا يبدأ مقطعُ الافتتاح قبل الجرس بساعاتٍ
    فيستنفد ميزانيّتَه نائمًا حين يعبر الجوبان منتصفَ ليل نيويورك · والاحتياطُ المعلَّق بعد الإغلاق (‏16:xx) بلا عملٍ كما كان ·
    والغدُ غيرُ جلسة ⟵ صفر (لا قفزَ فوق العطلة) · فاشلٌ-آمن ⟵ (None، 0)."""
    try:
        ny = now_utc.astimezone(NY)
        day = (ny.date() + dt.timedelta(1 if ny.hour * 60 + ny.minute >= PRE_OPEN_NEXT_FROM_NY_MIN else 0)).isoformat()
        if not V3.is_session(day, MC.session_info):
            return day, 0
        op = dt.datetime.fromtimestamp(V3.ny_ts(day, MC.session_info(day)["open_ny_min"]), tz=dt.timezone.utc)
        return day, pre_open_sleep_min(op, now_utc, lead, cap)
    except Exception:                                                    # noqa: BLE001
        return None, 0


def pre_open_sleep_min(open_utc, now_utc, lead=PRE_OPEN_LEAD_MIN, cap=PRE_OPEN_CAP_MIN):
    """دقائقُ نومِ جوب الانتظار: الجرسُ ناقصَ lead ناقصَ الآن مقصوصًا إلى [0، cap] — وصفرٌ عند أيّ عطل (فاشلٌ-آمن)."""
    try:
        gap = (open_utc - dt.timedelta(minutes=lead) - now_utc).total_seconds() / 60.0
        return 0 if gap <= 0 else int(min(cap, int(gap)))
    except Exception:                                                    # noqa: BLE001
        return 0


# ── الشبكة (رنر فقط · كلُّ نداءٍ فاشلٌ-آمن ⟵ None) ──────────────────────────────────────────────────────────
class Net:
    """منافذُ Polygon وSEC — تُحقَن بديلًا في السويّة. `calls`/`fails` تُطبع في كلّ خاتمة."""

    def __init__(self, key, ua):
        self.key, self.ua, self.calls, self.fails = key, ua, 0, 0

    def _count(self, j):
        self.calls += 1
        self.fails += int(j is None)
        return j

    def poly(self, path, params=None):
        return self._count(V3._poly(path, self.key, params))

    def poly_url(self, url):
        return self._count(V3._get_url(url, self.key))

    def paged(self, path, params, cap=100):
        rows, ok = V4._paged_all(self.key, path, params, cap=cap)
        self.calls += 1
        self.fails += int(not ok)
        return rows, ok

    def sec(self, url):
        return self._count(V3._sec_get(url, self.ua, True))

    def minutes(self, sym, d_from, d_to):
        from urllib.parse import quote
        j = self.poly(f"/v2/aggs/ticker/{quote(sym)}/range/1/minute/{d_from}/{d_to}",
                      {"adjusted": "false", "sort": "asc", "limit": 50000})
        if j is None:
            return None
        res = list(j.get("results") or [])
        nxt, pages = j.get("next_url"), 0
        while nxt and pages < 10:
            k = self.poly_url(nxt)
            if k is None:
                return None
            res.extend(k.get("results") or [])
            nxt, pages = k.get("next_url"), pages + 1
        return bars_by_day(res)

    def news(self, sym, a_iso, b_iso):
        rows, ok = self.paged("/v2/reference/news", {"ticker": sym, "published_utc.gte": a_iso, "published_utc.lte": b_iso,
                                                     "order": "asc", "sort": "published_utc", "limit": 1000}, cap=10)
        if not ok:
            return None
        out = []
        for it in rows:
            pub = it.get("publisher") or {}
            out.append({"id": it.get("id"), "published_utc": it.get("published_utc"), "tickers": it.get("tickers") or [],
                        "publisher": {"name": pub.get("name") if isinstance(pub, dict) else pub},
                        "author": it.get("author"), "article_url": it.get("article_url"), "title": it.get("title")})
        return out

    def snapshot(self):
        j = self.poly("/v2/snapshot/locale/us/markets/stocks/tickers")
        if j is None:
            return None
        out, self.snap_diag = snapshot_hl(j.get("tickers") or ())
        return out


class Day:
    """مرجعُ يومٍ واحد (يُجلب مرّةً) وذاكرتُه المؤقّتة لكلّ رمز — مشتركٌ بين `live` و`replay` و`trace`."""

    def __init__(self, net, day, MC, replay=False):
        self.net, self.day, self.replay = net, day, replay
        info = MC.session_info(day)
        self.op, self.cl = info["open_ny_min"], info["close_ny_min"]
        self.prev = V3._prev_session(day, MC)
        self.priors = V4._prev_sessions(day, V4.RVOL_WIN, MC)
        self.win_a = V3.ny_ts(self.prev, 16 * 60)                     # «مساء الأمس» = بعد 16:00 نيويورك للجلسة السابقة
        self.ok, self.why = True, []
        g = net.poly(f"/v2/aggs/grouped/locale/us/market/stocks/{self.prev}", {"adjusted": "false"})
        self.prev_close = {str(r.get("T") or "").upper(): r.get("c") for r in ((g or {}).get("results") or []) if r.get("T")}
        if not self.prev_close:
            self.ok = False
            self.why.append("إغلاقُ الجلسة السابقة")
        rows, oks = net.paged("/v3/reference/splits", {"execution_date.gte": self.priors[0], "execution_date.lte": day, "limit": 1000})
        self.splits = {}
        for r in rows:
            try:
                self.splits.setdefault(str(r.get("ticker") or "").upper(), []).append(
                    (str(r["execution_date"]), float(r["split_from"]), float(r["split_to"])))
            except (KeyError, TypeError, ValueError):
                continue
        if not oks:
            self.ok = False
            self.why.append("التقسيمات")
        trows, okt = net.paged("/v3/reference/tickers", {"market": "stocks", "date": day, "active": "true", "limit": 1000})
        self.types = {str(r.get("ticker") or "").upper(): str(r.get("type") or "") for r in trows if r.get("ticker")}
        if not okt:
            self.ok = False
            self.why.append("مرجعُ الأنواع")
        cmap = net.sec("https://www.sec.gov/files/company_tickers.json") or {}
        self.cik = {str(v.get("ticker", "")).upper(): int(v["cik_str"]) for v in cmap.values()
                    if isinstance(v, dict) and v.get("cik_str")}
        if not self.cik:
            self.ok = False
            self.why.append("خريطةُ CIK")
        from edgar2_probe import parse_acc, to_ny
        self.acc_ts = V3.make_acc_ts(parse_acc, to_ny)
        self._prior_cache, self._cat_cache, self._detail = {}, {}, {}
        self._prev_cache, self.sic_of = {}, {}

    def prev_ref(self, sym):
        """(إغلاقُ الأمس المسوّى، مصدرُه) — من مجمَّعة الجلسة السابقة («grouped») · **وإن غاب** (سهمٌ لم يتداول أمس: موقوفٌ ثمّ عائد)
        فآخرُ إغلاقٍ قبل اليوم في `LAST_CLOSE_LOOKBACK_D` يومًا مسوًّى بكلّ تقسيمٍ نُفِّذ بعده حتى اليوم («last_close يوم») — أمرُ المالك
        2026-10-29 «اعتمد آخر إغلاق للموقوف» · ولا إغلاقَ في النافذة (اكتتابٌ · تغييرُ رمز) ⟵ (None، None) = ① مجهول كما كان ·
        وتعذّرُ الشبكة لا يُخبَّأ (يُعاد في الحلقة التالية)."""
        if sym in self._prev_cache:
            return self._prev_cache[sym]
        pv = self.prev_close.get(sym)
        if pv:
            out = (pv * V4.price_factor(self.splits.get(sym, ()), self.day), "grouped")
        else:
            out = self._last_close(sym)
            if out is None:
                return (None, None)
        self._prev_cache[sym] = out
        return out

    def _last_close(self, sym):
        lo = (dt.date.fromisoformat(self.day) - dt.timedelta(LAST_CLOSE_LOOKBACK_D)).isoformat()
        j = self.net.poly(f"/v2/aggs/ticker/{sym}/range/1/day/{lo}/{self.prev}", {"adjusted": "false", "sort": "asc", "limit": 200})
        if j is None:
            return None
        rows = []
        for r in j.get("results") or ():
            try:
                d0 = dt.datetime.fromtimestamp(int(r["t"]) / 1000.0, tz=NY).date().isoformat()
                if d0 < self.day and r.get("c"):
                    rows.append((d0, float(r["c"])))
            except (KeyError, TypeError, ValueError):
                continue
        if not rows:
            return (None, None)
        d0, c0 = rows[-1]
        sp, ok = self.net.paged("/v3/reference/splits", {"ticker": sym, "execution_date.gt": d0, "execution_date.lte": self.day,
                                                         "limit": 100})
        if not ok:
            return None
        f = 1.0
        for r in sp:
            try:
                ex = str(r["execution_date"])
                if str(r.get("ticker") or sym).upper() == sym and d0 < ex <= self.day:
                    f *= float(r["split_from"]) / float(r["split_to"])
            except (KeyError, TypeError, ValueError, ZeroDivisionError):
                return None
        return (c0 * f, f"last_close {d0}")

    def prev_adj(self, sym):
        return self.prev_ref(sym)[0]

    def prev_adj_pf(self, sym):
        """للمرشِّح: إغلاقُ المجمَّعة لكلّ رمز · وآخرُ إغلاقِ الموقوف **لنوعٍ مقبولٍ معروف وحدَه** — المجهولُ النوعِ الغائبُ عن المجمَّعة كان
        خارجَ المرشِّح قبل الأمر ويبقى (مقيس: replay ‏`40876317066`/T نداءاتٌ 2,784 مقابل 761 من أجل رموزٍ مجهولة النوع لم يُنتج منها تنبيه)."""
        if sym in self.prev_close or self.types.get(sym) in TYPES_OK:
            return self.prev_adj(sym)
        return None

    def type_status(self, sym):
        if sym not in self.types and sym not in self._detail:
            j = self.net.poly(f"/v3/reference/tickers/{sym}", {"date": self.day})
            self._detail[sym] = ((j or {}).get("results") or {}).get("type")
        t = self.types.get(sym) or self._detail.get(sym)
        return "unknown" if not t else ("ok" if t in TYPES_OK else "excluded")

    def priors_of(self, sym):
        """[(يوم، منحنى أو None، عاملُ الحجم)] لعشرين جلسة — نداءٌ واحدٌ للرمز في اليوم · None إن تعذّر (② مجهول ⟵ لا تنبيه)."""
        if sym not in self._prior_cache:
            by = self.net.minutes(sym, self.priors[0], self.priors[-1])
            if by is None:
                self._prior_cache[sym] = None
            else:
                sp = self.splits.get(sym, ())
                self._prior_cache[sym] = [(d, V4.cum_curve(by[d]) if by.get(d) else None, V4.vol_factor(sp, d, self.day))
                                          for d in self.priors]
        return self._prior_cache[sym]

    def sec_of(self, sym):
        """(SIC، صفوفُ 8-K/6-K [(ثانية، نموذج، بنود)]، معلوم؟) — بلا CIK ⟵ ("", []، True) كالملحق 2 §③ (الأخبارُ وحدَها)."""
        cik = self.cik.get(sym)
        if cik is None:
            return "", [], True
        j = self.net.sec(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
        if j is None:
            return "", [], False
        rec = (j.get("filings") or {}).get("recent") or {}
        known = V3.sec_depth_ok(rec, bool((j.get("filings") or {}).get("files")), self.prev)
        return str(j.get("sic") or ""), V3.sec_index(rec, V4.SEC_FETCH, self.acc_ts), known

    def catalyst(self, sym, upto_ts):
        """⟵ (cat_of، تفصيلٌ للرسالة، SPAC؟) — أخبارُ الرمز حتى لحظة الفحص و`submissions` (تُجلب عند الحاجة · مرّةً لكلّ فحص).
        **وفي الإعادة** مرّةً للرمز في اليوم حتى 20:00 — والنافذةُ في `catalyst4` تقصّها عند نهاية كلّ حدثٍ (لا نظرَ للأمام)."""
        if self.replay:
            if sym in self._cat_cache:
                return self._cat_cache[sym]
            upto_ts = V3.ny_ts(self.day, V3.EXT_END)
        a_iso = dt.datetime.fromtimestamp(self.win_a, tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        b_iso = dt.datetime.fromtimestamp(upto_ts, tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        items = self.net.news(sym, a_iso, b_iso)
        sic, rows, known = self.sec_of(sym)
        self.sic_of[sym] = sic
        wix = V4.wire_index(items or [])[0]
        s8k = [r[0] for r in rows if r[1] == "8-K"]
        s6k = [r[0] for r in rows if r[1] == "6-K"]
        if items is None and not s8k:
            known = False                                              # الأخبارُ تعذّرت ولا 8-K ⟵ ④ مجهول لا «لا»

        def cat_of(e_mod):
            return V4.catalyst4(sym, self.win_a, V3.ny_ts(self.day, e_mod), wix, s8k, s6k, known)

        def detail(e_mod):
            b = V3.ny_ts(self.day, e_mod)
            wi = None
            for it in sorted(items or [], key=lambda x: str(x.get("published_utc") or "")):
                ts = V3._iso_ts(it.get("published_utc"))
                w = V4.wire_of(it)
                if w and ts is not None and self.win_a <= ts <= b and sym in {str(t).upper() for t in it.get("tickers") or []}:
                    wi = {"title": it.get("title"), "wire": w[0], "published_utc": it.get("published_utc"),
                          "time_ny": dt.datetime.fromtimestamp(ts, tz=NY).strftime("%m-%d %H:%M")}
            si, acq = None, False
            for ts, f, its in rows:
                if f == "8-K" and self.win_a <= ts <= b:
                    si = {"items": its, "time_ny": dt.datetime.fromtimestamp(ts, tz=NY).strftime("%m-%d %H:%M")}
                    acq = acq or "1.01" in [x.strip() for x in str(its or "").split(",")]
            return {"wire_item": wi, "sec_item": si, "acq_101": acq}
        out = (cat_of, detail, excl_label(sic))
        if self.replay:
            self._cat_cache[sym] = out
        return out


def excl_label(sic):
    """⑤ بكود SIC من `submissions` نفسِه: 6770 ⟵ «SPAC» (الملحق 3) · `FUND_SIC` ⟵ «صندوق (SIC …)» (أمرُ المالك 2026-10-29) · وإلّا None."""
    sic = str(sic or "")
    if sic == SPAC_SIC:
        return "SPAC"
    return f"صندوق (SIC {sic})" if sic in FUND_SIC else None


def scan_symbol(D, sym, bars_today, upto, detected_ts, full_info=False, prev_override=None, ldef=None):
    """فحصُ رمزٍ حتى `upto` ⟵ نتيجةُ `evaluate` وكلُّ تنبيهٍ فيها بخبره (`news` نصًّا و`news_detail`). أيّامُ ② والخبرُ وSEC
    **تُجلب عند الحاجة وحدَها** (حين تكتمل الشروطُ الأرخص قبلها) · وSPAC يُعرف من `submissions` نفسِه فيُعاد التقييمُ به."""
    b5, _b15, _ = complete_buckets(bars_today, D.op, D.cl, upto)
    if len(b5) < 4:
        return {"events": [], "alerts": []}
    state = {}

    def priors_fn():
        p = D.priors_of(sym)
        return p if p is not None else [(d, None, 1.0) for d in D.priors]   # ② مجهول ⟵ لا يكتمل A

    def cat_of(e):
        if "fn" not in state:
            state["fn"], state["detail"], state["spac"] = D.catalyst(sym, detected_ts)
        return state["fn"](e)
    ts = D.type_status(sym)
    ldef = resolve_ldef(ldef)
    pa, psrc = D.prev_ref(sym) if prev_override is None else (prev_override, "override")   # التجاوزُ لوضع trace وحدَه (`VWL14`)
    res = evaluate(bars_today, D.op, D.cl, upto, pa, priors_fn, cat_of, ts, False, full_info=full_info, ldef=ldef)
    if state.get("spac"):
        res = evaluate(bars_today, D.op, D.cl, upto, pa, priors_fn, state["fn"], ts, state["spac"], full_info=full_info, ldef=ldef)
    for a in res["alerts"]:
        a["news_detail"] = state["detail"](a["e"])
        a["news"] = news_brief(a["news_detail"])
        a["tags"] = alert_tags(a, b5, a["news_detail"])
        a["prev_src"], a["sic"], a["ldef"] = psrc, D.sic_of.get(sym), ldef
    return res


def read_ledger(path=LEDGER):
    rows = []
    try:
        with open(path, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    try:
                        rows.append(json.loads(ln))
                    except ValueError:
                        continue
    except FileNotFoundError:
        pass
    return rows


def append_ledger(row, path):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _sha():
    return (os.environ.get("GITHUB_SHA") or "").strip()[:7] or "local"


def _today_ny(now=None):
    return (now or dt.datetime.now(tz=NY)).astimezone(NY).date().isoformat()


def emit_json(out):
    """مُخرَجُ الأوضاع اليدويّة: سطرُ `VWLIVE_JSON` في السجلّ · وملفٌّ إن ضُبط `VWL_OUT` (يدفعه الـworkflow إلى فرعه — لا main)."""
    txt = json.dumps(out, ensure_ascii=False, sort_keys=True)
    log("VWLIVE_JSON " + txt)
    path = os.environ.get("VWL_OUT", "").strip()
    if path:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(out, ensure_ascii=False, sort_keys=True, indent=1) + "\n")


def _boundary_mods(op, cl, start_mod, end_mod):
    """حدودُ الشموع (كلَّ 5 دقائق من الافتتاح) في (start_mod، end_mod] — لحظاتُ الفحص."""
    return [m for m in range(op + 5, min(cl, end_mod) + 1, 5) if m > start_mod]


# ── الأوضاع ──────────────────────────────────────────────────────────────────────────────────────────────
def mode_replay(net, MC, end_day, ndays):
    """إعادةُ تشغيلٍ صامتة: لكلّ جلسةٍ مكتملة — المرشِّحُ الأعمّ من شمعة اليوم (المجمَّعة · لا نظرَ للأمام في الشروط) ثمّ محاكاةُ
    الحلقة الحيّة عند كلّ حدّ 5 دقائق (`scan_symbol` حتى الحدّ وحده) ⟵ كلُّ تنبيهٍ كان سيُرسَل بطابعه. بلا تلغرام · بلا سجلّ."""
    days, d = [], dt.date.fromisoformat(end_day)
    while len(days) < ndays:
        if V3.is_session(d.isoformat(), MC.session_info):
            days.append(d.isoformat())
        d -= dt.timedelta(1)
    days.reverse()
    out = {"mode": "replay", "ldef": resolve_ldef(), "days": days, "d_min": D_MIN_LIVE, "px": [PX_MIN, PX_MAX], "chg_min": CHG_MIN, "rvol_min": RVOL_MIN,
           "fresh_max_s": FRESH_MAX_S, "d_max": D_MAX_PER_DAY, "per_day": {}, "alerts": [], "near": []}
    bad = False
    for day in days:
        D = Day(net, day, MC, replay=True)
        g = net.poly(f"/v2/aggs/grouped/locale/us/market/stocks/{day}", {"adjusted": "false"})
        hl = {str(r.get("T") or "").upper(): (r.get("h"), r.get("l")) for r in ((g or {}).get("results") or []) if r.get("T")}
        if not D.ok or not hl:
            bad = True
            out["per_day"][day] = {"ok": False, "why": D.why + ([] if hl else ["شمعةُ اليوم المجمَّعة"])}
            log(f"⛔ {day}: مرجعٌ ناقص {out['per_day'][day]['why']}")
            continue
        cands = sorted(prefilter(hl, D.prev_adj_pf, D.types))
        no_prev = sorted(s for s, (h, low) in hl.items() if s not in D.prev_close and h is not None and low is not None
                         and low < PX_MAX and h >= PX_MIN and D.types.get(s) in TYPES_OK)   # وصفٌ: عاديٌّ بلا إغلاق أمسٍ في المجمَّعة
        lc_used = sorted(s for s in no_prev if str(D.prev_ref(s)[1] or "").startswith("last_close "))   # مُخبَّأٌ من المرشِّح
        bounds = _boundary_mods(D.op, D.cl, D.op, D.cl)
        miss_bars = n_ev = n_full = n_sym_ev = mismatch = 0
        first_fail = {}
        for sym in cands:
            by = net.minutes(sym, day, day)
            bars = (by or {}).get(day)
            if by is None:
                miss_bars += 1
                continue
            if not bars:
                continue
            got = {}
            for B in bounds:
                det = V3.ny_ts(day, B) + LOOP_OFFSET_S
                for a in scan_symbol(D, sym, bars, B, det)["alerts"]:
                    k = (a["arm"], a["n"])
                    if k not in got:
                        got[k] = ledger_row(day, sym, a, det, is_fresh(V3.ny_ts(day, a["e"]), det), None, "replay", _sha(),
                                            a.get("news"))
                        got[k]["news_detail"] = a.get("news_detail")
            fin = scan_symbol(D, sym, bars, D.cl, V3.ny_ts(day, D.cl) + LOOP_OFFSET_S, full_info=True)
            if {(a["arm"], a["n"]) for a in fin["alerts"]} != set(got):
                mismatch += 1                                           # الحلقةُ والتقييمُ الكامل يجب أن يتّفقا بالبناء
            out["alerts"].extend(got[k] for k in sorted(got, key=lambda x: (x[0] != "A", x[1])))
            n_ev += len(fin["events"])
            n_sym_ev += int(bool(fin["events"]))
            n_full += sum(1 for e in fin["events"] if e["full"])
            for e in fin["events"]:
                if e["why"]:
                    first_fail[e["why"][0]] = first_fail.get(e["why"][0], 0) + 1
                if len(e["why"]) == 1:
                    out["near"].append({"date": day, "sym": sym, "event_end_ny": _hm(e["e"]), "missing": e["why"][0],
                                        "px": round(e["px"], 4), "chg": None if e["chg"] is None else round(e["chg"], 4),
                                        "rvol": None if e["rvol"] in (None, float("inf")) else round(e["rvol"], 2),
                                        "cum_dollar": round(e["cum_dollar"])})
        na = sum(1 for r in out["alerts"] if r["date"] == day)
        out["per_day"][day] = {"ok": True, "candidates": len(cands), "bars_failed": miss_bars, "symbols_with_breaks": n_sym_ev,
                               "a_events": n_ev, "a_full": n_full, "alerts": na, "first_fail": first_fail, "loop_vs_full_mismatch": mismatch,
                               "no_prev_close": len(no_prev), "last_close_used": len(lc_used), "last_close_syms": lc_used[:40],
                               "no_prev_close_syms": no_prev[:40]}
        log(f"📅 {day}: مرشّحون {len(cands)} · شموعٌ تعذّرت {miss_bars} · رموزٌ بكسر {n_sym_ev} · أحداثُ كسر {n_ev} · كاملة {n_full} · "
            f"تنبيهات {na} · أوّلُ شرطٍ سقط {first_fail} · خلافُ الحلقة {mismatch}")
        bad = bad or miss_bars > 0 or mismatch > 0
    out["calls"], out["fails"] = net.calls, net.fails
    emit_json(out)
    for r in out["alerts"]:
        log(f"🟠 {r['date']} {r['event_end_ny']} ${r['sym']} · {r['arm']}{'#' + str(r['n']) if r['arm'] == 'D' else ''} · "
            f"${r['px']} · {_pct(r['chg'])} · RVOL {r['rvol']} · 📰 {r['news']}")
    return 4 if bad else 0


def mode_trace(net, MC, day, sym):
    """سهمٌ ويوم: شموعُ 5 دقائق النظاميّة بـVWAP · كلُّ لمسةٍ (قاعٌ حتى 1.01 × VWAP) · كلُّ كسرٍ A بشروطه وسببِ سقوطه ·
    والتنبيهاتُ التي كانت ستُرسَل (محاكاةُ الحلقة) · ثمّ وصفُ الممتدّة (VWAP من 04:00) — خارج نطاق الأداة بتعريف نايف."""
    D = Day(net, day, MC, replay=True)
    by = net.minutes(sym, day, day)
    bars = (by or {}).get(day) or []
    out = {"mode": "trace", "ldef": resolve_ldef(), "date": day, "sym": sym, "ref_ok": D.ok, "ref_why": D.why, "bars": len(bars),
           "prev_adj": D.prev_adj(sym), "prev_src": D.prev_ref(sym)[1], "type": D.type_status(sym), "candles": [], "touches": [], "events": [], "alerts": [], "ext": {}}
    if not D.prev_close.get(sym):                                      # تشخيص: لماذا غاب إغلاقُ الأمس عن المجمَّعة؟
        lo = (dt.date.fromisoformat(D.prev) - dt.timedelta(10)).isoformat()
        j = net.poly(f"/v2/aggs/ticker/{sym}/range/1/day/{lo}/{day}", {"adjusted": "false", "sort": "asc", "limit": 50})
        dref = net.poly(f"/v3/reference/tickers/{sym}", {"date": D.prev})
        out["prev_diag"] = {"prev_session": D.prev, "grouped_symbols": len(D.prev_close),
                            "daily": [{"d": dt.datetime.fromtimestamp(r["t"] / 1000, tz=NY).date().isoformat(), "c": r.get("c"),
                                       "v": r.get("v")} for r in ((j or {}).get("results") or []) if r.get("t")],
                            "ref_prev": {k: ((dref or {}).get("results") or {}).get(k) for k in ("ticker", "type", "active", "list_date",
                                                                                               "primary_exchange", "delisted_utc")},
                            "splits": D.splits.get(sym, [])}
        prior = [r for r in out["prev_diag"]["daily"] if r["d"] < day and r.get("c")]
        if prior:
            lc = prior[-1]
            f = 1.0
            for ex, sf, stt in D.splits.get(sym, ()):
                if lc["d"] < ex <= day and sf and stt:
                    f *= sf / stt
            out["last_close"] = {"d": lc["d"], "c": lc["c"], "split_factor": f, "adj": lc["c"] * f}
    if not bars:
        emit_json(out)
        return 4
    b5, _b15, _bb = complete_buckets(bars, D.op, D.cl, D.cl)
    for b in b5:
        out["candles"].append({"s": _hm(b["s"]), "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"],
                               "vwap": None if b["vwap"] is None else round(b["vwap"], 4), "dv": round(b["dv"])})
        if b["vwap"] is not None and b["l"] <= V3.RETEST_TOL * b["vwap"]:
            out["touches"].append({"s": _hm(b["s"]), "low": b["l"], "vwap": round(b["vwap"], 4), "close_above": b["c"] > b["vwap"]})
    seen = set()
    for B in _boundary_mods(D.op, D.cl, D.op, D.cl):
        det = V3.ny_ts(day, B) + LOOP_OFFSET_S
        res = scan_symbol(D, sym, bars, B, det)
        for a in res["alerts"]:
            if (a["arm"], a["n"]) not in seen:
                seen.add((a["arm"], a["n"]))
                out["alerts"].append(ledger_row(day, sym, a, det, True, None, "trace", _sha(), a.get("news")))
    lc = (out.get("last_close") or {}).get("adj")
    if lc:                                                              # ماذا لو كان «إغلاقُ الأمس» آخرَ إغلاقٍ قبل اليوم؟ — وصفٌ لا قاعدة
        wf = {"prev_used": lc, "alerts": [], "events": []}
        seen_w = set()
        for B in _boundary_mods(D.op, D.cl, D.op, D.cl):
            det = V3.ny_ts(day, B) + LOOP_OFFSET_S
            for a in scan_symbol(D, sym, bars, B, det, prev_override=lc)["alerts"]:
                if (a["arm"], a["n"]) not in seen_w:
                    seen_w.add((a["arm"], a["n"]))
                    wf["alerts"].append({"arm": a["arm"], "n": a["n"], "end_ny": _hm(a["e"]), "px": a["px"], "chg": round(a["chg"], 4)})
        for e in scan_symbol(D, sym, bars, D.cl, V3.ny_ts(day, D.cl) + LOOP_OFFSET_S, full_info=True, prev_override=lc)["events"]:
            wf["events"].append({"end_ny": _hm(e["e"]), "kind": e["kind"], "chg": round(e["chg"], 4), "why": e["why"]})
        out["whatif_last_close"] = wf
    b5f, b15f, _ = complete_buckets(bars, D.op, D.cl, D.cl)
    for tch in out["touches"]:                                          # كلُّ لمسة: الثباتُ الذي يليها بتعريف D (بـL وبدونه) — وصف
        sm = int(tch["s"][:2]) * 60 + int(tch["s"][3:])
        rev = {}
        for tag, nl in (("with_L", True), ("without_L", False)):
            rt = retest_hold(b5f, b15f, sm, resolve_ldef()) if nl else V3.retest_signal(b5f, b15f, sm, need_liq=False)
            if rt is None:
                rev[tag] = None
                continue
            rb = b5f[rt[2]] if rt[1] == "5x3" else b15f[rt[2]]
            rev[tag] = {"end_ny": _hm(rt[0]), "kind": rt[1], "px": rb["c"],
                        "chg_last_close": None if not lc else round(rb["c"] / lc - 1.0, 4)}
        tch["d_hold"] = rev
    last = scan_symbol(D, sym, bars, D.cl, V3.ny_ts(day, D.cl) + LOOP_OFFSET_S, full_info=True)
    for e in last["events"]:
        out["events"].append({"end_ny": _hm(e["e"]), "kind": e["kind"], "px": e["px"], "vwap": round(e["vwap"], 4),
                              "chg": None if e["chg"] is None else round(e["chg"], 4), "L": e["liq"],
                              "rvol": None if e["rvol"] in (None, float("inf")) else round(e["rvol"], 2),
                              "cum_dollar": round(e["cum_dollar"]), "why": e["why"], "full": e["full"],
                              "C": None if e["cat"] is None else e["cat"].get("C")})
    ext = [b for b in bars if V3.EXT_START <= b[0] < V3.EXT_END]
    vw = V3.vwap_series(ext)
    e5 = V3.bucketize(ext, vw, V3.EXT_START, 5, V3.EXT_END)
    out["ext"] = {"touches_outside_regular": [_hm(b["s"]) for b in e5 if b["vwap"] is not None and b["l"] <= V3.RETEST_TOL * b["vwap"]
                                              and not (D.op <= b["s"] < D.cl)],
                  "breaks_outside_regular": [_hm(ev[0]) for ev in V3.break_events(e5, V3.bucketize(ext, vw, V3.EXT_START, 15, V3.EXT_END),
                                                                                  skip=(D.op, D.cl))]}
    out["sic"] = D.sic_of.get(sym)
    out["excl"] = excl_label(out["sic"]) if out["sic"] is not None else None
    emit_json(out)
    log(f"🔎 {sym} {day}: شموع {len(bars)} دقيقة · لمساتُ الفيواب في النظاميّة {len(out['touches'])} · أحداثُ كسر {len(out['events'])} · "
        f"تنبيهاتٌ كانت ستُرسَل {len(out['alerts'])} · الممتدّة: لمسات {len(out['ext']['touches_outside_regular'])} وكسور "
        f"{len(out['ext']['breaks_outside_regular'])}")
    return 0


def mode_probe(net):
    """فحصُ المنافذ الحيّة قبل أيّ تفعيل: لقطةُ السوق (عددُ الرموز) · دقائقُ رمزٍ · أخبارُه · `submissions`."""
    snap = net.snapshot()
    log(f"🩺 اللقطة: {'تعذّرت' if snap is None else f'{len(snap)} رمزًا بسعر'} · الحقول {getattr(net, 'snap_diag', None)}")
    by = net.minutes("AAPL", _today_ny(), _today_ny())
    log(f"🩺 الدقائق (AAPL اليوم): {'تعذّرت' if by is None else sum(len(v) for v in by.values())}")
    now = dt.datetime.now(tz=dt.timezone.utc)
    items = net.news("AAPL", (now - dt.timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ"), now.strftime("%Y-%m-%dT%H:%M:%SZ"))
    log(f"🩺 الأخبار (AAPL يومان): {'تعذّرت' if items is None else len(items)}")
    j = net.sec("https://data.sec.gov/submissions/CIK0000320193.json")
    log(f"🩺 SEC submissions: {'تعذّر' if j is None else 'يعمل'} · نداءات {net.calls} · فشل {net.fails}")
    return 0 if (snap and by is not None and items is not None and j is not None) else 3


def mode_harvest(net, MC, path=LEDGER, now_fn=None):
    """حصادُ التنبيهات المُرسَلة بعد إغلاق جلستها — إلحاقيّ (صفُّ `harvest` بمفتاحه) · مرّةً لكلّ تنبيه · عدٌّ بلا حكم."""
    rows = read_ledger(path)
    done = {r.get("of") for r in rows if r.get("kind") == "harvest"}
    todo = [r for r in rows if r.get("kind") == "alert" and r.get("sent") and r.get("key") not in done]
    now_ny = dt.datetime.fromtimestamp((now_fn or time.time)(), tz=NY)
    added = 0
    for r in todo:
        info = MC.session_info(r["date"])
        cl = info.get("close_ny_min")
        if cl is None or (r["date"] == now_ny.date().isoformat() and now_ny.hour * 60 + now_ny.minute < cl + 5):
            continue                                                    # الجلسةُ لم تُغلق بعد
        by = net.minutes(r["sym"], r["date"], r["date"])
        bars = (by or {}).get(r["date"])
        if not bars:
            log(f"⚠️ حصاد {r['key']}: شموعٌ تعذّرت — يُعاد في التشغيلة التالية")
            continue
        h = harvest(bars, info["open_ny_min"], cl, r["event_end_mod"], r["px"])
        append_ledger({"v": 1, "kind": "harvest", "key": "H|" + r["key"], "of": r["key"], "date": r["date"], "sym": r["sym"],
                       "harvested_ts": round(now_ny.timestamp(), 1), **h}, path)
        added += 1
    log(f"🌾 الحصاد: {added} صفًّا جديدًا من {len(todo)} مستحقّ")
    return added


def mode_live(net, MC, send, segment, now_fn=None, sleep_fn=None, sender=None, saver=None, path=LEDGER):
    """الحلقةُ الحيّة: عند كلّ حدّ 5 دقائق (+ ثوانٍ) — لقطةُ السوق ⟵ المرشِّحُ الأعمّ ⟵ دقائقُ اليوم لكلّ مرشّح ⟵ `scan_symbol` ⟵
    تنبيهٌ جديدٌ طازج يُرسَل (إن `send`) ويُسجَّل · والمتأخّرُ أكثرَ من 10 دقائق يُسجَّل بلا إرسال · والدِّدوبُ من السجلّ.
    المقطع: open [الافتتاح، +195 د] · close [+195 د، الإغلاق] ثمّ الحصاد · single [الافتتاح، الإغلاق] ثمّ الحصاد."""
    now_fn = now_fn or (lambda: time.time())
    sleep_fn = sleep_fn or time.sleep
    day = _today_ny(dt.datetime.fromtimestamp(now_fn(), tz=NY))
    if not V3.is_session(day, MC.session_info):
        log(f"📴 {day} ليس جلسةَ تداول — لا عمل")
        return 0
    D = Day(net, day, MC)
    if not D.ok:
        log(f"⛔ مرجعُ اليوم ناقص: {D.why} — لا مسح (يُعلَن ولا يُكتَم)")
        return 2
    split = D.op + SEG_SPLIT_MIN
    lo, hi = {"open": (D.op, split), "close": (split, D.cl)}.get(segment, (D.op, D.cl))
    mr = int(os.environ.get("VWL_MAX_RUNTIME_MIN", "340") or 340)
    t_dead = now_fn() + mr * 60
    rows = read_ledger(path)
    used = used_keys(rows, day)
    cands, todays = set(), {}
    errors = {"snapshot": 0, "send": 0}
    sent_n = late_n = 0
    log(f"🟠 زخم الفيواب {day} · المقطع {segment} {_hm(lo)}-{_hm(hi)} نيويورك · الإرسال {'مفعَّل' if send else 'مطفأ (تجربة)'} · "
        f"مسجَّلٌ اليوم {len(used)}")
    for B in _boundary_mods(D.op, D.cl, lo, hi):
        t_check = V3.ny_ts(day, B) + LOOP_OFFSET_S
        if now_fn() > t_dead:
            log("⏱️ بلغ سقفَ التشغيل — يُكمل المقطعُ التالي")
            break
        if t_check < now_fn() - 300:
            continue                                                    # حدٌّ مضى (إقلاعٌ متأخّر) ⟵ الفحصُ الأوّل يلتقط ما فات بطابعه
        if t_check > now_fn():
            sleep_fn(t_check - now_fn())
        snap = net.snapshot()
        if snap is None:
            errors["snapshot"] += 1
            log(f"⚠️ {_hm(B)} اللقطة تعذّرت ({errors['snapshot']})")
        else:
            cands |= prefilter(snap, D.prev_adj_pf, D.types)
        for sym in sorted(cands):
            by = net.minutes(sym, day, day)
            if by is None:
                continue
            todays[sym] = by.get(day) or []
            det = now_fn()                                              # لحظةُ الاكتشاف لكلّ رمزٍ بعد جلب شموعه (لا يُقلَّل التأخّر)
            res = scan_symbol(D, sym, todays[sym], B, det)
            for a in res["alerts"]:
                k = alert_key(day, sym, a["arm"], a["n"])
                if k in used:
                    continue
                ets = V3.ny_ts(day, a["e"])
                fresh = is_fresh(ets, det)
                ok = False
                if fresh and send:
                    ok = bool((sender or _bot().send_telegram)(build_message(dict(a, sym=sym))))
                    errors["send"] += int(not ok)
                reason = None if (fresh and ok) else ("late" if not fresh else ("send_failed" if send else "dry"))
                row = ledger_row(day, sym, a, det, bool(fresh and ok), reason, "live", _sha(), a.get("news"))
                log(f"{'🟠 أُرسل' if row['sent'] else '📝 سُجّل (' + str(reason) + ')'} ${sym} {a['arm']}#{a['n']} عند {_hm(a['e'])} · "
                    f"تأخّر {row['latency_s']}ث")
                used.add(k)
                if send:
                    append_ledger(row, path)
                    (saver or _bot().git_save)([path])
                sent_n += int(row["sent"])
                late_n += int(reason == "late")
    if segment in ("close", "single") and send:
        sleep_fn(max(0.0, V3.ny_ts(day, D.cl) + 300 - now_fn()))
        if mode_harvest(net, MC, path, now_fn=now_fn):
            (saver or _bot().git_save)([path])
    log(f"🏁 انتهى المقطع {segment}: مرشّحون {len(cands)} · أُرسل {sent_n} · متأخّر {late_n} · نداءات {net.calls} · فشل {net.fails} · "
        f"أعطال {errors}")
    return 3 if (errors["send"] or errors["snapshot"] > 3) else 0


def _bot():
    import Super_stock as bot
    return bot


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--mode", default="live", choices=("live", "replay", "trace", "harvest", "probe"))
    p.add_argument("--days", type=int, default=5)
    p.add_argument("--end", default="")
    p.add_argument("--date", default="2026-10-26")
    p.add_argument("--sym", default="AZTR")
    p.add_argument("--segment", default=os.environ.get("VWL_SEGMENT", "single"), choices=("open", "close", "single"))
    p.add_argument("--pre-open-sleep", action="store_true")
    a = p.parse_args(argv)
    import market_calendar as MC
    if a.pre_open_sleep:
        day, m = pre_open_target(dt.datetime.now(tz=dt.timezone.utc), MC)
        print(f"PRE_OPEN_DAY={day}")
        print(f"PRE_OPEN_SLEEP_MIN={m}")
        return 0
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    ua = (os.environ.get("SEC_CONTACT") or "").strip()
    if not key:
        log("⛔ لا مفتاح Polygon — لا عمل (يُعلَن ولا يُكتَم)")
        return 2
    if not ua:
        log("⛔ SEC_CONTACT غيرُ مضبوط — ④ (8-K) مصدرٌ لازم")
        return 2
    net = Net(key, ua)
    if a.mode == "probe":
        return mode_probe(net)
    if a.mode == "replay":
        end = a.end
        if not end:
            d = dt.date.fromisoformat(_today_ny()) - dt.timedelta(1)
            while not V3.is_session(d.isoformat(), MC.session_info):
                d -= dt.timedelta(1)
            end = d.isoformat()
        return mode_replay(net, MC, end, a.days)
    if a.mode == "trace":
        return mode_trace(net, MC, a.date, a.sym.upper())
    if a.mode == "harvest":
        mode_harvest(net, MC)
        return 0
    return mode_live(net, MC, os.environ.get("VWL_SEND") == "1", a.segment)


if __name__ == "__main__":
    sys.exit(main())
