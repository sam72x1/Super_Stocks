# -*- coding: utf-8 -*-
"""🌊⏰ `T-WAVES` — «موجات السهم بتوقيتنا» على سهم الماركت (العقد `waves_prereg.md` + الملحق `§⑫`).

**قراءةٌ/بحثٌ فقط · صفرُ مسٍّ بالإنتاج · لا `LOGIC_VERSION` · ولا يُشحَن شيءٌ مهما كانت
النتيجة.** يفتح محورَ `T-SESSIONS` **لدعوى أخرى** بشروطه الثلاثة، و`sessions_probe.py` يبقى
مُغلَقًا يخرج ‏8.

🔗 **وكلُّ مستورَدٍ يُنادى بالاسم (‏«بُنيت لـ…» في العقد §②):**
`link100_probe.scan_year` (‏المجتمعُ وشاهدُ `CX` — الدالّةُ التي أنتجت مرساةَ `NL_UP`) ·
`link100_probe.splits_of` · `tier_fwd_report.fetch_day` (‏شموعُ دقيقةِ يومٍ كامل بـ`adjusted=false`)
· `opcurve_probe.ny_hour` · `market_calendar.session_info` · `kasih_scan.wilson` ·
`optrade_arms.no_config_assign` · `tc_yield_arms.production_untouched`.

**رموزُ الخروج (§⑫-ⓙ):** 0 حكم (الفرعُ 1 أو 2) · 2 لا مفتاح · 5 حارس (‏`V-W3` · `V-W5` ·
`V-W6` · `V-W7` · `V-W8`) · 7 الهُويّة (`V-W1`) · 9 «لا قياس» (الفرعُ 3).
"""
from __future__ import annotations

import ast
import csv
import datetime as dt
import math
import os
from collections import Counter

import link100_probe as LK                                      # بالاسم
from kasih_scan import NY, wilson                               # بالاسم
from market_calendar import (EARLY_CLOSE_COUNT_BY_YEAR, EARLY_CLOSES,  # بالاسم
                             session_info)
from opcurve_probe import ny_hour                               # بالاسم
from optrade_arms import no_config_assign                       # بالاسم
from tc_yield_arms import production_untouched                  # بالاسم
from tier_fwd_report import fetch_day                           # بالاسم

# ───────────────────────── الثوابتُ المُغلَقة بالعقد ──────────────────────────
YEARS = ("2023", "2024", "2025")          # §② — ثابتةٌ ولا تُقرأ من البيئة (`V-W7`)
OPEN_H, CLOSE_H = 9.5, 16.0               # الجلسةُ النظاميّة — ‏390 دقيقة
PM_OPEN_H = 4.0                           # البريماركت [04:00, 09:30) — ‏330 دقيقة
WINDOWS = (("09:30-10", 9.5, 10.0), ("10-11", 10.0, 11.0), ("11-12", 11.0, 12.0),
           ("12-13", 12.0, 13.0), ("13-14", 13.0, 14.0), ("14-15", 14.0, 15.0),
           ("15-16", 15.0, 16.0))         # §③-2 — سبعٌ ولا ثامنة
PM_WINDOWS = (("04-08", 4.0, 8.0), ("08-09", 8.0, 9.0), ("09-09:30", 9.0, 9.5))
W1, W2, W3 = "08-09", "09:30-10", "11-12"
NEIGHBORS = ("10-11", "12-13")            # `C-NEIGH`
WD4_WIN = "10-11"                         # القراءةُ الحرفيّةُ شتاءً (‏EST)
AFTER_NOON_H = 12.0                       # `WD1` «والأخيرة»
RATIO_MIN = 1.5                           # `WV1` — رقمُ `T-SESSIONS` ولم يُرخَ
ALPHA_EACH = 0.025                        # `WV2` — بونفيروني ‏0.05 ÷ 2
FLOOR = 150                               # §⑥-3
YEAR_MIN = 50                             # `WV3`
MIN_COVER = 0.90                          # `V-W2`
MARKET_X = 2.0                            # §② «سهمُ الماركت» (= `LK.EXPL_X`)
OUT_ROWS = "waves_rows.tsv"

RC_OK, RC_NOKEY, RC_GUARD, RC_IDENT, RC_NOJUDGE = 0, 2, 5, 7, 9


def log(m: str = "") -> None:
    print(m, flush=True)


# ───────────────────────── حرّاسٌ (‏§⑦) ───────────────────────────────────────
def selfcheck_readonly(src: str | None = None) -> bool:
    """`V-W5` — **قراءةٌ فقط** بالـAST: صفرُ إرسالٍ وصفرُ كتابةِ حالة.

    ما لا يُثبَت أنه قراءةٌ **يُعَدّ كتابة** (وضعٌ مُمرَّرٌ متغيّرًا يُرفَض) · والوضعُ الغائبُ
    قراءةٌ يقينًا · والكتابةُ لا تمرّ إلّا إلى `OUT_ROWS` — **مُخرَجُ قياسٍ لا حالةَ إنتاج**."""
    write_ok = {"OUT_ROWS"}
    if src is None:
        src = open(os.path.abspath(__file__), encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        name = getattr(n.func, "id", None) or getattr(n.func, "attr", None) or ""
        if name in ("send_telegram", "send_telegram_document", "git_save",
                    "save_watchlist", "save_op_entry_state", "record_new_alerts"):
            return False
        if name == "open":
            mode = n.args[1] if len(n.args) > 1 else None
            for kw in n.keywords or []:
                if kw.arg == "mode":
                    mode = kw.value
            if mode is None:
                continue
            if not (isinstance(mode, ast.Constant) and isinstance(mode.value, str)):
                return False
            if set(mode.value) <= set("rbt"):
                continue
            tgt = n.args[0] if n.args else None
            if not (isinstance(tgt, ast.Name) and tgt.id in write_ok):
                return False
    return True


def importers(root: str = ".", me: str = "waves_probe") -> list:
    """`V-W6`-ب — ملفّاتُ المستودع (‏المستوى الأعلى) التي **تستورد** هذي الأداة، بالـAST.

    تُستثنى السويّةُ والأداةُ نفسُها · والإنتاجُ لا يستوردها ⇒ القائمةُ فارغة ·
    **وملفٌّ لا يُحلَّل يُعَدّ مستوردًا** (فاشلٌ-مغلق: ما لا يُثبَت نظافتُه لا يُفترَض)."""
    out = []
    for fn in sorted(os.listdir(root)):
        if not fn.endswith(".py") or fn in (me + ".py", "test_bot.py"):
            continue
        try:
            tree = ast.parse(open(os.path.join(root, fn), encoding="utf-8").read())
        except (OSError, SyntaxError, ValueError):
            out.append(fn)
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Import) and any(a.name.split(".")[0] == me
                                                 for a in n.names):
                out.append(fn)
                break
            if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == me:
                out.append(fn)
                break
    return out


def early_complete(years=YEARS, table=None, pinned=None) -> tuple:
    """`V-W8` (‏§⑫-ⓝ) — جدولُ الإغلاق المبكّر **مكتملٌ لكلّ سنةٍ من المجتمع**: عددُ أيّامه في
    `EARLY_CLOSES` يساوي المثبَّتَ في `EARLY_CLOSE_COUNT_BY_YEAR`، **والسنةُ حاضرةٌ في المثبَّت**
    (غيابُها = جدولٌ لم يُمَدّ ⇒ سقوط). نقيّة — والجدولان محقونان للاختبار."""
    table = EARLY_CLOSES if table is None else table
    pinned = EARLY_CLOSE_COUNT_BY_YEAR if pinned is None else pinned
    got = {y: sum(1 for d in table if str(d).startswith(y)) for y in years}
    ok = all(int(y) in pinned and got[y] == pinned[int(y)] for y in years)
    return ok, got


# ───────────────────────── الدوالُّ النقيّة (‏§③ · §⑤) ────────────────────────
def time_share(lo: float, hi: float, open_h: float = OPEN_H,
               close_h: float = CLOSE_H) -> float:
    """`C-TIME` — الحصّةُ **الزمنيّة** للنافذة من الجلسة بالنسبة المئويّة — **تُحسَب من الحدود
    لا تُكتَب باليد** (‏`V-W3`). نقيّة."""
    span = close_h - open_h
    if span <= 0:
        return 0.0
    return max(0.0, min(hi, close_h) - max(lo, open_h)) / span * 100.0


def window_of(h, windows=WINDOWS):
    """النافذةُ التي تقع فيها ساعةُ نيويورك — `None` خارجها. نقيّة."""
    if h is None:
        return None
    for lab, lo, hi in windows:
        if lo <= h < hi:
            return lab
    return None


def ny_tzname(ms: int) -> str:
    """`EDT` أو `EST` للحظةٍ بالملّي (‏`zoneinfo` لا إزاحةٌ ثابتة — §⑫-ⓕ)."""
    return dt.datetime.fromtimestamp(int(ms) / 1000.0, tz=NY).tzname() or "?"


def session_extremes(bars, hour_fn=ny_hour, tz_fn=ny_tzname):
    """أعلى الجلسة النظاميّة وأدناها وأعلى البريماركت **ولحظةُ كلٍّ منها** (‏§③).

    - الجلسةُ = الدقائقُ التي تبدأ في [09:30, 16:00) نيويورك · والبريماركت [04:00, 09:30).
    - **التعادلُ ⟵ الأبكر**، ويُحصى عددُ الدقائق المتعادلة على الأعلى.
    - `None` إن لم تكن دقيقةٌ نظاميّةٌ واحدة. نقيّة (الساعةُ والمنطقةُ محقونتان للاختبار)."""
    reg, pm = [], []
    for b in sorted(bars or [], key=lambda x: x[0]):
        try:
            h = hour_fn(b[0])
            hi, lo = float(b[2]), float(b[3])
        except (TypeError, ValueError, IndexError, OverflowError, OSError):
            continue
        if OPEN_H <= h < CLOSE_H:
            reg.append((h, hi, lo, b[0]))
        elif PM_OPEN_H <= h < OPEN_H:
            pm.append((h, hi))
    if not reg:
        return None
    top = max(r[1] for r in reg)
    bot = min(r[2] for r in reg)
    high_h = next(r[0] for r in reg if r[1] == top)
    low_h = next(r[0] for r in reg if r[2] == bot)
    pm_top = max((p[1] for p in pm), default=None)
    pm_h = next((p[0] for p in pm if p[1] == pm_top), None) if pm_top is not None else None
    return {"reg_high": top, "high_h": high_h,
            "ties": sum(1 for r in reg if r[1] == top),
            "reg_low": bot, "low_h": low_h,
            "pm_high": pm_top, "pm_high_h": pm_h,
            "n_reg": len(reg), "tz": tz_fn(reg[0][3])}


def is_market_stock(reg_high, prev_close, x: float = MARKET_X) -> bool:
    """§② — **أعلى الجلسة النظاميّة وحدَها ضعفُ إغلاق الأمس فأكثر.** نقيّة."""
    try:
        return float(prev_close) > 0 and float(reg_high) >= x * float(prev_close)
    except (TypeError, ValueError):
        return False


def split_blocked(sp, day: str, guard: int = LK.SPLIT_GUARD):
    """§⑫-ⓒ — تقسيمٌ في ‏±`guard` أيّامٍ تقويميّة ⇒ `True` · وتعذّرُ الجلب (`None`) ⇒ `None`
    (يُستبعَد ويُعَدّ منفصلًا) — **القاعدةُ نفسُها في `enrich_rows` بـ`T-LINK100`**. نقيّة."""
    if sp is None:
        return None
    d0 = dt.date.fromisoformat(day)
    for x, _rev in sp:
        try:
            if abs((dt.date.fromisoformat(str(x)[:10]) - d0).days) <= guard:
                return True
        except ValueError:
            continue
    return False


def binom_sf(k: int, n: int) -> float:
    """`P(X ≥ k)` لـ`X ~ Bin(n, ½)` — **ذيلٌ دقيقٌ بلا تقريب** (§⑫-ⓖ). نقيّة."""
    if n <= 0:
        return 1.0
    k = max(0, int(k))
    if k > n:
        return 0.0
    # قسمةُ عددين صحيحين في بايثون مقرَّبةٌ تقريبًا صحيحًا مهما كبُرا — و`float(2 ** n)`
    # كان يفيض (`OverflowError`) فوق ‏n = 1023.
    return sum(math.comb(n, i) for i in range(k, n + 1)) / (2 ** n)


def bump_test(n3: int, n_nb: int, alpha: float = ALPHA_EACH) -> tuple:
    """`WV2` لجارةٍ واحدة — **تفوّقٌ صارم** (`n3 > n_nb`) **و** `p ≤ alpha`. نقيّة."""
    p = binom_sf(n3, n3 + n_nb)
    return (n3 > n_nb and p <= alpha), p


def fmt_p(p: float) -> str:
    """`p` للطباعة — **والصفرُ العشريُّ لا يُطبَع صفرًا** (ذيلٌ أصغرُ من أصغر عددٍ عشريّ). نقيّة."""
    return "أقلُّ من 1e-300" if p == 0.0 else f"{p:.4g}"


def shares_of(labels, windows=WINDOWS) -> dict:
    """حصّةُ كلّ نافذةٍ من قائمةِ تسمياتٍ (‏بالنسبة المئويّة) ومعها العدد. نقيّة."""
    c = Counter(x for x in labels if x)
    n = sum(c.values())
    return {lab: (c.get(lab, 0), (c.get(lab, 0) / n * 100.0) if n else 0.0)
            for lab, _lo, _hi in windows}


def read_verdict(n: int, cover: float, share3: float, wlo3: float, tshare3: float,
                 bumps_ok, years_ok: bool, guards_ok: bool = True) -> dict:
    """فروعُ §⑥ بحرفها — ثلاثةٌ ولا رابع. نقيّةٌ ومقفولةٌ بجدول حقيقة."""
    if (not guards_ok) or n < FLOOR or cover < MIN_COVER:
        return {"branch": 3, "rc": RC_NOJUDGE,
                "text": f"الفرعُ 3 «لا قياس» — أسهمُ الماركت المقيسة {n} (الحدّ {FLOOR}) · "
                        f"تغطيةُ الدقيقة {cover * 100:.1f}% (الحدّ {MIN_COVER * 100:.0f}%)"
                        f"{' · وحارسٌ ساقط' if not guards_ok else ''} ⇒ يُعلَن ولا يُفسَّر"}
    wv1 = share3 >= RATIO_MIN * tshare3 and wlo3 > tshare3
    wv2 = bool(bumps_ok) and all(bumps_ok)
    wv3 = bool(years_ok)
    if wv1 and wv2 and wv3:
        return {"branch": 1, "rc": RC_OK,
                "text": f"الفرعُ 1 «موجةٌ مقيسة» — WV1 ✅ ({share3:.2f}% · الحدُّ الأدنى "
                        f"{wlo3:.2f}%) · WV2 ✅ · WV3 ✅ ⇒ **يُعرَض على المالك وصفًا · لا بوّابةَ "
                        f"ولا سطرَ عرضٍ بلا أمرٍ مستقلّ**"}
    neg = share3 <= tshare3
    return {"branch": 2, "rc": RC_OK,
            "text": f"الفرعُ 2 «لا تُثبَت»{' — **سالبة**' if neg else ''} — حصّةُ {W3} "
                    f"{share3:.2f}% مقابل {tshare3:.2f}% زمنيًّا · WV1 {'✅' if wv1 else '❌'} · "
                    f"WV2 {'✅' if wv2 else '❌'} · WV3 {'✅' if wv3 else '❌'} ⇒ **يُوصى بإعادة "
                    f"إغلاق المحور**"}


# ───────────────────────── التشغيل ───────────────────────────────────────────
def run(key: str, *, scan=None, fetch=None, splits=None, sinfo=None, hour_fn=None,
        tz_fn=None, prod=None, imp=None, early=None, dry: bool = False,
        write_rows: bool = True) -> int:
    """المسارُ كاملًا **بجالبين محقونين** (للاختبار بلا شبكة) — والافتراضُ هو الحيّ بالاسم."""
    scan = scan or LK.scan_year
    fetch = fetch or fetch_day
    splits = splits or LK.splits_of
    sinfo = sinfo or session_info
    hour_fn = hour_fn or ny_hour
    tz_fn = tz_fn or ny_tzname
    prod = prod or production_untouched
    imp = imp or importers
    early = early or early_complete

    log("🌊⏰ `T-WAVES` — «موجات السهم بتوقيتنا» على سهم الماركت (العقد waves_prereg.md + §⑫)")
    log(f"   السنوات {' · '.join(YEARS)} · W3 = {W3} · WV1 {RATIO_MIN}× · WV2 α={ALPHA_EACH} "
        f"لكلّ جارة · الأرضيّة {FLOOR} · السنة {YEAR_MIN}")

    # ── `V-W5`/`V-W6` قبل أيّ رقم ──────────────────────────────────────────
    src = open(os.path.abspath(__file__), encoding="utf-8").read()
    ro, nc = selfcheck_readonly(src), no_config_assign(src)
    prod_ok, cur, base = prod()
    who = imp()
    log(f"   🔒 V-W5 قراءةٌ فقط={ro} · صفرُ إسنادٍ إلى CONFIG={nc} · "
        f"V-W6 الإنتاجُ بت-بت={prod_ok} ({cur} مقابل {base}) · "
        f"مستوردو الأداة={who or 'لا أحد'}")
    if not (ro and nc and prod_ok) or who:
        log(f"⛔ حارسٌ ساقطٌ قبل أيّ قياس — خروج {RC_GUARD}")
        return RC_GUARD

    # ── `V-W8` (‏§⑫-ⓝ) اكتمالُ جدول الإغلاق المبكّر لسنوات المجتمع ─────────
    e_ok, e_got = early()
    log(f"   🔒 V-W8 أيّامُ الإغلاق المبكّر في التقويم: {e_got} · المثبَّت "
        f"{ {y: EARLY_CLOSE_COUNT_BY_YEAR.get(int(y)) for y in YEARS} } ⇒ {e_ok}")
    if not e_ok:
        log(f"⛔ V-W8 — جدولُ الإغلاق المبكّر ناقصٌ لسنةٍ من المجتمع ⇒ نصفُ جلسةٍ يُقرأ "
            f"«نظاميًّا» صامتًا — خروج {RC_GUARD}")
        return RC_GUARD

    # ── `V-W3` الحصصُ الزمنيّة ─────────────────────────────────────────────
    tshare = {lab: time_share(lo, hi) for lab, lo, hi in WINDOWS}
    tot = sum(tshare.values())
    log("   🔒 V-W3 الحصصُ الزمنيّة: " +
        " · ".join(f"{k} {v:.2f}%" for k, v in tshare.items()) + f" · المجموع {tot:.2f}%")
    if abs(tot - 100.0) > 0.01:
        log(f"⛔ V-W3 — مجموعُ الحصص {tot:.4f}% ⇒ تعريفُ نافذةٍ مكسور — خروج {RC_GUARD}")
        return RC_GUARD
    pm_share = {lab: time_share(lo, hi, PM_OPEN_H, OPEN_H) for lab, lo, hi in PM_WINDOWS}

    # ── `V-W1` هُويّةُ المجتمع بت-بت ثمّ `V-W7` ────────────────────────────
    scans = {}
    for y in YEARS:
        s = scan(y, key)
        ident = (s.get("days"), s.get("got"), s.get("raw"), len(s.get("events") or []))
        want = tuple(LK.NL_UP[y])
        log(f"   🔒 V-W1 {y}: (أيّام · جُلبت · خام · بعد الطيّ) = {ident} · المنشور {want}")
        if ident != want:
            if s.get("got") != s.get("days"):
                log(f"   ⚠️ أيّامٌ لم تُجلَب: {(s.get('days') or 0) - (s.get('got') or 0)} ⇒ "
                    f"**عطلُ جلبٍ لا اختلافُ مجتمع** — يُعاد التشغيل ولا يُعدَّل شيء")
            log(f"⛔ V-W1 — المجتمعُ ليس مجتمعَ `T-LINK100` بت-بت — خروج {RC_IDENT} قبل أيّ نسبة")
            return RC_IDENT
        scans[y] = s
    bad = [e.get("day") for y in YEARS for e in scans[y]["events"]
           if not str(e.get("day", "")).startswith(y) or str(e.get("day", "")).startswith("2026")]
    log(f"   🔒 V-W7 صفوفٌ خارج سنواتها أو من 2026: {len(bad)}")
    if bad:
        log(f"⛔ V-W7 — {bad[:5]} — خروج {RC_GUARD}")
        return RC_GUARD

    if dry:
        log("")
        log("🧪 وضعُ الجدوى (§⑫-ⓗ) — أعدادُ المجتمع فقط · **صفرُ دقيقةٍ تُجلَب وصفرُ نسبة**.")
        for y in YEARS:
            ev = scans[y]["events"]
            log(f"   {y}: أحداثٌ {len(ev)} · بشاهدٍ مقطعيّ {sum(1 for e in ev if e.get('ctrl'))}")
        return RC_OK

    # ── القياس (‏§③) ───────────────────────────────────────────────────────
    cnt, rows, scache = Counter(), [], {}
    for y in YEARS:
        for ev in scans[y]["events"]:
            sym, day = ev["sym"], ev["day"]
            if (sinfo(day) or {}).get("session_type") != "regular":
                cnt["early"] += 1
                continue
            if sym not in scache:
                scache[sym] = splits(sym, key)
            blk = split_blocked(scache[sym], day)
            if blk is None:
                cnt["split_unknown"] += 1
                continue
            if blk:
                cnt["split_block"] += 1
                continue
            cnt["eligible"] += 1
            ext = session_extremes(fetch(sym, day, key), hour_fn, tz_fn)
            if not ext:
                cnt["no_bars"] += 1
                continue
            cnt["with_bars"] += 1
            if not is_market_stock(ext["reg_high"], ev["prev_close"]):
                cnt["not_market"] += 1
                continue
            row = {"year": y, "day": day, "sym": sym, "prev_close": ev["prev_close"],
                   "x": ext["reg_high"] / ev["prev_close"], "high_h": ext["high_h"],
                   "win": window_of(ext["high_h"]), "ties": ext["ties"],
                   "low_h": ext["low_h"], "low_win": window_of(ext["low_h"]),
                   "pm_h": ext["pm_high_h"], "pm_win": window_of(ext["pm_high_h"], PM_WINDOWS),
                   "tz": ext["tz"], "ctrl": ev.get("ctrl") or "", "ctrl_h": None,
                   "ctrl_win": None}
            if row["ctrl"]:
                cext = session_extremes(fetch(row["ctrl"], day, key), hour_fn, tz_fn)
                if cext:
                    row["ctrl_h"] = cext["high_h"]
                    row["ctrl_win"] = window_of(cext["high_h"])
            rows.append(row)

    elig = cnt["eligible"]
    cover = cnt["with_bars"] / elig if elig else 0.0
    n = len(rows)
    log(f"   📐 الإغلاقُ المبكّر {cnt['early']} · تقسيمٌ ±{LK.SPLIT_GUARD}ي {cnt['split_block']} · "
        f"تقسيماتٌ تعذّر جلبُها {cnt['split_unknown']} · مؤهَّلٌ {elig}")
    log(f"   🔒 V-W2 تغطيةُ الدقيقة: {cnt['with_bars']} من {elig} = {cover * 100:.1f}% "
        f"(الحدّ {MIN_COVER * 100:.0f}%) · سقط بشرط «سهم الماركت» {cnt['not_market']} · "
        f"**أسهمُ الماركت المقيسة {n}**")
    tzc = Counter(r["tz"] for r in rows)
    log(f"   🔒 V-W4 نظامُ التوقيت: {dict(tzc)}" +
        ("  ⚠️ **أحدُهما صفرٌ ⇒ WD4 بلا معنى ويُقال**" if len(tzc) < 2 else ""))
    log(f"   ℹ️ تعادلٌ على الأعلى (أكثرُ من دقيقة): {sum(1 for r in rows if r['ties'] > 1)}")

    if write_rows:
        with open(OUT_ROWS, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, delimiter="\t")
            w.writerow(["year", "day", "sym", "prev_close", "reg_high_x", "high_h", "win",
                        "ties", "low_h", "low_win", "pm_high_h", "pm_win", "tz", "ctrl",
                        "ctrl_high_h", "ctrl_win"])
            for r in rows:
                w.writerow([r["year"], r["day"], r["sym"], f"{r['prev_close']:.4f}",
                            f"{r['x']:.4f}", f"{r['high_h']:.4f}", r["win"] or "", r["ties"],
                            f"{r['low_h']:.4f}", r["low_win"] or "",
                            "" if r["pm_h"] is None else f"{r['pm_h']:.4f}", r["pm_win"] or "",
                            r["tz"], r["ctrl"],
                            "" if r["ctrl_h"] is None else f"{r['ctrl_h']:.4f}",
                            r["ctrl_win"] or ""])
        log(f"   🧾 الصفوف: {OUT_ROWS} ({n} صفًّا)")

    if n < FLOOR or cover < MIN_COVER:
        v = read_verdict(n, cover, 0.0, 0.0, tshare[W3], [], False, True)
        log("")
        log(f"JUDGE {v['text']}")
        return v["rc"]

    # ── `S-OBS` مقابل `C-TIME` ─────────────────────────────────────────────
    obs = shares_of([r["win"] for r in rows])
    log("   📊 `S-OBS` المرصود مقابل `C-TIME` (والمقامُ مع كلّ نسبة):")
    for lab, lo, hi in WINDOWS:
        k, pc = obs[lab]
        lo95, hi95 = wilson(k, n)
        log(f"      {lab:>8} · {k:>4} من {n} = {pc:6.2f}% [{lo95:.2f}, {hi95:.2f}] · "
            f"زمنيًّا {tshare[lab]:6.2f}% · نسبة {pc / tshare[lab]:.2f}× · "
            f"لكلّ ساعة {k / (hi - lo):.1f}")

    # ── المعاييرُ الثلاثة (‏§⑤) ───────────────────────────────────────────
    k3, share3 = obs[W3]
    wlo3, _whi3 = wilson(k3, n)
    wv1 = share3 >= RATIO_MIN * tshare[W3] and wlo3 > tshare[W3]
    log(f"   🥇 WV1: {W3} = {share3:.2f}% (الحدّ {RATIO_MIN * tshare[W3]:.2f}%) · الحدُّ الأدنى "
        f"لـWilson {wlo3:.2f}% مقابل {tshare[W3]:.2f}% ⇒ {'✅' if wv1 else '❌'}")
    bumps = []
    for nb in NEIGHBORS:
        ok, p = bump_test(k3, obs[nb][0])
        bumps.append(ok)
        log(f"   🥇 WV2: {W3} {k3} مقابل {nb} {obs[nb][0]} · p = {fmt_p(p)} (الحدّ {ALPHA_EACH}) ⇒ "
            f"{'✅' if ok else '❌'}")
    years_ok = True
    for y in YEARS:
        yr = [r for r in rows if r["year"] == y]
        ky, sy = shares_of([r["win"] for r in yr])[W3]
        oky = len(yr) >= YEAR_MIN and sy > tshare[W3]
        years_ok = years_ok and oky
        log(f"   🥇 WV3 {y}: {W3} {ky} من {len(yr)} = {sy:.2f}% (زمنيًّا {tshare[W3]:.2f}% · "
            f"الحدّ الأدنى للمقام {YEAR_MIN}) ⇒ {'✅' if oky else '❌'}")

    # ── وصفيٌّ يُطبَع ولا يحكم (‏WD1-WD5) ──────────────────────────────────
    after = sum(1 for r in rows if r["high_h"] >= AFTER_NOON_H)
    t_after = time_share(AFTER_NOON_H, CLOSE_H)
    log(f"   ℹ️ WD1 «والأخيرة»: بعد 12:00 {after} من {n} = {after / n * 100:.2f}% مقابل "
        f"{t_after:.2f}% زمنيًّا")
    lows = shares_of([r["low_win"] for r in rows])
    log(f"   ℹ️ WD2 قيعانُ {W2}: {lows[W2][0]} من {n} = {lows[W2][1]:.2f}% مقابل "
        f"{tshare[W2]:.2f}% زمنيًّا")
    pm_rows = [r for r in rows if r["pm_win"]]
    pms = shares_of([r["pm_win"] for r in pm_rows], PM_WINDOWS)
    log(f"   ℹ️ WD3 قمّةُ البريماركت في {W1}: {pms[W1][0]} من {len(pm_rows)} = {pms[W1][1]:.2f}% "
        f"مقابل {pm_share[W1]:.2f}% زمنيًّا · بلا بريماركت {n - len(pm_rows)}")
    est = [r for r in rows if r["tz"] == "EST"]
    ke, se = shares_of([r["win"] for r in est])[WD4_WIN]
    log(f"   ℹ️ WD4 القراءةُ الحرفيّةُ شتاءً ({WD4_WIN} على أيّام EST): {ke} من {len(est)} = "
        f"{se:.2f}% مقابل {tshare[WD4_WIN]:.2f}% زمنيًّا")
    cx = [r for r in rows if r["ctrl_win"]]
    cxs = shares_of([r["ctrl_win"] for r in cx])
    cx_ok = [bump_test(cxs[W3][0], cxs[nb][0])[0] for nb in NEIGHBORS]
    log(f"   ℹ️ WD5 `C-CX`: تغطيةُ الشاهد {len(cx)} من {n} · {W3} {cxs[W3][0]} = "
        f"{cxs[W3][1]:.2f}% · نتوءٌ على الجارتين={all(cx_ok) if cx else '—'}")
    if cx:
        log("      التوزيعُ نفسُه على الشاهد: " +
            " · ".join(f"{lab} {cxs[lab][0]} ({cxs[lab][1]:.2f}%)" for lab, _lo, _hi in WINDOWS))

    # ── تنبّؤاتي (‏§⑩ · حسمُها الآليّ §⑫-ⓛ) — تُطبَع مكذَّبةً أو مؤكَّدة ────────
    dens = {lab: obs[lab][0] / (hi - lo) for lab, lo, hi in WINDOWS}
    preds = [("WP1", "WV1 يسقط", not wv1),
             ("WP2", f"WV2 يسقط وقممُ 10-11 أكثرُ من {W3}",
              (not all(bumps)) and obs["10-11"][0] > k3),
             ("WP3", f"{W2} أعلى النوافذ كثافةً لكلّ ساعة (بصرامة)",
              all(dens[W2] > v for lab, v in dens.items() if lab != W2)),
             ("WP4", "C-CX بلا نتوء", None if not cx else not all(cx_ok)),
             ("WP5", "أسهمُ الماركت 1,000 فأكثر", n >= 1000)]
    for pid, txt, ok in preds:
        verdict = "⚪ لا يُحسَم (صفرُ تغطية)" if ok is None else ("✅ مؤكَّد" if ok else "❌ مكذَّب")
        log(f"   🔮 {pid} «{txt}» ⇒ {verdict}")

    v = read_verdict(n, cover, share3, wlo3, tshare[W3], bumps, years_ok, True)
    log("")
    log(f"JUDGE {v['text']}")
    return v["rc"]


def main() -> int:
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        log(f"⛔ لا POLYGON_API_KEY — خروج {RC_NOKEY}")
        return RC_NOKEY
    return run(key, dry=os.environ.get("WAVES_DRY", "").strip() == "1",
               write_rows=os.environ.get("WAVES_TSV", "1").strip() != "0")


if __name__ == "__main__":
    raise SystemExit(main())
