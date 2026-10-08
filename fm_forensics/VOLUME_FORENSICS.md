# VOLUME_FORENSICS — how Faisal uses volume vs how the bot uses it (2026-10-08)

## Faisal's volume vocabulary (all images re-read by eye in this mission)
| Image | Statement (verbatim fragments) | Meaning | Rule class |
|---|---|---|---|
| X_20260918_61_VEEE | «تحليلي لأسهم الارتكاز لا يبنى على السيولة الحالية — نبحث عن السيولة السابقة المتمركزة بالسهم (51000K)» | volume criterion = *prior* concentrated liquidity in the base, not today's volume | DIRECTLY_SUPPORTED |
| TG_57870 | «تجميع 2.10–2.30 كميات فوليوم · تحميل المشاركات بعد سحب السيولة وليس قبل · 90% يحدث فيها سحب سيولة» | accumulation candles inside the base; loading happens after the sweep | DIRECTLY_SUPPORTED |
| TG_2097 | «مسح السيولة = تصفية المراكز … ABC لابد تتحقق» | the sweep is a sequence (A sweep, B reclaim, C continuation), trigger = reclaim | DIRECTLY_SUPPORTED |
| TG_50829 / TG_50576 | «لماذا يهمني شموع الفوليوم» / «يهمك الآن الفوليوم حجم التداول» | volume candles read as evidence of who holds liquidity, at the developing stage | SUPPORTED |
| TG_2086 | «خلق السيولة الوهمية» (MFI) | fake liquidity detection; MFI as a diagnostic | SUPPORTED (indicator only) |
| TG_1870 / IMG_0531 | «الزناد: ضغط المضارب يوم قبل» | the trigger is an operator pressure day | DIRECTLY_SUPPORTED |
| TG_2043 | sweep + RSI 23–27 before the explosion | volume event + oversold | DIRECTLY_SUPPORTED |

**Negative evidence:** no image states a numeric volume threshold (×N average, $ amount, or share count) as a readiness condition. Counter-direction: Faisal rejects "current liquidity" as the basis (X_61_VEEE). Faisal mentions dollar sizes only for operator orders (≥ 1,000-share prints; «51000K» as prior liquidity) — these are trigger/flow observations, not screen gates.

## Bot's volume logic in the READY path
| Code | Role | Evidence class of the number |
|---|---|---|
| M5 `MIN_DOLLAR_VOL` = $14.3K (envelope) | hard identity gate (liquidity floor) | inferred from catalog; Faisal never states it |
| `VOL_SPIKE_MULT` = 5 (hand activity / flags) | display/warning | engineering |
| `liquidity_sweep` flag → `sweep_confirmed` entry mode | the only trigger-like input to READY NOW | faisal_adopted (sweep concept), threshold engineering |
| `rotation_pct` (volume/float) | display only | third-party (ELAB example) |
| `R1 ∪ T-C` live trigger (3× volume, $30k/3 min, +5%) | live alerts, silent since Polygon ended | engineering, measured +6.2 msgs/day |
| Ignition radar ($100k operator candle) | frozen since 2026-09-30 | faisal_verbatim thresholds for *candle class*, not readiness |

## Divergence
1. Faisal: volume = **where the prior liquidity sits in the base** (a structural, backward-looking read) + **a pressure event** (forward trigger). Bot: volume = a floor (M5) and a spike warning; prior-liquidity concentration is not computed anywhere in the READY path (the pressure radar's `press_*` tools measure a different thing — a channel, not base accumulation).
2. The only element of the trigger the bot can see on daily bars is the sweep flag; it fires `sweep_confirmed` on the day of the sweep's reclaim (consistent with TG_2097 B-leg), but it is not required for READY (`near_support` alone suffices).
3. UNKNOWN / not measurable here: whether "prior concentrated liquidity" (e.g. volume-at-price in the base) separates Faisal's focus names from the rest of the inside bucket — needs bars (probe pending) and a pre-registered test; it is a candidate for the V4.2 research queue, not a production rule.

## Recommendation (no production change)
Do not add a volume threshold to READY NOW; the corpus contradicts a current-volume gate. The measurable hypothesis is "base volume concentration" as a FOCUS feature — shadow-only.
