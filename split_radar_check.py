#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🎯 فحص رادار أسهم التقسيم (dry-run على اللقطة المجمَّدة — بلا تلغرام · بلا حفظ حالة).

الغرض (طلب المستخدم 2026-07-23): معايرة «رادار أسهم التقسيم» قبل الاعتماد على تشغيله
الحيّ — كم سهمًا يرصده على السوق الكامل، وهل العتبات (كليف الهبوط/السعر) معقولة؟

التشغيل: BT_FROZEN_PATH=frozen_backtest.pkl.gz python split_radar_check.py
- يحمّل OHLCV+splits من اللقطة (نفس مصدر باكتيست JEM · as-of مجمَّد · صفر Yahoo حيّ).
- يمرّر التقسيمات من splits_map (لا نداء شبكي)؛ الشورت/الفلوت/القروب = None (هذا الفحص
  يعاير **نمط السعر/التقسيم** = السؤال الأساسي «كم يرصد وهل منطقي»؛ معايير الشورت/الفلوت
  تُضاف حيًّا في الإنتاج).
- يطبع القمع (مُرشّح OHLCV رخيص → مؤكَّد بالتقسيم → قرب القاع÷2) + الصفوف النهائية.

🔒 عرض/تشخيص فقط — لا يمسّ أي حالة، لا يرسل تلغرام، خارج الفرز نهائيًا."""
import datetime as _dt
import os


def run():
    import Super_stock as S
    path = os.environ.get("BT_FROZEN_PATH", "").strip()
    if not path:
        print("⚠️ لا BT_FROZEN_PATH — مرّر مسار اللقطة المجمَّدة.")
        return 2
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

    # ── تشخيص القمع: عدّ كل مرحلة (نفس منطق scan_split_radar، للرؤية فقط) ──
    today = _dt.date.today()
    pre = confirmed = near = 0
    for sym, df in hist.items():
        try:
            c = df["Close"].values.astype(float)
            if len(c) < 20:
                continue
            price = float(c[-1])
            if not (0 < price <= C["SPLIT_RADAR_PRICE_MAX"]):
                continue
            look = min(int(C["SPLIT_LOOKBACK_DAYS"]), len(c) - 1)
            cliff = min((c[-k] / c[-k - 1] - 1.0)
                        for k in range(1, look + 1) if c[-k - 1] > 0)
            if cliff > -C["SPLIT_CLIFF_PCT"] / 100.0:
                continue
            pre += 1
            pr = S._split_setup_probe(df, splits_map.get(sym), today)
            if pr:
                confirmed += 1
                if pr["near_bottom"]:
                    near += 1
        except Exception:
            continue
    print(f"\nالقمع: مُرشّح OHLCV(سعر منخفض+كليف)={pre} → مؤكَّد تقسيم عكسي={confirmed}"
          f" → قرب القاع÷2={near}")

    # ── التشغيل الفعلي (نفس مسار الإنتاج): تقسيمات من اللقطة + اقتراض/فلوت/قروب حيّ من
    #    ChartExchange (فيصل: الشورت = المتاح CE · الفلوت من CE). CE يصل من Actions. ──
    rows = S.scan_split_radar(hist, fetch_splits=lambda s: splits_map.get(s),
                              fetch_borrow=S.ce_borrow_info,
                              fetch_float=S.ce_float_info,
                              fetch_pump=S.group_pump_scar)
    print(f"\nالرادار يعرض {len(rows)} سهمًا (سقف {C['SPLIT_RADAR_MAX']}):")

    def _fchk(ok):
        return "✅" if ok else "❌"

    for r in rows:
        av = f"{r['short']:,}" if r.get("short") is not None else "—"
        fl = f"{r['float']:,}" if r.get("float") is not None else "—"
        print(f"  • {r['symbol']:>6s} ${r['price']:.2f} · هدف÷2=${r['half']:.2f} "
              f"(شمعة التقسيم {r['ref']:.2f}) · تطابق {r.get('match', 0)}/5 · "
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
            pr = S._split_setup_probe(df, splits_map.get(sym), today) or {}
            bor = S.ce_borrow_info(sym) or {}
            av = bor.get("shares_available")
            flt = S.ce_float_info(sym)
            pump = S.group_pump_scar(df) or {}
            price = float(df["Close"].iloc[-1])
            print(f"  • {sym}: سعر ${price:.2f}")
            if pr:
                print(f"      قيمة شمعة التقسيم={pr['ref']:.2f} · هدف÷2=${pr['half']:.2f}"
                      f" · قرب القاع={_fchk(pr['near_bottom'])} · حافظ3ج={_fchk(pr['held_ok'])}"
                      f" · تقسيمات/سنة={pr.get('freq', 0)}")
            else:
                print("      (المِجَسّ: مو مقسّمًا عكسيًّا حديثًا أو بيانات ناقصة)")
            print(f"      فلوت CE={flt if flt is not None else '—'} "
                  f"(<2م {_fchk(flt is not None and flt < C['SPLIT_RADAR_FLOAT_MAX'])}) · "
                  f"متاح CE={av if av is not None else '—'} "
                  f"(<20ألف {_fchk(av is not None and av < C['SHORT_DAILY_MAX'])}) · "
                  f"رسوم={bor.get('borrow_fee', '—')}% · قروب={_fchk(pump.get('found'))}")
            # 🔬 تشخيص الفلوت: صفحة CE الخام + مصدر ياهو (المصدر الأساسي بالبوت)
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

    print("\nℹ️ الشورت = عمود Available من ChartExchange (قراءة فيصل). عرض/تشخيص — صفر مسّ حالة.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
