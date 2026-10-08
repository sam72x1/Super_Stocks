"""🔬 PHASE 3 — خطوطُ المراسي الزمنيّة (DKI/SXTC/HUBC + CRE) من T−20 إلى T+20 حول يوم المرجع (2026-09-11 = أوّلُ سجلّ رفضٍ محفوظ):
لكلّ جلسة: السعرُ والعائدُ والحجمُ والتذبذبُ والفجوةُ والبنيةُ من شموعٍ < اليوم · بوّاباتُ البوت اليوم (CURRENT) وأيُّ بوّابةٍ وحدَها
تُعيده مرشَّحًا (من LOGO) · حالتُه في القائمة/المتابعة/الجاهز (من bot_states) · ودليلُ فيصل المؤرَّخ في اليوم نفسِه وحدَه (HUBC: UNKNOWN)."""
import csv
import gzip
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p3lib as L                        # noqa: E402

REF = "2026-09-11"


def main():
    logo = {}
    for r in csv.DictReader(open(os.path.join(L.OUT, "logo_rows.csv"), encoding="utf-8")):
        if r["group"] == "anchor":
            logo[(r["symbol"], r["date"])] = r
    states = {}
    with gzip.open(os.path.join(L.OUT, "bot_states.csv.gz"), "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            states[(r["symbol"], r["date"])] = r
    ev = {}
    for r in csv.DictReader(open(os.path.join(HERE, "FAISAL_TIMELINE.csv"), encoding="utf-8")):
        if r["IS_FAISAL"] == "1":
            ev.setdefault((r["TICKER"], L.session(r["DATE"])), []).append(r)
    for sym in L.ANCHORS + [L.NEG_ANCHOR]:
        rows = []
        for k in range(-20, 21):
            d = L.shift(REF, k); c = L.context(sym, d) or {}; lg = logo.get((sym, d)) or {}; s = states.get((sym, d)) or {}
            e = ev.get((sym, d)) or []
            restores = [g for g in L.GATE_ORDER if lg.get(f"NO_{g}") == "PASS"]
            fstate = (sorted(x["FAISAL_STATE"] for x in e)[0] if e else ("UNKNOWN (no dated Faisal text)" if sym == "HUBC" else "UNKNOWN (no evidence this day)"))
            rows.append(dict(TICKER=sym, T_OFFSET=k, DATE=d, ASOF_BAR=c.get("asof"), price=c.get("price"), return_pct=c.get("ret1"), volume=c.get("volume"),
                             vol_ratio20=c.get("vol_ratio"), volatility_atr14_pct=c.get("atr14_pct"), gap_pct=c.get("gap_pct"),
                             structure=(f"hi52 {c.get('hi52')} drop {c.get('drop_pct')}% · spike {c.get('spike_pct')}% · base15 {c.get('base_range_pct')}% · low30 {c.get('low30')} (+{c.get('dist_low30_pct')}%, {c.get('bars_since_low30')}b) · touches {c.get('tested_touches')} · RSI {c.get('rsi14')} · EMA30 {c.get('vs_ema30_pct')}%"
                                        + (f" · rsplit {c.get('last_rsplit')} +{c.get('bars_since_split')}b PSH {c.get('post_split_high')} drop {c.get('drop_from_psh_pct')}%" if c.get("last_rsplit") else "")),
                             bot_result=lg.get("CURRENT", s.get("result", "")), bot_reject_reason=lg.get("CURRENT_reason", s.get("reason", "")), bot_first_gate=lg.get("CURRENT_gate", s.get("gate", "")),
                             gates_whose_removal_alone_restores=";".join(restores), all_identity_gates_off=lg.get("NO_ALL_IDENTITY", ""),
                             candidate=s.get("candidate", ""), watchlist=s.get("watchlist", ""), near_watch=s.get("near_watch", ""), ready=s.get("ready", ""),
                             FAISAL_EVIDENCE=";".join(x["EVIDENCE_ID"] for x in e), FAISAL_STATE=fstate,
                             CONFIDENCE=("DIRECT" if e else "NONE"), LOOKAHEAD_SAFE="YES (bars < DATE; evidence dated = DATE)"))
        L.write_csv(os.path.join(HERE, f"{sym}_TIMELINE.csv"), rows)
        print(sym, len(rows), "evidence days", sum(1 for r in rows if r["FAISAL_EVIDENCE"]), "candidate days", sum(1 for r in rows if r["candidate"] == "1"))


if __name__ == "__main__":
    main()
