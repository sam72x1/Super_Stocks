# GAP_DOWN_FORENSICS — "the gap below must be filled" (2026-10-08)

## Evidence
| Image | Ticker | Statement | Faisal action | Class |
|---|---|---|---|---|
| TG_57869 (2026-09-2x) | CRE | gap below current price must be covered before the up-move | WAIT | DIRECTLY_SUPPORTED (Faisal, owner-confirmed 2026-10-01: «فقاعات 12 و14 لفيصل») |
| TG_20260905_06 (2026-09-05) | SNAL | «الأزرق فجوة لازم يغطيها» | WAIT | DIRECTLY_SUPPORTED |
| IMG_0153 / ONCO cards | various | gap ABOVE = target («تجاوزها يحقق نسبة أعلى») | target | DIRECTLY_SUPPORTED (different rule) |
| T-GAPBELOW (pre-registered test, 2026-10-01, `gapbelow_result.md`) | 3 years, population G 59/68/82 (< floor 100) | «لازم» not literally true: coverage 53.2% filled before the move; no magnet effect (+0.3 pts); a fixed 28% depth beats gap-bottom as a reference (−0.05R) | — | measured: branch 3 «لا قياس» (sample below floor) — NOT confirmed, NOT refuted |

Negative evidence: 2 images only, both WAIT cases, both from the same month; no image shows Faisal entering *because* a gap was filled; no counter-example where he ignores an unfilled gap below (searched OCR for «فجوة» in 11 images: 10 are gap-above/targets).

## Bot
- M9 `GAP_ABOVE_REQUIRED` models only gaps above (targets). There is no gap-below condition in `analyze_ticker`, `entry_status`, or `build_interpretation`. `pivot_cycle_state` shows a sweep line (display).
- CRE case: bot READY NOW 10-06/07/08 on `sweep_confirmed`; Faisal WAIT on the unfilled gap. The bot's `sweep_confirmed` is consistent with the *trigger* rule; the gap-below WAIT is an additional *validity* rule the bot lacks.

## Verdict
- Rule class for "gap below must fill": **DIRECTLY_SUPPORTED as Faisal's stated wait condition (2 cases) · CONTRADICTED as a historical magnet by T-GAPBELOW (no advantage measured, sample too small for a verdict)**. The two are not in conflict: one is what Faisal does, the other is whether it pays.
- Production: no change. Shadow: a FOCUS/validity flag `gap_below_unfilled` could be displayed; it must not block READY without a pre-registered 3-year test with a matched control (T-GAPBELOW failed to reach the sample floor — reopening requires a new population definition, not a rerun).
