# -*- coding: utf-8 -*-
"""📅📉 **التأريخُ ببصمة المؤشّر** — مصدرُ تأريخٍ **ثانٍ** لشارتات فيصل القديمة،
مستقلٌّ عن `faisal_price_anchor.py` (السعر) وعن EXIF وعن تاريخ git.

**لماذا لزم مصدرٌ ثانٍ (مقيسٌ لا مُفترَض):**
  • الصورُ التي تستشهد بها الصفوفُ غيرُ المؤرَّخة (`IMG_4xxx`–`IMG_8xxx`) **ليست على
    القرص ولا في تاريخ git** ⇒ EXIF وتاريخُ أوّل كوميت **بابان مغلقان بالقياس**.
  • `telegram_collect_state.json` يحمل `offset`/`seen_msg_ids`/`seen_file_ids`
    **بلا طابعٍ زمنيّ واحد** ⇒ تلغرام بابٌ مغلقٌ بالقياس.
  • عناوينُ الأقسام استُنفدت سلفًا (‏`date_source=header`).
  • **والباقي في نصّ الكاتالوج نفسِه: قيمةُ المؤشّر المسجَّلة على الشارت** —
    «‏RSI 73.694» · «‏MACD(12,26,9):‑0.214 Signal:‑0.277» · «‏MACD:‑0.461/‑0.681/+0.221».

**قراءةٌ فقط:** لا حالة · لا تلغرام · لا سرّ · لا مسَّ إنتاج. يكتب
`faisal_indicator_anchor_dates.tsv` **منفصلًا** عن جدول المستويات.

القواعدُ الثابتة **قبل أيّ رقم**:
  • **لا تأريخَ من رقم الصورة** (‏`LVT2`) — البصمةُ تُحسَب من بيانات السوق حصرًا.
  • البصمةُ تُقرأ من **كتلة الرمز نفسِه**: سطرُه إن ذكره، وإلّا نقطتُه داخل قسمٍ
    متعدّدِ الرموز، وإلّا القسمُ `###` كلُّه (‏درسُ BNKK/HCAI: كتلةُ الجار تلوّث).
  • **الفريمُ يُحترَم:** الفريمُ = آخرُ كلمةِ فريمٍ قبل موضع البصمة على سطرها
    (‏`faisal_levels_extract.frame_before` **بالاسم**)، وإلّا فريمُ الصفّ. ولا تُطابَق
    إلّا بصمةٌ فريمُها **يوميّ** — لأن المتاح شمعاتٌ يوميّة، وما سواه يُعلَن ويُترَك.
  • **‏RSI بلا تسويةِ تقسيم** — لأنه **ثابتٌ تحت إعادة القياس** بالبناء
    (‏`RS = avg_gain/avg_loss` فيختصر العامل) ⇒ مناعةٌ من حدّ الصدق الذي وسمه
    `T-SUPDEF`. **و‏MACD خطّيٌّ فيُقسَم** المسجَّلُ على `_split_scale_factor`.
  • **بارامتراتُ MACD لا تُخمَّن:** إن كتبها الكاتالوج (`MACD(12,26,9)`) استُعملت
    وحدَها؛ وإن لم يكتبها جُرّبت المجموعتان المرصودتان معًا **والمطابقةُ زوجٌ
    (‏يوم · بارامترات)** ⇒ الوحدانيّةُ أصعبُ لا أسهل.
  • **التسامحُ الحاكم = نصفُ آخر خانةٍ مسجَّلة** (‏«‏73.694» ⇒ ‏0.0005 · «‏35.30» ⇒
    ‏0.005) = مغلّفُ التقريب وحدَه. وتُطبَع **حساسيّةٌ** عند مضاعفاتٍ أوسع
    **وصفيّةً لا حاكمة** — وأيُّ استعمالٍ لاحقٍ لتسامحٍ أوسعَ يلزمه ملحقٌ مؤرَّخ.
  • النافذةُ والمِصدرُ ودالّةُ الأهداف **مستورَدةٌ بالاسم** من `faisal_price_anchor`
    ⇒ نطاقُ `gov` هو نطاقُه **بت-بت** (مقفولٌ سلوكيًّا)، ونطاقُ `all` يوسّعه إلى كلّ
    صفٍّ غيرِ مؤرَّخ في الجدول.
  • الحكم: `unique` · `ambiguous` · `none` · `no_fp` (لا بصمةَ يوميّة) · `no_data`.
  • **وشاهدُ هُويّةٍ يُطبَع مع كلّ تشغيلة:** كلُّ رمزٍ أرّخه مرساةُ السعر سلفًا
    (‏`faisal_price_anchor_dates.tsv`) يُقارَن — `AGREE` أو `DISAGREE` بتاريخيهما.
"""
import csv
import os
import re
import sys
from collections import Counter

import Super_stock as bot
import faisal_levels_extract as fle
import faisal_price_anchor as pa

CAT = pa.CAT
LEVELS_TSV = "faisal_levels_table.tsv"
OUT = "faisal_indicator_anchor_dates.tsv"
W0, W1 = pa.W0, pa.W1
# ‏🔥 **تسخينٌ قبل النافذة:** `RSI(14)` و`MACD(26)` مؤشّراتٌ أُسّيّةٌ تحتاج تاريخًا
# ‏سابقًا لتستقرّ. التحميلُ من `W0` نفسِه يجعل أوائلَ النافذة **مُقاسةً على بذرةٍ
# ‏قصيرة** فتفارق ما يعرضه الشارت ⇒ يُحمَّل من `WARMUP` **والمطابقةُ تبقى داخل
# ‏`[W0, W1]` حصرًا** (‏صفرُ توسيعٍ للنافذة الحاكمة).
WARMUP = "2024-01-01"

RSI_PERIOD = 14
MACD_SETS = ((12, 26, 9), (10, 20, 3))     # المرصودتان في الكاتالوج حصرًا
TOL_MULT = 1.0                             # الحاكم: نصفُ آخر خانة
SENS_MULTS = (1.0, 4.0, 20.0, 100.0)       # وصفيّ فقط
MIN_BARS = 60

_NUM = r"[\-+]?\d+(?:\.\d+)?"
_BIDI = "\u200e\u200f\u061c\u202a\u202b\u202c"
# ‏قراءةُ المؤشّر تُميَّز عن **قاعدةٍ منطوقة** بوجود الكسر العشريّ: كلُّ قراءةٍ
# ‏مرصودةٍ في الكاتالوج بكسر («‏73.694» · «‏35.30») وكلُّ قاعدةٍ بعددٍ صحيح
# ‏(«‏RSI 50 تشبع» · «‏RSI بين 23‑27») ⇒ اشتراطُ الكسر يفصلهما بلا تخمين.
RE_RSI = re.compile(r"RSI(?![A-Za-z_])(?:\s*\(\s*(\d{1,3})\s*\))?[\s:：=]{0,4}"
                    r"(\d{1,2}\.\d+)((?:\s*/\s*\d{1,3}(?:\.\d+)?)*)")
RE_MACD3 = re.compile(r"MACD\s*(?:\(\s*([\d,\s]+)\)\s*)?[^:：\n]{0,10}[:：]\s*"
                      r"(" + _NUM + r")\s*/\s*(" + _NUM + r")\s*/\s*(" + _NUM + r")")
RE_MACD2 = re.compile(r"MACD\s*(?:\(\s*([\d,\s]+)\)\s*)?[^:：\n]{0,10}[:：]\s*"
                      r"(" + _NUM + r")\s*Signal\s*[:：]\s*(" + _NUM + r")")
# ‏«MACD(10,20,3):12.22/6.14» = خطٌّ/إشارة بصيغة الشرطة (ولا تلتقط الثلاثيّة)
RE_MACD2S = re.compile(r"MACD\s*(?:\(\s*([\d,\s]+)\)\s*)?[^:：\n]{0,10}[:：]\s*"
                       r"(" + _NUM + r")\s*/\s*(" + _NUM + r")")


def log(m):
    print(m, flush=True)


def selfcheck_scope(src: str = None) -> bool:
    """صفرُ إرسالٍ وصفرُ كتابةِ حالة — **والكتابةُ الوحيدةُ المسموحة هي `OUT`**.

    ليست «قراءةً محضة» (الأداةُ تكتب جدولَها)، فالحارسُ يُقيّد **الوجهة** لا
    الفعل: أيُّ `open` بوضعِ كتابةٍ هدفُه غيرُ الثابت `OUT` ⇒ سقوط، وأيُّ وضعٍ
    **غيرِ ثابتٍ نصّيًّا** يُعَدّ كتابةً (‏ثغرةُ 2026-09-17 المُغلَقة).
    `src` مصدرٌ بديلٌ **للاختبار وحدَه** ⇒ يُتاح شاهدُ ضبطٍ يُثبت أنه يمسك العيب."""
    import ast as _ast
    banned = {"send_telegram", "send_telegram_document", "git_save",
              "save_watchlist", "save_op_entry_state", "record_new_alerts",
              "save_near_watch", "save_hunter_watch"}
    try:
        tree = _ast.parse(src if src is not None
                          else open(__file__, encoding="utf-8").read())
    except Exception:                                             # noqa: BLE001
        return False
    for n in _ast.walk(tree):
        if not isinstance(n, _ast.Call):
            continue
        fn = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
        if fn in banned:
            return False
        if fn != "open":
            continue
        mode, given, const = "", False, True
        if len(n.args) > 1:
            given = True
            if isinstance(n.args[1], _ast.Constant):
                mode = str(n.args[1].value)
            else:
                const = False
        for kw in n.keywords or []:
            if kw.arg == "mode":
                given = True
                if isinstance(kw.value, _ast.Constant):
                    mode = str(kw.value.value)
                else:
                    const = False
        if given and not const:
            return False
        if not any(ch in mode for ch in ("w", "a", "x", "+")):
            continue
        tgt = n.args[0] if n.args else None
        if not (isinstance(tgt, _ast.Name) and tgt.id == "OUT"):
            return False
    return True


# ═══════════════ ① دوالُّ نقيّة (قابلةٌ للاختبار بلا شبكة) ════════════════════
def clean(line: str) -> str:
    """يُطبِّع السطرَ قبل أيّ نمط: يُسقط محارفَ الاتّجاه ويوحّد السوالب.

    **الموضعُ محفوظٌ لـ`frame_before`** لأن الفريمَ يُقرأ من السطر المُطبَّع نفسِه."""
    t = (line or "")
    for ch in _BIDI:
        t = t.replace(ch, "")
    return t.replace("\u2011", "-").replace("\u2212", "-").replace("\u2013", "-")


def to_float(txt: str) -> float:
    """يقرأ الرقمَ بعد التطبيع (السالبُ قد يأتي «‑» U+2011 أو «−» U+2212)."""
    t = clean(txt).strip().replace("+", "")
    return float(t)


def half_ulp(txt: str) -> float:
    """نصفُ آخر خانةٍ مسجَّلة: «73.694» ⇒ 0.0005 · «35.30» ⇒ 0.005 · «12» ⇒ 0.5."""
    t = (txt or "").strip()
    n = len(t.split(".")[1]) if "." in t else 0
    return 0.5 * (10.0 ** (-n))


def parse_params(txt) -> tuple:
    """«12,26,9» ⇒ (12,26,9) · وإلّا `None` (ولا تُخمَّن)."""
    if not txt:
        return None
    parts = [p.strip() for p in str(txt).split(",") if p.strip()]
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return None
    return tuple(int(p) for p in parts)


def parse_fingerprints(line: str, fallback_frame: str = "unknown") -> list:
    """بصماتُ السطر: `{kind, frame, params, vals, tol, raw}` — `kind` ∈ {rsi, macd}."""
    txt = clean(line)
    out = []
    for m in RE_RSI.finditer(txt):
        if m.group(3):            # «RSI 49.56/40.44» = قراءتان لشارتين ⇒ الإسنادُ مجهول
            continue
        v = to_float(m.group(2))
        if not 0.0 <= v <= 100.0:
            continue
        per = int(m.group(1)) if m.group(1) else RSI_PERIOD
        out.append({"kind": "rsi", "frame": fle.frame_before(txt, m.start(), fallback_frame),
                    "params": (per,), "vals": (v,),
                    "tol": (half_ulp(m.group(2)),), "raw": m.group(0).strip()})
    # ‏الثلاثيّةُ أوّلًا، ثمّ النمطان الثنائيّان **ما لم يتداخلا معها** — فصيغةُ
    # ‏الشرطة «a/b/c» تبتلعها قراءةٌ ثنائيّةٌ مبتورة لولا إقصاءُ التداخل.
    spans = []
    for rex, n in ((RE_MACD3, 3), (RE_MACD2, 2), (RE_MACD2S, 2)):
        for m in rex.finditer(txt):
            if any(a <= m.start() < b for a, b in spans):
                continue
            g = m.groups()
            vals = tuple(to_float(x) for x in g[1:1 + n])
            tols = tuple(half_ulp(x) for x in g[1:1 + n])
            spans.append(m.span())
            out.append({"kind": "macd", "frame": fle.frame_before(txt, m.start(), fallback_frame),
                        "params": parse_params(g[0]), "vals": vals, "tol": tols,
                        "raw": m.group(0).strip()})
    return out


def resolve_conflicts(fps: list):
    """يطوي المكرَّرَ ويُسقط **نوعًا كاملًا** تضاربت قراءاتُه.

    قسمٌ يصف شارتًا واحدًا (‏`### NEXR — يومي`) تكون بصماتُه على أسطرٍ عدّةٍ
    **لنفس الشارت** ⇒ تقاطعُها مشروع. وقسمٌ يصف شارتاتٍ (‏`### SMX — ٤س/يومي/4س`)
    قد يحمل قراءتين مختلفتين للنوع نفسِه ⇒ **الإسنادُ مجهولٌ فيُسقَط النوع**،
    ولا يُخمَّن أيُّهما للشارت المقصود."""
    uniq, seen = [], set()
    for f in fps:
        k = (f["kind"], f["params"], f["vals"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(f)
    bad = {k for k in {f["kind"] for f in uniq}
           if len({f["vals"] for f in uniq if f["kind"] == k}) > 1}
    return [f for f in uniq if f["kind"] not in bad], sorted(bad)


def symbol_block(lines: list, n: int, sym: str) -> list:
    """أصغرُ كتلةٍ تحمل الرمز، كقائمةِ (رقمُ السطر، نصُّه)."""
    if sym and re.search(r"\b" + re.escape(sym) + r"\b", lines[n - 1]):
        return [(n, lines[n - 1])]
    s = None
    for i in range(n - 1, -1, -1):
        if lines[i].startswith("### "):
            s = i
            break
    if s is None:
        return [(n, lines[n - 1])]
    e = len(lines)
    for j in range(s + 1, len(lines)):
        if lines[j].startswith("### ") or lines[j].startswith("## "):
            e = j
            break
    bullets = [(k + 1, lines[k]) for k in range(s, e)
               if re.match(r"\s*-\s*\*\*[A-Z]{2,6}\s*—", lines[k])]
    if len(bullets) > 1 and sym:
        own = [b for b in bullets if re.search(r"\*\*" + re.escape(sym) + r"\s*—", b[1])]
        if own:
            return [own[0]]
    return [(k + 1, lines[k]) for k in range(s, e)]


def targets(scope: str = "all") -> list:
    """أهدافُ التأريخ: `{symbol, line, frame}` لكلّ صفٍّ غيرِ مؤرَّخ (مكرَّراتٌ مطويّة).

    `scope="gov"` = نطاقُ `faisal_price_anchor.targets` نفسُه (دعمٌ · يوميّ ·
    غيرُ آليّ) ⇒ يُقارَن به بت-بت في السويّة."""
    rows = list(csv.DictReader(open(LEVELS_TSV, encoding="utf-8"), delimiter="\t"))
    seen, out = set(), []
    for r in rows:
        if r["date"].strip():
            continue
        if r["frame"] != "daily":
            # ‏لا شموعَ إلّا يوميّة ⇒ لا يُؤرَّخ صفٌّ فريمُه غيرُها (ولا يُستعار
            # ‏تاريخُ الشارت اليوميّ لشارتِ ٤س في القسم نفسِه — إسنادٌ مجهول).
            continue
        if scope == "gov" and not (r["role"] == "support" and r["auto_chart"] == "0"):
            continue
        key = (r["symbol"], int(r["line"]))
        if key in seen:
            continue
        seen.add(key)
        out.append({"symbol": r["symbol"], "line": int(r["line"]), "frame": r["frame"]})
    return out


def build_series(df, periods=(RSI_PERIOD,)) -> dict:
    """`{dates: [...], rsi: {period: [...]}, macd: {(f,s,g): (line[], sig[])}}` من شموعٍ يوميّة.

    **الفتراتُ المطلوبةُ تُمرَّر** ولا تُفترَض: بصمةٌ بفترةٍ لم تُبنَ لا تُطابَق أصلًا."""
    try:
        close = df["Close"].astype(float)
    except Exception:                                             # noqa: BLE001
        return {}
    dates = [idx.date().isoformat() if hasattr(idx, "date") else str(idx)[:10]
             for idx in df.index]
    ser = {"dates": dates, "rsi": {}, "macd": {}}
    for per in sorted(set(int(x) for x in periods)):
        ser["rsi"][per] = [float(v) for v in bot.rsi(close, per)]
    for p in MACD_SETS:
        line, sig = bot.macd(close, *p)
        ser["macd"][p] = ([float(v) for v in line], [float(v) for v in sig])
    return ser


def fp_match(ser: dict, fp: dict, splits=None, w0: str = W0, w1: str = W1,
             mult: float = TOL_MULT) -> list:
    """مرشّحو البصمة: `[{date, params, diff}]` — **صفرُ نظرٍ مستقبليّ** (قيمةُ اليوم نفسِه)."""
    if not ser or not ser.get("dates"):
        return []
    out = []
    dates = ser["dates"]
    if fp["kind"] == "rsi":
        per = int(fp["params"][0])
        seq = (ser.get("rsi") or {}).get(per)
        if seq is None:
            return []
        want, tol = fp["vals"][0], fp["tol"][0] * mult
        for i, d in enumerate(dates):
            if not (w0 <= d <= w1):
                continue
            v = seq[i]
            if v != v:                                            # NaN
                continue
            diff = abs(v - want)
            if diff <= tol:
                out.append({"date": d, "params": (per,), "diff": round(diff, 6)})
        return out
    sets = (fp["params"],) if fp["params"] else MACD_SETS
    for p in sets:
        if p not in ser["macd"]:
            continue
        line, sig = ser["macd"][p]
        for i, d in enumerate(dates):
            if not (w0 <= d <= w1):
                continue
            f = bot._split_scale_factor(splits, d) if splits is not None else 1.0
            if not f:
                continue
            want = [v / f for v in fp["vals"]]
            tols = [t * mult / f for t in fp["tol"]]
            got = [line[i], sig[i]]
            if len(want) == 3:
                got.append(line[i] - sig[i])
            if any(g != g for g in got):                          # NaN
                continue
            diffs = [abs(g - w) for g, w in zip(got, want)]
            if all(dv <= tv for dv, tv in zip(diffs, tols)):
                out.append({"date": d, "params": p, "diff": round(max(diffs), 6)})
    return out


def judge(cands: list) -> str:
    return "unique" if len(cands) == 1 else ("ambiguous" if cands else "none")


def price_witness(hist, splits_of=None) -> dict:
    """`{(symbol, line): date}` من **مرساة السعر مُعادةً في التشغيلة نفسِها**.

    شاهدُ هُويّةٍ حيّ: لا يُقرأ من ملفٍّ قد يغيب أو يبيت، بل يُحسَب بدوالّ
    `faisal_price_anchor` **بالاسم** على الشموع نفسِها ⇒ أيُّ اختلافٍ بين
    المصدرين يظهر `DISAGREE` ولا يُطوى."""
    out = {}
    for t in pa.targets():
        a, sym, ln = t["anchor"], t["symbol"], t["line"]
        df = (hist or {}).get(sym)
        if not a or df is None or len(df) <= MIN_BARS:
            continue
        sp = splits_of(sym) if splits_of else None
        cands = pa.match_days(pa._bars_of(df), a, sp)
        if len(cands) == 1:
            out[(sym, ln)] = cands[0]["date"]
    return out


# ═══════════════ ② المسار الحيّ ════════════════════
def collect(scope: str = "all") -> list:
    """لكلّ هدفٍ: بصماتُه اليوميّة من كتلته (بلا شبكة)."""
    lines = open(CAT, encoding="utf-8").read().splitlines()
    out = []
    for t in targets(scope):
        blk = symbol_block(lines, t["line"], t["symbol"])
        fps, skipped = [], Counter()
        for ln, txt in blk:
            for fp in parse_fingerprints(txt, t["frame"]):
                if fp["frame"] == "daily":
                    fp["at_line"] = ln
                    fps.append(fp)
                else:
                    skipped[fp["frame"]] += 1
        fps, conflict = resolve_conflicts(fps)
        out.append({**t, "fps": fps, "skipped": dict(skipped), "conflict": conflict})
    return out


def main() -> int:
    scope = (os.environ.get("IND_SCOPE") or "all").strip().lower()
    if scope not in ("all", "gov"):
        log(f"⛔ نطاقٌ غيرُ معروف: {scope!r} (المسموح: all · gov)")
        return 2
    log("📅📉 التأريخُ ببصمة المؤشّر (قراءةٌ فقط · RSI ثابتٌ تحت القياس · MACD مُسوًّى بالتقسيم)")
    tg = collect(scope)
    with_fp = [t for t in tg if t["fps"]]
    log(f"   النطاق: {scope} · أهداف: {len(tg)} (رمز·سطر) غيرُ مؤرَّخة · "
        f"منها ببصمةٍ **يوميّة**: {len(with_fp)}")
    nsk = Counter()
    for t in tg:
        for k, v in t["skipped"].items():
            nsk[k] += v
    if nsk:
        log(f"   بصماتٌ مُتروكةٌ لفريمها (لا شموعَ لها عندنا): {dict(nsk)}")
    ncf = Counter()
    for t in tg:
        for k in t.get("conflict") or []:
            ncf[k] += 1
    if ncf:
        log(f"   أنواعٌ مُسقَطةٌ لتضارب قراءتين في الكتلة (إسنادٌ مجهول): {dict(ncf)}")
    syms = sorted({t["symbol"] for t in with_fp if t["symbol"]})
    hist = bot.download_history(syms, start_override=WARMUP) if syms else {}
    _sp_cache = {}

    def splits_of(sym):
        if sym not in _sp_cache:
            try:
                _sp_cache[sym] = bot._fetch_splits(sym)
            except Exception:                                     # noqa: BLE001
                _sp_cache[sym] = None
        return _sp_cache[sym]

    price_dates = price_witness(hist, splits_of)
    rows, sens, agree = [], {m: Counter() for m in SENS_MULTS}, Counter()
    for t in tg:
        sym, ln = t["symbol"], t["line"]
        row = {"symbol": sym, "line": ln, "frame": t["frame"],
               "n_fp": len(t["fps"]), "kinds": ",".join(sorted({f["kind"] for f in t["fps"]})),
               "recorded": " | ".join(f["raw"] for f in t["fps"]),
               "verdict": "no_fp", "date": "", "n_cand": "", "diff": "", "params": "",
               "candidates": "", "price_date": price_dates.get((sym, ln), ""), "witness": ""}
        df = (hist or {}).get(sym)
        if t["fps"] and df is not None and len(df) > MIN_BARS:
            splits = splits_of(sym)
            pers = {int(f["params"][0]) for f in t["fps"] if f["kind"] == "rsi"}
            ser = build_series(df, sorted(pers) or (RSI_PERIOD,))
            inter = None
            for fp in t["fps"]:
                got = {c["date"] for c in fp_match(ser, fp, splits)}
                inter = got if inter is None else (inter & got)
            cands = sorted(inter or set())
            best = {}
            for fp in t["fps"]:
                for c in fp_match(ser, fp, splits):
                    if c["date"] in cands:
                        best.setdefault(c["date"], c)
            row["n_cand"] = len(cands)
            row["candidates"] = " | ".join(cands[:8])
            row["verdict"] = judge(cands)
            if len(cands) == 1:
                d = cands[0]
                row["date"] = d
                row["diff"] = best.get(d, {}).get("diff", "")
                row["params"] = str(best.get(d, {}).get("params", ""))
            for m in SENS_MULTS:
                it = None
                for fp in t["fps"]:
                    g = {c["date"] for c in fp_match(ser, fp, splits, mult=m)}
                    it = g if it is None else (it & g)
                sens[m][judge(sorted(it or set()))] += 1
            if row["price_date"]:
                if row["verdict"] == "unique":
                    ok = row["date"] == row["price_date"]
                    row["witness"] = "AGREE" if ok else "DISAGREE"
                    agree[row["witness"]] += 1
                else:
                    row["witness"] = "no_unique"
                    agree["no_unique"] += 1
        elif t["fps"]:
            row["verdict"] = "no_data"
        rows.append(row)
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    log("")
    log("   الرمز   سطر   بصمات  أنواع      الحكم       التاريخ       فرق        شاهد")
    for r in rows:
        if r["verdict"] in ("no_fp",):
            continue
        log(f"   {r['symbol']:6s} {r['line']:<5} {r['n_fp']:<6} {r['kinds']:<10s} "
            f"{r['verdict']:<10s} {r['date']:<13s} {str(r['diff']):<10s} {r['witness']}")
        if r["verdict"] == "ambiguous":
            log(f"          ⟶ مرشَّحات ({r['n_cand']}): {r['candidates']}")
    log("")
    for m in SENS_MULTS:
        c = sens[m]
        log(f"SENS mult={m:g}× unique={c['unique']} ambiguous={c['ambiguous']} none={c['none']}")
    log(f"WITNESS agree={agree['AGREE']} disagree={agree['DISAGREE']} no_unique={agree['no_unique']}")
    c = Counter(r["verdict"] for r in rows)
    log(f"JUDGE scope={scope} unique={c['unique']} ambiguous={c['ambiguous']} none={c['none']} "
        f"no_fp={c['no_fp']} no_data={c['no_data']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
