#!/usr/bin/env python3
"""🌘🎯 `T-SHADOW-TGT` — «عقدُ هدفٍ للظلّ أماميًّا» (العقد `fm_forensics/shadow_tgt/T_SHADOW_TGT_prereg.md` · مدموجٌ قبل أيّ رقم).

**التقاطُ مستويات الذراع ② عند 09:25 (§④):** يُنادى من `shadow_telegram.main` **بعد** إرسال الرسالة وختمها ⟵ لكلّ مرساةِ بريٍّ قبل وقت البناء: الرمزُ
النشطُ في قائمة البوت ⟵ `stop`/`t1`/`t2` منها (`list`) · وإلّا `analyze_one.analyze_on_demand` بالاسم على الشموع اليوميّة **قبل يوم الصفّ وحدَها**
(`stop[0]` = حقلُ القائمة نفسُه · `on_demand`) · والتعذّرُ ⟵ صفٌّ بسببه لا رقم. ⚠️ وشموعُ الأربع ساعات داخل التحليل حتى لحظة الالتقاط (09:25) — بلا نظرٍ لما بعدها.
🔒 الملفُّ `shadow_tgt_levels.jsonl` إلحاقيٌّ (لا يُعدَّل صفٌّ مكتوب · ولا يُكرَّر (يوم، رمز)) · فاشلٌ-آمنٌ مطلقًا: أيُّ عطلٍ ⟵ سطرُ سجلٍّ ولا يمسّ الرسالة ولا الختم ·
ولا تلغرام · ولا قاعدةَ S.

**أداةُ الحكم (§①-§⑤ · 2026-11-18 قبل أوانه):** `--mode status` أعدادٌ فقط (صفوفُ S وC20 من 11-09 · المستبعَدُ لمرساةٍ عند 09:25 أو بعدها · صفوفُ الالتقاط
بمصدرها · والإسقاطُ إلى الثلاثين) **بلا أيّ عائد** · و`--mode run`: دقائقُ Polygon (`tier_fwd_report.fetch_day` بالاسم) ⟵ الذراعان ⟵ **قبل الأوان (أقلُّ من
30 اسمًا مقيسًا في S بالذراع ① وقبل اكتمال جلسة 2026-12-31) خروج 7 بالعدد وحدَه بلا عائد** · وإلّا الحكمُ لكلّ ذراعٍ مرّةً واحدة · و9 إن تغيّرت بصمةُ العقد.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import random
import sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

LEVELS_FILE = "shadow_tgt_levels.jsonl"          # نسبةً إلى جذر المستودع (cwd الـworkflow)
WATCHLIST = "weekly_watchlist.json"
TGT_FROM = "2026-11-09"                          # §① أماميٌّ خالص


def list_levels(sym, wl):
    """مستوياتُ الرمز **النشط** في قائمة البوت ⟵ dict أو None."""
    for s in (wl or {}).get("stocks") or []:
        if str(s.get("symbol") or "").upper() == sym and s.get("status") == "active":
            try:
                return {"stop": float(s["stop"]), "t1": float(s["t1"]), "t2": float(s["t2"])}
            except (KeyError, TypeError, ValueError):
                return None
    return None


def before_day(day, dl):
    """غلافٌ لـ`download_history` يقصّ كلَّ إطارٍ إلى الجلسات **قبل** `day` (لا شمعةَ ليوم الصفّ)."""
    def _dl(syms, *a, **k):
        data = dl(syms, *a, **k) or {}
        out = {}
        for s, df in data.items():
            out[s] = None if df is None else df[[str(x)[:10] < day for x in df.index]]
        return out
    return _dl


def on_demand_levels(sym, day, ao=None):
    """`analyze_one.analyze_on_demand` بالاسم على الشموع قبل `day` ⟵ (dict | None، السبب)."""
    if ao is None:
        import analyze_one as ao
    keep = ao.bot.download_history
    try:
        ao.bot.download_history = before_day(day, keep)
        res = ao.analyze_on_demand(sym)
    except Exception as e:                                          # noqa: BLE001
        return None, f"تعذّر: {type(e).__name__}"
    finally:
        ao.bot.download_history = keep
    r = res[0] if res else None
    if not r:
        return None, str(res[1] if res and len(res) > 1 else "تعذّر")[:80]
    try:
        return {"stop": float(r["stop"][0]), "t1": float(r["t1"]), "t2": float(r["t2"])}, "ok"
    except (KeyError, TypeError, ValueError, IndexError):
        return None, "بلا مستويات"


def _done(path):
    seen = set()
    try:
        with open(path, encoding="utf-8") as fh:
            for ln in fh:
                if ln.strip():
                    x = json.loads(ln)
                    seen.add((x.get("date"), x.get("symbol")))
    except OSError:
        pass
    return seen


def capture(day, syms, wl=None, levels_of=None, path=None, now=None, log=print):
    """§④ ⟵ عددُ الصفوف المكتوبة. `syms` رموزُ مراسي البري قبل وقت البناء · `levels_of(sym, day)` محقونٌ للاختبار."""
    if str(day) < TGT_FROM:
        log(f"🎯 T-SHADOW-TGT: {day} قبل {TGT_FROM} — لا التقاط")
        return 0
    path = path or LEVELS_FILE
    levels_of = levels_of or on_demand_levels
    if wl is None:
        try:
            with open(WATCHLIST, encoding="utf-8") as fh:
                wl = json.load(fh)
        except (OSError, ValueError):
            wl = {}
    seen = _done(path)
    rows = []
    stamp = (now or dt.datetime.now(dt.timezone.utc)).isoformat(timespec="seconds")
    for sym in syms:
        sym = str(sym).upper()
        if (day, sym) in seen:
            continue
        lv, src, why = list_levels(sym, wl), "list", "ok"
        if lv is None:
            try:
                lv, why = levels_of(sym, day)
            except Exception as e:                                  # noqa: BLE001
                lv, why = None, f"تعذّر: {type(e).__name__}"
            src = "on_demand" if lv else "none"
        row = {"schema": 1, "date": day, "symbol": sym, "src": src, "why": why, "captured_at": stamp}
        if lv:
            row.update({k: round(lv[k], 6) for k in ("stop", "t1", "t2")})
        rows.append(row)
        seen.add((day, sym))
    if rows:
        with open(path, "a", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    log(f"🎯 T-SHADOW-TGT التقاطُ 09:25: {len(rows)} رمزًا · من القائمة {sum(r['src'] == 'list' for r in rows)} · "
        f"بالتحليل {sum(r['src'] == 'on_demand' for r in rows)} · بلا مستويات {sum(r['src'] == 'none' for r in rows)}")
    return len(rows)



# ══ أداةُ الحكم (§①-§⑤) ═══════════════════════════════════════════════════════════════════
CONTRACT = os.path.join(HERE, "T_SHADOW_TGT_prereg.md")
CONTRACT_SHA = "1a09ef47428db0391f3f84da6744b165eb637b0acfdc6367ce07ed0cbd2c4b97"
RC_EARLY, RC_CONTRACT, RC_DONE, RC_NOKEY = 7, 9, 6, 3
LEDGER_FILE = "shadow_ready_ledger.jsonl"
RESULT_FILE = os.path.join(HERE, "T_SHADOW_TGT_RESULT.md")   # وجودُه = صدر الحكم (مرّةً واحدة)
NY = ZoneInfo("America/New_York")
ENTRY_NY, CLOSE_NY, END_NY = 9 * 60 + 25, 16 * 60, 20 * 60   # §②
GAP_GOV = 20.0                                                # §① C20
ARM1 = (0.90, 1.20, 1.50)                                     # §③ ① (الوقف · الهدف 1 · الهدف 2) × E
TRIGGER_N, LAST_DAY = 30, "2026-12-31"                        # §⑤
FLOOR, BARS_FAIL_MAX = 20, 0.10                               # §⑤
BOOT_N, SEED = 2000, "TGT1"                                   # §⑤
WHY2 = ("بلا التقاط", "بلا مستويات", "تحت الوقف عند الدخول", "فوق الهدف الأول عند الدخول", "الهدف 1 ليس تحت الهدف 2")


def log(m=""):
    print(m, flush=True)


def contract_ok(path=CONTRACT):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest() == CONTRACT_SHA
    except OSError:
        return False


def ny_parts(t_ms):
    t = dt.datetime.fromtimestamp(int(t_ms) / 1000, dt.timezone.utc).astimezone(NY)
    return t.date().isoformat(), t.hour * 60 + t.minute


def tgt_groups(rows, upto=None):
    """§① ⟵ ({"S","C20": [صف]} · {"S","C20": مستبعَدٌ لمرساةٍ عند 09:25 أو بعدها}) — `fwd`/`pre` من 11-09 حتى `upto`."""
    out, cut = {"S": [], "C20": []}, {"S": 0, "C20": 0}
    for r in rows:
        d = str(r.get("date") or "")
        if r.get("sample") != "fwd" or r.get("tod") != "pre" or d < TGT_FROM or (upto and d > upto):
            continue
        g = r.get("gap_pct")
        if r.get("shadow") is True:
            nm = "S"
        elif r.get("shadow") is False and g is not None and g >= GAP_GOV:
            nm = "C20"
        else:
            continue
        try:
            ad, am = ny_parts(r.get("anchor_ms"))
            late = ad != d or am >= ENTRY_NY
        except Exception:                                            # noqa: BLE001
            late = True
        if late:
            cut[nm] += 1
        else:
            out[nm].append(r)
    return out, cut


def sim_half(seq, stop, tgt):
    """نصفٌ واحد على شموع `(m, o, h, l, c)` ⟵ (سعرُ الخروج، "stop"|"tgt"|"close"). الوقفُ أوّلًا داخل الشمعة · الافتتاحُ تحت الوقف ⟵ الافتتاح · والهدفُ بسعره."""
    for _m, o, h, lo, _c in seq:
        if lo <= stop:
            return min(o, stop), "stop"
        if h >= tgt:
            return tgt, "tgt"
    return seq[-1][4], "close"


def sim_arm(seq, E, stop, t1, t2):
    """§② الذراع على نافذة ⟵ dict: النتيجة = 0.5·r₁ + 0.5·r₂ · ومن مُلئ نصفُه الأوّل/الثاني · ومن أُوقف قبل الهدف الأوّل."""
    x1, k1 = sim_half(seq, stop, t1)
    x2, k2 = sim_half(seq, stop, t2)
    return {"ret": 0.5 * (x1 / E - 1) + 0.5 * (x2 / E - 1), "fill1": k1 == "tgt", "fill2": k2 == "tgt",
            "stop_pre1": k1 == "stop"}


def entry_and_windows(bars, day):
    """§② ⟵ (E، شموعُ 09:25-16:00، شموعُ 09:25-20:00، السبب)."""
    if not bars:
        return None, None, None, "bars"
    seq = []
    for b in bars:
        d, m = ny_parts(b[0])
        if d == day:
            seq.append((m, b[1], b[2], b[3], b[4]))
    pre = [b for b in seq if b[0] < ENTRY_NY]
    if not pre or not pre[-1][4] or pre[-1][4] <= 0:
        return None, None, None, "no_entry"
    n16 = [b for b in seq if ENTRY_NY <= b[0] < CLOSE_NY]
    n20 = [b for b in seq if ENTRY_NY <= b[0] < END_NY]
    if not n16:
        return None, None, None, "no_regular"
    return pre[-1][4], n16, n20, "ok"


def arm2_levels(E, lv):
    """§③ ② أهليّةُ الصفّ ⟵ (dict | None، السبب من `WHY2`)."""
    if lv is None:
        return None, WHY2[0]
    try:
        st, t1, t2 = float(lv["stop"]), float(lv["t1"]), float(lv["t2"])
    except (KeyError, TypeError, ValueError):
        return None, WHY2[1]
    if not st < E:
        return None, WHY2[2]
    if not E < t1:
        return None, WHY2[3]
    if not t1 < t2:
        return None, WHY2[4]
    return {"stop": st, "t1": t1, "t2": t2}, "ok"


def measure_row(bars, day, lv):
    """صفٌّ واحد ⟵ ({"a1": …، "a2": … | None، "why2": …، "src": …} | None، السبب)."""
    E, n16, n20, why = entry_and_windows(bars, day)
    if E is None:
        return None, why
    s1, t1, t2 = (k * E for k in ARM1)
    a1 = sim_arm(n16, E, s1, t1, t2)
    a1["ret20"] = sim_arm(n20, E, s1, t1, t2)["ret"]
    l2, why2 = arm2_levels(E, lv if (lv and lv.get("src") != "none") else (None if lv is None else {}))
    a2 = None
    if l2:
        a2 = sim_arm(n16, E, l2["stop"], l2["t1"], l2["t2"])
        a2["ret20"] = sim_arm(n20, E, l2["stop"], l2["t1"], l2["t2"])["ret"]
    return {"E": E, "a1": a1, "a2": a2, "why2": why2, "src": (lv or {}).get("src")}, "ok"


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2.0


def _diff(by_day, days):
    a = [x for d in days for x in by_day.get(d, {}).get("S", [])]
    b = [x for d in days for x in by_day.get(d, {}).get("C20", [])]
    return None if not a or not b else mean(a) - mean(b)


def boot(by_day, days, n=BOOT_N, seed=SEED):
    """§⑤ فاصلُ 95% بإعادة سحب الجلسات مع الإرجاع — السحبةُ نفسُها للمجموعتين."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        pick = [rng.choice(days) for _ in days]
        v = _diff(by_day, pick)
        if v is not None:
            out.append(v)
    if len(out) < 20:
        return None, None
    out.sort()
    return out[int(0.025 * len(out))], out[min(len(out) - 1, int(0.975 * len(out)))]


def _sgn(x):
    return (x > 0) - (x < 0)


def arm_verdict(by_day, nS, nC, bars_bad):
    """§⑤ ⟵ (الحكم، الفرق، الفاصل، النصفان)."""
    days = sorted(by_day)
    h = len(days) // 2
    d, ci = _diff(by_day, days), boot(by_day, days) if days else (None, None)
    h1, h2 = _diff(by_day, days[:h]), _diff(by_day, days[h:])
    if bars_bad or nS < FLOOR or nC < FLOOR or d is None or ci[0] is None:
        return "لا قياس", d, ci, (h1, h2)
    if (ci[0] > 0 or ci[1] < 0) and h1 is not None and h2 is not None and _sgn(h1) == _sgn(d) == _sgn(h2):
        return "يفرّق", d, ci, (h1, h2)
    return "لا يفرّق", d, ci, (h1, h2)


def triggered(n_s_arm1, now_ny):
    """§⑤ ⟵ (هل حان؟، يومُ القطع). الثلاثون اسمًا في S بالذراع ① أو اكتمالُ جلسة 2026-12-31."""
    after = now_ny.date().isoformat() > LAST_DAY or (now_ny.date().isoformat() == LAST_DAY and now_ny.hour >= 20)
    if after:
        return True, LAST_DAY
    return n_s_arm1 >= TRIGGER_N, None


def load_levels(path=None):
    out = {}
    try:
        with open(path or LEVELS_FILE, encoding="utf-8") as fh:
            for ln in fh:
                if ln.strip():
                    x = json.loads(ln)
                    out.setdefault((x.get("date"), str(x.get("symbol") or "").upper()), x)
    except OSError:
        pass
    return out


def load_ledger(path=LEDGER_FILE):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


def status_lines(rows, levels):
    """أعدادٌ فقط — بلا عائد."""
    grp, cut = tgt_groups(rows)
    days = sorted({r["date"] for r in rows if r.get("sample") == "fwd" and r.get("tod") == "pre" and str(r.get("date")) >= TGT_FROM})
    nS = len(grp["S"])
    per = (nS / len(days)) if days else 0.0
    left = max(0, TRIGGER_N - nS)
    src = {}
    for (d, _s), x in levels.items():
        if d >= TGT_FROM:
            src[x.get("src")] = src.get(x.get("src"), 0) + 1
    capS = sum(1 for r in grp["S"] if (r["date"], str(r["symbol"]).upper()) in levels)
    return [f"🎯 T-SHADOW-TGT status (أعدادٌ فقط · لا عائد) · الجلساتُ ذاتُ صفوف من {TGT_FROM}: {len(days)} ({days[0] if days else '—'} … {days[-1] if days else '—'})",
            f"   S {nS} · C20 {len(grp['C20'])} · مستبعَدٌ لمرساةٍ عند 09:25 أو بعدها S {cut['S']} · C20 {cut['C20']}",
            f"   الالتقاط: صفوف {sum(src.values())} · " + " · ".join(f"{k} {v}" for k, v in sorted(src.items(), key=lambda kv: str(kv[0])))
            + f" · أسماءُ S الملتقَطة {capS} من {nS}",
            f"   الإسقاط: {per:.2f} اسمًا في S لكلّ جلسة · الباقي إلى {TRIGGER_N} ⟵ {left}"
            + (f" (≈{left / per:.1f} جلسة)" if per > 0 and left else "")
            + " · ⚠️ العدُّ قبل الشموع (المقيسُ في الذراع ① قد يقلّ بتعذّرها)"]


def run(rows, levels, fetch, now_ny, done=False):
    """§①-§⑤ ⟵ (رمزُ الخروج، الأسطر). `fetch(sym, day)` ⟵ شموع."""
    if done:
        return RC_DONE, [f"⛔ صدر الحكمُ سلفًا (`{os.path.basename(RESULT_FILE)}`) — مرّةً واحدة لكلّ ذراع (§⑤) · خروج {RC_DONE}"]
    grp, cut = tgt_groups(rows, LAST_DAY)
    meas, fails, why2 = {"S": [], "C20": []}, {"S": {}, "C20": {}}, {"S": {}, "C20": {}}
    for g, rr in grp.items():
        for r in rr:
            sym, day = str(r["symbol"]).upper(), r["date"]
            m, why = measure_row(fetch(sym, day), day, levels.get((day, sym)))
            if m is None:
                fails[g][why] = fails[g].get(why, 0) + 1
                continue
            meas[g].append((day, sym, m))
            if m["a2"] is None:
                why2[g][m["why2"]] = why2[g].get(m["why2"], 0) + 1
    ok, upto = triggered(len(meas["S"]), now_ny)
    if not ok:
        return RC_EARLY, [f"⏳ قبل الأوان: أسماءُ S المقيسةُ في الذراع ① {len(meas['S'])} من {TRIGGER_N} وقبل اكتمال جلسة {LAST_DAY} — لا عائدَ يُطبع (خروج {RC_EARLY})"]
    L = [f"🎯 T-SHADOW-TGT — الحكم · S {len(meas['S'])} · C20 {len(meas['C20'])} مقيسًا · مستبعَدٌ (مرساةٌ عند 09:25 أو بعدها) {cut} · تعذّر {fails}"]
    tot = {g: len(grp[g]) for g in grp}
    bars_bad = any(tot[g] and sum(fails[g].values()) / tot[g] > BARS_FAIL_MAX for g in tot)
    res = {}
    for arm in ("a1", "a2"):
        by_day, n = {}, {"S": 0, "C20": 0}
        for g in ("S", "C20"):
            for d, _s, m in meas[g]:
                if m[arm] is not None:
                    by_day.setdefault(d, {}).setdefault(g, []).append(m[arm]["ret"])
                    n[g] += 1
        v, d_, ci, hh = arm_verdict(by_day, n["S"], n["C20"], bars_bad)
        res[arm] = (v, n)
        pc = lambda x: "—" if x is None else f"{x:+.2%}"                         # noqa: E731
        L.append(f"⚖️ الذراع {'①' if arm == 'a1' else '②'}: S {n['S']} · C20 {n['C20']} · الفرق S − C20 {pc(d_)} [{pc(ci[0])}، {pc(ci[1])}] · "
                 f"النصفان {pc(hh[0])} · {pc(hh[1])} ⟵ «{v}»")
        for g in ("S", "C20"):
            xs = [m[arm] for _d, _s, m in meas[g] if m[arm] is not None]
            k = len(xs) or 1
            L.append(f"   {g}: متوسّط {pc(mean([x['ret'] for x in xs]))} · وسيط {pc(median([x['ret'] for x in xs]))} · موجب {sum(x['ret'] > 0 for x in xs)}/{len(xs)} · "
                     f"مُلئ النصف 1 {sum(x['fill1'] for x in xs) / k:.1%} · النصف 2 {sum(x['fill2'] for x in xs) / k:.1%} · أُوقف قبل الهدف 1 {sum(x['stop_pre1'] for x in xs) / k:.1%} · "
                     f"حتى 20:00 متوسّط {pc(mean([x['ret20'] for x in xs]))}")
            if arm == "a2":
                srcs = {}
                for _d, _s, m in meas[g]:
                    if m["a2"] is not None:
                        srcs[m["src"]] = srcs.get(m["src"], 0) + 1
                L.append(f"   {g} مستبعَدٌ من ② بأسبابه {why2[g]} · مصدرُ المستويات {srcs}")
    if bars_bad:
        L.append(f"⚠️ شموعٌ متعذّرة فوق {BARS_FAIL_MAX:.0%} من صفوف مجموعة ⟵ «لا قياس» للذراعين")
    a1S = [m["a1"] for _d, _s, m in meas["S"]]
    elig2 = sum(1 for _d, _s, m in meas["S"] if m["a2"] is not None)
    mS = mean([x["ret"] for x in a1S])
    f1 = (sum(x["fill1"] for x in a1S) / len(a1S)) if a1S else None
    P = [("K1", elig2 < len(meas["S"]) / 2, f"مؤهَّلُ ② في S {elig2} من {len(meas['S'])}"),
         ("K2", res["a1"][0] == "لا يفرّق", f"① «{res['a1'][0]}»"),
         ("K3", res["a2"][0] == "لا قياس", f"② «{res['a2'][0]}»"),
         ("K4", mS is not None and -0.05 <= mS <= 0.05, f"متوسّطُ ① لـS {'—' if mS is None else f'{mS:+.2%}'}"),
         ("K5", f1 is not None and 0.30 <= f1 <= 0.55, f"مُلئ النصفُ الأوّل في S {'—' if f1 is None else f'{f1:.1%}'}"),
         ("K6", upto is None, "وقع بالثلاثين قبل 12-31" if upto is None else "وقع بتاريخ 12-31")]
    L.append("   التنبّؤات: " + " · ".join(f"{k} {'✅' if ok_ else '❌'} {t}" for k, ok_, t in P))
    return 0, L


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("status", "run"), default="status")
    a = ap.parse_args(argv)
    if not contract_ok():
        log(f"⛔ بصمةُ العقد `{CONTRACT}` تغيّرت أو غاب — المدموجُ لا يُعدَّل (خروج {RC_CONTRACT})")
        return RC_CONTRACT
    rows, levels = load_ledger(), load_levels()
    if a.mode == "status":
        for ln in status_lines(rows, levels):
            log(ln)
        return 0
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log(f"⛔ بلا مفتاح Polygon — لا قياس (خروج {RC_NOKEY})")
        return RC_NOKEY
    from tier_fwd_report import fetch_day
    rc, lines = run(rows, levels, lambda s, d: fetch_day(s, d, key), dt.datetime.now(NY), done=os.path.exists(RESULT_FILE))
    for ln in lines:
        log(ln)
    return rc


if __name__ == "__main__":
    sys.exit(main())
