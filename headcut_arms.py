#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🎯✂️ `T-HEADCUT` — **«بِع قبل رأس شمعة الهبوط»** · مجتمعُ `E-BT` الحاكم.

**العقد:** `headcut_prereg.md` (مدفوعٌ ومدموجٌ قبل هذا الملفّ ولم يُمَسّ).
أمرُ المالك «نفذ جميع النواقص» (‏2026-09-19).

**السؤال (`§⓪`):** هل قصُّ الهدف **قبل** رأس شمعة الهبوط — على نفس الصفقات
وبنفس الدخول ونفس الوقف — يُحسّن التوقّعَ؟ **وهل الأثرُ يخصّ الرأسَ أم هو
«هدفٌ أدنى عمومًا»؟** (‏الشاهدُ `C-HEAD` هو الذي يفصلهما · و`C-BACK` يقيس
الاتّجاه المعاكس.)

🔒 **المجتمعُ عينُ مجتمع `T-TRAIL`/`T-EXITMGMT` لا مثيلٌ له:** لقطاتُ PIT
الثلاث نفسُها · وفلترُ الطول `MIN_BARS + 60` المجمَّد · والمِرساةُ والسلّمُ
والخطّةُ **مستورَدةٌ بالاسم** — **و`V-H1` يُثبت أن `H0` يُعيد `Y0` المنشورَ في
`trail_result.md` بت-بت أو يخرج 5 قبل أيّ رقم.**

🔒 **صفرُ منطقِ حسمٍ مكرَّر:** `exitmgmt_arms.resolve_exit`/`anchor_at`/`ladder`/
`boot_ci`/`pool_clusters` · `tranche_arms.plan_at`/`r_fixed` ·
`optrade_arms.selfcheck_readonly`/`no_config_assign` · و`Super_stock.
_red_candle_heads` — **كلُّها بالاسم**.

🔴 **والمحورُ مُغلَقٌ بحكم `T-TRAIL`** («إدارةُ الخروج بعد الدخول») ⇒ هذا العقدُ
**يستوفي شروطَ فتحه الثلاثةَ صراحةً** (‏`headcut_prereg.md §⓪`) · **وإغلاقُ
`T-TRAIL` نفسُه لا يُمَسّ ولا يُضبَط `TRAIL_REOPEN` من هنا إطلاقًا.**

🔒 **قراءةٌ فقط:** صفرُ إرسالٍ · صفرُ كتابةِ ملفّ · صفرُ إسنادٍ إلى `CONFIG` ·
والإنتاجُ لا يستورد هذا الملفّ. **ولا يُشحَن منه شيءٌ مهما كانت النتيجة.**

**رموزُ الخروج:** 0 صدر حكمٌ (الفرعان 1 و2) · 2 مدخلاتٌ ناقصة · 3 عطبُ أداة ·
**5 حارسُ هُويّةٍ ساقط (`V-H1`)** · **9 «لا حكم» (الفرعُ 3)**.
"""
from __future__ import annotations

import os

os.environ.setdefault("SCREENER_MODE", "BACKTEST")   # قبل أيّ استيرادٍ للإنتاج

import re                                                        # noqa: E402
import sys                                                       # noqa: E402

from exitmgmt_arms import (anchor_at, boot_ci, ladder,            # noqa: E402
                           pool_clusters, resolve_exit)
from tranche_arms import plan_at, r_fixed                         # noqa: E402

TRAIL_RESULT = "trail_result.md"     # `V-H1` — المنشورُ يُقرأ لا يُكتَب بيدي
FLOOR_ROWS = 150                     # §⑥-3 أرضيّةُ «لا حكم»
MATERIAL = 0.08                      # §⑤ `HC2` — **شرطُ فتح المحور** لا اختياري
HEAD_TOL = 0.5                       # §④ `C-HEAD` — `engineering` مُعلَن
LEN_PAD = 60                         # 🧊 فلترُ الطول المجمَّدُ على `T-TRANCHE`
RET_ND = 1                           # 🧊 التكميمُ المجمَّد (خانةٌ واحدة)

# §④ — قائمةٌ **مُغلَقة**: (الاسم · نسبةُ القصّ `h` بالمئة)
ARMS = (("H0", 0.0), ("H1", 1.0), ("Hh", 0.5), ("H2", 2.0), ("H3", 3.0),
        ("C-BACK", -1.0))
BASE, GOV, CTRL = "H0", "H1", "C-BACK"
DESC = ("Hh", "H2", "H3")            # §④ — وصفيّةٌ لا تحكم

RC_OK, RC_INPUT, RC_TOOL, RC_POP, RC_NOVERDICT = 0, 2, 3, 5, 9
DRY = os.environ.get("HEADCUT_DRY", "").strip() == "1"
TSV_ON = os.environ.get("HEADCUT_TSV", "").strip() == "1"


def _log(msg: str = "") -> None:
    print(msg, flush=True)


# ═══════════ ① المُصيِّرُ — الهدفُ المقصوص وحدَه هو المتغيّر ════════════════
def cut_t1(t1, h):
    """`§②` — `t1_eff(h) = t1 × (1 − h/100)`. **دالّةٌ نقيّة**: عند `h = 0`
    تُعيد `t1` **بالضبط** (`V-H2`)، وعند `h < 0` ترفع الهدفَ (`C-BACK`)."""
    return float(t1) if not h else float(t1) * (1.0 - float(h) / 100.0)


def cut_exit(hi, lo, cl, op, entry, stop, t1, filled, h=0.0, spread=0.0):
    """يحسم الصفقةَ بهدفٍ مقصوص — **بلا أيّ إدارةٍ أخرى**.

    🔒 وعند `h = 0` **هو `exitmgmt_arms.resolve_exit` نفسُه بلا وسيطٍ زائد**
    ⇒ لا مِقياسَ ثانٍ على المجتمع."""
    return resolve_exit(hi, lo, cl, op, entry, stop, cut_t1(t1, h), filled,
                        spread=spread)


# ═══════════ ② `V-H1` — المنشورُ يُستخرَج نصًّا ═══════════════════════════════
_VT1 = re.compile(r"`V-H?T?1`\s*(\d{4})")
_TRIPLE = re.compile(r"([−\-]?\d+\.\d+)\s*·\s*(\d+)/(\d+)\s*·\s*(\d+)/(\d+)")


def read_published(path: str = TRAIL_RESULT) -> dict:
    """`V-H1` — `{سنة: {r, rows, fill}}` من صفوف `V-T1` في `trail_result.md`.

    🔒 **لا رقمَ يُكتَب بيدي** — والعمودُ الثالثُ موحّدُ الشكل في الصفوف الثلاثة
    (`‏−0.2602 · 1620/1620 · 1399/1399`)."""
    try:
        txt = open(path, encoding="utf-8").read()
    except Exception as e:                                       # noqa: BLE001
        return {"ok": False, "why": f"تعذّر فتحُ {path}: {type(e).__name__}"}
    out = {}
    for ln in txt.splitlines():
        if not ln.lstrip().startswith("|") or "V-T1" not in ln:
            continue
        my = _VT1.search(ln)
        mt = _TRIPLE.search(ln)
        if not (my and mt):
            continue
        out[my.group(1)] = {"r": float(mt.group(1).replace("−", "-")),
                            "rows": int(mt.group(2)), "fill": int(mt.group(4))}
    if len(out) < 3:
        return {"ok": False, "why": f"صفوفُ `V-T1` الثلاثةُ غيرُ مقروءة ({len(out)})"}
    out["ok"], out["years"] = True, sorted(k for k in out if k.isdigit())
    return out


# ═══════════ ③ الحرّاس ════════════════════════════════════════════════════════
def guards_ok() -> tuple:
    """`V-H5` — قراءةٌ فقط · صفرُ إسنادٍ إلى `CONFIG` (بالاسم من `optrade_arms`)."""
    from optrade_arms import (no_config_assign,                   # noqa: PLC0415
                              selfcheck_readonly)
    try:
        src = open(__file__, encoding="utf-8").read()
    except Exception as e:                                       # noqa: BLE001
        return False, f"تعذّر قراءةُ المصدر: {type(e).__name__}"
    ro, na = selfcheck_readonly(src), no_config_assign(src)
    return (ro and na), f"قراءةٌ فقط={ro} · صفرُ إسناد={na}"


def selfcheck_v2(n: int = 4000, seed: int = 20260919) -> int:
    """`V-H2` — **بوّابةُ التعريف**: `cut_t1(t1, 0) == t1` بالضبط ·
    و`< t1` لكلّ `h > 0` · و`> t1` لـ`h < 0`. وتُعاد على مدخلاتٍ عشوائيّةٍ
    ببذرةٍ ثابتة فلا تُصدَّق بحالةٍ واحدة."""
    import random
    rnd = random.Random(seed)
    bad = 0
    for _ in range(n):
        t1 = rnd.uniform(0.05, 900.0)
        if cut_t1(t1, 0.0) != t1 or cut_t1(t1, 0) != t1:
            bad += 1
            continue
        if not (cut_t1(t1, 1.0) < t1 < cut_t1(t1, -1.0)):
            bad += 1
    return bad


# ═══════════ ④ بناءُ الصفوف ══════════════════════════════════════════════════
def is_head_target(S, df_slice, t1, tol=HEAD_TOL) -> bool:
    """`§④` — هل `t1` رأسُ شمعةٍ حمراء (ضمن `tol`%)؟

    🔒 **النداءُ يُعاد كما يُنفّذه الإنتاج:** `analyze_ticker` يحسب
    `price = float(c[-1])` ثمّ `_red_candle_heads(df, price)` ⇒ نمرّر
    **آخرَ إغلاقٍ في الشريحة نفسِها**، فالمُخرَجُ هو مُخرَجُ الإنتاج لا شبيهُه."""
    try:
        px = float(df_slice["Close"].iloc[-1])
        heads = [float(x) for x in S._red_candle_heads(df_slice, px)]
    except Exception:                                            # noqa: BLE001
        return False
    t = float(t1)
    return any(abs(hd - t) / t * 100.0 <= tol for hd in heads if t > 0)


def arms_for(S, sym, df, tr, fwd, spread, n_tr, step_pct):
    """يحسم الأذرعَ الستَّ على **نفس الشموع ونفس الدخول ونفس الوقف** —
    المتغيّرُ **الهدفُ وحدَه** (`§②`-4). منقولُ البنية من `trail_arms.arms_for`
    حرفيًّا (المِرساةُ والسلّمُ والخطّةُ والتكميم) فيبقى `H0` مطابقًا للمنشور."""
    try:
        import pandas as pd                                      # noqa: PLC0415
        pos = df.index.get_loc(pd.Timestamp(tr["date"]))
    except Exception:                                            # noqa: BLE001
        return None, "تاريخٌ غيرُ موجود"
    i = int(pos) + 1
    pl = plan_at(S, sym, df, i)                                  # بالاسم
    if pl is None:
        return None, "تعذّرت إعادةُ الخطّة"
    anchor = anchor_at(S, df.iloc[:i], pl)                       # بالاسم
    if anchor is None:
        return None, "بلا مِرساة"
    stop, t1 = pl["stop"], pl["t1"]
    fut = df.iloc[i:i + fwd]
    if not len(fut):
        return None, "نافذةٌ فارغة"
    hi = fut["High"].values.astype(float)
    lo = fut["Low"].values.astype(float)
    cl = fut["Close"].values.astype(float)
    op = fut["Open"].values.astype(float)

    trs = ladder(anchor, n_tr, step_pct)                         # بالاسم
    entry = sum(trs) / len(trs)
    if entry - stop <= 0:
        return None, "مقامُ المخاطرة غيرُ موجب"
    if t1 <= entry:
        return None, "هدفٌ دون الدخول"
    filled = next((k for k in range(len(fut)) if lo[k] <= entry), None)
    row = {"symbol": sym, "date": tr["date"], "stop": round(stop, 4),
           "t1": round(t1, 4), "e": round(entry, 4),
           "head": bool(is_head_target(S, df.iloc[:i], t1)),
           "k": round((t1 - entry) / (entry - stop), 6)}
    for name, h in ARMS:
        o, rt, _info = cut_exit(hi, lo, cl, op, entry, stop, t1, filled,
                                h=h, spread=spread)
        row[f"o_{name}"] = o
        row[f"ret_{name}"] = (round(rt, RET_ND) if rt is not None else None)
    return row, None


def r_row(r, name):
    """`R₀` لذراعٍ على صفّ — `no_fill` = **صفرٌ يدخل المقام** · والمقامُ
    `entry − stop` **واحدٌ للأذرع الستّ** (`§②`-1)."""
    o = r.get(f"o_{name}")
    if o is None:
        return None
    if o == "no_fill":
        return 0.0
    return r_fixed(r.get(f"ret_{name}"), r["e"], r["e"], r["stop"])  # بالاسم


def pair_clusters(rows, a: str, b: str) -> dict:
    """عناقيدُ فرقِ `a − b` **مقترنًا** (نفسُ الصفقة) — العنقودُ **الرمز**."""
    g = {}
    for r in rows:
        va, vb = r_row(r, a), r_row(r, b)
        if va is None or vb is None:
            continue
        n, s = g.get(r["symbol"], (0, 0.0))
        g[r["symbol"]] = (n + 1, s + (va - vb))
    return g


def agg(rows, name: str) -> dict:
    fx, n_fill, wins, losses, opens = [], 0, 0, 0, 0
    for r in rows:
        o = r.get(f"o_{name}")
        if o is None:
            continue
        if o == "no_fill":
            fx.append(0.0)
            continue
        n_fill += 1
        wins += (o == "win")
        losses += (o == "loss")
        opens += (o == "open")
        v = r_row(r, name)
        fx.append(v if v is not None else 0.0)
    n = len(fx)
    return {"n": n, "n_fill": n_fill, "win": wins, "loss": losses, "open": opens,
            "fill_pct": (n_fill / n * 100.0) if n else 0.0,
            "win_pct": (wins / n_fill * 100.0) if n_fill else 0.0,
            "loss_pct": (losses / n_fill * 100.0) if n_fill else 0.0,
            "open_pct": (opens / n_fill * 100.0) if n_fill else 0.0,
            "r": (sum(fx) / n) if n else 0.0}


# ═══════════ ⑤ الحكمُ — دالّةٌ نقيّةٌ تطبّق `§⑥` بحرفه ═══════════════════════
def read_verdict(hc1: dict, hc2: dict, hc3: dict, hc4: dict) -> tuple:
    """فروعُ `§⑥` **بحرفها** — ولا فرعَ رابع.

    كلُّ وسيطٍ `{"ok": bool, "floor": bool}` · و`floor` كاذبٌ ⇒ الفرعُ 3."""
    if not all(x.get("floor", True) for x in (hc1, hc2, hc3, hc4)):
        return RC_NOVERDICT, ("الفرعُ 3 — **لا حكم**: الأرضيّةُ لم تُبلَغ أو "
                              "سقط حارس · تُعلَن بعددها ولا تُفسَّر")
    if all(x.get("ok") for x in (hc1, hc2, hc3, hc4)):
        return RC_OK, ("الفرعُ 1 — **تُوصى**: تُقترَح على المالك **اقتراحًا لا "
                       "تنفيذًا** · **ولا يُشحَن شيءٌ بهذا العقد**")
    return RC_OK, ("الفرعُ 2 — **لا تُوصى**: سقط "
                   + " · ".join(n for n, x in (("HC1", hc1), ("HC2", hc2),
                                               ("HC3", hc3), ("HC4", hc4))
                                if not x.get("ok")))


def crit(per_year: list, pooled, bar: float = 0.0) -> dict:
    """موجبٌ في كلّ سنة **و**فاصلٌ مجمَّعٌ لا يلمس `bar`."""
    pos = all(v > bar for _y, v, _n in per_year)
    lo = (pooled or {}).get("lo")
    return {"ok": bool(pos and lo is not None and lo > bar),
            "pos": pos, "lo": lo, "floor": True}


# ═══════════ ⑥ القياسُ لسنةٍ ═════════════════════════════════════════════════
def _measure(S, year: str, frozen: str):
    """يقيس سنةً واحدةً على لقطتها ويُرجع `(rc, rows, issues, attempted)`.
    🔒 **مصدرٌ واحد** — ولا `R` ولا فاصلَ هنا (فوضعُ الجدوى لا يمسّهما)."""
    hist, splits_map, asof = S.load_frozen_dataset(frozen)
    if not hist:
        _log("⛔ تعذّر تحميل اللقطة")
        return RC_INPUT, [], {}, 0
    if not S.CONFIG.get("PIVOT_STOP_AT_LOW"):
        _log("⛔ `H0` يشترط وقفَ القاع المشحون (`PIVOT_STOP_AT_LOW`) — مُطفأ")
        return RC_TOOL, [], {}, 0
    n_tr = max(1, int(S.CONFIG["ENTRY_TRANCHES"]))
    step_pct = float(S.CONFIG["ENTRY_STEP_PCT"])
    fwd = int(S.CONFIG["BACKTEST_FORWARD_DAYS"])
    spread = S.CONFIG.get("BT_SPREAD_PCT", 0.0) or 0.0
    if str(asof or "")[:4] != str(year):
        _log(f"⛔ اللقطة as-of {asof} لا تطابق سنةَ القياس {year} — يُوقَف")
        return RC_INPUT, [], {}, 0
    lo_d, hi_d = f"{year}-01-01", f"{year}-12-31"
    syms = sorted(hist)
    _log(f"📦 اللقطة as-of {asof} · رموز {len(syms)} · دفعات "
         f"{n_tr}×{step_pct}% · القصُّ الحاكم {dict(ARMS)[GOV]:.1f}% "
         f"(والحساسيّةُ {[h for _n, h in ARMS]})")
    rows, issues, missing = [], {}, []
    for k, sym in enumerate(syms):
        df = hist.get(sym)
        if df is None or len(df) < int(S.CONFIG["MIN_BARS"]) + LEN_PAD:
            continue
        try:
            trs = S.backtest_symbol(sym, df, date_window=(lo_d, hi_d),
                                    splits=(splits_map or {}).get(sym))
        except Exception as e:                                   # noqa: BLE001
            issues[type(e).__name__] = issues.get(type(e).__name__, 0) + 1
            continue
        for tr in trs:
            row, why = arms_for(S, sym, df, tr, fwd, spread, n_tr, step_pct)
            if row is None:
                issues[why] = issues.get(why, 0) + 1
                if len(missing) < 25:
                    missing.append(f"{sym}/{tr.get('date')}:{why}")
                continue
            rows.append(row)
        if (k + 1) % 500 == 0:
            _log(f"   … {k + 1}/{len(syms)} · صفوف {len(rows)}")
    if missing:
        _log("   🔍 عيّنةٌ من المفقود بتواريخه: " + " · ".join(missing))
    return RC_OK, rows, issues, len(rows) + sum(issues.values())


def year_table(rows, year: str) -> dict:
    st = {n: agg(rows, n) for n, _h in ARMS}
    base = st[BASE]
    _log(f"\n🎯✂️ T-HEADCUT · سنة {year} · صفوف {len(rows)}")
    _log("   الذراع │  h%  │ تعبئة% │ هدف% │ وقف% │ معلّق% │    R₀    │ عن H0")
    for n, h in ARMS:
        a = st[n]
        d = "" if n == BASE else f"{a['r'] - base['r']:+.4f}"
        _log(f"   {n:>6} │ {h:+5.1f} │ {a['fill_pct']:6.2f} │ "
             f"{a['win_pct']:5.2f} │ {a['loss_pct']:5.2f} │ "
             f"{a['open_pct']:6.2f} │ {a['r']:+9.4f} │ {d}")
    return st


def pair_year(per: dict, a: str, b: str, only=None) -> list:
    out = []
    for y in sorted(per):
        rows = per[y]["rows"]
        if only is not None:
            rows = [r for r in rows if bool(r.get("head")) is only]
        g = pair_clusters(rows, a, b)
        n = sum(v[0] for v in g.values())
        out.append([y, (sum(v[1] for v in g.values()) / n) if n else 0.0, n])
    return out


def pair_pool(per: dict, a: str, b: str, only=None):
    gs = []
    for y in sorted(per):
        rows = per[y]["rows"]
        if only is not None:
            rows = [r for r in rows if bool(r.get("head")) is only]
        gs.append(pair_clusters(rows, a, b))
    return boot_ci(pool_clusters(gs))                            # بالاسم


def _ci(ci) -> str:
    if not ci:
        return "—"
    return (f"{ci['mean']:+.4f}R [{ci['lo']:+.4f}, {ci['hi']:+.4f}] · "
            f"أزواج {ci['n']} · رموز {ci['k']}")


# ═══════════ ⑦ التقرير ═══════════════════════════════════════════════════════
def report(per: dict, tot: list, pub: dict) -> int:
    _log("\n" + "═" * 72)
    _log("🎯✂️ **`T-HEADCUT` — الحكم** (العقد `headcut_prereg.md`)")
    _log("═" * 72)

    # `V-H4` — عدُّ صفوف «`t1` رأسُ حمرا» **قبل** أيّ فرق
    n_head = sum(1 for r in tot if r.get("head"))
    share = (n_head / len(tot) * 100.0) if tot else 0.0
    degen = share <= 0.0 or share >= 100.0
    _log(f"\n🔎 `V-H4` صفوفٌ `t1` فيها رأسُ حمرا (تسامح {HEAD_TOL}%): "
         f"**{n_head}/{len(tot)} = {share:.1f}%**"
         + ("  🔴 **`C-HEAD` منحلٌّ ويُعلَن**" if degen else ""))

    y1 = pair_year(per, GOV, BASE)
    p1 = pair_pool(per, GOV, BASE)
    y3 = pair_year(per, GOV, CTRL)
    p3 = pair_pool(per, GOV, CTRL)
    ph = pair_pool(per, GOV, BASE, only=True)
    po = pair_pool(per, GOV, BASE, only=False)

    _log("\n### 🥇 `HC1` ‏`R(H1) − R(H0)` — القصُّ مقابل الإنتاج")
    for y, v, n in y1:
        _log(f"   {y}: **{v:+.4f}R** · أزواج {n}")
    _log(f"   **مجمَّعًا:** {_ci(p1)}")
    hc1 = crit(y1, p1)

    _log(f"\n### 🥇 `HC2` الماديّة ‏≥ +{MATERIAL}R — **شرطُ فتح المحور**")
    mean1 = (p1 or {}).get("mean")
    hc2 = {"ok": bool(mean1 is not None and mean1 >= MATERIAL), "floor": True}
    _log(f"   المجمَّع {('%+.4fR' % mean1) if mean1 is not None else '—'} "
         f"مقابل الحدّ **+{MATERIAL}R** ⇒ {'✅' if hc2['ok'] else '🔴'}")

    _log("\n### 🥇 `HC3` ‏`R(H1) − R(C-BACK)` — مقابل القصِّ المعاكس")
    for y, v, n in y3:
        _log(f"   {y}: **{v:+.4f}R** · أزواج {n}")
    _log(f"   **مجمَّعًا:** {_ci(p3)}")
    hc3 = crit(y3, p3)

    _log("\n### 🥇 `HC4` ‏`Δ_head − Δ_other` — هل الأثرُ يخصّ **الرأس**؟")
    for _lbl, _only in (("Δ_head ", True), ("Δ_other", False)):
        _log(f"   `{_lbl}` سنويًّا: "
             + " · ".join(f"{y} {v:+.4f} (n={n})"
                          for y, v, n in pair_year(per, GOV, BASE, only=_only)))
    _log(f"   `Δ_head`  (‏`t1` رأسُ حمرا): {_ci(ph)}")
    _log(f"   `Δ_other` (سواه):          {_ci(po)}")
    dh = (ph or {}).get("mean")
    do = (po or {}).get("mean")
    hc4 = {"ok": bool(dh is not None and do is not None and dh > do
                      and not degen),
           "floor": True}
    _log(f"   **الفرق:** "
         f"{('%+.4fR' % (dh - do)) if (dh is not None and do is not None) else '—'}"
         f" ⇒ {'✅' if hc4['ok'] else '🔴'}"
         + ("  (‏🔴 منحلٌّ — يسقط بنصّ `§④`)" if degen else ""))

    # الأرضيّة (`§⑥`-3) — **على الصفوف المحسومة في كلّ سنة**
    _log(f"\n### الأرضيّة (`§⑥`-3): ‏≥{FLOOR_ROWS} صفًّا محسومًا/سنة")
    floor_ok = True
    for y in sorted(per):
        settled = sum(1 for r in per[y]["rows"]
                      if r.get(f"o_{BASE}") in ("win", "loss"))
        ok = settled >= FLOOR_ROWS
        floor_ok = floor_ok and ok
        _log(f"   {y}: محسومة **{settled}** ⇒ {'✅' if ok else '🔴'}")
    for x in (hc1, hc2, hc3, hc4):
        x["floor"] = floor_ok

    _log("\n### 📏 وصفيٌّ — الحساسيّةُ كاملةً (لا يُنتقى منها الأمرح)")
    for n, h in ARMS:
        if n in (BASE,):
            continue
        yy = pair_year(per, n, BASE)
        pp = pair_pool(per, n, BASE)
        _log(f"   {n:>6} (h={h:+.1f}%): "
             + " · ".join(f"{y} {v:+.4f}" for y, v, _ in yy)
             + f" ⇒ {_ci(pp)}")

    _log("\n### 🔬 التنبّؤات — تُنشَر مكذَّبةً أو مؤكَّدة")
    _log(f"   `HP1` `HC1` يعبر ⟶ {'✅ مؤكَّد' if hc1['ok'] else '🔴 مكذَّب'}")
    _log(f"   `HP2` **`HC2` يسقط** ⟶ {'✅ مؤكَّد' if not hc2['ok'] else '🔴 مكذَّب'}")
    cb = [v for _y, v, _n in pair_year(per, CTRL, BASE)]
    _log(f"   `HP3` `C-BACK` أسوأُ من `H0` ⟶ "
         f"{'✅ مؤكَّد' if all(v < 0 for v in cb) else '🔴 مكذَّب'} "
         f"({' · '.join('%+.4f' % v for v in cb)})")
    _log(f"   `HP4` **`C-HEAD` ينحلّ أو `HC4` يسقط** ⟶ "
         f"{'✅ مؤكَّد' if (degen or not hc4['ok']) else '🔴 مكذَّب'}")
    _log(f"   `HP5` حصّةُ الرأس بين ‏40% و80% ⟶ "
         f"{'✅ مؤكَّد' if 40.0 <= share <= 80.0 else '🔴 مكذَّب'} ({share:.1f}%)")

    for ln in rows_out(tot, TSV_ON):
        _log(ln)

    rc, txt = read_verdict(hc1, hc2, hc3, hc4)
    _log("")
    _log("═══ الحكم ═══")
    _log(f"JUDGE rc={rc} · {txt}")
    return rc


def rows_out(tot: list, on: bool) -> list:
    """🔒 الحكمُ آخرَ ما يُطبَع (درسُ `T-TRAIL`: حكمٌ أُنتج ولم يكن مقروءًا)
    ⇒ الجدولُ **مطفأٌ افتراضًا** والقصُّ **يُعلَن بعدّاده**."""
    if not on:
        return [f"\n📄 جدولُ الصفوف **مطفأ** (‏{len(tot)} صفًّا) — "
                "`HEADCUT_TSV=1` ليُطبَع · والحكمُ يبقى آخرَ سطر."]
    cols = ["date", "sym", "e", "stop", "t1", "k", "head"] + \
           [f"{p}_{n}" for n, _h in ARMS for p in ("o", "R")]
    out = ["⟦TSV⟧" + "\t".join(cols)]
    for r in tot:
        cells = [r["date"], r["symbol"], f"{r['e']:.4f}", f"{r['stop']:.4f}",
                 f"{r['t1']:.4f}", f"{r['k']:.4f}", "1" if r["head"] else "0"]
        for n, _h in ARMS:
            v = r_row(r, n)
            cells += [str(r.get(f"o_{n}")), ("—" if v is None else f"{v:+.4f}")]
        out.append("⟦TSV⟧" + "\t".join(cells))
    return out


# ═══════════ ⑧ المسار ════════════════════════════════════════════════════════
def _pool(S, spec: str) -> int:
    gok, gwhy = guards_ok()
    if not gok:
        _log(f"⛔ `V-H5` حارسُ «قراءةٌ فقط / صفرُ إسناد» ساقط ({gwhy}) — خروج 3")
        return RC_TOOL
    _log(f"✅ `V-H5` {gwhy}")
    bad = selfcheck_v2()
    if bad:
        _log(f"⛔ `V-H2` تعريفُ القصّ لا يُحقّق شروطَه ({bad} تفرّقًا) — خروج 3")
        return RC_TOOL
    _log("✅ `V-H2` `cut_t1(t1,0) == t1` بالضبط · والقصُّ يخفض والمعاكسُ يرفع "
         "(‏4000 مدخلًا ببذرةٍ ثابتة)")
    pub = read_published()
    if not pub.get("ok"):
        _log(f"⛔ `V-H1` المنشورُ غيرُ مقروء: {pub.get('why')} — خروج 3")
        return RC_TOOL
    _log(f"📖 `V-H1` المنشورُ مُستخرَجٌ نصًّا من {TRAIL_RESULT}: "
         + " · ".join(f"{y} {pub[y]['r']:+.4f}/{pub[y]['rows']}/{pub[y]['fill']}"
                      for y in pub["years"]))
    parts = [p.strip() for p in spec.split(",") if p.strip() and ":" in p]
    if not parts:
        _log("⛔ مواصفةُ اللقطات فارغة — خروج 2")
        return RC_INPUT
    if not DRY and len(parts) < 3:
        _log("⛔ التجميعُ يشترط ثلاث سنوات — خروج 2")
        return RC_INPUT
    tot, per = [], {}
    for part in parts:
        year, path = (x.strip() for x in part.split(":", 1))
        if not os.path.exists(path):
            _log(f"⛔ لقطةُ {year} غيرُ موجودة: {path} — خروج 2")
            return RC_INPUT
        rc, rows, issues, attempted = _measure(S, year, path)
        if rc:
            return rc
        cov = (len(rows) / attempted * 100.0) if attempted else 0.0
        n_fill = sum(1 for r in rows
                     if r.get(f"o_{BASE}") not in (None, "no_fill"))
        n_head = sum(1 for r in rows if r.get("head"))
        _log(f"🩺 {year}: صفوف {len(rows)} من {attempted} = {cov:.1f}% · "
             f"مُعبَّأة {n_fill} · رأسُ حمرا {n_head}")
        if issues:
            _log("   ℹ️ أسبابُ عدم القياس: "
                 + " · ".join(f"{k}={v}" for k, v in sorted(issues.items())))
        per[year] = {"rows": rows, "n": len(rows), "fill": n_fill, "cov": cov}
        tot.extend(rows)
    if DRY:
        _log("\n🧪 **وضعُ الجدوى** — أربعةُ أعدادٍ لكلّ سنة (صفوف · مُعبَّأة · "
             "تغطية · رأسُ حمرا) · **صفرُ `R` وصفرُ فرقٍ وصفرُ فاصل**.")
        for y, v in per.items():
            nh = sum(1 for r in v["rows"] if r.get("head"))
            _log(f"   {y}: {v['n']} · {v['fill']} · {v['cov']:.1f}% · {nh}")
        _log("⚠️ ودرسُ `T-PMGATE`: **وضعُ الجدوى يُجيز ما يمرّ به وحدَه**.")
        return RC_OK
    # ── `V-H1` — هُويّةُ `H0` ضدّ المنشور · **قبل أيّ فرقٍ أو فاصل** ──────────
    for y in sorted(per):
        p = pub.get(y)
        if p is None:
            _log(f"⛔ `V-H1` سنةٌ بلا مرجعٍ منشور: {y} — خروج 5")
            return RC_POP
        got = round(agg(per[y]["rows"], BASE)["r"], 4)
        ok = (abs(got - p["r"]) <= 0.0001 and per[y]["n"] == p["rows"]
              and per[y]["fill"] == p["fill"])
        _log(f"   {'✅' if ok else '⛔'} `V-H1` {y}: R {got:+.4f} مقابل "
             f"{p['r']:+.4f} · صفوف {per[y]['n']}/{p['rows']} · تعبئة "
             f"{per[y]['fill']}/{p['fill']}")
        if not ok:
            _log("⛔ `V-H1` — المجتمعُ أو الأساسُ يخالف المنشور ⇒ لا يُفسَّر "
                 "رقم — خروج 5")
            return RC_POP
    for y in sorted(per):
        year_table(per[y]["rows"], y)
    return report(per, tot, pub)


def main() -> int:
    import Super_stock as S                                      # noqa: PLC0415
    spec = (os.environ.get("HEADCUT_SNAPSHOTS") or "").strip()
    if not spec:
        spec = ",".join(f"{y}:frozen_{y}.json" for y in (2023, 2024, 2025))
    _log("🎯✂️ `T-HEADCUT` — «بِع قبل رأس شمعة الهبوط» (قراءةٌ فقط · لا شحنَ)")
    _log(f"   اللقطات: {spec}" + ("  · 🧪 وضعُ الجدوى" if DRY else ""))
    return _pool(S, spec)


if __name__ == "__main__":
    sys.exit(main())
