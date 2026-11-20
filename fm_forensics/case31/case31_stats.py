#!/usr/bin/env python3
"""📊 `T-CASE31` — المقارنةُ والبحثُ واختبارُ الخلط (العقد §④-§⑤) — نقيٌّ بلا شبكة (numpy وحدَه).

المرصودُ والخلطةُ يمرّان من **الدالّة نفسِها** `search(...)` — لا فرعَ خاصًّا للمرصود. كلُّ تحضيرٍ لا يعتمد على الوسم (المئينيّات · الرُّتب ·
التغطية · أخماسُ الزخم · طيّاتُ التحقّق) يُحسب مرّةً في `prepare(...)`؛ وما يعتمد على الوسم (ترتيبُ الشروط · اختيارُ الأربعين · التوليفات ·
الاستبعاد · اختيارُ سمات النموذجين وتدريبُهما) يُعاد في كلّ خلطة.
"""
import hashlib
import itertools
import math

import numpy as np

import case31_catalog as CAT

COV = 0.80                    # تغطيةُ السمة في الصفوف وفي الموجبين
TOP_SINGLES = 40              # أعلى الشروط المنفردة الداخلة في التوليفات (شرطٌ واحد لكلّ سمةٍ أساسيّة)
MAX_K = 3
EXC_POS, EXC_NEG = 0.05, 0.20  # سمةُ الاستبعاد: أقلُّ من 5% من المنفجرين و20% فأكثر من الضابطة
TREE_FEATS, LOGIT_FEATS = 200, 50
TREE_DEPTH, L2 = 3, 1.0
BINS = 10
TOP_SHARE = 0.05
BOOT = 2000
SEED = "C31"
FOLDS_B = 20


def _seed(*parts):
    return int(hashlib.sha256("|".join(str(p) for p in (SEED,) + parts).encode()).hexdigest()[:8], 16)


def base_of(name):
    for suf in (".d5", ".d10"):
        if name.endswith(suf):
            return name[:-len(suf)]
    return name


# ══ التحضير (لا يعتمد على الوسم) ═════════════════════════════════════════════════════════════════════════════════════════════════
class FV:
    """صفُّ سماتٍ مضغوط (float32 بترتيب الفهرس الموسَّع · NaN = مجهول) بواجهة `.get` — يخفّض ذاكرةَ الصفّ من ‏≈120 ك.بايت إلى ‏≈8."""
    __slots__ = ("a",)
    _IX = None

    @classmethod
    def ix(cls):
        if cls._IX is None:
            cls._IX = {n: j for j, (n, _k, _a) in enumerate(CAT.expanded())}
        return cls._IX

    def __init__(self, f):
        ix = self.ix()
        a = np.full(len(ix), np.nan, dtype=np.float32)
        for k, v in f.items():
            j = ix.get(k)
            if j is not None and v is not None:
                a[j] = float(v)
        self.a = a

    def get(self, nm, default=None):
        j = self.ix().get(nm)
        if j is None:
            return default
        v = self.a[j]
        return default if v != v else float(v)


def prepare(rows, arm, min_k):
    """rows = [{sym, day, y (0/1), f: {اسم: قيمة}}] ⟵ هيكلُ البحث. `arm` = "A" (كلُّ السمات) أو "B" (سماتُ `AB` وحدَها)."""
    names = [(n, k) for n, k, a in CAT.expanded() if arm == "A" or a == "AB"]
    n, p = len(rows), len(names)
    X = np.full((n, p), np.nan, dtype=np.float32)
    cols = np.array([FV.ix()[nm] for nm, _k in names], dtype=np.int64)
    for i, r in enumerate(rows):
        f = r["f"]
        if isinstance(f, FV):
            X[i] = f.a[cols]
            continue
        for j, (nm, _k) in enumerate(names):
            v = f.get(nm)
            if v is not None:
                X[i, j] = float(v)
    y = np.array([int(r["y"]) for r in rows], dtype=np.int8)
    days = np.array([r["day"] for r in rows])
    uniq = sorted(set(days.tolist()))
    day_ix = np.array([uniq.index(d) for d in days], dtype=np.int32)
    known = ~np.isnan(X)
    cov_all = known.mean(axis=0)
    cov_pos = known[y == 1].mean(axis=0) if y.sum() else np.zeros(p)
    elig = (cov_all >= COV) & (cov_pos >= COV)
    # الرُّتبُ المعياريّة (0-1 · المجهولُ 0.5) والصناديقُ العشريّة — على كلّ الصفوف
    R = np.full((n, p), 0.5, dtype=np.float32)
    for j in range(p):
        m = known[:, j]
        if m.sum() > 1:
            v = X[m, j]
            order = np.argsort(v, kind="mergesort")
            rk = np.empty(len(v), dtype=np.float64)
            rk[order] = np.arange(len(v))
            _u, inv, cnt = np.unique(v, return_inverse=True, return_counts=True)
            sums = np.bincount(inv, weights=rk)
            R[m, j] = ((sums / cnt)[inv] + 0.5) / len(v)
    bins = np.minimum((R * BINS).astype(np.int8), BINS - 1)
    # الشروطُ الثنائيّة
    conds, vecs = [], []
    for j, (nm, kind) in enumerate(names):
        if not elig[j]:
            continue
        col, m = X[:, j], known[:, j]
        if kind == "bool":
            conds += [(nm + "=1", j, None), (nm + "=0", j, None)]
            vecs += [m & (col == 1), m & (col == 0)]
        else:
            qs = np.nanpercentile(col, CAT.QUANTS)
            for q, thr, lt in ((CAT.QUANTS[0], qs[0], True), (CAT.QUANTS[1], qs[1], True), (CAT.QUANTS[2], qs[2], False), (CAT.QUANTS[3], qs[3], False)):
                conds.append((f"{nm}{'<' if lt else '>'}q{q}", j, float(thr)))
                vecs.append(m & ((col < thr) if lt else (col > thr)))
    B = np.array(vecs, dtype=bool) if vecs else np.zeros((0, n), bool)
    n_c = B.sum(axis=1)
    bid = {}
    cbase = np.array([bid.setdefault(base_of(names[j][0]), len(bid)) for _nm, j, _t in conds], dtype=np.int64) if conds else np.zeros(0, np.int64)
    # أخماسُ الزخم داخل اليوم (px.ret5)
    jr = next((j for j, (nm, _k) in enumerate(names) if nm == "px.ret5"), None)
    quint = np.full(n, -1, dtype=np.int8)
    if jr is not None:
        for d in range(len(uniq)):
            m = (day_ix == d) & known[:, jr]
            if m.sum() >= 5:
                v = X[m, jr]
                quint[m] = np.minimum((np.argsort(np.argsort(v)) * 5 // len(v)), 4)
    # طيّاتُ التحقّق: يومٌ كامل (أ) · 20 طيّةً من أيّامٍ كاملة ببصمة التاريخ (ب)
    if arm == "A":
        fold = day_ix.copy()
    else:
        fmap = np.array([int(hashlib.sha256(d.encode()).hexdigest()[:8], 16) % FOLDS_B for d in uniq])
        fold = fmap[day_ix]
    folds = sorted(set(fold.tolist()))
    fold_sum = {f_: R[fold == f_].sum(axis=0, dtype=np.float64) for f_ in folds}
    fold_n = {f_: int((fold == f_).sum()) for f_ in folds}
    return {"names": names, "X": X, "R": R, "bins": bins, "known": known, "y": y, "day_ix": day_ix, "days": uniq, "elig": elig,
            "cov_all": cov_all, "cov_pos": cov_pos, "conds": conds, "B": B, "n_c": n_c, "cbase": cbase, "quint": quint, "fold": fold,
            "folds": folds, "fold_sum": fold_sum, "fold_n": fold_n, "tot_sum": R.sum(axis=0, dtype=np.float64), "arm": arm, "min_k": int(min_k),
            "n": n, "p": p}


def shuffle_labels(P, rng):
    """خلطُ الوسم **داخل كلّ يوم**: عددُ الموجبين في اليوم ثابت."""
    y = np.zeros(P["n"], dtype=np.int8)
    for d in range(len(P["days"])):
        idx = np.nonzero(P["day_ix"] == d)[0]
        m = int(P["y"][idx].sum())
        if m:
            y[rng.choice(idx, size=m, replace=False)] = 1
    return y


# ══ البحث (يعتمد على الوسم — يُعاد في كلّ خلطة) ═════════════════════════════════════════════════════════════════════════════════
def _z(k, n_c, p):
    den = np.sqrt(np.maximum(n_c * p * (1 - p), 1e-12))
    return (k - n_c * p) / den


def singles(P, y):
    pos = np.nonzero(y == 1)[0]
    npos, n = len(pos), P["n"]
    p0 = npos / n
    k = P["B"][:, pos].sum(axis=1) if npos else np.zeros(len(P["conds"]))
    z = _z(k, P["n_c"], p0)
    valid = (k >= P["min_k"]) & (P["n_c"] < n)
    return k, z, valid, p0


def top_conditions(P, z, valid):
    """أعلى `TOP_SINGLES` شرطًا صالحًا درجةً — شرطٌ واحد لكلّ سمةٍ أساسيّة."""
    order = np.argsort(-np.where(valid, z, -np.inf), kind="mergesort")
    out, seen = [], set()
    for c in order:
        if not valid[c] or len(out) >= TOP_SINGLES:
            break
        b = int(P["cbase"][c])
        if b in seen:
            continue
        seen.add(b)
        out.append(int(c))
    return out


def combos(P, y, top, p0):
    """كلُّ توليفةٍ من شرطين وثلاثة (AND) من `top` ⟵ [(z, k, n, (شروط))] للصالحة (k ≥ min_k) مرتّبةً تنازليًّا."""
    if len(top) < 2:
        return [], 0
    Bt = P["B"][top]
    pos = y == 1
    Bp = Bt[:, pos]
    out, tried = [], 0
    for r in (2, 3):
        for cmb in itertools.combinations(range(len(top)), r):
            tried += 1
            kp = Bp[cmb[0]] & Bp[cmb[1]]
            if r == 3:
                kp = kp & Bp[cmb[2]]
            k = int(kp.sum())
            if k < P["min_k"]:
                continue
            v = Bt[cmb[0]] & Bt[cmb[1]]
            if r == 3:
                v = v & Bt[cmb[2]]
            n_c = int(v.sum())
            out.append((float(_z(k, n_c, p0)), k, n_c, tuple(top[i] for i in cmb)))
    out.sort(key=lambda t: (-t[0], len(t[3]), t[3]))
    return out, tried


def exclusions(P, y, k):
    npos = int(y.sum())
    nneg = P["n"] - npos
    if not npos or not nneg:
        return []
    sp = k / npos
    sn = (P["n_c"] - k) / nneg
    ok = (sp < EXC_POS) & (sn >= EXC_NEG)
    idx = np.nonzero(ok)[0]
    return sorted(((float(sn[c]), int(c), float(sp[c])) for c in idx), key=lambda t: (-t[0], t[1]))


def _day_auc(score, y, day_ix):
    """متوسّطُ نسبة ضابطة اليوم نفسِه التي درجتُها أدنى من درجة الموجب (التعادلُ نصف) — AUC داخل اليوم."""
    vals = []
    for i in np.nonzero(y == 1)[0]:
        m = (day_ix == day_ix[i]) & (y == 0)
        if m.any():
            s = score[m]
            vals.append(((s < score[i]).sum() + 0.5 * (s == score[i]).sum()) / len(s))
    return float(np.mean(vals)) if vals else float("nan")


def _top_share(score, y, day_ix):
    """نسبةُ المنفجرين بين صفوف أعلى 5% درجةً داخل كلّ يوم (مجمَّعةً)."""
    hit = tot = 0
    for d in np.unique(day_ix):
        idx = np.nonzero(day_ix == d)[0]
        kq = max(1, int(math.ceil(TOP_SHARE * len(idx))))
        top = idx[np.argsort(-score[idx], kind="mergesort")[:kq]]
        hit += int(y[top].sum())
        tot += kq
    return hit / tot if tot else float("nan")


def _fit_tree(bins, y, feats, min_leaf):
    """شجرةُ Gini بعمق 3 على صناديقَ عشريّة ⟵ هيكلٌ متداخل (feat, thr, left, right) أو ورقةٌ (احتمال)."""
    nf = len(feats)

    def leaf(idx):
        return (float(y[idx].sum()) + 0.5) / (len(idx) + 1.0)

    def grow(idx, depth):
        npos = int(y[idx].sum())
        if depth == TREE_DEPTH or npos == 0 or npos == len(idx) or len(idx) < 2 * min_leaf:
            return leaf(idx)
        sub = bins[np.ix_(idx, feats)].astype(np.int64)
        off = np.arange(nf, dtype=np.int64) * BINS
        tot = np.bincount((sub + off).ravel(), minlength=nf * BINS).reshape(nf, BINS)
        ps = np.bincount((sub[y[idx] == 1] + off).ravel(), minlength=nf * BINS).reshape(nf, BINS)
        ctot, cpos = np.cumsum(tot, axis=1)[:, :-1], np.cumsum(ps, axis=1)[:, :-1]
        nl, nr = ctot, len(idx) - ctot
        pl, pr = cpos, npos - cpos
        with np.errstate(divide="ignore", invalid="ignore"):
            gl = 1 - (pl / nl) ** 2 - (1 - pl / nl) ** 2
            gr = 1 - (pr / nr) ** 2 - (1 - pr / nr) ** 2
            imp = (nl * gl + nr * gr) / len(idx)
        imp = np.where((nl >= min_leaf) & (nr >= min_leaf), imp, np.inf)
        j, t = np.unravel_index(int(np.argmin(imp)), imp.shape)
        if not np.isfinite(imp[j, t]):
            return leaf(idx)
        go = sub[:, j] <= t
        return (int(feats[j]), int(t), grow(idx[go], depth + 1), grow(idx[~go], depth + 1))

    return grow(np.arange(len(y)), 0)


def _tree_predict(tree, bins):
    out = np.empty(bins.shape[0], dtype=np.float64)

    def walk(node, idx):
        if not isinstance(node, tuple):
            out[idx] = node
            return
        j, t, a, b = node
        go = bins[idx, j] <= t
        walk(a, idx[go])
        walk(b, idx[~go])

    walk(tree, np.arange(bins.shape[0]))
    return out


def _fit_logit(Z, y):
    """لوجستيٌّ بـL2 وموزونٌ بالفئة (نيوتن 12 دورة) ⟵ (الأوزان، الانحراف)."""
    n, p = Z.shape
    npos = max(1, int(y.sum()))
    w = np.where(y == 1, n / (2.0 * npos), n / (2.0 * max(1, n - npos)))
    A = np.hstack([Z, np.ones((n, 1))])
    beta = np.zeros(p + 1)
    reg = np.eye(p + 1) * L2
    reg[p, p] = 0.0
    for _ in range(12):
        mu = 1 / (1 + np.exp(-np.clip(A @ beta, -30, 30)))
        g = A.T @ (w * (mu - y)) + reg @ beta
        H = (A * (w * mu * (1 - mu))[:, None]).T @ A + reg
        try:
            step = np.linalg.solve(H, g)
        except np.linalg.LinAlgError:
            break
        beta -= step
        if np.abs(step).max() < 1e-6:
            break
    return beta


def models(P, y):
    """شجرةٌ بعمق 3 ولوجستيّ بتحقّقٍ متقاطع يترك طيّةً من أيّامٍ كاملة ⟵ {tree_auc, tree_top, logit_auc, logit_top}."""
    R, bins, fold = P["R"], P["bins"], P["fold"]
    el = np.nonzero(P["elig"])[0]
    st = np.zeros(P["n"])
    sl = np.zeros(P["n"])
    min_leaf = 20 if P["arm"] == "A" else 50
    pos_all = y == 1
    pos_sum_all = R[pos_all].sum(axis=0, dtype=np.float64)
    for f_ in P["folds"]:
        te = fold == f_
        tr = ~te
        ytr = y[tr]
        npos = int(ytr.sum())
        if npos < 2 or not te.any():
            st[te] = sl[te] = 0.0
            continue
        ps = pos_sum_all - R[te & pos_all].sum(axis=0, dtype=np.float64)
        ntr = P["n"] - P["fold_n"][f_]
        mean_pos = ps / npos
        mean_neg = (P["tot_sum"] - P["fold_sum"][f_] - ps) / max(1, ntr - npos)
        sc = np.abs(mean_pos - mean_neg)[el]
        order = el[np.argsort(-sc, kind="mergesort")]
        tf_, lf_ = order[:TREE_FEATS], order[:LOGIT_FEATS]
        tree = _fit_tree(bins[tr], ytr, tf_, min_leaf)
        st[te] = _tree_predict(tree, bins[te])
        beta = _fit_logit(R[np.ix_(tr, lf_)].astype(np.float64) - 0.5, ytr.astype(np.float64))
        sl[te] = (R[np.ix_(te, lf_)].astype(np.float64) - 0.5) @ beta[:-1] + beta[-1]
    return {"tree_auc": _day_auc(st, y, P["day_ix"]), "tree_top": _top_share(st, y, P["day_ix"]),
            "logit_auc": _day_auc(sl, y, P["day_ix"]), "logit_top": _top_share(sl, y, P["day_ix"]), "_st": st, "_sl": sl}


def search(P, y, with_models=True, keep=False):
    """**البحثُ كلُّه لوسمٍ واحد** (المرصودُ والخلطةُ من هنا) ⟵ القِممُ: أعلى z لبصمة · أعلى اختصارٍ لاستبعاد · دقّةُ النموذجين."""
    k, z, valid, p0 = singles(P, y)
    top = top_conditions(P, z, valid)
    cmb, tried = combos(P, y, top, p0)
    exc = exclusions(P, y, k)
    best_single = max((float(z[c]) for c in np.nonzero(valid)[0]), default=float("nan"))
    best_combo = cmb[0][0] if cmb else float("nan")
    out = {"best_single": best_single, "best_combo": best_combo,
           "best_print": float(np.nanmax([best_single, best_combo])) if not (math.isnan(best_single) and math.isnan(best_combo)) else float("nan"),
           "best_excl": exc[0][0] if exc else 0.0, "n_excl": len(exc), "n_valid_singles": int(valid.sum()), "n_combos_tried": tried,
           "n_combos_valid": len(cmb)}
    if with_models:
        m = models(P, y)
        out.update({kk: v for kk, v in m.items() if keep or not kk.startswith("_")})
    if keep:
        out.update({"_k": k, "_z": z, "_valid": valid, "_top": top, "_combos": cmb, "_excl": exc, "_p0": p0})
    return out


SHUFFLE_KEYS = ("best_single", "best_combo", "best_print", "best_excl", "tree_auc", "logit_auc", "tree_top", "logit_top")


def shuffle_block(P, start, count, with_models=True):
    """خلطاتٌ مرقّمة [start، start+count) ⟵ [{المفاتيحُ القِمميّة}] · بذرةُ كلّ خلطةٍ من رقمها."""
    out = []
    for i in range(start, start + count):
        rng = np.random.default_rng(_seed("shuffle", P["arm"], i))
        r = search(P, shuffle_labels(P, rng), with_models=with_models)
        out.append({kk: r.get(kk) for kk in SHUFFLE_KEYS} | {"i": i})
    return out


def beats(obs, shuffled, key, q=95.0):
    """⟵ (المئينُ 95 لقِمم الخلطات، نسبةُ الخلطات التي يفوقها المرصود، يعبر؟) — المجهولُ في خلطةٍ يُعَدّ −∞."""
    xs = np.array([(-np.inf if (s.get(key) is None or s.get(key) != s.get(key)) else s[key]) for s in shuffled], dtype=float)
    if not len(xs) or obs is None or obs != obs:
        return None, None, False
    thr = float(np.percentile(xs, q))
    return thr, float((xs < obs).mean()), bool(obs > thr)


# ══ جداولُ الوصف (المرصودُ وحدَه) ═══════════════════════════════════════════════════════════════════════════════════════════════
def feature_table(P, y, extra_mask=None):
    """لكلّ سمة: نسبتُها/وسيطُها عند المنفجرين والضابطة · الفرقُ المعياريّ (متوسّطُ الرتبة) بفاصلٍ عنقوديّ بيوم القرار · ومقابل ضابط الزخم المطابق."""
    X, R, known = P["X"], P["R"], P["known"]
    pos, neg = y == 1, y == 0
    nd = len(P["days"])
    D1 = np.zeros((nd, P["n"]), dtype=np.float32)
    D1[P["day_ix"], np.arange(P["n"])] = 1.0
    sp, sn = D1[:, pos] @ R[pos].astype(np.float64), D1[:, neg] @ R[neg].astype(np.float64)
    cp, cn = D1[:, pos].sum(axis=1), D1[:, neg].sum(axis=1)
    rng = np.random.default_rng(_seed("boot", P["arm"]))
    draws = rng.integers(0, nd, size=(BOOT, nd))
    w = np.zeros((BOOT, nd))
    for b in range(BOOT):
        np.add.at(w[b], draws[b], 1.0)
    num_p, num_n = w @ sp, w @ sn
    den_p, den_n = np.maximum(w @ cp, 1e-9)[:, None], np.maximum(w @ cn, 1e-9)[:, None]
    bd = num_p / den_p - num_n / den_n
    lo, hi = np.percentile(bd, 2.5, axis=0), np.percentile(bd, 97.5, axis=0)
    diff = sp.sum(axis=0) / max(1, cp.sum()) - sn.sum(axis=0) / max(1, cn.sum())
    # ضابطُ الزخم المطابق: لكلّ موجبٍ ضابطةُ يومه في خُمسه
    md = np.full(P["p"], np.nan)
    acc, cnt = np.zeros(P["p"]), 0
    for i in np.nonzero(pos)[0]:
        if P["quint"][i] < 0:
            continue
        m = neg & (P["day_ix"] == P["day_ix"][i]) & (P["quint"] == P["quint"][i])
        if m.sum() >= 3:
            acc += R[i] - R[m].mean(axis=0)
            cnt += 1
    if cnt:
        md = acc / cnt
    out = []
    for j, (nm, kind) in enumerate(P["names"]):
        kp, kn = known[pos, j], known[neg, j]
        if kind == "bool":
            a = float(X[pos, j][kp].mean()) if kp.any() else None
            b = float(X[neg, j][kn].mean()) if kn.any() else None
        else:
            a = float(np.median(X[pos, j][kp])) if kp.any() else None
            b = float(np.median(X[neg, j][kn])) if kn.any() else None
        row = {"name": nm, "kind": kind, "pos": a, "neg": b, "diff": float(diff[j]), "lo": float(lo[j]), "hi": float(hi[j]),
               "matched": (None if md[j] != md[j] else float(md[j])), "cov": float(P["cov_all"][j]), "cov_pos": float(P["cov_pos"][j]),
               "elig": bool(P["elig"][j])}
        if extra_mask is not None and extra_mask.any():
            ke = known[extra_mask, j]
            row["x50"] = (float(X[extra_mask, j][ke].mean()) if kind == "bool" else float(np.median(X[extra_mask, j][ke]))) if ke.any() else None
        out.append(row)
    out.sort(key=lambda r: -abs(r["diff"]) if r["elig"] else 1.0)
    return out


def cond_text(P, c):
    return P["conds"][c][0]


def cond_matched(P, y, conds_ix):
    """فرقُ حمل التوليفة بين الموجبين وضابط الزخم المطابق (موجبٌ = يبقى بعد ضبط الزخم)."""
    v = np.ones(P["n"], bool)
    for c in conds_ix:
        v &= P["B"][c]
    pos, neg = y == 1, y == 0
    acc, cnt = 0.0, 0
    for i in np.nonzero(pos)[0]:
        if P["quint"][i] < 0:
            continue
        m = neg & (P["day_ix"] == P["day_ix"][i]) & (P["quint"] == P["quint"][i])
        if m.sum() >= 3:
            acc += float(v[i]) - float(v[m].mean())
            cnt += 1
    return (acc / cnt) if cnt else None


def neighbours(P, y, rows, k=5, top=10):
    """لكلّ منفجرٍ أشبهُ `k` صفوفٍ لم تنفجر في يومه (إقليديّةٌ على الرتب المعياريّة للسمات الرقميّة المؤهَّلة) وأكبرُ `top` سماتٍ فرّقته."""
    num = np.array([j for j, (_nm, kind) in enumerate(P["names"]) if kind == "num" and P["elig"][j]], dtype=int)
    out = []
    for i in np.nonzero(y == 1)[0]:
        m = np.nonzero((y == 0) & (P["day_ix"] == P["day_ix"][i]))[0]
        if not len(m) or not len(num):
            continue
        A = P["R"][np.ix_(m, num)].astype(np.float64)
        me = P["R"][i, num].astype(np.float64)
        mu, sd = A.mean(axis=0), A.std(axis=0) + 1e-9
        dist = np.sqrt((((A - mu) / sd - (me - mu) / sd) ** 2).sum(axis=1))
        nn = m[np.argsort(dist, kind="mergesort")[:k]]
        gap = P["R"][i, num].astype(np.float64) - P["R"][np.ix_(nn, num)].astype(np.float64).mean(axis=0)
        best = np.argsort(-np.abs(gap), kind="mergesort")[:top]
        out.append({"sym": rows[i]["sym"], "day": rows[i]["day"], "nn": [rows[q]["sym"] for q in nn],
                    "diff": [(P["names"][num[b]][0], float(gap[b])) for b in best]})
    return out


def wilson_lo(k, n, z=1.96):
    if not n:
        return None
    ph = k / n
    den = 1 + z * z / n
    return (ph + z * z / (2 * n) - z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))) / den
