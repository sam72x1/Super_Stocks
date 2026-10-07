# RULE_TRACEABILITY — صورة ⟵ معلومة ⟵ قاعدة ⟵ تنفيذ · وبالعكس (§3 · §5)

> 🧾 مولَّدٌ من `faisal_method_v41/corpus_audit/corpus_audit.py` (‏`EX_PROTOCOL.md` §⑪) — **لا رقمَ باليد** · لقطةُ التدقيق 2026-10-07 · V4 مجمَّدٌ لم يُمَسّ.

## ① الاتّجاهُ الأوّل — كلُّ عبارةٍ قاعديّة لها صنفُ تتبّعٍ واحد ومؤشّرٌ يُفحص
- العبارات: **942** (‏V4 871 · B48 69 · أعضاءُ العناقيد 2)
| الصنف | العدد |
|---|---|
| T-V4 | 330 |
| T-V31 | 318 |
| T-PROD | 64 |
| T-CLOSED | 46 |
| T-QUEUE | 20 |
| T-CASE | 108 |
| T-NONGEN | 53 |
| T-NONE | 3 |

**أساسُ التتبّع:** B48 69 · MEMBER 2 · auto:case-sid 104 · auto:similarity+review 139 · review:manual 390 · review:override 14 · review:untraced 224

**صفوفُ V3.1 المشار إليها بحالة تنفيذها:** DOCUMENTED_ONLY 169 · NOT_IMPLEMENTED 64 · PRODUCTION 88 · TOOL_V31 39 · TOOL_V31_ADVISORY 1

## ② الاتّجاهُ العكسيّ — قاعدة ⟵ مصدر ⟵ دليل ⟵ تحقّق (قواعدُ V4 الـ21)
| القاعدة | فاعلة | صورُ السجلّ | داعمٌ (وحدات) | مستقلّ | READY/WAIT/REJECT من العبارات | تعارضٌ قائم/جديد | حالةُ الدليل (V4.1) | التحقّق |
|---|---|---|---|---|---|---|---|---|
| `R4-DATA-01` | True | 0 | 0 | 0 | 0/0/0 | 0/0 | UNKNOWN | الأماميّ INSUFFICIENT (N=1) |
| `R4-BOT-01` | True | 5 | 8 | 8 | 0/0/0 | 0/0 | CONFIRMED | الأماميّ INSUFFICIENT (N=1) |
| `R4-HOLD-01` | True | 5 | 17 | 17 | 1/2/2 | 2/0 | SUPPORTED | الأماميّ INSUFFICIENT (N=1) |
| `R4-CYC-01` | True | 13 | 33 | 31 | 0/0/1 | 3/2 | SUPPORTED | الأماميّ INSUFFICIENT (N=1) |
| `R4-ZONE-01` | True | 5 | 8 | 8 | 1/0/0 | 1/0 | SUPPORTED | الأماميّ INSUFFICIENT (N=1) |
| `R4-HOLDZ-01` | True | 4 | 13 | 13 | 3/0/0 | 3/0 | SUPPORTED | الأماميّ INSUFFICIENT (N=1) |
| `R4-SWEEP-01` | True | 7 | 28 | 27 | 0/1/0 | 1/6 | SUPPORTED | الأماميّ INSUFFICIENT (N=1) |
| `R4-INV-01` | True | 5 | 23 | 22 | 0/0/1 | 2/2 | CONFIRMED | الأماميّ INSUFFICIENT (N=1) |
| `R4-LOC-01` | True | 4 | 9 | 9 | 0/3/1 | 0/0 | CONFIRMED | الأماميّ INSUFFICIENT (N=1) |
| `R4-OP-01` | True | 6 | 27 | 25 | 2/4/0 | 1/0 | SUPPORTED | الأماميّ INSUFFICIENT (N=1) |
| `R4-VAL-GRP-01` | True | 6 | 33 | 31 | 0/1/3 | 1/2 | CONFIRMED | الأماميّ INSUFFICIENT (N=1) |
| `R4-VAL-OFF-01` | True | 4 | 9 | 9 | 0/0/3 | 0/1 | CONFIRMED | الأماميّ INSUFFICIENT (N=1) |
| `R4-VAL-SHORT-01` | True | 3 | 29 | 28 | 1/0/4 | 2/3 | SUPPORTED | الأماميّ INSUFFICIENT (N=1) |
| `R4-ENT-01` | True | 6 | 24 | 23 | 2/0/0 | 4/0 | SUPPORTED | الأماميّ INSUFFICIENT (N=1) |
| `R4-ENT-02` | True | 5 | 13 | 13 | 0/1/1 | 1/0 | SUPPORTED | الأماميّ INSUFFICIENT (N=1) |
| `R4-STOP-01` | True | 5 | 12 | 12 | 2/0/0 | 3/0 | SUPPORTED | الأماميّ INSUFFICIENT (N=1) |
| `R4-TGT-01` | True | 5 | 46 | 44 | 0/1/0 | 1/0 | SUPPORTED | الأماميّ INSUFFICIENT (N=1) |
| `R4-TF-01` | True | 4 | 13 | 12 | 0/0/0 | 0/0 | SUPPORTED | الأماميّ INSUFFICIENT (N=1) |
| `R-W-SPAN` | False | 3 | 3 | 3 | 0/0/0 | 0/0 | PROBABLE | الأماميّ INSUFFICIENT (N=1) |
| `R-SUP-MAIN` | False | 0 | 0 | 0 | 0/0/0 | 0/0 | UNKNOWN | الأماميّ INSUFFICIENT (N=1) |
| `H-D2` | False | 0 | 0 | 0 | 0/0/0 | 0/0 | UNKNOWN | الأماميّ INSUFFICIENT (N=1) |

**بلا أيّ صورة (استنتاجٌ أو هندسة):** `H-D2` · `R-SUP-MAIN` · `R4-DATA-01`

## ③ استخلاصُ المنهج (§5) — ما تغطّيه العباراتُ بالأكثر
`R4-TGT-01` 46 · `R4-CYC-01` 33 · `R4-VAL-GRP-01` 33 · `R4-VAL-SHORT-01` 29 · `R4-SWEEP-01` 28 · `R4-OP-01` 27 · `R4-ENT-01` 24 · `R4-INV-01` 23 · `R4-HOLD-01` 17 · `R4-HOLDZ-01` 13
