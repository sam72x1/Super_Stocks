# -*- coding: utf-8 -*-
"""
🎯 FAISAL V3.1 — إعادةُ تدقيق «50٪» و«100٪» صورةً صورة (§13) · قراءةٌ فقط · `target_forensics.json` (V3) لا يُعدَّل.

    python3 faisal_method_v3/v31_targets.py     ⟵ faisal_method_v3/v31/target_forensics_v31.json

المسح: ① نصُّ OCR لكلّ صورةٍ في المدوَّنة (722) ② أسطرُ الوثائق التي تذكر «50٪/100٪» مع معرّفِ صورةٍ ليس في أدلّة V3
③ مراجعاتُ V3.1 البصريّة. لكلّ إصابة: الصورة · السياق · المعنى (من قاموسٍ مكتوبٍ قبل القراءة أدناه) · الكاتب · وهل تناقض حكمَ V3.
⚖️ «التناقض» = صورةٌ لفيصل تستعمل 50٪/100٪ إسقاطًا من ارتفاع النموذج — وهو ما نفاه V3.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "v31", "target_forensics_v31.json")
DOCS = ["FAISAL_IMAGES_CATALOG.md", "FAISAL_SOURCE_LEDGER.md", "FAISAL_IMAGE_PASS2.md", "FAISAL_IMAGE_PASS3.md", "faisal_images/README.md"]
_ID = re.compile(r"\b(IMG_\d{3,5}|TG_\d{3,6}|(?:X|CH|EDU|APP|WA|TG)_\d{8}_[A-Za-z0-9_]+)\b")
_NUM = re.compile(r"(?<![\d.,])(50|100)\s*[%٪]|[%٪]\s*(50|100)(?![\d.])")

# القراءةُ بالعين لكلّ إصابةٍ ليست في أدلّة V3 (المعنى · الكاتب) — مكتوبةٌ من الصورة/السطر نفسِه
READ = {
    "IMG_0362": ("PRICE_CHANGE", "—", "«‏−68.50%» تغيّرُ سعر YYAI في لوحة التطبيق — ليس معنًى لـ50٪"),
    "X_20260905_13": ("PRICE_CHANGE", "—", "«Pre Market +9.50%» — تغيّرُ سعر"),
    "X_20260905_14": ("PRICE_CHANGE", "—", "«Pre Market +9.50%» — تغيّرُ سعر"),
    "TG_2103": ("REALIZED_GAIN", "faisal", "قائمةُ صفقات الأسبوع: «FIEE 50%» · «NAMM 100%» · «SMX 200%» — ربحٌ محقَّق من الدخول"),
    "IMG_0144": ("REALIZED_GAIN", "third_party", "متابعٌ (@AbuAdel2): «تطبيق عملي لما تعلمته من ابو بدر … 100%» — ربحٌ محقَّق"),
    "X_20260828_09": ("REALIZED_GAIN", "edu_channel", "«اختبر المقاومه اليوم بربح 50٪ مجمل» — ربحٌ مجمَلٌ من القاع إلى المقاومة"),
    "TG_2097": ("TARGET_GAIN_FROM_SUPPORT", "faisal", "«دعم السهم 2 السعر الحالي 2.80 · الهدف 4 = 100٪» — المئةُ من الدعم (2⟵4) لا من السعر الحاليّ (2.80⟵4 = ‏+43%)"),
    "TG_2040": ("GAIN_FROM_BOTTOM", "faisal", "«كون قاع … عند 4.21 صعد منها الى 8.50 = 100٪» — من القاع"),
    "TG_2102": ("GAIN_FROM_BOTTOM", "faisal", "«سهم حقق قاع ارتفع 100٪ · هبط دعم ارتفاع 90٪»"),
    "TG_1819": ("TARGET_GAIN", "faisal", "الوصفةُ الصارمة: «هدفك 100% أقل شي»"),
    "TG_2208": ("TARGET_GAIN", "faisal", "الوصفةُ الصارمة نفسُها («هدفك 100٪ اقل شي») — تغريدةٌ أخرى"),
    "TG_1867": ("REALIZED_GAIN", "faisal", "«كنا نحقق بالارتكاز 100% وأكثر بأقل من 5 جلسات»"),
    "TG_1827": ("REALIZED_GAIN", "faisal", "DSY «حقق 7 فوق 100%»"),
    "TG_2091": ("TARGET_GAIN", "faisal", "BNAI «كانت الاهداف المتوقعه 100٪ ل 200٪ · حقق 4000٪»"),
    "TG_2173": ("TARGET_GAIN", "faisal", "JZ «اهدافه … اقلها 100٪»"),
    "TG_2213": ("REALIZED_GAIN", "faisal", "PAVS «شكرا شبل غامد 100٪ · فوق الهدف جاب 9»"),
    "TG_2214": ("EXPECTED_RISE", "unknown_author", "JEM «صعود السهم = 100٪ لو حققت منها 80٪ انت بطل» (الترويسة مقصوصة)"),
    "TG_2215": ("EXPECTED_RISE", "unknown_author", "مكرّرةُ TG_2214"),
    "IMG_0141": ("EXPECTED_RISE", "faisal", "JEM «صعود السهم = 100%، لو حققت 80% انت بطل»"),
    "TG_2037": ("EXPECTED_BOUNCE", "faisal", "«بيكون هذا القاع اللي يرتد منه 100٪»"),
    "TG_1811": ("TARGET_GAIN", "faisal", "«الهدف الشمعة الساقطة الأولى = 100%» (= IMG_0153)"),
    "TG_20260905_01": ("PARTIAL_TAKE_PROFIT", "third_party", "لقطةُ مجموعةٍ بلا اسمِ مُرسِل (الدفتر: third_party) — «100٪ جني ربح 70٪ من سيولتك · 30٪ تترك لاعلى هدف» — إدارةُ خروج (المحورُ مُغلَق TRAIL_REOPEN)"),
    "IMG_0179": ("REALIZED_GAIN", "faisal", "TG_2199 KUST «دبل الان فوق 100٪» (نسخة)"),
    "IMG_0316": ("TARGET_GAIN", "faisal", "TG_2173 (نسخة)"),
    "IMG_0688": ("REALIZED_GAIN", "faisal", "«سهم ارتكاز حقّق 100%» (DXST · الدورة المصغّرة)"),
    "IMG_0097": ("EXPECTED_MOVE", "faisal", "«حركة فيصل 30-50%» (doc_only)"),
    "IMG_0076": ("EXPECTED_MOVE", "faisal", "الدفتر: «حركة فيصل 30-50%» (IMG_0076-0098 غائبة)"),
    "TG_1907": ("EXPECTED_MOVE", "faisal", "«أضمن 20% نعمة» · SMX «من 4 لـ400» — معايرةُ توقّعات (لا 50/100 معنًى جديد)"),
    "TG_1810": ("OTHER", "faisal", "«متوسط أسّي 30-50 يوم» — مدّةٌ لا نسبة"),
    "TG_1834": ("FIB_FULL_RANGE", "faisal", "فيبوناتشي النطاق الكامل 0%(4.30)⟵100%(11.84) — = F100-4"),
    "TG_2195": ("PRICE_CHANGE", "—", "VWAP 2.352 (53.76%) — نسبُ مسافة في لوحة التطبيق"),
    "IMG_0293": ("PRICE_CHANGE", "—", "TG_2195 (نسخة)"),
    "TG_50584": ("OTHER", "faisal", "«ارتداد لاختبار المقاومه بنسبه 20٪ غالبا» — 20 لا 50/100"),
    "TG_50599": ("OTHER", "faisal", "كسابقتها"),
    "TG_50606": ("OTHER", "faisal", "تنبيهاتُ التقسيم (مستويات) — لا 50/100"),
    "TG_57858": ("FIB_ENTRY", "third_party", "إنفوغرافُ بيعٍ على المكشوف: فيبوناتشي 50% — = F50-6"),
    "TG_58047": ("OTHER", "third_party", "سطرُ «لا تبنِ» في الكاتالوج"),
    "TG_2197": ("RHETORIC", "faisal_adopted", "«100%» بلاغة (الدفتر)"),
    "TG_2041": ("OTHER", "faisal", "إسقاطُ القاع التالي بنسبة 30% — لا 50/100"),
    "TG_2214_": ("EXPECTED_RISE", "unknown_author", ""),
    "EDU_20260827_school_two_models_ma_ladder": ("OTHER", "edu_channel", "منهجُ المدرسة — لا 50/100 معنًى"),
    "TG_1840": ("OTHER", "faisal", "SPRC — السطرُ لا يحمل 50/100 معنًى لفيصل"),
}
PROJECTION = "PATTERN_HEIGHT_PROJECTION"     # ما ينفيه V3 عن فيصل — إن وُجدت إصابةٌ لفيصل بهذا المعنى فهي تناقض


def hits(corpus, v3_ev):
    out = {}
    for r in corpus["images"]:
        t = r.get("ocr_text") or ""
        for m in _NUM.finditer(t):
            a = max(0, m.start() - 120)
            out.setdefault(r["id"], []).append({"via": "ocr", "context": re.sub(r"\s+", " ", t[a:m.end() + 80])})
    for f in DOCS:
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            continue
        for ln in open(p, encoding="utf-8"):
            if _NUM.search(ln):
                for i in set(_ID.findall(ln)):
                    out.setdefault(i, []).append({"via": f, "context": re.sub(r"\s+", " ", ln.strip())[:300]})
    vr = json.load(open(os.path.join(HERE, "data", "visual_review_v31.json"), encoding="utf-8"))["new"]
    for k, x in vr.items():
        t = json.dumps(x, ensure_ascii=False)
        if _NUM.search(t):
            out.setdefault(k, []).append({"via": "visual_review_v31", "context": (x.get("observation") or "")[:300]})
    return {k: v for k, v in out.items() if k not in v3_ev}


def main(out=OUT):
    corpus = json.load(open(os.path.join(HERE, "image_corpus.json"), encoding="utf-8"))
    tf = json.load(open(os.path.join(HERE, "target_forensics.json"), encoding="utf-8"))
    v3_ev = {x for k in ("50", "100") for m in tf["meanings"][k] for x in m["evidence"]}
    H = hits(corpus, v3_ev)
    rows = []
    for i in sorted(H):
        meaning, author, note = READ.get(i, ("UNREAD", "?", ""))
        rows.append({"id": i, "meaning": meaning, "author": author, "note": note, "hits": H[i][:3],
                     "contradicts_v3": meaning == PROJECTION and author.startswith("faisal")})
    unread = [r["id"] for r in rows if r["meaning"] == "UNREAD"]
    add = {
        "F50-11": {"meaning": "ربحٌ محقَّق 50% (وصفٌ لنتيجة صفقة)", "kind": "realized_gain", "source_type": "faisal_verbatim",
                   "evidence": ["TG_2103", "X_20260828_09"], "status": "SUPPORTED",
                   "note": "TG_2103 لفيصل (قائمةُ صفقاته) ‏+ X_20260828_09 قناةٌ تعليميّة ⟵ وحدةٌ فيصليّة واحدة"},
        "F100-1b": {"meaning": "أساسُ «‏+100%» = الدعم/القاع (الدخولُ عند الدعم) لا السعرُ الحاليّ — «دعم 2 · السعر 2.80 · الهدف 4 = 100٪»",
                    "kind": "target_base", "source_type": "faisal_verbatim", "evidence": ["TG_2097", "TG_2040", "TG_2102"],
                    "status": "CONFIRMED",
                    "note": "ثلاثُ وحداتٍ لفيصل بحسابٍ صريح من الدعم/القاع · ومن دخول الاختراق (B) لا مثالَ له ⟵ هدفُ «‏+100% من B» في الأداة UNKNOWN الأساس"},
        "F100-8": {"meaning": "جنيُ ربحٍ جزئيّ عند ‏+100% (70% من السيولة · 30% لأعلى هدف)", "kind": "partial_take_profit",
                   "source_type": "third_party", "evidence": ["TG_20260905_01"], "status": "POSSIBLE",
                   "note": "لقطةُ مجموعةٍ لا منشورٌ باسم فيصل (FAISAL_SOURCE_LEDGER §دفعة 2026-09-05: third_party · «لا يُنسَب لفيصل حتى يُتحقَّق») · "
                           "⛔ ومحورُ إدارة الخروج مُغلَقٌ مُنفَّذًا (TRAIL_REOPEN) ⟵ يُوثَّق ولا يُنفَّذ"},
    }
    res = {"tool": "v31_targets", "v3_evidence_ids": len(v3_ev), "hits_outside_v3": len(rows), "unread": unread,
           "contradictions": [r["id"] for r in rows if r["contradicts_v3"]],
           "by_meaning": {m: sorted(r["id"] for r in rows if r["meaning"] == m) for m in sorted({r["meaning"] for r in rows})},
           "v31_additions": add, "rows": rows,
           "verdict_v31": {"50": "يبقى حكمُ V3: «50٪» عند فيصل ليست إسقاطًا من ارتفاع النموذج — والمعاني المضافة: ربحٌ محقَّق (F50-11)",
                           "100": "يبقى حكمُ V3: «100٪» مع «هدف» = ربحٌ ‏+100% — ويُضاف أساسُه: من الدعم/القاع (F100-1b · CONFIRMED) · "
                                  "وجنيٌ جزئيّ عنده في لقطة مجموعة (F100-8 · طرفٌ ثالث · POSSIBLE · محورٌ مُغلَق)"}}
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ("v3_evidence_ids", "hits_outside_v3", "unread", "contradictions", "by_meaning")},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
