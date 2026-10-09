# SOURCE_RECOVERY_AUDIT — تدقيقُ استعادة المصادر (2026-10-09)

> أرقامُ هذا الملفّ من `faisal_engine/out/source_audit.json` (يبنيها `source_audit.py` من الملفّات لا باليد).

## ① المدوّنة — المصالحة
- `faisal_method_v3/image_corpus.json`: **722 صورة** (SHA/dHash/pHash) ⟵ وحداتٌ مستقلّة بعد التكرار **609** (مرورُ العين V4 609/609).
- `MASTER_CORPUS_INVENTORY.json` (V4.1 corpus audit): **769 ملفًّا** (722 ‏+ دفعة 48 ‏− … بحسب الجرد) · وحدات **604** · عاليةُ المعلومة **565** · مُحلَّلٌ جزئيًّا **2**.
- حالةُ التحليل: FULLY_ANALYZED/NO_UNIQUE_INFO 165 · FULLY_ANALYZED/CONTEXT_ONLY 192 · FULLY_ANALYZED/RULE_EVIDENCE 181 · FULLY_ANALYZED/VALIDATION_CASE 203 · FULLY_ANALYZED/COUNTEREXAMPLE 17 · FULLY_ANALYZED/NON_EVIDENCE 9 · PARTIALLY_ANALYZED/CONTEXT_ONLY 2.
- القناة: APP 8 · CH 22 · EDU 13 · IMG 105 · TG 548 · WA 2 · X 70 · مرفقُ الجلسة (لا يُدفَع) 1.
- المؤلّف: APP 33 · F 576 · U 31 · EDU 58 · FG 2 · TP 22 · AI 6 · FA 7 · FO 5 · UNKNOWN 17 · F_inferred 4 · THIRD_PARTY 8 (F = فيصل · EDU/TP/THIRD_PARTY = غيرُه · U = المستخدم).
- التكرار: {'DUPLICATE/DERIVATIVE': 174, 'UNIQUE': 595}.

## ② فحصُ العين في هذه المهمّة (تغطيةٌ صادقة)
- الموروثُ: مرورٌ كامل 609/609 وحدة (V4 · 2026-10-02) ‏+ جردٌ 769/769 (V4.1 · 2026-10-07) ‏+ تدقيقٌ أعمى 30/30 (T-HS) — **وسومٌ موروثة لا أُعيد فحصُها كلُّها هنا**.
- أُعيد في هذه المهمّة فحصُ **4 صورٍ** هي مصادرُ القواعد الحاكمة للمحرّك، وطابق نصُّها ما في السجلّ:
  - `X_20260918_85_YMT`: «اذا ماكسر القاع اكثر من 5 جلسات يصعد 20٪ بعد القاع · يرجع يختبر الدعم · الدخول بعد الاختبار طلبات فوارق 5 سنت عند الدعم · يهمك قراءة الاخبار هل هناك طرح اسهم كذلك الشورت»
  - `IMG_0531`: «لكل 10 الاف سهم = 10٪ تقريبا هبوط · RSI من 22 ل 27 · قاع 2 تذبذب 2.20-2.40 · قبل يصعد بيوم ضغط من المضارب قريبا من القاع 2.10-2.20 · الطلبات جاهزة 2.10-2.30 · مع وقف قاع · هدف اول 30٪»
  - `IMG_0150`: «اسهم التقسيم: اذا قسم ولاصعد راقبه متوسط حركه 20 > 30 يوم · الشورت 550 الف تابعه لين يبقى تحت 20 الف · ثباته فوق 1 نقرر · ليست قاعده ولكن تطبق ع 80٪»
  - `TG_50584`: «نظرية الارتكاز: 1- الاخبار الاعلانات 2- متوسطات 20/30/50 3- الشورت ⟵ 1- القاع 2- ارتداد لاختبار المقاومه 20٪ غالبا 3- ثبات القاع او سحب السيوله 5٪ ادنى شمعة القاع 4- ثبات سعري بعد سحب السيوله = تحقيق الاهداف»
- ⚠️ **ما لم يُعَد فحصُه:** 605 وحدةً تبقى على وسومها الموروثة (الجردُ V4.1 ومرورُ V4).

## ③ المصادر — متاحٌ / مفحوصٌ / غيرُ متاح
| المعرّف | المصدر | الحالة |
|---|---|---|
| S-REPO-IMG | faisal_images/ + faisal_batches/ + chart_cards (repo) | ACCESSIBLE · INSPECTED (eye pass 609/609 units · inventory 769 files) |
| S-TG-BOT | Telegram bot updates (telegram_collect.py · scheduled) | ACCESSIBLE · collector pulls only what is sent to the bot; 2026-10-09 pull = 0 |
| S-TG-CHANNEL | Faisal's Telegram channel history (pre-bot) | UNAVAILABLE (no API access; only images the owner forwarded) |
| S-X | X (@kisar_) posts | UNAVAILABLE live (blocked from runners); 70 X images present in corpus via owner forwards |
| S-WA | WhatsApp cases | ACCESSIBLE only as 2 forwarded images (NUWE · SXTC); chat export UNAVAILABLE |
| S-APP | Faisal's app screenshots | ACCESSIBLE · 8 images (V3) · 1 dated WATCH unit (VEEE) |
| S-GIT | git history of state files (weekly_watchlist · company_cache · near_watch) | ACCESSIBLE · used by Phase 5 (S01/S02) for bot-era floats/borrow only |
| S-SEC | SEC EDGAR submissions (fm_forensics/data/sec_2026-10-08.json.gz · 234/238 ok) | ACCESSIBLE · dated filings · used for offering validity |
| S-BARS | TradingView daily bars frozen 2026-10-08 (232/238 symbols · from 2025-01-01) | ACCESSIBLE · split-adjusted · 6 symbols without bars |
| S-PDF | منهج فيصل.pdf + Elliott guide + audio transcript | ACCESSIBLE locally · NOT PUSHED (public repo) · tagged faisal_adopted |
| S-SESSIONS | earlier Claude sessions / artifacts (Phase A probe) | INSPECTED by Phase A: NEW_TO_CORPUS 0 of 9,930 records |

## ④ «أمثلةُ الأسهم الإضافيّة خارج حالات واتساب» — هل وُجدت؟
- حالاتُ واتساب في المدوّنة **صورتان فقط** (NUWE, SXTC) — ولا نصَّ محادثة.
- قراراتُ فيصل المؤرَّخة (FOCUS/WATCH/READY/ENTRY · `phase3/FAISAL_TIMELINE.csv`): **88 وحدةً على 45 رمزًا**، منها **42 رمزًا خارج واتساب**: AMIX, ATPC, BETA, BRTX, CANF, CDIO, CETX, CIIT, CRE, CUPR, DCOY, DKI, DXST, EDBL, EHGO, ELAB, ELPW, FRSX, GCTK, HUBC, IPDN, LABT, LIMN, MI, MNDR, MSGY, NRSN, OMH, ONCO, PIII, PPBT, SLXN, SMX, SPRC, STKH, SVRE, TRUG, UPC, WORX, YMT, ZCMD, ZNB.
- بحسب نوع الدليل (كلُّ ما يخصّ فيصل في الخطّ الزمنيّ):
  - APP_SCREENSHOT: VEEE
  - CHART_IMAGE: CANF, CUPR, DXST, JEM, LABT, MNDR, NUWE, ONCO, PAVS, SLXN, SPRC, UNK, UPC, WORX, ZCMD, ZNB
  - OTHER: DCOY, DRMA, VEEE
  - TELEGRAM: ADIL, ADVB, BETA, BNAI, BRTX, CANF, CDIO, CIIT, CRE, DCOY, DSY, DXST, EDBL, EHGO, ELAB, ELPW, ENPH, ENVB, EZRA, FGF, FIEE, FRSX, FUBO, FULC, GCTK, GWAV, HAO, HCAI, HUBC, HWH, IMCC, IPDN, JAGX, LABT, LIMN, LNAI, MI, MTEX, NAMM, NCT, NRSN, NUWE, NXTT, OMH, ONCO, PAVS, PIII, PPCB, PRFX, QMMM, RGC, SBDS, SCNI, SMX, SNAL, SNGX, SPHL, SPPL, SPRC, STKH, SXTC, TRUG, VEEE, VMAR, WHLR, WORX, XCUR, ZCMD
  - X_POST: AMIX, ATPC, BTOG, CETX, CUPR, DKI, GRI, HCWB, KWM, LABT, MSGY, PPBT, SGRX, SVRE, SXTC, UNK, YMT
- بلا شموعٍ في الملفّ المجمَّد: ATPC, LABT, MI, UNK (ATPC/LABT بلا شموع TradingView · MI/UNK هُويّةٌ غيرُ محسومة).
- **الجواب:** الأمثلةُ الإضافيّة **موجودةٌ في المستودع** (ملفّاتُ X/تلغرام/شارتات أرسلها المالك وأُرشفت في `faisal_images/`) ولا حاجةَ لمصدرٍ خارجيّ؛ وما لم يُستعَد: سجلُّ قناة فيصل قبل البوت، وX الحيّ، ونصُّ واتساب.

## ⑤ غيرُ المحسوم
- Faisal channel history before the bot (not retrievable)
- X live timeline (blocked)
- WhatsApp chat text (only 2 images)
- 10 chat images cited in Phase 3 (not recovered)
- float/borrow/short dated before bot logs (no source)
