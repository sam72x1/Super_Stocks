# -*- coding: utf-8 -*-
"""🧱🔬 `T-SUPDEF` — مِجَسُّ **تعريف الدعم** (العقد `support_def_prereg.md`).

**قراءةٌ فقط:** لا كتابةَ حالةٍ · لا إرسالَ تلغرام · لا سرَّ · لا مسَّ إنتاج.
**ولا يُشحَن منه شيءٌ مهما كانت النتيجة** (‏المحورُ يمسّ جذرًا — `§⓪`).

الحاكمُ `A0` = `pivot_stability` **الإنتاجيّة** كما هي · والوصفيّان `A1`/`A2`
**يُنشَران ولا يُرشَّحان** · و`A-FAR` شاهدُ ضبطٍ **سقوطُه شرطُ صحّة**.

رموزُ الخروج: 0 = الفرعُ 1 · 2 = الفرعُ 2 · 3 = الفرعُ 3 «لا قياس» · 5 = حارس.
"""
import datetime as dt
import os
import sys

import Super_stock as bot

TOL = 2.0                 # `FAISAL_LEVEL_TOL_PCT` — يُقرأ من CONFIG أدناه
FAR_LOOKBACK = 120        # شاهدُ الضبط `A-FAR`
SD0_MIN_ROWS, SD0_MIN_SYMS = 5, 3
SD1_SHARE, SD1_P = 80.0, 0.10
SD2_MEDIAN = 10.0

# ── جدولُ `§⑨-ⓒ`: (رمز · تاريخ · فريم · مستويات · سطرُ الكاتالوج) ──────────────
#    **لا يُوثَق بي**: قفلُ `SDT1` يقرأ الكاتالوج ويشترط ظهورَ كلّ رقمٍ في سطره.
CASES = [
    ("PPBT", "2026-09-05", "daily",  [1.980, 1.682], 1211),
    ("DCOY", "2026-09-05", "ambig",  [2.851],        1218),
    ("ELPW", "2026-09-18", "daily",  [2.500],        1461),
    ("NUWE", "2026-09-18", "h4",     [0.7119],       1464),
    ("DAIC", "2026-09-18", "h4",     [1.986],        1466),
    ("SXTC", "2026-09-18", "daily",  [2.064],        1474),
]


def log(m: str) -> None:
    print(m, flush=True)


def selfcheck_readonly() -> list:
    import ast
    bad = []
    src = open(__file__, encoding="utf-8").read()
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Call):
            nm = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
            if nm in ("send_telegram", "git_save", "save_watchlist"):
                bad.append(f"نداءٌ محرَّم: {nm}")
            if nm == "open":
                mode = getattr(n.args[1], "value", None) if len(n.args) > 1 else None
                for k in n.keywords:
                    if k.arg == "mode":
                        mode = getattr(k.value, "value", "؟")
                if mode is not None and "r" not in str(mode):
                    bad.append(f"فتحٌ بوضعٍ غيرِ قراءة: {mode}")
    if src.count("TELEGRAM_BOT" + "_TOKEN") > 1:
        bad.append("ذكرُ سرّ")
    return bad


def cut_asof(df, asof: str):
    try:
        d = dt.date.fromisoformat(asof)
        keep = [(x.date() if hasattr(x, "date") else x) <= d for x in df.index]
        out = df[keep]
        return out if len(out) >= 40 else None
    except Exception:                                          # noqa: BLE001
        return None


def a0(df):
    """`A0` الحاكم — دالّةُ الإنتاج نفسُها بلا مسٍّ لـ`CONFIG`."""
    try:
        ps = bot.pivot_stability(df["Low"].values.astype(float),
                                 df["Close"].values.astype(float))
        return None if not ps else round(float(ps["pivot"]), 4)
    except Exception:                                          # noqa: BLE001
        return None


def a1(df, look=None):
    """`A1` وصفيّ — أدنى **إغلاقٍ** في النافذة نفسِها."""
    try:
        n = int(look or bot.CONFIG["PIVOT_LOOKBACK"])
        return round(float(df["Close"].astype(float).tail(n).min()), 4)
    except Exception:                                          # noqa: BLE001
        return None


def a2(df, look=None, tol=None):
    """`A2` وصفيّ — أرضيةُ التماسك: أدنى قاعٍ **لُمس أكثرَ من مرّة** ضمن التسامح."""
    try:
        n = int(look or bot.CONFIG["PIVOT_LOOKBACK"])
        t = float(tol if tol is not None else TOL)
        lows = sorted(float(x) for x in df["Low"].astype(float).tail(n).values)
        for i, v in enumerate(lows):
            if v <= 0:
                continue
            hits = sum(1 for w in lows if abs(w - v) / max(w, v) * 100.0 <= t)
            if hits >= 2:
                return round(v, 4)
        return round(lows[0], 4) if lows else None
    except Exception:                                          # noqa: BLE001
        return None


def a_far(df):
    """`A-FAR` شاهدُ ضبطٍ معلومُ الخطأ — أدنى قاعٍ في 120 جلسة."""
    try:
        return round(float(df["Low"].astype(float).tail(FAR_LOOKBACK).min()), 4)
    except Exception:                                          # noqa: BLE001
        return None


def pick_level(levels, close):
    """`§②` قاعدةُ القراءة: الأقربُ **تحتَ** إغلاقِ يوم الصورة · وإلّا None."""
    try:
        below = [float(v) for v in levels if float(v) < float(close)]
        return max(below) if below else None
    except (TypeError, ValueError):
        return None


def err_pct(got, ref):
    try:
        return round((float(got) - float(ref)) / float(ref) * 100.0, 2)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def sign_test_p(n_below: int, n: int) -> float:
    """اختبارُ إشارةٍ ثنائيُّ الذيل عند p=0.5 — **يُحسَب** بلا مكتبةٍ خارجيّة."""
    from math import comb
    if n <= 0:
        return 1.0
    k = max(n_below, n - n_below)
    tail = sum(comb(n, i) for i in range(k, n + 1)) / (2 ** n)
    return round(min(1.0, 2 * tail), 4)


def read_verdict(n_rows, n_syms, share, p, med_abs, far_worse):
    """فروعُ `§④` بحرفها — ولا فرعَ رابع."""
    if n_rows < SD0_MIN_ROWS or n_syms < SD0_MIN_SYMS or not far_worse:
        return 3, ("الفرعُ 3 — **«لا قياس»**: الأرضيّةُ أو صحّةُ المقياس لم تُبلَغ "
                   "· يُعلَن بعدَده ولا يُفسَّر · ولا يُرفَع العدُّ بتأريخٍ مُستنتَج")
    sd1 = share >= SD1_SHARE and p <= SD1_P
    sd2 = med_abs >= SD2_MEDIAN
    if sd1 and sd2:
        return 0, ("الفرعُ 1 — الانحيازُ **مقيسٌ ومادّيّ** ⇒ يُنشَر رقمًا ويُقترَح "
                   "تسجيلٌ لاحق · **ولا يُمَسّ `pivot_stability`**")
    if sd1 and not sd2:
        return 2, ("الفرعُ 2 — الانحيازُ **موجودٌ وغيرُ مادّيّ** ⇒ **يُغلَق المحورُ** "
                   "بشرطِ فتحٍ مؤرَّخ")
    return 3, ("الفرعُ 3 — **«لا قياس»**: `SD1` لم تُستوفَ · يُعلَن ولا يُفسَّر")


def main() -> int:
    global TOL
    TOL = float(bot.CONFIG.get("FAISAL_LEVEL_TOL_PCT", 2.0))
    log("🧱🔬 T-SUPDEF — مِجَسُّ تعريف الدعم (قراءةٌ فقط · لا شحنَ مهما كانت النتيجة)")
    bad = selfcheck_readonly()
    log(f"   V-S1 قراءةٌ فقط: {'✅' if not bad else '🔴 ' + str(bad)}")
    if bad:
        return 5
    if int(bot.CONFIG["PIVOT_LOOKBACK"]) != 25:
        log("   V-S2 🔴 PIVOT_LOOKBACK تحرّك — يُوقَف")
        return 5
    log(f"   V-S2 ✅ PIVOT_LOOKBACK=25 · التسامح {TOL}% · A-FAR={FAR_LOOKBACK}")

    syms = sorted({c[0] for c in CASES})
    hist = bot.download_history(syms)
    rows, skipped = [], []
    for sym, asof, frame, levels, src in CASES:
        df0 = (hist or {}).get(sym)
        if df0 is None or len(df0) < 60:
            skipped.append((sym, asof, "تعذّر الجلب")); continue
        df = cut_asof(df0, asof)
        if df is None:
            skipped.append((sym, asof, "القصُّ لا يترك بياناتٍ كافية")); continue
        close = float(df["Close"].iloc[-1])
        ref = pick_level(levels, close)
        if ref is None:
            skipped.append((sym, asof, f"كلُّ المستويات فوق الإغلاق {close:.3f}"))
            continue
        r = {"sym": sym, "asof": asof, "frame": frame, "ref": ref, "close": close,
             "a0": a0(df), "a1": a1(df), "a2": a2(df), "far": a_far(df),
             "src": src, "bars": len(df)}
        r["e0"] = err_pct(r["a0"], ref)
        r["e1"] = err_pct(r["a1"], ref)
        r["e2"] = err_pct(r["a2"], ref)
        r["ef"] = err_pct(r["far"], ref)
        rows.append(r)

    log("")
    log("═══ V-S3 الجدول (‏صفًّا صفًّا) ═══")
    log("   الرمز  التاريخ     الفريم  إغلاق   فيصل    A0      A1      A2      A-FAR   خطأ%A0")
    for r in rows:
        tag = {"daily": "يوميّ", "h4": "4س*", "ambig": "ملتبس*"}[r["frame"]]
        log(f"   {r['sym']:6s} {r['asof']}  {tag:6s} {r['close']:<7.3f} "
            f"{r['ref']:<7.3f} {str(r['a0']):<7s} {str(r['a1']):<7s} "
            f"{str(r['a2']):<7s} {str(r['far']):<7s} {r['e0']}")
    log("   (* وصفيٌّ بنصّ §⑨-ⓐ — خارج كلّ معيار)")
    log(f"   V-S5 تغطية: طُلبت {len(CASES)} · نجحت {len(rows)} · استُبعدت "
        f"{len(skipped)}")
    for s in skipped:
        log(f"        ⟶ {s[0]} {s[1]}: {s[2]}")

    gov = [r for r in rows if r["frame"] == "daily"]
    n, nsym = len(gov), len({r["sym"] for r in gov})
    log("")
    log("═══ الحاكم (الصفوفُ اليوميّة وحدَها) ═══")
    log(f"   ثلاثيّاتٌ حاكمة: **{n}** من **{nsym}** رمزًا (الأرضيّة {SD0_MIN_ROWS}"
        f"/{SD0_MIN_SYMS})")
    share = p = med = 0.0
    far_worse = False
    if gov:
        below = sum(1 for r in gov if r["a0"] is not None and r["a0"] < r["ref"])
        share = below / n * 100.0
        p = sign_test_p(below, n)
        absl = sorted(abs(r["e0"]) for r in gov if r["e0"] is not None)
        med = absl[len(absl) // 2] if absl else 0.0
        absf = sorted(abs(r["ef"]) for r in gov if r["ef"] is not None)
        medf = absf[len(absf) // 2] if absf else 0.0
        far_worse = medf > med
        log(f"   `SD1` A0 أدنى في **{below}/{n}** = {share:.1f}% · p={p}")
        log(f"   `SD2` وسيطُ |خطأ A0| = **{med:.2f}%**")
        log(f"   `SD3` وسيطُ |خطأ A-FAR| = {medf:.2f}% ⇒ أسوأُ من A0؟ "
            f"**{'نعم' if far_worse else 'لا'}**")

    rc, txt = read_verdict(n, nsym, share, p, med, far_worse)
    log("")
    log("═══ الحكم ═══")
    log(f"JUDGE rc={rc} · {txt}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
