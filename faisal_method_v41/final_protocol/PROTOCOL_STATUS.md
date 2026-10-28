# 🧊🔒 FAISAL V4 — FINAL PROSPECTIVE VALIDATION — الحالة

> مولَّدٌ من `faisal_method_v41/final_protocol.py` (V4-FINAL-PROTOCOL 1.1 (2026-10-08 · amendment 1)) · العقد `faisal_method_v41/FINAL_PROTOCOL_prereg.md` · **لا يُحرَّر باليد**.

## ① كتلةُ الإخراج (FINAL OUTPUT)

```
V4_FROZEN = YES
V4_COMMIT = 7c8826c25e745668d33facabb2efbc488e997fb7
CORPUS_AUDIT = COMPLETE
VALID_PROSPECTIVE_CASES = 2
EXCLUDED_CASES = 108
MATCHES = 1
MISMATCHES = 1
FALSE_READY = 0
FALSE_WAIT = 1
FALSE_REJECT = 0
FALSE_UNKNOWN = 0
V4_UNKNOWN = 0
FAISAL_UNKNOWN = 0
ALWAYS_WAIT_MATCH = 1
V4_BEATS_BASELINE = NO
READY_CLASS_VALIDATED = NO
METHODOLOGY_CHANGED = NO
LOOKAHEAD = PASS
PROVENANCE = PASS
CURRENT_STATUS = VERY_PRELIMINARY
FINAL_VALIDATION_STATE = INSUFFICIENT_SAMPLE
— — —
SECONDARY_TRACKED = CASE_0001 BRTX MATCH (provenance LOW) · CASE_0002 CDT MATCH (provenance LOW) · CASE_0003 NCT MATCH (provenance LOW) · CASE_0004 CYCU MATCH (provenance LOW) · CASE_0005 ICMB FALSE_UNKNOWN (provenance LOW) · CASE_0008 NCT FALSE_WAIT (provenance LOW) · CASE_0009 BRTX PENDING (provenance LOW) · CASE_0010 FBGL PENDING (provenance LOW) · CASE_0011 GNPX PENDING (provenance LOW) · CASE_0012 BTOC PENDING (provenance LOW) · CASE_0013 CYCU PENDING (provenance LOW) · CASE_0014 NIVF PENDING (provenance LOW) · CASE_0015 BRAI PENDING (provenance LOW)
PENDING_PRIMARY = 0
EXCLUDED_BREAKDOWN = intake_not_new 95 · secondary_provenance 13 · invalid_data_quality 0 · invalidated_lookahead 0
INTAKE_BY_CLASS = NEW_PROSPECTIVE 15 · DUPLICATE 6 · DERIVATIVE 15 · CONTAMINATED 13 · PRE_EXISTING 7 · UNKNOWN 23 · INSUFFICIENT_CONTEXT 31
COLLECTOR = PASS_SIMULATED · PASS
INTEGRITY = PASS
BASELINE_B = NONE (لا خطَّ أساسٍ فنّيًّا مسجَّلًا مسبقًا — §⑭)
STRUCTURAL = V4 الأماميّ ∈ {WAIT · UNKNOWN} (FVO1) ⟵ لا READY ولا REJECT · وكلُّ تطابقٍ لـV4 تطابقٌ لـALWAYS_WAIT
```

## ② الحقبة (EPOCH 1 · V4 FROZEN)

- **V4_COMMIT:** `7c8826c25e745668d33facabb2efbc488e997fb7` · شهادةُ الملفّات عنده: ✅
- **freeze_id:** `5f291a3b301be047d8c9d2a42e17c82cc75b6a37077d4c3cf17bba6c420f392f`
- **V4_CONFIG_HASH:** `bd548f119a55de5c653d747b1eaa499809749df98973ef77f0b3082473af067d` · **V4_RULE_REGISTRY_HASH:** `5a2a86262511ac2143920c2d8cc1e910740f1325ed47f5c199ed07b3910e3531`
- **V4_TOOL_VERSION:** engine `FAISAL-V4 1.0 (2026-10-02)` · freeze `V4.1-FREEZE 1.0 (2026-10-07)` · rules `V4-RULES 1.0 (2026-10-02)` · runner `V41-RUNNER 1.0 (2026-10-07)`
- **DATA_PIPELINE_VERSION:** `e7d44195e6ad26340ce38cdd2143948a37cc2b2eb4c8fe911e387009101118c9` (93 مكوّنًا · numpy==2.4.6 · pandas==3.0.5 · requests==2.34.2 · websocket-client==1.8.0 · yfinance==1.5.2)

## ③ السلامة I1-I12 (PHASE 18)

| الفحص | الحكم | التفصيل |
|---|---|---|
| `I1_V4_FROZEN` | ✅ | [] |
| `I2_FREEZE_ID` | ✅ | 5f291a3b301be047 |
| `I3_CONFIG_HASH` | ✅ | bd548f119a55de5c |
| `I4_RULE_REGISTRY_HASH` | ✅ | 5a2a86262511ac21 |
| `I5_TOOL_VERSION` | ✅ | {'engine': 'FAISAL-V4 1.0 (2026-10-02)', 'rules': 'V4-RULES 1.0 (2026-10-02)', 'runner': 'V41-RUNNER 1.0 (2026-10-07)', 'freeze': 'V4.1-FREEZE 1.0 (2026-10-07)' |
| `I6_DATA_PIPELINE_VERSION` | ✅ | [] |
| `I7_NO_REVISION` | ✅ | rev 1 · revisions 1 |
| `I8_LEDGER` | ✅ | [] |
| `I9_META_PREFIX` | ✅ | البادئة 22264 بايت سليمة (الإلحاقُ بعدها لا يغيّرها) |
| `I10_CASE_IMAGES` | ✅ | [] |
| `I11_RECORD_EPOCH` | ✅ | [] |
| `I12_NO_LOOKAHEAD_DEFECT` | ✅ | [] |

## ④ المقاييس على PRIMARY (PHASE 13-15)

- **N الصالحة:** 2 · القابلة للمقارنة 2 · **الشريط:** VERY_PRELIMINARY
- **READY (أوّلًا):** V4 0 · فيصل 1 · الدقّة — · الاستدعاء 0.0% · FALSE_READY 0 (المعدّل 0.0% · من غير READY 0.0%)
- **WAIT:** الدقّة 50.0% · الاستدعاء 100.0% · **REJECT:** الدقّة — · الاستدعاء —
- **التطابقُ التامّ:** 50.0% مقابل **ALWAYS_WAIT** 50.0% · المتنافرة b 0 / c 0 ⟵ V4_BEATS_BASELINE **NO**
- **READY_CLASS_VALIDATED:** NO (STRUCTURAL (FVO1): V4 الأماميّ ∈ {WAIT · UNKNOWN}) · P1 (TECH_READY مقابل READY فيصل): {'faisal_ready': 1, 'tech_ready_given_ready': 0, 'faisal_wait_reject': 1, 'tech_ready_given_wait_reject': 0, 'newcombe95': [-0.7935, 0.7935], 'met': False}
- **التنوّع:** أطولُ سلسلةٍ بالإعداد نفسِه 1 · LOW_DIVERSITY لا

## ⑤ الحالات

| الحالة | الرمز | التاريخ | العيّنة (المصدريّة) | V4 (فنّيّ) | فيصل (الدليل) | المطابقة | النظرُ المستقبليّ | الحالة |
|---|---|---|---|---|---|---|---|---|
| `CASE_0001` | BRTX | 2026-10-03 | SECONDARY (LOW) | WAIT (BROKEN_NEW_BASE) | WAIT (DIRECT) | MATCH | PASS | COMPLETE |
| `CASE_0002` | CDT | 2026-10-07 | SECONDARY (LOW) | WAIT (BROKEN_NEW_BASE) | WAIT (STRONG_INFERENCE) | MATCH | PASS | COMPLETE |
| `CASE_0003` | NCT | 2026-10-07 | SECONDARY (LOW) | WAIT (BROKEN_NEW_BASE) | WAIT (STRONG_INFERENCE) | MATCH | PASS | COMPLETE |
| `CASE_0004` | CYCU | 2026-10-23 | SECONDARY (LOW) | WAIT (BROKEN_NEW_BASE) | WAIT (STRONG_INFERENCE) | MATCH | PASS | COMPLETE |
| `CASE_0005` | ICMB | 2026-10-24 | SECONDARY (LOW) | UNKNOWN (PRESS_RECLAIM) | WAIT (DIRECT) | FALSE_UNKNOWN | PASS | COMPLETE |
| `CASE_0006` | BKYI | 2026-10-22 | PRIMARY (MEDIUM) | WAIT (RETEST_PENDING) | READY (DIRECT) | FALSE_WAIT | PASS | COMPLETE |
| `CASE_0007` | ANPA | 2026-10-14 | PRIMARY (MEDIUM) | WAIT (BROKEN_NEW_BASE) | WAIT (DIRECT) | MATCH | PASS | COMPLETE |
| `CASE_0008` | NCT | 2026-10-10 | SECONDARY (LOW) | WAIT (BROKEN_NEW_BASE) | READY (DIRECT) | FALSE_WAIT | PASS | COMPLETE |
| `CASE_0009` | BRTX | 2026-10-27 | SECONDARY (LOW) | — (—) | — (—) | — | — | PENDING_V4 |
| `CASE_0010` | FBGL | 2026-10-27 | SECONDARY (LOW) | — (—) | — (—) | — | — | PENDING_V4 |
| `CASE_0011` | GNPX | 2026-10-27 | SECONDARY (LOW) | — (—) | — (—) | — | — | PENDING_V4 |
| `CASE_0012` | BTOC | 2026-10-27 | SECONDARY (LOW) | — (—) | — (—) | — | — | PENDING_V4 |
| `CASE_0013` | CYCU | 2026-10-27 | SECONDARY (LOW) | — (—) | — (—) | — | — | PENDING_V4 |
| `CASE_0014` | NIVF | 2026-10-27 | SECONDARY (LOW) | — (—) | — (—) | — | — | PENDING_V4 |
| `CASE_0015` | BRAI | 2026-10-27 | SECONDARY (LOW) | — (—) | — (—) | — | — | PENDING_V4 |

## ⑥ الاستلامُ بالأصناف السبعة (PHASE 3)

**NEW_PROSPECTIVE** 15 · **DUPLICATE** 6 · **DERIVATIVE** 15 · **CONTAMINATED** 13 · **PRE_EXISTING** 7 · **UNKNOWN** 23 · **INSUFFICIENT_CONTEXT** 31

## ⑦ طابورُ V4.2 من التحقّق الأماميّ (PHASE 9)

- **V4_2_CANDIDATE:** 3 — تُعرض في `docs/V4_2_RESEARCH_QUEUE.md` · **لا تدخل V4**.

