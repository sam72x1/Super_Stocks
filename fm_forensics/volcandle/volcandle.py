#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🕯️📊 `T-VOLCANDLE` — «شموع الفوليوم» بتعريف فيصل · المرحلةُ صفر (العقد `T_VOLCANDLE_prereg.md` · أمرُ المالك 2026-11-21).

  zero   — على رنر GitHub: شموعُ TradingView (4 ساعات ممتدّة ‏+ يوميّ) للشاهدَين المؤرَّخين وحدَهما ⟵ نطاقُ كلّ تعريفٍ من الثمانية
           في لحظة المنشور ⟵ المطابقةُ (التقاطع ÷ الاتّحاد) ⟵ بوّابةُ إعادة الإنتاج ⟵ `out/ZERO.json|md` · **مرّةً واحدة**.
🔒 قياسٌ فقط: لا تلغرام · لا Polygon · لا أسرار · لا CONFIG يُسنَد · لا رقمَ أداء (أداةُ الأداء لا تُبنى ما لم تعبر البوّابة).
رموزُ الخروج: 0 تمّ · 5 مادّةٌ ناقصة · 7 صدرت · 8 مُغلَق · 11 عقدٌ متغيّر.
"""
import datetime as dt
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CONTRACT = os.path.join(HERE, "T_VOLCANDLE_prereg.md")
CONTRACT_SHA = "8b36b4c831b2b3987c7830baa7c29d4e4daede0c974233dd313e1f22535cfec2"                                                # يُملأ قبل الدمج · فارغٌ أو مخالف ⟵ خروج 11
OUT = os.path.join(HERE, "out")
RC_OK, RC_DATA, RC_ONCE, RC_CLOSED, RC_CONTRACT = 0, 5, 7, 8, 11
CLOSED = True                                                      # 2026-11-21: «التعريف لا يُعاد إنتاجه» (`T_VOLCANDLE_RESULT.md`) ⟵ مُغلَقٌ مُنفَّذًا

BAR_S = 4 * 3600                                                   # شمعةُ 4 ساعات
AVG_N = 20                                                         # متوسّطُ حجم الشموع العشرين قبل الشمعة — العقد §③
KS = (3, 5)                                                        # هندسيّ — العقد §③
WIN_SESS = 60                                                      # «آخر 60 جلسة»
EXPL_LOOK = 250                                                    # «منذ آخر انفجار»: ضمن آخر 250 جلسة
IOU_MIN = 0.5
SCALE_LO, SCALE_HI = 0.85, 1.15                                    # فحصُ المقياس مقابل سعر الشارت — العقد §②
NEED_NUMERIC = 2
WINDOWS = ("w60", "expl")
BANDS = ("body", "wick")

# الشواهد (العقد §①): المؤرَّخان يدخلان · والثلاثة الباقية تُسمّى وتخرج
WITNESSES = [
    {"id": "TG_76009", "sym": "ELAB", "post_utc": "2026-10-20T23:52:00Z", "band": (1.80, 2.20), "chart_px": 2.95},
    {"id": "TG_76014", "sym": "ZCMD", "post_utc": "2026-10-14T00:57:00Z", "band": None, "chart_px": 1.30},
]
EXCLUDED = [
    {"id": "TG_76001 + TG_75999", "sym": "JEM", "band": (2.00, 2.20), "why": "تاريخُ المنشور غيرُ مؤكَّد (لقطةُ TG_76000 بعد إغلاق 23/10 حدٌّ أدنى لا يوم) · والبطاقةُ بلا كاتبٍ ظاهر"},
    {"id": "TG_76021", "sym": "FBGL", "band": None, "why": "طابعٌ نسبيّ «4 د» · قبل 10-15 بلا يومٍ مُثبَت"},
    {"id": "X_20260918_04_ELPW + CH_20260918_03_ELPW", "sym": "ELPW", "band": (2.186, 2.270),
     "why": "لا تاريخَ للمنشور (الاستلامُ دفعة 2026-09-18) · والتأريخُ بالشموع محورٌ مُغلَق"},
]


def log(m=""):
    print(m, flush=True)


def sha_of(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def contract_ok():
    try:
        return bool(CONTRACT_SHA) and sha_of(CONTRACT) == CONTRACT_SHA
    except OSError:
        return False


def closed():
    return bool(CLOSED) and os.environ.get("VOLCANDLE_REOPEN", "") != "1"


def guard(out_dir=None):
    """⟵ رمزُ الخروج قبل أيّ عمل: 11 عقدٌ متغيّر · 7 صدرت · 0 يمضي."""
    out_dir = OUT if out_dir is None else out_dir
    if not contract_ok():
        return RC_CONTRACT
    if os.path.exists(os.path.join(out_dir, "ZERO.json")):
        return RC_ONCE
    return RC_OK


# ══ نقيّة ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def post_ts(w):
    return int(dt.datetime.strptime(w["post_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).timestamp())


def completed(h4, cutoff):
    """شموعُ 4 ساعات المكتملة قبل اللحظة: افتتاحُها + 4 ساعات ≤ اللحظة (لا نظرَ إلى شمعةٍ لم تُغلق)."""
    return [b for b in h4 if int(b[0]) + BAR_S <= cutoff]


def vol_idx(bars, k):
    """أرقامُ شموع الفوليوم: حجمُها ≥ k × متوسّطِ الشموع العشرين قبلها (بلا هي) · وما قبله أقلُّ من 20 لا يُعَدّ."""
    out = []
    for i in range(AVG_N, len(bars)):
        prev = [float(b[5] or 0.0) for b in bars[i - AVG_N:i]]
        avg = sum(prev) / AVG_N
        if avg > 0 and float(bars[i][5] or 0.0) >= k * avg:
            out.append(i)
    return out


def window_days(daily, day_of, dec_day, kind):
    """⟵ أوّلُ يومٍ في النافذة أو None: «w60» آخرُ 60 جلسة حتى يوم القرار · «expl» آخرُ جلسةٍ إغلاقُها +EXPLOSION_PCT فوق سابقتها ضمن 250."""
    rows = [(day_of(b[0]), float(b[4])) for b in daily if day_of(b[0]) <= dec_day]
    if not rows:
        return None
    if kind == "w60":
        return rows[-WIN_SESS:][0][0]
    import Super_stock as S
    thr = float(S.CONFIG["EXPLOSION_PCT"]) / 100.0
    look = rows[-(EXPL_LOOK + 1):]
    for j in range(len(look) - 1, 0, -1):
        if look[j - 1][1] > 0 and look[j][1] / look[j - 1][1] - 1.0 >= thr:
            return look[j][0]
    return None


def band_of(bars, idx, price, mode):
    """شموعُ الفوليوم تحت السعر (حدُّها الأعلى المستعمَل دون السعر) ⟵ (أدنى، أعلى، عددُها) أو (None، None، 0)."""
    lo, hi, n = None, None, 0
    for i in idx:
        o, h, l, c = (float(x) for x in bars[i][1:5])
        a, b = (min(o, c), max(o, c)) if mode == "body" else (l, h)
        if b < price:
            lo = a if lo is None else min(lo, a)
            hi = b if hi is None else max(hi, b)
            n += 1
    return lo, hi, n


def iou(a, b):
    if a is None or b is None or a[0] is None or b[0] is None:
        return None
    inter = max(0.0, min(a[1], b[1]) - max(a[0], b[0]))
    union = max(a[1], b[1]) - min(a[0], b[0])
    return inter / union if union > 0 else (1.0 if inter == 0 and a == b else 0.0)


def definitions():
    """الثمانية بترتيب البساطة (العقد §③): K=3 قبل 5 · «60 جلسة» قبل «منذ الانفجار» · «الأجسام» قبل «الذيول»."""
    return [{"k": k, "win": w, "band": b, "name": f"K{k}·{w}·{b}"} for k in KS for w in WINDOWS for b in BANDS]


def witness_rows(w, h4, daily, day_of):
    """شاهدٌ مؤرَّخ ⟵ صفٌّ لكلّ تعريف: النطاق · التقاطع ÷ الاتّحاد · عددُ الشموع · وفحصُ المقياس."""
    cut = post_ts(w)
    bars = completed(h4, cut)
    dec_day = day_of(cut)
    if len(bars) <= AVG_N:
        return {"id": w["id"], "sym": w["sym"], "status": "بلا شموع كافية", "rows": []}
    price = float(bars[-1][4])
    scale = price / w["chart_px"] if w.get("chart_px") else None
    res = {"id": w["id"], "sym": w["sym"], "dec_day": dec_day, "last_bar": int(bars[-1][0]), "price": round(price, 4),
           "chart_px": w.get("chart_px"), "scale": round(scale, 4) if scale else None, "faisal": w["band"], "rows": []}
    if scale is None or not (SCALE_LO <= scale <= SCALE_HI):
        res["status"] = "فرقُ مقياس"
        return res
    res["status"] = "ok"
    days4 = [day_of(b[0]) for b in bars]
    for d in definitions():
        start = window_days(daily, day_of, dec_day, d["win"])
        row = {"def": d["name"], "start": start, "lo": None, "hi": None, "n": 0, "iou": None}
        if start is not None:
            idx = [i for i in vol_idx(bars, d["k"]) if days4[i] >= start]
            lo, hi, n = band_of(bars, idx, price, d["band"])
            row.update(lo=None if lo is None else round(lo, 4), hi=None if hi is None else round(hi, 4), n=n, n_vol=len(idx))
            if w["band"] is not None:
                row["iou"] = None if lo is None else round(iou((lo, hi), w["band"]), 4)
        res["rows"].append(row)
    return res


def gate(wits):
    """⟵ {verdict, chosen, per_def}: تعريفٌ يطابق شاهدين رقميّين فأكثر (ومعه الشاهدُ بلا رقم إن وُجد) · وإلّا «التعريف لا يُعاد إنتاجه»."""
    ok = [w for w in wits if w.get("status") == "ok"]
    numeric = [w for w in ok if w["faisal"] is not None]
    plain = [w for w in ok if w["faisal"] is None]
    per = []
    for k, d in enumerate(definitions()):
        m = [w["rows"][k]["iou"] for w in numeric if w["rows"][k]["iou"] is not None and w["rows"][k]["iou"] >= IOU_MIN]
        p = all(w["rows"][k]["n"] > 0 for w in plain)
        ious = [w["rows"][k]["iou"] for w in numeric if w["rows"][k]["iou"] is not None]
        per.append({"def": d["name"], "matched_numeric": len(m), "plain_ok": p, "mean_iou": (sum(ious) / len(ious)) if ious else None,
                    "pass": len(m) >= NEED_NUMERIC and p})
    passing = [x for x in per if x["pass"]]
    chosen = None
    if passing:
        chosen = sorted(passing, key=lambda x: (-x["matched_numeric"], -(x["mean_iou"] or 0.0)))[0]["def"]
    return {"verdict": "يُعاد إنتاجه" if chosen else "التعريف لا يُعاد إنتاجه", "chosen": chosen, "per_def": per,
            "numeric_dated": len(numeric), "need": NEED_NUMERIC, "reachable": len(numeric) >= NEED_NUMERIC}


def _f(x, nd=3):
    return "—" if x is None else f"{x:.{nd}f}"


def render(res):
    g = res["gate"]
    L = ["# 🕯️📊 `T-VOLCANDLE` — المرحلةُ صفر: هل يُعاد إنتاجُ «شموع الفوليوم»؟", ""]
    if not g["reachable"]:
        L += [f"**الشواهدُ الرقميّة المؤرَّخة {g['numeric_dated']} من {g['need']} لازمة ⟵ البوّابة لا تُبلَغ بالبناء · الحكم: {g['verdict']}** "
              "(محسومٌ بالعقد §① قبل التشغيل).", ""]
    else:
        L += [f"**الحكم: {g['verdict']}**" + (f" · التعريفُ المعتمد `{g['chosen']}`" if g["chosen"] else ""), ""]
    L += ["## الشواهد الداخلة", ""]
    for w in res["witnesses"]:
        L.append(f"### {w['sym']} · `{w['id']}` · يومُ القرار {w.get('dec_day', '—')} · السعر {_f(w.get('price'))} "
                 f"(الشارت {_f(w.get('chart_px'), 2)} · النسبة {_f(w.get('scale'))}) · {w['status']}")
        if w.get("faisal"):
            L.append(f"- نطاقُ فيصل: [{w['faisal'][0]}، {w['faisal'][1]}]")
        L += ["", "| التعريف | بداية النافذة | شموعُ الفوليوم في النافذة | منها تحت السعر | نطاقُنا | التقاطع ÷ الاتّحاد |", "|---|---|---|---|---|---|"]
        for r in w["rows"]:
            nb = "—" if r["lo"] is None else f"[{_f(r['lo'])}، {_f(r['hi'])}]"
            L.append(f"| `{r['def']}` | {r['start'] or '—'} | {r.get('n_vol', 0)} | {r['n']} | {nb} | {_f(r['iou'], 2)} |")
        L.append("")
    L += ["## الشواهد الخارجة (تُسمّى ولا تُحسب)", ""]
    for x in EXCLUDED:
        L.append(f"- {x['sym']} · `{x['id']}` — {x['why']}")
    L += ["", "## البوّابة لكلّ تعريف", "", "| التعريف | شواهدُ رقميّة طابقت (0.5 فأكثر) | الشاهدُ بلا رقم له نطاق | يعبر؟ |", "|---|---|---|---|"]
    for p in g["per_def"]:
        L.append(f"| `{p['def']}` | {p['matched_numeric']} | {'نعم' if p['plain_ok'] else 'لا'} | {'✅' if p['pass'] else '❌'} |")
    L += ["", "> التعريفاتُ هندسيّة (لا رقمَ من فيصل للعتبة ولا للنافذة) · ولا رقمَ أداءٍ في هذه المرحلة."]
    return "\n".join(L) + "\n"


# ══ الوضع ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def mode_zero(out_dir=None, fetch=None):
    out_dir = OUT if out_dir is None else out_dir
    rc = guard(out_dir)
    if rc:
        log(f"⛔ الحارس — خروج {rc}")
        return rc
    import tv_data as TV
    if fetch is None:
        import Super_stock as S
        tmap = S._tv_ticker_map() or {}

        def fetch(syms):
            full = {s: tmap.get(s) or f"NASDAQ:{s}" for s in syms}
            h4 = TV.fetch_many(sorted(set(full.values())), interval="240", n=1500, extended=True, workers=2, retry_pass=True)
            d1 = TV.fetch_many(sorted(set(full.values())), interval="1D", n=600, extended=False, workers=2, retry_pass=True)
            return ({s: h4.get(f) or [] for s, f in full.items()}, {s: d1.get(f) or [] for s, f in full.items()})
    h4, d1 = fetch([w["sym"] for w in WITNESSES])
    if not all(h4.get(w["sym"]) and d1.get(w["sym"]) for w in WITNESSES):
        log(f"⛔ شموعٌ ناقصة: {[w['sym'] for w in WITNESSES if not (h4.get(w['sym']) and d1.get(w['sym']))]} — خروج {RC_DATA}")
        return RC_DATA
    wits = [witness_rows(w, h4[w["sym"]], d1[w["sym"]], TV.ny_day) for w in WITNESSES]
    res = {"witnesses": wits, "excluded": EXCLUDED, "gate": gate(wits), "contract_sha": CONTRACT_SHA}
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "ZERO.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, sort_keys=True)
    md = render(res)
    with open(os.path.join(out_dir, "ZERO.md"), "w", encoding="utf-8") as fh:
        fh.write(md)
    log(md)
    return RC_OK


def main(argv):
    if len(argv) >= 2 and argv[1] == "zero":
        if closed():
            log(f"🔒 `T-VOLCANDLE` مُغلَقٌ مُنفَّذًا — الفتحُ إقرارُ المالك `VOLCANDLE_REOPEN=1` · خروج {RC_CLOSED}")
            return RC_CLOSED
        return mode_zero()
    log(__doc__)
    return RC_DATA


if __name__ == "__main__":
    sys.exit(main(sys.argv))
