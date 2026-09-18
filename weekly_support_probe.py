# -*- coding: utf-8 -*-
"""🧱📅 `T-WKSUP` — مِجَسُّ **الدعم الأسبوعيّ** (العقد `weekly_support_prereg.md`).

**قراءةٌ فقط:** لا كتابةَ حالةٍ · لا إرسالَ تلغرام · لا سرَّ · لا مسَّ إنتاج.
يُشغَّل يدويًّا بـ`weekly_support.yml`.

يقيس تعريفَين على **نفس البيانات ونفس القصّ** (‏`V-W5`):
  • **`W-SWING` 🥇** = `pivot_stability` **نفسُها** على `resample_ohlc(df, "W")`
    لكن على **آخر `look_wk` شمعةٍ أسبوعيّة** — فنافذةُ الدالّة تصير `min(25, look_wk)`
    = `look_wk` **بلا مسِّ `CONFIG`** (‏`V-W3`).
  • **`W-MIN`** = أدنى قاعٍ في **كلّ** التاريخ الأسبوعيّ = التنفيذُ الساذج (شاهدُ
    ضبطٍ **يُنشَر ولا يُشحَن**).

والنافذةُ **مُشتقّةٌ بالحساب لا مكتوبةً بيدي** (‏`V-W4`): `PIVOT_LOOKBACK // 5`.

رموزُ الخروج: 0 = الفرعُ 1 · 2 = الفرعُ 2 · 3 = الفرعُ 3 · 5 = حارسٌ سقط ·
7 = تغطيةٌ ناقصة.
"""
import datetime as dt
import os
import sys

import Super_stock as bot

# ── مرجعُ فيصل الموثَّق (`X_20260905_03` · الكاتالوج §خامس وعشرون) ──────────────
REF_SYM = (os.getenv("WKSUP_SYMBOL") or "PPBT").strip().upper()
REF_ASOF = (os.getenv("WKSUP_ASOF") or "2026-09-05").strip()
REF_WEEKLY = 1.694        # 🔴 الأحمرُ على الشارت الأسبوعيّ
REF_DAILY = 1.682         # 🔴 الأحمرُ الأدنى على اليوميّ
REF_AGREE = 1.70          # «يتفقان على 1.70»
REF_WEEKLY_LOW = 1.160    # القاعُ الظاهر أسبوعيًّا = ما يعطيه التنفيذُ الساذج
WS3_LO, WS3_HI = 5.0, 70.0   # حصّةُ الإطلاق المقبولة
WS4_MIN = 30.0               # أدنى حصّةِ افتراقٍ بين التعريفين


def log(m: str) -> None:
    print(m, flush=True)


# ── ⓪ حرّاسٌ تُطبَع قبل أيّ رقم ────────────────────────────────────────────────
def selfcheck_readonly() -> list:
    """`V-W1`: صفرُ كتابةِ حالةٍ وصفرُ إرسالٍ في هذي الوحدة (‏AST لا نصّ).
    وما لا يُثبَت أنه قراءةٌ **يُعَدّ كتابة** (تشديدُ حارسِ `optrade_arms`)."""
    import ast
    bad = []
    tree = ast.parse(open(__file__, encoding="utf-8").read())
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            nm = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
            if nm in ("send_telegram", "git_save", "save_watchlist"):
                bad.append(f"نداءٌ محرَّم: {nm}")
            if nm == "open":
                mode = None
                if len(n.args) > 1:
                    mode = getattr(n.args[1], "value", "؟")
                for k in n.keywords:
                    if k.arg == "mode":
                        mode = getattr(k.value, "value", "؟")
                if mode is not None and "r" not in str(mode):
                    bad.append(f"فتحٌ بوضعٍ غيرِ قراءة: {mode}")
    # 🐞 الحارسُ كان **يهزم نفسَه**: يبحث عن اسم السرّ وهو مكتوبٌ في سطر البحث
    #    ⇒ يسقط دائمًا. فيُركَّب الاسمُ من شطرَين ولا يُكتَب حرفيًّا.
    _tok = "TELEGRAM_BOT" + "_TOKEN"
    _chat = "TELEGRAM_CHAT" + "_ID"
    _own = open(__file__, encoding="utf-8").read()
    for _k in (_tok, _chat):
        if _own.count(_k) > 1:          # مرّةٌ واحدةٌ = هذا السطرُ نفسُه
            bad.append(f"ذكرُ سرٍّ: {_k}")
    return bad


def wk_window() -> int:
    """`V-W4`: النافذةُ الأسبوعيّة **مُشتقّة** — 25 جلسةً ÷ 5 = 5 أسابيع."""
    return max(2, int(bot.CONFIG["PIVOT_LOOKBACK"]) // 5)


# ── ① التعريفان — نقيّان ويُقاسان على نفس `df` ─────────────────────────────────
def w_swing(df, look_wk: int):
    """`W-SWING`: `pivot_stability` على آخر `look_wk` شمعةٍ أسبوعيّة."""
    try:
        wk = bot.resample_ohlc(df, "W")
        if wk is None or len(wk) < 2:
            return None
        lo = wk["Low"].values.astype(float)
        cl = wk["Close"].values.astype(float)
        ps = bot.pivot_stability(lo[-look_wk:], cl[-look_wk:])
        return None if not ps else round(float(ps["pivot"]), 4)
    except Exception:                                      # noqa: BLE001
        return None


def w_min(df):
    """`W-MIN`: أدنى قاعٍ أسبوعيٍّ في **كلّ** المتاح (التنفيذُ الساذج)."""
    try:
        wk = bot.resample_ohlc(df, "W")
        if wk is None or len(wk) < 2:
            return None
        return round(float(wk["Low"].values.astype(float).min()), 4)
    except Exception:                                      # noqa: BLE001
        return None


def d_pivot(df):
    """الدعمُ اليوميّ = **نفسُ ما يستعمله الإنتاج** (`pivot_stability` كاملةً)."""
    try:
        lo = df["Low"].values.astype(float)
        cl = df["Close"].values.astype(float)
        ps = bot.pivot_stability(lo, cl)
        return None if not ps else round(float(ps["pivot"]), 4)
    except Exception:                                      # noqa: BLE001
        return None


def cut_asof(df, asof: str):
    """قصُّ البيانات عند تاريخٍ — **إلزاميّ** (‏`§③`: شارتُ اليوم شارتٌ آخر)."""
    try:
        d = dt.date.fromisoformat(asof)
        idx = df.index
        keep = [ (x.date() if hasattr(x, "date") else x) <= d for x in idx ]
        out = df[keep]
        return out if len(out) >= 30 else None
    except Exception:                                      # noqa: BLE001
        return None


def within(a, b, tol_pct: float) -> bool:
    try:
        a, b = float(a), float(b)
        return a > 0 and b > 0 and abs(a - b) / max(a, b) * 100.0 <= tol_pct
    except (TypeError, ValueError):
        return False


# ── ② الحكم — دالّةٌ نقيّةٌ تطبّق `§④` بحرفه ────────────────────────────────────
def read_verdict(ws1: bool, ws2: bool, ws3: bool, ws4: bool):
    """الفروعُ الثلاثةُ كما في `§④` — ولا يُخترَع فرعٌ رابع."""
    if not ws1:
        return 3, "الفرعُ 3 — تسقط `WS1` ⇒ **لا يُشحَن شيء** · ولا تُعاير النافذةُ لتعبر"
    if ws1 and ws2 and ws3:
        return 0, "الفرعُ 1 — `WS1` و`WS2` تعبران ⇒ **يُشحَن** الحقلُ عرضًا"
    if ws1 and not ws3:
        return 2, "الفرعُ 2 — تعبر `WS1` وتسقط `WS3` ⇒ يُشحَن الحقلُ **ويُكتَم السطر**"
    return 2, "الفرعُ 2 — `WS1` تعبر و`WS2` لا ⇒ يُشحَن الحقلُ **ويُكتَم السطر**"


def main() -> int:
    tol = float(bot.CONFIG.get("FAISAL_LEVEL_TOL_PCT", 2.0))
    look = wk_window()
    log("🧱📅 T-WKSUP — مِجَسُّ الدعم الأسبوعيّ (قراءةٌ فقط)")
    log(f"   العقد: weekly_support_prereg.md · التسامح {tol}% "
        f"(`FAISAL_LEVEL_TOL_PCT`)")
    log(f"   V-W4 النافذةُ مُشتقّة: PIVOT_LOOKBACK={bot.CONFIG['PIVOT_LOOKBACK']}"
        f" ÷ 5 = **{look} أسابيع**")

    bad = selfcheck_readonly()
    log(f"   V-W1 قراءةٌ فقط: {'✅' if not bad else '🔴 ' + str(bad)}")
    if bad:
        return 5
    if int(bot.CONFIG["PIVOT_LOOKBACK"]) != 25:
        log("   V-W3 🔴 PIVOT_LOOKBACK تحرّك عن 25 — يُوقَف")
        return 5
    log("   V-W3 ✅ PIVOT_LOOKBACK=25 كما هو (النافذةُ الأسبوعيّة بلا مسِّ CONFIG)")

    # ── المرحلةُ الأولى: مرجعُ فيصل الموثَّق ──────────────────────────────────
    log("")
    log(f"═══ ① `WS1`/`WS2` — {REF_SYM} as-of {REF_ASOF} ═══")
    hist = bot.download_history([REF_SYM])
    df0 = (hist or {}).get(REF_SYM)
    if df0 is None or len(df0) < 60:
        log(f"🔴 تغطية: تعذّر جلبُ {REF_SYM} (‏{0 if df0 is None else len(df0)} شمعة)")
        return 7
    df = cut_asof(df0, REF_ASOF)
    if df is None:
        log(f"🔴 تغطية: القصُّ عند {REF_ASOF} لا يترك بياناتٍ كافية")
        return 7
    log(f"   V-W6 تغطية: {len(df0)} شمعةً خامًا ⟶ {len(df)} بعد القصّ "
        f"(آخرُها {str(df.index[-1])[:10]})")

    sw, mn, dp = w_swing(df, look), w_min(df), d_pivot(df)
    log(f"   W-SWING = {sw}   (مرجعُ فيصل {REF_WEEKLY})")
    log(f"   W-MIN   = {mn}   (القاعُ الظاهر {REF_WEEKLY_LOW} — الساذج)")
    log(f"   الدعمُ اليوميّ = {dp}   (مرجعُ فيصل {REF_DAILY})")

    ws1 = within(sw, REF_WEEKLY, tol)
    ag = bot.support_agreement(dp, sw)
    ws2 = bool(ag.get("agree")) and within(ag.get("level") or 0, REF_AGREE, tol)
    log(f"   `WS1` {'✅' if ws1 else '🔴'} — "
        f"فرقُ W-SWING عن {REF_WEEKLY} = "
        f"{'—' if not sw else round(abs(sw-REF_WEEKLY)/max(sw,REF_WEEKLY)*100,2)}%")
    log(f"   `WS2` {'✅' if ws2 else '🔴'} — التوافق: {ag}")
    naive_ok = within(mn, REF_WEEKLY_LOW, tol)
    log(f"   شاهدُ الضبط: W-MIN يطابق القاعَ الظاهر؟ "
        f"{'نعم ⇒ الساذجُ يكذب كما أُعلن' if naive_ok else 'لا'}")

    # ── المرحلةُ الثانية: القائمةُ الحيّة ─────────────────────────────────────
    log("")
    log("═══ ② `WS3`/`WS4` — القائمةُ الحيّة (‏اليوم، بلا قصّ) ═══")
    wl = bot.load_watchlist()
    syms = [s.get("symbol") for s in (wl.get("stocks") or []) if s.get("symbol")]
    log(f"   رموزُ القائمة: {len(syms)}")
    hist2 = bot.download_history(syms) if syms else {}
    fire = diverge = seen = 0
    rows = []
    for s in (wl.get("stocks") or []):
        sym = s.get("symbol")
        d2 = (hist2 or {}).get(sym)
        if d2 is None or len(d2) < 60:
            continue
        seen += 1
        sw2, mn2 = w_swing(d2, look), w_min(d2)
        dp2 = float(s.get("pivot") or 0) or d_pivot(d2)
        a2 = bot.support_agreement(dp2, sw2)
        if a2.get("agree"):
            fire += 1
        if sw2 is not None and mn2 is not None and abs(sw2 - mn2) > 1e-9:
            diverge += 1
        rows.append((sym, dp2, sw2, mn2, a2.get("agree"), a2.get("gap_pct")))
    if not seen:
        log("🔴 تغطية: صفرُ رمزٍ نجح جلبُه")
        return 7
    fr = fire / seen * 100.0
    dv = diverge / seen * 100.0
    log(f"   V-W6 تغطية: {seen} من {len(syms)} نجح جلبُها")
    log(f"   حصّةُ الإطلاق (`WS3`) = {fr:.1f}%  (المدى المقبول "
        f"{WS3_LO}-{WS3_HI}%)")
    log(f"   حصّةُ الافتراق (`WS4`) = {dv:.1f}%  (الحدُّ {WS4_MIN}%)")
    ws3 = WS3_LO <= fr <= WS3_HI
    ws4 = dv >= WS4_MIN
    log("")
    log("   الرمز   اليوميّ  W-SWING   W-MIN   توافق  الفرق%")
    for sym, a, b, c, ok, g in rows[:25]:
        log(f"   {str(sym):7s} {str(a):8s} {str(b):8s} {str(c):8s} "
            f"{'✅' if ok else '—':5s} {g}")
    if len(rows) > 25:
        log(f"   … و{len(rows)-25} رمزًا (قُصّ العرضُ ويُعلَن عدَدُه)")

    rc, txt = read_verdict(ws1, ws2, ws3, ws4)
    log("")
    log("═══ الحكم ═══")
    log(f"   `WS1`={ws1} · `WS2`={ws2} · `WS3`={ws3} ({fr:.1f}%) · "
        f"`WS4`={ws4} ({dv:.1f}%)")
    log(f"JUDGE rc={rc} · {txt}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
