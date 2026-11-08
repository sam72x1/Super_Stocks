# -*- coding: utf-8 -*-
"""📱⚖️ `T-APPDIFF` — «ثلاثة فروق بين تطبيق فيصل والبوت» (العقد `T_APPDIFF_prereg.md` · مدموجٌ قبل أيّ رقم).

قراءةٌ وقياسٌ فقط: لا يُستورَد في الإنتاج · لا يكتب حالةً · لا تلغرام · و③ ظلٌّ لا يمسّ `ANCHOR_MODE` ولا H6.
البنيةُ `T-REBUILD` بالاسم (`fm_forensics/rebuild/rebuild.py`): اللقطاتُ الشهريّة · الشموعُ وحرّاسُها · `asof_factor` · `exploded` · `new_entries` ·
`configs` · `install_stubs` · `post_scan` · ووكيلُ الفلوت `PROXY_URL` — لا نسخة.

الأوضاع: `--mode check` (بلا شبكة) · `prep` · `shard` (SHARD · NSHARDS) · `assemble` — وكلُّها تخرج 9 إن تغيّرت بصمةُ العقد.
"""
import argparse
import bisect
import datetime as dt
import glob
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CONTRACT = os.path.join(HERE, "T_APPDIFF_prereg.md")
CONTRACT_SHA = "c435d50b38a6a4c551585d9994f90b18cd5f370e69e49d4de6fccf2ad30d8901"
CONTRACT_RC = 9
OUT = os.path.join(HERE, "out")
SEED = 20261108
BOOT_B = 2000
WIN = 20
PCT = 50.0
PERIOD = ("2023-01-03", "2025-12-31")
YEARS = ("2023", "2024", "2025")
FLOOR = 30
PROXY_UNKNOWN_MAX = 0.20
BUDGET = 2.0
F5_MAX = 5_000_000
T1_WIN, T1_DIST = 30, 0.05
NSTRATA = 5
MONTHS = [(2022, 12)] + [(y, m) for y in (2023, 2024, 2025) for m in range(1, 13)]
SESS_FROM, SESS_TO, ALL_FROM = "2022-12-01", "2025-12-31", "2022-11-01"
# صفُّ الشريحة: [D، cur، b، below، m12، f5، t1، t2، ret5، y، proxy]
I_D, I_CUR, I_B, I_BELOW, I_M12, I_F5, I_T1, I_T2, I_R5, I_Y, I_PX = range(11)


def log(*a):
    print(*a, flush=True)


def contract_ok(path=CONTRACT, sha=None):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest() == (sha or CONTRACT_SHA)
    except OSError:
        return False


def _rb():
    sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "rebuild"))
    sys.path.insert(0, ROOT)
    import rebuild as RB
    return RB


# ── الأعلام (نقيّة · §②) ───────────────────────────────────────────────────────────────────────────
def below_all(S, closes):
    """التطبيق ①: إغلاقُ D−1 أقلّ من EMA20 وEMA30 وEMA50 معًا (`Super_stock.ema` · adjust=False)."""
    if closes is None or len(closes) < 1:
        return False
    p = float(closes.iloc[-1])
    ms = [S.ema(closes, n) for n in (20, 30, 50)]
    return all(m > 0 and p < m for m in ms)


def m12_ok(S, closes, band_pct):
    """البوت ①: صيغةُ M12 في `analyze_ticker` بحرفها — ∃ m ∈ {EMA30، EMA50}: m > 0 ∧ السعر ≥ m×0.98 ∧ (السعر÷m − 1) ≤ الحدّ."""
    if closes is None or len(closes) < 1:
        return False
    price = float(closes.iloc[-1])
    band = float(band_pct) / 100.0
    return any(m > 0 and (price >= m * (1.0 - 0.02)) and (price / m - 1.0) <= band
               for m in (S.ema(closes, 30), S.ema(closes, 50)))


def one_touch(lows, closes, win=T1_WIN, dist=T1_DIST):
    """التطبيق ③ تشغيليًّا: L1 = أدنى Low في آخر `win` شمعة · آخرُ شمعةٍ بلغته ليست الأخيرة (لمسةٌ «ناجحة») · و0 ≤ إغلاقُ D−1 ÷ L1 − 1 ≤ dist.
    ⟵ (ok، L1، المسافة) · وما نقص ⟵ (False، None، None)."""
    lo = [float(x) for x in list(lows)[-win:]]
    cl = [float(x) for x in list(closes)[-win:]]
    if len(lo) < 3 or len(cl) != len(lo):
        return False, None, None
    L1 = min(lo)
    if not L1 > 0:
        return False, None, None
    t = max(k for k, x in enumerate(lo) if x == L1)
    d = cl[-1] / L1 - 1.0
    return (t <= len(lo) - 2 and 0.0 <= d <= dist), round(L1, 6), round(d, 6)


def ret5(closes):
    cl = [float(x) for x in list(closes)]
    if len(cl) < 6 or not cl[-6] > 0:
        return None
    return round(cl[-1] / cl[-6] - 1.0, 6)


def f5_flag(proxy):
    return None if proxy is None else int(float(proxy) <= F5_MAX)


# ── الشريحة ─────────────────────────────────────────────────────────────────────────────────────────
def appdiff_symbol(sym, rows, splits_sym, member_days, prev_of, finra, proxy_fn, S, cfg_cur, cfg_piv, G5, RB):
    """صفوفُ رمزٍ: [[D، cur، b، below، m12، f5، t1، t2، ret5، y، proxy]] حيث تنطلق CURRENT أو B · بحرّاس `rebuild.shard_symbol` بحرفها."""
    import pandas as pd
    cnt = {"rows": 0, "no_history": 0, "stale": 0, "excl_split": 0, "excl_gap": 0, "unlabeled": 0,
           "pass_cur": 0, "pass_piv": 0, "fire_cur": 0, "fire_b": 0}
    out = []
    if not rows:
        return out, cnt
    dates = [x[0] for x in rows]
    full = pd.DataFrame({"Open": [x[1] for x in rows], "High": [x[2] for x in rows], "Low": [x[3] for x in rows],
                         "Close": [x[4] for x in rows], "Volume": [x[5] for x in rows]}, index=pd.to_datetime(dates))
    unadj = G5.split_unadjusted(rows, splits_sym, "0000-00-00", "9999-99-99")
    gp = RB.gaps(rows)
    band = float(cfg_cur["MA_GATE_MAX_ABOVE_PCT"])
    for d in member_days:
        i = bisect.bisect_left(dates, d)
        if i < 1:
            cnt["no_history"] += 1
            continue
        if (dt.date.fromisoformat(d) - dt.date.fromisoformat(dates[i - 1])).days > RB.STALE_DAYS:
            cnt["stale"] += 1
            continue
        sp, gq = RB.row_guards(dates, i, d, unadj, gp)
        if sp:
            cnt["excl_split"] += 1
            continue
        if gq:
            cnt["excl_gap"] += 1
            continue
        cnt["rows"] += 1
        y = RB.exploded(rows, d, PCT)
        cnt["unlabeled"] += y is None
        lo = bisect.bisect_left(dates, (dt.date.fromisoformat(d) - dt.timedelta(RB.HISTORY_DAYS)).isoformat())
        sub = full.iloc[lo:i]
        f = RB.asof_factor(splits_sym, d)
        if f != 1.0:
            sub = sub.copy()
            sub[["Open", "High", "Low", "Close"]] *= f
            sub["Volume"] /= f
        res = []
        for k, cfg in ((0, cfg_cur), (1, cfg_piv)):
            RB.with_config(S, cfg)
            try:
                r = S.analyze_ticker(sym, sub)
            except Exception:                                   # noqa: BLE001
                r = None
            res.append((k, cfg, r))
        if not any(r for _k, _c, r in res):
            continue
        prev = prev_of[d]
        short = (finra.get(prev) or {}).get(sym)
        proxy = proxy_fn(sym, prev)
        fired = [False, False]
        for k, cfg, r in res:
            if r:
                cnt["pass_cur" if k == 0 else "pass_piv"] += 1
                RB.with_config(S, cfg)
                fired[k] = RB.post_scan(S, r, short, proxy)
        cnt["fire_cur"] += fired[0]
        cnt["fire_b"] += fired[1]
        if not any(fired):
            continue
        cl, lw = sub["Close"], sub["Low"]
        RB.with_config(S, cfg_cur)
        t1 = one_touch(lw, cl)[0]
        t2 = S.tested_level(sub) is not None
        out.append([d, int(fired[0]), int(fired[1]), int(below_all(S, cl)), int(m12_ok(S, cl, band)), f5_flag(proxy),
                    int(t1), int(t2), ret5(cl), y, proxy])
    RB.with_config(S, cfg_cur)
    return out, cnt


def cfgs_of(S, RB):
    """(CURRENT، B): الحيّةُ كما يشتقّها `rebuild.configs` · وB = هي مع `BT_ANCHOR="pivot"` (`_anchor_mode` يُرجع فراغًا ⟵ لا مِرساةَ مختبَرة)."""
    cur, _org = RB.configs(S)
    piv = dict(cur)
    piv["BT_ANCHOR"] = "pivot"
    return cur, piv


# ── التجميع (نقيّ · §③-§⑤) ──────────────────────────────────────────────────────────────────────────
RULES = {
    "CUR": lambda r: r[I_CUR] == 1,
    "CUR_BELOW": lambda r: r[I_CUR] == 1 and r[I_BELOW] == 1,
    "CUR_NBELOW": lambda r: r[I_CUR] == 1 and r[I_BELOW] != 1,
    "CUR_M12": lambda r: r[I_CUR] == 1 and r[I_M12] == 1,
    "CUR_NM12": lambda r: r[I_CUR] == 1 and r[I_M12] != 1,
    "CUR_F5": lambda r: r[I_CUR] == 1 and r[I_F5] == 1,
    "CUR_NF5": lambda r: r[I_CUR] == 1 and r[I_F5] != 1,
    "B": lambda r: r[I_B] == 1,
    "B_T1": lambda r: r[I_B] == 1 and r[I_T1] == 1,
    "B_T2": lambda r: r[I_B] == 1 and r[I_T2] == 1,
}


def entries(rows_by, sessions, pred, period=PERIOD, new_entries=None):
    """§③ الإدخالُ الجديد لقاعدة: أيّامُ انطلاقها لكلّ رمز ⟵ `rebuild.new_entries` (‏20 جلسة) ⟵ داخل الفترة ⟵ {(sym، D): صفّ}."""
    if new_entries is None:
        new_entries = _rb().new_entries
    out = {}
    for sym, rws in rows_by.items():
        by = {r[I_D]: r for r in rws if pred(r)}
        for d in new_entries(sorted(by), sessions, WIN):
            if period[0] <= d <= period[1]:
                out[(sym, d)] = by[d]
    return out


def cuts_of(ents, n=NSTRATA):
    xs = sorted(r[I_R5] for r in ents.values() if r[I_R5] is not None)
    if len(xs) < n:
        return []
    return [xs[int(len(xs) * k / n)] for k in range(1, n)]


def stratum(x, cuts):
    return None if x is None else bisect.bisect_right(cuts, x)


def share(ents):
    lab = [r[I_Y] for r in ents.values() if r[I_Y] is not None]
    return {"n": len(ents), "lab": len(lab), "exp": sum(1 for y in lab if y), "p": (sum(1 for y in lab if y) / len(lab)) if lab else None}


def _tab(ents, cuts):
    """{sym: [[lab_s، exp_s] × NSTRATA]} للموسوم بطبقةٍ معلومة."""
    t = {}
    for (sym, _d), r in ents.items():
        s = stratum(r[I_R5], cuts)
        if r[I_Y] is None or s is None:
            continue
        a = t.setdefault(sym, [[0, 0] for _ in range(NSTRATA)])
        a[s][0] += 1
        a[s][1] += int(bool(r[I_Y]))
    return t


def _delta(ta, tr):
    """Δ = p_A − Σ_s w_{A,s} p_{R,s} على جداول مجمَّعة · وإدخالاتُ A في طبقةٍ بلا موسومٍ في R تُستبعد (تُعَدّ)."""
    la = [0] * NSTRATA
    ea = [0] * NSTRATA
    lr = [0] * NSTRATA
    er = [0] * NSTRATA
    for a in ta.values():
        for s in range(NSTRATA):
            la[s] += a[s][0]
            ea[s] += a[s][1]
    for a in tr.values():
        for s in range(NSTRATA):
            lr[s] += a[s][0]
            er[s] += a[s][1]
    keep = [s for s in range(NSTRATA) if la[s] and lr[s]]
    n = sum(la[s] for s in keep)
    if not n:
        return None, sum(la)
    pa = sum(ea[s] for s in keep) / n
    exp = sum(la[s] / n * er[s] / lr[s] for s in keep)
    return pa - exp, sum(la) - n


def adj_delta(ents_a, ents_r, cuts):
    d, dropped = _delta(_tab(ents_a, cuts), _tab(ents_r, cuts))
    return {"delta": d, "dropped": dropped}


def boot_delta(ents_a, ents_r, cuts, seed=SEED, b=BOOT_B):
    """فاصلُ 95% لـΔ ببوتستراب عنقوديٍّ بالرمز (يُسحب الرمزُ بإدخالاته في A وR معًا)."""
    import numpy as np
    ta, tr = _tab(ents_a, cuts), _tab(ents_r, cuts)
    syms = sorted(set(ta) | set(tr))
    if not syms:
        return None
    z = [[0, 0] for _ in range(NSTRATA)]
    A = np.array([ta.get(s, z) for s in syms], dtype=float)          # [sym، طبقة، (lab، exp)]
    R = np.array([tr.get(s, z) for s in syms], dtype=float)
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(b):
        w = np.bincount(rng.integers(0, len(syms), len(syms)), minlength=len(syms)).astype(float)
        sa = np.tensordot(w, A, axes=1)
        sr = np.tensordot(w, R, axes=1)
        keep = (sa[:, 0] > 0) & (sr[:, 0] > 0)
        n = sa[keep, 0].sum()
        if not n:
            continue
        out.append(sa[keep, 1].sum() / n - float((sa[keep, 0] / n * sr[keep, 1] / sr[keep, 0]).sum()))
    if not out:
        return None
    out.sort()
    return [round(float(out[int(0.025 * len(out))]), 4), round(float(out[min(len(out) - 1, int(0.975 * len(out)))]), 4)]


def by_year(ents, y):
    return {k: v for k, v in ents.items() if k[1][:4] == y}


def compare(ents_a, ents_r, cuts, seed=SEED, b=BOOT_B):
    """Δ المضبوط بفاصله · والخامُ · ولكلّ سنةٍ Δ وموسومُ الجانبين."""
    sa, sr = share(ents_a), share(ents_r)
    res = {"A": sa, "R": sr, "raw": (sa["p"] - sr["p"]) if sa["p"] is not None and sr["p"] is not None else None,
           "adj": adj_delta(ents_a, ents_r, cuts), "ci": boot_delta(ents_a, ents_r, cuts, seed, b), "years": {}}
    for y in YEARS:
        ay, ry = by_year(ents_a, y), by_year(ents_r, y)
        res["years"][y] = {"lab_a": share(ay)["lab"], "lab_r": share(ry)["lab"], "delta": adj_delta(ay, ry, cuts)["delta"]}
    return res


def verdict(cmp, words=("يرفع", "يخفض"), extra_nq=False):
    """§⑤ بالأضعف: الفاصلُ ∧ إشارةُ السنوات الثلاث · و«لا قياس» تحت 30 موسومًا لأيّ جانبٍ في أيّ سنة."""
    if extra_nq or any(v["lab_a"] < FLOOR or v["lab_r"] < FLOOR for v in cmp["years"].values()):
        return "لا قياس"
    ci, ys = cmp["ci"], [v["delta"] for v in cmp["years"].values()]
    if ci is None or any(x is None for x in ys):
        return "لا قياس"
    if ci[0] > 0 and all(x > 0 for x in ys):
        return words[0]
    if ci[1] < 0 and all(x < 0 for x in ys):
        return words[1]
    return "لا فرق قابل للكشف"


def n_sessions(sessions, period=PERIOD):
    return sum(1 for d in sessions if period[0] <= d <= period[1])


def analyse(rows_by, sessions, seed=SEED, b=BOOT_B):
    E = {k: entries(rows_by, sessions, p) for k, p in RULES.items()}
    ns = n_sessions(sessions)
    cut_cur, cut_b = cuts_of(E["CUR"]), cuts_of(E["B"])
    cur_n = len(E["CUR"])
    unk = sum(1 for r in E["CUR"].values() if r[I_F5] is None)
    res = {"n_sess": ns, "cuts_cur": cut_cur, "cuts_b": cut_b, "counts": {k: share(v) for k, v in E.items()},
           "per_day": {k: round(len(v) / ns, 3) if ns else None for k, v in E.items()},
           "below_share": round(sum(1 for r in E["CUR"].values() if r[I_BELOW] == 1) / cur_n, 4) if cur_n else None,   # حصّةُ إدخالات CURRENT بالعلَم
           "f5_share": round(sum(1 for r in E["CUR"].values() if r[I_F5] == 1) / cur_n, 4) if cur_n else None,
           "proxy_unknown": round(unk / cur_n, 4) if cur_n else None}
    res["c1_below"] = compare(E["CUR_BELOW"], E["CUR_NBELOW"], cut_cur, seed, b)
    res["c1_m12"] = compare(E["CUR_M12"], E["CUR_NM12"], cut_cur, seed, b)
    res["c2_f5"] = compare(E["CUR_F5"], E["CUR_NF5"], cut_cur, seed, b)
    res["c3_t1"] = compare(E["B_T1"], E["CUR"], cut_b, seed, b)
    res["c3_b"] = compare(E["B"], E["CUR"], cut_b, seed, b)
    res["c3_t2"] = compare(E["B_T2"], E["CUR"], cut_b, seed, b)
    res["v"] = {"c1_below": verdict(res["c1_below"]), "c1_m12": verdict(res["c1_m12"]),
                "c2_f5": verdict(res["c2_f5"], extra_nq=(res["proxy_unknown"] or 0) > PROXY_UNKNOWN_MAX),
                "c3_t1": verdict(res["c3_t1"], ("أدقّ", "أقلّ دقّة")), "c3_b": verdict(res["c3_b"], ("أدقّ", "أقلّ دقّة"))}
    res["budget"] = {k: (round(len(E[k]) / cur_n, 3) if cur_n else None) for k in ("B_T1", "B", "B_T2")}
    res["in_budget"] = {k: (v is not None and v <= BUDGET) for k, v in res["budget"].items()}
    res["shadow_ok"] = {k: res["v"][c] == "أدقّ" and res["in_budget"][k] for k, c in (("B_T1", "c3_t1"), ("B", "c3_b"))}
    return res


def predictions(res):
    v = res["v"]
    bs, fs = res.get("below_share"), res.get("f5_share")
    return {
        "APD1": bs is not None and 0.40 <= bs <= 0.80,
        "APD2": v["c1_below"] == "لا فرق قابل للكشف",
        "APD3": v["c1_m12"] == "لا فرق قابل للكشف",
        "APD4": fs is not None and 0.05 <= fs <= 0.30,
        "APD5": v["c2_f5"] == "يرفع",
        "APD6": res["in_budget"]["B"] is False,
        "APD7": res["in_budget"]["B_T1"] is False,
        "APD8": v["c3_t1"] == "لا فرق قابل للكشف",
        "APD9": v["c3_b"] == "لا فرق قابل للكشف",
    }


def _p(x, s="+.1f", mul=100.0):
    return "—" if x is None else format(x * mul, s)


def _row(name, c, ver, extra=""):
    ci = c["ci"]
    ys = " · ".join(f"{y} {_p(v['delta'])} ({v['lab_a']}/{v['lab_r']})" for y, v in c["years"].items())
    return (f"| {name} | {c['A']['n']} | {_p(c['A']['p'], '.1f')} | {_p(c['R']['p'], '.1f')} | {_p(c['raw'])} | **{_p(c['adj']['delta'])}** "
            f"[{_p(ci[0]) if ci else '—'}، {_p(ci[1]) if ci else '—'}] | {ys} | {extra}**{ver}** |")


def report_lines(res, meta, preds, counts=None):
    pdy, cn = res["per_day"], res["counts"]
    L = ["# 📱⚖️ `T-APPDIFF` — النتيجة (مولَّدةٌ بـ`appdiff.py --mode assemble` · لا رقمَ باليد)", "",
         f"**التشغيلة:** {meta.get('run')} · `{(meta.get('sha') or '')[:9]}` · الجلسات {res['n_sess']} (2023-01-03…2025-12-31)", ""]
    if counts:
        L += [f"- الصفوفُ المقيمة {counts.get('rows')} · قِدَم {counts.get('stale')} · فجوة {counts.get('excl_gap')} · تقسيمٌ غيرُ مسوّى "
              f"{counts.get('excl_split')} · بلا وسم {counts.get('unlabeled')} · عبورُ `analyze_ticker`: الحاليّ {counts.get('pass_cur')} · "
              f"بلا مرساة {counts.get('pass_piv')} · وتغطيةُ الشموع {meta.get('coverage')}", ""]
    L += ["| القاعدة | الإدخالات | يوميًّا | الموسوم | منفجر | الدقّة % |", "|---|---|---|---|---|---|"]
    for k in RULES:
        c = cn[k]
        L.append(f"| {k} | {c['n']} | {pdy[k]} | {c['lab']} | {c['exp']} | {_p(c['p'], '.1f')} |")
    L += ["", f"- خُمَيساتُ `ret5` (CURRENT): {res['cuts_cur']} · (B): {res['cuts_b']}",
          f"- BELOW من إدخالات CURRENT {_p(res['below_share'], '.1f')}% · F5 {_p(res['f5_share'], '.1f')}% · الوكيلُ مجهول {_p(res['proxy_unknown'], '.1f')}%", "",
          "## ① المتوسّطات (الأساس CURRENT · المرجعُ X ∧ ¬A)", "",
          "| الذراع | n | دقّتُها % | دقّةُ المرجع % | الفرقُ الخام | **Δ المضبوط بالزخم** [95%] | Δ لكلّ سنة (موسوم A/R) | الحكم |",
          "|---|---|---|---|---|---|---|---|",
          _row("BELOW (التطبيق)", res["c1_below"], res["v"]["c1_below"]),
          _row("M12 (البوت)", res["c1_m12"], res["v"]["c1_m12"]),
          f"| بلا شرط (CURRENT) | {cn['CUR']['n']} | {_p(cn['CUR']['p'], '.1f')} | — | — | — | — | المرجع |", "",
          "## ② الفلوت (الأساس CURRENT ≤ 50 بالوكيل · المرجعُ X ∧ ¬F5)", "",
          "| الذراع | n | دقّتُها % | دقّةُ المرجع % | الفرقُ الخام | **Δ المضبوط بالزخم** [95%] | Δ لكلّ سنة (موسوم A/R) | الحكم |",
          "|---|---|---|---|---|---|---|---|",
          _row("F5 ≤ 5 ملايين (التطبيق)", res["c2_f5"], res["v"]["c2_f5"]), "",
          "## ③ المرساة — ظلّ (المرجعُ CURRENT · الميزانية 2×)", "",
          "| الذراع | n | دقّتُها % | دقّةُ CURRENT % | الفرقُ الخام | **Δ المضبوط بالزخم** [95%] | Δ لكلّ سنة (موسوم A/R) | الحكم |",
          "|---|---|---|---|---|---|---|---|",
          _row("B ∧ T1 لمسة 0–5% (التطبيق)", res["c3_t1"], res["v"]["c3_t1"],
               f"{res['budget']['B_T1']}× {'داخل' if res['in_budget']['B_T1'] else 'خارج'} الميزانية · "),
          _row("B بلا مرساة", res["c3_b"], res["v"]["c3_b"], f"{res['budget']['B']}× {'داخل' if res['in_budget']['B'] else 'خارج'} الميزانية · "),
          _row("B ∧ T2 لمستان (وصفًا)", res["c3_t2"], "وصف", f"{res['budget']['B_T2']}× · "),
          f"| CURRENT لمستان (الحاليّ) | {cn['CUR']['n']} | {_p(cn['CUR']['p'], '.1f')} | — | — | — | — | المرجع · {pdy['CUR']}/جلسة |", "",
          f"- **تُقترح ظلًّا (أدقّ ∧ داخل الميزانية):** B ∧ T1 {'✅' if res['shadow_ok']['B_T1'] else '❌'} · B {'✅' if res['shadow_ok']['B'] else '❌'}", "",
          "## ④ التنبّؤات (منشورةٌ قبل الرقم)", ""]
    L += [f"- `{k}` {'✅' if v else '❌'}" for k, v in preds.items()]
    L += ["", "🔒 لا شيء يُشحَن · لا تغييرَ في أيّ عتبةٍ أو جذر · و③ ظلٌّ لا يمسّ H6 ولا الإنتاج · والقرارُ للمالك."]
    return L


# ── الملحق 1 (`T_APPDIFF_ADDENDUM_1.md` · سقفُ M2 والعائد/المخاطرة) ─────────────────────────────────────
ADDENDUM = os.path.join(HERE, "T_APPDIFF_ADDENDUM_1.md")
ADDENDUM_SHA = "26dd45c175326da8932997394e55f9937db1ffdbae082f398402176a3a376034"
ARMS2 = {"C9999": {"MAX_DROP_PCT": 99.99}, "CNOCAP": {"MAX_DROP_PCT": 100.0}, "CNORR": {"MIN_RR_T1": -1e9}}
CAP_REASON = "M2_هبوط_فوق_97"                 # اسمُ رفض السقف في `analyze_ticker` بحرفه
AUDIT_K = 4                                   # §② أوّلُ 4 رموزٍ في كلّ شريحة بلا شرط
R_CLIP = (-1.0, 10.0)
TIMELINE = os.path.join(ROOT, "fm_forensics", "phase3", "FAISAL_TIMELINE.csv")
# صفُّ الملحق: [D، cur، c9999، cnocap، cnorr، ret5، y، R، rr، rk]
J_D, J_CUR, J_C9999, J_CNOCAP, J_CNORR, J_R5, J_Y, J_R, J_RR, J_RK = range(10)
ARM_IX = {"CUR": J_CUR, "C9999": J_C9999, "CNOCAP": J_CNOCAP, "CNORR": J_CNORR}


def addendum_ok(path=ADDENDUM, sha=None):
    return contract_ok(path, sha or ADDENDUM_SHA)


def plan_r(rows, i, entry, stop, t1, win=WIN, clip=R_CLIP):
    """§③ R لإدخال يومَ i = D: الوقفُ أوّلًا (−1) ⟵ وإلّا t1 ⟵ وإلّا إغلاقُ D+19 · بوحدة (الدخول − الوقف) · مقصوصٌ · None إن تعذّر."""
    try:
        entry, stop, t1 = float(entry), float(stop), float(t1)
    except (TypeError, ValueError):
        return None
    if not (entry > stop > 0) or i < 1 or i + win > len(rows):
        return None
    risk = entry - stop
    for k in range(i, i + win):
        if float(rows[k][3]) <= stop:
            return clip[0]
        if float(rows[k][2]) >= t1:
            return round(max(clip[0], min(clip[1], (t1 - entry) / risk)), 6)
    return round(max(clip[0], min(clip[1], (float(rows[i + win - 1][4]) - entry) / risk)), 6)


def need_arm(name, cur_res, cur_fired, reason):
    """§② هل تُشغَّل الذراعُ؟ — السقف: فقط إن رُفض CURRENT باسم السقف · العائد/المخاطرة: إن لم ينطلق CURRENT ∧ (عبر أو رُفض بنواقص)."""
    if name in ("C9999", "CNOCAP"):
        return cur_res is None and reason == CAP_REASON
    if name == "CNORR":
        return (not cur_fired) and (cur_res is not None or "نواقص" in str(reason or ""))
    return True


def appdiff2_symbol(sym, rows, splits_sym, member_days, prev_of, finra, proxy_fn, S, cfg_cur, G5, RB, audit=False):
    """صفوفُ الملحق لرمز · بحرّاس `appdiff_symbol` بحرفها · والأذرعُ مشروطةٌ (وبلا شرطٍ تحت `audit` مع عدّ المخالفة)."""
    import pandas as pd
    cnt = {"rows": 0, "no_history": 0, "stale": 0, "excl_split": 0, "excl_gap": 0, "unlabeled": 0,
           "pass_cur": 0, "fire_cur": 0, "fire_c9999": 0, "fire_cnocap": 0, "fire_cnorr": 0,
           "arm_calls": 0, "audit_rows": 0, "audit_mismatch": 0}
    out = []
    if not rows:
        return out, cnt
    cfgs = {k: dict(cfg_cur, **v) for k, v in ARMS2.items()}
    dates = [x[0] for x in rows]
    full = pd.DataFrame({"Open": [x[1] for x in rows], "High": [x[2] for x in rows], "Low": [x[3] for x in rows],
                         "Close": [x[4] for x in rows], "Volume": [x[5] for x in rows]}, index=pd.to_datetime(dates))
    unadj = G5.split_unadjusted(rows, splits_sym, "0000-00-00", "9999-99-99")
    gp = RB.gaps(rows)
    for d in member_days:
        i = bisect.bisect_left(dates, d)
        if i < 1:
            cnt["no_history"] += 1
            continue
        if (dt.date.fromisoformat(d) - dt.date.fromisoformat(dates[i - 1])).days > RB.STALE_DAYS:
            cnt["stale"] += 1
            continue
        sp, gq = RB.row_guards(dates, i, d, unadj, gp)
        if sp:
            cnt["excl_split"] += 1
            continue
        if gq:
            cnt["excl_gap"] += 1
            continue
        cnt["rows"] += 1
        y = RB.exploded(rows, d, PCT)
        cnt["unlabeled"] += y is None
        lo = bisect.bisect_left(dates, (dt.date.fromisoformat(d) - dt.timedelta(RB.HISTORY_DAYS)).isoformat())
        sub = full.iloc[lo:i]
        f = RB.asof_factor(splits_sym, d)
        if f != 1.0:
            sub = sub.copy()
            sub[["Open", "High", "Low", "Close"]] *= f
            sub["Volume"] /= f

        def _run(cfg):
            RB.with_config(S, cfg)
            getattr(S, "_REJECT_REASONS", {}).pop(sym, None)
            try:
                r = S.analyze_ticker(sym, sub)
            except Exception:                                   # noqa: BLE001
                r = None
            return r, (None if r else getattr(S, "_REJECT_REASONS", {}).get(sym))
        r0, why0 = _run(cfg_cur)
        prev = prev_of[d]
        short = (finra.get(prev) or {}).get(sym)
        ctx = {}

        def _fire(cfg, r):
            if not r:
                return False
            if "proxy" not in ctx:
                ctx["proxy"] = proxy_fn(sym, prev)
            RB.with_config(S, cfg)
            return bool(RB.post_scan(S, r, short, ctx["proxy"]))
        f0 = _fire(cfg_cur, r0)
        cnt["pass_cur"] += bool(r0)
        res = {"CUR": (r0, f0)}
        for k in ARMS2:
            if need_arm(k, r0, f0, why0):
                cnt["arm_calls"] += 1
                rk, _w = _run(cfgs[k])
                res[k] = (rk, _fire(cfgs[k], rk))
            else:
                res[k] = (r0, f0)
        if audit:
            for k in ARMS2:
                ru, _w = _run(cfgs[k])
                fu = _fire(cfgs[k], ru)
                cnt["audit_rows"] += 1
                cnt["audit_mismatch"] += int(fu != res[k][1])
        fired = {k: res[k][1] for k in ("CUR",) + tuple(ARMS2)}
        cnt["fire_cur"] += fired["CUR"]
        for k in ARMS2:
            cnt["fire_" + k.lower()] += fired[k]
        if not any(fired.values()):
            continue
        rr0 = next((res[k][0] for k in ("CUR",) + tuple(ARMS2) if res[k][1]), None)
        RB.with_config(S, cfg_cur)
        try:
            rkey = list(S.rank_key(rr0))
        except Exception:                                       # noqa: BLE001
            rkey = None
        stop = (rr0.get("stop") or (None,))[0]
        out.append([d, int(fired["CUR"]), int(fired["C9999"]), int(fired["CNOCAP"]), int(fired["CNORR"]), ret5(sub["Close"]), y,
                    plan_r(rows, i, rr0.get("price"), stop, rr0.get("t1")), rr0.get("rr"), rkey])
    RB.with_config(S, cfg_cur)
    return out, cnt


RULES2 = {
    "CUR": lambda r: r[J_CUR] == 1,
    "C9999": lambda r: r[J_C9999] == 1,
    "CNOCAP": lambda r: r[J_CNOCAP] == 1,
    "CNORR": lambda r: r[J_CNORR] == 1,
    "ADD_C9999": lambda r: r[J_C9999] == 1 and r[J_CUR] != 1,
    "ADD_CNOCAP": lambda r: r[J_CNOCAP] == 1 and r[J_CUR] != 1,
    "ADD_CNORR": lambda r: r[J_CNORR] == 1 and r[J_CUR] != 1,
}


def entries2(rows_by, sessions, pred, period=PERIOD, new_entries=None):
    if new_entries is None:
        new_entries = _rb().new_entries
    out = {}
    for sym, rws in rows_by.items():
        by = {r[J_D]: r for r in rws if pred(r)}
        for d in new_entries(sorted(by), sessions, WIN):
            if period[0] <= d <= period[1]:
                out[(sym, d)] = by[d]
    return out


def fire_days(rows_by, pred, period=PERIOD):
    return sum(1 for rws in rows_by.values() for r in rws if pred(r) and period[0] <= r[J_D] <= period[1])


def _as1(ents):
    """تحويلٌ إلى بنية العقد الأصل ([D… ret5 في I_R5 · y في I_Y]) لتُستعمَل `share`/`compare` بالاسم."""
    z = [None] * 11
    return {k: [r[J_D]] + z[1:I_R5] + [r[J_R5], r[J_Y], None] for k, r in ents.items()}


def _as1_r(ents):
    """بنيةٌ تحمل R في موضع الوسم (للمقارنة على R) — الصفُّ بلا R لا يُقاس."""
    z = [None] * 11
    return {k: [r[J_D]] + z[1:I_R5] + [r[J_R5], r[J_R], None] for k, r in ents.items() if r[J_R] is not None}


def _tab_r(ents, cuts):
    t = {}
    for (sym, _d), r in ents.items():
        s = stratum(r[I_R5], cuts)
        if r[I_Y] is None or s is None:
            continue
        a = t.setdefault(sym, [[0, 0.0] for _ in range(NSTRATA)])
        a[s][0] += 1
        a[s][1] += float(r[I_Y])
    return t


def compare_r(ents_a, ents_r, cuts, seed=SEED, b=BOOT_B):
    """Δ R المضبوطُ بالزخم بأوزان `_delta` نفسِها (متوسّطُ R بدل الحصّة) · وفاصلُه · ولكلّ سنة — بنيةُ `compare` لتمرّ على `verdict` بالاسم."""
    import numpy as np

    def _mean(e):
        xs = [float(r[I_Y]) for r in e.values() if r[I_Y] is not None]
        return {"n": len(e), "lab": len(xs), "exp": None, "p": (sum(xs) / len(xs)) if xs else None}

    def _adj(ea, er):
        return _delta(_tab_r(ea, cuts), _tab_r(er, cuts))[0]
    ta, tr = _tab_r(ents_a, cuts), _tab_r(ents_r, cuts)
    syms = sorted(set(ta) | set(tr))
    ci = None
    if syms:
        z = [[0, 0.0] for _ in range(NSTRATA)]
        A = np.array([ta.get(s, z) for s in syms], dtype=float)
        R = np.array([tr.get(s, z) for s in syms], dtype=float)
        rng = np.random.default_rng(seed)
        bo = []
        for _ in range(b):
            w = np.bincount(rng.integers(0, len(syms), len(syms)), minlength=len(syms)).astype(float)
            sa, sr = np.tensordot(w, A, axes=1), np.tensordot(w, R, axes=1)
            keep = (sa[:, 0] > 0) & (sr[:, 0] > 0)
            n = sa[keep, 0].sum()
            if n:
                bo.append(sa[keep, 1].sum() / n - float((sa[keep, 0] / n * sr[keep, 1] / sr[keep, 0]).sum()))
        if bo:
            bo.sort()
            ci = [round(float(bo[int(0.025 * len(bo))]), 4), round(float(bo[min(len(bo) - 1, int(0.975 * len(bo)))]), 4)]
    ma, mr = _mean(ents_a), _mean(ents_r)
    res = {"A": ma, "R": mr, "raw": (ma["p"] - mr["p"]) if ma["p"] is not None and mr["p"] is not None else None,
           "adj": {"delta": _adj(ents_a, ents_r)}, "ci": ci, "years": {}}
    for y in YEARS:
        ay, ry = by_year(ents_a, y), by_year(ents_r, y)
        res["years"][y] = {"lab_a": _mean(ay)["lab"], "lab_r": _mean(ry)["lab"], "delta": _adj(ay, ry)}
    return res


def r_stats(ents):
    xs = sorted(float(r[J_R]) for r in ents.values() if r[J_R] is not None)
    if not xs:
        return {"n_r": 0, "mean": None, "median": None}
    return {"n_r": len(xs), "mean": round(sum(xs) / len(xs), 4), "median": round(xs[len(xs) // 2], 4)}


def capacity_pick(ents_arm, ents_cur):
    """§④ وصفًا: كلَّ جلسةٍ أوّلُ n_CUR(D) من إدخالات الذراع بـ`rank_key` الإنتاج (المخزَّن · الأصغرُ أوّلًا كـ`sorted`) — الصفُّ بلا مفتاحٍ آخرًا."""
    per_cur = {}
    for (_s, d) in ents_cur:
        per_cur[d] = per_cur.get(d, 0) + 1
    by_d = {}
    for (s, d), r in ents_arm.items():
        by_d.setdefault(d, []).append((s, r))
    out = {}
    for d, xs in by_d.items():
        xs.sort(key=lambda t: (t[1][J_RK] is None, t[1][J_RK] or [], t[0]))
        for s, r in xs[:per_cur.get(d, 0)]:
            out[(s, d)] = r
    return out


def timeline_units(path=TIMELINE, period=PERIOD):
    """§④ وحداتُ فيصل المؤرَّخة: (الرمز، التاريخ) فريدة بـIS_FAISAL=1 داخل الفترة."""
    import csv
    try:
        rows = list(csv.DictReader(open(path, encoding="utf-8")))
    except OSError:
        return []
    return sorted({(r["TICKER"], r["DATE"]) for r in rows if str(r.get("IS_FAISAL")) == "1" and period[0] <= (r.get("DATE") or "") <= period[1]})


def unit_admission(units, rows_by, sessions, win=WIN):
    """لكلّ وحدةٍ ولكلّ ذراع: انطلقت للرمز في الجلسات العشرين المنتهية بتاريخ الوحدة؟ · و«خارج الصفوف» إن لم يكن للرمز صفّ."""
    out = []
    for sym, d in units:
        k = bisect.bisect_right(sessions, d)
        win_days = set(sessions[max(0, k - win):k])
        rws = rows_by.get(sym)
        row = {"sym": sym, "date": d, "in_rows": bool(rws)}
        for a, ix in ARM_IX.items():
            row[a] = bool(rws) and any(r[ix] == 1 and r[J_D] in win_days for r in rws)
        out.append(row)
    return out


def analyse2(rows_by, sessions, units=None, seed=SEED, b=BOOT_B):
    E = {k: entries2(rows_by, sessions, p) for k, p in RULES2.items()}
    ns = n_sessions(sessions)
    cut = cuts_of(_as1(E["CUR"]))
    fd = {k: fire_days(rows_by, RULES2[k]) for k in ("CUR", "C9999", "CNOCAP", "CNORR")}
    cur_n, cur_fd = len(E["CUR"]), fd["CUR"]
    res = {"n_sess": ns, "cuts": cut, "counts": {k: share(_as1(v)) for k, v in E.items()},
           "per_day_entries": {k: round(len(v) / ns, 3) if ns else None for k, v in E.items()},
           "fire_days": fd, "per_day_fire": {k: round(v / ns, 3) if ns else None for k, v in fd.items()},
           "r": {k: r_stats(v) for k, v in E.items()}, "cmp": {}, "cmp_r": {}, "whole": {}, "budget": {}, "cap": {}, "v": {}}
    for arm in ("C9999", "CNOCAP", "CNORR"):
        add = E["ADD_" + arm]
        res["cmp"][arm] = compare(_as1(add), _as1(E["CUR"]), cut, seed, b)
        res["cmp_r"][arm] = compare_r(_as1_r(add), _as1_r(E["CUR"]), cut, seed, b)
        res["v"][arm] = {"p": verdict(res["cmp"][arm], ("المضافُ أدقّ", "المضافُ أقلّ دقّة")),
                         "r": verdict(res["cmp_r"][arm], ("R أعلى", "R أقلّ"))}
        w = compare(_as1(E[arm]), _as1(E["CUR"]), cut, seed, b)
        res["whole"][arm] = {"p": w["A"]["p"], "raw": w["raw"], "adj": w["adj"]["delta"], "ci": w["ci"]}
        be = round(len(E[arm]) / cur_n, 3) if cur_n else None
        bf = round(fd[arm] / cur_fd, 3) if cur_fd else None
        res["budget"][arm] = {"entries": be, "fire_days": bf, "in": (be is not None and bf is not None and max(be, bf) <= BUDGET),
                              "added_fire_pct": round((fd[arm] - cur_fd) / cur_fd, 4) if cur_fd else None}
        cp = capacity_pick(E[arm], E["CUR"])
        res["cap"][arm] = {"n": len(cp), "p": share(_as1(cp))["p"], **r_stats(cp)}
    res["units"] = unit_admission(units or [], rows_by, sessions)
    return res


def predictions2(res, audit_mismatch):
    v, bu = res["v"], res["budget"]
    u = res["units"]
    ncur = sum(1 for x in u if x["CUR"])
    return {
        "APD10": bu["C9999"]["added_fire_pct"] is not None and bu["C9999"]["added_fire_pct"] <= 0.05,
        "APD11": (bu["CNOCAP"]["added_fire_pct"] is not None and bu["C9999"]["added_fire_pct"] is not None
                  and bu["CNOCAP"]["added_fire_pct"] > bu["C9999"]["added_fire_pct"] and bu["CNOCAP"]["added_fire_pct"] <= 0.15),
        "APD12": v["C9999"]["p"] == "لا قياس",
        "APD13": v["CNOCAP"]["p"] == "لا فرق قابل للكشف",
        "APD14": v["CNORR"]["p"] == "لا قياس",
        "APD15": v["CNOCAP"]["r"] == "لا فرق قابل للكشف",
        "APD16": ncur <= 2 and all(sum(1 for x in u if x[a]) <= ncur + 2 for a in ("C9999", "CNOCAP", "CNORR")),
        "APD17": audit_mismatch == 0,
    }


def _r(x, s="+.3f"):
    return "—" if x is None else format(x, s)


def report2_lines(res, meta, preds, counts):
    cn, pe, pf, rs = res["counts"], res["per_day_entries"], res["per_day_fire"], res["r"]
    L = ["# 📱⚖️ `T-APPDIFF` الملحق 1 — النتيجة (مولَّدةٌ بـ`appdiff.py` و`APD_ADDENDUM=1` · لا رقمَ باليد)", "",
         f"**التشغيلة:** {meta.get('run')} · `{(meta.get('sha') or '')[:9]}` · الجلسات {res['n_sess']} (2023-01-03…2025-12-31) · تغطيةُ الشموع {meta.get('coverage')}", "",
         f"- الصفوفُ المقيمة {counts.get('rows')} · قِدَم {counts.get('stale')} · فجوة {counts.get('excl_gap')} · تقسيمٌ غيرُ مسوّى {counts.get('excl_split')} · "
         f"بلا وسم {counts.get('unlabeled')} · نداءاتُ الأذرع المشروطة {counts.get('arm_calls')} · "
         f"**تدقيقُ السوبرست: {counts.get('audit_rows')} صفًّا × ذراع · مخالفة {counts.get('audit_mismatch')}**", "",
         "| القاعدة | الإدخالات | إدخالٌ/جلسة | أيّامُ الظهور | ظهورٌ/جلسة | الموسوم | منفجر | الدقّة % | R متوسّط | R وسيط |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for k in RULES2:
        c, fdv = cn[k], res["fire_days"].get(k)
        L.append(f"| {k} | {c['n']} | {pe[k]} | {fdv if fdv is not None else '—'} | {pf.get(k, '—')} | {c['lab']} | {c['exp']} | "
                 f"{_p(c['p'], '.1f')} | {_r(rs[k]['mean'])} | {_r(rs[k]['median'])} |")
    L += ["", f"- خُمَيساتُ `ret5` (CUR): {res['cuts']}", "",
          "## الحاكمة — «المضاف» (L ∧ ¬CUR) مقابل CUR", "",
          "| الذراع | المقياس | n | المضاف | CUR | الفرقُ الخام | **Δ المضبوط بالزخم** [95%] | Δ لكلّ سنة (A/R) | الحكم |",
          "|---|---|---|---|---|---|---|---|---|"]
    names = {"C9999": "④ السقف 99.99", "CNOCAP": "④ بلا سقف", "CNORR": "⑤ بلا عائد/مخاطرة"}
    for arm, nm in names.items():
        for lab, c, ver, fmt, mul in (("الدقّة %", res["cmp"][arm], res["v"][arm]["p"], ".1f", 100.0),
                                      ("R", res["cmp_r"][arm], res["v"][arm]["r"], ".3f", 1.0)):
            ci = c["ci"]
            ys = " · ".join(f"{y} {_p(v['delta'], '+' + fmt, mul)} ({v['lab_a']}/{v['lab_r']})" for y, v in c["years"].items())
            L.append(f"| {nm} | {lab} | {c['A']['n']} | {_p(c['A']['p'], fmt, mul)} | {_p(c['R']['p'], fmt, mul)} | {_p(c['raw'], '+' + fmt, mul)} | "
                     f"**{_p(c['adj']['delta'], '+' + fmt, mul)}** [{_p(ci[0], '+' + fmt, mul) if ci else '—'}، {_p(ci[1], '+' + fmt, mul) if ci else '—'}] | {ys} | **{ver}** |")
    L += ["", "## وصفًا — الذراعُ كاملةً · الميزانية · وتحت سعة CURRENT بمرتّب الإنتاج", "",
          "| الذراع | دقّتُها % | Δ المضبوط مقابل CUR [95%] | ×CUR بالإدخالات | ×CUR بأيّام الظهور | يُضيف من الظهور | الميزانية 2× (بالأشدّ) | تحت سعة CUR: n · الدقّة % · R متوسّط |",
          "|---|---|---|---|---|---|---|---|"]
    for arm, nm in names.items():
        w, bu, cp = res["whole"][arm], res["budget"][arm], res["cap"][arm]
        ci = w["ci"]
        L.append(f"| {nm} | {_p(w['p'], '.1f')} | {_p(w['adj'])} [{_p(ci[0]) if ci else '—'}، {_p(ci[1]) if ci else '—'}] | {bu['entries']} | {bu['fire_days']} | "
                 f"{_p(bu['added_fire_pct'], '+.1f')}% | {'داخلها' if bu['in'] else 'خارجها'} | {cp['n']} · {_p(cp['p'], '.1f')} · {_r(cp['mean'])} |")
    L += [f"| CUR (الحاليّ) | {_p(cn['CUR']['p'], '.1f')} | — | 1.0 | 1.0 | — | — | {cn['CUR']['n']} · {_p(cn['CUR']['p'], '.1f')} · {_r(rs['CUR']['mean'])} |", "",
          "## وحداتُ فيصل المؤرَّخة داخل الفترة (`FAISAL_TIMELINE.csv` · IS_FAISAL=1 · وصفٌ بلا حكم)", "",
          "| الرمز | التاريخ | له صفوف | CUR | C9999 | CNOCAP | CNORR |", "|---|---|---|---|---|---|---|"]
    for x in res["units"]:
        L.append(f"| {x['sym']} | {x['date']} | {'نعم' if x['in_rows'] else 'خارج الصفوف'} | " + " | ".join('✅' if x[a] else '—' for a in ARM_IX) + " |")
    L += ["", "## التنبّؤات (منشورةٌ قبل الرقم)", ""]
    L += [f"- `{k}` {'✅' if v else '❌'}" for k, v in preds.items()]
    L += ["", "🔒 لا شيء يُشحَن · لا تغييرَ في أيّ عتبةٍ أو جذر · والقرارُ للمالك."]
    return L


def mode_shard2(key, shard, nshards):
    RB = _rb()
    os.environ["FAISAL_ONLY"] = "0"
    import Super_stock as S
    import pit_history as PH
    prep = RB._jload(os.path.join(OUT, "prep.json.gz"))
    cur, _piv = cfgs_of(S, RB)
    if float(cur.get("EXPLOSION_PCT")) != PCT:
        raise ValueError(f"EXPLOSION_PCT {cur.get('EXPLOSION_PCT')} ليس {PCT}")
    log(f"الملحق 1: CUR MAX_DROP_PCT={cur.get('MAX_DROP_PCT')} · MIN_RR_T1={cur.get('MIN_RR_T1')} · WATCH_MAX_FAILS={cur.get('WATCH_MAX_FAILS')}")
    RB.install_stubs(S)
    G5 = RB._gen5_ext()
    member = {}
    for d in prep["sessions"]:
        for s in prep["snapshots"].get(d[:7], []):
            member.setdefault(s, []).append(d)
    cache = {}

    def _proxy(sym, day):
        if (sym, day) not in cache:
            code, body = RB._get(RB.PROXY_URL.format(t=sym, d=day, k=key))
            try:
                cache[(sym, day)] = json.loads(body or b"{}").get("results", {}).get("share_class_shares_outstanding")
            except Exception:                                   # noqa: BLE001
                cache[(sym, day)] = None
        return cache[(sym, day)]
    syms = prep["union"][shard::nshards]
    rows_by, tot, diag = {}, {}, {}
    import time
    t0 = time.time()
    for n, sym in enumerate(syms):
        df, why = PH.polygon_daily(sym, RB.BARS_FROM, RB.BARS_TO, key)
        rows = RB._rows(df) if df is not None else []
        diag[why.split("(")[0]] = diag.get(why.split("(")[0], 0) + 1
        out, cnt = appdiff2_symbol(sym, rows, prep["splits"].get(sym), member.get(sym, []), prep["prev_of"], prep["finra"], _proxy,
                                   S, cur, G5, RB, audit=(n < AUDIT_K))
        if out:
            rows_by[sym] = out
        for k, v in cnt.items():
            tot[k] = tot.get(k, 0) + v
        if n % 25 == 0:
            log(f"shard2 {shard}: {n + 1}/{len(syms)} · {round(time.time() - t0)}s · {tot}")
    res = {"shard": shard, "nshards": nshards, "symbols": len(syms), "bars_diag": diag, "counts": tot, "addendum": 1,
           "proxy_calls": len(cache), "proxy_none": sum(1 for x in cache.values() if x is None), "rows": rows_by}
    RB._jdump(res, os.path.join(OUT, f"shard_{shard:02d}.json.gz"))
    log(f"shard2 {shard}: انتهت · رموزٌ بصفوف {len(rows_by)} · {tot} · الشموع {diag}")
    return res


def mode_assemble2(nshards):
    RB = _rb()
    import subprocess
    prep = RB._jload(os.path.join(OUT, "prep.json.gz"))
    paths = sorted(glob.glob(os.path.join(OUT, "**", "shard_*.json.gz"), recursive=True))
    shards = [s for s in (RB._jload(p) for p in paths) if s.get("addendum") == 1]
    got = sorted({s["shard"] for s in shards})
    if got != list(range(nshards)):
        log(f"⛔ شرائحُ الملحق ناقصة: {sorted(set(range(nshards)) - set(got))} — «لا قياس»")
        return 7
    rows_by, tot, diag = {}, {}, {}
    for sh in shards:
        rows_by.update(sh["rows"])
        for k, v in sh["counts"].items():
            tot[k] = tot.get(k, 0) + v
        for k, v in sh["bars_diag"].items():
            diag[k] = diag.get(k, 0) + v
    nsym = sum(diag.values())
    cov = round(diag.get("ok", 0) / nsym, 4) if nsym else 0.0
    res = analyse2(rows_by, prep["sessions"], timeline_units())
    preds = predictions2(res, tot.get("audit_mismatch", 0))
    meta = {"run": os.environ.get("GITHUB_RUN_ID"), "coverage": cov,
            "sha": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()}
    bad = cov < RB.COVERAGE_FLOOR or tot.get("audit_mismatch", 0) > 0
    if bad:
        log(f"⛔ «لا قياس» للكلّ: التغطية {cov} · مخالفاتُ السوبرست {tot.get('audit_mismatch', 0)}")
    for ln in report2_lines(res, meta, preds, tot):
        print(ln)
    print("APPDIFF2_JSON " + json.dumps({"res": res, "preds": preds, "meta": meta, "counts": tot, "bars": diag},
                                        ensure_ascii=False, default=str))
    return 7 if bad else 0


# ── الأوضاع ─────────────────────────────────────────────────────────────────────────────────────────
def mode_prep(key):
    RB = _rb()
    return RB.mode_bases_prep(key, months=MONTHS, sess_from=SESS_FROM, sess_to=SESS_TO, all_from=ALL_FROM,
                              out=os.path.join(OUT, "prep.json.gz"), tag="appdiff_prep")


def mode_shard(key, shard, nshards):
    RB = _rb()
    os.environ["FAISAL_ONLY"] = "0"
    import Super_stock as S
    import pit_history as PH
    prep = RB._jload(os.path.join(OUT, "prep.json.gz"))
    cur, piv = cfgs_of(S, RB)
    if float(cur.get("EXPLOSION_PCT")) != PCT:
        raise ValueError(f"EXPLOSION_PCT {cur.get('EXPLOSION_PCT')} ليس {PCT}")
    RB.install_stubs(S)
    G5 = RB._gen5_ext()
    member = {}
    for d in prep["sessions"]:
        for s in prep["snapshots"].get(d[:7], []):
            member.setdefault(s, []).append(d)
    cache = {}

    def _proxy(sym, day):
        if (sym, day) not in cache:
            code, body = RB._get(RB.PROXY_URL.format(t=sym, d=day, k=key))
            try:
                cache[(sym, day)] = json.loads(body or b"{}").get("results", {}).get("share_class_shares_outstanding")
            except Exception:                                   # noqa: BLE001
                cache[(sym, day)] = None
        return cache[(sym, day)]
    syms = prep["union"][shard::nshards]
    rows_by, tot, diag = {}, {}, {}
    import time
    t0 = time.time()
    for n, sym in enumerate(syms):
        df, why = PH.polygon_daily(sym, RB.BARS_FROM, RB.BARS_TO, key)
        rows = RB._rows(df) if df is not None else []
        diag[why.split("(")[0]] = diag.get(why.split("(")[0], 0) + 1
        out, cnt = appdiff_symbol(sym, rows, prep["splits"].get(sym), member.get(sym, []), prep["prev_of"], prep["finra"], _proxy,
                                  S, cur, piv, G5, RB)
        if out:
            rows_by[sym] = out
        for k, v in cnt.items():
            tot[k] = tot.get(k, 0) + v
        if n % 25 == 0:
            log(f"shard {shard}: {n + 1}/{len(syms)} · {round(time.time() - t0)}s · {tot}")
    res = {"shard": shard, "nshards": nshards, "symbols": len(syms), "bars_diag": diag, "counts": tot,
           "proxy_calls": len(cache), "proxy_none": sum(1 for x in cache.values() if x is None), "rows": rows_by}
    RB._jdump(res, os.path.join(OUT, f"shard_{shard:02d}.json.gz"))
    log(f"shard {shard}: انتهت · رموزٌ بصفوف {len(rows_by)} · {tot} · الشموع {diag}")
    return res


def mode_assemble(nshards):
    RB = _rb()
    import subprocess
    prep = RB._jload(os.path.join(OUT, "prep.json.gz"))
    paths = sorted(glob.glob(os.path.join(OUT, "**", "shard_*.json.gz"), recursive=True))
    shards = [RB._jload(p) for p in paths]
    got = sorted({s["shard"] for s in shards})
    if got != list(range(nshards)):
        log(f"⛔ شرائحُ ناقصة: {sorted(set(range(nshards)) - set(got))} — «لا قياس» (§⑤)")
        return 7
    rows_by, tot, diag = {}, {}, {}
    for sh in shards:
        rows_by.update(sh["rows"])
        for k, v in sh["counts"].items():
            tot[k] = tot.get(k, 0) + v
        for k, v in sh["bars_diag"].items():
            diag[k] = diag.get(k, 0) + v
    nsym = sum(diag.values())
    cov = round(diag.get("ok", 0) / nsym, 4) if nsym else 0.0
    res = analyse(rows_by, prep["sessions"])
    preds = predictions(res)
    meta = {"run": os.environ.get("GITHUB_RUN_ID"), "coverage": cov,
            "sha": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()}
    if cov < RB.COVERAGE_FLOOR:
        log(f"⛔ تغطيةُ الشموع {cov} دون {RB.COVERAGE_FLOOR} — «لا قياس» للكلّ (§⑤)")
    for ln in report_lines(res, meta, preds, tot):
        print(ln)
    print("APPDIFF_JSON " + json.dumps({"res": res, "preds": preds, "meta": meta, "counts": tot, "bars": diag},
                                       ensure_ascii=False, default=str))
    return 0 if cov >= RB.COVERAGE_FLOOR else 7


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("check", "prep", "shard", "assemble"), default="check")
    a = ap.parse_args(argv)
    if not contract_ok():
        log("⛔ بصمةُ العقد تغيّرت — خروج 9 (لا قياس).")
        return CONTRACT_RC
    add = os.environ.get("APD_ADDENDUM", "0") == "1"
    if add and not addendum_ok():
        log("⛔ بصمةُ الملحق 1 تغيّرت — خروج 9 (لا قياس).")
        return CONTRACT_RC
    if a.mode == "check":
        log("🔒 بصمةُ العقد ✅" + (" · والملحق 1 ✅" if add else ""))
        return 0
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key and a.mode in ("prep", "shard"):
        log("⛔ بلا مفتاح Polygon — لا قياس")
        return 3
    if a.mode == "prep":
        log(json.dumps(mode_prep(key), ensure_ascii=False))
        return 0
    if a.mode == "shard":
        (mode_shard2 if add else mode_shard)(key, int(os.environ.get("SHARD", "0")), int(os.environ.get("NSHARDS", "20")))
        return 0
    return (mode_assemble2 if add else mode_assemble)(int(os.environ.get("NSHARDS", "20")))


if __name__ == "__main__":
    sys.exit(main())
