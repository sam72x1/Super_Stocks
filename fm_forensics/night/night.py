"""🌙 `T-NIGHT` المرحلة 2 — أداةُ القياس على العقد `T_NIGHT_prereg.md` (قراءةٌ فقط · بلا تلغرام · لا تكتب في المستودع).

`--mode discover` ⟵ جزءُ الاكتشاف وحدَه (حتى 2026-09-30) وترشيحُ ذراعٍ واحدة أو «لا مرشَّح».
`--mode confirm`  ⟵ جزءُ التأكيد (من 2026-10-01) للذراع المثبَّتة في `data/night_freeze.json` — مرّةً واحدة.
الخروج: 0 تمّ · 5 تغطيةٌ دون الحدّ · 7 النتيجةُ صدرت · 8 المحورُ مُغلَق · 9 لا تثبيت · 11 العقدُ تغيّر.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import queue
import random
import subprocess
import sys
import threading
import zoneinfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
NY = zoneinfo.ZoneInfo("America/New_York")

PREREG = os.path.join(HERE, "T_NIGHT_prereg.md")
PREREG_SHA16 = "04c371ca4ad25da0"
FREEZE = os.path.join(HERE, "data", "night_freeze.json")
RESULT = os.path.join(HERE, "T_NIGHT_RESULT.md")
FIRST_DAY = "2026-08-18"
SPLIT_LAST_DISCOVER = "2026-09-30"
COST_PCT = 1.8
NIGHT_USD_MIN = 10_000.0
BUCKETS = (("B2_5", 0.02, 0.05), ("B5_10", 0.05, 0.10), ("B10_20", 0.10, 0.20))
POOLED = ("P2_20", 0.02, 0.20)
ARMS = BUCKETS + (POOLED,)
MIN_ARM, MIN_CTL = 30, 20
BOOT_N, BOOT_SEED = 2000, 20261119
COVER_MAX_FAIL = 0.20
SEEN_DAYS = 7
BARS_N, INTERVAL = 5000, "15"
CLOSED_RC = 8
CLOSED = False           # يُقلب True عند الإقفال المُنفَّذ (والفتحُ إقرارُ المالك `NIGHT_REOPEN == "1"`)


def prereg_sha16(path=PREREG):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def ny(ts):
    return dt.datetime.fromtimestamp(int(ts), tz=dt.timezone.utc).astimezone(NY)


def _mins(t):
    return t.hour * 60 + t.minute


def night_bounds(day):
    """الليلةُ `N(D)`: [20:00 من اليوم التقويميّ السابق، 04:00 من D) نيويورك ⟵ (بداية، نهاية) بثواني يونكس."""
    d = dt.date.fromisoformat(day)
    a = dt.datetime.combine(d - dt.timedelta(days=1), dt.time(20, 0), tzinfo=NY)
    b = dt.datetime.combine(d, dt.time(4, 0), tzinfo=NY)
    return int(a.timestamp()), int(b.timestamp())


def by_day(bars):
    """شموعٌ ممتدّة ⟵ {يوم نيويورك: [(دقيقةُ اليوم, o, h, l, c, v)]} مرتّبةً."""
    out = {}
    for ts, o, h, lo, c, v in bars or []:
        t = ny(ts)
        out.setdefault(t.date().isoformat(), []).append((_mins(t), o, h, lo, c, v))
    return out


def unit_row(sym, day, prev, prev2, ext_days, boats_bars):
    """وحدةُ (رمز · D) على تعريفات العقد §③ ⟵ صفٌّ أو {"skip": السبب}. `ext_days` = `by_day` للسلسلة الممتدّة."""
    pb = ext_days.get(prev) or []
    if not pb:
        return {"skip": "بلا مرجع"}
    ref = pb[-1][4]
    if not ref or ref <= 0:
        return {"skip": "بلا مرجع"}
    a, b = night_bounds(day)
    nb = [x for x in boats_bars or [] if a <= x[0] < b]
    night_last = nb[-1][4] if nb else None
    night_usd = sum(x[4] * (x[5] or 0) for x in nb)
    r_night = (night_last / ref - 1) if night_last else None
    db = ext_days.get(day) or []
    pre = [x for x in db if 240 <= x[0] < 570]
    reg = [x for x in db if 570 <= x[0] < 960]
    if not pre:
        return {"skip": "لا دخول"}
    if not reg:
        return {"skip": "لا خروج"}
    entry, exit_ = pre[0][1], reg[-1][4]
    if not entry or entry <= 0:
        return {"skip": "لا دخول"}
    hi = max(x[2] for x in pre + reg)
    p2 = [x for x in (ext_days.get(prev2) or []) if 570 <= x[0] < 960]
    r_mom = (ref / p2[-1][4] - 1) if p2 and p2[-1][4] > 0 else None
    return {"sym": sym, "day": day, "ref": ref, "r_night": r_night, "night_usd": night_usd, "night_bars": len(nb),
            "r_mom": r_mom, "entry": entry, "exit": exit_, "net": (exit_ / entry - 1) * 100 - COST_PCT,
            "touch_ref": hi >= ref * 1.30, "touch_entry": hi >= entry * 1.30}


def is_z(r):
    return r["r_night"] is None or r["r_night"] < 0.02


def in_arm(r, lo, hi):
    return r["r_night"] is not None and lo <= r["r_night"] < hi and r["night_usd"] >= NIGHT_USD_MIN


def in_ctl(r, lo, hi):
    return is_z(r) and r["r_mom"] is not None and lo <= r["r_mom"] < hi


def label(r):
    """وسمُ العرض: الشريحة · B20P · THIN (رفعةٌ بدولارٍ دون الأرضيّة) · Z."""
    if is_z(r):
        return "Z"
    if r["night_usd"] < NIGHT_USD_MIN:
        return "THIN"
    for name, lo, hi in BUCKETS:
        if lo <= r["r_night"] < hi:
            return name
    return "B20P"


def _mean(xs):
    return sum(xs) / len(xs) if xs else None


def _median(xs):
    s = sorted(xs)
    n = len(s)
    return None if not n else (s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2)


def describe(rows):
    nets = [r["net"] for r in rows]
    return {"n": len(rows), "mean": _mean(nets), "median": _median(nets),
            "win_pct": (100 * sum(1 for x in nets if x > 0) / len(nets)) if nets else None,
            "touch_ref_pct": (100 * sum(1 for r in rows if r["touch_ref"]) / len(rows)) if rows else None,
            "touch_entry_pct": (100 * sum(1 for r in rows if r["touch_entry"]) / len(rows)) if rows else None,
            "days": len({r["day"] for r in rows}),
            "worst": [(r["sym"], r["day"], round(r["net"], 1)) for r in sorted(rows, key=lambda r: r["net"])[:5]]}


def boot(arm, ctl, n=BOOT_N, seed=BOOT_SEED):
    """بوتستراب عنقوديّ بالجلسة ⟵ فاصلا 95% لمتوسّط الذراع وللفرق (الذراع − الضابط). None حين تفرغ إحداهما."""
    if not arm or not ctl:
        return None
    days = sorted({r["day"] for r in arm} | {r["day"] for r in ctl})
    ad, cd = {}, {}
    for r in arm:
        ad.setdefault(r["day"], []).append(r["net"])
    for r in ctl:
        cd.setdefault(r["day"], []).append(r["net"])
    rng = random.Random(seed)
    ms, ds = [], []
    for _ in range(n):
        pick = [days[rng.randrange(len(days))] for _ in days]
        a = [x for d in pick for x in ad.get(d, ())]
        c = [x for d in pick for x in cd.get(d, ())]
        if not a or not c:
            continue
        ma = sum(a) / len(a)
        ms.append(ma)
        ds.append(ma - sum(c) / len(c))
    if len(ms) < n * 0.5:
        return None
    ms.sort()
    ds.sort()
    q = lambda s, p: s[min(len(s) - 1, max(0, int(p * len(s))))]          # noqa: E731
    return {"mean_ci": (q(ms, 0.025), q(ms, 0.975)), "diff_ci": (q(ds, 0.025), q(ds, 0.975)), "reps": len(ms)}


def discover_pick(rows):
    """قاعدةُ §⑤: المتأهّلةُ الأعلى متوسّطَ صافٍ أو None. يُرجع (الاسم|None، جدولُ المرشّحات)."""
    table, best = {}, None
    for name, lo, hi in ARMS:
        a = [r for r in rows if in_arm(r, lo, hi)]
        c = [r for r in rows if in_ctl(r, lo, hi)]
        ma, mc = _mean([r["net"] for r in a]), _mean([r["net"] for r in c])
        ok = len(a) >= MIN_ARM and len(c) >= MIN_CTL and ma is not None and mc is not None and ma > 0 and ma > mc
        table[name] = {"arm": describe(a), "ctl": describe(c), "qualifies": ok}
        if ok and (best is None or ma > table[best]["arm"]["mean"]):
            best = name
    return best, table


def confirm_verdict(rows, arm_name):
    """حكمُ §⑥ للذراع المثبَّتة: «تعبر» · «لا تعبر» · «لا قياس»."""
    lo, hi = next((lo, hi) for n, lo, hi in ARMS if n == arm_name)
    a = [r for r in rows if in_arm(r, lo, hi)]
    c = [r for r in rows if in_ctl(r, lo, hi)]
    out = {"arm": describe(a), "ctl": describe(c), "boot": None}
    if len(a) < MIN_ARM or len(c) < MIN_CTL:
        out["verdict"] = "لا قياس"
        return out
    b = boot(a, c)
    out["boot"] = b
    out["verdict"] = "تعبر" if b and b["mean_ci"][0] > 0 and b["diff_ci"][0] > 0 else "لا تعبر"
    return out


# ───────────────────────── الجلب والكون (شبكة · git) ─────────────────────────
def sessions(first, last):
    import market_calendar as MC
    d, out = dt.date.fromisoformat(first), []
    end = dt.date.fromisoformat(last)
    while d <= end:
        if MC.is_trading_day(d.isoformat()):
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def last_complete_day(now=None):
    import market_calendar as MC
    t = (now or dt.datetime.now(dt.timezone.utc)).astimezone(NY)
    d = t.date()
    if _mins(t) < 16 * 60 + 30:
        d -= dt.timedelta(days=1)
    while not MC.is_trading_day(d.isoformat()):
        d -= dt.timedelta(days=1)
    return d.isoformat()


def universe_at(prev_day, day):
    """رموزُ `near_watch.json` في آخر commit قبل 20:00 نيويورك من `prev_day` التي شوهدت خلال `SEEN_DAYS` قبل `day`."""
    cut = dt.datetime.combine(dt.date.fromisoformat(prev_day), dt.time(20, 0), tzinfo=NY)
    c = subprocess.run(["git", "rev-list", "-1", f"--before={int(cut.timestamp())}", "HEAD", "--", "near_watch.json"],
                       cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if not c:
        return []
    raw = subprocess.run(["git", "show", f"{c}:near_watch.json"], cwd=ROOT, capture_output=True, text=True).stdout
    try:
        nw = json.loads(raw)
    except ValueError:
        return []
    lim = (dt.date.fromisoformat(day) - dt.timedelta(days=SEEN_DAYS)).isoformat()
    return sorted(s for s, e in nw.items() if isinstance(e, dict) and str(e.get("last_seen") or "") >= lim)


def fetch_all(symbols, workers=8):
    """{رمز: (ext, ext_status, boats, boats_status)} — `symbol_error` = غيرُ مُدرَج (ليس تعذّرًا)."""
    import night_probe as P
    q, out, lock = queue.Queue(), {}, threading.Lock()
    for s in symbols:
        q.put(s)

    def one(full, ses):
        for _ in range(2):
            bars, st, _info = P.tv_bars(full, ses, n=BARS_N, interval=INTERVAL)
            if bars is not None or st.startswith("symbol_error"):
                return bars, st
        return bars, st

    def work():
        while True:
            try:
                s = q.get_nowait()
            except queue.Empty:
                return
            e, es = one(f"NASDAQ:{s}", "extended")
            b, bs = one(f"BOATS:{s}", "regular")
            with lock:
                out[s] = (e, es, b, bs)
                if len(out) % 100 == 0:
                    print(f"   … جُلب {len(out)} من {len(symbols)}", flush=True)

    ts = [threading.Thread(target=work, daemon=True) for _ in range(workers)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return out


def depth_short(bars, need_ts):
    return bool(bars) and len(bars) >= BARS_N and bars[0][0] > need_ts


def build_rows(days_all, part_days, uni, data):
    rows, skips, units, fetch_fail = [], {}, 0, 0
    idx = {d: i for i, d in enumerate(days_all)}
    cache = {}
    for day in part_days:
        i = idx[day]
        if i < 2:
            continue
        prev, prev2 = days_all[i - 1], days_all[i - 2]
        for s in uni.get(day, ()):
            units += 1
            e, es, b, bs = data.get(s, (None, "missing", None, "missing"))
            if e is None or (b is None and not bs.startswith("symbol_error")):
                if es.startswith("symbol_error"):
                    skips["رمزٌ غيرُ مُدرَج"] = skips.get("رمزٌ غيرُ مُدرَج", 0) + 1
                else:
                    fetch_fail += 1
                continue
            need = int(dt.datetime.combine(dt.date.fromisoformat(prev2), dt.time(4, 0), tzinfo=NY).timestamp())
            if depth_short(e, need) or depth_short(b, night_bounds(day)[0]):
                skips["عمق"] = skips.get("عمق", 0) + 1
                continue
            if s not in cache:
                cache[s] = by_day(e)
            r = unit_row(s, day, prev, prev2, cache[s], b)
            if "skip" in r:
                skips[r["skip"]] = skips.get(r["skip"], 0) + 1
            else:
                rows.append(r)
    return rows, skips, units, fetch_fail


def fmt(d):
    if not d or not d.get("n"):
        return "n=0"
    return (f"n={d['n']} · أيّام {d['days']} · متوسّط {d['mean']:+.2f}% · وسيط {d['median']:+.2f}% · رابح {d['win_pct']:.1f}% · "
            f"لمس +30% من المرجع {d['touch_ref_pct']:.1f}% · من الدخول {d['touch_entry_pct']:.1f}%")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("discover", "confirm"), required=True)
    ap.add_argument("--out", default="night_out.json")
    a = ap.parse_args(argv)
    if CLOSED and os.environ.get("NIGHT_REOPEN", "") != "1":
        print("🔒 محورُ T-NIGHT مُغلَقٌ مُنفَّذًا — الفتحُ إقرارُ المالك")
        return CLOSED_RC
    if prereg_sha16() != PREREG_SHA16:
        print("⛔ العقدُ تغيّر عن بصمته المثبَّتة")
        return 11
    frozen = None
    if a.mode == "confirm":
        if os.path.exists(RESULT):
            print("⛔ النتيجةُ صدرت — التأكيدُ مرّةً واحدة")
            return 7
        try:
            with open(FREEZE, encoding="utf-8") as f:
                frozen = json.load(f)
        except (OSError, ValueError):
            frozen = None
        if not frozen or frozen.get("prereg_sha16") != PREREG_SHA16 or frozen.get("arm") not in [n for n, _, _ in ARMS]:
            print("⛔ لا ملفَّ تثبيتٍ ببصمة العقد")
            return 9
    last = last_complete_day()
    days_all = sessions("2026-08-10", last)
    days = [d for d in days_all if d >= FIRST_DAY]
    part = [d for d in days if (d <= SPLIT_LAST_DISCOVER) == (a.mode == "discover")]
    idx = {d: i for i, d in enumerate(days_all)}
    uni = {d: universe_at(days_all[idx[d] - 1], d) for d in part}
    syms = sorted({s for v in uni.values() for s in v})
    print(f"🌙 T-NIGHT {a.mode}: جلسات {len(part)} ({part[0]} … {part[-1]}) · رموز {len(syms)} · وحدات {sum(len(v) for v in uni.values())}", flush=True)
    data = fetch_all(syms)
    rows, skips, units, fetch_fail = build_rows(days_all, part, uni, data)
    rep = {"mode": a.mode, "prereg_sha16": PREREG_SHA16, "days": [part[0], part[-1], len(part)], "symbols": len(syms), "units": units,
           "rows": len(rows), "skips": skips, "fetch_fail": fetch_fail,
           "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    print(f"   وحدات {units} · صفوف {len(rows)} · تعذّر جلب {fetch_fail} · مستبعَد {skips}")
    if units and fetch_fail / units > COVER_MAX_FAIL:
        print("⛔ تغطيةُ الجلب دون الحدّ ⟵ «لا قياس»")
        rep["verdict"] = "لا قياس (تغطية)"
        json.dump(rep, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return 5
    labs = {}
    for r in rows:
        labs.setdefault(label(r), []).append(r)
    rep["labels"] = {k: describe(v) for k, v in sorted(labs.items())}
    print("── وصف (كلُّ الوسوم):")
    for k, v in rep["labels"].items():
        print(f"   {k}: {fmt(v)}")
    if a.mode == "discover":
        best, table = discover_pick(rows)
        rep["candidates"], rep["pick"] = table, best
        print("── المرشّحات (§⑤):")
        for k, v in table.items():
            print(f"   {k}: الذراع {fmt(v['arm'])}\n        الضابط {fmt(v['ctl'])} ⟵ {'متأهّلة' if v['qualifies'] else 'غيرُ متأهّلة'}")
        print(f"⚖️ الاكتشاف: {'المرشَّح ' + best if best else '«لا مرشَّح» ⟵ يُقفل المحور'}")
    else:
        v = confirm_verdict(rows, frozen["arm"])
        rep["confirm"], rep["arm"] = v, frozen["arm"]
        print(f"── التأكيد للذراع {frozen['arm']}:\n   الذراع {fmt(v['arm'])}\n   الضابط {fmt(v['ctl'])}")
        if v["boot"]:
            print(f"   فاصلُ متوسّط الذراع [{v['boot']['mean_ci'][0]:+.2f}، {v['boot']['mean_ci'][1]:+.2f}] · "
                  f"فاصلُ الفرق [{v['boot']['diff_ci'][0]:+.2f}، {v['boot']['diff_ci'][1]:+.2f}]")
        print(f"   أسوأ 5: {v['arm']['worst']}")
        print(f"⚖️ الحكم: «{v['verdict']}»")
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
