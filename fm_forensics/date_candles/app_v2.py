#!/usr/bin/env python3
"""📱🕯️📅 T-DATE-CANDLES v2 (`T_DATE_CANDLES_ADDENDUM_6.md`) — قارئُ لقطات تطبيق فيصل ⟵ مطابقةٌ على التاريخ ⟵ الحكمُ على المحجوز.

الأوضاع (`DCV2_STAGE`):
- `split`   : القسمة (بلا شبكة) — تُطبع القائمتان.
- `cal`     : نصفُ المعايرة: بطاقة ⟵ مطابقة ⟵ إصابة لكلّ صورة ‏+ الملخّص (وصفٌ · ضُبط عليه).
- `holdout` : النصفُ المحجوز — **مرّةً واحدة** بعد التجميد: يخرج 9 ما لم تطابق `FROZEN_SHA` بصمةَ `app_card.py` (وفارغةٌ ⟵ 9).
- `corpus`  : المدوّنة كلّها (§⑦) — يخرج 9 ما لم يكن الحكمُ «يعبر» منشورًا (`PASSED = True`).
🔒 `closed.gate("app_v2")` أوّلًا ⟵ بلا `DATE_CANDLES_REOPEN=1` يخرج 8 · قراءةٌ فقط · لا كتابةَ في المستودع (السطورُ في السجلّ).
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (HERE, REPO):
    if _p not in sys.path:
        sys.path.insert(0, _p)

TABLE = os.path.join(HERE, "data", "header_dates.tsv")
APP_CARD = os.path.join(HERE, "app_card.py")
SALT = "T-DATE-CANDLES-V2|"
FROZEN_SHA = ""                # ⟵ بصمةُ app_card.py المجمَّد (تُكتب في PR التجميد قبل تشغيل المحجوز)
PASSED = False                 # ⟵ يصير True فقط في PR نتيجةٍ «يعبر» (§⑦)
BUILD_MIN, HIT_MIN = 0.70, 0.85   # §⑥ نصُّ المالك
# ── المطابقةُ على الملمح (معلماتٌ حرّة · تُضبط على المعايرة) ──────────────────────────────────────────────
N_MIN, N_MAX = 8, 300          # عددُ الشموع المرشَّح في عرض اللوحة
SLOT_MIN_PX = 2.0              # أضيقُ شمعةٍ مقبولة (بكسل)
SLOT_PRESENT = 0.60            # أدنى نسبةِ خاناتٍ حاضرة
PX_TOL = 2.0                   # تسامحُ القيمة بالبكسل (= `auto_card.CAL_TOL_PX`)
SHAPE_MULT = 3.0               # مضاعفُ تسامح الشكل (القسمةُ إلى خاناتٍ تُضيف خطأً لا يعرفه تسامحُ البكسل)
LEVEL_MULT = 3.0               # مضاعفُ تسامح المستوى


def truth_rows() -> list:
    return [r for r in csv.DictReader(open(TABLE, encoding="utf-8"), delimiter="\t") if r["conf"] == "واثق"]


def split(rows: list = None) -> tuple:
    """§③: المجموعة (الرمز، التاريخ، الساعة) ⟵ ترتيبٌ بـsha256 ⟵ أوّلُ ⌈n/2⌉ مجموعة معايرة · والباقي محجوز ⟵ (معايرة، محجوز) بأسماء الصور."""
    rows = truth_rows() if rows is None else rows
    g = {}
    for r in rows:
        g.setdefault((r["symbol"], r["date"], r["hour"]), []).append(r["file"])
    keys = sorted(g, key=lambda k: hashlib.sha256((SALT + "|".join(k)).encode()).hexdigest())
    half = (len(keys) + 1) // 2
    cal = sorted(f for k in keys[:half] for f in g[k])
    ho = sorted(f for k in keys[half:] for f in g[k])
    return cal, ho


def slots(card: dict, n: int):
    """الملمح ⟵ n خانة ⟵ (ref n×2 [قمّة، قاع] بالسعر، rel n×2 تسامحٌ نسبيّ، mask n)."""
    w = card["width"]
    s = w / float(n)
    hi = np.full(n, -np.inf)
    lo = np.full(n, np.inf)
    for x, tp, bp in card["profile"]:
        j = min(n - 1, int(x / s))
        hi[j] = max(hi[j], tp)
        lo[j] = min(lo[j], bp)
    mask = np.isfinite(hi) & np.isfinite(lo) & (lo > 0)
    ref = np.ones((n, 2))
    ref[mask, 0], ref[mask, 1] = hi[mask], lo[mask]
    px = card["px_price"] * PX_TOL
    rel = np.zeros((n, 2))
    rel[mask] = px / ref[mask] + 0.005                          # = `match.FEED_TOL`
    return ref, rel, mask


def fit_windows(hl: np.ndarray, ref: np.ndarray, mask: np.ndarray):
    """كلُّ نافذةٍ بطول n ⟵ (rms, logk) على الحاضر — `k` = سعرُ المصدر ÷ سعرُ البطاقة (كـ`match.masked_fit` على عمودين)."""
    n = len(ref)
    if len(hl) < n or mask.sum() == 0:
        return None
    lw = np.log(np.clip(hl, 1e-9, None))
    win = np.lib.stride_tricks.sliding_window_view(lw, (n, 2))[:, 0]
    d = (win - np.log(ref)[None, :, :])[:, mask, :]
    logk = d.mean(axis=(1, 2))
    res = d - logk[:, None, None]
    return np.sqrt((res ** 2).mean(axis=(1, 2))), logk


def judge_profile(card: dict, series: dict, events, day_of) -> dict:
    """الملمح ‏+ {متغيّر: شموع} ⟵ {label, top1, top2, …} بقاعدة `match.merge`/`match.verdict` بالاسم."""
    import match as M                                              # noqa: PLC0415
    bar_sec = M.BAR_MIN[card["frame"]] * 60
    n_hi = int(min(N_MAX, card["width"] / SLOT_MIN_PX))
    passers, shape_n = [], 0
    for lab, bars in series.items():
        adj = lab.split("|split:")[1] if "|split:" in lab else None
        good = [b for b in bars if all(isinstance(x, (int, float)) and x > 0 for x in b[1:5])]
        if not good:
            continue
        hl = np.array([[b[2], b[3]] for b in good], dtype=float)
        for n in range(N_MIN, n_hi + 1):
            ref, rel, mask = slots(card, n)
            if mask.mean() < SLOT_PRESENT:
                continue
            fit = fit_windows(hl, ref, mask)
            if fit is None:
                continue
            rms, logk = fit
            r = np.log1p(rel[mask])
            st = float(np.sqrt((r ** 2).mean())) * SHAPE_MULT
            lt = float(np.log1p(np.median(rel[mask]))) * LEVEL_MULT
            for i in np.where(rms <= st)[0]:
                i = int(i)
                shape_n += 1
                end = good[i + n - 1][0]
                k = float(math.exp(logk[i]))
                if events is None:
                    ok = None
                else:
                    ev = [e for e in events if e[0] != adj]
                    ok = abs(math.log(k) - math.log(M.split_factor(day_of(end), ev))) <= lt
                if ok is False:
                    continue
                passers.append({"i": i, "end_ts": int(end), "rms": float(rms[i]), "k": k, "n": n, "variant": lab,
                                "level_ok": ok})
    merged = M.merge(passers, bar_sec)
    label, t1, t2 = M.verdict(merged, 2 if events is not None else 1)
    row = {"label": label, "shape_pass": shape_n, "passers": len(merged)}
    for nm, t in (("top1", t1), ("top2", t2)):
        if t:
            row[nm] = {"end_ts": t["end_ts"], "rms": round(t["rms"], 5), "k": round(t["k"], 4), "n": t["n"],
                       "variant": t["variant"], "i": t["i"]}
    return row


def hit(frame: str, end_ts: int, truth_day: str, truth_hour: str, bars: list) -> bool:
    """§⑤: `1D`/`1W` ⟵ `results.side_hit` بالاسم مع جلسة الطابع · `4H` ⟵ فرقُ الفهرس 1 فأقلّ في السلسلة المطابَقة."""
    import header as HD                                            # noqa: PLC0415
    import results as RS                                           # noqa: PLC0415
    import tv_data as TV                                           # noqa: PLC0415
    if frame in ("1D", "1W"):
        last = TV.ny_time(end_ts).strftime("%Y-%m-%d")
        return bool(RS.side_hit(frame, last, HD.session_of(truth_day)))
    from zoneinfo import ZoneInfo                                  # noqa: PLC0415
    hh, mm = (int(x) for x in truth_hour.split(":"))
    t = dt.datetime.fromisoformat(truth_day).replace(hour=hh, minute=mm, tzinfo=ZoneInfo("America/New_York")).timestamp()
    ts = [b[0] for b in bars]
    j_end = ts.index(end_ts) if end_ts in ts else None
    j_t = max((j for j, x in enumerate(ts) if x <= t), default=None)
    return j_end is not None and j_t is not None and abs(j_end - j_t) <= 1


def run(ids: list, truth: dict, stage: str) -> list:
    """البطاقة ⟵ المطابقة ⟵ الإصابة لكلّ صورة ⟵ سطرُ `DV2\t{json}` ‏+ القائمة."""
    import app_card as AC6                                         # noqa: PLC0415
    import chart_id_tv as CT                                       # noqa: PLC0415
    import chart_pixels as P                                       # noqa: PLC0415
    import match as M                                              # noqa: PLC0415
    import tv_data as TV                                           # noqa: PLC0415
    uni = CT.universe()
    tmap = TV.ticker_map(uni) if uni else {}
    ch = TV.Chart()
    cache, out = {}, []
    img_dir = os.path.join(REPO, "faisal_images")
    files = {os.path.splitext(f)[0]: f for f in os.listdir(img_dir)}
    for iid in ids:
        tr = truth.get(iid) or {}
        row = {"id": iid, "stage": stage, "truth": tr.get("date"), "hour": tr.get("hour"), "symbol": tr.get("symbol")}
        try:
            card = AC6.build_card_app(P.load_rgb(os.path.join(img_dir, files[iid])))
        except Exception as e:                                     # noqa: BLE001
            card = {"ok": False, "why": f"رمى: {type(e).__name__}: {e}"[:160]}
        row["card_ok"] = bool(card.get("ok"))
        row["why"] = card.get("why", "")
        row["frame"] = card.get("frame")
        row["diag"] = {k: card.get(k) for k in ("tab_rel", "band", "hl", "width", "x_span", "cover", "y_hi", "y_lo")}
        if card.get("ok"):
            answers = []
            for sym in [s for s in (tr.get("symbol") or "").split(",") if s] or []:
                sym = sym.upper()
                names = [tmap[sym]] if sym in tmap else [f"{x}:{sym}" for x in ("NASDAQ", "NYSE", "AMEX")]
                events = M._events(sym)
                series = {}
                for lab, interval, ext, anc in M.FRAMES[card["frame"]]:
                    key = (sym, interval, ext)
                    if key not in cache:
                        got = None
                        for nm in names:
                            got = ch.bars(nm, interval=interval, n=M.N_BARS, extended=ext)
                            if got:
                                break
                        cache[key] = got
                    bars = cache[key]
                    if not bars:
                        continue
                    if anc is not None:
                        starts, end = CT.parse_anchors(CT.DEFAULT_ANCHORS)[anc]
                        bars = CT.aggregate(bars, starts, end)
                    series[lab] = bars
                    for d0, r0 in (events or []):
                        series[f"{lab}|split:{d0}"] = M.unadjust(bars, d0, r0, TV.ny_day)
                if not series:
                    continue
                j = judge_profile(card, series, events, TV.ny_day)
                j["sym"] = sym
                if j["label"] in ("واثق", "مرجّح"):
                    t1 = j["top1"]
                    j["end"] = TV.ny_time(t1["end_ts"]).strftime("%Y-%m-%d %H:%M")
                    j["hit"] = hit(card["frame"], t1["end_ts"], tr.get("date", ""), tr.get("hour") or "16:00",
                                   series[t1["variant"]])
                answers.append(j)
            got = [a for a in answers if a["label"] in ("واثق", "مرجّح")]
            row["answers"] = [{k: a.get(k) for k in ("sym", "label", "end", "hit", "shape_pass", "passers")} for a in answers]
            row["answered"] = len(got) == 1
            row["hit"] = bool(len(got) == 1 and got[0].get("hit"))
            row["label"] = got[0]["label"] if len(got) == 1 else ("غير محسوم" if got else "لا جواب")
        print(f"DV2\t{json.dumps(row, ensure_ascii=False)}", flush=True)
        out.append(row)
    return out


def summary(rows: list) -> dict:
    n = len(rows)
    built = [r for r in rows if r.get("card_ok")]
    hits = [r for r in built if r.get("hit")]
    b = len(built) / n if n else 0.0
    h = len(hits) / len(built) if built else 0.0
    return {"n": n, "built": len(built), "build_rate": round(b, 4), "hits": len(hits), "hit_rate": round(h, 4),
            "pass": bool(b >= BUILD_MIN and h >= HIT_MIN)}


def file_sha(p: str = APP_CARD) -> str:
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main(argv=None) -> int:
    import closed                                                  # noqa: PLC0415  🔒 الملحق 5 §⑤
    rc = closed.gate("app_v2", argv)
    if rc is not None:
        return rc
    stage = (os.environ.get("DCV2_STAGE") or "split").strip()
    rows = truth_rows()
    truth = {r["file"]: r for r in rows}
    cal, ho = split(rows)
    print(f"DV2S\t{json.dumps({'n': len(rows), 'cal': cal, 'holdout': ho, 'sha': file_sha()}, ensure_ascii=False)}")
    if stage == "split":
        return 0
    if stage == "cal":
        res = run(cal, truth, "cal")
    elif stage == "holdout":
        if not FROZEN_SHA or FROZEN_SHA != file_sha():
            print(f"⛔ holdout: البصمةُ المجمَّدة «{FROZEN_SHA or '—'}» لا تطابق app_card.py «{file_sha()}» (§④)")
            return 9
        res = run(ho, truth, "holdout")
    elif stage == "corpus":
        if not PASSED:
            print("⛔ corpus: لا يُؤرَّخ المدوّنُ إلّا بعد حكم «يعبر» منشور (§⑦)")
            return 9
        print("⛔ corpus: يُبنى بعد العبور (§⑦) — لم يُبنَ")
        return 9
    else:
        print(f"⛔ وضعٌ غيرُ معروف: {stage}")
        return 2
    s = summary(res)
    print(f"DV2R\t{json.dumps(s, ensure_ascii=False)}")
    print(f"📊 {stage}: بطاقة {s['built']}/{s['n']} = {s['build_rate']:.1%} (الحدّ {BUILD_MIN:.0%}) · إصابة {s['hits']}/{s['built']} = "
          f"{s['hit_rate']:.1%} (الحدّ {HIT_MIN:.0%}) ⟵ {'✅ يعبر' if s['pass'] else '❌ لا يعبر'}"
          + (" — وصفٌ (ضُبط عليه)" if stage == "cal" else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
