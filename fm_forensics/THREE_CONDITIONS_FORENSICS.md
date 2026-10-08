# THREE_CONDITIONS_FORENSICS — the owner's three conditions vs READY NOW (2026-10-08)

## What the tool is (`three_cond_daily.py`, scheduled 02:43 UTC Tue–Sat)
Match = RSI14 < `rsi_max()` (= `RSI_OVERSOLD` 33 by name) ∧ float < 4M ∧ available-to-borrow < 20,000 ∧ **5-session stability above the exact low** (hourly extended bars) ∧ no ≥ 50% explosion in the last 5 sessions. Price is a category (💵/🪙), not a condition. DQ gate quarantines recent reverse splits and unverified data. Output: one Telegram message, matches named, everything else counted.

## What it produced for the anchors (from run logs / memory, read-only)
| Date | Result |
|---|---|
| 09-25 (first live) | 12 matches incl. SXTC (RSI 26.2, float 401,683, avail 2,000, stable 11 sessions above 1.78); HUBC «مشكوك» (source split mismatch) |
| 09-26 dry (new definition) | SXTC 💵 + HCAI 🪙 (2 matches); FGL excluded as exploded (+62%) |
| 09-29 → 10-02 | SXTC matched every session (6 consecutive sessions 09-25 → 10-02; closes 2.57 → 2.41) |
| 10-05 → 10-07 | 0 matches |
| 10-08 | HUBC avail-unknown + DQ-quarantined (recent split; ÷2 hit 10-07, held 0/3) → not named |
| DKI | never matched (float/avail unknown or RSI; exact low 2.18 then broken 10-01) — per-session reason not reconstructed here (UNKNOWN) |

## Relationship to READY NOW
| Dimension | Three conditions | READY NOW |
|---|---|---|
| Universe | whole NASDAQ ∪ bot lists | 15-slot watchlist only |
| Identity gates (M1–M5) | none | required |
| Anchor | exact low + 5-session hold | tested level (2 touches) + price ≤ top tranche |
| RSI | required < 33 | soft fail only |
| Float / borrow | required (< 4M, < 20k) | float < 50M hard; borrow ≤ 20k at selection |
| Split handling | quarantined (DQ) | M2 wall (de facto exclusion) |
| Trigger | none (stability is a state) | `sweep_confirmed` optional |
| Faisal stage mapped | WATCH/READY (state) | ZONE (location) |

## Verdict
- The three conditions are a **WATCH/READY-state filter** on the whole market; READY NOW is a **location flag** on a tiny selected set. They are orthogonal in universe and in anchor logic. Merging them into READY NOW would (a) import the whole-market universe into a 15-slot list, (b) impose RSI < 33 as hard (contradicting the measured soft-fail design), and (c) still lack the trigger. **Do not merge.**
- What the three-conditions tool demonstrated: it was the only channel that named SXTC for six sessions before its second wave, i.e., a stability-based WATCH signal has recall that READY NOW lacks. Its precision is UNKNOWN (no outcome harvest exists for its matches — a measurable gap, listed in the missed-information register).
- Negative evidence: 10-05 → 10-07 produced 0 matches while SXTC's second wave started 10-07 AH; the tool's 5-session stability requirement had reset after SXTC's 10-01 spike (3.27) — showing that "stability" as defined (exact-low hold) and Faisal's re-entry (sweep to 1.25 then reclaim) are different events.
