#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🗜️🎯 `T-PRESS-Q` — الضغطُ على مرشّحينا (العقد: `press_prereg.md §⑨` ·
مدفوعٌ قبل أيّ رقم).

**السؤال:** داخل إشارات الفارز الإنتاجيّ (بعد اعتماد B2)، هل حالةُ يوم الإشارة
(ضُغط وحُفظ / ضُغط وكُسر / لم يُضغَط) تميّز مَن يبلغ ‏+50% قبل وقفه؟

🔒 بنمط `anchor_arms` حرفيًّا (نسخُ النمط القائم أوثقُ من الذاكرة): طفلٌ يرفع
أعلامَ الباكتيست ويشغّل `run_backtest` الإنتاجيّ، والتصنيفُ بدالّة
**`press_scan.classify` بالاسم وبنافذتها `W`** (مصدرٌ واحد — `PQ1`) على شموع
اللقطة المجمَّدة، من **إغلاق يوم الإشارة** ⇒ صفرُ نظرٍ مستقبليّ."""
from __future__ import annotations

import json
import os
import subprocess
import sys

# `PQV1`: أرقامُ `B2` المنشورة (‏anchor_prereg §⑨-⑪) — الإنتاجُ بعد الاعتماد
# يجب أن يعيدها بت-بت؛ خرقٌ ⇒ ℹ️ «مقامٌ جديد» يُعلَن ولا يُسقِط.
PUB_SIGNALS = {"2024": 1591, "2025": 1607, "2026": 736}
MIN_PRESSED = 100                  # أرضيةُ الحكم لكلّ سنة (§⑨)
MAX_UNCLASSIFIED_PCT = 10.0        # تعذّرٌ فوقها = عطبُ أداة ⇒ خروج 3


def _log(msg: str) -> None:
    print(msg, flush=True)


def child_env() -> dict:
    """أعلامُ الباكتيست — نفسُ `anchor_arms.child_env` (بلاها `mg_pre_stop`
    غائبٌ فتُطبَع أصفارٌ كاذبة — بصمةُ `T-CHASE`)."""
    return {"SCREENER_MODE": "BACKTEST", "BT_REPLAY10": "1",
            "BT_ENVVALS": "1", "BT_POTENTIAL": "1"}


def state_of(hist: dict, sym: str, date_iso: str):
    """نقيّة: حالةُ يوم الإشارة من شموع اللقطة — بـ`classify`/`W` **بالاسم**.

    ترجع `('held'|'broken'|None, swept)` أو `('تعذّر', False)` إن غاب الرمزُ أو
    اليومُ أو قصُر التاريخ — **يُعَدّ ولا يُصنَّف** (عطبٌ ليس «لم يُضغَط»)."""
    import press_scan as P                                       # noqa: PLC0415
    df = (hist or {}).get(str(sym).upper())
    if df is None:
        return "تعذّر", False
    try:
        dates = [str(d.date()) for d in df.index]
        i = dates.index(str(date_iso)[:10])
    except ValueError:
        return "تعذّر", False
    if i < P.W:
        return "تعذّر", False
    try:
        lo = df["Low"].values.astype(float)
        cl = df["Close"].values.astype(float)
        prior_min = float(min(lo[i - P.W:i]))
        if prior_min <= 0:
            return "تعذّر", False
        return P.classify(float(lo[i]), float(cl[i]), prior_min)
    except Exception:                                             # noqa: BLE001
        return "تعذّر", False


def exploded50(t: dict):
    """‏`mg_pre_stop ≥ 50` — نفسُ استبعاد `anchor_arms._d`: `no_fill`/الغائبُ
    خارج المقام (`None` = لا يدخل)."""
    if t.get("mg_outcome") in (None, "no_fill"):
        return None
    try:
        return float(t.get("mg_pre_stop") or 0.0) >= 50.0
    except (TypeError, ValueError):
        return None


def run_child() -> int:
    import Super_stock as S                                      # noqa: PLC0415
    trades = S.run_backtest() or []
    hist, _sp, asof = S.load_frozen_dataset(
        os.environ.get("BT_FROZEN_PATH") or "frozen_backtest.pkl.gz")
    rows = []
    for t in trades:
        st, swept = state_of(hist, t.get("symbol"), str(t.get("date")))
        rows.append({"state": st, "swept": bool(swept), "e50": exploded50(t)})
    print("PQ_JSON: " + json.dumps(
        {"signals": len(trades), "asof": str(asof), "rows": rows},
        ensure_ascii=False))
    return 0


def wilson(k, n):
    import press_scan as P                                       # noqa: PLC0415
    return P.wilson(k, n)


def report(payload: dict, year: str) -> int:
    rows = payload["rows"]
    sig = payload["signals"]
    _log(f"\n📊 T-PRESS-Q سنة {year} — إشاراتُ الإنتاج {sig}")
    pub = PUB_SIGNALS.get(year)
    if pub is None:
        _log("  PQV1 ℹ️ سنةٌ غيرُ مرجعية — لا مِرساةَ منشورة.")
    elif sig == pub:
        _log(f"  PQV1 ✅ فحصُ التكامل بت-بت: الإشارات {sig} = منشور B2 {pub} "
             "⇒ **الإنتاجُ ≡ B2 بعد الاعتماد**")
    else:
        _log(f"  PQV1 ℹ️ 🔴 خرق: {sig} ≠ منشور {pub} ⇒ **مقامٌ جديد يُعلَن** — "
             "المقارنةُ الداخلية بين الحالات قائمة")
    unc = sum(1 for r in rows if r["state"] == "تعذّر")
    if rows and 100.0 * unc / len(rows) > MAX_UNCLASSIFIED_PCT:
        _log(f"⛔ PQV2: تعذّرُ تصنيف {unc}/{len(rows)} فوق "
             f"{MAX_UNCLASSIFIED_PCT}% ⇒ عطبُ أداةٍ — خروج 3.")
        return 3
    groups = {"Q1 ضُغط وحُفظ": lambda r: r["state"] == "held",
              "Q2 ضُغط وكُسر": lambda r: r["state"] == "broken",
              "Q0 لم يُضغَط": lambda r: r["state"] is None,
              "Q3 مسحٌ واستُعيد": lambda r: r["swept"]}
    stats = {}
    for name, fn in groups.items():
        sub = [r for r in rows if fn(r) and r["e50"] is not None]
        k = sum(1 for r in sub if r["e50"])
        n = len(sub)
        w = wilson(k, n)
        stats[name[:2]] = (n, k, w)
        _log(f"  {name:<16} محسومة={n:<6} انفجر50={k:<5} "
             f"نسبة={100.0 * k / n if n else 0.0:6.2f}% "
             f"Wilson=[{100 * w[0]:.2f},{100 * w[1]:.2f}]")
    _log(f"  (تعذّرُ تصنيف {unc} — يُعَدّ ولا يُصنَّف)")
    n_press = stats["Q1"][0] + stats["Q2"][0]
    if n_press == 0:
        _log("⛔ PQV2: صفرُ إشارةٍ مضغوطة ⇒ خروج 3 — لا تشغيلةَ خضراءَ بلا قياس.")
        return 3
    floor_ok = n_press >= MIN_PRESSED
    (n1, k1, w1), (n2, k2, w2) = stats["Q1"], stats["Q2"]
    (n0, k0, w0) = stats["Q0"]
    kp, np_ = k1 + k2, n1 + n2
    wp = wilson(kp, np_)
    r_p = kp / np_ if np_ else 0.0
    r_0 = k0 / n0 if n0 else 0.0
    c1 = bool(n0 and np_ and ((wp[0] > w0[1]) or (wp[1] < w0[0])))
    _log(f"  🧭 ① المضغوطُ مجمَّعًا {100 * r_p:.2f}% [{100 * wp[0]:.2f},"
         f"{100 * wp[1]:.2f}] مقابل غير المضغوط {100 * r_0:.2f}% ⇒ "
         f"فاصلان {'منفصلان ✅' if c1 else 'متداخلان 🔴'}")
    _log(f"  🧭 ② تنبّؤ PQ1 (المكسورُ ≥ المحفوظ): "
         f"{100.0 * k2 / n2 if n2 else 0:.2f}% مقابل "
         f"{100.0 * k1 / n1 if n1 else 0:.2f}% ⇒ "
         f"{'✅' if (n1 and n2 and k2 / n2 >= k1 / n1) else '🔴'}")
    _log(f"  🧭 أرضيّة (مضغوطٌ ≥{MIN_PRESSED}): {n_press} ⇒ "
         + ("✅" if floor_ok else "🔴 **لا حكم لهذي السنة**"))
    return 0


def main() -> int:
    if "--child" in sys.argv:
        return run_child()
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    path = os.environ.get("BT_FROZEN_PATH") or "frozen_backtest.pkl.gz"
    _log(f"\n{'=' * 78}\n🗜️🎯 T-PRESS-Q — الضغطُ على مرشّحينا · السنة {year}"
         f"\n{'=' * 78}")
    if not os.path.exists(path):
        _log(f"⛔ PQV3: اللقطةُ المجمَّدة مفقودة ({path!r}) ⇒ خروج 4.")
        return 4
    p = subprocess.run([sys.executable, os.path.abspath(__file__), "--child"],
                       capture_output=True, text=True,
                       env={**dict(os.environ), **child_env()})
    blob = (p.stdout or "") + "\n" + (p.stderr or "")
    for ln in blob.splitlines():
        if not ln.startswith("PQ_JSON:"):
            _log("  " + ln)
    rows = [x for x in blob.splitlines() if x.startswith("PQ_JSON:")]
    if p.returncode != 0 or not rows:
        _log(f"⛔ الطفلُ سقط (rc={p.returncode}) — لا حكم (خروج 2).")
        return 2
    rc = report(json.loads(rows[-1].split("PQ_JSON:", 1)[1]), year)
    _log("\n⚠️ **تشخيصٌ لا حكم نهائيّ بسنة** (§⑨): الحكمُ بالسنوات الثلاث · "
         "لا `R` يُقاس · وحدودُ §⑥ قائمة.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
