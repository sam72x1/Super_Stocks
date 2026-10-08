# RSI_READY_FORENSICS — does the corpus support "RSI above 40" as a readiness rule? (2026-10-08)

## Corpus evidence (71 images mention RSI by OCR; 62 with a number; eye-read set below)
| Image | Statement | Direction | Class |
|---|---|---|---|
| TG_2043 | «ضغط الارتكاز لابد قبل ينفجر يكون RSI بين 23–27 … لايمكن ومستحيل يصعد اذا RSI بمناطق 40» | low RSI required; RSI ≈ 40 = NOT ready | DIRECTLY_SUPPORTED |
| TG_1870 / IMG_0531 | «جاهز للانفجار» = oversold 22–27 + yearly bottom + oscillation 10–20% | low RSI = readiness component | DIRECTLY_SUPPORTED |
| DRCT card («rsi اقل من 30») | entry condition | low RSI | DIRECTLY_SUPPORTED |
| X_20260918_61_VEEE | «Rsi < 41.95» listed among the chart notes of a WAIT case | RSI ~42 noted, stock explicitly «للانتظار وليس للدخول» | SUPPORTS "40 = wait", not "40 = ready" |
| TG_58386 (owner chart, DKI post-collapse) | RSI 42.0 on the 4h | no Faisal statement | NONE |
| Owner's three conditions (2026-09-26) | RSI < 33 (Faisal's bot threshold by name) | low RSI | OWNER rule |
| CRE case | RSI 43–55 throughout Faisal's focus; WAIT on gap | focus does not require low RSI | counter to "RSI required for FOCUS" |
| SXTC 09-10 (entry) | RSI 23.3 (bot near_watch) | low RSI at trigger | consistent |
| DKI 09-2x WAIT | RSI 22–35 | low RSI while waiting for the sweep | consistent |

**Count:** images stating low RSI (≤ ~30) as a readiness/entry component: 4 direct + owner rule. Images stating "RSI above 40 = ready": **0**. Images stating RSI ~40 = not ready / wait: 2 (TG_2043 explicit, X_61 contextual).

## Verdict
- "RSI above 40 as a readiness rule": **CONTRADICTED** by TG_2043 and unsupported elsewhere. It must NOT become a production rule.
- "RSI ≤ ~33 as a readiness component": DIRECTLY_SUPPORTED; already live (`RSI_OVERSOLD` 33 soft fail, `FAISAL_RSI_ENTRY_MAX` 30 near-watch bucket, three-conditions RSI < 33).
- Nuance (STRONGLY_SUPPORTED): RSI low is a *readiness* condition, not a *focus* condition (CRE in focus at RSI 45–55), and not a *trigger* (the trigger is pressure). Historical tests already measured RSI-based entry *ordering* (T-WAIT-23W, T-RSI40, T-RSI-RANK) and found no tradable edge — those axes are CLOSED and are not reopened here.
