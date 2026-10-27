# B36_20261027 — تقريرُ الاستلام والختم (قبل V4 · بلا قرار فيصل)

> الختمُ بالبروتوكول المجمَّد (`final_protocol.py seal` · التعديل 1) **قبل** تشغيل V4 وقبل أيّ قراءةٍ استكشافيّة — أمرُ المالك 2026-10-27 «اختمها أوّلًا ولا تقرأ صورةً قبل الختم».
> قراءةُ العين هنا = الحقولُ العمياء وحدَها (الرمز · التاريخ · الفريم · الكاتب · وجودُ عبارة قرار · المصدريّة) — بلا قرارٍ ولا دخولٍ ولا وقفٍ ولا هدف.

## ① الاستلام

| | العدد |
|---|---|
| رسائلُ وصلت (61 صفًّا في `telegram_collect_meta.jsonl` · 13:15:32Z…13:18:08Z) | 61 |
| مكرَّرٌ تخطّاه الجامعُ (dhash) | 25 |
| حُفظ جديدًا (`5432e669c` · تشغيلة 40519535590) | 36 |
| عدُّ المالك (TG_76000…76031 ‏+ 76039) | 33 — والفرقُ TG_75997/75998/75999: أوّلُ ثلاثٍ في الألبوم الأوّل (13:15:32Z) |

**المُرسِل:** المالك (بتصريحه 2026-10-27) · وصفوفُ الجامع `from_admin=false · from_recipient=true` لأن حسابه المُرسِل مستلمٌ مُعرَّف لا أوّلُ معرّفٍ في `TELEGRAM_CHAT_ID` — والسجلُّ إلحاقيٌّ فالتصحيحُ في `annotations.json → source.sender`.

## ② الأصنافُ السبعة (مختومة)

| الصنف | العدد |
|---|---|
| UNKNOWN | 10 |
| INSUFFICIENT_CONTEXT | 7 |
| DERIVATIVE | 6 |
| CONTAMINATED | 6 |
| NEW_PROSPECTIVE | 5 |
| DUPLICATE | 2 |

## ③ لكلّ صورة

| الصورة | الصنف | السبب | الرمز | تاريخُ القرار (نيويورك) | المصدريّة | الحالة |
|---|---|---|---|---|---|---|
| TG_75997 | NEW_PROSPECTIVE | — | CYCU | 2026-10-23 | LOW | CASE_0004 |
| TG_75998 | NEW_PROSPECTIVE | — | ICMB | 2026-10-24 | LOW | CASE_0005 |
| TG_75999 | UNKNOWN | AUTHOR_NOT_ESTABLISHED | JEM | — | UNKNOWN | — |
| TG_76000 | UNKNOWN | AUTHOR_NOT_ESTABLISHED | JEM | — | UNKNOWN | — |
| TG_76001 | UNKNOWN | AUTHOR_NOT_ESTABLISHED | — | — | UNKNOWN | — |
| TG_76002 | UNKNOWN | AUTHOR_NOT_ESTABLISHED | — | — | UNKNOWN | — |
| TG_76003 | UNKNOWN | AUTHOR_NOT_ESTABLISHED | BRTX | — | UNKNOWN | — |
| TG_76004 | NEW_PROSPECTIVE | — | BKYI | 2026-10-22 | MEDIUM | CASE_0006 |
| TG_76005 | DERIVATIVE | C6:TG_76004 | BKYI | — | UNKNOWN | — |
| TG_76006 | DERIVATIVE | C6:TG_76004 | BKYI | — | UNKNOWN | — |
| TG_76007 | DUPLICATE | SAME_DECISION:CASE_0006 | BKYI | 2026-10-22 | LOW | — |
| TG_76008 | DERIVATIVE | C6:TG_76007 | BKYI | — | UNKNOWN | — |
| TG_76009 | CONTAMINATED | C5:EX:TG_2080 | ELAB | 2026-10-20 | MEDIUM | — |
| TG_76010 | CONTAMINATED | C5:EX:TG_50587,EX:TG_57878,EX:TG_57879,EX:TG_57880,EX:TG_578 | CIIT | 2026-10-20 | LOW | — |
| TG_76011 | UNKNOWN | AUTHOR_NOT_ESTABLISHED | WORX | — | UNKNOWN | — |
| TG_76012 | DUPLICATE | SAME_DECISION:CASE_0007 | ANPA | 2026-10-14 | LOW | — |
| TG_76013 | NEW_PROSPECTIVE | — | ANPA | 2026-10-14 | MEDIUM | CASE_0007 |
| TG_76014 | CONTAMINATED | C5:EX:IMG_0152,EX:TG_1826,EX:TG_1828,EX:TG_1829,EX:TG_2205,E | ZCMD | 2026-10-13 | MEDIUM | — |
| TG_76015 | UNKNOWN | AUTHOR_NOT_ESTABLISHED | AEHL | — | UNKNOWN | — |
| TG_76016 | CONTAMINATED | C5:EX:TG_50828,EX:X_20260918_23_watchlist | CETX | 2026-09-28 | LOW | — |
| TG_76017 | CONTAMINATED | C5:EX:TG_50828,EX:X_20260918_23_watchlist | CETX | 2026-09-28 | LOW | — |
| TG_76018 | CONTAMINATED | C5:EX:TG_50828,EX:X_20260918_23_watchlist | CETX | 2026-10-10 | LOW | — |
| TG_76019 | INSUFFICIENT_CONTEXT | NO_TICKER | — | 2026-10-10 | LOW | — |
| TG_76020 | NEW_PROSPECTIVE | — | NCT | 2026-10-10 | LOW | CASE_0008 |
| TG_76021 | INSUFFICIENT_CONTEXT | DATE_NOT_ESTABLISHED | FBGL | — | UNKNOWN | — |
| TG_76022 | DERIVATIVE | C6:TG_76021 | FBGL | — | UNKNOWN | — |
| TG_76023 | DERIVATIVE | C6:TG_76021 | FBGL | — | UNKNOWN | — |
| TG_76024 | INSUFFICIENT_CONTEXT | NO_DECISION | GMEX | 2026-10-10 | LOW | — |
| TG_76025 | INSUFFICIENT_CONTEXT | NO_DECISION | GMEX | 2026-10-10 | LOW | — |
| TG_76026 | UNKNOWN | AUTHOR_NOT_ESTABLISHED | NTCL | — | UNKNOWN | — |
| TG_76027 | UNKNOWN | AUTHOR_NOT_ESTABLISHED | DKI | — | UNKNOWN | — |
| TG_76028 | DERIVATIVE | C2:TG_1827,TG_1908,X_20260827_raya_notready,X_20260827_raya_ | GMEX | 2026-10-10 | LOW | — |
| TG_76029 | UNKNOWN | AUTHOR_NOT_ESTABLISHED | SUGP | — | UNKNOWN | — |
| TG_76030 | INSUFFICIENT_CONTEXT | NO_TICKER | — | 2026-10-08 | LOW | — |
| TG_76031 | INSUFFICIENT_CONTEXT | NO_TICKER | — | — | UNKNOWN | — |
| TG_76039 | INSUFFICIENT_CONTEXT | NO_DECISION | MI | — | UNKNOWN | — |

## ④ حدودُ الصدق

- **TG_76028 (GMEX)** صُنّف DERIVATIVE بـC2 (قالبُ منشور X الداكن نفسُه عند TG_1827/TG_1908) — والعينُ ترى شارتًا مختلفًا · المصنِّفُ المجمَّد لا يُتجاوَز (§⑦) ⟵ يُفصَح.
- **TG_76001 (بطاقةُ نصّ «شموع الفوليوم 2 > 2.20»)** بلا كاتبٍ ولا رمزٍ في الصورة ⟵ AUTHOR_NOT_ESTABLISHED · ونسبتُها إلى JEM/فيصل استنتاجٌ من جيرانها لا يُختم.
- التواريخُ المستنتَجة (CYCU · ICMB · CIIT · CETX · GMEX · BKYI TG_76007) من إغلاق اللقطة مقابل `near_watch.json` وساعة الجهاز — LOW ⟵ SECONDARY · وICMB له بديلٌ أضعف (10-10).
- **ANPA (CASE_0007)** عرضه المالكُ في المحادثة ≈10-15 ودرسه `T-ANCHOR-AGE` و`T-COLOUR` — بعد تجميد V4 (10-02) فلا يمسّ V4 · يُفصَح.
- الملوَّثُ (ELAB · CIIT · ZCMD · CETX) بـC5: نوافذُ شارتٍ رآها التطوير — لا يُحسب أماميًّا.
