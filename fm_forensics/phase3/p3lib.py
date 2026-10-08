"""🔬 PHASE 3 — مكتبةُ البحث (قراءةٌ فقط · لا إنتاج · لا V4 · لا تلغرام).

جدارُ النظر للأمام: كلُّ قرارٍ بتاريخ T يُحسب على شموعٍ تاريخُها < T (الفرزُ الصباحيُّ يرى إغلاقَ الأمس)،
ووسومُ النتيجة تُحسب من شموعٍ تاريخُها ≥ T **بعد** تجميد الحقول التاريخيّة (الدالّتان منفصلتان بالاسم).

`run_gates(sym, df, neutral=…)` تُعيد `analyze_ticker` الإنتاجيّ **بلا تعديلٍ في الكود**: التعطيلُ الموضعيّ لبوّابةٍ
واحدة يتمّ بقيمٍ مُرخاةٍ في `CONFIG` تُستعاد في `finally` (وفي مرساة اللمستين بغلافٍ على `tested_level` يُستعاد كذلك).
هذا بحثٌ معزول: لا يُستورَد من الإنتاج ولا يكتب حالةً."""
import contextlib
import csv
import gzip
import io
import json
import os
import re
import sys

os.environ.setdefault("FAISAL_ONLY", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import numpy as np                      # noqa: E402
import pandas as pd                     # noqa: E402
with contextlib.redirect_stdout(io.StringIO()):
    import Super_stock as S             # noqa: E402

ANCHORS = ["DKI", "SXTC", "HUBC"]
NEG_ANCHOR = "CRE"
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- bars
_DATA = None


def load():
    global _DATA
    if _DATA is None:
        p = sorted(f for f in os.listdir(os.path.join(ROOT, "fm_forensics", "data")) if f.startswith("bars_"))[-1]
        _DATA = json.load(gzip.open(os.path.join(ROOT, "fm_forensics", "data", p), "rt"))
        _DATA["_cal"] = sorted({r[0] for rows in _DATA["daily"].values() for r in rows})
    return _DATA


def calendar():
    return load()["_cal"]


def cal_index(day):
    """موضعُ التاريخ في تقويم الجلسات (أو موضعُ أوّل جلسةٍ بعده)."""
    cal = calendar()
    lo, hi = 0, len(cal)
    while lo < hi:
        mid = (lo + hi) // 2
        if cal[mid] < day:
            lo = mid + 1
        else:
            hi = mid
    return lo


def session(day):
    """أوّلُ جلسةٍ بتاريخ ≥ day (قرارُ عطلة نهاية الأسبوع يُنسَب إلى الجلسة التالية؛ شموعُه < تلك الجلسة = حتى الجمعة)."""
    cal = calendar()
    return cal[min(cal_index(day), len(cal) - 1)]


def shift(day, n):
    """التاريخُ بعد n جلسة (n سالبٌ = قبل)."""
    cal = calendar()
    i = cal_index(day) + n
    return cal[max(0, min(len(cal) - 1, i))]


def frame(rows):
    df = pd.DataFrame(rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"])
    df["Date"] = pd.to_datetime(df["Date"])
    return df.set_index("Date")


def bars_before(sym, day):
    """شموعُ الرمز بتاريخٍ < day (جدارُ النظر للأمام)."""
    rows = load()["daily"].get(sym) or []
    return [r for r in rows if r[0] < day]


def bars_from(sym, day):
    rows = load()["daily"].get(sym) or []
    return [r for r in rows if r[0] >= day]


def rsplits(sym):
    sp = (load().get("splits") or {}).get(sym) or []
    return sorted((d, float(r)) for d, r in sp if float(r) < 1.0)


# ---------------------------------------------------------------- gates
GATE_NEUTRAL = {
    "M1": {"MIN_PRICE": 0.0},
    "M2_CEIL": {"MAX_DROP_PCT": 1e9},
    "M2_FLOOR": {"MIN_DROP_FLOOR": -1e9},
    "M3": {"PRIOR_SPIKE_FLOOR": -1e9},
    "M4_RANGE": {"BASE_RANGE_MAX_PCT": 1e9},
    "M4_RISE": {"RECENT_RISE_BLOCK_PCT": 1e9},
    "M5": {"MIN_DOLLAR_VOL": 0.0},
    "RSI_OS": {"RSI_OS_HARD": 1e9},
    "RSI_NOW": {"RSI_NOW_HARD": 1e9},
    "SOFT": {"WATCH_MAX_FAILS": 10 ** 6},
    "SCORE": {"SCORE_MIN": -1e9},
    "ANCHOR": {},                       # يُعالَج بغلاف tested_level
}
GATE_ORDER = ["M1", "M2_CEIL", "M2_FLOOR", "M3", "M4_RANGE", "M4_RISE", "M5", "RSI_OS", "RSI_NOW", "SOFT", "ANCHOR", "SCORE"]
_ORIG_TL = S.tested_level


def _tl_neutral(df, lookback=30, tol=0.015, min_touches=2):
    r = _ORIG_TL(df, lookback, tol, min_touches)
    if r:
        return r
    try:
        base = float(df.tail(int(lookback))["Low"].min())
    except Exception:                                            # noqa: BLE001
        return None
    return {"level": round(base, 4), "touches": 1}


def run_gates(sym, df, neutral=()):
    """(النتيجة، سببُ الرفض، تفاصيل) — `analyze_ticker` الإنتاجيّ كما هو؛ التعطيلُ بقيمٍ مُرخاةٍ تُستعاد."""
    saved = {}
    for g in neutral:
        for k, v in GATE_NEUTRAL[g].items():
            saved[k] = S.CONFIG[k]
            S.CONFIG[k] = v
    if "ANCHOR" in neutral:
        S.tested_level = _tl_neutral
    S._REJECT_REASONS.pop(sym, None)
    for k in ("BT_SPLIT_REF_M2", "BT_SPLIT_AWARE_M4"):
        S.CONFIG[k] = 0
    S._BT_SPLITS_CTX = None
    try:
        if len(df) < S.CONFIG["MIN_BARS"]:
            return "TOO_FEW_BARS", "MIN_BARS", None
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                r = S.analyze_ticker(sym, df)
            except Exception as e:                                # noqa: BLE001
                return "ERROR", type(e).__name__, None
        if r:
            return "PASS", "", dict(score=r.get("score"), soft_fails=len(r.get("soft_fails") or []),
                                    readiness=r.get("readiness_pct"), entry_lo=r.get("entry_lo"), stop=r.get("stop"))
        return "REJECT", S._REJECT_REASONS.get(sym, "?"), None
    finally:
        for k, v in saved.items():
            S.CONFIG[k] = v
        S.tested_level = _ORIG_TL


def reason_gate(reason):
    """تحويلُ رمز الرفض الإنتاجيّ إلى اسم بوّابةٍ في مصفوفة LOGO."""
    if not reason:
        return ""
    m = {"M1_سعر": "M1", "M2_هبوط_فوق_97": "M2_CEIL", "M2_هبوط_تحت_40": "M2_FLOOR", "M2_hi52": "M2_FLOOR",
         "M3_انفجار_تحت_60": "M3", "M4_base_واسعة": "M4_RANGE", "M4_base_lo": "M4_RANGE", "M4_انفجر_فعلاً": "M4_RISE",
         "M5_سيولة": "M5", "M10_RSI_ما_تشبّع": "RSI_OS", "M10_RSI_فات_القطار": "RSI_NOW", "M_لا_مستوى_مختبر": "ANCHOR",
         "MIN_BARS": "DEPTH"}
    if reason in m:
        return m[reason]
    if reason.startswith("نواقص_فوق") or reason.startswith("RR+نواقص"):
        return "SOFT"
    if reason.startswith("نقاط_تحت"):
        return "SCORE"
    if reason.startswith("بعيد_عن_الدخول"):
        return "NEAR"
    return reason


# ---------------------------------------------------------------- context (T−1 only)
def context(sym, day):
    """حقولُ السياق من شموعٍ < day وحدَها (بلا نظرٍ للأمام)."""
    rows = bars_before(sym, day)
    if len(rows) < 2:
        return None
    df = frame(rows)
    c = df["Close"].values.astype(float); h = df["High"].values.astype(float); l = df["Low"].values.astype(float)
    o = df["Open"].values.astype(float); v = df["Volume"].values.astype(float)
    n = len(c); price = float(c[-1])
    out = dict(asof=rows[-1][0], bars=n, price=round(price, 4),
               ret1=round((c[-1] / c[-2] - 1) * 100, 2) if n > 1 and c[-2] > 0 else None,
               ret5=round((c[-1] / c[-6] - 1) * 100, 2) if n > 6 and c[-6] > 0 else None,
               volume=float(v[-1]), dollar_vol20=round(float(np.mean(c[-20:] * v[-20:])), 0),
               vol_ratio=round(float(v[-1] / np.mean(v[-21:-1])), 2) if n > 21 and np.mean(v[-21:-1]) > 0 else None,
               gap_pct=round((o[-1] / c[-2] - 1) * 100, 2) if n > 1 and c[-2] > 0 else None)
    tr = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    out["atr14_pct"] = round(float(np.mean(tr[-14:]) / price * 100), 2) if len(tr) >= 14 and price > 0 else None
    hi52 = float(np.max(h[-252:])); out["hi52"] = round(hi52, 4)
    out["drop_pct"] = round((1 - price / hi52) * 100, 2) if hi52 > 0 else None
    try:
        bs, ns = S.spike_info(c, exclude_last=S.CONFIG["BASE_WINDOW"]); out["spike_pct"] = round(float(bs), 1); out["n_spikes"] = int(ns)
    except Exception:                                            # noqa: BLE001
        out["spike_pct"] = None; out["n_spikes"] = None
    bw = S.CONFIG["BASE_WINDOW"]; bh = float(np.max(h[-bw:])); bl = float(np.min(l[-bw:]))
    out["base_range_pct"] = round((bh / bl - 1) * 100, 1) if bl > 0 else None
    lo30 = float(np.min(l[-30:])); out["low30"] = round(lo30, 4)
    out["dist_low30_pct"] = round((price / lo30 - 1) * 100, 2) if lo30 > 0 else None
    out["bars_since_low30"] = int(n - 1 - int(np.argmin(l[-30:])) - (n - min(n, 30)))
    try:
        tl = _ORIG_TL(df); out["tested_touches"] = int(tl["touches"]) if tl else 0; out["tested_level"] = tl["level"] if tl else None
    except Exception:                                            # noqa: BLE001
        out["tested_touches"] = None; out["tested_level"] = None
    try:
        r = S.rsi(df["Close"]); out["rsi14"] = round(float(r.iloc[-1]), 1); out["rsi_min25"] = round(float(r.tail(25).min()), 1)
    except Exception:                                            # noqa: BLE001
        out["rsi14"] = None; out["rsi_min25"] = None
    try:
        e30 = float(S.ema(df["Close"], 30)); out["vs_ema30_pct"] = round((price / e30 - 1) * 100, 2) if e30 > 0 else None
    except Exception:                                            # noqa: BLE001
        out["vs_ema30_pct"] = None
    sp = [(d, r) for d, r in rsplits(sym) if d <= rows[-1][0]]
    if sp:
        d0 = sp[-1][0]; post = [r for r in rows if r[0] >= d0]
        out["last_rsplit"] = d0; out["bars_since_split"] = len(post)
        psh = max((r[2] for r in post), default=None); out["post_split_high"] = round(psh, 4) if psh else None
        out["drop_from_psh_pct"] = round((1 - price / psh) * 100, 2) if psh else None
        out["first_post_split_open"] = post[0][1] if post else None
    else:
        out["last_rsplit"] = ""; out["bars_since_split"] = None; out["post_split_high"] = None; out["drop_from_psh_pct"] = None
        out["first_post_split_open"] = None
    # فجوةٌ هابطةٌ غيرُ مغطّاةٍ تحت السعر (نافذة 60): أدنى فجوةٍ (ارتفاعُ شمعةٍ < أدنى الشمعة السابقة) لم يعُد السعرُ فوقها
    g_below = None
    for i in range(max(1, n - 60), n):
        if h[i] < l[i - 1]:                                      # فجوةٌ هابطة
            top = l[i - 1]
            if not (np.max(h[i:]) >= top):                      # لم تُغطَّ
                g_below = top
    out["gap_below_level"] = round(float(g_below), 4) if g_below else None
    return out


# ---------------------------------------------------------------- outcomes (future, evaluation only)
P_LEVELS = (25, 50, 100)
K_WINDOWS = (5, 10, 15, 20)


def outcomes(sym, day):
    """وسومُ النتيجة من شموعٍ ≥ day — تقييمٌ فقط؛ تُنادى بعد تجميد الحقول التاريخيّة."""
    before = bars_before(sym, day)
    after = bars_from(sym, day)
    if not before or not after:
        return None
    ref = float(before[-1][4])
    c_prev = np.array([r[4] for r in before], dtype=float); h_prev = np.array([r[2] for r in before], dtype=float)
    l_prev = np.array([r[3] for r in before], dtype=float)
    tr = np.maximum(h_prev[1:] - l_prev[1:], np.maximum(abs(h_prev[1:] - c_prev[:-1]), abs(l_prev[1:] - c_prev[:-1])))
    atr = float(np.mean(tr[-14:])) if len(tr) >= 14 else None
    highs = [float(r[2]) for r in after]
    out = dict(ref_close=round(ref, 4), n_after=len(after))
    for k in K_WINDOWS:
        mx = max(highs[:k]) if highs[:k] else None
        out[f"max_gain_{k}"] = round((mx / ref - 1) * 100, 1) if mx and ref > 0 else None
        for p in P_LEVELS:
            out[f"MOVE_{p}_{k}"] = int(bool(mx and ref > 0 and mx >= ref * (1 + p / 100))) if len(highs) >= min(k, 1) else None
        out[f"VOL_ADJ_{k}"] = int(bool(mx and atr and mx >= ref + 3 * atr)) if atr else None
    for p in P_LEVELS:
        first = next((i + 1 for i, hh in enumerate(highs[:60]) if ref > 0 and hh >= ref * (1 + p / 100)), None)
        out[f"first_session_{p}"] = first
    return out


# ---------------------------------------------------------------- Faisal dated evidence
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})$")
STATE_MAP = {"READY": "READY", "WAIT": "WATCH", "WATCH": "WATCH", "FOCUS_LIST": "FOCUS", "OPEN_POSITION": "ENTRY",
             "TARGET": "ENTRY", "OUTCOME": "ENTRY", "OUTCOME/WAIT": "ENTRY", "REJECT": "EXIT", "PLAN": "WATCH",
             "MULTI": "UNKNOWN", "UNKNOWN": "UNKNOWN", "NONE": "MENTION", "": "MENTION"}
ENTRY_WORDS = ("دخلت", "دخلنا", "ندخل", "دخول من", "الشراء", "شريت", "اشتريت", "اضفت", "تعزيز")
EXIT_WORDS = ("طلعت", "خرجت", "بعت", "بعنا", "جنيت", "خروج")


def faisal_rows():
    """الصفوفُ المؤرَّخةُ بدقّة اليوم من المدوّنة (الخطُّ الزمنيّ ‏+ المرورُ البصريّ V4 ‏+ حالاتُ V4)."""
    rows = {}
    with open(os.path.join(ROOT, "fm_forensics", "FAISAL_FOCUS_TIMELINE.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d = r["DATE"].strip()
            if not DATE_RE.match(d) or not r["TICKER"]:
                continue
            key = (r["IMAGE_ID"], r["TICKER"])
            rows[key] = dict(image=r["IMAGE_ID"], ticker=r["TICKER"].strip().upper(), date=d, author=r["AUTHOR"],
                             is_faisal=r["IS_FAISAL"] == "True", decision=r["DECISION"], role=r["ROLE"], note=r["EYE_NOTE"], gist="")
    vp = os.path.join(ROOT, "faisal_method_v4", "data", "visual_pass_v4.jsonl")
    if os.path.exists(vp):
        for line in open(vp, encoding="utf-8"):
            u = json.loads(line)
            d = (u.get("d") or "").strip()
            if not DATE_RE.match(d):
                continue
            for t in (u.get("t") or []):
                t = str(t).strip().upper().rstrip("?")
                if not t.isalpha():
                    continue
                key = (u["id"], t)
                base = rows.get(key) or dict(image=u["id"], ticker=t, date=d, author=u.get("a"), is_faisal=str(u.get("a")) in ("F", "F_inferred"),
                                             decision=u.get("dec") or "NONE", role="", note="")
                base["gist"] = (u.get("g") or "")[:300]
                base["dec_v4"] = u.get("dec")
                base["levels"] = json.dumps(u.get("lv") or {}, ensure_ascii=False)
                base["tf"] = ",".join(u.get("tf") or [])
                rows[key] = base
    out = list(rows.values())
    for r in out:
        r["state"] = classify(r)
    return sorted(out, key=lambda r: (r["ticker"], r["date"], r["image"]))


def classify(r):
    """صنفُ الملاحظة من القرار الموسوم ‏+ كلماتِ الفعل في الخلاصة — لا يُستدَلّ من السعر اللاحق."""
    dec = (r.get("decision") or "NONE").strip()
    st = STATE_MAP.get(dec, "UNKNOWN")
    g = (r.get("gist") or "") + " " + (r.get("note") or "")
    if st in ("MENTION", "UNKNOWN", "WATCH"):
        if any(w in g for w in EXIT_WORDS) and st != "WATCH":
            return "EXIT"
        if any(w in g for w in ENTRY_WORDS) and st != "WATCH":
            return "ENTRY"
    if not r.get("is_faisal", True):
        return "MENTION" if st in ("MENTION",) else st
    return st


def write_csv(path, rows, keys=None):
    if not rows:
        open(path, "w").write("")
        return
    keys = keys or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
