#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🗂️🔬 `T-CASE31` — مجتمعُ الذراع ب (العقد §②): إدخالاتُ CURRENT في شرائح `T-BASKET` لـ2023-2025 بشموع TradingView.

- `collect`: الإدخالات (رمز، يوم) من الشرائح ⟵ شموعُ رموزها (يوميّ و4 ساعات) وتقسيماتُ ياهو وملفّاتُ FINRA ⟵ الخطّة: أحداثُ ‏+100% بتعريف ⓪-ب التي
  يومُ قرارها داخل نافذة عضويّة (من يوم الإدخال إلى 20 جلسةً بعده) · وضابطةُ كلّ يوم قرار = بقيّةُ الأعضاء فيه.
- `feat k n`: سماتُ الشموع وحدَها (`AB` في الفهرس) لكلّ (عضو، يوم قرار) كما كانت عند ذلك اليوم.
قراءةٌ فقط · لا Polygon · لا تلغرام · **ولا صفَّ بيوم قرارٍ بعد 2025-12-31** (صفوفُ 2026 للتأكيد بعد التثبيت وحدَه).
"""
import bisect
import glob
import gzip
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (HERE, ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import case31 as C                      # noqa: E402
import case31_build as B                # noqa: E402
import case31_catalog as CAT            # noqa: E402

YEARS = ("2023", "2024", "2025")
B_FROM, B_TO = "2023-01-01", "2025-12-31"
MEMBER_WIN = 20                         # العضويّة: من يوم الإدخال إلى 20 جلسةً بعده (العقد §②)
LIST = "CURRENT"
DATA_B = os.path.join(ROOT, "case31_data_b")
FEAT_B = os.path.join(ROOT, "case31_feat_b")
TV_D_N = 1500                           # ‏≈6 سنوات يوميّة: تكفي 520 شمعةً قبل أوّل إدخالٍ في 2023
TV_H4_N = 5000                          # أقصى ما يُطلب من 4 ساعات الممتدّة · ما لا يغطّيه «غير مقيس»
SH_BACK = 20                            # ملفّاتُ FINRA: 20 جلسةً حتى يوم القرار (تكفي نسبة 10 جلسات وتغيّرَ 5 و10)


def log(m=""):
    print(m, flush=True)


def entries_from_shards(d_in):
    """الإدخالاتُ (رمز، يوم) لقائمة CURRENT في السنوات الثلاث من شرائح `T-BASKET` · بلا تكرار."""
    out = set()
    for p in sorted(glob.glob(os.path.join(d_in, "**", "basket_shard_*.json.gz"), recursive=True)):
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            js = json.load(fh)
        for r in js.get("recs") or []:
            if LIST in (r.get("lists") or []) and str(r.get("y")) in YEARS and r.get("sym") and r.get("d"):
                out.add((str(r["sym"]).upper(), str(r["d"])))
    return sorted(out)


def membership(entries, sessions):
    """(نقيّة) ⟵ {رمز: [(أوّلُ جلسة، آخرُ جلسة)]}: نافذةُ كلّ إدخالٍ من يومه إلى `MEMBER_WIN` جلسةً بعده على تقويم `sessions` المرتّب."""
    out = {}
    for sym, d in entries:
        i = bisect.bisect_left(sessions, d)
        if i >= len(sessions):
            continue
        j = min(len(sessions) - 1, i + MEMBER_WIN)
        out.setdefault(sym, []).append((sessions[i], sessions[j]))
    return out


def is_member(mem, sym, day):
    return any(a <= day <= z for a, z in mem.get(sym, ()))


def plan_b(mem, rows_by, splits_by, sessions):
    """(نقيّة) ⟵ {events, days, members, stat}: أحداثُ ‏+100% (⓪-ب) بيوم قرارٍ داخل نافذة عضويّة وفي [B_FROM، B_TO] بعد قاعدة الإسقاط (أ)."""
    events, stat = [], {"symbols": len(mem), "no_bars": 0, "x100_any": 0, "outside_membership": 0, "dropped": 0}
    for sym in sorted(mem):
        rows = rows_by.get(sym)
        if not rows:
            stat["no_bars"] += 1
            continue
        for e in C.find_events(rows, B_FROM, sessions[-1] if sessions else B_TO, 2.0):
            if C.event_class(e) != "x100":
                continue
            stat["x100_any"] += 1
            if not (B_FROM <= e["D"] <= B_TO and is_member(mem, sym, e["D"])):
                stat["outside_membership"] += 1
                continue
            why, _src = C.drop_reason(e, "x100", rows, None, splits_by.get(sym) or [], lo=B_FROM, hi=sessions[-1] if sessions else B_TO)
            if why:
                stat["dropped"] += 1
                continue
            events.append({"sym": sym, "cls": "x100", "win": "B", "D": e["D"], "s": e["s"], "p": e["p"], "b": e["b"], "close_D": e["close_D"],
                           "top": e["top"], "low": e["low"], "gov": e["gov"], "one_day": C.one_day(e, rows), "one_candle": e["one_candle"],
                           "sessions": e["sessions"], "rs_recent": C.rs_recent(splits_by.get(sym) or [], e["D"]) if splits_by.get(sym) is not None else None,
                           "cat": {"status": "غير مقيس"}})
    days = sorted({e["D"] for e in events})
    members = {d: sorted(s for s in mem if is_member(mem, s, d)) for d in days}
    stat.update(events=len(events), days=len(days), rows=sum(len(v) for v in members.values()))
    return {"events": events, "days": days, "members": members, "stat": stat}


def mode_collect(d_in):
    import Super_stock as S
    import tv_data as TV
    entries = entries_from_shards(d_in)
    if not entries:
        log(f"⛔ لا إدخالاتِ CURRENT في الشرائح — خروج {C.RC_DATA}")
        return C.RC_DATA
    syms = sorted({s for s, _d in entries})
    log(f"🧺 الذراع ب: إدخالات {len(entries):,} · رموز {len(syms):,}")
    tmap = S._tv_ticker_map() or {}
    bars_d = B.tv_frames(syms + ["AAPL", "MSFT"], tmap, "1D", TV_D_N, False)
    log(f"📺 يوميّ {len(bars_d)}/{len(syms) + 2}")
    sessions = sorted({TV.ny_day(b[0]) for s in ("AAPL", "MSFT") for b in bars_d.get(s, [])})
    rows_by = {s: [(TV.ny_day(b[0]), b[1], b[2], b[3], b[4], b[5]) for b in bars_d[s]] for s in syms if bars_d.get(s)}
    splits = {}
    for j, s in enumerate(sorted(rows_by)):
        splits[s] = C.yahoo_splits(s)
        if j % 200 == 0:
            log(f"   … تقسيماتُ ياهو {j + 1}/{len(rows_by)}")
    mem = membership(entries, sessions)
    plan = plan_b(mem, rows_by, splits, sessions)
    log("🗂️ الخطّة: " + json.dumps(plan["stat"], ensure_ascii=False))
    need = sorted({s for v in plan["members"].values() for s in v})
    bars_h4 = B.tv_frames(need, tmap, "240", TV_H4_N, True)
    log(f"📺 4 ساعات {len(bars_h4)}/{len(need)}")
    fin_days = set()
    for d in plan["days"]:
        i = sessions.index(d)
        fin_days |= set(sessions[max(0, i - SH_BACK):i + 1])
    finra, need_set = {}, set(need)
    for j, d in enumerate(sorted(fin_days)):
        m = B.finra_day(d)
        finra[d] = {s: m[s] for s in need_set if s in m}
        if j % 100 == 0:
            log(f"   … FINRA {j + 1}/{len(fin_days)}")
    os.makedirs(DATA_B, exist_ok=True)
    keep = B.DATA
    try:
        B.DATA = DATA_B
        B._dump("plan.pkl.gz", {"plan": plan, "all_days": sessions, "entries": entries, "membership": mem})
        B._dump("bars_d.pkl.gz", {s: bars_d[s] for s in need if s in bars_d})
        B._dump("bars_h4.pkl.gz", bars_h4)
        B._dump("meta.pkl.gz", {"splits": splits, "finra": finra})
    finally:
        B.DATA = keep
    h4_first = sorted(TV.ny_day(v[0][0]) for v in bars_h4.values() if v)
    cov = dict(plan["stat"], entries=len(entries), daily=len(rows_by), h4=len(bars_h4), need=len(need),
               splits=sum(1 for v in splits.values() if v is not None), finra_days=sum(1 for d in finra if finra[d]), finra_need=len(fin_days),
               h4_first_median=h4_first[len(h4_first) // 2] if h4_first else None, sessions=[sessions[0], sessions[-1]] if sessions else None,
               events_by_year={y: sum(1 for e in plan["events"] if e["D"][:4] == y) for y in YEARS})
    os.makedirs(C.OUT, exist_ok=True)
    with open(os.path.join(C.OUT, "collect_b_coverage.json"), "w", encoding="utf-8") as fh:
        json.dump(cov, fh, ensure_ascii=False, indent=1)
    log("🧾 تغطيةُ الذراع ب: " + json.dumps(cov, ensure_ascii=False))
    return C.RC_OK


def mode_feat(k, n, d_in):
    import pandas as pd
    import case31_feat as F
    import tv_data as TV
    P, meta = B._load(d_in, "plan.pkl.gz"), B._load(d_in, "meta.pkl.gz")
    bars_d, bars_h4 = B._load(d_in, "bars_d.pkl.gz"), B._load(d_in, "bars_h4.pkl.gz")
    if not P or meta is None or bars_d is None:
        log(f"⛔ مادّةُ الذراع ب ناقصة — خروج {C.RC_DATA}")
        return C.RC_DATA
    plan, all_days = P["plan"], P["all_days"]
    ev_by = {(e["sym"], e["D"]): e for e in plan["events"]}
    jobs = {}
    for d, ms in plan["members"].items():
        if d > B_TO:                                              # 🔒 لا صفَّ بعد 2025
            continue
        for s in ms:
            jobs.setdefault(s, set()).add(d)
    mine = sorted(s for s in jobs if (sum(map(ord, s)) % n) == k)
    out, t0 = [], time.time()
    for j, s in enumerate(mine):
        rd = bars_d.get(s)
        if not rd:
            out += [{"sym": s, "D": d, "ok": False, "why": "بلا شموعٍ يوميّة"} for d in sorted(jobs[s])]
            continue
        rows_d = [(TV.ny_day(b[0]), b[1], b[2], b[3], b[4], b[5]) for b in rd]
        dfD = pd.DataFrame([r[1:] for r in rows_d], columns=["Open", "High", "Low", "Close", "Volume"], index=pd.to_datetime([r[0] for r in rows_d]))
        rh = (bars_h4 or {}).get(s) or []
        dfH = pd.DataFrame([b[1:] for b in rh], columns=["Open", "High", "Low", "Close", "Volume"],
                           index=pd.to_datetime([TV.ny_time(b[0]).replace(tzinfo=None) for b in rh])) if rh else None
        days_s = [r[0] for r in rows_d]
        vol_by = {r[0]: r[5] for r in rows_d}
        for d in sorted(jobs[s]):
            if d not in vol_by:
                out.append({"sym": s, "D": d, "ok": False, "why": "لا شمعةَ يومَ القرار"})
                continue
            i = days_s.index(d)
            rf = B.raw_factor(meta["splits"].get(s), d)
            f = F.with_deltas(dfD, dfH, d, rf)
            f.update(B.short_features(meta["finra"], s, d, all_days, vol_by))
            for kk in (5, 10):
                dprev = B.sessions_before(all_days, d, kk)
                sp = B.short_features(meta["finra"], s, dprev, all_days, vol_by) if dprev else {}
                for nm in ("sh.ratio_d", "sh.ratio5", "sh.ratio10", "sh.vol_d"):
                    a, b = f.get(nm), sp.get(nm)
                    f[f"{nm}.d{kk}"] = (a - b) if a is not None and b is not None else None
            x, n_after, ret = B.label(rows_d, d)
            e = ev_by.get((s, d))
            rec = {"sym": s, "D": d, "ok": True, "x20": x, "after": n_after, "ret": ret, "ev": ("x100", "B") if e else None, "in_pool": True, "f": f}
            if e:
                rec["lead"] = [F.with_deltas(dfD, dfH, days_s[i - q], rf) for q in range(1, B.LEAD_MAX + 1) if i - q >= 80]
                lo_i = days_s.index(e["s"]) if e["s"] in vol_by else i + 1
                rec["dd_before"] = (min(r[3] for r in rows_d[i + 1:lo_i + 1]) / rows_d[i + 1][1] - 1.0) if lo_i > i and rows_d[i + 1][1] > 0 else None
            out.append(rec)
        if j % 20 == 0:
            log(f"   … {j + 1}/{len(mine)} رمزًا · {len(out)} صفًّا · {time.time() - t0:.0f}ث")
    os.makedirs(FEAT_B, exist_ok=True)
    with gzip.open(os.path.join(FEAT_B, f"feat_{k}.json.gz"), "wt", encoding="utf-8") as fh:
        json.dump({"shard": k, "of": n, "rows": out, "catalog_sha": CAT.sha(), "arm": "B"}, fh, ensure_ascii=False)
    if k == 0:
        with open(os.path.join(FEAT_B, "plan_events.json"), "w", encoding="utf-8") as fh:
            json.dump(plan["events"], fh, ensure_ascii=False)
    log(f"🧮 ب الشريحة {k}/{n}: {len(mine)} رمزًا · {len(out)} صفًّا · سليم {sum(1 for r in out if r.get('ok'))}")
    return C.RC_OK


def main(argv):
    if not C.contract_ok():
        log(f"⛔ العقدُ أو الفهرسُ لا يطابق بصمتَه — خروج {C.RC_CONTRACT}")
        return C.RC_CONTRACT
    os.environ.pop("POLYGON_API_KEY", None)
    mode = argv[1] if len(argv) > 1 else ""
    d_in = argv[argv.index("--dir") + 1] if "--dir" in argv else "."
    if mode == "collect":
        return mode_collect(d_in)
    if mode == "feat":
        return mode_feat(int(argv[2]), int(argv[3]), d_in)
    log("الاستعمال: case31_b.py collect --dir <الشرائح> | feat <k> <n> --dir <المادّة>")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
