"""🔬 PHASE 4 — الضوابطُ المطابَقة (§14 · الإجراءُ مجمَّدٌ في PHASE4_PREREG.md §⑦) تُبنى قبل أيّ نتيجةِ بنية:
لكلّ رمزِ فيصل ويومِ حالته الأولى D: مرشَّحون = رموزٌ بلا أيّ ذكرٍ لفيصل · أهلٌ بلا مرساة عند D · ≥120 شمعة · مطابَقون على دلاء
(السعر · ATR14% · حجمُ الدولار 20 · تقسيمٌ عكسيّ خلال 252) · الأقربُ في (log سعر · ATR · log حجم) حتى 4 · بلا إعادة استعمالٍ ما أمكن · بذرة 20261008."""
import collections
import math
import multiprocessing as mp
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p4lib as P                        # noqa: E402

L = P.L


def buckets(c):
    px = float(c["price"]); atr = c.get("atr14_pct"); dv = float(c.get("dollar_vol20") or 0)
    pb = "<1" if px < 1 else ("1-5" if px <= 5 else ">5")
    ab = "?" if atr is None else ("<8" if atr < 8 else ("8-15" if atr <= 15 else ">15"))
    db = "<50k" if dv < 5e4 else ("50k-500k" if dv <= 5e5 else ">500k")
    rs = int(bool(c.get("last_rsplit")) and (c.get("bars_since_split") or 9999) <= 252)
    return pb, ab, db, rs


def dist(a, b):
    la, lb = math.log(max(float(a["price"]), 1e-6)), math.log(max(float(b["price"]), 1e-6))
    da, db = math.log(max(float(a.get("dollar_vol20") or 1), 1)), math.log(max(float(b.get("dollar_vol20") or 1), 1))
    aa, ab = float(a.get("atr14_pct") or 0), float(b.get("atr14_pct") or 0)
    return ((la - lb) ** 2 + ((aa - ab) / 10.0) ** 2 + ((da - db) / 2.0) ** 2) ** 0.5


def _worker(args):
    sym, dates = args
    P.load_extra()
    out = []
    for d in dates:
        g = P.gate_row(sym, d)
        out.append((sym, d, g))
    return out


def main():
    rows = [r for r in P.faisal_timeline() if r["has_bars"]]
    fs = P.first_states(rows)
    all_faisal = {r["ticker"] for r in L.faisal_rows()} | set(fs)       # أيُّ ذكرٍ لفيصل (حتى MENTION) يُقصي الرمزَ من الضوابط
    pool = sorted(s for s in L.load()["daily"] if s not in all_faisal)
    dates = sorted({v["first_state"] for v in fs.values()})
    print("positives", len(fs), "dates", len(dates), "pool", len(pool))
    P.load_extra()
    need = [(s, [d for d in dates if (s, d) not in P.bot_states() and (s, d) not in P._EXTRA]) for s in pool]
    need = [(s, ds) for s, ds in need if ds]
    print("gate runs needed", sum(len(ds) for _, ds in need))
    if need:
        with mp.Pool(3) as pl:
            for res in pl.imap_unordered(_worker, need):
                for s, d, g in res:
                    P._EXTRA[(s, d)] = g
        P.save_extra()
    random.seed(20261008)
    used = collections.Counter()
    pos_rows, neg_rows = [], []
    for t in sorted(fs, key=lambda x: fs[x]["first_state"]):
        D = fs[t]["first_state"]
        c = L.context(t, D)
        if not c:
            pos_rows.append(dict(TICKER=t, SET=P.which_set(t), FIRST_STATE_DATE=D, FIRST_STATE_CLASS=fs[t]["first_state_class"], EVIDENCE_CLASS=fs[t]["first_state_evidence"],
                                 PRICE="", ATR14_PCT="", DOLLAR_VOL20="", RSPLIT_252="", BUCKETS="", N_CONTROLS=0, NOTE="no context (insufficient bars)"))
            continue
        pb = buckets(c)
        cands = []
        for s in pool:
            el, g = P.eligible(s, D)
            if not el:
                continue
            cs = L.context(s, D)
            if not cs or cs["bars"] < S_MIN_BARS():
                continue
            cb = buckets(cs)
            quality = 4 - sum(1 for i in range(4) if cb[i] != pb[i])
            cands.append((quality, used[s], dist(c, cs), s, cs, cb))
        cands.sort(key=lambda x: (-x[0], x[1], x[2]))
        chosen = cands[:4]
        for quality, _, dd, s, cs, cb in chosen:
            used[s] += 1
            neg_rows.append(dict(CONTROL=s, MATCHED_POSITIVE=t, SET=P.which_set(t), DATE=D, PRICE=cs["price"], ATR14_PCT=cs["atr14_pct"], DOLLAR_VOL20=cs["dollar_vol20"],
                                 RSPLIT_252=cb[3], BUCKETS="|".join(map(str, cb)), POSITIVE_BUCKETS="|".join(map(str, pb)), MATCH_QUALITY_OF_4=quality, DISTANCE=round(dd, 3),
                                 ELIGIBLE_NO_ANCHOR_AT_DATE=1, CURRENT_RESULT=P.gate_row(s, D)["result"], CURRENT_GATE=P.gate_row(s, D)["gate"],
                                 FAISAL_EVIDENCE="NONE (no dated or undated Faisal unit for this symbol)", SELECTION="pre-registered procedure §⑦ · seed 20261008"))
        pos_rows.append(dict(TICKER=t, SET=P.which_set(t), FIRST_STATE_DATE=D, FIRST_STATE_CLASS=fs[t]["first_state_class"], EVIDENCE_CLASS=fs[t]["first_state_evidence"],
                             PRICE=c["price"], ATR14_PCT=c["atr14_pct"], DOLLAR_VOL20=c["dollar_vol20"], RSPLIT_252=pb[3], BUCKETS="|".join(map(str, pb)), N_CONTROLS=len(chosen),
                             N_FULL_MATCH=sum(1 for x in chosen if x[0] == 4), ELIGIBLE_NO_ANCHOR_AT_DATE=int(P.eligible(t, D)[0]), REACHED_READY_OR_ENTRY=int(t in P.POSITIVE_CONTROLS or t == "SXTC"),
                             NOTE=""))
    L.write_csv(os.path.join(HERE, "POSITIVE_VALIDATION_CASES.csv"), pos_rows)
    L.write_csv(os.path.join(HERE, "NEGATIVE_VALIDATION_CASES.csv"), neg_rows)
    print("controls", len(neg_rows), "full-match", sum(1 for r in neg_rows if r["MATCH_QUALITY_OF_4"] == 4), "distinct", len({r["CONTROL"] for r in neg_rows}))
    # eligibility windows for the controls (sessions from first touch of LEVEL(D) up to D) — needed by the architectures
    need2 = collections.defaultdict(list)
    for r in neg_rows:
        lv = P.level_at(r["CONTROL"], r["DATE"])
        if not lv:
            continue
        for d in L.load()["daily"][r["CONTROL"]]:
            pass
        ds = [L.shift(x, 1) for x in P.sym_sessions_after(r["CONTROL"], lv["first_touch"], P.E2_MAX + 1)]
        ds = [x for x in ds if x <= r["DATE"] and (r["CONTROL"], x) not in P.bot_states() and (r["CONTROL"], x) not in P._EXTRA]
        need2[r["CONTROL"]].extend(ds)
    need2 = [(s, sorted(set(ds))) for s, ds in need2.items() if ds]
    print("window gate runs needed", sum(len(ds) for _, ds in need2))
    if need2:
        with mp.Pool(3) as pl:
            for res in pl.imap_unordered(_worker, need2):
                for s, d, g in res:
                    P._EXTRA[(s, d)] = g
        P.save_extra()


def S_MIN_BARS():
    return int(P.S.CONFIG["MIN_BARS"])


if __name__ == "__main__":
    main()
