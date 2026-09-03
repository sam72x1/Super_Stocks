# -*- coding: utf-8 -*-
"""🌙⏱️ `T-PRESESSION` — الحكمُ من الصفوف المرفوعة (العقد `presession_prereg.md`).

يقرأ `presession_rows_*.jsonl.gz` (مُخرَجَ `presession_scan.py`) ويُنفّذ §⑤ و§⑥
حرفيًّا: ترتيبٌ لكلّ قرار ⟶ `P@10`/`R@10`/`base`/`lift` ⟶ الدرجاتُ `S0`/`S1`
وشاهدا الضبط `B1`/`B2` ⟶ متانةُ `leave-one-year-out` ⟶ **حكمٌ بإحدى ثلاثٍ**:
«استوفت» · «فشلت» · «لا حكم» (مع ترتيب التراجع المقفول 10 ⟵ 30 ⟵ 60 ⟵ الجلسة).

🔒 قراءةٌ/حسابٌ فقط · بلا شبكة · بلا كتابةِ حالة · لا يستورده الإنتاج.
🔒 **ولا عتبةَ تتحرّك هنا:** كلُّ حدٍّ يُقرأ من العقد ويُطبَع مع الرقم.
"""
from __future__ import annotations

import glob
import gzip
import json
import math
import os
import sys

TRAIN_YEARS = ("2023", "2024")     # §⑤-2: المعايرةُ عليهما وحدَهما
EVAL_YEAR = "2025"                 # §⑥: الحكمُ خارج العيّنة
WINDOWS = (10, 30, 60, 0)          # 0 = الجلسةُ كاملةً (ترتيبُ التراجع المقفول)
TOPK = 10
MIN_EXPLODERS = 30                 # §⑥-⑤
LIFT_MIN, P_MIN, R_MIN = 10.0, 0.01, 0.10
L2 = 1.0
ITERS, LR = 400, 0.5


def log(m=""):
    print(m, flush=True)


def load_rows(paths):
    rows = []
    for p in paths:
        op = gzip.open if p.endswith(".gz") else open
        with op(p, "rt", encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                if r.get("wit"):          # شاهدُ الضبط لا يدخل الترتيب ولا الحكم
                    continue
                rows.append(r)
    return rows


def label_of(r, w):
    return int(r.get(f"hit80_{w}" if w else "hit80_sess") or 0)


def groups(rows):
    """قراراتٌ = (يوم، جلسة) — لكلٍّ كونُه ووسمُه."""
    g = {}
    for r in rows:
        g.setdefault((r.get("day"), r.get("slot")), []).append(r)
    return g


def _feat_vec(r, feats):
    return [float(r.get(f) or 0.0) for f in feats]


def zstats(rows, feats):
    n = max(1, len(rows))
    mu = [sum(float(r.get(f) or 0.0) for r in rows) / n for f in feats]
    sd = []
    for i, f in enumerate(feats):
        v = sum((float(r.get(f) or 0.0) - mu[i]) ** 2 for r in rows) / n
        sd.append(math.sqrt(v) or 1.0)
    return mu, sd


def fit_logistic(rows, feats, w, mu, sd, iters=ITERS, lr=LR, l2=L2):
    """انحدارٌ لوجستيٌّ بتنظيم L2 — نزولٌ حتميّ (بلا عشوائيةٍ ولا بذرة)."""
    X = [[(v - mu[i]) / sd[i] for i, v in enumerate(_feat_vec(r, feats))] for r in rows]
    y = [label_of(r, w) for r in rows]
    n, d = len(X), len(feats)
    if not n:
        return [0.0] * d, 0.0
    b, b0 = [0.0] * d, 0.0
    for _ in range(iters):
        gb, g0 = [0.0] * d, 0.0
        for xi, yi in zip(X, y):
            z = b0 + sum(b[j] * xi[j] for j in range(d))
            p = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))
            e = p - yi
            g0 += e
            for j in range(d):
                gb[j] += e * xi[j]
        b0 -= lr * g0 / n
        for j in range(d):
            b[j] -= lr * (gb[j] / n + l2 * b[j] / n)
    return b, b0


def score_rows(rows, feats, mu, sd, b, b0):
    for r in rows:
        x = [(v - mu[i]) / sd[i] for i, v in enumerate(_feat_vec(r, feats))]
        r["_s1"] = b0 + sum(b[j] * x[j] for j in range(len(feats)))
    return rows


def eval_key(gs, key, w, asc=False, k=TOPK):
    """`P@10` · `R@10` · `base` على مجموعةِ قرارات."""
    hits = taken = expl = uni = 0
    for _, rs in sorted(gs.items()):
        cand = [r for r in rs if r.get(key) is not None]
        if not cand:
            continue
        cand.sort(key=lambda r: ((r[key] if asc else -r[key]), r.get("sym") or ""))
        top = cand[:k]
        hits += sum(label_of(r, w) for r in top)
        taken += len(top)
        expl += sum(label_of(r, w) for r in rs)
        uni += len(rs)
    p = (hits / taken) if taken else 0.0
    base = (expl / uni) if uni else 0.0
    rec = (hits / expl) if expl else 0.0
    return {"p": p, "r": rec, "base": base, "lift": (p / base) if base else 0.0,
            "hits": hits, "taken": taken, "expl": expl, "uni": uni}


def verdict(res_s1, res_b1, res_b2, expl, signs_ok):
    if expl < MIN_EXPLODERS:
        return "لا حكم", [f"⑤ الأرضيةُ ساقطة: {expl} منفجرًا < {MIN_EXPLODERS}"]
    bad = []
    if not (res_s1["lift"] >= LIFT_MIN and res_s1["p"] >= P_MIN):
        bad.append(f"① P@10={res_s1['p']*100:.2f}% · lift={res_s1['lift']:.1f}× "
                   f"(الحدّ {LIFT_MIN:g}× و{P_MIN*100:g}%)")
    if res_s1["r"] < R_MIN:
        bad.append(f"② R@10={res_s1['r']*100:.1f}% < {R_MIN*100:g}%")
    if not (res_s1["p"] > res_b1["p"] and res_s1["p"] > res_b2["p"]):
        bad.append(f"③ لا يتفوّق على الشاهدين (B1={res_b1['p']*100:.2f}% · "
                   f"B2={res_b2['p']*100:.2f}%)")
    if not signs_ok:
        bad.append("④ إشارةُ الميزات الثلاث الأولى تنقلب")
    return ("استوفت" if not bad else "فشلت"), bad


def main() -> int:
    paths = sorted(glob.glob("presession_rows_*.jsonl.gz")) + \
        sorted(glob.glob("presession_rows_*.jsonl"))
    if not paths:
        log("⛔ لا صفوف — نزّل artifacts أوّلًا (لا يُخمَّن رقم).")
        return 2
    rows = load_rows(paths)
    log(f"🌙 صفوف: {len(rows)} من {len(paths)} ملفًّا")
    if not rows:
        return 4
    feats = [f for f in (os.environ.get("PRESESSION_FEATS") or "").split(",") if f]
    if not feats:
        skip = {"sym", "day", "slot", "wit", "ref", "_s1"}
        feats = sorted({k for r in rows[:2000] for k, v in r.items()
                        if k not in skip and not k.startswith("hit")
                        and not k.startswith("max_") and not k.startswith("t80")
                        and isinstance(v, (int, float))})
    log(f"🔢 ميزاتُ الدرجة S1 ({len(feats)}): {', '.join(feats)}")
    tr = [r for r in rows if str(r.get("day", ""))[:4] in TRAIN_YEARS]
    ev = [r for r in rows if str(r.get("day", ""))[:4] == EVAL_YEAR]
    log(f"📚 معايرة {len(tr)} · تقييم {len(ev)}")
    if not tr or not ev:
        log("⛔ لا معايرةَ أو لا تقييم — لا حكم.")
        return 3
    out_lines = []
    for w in WINDOWS:
        wname = f"{w}د" if w else "الجلسة"
        for slot in ("AH", "PM"):
            trs = [r for r in tr if r.get("slot") == slot]
            evs = [r for r in ev if r.get("slot") == slot]
            if not trs or not evs:
                continue
            mu, sd = zstats(trs, feats)
            b, b0 = fit_logistic(trs, feats, w, mu, sd)
            score_rows(evs, feats, mu, sd, b, b0)
            gs = groups(evs)
            s1 = eval_key(gs, "_s1", w)
            b1 = eval_key(gs, "usd_day", w)
            b2 = eval_key(gs, "day_ret", w)
            order = sorted(range(len(feats)), key=lambda j: -abs(b[j]))[:3]
            top3 = [(feats[j], b[j]) for j in order]
            # ④ ثباتُ الإشارة عبر سنتَي المعايرة
            signs_ok = True
            for yr in TRAIN_YEARS:
                sub = [r for r in trs if str(r.get("day", ""))[:4] == yr]
                if len(sub) < 50:
                    continue
                m2, s2 = zstats(sub, feats)
                bb, _ = fit_logistic(sub, feats, w, m2, s2)
                for j, _c in zip(order, top3):
                    if bb[j] * b[j] < 0:
                        signs_ok = False
            v, why = verdict(s1, b1, b2, s1["expl"], signs_ok)
            line = (f"‏[{slot} · نافذة {wname}] الحكم: **{v}** · "
                    f"P@10={s1['p']*100:.2f}% · base={s1['base']*100:.3f}% · "
                    f"lift={s1['lift']:.1f}× · R@10={s1['r']*100:.1f}% · "
                    f"منفجرون={s1['expl']} · كون={s1['uni']} · "
                    f"B1={b1['p']*100:.2f}% · B2={b2['p']*100:.2f}%")
            log(line)
            for x in why:
                log("      🔴 " + x)
            log("      🔢 أقوى ثلاث: " + " · ".join(f"{n}={c:+.3f}" for n, c in top3))
            out_lines.append((w, slot, v, line))
    log("")
    log("📌 ترتيبُ التراجع المقفول: تُقرأ نافذةُ 10 أوّلًا، ولا يُقرأ حكمُ نافذةٍ "
        "أوسعَ حكمًا على الأضيق.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
