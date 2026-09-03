# -*- coding: utf-8 -*-
"""🌙⏱️ `T-PRESESSION` — الحكمُ من الصفوف المرفوعة (العقد `presession_prereg.md`).

يقرأ `presession_rows_*.jsonl.gz` (مُخرَجَ `presession_scan.py`) ويُنفّذ §⑤ و§⑥
حرفيًّا: ترتيبٌ لكلّ قرار ⟶ `P@10`/`R@10`/`base`/`lift` ⟶ الدرجةُ `S1` وشاهدا
الضبط `B1`/`B2` ⟶ ثباتُ الإشارة عبر سنتَي المعايرة ⟶ **حكمٌ بإحدى ثلاثٍ**:
«استوفت» · «فشلت» · «لا حكم» (بترتيب التراجع المقفول 10 ⟵ 30 ⟵ 60 ⟵ الجلسة).

🔒 قراءةٌ/حسابٌ فقط · بلا شبكة · بلا كتابةِ حالة · لا يستورده الإنتاج.
🔒 **ولا عتبةَ تتحرّك هنا:** كلُّ حدٍّ يُقرأ من العقد ويُطبَع مع الرقم.

🔴🔴 **عيبان قاتلان أُصلحا قبل أيّ رقم (2026-09-03) — يُدوَّنان لا يُطويان:**

**① تسريبٌ كامل.** كان اختيارُ الميزات **آليًّا** بقائمةٍ سوداء
(`not k.startswith("hit"|"max_"|"t80")`)، **ومفاتيحُ الوسم في الصفّ اسمُها
`max10`/`max30`/`max60`/`maxs` و`usd10`…`usds`** — ولا واحدٌ منها يبدأ بـ`max_`
⇒ **كانت ستدخل ميزاتٍ فيعرف النموذجُ قمّةَ النافذة التي يتنبّأ بها**، فيخرج
`P@10` خياليًّا. ✅ العلاج **قائمةٌ بيضاء من المصدر الواحد** `presession_feats`
(‏`FEATS_DESC + FEATS_ASC` المثبَّتة في العقد قبل الأرقام) — **والقائمةُ السوداء
تنسى، والبيضاءُ يستحيل عليها أن تنسى** (درسُ «عدّادُ الأسباب يُكتَب مُكمِّلًا»).

**② وسمُ الجلسة ميّت.** `label_of` كان يقرأ `hit80_sess` **والصفُّ يكتب
`hit80_s`** ⇒ نافذةُ الجلسة كانت تُقرأ **صفرًا دائمًا** (صنفُ «المفتاح
المتخيَّل»). ✅ وُحِّد على `hit80_s`.

**③ وعطبٌ تشغيليّ:** النسخةُ الأولى حمّلت 4 ملايين **قاموس** ودرّبت بحلقةٍ
بايثونية خالصة ⇒ **قتل الرنر** (‏`shutdown signal` في التشغيلة `33729925821`).
✅ الآن انسيابٌ إلى مصفوفات `numpy` وتدريبٌ متّجه.
"""
from __future__ import annotations

import glob
import gzip
import json
import os
import sys

import numpy as np

import presession_feats as PF                 # 🔒 المصدرُ الواحد للميزات

TRAIN_YEARS = ("2023", "2024")     # §⑤-2: المعايرةُ عليهما وحدَهما
EVAL_YEAR = "2025"                 # §⑥: الحكمُ خارج العيّنة
WINDOWS = (10, 30, 60, 0)          # 0 = الجلسةُ كاملةً (ترتيبُ التراجع المقفول)
TOPK = PF.TOPK
MIN_EXPLODERS = 30                 # §⑥-⑤
LIFT_MIN, P_MIN, R_MIN = 10.0, 0.01, 0.10
L2 = 1.0
ITERS, LR = 400, 0.5

# 🔒 **قائمةٌ بيضاء لا سوداء** — من العقد حصرًا. أيُّ مفتاحٍ خارجها لا يدخل
#    النموذجَ مهما كان اسمُه، فيستحيل أن يتسرّب وسمٌ إلى الميزات.
FEATS = list(PF.FEATS_DESC) + list(PF.FEATS_ASC)
LABEL_KEYS = {10: "hit80_10", 30: "hit80_30", 60: "hit80_60", 0: "hit80_s"}


def log(m=""):
    print(m, flush=True)


def load_cols(paths, feats):
    """انسيابٌ إلى أعمدةٍ رقميّة — بلا الاحتفاظ بالقواميس (‏4 ملايين صفّ)."""
    F = len(feats)
    xs = [[] for _ in range(F)]
    ys = {w: [] for w in WINDOWS}
    gid, syms, years, slots = [], [], [], []
    gmap, smap = {}, {}
    n_wit = 0
    for p in paths:
        op = gzip.open if p.endswith(".gz") else open
        with op(p, "rt", encoding="utf-8") as fh:
            for ln in fh:
                if not ln.strip():
                    continue
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                if r.get(PF.ROW_WIT):   # شاهدُ الضبط خارج الترتيب والحكم
                    n_wit += 1
                    continue
                # 🔒 مفاتيحُ الهويّة من `PF` لا مكتوبةً هنا — العطبُ الذي تخطّى
                #    الخلايا الثمانَ صامتًا كان `slot` مقابل `sess`.
                day, slot = r.get(PF.ROW_DAY), r.get(PF.ROW_SESS)
                k = (day, slot)
                if k not in gmap:
                    gmap[k] = len(gmap)
                gid.append(gmap[k])
                sym = r.get(PF.ROW_SYM) or ""
                if sym not in smap:
                    smap[sym] = len(smap)
                syms.append(smap[sym])
                years.append(str(day or "")[:4])
                slots.append(slot)
                for i, f in enumerate(feats):
                    v = r.get(f)
                    xs[i].append(float(v) if isinstance(v, (int, float)) else np.nan)
                for w in WINDOWS:
                    ys[w].append(int(r.get(LABEL_KEYS[w]) or 0))
    X = np.array(xs, dtype=np.float64).T if xs else np.zeros((0, F))
    # 🔒 رتبةُ الرمز **أبجديّةٌ** لا رتبةُ الظهور — كسرُ التعادل يطابق
    #    `PF.order_rows` (‏`r["sym"]`) حرفيًّا.
    order = {s: i for i, s in enumerate(sorted(smap))}
    sym_ord = np.array([order[s] for s in sorted(smap, key=lambda z: smap[z])],
                       dtype=np.int64)
    return {"X": X, "y": {w: np.array(v, dtype=np.int8) for w, v in ys.items()},
            "gid": np.array(gid, dtype=np.int64),
            "sym": sym_ord[np.array(syms, dtype=np.int64)] if syms else np.zeros(0, int),
            "year": np.array(years), "slot": np.array(slots), "wit": n_wit}


def zfit(X):
    mu = np.nanmean(X, axis=0)
    mu = np.where(np.isfinite(mu), mu, 0.0)
    sd = np.nanstd(X, axis=0)
    sd = np.where(np.isfinite(sd) & (sd > 0), sd, 1.0)
    return mu, sd


def zapply(X, mu, sd):
    Z = (np.nan_to_num(X, nan=0.0) - mu) / sd
    return np.clip(Z, -8.0, 8.0)


def fit_logistic(Z, y, iters=ITERS, lr=LR, l2=L2):
    """انحدارٌ لوجستيٌّ بتنظيم L2 — نزولٌ حتميّ (بلا عشوائيةٍ ولا بذرة)."""
    n, d = Z.shape
    if not n:
        return np.zeros(d), 0.0
    b, b0 = np.zeros(d), 0.0
    yv = y.astype(np.float64)
    for _ in range(iters):
        z = Z @ b + b0
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -30.0, 30.0)))
        e = p - yv
        b0 -= lr * e.mean()
        b -= lr * ((Z.T @ e) / n + l2 * b / n)
    return b, b0


def eval_scores(score, gid, sym, y, k=TOPK, asc=False):
    """`P@10` · `R@10` · `base` — الترتيبُ داخل كلّ قرارٍ وكسرُ التعادل بالرمز."""
    if score.size == 0:
        return {"p": 0.0, "r": 0.0, "base": 0.0, "lift": 0.0,
                "hits": 0, "taken": 0, "expl": 0, "uni": 0}
    s = score if asc else -score
    idx = np.lexsort((sym, s, gid))          # gid ⟶ الدرجة ⟶ الرمز
    g = gid[idx]
    rank = np.arange(len(g)) - np.searchsorted(g, g, side="left")
    top = idx[rank < k]
    hits = int(y[top].sum())
    taken = int(top.size)
    expl = int(y.sum())
    uni = int(y.size)
    p = (hits / taken) if taken else 0.0
    base = (expl / uni) if uni else 0.0
    return {"p": p, "r": (hits / expl) if expl else 0.0, "base": base,
            "lift": (p / base) if base else 0.0,
            "hits": hits, "taken": taken, "expl": expl, "uni": uni}


# 🔴🔴 **تصحيحُ المالك 2026-09-03: النافذةُ التي يريدها هي الجلسةُ كاملةً.**
#    «‏10 دقائق» في أمره **وقتُ وصول الإشعار قبل بدء الجلسة**، لا مدّةُ التوقّع —
#    وأنا قرأتُها مدّةَ توقّعٍ فكتبتُ العقدَ على نافذة العشر دقائق. ✅ **والنافذةُ
#    الكاملة مقيسةٌ في الجدول نفسِه منذ أوّل تشغيلة** (‏`hit80_s`) فلا انتقاءَ بعديّ.
#    ⇒ هذي الجدولةُ تُخرج **الترتيبَ بمفتاحٍ منفردٍ لكلّ نافذة** كي يُختار مفتاحُ
#    الجلسة **بالقاعدة نفسِها: من سنتَي المعايرة وحدهما**.
S0_WINDOWS = (10, 0)


def s0_table(d, feats, mask, w, k=TOPK):
    """‏`P@10` لكلّ ميزةٍ منفردةً على شريحةٍ — بالمصدر الواحد وبمقياس `eval_scores`
    نفسِه (لا مقياسَ ثانٍ يتفرّق). يُرجع قائمةً مرتَّبةً تنازليًّا."""
    if not mask.any():
        return []
    gid, sym, y = d["gid"][mask], d["sym"][mask], d["y"][w][mask]
    asc_set = set(PF.FEATS_ASC)
    out = []
    for i, f in enumerate(feats):
        v = np.nan_to_num(d["X"][mask][:, i], nan=(np.inf if f in asc_set else -np.inf))
        r = eval_scores(v, gid, sym, y, k=k, asc=(f in asc_set))
        out.append((f, r))
    out.sort(key=lambda kv: (-kv[1]["p"], kv[0]))
    return out


def verdict(res_s1, res_b1, res_b2, expl, signs_ok):
    if expl < MIN_EXPLODERS:
        return "لا حكم", [f"⑤ الأرضيةُ ساقطة: {expl} منفجرًا دون {MIN_EXPLODERS}"]
    bad = []
    if not (res_s1["lift"] >= LIFT_MIN and res_s1["p"] >= P_MIN):
        bad.append(f"① P@10={res_s1['p']*100:.2f}% · lift={res_s1['lift']:.1f}× "
                   f"(الحدّ {LIFT_MIN:g}× و{P_MIN*100:g}%)")
    if res_s1["r"] < R_MIN:
        bad.append(f"② R@10={res_s1['r']*100:.1f}% دون {R_MIN*100:g}%")
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
    feats = [f for f in (os.environ.get("PRESESSION_FEATS") or "").split(",") if f]
    bad_env = [f for f in feats if f not in FEATS]
    if bad_env:
        log(f"⛔ ميزةٌ خارج قائمة العقد البيضاء: {bad_env} — لا حكم.")
        return 3
    feats = feats or FEATS
    log(f"🔢 ميزاتُ `S1` ({len(feats)}) — **قائمةٌ بيضاء من العقد**: {', '.join(feats)}")
    d = load_cols(paths, feats)
    n = d["X"].shape[0]
    log(f"🌙 صفوف: {n:,} من {len(paths)} ملفًّا · شاهدُ الضبط المستبعَد {d['wit']:,}")
    if not n:
        return 4
    for w in WINDOWS:
        log(f"   وسمُ {w or 'الجلسة'}: منفجرون {int(d['y'][w].sum()):,}")
    tr_m = np.isin(d["year"], TRAIN_YEARS)
    ev_m = d["year"] == EVAL_YEAR
    log(f"📚 معايرة {int(tr_m.sum()):,} · تقييم {int(ev_m.sum()):,}")
    if not tr_m.any() or not ev_m.any():
        log("⛔ لا معايرةَ أو لا تقييم — لا حكم.")
        return 3
    i_b1 = feats.index("usd_day") if "usd_day" in feats else None
    i_b2 = feats.index("day_ret") if "day_ret" in feats else None
    for w in WINDOWS:
        wname = f"{w}د" if w else "الجلسة"
        for slot in ("AH", "PM"):
            tm = tr_m & (d["slot"] == slot)
            em = ev_m & (d["slot"] == slot)
            if not tm.any() or not em.any():
                continue
            Xtr, Xev = d["X"][tm], d["X"][em]
            mu, sd = zfit(Xtr)
            Ztr, Zev = zapply(Xtr, mu, sd), zapply(Xev, mu, sd)
            b, b0 = fit_logistic(Ztr, d["y"][w][tm])
            sc = Zev @ b + b0
            gid, sym, y = d["gid"][em], d["sym"][em], d["y"][w][em]
            s1 = eval_scores(sc, gid, sym, y)
            b1 = eval_scores(np.nan_to_num(Xev[:, i_b1]), gid, sym, y) if i_b1 is not None \
                else {"p": 0.0}
            b2 = eval_scores(np.nan_to_num(Xev[:, i_b2]), gid, sym, y) if i_b2 is not None \
                else {"p": 0.0}
            order = list(np.argsort(-np.abs(b))[:3])
            top3 = [(feats[j], float(b[j])) for j in order]
            signs_ok = True
            for yr in TRAIN_YEARS:
                sm = (d["year"] == yr) & (d["slot"] == slot)
                if int(sm.sum()) < 50:
                    continue
                m2, s2 = zfit(d["X"][sm])
                bb, _ = fit_logistic(zapply(d["X"][sm], m2, s2), d["y"][w][sm])
                for j in order:
                    if bb[j] * b[j] < 0:
                        signs_ok = False
            v, why = verdict(s1, b1, b2, s1["expl"], signs_ok)
            log(f"‏[{slot} · نافذة {wname}] الحكم: **{v}** · "
                f"P@10={s1['p']*100:.2f}% · base={s1['base']*100:.3f}% · "
                f"lift={s1['lift']:.1f}× · R@10={s1['r']*100:.1f}% · "
                f"إصابات={s1['hits']} · منفجرون={s1['expl']} · كون={s1['uni']:,} · "
                f"B1={b1['p']*100:.2f}% · B2={b2['p']*100:.2f}%")
            for x in why:
                log("      🔴 " + x)
            log("      🔢 أقوى ثلاث: " + " · ".join(f"{nm}={c:+.3f}" for nm, c in top3)
                + f" · ثباتُ الإشارة: {'✅' if signs_ok else '🔴'}")
    # ── `S0` — الترتيبُ بمفتاحٍ منفردٍ لكلّ نافذةٍ وسنة (اختيارُ مفتاح الحيّ) ──
    log("")
    log("=" * 78)
    log("🔑 `S0` — الترتيبُ بمفتاحٍ منفردٍ (لا نموذج) · **يُختار من سنتَي المعايرة "
        "وحدهما** · سنةُ التقييم تُطبَع للقراءة لا للاختيار")
    log("=" * 78)
    for w in S0_WINDOWS:
        wname = f"{w}د" if w else "الجلسة"
        for slot in ("AH", "PM"):
            for yr in list(TRAIN_YEARS) + [EVAL_YEAR]:
                m = (d["year"] == yr) & (d["slot"] == slot)
                tab = s0_table(d, feats, m, w)
                if not tab:
                    continue
                base = tab[0][1]["base"]
                tag = "معايرة" if yr in TRAIN_YEARS else "تقييم (خارج العيّنة)"
                log(f"\n【{slot} · نافذة {wname} · {yr} — {tag}】 كون={tab[0][1]['uni']:,}"
                    f" · منفجرون={tab[0][1]['expl']} · base={base*100:.3f}%")
                for f, r in tab[:8]:
                    bt = next((b for b, ff in PF.BASELINES.items() if ff == f), "")
                    log(f"      {f:14} {'(' + bt + ')' if bt else '':5} إصابات "
                        f"{r['hits']:4} من {r['taken']:6} ⇒ P@10 {r['p']*100:.3f}% · "
                        f"lift {r['lift']:5.1f}× · R@10 {r['r']*100:.1f}%")
    log("")
    log("📌 ترتيبُ التراجع المقفول: تُقرأ نافذةُ 10 أوّلًا، ولا يُقرأ حكمُ نافذةٍ "
        "أوسعَ حكمًا على الأضيق. **والنافذةُ التي يريدها المالك هي الجلسةُ كاملةً "
        "(تصحيحُه 2026-09-03) — وحكمُها مطبوعٌ أعلاه ولم يُنتقَ بعد الأرقام.**")
    return 0


if __name__ == "__main__":
    sys.exit(main())
