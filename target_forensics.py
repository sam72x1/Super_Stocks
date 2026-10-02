"""🎯 `T-TGT` — TARGET FORENSICS: «ما معنى الهدف 100٪؟» (العقد `hs_forensic/target_forensics_prereg.md` · مدموجٌ قبل أيّ رقم).

قراءةٌ فقط (أمرُ المالك 2026-10-02 «DO NOT REOPEN H&S YET»): الإشاراتُ **مخزَّنةٌ سلفًا** من `T-HS-FX` (`fx_signals_bot.csv`) —
**لا يُنادى الكاشف** (`HS.detect` ولا `retest_state` ولا غيرُهما) · لا تلغرام · لا حالةَ إنتاج · `git_save` يدفع `hs_research/target/`
وحدَه · ومن `hs_forensic.py` (المُغلَق) دوالُّ الترتيب النقيّة وحدَها (`event_bars` · `classify` · `excursion`) فيطابق التعريفُ
ما قيس سابقًا بت-بت — ولا يمسّ إغلاقَه.

الأوضاع (`TGT_MODE`): **sample** (حالةُ DXST ‏+ تصديرُ العيّنة العمياء · بلا إحصاءٍ للمجتمع) · **pop** (المجتمع — يرفض قبل دفع الوسوم ·
§⑤) · **open** (محلّيّ بلا شبكة: فتحُ المفتاح بعد دفع الوسوم)."""
from __future__ import annotations

import base64
import csv
import datetime as dt
import hashlib
import json
import math
import os
import random
import sys
import zlib

import numpy as np
import pandas as pd

import hs_forensic as FX

TOOL = "T-TGT"
OUT_DIR = os.path.join("hs_research", "target")
SIG_FILE = os.path.join("hs_research", "forensic", "fx_signals_bot.csv")
SEEN_FILES = tuple(os.path.join("hs_research", "forensic", f)
                   for f in ("fx_blind_result.json", "fx_rx_blind_result.json", "fx_replay.json"))
DXST_FILE = os.path.join(OUT_DIR, "tf_dxst.json")
CHARTS_FILE = os.path.join(OUT_DIR, "tf_blind_charts.json")
KEY_FILE = os.path.join(OUT_DIR, "tf_blind_key.b64")
LABELS_FILE = os.path.join(OUT_DIR, "tf_blind_labels.json")
RESULT_FILE = os.path.join(OUT_DIR, "tf_blind_result.json")
POP_FILE = os.path.join(OUT_DIR, "tf_pop.json")
POP_CSV = os.path.join(OUT_DIR, "tf_pop_signals.csv")

START = "2016-01-01"                     # إطارُ `T-HS-FX` نفسُه (FX_START)
ERAS_OK = ("TRAIN", "VAL", "TEST", "SEEN")
ENTRIES = ("B", "C", "D")                # §③ المداخلُ المدعومة
TARGETS = ("TC", "TR1", "TR2", "TFT", "T30E", "T100E", "T100L")
STOPS = ("I1", "I2")
WINS = (30, 60, 90)
SAMPLE_N = 30
SAMPLE_SEED = 20261011                   # §⑦
MIX_SEED = 20261012                      # §⑦
SAMPLE_YEAR_OUT = "2022"                 # سنةُ بناء القواعد (`hs_prereg.md §⑤`)
EXCL_DAYS = 30                           # §⑦ ‏±30 يومًا تقويميًّا من حالةٍ رُئيت
CHART_BARS = 200                         # §⑦
LADDER_SHOW = 5                          # §⑦ L1…L5
ALIGN_TOL = 0.001                        # §⑨ ‏|إغلاقُ e ÷ E − 1| ‏≤0.1%
D_MATCH_TOL = 1e-6                       # §⑧ استعادةُ بار D
ALIGN_MIN = 0.95                         # §⑨
REPRO_MIN = 0.99                         # §⑨
LABEL_TOL = 0.03                         # §⑦ MATCH ‏|TC/F − 1| ‏≤3%
F_MIN_GAP = 0.03                         # §⑦ F بعيدٌ ‏≥3% عن E
F_NECK_BAND = 0.02                       # §⑦ وخارج ‏±2% من العنق
DXST = {"sym": "DXST", "tweet": "2026-06-16", "neck": 2.864, "s1": 2.539, "s2": 2.306, "low": 2.280, "trough": 2.455,
        "levels": {"R 3.114": 3.114, "T-C 3.273": 3.273, "T1 3.302": 3.302, "T2 3.610": 3.610, "PATH 4.467": 4.467,
                   "2x2.280 = 4.56": 4.56, "2x2.455 = 4.91": 4.91},
        "drawn": (2.864, 3.114, 3.302, 3.610, 4.467, 2.539, 2.306, 2.280)}
DXST_PROV_BARS = 120                     # §⑥
DXST_PROV_TOL = 0.005                    # §⑥ ‏≤0.5%
DXST_LADDER_TOL = 0.01                   # §⑥ ضمن 1%

HIT, AFTER, INVF, MISS, OPEN = ("TARGET_HIT", "TARGET_AFTER_INVALIDATION", "INVALIDATION_FIRST", "TARGET_MISSED",
                                "OPEN_WINDOW")
NOTGT, ATENTRY = "NO_TARGET", "TARGET_AT_OR_BELOW_ENTRY"
CLASSES = (HIT, AFTER, INVF, MISS, OPEN, NOTGT, ATENTRY)
_MAP = {"CLEAN": HIT, "DIRTY": AFTER, "STOP": INVF, "NEITHER": MISS}


def log(*a):
    print(*a, flush=True)


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# ① أدواتٌ نقيّة (تُختبَر بلا شبكة)
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
def _f(x):
    """حقلُ CSV ⟵ float أو None (الفارغُ وغيرُ المنتهي None)."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _i(x):
    v = _f(x)
    return None if v is None else int(round(v))


def outcome(h, c, e: int, E: float, target, stop_px, w: int) -> dict:
    """الفئاتُ الخمس (§④) لهدفٍ وإبطالٍ ونافذة: الهدفُ **بالأعلى** والإبطالُ **بالإغلاق** من e+1 · والتعادلُ إبطالٌ أوّلًا (`FX.classify`) ·
    ونافذةٌ ناقصة ⟵ OPEN_WINDOW · وتعريفٌ غائب ⟵ NO_TARGET · وهدفٌ ‏≤E ⟵ TARGET_AT_OR_BELOW_ENTRY (خارج المقام)."""
    if target is None or not math.isfinite(float(target)):
        return {"cls": NOTGT}
    if not float(target) > float(E):
        return {"cls": ATENTRY}
    eb = FX.event_bars(h, c, e, float(target), stop_px, w)
    if eb is None:
        return {"cls": OPEN}
    t_t, t_s = eb
    return {"cls": _MAP[FX.classify(t_t, t_s)], "t_tgt": t_t, "t_stop": t_s}


def target_prices(tc, E: float, head_low, ladder, ft) -> dict:
    """§② التعريفاتُ السبعة بأسمائها — ثابتةٌ ولا يُختار أحدُها."""
    lv = list(ladder or [])
    return {"TC": _f(tc), "TR1": (lv[0] if len(lv) > 0 else None), "TR2": (lv[1] if len(lv) > 1 else None),
            "TFT": _f(ft), "T30E": 1.30 * float(E), "T100E": 2.0 * float(E),
            "T100L": (2.0 * float(head_low) if _f(head_low) is not None else None)}


def ladder_frame(df, e: int, days: int):
    """الإطارُ حتى بار الدخول ضمنًا (لا نظرَ مستقبليّ) بنافذة الإنتاج (`HISTORY_DAYS` يومًا تقويميًّا)."""
    sub = df.iloc[:e + 1]
    start = pd.Timestamp(sub.index[-1]) - pd.Timedelta(days=int(days))
    return sub[pd.DatetimeIndex(sub.index) >= start]


def ladder_and_ft(df, e: int, E: float, S) -> tuple:
    """`S.resistance_levels` و`S.first_target` **كما هما في الإنتاج** على الإطار المقصوص ⟵ (المستويات فوق E · منشأُ الشمعة) · التعذّرُ None."""
    sub = ladder_frame(df, e, int(S.CONFIG["HISTORY_DAYS"]))
    try:
        lv = [float(x) for x in S.resistance_levels(sub, float(E))]
    except Exception:                                                      # noqa: BLE001
        lv = None
    try:
        ft = float(S.first_target(sub))
    except Exception:                                                      # noqa: BLE001
        ft = None
    return lv, ft


def stored_events(row) -> tuple:
    """أحداثُ T-C المخزَّنة (`T-HS-FX`) ⟵ (cls_I1 · cls_I2 · t_tgt · t_stop_I2 · t_stop_I1)."""
    return (row.get("cls_I1_60") or None, row.get("cls_I2_60") or None, _i(row.get("t_tgt_60")),
            _i(row.get("t_stop_I2_60")), _i(row.get("t_stop_I1_60")))


def fx_events(h, c, e: int, tc, i1, i2) -> tuple | None:
    """أحداثُ T-C كما حسبها `T-HS-FX` (بلا قاعدة «الهدف ‏≤E») ⟵ الصيغةُ نفسُها لـ`stored_events` · نافذةٌ ناقصة ⟵ None."""
    a = FX.event_bars(h, c, e, tc, i1, 60)
    b = FX.event_bars(h, c, e, tc, i2, 60)
    if a is None or b is None:
        return None
    return (FX.classify(*a), FX.classify(*b), b[0], b[1], a[1])


def locate_e(dates: list, h, c, row) -> tuple:
    """بارُ الدخول ⟵ (e · السبب). B/C: بارُ التاريخ المخزَّن وإغلاقُه = E ضمن `ALIGN_TOL` · D: أوّلُ بارٍ بعد الاختراق إغلاقُه = E
    (`D_MATCH_TOL`) **وأحداثُ T-C منه تساوي المخزَّن** (§⑧ · الإغلاقُ وحدَه قد يتكرّر في أسهم السنتات) · وإلّا (None · السبب)."""
    d, E = str(row.get("date", ""))[:10], _f(row.get("entry"))
    if E is None or E <= 0:
        return None, "bad_entry"
    try:
        b = dates.index(d)
    except ValueError:
        return None, "no_date"
    kind = row.get("entry_kind")
    if kind in ("B", "C"):
        return (b, "ok") if abs(float(c[b]) / E - 1.0) <= ALIGN_TOL else (None, "misaligned")
    want = stored_events(row)
    tc, i1, i2 = _f(row.get("target")), _f(row.get("stop_I1")), _f(row.get("stop_I2"))
    for i in range(b + 1, len(c)):
        if abs(float(c[i]) / E - 1.0) > D_MATCH_TOL:
            continue
        got = fx_events(h, c, i, tc, i1, i2)
        if (got == want) if want[0] is not None else (got is None):    # نافذةٌ ناقصةٌ مخزَّنة ⟵ ناقصةٌ هنا أيضًا
            return i, "ok"
    return None, "d_not_found"


def wilson(k: int, n: int, z: float = 1.959964) -> tuple:
    if not n:
        return (None, None)
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    hw = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (mid - hw, mid + hw)


def _q(vals, q):
    v = sorted(x for x in vals if x is not None)
    return float(np.percentile(v, q)) if v else None


def summarize(cells: list) -> dict:
    """خليّةُ (هدف × إبطال × نافذة): العدُّ لكلّ فئة · المكتملُ = HIT ‏+ AFTER ‏+ INVF ‏+ MISS · المعدّلان بفواصل Wilson ·
    زمنُ الهدف (HIT وحدَها · وAFTER منفصلًا) · MFE (الوسيط · وMFE ÷ المسافة لـMISS)."""
    cnt = {k: 0 for k in CLASSES}
    for x in cells:
        cnt[x["cls"]] += 1
    n = cnt[HIT] + cnt[AFTER] + cnt[INVF] + cnt[MISS]
    any_k = cnt[HIT] + cnt[AFTER]
    t_hit = [x.get("t_tgt") for x in cells if x["cls"] == HIT]
    t_aft = [x.get("t_tgt") for x in cells if x["cls"] == AFTER]
    mfe = [x.get("mfe") for x in cells if x["cls"] in (HIT, AFTER, INVF, MISS)]
    reach = [x.get("reach") for x in cells if x["cls"] == MISS]
    dist = [x.get("dist") for x in cells if x["cls"] in (HIT, AFTER, INVF, MISS)]
    return {"counts": cnt, "n_complete": n,
            "hit_any": (any_k / n if n else None), "hit_any_ci": wilson(any_k, n),
            "hit_before_inv": (cnt[HIT] / n if n else None), "hit_before_inv_ci": wilson(cnt[HIT], n),
            "after_inv_share": (cnt[AFTER] / n if n else None),
            "t_hit_med": _q(t_hit, 50), "t_hit_p25": _q(t_hit, 25), "t_hit_p75": _q(t_hit, 75),
            "t_after_med": _q(t_aft, 50), "mfe_med": _q(mfe, 50), "reach_miss_med": _q(reach, 50),
            "dist_med": _q(dist, 50), "dist_p25": _q(dist, 25), "dist_p75": _q(dist, 75)}


def signal_cells(h, l, c, e: int, E: float, tg: dict, stops: dict) -> dict:
    """لكلّ (هدف × إبطال × نافذة): الفئة · زمنُ الهدف والإبطال · MFE · ومسافةُ الهدف ونسبةُ ما بلغه (MFE ÷ المسافة)."""
    out = {}
    for w in WINS:
        mfe, _mae = FX.excursion(h, l, e, E, w)
        for tk in TARGETS:
            t = tg.get(tk)
            dist = (t / E - 1.0) if (t is not None and E > 0) else None
            for sk in STOPS:
                o = outcome(h, c, e, E, t, stops.get(sk), w)
                o["mfe"] = mfe
                o["dist"] = dist
                o["reach"] = (mfe / dist) if (mfe is not None and dist and dist > 0) else None
                out[f"{tk}|{sk}|{w}"] = o
    return out


def seen_cases(paths=SEEN_FILES) -> list:
    """(رمز · تاريخ اختراق) لكلّ حالةٍ رُئيت سابقًا (التدقيقان الأعميان والإعادةُ البصريّة) — الغائبُ يُتخطّى."""
    out = []
    for p in paths:
        try:
            d = json.load(open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        rows = d.get("rows") if isinstance(d, dict) else d
        for r in rows or []:
            if r.get("sym") and r.get("b_date"):
                out.append((str(r["sym"]), str(r["b_date"])[:10]))
    return out


def near_seen(sym: str, d: str, seen: list, days: int = EXCL_DAYS) -> bool:
    try:
        t = dt.date.fromisoformat(str(d)[:10])
    except ValueError:
        return True
    for s, sd in seen:
        if s != sym:
            continue
        try:
            if abs((dt.date.fromisoformat(sd) - t).days) <= days:
                return True
        except ValueError:
            continue
    return False


def prefilter(rows: list, seen: list) -> list:
    """§⑦ ما لا يحتاج شموعًا: C · صالح · حقبةٌ من الأربع · غيرُ 2022 · غيرُ DXST · بعيدٌ عن كلّ ما رُئي."""
    out = []
    for r in rows:
        if r.get("entry_kind") != "C" or str(r.get("data_valid")) != "True" or r.get("era") not in ERAS_OK:
            continue
        if str(r.get("date", ""))[:4] == SAMPLE_YEAR_OUT or r.get("ticker") == DXST["sym"]:
            continue
        if near_seen(r["ticker"], r["date"], seen):
            continue
        out.append(r)
    return out


def draw_sample(keys: list, n: int = SAMPLE_N, seed: int = SAMPLE_SEED) -> list:
    keys = sorted(set(keys))
    return random.Random(seed).sample(keys, min(n, len(keys)))


def neck_points(row, dates: list, e_b: int) -> tuple | None:
    """العنقُ المخزَّن خطٌّ مستقيم ⟵ نقطتاه: (بارُ الرأس · قاعُ الرأس ‏+ الارتفاع) و(بارُ الاختراق · العنقُ عنده) · الارتفاع = T-C − العنق."""
    parts = str(row.get("pid", "")).split("|")
    nb, tc, hl = _f(row.get("neckline")), _f(row.get("target")), _f(row.get("stop_I1"))
    if len(parts) < 5 or None in (nb, tc, hl):
        return None
    try:
        hi = dates.index(parts[4])
    except ValueError:
        return None
    return (hi, hl + (tc - nb)), (e_b, nb)


def chart_payload(df, e: int, row, ladder, bars: int = CHART_BARS) -> dict:
    """شارتُ الوسم (§⑦): **حتى بار الدخول وحدَه** · بلا رمزٍ ولا تواريخ · فهارسُ نسبيّة · علاماتُ LS/H/RS · العنق · TC · L1…L5 · I1 · I2."""
    lo = max(0, e - bars + 1)
    sub = df.iloc[lo:e + 1]
    dates = [str(x)[:10] for x in df.index]
    o, h, l, c = (sub[k].to_numpy(float) for k in ("Open", "High", "Low", "Close"))
    parts = str(row.get("pid", "")).split("|")
    marks = {}
    for k, d in (("LS", parts[3] if len(parts) > 3 else None), ("H", parts[4] if len(parts) > 4 else None)):
        if d in dates and dates.index(d) >= lo:
            marks[k] = dates.index(d) - lo
    rs_px, hpos = _f(row.get("stop_I2")), marks.get("H")
    if rs_px is not None and hpos is not None:
        for i in range(hpos + 1, len(l)):
            if abs(l[i] / rs_px - 1.0) <= 1e-9:
                marks["RS"] = i
                break
    np_ = neck_points(row, dates, e)
    neck = None if np_ is None else [[np_[0][0] - lo, np_[0][1]], [np_[1][0] - lo, np_[1][1]]]
    lines = {"TC": _f(row.get("target")), "I1": _f(row.get("stop_I1")), "I2": _f(row.get("stop_I2"))}
    for j, v in enumerate((ladder or [])[:LADDER_SHOW]):
        lines[f"L{j + 1}"] = float(v)
    return {"bars": [[round(float(a), 6), round(float(b), 6), round(float(x), 6), round(float(y), 6)]
                     for a, b, x, y in zip(o, h, l, c)],
            "marks": marks, "neck": neck, "lines": lines, "E": _f(row.get("entry")), "decision": len(sub) - 1}


def seal(obj) -> tuple:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")
    blob = base64.b64encode(zlib.compress(raw, 9)).decode("ascii")
    return blob, hashlib.sha256(blob.encode("ascii")).hexdigest()


def unseal(blob: str):
    return json.loads(zlib.decompress(base64.b64decode(blob.encode("ascii"))).decode("utf-8"))


def target_label(tc, f_raw) -> str:
    """§⑦ مشتقٌّ آليًّا من وسم F: «AMBIGUOUS» ⟵ AMBIGUOUS · «NONE» أو غائب ⟵ OPEN_SPACE · وإلّا MATCH (‏≤3%) · BEYOND (F أدنى من TC
    بأكثرَ من 3%: مقاومةٌ مرئيّةٌ قبل TC) · SHORT (F أعلى) · وTC غائب ⟵ AMBIGUOUS."""
    if str(f_raw).strip().upper() == "AMBIGUOUS":
        return "AMBIGUOUS"
    f = _f(f_raw)
    if f is None:
        return "OPEN_SPACE"
    if tc is None or not tc > 0 or not f > 0:
        return "AMBIGUOUS"
    r = float(tc) / float(f) - 1.0
    if abs(r) <= LABEL_TOL:
        return "MATCH"
    return "BEYOND" if float(f) < float(tc) else "SHORT"


def f_rule_ok(f_raw, E: float, neck) -> bool | None:
    """§⑦ قاعدةُ F المكتوبة قبل الوسم: ‏≥3% فوق E وخارج ‏±2% من العنق ⟵ True/False · و«NONE»/«AMBIGUOUS» ⟵ None (لا تُفحص)."""
    f = _f(f_raw)
    if f is None:
        return None
    if not f >= float(E) * (1.0 + F_MIN_GAP):
        return False
    return not (neck is not None and abs(f / float(neck) - 1.0) <= F_NECK_BAND)


def first_idx(seq, start: int, pred) -> int | None:
    for i in range(max(0, start), len(seq)):
        if pred(i):
            return i
    return None


def nearest_ohlc(df, t0: int, level: float, bars: int = DXST_PROV_BARS) -> dict | None:
    """§⑥ منشأُ المستوى: أقربُ O/H/L/C في `bars` جلسةً قبل t0 ⟵ {date · field · value · diff}."""
    best = None
    for i in range(max(0, t0 - bars), t0):
        for k in ("Open", "High", "Low", "Close"):
            v = float(df[k].iloc[i])
            if v > 0:
                d = v / level - 1.0
                if best is None or abs(d) < abs(best["diff"]):
                    best = {"date": str(df.index[i])[:10], "field": k, "value": v, "diff": d}
    return best


def dxst_classify(trig: int | None, inv: int | None, touch: int | None) -> str:
    """§⑥ فئةُ مستوى DXST: إبطالٌ في بار الزناد أو قبله ⟵ INVALIDATED_BEFORE_TRIGGER · بلا زناد ⟵ NO_TRIGGER · وإلّا الفئاتُ الأربع
    (النافذةُ حتى آخر جلسةٍ مكتملة · والتعادلُ إبطالٌ أوّلًا)."""
    if trig is None:
        return "NO_TRIGGER"
    if inv is not None and inv <= trig:
        return "INVALIDATED_BEFORE_TRIGGER"
    t_t = touch if (touch is not None and touch > trig) else None
    t_s = inv
    if t_t is not None and (t_s is None or t_t < t_s):
        return HIT
    if t_t is not None:
        return AFTER
    if t_s is not None:
        return INVF
    return MISS


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# ② الجلب والتشغيل (شبكة · Actions)
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
def read_signals(path: str = SIG_FILE) -> list:
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def fetch_daily(syms):
    """شموعُ TradingView اليوميّة من 2016 (جلساتٌ مكتملة) — مسارُ `T-HS-FX` نفسُه بلا تقسيمات ياهو (لا سعرَ خامًّا هنا)."""
    import Super_stock as S
    import head_shoulders as HS
    frames, rep = S.tv_download(sorted(set(syms)), START)
    frames = HS._completed_all(frames, rep)
    log(S._tv_bars_line(rep))
    return frames, rep


def _arr(df):
    return ([str(x)[:10] for x in df.index], df["Open"].to_numpy(float), df["High"].to_numpy(float),
            df["Low"].to_numpy(float), df["Close"].to_numpy(float))


def _save(files: list):
    import Super_stock as S
    if os.environ.get("TGT_SAVE", "1") == "1":
        S.git_save(files)


def run_dxst() -> dict:
    """§⑥ حالةُ فيصل نفسِه — الشموعُ اليوميّة ‏+ شموعُ 15 دقيقة ⟵ الزنادان · الإبطالان · لمسُ المستويات · المنشأ · السلّم · وكاشفُ النظام."""
    import Super_stock as S
    import tv_data as TV
    frames, rep = fetch_daily([DXST["sym"]])
    df = frames.get(DXST["sym"])
    out = {"tool": TOOL, "case": "DXST", "source": "IMG_0627 · IMG_0628", "levels": DXST, "fetch": {"tv": rep.get("tv")}}
    if df is None or not len(df):
        out["error"] = "no_daily_bars"
        return out
    dates, o, h, l, c = _arr(df)
    t0 = first_idx(dates, 0, lambda i: dates[i] >= DXST["tweet"])
    if t0 is None:
        out["error"] = "no_bars_after_tweet"
        return out
    nk = DXST["neck"]
    ev = {"high_above_neck": first_idx(h, t0, lambda i: h[i] > nk), "close_above_neck": first_idx(c, t0, lambda i: c[i] > nk),
          "close_below_s1": first_idx(c, t0, lambda i: c[i] < DXST["s1"]),
          "close_below_s2": first_idx(c, t0, lambda i: c[i] < DXST["s2"])}
    lo_i = t0 + int(np.argmin(l[t0:]))
    out["daily"] = {k: (None if v is None else {"date": dates[v], "i": v}) for k, v in ev.items()}
    out["low_after"] = {"date": dates[lo_i], "low": float(l[lo_i])}
    # شموعُ 15 دقيقة (الجلسةُ النظاميّة) ⟵ أوّلُ شمعةٍ كاملةٍ فوق العنق (أدناها فوقه) بعد بداية 06-16
    m15 = None
    try:
        full = S._tv_full_name(DXST["sym"], S._tv_ticker_map(None))
        bars = TV.Chart().bars(full, "15", n=int(S.TV_BARS_MAX), extended=False)
    except Exception as e:                                                 # noqa: BLE001
        bars, out["m15_error"] = None, f"{type(e).__name__}: {e}"
    if bars:
        rows = [(TV.ny_time(int(b[0])), float(b[3])) for b in bars]
        rows = [(t, lo) for t, lo in rows if t.strftime("%Y-%m-%d") >= DXST["tweet"]]
        first_ok = next(((t, lo) for t, lo in rows if lo > nk), None)
        m15 = {"bars": len(bars), "first_bar": TV.ny_time(int(bars[0][0])).isoformat(), "since_tweet": len(rows),
               "first_full_15m_above_neck": (None if first_ok is None else first_ok[0].isoformat())}
        if first_ok is not None:
            dd = first_ok[0].strftime("%Y-%m-%d")
            m15["trigger_i"] = dates.index(dd) if dd in dates else None
    out["m15"] = m15
    inv = {"S1": ev["close_below_s1"], "S2": ev["close_below_s2"]}
    trig = {"daily_close": ev["close_above_neck"], "m15": (m15 or {}).get("trigger_i")}
    lvls = dict(DXST["levels"])
    res = {}
    for tname, ti in trig.items():
        if ti is not None:
            lvls_t = dict(lvls, **{f"2xE({tname})": 2.0 * float(c[ti])})
        else:
            lvls_t = dict(lvls)
        for lname, lv in lvls_t.items():
            touch = first_idx(h, (t0 if ti is None else ti + 1), lambda i, lv=lv: h[i] >= lv)
            for sname, si in inv.items():
                res[f"{tname}|{lname}|{sname}"] = {
                    "cls": dxst_classify(ti, si, touch), "trigger": (None if ti is None else dates[ti]),
                    "touch": (None if touch is None else dates[touch]),
                    "touch_any_after_tweet": (lambda j: None if j is None else dates[j])(
                        first_idx(h, t0, lambda i, lv=lv: h[i] >= lv)),
                    "inv": (None if si is None else dates[si]),
                    "sessions_trigger_to_touch": (None if (ti is None or touch is None) else int(touch - ti))}
    out["classes"] = res
    out["provenance"] = {f"{v}": nearest_ohlc(df, t0, v) for v in DXST["drawn"]}
    for k, v in out["provenance"].items():
        if v is not None:
            v["match"] = abs(v["diff"]) <= DXST_PROV_TOL
    pre = t0 - 1 if dates[t0] > DXST["tweet"] else t0
    lv, ft = ladder_and_ft(df, pre, float(c[pre]), S)
    out["ladder"] = {"asof": dates[pre], "price": float(c[pre]), "levels": lv, "first_target": ft,
                     "match": {str(x): (None if not lv else min(lv, key=lambda y, x=x: abs(y / x - 1.0))) for x in (3.114, 3.302, 3.610)}}
    for k, v in list(out["ladder"]["match"].items()):
        if v is not None:
            out["ladder"]["match"][k] = {"level": v, "diff": v / float(k) - 1.0, "within": abs(v / float(k) - 1.0) <= DXST_LADDER_TOL}
    out["detector_rows"] = [{k: r.get(k) for k in ("date", "entry_kind", "pid", "entry", "neckline", "target", "stop_I1", "stop_I2", "retest")}
                            for r in read_signals() if r.get("ticker") == DXST["sym"]]
    k0 = first_idx(dates, 0, lambda i: dates[i] >= "2026-03-01") or 0
    out["bars"] = [[dates[i], float(o[i]), float(h[i]), float(l[i]), float(c[i])] for i in range(k0, len(dates))]
    out["last_session"] = dates[-1]
    return out


def run_sample() -> int:
    """§⑤-1 · §⑥ · §⑦: DXST ‏+ العيّنة العمياء (بلا أيّ إحصاءٍ للمجتمع) ⟵ الشارتات والمفتاحُ المختوم."""
    import Super_stock as S
    os.makedirs(OUT_DIR, exist_ok=True)
    dx = run_dxst()
    with open(DXST_FILE, "w", encoding="utf-8") as fh:
        json.dump(dx, fh, ensure_ascii=False, indent=1)
    files = [DXST_FILE]
    log(f"📌 DXST: {json.dumps({k: dx.get(k) for k in ('daily', 'low_after', 'm15')}, ensure_ascii=False)}")
    if os.path.exists(CHARTS_FILE):
        log("🔒 العيّنةُ العمياء مصدَّرةٌ سلفًا — لا تُعاد (§⑦: سحبٌ واحد)")
        _save(files)
        return 0
    rows = read_signals()
    pre = prefilter(rows, seen_cases())
    frames, rep = fetch_daily({r["ticker"] for r in pre})
    elig, why = [], {}
    cache = {}
    for r in pre:
        df = frames.get(r["ticker"])
        if df is None:
            why["no_bars"] = why.get("no_bars", 0) + 1
            continue
        A = cache.get(r["ticker"]) or _arr(df)
        cache[r["ticker"]] = A
        dates, _o, h, _l, c = A
        e, st = locate_e(dates, h, c, r)
        if e is None:
            why[st] = why.get(st, 0) + 1
            continue
        if e + max(WINS) >= len(c):
            why["open_window"] = why.get("open_window", 0) + 1
            continue
        elig.append((f"{r['pid']}|{r['date']}", r, e))
    log(f"🧮 إطارُ العيّنة: قبل الشموع {len(pre)} ⟵ مؤهَّل {len(elig)} · مُستبعَد {why}")
    pick = set(draw_sample([k for k, _r, _e in elig]))
    chosen = sorted([(k, r, e) for k, r, e in elig if k in pick], key=lambda t: t[0])
    ids = [f"TG{j + 1:02d}" for j in range(len(chosen))]
    random.Random(MIX_SEED).shuffle(ids)
    charts, key = {}, {}
    for (k, r, e), tid in zip(chosen, ids):
        df = frames[r["ticker"]]
        dates, o, h, l, c = cache[r["ticker"]]
        E = float(r["entry"])
        lv, ft = ladder_and_ft(df, e, E, S)
        tg = target_prices(r.get("target"), E, r.get("stop_I1"), lv, ft)
        stops = {"I1": _f(r.get("stop_I1")), "I2": _f(r.get("stop_I2"))}
        charts[tid] = chart_payload(df, e, r, lv)
        fut = [[dates[i], float(o[i]), float(h[i]), float(l[i]), float(c[i])] for i in range(e + 1, min(len(c), e + max(WINS) + 1))]
        key[tid] = {"sym": r["ticker"], "pid": r["pid"], "b_date": r["date"], "e_date": dates[e], "E": E, "targets": tg,
                    "stops": stops, "neckline": _f(r.get("neckline")), "future": fut,
                    "cells": signal_cells(h, l, c, e, E, tg, stops)}
    blob, sha = seal(key)
    meta = {"tool": TOOL, "seed": SAMPLE_SEED, "mix_seed": MIX_SEED, "frame_pre": len(pre), "frame": len(elig), "excluded": why,
            "n": len(charts), "key_sha256": sha, "generated": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"}
    with open(CHARTS_FILE, "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "charts": charts}, fh, ensure_ascii=False)
    with open(KEY_FILE, "w", encoding="ascii") as fh:
        fh.write(blob)
    log(f"🔐 المفتاحُ مختوم: sha256 {sha} · {len(charts)} شارتًا")
    files += [CHARTS_FILE, KEY_FILE]
    _save(files)
    return 0


def run_pop() -> int:
    """§⑤-3 · §⑧ · §⑨: المجتمع **بعد دفع الوسوم وحدَه** ⟵ بوّابةُ إعادة الإنتاج ثمّ الشبكة كلُّها."""
    import Super_stock as S
    if not os.path.exists(LABELS_FILE):
        log("⛔ pop قبل دفع الوسوم ممنوع (§⑤) — ادفع tf_blind_labels.json أوّلًا")
        return 3
    rows = [r for r in read_signals() if r.get("entry_kind") in ENTRIES and str(r.get("data_valid")) == "True"
            and r.get("era") in ERAS_OK]
    frames, rep = fetch_daily({r["ticker"] for r in rows})
    syms = {r["ticker"] for r in rows}
    recs, why, rep_ok, rep_n, align = [], {}, 0, 0, {"BC": 0, "BC_n": 0}
    cache = {}
    for r in rows:
        df = frames.get(r["ticker"])
        if r["entry_kind"] in ("B", "C"):
            align["BC_n"] += 1
        if df is None:
            why["no_bars"] = why.get("no_bars", 0) + 1
            continue
        A = cache.get(r["ticker"]) or _arr(df)
        cache[r["ticker"]] = A
        dates, _o, h, l, c = A
        e, st = locate_e(dates, h, c, r)
        if e is None:
            why[st] = why.get(st, 0) + 1
            continue
        E = float(r["entry"])
        if r["entry_kind"] in ("B", "C"):
            align["BC"] += 1
            want = stored_events(r)
            if all(x is not None for x in want[:2]):
                got = fx_events(h, c, e, _f(r.get("target")), _f(r.get("stop_I1")), _f(r.get("stop_I2")))
                rep_n += 1
                rep_ok += int(got == want)
        lv, ft = ladder_and_ft(df, e, E, S)
        tg = target_prices(r.get("target"), E, r.get("stop_I1"), lv, ft)
        stops = {"I1": _f(r.get("stop_I1")), "I2": _f(r.get("stop_I2"))}
        recs.append({"sym": r["ticker"], "pid": r["pid"], "date": r["date"], "entry": r["entry_kind"], "era": r["era"], "E": E,
                     "targets": tg, "cells": signal_cells(h, l, c, e, E, tg, stops)})
    a_rate = align["BC"] / align["BC_n"] if align["BC_n"] else 0.0
    r_rate = rep_ok / rep_n if rep_n else 0.0
    gate = {"align_rate": a_rate, "align_ok": a_rate >= ALIGN_MIN, "repro_rate": r_rate, "repro_n": rep_n,
            "repro_ok": r_rate >= REPRO_MIN, "coverage_syms": (len([s for s in syms if s in frames]) / len(syms) if syms else 0.0)}
    gate["pass"] = bool(gate["align_ok"] and gate["repro_ok"])
    log(f"🧪 بوّابةُ إعادة الإنتاج: {json.dumps(gate, ensure_ascii=False)} · مستبعَد {why}")
    grid = {}
    for ent in ENTRIES:
        for era in ERAS_OK + ("ALL",):
            sub = [x for x in recs if x["entry"] == ent and (era == "ALL" or x["era"] == era)]
            for key in (f"{tk}|{sk}|{w}" for tk in TARGETS for sk in STOPS for w in WINS):
                grid[f"{ent}|{era}|{key}"] = summarize([x["cells"][key] for x in sub])
    out = {"tool": TOOL, "mode": "pop", "generated": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", "gate": gate,
           "excluded": why, "n": len(recs), "grid": grid, "fetch": {"tv": rep.get("tv"), "asked": rep.get("asked")},
           "label": ("" if gate["pass"] else "غيرُ مطابق — لا يُقرأ (§⑨)")}
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(POP_FILE, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False)
    with open(POP_CSV, "w", encoding="utf-8", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["sym", "pid", "date", "entry", "era", "E"] + [f"tgt_{t}" for t in TARGETS]
                    + [f"{t}|{s}|{w}" for t in TARGETS for s in STOPS for w in WINS])
        for x in recs:
            wr.writerow([x["sym"], x["pid"], x["date"], x["entry"], x["era"], x["E"]] + [x["targets"].get(t) for t in TARGETS]
                        + [x["cells"][f"{t}|{s}|{w}"]["cls"] for t in TARGETS for s in STOPS for w in WINS])
    for ent in ENTRIES:
        for sk in STOPS:
            for w in (60, 90):
                parts = []
                for tk in TARGETS:
                    g = grid[f"{ent}|ALL|{tk}|{sk}|{w}"]
                    hb = g["hit_before_inv"]
                    parts.append(f"{tk} {('—' if hb is None else f'{hb:.1%}')}")
                log(f"   {ent} · {sk} · {w}: " + " · ".join(parts))
    _save([POP_FILE, POP_CSV])
    return 0


def run_open() -> int:
    """§⑦ بعد الفتح (محلّيّ · بلا شبكة): الوسومُ مدفوعة ⟵ المفتاحُ يطابق بصمتَه ⟵ فئاتُ F وجداولُ PATTERN وTARGET كلٌّ وحدَه."""
    if not os.path.exists(LABELS_FILE):
        log("⛔ لا وسوم — لا فتح (§⑦)")
        return 3
    labels = json.load(open(LABELS_FILE, encoding="utf-8"))
    meta = json.load(open(CHARTS_FILE, encoding="utf-8"))["meta"]
    blob = open(KEY_FILE, encoding="ascii").read()
    if hashlib.sha256(blob.encode("ascii")).hexdigest() != meta["key_sha256"]:
        log("⛔ بصمةُ المفتاح لا تطابق المسجَّلة")
        return 4
    key = unseal(blob)
    rows = []
    for tid in sorted(key):
        k, lb = key[tid], (labels.get("labels") or {}).get(tid) or {}
        fut = k["future"]
        E = float(k["E"])
        h = np.array([E] + [x[2] for x in fut], float)
        lo_ = np.array([E] + [x[3] for x in fut], float)
        c = np.array([E] + [x[4] for x in fut], float)
        f_raw = lb.get("F")
        f = _f(f_raw)
        tg = dict(k["targets"], F=f)
        cells = {}
        for w in (60, 90):
            mfe, _m = FX.excursion(h, lo_, 0, E, w)
            for tk in ("TC", "F", "TR1", "T30E", "T100E", "T100L"):
                for sk in STOPS:
                    o = outcome(h, c, 0, E, tg.get(tk), k["stops"].get(sk), w)
                    o["mfe"], t = mfe, tg.get(tk)
                    o["dist"] = (t / E - 1.0) if t else None
                    o["reach"] = (mfe / o["dist"]) if (mfe is not None and o["dist"] and o["dist"] > 0) else None
                    if o.get("t_tgt") is not None:
                        o["date_tgt"] = fut[o["t_tgt"] - 1][0]
                    cells[f"{tk}|{sk}|{w}"] = o
        rows.append({"id": tid, "sym": k["sym"], "b_date": k["b_date"], "e_date": k["e_date"], "E": E, "pid": k["pid"],
                     "neckline": k["neckline"], "targets": tg, "stops": k["stops"], "pattern": lb.get("pattern"),
                     "neckline_label": lb.get("neckline"), "F": f_raw, "F_rule_ok": f_rule_ok(f_raw, E, k["neckline"]),
                     "target_label": target_label(_f(k["targets"].get("TC")), f_raw),
                     "why": lb.get("why"), "cells": cells})
    tabs = {}
    for dim in ("pattern", "target_label"):
        for val in sorted({str(r[dim]) for r in rows}):
            sub = [r for r in rows if str(r[dim]) == val]
            for key2 in (f"{tk}|{sk}|{w}" for tk in ("TC", "F", "TR1", "T30E", "T100E", "T100L") for sk in STOPS for w in (60, 90)):
                tabs[f"{dim}={val}|{key2}"] = summarize([r["cells"][key2] for r in sub])
    out = {"tool": TOOL, "key_sha256": meta["key_sha256"], "n": len(rows), "rows": rows, "tables": tabs}
    with open(RESULT_FILE, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    log(f"🔓 فُتح المفتاح: {len(rows)} حالة ⟵ {RESULT_FILE}")
    return 0


def main() -> int:
    mode = os.environ.get("TGT_MODE", "sample").strip()
    log(f"🎯 {TOOL} · الوضع {mode} · قراءةٌ فقط (لا كاشف · لا تلغرام · لا حالةَ إنتاج)")
    if mode == "sample":
        return run_sample()
    if mode == "pop":
        return run_pop()
    if mode == "open":
        return run_open()
    log(f"⛔ وضعٌ مجهول: {mode}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
