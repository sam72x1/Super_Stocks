# -*- coding: utf-8 -*-
"""🧾📚 EX — تدقيقُ اكتمال مدوّنة فيصل (`EX_PROTOCOL.md` §⑪) — بنّاءٌ حتميٌّ بلا شبكة.

المُدخَلات (كلُّها ملفّاتٌ في المستودع · لا رقمَ باليد):
  V3 (`image_corpus.json` · `dedup_clusters.json`) · V3.1 (`visual_review_v31.json` · `rule_audit_v31.json` ·
  `reconcile_v31.json`) · V4 المجمَّد (`visual_pass_v4.jsonl` · `image_reconciliation_v4.json` · `cases_v4.json` · `rules_v4.py`) ·
  V4.1 (`V4_RULE_PROVENANCE.json` · دفعة B48: المانيفست والطابور وبصماتُ OCR) ‏+ **قراءةُ العين في `eye_pass_ex.jsonl`**.
المُخرَجات: `MASTER_CORPUS_INVENTORY.json` ‏+ `research_queue_ex.json` ‏+ تسعُ وثائق MD (§⑪).

`python3 corpus_audit.py` يكتب · و`--check` يعيد التوليد ويقارن بالمدفوع بايتًا بايتًا ويُخرج 1 عند أيّ عيب (`validate`).
🔒 لا يمسّ V4 (قراءةٌ فقط) ولا دفعةَ B48 المختومة · ولا ينسخ نصَّ OCR ولا خلاصاتِ V4 (فيها أسماءٌ خاصّة) — العبارةُ تُذكر بـ`وحدة#رقم`
وبصمتِها · و«المتاح الآن» = لقطةُ التدقيق (768 ملفًّا ‏+ مرفقٌ واحد) — ما يصل بعدها **استلامٌ أماميٌّ لا عيبٌ في الجرد**.
"""
import collections
import datetime as dt
import glob
import hashlib
import importlib.util
import itertools
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V41 = os.path.dirname(HERE)
ROOT = os.path.dirname(V41)
AUDIT_DATE = "2026-10-07"
EYE = "faisal_method_v41/corpus_audit/eye_pass_ex.jsonl"
OUT_INV = "MASTER_CORPUS_INVENTORY.json"
OUT_QUEUE = "research_queue_ex.json"
DOCS = ("SOURCE_INVENTORY.md", "CORPUS_INVENTORY_SUMMARY.md", "DUPLICATE_AUDIT.md", "RULE_TRACEABILITY.md", "CONTRADICTION_AUDIT.md",
        "NEGATIVE_EVIDENCE.md", "MISSED_INFORMATION.md", "COLLECTOR_PROVENANCE_CHECK.md", "CORPUS_EXHAUSTIVENESS_REPORT.md")
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif")

TRACE_CLASSES = ("T-V4", "T-V31", "T-PROD", "T-CLOSED", "T-QUEUE", "T-CASE", "T-NONGEN", "T-NONE")
DEPTHS = ("FULLY_ANALYZED", "PARTIALLY_ANALYZED", "SUPERFICIAL", "OCR_ONLY", "NOT_ANALYZED")
ROLES = ("VALIDATION_CASE", "COUNTEREXAMPLE", "RULE_EVIDENCE", "CONTEXT_ONLY", "NO_UNIQUE_INFO", "NON_EVIDENCE")
MISSED_CLASSES = ("CONFIRMED_MISSED_RULE", "PROBABLE_MISSED_RULE", "HYPOTHESIS", "ALREADY_COVERED", "INSUFFICIENT_EVIDENCE")
DUP_RELATIONS = ("EXACT", "NEAR", "RESIZE", "CROP", "ANNOTATED_VERSION", "DIFFERENT_TIMEFRAME", "DIFFERENT_DATE",
                 "SAME_CHART_DIFFERENT_DECISION", "SAME_CHART_ADDITIONAL_INFO", "SAME_CASE_DIFFERENT_CONTENT",
                 # تفصيلاتٌ أدقُّ سُجّلت بها أحكامُ العين (كلٌّ منها ينتمي لصنفٍ من أصناف §④)
                 "SAME_CHART", "SAME_POST_ADDITIONAL_INFO", "ATTACHMENT", "ATTACHMENT_LEGIBILITY", "DIFFERENT_POST",
                 "DIFFERENT_STOCK_OR_TEMPLATE")
FAISAL_AUTHORS = ("F", "F_visible", "F_inferred")
DECISION_WORDS = ("READY", "WAIT", "REJECT", "WATCH", "MULTI")
NONEV_RES = ("OFF_TOPIC_AI", "OFF_TOPIC", "OFF_TOPIC_META", "OWNER_NOTE")
NOUNIQ_RES = ("DECISION_DUP",)
EVIDENCE_ROLES = ("VALIDATION_CASE", "COUNTEREXAMPLE", "RULE_EVIDENCE")
MEMORY_DOCS = ("CLAUDE.md", "DECISIONS_ARCHIVE.md")      # النقلُ بين الدليل والأرشيف لا يكسر المؤشّر (نقلٌ لا حذف)

# حقائقُ مسجَّلةٌ قبل أيّ عدد (EX_PROTOCOL §⓪) — لا تُعاد حسابًا لأنها تحتاج الشبكة
SNAPSHOT = {
    "collector_run_after_558": "37652483700",
    "b48_collector_run": "37616553357",
    "collector_558_commit": "cbdcc52c",
    "branches_scanned": 51,
    "images_outside_main": 0,
    "v3_snapshot_commit": "e939785e0",
    "deleted_or_renamed_since_v3": 0,
    "session_attachments": 1,
}

# ── طابورُ EX (§⑥ · §⑦ · §⑭): نصٌّ مكتوب · والحالاتُ الداعمة تُحسب من التتبّع (`trace_ptrs`) ‏+ ما يُذكر صراحةً (`extra`)
QUEUE_EX = [
    dict(id="RQ-EX-01", rules=(), cls="V4_COVERAGE_GAP", title="«ساعةُ النضج» — حقّق متوسّطَ 20/30/50 جلسة قبل الحكم",
         observation="فيصل يشترط مرارًا «حقق متوسط 20/30/50» محسوبًا بالجلسات من تاريخ التقسيم أو من أعلى شمعة هبوط — موجودٌ في V3.1 "
                     "(CK-01 غيرُ منفَّذ · L-057 · L-262 · L-288) ويُعرض في الإنتاج (`split_ma_maturity`) — **ولا شرطَ زمنيّ في V4** (بنيةُ السعر وحدَها). "
                     "ودفعةُ B48 تضيف نقطةَ البدء: «من قاع السهم تحسب للصعود ومن اعلى شمعة هبوط لتحقيق القاع» و«مالم يصعد اول متوسط 10 بعد التقسيم».",
         candidate_rule="قبل READY: مضى منذ التقسيم (أو منذ أعلى شمعة هبوط) عددُ جلساتٍ يبلغ المتوسّطَ المعنيّ (20 · 30 · 50) — "
                        "والعدُّ من القاع للصعود ومن أعلى شمعة هبوط لبلوغ القاع.",
         trace_ptrs=("queue:RQ-EX-01", "v31:L-057", "v31:CK-01", "v31:L-262", "v31:L-288"),
         extra=(), contradictory=("IMG_0150 — «بعضُها يتضاعف قبل» المتوسّط", "EDU_20260827_ma_rizq_rule_sle — «صعد قبل متوسطات الحركه = رزق لم يكتب»"),
         confidence="مرجّحٌ جدًّا أنه شرطُ فيصل (نصُّه في وحداتٍ مستقلّةٍ كثيرة) · ومعناه الدقيق (متوسّطٌ حسابيٌّ أم عدُّ جلسات · ونقطةُ البدء) غيرُ محسوم",
         generality="نوعا الارتكاز: المقسَّمُ حديثًا والهابطُ بعد صعودٍ عالٍ",
         why_not_v4="V4 مجمَّدٌ أثناء التحقّق الأماميّ · وأثرُه اليوم صفر لأنّ V4 لا يقول READY بلا مصادر صلاحيّة (FVO1 · RQ-05) · "
                    "ويلزمه تعريفٌ مكتوبٌ وتسجيلٌ مسبق · و`T-MA-LADDER` قاس لمسَ EMA50 لا عدَّ الجلسات",
         v4_effect="FALSE READY محتملٌ على المقسَّم حديثًا متى حُلّت RQ-05"),
    dict(id="RQ-EX-02", rules=("R4-VAL-GRP-01",), cls="V4_COVERAGE_GAP", title="مؤشّرُ القروبات السعريّ (CK-05) — جوابٌ جزئيٌّ لـRQ-05",
         observation="«الجاهزُ يتذبذب 10% حدًّا أقصى · والقروبُ يرفع بشموعٍ بلا جسم تصل 20% على 4 ساعات» (CK-05 · نصُّ فيصل) — بصمةٌ سعريّةٌ تُقرأ as-of "
                     "بينما `R4-VAL-GRP-01` بلا مصدرٍ أماميّ فيمتنع V4 عن READY.",
         candidate_rule="«قروبٌ محتمل» = شمعةُ 4 ساعات بلا جسمٍ تبلغ ‏+20% أو تذبذبٌ فوق 10% في نافذة القاع — يُقاس قبل أن يُعتمد مصدرًا لـR4-VAL-GRP-01.",
         trace_ptrs=("v31:CK-05",), extra=("TG_1959",), contradictory=(),
         confidence="محتمل — نصٌّ واحدٌ صريح (CK-05) وشواهدُ وصفيّة · ولم يُقَس",
         generality="كلُّ مرشَّحٍ عند القاع",
         why_not_v4="تغييرٌ منهجيّ ممنوع أثناء التحقّق · وقد يُصيب شمعةَ مضاربٍ عنيفة · يلزمه تسجيلٌ مسبقٌ ووسومٌ مستقلّة",
         v4_effect="يرفع امتناعَ V4 (UNKNOWN) حيث لا مصدرَ للقروبات"),
    dict(id="RQ-EX-03", rules=("R4-VAL-SHORT-01",), cls="CONTRADICTION", title="الشورتُ نسبيٌّ لا مطلق — `R4-VAL-SHORT-01` (20 ألفًا)",
         observation="«30 الف على عدد اسهمه لاشي» (WNW) · و«هبوط الشورت تحت 50 ألفًا» في وصفة الهبوط · ومتاحٌ 55 ألفًا لم يمنع التحليل — "
                     "مقابل عتبةٍ مطلقة 20 ألفًا في V4 · ووصفةُ المقسّم نفسُها تقرن 20 ألفًا بأقلَّ من مليوني سهم (‏≈1%).",
         candidate_rule="عتبةُ المتاح تُقرأ نسبةً من عدد الأسهم/الفلوت (المرشَّح ‏≈1-2%) لا رقمًا ثابتًا — أو تبقى 20 ألفًا لما دون مليوني سهم.",
         trace_ptrs=("queue:RQ-EX-03",), extra=("TG_1831", "IMG_0143", "IMG_0153", "TG_1821", "IMG_0150", "TG_50578"),
         contradictory=("IMG_0496 — «الشورت مايتعدا كم؟ 20 وتحت» عتبةٌ مطلقة",),
         confidence="فرضيّةٌ محتملة — نصٌّ صريحٌ واحد (WNW · قناةٌ تعليميّة) وشواهدُ أرقامٍ متفرّقة",
         generality="كلُّ مرشَّح — والأثرُ أكبرُ على كبار الفلوت",
         why_not_v4="عتبةٌ في قاعدة صلاحيّة · تغييرُها منهجيّ · والمتاحُ التاريخيّ غيرُ متاحٍ رجعيًّا (أماميٌّ وحدَه)",
         v4_effect="FALSE WAIT على كبار الفلوت · وFALSE READY محتمل على الصغار جدًّا"),
    dict(id="RQ-EX-04", rules=("R4-LOC-01",), cls="CONFIRMED_MISSED_RULE", title="«الصعودُ التدريجيّ ما افضله» — صعودٌ بلا شمعة مضارب لا يُعدّ انطلاقًا",
         observation="فيصل: «ذكرت في تغريده سابقه الصعود التدريجي ما افضله · هذا صعد تدريجي 40٪ وهبط» (KWM) · و«جميل السهم لكن صعوده تدريجي حقق 50٪» "
                     "ثمّ «عن نفسي ما اخاطر انتظر 1.60» (MNDR) — لا أثرَ لها في V3.1 ولا V4 ولا الدفتر.",
         candidate_rule="صعودٌ تدريجيٌّ من القاع (شموعٌ متتالية بلا شمعة مضاربٍ واحدة) لا يُقرأ انطلاقًا ⟵ انتظارُ اختبار الدعم.",
         trace_ptrs=("queue:RQ-EX-04",), extra=("TG_2108",), contradictory=(),
         confidence="مؤكَّدٌ نصًّا (نصُّ فيصل في وحدتين مستقلّتين برمزين وتاريخين) · ومعيارُ «تدريجيّ» غيرُ معرَّفٍ رقميًّا",
         generality="عامّة بنصّه («ذكرت في تغريده سابقه»)",
         why_not_v4="قرارُ V4 لا يتغيّر اليوم: الصاعدُ فوق المنطقة WAIT أصلًا (`R4-LOC-01` · R-50-01) — الأثرُ في وصف الحالة لا في القرار",
         v4_effect="صفرٌ على القرار · يُوسم سببُ الانتظار"),
    dict(id="RQ-EX-05", rules=("R4-HOLD-01", "R4-HOLDZ-01"), cls="PROBABLE_MISSED_RULE", title="يومُ حدثٍ اقتصاديٍّ كلّيّ (الفدرالي) — الثباتُ يومَها ليس ثباتًا فنّيًّا",
         observation="«غدا الفدرالي الاسهم اغلبها ثابته» (فيصل) — يومُ الحدث يُنتج ثباتًا عامًّا قد يُعدّ في جلسات الحفظ.",
         candidate_rule="أيّامُ الأحداث الكلّيّة المعلنة لا تُعدّ جلساتِ ثباتٍ في `R4-HOLD-01`/`R4-HOLDZ-01` (أو تُوسم).",
         trace_ptrs=("queue:RQ-EX-05",), extra=(), contradictory=(),
         confidence="ضعيفة — وحدةٌ واحدة",
         generality="مجهولة",
         why_not_v4="وحدةٌ واحدة · بلا قياس · وتقويمُ الأحداث الكلّيّة غيرُ موصولٍ في V4",
         v4_effect="عدُّ ثباتٍ زائفٍ محتمل يومَ الحدث"),
    dict(id="RQ-EX-06", rules=("R4-SWEEP-01", "R4-INV-01"), cls="CONTRADICTION", title="حدُّ عمق السحب/الإبطال 13% غيرُ متعيّنٍ من المدوّنة",
         observation="شواهدُ أضيق: «لايمكن تكسر اكثر من 10٪» · «كسر 4 يفشل التحليل» (‏≈−5.5%) — وشواهدُ أعمق: ‏−14.2% · ‏−15.1% · ‏−15.6% · ‏≈−35% ثمّ عودة — "
                     "مقابل `SWEEP_MAX_PCT` 13 في `R4-SWEEP-01`/`R4-INV-01` (وسمُه في الدفتر faisal_adopted).",
         candidate_rule="لا رقمَ واحدًا: الحدُّ يُكتب نطاقًا بحسب نوع الإعداد (قاعٌ محفوظ مقابل وصفة ÷2) — يُقاس أماميًّا قبل أيّ تعديل.",
         trace_ptrs=(), extra=("TG_1867", "IMG_0395", "TG_1880", "IMG_0299", "IMG_0320", "TG_20260918_67_BRNX", "IMG_0143", "IMG_0153"),
         contradictory=("TG_58387 — ‏−10.9% داخل الحدّ", "TG_2068 — ‏−8% داخل الحدّ", "IMG_0297 — «سحب السيوله متعارف عليه من 7٪ ل 13٪»"),
         confidence="التعارضُ مؤكَّدٌ بالأرقام · والحدُّ الصحيح مجهول",
         generality="كلُّ إعدادٍ فيه سحب",
         why_not_v4="عتبةٌ حاكمة · وتغييرُها بلا قياسٍ أماميٍّ تفصيلٌ على المدوّنة",
         v4_effect="BROKEN_NEW_BASE مبكّرٌ (أعمق من 13%) أو متأخّر (أضيق منه)"),
    dict(id="RQ-EX-07", rules=("R4-VAL-OFF-01",), cls="CONTRADICTION", title="الطرحُ المعلَّق: فيصل يرفض و V4 ينتظر (`R4-VAL-OFF-01`)",
         observation="«عليه طرح ⟵ لا» · و«السهم سلبي اولا بسبب الطرح وكذلك الشورت» — قرارُ فيصل REJECT · وقرارُ V4 للطرح المعلَّق WAIT.",
         candidate_rule="طرحٌ معلَّقٌ لم يُغلق ⟵ REJECT لا WAIT (حتى يُعلن الإغلاق).",
         trace_ptrs=(), extra=("TG_1813", "TG_58390"), contradictory=(),
         confidence="محتمل — حالتان",
         generality="كلُّ سهمٍ عليه طرح",
         why_not_v4="FALSE WAIT لا FALSE READY (الأثرُ أقلّ خطرًا) · وتغييرُ أثر قاعدةٍ منهجيّ",
         v4_effect="WAIT بدل REJECT"),
]
QUEUE_UPDATES = [
    dict(id="RQ-EX-U1", rules=(), updates="RQ-B48-01", note="قاعدةُ ÷2 بنصّ فيصل لا تخمين: «2.33 ع 2 · محتمل يهبط ل 1.16» ووصفةُ الهبوط ÷2 والمساعدُ «حقق المتوسط» عند ÷2.",
         evidence=("IMG_0150", "IMG_0153", "IMG_0143", "TG_2200", "TG_58404")),
    dict(id="RQ-EX-U2", rules=(), updates="RQ-B48-03", note="عتباتُ التطبيق (ممتاز 0-5% · ضمن 15% · ثباتُ جلستين · أسفل EMA20/30/50 · فلوت 5 ملايين) موثَّقةٌ في V3.1 "
                                               "(L-289 · L-296 · L-300) — طرفٌ ثالث لا فيصل.",
         evidence=("TG_57914", "TG_57915", "TG_57926", "TG_58401", "TG_58403", "TG_58406", "TG_58420")),
    dict(id="RQ-EX-U3", rules=(), updates="RQ-B48-04", note="«اجابيه» ثلاثةُ معانٍ: صلاحيّةٌ (الشورت والأخبار والإعلانات خلال فترة المتوسّطات) · فنّيّةٌ (ثباتٌ/تجاوزُ شمعة) · وإنجازٌ («إيجابيّةُ السهم = تحقيق 100٪»).",
         evidence=("TG_58419", "TG_58390", "TG_58411", "TG_1813", "IMG_0302", "IMG_0391", "X_20260918_13_NUWE", "TG_2044")),
    dict(id="RQ-EX-U4", rules=(), updates="RQ-07", note="«70٪» كمّيّةٌ لا هدف: «جني الربح … باكثر من 70٪ من الكميه» · «جني 70٪ من السيولة و30٪ لأعلى هدف» · «لو حققت منها 80٪ انت بطل».",
         evidence=("TG_57862", "TG_20260905_01", "IMG_0141", "TG_57885")),
    dict(id="RQ-EX-U5", rules=("R4-CYC-01",), updates="RQ-08", note="ارتدادُ الاختبار «غالبا من 10 > 15٪» و«من 10 ل 20٪» — الطرفُ الأدنى دون 15% في `R4-CYC-01`.",
         evidence=("IMG_0486", "IMG_0497")),
    dict(id="RQ-EX-U6", rules=("R4-VAL-GRP-01",), updates="RQ-05", note="القروبُ مؤقّتٌ عند فيصل: «قروبات هيّضته … هبط بالسهم … حقق المتوسط والدخول» — والإبطالُ بالقروب زمنيٌّ لا نهائيّ · ومؤشّرُه السعريّ في RQ-EX-02.",
         evidence=("TG_1807", "TG_20260905_03", "X_20260905_10", "IMG_0746")),
]

# ── الأدلّةُ السالبة (§⑥ من أمر المالك) — كلٌّ بمؤشّرٍ يُفحص
NEGATIVE = [
    dict(id="NE-01", units=("TG_2042",), kind="CLAIM_REFUTED", ptr="doc:DECISIONS_ARCHIVE.md::نسبة الربح الحيّة 2025 = 25.9%",
         text="«نسبة فشلها 1٪» — نسبةُ الربح الحيّة المقيسة 2025 = 25.9%"),
    dict(id="NE-02", units=("IMG_0179",), kind="CLAIM_MEASURED_NEGATIVE", ptr="doc:DECISIONS_ARCHIVE.md::`T-LINK100-2` — «قبل ما يدبل يُضغط لأدنى قاع»",
         text="«دائما السهم قبل يدبل يتم ضغطه لادنى قاع» — قِيس `T-LINK100-2` فلم يعبر"),
    dict(id="NE-03", units=("X_20260827_hcwb_leak_read", "X_20260827_hcwb_leak_close_dm"), kind="READY_FAILED", ptr="rule:R4-VAL-GRP-01",
         text="«جاهز فنيا» ثمّ تسريبٌ ورفعُ أفرادٍ ‏+20% ثمّ هبوط — READY فشل بسبب صلاحيّةٍ غيرِ مرئيّةٍ وقتَ القرار"),
    dict(id="NE-04", units=("X_20260827_kwm_offering_notready",), kind="NOT_READY_CORRECT", ptr="rule:R4-VAL-OFF-01",
         text="«غير جاهز فنيا» مع طرح — الامتناعُ صدق"),
    dict(id="NE-05", units=("TG_2127",), kind="SUPPORT_BROKEN", ptr="rule:R4-INV-01",
         text="ELAB: الدعمُ كُسر ‏≈−39% (فشلُ الإعداد بقاعدة الإبطال) ثمّ صعودٌ كبير — شاهدٌ قائمٌ على حدود `R4-INV-01`"),
    dict(id="NE-06", units=("TG_1806",), kind="RESULT_ILLUSTRATION", ptr="rule:R4-INV-01", text="سهمٌ أحمرُ على هبوطٍ إلى ‏≈4 بعد الإعداد — توضيحُ فشل"),
    dict(id="NE-07", units=("TG_2002", "TG_2060", "TG_2274"), kind="AXIS_FAILED", ptr="doc:DECISIONS_ARCHIVE.md::`T-CANDLE` «أيُّ شمعةٍ انعكاسية تفصل؟»",
         text="شموعُ الانعكاس (همر · شهاب) — قِيست `T-CANDLE` ففشلت"),
    dict(id="NE-08", units=("TG_1844", "TG_1981", "IMG_9925"), kind="AXIS_FAILED", ptr="doc:DECISIONS_ARCHIVE.md::`T-WKSUP` — «سجل الدعم الأسبوعي»",
         text="شمعةُ الدعم الأسبوعيّة — `T-WKSUP` لا يُشحَن"),
    dict(id="NE-09", units=("TG_2066", "IMG_0150", "IMG_0498"), kind="UNMEASURED_FREQUENCY", ptr="rule:R4-CYC-01",
         text="دعاوى تكرار («90٪» · «80٪» · «80٪ هذا نهج الاسهم») بلا قياس — لا تُقرأ نسبًا"),
    dict(id="NE-10", units=("TG_58402", "TG_58407"), kind="FORWARD_INSUFFICIENT",
         ptr="doc:faisal_method_v41/docs/V4.1_VALIDATION_REPORT.md::دون N_MIN 43",
         text="الحالةُ الأماميّة الوحيدة (BRTX · WAIT) تطابق «دائمًا WAIT» أيضًا — لا ميزةَ مُثبتة"),
]

# ── 50 / 70 / 100 (§⑧) — معانٍ مسنودةٌ بوحدات
TARGETS = [
    dict(k="100٪", meaning="ربحٌ ‏+100% من الدخول (ضعفُ السعر)", units=("X_20260827_amix_3m_inflow", "X_20260827_indicators_canf", "TG_2091"), ptr="rule:R4-TGT-01"),
    dict(k="100٪", meaning="العودةُ إلى منشأ الهبوط/الشمعة الساقطة الأولى بعد هبوطٍ ‏≈50% (وصفةُ ÷2) — يلتقي مع الأوّل حسابيًّا",
         units=("IMG_0143", "IMG_0153", "IMG_0141", "TG_1813", "TG_58390"), ptr="v31:R-100-01"),
    dict(k="100٪", meaning="تراكميٌّ عبر موجتين («اخذنا منه فوق 100٪ بموجتين»)", units=("TG_58417",), ptr="rule:R4-TGT-01"),
    dict(k="100٪", meaning="يقينٌ لا مسافة («100٪ مضمونه عند 5»)", units=("IMG_0587",), ptr="rule:R4-TGT-01"),
    dict(k="100٪", meaning="«إيجابيّةُ السهم = تحقيق 100٪» (معيارُ نجاح)", units=("TG_2044",), ptr="queue:RQ-B48-04"),
    dict(k="50٪", meaning="«50٪ هبوط تمثل 100٪ صعود» · ولا مطاردةَ بعد ‏+50% الأولى · وتجاوزُ 50% ⟵ تصحيحٌ ‏≈30%",
         units=("IMG_8242", "TG_50606", "IMG_0566"), ptr="v31:R-50-01"),
    dict(k="25٪", meaning="«كلُّ ‏≈25% مقاومة»", units=("TG_50606",), ptr="v31:L-245"),
    dict(k="70٪", meaning="كمّيّةٌ تُجنى عند المقاومة لا هدفٌ سعريّ", units=("TG_57862", "TG_20260905_01", "TG_57885"), ptr="queue:RQ-07"),
]


def _p(*a):
    return os.path.join(ROOT, *a)


def _j(rel):
    with open(_p(rel), encoding="utf-8") as f:
        return json.load(f)


def _jl(rel):
    with open(_p(rel), encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def _sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _sha_text(t):
    return hashlib.sha256((t or "").encode("utf-8")).hexdigest()[:16]


def _mod(name, rel):
    spec = importlib.util.spec_from_file_location(name, _p(rel))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def load():
    d = {"corpus": _j("faisal_method_v3/image_corpus.json")["images"],
         "dedup": _j("faisal_method_v3/dedup_clusters.json"),
         "v31": _j("faisal_method_v3/data/visual_review_v31.json"),
         "rules31": _j("faisal_method_v3/v31/rule_audit_v31.json")["rules"],
         "doc_only": _j("faisal_method_v3/v31/reconcile_v31.json")["corpus"]["doc_only"],
         "vp": _jl("faisal_method_v4/data/visual_pass_v4.jsonl"),
         "rec": _j("faisal_method_v4/results/image_reconciliation_v4.json")["rows"],
         "cases": _j("faisal_method_v4/results/cases_v4.json")["cases"],
         "rules4": _mod("_ex_rules_v4", "faisal_method_v4/rules_v4.py").RULES_V4,
         "prov": _j("faisal_method_v41/docs/V4_RULE_PROVENANCE.json")["rules"],
         "b48m": _j("faisal_method_v41/batches/B48_20261007/PROSPECTIVE_BATCH_48_MANIFEST.json"),
         "b48q": _j("faisal_method_v41/batches/B48_20261007/research_queue.json"),
         "b48ocr": _j("faisal_method_v41/batches/B48_20261007/ocr_text.json")["texts"],
         "b48r": _j("faisal_method_v41/batches/B48_20261007/PROSPECTIVE_BATCH_48_RESULTS.json"),   # مختومٌ (BIM9) — لا يتغيّر بتشغيلٍ لاحق
         "n_min": int(re.search(r"^N_MIN = (\d+)", open(_p("faisal_method_v41/analysis.py"), encoding="utf-8").read(), re.M).group(1)),
         "eye": _jl(EYE)}
    d["VP"] = {r["id"]: r for r in d["vp"]}
    d["IMG"] = {r["id"]: r for r in d["corpus"]}
    d["REC"] = {r["id"]: r for r in d["rec"]}
    d["R31"] = {r["RULE_ID"]: r for r in d["rules31"]}
    d["PRV"] = {r["RULE_ID"]: r for r in d["prov"]}
    d["E"] = collections.defaultdict(list)
    for o in d["eye"]:
        d["E"][o["kind"]].append(o)
    d["B48"] = {o["id"]: o for o in d["E"]["b48"]}
    d["MEM"] = {o["id"]: o for o in d["E"]["member"]}
    d["NU"] = {o["id"]: o for o in d["E"]["not_used"]}
    return d


# ── المؤشّرات ────────────────────────────────────────────────────────────────────────────────
_DOC_CACHE = {}


def _doc_text(rel):
    if rel not in _DOC_CACHE:
        if rel in MEMORY_DOCS:
            _DOC_CACHE[rel] = "\n".join(open(_p(x), encoding="utf-8").read() for x in MEMORY_DOCS)
        elif os.path.isfile(_p(rel)):
            _DOC_CACHE[rel] = open(_p(rel), encoding="utf-8").read()
        else:
            _DOC_CACHE[rel] = None
    return _DOC_CACHE[rel]


def queue_ids(d):
    ids = set(re.findall(r"^## (RQ-\d\d) ·", _queue_md_base(), re.M))
    ids |= {it["id"] for it in d["b48q"]["items"]}
    ids |= {q["id"] for q in QUEUE_EX}
    return ids


def _queue_md_base():
    """معرّفاتُ RQ-01…RQ-08 من بنّاء الطابور نفسِه (`docs_v41.doc_queue`) لا من الوثيقة المولَّدة."""
    return open(_p("faisal_method_v41/docs_v41.py"), encoding="utf-8").read()


def pointer_problem(d, p, unit=None, i=None, qids=None, alias=()):
    kind, _, rest = p.partition(":")
    if kind == "rule":
        return None if rest in d["rules4"] else f"قاعدةٌ غيرُ موجودة {rest}"
    if kind == "v31":
        return None if rest in d["R31"] else f"صفُّ V3.1 غيرُ موجود {rest}"
    if kind == "queue":
        return None if rest in (qids or queue_ids(d)) else f"بندُ طابورٍ غيرُ موجود {rest}"
    if kind == "closed":
        t = _doc_text(rest)
        return None if (t and "CLOSED_RC" in t and rest.endswith(".py")) else f"أداةُ محورٍ مُغلَقٍ غيرُ موجودة {rest}"
    if kind == "doc":
        rel, _, sub = rest.partition("::")
        t = _doc_text(rel)
        if t is None:
            return f"وثيقةٌ غيرُ موجودة {rel}"
        return None if (sub and sub in t) else f"نصٌّ غيرُ موجودٍ في {rel}: {sub[:40]}"
    if kind == "case":
        if rest.startswith("CASE_"):
            return None if glob.glob(_p("faisal_method_v41/prospective_validation/cases", rest + ".*.json")) else f"حالةٌ أماميّةٌ غيرُ موجودة {rest}"
        cs = [c for c in d["cases"] if c["case"] == rest]
        if not cs:
            return f"حالةُ V4 غيرُ موجودة {rest}"
        ok = {f"{unit}#{i}", unit} | set(alias)
        if unit is not None and i is not None and not ok & set(cs[0]["sids"]):
            return f"العبارةُ {unit}#{i} ليست في حالة {rest}"
        return None
    return f"صنفُ مؤشّرٍ مجهول {p[:20]}"


NEED_PTR = {"T-V4": ("rule:",), "T-V31": ("v31:",), "T-PROD": ("doc:",), "T-CLOSED": ("closed:", "doc:"), "T-QUEUE": ("queue:",),
            "T-CASE": ("case:",), "T-NONGEN": (), "T-NONE": ("queue:",)}


def statement_problems(d, st, unit=None, qids=None, alias=()):
    out = []
    cls, ptr = st.get("cls"), st.get("ptr") or []
    if cls not in TRACE_CLASSES:
        return [f"صنفُ تتبّعٍ مجهول {cls}"]
    need = NEED_PTR[cls]
    if need and not any(p.startswith(need) for p in ptr):
        out.append(f"{cls} بلا مؤشّرٍ من صنفه")
    for p in ptr:
        e = pointer_problem(d, p, unit, st.get("i"), qids, alias)
        if e:
            out.append(e)
    if cls == "T-NONE":
        m = st.get("missed") or {}
        if m.get("class") not in MISSED_CLASSES:
            out.append("T-NONE بلا صنفٍ في §⑥")
        elif m["class"] in ("CONFIRMED_MISSED_RULE", "PROBABLE_MISSED_RULE", "HYPOTHESIS") and f"queue:{m.get('queue')}" not in ptr:
            out.append("مرشَّحٌ فائتٌ بلا بندِ طابور")
    for c in st.get("contra") or []:
        if c.get("rule") not in d["rules4"]:
            out.append(f"تعارضٌ على قاعدةٍ غيرِ موجودة {c.get('rule')}")
    return out


# ── المرشَّحون للتكرار (§④): أربعةُ مولِّدات ثمّ حكمٌ لكلّ زوج ─────────────────────────────────────
_REF = re.compile(r"(TG_\d{8}_\d+_[A-Za-z0-9]+|TG_\d{8}_\d+|TG_\d+|IMG_\d+|X_\d{8}_[A-Za-z0-9_]+|CH_\d{8}_[A-Za-z0-9_]+|"
                  r"EDU_\d{8}_[A-Za-z0-9_]+|WA_\d{8}_\d+_[A-Za-z]+|APP_\d{8}_\d+_[A-Za-z]+)")
_NUM = re.compile(r"(?<![\d.])(\d{1,4}\.\d{2,4})(?![\d])")
_TOK = re.compile(r"[؀-ۿ]{3,}|[A-Za-z]{3,}|\d+\.\d+")


def candidates(d):
    VP, IMG = d["VP"], d["IMG"]
    reps = sorted(VP)
    c = {}

    def add(a, b, g, s):
        if a == b or a not in VP or b not in VP:
            return
        c.setdefault(tuple(sorted((a, b))), {})[g] = s
    for i in reps:
        for m in sorted(set(_REF.findall(VP[i].get("g", "")))):
            if m != i and m in VP:
                add(i, m, "REF", 1)
    N = {i: set(_NUM.findall(VP[i].get("g", ""))) for i in reps}
    T = {i: set(_TOK.findall(IMG[i].get("ocr_text") or "")) for i in reps}

    def grams(s, n=5):
        s = re.sub(r"[\s‏‎·]+", " ", s)
        return {s[k:k + n] for k in range(max(0, len(s) - n + 1))}
    Q = {i: grams(" ".join(re.findall(r"«([^»]{6,})»", VP[i].get("g", "")))) for i in reps}
    for a, b in itertools.combinations(reps, 2):
        s = N[a] & N[b]
        if len(s) >= 4:
            add(a, b, "NUM", round(len(s) / len(N[a] | N[b]), 2))
        A, B = T[a], T[b]
        if len(A) >= 12 and len(B) >= 12:
            k = len(A & B)
            if k >= 12 and k / min(len(A), len(B)) >= 0.5:
                add(a, b, "OCR", round(k / min(len(A), len(B)), 2))
        if len(Q[a]) >= 40 and len(Q[b]) >= 40:
            k = len(Q[a] & Q[b])
            if k >= 25 and k / min(len(Q[a]), len(Q[b])) >= 0.35:
                add(a, b, "QUOTE", round(k / min(len(Q[a]), len(Q[b])), 2))
    return c


def _drange(s):
    if not isinstance(s, str):
        return None
    s = s.strip()
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        x = dt.date(*map(int, m.groups()))
        return x, x
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d)x", s)
    if m:
        y, mo, dd = int(m[1]), int(m[2]), int(m[3])
        last = (dt.date(y + (mo == 12), mo % 12 + 1, 1) - dt.timedelta(days=1)).day
        lo, hi = max(1, dd * 10), min(last, dd * 10 + 9)
        return (dt.date(y, mo, lo), dt.date(y, mo, hi)) if lo <= last else None
    m = re.fullmatch(r"(\d{4})-(\d{2})", s)
    if m:
        y, mo = int(m[1]), int(m[2])
        last = (dt.date(y + (mo == 12), mo % 12 + 1, 1) - dt.timedelta(days=1)).day
        return dt.date(y, mo, 1), dt.date(y, mo, last)
    m = re.fullmatch(r"≤(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return dt.date(2000, 1, 1), dt.date(*map(int, m.groups()))
    return None


def _v31_merges(d):
    out = []
    for k, v in sorted(list(d["v31"]["new"].items()) + list(d["v31"]["amend"].items())):
        for rel in ("derivative_of", "same_drawing_as"):
            if v.get(rel):
                out.append((k, v[rel], rel))
    return out


def resolve_candidates(d, cands=None):
    VP = d["VP"]
    cands = candidates(d) if cands is None else cands
    parent = {}

    def find(x):
        while parent.get(x, x) != x:
            x = parent[x]
        return x
    for a, b, _ in _v31_merges(d):
        parent[a] = b
    for p in d["E"]["pair"]:
        if p["verdict"] == "NO_NEW_INFO":
            parent[p["a"]] = p["b"]
    verd = {}
    for p in d["E"]["pair"]:
        if p["verdict"] != "NO_NEW_INFO":
            verd[tuple(sorted((find(p["a"]), find(p["b"]))))] = p["verdict"]

    def tset(i):
        return {x.upper() for x in VP[i].get("t") or [] if isinstance(x, str) and x.strip() and x.upper() not in ("UNK", "?")}

    def tfset(i):
        return {x for x in VP[i].get("tf") or [] if x}
    res = {}
    for (a, b) in sorted(cands):
        ka, kb = find(a), find(b)
        if ka == kb:
            res[(a, b)] = "SAME_UNIT"
            continue
        pk = tuple(sorted((ka, kb)))
        if pk in verd:
            res[(a, b)] = verd[pk]
            continue
        A, B = tset(ka), tset(kb)
        if A and B and not A & B:
            res[(a, b)] = "AUTO_DIFFERENT_STOCK"
            continue
        FA, FB = tfset(ka), tfset(kb)
        if FA and FB and not FA & FB:
            res[(a, b)] = "AUTO_DIFFERENT_TIMEFRAME"
            continue
        ra, rb = _drange(VP[ka].get("d")), _drange(VP[kb].get("d"))
        if ra and rb and (ra[1] < rb[0] or rb[1] < ra[0]):
            res[(a, b)] = "AUTO_DIFFERENT_DATE"
            continue
        res[(a, b)] = "NEEDS_EYE"
    return cands, res


# ── الوحدات ───────────────────────────────────────────────────────────────────────────────────
def snapshot_files(d):
    """لقطةُ التدقيق: ملفّاتُ V3 (722) ‏+ ملفّاتُ B48 (46) — لا قائمةُ المجلّد الحيّة (الجامعُ يضيف بعدها)."""
    corp = {r["id"]: r["file"] for r in d["corpus"]}
    b48 = {it["image_id"]: it["file"] for it in d["b48m"]["items"]
           if it.get("file") and os.path.splitext(os.path.basename(it["file"]))[0] == it["image_id"]}   # MSG_* بلا ملفٍّ خاصّ
    return corp, b48


def units(d):
    corp, b48 = snapshot_files(d)
    parent = {}

    def find(x):
        while parent.get(x, x) != x:
            x = parent[x]
        return x

    def merge(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    newinfo = {m["id"] for m in d["E"]["member"] if m["verdict"] == "NEW_INFO"}
    for r in d["rec"]:
        if r["representative"] != r["id"] and r["id"] not in newinfo:
            merge(r["id"], r["representative"])
    for a, b, _ in _v31_merges(d):
        merge(a, b)
    for p in sorted(d["E"]["pair"], key=lambda x: (x["a"], x["b"])):
        if p["verdict"] == "NO_NEW_INFO":
            merge(p["a"], p["b"])
    for o in sorted(d["E"]["b48"], key=lambda x: x["id"]):
        if (o.get("dup") or {}).get("verdict") == "NO_NEW_INFO":
            merge(o["id"], o["dup"]["of"])
    files = sorted(corp) + sorted(b48)
    return {f: find(f) for f in files}


# ── العبارات لكلّ ملفّ ────────────────────────────────────────────────────────────────────────
def file_statements(d):
    """{ملف: [عبارة]} — عباراتُ V4 بتتبّعها ‏+ عباراتُ B48 ‏+ عباراتُ أعضاء العناقيد ذوي المعلومة الزائدة."""
    st = collections.defaultdict(list)
    for t in d["E"]["trace"]:
        st[t["unit"]].append(dict(t, src="V4"))
    for o in d["E"]["b48"]:
        for s in o["statements"]:
            st[o["id"]].append(dict(s, src="B48", eff=o.get("decision") or "INFO"))
    for o in d["E"]["member"]:
        for s in o.get("statements") or []:
            st[o["id"]].append(dict(s, src="MEMBER", eff="INFO"))
    return st


def _cited_by_rules(d):
    sup, con = collections.defaultdict(set), collections.defaultdict(set)
    for k, r in d["rules4"].items():
        for i in r.get("image_ids") or []:
            sup[i].add(k)
    for r in d["prov"]:
        for f in ("PRIMARY_SOURCE_IDS", "SUPPORTING_SOURCE_IDS", "DISCOVERY_DATASET", "GOLDEN_WITNESS_IDS"):
            for i in r.get(f) or []:
                sup[i].add(r["RULE_ID"])
        for i in r.get("CONTRADICTORY_SOURCE_IDS") or []:
            con[i].add(r["RULE_ID"])
    return sup, con


def analyse(d):
    """القلبُ: لكلّ ملفٍّ عمقُه ودورُه · ولكلّ وحدةٍ دورُها وعلوُّ معلومتها."""
    u = units(d)
    st = file_statements(d)
    sup, con = _cited_by_rules(d)
    corp, b48 = snapshot_files(d)
    case_units = {s.split("#")[0] for c in d["cases"] for s in c["sids"]}
    UNREAD = {o["id"] for o in d["E"]["not_used"] if o["verdict"] == "UNREADABLE_RESOLUTION"}
    newinfo = {m["id"] for m in d["E"]["member"] if m["verdict"] == "NEW_INFO"}
    newinfo_pair = {x for p in d["E"]["pair"] if p["verdict"] == "NEW_INFO" for x in (p["a"], p["b"])}
    dup_file = set()
    for r in d["rec"]:
        if r["representative"] != r["id"] and r["id"] not in newinfo:
            dup_file.add(r["id"])
    dup_file |= {a for a, b, _ in _v31_merges(d)}
    dup_file |= {p["a"] for p in d["E"]["pair"] if p["verdict"] == "NO_NEW_INFO"}
    dup_file |= {o["id"] for o in d["E"]["b48"] if (o.get("dup") or {}).get("verdict") == "NO_NEW_INFO"}

    def depth_rep(i):
        r = d["VP"][i]
        if i in UNREAD:
            return "PARTIALLY_ANALYZED", "صورةٌ مصغَّرةٌ غيرُ مقروءة"
        if not (r.get("a") and r.get("ab") and r.get("g")):
            return "PARTIALLY_ANALYZED", "سجلٌّ ينقصه الكاتبُ أو أساسُه أو النصّ"
        n = len(r.get("rules") or [])
        if sum(1 for t in st.get(i, []) if t["src"] == "V4") != n:
            return "PARTIALLY_ANALYZED", "عبارةٌ بلا صنفِ تتبّع"
        return "FULLY_ANALYZED", "قراءةُ V4 بالعين ‏+ تتبّعُ EX لكلّ عبارة"
    depth = {}
    for f in sorted(corp):
        if f in d["VP"]:
            depth[f] = depth_rep(f)
        elif f in d["MEM"]:
            m = d["MEM"][f]
            if m["verdict"] == "NEW_INFO":
                depth[f] = ("FULLY_ANALYZED", "قراءةُ EX بالعين (معلومةٌ زائدة مسجّلة)")
            else:
                depth[f] = None          # يرث ممثّله بعد الحساب
        else:
            depth[f] = ("NOT_ANALYZED", "لا سجلّ")
    for f in corp:
        if depth[f] is None:
            rd = depth[d["MEM"][f]["rep"]]
            depth[f] = (rd[0], f"مطابقٌ لممثّله {d['MEM'][f]['rep']} ({d['MEM'][f]['basis']}) — {rd[1]}")
    REQ = ("author", "date", "ticker", "tf", "annotations", "pattern", "structure", "indicators", "entry", "stop", "invalidation",
           "target", "decision", "context", "role")
    for f in sorted(b48):
        o = d["B48"].get(f)
        if not o:
            depth[f] = ("NOT_ANALYZED", "لا سجلّ")
        elif all(k in o for k in REQ) and o.get("context"):
            depth[f] = ("FULLY_ANALYZED", "قراءةُ EX بالعين بالحقول الأحد والعشرين")
        else:
            depth[f] = ("PARTIALLY_ANALYZED", "حقلٌ ناقص")

    def file_author(f):
        if f in d["VP"]:
            return d["VP"][f].get("a"), d["VP"][f].get("ab")
        if f in d["B48"]:
            return d["B48"][f].get("author"), "EX_EYE"
        if f in d["MEM"]:
            rep = d["MEM"][f]["rep"]
            return d["VP"][rep].get("a"), d["VP"][rep].get("ab")
        return None, None

    by_unit = collections.defaultdict(list)
    for f, root in u.items():
        by_unit[root].append(f)
    unit_info = {}
    for root, fs in sorted(by_unit.items()):
        sts = [s for f in fs for s in st.get(f, [])]
        auth = [file_author(f)[0] for f in fs]
        faisal = any(a in FAISAL_AUTHORS for a in auth)
        decs = {d["VP"][f].get("dec") for f in fs if f in d["VP"]} | {d["B48"][f].get("decision") for f in fs if f in d["B48"]}
        lv = any(d["VP"][f].get("lv") for f in fs if f in d["VP"]) or any(
            re.search(r"\d\.\d", d["B48"][f].get("annotations") or "") for f in fs if f in d["B48"])
        hi = bool(faisal and (sts or (decs & set(DECISION_WORDS)) or lv))
        cls = {s["cls"] for s in sts}
        b48roles = {d["B48"][f]["role"] for f in fs if f in d["B48"]}
        memroles = {d["MEM"][f].get("role") for f in fs if f in d["MEM"] and d["MEM"][f].get("role")}
        res = {d["VP"][f].get("res") for f in fs if f in d["VP"]}
        v31cls = {(d["v31"]["new"].get(f) or {}).get("source_class") or "" for f in fs}
        if any(f in case_units for f in fs) or "VALIDATION_CASE" in b48roles:
            role = "VALIDATION_CASE"
        elif any(s.get("contra") for s in sts) or any(con.get(f) for f in fs):
            role = "COUNTEREXAMPLE"
        elif cls & {"T-V4", "T-V31", "T-PROD", "T-CLOSED", "T-QUEUE", "T-NONE"} or any(sup.get(f) for f in fs) \
                or "RULE_EVIDENCE" in b48roles | memroles:
            role = "RULE_EVIDENCE"
        elif res and res <= set(NONEV_RES) or any(c.startswith("NON_EVIDENCE") for c in v31cls):
            role = "NON_EVIDENCE"
        elif res and res <= set(NOUNIQ_RES) and not sts and not any(f in newinfo_pair for f in fs):
            role = "NO_UNIQUE_INFO"
        else:
            role = "CONTEXT_ONLY"
        udepth = depth[root][0]
        unit_info[root] = dict(files=sorted(fs), role=role, high_info=hi, depth=udepth, faisal=faisal,
                               n_statements=len(sts), trace=dict(collections.Counter(s["cls"] for s in sts)),
                               corpus=all(f in corp for f in fs), b48=any(f in b48 for f in fs))
    file_role = {}
    for f, root in u.items():
        file_role[f] = "NO_UNIQUE_INFO" if f in dup_file else unit_info[root]["role"]
    return dict(unit=u, depth=depth, unit_info=unit_info, file_role=file_role, statements=st, dup_file=dup_file,
                author=file_author, cited=sup, contra_cited=con)


# ── تدقيقُ القواعد (§③ · §⑩) ──────────────────────────────────────────────────────────────────────
def rule_audit(d, A):
    sup_src, con_src = collections.defaultdict(set), collections.defaultdict(set)
    for f, rs in A["cited"].items():
        for r in rs:
            sup_src[r].add(f)
    for f, rs in A["contra_cited"].items():
        for r in rs:
            con_src[r].add(f)
    ex_sup, ex_con = collections.defaultdict(set), collections.defaultdict(dict)
    dec_by_rule = collections.defaultdict(collections.Counter)
    for f, sts in A["statements"].items():
        for s in sts:
            for p in s.get("ptr") or []:
                if p.startswith("rule:"):
                    ex_sup[p[5:]].add(f)
                    if s.get("eff") in DECISION_WORDS:
                        dec_by_rule[p[5:]][s["eff"]] += 1
            for c in s.get("contra") or []:
                ex_con[c["rule"]].setdefault(f, c["why"])

    def indep(fs):
        keys = set()
        for f in fs:
            r = A["unit"].get(f, f)
            v = d["VP"].get(r) or d["VP"].get(f) or {}
            t = tuple(sorted(v.get("t") or [])) or (r,)
            keys.add((t, v.get("d") or r))
        return len(keys)
    out = []
    for k, r in d["rules4"].items():
        p = d["PRV"].get(k, {})
        old_c = sorted(con_src.get(k, set()))
        new_c = sorted(f for f in ex_con.get(k, {}) if f not in old_c)
        supp = sorted((sup_src.get(k, set()) | ex_sup.get(k, set())) - set(old_c) - set(new_c))
        out.append(dict(rule=k, desc=r.get("description", ""), active=r.get("active"), status=r.get("status"),
                        decisionality=r.get("decisionality"), image_ids=sorted(r.get("image_ids") or []),
                        registry=p.get("REGISTRY_STATUS"), evidence=p.get("EVIDENCE_STATUS"),
                        support=supp, support_ex=sorted(ex_sup.get(k, set())), contra_old=old_c, contra_new=new_c,
                        contra_why={f: ex_con[k][f] for f in sorted(ex_con.get(k, {}))},
                        independent=indep(supp), decisions=dict(dec_by_rule.get(k, {})),
                        image_traceable=bool(supp or old_c or new_c)))
    return out


def queue_ex(d, A):
    qptr = collections.defaultdict(set)
    for f, sts in A["statements"].items():
        for s in sts:
            for p in s.get("ptr") or []:
                qptr[p].add(f)
    items = []
    for q in QUEUE_EX:
        sup = set(q["extra"])
        for p in q["trace_ptrs"]:
            sup |= qptr.get(p, set())
        items.append(dict(id=q["id"], cls=q["cls"], title=q["title"], observation=q["observation"], candidate_rule=q["candidate_rule"],
                          supporting_cases=sorted(sup), contradictory_cases=list(q["contradictory"]), confidence=q["confidence"],
                          generality=q["generality"], why_not_v4=q["why_not_v4"], v4_effect=q["v4_effect"],
                          trace_pointers=list(q["trace_ptrs"]), rules=list(q["rules"])))
    return dict(batch_id="EX_20261007", source="faisal_method_v41/corpus_audit/EX_PROTOCOL.md §⑥ · §⑦",
                rule="مرشَّحاتُ تدقيق اكتمال المدوّنة — لا يدخل V4 منها شيءٌ أثناء التحقّق الأماميّ · كلٌّ يحتاج تسجيلًا مسبقًا ودليلًا أماميًّا",
                generated_by="faisal_method_v41/corpus_audit/corpus_audit.py", items=items,
                updates=[dict(u, evidence=list(u["evidence"]), rules=list(u["rules"])) for u in QUEUE_UPDATES])


# ── الجردُ الرئيسيّ (§②) — صفٌّ لكلّ ملفٍّ بحقول المالك الأحد والعشرين ─────────────────────────────────
EFF_GROUP = {
    "PATTERN": ("PATTERN",),
    "STRUCTURE": ("STRUCTURE", "SEQUENCE", "S/R", "SR", "S_R", "PIPELINE", "MAP", "DEFINITION", "SCOPE", "HOLD"),
    "ENTRY": ("ENTRY", "ENTRY_MECHANISM", "ENTRY_EDU", "READY", "READINESS", "PRESS"),
    "STOP": ("STOP",),
    "INVALIDATION": ("INVALIDATION",),
    "TARGET": ("TARGET", "TARGET_TIMING", "TP_RULE", "EXIT", "PROJECTION", "SPLIT_WAIT_LEVELS"),
}


def _refs(sts, unit, group):
    return [f"{unit}#{s['i']}" for s in sts if s.get("eff") in EFF_GROUP[group]]


def _dup_status(d, A, f):
    v31 = {a: (b, rel) for a, b, rel in _v31_merges(d)}
    exm = {p["a"]: p for p in d["E"]["pair"] if p["verdict"] == "NO_NEW_INFO"}
    if f in d["MEM"]:
        m = d["MEM"][f]
        x = {"verdict": m["verdict"], "of": m["rep"], "relation": m["relation"], "basis": m["basis"], "cluster": m["cluster"],
             "max_block": m["max_block"]}
        if m.get("new_info"):
            x["new_info"] = m["new_info"]
        return x
    if f in v31:
        return {"verdict": "NO_NEW_INFO", "of": v31[f][0], "relation": "V31_" + v31[f][1].upper(), "basis": "V3.1 eye"}
    if f in exm:
        p = exm[f]
        return {"verdict": "NO_NEW_INFO", "of": p["b"], "relation": p["relation"], "basis": p["basis"]}
    if f in d["B48"] and d["B48"][f].get("dup"):
        x = d["B48"][f]["dup"]
        y = {"verdict": x["verdict"], "of": x["of"], "relation": x["relation"], "basis": "EX eye"}
        if x.get("new_info"):
            y["new_info"] = x["new_info"]
        return y
    rel = sorted({(p["b"] if p["a"] == f else p["a"]) for p in d["E"]["pair"] if p["verdict"] == "NEW_INFO" and f in (p["a"], p["b"])})
    return {"verdict": "UNIQUE", "kept_beside": rel} if rel else {"verdict": "UNIQUE"}


def inventory(d, A):
    corp, b48 = snapshot_files(d)
    rows = []
    ex_checks = collections.defaultdict(set)
    for o in d["E"]["trace"]:
        ex_checks[o["unit"]].add("trace")
    for o in d["E"]["not_used"]:
        ex_checks[o["id"]].add("not_used_recheck")
    for o in d["E"]["member"]:
        ex_checks[o["id"]].add("member_" + o["basis"])
    for o in d["E"]["pair"]:
        ex_checks[o["a"]].add("pair")
        ex_checks[o["b"]].add("pair")
    for f in sorted(corp):
        img, rec = d["IMG"][f], d["REC"][f]
        src_id = f if f in d["VP"] else rec["representative"]
        v = d["VP"][src_id]
        sts = [s for s in A["statements"].get(f, []) if s["src"] in ("V4", "MEMBER")]
        a, ab = A["author"](f)
        u = A["unit"][f]
        row = {
            "IMAGE_ID": f, "SOURCE": f"A1 · {img['family']} · V3", "HASH": img["sha256"],
            "PERCEPTUAL_HASH": {"dhash256": img.get("dhash256"), "phash64": img.get("phash64")},
            "DATE": v.get("d"), "TICKER": v.get("t") or [], "TIMEFRAME": v.get("tf") or [],
            "OCR": {"ref": "faisal_method_v3/image_corpus.json", "text_sha256": _sha_text(img.get("ocr_text")),
                    "chars": len(img.get("ocr_text") or "")},
            "ANNOTATIONS": v.get("lv") or None,
            "PATTERN": _refs(sts, f, "PATTERN"), "STRUCTURE": _refs(sts, f, "STRUCTURE"), "INDICATORS": v.get("ind") or [],
            "ENTRY": _refs(sts, f, "ENTRY"), "STOP": _refs(sts, f, "STOP"), "INVALIDATION": _refs(sts, f, "INVALIDATION"),
            "TARGET": _refs(sts, f, "TARGET"),
            "FAISAL_DECISION": {"decision": v.get("dec"), "author": v.get("a"), "is_faisal": v.get("a") in FAISAL_AUTHORS},
            "CONTEXT": {"kind": v.get("k"), "result_type": v.get("res"), "v4_use": rec.get("use"),
                        "statements": [f"{f}#{s['i']}" for s in sts]},
            "DUPLICATE_STATUS": _dup_status(d, A, f),
            "DERIVATIVE_STATUS": next((f"V31_{rel.upper()}:{b}" for a2, b, rel in _v31_merges(d) if a2 == f), "NONE"),
            "ANALYSIS_STATUS": f"{A['depth'][f][0]}/{A['file_role'][f]}",
            "UNIT_ID": u, "DEPTH": A["depth"][f][0], "DEPTH_BASIS": A["depth"][f][1], "ROLE": A["unit_info"][u]["role"],
            "FILE_ROLE": A["file_role"][f], "HIGH_INFO": A["unit_info"][u]["high_info"], "AUTHOR": a, "AUTHOR_BASIS": ab,
            "FIELDS_FROM": src_id, "TRACE": dict(sorted(collections.Counter(s["cls"] for s in sts).items())),
            "EX_CHECKS": sorted(ex_checks.get(f, ())),
        }
        rows.append(row)
    items = {it["image_id"]: it for it in d["b48m"]["items"]}
    for f in sorted(b48):
        o, it = d["B48"][f], items[f]
        sts = o["statements"]
        ocr = d["b48ocr"].get(f) or {}
        u = A["unit"][f]
        row = {
            "IMAGE_ID": f, "SOURCE": "A1 · TG · B48 (بوت التلغرام 2026-10-07)", "HASH": it["sha256"],
            "PERCEPTUAL_HASH": {"dhash256": it.get("dhash256"), "phash64": it.get("phash64")},
            "DATE": o.get("date"), "TICKER": o.get("ticker") or [], "TIMEFRAME": o.get("tf") or [],
            "OCR": {"ref": "faisal_method_v41/batches/B48_20261007/ocr_text.json", "text_sha256": (ocr.get("text_sha256") or "")[:16],
                    "tokens": ocr.get("n_tokens")},
            "ANNOTATIONS": o.get("annotations"), "PATTERN": o.get("pattern"), "STRUCTURE": o.get("structure"),
            "INDICATORS": o.get("indicators"), "ENTRY": o.get("entry"), "STOP": o.get("stop"), "INVALIDATION": o.get("invalidation"),
            "TARGET": o.get("target"),
            "FAISAL_DECISION": {"decision": o.get("decision"), "author": o.get("author"), "is_faisal": o.get("author") in FAISAL_AUTHORS},
            "CONTEXT": {"text": o.get("context"), "b48_class": it.get("class"), "statements": [f"{f}#{s['i']}" for s in sts]},
            "DUPLICATE_STATUS": _dup_status(d, A, f),
            "DERIVATIVE_STATUS": it.get("derivative_status") or "NONE",
            "ANALYSIS_STATUS": f"{A['depth'][f][0]}/{A['file_role'][f]}",
            "UNIT_ID": u, "DEPTH": A["depth"][f][0], "DEPTH_BASIS": A["depth"][f][1], "ROLE": A["unit_info"][u]["role"],
            "FILE_ROLE": A["file_role"][f], "HIGH_INFO": A["unit_info"][u]["high_info"], "AUTHOR": o.get("author"),
            "AUTHOR_BASIS": "EX_EYE", "FIELDS_FROM": f, "TRACE": dict(sorted(collections.Counter(s["cls"] for s in sts).items())),
            "EX_CHECKS": ["b48_eye"],
        }
        rows.append(row)
    for up in d["E"]["upload"]:       # غيابُه لا يُسقط البناء — يُسقط C1 (عددُ الصفوف لا يطابق اللقطة)
        rows.append({"IMAGE_ID": up["id"], "SOURCE": "A2 · مرفقُ الجلسة (لا يُدفَع)", "HASH": up["sha256"], "PERCEPTUAL_HASH": None,
                     "DATE": AUDIT_DATE, "TICKER": [], "TIMEFRAME": [], "OCR": None, "ANNOTATIONS": {"card": up["card"]},
                     "PATTERN": None, "STRUCTURE": None, "INDICATORS": None, "ENTRY": None, "STOP": None, "INVALIDATION": None,
                     "TARGET": None, "FAISAL_DECISION": None, "CONTEXT": {"text": up["note"], "result": up["result"]},
                     "DUPLICATE_STATUS": {"verdict": "UNIQUE"}, "DERIVATIVE_STATUS": "NONE",
                     "ANALYSIS_STATUS": "FULLY_ANALYZED/NON_EVIDENCE", "UNIT_ID": up["id"], "DEPTH": "FULLY_ANALYZED",
                     "DEPTH_BASIS": "بطاقةُ اختبارٍ أعمى قبل أيّ بحث", "ROLE": "NON_EVIDENCE", "FILE_ROLE": "NON_EVIDENCE",
                     "HIGH_INFO": False, "AUTHOR": "UNKNOWN", "AUTHOR_BASIS": "NONE", "FIELDS_FROM": up["id"], "TRACE": {},
                     "EX_CHECKS": ["upload_card"]})
    return rows


# ── الأرقامُ المجمَّعة ───────────────────────────────────────────────────────────────────────────
def numbers(d, A, RA, Q, cands_res):
    corp, b48 = snapshot_files(d)
    ui = A["unit_info"]
    fd = collections.Counter(x[0] for x in A["depth"].values())
    ud = collections.Counter(v["depth"] for v in ui.values())
    ur = collections.Counter(v["role"] for v in ui.values())
    fr = collections.Counter(A["file_role"].values())
    hi = [k for k, v in ui.items() if v["high_info"]]
    tr = collections.Counter(s["cls"] for sts in A["statements"].values() for s in sts)
    missed = collections.Counter(c for c, _ in {((s.get("missed") or {}).get("class"), (s.get("missed") or {}).get("queue"))
                                                  for sts in A["statements"].values() for s in sts if s["cls"] == "T-NONE"})
    con_old = sum(len(r["contra_old"]) for r in RA)
    con_new = sum(len(r["contra_new"]) for r in RA)
    return dict(
        files_a1=len(corp) + len(b48), files_corpus=len(corp), files_b48=len(b48), attachments=SNAPSHOT["session_attachments"],
        accessible_images=len(corp) + len(b48) + SNAPSHOT["session_attachments"],
        units=len(ui), units_corpus_root=sum(1 for k in ui if k in corp), units_b48_root=sum(1 for k in ui if k in b48),
        v3_clusters=len({d["REC"][f]["representative"] for f in corp}),
        member_new_info=sum(1 for m in d["E"]["member"] if m["verdict"] == "NEW_INFO"),
        v31_merges=len(_v31_merges(d)), ex_merges=sum(1 for p in d["E"]["pair"] if p["verdict"] == "NO_NEW_INFO"),
        b48_merged=sum(1 for o in d["E"]["b48"] if (o.get("dup") or {}).get("verdict") == "NO_NEW_INFO"),
        files_fully=fd["FULLY_ANALYZED"], files_partially=fd["PARTIALLY_ANALYZED"], files_superficial=fd["SUPERFICIAL"],
        files_ocr_only=fd["OCR_ONLY"], files_not_analyzed=fd["NOT_ANALYZED"],
        units_fully=ud["FULLY_ANALYZED"], units_partially=ud["PARTIALLY_ANALYZED"], units_not_analyzed=ud["NOT_ANALYZED"] + ud["OCR_ONLY"] + ud["SUPERFICIAL"],
        high_info=len(hi), high_info_fully=sum(1 for k in hi if ui[k]["depth"] == "FULLY_ANALYZED"),
        unit_roles=dict(ur), file_roles=dict(fr),
        files_contributing=sum(fr[r] for r in EVIDENCE_ROLES), files_no_unique=fr["NO_UNIQUE_INFO"],
        statements=sum(tr.values()), trace=dict(tr),
        v4_rules=len(RA), rules_image_traceable=sum(1 for r in RA if r["image_traceable"]),
        rules_inference_only=sorted(r["rule"] for r in RA if not r["image_traceable"]),
        confirmed_missed=missed["CONFIRMED_MISSED_RULE"], probable_missed=missed["PROBABLE_MISSED_RULE"],
        hypothesis=missed["HYPOTHESIS"],
        contradictions_old=con_old, contradictions_new=con_new, negative=len(NEGATIVE),
        queue_items=len(Q["items"]), queue_updates=len(Q["updates"]),
        candidates=len(cands_res), needs_eye=sum(1 for v in cands_res.values() if v == "NEEDS_EYE"),
        doc_only_refs=len(d["doc_only"]),
    )


# ── الوثائق ──────────────────────────────────────────────────────────────────────────────────────
def _ptr_md(p):
    kind, _, rest = p.partition(":")
    if kind == "doc":
        rel, _, sub = rest.partition("::")
        return f"`{rel}` «{sub.replace('`', '')}»"
    return f"`{p}`"


def _head(title):
    return (f"# {title}\n\n> 🧾 مولَّدٌ من `faisal_method_v41/corpus_audit/corpus_audit.py` (‏`EX_PROTOCOL.md` §⑪) — **لا رقمَ باليد** · "
            f"لقطةُ التدقيق {AUDIT_DATE} · V4 مجمَّدٌ لم يُمَسّ.\n\n")


def doc_sources(d, N):
    rows = [
        ("A1", "ملفّاتُ `faisal_images/` على main", "نعم", N["files_a1"], N["files_a1"], 0,
         f"{N['files_corpus']} (سجلّ V3 المجمَّد) ‏+ {N['files_b48']} (دفعة B48) — كلُّها في الجرد"),
        ("A2", "مرفقاتُ الجلسة", "نعم", N["attachments"], N["attachments"], 0, "شارتُ اختبار المالك الأعمى — NON_EVIDENCE · والصورةُ لا تُدفع"),
        ("A3", "تحديثاتُ بوت التلغرام المعلَّقة", "نعم", 0, 0, 0,
         f"الجامعُ بعد #558 (‏`{SNAPSHOT['collector_run_after_558']}`): 0 صورٍ جديدة"),
        ("A4", "وثائقُ المستودع (الكاتالوج · المسحان · الدفتر · الأرشيف · CLAUDE.md)", "نعم", "—", "—", "—",
         "تفسيراتٌ سابقة لا دليلٌ أوّليّ — تُستعمل مؤشّراتِ تتبّعٍ تُفحص نصًّا"),
        ("A5", "فروعُ git وتاريخُه", "نعم", SNAPSHOT["images_outside_main"], 0, 0,
         f"{SNAPSHOT['branches_scanned']} فرعًا: 0 صورٍ خارج main · ومنذ لقطة V3 (`{SNAPSHOT['v3_snapshot_commit']}`): "
         f"{SNAPSHOT['deleted_or_renamed_since_v3']} حذفٍ أو إعادةِ تسمية"),
        ("N1", "X مباشرةً · سجلُّ قناة التلغرام الكامل · محادثاتُ claude.ai الأخرى · artifacts أقدمُ من 7 أيّام", "لا", "مجهول", 0, "مجهول",
         "غيرُ متاحٍ من الحاوية (X محجوب · البوتُ يرى ما يُرسَل إليه وحدَه · لا وصولَ لمحادثاتٍ أخرى)"),
        ("N2", "«دليل طريقة فيصل» PDF · دليلُ إليوت · التسجيلُ الصوتيّ وتفريغُه", "لا", 3, 0, 3,
         "ليست في هذه الحاوية — حُلّلت في جلساتٍ سابقة (مستخلَصُها في الأرشيف) ولا تُدفَع (المستودعُ عامّ)"),
        ("N3", "الإحالاتُ بلا ملفّ (V3.1)", "لا", N["doc_only_refs"], 0, N["doc_only_refs"],
         "وصفُها النصّيّ في الوثائق وحدَه — لا صورةَ تُقرأ"),
        ("X", "الطبقاتُ المولَّدة (36) · صورةُ معيار التشغيل", "خارج المدوّنة", 37, "—", "—", "ليست دليلًا"),
    ]
    t = "| SOURCE | الوصف | ACCESSIBLE | ITEMS FOUND | PROCESSED | UNPROCESSED | REASON |\n|---|---|---|---|---|---|---|\n"
    t += "".join(f"| {a} | {b} | {c} | {e} | {f} | {g} | {h} |\n" for a, b, c, e, f, g, h in rows)
    return _head("SOURCE_INVENTORY — جردُ المصادر (§1)") + t + (
        "\n**الأثرُ المحتمل لغير المتاح على V4:** N1 قد يحوي قراراتٍ لفيصل لم تُلتقط (لا يُعرف عددُها) — وهي مادّةُ التحقّق الأماميّ لا التاريخيّ ·"
        " N2 مستخلَصُه موثَّقٌ سلفًا (ثلاثُ ميزاتِ عرض · `FAISAL_SOURCE_LEDGER.md`) · N3 نصٌّ بلا صورة لا يُعاد فحصُه.\n")


def doc_summary(d, A, N):
    ui = A["unit_info"]
    fam = collections.Counter(d["IMG"][f]["family"] for f in d["IMG"])
    auth = collections.Counter(A["author"](f)[0] for f in A["unit"])
    b48c = collections.Counter(it["class"] for it in d["b48m"]["items"] if it["image_id"] in d["B48"])
    t = _head("CORPUS_INVENTORY_SUMMARY — خلاصةُ الجرد الرئيسيّ (§2)")
    t += (f"## الوحدات\n- عناقيدُ V3: **{N['v3_clusters']}** ‏+ أعضاءٌ بمعلومةٍ زائدة **{N['member_new_info']}** − دمجُ V3.1 **{N['v31_merges']}** − دمجُ EX "
          f"**{N['ex_merges']}** = **{N['units_corpus_root']}** وحدةً للمدوّنة\n"
          f"- B48: {N['files_b48']} ملفًّا − {N['b48_merged']} نسخةً بلا معلومةٍ زائدة = **{N['units_b48_root']}** وحدة\n"
          f"- **المجموع {N['units']} وحدةً مستقلّة** ‏+ مرفقُ الجلسة (NON_EVIDENCE)\n\n")
    t += "## العمق (ملفّات · وحدات)\n| العمق | ملفّات | وحدات |\n|---|---|---|\n"
    fd = collections.Counter(x[0] for x in A["depth"].values())
    ud = collections.Counter(v["depth"] for v in ui.values())
    t += "".join(f"| {k} | {fd[k]} | {ud[k]} |\n" for k in DEPTHS)
    t += "\n## الدور (ملفّات · وحدات)\n| الدور | ملفّات | وحدات |\n|---|---|---|\n"
    fr = collections.Counter(A["file_role"].values())
    ur = collections.Counter(v["role"] for v in ui.values())
    t += "".join(f"| {k} | {fr[k]} | {ur[k]} |\n" for k in ROLES)
    t += (f"\n> VALIDATION_CASE = وحدةٌ فيها عبارةٌ من حالات V4 (**تاريخيّةٌ ملوَّثةٌ وصفيّة**) أو حالةٌ أماميّةٌ مختومة (**1**: CASE_0001) — "
          f"ليست {ur['VALIDATION_CASE']} حالةَ تحقّق.\n\n")
    t += (f"## عاليةُ المعلومة\n- **{N['high_info']}** وحدةً (كاتبُها فيصل ‏+ قرارٌ أو عبارةٌ أو مستوى مرسوم) — **{N['high_info_fully']}** منها FULLY_ANALYZED\n"
          f"- أساسُ الكاتب في سجلّ V4: الظاهرُ وأساسُ OCR وإسنادُ الكاتالوج مُفصَحٌ عنها في الجرد (`AUTHOR_BASIS`) · "
          f"و{sum(1 for r in d['vp'] if r.get('ab_basis'))} سجلًّا أساسُه مُعبّأٌ آليًّا في V4 («لم يُعَد فحصُها بالعين في V4»)\n\n")
    t += "## الأسر والكُتّاب\n" + " · ".join(f"{k} {v}" for k, v in sorted(fam.items())) + "\n\n"
    t += " · ".join(f"{k} {v}" for k, v in sorted(auth.items(), key=lambda x: (-x[1], str(x[0])))) + "\n\n"
    t += "## B48\n" + " · ".join(f"{k} {v}" for k, v in sorted(b48c.items())) + "\n"
    return t


def doc_duplicates(d, A, N, cands_res):
    t = _head("DUPLICATE_AUDIT — تدقيقُ التكرار (§4)")
    mem = d["E"]["member"]
    t += (f"## ① أعضاءُ عناقيد V3 ({len(mem)}) مقابل ممثّليهم\n"
          f"- بالبكسل (أقصى فرقٍ بين كتل 20×20 عند عرض 300 ≤ 12.3): **{sum(1 for m in mem if m['basis'] == 'pixel')}** · بالعين: **{sum(1 for m in mem if m['basis'] == 'eye')}**\n"
          f"- **NEW_INFO {sum(1 for m in mem if m['verdict'] == 'NEW_INFO')}** · NO_NEW_INFO {sum(1 for m in mem if m['verdict'] == 'NO_NEW_INFO')}\n\n")
    t += "| العضو | الممثّل | العلاقة | الحكم | المعلومةُ الزائدة |\n|---|---|---|---|---|\n"
    t += "".join(f"| `{m['id']}` | `{m['rep']}` | {m['relation']} | {m['verdict']} | {m.get('new_info') or '—'} |\n"
                 for m in mem if m["basis"] == "eye")
    rc = collections.Counter(cands_res.values())
    t += (f"\n## ② الممثّلون أزواجًا — {len(cands_res)} مرشَّحًا من أربعة مولِّدات (إحالة · أرقام · اقتباس · OCR)\n"
          + " · ".join(f"{k} {v}" for k, v in sorted(rc.items())) + "\n\n")
    t += "### الدمجُ (عضوٌ ⟵ حافظ): كلُّ ما في العضو مقروءٌ في الحافظ\n| العضو | الحافظ | العلاقة | الأساس | الملاحظة |\n|---|---|---|---|---|\n"
    t += "".join(f"| `{p['a']}` | `{p['b']}` | {p['relation']} | {p['basis']} | {p['note']} |\n"
                 for p in sorted(d["E"]["pair"], key=lambda x: x["a"]) if p["verdict"] == "NO_NEW_INFO")
    t += "\n### نسخٌ تبقى (NEW_INFO)\n| أ | ب | العلاقة | المعلومةُ الزائدة |\n|---|---|---|---|\n"
    t += "".join(f"| `{p['a']}` | `{p['b']}` | {p['relation']} | {p['note']} |\n"
                 for p in sorted(d["E"]["pair"], key=lambda x: (x["a"], x["b"])) if p["verdict"] == "NEW_INFO")
    t += "\n## ③ V3.1 (دمجٌ بصريّ سابق)\n" + " · ".join(f"`{a}` ⟵ `{b}` ({rel})" for a, b, rel in _v31_merges(d)) + "\n"
    t += "\n## ④ B48\n| الملف | النسخةُ من | العلاقة | الحكم | المعلومةُ الزائدة |\n|---|---|---|---|---|\n"
    t += "".join(f"| `{o['id']}` | `{o['dup']['of']}` | {o['dup']['relation']} | {o['dup']['verdict']} | {o['dup'].get('new_info') or '—'} |\n"
                 for o in sorted(d["E"]["b48"], key=lambda x: x["id"]) if o.get("dup"))
    t += "".join(f"| `{m['id']}` (بلا ملفّ) | `{m['dup_of']}` | {m['relation']} | {m['verdict']} | — |\n" for m in d["E"]["msg"])
    return t


def doc_traceability(d, A, N, RA):
    t = _head("RULE_TRACEABILITY — صورة ⟵ معلومة ⟵ قاعدة ⟵ تنفيذ · وبالعكس (§3 · §5)")
    tr = collections.Counter(s["cls"] for sts in A["statements"].values() for s in sts)
    basis = collections.Counter(s.get("basis") or s["src"] for sts in A["statements"].values() for s in sts)
    t += (f"## ① الاتّجاهُ الأوّل — كلُّ عبارةٍ قاعديّة لها صنفُ تتبّعٍ واحد ومؤشّرٌ يُفحص\n- العبارات: **{N['statements']}** "
          f"(‏V4 {sum(1 for o in d['E']['trace'])} · B48 {sum(len(o['statements']) for o in d['E']['b48'])} · أعضاءُ العناقيد "
          f"{sum(len(o.get('statements') or []) for o in d['E']['member'])})\n")
    t += "| الصنف | العدد |\n|---|---|\n" + "".join(f"| {k} | {tr[k]} |\n" for k in TRACE_CLASSES)
    t += "\n**أساسُ التتبّع:** " + " · ".join(f"{k} {v}" for k, v in sorted(basis.items())) + "\n"
    impl = collections.Counter()
    for sts in A["statements"].values():
        for s in sts:
            for p in s.get("ptr") or []:
                if p.startswith("v31:"):
                    impl[d["R31"][p[4:]].get("IMPLEMENTATION_STATUS")] += 1
    t += "\n**صفوفُ V3.1 المشار إليها بحالة تنفيذها:** " + " · ".join(f"{k} {v}" for k, v in sorted(impl.items())) + "\n"
    t += "\n## ② الاتّجاهُ العكسيّ — قاعدة ⟵ مصدر ⟵ دليل ⟵ تحقّق (قواعدُ V4 الـ21)\n"
    t += "| القاعدة | فاعلة | صورُ السجلّ | داعمٌ (وحدات) | مستقلّ | READY/WAIT/REJECT من العبارات | تعارضٌ قائم/جديد | حالةُ الدليل (V4.1) | التحقّق |\n|---|---|---|---|---|---|---|---|---|\n"
    for r in RA:
        dec = "/".join(str(r["decisions"].get(k, 0)) for k in ("READY", "WAIT", "REJECT"))
        t += (f"| `{r['rule']}` | {r['active']} | {len(r['image_ids'])} | {len(r['support'])} | {r['independent']} | {dec} | "
              f"{len(r['contra_old'])}/{len(r['contra_new'])} | {r['evidence']} | الأماميّ INSUFFICIENT (N=1) |\n")
    t += ("\n**بلا أيّ صورة (استنتاجٌ أو هندسة):** " + " · ".join(f"`{x}`" for x in N["rules_inference_only"]) +
          "\n\n## ③ استخلاصُ المنهج (§5) — ما تغطّيه العباراتُ بالأكثر\n")
    top = sorted(RA, key=lambda r: -len(r["support"]))[:10]
    t += " · ".join(f"`{r['rule']}` {len(r['support'])}" for r in top) + "\n"
    return t


def doc_contradictions(d, A, RA):
    t = _head("CONTRADICTION_AUDIT — تدقيقُ التعارض (§10 · §⑦)")
    t += ("> القائمُ = `CONTRADICTORY_SOURCE_IDS` في `V4_RULE_PROVENANCE.json` · الجديد = شاهدُ تعارضٍ سجّله EX في `eye_pass_ex.jsonl`. "
          "**لا تتغيّر حالةُ قاعدةٍ في V4** — التوصيةُ في الطابور.\n\n")
    rec = collections.defaultdict(list)          # من حقل `rules` في بنود الطابور وتحديثاته — لا خريطةَ باليد
    for q in QUEUE_EX:
        for r in q["rules"]:
            rec[r].append(q["id"])
    for u in QUEUE_UPDATES:
        for r in u["rules"]:
            rec[r].append(f"{u['updates']} ({u['id']})")
    t += "| RULE | SUPPORT | CONTRADICTIONS (قائم · جديد) | INDEPENDENT CASE COUNT | CONFIDENCE (V4.1) | STATUS |\n|---|---|---|---|---|---|\n"
    for r in RA:
        cons = " · ".join([f"`{x}`" for x in r["contra_old"]] + [f"`{x}`🆕" for x in r["contra_new"]]) or "—"
        status = "V4 بلا تغيير" + (f" ⟵ الطابور {' · '.join(rec[r['rule']])}" if rec.get(r["rule"]) else "")
        t += f"| `{r['rule']}` | {len(r['support'])} | {cons} | {r['independent']} | {r['evidence']} | {status} |\n"
    t += "\n## شواهدُ التعارض الجديدة بنصّها\n"
    for r in RA:
        for f, why in r["contra_why"].items():
            t += f"- `{r['rule']}` · `{f}` — {why}\n"
    return t


def doc_negative(d, A, RA):
    t = _head("NEGATIVE_EVIDENCE — الأدلّةُ السالبة وفواصلُ القرار (§6 · §7)")
    t += "## ① الأدلّةُ السالبة\n| # | الوحدات | النوع | الخلاصة | المؤشّر |\n|---|---|---|---|---|\n"
    t += "".join(f"| {n['id']} | {' · '.join('`' + u + '`' for u in n['units'])} | {n['kind']} | {n['text']} | {_ptr_md(n['ptr'])} |\n" for n in NEGATIVE)
    t += "\n## ② فواصلُ READY / WAIT / REJECT من العبارات (أيُّ قاعدةٍ تحمل كلمةَ القرار)\n| القاعدة | READY | WAIT | REJECT | WATCH |\n|---|---|---|---|---|\n"
    for r in sorted(RA, key=lambda x: -sum(x["decisions"].values())):
        if r["decisions"]:
            t += f"| `{r['rule']}` | " + " | ".join(str(r["decisions"].get(k, 0)) for k in ("READY", "WAIT", "REJECT", "WATCH")) + " |\n"
    t += ("\n## ③ FALSE READY أوّلًا — ما يحرس READY وما لا يحرسه\n"
          "- **محروسٌ في V4:** الصلاحيّةُ (`R4-VAL-GRP-01` · `R4-VAL-OFF-01` · `R4-VAL-SHORT-01`) ‏+ `R4-OP-01` ‏+ `R4-INV-01` ‏+ `R4-LOC-01` — "
          "وبلا مصدرٍ أماميٍّ للصلاحيّة يمتنع V4 عن READY بالبناء (FVO1).\n"
          "- **غيرُ محروسٍ في V4 (مرشَّحاتُ الطابور):** «ساعةُ النضج» (`RQ-EX-01`: READY على مقسَّمٍ لم يبلغ متوسّطَه) · "
          "مؤشّرُ القروبات السعريّ (`RQ-EX-02`).\n"
          "- **READY فشل في المدوّنة:** NE-03 (تسريبٌ ورفعُ أفراد) — سببُه صلاحيّةٌ لم تكن مرئيّة وقتَ القرار.\n")
    return t


def doc_missed(d, A, Q):
    t = _head("MISSED_INFORMATION — المعلومةُ الفائتة (§9 · §6) وطابورُ V4.2")
    nones = [(f, s) for f, sts in sorted(A["statements"].items()) for s in sts if s["cls"] == "T-NONE"]
    t += "## ① لم تُستخرج قطّ (T-NONE)\n| العبارة | الصنف | البند |\n|---|---|---|\n"
    t += "".join(f"| `{f}#{s['i']}` | {s['missed']['class']} | `{s['missed']['queue']}` |\n" for f, s in nones)
    t += "\n## ② بنودُ الطابور (لا تدخل V4)\n"
    for it in Q["items"]:
        t += (f"\n### {it['id']} · {it['title']} ({it['cls']})\n- **الملاحظة:** {it['observation']}\n- **القاعدةُ المرشَّحة:** {it['candidate_rule']}\n"
              f"- **قواعدُ V4 المعنيّة:** {' · '.join('`' + r + '`' for r in it['rules']) or '— (فجوةٌ لا قاعدةَ لها في V4)'}\n"
              f"- **حالاتٌ تدعم ({len(it['supporting_cases'])}):** {' · '.join('`' + x + '`' for x in it['supporting_cases'])}\n"
              f"- **حالاتٌ تعارض:** {' · '.join(it['contradictory_cases']) or 'لا شيء معروف'}\n"
              f"- **الثقة:** {it['confidence']} · **العموم:** {it['generality']}\n- **لماذا لا تدخل V4 الآن:** {it['why_not_v4']} · **الأثر:** {it['v4_effect']}\n")
    t += "\n## ③ تحديثاتٌ لبنودٍ قائمة (سجلٌّ جديد — البندُ المختوم لا يُعدَّل)\n"
    t += "".join(f"- **{u['id']} ⟵ {u['updates']}:** {u['note']} ({' · '.join('`' + e + '`' for e in u['evidence'])})"
                 + (f" · قواعدُ V4: {' · '.join('`' + r + '`' for r in u['rules'])}" if u["rules"] else "") + "\n" for u in Q["updates"])
    t += ("\n## ④ لا إفراطَ في الملاءمة (§11)\nلا بندَ لرمزٍ أو تاريخٍ أو لقطةٍ بعينها · ولا لحالةٍ ذهبيّة (DXST · VEEE · RAYA · ATMV) · ولا من الشارت الأخير وحدَه · "
          "ولا لتحسين رقم — والقفلُ يُسقط قاعدةً مرشَّحةً فيها رمزُ سهمٍ أو تاريخ.\n")
    return t


def doc_collector(d):
    meta = [r for r in (_jl("telegram_collect_meta.jsonl") if os.path.isfile(_p("telegram_collect_meta.jsonl")) else [])
            if r.get("run_id") == SNAPSHOT["b48_collector_run"]]          # لقطةُ التدقيق — ما يُلحق بعدها لا يغيّر هذا المخرَج
    src = open(_p("telegram_collect.py"), encoding="utf-8").read()
    has_fp = "def forward_public(" in src and "from_recipient" in src
    runs = sorted({r.get("run_id") for r in meta})
    fwd = sum(1 for r in meta if "forward" in r)
    t = _head("COLLECTOR_PROVENANCE_CHECK — فحصُ جامع #558 (§13)")
    t += ("| البند | الحالة | الدليل |\n|---|---|---|\n"
          f"| الكود: مصدرُ التوجيه بلا هويّة لكلّ مُرسِل ‏+ `from_recipient` | {'✅' if has_fp else '❌'} | `telegram_collect.py` (`forward_public`) · قفل TCM7 |\n"
          f"| صفوفُ البيانات المحفوظة | {len(meta)} صفًّا من التشغيلة {', '.join('`' + r + '`' for r in runs)} | `telegram_collect_meta.jsonl` |\n"
          f"| صفوفٌ تحمل مصدرَ التوجيه | {fwd} | جُمعت قبل #558 (`{SNAPSHOT['collector_558_commit']}`) ⟵ **ضاع ولا يُخترَع رجعيًّا** |\n"
          f"| تشغيلُ الجامع بعد #558 | 0 صورٍ جديدة | `{SNAPSHOT['collector_run_after_558']}` |\n")
    t += ("\n**الحكم:** الكودُ والأقفالُ ✅ · **التحقّقُ الحيّ لم يحدث بعد** (لا رسالةَ موجَّهة وصلت منذ #558) · ومصدرُ التوجيه لدفعة B48 **مفقودٌ** "
          "ولا يُعاد بناؤه — يبقى `date_source` للحالة CASE_0001 كما خُتم.\n")
    return t


def b48_validation(d, A):
    """§12 من الدفعة المختومة وأدوار الجرد — لا رقمَ باليد: الحالاتُ الأماميّة (مؤشّر `case:CASE_`) غيرُ النسخ الأوضح لحالاتٍ تاريخيّة."""
    b48 = sorted(snapshot_files(d)[1])
    vc = [f for f in b48 if A["file_role"][f] == "VALIDATION_CASE"]
    ptrs = {f: [p for s in A["statements"].get(f, []) for p in s.get("ptr") or [] if p.startswith("case:")] for f in vc}
    pros_files = [f for f in vc if any(p.startswith("case:CASE_") for p in ptrs[f])]
    agg = d["b48r"]["aggregate"]
    return dict(files=len(b48), msgs=len(d["E"]["msg"]), vc_files=len(vc), pros_files=len(pros_files),
                pros_cases=sorted({p[5:] for f in pros_files for p in ptrs[f] if p.startswith("case:CASE_")}),
                hist_cases=sorted({p[5:] for f in vc if f not in pros_files for p in ptrs[f]}),
                rows=[(r["CASE_ID"], r["symbol"], r["V4_STATE"], r["FAISAL_STATE"]) for r in d["b48r"]["rows"]],
                n=agg["N"], exact=agg["exact"], aw=agg["always_wait_baseline"], n_min=d["n_min"],
                roles=dict(sorted(collections.Counter(A["file_role"][f] for f in b48).items())))


def doc_b48_block(d, A, N):
    v = b48_validation(d, A)
    edge = v["exact"] > v["aw"]["agree"]
    return ("\n## دفعة الـ48 (§12)\n"
            f"- وصل 48 = {v['files']} ملفًّا ‏+ رسائلُ مكرَّرةٌ بلا ملفّ ({v['msgs']}) ⟵ {N['units_b48_root']} وحدة · "
            f"**حالاتُ التحقّق الأماميّ الكاملة: {v['n']}** (" + " · ".join(f"{a} · {b} · V4 {c} · فيصل {e}" for a, b, c, e in v["rows"]) + ") · "
            f"V4 = فيصل {v['exact']}/{v['n']} و«دائمًا WAIT» {v['aw']['agree']}/{v['aw']['n']} ⟵ "
            + ("ميزةٌ وصفيّة" if edge else "**لا ميزةَ مُثبتة**") + " · "
            + (f"**PROSPECTIVE VALIDATION REMAINS INSUFFICIENT** (N={v['n']} دون {v['n_min']})" if v["n"] < v["n_min"] else "N بلغ الحدّ") + ".\n"
            f"- ملفّاتُ B48 بدور VALIDATION_CASE ({v['vc_files']}) = {v['pros_files']} للحالة الأماميّة ({' · '.join(v['pros_cases'])}) "
            f"‏+ {v['vc_files'] - v['pros_files']} نسخٌ أوضحُ لحالاتٍ تاريخيّةٍ مكشوفة ({' · '.join(v['hist_cases'])}) — ملوَّثةٌ لا تُحسب تحقّقًا.\n"
            "- الباقي ليس 48 حالة — أدوارُ ملفّات B48 في الجرد: " + " · ".join(f"{k} {n}" for k, n in v["roles"].items()) + "\n")


def doc_report(d, A, N, RA, Q, cands_res, core):
    """معيارُ الإغلاق يُقرأ من مشاكل التحقّق (`validate_core`) لا من حسابٍ موازٍ — فأيُّ عيبٍ يقلب الجوابَ إلى NO."""
    c = {k: not any(p.startswith(k + ":") for p in core) for k in ("C1", "C2", "C3", "C4", "C5", "C6")}
    other = [p for p in core if not p.startswith(("C1:", "C2:", "C3:", "C4:", "C5:", "C6:"))]
    yes = all(c.values()) and not other
    t = _head("CORPUS_EXHAUSTIVENESS_REPORT — تقريرُ اكتمال المدوّنة")
    t += "## معيارُ الإغلاق (§⑨ · مكتوبٌ قبل النتيجة)\n| # | الشرط | النتيجة |\n|---|---|---|\n"
    lab = {"C1": "لكلّ ملفٍّ صفّ (لقطةُ التدقيق)", "C2": "صفرُ وحدةٍ عاليةِ المعلومة في NOT_ANALYZED/OCR_ONLY/SUPERFICIAL",
           "C3": "صفرُ عبارةٍ بلا صنف · وكلُّ T-NONE مصنَّف وفي الطابور", "C4": "لكلّ عضوٍ ومشتقٍّ ومرشَّحِ تكرارٍ حكم",
           "C5": "لكلّ «NOT_USED» حكمُ إعادة فحص", "C6": "غيرُ المتاح مسمًّى بسببه وأثره (SOURCE_INVENTORY.md)"}
    t += "".join(f"| {k} | {lab[k]} | {'✅' if v else '❌'} |\n" for k, v in c.items())
    t += "\n## تنبّؤاتُ §⑩\n"
    b48set = set(snapshot_files(d)[1])
    q1 = [it["id"] for it in Q["items"] if it["cls"] in ("PROBABLE_MISSED_RULE", "HYPOTHESIS") and b48set & set(it["supporting_cases"])]
    q1_other = [it["id"] for it in Q["items"] if b48set & set(it["supporting_cases"])] + \
               [u["id"] for u in Q["updates"] if b48set & set(u["evidence"])]
    n_mem, n_nu = len(d["E"]["member"]), len(d["E"]["not_used"])
    unt = [s for sts in A["statements"].values() for s in sts if s.get("basis") == "review:untraced"]
    unt_ok = sum(1 for s in unt if s["cls"] != "T-NONE")
    q = {
        "Q1": ("صورُ B48 غيرُ الحالة تُخرج مرشَّحًا (PROBABLE أو HYPOTHESIS)", bool(q1),
               " · ".join(q1) if q1 else f"خاب: أسهمت في بنودٍ وتحديثات ({' · '.join(q1_other)}) لا مرشَّحًا جديدًا"),
        "Q2": ("أعضاءُ العناقيد بـNEW_INFO ≤ 10%", bool(n_mem) and N["member_new_info"] / n_mem <= 0.10, f"{N['member_new_info']}/{n_mem}"),
        "Q3": ("≥ 80% من العبارات غيرِ المتتبَّعة تُتتبَّع بالمحتوى", bool(unt) and unt_ok / len(unt) >= 0.8, f"{unt_ok}/{len(unt)}"),
        "Q4": ("CONFIRMED_MISSED_RULE ثلاثةٌ فأقلّ", N["confirmed_missed"] <= 3, f"{N['confirmed_missed']}"),
        "Q5": ("لا تغييرَ مطلوبًا على V4 قبل الأماميّ", True, "حكم: كلُّ ما وُجد بندُ طابور (لا عيبَ تنفيذٍ في V4)"),
        "Q6": ("الجوابُ النهائيّ YES محدودةٌ بالمتاح", yes, "انظر الجواب"),
    }
    t += "| # | التنبّؤ | صدق؟ | الدليل |\n|---|---|---|---|\n" + "".join(
        f"| {k} | {a} | {'✅' if b else '❌ (يُنشر)'} | {e} |\n" for k, (a, b, e) in q.items())
    t += "\n## 50 · 70 · 100 (§8)\n| الرقم | المعنى | الوحدات | المؤشّر |\n|---|---|---|---|\n"
    t += "".join(f"| {x['k']} | {x['meaning']} | {' · '.join('`' + u + '`' for u in x['units'])} | {_ptr_md(x['ptr'])} |\n" for x in TARGETS)
    t += doc_b48_block(d, A, N)
    t += "\n## طابورُ V4.2 (§14)\n" + " · ".join(f"`{x}`" for x in sorted(queue_ids(d))) + \
         f" — منها {N['queue_items']} بندًا جديدًا من EX و{N['queue_updates']} تحديثاتٍ لبنودٍ قائمة (`MISSED_INFORMATION.md`)\n"
    t += ("\n## سلامةُ البرمجيّات (§15)\n- السويّةُ بوّابةٌ بخروج 0 · أقفالُ EXA تُسقطها طفراتُها · `--check` يعيد التوليد ويقارن بايتًا بايتًا · "
          "لا شبكةَ ولا بياناتِ سوق (لا نظرَ للأمام) · V4 مجمَّدٌ (FV41) ودفعةُ B48 مختومة (BIM9) لم تُمسّا.\n")
    t += "\n## كتلةُ الأعداد (§16)\n```\n"
    t += (f"TOTAL ACCESSIBLE IMAGES ............ {N['accessible_images']} ({N['files_a1']} في faisal_images ‏+ {N['attachments']} مرفق)\n"
          f"UNIQUE EVIDENCE UNITS .............. {N['units']} ‏+ المرفق (NON_EVIDENCE)\n"
          f"FULLY / PARTIALLY / OCR ONLY / NOT ANALYZED (ملفّات) ... {N['files_fully']} / {N['files_partially']} / {N['files_ocr_only']} / {N['files_not_analyzed']}\n"
          f"FULLY / PARTIALLY / NOT ANALYZED (وحدات) ............. {N['units_fully']} / {N['units_partially']} / {N['units_not_analyzed']}\n"
          f"HIGH-INFORMATION / HIGH-INFO FULLY ANALYZED ........ {N['high_info']} / {N['high_info_fully']}\n"
          f"IMAGES CONTRIBUTING EVIDENCE / NO UNIQUE INFO ...... {N['files_contributing']} / {N['files_no_unique']}\n"
          f"V4 RULES / DIRECT IMAGE TRACEABILITY / INFERENCE-ONLY ... {N['v4_rules']} / {N['rules_image_traceable']} / {len(N['rules_inference_only'])}\n"
          f"CONFIRMED / PROBABLE MISSED INFO ................... {N['confirmed_missed']} / {N['probable_missed']}\n"
          f"CONTRADICTIONS (قائم ‏+ جديد) / NEGATIVE EVIDENCE CASES ... {N['contradictions_old']} ‏+ {N['contradictions_new']} / {N['negative']}\n"
          f"INACCESSIBLE SOURCES ............................... N1 (X · قناةُ التلغرام كاملة · محادثاتٌ أخرى · artifacts قديمة) · N2 (3) · N3 ({N['doc_only_refs']} إحالة)\n"
          f"MATERIAL UNREVIEWED EVIDENCE ....................... NO (في المتاح)\n```\n")
    t += ("\n## الجواب\n> **Can we honestly say that we have extracted essentially everything methodologically useful that is currently accessible "
          "from the complete Faisal corpus?**\n\n")
    if yes:
        t += ("**YES — محدودةٌ بالمتاح.** الدليل: الشروطُ الستّة أعلاه ✅ — كلُّ ملفٍّ في اللقطة له صفّ · كلُّ وحدةٍ عاليةِ المعلومة "
              f"({N['high_info']}) مقروءةٌ كاملًا · كلُّ عبارةٍ ({N['statements']}) لها صنفُ تتبّعٍ ومؤشّرٌ يُفحص آليًّا · كلُّ مرشَّحِ تكرار "
              f"({N['candidates']}) وكلُّ عضو عنقودٍ ({n_mem}) وكلُّ «NOT_USED» ({n_nu}) له حكم · وما فات ({N['confirmed_missed']} مؤكَّدة · "
              f"{N['probable_missed']} محتملة) وفجواتُ V4 والتعارضاتُ في الطابور.\n"
              "**وحدُّها:** N1 (X مباشرةً · سجلُّ القناة الكامل · محادثاتٌ أخرى) قد يحوي قراراتٍ لم تُلتقط — طريقُها الاستلامُ الأماميّ لا هذا التدقيق · "
              "وN2 مستخلَصٌ سابقًا · وN3 نصٌّ بلا صورة.\n")
    else:
        t += "**NO** — " + " · ".join([k for k, v in c.items() if not v] + other[:10]) + "\n"
    return t


def build(d=None):
    d = load() if d is None else d
    A = analyse(d)
    cands, cres = resolve_candidates(d)
    RA = rule_audit(d, A)
    Q = queue_ex(d, A)
    N = numbers(d, A, RA, Q, cres)
    inv = inventory(d, A)
    ctx = dict(d=d, A=A, RA=RA, Q=Q, N=N, cres=cres, inv=inv)
    ctx["core"] = validate_core(ctx)
    out = {
        OUT_INV: "{\n" + f' "meta": {json.dumps(dict(audit_date=AUDIT_DATE, generated_by="faisal_method_v41/corpus_audit/corpus_audit.py", fields=list(inv[0].keys()), numbers=N), ensure_ascii=False, sort_keys=True)},\n'
                 + ' "rows": [\n' + ",\n".join("  " + json.dumps(r, ensure_ascii=False, sort_keys=True) for r in inv) + "\n ]\n}\n",
        OUT_QUEUE: json.dumps(Q, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        "SOURCE_INVENTORY.md": doc_sources(d, N),
        "CORPUS_INVENTORY_SUMMARY.md": doc_summary(d, A, N),
        "DUPLICATE_AUDIT.md": doc_duplicates(d, A, N, cres),
        "RULE_TRACEABILITY.md": doc_traceability(d, A, N, RA),
        "CONTRADICTION_AUDIT.md": doc_contradictions(d, A, RA),
        "NEGATIVE_EVIDENCE.md": doc_negative(d, A, RA),
        "MISSED_INFORMATION.md": doc_missed(d, A, Q),
        "COLLECTOR_PROVENANCE_CHECK.md": doc_collector(d),
        "CORPUS_EXHAUSTIVENESS_REPORT.md": doc_report(d, A, N, RA, Q, cres, ctx["core"]),
    }
    return out, ctx


# ── التحقّق (يستعمله `--check` والأقفال) ───────────────────────────────────────────────────────────
PRIVATE_NAME_HASHES = ("0099a2202ae63c63", "0dec1d606b104b63", "1573557bf6e35e8d", "15ca919efa9c1ea6", "1bbd1a4e54a8c768", "2e48004a833cb430", "350f67d924ba24de", "37937dcd4d1c2097", "37b3fbcab172a422", "3b22a42e58aaeddd", "3f0c9b03e8e39b03", "41d18df3842c2569", "4ce71482d7ee5ce8", "5904410b2f52901f", "5d8e35318411d21b", "5f0c8befd87aec7e", "63e7ac892afd3385", "6ba0e95e87412ae5", "9ec2826a33408729", "ad49945b7555af20", "d08f341de4dee7a5", "d7df7809554a054d", "e5fd31aff6f31113", "ecf9c6eca7229adf", "f1f2fd2878071515")   # بصماتُ أسماءٍ خاصّة ظهرت في سجلّ V4 — الأسماءُ نفسُها لا تُكتب هنا


def privacy_problems(texts):
    out = []
    for name, t in texts.items():
        for m in re.findall(r"@[A-Za-z0-9_]{2,}", t):
            if m != "@kisar_":
                out.append(f"{name}: معرّفُ حسابٍ {m}")
        for m in re.findall(r"(?<![\w.])\d{8,10}(?![\w.])", t):
            out.append(f"{name}: رقمٌ يشبه معرّفًا ({len(m)} خانات)")
        toks = re.findall(r"[A-Za-z.]{3,}|[؀-ۿ]{3,}", t)
        toks += [a + " " + b for a, b in zip(toks, toks[1:])]
        hs = {hashlib.sha256(x.encode("utf-8")).hexdigest()[:16] for x in toks}
        bad = hs & set(PRIVATE_NAME_HASHES)
        if bad:
            out.append(f"{name}: اسمٌ خاصّ ({len(bad)})")
    return out


def validate(out=None, ctx=None):
    """كلُّ العيوب: محتوى الجرد (`validate_core`) ‏+ الخصوصيّة على المخرَجات."""
    if out is None:
        out, ctx = build()
    return list(ctx["core"]) + privacy_problems(dict(out, **{os.path.basename(EYE): open(_p(EYE), encoding="utf-8").read()}))


def corpus_tickers(d):
    """رموزُ المدوّنة (V4 ‏+ B48) — قائمةُ ما يُمنع في نصّ القاعدة المرشَّحة (§11: لا قاعدةَ لرمزٍ بعينه)."""
    t = {x.upper() for r in d["vp"] for x in r.get("t") or [] if isinstance(x, str)} | \
        {x.upper() for o in d["E"]["b48"] for x in o.get("ticker") or []}
    return t - {"UNK", "?", "READY", "WAIT", "REJECT", "EMA", "RSI", "MACD"}


def overfit_problems(items, tickers):
    """§11 — القاعدةُ المرشَّحة لا تحمل رمزَ سهمٍ من المدوّنة ولا تاريخًا (لا رقعةَ سهمٍ ولا رقعةَ يوم)."""
    out = []
    for q in items:
        hit = set(re.findall(r"(?<![\w-])[A-Z]{2,5}(?![\w-])", q["candidate_rule"])) & tickers
        if hit:
            out.append(f"§11: رمزٌ في قاعدةٍ مرشَّحة {q['id']}: {sorted(hit)}")
        if re.search(r"\b20\d\d-\d\d", q["candidate_rule"]):
            out.append(f"§11: تاريخٌ في قاعدةٍ مرشَّحة {q['id']}")
    return out


def validate_core(ctx):
    d, A, cres = ctx["d"], ctx["A"], ctx["cres"]
    probs = []
    corp, b48 = snapshot_files(d)
    for f, rel in sorted(list(corp.items()) + list(b48.items())):
        if not os.path.isfile(_p(rel)):
            probs.append(f"C1: ملفٌّ مفقود {rel}")
    sha = {r["IMAGE_ID"]: r["HASH"] for r in ctx["inv"]}
    for f, rel in sorted(list(corp.items()) + list(b48.items())):
        if os.path.isfile(_p(rel)) and _sha_file(_p(rel)) != sha.get(f):
            probs.append(f"C1: بصمةٌ لا تطابق {f}")
    if len(ctx["inv"]) != len(corp) + len(b48) + SNAPSHOT["session_attachments"]:
        probs.append("C1: صفوفُ الجرد لا تطابق اللقطة")
    qids = queue_ids(d)
    for f, sts in A["statements"].items():
        al = [d["B48"][f]["dup"]["of"]] if f in d["B48"] and d["B48"][f].get("dup") else []
        for s in sts:
            probs += [f"C3: {f}#{s.get('i')}: {e}" for e in statement_problems(d, s, f, qids, al)]
    allst = {(r["id"], i) for r in d["vp"] for i in range(len(r.get("rules") or []))}
    got = [(o["unit"], o["i"]) for o in d["E"]["trace"]]
    if len(got) != len(set(got)) or set(got) != allst:
        probs.append("C3: تتبّعُ عبارات V4 ناقصٌ أو مكرَّر")
    for o in d["E"]["trace"]:
        v = d["VP"].get(o["unit"])
        if v and o["i"] < len(v["rules"]) and _sha_text(v["rules"][o["i"]]["txt"]) != o["sha"]:
            probs.append(f"C3: بصمةُ العبارة لا تطابق {o['unit']}#{o['i']}")
    if any(v == "NEEDS_EYE" for v in cres.values()):
        probs.append("C4: مرشَّحُ تكرارٍ بلا حكم")
    members = {r["id"] for r in d["rec"] if r["representative"] != r["id"]}
    if set(d["MEM"]) != members:
        probs.append("C4: أعضاءُ العناقيد لا يطابقون سجلّ V4")
    for m in d["E"]["member"]:
        if m["verdict"] not in ("NEW_INFO", "NO_NEW_INFO") or m["relation"] not in DUP_RELATIONS:
            probs.append(f"C4: حكمُ عضوٍ غيرُ صالح {m['id']}")
        if m["verdict"] == "NEW_INFO" and not m.get("new_info"):
            probs.append(f"C4: معلومةٌ زائدة بلا نصّ {m['id']}")
    for p in d["E"]["pair"]:
        if p["a"] not in d["VP"] or p["b"] not in d["VP"] or p["relation"] not in DUP_RELATIONS:
            probs.append(f"C4: زوجٌ غيرُ صالح {p['a']}|{p['b']}")
    for o in d["E"]["b48"]:
        if o.get("dup") and o["dup"]["verdict"] not in ("NEW_INFO", "NO_NEW_INFO"):
            probs.append(f"C4: مشتقٌّ بلا حكم {o['id']}")
    nu = {r["id"] for r in d["rec"] if r["representative"] == r["id"] and r["use"] == "NOT_USED"}
    if set(d["NU"]) != nu or any(o["verdict"] not in ("CONSISTENT", "UNREADABLE_RESOLUTION") for o in d["E"]["not_used"]):
        probs.append("C5: إعادةُ فحص NOT_USED ناقصة")
    if set(d["B48"]) != set(b48):
        probs.append("B48: سجلُّ العين لا يطابق ملفّات الدفعة")
    for f, o in d["B48"].items():
        if f in A["file_role"] and o.get("role") != A["file_role"][f]:
            probs.append(f"B48: دورُ العين لا يطابق التعريف {f}")
    for k, v in A["unit_info"].items():
        if v["high_info"] and v["depth"] in ("NOT_ANALYZED", "OCR_ONLY", "SUPERFICIAL"):
            probs.append(f"C2: وحدةٌ عاليةُ المعلومة غيرُ مقروءة {k}")
    probs += overfit_problems(ctx["Q"]["items"], corpus_tickers(d))
    for q in ctx["Q"]["items"] + ctx["Q"]["updates"]:
        for r in q["rules"]:
            if r not in d["rules4"]:
                probs.append(f"§14: قاعدةٌ غيرُ موجودة {r} في {q['id']}")
    for q in ctx["Q"]["items"]:
        if not (q["trace_pointers"] or q["rules"]):
            probs.append(f"§14: بندٌ بلا مرساة (لا مؤشّرَ تتبّعٍ ولا قاعدة) {q['id']}")
        traced = {f for f, sts in A["statements"].items() for s in sts if f"queue:{q['id']}" in (s.get("ptr") or [])}
        if not traced <= set(q["supporting_cases"]):
            probs.append(f"§14: بندٌ لا يضمّ وحداتِ تتبّعه {q['id']}")
    for n in NEGATIVE:
        e = pointer_problem(d, n["ptr"])
        if e:
            probs.append(f"§6: {n['id']}: {e}")
    for x in TARGETS:
        e = pointer_problem(d, x["ptr"])
        if e:
            probs.append(f"§8: {e}")
    known = set(corp) | set(b48)
    for x in [u for n in NEGATIVE for u in n["units"]] + [u for t in TARGETS for u in t["units"]] + \
            [u for q in QUEUE_UPDATES for u in q["evidence"]] + [u for q in QUEUE_EX for u in q["extra"]]:
        if x not in known:
            probs.append(f"وحدةٌ غيرُ موجودة {x}")
    src = doc_sources(d, ctx["N"])
    for k in ("N1", "N2", "N3"):
        row = next((ln for ln in src.splitlines() if ln.startswith(f"| {k} |")), "")
        cells = [x.strip() for x in row.split("|")[1:-1]]
        if len(cells) != 7 or cells[2] != "لا" or len(cells[6]) < 10:
            probs.append(f"C6: مصدرٌ غيرُ متاحٍ بلا تسميةٍ أو سببٍ {k}")
    return probs


def main(argv):
    out, ctx = build()
    if "--check" in argv:
        bad = []
        for name, text in out.items():
            path = os.path.join(HERE, name)
            if not os.path.isfile(path) or open(path, encoding="utf-8").read() != text:
                bad.append(f"مخرَجٌ لا يطابق التوليد: {name}")
        bad += validate(out, ctx)
        live = {x for x in os.listdir(_p("faisal_images")) if x.lower().endswith(IMG_EXT)}
        snap = {os.path.basename(v) for v in list(snapshot_files(ctx["d"])[0].values()) + list(snapshot_files(ctx["d"])[1].values())}
        extra = sorted(live - snap)
        print(f"EX --check: {len(bad)} عيب · ملفّاتٌ بعد اللقطة (استلامٌ أماميّ لا عيب): {len(extra)}")
        for b in bad[:40]:
            print("  ❌", b)
        return 1 if bad else 0
    for name, text in out.items():
        with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
            f.write(text)
    N = ctx["N"]
    print(f"EX: {N['files_a1']} ملفًّا ‏+ {N['attachments']} مرفق · {N['units']} وحدة · عاليةُ المعلومة {N['high_info']} (كاملة {N['high_info_fully']}) · "
          f"عبارات {N['statements']} · فائتة {N['confirmed_missed']}/{N['probable_missed']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
