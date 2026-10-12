# Candle pattern study

**What is new here and what is not.** T-CANDLE (2026-08-27, archive line 7108) measured six reversal candles as trade selectors in the pressure channel (R expectancy) and failed 0/6; that axis stays closed and its verdict is unchanged. This study asks a different question on a different population: does a candle on a pivot-day mark a +70% leg starting 7–10 sessions later? It is descriptive and does not reopen T-CANDLE. The 4-hour frame, which Faisal uses for most candle readings (IMG_0569, TG_1865), is not archived, so every candle here is daily.

## 1. Definitions (no incomplete or future candle: the candle at T is the completed daily bar of T)

| flag | definition | source |
|---|---|---|
| K01_HAMMER | the bot's «مطرقة»: body ≤ 0.4 range, lower wick ≥ 2 body, upper wick ≤ max(0.5 body, 0.1 range) | IMG_0569, IMG_0691 · F |
| K01_HAMMER_3 | a hammer on any of the last 3 sessions | IMG_0569, IMG_0691 · F |
| K02_RED_HAMMER | hammer with close < open («شمعة حمرا = صعود قصير الامد», IMG_0569) | IMG_0569 · F |
| K03_INV_HAMMER | the bot's «مطرقة مقلوبة»: body ≤ 0.4 range, upper wick ≥ 2 body, small lower wick | TG_2001, TG_2032 · F |
| K03_INV_HAMMER_3 | an inverted hammer on any of the last 3 sessions | TG_2001, TG_2032 · F |
| K04_DOJI | body ≤ 0.10 × range (DOJI_BODY_MAX) | TG_58383, TG_58382 · T |
| K04b_DOJI_SUPPORT | the bot's «دوجي عند الدعم»: doji with the low within 3% of the 30-session low | TG_58383, TG_58382 · T |
| K05_ENGULF | the bot's «ابتلاع صاعد»: red then green, open ≤ previous close, close ≥ previous open, larger body | TG_1973, TG_1929 · A |
| K05_ENGULF_3 | a bullish engulfing on any of the last 3 sessions | TG_1973, TG_1929 · A |
| K06_MSTAR | the bot's «نجمة الصباح»: big red (body ≥ 0.4 range), small body (≤ 0.5 of the first) not above its close, green closing above the first body's midpoint | TG_58382 · T |
| K06b_DOJI_THEN_ENGULF | doji (T−1 or T−2) or morning star (T−1), then a bullish engulfing (TG_58382, third party) | TG_58382 · T |
| K07_HARAMI | previous red with body ≥ 0.4 range; today green inside the previous body, body ≤ 0.6 previous | IMG_0448 (text record) · F |
| K08_WICK_BOUNCE | long lower wick (≥ 0.5 range and ≥ 2 body) at the 25-session low in the last 3 sessions, close ≥ 1.05 × that low (TG_57874) | TG_57874, TG_50581 · F |
| K08b_LONGWICK | long lower wick today (≥ 0.5 range and ≥ 2 body) | TG_57874, TG_50581 · F |
| K09_HANGMAN | hammer shape with the close within 3% of the 20-session high (the bot's _hanging_man) | TG_2108 · F |
| K10_SHOOT | inverted-hammer shape with the close within 3% of the 20-session high | TG_2032 · T |
| K11_INSIDE | high ≤ previous high and low ≥ previous low | Super_stock._patterns_at · P |
| K11_SPIN | body ≤ 0.3 range, both wicks ≥ body, not a doji | Super_stock._patterns_at · P |
| K11_PIERCING | the bot's «اختراق صاعد»: red then green opening below the red close, closing above its midpoint | Super_stock._patterns_at · P |
| K11_MARUBOZU | the bot's «ماروبوزو أخضر»: green body ≥ 0.9 range, range ≥ 2% of the close | Super_stock._patterns_at · P |
| K11_SOLDIERS | the bot's «ثلاثة جنود بيض» | Super_stock._patterns_at · P |
| B20_CANDLE_AT_SUPPORT | any of hammer, inverted hammer, doji at support, engulfing, piercing, morning star, long lower wick in the last 3 sessions ∧ within 15% of the 25-session low | TG_58420, IMG_0569 · A |

## 2. Development (2025-05-01 → 12-31; base 3.12%, 540 events)

| flag | flags / session | prevalence POS · NEG | lift [95%] | Bonferroni | matched [95%] | events captured (exclusion cost) | − DROP_k pp | − VOLAT_k pp | halves lift | at support · oversold |
|---|---|---|---|---|---|---|---|---|---|---|
| K01_HAMMER | 16.75 | 0.0466 · 0.0408 | 1.136 [0.935, 1.357] | [0.826, 1.504] | 1.229 [0.839, 1.829] | 86/540 (454) | -1.93 [-3.45, -0.45] | -1.48 [-3.05, 0.03] | 1.066 · 1.195 | 1.165 · 0.861 |
| K01_HAMMER_3 | 47.79 | 0.1294 · 0.1163 | 1.109 [0.933, 1.292] | [0.83, 1.453] | 1.014 [0.747, 1.362] | 126/540 (414) | -1.10 [-2.0, -0.24] | -1.25 [-2.23, -0.29] | 1.12 · 1.048 | 1.109 · 1.049 |
| K02_RED_HAMMER | 9.91 | 0.0279 · 0.0243 | 1.143 [0.883, 1.424] | [0.782, 1.588] | 1.333 [0.794, 2.264] | 56/540 (484) | -2.93 [-5.08, -0.77] | -1.24 [-3.37, 0.67] | 1.137 · 1.106 | 1.265 · 0.898 |
| K03_INV_HAMMER | 24.89 | 0.0598 · 0.0603 | 0.992 [0.819, 1.159] | [0.712, 1.284] | 1.048 [0.74, 1.464] | 105/540 (435) | -2.31 [-3.59, -1.08] | -1.92 [-3.28, -0.62] | 0.912 · 1.098 | 0.988 · 0.736 |
| K03_INV_HAMMER_3 | 68.06 | 0.1632 · 0.1647 | 0.992 [0.852, 1.129] | [0.768, 1.215] | 0.884 [0.672, 1.145] | 145/540 (395) | -1.13 [-1.85, -0.41] | -1.26 [-2.04, -0.45] | 0.928 · 1.077 | 1.0 · 0.736 |
| K04_DOJI | 46.43 | 0.1123 · 0.1133 | 0.991 [0.873, 1.115] | [0.752, 1.203] | 0.993 [0.767, 1.272] | 187/540 (353) | -1.52 [-2.3, -0.76] | -1.52 [-2.38, -0.69] | 0.958 · 1.014 | 1.01 · 1.096 |
| K04b_DOJI_SUPPORT | 9.64 | 0.024 · 0.0249 | 0.965 [0.711, 1.243] | [0.535, 1.415] | 0.833 [0.51, 1.334] | 41/540 (499) | -3.61 [-5.71, -1.59] | -2.17 [-4.23, -0.32] | 1.13 · 0.881 | 0.951 · 0.859 |
| K05_ENGULF | 18.28 | 0.0402 · 0.0432 | 0.932 [0.753, 1.119] | [0.685, 1.227] | 1.064 [0.727, 1.532] | 78/540 (462) | -2.23 [-3.62, -0.88] | -1.99 [-3.46, -0.64] | 1.076 · 0.728 | 0.906 · 0.567 |
| K05_ENGULF_3 | 54.21 | 0.125 · 0.129 | 0.97 [0.82, 1.133] | [0.702, 1.263] | 0.939 [0.706, 1.252] | 121/540 (419) | -1.40 [-2.24, -0.56] | -1.47 [-2.35, -0.63] | 1.163 · 0.699 | 0.888 · 0.592 |
| K06_MSTAR | 4.46 | 0.0078 · 0.0105 | 0.754 [0.422, 1.127] | [0.226, 1.434] | 0.818 [0.278, 2.167] | 15/540 (525) | -5.34 [-8.76, -2.25] | -3.15 [-6.44, -0.29] | 0.663 · 0.862 | 0.748 · 0.756 |
| K06b_DOJI_THEN_ENGULF | 4.61 | 0.0088 · 0.0111 | 0.8 [0.474, 1.204] | [0.3, 1.536] | 0.846 [0.333, 2.0] | 18/540 (522) | -5.72 [-9.03, -2.34] | -1.62 [-4.53, 1.03] | 0.883 · 0.644 | 0.43 · 0.229 |
| K07_HARAMI | 14.34 | 0.027 · 0.0356 | 0.764 [0.572, 0.964] | [0.484, 1.087] | 0.638 [0.394, 1.0] | 54/540 (486) | -3.35 [-4.91, -1.78] | -2.68 [-4.36, -1.04] | 0.635 · 0.922 | 0.745 · 0.575 |
| K08_WICK_BOUNCE | 15.24 | 0.0328 · 0.0387 | 0.852 [0.565, 1.138] | [0.424, 1.308] | 0.635 [0.352, 1.035] | 38/540 (502) | -2.85 [-4.42, -1.31] | -2.78 [-4.42, -1.33] | 1.115 · 0.589 | 0.857 · 0.678 |
| K08b_LONGWICK | 49.44 | 0.1142 · 0.121 | 0.946 [0.841, 1.059] | [0.773, 1.14] | 1.076 [0.852, 1.365] | 191/540 (349) | -1.56 [-2.31, -0.82] | -1.59 [-2.4, -0.78] | 0.92 · 0.96 | 0.961 · 0.915 |
| K09_HANGMAN | 0.67 | 0.001 · 0.0012 | 0.831 [0.0, 2.096] | [0.0, 3.547] | None — | 2/540 (538) | -1.99 [-9.17, 4.0] | +0.66 [-4.41, 5.13] | 0.653 · 1.06 | 0.0 · — |
| K10_SHOOT | 0.06 | 0.0 · 0.0001 | 0.0 [0.0, 0.0] | [0.0, 0.0] | None — | 0/540 (540) | +0.00 [0.0, 0.0] | +0.00 [0.0, 0.0] | 0.0 · 0.0 | 0.0 · — |
| K11_INSIDE | 87.5 | 0.2211 · 0.2127 | 1.038 [0.966, 1.11] | [0.91, 1.162] | 1.032 [0.845, 1.25] | 340/540 (200) | -0.82 [-1.32, -0.33] | -0.74 [-1.33, -0.16] | 0.996 · 1.072 | 1.071 · 1.189 |
| K11_SPIN | 48.7 | 0.126 · 0.1188 | 1.059 [0.949, 1.171] | [0.868, 1.257] | 0.918 [0.712, 1.181] | 212/540 (328) | -1.23 [-1.98, -0.46] | -1.41 [-2.3, -0.57] | 1.042 · 1.065 | 1.107 · 0.976 |
| K11_PIERCING | 5.25 | 0.0127 · 0.0127 | 1.004 [0.621, 1.424] | [0.408, 1.697] | 0.824 [0.36, 1.833] | 23/540 (517) | -4.77 [-7.91, -1.69] | -1.93 [-4.73, 0.6] | 0.981 · 1.055 | 0.872 · 1.036 |
| K11_MARUBOZU | 9.16 | 0.0216 · 0.0212 | 1.015 [0.699, 1.351] | [0.565, 1.598] | 1.0 [0.594, 1.685] | 38/540 (502) | -3.55 [-5.92, -1.15] | -1.45 [-3.65, 0.58] | 0.995 · 1.018 | 1.018 · 0.993 |
| K11_SOLDIERS | 2.62 | 0.0039 · 0.0054 | 0.728 [0.281, 1.26] | [0.085, 1.62] | 0.8 [0.125, 4.0] | 8/540 (532) | -5.47 [-9.32, -1.8] | -2.66 [-6.22, 0.56] | 0.859 · 0.588 | 0.492 · 1.489 |
| B20_CANDLE_AT_SUPPORT | 119.27 | 0.3015 · 0.3056 | 0.987 [0.894, 1.088] | [0.822, 1.142] | 1.045 [0.867, 1.282] | 256/540 (284) | -0.63 [-1.04, -0.2] | -0.64 [-1.16, -0.08] | 1.032 · 0.977 | 0.957 · 0.902 |

## 3. 2026 (descriptive)

| flag | validation lift [95%] | prevalence POS · NEG | holdout lift [95%] | prevalence POS · NEG |
|---|---|---|---|---|
| K01_HAMMER | 1.137 [0.863, 1.437] | 0.053 · 0.0464 | 1.191 [0.83, 1.604] | 0.0495 · 0.0413 |
| K01_HAMMER_3 | 1.093 [0.871, 1.315] | 0.1422 · 0.1297 | 1.046 [0.774, 1.347] | 0.1213 · 0.1159 |
| K02_RED_HAMMER | 1.111 [0.751, 1.494] | 0.0297 · 0.0267 | 1.195 [0.733, 1.749] | 0.0283 · 0.0235 |
| K03_INV_HAMMER | 1.119 [0.903, 1.356] | 0.0739 · 0.0658 | 0.879 [0.647, 1.124] | 0.0624 · 0.0713 |
| K03_INV_HAMMER_3 | 1.066 [0.886, 1.253] | 0.1912 · 0.179 | 0.958 [0.764, 1.153] | 0.1826 · 0.1908 |
| K04_DOJI | 0.977 [0.825, 1.129] | 0.11 · 0.1127 | 0.992 [0.822, 1.178] | 0.1154 · 0.1164 |
| K04b_DOJI_SUPPORT | 0.834 [0.565, 1.13] | 0.0233 · 0.0281 | 0.96 [0.601, 1.356] | 0.0283 · 0.0295 |
| K05_ENGULF | 0.892 [0.639, 1.151] | 0.0353 · 0.0397 | 0.877 [0.597, 1.169] | 0.0365 · 0.0418 |
| K05_ENGULF_3 | 0.981 [0.773, 1.207] | 0.1181 · 0.1204 | 0.911 [0.679, 1.167] | 0.1143 · 0.1257 |
| K06_MSTAR | 1.157 [0.592, 1.774] | 0.0112 · 0.0097 | 0.907 [0.289, 1.616] | 0.0082 · 0.0091 |
| K06b_DOJI_THEN_ENGULF | 0.571 [0.187, 1.005] | 0.0056 · 0.01 | 1.079 [0.49, 1.764] | 0.013 · 0.012 |
| K07_HARAMI | 0.998 [0.724, 1.307] | 0.0337 · 0.0338 | 0.922 [0.61, 1.274] | 0.033 · 0.0358 |
| K08_WICK_BOUNCE | 1.445 [1.025, 1.882] | 0.061 · 0.0416 | 1.05 [0.609, 1.575] | 0.0412 · 0.0392 |
| K08b_LONGWICK | 0.972 [0.818, 1.135] | 0.1189 · 0.1224 | 0.936 [0.748, 1.126] | 0.1095 · 0.1172 |
| K09_HANGMAN | 1.758 [0.0, 3.997] | 0.0024 · 0.0013 | 0.0 [0.0, 0.0] | 0.0 · 0.0016 |
| K10_SHOOT | 0.0 [0.0, 0.0] | 0.0 · 0.0002 | 0.0 [0.0, 0.0] | 0.0 · 0.0001 |
| K11_INSIDE | 1.023 [0.929, 1.112] | 0.2129 · 0.2078 | 1.025 [0.925, 1.134] | 0.2167 · 0.2112 |
| K11_SPIN | 0.936 [0.789, 1.09] | 0.1044 · 0.1117 | 0.978 [0.808, 1.147] | 0.119 · 0.1217 |
| K11_PIERCING | 1.083 [0.602, 1.605] | 0.0145 · 0.0133 | 0.888 [0.401, 1.463] | 0.0118 · 0.0133 |
| K11_MARUBOZU | 0.856 [0.532, 1.23] | 0.0193 · 0.0226 | 0.73 [0.325, 1.231] | 0.0141 · 0.0195 |
| K11_SOLDIERS | 0.716 [0.147, 1.408] | 0.004 · 0.0057 | 0.23 [0.0, 0.738] | 0.0012 · 0.0052 |
| B20_CANDLE_AT_SUPPORT | 0.986 [0.874, 1.102] | 0.2996 · 0.3039 | 0.836 [0.695, 0.975] | 0.2497 · 0.3 |

## 4. Lead profile of the hammer

| flag | far | T−10 | T−9 | T−8 | T−7 | T−6 | T−5 | T−4 | T−3 | T−2 | T−1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| K01_HAMMER | 0.041 | 0.0391 | 0.0474 | 0.0494 | 0.0504 | 0.0389 | 0.0249 | 0.0458 | 0.0314 | 0.0354 | 0.0398 |

## 5. Reading

- **Alone:** no candle separates. Hammer 1.136 [0.935, 1.357], inverted hammer 0.992, bullish engulfing 0.932, morning star 0.754, harami 0.764 [0.572, 0.964] (below 1). Every candle ranks below the drop and volatility rankings at equal burden.
- **In context:** the hammer at the support has lift 1.165 and 0.861 when the stock is oversold. A positive candle at the support (the app's condition) is 0.987 [0.894, 1.088].
- **Composite:** the third-party rule «doji or morning star must be followed by an engulfing» is 0.8 [0.474, 1.204].
- **2026:** one candle has a lower bound above 1 in one window (long lower wick then +5%, validation 1.445 [1.025, 1.882]). It is not in the other window (1.05) or in development (0.852). With 22 candle flags, one such hit is expected by chance.
- The hanging man and the shooting star almost never occur on pivot-days (they need a close near the 20-session high), so they cannot be judged here.
- **Conclusion:** on daily bars, Faisal's candles are confirmations a trader reads at a prepared moment, as T-CANDLE concluded. They carry no measurable information about a +70% leg 7–10 sessions ahead.

