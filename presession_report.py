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
import math
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
MAX_KEYS = {10: "max10", 30: "max30", 60: "max60", 0: "maxs"}


def log(m=""):
    print(m, flush=True)


def load_cols(paths, feats):
    """انسيابٌ إلى أعمدةٍ رقميّة — بلا الاحتفاظ بالقواميس (‏4 ملايين صفّ)."""
    F = len(feats)
    xs = [[] for _ in range(F)]
    ys = {w: [] for w in WINDOWS}
    gid, syms, years, slots = [], [], [], []
    # 🔴 **للتسمية لا للحكم:** أعلى نسبةٍ في النافذة (`maxs`/`max10`) تُحمَل
    #    `float32` كي تُطبَع أسماءُ الإصابات بنسبها — ولا تدخل درجةً ولا ترتيبًا.
    mxs = {w: [] for w in WINDOWS}
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
                    mv = r.get(MAX_KEYS[w])
                    mxs[w].append(float(mv) if isinstance(mv, (int, float)) else np.nan)
    X = np.array(xs, dtype=np.float64).T if xs else np.zeros((0, F))
    # 🔒 رتبةُ الرمز **أبجديّةٌ** لا رتبةُ الظهور — كسرُ التعادل يطابق
    #    `PF.order_rows` (‏`r["sym"]`) حرفيًّا.
    order = {s: i for i, s in enumerate(sorted(smap))}
    sym_ord = np.array([order[s] for s in sorted(smap, key=lambda z: smap[z])],
                       dtype=np.int64)
    # 🔒 `names[d["sym"][i]]` = رمزُ الصفّ (‏`sym_ord` رتبةٌ أبجديّة) · و`gkey[gid]`
    #    = (يومٌ، جلسة) — كلاهما **للتسمية**، وصفرُ أثرٍ على درجةٍ أو ترتيبٍ أو حكم.
    gkey = [k for k, _ in sorted(gmap.items(), key=lambda kv: kv[1])]
    return {"X": X, "y": {w: np.array(v, dtype=np.int8) for w, v in ys.items()},
            "mx": {w: np.array(v, dtype=np.float32) for w, v in mxs.items()},
            "gid": np.array(gid, dtype=np.int64),
            "sym": sym_ord[np.array(syms, dtype=np.int64)] if syms else np.zeros(0, int),
            "names": np.array(sorted(smap)) if smap else np.zeros(0, dtype="<U1"),
            "gkey": gkey,
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


def group_ranks(score, gid, sym, asc=False):
    """رتبةُ **كلّ صفٍّ داخل قراره** (‏0 = الأوّل) — **المصدرُ الواحد للترتيب**.

    🔒 يقرؤه `topk_idx` (ومنه الحكمُ والتسمية) و`miss_report` معًا، فيستحيل أن
    يُحكَم بترتيبٍ ويُشخَّص فوتٌ بترتيبٍ آخر. كسرُ التعادل بالرمز (يطابق
    `PF.order_rows`)، و`lexsort` **هنا وحدَها** في الوحدة كلِّها.
    """
    s = score if asc else -score
    idx = np.lexsort((sym, s, gid))          # gid ⟶ الدرجة ⟶ الرمز
    g = gid[idx]
    r = np.arange(len(g)) - np.searchsorted(g, g, side="left")
    out = np.empty(len(g), dtype=np.int64)
    out[idx] = r
    return out


def topk_idx(score, gid, sym, k=TOPK, asc=False):
    """فهارسُ أعلى `k` **داخل كلّ قرار** — يقرؤه الحكمُ (`eval_scores`) وتسميةُ
    الإصابات (`hit_names`) معًا، وكلاهما من `group_ranks` نفسِها."""
    if score.size == 0:
        return np.zeros(0, dtype=np.int64)
    return np.where(group_ranks(score, gid, sym, asc=asc) < k)[0]


def eval_scores(score, gid, sym, y, k=TOPK, asc=False):
    """`P@10` · `R@10` · `base` — الترتيبُ داخل كلّ قرارٍ وكسرُ التعادل بالرمز."""
    if score.size == 0:
        return {"p": 0.0, "r": 0.0, "base": 0.0, "lift": 0.0,
                "hits": 0, "taken": 0, "expl": 0, "uni": 0}
    top = topk_idx(score, gid, sym, k=k, asc=asc)
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


def hit_names(d, score, mask, w, k=TOPK, asc=False):
    """**أسماءُ الإصابات**: مَن كانت ستصله القائمةُ (أعلى `k` في قراره) وانفجر
    فعلًا (‏`+80%` بالوسم) — سؤالُ المالك «وش الأسهم اللي كانت بتوصلني وفعلًا
    تنفجر؟». تُبنى من **`topk_idx` نفسِه** الذي يحكم به `eval_scores` ⇒ عددُها
    يساوي `hits` بالبناء (فحصُ اتّساقٍ مجّانيّ)، وهي **تسميةٌ لا حكم**."""
    gid, sym, y = d["gid"][mask], d["sym"][mask], d["y"][w][mask]
    mx = d["mx"][w][mask]
    top = topk_idx(score, gid, sym, k=k, asc=asc)
    out = []
    for i in top:
        if not y[i]:
            continue
        day, slot = d["gkey"][int(gid[i])]
        out.append({"day": day, "slot": slot, "sym": str(d["names"][int(sym[i])]),
                    "max": (None if not np.isfinite(mx[i]) else float(mx[i]))})
    out.sort(key=lambda r: (-(r["max"] or 0.0), r["day"], r["sym"]))
    return out


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


def miss_report(d, feats, code, slot, w, key, k=TOPK, best_n=5):
    """**«ليه فات؟»** — تشخيصُ رمزٍ بعينه يومًا يومًا داخل قرارِ ذلك اليوم.

    لكلّ يومٍ للرمز في هذي الجلسة: هل انفجر ‏+80%؟ · **رتبتُه بالمفتاح المشحون**
    وكمُ كونُ القرار · قيمةُ المفتاح (‏أو **معدومة** ⇒ يُدفَع إلى الذيل بالبناء) ·
    وأفضلُ `best_n` رتبٍ عبر ميزات العقد كلِّها.

    🔒 **وصفٌ لا اختيار:** يُقرأ تشخيصًا لسهمٍ بعينه — **ولا يُبدَّل به مفتاحُ
    ترتيبٍ ولا حدّ**، فاختيارُ مفتاحٍ بعد رؤية نتيجة سهمٍ هو `p-hacking` بحرفه.
    والرتبُ من `group_ranks` **نفسِها** التي يحكم بها `eval_scores`.
    """
    asc_set = set(PF.FEATS_ASC)
    ki = feats.index(key)
    sm = (d["slot"] == slot) & (d["sym"] == code)
    # 🔒 فهرسةٌ مرّةً واحدة: مسحُ الكونِ كلِّه لكلّ يومٍ كان يقرأ ملايينَ الصفوف
    #    مرّاتٍ بعدد أيام الرمز — والنتيجةُ نفسُها بترتيبٍ مستقرّ.
    sl = np.where(d["slot"] == slot)[0]
    gs = d["gid"][sl]
    o = np.argsort(gs, kind="stable")
    sl, gs = sl[o], gs[o]
    out = []
    for g in sorted({int(x) for x in d["gid"][sm]}):
        lo = int(np.searchsorted(gs, g, side="left"))
        hi = int(np.searchsorted(gs, g, side="right"))
        rows = sl[lo:hi]
        tgt = np.where(d["sym"][rows] == code)[0]
        if not tgt.size:
            continue
        t, gsym, ggid = int(tgt[0]), d["sym"][rows], d["gid"][rows]
        Xr = d["X"][rows]
        ranks = []
        for j, f in enumerate(feats):
            a = f in asc_set
            v = np.nan_to_num(Xr[:, j], nan=(np.inf if a else -np.inf))
            ranks.append((int(group_ranks(v, ggid, gsym, asc=a)[t]) + 1, f))
        kv = float(Xr[t, ki])
        mx = d["mx"][w][rows][t]
        day, _ = d["gkey"][g]
        out.append({
            "day": day, "uni": int(rows.size),
            "hit": bool(d["y"][w][rows][t]),
            "rank": next(r for r, f in ranks if f == key),
            "val": (None if not np.isfinite(kv) else kv),
            "max": (None if not np.isfinite(mx) else float(mx)),
            "in_list": next(r for r, f in ranks if f == key) <= k,
            "best": sorted(ranks)[:best_n],
            # 🔴 **كلُّ** مفتاحٍ رتبتُه داخل العشرة — لا أفضلُ `best_n` فقط:
            #    القصُّ هنا كان سيُسقط مفاتيحَ ملتقِطةً من عدّاد §الوصفيّ.
            "in_top": sorted(r for r, f in ranks if r <= k),
            "top_keys": sorted((r, f) for r, f in ranks if r <= k),
        })
    out.sort(key=lambda r: r["day"])
    return out


def miss_key_tally(rows, feats, k=TOPK):
    """**وصفيٌّ صرف:** كم يومَ انفجارٍ كان كلُّ مفتاحٍ سيلتقطه (رتبةٌ ≤ `k`).

    🔴 **لا يُختار منه مفتاح**: هو عدٌّ على **سهمٍ واحدٍ بعد رؤية نتيجته** —
    وترقيتُه قرارًا هي `p-hacking` بحرفه. يُنشَر تشخيصًا ويُوسَم كذلك.
    """
    ex = [r for r in rows if r["hit"]]
    tally = {f: 0 for f in feats}
    for r in ex:
        for rank, f in r["top_keys"]:     # لا `best` — كانت مقصوصةً بـ`best_n`
            if rank <= k:
                tally[f] += 1
    return len(ex), sorted(((n, f) for f, n in tally.items() if n),
                           key=lambda kv: (-kv[0], kv[1]))


# ── 📦 `T-TOPK` — «كم اسمًا يصل المالك؟» (العقد `topk_prereg.md`) ──────────
#    🔒 **قرارُ تسليمٍ لا حكمُ تجربة:** يُخرِج منحنى كلفةٍ للمالك — ولا يمسّ
#    الحكمَ الرسميّ عند `TOPK`=10 ولا المفتاحَ المشحون ولا عتبةً حيّة.
LADDER_KS = (1, 2, 3, 5, 10, 15, 20)       # §③ — مثبَّتٌ قبل أيّ رقم
FLOOR_TARGETS = (1.0, 3.0, 5.0)            # متوسّطُ الأسماء لكلّ قرار
COMBO_K = 3                                # `C3` = `K3` ∩ `F3`


def wilson(k, n, z=1.96):
    """فاصلُ ثقةٍ 95% لنسبةٍ — إلزاميٌّ هنا لأن المقامات تصغر عند `k`=1..3."""
    if n <= 0:
        return (0.0, 0.0)
    p = k / n
    dn = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - h) / dn) * 100, min(1.0, (c + h) / dn) * 100)


def cut_stats(sel, inv, y, n_dec, base):
    """مقاييسُ **قطعٍ واحد** — مصدرٌ واحدٌ لكلّ الأذرع (رتبةً كانت أو أرضية)
    فلا يتفرّق حسابُ ذراعٍ عن أخرى. `sel` قناعُ الاختيار · `inv` رقمُ القرار."""
    taken = int(sel.sum())
    hits = int(y[sel].sum())
    expl = int(y.sum())
    per = (np.bincount(inv[sel], minlength=n_dec) if taken
           else np.zeros(max(n_dec, 1), dtype=np.int64))
    p = (hits / taken) if taken else 0.0
    lo, hi = wilson(hits, taken)
    return {"taken": taken, "hits": hits, "p": p,
            "r": (hits / expl) if expl else 0.0,
            "lift": (p / base) if base else 0.0,
            "per_mean": (float(per.mean()) if n_dec else 0.0),
            "per_med": (float(np.median(per)) if n_dec else 0.0),
            "zero": ((float((per == 0).sum()) / n_dec * 100) if n_dec else 0.0),
            "lo": lo, "hi": hi}


def floor_value(sc, n_dec, target, asc=False):
    """أرضيةٌ **مطلقة** تُعطي متوسّطَ `target` اسمًا لكلّ قرار **على العيّنة
    التي تُعايَر عليها** — ثم تُطبَّق كما هي حرفيًّا خارج العيّنة (‏§③).

    🔒 المفتاحُ الصاعد يقلب الاتّجاه: الأدنى أفضل ⇒ الأرضيةُ سقفٌ لا قاع.
    """
    if sc.size == 0 or n_dec <= 0:
        return None
    m = int(round(float(target) * n_dec))
    if m <= 0:
        return None
    m = min(m, int(sc.size))
    srt = np.sort(sc)
    return float(srt[m - 1] if asc else srt[-m])


def floor_sel(sc, thr, asc=False):
    """قناعُ الأرضية — والصاعدُ يُقارَن بالعكس (مقفولٌ سلوكيًّا)."""
    if thr is None:
        return np.zeros(sc.shape, dtype=bool)
    return (sc <= thr) if asc else (sc >= thr)


def delivery_rows(d, mask, w, ki, asc, thrs, ks=LADDER_KS):
    """صفوفُ منحنى الكلفة لسنةٍ/جلسةٍ واحدة: سلّمُ الرتبة ‏+ سلّمُ الأرضية ‏+
    المركَّبة — **كلُّها من `group_ranks` و`cut_stats` نفسِهما**.

    🔒 السلّمُ **رتيبٌ بالبناء** (‏`rank < k` متداخلة) فلا يمكن أن ينقص المأخوذُ
    ولا الإصاباتُ برفع `k` — وهو ما يقفله `PS30`.
    """
    sc = np.nan_to_num(d["X"][mask][:, ki], nan=(np.inf if asc else -np.inf))
    gid, sym, y = d["gid"][mask], d["sym"][mask], d["y"][w][mask]
    _, inv = np.unique(gid, return_inverse=True)
    n_dec = int(inv.max()) + 1 if inv.size else 0
    expl, uni = int(y.sum()), int(y.size)
    base = (expl / uni) if uni else 0.0
    r = group_ranks(sc, gid, sym, asc=asc)
    out = {"n_dec": n_dec, "expl": expl, "uni": uni, "base": base,
           "expl_per": (expl / n_dec) if n_dec else 0.0,
           "K": [], "F": [], "C": None}
    for k in ks:
        st = cut_stats(r < k, inv, y, n_dec, base)
        st["arm"] = f"K{k}"
        out["K"].append(st)
    for tg, thr in thrs:
        st = cut_stats(floor_sel(sc, thr, asc), inv, y, n_dec, base)
        st["arm"] = f"F{tg:g}"
        st["thr"] = thr
        out["F"].append(st)
    thr3 = next((t for tg, t in thrs if abs(tg - 3.0) < 1e-9), None)
    if thr3 is not None:
        st = cut_stats((r < COMBO_K) & floor_sel(sc, thr3, asc), inv, y,
                       n_dec, base)
        st["arm"] = f"C{COMBO_K}"
        out["C"] = st
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


def year_lists(years) -> tuple:
    """(‏سنواتُ العقد بترتيبها · أيُّ سنةٍ زائدةٍ **وصفيّةً** خارجَه).

    🔒 الزائدةُ **لا تدخل الاختيارَ ولا الحكم بنيويًّا**: `tr_m`/`ev_m`
    مبنيّان على `TRAIN_YEARS`/`EVAL_YEAR` حرفيًّا فلا يبلغهما شيءٌ من هنا،
    وسقفُ ما تفعله هذي القائمةُ **طباعةُ صفوفها** (تسميةٌ لا حكم).
    """
    seen = list(TRAIN_YEARS) + [EVAL_YEAR]
    extra = sorted({str(y) for y in years} - set(seen))
    return seen, extra


def year_tag(yr: str) -> str:
    """وسمُ السنة في العرض — والزائدةُ تُسمّى «وصفيّ» صريحًا لا تُخلَط."""
    if yr in TRAIN_YEARS:
        return "معايرة"
    if yr == EVAL_YEAR:
        return "تقييم (خارج العيّنة)"
    return "وصفيّ خارج العقد — لا اختيارَ ولا حكم"


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
    _yu, _yc = np.unique(d["year"], return_counts=True)
    _seen, _extra = year_lists(_yu)
    log("📅 صفوفٌ بالسنة: " + " · ".join(f"{a}={int(b):,}" for a, b in zip(_yu, _yc))
        + (f" — ومنها **وصفيّةٌ خارج العقد**: {', '.join(_extra)} "
           "(تُطبَع ولا تدخل نموذجًا ولا حكمًا)" if _extra else ""))
    if _extra:
        log("   ⚠️ ومجاميعُ «منفجرون» أعلاه **تشمل السنةَ الوصفيّة** — تُقرأ بالسنة "
            "من الجداول أدناه لا من المجموع.")
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
            for yr in _seen + _extra:
                m = (d["year"] == yr) & (d["slot"] == slot)
                tab = s0_table(d, feats, m, w)
                if not tab:
                    continue
                base = tab[0][1]["base"]
                tag = year_tag(yr)
                log(f"\n【{slot} · نافذة {wname} · {yr} — {tag}】 كون={tab[0][1]['uni']:,}"
                    f" · منفجرون={tab[0][1]['expl']} · base={base*100:.3f}%")
                for f, r in tab[:8]:
                    bt = next((b for b, ff in PF.BASELINES.items() if ff == f), "")
                    log(f"      {f:14} {'(' + bt + ')' if bt else '':5} إصابات "
                        f"{r['hits']:4} من {r['taken']:6} ⇒ P@10 {r['p']*100:.3f}% · "
                        f"lift {r['lift']:5.1f}× · R@10 {r['r']*100:.1f}%")
    # ── 🎯 أسماءُ الإصابات — «وش الأسهم اللي كانت بتوصلني وفعلًا تنفجر؟» ──
    #    بالمفتاح **المشحون حيًّا** لكلّ جلسة (`PF.rank_key`) لا بمفتاحٍ مختار
    #    الآن، وبـ`topk_idx` نفسِه الذي يحكم به `eval_scores` ⇒ عددُ الأسماء
    #    **يساوي `hits`** بالبناء. تسميةٌ لا حكم.
    log("")
    log("=" * 78)
    log("🎯 أسماءُ الإصابات بالمفتاح **المشحون حيًّا** — مَن كانت ستصله القائمةُ "
        "(أعلى عشرة في قراره) وانفجر فعلًا ‏+80%")
    log("=" * 78)
    syms_env = [x.strip().upper() for x in
                (os.environ.get("PRESESSION_SYMS") or "").replace(",", " ").split() if x.strip()]
    for slot in ("PM", "AH"):
        key = PF.rank_key(slot)
        if key not in feats:
            log(f"\n【{slot}】 ⛔ المفتاحُ المشحون `{key}` خارج قائمة الميزات — لا تسمية.")
            continue
        ki = feats.index(key)
        asc = key in set(PF.FEATS_ASC)
        for w in S0_WINDOWS:
            wname = f"{w}د" if w else "الجلسة"
            for yr in _seen + _extra:
                m = (d["year"] == yr) & (d["slot"] == slot)
                if not m.any():
                    continue
                sc = np.nan_to_num(d["X"][m][:, ki],
                                   nan=(np.inf if asc else -np.inf))
                res = eval_scores(sc, d["gid"][m], d["sym"][m], d["y"][w][m], asc=asc)
                names = hit_names(d, sc, m, w, asc=asc)
                ok = "✅" if len(names) == res["hits"] else "🔴 تفرّق"
                tag = year_tag(yr)
                log(f"\n【{slot} · `{key}` · نافذة {wname} · {yr} — {tag}】 "
                    f"إصابات {res['hits']} من {res['taken']} مأخوذًا "
                    f"(‏P@10 {res['p']*100:.3f}% · lift {res['lift']:.1f}×) · "
                    f"اتّساقُ التسمية {ok}")
                if not names:
                    log("      لا إصابةَ واحدة.")
                for r in names[:40]:
                    mv = "—" if r["max"] is None else f"+{r['max']:.0f}%"
                    log(f"      {r['day']}  {r['sym']:<8} {mv}")
                if len(names) > 40:
                    log(f"      … و{len(names) - 40} إصابةً أخرى (قُصّت للعرض — "
                        f"المجموعُ {len(names)}).")
        # 🔎 تتبُّعُ رموزٍ يطلبها المالك: هل كانت في القائمة؟ وهل انفجرت؟
        for sym_q in syms_env:
            idx = np.where(d["names"] == sym_q)[0]
            if not idx.size:
                log(f"\n   🔎 {sym_q}: **خارج كون القياس كلِّه** (لا صفَّ واحدًا) — "
                    "لا يُخمَّن حكمٌ عليه.")
                continue
            code = int(idx[0])
            sm = (d["slot"] == slot) & (d["sym"] == code)
            if not sm.any():
                log(f"\n   🔎 {sym_q} [{slot}]: بلا صفٍّ في هذي الجلسة.")
                continue
            rows_n = int(sm.sum())
            for w in S0_WINDOWS:
                wname = f"{w}د" if w else "الجلسة"
                hit_days = []
                for yr in _seen + _extra:
                    m = (d["year"] == yr) & (d["slot"] == slot)
                    if not m.any():
                        continue
                    sc = np.nan_to_num(d["X"][m][:, ki],
                                       nan=(np.inf if asc else -np.inf))
                    top = topk_idx(sc, d["gid"][m], d["sym"][m], asc=asc)
                    ss, gg, yy = d["sym"][m], d["gid"][m], d["y"][w][m]
                    for i in top:
                        if int(ss[i]) != code:
                            continue
                        day, _ = d["gkey"][int(gg[i])]
                        hit_days.append(f"{day}{'✅' if yy[i] else '·'}")
                expl = int(d["y"][w][sm].sum())
                log(f"\n   🔎 {sym_q} [{slot} · {wname}]: صفوفٌ {rows_n} · "
                    f"انفجر ‏+80% في {expl} يومًا · **دخل القائمةَ** في "
                    f"{len(hit_days)} يومًا"
                    + (": " + ", ".join(hit_days[:20]) if hit_days else " (ولا مرّة)"))
            # ⛔ «ليه فات؟» — يومًا يومًا داخل قرارِ ذلك اليوم (وصفٌ لا اختيار)
            for w in S0_WINDOWS:
                wname = f"{w}د" if w else "الجلسة"
                mr = miss_report(d, feats, code, slot, w, key)
                ex = [r for r in mr if r["hit"]]
                if not ex:
                    continue
                log(f"\n   ⛔ **ليه فات {sym_q}؟** [{slot} · {wname}] — "
                    f"أيامُ الانفجار {len(ex)} · المفتاحُ المشحون `{key}`")
                for r in ex:
                    v = "**معدومة**" if r["val"] is None else f"{r['val']:.4g}"
                    mv = "—" if r["max"] is None else f"+{r['max']:.0f}%"
                    tag = "✅ دخل القائمة" if r["in_list"] else "🔴 خارجها"
                    log(f"      {r['day']}  رتبتُه {r['rank']:,} من {r['uni']:,} "
                        f"({tag}) · `{key}`={v} · أعلى نسبة {mv}")
                    log("         أفضلُ رتبٍ: " + " · ".join(
                        f"{f}#{rk}" for rk, f in r["best"]))
                lst = [r for r in mr if r["in_list"] and not r["hit"]]
                if lst:
                    log(f"      🟡 وأيامُ القائمة بلا انفجار ({len(lst)}): " + " · ".join(
                        f"{r['day']} رتبة {r['rank']}"
                        + ("" if r["max"] is None else f" · أعلى نسبته {r['max']:+.0f}%")
                        for r in lst[:12]))
                n_ex, tal = miss_key_tally(mr, feats)
                log(f"      📊 **وصفيٌّ صرف** — كم يومَ انفجارٍ كان كلُّ مفتاحٍ "
                    f"سيلتقطه (من {n_ex}): "
                    + (" · ".join(f"{f}={n}" for n, f in tal[:8]) or "لا مفتاح")
                    + " 🔴 **ولا يُبدَّل به مفتاحٌ**: عدٌّ على سهمٍ واحدٍ بعد رؤية "
                      "نتيجته هو `p-hacking` بحرفه.")
    # ── 📦 `T-TOPK` — منحنى كلفة «كم اسمًا يصل المالك؟» (لا حكم) ──────────
    log("")
    log("=" * 78)
    log("📦 T-TOPK — «كم اسمًا يصل المالك؟» **منحنى كلفةٍ لقرار تسليم لا حكم** "
        "(العقد `topk_prereg.md` · النافذةُ الحاكمة: الجلسةُ كاملةً)")
    log("=" * 78)
    log("🔒 الحكمُ الرسميّ «فشلت» عند TOPK=10 **لا يتغيّر** · والمفتاحُ المشحون "
        "**لا يُبدَّل** · وصفرُ مسٍّ بعتبةٍ حيّة — ولا شحنَ بلا أمر المالك.")
    _tw = 0                       # النافذةُ الحاكمة = الجلسةُ كاملةً
    for slot in ("PM", "AH"):
        key = PF.rank_key(slot)
        if key not in feats:
            log(f"\n【{slot}】 ⛔ المفتاحُ المشحون `{key}` خارج الميزات — لا جدول.")
            continue
        ki = feats.index(key)
        asc = key in set(PF.FEATS_ASC)
        # 🔒 الأرضياتُ **مُعايَرةٌ على سنتَي المعايرة وحدهما** ثم تُطبَّق كما هي
        tr_d = (d["slot"] == slot) & np.isin(d["year"], list(TRAIN_YEARS))
        thrs = []
        if tr_d.any():
            sc_tr = np.nan_to_num(d["X"][tr_d][:, ki],
                                  nan=(np.inf if asc else -np.inf))
            n_tr = int(np.unique(d["gid"][tr_d]).size)
            thrs = [(t, floor_value(sc_tr, n_tr, t, asc=asc))
                    for t in FLOOR_TARGETS]
        log(f"\n【{slot} · المفتاحُ المشحون `{key}`】 أرضياتٌ مُعايَرةٌ على "
            f"{'+'.join(TRAIN_YEARS)} حصرًا: "
            + " · ".join(f"F{t:g}={'—' if v is None else f'{v:.5g}'}"
                         for t, v in thrs))
        for yr in _seen + _extra:
            m = (d["year"] == yr) & (d["slot"] == slot)
            if not m.any():
                continue
            rr = delivery_rows(d, m, _tw, ki, asc, thrs)
            log(f"\n  ── {yr} — {year_tag(yr)} · قرارات {rr['n_dec']} · "
                f"منفجرون {rr['expl']} (**{rr['expl_per']:.2f} لكلّ قرار** = "
                f"سقفُ العرّاف) · الأساس {rr['base']*100:.3f}%")
            log("     ذراع │ أسماء/قرار │ صفرُ أسماء │ مأخوذ │ إصابات │  P    "
                "│ Wilson95      │  R    │ lift")
            for st in rr["K"] + rr["F"] + ([rr["C"]] if rr["C"] else []):
                log(f"     {st['arm']:<5}│ {st['per_mean']:9.2f}  │ "
                    f"{st['zero']:8.1f}% │{st['taken']:6} │{st['hits']:7} │"
                    f"{st['p']*100:6.3f}%│ [{st['lo']:5.2f},{st['hi']:6.2f}] │"
                    f"{st['r']*100:6.2f}%│{st['lift']:6.1f}×")
    log("")
    log("📌 **يُقرأ منحنى كلفةٍ لا حكمًا** — ولا تُرقّى ذراعٌ منه إلى قرارٍ إلّا "
        "بأمر المالك الصريح (سقفُ النجاح في `topk_prereg §⑤`).")

    log("")
    log("📌 ترتيبُ التراجع المقفول: تُقرأ نافذةُ 10 أوّلًا، ولا يُقرأ حكمُ نافذةٍ "
        "أوسعَ حكمًا على الأضيق. **والنافذةُ التي يريدها المالك هي الجلسةُ كاملةً "
        "(تصحيحُه 2026-09-03) — وحكمُها مطبوعٌ أعلاه ولم يُنتقَ بعد الأرقام.**")
    return 0


if __name__ == "__main__":
    sys.exit(main())
