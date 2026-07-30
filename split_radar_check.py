#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🎯 فحص رادار أسهم التقسيم (dry-run على اللقطة المجمَّدة — بلا تلغرام · بلا حفظ حالة).

الغرض (طلب المستخدم 2026-07-23): معايرة «رادار أسهم التقسيم» قبل الاعتماد على تشغيله
الحيّ — كم سهمًا يرصده على السوق الكامل، وهل العتبات (كليف الهبوط/السعر) معقولة؟

التشغيل: BT_FROZEN_PATH=frozen_backtest.pkl.gz python split_radar_check.py
- يحمّل OHLCV+splits من اللقطة (نفس مصدر باكتيست JEM · as-of مجمَّد · صفر Yahoo حيّ).
- يمرّر التقسيمات من splits_map (لا نداء شبكي)؛ الشورت/القروب من نفس مصادر الإنتاج.
- يطبع القمع (مُرشّح OHLCV رخيص → مؤكَّد بالتقسيم → قرب القاع÷2) + الصفوف النهائية.

🔴 **إصلاح 2026-07-30 (شرطٌ مسبق لأي قياس — الحزمة ④-د-①):** كان الفلوت يُقرأ من
`ce_float_info` **الميتة منذ 2026-07-24** (صفحة CE overview صارت قِشرة JS) بينما
الإنتاج أُصلح لـ`_yahoo_float` ⇒ **كل dry-run كان يطبع «فلوت —/❌» زورًا** (DSY 1.25م
وEHGO 1.15م وSPRC 553K كلها تُقرأ «—»). وُحِّد على **`_yahoo_float(strict=True)`**
(قاعدة `CLAUDE.md`: `strict` إلزاميّ حيث يصل المخرج للحكم — الوضع المتساهل يسقط
لـ`sharesOutstanding` وهو ≥ الفلوت دائمًا)، **وسطر CE الخام باقٍ للتشخيص** (لنعرف
متى تعود الصفحة).

🕰️ **وسيط `cutoff`** (‏`SPLIT_RADAR_CUTOFF=YYYY-MM-DD`): يقصّ الإطار عند تاريخ
اللحظة فيصير الفحص point-in-time. ⚠️ **حدّ مُعلَن:** `scan_split_radar` تقرأ
`dt.date.today()` **داخليًّا** (لا وسيط `today` لها) ⇒ في وضع القصّ يبقى **عمر
التقسيم** فيها مقيسًا من اليوم الحقيقي؛ القمع وقسم رموز التركيز أدناه **يمرّران
الـcutoff صراحةً** فهما صحيحان point-in-time. (المشي التاريخي الكامل يوم-بيوم مكانه
`hunter_six_check.py` — يستعمل `scan_split_hunter(…, today=D)` التي تقبل التاريخ.)

🔒 عرض/تشخيص فقط — لا يمسّ أي حالة، لا يرسل تلغرام، خارج الفرز نهائيًا."""
import datetime as _dt
import os


def _yf_float(S, sym):
    """الفلوت من **مصدر الإنتاج الحيّ** بعد إصلاح 07-27: `_yahoo_float(strict=True)`
    (‏`floatShares` حصرًا — لا سقوط لـ`sharesOutstanding`). فاشل-آمن → None = «تعذّر»
    لا «صفر»."""
    try:
        return S._yahoo_float(sym, strict=True)
    except Exception:
        return None


def run(cutoff=None):
    import Super_stock as S
    path = os.environ.get("BT_FROZEN_PATH", "").strip()
    if not path:
        print("⚠️ لا BT_FROZEN_PATH — مرّر مسار اللقطة المجمَّدة.")
        return 2
    if cutoff is None:
        _cs = os.environ.get("SPLIT_RADAR_CUTOFF", "").strip()
        if _cs:
            try:
                cutoff = _dt.date.fromisoformat(_cs[:10])
            except Exception:
                print(f"⚠️ SPLIT_RADAR_CUTOFF غير صالح ({_cs}) — يُتجاهل (بلا قصّ).")
    elif isinstance(cutoff, str):
        cutoff = _dt.date.fromisoformat(cutoff[:10])
    hist, splits_map, asof = S.load_frozen_dataset(path)
    if not hist:
        print(f"⚠️ تعذّر تحميل اللقطة {path}")
        return 2
    splits_map = splits_map or {}
    C = S.CONFIG
    print(f"🎯 فحص رادار المقسّم — لقطة {path} · as-of {asof} · {len(hist)} رمز")
    print(f"عتبات: سعر≤${C['SPLIT_RADAR_PRICE_MAX']:g} · كليف هبوط≥{C['SPLIT_CLIFF_PCT']:g}% "
          f"· فلوت<{C['SPLIT_RADAR_FLOAT_MAX']:,} · probe_cap={C['SPLIT_RADAR_PROBE_CAP']} "
          f"· max العرض={C['SPLIT_RADAR_MAX']}")
    print("ℹ️ الفلوت = `_yahoo_float(strict=True)` (مصدر الإنتاج بعد موت CE overview "
          "2026-07-24) · «—» = **تعذّر الجلب لا صفر**.")

    # 🕰️ القصّ عند تاريخ اللحظة (point-in-time) — يُعلَن دائمًا مع حدّه
    if cutoff:
        n0 = len(hist)
        hist = {s: d[[S.pd.Timestamp(t).date() <= cutoff for t in d.index]]
                for s, d in hist.items()}
        hist = {s: d for s, d in hist.items() if len(d) >= 20}
        print(f"🕰️ قصّ عند {cutoff}: {len(hist)} رمز بقي من {n0} (الباقي أقصر من 20 شمعة "
              f"عند ذلك التاريخ — مُعلَن لا صامت).")
        print("   ⚠️ حدّ: `scan_split_radar` تستعمل `date.today()` داخليًّا ⇒ **عمر "
              "التقسيم** في مخرجاتها يُقاس من اليوم الحقيقي لا من الـcutoff؛ القمع "
              "وقسم التركيز أدناه يمرّران الـcutoff صراحةً فهما point-in-time.")

    def _sp(sym):
        """تقسيمات الرمز **مقصوصة عند الـcutoff** = ما كان الجالب الحيّ سيعيده ذلك
        اليوم. بلا القصّ يتسرّب تقسيمٌ لاحق إلى `freq` (‏`_split_frequency` بلا حدّ
        أعلى للتاريخ) — تسريبٌ عرضيّ لكنه تسريب."""
        sp = splits_map.get(sym)
        if sp is None or not cutoff:
            return sp
        try:
            keep = [i for i in range(len(sp))
                    if S.pd.Timestamp(sp.index[i]).date() <= cutoff]
            return sp.iloc[keep] if keep else sp.iloc[0:0]
        except Exception:
            return sp

    # ── تشخيص القمع: عدّ كل مرحلة (نفس منطق scan_split_radar، للرؤية فقط) ──
    today = cutoff or _dt.date.today()
    pre = confirmed = near = 0
    below_floor = 0            # 🚫 كم رمزًا أسقطته **أرضية $1** وحدها (كلفة معلنة)
    for sym, df in hist.items():
        try:
            c = df["Close"].values.astype(float)
            if len(c) < 20:
                continue
            price = float(c[-1])
            # ⚠️ كان `0 < price` هنا بينما الإنتاج يستعمل `SPLIT_RADAR_PRICE_MIN`
            # (أُضيفت 2026-07-27 من نصّ فيصل «السنتات خارج الشرح») ⇒ كان العدّاد
            # يزعم «نفس منطق scan_split_radar» وهو أوسع منه. وُحِّد، وكلفة الأرضية
            # تُطبع صراحةً بدل أن تختفي.
            if not (0 < price <= C["SPLIT_RADAR_PRICE_MAX"]):
                continue
            look = min(int(C["SPLIT_LOOKBACK_DAYS"]), len(c) - 1)
            cliff = min((c[-k] / c[-k - 1] - 1.0)
                        for k in range(1, look + 1) if c[-k - 1] > 0)
            if cliff > -C["SPLIT_CLIFF_PCT"] / 100.0:
                continue
            if price < C["SPLIT_RADAR_PRICE_MIN"]:
                below_floor += 1
                continue
            pre += 1
            pr = S._split_setup_probe(df, _sp(sym), today)
            if pr:
                confirmed += 1
                if pr["near_bottom"]:
                    near += 1
        except Exception:
            continue
    print(f"\nالقمع: مُرشّح OHLCV(سعر منخفض+كليف)={pre} → مؤكَّد تقسيم عكسي={confirmed}"
          f" → قرب القاع÷2={near}")
    print(f"🚫 أسقطتهم **أرضية السعر** ${C['SPLIT_RADAR_PRICE_MIN']:g} وحدها (اجتازوا "
          f"الكليف): {below_floor} — كلفة معلنة لا مقصوصة صامتًا.")

    # ── التشغيل الفعلي (نفس مسار الإنتاج): تقسيمات من اللقطة + اقتراض/قروب حيّ من
    #    ChartExchange (فيصل: الشورت = المتاح CE) + **الفلوت من ياهو** (CE ميتة). ──
    rows = S.scan_split_radar(hist, fetch_splits=_sp,
                              fetch_borrow=S.ce_borrow_info,
                              fetch_float=lambda s: _yf_float(S, s),
                              fetch_pump=S.group_pump_scar)
    print(f"\nالرادار يعرض {len(rows)} سهمًا (سقف {C['SPLIT_RADAR_MAX']}):")

    def _fchk(ok):
        return "✅" if ok else "❌"

    for r in rows:
        av = f"{r['short']:,}" if r.get("short") is not None else "—"
        fl = f"{r['float']:,}" if r.get("float") is not None else "—"
        print(f"  • {r['symbol']:>6s} ${r['price']:.2f} · هدف÷2=${r['half']:.2f} "
              f"(قمة ما بعد التقسيم {r['ref']:.2f}) · تطابق {r.get('match', 0)}/5 · "
              f"{_fchk(r.get('float_ok'))}فلوت {fl} · {_fchk(r.get('short_ok'))}متاح {av} · "
              f"{_fchk(r['held_ok'])}حافظ3ج · {_fchk(not r.get('pump'))}لا-قروب · "
              f"تقسيمات/سنة={r.get('freq', 0)}")
    if not rows:
        print("  (لا شيء — قد تكون العتبات ضيّقة أو اللقطة بلا مقسّم وصل ÷2)")

    # ── 🔍 رموز تركيز (SPLIT_RADAR_FOCUS=JEM,PAVS): تطبع الشيك ليست الكاملة حتى لو خارج
    #    السقف أو لم تمرّ المِجَسّ — للإجابة الحاسمة «هل يطابق معايير فيصل؟» ──
    focus = [s.strip().upper() for s in os.environ.get("SPLIT_RADAR_FOCUS", "").split(",")
             if s.strip()]
    if focus:
        print("\n🔍 رموز التركيز (شيك ليست فيصل الكاملة):")
        for sym in focus:
            df = hist.get(sym)
            if df is None:
                print(f"  • {sym}: غير موجود في اللقطة")
                continue
            pr = S._split_setup_probe(df, _sp(sym), today) or {}
            bor = S.ce_borrow_info(sym) or {}
            av = bor.get("shares_available")
            flt = _yf_float(S, sym)          # 🔴 كان `ce_float_info` الميتة ⇒ «—» زورًا
            pump = S.group_pump_scar(df) or {}
            price = float(df["Close"].iloc[-1])
            print(f"  • {sym}: سعر ${price:.2f}")
            if pr:
                print(f"      قمة ما بعد التقسيم={pr['ref']:.2f} · هدف÷2=${pr['half']:.2f}"
                      f" · قرب القاع={_fchk(pr['near_bottom'])} · حافظ3ج={_fchk(pr['held_ok'])}"
                      f" · لم يصعد={_fchk(pr.get('didnt_rise'))}"
                      f" · تقسيمات/سنة={pr.get('freq', 0)}")
            else:
                print("      (المِجَسّ: مو مقسّمًا عكسيًّا حديثًا أو بيانات ناقصة)")
            print(f"      فلوت ياهو(strict)={flt if flt is not None else '— (تعذّر)'} "
                  f"(<2م {_fchk(flt is not None and flt < C['SPLIT_RADAR_FLOAT_MAX'])}) · "
                  f"متاح CE={av if av is not None else '—'} "
                  f"(<20ألف {_fchk(av is not None and av < C['SHORT_DAILY_MAX'])}) · "
                  f"رسوم={bor.get('borrow_fee', '—')}% · قروب={_fchk(pump.get('found'))}")
            # 🔬 تشخيص الفلوت: **سطر CE الخام باقٍ عمدًا** (لنعرف متى تعود الصفحة من
            #    قِشرة JS) + مُخرَج `ce_float_info` نفسها + حقلا ياهو الخامان.
            try:
                _cef = S.ce_float_info(sym)
                print(f"      🔬 ce_float_info (ميتة منذ 07-24، للتشخيص): "
                      f"{_cef if _cef is not None else 'None'}")
            except Exception as _e:
                print(f"      🔬 ce_float_info: تعذّر ({type(_e).__name__})")
            try:
                _u = f"https://chartexchange.com/symbol/nasdaq-{sym.lower()}/"
                _rp = S.requests.get(_u, headers=S.BROWSER_UA, timeout=8)
                _h = _rp.text or ""
                _fi = _h.find("Float")
                print(f"      🔬 CE overview: HTTP {_rp.status_code} · طول={len(_h)} · "
                      f"«Float» {'موجودة' if _fi >= 0 else 'غائبة'}")
            except Exception as _e:
                print(f"      🔬 CE overview: تعذّر ({type(_e).__name__})")
            try:
                _info = S.yf.Ticker(sym).info if S.yf is not None else {}
                print(f"      🔬 ياهو: floatShares={_info.get('floatShares')} · "
                      f"sharesOutstanding={_info.get('sharesOutstanding')}")
            except Exception as _e:
                print(f"      🔬 ياهو: تعذّر ({type(_e).__name__})")

    print("\nℹ️ الشورت = عمود Available من ChartExchange (قراءة فيصل) · **الفلوت من ياهو "
          "`strict` لا من CE** (ماتت 07-24) · «—» تعذّر لا صفر. عرض/تشخيص — صفر مسّ حالة.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
