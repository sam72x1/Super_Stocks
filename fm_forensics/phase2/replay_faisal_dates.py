"""🔬 PHASE 2 — إعادةُ تشغيل بوّابات الهُويّة على **تواريخ قرارات فيصل المؤرَّخة** (صفوفٌ مستقلّة عن المراسي) في العوالم A/B_PSH/B_RAW.
قراءةٌ فقط · لا نظرَ للأمام (شموعُ ≤ يوم القرار)."""
import csv, os, sys, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replay as R
data = R.load(); anch = {"DKI", "SXTC", "HUBC", "CRE"}
tl = list(csv.DictReader(open(os.path.join(R.ROOT, "fm_forensics", "FAISAL_FOCUS_TIMELINE.csv"))))
pairs = sorted({(r["TICKER"], r["DATE"], r["DECISION"], r["IMAGE_ID"]) for r in tl if re.match(r"\d{4}-\d{2}-\d{2}$", r["DATE"]) and r["IS_FAISAL"] in ("True", "F") and r["DECISION"] in ("READY", "WAIT", "WATCH", "REJECT") and r["TICKER"] in data["daily"]})
out = []
for sym, day, dec, img in pairs:
    rows = data["daily"][sym]; sp = [(d, float(r)) for d, r in (data.get("splits") or {}).get(sym) or []]
    asof_rows = [r for r in rows if r[0] <= day]
    if not asof_rows or asof_rows[-1][0] < day[:7] + "-01":
        continue
    for w in ("A", "B_PSH", "B_RAW"):
        df = R.frame(asof_rows if w != "B_RAW" else R.raw_rows(asof_rows, sp))
        res, extra = R.run_one(sym, df, w, sp if w == "B_PSH" else None)
        row = dict(ticker=sym, faisal_date=day, faisal_decision=dec, image=img, anchor=("yes" if sym in anch else ""), world=w, bot_result=res, **R.inputs(df))
        if extra: row.update(extra)
        out.append(row)
keys = ["ticker", "faisal_date", "faisal_decision", "image", "anchor", "world", "bot_result", "price", "hi52", "drop", "spike", "base_range", "dollar_vol", "bars", "score", "soft_fails"]
p = os.path.join(R.HERE, "FAISAL_DATED_REPLAY.csv")
with open(p, "w", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore"); wr.writeheader(); [wr.writerow(r) for r in out]
print(p, len(out), "pairs", len(pairs))
c = collections.Counter((r["faisal_decision"], r["world"], r["bot_result"][:16]) for r in out if not r["anchor"])
for k in sorted(c): print(k, c[k])
