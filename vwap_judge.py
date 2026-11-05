#!/usr/bin/env python3
"""🟠⚖️ `T-VWAP-J30` — حكمُ «زخم الفيواب» الحيّ على أوّل 30 تنبيهًا قادمًا (العقد `vwap_live_judgment_prereg.md`) — قراءةٌ فقط.

لكلّ تنبيهٍ مُرسَلٍ بالملحق 5 من 2026-11-06 (بلا آخر ربع ساعة): هل بلغ ‏+7% (سلّم نايف) قبل إغلاق شمعة 5د تحت الفيواب؟ مقابل ضابطٍ = متوسّطُ النتيجة
نفسِها على حدود 5د في الرمز واليوم نفسه أُغلقت شمعتُها فوق الفيواب ⟵ فرقُ الحصّتين ببوتستراب عنقوديّ على الرمز-اليوم ⟵ «يتفوّق» · «أسوأ» · «لا يتفوّق».
🔒 لا تلغرام · لا كتابة · لا تغيير إنتاجيّ · وتخرج 9 إن تغيّرت بصمةُ العقد.
"""
import argparse
import datetime as dt
import hashlib
import json
import random
import sys

import vwap_momentum_live as V

CONTRACT = "vwap_live_judgment_prereg.md"
CONTRACT_SHA = "55e13cea29e726427b5e0f82f5bebd35c9c51e109ddbde7d06c410852e97f259"
CONTRACT_RC = 9
FROM_DAY = "2026-11-06"            # §① أوّلُ جلسةٍ بعد العقد
N_TARGET = 30                      # §① «أول 30 تنبيهًا قادمًا»
TARGET = 0.07                      # §② سلّمُ نايف «كل 7٪ - 10٪ ربح» (`nayef_verbatim`)
TAIL_MIN = 15                      # §① آخرُ ربع ساعة خارج المجتمع (تفسيرٌ مُفصَح)
CTRL_FROM_MIN = 15                 # §③ الضابط من الافتتاح ‏+15 (أوّلُ ثلاث شموع)
BOOT_N = 10000
SEED = "VWJ30"
SLOT_ENDS = (10 * 60 + 30, 12 * 60, 14 * 60)   # فتراتُ `T-VWAP-CONT` ⑦ (حتى 10:30 · حتى 12:00 · حتى 14:00 · ثمّ حتى الإغلاق − 15)


def log(m=""):
    print(m, flush=True)


def contract_ok(path=CONTRACT):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest() == CONTRACT_SHA
    except OSError:
        return False


def slot_of(e):
    """فترةُ ⑦ لنهاية شمعةٍ (دقيقةُ اليوم) ⟵ 1..4."""
    for k, end in enumerate(SLOT_ENDS, 1):
        if e <= end:
            return k
    return 4


def _key(r):
    return (r["date"], r.get("event_end_mod") or 0, r["sym"], r.get("arm") or "", r.get("n") or 0)


def population(rows, session_info, from_day=FROM_DAY):
    """§① ⟵ (المجتمع مرتّبًا، المستبعَد في آخر ربع ساعة، أوّلُ تغيّرٍ في التعريف أو None) — والمجتمعُ ما قبل التغيّر وحدَه."""
    live = sorted((r for r in rows if r.get("kind") == "alert" and r.get("sent") and r.get("mode") == "live"
                   and str(r.get("date") or "") >= from_day), key=_key)
    change = next((r for r in live if r.get("def") != "A5" or r.get("ldef") != "T"), None)
    keep, tail = [], []
    for r in live:
        if change is not None and _key(r) >= _key(change):
            break
        cl = (session_info(r["date"]) or {}).get("close_ny_min")
        (tail if cl is None or r["event_end_mod"] >= cl - TAIL_MIN else keep).append(r)
    return keep, tail, change


def reach(bars, op, cl, start, px, target=TARGET):
    """§② 1 إن بلغ أعلى دقيقةٍ في [start، نهايةِ شمعة الخروج) ‏(1+target)×px — الخروجُ أوّلُ شمعة 5د مكتملة تبدأ عند start أو بعده
    إغلاقُها تحت فيوابها (تعريفُ `harvest` بحرفه) وإلّا الإغلاق · ودقائقُ شمعة الخروج تُحسب · وإلّا 0."""
    b5, _b15, bb = V.complete_buckets(bars, op, cl, cl)
    ex = next((b for b in b5 if b["s"] >= start and b["vwap"] is not None and b["c"] < b["vwap"]), None)
    end = ex["e"] if ex is not None else cl
    lim = px * (1.0 + target)
    return int(any(b[2] >= lim for b in bb if start <= b[0] < end))


def control_points(bars, op, cl, above_only=True, slot=None):
    """§③ حدودُ 5د t في [الافتتاح+15، الإغلاق−15) ⟵ [(t، إغلاقُ الشمعة المنتهية عند t)] · above_only ⟵ أُغلقت فوق فيوابها ·
    slot ⟵ في فترة ⑦ نفسها."""
    b5, _b15, _bb = V.complete_buckets(bars, op, cl, cl)
    out = []
    for b in b5:
        t = b["e"]
        if not (op + CTRL_FROM_MIN <= t < cl - TAIL_MIN):
            continue
        if above_only and not (b["vwap"] is not None and b["c"] > b["vwap"]):
            continue
        if slot is not None and slot_of(t) != slot:
            continue
        out.append((t, b["c"]))
    return out


def control_prob(bars, op, cl, outcome, above_only=True, slot=None):
    """متوسّطُ `outcome(t، px)` على حدود الضابط ⟵ احتمالٌ تامّ بلا بذرة · أو None بلا حدٍّ مؤهَّل."""
    pts = control_points(bars, op, cl, above_only=above_only, slot=slot)
    if not pts:
        return None
    return sum(outcome(t, px) for t, px in pts) / len(pts)


def wilson(k, n, z=1.96):
    if not n:
        return None, None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return max(0.0, c - h), min(1.0, c + h)


def boot_diff(clusters, n=BOOT_N, seed=SEED):
    """clusters: {عنقود: [(نتيجة، ضابط)]} ⟵ (الفرق، الأدنى، الأعلى) — بوتستراب عنقوديّ 95% (المئينان 2.5 و97.5)."""
    keys = sorted(clusters)
    if not keys:
        return None, None, None

    def stat(ks):
        xs = [p for k in ks for p in clusters[k]]
        return sum(a for a, _c in xs) / len(xs) - sum(c for _a, c in xs) / len(xs)
    rng = random.Random(seed)
    bs = sorted(stat([rng.choice(keys) for _ in keys]) for _ in range(n))
    return stat(keys), bs[int(0.025 * n)], bs[int(0.975 * n) - 1]


def verdict(lo, hi):
    if lo is None or hi is None:
        return "لا حكم"
    return "يتفوّق على العشوائيّ" if lo > 0 else ("أسوأ من العشوائيّ" if hi < 0 else "لا يتفوّق")


def judge(alerts, bars_of, session_info):
    """المجتمعُ (30) ⟵ صفوفُ النتيجة والضوابط · `bars_of(sym, day)` ⟵ دقائقُ اليوم أو None."""
    out, cache = [], {}
    for r in alerts:
        sym, day, e, px = r["sym"], r["date"], r["event_end_mod"], r["px"]
        info = session_info(day) or {}
        op, cl = info.get("open_ny_min"), info.get("close_ny_min")
        if (sym, day) not in cache:
            cache[(sym, day)] = bars_of(sym, day)
        bars = cache[(sym, day)]
        row = {"date": day, "sym": sym, "arm": r.get("arm"), "n": r.get("n"), "e": e, "px": px, "key": r.get("key")}
        if not bars or op is None:
            row["status"] = "تعذّر"
            out.append(row)
            continue

        def oc(t, p, _b=bars, _op=op, _cl=cl):
            return reach(_b, _op, _cl, t, p)
        row.update(status="ok", hit=reach(bars, op, cl, e, px),
                   ctl=control_prob(bars, op, cl, oc), ctl_any=control_prob(bars, op, cl, oc, above_only=False),
                   ctl_slot=control_prob(bars, op, cl, oc, slot=slot_of(e)))
        out.append(row)
    return out


def summarize(rows):
    ok = [r for r in rows if r["status"] == "ok"]
    pairs = [r for r in ok if r["ctl"] is not None]
    k = sum(r["hit"] for r in ok)
    cl = {}
    for r in pairs:
        cl.setdefault((r["sym"], r["date"]), []).append((r["hit"], r["ctl"]))
    d, lo, hi = boot_diff(cl)

    def mean(xs):
        xs = [x for x in xs if x is not None]
        return (sum(xs) / len(xs)) if xs else None
    return {"n": len(ok), "hits": k, "share": (k / len(ok)) if ok else None, "wilson": wilson(k, len(ok)),
            "ctl": mean(r["ctl"] for r in pairs), "ctl_any": mean(r["ctl_any"] for r in ok), "ctl_slot": mean(r["ctl_slot"] for r in ok),
            "pairs": len(pairs), "no_ctl": len(ok) - len(pairs), "clusters": len(cl), "diff": d, "lo": lo, "hi": hi,
            "verdict": verdict(lo, hi), "failed": len(rows) - len(ok)}


def _p(x):
    return "—" if x is None else f"{x * 100:.1f}%"


def main(argv=None):
    argparse.ArgumentParser().parse_args(argv)
    if not contract_ok():
        log(f"⛔ بصمةُ العقد `{CONTRACT}` تغيّرت أو غاب — العقدُ المدموجُ لا يُعدَّل (خروج {CONTRACT_RC})")
        return CONTRACT_RC
    import os
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log("⛔ لا مفتاح Polygon — لا عمل (يُعلَن ولا يُكتَم)")
        return 2
    import market_calendar as MC
    rows = V.read_ledger()
    keep, tail, change = population(rows, MC.session_info)
    log(f"⚖️ `T-VWAP-J30` — المجتمع من {FROM_DAY}: مؤهَّلٌ {len(keep)} · آخرُ ربع ساعة (خارج) {len(tail)}"
        + (f" · تغيّرُ التعريف عند {change['date']} {change.get('event_end_ny')} (def={change.get('def')} · L={change.get('ldef')})" if change else ""))
    if len(keep) < N_TARGET:
        log(f"⏳ {len(keep)} من {N_TARGET} — لا حكم بعد" + (" · والتعريفُ تغيّر قبل الثلاثين ⟵ «لا حكم» والقرارُ للمالك" if change else ""))
        for r in keep:
            log(f"   {r['date']} {r.get('event_end_ny')} ${r['sym']} {r.get('arm')}{'#' + str(r.get('n')) if r.get('arm') == 'D' else ''} ${r.get('px')}")
        return 0
    pop = keep[:N_TARGET]
    last = pop[-1]
    now_ny = dt.datetime.now(tz=V.NY)
    cl_last = MC.session_info(last["date"])["close_ny_min"]
    if last["date"] > now_ny.date().isoformat() or (last["date"] == now_ny.date().isoformat() and now_ny.hour * 60 + now_ny.minute < cl_last + 5):
        log(f"⏳ الثلاثون اكتملت لكنّ جلسةَ الأخير ({last['date']}) لم تُغلق بعد — لا حكم قبل الإغلاق ‏+5")
        return 0
    net = V.Net(key, (os.environ.get("SEC_CONTACT") or "").strip())

    def bars_of(sym, day):
        by = net.minutes(sym, day, day)
        return None if by is None else (by.get(day) or None)
    res = judge(pop, bars_of, MC.session_info)
    s = summarize(res)
    log(f"🕐 قُرئت الدقائق {now_ny.strftime('%Y-%m-%d %H:%M')} نيويورك · نداءات Polygon {net.calls} · تعذّر {net.fails}")
    log("| # | اليوم | الرمز | ذراع | الوقت | السعر | بلغ +7% قبل الخروج | الضابط (فوق الفيواب) | الضابط (أيّ حدّ) | الضابط (الفترة) |")
    log("|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(res, 1):
        if r["status"] != "ok":
            log(f"| {i} | {r['date']} | {r['sym']} | {r['arm']} | {V._hm(r['e'])} | ${r['px']} | تعذّر | — | — | — |")
            continue
        log(f"| {i} | {r['date'][5:]} | {r['sym']} | {r['arm']}{'#' + str(r['n']) if r['arm'] == 'D' else ''} | {V._hm(r['e'])} | ${r['px']:g} | "
            f"{'✅' if r['hit'] else '—'} | {_p(r['ctl'])} | {_p(r['ctl_any'])} | {_p(r['ctl_slot'])} |")
    w = s["wilson"]
    log(f"\n📊 حصةُ التنبيهات {s['hits']} من {s['n']} = {_p(s['share'])} [{_p(w[0])}، {_p(w[1])}] · الضابطُ الحاكم {_p(s['ctl'])} "
        f"(على {s['pairs']} · بلا حدٍّ مؤهَّل {s['no_ctl']}) · الحرفيّ {_p(s['ctl_any'])} · المطابِقُ في الفترة {_p(s['ctl_slot'])}")
    f = lambda v: "—" if v is None else f"{v * 100:+.1f} نقطة"           # noqa: E731
    log(f"⚖️ الفرق {f(s['diff'])} · فاصل 95% (بوتستراب عنقوديّ على {s['clusters']} رمز-يوم) [{f(s['lo'])}، {f(s['hi'])}] ⟵ **{s['verdict']}**")
    log("   حدُّ القوّة: بثلاثين تنبيهًا فرقٌ أصغرُ من ‏≈15 نقطةً لا يُكشف · و«لا يتفوّق» لا تعني «يساوي».")
    log("VWJ30_JSON " + json.dumps({"summary": s, "rows": res, "tail": len(tail), "read_ny": now_ny.isoformat()}, ensure_ascii=False, default=str))
    return 4 if s["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
