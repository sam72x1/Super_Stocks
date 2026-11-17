#!/usr/bin/env python3
"""🥁 `T-RHYTHM` «إيقاعُ انفجارات السهم نفسِه» (عقد `T_RHYTHM_prereg.md` · قراءةٌ فقط).

  shard <k> --dir D   — الإشارةُ R لإدخالات مجتمع `T-FPRINT` (رموزُ الشريحة k من 40) من شموع `T-FPRINT` نفسِها (`daily_filters._bars` بالاسم).
  assemble --dir D    — الحكمُ بحرف FILTER_PROTOCOL ⟵ `T_RHYTHM_RESULT.md`.
أداةٌ جديدة: **لا تعديلَ** على `daily_filters.py` ولا `filter_core.py` (تُستوردان بالاسم) · لا تلغرام · لا إنتاج · لا CONFIG.
"""
import glob
import gzip
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import daily_filters as DF                                       # noqa: E402
import filter_core as FC                                         # noqa: E402
import tbook as TB                                               # noqa: E402

CONTRACT = os.path.join(HERE, "T_RHYTHM_prereg.md")
CONTRACT_SHA = "2807e0f04260bf89fe5df05a414c89b216027f35ef6600b2d69bbcdc0b21a459"
RESULT = os.path.join(HERE, "T_RHYTHM_RESULT.md")
FPRINT_RUN = 44071032068
TOL = 0.25                                                       # §② ±25% (المالك · هندسيّ · لا يُعايَر)
RC_OK, RC_KEY, RC_POP, RC_CONTRACT = 0, 2, 5, 11


def log(m=""):
    print(m, flush=True)


def contract_ok():
    return FC.sha_of(CONTRACT) == CONTRACT_SHA and FC.sha_of(FC.PROTOCOL) == TB.PROTOCOL_SHA


def rhythm(closes, i, n_ev_rec=None, tol=TOL):
    """(نقيّة) §② عند الصفّ i ⟵ {R، s، g، k} · أو "mismatch" إن خالف عددُ الانفجارات المُسجَّلَ · أو "out" إن قلّ عن اثنين."""
    ev = DF.explosions(closes, i - 20)
    if n_ev_rec is not None and len(ev) != int(n_ev_rec):
        return "mismatch"
    if len(ev) < 2:
        return "out"
    E = [e for e, _b in ev]
    gaps = [E[j + 1] - E[j] for j in range(len(E) - 1)]
    g = sum(gaps) / len(gaps)
    s = i - E[-1]
    return {"R": abs(s - g) <= tol * g, "s": s, "g": round(g, 4), "k": len(E)}


def load_fprint(d_in):
    """⟵ ({مفتاح: قيمةُ fprint}، عددُ الشرائح) من `fprint_shard_*.json.gz` (التشغيلة 44071032068)."""
    paths = sorted(glob.glob(os.path.join(d_in, "**", "fprint_shard_*.json.gz"), recursive=True))
    raw = {}
    for p in paths:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            raw.update(json.load(fh).get("sig") or {})
    return raw, len(paths)


def mode_shard(key, k, d_in):
    recs, n = FC.load_shards(d_in)
    fp, nf = load_fprint(d_in)
    if n != FC.NSHARDS or nf != FC.NSHARDS:
        log(f"⛔ الشرائح {n}/{nf} لا {FC.NSHARDS} — خروج 5")
        return RC_POP
    cur = FC.current(recs)
    syms = sorted({r["sym"] for r in cur})[k::FC.NSHARDS]          # تقسيمُ daily_filters نفسُه
    by = {}
    for r in cur:
        key_ = f"{r['sym']}|{r['d']}"
        if r["sym"] in set(syms) and key_ in fp and fp[key_] != "out":
            by.setdefault(r["sym"], set()).add(r["d"])
    out, why, t0 = {}, {}, time.time()
    for j, sym in enumerate(sorted(by)):
        rows = DF._bars(sym, key)
        days = [x[0] for x in rows]
        C = [x[3] for x in rows]
        for d in sorted(by[sym]):
            rec = fp.get(f"{sym}|{d}")
            if d not in days:
                out[f"{sym}|{d}"] = None
                why["لا شمعة"] = why.get("لا شمعة", 0) + 1
                continue
            v = rhythm(C, days.index(d), rec.get("n_ev") if isinstance(rec, dict) else None)
            if v in ("mismatch", "out"):
                out[f"{sym}|{d}"] = None
                why["اختلاف المادّة"] = why.get("اختلاف المادّة", 0) + 1
                continue
            out[f"{sym}|{d}"] = v
        if j % 25 == 0:
            log(f"rhythm شريحة {k}: {j + 1}/{len(by)} رمزًا · {round(time.time() - t0)}s")
    os.makedirs(TB.OUT, exist_ok=True)
    with gzip.open(os.path.join(TB.OUT, f"rhythm_shard_{k:02d}.json.gz"), "wt", encoding="utf-8") as fh:
        json.dump({"shard": k, "why": why, "sig": out}, fh, ensure_ascii=False)
    log(f"📦 rhythm شريحة {k}: {len(out)} إدخالًا · {why}")
    return RC_OK


def phase_rows(pop, raw, arm):
    """وصفًا: مبكّر/في موعده/متأخّر ⟵ (n، متوسّطُ r الخام)."""
    acc = {"مبكّر": [], "في موعده": [], "متأخّر": []}
    for r in FC.current(pop):
        v = raw.get(f"{r['sym']}|{r['d']}")
        res = (r.get("res") or {}).get(arm)
        if not isinstance(v, dict) or not res or res.get("r") is None or r["y"] not in FC.YEARS:
            continue
        ph = "في موعده" if v["R"] else ("مبكّر" if v["s"] < (1 - TOL) * v["g"] else "متأخّر")
        acc[ph].append(float(res["r"]))
    return {k: (len(v), FC._mean(v)) for k, v in acc.items()}


def mode_assemble(d_in):
    import market_calendar as MC
    recs, n = FC.load_shards(d_in)
    fp, nf = load_fprint(d_in)
    paths = sorted(glob.glob(os.path.join(d_in, "**", "rhythm_shard_*.json.gz"), recursive=True))
    if n != FC.NSHARDS or nf != FC.NSHARDS or len(paths) != FC.NSHARDS:
        log(f"⛔ الشرائح {n}/{nf}/{len(paths)} لا {FC.NSHARDS} — خروج 5")
        return RC_POP
    raw, why = {}, {}
    for p in paths:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            js = json.load(fh)
        raw.update(js["sig"])
        for k_, v in (js.get("why") or {}).items():
            why[k_] = why.get(k_, 0) + v
    pop = [r for r in recs if f"{r['sym']}|{r['d']}" in fp and fp[f"{r['sym']}|{r['d']}"] != "out"]
    sig = {(r["sym"], r["d"]): (bool(raw[f"{r['sym']}|{r['d']}"]["R"]) if isinstance(raw.get(f"{r['sym']}|{r['d']}"), dict) else None)
           for r in pop}
    ev = FC.evaluate(pop, sig, FC.last_sessions(TB._sessions("2026-01-01", FC.WIN_END, MC)))
    known = [v for v in raw.values() if isinstance(v, dict)]
    L = ["# 🥁 `T-RHYTHM` «إيقاعُ انفجارات السهم نفسِه» — النتيجة", "",
         f"> العقد `T_RHYTHM_prereg.md` · القاعدة `FILTER_PROTOCOL.md` · شرائحُ T-BASKET `{FC.BASKET_RUN}` · مجتمعُ T-FPRINT `{FPRINT_RUN}`.", "",
         f"- محسوبة {len(known)} · R = True {sum(1 for v in known if v['R'])} · أسبابُ غير المحسوب {why}"]
    for y in FC.YEARS:
        py = [r for r in FC.current(pop) if r["y"] == y]
        ty = sum(1 for r in py if sig.get((r["sym"], r["d"])) is True)
        L.append(f"- {y}: المجتمع {len(py)} · R = True {ty} ({(ty / len(py) * 100) if py else 0:.1f}%)")
    L.append("")
    L += FC.report_lines(ev, "الحاكم (بالأضعف)")
    L += ["", "### وصفًا لا حكمًا — موضعُ الإدخال من الإيقاع (2023-2025 · r الخام بعد الكلفة)", "",
          "| الخليّة | مبكّر (n · r) | في موعده (n · r) | متأخّر (n · r) |", "|---|---|---|---|"]
    for a in FC.ARMS:
        pr = phase_rows(pop, raw, a)
        L.append(f"| {a} | " + " | ".join(f"{pr[k][0]} · {FC.pct(pr[k][1])}" for k in ("مبكّر", "في موعده", "متأخّر")) + " |")
    L += ["", f"⚖️ rhythm: {ev['verdict']}"]
    txt = "\n".join(L) + "\n"
    open(RESULT, "w", encoding="utf-8").write(txt)
    print(txt)
    log(f"⚖️ rhythm: {ev['verdict']}")
    return RC_OK


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not contract_ok():
        log("⛔ العقد أو البروتوكول لا يطابق بصمتَه — خروج 11 قبل أيّ جلب")
        return RC_CONTRACT
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
