#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📈✖️③➕ `T-EMA3` الملحق 1 — «تقاطع إيما بعد اختبار القاع» (العقد `T_EMA3_ADDENDUM_1.md` · أمرُ المالك 2026-11-21 · مسجَّلٌ بعد رؤية أرقام).

  run <part> --dir D   — على مادّة `T-EMA3` المجلوبة نفسِها: أحداثُ «قاع ثم ارتداد ثم رجوع» بتعريف `T-SUPPORT2` بالاسم ⟵ أوّلُ تقاطعٍ بعد الرجوع ⟵
                         العددُ أوّلًا ثمّ المقارناتُ الثلاث ⟵ `out/RETEST_<PART>.json|md` · **مرّةً واحدة** لكلّ جزء · والتأكيدُ بعد الاكتشاف.
  verdict              — يقرأ الجزأين ويطبع الحكم المنفرد (العقد §④).
🔒 لا جلبَ جديد · لا تلغرام · لا Polygon · لا CONFIG يُسنَد · وأوضاعُ `ema3.py` المُغلَقة لا تُنادى.
"""
import bisect
import datetime as dt
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
NAWAQIS = os.path.join(ROOT, "fm_forensics", "nawaqis")
for _p in (ROOT, NAWAQIS, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import ema3 as E                                                  # noqa: E402
import support2 as S2                                             # noqa: E402  — تعريفُ «الدعم الثاني» بالاسم (`level_of` · `second_entry`)

CONTRACT = os.path.join(HERE, "T_EMA3_ADDENDUM_1.md")
CONTRACT_SHA = "69cc81ed7c315b865fe5db6a97b38b05cf101f33d24a332fb3b3ab230f479151"                                                # يُملأ قبل الدمج · فارغٌ أو مخالف ⟵ خروج 11
PARTS = {"discover": "RETEST_DISCOVER", "confirm": "RETEST_CONFIRM"}
BASE = {"discover": "DISCOVER", "confirm": "CONFIRM"}             # صفوفُ الإشارة الأولى المودَعة
SRC_RUNS = {"discover": "44888937080", "confirm": "44890468806"}  # مادّةُ T-EMA3 المجلوبة — لا جلبَ جديد
HIST_DAYS = 90                                                     # T-SUPPORT2 §①: 90 يومًا تقويميًّا حتى يوم القرار
WIN = S2.WIN                                                       # 20 جلسة: نافذةُ الارتداد والرجوع · ونافذةُ الإشارة بعد الرجوع
CLOSE_HOUR, BAR_HOURS = 16, 4                                      # الشمعةُ تُغلق عند الإغلاق النظاميّ (16:00 نيويورك) أو بعده
CLOSED = True                                                      # 2026-11-21: الحكم «لا تعبر» (`T_EMA3_ADDENDUM_1_RESULT.md`) ⟵ مُغلَقٌ مُنفَّذًا


def log(m=""):
    print(m, flush=True)


def contract_ok():
    try:
        return bool(CONTRACT_SHA) and E.sha_of(CONTRACT) == CONTRACT_SHA and E.contract_ok()
    except OSError:
        return False


def closed():
    return bool(CLOSED) and os.environ.get("EMA3_REOPEN", "") != "1"


def guard(part, out_dir=None):
    """⟵ رمزُ الخروج قبل أيّ عمل: 5 جزءٌ مجهول · 11 عقدٌ متغيّر · 7 الجزءُ صدر · 9 التأكيدُ قبل الاكتشاف · 0 يمضي."""
    out_dir = E.OUT if out_dir is None else out_dir
    if part not in PARTS:
        return E.RC_DATA
    if not contract_ok():
        return E.RC_CONTRACT
    if os.path.exists(os.path.join(out_dir, PARTS[part] + ".json")):
        return E.RC_ONCE
    if part == "confirm" and not os.path.exists(os.path.join(out_dir, PARTS["discover"] + ".json")):
        return E.RC_ORDER
    return E.RC_OK


# ══ ① أحداثُ «قاع ثم ارتداد ثم رجوع» (تعريفُ T-SUPPORT2 بالاسم) ══════════════════════════════════════════════════════════════════
def decision_days(part, plan):
    """⟵ [(رمز، يومُ قرار)] مرتّبةً باليوم: إدخالاتُ CURRENT في الاكتشاف · وكلُّ (رمز، يومُ لقطة) في التأكيد."""
    if part == "discover":
        pairs = {(str(s).upper(), str(d)) for s, d in plan["entries"]}
    else:
        pairs = {(str(s).upper(), str(d)) for d, syms in plan["snap_days"].items() for s in syms}
    return sorted(pairs, key=lambda x: (x[1], x[0]))


def retests(pairs, rows_by, sessions, level_fn):
    """rows_by = {رمز: [(يوم, o, h, l, c, v)]} ⟵ (الأحداث {(رمز، d′): {L, d, up}}، العدّ).
    `level_fn(hist)` = `support2.level_of` · والحالةُ من `support2.second_entry` بالاسم · والحدثُ الواحد يُحفظ بأبكر يوم قرار."""
    pos = {d: i for i, d in enumerate(sessions)}
    events, why, cache = {}, {}, {}
    for sym, d in pairs:
        rows = rows_by.get(sym)
        if not rows:
            why["بلا شموع"] = why.get("بلا شموع", 0) + 1
            continue
        i = pos.get(d)
        if i is None:
            why["خارج التقويم"] = why.get("خارج التقويم", 0) + 1
            continue
        if sym not in cache:
            cache[sym] = ([x[0] for x in rows], {x[0]: (x[0], x[2], x[3], x[4]) for x in rows})
        days, byday = cache[sym]
        lo_day = (dt.date.fromisoformat(d) - dt.timedelta(days=HIST_DAYS)).isoformat()
        hist = rows[bisect.bisect_left(days, lo_day):bisect.bisect_right(days, d)]
        lv = level_fn(hist)
        if not lv:
            why["لا مستوى"] = why.get("لا مستوى", 0) + 1
            continue
        win = sessions[i + 1:i + 1 + WIN]
        st, up, d2 = S2.second_entry([byday[s] for s in win if s in byday], float(lv))
        why[st] = why.get(st, 0) + 1
        if st == "ok" and (sym, d2) not in events:
            events[(sym, d2)] = {"L": float(lv), "d": d, "up": up}
    return events, why


# ══ ② الإشارة بعد الرجوع ══════════════════════════════════════════════════════════════════════════════════════════════════════════
def window_after(p, d2, sessions, hour_of):
    """⟵ (أوّلُ شمعةٍ تُغلق عند الإغلاق النظاميّ لـd′ أو بعده، آخرُ يومٍ في نافذة العشرين جلسة بعد d′)."""
    a = bisect.bisect_left(p["days4"], d2)
    while a < len(p["h4"]) and p["days4"][a] == d2 and hour_of(p["h4"][a][0]) + BAR_HOURS < CLOSE_HOUR:
        a += 1
    i2 = bisect.bisect_right(sessions, d2)
    end = sessions[min(len(sessions) - 1, i2 + WIN - 1)] if i2 < len(sessions) else d2
    return a, end


def signal_cross(p, d2, sessions, hour_of):
    """القراءةُ الحاكمة: أوّلُ تقاطعٍ معدود (`ema3.fire`) في النافذة بعد الرجوع ⟵ رقمُ شمعته أو None."""
    a, end = window_after(p, d2, sessions, hour_of)
    k = bisect.bisect_left(p["sigs"], a)
    c = p["sigs"][k] if k < len(p["sigs"]) else None
    return c if c is not None and p["days4"][c] <= end else None


def signal_state(p, d2, sessions, hour_of, st):
    """القراءةُ الحرفيّة (وصف): أوّلُ شمعةٍ في النافذة حالتُها «فوق» بعد التسخين ولو كان EMA9 فوقهما من قبل."""
    a, end = window_after(p, d2, sessions, hour_of)
    for i in range(max(a, E.WARMUP), len(p["h4"])):
        if p["days4"][i] > end:
            return None
        if st[i] == 1:
            return i
    return None


def return_entry(p, d2):
    """دخولُ `T-SUPPORT2` «افتتاحُ الجلسة التالية» بالمحرّك نفسِه: أوّلُ شمعةٍ يومُها بعد d′ ⟵ رقمُها أو None."""
    r = bisect.bisect_right(p["days4"], d2)
    return r if r < len(p["h4"]) else None


# ══ الإحصاء ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def boot_diff2(a, b, n=None, seed=None):
    """عيّنتان [(يوم، قيمة)] ⟵ فرقُ المتوسّطين وفاصلُه 95% بإعادة عيّنةٍ عنقوديّة بالأيّام (اتّحادُ أيّام المجموعتين)."""
    import numpy as np
    n, seed = E.BOOT_N if n is None else n, E.SEED if seed is None else seed
    a = [(c, float(v)) for c, v in a if v is not None]
    b = [(c, float(v)) for c, v in b if v is not None]
    out = {"n": len(a), "n_b": len(b), "days": len({c for c, _v in a}), "mean": None, "lo": None, "hi": None}
    if not a or not b:
        return out
    ks = sorted({c for c, _v in a} | {c for c, _v in b})
    ix = {k: i for i, k in enumerate(ks)}
    arr = np.zeros((4, len(ks)))
    for c, v in a:
        arr[0, ix[c]] += v
        arr[1, ix[c]] += 1
    for c, v in b:
        arr[2, ix[c]] += v
        arr[3, ix[c]] += 1
    rng = np.random.default_rng(seed)
    draw = rng.integers(0, len(ks), size=(n, len(ks)))
    s = arr[:, draw].sum(axis=2)
    with np.errstate(divide="ignore", invalid="ignore"):
        diff = s[0] / s[1] - s[2] / s[3]
    lo, hi = np.nanpercentile(diff, [2.5, 97.5])
    ma, mb = arr[0].sum() / arr[1].sum(), arr[2].sum() / arr[3].sum()
    out.update(mean=float(ma - mb), lo=float(lo), hi=float(hi), a_mean=float(ma), b_mean=float(mb))
    return out


def _rates(outs):
    """قائمةُ نتائج `ema3.outcome` ⟵ {n, r5.., tp30..}: المتوسّطُ والوسيطُ للعوائد · والنسبةُ للثنائيّات."""
    res = {"n": len(outs)}
    for k in E.REC_KEYS:
        v = [o[k] for o in outs if o is not None and o[k] is not None]
        if k.startswith("r"):
            res[k] = E._dist(v)
        else:
            res[k] = {"n": len(v), "rate": (sum(1 for x in v if x) / len(v)) if v else None}
    return res


# ══ الحساب ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def measure(P, members, events, sessions, hour_of, base_rows, lo=None, hi=None, keep=False):
    """الأحداث ⟵ العددُ والإشارةُ الثانية ومقارناتُها الثلاث (العقد §③-§④). `P` من `ema3.prep` · `base_rows` صفوفُ الإشارة الأولى المودَعة."""
    cache = {}

    def oc(s, i):
        if (s, i) not in cache:
            p = P[s]
            cache[(s, i)] = E.outcome(p["h4"], p["days4"], i, p["drows"], p["ddays"])
        return cache[(s, i)]

    def rows_for(pick):
        """pick(رمز، بنية، d′) ⟵ رقمُ شمعة الإشارة · يُرجع (الصفوف، عدّ)."""
        seen, recs, had, cnt = {}, [], set(), {"بلا شموع 4 ساعات": 0, "بلا إشارة في النافذة": 0, "خارج نافذة الجزء": 0, "مكرّرة": 0, "بلا شمعةٍ تالية": 0}
        for (s, d2) in sorted(events):
            p = P.get(s)
            if p is None:
                cnt["بلا شموع 4 ساعات"] += 1
                continue
            c = pick(s, p, d2)
            if c is None:
                cnt["بلا إشارة في النافذة"] += 1
                continue
            had.add((s, d2))
            dx = p["days4"][c]
            if (lo and dx < lo) or (hi and dx > hi):
                cnt["خارج نافذة الجزء"] += 1
                continue
            if (s, c) in seen:
                cnt["مكرّرة"] += 1
                continue
            if c + 1 >= len(p["h4"]):
                cnt["بلا شمعةٍ تالية"] += 1
                continue
            seen[(s, c)] = d2
            o = oc(s, c + 1)
            if o is None:
                continue
            t = p["h4"][c + 1][0]
            pool = E.pool_at(P, members.get(dx, ()), dx, t)
            pool.pop(s, None)
            mom = {}
            for q, j in list(pool.items()) + [(s, c + 1)]:
                m = E.momentum(P[q]["h4"], P[q]["days4"], j, P[q]["drows"], P[q]["ddays"])
                if m is not None:
                    mom[q] = m
            ctl = {q: oc(q, j) for q, j in pool.items()}
            ctl = {q: v for q, v in ctl.items() if v is not None}
            near = E.match(s, mom, [q for q in ctl if q in mom])
            r = return_entry(p, d2)
            ro = oc(s, r) if r is not None else None
            rec = {"sym": s, "d2": d2, "L": events[(s, d2)]["L"], "d": events[(s, d2)]["d"], "Dx": dx, "D0": o["D0"], "t": t,
                   "sig": {k: o[k] for k in E.REC_KEYS}, "ret": ({k: ro[k] for k in E.REC_KEYS} if ro else None),
                   "n_same": len(ctl), "n_match": len(near), "m": near}
            for name, grp in (("same", list(ctl)), ("match", near)):
                agg = {}
                for k in E.REC_KEYS:
                    v = [float(ctl[q][k]) for q in grp if ctl[q][k] is not None]
                    agg[k] = (sum(v) / len(v)) if v else None
                rec[name] = agg
            recs.append(rec)
        return recs, cnt, had

    recs, cnt, with_x = rows_for(lambda s, p, d2: signal_cross(p, d2, sessions, hour_of))
    st_cache = {}

    def pick_state(s, p, d2):
        if s not in st_cache:
            st_cache[s] = E.states([b[4] for b in p["h4"]])
        return signal_state(p, d2, sessions, hour_of, st_cache[s])

    recs_lit, cnt_lit, _had = rows_for(pick_state)
    gk = f"r{E.GOV_H}"
    full = [r for r in recs if r["sig"][gk] is not None]
    n20, days20 = len(full), len({r["D0"] for r in full})
    B, _g = E.table_b(recs)
    keys2 = {(r["sym"], r["t"]) for r in recs}
    base = [(r["D0"], r["sig"][gk]) for r in base_rows if (r["sym"], r["t"]) not in keys2]
    cells = {"ret": E.boot_ci([(r["D0"], r["sig"][gk] - r["ret"][gk]) for r in full if r["ret"] and r["ret"][gk] is not None]),
             "sig1": boot_diff2([(r["D0"], r["sig"][gk]) for r in full], base),
             "match": dict(B[gk]["match"])}
    enough = n20 >= E.MIN_SIG and days20 >= E.MIN_DAYS
    # وصف: الدخولُ عند الرجوع لكلّ الأحداث · ولمَن جاءه تقاطعٌ ومَن لم يأتِه
    ret_all, ret_x, ret_no = [], [], []
    for (s, d2) in sorted(events):
        p = P.get(s)
        if p is None:
            continue
        r = return_entry(p, d2)
        o = oc(s, r) if r is not None else None
        if o is None or (lo and o["D0"] < lo) or (hi and o["D0"] > hi):
            continue
        ret_all.append(o)
        (ret_x if (s, d2) in with_x else ret_no).append(o)
    Bl, _gl = E.table_b(recs_lit)
    out = {"counts": {"events": len(events), "events_bars": sum(1 for (s, _d) in events if s in P), "signals": len(recs), "skip": cnt,
                      "n20": n20, "days20": days20, "literal_signals": len(recs_lit), "literal_skip": cnt_lit,
                      "literal_same_bar": len(keys2 & {(r["sym"], r["t"]) for r in recs_lit})},
           "B": B, "cells": cells, "enough": bool(enough), "base_n": len(base),
           "ret_entry": {"all": _rates(ret_all), "with_cross": _rates(ret_x), "no_cross": _rates(ret_no)},
           "literal": {"sig": Bl[gk]["sig"], "match": Bl[gk]["match"], "same": Bl[gk]["same"], "tp30": Bl["tp30"]["sig"], "x100": Bl["x100"]["sig"]}}
    if keep:
        out["recs"] = recs
    return out


# ══ الحكم المنفرد (العقد §④ · نقيّة) ══════════════════════════════════════════════════════════════════════════════════════════════
CELL_NAMES = (("ret", "الدخول عند الرجوع بلا تقاطع (زوجيّ)"), ("sig1", "التقاطع بلا شرط القاع"), ("match", "ضابط الزخم المطابق"))


def _cells(j):
    return [{"k": k, "name": nm, "lo": ((j or {}).get("cells") or {}).get(k, {}).get("lo"), "hi": ((j or {}).get("cells") or {}).get(k, {}).get("hi")}
            for k, nm in CELL_NAMES]


def verdict(disc, conf):
    cd, cc = _cells(disc), _cells(conf)
    for c in cd + cc:
        c["ok"] = c["lo"] is not None and c["lo"] > 0
    res = {"disc": cd, "conf": cc, "pass": False}
    if not (disc or {}).get("enough"):
        res["verdict"] = "وصف لا حكم"
    elif not all(c["ok"] for c in cd):
        res["verdict"] = "لا تعبر"
    elif not (conf or {}).get("enough"):
        res["verdict"] = "وصف لا حكم"
    elif all(c["ok"] for c in cc):
        res["verdict"], res["pass"] = "تعبر", True
    else:
        res["verdict"] = "لا تعبر"
    return res


def predictions(disc, conf):
    def inc(c):
        return None if c.get("lo") is None else c["lo"] <= 0 <= c["hi"]

    def neg(j):
        m = j["B"][f"r{E.GOV_H}"]["sig"].get("mean")
        return None if m is None else m < 0

    both = [neg(disc), neg(conf)]
    return [("R1", "الإشاراتُ بنافذة 20 كاملة في 2026 دون 100", conf["counts"]["n20"] < E.MIN_SIG),
            ("R2", "في الاكتشاف: الفرقُ الزوجيّ عن الدخول عند الرجوع يشمل الصفر", inc(disc["cells"]["ret"])),
            ("R3", "في الاكتشاف: الفرقُ عن ضابط الزخم المطابق يشمل الصفر", inc(disc["cells"]["match"])),
            ("R4", "متوسّطُ عائد الإشارة الثانية عند 20 جلسة سالبٌ في الجزأين", None if None in both else all(both)),
            ("R5", "الحكم ليس «تعبر»", not verdict(disc, conf)["pass"])]


# ══ العرض ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def render(part, j):
    nm = {"discover": "الاكتشاف 2023-2025", "confirm": "التأكيد 2026"}[part]
    c, B, w = j["counts"], j["B"], j["why"]
    p, u = E._p, E._u
    L = [f"# 📈✖️③➕ «تقاطع إيما بعد اختبار القاع» — {nm}", "", "## العددُ أوّلًا", "",
         f"- أيّامُ القرار (رمز، يوم): {j['pairs']:,} · " + " · ".join(f"{k} {v:,}" for k, v in sorted(w.items())) + ".",
         f"- أحداثُ الرجوع الفريدة (رمز، d′): {c['events']:,} (بشموع 4 ساعات {c['events_bars']:,}) · **الإشاراتُ الفريدة: {c['signals']:,}** · "
         + " · ".join(f"{k} {v:,}" for k, v in c["skip"].items()) + ".",
         f"- بنافذة 20 كاملة: **{c['n20']:,} إشارة في {c['days20']:,} يومَ دخول** · الأرضيّة (100 و20) "
         f"{'مستوفاة' if j['enough'] else 'غيرُ مستوفاة ⟵ **وصفٌ لا حكم** لهذا الجزء'}.",
         f"- القراءةُ الحرفيّة (أوّلُ شمعةٍ «فوق» ولو بلا تقاطع): {c['literal_signals']:,} إشارة · منها على شمعة القراءة الحاكمة نفسِها {c['literal_same_bar']:,}.",
         "", "## الإشارةُ الثانية — بعد الدخول على افتتاح الشمعة التالية", "",
         "| الأفق | الإشارات | متوسّط العائد بعد الكلفة | الوسيط | الرابحون | الفرق عن الزخم المطابق [95%] | الفرق عن اليوم نفسه [95%] (وصف) |", "|---|---|---|---|---|---|---|"]
    for k in E.HORIZONS:
        x = B[f"r{k}"]
        L.append(f"| {k} جلسات | {x['sig'].get('n', 0):,} | {p(x['sig'].get('mean'))} | {p(x['sig'].get('median'))} | {u(x['sig'].get('win'))} | "
                 f"{p(x['match']['mean'])} [{p(x['match']['lo'])}، {p(x['match']['hi'])}] | {p(x['same']['mean'])} [{p(x['same']['lo'])}، {p(x['same']['hi'])}] |")
    L += ["", "| خلال 20 جلسة | الإشارة الثانية | ضابط الزخم | ضابط اليوم | الدخول عند الرجوع (كلّ الأحداث) |", "|---|---|---|---|---|"]
    ra = j["ret_entry"]["all"]
    for k, lab in (("tp30", "‏+30% قبل −10%"), ("tp50", "‏+50% قبل −10%"), ("x100", "بلغ ‏+100%")):
        x = B[k]
        L.append(f"| {lab} | {u(x['sig'].get('rate'))} (n={x['sig'].get('n', 0):,}) | {u(x['match']['ctl_mean'])} | {u(x['same']['ctl_mean'])} | {u(ra[k].get('rate'))} (n={ra[k].get('n', 0):,}) |")
    gk = f"r{E.GOV_H}"
    L += ["", "## المقارناتُ الثلاث (فرقُ متوسّط العائد بعد الكلفة عند 20 جلسة)", "", "| أمام | n | الفرق | الفاصل 95% | فوق الصفر؟ |", "|---|---|---|---|---|"]
    for k, nm2 in CELL_NAMES:
        x = j["cells"][k]
        ok = x.get("lo") is not None and x["lo"] > 0
        L.append(f"| {nm2} | {x.get('n', 0):,} | {p(x.get('mean'))} | [{p(x.get('lo'))}، {p(x.get('hi'))}] | {'✅' if ok else '❌'} |")
    re_ = j["ret_entry"]
    lit = j["literal"]
    L += ["", "## وصف", "",
          f"- الدخولُ عند الرجوع بلا تقاطع (كلُّ الأحداث · n={re_['all'][gk].get('n', 0):,}): متوسّط {p(re_['all'][gk].get('mean'))} · وسيط {p(re_['all'][gk].get('median'))}"
          f" — لمَن جاءه تقاطعٌ بعدها (n={re_['with_cross'][gk].get('n', 0):,}): {p(re_['with_cross'][gk].get('mean'))} · ولمَن لم يأتِه "
          f"(n={re_['no_cross'][gk].get('n', 0):,}): {p(re_['no_cross'][gk].get('mean'))}.",
          f"- صفوفُ الإشارة الأولى (بلا شرط القاع) في المقارنة: {j['base_n']:,}.",
          f"- القراءةُ الحرفيّة عند 20 جلسة (n={lit['sig'].get('n', 0):,}): متوسّط {p(lit['sig'].get('mean'))} · الفرق عن الزخم المطابق {p(lit['match']['mean'])} "
          f"[{p(lit['match']['lo'])}، {p(lit['match']['hi'])}] · ‏+30% قبل −10% {u(lit['tp30'].get('rate'))} · بلغ ‏+100% {u(lit['x100'].get('rate'))}.", ""]
    return "\n".join(L)


def render_verdict(disc, conf):
    v = verdict(disc, conf)
    L = ["# 📈✖️③➕ «تقاطع إيما بعد اختبار القاع» — الحكمُ المنفرد (الملحق 1 §④ · مسجَّلٌ بعد رؤية أرقام)", "",
         f"- الاكتشاف: {disc['counts']['n20']:,} إشارة بنافذة 20 كاملة في {disc['counts']['days20']:,} يومًا · الأرضيّة {'مستوفاة' if disc['enough'] else 'غيرُ مستوفاة'}.",
         f"- التأكيد: {conf['counts']['n20']:,} إشارة في {conf['counts']['days20']:,} يومًا · الأرضيّة {'مستوفاة' if conf['enough'] else 'غيرُ مستوفاة'}.", "",
         "| الجزء | أمام | فاصلُ فرق العائد عند 20 جلسة | فوق الصفر؟ |", "|---|---|---|---|"]
    for part, cs in (("الاكتشاف", v["disc"]), ("التأكيد", v["conf"])):
        for c in cs:
            L.append(f"| {part} | {c['name']} | [{E._p(c['lo'])}، {E._p(c['hi'])}] | {'✅' if c['ok'] else '❌'} |")
    L += ["", f"**الحكم: {v['verdict']}** ⟵ " + ("يُقترح وسمُ عرضٍ ويُنتظر قرارُ المالك · لا شيءَ يُشحن." if v["pass"]
                                               else "لا وسمَ يُقترح · والمحورُ يبقى مُغلَقًا بمفتاح `EMA3_REOPEN` · ولا محاولةَ ثانية."), "",
          "## التنبّؤات (§⑤)", "", "| # | التنبّؤ | النتيجة |", "|---|---|---|"]
    for k, txt, ok in predictions(disc, conf):
        L.append(f"| `{k}` | {txt} | {'—' if ok is None else ('✅ صدق' if ok else '❌ كذب')} |")
    return "\n".join(L) + "\n"


# ══ الأوضاع ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def mode_run(part, d_in):
    rc = guard(part)
    if rc:
        log(f"⛔ الحارس — خروج {rc}")
        return rc
    import Super_stock as S
    import tv_data as TV
    plan, bars_d, bars_h4 = E._load(d_in, "plan.pkl.gz"), E._load(d_in, "bars_d.pkl.gz"), E._load(d_in, "bars_h4.pkl.gz")
    base_path = os.path.join(E.OUT, BASE[part] + "_rows.json.gz")
    if not plan or not bars_d or not bars_h4 or not os.path.exists(base_path):
        log(f"⛔ المادّةُ ناقصة — خروج {E.RC_DATA}")
        return E.RC_DATA
    memo, hmemo = {}, {}

    def day_of(ts):
        if ts not in memo:
            memo[ts] = TV.ny_day(ts)
        return memo[ts]

    def hour_of(ts):
        if ts not in hmemo:
            hmemo[ts] = TV.ny_time(ts).hour
        return hmemo[ts]

    sessions, lo, hi = plan["sessions"], None, None
    if part == "discover":
        bars_d, bars_h4 = E.cut_blind(bars_d, day_of, E.D_BLIND), E.cut_blind(bars_h4, day_of, E.D_BLIND)
        sessions = [s for s in sessions if s <= E.D_BLIND]
        members, lo, hi = E.members_discover(plan["entries"], sessions), E.D_FROM, E.D_TO
    else:
        members, lo = E.members_confirm(sessions, plan["snap_days"]), E.C_FROM
    P = E.prep(bars_h4, bars_d, day_of)
    rows_by = {s: [(day_of(b[0]),) + tuple(b[1:6]) for b in v] for s, v in bars_d.items() if v}
    pairs = decision_days(part, plan)
    events, why = retests(pairs, rows_by, sessions, lambda hist: S2.level_of(hist, S))
    with gzip.open(base_path) as fh:
        base_rows = json.loads(fh.read().decode("utf-8"))
    res = measure(P, members, events, sessions, hour_of, base_rows, lo=lo, hi=hi, keep=True)
    recs = res.pop("recs")
    res.update(part=part, pairs=len(pairs), why=why, contract_sha=CONTRACT_SHA, src_run=SRC_RUNS[part])
    os.makedirs(E.OUT, exist_ok=True)
    with gzip.GzipFile(os.path.join(E.OUT, PARTS[part] + "_rows.json.gz"), "wb", mtime=0) as fh:
        fh.write(json.dumps(recs, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    md = render(part, res)
    with open(os.path.join(E.OUT, PARTS[part] + ".json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, sort_keys=True)
    with open(os.path.join(E.OUT, PARTS[part] + ".md"), "w", encoding="utf-8") as fh:
        fh.write(md)
    log(md)
    if part == "confirm":
        return mode_verdict()
    return E.RC_OK


def mode_verdict():
    js = []
    for nm in PARTS.values():
        path = os.path.join(E.OUT, nm + ".json")
        if not os.path.exists(path):
            log(f"⛔ {nm}.json لم يصدر — خروج {E.RC_ORDER}")
            return E.RC_ORDER
        with open(path, encoding="utf-8") as fh:
            js.append(json.load(fh))
    md = render_verdict(*js)
    with open(os.path.join(E.OUT, "RETEST_VERDICT.md"), "w", encoding="utf-8") as fh:
        fh.write(md)
    log(md)
    return E.RC_OK


def main(argv):
    if len(argv) >= 2 and argv[1] == "verdict":
        return mode_verdict()
    if len(argv) >= 3 and argv[1] == "run":
        if closed():
            log(f"🔒 الملحق 1 مُغلَقٌ مُنفَّذًا — الفتحُ إقرارُ المالك `EMA3_REOPEN=1` · خروج {E.RC_CLOSED}")
            return E.RC_CLOSED
        d_in = argv[argv.index("--dir") + 1] if "--dir" in argv else os.path.join(E.DATA, argv[2])
        return mode_run(argv[2], d_in)
    log(__doc__)
    return E.RC_DATA


if __name__ == "__main__":
    sys.exit(main(sys.argv))
