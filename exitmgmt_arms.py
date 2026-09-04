#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🎚️🚪 `T-EXITMGMT` — «سجّل إدارة الخروج» (العقد `exitmgmt_prereg.md` مدفوعٌ
**قبل هذا الملفّ** ولم يُمَسّ).

**السؤال (§⓪):** أربعُ تجاربِ دخولٍ متتالية سقطت وكلُّها غيّرت ما **قبل**
الدخول (`T-TRANCHE` ‏−0.199R · `T-LIBVOL` ‏−0.879R · `T-LIBVOL-2` ‏−0.820R ·
`T-T1MOVE` ‏−0.130R). فماذا لو تُرك الدخولُ والوقفُ والهدفُ كما هي **وغُيِّر
ما بعدها وحدَه**؟

**المحرّك — إعادةُ استعمالٍ بالاسم لا نسخ:** صفقاتُ `backtest_symbol`
الإنتاجية · وخطّةُ كلّ صفقةٍ من `analyze_ticker` عند فهرسها نفسِه.
🔴 **والمُصيِّرُ الجديد ضرورةٌ لا اختيار:** `_resolve_arm` تأخذ وقفًا واحدًا
وهدفًا واحدًا فيستحيل أن تعبّر عن جنيٍ جزئيّ أو وقفٍ يتحرّك ⇒ `resolve_exit`،
**و`V0` تشترط أن يُعيدها بت-بت عند إطفاء الإدارة** فلا يصير على المجتمع
مقياسان (درسُ «مقياسٌ واحدٌ لا اثنان»).

🔒 `Super_stock.py` لا يُمَسّ بحرف · ولا علمَ جديد ولا عتبة.
🔒 بحث/قياس حصرًا: قراءةٌ فقط · الإنتاجُ لا يستوردها · لا `LOGIC_VERSION`.

🧊 **ومجتمعُ الإعادة مجمَّدٌ على `T-TRANCHE`** (سابقةُ `CAP15`): فلترُ الطول
`MIN_BARS + 60` حرفيًّا — وإلّا استحال أن تُعيد `V1` أرقامَها المنشورة."""
from __future__ import annotations

import ast
import json
import os
import sys

OUT_ROWS = "exitmgmt_rows.jsonl"
FLOOR_YEAR = 30              # §④-4 — أرضيةُ السنة (رقمُ العقد)
FLOOR_TOTAL = 150            # §④-4 — الأرضيةُ المجمَّعة
BAR_R = 0.15                 # §④-1 — البارُ المُعادُ حرفيًّا (لا يُحرَّك)
BOOT_N = 10000
BOOT_SEED = 99991
HALF = 0.5                   # §② — القسمةُ المحايدة (`engineering`) · ولا
#                              تُجرَّب نسبةٌ ثانية بعد الأرقام.
OPEN_FLOOR_PCT = 5.0         # §⑥ `EX-P6` — أرضيةُ «مادّةِ الهدف الزمنيّ»

# §② — خمسُ أذرعٍ ولا سادسة (مثبَّتةٌ في العقد · إضافةُ ذراعٍ بعد الأرقام
#      ممنوعة). (الاسم · حصّةُ الجني · مستوى الجني/التسليح · نقلُ الوقف)
ARMS = (("X0", 0.0,  None,   False),
        ("X1", HALF, "mid",  False),
        ("X2", HALF, "pct",  False),
        ("X3", 0.0,  "mid",  True),
        ("X4", HALF, "mid",  True))
GOV = "X1"                   # §② — الحاكمة

# §⑤ `V1` — أرقامُ `T-TRANCHE` المنشورة (‏`tranche_result.md §③` · وأعادتها
#            `T-T1MOVE` بت-بت) — لا تُحرَّك.
PUBLISHED = {"2023": -0.2602, "2024": -0.1807, "2025": -0.2172}


def _log(m):
    print(m, flush=True)


def ladder(anchor, n_tr, step_pct):
    """سلّمُ الدفعات الإنتاجيّ من المِرساة — بخانتين كالإنتاج، وبه يبقى `X0`
    مطابقًا لدفعات `analyze_ticker` بت-بت."""
    return [round(float(anchor) * (1.0 + step_pct * i / 100.0), 2)
            for i in range(int(n_tr))]


def r_of(ret_pct, entry, stop):
    """§② — العائدُ بوحدةِ المخاطرة `R₀ = entry − stop`. والدخولُ **واحدٌ لكلّ
    الأذرع** هنا (المتغيّرُ الخروجُ وحدَه) ⇒ الوحدةُ متطابقةٌ بالبناء."""
    try:
        e, s = float(entry), float(stop)
    except (TypeError, ValueError):
        return None
    if ret_pct is None or e - s <= 0:
        return None
    try:
        return (float(ret_pct) / 100.0 * e) / (e - s)
    except (TypeError, ValueError):
        return None


def resolve_exit(hi, lo, cl, op, entry, stop, t1, filled,
                 take=0.0, level=None, move_be=False, spread=0.0):
    """يحسم صفقةً بإدارةِ خروجٍ اختياريّة. يُرجع `(outcome, ret_pct, info)`.

    **العقدُ الحاكم (`V0`):** بلا إدارة (`take=0` و`level=None` و`move_be=False`)
    يجب أن يطابق **ذراعَ الذيل A في `_resolve_arm`** بت-بت — نفسُ الترتيب
    المحافظ (الوقفُ أوّلًا كلَّ شمعة) ونفسُ حارس `F-L1` (لا يُحسم الهدفُ على
    شمعة التعبئة) ونفسُ حسابِ العائد.

    وبالإدارة: `level` مستوى الجني/التسليح · `take` حصّةُ الخروج عنده ·
    و`move_be` ينقل الوقفَ إلى **التعادل** (سعرِ الدخول) **من الشمعة التالية**
    لبلوغه (لا يُحرَّك وقفٌ إلى الماضي داخل الشمعة نفسِها).
    🔒 و`level` لا يُستعمَل إلّا إن كان **دون `t1`** — وإلّا كان «جنيًا» فوق
    الهدف وهو تناقض، فتؤول الذراعُ إلى `X0` (‏`degenerate`)."""
    if filled is None or entry <= 0:
        return "no_fill", None, {}
    t1_from = filled + 1                     # `F-L1` كالأساس (تعبئةٌ داخل الشمعة)
    last_close = float(cl[-1])
    stop0 = float(stop)
    lvl = None if level is None else float(level)
    degen = lvl is not None and lvl >= float(t1)
    if degen:
        lvl = None                           # لا جنيَ فوق الهدف ⇒ تؤول إلى X0
    take_left = float(take) if (lvl is not None and take > 0.0) else 0.0
    arm_be = bool(move_be) and lvl is not None
    legs = []                                # [(وزن، سعرُ خروج)]
    w_left = 1.0
    be_from = None
    hit = False
    out, exit_last = "open", last_close
    for k in range(filled, len(cl)):
        st = float(entry) if (be_from is not None and k >= be_from) else stop0
        if lo[k] <= st:
            out, exit_last = "loss", min(st, float(op[k]))
            break
        if lvl is not None and k >= t1_from and hi[k] >= lvl:
            hit = True
            if take_left > 0.0:
                legs.append((take_left, lvl))
                w_left -= take_left
                take_left = 0.0
            if arm_be and be_from is None:
                # `+ 1` صريحٌ عمدًا: وقفُ التعادل يسري من الشمعة **التالية**.
                # 🔒 وهو حارسٌ **خامدٌ بالبناء** — `st` يُحسَب في رأس الدورة قبل
                # فحص المستوى، فـ`k` و`k + 1` لا يفترقان (مُبرهَنٌ على 90,000
                # حالة: صفرُ تفرّق). يبقى مكتوبًا للدلالة ويُقفَل **بنيويًّا**
                # (`EXM3ب`) لا بطفرة — قاعدةُ «الحارسُ الخامد لا يُطفَر».
                be_from = k + 1
        if k >= t1_from and hi[k] >= float(t1):
            out, exit_last = "win", float(t1)
            break
    legs.append((w_left, exit_last))
    buy = float(entry) * (1.0 + spread / 2.0)
    sell_f = 1.0 - spread / 2.0
    ret = sum(w * ((px * sell_f / buy - 1.0) * 100.0) for w, px in legs)
    return out, ret, {"hit": hit, "legs": len(legs), "degen": degen,
                      "be": be_from is not None}


def plan_at(S, sym, df, i):
    """خطّةُ الصفقة عند الفهرس `i` بنداء `analyze_ticker` **الإنتاجيّ**."""
    try:
        r = S.analyze_ticker(sym, df.iloc[:i])
    except Exception:                                            # noqa: BLE001
        return None
    if not r or not r.get("tranches"):
        return None
    try:
        # 🔴 `r["stop"]` **صفٌّ** `(stop_lo, stop_hi)` في الإنتاج
        #    (`Super_stock.py:4008`) — والوقفُ النافذ `[0]`. منقولةٌ حرفيًّا من
        #    `t1move_arms.plan_at` (الأداةُ التي أنتجت أرقامًا منشورة) فيبقى
        #    `X0` مطابقًا لأساسِ `T-TRANCHE` بت-بت.
        return {"tranches": [float(x) for x in r["tranches"]],
                "stop": float(r["stop"][0]), "t1": float(r["t1"]),
                "pivot": (None if r.get("pivot") is None
                          else float(r["pivot"]))}
    except (TypeError, ValueError, KeyError, IndexError):
        return None


def anchor_at(S, df_slice, pl):
    """مِرساةُ الدفعات كما يبنيها الإنتاجُ حرفيًّا — **صفرُ إعادةِ بناءٍ بالقسمة**
    (درسُ `TV1` في `T-TRANCHE`). منقولةٌ من `t1move_arms.anchor_at` بلا تغيير
    فيبقى `X0` مطابقًا لأساسِ المنشور بت-بت."""
    try:
        amode = S._anchor_mode(S.CONFIG.get("BT_ANCHOR"),
                               S.CONFIG.get("ANCHOR_MODE"))
    except Exception:                                            # noqa: BLE001
        return None
    if amode:
        try:
            tl = S.tested_level(df_slice)
        except Exception:                                        # noqa: BLE001
            return None
        if tl:
            try:
                return float(tl["level"])
            except (TypeError, ValueError, KeyError):
                return None
        if amode == "tested_strict":
            return None
    return pl.get("pivot")


def arms_for(S, sym, df, tr, fwd, spread, n_tr, step_pct, pct10):
    """يحسم الأذرعَ الخمس على **نفس الشموع ونفس الدخول ونفس الوقف ونفس الهدف**
    — المتغيّرُ الوحيد **ما يقع بعد التعبئة**."""
    try:
        import pandas as pd                                      # noqa: PLC0415
        pos = df.index.get_loc(pd.Timestamp(tr["date"]))
    except Exception:                                            # noqa: BLE001
        return None, "تاريخٌ غيرُ موجود"
    i = int(pos) + 1
    pl = plan_at(S, sym, df, i)
    if pl is None:
        return None, "تعذّرت إعادةُ الخطّة"
    anchor = anchor_at(S, df.iloc[:i], pl)
    if anchor is None:
        return None, "بلا مِرساة"
    stop = pl["stop"]
    t1 = pl["t1"]
    fut = df.iloc[i:i + fwd]
    if not len(fut):
        return None, "نافذةٌ فارغة"
    hi = fut["High"].values.astype(float)
    lo = fut["Low"].values.astype(float)
    cl = fut["Close"].values.astype(float)
    op = fut["Open"].values.astype(float)

    trs = ladder(anchor, n_tr, step_pct)
    entry = sum(trs) / len(trs)
    if entry - stop <= 0:
        return None, "مقامُ المخاطرة غيرُ موجب"
    if t1 <= entry:
        return None, "هدفٌ دون الدخول"

    mid = entry + (t1 - entry) / 2.0          # §② — بنيويّ: صفرُ رقمٍ مخترَع
    lv_pct = entry * (1.0 + float(pct10) / 100.0)
    # 🔒 التعبئةُ واحدةٌ لكلّ الأذرع **بالبناء** (الدخولُ لم يتغيّر) — و`V3`
    #    يُثبتها بدل أن يفترضها.
    filled = next((k for k in range(len(fut)) if lo[k] <= entry), None)
    row = {"symbol": sym, "date": tr["date"], "stop": round(stop, 4),
           "t1": round(t1, 4), "anchor": round(anchor, 6),
           "e": round(entry, 4), "prod_tr": [round(x, 4) for x in pl["tranches"]],
           "tr0": trs, "mid": round(mid, 4), "lv_pct": round(lv_pct, 4),
           "k": round((t1 - entry) / (entry - stop), 6)}
    for name, take, kind, be in ARMS:
        lvl = None if kind is None else (mid if kind == "mid" else lv_pct)
        o, rt, info = resolve_exit(hi, lo, cl, op, entry, stop, t1, filled,
                                   take=take, level=lvl, move_be=be,
                                   spread=spread)
        row[f"o_{name}"] = o
        row[f"ret_{name}"] = (round(rt, 6) if rt is not None else None)
        row[f"hit_{name}"] = bool(info.get("hit"))
        if info.get("degen"):
            row[f"degen_{name}"] = True
    return row, None


def _selfcheck_readonly() -> bool:
    """`V6` — قراءةٌ فقط: صفرُ إرسالٍ وصفرُ كتابةِ حالة (بالـAST على مصدرها هي).
    الملفُّ الوحيد المسموحُ فتحُه للكتابة هو `OUT_ROWS`."""
    try:
        src = open(__file__, encoding="utf-8").read()
    except Exception:                                            # noqa: BLE001
        return False
    banned = {"send_telegram", "git_save", "save_watchlist",
              "save_op_entry_state", "record_new_alerts", "save_near_watch",
              "save_hunter_watch"}
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Call):
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
                if any(c in mode for c in ("w", "a", "x", "+")):
                    ok = (n.args and isinstance(n.args[0], ast.Name)
                          and n.args[0].id == "OUT_ROWS")
                    if not ok:
                        return False
    return True


def selfcheck_v0(S, n=4000, seed=20260904):
    """`V0` — **بوّابةُ المِقياس الواحد**: `resolve_exit` بلا إدارةٍ تُعيد ذراعَ
    الذيل A في `_resolve_arm` **بت-بت** (`outcome` والعائد) على مدخلاتٍ
    عشوائيّةٍ ببذرةٍ ثابتة. تفرّقٌ واحد ⇒ عطبُ أداةٍ لا نتيجة."""
    import random                                                # noqa: PLC0415
    rng = random.Random(seed)
    bad = 0
    for _ in range(n):
        m = rng.randint(2, 40)
        base = rng.uniform(0.4, 10.0)
        op = [round(base * rng.uniform(0.7, 1.3), 4) for _ in range(m)]
        cl = [round(o * rng.uniform(0.85, 1.15), 4) for o in op]
        hi = [round(max(a, b) * rng.uniform(1.0, 1.12), 4)
              for a, b in zip(op, cl)]
        lo = [round(min(a, b) * rng.uniform(0.88, 1.0), 4)
              for a, b in zip(op, cl)]
        entry = round(base * rng.uniform(0.9, 1.1), 4)
        stop = round(entry * rng.uniform(0.90, 0.995), 4)
        t1 = round(entry * rng.uniform(1.02, 1.60), 4)
        filled = rng.choice([None] + list(range(m)))
        spread = rng.choice([0.0, 0.0, 0.05])
        ow, rw, _oc, _rc = S._resolve_arm(hi, lo, cl, op, entry, stop, t1,
                                          filled, spread=spread)
        o2, r2, _ = resolve_exit(hi, lo, cl, op, entry, stop, t1, filled,
                                 spread=spread)
        if ow != o2 or (rw is None) != (r2 is None):
            bad += 1
            continue
        if rw is not None and rw != r2:
            bad += 1
    return bad


def clusters(rows, name):
    """عناقيدُ البوتستراب: لكلّ رمزٍ `(عدد، مجموعُ فرقِ R₀)` — كافيةٌ تمامًا
    لبوتستراب متوسّطِ الفرق بعنقود الرمز (§④-3)."""
    g = {}
    for r in rows:
        d = pair_diff(r, name)
        if d is None:
            continue
        n, s = g.get(r["symbol"], (0, 0.0))
        g[r["symbol"]] = (n + 1, s + d)
    return g


def pair_diff(r, name):
    """فرقُ `R₀` المقترن (نفسُ الصفقة) — و`no_fill` = **صفرُ عائد** يدخل المقام
    (§③ · مُعادٌ من `T-TRANCHE §⑨-4`)."""
    ob, ok = r.get("o_X0"), r.get(f"o_{name}")
    if ob is None or ok is None:
        return None
    vb = 0.0 if ob == "no_fill" else r_of(r.get("ret_X0"), r["e"], r["stop"])
    vk = 0.0 if ok == "no_fill" else r_of(r.get(f"ret_{name}"), r["e"],
                                          r["stop"])
    if vb is None or vk is None:
        return None
    return vk - vb


def pool_clusters(gs):
    """يجمع عناقيدَ السنوات **بالرمز** — رمزٌ يظهر في سنتين يبقى **عنقودًا
    واحدًا** لا اثنين، وإلّا انكسر استقلالُ العنقود وضاق الفاصلُ كذبًا."""
    out = {}
    for g in gs:
        for sym, v in g.items():
            cur = out.get(sym, (0, 0.0))
            out[sym] = (cur[0] + v[0], cur[1] + v[1])
    return out


def boot_ci(g, n=BOOT_N, seed=BOOT_SEED, level=0.95):
    """فاصلُ 95% لمتوسّطِ الفرق — بوتستراب **عنقودُه الرمز** (§④-3)، حتميٌّ
    ببذرةٍ ثابتة."""
    import random                                                # noqa: PLC0415
    ks = sorted(g)
    if not ks:
        return None
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        tn, ts = 0, 0.0
        for _ in ks:
            a, b = g[ks[rng.randrange(len(ks))]]
            tn += a
            ts += b
        out.append(ts / tn if tn else 0.0)
    out.sort()
    a = (1.0 - level) / 2.0

    def _p(q):
        return out[min(max(int(round(q * (len(out) - 1))), 0), len(out) - 1)]
    tn = sum(v[0] for v in g.values())
    ts = sum(v[1] for v in g.values())
    return {"lo": _p(a), "hi": _p(1.0 - a), "mean": (ts / tn if tn else 0.0),
            "n": tn, "k": len(ks)}


def agg(rows, name):
    """`no_fill` = صفرُ عائدٍ **ويدخل المقام** — فالمقامُ واحدٌ للأذرع الخمس."""
    fx, n_fill, wins, hits, opens, degen = [], 0, 0, 0, 0, 0
    for r in rows:
        o = r.get(f"o_{name}")
        if o is None:
            continue
        if r.get(f"degen_{name}"):
            degen += 1
        if o == "no_fill":
            fx.append(0.0)
            continue
        n_fill += 1
        if o == "win":
            wins += 1
        if o == "open":
            opens += 1
        if r.get(f"hit_{name}"):
            hits += 1
        v = r_of(r.get(f"ret_{name}"), r["e"], r["stop"])
        fx.append(v if v is not None else 0.0)
    n = len(fx)
    return {"n": n, "n_fill": n_fill,
            "fill_pct": (n_fill / n * 100.0) if n else 0.0,
            "win_pct": (wins / n_fill * 100.0) if n_fill else 0.0,
            "hit_pct": (hits / n_fill * 100.0) if n_fill else 0.0,
            "open_pct": (opens / n_fill * 100.0) if n_fill else 0.0,
            "degen": degen,
            "r": (sum(fx) / n) if n else 0.0}


def report(rows, year, issues, v0_bad):
    """يطبع البوّابات والجدول. خروج: 0 سليم · 3 عطبُ أداة · 4 `no-op`/أرضية.
    🔒 **ورمزُ الخروج لا يحمل الحكم** (درسُ `ignition.yml` و`T-T1MOVE`)."""
    attempted = len(rows) + sum(issues.values())
    _log(f"\n🎚️ T-EXITMGMT · سنة {year} · صفقات {len(rows)} من {attempted}")
    if issues:
        _log("   ℹ️ أسبابُ عدم القياس: "
             + " · ".join(f"{k}={v}" for k, v in sorted(issues.items())))
    if v0_bad:
        _log(f"⛔ `V0` المُصيِّرُ لا يُعيد `_resolve_arm` بت-بت ({v0_bad} تفرّقًا)"
             " — عطبُ أداةٍ لا نتيجة")
        return 3
    _log("   ✅ `V0` المُصيِّرُ يُعيد `_resolve_arm` بت-بت (صفرُ تفرّق)")
    if not rows:
        _log("⛔ صفرُ صفوف — لا يُفسَّر")
        return 4

    st = {n: agg(rows, n) for n, _t, _k, _b in ARMS}
    base = st["X0"]
    # `V1` — إعادةُ أساس `T-TRANCHE` بت-بت
    pub = PUBLISHED.get(str(year))
    if pub is not None:
        got = round(base["r"], 4)
        ok = abs(got - pub) <= 0.0001
        _log(f"   {'✅' if ok else '⛔'} `V1` أساسُ `T-TRANCHE`: {got:+.4f} "
             f"مقابل {pub:+.4f}")
        if not ok:
            return 3
    # `V3` — التعبئةُ متطابقةٌ في الخمس (إدارةُ الخروج لا تمسّها بالبناء)
    fills = {n: st[n]["n_fill"] for n, _t, _k, _b in ARMS}
    if len(set(fills.values())) != 1:
        _log(f"⛔ `V3` التعبئةُ تختلف بين الأذرع {fills} — عطبُ أداة")
        return 3
    _log(f"   ✅ `V3` التعبئةُ متطابقة ({base['n_fill']} في الخمس)")
    # `V2` — تفرّقُ الأذرع (بصمةُ `no-op`)
    sig = {n: round(st[n]["r"], 9) for n, _t, _k, _b in ARMS}
    if sig["X1"] == sig["X0"] or sig["X3"] == sig["X0"] or sig["X2"] == sig["X1"]:
        _log(f"⛔ `V2` ذراعٌ خامدة — بصمةُ no-op: {sig}")
        return 4

    _log("   ┌─ الأذرع (الحاكم: متوسّطُ R₀ · و`no_fill`=0R يدخل المقام) ─")
    _log("   الذراع │ تعبئة% │ هدف% │ بلغ المستوى% │ معلّق% │   R₀    │ فرقٌ عن X0")
    for n, _t, _k, _b in ARMS:
        a = st[n]
        d = "" if n == "X0" else f"{a['r'] - base['r']:+.4f}"
        dg = f" · مؤوَّلةٌ إلى X0: {a['degen']}" if a["degen"] else ""
        _log(f"   {n:>6} │ {a['fill_pct']:6.2f} │ {a['win_pct']:5.2f} │"
             f" {a['hit_pct']:12.2f} │ {a['open_pct']:6.2f} │ {a['r']:+8.4f} │"
             f" {d}{dg}")
    _log(f"   📏 `k` وسيطًا ‏≈ {sorted(r['k'] for r in rows)[len(rows) // 2]:.2f}")
    # §⑥ `EX-P6` — هل للهدف الزمنيّ مادّة؟
    op = base["open_pct"]
    _log(f"   🕒 `EX-P6` حصّةُ `open` = {op:.2f}% "
         + ("⇒ **فيه مادّة** ⇒ يلزمه تسجيلٌ مستقلّ"
            if op >= OPEN_FLOOR_PCT else "⇒ خامدٌ بنيويًّا (الأرضية "
            f"{OPEN_FLOOR_PCT:.0f}%) — ولا تُضاف ذراعٌ هنا"))
    for n, _t, _k, _b in ARMS:
        if n == "X0":
            continue
        g = clusters(rows, n)
        ci = boot_ci(g)
        if ci:
            _log(f"   📐 {n} − X0 = {ci['mean']:+.4f}R "
                 f"[{ci['lo']:+.4f} · {ci['hi']:+.4f}] · أزواج {ci['n']} · "
                 f"رموز {ci['k']}")
    _log("   └─ (الحكمُ الرباعيّ مجمَّعًا في وضع التجميع لا هنا)")
    return 0


def _measure(S, year, frozen):
    """يقيس سنةً واحدةً على لقطتها ويُرجع `(rc, rows, issues)`.
    🔒 **مصدرٌ واحد**: مسارُ السنة المفردة ومسارُ التجميع ينادِيانه معًا."""
    hist, splits_map, asof = S.load_frozen_dataset(frozen)
    if not hist:
        _log("⛔ تعذّر تحميل اللقطة")
        return 2, [], {}
    S.CONFIG["BT_REPLAY10"] = 1
    S.CONFIG["BT_ENVVALS"] = 1
    # §① — الوقفُ والدخولُ المشحونان لا يُمَسّان (عزلُ أثر الخروج شرطُ صلاحية)
    if not S.CONFIG.get("PIVOT_STOP_AT_LOW"):
        _log("⛔ `X0` يشترط وقفَ القاع المشحون (`PIVOT_STOP_AT_LOW`) — مُطفأ")
        return 3, [], {}
    n_tr = max(1, int(S.CONFIG["ENTRY_TRANCHES"]))
    step_pct = float(S.CONFIG["ENTRY_STEP_PCT"])
    fwd = int(S.CONFIG["BACKTEST_FORWARD_DAYS"])
    spread = S.CONFIG.get("BT_SPREAD_PCT", 0.0) or 0.0
    # §② — رقمُ `X2` **مُعادٌ من الإنتاج لا مخترَع** (`LIQ_TARGET10_PCT`)
    pct10 = float(S.LIQ_TARGET10_PCT)   # ثابتُ وحدةٍ لا مفتاحُ CONFIG
    lo_d, hi_d = f"{year}-01-01", f"{year}-12-31"
    if str(asof or "")[:4] != str(year):
        _log(f"⛔ اللقطة as-of {asof} لا تطابق سنةَ القياس {year} — "
             "مجتمعٌ مختلف، لا تُقاس")
        return 4, [], {}
    syms = sorted(hist)
    _log(f"📦 اللقطة as-of {asof} · رموز {len(syms)} · دفعات {n_tr}×{step_pct}%"
         f" · جنيٌ {HALF:.0%} · مستوى X2 = +{pct10:.1f}% "
         "(`LIQ_TARGET10_PCT`)")
    rows, issues, missing = [], {}, []
    with open(OUT_ROWS, "w", encoding="utf-8") as fh:
        for k, sym in enumerate(syms):
            df = hist.get(sym)
            # 🧊 مجمَّدٌ على `T-TRANCHE` (‏`MIN_BARS + 60`)
            if df is None or len(df) < int(S.CONFIG["MIN_BARS"]) + 60:
                continue
            try:
                trs = S.backtest_symbol(sym, df, date_window=(lo_d, hi_d),
                                        splits=(splits_map or {}).get(sym))
            except Exception as e:                               # noqa: BLE001
                issues[type(e).__name__] = issues.get(type(e).__name__, 0) + 1
                continue
            for tr in trs:
                row, why = arms_for(S, sym, df, tr, fwd, spread, n_tr,
                                    step_pct, pct10)
                if row is None:
                    issues[why] = issues.get(why, 0) + 1
                    if len(missing) < 25:
                        missing.append(f"{sym}/{tr.get('date')}:{why}")
                    continue
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                rows.append(row)
            if (k + 1) % 500 == 0:
                _log(f"   … {k + 1}/{len(syms)} · صفوف {len(rows)}")
    if missing:
        _log("   🔍 `V4` عيّنةٌ من المفقود بتواريخه: " + " · ".join(missing))
    return 0, rows, issues


def _pool(S, spec):
    """§④ **مجمَّعًا**: السنوات في تشغيلةٍ واحدة (ميزانيةٌ واحدةٌ بالبناء) ثم
    تُجمع عناقيدُ البوتستراب **بالرمز عبر السنوات**."""
    v0_bad = selfcheck_v0(S)
    if v0_bad:
        _log(f"⛔ `V0` {v0_bad} تفرّقًا عن `_resolve_arm` — عطبُ أداة")
        return 3
    _log("✅ `V0` المُصيِّرُ يُعيد `_resolve_arm` بت-بت (صفرُ تفرّق)")
    per_year, gs, tot = [], [], []
    for part in spec.split(","):
        part = part.strip()
        if not part or ":" not in part:
            continue
        year, path = part.split(":", 1)
        year, path = year.strip(), path.strip()
        if not os.path.exists(path):
            _log(f"⛔ لقطةُ {year} غيرُ موجودة: {path}")
            return 2
        rc, rows, issues = _measure(S, year, path)
        if rc:
            return rc
        rc2 = report(rows, year, issues, 0)
        if rc2:
            return rc2
        d = clusters(rows, GOV)
        per_year.append([year, (sum(v[1] for v in d.values())
                                / max(1, sum(v[0] for v in d.values()))),
                         sum(v[0] for v in d.values())])
        gs.append(d)
        tot.extend(rows)
    if len(per_year) < 3:
        _log("⛔ التجميعُ يشترط ثلاث سنوات")
        return 2
    pooled = pool_clusters(gs)
    ci = boot_ci(pooled)
    tot_rows = sum(n for _y, _d, n in per_year)
    c1 = ci["mean"] >= BAR_R
    c2 = all(d > 0 for _y, d, _n in per_year)
    c3 = (ci["lo"] > 0) or (ci["hi"] < 0)
    c4 = tot_rows >= FLOOR_TOTAL and all(n >= FLOOR_YEAR
                                         for _y, _d, n in per_year)
    n_ok = sum((c1, c2, c3, c4))
    _log("\n" + "═" * 62)
    _log(f"🎚️ الحكمُ المجمَّع — الحاكمة `{GOV} − X0` (§③)")
    for y, d, n in per_year:
        _log(f"   {y}: {d:+.6f}R · أزواج {n}")
    _log(f"   مجمَّعًا {ci['mean']:+.4f}R [{ci['lo']:+.4f} · {ci['hi']:+.4f}]"
         f" · أزواج {ci['n']} · رموز {ci['k']}")
    _log(f"   ① البار ({BAR_R:+.2f}R): {'✅' if c1 else '🔴'}")
    _log(f"   ② ثباتُ الإشارة في الثلاث: {'✅' if c2 else '🔴'}")
    _log(f"   ③ الفاصلُ لا يلمس الصفر: {'✅' if c3 else '🔴'}")
    _log(f"   ④ الأرضية ({FLOOR_TOTAL} مجمَّعًا و{FLOOR_YEAR} للسنة):"
         f" {'✅' if c4 else '🔴'}")
    _log(f"   ⇒ **{n_ok} من 4** ⇒ "
         + ("تُوصى (اقتراحُ سطرِ عرضٍ للمالك — بلا شحن)" if n_ok == 4
            else "لا تُوصى"))
    # §⑥ `EX-P4` — التفكيك: هل يجمع الأثران بلا تفاعل؟
    d1 = boot_ci(pool_clusters([clusters(tot, "X1")]))
    d3 = boot_ci(pool_clusters([clusters(tot, "X3")]))
    d4 = boot_ci(pool_clusters([clusters(tot, "X4")]))
    if d1 and d3 and d4:
        inter = d4["mean"] - (d1["mean"] + d3["mean"])
        _log(f"\n🧩 التفكيك: X1 {d1['mean']:+.4f} · X3 {d3['mean']:+.4f} · "
             f"X4 {d4['mean']:+.4f} ⇒ التفاعل {inter:+.4f}R "
             f"(`EX-P4` يتوقّع |تفاعل| لا يتجاوز 0.03)")
    _log("═" * 62)
    _log("JUDGE " + json.dumps(
        {"gov": GOV, "mean": round(ci["mean"], 6),
         "lo": round(ci["lo"], 6), "hi": round(ci["hi"], 6),
         "pairs": ci["n"], "symbols": ci["k"],
         "per_year": [[y, round(d, 6), n] for y, d, n in per_year],
         "criteria": [c1, c2, c3, c4], "passed": n_ok},
        ensure_ascii=False))
    return 0


def main() -> int:
    if not _selfcheck_readonly():
        _log("⛔ `V6` الأداةُ ليست قراءةً فقط")
        return 3
    os.environ["SCREENER_MODE"] = "BACKTEST"
    import Super_stock as S                                      # noqa: PLC0415
    spec = (os.environ.get("EXITMGMT_POOL") or "").strip()
    if spec:
        return _pool(S, spec)
    year = (os.environ.get("BACKTEST_YEAR") or "").strip()
    if not year.isdigit():
        _log("⛔ BACKTEST_YEAR مطلوب")
        return 2
    frozen = (os.environ.get("BT_FROZEN_PATH") or "").strip()
    if not frozen or not os.path.exists(frozen):
        _log("⛔ BT_FROZEN_PATH مطلوب (لقطةٌ مجمَّدة)")
        return 2
    v0_bad = selfcheck_v0(S)
    rc, rows, issues = _measure(S, year, frozen)
    if rc:
        return rc
    return report(rows, year, issues, v0_bad)


if __name__ == "__main__":
    sys.exit(main())
