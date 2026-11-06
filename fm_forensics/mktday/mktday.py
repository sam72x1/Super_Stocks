#!/usr/bin/env python3
"""🌡️📅 `T-MKTDAY` — «حالة السوق كبوابة» (العقد `fm_forensics/mktday/MKTDAY_prereg.md` · مدموجٌ قبل أيّ رقم) — قراءةٌ فقط.

`--mode shard --shard k`: جلساتُ شظيّةٍ من الستّين (`vwap_cont.shard_days` بالاسم) ⟵ لكلّ جلسة: الكونُ (`prefilter` بالاسم) · عرضُ الزخم `B` ·
عرضُ البري `P` · وصفوفُ التنبيهات المحفوظة (`vwap_cont.reading_row` بالاسم) · وأسماءُ S بالراكض (`gcross_runner.run_ratio` بالاسم) ⟵ JSON.
`--mode report --in DIR`: الشظايا ⟵ بوّاباتُ التغطية · الوسيطان · ①②③ لكلّ ذراع · الفرقُ بإعادة سحب الجلسات · النصفان · K1-K7. نقيٌّ بلا شبكة.
🔒 لا تلغرام · لا كتابة في المستودع · لا تغيير إنتاجيّ · وتخرج 9 إن تغيّرت بصمةُ العقد.
"""
import argparse
import glob
import hashlib
import json
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CONTRACT = os.path.join(HERE, "MKTDAY_prereg.md")
CONTRACT_SHA = "4fe5735fc7783f77844b66b08edff6798f52009a3a300c440a0befdf26d06588"
CONTRACT_RC = 9
SRC_RUN = 42134086032                          # §① شظايا T-VWAP-CONT
SHADOW_REF = "7936c0bfcdb2caf9f8a44db8a782ece4a7ff651a"   # §① سجلُّ الظلّ المجمَّد
SHADOW_FILE = "shadow_ready_ledger.jsonl"
PRE_FROM, PRE_CUT = 4 * 60, 9 * 60 + 25        # §② [04:00، 09:25) نيويورك
RUN_MIN = 1.0                                  # §① الراكض ‏+100%
FLOOR_A, FLOOR_S = 20, 10                      # §④ الأرضيّات
BOOT_N, SEED = 2000, "MKT1"                    # §④
DAYS_OK_MIN, BARS_FAIL_MAX, UNK_MAX, CONSIST_MIN = 54, 0.02, 0.10, 0.95   # §④ بوّاباتُ التغطية


def log(m=""):
    print(m, flush=True)


def contract_ok(path=CONTRACT):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest() == CONTRACT_SHA
    except OSError:
        return False


# ── نقيّات ─────────────────────────────────────────────────────────────────────────────
def median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2.0


def split_days(val_of, days):
    """§② الوسيطُ على الأيّام ⟵ (الوسيط، {يوم: "rich"|"poor"}) · غنيّةٌ فوقه تمامًا · والتعادلُ للفقيرة."""
    vals = [val_of[d] for d in days if val_of.get(d) is not None]
    med = median(vals)
    lab = {}
    for d in days:
        v = val_of.get(d)
        if v is not None and med is not None:
            lab[d] = "rich" if v > med else "poor"
    return med, lab


def share(rows, key):
    xs = [r[key] for r in rows if r.get(key) is not None]
    return (sum(1 for x in xs if x) / len(xs)) if xs else None


def stat(rows, metric):
    """① حصّةُ `win` · ② وسيطُ `ret2` · ③ حصّةُ `runner`."""
    if metric == "m1":
        return share(rows, "win")
    if metric == "m2":
        return median([r.get("ret2") for r in rows])
    return share(rows, "runner")


def diff(rows_by_day, lab, metric, days=None):
    keep = set(days) if days is not None else None
    rich = [r for d, rs in rows_by_day.items() if lab.get(d) == "rich" and (keep is None or d in keep) for r in rs]
    poor = [r for d, rs in rows_by_day.items() if lab.get(d) == "poor" and (keep is None or d in keep) for r in rs]
    a, b = stat(rich, metric), stat(poor, metric)
    return (None if a is None or b is None else a - b), len(rich), len(poor), a, b


def boot(rows_by_day, lab, metric, n=BOOT_N, seed=SEED):
    """§④ فاصلُ 95% للفرق بإعادة سحب **الجلسات** داخل كلّ فئة ⟵ (أدنى، أعلى) أو (None، None)."""
    rich = sorted(d for d in rows_by_day if lab.get(d) == "rich")
    poor = sorted(d for d in rows_by_day if lab.get(d) == "poor")
    if not rich or not poor:
        return (None, None)
    rnd = random.Random(seed)
    vals = []
    for _ in range(n):
        rr = [r for _k in rich for r in rows_by_day[rich[rnd.randrange(len(rich))]]]
        pp = [r for _k in poor for r in rows_by_day[poor[rnd.randrange(len(poor))]]]
        a, b = stat(rr, metric), stat(pp, metric)
        if a is not None and b is not None:
            vals.append(a - b)
    if len(vals) < n * 0.9:
        return (None, None)
    vals.sort()
    return (vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1])


def verdict(d_all, ci, d_h1, d_h2, n_rich, n_poor, floor):
    """§④ ⟵ «لا قياس» · «يفرّق» · «لا يفرّق»."""
    if n_rich < floor or n_poor < floor or d_all is None:
        return "لا قياس"
    lo, hi = ci
    if lo is None or hi is None:
        return "لا قياس"
    sep = (lo > 0 or hi < 0)
    halves = d_h1 is not None and d_h2 is not None and d_h1 != 0 and d_h2 != 0 and (d_h1 > 0) == (d_h2 > 0) == (d_all > 0)
    return "يفرّق" if sep and halves else "لا يفرّق"


def spearman(xs, ys):
    pts = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pts) < 3:
        return None

    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2.0 + 1
            i = j + 1
        return r
    rx, ry = ranks([p[0] for p in pts]), ranks([p[1] for p in pts])
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else None


# ── الشظيّة (الرنر · Polygon) ─────────────────────────────────────────────────────────
def load_shadow(ref=SHADOW_REF):
    """§① صفوفُ S من سجلّ الظلّ عند `ref` (git) ⟵ قائمة · أو None إن تعذّر (⟵ ③ «لا قياس»)."""
    try:
        txt = subprocess.run(["git", "show", f"{ref}:{SHADOW_FILE}"], cwd=ROOT, capture_output=True, text=True, timeout=60)
        if txt.returncode != 0:
            return None
        rows = [json.loads(x) for x in txt.stdout.splitlines() if x.strip()]
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return [r for r in rows if r.get("shadow") is True]


def load_alerts(src_dir):
    out = []
    for path in sorted(glob.glob(os.path.join(src_dir, "**", "*.json"), recursive=True)):
        with open(path, encoding="utf-8") as f:
            out.extend(json.load(f).get("alerts") or [])
    return [r for r in out if not r.get("tail")]


def day_measure(D, day, cands, hl, bars_of, op, cl, V, cut=PRE_CUT):
    """§② لجلسةٍ واحدة ⟵ {B · P · up20 · unk · pre20 · unk_pre · pre_over_hl} — `bars_of(sym)` ⟵ دقائقُ اليوم أو None."""
    res = {"B": 0, "P": 0, "up20": 0, "unk": 0, "pre20": 0, "unk_pre": 0, "pre_over_hl": 0, "B_syms": [], "P_syms": []}
    for sym in cands:
        bars = bars_of(sym)
        pa = D.prev_adj(sym)
        if not bars or not pa:
            continue
        b5, _b15, _bb = V.complete_buckets(bars, op, cl, cl)
        hits = [x["e"] for x in b5 if V.V4.ge(V.V4.pct_change(x["c"], pa), V.CHG_MIN)]
        pre = [b for b in bars if PRE_FROM <= b[0] < cut]
        pre_hit = any(V.V4.ge(V.V4.pct_change(b[4], pa), V.CHG_MIN) for b in pre)
        h_day = (hl.get(sym) or (None,))[0]
        if pre and h_day is not None and max(b[2] for b in pre) > float(h_day) * (1 + 1e-6):
            res["pre_over_hl"] += 1
        if not hits and not pre_hit:
            continue
        cat_of = D.catalyst(sym, V.V3.ny_ts(day, cl))[0]
        if hits:
            res["up20"] += 1
            cs = [cat_of(e).get("C") for e in hits]
            if any(c is True for c in cs):
                res["B"] += 1
                res["B_syms"].append(sym)
            elif any(c is None for c in cs):
                res["unk"] += 1
        if pre_hit:
            res["pre20"] += 1
            c = cat_of(cut).get("C")
            if c is True:
                res["P"] += 1
                res["P_syms"].append(sym)
            elif c is None:
                res["unk_pre"] += 1
    return res


def mode_shard(net, MC, k, src_dir):
    import vwap_cont as VC
    import vwap_momentum_live as V
    import gcross_runner as GR
    days = VC.shard_days(VC.sessions(MC), k)
    alerts = [r for r in load_alerts(src_dir) if r["date"] in days]
    srows = load_shadow()
    out = {"shard": k, "days": days, "per_day": {}, "alerts": [], "s_rows": [], "shadow_ok": srows is not None,
           "src_alerts": len(alerts)}
    for day in days:
        D = V.Day(net, day, MC, replay=True)
        g = net.poly(f"/v2/aggs/grouped/locale/us/market/stocks/{day}", {"adjusted": "false"})
        hl = {str(r.get("T") or "").upper(): (r.get("h"), r.get("l"), r.get("v")) for r in ((g or {}).get("results") or []) if r.get("T")}
        if not D.ok or not hl:
            out["per_day"][day] = {"ok": False, "why": D.why + ([] if hl else ["شمعةُ اليوم المجمَّعة"])}
            log(f"⛔ {day}: مرجعٌ ناقص {out['per_day'][day]['why']}")
            continue
        info = MC.session_info(day)
        op, cl = info["open_ny_min"], info["close_ny_min"]
        cands = sorted(V.prefilter(hl, D.prev_adj_pf, D.types))
        day_alerts = [r for r in alerts if r["date"] == day]
        day_s = [r for r in (srows or []) if r.get("date") == day]
        need = sorted(set(cands) | {r["sym"] for r in day_alerts} | {str(r["symbol"]).upper() for r in day_s})
        cache, miss = {}, 0
        for sym in need:
            by = net.minutes(sym, day, day)
            if by is None:
                miss += sym in cands
                continue
            cache[sym] = by.get(day) or []
        m = day_measure(D, day, cands, hl, cache.get, op, cl, V)
        for r in day_alerts:
            bars = cache.get(r["sym"])
            if not bars:
                continue
            rr = VC.reading_row(r, bars, op, cl)
            out["alerts"].append({"date": day, "sym": r["sym"], "win": rr["win"], "consistent": rr["consistent"], "ret2": rr["ret2"]})
        for r in day_s:
            sym = str(r["symbol"]).upper()
            split = any(str(x[0]) == day for x in (D.splits.get(sym) or []))
            bars = cache.get(sym)
            ratio = None if split or not bars else GR.run_ratio(bars, D.prev_adj(sym))[0]
            out["s_rows"].append({"date": day, "sym": sym, "split": split, "ratio": ratio,
                                  "runner": (None if ratio is None else ratio >= RUN_MIN)})
        out["per_day"][day] = dict({"ok": True, "candidates": len(cands), "bars_failed": miss}, **m)
        log(f"📅 {day}: كون {len(cands)} · تعذّر {miss} · B {m['B']} · P {m['P']} · بلغ20 {m['up20']} (مجهول {m['unk']}) · "
            f"تنبيهات {len(day_alerts)} · S {len(day_s)}")
    out["calls"], out["fails"] = net.calls, net.fails
    return out


# ── التقرير (نقيّ) ─────────────────────────────────────────────────────────────────────
def predictions(res):
    def v(arm, m):
        return (res["arms"].get(arm) or {}).get(m, {}).get("verdict")
    k = []
    medB = res["med"].get("B")
    k.append(("K1", medB is not None and 5 <= medB <= 25, f"وسيطُ B {medB}"))
    d1 = (res["arms"].get("B") or {}).get("m1", {}).get("diff")
    k.append(("K2", v("B", "m1") == "لا يفرّق" and d1 is not None and -0.08 <= d1 <= 0.08, f"① B {v('B', 'm1')} · الفرق {d1}"))
    k.append(("K3", v("B", "m2") == "لا يفرّق", f"② B {v('B', 'm2')}"))
    k.append(("K4", v("B", "m3") in ("لا قياس", "لا يفرّق"), f"③ B {v('B', 'm3')}"))
    k.append(("K5", v("P", "m1") == "لا يفرّق" and v("P", "m2") == "لا يفرّق", f"① P {v('P', 'm1')} · ② P {v('P', 'm2')}"))
    rho = res.get("spearman")
    k.append(("K6", rho is not None and rho >= 0.5, f"سبيرمان {rho}"))
    sh = res.get("rich_alert_share")
    k.append(("K7", sh is not None and sh >= 0.60, f"حصّةُ التنبيهات في الغنيّة {sh}"))
    return k


def analyze(shards, all_days):
    per_day, alerts, srows, shadow_ok = {}, [], [], True
    calls = fails = 0
    for s in shards:
        per_day.update(s.get("per_day") or {})
        alerts.extend(s.get("alerts") or [])
        srows.extend(s.get("s_rows") or [])
        shadow_ok = shadow_ok and bool(s.get("shadow_ok"))
        calls += s.get("calls") or 0
        fails += s.get("fails") or 0
    ok_days = [d for d in all_days if (per_day.get(d) or {}).get("ok")]
    cands = sum(per_day[d].get("candidates") or 0 for d in ok_days)
    miss = sum(per_day[d].get("bars_failed") or 0 for d in ok_days)
    up20 = sum(per_day[d].get("up20") or 0 for d in ok_days)
    unk = sum(per_day[d].get("unk") or 0 for d in ok_days)
    consist = (sum(1 for r in alerts if r.get("consistent")) / len(alerts)) if alerts else None
    gates = {"days_ok": len(ok_days), "days": len(all_days), "cands": cands, "bars_failed": miss, "up20": up20, "unk": unk,
             "consist": consist, "alerts": len(alerts), "s_rows": len(srows), "shadow_ok": shadow_ok,
             "pre_over_hl": sum(per_day[d].get("pre_over_hl") or 0 for d in ok_days), "calls": calls, "fails": fails}
    cov_ok = (len(ok_days) >= DAYS_OK_MIN and cands and miss / cands <= BARS_FAIL_MAX
              and (up20 == 0 or unk / up20 <= UNK_MAX) and consist is not None and consist >= CONSIST_MIN)
    res = {"gates": gates, "cov_ok": bool(cov_ok), "med": {}, "arms": {}, "n_class": {}}
    a_by, s_by = {}, {}
    for r in alerts:
        a_by.setdefault(r["date"], []).append(r)
    for r in srows:
        if r.get("runner") is not None:
            s_by.setdefault(r["date"], []).append(r)
    h1, h2 = all_days[:30], all_days[30:]
    for arm in ("B", "P"):
        val = {d: per_day[d].get(arm) for d in ok_days}
        med, lab = split_days(val, ok_days)
        res["med"][arm] = med
        res["n_class"][arm] = {"rich": sum(1 for d in lab if lab[d] == "rich"), "poor": sum(1 for d in lab if lab[d] == "poor")}
        res["arms"][arm] = {}
        for m, rows_by, floor in (("m1", a_by, FLOOR_A), ("m2", a_by, FLOOR_A), ("m3", s_by, FLOOR_S)):
            d_all, nr, npo, a, b = diff(rows_by, lab, m)
            ci = boot(rows_by, lab, m)
            d1 = diff(rows_by, lab, m, h1)[0]
            d2 = diff(rows_by, lab, m, h2)[0]
            vd = verdict(d_all, ci, d1, d2, nr, npo, floor) if cov_ok and (m != "m3" or shadow_ok) else "لا قياس"
            res["arms"][arm][m] = {"rich": a, "poor": b, "n_rich": nr, "n_poor": npo, "diff": d_all, "ci": list(ci),
                                   "h1": d1, "h2": d2, "verdict": vd}
        if arm == "B":
            res["rich_alert_share"] = (sum(len(rs) for d, rs in a_by.items() if lab.get(d) == "rich") / len(alerts)) if alerts else None
    res["spearman"] = spearman([per_day[d].get("P") for d in ok_days], [per_day[d].get("B") for d in ok_days])
    res["dist"] = {arm: sorted(per_day[d].get(arm) for d in ok_days) for arm in ("B", "P")}
    res["predictions"] = predictions(res)
    return res


def _p(x):
    return "—" if x is None else f"{x * 100:.1f}%"


def report_lines(res):
    g = res["gates"]
    L = [f"🧮 جلساتٌ بمرجعٍ كامل {g['days_ok']} من {g['days']} · كونٌ {g['cands']} · شموعٌ تعذّرت {g['bars_failed']} · بلغ ‏+20% نظاميًّا {g['up20']} "
         f"(خبرٌ مجهول {g['unk']}) · تنبيهات {g['alerts']} (اتّساق ① {g['consist']}) · أسماءُ S {g['s_rows']} (السجلّ {'✅' if g['shadow_ok'] else '⛔'}) · "
         f"أعلى البري فوق أعلى المجمَّعة {g['pre_over_hl']} · نداءات {g['calls']} · تعذّر {g['fails']}",
         f"بوّاباتُ التغطية: {'✅ عبرت' if res['cov_ok'] else '⛔ لم تعبر ⟵ «لا قياس»'}", ""]
    names = {"m1": "① ‏+7% قبل الخروج", "m2": "② النتيجةُ الصافية (وسيط)", "m3": "③ دقّةُ S (+100%)"}
    for arm, title in (("B", "ذراعُ «عرض الزخم» B"), ("P", "ذراعُ «عرض البري» P (قبل الافتتاح)")):
        nc = res["n_class"].get(arm) or {}
        L.append(f"### {title} — الوسيط {res['med'].get(arm)} · غنيّة {nc.get('rich')} جلسة · فقيرة {nc.get('poor')}")
        L.append("| المقياس | الغنيّة | الفقيرة | الفرق | فاصلُ 95% (جلسات) | النصفان | الحكم |")
        L.append("|---|---|---|---|---|---|---|")
        for m in ("m1", "m2", "m3"):
            x = res["arms"][arm][m]
            fmt = (lambda v: "—" if v is None else f"{v * 100:+.2f}%") if m == "m2" else _p
            lo, hi = x["ci"]
            L.append(f"| {names[m]} | {fmt(x['rich'])} (n {x['n_rich']}) | {fmt(x['poor'])} (n {x['n_poor']}) | {fmt(x['diff'])} | "
                     f"[{fmt(lo)}، {fmt(hi)}] | {fmt(x['h1'])} · {fmt(x['h2'])} | **{x['verdict']}** |")
        L.append("")
    L.append(f"وصفًا: سبيرمان (P، B) {res['spearman']} · حصّةُ التنبيهات في أيّام B الغنيّة {_p(res.get('rich_alert_share'))} · "
             f"توزيعُ B {res['dist']['B']} · توزيعُ P {res['dist']['P']}")
    L.append("")
    for c, ok, why in res["predictions"]:
        L.append(f"- `{c}` {'✅' if ok else '❌'} ({why})")
    return L


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--mode", required=True, choices=("shard", "report"))
    p.add_argument("--shard", type=int, default=0)
    p.add_argument("--src", default="vwap_cont_shards")
    p.add_argument("--out", default="")
    p.add_argument("--in", dest="in_dir", default="mktday_shards")
    a = p.parse_args(argv)
    if not contract_ok():
        log(f"⛔ بصمةُ العقد `{CONTRACT}` تغيّرت أو غاب — المدموجُ لا يُعدَّل (خروج {CONTRACT_RC})")
        return CONTRACT_RC
    import market_calendar as MC
    import vwap_cont as VC
    if a.mode == "report":
        shards = []
        for path in sorted(glob.glob(os.path.join(a.in_dir, "**", "*.json"), recursive=True)):
            with open(path, encoding="utf-8") as f:
                shards.append(json.load(f))
        res = analyze(shards, VC.sessions(MC))
        for ln in report_lines(res):
            log(ln)
        log("MKTDAY_JSON " + json.dumps(res, ensure_ascii=False, default=str))
        return 0 if res["cov_ok"] else 4
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log("⛔ لا مفتاح Polygon — لا عمل (يُعلَن ولا يُكتَم)")
        return 2
    if not (0 <= a.shard < VC.N_SHARDS) or not a.out:
        log("⛔ --shard في [0، 3) و--out إلزاميّان")
        return 2
    import vwap_momentum_live as V
    net = V.Net(key, (os.environ.get("SEC_CONTACT") or "").strip())
    out = mode_shard(net, MC, a.shard, a.src)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    log(f"🗂️ الشظيّة {a.shard}: جلسات {len(out['days'])} · تنبيهات {len(out['alerts'])} من {out['src_alerts']} · S {len(out['s_rows'])} · "
        f"نداءات {out['calls']} · تعذّر {out['fails']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
