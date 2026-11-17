"""📐 نواةُ بروتوكول الفلتر المشترك (`FILTER_PROTOCOL.md`) — قراءةٌ فقط · صفرُ نداءٍ خارجيّ.

سجلّاتُ شرائح `T-BASKET` (`43955351411`) ⟵ إدخالاتُ CURRENT بفائضها على ضابط الزخم ⟵ (أ) مع الإشارة و(ب) مع مقابل بدون · بالخليّتين `O0`/`O50`
والسنوات 2023-2025 كلٍّ وحدَها · والحكمُ بالأضعف. البوتستراب `basket.boot_mean` **بالاسم**.
"""
import glob
import gzip
import hashlib
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PROTOCOL = os.path.join(HERE, "FILTER_PROTOCOL.md")
BASKET_RUN = 43955351411
NSHARDS = 40
ARMS = ("O0", "O50")
YEARS = ("2023", "2024", "2025")
MIN_N = 30
COV_FLOOR = 0.80
LAST_N = 60
WIN_END = "2026-11-13"


def _basket():
    spec = importlib.util.spec_from_file_location("basket_fc", os.path.join(ROOT, "fm_forensics", "basket", "basket.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha_of(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def load_shards(d_in):
    """⟵ (السجلّات، عددُ الشرائح) من `basket_shard_*.json.gz` تحت `d_in`."""
    paths = sorted(glob.glob(os.path.join(d_in, "**", "basket_shard_*.json.gz"), recursive=True))
    recs = []
    for p in paths:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            recs.extend(json.load(fh).get("recs") or [])
    return recs, len(paths)


def current(recs):
    return [r for r in recs if "CURRENT" in (r.get("lists") or [])]


def excess(r, arm):
    """(نقيّة) فائضُ الإدخال على متوسّط ضوابطه في الذراع · None إن غابت نتيجتُه أو ضوابطُه."""
    res = (r.get("res") or {}).get(arm)
    if not res or res.get("r") is None:
        return None
    cr = [c.get(arm) for c in (r.get("ctrl") or []) if c and c.get(arm) is not None]
    if not cr:
        return None
    return float(res["r"]) - sum(cr) / len(cr)


def boot_diff(a_pairs, b_pairs, boot_mean_fn=None, seed=None, b=10_000):
    """(أ − ب) بفاصل 95% ببوتستراب عنقوديّ بالرمز داخل كلّ مجموعةٍ مستقلًّا (pairs = [(رمز، قيمة)])."""
    import numpy as np
    if seed is None:
        seed = _basket().SEED

    def _draws(pairs, sd):
        per = {}
        for s, v in pairs:
            p = per.setdefault(s, [0.0, 0])
            p[0] += v
            p[1] += 1
        sums = np.array([per[s][0] for s in sorted(per)])
        cnts = np.array([per[s][1] for s in sorted(per)])
        rng = np.random.default_rng(sd)
        idx = rng.integers(0, len(sums), size=(b, len(sums)))
        return sums[idx].sum(axis=1) / cnts[idx].sum(axis=1)
    if not a_pairs or not b_pairs:
        return None
    d = np.sort(_draws(a_pairs, seed) - _draws(b_pairs, seed + 1))
    return [round(float(d[int(0.025 * b)]), 6), round(float(d[min(b - 1, int(0.975 * b))]), 6)]


def _mean(xs):
    return round(sum(xs) / len(xs), 6) if xs else None


def cell(rows, sig, arm, boot_mean_fn):
    """rows = إدخالاتُ CURRENT لسنةٍ واحدة · sig = {(رمز، يوم): True/False/None} ⟵ إحصاءاتُ الخليّة."""
    with_r = [r for r in rows if (r.get("res") or {}).get(arm)]
    known = [r for r in with_r if sig.get((r["sym"], r["d"])) is not None]
    cov = round(len(known) / len(with_r), 4) if with_r else None
    t = [(r["sym"], excess(r, arm)) for r in known if sig[(r["sym"], r["d"])] is True]
    f = [(r["sym"], excess(r, arm)) for r in known if sig[(r["sym"], r["d"])] is False]
    t = [x for x in t if x[1] is not None]
    f = [x for x in f if x[1] is not None]
    return {"n_all": len(with_r), "coverage": cov, "n_true": len(t), "n_false": len(f),
            "a_mean": _mean([v for _s, v in t]), "a_ci": boot_mean_fn(t) if len(t) >= 2 else None,
            "b_mean": (round(_mean([v for _s, v in t]) - _mean([v for _s, v in f]), 6) if t and f else None),
            "b_ci": boot_diff(t, f) if len(t) >= 2 and len(f) >= 2 else None,
            "raw_true": _mean([float(r["res"][arm]["r"]) for r in known if sig[(r["sym"], r["d"])] is True]),
            "raw_false": _mean([float(r["res"][arm]["r"]) for r in known if sig[(r["sym"], r["d"])] is False]),
            "none": len(with_r) - len(known)}


def verdict(cells):
    """cells[arm][year] ⟵ «✅ تعبر» · «❌ لا تعبر» · «لا قياس» (§③ بالأضعف)."""
    for arm in ARMS:
        for y in YEARS:
            c = (cells.get(arm) or {}).get(y) or {}
            if c.get("n_true", 0) < MIN_N or c.get("n_false", 0) < MIN_N or (c.get("coverage") or 0) < COV_FLOOR:
                return "لا قياس"
    ok = all((cells[a][y].get("a_ci") or [0])[0] > 0 and (cells[a][y].get("b_ci") or [0])[0] > 0 for a in ARMS for y in YEARS)
    return "✅ تعبر" if ok else "❌ لا تعبر"


def last_sessions(allsess, n=LAST_N, end=WIN_END):
    s = [d for d in allsess if d <= end]
    return set(s[-n:])


def evaluate(recs, sig, last_set=None):
    """⟵ {cells, verdict, pooled, last60} على إدخالات CURRENT."""
    B = _basket()
    cur = current(recs)
    cells = {a: {y: cell([r for r in cur if r["y"] == y], sig, a, B.boot_mean) for y in YEARS} for a in ARMS}
    pooled = {a: cell([r for r in cur if r["y"] in YEARS], sig, a, B.boot_mean) for a in ARMS}
    last = {a: cell([r for r in cur if last_set and r["d"] in last_set], sig, a, B.boot_mean) for a in ARMS} if last_set else None
    return {"cells": cells, "verdict": verdict(cells), "pooled": pooled, "last60": last}


def pct(x):
    return "—" if x is None else f"{x * 100:+.1f}%"


def cov_txt(x):
    return "—" if x is None else f"{x * 100:.1f}%"


def ci_txt(ci):
    return "—" if not ci else f"[{ci[0] * 100:+.1f}، {ci[1] * 100:+.1f}]"


def report_lines(ev, title):
    L = [f"## {title} — الحكم: **{ev['verdict']}**", "",
         "| الخليّة | السنة | n الكلّ | التغطية | n مع | n بدون | (أ) مع − الزخم | فاصل (أ) | (ب) مع − بدون | فاصل (ب) | r الخام مع/بدون |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for a in ARMS:
        rows = [(y, ev["cells"][a][y]) for y in YEARS] + [("مجمَّع", ev["pooled"][a])]
        if ev.get("last60"):
            rows.append(("آخر 60 جلسة", ev["last60"][a]))
        for y, c in rows:
            L.append(f"| {a} | {y} | {c['n_all']} | {cov_txt(c['coverage'])} | {c['n_true']} | {c['n_false']} | "
                     f"{pct(c['a_mean'])} | {ci_txt(c['a_ci'])} | {pct(c['b_mean'])} | {ci_txt(c['b_ci'])} | {pct(c['raw_true'])} / {pct(c['raw_false'])} |")
    return L


def level_value(x):
    """`Super_stock.tested_level` يُرجع {"level", "touches"} أو None ⟵ السعرُ float أو None (عطلٌ مُثبَت 2026-11-17: `float(dict)`)."""
    if isinstance(x, dict):
        x = x.get("level")
    try:
        v = float(x) if x is not None else None
    except (TypeError, ValueError):
        return None
    return v if v and v > 0 else None
