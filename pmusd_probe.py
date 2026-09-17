#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🌅💧 `T-PMUSD` — هل سيولةُ البريماركت رابطٌ **قبل** الانفجار، أم أنها الانفجارُ نفسُه؟

العقدُ `pmusd_prereg.md` **مدفوعٌ ومدموجٌ قبل هذا الملفّ وقبل أيّ رقمٍ من موضوعه**.

🔑 **إعادةُ استعمالٍ بالاسم لا نسخ:** المجتمعُ والحدثُ والشاهدان والعتبةُ والحسمُ
كلُّها مستورَدةٌ من `link100_probe` ⇒ **هُويّةٌ لا شبيه**. والجديدُ بنيويًّا شيءٌ
واحد: **الطبقةُ الدقيقةُ تُجلَب للشاهد الذاتيّ `CC` ولِيوم `d−1`** — وهو ما لم
يُفعَل في `T-LINK100` فسقطت `pm_*` على «‏—».

🔒 **قراءةٌ فقط:** صفرُ إرسالٍ · صفرُ كتابةِ حالة · صفرُ إسنادٍ إلى `CONFIG`
(مُثبَتٌ بـ`selfcheck_readonly`/`no_config_assign` المستورَدتين) — والمُخرَجُ
نصٌّ على stdout يُنسَخ إلى `pmusd_result.md` **بجانب العقد لا فوقه**.
"""
import os
import sys

from link100_probe import (                                      # كلُّها بالاسم
    ALPHA, CC_BACK, CC_CLEAR, EXPL_X, HIST_BACK_DAYS, MIN_BUCKET_N,
    MIN_DAYS_COVER, MIN_MATCH, PRICE_LO, RATIO_MIN, SPLIT_GUARD,
    FEATURES as L_FEATURES,
    cell_pass, daily_feats, enrich, fetch_day, no_config_assign, pm_feats,
    scan_year, selfcheck_readonly, splits_of, ticker_daily, z_bonf,
)
from opcurve_probe import ny_hour                                # بالاسم

# ═══════════════ ⓪ الحدود — مثبَّتةٌ بالعقد §② و§⑥ ════════════════════════════
YEARS = [y.strip() for y in
         os.environ.get("PMUSD_YEARS", "2023,2024,2025").split(",") if y.strip()]
DRY = os.environ.get("PMUSD_DRY", "").strip() == "1"
PMUSD_CAP = int(os.environ.get("PMUSD_CAP", "1500"))   # سقفُ الطبقة الدقيقة/سنة

GOV_YEARS = ("2023", "2024", "2025")                   # الحكمُ يشترطها معًا
PUBLISHED = {"2023": 481, "2024": 655, "2025": 773}    # `V-U1` من `link100_result.md §①`
PM_COVER_MIN = 0.95                                    # `V-U4`
BARS_CACHE_MAX = 600                                   # حدُّ كاشِ الدقائق (FIFO)
KNOWN_RATIO = 1.5                                      # `PU3`
GOV_BUCKET = ">1M"                                     # السلّةُ الحاكمةُ لـ`pm_usd`
KNOWN_VOL, KNOWN_RET = "≥3", ">+20%"                   # العابرتان في `T-LINK100`

RC_OK, RC_NOKEY, RC_COVER, RC_NOEVENT = 0, 2, 3, 4
RC_POP, RC_GUARD, RC_NOVERDICT = 5, 6, 9

# الأذرعُ **مُغلَقةٌ** (§④) — لا تُضاف ذراعٌ بعد أيّ رقم.
ARMS = (("U-NOW", "u_now", "reg", True),      # حاكمةٌ (أ) — `E-REG` وحدَها
        ("U-PREV", "u_prev", "all", True),    # حاكمةٌ (ب) — سابقةٌ بالكامل
        ("U-RAW", "u_now", "all", False),     # وصفيّة — «الإصلاحُ الساذج»
        ("G-PREV", "g_prev", "all", False),   # وصفيّة
        ("G-NOW", "g_now", "reg", False))     # وصفيّة

_CALLS = {"stat": 0}                                   # عدّادُ نداءات الإحصاء


def _log(msg: str = "") -> None:
    print(msg, flush=True)


def _stat_enrich(ev_rows, ct_rows, feat):
    """غلافُ `enrich` بعدّاد — فوضعُ الجدوى يُثبَت **بعدّادٍ حقيقيّ** لا بدعوى."""
    _CALLS["stat"] += 1
    return enrich(ev_rows, ct_rows, feat)


def _stat_cell(e_cx, e_cc, z):
    _CALLS["stat"] += 1
    return cell_pass(e_cx, e_cc, z)


def _stat_z(n):
    _CALLS["stat"] += 1
    return z_bonf(n)


# ═══════════════ ① التعريفاتُ الجديدة (§③) ════════════════════════════════════
def pm_high(bars):
    """أعلى `high` بين شموع الدقيقة **قبل 09:30 نيويورك** — أو `None`."""
    pre = [b[2] for b in (bars or []) if ny_hour(b[0]) < 9.5]
    return max(pre) if pre else None


def is_pm_event(bars, prev_close, fetched=None):
    """`E-PM` — الانفجارُ وقع **قبل الجرس**. تُرجّع `(داخلَ E-PM، مجهول؟)`.

    🔴 **ملحقُ §⑫-2 — الفراغُ ليس نقصًا:** فشلُ الجلب (`bars is None`) أو غيابُ
    إغلاقِ الأمس **مجهولٌ** فيبقى داخلَ `E-PM` تحفّظًا (‏§⑧-6). أمّا جلبٌ
    **نجح** وجلستُه فارغةٌ قبل الجرس فمعناه أن السهمَ **لم يتداول بريماركتًا
    أصلًا** ⇒ الانفجارُ قطعًا لم يقع قبل الجرس ⇒ **`E-REG` ومعلومٌ لا مجهول**.
    واتّجاهُ التصحيح **ضدّ الفرضيّة**: يُدخل في الحاكمة (أ) صفوفًا بريماركتُها صفر."""
    ok = (bars is not None) if fetched is None else bool(fetched)
    if not ok or not prev_close:
        return True, True                                 # (داخلَ `E-PM`، مجهول)
    h = pm_high(bars)
    if h is None:
        return False, False                               # فراغٌ حقيقيّ ⇒ `E-REG`
    return (h / prev_close) >= EXPL_X, False


def known_of(f):
    """«المعروف» = اتّحادُ الميزتين العابرتين في `T-LINK100` (§④ · `C-KNOWN`)."""
    return bool(f.get("vol_x") == KNOWN_VOL or f.get("ret5") == KNOWN_RET)


def _zero_enc(val, ok, low):
    """الفراغُ الحقيقيُّ صفرٌ لا مجهول — **وصفيٌّ فقط** (ملحق §⑫-4).

    جلبٌ **نجح** وقيمةٌ `None` ⇒ لا تداولَ بريماركت ⇒ أدنى سلّة. وفشلُ الجلب
    يبقى `None`. 🔺 واتّجاهُ هذي القراءة **مع الفرضيّة** فهي لا تحكم."""
    if val is not None:
        return val
    return low if ok else None


def _pm_pair(bars_now, pc_now, bars_prev, pc_prev, ok_now=None, ok_prev=None):
    """مفاتيحُ الأذرع لصفٍّ واحد — من `pm_feats` بالاسم ‏+ القراءةُ الوصفيّة."""
    a = pm_feats(bars_now, pc_now)
    b = pm_feats(bars_prev, pc_prev)
    on = (bars_now is not None) if ok_now is None else bool(ok_now)
    op = (bars_prev is not None) if ok_prev is None else bool(ok_prev)
    return {"u_now": a["pm_usd"], "g_now": a["pm_gap"],
            "u_prev": b["pm_usd"], "g_prev": b["pm_gap"],
            # 🔑 بأسماء `T-LINK100` نفسِها ⇒ عدُّ الخلايا وإعادةُ الإنتاج
            "pm_usd": a["pm_usd"], "pm_gap": a["pm_gap"],
            # 🔻 القراءةُ الثانية **الوصفيّة** (ملحق §⑫-4) — تُطبَع ولا تحكم
            "u_now0": _zero_enc(a["pm_usd"], on, "<100k"),
            "g_now0": _zero_enc(a["pm_gap"], on, "<10%"),
            "u_prev0": _zero_enc(b["pm_usd"], op, "<100k"),
            "g_prev0": _zero_enc(b["pm_gap"], op, "<10%"),
            "fetch_ok": on}


_EMPTY_PM = {"u_now": None, "g_now": None, "u_prev": None, "g_prev": None,
             "pm_usd": None, "pm_gap": None, "u_now0": None, "g_now0": None,
             "u_prev0": None, "g_prev0": None, "fetch_ok": False}


# ═══════════════ ② الإثراءُ — الطبقةُ الدقيقةُ للشاهدَين ولِيوم `d−1` ══════════
def enrich_pm(events: list, key: str, cap: int) -> dict:         # noqa: PLR0912, PLR0915
    """المرّةُ الثانية — بنيةُ `link100_probe.enrich_rows` نفسُها ‏+ الطبقةُ الناقصة.

    🔑 الحارسُ والتاريخُ والميزاتُ بالدوالّ المستورَدة نفسِها، والفرقُ الوحيدُ
    **ستُّ جلباتِ دقيقةٍ لكلّ حدث** بدل واحدةٍ: الحدثُ و`d−1` · والشاهدُ
    المقطعيُّ ويومُه السابق · والشاهدُ الذاتيُّ ويومُه السابق."""
    import datetime as _dt

    ev_rows, cx_rows, cc_rows = [], [], []
    dropped_split = no_hist = no_cc = 0
    pm_used, calls, unknown = 0, 0, 0
    fetch_fail = empty_pm = has_pm = 0
    hcache, scache, bcache = {}, {}, {}

    def hist_of(sym, day):
        k = (sym, day)
        if k not in hcache:
            d0 = (_dt.date.fromisoformat(day)
                  - _dt.timedelta(days=HIST_BACK_DAYS)).isoformat()
            hcache[k] = ticker_daily(sym, d0, day, key)
        return hcache[k]

    def splits_cached(sym):
        if sym not in scache:
            scache[sym] = splits_of(sym, key)
        return scache[sym]

    def bars_of(sym, day):
        nonlocal calls
        k = (sym, day)
        if k not in bcache:
            bcache[k] = fetch_day(sym, day, key)                 # بالاسم
            calls += 1
            # 🔒 حدٌّ FIFO: إعادةُ الاستعمال **بين الأحداث** لا داخلَها، فالحدُّ
            #    لا يُضيع نداءً يُذكر ويمنع تضخّمَ الذاكرة إلى الجيجابايت.
            if len(bcache) > BARS_CACHE_MAX:
                bcache.pop(next(iter(bcache)))
        return bcache[k]

    for ev in events:
        sym, day = ev["sym"], ev["day"]
        sp = splits_cached(sym)
        d0 = _dt.date.fromisoformat(day)
        if sp is None:
            dropped_split += 1
            continue
        if any(abs((_dt.date.fromisoformat(x) - d0).days) <= SPLIT_GUARD
               for x, _rev in sp):
            dropped_split += 1
            continue
        h = hist_of(sym, day)
        if not h:
            no_hist += 1
            continue
        idx = next((k for k, b in enumerate(h) if b[0] == day), None)
        if idx is None or idx < 2:
            no_hist += 1
            continue
        rsp = any(0 <= (d0 - _dt.date.fromisoformat(x)).days <= 180
                  for x, rev in sp if rev)
        f = daily_feats(h, idx, rsp)
        if f is None:
            no_hist += 1
            continue
        f.update({"_sym": sym, "_day": day, "known": known_of(f)})
        f.update(_EMPTY_PM)

        # ── الشاهدُ الذاتيّ `CC` عند `d−21` (نفسُ شرط الخلوّ) ────────────────
        cf = None
        j = idx - CC_BACK
        if j >= 2:
            clear = True
            for k in range(max(1, idx - CC_CLEAR), j + 1):
                if h[k - 1][4] > 0 and h[k][2] / h[k - 1][4] >= EXPL_X:
                    clear = False
                    break
            if clear:
                cf = daily_feats(h, j, rsp)
                if cf:
                    cf.update({"_sym": sym, "_day": h[j][0],
                               "known": known_of(cf)})
                    cf.update(_EMPTY_PM)
                else:
                    no_cc += 1
            else:
                no_cc += 1
        else:
            no_cc += 1

        # ── الشاهدُ المقطعيّ `CX` ───────────────────────────────────────────
        cs, cxf, ci, ch = ev.get("ctrl"), None, None, None
        if cs:
            ch = hist_of(cs, day)
            ci = next((k for k, b in enumerate(ch or []) if b[0] == day), None)
            if ch and ci is not None and ci >= 2:
                csp = splits_cached(cs) or []
                crsp = any(0 <= (d0 - _dt.date.fromisoformat(x)).days <= 180
                           for x, rev in csp if rev)
                cxf = daily_feats(ch, ci, crsp)
                if cxf:
                    cxf.update({"_sym": cs, "_day": day, "known": known_of(cxf)})
                    cxf.update(_EMPTY_PM)

        # ── الطبقةُ الدقيقة — ستُّ جلباتٍ بسقفٍ مُعلَنٍ ويُطبَع ───────────────
        pm_done = False
        if pm_used < cap:
            eb = bars_of(sym, day)
            ebp = bars_of(sym, h[idx - 1][0])
            # 🔑 مرجعُ إغلاق الأمس **من `grouped` كما في `T-LINK100`** ⇒
            #    `U-RAW` تعيد رقمَه المنشور بمِسطرته لا بمِسطرةٍ ثانية.
            pc0 = ev.get("prev_close") or h[idx - 1][4]
            f.update(_pm_pair(eb, pc0, ebp, h[idx - 2][4]))
            inpm, unk = is_pm_event(eb, pc0)
            f["is_pm"] = inpm
            unknown += 1 if unk else 0
            # 🔎 ملحقُ §⑫-ⓓ — ثلاثةُ عدّاداتٍ تفرّق ما كان سطرٌ واحدٌ يخلطه
            if eb is None:
                fetch_fail += 1
            elif f["u_now"] is None:
                empty_pm += 1
            else:
                has_pm += 1
            if cxf is not None:
                cb = bars_of(cs, day)
                cbp = bars_of(cs, ch[ci - 1][0])
                cxf.update(_pm_pair(cb, ch[ci - 1][4], cbp, ch[ci - 2][4]))
            if cf is not None:
                jb = bars_of(sym, h[j][0])
                jbp = bars_of(sym, h[j - 1][0])
                cf.update(_pm_pair(jb, h[j - 1][4], jbp, h[j - 2][4]))
            pm_used += 1
            pm_done = True
        if not pm_done:
            f["is_pm"] = True            # مجهولٌ ⇒ داخلَ `E-PM` (متحفّظ)
            unknown += 1

        ev_rows.append(f)
        if cxf is not None:
            cx_rows.append(cxf)
        if cf is not None:
            cc_rows.append(cf)

    return {"ev": ev_rows, "cx": cx_rows, "cc": cc_rows,
            "dropped_split": dropped_split, "no_hist": no_hist, "no_cc": no_cc,
            "pm_used": pm_used, "calls": calls, "unknown": unknown,
            "fetch_fail": fetch_fail, "empty_pm": empty_pm, "has_pm": has_pm,
            # 🐞 كان `len(events) - pm_used` فيطبع صفوفًا أسقطها فلترُ التقسيم
            #    والتاريخ **قصًّا بالسقف** وهو كذب (ملحق §⑫-ⓓ).
            "truncated": max(0, len(ev_rows) - pm_used),
            "match": (len(cx_rows) / len(ev_rows)) if ev_rows else 0.0}


def bonf_z(ev_rows, ct_rows):
    """`(عددُ الخلايا، z)` — **عتبةُ `T-LINK100` حرفيًّا** (§⓪-1).

    🔒 العائلةُ هي عائلةُ الميزات **الثلاثَ عشرةَ** التي اشتقّ منها `T-LINK100`
    عتبتَه، لا عائلةٌ أضيقُ من أذرعي أنا — تلك **تخفيضٌ صامتٌ للعتبة** وهو
    بعينه ما يمنعه القيدُ الأوّل في العقد. والتركيبُ هو تركيبُه نفسُه."""
    n = max(1, sum(len(_stat_enrich(ev_rows, ct_rows, f)) for f in L_FEATURES))
    return n, _stat_z(n)


def pm_cover(rows):
    """`V-U4` — حصّةُ الصفوف التي **نجح جلبُ دقائقها**، لا التي حملت سلّة.

    🔴 **ملحقُ §⑫-1:** المقياسُ الأوّل كان «`pm_usd` غيرُ `None`» وهو يخلط
    «لم تُجلَب» بـ«جُلبت فوجدت الجلسةَ فارغة» — وسهمٌ مغمورٌ في يومٍ عاديٍّ
    **لا يتداول بريماركتًا أصلًا** ⇒ كان الحارسُ يُسقط التجربةَ على بياناتٍ
    سليمة. والنصُّ المسجَّل «الطبقةُ الدقيقةُ **تُجلَب فعلًا**» — وهذا قياسُه."""
    if not rows:
        return 0.0
    return sum(1 for r in rows if r.get("fetch_ok")) / len(rows)


def split_pop(ev_rows):
    """`E-PM ⊎ E-REG` — قسمةٌ **تامّةٌ** بلا ثالث (`V-U5`)."""
    pm = [r for r in ev_rows if r.get("is_pm")]
    reg = [r for r in ev_rows if not r.get("is_pm")]
    return pm, reg


def pm_flag_ok(ev_rows):
    """`V-U5` — **حارسٌ حيٌّ لا تحصيلُ حاصل.**

    مقارنةُ الأطوال وحدَها تصدق دائمًا لأن `split_pop` تقسم بالتعريف ⇒ الحارسُ
    الحقيقيُّ أن **كلَّ صفٍّ يحمل `is_pm` منطقيًّا صريحًا**: صفٌّ غفل عنه
    الإثراءُ كان سينزلق إلى `E-REG` صامتًا فيدخل الحاكمةَ (أ) بلا حقّ."""
    return all(isinstance(r.get("is_pm"), bool) for r in ev_rows)


# ═══════════════ ③ الأذرعُ والحكم (§④ · §⑥) ═══════════════════════════════════
def arm_cells(ev_rows, cx_rows, cc_rows, feat, scope):
    """خلايا ذراعٍ واحدة — `enrich` بالاسم على الجانبين."""
    side = ev_rows if scope == "all" else split_pop(ev_rows)[1]
    return (side,
            _stat_enrich(side, cx_rows, feat),
            _stat_enrich(side, cc_rows, feat))


def known_split_ok(ev_rows):
    """أرضيّةُ `C-KNOWN`: ‏50 فأكثر في **كلٍّ** من الشقَّين (§⑥)."""
    kn = sum(1 for r in ev_rows if r.get("known"))
    return kn, len(ev_rows) - kn, (kn >= MIN_BUCKET_N
                                   and (len(ev_rows) - kn) >= MIN_BUCKET_N)


def read_pm_verdict(per_year: dict, guards: dict) -> tuple:
    """§⑥ بحرفه — والفروعُ الثلاثةُ كلٌّ في سطرها.

    1. **تُوصى** — (`PU1` أو `PU2`) **و**`PU3` والأرضيّةُ مستوفاة.
    2. **فشلت** — الأرضيّةُ قائمةٌ وسقط معيار.
    3. **لا حكم** — أرضيّةٌ ساقطة (أو سنةٌ من الثلاث غائبة)."""
    if not guards.get("pass"):
        return RC_GUARD, ("لا حكم", "حارسٌ ساقط ⇒ لا يُفسَّر رقم")
    if any(y not in per_year for y in GOV_YEARS):
        return RC_NOVERDICT, ("لا حكم", "سنةٌ من الثلاث غائبةٌ عن التشغيلة")
    if not all(per_year[y]["floor"] for y in GOV_YEARS):
        return RC_NOVERDICT, ("لا حكم", "الأرضيّةُ ساقطةٌ في سنةٍ فأكثر")
    pu1 = all(per_year[y]["PU1"] for y in GOV_YEARS)
    pu2 = all(per_year[y]["PU2"] for y in GOV_YEARS)
    pu3 = all(per_year[y]["PU3"] for y in GOV_YEARS)
    if (pu1 or pu2) and pu3:
        return RC_OK, ("تُوصى",
                       "الحاكمةُ تعبر `LK1` **وتُضيف** فوق المعروف ⇒ تسجيلٌ "
                       "أماميٌّ جديدٌ يُقترَح على المالك قبل أيّ استعمال")
    miss = [n for n, v in (("PU1", pu1), ("PU2", pu2), ("PU3", pu3)) if not v]
    return RC_OK, ("فشلت", "الأرضيّةُ قائمةٌ وسقط: " + " · ".join(miss))


# ═══════════════ ④ التشغيل ════════════════════════════════════════════════════
def measure_year(year: str, key: str) -> dict:
    """مسحُ سنةٍ كاملةً — `scan_year` بالاسم ثمّ الإثراءُ بالطبقة الدقيقة."""
    sc = scan_year(year, key)                                    # بالاسم
    _log(f"   📅 {year}: أيّامٌ {sc['days']} · مجلوبةٌ {sc['got']} "
         f"(‏{sc['cover'] * 100:.1f}%) · خامٌ {sc['raw']} · أحداثٌ بعد الطيّ "
         f"{len(sc['events'])}")
    en = enrich_pm(sc["events"], key, PMUSD_CAP)
    _log(f"      🔬 مقيسةٌ {len(en['ev'])} · تقسيمٌ {en['dropped_split']} · "
         f"بلا تاريخٍ {en['no_hist']} · بلا `CC` {en['no_cc']} · "
         f"`CX` {len(en['cx'])} · `CC` {len(en['cc'])} · "
         f"جلباتُ دقيقةٍ {en['calls']} · مستعمَلٌ من السقف {en['pm_used']}/"
         f"{PMUSD_CAP} · مقصوصٌ {en['truncated']} · مجهولٌ {en['unknown']}")
    _log(f"      🔎 الجلبُ (§⑫-ⓓ): فشلٌ {en['fetch_fail']} · فراغٌ حقيقيٌّ "
         f"{en['empty_pm']} · ببريماركتٍ {en['has_pm']} — والفراغُ **ليس** فشلًا")
    sc.update(en)
    return sc


def guards_of(scans: dict) -> dict:
    """`V-U1`-`V-U5` — كلٌّ برمز خروجه."""
    g = {"pass": True, "rc": RC_OK, "why": []}
    for y in sorted(scans):
        s = scans[y]
        if y in PUBLISHED and len(s["ev"]) != PUBLISHED[y]:
            g["pass"], g["rc"] = False, RC_POP
            g["why"].append(f"`V-U1` {y}: {len(s['ev'])} ≠ {PUBLISHED[y]}")
        if s["cover"] < MIN_DAYS_COVER:
            g["pass"], g["rc"] = False, RC_COVER
            g["why"].append(f"`V-U2` {y}: تغطيةٌ {s['cover'] * 100:.1f}%")
        if s["match"] < MIN_MATCH:
            g["pass"], g["rc"] = False, RC_COVER
            g["why"].append(f"`V-U3` {y}: مطابقةٌ {s['match'] * 100:.1f}%")
        for nm, rows in (("الأحداث", s["ev"]), ("`CX`", s["cx"]), ("`CC`", s["cc"])):
            c = pm_cover(rows)
            if c < PM_COVER_MIN:
                g["pass"], g["rc"] = False, RC_GUARD
                g["why"].append(f"`V-U4` {y} {nm}: طبقةٌ دقيقةٌ {c * 100:.1f}%")
        pm, reg = split_pop(s["ev"])
        if len(pm) + len(reg) != len(s["ev"]) or not pm_flag_ok(s["ev"]):
            g["pass"], g["rc"] = False, RC_GUARD
            g["why"].append(f"`V-U5` {y}: صفٌّ بلا وسمِ `E-PM` صريح")
    return g


def main() -> int:                                               # noqa: PLR0911, PLR0915
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        _log("⛔ لا POLYGON_API_KEY — خروج 2")
        return RC_NOKEY
    src = open(__file__, encoding="utf-8").read()
    if not (selfcheck_readonly(src) and no_config_assign(src)):   # بالاسم
        _log("⛔ حارسُ «قراءةٌ فقط / صفرُ إسناد» ساقط — خروج 6")
        return RC_GUARD
    _log("🌅💧 T-PMUSD — سيولةُ البريماركت: رابطٌ قبل الانفجار أم الانفجارُ نفسُه؟")
    _log("   (العقد `pmusd_prereg.md` مدموجٌ قبل هذا الملفّ)")
    _log(f"⚙️ السنوات: {' · '.join(YEARS)} · الحاكمُ high(d)/close(d−1) ≥ "
         f"{EXPL_X} · إغلاقُ الأمس في [{PRICE_LO:.2f}, 20]$ · سقفُ الطبقة "
         f"الدقيقة {PMUSD_CAP}/سنة · `LK1` ≥{RATIO_MIN}× مقابل الشاهدَين "
         f"وفواصلُ ويلسون منفصلة و`n ≥ {MIN_BUCKET_N}` وبونفيروني α={ALPHA}")
    if DRY:
        _log("🧪 وضعُ جدوى `PMUSD_DRY=1` — أربعةُ أعدادٍ ثمّ عودةٌ **قبل أيّ "
             "نسبةٍ أو فاصلٍ أو حكم**")

    scans = {}
    for y in YEARS:
        s = measure_year(y, key)
        if not s["ev"]:
            _log(f"⛔ {y}: صفرُ حدثٍ مقيس — خروج 4")
            return RC_NOEVENT
        scans[y] = s

    # ── الأعدادُ الأربعةُ (§⑩) ───────────────────────────────────────────────
    _log("")
    _log("📊 الأعدادُ الأربعة:")
    for y in sorted(scans):
        s = scans[y]
        pm, reg = split_pop(s["ev"])
        cc_ok = sum(1 for r in s["cc"] if r.get("fetch_ok"))
        cc_pm = sum(1 for r in s["cc"] if r.get("u_now") is not None)
        _log(f"   {y}: أحداثٌ {len(s['ev'])} · `E-PM` {len(pm)} "
             f"(‏{len(pm) / len(s['ev']) * 100:.1f}%) و`E-REG` {len(reg)} · "
             f"صفوفُ `CC` **نجح جلبُها** {cc_ok}/{len(s['cc'])} "
             f"(‏ومنها {cc_pm} ببريماركتٍ فعليّ) · "
             f"المستعمَلُ من السقف {s['pm_used']}/{PMUSD_CAP}")
    if DRY:
        _log("")
        _log(f"🧪 نداءاتُ الإحصاء = {_CALLS['stat']} (يجب أن تكون صفرًا) — "
             "وضعُ الجدوى يعود الآن بلا نسبةٍ ولا فاصلٍ ولا حكم")
        return RC_OK

    g = guards_of(scans)
    _log("")
    _log(f"🛡️ الحرّاس: {'✅ كلُّها خضراء' if g['pass'] else '⛔ ' + ' · '.join(g['why'])}")
    if not g["pass"]:
        _log(f"⛔ خروج {g['rc']}")
        return g["rc"]

    # ── الأذرعُ الخمس ────────────────────────────────────────────────────────
    per_year, table = {}, []
    for y in sorted(scans):
        s = scans[y]
        # 🔒 **عتبةُ `T-LINK100` حرفيًّا** (§⓪-1) — القرارُ في `bonf_z` وحدَها
        #    فلا يُعاد اختيارُ العائلة هنا. والأضيقُ يُطبَع **حساسيّةً لا حكمًا**.
        n_cells, z = bonf_z(s["ev"], s["cx"])
        z_wide = _stat_z(len(ARMS))
        res = {}
        for name, feat, scope, _gov in ARMS:
            side, e_cx, e_cc = arm_cells(s["ev"], s["cx"], s["cc"], feat, scope)
            cx_c, cc_c = e_cx.get(GOV_BUCKET), e_cc.get(GOV_BUCKET)
            if feat.startswith("g_"):
                cx_c, cc_c = e_cx.get("≥30%"), e_cc.get("≥30%")
            ok = _stat_cell(cx_c, cc_c, z)
            ok_w = _stat_cell(cx_c, cc_c, z_wide)
            # 🔻 القراءةُ الثانية **الوصفيّة** — الفراغُ الحقيقيُّ صفرٌ (§⑫-4).
            s0, e0_cx, e0_cc = arm_cells(s["ev"], s["cx"], s["cc"],
                                         feat + "0", scope)
            lab0 = "≥30%" if feat.startswith("g_") else GOV_BUCKET
            c0x, c0c = e0_cx.get(lab0), e0_cc.get(lab0)
            res[name] = {"n": len(side), "cx": cx_c, "cc": cc_c,
                         "pass": ok, "pass_wide": ok_w,
                         "n0": len(s0), "cx0": c0x, "cc0": c0c,
                         "pass0": _stat_cell(c0x, c0c, z)}
            table.append((y, name, len(side), cx_c, cc_c, ok))
        kn, unkn, floor = known_split_ok(s["ev"])
        # ── `C-KNOWN` على الحاكمة العابرة (وإلّا على `U-NOW` عرضًا) ──────────
        gov = "U-NOW" if res["U-NOW"]["pass"] else (
            "U-PREV" if res["U-PREV"]["pass"] else "U-NOW")
        feat = "u_now" if gov == "U-NOW" else "u_prev"
        scope = "reg" if gov == "U-NOW" else "all"
        side = s["ev"] if scope == "all" else split_pop(s["ev"])[1]
        comp = [r for r in side if not r.get("known")]
        comp_cx = [r for r in s["cx"] if not r.get("known")]
        comp_cc = [r for r in s["cc"] if not r.get("known")]
        kn_side = [r for r in side if r.get("known")]
        kn_cx = [r for r in s["cx"] if r.get("known")]
        kn_cc = [r for r in s["cc"] if r.get("known")]
        lab = GOV_BUCKET
        c_cx = _stat_enrich(comp, comp_cx, feat).get(lab)
        c_cc = _stat_enrich(comp, comp_cc, feat).get(lab)
        k_cx = _stat_enrich(kn_side, kn_cx, feat).get(lab)
        k_cc = _stat_enrich(kn_side, kn_cc, feat).get(lab)
        r_cx = c_cx["ratio"] if c_cx and c_cx["ratio"] else 0.0
        r_cc = c_cc["ratio"] if c_cc and c_cc["ratio"] else 0.0
        pu3 = bool(r_cx >= KNOWN_RATIO and r_cc >= KNOWN_RATIO)
        per_year[y] = {"PU1": res["U-NOW"]["pass"], "PU2": res["U-PREV"]["pass"],
                       "PU3": pu3, "floor": floor, "gov": gov,
                       "known": kn, "unknown_side": unkn,
                       "c_cx": c_cx, "c_cc": c_cc, "k_cx": k_cx, "k_cc": k_cc,
                       "r_cx": r_cx, "r_cc": r_cc, "z": z, "z_wide": z_wide,
                       "n_cells": n_cells, "res": res}

    return report(scans, per_year, table, g)


def _cell(c):
    if not c:
        return "—"
    r = "—" if c["ratio"] is None else f"{c['ratio']:.2f}×"
    return (f"{c['pe']:.1f}% ({c['ke']}/{c['ne']}) مقابل {c['pc']:.1f}% "
            f"({c['kc']}/{c['nc']}) = {r}" + (" · منفصلان" if c["disjoint"] else ""))


def report(scans, per_year, table, g) -> int:                    # noqa: PLR0915
    """التقريرُ — الصفوفُ أوّلًا ثمّ الحكم، فيبقى الحكمُ في ذيل السجلّ."""
    _log("")
    _log("⟦TSV⟧\tyear\tarm\tn\tbucket\tpe\tke\tne\tpc\tkc\tnc\tratio_cx\tdisj_cx\tpass")
    for y, name, n, c_cx, c_cc, ok in table:
        if not c_cx:
            _log(f"⟦TSV⟧\t{y}\t{name}\t{n}\t—\t—\t—\t—\t—\t—\t—\t—\t—\t{int(ok)}")
            continue
        rc = "" if c_cx["ratio"] is None else f"{c_cx['ratio']:.4f}"
        _log(f"⟦TSV⟧\t{y}\t{name}\t{n}\t{GOV_BUCKET}\t{c_cx['pe']:.4f}\t"
             f"{c_cx['ke']}\t{c_cx['ne']}\t{c_cx['pc']:.4f}\t{c_cx['kc']}\t"
             f"{c_cx['nc']}\t{rc}\t{int(c_cx['disjoint'])}\t{int(ok)}")
    _log("")
    _log("═══════════════ 🌅💧 T-PMUSD — النتيجة ═══════════════")
    _log("")
    _log("🔁 **إعادةُ إنتاجٍ لأرقام `T-LINK100`** (تحقّقٌ يُطبَع ولا يحكم): "
         "`U-RAW` مقابل `CX` على `pm_usd` هي الميزةُ نفسُها بالتعريف نفسِه ⇒ "
         "نسبتُها يجب أن تعيد المنشور 34.72× · 21.69× · 14.03×")
    for y in sorted(scans):
        c = per_year[y]["res"]["U-RAW"]["cx"]
        txt = "—" if not c or c["ratio"] is None else f"{c['ratio']:.2f}×"
        _log(f"   {y}: {txt}   ({_cell(c)})")
    for y in sorted(scans):
        s, p = scans[y], per_year[y]
        pm, reg = split_pop(s["ev"])
        _log("")
        _log(f"📅 {y} — أحداثٌ {len(s['ev'])} · `E-PM` {len(pm)} "
             f"(‏{len(pm) / len(s['ev']) * 100:.1f}%) · `E-REG` {len(reg)} · "
             f"مجهولٌ داخلَ `E-PM` {s['unknown']} · خلايا {p['n_cells']} · "
             f"z={p['z']:.3f} (وعائلةٌ **أضيقُ** z={p['z_wide']:.3f} — "
             f"حساسيّةٌ تُطبَع ولا تحكم)")
        for name, _f, _sc, gov in ARMS:
            r = p["res"][name]
            tag = "🥇 حاكمة" if gov else "وصفيّة"
            _log(f"   {'✅' if r['pass'] else '🔴'} `{name}` ({tag} · n={r['n']}) "
                 f"· مقابل `CX`: {_cell(r['cx'])}")
            _log(f"       مقابل `CC`: {_cell(r['cc'])}"
                 + ("" if r["pass"] == r["pass_wide"]
                    else "  ⚠️ تعبر بعائلةٍ أضيقَ وحدَها"))
            _log(f"       🔻 قراءةٌ ثانيةٌ **وصفيّة** (الفراغُ صفرٌ · §⑫-4 · "
                 f"اتّجاهُها مع الفرضيّة فلا تحكم) — `CX`: {_cell(r['cx0'])}")
            _log(f"           و`CC`: {_cell(r['cc0'])} ⇒ "
                 f"{'✅' if r['pass0'] else '🔴'}")
        _log(f"   🧭 `C-KNOWN` على `{p['gov']}` — المعروفُ {p['known']} · "
             f"مُكمِّلُه {p['unknown_side']} · أرضيّةٌ "
             f"{'✅' if p['floor'] else '🔴'}")
        _log(f"       داخلَ المُكمِّل مقابل `CX`: {_cell(p['c_cx'])}")
        _log(f"       داخلَ المُكمِّل مقابل `CC`: {_cell(p['c_cc'])}")
        _log(f"       داخلَ المعروف  مقابل `CX`: {_cell(p['k_cx'])}")
        _log(f"       داخلَ المعروف  مقابل `CC`: {_cell(p['k_cc'])}")
        _log(f"       ⇒ `PU3` (‏≥{KNOWN_RATIO}× مقابل **الشاهدَين معًا**، وهي "
             f"القراءةُ الأشدّ): {'✅' if p['PU3'] else '🔴'} "
             f"(CX {p['r_cx']:.2f}× · CC {p['r_cc']:.2f}×)")

    rc, (branch, why) = read_pm_verdict(per_year, g)
    _log("")
    _log(f"⚖️ الحكم: **{branch}** — {why}")
    for nm in ("PU1", "PU2", "PU3"):
        _log(f"   {nm}: " + " · ".join(
            f"{y} {'✅' if per_year[y][nm] else '🔴'}" for y in sorted(per_year)))
    _log("   الأرضيّة: " + " · ".join(
        f"{y} {'✅' if per_year[y]['floor'] else '🔴'}" for y in sorted(per_year)))
    _log(f"🔢 نداءاتُ الإحصاء = {_CALLS['stat']}")
    _log(f"🚪 رمزُ الخروج = {rc}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
