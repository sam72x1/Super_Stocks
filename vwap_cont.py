#!/usr/bin/env python3
"""🟠🔬 `T-VWAP-CONT` — «مَن يواصل بعد تنبيه الفيواب؟» على إعادة 60 جلسة بالملحق 5 (العقد `vwap_cont_prereg.md`) — قراءةٌ فقط.

`--mode shard`: جلساتُ شظيّةٍ من الستّين ⟵ محاكاةُ الحلقة الحيّة بالاسم (`Day` · `prefilter` · `_replay_got`) ⟵ لكلّ تنبيه: النتيجةُ (`harvest.max_gain`
‏+10%) والسماتُ السبع والضابطُ المطابِق ⟵ ملفُّ JSON. `--mode report`: الشظايا ‏+ الـ61 الحيّة (وصفًا) ⟵ جدولُ الشرائح · Wilson · أرضيّةُ 20 ·
«يفرّق» (عدمُ التداخل ‏+ النصفان) · شرطُ الاقتراح (الضابط) · والتنبّؤات C0-C9.
`--mode reading` (الملحق 1 · `vwap_cont_addendum_1.md`): الشظايا المحفوظة ⟵ الجدولُ نفسُه بمقياس العقد (① ‏+7% قبل الخروج · ② النتيجةُ الصافية) ‏+ A1-A8.
🔒 لا تلغرام · لا كتابة في المستودع · لا تغيير إنتاجيّ · وتخرج 9 إن تغيّرت بصمةُ العقد.
"""
import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import sys

import vwap_judge as J
import vwap_momentum_live as V

CONTRACT = "vwap_cont_prereg.md"
CONTRACT_SHA = "0c9fd7e092fe044590352d33618dd796898d9d67eb851e585f809d5103547cea"
CONTRACT_RC = 9
END_DAY = "2026-11-05"
N_DAYS = 60
N_SHARDS = 3
WIN = 0.10                         # §② «حصة ≥+10%» (`nayef_verbatim`)
FLOOR = 20                         # §④ أرضيّةُ الشريحة
GAP_MIN = 0.20                     # §③ ③ = `CHG_MIN`
DAYS_OK_MIN = 54                   # §① بوّابةُ التغطية: 54 من 60
BARS_FAIL_MAX = 0.02               # §① والشموعُ المتعذّرة 2% من المرشّحين أو أقلّ
LIVE_FROM, LIVE_TO = "2026-11-02", "2026-11-05"   # §⑥ الـ61 الحيّة


def log(m=""):
    print(m, flush=True)


def contract_ok(path=CONTRACT):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest() == CONTRACT_SHA
    except OSError:
        return False


def sessions(MC, end_day=END_DAY, n=N_DAYS):
    days, d = [], dt.date.fromisoformat(end_day)
    while len(days) < n:
        if V.V3.is_session(d.isoformat(), MC.session_info):
            days.append(d.isoformat())
        d -= dt.timedelta(1)
    return days[::-1]


def shard_days(days, k, of=N_SHARDS):
    """شظيّةٌ متّصلة: k ∈ [0، of) ⟵ جلساتُها بالترتيب."""
    m = -(-len(days) // of)
    return days[k * m:(k + 1) * m]


# ── السماتُ (نقيّة) ──────────────────────────────────────────────────────────────────
def earn8k(news_detail):
    """② «8-K أرباح» = آخرُ 8-K في النافذة بنودُه تشمل 2.02."""
    si = (news_detail or {}).get("sec_item") or {}
    return "2.02" in [x.strip() for x in str(si.get("items") or "").split(",")]


def earn8k_text(news):
    """② للحيّة من نصّ الخبر المعروض (`news_brief`): «إيداع 8-K (بنود … 2.02 …)»."""
    s = str(news or "")
    if not s.startswith("إيداع 8-K"):
        return False
    i, j = s.find("(بنود "), s.find(")")
    return i >= 0 and j > i and "2.02" in [x.strip() for x in s[i + 6:j].split(",")]


def gap_of(bars, op, prev):
    """③ افتتاحُ أوّل دقيقةٍ نظاميّة ÷ إغلاقِ الأمس − 1 ⟵ أو None."""
    o = next((b[1] for b in bars if b[0] >= op), None)
    return None if (o is None or not prev) else o / prev - 1.0


def vol_rising(bars, e):
    """④ حجمُ الأسهم في شموع 5د الثلاث المنتهية عند e صاعدٌ تمامًا (v1 أقلّ من v2 أقلّ من v3)."""
    v = [sum(b[5] for b in bars if e - 15 + 5 * k <= b[0] < e - 10 + 5 * k) for k in range(3)]
    return v[0] < v[1] < v[2]


def tertile_cuts(xs):
    """فاصلا الأثلاث (المئينان 33.3 و66.7 بالرتبة) ⟵ (c1، c2) · والقيمةُ حتى c1 الأدنى · حتى c2 الأوسط · وما فوقه الأعلى."""
    s = sorted(xs)
    n = len(s)
    if n < 3:
        return None
    return s[-(-n // 3) - 1], s[-(-2 * n // 3) - 1]


def tier(x, cuts):
    if x is None or cuts is None:
        return None
    return 1 if x <= cuts[0] else (2 if x <= cuts[1] else 3)


# ── الشظيّة ────────────────────────────────────────────────────────────────────────
def alert_record(D, day, sym, bars, row, cap_shares):
    """صفُّ تنبيهٍ بنتيجته وسماته وضابطه (الإعادة)."""
    e, px = row["event_end_mod"], row["px"]
    h = V.harvest(bars, D.op, D.cl, e, px)

    def win(t, p, _b=bars):
        g = V.harvest(_b, D.op, D.cl, t, p)["max_gain"]
        return int(g is not None and g >= WIN)
    prev = D.prev_adj(sym)
    return {"date": day, "sym": sym, "arm": row["arm"], "n": row["n"], "kind": row.get("candle"), "e": e, "px": px,
            "tail": e >= D.cl - J.TAIL_MIN, "max_gain": h["max_gain"], "win": int(h["max_gain"] is not None and h["max_gain"] >= WIN),
            "reach7": J.reach(bars, D.op, D.cl, e, px), "earn": earn8k(row.get("news_detail")),
            "gap": gap_of(bars, D.op, prev), "vol_up": vol_rising(bars, e),
            "cap": (px * cap_shares) if cap_shares else None, "slot": J.slot_of(e),
            "ctl_slot": J.control_prob(bars, D.op, D.cl, win, slot=J.slot_of(e)), "ctl_day": J.control_prob(bars, D.op, D.cl, win),
            "news": row.get("news")}


def shares_of(net, sym, day):
    j = net.poly(f"/v3/reference/tickers/{sym}", {"date": day})
    r = (j or {}).get("results") or {}
    return r.get("weighted_shares_outstanding") or r.get("share_class_shares_outstanding")


def mode_shard(net, MC, k):
    days = shard_days(sessions(MC), k)
    out = {"shard": k, "days": days, "per_day": {}, "alerts": []}
    for day in days:
        D = V.Day(net, day, MC, replay=True)
        g = net.poly(f"/v2/aggs/grouped/locale/us/market/stocks/{day}", {"adjusted": "false"})
        hl = {str(r.get("T") or "").upper(): (r.get("h"), r.get("l"), r.get("v")) for r in ((g or {}).get("results") or []) if r.get("T")}
        if not D.ok or not hl:
            out["per_day"][day] = {"ok": False, "why": D.why + ([] if hl else ["شمعةُ اليوم المجمَّعة"])}
            log(f"⛔ {day}: مرجعٌ ناقص {out['per_day'][day]['why']}")
            continue
        cands = sorted(V.prefilter(hl, D.prev_adj_pf, D.types))
        bounds = V._boundary_mods(D.op, D.cl, D.op, D.cl)
        miss = na = 0
        for sym in cands:
            by = net.minutes(sym, day, day)
            if by is None:
                miss += 1
                continue
            bars = by.get(day)
            if not bars:
                continue
            got = V._replay_got(D, day, sym, bars, bounds)
            if not got:
                continue
            sh = shares_of(net, sym, day)
            for kk in sorted(got, key=lambda x: (x[0] != "A", x[1])):
                out["alerts"].append(alert_record(D, day, sym, bars, got[kk], sh))
                na += 1
        out["per_day"][day] = {"ok": True, "candidates": len(cands), "bars_failed": miss, "alerts": na}
        log(f"📅 {day}: مرشّحون {len(cands)} · شموعٌ تعذّرت {miss} · تنبيهات {na}")
    out["calls"], out["fails"] = net.calls, net.fails
    return out


# ── التقرير (نقيّ على الصفوف) ──────────────────────────────────────────────────────────
def share(rows):
    n = len(rows)
    k = sum(r["win"] for r in rows)
    return {"n": n, "k": k, "p": (k / n) if n else None, "w": J.wilson(k, n)}


def _ctl(rows):
    xs = [r["ctl_slot"] for r in rows if r.get("ctl_slot") is not None]
    return (sum(xs) / len(xs)) if xs else None


ATTRS = (
    ("①", "الذراع A مقابل D", lambda r: "A" if r["arm"] == "A" else "D", ("A", "D")),
    ("①ب", "D#1 مقابل D#2 و3", lambda r: None if r["arm"] != "D" else ("D#1" if r["n"] == 1 else "D#2-3"), ("D#1", "D#2-3")),
    ("②", "8-K أرباح مقابل خبرٌ آخر", lambda r: "أرباح 8-K" if r["earn"] else "خبرٌ آخر", ("أرباح 8-K", "خبرٌ آخر")),
    ("③", "فجوةُ افتتاح مقابل مبنيّ", lambda r: None if r["gap"] is None else ("فجوة" if r["gap"] >= GAP_MIN else "مبنيّ"), ("فجوة", "مبنيّ")),
    ("④", "حجمُ الثبات صاعد", lambda r: "صاعد" if r["vol_up"] else "غيرُ صاعد", ("صاعد", "غيرُ صاعد")),
    ("⑤", "القيمةُ السوقيّة (أثلاث)", None, ("صغرى", "وسطى", "كبرى")),
    ("⑥", "السعر (أثلاث)", None, ("أرخص", "أوسط", "أغلى")),
    ("⑦", "وقتُ التنبيه", lambda r: ("09:30-10:30", "10:30-12:00", "12:00-14:00", "14:00-15:45")[r["slot"] - 1],
     ("09:30-10:30", "10:30-12:00", "12:00-14:00", "14:00-15:45")),
)


def labeler(code, cuts):
    for c, _t, fn, labs in ATTRS:
        if c != code:
            continue
        if code == "⑤":
            return lambda r: None if tier(r.get("cap"), cuts["cap"]) is None else labs[tier(r["cap"], cuts["cap"]) - 1]
        if code == "⑥":
            return lambda r: labs[tier(r["px"], cuts["px"]) - 1]
        return fn
    raise KeyError(code)


def separates(rows, lab, labs, halves):
    """§④ ⟵ (الحكم، الأعلى، الأدنى، شرطُ الاقتراح) — «يفرّق» = كلتاهما 20 فأكثر ∧ Wilson لا يتداخل ∧ الاتّجاهُ نفسُه في النصفين."""
    sl = {x: share([r for r in rows if lab(r) == x]) for x in labs}
    valid = [x for x in labs if sl[x]["n"] >= FLOOR]
    if len(labs) == 2:
        if len(valid) < 2:
            return "لا قياس", None, None, False
        hi, lo = sorted(labs, key=lambda x: -sl[x]["p"])
    else:
        if len(valid) < 2:
            return "لا قياس", None, None, False
        hi, lo = max(valid, key=lambda x: sl[x]["p"]), min(valid, key=lambda x: sl[x]["p"])
        if any(sl[x]["n"] < FLOOR for x in (hi, lo)):
            return "لا قياس", hi, lo, False
    if sl[hi]["w"][0] <= sl[lo]["w"][1]:
        return "لا يفرّق", hi, lo, False
    for half in halves:
        a = share([r for r in half if lab(r) == hi])
        b = share([r for r in half if lab(r) == lo])
        if not a["n"] or not b["n"] or not (a["p"] > b["p"]):
            return "لا يفرّق", hi, lo, False
    ex = lambda x: None if _ctl([r for r in rows if lab(r) == x]) is None else sl[x]["p"] - _ctl([r for r in rows if lab(r) == x])   # noqa: E731
    prop = ex(hi) is not None and ex(lo) is not None and ex(hi) > ex(lo)
    return "يفرّق", hi, lo, prop


def first_per_symday(rows):
    seen, out = set(), []
    for r in sorted(rows, key=lambda r: (r["date"], r["e"], r["arm"] != "A", r["n"])):
        if (r["date"], r["sym"]) not in seen:
            seen.add((r["date"], r["sym"]))
            out.append(r)
    return out


def report_lines(pop, live, cuts, half_split, n_tail, cov):
    """جدولُ الشرائح · والأحكام · والـ61 وصفًا."""
    h1 = [r for r in pop if r["date"] <= half_split]
    h2 = [r for r in pop if r["date"] > half_split]
    dd = first_per_symday(pop)
    p = lambda x: "—" if x is None else f"{x * 100:.1f}%"                      # noqa: E731
    tot = share(pop)
    L = ["# 🟠🔬 `T-VWAP-CONT` — النتيجة", "",
         f"المجتمعُ الحاكم {tot['n']} تنبيهًا ({cov}) · آخرُ ربع ساعة خارجه {n_tail} · ‏+10% حتى الإغلاق {tot['k']} = {p(tot['p'])} "
         f"[{p(tot['w'][0])}، {p(tot['w'][1])}] · والضابطُ المطابِق {p(_ctl(pop))} · و«+7% قبل الخروج» (وصفًا) "
         f"{p(sum(r['reach7'] for r in pop) / len(pop) if pop else None)}",
         f"فاصلا الأثلاث: القيمةُ السوقيّة {cuts['cap']} · السعر {cuts['px']} · وقيمةٌ سوقيّةٌ مجهولة {sum(1 for r in pop if r.get('cap') is None)}", "",
         "| السمة | الشريحة | n | ‏+10% | الحصة [Wilson 95%] | النصف 1 | النصف 2 | أوّلُ تنبيهٍ للرمز-اليوم | الضابط | الزيادة | +7% قبل الخروج | الحيّة (وصفًا) |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    verdicts = {}
    for code, title, _fn, labs in ATTRS:
        lab = labeler(code, cuts)
        for x in labs:
            rs = [r for r in pop if lab(r) == x]
            s, a, b = share(rs), share([r for r in h1 if lab(r) == x]), share([r for r in h2 if lab(r) == x])
            d = share([r for r in dd if lab(r) == x]) if code not in ("①", "①ب") else None
            lv = share([r for r in live if lab(r) == x])
            c = _ctl(rs)
            exc = "—" if c is None or s["p"] is None else f"{(s['p'] - c) * 100:+.1f}"
            fl = "" if s["n"] >= FLOOR else " (دون 20)"
            L.append(f"| {code} {title} | {x} | {s['n']}{fl} | {s['k']} | {p(s['p'])} [{p(s['w'][0])}، {p(s['w'][1])}] | {p(a['p'])} ({a['n']}) | "
                     f"{p(b['p'])} ({b['n']}) | {'—' if d is None else p(d['p']) + ' (' + str(d['n']) + ')'} | {p(c)} | "
                     f"{exc} | "
                     f"{p(sum(r['reach7'] for r in rs) / len(rs) if rs else None)} | {p(lv['p'])} ({lv['n']}) |")
        verdicts[code] = separates(pop, lab, labs, (h1, h2))
    L += ["", "| السمة | الحكم | الأعلى | الأدنى | شرطُ الاقتراح |", "|---|---|---|---|---|"]
    for code, title, _fn, _labs in ATTRS:
        v, hi, lo, prop = verdicts[code]
        L.append(f"| {code} {title} | **{v}** | {hi or '—'} | {lo or '—'} | "
                 f"{'✅ يُقترح ملحقًا 7' if prop else ('تفرّق لكنّ الضابطَ يفسّرها' if v == 'يفرّق' else '—')} |")
    return L, verdicts, tot


def live_rows(net, MC, rows):
    """§⑥ الـ61 الحيّة بالتعريفات نفسِها (وصفًا) — الخبرُ من النصّ المعروض · وإغلاقُ الأمس px ÷ (1 + chg)."""
    out, cache = [], {}
    for r in rows:
        if not (r.get("kind") == "alert" and r.get("sent") and r.get("def") == "A5" and LIVE_FROM <= str(r.get("date")) <= LIVE_TO):
            continue
        day, sym = r["date"], r["sym"]
        info = MC.session_info(day)
        op, cl = info["open_ny_min"], info["close_ny_min"]
        if r["event_end_mod"] >= cl - J.TAIL_MIN:
            continue
        if (sym, day) not in cache:
            by = net.minutes(sym, day, day)
            cache[(sym, day)] = ((by or {}).get(day), shares_of(net, sym, day))
        bars, sh = cache[(sym, day)]
        if not bars:
            continue
        px, e = r["px"], r["event_end_mod"]
        h = V.harvest(bars, op, cl, e, px)
        prev = px / (1.0 + r["chg"]) if r.get("chg") is not None else None
        out.append({"date": day, "sym": sym, "arm": r["arm"], "n": r["n"], "e": e, "px": px, "max_gain": h["max_gain"],
                    "win": int(h["max_gain"] is not None and h["max_gain"] >= WIN), "reach7": J.reach(bars, op, cl, e, px),
                    "earn": earn8k_text(r.get("news")), "gap": gap_of(bars, op, prev), "vol_up": vol_rising(bars, e),
                    "cap": (px * sh) if sh else None, "slot": J.slot_of(e), "ctl_slot": None})
    return out


def predictions(tot, n_tail, verdicts, pop):
    def v(c):
        return verdicts[c][0]
    hi = lambda c: verdicts[c][1]                                                     # noqa: E731
    prop_any = any(x[3] for x in verdicts.values())
    allp = len(pop) + n_tail
    return [
        ("C0", 300 <= tot["n"] <= 1500 and 0.05 <= (n_tail / allp if allp else 0) <= 0.20, f"{tot['n']} · المستبعَد {n_tail}"),
        ("C1", tot["p"] is not None and 0.10 <= tot["p"] <= 0.30, f"{tot['p']}"),
        ("C2", v("①") == "لا يفرّق" and hi("①") == "A" and v("①ب") in ("لا يفرّق", "لا قياس"), f"{v('①')} · الأعلى {hi('①')} · {v('①ب')}"),
        ("C3", v("②") == "لا يفرّق" and hi("②") == "خبرٌ آخر", f"{v('②')} · الأعلى {hi('②')}"),
        ("C4", v("③") == "لا يفرّق" and hi("③") == "مبنيّ", f"{v('③')} · الأعلى {hi('③')}"),
        ("C5", v("④") == "لا يفرّق", v("④")),
        ("C6", v("⑤") == "يفرّق" and hi("⑤") == "صغرى" and not verdicts["⑤"][3], f"{v('⑤')} · الأعلى {hi('⑤')} · اقتراح {verdicts['⑤'][3]}"),
        ("C7", v("⑥") == "يفرّق" and hi("⑥") == "أرخص" and not verdicts["⑥"][3], f"{v('⑥')} · الأعلى {hi('⑥')} · اقتراح {verdicts['⑥'][3]}"),
        ("C8", v("⑦") == "يفرّق" and hi("⑦") == "09:30-10:30" and not verdicts["⑦"][3], f"{v('⑦')} · الأعلى {hi('⑦')} · اقتراح {verdicts['⑦'][3]}"),
        ("C9", not prop_any, "لا اقتراح" if not prop_any else "اقتراحٌ قائم"),
    ]


def mode_report(net, MC, in_dir):
    days = sessions(MC)
    shards = []
    for path in sorted(glob.glob(os.path.join(in_dir, "**", "*.json"), recursive=True)):
        with open(path, encoding="utf-8") as f:
            shards.append(json.load(f))
    per_day = {}
    allr = []
    for s in shards:
        per_day.update(s.get("per_day") or {})
        allr.extend(s.get("alerts") or [])
    ok_days = [d for d in days if (per_day.get(d) or {}).get("ok")]
    cands = sum((per_day[d].get("candidates") or 0) for d in ok_days)
    miss = sum((per_day[d].get("bars_failed") or 0) for d in ok_days)
    cov_ok = len(ok_days) >= DAYS_OK_MIN and (cands and miss / cands <= BARS_FAIL_MAX)
    cov = f"جلساتٌ بمرجعٍ كامل {len(ok_days)} من {len(days)} · شموعٌ تعذّرت {miss} من {cands} مرشّحًا"
    log(f"📦 الشظايا {len(shards)} · {cov}")
    if not cov_ok:
        log("⛔ **لا قياس** — بوّابةُ التغطية (54 من 60 · والتعذّرُ 2% أو أقلّ) لم تعبر · وإعادةُ التشغيل بالتعريف نفسِه مسموحة")
        return 4
    pop = [r for r in allr if not r["tail"]]
    n_tail = len(allr) - len(pop)
    cuts = {"cap": tertile_cuts([r["cap"] for r in pop if r.get("cap") is not None]), "px": tertile_cuts([r["px"] for r in pop])}
    live = live_rows(net, MC, V.read_ledger())
    L, verdicts, tot = report_lines(pop, live, cuts, days[29], n_tail, cov)
    for ln in L:
        log(ln)
    log("")
    for c, ok, why in predictions(tot, n_tail, verdicts, pop):
        log(f"- `{c}` {'✅' if ok else '❌'} ({why})")
    log("CONT_JSON " + json.dumps({"cov": cov, "n": tot, "tail": n_tail, "cuts": cuts,
                                   "verdicts": {k: list(v) for k, v in verdicts.items()}, "live_n": len(live)},
                                  ensure_ascii=False, default=str))
    return 0


# ── الملحق 1: القراءةُ بمقياس العقد على الشظايا المحفوظة (`vwap_cont_addendum_1.md`) ─────────────────────────────────
ADDENDUM = "vwap_cont_addendum_1.md"
ADDENDUM_SHA = "5cd7451fb8c8a541ad518880e84c7e713298f97e454757d6d29798543a1397db"
SOURCE_RUN = 42134086032            # §① التشغيلةُ التي حُفظت شظاياها
CONSIST_MIN = 0.95                  # §① فحصُ الاتّساق: ① المعادُ = `reach7` المخزَّن
READ_BOOT_N = 2000                  # §④ ② بوتستراب عنقوديّ على الرمز-اليوم
READ_SEED = "VCA1"


def addendum_ok(path=ADDENDUM):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest() == ADDENDUM_SHA
    except OSError:
        return False


def net_ret(bars, op, cl, t, px):
    """§② ② النتيجةُ الصافية بوقف نايف: `harvest.ret_exit` إن أُغلقت شمعةُ 5د تحت الفيواب بعد t · وإلّا `ret_close`."""
    h = V.harvest(bars, op, cl, t, px)
    return h["ret_exit"] if h["exit_px"] is not None else h["ret_close"]


def _median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2.0


def reading_row(r, bars, op, cl):
    """صفُّ الشظيّة ⟵ نفسُه ‏+ المقياسان والضابطان (§②-§③) · و`win`/`ctl_slot` يُستبدلان بـ① وضابطه فتُعاد آلةُ العقد بالاسم."""
    e, px, slot = r["e"], r["px"], J.slot_of(r["e"])
    pts = J.control_points(bars, op, cl, slot=slot)
    c1 = (sum(J.reach(bars, op, cl, t, p) for t, p in pts) / len(pts)) if pts else None
    c2 = _median([net_ret(bars, op, cl, t, p) for t, p in pts]) if pts else None
    m1 = J.reach(bars, op, cl, e, px)
    return dict(r, win=m1, reach_new=m1, consistent=(m1 == r.get("reach7")), ret2=net_ret(bars, op, cl, e, px),
                ctl_slot=c1, ctl2=c2, n_ctl=len(pts))


def boot_median(rows, n=READ_BOOT_N, seed=READ_SEED):
    """فاصلُ 95% لوسيط ② بإعادة سحب عناقيد الرمز-اليوم ⟵ (أدنى، أعلى) أو (None، None)."""
    import random
    by = {}
    for r in rows:
        if r.get("ret2") is not None:
            by.setdefault((r["date"], r["sym"]), []).append(r["ret2"])
    keys = sorted(by)
    if len(keys) < 2:
        return (None, None)
    rnd = random.Random(seed)
    vals = []
    for _ in range(n):
        smp = []
        for _k in keys:
            smp.extend(by[keys[rnd.randrange(len(keys))]])
        vals.append(_median(smp))
    vals.sort()
    return (vals[int(0.025 * n)], vals[int(0.975 * n) - 1])


def reading_lines(pop, cuts, half_split):
    """§④ الجدولُ السباعيّ بمقياس العقد ⟵ (أسطر، أحكام، كلّيّ)."""
    h1 = [r for r in pop if r["date"] <= half_split]
    h2 = [r for r in pop if r["date"] > half_split]
    p = lambda x: "—" if x is None else f"{x * 100:.1f}%"                      # noqa: E731
    s2 = lambda x: "—" if x is None else f"{x * 100:+.2f}%"                    # noqa: E731
    tot = share(pop)
    b0 = boot_median(pop)
    L = ["# 🟠🔬① `T-VWAP-CONT` الملحق 1 — الجدولُ السباعيّ بمقياس العقد (① بلغ ‏+7% قبل إغلاق 5د تحت الفيواب · ② النتيجةُ الصافية)", "",
         f"المجتمعُ {tot['n']} · **①** {tot['k']} = {p(tot['p'])} [{p(tot['w'][0])}، {p(tot['w'][1])}] · ضابطُ ① {p(_ctl(pop))} · "
         f"**② الوسيط** {s2(_median([r['ret2'] for r in pop]))} [{s2(b0[0])}، {s2(b0[1])}] · ضابطُ ② {s2(_median([r['ctl2'] for r in pop]))} · "
         f"بلا حدٍّ ضابطٍ مؤهَّل {sum(1 for r in pop if r['ctl_slot'] is None)}", "",
         "| السمة | الشريحة | n | ① | الحصة [Wilson 95%] | النصف 1 | النصف 2 | ضابطُ ① | الزيادة | ② الوسيط [95%] | ضابطُ ② |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    verdicts = {}
    for code, title, _fn, labs in ATTRS:
        lab = labeler(code, cuts)
        for x in labs:
            rs = [r for r in pop if lab(r) == x]
            s, a, b = share(rs), share([r for r in h1 if lab(r) == x]), share([r for r in h2 if lab(r) == x])
            c = _ctl(rs)
            bm = boot_median(rs)
            exc = "—" if c is None or s["p"] is None else f"{(s['p'] - c) * 100:+.1f}"
            fl = "" if s["n"] >= FLOOR else " (دون 20)"
            L.append(f"| {code} {title} | {x} | {s['n']}{fl} | {s['k']} | {p(s['p'])} [{p(s['w'][0])}، {p(s['w'][1])}] | {p(a['p'])} ({a['n']}) | "
                     f"{p(b['p'])} ({b['n']}) | {p(c)} | {exc} | {s2(_median([r['ret2'] for r in rs]))} [{s2(bm[0])}، {s2(bm[1])}] | "
                     f"{s2(_median([r['ctl2'] for r in rs]))} |")
        verdicts[code] = separates(pop, lab, labs, (h1, h2))
    L += ["", "| السمة | الحكم على ① | الأعلى | الأدنى | شرطُ الاقتراح |", "|---|---|---|---|---|"]
    for code, title, _fn, _labs in ATTRS:
        v, hi, lo, prop = verdicts[code]
        tag = ("مفسَّرةٌ بقرار المالك (2026-11-06) — تُطبع ولا تُقترح" if code == "⑤"
               else ("✅ يُضاف إلى مقترَح الملحق 7 (لا يُبنى قبل حكم J30)" if prop else ("تفرّق لكنّ الضابطَ يفسّرها" if v == "يفرّق" else "—")))
        L.append(f"| {code} {title} | **{v}** | {hi or '—'} | {lo or '—'} | {tag} |")
    return L, verdicts, tot


def reading_predictions(pop, verdicts, consist):
    v = lambda c: verdicts[c][0]                                                     # noqa: E731
    tot = share(pop)
    m2, c2 = _median([r["ret2"] for r in pop]), _median([r["ctl2"] for r in pop])
    c1 = _ctl(pop)
    props = [c for c in verdicts if c != "⑤" and verdicts[c][3]]
    return [
        ("A1", v("③") == "لا يفرّق", f"③ {v('③')}"),
        ("A2", v("②") == "يفرّق" and not verdicts["②"][3], f"② {v('②')} · اقتراح {verdicts['②'][3]}"),
        ("A3", v("⑦") == "يفرّق" and not verdicts["⑦"][3], f"⑦ {v('⑦')} · اقتراح {verdicts['⑦'][3]}"),
        ("A4", m2 is not None and -0.03 <= m2 <= -0.005, f"وسيطُ ② {m2}"),
        ("A5", c1 is not None and tot["p"] is not None and c1 > tot["p"], f"ضابطُ ① {c1} مقابل {tot['p']}"),
        ("A6", m2 is not None and c2 is not None and m2 < c2, f"② {m2} مقابل ضابطه {c2}"),
        ("A7", not props, "لا اقتراح" if not props else "اقتراحٌ في " + " · ".join(props)),
        ("A8", consist is not None and consist >= CONSIST_MIN, f"الاتّساق {consist}"),
    ]


def mode_reading(net, MC, in_dir):
    """§⑥ الشظايا المحفوظة ⟵ الدقائقُ من جديد ⟵ المقياسان والضابطان ⟵ الجدولُ والأحكامُ وA1-A8 · و«لا قياس» دون بوّابتي التغطية والاتّساق."""
    days = sessions(MC)
    allr = []
    for path in sorted(glob.glob(os.path.join(in_dir, "**", "*.json"), recursive=True)):
        with open(path, encoding="utf-8") as f:
            allr.extend(json.load(f).get("alerts") or [])
    src = [r for r in allr if not r["tail"]]
    keys = sorted({(r["date"], r["sym"]) for r in src})
    bars_of, miss = {}, 0
    for day, sym in keys:
        by = net.minutes(sym, day, day)
        if by is None or not by.get(day):
            miss += 1
            continue
        bars_of[(day, sym)] = by[day]
    pop = []
    for r in src:
        bars = bars_of.get((r["date"], r["sym"]))
        if bars is None:
            continue
        info = MC.session_info(r["date"])
        pop.append(reading_row(r, bars, info["open_ny_min"], info["close_ny_min"]))
    consist = (sum(r["consistent"] for r in pop) / len(pop)) if pop else None
    cov = f"صفوفُ الشظايا {len(allr)} · بلا آخر ربع ساعة {len(src)} · رموزٌ-أيّام {len(keys)} · دقائقُ تعذّرت {miss} · الاتّساق {consist}"
    log(f"📦 {cov} · نداءات {net.calls} · تعذّر {net.fails}")
    if not src or (miss / len(keys) if keys else 1.0) > BARS_FAIL_MAX or consist is None or consist < CONSIST_MIN:
        log("⛔ **لا قياس** — بوّابةُ التغطية (2% أو أقلّ) أو الاتّساق (95% فأكثر) لم تعبر · والقراءةُ قبل انتهاء الـartifacts (≈2026-12-06)")
        return 4
    cuts = {"cap": tertile_cuts([r["cap"] for r in src if r.get("cap") is not None]), "px": tertile_cuts([r["px"] for r in src])}   # §① كما في الشظايا
    L, verdicts, tot = reading_lines(pop, cuts, days[29])
    for ln in L:
        log(ln)
    log("")
    for c, ok, why in reading_predictions(pop, verdicts, consist):
        log(f"- `{c}` {'✅' if ok else '❌'} ({why})")
    log("CONT_A1_JSON " + json.dumps({"cov": cov, "n": tot, "consist": consist, "cuts": cuts,
                                      "verdicts": {k: list(v) for k, v in verdicts.items()},
                                      "m2": _median([r["ret2"] for r in pop]), "c2": _median([r["ctl2"] for r in pop]), "c1": _ctl(pop)},
                                     ensure_ascii=False, default=str))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--mode", required=True, choices=("shard", "report", "reading"))
    p.add_argument("--shard", type=int, default=0)
    p.add_argument("--out", default="")
    p.add_argument("--in", dest="in_dir", default="vwap_cont_shards")
    a = p.parse_args(argv)
    if not contract_ok() or (a.mode == "reading" and not addendum_ok()):
        log(f"⛔ بصمةُ العقد `{CONTRACT}` أو الملحق `{ADDENDUM}` تغيّرت أو غاب — المدموجُ لا يُعدَّل (خروج {CONTRACT_RC})")
        return CONTRACT_RC
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log("⛔ لا مفتاح Polygon — لا عمل (يُعلَن ولا يُكتَم)")
        return 2
    import market_calendar as MC
    net = V.Net(key, (os.environ.get("SEC_CONTACT") or "").strip())
    if a.mode == "shard":
        if not (0 <= a.shard < N_SHARDS) or not a.out:
            log("⛔ --shard في [0، 3) و--out إلزاميّان")
            return 2
        out = mode_shard(net, MC, a.shard)
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False)
        log(f"🗂️ الشظيّة {a.shard}: جلسات {len(out['days'])} · تنبيهات {len(out['alerts'])} · نداءات {out['calls']} · تعذّر {out['fails']}")
        return 0
    if a.mode == "reading":
        return mode_reading(net, MC, a.in_dir)
    return mode_report(net, MC, a.in_dir)


if __name__ == "__main__":
    sys.exit(main())
