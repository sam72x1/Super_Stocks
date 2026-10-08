"""🔬 PHASE 3 — إعادةُ بناء حالة البوت لكلّ رمزٍ وجلسة (بلا نظرٍ للأمام):
CANDIDATE(T) = `analyze_ticker` الإنتاجيّ على شموعٍ < T · WATCHLIST/READY(T) من تاريخ git لقائمة الأسبوع (لقطةُ اليوم أو آخرُ لقطةٍ قبله)
· NEAR_WATCH(T) من تاريخ git لـ`near_watch.json`. قراءةٌ فقط."""
import csv
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p3lib as L                        # noqa: E402

SCR = "/tmp/claude-0/-home-user-Super-Stocks/59271cc5-48be-5019-b321-70eeaec06f58/scratchpad/fm"
START = "2025-06-20"                      # بدءُ تاريخ القائمة في git


def sample():
    g = json.load(open(os.path.join(L.ROOT, "fm_forensics", "phase2", "out", "groups.json")))
    f = {r["ticker"] for r in L.faisal_rows() if r["is_faisal"]}
    syms = set(L.ANCHORS) | {L.NEG_ANCHOR} | f | set(g.get("neg", [])) | set(g.get("m2hi", []))
    return sorted(s for s in syms if s in L.load()["daily"])


def history():
    wl = json.load(open(os.path.join(SCR, "wl_members.json")))
    nw = json.load(open(os.path.join(SCR, "nw_sets.json")))
    by_day = {}
    for r in wl:                                           # آخرُ لقطةٍ في اليوم
        by_day[r["day"]] = r
    nw_day = {}
    for r in nw:
        nw_day[r["day"]] = r
    return by_day, nw_day


def snap_at(by_day, day):
    """لقطةُ اليوم أو آخرُ لقطةٍ قبله (الحالةُ الصباحيّة = ما كُتب حتى اليوم)."""
    keys = [k for k in by_day if k <= day]
    return by_day[max(keys)] if keys else None


def main():
    syms = sample(); cal = [d for d in L.calendar() if d >= START]
    by_day, nw_day = history()
    out = []
    for i, sym in enumerate(syms):
        rows = L.load()["daily"][sym]
        for day in cal:
            before = [r for r in rows if r[0] < day]
            if len(before) < 2:
                continue
            res, reason, extra = L.run_gates(sym, L.frame(before))
            wl = snap_at(by_day, day); nw = snap_at(nw_day, day)
            m = (wl or {}).get("members", {}).get(sym)
            out.append(dict(symbol=sym, date=day, asof=before[-1][0], candidate=int(res == "PASS"), result=res, reason=reason,
                            gate=L.reason_gate(reason) if res == "REJECT" else ("DEPTH" if res == "TOO_FEW_BARS" else ""),
                            watchlist=int(bool(m)), watch_es=(m or {}).get("es", ""), watch_cont=(m or {}).get("cont", "") or "",
                            ready=int(bool(m) and (m or {}).get("es") == "ready_now"),
                            pullback=int(sym in ((wl or {}).get("pullback") or [])),
                            near_watch=("inside" if nw and sym in nw.get("inside", []) else ("oversold" if nw and sym in nw.get("oversold", []) else "")),
                            nw_known=int(bool(nw)), wl_snap=(wl or {}).get("day", "")))
        print(i + 1, sym, len(out), flush=True)
    path = os.path.join(L.OUT, "bot_states.csv.gz")
    keys = list(out[0].keys())
    with gzip.open(path, "wt", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); [w.writerow(r) for r in out]
    print(path, len(out), "symbols", len(syms))


if __name__ == "__main__":
    main()
