# 12 — تدقيقُ القواعد V4 (§7 · §11 · §24 · §27 · §29)

## ① المكوّنات كلّها (PROVE أو UNKNOWN)
حرفيٌّ في وحدتين فأكثر من الطبقة 1 ⟵ PROVEN_IN_TEXT · وحدة ⟵ SINGLE_SOURCE · وصفُ المراجع وحدَه ⟵ OBSERVED_ONLY · صفر ⟵ UNKNOWN

| المكوّن | الحالة | حرفيّ 1 | حرفيّ 2 | حرفيّ 2b | حرفيّ X | وصفٌ 1 | أمثلة الطبقة 1 | ملاحظة |
|---|---|---|---|---|---|---|---|---|
| BOS_CHOCH | UNKNOWN | 0 | 0 | 0 | 0 | 0 | — |  |
| BREAKOUT | PROVEN_IN_TEXT | 43 | 18 | 11 | 1 | 2 | IMG_0143 · IMG_0153 · IMG_0302 · IMG_0316 |  |
| CCI | OBSERVED_ONLY | 0 | 0 | 0 | 0 | 39 | — |  |
| CHANNEL | UNKNOWN | 0 | 0 | 0 | 0 | 0 | — |  |
| CONSOLIDATION | PROVEN_IN_TEXT | 51 | 14 | 12 | 11 | 3 | IMG_0150 · IMG_0302 · IMG_0319 · IMG_0361 |  |
| ELLIOTT | PROVEN_IN_TEXT | 24 | 2 | 2 | 5 | 0 | IMG_0393 · TG_1845 · TG_1849 · TG_1860 |  |
| FALLING_CANDLE | PROVEN_IN_TEXT | 16 | 6 | 5 | 1 | 2 | IMG_0143 · IMG_0153 · IMG_0302 · IMG_0509 |  |
| FALSE_BREAKOUT | PROVEN_IN_TEXT | 4 | 0 | 0 | 0 | 0 | TG_1840 · TG_1854 · TG_57862 · X_20260827_labt_supports_wait |  |
| FIBONACCI | PROVEN_IN_TEXT | 4 | 0 | 0 | 1 | 1 | TG_2085 · TG_57928 · X_20260918_54_indicators · X_20260918_61_VEEE |  |
| FLAG | UNKNOWN | 0 | 0 | 0 | 0 | 0 | — |  |
| FSTO | SINGLE_SOURCE | 1 | 0 | 0 | 0 | 43 | TG_1812 |  |
| GAP | PROVEN_IN_TEXT | 6 | 7 | 0 | 0 | 4 | IMG_0486 · IMG_0512 · IMG_0513 · TG_20260905_06 |  |
| GROUPS | PROVEN_IN_TEXT | 24 | 12 | 6 | 2 | 3 | IMG_0143 · IMG_0151 · IMG_0153 · IMG_0177 |  |
| HAMMER | PROVEN_IN_TEXT | 3 | 4 | 2 | 0 | 1 | IMG_0569 · IMG_0691 · TG_1824 |  |
| HEAD_SHOULDERS | PROVEN_IN_TEXT | 2 | 2 | 0 | 0 | 0 | TG_2197 · TG_50589 | محورٌ مُغلَق (HSFX_REOPEN · T-HS-FX/RX) — أمثلةُ فيصل قممٌ يُخرَج عندها |
| INVERSE_HEAD_SHOULDERS | OBSERVED_ONLY | 0 | 2 | 0 | 0 | 1 | — | محورٌ مُغلَق (HSFX_REOPEN) |
| KLINGER | PROVEN_IN_TEXT | 5 | 1 | 0 | 0 | 0 | TG_2085 · TG_2090 · TG_2218 · TG_57928 |  |
| KST | OBSERVED_ONLY | 0 | 0 | 0 | 0 | 6 | — |  |
| MACD | PROVEN_IN_TEXT | 4 | 3 | 0 | 0 | 21 | TG_1814 · TG_2085 · TG_57928 · X_20260918_54_indicators |  |
| MOVING_AVERAGE | PROVEN_IN_TEXT | 39 | 8 | 8 | 8 | 7 | IMG_0143 · IMG_0150 · IMG_0151 · IMG_0152 |  |
| M_DOUBLE_TOP | PROVEN_IN_TEXT | 2 | 1 | 0 | 0 | 0 | TG_58044 · TG_58050 |  |
| OFFERING | PROVEN_IN_TEXT | 13 | 2 | 0 | 1 | 0 | IMG_0497 · IMG_0587 · IMG_8127 · IMG_8136 |  |
| PENNANT | UNKNOWN | 0 | 0 | 0 | 0 | 0 | — |  |
| PRESS | PROVEN_IN_TEXT | 29 | 7 | 4 | 1 | 2 | IMG_0177 · IMG_0179 · IMG_0316 · IMG_0531 |  |
| RETEST | PROVEN_IN_TEXT | 15 | 3 | 5 | 4 | 1 | IMG_0486 · IMG_0508 · IMG_0566 · IMG_8133 |  |
| RSI | PROVEN_IN_TEXT | 19 | 7 | 3 | 0 | 4 | IMG_0177 · IMG_0531 · TG_1810 · TG_1812 |  |
| SHORT_BORROW | PROVEN_IN_TEXT | 60 | 23 | 8 | 17 | 2 | IMG_0143 · IMG_0150 · IMG_0151 · IMG_0152 |  |
| SPLIT | PROVEN_IN_TEXT | 29 | 14 | 3 | 13 | 7 | IMG_0143 · IMG_0150 · IMG_0151 · IMG_0152 |  |
| STRUCTURE_HH_HL_LH_LL | SINGLE_SOURCE | 1 | 0 | 0 | 0 | 0 | IMG_8127 |  |
| SUPPORT_RESISTANCE | PROVEN_IN_TEXT | 97 | 46 | 28 | 23 | 3 | IMG_0179 · IMG_0302 · IMG_0319 · IMG_0361 |  |
| SWEEP | PROVEN_IN_TEXT | 25 | 10 | 6 | 2 | 1 | IMG_0143 · IMG_0153 · IMG_0177 · IMG_0179 |  |
| TRIANGLE | UNKNOWN | 0 | 0 | 0 | 0 | 0 | — |  |
| VOLUME | PROVEN_IN_TEXT | 6 | 0 | 0 | 1 | 1 | TG_50576 · TG_50577 · TG_50829 · TG_57870 |  |
| VWAP | PROVEN_IN_TEXT | 2 | 0 | 1 | 1 | 9 | IMG_0617 · IMG_0688 |  |
| WYCKOFF | PROVEN_IN_TEXT | 4 | 0 | 2 | 2 | 0 | TG_1980 · TG_50581 · TG_50584 · TG_50831 |  |
| W_DOUBLE_BOTTOM | PROVEN_IN_TEXT | 6 | 2 | 2 | 0 | 0 | TG_50589 · TG_58044 · TG_58046 · TG_58048 |  |

## ② سجلُّ القواعد (§27)
الحقولُ في `rules_v4.py`: rule_id · description · source · author · source_level · image_ids · supporting · contradicting · status · decisionality · active · backtest_derived · current_version · change_history

| RULE_ID | الوصف | المصدر | الكاتب | المستوى | الصور | مؤيِّد | مناقِض | الحالة | القراريّة | IMPLEMENTED | TESTED | MUTATION_LOCK | BACKTEST_DERIVED | النسخة | التاريخ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R4-DATA-01 | جودةُ البيانات: 40 جلسةً يوميّةً فأكثر حتى تاريخ القراءة · بلا قيمٍ ناقصة · والقراءةُ لا ت | engineering (§26 · §35) | — | 7 |  | 0 | 0 | CONFIRMED | DECISIONAL | ✅ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | أُنشئت في V4 (2026-10-02) |
| R4-BOT-01 | القاعُ = أدنى ذيلٍ منذ قمّة الدورة (نافذة 120 جلسة) · وكسرُه بأبعد من مدى السحب يعيد التحل | faisal | F | 2 | TG_50584 · X_20260827_checklist_7points · X_20260905_10 · X_20260905_07 … | 5 | 1 | SUPPORTED | DECISIONAL | ✅ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | أُنشئت في V4 (2026-10-02) |
| R4-HOLD-01 | القاعُ لا يُكسر 5 جلساتٍ فأكثر قبل أيّ حكمٍ بالإيجابيّة | faisal | F | 3 | X_20260918_85_YMT · X_20260827_checklist_7points · TG_20260905_09 · TG_2066 … | 5 | 2 | SUPPORTED | DECISIONAL | ✅ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | أُنشئت في V4 (2026-10-02) |
| R4-CYC-01 | الدورة: قاع ⟵ صعودُ اختبارٍ (15% فأكثر · غالبًا 20%) ⟵ رجوعٌ يختبر الدعم ⟵ الحكمُ عند الاخ | faisal | F | 3 | X_20260918_85_YMT · TG_50584 · X_20260918_13_NUWE · TG_50585 … | 12 | 3 | CONFIRMED | DECISIONAL | ✅ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | أُنشئت في V4 (2026-10-02) |
| R4-ZONE-01 | منطقةُ الدخول/الاختبار: من القاع حتى 15% فوقه · والطلباتُ 5-15% فوق القاع | faisal | F | 1 | IMG_0531 · IMG_0569 · X_20260827_checklist_7points · TG_50585 … | 5 | 1 | SUPPORTED | DECISIONAL | ✅ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | أُنشئت في V4 (2026-10-02) |
| R4-HOLDZ-01 | ثباتٌ داخل المنطقة بعد الاختبار (2-5 جلسات · الأساسيّ 3) = جاهزيّةٌ فنيّة | faisal | F | 2 | TG_2108 · TG_20260905_09 · IMG_0566 · IMG_0697 | 4 | 3 | PROBABLE | DECISIONAL | ✅ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | أُنشئت في V4 (2026-10-02) |
| R4-SWEEP-01 | سحبُ سيولةٍ تحت القاع السابق (حتى 13% · مدى الطبقة 1: 5-15%) ثمّ عودةٌ فوقه = ضغطُ المضارب | faisal + EDU | F (المدى) · EDU (7-13 حرفيًّا) | 2 | TG_50584 · IMG_0177 · TG_57874 · TG_57870 … | 7 | 2 | SUPPORTED | DECISIONAL | ✅ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | أُنشئت في V4 (2026-10-02) |
| R4-INV-01 | كسرُ القاع بأبعد من مدى السحب يُفشل التحليل الحاليّ ⟵ انتظارُ قاعٍ جديد | faisal | F | 2 | IMG_0512 · IMG_0513 · IMG_0569 · X_20260905_10 … | 4 | 1 | SUPPORTED | DECISIONAL | ✅ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | أُنشئت في V4 (2026-10-02) |
| R4-LOC-01 | السعرُ فوق المنطقة بعد الصعود («الوسط غير الآمن») ⟵ لا دخول · انتظارُ الاختبار | faisal | F | 2 | X_20260918_12_doublebottom · TG_2097 · TG_50580 · X_20260827_target10_entry_below | 4 | 1 | CONFIRMED | DECISIONAL | ✅ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | أُنشئت في V4 (2026-10-02) |
| R4-OP-01 | بصمةُ المضارب (الضغط) هي التأكيدُ الافتراضيّ قبل READY · والجاهزيّةُ الفنيّة بلا بصمةٍ ⟵ ا | faisal | F | 2 | TG_1822 · TG_2218 · X_20260827_amix_hcwb_ready · X_20260905_01 … | 6 | 2 | SUPPORTED | UNKNOWN | ✅ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | أُنشئت في V4 (2026-10-02) |
| R4-VAL-GRP-01 | دخولُ القروبات يُبطل قراءةَ الشموع ⟵ رفض | faisal | F | 2 | IMG_0488 · TG_1835 · X_20260827_checklist_7points · TG_2090 … | 6 | 1 | SUPPORTED | DECISIONAL | ✅ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | أُنشئت في V4 (2026-10-02) |
| R4-VAL-OFF-01 | طرحٌ أو تخفيفٌ معلَّق ⟵ انتظار | faisal | F | 2 | X_20260827_kwm_offering_notready · TG_50828 · TG_2064 · X_20260918_85_YMT | 4 | 0 | SUPPORTED | DECISIONAL | ✅ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | أُنشئت في V4 (2026-10-02) |
| R4-VAL-SHORT-01 | المتاحُ للشورت فوق 20 ألفًا ⟵ انتظار | faisal | F | 2 | IMG_0150 · TG_50578 · X_20260827_rubi_read_short150k | 3 | 2 | PROBABLE | DECISIONAL | ✅ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | أُنشئت في V4 (2026-10-02) |
| R4-ENT-01 | الدخولُ الأوّل: طلباتٌ عند الدعم بدفعاتٍ (فوارق 5 سنتات) — آليّةُ دخولٍ مفضّلة لا شرطُ قرا | faisal | F | 2 | IMG_0569 · X_20260918_85_YMT · X_20260827_checklist_7points · IMG_0510 … | 4 | 4 | CONFIRMED | SUPPORTING | ✅ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | أُنشئت في V4 (2026-10-02) |
| R4-ENT-02 | الدخولُ الثاني: بعد التحرّر/الاختراق مع التأكيد (ثباتٌ فوقه · إقفالٌ يوميٌّ ثانٍ) | faisal | F | 2 | TG_2197 · X_20260827_checklist_7points_cont · TG_57862 · IMG_0602 … | 4 | 1 | SUPPORTED | INFORMATIONAL | ✅ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | أُنشئت في V4 (2026-10-02) |
| R4-STOP-01 | الوقف: القاعُ نفسُه (الأساسيّ) · وبدائلُ موسومة: ‏−5% · ‏−7% تحت الدعم · 7% من الدخول | faisal | F | 2 | X_20260827_checklist_7points · TG_2106 · TG_1978 · TG_2098 … | 3 | 3 | SUPPORTED | SUPPORTING | ✅ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | أُنشئت في V4 (2026-10-02) |
| R4-TGT-01 | الأهداف: سلّمُ المقاومات (الأسود) · رأسُ/ذيلُ الشمعة الساقطة · الفجوات · و«100٪ هدف» = مسا | faisal | F | 2 | X_20260827_amix_hcwb_ready · IMG_0508 · TG_2097 · IMG_0587 … | 3 | 1 | CONFIRMED | INFORMATIONAL | ✅ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | أُنشئت في V4 (2026-10-02) |
| R4-TF-01 | الفريمات: يوميّ ‏+ 4 ساعات · و30/5 دقائق للّحظيّ · والمستوياتُ تختلف بالفريم — المحرّكُ يو | faisal | F | 2 | X_20260905_10 · IMG_0361 · TG_58048 · TG_2031 | 3 | 0 | SUPPORTED | INFORMATIONAL | ✅ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | أُنشئت في V4 (2026-10-02) |
| R-W-SPAN | (V3.1) لا قاعَ بين قاعَي W أدنى منهما بأكثر من 2% | inferred (V3.1) | طرفٌ ثالث + رسمُ فيصل | 4 | IMG_0627 · TG_58042 · TG_58043 | 0 | 0 | SUPPORTED | UNKNOWN | ❌ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | V3.1 ⟵ V4: في V4: مُدمَجةٌ في R4-BOT-01 (القاعُ = الأدنى) — لا تُستعمل منفصلة |
| R-SUP-MAIN | (V3.1 · معلومة) أدنى ذيلٍ منذ قمّة الدورة | engineering (V3.1) | — | 6 |  | 0 | 1 | SUPPORTED | DECISIONAL | ❌ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | V3.1 ⟵ V4: في V4: هو تعريفُ القاع (R4-BOT-01) · والدعمُ فوقه يُقرأ بالجسم والدعم الثاني والمنطقة |
| H-D2 | (V3.1 · مرفوضة) جلسةٌ ممتدّة لـW على 30 دقيقة | faisal_adopted | — | 5 |  | 0 | 1 | CONTRADICTED | UNKNOWN | ❌ | ✅ (V4L6/V4L7) | V4L1-V4L10 | False | V4-RULES 1.0 (2026-10-02) | V3.1 ⟵ V4: لا أثر |

## ③ RAYA و R-W-SPAN (§12)
| البند | النتيجة |
|---|---|
| contradiction_search | بحثٌ في 609 وحدة عن W مقبولٍ رغم قاعٍ داخليٍّ أدنى: صفرُ مثالٍ لفيصل · وRAYA (ذهبيّ) يوافق (دعمُه 1.999 = القاعُ الداخليّ) |
| decision | SUBSUMED — يُعمَّم في R4-BOT-01 (القاع = أدنى ذيلٍ منذ قمّة الدورة) ولا يُستعمل قاعدةً مستقلّة في V4 · وV3.1 محفوظٌ كما هو |
| question | هل R-W-SPAN قاعدةٌ عامّةٌ لفيصل؟ |
| status | SUPPORTED (المعنى العامّ) · والصيغةُ الهندسيّة الخاصّة بـW (2% بين القاعين) POSSIBLE |
| v31_basis | تعريفُ طرفٍ ثالث (TG_58042/43/50/51) يطابقه رسمُ فيصل IMG_0627 · وصفرُ مثالٍ يناقضه |
| v4_finding | المعنى العامّ «القاعُ الحقيقيُّ هو الأدنى · وكسرُه يعيد التحليل» مسنودٌ مستقلًّا (R4-BOT-01 · R4-INV-01): TG_50584 «أدنى شمعة القاع» · X_20260905_10 «كسر 1.81 تصنع تحليل اخر» · X_20260905_07 «إن كسر 2.08 يذهب إلى 1.70» · IMG_0689 |

## ④ جدارُ الصورة الواحدة (§29): لا قاعدةَ نشطة بصورةٍ واحدة
## ⑤ جدارُ الباكتيست (§24): كلُّ قاعدةٍ `backtest_derived = False` (قفل V4L7) · ولا عتبةَ ضُبطت بعائد.
