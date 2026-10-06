# 13 — الوصولُ إلى المصادر V4 (§6)

## ① V4 (مُتحقَّقٌ اليوم)
| المصدر | الحالة | السبب الدقيق |
|---|---|---|
| TradingView (الشارت · الماسح) | AVAILABLE (من Actions وحدَه) | fetch: 1 تشغيلة · 79 من 80 رمزًا · بلا تسجيل دخول · لا واجهةَ رسميّة |
| Yahoo (yfinance) | PARTIALLY_AVAILABLE | ATMV «Quote not found» · شموعٌ لغيره |
| Polygon | UNAVAILABLE | الاشتراك منتهٍ منذ 2026-09-29 (403/429) |
| GitHub artifacts | UNAVAILABLE من الجلسة | التنزيلُ محجوب ⟵ المخرجاتُ أجزاءٌ في السجلّ (V4OUT) |
| روابطُ السجلّ الموقَّعة (blob) | UNAVAILABLE | الوكيلُ يردّ CONNECT 403 ⟵ السجلُّ عبر أداة GitHub ونصُّ الجلسة |
| X / تويتر | UNAVAILABLE | لا وصول · لقطاتُ X في المدوّنة وحدَها |
| محادثاتُ Claude/Claude Code الأخرى | UNAVAILABLE | لا تعرضها البيئة |
| سجلُّ تلغرام الكامل | PARTIALLY_AVAILABLE | صورُ البوت المحفوظة وحدَها (11 من الدفعة الأخيرة) |
| مدوّنةُ الصور في المستودع | AVAILABLE | 722/722 موجودة · SHA 722 |
| صورٌ مذكورةٌ غائبة | UNAVAILABLE | IMG_0485/0487/0489/0490 (النهج العلميّ) · IMG_0098/0125 (KST/كلنجر) |

## ② سجلُّ V3 (للمقارنة · `faisal_method_v3/source_access.json`)
| المعرّف | الحالة | السبب |
|---|---|---|
| SRC-REPO | KNOWN_TO_EXIST · ACCESSIBLE · RETRIEVED · INSPECTED · ANALYZED · USED_AS_EVIDENCE |  |
| SRC-GIT-HISTORY | ACCESSIBLE · RETRIEVED · INSPECTED |  |
| SRC-BRANCHES | ACCESSIBLE · INSPECTED |  |
| SRC-TELEGRAM-BOT | ACCESSIBLE · RETRIEVED · INSPECTED · ANALYZED · USED_AS_EVIDENCE |  |
| SRC-SESSION-UPLOADS | ACCESSIBLE · RETRIEVED · INSPECTED | لم تُنسخ المرفقاتُ إلى المستودع — الأربعُ والخمسون المطابقةُ موجودةٌ فيه أصلًا والتسعُ مصنَّفةٌ أعلاه |
| SRC-CONVERSATION-TRANSCRIPTS | KNOWN_TO_EXIST · NOT_ACCESSIBLE | رفض مُصنِّفُ الصلاحيات قراءةَ السجلّات بحثًا عن الصور في هذه الجلسة ⟵ لم يُلتفّ عليه · ومحادثاتُ claude.ai الأخرى غيرُ مرئيّةٍ من الحاوية أص |
| SRC-PDF-FAISAL-GUIDE | KNOWN_TO_EXIST · ACCESSIBLE · RETRIEVED · INSPECTED · ANALYZED · USED_AS_EVIDENCE |  |
| SRC-PDF-ELLIOTT | KNOWN_TO_EXIST · ACCESSIBLE · RETRIEVED · INSPECTED |  |
| SRC-AUDIO | KNOWN_TO_EXIST · ACCESSIBLE | لا يُدفَع · التفريغُ آليٌّ مشوَّش (وسمُه faisal_adopted في الذاكرة) · لم يُستعمَل في هذه المهمّة سوى ما سبق توثيقُه |
| SRC-X-LIVE | KNOWN_TO_EXIST · NOT_ACCESSIBLE | EGRESS_BLOCKED — بروكسي الشبكة يحجب x.com (محاولةٌ واحدة 2026-10-02) |
| SRC-ACTIONS-ARTIFACTS | KNOWN_TO_EXIST · ACCESSIBLE | faisal-images (نسخةُ أمانٍ 7 أيام لكلّ سحب) = نسخةٌ من المستودع لا مصدرٌ جديد · وartifacts التحقيق السابق (hs_forensic) مستعمَلةٌ في وثائقها |
| SRC-REPO-DOCS | ACCESSIBLE · RETRIEVED · INSPECTED · ANALYZED · USED_AS_EVIDENCE | تفسيراتٌ سابقة تُقرأ مقابل الصورة لا بدلًا منها · والإحالاتُ لكلّ صورةٍ في image_provenance.json (doc_mentions) |
| SRC-OCR | ACCESSIBLE · USED_AS_EVIDENCE |  |
| SRC-DOC-ONLY-IMAGES | KNOWN_TO_EXIST · NOT_ACCESSIBLE | وصفُها النصّيّ في الوثائق متاح (تفسيرٌ سابق) والصورةُ نفسُها غائبة ⟵ تُستشهَد بوصفها «doc_only» ولا تُعَدّ دليلًا بصريًّا · وبعضُها قد يكون  |
