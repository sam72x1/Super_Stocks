"""🔬 PHASE 4 — اختبارا الميزتين (§18-19 · تشخيصٌ فقط · لا عتبةَ تُشتقّ) على كون حالات المرحلة الثالثة (95 رمزًا · كلُّ جلسةٍ من 2025-06-20):
الأيّامُ الأهلة بلا مرساة · «لمسةٌ أولى حديثة» = المستوى تكوّن خلال آخر 5 جلسات · «لمسةٌ ثانية» = tested_level≥2 عند T · «إعادةُ اختبار» = pivot_cycle_state stage≥3 عند T
⟵ احتمالُ وحدةِ فيصل مؤرَّخة (FOCUS/WATCH/READY/ENTRY) خلال 20 جلسةً بعد T (كشفٌ أماميّ بعد تجميد الحقول). و§21: التحوّلات بين حالات فيصل الموثَّقة."""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p4lib as P                        # noqa: E402

L = P.L
S = P.S


def main():
    rows = [r for r in P.faisal_timeline() if r["has_bars"]]
    by_t = collections.defaultdict(list)
    for r in rows:
        by_t[r["ticker"]].append(r)
    bs = P.bot_states()
    recs = []
    for (sym, day), g in bs.items():
        el = (g["result"] == "PASS") or (g["gate"] == "ANCHOR")
        if not el:
            continue
        lv = P.level_at(sym, day)
        if not lv:
            continue
        df = L.frame(L.bars_before(sym, day))
        pc = S.pivot_cycle_state(df)
        fut = [r for r in by_t.get(sym, []) if r["session"] > day and L.cal_index(r["session"]) - L.cal_index(day) <= 20]
        recs.append(dict(sym=sym, day=day, ft_recent=int(lv["sessions_since"] <= 5), e2=int(lv["touches"] >= 2), e3=int(bool(pc) and pc["stage"] >= 3 and abs(float(pc["bottom"]) - lv["level"]) <= 1e-4 * max(1.0, lv["level"])),
                         any_state=int(bool(fut)), watch=int(any(r["state"] in ("WATCH", "FOCUS") for r in fut)), ready=int(any(r["state"] == "READY" for r in fut)), entry=int(any(r["state"] == "ENTRY" for r in fut)),
                         faisal_ticker=int(sym in by_t)))
    out = []
    def block(name, flag, targets):
        for tgt in targets:
            a = [r for r in recs if r[flag] == 1]; b = [r for r in recs if r[flag] == 0]
            ka, kb = sum(r[tgt] for r in a), sum(r[tgt] for r in b)
            pa = ka / len(a) if a else None; pb = kb / len(b) if b else None
            out.append(dict(TEST=name, FEATURE=flag, TARGET=f"documented Faisal {tgt} within 20 sessions", PRESENT=f"{ka}/{len(a)}", P_PRESENT=round(pa, 4) if pa is not None else None,
                            WILSON_PRESENT=P.wilson(ka, len(a)), ABSENT=f"{kb}/{len(b)}", P_ABSENT=round(pb, 4) if pb is not None else None, WILSON_ABSENT=P.wilson(kb, len(b)),
                            RATIO=round(pa / pb, 2) if pa is not None and pb else None,
                            UNIVERSE="identity-eligible symbol-days (anchor neutral) of the 95-symbol bot_states universe from 2025-06-20; Faisal evidence sparse (41 tickers) — diagnostic only",
                            DIRECTION_NOTE="first touch is 'recent' when the 30-bar low formed within the last 5 sessions"))
    block("FIRST_TOUCH(§18)", "ft_recent", ("any_state", "watch", "ready", "entry"))
    block("SECOND_TOUCH_E2(§19)", "e2", ("ready", "entry", "any_state"))
    block("RETEST_E3(§19)", "e3", ("ready", "entry", "any_state"))
    L.write_csv(os.path.join(HERE, "FEATURE_TESTS.csv"), out)
    for r in out:
        print(r["TEST"], r["TARGET"], r["PRESENT"], r["P_PRESENT"], "vs", r["ABSENT"], r["P_ABSENT"], "ratio", r["RATIO"])
    print("eligible symbol-days", len(recs), "faisal-ticker days", sum(r["faisal_ticker"] for r in recs))

    # ---- §21 transitions from documented sequences (per ticker, chronological classes)
    seqs = {}
    for t, rs in by_t.items():
        seq = []
        for r in sorted(rs, key=lambda x: x["session"]):
            if not seq or seq[-1][1] != r["state"]:
                seq.append((r["session"], r["state"]))
        seqs[t] = seq
    trans = []
    for a, b in (("FOCUS", "WATCH"), ("WATCH", "READY"), ("READY", "ENTRY"), ("WATCH", "ENTRY"), ("FOCUS", "READY")):
        direct = [t for t, s in seqs.items() if any(s[i][1] == a and s[i + 1][1] == b for i in range(len(s) - 1))]
        b_without_a = [t for t, s in seqs.items() if any(x[1] == b for x in s) and not any(x[1] == a and x[0] <= min(y[0] for y in s if y[1] == b) for x in s)]
        n_b = [t for t, s in seqs.items() if any(x[1] == b for x in s)]
        trans.append(dict(TRANSITION=f"{a}→{b}", DIRECTLY_SUPPORTED_TICKERS=";".join(direct), N_DIRECT=len(direct), N_WITH_TARGET_STATE=len(n_b), TARGET_WITHOUT_PRECEDING=len(b_without_a),
                         TARGET_WITHOUT_PRECEDING_TICKERS=";".join(b_without_a), VERDICT=("CONFIRMED" if len(direct) >= 3 else ("MODIFIED" if direct else ("UNKNOWN" if n_b else "UNKNOWN"))),
                         NOTE="dated units only; 'without preceding' counts tickers whose first dated unit of the target state has no earlier dated unit of the preceding state (text may still describe it)"))
    L.write_csv(os.path.join(HERE, "TRANSITION_ANALYSIS.csv"), trans)
    for t in trans:
        print(t["TRANSITION"], t["N_DIRECT"], t["N_WITH_TARGET_STATE"], t["TARGET_WITHOUT_PRECEDING"])


if __name__ == "__main__":
    main()
