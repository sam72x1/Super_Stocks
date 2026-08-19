#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⛏️🔁 T-SWEEP-RECLAIM — «الستوب المكنوس» (العقد: `sweep_reclaim_prereg.md`).

**السؤال:** بين صفقات الإنتاج الموقوفة (ضُرب وقفُها)، كم نسبةُ مَن استعاد الإغلاق
فوق الدعم الأصليّ خلال نافذةٍ قصيرة؟ وهل إعادةُ الدخول عند الاستعادة — بوقفِ صيغة
الإنتاج على القاع الجديد وهدفِ الخطّة الأصليّ — تعطي توقّعًا موجبًا؟

**الأذرع مثبَّتة قبل أيّ رقم (§③):** `W0` الأساس (الستوب نهائيّ) · `W1` استعادة
خلال 5 جلسات · `W2` خلال 10. **ولا خامسة.**

🔒 **بحث/قياس — صفر مسّ إنتاج.** يشغّل `run_backtest` الإنتاجيّ نفسَه (بلا أيّ
تجاوز بوّابات: الفارز الحيّ كما هو اليوم) على اللقطة المجمّدة، ثم يمشي إعادةَ
الدخول على سلاسل اللقطة نفسها. النتائج تُطبَع للسجلّ.
"""
from __future__ import annotations

import os
import sys

# ⚠️ قبل الاستيراد — `_apply_backtest_overrides` يُنفَّذ وقت تحميل الوحدة
# (بصمة الـno-op الموثّقة: `BT_CANDLE`).
os.environ["SCREENER_MODE"] = "BACKTEST"
os.environ["BT_REPLAY10"] = "1"       # تاريخ الخروج + pivot — بلاه الأذرع no-op
os.environ.setdefault("BT_POTENTIAL", "1")   # وصفيّ يُنشَر ولا يحكم

import Super_stock as S                                        # noqa: E402

RECLAIM_WINDOWS = (5, 10)             # §③: W1=5 · W2=10 (engineering — مُعلَن)
RESOLVE_WINDOW = int(S.CONFIG["BACKTEST_FORWARD_DAYS"])   # 40 — ثابت المحرّك
MIN_REENTRIES = 50                    # §⑥: الأرضية المجمّعة لكلّ ذراع
PIPE_FAIL_PCT = 20.0                  # §⑤ V3/V4: سقف الفقد قبل إعلان عطب أنابيب


def _stop2_of(new_low: float) -> float:
    """وقف إعادة الدخول = صيغة الإنتاج حرفيًّا على القاع الجديد (سطر `stop_lo`
    في `analyze_ticker`: `pivot * (1 - s_hi/100)`)."""
    _s_lo, s_hi = S.CONFIG["STOP_BELOW_LOW_PCT"]
    return float(new_low) * (1.0 - float(s_hi) / 100.0)


def reclaim_walk(hi, lo, cl, exit_idx: int, pivot: float, t1: float,
                 window: int, resolve_window: int = RESOLVE_WINDOW) -> dict:
    """يمشي إعادةَ الدخول لصفقةٍ موقوفة. دالّة نقيّة (مصفوفات + فهرس الستوب).

    الاستعادة = أوّل إغلاق فوق `pivot` في [exit_idx .. exit_idx+window]
    (جلسة الستوب نفسُها تُحسب — §③). القاع الجديد = أدنى Low من جلسة الستوب إلى
    جلسة الاستعادة شاملتين. الحسم من الجلسة **التالية** للدخول (رأس شمعة الدخول
    لا يُحسم — درس F-L1)، الوقف أوّلًا كلّ شمعة (محافظ).

    يرجّع dict فيه `kind` ∈ {no_reclaim, already_above_t1, bad_levels,
    win, loss, survived} + الأرقام."""
    n = len(cl)
    out = {"kind": "no_reclaim", "entry2": None, "stop2": None, "r": None,
           "reclaim_idx": None, "mg2_pct": None}
    if exit_idx is None or exit_idx < 0 or exit_idx >= n or pivot is None:
        return out
    j_end = min(exit_idx + int(window), n - 1)
    rec = None
    for j in range(exit_idx, j_end + 1):
        if float(cl[j]) > float(pivot):
            rec = j
            break
    if rec is None:
        return out
    entry2 = float(cl[rec])
    new_low = float(min(lo[exit_idx:rec + 1]))
    stop2 = _stop2_of(new_low)
    out.update({"reclaim_idx": int(rec), "entry2": round(entry2, 4),
                "stop2": round(stop2, 4)})
    if t1 is not None and entry2 >= float(t1):
        out["kind"] = "already_above_t1"          # ملاحقة — يُعَدّ ولا يُتاجَر
        return out
    if entry2 <= stop2 or t1 is None:
        out["kind"] = "bad_levels"
        return out
    risk = entry2 - stop2
    # مقياس وصفيّ: أقصى صعود قبل ضرب stop2 (لمس +50%)
    peak = None
    end = min(rec + resolve_window, n - 1)
    for k in range(rec + 1, end + 1):
        if float(lo[k]) <= stop2:                 # الوقف أوّلًا (محافظ)
            out["kind"] = "loss"
            out["r"] = -1.0
            break
        peak = max(peak or 0.0, float(hi[k]))
        if float(hi[k]) >= float(t1):
            out["kind"] = "win"
            out["r"] = round((float(t1) - entry2) / risk, 4)
            break
    else:
        if rec + 1 > end:                          # لا شموع بعد الدخول
            out["kind"] = "survived"
            out["r"] = 0.0
        else:
            out["kind"] = "survived"
            out["r"] = round((float(cl[end]) - entry2) / risk, 4)
    if peak is not None and entry2 > 0:
        out["mg2_pct"] = round((peak / entry2 - 1.0) * 100.0, 1)
    return out


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return (sum(xs) / len(xs)) if xs else None


def main() -> int:
    year = os.environ.get("BACKTEST_YEAR", "").strip() or "؟"
    frozen = os.environ.get("BT_FROZEN_PATH", "").strip()
    # V1: لقطة مجمّدة إلزامية (لا كونَ حيًّا صامتًا — انحياز بقاء)
    if not frozen or not os.path.exists(frozen):
        print("⛔ V1: لا لقطة مجمّدة (BT_FROZEN_PATH) — التجربة تشترطها (§⑤). خروج 4.")
        return 4
    hist, _splits, asof = S.load_frozen_dataset(frozen)
    if not isinstance(hist, dict) or not hist:
        print("⛔ V1: تعذّر تحميل اللقطة — خروج 4.")
        return 4
    print(f"⛏️🔁 T-SWEEP-RECLAIM · سنة {year} · لقطة as-of {asof} · رموز اللقطة {len(hist)}")
    print(f"   الأذرع: W1={RECLAIM_WINDOWS[0]}ج · W2={RECLAIM_WINDOWS[1]}ج · "
          f"حسم {RESOLVE_WINDOW}ج · وقف إعادة الدخول = صيغة الإنتاج (7% تحت القاع الجديد)")

    trades = S.run_backtest()
    decided = [t for t in trades if t.get("outcome") in ("win", "loss")]
    stopped = [t for t in trades if t.get("outcome") == "loss"]
    wins = [t for t in decided if t.get("outcome") == "win"]
    wr = (100.0 * len(wins) / len(decided)) if decided else 0.0
    print(f"\n📊 الأساس (W0): إشارات {len(trades)} · محسومة {len(decided)} · "
          f"موقوفة {len(stopped)} · نجاح {wr:.1f}%")

    # V2: العلم فعّال؟ (بصمة الـno-op)
    ex_ok = sum(1 for t in decided if t.get("exit_date"))
    if decided and ex_ok == 0:
        print("⛔ V2: صفر exit_date على المحسومة — علم BT_REPLAY10 خامل. خروج 2.")
        return 2
    print(f"   ✅ العلم فعّال: exit_date على {ex_ok} من {len(decided)} محسومة")

    counters = {"no_data": 0, "no_align": 0, "no_pivot": 0}
    per_arm = {w: {"reclaimed": 0, "trades": [], "already_above_t1": 0,
                   "bad_levels": 0, "no_reclaim": 0} for w in RECLAIM_WINDOWS}
    for t in stopped:
        sym = t.get("symbol")
        df = hist.get(sym)
        if df is None or getattr(df, "empty", True):
            counters["no_data"] += 1
            continue
        pivot = t.get("pivot")
        if pivot is None:
            counters["no_pivot"] += 1
            continue
        try:
            import pandas as pd  # noqa: F401
            idx = df.index
            ex = t.get("exit_date")
            pos = idx.get_indexer([S.pd.Timestamp(ex)])[0] if ex else -1
        except Exception:
            pos = -1
        if pos is None or pos < 0:
            counters["no_align"] += 1
            continue
        hi = df["High"].astype(float).values
        lo = df["Low"].astype(float).values
        cl = df["Close"].astype(float).values
        for w in RECLAIM_WINDOWS:
            res = reclaim_walk(hi, lo, cl, pos, float(pivot), t.get("t1"), w)
            k = res["kind"]
            if k in ("win", "loss", "survived"):
                per_arm[w]["reclaimed"] += 1
                per_arm[w]["trades"].append(res)
            elif k in ("already_above_t1", "bad_levels"):
                per_arm[w]["reclaimed"] += 1
                per_arm[w][k] += 1
            else:
                per_arm[w]["no_reclaim"] += 1

    lost = counters["no_data"] + counters["no_align"] + counters["no_pivot"]
    lost_pct = (100.0 * lost / len(stopped)) if stopped else 0.0
    print(f"\n🩺 التغطية: موقوفة {len(stopped)} · بلا بيانات {counters['no_data']} · "
          f"بلا محاذاة {counters['no_align']} · بلا pivot {counters['no_pivot']} "
          f"({lost_pct:.1f}% فقد)")
    if stopped and lost_pct > PIPE_FAIL_PCT:
        print(f"⛔ V3/V4: الفقد فوق {PIPE_FAIL_PCT:.0f}% — عطب أنابيب لا نتيجة. خروج 3.")
        return 3

    for w in RECLAIM_WINDOWS:
        arm = per_arm[w]
        tr = arm["trades"]
        n_stop = len(stopped) - lost
        rec_pct = (100.0 * arm["reclaimed"] / n_stop) if n_stop else 0.0
        n_win = sum(1 for r in tr if r["kind"] == "win")
        n_loss = sum(1 for r in tr if r["kind"] == "loss")
        n_srv = sum(1 for r in tr if r["kind"] == "survived")
        mean_all = _mean([r["r"] for r in tr])
        mean_dec = _mean([r["r"] for r in tr if r["kind"] in ("win", "loss")])
        hit50 = sum(1 for r in tr if (r.get("mg2_pct") or 0) >= 50)
        print(f"\n⛏️ الذراع W (نافذة {w}ج): استعاد {arm['reclaimed']} من {n_stop} "
              f"موقوفًا صالحًا ({rec_pct:.1f}%)")
        print(f"   منها: تداول {len(tr)} · فوق الهدف أصلًا {arm['already_above_t1']} · "
              f"مستويات شاذّة {arm['bad_levels']}")
        print(f"   💰 win {n_win} · loss {n_loss} · survived {n_srv}")
        print(f"   📐 متوسّط R (survived بسعر آخر شمعة): "
              f"{mean_all:+.4f}" if mean_all is not None else "   📐 متوسّط R: —")
        print(f"   📐 متوسّط R (المحسومة فقط، survived مُسقَط): "
              f"{mean_dec:+.4f}" if mean_dec is not None else
              "   📐 متوسّط R (محسومة): —")
        print(f"   💥 لمس +50% بعد إعادة الدخول: {hit50}")
        print(f"   SR_ROW|{year}|W{w}|{arm['reclaimed']}|{n_stop}|{len(tr)}|"
              f"{n_win}|{n_loss}|{n_srv}|"
              f"{(round(mean_all,4) if mean_all is not None else '')}|"
              f"{(round(mean_dec,4) if mean_dec is not None else '')}|{hit50}")

    print(f"\nℹ️ الأرضية للحكم (§⑥): مجموع إعادات الدخول عبر السنوات الثلاث "
          f"{MIN_REENTRIES} فأكثر لكلّ ذراع — الحكم يُكتب بعد السنوات الثلاث لا هنا.")
    print("⚠️ حدود الصدق (§⑧): win لمسُ الهدف لا تنفيذًا · الدخول بالإغلاق · "
          "انحياز بقاء اللقطة · الآليّة الحيّة (جدار الطلبات) لا تُرى هنا.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
