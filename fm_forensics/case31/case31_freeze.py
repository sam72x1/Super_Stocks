#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🗂️🔬 `T-CASE31` — ملفُّ التثبيت (العقد §⑥): أفضلُ 3 بصمات وأفضلُ 3 سمات استبعاد لكلّ ذراعٍ **ممّا عبر الخلطَ وحدَه**.

يقرأ `out/armA.json.gz` و`out/armB.json.gz` (ما صدر منهما) ⟵ `data/case31_freeze.json` بالعتبات الرقميّة. صفرُ عابرٍ ⟵ لا ملفَّ ولا تحقّق.
الاختيارُ حتميّ: بالدرجة ثمّ الأقصر ثمّ الاسم · وتُتخطّى بصمةٌ تشارك مثبَّتةً شرطين. قراءةٌ فقط — لا يُعدَّل بعد الدمج (بصمتُه في `case31.FREEZE_SHA`).
"""
import gzip
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (HERE, ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import case31 as C                      # noqa: E402

TOP = 3                                 # من المالك: أفضلُ 3 بصمات و3 سمات استبعاد
FREEZE = os.path.join(HERE, "data", "case31_freeze.json")


def log(m=""):
    print(m, flush=True)


def parse_cond(text, thr):
    """(نقيّة) نصُّ الشرط وعتبتُه ⟵ {f, op, v}: «اسم=1/0» منطقيّ · «اسم<qNN» دون العتبة · «اسم>qNN» فوقها."""
    if text.endswith("=1") or text.endswith("=0"):
        return {"f": text[:-2], "op": "==", "v": int(text[-1]), "text": text}
    for op in ("<q", ">q"):
        if op in text:
            return {"f": text.rsplit(op, 1)[0], "op": op[0], "v": float(thr), "text": text}
    raise ValueError(text)


def holds(cond, f):
    """(نقيّة) هل يتحقّق الشرطُ المثبَّت على صفّ سمات (`.get`)؟ المجهولُ ⟵ None (لا يُحسب حاملًا)."""
    v = f.get(cond["f"])
    if v is None:
        return None
    if cond["op"] == "==":
        return bool(v) == bool(cond["v"])
    return (v < cond["v"]) if cond["op"] == "<" else (v > cond["v"])


def carries(conds, f):
    """(نقيّة) يحمل الصفُّ التوليفةَ ⟸ كلُّ شروطها متحقّقة · وأيُّ مجهولٍ ⟵ لا يحمل."""
    return all(holds(c, f) is True for c in conds)


def select(arm):
    """(نقيّة) نتيجةُ ذراعٍ (`arm?.json.gz`) ⟵ {prints, excl, p95_print, p95_excl}: العابرُ وحدَه (فوق المئين 95 لأقصى الخلطات) بالترتيب الحتميّ."""
    ver = (arm.get("summary") or {}).get("verdict") or {}
    p95p, p95e = (ver.get("best_print") or {}).get("p95"), (ver.get("best_excl") or {}).get("p95")
    thr = arm.get("thresholds") or {}
    cands = [{"conds": [t["cond"]], "z": t["z"], "k": t["k"], "n": t["n"]} for t in arm.get("top_singles") or []]
    cands += [{"conds": list(t["conds"]), "z": t["z"], "k": t["k"], "n": t["n"]} for t in arm.get("top_combos") or []]
    cands = [c for c in cands if p95p is not None and c["z"] is not None and c["z"] > p95p]
    cands.sort(key=lambda c: (-c["z"], len(c["conds"]), "+".join(sorted(c["conds"]))))
    prints = []
    for c in cands:
        if any(len(set(c["conds"]) & set(p["texts"])) >= 2 for p in prints) or any(set(c["conds"]) == set(p["texts"]) for p in prints):
            continue
        prints.append({"texts": sorted(c["conds"]), "conds": [parse_cond(t, thr.get(t)) for t in sorted(c["conds"])], "z": c["z"], "k": c["k"], "n": c["n"]})
        if len(prints) == TOP:
            break
    ex = [e for e in arm.get("exclusions") or [] if p95e is not None and e["removes"] > p95e]
    ex.sort(key=lambda e: (-e["removes"], e["cond"]))
    excl = [{"texts": [e["cond"]], "conds": [parse_cond(e["cond"], thr.get(e["cond"]))], "removes": e["removes"], "pos_share": e["pos_share"]} for e in ex[:TOP]]
    return {"prints": prints, "excl": excl, "p95_print": p95p, "p95_excl": p95e}


def build_freeze(arms):
    """(نقيّة) {ذراع: نتيجتُها} ⟵ محتوى ملفّ التثبيت أو None عند صفر عابر."""
    out = {"contract_sha": C.CONTRACT_SHA, "catalog_sha": C.CATALOG_SHA, "arms": {}}
    for a in sorted(arms):
        sel = select(arms[a])
        if sel["prints"] or sel["excl"]:
            out["arms"][a] = sel
    return out if out["arms"] else None


def freeze_sha(path=FREEZE):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest()
    except OSError:
        return None


def load_freeze():
    """ملفُّ التثبيت ببصمته في `case31.FREEZE_SHA` أو None (غائبٌ أو لا يطابق ⟵ خروج 9 عند مناديه)."""
    want = getattr(C, "FREEZE_SHA", None)
    if not want or freeze_sha() != want:
        return None
    return json.load(open(FREEZE, encoding="utf-8"))


def mode_build():
    arms = {}
    for a in ("A", "B"):
        p = os.path.join(C.OUT, f"arm{a}.json.gz")
        if os.path.exists(p):
            with gzip.open(p, "rt", encoding="utf-8") as fh:
                arms[a] = json.load(fh)
    if not arms:
        log(f"⛔ لا نتيجةَ ذراعٍ بعد — خروج {C.RC_DATA}")
        return C.RC_DATA
    if os.path.exists(FREEZE):
        log(f"⛔ ملفُّ التثبيت قائم — لا يُعاد بناؤه · خروج {C.RC_ONCE}")
        return C.RC_ONCE
    fz = build_freeze(arms)
    if fz is None:
        log("🧊 صفرُ عابرٍ في الأذرع الصادرة (" + " · ".join(sorted(arms)) + ") ⟵ لا تثبيتَ ولا تحقّق (العقد §⑥)")
        return C.RC_OK
    os.makedirs(os.path.dirname(FREEZE), exist_ok=True)
    with open(FREEZE, "w", encoding="utf-8") as fh:
        json.dump(fz, fh, ensure_ascii=False, indent=1, sort_keys=True)
    log("🧊 ثُبِّت: " + " · ".join(f"{a}: بصمات {len(v['prints'])} واستبعاد {len(v['excl'])}" for a, v in fz["arms"].items()) + f" · البصمة {freeze_sha()}")
    return C.RC_OK


def main(argv):
    if not C.contract_ok():
        return C.RC_CONTRACT
    if len(argv) > 1 and argv[1] == "build":
        return mode_build()
    log("الاستعمال: case31_freeze.py build")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
