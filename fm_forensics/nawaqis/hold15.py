#!/usr/bin/env python3
"""⏱️ `T-HOLD15` «الدخولُ بعد صمود ربع الساعة» (المعلّقات ②-6 · العقد `T_HOLD15_prereg.md`).

  shard <k> --dir D     — أيّامُ الشريحة k من 40 (2023-2025): المرشّحون ⟵ `xmove_fire` بالاسم ⟵ H15 وC0 وCR بالأذرع الثلاثة.
  assemble --dir D      — الحكمُ بالأضعف ⟵ `T_HOLD15_RESULT.md`.
🔒 محورُ الخروج مُغلَق: تخرج 8 ما لم يكن `TRAIL_REOPEN == "1"` (إقرارُ المالك لهذه القراءة وحدَها). قراءةٌ فقط · لا تلغرام · لا إنتاج.
الأسعارُ **خامٌ** كلُّها (الدقائقُ والإغلاقُ اليوميّ) ⟵ يومٌ نُفّذ فيه تقسيمٌ يُتخطّى ويُعَدّ.
"""
import glob
import gzip
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import filter_core as FC                                         # noqa: E402
import tbook as TB                                               # noqa: E402

CONTRACT = os.path.join(HERE, "T_HOLD15_prereg.md")
CONTRACT_SHA = "b78571a90a47f429c688edf19a281ce1564fb0f670684b32671d7d8e46fe4291"
RESULT = os.path.join(HERE, "T_HOLD15_RESULT.md")
REOPEN_ENV = "TRAIL_REOPEN"
HOLD_MIN = 15
RETEST = 1.03
STOPS = (0.04, 0.10, 0.20)
T1, T2 = 1.20, 1.50
COST = 0.018
FILL_USD = 5000.0
CLOSE_MIN = 16 * 60
DAYS = ("2023-01-03", "2025-12-31")
RC_OK, RC_KEY, RC_POP, RC_CLOSED, RC_CONTRACT = 0, 2, 5, 8, 11


def log(m=""):
    print(m, flush=True)


def contracts_ok():
    return FC.sha_of(CONTRACT) == CONTRACT_SHA and FC.sha_of(FC.PROTOCOL) == TB.PROTOCOL_SHA


def reopened(env=None):
    return (os.environ if env is None else env).get(REOPEN_ENV, "") == "1"


def h15_entry(mins, fi, P, hold=HOLD_MIN, retest=RETEST, close_min=CLOSE_MIN):
    """(نقيّة) mins = [(ms، دقيقةُ نيويورك، o، h، l، c، v)] · fi = موضعُ دقيقة الإشعار ⟵ (موضعُ الدخول، السعر، الحالة)."""
    hold_bars = [b for b in mins[fi + 1:fi + 1 + hold] if b[1] < close_min]
    if len(hold_bars) < hold or any(b[5] < P for b in hold_bars):
        return None, None, "no_hold"
    for j in range(fi + 1 + hold, len(mins)):
        b = mins[j]
        if b[1] >= close_min:
            break
        if b[4] <= retest * P:
            return j, min(b[2], retest * P), "ok"
    return None, None, "no_retest"


def exit_sim(mins, ei, E, stop, fill_ok, close_min=CLOSE_MIN, cost=COST):
    """(نقيّة) الخروجُ من الدقيقة التالية للدخول ⟵ العائدُ بعد التكلفة (نسبة)."""
    st, rem, got, half = E * (1 - stop), 1.0, 0.0, False
    last = E
    for b in mins[ei + 1:]:
        if b[1] >= close_min:
            break
        ms, _m, o, h, lo, c, _v = b
        last = c
        if lo <= st:
            got += rem * min(o, st) / E
            rem = 0.0
            break
        if not half and h >= T1 * E and fill_ok(ms, T1 * E):
            got += 0.5 * T1
            rem, half = 0.5, True
        if half and h >= T2 * E and fill_ok(ms, T2 * E):
            got += rem * T2
            rem = 0.0
            break
    got += rem * last / E
    return got - 1.0 - cost


def rand_index(sym, day, fi, n_until):
    """(نقيّة) دقيقةٌ حتميّةٌ بين fi+1 وn_until−1 (‏sha256)."""
    span = n_until - (fi + 1)
    if span <= 0:
        return None
    return fi + 1 + int(hashlib.sha256(f"{sym}|{day}".encode()).hexdigest(), 16) % span


def run_fire(sym, day, mins, fire, fill_ok):
    fi = next((i for i, b in enumerate(mins) if b[0] == fire["ms"]), None)
    if fi is None:
        return {"st": "nobar"}
    P = float(fire["px"])
    n_until = sum(1 for b in mins if b[1] < CLOSE_MIN)
    ei, E, st = h15_entry(mins, fi, P)
    ri = rand_index(sym, day, fi, n_until)
    out = {"st": st, "P": P, "m": fire["m"]}
    for s in STOPS:
        tag = f"{int(s * 100)}"
        out[f"C0_{tag}"] = exit_sim(mins, fi, P, s, fill_ok)
        out[f"CR_{tag}"] = exit_sim(mins, ri, mins[ri][5], s, fill_ok) if ri is not None else None
        out[f"H_{tag}"] = exit_sim(mins, ei, E, s, fill_ok) if ei is not None else None
    return out


def mode_shard(key, k, d_in):
    import market_calendar as MC
    os.environ["FAISAL_ONLY"] = "0"
    import Super_stock as S
    B = FC._basket()
    prep = B._jload(glob.glob(os.path.join(d_in, "**", "basket_rbprep.json.gz"), recursive=True)[0])
    sess = TB._sessions("2022-12-15", DAYS[1], MC)
    days = [d for d in sess if DAYS[0] <= d <= DAYS[1]][k::FC.NSHARDS]
    prev_of = {sess[i]: sess[i - 1] for i in range(1, len(sess))}
    recs, why, t0 = [], {}, time.time()
    gcache = {}

    def _grouped(d):
        if d not in gcache:
            js = TB._get(f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{d}?adjusted=false&apiKey={key}") or {}
            gcache[d] = {r["T"]: r for r in js.get("results") or []}
        return gcache[d]
    for j, d in enumerate(days):
        g, gp = _grouped(d), _grouped(prev_of[d])
        mem = prep["snapshots"].get(d[:7]) or []
        cands = [s for s in mem if s in g and s in gp and gp[s].get("c") and g[s].get("h", 0) >= 1.30 * gp[s]["c"]]
        for sym in cands:
            if any(str(e) == d for e, _r in (prep["splits"].get(sym) or [])):
                why["تقسيم"] = why.get("تقسيم", 0) + 1
                continue
            mm = (B.poly_minutes(sym, d, d, key) or {}).get(d) or []
            if not mm:
                why["بلا دقائق"] = why.get("بلا دقائق", 0) + 1
                continue
            fire = S.xmove_fire([{"t": b[0], "h": b[3], "c": b[5], "v": b[6]} for b in mm], d, gp[sym]["c"])
            if not fire:
                why["لا إشعار"] = why.get("لا إشعار", 0) + 1
                continue
            fc = {}

            def _fill(ms, px, _s=sym, _fc=fc):
                kk = (ms, round(px, 8))
                if kk not in _fc:
                    u = B.poly_usd_at_or_above(_s, ms, px, key)
                    _fc[kk] = u is not None and u >= FILL_USD
                return _fc[kk]
            r = run_fire(sym, d, mm, fire, _fill)
            recs.append(dict(r, sym=sym, d=d, y=d[:4]))
            why[r["st"]] = why.get(r["st"], 0) + 1
        if j % 5 == 0:
            log(f"T-HOLD15 شريحة {k}: يوم {j + 1}/{len(days)} · إشعارات {len(recs)} · {round(time.time() - t0)}s")
    os.makedirs(TB.OUT, exist_ok=True)
    with gzip.open(os.path.join(TB.OUT, f"hold15_shard_{k:02d}.json.gz"), "wt", encoding="utf-8") as fh:
        json.dump({"shard": k, "days": len(days), "why": why, "recs": recs}, fh, ensure_ascii=False)
    log(f"📦 شريحة {k}: أيّام {len(days)} · إشعارات {len(recs)} · {why}")
    return RC_OK


def evaluate(recs, boot_mean):
    cells, verdict = {}, "✅ تعبر"
    for s in STOPS:
        tag = f"{int(s * 100)}"
        for y in FC.YEARS:
            ok = [r for r in recs if r["y"] == y and r.get(f"H_{tag}") is not None]
            p0 = [(r["sym"], r[f"H_{tag}"] - r[f"C0_{tag}"]) for r in ok if r.get(f"C0_{tag}") is not None]
            pr = [(r["sym"], r[f"H_{tag}"] - r[f"CR_{tag}"]) for r in ok if r.get(f"CR_{tag}") is not None]
            c = {"n": len(ok), "h": FC._mean([r[f"H_{tag}"] for r in ok]), "c0": FC._mean([r[f"C0_{tag}"] for r in ok]),
                 "cr": FC._mean([r[f"CR_{tag}"] for r in ok if r.get(f"CR_{tag}") is not None]),
                 "d0": FC._mean([v for _s, v in p0]), "ci0": boot_mean(p0) if len(p0) >= 2 else None,
                 "dr": FC._mean([v for _s, v in pr]), "cir": boot_mean(pr) if len(pr) >= 2 else None}
            cells[(tag, y)] = c
            if c["n"] < FC.MIN_N:
                verdict = "لا قياس"
    if verdict != "لا قياس" and not all((c["ci0"] or [0])[0] > 0 and (c["cir"] or [0])[0] > 0 for c in cells.values()):
        verdict = "❌ لا تعبر"
    return cells, verdict


def mode_assemble(d_in):
    B = FC._basket()
    paths = sorted(glob.glob(os.path.join(d_in, "**", "hold15_shard_*.json.gz"), recursive=True))
    if len(paths) != FC.NSHARDS:
        log(f"⛔ شرائحُ T-HOLD15 {len(paths)} لا {FC.NSHARDS} — خروج 5")
        return RC_POP
    recs, why = [], {}
    for p in paths:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            js = json.load(fh)
        recs += js["recs"]
        for k_, v in (js.get("why") or {}).items():
            why[k_] = why.get(k_, 0) + v
    cells, verdict = evaluate(recs, B.boot_mean)
    L = ["# ⏱️ `T-HOLD15` «الدخولُ بعد صمود ربع الساعة» — النتيجة", "",
         "> العقد `T_HOLD15_prereg.md` · `TRAIL_REOPEN` مُقَرٌّ لهذه القراءة وحدَها · العوائدُ بعد 1.8% · H15 مقابل الدخول عند الإشعار (C0) ودقيقةٍ عشوائيّة (CR).", "",
         f"- الإشعارات {len(recs)} · الحالاتُ {why}", "", f"## الحكم (بالأضعف): **{verdict}**", "",
         "| الوقف | السنة | صفقاتُ H15 | H15 | C0 | CR | H15 − C0 | فاصل | H15 − CR | فاصل |", "|---|---|---|---|---|---|---|---|---|---|"]
    for (tag, y), c in sorted(cells.items(), key=lambda kv: (int(kv[0][0]), kv[0][1])):
        L.append(f"| −{tag}% | {y} | {c['n']} | {FC.pct(c['h'])} | {FC.pct(c['c0'])} | {FC.pct(c['cr'])} | {FC.pct(c['d0'])} | {FC.ci_txt(c['ci0'])} | "
                 f"{FC.pct(c['dr'])} | {FC.ci_txt(c['cir'])} |")
    L += ["", "## حدودُ الصدق", "- الكونُ لقطةُ الأعضاء الشهريّة لا كونُ البوت الحيّ · وشموعُ الدقيقة لا تُظهر الترتيبَ داخلها (الوقفُ أوّلًا) · وشرطُ 5,000$ على صفقات Polygon."]
    txt = "\n".join(L) + "\n"
    open(RESULT, "w", encoding="utf-8").write(txt)
    print(txt)
    log(f"⚖️ T-HOLD15: {verdict}")
    return RC_OK


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not contracts_ok():
        log("⛔ العقد أو البروتوكول لا يطابق بصمتَه — خروج 11 قبل أيّ جلب")
        return RC_CONTRACT
    if not reopened():
        log(f"⛔ محورُ إدارة الخروج مُغلَق (`T-TRAIL`) — `{REOPEN_ENV}` لم يُقَرّ بـ\"1\" — خروج 8")
        return RC_CLOSED
    mode = argv[0] if argv else ""
    d_in = argv[argv.index("--dir") + 1] if "--dir" in argv else "nq_in"
    if mode == "assemble":
        return mode_assemble(d_in)
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log("⛔ بلا مفتاح Polygon — خروج 2")
        return RC_KEY
    if mode == "shard":
        return mode_shard(key, int(argv[1]), d_in)
    return 1


if __name__ == "__main__":
    sys.exit(main())
