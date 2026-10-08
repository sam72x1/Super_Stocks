"""🔬 PHASE 3 — خطُّ فيصل الزمنيّ من الأدلّة المؤرَّخة وحدَها (بلا نظرٍ للأمام):
FAISAL_TIMELINE.csv = صفٌّ لكلّ ملاحظةٍ (رمز، يوم، دليل) بصنفها وسياقِ السوق **قبل** يومها.
FAISAL_DAILY_TIMELINE.csv = للرموز ذات الملاحظتين فأكثر والمراسي: صفٌّ لكلّ جلسةٍ من −20 إلى +20 حول أوّل/آخر ملاحظة —
الحالةُ تُكتب في يوم الدليل وحدَه، وما بينها «UNKNOWN» مع `last_known_state` منفصلًا (لا يُفرَض استمرار)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p3lib as L                        # noqa: E402

FOCUS_LIST_0913 = ["SXTC", "MSGY", "DKI", "CUPR", "YMT", "CETX", "ATPC", "SVRE"]
CONF = {"READY": "DIRECT", "ENTRY": "DIRECT", "EXIT": "DIRECT", "WATCH": "DIRECT", "FOCUS": "DIRECT", "MENTION": "DIRECT", "UNKNOWN": "INSUFFICIENT"}


def ev_type(image):
    if image.startswith("X_"):
        return "X_POST"
    if image.startswith("TG_") or image.startswith("WA_"):
        return "TELEGRAM"
    if image.startswith("IMG_"):
        return "CHART_IMAGE"
    if image.startswith("APP_"):
        return "APP_SCREENSHOT"
    if image.startswith("EDU_"):
        return "EDU_CHANNEL"
    return "OTHER"


def obs_rows():
    rows = [dict(r) for r in L.faisal_rows()]
    for t in FOCUS_LIST_0913:
        rows.append(dict(image="X_20260918_23_watchlist", ticker=t, date="2026-09-13", author="F", is_faisal=True, decision="FOCUS_LIST",
                         role="VALIDATION_CASE", note="in Faisal app tab «قائمتي»", gist="app list tab", state="FOCUS"))
    rows.sort(key=lambda r: (r["ticker"], r["date"], r["image"]))
    return rows


def main():
    obs = obs_rows(); daily = L.load()["daily"]
    out = []
    for r in obs:
        c = L.context(r["ticker"], r["date"]) if r["ticker"] in daily else None
        st = r["state"] if r["is_faisal"] else ("MENTION" if r["state"] == "MENTION" else r["state"])
        if not r["is_faisal"]:
            conf = "THIRD_PARTY"
        else:
            conf = CONF.get(st, "INSUFFICIENT")
        out.append(dict(TICKER=r["ticker"], DATE=r["date"], FAISAL_STATE=st if r["is_faisal"] else "UNKNOWN",
                        OBSERVATION_CLASS=st, EVIDENCE_ID=r["image"], EVIDENCE_TYPE=ev_type(r["image"]),
                        AUTHOR=r["author"], IS_FAISAL=int(bool(r["is_faisal"])), DIRECT_OR_INFERRED="DIRECT" if r["is_faisal"] else "THIRD_PARTY",
                        PRICE_CONTEXT=(f"close(T−1) {c['price']} · ret1 {c['ret1']}% · ret5 {c['ret5']}% · vs EMA30 {c['vs_ema30_pct']}%" if c else "NO_BARS"),
                        STRUCTURAL_CONTEXT=(f"hi52 {c['hi52']} · drop {c['drop_pct']}% · spike {c['spike_pct']}% · base15 {c['base_range_pct']}% · low30 {c['low30']} ({c['bars_since_low30']}b ago, +{c['dist_low30_pct']}%) · touches {c['tested_touches']}"
                                            + (f" · rsplit {c['last_rsplit']} (+{c['bars_since_split']}b · PSH {c['post_split_high']} · drop {c['drop_from_psh_pct']}%)" if c and c["last_rsplit"] else "") if c else "NO_BARS"),
                        VOLUME_CONTEXT=(f"vol {c['volume']:.0f} · ratio20 {c['vol_ratio']} · $vol20 {c['dollar_vol20']:.0f}" if c else "NO_BARS"),
                        GAP_CONTEXT=(f"open gap {c['gap_pct']}% · unfilled gap-below top {c['gap_below_level']}" if c else "NO_BARS"),
                        INDICATOR_CONTEXT=(f"RSI14 {c['rsi14']} · RSI min25 {c['rsi_min25']} · ATR14 {c['atr14_pct']}%" if c else "NO_BARS"),
                        ACTION={"READY": "declared ready", "ENTRY": "entered/holds", "EXIT": "exited/rejected", "WATCH": "wait/plan", "FOCUS": "in focus list",
                                "MENTION": "mention/chart only", "UNKNOWN": "unclear"}.get(st, ""),
                        CONFIDENCE=conf, LOOKAHEAD_SAFE="YES (bars < DATE; evidence dated ≤ DATE)", DECISION_RAW=r.get("decision", ""),
                        GIST=(r.get("gist") or r.get("note") or "")[:160].replace("\n", " ")))
    L.write_csv(os.path.join(HERE, "FAISAL_TIMELINE.csv"), out)
    # daily timelines
    by = {}
    for r in out:
        if r["IS_FAISAL"] and r["OBSERVATION_CLASS"] != "MENTION":
            by.setdefault(r["TICKER"], []).append(r)
    multi = {t: v for t, v in by.items() if len({x["DATE"] for x in v}) >= 2 or t in L.ANCHORS}
    drows = []
    for t, v in sorted(multi.items()):
        if t not in daily:
            continue
        d0 = L.shift(min(x["DATE"] for x in v), -20); d1 = L.shift(max(x["DATE"] for x in v), 20)
        cal = [d for d in L.calendar() if d0 <= d <= d1]
        ev = {}
        for x in v:
            ev.setdefault(x["DATE"], []).append(x)
        last = "UNKNOWN"
        for d in cal:
            c = L.context(t, d)
            e = ev.get(d)
            if e:
                order = ["ENTRY", "READY", "FOCUS", "WATCH", "EXIT", "UNKNOWN"]
                st = sorted((x["OBSERVATION_CLASS"] for x in e), key=lambda s: order.index(s) if s in order else 9)[0]
                last = st
            else:
                st = "UNKNOWN"
            drows.append(dict(TICKER=t, DATE=d, FAISAL_STATE=st, LAST_KNOWN_STATE=last, EVIDENCE_ID=";".join(x["EVIDENCE_ID"] for x in (e or [])),
                              price=c and c["price"], ret1=c and c["ret1"], volume=c and c["volume"], vol_ratio=c and c["vol_ratio"],
                              atr14_pct=c and c["atr14_pct"], gap_pct=c and c["gap_pct"], drop_pct=c and c["drop_pct"], spike_pct=c and c["spike_pct"],
                              base_range_pct=c and c["base_range_pct"], low30=c and c["low30"], bars_since_low30=c and c["bars_since_low30"],
                              tested_touches=c and c["tested_touches"], rsi14=c and c["rsi14"], vs_ema30_pct=c and c["vs_ema30_pct"],
                              last_rsplit=c and c["last_rsplit"], drop_from_psh_pct=c and c["drop_from_psh_pct"], gap_below_level=c and c["gap_below_level"],
                              LOOKAHEAD_SAFE="YES"))
    L.write_csv(os.path.join(HERE, "FAISAL_DAILY_TIMELINE.csv"), drows)
    import collections
    print("observations", len(out), "faisal", sum(r["IS_FAISAL"] for r in out), collections.Counter(r["OBSERVATION_CLASS"] for r in out if r["IS_FAISAL"]))
    print("tickers", len({r["TICKER"] for r in out}), "with bars", len({r["TICKER"] for r in out if r["TICKER"] in daily}),
          "no bars:", sorted({r["TICKER"] for r in out if r["TICKER"] not in daily}))
    print("daily timelines", len(multi), "tickers", len(drows), "rows")


if __name__ == "__main__":
    main()
