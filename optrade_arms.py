#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🕵️💥 `T-OPTRADE` — سياسةُ مضاربةٍ واحدةٌ بعد مِرساة «هنا الدخول»، بالتكلفة وبضبطِ زخم.

**العقد:** `optrade_prereg.md` (مدفوعٌ ومدموجٌ `678c64c5` قبل هذا الملفّ). أمرُ المالك
«سجل السياسة» ثمّ «ابن الاداة» (‏2026-09-16).

**السياسة (العقد §③):** دخولٌ عند سعر كرت المِرساة ‏+ نصفِ تكلفةِ الدورة · وقفٌ = قاعُ
المِرساة · خروجٌ = الهدف أو الوقف أو انتهاءُ النافذة · لا حملَ ليليّ · ولا إعادةَ دخول.

🔒 **المجتمعُ عينُ مجتمع `T-OPCURVE` لا مثيلٌ له:** الطبقاتُ الثلاث تُبنى بالدوالّ
نفسِها وبالترتيب نفسِه، و`V-T1` يُثبت تطابقَ مُتعدَّدِ `(date, sym)` مع الصفوف
المنشورة — وأيُّ فرقٍ يُوقف قبل أيّ رقم.

🔒 **صفرُ منطقِ حسمٍ مكرَّر:** `opcurve_probe.resolve_anchor`/`trig_bucket`/`buckets_of`/
`ny_hour`/`CARD_OFFSET_MS`/`HIT_PCT` · `tierlink_probe.anchor_history`/`features`/
`daily_range` · `tier_fwd_report.fetch_day`/`load_ledger` · `tier_days_report.true_e5` ·
`sym_day_probe.exit_point` · `tranche_arms.r_fixed` · `fcost_arms.ret_at`/`k_of`/
`e_resolved`/`fill_frac`/`roots_identical` · `exitmgmt_arms.boot_ci` ·
`btcost_arms.pctile` — **كلُّها بالاسم**.

🔒 **قراءةٌ فقط:** صفرُ إرسالٍ · صفرُ كتابةِ حالة · صفرُ إسنادٍ إلى إعدادات الإنتاج ·
والإنتاجُ لا يستورد هذا الملفّ.

🔒 **ولا رقمَ يُكتَب بيدي:** تكلفةُ الدورة وانزلاقُها يُستخرَجان من نتيجة `T-BTCOST`
نصًّا (‏`V-T3`) · ونافذةُ الخروج تُستخرَج من نتيجة `T-OPCURVE` نصًّا وتُطابَق
بالثابت (‏`V-T6`).

**رموزُ الخروج:** 0 صدر حكمٌ (الفرعان 1 و2) · 2 لا مفتاح · 3 تغطيةُ الجلب دون الحدّ ·
4 صفرُ مِرساة · 5 المجتمعُ يخالف الصفوفَ المنشورة (`V-T1`) · **6 حارسٌ ساقط**
(`V-T3`/`V-T6`/`V-T7`) · **9 «لا حكم» (الفرعُ 3)**.
"""
import ast
import os
import re
import statistics as st
import sys

from opcurve_probe import (CARD_OFFSET_MS, HIT_PCT, buckets_of, ny_hour,
                           resolve_anchor, trig_bucket)          # بالاسم
import opcurve_probe as OC                                       # للحدود الحيّة
from tierlink_probe import anchor_history, daily_range, features  # بالاسم
from tier_fwd_report import fetch_day, load_ledger                # بالاسم
from tier_days_report import true_e5                              # بالاسم
from sym_day_probe import exit_point                              # بالاسم
from tranche_arms import r_fixed                                  # بالاسم
from fcost_arms import e_resolved, fill_frac, k_of, ret_at, roots_identical
from exitmgmt_arms import boot_ci                                 # بالاسم
from btcost_arms import pctile                                    # بالاسم

# ═══════════════ ⓪ الحدود — من الوحدة الحيّة لا مكتوبةً بيدي (‏`V-T2`) ═══════════
SINCE = os.environ.get("OPTRADE_SINCE", OC.SINCE)
H2_FROM = os.environ.get("OPTRADE_H2_FROM", OC.H2_FROM)
FROZEN_UNTIL = "2026-09-15"                     # نافذةُ الصفوف المنشورة (العقد §②)
UNTIL = os.environ.get("OPTRADE_UNTIL", FROZEN_UNTIL).strip()
DRY = os.environ.get("OPTRADE_DRY", "").strip() == "1"

ROWS_TSV = "opcurve_rows.tsv"                   # `V-T1`
BT_RESULT = "btcost_result.md"                  # `V-T3`
OC_RESULT = "opcurve_result.md"                 # `V-T6`

HSTAR = 120                                     # العقد §③ — يُطابَق بـ`V-T6`
W_GRID = (15, 30, 60, HSTAR, 240, None)         # §⓪-1 — `None` = إغلاقُ النظاميّ
MOM_GAP_MIN = HSTAR + 4                         # §⑤-أ — صفرُ تداخل
MOM_GAP_OVL = 15                                # `C-MOM-15` وصفيّ
FLOOR_ARM = 150                                 # `OT3`
FLOOR_PAIR = 150                                # أرضيّةُ `OT2`
MIN_COVER = 0.80                                # مرآةُ `V-C3`
ARMS = ("P0", "P1", "P2", "P3")                 # §④ — قائمةٌ مُغلَقة
CONTROLS = ("C-MOM", "C-ANY", "C-MOM-15")       # §⑤ — `C-MOM` وحدَه حاكم
RC_OK, RC_NOKEY, RC_COVER, RC_NOANCHOR = 0, 2, 3, 4
RC_POP, RC_GUARD, RC_NOVERDICT = 5, 6, 9
TSV_COLS = ("date", "sym", "half", "tod", "tier", "gap", "trig",
            "e5", "alow", "risk_pct", "out", "r0", "R", "t_exit", "win_min",
            "tie", "p_lvl", "p_out", "p_r0", "p_R")


def _log(msg: str) -> None:
    print(msg, flush=True)


def _n(v, nd=4):
    return "—" if v is None else f"{v:+.{nd}f}"


# ═══════════════ ① الأرقامُ تُستخرَج من النتائج المنشورة لا تُكتَب ═══════════════
def _pct_nums(line: str) -> list:
    """كلُّ عددٍ متبوعٍ بـ`%` في السطر، بترتيب وروده · والسالبُ الرياضيّ يُطبَّع."""
    out = []
    for m in re.finditer(r"([−+-]?\d+(?:\.\d+)?)%", line or ""):
        out.append(float(m.group(1).replace("−", "-")))
    return out


def read_costs(path: str = BT_RESULT) -> dict:
    """`V-T3` — `C-MED`/`S-MED`/`C-P25`/`C-P75` من نتيجة `T-BTCOST` **نصًّا**.

    يُرجع كسورًا (‏لا نسبًا مئوية) لأن `ret_at` تأخذ `c`/`s` كسرًا."""
    try:
        txt = open(path, encoding="utf-8").read()
    except Exception as e:                                       # noqa: BLE001
        return {"ok": False, "why": f"تعذّر فتحُ {path}: {type(e).__name__}"}
    out = {}
    for lab in ("C-MED", "S-MED"):
        m = re.search(r"^\|\s*\*\*`" + lab + r"`\*\*\s*\|(.*)$", txt, re.M)
        v = _pct_nums(m.group(1)) if m else []
        if not v:
            return {"ok": False, "why": f"صفُّ `{lab}` غائبٌ أو بلا نسبة"}
        out[lab] = v[0] / 100.0
    m = re.search(r"^\|\s*`C-P25`\s*·\s*`C-P75`\s*\|(.*)$", txt, re.M)
    v = _pct_nums(m.group(1)) if m else []
    if len(v) < 2:
        return {"ok": False, "why": "صفُّ `C-P25`/`C-P75` غائبٌ أو ناقص"}
    out["C-P25"], out["C-P75"] = v[0] / 100.0, v[1] / 100.0
    if not (out["C-P25"] < out["C-MED"] < out["C-P75"]) or out["C-MED"] <= 0:
        return {"ok": False, "why": f"قيمٌ غيرُ متّسقة: {out}"}
    out["ok"] = True
    return out


def read_hstar(path: str = OC_RESULT) -> dict:
    """`V-T6` — نافذةُ الخروج من نتيجة `T-OPCURVE` نصًّا، وتُطابَق بالثابت."""
    try:
        txt = open(path, encoding="utf-8").read()
    except Exception as e:                                       # noqa: BLE001
        return {"ok": False, "why": f"تعذّر فتحُ {path}: {type(e).__name__}"}
    m = re.search(r"`h\\?\*`\s*=\s*\*\*[‏]?(\d+)\s*دقيقة\*\*", txt)
    if not m:
        m = re.search(r"\*\*`h\\?\*`\s*=\s*(\d+)\s*دقيقة\*\*", txt)
    if not m:
        return {"ok": False, "why": "لم يُعثَر على نافذة الخروج في النتيجة"}
    v = int(m.group(1))
    return {"ok": v == HSTAR, "h": v,
            "why": "" if v == HSTAR else f"المنشور {v} والثابتُ {HSTAR}"}


# ═══════════════ ② الجلسة — القاعدةُ نفسُها التي في `features` ═════════════════
def tod_of(ms: int) -> str:
    """`pre` دون 9.5 · `reg` دون 16 · وإلّا `after` — مرآةُ `features['tod']`
    (‏مقفولةٌ سلوكيًّا بمقارنةٍ مباشرةٍ معها، لا بالثقة)."""
    hh = ny_hour(ms)
    return "pre" if hh < 9.5 else ("reg" if hh < 16 else "after")


# ═══════════════ ③ محاكاةُ الصفقة — السياسةُ بحرفها (العقد §③) ════════════════
def simulate(bars, t0: int, e5, alow, h_min, use_target: bool = True,
             tie_to_stop: bool = True):
    """يُرجع قاموسَ الصفقة أو `None` إن تعذّرت.

    `h_min = None` ⇒ إغلاقُ النظاميّ. **الوقفُ من `exit_point` بالاسم** على شموع
    النافذة (‏أوّلُ إغلاقِ دقيقةٍ دون القاع) · **والهدفُ أوّلُ لمسةِ قمّةٍ** عند
    `e5 × (1 + HIT_PCT/100)`. وعند وقوعهما في الدقيقة نفسِها **يفوز الوقف**
    (‏متحفّظ) ما لم يُطلَب البديلُ الوصفيّ."""
    if e5 is None or alow is None or e5 <= alow:
        return None                                              # غيرُ قابلٍ للتداول
    after = [b for b in bars if b[0] > t0]
    if not after:
        return None
    if h_min is None:
        win = [b for b in after if ny_hour(b[0]) < 16]
    else:
        win = [b for b in after if b[0] <= t0 + h_min * 60_000]
    if not win:
        return None
    tgt = e5 * (1.0 + HIT_PCT / 100.0)
    hit = next((b for b in win if b[2] >= tgt), None) if use_target else None
    _sc, st_t = exit_point(win, t0, alow)                        # بالاسم
    tie = bool(hit and st_t is not None and hit[0] == st_t)
    stop_first = st_t is not None and (hit is None or st_t < hit[0]
                                       or (tie and tie_to_stop))
    if stop_first:
        out, r0, t_at = "loss", (_sc / e5 - 1.0) * 100.0, st_t
    elif hit is not None:
        out, r0, t_at = "win", float(HIT_PCT), hit[0]
    else:
        out, r0, t_at = "window", (win[-1][4] / e5 - 1.0) * 100.0, win[-1][0]
    return {"out": out, "r0": r0, "tie": tie,
            "t_exit": (t_at - t0) / 60_000.0,
            "win_min": (win[-1][0] - t0) / 60_000.0,
            "risk_pct": (e5 - alow) / e5 * 100.0}


def trade_r(tr: dict, e5, alow, c: float, s: float):
    """§⑥ — `ret_at` أوّلًا ثمّ `r_fixed`؛ المقامُ ثابتٌ لا يتحرّك بالتكلفة."""
    if tr is None:
        return None
    return r_fixed(ret_at(tr["r0"], tr["out"], c, s), e5, e5, alow)


# ═══════════════ ④ البديلة — بركةٌ بمستويَين، حتميّةٌ بلا بذرة (§⑤-أ) ═══════════
def placebo_pool(bars_day, bars_prev, anchor_ms: int, tod: str, gap_min: int):
    """`(مرشّحون, مستوى)` — `D0` اليومُ نفسُه بصفرِ تداخل، وإلّا `D1` اليومُ السابق."""
    d0 = [b for b in (bars_day or [])
          if b[0] < anchor_ms and anchor_ms - b[0] >= gap_min * 60_000
          and tod_of(b[0]) == tod]
    if d0:
        return d0, "D0"
    d1 = [b for b in (bars_prev or []) if tod_of(b[0]) == tod]
    if d1:
        return d1, "D1"
    return [], "—"


def _bar_ret(b):
    return (b[4] - b[1]) / b[1] if b[1] else None


def pick_placebo(pool, anchor_bar, mode: str):
    """`C-MOM`/`C-MOM-15`: أقربُ عائدٍ دقيقيّ · وفضُّ التعادل **الأقدمُ طابعًا**.
    `C-ANY`: الوسطى زمنيًّا بلا أيّ مطابقة. الاثنان حتميّان بلا بذرة."""
    if not pool:
        return None
    if mode == "C-ANY":
        return sorted(pool, key=lambda b: b[0])[len(pool) // 2]
    tr = _bar_ret(anchor_bar)
    if tr is None:
        return None
    cand = [(abs((_bar_ret(b) if _bar_ret(b) is not None else 1e9) - tr), b[0], b)
            for b in pool if _bar_ret(b) is not None]
    if not cand:
        return None
    cand.sort(key=lambda x: (x[0], x[1]))
    return cand[0][2]


def placebo_trade(bars, pb, h_min):
    """السياسةُ **نفسُها حرفيًّا** على الدقيقة البديلة — وبتعريف الإنتاج للحقلين:
    سعرُ المِرساة إغلاقُ الشمعة وقاعُها قاعُها، مقرَّبَين لأربع خانات."""
    p_ms = int(pb[0])
    p_price, p_low = round(float(pb[4]), 4), round(float(pb[3]), 4)
    e5p, _b5 = true_e5(bars, p_ms, p_price)                      # بالاسم
    if not e5p:
        return None, None, None
    t0p = p_ms + CARD_OFFSET_MS
    return simulate(bars, t0p, e5p, p_low, h_min), e5p, p_low


# ═══════════════ ⑤ التجميع والحكم ══════════════════════════════════════════════
def cl_map(rows, val):
    """خريطةُ عناقيدَ لـ`boot_ci` — العنقودُ **الرمز** (§⑥)."""
    g = {}
    for r in rows:
        v = val(r)
        if v is None:
            continue
        n, ssum = g.get(r["sym"], (0, 0.0))
        g[r["sym"]] = (n + 1, ssum + float(v))
    return g


def ci_of(rows, val):
    g = cl_map(rows, val)
    return boot_ci(g) if g else None                             # بالاسم


def read_verdict(ot1: dict, ot2: dict, ot3: dict) -> tuple:
    """يطبّق §⑥ **بحرفه** — والفروعُ الثلاثةُ كلٌّ في سطرها.

    `OT3` أرضيةُ الذراع في **كلّ** نصف · وأرضيّةُ `OT2` أزواجٌ في **كلّ** نصف ·
    و`OT1`/`OT2`: موجبٌ في **النصفين** ‏+ فاصلُ المجمَّع لا يلمس الصفر."""
    floors = bool(ot3.get("pass")) and bool(ot2.get("floor"))
    if not floors:
        return 3, ("لا حكم", "سقطت أرضيّةٌ ⇒ حصادٌ أماميّ · ولا تُرفَع العيّنة")
    if ot1.get("pass") and ot2.get("pass"):
        return 1, ("تُوصى", "المعاييرُ الثلاثةُ عبرت ⇒ سقفُ النجاح في §⑨")
    return 2, ("فشلت", "أرضيّةٌ قائمةٌ وسقط معيارٌ ⇒ لا تُوصى، ويُنشَر الرقم")


def crit_halves(per_half: dict, pooled) -> dict:
    """موجبٌ في النصفين ‏+ فاصلُ المجمَّع لا يلمس الصفر · والقراءةُ الأشدّ تُطبَع."""
    hs = [h for h in ("H1", "H2") if per_half.get(h)]
    pos = all(per_half[h]["mean"] > 0 for h in hs) and len(hs) == 2
    lo = bool(pooled and pooled["lo"] > 0)
    strict = all(per_half[h]["lo"] > 0 for h in hs) and len(hs) == 2
    return {"pass": bool(pos and lo), "pos": pos, "lo": lo, "strict": strict,
            "halves": per_half, "pooled": pooled}


# ═══════════════ ⑥ حرّاسُ القراءة-فقط (على هذا الملفّ) ═════════════════════════
def selfcheck_readonly(src: str = None) -> bool:
    """`V-T4` — صفرُ إرسالٍ وصفرُ كتابةِ حالة (AST على هذا الملفّ).

    `src` مصدرٌ بديلٌ **للاختبار وحدَه** ⇒ يُتاح شاهدُ ضبطٍ يُثبت أن الحارسَ
    يمسك العيبَ لو وُجد، لا أن يمرّ لأنه لا يفحص شيئًا."""
    banned = {"send_telegram", "send_telegram_document", "git_save",
              "save_watchlist", "save_op_entry_state", "record_new_alerts",
              "save_near_watch", "save_hunter_watch"}
    try:
        tree = ast.parse(src if src is not None
                         else open(__file__, encoding="utf-8").read())
    except Exception:                                            # noqa: BLE001
        return False
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        fn = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
        if fn in banned:
            return False
        if fn == "open":
            mode = ""
            if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                mode = str(n.args[1].value)
            for kw in n.keywords or []:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = str(kw.value.value)
            if any(ch in mode for ch in ("w", "a", "x", "+")):
                return False
    return True


def no_config_assign(src: str = None) -> bool:
    """`V-T4`-ب — صفرُ إسنادٍ إلى `CONFIG` إطلاقًا (درسُ `RKA10`).

    `src` مصدرٌ بديلٌ **للاختبار وحدَه** — شاهدُ الضبط نفسُه."""
    try:
        tree = ast.parse(src if src is not None
                         else open(__file__, encoding="utf-8").read())
    except Exception:                                            # noqa: BLE001
        return False
    for n in ast.walk(tree):
        tgts = []
        if isinstance(n, ast.Assign):
            tgts = list(n.targets)
        elif isinstance(n, (ast.AugAssign, ast.AnnAssign)):
            tgts = [n.target]
        for t in tgts:
            if isinstance(t, ast.Subscript):
                nm = getattr(t.value, "id", None) or getattr(t.value, "attr", None)
                if nm == "CONFIG":
                    return False
        if isinstance(n, ast.Call):
            f = n.func
            if (isinstance(f, ast.Attribute) and f.attr in ("update", "setdefault")
                    and (getattr(f.value, "id", None)
                         or getattr(f.value, "attr", None)) == "CONFIG"):
                return False
    return True


def tsv_population(path: str = ROWS_TSV):
    """مُتعدَّدُ `(date, sym)` من الصفوف المنشورة — `V-T1`."""
    try:
        with open(path, encoding="utf-8") as fh:
            rows = [ln.rstrip("\n").split("\t") for ln in fh if ln.strip()]
    except Exception:                                            # noqa: BLE001
        return None
    if len(rows) < 2 or rows[0][:2] != ["date", "sym"]:
        return None
    return sorted((r[0], r[1]) for r in rows[1:])


# ═══════════════ ⑦ المسار ══════════════════════════════════════════════════════
def build_rows(key: str, anchors: dict, ledger: dict):
    """يبني صفوفَ المجتمع **بالترتيب نفسِه** الذي بنى به `T-OPCURVE` صفوفَه."""
    rows, fails, nobase = [], 0, 0
    cache, dcache = {}, {}
    for (day, sym), a in sorted(anchors.items()):
        bars = cache.get((sym, day))
        if bars is None:
            bars = fetch_day(sym, day, key)
            cache[(sym, day)] = bars or []
        if not bars:
            fails += 1
            continue
        b = ledger.get((day, sym))
        a_ms = int(a["anchor_ms"])
        ra = resolve_anchor(a, b, bars)                          # بالاسم
        ap = ra["ap"]
        e5 = (b or {}).get("e5")
        if not e5:
            e5, _x = true_e5(bars, a_ms, ap) if ap else (None, False)
        if not e5:
            nobase += 1
            continue
        f = features(a, b)
        tg = trig_bucket(a)
        rows.append({"date": day, "sym": sym,
                     "half": "H1" if day < H2_FROM else "H2",
                     "a_ms": a_ms, "e5": e5, "alow": ra["alow"],
                     "bars": bars, "f": f, "trig": tg,
                     # 🔒 السلالُ **بالاسم** من `buckets_of` ⇒ عضويّةُ `P2`/`P3`
                     #    تُقرأ من السلّة المنشورة لا تُكتب ثانيةً. و`exploded50`
                     #    سلّةُ نتيجةٍ لا تدخل ذراعًا فيُمرَّر `False` ولا يُقرأ.
                     "b": buckets_of(f, tg, False),
                     "tod": f["tod"], "cache": cache, "dcache": dcache})
    return rows, fails, nobase


def attach_trades(rows, key: str, costs: dict):
    """يُلحق بكلّ صفٍّ صفقةَ `P0`/`P1` وبديلاتِ الضبط — **بلا أيّ `R`** هنا.

    🔒 التكلفةُ و`R` تُحسبان في التجميع وحدَه ⇒ وضعُ الجدوى لا يمسّهما."""
    for r in rows:
        bars, e5, alow = r["bars"], r["e5"], r["alow"]
        t0 = r["a_ms"] + CARD_OFFSET_MS
        r["t0"] = t0
        r["P0"] = simulate(bars, t0, e5, alow, HSTAR)
        r["P1"] = simulate(bars, t0, e5, alow, HSTAR, use_target=False)
        r["P0_alt"] = simulate(bars, t0, e5, alow, HSTAR, tie_to_stop=False)
        r["W"] = {h: simulate(bars, t0, e5, alow, h) for h in W_GRID}
        abar = next((b for b in bars if b[0] == r["a_ms"]), None)
        r["ctrl"] = {}
        if r["P0"] is None or abar is None:
            continue
        prev_bars = None
        for mode in CONTROLS:
            gap = MOM_GAP_OVL if mode == "C-MOM-15" else MOM_GAP_MIN
            if mode == "C-MOM-15":
                pool = [b for b in bars
                        if b[0] < r["a_ms"] and r["a_ms"] - b[0] >= gap * 60_000
                        and tod_of(b[0]) == r["tod"]]
                lvl = "D0" if pool else "—"
            else:
                pool, lvl = placebo_pool(bars, None, r["a_ms"], r["tod"], gap)
                if not pool:                                     # `D1` — جلبةٌ واحدة
                    if prev_bars is None:
                        dl = r["dcache"].get((r["sym"], r["date"]))
                        if dl is None:
                            dl = daily_range(r["sym"], r["date"], key) or []
                            r["dcache"][(r["sym"], r["date"])] = dl
                        pv = [d for (d, _h, _c) in dl if d < r["date"]]
                        prev_bars = []
                        if pv:
                            pb = r["cache"].get((r["sym"], pv[-1]))
                            if pb is None:
                                pb = fetch_day(r["sym"], pv[-1], key) or []
                                r["cache"][(r["sym"], pv[-1])] = pb
                            prev_bars = pb
                    pool, lvl = placebo_pool(bars, prev_bars, r["a_ms"],
                                             r["tod"], gap)
            pb = pick_placebo(pool, abar, mode)
            if pb is None:
                r["ctrl"][mode] = {"lvl": "—", "tr": None}
                continue
            src = bars if (lvl == "D0" or mode == "C-MOM-15") else prev_bars
            tr, pe5, plow = placebo_trade(src, pb, HSTAR)
            r["ctrl"][mode] = {"lvl": lvl, "tr": tr, "e5": pe5, "alow": plow}
    return rows


# ═══════════════ ⑧ الأذرع — القائمةُ المُغلَقة (§④) ═══════════════════════════
def arm_subset(rows, arm: str):
    """صفوفُ الذراع · و`P2`/`P3` شريحتان من `P0` **بالسياسة نفسِها**."""
    if arm == "P1":
        return [r for r in rows if r.get("P1")]
    base = [r for r in rows if r.get("P0")]
    if arm == "P0":
        return base
    if arm == "P2":
        return [r for r in base if r["b"]["pre∧gap≥30%"] == "نعم"]
    if arm == "P3":
        return [r for r in base if r["b"]["tier"] == "قوي"]
    return []


def arm_key(arm: str) -> str:
    return "P1" if arm == "P1" else "P0"


def arm_R(r, arm: str, c: float, s: float):
    return trade_r(r.get(arm_key(arm)), r["e5"], r["alow"], c, s)


def arm_stats(rows, arm: str, c: float, s: float) -> dict:
    """`n` · متوسّطُ `R` وفاصلُه (مجمَّعًا وبالنصفين) · ونسبةُ التعبئة (‏`V-T5`)."""
    sub = arm_subset(rows, arm)
    fn = (lambda r: arm_R(r, arm, c, s))
    per = {}
    for h in ("H1", "H2"):
        hr = [r for r in sub if r["half"] == h]
        ci = ci_of(hr, fn) if hr else None
        if ci:
            per[h] = ci
    view = [(r[arm_key(arm)]["out"], r[arm_key(arm)]["r0"]) for r in sub]
    return {"arm": arm, "n": len(sub), "halves": per, "pooled": ci_of(sub, fn),
            "ret_pct": (e_resolved(view, c, s) if view else None),
            "fill": (fill_frac(view, len(sub)) if sub else None)}


def paired_ctrl(rows, mode: str, c: float, s: float):
    """`P0 − الضبط` **مقترنًا** (كلُّ مِرساةٍ مطروحًا منها بديلتُها) · والحصّةُ `D0`/`D1`."""
    pairs, lv = [], {"D0": 0, "D1": 0, "—": 0}
    for r in rows:
        ct = (r.get("ctrl") or {}).get(mode) or {}
        if not r.get("P0"):
            continue          # 🔒 لا صفقةَ أصلًا ⇒ لا يُعَدّ «بلا بديلة»
        lv[ct.get("lvl", "—")] = lv.get(ct.get("lvl", "—"), 0) + 1
        if not ct.get("tr"):
            continue
        a = trade_r(r["P0"], r["e5"], r["alow"], c, s)
        p = trade_r(ct["tr"], ct["e5"], ct["alow"], c, s)
        if a is None or p is None:
            continue
        pairs.append({"sym": r["sym"], "half": r["half"], "d": a - p,
                      "a": a, "p": p})
    per = {}
    for h in ("H1", "H2"):
        hp = [x for x in pairs if x["half"] == h]
        ci = ci_of(hp, lambda x: x["d"]) if hp else None
        if ci:
            per[h] = ci
    return {"mode": mode, "n": len(pairs), "lv": lv, "halves": per,
            "pooled": ci_of(pairs, lambda x: x["d"]),
            "a_mean": (st.mean(x["a"] for x in pairs) if pairs else None),
            "p_mean": (st.mean(x["p"] for x in pairs) if pairs else None),
            "counts": {h: sum(1 for x in pairs if x["half"] == h)
                       for h in ("H1", "H2")}}


def paired_arms(rows, a1: str, a2: str, c: float, s: float):
    """فرقٌ مقترنٌ بين ذراعين على **الصفوف نفسِها** (‏`OP5`)."""
    sub = [r for r in rows if r.get(arm_key(a1)) and r.get(arm_key(a2))]
    d = []
    for r in sub:
        x = arm_R(r, a1, c, s)
        y = arm_R(r, a2, c, s)
        if x is not None and y is not None:
            d.append({"sym": r["sym"], "d": x - y})
    return {"n": len(d), "pooled": ci_of(d, lambda z: z["d"])}


def csub(rows, arm: str, c: float, s: float):
    """`C-SUB` (§⑤-ج) — الجزئيّةُ تُقارَن **بمُكمِّلها** لا بالمجتمع."""
    sub = set(id(r) for r in arm_subset(rows, arm))
    comp = [r for r in arm_subset(rows, "P0") if id(r) not in sub]
    fn = (lambda r: arm_R(r, "P0", c, s))
    return {"n_sub": len(sub), "n_comp": len(comp),
            "sub": ci_of([r for r in arm_subset(rows, "P0") if id(r) in sub], fn),
            "comp": ci_of(comp, fn)}


def grid(rows, costs: dict):
    """شبكةُ الحساسيّة `c × s` (§③) — وصفيّةٌ تُطبَع دائمًا ولا تحكم."""
    cs = [("0", 0.0), ("C-P25", costs["C-P25"]),
          ("C-MED", costs["C-MED"]), ("C-P75", costs["C-P75"])]
    ss = [("0", 0.0), ("S-MED", costs["S-MED"])]
    out = []
    for cn, cv in cs:
        for sn, sv in ss:
            ci = ci_of(arm_subset(rows, "P0"),
                       lambda r, _c=cv, _s=sv: arm_R(r, "P0", _c, _s))
            out.append({"c": cn, "s": sn, "mean": (ci or {}).get("mean")})
    return out


def exit_mix(rows, arm: str):
    """حصّةُ كلّ سببِ خروجٍ بالنصفين (‏`OP4`)."""
    out = {}
    for h in ("H1", "H2", "الكلّ"):
        sub = [r for r in arm_subset(rows, arm)
               if h == "الكلّ" or r["half"] == h]
        n = len(sub)
        cnt = {k: sum(1 for r in sub if r[arm_key(arm)]["out"] == k)
               for k in ("win", "loss", "window")}
        out[h] = {"n": n, **{k: (v / n * 100.0 if n else None)
                             for k, v in cnt.items()}}
    return out


# ═══════════════ ⑨ التنبّؤاتُ السبعة (§⑦) — تُطبَع كما وقعت ═══════════════════
def predictions(rows, stats, ctrl, p10, mix, tie_share, alt_gap) -> list:
    """`OP1`-`OP3` منقولةٌ حرفيًّا من الحزمة · و`OP4`-`OP7` من العقد.

    **تشغيلُ `OP3` كُتب قبل أيّ رقم:** «يلتهم نصفَ الفرق» = حصّةُ ما تبقى للبديلة
    من مستوى الذراع على الأزواج ‏= `1 − d ÷ a` ‏≥ 0.5 (وعند `a = 0` يُعلَن «غيرُ منطبق»)."""
    out = []
    p0 = (stats["P0"]["pooled"] or {}).get("mean")
    out.append(("OP1", "`P0` سالبٌ بعد التكلفة",
                (p0 is not None and p0 < 0), f"توقّعُ P0 = {_n(p0)}R"))
    p2m = (stats["P2"]["pooled"] or {}).get("mean")
    p2n = stats["P2"]["n"]
    out.append(("OP2", "`P2` موجبٌ لكن `n<150` ⇒ لا حكم",
                (p2m is not None and p2m > 0 and p2n < FLOOR_ARM),
                f"P2 = {_n(p2m)}R · n = {p2n}"))
    a, d = ctrl["a_mean"], (ctrl["pooled"] or {}).get("mean")
    if a is None or d is None or abs(a) < 1e-12:
        out.append(("OP3", "`C-MOM` يلتهم نصفَ الفرق على الأقلّ", None,
                    "غيرُ منطبق (‏مستوى الذراع على الأزواج ≈ صفر أو لا أزواج)"))
    else:
        eaten = 1.0 - d / a
        out.append(("OP3", "`C-MOM` يلتهم نصفَ الفرق على الأقلّ", eaten >= 0.5,
                    f"الذراعُ على الأزواج {_n(a)}R · الفرقُ {_n(d)}R "
                    f"⇒ التهم {eaten*100:.1f}%"))
    okm = all((mix[h]["loss"] or 0) > (mix[h]["win"] or 0) for h in ("H1", "H2"))
    out.append(("OP4", "حصّةُ الوقف أكبرُ من حصّة الهدف في النصفين", okm,
                " · ".join(f"{h}: وقف {mix[h]['loss']:.1f}% مقابل هدف "
                           f"{mix[h]['win']:.1f}%" for h in ("H1", "H2")
                           if mix[h]["n"])))
    dm = (p10["pooled"] or {}).get("mean")
    out.append(("OP5", "`P1 − P0` سالب", (dm is not None and dm < 0),
                f"P1 − P0 = {_n(dm)}R على {p10['n']} صفًّا مقترنًا"))
    out.append(("OP6", "التعادلُ داخل الدقيقة دون ‏5% وأثرُ قلبه دون ‏0.05R",
                (tie_share is not None and tie_share < 5.0
                 and alt_gap is not None and abs(alt_gap) < 0.05),
                f"التعادل {tie_share:.2f}% · أثرُ القلب {_n(alt_gap)}R"))
    d0 = ctrl["lv"].get("D0", 0)
    tot = sum(v for k, v in ctrl["lv"].items() if k in ("D0", "D1"))
    sh = (d0 / tot * 100.0) if tot else None
    out.append(("OP7", "حصّةُ `D0` دون ‏60% من الأزواج",
                (sh is not None and sh < 60.0),
                f"D0 = {d0} · D1 = {ctrl['lv'].get('D1', 0)}"
                + (f" ⇒ {sh:.1f}%" if sh is not None else "")))
    return out


def tsv_block(rows, c: float, s: float) -> list:
    """مُخرَجٌ آليٌّ للاستخراج — صفٌّ لكلّ مِرساةٍ بلا قصّ."""
    out = ["⟦TSV⟧", "\t".join(TSV_COLS)]
    for r in sorted(rows, key=lambda x: (x["date"], x["sym"])):
        t = r.get("P0")
        ct = (r.get("ctrl") or {}).get("C-MOM") or {}
        pt = ct.get("tr")
        R = trade_r(t, r["e5"], r["alow"], c, s) if t else None
        pR = (trade_r(pt, ct.get("e5"), ct.get("alow"), c, s)
              if pt and ct.get("e5") else None)

        def _f(v, nd=4):
            return "—" if v is None else f"{v:.{nd}f}"
        out.append("\t".join([
            r["date"], r["sym"], r["half"], r["tod"], r["f"]["tier"],
            r["f"]["gap"], r["trig"], _f(r["e5"]), _f(r["alow"]),
            _f(t["risk_pct"], 2) if t else "—",
            (t["out"] if t else "—"), _f(t["r0"], 2) if t else "—", _f(R),
            _f(t["t_exit"], 1) if t else "—", _f(t["win_min"], 1) if t else "—",
            ("نعم" if t and t["tie"] else "لا") if t else "—",
            ct.get("lvl", "—"), (pt["out"] if pt else "—"),
            _f(pt["r0"], 2) if pt else "—", _f(pR)]))
    out.append("⟦/TSV⟧")
    return out


# ═══════════════ ⑩ main ════════════════════════════════════════════════════════
def main() -> int:                                               # noqa: PLR0911, PLR0915
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        _log("⛔ لا POLYGON_API_KEY — خروج 2")
        return RC_NOKEY
    if not (selfcheck_readonly() and no_config_assign()):
        _log("⛔ V-T7 — حارسُ «قراءةٌ فقط / صفرُ إسناد» ساقط — خروج 6")
        return RC_GUARD
    costs = read_costs()
    if not costs.get("ok"):
        _log(f"⛔ V-T3 — تعذّر استخراجُ التكلفة من النتيجة المنشورة: "
             f"{costs.get('why')} — خروج 6")
        return RC_GUARD
    hs = read_hstar()
    if not hs.get("ok"):
        _log(f"⛔ V-T6 — نافذةُ الخروج لا تطابق المنشور: {hs.get('why')} — خروج 6")
        return RC_GUARD
    rid, rmsg = roots_identical()                                # بالاسم
    C, S = costs["C-MED"], costs["S-MED"]
    frozen = UNTIL == FROZEN_UNTIL
    _log("🕵️💥 T-OPTRADE — سياسةُ مضاربةٍ واحدةٌ بعد المِرساة (العقد optrade_prereg.md)")
    _log(f"⚙️ الحدود: منذ {SINCE} · H2 من {H2_FROM} · حتى "
         f"{UNTIL or 'يوم التشغيل'} · نافذةُ الخروج {HSTAR} دقيقة "
         f"(منشورةٌ ومطابَقة) · الهدف +{HIT_PCT:.0f}%")
    _log(f"💸 التكلفةُ **مستخرَجةٌ نصًّا** من نتيجة T-BTCOST: C-MED {C*100:.4f}% · "
         f"S-MED {S*100:.4f}% · C-P25 {costs['C-P25']*100:.4f}% · "
         f"C-P75 {costs['C-P75']*100:.4f}% · ومعامِلُ الدخول k(C-MED) = {k_of(C):.6f}")
    _log(f"🌳 الجذور: {'مطابقة' if rid else '⚠️ ' + rmsg}")
    if not frozen:
        _log("⚠️⚠️ النافذةُ ليست المجمَّدة ⇒ V-T1 غيرُ منطبق · والأرقامُ **وصفيّةٌ** "
             "والحكمُ يُجبَر على «لا حكم» (المعاييرُ معرَّفةٌ على المجتمع المجمَّد).")
    anchors = anchor_history(SINCE)
    if UNTIL:
        anchors = {k: v for k, v in anchors.items() if k[0] <= UNTIL}
    if not anchors:
        _log("⛔ صفرُ مِرساةٍ في تاريخ git — خروج 4")
        return RC_NOANCHOR
    ledger = {(r["date"], r["symbol"]): r for r in load_ledger()}
    _log(f"📚 مراسٍ {len(anchors)} · سجلّ M5 {len(ledger)}")
    rows, fails, nobase = build_rows(key, anchors, ledger)
    cover = len(rows) / len(anchors)
    _log(f"🩺 التغطية: قِيس {len(rows)} · تعذّر الجلب {fails} · بلا أساس {nobase} "
         f"من {len(anchors)} = {cover*100:.1f}%")
    if cover < MIN_COVER:
        _log("⛔ التغطية دون الحدّ ⇒ لا يُفسَّر رقم — خروج 3")
        return RC_COVER
    if frozen:
        pub = tsv_population()
        got = sorted((r["date"], r["sym"]) for r in rows)
        if pub is None:
            _log("⛔ V-T1 — الصفوفُ المنشورةُ غيرُ مقروءة — خروج 5")
            return RC_POP
        if pub != got:
            miss = sorted(set(pub) - set(got))[:5]
            extra = sorted(set(got) - set(pub))[:5]
            _log(f"⛔ V-T1 — المجتمعُ يخالف المنشور: هنا {len(got)} · منشور "
                 f"{len(pub)} · ناقصٌ {miss} · زائدٌ {extra} — خروج 5")
            return RC_POP
        h1 = sum(1 for r in rows if r["half"] == "H1")
        _log(f"🔒 V-T1: المجتمعُ مطابقٌ بت-بت للصفوف المنشورة "
             f"({len(got)} صفًّا · H1 {h1} · H2 {len(got)-h1})")
    attach_trades(rows, key, costs)
    # ── العدّادات (تُطبَع دائمًا · وكلُّ قصٍّ بعدّاده) ──────────────────────────
    untr = [r for r in rows if r["alow"] is None or r["e5"] <= r["alow"]]
    nobar = [r for r in rows if r not in untr and r["P0"] is None]
    tradable = [r for r in rows if r.get("P0")]
    ties = sum(1 for r in tradable if r["P0"]["tie"])
    tie_share = ties / len(tradable) * 100.0 if tradable else None
    per_half_n = {h: sum(1 for r in tradable if r["half"] == h)
                  for h in ("H1", "H2")}
    lv = {"D0": 0, "D1": 0, "—": 0}
    for r in tradable:          # 🔒 على القابل للتداول لا على المعالَج
        ct = (r.get("ctrl") or {}).get("C-MOM") or {}
        lv[ct.get("lvl", "—")] = lv.get(ct.get("lvl", "—"), 0) + 1
    _log(f"🧮 القابلُ للتداول {len(tradable)} (H1 {per_half_n['H1']} · "
         f"H2 {per_half_n['H2']}) · غيرُ قابلٍ (سعرُ الكرت عند القاع أو دونه) "
         f"{len(untr)} · بلا شموعٍ بعد الكرت {len(nobar)}")
    _log(f"🔀 بديلةُ C-MOM: D0 {lv['D0']} · D1 {lv['D1']} · بلا بديلة {lv['—']}")
    if tradable:
        _log(f"⚖️ التعادلُ داخل الدقيقة: {ties} من {len(tradable)} = "
             f"{tie_share:.2f}%")
    else:
        _log("⚖️ لا صفقات")
    if DRY:
        _log("🧪 وضعُ الجدوى — ثلاثةُ أعدادٍ فقط · صفرُ R وصفرُ عائدٍ وصفرُ فرقٍ "
             "وصفرُ فاصل. ⚠️ ودرسُ T-PMGATE: وضعُ الجدوى يُجيز ما يمرّ به وحدَه "
             "فلا يُقرأ إذنًا للمسار كلِّه.")
        return RC_OK
    return report(rows, tradable, per_half_n, lv, tie_share, costs, frozen)


def _ci_txt(ci) -> str:
    if not ci:
        return "—"
    return (f"{_n(ci['mean'])}R [{_n(ci['lo'])}, {_n(ci['hi'])}] "
            f"n={ci['n']} · رموز={ci['k']}")


def report(rows, tradable, per_half_n, lv, tie_share, costs, frozen) -> int:  # noqa: PLR0915
    """يطبع كلَّ ما يقوله العقد ثمّ يُصدر الفرعَ من `read_verdict` بحرفه."""
    C, S = costs["C-MED"], costs["S-MED"]
    stats = {a: arm_stats(rows, a, C, S) for a in ARMS}
    _log("")
    _log("═══ ⓪ تركيبةُ السلال المنشورة (أعدادٌ فقط · تقويةٌ لـV-T1) ═══")
    for bk in ("trig", "tod", "tier", "gap", "pre∧gap≥30%"):
        cnt = {}
        for r in rows:
            cnt[r["b"][bk]] = cnt.get(r["b"][bk], 0) + 1
        _log(f"  {bk:12s} " + " · ".join(f"{k}={v}"
                                        for k, v in sorted(cnt.items())))
    _log("")
    _log("═══ ① الأذرع عند الخليّة الحاكمة (C-MED, S-MED) — متوسّطُ R لكلّ صفقة ═══")
    for a in ARMS:
        s = stats[a]
        _log(f"  {a:3s} n={s['n']:4d} · تعبئة {(s['fill'] or 0)*100:5.1f}% · "
             f"مجمَّع {_ci_txt(s['pooled'])}")
        for h in ("H1", "H2"):
            if s["halves"].get(h):
                _log(f"        {h}: {_ci_txt(s['halves'][h])}")
        _log(f"        متوسّطُ العائد ٪ (سياقٌ لا حكم): "
             f"{_n(s['ret_pct'], 3) if s['ret_pct'] is not None else '—'}%")
    _log("")
    _log("═══ ② الخليّةُ (C-MED, 0) ملاصقةً — لأن S-MED سالبٌ يُجمّل الخاسر ═══")
    z = arm_stats(rows, "P0", C, 0.0)
    _log(f"  P0 عند (C-MED, 0): {_ci_txt(z['pooled'])}")
    _log("")
    _log("═══ ③ شبكةُ الحساسيّة c × s — وصفيّةٌ لا تحكم ═══")
    g = grid(rows, costs)
    signs = set()
    for cell in g:
        if cell["mean"] is not None:
            signs.add(cell["mean"] > 0)
        _log(f"  c={cell['c']:6s} s={cell['s']:6s} ⇒ P0 = "
             f"{_n(cell['mean']) if cell['mean'] is not None else '—'}R")
    fragile = len(signs) > 1
    _log(f"  ⇒ {'🔴 الإشارةُ تنقلب داخل الشبكة ⇒ الحكمُ **هشّ**' if fragile else '✅ الإشارةُ لا تنقلب في أيّ خليّة'}")
    _log("")
    _log(f"═══ ④ حساسيّةُ النافذة — و`h*` = {HSTAR} **اختيارٌ داخلَ العيّنة** (§⓪-1) ═══")
    wbest, wtab = None, []
    for h in W_GRID:
        sub = [r for r in rows if r["W"].get(h)]
        ci = ci_of(sub, lambda r, _h=h: r_fixed(
            ret_at(r["W"][_h]["r0"], r["W"][_h]["out"], C, S),
            r["e5"], r["e5"], r["alow"]))
        nm = "EOD" if h is None else f"{h}د"
        wtab.append((nm, ci))
        _log(f"  نافذة {nm:5s} ⇒ {_ci_txt(ci)}")
        if ci and (wbest is None or ci["mean"] > wbest[1]):
            wbest = (nm, ci["mean"])
    if wbest:
        _log(f"  ⇒ أفضلُ نافذةٍ بين الستّ: **{wbest[0]}** ({_n(wbest[1])}R) — "
             f"{'وهي الحاكمة ⇒ يُقال صراحةً إنه اختيارٌ داخلَ العيّنة لا نتيجة' if wbest[0] == f'{HSTAR}د' else 'والحاكمةُ غيرُها ⇒ الحاكمةُ تبقى بنصّ العقد'}")
    _log("")
    _log("═══ ⑤ حصّةُ كلّ سببِ خروجٍ (P0) ═══")
    mix = exit_mix(rows, "P0")
    for h in ("H1", "H2", "الكلّ"):
        m = mix[h]
        if m["n"]:
            _log(f"  {h:6s} n={m['n']:4d} · هدف {m['win']:5.1f}% · وقف "
                 f"{m['loss']:5.1f}% · نافذة {m['window']:5.1f}%")
    _log("")
    _log("═══ ⑥ الضبط — C-MOM حاكمٌ · والباقي وصفيّ ═══")
    ctrls = {m: paired_ctrl(rows, m, C, S) for m in CONTROLS}
    for m in CONTROLS:
        cc = ctrls[m]
        tag = "**حاكم**" if m == "C-MOM" else "وصفيّ"
        _log(f"  {m:9s} ({tag}) أزواج={cc['n']:4d} "
             f"(H1 {cc['counts']['H1']} · H2 {cc['counts']['H2']}) · "
             f"D0 {cc['lv'].get('D0',0)} · D1 {cc['lv'].get('D1',0)} · "
             f"بلا بديلة {cc['lv'].get('—',0)}")
        _log(f"            الذراعُ على الأزواج {_n(cc['a_mean'])}R · البديلةُ "
             f"{_n(cc['p_mean'])}R · الفرقُ المقترن {_ci_txt(cc['pooled'])}")
        for h in ("H1", "H2"):
            if cc["halves"].get(h):
                _log(f"            {h}: {_ci_txt(cc['halves'][h])}")
    _log("")
    _log("═══ ⑦ C-SUB — الجزئيّةُ تُقارَن بمُكمِّلها لا بالمجتمع (§⑤-ج) ═══")
    for a in ("P2", "P3"):
        cs = csub(rows, a, C, S)
        _log(f"  {a}: الشريحة n={cs['n_sub']} {_ci_txt(cs['sub'])}")
        _log(f"      المُكمِّل n={cs['n_comp']} {_ci_txt(cs['comp'])}")
    _log("")
    _log("═══ ⑧ المعايير والحكم (§⑥ بحرفه) ═══")
    ot3 = {"halves": per_half_n,
           "pass": all(per_half_n[h] >= FLOOR_ARM for h in ("H1", "H2"))}
    cm = ctrls["C-MOM"]
    ot2_floor = all(cm["counts"][h] >= FLOOR_PAIR for h in ("H1", "H2"))
    ot1 = crit_halves(stats["P0"]["halves"], stats["P0"]["pooled"])
    ot2 = crit_halves(cm["halves"], cm["pooled"])
    ot2["floor"] = ot2_floor
    _log(f"  OT3 أرضيّةُ الذراع ≥{FLOOR_ARM} في كلّ نصف: H1 {per_half_n['H1']} · "
         f"H2 {per_half_n['H2']} ⇒ {'✅' if ot3['pass'] else '🔴'}")
    _log(f"  أرضيّةُ OT2 ≥{FLOOR_PAIR} زوجًا في كلّ نصف: H1 {cm['counts']['H1']} · "
         f"H2 {cm['counts']['H2']} ⇒ {'✅' if ot2_floor else '🔴'}")
    _log(f"  OT1 توقّعُ R بعد التكلفة: موجبٌ في النصفين "
         f"{'✅' if ot1['pos'] else '🔴'} · فاصلُ المجمَّع لا يلمس الصفر "
         f"{'✅' if ot1['lo'] else '🔴'} ⇒ {'✅' if ot1['pass'] else '🔴'} "
         f"(والقراءةُ الأشدّ — فاصلٌ لكلّ نصف — "
         f"{'تعبر أيضًا' if ot1['strict'] else 'لا تعبر'})")
    _log(f"  OT2 P0 − C-MOM مقترنًا: موجبٌ في النصفين "
         f"{'✅' if ot2['pos'] else '🔴'} · فاصلُ المجمَّع لا يلمس الصفر "
         f"{'✅' if ot2['lo'] else '🔴'} ⇒ {'✅' if ot2['pass'] else '🔴'} "
         f"(والأشدّ {'تعبر' if ot2['strict'] else 'لا تعبر'})")
    branch, (name, why) = read_verdict(ot1, ot2, ot3)
    if not frozen and branch != 3:
        branch, name, why = 3, "لا حكم", "النافذةُ غيرُ مجمَّدة ⇒ الأرقامُ وصفيّة"
    _log(f"  ⇒ **الفرعُ {branch} — {name}**: {why}")
    _log("")
    _log("═══ ⑨ التنبّؤاتُ السبعة — تُنشَر كما وقعت ═══")
    p10 = paired_arms(rows, "P1", "P0", C, S)
    both = [r for r in rows if r.get("P0") and r.get("P0_alt")]
    alt_gap = None
    if both:
        alt_gap = (st.mean(trade_r(r["P0_alt"], r["e5"], r["alow"], C, S)
                           for r in both)
                   - st.mean(trade_r(r["P0"], r["e5"], r["alow"], C, S)
                             for r in both))
    for tag, txt, ok, detail in predictions(rows, stats, cm, p10, mix,
                                            tie_share, alt_gap):
        mark = "✅" if ok else ("🔴" if ok is False else "⚪")
        _log(f"  {mark} {tag}: {txt} — {detail}")
    _log("")
    _log("═══ ⑩ حدودُ صدقٍ (§⑧) تُطبَع في كلّ تقرير ═══")
    med_a = st.median([r["P0"]["win_min"] for r in tradable]) if tradable else None
    te = sorted(r["P0"]["t_exit"] for r in tradable)
    if te:
        _log(f"  • زمنُ الخروج (دقائق · رتبةٌ أقرب): p25 {pctile(te, 25):.0f} · "
             f"p50 {pctile(te, 50):.0f} · p75 {pctile(te, 75):.0f} · "
             f"p90 {pctile(te, 90):.0f}")
    _log("  • لمسٌ لا تنفيذ: الهدفُ لمسةُ قمّةٍ (متفائل) والوقفُ إغلاقُ دقيقةٍ "
         "(متحفّظ) ⇒ الرقمُ سقفُ أداءٍ لا أرضية.")
    _log("  • C-MED/S-MED **مستعارتان** من مجتمع محرّك الباكتيست لا مجتمع "
         "المِرساة ⇒ نقلٌ مُعلَن لا قياس (ولذلك شبكةُ الحساسيّة أعلاه).")
    _log(f"  • النافذةُ المتاحةُ فعلًا وسيطًا {med_a:.0f} دقيقة من {HSTAR} "
         "⇒ ما قُصّ بنهاية البيانات يُقال لا يُطوى." if med_a is not None else
         "  • النافذةُ المتاحة: لا صفقات.")
    _log("  • ‏≈4 أسابيعَ من سوقٍ واحد · والمجتمعُ ما صمد في آخر لقطةِ يومه "
         "(المكتومُ ببوّابة المضارب ليس فيه).")
    _log("  • C-MOM لا يضبط الاختيارَ المقطعيّ · وD1 يضبط السهمَ والجلسةَ لا اليوم.")
    _log("  • ‏64% من الانفجارات بلا مِرساةٍ أصلًا ⇒ سقفُ أيّ سياسةٍ ‏≈36% من الفرص.")
    _log("  • بلا رسوم ولا طابورٍ ولا تعبئةٍ جزئيّة · وانحيازُ البقاء قائم.")
    _log("")
    for ln in tsv_block(rows, C, S):
        _log(ln)
    return RC_OK if branch in (1, 2) else RC_NOVERDICT


if __name__ == "__main__":
    sys.exit(main())
