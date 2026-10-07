# -*- coding: utf-8 -*-
"""
📜 FAISAL V4.1 — مصدريّةُ قواعد V4 (§3 · العقد `V41_prereg.md` §④): سجلٌّ بالحقول العشرين لكلّ قاعدةٍ في السجلّ المجمَّد
وحالةُ دليلٍ **بمسطرةٍ آليّةٍ مستقلّةٍ عن الأداء** (لا تقرأ نتائجَ تقييمٍ ولا ذهبيّةً ولا مصفوفاتٍ — قفل FV49 بالـAST).

المدخلات (مجمَّدةٌ كلُّها · FV41): `rules_v4.RULES_V4` · `decision_engine` (PARAMS · STATE_RULE · المصدر) · المرورُ البصريّ (`v4_cases.load_records`
· `v4_cases.tier`) · `image_corpus.json` (عناقيدُ النسخ) · `mutations_v4.json` (أسماءُ الطفرات) · ونصُّ `test_bot.py` (هل اختُبرت).
المخرَج: `docs/V4_RULE_PROVENANCE.json` (مولَّدٌ · لا يُحرَّر).
"""
import ast
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
V4 = os.path.join(ROOT, "faisal_method_v4")
for _p in (V4, os.path.join(ROOT, "faisal_method_v3"), HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import decision_engine as E      # noqa: E402 — مجمَّد
import rules_v4 as RV            # noqa: E402 — مجمَّد
import v4_cases as VC            # noqa: E402 — مجمَّد

OUT = os.path.join(HERE, "docs", "V4_RULE_PROVENANCE.json")
CORPUS = os.path.join(ROOT, "faisal_method_v3", "image_corpus.json")
MUTS = os.path.join(V4, "results", "mutations_v4.json")
TESTS = os.path.join(ROOT, "test_bot.py")
ENGINE_SRC = os.path.join(V4, "decision_engine.py")
RUBRIC_VERSION = "V41-RUBRIC 1.0 (V41_prereg §④)"
STATUSES = ("CONFIRMED", "SUPPORTED", "PROBABLE", "POSSIBLE", "CONTRADICTED", "UNKNOWN")
TOKEN = re.compile(r"[A-Za-z0-9_]+")

# مفاتيحُ السياق التي تقرؤها قاعدةُ صلاحيّة (لربط الطفرات بها — «مفاتيحُها» في العقد §④)
CONTEXT_KEYS = {"R4-VAL-GRP-01": ("groups",), "R4-VAL-OFF-01": ("offering",), "R4-VAL-SHORT-01": ("short",),
                "R4-OP-01": ("operator",)}
# حدودُ صدقٍ معروفةٌ قبل الرقم لكلّ قاعدة (وصفٌ · لا تغيّر حالةً)
EXTRA_LIMITS = {
    "R4-OP-01": "CR-01: `operator_press = False` يُعامَل معلومةً مكتملةً لا تمنع (ملتبس · لا يُصلح) · ولا مصدرَ للبصمة بعد Polygon ⟵ `None` دائمًا ⟵ READY مستحيلٌ عمليًّا",
    "R4-VAL-GRP-01": "لا مصدرَ نقطيٌّ لدخول القروبات ⟵ `None` دائمًا في التحقّق",
    "R4-VAL-OFF-01": "لا تعريفَ آليٌّ مُتحقَّقٌ لـ«طرحٍ معلَّق» وقتَ النقطة ⟵ `None` في التحقّق الأماميّ",
    "R4-VAL-SHORT-01": "«المتاح» من حصّاد الاقتراض (ChartExchange) لرموز الحصّاد وحدَها · وغيرُها `None`",
    "R4-TF-01": "المحرّكُ يوميٌّ وحدَه — صورُ فيصل على 4 ساعات/30 دقيقة تُقارن بقراءةٍ يوميّة",
    "R4-DATA-01": "قاعدةٌ هندسيّة (ليست دعوى عن فيصل)",
}


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def corpus_units():
    """معرّفُ كلِّ صورةٍ في المدوّنة (722) ⟵ معرّفُ وحدتها في المرور البصريّ (ممثّلُ عنقودها)."""
    imgs = _load_json(CORPUS)["images"]
    recs = {r["id"]: r for r in VC.load_records()}
    by_cluster = {}
    for i in imgs:
        if i.get("dup_cluster") and i["id"] in recs:
            by_cluster[i["dup_cluster"]] = i["id"]
    unit = {}
    for i in imgs:
        cid = i.get("dup_cluster")
        unit[i["id"]] = i["id"] if i["id"] in recs else by_cluster.get(cid, i["id"])
    return unit, recs


def ids_in(obj, known):
    """كلُّ معرّفٍ من المدوّنة يرد رمزًا كاملًا في نصّ/قائمة (مطابقةٌ حرفيّة · لا تخمين)."""
    txt = json.dumps(obj, ensure_ascii=False) if not isinstance(obj, str) else obj
    return sorted({t for t in TOKEN.findall(txt) if t in known})


def unit_tier(uid, recs):
    r = recs.get(uid)
    return VC.tier(r.get("a"), r.get("ab")) if r else "X"


def rubric(source_level, source, n1, n2, c1, cited_any):
    """مسطرةُ العقد §④ بترتيبها — الحالةُ ووسمُ «هندسيّة»."""
    eng = (source_level >= 6 or "engineering" in (source or "").lower()) and not cited_any
    if eng:
        return "UNKNOWN", True
    if c1 >= 1 and c1 >= n1:
        return "CONTRADICTED", False
    if n1 >= 3 and c1 == 0:
        return "CONFIRMED", False
    if n1 >= 2:
        return "SUPPORTED", False
    if n1 == 1:
        return "PROBABLE", False
    if n2 >= 1:
        return "POSSIBLE", False
    return "UNKNOWN", False


def _engine_functions_mentioning(rid, src):
    tree = ast.parse(src)
    out = []
    for n in tree.body:
        if isinstance(n, ast.FunctionDef):
            seg = ast.get_source_segment(src, n) or ""
            if rid in seg:
                out.append(n.name)
    return out


def build():
    unit, recs = corpus_units()
    known = set(unit)
    engine_src = open(ENGINE_SRC, encoding="utf-8").read()
    tests_src = open(TESTS, encoding="utf-8").read()
    muts = [m["mutation"] for m in _load_json(MUTS)["rows"]]
    param_of = {}
    for k, v in E.PARAMS.items():
        rid = (v[2] or "").split(":")[0].strip()
        param_of.setdefault(rid, []).append(k)
    states_of = {}
    for st, rid in E.STATE_RULE.items():
        states_of.setdefault(rid, []).append(st)
    rows = []
    for rid in sorted(RV.RULES_V4):
        r = RV.RULES_V4[rid]
        prim = ids_in(r.get("image_ids") or [], known)
        sup = ids_in(r.get("supporting") or [], known)
        con = ids_in(r.get("contradicting") or [], known)
        wit = ids_in(r.get("golden_witness") or [], known)
        sup_units = sorted({unit[x] for x in prim + sup})
        con_units = sorted({unit[x] for x in con})
        n1 = len({u for u in sup_units if unit_tier(u, recs) == "1"})
        n2 = len({u for u in sup_units if unit_tier(u, recs) in ("2", "2b")})
        c1 = len({u for u in con_units if unit_tier(u, recs) == "1"})
        c2 = len({u for u in con_units if unit_tier(u, recs) in ("2", "2b")})
        status, eng = rubric(r["source_level"], r.get("source"), n1, n2, c1, bool(sup_units or con_units))
        keys = param_of.get(rid, []) + states_of.get(rid, []) + list(CONTEXT_KEYS.get(rid, ()))
        toks = [rid] + keys + [k.replace("_PCT", "") for k in param_of.get(rid, [])]
        mut_hits = sorted({m for m in muts if any(t and t in m for t in toks)})
        tested = rid in tests_src or any(k in tests_src for k in param_of.get(rid, []))
        impl_fns = _engine_functions_mentioning(rid, engine_src)
        implemented = (rid in engine_src) and bool(r.get("active"))
        cited = sorted(set(prim + sup + con + wit))
        rows.append({
            "RULE_ID": rid,
            "DESCRIPTION": r.get("description"),
            "SOURCE_LEVEL": r.get("source_level"),
            "PRIMARY_SOURCE_IDS": prim,
            "SUPPORTING_SOURCE_IDS": [x for x in sup if x not in prim],
            "CONTRADICTORY_SOURCE_IDS": con,
            "GOLDEN_WITNESS_IDS": wit,
            "AUTHOR": r.get("author"),
            "DIRECTLY_OBSERVED": r.get("source_level") in (1, 3),
            "INFERRED": r.get("source_level") not in (1, 3),
            "IMPLEMENTED": implemented,
            "TESTED": tested,
            "MUTATION_LOCK": mut_hits,
            "DECISIONALITY": r.get("decisionality"),
            "EVIDENCE_STATUS": status,
            "REGISTRY_STATUS": r.get("status"),
            "STATUS_DIFFERS": status != r.get("status"),
            "ENGINEERING": eng,
            "COUNTS": {"n1": n1, "n2": n2, "c1": c1, "c2": c2, "support_units": len(sup_units), "contra_units": len(con_units)},
            "DISCOVERY_DATASET": cited,
            "VALIDATION_DATASET": [],
            "HOLDOUT_DATASET": [],
            "BACKTEST_DERIVED": bool(r.get("backtest_derived")),
            "CURRENT_IMPLEMENTATION": {"engine_functions": impl_fns, "params": param_of.get(rid, []),
                                       "states": states_of.get(rid, []), "active": bool(r.get("active")),
                                       "superseded_by": r.get("superseded_by")},
            "KNOWN_LIMITATIONS": [x for x in [r.get("effect"), EXTRA_LIMITS.get(rid)] if x]
                                 + [f"تناقض: {c}" for c in (r.get("contradicting") or [])],
        })
    order = {s: i for i, s in enumerate(STATUSES)}
    summary = {
        "rules": len(rows), "active": sum(1 for x in rows if x["CURRENT_IMPLEMENTATION"]["active"]),
        "audit_status": {s: sum(1 for x in rows if x["EVIDENCE_STATUS"] == s) for s in STATUSES},
        "registry_status": {s: sum(1 for x in rows if x["REGISTRY_STATUS"] == s) for s in STATUSES},
        "differs": [x["RULE_ID"] for x in rows if x["STATUS_DIFFERS"]],
        "registry_stronger": [x["RULE_ID"] for x in rows if x["STATUS_DIFFERS"]
                              and order.get(x["REGISTRY_STATUS"], 9) < order.get(x["EVIDENCE_STATUS"], 9)],
        "cited_units_all": len({u for x in rows for u in x["DISCOVERY_DATASET"]}),
    }
    return {"generated_by": "faisal_method_v41/provenance.py", "rubric": RUBRIC_VERSION, "rules": rows, "summary": summary}


def cited_units():
    """وحداتُ المرور البصريّ المستشهَدُ بها في أيّ حقلٍ من السجلّ (لتصنيف التلوّث · §⑤) — بعنقودها."""
    unit, _ = corpus_units()
    known = set(unit)
    out = set()
    for r in RV.RULES_V4.values():
        for f in ("image_ids", "supporting", "contradicting", "golden_witness", "params", "description", "effect", "source"):
            out |= {unit[x] for x in ids_in(r.get(f) or "", known)}
    return out


def write(obj=None):
    obj = obj or build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    return obj


if __name__ == "__main__":
    o = write()
    print(json.dumps(o["summary"], ensure_ascii=False))
