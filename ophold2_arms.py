#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🕵️📈🌙 `T-OPHOLD-2` — الحملُ إلى **أوّلِ إغلاقٍ نظاميٍّ عند المِرساة أو بعدها**.

**العقد:** `ophold2_prereg.md` (مدفوعٌ ومدموجٌ `5c1f03db` ‏+ الملحقُ المؤرَّخ §⑫
`6641b007` — **كلاهما قبل هذا الملفّ وقبل أيّ رقمٍ من موضوعه**). أمرُ المالك
«سجّل الحمل 2» ثمّ «ابن أداة الحمل 2» (‏2026-09-16).

**لماذا وُلدت:** جدوى `T-OPHOLD` أخرجت أن ذراعَها الحاكمة `HC` (إغلاقُ نظاميِّ
اليوم نفسِه) **لا معنى لها لمِرساةِ افتر** فتسقط ‏92 مِرساةً (‏19%) بلا رقم
⇒ الأرضيّةُ ساقطةٌ والحكمُ «لا حكم» محتومٌ حسابيًّا. فأُعيد تعريفُ الخروج هنا
ليغطّي المجتمعَ كلَّه: **بريماركتٌ/نظاميٌّ ⟶ إغلاقُ يومه · وافترٌ ⟶ إغلاقُ يوم
التداول التالي** — **والوقفُ نافذٌ في كلّ دقيقةٍ بين الطرفين**.

🔒 **المجتمعُ والسياسةُ والحسمُ تُستورَد لا تُبنى** — `optrade_arms.build_rows`/
`attach_trades`/`simulate`/`trade_r`/`placebo_pool`/`pick_placebo`/`read_costs`/
`read_hstar`/`ci_of`/`crit_halves`/`tod_of`/`tsv_population`/`selfcheck_readonly`/
`no_config_assign` · و`ophold_arms.arm_R`/`arm_subset`/`arm_stats`/`paired`/
`exit_mix`/`tail_share`/`floors_of`/`read_verdict`/`bars_before`/`next_session` ·
و`tier_days_report.true_e5` · `tier_fwd_report.fetch_day` ·
`tierlink_probe.anchor_history`/`daily_range` · `opcurve_probe.ny_hour` ·
`fcost_arms.k_of`/`e_resolved`/`fill_frac`/`roots_identical` — **كلُّها بالاسم**.

⚖️ **وما كُتب هنا تجميعٌ لا حسم:** `hn_window` (ترشيحُ شموعٍ) · `attach_hold2`
(إلحاق) · `paired_placebo` (جمعُ أزواج) · `csub_after`/`sens_grid` (عرض) —
وكلُّ قرارِ نجاحٍ أو فشلٍ أو فرعٍ يأتي من `crit_halves`/`floors_of`/`read_verdict`
المستورَدة. و**صفرُ دالّةٍ هنا تحمل اسمَ دالّةِ حسمٍ مستورَدة** (مقفولٌ بالـAST).

🔑 **و`H0` ليس شبيهَ `P0` بل هو هو** (‏`V-N2` يقارن حقلًا حقلًا فيُوقف عند أوّل
اختلاف) · **و`HN ≡ HC0` على كلّ صفٍّ غيرِ افتريّ** (‏`V-N3` سلوكيٌّ: مسارا كودٍ
مختلفان يجب أن يتطابقا) · **والمجتمعُ عينُ مجتمع `T-OPCURVE`** (‏`V-N1`).

⚠️ **وفارقٌ مُعلَنٌ عن `C-MOM` في `T-OPTRADE`:** وقفُ البديلة هنا **مشتقٌّ بنسبة
`alow/e5`** لا قاعُ شمعتها — بنصّ العقد §④، ومثلُ `T-OPHOLD` حرفيًّا.

**رموزُ الخروج:** 0 صدر حكمٌ (الفرعان 1 و2) · 2 لا مفتاح · 3 تغطيةٌ دون الحدّ ·
4 صفرُ مِرساة · 5 المجتمعُ يخالف `V-N1` · **6 حارسٌ ساقط** (`V-N2`/`V-N3`/التكلفة/
`h*`/القراءة-فقط) · **9 «لا حكم» (الفرعُ 3)**.
"""
import os
import statistics as st
import sys

from optrade_arms import (CARD_OFFSET_MS, FLOOR_ARM, FLOOR_PAIR, FROZEN_UNTIL,
                          HIT_PCT, HSTAR, MIN_COVER, RC_COVER, RC_GUARD,
                          RC_NOANCHOR, RC_NOKEY, RC_NOVERDICT, RC_OK, RC_POP,
                          attach_trades, build_rows, ci_of, crit_halves,
                          no_config_assign, pick_placebo, placebo_pool,
                          read_costs, read_hstar, selfcheck_readonly, simulate,
                          tod_of, trade_r, tsv_population)       # بالاسم
import optrade_arms as OT                                        # للحدود الحيّة
from ophold_arms import (EXT_END_H, NO_CAP, arm_R, arm_stats, arm_subset,
                         bars_before, exit_mix, floors_of, next_session,
                         paired, read_verdict, tail_share)       # بالاسم
from ophold_arms import _ci_txt as ci_txt                        # عرضٌ لا حسم
from ophold_arms import _n as nfmt                               # عرضٌ لا حسم
from tierlink_probe import anchor_history, daily_range           # بالاسم
from tier_fwd_report import fetch_day, load_ledger               # بالاسم
from tier_days_report import true_e5                             # بالاسم
from fcost_arms import k_of, roots_identical                     # بالاسم

# ═══════════════ ⓪ الحدود — من الوحدة الحيّة لا مكتوبةً بيدي ═══════════════════
SINCE = os.environ.get("OPHOLD2_SINCE", OT.SINCE)
H2_FROM = os.environ.get("OPHOLD2_H2_FROM", OT.H2_FROM)
UNTIL = os.environ.get("OPHOLD2_UNTIL", FROZEN_UNTIL).strip()
DRY = os.environ.get("OPHOLD2_DRY", "").strip() == "1"

REG_END_H = 16.0                  # إغلاقُ الجلسة النظاميّة (§③)
ARMS = ("HN", "H0", "HC0", "HD", "HX2")          # §④ — قائمةٌ مُغلَقة
GOV = "HN"                                       # §④ — الحاكمةُ الوحيدة
DESC_ARMS = ("HC0", "HD", "HX2")                 # §④ — وصفيّة
LADDER = 4                       # `D1`…`D4` — الملحقُ §⑫ (و`D0` يُحسَب دائمًا)
FWD_FLOOR_DATE = "2026-11-15"                    # §⑧ — أرضيّةُ `N-FWD`
RESULT_MD = "ophold2_result.md"
TSV_COLS = ("date", "sym", "half", "tod", "tier", "gap", "trig", "e5", "alow",
            "risk_pct", "H0_out", "H0_R", "HN_out", "HN_R", "HN_t", "HN_day",
            "HC0_out", "HC0_R", "HX2_R", "HD_R", "mom_lvl", "mom_out", "mom_R")


def _log(msg: str = "") -> None:
    print(msg, flush=True)


# ═══════════════ ① نافذةُ الحمل — ترشيحُ شموعٍ لا منطقُ حسم ════════════════════
def day_bars(sym: str, day: str, key: str, cache: dict):
    """شموعُ يومٍ من الكاش أو `fetch_day` **بالاسم** — ولا تُجلَب مرّتين."""
    b = cache.get((sym, day))
    if b is None:
        b = fetch_day(sym, day, key) or []
        cache[(sym, day)] = b
    return b


def hn_window(sym: str, day: str, bars, t0: int, tod: str, key: str,
              cache: dict, dcache: dict, end_h: float = REG_END_H):
    """‏`(شموعُ النافذة، يومُ الخروج)` — §③ بحرفه، بلا أيّ حكم.

    **بريماركتٌ أو نظاميّ** ⇒ شموعُ ما بعد `t0` من يومه حتى `end_h`.
    **افتر** ⇒ بقيّةُ يومه **كاملةً** (فالوقفُ نافذٌ ليلًا) ‏+ شموعُ يوم التداول
    التالي حتى `end_h`. و`end_h = 16` لـ`HN` و`20` لـ`HX2` (§④).

    🔑 **وهذا مسارُ كودٍ مستقلٌّ عن `HC0`** — تطابقُهما على غير الافتر يُثبَت
    سلوكيًّا بـ`V-N3` ولا يُفترَض."""
    if tod != "after":
        return [b for b in bars_before(bars, end_h) if b[0] > t0], day
    nd = next_session(sym, day, key, dcache)
    if not nd:
        return None, None
    nb = day_bars(sym, nd, key, cache)
    if not nb:
        return None, None
    return ([b for b in (bars or []) if b[0] > t0]
            + bars_before(nb, end_h)), nd


def hold_trade(win, t0: int, e5, alow):
    """`simulate` **بالاسم** على نافذةٍ مُرشَّحةٍ سلفًا · بلا هدفٍ ثابت (§③)."""
    if not win:
        return None
    return simulate(win, t0, e5, alow, NO_CAP, use_target=False)


def prev_days(sym: str, day: str, key: str, dcache: dict, n: int):
    """آخرُ `n` يومَ تداولٍ **قبل** `day` من `daily_range` — الأحدثُ أوّلًا."""
    dl = dcache.get((sym, day))
    if dl is None:
        dl = daily_range(sym, day, key) or []
        dcache[(sym, day)] = dl
    pv = [d for (d, _h, _c) in dl if d < day]
    return list(reversed(pv))[:n]


# ═══════════════ ② إلحاقُ الأذرع والبديلة ═════════════════════════════════════
def attach_hold2(rows, key: str) -> dict:
    """يُلحق `HN`/`HC0`/`HD`/`HX2` وبديلةَ `C-MOM` بسلّم `D0 ⟶ D4` (§⑤ + §⑫).

    🔒 التكلفةُ و`R` لا تُحسبان هنا إطلاقًا ⇒ وضعُ الجدوى لا يمسّهما."""
    diag = {"trunc": 0, "no_next": 0, "tod_clash": 0}
    for r in rows:
        bars, e5, alow, t0 = r["bars"], r["e5"], r["alow"], r["t0"]
        sym, day, tod = r["sym"], r["date"], r["tod"]
        cache, dcache = r["cache"], r["dcache"]
        r["H0"] = simulate(bars, t0, e5, alow, HSTAR)             # = `P0` بالبناء
        r["HC0"] = simulate(bars, t0, e5, alow, None, use_target=False)
        win, nday = hn_window(sym, day, bars, t0, tod, key, cache, dcache)
        if win is None:
            diag["no_next"] += 1
        if win and (win[-1][0] - t0) > NO_CAP * 60_000:           # حدُّ صدقٍ يُعَدّ
            diag["trunc"] += 1
        r["HN"] = hold_trade(win, t0, e5, alow)
        r["HN_day"] = nday if r["HN"] else None
        r["HD"] = r["HN"] if tod == "after" else None
        wx, _dx = hn_window(sym, day, bars, t0, tod, key, cache, dcache,
                            end_h=EXT_END_H)
        r["HX2"] = hold_trade(wx, t0, e5, alow)
        # ── ضبطُ الزخم `C-MOM` — السياسةُ `HN` نفسُها بوقفٍ مشتقٍّ بالنسبة ────
        abar = next((b for b in bars if b[0] == r["a_ms"]), None)
        r["mom"] = {"lvl": "—", "tr": None, "e5": None, "alow": None}
        if r["HN"] is None or abar is None:
            continue
        # 🔒 جلسةُ المِرساة تُشتقّ بـ`tod_of` **بالاسم** وتُقارَن بقيمة
        #    `features` — تعارضُهما يُسقط الصفَّ ولا يُخمَّن.
        if tod_of(r["a_ms"]) != tod:
            r["mom"] = {"lvl": "تعارضُ جلسة", "tr": None, "e5": None,
                        "alow": None}
            diag["tod_clash"] += 1
            continue
        # 🔑 «صفرُ تداخل» = طولُ نافذة الحمل نفسِه ‏+ إزاحةُ الكرت (§⑤ · §⑫)
        gap = int(round((win[-1][0] - r["a_ms"]) / 60_000.0
                        + CARD_OFFSET_MS / 60_000.0))
        pool, _lv = placebo_pool(bars, None, r["a_ms"], tod, gap)  # `D0` وحدَه
        src, lvl, sday = bars, ("D0" if pool else "—"), day
        if not pool:
            for i, pd in enumerate(prev_days(sym, day, key, dcache, LADDER), 1):
                pb_day = day_bars(sym, pd, key, cache)
                pool, _lv = placebo_pool(bars, pb_day, r["a_ms"], tod, gap)
                if pool:
                    src, lvl, sday = pb_day, f"D{i}", pd
                    break
        r["mom"]["lvl"] = lvl
        pb = pick_placebo(pool, abar, "C-MOM")                    # بالاسم
        if pb is None:
            continue
        p_ms, p_price = int(pb[0]), round(float(pb[4]), 4)
        pe5, _b5 = true_e5(src, p_ms, p_price)                    # بالاسم
        if not pe5:
            continue
        t0p = p_ms + CARD_OFFSET_MS
        pwin, _pd = hn_window(sym, sday, src, t0p, tod, key, cache, dcache)
        p_low = pe5 * (alow / e5)          # الوقفُ المشتقُّ بالنسبة (§④)
        r["mom"].update({"tr": hold_trade(pwin, t0p, pe5, p_low), "e5": pe5,
                         "alow": p_low})
    return diag


# ═══════════════ ③ تجميعٌ — والحسمُ كلُّه مستورَدٌ بالاسم ══════════════════════
def pair_rows(rows, arm: str):
    """‏`(صفوفُ الأزواج، حصّةُ كلّ مستوًى)` — **عَدٌّ بلا `R` ولا تكلفة**.

    🔑 وجودُ الزوج يُحسَم من وجود الصفقتين وحدَهما (`trade_r` تُرجع `None` عند
    `None` فقط) ⇒ وضعُ الجدوى يعدّ الأزواجَ **قبل أيّ نداءِ تكلفةٍ أو `R`**."""
    out, lv = [], {}
    for r in rows:
        if not r.get(arm):
            continue                 # 🔒 لا صفقةَ أصلًا ⇒ لا يُعَدّ «بلا بديلة»
        m = r.get("mom") or {}
        k = m.get("lvl", "—")
        lv[k] = lv.get(k, 0) + 1
        if m.get("tr"):
            out.append((r, m, k))
    return out, lv


def pair_counts(pr) -> dict:
    return {h: sum(1 for (r, _m, _k) in pr if r["half"] == h)
            for h in ("H1", "H2")}


def paired_placebo(rows, arm: str, c: float, s: float) -> dict:
    """`arm − C-MOM` مقترنًا · وحصّةُ كلّ مستوًى على **القابل للتداول** وحدَه.

    ⚖️ **جمعُ أزواجٍ لا حسم:** كلُّ `R` من `trade_r` وكلُّ فاصلٍ من `ci_of`."""
    pr, lv = pair_rows(rows, arm)
    pairs = []
    for (r, m, k) in pr:
        a = arm_R(r, arm, c, s)
        p = trade_r(m["tr"], m["e5"], m["alow"], c, s)
        if a is None or p is None:
            continue
        pairs.append({"sym": r["sym"], "half": r["half"], "d": a - p,
                      "a": a, "p": p, "lvl": k})
    return _pair_stats(pairs, lv)


def _pair_stats(pairs, lv=None) -> dict:
    per = {}
    for h in ("H1", "H2"):
        hp = [z for z in pairs if z["half"] == h]
        ci = ci_of(hp, lambda z: z["d"]) if hp else None
        if ci:
            per[h] = ci
    return {"n": len(pairs), "lv": dict(lv or {}), "halves": per,
            "pairs": pairs, "pooled": ci_of(pairs, lambda z: z["d"]),
            "a_mean": (st.mean(z["a"] for z in pairs) if pairs else None),
            "p_mean": (st.mean(z["p"] for z in pairs) if pairs else None),
            "counts": {h: sum(1 for z in pairs if z["half"] == h)
                       for h in ("H1", "H2")}}


def csub_after(rows, c: float, s: float) -> dict:
    """`C-SUB` (§④) — `HD` تُقارَن **بمُكمِّلها** لا بالمجتمع · عرضٌ لا حسم."""
    base = arm_subset(rows, GOV)

    def fn(r):
        return arm_R(r, GOV, c, s)
    ins = [r for r in base if r["tod"] == "after"]
    comp = [r for r in base if r["tod"] != "after"]
    return {"n_sub": len(ins), "n_comp": len(comp),
            "sub": ci_of(ins, fn), "comp": ci_of(comp, fn)}


def sens_grid(rows, costs: dict) -> list:
    """شبكةُ الحساسيّة `c × s` (§③) — وصفيّةٌ تُطبَع دائمًا ولا تحكم."""
    cs = [("0", 0.0), ("C-P25", costs["C-P25"]),
          ("C-MED", costs["C-MED"]), ("C-P75", costs["C-P75"])]
    ss = [("0", 0.0), ("S-MED", costs["S-MED"])]
    out = []
    for cn, cv in cs:
        for sn, sv in ss:
            ci = ci_of(arm_subset(rows, GOV),
                       lambda r, _c=cv, _s=sv: arm_R(r, GOV, _c, _s))
            out.append({"c": cn, "s": sn, "mean": (ci or {}).get("mean")})
    return out


# ═══════════════ ④ حرّاسٌ خاصّة بهذي الأداة ════════════════════════════════════
def v_n2(rows) -> tuple:
    """`V-N2` — `H0` يطابق `P0` **حقلًا حقلًا** لكلّ صفّ، وإلّا يُوقَف (خروج 6)."""
    bad = []
    for r in rows:
        if r.get("H0") != r.get("P0"):
            bad.append(f"{r['date']}·{r['sym']}")
        if len(bad) >= 5:
            break
    return (not bad), bad


def v_n3(rows) -> tuple:
    """`V-N3` — `HN ≡ HC0` على **كلّ صفٍّ غيرِ افتريّ** · سلوكيٌّ لا بنيويّ."""
    bad, n = [], 0
    for r in rows:
        if r["tod"] == "after":
            continue
        n += 1
        if r.get("HN") != r.get("HC0"):
            bad.append(f"{r['date']}·{r['sym']}")
        if len(bad) >= 5:
            break
    return (not bad), bad, n


# ═══════════════ ⑤ التنبّؤاتُ السبعة — §⑦ كما وقعت ════════════════════════════
def predictions(rows, stats, cp0, cpc, mom, c, s) -> list:
    out = []
    mean = (stats[GOV]["pooled"] or {}).get("mean")
    out.append(("NP1", "متوسّطُ `R` لـ`HN` بعد التكلفة **سالب**",
                (mean is not None and mean < 0), f"{nfmt(mean)}R"))
    dc = (cpc["pooled"] or {}).get("mean")
    out.append(("NP2", "`HN − HC0` **سالبٌ** على مُشتركِهما (الليلُ يضرّ)",
                (dc is not None and dc < 0),
                f"{nfmt(dc)}R على {cpc['n']} صفًّا مشتركًا"))
    h1 = (cp0["halves"].get("H1") or {}).get("mean")
    h2 = (cp0["halves"].get("H2") or {}).get("mean")
    out.append(("NP3", "`HN − H0` موجبٌ في `H1` (وإشارةُ `H2` مُعلَنٌ أنها مجهولة)",
                (h1 is not None and h1 > 0),
                f"H1 {nfmt(h1)}R · H2 {nfmt(h2)}R — والثانيةُ تُطبَع ولا تُحاسَب"))
    ts = tail_share(rows, GOV, c, s)
    out.append(("NP4", "أعلى ‏10% تحمل أكثرَ من نصف مجموع `R` الموجب",
                (ts is not None and ts > 50.0),
                f"حصّةُ الذيل {ts:.1f}%" if ts is not None else "غيرُ منطبق"))
    a, d = mom["a_mean"], (mom["pooled"] or {}).get("mean")
    if a is None or d is None or abs(a) < 1e-12:
        out.append(("NP5", "`C-MOM` يأكل نصفَ فرقِ `HN` عن الصفر فأكثر", None,
                    "غيرُ منطبق (‏مستوى الذراع على الأزواج ≈ صفر أو لا أزواج)"))
    else:
        eaten = 1.0 - d / a
        out.append(("NP5", "`C-MOM` يأكل نصفَ فرقِ `HN` عن الصفر فأكثر",
                    eaten >= 0.5,
                    f"الذراعُ على الأزواج {nfmt(a)}R · الفرقُ {nfmt(d)}R "
                    f"⇒ أكل {eaten*100:.1f}%"))
    ok6 = all(mom["counts"].get(h, 0) >= FLOOR_PAIR for h in ("H1", "H2"))
    out.append(("NP6", "بالسلّم الممتدّ تعبر الأزواجُ ‏150 في كلّ نصف", ok6,
                f"H1 {mom['counts'].get('H1', 0)} · H2 "
                f"{mom['counts'].get('H2', 0)} (حدّ {FLOOR_PAIR})"))
    cs = csub_after(rows, c, s)
    sm = (cs["sub"] or {}).get("mean")
    cm = (cs["comp"] or {}).get("mean")
    out.append(("NP7", "`HD` (الافتر) **أدنى** من مُكمِّلها متوسّطًا",
                (None if (sm is None or cm is None) else sm < cm),
                f"افتر {nfmt(sm)}R (n={cs['n_sub']}) · غيرُه {nfmt(cm)}R "
                f"(n={cs['n_comp']})"))
    return out


def tsv_block(rows, c: float, s: float) -> list:
    """مُخرَجٌ آليٌّ — صفٌّ لكلّ مِرساةٍ بأذرعه الخمسة، بلا قصّ."""
    out = ["⟦TSV⟧", "\t".join(TSV_COLS)]

    def _f(v, nd=4):
        return "—" if v is None else f"{v:.{nd}f}"
    for r in sorted(rows, key=lambda x: (x["date"], x["sym"])):
        h0, hn = r.get("H0"), r.get("HN")
        m = r.get("mom") or {}
        mt = m.get("tr")
        mR = (trade_r(mt, m.get("e5"), m.get("alow"), c, s)
              if mt and m.get("e5") else None)
        hc0 = r.get("HC0")
        out.append("\t".join([
            r["date"], r["sym"], r["half"], r["tod"], r["f"]["tier"],
            r["f"]["gap"], r["trig"], _f(r["e5"]), _f(r["alow"]),
            _f(hn["risk_pct"], 2) if hn else "—",
            (h0["out"] if h0 else "—"), _f(arm_R(r, "H0", c, s)),
            (hn["out"] if hn else "—"), _f(arm_R(r, "HN", c, s)),
            _f(hn["t_exit"], 1) if hn else "—", (r.get("HN_day") or "—"),
            (hc0["out"] if hc0 else "—"), _f(arm_R(r, "HC0", c, s)),
            _f(arm_R(r, "HX2", c, s)), _f(arm_R(r, "HD", c, s)),
            m.get("lvl", "—"), (mt["out"] if mt else "—"), _f(mR)]))
    out.append("⟦/TSV⟧")
    return out


# ═══════════════ ⑥ main ════════════════════════════════════════════════════════
def main() -> int:                                               # noqa: PLR0911, PLR0915
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        _log("⛔ لا POLYGON_API_KEY — خروج 2")
        return RC_NOKEY
    src = open(__file__, encoding="utf-8").read()
    if not (selfcheck_readonly(src) and no_config_assign(src)):   # بالاسم
        _log("⛔ حارسُ «قراءةٌ فقط / صفرُ إسناد» ساقط — خروج 6")
        return RC_GUARD
    costs = read_costs()
    if not costs.get("ok"):
        _log(f"⛔ تعذّر استخراجُ التكلفة نصًّا: {costs.get('why')} — خروج 6")
        return RC_GUARD
    hs = read_hstar()
    if not hs.get("ok"):
        _log(f"⛔ نافذةُ `h*` لا تطابق المنشور: {hs.get('why')} — خروج 6")
        return RC_GUARD
    rid, rmsg = roots_identical()                                # بالاسم
    C, S = costs["C-MED"], costs["S-MED"]
    frozen = UNTIL == FROZEN_UNTIL
    _log("🕵️📈🌙 T-OPHOLD-2 — الحملُ إلى أوّلِ إغلاقٍ نظاميٍّ بعد المِرساة "
         "(العقد ophold2_prereg.md + الملحق §⑫)")
    _log(f"⚙️ الحدود: منذ {SINCE} · H2 من {H2_FROM} · حتى "
         f"{UNTIL or 'يوم التشغيل'} · `HN` = أوّلُ إغلاقٍ نظاميٍّ عند المِرساة "
         f"أو بعدها أو الوقف · و`H0` = سياسةُ T-OPTRADE بالحرف "
         f"({HSTAR} دقيقة · هدف +{HIT_PCT:.0f}%)")
    _log(f"💸 التكلفةُ **مستخرَجةٌ نصًّا**: C-MED {C*100:.4f}% · S-MED "
         f"{S*100:.4f}% · k(C-MED) = {k_of(C):.6f}")
    _log(f"🌳 الجذور: {'مطابقة' if rid else '⚠️ ' + rmsg}")
    if not frozen:
        _log("⚠️⚠️ النافذةُ ليست المجمَّدة ⇒ V-N1 غيرُ منطبق · والأرقامُ "
             "**وصفيّةٌ** والحكمُ يُجبَر على «لا حكم».")
    all_anchors = anchor_history(SINCE)
    fwd_n = sum(1 for (d, _s) in all_anchors if d > FROZEN_UNTIL)
    anchors = ({k: v for k, v in all_anchors.items() if k[0] <= UNTIL}
               if UNTIL else all_anchors)
    if not anchors:
        _log("⛔ صفرُ مِرساةٍ في تاريخ git — خروج 4")
        return RC_NOANCHOR
    ledger = {(r["date"], r["symbol"]): r for r in load_ledger()}
    _log(f"📚 مراسٍ {len(anchors)} · سجلّ M5 {len(ledger)}")
    _log(f"⏳ N-FWD (§⑧): مراسٍ بعد {FROZEN_UNTIL} = {fwd_n} · الأرضيّةُ "
         f"{FLOOR_ARM} صفًّا قابلًا للتداول أو {FWD_FLOOR_DATE} أيُّهما أوّلًا "
         "— ولا وعدَ يتعفّن.")
    rows, fails, nobase = build_rows(key, anchors, ledger)        # بالاسم
    cover = len(rows) / len(anchors)
    _log(f"🩺 التغطية: قِيس {len(rows)} · تعذّر الجلب {fails} · بلا أساس "
         f"{nobase} من {len(anchors)} = {cover*100:.1f}%")
    if cover < MIN_COVER:
        _log("⛔ التغطية دون الحدّ ⇒ لا يُفسَّر رقم — خروج 3")
        return RC_COVER
    if frozen:
        pub = tsv_population()                                   # بالاسم
        got = sorted((r["date"], r["sym"]) for r in rows)
        if pub is None:
            _log("⛔ V-N1 — الصفوفُ المنشورةُ غيرُ مقروءة — خروج 5")
            return RC_POP
        if pub != got:
            miss = sorted(set(pub) - set(got))[:5]
            extra = sorted(set(got) - set(pub))[:5]
            _log(f"⛔ V-N1 — المجتمعُ يخالف المنشور: هنا {len(got)} · منشور "
                 f"{len(pub)} · ناقصٌ {miss} · زائدٌ {extra} — خروج 5")
            return RC_POP
        nh1 = sum(1 for r in rows if r["half"] == "H1")
        _log(f"🔒 V-N1: المجتمعُ مطابقٌ بت-بت للصفوف المنشورة ({len(got)} صفًّا "
             f"· H1 {nh1} · H2 {len(got)-nh1})")
    attach_trades(rows, key, costs)                              # بالاسم ⇒ `P0`
    diag = attach_hold2(rows, key)
    ok2, bad2 = v_n2(rows)
    if not ok2:
        _log(f"⛔ V-N2 — `H0` يخالف `P0` في: {bad2} — خروج 6")
        return RC_GUARD
    _log(f"🔒 V-N2: `H0` يطابق `P0` حقلًا حقلًا في {len(rows)} صفًّا")
    ok3, bad3, n_non = v_n3(rows)
    if not ok3:
        _log(f"⛔ V-N3 — `HN` يخالف `HC0` على صفٍّ غيرِ افتريّ: {bad3} — خروج 6")
        return RC_GUARD
    _log(f"🔒 V-N3: `HN ≡ HC0` سلوكيًّا على {n_non} صفًّا غيرِ افتريّ "
         "(مسارا كودٍ مختلفان)")
    tradable = arm_subset(rows, GOV)
    per_half_n = {h: sum(1 for r in tradable if r["half"] == h)
                  for h in ("H1", "H2")}
    untr = [r for r in rows if r["alow"] is None or r["e5"] <= r["alow"]]
    aft = [r for r in rows if r["tod"] == "after"]
    aft_ok = [r for r in aft if r.get("HN")]
    hc0_n = len(arm_subset(rows, "HC0"))
    pr, lv = (pair_rows(rows, GOV) if DRY else (None, None))
    _log(f"🧮 القابلُ للتداول تحت `HN` {len(tradable)} (H1 {per_half_n['H1']} · "
         f"H2 {per_half_n['H2']}) · غيرُ قابلٍ (سعرُ الكرت عند القاع أو دونه) "
         f"{len(untr)}")
    _log(f"🌙 الافتر: {len(aft)} مِرساةً · صارت قابلةً {len(aft_ok)} — "
         f"و`HC0` (إغلاقُ اليوم نفسِه) يُغطّي {hc0_n} فقط ⇒ الفرقُ "
         f"{len(tradable) - hc0_n}")
    _log(f"🩺 تشخيصُ النافذة: بلا يومٍ تالٍ {diag['no_next']} · تجاوزُ السقف "
         f"{diag['trunc']} · تعارضُ جلسة {diag['tod_clash']}")
    if DRY:
        _log("🔀 بديلةُ C-MOM بالسلّم الممتدّ: "
             + " · ".join(f"{k} {lv.get(k, 0)}"
                          for k in ("D0", "D1", "D2", "D3", "D4", "—")))
        _pc = pair_counts(pr)
        _log(f"🔀 أزواجٌ: H1 {_pc['H1']} · H2 {_pc['H2']} (حدّ {FLOOR_PAIR})")
        _log("🧪 وضعُ الجدوى — أربعةُ أعدادٍ فقط · صفرُ R وصفرُ تكلفةٍ وصفرُ "
             "فرقٍ وصفرُ فاصل. ⚠️ ودرسُ T-PMGATE: وضعُ الجدوى يُجيز ما يمرّ به "
             "وحدَه فلا يُقرأ إذنًا للمسار كلِّه · وهو يكشف `NP6` جزئيًّا.")
        return RC_OK
    return report(rows, per_half_n, diag, costs, frozen)


def report(rows, per_half_n, diag, costs, frozen) -> int:        # noqa: PLR0915
    """يطبع كلَّ ما يقوله العقد ثمّ يُصدر الفرعَ من `read_verdict` **بالاسم**."""
    C, S = costs["C-MED"], costs["S-MED"]
    stats = {a: arm_stats(rows, a, C, S) for a in ARMS}
    cp0 = paired(rows, GOV, "H0", C, S)                          # `C-P0`
    cpc = paired(rows, GOV, "HC0", C, S)                         # وصفيّ (`NP2`)
    mom = paired_placebo(rows, GOV, C, S)
    mix = exit_mix(rows, GOV)
    _log("")
    _log("═══ ① الأذرعُ الخمس عند الخليّة الحاكمة (C-MED, S-MED) ═══")
    for a in ARMS:
        s = stats[a]
        tag = ("🥇 حاكمة" if a == GOV else
               ("مرجعٌ مقترن" if a == "H0" else "وصفيّة"))
        _log(f"  {a:4s} [{tag}] n={s['n']:4d} · تعبئة "
             f"{(s['fill'] or 0)*100:5.1f}% · مجمَّع {ci_txt(s['pooled'])}")
        for h in ("H1", "H2"):
            if s["halves"].get(h):
                _log(f"        {h}: {ci_txt(s['halves'][h])}")
    _log("")
    _log("═══ ② الضبطان الحاكمان ═══")
    _log(f"  C-P0  (HN − H0): {ci_txt(cp0['pooled'])} · "
         f"H1 {ci_txt(cp0['halves'].get('H1'))} · "
         f"H2 {ci_txt(cp0['halves'].get('H2'))}")
    _log(f"        مستوى HN على الأزواج {nfmt(cp0['a_mean'])}R · "
         f"H0 {nfmt(cp0['p_mean'])}R")
    _log(f"  C-MOM (HN − زخم): {ci_txt(mom['pooled'])} · "
         f"H1 {ci_txt(mom['halves'].get('H1'))} · "
         f"H2 {ci_txt(mom['halves'].get('H2'))}")
    _log(f"        أزواج: H1 {mom['counts']['H1']} · H2 {mom['counts']['H2']} · "
         + " · ".join(f"{k} {mom['lv'].get(k, 0)}"
                      for k in ("D0", "D1", "D2", "D3", "D4", "—")))
    near = [z for z in mom["pairs"] if z["lvl"] in ("D0", "D1")]
    _log(f"        🔎 قراءةٌ ثانيةٌ **وصفيّة** على `D0 ∪ D1` وحدَها (§⑤ · §⑫): "
         f"{ci_txt(_pair_stats(near)['pooled'])} — و`D0` فارغٌ بنيويًّا "
         "فهي `D1` وحدَها")
    cs = csub_after(rows, C, S)
    _log(f"  C-SUB (HD الافتر مقابل مُكمِّلها على HN): داخل {cs['n_sub']} "
         f"{ci_txt(cs['sub'])} · خارج {cs['n_comp']} {ci_txt(cs['comp'])}")
    _log(f"  وصفيٌّ (NP2) — HN − HC0 على مُشتركِهما: {ci_txt(cpc['pooled'])}")
    _log("")
    _log("═══ ③ شبكةُ الحساسيّة c × s لـHN — وصفيّةٌ لا تحكم ═══")
    for g in sens_grid(rows, costs):
        star = " 🥇" if (g["c"], g["s"]) == ("C-MED", "S-MED") else (
            " ◀ ملاصقة" if (g["c"], g["s"]) == ("C-MED", "0") else "")
        _log(f"  c={g['c']:6s} s={g['s']:6s} ⇒ {nfmt(g['mean'])}R{star}")
    _log("")
    _log("═══ ④ مزيجُ الخروج تحت HN ═══")
    for h in ("H1", "H2", "الكلّ"):
        if mix[h]["n"]:
            _log(f"  {h:5s} n={mix[h]['n']:4d} · وقف {mix[h]['loss']:5.1f}% · "
                 f"إغلاق {mix[h]['window']:5.1f}% · هدف {mix[h]['win']:5.1f}%")
    _log("")
    _log("═══ ⑤ المعاييرُ الثلاثة ═══")
    nh1 = crit_halves(stats[GOV]["halves"], stats[GOV]["pooled"])
    nh2 = crit_halves(cp0["halves"], cp0["pooled"])
    nh3 = crit_halves(mom["halves"], mom["pooled"])
    floors = floors_of(per_half_n, mom["counts"])
    for nm, cr in (("NH1 توقّعُ HN", nh1), ("NH2 HN − H0", nh2),
                   ("NH3 HN − C-MOM", nh3)):
        _log(f"  {nm:16s}: {'✅' if cr['pass'] else '🔴'} · موجبٌ بالنصفين="
             f"{cr['pos']} · فاصلُ المجمَّع فوق الصفر={cr['lo']} · "
             f"الأشدّ (النصفان أيضًا)={cr['strict']}")
    _log(f"  الأرضيّة       : {'✅' if floors['pass'] else '🔴'} · صفوف "
         f"{floors['n']} (حدّ {FLOOR_ARM}) · أزواج {floors['pairs']} "
         f"(حدّ {FLOOR_PAIR})")
    _log("")
    _log("═══ ⑥ التنبّؤاتُ السبعة ═══")
    for pid, txt, ok, why in predictions(rows, stats, cp0, cpc, mom, C, S):
        mark = "✅" if ok else ("🔴 مكذَّب" if ok is False else "— غيرُ منطبق")
        _log(f"  {pid}: {txt} ⇒ {mark} · {why}")
    _log("")
    br, (lbl, _w) = read_verdict(nh1, nh2, nh3, floors)          # بالاسم
    why = {1: "المعاييرُ الثلاثةُ عبرت ⇒ ثمّ `N-FWD` (§⑧) قبل أيّ اقتراح",
           2: "أرضيّةٌ قائمةٌ وسقط معيارٌ ⇒ لا تُوصى، ويُنشَر الرقم",
           3: "سقطت أرضيّةٌ ⇒ حصادٌ أماميّ `N-FWD` · ولا تُرفَع العيّنة"}[br]
    if not frozen:
        br, lbl, why = 3, "لا حكم", "النافذةُ غيرُ مجمَّدة ⇒ V-N1 غيرُ منطبق"
    _log(f"🏁 الفرعُ {br} — **{lbl}** · {why}")
    if br == 1:
        _log("⏭️ ولا يُقترَح سطرُ تسليمٍ قبل `N-FWD` (§⑧) — بنصّ العقد.")
    _log(f"🩺 تشخيصُ النافذة (يُعاد): {diag}")
    _log("")
    for ln in tsv_block(rows, C, S):
        _log(ln)
    return RC_OK if br in (1, 2) else RC_NOVERDICT


if __name__ == "__main__":
    sys.exit(main())
