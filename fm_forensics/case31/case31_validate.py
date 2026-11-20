#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🗂️🔬 `T-CASE31` — التحقّقُ للخلف (العقد §⑥) لما ثُبِّت وحدَه · يرفض (خروج 9) بلا ملفّ تثبيتٍ ببصمته · مرّةً واحدة (7).

- بصماتُ الذراع أ ⟵ منفجرو «قبل الشهر» وضابطتُهم · وعلى 2023-2025 لما كان كلُّه من سمات `AB`.
- بصماتُ الذراع ب ⟵ صفوفُ 2026-09-29…2026-11-20 (النافذتان).
الحاكم: أدنى فاصل ويلسون 95% لنسبة الانفجار عند الحاملين فوق نسبة مجتمع التحقّق · ومتوسّطُ الربح بعد الكلفة موجبٌ وفوق غير الحاملين في أيّامهم.
الاستبعاد: حاملوه من المنفجرين 5% فأقلّ (أو واحدٌ فأقلّ إن قلّوا عن 20) ومن الضابطة 20% فأكثر. حاملون دون 20 ⟵ «لا قياس». قراءةٌ فقط.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (HERE, ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import case31 as C                      # noqa: E402
import case31_arm as A                  # noqa: E402
import case31_catalog as CAT            # noqa: E402
import case31_freeze as FZ              # noqa: E402
import case31_stats as ST               # noqa: E402

MIN_CARRIERS = 20
EXCL_POS, EXCL_NEG = 0.05, 0.20
COST = A.COST


def log(m=""):
    print(m, flush=True)


def _mean(xs):
    return (sum(xs) / len(xs)) if xs else None


def judge_print(conds, rows):
    """(نقيّة) بصمةٌ مثبَّتة على مجتمع تحقّق [{y, f, ret, day, src}] ⟵ {n, k, rate, base, wilson_lo, profit, profit_ctrl, losers, verdict, …}."""
    car = [r for r in rows if FZ.carries(conds, r["f"])]
    n, k = len(car), sum(r["y"] for r in car)
    npos = sum(r["y"] for r in rows)
    base = (npos / len(rows)) if rows else None
    out = {"n": n, "k": k, "pos_total": npos, "rows": len(rows), "base": base, "rate": (k / n) if n else None}
    if n < MIN_CARRIERS:
        return dict(out, verdict="لا قياس")
    days = {r["day"] for r in car}
    pr = [r["ret"] - COST for r in car if r.get("ret") is not None]
    ids = {id(r) for r in car}
    pc = [r["ret"] - COST for r in rows if r["day"] in days and id(r) not in ids and r.get("ret") is not None]
    lo = ST.wilson_lo(k, n)
    dd = [(r.get("src") or {}).get("dd_before") for r in car if r["y"] == 1]
    dd = [x for x in dd if x is not None]
    span = sorted(days)
    out.update(wilson_lo=lo, profit=_mean(pr), profit_ctrl=_mean(pc), losers=_mean([x < 0 for x in pr]), touch=(k / n),
               per_week=n / max(1.0, len(span) / 5.0), max_dd=min(dd) if dd else None, days=len(span))
    ok = (base is not None and lo > base and out["profit"] is not None and out["profit"] > 0
          and out["profit_ctrl"] is not None and out["profit"] > out["profit_ctrl"])
    return dict(out, verdict="✅ تثبت" if ok else "❌ لا تثبت")


def judge_excl(conds, rows):
    """(نقيّة) سمةُ استبعادٍ مثبَّتة ⟵ {pos_share, neg_share, verdict}: المنفجرون الحاملون 5% فأقلّ (أو واحدٌ فأقلّ دون 20) والضابطةُ 20% فأكثر."""
    pos, neg = [r for r in rows if r["y"] == 1], [r for r in rows if r["y"] == 0]
    cp, cn = sum(FZ.carries(conds, r["f"]) for r in pos), sum(FZ.carries(conds, r["f"]) for r in neg)
    out = {"pos": len(pos), "neg": len(neg), "pos_carry": cp, "neg_carry": cn, "pos_share": (cp / len(pos)) if pos else None,
           "neg_share": (cn / len(neg)) if neg else None}
    if cp + cn < MIN_CARRIERS or not pos or not neg:
        return dict(out, verdict="لا قياس")
    ok_pos = (cp <= 1) if len(pos) < 20 else (cp / len(pos) <= EXCL_POS)
    return dict(out, verdict="✅ يثبت" if (ok_pos and cn / len(neg) >= EXCL_NEG) else "❌ لا يثبت")


def ab_only(conds):
    ab = {n for n, _k, a in CAT.expanded() if a == "AB"}
    return all(c["f"] in ab for c in conds)


def populations(feat_a, feat_b):
    """مجتمعاتُ التحقّق: «قبل الشهر» (أ) · 2023-2025 (ب) · و2026 كاملةً (النافذتان) لبصمات الذراع ب."""
    pre = A.build_rows(feat_a, "قبل الشهر")[0] if feat_a else []
    month = A.build_rows(feat_a, "الشهر")[0] if feat_a else []
    old = A.build_rows(feat_b, "B")[0] if feat_b else []
    return {"قبل الشهر": pre, "2023-2025": old, "2026 (09-29…11-20)": pre + month}


def run(fz, pops):
    """(نقيّة) ملفُّ التثبيت والمجتمعات ⟵ [{arm, kind, texts, pop, …حكم}] بقاعدة العقد: أ ⟵ قبل الشهر و2023-2025 (لـAB) · ب ⟵ 2026."""
    out = []
    for arm, sel in sorted((fz.get("arms") or {}).items()):
        for kind, items, fn in (("بصمة", sel.get("prints") or [], judge_print), ("استبعاد", sel.get("excl") or [], judge_excl)):
            for it in items:
                targets = ["قبل الشهر"] + (["2023-2025"] if ab_only(it["conds"]) else []) if arm == "A" else ["2026 (09-29…11-20)"]
                for pn in targets:
                    rows = pops.get(pn) or []
                    res = fn(it["conds"], rows) if rows else {"verdict": "لا قياس — المجتمعُ غائب"}
                    out.append(dict(res, arm=arm, kind=kind, texts=it["texts"], pop=pn))
    return out


def report(res):
    pct = lambda x: "—" if x is None else f"{x * 100:.1f}%"      # noqa: E731
    L = ["# ✅ `T-CASE31` — التحقّقُ للخلف لما ثُبِّت (مولَّدٌ آليًّا · لا يُعدَّل باليد)", "",
         "## البصمات", "", "| الذراع | البصمة | مجتمعُ التحقّق | الحاملون | منفجرون منهم | النسبة | أدنى ويلسون | نسبةُ المجتمع | الربح بعد الكلفة | ربحُ غير الحاملين | الخاسرون | الحكم |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in res:
        if r["kind"] == "بصمة":
            L.append(f"| {r['arm']} | `{' + '.join(r['texts'])}` | {r['pop']} | {r.get('n', '—')} | {r.get('k', '—')} | {pct(r.get('rate'))} | {pct(r.get('wilson_lo'))} | "
                     f"{pct(r.get('base'))} | {pct(r.get('profit'))} | {pct(r.get('profit_ctrl'))} | {pct(r.get('losers'))} | **{r['verdict']}** |")
    L += ["", "## سماتُ الاستبعاد", "", "| الذراع | السمة | مجتمعُ التحقّق | المنفجرون الحاملون | الضابطةُ الحاملة | الحكم |", "|---|---|---|---|---|---|"]
    for r in res:
        if r["kind"] == "استبعاد":
            L.append(f"| {r['arm']} | `{' + '.join(r['texts'])}` | {r['pop']} | {r.get('pos_carry', '—')} من {r.get('pos', '—')} ({pct(r.get('pos_share'))}) | "
                     f"{r.get('neg_carry', '—')} من {r.get('neg', '—')} ({pct(r.get('neg_share'))}) | **{r['verdict']}** |")
    ok = [r for r in res if r["kind"] == "بصمة" and r["verdict"] == "✅ تثبت"]
    L += ["", "## لكلّ بصمةٍ تثبت", ""]
    for r in ok:
        L.append(f"- `{' + '.join(r['texts'])}` ({r['pop']}): إشاراتٌ في الأسبوع {r['per_week']:.1f} · أقصى نزولٍ قبل الانفجار {pct(r.get('max_dd'))} · الخاسرون {pct(r.get('losers'))} · "
                 f"اللمس (وصف) {pct(r.get('touch'))}")
    if not ok:
        L.append("- لا بصمةَ تثبت.")
    return "\n".join(L) + "\n"


def mode_validate(d_a, d_b):
    fz = FZ.load_freeze()
    if fz is None:
        log(f"⛔ لا ملفَّ تثبيتٍ ببصمته — خروج {C.RC_FREEZE}")
        return C.RC_FREEZE
    out_md = os.path.join(C.OUT, "VALIDATE.md")
    if os.path.exists(out_md):
        log(f"⛔ التحقّقُ صادر — لا محاولةَ ثانية · خروج {C.RC_ONCE}")
        return C.RC_ONCE
    fa = A.load_feat(d_a) if d_a and os.path.isdir(d_a) else []
    fb = A.load_feat(d_b) if d_b and os.path.isdir(d_b) else []
    pops = populations(fa, fb)
    res = run(fz, pops)
    os.makedirs(C.OUT, exist_ok=True)
    with open(out_md, "w", encoding="utf-8") as fh:
        fh.write(report(res))
    with open(os.path.join(C.OUT, "validate.json"), "w", encoding="utf-8") as fh:
        json.dump([{k: v for k, v in r.items()} for r in res], fh, ensure_ascii=False, indent=1)
    log(report(res))
    return C.RC_OK


def main(argv):
    if not C.contract_ok():
        return C.RC_CONTRACT
    if len(argv) > 1 and argv[1] == "validate":
        d_a = argv[argv.index("--feat") + 1] if "--feat" in argv else ""
        d_b = argv[argv.index("--featb") + 1] if "--featb" in argv else ""
        return mode_validate(d_a, d_b)
    log("الاستعمال: case31_validate.py validate --feat <سماتُ أ> --featb <سماتُ ب>")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
