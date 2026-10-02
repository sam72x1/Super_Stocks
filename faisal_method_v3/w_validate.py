# -*- coding: utf-8 -*-
"""
📊 `T-W` — التحقّقُ الكمّيّ لدعوى فيصل «الدخولُ بين خط العنق والقاع المزدوج غيرُ آمن» (العقد `T_W_prereg.md`).

قراءةٌ فقط · لا تلغرام · لا حالةَ إنتاج. الكاشفُ والحالةُ من `faisal_tool.py` المجمَّد · والصفقةُ والبوتستراب والجلبُ من
`hs_forensic.py` استيرادًا (بلا main() المُغلَق). المخرَج `faisal_method_v3/out/w_validate.json`.
"""
import datetime as dt
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import faisal_tool as T          # noqa: E402

TOOL = "T-W"
WIN = 60                          # §④ نافذةُ الصفقة
N_CTRL = 10                       # §④
CTRL_GAP = 10                     # §④ خارج ±10 جلسات
CTRL_SPAN = 250                   # §④ داخل ±250
SEED = 20261002                   # §④
ALPHA4 = 0.05 / 4                 # §⑤ بونفيروني على أربع ⟵ 98.75%
MIN_N = 30                        # §⑤ W-4
SPLIT_PAD_DAYS = 45               # §④
COV_MIN, UNK_MAX = 0.90, 0.10     # §②


def log(*a):
    print(*a, flush=True)


def _arrays(df):
    return {"o": df["Open"].astype(float).values, "h": df["High"].astype(float).values,
            "l": df["Low"].astype(float).values, "c": df["Close"].astype(float).values,
            "d": [str(x)[:10] for x in df.index]}


def detect_events(A: dict) -> list:
    """كلُّ W مؤكَّدٍ مرّةً واحدة عند بار تأكيده ⟵ مداخلُ A/M/B (§③) — بلا نظرٍ للأمام: الكشفُ بالبيانات حتى بار التأكيد،
    والمداخلُ تُفحص بارًا بارًا بعده. ⟵ [{kind · e (بارُ الإشارة) · E (افتتاحُ التالي) · w}]."""
    o, h, l, c = A["o"], A["h"], A["l"], A["c"]
    n = len(c)
    k = T.P("SWING_K")
    seen, out = set(), []
    sw_all = T.confirmed_swings(h, l, n - 1, k)          # المحاورُ النهائيّة — كلٌّ يُستعمل فقط بعد i+k
    lows = [(i, p) for i, t, p in sw_all if t == "L"]
    for j in range(1, len(lows)):
        i2 = lows[j][0]
        conf = i2 + k
        if conf >= n - 1:
            continue
        w = T.find_w(o, h, l, c, conf, k, sw=sw_all)
        if not w or w["i2"] != i2:
            continue
        key = (w["i1"], w["i2"])
        if key in seen:
            continue
        seen.add(key)
        zone_hi = w["low2"] * (1 + T.P("SUPPORT2_ZONE_PCT") / 100)
        inval = w["base"] * (1 - T.P("LOW2_SWEEP_MAX_PCT") / 100)
        if c[conf] <= zone_hi and c[conf] >= inval:
            out.append({"kind": "A", "e": conf, "w": w})
        got_m = False
        for i in range(conf + 1, min(n - 1, conf + WIN + 1)):
            if c[i] < inval:
                break
            if c[i] > w["neckline"]:
                out.append({"kind": "B", "e": i, "w": w})
                break
            if not got_m and zone_hi < c[i] < w["neckline"]:
                out.append({"kind": "M", "e": i, "w": w})
                got_m = True
    for ev in out:
        e = ev["e"]
        ev["E"] = float(o[e + 1]) if e + 1 < n else None
    return [ev for ev in out if ev["E"] and ev["E"] > 0]


def trade(A, ev, sw_all=None):
    import hs_forensic as FX
    o, h, l, c = A["o"], A["h"], A["l"], A["c"]
    e, E, w = ev["e"] + 1, ev["E"], ev["w"]          # الدخولُ افتتاحُ e+1 ⟵ القياسُ بعده
    stop = w["low2"] * (1 - T.P("STOP_BELOW_PCT") / 100)
    k = T.P("SWING_K")
    sw = (T.confirmed_swings(h, l, ev["e"], k) if sw_all is None
          else [x for x in sw_all if x[0] + k <= ev["e"]])
    lad = T.resistance_ladder(h, sw, E, ev["e"], n=1)
    tgt = lad[0] if lad else None
    if not (stop < E) or tgt is None:
        return None
    b = FX.bracket(o, h, c, e, E, tgt, stop, WIN)
    if b is None:
        return None
    return dict(b, stop_pct=stop / E - 1, tgt_pct=tgt / E - 1)


def ctrl_trades(A, ev, rng):
    import hs_forensic as FX
    o, h, c = A["o"], A["h"], A["c"]
    n = len(c)
    e0 = ev["e"] + 1
    cand = [i for i in range(max(1, e0 - CTRL_SPAN), min(n - WIN - 1, e0 + CTRL_SPAN)) if abs(i - e0) > CTRL_GAP]
    if not cand:
        return []
    pick = rng.choice(cand, size=min(N_CTRL, len(cand)), replace=False)
    out = []
    for i in pick:
        E = float(o[i])
        if not E > 0:
            continue
        b = FX.bracket(o, h, c, int(i), E, E * (1 + ev["tgt_pct"]), E * (1 + ev["stop_pct"]), WIN)
        if b is not None:
            out.append(b["ret"])
    return out


def split_ok(ev, A, sp_dates):
    if sp_dates is None:
        return None
    a = A["d"][ev["w"]["i1"]]
    end_i = min(len(A["d"]) - 1, ev["e"] + 1 + WIN)
    b = (dt.date.fromisoformat(A["d"][end_i]) + dt.timedelta(days=SPLIT_PAD_DAYS)).isoformat()
    return not any(a <= d <= b for d in sp_dates)


def analyze_sym(task):
    """(sym, df, sp_dates) ⟵ مداخلُ بصفقاتها وضبطها — يعمل في عمليّةٍ منفصلة."""
    import hs_forensic as FX
    sym, df, sp_dates = task
    try:
        A = _arrays(df)
        evs = detect_events(A)
        sw_all = T.confirmed_swings(A["h"], A["l"], len(A["c"]) - 1, T.P("SWING_K"))
        rng = np.random.default_rng(SEED + sum(map(ord, sym)))
        rows = []
        for ev in evs:
            tr = trade(A, ev, sw_all)
            if tr is None:
                continue
            ev2 = dict(ev, **{k: tr[k] for k in ("stop_pct", "tgt_pct")})
            rows.append({"sym": sym, "kind": ev["kind"], "date": A["d"][ev["e"]], "era": FX.era_of(A["d"][ev["e"]]),
                         "ret": tr["ret"], "R": tr["R"], "why": tr["why"], "bars": tr["bars"],
                         "stop_pct": tr["stop_pct"], "tgt_pct": tr["tgt_pct"], "swept": ev["w"]["low2_is_sweep"],
                         "split_ok": split_ok(ev, A, sp_dates), "ctrl": ctrl_trades(A, ev2, rng)})
        return {"sym": sym, "rows": rows, "n_w": len({(e["w"]["i1"], e["w"]["i2"]) for e in evs})}
    except Exception as ex:                                              # noqa: BLE001
        return {"sym": sym, "rows": [], "err": f"{type(ex).__name__}: {ex}"[:200]}


def verdict(rows):
    import hs_forensic as FX
    test = [r for r in rows if r["era"] == "TEST" and r["split_ok"] is not False]
    by = {k: [r for r in test if r["kind"] == k] for k in ("A", "M", "B")}
    n = {k: len(v) for k, v in by.items()}
    H1 = FX._ind_diff([r["ret"] for r in by["A"]], [r["ret"] for r in by["M"]], alpha=ALPHA4)
    H2 = FX._ind_diff([r["ret"] for r in by["B"]], [r["ret"] for r in by["M"]], alpha=ALPHA4)
    H3 = FX.boot_diff([r["ret"] for r in by["A"]], [r["ctrl"] for r in by["A"]], alpha=ALPHA4)
    H4 = FX.boot_diff([r["ret"] for r in by["B"]], [r["ctrl"] for r in by["B"]], alpha=ALPHA4)

    def passes(x):
        return x.get("lo") is not None and x["lo"] > 0
    if min(n["A"], n["M"], n["B"]) < MIN_N:
        branch = "W-4 «لا قياس»"
    else:
        br = []
        if passes(H1) and passes(H2):
            br.append("W-1 «الوسطُ أسوأ»")
        if passes(H3) or passes(H4):
            br.append("W-2 «ميزةٌ للمدخل» (" + " · ".join(x for x, h in (("A", H3), ("B", H4)) if passes(h)) + ")")
        branch = " ⟵ ".join(br) if br else "W-3 «لا فرق»"
    return {"n_test": n, "H1_A_minus_M": H1, "H2_B_minus_M": H2, "H3_A_vs_ctrl": H3, "H4_B_vs_ctrl": H4, "branch": branch}


def era_tables(rows):
    import hs_forensic as FX
    out = {}
    for era in ("TRAIN", "VAL", "TEST", "SEEN"):
        for k in ("A", "M", "B"):
            v = [r for r in rows if r["era"] == era and r["kind"] == k and r["split_ok"] is not False]
            out[f"{era}|{k}"] = {"n": len(v), "ret": FX.boot_ci([r["ret"] for r in v]),
                                 "target_first": (sum(1 for r in v if r["why"] == "target") / len(v)) if v else None,
                                 "stop_first": (sum(1 for r in v if r["why"] == "stop") / len(v)) if v else None}
    return out


def main():
    import head_shoulders as HS
    import hs_forensic as FX
    t0 = time.time()
    pop = HS.load_population(ROOT)
    log(f"📊 {TOOL} · المجتمع {len(pop)} · الكاشف {T.TOOL_VERSION} · PARAMS {json.dumps({k: v[0] for k, v in T.PARAMS.items()})}")
    frames, rep, sp = FX._fetch(pop)
    unk = sum(1 for s in frames if sp.get(s) is None)
    cov = len(frames) / max(1, len(pop))
    partial = cov < COV_MIN or (unk / max(1, len(frames))) > UNK_MAX
    log(f"📥 شموعٌ {len(frames)}/{len(pop)} ({cov:.1%}) · تقسيماتٌ مجهولة {unk} · جزئيّ {partial}")
    tasks = [(s, frames[s], (None if sp.get(s) is None else sorted({d for d, _r in sp[s]}))) for s in sorted(frames)]
    res = FX._pool_run(analyze_sym, tasks)
    rows = [r for x in res for r in x["rows"]]
    errs = [(x["sym"], x["err"]) for x in res if x.get("err")]
    log(f"⚙️ حُلّل {len(res)} رمزًا · W {sum(x.get('n_w', 0) for x in res)} · مداخل {len(rows)} · أخطاء {len(errs)} {errs[:3]}")
    v = verdict(rows)
    out = {"tool": TOOL, "generated": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", "detector": T.TOOL_VERSION,
           "params": {k: v2[0] for k, v2 in T.PARAMS.items()}, "population": len(pop), "fetched": len(frames),
           "coverage": round(cov, 4), "splits_unknown": unk, "partial": partial, "errors": errs[:30],
           "n_w": sum(x.get("n_w", 0) for x in res), "n_rows": len(rows),
           "kinds_all": {k: sum(1 for r in rows if r["kind"] == k) for k in ("A", "M", "B")},
           "split_excluded": sum(1 for r in rows if r["split_ok"] is False),
           "split_unknown_rows": sum(1 for r in rows if r["split_ok"] is None),
           "eras": era_tables(rows), "verdict": (None if partial else v), "verdict_if_partial": (v if partial else None),
           "elapsed_s": round(time.time() - t0)}
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, "out", "w_validate.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    with open(os.path.join(HERE, "out", "w_rows.jsonl"), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps({k: v3 for k, v3 in r.items() if k != "ctrl"}, ensure_ascii=False, default=str) + "\n")
    log(json.dumps({k: out[k] for k in ("coverage", "partial", "n_w", "n_rows", "kinds_all", "split_excluded")}, ensure_ascii=False))
    for k3 in ("TEST|A", "TEST|M", "TEST|B"):
        log(k3, json.dumps(out["eras"][k3], ensure_ascii=False, default=str))
    log("🏁", json.dumps(v, ensure_ascii=False, default=str)[:1500])
    return 0 if not partial else 3


if __name__ == "__main__":
    raise SystemExit(main())
