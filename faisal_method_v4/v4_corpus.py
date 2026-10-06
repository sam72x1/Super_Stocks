# -*- coding: utf-8 -*-
"""
🧭 FAISAL V4 — مطابقةُ المدوّنة صورةً صورة (§4) ‏+ دفعةُ تلغرام الأخيرة (§5) — حتميّ · بلا شبكة.

لكلّ صورةٍ من الـ722 حالاتٌ منفصلة لا يُستنتج بعضُها من بعض (§4 «EXISTS ≠ ACCESSIBLE ≠ VISUALLY INSPECTED ≠ USED AS EVIDENCE ≠ PRIMARY»):
  EXISTS            — الملفُّ على القرص بمساره في سجلّ V3 (`faisal_method_v3/image_corpus.json`)
  ACCESSIBLE        — تفتحه PIL وتتحقّق منه ‏+ بصمتُه SHA-256 = بصمةُ السجلّ
  VISUALLY_INSPECTED— ممثّلُ وحدته قُرئ بالعين في المرور البصريّ V4 (609 وحدة) · وعضوُ العنقود رُوجع تكرارًا بالعين في V3 (102 عنقودًا)
  USED_AS_EVIDENCE  — سجلُّ وحدته عبارةُ قرارٍ في `results/cases_v4.json` أو شاهدُ قاعدةٍ (حقل rules) — والطبقة X «طرفٌ ثالث» لا دليلٌ لفيصل
  PRIMARY           — فيصل كاتبُها (a = F) بطبقة 1 (ظاهرٌ/مربوطٌ/مُقرٌّ من المالك)
والمحتوى طرفٌ ثالث (content_third_party) حين الكاتبُ غيرُ فيصل أو المحتوى المضمَّن لغيره (third_party · third_party_content) — ولو نشره فيصل.

المخرجات: `results/image_reconciliation_v4.json` (722 صفًّا) · `results/corpus_counts_v4.json` · `results/telegram_reconciliation_v4.json`.

🔁 أُعيد بناءُ هذا الملفّ يوم 2026-10-06 بعد ضياع نسخته غيرِ المدفوعة باستعادة الحاوية — والتعريفاتُ أعلاه تعيد الأرقامَ المطبوعة يوم 2026-10-02
حرفًا (722 · 722 · 722 · 609 · 102 · 602 · 609 · 265 · 369 · واستعمالُ الدليل 220/190/277/35 · وتلغرام 11/11 · مكرّر 1 · أوّليّ 6 · محتوى أوّليّ 3 · طرفٌ ثالث 7).
"""
import collections
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import v4_cases as VC     # noqa: E402

V3 = os.path.join(ROOT, "faisal_method_v3")
CORPUS = os.path.join(V3, "image_corpus.json")
CLUSTERS = os.path.join(V3, "dedup_clusters.json")
RECONCILE_V31 = os.path.join(V3, "v31", "reconcile_v31.json")
RULE_AUDIT_V31 = os.path.join(V3, "v31", "rule_audit_v31.json")
CASES = os.path.join(HERE, "results", "cases_v4.json")
OUT_IMG = os.path.join(HERE, "results", "image_reconciliation_v4.json")
OUT_CNT = os.path.join(HERE, "results", "corpus_counts_v4.json")
OUT_TG = os.path.join(HERE, "results", "telegram_reconciliation_v4.json")

USE_CLASSES = ("DECISION_STATEMENT", "RULE_WITNESS", "THIRD_PARTY", "NOT_USED")


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _pil_ok(path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            im.verify()
        return True
    except Exception:                                   # noqa: BLE001 — ملفٌّ لا يُفتح ⟵ غيرُ قابلٍ للوصول (يُعدّ ولا يُسقط)
        return False


def representatives(images, recs, clusters):
    """كلُّ صورة ⟵ سجلُّ وحدتها في المرور البصريّ (نفسُها أو عضوُ عنقودها المقروء)."""
    m2c = {m: c for c in clusters for m in c["members"]}
    out = {}
    for x in images:
        i = x["id"]
        if i in recs:
            out[i] = i
        else:
            c = m2c.get(i)
            out[i] = next((m for m in (c or {}).get("members", []) if m in recs), None)
    return out, m2c


def use_class(r, statement_ids):
    """§4: عبارةُ قرارٍ أو شاهدُ قاعدةٍ أو طرفٌ ثالث أو غيرُ مستعمَل — الطبقة X لا تكون دليلًا لفيصل."""
    used = (r["id"] in statement_ids) or bool(r.get("rules"))
    if VC.tier(r["a"], r.get("ab")) == "X":
        return "THIRD_PARTY" if used else "NOT_USED"
    if r["id"] in statement_ids:
        return "DECISION_STATEMENT"
    return "RULE_WITNESS" if r.get("rules") else "NOT_USED"


def content_third_party(r):
    return bool(r.get("third_party") or r.get("third_party_content") or r.get("a") != "F")


def build(check_files=True):
    corpus = json.load(open(CORPUS, encoding="utf-8"))
    clusters = json.load(open(CLUSTERS, encoding="utf-8"))["clusters"]
    recs = {r["id"]: r for r in VC.load_records()}
    cases = json.load(open(CASES, encoding="utf-8"))["cases"]
    statement_ids = {s.split("#")[0] for c in cases for s in (c.get("sids") or [])}
    reps, m2c = representatives(corpus["images"], recs, clusters)
    rows = []
    for x in corpus["images"]:
        p = os.path.join(ROOT, x["file"])
        exists = os.path.exists(p)
        sha_ok = bool(exists and check_files and _sha256(p) == x["sha256"])
        pil = bool(exists and check_files and _pil_ok(p))
        rid = reps.get(x["id"])
        r = recs.get(rid) or {}
        t = VC.tier(r["a"], r.get("ab")) if r else None
        uc = use_class(r, statement_ids) if r else "NOT_USED"
        rows.append({"id": x["id"], "file": x["file"], "family": x.get("family"),
                     "EXISTS": exists, "ACCESSIBLE": bool(pil and sha_ok), "sha256_match": sha_ok,
                     "VISUALLY_INSPECTED": bool(r), "inspected_by": ("V4_PASS" if rid == x["id"] else ("V3_CLUSTER_REVIEW" if r else None)),
                     "representative": rid, "cluster": (m2c.get(x["id"]) or {}).get("cluster_id"),
                     "author": r.get("a"), "basis": r.get("ab"), "tier": t, "use": uc,
                     "USED_AS_EVIDENCE": uc in ("DECISION_STATEMENT", "RULE_WITNESS"),
                     "PRIMARY": bool(r) and t == "1" and r.get("a") == "F",
                     "content_third_party": content_third_party(r) if r else None})
    v31 = json.load(open(RECONCILE_V31, encoding="utf-8"))
    after_v31 = next(m["v31"] for m in v31["corpus"]["table"] if m["metric"] == "unique_units_after_v31_visual")
    rules_v31 = json.load(open(RULE_AUDIT_V31, encoding="utf-8"))["summary"]["rules_v31"]
    counts = {
        "generated_by": "faisal_method_v4/v4_corpus.py",
        "images_in_corpus_record": len(corpus["images"]),
        "files_exist": sum(1 for r in rows if r["EXISTS"]),
        "sha256_match": sum(1 for r in rows if r["sha256_match"]),
        "accessible": sum(1 for r in rows if r["ACCESSIBLE"]),
        "units_by_hash_ocr": corpus["meta"]["clusters"],
        "multi_member_clusters": corpus["meta"]["multi_member_clusters"],
        "units_after_v31_visual_merges": after_v31,
        "v4_pass_records": len(recs),
        "opened_representatives": sum(1 for r in rows if r["inspected_by"] == "V4_PASS"),
        "cluster_members_reviewed_v3": sum(1 for r in rows if r["inspected_by"] == "V3_CLUSTER_REVIEW"),
        "visually_inspected": sum(1 for r in rows if r["VISUALLY_INSPECTED"]),
        "used_as_evidence": dict(collections.Counter(r["use"] for r in rows)),
        "used_as_evidence_total": sum(1 for r in rows if r["USED_AS_EVIDENCE"]),
        "primary_images": sum(1 for r in rows if r["PRIMARY"]),
        "content_third_party": sum(1 for r in rows if r["content_third_party"]),
        "tiers_by_image": dict(collections.Counter(r["tier"] for r in rows)),
        "rules_v31_inventory": rules_v31,
        "definitions": {"EXISTS": "الملفُّ على القرص", "ACCESSIBLE": "PIL يفتحه ‏+ SHA-256 = السجلّ",
                        "VISUALLY_INSPECTED": "ممثّلُ الوحدة في مرور V4 · وعضوُ العنقود في مراجعة V3 البصريّة",
                        "USED_AS_EVIDENCE": "عبارةُ قرار (cases_v4) أو شاهدُ قاعدة (rules) بطبقةٍ غيرِ X",
                        "PRIMARY": "a = F بطبقة 1", "content_third_party": "الكاتبُ غيرُ فيصل أو المحتوى المضمَّن لغيره"},
    }
    tg = telegram(v31, recs, rows)
    return rows, counts, tg


def telegram(v31, recs, rows):
    byimg = {r["id"]: r for r in rows}
    per = []
    for p in v31["telegram"]["per_image"]:
        row = byimg.get(p["id"]) or {}
        rid = row.get("representative")
        r = recs.get(rid) or {}
        t = row.get("tier")
        per.append({"id": p["id"], "message_id": p["message_id"], "sent_utc": p["sent_utc"], "exists": row.get("EXISTS", False),
                    "accessible": row.get("ACCESSIBLE", False), "sha_matches_corpus": row.get("sha256_match", False),
                    "in_corpus": p["id"] in byimg, "duplicate_of": p.get("duplicate_of") or [], "v4_record": rid,
                    "author": r.get("a"), "basis": r.get("ab"), "tier": t, "decision": r.get("dec"), "res": r.get("res"),
                    "case": r.get("case"), "primary_author": bool(t == "1" and r.get("a") == "F"),
                    "content_third_party": row.get("content_third_party"),
                    "primary_content": bool(t == "1" and r.get("a") == "F" and not row.get("content_third_party")),
                    "use": row.get("use"), "v31_author_or_source": p.get("author_or_source"), "v31_evidence_status": p.get("evidence_status")})
    summary = {"expected": len(per), "found_in_corpus": sum(1 for x in per if x["in_corpus"]),
               "accessible": sum(1 for x in per if x["accessible"]), "sha_match": sum(1 for x in per if x["sha_matches_corpus"]),
               "duplicates": sum(1 for x in per if x["duplicate_of"]),
               "duplicate_map": {x["id"]: x["duplicate_of"] for x in per if x["duplicate_of"]},
               "primary_author": sum(1 for x in per if x["primary_author"]),
               "primary_content": sum(1 for x in per if x["primary_content"]),
               "primary_content_ids": [x["id"] for x in per if x["primary_content"]],
               "third_party": sum(1 for x in per if x["content_third_party"]),
               "sends": v31["telegram"]["sends"]}
    return {"generated_by": "faisal_method_v4/v4_corpus.py ⟵ v31/reconcile_v31.json · data/visual_pass_v4.jsonl",
            "summary": summary, "per_image": per,
            "note": "«أوّليّ» = فيصل كاتبُه بطبقة 1 · و«محتوى أوّليّ» = ذاك بلا محتوًى مضمَّنٍ لطرفٍ ثالث (إنفوغراف · نتائجُ بحث) · "
                    "والمكرّر يُقرأ بممثّل عنقوده"}


def main():
    rows, counts, tg = build()
    json.dump({"generated_by": "faisal_method_v4/v4_corpus.py", "rows": rows}, open(OUT_IMG, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, sort_keys=True)
    json.dump(counts, open(OUT_CNT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    json.dump(tg, open(OUT_TG, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    print({k: v for k, v in counts.items() if k != "definitions"})
    print("telegram:", tg["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
