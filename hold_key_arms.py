#!/usr/bin/env python3
"""🕰️🥇 `T-HOLD-KEY` — «الأطولُ حفظًا أوّلًا» عند الكثافة الحيّة وبمفاتيحَ محياة.

العقد `hold_key_prereg.md` **مدفوعٌ قبل أيّ سطرٍ هنا**، وملحقُه §⑨ (سبعةُ
إقرارات) **قبل أيّ رقم**. 🔒 **قراءةٌ فقط · صفرُ مسٍّ بالإنتاج · لا
`LOGIC_VERSION`** — والمقياسُ **واحدٌ لا اثنان**: كلُّ ما يُعاد استعمالُه
يُستورَد **بالاسم** من `press_rank_arms` (المجمَّدة بأرقامها المنشورة) ومن
`press_radar`/`rebound_arms`/`Super_stock` الإنتاجية.
"""
import json
import os
import random
import statistics
import sys
import time

import press_rank_arms as PRA          # r_of · boot_ci · ready_rows · deliver · order_a0/a2/a3 · pv0_gate

# ─────────────────────────────── ثوابتُ العقد ───────────────────────────────
ARM_NAMES = ("B0", "B1", "B2", "B3")
PV0_WINNERS = {"2023": 351, "2024": 333, "2025": 341}      # §⑥ HV1 (فوق المحسومة)
HV0_NET = {"2023": 0.3102, "2024": 0.7353, "2025": 1.9946}  # §⑥ HV0 جسرُ الأمس
HV0_TOL = 5e-5                        # تسامحُ تقريبِ الطباعة (4 خانات)
LIVE_MED_MIN, LIVE_MED_MAX = 8.0, 40.0                     # §⑥ HV4 الكثافةُ الحيّة
Q5_STRIDE = 5                         # §⑨-7 — نفسُ خطوة `prev_qualified`
PQ_MAX_BACK = 120                     # §⑨-7 — نفسُ `max_back` الإنتاجيّ
HV8_SAMPLE = 150                      # §⑨-7 عيّنةُ مطابقةِ البديل
HV8_MIN_AGREE = 90.0                  # §⑨-7 حدُّ التوافق
HV8_SEED = 20260827
BUDGET_SEC = 240 * 60                 # §⑨-3 سقفٌ دون سقف الـworkflow (300د)
PROBE_SYMS = 40                       # §⑨-3 عيّنةُ قياس الكلفة


def _log(m):
    print(m, flush=True)


# ─────────────────────── §⑨-7 شبكةُ التأهّل العامّة `Q5` ───────────────────────

def q5_grid(sym, df, lo_pos, hi_pos):
    """أيامُ التأهّل المُعايَنة لرمزٍ واحد — `analyze_ticker` **بالاسم**.

    تُعايَن كلُّ `Q5_STRIDE` جلسة (نفسُ خطوة `press_radar.prev_qualified`)،
    وتُرجع قائمةَ `(موضعُ الشمعة، تاريخُها)` مرتَّبةً تصاعديًّا.
    ⚖️ فرزًا **أو** ارتدادًا — تعريفُ `prev_qualified` حرفيًّا."""
    import Super_stock as S                                     # noqa: PLC0415
    out = []
    days = [str(d)[:10] for d in df.index]
    for i in range(max(lo_pos, 0), min(hi_pos, len(df))):
        if (i % Q5_STRIDE) != 0:
            continue
        sl = df.iloc[:i + 1]
        try:
            ok = bool(S.analyze_ticker(sym, sl)) or \
                bool(S.analyze_ticker(sym, sl, pullback=True))
        except Exception:                                       # noqa: BLE001
            continue
        if ok:
            out.append((i, days[i]))
    return out


def mover_days(df):
    """أيامُ «متحرّكٍ حديث» — قفزةُ اليوم الواحد بعتبة `EXPLOSION_PCT` **بالاسم**.

    §⑨-1: تُستعمل العتبةُ لا `scan_explosions` (ماسحُ «اليوم» ويستدعي
    `analyze_ticker` للتصنيف الذي لا نحتاجه)."""
    import Super_stock as S                                     # noqa: PLC0415
    thr = float(S.CONFIG["EXPLOSION_PCT"])
    try:
        c = df["Close"].values.astype(float)
    except Exception:                                           # noqa: BLE001
        return []
    days = [str(d)[:10] for d in df.index]
    return [days[k] for k in range(1, len(c))
            if c[k - 1] > 0 and (c[k] / c[k - 1] - 1.0) * 100.0 >= thr]


def _within(d_from, d_to, max_days):
    """هل `d_from` داخل `max_days` يومًا تقويميًّا قبل `d_to`؟ (‏`_days_between` بالاسم)."""
    import press_radar as PR                                    # noqa: PLC0415
    g = PR._days_between(d_from, d_to)
    return g is not None and 0 <= g <= max_days


# ───────────────────────── الإحياءُ وبناءُ البِركة الحيّة ─────────────────────────

def enrich(rows, grids, movers, pos_of):
    """§⑨-7: يشتقّ من `Q5` كمّيتين — `prev_q` (المفتاح) و`live_q` (عضويّةُ البِركة).

    `prev_q` = تأهّلٌ داخل `PQ_MAX_BACK` شمعةً قبل المِرساة (وبفجوةٍ 3 كالإنتاج).
    `live_q` = تأهّلٌ داخل `MEMORY_DAYS` يومًا تقويميًّا."""
    import press_radar as PR                                    # noqa: PLC0415
    for r in rows:
        sym, s = r["symbol"], r["session"]
        g = grids.get(sym) or []
        p = (pos_of.get(sym) or {}).get(s)
        hit = None
        if p is not None:
            for gp, gd in reversed(g):                 # الأحدثُ أوّلًا
                if gp <= p - 3 and gp >= p - PQ_MAX_BACK:
                    hit = gd
                    break
        r["prev_q"] = bool(hit)
        r["pq_date"] = hit
        r["live_q"] = bool(hit and _within(hit, s, PR.MEMORY_DAYS))
        r["live_mv"] = any(_within(d, s, PR.MEMORY_DAYS)
                           for d in (movers.get(sym) or []))
    return rows


def live_pool(rows):
    """§③: الصفوفُ المقصورةُ على البِركة المُعادِ بناؤها (ترشيحٌ حيّ **أو** متحرّك).

    ⚖️ سقفُ `POOL_CAP` يُطبَّق على المؤهَّلين في الجلسة ويُعلَن إن بنّد."""
    import press_radar as PR                                    # noqa: PLC0415
    by, cut = {}, 0
    for r in rows:
        if r.get("live_q") or r.get("live_mv"):
            by.setdefault(r["session"], []).append(r)
    out = []
    for s in sorted(by):
        xs = sorted(by[s], key=lambda r: (0 if r.get("live_q") else 1, r["symbol"]))
        if len(xs) > PR.POOL_CAP:
            cut += len(xs) - PR.POOL_CAP
        out.extend(xs[:PR.POOL_CAP])
    return out, cut


# ──────────────────────────────── الأذرعُ الأربع ────────────────────────────────

def order_b0(rows):
    """**`B0` المرجع** — `press_radar.alert_rank` **بالاسم** و`prev_q` **محيًى**.
    ⚖️ §⑨-4: بلا تجزئةِ المستيقظين هنا — `deliver_prod` وحدَها تطبّقها."""
    import press_radar as PR                                    # noqa: PLC0415
    return sorted(rows, key=PR.alert_rank)


def order_b1(rows):
    """**`B1` الحاكمة** — `hold_sessions` تنازليًّا **مفتاحًا أوّلَ** ثم ترتيبُ
    `B0` حرفيًّا (فرزٌ مستقرّ ⇒ مفاتيحُ الإنتاج تبقى فاصلَ تعادل)."""
    return sorted(order_b0(rows),
                  key=lambda r: -int((r.get("read") or {}).get("hold_sessions") or 0))


def order_b2(rows, rng):
    """**`B2`** شاهدُ الصدفة."""
    xs = list(rows)
    rng.shuffle(xs)
    return xs


def order_b3(rows):
    """**`B3`** حفظٌ صرف (‏= `A3` القديمة): الرمزُ فاصلُ تعادلٍ حتميّ."""
    return PRA.order_a3(rows)


def deliver_prod(by_sess, sessions, order_fn, rw):
    """§⑨-4 قاعدةُ عددِ كروت الإنتاج حرفيًّا (`press_radar.py:604,618,622`):
    يُرتَّب الجاهزون، ثم **إن وُجد مستيقظون فهم الكروتُ حصرًا بلا إكمالٍ من
    الهادئين**، وإلّا فأوائلُ الجاهزين. ودِدوبٌ لكلّ ذراعٍ على حدة (§⑨-3 القديم)."""
    import press_radar as PR                                    # noqa: PLC0415
    mem, per_sess, cards = {}, {}, []
    n_bind = 0
    for s in sessions:
        pool = by_sess.get(s, [])
        cand = [r for r in pool if PR.should_alert(mem.get(r["symbol"], {}), s)]
        xs = order_fn(cand)
        fire = [r for r in xs if (r.get("wake") or {}).get("awake")]
        base = fire if fire else xs
        if len(base) > PR.ALERT_CAP:
            n_bind += 1
        picked = base[:PR.ALERT_CAP]
        tot = 0.0
        for r in picked:
            mem[r["symbol"]] = {"last_alert": s}
            tot += PRA.r_of(r["oc"], rw)
            cards.append({"s": s, "sym": r["symbol"], "oc": r["oc"]})
        per_sess[s] = tot
    return {"per_sess": per_sess, "cards": cards, "bind": n_bind}


def run_arms(rows, rw, tag):
    """يشغّل الأذرعَ الأربع على مجتمعٍ واحدٍ بقاعدةِ عددِ كروت الإنتاج."""
    by_sess, sessions = {}, []
    for r in rows:
        by_sess.setdefault(r["session"], []).append(r)
    sessions = sorted(by_sess)
    res = {"B0": deliver_prod(by_sess, sessions, order_b0, rw),
           "B1": deliver_prod(by_sess, sessions, order_b1, rw),
           "B3": deliver_prod(by_sess, sessions, order_b3, rw)}
    nets = []
    for k in range(PRA.N_SEEDS):
        rng = random.Random(1000 + k)
        d = deliver_prod(by_sess, sessions, lambda xs, _r=rng: order_b2(xs, _r), rw)
        nets.append(sum(d["per_sess"].values()) / max(1, len(sessions)))
    nets.sort()
    res["_a2"] = {"med": statistics.median(nets),
                  "p95": nets[min(len(nets) - 1, int(round(0.95 * (len(nets) - 1))))]}
    res["_sessions"] = sessions
    res["_tag"] = tag
    return res


# ──────────────────────────── بوّاباتُ الصلاحية ────────────────────────────

def hv0_bridge(rows_full, rw, year):
    """**`HV0` جسرُ الأمس** (‏§⑨-6): بصفوفٍ `prev_q=None` وبقاعدةِ عددِ كروت
    الأمس (`PRA.deliver` تُكمل إلى السقف) و`PRA.order_a0` — يجب أن يُعيد
    صافيَ `A0` المنشورَ في `press_rank_result §①`."""
    by, _ = {}, None
    for r in rows_full:
        by.setdefault(r["session"], []).append(dict(r, prev_q=None, plan=None))
    sess = sorted(by)
    d = PRA.deliver(by, sess, PRA.order_a0, rw)
    net = sum(d["per_sess"].values()) / max(1, len(sess))
    exp = HV0_NET.get(str(year))
    ok = exp is not None and abs(net - exp) <= HV0_TOL
    return ok, net, exp


def hv8_agree(rows, hist, grids, pos_of):
    """**`HV8`** (‏§⑨-7): توافقُ `prev_q` المشتقِّ من `Q5` مع
    `press_radar.prev_qualified` **الحقيقيّة** على عيّنةٍ عشوائيّةٍ حتميّة."""
    import press_radar as PR                                     # noqa: PLC0415
    rng = random.Random(HV8_SEED)
    idx = list(range(len(rows)))
    rng.shuffle(idx)
    agree = n = 0
    for j in idx[:HV8_SAMPLE]:
        r = rows[j]
        df = hist.get(r["symbol"])
        if df is None:
            continue
        try:
            truth = PR.prev_qualified(r["symbol"], df, r["session"])
        except Exception:                                        # noqa: BLE001
            continue
        n += 1
        agree += int(bool(truth) == bool(r.get("prev_q")))
    return (100.0 * agree / n if n else 0.0), n


def budget_probe(hist, syms, lo_hi):
    """**`HV3`** (‏§⑨-3): تُقاس كلفةُ شبكة `Q5` على عيّنةٍ **حقيقيّة** ثم تُسقَط."""
    t0 = time.perf_counter()
    done = 0
    for sym in syms[:PROBE_SYMS]:
        df = hist.get(sym)
        if df is None:
            continue
        lo, hi = lo_hi(df)
        q5_grid(sym, df, lo, hi)
        done += 1
    if not done:
        return None, 0.0
    per = (time.perf_counter() - t0) / done
    return per, per * len(syms)


# ──────────────────────────────── التقرير ────────────────────────────────

def _arm_line(name, res, rw):
    sess = res["_sessions"]
    d = res[name]
    dec = [c for c in d["cards"] if c["oc"] in ("win", "loss")]
    win = sum(1 for c in dec if c["oc"] == "win")
    net = sum(d["per_sess"].values()) / max(1, len(sess))
    hit = 100.0 * win / max(1, len(dec))
    return (f"   │ {name}: {net:+.4f} · كروت {len(d['cards'])} · محسومة "
            f"{len(dec)} · بلغ الهدف {hit:.2f}% · بنّد السقف {d['bind']} جلسة"), net


def report(rows_full, rows_live, cut, n_syms, n_seen, year, hv8, pq_share) -> int:
    import press_backtest as PB                                  # noqa: PLC0415
    import press_radar as PR                                     # noqa: PLC0415
    rw = PB.r_win_value()
    _log(f"\n{'—' * 74}\n📊 T-HOLD-KEY سنة {year} — رموزٌ مفحوصة {n_syms} · "
         f"جاهزٌ (كون) {len(rows_full)} · جاهزٌ (بِركة) {len(rows_live)} · "
         f"R_win={rw:.2f}")

    cov = 100.0 * n_syms / max(n_seen, 1)
    _log(f"   🩺 `HV7` التغطية {cov:.1f}% ({n_syms} من {n_seen}) · "
         f"مفقودٌ {n_seen - n_syms}")
    if cov < PRA.COVERAGE_MIN:
        _log(f"   ⛔ `HV7` دون {PRA.COVERAGE_MIN}% ⇒ خروج 3.")
        return 3
    if not rows_full or not rows_live:
        _log("   ⛔ صفرُ صفٍّ (بصمةُ الـ`no-op`) ⇒ خروج 4.")
        return 4

    ok0, net0, exp0 = hv0_bridge(rows_full, rw, year)
    _log(f"   {'✅' if ok0 else '⛔'} `HV0` جسرُ الأمس: A0={net0:+.4f} "
         f"(المنشور {exp0})")
    if not ok0:
        _log("   ⛔ `HV0` تفرّقٌ عن `press_rank_result §①` ⇒ عطبُ أداة (خروج 3).")
        return 3

    _log(f"   {'✅' if hv8[0] >= HV8_MIN_AGREE else '⛔'} `HV8` توافقُ شبكة `Q5` "
         f"مع `prev_qualified` = {hv8[0]:.1f}% (ن={hv8[1]})")
    if hv8[0] < HV8_MIN_AGREE:
        _log(f"   ⛔ `HV8` دون {HV8_MIN_AGREE}% ⇒ البديلُ لم يُثبت (خروج 3).")
        return 3

    _log(f"   📐 `HV2` نصيبُ `prev_q` الصادق = {pq_share:.1f}%")
    if not (0.0 < pq_share < 100.0):
        _log("   ⛔ `HV2` الإحياءُ منحلّ (‏0% أو 100%) ⇒ خروج 4.")
        return 4

    by = {}
    for r in rows_live:
        by.setdefault(r["session"], []).append(r)
    sess = sorted(by)
    if len(sess) < PRA.FLOOR_SESSIONS:
        _log(f"   ⛔ الأرضية: الجلسات {len(sess)} دون {PRA.FLOOR_SESSIONS} "
             "⇒ لا حكم (خروج 4).")
        return 4
    per_n = [len(by[s]) for s in sess]
    med = statistics.median(per_n)
    _log(f"   📐 `HV4` وسيطُ الجاهزين/جلسة في `D_live` = {med:.1f} "
         f"(المدى {min(per_n)}-{max(per_n)}) · قُصّ بالسقف {cut}")
    if not (LIVE_MED_MIN <= med <= LIVE_MED_MAX):
        _log(f"   ⛔ `HV4` خارج [{LIVE_MED_MIN},{LIVE_MED_MAX}] ⇒ ليست كثافةً "
             "حيّة (خروج 4).")
        return 4

    res = run_arms(rows_live, rw, "D_live")
    set0 = {(c["s"], c["sym"]) for c in res["B0"]["cards"]}
    set1 = {(c["s"], c["sym"]) for c in res["B1"]["cards"]}
    only1 = len(set1 - set0)
    _log(f"   📐 `HV5` كروتٌ تُسلّمها `B1` ولا تُسلّمها `B0`: {only1}")
    if only1 == 0:
        _log("   ⛔ `HV5` `B1` لم تتفرّق عن `B0` ⇒ `no-op` (خروج 4).")
        return 4

    bad = {k: PRA.dedupe_violations(res[k]["cards"]) for k in ("B0", "B1", "B3")}
    _log("   📐 `HV6` خرقُ الدِدوب: " + " · ".join(f"{k}={v}" for k, v in bad.items()))
    if any(bad.values()):
        _log("   ⛔ `HV6` الدِدوبُ غيرُ نافذ ⇒ خروج 3.")
        return 3

    _log("   ┌─ الأذرع على `D_live` (الحاكم: صافي R المُسلَّم لكلّ جلسة) ──────")
    nets = {}
    for name in ("B0", "B1", "B3"):
        line, net = _arm_line(name, res, rw)
        _log(line)
        nets[name] = net
    a2 = res["_a2"]
    _log(f"   │ B2 العشوائيّ: وسيط {a2['med']:+.4f} · مئين 95 {a2['p95']:+.4f} "
         f"(‏{PRA.N_SEEDS} بذرة)")
    _log("   └───────────────────────────────────────────────────────────")

    n_cards0 = len(res["B0"]["cards"])
    if n_cards0 < PRA.FLOOR_CARDS:
        _log(f"   ⛔ الأرضية: كروتُ `B0` {n_cards0} دون {PRA.FLOOR_CARDS} "
             "⇒ لا حكم (خروج 4).")
        return 4

    d1 = [res["B1"]["per_sess"][s] - res["B0"]["per_sess"][s] for s in sess]
    d3 = [res["B3"]["per_sess"][s] - res["B0"]["per_sess"][s] for s in sess]
    ci1, ci3 = PRA.boot_ci(d1), PRA.boot_ci(d3)                  # §⑨-5
    _log(f"   📐 B1−B0 = {nets['B1'] - nets['B0']:+.4f} "
         f"[{ci1['lo']:+.4f},{ci1['hi']:+.4f}] · B3−B0 = "
         f"{nets['B3'] - nets['B0']:+.4f} [{ci3['lo']:+.4f},{ci3['hi']:+.4f}] · "
         f"B1 فوق مئين95؟ {'نعم' if nets['B1'] > a2['p95'] else 'لا'}")

    # 📎 المجتمعُ الكامل يُنشَر للمقارنة ولا يحكم (§⑤)
    rf = run_arms(rows_full, rw, "D_full")
    _log("   ┌─ للمقارنة فقط · `D_full` (لا يحكم) ─────────────────────────")
    for name in ("B0", "B1", "B3"):
        _log(_arm_line(name, rf, rw)[0])
    _log(f"   │ B2 العشوائيّ: وسيط {rf['_a2']['med']:+.4f} · مئين 95 "
         f"{rf['_a2']['p95']:+.4f}")
    _log("   └───────────────────────────────────────────────────────────")

    _log("DIFFS " + json.dumps({"year": year,
                                "d1": [round(x, 6) for x in d1],
                                "d3": [round(x, 6) for x in d3]},
                               ensure_ascii=False))
    _log("HOLDK " + json.dumps(
        {"year": year, "sessions": len(sess), "ready_full": len(rows_full),
         "ready_live": len(rows_live), "median_live": med, "pool_cut": cut,
         "bind": res["B0"]["bind"], "pq_share": round(pq_share, 1),
         "hv8": round(hv8[0], 1), "r_win": round(rw, 4), "only1": only1,
         "a2_med": round(a2["med"], 4), "a2_p95": round(a2["p95"], 4),
         "live": {k: round(nets[k], 4) for k in nets},
         "full": {k: round(sum(rf[k]["per_sess"].values()) /
                           max(1, len(rf["_sessions"])), 4)
                  for k in ("B0", "B1", "B3")},
         "ci1": {"lo": round(ci1["lo"], 4), "hi": round(ci1["hi"], 4)},
         "ci3": {"lo": round(ci3["lo"], 4), "hi": round(ci3["hi"], 4)}},
        ensure_ascii=False))
    return 0


def main() -> int:
    import Super_stock as S                                      # noqa: PLC0415
    import press_radar as PR                                     # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    path = os.environ.get("BT_FROZEN_PATH") or "frozen_backtest.pkl.gz"
    _log(f"\n{'=' * 78}\n🕰️🥇 T-HOLD-KEY — سنة {year}\n{'=' * 78}")
    if not os.path.exists(path):
        _log(f"⛔ اللقطة المجمَّدة مفقودة ({path!r}) ⇒ خروج 2.")
        return 2
    hist, _sp, asof = S.load_frozen_dataset(path)
    _log(f"📦 لقطة as-of {asof} · رموز {len(hist)}")
    yr = year if year and year != "?" else None

    ok, dec, k = PRA.pv0_gate(hist, yr)
    exp_w = PV0_WINNERS.get(str(year))
    ok = ok and (exp_w is None or k == exp_w)
    _log(f"   {'✅' if ok else '⛔'} `HV1` HOLD3 محسومة={dec} · فائزة={k} "
         f"(المنشور {PRA.PV0_RESOLVED.get(str(year), '؟')} · {exp_w})")
    if not ok:
        _log("   ⛔ `HV1` تفرّقٌ عن أرقام §⑬ المنشورة ⇒ عطبُ أداة (خروج 3).")
        return 3

    def lo_hi(df):
        """نطاقُ الشبكة: من قبل السنة بـ`PQ_MAX_BACK` شمعةً إلى آخرها."""
        days = [str(d)[:10] for d in df.index]
        ys = [i for i, d in enumerate(days) if not yr or d[:4] == str(yr)]
        if not ys:
            return 0, 0
        return max(RB.MIN_BARS, ys[0] - PQ_MAX_BACK - 5), min(len(df), ys[-1] + 1)

    syms = [s for s, d in hist.items()
            if d is not None and len(d) >= RB.MIN_BARS + 5]
    per, proj = budget_probe(hist, syms, lo_hi)
    _log(f"   📐 `HV3` كلفةُ شبكة `Q5`: {(per or 0)*1000:.0f}ms للرمز ⇒ "
         f"الإسقاط {proj/60:.1f} دقيقة لـ{len(syms)} رمزًا "
         f"(السقف {BUDGET_SEC/60:.0f})")
    if per is None or proj > BUDGET_SEC:
        _log("   ⛔ `HV3` الإسقاطُ يتجاوز الميزانية ⇒ يقف قبل حرق التشغيلة "
             "(خروج 6).")
        return 6

    grids, movers, pos_of, rows, n_syms, n_seen = {}, {}, {}, [], 0, 0
    for sym, df in hist.items():
        n_seen += 1
        if df is None or len(df) < RB.MIN_BARS + 5:
            continue
        n_syms += 1
        lo, hi = lo_hi(df)
        grids[sym] = q5_grid(sym, df, lo, hi)
        movers[sym] = mover_days(df)
        pos_of[sym] = {str(d)[:10]: i for i, d in enumerate(df.index)}
        rows.extend(PRA.ready_rows(sym, df, yr))
        if n_syms % 500 == 0:
            _log(f"  … مشى {n_syms} رمزًا · صفوفٌ جاهزة {len(rows)}")

    enrich(rows, grids, movers, pos_of)
    pq_share = 100.0 * sum(1 for r in rows if r.get("prev_q")) / max(1, len(rows))
    hv8 = hv8_agree(rows, hist, grids, pos_of)
    rows_live, cut = live_pool(rows)
    _log(f"   📡 البِركةُ المُعادُ بناؤها: ترشيحٌ حيّ "
         f"{sum(1 for r in rows if r.get('live_q'))} · متحرّك "
         f"{sum(1 for r in rows if r.get('live_mv'))} · "
         f"`MEMORY_DAYS`={PR.MEMORY_DAYS} · `POOL_CAP`={PR.POOL_CAP}")
    return report(rows, rows_live, cut, n_syms, n_seen, year, hv8, pq_share)


if __name__ == "__main__":
    sys.exit(main())
