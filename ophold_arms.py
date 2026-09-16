#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🕵️📈🪙 `T-OPHOLD` — سياسةُ **حَمْلٍ** بعد مِرساة «هنا الدخول» بلا سقفِ ‏+10%.

**العقد:** `ophold_prereg.md` (مدفوعٌ ومدموجٌ `13be23e9` قبل هذا الملفّ). أمرُ المالك
«سجّل الحمل» ثمّ «ابن الأداتين» (‏2026-09-16).

**السياسةُ الحاكمة (العقد §③/§④):** دخولٌ عند سعر كرت المِرساة · وقفٌ = قاعُ المِرساة
· خروجٌ = **إغلاقُ الجلسة النظاميّة** أو الوقف — أيُّهما أوّلًا · **بلا هدفٍ ثابت** ·
ولا إعادةَ دخول.

🔒 **المجتمعُ والسياسةُ يُستورَدان لا يُبنيان:** `optrade_arms.build_rows`/`attach_trades`/
`simulate`/`trade_r`/`placebo_pool`/`pick_placebo`/`read_costs`/`read_hstar`/`ci_of`
(ومعها `cl_map` عبرها)/`crit_halves`/`tod_of`/`tsv_population`/`selfcheck_readonly`/
`no_config_assign` — **كلُّها بالاسم**، ومعها `tier_days_report.true_e5` ·
`tier_fwd_report.fetch_day` · `tierlink_probe.anchor_history`/`daily_range` ·
`opcurve_probe.ny_hour` · `fcost_arms.k_of`/`e_resolved`/`fill_frac`/`roots_identical`.

🔑 **و`H0` ليس شبيهَ `P0` بل هو هو:** `attach_trades` تضعه في `r["P0"]`، و`V-H2`
يُعيد حسابَه بنداءٍ مستقلٍّ ويشترط التطابقَ حقلًا حقلًا — فإن اختلف صفٌّ واحد
**يُوقَف قبل أيّ رقم** (خروج 6).

⚠️ **وفارقٌ مُعلَنٌ عن `C-MOM` في `T-OPTRADE`:** هناك وقفُ البديلة **قاعُ شمعتها**،
وهنا **يُشتقّ بنسبة `alow/e5` نفسِها** — لأن العقد §④ نصَّ على ذلك صراحةً
(‏يعزل السياسةَ عن هندسة ذيل الشمعة). فلا تُعاد `optrade_arms.placebo_trade` هنا،
والفرقُ مقصودٌ ومكتوبٌ لا سهوٌ.

🔒 **قراءةٌ فقط:** صفرُ إرسالٍ · صفرُ كتابةِ حالة · صفرُ إسنادٍ إلى إعدادات الإنتاج ·
والإنتاجُ لا يستورد هذا الملفّ.

**رموزُ الخروج:** 0 صدر حكمٌ (الفرعان 1 و2) · 2 لا مفتاح · 3 تغطيةُ الجلب دون الحدّ ·
4 صفرُ مِرساة · 5 المجتمعُ يخالف الصفوفَ المنشورة (`V-H1`) · **6 حارسٌ ساقط**
(`V-H2`/التكلفة/`h*`/القراءة-فقط) · **9 «لا حكم» (الفرعُ 3)**.
"""
import os
import statistics as st
import sys

from optrade_arms import (CARD_OFFSET_MS, FLOOR_ARM, FLOOR_PAIR, FROZEN_UNTIL,
                          HIT_PCT, HSTAR, MIN_COVER, MOM_GAP_MIN, RC_COVER,
                          RC_GUARD, RC_NOANCHOR, RC_NOKEY, RC_NOVERDICT,
                          RC_OK, RC_POP, attach_trades, build_rows, ci_of,
                          crit_halves, no_config_assign, pick_placebo,
                          placebo_pool, read_costs, read_hstar,
                          selfcheck_readonly, simulate, tod_of, trade_r,
                          tsv_population)                        # بالاسم
import optrade_arms as OT                                        # للحدود الحيّة
from opcurve_probe import ny_hour                                # بالاسم
from tierlink_probe import anchor_history, daily_range           # بالاسم
from tier_fwd_report import fetch_day, load_ledger               # بالاسم
from tier_days_report import true_e5                             # بالاسم
from fcost_arms import e_resolved, fill_frac, k_of, roots_identical

# ═══════════════ ⓪ الحدود — من الوحدة الحيّة لا مكتوبةً بيدي ═══════════════════
SINCE = os.environ.get("OPHOLD_SINCE", OT.SINCE)
H2_FROM = os.environ.get("OPHOLD_H2_FROM", OT.H2_FROM)
UNTIL = os.environ.get("OPHOLD_UNTIL", FROZEN_UNTIL).strip()
DRY = os.environ.get("OPHOLD_DRY", "").strip() == "1"

EXT_END_H = 20.0                  # نهايةُ الجلسة الممتدّة (§④ — `HX`)
PRE_END_H = 9.5                   # نهايةُ البريماركت (§④ — `HP`)
NO_CAP = 10_000                   # «بلا سقفٍ زمنيّ» — النافذةُ يحدّها ترشيحُ الشموع
ARMS = ("H0", "HC", "HX", "HP", "HT", "HH")      # §④ — قائمةٌ مُغلَقة
GOV_ARM = "HC"                                   # §④ — الحاكمةُ الوحيدة
DESC_ARMS = ("HX", "HP", "HT", "HH")             # §④ — وصفيّة
RESULT_MD = "ophold_result.md"
TSV_COLS = ("date", "sym", "half", "tod", "tier", "gap", "trig", "e5", "alow",
            "risk_pct", "H0_out", "H0_R", "HC_out", "HC_R", "HC_t", "HX_R",
            "HP_R", "HT_R", "HH_R", "mom_lvl", "mom_out", "mom_R")


def _log(msg: str = "") -> None:
    print(msg, flush=True)


def _n(v, nd=4):
    return "—" if v is None else f"{v:+.{nd}f}"


def _ci_txt(ci) -> str:
    if not ci:
        return "—"
    return (f"{_n(ci['mean'])}R [{_n(ci['lo'])}, {_n(ci['hi'])}] "
            f"n={ci['n']} · رموز={ci['k']}")


# ═══════════════ ① ترشيحُ الشموع — فلترٌ لا منطقُ حسم ═════════════════════════
def bars_before(bars, hour: float):
    """شموعُ اليوم التي إغلاقُها قبل ساعةِ نيويورك المعطاة — ترشيحٌ زمنيٌّ بحت."""
    return [b for b in (bars or []) if ny_hour(b[0]) < hour]


def next_session(sym: str, day: str, key: str, dcache: dict):
    """أوّلُ يومِ تداولٍ **بعد** `day` من `daily_range` — أو `None`."""
    dl = dcache.get((sym, day))
    if dl is None:
        dl = daily_range(sym, day, key) or []
        dcache[(sym, day)] = dl
    nxt = [d for (d, _h, _c) in dl if d > day]
    return nxt[0] if nxt else None


# ═══════════════ ② الأذرعُ التي لا تُعبَّر بـ`simulate` (§④ — وصفيّتان) ════════
def trail_trade(bars, t0: int, e5, alow):
    """`HT` — وقفٌ زاحفٌ بمقدار `1R` تحت أعلى إغلاقِ دقيقةٍ بلغه السعر.

    **قاعدةٌ جديدة لا نسخةٌ من قائم:** الخروجُ البنيويُّ في الإنتاج مستوًى
    **ثابت** وحدَه. 🔒 ويُقفَل تطابقُها معه سلوكيًّا في السويّة: عند مخاطرةٍ
    ضخمةٍ لا يزحف المستوى أبدًا فيجب أن تُعطي هذي **عينَ مُخرَج `exit_point`**
    الإنتاجيّة (‏`OHA6`).

    ⚠️ **وحدُّ صدقٍ يُعلَن:** خروجُ الزحف يُوسَم `loss` كما يفعل `simulate`
    بخروج الوقف، و`S-MED` **سالبٌ** ⇒ الوسمُ **يُجمّل** هذي الذراع — وهي
    وصفيّةٌ بنصّ العقد فلا تحكم."""
    if e5 is None or alow is None or e5 <= alow:
        return None
    win = [b for b in (bars or []) if b[0] > t0 and ny_hour(b[0]) < 16]
    if not win:
        return None
    risk = e5 - alow
    peak, lvl = None, alow
    for b in win:
        c = b[4]
        if c < lvl:
            return {"out": "loss", "r0": (c / e5 - 1.0) * 100.0, "tie": False,
                    "t_exit": (b[0] - t0) / 60_000.0,
                    "win_min": (win[-1][0] - t0) / 60_000.0,
                    "risk_pct": risk / e5 * 100.0}
        peak = c if peak is None else max(peak, c)
        lvl = max(alow, peak - risk)
    return {"out": "window", "r0": (win[-1][4] / e5 - 1.0) * 100.0, "tie": False,
            "t_exit": (win[-1][0] - t0) / 60_000.0,
            "win_min": (win[-1][0] - t0) / 60_000.0,
            "risk_pct": risk / e5 * 100.0}


def half_legs(bars, t0: int, e5, alow):
    """`HH` — نصفٌ عند لمسِ `T10` ونصفٌ إلى إغلاق النظاميّة أو الوقف.

    يُرجع `(ساقُ الهدف أو None، الساقُ الباقية)` — وكلُّ ساقٍ تمرّ بـ`trade_r`
    وحدَها فتُكلَّف بقاعدتها. 🔒 **وإن لم يُلمَس الهدفُ فالساقان واحدةٌ هي
    `HC` بعينها** ⇒ `HH ≡ HC` (مقفولٌ سلوكيًّا `OHA7`)."""
    full = simulate(bars, t0, e5, alow, None, use_target=True)    # بالاسم
    if full is None:
        return None, None
    if full["out"] != "win":
        return None, full
    t_hit = int(t0 + round(full["t_exit"] * 60_000))
    rest = simulate(bars, t_hit, e5, alow, None, use_target=False)
    leg_a = {"out": "win", "r0": float(HIT_PCT), "tie": False,
             "t_exit": full["t_exit"], "win_min": full["win_min"],
             "risk_pct": full["risk_pct"]}
    return leg_a, (rest if rest is not None else leg_a)


# ═══════════════ ③ إلحاقُ أذرع الحمل والضبط ═══════════════════════════════════
def attach_hold(rows, key: str):
    """يُلحق `HC`/`HX`/`HP`/`HT`/`HH` وبديلةَ `C-MOM` **بخروج `HC` نفسِه**.

    🔒 التكلفةُ و`R` لا تُحسبان هنا إطلاقًا ⇒ وضعُ الجدوى لا يمسّهما."""
    for r in rows:
        bars, e5, alow, t0 = r["bars"], r["e5"], r["alow"], r["t0"]
        r["H0"] = simulate(bars, t0, e5, alow, HSTAR)             # = `P0` بالبناء
        r["HC"] = simulate(bars, t0, e5, alow, None, use_target=False)
        r["HX"] = simulate(bars_before(bars, EXT_END_H), t0, e5, alow, NO_CAP,
                           use_target=False)
        r["HT"] = trail_trade(bars, t0, e5, alow)
        la, lb = half_legs(bars, t0, e5, alow)
        r["HH_legs"] = (la, lb)
        r["HH"] = lb                                  # للعرض؛ و`R` من الساقين
        # ── `HP`: حملٌ ليليٌّ إلى آخر شمعةِ بريماركتِ الغد (§④ — وصفيّة) ──────
        r["HP"] = None
        nd = next_session(r["sym"], r["date"], key, r["dcache"])
        if nd:
            nb = r["cache"].get((r["sym"], nd))
            if nb is None:
                nb = fetch_day(r["sym"], nd, key) or []
                r["cache"][(r["sym"], nd)] = nb
            pmb = bars_before(nb, PRE_END_H)
            if pmb:
                r["HP"] = simulate(bars_before(bars, EXT_END_H) + pmb, t0, e5,
                                   alow, NO_CAP, use_target=False)
        # ── ضبطُ الزخم `C-MOM` بخروج `HC` ووقفٍ مشتقٍّ بالنسبة نفسِها ─────────
        abar = next((b for b in bars if b[0] == r["a_ms"]), None)
        r["mom"] = {"lvl": "—", "tr": None, "e5": None, "alow": None}
        if r["HC"] is None or abar is None:
            continue
        # 🔒 جلسةُ المِرساة تُشتقّ بـ`tod_of` **بالاسم** وتُقارَن بقيمة
        #    `features` — تعارضُهما يُسقط الصفَّ ولا يُخمَّن (‏`OHA9`).
        tod = tod_of(r["a_ms"])
        if tod != r["tod"]:
            r["mom"] = {"lvl": "تعارضُ جلسة", "tr": None, "e5": None,
                        "alow": None}
            continue
        pool, lvl = placebo_pool(bars, None, r["a_ms"], tod, MOM_GAP_MIN)
        src = bars
        if not pool:
            prev = r.get("_prev")
            if prev is None:
                dl = r["dcache"].get((r["sym"], r["date"]))
                if dl is None:
                    dl = daily_range(r["sym"], r["date"], key) or []
                    r["dcache"][(r["sym"], r["date"])] = dl
                pv = [d for (d, _h, _c) in dl if d < r["date"]]
                prev = []
                if pv:
                    pb = r["cache"].get((r["sym"], pv[-1]))
                    if pb is None:
                        pb = fetch_day(r["sym"], pv[-1], key) or []
                        r["cache"][(r["sym"], pv[-1])] = pb
                    prev = pb
                r["_prev"] = prev
            pool, lvl = placebo_pool(bars, prev, r["a_ms"], tod, MOM_GAP_MIN)
            src = prev
        pb = pick_placebo(pool, abar, "C-MOM")                    # بالاسم
        if pb is None:
            continue
        p_ms, p_price = int(pb[0]), round(float(pb[4]), 4)
        pe5, _b5 = true_e5(src, p_ms, p_price)                    # بالاسم
        if not pe5:
            continue
        # 🔑 الوقفُ المشتقُّ بنسبة المخاطرة نفسِها (العقد §④) لا قاعُ الشمعة
        p_low = pe5 * (alow / e5)
        tr = simulate(src, p_ms + CARD_OFFSET_MS, pe5, p_low, None,
                      use_target=False)
        r["mom"] = {"lvl": lvl, "tr": tr, "e5": pe5, "alow": p_low}
    return rows


# ═══════════════ ④ `R` لكلّ ذراع — `ret_at` ثمّ `r_fixed` بالترتيب المثبَّت ════
def arm_R(r, arm: str, c: float, s: float):
    if arm == "HH":
        la, lb = r.get("HH_legs") or (None, None)
        if lb is None:
            return None
        rb = trade_r(lb, r["e5"], r["alow"], c, s)
        if la is None:
            return rb
        ra = trade_r(la, r["e5"], r["alow"], c, s)
        if ra is None or rb is None:
            return None
        return 0.5 * (ra + rb)
    return trade_r(r.get(arm), r["e5"], r["alow"], c, s)


def arm_subset(rows, arm: str):
    if arm == "HH":
        return [r for r in rows if (r.get("HH_legs") or (None, None))[1]]
    return [r for r in rows if r.get(arm)]


def arm_stats(rows, arm: str, c: float, s: float) -> dict:
    sub = arm_subset(rows, arm)
    def fn(r):
        return arm_R(r, arm, c, s)
    per = {}
    for h in ("H1", "H2"):
        hr = [r for r in sub if r["half"] == h]
        ci = ci_of(hr, fn) if hr else None
        if ci:
            per[h] = ci
    view = []
    for r in sub:
        t = (r.get("HH_legs") or (None, None))[1] if arm == "HH" else r.get(arm)
        if t:
            view.append((t["out"], t["r0"]))
    return {"arm": arm, "n": len(sub), "halves": per, "pooled": ci_of(sub, fn),
            "ret_pct": (e_resolved(view, c, s) if view else None),
            "fill": (fill_frac(view, len(sub)) if sub else None)}


def paired(rows, a1: str, a2: str, c: float, s: float) -> dict:
    """فرقٌ مقترنٌ بين ذراعين على **الصفوف نفسِها** — `C-P0` حين `a2 = H0`."""
    d = []
    for r in rows:
        x, y = arm_R(r, a1, c, s), arm_R(r, a2, c, s)
        if x is not None and y is not None:
            d.append({"sym": r["sym"], "half": r["half"], "d": x - y,
                      "a": x, "p": y})
    per = {}
    for h in ("H1", "H2"):
        hp = [z for z in d if z["half"] == h]
        ci = ci_of(hp, lambda z: z["d"]) if hp else None
        if ci:
            per[h] = ci
    return {"n": len(d), "halves": per, "pooled": ci_of(d, lambda z: z["d"]),
            "a_mean": (st.mean(z["a"] for z in d) if d else None),
            "p_mean": (st.mean(z["p"] for z in d) if d else None),
            "counts": {h: sum(1 for z in d if z["half"] == h)
                       for h in ("H1", "H2")}}


def paired_mom(rows, c: float, s: float) -> dict:
    """`HC − C-MOM` مقترنًا · وحصّةُ `D0`/`D1` على **القابل للتداول** وحدَه."""
    pairs, lv = [], {"D0": 0, "D1": 0, "—": 0}
    for r in rows:
        if not r.get("HC"):
            continue                 # 🔒 لا صفقةَ أصلًا ⇒ لا يُعَدّ «بلا بديلة»
        m = r.get("mom") or {}
        lv[m.get("lvl", "—")] = lv.get(m.get("lvl", "—"), 0) + 1
        if not m.get("tr"):
            continue
        a = arm_R(r, "HC", c, s)
        p = trade_r(m["tr"], m["e5"], m["alow"], c, s)
        if a is None or p is None:
            continue
        pairs.append({"sym": r["sym"], "half": r["half"], "d": a - p,
                      "a": a, "p": p})
    per = {}
    for h in ("H1", "H2"):
        hp = [z for z in pairs if z["half"] == h]
        ci = ci_of(hp, lambda z: z["d"]) if hp else None
        if ci:
            per[h] = ci
    return {"n": len(pairs), "lv": lv, "halves": per,
            "pooled": ci_of(pairs, lambda z: z["d"]),
            "a_mean": (st.mean(z["a"] for z in pairs) if pairs else None),
            "p_mean": (st.mean(z["p"] for z in pairs) if pairs else None),
            "counts": {h: sum(1 for z in pairs if z["half"] == h)
                       for h in ("H1", "H2")}}


def csub(rows, arm: str, c: float, s: float) -> dict:
    """`C-SUB` (§④) — الجزئيّةُ `HP` تُقارَن **بمُكمِّلها** لا بالمجتمع."""
    sub = set(id(r) for r in arm_subset(rows, arm))
    base = arm_subset(rows, GOV_ARM)

    def fn(r):
        return arm_R(r, GOV_ARM, c, s)
    ins = [r for r in base if id(r) in sub]
    comp = [r for r in base if id(r) not in sub]
    return {"n_sub": len(ins), "n_comp": len(comp),
            "sub": ci_of(ins, fn), "comp": ci_of(comp, fn)}


# ═══════════════ ⑤ الحكم — §⑤ بحرفه ═══════════════════════════════════════════
def read_verdict(oh1: dict, oh2: dict, oh3: dict, floors: dict) -> tuple:
    """الفروعُ الثلاثةُ كلٌّ في سطرها — والأرضيّةُ **تمنع الفرعَ 1** بنصّ §⑤."""
    if not floors.get("pass"):
        return 3, ("لا حكم", "سقطت أرضيّةٌ ⇒ حصادٌ أماميّ · ولا تُرفَع العيّنة")
    if oh1.get("pass") and oh2.get("pass") and oh3.get("pass"):
        return 1, ("تُوصى", "المعاييرُ الثلاثةُ عبرت ⇒ ثمّ `H-FWD` قبل أيّ اقتراح")
    return 2, ("فشلت", "أرضيّةٌ قائمةٌ وسقط معيارٌ ⇒ لا تُوصى، ويُنشَر الرقم")


def floors_of(per_half_n: dict, mom_counts: dict) -> dict:
    """‏≥150 صفًّا قابلًا للتداول **و**‏≥150 زوجَ `C-MOM` في **كلّ** نصف."""
    arm_ok = all(per_half_n.get(h, 0) >= FLOOR_ARM for h in ("H1", "H2"))
    pair_ok = all(mom_counts.get(h, 0) >= FLOOR_PAIR for h in ("H1", "H2"))
    return {"pass": bool(arm_ok and pair_ok), "arm": arm_ok, "pair": pair_ok,
            "n": dict(per_half_n), "pairs": dict(mom_counts)}


def exit_mix(rows, arm: str) -> dict:
    """حصّةُ كلّ سببِ خروجٍ بالنصفين (‏`HP4`)."""
    out = {}
    for h in ("H1", "H2", "الكلّ"):
        sub = [r for r in arm_subset(rows, arm)
               if h == "الكلّ" or r["half"] == h]
        n = len(sub)
        def get(r):
            return r["HH_legs"][1] if arm == "HH" else r[arm]
        cnt = {k: sum(1 for r in sub if get(r)["out"] == k)
               for k in ("win", "loss", "window")}
        out[h] = {"n": n, **{k: (v / n * 100.0 if n else None)
                             for k, v in cnt.items()}}
    return out


def tail_share(rows, arm: str, c: float, s: float):
    """`HP2` — حصّةُ أعلى ‏10% من **مجموع `R` الموجب** لهذي الذراع."""
    vals = sorted((v for v in (arm_R(r, arm, c, s) for r in arm_subset(rows, arm))
                   if v is not None), reverse=True)
    pos = sum(v for v in vals if v > 0)
    if not vals or pos <= 0:
        return None
    k = max(1, int(round(len(vals) * 0.10)))
    return sum(v for v in vals[:k] if v > 0) / pos * 100.0


def predictions(rows, stats, cp0, mom, mix, c, s) -> list:
    """`HP1`-`HP7` من §⑥ — تُطبَع كما وقعت مؤكَّدةً أو مكذَّبة."""
    out = []
    sub = arm_subset(rows, GOV_ARM)
    vals = [v for v in (arm_R(r, GOV_ARM, c, s) for r in sub) if v is not None]
    med = st.median(vals) if vals else None
    mean = (stats[GOV_ARM]["pooled"] or {}).get("mean")
    out.append(("HP1", "وسيطُ `R` لـ`HC` سالبٌ والمتوسّطُ موجب",
                (med is not None and mean is not None and med < 0 and mean > 0),
                f"وسيط {_n(med)}R · متوسّط {_n(mean)}R · n={len(vals)}"))
    ts = tail_share(rows, GOV_ARM, c, s)
    out.append(("HP2", "أعلى ‏10% تحمل أكثرَ من نصف مجموع `R` الموجب",
                (ts is not None and ts > 50.0),
                f"حصّةُ الذيل {ts:.1f}%" if ts is not None else "غيرُ منطبق"))
    h1 = (cp0["halves"].get("H1") or {}).get("mean")
    h2 = (cp0["halves"].get("H2") or {}).get("mean")
    out.append(("HP3", "`HC − H0` موجبٌ في `H1` (وإشارةُ `H2` مُعلَنٌ أنها مجهولة)",
                (h1 is not None and h1 > 0),
                f"H1 {_n(h1)}R · H2 {_n(h2)}R — والثانيةُ تُطبَع ولا تُحاسَب"))
    okm = all((mix[h]["loss"] or 0) > 50.0 for h in ("H1", "H2") if mix[h]["n"])
    out.append(("HP4", "حصّةُ الوقف تحت `HC` فوق ‏50% في النصفين", okm,
                " · ".join(f"{h}: {mix[h]['loss']:.1f}%"
                           for h in ("H1", "H2") if mix[h]["n"])))
    a, d = mom["a_mean"], (mom["pooled"] or {}).get("mean")
    if a is None or d is None or abs(a) < 1e-12:
        out.append(("HP5", "`C-MOM` يأكل نصفَ فرقِ `HC` عن الصفر فأكثر", None,
                    "غيرُ منطبق (‏مستوى الذراع على الأزواج ≈ صفر أو لا أزواج)"))
    else:
        eaten = 1.0 - d / a
        out.append(("HP5", "`C-MOM` يأكل نصفَ فرقِ `HC` عن الصفر فأكثر",
                    eaten >= 0.5,
                    f"الذراعُ على الأزواج {_n(a)}R · الفرقُ {_n(d)}R "
                    f"⇒ أكل {eaten*100:.1f}%"))
    hx = (stats["HX"]["pooled"] or {})
    hc = (stats[GOV_ARM]["pooled"] or {})
    hp = (stats["HP"]["pooled"] or {})
    def wid(ci):
        return (ci["hi"] - ci["lo"]) if ci else None
    ok6 = (hx.get("mean") is not None and hc.get("mean") is not None
           and hx["mean"] > hc["mean"]
           and (wid(hx) or 0) > (wid(hc) or 0)
           and hp.get("mean") is not None and hp["mean"] < hc["mean"])
    out.append(("HP6", "`HX` أعلى وأوسعُ فاصلًا من `HC` · و`HP` أدنى منه", ok6,
                f"HX {_n(hx.get('mean'))} (عرض {_n(wid(hx))}) · "
                f"HC {_n(hc.get('mean'))} (عرض {_n(wid(hc))}) · "
                f"HP {_n(hp.get('mean'))}"))
    ht = (stats["HT"]["pooled"] or {}).get("mean")
    h0 = (stats["H0"]["pooled"] or {}).get("mean")
    ok7 = (ht is not None and h0 is not None and hc.get("mean") is not None
           and min(h0, hc["mean"]) <= ht <= max(h0, hc["mean"]))
    out.append(("HP7", "`HT` بين `H0` و`HC` متوسّطًا", ok7,
                f"H0 {_n(h0)} · HT {_n(ht)} · HC {_n(hc.get('mean'))}"))
    return out


# ═══════════════ ⑥ حرّاسٌ خاصّة بهذي الأداة ════════════════════════════════════
def v_h2(rows) -> tuple:
    """`V-H2` — `H0` يطابق `P0` **حقلًا حقلًا** لكلّ صفّ، وإلّا يُوقَف."""
    bad = []
    for r in rows:
        a, b = r.get("H0"), r.get("P0")
        if a != b:
            bad.append(f"{r['date']}·{r['sym']}")
        if len(bad) >= 5:
            break
    return (not bad), bad


def grid(rows, costs: dict) -> list:
    """شبكةُ الحساسيّة `c × s` (§③) — وصفيّةٌ تُطبَع دائمًا ولا تحكم."""
    cs = [("0", 0.0), ("C-P25", costs["C-P25"]),
          ("C-MED", costs["C-MED"]), ("C-P75", costs["C-P75"])]
    ss = [("0", 0.0), ("S-MED", costs["S-MED"])]
    out = []
    for cn, cv in cs:
        for sn, sv in ss:
            ci = ci_of(arm_subset(rows, GOV_ARM),
                       lambda r, _c=cv, _s=sv: arm_R(r, GOV_ARM, _c, _s))
            out.append({"c": cn, "s": sn, "mean": (ci or {}).get("mean")})
    return out


def tsv_block(rows, c: float, s: float) -> list:
    """مُخرَجٌ آليٌّ — صفٌّ لكلّ مِرساةٍ بأذرعه الستّة، بلا قصّ."""
    out = ["⟦TSV⟧", "\t".join(TSV_COLS)]

    def _f(v, nd=4):
        return "—" if v is None else f"{v:.{nd}f}"
    for r in sorted(rows, key=lambda x: (x["date"], x["sym"])):
        h0, hc = r.get("H0"), r.get("HC")
        m = r.get("mom") or {}
        mt = m.get("tr")
        mR = (trade_r(mt, m.get("e5"), m.get("alow"), c, s)
              if mt and m.get("e5") else None)
        out.append("\t".join([
            r["date"], r["sym"], r["half"], r["tod"], r["f"]["tier"],
            r["f"]["gap"], r["trig"], _f(r["e5"]), _f(r["alow"]),
            _f(hc["risk_pct"], 2) if hc else "—",
            (h0["out"] if h0 else "—"), _f(arm_R(r, "H0", c, s)),
            (hc["out"] if hc else "—"), _f(arm_R(r, "HC", c, s)),
            _f(hc["t_exit"], 1) if hc else "—",
            _f(arm_R(r, "HX", c, s)), _f(arm_R(r, "HP", c, s)),
            _f(arm_R(r, "HT", c, s)), _f(arm_R(r, "HH", c, s)),
            m.get("lvl", "—"), (mt["out"] if mt else "—"), _f(mR)]))
    out.append("⟦/TSV⟧")
    return out


# ═══════════════ ⑦ main ════════════════════════════════════════════════════════
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
    _log("🕵️📈🪙 T-OPHOLD — سياسةُ الحمل بعد المِرساة (العقد ophold_prereg.md)")
    _log(f"⚙️ الحدود: منذ {SINCE} · H2 من {H2_FROM} · حتى "
         f"{UNTIL or 'يوم التشغيل'} · `HC` = إغلاقُ النظاميّة أو الوقف · "
         f"و`H0` = سياسةُ T-OPTRADE بالحرف ({HSTAR} دقيقة · هدف +{HIT_PCT:.0f}%)")
    _log(f"💸 التكلفةُ **مستخرَجةٌ نصًّا**: C-MED {C*100:.4f}% · S-MED "
         f"{S*100:.4f}% · k(C-MED) = {k_of(C):.6f}")
    _log(f"🌳 الجذور: {'مطابقة' if rid else '⚠️ ' + rmsg}")
    if not frozen:
        _log("⚠️⚠️ النافذةُ ليست المجمَّدة ⇒ V-H1 غيرُ منطبق · والأرقامُ "
             "**وصفيّةٌ** والحكمُ يُجبَر على «لا حكم».")
    anchors = anchor_history(SINCE)
    if UNTIL:
        anchors = {k: v for k, v in anchors.items() if k[0] <= UNTIL}
    if not anchors:
        _log("⛔ صفرُ مِرساةٍ في تاريخ git — خروج 4")
        return RC_NOANCHOR
    ledger = {(r["date"], r["symbol"]): r for r in load_ledger()}
    _log(f"📚 مراسٍ {len(anchors)} · سجلّ M5 {len(ledger)}")
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
            _log("⛔ V-H1 — الصفوفُ المنشورةُ غيرُ مقروءة — خروج 5")
            return RC_POP
        if pub != got:
            miss = sorted(set(pub) - set(got))[:5]
            extra = sorted(set(got) - set(pub))[:5]
            _log(f"⛔ V-H1 — المجتمعُ يخالف المنشور: هنا {len(got)} · منشور "
                 f"{len(pub)} · ناقصٌ {miss} · زائدٌ {extra} — خروج 5")
            return RC_POP
        nh1 = sum(1 for r in rows if r["half"] == "H1")
        _log(f"🔒 V-H1: المجتمعُ مطابقٌ بت-بت للصفوف المنشورة ({len(got)} صفًّا "
             f"· H1 {nh1} · H2 {len(got)-nh1})")
    attach_trades(rows, key, costs)                              # بالاسم ⇒ `P0`
    attach_hold(rows, key)
    ok2, bad2 = v_h2(rows)
    if not ok2:
        _log(f"⛔ V-H2 — `H0` يخالف `P0` في: {bad2} — خروج 6")
        return RC_GUARD
    _log(f"🔒 V-H2: `H0` يطابق `P0` حقلًا حقلًا في {len(rows)} صفًّا")
    tradable = arm_subset(rows, GOV_ARM)
    untr = [r for r in rows if r["alow"] is None or r["e5"] <= r["alow"]]
    per_half_n = {h: sum(1 for r in tradable if r["half"] == h)
                  for h in ("H1", "H2")}
    lv = {"D0": 0, "D1": 0, "—": 0}
    for r in tradable:
        m = r.get("mom") or {}
        lv[m.get("lvl", "—")] = lv.get(m.get("lvl", "—"), 0) + 1
    mix = exit_mix(rows, GOV_ARM)
    _log(f"🧮 القابلُ للتداول تحت `HC` {len(tradable)} (H1 {per_half_n['H1']} · "
         f"H2 {per_half_n['H2']}) · غيرُ قابلٍ (سعرُ الكرت عند القاع أو دونه) "
         f"{len(untr)}")
    _log(f"🔀 بديلةُ C-MOM: D0 {lv['D0']} · D1 {lv['D1']} · بلا بديلة {lv['—']}")
    _log("🛑 حصّةُ الوقف تحت `HC`: "
         + " · ".join(f"{h} {mix[h]['loss']:.1f}%" for h in ("H1", "H2")
                      if mix[h]["n"]))
    if DRY:
        _log("🧪 وضعُ الجدوى — ثلاثةُ أعدادٍ فقط · صفرُ R وصفرُ تكلفةٍ وصفرُ "
             "فرقٍ وصفرُ فاصل. ⚠️ ودرسُ T-PMGATE: وضعُ الجدوى يُجيز ما يمرّ به "
             "وحدَه فلا يُقرأ إذنًا للمسار كلِّه · وهو يكشف `HP4` جزئيًّا.")
        return RC_OK
    return report(rows, tradable, per_half_n, lv, mix, costs, frozen)


def report(rows, tradable, per_half_n, lv, mix, costs, frozen) -> int:  # noqa: PLR0915
    """يطبع كلَّ ما يقوله العقد ثمّ يُصدر الفرعَ من `read_verdict` بحرفه."""
    C, S = costs["C-MED"], costs["S-MED"]
    stats = {a: arm_stats(rows, a, C, S) for a in ARMS}
    cp0 = paired(rows, GOV_ARM, "H0", C, S)                      # `C-P0`
    mom = paired_mom(rows, C, S)
    _log("")
    _log("═══ ① الأذرعُ الستّ عند الخليّة الحاكمة (C-MED, S-MED) ═══")
    for a in ARMS:
        s = stats[a]
        tag = "🥇 حاكمة" if a == GOV_ARM else ("مرجعٌ مقترن" if a == "H0"
                                               else "وصفيّة")
        _log(f"  {a:3s} [{tag}] n={s['n']:4d} · تعبئة "
             f"{(s['fill'] or 0)*100:5.1f}% · مجمَّع {_ci_txt(s['pooled'])}")
        for h in ("H1", "H2"):
            if s["halves"].get(h):
                _log(f"        {h}: {_ci_txt(s['halves'][h])}")
    _log("")
    _log("═══ ② الضبطان الحاكمان ═══")
    _log(f"  C-P0  (HC − H0): {_ci_txt(cp0['pooled'])} · "
         f"H1 {_ci_txt(cp0['halves'].get('H1'))} · "
         f"H2 {_ci_txt(cp0['halves'].get('H2'))}")
    _log(f"        مستوى HC على الأزواج {_n(cp0['a_mean'])}R · "
         f"H0 {_n(cp0['p_mean'])}R")
    _log(f"  C-MOM (HC − زخم): {_ci_txt(mom['pooled'])} · "
         f"H1 {_ci_txt(mom['halves'].get('H1'))} · "
         f"H2 {_ci_txt(mom['halves'].get('H2'))}")
    _log(f"        أزواج: H1 {mom['counts']['H1']} · H2 {mom['counts']['H2']} "
         f"· D0 {lv['D0']} · D1 {lv['D1']}")
    cs = csub(rows, "HP", C, S)
    _log(f"  C-SUB (HP مقابل مُكمِّلها على HC): داخل {cs['n_sub']} "
         f"{_ci_txt(cs['sub'])} · خارج {cs['n_comp']} {_ci_txt(cs['comp'])}")
    _log("")
    _log("═══ ③ شبكةُ الحساسيّة c × s لـHC — وصفيّةٌ لا تحكم ═══")
    for g in grid(rows, costs):
        star = " 🥇" if (g["c"], g["s"]) == ("C-MED", "S-MED") else (
            " ◀ ملاصقة" if (g["c"], g["s"]) == ("C-MED", "0") else "")
        _log(f"  c={g['c']:6s} s={g['s']:6s} ⇒ {_n(g['mean'])}R{star}")
    _log("")
    _log("═══ ④ مزيجُ الخروج تحت HC ═══")
    for h in ("H1", "H2", "الكلّ"):
        if mix[h]["n"]:
            _log(f"  {h:5s} n={mix[h]['n']:4d} · وقف {mix[h]['loss']:5.1f}% · "
                 f"إغلاق {mix[h]['window']:5.1f}% · هدف {mix[h]['win']:5.1f}%")
    _log("")
    _log("═══ ⑤ المعاييرُ الثلاثة ═══")
    oh1 = crit_halves(stats[GOV_ARM]["halves"], stats[GOV_ARM]["pooled"])
    oh2 = crit_halves(cp0["halves"], cp0["pooled"])
    oh3 = crit_halves(mom["halves"], mom["pooled"])
    floors = floors_of(per_half_n, mom["counts"])
    for nm, cr in (("OH1 توقّعُ HC", oh1), ("OH2 HC − H0", oh2),
                   ("OH3 HC − C-MOM", oh3)):
        _log(f"  {nm:16s}: {'✅' if cr['pass'] else '🔴'} · موجبٌ بالنصفين="
             f"{cr['pos']} · فاصلُ المجمَّع فوق الصفر={cr['lo']} · "
             f"الأشدّ (النصفان أيضًا)={cr['strict']}")
    _log(f"  الأرضيّة       : {'✅' if floors['pass'] else '🔴'} · صفوف "
         f"{floors['n']} (حدّ {FLOOR_ARM}) · أزواج {floors['pairs']} "
         f"(حدّ {FLOOR_PAIR})")
    _log("")
    _log("═══ ⑥ التنبّؤاتُ السبعة ═══")
    for pid, txt, ok, why in predictions(rows, stats, cp0, mom, mix, C, S):
        mark = "✅" if ok else ("🔴 مكذَّب" if ok is False else "— غيرُ منطبق")
        _log(f"  {pid}: {txt} ⇒ {mark} · {why}")
    _log("")
    br, (lbl, why) = read_verdict(oh1, oh2, oh3, floors)
    if not frozen:
        br, lbl, why = 3, "لا حكم", "النافذةُ غيرُ مجمَّدة ⇒ V-H1 غيرُ منطبق"
    _log(f"🏁 الفرعُ {br} — **{lbl}** · {why}")
    if br == 1:
        _log("⏭️ ولا يُقترَح سطرُ تسليمٍ قبل `H-FWD` (§⑧) — بنصّ العقد.")
    _log("")
    for ln in tsv_block(rows, C, S):
        _log(ln)
    return RC_OK if br in (1, 2) else RC_NOVERDICT


if __name__ == "__main__":
    sys.exit(main())
