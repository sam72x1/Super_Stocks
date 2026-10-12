# READY classification — specification (research candidate; NOT validated)

Status: frozen on development and checked once on 2026 (`CA_PROTOCOL.md`). **Sealed verdict: NO_DEMONSTRATED_IMPROVEMENT · NOT_GRADED** (HISTORICAL_CLASSIFICATION_RESULTS.md). Not a production rule; nothing here changes the bot.

## Three separate questions, three axes

- **A · Is it a valid pivot?** The population already passes the identity (M1–M3: prior spike, drop band, price). Axis A grades validity with 9 flags (spike ≥ 100%, drop ≥ 50%, near the annual low, no rise in 20 sessions, reverse split ≤ 120 days, not risen > 20% after the split, ÷2 band, split ≥ 3 times, no group candle). Float, borrow, offering and news are UNKNOWN for history (always reported as such).
- **B · How strong is its technical readiness?** Technical flags and candles.
- **C · How close is it to a +70% leg?** Every flag, including invalidation and timing.

Each axis is a ridge logistic regression on binary flags (intercept unpenalised). The penalty λ is chosen by the development test-half AUC (train 2025-05 → 09, test 10 → 12), then the model is refitted on the whole development window. Chosen λ: A 100.0, B 1000.0, C 10000.0. Nothing is mandatory except not being invalidated; a missing auxiliary condition contributes 0, so a pivot with high readiness is not dropped for one absent condition.

## Classes (per session; k = the rows the tool's technical part flags that session)

| class | rule |
|---|---|
| INVALIDATED | chasing (more than 40% above the 25-session low, or more than 30% in 5 sessions), exploded within 5 sessions, or a daily group-candle proxy in the last 10 sessions |
| READY_1 | top k of the valid pivot-days by C |
| READY_2 | the next k |
| READY_3 | the next 2k |
| WATCH | the rest with B at or above the session median |
| NOT_READY | the rest |

**The numerals are score ranks, not grades.** READY_1–3 are bands of the C score inside a session (top k, next k, next 2k). The sealed check found the classes NOT_GRADED, and no fine difference between them holds in 2026 (RECONCILIATION_ADDENDUM.md §4): read them as a review order, not as levels of readiness.

Per-stock row (`data/ready_rows_2026.csv.gz` for READY_1–3 in 2026; the casebook for every case): class, the three axis probabilities, the flags that hold, top contributors (largest positive coefficient × flag), blockers (negative), and confidence = «partial»: daily bars only; float, borrow, offering, groups and operator UNKNOWN.

## Frozen coefficients (largest by absolute value)

**Axis A** (λ 100.0, intercept -3.340385): A11_NO_GROUP_PROXY -0.2058 · A03_ANNUAL_LOW +0.1629 · A07_HALF_BAND -0.1321 · A05_SPLIT120 +0.1288 · A08_SPLIT3 -0.0930 · A06_SPLIT_NORISE +0.0848 · A01_SPIKE100 +0.0554 · A04_NO_RISE20 -0.0329 · A02_DROP50 +0.0000

**Axis B** (λ 1000.0, intercept -3.436206): B01b_RSI33 +0.0751 · B02_RSI27_10 +0.0499 · B01_RSI30 +0.0424 · B03_BELOW3 +0.0402 · B02b_RSI20_27_10 +0.0383 · B10_VOL5_3 +0.0335 · B06_TEST15 +0.0327 · B14_KVO_UP -0.0325 · B04_PEAK_AGE30 -0.0278 · B22_MA20_FLAT -0.0273 · K01_HAMMER_3 +0.0236 · B13_EMA_X5 -0.0231

**Axis C** (λ 10000.0, intercept -3.425415): I02_RSI40 -0.0116 · B01b_RSI33 +0.0114 · B02_RSI27_10 +0.0082 · A03_ANNUAL_LOW +0.0076 · B01_RSI30 +0.0074 · T01_DIP_LOW +0.0067 · A11_NO_GROUP_PROXY -0.0066 · I04_GROUP_PROXY +0.0066 · B02b_RSI20_27_10 +0.0064 · B03_BELOW3 +0.0061 · A05_SPLIT120 +0.0055 · B14_KVO_UP -0.0054

## Comparison set (all at the same per-session burden k)

TC_TECH · CAPIT_TC · DROP_k · VOLAT_k · VOL_k · COUNT_k (number of Faisal's 11 counted conditions) · APPW_k (the app's weighted screen TG_58420: support with failed breaks 12, entry near the support 8, averages 8, daily RSI 23–27 12, MACD improving 10, positive candle at the support 8, selling weakens 7, room above 5; daily proxies) · W_k (= READY_1) · W_k without invalidation · B_k · A_k.

