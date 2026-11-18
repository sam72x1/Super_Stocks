#!/usr/bin/env python3
"""📏 `T-GATECAL` — معايرةُ شروط الأدوات (العقد `T_GATECAL_prereg.md` · أمرُ المالك 2026-11-18) — قراءةٌ فقط.

  prep --tool T                         — قائمةُ التقسيمات العكسيّة (Polygon) والجلسات ⟵ `out/gatecal_prep_T.json.gz`
  feat <k> --tool T --from A --to B     — إعادةُ حساب الأداة (بدوالّها بالاسم) لكلّ (رمز، جلسة) ⟵ القيمُ الخامّ لكلّ شرط ‏+ الصفقة والوسم
  count --tool T --dir D                — §⑤ العدُّ أوّلًا (حلقات · منفجرون) ومطابقةُ السجلّ
  select --tool T --dir D               — §③-§④ منحنياتُ العتبة على جزء الاختيار ⟵ سطرُ `GATECAL_FREEZE`
  confirm --tool T --dir D              — §④ التأكيدُ مرّةً واحدة (خروج 9 بلا تثبيتٍ ببصمته · 7 إن صدر)
🔒 لا تلغرام · لا كتابةَ حالة · والإرخاءُ المؤقّت لـ`CONFIG` يُستعاد في `finally` · ولا تغييرَ عتبةٍ هنا (اقتراحٌ للمالك وحدَه).
"""
import bisect
import datetime as dt
import glob
import gzip
import hashlib
import json
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CONTRACT = os.path.join(HERE, "T_GATECAL_prereg.md")
CONTRACT_SHA = "2bc8b9eac39cdf6cb07c6536753107e9c6c859b0d1ee73ddced41ac78adb3ba0"
OUT = os.path.join(HERE, "out")
NSHARDS = 40
WIN = 20                       # نافذةُ الوسم والصفقة (العقد §②)
COST = 0.018                   # §④
NCTRL = 5                      # §④
SEED = 20261118
BOOT = 10_000
MATCH_FLOOR = 0.80             # §② مطابقةُ السجلّ
SUFF = {"loose_eps": 100, "loose_x": 30, "cur_eps": 20}          # §⑤
MIN_ADDED = 5                  # §④
SEL_FRAC = 0.60                # §④ (فترةُ البوت)
HIST_SEL = ("2023", "2024")    # §④ (التاريخ)
HIST_CONF = ("2025", "2026")
BARS_FROM = "2022-01-03"
RC_OK, RC_KEY, RC_POP, RC_ONCE, RC_BLIND, RC_FREEZE, RC_CONTRACT = 0, 2, 5, 7, 8, 9, 11

# ══ الأدوات (ملحقُ كلّ أداةٍ يثبّت سلّمَها قبل رقمها الأوّل) ═══════════════════════════════════════════════
TOOLS = {
    "split_hunter": {
        "addendum": "T_GATECAL_A1_split_hunter.md", "addendum_sha": "3962194d1c3ed8fef53c6ac9979addd77f1d53cb0e42814c52f1fe32589eedf3",
        "built": "2026-07-24", "ledger_hunter": ("split",),
        "current": {"rose": 20.0, "band_low": 0.70, "band_hi": 0.25, "hold": 3, "shares": 2_000_000, "cliff": 30.0, "lookback": 120, "price_max": 10.0},
        "ladders": {"rose": [15.0, 20.0, 23.0, 25.0, 30.0, 40.0], "band_low": [0.80, 0.75, 0.70, 0.65, 0.60], "band_hi": [0.15, 0.25, 0.35, 0.50],
                    "hold": [5, 4, 3, 2], "shares": [1e6, 2e6, 3e6, 5e6, 10e6], "cliff": [50.0, 40.0, 30.0, 25.0, 20.0],
                    "lookback": [60, 90, 120, 180, 250], "price_max": [5.0, 7.5, 10.0, 15.0, 20.0]},
        # اتّجاهُ الإرخاء: +1 = القيمةُ الأكبر أرخى · −1 = الأصغر أرخى
        "loose_dir": {"rose": 1, "band_low": -1, "band_hi": 1, "hold": -1, "shares": 1, "cliff": -1, "lookback": 1, "price_max": 1},
        "label": {"rose": "«لم يصعد بعد الحدث» % (فيصل: 20)", "band_low": "أدنى النطاق حول القمّة÷2 (×)", "band_hi": "أعلى النطاق فوق القمّة÷2 (+)",
                  "hold": "حافظ عددَ جلسات (فيصل: 3)", "shares": "الأسهمُ القائمة — وكيلُ الفلوت (فيصل: دون 2م)", "cliff": "كليفُ هبوط يوم %",
                  "lookback": "عمرُ الحدث بالأيّام", "price_max": "سقفُ السعر $"},
    },
}
TOOLS["split_filter"] = {
    "addendum": "T_GATECAL_A2_split_filter.md", "addendum_sha": "b918d13bf4001246c9959afc2ae3107f8a48658dd61cbe83f31f5e4721fe6187",
    "built": "2026-08-21", "ledger_hunter": ("split_filter", "split_filter_g2soft"),
    "current": {"rose": 20.0, "band_low": 0.70, "band_hi": 0.25, "bounce": 10.0, "tol": 0.015, "zone": 0.0},
    "ladders": {"rose": [15.0, 20.0, 23.0, 25.0, 30.0, 40.0], "band_low": [0.80, 0.75, 0.70, 0.65, 0.60], "band_hi": [0.15, 0.25, 0.35, 0.50],
                "bounce": [15.0, 10.0, 7.5, 5.0], "tol": [0.01, 0.015, 0.025, 0.04], "zone": [0.0, 0.03, 0.05, 0.10]},
    "loose_dir": {"rose": 1, "band_low": -1, "band_hi": 1, "bounce": -1, "tol": 1, "zone": 1},
    "label": {"rose": "G1 «ما صعد أوّل التقسيم» % (فيصل: 20)", "band_low": "أدنى النطاق حول القمّة÷2 (×)", "band_hi": "أعلى النطاق فوق القمّة÷2 (+)",
              "bounce": "الارتدادُ من القاع % (فيصل: 10)", "tol": "تسامحُ ثبات الدعم الثاني (هندسيّ)", "zone": "فوق أعلى الطلبات % (منطقةُ الدخول)"},
}
# الأداة 3 «الجاهزية وتحت المتابعة» (الملحق 3): كلُّ شرطٍ = مفتاحُ `CONFIG` واحد في `analyze_ticker` الإنتاجيّ · والحاليُّ = النافذُ بعد `apply_faisal_only`
_RD = {"price": 0.4000000059604645, "floor": 71.72029570041596, "ceil": 99.94998260261913, "spike": 78.27380827782238,
       "dvol": 14314.770054221153, "gapdist": 1134.782634295228}
TOOLS["ready"] = {
    "addendum": "T_GATECAL_A3_ready.md", "addendum_sha": "8d89e67f520fb7943f0108cc5badb34028f9d9fa8bfc8088d899b1bac7711248",
    "built": "2026-08-16", "ledger_hunter": (), "bars_from": "2020-10-01",
    "addendum2": "T_GATECAL_A3b_ready_split.md", "addendum2_sha": "065d5924a8a608441016c69f69f06e8139df55851dbb4d32513e6be11e0659aa",
    "era": {"sel_from": "2026-08-16", "conf": ("2024-01-02", "2025-12-31")},     # الملحق 3-ب: الاختيارُ على فترة البوت والتأكيدُ على سنتين لم تُرَيا
    "current": {"base": 120.0, "rr": 0.5, "price": _RD["price"], "spike": _RD["spike"], "ceil": _RD["ceil"], "floor": _RD["floor"],
                "dvol": _RD["dvol"], "chase": 35.0, "gapdist": _RD["gapdist"]},
    "ladders": {"base": [80.0, 100.0, 120.0, 150.0, 200.0, 300.0, 475.0], "rr": [0.75, 0.5, 0.4, 0.3, 0.2, 0.0],
                "price": [0.5, _RD["price"], 0.3, 0.2], "spike": [100.0, _RD["spike"], 70.0, 60.0, 50.0],
                "ceil": [99.9, _RD["ceil"], 99.99, 100.0], "floor": [80.0, _RD["floor"], 65.0, 60.0, 50.0],
                "dvol": [25000.0, _RD["dvol"], 10000.0, 5000.0, 0.0], "chase": [25.0, 35.0, 50.0, 75.0, 100.0],
                "gapdist": [_RD["gapdist"], 2000.0, 5000.0]},
    "loose_dir": {"base": 1, "rr": -1, "price": -1, "spike": -1, "ceil": 1, "floor": -1, "dvol": -1, "chase": 1, "gapdist": 1},
    "label": {"base": "M4 عرضُ القاعدة % (قرارُ المالك 120)", "rr": "العائد/المخاطرة للهدف الأوّل (هندسيّ)", "price": "M1 أدنى سعر $ (ظرفُ الكاتالوج)",
              "spike": "M3 الانفجارُ السابق % (ظرف)", "ceil": "M2 سقفُ الهبوط من القمّة % (ظرف)", "floor": "M2 أرضيّةُ الهبوط % (ظرف)",
              "dvol": "M5 السيولةُ الدولاريّة $ (ظرف)", "chase": "M4ب صعودُ 5 جلسات % (قرارُ المالك 35)", "gapdist": "M9 بُعدُ الفجوة % (ظرف)"},
}
RD_KEY = {"base": "BASE_RANGE_MAX_PCT", "rr": "MIN_RR_T1", "price": "MIN_PRICE", "spike": "PRIOR_SPIKE_FLOOR", "ceil": "MAX_DROP_PCT",
          "floor": "MIN_DROP_FLOOR", "dvol": "MIN_DOLLAR_VOL", "chase": "RECENT_RISE_BLOCK_PCT", "gapdist": "GAP_ABOVE_MAX_DIST_PCT"}
RD_VAL = {"base": "base_range", "rr": "rr", "price": "price", "spike": "best_spike", "ceil": "drop_pct", "floor": "drop_pct",
          "dvol": "dollar_vol", "chase": "gain5", "gapdist": "gap_above_dist"}
RD_NW_FROM = "2026-08-16"                      # صفوفُ «تحت المتابعة» (ناقصٌ واحد فأقلّ) تُحفظ من يوم بُنيت القائمة — جدولُ الجدار الفعليّ
RD_HISTORY_DAYS, RD_STALE_DAYS = 800, 7        # نافذةُ الإنتاج (`T-REBUILD` §③) · ولا شمعةَ في 7 أيّام ⟵ خارج كون يومه
SF_LOOKBACK, SF_PRICE = 120, (1.0, 10.0)        # نافذةُ الحدث وحدودُ السعر في فلتر التقسيم — ثابتةٌ عند النافذ (الملحق 2)


def log(m=""):
    print(m, flush=True)


def sha_of(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def contract_ok(tool):
    try:
        t = TOOLS[tool]
        return (sha_of(CONTRACT) == CONTRACT_SHA and sha_of(os.path.join(HERE, t["addendum"])) == t["addendum_sha"]
                and ("addendum2" not in t or sha_of(os.path.join(HERE, t["addendum2"])) == t["addendum2_sha"]))
    except (OSError, KeyError):
        return False


def freeze_path(tool):
    return os.path.join(HERE, "data", f"{tool}_freeze.json")


def result_path(tool):
    return os.path.join(HERE, f"T_GATECAL_{tool}_RESULT.md")


FREEZE_SHA = {"ready": "b063303cb5457bce6e64e5f962372d8ba38683ebe483c44e5e6f8de1632c8a7b"}                # {أداة: بصمةُ ملفّ تثبيتها} — يُملأ في PR التثبيت قبل فتح جزء التأكيد


def freeze_ok(tool):
    try:
        return bool(FREEZE_SHA.get(tool)) and sha_of(freeze_path(tool)) == FREEZE_SHA[tool]
    except OSError:
        return False


# ══ نقيّات مشتركة ══════════════════════════════════════════════════════════════════════════════════════
def fwd_factor(splits, day):
    """∏(to/from) للتقسيمات المنفّذة بعد day ⟵ السعرُ المسوّى × الحاصل = سعرُ يومِه الخامّ (لا تقسيمَ لاحقًا يُقرأ)."""
    f = 1.0
    for x, r in splits or []:
        if x > day and r and r > 0:
            f *= float(r)
    return f


def exploded_label(days, H, C, i, pct, split_days, win=WIN):
    """§② «المنفجر» (`EXPLODED_PCT` · حصرًا) في [D+1، D+win] مع **استبعاد جلسة تنفيذ أيّ تقسيمٍ والتي تليها** ⟵ (bool، أقصى صعود) · None لنافذةٍ ناقصة."""
    if i + win >= len(days) or C[i] <= 0:
        return None, None
    bad = set()
    for j in range(i + 1, i + 1 + win):
        if days[j] in split_days:
            bad.add(j)
            bad.add(j + 1)
    hs = [H[j] for j in range(i + 1, i + 1 + win) if j not in bad]
    if not hs:
        return None, None
    mx = max(hs) / C[i] - 1.0
    return bool(mx * 100.0 > pct), round(mx, 6)


def trade_return(O, H, C, i, win=WIN, cost=COST):
    """§④ صفقةُ الحلقة بشموعٍ يوميّة: دخولٌ افتتاحُ D+1 · نصفٌ عند ‏+50% والباقي عند ‏+100% إن بلغهما أعلى جلسة · وإلّا إغلاقُ الجلسة win · بعد الكلفة."""
    if i + win >= len(C):
        return None
    e = O[i + 1]
    if not e or e <= 0:
        return None
    half = rest = None
    for j in range(i + 1, i + 1 + win):
        if half is None and H[j] >= 1.5 * e:
            half = 0.5
        if half is not None and H[j] >= 2.0 * e:
            rest = 1.0
            break
    last = C[i + win] / e - 1.0
    r = 0.5 * (half if half is not None else last) + 0.5 * (rest if rest is not None else last)
    return round(r - cost, 6)


def sf_bottom(v, P):
    """فلترُ التقسيم: قاعُ الطلبات عند P — قاعُ التسلسل المكتمل · وإلّا (نقصٌ لين) قاعُ النافذة لمن ارتدّ `bounce`% فأكثر · وإلّا None."""
    sq = (v.get("seqs") or {}).get(f"{P['bounce']:g}|{P['tol']:g}")
    if sq and sq.get("ok"):
        return float(sq["bottom"])
    g = v.get("g2") or {}
    if g.get("low") and g.get("bounce") is not None and float(g["bounce"]) >= P["bounce"]:
        return float(g["low"])
    return None


def sf_why(v, P):
    """فلترُ التقسيم: الشروطُ الساقطة بترتيب `scan_split_filter` (حدث/سعر ثابتان · نطاق · G1 · التسلسل · منطقةُ الطلبات · القروب)."""
    out = []
    if v["age"] > SF_LOOKBACK or not (SF_PRICE[0] <= v["price"] <= SF_PRICE[1]):
        out.append("event_price")
    if not (P["band_low"] <= v["tail"][-1] <= 1.0 + P["band_hi"]):
        out.append("band")
    if v["rose"] is not None and v["rose"] > P["rose"]:
        out.append("rose")
    bot = sf_bottom(v, P)
    if bot is None:
        out.append("seq")
    elif v["price"] > (bot + v["step"] * v["nlad"]) * (1.0 + P["zone"]):
        out.append("zone")
    if v.get("pump"):
        out.append("pump")
    return out


def rd_passes(v, P):
    """الجاهزيّة: صفُّها يحمل نتيجةَ `analyze_ticker` الإنتاجيّ لكلّ قيمةِ سلّمٍ بشرطٍ واحد (`p`) وبإرخاء الكلّ (`all`) ⟵ P = الحاليُّ · أو يختلف
    عنه في شرطٍ واحد · أو أرخى السلّم في الكلّ — وغيرُ ذلك لم يُحسب فيُرفع (لا تخمين)."""
    t = TOOLS["ready"]
    diff = [c for c in t["current"] if P[c] != t["current"][c]]
    if not diff:
        return bool(v["p"]["base"][t["ladders"]["base"].index(t["current"]["base"])])
    if len(diff) == 1:
        return bool(v["p"][diff[0]][t["ladders"][diff[0]].index(P[diff[0]])])
    if all(P[c] == loosest("ready", c) for c in t["current"]):
        return bool(v["all"])
    raise ValueError("توليفةٌ لم تُحسب في إعادة الجاهزيّة")


def passes(v, P):
    """هل يعبر الصفُّ بالأرقام P؟ — صفُّ فلتر التقسيم (يحمل `seqs`) بترتيب فلتره · وصفُّ الصيّاد بترتيب الصيّاد: (ترتيبُ الصيّاد نفسُه: حدث · سعر · كليف · قرب القمّة÷2 · حافظ · لم يصعد · فلوت · قروب)."""
    if "seqs" in v:
        return not sf_why(v, P)
    if "p" in v:
        return rd_passes(v, P)
    if v["age"] > P["lookback"] or not (1.0 <= v["price"] <= P["price_max"]):
        return False
    cl = v["cliff"].get(str(int(P["lookback"])))
    if cl is None or cl > -P["cliff"] / 100.0:
        return False
    lo, hi = P["band_low"], 1.0 + P["band_hi"]
    t = v["tail"]
    n = int(P["hold"])
    if not (lo <= t[-1] <= hi) or len(t) < n or not all(lo <= x <= hi for x in t[-n:]):
        return False
    if v["rose"] is not None and v["rose"] > P["rose"]:
        return False
    if v.get("shares") is None or not (v["shares"] < P["shares"]):
        return False
    return not v.get("pump")


def fails_only(v, P, cond):
    """هل يرفضه `cond` وحدَه؟ (يعبر بإرخاء هذا الشرط إلى ما لا نهاية ولا يعبر بـP)."""
    if passes(v, P):
        return False
    Q = dict(P)
    if "p" in v:                                    # الجاهزيّة: «وحدَه» = يعبر بأرخى سلّم هذا الشرط والبقيّةُ عند الحاليّ
        Q[cond] = loosest("ready", cond)
        return passes(v, Q)
    if "seqs" in v:                                 # فلترُ التقسيم: الارتدادُ والتسامحُ يُرخيان إلى أرخى سلّمهما (مفاتيحُ التسلسل المحسوبة)
        Q[cond] = {"rose": 1e9, "band_low": 0.0, "band_hi": 1e9, "bounce": loosest("split_filter", "bounce"),
                   "tol": loosest("split_filter", "tol"), "zone": 1e9}[cond]
        return passes(v, Q)
    Q[cond] = {"rose": 1e9, "band_low": 0.0, "band_hi": 1e9, "hold": 1, "shares": 1e18, "cliff": -1e9, "lookback": 10**6, "price_max": 1e9}[cond]
    if cond == "lookback":
        return False                                # العمرُ يغيّر نافذةَ الكليف ⟵ لا يُحسب «وحدَه» خارج سلّمه
    return passes(v, Q)


def cond_value(v, cond, P):
    """قيمةُ الشرط في الصفّ (لتوزيعه وهامشه)."""
    if "p" in v:
        return (v.get("vals") or {}).get(RD_VAL[cond])
    if cond == "rose":
        return v["rose"]
    if "seqs" in v:
        if cond == "band_low":
            return v["tail"][-1]
        if cond == "band_hi":
            return v["tail"][-1] - 1.0
        if cond == "bounce":
            return (v.get("g2") or {}).get("bounce")
        if cond == "zone":
            bot = sf_bottom(v, P)
            return None if bot is None else v["price"] / (bot + v["step"] * v["nlad"]) - 1.0
        return None
    if cond == "band_low":
        return min(v["tail"][-int(P["hold"]):]) if len(v["tail"]) >= int(P["hold"]) else None
    if cond == "band_hi":
        return (max(v["tail"][-int(P["hold"]):]) - 1.0) if len(v["tail"]) >= int(P["hold"]) else None
    if cond == "hold":
        lo, hi, n = P["band_low"], 1.0 + P["band_hi"], 0
        for x in reversed(v["tail"]):
            if lo <= x <= hi:
                n += 1
            else:
                break
        return n
    if cond == "shares":
        return v.get("shares")
    if cond == "cliff":
        c = v["cliff"].get(str(int(P["lookback"])))
        return None if c is None else -c * 100.0
    if cond == "lookback":
        return v["age"]
    if cond == "price_max":
        return v["price"]
    return None


def episodes(rows_by_sym, sessions_ix, P_loose, P, win=WIN):
    """§② الحلقات: نافذتُها تبدأ بأوّل جلسةٍ تعبر عند `P_loose` (ولا حلقةَ جديدة قبل win جلسة) · ودخولُها عند `P` = أوّلُ جلسةٍ في نافذتها تعبر عند P.
    ⟵ [(رمز، يومُ بدء النافذة، صفُّ الدخول عند P أو None)]"""
    out = []
    for sym in sorted(rows_by_sym):
        rs = rows_by_sym[sym]                       # مرتَّبةٌ باليوم
        start_ix, cur = None, None
        for r in rs:
            ix = sessions_ix[r["d"]]
            if start_ix is not None and ix - start_ix < win:
                if cur[2] is None and passes(r["v"], P):
                    cur[2] = r
                continue
            if passes(r["v"], P_loose):
                start_ix = ix
                cur = [sym, r["d"], r if passes(r["v"], P) else None]
                out.append(cur)
    return [tuple(x) for x in out]


def quartiles(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None

    def q(p):
        k = (len(xs) - 1) * p
        a, b = int(math.floor(k)), int(math.ceil(k))
        return xs[a] + (xs[b] - xs[a]) * (k - a)
    return [round(q(0.25), 4), round(q(0.5), 4), round(q(0.75), 4), len(xs)]


def pick_controls(pool, sym, seed_key, n=NCTRL):
    """§④ خمسةُ ضوابطَ حتميّةٌ بالبذرة من رموز العُشير نفسِه في الجلسة (غيرَ الرمز) — pool = [(رمز، عائدُ صفقته)] مرتَّبة."""
    cand = [(s, r) for s, r in pool if s != sym and r is not None]
    if not cand:
        return []
    rnd = random.Random(f"{SEED}|{seed_key}")
    return rnd.sample(cand, min(n, len(cand)))


def deciles(pairs):
    """[(رمز، عائد5)] ⟵ {رمز: عُشير 0-9} بالترتيب (تعادلٌ بالرمز)."""
    xs = sorted(pairs, key=lambda t: (t[1], t[0]))
    n = len(xs)
    return {s: min(9, int(10 * k / n)) for k, (s, _r) in enumerate(xs)} if n else {}


def boot_diff_mean(a, b, seed=SEED, B=BOOT):
    """فاصلُ 95% لفرق متوسّطَي مجموعتين ([(رمز، قيمة)]) ببوتستراب عنقوديّ بالرمز داخل كلٍّ — وصفٌ (§④)."""
    import numpy as np

    def draws(pairs, sd):
        per = {}
        for s, v in pairs:
            p = per.setdefault(s, [0.0, 0])
            p[0] += v
            p[1] += 1
        if not per:
            return None
        sums = np.array([per[s][0] for s in sorted(per)])
        cnts = np.array([per[s][1] for s in sorted(per)])
        idx = np.random.default_rng(sd).integers(0, len(sums), size=(B, len(sums)))
        return sums[idx].sum(axis=1) / cnts[idx].sum(axis=1)
    da, db = draws(a, seed), draws(b, seed + 1)
    if da is None or db is None:
        return None
    d = np.sort(da - db)
    return [float(d[int(0.025 * B)]), float(d[int(0.975 * B) - 1])]


# ══ التجميع: منحنى شرطٍ واحد ══════════════════════════════════════════════════════════════════════════
def loosest(tool, cond):
    t = TOOLS[tool]
    lad = t["ladders"][cond]
    return max(lad) if t["loose_dir"][cond] > 0 else min(lad)


def with_excess(eps, ctrl_pool):
    """لكلّ حلقةٍ داخلة: الفائضُ = عائدُها − متوسّطُ ضوابطها (None إن غاب عائدُها أو ضوابطُها)."""
    out = []
    for sym, d0, row in eps:
        if row is None:
            continue
        r = row.get("r")
        cs = pick_controls(ctrl_pool.get((row["d"], row.get("dec")), []), sym, f"{sym}|{row['d']}")
        e = (r - sum(c for _s, c in cs) / len(cs)) if (r is not None and cs) else None
        out.append({"sym": sym, "d": row["d"], "x": row.get("x"), "r": r, "e": e})
    return out


def curve(tool, cond, rows_by_sym, sessions_ix, ctrl_pool, months):
    """§③ منحنى شرطٍ واحد ⟵ {قيمة: إحصاءات} ‏+ توزيعُ قيمته ‏+ المرفوضون به وحدَه بهامشهم."""
    t = TOOLS[tool]
    cur = dict(t["current"])
    PL = dict(cur)
    PL[cond] = loosest(tool, cond)
    pts = {}
    for val in t["ladders"][cond]:
        P = dict(cur)
        P[cond] = val
        ent = with_excess(episodes(rows_by_sym, sessions_ix, PL, P), ctrl_pool)
        lab = [z for z in ent if z["x"] is not None]
        nx = sum(1 for z in lab if z["x"])
        es = [z["e"] for z in ent if z["e"] is not None]
        rs_ = [z["r"] for z in ent if z["r"] is not None]
        pts[val] = {"n": len(ent), "n_lab": len(lab), "x": nx, "nonx": len(lab) - nx, "rate": (nx / len(lab)) if lab else None,
                    "per_month": (len(ent) / months) if months else None, "e_mean": (sum(es) / len(es)) if es else None, "n_e": len(es),
                    "r_mean": (sum(rs_) / len(rs_)) if rs_ else None, "ent": ent}
    # التوزيعُ والهامش: حلقاتُ النافذة عند الأرخى — صفُّ بدء النافذة
    PLs = episodes(rows_by_sym, sessions_ix, PL, PL)
    vx, vn, only = [], [], {"1": 0, "5": 0, "10": 0, "all": 0}
    for _sym, _d0, row in PLs:
        if row is None or row.get("x") is None:
            continue
        cv = cond_value(row["v"], cond, cur)
        (vx if row["x"] else vn).append(cv)
        if row["x"] and fails_only(row["v"], cur, cond) and cv is not None and cur[cond]:
            m = abs(cv - cur[cond]) / abs(cur[cond]) * 100.0
            only["all"] += 1
            for k in ("1", "5", "10"):
                if m <= float(k):
                    only[k] += 1
    return {"points": pts, "q_x": quartiles(vx), "q_nonx": quartiles(vn), "only": only}


def propose(tool, cond, pts):
    """§④ قاعدةُ الاقتراح: **أرخى** قيمةٍ تُبقي نسبةَ الانفجار ومتوسّطَ الفائض غيرَ أدنى من الحاليّ وتُدخل `MIN_ADDED` حلقةً إضافيّة فأكثر · وإلّا None."""
    t = TOOLS[tool]
    cur = t["current"][cond]
    base = pts.get(cur)
    if not base or base["rate"] is None or base["e_mean"] is None:
        return None
    lad = sorted(t["ladders"][cond], key=lambda v: -v * t["loose_dir"][cond])      # الأرخى أوّلًا
    for v in lad:
        if v == cur or (v - cur) * t["loose_dir"][cond] <= 0:
            continue
        p = pts[v]
        if p["rate"] is None or p["e_mean"] is None:
            continue
        if p["rate"] >= base["rate"] and p["e_mean"] >= base["e_mean"] and p["n"] - base["n"] >= MIN_ADDED:
            return v
    return None


def confirm_one(tool, cond, val, pts):
    """§④ حكمُ التأكيد لشرطٍ مثبَّت ⟵ (الحكم، تفصيل)."""
    cur = TOOLS[tool]["current"][cond]
    a, b = pts.get(cur), pts.get(val)
    if not a or not b or a["rate"] is None or b["rate"] is None or a["e_mean"] is None or b["e_mean"] is None:
        return "يبقى الرقم (لا قياس)", {}
    added = b["n"] - a["n"]
    ok = b["rate"] >= a["rate"] and b["e_mean"] >= a["e_mean"] and added >= MIN_ADDED
    cur_keys = {(z["sym"], z["d"]) for z in a["ent"]}
    add_e = [(z["sym"], z["e"]) for z in b["ent"] if (z["sym"], z["d"]) not in cur_keys and z["e"] is not None]
    cur_e = [(z["sym"], z["e"]) for z in a["ent"] if z["e"] is not None]
    ci = boot_diff_mean(add_e, cur_e) if (len(add_e) >= 2 and len(cur_e) >= 2) else None
    return ("✅ يُقترح التغيير" if ok else "يبقى الرقم"), {"added": added, "ci_added_minus_current": ci}


# ══ الرنر ══════════════════════════════════════════════════════════════════════════════════════════════
def _getjson(url, tries=4):
    import urllib.error
    import urllib.request
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "t-gatecal/1"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:                       # noqa: PERF203
            if e.code in (403, 404):
                return None
            time.sleep(2 ** k)
        except Exception:                                         # noqa: BLE001
            time.sleep(2 ** k)
    return None


def _jdump(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False)


def _jload_glob(d_in, pat):
    ps = sorted(glob.glob(os.path.join(d_in, "**", pat), recursive=True))
    out = []
    for p in ps:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            out.append(json.load(fh))
    return out


def mode_prep(key, tool):
    """كلُّ التقسيمات (Polygon · بالصفحات) منذ 2021-09 ⟵ {رمز: [[يوم التنفيذ، to/from]]} ‏+ الجلسات."""
    import market_calendar as MC
    splits, url, pages = {}, f"https://api.polygon.io/v3/reference/splits?execution_date.gte=2021-09-01&limit=1000&order=asc&sort=execution_date&apiKey={key}", 0
    while url:
        js = _getjson(url)
        if js is None:
            log("⛔ تعذّرت صفحةُ التقسيمات — لا تغطيةَ ناقصة تُقبل")
            return RC_POP
        pages += 1
        for r in js.get("results") or []:
            try:
                ratio = float(r["split_to"]) / float(r["split_from"])
            except (KeyError, ValueError, ZeroDivisionError):
                continue
            splits.setdefault(r["ticker"], []).append([r["execution_date"], ratio])
        nx = js.get("next_url")
        url = (nx + f"&apiKey={key}") if nx else None
    today = dt.date.today().isoformat()
    sess, d = [], dt.date.fromisoformat(BARS_FROM)
    while d.isoformat() <= today:
        if d.weekday() < 5 and MC.session_info(d.isoformat()).get("open_ny_min") is not None:
            sess.append(d.isoformat())
        d += dt.timedelta(1)
    rev = sorted(s for s, v in splits.items() if any(r < 1 for _x, r in v) and s.isalpha() and len(s) <= 5)
    members = {}
    if tool == "ready":                             # كونُ الجاهزيّة: لقطةُ ناسداك (CS/ADRC) أوّلَ كلّ شهرٍ في المدى — نقطةً في الزمن (يشمل المشطوب)
        import pit_universe as PU
        a, b = (os.environ.get("GATECAL_FROM") or "2026-08-16"), (os.environ.get("GATECAL_TO") or today)
        for m in sorted({d[:7] for d in sess if a[:7] <= d[:7] <= b[:7]}):
            first = next(d for d in sess if d[:7] == m)
            members[m] = sorted(r["ticker"] for r in PU.fetch_universe(first, key) if r.get("type") in ("CS", "ADRC"))
            log(f"prep ready {first}: {len(members[m])}")
        rev = sorted({x for v in members.values() for x in v})
    _jdump({"tool": tool, "splits": splits, "sessions": sess, "rev_syms": rev, "members": members, "pages": pages, "asof": today}, os.path.join(OUT, f"gatecal_prep_{tool}.json.gz"))
    log(f"📦 prep {tool}: صفحات {pages} · رموزٌ بتقسيم {len(splits)} · بتقسيمٍ عكسيّ {len(rev)} · جلسات {len(sess)}")
    return RC_OK


def _feat_split_hunter(S, key, sym, rows, sp, d_from, d_to, pct, loose):
    """صيّادُ التقسيم: لكلّ جلسةٍ D ∈ [d_from، d_to] حيث للرمز تقسيمٌ عكسيٌّ خلال أرخى عمر — القيمُ الخامّ بدوالّ الصيّاد بالاسم."""
    import pandas as pd
    days = [x[0] for x in rows]
    O, H, Lw, C, V = ([float(x[q]) for x in rows] for q in (1, 2, 3, 4, 5))
    df_all = pd.DataFrame({"Open": O, "High": H, "Low": Lw, "Close": C, "Volume": V}, index=pd.to_datetime(days))
    rev_days = sorted(x for x, r in sp if r < 1)
    split_days = {x for x, _r in sp}
    out, shares_memo = [], {}
    for i, d in enumerate(days):
        if d < d_from or d > d_to or i < 25:
            continue
        k = bisect.bisect_right(rev_days, d) - 1
        if k < 0:
            continue
        ev = rev_days[k]
        age = (dt.date.fromisoformat(d) - dt.date.fromisoformat(ev)).days
        if age > loose["lookback"]:
            continue
        price = C[i] * fwd_factor(sp, d)
        if not (1.0 <= price <= loose["price_max"]):
            continue
        cl = {}
        for L in TOOLS["split_hunter"]["ladders"]["lookback"]:
            look = min(int(L), i)
            cl[str(L)] = min((C[i - q + 1] / C[i - q] - 1.0) for q in range(1, look + 1) if C[i - q] > 0)
        if cl[str(int(loose["lookback"]))] > -loose["cliff"] / 100.0:
            continue
        df = df_all.iloc[:i + 1]
        sp_asof = pd.Series({pd.Timestamp(x): r for x, r in sp if x <= d})
        today = dt.date.fromisoformat(d)
        pr = S._split_setup_probe(df, sp_asof, today)              # ①: الحدثُ والقمّةُ÷2 بدالّة الصيّاد نفسِها
        if not pr or pr.get("event_kind") != "split" or not pr.get("half"):
            continue
        ref = S._post_split_high(df["High"], sp_asof, df.index[-1])
        if not ref or ref <= 0:
            continue
        half = ref / 2.0
        tail = [round(float(x) / half, 5) for x in C[max(0, i - 4):i + 1]]
        lo, hi = loose["band_low"], 1.0 + loose["band_hi"]
        if not (lo <= tail[-1] <= hi):
            continue
        fv = S._event_day_open(df.get("Open"), dt.date.fromisoformat(pr["event_date"]))
        if fv is None or fv != fv:
            fv = S._split_day_value(df["Close"], sp_asof, df.index[-1])
        rose = ((ref / fv - 1.0) * 100.0) if (fv and fv == fv and fv > 0) else None
        if rose is not None and rose > loose["rose"]:
            continue
        mon = d[:7]
        if mon not in shares_memo:
            js = _getjson(f"https://api.polygon.io/v3/reference/tickers/{sym}?date={d}&apiKey={key}") or {}
            _res = js.get("results") or {}
            shares_memo[mon] = (_res.get("share_class_shares_outstanding"), _res.get("primary_exchange"))
        pump = bool((S.group_pump_scar(df) or {}).get("found"))
        x, mx = exploded_label(days, H, C, i, pct, split_days)
        out.append({"sym": sym, "d": d, "x": x, "mx": mx, "r": trade_return(O, H, C, i),
                    "ret5": (C[i] / C[i - 5] - 1.0) if C[i - 5] > 0 else None,
                    "v": {"age": age, "price": round(price, 4), "cliff": {a: round(b, 5) for a, b in cl.items()}, "tail": tail,
                          "rose": (round(rose, 3) if rose is not None else None), "shares": shares_memo[mon][0], "exch": shares_memo[mon][1], "pump": pump, "ev": ev}})
    return out


def _feat_split_filter(S, key, sym, rows, sp, d_from, d_to, pct, loose):
    """فلترُ التقسيم: لكلّ جلسةٍ D — الحدثُ والقمّةُ÷2 و«ما صعد» بدوالّ الصيّاد · والتسلسلُ `method_sequence` لكلّ قيمةٍ في سلّمَي الارتداد والتسامح ·
    وقاعُ النافذة `g2_soft_facts` · والقروب — **كلُّها بالاسم** على شموعٍ بمقياس يوم D الخامّ (سلّمُ الطلبات بالسنتات)."""
    import pandas as pd
    t = TOOLS["split_filter"]
    days = [x[0] for x in rows]
    O, H, Lw, C, V = ([float(x[q]) for x in rows] for q in (1, 2, 3, 4, 5))
    rev_days = sorted(x for x, r in sp if r < 1)
    split_days = {x for x, _r in sp}
    idx = pd.to_datetime(days)
    win = int(S.CONFIG["FAISAL_BOTTOM_LOOKBACK"])
    step, nlad = float(S.CONFIG["FAISAL_LADDER_STEP"]), int(S.CONFIG["ENTRY_TRANCHES"])
    cb, ct = t["current"]["bounce"], t["current"]["tol"]
    grid = sorted({(b, ct) for b in t["ladders"]["bounce"]} | {(cb, x) for x in t["ladders"]["tol"]}
                  | {(loosest("split_filter", "bounce"), loosest("split_filter", "tol"))})      # ومعها أرخى الاثنين معًا (عدُّ «إرخاء الكلّ»)
    out, exch_memo = [], {}
    for i, d in enumerate(days):
        if d < d_from or d > d_to or i < 40:
            continue
        k = bisect.bisect_right(rev_days, d) - 1
        if k < 0 or (dt.date.fromisoformat(d) - dt.date.fromisoformat(rev_days[k])).days > SF_LOOKBACK:
            continue
        f = fwd_factor(sp, d)
        price = C[i] * f
        if not (SF_PRICE[0] <= price <= SF_PRICE[1]):
            continue
        df = pd.DataFrame({"Open": [x * f for x in O[:i + 1]], "High": [x * f for x in H[:i + 1]], "Low": [x * f for x in Lw[:i + 1]],
                           "Close": [x * f for x in C[:i + 1]], "Volume": V[:i + 1]}, index=idx[:i + 1])
        sp_asof = pd.Series({pd.Timestamp(x): r for x, r in sp if x <= d})
        today = dt.date.fromisoformat(d)
        pr = S._split_setup_probe(df, sp_asof, today)
        if not pr or pr.get("event_kind") != "split":
            continue
        ref = S._post_split_high(df["High"], sp_asof, df.index[-1])
        if not ref or ref <= 0:
            continue
        half = ref / 2.0
        tail = [round(float(x) * f / half, 5) for x in C[max(0, i - 4):i + 1]]
        if not (loose["band_low"] <= tail[-1] <= 1.0 + loose["band_hi"]):
            continue
        fv = S._event_day_open(df.get("Open"), dt.date.fromisoformat(pr["event_date"]))
        if fv is None or fv != fv:
            fv = S._split_day_value(df["Close"], sp_asof, df.index[-1])
        rose = ((ref / fv - 1.0) * 100.0) if (fv and fv == fv and fv > 0) else None
        if rose is not None and rose > loose["rose"]:
            continue
        seqs = {}
        for b, tl in grid:
            sq = S.method_sequence(df, win=win, bounce_min=b, tol=tl)
            seqs[f"{b:g}|{tl:g}"] = ({"ok": True, "bottom": round(float(sq["bottom"]), 5)} if (sq and sq.get("ok")) else {"ok": False})
        g = S.g2_soft_facts(df, win) or {}
        mon = d[:7]
        if mon not in exch_memo:
            js = _getjson(f"https://api.polygon.io/v3/reference/tickers/{sym}?date={d}&apiKey={key}") or {}
            exch_memo[mon] = (js.get("results") or {}).get("primary_exchange")
        x, mx = exploded_label(days, H, C, i, pct, split_days)
        out.append({"sym": sym, "d": d, "x": x, "mx": mx, "r": trade_return(O, H, C, i),
                    "ret5": (C[i] / C[i - 5] - 1.0) if C[i - 5] > 0 else None,
                    "v": {"age": (today - dt.date.fromisoformat(rev_days[k])).days, "price": round(price, 4), "tail": tail,
                          "rose": (round(rose, 3) if rose is not None else None), "seqs": seqs,
                          "g2": {"low": g.get("low"), "bounce": g.get("bounce_pct")}, "step": step, "nlad": nlad,
                          "pump": bool(S.group_pump_scar(df)), "exch": exch_memo[mon]}})
    return out


def rd_reason(S, sym, df):
    """`analyze_ticker` بالإعداد القائم ⟵ (عبر؟، سببُ الرفض من `_REJECT_STATS`) — الدالّةُ الإنتاجيّة بالاسم."""
    S._REJECT_STATS.clear()
    try:
        r = S.analyze_ticker(sym, df)
    except Exception:                                            # noqa: BLE001
        return False, "⛔ استثناء", None
    why = next(iter(S._REJECT_STATS), None) if not r else None
    return bool(r), why, r


def _feat_ready(S, key, sym, rows, sp, d_from, d_to, pct, loose, ctx=None):
    """الجاهزيّة: لكلّ جلسة D والرمزُ عضوٌ في كون شهرها — `analyze_ticker` الإنتاجيّ على آخر 800 يومٍ حتى D بمقياس D (تقسيماتٌ منفّذة حتى D) ·
    الحاليّ ⟵ وإن رُفض فبإرخاء الكلّ ⟵ وإن عبر أحدُهما فكلُّ قيمةِ سلّمٍ بشرطٍ واحد · والقيمُ بـ`near_watch_measure` بالاسم."""
    import pandas as pd
    import catalog_envelope as CE
    t = TOOLS["ready"]
    cur_cfg, member = ctx["cfg"], ctx["member"]
    days = [x[0] for x in rows]
    O, H, Lw, C, V = ([float(x[q]) for x in rows] for q in (1, 2, 3, 4, 5))
    split_days = {x for x, _r in sp}
    full = pd.DataFrame({"Open": O, "High": H, "Low": Lw, "Close": C, "Volume": V}, index=pd.to_datetime(days))
    loose_cfg = dict(cur_cfg)
    loose_cfg.update({RD_KEY[c]: loose[c] for c in loose})
    out = []
    try:
        for i, d in enumerate(days):
            if d < d_from or d > d_to or i < 60 or sym not in member.get(d[:7], ()):
                continue
            lo = bisect.bisect_left(days, (dt.date.fromisoformat(d) - dt.timedelta(RD_HISTORY_DAYS)).isoformat())
            sub = full.iloc[lo:i + 1]
            f = fwd_factor(sp, d)
            if f != 1.0:
                sub = sub.copy()
                sub[["Open", "High", "Low", "Close"]] *= f
                sub["Volume"] /= f
            S.CONFIG.clear()
            S.CONFIG.update(cur_cfg)
            ok0, why, r0 = rd_reason(S, sym, sub)
            ok_all = ok0
            if not ok0:
                S.CONFIG.clear()
                S.CONFIG.update(loose_cfg)
                ok_all = rd_reason(S, sym, sub)[0]
            S.CONFIG.clear()
            S.CONFIG.update(cur_cfg)
            nw, vals = None, (CE.result_vals(r0) if r0 else None)
            if not ok0:                             # «تحت المتابعة» كما يقيسها البوت: القيمُ بالبوّابات مُرخاة والخارجُ عن ظرف الكاتالوج
                m = S.near_watch_measure(sym, sub, ctx["edges"])
                if m:
                    vals = m[0]
                    nw = list(m[1]) if S.near_watch_founded(m[0], ctx["edges"]) else None
            if not (ok0 or ok_all or (nw is not None and len(nw) <= 1 and d >= RD_NW_FROM)):
                continue
            pm = {}
            for c, lad in t["ladders"].items():
                pm[c] = []
                for val in lad:
                    if val == t["current"][c]:
                        pm[c].append(int(ok0))
                        continue
                    if not ok_all:                  # لا يعبر حتى بإرخاء الكلّ ⟵ لا يعبر بإرخاء شرطٍ واحد (السلالمُ داخل الأرخى)
                        pm[c].append(0)
                        continue
                    S.CONFIG.clear()
                    S.CONFIG.update(cur_cfg)
                    S.CONFIG[RD_KEY[c]] = val
                    pm[c].append(int(rd_reason(S, sym, sub)[0]))
            S.CONFIG.clear()
            S.CONFIG.update(cur_cfg)
            x, mx = exploded_label(days, H, C, i, pct, split_days)
            out.append({"sym": sym, "d": d, "x": x, "mx": mx, "r": trade_return(O, H, C, i),
                        "ret5": (C[i] / C[i - 5] - 1.0) if C[i - 5] > 0 else None,
                        "v": {"p": pm, "all": int(ok_all), "why": why, "exch": "XNAS", "nw": nw,
                              "vals": {k: (round(float(z), 4) if isinstance(z, (int, float)) and z == z else None)
                                       for k, z in (vals or {}).items() if k in set(RD_VAL.values())}}})
    finally:
        S.CONFIG.clear()
        S.CONFIG.update(cur_cfg)
    return out


def rd_context(S, prep):
    """إعدادُ الإنتاج الحيّ (`apply_faisal_only` بالمفتاح 1 على نسخة) وعضويّةُ الكون الشهريّة — وصمتُ السجلّ."""
    cur = dict(S.CONFIG)
    cur["FAISAL_ONLY"] = 1
    S.apply_faisal_only(cur, log_fn=lambda *a: None)
    S.log = lambda *a, **k: None
    import envelope_scan as EV
    return {"cfg": cur, "member": {m: set(v) for m, v in (prep.get("members") or {}).items()}, "edges": EV.load_edges() or {}}


FEAT_FN = {"split_hunter": _feat_split_hunter, "split_filter": _feat_split_filter, "ready": _feat_ready}
RELAX = {"split_hunter": lambda loose: {"SPLIT_LOOKBACK_DAYS": int(loose["lookback"])}, "split_filter": lambda loose: {}, "ready": lambda loose: {}}
DIAG_WIDE = {"split_hunter": {"rose": 1e9, "band_low": 0.0, "band_hi": 1e9, "hold": 1, "shares": 1e18, "cliff": -1e9, "lookback": 250, "price_max": 1e9},
             "split_filter": {"rose": 1e9, "band_low": 0.0, "band_hi": 1e9, "bounce": 5.0, "tol": 0.04, "zone": 1e9}, "ready": {}}


def mode_feat(key, tool, k, d_from, d_to, d_in):
    if tool not in TOOLS:
        return 1
    preps = _jload_glob(d_in, f"gatecal_prep_{tool}.json.gz")
    if not preps:
        log(f"⛔ غاب تحضيرُ {tool} — خروج {RC_POP}")
        return RC_POP
    prep = preps[0]
    import Super_stock as S
    pct = float(S.EXPLODED_PCT)
    t = TOOLS[tool]
    loose = {c: loosest(tool, c) for c in t["ladders"]}
    syms = prep["rev_syms"][k::NSHARDS]
    relax = RELAX[tool](loose)
    sv = {kk: S.CONFIG.get(kk) for kk in relax}
    out, nobars, t0 = [], 0, time.time()
    bars_from = t.get("bars_from", BARS_FROM)
    ctx = rd_context(S, prep) if tool == "ready" else None
    try:
        S.CONFIG.update(relax)                                      # إرخاءُ نافذة الحدث لقراءة القيم — يُستعاد
        for j, sym in enumerate(syms):
            js = _getjson(f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/day/{bars_from}/{prep['asof']}?adjusted=true&sort=asc&limit=50000&apiKey={key}") or {}
            rows = [(dt.datetime.utcfromtimestamp(x["t"] / 1000).date().isoformat(), x["o"], x["h"], x["l"], x["c"], x.get("v") or 0.0)
                    for x in js.get("results") or []]
            if len(rows) < 30:
                nobars += 1
                continue
            if ctx is not None:
                out.extend(_feat_ready(S, key, sym, rows, prep["splits"].get(sym) or [], d_from, d_to, pct, loose, ctx))
                continue
            out.extend(FEAT_FN[tool](S, key, sym, rows, prep["splits"].get(sym) or [], d_from, d_to, pct, loose))
            if j % 25 == 0:
                log(f"gatecal feat {tool} {k}: {j + 1}/{len(syms)} · صفوف {len(out)} · {round(time.time() - t0)}s")
    finally:
        S.CONFIG.update(sv)
    _jdump({"tool": tool, "shard": k, "from": d_from, "to": d_to, "syms": len(syms), "nobars": nobars, "rows": out},
           os.path.join(OUT, f"gatecal_feat_{tool}_{k:02d}.json.gz"))
    log(f"📦 gatecal feat {tool} {k}: رموز {len(syms)} · بلا شموع {nobars} · صفوف {len(out)}")
    return RC_OK


def load_rows(tool, d_in):
    shards = _jload_glob(d_in, f"gatecal_feat_{tool}_*.json.gz")
    rows = [r for s in shards for r in s["rows"] if (r.get("v") or {}).get("exch") == "XNAS"]      # كونُ البوت ناسداك (الملحق)
    return rows, len(shards), (shards[0]["from"], shards[0]["to"]) if shards else (None, None)


def build(rows, sessions):
    """⟵ (rows_by_sym، sessions_ix، ctrl_pool {(يوم، عُشير): [(رمز، عائد)]}) · ويَسِم كلَّ صفٍّ بعُشيره داخل كون الأداة في جلسته."""
    ix = {d: q for q, d in enumerate(sessions)}
    by_day = {}
    for r in rows:
        by_day.setdefault(r["d"], []).append(r)
    pool = {}
    for d, rs in by_day.items():
        dec = deciles([(r["sym"], r["ret5"]) for r in rs if r.get("ret5") is not None])
        for r in rs:
            r["dec"] = dec.get(r["sym"])
            pool.setdefault((d, r["dec"]), []).append((r["sym"], r.get("r")))
    for kk in pool:
        pool[kk].sort()
    by_sym = {}
    for r in sorted(rows, key=lambda z: (z["sym"], z["d"])):
        by_sym.setdefault(r["sym"], []).append(r)
    return by_sym, ix, pool


def _months(a, b):
    return max(1.0, (dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days / 30.44)


def wall_base(code):
    """مفتاحُ الجدار بلا ما بين القوسين (`_reject_key_base` بمعناه) — نقيّة."""
    k = str(code or "")
    i = k.find("(")
    return (k[:i].strip() or k) if i > 0 else k


def rd_ledger_pairs(snaps, sessions):
    """سجلُّ الرفض اليوميّ (`reject_log.json` بلقطاته) ⟵ {(رمز، جلسةُ الشموع): جدار} — يومُ اللقطة X يقرأ شموعَ آخر جلسةٍ قبل X ·
    والجدرانُ المقصوصةُ بالعيّنة (`sampled`) لا تُعَدّ (قائمتُها ناقصة) · نقيّة."""
    out = {}
    for day in snaps:
        date = str(day.get("date") or "")
        k = bisect.bisect_left(sessions, date) - 1
        if k < 0:
            continue
        cut = set(day.get("sampled") or [])
        for wall, syms in (day.get("walls") or {}).items():
            if wall in cut:
                continue
            for sym in syms or []:
                out[(sym, sessions[k])] = wall
    return out


def rd_ledger(rows_by_sym, sessions, snaps=None):
    """§② مطابقةُ الجاهزيّة: جدارُ البوت المسجَّل مقابل جدار الإعادة للصفّ نفسِه (حيث للإعادة صفّ) ⟵ (المقارَن، المتّفق، المختلف)."""
    if snaps is None:
        import subprocess
        snaps, seen = [], set()
        try:
            cs = subprocess.run(["git", "log", "--format=%H", "--", "reject_log.json"], cwd=ROOT, capture_output=True, text=True, timeout=120).stdout.split()
        except Exception:                                        # noqa: BLE001
            cs = []
        for c in cs:
            try:
                blob = subprocess.run(["git", "show", f"{c}:reject_log.json"], cwd=ROOT, capture_output=True, text=True, timeout=60).stdout
                for day in json.loads(blob):
                    if day.get("date") not in seen:              # الأحدثُ أوّلًا (git log) ⟵ آخرُ كتابةٍ لليوم تغلب
                        seen.add(day.get("date"))
                        snaps.append(day)
            except Exception:                                    # noqa: BLE001
                continue
    pairs = rd_ledger_pairs(snaps, sessions)
    tot, hit, miss = 0, 0, []
    for (sym, d), wall in sorted(pairs.items()):
        r = next((z for z in rows_by_sym.get(sym, []) if z["d"] == d), None)
        if r is None:
            continue
        tot += 1
        got = wall_base(r["v"].get("why")) if not r["v"]["p"]["base"][TOOLS["ready"]["ladders"]["base"].index(TOOLS["ready"]["current"]["base"])] else "عبر"
        if got == wall_base(wall):
            hit += 1
        else:
            miss.append((sym, d, f"السجلّ {wall} · الإعادة {got}"))
    return tot, hit, miss


def wall_table(rows_by_sym, ix, win=WIN):
    """🧱 جدولُ الجدار الفعليّ: صفوفُ «تحت المتابعة» بناقصٍ واحد فأقلّ (أوّلُ صفٍّ للرمز ثمّ لا صفَّ قبل win جلسة) ⟵
    {(ناقصُ الظرف، جدارُ الفرز): [عدد، موسوم، منفجر]} — نقيّة."""
    out = {}
    for sym in sorted(rows_by_sym):
        last = None
        for r in rows_by_sym[sym]:
            nw = r["v"].get("nw")
            if nw is None or len(nw) > 1 or r["v"]["p"]["base"][TOOLS["ready"]["ladders"]["base"].index(120.0)]:
                continue
            q = ix[r["d"]]
            if last is not None and q - last < win:
                continue
            last = q
            k = ((nw[0] if nw else "لا ناقص"), wall_base(r["v"].get("why")))
            c = out.setdefault(k, [0, 0, 0])
            c[0] += 1
            if r.get("x") is not None:
                c[1] += 1
                c[2] += int(bool(r["x"]))
    return out


def ledger_match(tool, rows_by_sym):
    """§② مطابقةُ السجلّ: عابرو `hunter_ledger.jsonl` (مرشَّحين) — كم منهم يعبر في الإعادة بالأرقام الحاليّة في جلسته؟"""
    t = TOOLS[tool]
    path = os.path.join(ROOT, "hunter_ledger.jsonl")
    led = []
    if os.path.exists(path):
        for ln in open(path, encoding="utf-8"):
            try:
                j = json.loads(ln)
            except ValueError:
                continue
            if j.get("hunter") in t["ledger_hunter"] and j.get("kind") == "candidate":
                led.append((j["symbol"], j["session"]))
    hit, miss = 0, []
    for sym, d in sorted(set(led)):
        r = next((z for z in rows_by_sym.get(sym, []) if z["d"] == d), None)
        if r is not None and passes(r["v"], t["current"]):
            hit += 1
        else:
            miss.append((sym, d, "لا صفّ" if r is None else "صفٌّ لا يعبر"))
    return len(set(led)), hit, miss


def why_fails(v, P):
    """أسماءُ الشروط التي يسقط عليها الصفُّ بالأرقام P (بترتيب الصيّاد) — نقيّة · للتشخيص."""
    if "seqs" in v:
        return sf_why(v, P)
    if "p" in v:
        return [] if passes(v, P) else [str(v.get("why") or "؟")]
    out = []
    if v["age"] > P["lookback"]:
        out.append("lookback")
    if not (1.0 <= v["price"] <= P["price_max"]):
        out.append("price")
    cl = v["cliff"].get(str(int(P["lookback"])))
    if cl is None or cl > -P["cliff"] / 100.0:
        out.append("cliff")
    lo, hi, n, t = P["band_low"], 1.0 + P["band_hi"], int(P["hold"]), v["tail"]
    if not (lo <= t[-1] <= hi):
        out.append("band")
    elif len(t) < n or not all(lo <= x <= hi for x in t[-n:]):
        out.append("hold")
    if v["rose"] is not None and v["rose"] > P["rose"]:
        out.append("rose")
    if v.get("shares") is None or not (v["shares"] < P["shares"]):
        out.append("shares")
    if v.get("pump"):
        out.append("pump")
    return out


def mode_diag(key, tool):
    """§② أسبابُ فرق المطابقة: لكلّ (رمز، جلسة) في السجلّ الحقيقيّ تُعاد القيمُ **بلا أيّ مرشِّح** وتُطبع مع الشروط الساقطة — قراءةٌ ووصف."""
    import Super_stock as S
    t = TOOLS[tool]
    led = {}
    for ln in open(os.path.join(ROOT, "hunter_ledger.jsonl"), encoding="utf-8"):
        try:
            j = json.loads(ln)
        except ValueError:
            continue
        if j.get("hunter") in t["ledger_hunter"] and j.get("kind") == "candidate":
            led.setdefault(j["symbol"], {})[j["session"]] = j
    wide = DIAG_WIDE[tool]
    relax = RELAX[tool]({"lookback": 250})
    today = dt.date.today().isoformat()
    log(f"# 📏 T-GATECAL — تشخيصُ مطابقة السجلّ · {tool} · {sum(len(v) for v in led.values())} (رمز·جلسة) في {len(led)} رمزًا")
    tally = {}
    sv = {kk: S.CONFIG.get(kk) for kk in relax}
    try:
        S.CONFIG.update(relax)
        for sym in sorted(led):
            js = _getjson(f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/day/{BARS_FROM}/{today}?adjusted=true&sort=asc&limit=50000&apiKey={key}") or {}
            rows = [(dt.datetime.utcfromtimestamp(x["t"] / 1000).date().isoformat(), x["o"], x["h"], x["l"], x["c"], x.get("v") or 0.0)
                    for x in js.get("results") or []]
            sj = _getjson(f"https://api.polygon.io/v3/reference/splits?ticker={sym}&limit=1000&apiKey={key}") or {}
            sp = sorted([r["execution_date"], float(r["split_to"]) / float(r["split_from"])] for r in sj.get("results") or [] if float(r.get("split_from") or 0) > 0)
            d0, d1 = min(led[sym]), max(led[sym])
            got = {r["d"]: r for r in (FEAT_FN[tool](S, key, sym, rows, sp, d0, d1, float(S.EXPLODED_PCT), wide) if len(rows) >= 30 else [])}
            log(f"## {sym} — شموع {len(rows)} · تقسيماتُ Polygon {sp[-4:]}")
            for d in sorted(led[sym]):
                lj, r = led[sym][d], got.get(d)
                if r is None:
                    why = "لا صفّ: " + ("لا شموع" if len(rows) < 30 else "لا تقسيمَ عكسيًّا في 250 يومًا عند Polygon (أو الحدثُ طرح)" if not any(
                        x <= d and q < 1 and (dt.date.fromisoformat(d) - dt.date.fromisoformat(x)).days <= 250 for x, q in sp) else "سقط في الإعادة (القمّة÷2 أو السعر)")
                    tally[why] = tally.get(why, 0) + 1
                    log(f"- {d}: {why} · السجلّ: فلوت {lj.get('float')} · سعر {lj.get('price')} · ÷2 {lj.get('half')} · مرجع {lj.get('ref')}")
                    continue
                v = r["v"]
                f = why_fails(v, t["current"]) + ([] if v.get("exch") == "XNAS" else [f"exch={v.get('exch')}"])
                kk = "يعبر" if not f else "يسقط على: " + "+".join(f)
                tally[kk] = tally.get(kk, 0) + 1
                _x = (f"تسلسل {v['seqs'].get('10|0.015')} · قاعُ النافذة {v['g2']}" if "seqs" in v
                      else f"كليف120 {v['cliff'].get('120')} · أسهم {v.get('shares')}")
                log(f"- {d}: {kk} · عمر {v['age']} · سعر {v['price']} · ذيل {v['tail']} · صعد {v['rose']} · {_x} · قروب {v.get('pump')} ‖ السجلّ: فلوت {lj.get('float')} · سعر {lj.get('price')} · ÷2 {lj.get('half')} · مرجع {lj.get('ref')}")
    finally:
        S.CONFIG.update(sv)
    log("")
    log("## الحصيلة")
    for kk, n in sorted(tally.items(), key=lambda z: -z[1]):
        log(f"- {kk}: {n}")
    return RC_OK


def _fmt(x, pc=False):
    if x is None:
        return "—"
    return f"{x * 100:.1f}%" if pc else (f"{x:,.0f}" if abs(x) >= 1000 else f"{x:g}")


def _sp(x):
    return "—" if x is None else f"{x * 100:+.1f}%"


def print_curves(tool, by_sym, ix, pool, months, conds=None):
    t = TOOLS[tool]
    res, tried = {}, 0
    for cond in (conds or list(t["ladders"])):
        cv = curve(tool, cond, by_sym, ix, pool, months)
        res[cond] = cv
        log("")
        log(f"### {t['label'][cond]} — الحاليّ {_fmt(t['current'][cond])}")
        log("| القيمة | منفجرون يدخلون | غيرُ منفجرين | نسبةُ الانفجار | حلقات/شهر | متوسّطُ الفائض بعد الكلفة | متوسّطُ العائد | n |")
        log("|---|---|---|---|---|---|---|---|")
        for val in t["ladders"][cond]:
            p = cv["points"][val]
            tried += 1
            log(f"| {_fmt(val)}{' ◀' if val == t['current'][cond] else ''} | {p['x']} | {p['nonx']} | {_fmt(p['rate'], True)} | "
                f"{(p['per_month'] or 0):.1f} | {_sp(p['e_mean'])} | {_sp(p['r_mean'])} | {p['n']} |")
        log(f"- قيمةُ الشرط (ربيع أدنى · وسيط · ربيع أعلى · n): المنفجرون {cv['q_x']} · غيرُهم {cv['q_nonx']}")
        o = cv["only"]
        log(f"- منفجرون رفضهم هذا الشرطُ وحدَه: بهامش 1% فأقلّ {o['1']} · 5% فأقلّ {o['5']} · 10% فأقلّ {o['10']} · الكلّ {o['all']}")
    return res, tried


def mode_count(tool, d_in):
    rows, n, (a, b) = load_rows(tool, d_in)
    preps = _jload_glob(d_in, f"gatecal_prep_{tool}.json.gz")
    if n != NSHARDS or not preps:
        log(f"⛔ الشرائح {n} لا {NSHARDS} أو غاب التحضير — خروج {RC_POP}")
        return RC_POP
    t = TOOLS[tool]
    by_sym, ix, _pool = build(rows, preps[0]["sessions"])
    loose = {c: loosest(tool, c) for c in t["ladders"]}
    log(f"# 📏 T-GATECAL — العدُّ أوّلًا · {tool} · [{a}، {b}]")
    cur_eps = episodes(by_sym, ix, t["current"], t["current"])
    lo_eps = episodes(by_sym, ix, loose, loose)

    def cnt(eps):
        lab = [r for _s, _d, r in eps if r is not None and r.get("x") is not None]
        return len(eps), len(lab), sum(1 for r in lab if r["x"])
    c1, c2 = cnt(cur_eps), cnt(lo_eps)
    log(f"- صفوفُ الإعادة {len(rows)} · رموز {len(by_sym)}")
    log(f"- **بالأرقام الحاليّة: {c1[0]} حلقة · موسومة {c1[1]} · منفجرون {c1[2]}**")
    log(f"- **بأرخى السلّم في كلّ الشروط معًا: {c2[0]} حلقة · موسومة {c2[1]} · منفجرون {c2[2]}**")
    per = {}
    for cond in t["ladders"]:
        PL = dict(t["current"])
        PL[cond] = loosest(tool, cond)
        per[cond] = cnt(episodes(by_sym, ix, PL, PL))
        log(f"  - بإرخاء «{t['label'][cond]}» وحدَه إلى {_fmt(PL[cond])}: {per[cond][0]} حلقة · منفجرون {per[cond][2]}")
    best = max(per.values(), key=lambda z: z[0]) if per else (0, 0, 0)
    suff = best[0] >= SUFF["loose_eps"] and best[2] >= SUFF["loose_x"] and c1[0] >= SUFF["cur_eps"]
    tot, hit, miss = rd_ledger(by_sym, preps[0]["sessions"]) if tool == "ready" else ledger_match(tool, by_sym)
    if tool == "ready":
        log("")
        log("### 🧱 الجدارُ الفعليّ لصفوف «تحت المتابعة» بناقصٍ واحد فأقلّ (أوّلُ ظهورٍ للرمز كلَّ 20 جلسة)")
        log("| ناقصُ الظرف المعروض | جدارُ الفرز الفعليّ | حلقات | موسومة | منفجرون | نسبة |")
        log("|---|---|---|---|---|---|")
        for (a_, b_), c in sorted(wall_table(by_sym, ix).items(), key=lambda z: -z[1][0]):
            log(f"| {a_} | {b_} | {c[0]} | {c[1]} | {c[2]} | {_fmt(c[2] / c[1] if c[1] else None, True)} |")
        log("")
    log(f"- مطابقةُ السجلّ (§②): {'صفوفُ سجلّ الرفض المقارَنة' if tool == 'ready' else 'عابرو السجلّ الحقيقيّ'} {tot} (رمز·جلسة) · منهم {'متّفقُ الجدار' if tool == 'ready' else 'في الإعادة عابرون'} {hit} "
        f"({_fmt(hit / tot if tot else None, True)}) · الحدّ {MATCH_FLOOR:.0%}")
    for m in miss[:40]:
        log(f"  - لم يطابق: {m[0]} {m[1]} — {m[2]}")
    log(f"⚖️ GATECAL_COUNT {tool}: {'يكفي للحكم' if suff else 'لا يكفي للحكم في هذه الفترة'} "
        f"(الحدود: {SUFF['loose_eps']} حلقة و{SUFF['loose_x']} منفجرًا عند أرخى شرطٍ منفرد · {SUFF['cur_eps']} حلقة بالحاليّ)")
    return RC_OK


def _part(rows, lo=None, hi=None, years=None):
    return [r for r in rows if (years is None or r["d"][:4] in years) and (lo is None or r["d"] >= lo) and (hi is None or r["d"] <= hi)]


def mode_select(tool, d_in):
    rows, n, (a, b) = load_rows(tool, d_in)
    preps = _jload_glob(d_in, f"gatecal_prep_{tool}.json.gz")
    if n != NSHARDS or not preps:
        log(f"⛔ الشرائح {n} لا {NSHARDS} أو غاب التحضير — خروج {RC_POP}")
        return RC_POP
    t = TOOLS[tool]
    era = t.get("era")
    if era:
        if any(r["d"] < era["sel_from"] for r in rows):
            log(f"⛔ في المادّة جلسةٌ قبل جزء الاختيار {era['sel_from']} — خروج {RC_BLIND}")
            return RC_BLIND
    elif any(r["d"][:4] not in HIST_SEL for r in rows):
        log(f"⛔ في المادّة جلسةٌ خارج جزء الاختيار {HIST_SEL} — خروج {RC_BLIND}")
        return RC_BLIND
    by_sym, ix, pool = build(rows, preps[0]["sessions"])
    log(f"# 📏 T-GATECAL — الاختيار · {tool} · [{a}، {b}]")
    res, tried = print_curves(tool, by_sym, ix, pool, _months(a, b))
    props = {c: propose(tool, c, res[c]["points"]) for c in t["ladders"]}
    log("")
    log(f"- **عددُ كلّ ما جُرِّب: {tried}** (شرط × قيمة)")
    for c, v in props.items():
        log(f"- {t['label'][c]}: {'يبقى الرقم' if v is None else f'مرشَّح ⟵ {_fmt(v)}'}")
    fz = {"tool": tool, "contract_sha": CONTRACT_SHA, "addendum_sha": t["addendum_sha"], "part": ([era["sel_from"], b] if era else list(HIST_SEL)), "tried": tried,
          "proposals": {c: v for c, v in props.items() if v is not None},
          "stats": {c: {str(v): {k: (round(q, 6) if isinstance(q, float) else q) for k, q in p.items() if k != "ent"}
                        for v, p in res[c]["points"].items()} for c in t["ladders"]}}
    log("GATECAL_FREEZE " + json.dumps(fz, ensure_ascii=False, sort_keys=True))
    return RC_OK


def mode_confirm(tool, d_in):
    if os.path.exists(result_path(tool)):
        log(f"⛔ صدر حكمُ تأكيد {tool} — مرّةً واحدة · خروج {RC_ONCE}")
        return RC_ONCE
    if not freeze_ok(tool):
        log(f"⛔ ملفُّ تثبيت {tool} غائبٌ أو لا يطابق بصمتَه — خروج {RC_FREEZE}")
        return RC_FREEZE
    rows, n, (a, b) = load_rows(tool, d_in)
    preps = _jload_glob(d_in, f"gatecal_prep_{tool}.json.gz")
    if n != NSHARDS or not preps:
        return RC_POP
    t = TOOLS[tool]
    fz = json.load(open(freeze_path(tool), encoding="utf-8"))
    era = t.get("era")
    if era:
        if any(not (era["conf"][0] <= r["d"] <= era["conf"][1]) for r in rows):
            log(f"⛔ في المادّة جلسةٌ خارج جزء التأكيد {era['conf']} — خروج {RC_BLIND}")
            return RC_BLIND
    else:
        rows = _part(rows, years=HIST_CONF)
    by_sym, ix, pool = build(rows, preps[0]["sessions"])
    log(f"# 📏 T-GATECAL — التأكيد (مرّةً واحدة) · {tool} · {era['conf'] if era else HIST_CONF}")
    res, _tried = print_curves(tool, by_sym, ix, pool, _months(a, b), conds=sorted(fz["proposals"]) or None)
    out = []
    for c, v in sorted(fz["proposals"].items()):
        v = type(t["current"][c])(v) if not isinstance(t["current"][c], float) else float(v)
        vd, det = confirm_one(tool, c, v, res[c]["points"])
        out.append(vd)
        log(f"⚖️ {t['label'][c]}: {_fmt(t['current'][c])} ⟵ {_fmt(v)} — **{vd}** · المضافون {det.get('added')} · "
            f"فاصلُ فرق الفائض (المضافون − الحاليّون) {det.get('ci_added_minus_current')}")
    if not fz["proposals"]:
        log("⚖️ لا شرطَ مرشَّحًا من الاختيار ⟵ كلُّ الأرقام تبقى (والمنحنياتُ أعلاه وصف)")
    log("⚖️ GATECAL_CONFIRM " + tool + ": " + (" · ".join(out) or "لا مرشَّح"))
    rest = [c for c in t["ladders"] if c not in fz["proposals"]]
    if era and rest:                                # بقيّةُ الشروط على جزء التأكيد — وصفٌ لا حكم (لم تُرشَّح في الاختيار فلا يُقترح لها شيء)
        log("")
        log("## وصفٌ لا حكم — منحنياتُ الشروط غيرِ المرشَّحة على جزء التأكيد")
        print_curves(tool, by_sym, ix, pool, _months(a, b), conds=rest)
    return RC_OK


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    mode = argv[0] if argv else ""
    tool = argv[argv.index("--tool") + 1] if "--tool" in argv else ""
    if tool not in TOOLS:
        log("⛔ --tool " + " | ".join(TOOLS))
        return 1
    if not contract_ok(tool):
        log(f"⛔ العقدُ أو ملحقُ الأداة لا يطابق بصمتَه — خروج {RC_CONTRACT} قبل أيّ جلب")
        return RC_CONTRACT
    d_in = argv[argv.index("--dir") + 1] if "--dir" in argv else "gatecal_in"
    if mode == "count":
        return mode_count(tool, d_in)
    if mode == "select":
        return mode_select(tool, d_in)
    if mode == "confirm":
        return mode_confirm(tool, d_in)
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if mode in ("prep", "feat", "diag") and not key:
        log(f"⛔ بلا مفتاح Polygon — خروج {RC_KEY}")
        return RC_KEY
    if mode == "prep":
        return mode_prep(key, tool)
    if mode == "diag":
        return mode_diag(key, tool)
    if mode == "feat":
        d_from, d_to = argv[argv.index("--from") + 1], argv[argv.index("--to") + 1]
        _era = TOOLS[tool].get("era")
        if _era and d_from < _era["sel_from"] and not freeze_ok(tool):
            log(f"⛔ ما قبل {_era['sel_from']} (جزءُ التأكيد) مغلقٌ قبل ملفّ التثبيت ببصمته — خروج {RC_BLIND}")
            return RC_BLIND
        if d_to[:4] in HIST_CONF and d_from < TOOLS[tool]["built"] and not freeze_ok(tool):
            log(f"⛔ جزءُ التأكيد التاريخيّ {HIST_CONF} مغلقٌ قبل ملفّ التثبيت ببصمته — خروج {RC_BLIND}")
            return RC_BLIND
        return mode_feat(key, tool, int(argv[1]), d_from, d_to, d_in)
    log("⛔ prep | feat <k> | count | select | confirm")
    return 1


if __name__ == "__main__":
    sys.exit(main())
