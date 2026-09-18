# -*- coding: utf-8 -*-
"""🧱📅🔬 قياسُ **فرضيّة التقسيم** — الملحق `weekly_support_prereg.md §⑦`.

**قراءةٌ فقط:** لا كتابةَ حالةٍ · لا إرسالَ تلغرام · لا سرَّ · لا مسَّ إنتاج.

يقيس ثلاثةً ولا شيءَ غيرَها (‏`D1` أحداثُ التقسيم · `D2` العاملُ المطلوب ·
`D3` شكلُ القاع)، ويطبّق الفروعَ الثلاثةَ بحرفها.

رموزُ الخروج: 0 = الفرعُ 2 (التفسيرُ البديلُ يسقط) · 2 = الفرعُ 1 (مقياسان
مختلفان) · 7 = الفرعُ 3 «لا قياس».
"""
import datetime as dt
import os
import sys

import Super_stock as bot

SYM = (os.getenv("WKSUP_SYMBOL") or "PPBT").strip().upper()
ASOF = (os.getenv("WKSUP_ASOF") or "2026-09-05").strip()
REF_WEEKLY = 1.694
REF_DAILY = 1.682
MEASURED = 1.16        # ما أعطاه المِجَسُّ في `§①` (‏التشغيلة 35388853118)


def log(m: str) -> None:
    print(m, flush=True)


def selfcheck_readonly() -> list:
    """قراءةٌ فقط — بالـAST · وما لا يُثبَت أنه قراءةٌ يُعَدّ كتابة."""
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
    _tok = "TELEGRAM_BOT" + "_TOKEN"
    if src.count(_tok) > 1:
        bad.append("ذكرُ سرٍّ")
    return bad


def needed_factor(ref: float, got: float):
    """`D2`: العاملُ المطلوب **يُحسَب** لا يُكتَب."""
    try:
        return round(float(ref) / float(got), 4) if got else None
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def within(a, b, tol_pct: float) -> bool:
    try:
        a, b = float(a), float(b)
        return a > 0 and b > 0 and abs(a - b) / max(a, b) * 100.0 <= tol_pct
    except (TypeError, ValueError):
        return False


def read_verdict(has_split_after: bool, matches: bool, measured_ok: bool):
    """فروعُ `§⑦` بحرفها — ولا فرعَ رابع."""
    if not measured_ok:
        return 7, "الفرعُ 3 — **لا قياس** (تعذّر الجلب) · يُعلَن ولا يُفسَّر"
    if has_split_after and matches:
        return 2, ("الفرعُ 1 — **مقياسان مختلفان لا خطأَ تعريف** ⇒ يُعاد فتحُ "
                   "المحور بتسجيلٍ جديدٍ على بياناتٍ غيرِ معدَّلة")
    return 0, ("الفرعُ 2 — **التفسيرُ البديلُ يسقط** ⇒ فرضيّةُ عطبِ التعريف تبقى "
               "بلا منازعٍ معروف · والحكمُ يبقى الفرعَ 3")


def main() -> int:
    tol = float(bot.CONFIG.get("FAISAL_LEVEL_TOL_PCT", 2.0))
    log("🧱📅🔬 قياسُ فرضيّة التقسيم — الملحق §⑦ (قراءةٌ فقط)")
    bad = selfcheck_readonly()
    log(f"   حارسُ القراءة: {'✅' if not bad else '🔴 ' + str(bad)}")
    if bad:
        return 7

    # ── D1 أحداثُ التقسيم (من دالّة الإنتاج نفسِها) ──────────────────────────
    sp = bot._fetch_splits(SYM)
    if sp is None:
        log(f"🔴 `D1` تعذّر جلبُ تقسيمات {SYM}")
        return 7
    try:
        items = [(str(d)[:10], float(v)) for d, v in sp.items()]
    except Exception:                                          # noqa: BLE001
        items = []
    log(f"   `D1` أحداثُ تقسيم {SYM}: **{len(items)}**")
    for d, v in items[-12:]:
        log(f"        {d}  ×{v}")
    after = [(d, v) for d, v in items if d > ASOF]
    log(f"   ومنها **بعد {ASOF}**: {len(after)} ⟶ {after if after else '— لا شيء'}")

    # ── D2 العاملُ المطلوب مقابل عاملِ التقسيم الفعليّ ───────────────────────
    nf_w = needed_factor(REF_WEEKLY, MEASURED)
    nf_d = needed_factor(REF_DAILY, MEASURED)
    prod = 1.0
    for _, v in after:
        prod *= v
    scale = bot._split_scale_factor(sp, ASOF)
    log(f"   `D2` العاملُ المطلوب: أسبوعيّ {REF_WEEKLY}÷{MEASURED} = **{nf_w}** · "
        f"يوميّ {REF_DAILY}÷{MEASURED} = **{nf_d}**")
    log(f"        حاصلُ ضربِ نِسَب ما بعد التاريخ = **{round(prod, 4)}** · "
        f"و`_split_scale_factor` الإنتاجيّة = **{scale}**")
    matches = bool(after) and (within(prod, nf_w, tol) or within(prod, nf_d, tol)
                               or within(1.0 / prod if prod else 0, nf_w, tol))
    log(f"        يطابق داخلَ {tol}%؟ **{'نعم' if matches else 'لا'}**")

    # ── D3 شكلُ القاع (وصفيٌّ لا يحكم) ───────────────────────────────────────
    hist = bot.download_history([SYM])
    df0 = (hist or {}).get(SYM)
    if df0 is None or len(df0) < 60:
        log("⚠️ `D3` تعذّرت الشموع — يُعلَن ولا يُخمَّن")
    else:
        d = dt.date.fromisoformat(ASOF)
        keep = [(x.date() if hasattr(x, "date") else x) <= d for x in df0.index]
        df = df0[keep]
        lo = df["Low"].astype(float)
        k = int(lo.values.argmin()) if len(lo) else -1
        if k >= 0:
            row = df.iloc[k]
            gap = (float(row["Close"]) / float(row["Low"]) - 1.0) * 100.0
            log(f"   `D3` قاعُ المدى: {str(df.index[k])[:10]} · Low={float(row['Low']):.4f}"
                f" · Close={float(row['Close']):.4f} ⇒ الإغلاقُ أعلى من الذيل بـ"
                f"**{gap:.1f}%**")
            lo25 = lo.tail(25)
            k25 = int(lo25.values.argmin())
            log(f"        وأدنى قاعٍ في آخر 25 جلسة: {str(lo25.index[k25])[:10]} ·"
                f" {float(lo25.iloc[k25]):.4f}")
            below = int((df["Close"].astype(float).tail(25) < REF_WEEKLY).sum())
            log(f"        وجلساتٌ أغلقت تحت {REF_WEEKLY} من آخر 25: **{below}**")

    rc, txt = read_verdict(bool(after), matches, True)
    log("")
    log("═══ الحكم ═══")
    log(f"JUDGE rc={rc} · {txt}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
