"""🔬 PHASE 4 — جدولا التدقيق المكتوبان من قراءة الكود (§24 · §25): توفّرُ البيانات لكلّ حدث · ومرحلةُ كلّ بوّابةٍ قبل المرساة. لا أرقامَ تجريبيّة هنا."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p4lib as P                        # noqa: E402

L = P.L

DATA = [
    dict(EVENT="FIRST_TOUCH (E1: 30-bar low forms)", IN_BOT_DATA="YES (daily bars; `tested_level` base = tail(30).Low.min())", CORRECT_TIMESTAMP="YES (bar close; observable next session)", CORRECT_TIMEFRAME="daily only (Faisal reads 4h/1h for the exact low — `exact_low_stability` exists for display, not for candidacy)", SUFFICIENT_HISTORY="YES (30 bars)", WITHOUT_FUTURE_ADJUSTMENT="split-adjusted series (TradingView adjusted); a reverse split after the low re-bases the level", VERDICT="MODEL MISSING: the event is computable but no object is created from it (no pre-candidate state); timeframe partially DATA MISSING"),
    dict(EVENT="SECOND_TOUCH (E2: production `tested_level` ≥2 clusters within 1.5%)", IN_BOT_DATA="YES", CORRECT_TIMESTAMP="YES", CORRECT_TIMEFRAME="daily", SUFFICIENT_HISTORY="YES", WITHOUT_FUTURE_ADJUSTMENT="YES on the adjusted series", VERDICT="STATE MODEL MISSING: evaluated as an admission test (candidate) instead of as a confirmation on an existing object"),
    dict(EVENT="RETEST (E3: `pivot_cycle_state` stage≥3 — bounce ≥10% then touch of the low band, hold or sweep ≤13%)", IN_BOT_DATA="YES (display-only function on daily bars)", CORRECT_TIMESTAMP="YES", CORRECT_TIMEFRAME="daily (Faisal's 7–13% sweep is read on 1h/4h in his posts)", SUFFICIENT_HISTORY="60-bar window", WITHOUT_FUTURE_ADJUSTMENT="YES", VERDICT="STATE MODEL MISSING: computed for the card text only; never feeds any state; a sweep below the low invalidates E2 by construction"),
    dict(EVENT="TRIGGER (E4: sweep-and-reclaim or stability ≥3 after the test)", IN_BOT_DATA="PARTIAL (daily proxy; the live operator trigger needed Polygon tape — ended 2026-09-29)", CORRECT_TIMESTAMP="daily close only", CORRECT_TIMEFRAME="Faisal: intraday (pre-market/operator); bot: daily", SUFFICIENT_HISTORY="YES", WITHOUT_FUTURE_ADJUSTMENT="YES", VERDICT="DATA MISSING (intraday/operator) + STATE MODEL MISSING (no trigger state; READY NOW is a price-location flag)"),
    dict(EVENT="BREAK (E5: low < level × 0.87 or 60 sessions)", IN_BOT_DATA="YES", CORRECT_TIMESTAMP="YES", CORRECT_TIMEFRAME="daily", SUFFICIENT_HISTORY="YES", WITHOUT_FUTURE_ADJUSTMENT="YES", VERDICT="MODEL MISSING: no object to invalidate"),
    dict(EVENT="Faisal FOCUS/WATCH declaration", IN_BOT_DATA="NO (external text)", CORRECT_TIMESTAMP="dated units only (58% of corpus undated)", CORRECT_TIMEFRAME="n/a", SUFFICIENT_HISTORY="n/a", WITHOUT_FUTURE_ADJUSTMENT="n/a", VERDICT="DATA MISSING for the bot by nature; used here only as ground truth"),
    dict(EVENT="Validity inputs Faisal checks at READY (short available <20k, offering closed, operator present)", IN_BOT_DATA="PARTIAL (borrow via ChartExchange post-select; offering via SEC filings; operator: none after Polygon)", CORRECT_TIMESTAMP="borrow daily (harvest), filings daily", CORRECT_TIMEFRAME="daily", SUFFICIENT_HISTORY="no borrow history before 2026-08", WITHOUT_FUTURE_ADJUSTMENT="YES", VERDICT="DATA MISSING (operator, borrow history) — evaluated after candidacy, never before"),
]

GATES = [
    dict(GATE="DEPTH (MIN_BARS=120)", CONCEPT="data sufficiency", CURRENT_STAGE="EARLY (silent drop)", EVIDENCE_STAGE="UNKNOWN (Faisal measures from the split date — TG_1807/1811)", DIRECT_SUPPORT="NONE", CONTRADICTIONS="post-split histories of 22-42 bars rejected (Phase 2 B_CUT)", KEEP_STAGE="", MOVE_STAGE="", UNKNOWN="x", CONFIDENCE="n/a"),
    dict(GATE="M1 price ≥ 0.40", CONCEPT="exclude sub-penny", CURRENT_STAGE="EARLY", EVIDENCE_STAGE="EARLY (identity)", DIRECT_SUPPORT="PARTIAL (IMG_0153 concept; number from envelope)", CONTRADICTIONS="HCAI 0.46 on his list", KEEP_STAGE="x", MOVE_STAGE="", UNKNOWN="", CONFIDENCE="medium"),
    dict(GATE="M2 ceiling drop ≤ 99.95%", CONCEPT="not a dead/split-trap name", CURRENT_STAGE="EARLY", EVIDENCE_STAGE="UNKNOWN (no Faisal concept; cumulative-adjusted artefact)", DIRECT_SUPPORT="NONE", CONTRADICTIONS="SXTC/HUBC (Phase 2)", KEEP_STAGE="", MOVE_STAGE="", UNKNOWN="x", CONFIDENCE="low"),
    dict(GATE="M2 floor drop ≥ 71.7%", CONCEPT="pivot = exploded then collapsed", CURRENT_STAGE="EARLY", EVIDENCE_STAGE="EARLY (identity, IMG_0151/TG_2077)", DIRECT_SUPPORT="PARTIAL (concept direct; number envelope)", CONTRADICTIONS="post-split reference frame (Phase 2 B_PSH)", KEEP_STAGE="x", MOVE_STAGE="", UNKNOWN="", CONFIDENCE="medium"),
    dict(GATE="M3 prior spike ≥ 78% in 20 sessions", CONCEPT="exploded before", CURRENT_STAGE="EARLY", EVIDENCE_STAGE="EARLY (identity) — but Faisal's «100%» is the target, not the prior spike", DIRECT_SUPPORT="PARTIAL/MISREAD", CONTRADICTIONS="first wall on 13/53 Faisal rows (Phase 3)", KEEP_STAGE="x (concept)", MOVE_STAGE="", UNKNOWN="window/number", CONFIDENCE="low"),
    dict(GATE="M4 range: 15-session range ≤ 120%", CONCEPT="narrow base", CURRENT_STAGE="EARLY", EVIDENCE_STAGE="LATER (Faisal: stability 3-5 sessions ABOVE the low after the test — a post-retest condition)", DIRECT_SUPPORT="NONE for the 15-bar metric", CONTRADICTIONS="Faisal's names have wider 15-bar ranges than date-matched names (Phase 3 inverse odds)", KEEP_STAGE="", MOVE_STAGE="x (as stability after the test)", UNKNOWN="", CONFIDENCE="medium"),
    dict(GATE="M4 rise: 5-session gain ≤ 215%", CONCEPT="don't chase", CURRENT_STAGE="EARLY", EVIDENCE_STAGE="BOTH (chase guard at entry)", DIRECT_SUPPORT="INFERRED", CONTRADICTIONS="second-wave entries (TG_58417)", KEEP_STAGE="", MOVE_STAGE="x (entry)", UNKNOWN="", CONFIDENCE="low"),
    dict(GATE="M5 $vol20 ≥ $14.3K", CONCEPT="liquidity floor", CURRENT_STAGE="EARLY", EVIDENCE_STAGE="UNKNOWN (Faisal: prior concentrated liquidity, not current)", DIRECT_SUPPORT="NONE", CONTRADICTIONS="his picks at $10-170K/day", KEEP_STAGE="", MOVE_STAGE="", UNKNOWN="x", CONFIDENCE="low"),
    dict(GATE="RSI min25 ≤ 69 / RSI now ≤ 71", CONCEPT="was oversold / not flown", CURRENT_STAGE="EARLY", EVIDENCE_STAGE="LATER (RSI <30-33 is an entry/watch condition — three-condition tool)", DIRECT_SUPPORT="PARTIAL", CONTRADICTIONS="RSI_NOW contradicted by his READY calls (Phase 1)", KEEP_STAGE="", MOVE_STAGE="x (watch/entry)", UNKNOWN="", CONFIDENCE="medium"),
    dict(GATE="SOFT ≤ 8 / SCORE ≥ 5", CONCEPT="enough confirmations", CURRENT_STAGE="EARLY", EVIDENCE_STAGE="UNKNOWN (engineering)", DIRECT_SUPPORT="NONE", CONTRADICTIONS="—", KEEP_STAGE="", MOVE_STAGE="", UNKNOWN="x", CONFIDENCE="n/a"),
    dict(GATE="ANCHOR two-touch (tested_level 30/1.5%/2)", CONCEPT="level tested twice and not broken (IMG_0451) = entry/stop reference", CURRENT_STAGE="EARLY (admission)", EVIDENCE_STAGE="LATER (retest/confirmation — the thing Faisal waits for after Watch)", DIRECT_SUPPORT="DIRECT for the entry reference; NONE for admission", CONTRADICTIONS="Watch at touch #1 (SMX TG_1908, KWM, ELPW, DKI TG_57894); sweep retests invalidate it by construction", KEEP_STAGE="", MOVE_STAGE="x (tested in this phase)", UNKNOWN="", CONFIDENCE="measured here"),
    dict(GATE="BORROW ≤ 20k / FLOAT ≤ 50M (post-select)", CONCEPT="short under 20k, small float", CURRENT_STAGE="LATER (after select_top)", EVIDENCE_STAGE="LATER (READY validity: «الشورت 20 ع وشك» CETX TG_50828)", DIRECT_SUPPORT="DIRECT (borrow)", CONTRADICTIONS="—", KEEP_STAGE="x", MOVE_STAGE="", UNKNOWN="", CONFIDENCE="high"),
]


def main():
    L.write_csv(os.path.join(HERE, "DATA_AVAILABILITY_AUDIT.csv"), DATA)
    L.write_csv(os.path.join(HERE, "PHASE4_GATE_STAGE_MATRIX.csv"), GATES)
    print("written", len(DATA), len(GATES))


if __name__ == "__main__":
    main()
