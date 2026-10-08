"""🔬 PHASE 3 — تعطيلُ بوّابةٍ واحدة (leave-one-gate-out · بحثٌ فقط):
لكلّ صفٍّ مؤرَّخ (رمز، يوم) يُعاد `analyze_ticker` الإنتاجيّ على شموعٍ < اليوم مرّةً كما هو ومرّةً لكلّ بوّابةٍ مُرخاة
(القيمُ تُستعاد في `finally` — لا تعديلَ في الإنتاج). المجموعات: فيصل المؤرَّخ (مستقلّ) · المراسي (يوميًّا ±20) ·
الضوابطُ السالبة والمطابقة (تواريخُ سجلّ الرفض العشرون) · ومجموعةُ ذاكرةِ المرشَّح (N جلسات)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p3lib as L                        # noqa: E402

FOCUS_LIST_0913 = ["SXTC", "MSGY", "DKI", "CUPR", "YMT", "CETX", "ATPC", "SVRE"]   # X_20260918_23 (قائمتي · 2026-09-13)


def targets():
    g = json.load(open(os.path.join(L.ROOT, "fm_forensics", "phase2", "out", "groups.json")))
    log_dates = [d["date"] for d in json.load(open(os.path.join(L.ROOT, "reject_log.json")))]
    T = []
    for r in L.faisal_rows():
        if r["is_faisal"] and r["state"] in ("FOCUS", "WATCH", "READY", "ENTRY") and r["ticker"] in L.load()["daily"]:
            T.append(("faisal", r["ticker"], r["date"], r["state"], r["image"]))
    for t in FOCUS_LIST_0913:
        if t in L.load()["daily"]:
            T.append(("faisal", t, "2026-09-13", "FOCUS", "X_20260918_23_watchlist"))
    for a in L.ANCHORS + [L.NEG_ANCHOR]:
        for d in [L.shift("2026-09-11", k) for k in range(-20, 21)]:
            T.append(("anchor", a, d, "", ""))
    for grp in ("neg", "m2hi"):
        for s in g.get(grp, []):
            if s in L.load()["daily"]:
                for d in log_dates:
                    T.append((grp, s, d, "", ""))
    seen = set(); out = []
    for t in T:
        k = (t[0], t[1], t[2])
        if k not in seen:
            seen.add(k); out.append(t)
    return out


def main():
    out = []
    for i, (grp, sym, day, fstate, image) in enumerate(targets()):
        before = L.bars_before(sym, day)
        if len(before) < 2:
            continue
        df = L.frame(before)
        base, reason, extra = L.run_gates(sym, df)
        row = dict(group=grp, symbol=sym, date=day, asof=before[-1][0], faisal_state=fstate, image=image,
                   CURRENT=base, CURRENT_reason=reason, CURRENT_gate=L.reason_gate(reason) if base == "REJECT" else ("DEPTH" if base == "TOO_FEW_BARS" else ""))
        for gte in L.GATE_ORDER:
            r2, why2, _ = L.run_gates(sym, df, (gte,))
            row[f"NO_{gte}"] = r2 if r2 != "REJECT" else L.reason_gate(why2)
        r3, why3, _ = L.run_gates(sym, df, tuple(L.GATE_ORDER))
        row["NO_ALL_IDENTITY"] = r3 if r3 != "REJECT" else L.reason_gate(why3)
        out.append(row)
        if i % 200 == 0:
            print(i, sym, day, base, reason, flush=True)
    path = os.path.join(L.OUT, "logo_rows.csv")
    L.write_csv(path, out)
    print(path, len(out))


if __name__ == "__main__":
    main()
