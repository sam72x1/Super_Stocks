# FAISAL_FOCUS_MODEL — what makes a stock a focus item, and a scoring hypothesis (NOT implemented) (2026-10-08)

## 1. Observed inputs to focus (from images; each with evidence class)
| Input | Direction | Evidence | Class |
|---|---|---|---|
| Founding event: reverse split or offering, then collapse | required context | IMG_0151/0153 (split recipe), TG_2077 («مقسم أو طرح أو نقل من otc»), DKI/SXTC/HUBC all post-split | DIRECTLY_SUPPORTED |
| Prior concentrated liquidity in the base («السيولة السابقة المتمركزة») | required | X_20260918_61_VEEE, TG_57870, TG_50829 | DIRECTLY_SUPPORTED (no threshold) |
| Low RSI at the base (22–27 ideal; «مستحيل يصعد إذا RSI بمناطق 40») | required for readiness, not for focus | TG_2043, TG_1870, IMG_0531 | DIRECTLY_SUPPORTED |
| Base holds 3–5 sessions; test bounce 10–20%; retest | stage marker | IMG_0151, X_85_YMT, IMG_0486, TG_50584 | STRONGLY_SUPPORTED |
| Small float, available-to-borrow < 20k, no groups, no pending offering | validity filters («فرز ثاني») | X_22_pipeline, IMG_0150, TG_50578, IMG_0488, X_kwm | DIRECTLY_SUPPORTED |
| Gap below must be filled before the move (blue gap) | wait condition | TG_57869 (CRE), TG_20260905_06 (SNAL) | SUPPORTED (2 images, both WAIT cases) |
| Gap above = target | target, not focus | IMG_0153, ONCO cards | SUPPORTED |
| Moving averages 20/30/50 as the ladder | stage context | TG_50584, EDU_ma_rizq (third-party), IMG_0486 («حقق متوسط 30») | SUPPORTED (mixed sources) |
| Operator pressure / sweep then reclaim | trigger (not focus) | TG_57894, WA_31, TG_58417, TG_2097 | DIRECTLY_SUPPORTED |

## 2. Temporal pattern (how early focus starts)
- SXTC: FOCUS visible 09-10 (entry day) and in list 09-13; second wave 10-07 — focus persisted ≥ 4 weeks across an exit.
- DKI: in the 09-13 list; explicit WAIT late Sept; still tracked by the owner on 10-0x.
- CRE: open since 2025-08 (TG_2103) → 13+ months of focus before the bot's first READY NOW (2026-10-06).
- HUBC: plan in 2026-04; current chart 10-07 — focus spans months and survives a 1:25 split.
Conclusion (STRONGLY_SUPPORTED): focus is **long-lived and event-driven**, not a daily re-ranking; a stock stays in focus through exits and splits as long as the base thesis survives.

## 3. Focus-score hypothesis (for a shadow evaluator only — not production)
`FOCUS_SCORE = founding_event ∧ identity(M1–M5 or split-restart) ∧ prior_liquidity_in_base ∧ validity(float<4M? · avail<20k · no groups · no offering)` then **stage** ∈ {BASE_FORMING (<3 sessions), BASE_HELD (3–5), TESTED (bounce 10–20% then retest), ZONE (price within 15% above base), PRESSED (sweep 7–13% then reclaim within 2 sessions)}.
- READY (Faisal sense) = ZONE ∧ RSI ≤ ~33 ∧ BASE_HELD.
- TRIGGER = PRESSED (the only event the bot can see on daily bars; intraday operator flow is unavailable since 2026-09-29).
- This is a hypothesis to be measured by shadow evaluation (see `READY_NOW_V2_SPEC.md`), with the explicit risk that V4 (frozen) already encodes most of it and found no advantage over "always WAIT" on the historical cases (V4.1 docs). The *novel* part is the lifecycle persistence + split-restart + visibility, not the rules.

## 4. What the bot does instead (first divergence)
The bot computes focus-like membership every day from scratch (identity gates + tested-level + 15 slots + borrow gate) and shows only 15 members + a 40-row cut of a 300-symbol inside list. The FIRST DIVERGENCE from Faisal is at the **anchor/membership step (L5/L8)**: Faisal keeps a stock in focus from the founding event; the bot admits it only after two touches of the low and only if a slot is free, then forgets the rest.
