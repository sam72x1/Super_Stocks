#!/usr/bin/env python3
"""🎯🌘 `T-LIVE-VS-SHADOW` — «اللحظيّ الموجود مقابل الظلّ» (العقد `fm_forensics/live_vs_shadow/LVS_prereg.md` · مدموجٌ قبل أيّ رقم) — قراءةٌ فقط.

`--mode run` (الرنر · Polygon · تاريخُ git كامل): الراكضون المجمَّدون (`runners_60.json`) والمراسي المجمَّدة (`gcross_runner_universe.json` ‏`alerts`) ⟵
① الظلُّ 09:25 من لقطة `op_entry_state.json`/`tier_fwd_ledger.jsonl` عند آخر التزامٍ قبل 09:25 نيويورك (`shadow_telegram.premarket_anchors`/`shadow_rows`
بالاسم) ⟵ ② «هنا الدخول» (أبكرُ مِرساةٍ مُرسَلة) دقيقتُها ونسبتُها وما بقي من الحركة ⟵ ③ الفئات بالأسماء ⟵ ④ الكلفة على الكون `L ∪ N` ⟵ ⑤ ذراع J1 ⟵
التنبّؤات L1-L8 · ويطبع markdown النتيجة و`LVS_JSON`.
🔒 لا تلغرام · لا كتابة في المستودع · لا تغيير في أيّ أداة · وتخرج 9 إن تغيّرت بصمةُ العقد.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CONTRACT = os.path.join(HERE, "LVS_prereg.md")
CONTRACT_SHA = "2c048188ca0841f205d05f3f2b343a0b43f636f701fd5809bb848f39072b600b"
CONTRACT_RC = 9
UNIVERSE = os.path.join(ROOT, "fm_forensics", "ema_cross", "data", "gcross_runner_universe.json")
RUNNERS = os.path.join(ROOT, "fm_forensics", "rrgate", "data", "runners_60.json")
LEDGER_REF = "86bc3838b5c0ee692a919ca346e667fdce475d92"     # §④ سجلُّ التصنيف المجمَّد (main وقتَ العقد)
STATE_FILE, TIER_FILE = "op_entry_state.json", "tier_fwd_ledger.jsonl"
NY = ZoneInfo("America/New_York")
GAP = ("2026-09-29", "2026-10-12")                          # = `gcross_runner.GAP` (فجوةُ المصدر · مقفولٌ بالهُويّة)
OP_NY, SHADOW_NY, END_NY = 4 * 60, 9 * 60 + 25, 20 * 60      # §② نافذةُ R [04:00، 20:00) · رسالةُ الظلّ 09:25
REG_FROM, REG_TO = 9 * 60 + 30, 16 * 60                       # §④ وصفًا: الجلسةُ النظاميّة
RUN50, RUN100 = 0.5, 1.0
R_TOL, AGREE_MIN = 0.02, 0.90                                 # §② بوّابةُ صدق الشموع
FLOOR_RUN, FLOOR_ARM, FAIL_MAX = 30, 20, 0.10                 # §⑤ · §④
J1_FROM = "2026-08-24"                                        # §④ أوّلُ صفوف السجلّ
NAMED = (("OMH", "2026-11-04"), ("CHSN", "2026-11-03"))       # ③ بسطرٍ صريح
CATS = ("كلاهما", "هنا الدخول فقط", "الظلّ فقط", "لا أحد")


def log(m=""):
    print(m, flush=True)


def contract_ok(path=CONTRACT):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest() == CONTRACT_SHA
    except OSError:
        return False


# ── دوالُّ نقيّة (مقفولةٌ في السويّة) ─────────────────────────────────────────────────────────────────────
def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, c - h), min(1.0, c + h))


def median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def ny_parts(t_ms):
    t = dt.datetime.fromtimestamp(int(t_ms) / 1000, dt.timezone.utc).astimezone(NY)
    return t.date().isoformat(), t.hour * 60 + t.minute


def ny_ts(day, minute):
    d = dt.date.fromisoformat(day)
    return dt.datetime(d.year, d.month, d.day, minute // 60, minute % 60, tzinfo=NY).timestamp()


def source_days(U, gap=GAP):
    """§① أيّامُ المصدر: جلساتٌ فيها مِرساةٌ مجمَّدة واحدةٌ على الأقلّ خارج فجوة المصدر."""
    return [d for d in U.get("sessions") or [] if (U.get("alerts") or {}).get(d) and not (gap[0] <= d <= gap[1])]


def universe_of(U, d):
    v = (U.get("days") or {}).get(d) or {}
    return set(v.get("L") or {}) | set(v.get("N") or ())


def day_seq(bars, day):
    """شموعُ `fetch_day` ⟵ [(دقيقة نيويورك، o، h، l، c)] ليوم `day` داخل [04:00، 20:00)."""
    out = []
    for b in bars or ():
        d, m = ny_parts(b[0])
        if d == day and OP_NY <= m < END_NY:
            out.append((m, b[1], b[2], b[3], b[4]))
    return out


def prev_close(dailies, day):
    """§② `P0` = آخرُ إغلاقٍ قبل اليوم من `daily_range` ⟵ (تاريخُه، الإغلاق) أو (None، None)."""
    raw = sorted((d, c) for (d, _h, c) in (dailies or []) if d < day and c)
    return raw[-1] if raw else (None, None)


def day_R(seq, p0):
    """(R، دقيقةُ القمّة، H) — أعلى `high` في النافذة ÷ P0 − 1."""
    if not seq or not p0:
        return None, None, None
    top = max(seq, key=lambda b: b[2])
    return top[2] / p0 - 1.0, top[0], top[2]


def price_before(seq, minute):
    """إغلاقُ آخر شمعةٍ تبدأ قبل `minute` (سعرُ 09:25 كما في `T-SHADOW-CONT`)."""
    pre = [b for b in seq if b[0] < minute]
    return pre[-1][4] if pre else None


def after_stats(seq, m_from, px, p0):
    """§② من سعرٍ `px` عند دقيقة `m_from` ⟵ {left: ما بقي من الحركة · gain: المكسبُ المتاح · pct: النسبةُ من إغلاق الأمس}."""
    if not seq or not px or not p0:
        return None
    H = max(b[2] for b in seq)
    aft = [b[2] for b in seq if b[0] >= m_from]
    h_aft = max(aft) if aft else None
    left = None if (H <= p0 or h_aft is None) else max(0.0, h_aft - px) / (H - p0)
    gain = None if h_aft is None else h_aft / px - 1.0
    return {"left": left, "gain": gain, "pct": px / p0 - 1.0}


def commit_before(commits, ts):
    """آخرُ التزامٍ وقتُ مُلتزِمه عند `ts` أو قبله ⟵ hash أو None · commits = [(ct، h)] تصاعديّة."""
    best = None
    for ct, h in commits:
        if ct <= ts:
            best = h
        else:
            break
    return best


def j1_map(lines):
    """§④ ⟵ ({(يوم، رمز): أبكرُ صفٍّ بـj1 = true بـprice_ms} · مجموعةُ (يوم، رمز) لها صفٌّ أيًّا كان)."""
    out, has = {}, set()
    for ln in lines:
        try:
            r = json.loads(ln)
        except (ValueError, TypeError):
            continue
        if not isinstance(r, dict):
            continue
        k = (str(r.get("date") or ""), str(r.get("symbol") or "").upper())
        has.add(k)
        if r.get("j1") is True and r.get("price_ms"):
            if k not in out or int(r["price_ms"]) < int(out[k]["price_ms"]):
                out[k] = r
    return out, has


def anchors_at(state, day, SH=None):
    """§② مراسي البري التي كانت ستراها رسالةُ 09:25: `shadow_telegram.premarket_anchors` بالاسم ثمّ ما وقع قبل 09:25 وحدَه."""
    if SH is None:
        import shadow_telegram as SH
    return [(s, a) for s, a in SH.premarket_anchors(state, day) if ny_parts(a["anchor_ms"])[1] < SHADOW_NY]


def anchors_at_full(state, day, SH=None):
    """🔧 `CORRECTION_PROTOCOL.md §①` (وصفًا): مراسي `anchors_at` **ومعها** المِرساةُ الخارجة قبل 09:25 (`rearm_prev` من يومها · بلا مِرساةٍ فوقه)."""
    import tierlink_probe as TLP
    out = list(anchors_at(state, day, SH))
    have = {s for s, _a in out}
    for k, v in (state or {}).items():
        if not str(k).startswith("LIQ:") or not isinstance(v, dict) or str(v.get("date") or "") != day:
            continue
        sym = str(k)[4:]
        a = TLP.exited_anchor(v, day)
        if sym in have or not a or ny_parts(a["anchor_ms"])[1] >= SHADOW_NY:
            continue
        out.append((sym, a))
    return sorted(out, key=lambda kv: int(kv[1]["anchor_ms"]))


def rebuild_alerts(U, full):
    """🔧 `CORRECTION_PROTOCOL.md §①`: أبكرُ مِرساةٍ لكلّ (يوم، رمز) في جلسات `U` من تاريخ git — `anchor_history` ثمّ `first_anchor` بالاسم بالمفتاح المُعطى."""
    import tierlink_probe as TLP
    import gcross_runner as GR
    g0 = GR.ANCHOR_HIST_FULL
    try:
        GR.ANCHOR_HIST_FULL = bool(full)
        days, out = set(U.get("sessions") or []), {}
        for (d, sym), v in TLP.anchor_history(GR.SINCE_ALERTS, full=bool(full)).items():
            if d in days:
                fa = GR.first_anchor(v, d)
                if fa:
                    out.setdefault(d, {})[sym] = {"ms": fa[0], "px": fa[1]}
        return out
    finally:
        GR.ANCHOR_HIST_FULL = g0


def fill_px(alerts, bars_fn):
    """🔧 المِرساةُ بلا سعر ⟵ إغلاقُ شمعة دقيقة المِرساة (`anchor_price` = `c` شمعتها في `liq_stage_events`) · ويُرجع (مُلئ، تعذّر)."""
    ok = miss = 0
    for d, m in alerts.items():
        for sym, a in m.items():
            if a.get("px") is not None:
                continue
            row = next((b for b in (bars_fn(sym, d) or []) if int(b[0]) == int(a["ms"])), None)
            if row is not None:
                a["px"] = float(row[4])
                ok += 1
            else:
                miss += 1
    return ok, miss


def category(in_s, fire_min):
    """③ ⟵ (الفئة، الفرعيّة)."""
    if in_s and fire_min is not None:
        return "كلاهما", ""
    if in_s:
        return "الظلّ فقط", ""
    if fire_min is not None:
        return "هنا الدخول فقط", ("قبل 09:25 ولم يدخل S" if fire_min < SHADOW_NY else "بعد 09:25")
    return "لا أحد", ""


def r_class(R):
    if R is None:
        return None
    return "run100" if R >= RUN100 else ("mid" if R >= RUN50 else "false")


def precision_verdict(k_arm, n_arm, k_all, n_all, floor=FLOOR_ARM):
    """§④ «انتقائيّة» = فاصلُ دقّة الذراع فوق فاصل الكلّ لا يتداخل · وإلّا «غيرُ انتقائيّة» · وراكضون باقون دون الأرضيّة «لا قياس»."""
    if k_arm < floor or not n_arm or not n_all:
        return "لا قياس"
    a, b = wilson(k_arm, n_arm), wilson(k_all, n_all)
    return "انتقائيّة" if a[0] > b[1] else "غيرُ انتقائيّة"


def runner_row(r, src, S_d, alert, j1row, seq, dailies):
    """③ لراكضٍ واحد (نقيّ على المُدخلات) ⟵ dict · `why` يقول لماذا لا يُقاس إن لم يُقس."""
    out = {"sym": r["sym"], "day": r["day"], "R": r["R"], "why": None}
    if r["day"] not in src:
        out["why"] = "المصدرُ غائب"
        return out
    if not seq:
        out["why"] = "شموعٌ متعذّرة"
        return out
    _pd, p0 = prev_close(dailies, r["day"])
    R_re, top_m, _H = day_R(seq, p0)
    if R_re is None:
        out["why"] = "إغلاقُ الأمس متعذّر"
        return out
    out.update({"R_re": R_re, "agree": abs(R_re - r["R"]) <= R_TOL, "top_m": top_m, "P0": p0})
    in_s = r["sym"] in (S_d or set())
    fm = None
    if alert:
        _d, fm = ny_parts(alert["ms"])
        out["fire"] = {"m": fm, **(after_stats(seq, fm, alert["px"], p0) or {})}
    if in_s:
        E = price_before(seq, SHADOW_NY)
        out["shadow"] = {"m": SHADOW_NY, **(after_stats(seq, SHADOW_NY, E, p0) or {})} if E else {"m": SHADOW_NY}
    if j1row:
        _d, am = ny_parts(j1row["price_ms"])
        px = j1row.get("e5") or j1row.get("anchor_price")
        out["arm"] = {"m": am, **(after_stats(seq, am, px, p0) or {})}
    out["in_s"] = in_s
    out["cat"], out["sub"] = category(in_s, fm)
    return out


def summarize(rows, cost, shadow_cost, arm_scope_days, n_shadow_days):
    """⟵ dict النتيجة (نقيّ على الصفوف)."""
    res = {"n": len(rows)}
    meas = [x for x in rows if x["why"] is None]
    res["why"] = {}
    for x in rows:
        if x["why"]:
            res["why"][x["why"]] = res["why"].get(x["why"], 0) + 1
    res["measured"] = len(meas)
    in_src = [x for x in rows if x["why"] != "المصدرُ غائب"]
    res["bars_fail"] = sum(1 for x in in_src if x["why"] == "شموعٌ متعذّرة")
    res["bars_ok"] = (not in_src) or res["bars_fail"] / len(in_src) <= FAIL_MAX
    res["agree"] = [sum(1 for x in meas if x.get("agree")), len(meas)]
    res["agree_ok"] = bool(meas) and res["agree"][0] / len(meas) >= AGREE_MIN
    res["floor_ok"] = len(meas) >= FLOOR_RUN
    res["cats"] = {c: sorted((x["sym"], x["day"], x["R"], x.get("sub", "")) for x in meas if x["cat"] == c) for c in CATS}
    fired = [x for x in meas if x.get("fire")]
    res["fired"] = [len(fired), len(meas)]
    res["shadow"] = [sum(1 for x in meas if x.get("in_s")), len(meas)]
    res["fire_min_med"] = median([x["fire"]["m"] for x in fired])
    res["fire_pct_med"] = median([x["fire"].get("pct") for x in fired])
    res["fire_left_med"] = median([x["fire"].get("left") for x in fired])
    res["fire_gain_med"] = median([x["fire"].get("gain") for x in fired])
    sh = [x for x in meas if x.get("in_s") and x.get("shadow", {}).get("pct") is not None]
    res["sh_pct_med"] = median([x["shadow"]["pct"] for x in sh])
    res["sh_left_med"] = median([x["shadow"].get("left") for x in sh])
    res["sh_gain_med"] = median([x["shadow"].get("gain") for x in sh])
    # ④ الكلفة
    c_all = [c for c in cost if c["cls"]]
    nf = sum(1 for c in c_all if c["cls"] == "false")
    nr = sum(1 for c in c_all if c["cls"] == "run100")
    nm = sum(1 for c in c_all if c["cls"] == "mid")
    days = sorted({c["day"] for c in cost})
    per_day = [sum(1 for c in c_all if c["day"] == d) for d in days]
    per_day_f = [sum(1 for c in c_all if c["day"] == d and c["cls"] == "false") for d in days]
    res["cost"] = {"fires": len(c_all), "false": nf, "run100": nr, "mid": nm, "days": len(days), "per_day_med": median(per_day),
                   "false_day_med": median(per_day_f), "false_per_run": (nf / nr) if nr else None,
                   "false_per_run50": (nf / (nr + nm)) if (nr + nm) else None, "prec": [nr, len(c_all)], "prec_ci": wilson(nr, len(c_all)),
                   "split": sum(1 for c in cost if c.get("split")), "nobars": sum(1 for c in cost if c["cls"] is None and not c.get("split"))}
    s_all = [c for c in shadow_cost if c["cls"]]
    sf = sum(1 for c in s_all if c["cls"] == "false")
    sr = sum(1 for c in s_all if c["cls"] == "run100")
    res["shadow_cost"] = {"names": len(s_all), "false": sf, "run100": sr, "mid": sum(1 for c in s_all if c["cls"] == "mid"),
                          "false_per_run": (sf / sr) if sr else None, "prec": [sr, len(s_all)], "prec_ci": wilson(sr, len(s_all)),
                          "days": n_shadow_days}
    # ⑤ الذراع
    sc = [c for c in c_all if c["day"] in arm_scope_days]
    kept = [c for c in sc if c.get("j1")]
    f_all = sum(1 for c in sc if c["cls"] == "false")
    r_all = sum(1 for c in sc if c["cls"] == "run100")
    f_k = sum(1 for c in kept if c["cls"] == "false")
    r_k = sum(1 for c in kept if c["cls"] == "run100")
    arm_runners = [x for x in fired if x["day"] in arm_scope_days]
    arm_kept_r = [x for x in arm_runners if x.get("arm")]
    res["arm"] = {"scope_fires": len(sc), "kept": len(kept), "false_all": f_all, "false_kept": f_k, "run_all": r_all, "run_kept": r_k,
                  "cut_false": (1 - f_k / f_all) if f_all else None, "cut_run": (1 - r_k / r_all) if r_all else None,
                  "prec_all": [r_all, len(sc)], "prec_all_ci": wilson(r_all, len(sc)), "prec_kept": [r_k, len(kept)],
                  "prec_kept_ci": wilson(r_k, len(kept)), "verdict": precision_verdict(r_k, len(kept), r_all, len(sc)),
                  "no_row": sum(1 for c in sc if not c.get("has_row")),
                  "kept_reg": sum(1 for c in kept if c.get("j1_m") is not None and REG_FROM <= c["j1_m"] < REG_TO),
                  "runners_scope": len(arm_runners), "runners_kept": len(arm_kept_r),
                  "arm_min_med": median([x["arm"]["m"] for x in arm_kept_r]),
                  "arm_pct_med": median([x["arm"].get("pct") for x in arm_kept_r]),
                  "arm_left_med": median([x["arm"].get("left") for x in arm_kept_r]),
                  "fire_left_med_scope": median([x["fire"].get("left") for x in arm_runners]),
                  "fire_pct_med_scope": median([x["fire"].get("pct") for x in arm_runners])}
    return res


def predictions(res):
    def share(p):
        return (p[0] / p[1]) if p and p[1] else None
    f, s = share(res["fired"]), share(res["shadow"])
    so = len(res["cats"]["الظلّ فقط"]) / res["measured"] if res["measured"] else None
    c, a = res["cost"], res["arm"]

    def within(x, lo, hi):
        return None if x is None else (lo <= x <= hi)
    return {"L1": within(f, 0.60, 0.85), "L2": within(s, 0.20, 0.40), "L3": None if so is None else so <= 0.02,
            "L4": within(res["fire_pct_med"], 0.20, 0.60), "L5": within(res["fire_left_med"], 0.30, 0.70),
            "L6": within(c["false_per_run"], 2.0, 8.0),
            "L7": None if (a["cut_false"] is None or a["cut_run"] is None) else (a["cut_false"] >= 0.70 and a["cut_run"] >= 0.40),
            "L8": None if res["shadow_cost"]["false_per_run"] is None else res["shadow_cost"]["false_per_run"] <= 1.0}


# ── العرض ───────────────────────────────────────────────────────────────────────────────────────────
def _p(x, sign=True):
    return "—" if x is None else (f"{x * 100:+.1f}%" if sign else f"{x * 100:.1f}%")


def _hm(m):
    return "—" if m is None else f"{int(m) // 60:02d}:{int(m) % 60:02d}"


def _sh(p, ci=None):
    if not p or not p[1]:
        return "—"
    s = f"{p[0]} من {p[1]} = {p[0] / p[1] * 100:.1f}%"
    if ci:
        s += f" [{ci[0] * 100:.1f}، {ci[1] * 100:.1f}]"
    return s


def report_lines(res, named, preds, meta):
    L = ["# 🎯🌘 `T-LIVE-VS-SHADOW` — النتيجة (مولَّدةٌ بـ`live_vs_shadow.py --mode run` · لا رقمَ باليد)", ""]
    L.append(f"**التشغيلة:** {meta.get('run') or '—'} · main `{meta.get('sha', '')[:9]}` · أيّامُ المصدر {meta['src_days']} من {meta['sessions']} · "
             f"لقطاتُ 09:25 المقروءة {meta['snap_days']}")
    L.append("")
    L.append(f"**المجتمع (+100%):** {res['n']} · مقيس {res['measured']} · لا يُقاس: "
             + (" · ".join(f"{k} {v}" for k, v in sorted(res["why"].items())) or "0"))
    L.append(f"**بوّابةُ صدق الشموع:** R المُعاد يطابق المجمَّد (±{R_TOL * 100:.0f} نقطة) في {res['agree'][0]} من {res['agree'][1]} ⟵ "
             + ("تُعتمد" if res["agree_ok"] else "**لا قياس لـ②-④**") + f" · شموعٌ متعذّرة {res['bars_fail']}"
             + ("" if res["bars_ok"] else " ⟵ **فوق 10%: لا قياس**"))
    ok = res["agree_ok"] and res["bars_ok"] and res["floor_ok"]
    if not res["floor_ok"]:
        L.append(f"⛔ مقيسون {res['measured']} دون الأرضيّة {FLOOR_RUN} ⟵ «لا قياس»")
    L += ["", "## ① ② الظلُّ 09:25 و«هنا الدخول» على راكضي +100% المقيسين", ""]
    L.append("| | التقط/أُطلق | الدقيقة (الوسيط) | من إغلاق الأمس (الوسيط) | ما بقي من الحركة (الوسيط) | المكسبُ المتاح بعده (الوسيط) |")
    L.append("|---|---|---|---|---|---|")
    L.append(f"| الظلّ 09:25 | {_sh(res['shadow'])} | 09:25 | {_p(res['sh_pct_med'])} | {_p(res['sh_left_med'], False)} | {_p(res['sh_gain_med'])} |")
    L.append(f"| «هنا الدخول» | {_sh(res['fired'])} | {_hm(res['fire_min_med'])} | {_p(res['fire_pct_med'])} | {_p(res['fire_left_med'], False)} | "
             f"{_p(res['fire_gain_med'])} |")
    L += ["", "## ③ الفئات (بالأسماء)", ""]
    for c in CATS:
        xs = res["cats"][c]
        L.append(f"**{c} — {len(xs)}**")
        if c == "هنا الدخول فقط" and xs:
            subs = {}
            for x in xs:
                subs[x[3]] = subs.get(x[3], 0) + 1
            L.append("وصفًا: " + " · ".join(f"{k} {v}" for k, v in sorted(subs.items())))
        if xs:
            L.append(" · ".join(f"{s} {d[5:]} ({R * 100:+.0f}%)" for s, d, R, _sub in xs))
        L.append("")
    L.append("**OMH وCHSN:**")
    for ln in named:
        L.append(f"- {ln}")
    c = res["cost"]
    L += ["", "## ④ الكلفة — إطلاقاتُ «هنا الدخول» على الكون L ∪ N", ""]
    L.append(f"- الإطلاقات {c['fires']} في {c['days']} يومًا (الوسيطُ اليوميّ {c['per_day_med']}) · يومُ تقسيمٍ مستبعَد {c['split']} · بلا شموع {c['nobars']}")
    L.append(f"- **كاذب (R دون 50%) {c['false']}** (الوسيطُ اليوميّ {c['false_day_med']}) · بين 50% و100% {c['mid']} · **راكضٌ +100% {c['run100']}**")
    fpr = "—" if c["false_per_run"] is None else format(c["false_per_run"], ".1f")
    fpr50 = "—" if c["false_per_run50"] is None else format(c["false_per_run50"], ".1f")
    L.append(f"- **كاذبٌ لكلّ راكضٍ +100%: {fpr}** · ولكلّ راكضٍ +50%: {fpr50} · دقّةُ الإطلاق (+100%) {_sh(c['prec'], c['prec_ci'])}")
    s = res["shadow_cost"]
    L.append(f"- وصفًا — **الظلّ 09:25** على الكون نفسِه: أسماء {s['names']} في {s['days']} يومًا · كاذب {s['false']} · بين 50% و100% {s['mid']} · راكضٌ +100% "
             f"{s['run100']} · كاذبٌ لكلّ راكض {('—' if s['false_per_run'] is None else format(s['false_per_run'], '.1f'))} · دقّتُه {_sh(s['prec'], s['prec_ci'])}")
    a = res["arm"]
    L += ["", f"## ⑤ الذراع J1 (من {J1_FROM})", ""]
    L.append(f"- الإطلاقاتُ في النطاق {a['scope_fires']} ⟵ تبقى مع J1 {a['kept']} (منها في الجلسة النظاميّة {a['kept_reg']}) · بلا صفٍّ في السجلّ {a['no_row']}")
    L.append(f"- **تقصّ من الكاذب {a['false_all'] - a['false_kept']} من {a['false_all']} ({_p(a['cut_false'], False)})** · **ومن راكضي +100% "
             f"{a['run_all'] - a['run_kept']} من {a['run_all']} ({_p(a['cut_run'], False)})**")
    L.append(f"- الدقّة: الكلّ {_sh(a['prec_all'], a['prec_all_ci'])} · مع J1 {_sh(a['prec_kept'], a['prec_kept_ci'])} ⟵ **{a['verdict']}**")
    L.append(f"- الراكضون الباقون (راكضو ①-③ في النطاق {a['runners_scope']} ⟵ مع J1 {a['runners_kept']}): الدقيقة {_hm(a['arm_min_med'])} · من إغلاق الأمس "
             f"{_p(a['arm_pct_med'])} · ما بقي {_p(a['arm_left_med'], False)} (بلا الذراع في النطاق: {_p(a['fire_pct_med_scope'])} · ما بقي "
             f"{_p(a['fire_left_med_scope'], False)})")
    L += ["", "## ⑥ التنبّؤات (منشورةٌ قبل الرقم)", ""]
    for k, v in preds.items():
        L.append(f"- `{k}` " + ("✅" if v else ("❌" if v is False else "— لا قياس")))
    L += ["", ("⚠️ **أجزاءٌ «لا قياس» أعلاه بالأرضيّات** — " if not ok else "")
          + "🔒 لا تغييرَ في أيّ أداة · «هنا الدخول» = مِرساةُ العامل المُرسَلة (K1) · والظلُّ مُعادٌ بقواعد اليوم على لقطاتٍ ماضية · وأيُّ شرطٍ عقدٌ آخر وقرارُ المالك."]
    return L


# ── الرنر ───────────────────────────────────────────────────────────────────────────────────────────
def _git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout


def _commits(path):
    out = []
    for ln in _git("log", "--format=%H %ct", "--", path).splitlines():
        try:
            h, ct = ln.split()
            out.append((int(ct), h))
        except ValueError:
            continue
    return sorted(out)


def _show(h, path):
    return subprocess.run(["git", "show", f"{h}:{path}"], cwd=ROOT, capture_output=True, text=True).stdout


def mode_run(alerts_mode="frozen"):
    from concurrent.futures import ThreadPoolExecutor
    import shadow_telegram as SH
    from shadow_ready import split_fn, split_ratio
    from tier_fwd_report import fetch_day, load_ledger
    from tierlink_probe import daily_range
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log("⛔ بلا مفتاح Polygon — لا قياس")
        return 3
    U = json.load(open(UNIVERSE, encoding="utf-8"))
    RN = json.load(open(RUNNERS, encoding="utf-8"))
    corr = alerts_mode == "full"
    if corr:
        old = rebuild_alerts(U, False)
        n_fz = sum(len(v) for v in (U.get("alerts") or {}).values())
        if old != (U.get("alerts") or {}):
            log(f"⛔ بوّابةُ الصدق: الإعادةُ بالمفتاح المُطفأ لا تطابق المراسي المجمَّدة ({sum(len(v) for v in old.values())} مقابل {n_fz}) — لا قياس")
            return 7
        full = rebuild_alerts(U, True)
        n_fu = sum(len(v) for v in full.values())
        log(f"🔧 التصحيح: المراسي المجمَّدة {n_fz} = الإعادةُ المُطفأة بت-بت ✅ · المصحَّحة {n_fu} (‏+{n_fu - n_fz}) · بلا سعر "
            f"{sum(1 for v in full.values() for a in v.values() if a.get('px') is None)} · بصمةٌ "
            f"{hashlib.sha256(json.dumps(full, sort_keys=True).encode()).hexdigest()[:16]}")
        U = dict(U, alerts=full)
    run100 = [r for r in RN["rows"] if r["R"] >= RUN100]
    src = source_days(U)
    j1m, has_row = j1_map(_show(LEDGER_REF, TIER_FILE).splitlines())
    arm_days = {d for d in src if d >= J1_FROM}
    log(f"📅 الجلسات {len(U['sessions'])} · أيّامُ المصدر {len(src)} ({src[0]} ⟵ {src[-1]}) · راكضو +100% {len(run100)} · صفوفُ J1 {len(j1m)}")
    bars_c, dly_c = {}, {}

    def bars(sym, d):
        k = (sym, d)
        if k not in bars_c:
            bars_c[k] = fetch_day(sym, d, key)
        return bars_c[k]

    def dly(sym, d):
        k = (sym, d)
        if k not in dly_c:
            dly_c[k] = daily_range(sym, d, key)
        return dly_c[k]
    # ① لقطاتُ 09:25 (القراءةُ من git أوّلًا · ثمّ جلبٌ متوازٍ لكلّ ما يلزم)
    commits = _commits(STATE_FILE)
    snaps, snap_days, anchors_n = {}, 0, 0
    for d in src:
        h = commit_before(commits, ny_ts(d, SHADOW_NY))
        if not h:
            continue
        try:
            state = json.loads(_show(h, STATE_FILE) or "{}")
        except ValueError:
            state = {}
        tmp = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
        tmp.write(_show(h, TIER_FILE))
        tmp.close()
        try:
            led = {(r["date"], r["symbol"]): r for r in load_ledger(tmp.name)}
        finally:
            os.unlink(tmp.name)
        anchors = anchors_at(state, d, SH)
        anchors_n += len(anchors)
        snaps[d] = (anchors, led)
        snap_days += 1
    need = {(r["sym"], r["day"]) for r in RN["rows"] if r["day"] in src}
    for d in src:
        for sym in (U["alerts"].get(d) or {}):
            if sym in universe_of(U, d):
                need.add((sym, d))
        for sym, _a in (snaps.get(d) or ((), None))[0]:
            need.add((sym, d))
    for s_, d_ in NAMED:
        need.add((s_, d_))
    with ThreadPoolExecutor(8) as pool:
        list(pool.map(lambda k: (bars(*k), dly(*k)), sorted(need)))
    log(f"📡 رموزٌ-أيّام مجلوبة {len(need)} · بلا شموع {sum(1 for k in need if not bars_c.get(k))}")
    if corr:
        _f_ok, _f_miss = fill_px(U["alerts"], bars)
        log(f"🔧 سعرُ المِرساة بلا سعر من شمعتها: مُلئ {_f_ok} · تعذّر {_f_miss}")
    S_by = {}
    for d in src:
        if d not in snaps:
            S_by[d] = set()
            continue
        anchors, led = snaps[d]
        srows, _allr, _sk = SH.shadow_rows(anchors, lambda s_, _d=d: dly(s_, _d), d, lambda s_, _d=d: bars(s_, _d), led,
                                           lambda s_, _d=d: split_fn(s_, _d, key))
        S_by[d] = {x["sym"] for x in srows}
    log(f"🌘 لقطاتُ 09:25: {snap_days} يومًا · مراسي البري قبل 09:25 {anchors_n} · أسماءُ S {sum(len(v) for v in S_by.values())}")
    rows = []
    for r in run100:
        d = r["day"]
        rows.append(runner_row(r, set(src), S_by.get(d), (U["alerts"].get(d) or {}).get(r["sym"]),
                               j1m.get((d, r["sym"])) if d in arm_days else None, day_seq(bars(r["sym"], d), d) if d in src else None,
                               dly(r["sym"], d) if d in src else None))
    # ④ الكلفة
    split_c = {}

    def classify(sym, d):
        seq = day_seq(bars(sym, d), d)
        pd_, p0 = prev_close(dly(sym, d), d)
        if not seq or not p0:
            return {"cls": None}
        if (sym, d) not in split_c:
            split_c[(sym, d)] = split_ratio(sym, pd_, d, key) if pd_ else None
        sr = split_c[(sym, d)]
        if sr is not None and sr != 1.0:
            return {"cls": None, "split": True}
        R, _m, _H = day_R(seq, p0)
        return {"cls": r_class(R), "R": R}
    ck = set()
    for d in src:
        uni = universe_of(U, d)
        ck |= {(sym, d) for sym in (U["alerts"].get(d) or {}) if sym in uni}
        ck |= {(sym, d) for sym in (S_by.get(d) or ()) if sym in uni}

    def _sp(k):
        pd_, _p0 = prev_close(dly(*k), k[1])
        split_c[k] = split_ratio(k[0], pd_, k[1], key) if pd_ else None
    with ThreadPoolExecutor(8) as pool:
        list(pool.map(_sp, sorted(ck)))
    cost, shadow_cost, outside = [], [], 0
    for d in src:
        uni = universe_of(U, d)
        for sym in sorted(U["alerts"].get(d) or {}):
            if sym not in uni:
                outside += 1
                continue
            c = {"sym": sym, "day": d, **classify(sym, d)}
            j = j1m.get((d, sym))
            c["j1"] = bool(j)
            c["j1_m"] = ny_parts(j["price_ms"])[1] if j else None
            c["has_row"] = (d, sym) in has_row
            cost.append(c)
        for sym in sorted(S_by.get(d) or ()):
            if sym in uni:
                shadow_cost.append({"sym": sym, "day": d, **classify(sym, d)})
    res = summarize(rows, cost, shadow_cost, arm_days, snap_days)
    res["outside"] = outside
    named = []
    by = {(x["sym"], x["day"]): x for x in rows}
    for s_, d_ in NAMED:
        x = by.get((s_, d_))
        if x:
            named.append(f"{s_} {d_}: في الـ248 · R {x['R'] * 100:+.0f}% · الفئة «{x.get('cat') or x['why']}»"
                         + (f" · «هنا الدخول» {_hm(x['fire']['m'])} ({_p(x['fire'].get('pct'))} · بقي {_p(x['fire'].get('left'), False)})" if x.get("fire") else "")
                         + (" · في الظلّ 09:25" if x.get("in_s") else ""))
        else:
            seq = day_seq(bars(s_, d_), d_)
            _pd, p0 = prev_close(dly(s_, d_), d_)
            R, tm, _H = day_R(seq, p0)
            al = (U["alerts"].get(d_) or {}).get(s_)
            named.append(f"{s_} {d_}: **ليس في الـ248** · R المُعادة {_p(R)} (القمّة {_hm(tm)}) · في الكون {'نعم' if s_ in universe_of(U, d_) else 'لا'} · "
                         f"«هنا الدخول» {(_hm(ny_parts(al['ms'])[1]) + ((' $' + format(al['px'], 'g')) if al.get('px') is not None else '')) if al else 'لا'} · في الظلّ 09:25 "
                         f"{'نعم' if s_ in (S_by.get(d_) or ()) else 'لا'}")
        for x in rows:
            if x["sym"] == s_ and x["day"] != d_:
                named.append(f"{s_} {x['day']} (راكضٌ +100% آخر): الفئة «{x.get('cat') or x['why']}»")
    preds = predictions(res)
    meta = {"run": os.environ.get("GITHUB_RUN_ID"), "sha": _git("rev-parse", "HEAD").strip(), "src_days": len(src),
            "sessions": len(U["sessions"]), "snap_days": snap_days}
    for ln in report_lines(res, named, preds, meta):
        log(ln)
    if corr:
        # 🌘 وصفًا (أمرُ المالك ③): الظلُّ 09:25 بالتعريف المصحَّح (ومعه الخارجةُ قبل 09:25) مقابل الرسالة كما هي
        S_full, add_days = {}, 0
        for d in src:
            if d not in snaps:
                S_full[d] = set()
                continue
            h = commit_before(commits, ny_ts(d, SHADOW_NY))
            try:
                state = json.loads(_show(h, STATE_FILE) or "{}")
            except ValueError:
                state = {}
            af = anchors_at_full(state, d, SH)
            extra = [(s_, a_) for s_, a_ in af if s_ not in {x for x, _y in snaps[d][0]}]
            if extra:
                add_days += 1
                for s_, _a in extra:
                    bars(s_, d), dly(s_, d)
            srows, _allr, _sk = SH.shadow_rows(af, lambda s_, _d=d: dly(s_, _d), d, lambda s_, _d=d: bars(s_, _d), snaps[d][1],
                                               lambda s_, _d=d: split_fn(s_, _d, key))
            S_full[d] = {x["sym"] for x in srows}
        r_old = sum(1 for x in rows if x.get("in_s"))
        r_full = sum(1 for x in rows if x["day"] in src and x["sym"] in (S_full.get(x["day"]) or ()))
        f_old = sum(1 for c in shadow_cost if c.get("cls") == "false")
        sc_full = [{"sym": s_, "day": d, **classify(s_, d)} for d in src for s_ in sorted(S_full.get(d) or ()) if s_ in universe_of(U, d)]
        f_full = sum(1 for c in sc_full if c.get("cls") == "false")
        log("\n## 🌘 الظلُّ 09:25 بالتعريفين (وصفًا · الرسالةُ لم تُمَسّ)")
        log(f"- أسماءُ S: الرسالةُ كما هي {sum(len(v) for v in S_by.values())} · بالمصحَّح {sum(len(v) for v in S_full.values())} · أيّامٌ فيها خارجةٌ قبل 09:25 {add_days}")
        log(f"- راكضو +100% في S: كما هي {r_old} · بالمصحَّح {r_full} · وكاذبُ S على الكون: كما هي {f_old} · بالمصحَّح {f_full}")
        log("- الأسماءُ المضافة: " + (" · ".join(f"{s_} {d[5:]}" for d in src for s_ in sorted((S_full.get(d) or set()) - (S_by.get(d) or set()))) or "لا شيء"))
    log("LVS_ROWS " + json.dumps(rows, ensure_ascii=False, default=str))
    log("LVS_JSON " + json.dumps({"res": res, "preds": preds, "named": named, "meta": meta}, ensure_ascii=False, default=str))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("run", "check"), default="run")
    ap.add_argument("--alerts", choices=("frozen", "full"), default="frozen")   # 🔧 CORRECTION_PROTOCOL.md §①
    a = ap.parse_args(argv)
    if not contract_ok():
        log(f"⛔ بصمةُ العقد `{CONTRACT}` تغيّرت أو غاب — المدموجُ لا يُعدَّل (خروج {CONTRACT_RC})")
        return CONTRACT_RC
    if a.mode == "check":
        log("✅ العقدُ مطابقٌ لبصمته")
        return 0
    return mode_run(a.alerts)


if __name__ == "__main__":
    sys.exit(main())
