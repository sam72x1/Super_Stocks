#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🪝 T-HUNTER-SIX — قياس **صيّاد المقسّم** نفسه على الستة (+ الشاهدين JEM/NUWE).

العقد: `OPUS_EXECUTION_PACKAGE.md` ④-د · التسجيل المسبق: `hunter_six_prereg.md`.

**السؤال:** عند لحظة فيصل لكلٍّ من الثمانية — أيُّ شرطٍ من شروط الصيّاد الستة كان
يمرّ وأيُّه يسقط، **وبأي هامش**؟ (الصيّاد هو الرابح الحيّ الوحيد — أصاب NUWE ‏+100% —
ولم يُختبَر على الستة قطّ.)

**كيف:** لكل رمز نمشي **كل جلسة** في نافذة [لحظة فيصل −PRE ، +POST] على **لقطة
مجمّدة** (لا ياهو حيّ: البيئة محجوبة، والتقسيم اللاحق يعيد تسوية الأسعار رجعيًّا)،
ونقصّ الإطار **والتقسيمات** عند كل يوم (نفس ما يراه الجالب الحيّ ذلك اليوم) ثم:

  ① **الحكم المرجعيّ** = نداء `scan_split_hunter({sym: df_مقصوص}, today=D)` **نفسها**
     — دالّة الإنتاج حرفيًّا. الأداة **لا تحكم بنفسها**.
  ② **التشخيص** لكل شرط على حدة من **دوال الإنتاج نفسها** (`_split_setup_probe` ·
     `_post_split_high` · `_split_day_value` · `_event_day_open` · `group_pump_scar`)
     ‏+ هوامش الحلاقة (عمر التقسيم · بُعد السعر عن النطاق · `rose_pct` عن حدّه …).
  ③ **قفل ضد إعادة التنفيذ:** حكم التشخيص يُقارَن بالحكم المرجعيّ كل يوم، وأي
     اختلاف يُطبع «⚠️ تعارض» بدل أن يُبتلع.

🔒 بحث/تشخيص فقط — صفر مسّ إنتاج · لا تلغرام · لا حفظ حالة · لا بوّابة · لا وزن.
   لا يعدّل أي عتبة (يقرأ `CONFIG` ويطبع الهامش). خارج الفرز نهائيًّا.

التشغيل:
  BT_FROZEN_PATH=frozen_backtest.pkl.gz python hunter_six_check.py
متغيّرات اختيارية:
  HUNTER_SIX_SYMBOLS   رموز مفصولة بفاصلة (افتراضي: الثمانية)
  HUNTER_SIX_MOMENTS   "SYM=YYYY-MM-DD,…" لتحديد/تصحيح لحظة فيصل
  HUNTER_SIX_PRE       جلسات قبل اللحظة (افتراضي 40)
  HUNTER_SIX_POST      جلسات بعدها (افتراضي 10)
  HUNTER_SIX_FLOAT     "SYM=NUM,…" تجاوز يدويّ للفلوت
  HUNTER_SIX_FLOAT_ORDER  ترتيب مصادر الفلوت (افتراضي "yahoo,cache,card")
  HUNTER_SIX_COUNTER=1 ذراع تشخيصية: إعادة نداء **نفس** المِجَسّ بنافذة عمرٍ موسَّعة
                       (تفصل «سقط على عمر التقسيم وحده» عن غيره) — عمود موسوم ولا
                       يدخل الحكم.
  HUNTER_SIX_CSV       مسار CSV اختياري (الجدول نفسه)
"""
import csv
import datetime as dt
import json
import os

# ── الرموز والثمانية ───────────────────────────────────────────────────────────
DEFAULT_SYMBOLS = ["AZI", "DSY", "EHGO", "ZCMD", "JZ", "SPRC", "JEM", "NUWE"]

# لحظة فيصل لكل رمز + **مصدرها** (تُطبع دائمًا). None = غير موثّقة ⇒ تُعلَن صراحةً
# وتُمشى آخر نافذة من اللقطة موسومةً — **ولا تُقرأ حكمًا** (تسجيل مسبق P6).
MOMENTS = {
    "EHGO": ("2026-05-22", "الحزمة ④-د-② «EHGO 05-22»"),
    "DSY":  ("2026-07-01", "الحزمة ④-د-② «DSY ~07-01» (تقديريّ لليوم)"),
    "ZCMD": ("2026-07-02", "الحزمة ④-د-② «ZCMD 07-02»"),
    "SPRC": ("2026-07-16", "الحزمة ④-د-② «SPRC 07-16» (ولحظة ثانية 07-28)"),
    "JZ":   ("2026-07-27", "الحزمة ④-د-② «JZ 07-27+»"),
    "NUWE": ("2026-07-29", "الحزمة ⓪-8: رُشِّح 07-29 ثم حقّق +100%"),
    "AZI":  (None, "⚠️ غير موثّقة في الحزمة/الكاتالوج — مرّرها بـHUNTER_SIX_MOMENTS"),
    "JEM":  (None, "⚠️ غير موثّقة (تحقيق 07-23 بلا تاريخ لحظة)"),
}

# حقيقة أرضية للفلوت من بطاقات فيصل المؤرَّخة (الحزمة ④-د). **AZI/ZCMD/SPRC غير
# مذكورين هنا عمدًا: «يُعلَن مجهولًا — لا يُخمَّن»** (SPRC يأتي من company_cache المقيس).
FAISAL_FLOAT = {
    "DSY":  (1_250_000, "بطاقة فيصل IMG_0291 «فلوت 1.25 مليون»"),
    "EHGO": (1_620_000, "بطاقة فيصل (الحزمة ④-د)"),
    "JZ":   (282_000, "بطاقة فيصل (الحزمة ④-د، تقريبيّ ~282 ألف)"),
    "JEM":  (94_000, "بطاقة فيصل (الحزمة ④-د) · مِجَسّ ياهو 93,759"),
}

OK, NO, UNK = "✅", "❌", "—"


def _fchk(v):
    return OK if v else NO


def _pairs_env(name):
    """يقرأ "A=1,B=2" من البيئة → dict. فاشل-آمن (يتخطّى المشوّه **ويُعلنه**)."""
    out, bad = {}, []
    for part in (os.environ.get(name, "") or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            bad.append(part)
            continue
        k, v = part.split("=", 1)
        out[k.strip().upper()] = v.strip()
    if bad:
        print(f"⚠️ {name}: تُخطّيت مدخلات مشوّهة (تُعلَن لا تُصمت): {bad}")
    return out


def _rev_splits(sp, upto):
    """استخراج **بيانات** (لا قرار): تواريخ التقسيمات العكسية (نسبة<1) حتى `upto`.
    مطابق لطريقة قراءة `_split_setup_probe` للسلسلة — يُستعمل للهامش (عمر التقسيم)
    فقط، والقرار يبقى للمِجَسّ نفسه."""
    out = []
    it = sp.items() if hasattr(sp, "items") else (sp or [])
    for ts, ratio in it:
        try:
            d = ts.date() if hasattr(ts, "date") else ts
            if isinstance(d, str):
                d = dt.date.fromisoformat(d[:10])
            if float(ratio) < 1.0 and d <= upto:
                out.append((d, float(ratio)))
        except Exception:
            continue
    return sorted(out)


def _slice_splits(sp, upto):
    """يقصّ سلسلة التقسيمات عند `upto` — **إعادة إنتاج أمينة لما يراه الجالب الحيّ
    ذلك اليوم** (`_fetch_splits` لا يمكن أن يعيد تقسيمًا مستقبليًّا). بلا هذا القصّ
    يتسرّب تقسيمٌ لاحق إلى حقل `freq` العرضيّ (`_split_frequency` بلا حدّ أعلى)."""
    try:
        if sp is None:
            return None
        # 🔴 **الفخّ الموثّق في `CLAUDE.md` تكرّر هنا وأمسكه القفل (2026-07-30):**
        # `hasattr(x, "index")` **صحيح للقوائم أيضًا** (`list.index` دالّة!) ⇒ القائمة
        # كانت تدخل مسار pandas فيرمي `sp.index[i]` (دالّة غير قابلة للفهرسة) فيُبتلع
        # الاستثناء ويُرجَع **السلسلة كاملةً بلا قصّ** = تسريبٌ مستقبليّ صامت — وهو
        # عينُ ما بُنيت الأداة لتفاديه. الفحص الصحيح على `iloc` (خاصّ بـpandas).
        if hasattr(sp, "iloc") and hasattr(sp, "index"):
            import pandas as pd
            keep = [i for i in range(len(sp))
                    if pd.Timestamp(sp.index[i]).date() <= upto]
            return sp.iloc[keep] if keep else sp.iloc[0:0]
        return [(d, r) for d, r in (sp or []) if d <= upto]
    except Exception:
        return sp


def _resolve_float(S, sym, order, manual, cache):
    """يحلّ الفلوت مع **مصدره** ويطبع كل المرشّحين (تعذّر ≠ صفر).
    يرجّع (value, source, candidates) — value=None ⇒ «مجهول» (وهو ما يُقصيه الشرط ⑤
    في الإنتاج **صامتًا**؛ هنا يُعلَن)."""
    cands = {}
    if sym in manual:
        try:
            cands["يدويّ"] = int(float(manual[sym]))
        except Exception:
            print(f"⚠️ HUNTER_SIX_FLOAT[{sym}] غير رقمي — تُجوهل.")
    # ياهو الحيّ = **مصدر الإنتاج حرفيًّا** (`_yahoo_float` المتساهل: floatShares ثم
    # sharesOutstanding). محجوب في بيئة التطوير ⇒ None، ويُعلَن. لا يُنادى أصلًا إن
    # لم يكن في ترتيب المصادر أو كان `yf` غائبًا (فلا تعليق على انتظار شبكة).
    y_loose = y_strict = None
    if "yahoo" in order and getattr(S, "yf", None) is not None:
        try:
            y_loose = S._yahoo_float(sym)
            y_strict = S._yahoo_float(sym, strict=True)
        except Exception:
            y_loose = y_strict = None
    if y_loose is not None:
        cands["ياهو/floatShares" if y_strict else "ياهو/sharesOutstanding"] = int(y_loose)
    c = (cache or {}).get(sym) or {}
    if isinstance(c, dict) and c.get("float") is not None:
        try:
            cands["company_cache"] = int(c["float"])
        except Exception:
            pass
    if sym in FAISAL_FLOAT:
        cands[f"بطاقة فيصل ({FAISAL_FLOAT[sym][1]})"] = FAISAL_FLOAT[sym][0]

    def _pick(tag):
        for k in cands:
            if tag == "manual" and k == "يدويّ":
                return k
            if tag == "yahoo" and k.startswith("ياهو"):
                return k
            if tag == "cache" and k == "company_cache":
                return k
            if tag == "card" and k.startswith("بطاقة"):
                return k
        return None

    for tag in ["manual"] + list(order):
        k = _pick(tag)
        if k:
            return cands[k], k, cands
    return None, "مجهول", cands


def _band(S, half):
    lo = half * S.CONFIG["SPLIT_RADAR_BAND_LOW"]
    hi = half * 1.25            # tol الافتراضي في `_split_setup_probe`
    return lo, hi


def run():
    import Super_stock as S
    C = S.CONFIG
    path = os.environ.get("BT_FROZEN_PATH", "").strip()
    if not path:
        print("⚠️ لا BT_FROZEN_PATH — هذي الأداة تعمل على **لقطة مجمّدة** حصرًا "
              "(دستور ⑦: لقطة إلزامية لكل ما يمسّ التقسيمات).")
        return 2
    hist, splits_map, asof = S.load_frozen_dataset(path)
    if not hist:
        print(f"⚠️ تعذّر تحميل اللقطة {path}")
        return 2
    splits_map = splits_map or {}
    syms = [s.strip().upper() for s in
            (os.environ.get("HUNTER_SIX_SYMBOLS", "") or "").split(",") if s.strip()] \
        or list(DEFAULT_SYMBOLS)
    pre_n = int(os.environ.get("HUNTER_SIX_PRE", "40") or 40)
    post_n = int(os.environ.get("HUNTER_SIX_POST", "10") or 10)
    counter = os.environ.get("HUNTER_SIX_COUNTER", "").strip() == "1"
    order = [t.strip() for t in (os.environ.get("HUNTER_SIX_FLOAT_ORDER")
                                 or "yahoo,cache,card").split(",") if t.strip()]
    mom_override = _pairs_env("HUNTER_SIX_MOMENTS")
    flt_manual = _pairs_env("HUNTER_SIX_FLOAT")
    try:
        with open("company_cache.json", encoding="utf-8") as fh:
            cache = json.load(fh)
    except Exception:
        cache = {}

    print("🪝 T-HUNTER-SIX — صيّاد المقسّم على الثمانية (بحث/تشخيص فقط · صفر مسّ إنتاج)")
    print(f"لقطة: {path} · as-of {asof} · {len(hist)} رمز في اللقطة")
    # ── دستور ⑧: أثبت أن التجربة اشتغلت (سطر «العلم فعّال») ─────────────────────
    with_splits = [s for s in syms
                   if splits_map.get(s) is not None and len(splits_map.get(s)) > 0]
    print(f"✔️ العلم فعّال: قرأ لقطة splits لـ{len(with_splits)} رمزًا من {len(syms)} "
          f"مطلوبًا ({', '.join(with_splits) if with_splits else 'لا شيء'}) · "
          f"وإجمالي رموز اللقطة ذات التقسيمات = {sum(1 for v in splits_map.values() if v is not None and len(v))}")
    if not with_splits:
        print("🔴 **تحذير حاسم**: صفر رمز بتقسيمات ⇒ الشرط ① يسقط لكل رمز بنيويًّا "
              "والتجربة **لا تُفسَّر** (بصمة no-op). راجع اللقطة/الرموز.")
    print(f"العتبات الحيّة (تُقرأ ولا تُمَسّ): سعر [{C['SPLIT_RADAR_PRICE_MIN']:g}, "
          f"{C['SPLIT_RADAR_PRICE_MAX']:g}] · كليف ≥{C['SPLIT_CLIFF_PCT']:g}% · "
          f"نافذة الحدث {C['SPLIT_LOOKBACK_DAYS']}ي · نطاق ÷2 "
          f"[×{C['SPLIT_RADAR_BAND_LOW']:g}, ×1.25] · صعود ≤{C['SPLIT_ROSE_MAX_PCT']:g}% "
          f"· فلوت <{C['SPLIT_RADAR_FLOAT_MAX']:,} · قروب: قفزة ≥{C['EXPLOSION_PCT']:g}% "
          f"بحجم ≥{C['VOL_SPIKE_MULT']:g}× · MIN_BARS={C['MIN_BARS']}")
    print("ℹ️ قناة «الطرح الجديد» (SEC) **معطَّلة** هنا (بلا شبكة) ⇒ الحدث المؤسِّس = "
          "التقسيم العكسي فقط — حدٌّ مُعلَن لا نتيجة.")
    print(f"النافذة: لحظة فيصل −{pre_n} جلسة … +{post_n} جلسة · "
          f"ترتيب مصادر الفلوت: {order}"
          + (" · ذراع العدّاد مُفعَّلة (عمود موسوم، خارج الحكم)" if counter else ""))

    rows_csv = []
    summary = []
    for sym in syms:
        print("\n" + "═" * 118)
        df = hist.get(sym)
        mom_src = MOMENTS.get(sym, (None, "غير مُدرَج في جدول اللحظات"))[1]
        mom_raw = mom_override.get(sym) or MOMENTS.get(sym, (None, ""))[0]
        if mom_raw and sym in mom_override:
            mom_src = "HUNTER_SIX_MOMENTS (تجاوز يدويّ)"
        if df is None or len(df) == 0:
            print(f"🔻 {sym}: **غير موجود في اللقطة** (لا يُعطى صفرًا صامتًا). "
                  f"لحظته المدوَّنة: {mom_raw or 'غير موثّقة'} — {mom_src}")
            summary.append((sym, "غير موجود في اللقطة", None, {}))
            continue
        sess = [S.pd.Timestamp(t).date() for t in df.index]
        moment = None
        if mom_raw:
            try:
                moment = dt.date.fromisoformat(str(mom_raw)[:10])
            except Exception:
                print(f"⚠️ {sym}: تاريخ لحظة غير صالح ({mom_raw}) — يُتجاهل.")
        notes = []
        if moment is None:
            idx = len(sess) - 1
            notes.append("⚠️ **لحظة غير موثّقة** ⇒ مُشِيَ آخر نافذة من اللقطة "
                         "(مُعلَن لا صامت) — لا يُقرأ حكمًا على الرمز.")
        elif moment > sess[-1]:
            idx = len(sess) - 1
            notes.append(f"🔴 **لحظته ({moment}) خارج تغطية اللقطة** (آخر جلسة "
                         f"{sess[-1]} · as-of {asof}) ⇒ تلزم لقطة أحدث. "
                         f"المطبوع أدناه لا يجيب عن لحظته.")
        else:
            idx = max(i for i in range(len(sess)) if sess[i] <= moment)
            if sess[idx] != moment:
                notes.append(f"ℹ️ لا جلسة يوم {moment} (عطلة/بلا تداول) ⇒ "
                             f"أقرب جلسة سابقة {sess[idx]}.")
        start, end = max(0, idx - pre_n), min(len(sess) - 1, idx + post_n)
        if idx - pre_n < 0:
            notes.append(f"ℹ️ اللقطة أقصر من النافذة قبل اللحظة ({idx} جلسة متاحة "
                         f"من {pre_n} مطلوبة) — مُعلَن.")
        if idx + post_n > len(sess) - 1:
            notes.append(f"ℹ️ اللقطة تنتهي قبل نهاية النافذة (+{len(sess)-1-idx} "
                         f"من {post_n}) — مُعلَن.")

        sp_full = splits_map.get(sym)
        flt, flt_src, flt_cands = _resolve_float(S, sym, order, flt_manual, cache)
        flt_ok = (flt is not None and flt < C["SPLIT_RADAR_FLOAT_MAX"])
        print(f"🔹 {sym} · لحظة فيصل: {moment or 'غير موثّقة'} ({mom_src}) · "
              f"نافذة {sess[start]} → {sess[end]} ({end - start + 1} جلسة)")
        print(f"   فلوت مُعتمَد: {flt:,} [{flt_src}]" if flt is not None
              else f"   فلوت مُعتمَد: مجهول [{flt_src}] — "
                   f"⚠️ الإنتاج **يُقصي المجهول صامتًا** (الشرط ⑤)")
        print("   مرشّحو الفلوت: " + (" · ".join(
            f"{k}={v:,}" for k, v in flt_cands.items()) or "لا شيء"))
        if flt_cands:
            verdicts = {v < C["SPLIT_RADAR_FLOAT_MAX"] for v in flt_cands.values()}
            if len(verdicts) > 1:
                print("   ⚠️ **حكم ⑤ يختلف باختلاف مصدر الفلوت** — يُقرأ بحذر.")
        rs = _rev_splits(sp_full, sess[end]) if sp_full is not None else []
        print("   تقسيمات عكسية في اللقطة (حتى نهاية النافذة): "
              + (" · ".join(f"{d}×{r:g}" for d, r in rs) or "لا شيء"))
        for n in notes:
            print("   " + n)

        # ── الجدول ───────────────────────────────────────────────────────────
        print("   " + "-" * 114)
        print(f"   التاريخ    شموع/{C['MIN_BARS']} السعر ⓿سعر ⓿كليف   ①عمر-التقسيم  "
              "②النطاق/الموقع            ③ثبات ④صعد%      ⑤فلوت ⑥قروب  الحكم")
        logs = {}
        _orig_log = S.log
        first_match, blockers = None, {}
        for i in range(start, end + 1):
            D = sess[i]
            dfc = df.iloc[:i + 1]
            sp = _slice_splits(sp_full, D)
            # (أ) الحكم المرجعيّ = دالّة الإنتاج نفسها (بلا شبكة: جالبات محقونة)
            S.log = lambda m, _b=logs: _b.__setitem__(str(m), _b.get(str(m), 0) + 1)
            try:
                auth_rows = S.scan_split_hunter(
                    {sym: dfc}, today=D,
                    fetch_splits=lambda s, _sp=sp: _sp,
                    fetch_float=lambda s, _f=flt: _f,
                    fetch_borrow=lambda s: None,
                    fetch_pump=S.group_pump_scar,
                    fetch_offering=lambda s, today=None: None)
            except Exception as e:
                auth_rows = None
                logs[f"استثناء scan_split_hunter: {type(e).__name__}"] = 1
            finally:
                S.log = _orig_log
            auth = bool(auth_rows)

            # (ب) التشخيص — من دوال الإنتاج نفسها + هوامش (بيانات لا قرار)
            c = dfc["Close"].values.astype(float)
            price = float(c[-1])
            px_ok = C["SPLIT_RADAR_PRICE_MIN"] <= price <= C["SPLIT_RADAR_PRICE_MAX"]
            look = min(int(C["SPLIT_LOOKBACK_DAYS"]), len(c) - 1)
            _ratios = [c[-k] / c[-k - 1] - 1.0
                       for k in range(1, look + 1) if c[-k - 1] > 0]
            cliff = min(_ratios) if _ratios else 0.0
            cliff_ok = cliff <= -C["SPLIT_CLIFF_PCT"] / 100.0
            pr = S._split_setup_probe(dfc, sp, D)
            revs = _rev_splits(sp, D)
            age = (D - revs[-1][0]).days if revs else None
            pump = S.group_pump_scar(dfc) or {}
            pump_ok = not pump.get("found")

            if pr:
                lo, hi = _band(S, pr["half"])
                inside = lo <= pr["price"] <= hi
                if inside:
                    pos = "داخل"
                elif pr["price"] < lo:
                    pos = f"تحت {(pr['price']/lo - 1)*100:+.0f}%"
                else:
                    pos = f"فوق {(pr['price']/hi - 1)*100:+.0f}%"
                band_s = f"{lo:.2f}-{hi:.2f}÷2={pr['half']:.2f} {pos}"
                near_ok, held_ok2 = pr["near_bottom"], pr["held_ok"]
                rose = pr.get("rose_pct")
                rose_s = f"{rose:+.1f}" if rose is not None else "لا-قاعدة"
                rise_ok = pr["didnt_rise"]
                # فرع المرجع (اكتشاف الحزمة: ارتداد صامت للإغلاق غير مُصرَّح به)
                ov = S._event_day_open(dfc.get("Open"), pr["event_date"])
                cv = S._split_day_value(dfc["Close"], sp, dfc.index[-1])
                if ov is None:
                    branch = "إغلاق (لا افتتاح)"
                elif ov != ov:
                    branch = "إغلاق (افتتاح NaN) ⚠️ارتداد-صامت"
                else:
                    branch = "افتتاح-يوم-الحدث"
                fv = pr.get("first_val")
                if fv is not None and ov is not None and ov == ov \
                        and abs(round(float(ov), 2) - fv) > 0.005:
                    branch += " ⚠️(لا يطابق first_val)"
            else:
                band_s, pos, near_ok, held_ok2, rise_ok = UNK, UNK, None, None, None
                rose_s, branch, ov, cv, fv = UNK, UNK, None, None, None

            # الحكم المشتقّ (ترتيب الإنتاج: ⓿→①→②→③→④→⑤→⑥)
            chain = [("⓿سعر", px_ok), ("⓿كليف", cliff_ok), ("①حدث", pr is not None),
                     ("②نطاق", near_ok), ("③ثبات", held_ok2), ("④صعد", rise_ok),
                     ("⑤فلوت", flt_ok), ("⑥قروب", pump_ok)]
            blk = next((n for n, v in chain if not v), None)
            derived = blk is None
            if blk:
                blockers[blk] = blockers.get(blk, 0) + 1
            if derived and first_match is None:
                first_match = D
            conflict = "" if derived == auth else "  ⚠️تعارض"

            age_s = (f"{age}ي/{C['SPLIT_LOOKBACK_DAYS']}"
                     + (OK if age is not None and age <= C["SPLIT_LOOKBACK_DAYS"] else NO)
                     ) if age is not None else "لا-تقسيم" + NO
            pump_s = (OK if pump_ok else
                      f"{NO}{pump.get('jump_pct', 0):.0f}%×{pump.get('n_pumps', 0)}"
                      f"@{pump.get('bars_ago', 0)}ج")
            # `MIN_BARS` ليست بوّابة في الصيّاد (يكتفي بـ20) — تُطبع للمقارنة مع
            # مسار التحليل الذي يشترطها، ويُوسَم ما دونها بدل أن يمرّ بلا ملاحظة.
            bars_s = f"{len(dfc)}" + ("" if len(dfc) >= C["MIN_BARS"] else "⚠")
            print(f"   {D}  {bars_s:>5s}  {price:6.2f}  {_fchk(px_ok)}   "
                  f"{cliff*100:6.1f}%{_fchk(cliff_ok)}  {age_s:>13s}  {band_s:<26s} "
                  f"{_fchk(held_ok2) if held_ok2 is not None else UNK}    "
                  f"{rose_s:>9s}{_fchk(rise_ok) if rise_ok is not None else UNK} "
                  f"{_fchk(flt_ok)}    {pump_s:<12s} "
                  f"{'🟢مطابق-كامل' if auth else NO + (' [' + blk + ']' if blk else '')}"
                  f"{conflict}")

            ctr = ""
            if counter and pr is None and revs:
                old = C["SPLIT_LOOKBACK_DAYS"]
                try:
                    C["SPLIT_LOOKBACK_DAYS"] = 100000
                    pr2 = S._split_setup_probe(dfc, sp, D)
                finally:
                    C["SPLIT_LOOKBACK_DAYS"] = old
                if pr2:
                    lo2, hi2 = _band(S, pr2["half"])
                    ctr = (f"عدّاد(نافذة∞): ①يمرّ · ÷2={pr2['half']:.2f} "
                           f"[{lo2:.2f}-{hi2:.2f}] ②{_fchk(pr2['near_bottom'])} "
                           f"③{_fchk(pr2['held_ok'])} ④{_fchk(pr2['didnt_rise'])}"
                           f" (صعد {pr2.get('rose_pct')})")
                else:
                    ctr = "عدّاد(نافذة∞): ما زال None ⇒ الساقط ليس العمر وحده"
                print(f"        ↳ {ctr}")

            rows_csv.append({
                "symbol": sym, "date": D.isoformat(), "bars": len(dfc),
                "price": round(price, 4), "price_ok": px_ok,
                "cliff_pct": round(cliff * 100, 2), "cliff_ok": cliff_ok,
                "split_date": revs[-1][0].isoformat() if revs else "",
                "split_age_days": age, "lookback": C["SPLIT_LOOKBACK_DAYS"],
                # `freq` عرضيّ فقط، ويُطبع لأنه **شاهد قصّ التقسيمات**: `_split_frequency`
                # بلا حدّ أعلى للتاريخ ⇒ بلا `_slice_splits` يتسرّب تقسيمٌ لاحق إليه.
                "freq": pr.get("freq") if pr else "",
                "ref": pr["ref"] if pr else "", "half": pr["half"] if pr else "",
                "band_lo": round(_band(S, pr["half"])[0], 4) if pr else "",
                "band_hi": round(_band(S, pr["half"])[1], 4) if pr else "",
                "band_pos": pos if pr else "", "near_bottom": near_ok,
                "held_ok": held_ok2, "rose_pct": pr.get("rose_pct") if pr else "",
                "didnt_rise": rise_ok, "ref_branch": branch,
                "first_val": fv if pr else "",
                "open_val": (round(float(ov), 4) if ov is not None and ov == ov else ""),
                "close_val": (round(float(cv), 4) if cv is not None and cv == cv else ""),
                "float": flt if flt is not None else "", "float_src": flt_src,
                "float_ok": flt_ok, "pump_found": bool(pump.get("found")),
                "pump_jump_pct": pump.get("jump_pct", ""),
                "pump_n": pump.get("n_pumps", ""),
                "pump_bars_ago": pump.get("bars_ago", ""),
                "pump_broke_support": pump.get("broke_support", ""),
                "authoritative_match": auth, "derived_match": derived,
                "first_blocker": blk or "", "conflict": derived != auth,
                "counter_arm": ctr,
            })
        if logs:
            print("   📝 رسائل الإنتاج أثناء المشي (فريدة + تكرارها — لا حذف صامت):")
            for m, n in sorted(logs.items(), key=lambda x: -x[1]):
                print(f"      ×{n}  {m}")
        summary.append((sym, None, first_match, blockers))

    # ── الخلاصة ──────────────────────────────────────────────────────────────
    print("\n" + "═" * 118)
    print("📊 الخلاصة (معيار النجاح المسجَّل مسبقًا: ≥1 يوم مطابقة كاملة قبل الانفجار)")
    for sym, err, first_match, blockers in summary:
        if err:
            print(f"  • {sym}: {err}")
            continue
        if first_match:
            print(f"  • {sym}: 🟢 **مطابقة كاملة** أول مرة {first_match}")
        else:
            top = " · ".join(f"{k}={v}ي" for k, v in
                             sorted(blockers.items(), key=lambda x: -x[1]))
            print(f"  • {sym}: {NO} صفر مطابقة · الشروط الساقطة (أول جدار/عدد الأيام): "
                  f"{top or 'لا بيانات'}")
    n_conf = sum(1 for r in rows_csv if r["conflict"])
    print(f"\n🔒 قفل «لا إعادة تنفيذ»: تعارض التشخيص مع الحكم المرجعيّ في "
          f"{n_conf} من {len(rows_csv)} صفًّا"
          + ("  ✅" if n_conf == 0 else "  ⚠️ **راجع** — التشخيص لا يطابق الإنتاج"))
    out = os.environ.get("HUNTER_SIX_CSV", "").strip()
    if out and rows_csv:
        try:
            with open(out, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows_csv[0].keys()))
                w.writeheader()
                w.writerows(rows_csv)
            print(f"💾 CSV: {out} ({len(rows_csv)} صف)")
        except Exception as e:
            print(f"⚠️ تعذّر كتابة CSV: {e}")
    print("\nℹ️ حدود الصدق (من التسجيل المسبق §⑥): الفلوت **ليس point-in-time** "
          "ومصدره مطبوع · قناة الطرح الجديد معطَّلة · الشمعة اليومية لا تشمل الافتر · "
          "رمزٌ خارج تغطية اللقطة مُعلَن. عرض/تشخيص — صفر مسّ حالة.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
