# -*- coding: utf-8 -*-
"""🧭📐 اختبارُ الكون الكامل (UNIVERSE_TEST_PROTOCOL.md) — يقيس عبءَ الفرز والتقاطَ حالات فيصل والتركّزَ للمحرّك مقابل البوت.
المدخلات: data/universe_manifest.json (التواريخ · جدارُ اللمستين · reject_stats) · data/universe_bars.json.gz (شموعٌ من رنر) ·
fm_forensics/phase3/FAISAL_TIMELINE.csv · out/replay_units.csv (قراءةُ المحرّك عند تاريخ فيصل) · weekly_watchlist.json (الإضافات).
المخرجات: out/universe_daily.csv · out/universe_stages.csv · out/universe_summary.json · UNIVERSE_TEST_RESULT.md. قراءةٌ فقط."""
import csv
import gzip
import json
import math
import os
import sys
import time

os.environ["FAISAL_ONLY"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
for p in (HERE, os.path.join(ROOT, "fm_forensics", "phase3"), os.path.join(ROOT, "fm_forensics", "phase4")):
    sys.path.insert(0, p)
import engine as E          # noqa: E402

OUT = os.environ.get("FE_OUT") or os.path.join(HERE, "out")
MAN = os.path.join(HERE, "data", "universe_manifest.json")
BARS = os.path.join(HERE, "data", "universe_bars.json.gz")
IN_PROCESS = ("FOCUS", "WATCH", "READY", "TRIGGER", "HOLD")
WATCH_STAGES = ("READY", "HOLD")
STATES = ("FOCUS", "WATCH", "READY", "ENTRY")


def wilson(k, n, z=1.96):
    if not n:
        return (None, None, None)
    p = k / n; den = 1 + z * z / n; c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (round(p, 5), round(c - h, 5), round(c + h, 5))


def _median(xs):
    xs = sorted(xs)
    return None if not xs else (xs[len(xs) // 2] if len(xs) % 2 else (xs[len(xs) // 2 - 1] + xs[len(xs) // 2]) / 2)


def load():
    man = json.load(open(MAN, encoding="utf-8"))
    bars = json.load(gzip.open(BARS, "rt", encoding="utf-8"))
    return man, bars


def faisal_units(man):
    lo, hi = man["window"]
    rows = [r for r in csv.DictReader(open(os.path.join(ROOT, "fm_forensics", "phase3", "FAISAL_TIMELINE.csv"), encoding="utf-8"))
            if r["IS_FAISAL"] == "1" and r["OBSERVATION_CLASS"] in STATES and len(r["DATE"]) == 10]
    rep = {(r["ticker"], r["session"], r["state"], r["evidence_id"]): r for r in csv.DictReader(open(os.path.join(OUT, "replay_units.csv"), encoding="utf-8"))}
    out = []
    for r in rows:
        key = next((k for k in rep if k[0] == r["TICKER"] and k[3] == r["EVIDENCE_ID"]), None)
        rr = rep.get(key) if key else None
        sess = rr["session"] if rr else r["DATE"]
        if not (lo <= sess <= hi):
            continue
        out.append(dict(ticker=r["TICKER"], session=sess, state=r["OBSERVATION_CLASS"], evidence_id=r["EVIDENCE_ID"],
                        engine_stage=(rr["stage"] if rr else "NO_REPLAY"), base_result=(rr["base_result"] if rr else "NO_REPLAY")))
    return out


def nearest_date(man, session):
    """أقربُ تاريخِ تشغيلٍ كامل ≤ الجلسة (قراءةُ البوت صباحَ ذلك اليوم بشموعٍ قبله)."""
    ds = [d for d in man["dates"] if d <= session]
    return ds[-1] if ds else None


def stage_table(man, bars, log):
    """مراحلُ المحرّك لكلّ (تاريخ · رمزٌ في جدار اللمستين) بشموعٍ < التاريخ."""
    rows = []; cache = {}
    for d in man["dates"]:
        syms = man["anchor_wall"][d]
        for s in syms:
            b = bars["daily"].get(s)
            if not b:
                rows.append(dict(date=d, symbol=s, stage="NO_BARS", tech_state="", first_failed="")); continue
            ctx = {"splits": ([(x[0], x[1]) for x in bars["splits"].get(s)] if bars["splits"].get(s) is not None else None),
                   "sec_filings": None, "float_shares": None, "short_available": None, "groups": None, "operator_press": None}
            rec = E.evaluate(s, b, d, ctx, label="HISTORICAL")
            rows.append(dict(date=d, symbol=s, stage=rec["stage"], tech_state=(rec.get("v4") or {}).get("tech_state", ""),
                             first_failed=((rec.get("first_failed") or {}).get("rule", "")), frame=(rec.get("screen") or {}).get("frame", "")))
        done = sum(1 for r in rows if r["date"] == d)
        print(f"{d}: {done} رموز الجدار · بلا شموع {sum(1 for r in rows if r['date'] == d and r['stage'] == 'NO_BARS')}", file=log, flush=True)
    return rows


def main():
    os.makedirs(OUT, exist_ok=True)
    log = open(os.path.join(OUT, "universe_run.log"), "w", encoding="utf-8")
    t0 = time.time()
    man, bars = load()
    wl = json.load(open(os.path.join(ROOT, "weekly_watchlist.json"), encoding="utf-8"))
    adds = {}
    for h in wl.get("history", []):
        for s in h.get("stocks", []):
            adds[s.get("added")] = adds.get(s.get("added"), 0) + 1
    for s in wl.get("stocks", []):
        adds[s.get("added")] = adds.get(s.get("added"), 0) + 1
    st_rows = stage_table(man, bars, log)
    daily = []
    for d in man["dates"]:
        rs = man["reject_stats"][d]; valid = rs["valid"]; rej = sum(rs["stats"].values()); pas = valid - rej
        wall = len(man["anchor_wall"][d]); sr = [r for r in st_rows if r["date"] == d]
        cnt = {k: sum(1 for r in sr if r["stage"] == k) for k in IN_PROCESS + ("REJECTED", "INSUFFICIENT_DATA", "NO_BARS")}
        inproc = sum(cnt[k] for k in IN_PROCESS); watch = sum(cnt[k] for k in WATCH_STAGES)
        daily.append(dict(date=d, universe=rs["universe"], valid=valid, bot_pass=pas, bot_pass_pct=round(pas / valid * 100, 3) if valid else None,
                          bot_added=adds.get(d, 0), wall=wall, engine_screen=pas + wall, engine_screen_pct=round((pas + wall) / valid * 100, 3) if valid else None,
                          wall_with_bars=wall - cnt["NO_BARS"], wall_inproc=inproc, wall_focus=cnt["FOCUS"], wall_watch=cnt["WATCH"], wall_ready=cnt["READY"], wall_hold=cnt["HOLD"],
                          wall_rejected=cnt["REJECTED"], wall_insufficient=cnt["INSUFFICIENT_DATA"], wall_nobars=cnt["NO_BARS"],
                          engine_inproc_lo=inproc, engine_inproc_hi=inproc + pas, engine_watch_lo=watch, engine_watch_hi=watch + pas))
    # Faisal units
    U = faisal_units(man); units = []
    for u in U:
        d = nearest_date(man, u["session"]); inwall = (d is not None and u["ticker"] in set(man["anchor_wall"][d]))
        bot = (u["base_result"] == "PASS"); eng_inproc = u["engine_stage"] in IN_PROCESS
        evaluable = u["engine_stage"] not in ("NO_BARS", "NO_REPLAY")
        units.append(dict(**u, run_date=d or "", in_wall=int(inwall), bot_flag=int(bot), engine_screen=int(bot or inwall),
                          engine_flag=int(evaluable and eng_inproc and (bot or inwall)), engine_flag_replay=int(eng_inproc), engine_watch=int(u["engine_stage"] in WATCH_STAGES),
                          evaluable=int(evaluable), consistent=int((bot or inwall) == eng_inproc) if evaluable else ""))
    ev = [u for u in units if u["evaluable"]]
    nb = len(ev); kb = sum(u["bot_flag"] for u in ev); ke = sum(u["engine_flag"] for u in ev); kw = sum(u["engine_watch"] for u in ev); ks = sum(u["engine_screen"] for u in ev)
    # background rates (symbol-days)
    tot_valid = sum(r["valid"] for r in daily); tot_pass = sum(r["bot_pass"] for r in daily); tot_screen = sum(r["engine_screen"] for r in daily)
    tot_in_lo = sum(r["engine_inproc_lo"] for r in daily); tot_in_hi = sum(r["engine_inproc_hi"] for r in daily)
    tot_w_lo = sum(r["engine_watch_lo"] for r in daily); tot_w_hi = sum(r["engine_watch_hi"] for r in daily)
    pb = wilson(tot_pass, tot_valid); ps = wilson(tot_screen, tot_valid); pin = (wilson(tot_in_lo, tot_valid), wilson(tot_in_hi, tot_valid)); pw = (wilson(tot_w_lo, tot_valid), wilson(tot_w_hi, tot_valid))
    cb = wilson(kb, nb); cs = wilson(ks, nb); ce = wilson(ke, nb); cw = wilson(kw, nb)
    def lr(c, p):
        return round(c[0] / p[0], 2) if c[0] and p[0] else None
    cov = [r["wall_with_bars"] / r["wall"] for r in daily if r["wall"]]
    summary = {
        "protocol": "UNIVERSE_TEST_PROTOCOL.md", "label": "EXPLORATORY", "runtime_s": round(time.time() - t0, 1),
        "dates": len(daily), "window": man["window"], "excluded_sampled_dates": "see manifest (walls_n > 400)",
        "faisal_units_window": len(units), "faisal_units_evaluable": nb, "faisal_units_unevaluable": len(units) - nb,
        "capture": {"bot_pass": cb, "engine_screen": cs, "engine_inproc": ce, "engine_watch_stage": cw},
        "burden_daily": {"bot_pass_median": _median([r["bot_pass"] for r in daily]), "bot_pass_range": [min(r["bot_pass"] for r in daily), max(r["bot_pass"] for r in daily)],
                         "bot_added_median": _median([r["bot_added"] for r in daily]), "engine_screen_median": _median([r["engine_screen"] for r in daily]),
                         "engine_screen_range": [min(r["engine_screen"] for r in daily), max(r["engine_screen"] for r in daily)],
                         "engine_inproc_median_lo_hi": [_median([r["engine_inproc_lo"] for r in daily]), _median([r["engine_inproc_hi"] for r in daily])],
                         "engine_watch_median_lo_hi": [_median([r["engine_watch_lo"] for r in daily]), _median([r["engine_watch_hi"] for r in daily])],
                         "wall_ready_median": _median([r["wall_ready"] for r in daily]), "valid_median": _median([r["valid"] for r in daily])},
        "universe_fraction": {"bot_pass": pb, "bot_added_pct_median": _median([round(r["bot_added"] / r["valid"] * 100, 3) for r in daily if r["valid"]]),
                              "engine_screen": ps, "engine_inproc_lo_hi": pin, "engine_watch_lo_hi": pw},
        "concentration_LR": {"bot_pass": lr(cb, pb), "engine_screen": lr(cs, ps), "engine_inproc_lo_hi": [lr(ce, pin[1]), lr(ce, pin[0])], "engine_watch_lo_hi": [lr(cw, pw[1]), lr(cw, pw[0])]},
        "consistency_wall_vs_replay": {"agree": sum(1 for u in ev if u["consistent"] == 1), "n": nb},
        "coverage": {"wall_bars_mean": round(sum(cov) / len(cov), 4) if cov else None, "symbols_asked": bars["meta"]["asked"], "symbols_got": bars["meta"]["got"]},
        "unknown_note": "كلُّ رمزٍ من الكون لم يذكره فيصل = UNKNOWN (لا إنذارَ كاذبًا مؤكَّدًا) — سجلّاتُه لا تغطّي اختياراته كلَّها",
    }
    # verdict per §⑤
    undecidable = (summary["coverage"]["wall_bars_mean"] or 0) < 0.8 or len(daily) < 20 or nb < 20
    lr_e = summary["concentration_LR"]["engine_inproc_lo_hi"][0]; lr_b = summary["concentration_LR"]["bot_pass"]
    disjoint = (ce[1] is not None and cb[2] is not None and ce[1] > cb[2])
    burden_ok = (summary["burden_daily"]["engine_inproc_median_lo_hi"][1] or 1e9) <= 2 * (summary["burden_daily"]["bot_pass_median"] or 0)
    if undecidable:
        verdict = "لا يمكن الحسم بسبب نقص محدد في البيانات"
    elif lr_e is not None and lr_b is not None and lr_e > lr_b and disjoint and burden_ok:
        verdict = "توجد أدلة على تحسن الفرز"
    else:
        verdict = "لا توجد أدلة كافية على تحسن الفرز"
    summary["verdict"] = verdict
    summary["verdict_inputs"] = {"undecidable": undecidable, "lr_engine_lo": lr_e, "lr_bot": lr_b, "capture_ci_disjoint": disjoint, "burden_ok": burden_ok}
    summary["falsification"] = {"P1_burden_ratio_screen_over_bot": (round(summary["burden_daily"]["engine_screen_median"] / summary["burden_daily"]["bot_pass_median"], 2) if summary["burden_daily"]["bot_pass_median"] else None),
                                "P2_engine_capture_gt_bot_but_LR_not_disjoint": bool(ce[0] is not None and cb[0] is not None and ce[0] > cb[0] and not disjoint),
                                "P3_wall_ready_median": summary["burden_daily"]["wall_ready_median"]}
    keys = list(daily[0].keys())
    with open(os.path.join(OUT, "universe_daily.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(daily)
    with open(os.path.join(OUT, "universe_stages.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "symbol", "stage", "tech_state", "first_failed", "frame"]); w.writeheader(); w.writerows([{k: r.get(k, "") for k in ["date", "symbol", "stage", "tech_state", "first_failed", "frame"]} for r in st_rows])
    with open(os.path.join(OUT, "universe_units.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(units[0].keys())); w.writeheader(); w.writerows(units)
    json.dump(summary, open(os.path.join(OUT, "universe_summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    write_md(summary, daily, units)
    print(json.dumps({k: summary[k] for k in ("verdict", "capture", "burden_daily", "concentration_LR", "coverage")}, ensure_ascii=False, indent=1))


def pct(t):
    return "—" if not t or t[0] is None else f"{t[0]*100:.2f}% [{t[1]*100:.2f}، {t[2]*100:.2f}]"


def write_md(S, daily, units):
    c = S["capture"]; b = S["burden_daily"]; u = S["universe_fraction"]; L = S["concentration_LR"]
    s = ["# 🧭📐 UNIVERSE_TEST_RESULT — عبءُ الفرز على الكون الكامل: المحرّك مقابل البوت", "",
         f"> البروتوكول `UNIVERSE_TEST_PROTOCOL.md` (مدموجٌ قبل الرقم) · الوسم {S['label']} · تواريخُ كاملة **{S['dates']}** ({S['window'][0]} ⟵ {S['window'][1]}) · زمن {S['runtime_s']} ث.",
         f"> تغطيةُ شموع جدار اللمستين: {S['coverage']['wall_bars_mean']*100:.1f}% (طُلب {S['coverage']['symbols_asked']} · وصل {S['coverage']['symbols_got']}).", "",
         "## ① التقاطُ حالات فيصل المؤرَّخة داخل النافذة",
         f"- وحداتٌ في النافذة {S['faisal_units_window']} · قابلةٌ للتقييم **{S['faisal_units_evaluable']}** · غيرُ قابلة {S['faisal_units_unevaluable']} (بلا شموع/بلا إعادة).",
         "| النظام | الالتقاط (Wilson 95%) |", "|---|---|",
         f"| البوت (PASS يومَها) | {pct(c['bot_pass'])} |", f"| المحرّك — الفرزُ (PASS أو جدارُ اللمستين يومَها) | {pct(c['engine_screen'])} |",
         f"| المحرّك — في المسار (الفرزُ ∧ مرحلةُ FOCUS/WATCH/READY/HOLD) | {pct(c['engine_inproc'])} |", f"| المحرّك — مرحلةُ READY/HOLD | {pct(c['engine_watch_stage'])} |",
         f"- اتّساقُ عضويّة الجدار يومَها مع قراءة المحرّك من الملفّ المجمَّد: {S['consistency_wall_vs_replay']['agree']}/{S['consistency_wall_vs_replay']['n']}.", "",
         "## ② العبءُ اليوميّ من الكون (وسيط عبر التواريخ · المدى)", "| المقياس | البوت | المحرّك |", "|---|---|---|",
         f"| مرشَّحون/يوم (فرز) | {b['bot_pass_median']} {b['bot_pass_range']} | {b['engine_screen_median']} {b['engine_screen_range']} |",
         f"| في المسار/يوم | — | [{b['engine_inproc_median_lo_hi'][0]}، {b['engine_inproc_median_lo_hi'][1]}] (جدارٌ فقط ⟵ + PASS مجهولُ المرحلة) |",
         f"| READY+HOLD/يوم | إضافاتُ القائمة {b['bot_added_median']} | [{b['engine_watch_median_lo_hi'][0]}، {b['engine_watch_median_lo_hi'][1]}] |",
         f"| الكونُ الصالح/يوم | {b['valid_median']} | {b['valid_median']} |", "",
         "## ③ نسبةُ الكون", f"- البوت PASS {pct(u['bot_pass'])} · إضافاتُ القائمة (وسيط) {u['bot_added_pct_median']}% · المحرّك فرزٌ {pct(u['engine_screen'])} · في المسار [{pct(u['engine_inproc_lo_hi'][0])} ⟵ {pct(u['engine_inproc_lo_hi'][1])}] · READY/HOLD [{pct(u['engine_watch_lo_hi'][0])} ⟵ {pct(u['engine_watch_lo_hi'][1])}].", "",
         "## ④ التركّزُ حول حالات فيصل مقابل خلفيّة الكون (LR = الالتقاط ÷ نسبة الكون)",
         f"- البوت PASS: **{L['bot_pass']}** · المحرّك فرزٌ: **{L['engine_screen']}** · المحرّك في المسار: **[{L['engine_inproc_lo_hi'][0]}، {L['engine_inproc_lo_hi'][1]}]** · READY/HOLD: [{L['engine_watch_lo_hi'][0]}، {L['engine_watch_lo_hi'][1]}].",
         "- ⚠️ الخلفيّةُ تحمل حالاتِ فيصل غيرَ المسجَّلة ⟵ LR محافظٌ للنظامين معًا، والمقارنةُ بينهما هي المعنى.", "",
         "## ⑤ غيرُ القابل للتقييم", f"- حالاتُ فيصل بلا شموع/إعادة: {S['faisal_units_unevaluable']} · رموزُ PASS مجهولةُ الهُويّة (المدى) · {S['unknown_note']}.", "",
         "## ⑥ الضوابطُ السابقة", "- ضوابطُ المرحلة 4 = جدارُ اللمستين بالبناء ⟵ منحازةٌ إلى ما اجتاز بقيّةَ المرشِّحات ⟵ **لم تُستعمل**؛ المرجعُ هنا الكونُ الذي فرزه البوت يومَها.", "",
         "## ⑦ التنبّؤات", f"- {S['falsification']}", "",
         f"## ⑧ الحكم: **{S['verdict']}**", f"- مدخلاتُ الحكم: {S['verdict_inputs']}"]
    open(os.path.join(HERE, "UNIVERSE_TEST_RESULT.md"), "w", encoding="utf-8").write("\n".join(s) + "\n")


if __name__ == "__main__":
    main()
