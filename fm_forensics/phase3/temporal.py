"""🔬 PHASE 3 — التجاربُ الزمنيّة (وسومُ النتيجة مسجَّلةٌ مسبقًا في PHASE3_prereg.md §②؛ تُحسب بعد تجميد الحقول التاريخيّة):
① TEMPORAL_LEAD_TIME_ANALYSIS.csv — زمنُ القيادة من كلّ ملاحظةٍ لفيصل (FOCUS/WATCH/READY/ENTRY) إلى أوّل جلسةٍ تحقّق +25/+50/+100% ·
   وشبكةُ T−k: هل كان البوت مرشِّحًا/مراقِبًا/جاهزًا قبل الملاحظة بـk جلسات (من bot_states).
② TEMPORAL_PERSISTENCE_ANALYSIS.csv — استمرارُ فيصل (الملاحظاتُ المتتالية) مقابل استمرار البوت (CANDIDATE/WATCHLIST/READY متتالية).
③ TEMPORAL_ARCHITECTURE_COMPARISON.csv — A (لقطة) مقابل B (ذاكرةُ مرشَّحٍ N جلسات) على الاختلاف الأوّل والضوابط السالبة.
④ POSITIVE/NEGATIVE_TEMPORAL_CONTROLS.csv — الضوابطُ المثبَّتةُ في العقد §⑤.
⑤ FIRST_DIVERGENCE_TEMPORAL_MATRIX.csv — أوّلُ يومٍ لفيصل حالةٌ ولا تمثيلَ للبوت · وأوّلُ رفضٍ وجدار."""
import collections
import csv
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p3lib as L                        # noqa: E402

GRID = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20]
ACTIVE = ("FOCUS", "WATCH", "READY", "ENTRY")


def load_states():
    p = os.path.join(L.OUT, "bot_states.csv.gz")
    if not os.path.exists(p):
        return {}
    d = {}
    with gzip.open(p, "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d[(r["symbol"], r["date"])] = r
    return d


def faisal_obs():
    rows = [r for r in csv.DictReader(open(os.path.join(HERE, "FAISAL_TIMELINE.csv"), encoding="utf-8"))
            if r["IS_FAISAL"] == "1" and r["OBSERVATION_CLASS"] in ACTIVE and r["TICKER"] in L.load()["daily"]]
    # صفٌّ واحد لكلّ (رمز، يوم) بأعلى حالة
    order = {"ENTRY": 0, "READY": 1, "FOCUS": 2, "WATCH": 3}
    best = {}
    for r in rows:
        k = (r["TICKER"], r["DATE"])
        if k not in best or order[r["OBSERVATION_CLASS"]] < order[best[k]["OBSERVATION_CLASS"]]:
            best[k] = r
    return sorted(best.values(), key=lambda r: (r["TICKER"], r["DATE"]))


def q(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return dict(n=0, median=None, q1=None, q3=None, min=None, max=None)
    def pct(p):
        i = (len(xs) - 1) * p; lo = int(i); hi = min(lo + 1, len(xs) - 1)
        return round(xs[lo] + (xs[hi] - xs[lo]) * (i - lo), 1)
    return dict(n=len(xs), median=pct(0.5), q1=pct(0.25), q3=pct(0.75), min=xs[0], max=xs[-1])


def lead_time(obs, states):
    out = []
    for r in obs:
        t, d = r["TICKER"], r["DATE"]
        o = L.outcomes(t, d) or {}
        row = dict(TICKER=t, DATE=d, FAISAL_STATE=r["OBSERVATION_CLASS"], EVIDENCE_ID=r["EVIDENCE_ID"], ANCHOR=int(t in L.ANCHORS),
                   DATA_CUTOFF=f"bars < {d}", DECISION_TIME=d, LOOKAHEAD_PROTECTION="state from evidence dated ≤ DATE; bars < DATE",
                   FUTURE_REVEAL_TIME="after row frozen (outcomes() on bars ≥ DATE)", n_after=o.get("n_after"))
        for k in L.K_WINDOWS:
            for p in L.P_LEVELS:
                row[f"MOVE_{p}_{k}"] = o.get(f"MOVE_{p}_{k}")
            row[f"VOL_ADJ_{k}"] = o.get(f"VOL_ADJ_{k}"); row[f"max_gain_{k}"] = o.get(f"max_gain_{k}")
        for p in L.P_LEVELS:
            row[f"lead_sessions_to_{p}"] = o.get(f"first_session_{p}")
        # شبكة T−k: حالةُ البوت قبل الملاحظة بـk جلسات (لقطةُ ذلك اليوم)
        for k in GRID:
            s = states.get((t, L.shift(d, -k))) if k else None
            row[f"bot_cand_T-{k}"] = (s or {}).get("candidate", "")
            row[f"bot_watch_T-{k}"] = (s or {}).get("watchlist", "")
            row[f"bot_nw_T-{k}"] = (s or {}).get("near_watch", "")
            row[f"bot_ready_T-{k}"] = (s or {}).get("ready", "")
        s0 = states.get((t, L.session(d))) or {}
        row.update(bot_cand_T=s0.get("candidate", ""), bot_gate_T=s0.get("gate", ""), bot_watch_T=s0.get("watchlist", ""), bot_nw_T=s0.get("near_watch", ""), bot_ready_T=s0.get("ready", ""))
        out.append(row)
    L.write_csv(os.path.join(HERE, "TEMPORAL_LEAD_TIME_ANALYSIS.csv"), out)
    summary = {}
    for sub, rows in (("ALL", out), ("NON_ANCHOR", [r for r in out if not r["ANCHOR"]]), ("FOCUS", [r for r in out if r["FAISAL_STATE"] == "FOCUS"]),
                      ("WATCH", [r for r in out if r["FAISAL_STATE"] == "WATCH"]), ("READY", [r for r in out if r["FAISAL_STATE"] == "READY"]),
                      ("ENTRY", [r for r in out if r["FAISAL_STATE"] == "ENTRY"])):
        rows20 = [r for r in rows if (r["n_after"] or 0) >= 20]
        summary[sub] = dict(n=len(rows), n_with_20_after=len(rows20),
                            hit_50_20=sum(1 for r in rows20 if r["MOVE_50_20"] == 1), hit_25_10=sum(1 for r in rows20 if r["MOVE_25_10"] == 1),
                            hit_100_20=sum(1 for r in rows20 if r["MOVE_100_20"] == 1),
                            lead_50=q([r["lead_sessions_to_50"] for r in rows20 if r["lead_sessions_to_50"] and r["lead_sessions_to_50"] <= 20]),
                            lead_25=q([r["lead_sessions_to_25"] for r in rows20 if r["lead_sessions_to_25"] and r["lead_sessions_to_25"] <= 10]),
                            lead_100=q([r["lead_sessions_to_100"] for r in rows20 if r["lead_sessions_to_100"] and r["lead_sessions_to_100"] <= 20]))
        for k in GRID:
            summary[sub][f"cand_T-{k}"] = sum(1 for r in rows if r[f"bot_cand_T-{k}"] == "1")
            summary[sub][f"watch_T-{k}"] = sum(1 for r in rows if r[f"bot_watch_T-{k}"] == "1")
        summary[sub]["cand_T"] = sum(1 for r in rows if r["bot_cand_T"] == "1"); summary[sub]["watch_T"] = sum(1 for r in rows if r["bot_watch_T"] == "1")
        summary[sub]["nw_T"] = sum(1 for r in rows if r["bot_nw_T"]); summary[sub]["ready_T"] = sum(1 for r in rows if r["bot_ready_T"] == "1")
        summary[sub]["gate_T"] = collections.Counter(r["bot_gate_T"] for r in rows if r["bot_cand_T"] == "0").most_common(6)
    json.dump(summary, open(os.path.join(L.OUT, "lead_time_summary.json"), "w"), ensure_ascii=False, indent=1)
    return out, summary


def runs(flags):
    """أطوالُ المقاطع المتتالية من 1 في متتالية."""
    out, cur = [], 0
    for f in flags:
        if f:
            cur += 1
        else:
            if cur:
                out.append(cur)
            cur = 0
    if cur:
        out.append(cur)
    return out


def persistence(obs, states):
    cal = L.calendar(); out = []
    by = collections.defaultdict(list)
    for r in obs:
        by[r["TICKER"]].append(r)
    for t, rs in sorted(by.items()):
        days = sorted({r["DATE"] for r in rs}); idx = [L.cal_index(d) for d in days]
        # ملاحظاتٌ متتالية = فرقٌ ≤ 3 جلسات (عطلاتٌ ونشرٌ غيرُ يوميّ)
        chains, cur = [], [idx[0]]
        for a, b in zip(idx, idx[1:]):
            if b - a <= 3:
                cur.append(b)
            else:
                chains.append(cur); cur = [b]
        chains.append(cur)
        seq = [r["OBSERVATION_CLASS"] for r in sorted(rs, key=lambda x: x["DATE"])]
        changes = sum(1 for a, b in zip(seq, seq[1:]) if a != b)
        span = idx[-1] - idx[0] + 1
        s_days = [d for d in cal if days[0] <= d <= days[-1]]
        cand = [int((states.get((t, d)) or {}).get("candidate", "0") or 0) for d in s_days]
        wl = [int((states.get((t, d)) or {}).get("watchlist", "0") or 0) for d in s_days]
        rd = [int((states.get((t, d)) or {}).get("ready", "0") or 0) for d in s_days]
        first_state = {s: min(r["DATE"] for r in rs if r["OBSERVATION_CLASS"] == s) for s in ACTIVE if any(r["OBSERVATION_CLASS"] == s for r in rs)}
        def gap(a, b):
            return (L.cal_index(first_state[b]) - L.cal_index(first_state[a])) if a in first_state and b in first_state else None
        out.append(dict(TICKER=t, ANCHOR=int(t in L.ANCHORS), n_obs=len(rs), n_days=len(days), first=days[0], last=days[-1], span_sessions=span,
                        max_consecutive_obs=max(len(c) for c in chains), n_chains=len(chains), n_state_changes=changes, state_sequence="→".join(seq),
                        sessions_in_FOCUS_or_WATCH=sum(1 for d in days if any(r["DATE"] == d and r["OBSERVATION_CLASS"] in ("FOCUS", "WATCH") for r in rs)),
                        watch_to_ready=gap("WATCH", "READY"), focus_to_watch=gap("FOCUS", "WATCH"), ready_to_entry=gap("READY", "ENTRY"), watch_to_entry=gap("WATCH", "ENTRY"),
                        bot_cand_days=sum(cand), bot_cand_max_run=max(runs(cand), default=0), bot_cand_runs=len(runs(cand)),
                        bot_watch_days=sum(wl), bot_watch_max_run=max(runs(wl), default=0), bot_ready_days=sum(rd), bot_ready_max_run=max(runs(rd), default=0),
                        bot_known_days=sum(1 for d in s_days if (t, d) in states)))
    L.write_csv(os.path.join(HERE, "TEMPORAL_PERSISTENCE_ANALYSIS.csv"), out)
    # استمرارُ البوت عمومًا (كلُّ الرموز في bot_states)
    allsym = collections.defaultdict(list)
    for (s, d), r in sorted(states.items()):
        allsym[s].append(r)
    cr, wr, rr = [], [], []
    for s, rs in allsym.items():
        cr += runs([int(r["candidate"]) for r in rs]); wr += runs([int(r["watchlist"]) for r in rs]); rr += runs([int(r["ready"]) for r in rs])
    summ = dict(faisal_max_consec_obs=q([r["max_consecutive_obs"] for r in out]), faisal_chains=q([r["n_chains"] for r in out]),
                faisal_span=q([r["span_sessions"] for r in out if r["n_days"] >= 2]), faisal_state_changes=q([r["n_state_changes"] for r in out]),
                watch_to_ready=q([r["watch_to_ready"] for r in out]), watch_to_entry=q([r["watch_to_entry"] for r in out]),
                bot_candidate_run=q(cr), bot_watchlist_run=q(wr), bot_ready_run=q(rr),
                multi_obs_tickers=sum(1 for r in out if r["n_days"] >= 2), tickers=len(out),
                multi_with_consec2=sum(1 for r in out if r["max_consecutive_obs"] >= 2))
    json.dump(summ, open(os.path.join(L.OUT, "persistence_summary.json"), "w"), ensure_ascii=False, indent=1)
    return out, summ


def first_divergence(obs, states):
    out = []; by = collections.defaultdict(list)
    for r in obs:
        by[r["TICKER"]].append(r)
    for t, rs in sorted(by.items()):
        rs = sorted(rs, key=lambda r: r["DATE"])
        first_f = rs[0]
        d = first_f["DATE"]; s0 = states.get((t, L.session(d))) or {}
        rep = any([s0.get("candidate") == "1", s0.get("watchlist") == "1", bool(s0.get("near_watch"))])
        # أوّلُ يوم (من −20 قبل أوّل دليل) كان فيه البوت مرشِّحًا/مراقِبًا
        pre = [L.shift(d, -k) for k in range(20, 0, -1)]
        d = L.session(d)
        bot_first_cand = next((p for p in pre + [d] if (states.get((t, p)) or {}).get("candidate") == "1"), "")
        bot_first_wl = next((p for p in pre + [d] if (states.get((t, p)) or {}).get("watchlist") == "1"), "")
        bot_first_nw = next((p for p in pre + [d] if (states.get((t, p)) or {}).get("near_watch")), "")
        bot_first_ready = next((p for p in pre + [d] if (states.get((t, p)) or {}).get("ready") == "1"), "")
        ready_rows = [r for r in rs if r["OBSERVATION_CLASS"] == "READY"]; entry_rows = [r for r in rs if r["OBSERVATION_CLASS"] == "ENTRY"]
        ready_mismatch = ""
        if ready_rows:
            sr = states.get((t, L.session(ready_rows[0]["DATE"]))) or {}
            ready_mismatch = f"Faisal READY {ready_rows[0]['DATE']} · bot ready={sr.get('ready','?')} cand={sr.get('candidate','?')} gate={sr.get('gate','')}"
        entry_mismatch = f"Faisal ENTRY {entry_rows[0]['DATE']} · bot has no entry state" if entry_rows else ""
        out.append(dict(TICKER=t, ANCHOR=int(t in L.ANCHORS), FIRST_FAISAL_STATE=first_f["OBSERVATION_CLASS"], FIRST_FAISAL_DATE=d, EVIDENCE=first_f["EVIDENCE_ID"],
                        BOT_CANDIDATE_ON_DATE=s0.get("candidate", "NA"), BOT_GATE_ON_DATE=s0.get("gate", ""), BOT_REASON_ON_DATE=s0.get("reason", ""),
                        BOT_WATCHLIST_ON_DATE=s0.get("watchlist", "NA"), BOT_NEAR_WATCH_ON_DATE=s0.get("near_watch", ""), BOT_READY_ON_DATE=s0.get("ready", "NA"),
                        FIRST_DATE_FAISAL_STATE_WITHOUT_BOT_REPRESENTATION=("" if rep else d),
                        BOT_FIRST_CANDIDATE_WITHIN_20_BEFORE=bot_first_cand, BOT_FIRST_WATCHLIST_WITHIN_20_BEFORE=bot_first_wl,
                        BOT_FIRST_NEAR_WATCH_WITHIN_20_BEFORE=bot_first_nw, BOT_FIRST_READY_WITHIN_20_BEFORE=bot_first_ready,
                        FIRST_CANDIDATE_REJECTION=(f"{s0.get('reason','')} on {d}" if s0.get("candidate") == "0" else ""),
                        FIRST_STRUCTURAL_MISMATCH=(s0.get("gate", "") if s0.get("candidate") == "0" else ""),
                        FIRST_STATE_MISMATCH=(f"Faisal {first_f['OBSERVATION_CLASS']} on {d}; bot cand={s0.get('candidate','NA')} wl={s0.get('watchlist','NA')} nw={s0.get('near_watch','')}" if not rep else ""),
                        FIRST_READINESS_MISMATCH=ready_mismatch, FIRST_ENTRY_MISMATCH=entry_mismatch, STATE_SEQUENCE="→".join(r["OBSERVATION_CLASS"] for r in rs),
                        BOT_STATES_KNOWN=int(bool(s0))))
    L.write_csv(os.path.join(HERE, "FIRST_DIVERGENCE_TEMPORAL_MATRIX.csv"), out)
    return out


def architecture(obs, states):
    """A: لقطةٌ يوميّة · B: ذاكرةُ مرشَّح N جلسات (PASS مرّةً خلال N يُبقيه «مرشَّحًا») — البوّاباتُ نفسُها بلا تغيير."""
    syms = sorted({s for s, _ in states})
    byS = collections.defaultdict(dict)
    for (s, d), r in states.items():
        byS[s][d] = int(r["candidate"])
    g = json.load(open(os.path.join(L.ROOT, "fm_forensics", "phase2", "out", "groups.json")))
    faisal_t = {r["TICKER"] for r in obs}; neg = [s for s in g.get("neg", []) if s in byS and s not in faisal_t]
    obs_keys = {(r["TICKER"], L.session(r["DATE"])) for r in obs}
    out = []
    for N in (1, 3, 5, 10, 15):
        neg_days = 0; neg_total = 0; obs_rep = 0; first_rep = 0
        for s in syms:
            dd = sorted(byS[s]); flags = [byS[s][d] for d in dd]
            mem = []
            run = 0
            for i, f in enumerate(flags):
                run = N if f else max(0, run - 1)
                mem.append(1 if run > 0 else 0)
            m = dict(zip(dd, mem))
            if s in neg:
                neg_days += sum(mem); neg_total += len(mem)
            for (t, d) in obs_keys:
                if t == s and d in m and m[d]:
                    obs_rep += 1
        by = collections.defaultdict(list)
        for r in obs:
            by[r["TICKER"]].append(r["DATE"])
        for t, ds in by.items():
            d0 = L.session(min(ds))
            if t in byS:
                dd = sorted(byS[t]); flags = [byS[t][d] for d in dd]; run = 0; m = {}
                for d, f in zip(dd, flags):
                    run = N if f else max(0, run - 1); m[d] = 1 if run > 0 else 0
                if m.get(d0):
                    first_rep += 1
        out.append(dict(ARCHITECTURE=("A_SNAPSHOT" if N == 1 else "B_MEMORY"), MEMORY_SESSIONS=N, FAISAL_OBS_DAYS=len(obs_keys), FAISAL_OBS_REPRESENTED=obs_rep,
                        FAISAL_TICKERS=len(by), FIRST_OBS_REPRESENTED=first_rep, NEG_CONTROL_DAYS=neg_total, NEG_CONTROL_CANDIDATE_DAYS=neg_days,
                        NEG_FALSE_POSITIVE_RATE=round(neg_days / max(1, neg_total), 3)))
    L.write_csv(os.path.join(HERE, "TEMPORAL_ARCHITECTURE_COMPARISON.csv"), out)
    return out


def controls(obs, states):
    g = json.load(open(os.path.join(L.ROOT, "fm_forensics", "phase2", "out", "groups.json")))
    by = collections.defaultdict(list)
    for r in obs:
        by[r["TICKER"]].append(r)
    pos = []
    for t, rs in sorted(by.items()):
        if any(r["OBSERVATION_CLASS"] in ("READY", "ENTRY") for r in rs):
            d = min(r["DATE"] for r in rs if r["OBSERVATION_CLASS"] in ("READY", "ENTRY"))
            first = min(r["DATE"] for r in rs)
            c = L.context(t, d) or {}
            s = states.get((t, L.session(d))) or {}
            o = L.outcomes(t, d) or {}
            pos.append(dict(TICKER=t, ANCHOR=int(t in L.ANCHORS), FIRST_OBS=first, READY_OR_ENTRY_DATE=d, SESSIONS_FROM_FIRST_OBS=L.cal_index(d) - L.cal_index(first),
                            BOT_CANDIDATE=s.get("candidate", "NA"), BOT_GATE=s.get("gate", ""), BOT_WATCHLIST=s.get("watchlist", "NA"), BOT_NEAR_WATCH=s.get("near_watch", ""), BOT_READY=s.get("ready", "NA"),
                            drop_pct=c.get("drop_pct"), spike_pct=c.get("spike_pct"), base_range_pct=c.get("base_range_pct"), tested_touches=c.get("tested_touches"), rsi14=c.get("rsi14"),
                            rsi_min25=c.get("rsi_min25"), bars_since_low30=c.get("bars_since_low30"), last_rsplit=c.get("last_rsplit"), drop_from_psh_pct=c.get("drop_from_psh_pct"),
                            gap_below_level=c.get("gap_below_level"), vs_ema30_pct=c.get("vs_ema30_pct"), MOVE_50_20=o.get("MOVE_50_20"), MOVE_25_10=o.get("MOVE_25_10")))
    L.write_csv(os.path.join(HERE, "POSITIVE_TEMPORAL_CONTROLS.csv"), pos)
    neg = []
    faisal_t = set(by)
    ready_days = json.load(open("/tmp/claude-0/-home-user-Super-Stocks/59271cc5-48be-5019-b321-70eeaec06f58/scratchpad/fm/ready_days.json"))
    for t in sorted(set(g.get("neg", [])) - faisal_t):
        ds = [d for (s, d) in states if s == t and states[(s, d)]["candidate"] == "1"]
        if not ds:
            continue
        d = min(ds); c = L.context(t, d) or {}; o = L.outcomes(t, d) or {}; s = states[(t, d)]
        neg.append(dict(TICKER=t, KIND="bot_candidate_no_faisal_evidence", DATE=d, BOT_CANDIDATE=1, BOT_WATCHLIST=s.get("watchlist"), BOT_READY=s.get("ready"),
                        drop_pct=c.get("drop_pct"), spike_pct=c.get("spike_pct"), base_range_pct=c.get("base_range_pct"), tested_touches=c.get("tested_touches"), rsi14=c.get("rsi14"),
                        rsi_min25=c.get("rsi_min25"), bars_since_low30=c.get("bars_since_low30"), last_rsplit=c.get("last_rsplit"), drop_from_psh_pct=c.get("drop_from_psh_pct"),
                        gap_below_level=c.get("gap_below_level"), vs_ema30_pct=c.get("vs_ema30_pct"), MOVE_50_20=o.get("MOVE_50_20"), MOVE_25_10=o.get("MOVE_25_10")))
    for t, ds in sorted(ready_days.items()):
        if t in faisal_t or t not in L.load()["daily"]:
            continue
        d = min(ds); c = L.context(t, d) or {}; o = L.outcomes(t, d) or {}; s = states.get((t, L.session(d))) or {}
        neg.append(dict(TICKER=t, KIND="bot_ready_no_faisal_evidence", DATE=d, BOT_CANDIDATE=s.get("candidate", "NA"), BOT_WATCHLIST=s.get("watchlist", "NA"), BOT_READY=1,
                        drop_pct=c.get("drop_pct"), spike_pct=c.get("spike_pct"), base_range_pct=c.get("base_range_pct"), tested_touches=c.get("tested_touches"), rsi14=c.get("rsi14"),
                        rsi_min25=c.get("rsi_min25"), bars_since_low30=c.get("bars_since_low30"), last_rsplit=c.get("last_rsplit"), drop_from_psh_pct=c.get("drop_from_psh_pct"),
                        gap_below_level=c.get("gap_below_level"), vs_ema30_pct=c.get("vs_ema30_pct"), MOVE_50_20=o.get("MOVE_50_20"), MOVE_25_10=o.get("MOVE_25_10")))
    L.write_csv(os.path.join(HERE, "NEGATIVE_TEMPORAL_CONTROLS.csv"), neg)
    return pos, neg


def main():
    states = load_states(); obs = faisal_obs()
    print("faisal active obs", len(obs), "tickers", len({r['TICKER'] for r in obs}), "bot_states", len(states))
    lt, s1 = lead_time(obs, states); print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk in ('n','n_with_20_after','hit_50_20','hit_25_10','hit_100_20','lead_50','lead_25','cand_T','watch_T','nw_T','ready_T','gate_T')} for k, v in s1.items()}, ensure_ascii=False, indent=0)[:3000])
    pe, s2 = persistence(obs, states); print(json.dumps(s2, ensure_ascii=False)[:1500])
    fd = first_divergence(obs, states); print("first divergence rows", len(fd), "no-rep", sum(1 for r in fd if r["FIRST_DATE_FAISAL_STATE_WITHOUT_BOT_REPRESENTATION"]))
    ar = architecture(obs, states); [print(r) for r in ar]
    pos, neg = controls(obs, states); print("pos", len(pos), "neg", len(neg))


if __name__ == "__main__":
    main()
