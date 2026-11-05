"""📈✖️ «التقاطع الذهبي» — الذراع ب: تقاطعُ EMA8/EMA15 على الدقيقة لأسهم الزخم بتعريف نايف (@Naifo9x) · تنبيهٌ فقط.

**العقد:** `fm_forensics/ema_cross/T_GCROSS_prereg.md` (مدموجٌ قبل أيّ رقم · `GCX0`) — كلُّ بندٍ هنا برقمه هناك (B-① … B-⑪).
**التطبيقُ بالحرف:** لا شرطَ من عندي — وما لم يقله نايف يُطبع «غير محدّد في المصدر» ويُترك للمالك.

- B-② المتوسّطان بـ`vwap_momentum_live.ema_last` **بالاسم** (‏`ema_series` توأمُها المتزايد · مقفولٌ بالتطابق في `GCB1`).
- B-④ المجتمع = مرشِّحُ الفيواب `prefilter` بالاسم ثمّ شروطُ `CHECK_ORDER_A5` **عدا ③ L** بدوالّ الفيواب نفسِها بالاسم.
- **لا تلغرامَ قبل عبور القبول ② وكلمةِ المالك «فعّل الذهبي»:** الإرسالُ لا يقع إلّا بـ`GC_SEND=1` **والـworkflow لا يحمل سرَّ تلغرام** (`GCB6`).

الأوضاع (`--mode`): `accept` (الشهود B1-B3 · إعادةٌ صامتة على Polygon) · `measure` (القياس ③ · 60 جلسة) · `trace` (رمزٌ ويوم) ·
`live` (الحلقةُ الحيّة · صامتةٌ ما لم يُضبط `GC_SEND=1`). **قراءةٌ وتنبيه — خارج الجذور · لا `LOGIC_VERSION` · لا يمسّ `Super_stock.py`.**
"""
import argparse
import datetime as dt
import json
import os
import random
import sys
import time

import vwap_momentum_live as V

V3, V4, NY = V.V3, V.V4, V.NY

# ── الثوابت (كلٌّ بوسمه في `FAISAL_SOURCE_LEDGER.md §T-GCROSS`) ─────────────────────────────────────────────
FAST_N, SLOW_N = 8, 15                       # B-② «متوسط 8 يقطع متوسط 15» · رأسا شارتَي CHSN وOMH — `nayef_verbatim`
MEASURE_ARMS = ((8, 15), (9, 15), (8, 16))   # ⑤ الحيُّ أوّلًا (الحاكم) ثمّ «9 و15» و«15 أو 16» — قياسٌ فقط
ACCEPT_TOL = 0.02                            # ④ «بفارق ≤2%» — برومبتُ المالك (`engineering`)
SEED = 20261105                              # ⑤ بذرةُ الضابط والبوتستراب — العقد
BOOT_N = 10000                               # ⑤ عددُ إعادات البوتستراب — العقد
MIN_CYCLES = 30                              # ⑤ أقلُّ من 30 دورةً في الذراع ⟵ «لا قياس» — العقد
N_SESSIONS = 60                              # ⑤ آخرُ 60 جلسةً مكتملة — برومبتُ المالك
LEDGER = "ema_cross_ledger.jsonl"            # B-⑪ سجلُّ الحصاد الإلحاقيّ (يُدفَع لحظةَ كلّ صفّ — بعد «فعّل الذهبي»)
SILENT_LEDGER = "ema_cross_ledger_silent.jsonl"   # التجربةُ الصامتة: ملفٌّ محلّيٌّ على الرنر لا يُدفع (`.gitignore`)
SEND_ENV, UNIVERSE_ENV, EXT_ENV = "GC_SEND", "GC_UNIVERSE", "GC_EXT"
UNIVERSE_OK = ("vwap", "top_gainers")        # B-④ `vwap` الافتراض · و`top_gainers` بديلٌ للمالك (لا يعمل افتراضًا)
CHECK_ORDER = tuple(c for c in V.CHECK_ORDER_A5 if c != "③ L")   # B-④ ترتيبُ الملحق 5 عدا ③ L (جزءٌ من زناد الفيواب)
POLL_STEPS_S = (1, 2, 3, 4, 5, 7, 10)        # B-⑨ تحقّقُ REST: إعادةُ الجلب حتى تظهر الدقيقة (آخرُها مهلةٌ دون LAT_WARN_S)
UNSPEC = "غير محدّد في المصدر"

# ④ الشهود — أرقامُ نايف كما نقلها المالك (العقد §④)
WITNESS_B = (
    {"id": "B1", "sym": "CHSN", "day": "2026-10-21",
     "seq": [("+", 1.19, None), ("-", None, 3.00), ("+", 2.00, None), ("-", 3.49, None)],
     "note": {"peak_after_3": 4.15}},
    {"id": "B2", "sym": "OMH", "day": "2026-11-04", "seq": [("+", 5.80, None)], "note": {"low_before": 5.76, "high_after": 9.20}},
)
WITNESS_B3 = {"id": "B3", "sym": "OMH", "day": "2026-11-04", "px": 3.00, "low": 3.03, "high": 17.80}


def log(m=""):
    print(m, flush=True)


# ── دوالُّ نقيّة (بلا شبكة · مقفولةٌ في السويّة) ────────────────────────────────────────────────────────
def ema_series(values, n):
    """EMA لكلّ موضع = `V.ema_last(values[:i+1], n)` بالضبط (α = 2/(n+1) · البذرةُ أوّلُ قيمة) — متزايدٌ لا تربيعيّ (`GCB1`)."""
    a, e, out = 2.0 / (n + 1.0), None, []
    for x in values:
        e = x if e is None else a * x + (1.0 - a) * e
        out.append(e)
    return out


def regular(bars, op, cl):
    """B-① دقائقُ الجلسة النظاميّة وحدَها [op، cl) مرتّبة — والدقيقةُ بلا صفقةٍ غائبةٌ لا تُملأ."""
    return sorted((b for b in bars or () if op <= b[0] < cl), key=lambda b: b[0])


def resample(bars, k, op, cl):
    """شموعُ k دقيقة من دقائق النظاميّة (B3 وصفًا): السلّةُ op + ⌊(m−op)/k⌋·k · افتتاحُ أوّلها · أعلى/أدنى · إغلاقُ آخرها · مجموعُ الحجم."""
    out = {}
    for m, o, h, low, c, v in regular(bars, op, cl):
        s = op + ((m - op) // k) * k
        r = out.get(s)
        out[s] = (s, o, h, low, c, v) if r is None else (s, r[1], max(r[2], h), min(r[3], low), c, r[5] + v)
    return [out[s] for s in sorted(out)]


def crosses(bars, fast=FAST_N, slow=SLOW_N):
    """B-③ تقاطعاتُ الشموع المرتّبة ⟵ [{i · m · sign («+»/«-») · px · ef · es}] — الإيجابيُّ: السريعُ فوق البطيء الآن وليس فوقه قبلها ·
    السلبيُّ عكسُه · والتساوي «ليس فوق» · والشمعةُ الأولى بلا تقاطع."""
    closes = [b[4] for b in bars]
    ef, es = ema_series(closes, fast), ema_series(closes, slow)
    out = []
    for i in range(1, len(bars)):
        now_up, prev_up = ef[i] > es[i], ef[i - 1] > es[i - 1]
        if now_up != prev_up:
            out.append({"i": i, "m": bars[i][0], "sign": "+" if now_up else "-", "px": closes[i], "ef": ef[i], "es": es[i]})
    return out


def match_seq(xs, bars, seq, tol=ACCEPT_TOL):
    """④ مطابقةُ تسلسل نايف بالترتيب: لكلّ بند (الإشارة، السعر أو None، القمّة أو None) أوّلُ تقاطعٍ بإشارته **بعد** المطابَق السابق ·
    سعرُه ضمن ±tol من رقم نايف (إن وُجد) · وإن كان للبند قمّة: أعلى `h` من دقيقة المطابَق السابق حتى دقيقته ضمن ±tol منها ⟵
    [{ok · x · diff · peak}] — وما بعد أوّل سقوطٍ لا يُطابَق (يُطبع «—»)."""
    out, after, prev_m, stop = [], -1, None, False
    for sign, px, peak in seq:
        hit = None
        if not stop:
            for x in xs:
                if x["i"] <= after or x["sign"] != sign:
                    continue
                if px is not None and round(abs(x["px"] / px - 1.0), 9) > tol:     # الحدُّ شاملٌ بلا خطأ فاصلةٍ عائمة (كـ`V4.ge`)
                    continue
                pk = None
                if peak is not None:
                    lo_m = prev_m if prev_m is not None else bars[0][0]
                    pk = max((b[2] for b in bars if lo_m <= b[0] <= x["m"]), default=None)
                    if pk is None or round(abs(pk / peak - 1.0), 9) > tol:
                        continue
                hit = (x, pk)
                break
        if hit is None:
            out.append({"ok": False, "x": None, "diff": None, "peak": None, "want": (sign, px, peak)})
            stop = True
            continue
        x, pk = hit
        out.append({"ok": True, "x": x, "diff": None if px is None else x["px"] / px - 1.0, "peak": pk, "want": (sign, px, peak)})
        after, prev_m = x["i"], x["m"]
    return out


def cycle_from(bars, xs, entry_i):
    """دورةٌ تبدأ بإغلاق الشمعة `entry_i` وتنتهي عند أوّل سلبيٍّ **بعدها** أو «الإغلاق» (آخرُ شمعة) ⟵ {الدخول · الخروج · النتيجة ·
    أقصى الربح (أعلى `h` بعد الدخول حتى الخروج شاملًا) · المدّة بالدقائق · نوعُ الخروج}."""
    neg = next((x for x in xs if x["sign"] == "-" and x["i"] > entry_i), None)
    ex_i, kind = (neg["i"], "neg") if neg else (len(bars) - 1, "close")
    e_px, x_px = bars[entry_i][4], bars[ex_i][4]
    hi = max((b[2] for b in bars[entry_i + 1:ex_i + 1]), default=x_px)
    return {"entry_m": bars[entry_i][0], "entry_px": e_px, "exit_m": bars[ex_i][0], "exit_px": x_px, "exit": kind,
            "ret": x_px / e_px - 1.0, "maxp": hi / e_px - 1.0, "dur": bars[ex_i][0] - bars[entry_i][0]}


def cycles(bars, xs, entry_ok):
    """B-⑤ الدورات: كلُّ إيجابيٍّ يعبر `entry_ok(x)` ولا دورةَ مفتوحة يفتح دورةً تُغلَق بالسلبيّ التالي (أو «الإغلاق») · وإعادةُ الدخول
    بكلّ إيجابيٍّ جديد (CHSN «تقاطع ثاني مرة»)."""
    out, open_until = [], -1
    for x in xs:
        if x["sign"] != "+" or x["i"] <= open_until or not entry_ok(x):
            continue
        c = cycle_from(bars, xs, x["i"])
        c["n"] = 1 + sum(1 for y in xs if y["sign"] == "+" and y["i"] < x["i"])
        out.append(c)
        open_until = next((y["i"] for y in xs if y["sign"] == "-" and y["i"] > x["i"]), len(bars))
    return out


def pct_from_low(bars, i):
    """% الإغلاق عند i من أدنى `l` نظاميٍّ حتى i (عرضٌ B-⑦)."""
    lo = min(b[3] for b in bars[:i + 1])
    return bars[i][4] / lo - 1.0 if lo > 0 else None


def vwap_side(bars, i):
    """«فوق/تحت» فيواب الجلسة عند i بـ`V3.vwap_series` بالاسم — معلومةٌ لا شرط (B-⑦)."""
    vw = V3.vwap_series(bars[:i + 1])
    v = vw[-1] if vw else None
    return None if v is None else ("فوق" if bars[i][4] > v else "تحت")


def momentum_why(info, type_status, spac, cat_C):
    """B-④ شروطُ المجتمع بترتيب `CHECK_ORDER` (الملحق 5 عدا ③ L) ⟵ قائمةُ ما سقط (فارغةٌ = داخل المجتمع) — تقف عند أوّل سقوط.
    `info` = {px · cum_dollar · chg} · `type_status` ∈ {ok · excluded · unknown} · `spac` وسمٌ أو None · `cat_C` ∈ {True · False · None}."""
    if not (V.PX_MIN <= info["px"] < V.PX_MAX):
        return ["⑤ السعر"]
    if info["cum_dollar"] < V.D_MIN_LIVE:
        return ["الحجم الدولاري"]
    if not V4.ge(info["chg"], V.CHG_MIN):
        return ["① التغيّر"]
    if type_status != "ok":
        return ["⑤ النوع" + (" (مجهول)" if type_status == "unknown" else "")]
    if spac:
        return ["⑤ " + str(spac)]
    if cat_C is not True:
        return ["④ الخبر" + (" (مجهول)" if cat_C is None else "")]
    return []


def wilson(k, n, z=1.959964):
    """فاصل Wilson 95% لنسبة k/n ⟵ (أدنى، أعلى) أو (None، None)."""
    if not n:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return ((c - r) / d, (c + r) / d)


def _median(xs):
    return V._median(xs) if xs else None


def summarize(cyc):
    """⑤ ملخّصُ ذراعٍ أو ضابط: الدورات · الوسيط · المتوسّط · ‏+7% · ‏+20% · السالبة (بـWilson) · وسيطُ أقصى الربح والمدّة · حصّةُ «الإغلاق»."""
    n = len(cyc)
    rs = [c["ret"] for c in cyc]
    k7, k20, kn = sum(r >= 0.07 for r in rs), sum(r >= 0.20 for r in rs), sum(r < 0 for r in rs)
    return {"n": n, "median": _median(rs), "mean": (sum(rs) / n) if n else None,
            "ge7": (k7, wilson(k7, n)), "ge20": (k20, wilson(k20, n)), "neg": (kn, wilson(kn, n)),
            "maxp_median": _median([c["maxp"] for c in cyc]), "dur_median": _median([c["dur"] for c in cyc]),
            "close_share": (sum(c["exit"] == "close" for c in cyc) / n) if n else None}


def cluster_boot(pairs, n_boot=BOOT_N, seed=SEED):
    """⑤ P4: `pairs` = {عنقود (رمز·يوم): ([نتائجُ الذراع]، [نتائجُ الضابط])} ⟵ (الفرق، أدنى 2.5%، أعلى 97.5%) لفرق متوسّط النتيجة لكلّ دورة
    بإعادة سحب العناقيد مع الإحلال — أو (None، None، None) بلا عنقود."""
    keys = sorted(pairs)
    if not keys:
        return (None, None, None)

    def diff(ks):
        a = [r for k in ks for r in pairs[k][0]]
        b = [r for k in ks for r in pairs[k][1]]
        return (sum(a) / len(a) - sum(b) / len(b)) if a and b else None
    rng = random.Random(seed)
    base = diff(keys)
    ds = sorted(d for d in (diff([keys[rng.randrange(len(keys))] for _ in keys]) for _ in range(n_boot)) if d is not None)
    if not ds:
        return (base, None, None)
    return (base, ds[int(0.025 * (len(ds) - 1))], ds[int(0.975 * (len(ds) - 1))])


def build_message(row):
    """B-⑦ نصُّ التنبيه (عرضٌ فقط) — بلا علامات مقارنة."""
    sym, px, t = row["sym"], row["px"], row["time_ny"]
    if row["sign"] == "+":
        lines = [f"✅ تقاطع إيجابي — ${sym}", f"💵 ${px:g} · 🕐 {t} نيويورك",
                 f"📈 EMA8 {row['ef']:.4g} فوق EMA15 {row['es']:.4g} · تقاطع رقم {row['n']} اليوم"]
    else:
        lines = [f"❌ تقاطع سلبي — خروج — ${sym}", f"💵 ${px:g} · 🕐 {t} نيويورك",
                 f"📉 EMA8 {row['ef']:.4g} تحت EMA15 {row['es']:.4g}"]
        if row.get("ret") is not None:
            lines.append(f"🧾 نتيجة الدورة من آخر إيجابي ${row['entry_px']:g}: {row['ret'] * 100:+.1f}%")
    if row.get("from_low") is not None:
        lines.append(f"↗️ من قاع اليوم {row['from_low'] * 100:+.1f}%")
    if row.get("vwap_side"):
        lines.append(f"〰️ الفيواب: {row['vwap_side']} (معلومة لا شرط)")
    lines.append("⚠️ قيد الإثبات الأمامي · نايف (@Naifo9x) — الهدف والوقف غير محدّدين في المصدر")
    return "\n".join(lines)


def hm(m):
    return f"{m // 60:02d}:{m % 60:02d}"


# ── وضعُ القبول ② ─────────────────────────────────────────────────────────────────────────────────────────
def _membership(D, sym, all_bars, x):
    """B-④ عند نهاية دقيقة التقاطع ⟵ قائمةُ ما سقط (وصفٌ في القبول · شرطٌ في القياس والحيّ)."""
    e = x["m"] + 1
    info = {"px": x["px"], "cum_dollar": V3.cum_dollar_at(all_bars, e), "chg": V4.pct_change(x["px"], D.prev_adj(sym))}
    why = momentum_why(info, "ok", None, True)
    if why:
        return why
    ts = D.type_status(sym)
    cat_of, _detail, spac = D.catalyst(sym, V3.ny_ts(D.day, e))
    return momentum_why(info, ts, spac, cat_of(e).get("C"))


def mode_accept(net, MC):
    """② الشهود B1-B3 على دقائق Polygon (`adjusted=false` · أسعارُ يومها) ⟵ لكلّ بند: التُقط؟ السعر · الوقت · الفرق · والمجتمعُ لحظتَها وصفًا ·
    وتسلسلُ OMH كلُّه بنتيجة كلّ دورة · وB3 بالحاكم (8/15 · دقيقة) ثمّ التركيباتُ الوصفيّة. ⟵ 0 عبر · 1 سقط · 4 تعذّرت البيانات."""
    out, ok_all, bad = {"mode": "accept", "witnesses": []}, True, False
    days = {}
    for w in list(WITNESS_B) + [WITNESS_B3]:
        days.setdefault((w["sym"], w["day"]), None)
    for (sym, day) in days:
        by = net.minutes(sym, day, day)
        info = MC.session_info(day)
        if by is None or not (by or {}).get(day):
            log(f"⛔ {sym} {day}: تعذّرت دقائقُ Polygon")
            bad = True
            continue
        D = V.Day(net, day, MC, replay=True)
        days[(sym, day)] = (by[day], info["open_ny_min"], info["close_ny_min"], D)
    for w in WITNESS_B:
        got = days.get((w["sym"], w["day"]))
        if got is None:
            ok_all = False
            continue
        allb, op, cl, D = got
        bars = regular(allb, op, cl)
        xs = crosses(bars)
        res = match_seq(xs, bars, w["seq"])
        ok = all(r["ok"] for r in res)
        ok_all = ok_all and ok
        log(f"{'✅' if ok else '❌'} {w['id']} ${w['sym']} {w['day']} · EMA{FAST_N}/{SLOW_N} دقيقة · تقاطعاتُ اليوم {len(xs)}")
        rows = []
        for r in res:
            s, px, pk = r["want"]
            want = f"{s} {px if px is not None else 'بعد قمّة ' + str(pk)}"
            if not r["ok"]:
                log(f"   ✗ {want} ⟵ لم يُلتقط")
                rows.append({"want": want, "ok": False})
                continue
            x = r["x"]
            mem = _membership(D, w["sym"], allb, x)
            d = "" if r["diff"] is None else f" · الفرق {r['diff'] * 100:+.2f}%"
            p = "" if r["peak"] is None else f" · القمّة قبله {r['peak']:g}"
            log(f"   ✓ {want} ⟵ {hm(x['m'])} ${x['px']:g}{d}{p} · المجتمع لحظتَها: {'داخل' if not mem else 'خارج ' + mem[0]}")
            rows.append({"want": want, "ok": True, "m": hm(x["m"]), "px": x["px"], "diff": r["diff"], "peak": r["peak"], "out": mem})
        if w["id"] == "B1" and all(r["ok"] for r in res[2:4]):
            i3, i4 = res[2]["x"]["m"], res[3]["x"]["m"]
            pk = max(b[2] for b in bars if i3 <= b[0] <= i4)
            log(f"   ℹ️ أعلى قمّةٍ بين الثالث والرابع {pk:g} مقابل {w['note']['peak_after_3']}")
        out["witnesses"].append({"id": w["id"], "ok": ok, "rows": rows})
    # B3 — الحاكمُ ثمّ التركيباتُ الوصفيّة
    got = days.get((WITNESS_B3["sym"], WITNESS_B3["day"]))
    b3 = {"id": "B3", "ok": False, "combos": []}
    if got is None:
        ok_all = False
    else:
        allb, op, cl, D = got
        bars1 = regular(allb, op, cl)
        b2 = match_seq(crosses(bars1), bars1, WITNESS_B[1]["seq"])
        lim = b2[0]["x"]["m"] if b2[0]["ok"] else cl
        reg_low = min(b[3] for b in bars1)
        ext_low = min(b[3] for b in allb)
        log(f"ℹ️ B3 قاعُ OMH {WITNESS_B3['day']}: نظاميّ {reg_low:g} · ممتدّ {ext_low:g} · مقابل {WITNESS_B3['low']} · وأعلى اليوم النظاميّ "
            f"{max(b[2] for b in bars1):g} مقابل {WITNESS_B3['high']}")
        for k, (f, s) in ((1, (8, 15)), (1, (9, 15)), (5, (8, 15)), (5, (9, 15))):
            bk = bars1 if k == 1 else resample(allb, k, op, cl)
            xs = [x for x in crosses(bk, f, s) if x["m"] < lim]
            hit = next((x for x in xs if x["sign"] == "+" and round(abs(x["px"] / WITNESS_B3["px"] - 1.0), 9) <= ACCEPT_TOL), None)
            gov = (k, f, s) == (1, FAST_N, SLOW_N)
            tag = "الحاكم" if gov else "وصفًا"
            if hit:
                log(f"   {'✅' if gov else 'ℹ️'} B3 [{tag}] {f}/{s} · {k}د ⟵ إيجابيّ {hm(hit['m'])} ${hit['px']:g} · الفرق "
                    f"{(hit['px'] / WITNESS_B3['px'] - 1) * 100:+.2f}%")
            else:
                near = [x for x in xs if x["sign"] == "+"][:3]
                log(f"   {'❌' if gov else 'ℹ️'} B3 [{tag}] {f}/{s} · {k}د ⟵ لا إيجابيّ ضمن ±2% من 3.00 قبل {hm(lim)} · أوّلُ الإيجابيّات: "
                    + (" · ".join(f"{hm(x['m'])} ${x['px']:g}" for x in near) or "لا شيء"))
            b3["combos"].append({"k": k, "fast": f, "slow": s, "gov": gov, "hit": None if not hit else {"m": hm(hit["m"]), "px": hit["px"]}})
            if gov:
                b3["ok"] = hit is not None
        ok_all = ok_all and b3["ok"]
        # تسلسلُ OMH كلُّه من الافتتاح إلى الإغلاق بنتيجة كلّ دورة (بلا فحص مجتمع · وعضويّتُه وصفًا)
        xs = crosses(bars1)
        log(f"📜 OMH {WITNESS_B3['day']} — التقاطعاتُ كلُّها ({len(xs)}) ودوراتُها (EMA{FAST_N}/{SLOW_N} · دقيقة):")
        for c in cycles(bars1, xs, lambda x: True):
            ent = next(x for x in xs if x["m"] == c["entry_m"])
            mem = _membership(D, WITNESS_B3["sym"], allb, ent)
            log(f"   #{c['n']} ⟵ {hm(c['entry_m'])} ${c['entry_px']:g} ⟵ {hm(c['exit_m'])} ${c['exit_px']:g} ({'سلبيّ' if c['exit'] == 'neg' else 'الإغلاق'}) · "
                f"{c['ret'] * 100:+.1f}% · أقصى {c['maxp'] * 100:+.1f}% · {c['dur']}د · المجتمع: {'داخل' if not mem else 'خارج ' + mem[0]}")
    out["witnesses"].append(b3)
    out["ok"] = bool(ok_all and not bad)
    out["calls"], out["fails"] = net.calls, net.fails
    log(f"{'✅' if out['ok'] else '❌'} **القبول ② (الذراع ب):** {'عبر B1 وB2 وB3 بالحاكم' if out['ok'] else 'لم يعبر — أين سقط مطبوعٌ أعلاه'}")
    log("GCROSS_JSON " + json.dumps(out, ensure_ascii=False, sort_keys=True, default=str))
    return 4 if bad else (0 if out["ok"] else 1)


# ── وضعُ القياس ③ ────────────────────────────────────────────────────────────────────────────────────────
def sessions_before(MC, end_day, n):
    """آخرُ n جلسةً مكتملة حتى `end_day` شاملًا (`V3.is_session` بالاسم) ⟵ مرتّبةً تصاعديًّا."""
    out, d = [], dt.date.fromisoformat(end_day)
    while len(out) < n:
        if V3.is_session(d.isoformat(), MC.session_info):
            out.append(d.isoformat())
        d -= dt.timedelta(1)
    return out[::-1]


def control_cycles(bars, xs, ok_idx, n, rng):
    """⑤ الضابط: n دخولًا بدقائقَ عشوائيّة (مع الإحلال) من `ok_idx` (دقائقُ يعبر فيها B-④ · عدا آخر دقيقة) بخروجٍ عند السلبيّ التالي."""
    pool = [i for i in ok_idx if i < len(bars) - 1]
    if not pool:
        return []
    return [cycle_from(bars, xs, pool[rng.randrange(len(pool))]) for _ in range(n)]


def mode_measure(net, MC, end_day, n_sessions=N_SESSIONS):
    """③ القياس: 60 جلسة · كونُ الفيواب المُعاد بناؤه · لكلّ ذراعٍ دوراتُه داخل المجتمع وضابطُه ⟵ الملخّصُ وP1-P4. بلا تلغرام · بلا سجلّ."""
    days = sessions_before(MC, end_day, n_sessions)
    log(f"📅 الجلسات {len(days)}: {days[0]} ⟵ {days[-1]} · الأذرع {MEASURE_ARMS} · البذرة {SEED}")
    rng = random.Random(SEED)
    per = {a: {"cyc": [], "ctl": [], "pairs": {}, "pos_all": [], "pos_in": []} for a in MEASURE_ARMS}
    bad_days, miss_total = [], 0
    for day in days:
        D = V.Day(net, day, MC, replay=True)
        g = net.poly(f"/v2/aggs/grouped/locale/us/market/stocks/{day}", {"adjusted": "false"})
        hl = {str(r.get("T") or "").upper(): (r.get("h"), r.get("l"), r.get("v")) for r in ((g or {}).get("results") or []) if r.get("T")}
        if not D.ok or not hl:
            bad_days.append(day)
            log(f"⛔ {day}: مرجعٌ ناقص {D.why + ([] if hl else ['شمعةُ اليوم المجمَّعة'])}")
            continue
        cands = sorted(V.prefilter(hl, D.prev_adj_pf, D.types))
        miss = 0
        for sym in cands:
            by = net.minutes(sym, day, day)
            if by is None:
                miss += 1
                continue
            allb = (by or {}).get(day) or []
            bars = regular(allb, D.op, D.cl)
            if len(bars) < 2:
                continue
            memo = {}

            def ok_at(i, _bars=bars, _allb=allb, _sym=sym, _memo=memo):
                if i not in _memo:
                    x = {"m": _bars[i][0], "px": _bars[i][4]}
                    _memo[i] = not _membership(D, _sym, _allb, x)
                return _memo[i]
            ok_idx = None
            for arm in MEASURE_ARMS:
                xs = crosses(bars, *arm)
                pos = [x for x in xs if x["sign"] == "+"]
                cyc = cycles(bars, xs, lambda x: ok_at(x["i"]))
                per[arm]["pos_all"].append(len(pos))
                per[arm]["pos_in"].append(sum(1 for x in pos if ok_at(x["i"])))
                if not cyc:
                    continue
                if ok_idx is None:
                    ok_idx = [i for i in range(len(bars)) if ok_at(i)]
                ctl = control_cycles(bars, xs, ok_idx, len(cyc), rng)
                per[arm]["cyc"].extend(cyc)
                per[arm]["ctl"].extend(ctl)
                per[arm]["pairs"][(sym, day)] = ([c["ret"] for c in cyc], [c["ret"] for c in ctl])
        miss_total += miss
        log(f"📅 {day}: مرشّحون {len(cands)} · شموعٌ تعذّرت {miss} · دوراتُ 8/15 حتى الآن {len(per[MEASURE_ARMS[0]]['cyc'])}")
    out = {"mode": "measure", "days": [days[0], days[-1], len(days)], "bad_days": bad_days, "bars_failed": miss_total, "arms": {}}
    for arm in MEASURE_ARMS:
        a = per[arm]
        s_arm, s_ctl = summarize(a["cyc"]), summarize(a["ctl"])
        boot = cluster_boot(a["pairs"]) if len(a["cyc"]) >= MIN_CYCLES else (None, None, None)
        verdict = "لا قياس" if len(a["cyc"]) < MIN_CYCLES else ("يتفوّق" if boot[1] is not None and boot[1] > 0 else "لا يتفوّق")
        out["arms"][f"{arm[0]}/{arm[1]}"] = {"arm": s_arm, "control": s_ctl, "boot": boot, "verdict": verdict,
                                              "pos_all_median": _median(a["pos_all"]), "pos_in_median": _median(a["pos_in"]),
                                              "symbol_days": len(a["pairs"])}
        f = lambda v: "—" if v is None else f"{v * 100:+.2f}%"                                  # noqa: E731
        log(f"📊 {arm[0]}/{arm[1]}{' (الحاكم)' if arm == MEASURE_ARMS[0] else ' (وصفًا)'}: دورات {s_arm['n']} على {len(a['pairs'])} رمز-يوم · "
            f"الوسيط {f(s_arm['median'])} · المتوسّط {f(s_arm['mean'])} · ‏+7% {s_arm['ge7'][0]} · ‏+20% {s_arm['ge20'][0]} · سالبة {s_arm['neg'][0]} · "
            f"أقصى ربح (وسيط) {f(s_arm['maxp_median'])} · المدّة (وسيط) {s_arm['dur_median']}د · خروجُ «الإغلاق» "
            f"{'—' if s_arm['close_share'] is None else round(s_arm['close_share'] * 100, 1)}%")
        log(f"   الضابط: الوسيط {f(s_ctl['median'])} · المتوسّط {f(s_ctl['mean'])} · ‏+20% {s_ctl['ge20'][0]} · سالبة {s_ctl['neg'][0]} · "
            f"التقاطعاتُ الإيجابيّة/رمز/يوم (وسيط) كلُّها {_median(a['pos_all'])} · داخل المجتمع {_median(a['pos_in'])}")
        log(f"   P4 الفرق (الذراع − الضابط) {f(boot[0])} · فاصل 95% [{f(boot[1])} ، {f(boot[2])}] ⟵ **{verdict}**")
    out["calls"], out["fails"] = net.calls, net.fails
    log("GCROSS_JSON " + json.dumps(out, ensure_ascii=False, sort_keys=True, default=str))
    return 4 if (bad_days or miss_total) else 0


# ── وضعُ التتبّع ─────────────────────────────────────────────────────────────────────────────────────────
def mode_trace(net, MC, day, sym, fast=FAST_N, slow=SLOW_N):
    """رمزٌ ويوم: كلُّ تقاطعٍ بسعره ووقته وعضويّته · ودوراتُه — تشخيصٌ لا قرار."""
    info = MC.session_info(day)
    by = net.minutes(sym, day, day)
    if by is None or not (by or {}).get(day):
        log(f"⛔ {sym} {day}: تعذّرت الدقائق")
        return 4
    D = V.Day(net, day, MC, replay=True)
    allb = by[day]
    bars = regular(allb, info["open_ny_min"], info["close_ny_min"])
    xs = crosses(bars, fast, slow)
    for x in xs:
        mem = _membership(D, sym, allb, x) if x["sign"] == "+" else []
        log(f"{x['sign']} {hm(x['m'])} ${x['px']:g} · EMA{fast} {x['ef']:.4g} · EMA{slow} {x['es']:.4g}"
            + ("" if x["sign"] == "-" else f" · المجتمع: {'داخل' if not mem else 'خارج ' + mem[0]}"))
    return 0


# ── الوضعُ الحيّ (B-⑧ · B-⑨ · B-⑩) ───────────────────────────────────────────────────────────────────────
class AMBars(V.WSShadow):
    """قناةُ AM بكود الظلّ نفسِه (الاتّصال · المصادقة · `AM.*`) ⟵ ويحفظ هنا الشمعةَ نفسَها لا لحظةَ وصولها وحدَها."""

    def __init__(self, key, **kw):
        super().__init__(key, **kw)
        self.bars = {}

    def handle(self, raw, now):
        super().handle(raw, now)
        try:
            msgs = json.loads(raw)
        except ValueError:
            return
        for m in msgs if isinstance(msgs, list) else [msgs]:
            if not isinstance(m, dict) or m.get("ev") != "AM":
                continue
            try:
                sym, s = str(m["sym"]).upper(), int(m["s"])
                bar = (float(m["o"]), float(m["h"]), float(m["l"]), float(m["c"]), float(m.get("v") or 0.0))
            except (KeyError, TypeError, ValueError):
                continue
            with self.lk:
                self.bars[(sym, s)] = (bar, now)

    def bar(self, sym, start_ms):
        with self.lk:
            return self.bars.get((str(sym).upper(), int(start_ms)))


def live_eval(bars, prev_open):
    """B-⑩ تقييمُ **دقيقة الحدّ وحدَها** (آخرُ شمعة): ⟵ التقاطعُ عندها أو None — والإيجابيُّ يُعاد وحدَه بلا دورةٍ مفتوحة والسلبيُّ بدورةٍ مفتوحة."""
    xs = crosses(bars)
    if not xs or xs[-1]["i"] != len(bars) - 1:
        return None
    x = xs[-1]
    if (x["sign"] == "+") == bool(prev_open):
        return None
    x["n"] = sum(1 for y in xs if y["sign"] == "+")
    return x


def ledger_row(day, sym, x, bars, cyc_open, lat, sent, reason, sha):
    """B-⑪ صفٌّ إلحاقيّ لكلّ تنبيه (ومعه نتيجةُ الدورة عند السلبيّ)."""
    i = x["i"]
    row = {"date": day, "sym": sym, "sign": x["sign"], "m": x["m"], "time_ny": hm(x["m"] + 1), "px": x["px"], "ef": x["ef"], "es": x["es"],
           "n": x.get("n"), "from_low": pct_from_low(bars, i), "vwap_side": vwap_side(bars, i), "lat": lat, "sent": sent, "reason": reason,
           "sha": sha, "def": f"EMA{FAST_N}/{SLOW_N}·1m"}
    if x["sign"] == "-" and cyc_open:
        e_px = cyc_open["px"]
        hi = max((b[2] for b in bars if cyc_open["m"] < b[0] <= x["m"]), default=x["px"])
        row.update({"entry_px": e_px, "entry_m": cyc_open["m"], "ret": x["px"] / e_px - 1.0, "maxp": hi / e_px - 1.0,
                    "dur": x["m"] - cyc_open["m"]})
    return row


AM_WAIT_S = 1.5                              # B-⑨ انتظارُ شمعة AM بعد الحدّ مرّةً لكلّ حدّ (وصولُها مقيسٌ ‏≈1.03ث) — engineering
FETCH_WORKERS = 16                           # جلبُ REST المتوازي لمن غابت شمعتُه — engineering (نمطُ الفيواب)


def lat_parts(t_b, t_ready, t_det, t_ver, t_sent):
    """B-⑧ مراحلُ التأخّر بالثواني من إغلاق الدقيقة (نقيّة): الشموع (AM أو REST) · المجتمع · تحقّقُ REST · الإرسال · والكلّيّ حتى الإرسال
    إن أُرسل وإلّا حتى القرار."""
    r = lambda x: None if x is None else round(x, 2)                       # noqa: E731
    end = t_sent if t_sent is not None else t_ver
    return {"bars_s": r(t_ready - t_b), "check_s": r(t_det - t_ready), "verify_s": r(t_ver - t_det),
            "send_s": None if t_sent is None else r(t_sent - t_ver), "total_s": r(end - t_b)}


def lat_line(lat):
    snd = "—" if lat.get("send_s") is None else f"{lat['send_s']}"
    return (f"تأخّر {lat['total_s']}ث (شموع {lat['bars_s']} · مجتمع {lat['check_s']} · تحقّق {lat['verify_s']} · إرسال {snd}"
            f" · جلبات {lat.get('polls')} · المصدر {lat.get('src')})")


def merge_bar(hist, m, bar):
    """يضمّ شمعةَ AM للدقيقة m إلى سجلّ الرمز (تحلّ محلّ نسختها إن وُجدت) ⟵ قائمةٌ مرتّبة."""
    return sorted([b for b in hist if b[0] != m] + [(m,) + tuple(bar)], key=lambda b: b[0])


def mode_live(net, MC, send=False, now_fn=time.time, sleep_fn=time.sleep, sender=None, saver=None, path=LEDGER, ws=None, until_mod=None):
    """الحلقةُ الحيّة: كلَّ حدّ دقيقة ⟵ شمعةُ الحدّ لكلّ مرشّح من AM (وإلّا REST متوازيًا) ⟵ التقاطعُ عند دقيقة الحدّ وحدَها ⟵ المجتمعُ
    للإيجابيّ ⟵ تحقّقُ REST ⟵ الإرسالُ (بـ`send` وحدَه) والسجلّ ⟵ ثمّ تحديثُ المرشِّح (لقطةٌ ⟵ `prefilter`) بعد التقييم كي لا يؤخّره.
    ⟵ 0 · 4 لمرجعٍ ناقص. **صامتٌ ما لم يُضبط `GC_SEND=1`** (والـworkflow بلا سرّ تلغرام)."""
    from concurrent.futures import ThreadPoolExecutor
    day = V._today_ny(dt.datetime.fromtimestamp(now_fn(), tz=NY))
    info = MC.session_info(day)
    if not V3.is_session(day, MC.session_info):
        log(f"🗓️ {day} ليس جلسة — لا عمل")
        return 0
    op, cl = info["open_ny_min"], info["close_ny_min"]
    end = min(cl, until_mod or cl)
    D = V.Day(net, day, MC)
    if not D.ok:
        log(f"⛔ مرجعٌ ناقص {D.why}")
        return 4
    log(f"📈✖️ «التقاطع الذهبي» حيّ · {day} · EMA{FAST_N}/{SLOW_N} · {'يُرسل' if send else 'صامت'} · AM {'مُشعَل' if ws else 'غائب ⟵ REST وحدَه'}")
    cands, hist, open_cyc, seen = set(), {}, {}, set()
    stats = {"rest_fail": 0, "am_hit": 0, "rest": 0, "mismatch": 0, "unverified": 0, "boundaries": 0}
    snap = net.snapshot()
    if snap:
        cands |= V.prefilter(snap, D.prev_adj_pf, D.types)

    def rest_day(sym):
        by = net.minutes(sym, day, day)
        return None if by is None else ((by or {}).get(day) or [])
    with ThreadPoolExecutor(FETCH_WORKERS) as pool:
        while True:
            now = now_fn()
            b_mod = int((now - V3.ny_ts(day, 0)) // 60) + 1                    # الحدُّ القادم (نهايةُ الدقيقة الجارية)
            if b_mod > end:
                break
            t_b = V3.ny_ts(day, b_mod)
            if t_b + (AM_WAIT_S if ws is not None else 0.0) > now:
                sleep_fn(t_b + (AM_WAIT_S if ws is not None else 0.0) - now)
            if b_mod <= op:
                continue
            stats["boundaries"] += 1
            m_last, start_ms = b_mod - 1, int(V3.ny_ts(day, b_mod - 1) * 1000)
            ready, need = {}, []
            for sym in sorted(cands):
                got = ws.bar(sym, start_ms) if ws is not None else None
                if got is not None and sym in hist:
                    hist[sym] = merge_bar(hist[sym], m_last, got[0])
                    ready[sym] = (now_fn(), "AM")
                    stats["am_hit"] += 1
                else:
                    need.append(sym)
            for sym, rows in zip(need, pool.map(rest_day, need)):
                if rows is None:
                    stats["rest_fail"] += 1
                    continue
                hist[sym] = rows
                ready[sym] = (now_fn(), "REST")
                stats["rest"] += 1
            for sym in sorted(ready):
                t_ready, src = ready[sym]
                allb = [b for b in hist[sym] if b[0] <= m_last]
                bars = regular(allb, op, cl)
                if not bars or bars[-1][0] != m_last:
                    continue                                                 # B-⑩ لا شمعةَ لدقيقة الحدّ ⟵ لا تقييم (البائتةُ لا تُقيَّم)
                x = live_eval(bars, open_cyc.get(sym))
                if x is None:
                    continue
                key = (day, sym, x["m"], x["sign"])
                if key in seen:
                    continue
                seen.add(key)
                if x["sign"] == "+" and _membership(D, sym, allb, x):
                    continue
                t_det = now_fn()
                verified, polls = None, 0                                     # B-⑨ تحقّقُ REST بالتقاطع نفسِه في الدقيقة نفسِها
                for step in POLL_STEPS_S:
                    polls += 1
                    rows = rest_day(sym)
                    rb = [b for b in regular(rows or [], op, cl) if b[0] <= m_last]
                    if rb and rb[-1][0] == m_last:
                        hist[sym] = rows
                        rx = live_eval(rb, open_cyc.get(sym))
                        verified = rx is not None and rx["sign"] == x["sign"] and rx["m"] == x["m"]
                        if verified:
                            x, bars = rx, rb
                        break
                    wait = t_b + step - now_fn()
                    if wait > 0:
                        sleep_fn(wait)
                t_ver = now_fn()
                reason = None if verified else ("خلاف AM/REST" if verified is False else "REST لم ينشر الدقيقة")
                stats["mismatch"] += int(verified is False)
                stats["unverified"] += int(verified is None)
                row = ledger_row(day, sym, x, bars, open_cyc.get(sym), None, False, reason, V._sha())
                t_sent = None
                if verified and send:
                    ok, t_sent = V._send_measured(sender, build_message(row), now_fn)
                    row["sent"] = bool(ok)
                lat = lat_parts(t_b, t_ready, t_det, t_ver, t_sent)
                lat.update({"polls": polls, "src": src})
                row["lat"] = lat
                if verified:
                    if x["sign"] == "+":
                        open_cyc[sym] = {"m": x["m"], "px": x["px"]}
                    else:
                        open_cyc.pop(sym, None)
                if lat["total_s"] is not None and lat["total_s"] > V.LAT_WARN_S:
                    log(f"⏱️ تأخّرٌ فوق {V.LAT_WARN_S}ث: ${sym} {x['sign']} · {lat_line(lat)}")
                V.append_ledger(row, path)
                try:
                    (saver or V._bot().git_save)([path])
                except Exception as e:                                       # noqa: BLE001
                    log(f"⚠️ دفعُ السجلّ تعذّر ({type(e).__name__}) — الصفُّ محفوظٌ محلّيًّا ويُدفع مع التالي")
                log(f"{'✅' if x['sign'] == '+' else '❌'} ${sym} {hm(x['m'] + 1)} ${x['px']:g} · {'تحقّق' if verified else reason} · "
                    f"{'أُرسل' if row['sent'] else 'لم يُرسَل'} · {lat_line(lat)}")
            snap = net.snapshot()                                            # المرشِّحُ بعد التقييم (لا يؤخّره) ويتراكم كالفيواب
            if snap:
                cands |= V.prefilter(snap, D.prev_adj_pf, D.types)
    log(f"🩺 التغطية: حدود {stats['boundaries']} · مرشّحون {len(cands)} · شموعُ AM {stats['am_hit']} · REST {stats['rest']} · REST تعذّر "
        f"{stats['rest_fail']} · خلافُ AM/REST {stats['mismatch']} · لم يُتحقَّق {stats['unverified']} · دوراتٌ مفتوحةٌ عند النهاية "
        f"{len(open_cyc)} (لا يُرسَل خروجٌ لم يقع — {UNSPEC})")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--mode", default="accept", choices=("accept", "measure", "trace", "live"))
    p.add_argument("--end", default="")
    p.add_argument("--days", type=int, default=N_SESSIONS)
    p.add_argument("--date", default="2026-11-04")
    p.add_argument("--sym", default="OMH")
    p.add_argument("--until", default="")
    a = p.parse_args(argv)
    import market_calendar as MC
    uni = (os.environ.get(UNIVERSE_ENV) or "vwap").strip()
    if uni not in UNIVERSE_OK or uni != "vwap":
        log(f"⛔ {UNIVERSE_ENV}={uni!r}: المبنيُّ `vwap` وحدَه · و`top_gainers` بديلٌ للمالك لم يُبنَ بعد ({UNSPEC})")
        return 2
    if (os.environ.get(EXT_ENV) or "0").strip() != "0":
        log(f"⛔ {EXT_ENV}: الجلسةُ النظاميّة وحدَها (B-①) · والممتدّة {UNSPEC}")
        return 2
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    ua = (os.environ.get("SEC_CONTACT") or "").strip()
    if not key or not ua:
        log("⛔ مفتاحُ Polygon أو SEC_CONTACT غائب — لا عمل (يُعلَن ولا يُكتَم)")
        return 2
    net = V.Net(key, ua)
    if a.mode == "accept":
        return mode_accept(net, MC)
    if a.mode == "trace":
        return mode_trace(net, MC, a.date, a.sym.upper())
    if a.mode == "measure":
        end = a.end
        if not end:
            d = dt.date.fromisoformat(V._today_ny()) - dt.timedelta(1)
            while not V3.is_session(d.isoformat(), MC.session_info):
                d -= dt.timedelta(1)
            end = d.isoformat()
        return mode_measure(net, MC, end, a.days)
    until = None
    if a.until:
        hh, mm = a.until.split(":")
        until = int(hh) * 60 + int(mm)
    send = os.environ.get(SEND_ENV) == "1"
    ws = AMBars(key)
    ws.start(time.time() + 7 * 3600)
    if not send:                                                         # صامت ⟵ سجلٌّ محلّيٌّ لا يُدفع (التجربةُ قبل «فعّل الذهبي»)
        return mode_live(net, MC, send=False, ws=ws, until_mod=until, path=SILENT_LEDGER, saver=lambda _paths: None)
    return mode_live(net, MC, send=True, ws=ws, until_mod=until)


if __name__ == "__main__":
    sys.exit(main())
