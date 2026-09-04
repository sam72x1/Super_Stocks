#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🎯🪜 `T-T1MOVE` — «سجّل t1 متحرّك» (العقد `t1move_prereg.md` مدفوعٌ **قبل
هذا الملفّ** ولم يُمَسّ).

**السؤال (§⓪):** ثلاثُ تجاربِ دخولٍ متتالية سقطت (`T-TRANCHE` ‏−0.199R ·
`T-LIBVOL` ‏−0.879R · `T-LIBVOL-2` ‏−0.820R) وكلُّها رفعت **سعرَ الدخول**
و**الهدفُ ثابت** ⇒ هندسةٌ عقابيّةٌ بالبناء. فهل يعود التوقّعُ إن **تحرّك الهدفُ
مع الدخول** فحُفظت نسبةُ العائد إلى المخاطرة؟

**المحرّك — إعادةُ استعمالٍ بالاسم لا نسخ:** صفقاتُ `backtest_symbol` الإنتاجية،
ثم تُعاد خطّةُ كلّ صفقةٍ بـ`analyze_ticker` **عند فهرسها نفسِه**، والحسمُ
بـ`_resolve_arm` **الإنتاجيّة** — وهي تأخذ `t1` **وسيطًا** فتحريكُه صفرُ منطقٍ
جديد.

🔒 **`Super_stock.py` لا يُمَسّ بحرف** — ولا علمَ جديد ولا عتبة.
🔒 بحث/قياس حصرًا: قراءةٌ فقط · الإنتاجُ لا يستوردها · لا `LOGIC_VERSION`.

🧊 **ومجتمعُ الإعادة مجمَّدٌ على `T-TRANCHE` عمدًا** (سابقةُ `CAP15`): فلترُ
الطول `MIN_BARS + 60` **حرفيًّا كما مشت** — وإلّا استحال أن تُعيد `V0`/`V1`
أرقامَها المنشورة، فتُقارَن سنةٌ بمجتمعٍ آخر."""
from __future__ import annotations

import ast
import json
import os
import sys

OUT_ROWS = "t1move_rows.jsonl"
FLOOR_YEAR = 30              # §④-4 — أرضيةُ السنة (رقمُ العقد)
FLOOR_TOTAL = 150            # §④-4 — الأرضيةُ المجمَّعة
BAR_R = 0.15                 # §④-1 — البارُ المُعادُ حرفيًّا (لا يُحرَّك)
BOOT_N = 10000
BOOT_SEED = 99991

# §② — خمسُ أذرعٍ ولا سادسة (مثبَّتةٌ في العقد · إضافةُ ذراعٍ بعد الأرقام ممنوعة)
#      (الاسم · إزاحةُ بداية السلّم٪ · وضعُ الهدف)
ARMS = (("A0", 0.0, "fixed"),
        ("M1", 2.0, "fixed"),
        ("M2", 2.0, "r"),
        ("M3", 7.0, "r"),
        ("M4", 2.0, "ratio"))
GOV = "M2"                   # §② — الحاكمة

# §⑤ — أرقامُ `T-TRANCHE` المنشورة (‏`tranche_result.md §③`) — لا تُحرَّك.
PUBLISHED = {
    "2023": {"A0": -0.2602, "M1": -0.4620},
    "2024": {"A0": -0.1807, "M1": -0.4056},
    "2025": {"A0": -0.2172, "M1": -0.3889},
}


def _log(m):
    print(m, flush=True)


def ladder(anchor, off_pct, n_tr, step_pct):
    """سلّمُ الدفعات **بصيغة الإنتاج حرفيًّا** مع إزاحةِ بداية — التدويرُ
    بخانتين كالإنتاج، وبه يبقى `A0` مطابقًا لدفعات `analyze_ticker` بت-بت."""
    off = float(off_pct) / 100.0
    step = float(step_pct) / 100.0
    return [round(float(anchor) * (1.0 + off + step * i), 2)
            for i in range(int(n_tr))]


def t1_for(mode, t1_base, entry, entry_base, stop):
    """§② — هدفُ الذراع:
    `fixed` هدفُ الإنتاج كما هو ·
    `r`     `t1' = entry' + k(entry' − stop)` حيث
            `k = (t1_A0 − entry_A0) ÷ (entry_A0 − stop)` ⇒ **نسبةُ العائد إلى
            المخاطرة محفوظةٌ بالضبط** (وهي الحاكمة) ·
    `ratio` `t1' = t1_A0 × (entry' ÷ entry_A0)`.
    يرجّع None إن تعذّر (مقامٌ غيرُ موجب) — والصفُّ يُسقَط بسببٍ مُسمًّى."""
    try:
        t1b, e, eb, s = (float(t1_base), float(entry), float(entry_base),
                         float(stop))
    except (TypeError, ValueError):
        return None
    if mode == "fixed":
        return t1b
    if eb - s <= 0 or eb <= 0:
        return None
    if mode == "ratio":
        return t1b * (e / eb)
    if mode == "r":
        k = (t1b - eb) / (eb - s)
        if k <= 0:
            return None
        return e + k * (e - s)
    return None


def r_fixed(ret_pct, entry_k, entry_base, stop):
    """§② — العائدُ بوحدةِ مخاطرةٍ **واحدةٍ لكلّ الأذرع** `R₀ = entry(A0) − stop`.
    فالذراعُ الأوسعُ دخولًا لا تُكافأ بصِغَر مقامها (درسُ `T-RECLAIM-INTRADAY`)."""
    try:
        e_k, e_b, s = float(entry_k), float(entry_base), float(stop)
    except (TypeError, ValueError):
        return None
    if ret_pct is None or e_b - s <= 0:
        return None
    try:
        return (float(ret_pct) / 100.0 * e_k) / (e_b - s)
    except (TypeError, ValueError):
        return None


def plan_at(S, sym, df, i):
    """خطّةُ الصفقة عند الفهرس `i` بنداء `analyze_ticker` **الإنتاجيّ**."""
    try:
        r = S.analyze_ticker(sym, df.iloc[:i])
    except Exception:                                            # noqa: BLE001
        return None
    if not r or not r.get("tranches"):
        return None
    try:
        return {"tranches": [float(x) for x in r["tranches"]],
                "stop": float(r["stop"][0]),
                "t1": float(r["t1"]),
                "pivot": (float(r["pivot"]) if r.get("pivot") is not None
                          else None)}
    except (TypeError, ValueError, KeyError, IndexError):
        return None


def anchor_at(S, df_slice, pl):
    """مِرساةُ الدفعات كما يبنيها الإنتاجُ حرفيًّا — **صفرُ إعادةِ بناءٍ بالقسمة**
    (درسُ `TV1` في `T-TRANCHE`: الاسترجاعُ يُزيح بوحدةِ `ULP` فيعبر حدَّ
    التدوير)."""
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


def arms_for(S, sym, df, tr, fwd, spread, n_tr, step_pct):
    """يحسم الأذرعَ الخمس على **نفس الشموع ونفس الوقف** — المتغيّرُ بدايةُ
    السلّم **وموضعُ الهدف**. يرجّع (صفّ، None) أو (None، سبب)."""
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
    t1_base = pl["t1"]
    fut = df.iloc[i:i + fwd]
    if not len(fut):
        return None, "نافذةٌ فارغة"
    hi = fut["High"].values.astype(float)
    lo = fut["Low"].values.astype(float)
    cl = fut["Close"].values.astype(float)
    op = fut["Open"].values.astype(float)

    base_trs = ladder(anchor, 0.0, n_tr, step_pct)
    entry_base = sum(base_trs) / len(base_trs)
    if entry_base - stop <= 0:
        return None, "مقامُ المخاطرة غيرُ موجب"
    if t1_base <= entry_base:
        return None, "هدفٌ دون الدخول"

    row = {"symbol": sym, "date": tr["date"], "stop": round(stop, 4),
           "t1": round(t1_base, 4), "anchor": round(anchor, 6),
           "prod_tr": [round(x, 4) for x in pl["tranches"]],
           "tr0": base_trs,
           "k": round((t1_base - entry_base) / (entry_base - stop), 6)}
    for name, off, mode in ARMS:
        trs = ladder(anchor, off, n_tr, step_pct)
        entry = sum(trs) / len(trs)
        if entry - stop <= 0:
            row[f"skip_{name}"] = True
            continue
        t1k = t1_for(mode, t1_base, entry, entry_base, stop)
        if t1k is None or t1k <= entry:
            row[f"skip_{name}"] = True
            continue
        filled = next((k for k in range(len(fut)) if lo[k] <= entry), None)
        o, rt, _, _ = S._resolve_arm(hi, lo, cl, op, entry, stop, t1k, filled,
                                     spread=spread)
        row[f"e_{name}"] = round(entry, 4)
        row[f"t1_{name}"] = round(t1k, 4)
        row[f"lo_{name}"] = trs[0]
        row[f"o_{name}"] = o
        row[f"ret_{name}"] = (round(rt, 1) if rt is not None else None)
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


def clusters(rows, name):
    """عناقيدُ البوتستراب: لكلّ رمزٍ `(عدد، مجموعُ فرقِ R₀)` — وهي **كافيةٌ
    تمامًا** لبوتستراب متوسّطِ الفرق بعنقود الرمز (§④-3)، وأصغرُ من سردِ
    الأزواج بمراتب فتُقرأ من السجلّ بلا قصّ."""
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
    (§⑨-4 في `T-TRANCHE`: المقامُ واحدٌ للأذرع وزيادةُ التعبئة تُحسَب لا تُخفى)."""
    ob, ok = r.get("o_A0"), r.get(f"o_{name}")
    if ob is None or ok is None:
        return None
    vb = 0.0 if ob == "no_fill" else r_fixed(r.get("ret_A0"), r.get("e_A0"),
                                             r.get("e_A0"), r["stop"])
    vk = 0.0 if ok == "no_fill" else r_fixed(r.get(f"ret_{name}"),
                                             r.get(f"e_{name}"),
                                             r.get("e_A0"), r["stop"])
    if vb is None or vk is None:
        return None
    return vk - vb


def pool_clusters(gs):
    """يجمع عناقيدَ السنوات **بالرمز** — رمزٌ يظهر في سنتين يبقى **عنقودًا
    واحدًا** لا اثنين، وإلّا انكسر استقلالُ العنقود وضاق الفاصلُ كذبًا.
    (‏`T-TRANCHE` جمعت هكذا: «4,817 زوجًا · **1,375 رمزًا**» لا 2,222.)"""
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
    """§⑨-4 (مُعادٌ من `T-TRANCHE` حرفيًّا): `no_fill` = صفرُ عائدٍ **ويدخل
    المقام** — فالمقامُ واحدٌ للأذرع الخمس."""
    fx, n_fill, wins = [], 0, 0
    for r in rows:
        o = r.get(f"o_{name}")
        if o is None:
            continue
        if o == "no_fill":
            fx.append(0.0)
            continue
        n_fill += 1
        if o == "win":
            wins += 1
        v = r_fixed(r.get(f"ret_{name}"), r.get(f"e_{name}"), r.get("e_A0"),
                    r["stop"])
        fx.append(v if v is not None else 0.0)
    n = len(fx)
    rets = [r.get(f"ret_{name}") for r in rows
            if r.get(f"o_{name}") not in (None, "no_fill")
            and r.get(f"ret_{name}") is not None]
    return {"n": n, "n_fill": n_fill,
            "fill_pct": (n_fill / n * 100.0) if n else 0.0,
            "win_pct": (wins / n_fill * 100.0) if n_fill else 0.0,
            "r_fixed": (sum(fx) / n) if n else 0.0,
            "ret_avg": (sum(rets) / len(rets)) if rets else 0.0}


def report(rows, year, issues):
    """يطبع البوّابات والجدول. خروج: 0 سليم · 3 عطبُ أداة · 4 `no-op`/أرضية."""
    attempted = len(rows) + sum(issues.values())
    _log(f"\n🎯 T-T1MOVE · سنة {year} · صفقات {len(rows)} من {attempted}")
    if issues:
        _log("   ℹ️ أسبابُ عدم القياس: " + " · ".join(
            f"{k} {v}" for k, v in sorted(issues.items())))
    if not rows:
        _log("   ⛔ صفرُ صفقات ⇒ بصمةُ `no-op`")
        return 4

    # `V4` — تغطيةُ الصفقات ‏≥95% والمفقودُ يُسمّى
    cov = len(rows) / attempted * 100.0 if attempted else 0.0
    _log(f"   🔒 `V4`: التغطية {cov:.1f}% ({len(rows)}/{attempted})")
    if cov < 95.0:
        _log("   ⛔ `V4` التغطيةُ دون 95% ⇒ مجتمعٌ مبتور")
        return 3

    # سلّمُ `A0` يطابق دفعاتِ الإنتاج بت-بت (شرطُ صلاحيةِ المِرساة — درسُ `TV1`)
    mism = [r for r in rows if r.get("tr0") != r.get("prod_tr")]
    _log(f"   🔒 سلّمُ `A0` يطابق دفعاتِ الإنتاج في "
         f"{len(rows) - len(mism)} من {len(rows)}")
    if mism:
        m = mism[0]
        _log(f"   ⛔ تفرّق — {m['symbol']}/{m['date']}: "
             f"{m.get('tr0')} مقابل {m.get('prod_tr')}")
        return 3

    a = {name: agg(rows, name) for name, _o, _m in ARMS}

    # `V0`/`V1` — إعادةُ أرقام `T-TRANCHE` المنشورة بت-بت
    pub = PUBLISHED.get(str(year))
    if pub:
        for nm, gate in (("A0", "V0"), ("M1", "V1")):
            got, want = round(a[nm]["r_fixed"], 4), pub[nm]
            okk = abs(got - want) < 1e-9
            _log(f"   🔒 `{gate}`: {nm} = {got:+.4f} · المنشور {want:+.4f} "
                 f"{'✅' if okk else '❌'}")
            if not okk:
                _log(f"   ⛔ `{gate}` لم يُعِد المنشورَ ⇒ عطبُ أداةٍ لا نتيجة")
                return 3
    else:
        _log(f"   ⚠️ لا رقمَ منشورًا لسنة {year} ⇒ `V0`/`V1` غيرُ قابلتين للفحص")

    # `V3` — الهدفُ لا يؤثّر في التعبئة بالبناء ⇒ `M1` و`M2` متطابقتا التعبئة
    if a["M1"]["n_fill"] != a["M2"]["n_fill"]:
        _log(f"   ⛔ `V3` التعبئةُ تفرّقت: M1={a['M1']['n_fill']} "
             f"M2={a['M2']['n_fill']} ⇒ عطبُ أداة")
        return 3
    _log(f"   🔒 `V3`: تعبئةُ `M1` و`M2` متطابقة ({a['M1']['n_fill']})")

    # `V2` — التفرّق (بصمةُ `no-op`)
    same = []
    for x, y in (("M1", "M2"), ("M2", "M4")):
        if all(r.get(f"o_{x}") == r.get(f"o_{y}")
               and r.get(f"ret_{x}") == r.get(f"ret_{y}") for r in rows):
            same.append(f"{x}≡{y}")
    if same:
        _log(f"   ⛔ `V2` لم تتفرّق: {' · '.join(same)} ⇒ `no-op`")
        return 4
    _log("   🔒 `V2`: الأذرعُ تتفرّق (M1≠M2 · M2≠M4)")

    if a["A0"]["n"] < FLOOR_YEAR or a[GOV]["n"] < FLOOR_YEAR:
        _log(f"   ⛔ الأرضية: {a['A0']['n']}/{a[GOV]['n']} دون {FLOOR_YEAR} "
             "⇒ لا حكم")
        return 4

    _log("   ┌─ الأذرع (الحاكم: متوسّطُ R₀ · و`no_fill`=0R يدخل المقام) ─")
    for name, off, mode in ARMS:
        x = a[name]
        mark = " 🥇" if name == GOV else ""
        _log(f"   │ {name} (‏إزاحة {off:+.1f}% · هدفٌ {mode}){mark}: "
             f"R₀ {x['r_fixed']:+.4f} · تعبئة {x['fill_pct']:.2f}% "
             f"({x['n_fill']}) · ربح {x['win_pct']:.2f}% · "
             f"عائدٌ محقَّق {x['ret_avg']:+.2f}%")
    _log("   └───────────────────────────────────────────────────────────")

    for name, _o, _m in ARMS[1:]:
        g = clusters(rows, name)
        ci = boot_ci(g) if name == GOV else None
        line = (f"   🎯 {name}−A0 بـR₀ = "
                f"{a[name]['r_fixed'] - a['A0']['r_fixed']:+.4f}")
        if ci:
            line += (f"   · مقترنًا {ci['mean']:+.4f} "
                     f"[{ci['lo']:+.4f} · {ci['hi']:+.4f}] "
                     f"· أزواج {ci['n']} · رموز {ci['k']}")
        _log(line)

    ks = round(sum(r["k"] for r in rows) / len(rows), 4)
    _log(f"   📏 وسيطُ الحساب: متوسّطُ `k` = {ks:+.4f} "
         f"(نسبةُ العائد إلى المخاطرة في خطّة الإنتاج)")

    _log("SUMMARY " + json.dumps(
        {"year": year, "arms": a, "n_rows": len(rows), "cov": round(cov, 2),
         "k_avg": ks}, ensure_ascii=False))
    gg = clusters(rows, GOV)
    _log("CLUSTERS " + json.dumps(
        {"year": year, "gov": GOV,
         "c": [[_s, v[0], round(v[1], 6)] for _s, v in sorted(gg.items())]},
        ensure_ascii=False))
    return 0


def _measure(S, year, frozen):
    """يقيس سنةً واحدةً على لقطتها ويُرجع `(rc, rows, issues)`.
    🔒 **مصدرٌ واحد**: مسارُ السنة المفردة ومسارُ التجميع ينادِيانه معًا فلا
    يتفرّق مقياسان على المجتمع نفسِه (درسُ «مقياسٌ واحدٌ لا اثنان»)."""
    hist, splits_map, asof = S.load_frozen_dataset(frozen)
    if not hist:
        _log("⛔ تعذّر تحميل اللقطة")
        return 2, [], {}
    S.CONFIG["BT_REPLAY10"] = 1
    S.CONFIG["BT_ENVVALS"] = 1
    # §② — الوقفُ المشحون لا يُمَسّ (عزلُ أثر الهدف عن أثر الوقف شرطُ صلاحية)
    if not S.CONFIG.get("PIVOT_STOP_AT_LOW"):
        _log("⛔ `A0` يشترط وقفَ القاع المشحون (`PIVOT_STOP_AT_LOW`) — مُطفأ")
        return 3, [], {}
    n_tr = max(1, int(S.CONFIG["ENTRY_TRANCHES"]))
    step_pct = float(S.CONFIG["ENTRY_STEP_PCT"])
    fwd = int(S.CONFIG["BACKTEST_FORWARD_DAYS"])
    spread = S.CONFIG.get("BT_SPREAD_PCT", 0.0) or 0.0
    lo_d, hi_d = f"{year}-01-01", f"{year}-12-31"
    # 🔒 بوّابةُ اللقطة: سنةُ اللقطة **تطابق** سنةَ القياس (درسُ 2026-08-29:
    #    لقطةُ 2024 على سنة 2025 أعطت 153 صفقة مقابل 1606 **بخروجٍ صفريّ صامت**).
    if str(asof or "")[:4] != str(year):
        _log(f"⛔ اللقطة as-of {asof} لا تطابق سنةَ القياس {year} — "
             "مجتمعٌ مختلف، لا تُقاس")
        return 4, [], {}
    syms = sorted(hist)
    _log(f"📦 اللقطة as-of {asof} · رموز {len(syms)} · دفعات {n_tr}×{step_pct}% "
         "· الأذرع " + " · ".join(f"{n}{o:+.0f}%/{m}" for n, o, m in ARMS))
    rows, issues = [], {}
    missing = []
    with open(OUT_ROWS, "w", encoding="utf-8") as fh:
        for k, sym in enumerate(syms):
            df = hist.get(sym)
            # 🧊 مجمَّدٌ على `T-TRANCHE` (‏`MIN_BARS + 60`) وإلّا استحال أن
            #    تُعيد `V0`/`V1` أرقامَها المنشورة.
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
                                    step_pct)
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
    """§④ **مجمَّعًا**: يقيس السنوات في تشغيلةٍ واحدة ثم يجمع عناقيدَ البوتستراب
    **بالرمز عبر السنوات** — كما فعلت `T-TRANCHE` («4,817 زوجًا · 1,375 رمزًا»
    = رموزٌ مجمَّعة لا سنةً سنة) — فيصدر فاصلُ ثقةٍ واحدٌ لا ثلاثة.
    ⚖️ **والميزانيةُ واحدةٌ بالبناء**: السنواتُ الثلاث في تشغيلةٍ واحدة بنفس
    الكود ونفس السقوف (قاعدةُ `karpathy/autoresearch` المدوَّنة)."""
    items = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        year, _sep, path = part.partition(":")
        items.append((year.strip(), path.strip()))
    if len(items) < 2:
        _log("⛔ `T1MOVE_POOL` يلزمه سنتان فأكثر بصيغة سنة:مسار")
        return 2
    pooled, per_year, tot_rows = {}, [], 0
    for year, path in items:
        if not path or not os.path.exists(path):
            _log(f"⛔ لقطةُ {year} غيرُ موجودة: {path}")
            return 2
        rc, rows, issues = _measure(S, year, path)
        if rc:
            return rc
        rc = report(rows, year, issues)
        if rc:
            return rc
        pooled = pool_clusters([pooled, clusters(rows, GOV)])
        d = agg(rows, GOV)["r_fixed"] - agg(rows, "A0")["r_fixed"]
        per_year.append((year, d, len(rows)))
        tot_rows += len(rows)
    ci = boot_ci(pooled)
    _log("\n" + "=" * 62)
    _log(f"🎯 T-T1MOVE · الحكمُ المجمَّع · {GOV} − A0 (وحدةُ المخاطرة R₀)")
    _log("   " + " · ".join(f"{y} {d:+.4f}" for y, d, _n in per_year))
    _log(f"   📐 مجمَّعًا {ci['mean']:+.4f}R "
         f"[{ci['lo']:+.4f} · {ci['hi']:+.4f}] "
         f"· أزواج {ci['n']} · رموز {ci['k']}")
    c1 = ci["mean"] >= BAR_R
    c2 = all(d > 0 for _y, d, _n in per_year)
    c3 = (ci["lo"] > 0) or (ci["hi"] < 0)
    c4 = tot_rows >= FLOOR_TOTAL and all(n >= FLOOR_YEAR
                                         for _y, _d, n in per_year)
    ok = "✅"
    bad = "🔴"
    _log(f"   ① الفرقُ يبلغ {BAR_R:+.2f}R فأكثر: "
         f"{ci['mean']:+.4f} {ok if c1 else bad}")
    _log(f"   ② موجبُ الإشارة في السنوات كلِّها: {ok if c2 else bad}")
    _log(f"   ③ الفاصلُ لا يلمس الصفر: {ok if c3 else bad}")
    _log(f"   ④ الأرضية ({FLOOR_TOTAL} مجمَّعًا · {FLOOR_YEAR} لكلّ سنة): "
         f"{tot_rows} · {ok if c4 else bad}")
    n_ok = sum(1 for x in (c1, c2, c3, c4) if x)
    _log(f"   ⇒ **{n_ok} من 4** — "
         + ("تُوصى" if n_ok == 4 else "لا تُوصى"))
    _log("=" * 62)
    _log("POOLED " + json.dumps(
        {"gov": GOV, "mean": round(ci["mean"], 6),
         "lo": round(ci["lo"], 6), "hi": round(ci["hi"], 6),
         "pairs": ci["n"], "symbols": ci["k"],
         "per_year": [[y, round(d, 6), n] for y, d, n in per_year],
         "criteria": [c1, c2, c3, c4], "passed": n_ok},
        ensure_ascii=False))
    return 0 if n_ok == 4 else 1


def main() -> int:
    if not _selfcheck_readonly():
        _log("⛔ `V6` الأداةُ ليست قراءةً فقط")
        return 3
    os.environ["SCREENER_MODE"] = "BACKTEST"
    import Super_stock as S                                      # noqa: PLC0415
    spec = (os.environ.get("T1MOVE_POOL") or "").strip()
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
    rc, rows, issues = _measure(S, year, frozen)
    if rc:
        return rc
    return report(rows, year, issues)


if __name__ == "__main__":
    sys.exit(main())
