# -*- coding: utf-8 -*-
"""سجلُّ القواعد القابل للقراءة آليًّا (FAISAL_RULE_LEDGER.json/.csv) — من `rules_v4.RULES_V4` المجمَّدة + قواعدِ مراحل المحرّك،
بصنف الدليل الذي طلبه المالك: DIRECTLY_OBSERVED · REPEATEDLY_SUPPORTED · INFERRED · CONTRADICTED · UNRESOLVED.
كلُّ معرّفِ صورةٍ يُفحَص في جرد المدوّنة (MASTER_CORPUS_INVENTORY) ⟵ `image_in_corpus`. قراءةٌ فقط."""
import ast
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (os.path.join(ROOT, "faisal_method_v4"), os.path.join(ROOT, "faisal_method_v3")):
    sys.path.insert(0, _p)
import rules_v4 as RV          # noqa: E402

EVIDENCE_CLASS = {"CONFIRMED": "DIRECTLY_OBSERVED", "SUPPORTED": "REPEATEDLY_SUPPORTED", "PROBABLE": "INFERRED",
                  "CONTRADICTED": "CONTRADICTED", "UNKNOWN": "UNRESOLVED"}
DIMENSION = {"R4-DATA-01": "DATA", "R4-BOT-01": "CHART", "R4-HOLD-01": "TEMPORAL", "R4-CYC-01": "CHART", "R4-ZONE-01": "RISK",
             "R4-HOLDZ-01": "TEMPORAL", "R4-SWEEP-01": "CHART", "R4-INV-01": "RISK", "R4-LOC-01": "TEMPORAL", "R4-OP-01": "TEMPORAL",
             "R4-VAL-GRP-01": "SELECTION", "R4-VAL-OFF-01": "SELECTION", "R4-VAL-SHORT-01": "SELECTION", "R4-ENT-01": "RISK",
             "R4-ENT-02": "RISK", "R4-STOP-01": "RISK", "R4-TGT-01": "RISK", "R4-TF-01": "CHART", "R-W-SPAN": "CHART",
             "R-SUP-MAIN": "CHART", "H-D2": "CHART"}
ENGINE_RULES = [
    dict(rule_id="FE-DATA-01", dimension="DATA", description="40 جلسةً يوميّةً فأكثر قبل تاريخ القراءة وإلّا INSUFFICIENT_DATA (= R4-DATA-01)",
         status="CONFIRMED", decisionality="DECISIONAL", image_ids=[], supporting=["V4 PARAMS MIN_BARS (engineering)"], contradicting=[], source_tag="engineering"),
    dict(rule_id="FE-SCREEN-01", dimension="SELECTION", description="هُويّةُ الارتكاز = بوّاباتُ الفارز الإنتاجيّ المجمَّد (M1-M5 · RSI · النواقص) **بلا جدار اللمستين** (REMOVE_candidate · المرحلة 4)",
         status="SUPPORTED", decisionality="DECISIONAL", image_ids=["IMG_0151", "IMG_0143", "TG_50584"],
         supporting=["Phase 3: الجدارُ الأوّل مرساةُ اللمستين 20/53 · لمساتُها 0 في 20/20", "Phase 4: اللمستان لا تقعان على 32/38 من مستويات فيصل"],
         contradicting=["Phase 4: الضوابطُ المطابَقة تُظهر التسلسلَ نفسَه (0.94/1.00) — الوعاءُ ضروريٌّ لا مُميِّز"], source_tag="inferred"),
    dict(rule_id="FE-FRAME-01", dimension="SELECTION", description="بعد تقسيمٍ عكسيٍّ داخل نافذة الدورة تُقرأ الهُويّةُ أيضًا على إطار ما بعد التقسيم (بعمقٍ 40 جلسة) ويمرّ السهم إن مرّ أحدُ الإطارين",
         status="PROBABLE", decisionality="DECISIONAL", image_ids=["IMG_0143", "IMG_0151", "IMG_0150"],
         supporting=["Phase 2: سقفُ M2 على SXTC/HUBC أثرُ تراكم التسوية · مستوى 4: تعريفاتُ البوّابات على النظام المسوّى مقابل إطار فيصل بعد التقسيم"],
         contradicting=["Phase 2: تصحيحُ السقف لا يصنع ترشيحًا لأيّ مِرساة ويُسقط 33 من 56 ضابطًا سالبًا"], source_tag="inferred"),
    dict(rule_id="FE-STAGE-01", dimension="TEMPORAL", description="الحالةُ الفنيّة في V4 ⟵ المرحلةُ الزمنيّة: BASE_FORMING/BROKEN_NEW_BASE ⟵ FOCUS · SWEEP_ACTIVE/RETEST_* ⟵ WATCH · TECH_READY ⟵ READY · والضغطُ المعلوم ⟵ TRIGGER",
         status="PROBABLE", decisionality="DECISIONAL", image_ids=["X_20260918_85_YMT", "IMG_0531", "TG_50584"],
         supporting=["FAISAL_STATE_MACHINE.md (FOCUS→WATCH→READY→TRIGGERED)", "Phase 3: فيصل يراقب عند اللمسة الأولى لقاعٍ غيرِ مُختبَر (13 قبل إعادة الاختبار مقابل 8 بعدها)"],
         contradicting=["Phase 4: H1 مكذَّبة — اللمسةُ الأولى الحديثة لا ترفع احتمالَ انتباهه (1.12×)"], source_tag="inferred"),
    dict(rule_id="FE-VAL-FLOAT-01", dimension="SELECTION", description="الفلوتُ 5 ملايين أو أقلّ شرطُ صلاحيّة؛ وغيابُه UNKNOWN لا رفض",
         status="SUPPORTED", decisionality="DECISIONAL", image_ids=["IMG_0150", "IMG_9510"], supporting=["H6 §3 A (faisal_adopted)", "T-HS-SF FWD_FLOAT_MAX"],
         contradicting=["Phase 5: NOT TESTABLE تاريخيًّا (5/23)"], source_tag="faisal_adopted"),
    dict(rule_id="FE-UNKNOWN-01", dimension="DATA", description="المعلومةُ الغائبة (فلوت · متاح · قروبات · ضغط · طرح بلا سجلّ) تُسجَّل UNKNOWN وتمنع READY المُتحقَّق ولا تُستنتَج «لا»",
         status="CONFIRMED", decisionality="DECISIONAL", image_ids=[], supporting=["FVO1 (V4.1): لا READY ولا REJECT بلا مصدر"], contradicting=[], source_tag="engineering"),
]


def _lst(v):
    if isinstance(v, (list, tuple)):
        return list(v)
    try:
        return list(ast.literal_eval(str(v)))
    except Exception:            # noqa: BLE001
        return [str(v)] if v else []


def corpus_ids():
    p = os.path.join(ROOT, "faisal_method_v41", "corpus_audit", "MASTER_CORPUS_INVENTORY.json")
    inv = json.load(open(p, encoding="utf-8"))
    rows = inv["rows"] if isinstance(inv, dict) and "rows" in inv else inv
    ids = set()
    for r in rows:
        ids.add(str(r.get("IMAGE_ID")))
    return ids


def build():
    ids = corpus_ids()
    out = []
    for rid, r in RV.RULES_V4.items():
        imgs = _lst(r.get("image_ids"))
        out.append(dict(rule_id=rid, dimension=DIMENSION.get(rid, "CHART"), description=r.get("description", ""), status=r.get("status"),
                        evidence_class=EVIDENCE_CLASS.get(r.get("status"), "UNRESOLVED"), decisionality=r.get("decisionality"),
                        source_tag=r.get("source", ""), image_ids=imgs, image_in_corpus=sum(1 for i in imgs if i in ids),
                        supporting=_lst(r.get("supporting")), contradicting=_lst(r.get("contradicting")), origin="rules_v4 " + RV.VERSION,
                        engine_use=("stage mapping" if rid in ("R4-HOLD-01", "R4-SWEEP-01", "R4-HOLDZ-01", "R4-LOC-01", "R4-INV-01", "R4-OP-01") else
                                    "validity" if rid.startswith("R4-VAL") else "levels/informational")))
    for r in ENGINE_RULES:
        imgs = r["image_ids"]
        out.append(dict(rule_id=r["rule_id"], dimension=r["dimension"], description=r["description"], status=r["status"],
                        evidence_class=EVIDENCE_CLASS[r["status"]], decisionality=r["decisionality"], source_tag=r["source_tag"], image_ids=imgs,
                        image_in_corpus=sum(1 for i in imgs if i in ids), supporting=r["supporting"], contradicting=r["contradicting"],
                        origin="faisal_engine (2026-10-09)", engine_use="stage"))
    return out


def write(out_dir=None):
    out_dir = out_dir or HERE
    rows = build()
    json.dump({"version": "FAISAL_RULE_LEDGER 1.0 (2026-10-09)", "rules_v4": RV.VERSION, "n": len(rows), "rules": rows},
              open(os.path.join(out_dir, "FAISAL_RULE_LEDGER.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    keys = ["rule_id", "dimension", "evidence_class", "status", "decisionality", "source_tag", "engine_use", "image_in_corpus", "image_ids", "description"]
    with open(os.path.join(out_dir, "FAISAL_RULE_LEDGER.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
        for r in rows:
            w.writerow({k: ("|".join(r[k]) if isinstance(r[k], list) else r[k]) for k in keys})
    return rows


if __name__ == "__main__":
    rows = write()
    from collections import Counter
    print(len(rows), Counter(r["evidence_class"] for r in rows), "images not in corpus:", [(r["rule_id"], len(r["image_ids"]) - r["image_in_corpus"]) for r in rows if len(r["image_ids"]) - r["image_in_corpus"]])
