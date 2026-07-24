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

    # ── التشغيل الفعلي (نفس مسار الإنتاج، بتقسيمات اللقطة · بلا شورت/فلوت/قروب حيّ) ──
    rows = S.scan_split_radar(hist, fetch_splits=lambda s: splits_map.get(s))
    print(f"\nالرادار يعرض {len(rows)} سهمًا (سقف {C['SPLIT_RADAR_MAX']}):")
    for r in rows:
        print(f"  • {r['symbol']:>6s} ${r['price']:.2f} · هدف÷2=${r['half']:.2f} "
              f"(قمة {r['post_high']:.2f}) · حافظ3ج={'✅' if r['held_ok'] else '❌'} "
              f"· تقسيمات/سنة={r.get('freq', 0)} · آخر تقسيم {r['split_date']}")
    if not rows:
        print("  (لا شيء — قد تكون العتبات ضيّقة أو اللقطة بلا مقسّم وصل ÷2)")
    print("\nℹ️ فحص نمط السعر/التقسيم فقط (بلا شورت/فلوت حيّ). الإنتاج يضيف "
          "فلوت<2م/شورت<20ألف/خالٍ-من-قروب حيًّا. عرض/تشخيص — صفر مسّ حالة.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
