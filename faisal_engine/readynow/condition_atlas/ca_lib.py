"""Faisal condition atlas — condition flags, the classifiers and the comparison rankings (research only).

Rows = the READY NOW discovery rows of one window (pivot-days, corrected onset labels; seeds and HUBC excluded,
`rn_disc_dev.load`) joined with the atlas columns of `ca_build.py` (key: symbol, date).
A flag reads only columns computed from bars <= T. A missing value never satisfies a flag (counted in the reports).
"""
import csv
import gzip
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RN = os.path.dirname(HERE)
sys.path.insert(0, RN)
sys.path.insert(0, os.path.join(RN, "disc"))
os.environ["FAISAL_ONLY"] = "1"
import numpy as np                                                        # noqa: E402
import rn_disc_dev as D                                                   # noqa: E402
import rn_lib as K                                                        # noqa: E402

DATA = os.path.join(HERE, "data")
num = K.num


def _ge(r, k, x):
    v = num(r.get(k))
    return v is not None and v >= x


def _le(r, k, x):
    v = num(r.get(k))
    return v is not None and v <= x


def _lt(r, k, x):
    v = num(r.get(k))
    return v is not None and v < x


def _one(r, k):
    return r.get(k) in ("1", "1.0", 1, 1.0, True)


def _between(r, k, lo, hi):
    v = num(r.get(k))
    return v is not None and lo <= v <= hi


def _held(r):
    return _one(r, "held")


AT_SUPPORT = ("k_hammer_3", "k_invhammer_3", "k_doji_sup_3", "k_engulf_3", "k_piercing_3", "k_mstar_3", "k_longwick_3")

COND = {
    # A · pivot validity
    "A01_SPIKE100": lambda r: _ge(r, "a_spike", 100),
    "A02_DROP50": lambda r: _ge(r, "a_drop", 50),
    "A03_ANNUAL_LOW": lambda r: _le(r, "a_low250", 25),
    "A04_NO_RISE20": lambda r: _lt(r, "a_boom20", 50),
    "A05_SPLIT120": lambda r: _one(r, "split120"),
    "A06_SPLIT_NORISE": lambda r: _le(r, "a_split_rise", 20),
    "A07_HALF_BAND": lambda r: _between(r, "a_half_ratio", 0.70, 1.25),
    "A08_SPLIT3": lambda r: _ge(r, "a_rsplit_n", 3),
    "A11_NO_GROUP_PROXY": lambda r: num(r.get("a_grp10")) == 0,
    # B · technical state
    "B01_RSI30": lambda r: _lt(r, "rsi", 30),
    "B01b_RSI33": lambda r: _lt(r, "rsi", 33),
    "B02_RSI27_10": lambda r: _le(r, "b_rsi_min10", 27),
    "B02b_RSI20_27_10": lambda r: _between(r, "b_rsi_min10", 20, 27),
    "B03_BELOW3": lambda r: _one(r, "below3"),
    "B04_PEAK_AGE30": lambda r: _ge(r, "b_peak_age", 30),
    "B05_HOLD3": lambda r: _ge(r, "hold_n", 3) and _held(r),
    "B05b_HOLD5": lambda r: _ge(r, "hold_n", 5) and _held(r),
    "B06_TEST15": lambda r: _ge(r, "bounce", 15),
    "B07_RETEST": lambda r: _ge(r, "bounce", 15) and _le(r, "dist", 10) and _held(r) and _ge(r, "b_test_ago", 1),
    "B08_SWEEP": lambda r: _one(r, "b_sweep"),
    "B09_TIGHT_NEAR_LOW": lambda r: _le(r, "b_range5", 10) and _le(r, "a_low250", 25),
    "B10_VOL5_3": lambda r: _ge(r, "b_vmax3", 5),
    "B11_MACD_X9": lambda r: _one(r, "b_macd_x9"),
    "B12_GAP10": lambda r: _ge(r, "b_gap_max", 10),
    "B13_EMA_X5": lambda r: _one(r, "ema_x5"),
    "B14_KVO_UP": lambda r: _one(r, "b_kvo_up"),
    "B14b_KVO_X5": lambda r: _one(r, "b_kvo_x5"),
    "B15_CHOP_CTRL": lambda r: _le(r, "b_chop30", 6),
    "B15b_CHOP_VIOLENT": lambda r: _ge(r, "b_chop30", 12),
    "B16_WR_TURN": lambda r: _one(r, "b_wr_turn"),
    "B17_UPDN_VOL": lambda r: _ge(r, "b_updn_v10", 1.0000001),
    "B18_TOUCHES": lambda r: _ge(r, "b_touch5", 3) and _held(r),
    "B19_NEAR5": lambda r: _le(r, "dist", 5),
    "B19b_NEAR15": lambda r: _le(r, "dist", 15),
    "B20_CANDLE_AT_SUPPORT": lambda r: _le(r, "dist", 15) and any(_one(r, k) for k in AT_SUPPORT),
    "B21_ABOVE3050": lambda r: _one(r, "b_above3050"),
    "B22_MA20_FLAT": lambda r: _one(r, "below3") and _ge(r, "b_sma20_slope5", -1),
    "B23_CYCLE3": lambda r: (num(r.get("pc_stage")) or 0) >= 3,
    # K · candles (today, or any of the last 3 sessions with the _3 suffix)
    "K01_HAMMER": lambda r: _one(r, "k_hammer"),
    "K01_HAMMER_3": lambda r: _one(r, "k_hammer_3"),
    "K02_RED_HAMMER": lambda r: _one(r, "k_hammer_red"),
    "K03_INV_HAMMER": lambda r: _one(r, "k_invhammer"),
    "K03_INV_HAMMER_3": lambda r: _one(r, "k_invhammer_3"),
    "K04_DOJI": lambda r: _one(r, "k_doji"),
    "K04b_DOJI_SUPPORT": lambda r: _one(r, "k_doji_sup"),
    "K05_ENGULF": lambda r: _one(r, "k_engulf"),
    "K05_ENGULF_3": lambda r: _one(r, "k_engulf_3"),
    "K06_MSTAR": lambda r: _one(r, "k_mstar"),
    "K06b_DOJI_THEN_ENGULF": lambda r: _one(r, "k_doji_engulf"),
    "K07_HARAMI": lambda r: _one(r, "k_harami"),
    "K08_WICK_BOUNCE": lambda r: _one(r, "k_wick_bounce"),
    "K08b_LONGWICK": lambda r: _one(r, "k_longwick"),
    "K09_HANGMAN": lambda r: _one(r, "k_hangman"),
    "K10_SHOOT": lambda r: _one(r, "k_shoot"),
    "K11_INSIDE": lambda r: _one(r, "k_inside"),
    "K11_SPIN": lambda r: _one(r, "k_spin"),
    "K11_PIERCING": lambda r: _one(r, "k_piercing"),
    "K11_MARUBOZU": lambda r: _one(r, "k_marubozu"),
    "K11_SOLDIERS": lambda r: _one(r, "k_soldiers"),
    # I · invalidation
    "I01_CHASE": lambda r: _ge(r, "dist", 40.0000001) or _ge(r, "ret5", 30.0000001),
    "I02_RSI40": lambda r: _ge(r, "rsi", 40),
    "I03_BOOM5": lambda r: _ge(r, "boom5", 50),
    "I04_GROUP_PROXY": lambda r: _ge(r, "a_grp10", 1),
    # T · timing
    "T01_DIP_LOW": lambda r: _one(r, "t_dip_low"),
    "T02_PEAK_20_30": lambda r: _between(r, "b_peak_age", 20, 30),
}

GROUP = {k: k[0] for k in COND}
# the conditions in context: «at the support» (within 15% of the 25-session low and above it) and «oversold» (RSI < 33)
CONTEXTS = {"all": lambda r: True, "at_support": lambda r: _le(r, "dist", 15) and _held(r),
            "oversold": lambda r: _lt(r, "rsi", 33)}

# ───────── the documented technical conditions counted by the condition-count classifier (Faisal's own, daily) ─────
COUNT_SET = ("A03_ANNUAL_LOW", "A04_NO_RISE20", "B01_RSI30", "B03_BELOW3", "B04_PEAK_AGE30", "B05_HOLD3",
             "B06_TEST15", "B07_RETEST", "B08_SWEEP", "B11_MACD_X9", "B12_GAP10")

# ───────── the app's weighted 4-hour conditions (TG_58420), computed with their daily proxies ─────────
# visible weights sum to 70 of 100 (the rest of the screen is cut off); half credit as the app shows it
APP_WEIGHTS = (
    ("support clear, break failed (12)", 12.0, lambda r: COND["B18_TOUCHES"](r) or COND["B08_SWEEP"](r)),
    ("entry near the support (8)", 8.0, lambda r: _le(r, "dist", 5)),
    ("averages 50/30/20 (8; 4 under and not flattening)", None, None),
    ("daily RSI in 23–27 (12)", 12.0, lambda r: _between(r, "b_rsi_min10", 23, 27)),
    ("MACD improving (10)", 10.0, lambda r: _one(r, "b_macd_x9")),
    ("positive candle at the support (8)", 8.0, COND["B20_CANDLE_AT_SUPPORT"]),
    ("selling weakens, buying improves (7)", 7.0, COND["B17_UPDN_VOL"]),
    ("room or gap above (5)", 5.0, lambda r: _ge(r, "b_gap_max", 10)),
)


def app_score(r):
    s = 0.0
    for _n, w, f in APP_WEIGHTS:
        if f is None:
            s += 8.0 if COND["B22_MA20_FLAT"](r) else (4.0 if _one(r, "below3") else 0.0)
        elif f(r):
            s += w
    return s


def count_score(r):
    return float(sum(1 for k in COUNT_SET if COND[k](r)))


INVALID = ("I01_CHASE", "I03_BOOM5", "I04_GROUP_PROXY")    # Faisal's explicit «no entry» states (I02 is a strength
#                                                           blocker kept inside the model, not a removal)


def invalidated(r):
    return any(COND[k](r) for k in INVALID)


# ───────── the three axes (feature sets for the regularised models) ─────────
AXIS_A = ("A01_SPIKE100", "A02_DROP50", "A03_ANNUAL_LOW", "A04_NO_RISE20", "A05_SPLIT120", "A06_SPLIT_NORISE",
          "A07_HALF_BAND", "A08_SPLIT3", "A11_NO_GROUP_PROXY")
AXIS_B = tuple(k for k in COND if k[0] in "BK")
AXIS_C = AXIS_A + AXIS_B + tuple(k for k in COND if k[0] in "IT")


def design(rows, feats):
    return np.array([[1.0 if COND[k](r) else 0.0 for k in feats] for r in rows])


def _rd(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


_CA = None


def ca_index():
    global _CA
    if _CA is None:
        _CA = {(r["sym"], r["t"]): r for r in _rd(os.path.join(DATA, "ca_rows.csv.gz"))}
    return _CA


def load(window):
    """The window's rows (corrected target, seeds/HUBC excluded, annotated) with the atlas columns joined."""
    rows, by = D.load(window)
    ca = ca_index()
    miss = 0
    for r in rows:
        x = ca.get((r["sym"], r["t"]))
        if x is None:
            miss += 1
            continue
        for k, v in x.items():
            if k not in ("sym", "t"):
                r[k] = v
    return rows, by, miss
