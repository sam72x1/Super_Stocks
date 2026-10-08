"""🔬 PHASE 3 — §11 نافذةٌ زمنيّة (بحثٌ فقط): هل تتميّز أسماءُ فيصل عن ضابطٍ مطابَقِ التاريخ بميزاتِ الشموع عند T−k (k ∈ 1,2,3,5,7,10,15)؟
و§17 «أبكرُ تركيزٍ مُسنَد»: لكلّ رمزٍ أبكرُ يومِ FOCUS/WATCH مؤرَّخ ⟵ الجلساتُ حتى READY/ENTRY/أوّل +50% (من التسميات المسجَّلة مسبقًا)."""
import csv
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p3lib as L                        # noqa: E402

WINDOWS = [1, 2, 3, 5, 7, 10, 15]


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


TESTS = {"touches==0": lambda c: f(c.get("tested_touches")) is not None and f(c.get("tested_touches")) < 1,
         "drop_in_band": lambda c: f(c.get("drop_pct")) is not None and 71.72 <= f(c.get("drop_pct")) <= 99.95,
         "spike>=78": lambda c: f(c.get("spike_pct")) is not None and f(c.get("spike_pct")) >= 78.27,
         "base15<=120": lambda c: f(c.get("base_range_pct")) is not None and f(c.get("base_range_pct")) <= 120,
         "rsi<33": lambda c: f(c.get("rsi14")) is not None and f(c.get("rsi14")) < 33,
         "dist_low30<=10%": lambda c: f(c.get("dist_low30_pct")) is not None and f(c.get("dist_low30_pct")) <= 10,
         "post_split_frame": lambda c: f(c.get("drop_from_psh_pct")) is not None}


def windows():
    pos = list(csv.DictReader(open(os.path.join(HERE, "POSITIVE_TEMPORAL_CONTROLS.csv"), encoding="utf-8")))
    faisal_t = {r["ticker"] for r in L.faisal_rows()}
    pool = sorted(s for s in L.load()["daily"] if s not in faisal_t)
    random.seed(20261008)
    ctrl = {p["TICKER"]: random.sample(pool, 6) for p in pos}
    out = []
    for k in WINDOWS:
        pc = [L.context(p["TICKER"], L.shift(L.session(p["READY_OR_ENTRY_DATE"]), -k)) or {} for p in pos]
        cc = [L.context(s, L.shift(L.session(p["READY_OR_ENTRY_DATE"]), -k)) or {} for p in pos for s in ctrl[p["TICKER"]]]
        cc = [c for c in cc if c]
        for name, t in TESTS.items():
            a = sum(1 for c in pc if c and t(c)); b = sum(1 for c in cc if t(c))
            odds = round(((a + 0.5) / (len(pc) - a + 0.5)) / ((b + 0.5) / (len(cc) - b + 0.5)), 2)
            out.append(dict(WINDOW_SESSIONS_BEFORE=k, FEATURE=name, POS=f"{a}/{len(pc)}", DATE_MATCHED_CTRL=f"{b}/{len(cc)}", ODDS=odds,
                            SEPARATES=("YES" if odds >= 3 else ("INVERSE" if odds <= 0.33 else "NO")),
                            NOTE="post-hoc supplementary (announced in prereg §⑥ as an extension of the window test); 7 positives vs 6 date-matched probe-universe names each; bars < date"))
    L.write_csv(os.path.join(HERE, "TEMPORAL_WINDOW_DISTINGUISHABILITY.csv"), out)
    for r in out:
        if r["SEPARATES"] != "NO":
            print(r["WINDOW_SESSIONS_BEFORE"], r["FEATURE"], r["POS"], r["DATE_MATCHED_CTRL"], r["ODDS"], r["SEPARATES"])
    print("rows", len(out))


def earliest_focus():
    lead = {}
    for r in csv.DictReader(open(os.path.join(HERE, "TEMPORAL_LEAD_TIME_ANALYSIS.csv"), encoding="utf-8")):
        lead[(r["TICKER"], r["DATE"])] = r
    by = {}
    for r in csv.DictReader(open(os.path.join(HERE, "FAISAL_TIMELINE.csv"), encoding="utf-8")):
        if r["IS_FAISAL"] != "1" or r["OBSERVATION_CLASS"] not in ("FOCUS", "WATCH", "READY", "ENTRY") or len(r["DATE"]) != 10:
            continue
        by.setdefault(r["TICKER"], []).append(r)
    out = []
    for t, rows in sorted(by.items()):
        rows.sort(key=lambda r: r["DATE"])
        first = rows[0]
        def firstof(cls):
            return next((x["DATE"] for x in rows if x["OBSERVATION_CLASS"] == cls), "")
        rd, ed = firstof("READY"), firstof("ENTRY")
        fs = L.session(first["DATE"])
        def gap(d):
            return (L.cal_index(L.session(d)) - L.cal_index(fs)) if d else ""
        lr = lead.get((t, first["DATE"])) or {}
        out.append(dict(TICKER=t, EARLIEST_FOCUS_OR_WATCH_DATE=first["DATE"], CLASS=first["OBSERVATION_CLASS"], EVIDENCE=first["EVIDENCE_ID"],
                        EVIDENCE_AVAILABLE_ON_DATE="YES (dated unit)", FIRST_READY=rd, SESSIONS_TO_READY=gap(rd), FIRST_ENTRY=ed, SESSIONS_TO_ENTRY=gap(ed),
                        SESSIONS_TO_FIRST_PLUS50=lr.get("lead_sessions_to_50", "NA (no bars)"), SESSIONS_TO_FIRST_PLUS100=lr.get("lead_sessions_to_100", "NA (no bars)"),
                        N_AFTER=lr.get("n_after", ""), NOTE="Focus date = earliest dated FOCUS/WATCH/READY/ENTRY unit; never backfilled from outcome"))
    L.write_csv(os.path.join(HERE, "EARLIEST_FOCUS.csv"), out)
    have = [r for r in out if r["SESSIONS_TO_FIRST_PLUS50"] not in ("", "NA (no bars)")]
    print("tickers", len(out), "with +50 reached", len(have), sorted(int(float(r["SESSIONS_TO_FIRST_PLUS50"])) for r in have))
    print("ready gaps", [(r["TICKER"], r["SESSIONS_TO_READY"]) for r in out if r["SESSIONS_TO_READY"] != ""], "entry gaps", [(r["TICKER"], r["SESSIONS_TO_ENTRY"]) for r in out if r["SESSIONS_TO_ENTRY"] != ""])


if __name__ == "__main__":
    windows()
    earliest_focus()
