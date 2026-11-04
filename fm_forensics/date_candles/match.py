# -*- coding: utf-8 -*-
"""🕯️📅 مطابقةُ بطاقة الشموع على تاريخ رمزها (`T_DATE_CANDLES_ADDENDUM_2.md §④`) — قراءةٌ فقط · بلا تلغرام · بلا أسرار.

البطاقةُ (`auto_card.build_card`: شموعٌ بالسعر كما ظهر يومَ اللقطة · والمفقودُ `None`) ⟵ شموعُ TradingView لرمزها بفريمها
(مسوّاةٌ بالتقسيم حتى اليوم) ⟵ **كلُّ نافذةٍ بطول البطاقة** تُطابَق باللوغاريتم على الحاضر وحدَه (`masked_fit`: `k` حرّ ⟵ الشكل) ⟵
**قيدان مستقلّان** كما في `chart_finder.verdict` (بُنيت لتعريف رمز الشارت · وتُستعمل هنا لتاريخه بقيدَين لا بقيود النصّ):
  ① **الشكل:** جذرُ متوسّط مربّعات البواقي لا يتجاوز تسامحَ البطاقة نفسِها (بكسلان لكلّ قيمة ‏+ هامشُ المصدر 0.5%).
  ② **المستوى:** `k` المقيس = **معاملُ التقسيم المسجَّل لتاريخ النافذة** (حاصلُ التقسيمات بعد آخر شمعة · ياهو ∪ تقويمُ ناسداك)
     ضمن هامش المصدر ‏+ تسامح البكسل — فالسعرُ على الشاشة خامٌ يومَ اللقطة والتاريخُ مسوًّى اليوم.
  ⟵ العابرون (①∧②) تُدمج نوافذُهم التي تنتهي على مسافة شمعةٍ واحدة ⟵ `verdict`: **واثق** = عابرٌ وحيد بقيدَين · **مرجّح** =
  عابرٌ وحيد بقيدٍ واحد (المستوى غيرُ قابلٍ للحساب) أو خطأُ الثاني 3 أضعاف الأوّل فأكثر · **غير محسوم** · **لا تطابق**.
والمتغيّراتُ (العقد §④-②): الشموعُ كما هي ‏+ متغيّرٌ لكلّ تقسيمٍ مسجَّل (ما قبله يُعاد إلى مقياسه الخامّ) — كلٌّ يُبحث وحدَه.

السطرُ لكلّ بطاقة: `DCR\t{json}` في السجلّ · ولا كتابةَ في المستودع (الحصادُ من السجلّ).
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

FEED_TOL = 0.005          # = `chart_finder.FEED_TOL_PCT` (0.5%) هامشُ اختلاف المصدر بين التطبيق وTradingView
DECISIVE_RATIO = 3.0      # = `chart_finder.DECISIVE_RATIO`
N_BARS = 5000             # أقصى شموعِ الطلب الواحد (حسابُ الزائر)
# الفريم ⟵ [(وسمُ المتغيّر، فاصلُ TradingView، ممتدّ؟، حدودُ تجميع a30 أو None)] · ومدّةُ الشمعة بالدقائق للدمج والإصابة
FRAMES = {
    "1D": [("1D", "1D", False, None)],
    "1W": [("1W", "1W", False, None)],
    "4H": [("240e", "240", True, None)] + [(f"a30#{i}", "30", True, i) for i in range(5)],
    "2H": [("120e", "120", True, None)],
    "1H": [("60e", "60", True, None)],
    "30m": [("30e", "30", True, None)],
}
BAR_MIN = {"1D": 24 * 60, "1W": 7 * 24 * 60, "4H": 240, "2H": 120, "1H": 60, "30m": 30}
LABELS = ("واثق", "مرجّح", "غير محسوم", "لا تطابق")


def card_arrays(card: dict):
    """البطاقة ⟵ (ref m×4 بالسعر · tol m×4 نسبيّ · mask m) — والمفقودُ صفوفٌ صفريّة مقنَّعة."""
    bars, tols = card["bars"], card["tol"]
    m = len(bars)
    ref = np.ones((m, 4))
    rel = np.zeros((m, 4))
    mask = np.zeros(m, dtype=bool)
    for i, (b, t) in enumerate(zip(bars, tols)):
        if not b:
            continue
        vals = [b[k] for k in ("o", "h", "l", "c")]
        if any((v is None) or not (v > 0) for v in vals):
            continue
        ref[i] = vals
        rel[i] = [t[k] / v + FEED_TOL for k, v in zip(("o", "h", "l", "c"), vals)]
        mask[i] = True
    return ref, rel, mask


def shape_tol(rel: np.ndarray, mask: np.ndarray) -> float:
    """تسامحُ الشكل = جذرُ متوسّط مربّعات log(1+تسامح كلِّ قيمة) على الحاضر."""
    r = np.log1p(rel[mask])
    return float(np.sqrt((r ** 2).mean())) if r.size else math.inf


def level_tol(rel: np.ndarray, mask: np.ndarray) -> float:
    """تسامحُ المستوى = log(1 + وسيطُ التسامح النسبيّ) — والوسيطُ يتضمّن هامشَ المصدر."""
    r = rel[mask]
    return float(np.log1p(np.median(r))) if r.size else math.inf


def masked_fit(ohlc: np.ndarray, ref: np.ndarray, mask: np.ndarray):
    """كلُّ نافذةٍ بطول البطاقة ⟵ (rms, logk) على الصفوف الحاضرة وحدَها · `k` = سعرُ المصدر ÷ سعرُ البطاقة."""
    m = len(ref)
    if len(ohlc) < m or mask.sum() == 0:
        return None
    lw = np.log(np.clip(ohlc, 1e-9, None))
    win = np.lib.stride_tricks.sliding_window_view(lw, (m, 4))[:, 0]          # (T, m, 4)
    d = (win - np.log(ref)[None, :, :])[:, mask, :]
    logk = d.mean(axis=(1, 2))
    res = d - logk[:, None, None]
    rms = np.sqrt((res ** 2).mean(axis=(1, 2)))
    return rms, logk


def split_factor(day: str, events: list) -> float:
    """معاملُ التسوية لتاريخ `day` = حاصلُ (1 ÷ النسبة) للتقسيمات **بعده** — `events` = [(YYYY-MM-DD، نسبة ياهو)]
    (العكسيُّ 1:10 نسبتُه 0.1 ⟵ ما قبله يُضرب في 10 في التاريخ المسوّى)."""
    f = 1.0
    for d, r in events:
        if d > day and r and r > 0:
            f *= 1.0 / r
    return f


def unadjust(bars: list, split_day: str, ratio: float, day_of) -> list:
    """متغيّرُ العقد §④-②: الشموعُ قبل `split_day` تُعاد إلى مقياسها الخامّ لذلك التقسيم (تُقسم على 1/النسبة)."""
    if not ratio or ratio <= 0:
        return bars
    out = []
    for b in bars:
        if day_of(b[0]) < split_day:
            out.append([b[0]] + [v * ratio for v in b[1:5]] + list(b[5:]))
        else:
            out.append(list(b))
    return out


def window_candidates(bars: list, ref, rel, mask, events, day_of, adjusted_out: str = None, mult: float = 1.0) -> list:
    """النوافذُ العابرة للشكل ⟵ [{i, end_ts, rms, k, k_exp, level_ok}] · و`events=None` ⟵ المستوى غيرُ قابلٍ للحساب.
    `adjusted_out` = تقسيمٌ أُعيد في هذا المتغيّر إلى مقياسه الخامّ فلا يدخل معاملَ النافذة · و`mult` مضاعفُ تسامح الشكل
    (الملحق 3 §⑥ · و1.0 = الملحق 2 بت-بت)."""
    good = [b for b in bars if all(isinstance(x, (int, float)) and x > 0 for x in b[1:5])]
    if len(good) < len(ref):
        return []
    ohlc = np.array([[b[1], b[2], b[3], b[4]] for b in good], dtype=float)
    fit = masked_fit(ohlc, ref, mask)
    if fit is None:
        return []
    rms, logk = fit
    st, lt = shape_tol(rel, mask), level_tol(rel, mask)
    m = len(ref)
    out = []
    for i in np.where(rms <= st * mult)[0]:
        i = int(i)
        end = good[i + m - 1][0]
        k = float(math.exp(logk[i]))
        if events is None:
            k_exp, ok = None, None
        else:
            ev = [e for e in events if e[0] != adjusted_out]
            k_exp = split_factor(day_of(end), ev)
            ok = abs(math.log(k) - math.log(k_exp)) <= lt
        out.append({"i": i, "end_ts": int(end), "rms": float(rms[i]), "k": k, "k_exp": k_exp, "level_ok": ok})
    return out


def merge(cands: list, bar_sec: int) -> list:
    """العابرون الذين تنتهي نوافذُهم على مسافة شمعةٍ واحدة (أو أقلّ) جوابٌ واحد ⟵ يُحفظ الأصغرُ خطأً · مرتَّبين بالخطأ."""
    out = []
    for c in sorted(cands, key=lambda c: (c["rms"], c["end_ts"])):
        if any(abs(c["end_ts"] - o["end_ts"]) <= bar_sec for o in out):
            continue
        out.append(c)
    return out


def verdict(passers: list, n_groups: int) -> tuple:
    """قاعدةُ `chart_finder.verdict` بحرفها على النوافذ: (الوسم، الأوّل، الثاني)."""
    if not passers:
        return "لا تطابق", None, None
    p = sorted(passers, key=lambda c: (c["rms"], c["end_ts"]))
    t1 = p[0]
    t2 = p[1] if len(p) > 1 else None
    if t2 is None:
        return ("واثق" if n_groups >= 2 else "مرجّح"), t1, None
    if t2["rms"] >= DECISIVE_RATIO * max(t1["rms"], 1e-9):
        return "مرجّح", t1, t2
    return "غير محسوم", t1, t2


def judge(card: dict, series: dict, events, day_of, stamp, mult: float = 1.0) -> dict:
    """البطاقة ‏+ {وسمُ المتغيّر: شموع} ‏+ التقسيمات ⟵ صفُّ النتيجة. `series` يحمل كلَّ متغيّرٍ للفريم (والتقسيمُ متغيّرٌ مستقلّ)."""
    ref, rel, mask = card_arrays(card)
    tf = card["frame"]
    bar_sec = BAR_MIN[tf] * 60
    shape_pass, n_groups = [], (2 if events is not None else 1)
    for lab, bars in series.items():
        adj = lab.split("|split:")[1] if "|split:" in lab else None
        for c in window_candidates(bars, ref, rel, mask, events, day_of, adjusted_out=adj, mult=mult):
            c["variant"] = lab
            shape_pass.append(c)
    passers = [c for c in shape_pass if c["level_ok"] is not False]
    merged = merge(passers, bar_sec)
    label, t1, t2 = verdict(merged, n_groups)
    row = {"id": card["id"], "symbol": card["symbol"], "frame": tf, "label": label, "n_groups": n_groups,
           "shape_pass": len(shape_pass), "passers": len(merged), "m": len(ref), "present": int(mask.sum()),
           "shape_tol": round(shape_tol(rel, mask), 5), "level_tol": round(level_tol(rel, mask), 5)}
    if mult != 1.0:
        row["mult"] = mult
    for nm, t in (("top1", t1), ("top2", t2)):
        if t:
            row[nm] = {"end": stamp(t["end_ts"], tf), "rms": round(t["rms"], 5), "k": round(t["k"], 4),
                       "k_exp": None if t["k_exp"] is None else round(t["k_exp"], 4), "variant": t["variant"]}
    if not merged and shape_pass:
        b = min(shape_pass, key=lambda c: c["rms"])
        row["best_shape"] = {"end": stamp(b["end_ts"], tf), "rms": round(b["rms"], 5), "k": round(b["k"], 4),
                             "k_exp": None if b["k_exp"] is None else round(b["k_exp"], 4), "variant": b["variant"]}
    return row


CALIB_R_MAX = 10.0        # أعلى مضاعفٍ في شبكة الملحق 3 §⑤ (ما فوقه لا يدخل المنحنى)
CALIB_SHOW = 10           # أصغرُ النوافذ الكاذبة تُطبع للفحص


def calib(card: dict, series: dict, events, day_of, stamp, truth: str) -> dict:
    """الملحق 3 §⑤: البحثُ في كلّ نوافذ تاريخ الرمز (كلُّ المتغيّرات) **بلا الحقيقة** ⟵ لكلّ نافذةٍ النسبةُ `r` = rms ÷ تسامحُ الشكل للبطاقة
    وقيدُ المستوى كما هو ⟵ **ثمّ** تُصنَّف النوافذُ بالحقيقة (`results.side_hit` بالاسم): `r_true` = أصغرُ `r` لنافذةٍ «تصيب» · `r_false` =
    أصغرُ `r` لكلّ نافذةٍ أخرى — مرّةً مع قيد المستوى (لا يرفضها) ومرّةً بلا قيده (وصف). وما فوق `CALIB_R_MAX` لا يُحسب (`None`)."""
    import results as RS                                           # noqa: PLC0415  (بُنيت للفحص الجانبيّ في الملحق 2)
    ref, rel, mask = card_arrays(card)
    tf = card["frame"]
    st, lt = shape_tol(rel, mask), level_tol(rel, mask)
    out = {"lv": {"true": None, "false": None}, "sh": {"true": None, "false": None}}
    fal = []
    n = 0
    for lab, bars in series.items():
        adj = lab.split("|split:")[1] if "|split:" in lab else None
        for c in window_candidates(bars, ref, rel, mask, events, day_of, adjusted_out=adj, mult=CALIB_R_MAX):
            n += 1
            r = c["rms"] / st if st > 0 else math.inf
            end = stamp(c["end_ts"], tf)
            hit = bool(RS.side_hit(tf, end, truth))
            key = "true" if hit else "false"
            for grp, ok in (("sh", True), ("lv", c["level_ok"] is not False)):
                if ok and (out[grp][key] is None or r < out[grp][key][0]):
                    out[grp][key] = (r, end, lab, c["level_ok"])
            if not hit and c["level_ok"] is not False:
                fal.append((r, end, lab))
    fal.sort()
    show, seen_end = [], set()
    for r, end, lab in fal:
        if end not in seen_end:
            seen_end.add(end)
            show.append([end, round(r, 4), lab])
        if len(show) >= CALIB_SHOW:
            break
    rnd = lambda t: None if t is None else [round(t[0], 4), t[1], t[2], t[3]]  # noqa: E731
    return {"id": card["id"], "symbol": card["symbol"], "frame": tf, "truth": truth,
            "n_groups": 2 if events is not None else 1, "shape_tol": round(st, 5), "level_tol": round(lt, 5),
            "m": len(ref), "present": int(mask.sum()), "windows_r_le_max": n,
            "lv_true": rnd(out["lv"]["true"]), "lv_false": rnd(out["lv"]["false"]),
            "sh_true": rnd(out["sh"]["true"]), "sh_false": rnd(out["sh"]["false"]), "false_top": show}


# ── التشغيل على الرنر ──────────────────────────────────────────────────────────────────────────────
def _events(sym: str):
    """التقسيماتُ المسجَّلة: ياهو ∪ تقويمُ ناسداك (`Super_stock._fetch_splits_dq` بالاسم · بُنيت لمسارات الحسم) ⟵ [(يوم، نسبة)]
    أو None عند التعذّر (فلا يُحسب المستوى ولا يُدّعى «واثق»)."""
    try:
        import Super_stock as S                                    # noqa: PLC0415
        sp = S._fetch_splits_dq(sym)
    except Exception:                                              # noqa: BLE001
        return None
    if sp is None:
        return None
    out = []
    try:
        items = sp.items() if hasattr(sp, "items") else sp
        for d, r in items:
            day = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)[:10]
            out.append((day, float(r)))
    except Exception:                                              # noqa: BLE001
        return None
    return sorted(out)


def main() -> int:
    import closed                                                  # noqa: PLC0415  🔒 الملحق 5 §⑤
    _rc = closed.gate("match")
    if _rc is not None:
        return _rc
    import chart_id_tv as CT                                       # noqa: PLC0415
    import tv_data as TV                                           # noqa: PLC0415
    path = os.environ.get("DC_CARDS", os.path.join(HERE, "data", "cards.jsonl"))
    mode = (os.environ.get("DC_MODE") or "match").strip()
    mult = float(os.environ.get("DC_TOL_MULT", "1") or 1)
    truth = json.loads(os.environ.get("DC_TRUTH") or "{}")       # الملحق 3 §⑤: {معرّف: الحقيقة} — للتصنيف بعد البحث وحدَه
    if mode == "calib" and not truth:                              # الافتراض: مجموعةُ المعايرة المجمَّدة (`v3.calib_set`)
        cs = json.load(open(os.path.join(HERE, "data", "calib_set.json"), encoding="utf-8"))
        truth = {x["file"]: x["truth"] for x in cs["set"]}
    batch = int(os.environ.get("DC_BATCH", "0") or 0)
    size = int(os.environ.get("DC_SIZE", "40") or 40)
    only = {x.strip() for x in (os.environ.get("DC_IDS") or "").split(",") if x.strip()}
    cards = [json.loads(ln) for ln in open(path, encoding="utf-8") if ln.strip()]
    cards = [c for c in cards if c.get("ok")]
    if mode == "calib" and not only:
        only = set(truth)
    if only:
        cards = [c for c in cards if c["id"] in only]
    else:
        cards = cards[batch * size:(batch + 1) * size]
    print(f"DCB\t{json.dumps({'batch': batch, 'size': size, 'n': len(cards)})}", flush=True)
    if not cards:
        return 0
    uni = CT.universe()
    tmap = TV.ticker_map(uni) if uni else {}
    anchors = CT.parse_anchors(CT.DEFAULT_ANCHORS)
    day_of = TV.ny_day

    def stamp(ts, tf):
        return TV.ny_time(ts).strftime("%Y-%m-%d") if tf in ("1D", "1W") else TV.ny_time(ts).strftime("%Y-%m-%d %H:%M")
    ch = TV.Chart()
    cache = {}
    for card in cards:
        sym = card["symbol"].upper()
        names = [tmap[sym]] if sym in tmap else [f"{x}:{sym}" for x in ("NASDAQ", "NYSE", "AMEX")]
        events = _events(sym)
        series, why = {}, None
        for lab, interval, ext, anc in FRAMES[card["frame"]]:
            key = (sym, interval, ext)
            if key not in cache:
                got = None
                for nm in names:
                    got = ch.bars(nm, interval=interval, n=N_BARS, extended=ext)
                    if got:
                        break
                cache[key] = got
            bars = cache[key]
            if not bars:
                why = "لا شموعَ من TradingView"
                continue
            if anc is not None:
                starts, end = anchors[anc]
                bars = CT.aggregate(bars, starts, end)
            series[lab] = bars
            for d, r in (events or []):
                series[f"{lab}|split:{d}"] = unadjust(bars, d, r, day_of)
        if mode == "calib":
            row = (calib(card, series, events, day_of, stamp, truth.get(card["id"], "")) if series
                   else {"id": card["id"], "why": why or "لا متغيّر"})
            print(f"DCC\t{json.dumps(row, ensure_ascii=False)}", flush=True)
            continue
        if not series:
            row = {"id": card["id"], "symbol": sym, "frame": card["frame"], "label": "لا تطابق", "why": why or "لا متغيّر"}
        else:
            row = judge(card, series, events, day_of, stamp, mult=mult)
            if mult != 1.0:                                        # الملحق 3 §⑥: «واثق» عند m = 1 بجوارها
                base = judge(card, series, events, day_of, stamp)
                row["at_m1"] = {"label": base["label"], "end": (base.get("top1") or {}).get("end")}
            first = min((b[0] for v in series.values() for b in v[:1]), default=None)
            row["history_from"] = stamp(first, card["frame"]) if first else None
            row["splits"] = events
        print(f"DCR\t{json.dumps(row, ensure_ascii=False)}", flush=True)
    print(f"DCE\t{json.dumps({'calls': TV.CALLS})}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
