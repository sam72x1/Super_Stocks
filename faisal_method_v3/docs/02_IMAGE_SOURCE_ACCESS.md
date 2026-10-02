# 02 · جردُ المصادر وصلاحيةُ الوصول (§2)

سلّمُ الحالة (§2): KNOWN_TO_EXIST · ACCESSIBLE · RETRIEVED · INSPECTED · ANALYZED · USED_AS_EVIDENCE · NOT_ACCESSIBLE — **لا يُفترض وصولٌ قبل التحقّق** ولا يُختلق محتوى ما لم يُصَل إليه.

| المصدر | الاسم | الحالة (مسارٌ متحقَّق) | العدد |
|---|---|---|---|
| SRC-REPO | faisal_images/ على main (e939785e0) | KNOWN_TO_EXIST ⟵ ACCESSIBLE ⟵ RETRIEVED ⟵ INSPECTED ⟵ ANALYZED ⟵ USED_AS_EVIDENCE | 722 |
| SRC-GIT-HISTORY | تاريخُ git (38,741 commit · غيرُ ضحل) | ACCESSIBLE ⟵ RETRIEVED ⟵ INSPECTED | — |
| SRC-BRANCHES | فروعُ الريموت (51) والوسوم (1) | ACCESSIBLE ⟵ INSPECTED | — |
| SRC-TELEGRAM-BOT | بوتُ التلغرام (getUpdates عبر telegram_collect.yml) | ACCESSIBLE ⟵ RETRIEVED ⟵ INSPECTED ⟵ ANALYZED ⟵ USED_AS_EVIDENCE | — |
| SRC-SESSION-UPLOADS | مرفقاتُ محادثة هذه الجلسة على القرص (/root/.claude/uploads/<session>) | ACCESSIBLE ⟵ RETRIEVED ⟵ INSPECTED | — |
| SRC-CONVERSATION-TRANSCRIPTS | سجلّاتُ المحادثات (jsonl) وصورُها المضمَّنة | KNOWN_TO_EXIST ⟵ NOT_ACCESSIBLE | — |
| SRC-PDF-FAISAL-GUIDE | «دليل طريقة فيصل لفلترة الأسهم» (94 صفحة · 78 صورةً مضمَّنة) | KNOWN_TO_EXIST ⟵ ACCESSIBLE ⟵ RETRIEVED ⟵ INSPECTED ⟵ ANALYZED ⟵ USED_AS_EVIDENCE | — |
| SRC-PDF-ELLIOTT | «موجات إليوت — RTL مع جميع الصور التعليمية» (57 صفحة · 48 صورة) | KNOWN_TO_EXIST ⟵ ACCESSIBLE ⟵ RETRIEVED ⟵ INSPECTED | — |
| SRC-AUDIO | تسجيلٌ صوتيّ (ogg · 12.3 ميغا) وتفريغُه (txt · 33.8 ك) | KNOWN_TO_EXIST ⟵ ACCESSIBLE | — |
| SRC-X-LIVE | حسابُ فيصل على X مباشرةً (@kisar_) | KNOWN_TO_EXIST ⟵ NOT_ACCESSIBLE | — |
| SRC-ACTIONS-ARTIFACTS | artifacts على GitHub Actions | KNOWN_TO_EXIST ⟵ ACCESSIBLE | — |
| SRC-REPO-DOCS | وثائقُ المستودع السابقة (الكاتالوج · المسحان PASS2/PASS3 · دفترُ المصا | ACCESSIBLE ⟵ RETRIEVED ⟵ INSPECTED ⟵ ANALYZED ⟵ USED_AS_EVIDENCE | — |
| SRC-OCR | محرّكُ OCR | ACCESSIBLE ⟵ USED_AS_EVIDENCE | — |
| SRC-DOC-ONLY-IMAGES | صورٌ تذكرها الوثائق ولا ملفَّ لها في المدوَّنة (دفعاتٌ قُرئت في محادثا | KNOWN_TO_EXIST ⟵ NOT_ACCESSIBLE | 101 |

## الخلاصة (مؤكَّد)
- `corpus_images_in_repo`: 722
- `non_evidence_image_in_repo_root`: operating_standard_v1.jpg (معيار التشغيل — ليس دليلَ منهج)
- `independent_units_after_dedup`: 609
- `new_images_collected_this_mission`: 11
- `images_lost_in_git_history`: 0
- `images_only_on_other_branches`: 0
- `doc_only_image_ids`: 101

## ما لم يُصَل إليه — ولماذا (بلا تخمينٍ لمحتواه)
- **SRC-CONVERSATION-TRANSCRIPTS** — 
- **SRC-X-LIVE** — 
- **SRC-DOC-ONLY-IMAGES** — 

🔒 **لا يُدفَع:** دليلُ طريقة فيصل (PDF) · دليلُ إليوت · التفريغُ الصوتيّ · مرفقاتُ الجلسة (المستودعُ عامّ) — يُستشهد بها بالصفحة وحدَها.
