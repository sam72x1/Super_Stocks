# -*- coding: utf-8 -*-
"""🏦 `T-HRT` — «اي سهم يتخارج منه صندوق hrt يعطي 200٪ بالراحه» (العقد `hrt_prereg.md` + الملحق `§⑪`).

**قراءةٌ/بحثٌ فقط · صفرُ مسٍّ بالإنتاج · لا `LOGIC_VERSION` · ولا يُشحَن شيءٌ مهما كانت
النتيجة.** والعقدُ ينصّ: **لا فرعَ يُثبت الدعوى** — ذراعٌ وصفيّةٌ تُجيب «أحصادٌ أماميّ أم إغلاق؟».

🔗 **وكلُّ مستورَدٍ يُنادى بالاسم (‏«بُنيت لـ…» في الملحق §⑪-ⓑ و-ⓝ):**
`link100_probe.splits_of` · `market_calendar.session_info` و`is_trading_day` · `kasih_scan.wilson`
و`NY` · `optrade_arms.no_config_assign` · `tc_yield_arms.production_untouched` ·
و`Super_stock.SEC_UA` (هويّةُ SEC نفسُها).
🔴 **و`selfcheck_readonly`/`importers` نسختان محلّيّتان** مطابقتان سلوكيًّا لنظيرتيهما في
`waves_probe` (قفلُ تكافؤ `HRA11`): استيرادُهما منه يجعل هذي الأداةَ **مستوردةً لأداة الموجات**
فيُسقط حارسَها `V-W6`-ب — أمسكه `WVA1` قبل الدمج (§⑪-ⓝ).

**رموزُ الخروج (§⑪-ⓜ):** 0 حكم (الفرعُ 1 أو 2) · 2 مفتاحٌ غائب · 5 حارس (`V-H5` · `V-H6`) ·
7 الهُويّة (`V-H1`) · 9 «لا قياس» (الفرعُ 3 — ومنه `V-H2` و`V-H4`) · **8 المحورُ مُغلَق**.

🔒🔴 **والمحورُ مُغلَقٌ بـ«اقفل HRT» (‏2026-09-24 · `hrt_result.md §⑦`):** الحكمُ صدر الفرعَ 3
«لا قياس» والانتظارُ لا يرفعه، فالأداةُ تخرج **‏8** قبل أيّ عمليّة، و`HRT_REOPEN=1`
**إقرارٌ بشروط الفتح الثلاثة لا التفافٌ عليها** (يُقرأ `1` حرفيًّا).
"""
from __future__ import annotations

import ast
import csv
import datetime as dt
import os
import re
import statistics
import time
from collections import Counter

import requests

from kasih_scan import NY, wilson                               # بالاسم
from link100_probe import splits_of                             # بالاسم
from market_calendar import is_trading_day, session_info        # بالاسم
from optrade_arms import no_config_assign                       # بالاسم
from Super_stock import SEC_UA                                  # بالاسم — هويّةُ SEC
from tc_yield_arms import production_untouched                  # بالاسم

# ───────────────────────── الثوابتُ المُغلَقة بالعقد ──────────────────────────
OWNER_CIK = 1475597                       # §①-ⓐ `HRT FINANCIAL LP`
OWNER_KEY = "HRT FINANCIAL"               # `V-H1`
SCOPE_FROM, SCOPE_TO = "2026-01-01", "2026-09-23"   # §② — وما بعده لا يدخل
OLD_FROM = "2023-01-01"                   # إيداعاتُ 2023-2025 تُطبَع ولا تُعَدّ
FOLD = 20                                 # §② الطيّ بالجلسات
WIN = 20                                  # §② `mr20`
HIT200_X, HIT100_X = 3.0, 2.0             # ‏+200% · ‏+100%
PRE_N = 5                                 # §⑪-ⓘ `pre5`
SPLIT_PRE = 3                             # §② تقسيمٌ في [t0−3، t0+20] ⇒ استبعاد
SPLIT_POST = 20                           # §② الطرفُ الأعلى حرفيًّا (ويمتدّ بإزاحة p0 — §⑪-ⓟ)
MIN_ARM = 20                              # §⑤-3 أرضيّةُ كلّ ذراعٍ حاكمة
HR2_UP = 50.0                             # §④ `HR2` (‏`engineering`)
MIN_EDGAR = 0.95                          # `V-H2`
MIN_PRICE = 0.90                          # `V-H4`
WHLR_SYM = "WHLR"                         # §⑪-ⓙ خارج العدّ في كلّ الأذرع
HP3_PRE5 = 30.0                           # §⑨ `HP3`
HP4_LO, HP4_HI = 30, 60                   # §⑨ `HP4`
LOOKBACK_SESS = PRE_N + 2                 # جلساتٌ قبل `t0` تُجلَب لـ`pre5`
SHIFT_SESS = 3                            # احتياطُ إزاحةِ `p0` إلى جلسةٍ تالية
SEC_SLEEP = 0.15                          # SEC ‏≤10 طلباتٍ/ثانية
OUT_ROWS = "hrt_rows.tsv"
COMMON_RE = re.compile(r"\bcommon\b|\bordinary\b", re.I)
ARMS = ("exit", "buy", "f3")              # `S-EXIT` · `C-BUY` · `C-F3` (و`C-SELF` لكلّ مُصدِر)
ARM_NAME = {"exit": "S-EXIT", "buy": "C-BUY", "f3": "C-F3", "self": "C-SELF"}

RC_OK, RC_NOKEY, RC_GUARD, RC_IDENT, RC_NOJUDGE = 0, 2, 5, 7, 9

# ═══════════ 🔒 إغلاقُ المحور — «اقفل HRT» (‏2026-09-24، بالتفويض الكامل) ═══════════
#   الحكمُ صدر **الفرعَ 3 «لا قياس»** (‏`hrt_result.md` · التشغيلة ‏35950256119) والانتظارُ
#   لا يرفعه (‏19 · 10 دون 20) ⇒ إغلاقٌ **يُنفَّذ لا يُكتَب** بنمط `T-WAVES §⑨` حرفيًّا: الأداةُ
#   تخرج ‏8 **قبل** أيّ سطرٍ أو قراءةِ مفتاحٍ أو نداءِ EDGAR أو جلب.
AXIS_CLOSED = True
REOPEN_ENV = "HRT_REOPEN"
CLOSED_RC = 8            # مميَّزٌ عمدًا عن 0/2/5/7/**9 «لا قياس»**


def _closed_now() -> bool:
    """أمُغلَقٌ الآن؟ — المفتاحُ يُقرأ **وقت النداء** لا وقت الاستيراد.

    🔒 **والإقرارُ `1` حرفيًّا** (سابقةُ `SESSIONS_REOPEN`/`WAVES_REOPEN`): مُدخَلُ الـworkflow
    افتراضُه `0` ويصل البيئةَ نصًّا غيرَ فارغ ⇒ لو فُحص «غيرُ فارغ» **لارتفع الإغلاقُ في كلّ
    تشغيلة** وهو يبدو مُغلَقًا. **ويُقرأ باسمه الحرفيّ** فيراه قفلُ البيئة `HRA9`."""
    return AXIS_CLOSED and (os.environ.get("HRT_REOPEN") or "").strip() != "1"


def closure_notice() -> list:
    """نصُّ الإغلاق — **دالّةٌ نقيّة** ليُقفَل مضمونُها لا شكلُها."""
    return [
        "🔒🔴 **محورُ «اي سهم يتخارج منه صندوق hrt يعطي 200٪» (`T-HRT`) مُغلَق** — "
        "«اقفل HRT» (‏2026-09-24 · بالتفويض الكامل) · `hrt_result.md §⑦`.",
        "",
        "⚖️ **السبب — بالأرقام لا بالرأي** (`hrt_result.md` · التشغيلةُ الحاكمة ‏35950256119):",
        "   • **الفرعُ 3 «لا قياس»:** خروجٌ مقيسٌ **‏14** وشراءٌ **‏6** دون أرضيّة ‏20 · "
        "**والانتظارُ لا يرفعه** (اكتمالُ المعلَّق ‏19 · 10).",
        "   • **ووصفيًّا لا حكمًا:** `S-EXIT` **‏0 من 14** بلغ ‏+200% في 20 جلسة (سقفُ ويلسون ‏21.5%) — "
        "ولو أصاب المستبعَدُ بالتقسيم كلُّه فالأقصى ‏19 من 33 ⇒ ليس «أيَّ سهم».",
        "   • **و«hrt» صانعُ سوقٍ (`HRT FINANCIAL LP`) لا صندوق** · وإيداعاتُه Form 3/4.",
        "",
        "🔓 **ولا يُعاد فتحُه إلّا بثلاثةٍ معًا (`hrt_result.md §⑦`):**",
        "   ① **مصدرٌ جديدٌ للدعوى غيرُ الحديث المنقول (`TG_50826`)** — وإعادةُ تشغيل الذراع "
        "على الدعوى نفسِها ليست مصدرًا.",
        "   ② **تسجيلٌ مسبقٌ جديد** — العقدُ الحاليُّ مدموجٌ لا يُعدَّل، ولا يُرخى فيه حدٌّ رُئيت قيمتُه "
        "(‏الأرضيّة 20 · ‏+200% · نافذةُ 20 جلسة · 50%).",
        "   ③ **إذنُ المالك**.",
        "   ⚖️ والمفتاحُ `HRT_REOPEN=1` **إقرارٌ بالثلاثة لا التفافٌ عليها** — ويُقرأ `1` حرفيًّا.",
    ]


def log(m: str = "") -> None:
    print(m, flush=True)


# ───────────────────────── حرّاسٌ (`V-H5` · `V-H6`) ───────────────────────────
def selfcheck_readonly(src: str | None = None) -> bool:
    """`V-H5` — **قراءةٌ فقط** بالـAST: صفرُ إرسالٍ وصفرُ كتابةِ حالة. ما لا يُثبَت أنه قراءةٌ
    **يُعَدّ كتابة** (وضعٌ متغيّرٌ يُرفَض) · والكتابةُ لا تمرّ إلّا إلى `OUT_ROWS`.
    🔒 مطابقةٌ سلوكيًّا لـ`waves_probe.selfcheck_readonly` (‏`HRA11`)."""
    write_ok = {"OUT_ROWS"}
    if src is None:
        src = open(os.path.abspath(__file__), encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        name = getattr(n.func, "id", None) or getattr(n.func, "attr", None) or ""
        if name in ("send_telegram", "send_telegram_document", "git_save",
                    "save_watchlist", "save_op_entry_state", "record_new_alerts"):
            return False
        if name == "open":
            mode = n.args[1] if len(n.args) > 1 else None
            for kw in n.keywords or []:
                if kw.arg == "mode":
                    mode = kw.value
            if mode is None:
                continue
            if not (isinstance(mode, ast.Constant) and isinstance(mode.value, str)):
                return False
            if set(mode.value) <= set("rbt"):
                continue
            tgt = n.args[0] if n.args else None
            if not (isinstance(tgt, ast.Name) and tgt.id in write_ok):
                return False
    return True


def importers(root: str = ".", me: str = "hrt_arms") -> list:
    """`V-H6` — ملفّاتُ المستودع (المستوى الأعلى) التي **تستورد** هذي الأداة، بالـAST.
    تُستثنى السويّةُ والأداةُ نفسُها · **وملفٌّ لا يُحلَّل يُعَدّ مستوردًا** (فاشلٌ-مغلق).
    🔒 مطابقةٌ سلوكيًّا لـ`waves_probe.importers` (‏`HRA11`)."""
    out = []
    for fn in sorted(os.listdir(root)):
        if not fn.endswith(".py") or fn in (me + ".py", "test_bot.py"):
            continue
        try:
            tree = ast.parse(open(os.path.join(root, fn), encoding="utf-8").read())
        except (OSError, SyntaxError, ValueError):
            out.append(fn)
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Import) and any(a.name.split(".")[0] == me for a in n.names):
                out.append(fn)
                break
            if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == me:
                out.append(fn)
                break
    return out


# ───────────────────────── الدوالُّ النقيّة: الإيداع ─────────────────────────
def _v(block: str, tag: str):
    m = re.search(rf"<{tag}>\s*(?:<value>\s*)?([^<]*)", block or "", re.S)
    return m.group(1).strip() if m else None


def _num(x):
    try:
        return float(str(x).replace(",", ""))
    except (TypeError, ValueError):
        return None


def parse_filing(txt: str) -> dict:
    """نصُّ إيداع Form 3/4 الكامل ⟵ حقولُه — نقيّة. والمالكون **كلُّهم** (الإيداعُ المشترك)."""
    t = txt or ""
    acc = re.search(r"<ACCEPTANCE-DATETIME>\s*(\d{14})", t)
    rows = []
    for b in re.findall(r"<nonDerivativeTransaction>(.*?)</nonDerivativeTransaction>", t, re.S):
        rows.append({"title": _v(b, "securityTitle"), "date": _v(b, "transactionDate"),
                     "code": (_v(b, "transactionCode") or "").upper(),
                     "shares": _num(_v(b, "transactionShares")),
                     "price": _num(_v(b, "transactionPricePerShare"))})
    ciks = []
    for c in re.findall(r"<rptOwnerCik>\s*([^<]+)", t):
        try:
            ciks.append(int(c.strip()))
        except ValueError:
            continue
    return {"acc_dt": acc.group(1) if acc else None,
            "doc": (_v(t, "documentType") or "").upper(),
            "symbol": (_v(t, "issuerTradingSymbol") or "").upper(),
            "issuer_cik": (_v(t, "issuerCik") or "").lstrip("0"),
            "owner_ciks": ciks,
            "owners": [x.strip() for x in re.findall(r"<rptOwnerName>\s*([^<]+)", t)],
            "rows": rows}


def owner_ok(p: dict) -> bool:
    """`V-H1`: `CIK 1475597` بين المالكين **واسمٌ يحمل `HRT FINANCIAL`**."""
    return (OWNER_CIK in (p.get("owner_ciks") or [])
            and any(OWNER_KEY in (n or "").upper() for n in (p.get("owners") or [])))


def acceptance_ny(s14):
    """`ACCEPTANCE-DATETIME` (‏EDGAR بتوقيت الشرق) ⟵ لحظةٌ بتوقيت نيويورك — أو `None`."""
    try:
        return dt.datetime.strptime(str(s14), "%Y%m%d%H%M%S").replace(tzinfo=NY)
    except (TypeError, ValueError):
        return None


def is_common(title) -> bool:
    """§⑪-ⓒ «سهمٌ عاديّ»: العنوانُ يحمل `common` أو `ordinary`."""
    return bool(title) and COMMON_RE.search(str(title)) is not None


def classify(form: str, rows: list):
    """§⑪-ⓓ: `exit` (‏S) · `buy` (‏P بلا S) · `f3` (‏Form 3) — على السهم العاديّ غير المشتقّ ·
    والتعديلاتُ وما سواها ⇒ `None`."""
    f = str(form or "").strip().upper()
    if f == "3":
        return "f3"
    if f != "4":
        return None
    codes = {r.get("code") for r in rows or [] if is_common(r.get("title"))}
    if "S" in codes:
        return "exit"
    if "P" in codes:
        return "buy"
    return None


# ───────────────────────── الدوالُّ النقيّة: الجلسات ─────────────────────────
def is_session(d: dt.date) -> bool:
    return d.weekday() < 5 and is_trading_day(d.isoformat())


def next_session(d: dt.date) -> dt.date:
    d = d + dt.timedelta(days=1)
    while not is_session(d):
        d += dt.timedelta(days=1)
    return d


def prev_session(d: dt.date) -> dt.date:
    d = d - dt.timedelta(days=1)
    while not is_session(d):
        d -= dt.timedelta(days=1)
    return d


def shift(d: dt.date, n: int) -> dt.date:
    """الجلسةُ رقم `n` بعد `d` (سالبٌ = قبله) — `d` جلسةٌ أو لا."""
    for _ in range(abs(n)):
        d = next_session(d) if n > 0 else prev_session(d)
    return d


def gap_sessions(a: dt.date, b: dt.date) -> int:
    """عددُ الجلسات في (a، b] — والمعكوسُ صفر."""
    n, d = 0, a
    while d < b:
        d = next_session(d)
        if d <= b:
            n += 1
    return n


def close_min(d: dt.date) -> int:
    cm = session_info(d.isoformat()).get("close_ny_min")
    return cm if isinstance(cm, int) else 16 * 60


def t0_session(t0: dt.datetime) -> dt.date:
    """§⑪-ⓔ: قبولٌ قبل إغلاق يومِ تداول (‏`session_info` — 13:00 يومَ الإغلاق المبكّر) ⇒ ذلك اليوم،
    وإلّا يومُ التداول التالي."""
    d = t0.date()
    if is_session(d) and t0.hour * 60 + t0.minute < close_min(d):
        return d
    return next_session(d)


def fold(items: list, gap: int = FOLD) -> list:
    """§⑪-ⓕ: حلقةٌ جديدةٌ للمُصدِر **فقط** إن بعدت جلستُها أكثرَ من `gap` جلسةً عن جلسة
    **آخر** إيداعٍ مؤهَّل له (لا عن بدء الحلقة). `items` فيها `issuer` · `sess` · `t0`."""
    last, eps = {}, []
    for it in sorted(items, key=lambda x: x["t0"]):
        prev = last.get(it["issuer"])
        if prev is None or gap_sessions(prev, it["sess"]) > gap:
            eps.append(dict(it, folded=1))
        else:
            eps[max(i for i, e in enumerate(eps) if e["issuer"] == it["issuer"])]["folded"] += 1
        last[it["issuer"]] = it["sess"]
    return eps


# ───────────────────────── الدوالُّ النقيّة: السعر ────────────────────────────
def regular_by_session(bars: list) -> dict:
    """{يوم: [(t, o, h, l, c)…]} للدقائق **النظاميّة** وحدَها بحدود `session_info` لكلّ يوم."""
    out: dict = {}
    for b in bars or []:
        try:
            t, o, h, lo, c = int(b[0]), float(b[1]), float(b[2]), float(b[3]), float(b[4])
        except (TypeError, ValueError, IndexError):
            continue
        m = dt.datetime.fromtimestamp(t / 1000, tz=NY)
        d = m.date()
        if not is_session(d):
            continue
        info = session_info(d.isoformat())
        op, cl = info.get("open_ny_min"), info.get("close_ny_min")
        mod = m.hour * 60 + m.minute
        if op is None or cl is None or not (op <= mod < cl):
            continue
        out.setdefault(d, []).append((t, o, h, lo, c))
    for v in out.values():
        v.sort()
    return out


def outcome(bars: list, t0: dt.datetime, win: int = WIN, shift_max: int = SHIFT_SESS) -> dict:
    """`p0` · `mr20` · `pre5` لحلقةٍ واحدة (§② · §⑪-ⓔ ⓖ ⓘ) — نقيّة.

    ترجّع `p0=None` إن لم توجد دقيقةٌ نظاميّةٌ عند `t0` أو بعده خلال `shift_max` جلسات."""
    reg = regular_by_session(bars)
    t0_ms = int(t0.timestamp() * 1000)
    s = t0_session(t0)
    p0 = p0_t = p0_s = None
    for _ in range(shift_max + 1):
        cand = [b for b in reg.get(s, []) if b[0] >= t0_ms]
        if cand:
            p0_t, p0, p0_s = cand[0][0], cand[0][1], s
            break
        s = next_session(s)
    res = {"p0": p0, "p0_session": p0_s, "shifted": (p0_s != t0_session(t0)) if p0_s else None,
           "mr20": None, "last_session": None, "sessions_seen": 0, "pre5": None}
    # §⑪-ⓘ «آخرُ إغلاقٍ نظاميٍّ قبل `t0`» = إغلاقُ الجلسة السابقة لجلسة `t0` في كلّ الحالات:
    #   قبولٌ أثناء الجلسة ⇒ جلستُه لم تُغلق · وبعد الإغلاق أو في عطلة ⇒ جلستُه التالية.
    c0_s = prev_session(t0_session(t0))
    c5_s = shift(c0_s, -PRE_N)
    if reg.get(c0_s) and reg.get(c5_s) and reg[c5_s][-1][4] > 0:
        res["pre5"] = (reg[c0_s][-1][4] / reg[c5_s][-1][4] - 1.0) * 100.0
    if p0 is None or p0 <= 0:
        return res
    sess = [p0_s]
    while len(sess) < win:
        sess.append(next_session(sess[-1]))
    res["last_session"] = sess[-1]
    highs = [b[2] for d in sess for b in reg.get(d, []) if b[0] >= p0_t]
    res["sessions_seen"] = sum(1 for d in sess if reg.get(d))
    if highs:
        res["mr20"] = (max(highs) / p0 - 1.0) * 100.0
    return res


def split_window(s0: dt.date, last_session=None) -> tuple:
    """§② حرفيًّا: [جلسة `t0` − 3، جلسة `t0` + 20] — **ويمتدّ الطرفُ الأعلى إلى آخر جلسةٍ في نافذة
    `mr20` إن تجاوزته بإزاحة `p0`** (§⑪-ⓟ · تشديدٌ لا إرخاء: تقسيمٌ داخل نافذة القياس الفعليّة
    يُفسد `mr20` على شموعٍ غيرِ مُسوّاة)."""
    lo, hi = shift(s0, -SPLIT_PRE), shift(s0, SPLIT_POST)
    if last_session and last_session > hi:
        hi = last_session
    return lo, hi


def split_blocked(sp, first: dt.date, last: dt.date):
    """§②: تقسيمٌ تاريخُه في [first، last] ⇒ `True` · `None` إن تعذّر الفحص (يُعَدّ)."""
    if sp is None:
        return None
    for d, _rev in sp:
        try:
            dd = dt.date.fromisoformat(str(d)[:10])
        except ValueError:
            continue
        if first <= dd <= last:
            return True
    return False


def asof_session(now_ny: dt.datetime) -> dt.date:
    """آخرُ جلسةٍ **مكتملة** عند لحظة التشغيل (نيويورك)."""
    d = now_ny.date()
    if is_session(d) and now_ny.hour * 60 + now_ny.minute >= close_min(d):
        return d
    return prev_session(d)


def rate(eps: list, key: str = "hit200") -> tuple:
    """(k، n، %، Wilson) على الحلقات **المقيسة** وحدَها."""
    m = [e for e in eps if e.get("status") == "measured"]
    k = sum(1 for e in m if e.get(key))
    n = len(m)
    return k, n, (100.0 * k / n if n else None), wilson(k, n)


def read_branch(ex: tuple, by: tuple, guard_ok: bool) -> tuple:
    """فروعُ §⑤ — ثلاثةٌ لا غير. `ex`/`by` = (k، n، %، Wilson)."""
    if not guard_ok or ex[1] < MIN_ARM or by[1] < MIN_ARM:
        return 3, "لا قياس"
    if ex[2] > by[2] and ex[3][1] >= HR2_UP:
        return 1, "إشارةٌ وصفيّةٌ موجبة (ليس إثباتًا)"
    return 2, "لا ميزة"


def predictions(ex: tuple, by: tuple, pre5_med, n_exit_eps: int) -> dict:
    """حسمُ `HP1`-`HP4` آليًّا (§⑪-ⓛ)."""
    out = {}
    if ex[1] and by[1]:
        overlap = ex[3][0] <= by[3][1] and by[3][0] <= ex[3][1]
        out["HP1"] = "مؤكَّد" if (overlap or ex[2] <= by[2]) else "مكذَّب"
    else:
        out["HP1"] = "لا يُحسَم"
    out["HP2"] = ("مؤكَّد" if ex[3][1] < HR2_UP else "مكذَّب") if ex[1] else "لا يُحسَم"
    out["HP3"] = "لا يُحسَم" if pre5_med is None else (
        "مؤكَّد" if pre5_med > HP3_PRE5 else "مكذَّب")
    out["HP4"] = "مؤكَّد" if HP4_LO <= n_exit_eps <= HP4_HI else "مكذَّب"
    return out


# ───────────────────────── الجالبون (الحيّ — تُحقَن بدائلُهم للاختبار) ─────────
def sec_get(url: str):
    """نصُّ صفحة SEC بهويّة `SEC_UA` — أو `None` (يُعَدّ ولا يُصمَت)."""
    time.sleep(SEC_SLEEP)
    try:
        r = requests.get(url, headers=SEC_UA, timeout=40)
    except Exception:                                            # noqa: BLE001
        return None
    return r.text if getattr(r, "status_code", 0) == 200 else None


def px_get(sym: str, frm: str, to: str, key: str):
    """شموعُ الدقيقة لمدى [frm، to] بـ`adjusted=false` ويُتبَع `next_url` — أو `None`."""
    url = (f"https://api.polygon.io/v2/aggs/ticker/{sym.upper()}/range/1/minute/{frm}/{to}"
           "?adjusted=false&sort=asc&limit=50000")
    out = []
    try:
        for _ in range(20):
            r = requests.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=40)
            if getattr(r, "status_code", 0) != 200:
                return out or None
            j = r.json() or {}
            out += [(int(b["t"]), b["o"], b["h"], b["l"], b["c"]) for b in j.get("results") or []
                    if b.get("t") is not None and b.get("h") is not None]
            url = j.get("next_url")
            if not url:
                break
    except Exception:                                            # noqa: BLE001
        return out or None
    return out or None


def list_filings(get) -> tuple:
    """قائمةُ إيداعات المالك (‏`recent` ثمّ `files`) ⟵ ([(نموذج، تاريخ، رقم)]، أخطاء)."""
    import json                                                  # noqa: PLC0415
    base = f"https://data.sec.gov/submissions/CIK{OWNER_CIK:010d}.json"
    txt = get(base)
    if not txt:
        return [], 1
    j = json.loads(txt)
    parts, errs = [j.get("filings", {}).get("recent", {})], 0
    for fobj in j.get("filings", {}).get("files", []) or []:
        t = get("https://data.sec.gov/submissions/" + str(fobj.get("name", "")))
        if not t:
            errs += 1
            continue
        parts.append(json.loads(t))
    out = []
    for p in parts:
        for f, d, a in zip(p.get("form", []), p.get("filingDate", []),
                           p.get("accessionNumber", [])):
            out.append((str(f), str(d), str(a)))
    return sorted(set(out), key=lambda x: (x[1], x[2])), errs


def filing_url(acc: str) -> str:
    return (f"https://www.sec.gov/Archives/edgar/data/{OWNER_CIK}/"
            f"{acc.replace('-', '')}/{acc}.txt")


# ───────────────────────── التشغيل ───────────────────────────────────────────
def run(key: str, *, sec=None, px=None, splits=None, now=None, prod=None, imp=None,
        dry: bool = False, write_rows: bool = True) -> int:
    """المسارُ كاملًا **بجالبين محقونين** (للاختبار بلا شبكة) — والافتراضُ هو الحيّ بالاسم."""
    sec = sec or sec_get
    px = px or (lambda s, a, b: px_get(s, a, b, key))
    splits = splits or (lambda s: splits_of(s, key))
    now = now or dt.datetime.now(tz=NY)
    prod = prod or production_untouched
    imp = imp or (lambda: importers(".", "hrt_arms"))

    log("🏦 `T-HRT` — «اي سهم يتخارج منه صندوق hrt يعطي 200٪ بالراحه» (العقد hrt_prereg.md + §⑪)")
    log(f"   المالك CIK {OWNER_CIK} · النطاق {SCOPE_FROM} ⟶ {SCOPE_TO} · الطيّ {FOLD} · النافذة {WIN} "
        f"جلسة · ‏+200% · الأرضيّة {MIN_ARM} · HR2 {HR2_UP:g}% (engineering)")

    # ── `V-H5`/`V-H6` قبل أيّ جلب ──────────────────────────────────────────
    src = open(os.path.abspath(__file__), encoding="utf-8").read()
    ro, nc = selfcheck_readonly(src), no_config_assign(src)
    prod_ok, cur, base = prod()
    who = imp()
    log(f"   🔒 V-H5 قراءةٌ فقط={ro} · صفرُ إسنادٍ إلى CONFIG={nc} · V-H6 الإنتاجُ بت-بت={prod_ok} "
        f"({cur} مقابل {base}) · مستوردو الأداة={who or 'لا أحد'} · SEC_UA مضبوط="
        f"{'contact@example.com' not in str(SEC_UA.get('User-Agent'))}")
    if not (ro and nc and prod_ok) or who:
        log(f"⛔ حارسٌ ساقطٌ قبل أيّ جلب — خروج {RC_GUARD}")
        return RC_GUARD
    if not dry and not key:
        log(f"⛔ POLYGON_API_KEY غائب ⇒ خروج {RC_NOKEY} (وضعُ الجدوى لا يحتاجه)")
        return RC_NOKEY

    # ── EDGAR: القائمة ثمّ الإيداعات ────────────────────────────────────────
    lst, lerr = list_filings(sec)
    inscope = [x for x in lst if SCOPE_FROM <= x[1] <= SCOPE_TO and x[0] in ("3", "4")]
    amends = Counter(x[0] for x in lst if SCOPE_FROM <= x[1] <= SCOPE_TO and x[0] in ("3/A", "4/A"))
    old4 = [x for x in lst if OLD_FROM <= x[1] < SCOPE_FROM and x[0] == "4"]
    log(f"\n① EDGAR: إيداعاتٌ مُدرجة {len(lst)} (أخطاءُ صفحات {lerr}) · في النطاق Form 3/4 أصليّة "
        f"{len(inscope)} · تعديلات (تُعَدّ ولا تدخل) {dict(amends) or 0} · Form 4 في 2023-2025 {len(old4)}")
    parsed, bad_owner, miss = [], [], 0
    for form, fdate, acc in inscope:
        t = sec(filing_url(acc))
        if not t:
            miss += 1
            continue
        p = parse_filing(t)
        p.update(form=form, fdate=fdate, acc=acc)
        if not owner_ok(p):
            bad_owner.append(acc)
        parsed.append(p)
    cover = (len(parsed) / len(inscope)) if inscope else 0.0
    log(f"   🔒 V-H2 تغطيةُ EDGAR {len(parsed)} من {len(inscope)} = {cover * 100:.1f}% (الحدّ "
        f"{MIN_EDGAR * 100:g}%)")
    log(f"   🔒 V-H1 هُويّةُ المالك: {len(parsed) - len(bad_owner)} من {len(parsed)} = CIK "
        f"{OWNER_CIK} + «{OWNER_KEY}»" + (f" · ساقطة: {bad_owner[:5]}" if bad_owner else ""))
    if bad_owner:
        log(f"⛔ V-H1 — إيداعٌ ليس لـHRT ⇒ خروج {RC_IDENT}")
        return RC_IDENT
    for form, fdate, acc in old4:
        p = parse_filing(sec(filing_url(acc)) or "")
        codes = sorted({r["code"] for r in p["rows"] if r.get("code")})
        log(f"   📜 خارج العدّ {fdate} Form {form} {p.get('symbol') or '?'} رموز={codes or '—'}")

    # ── التصنيف ثمّ الطيّ ───────────────────────────────────────────────────
    titles_in, titles_out = Counter(), Counter()
    items = {a: [] for a in ARMS}
    first_any = {}
    for p in parsed:
        t0 = acceptance_ny(p.get("acc_dt"))
        if t0 is None:
            continue
        for r in p["rows"]:
            (titles_in if is_common(r.get("title")) else titles_out)[str(r.get("title"))] += 1
        iss = p.get("issuer_cik") or p.get("symbol")
        first_any.setdefault(iss, (t0, p.get("symbol")))
        if t0 < first_any[iss][0]:
            first_any[iss] = (t0, p.get("symbol"))
        arm = classify(p["form"], p["rows"])
        if arm is None:
            continue
        tx = [r.get("date") for r in p["rows"] if r.get("code") in ("S", "P") and r.get("date")]
        items[arm].append({"arm": arm, "issuer": iss, "sym": p.get("symbol"), "acc": p["acc"],
                           "t0": t0, "sess": t0_session(t0), "tx_date": max(tx) if tx else None})
    log("   العناوينُ المعدودة «سهمًا عاديًّا»: " + (" · ".join(f"{k}={v}" for k, v in titles_in.most_common(6)) or "—"))
    log("   العناوينُ المستبعَدة: " + (" · ".join(f"{k}={v}" for k, v in titles_out.most_common(6)) or "لا شيء"))
    eps = {a: fold(items[a]) for a in ARMS}
    whlr = {a: [e for e in eps[a] if e.get("sym") == WHLR_SYM] for a in ARMS}
    eps = {a: [e for e in eps[a] if e.get("sym") != WHLR_SYM] for a in ARMS}
    tx_ok = sum(1 for e in eps["exit"] if e["tx_date"] and e["tx_date"] <= e["t0"].date().isoformat())
    log("\n② الحلقاتُ بعد الطيّ (خارج WHLR): " +
        " · ".join(f"{ARM_NAME[a]} {len(eps[a])} (من {len(items[a])} إيداعًا)" for a in ARMS) +
        f" · مُصدِرون {len(first_any)}")
    log(f"   🔒 V-H3 `t0` من القبول وحدَه: تاريخُ العمليّة سبق `t0` في {tx_ok} من {len(eps['exit'])} "
        "حلقةَ خروج (المتوقَّع كلُّها)")
    log("   🔒 V-H7 WHLR خارج العدّ: " + " · ".join(
        f"{ARM_NAME[a]} {[e['acc'] for e in whlr[a]] or '—'}" for a in ARMS))
    asof = asof_session(now)
    pend_proj = sum(1 for e in eps["exit"] if shift(e["sess"], WIN - 1) > asof)
    log(f"   آخرُ جلسةٍ مكتملة {asof} · حلقاتُ خروجٍ ستُعلَّق (إسقاطًا) {pend_proj} من {len(eps['exit'])}")
    if dry:
        log("\n🧪 وضعُ الجدوى — EDGAR وحدَه · **صفرُ سعرٍ وصفرُ نسبة**.")
        return RC_OK

    # ── الأسعار ─────────────────────────────────────────────────────────────
    sp_cache, rows_out, px_ok, px_need = {}, [], 0, 0

    def measure(e, arm):
        nonlocal px_ok, px_need
        sym = e.get("sym") or ""
        s0 = e["sess"]
        frm = shift(s0, -LOOKBACK_SESS)
        to = shift(s0, WIN + SHIFT_SESS)
        bars = px(sym, frm.isoformat(), to.isoformat()) if sym else None
        o = outcome(bars or [], e["t0"])
        e.update(o)
        if arm in ("exit", "buy"):
            px_need += 1
            px_ok += 1 if o["p0"] else 0
        if sym not in sp_cache:
            sp_cache[sym] = splits(sym) if sym else None
        blk = split_blocked(sp_cache[sym], *split_window(s0, o["last_session"]))
        if o["p0"] is None:
            e["status"] = "noprice"
        elif blk is None:
            e["status"] = "split_unknown"
        elif blk:
            e["status"] = "split"
        elif o["last_session"] and o["last_session"] > asof:
            e["status"] = "pending"
        elif o["mr20"] is None:
            e["status"] = "noprice"
        else:
            e["status"] = "measured"
        e["hit200"] = e["status"] == "measured" and o["mr20"] >= (HIT200_X - 1) * 100
        e["hit100"] = e["status"] == "measured" and o["mr20"] >= (HIT100_X - 1) * 100
        rows_out.append(e)

    for a in ARMS:
        for e in eps[a]:
            measure(e, a)
    selfeps = []
    for iss, (t_first, sym) in sorted(first_any.items(), key=lambda x: x[1][0]):
        if sym == WHLR_SYM:
            continue
        end = shift(t0_session(t_first), -WIN)
        start = shift(end, -(WIN - 1))
        e = {"arm": "self", "issuer": iss, "sym": sym, "acc": "—",
             "t0": dt.datetime.combine(start, dt.time(9, 30), tzinfo=NY), "sess": start,
             "tx_date": None}
        measure(e, "self")
        selfeps.append(e)
    cover_px = (px_ok / px_need) if px_need else 0.0
    log(f"\n③ الأسعار: 🔒 V-H4 تغطيةُ `p0` للذراعين الحاكمتين {px_ok} من {px_need} = "
        f"{cover_px * 100:.1f}% (الحدّ {MIN_PRICE * 100:g}%)")
    for a in list(ARMS) + ["self"]:
        pool = eps.get(a, selfeps) if a != "self" else selfeps
        st = Counter(e.get("status") for e in pool)
        log(f"   {ARM_NAME[a]}: " + " · ".join(f"{k}={v}" for k, v in sorted(st.items())))

    # ── الحكم (§④ · §⑤) ─────────────────────────────────────────────────────
    ex, by = rate(eps["exit"]), rate(eps["buy"])
    f3, sf = rate(eps["f3"]), rate(selfeps)
    guard_ok = cover >= MIN_EDGAR and cover_px >= MIN_PRICE
    br, why = read_branch(ex, by, guard_ok)
    pre = [e["pre5"] for e in eps["exit"] if e.get("status") == "measured" and e.get("pre5") is not None]
    pre_med = statistics.median(pre) if pre else None
    mr = [e["mr20"] for e in eps["exit"] if e.get("status") == "measured"]
    log("\n④ HR1/HR2 — ‏+200% في 20 جلسةً بعد `p0`:")
    for nm, r in (("S-EXIT 🥇", ex), ("C-BUY 🥇", by), ("C-F3", f3), ("C-SELF", sf)):
        pct = "—" if r[2] is None else f"{r[2]:.1f}%"
        log(f"   {nm}: {r[0]} من {r[1]} = {pct} · Wilson [{r[3][0]:.1f}, {r[3][1]:.1f}]")
    h1 = rate(eps["exit"], "hit100")
    log(f"   وصفيّ: hit100(خروج) {h1[0]} من {h1[1]} · وسيطُ mr20(خروج) "
        f"{statistics.median(mr):.1f}%" if mr else "   وصفيّ: لا mr20 مقيس")
    log("   وصفيّ: وسيطُ pre5(خروج) " + ("—" if pre_med is None else f"{pre_med:.1f}%") +
        f" على {len(pre)} حلقة")
    hp = predictions(ex, by, pre_med, len(eps["exit"]))
    log("   التنبّؤات: " + " · ".join(f"{k} {v}" for k, v in hp.items()))
    if write_rows:
        with open(OUT_ROWS, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, delimiter="\t")
            w.writerow(["arm", "issuer", "sym", "acc", "t0", "sess", "p0_session", "p0", "mr20",
                        "pre5", "status", "hit200", "hit100", "folded"])
            for e in rows_out:
                w.writerow([e["arm"], e["issuer"], e.get("sym"), e.get("acc"), e["t0"].isoformat(),
                            e["sess"], e.get("p0_session"), e.get("p0"), e.get("mr20"),
                            e.get("pre5"), e.get("status"), int(bool(e.get("hit200"))),
                            int(bool(e.get("hit100"))), e.get("folded")])
    log(f"\nJUDGE branch={br} ({why}) exit={ex[0]}/{ex[1]} buy={by[0]}/{by[1]} "
        f"edgar={cover * 100:.1f}% price={cover_px * 100:.1f}% " +
        " ".join(f"{k}={v}" for k, v in hp.items()))
    return RC_NOJUDGE if br == 3 else RC_OK


def main() -> int:
    # 🔒 الحارسُ **قبل أيّ سطرٍ أو قراءةِ مفتاحٍ أو نداءِ EDGAR أو جلب** (‏«اقفل HRT»).
    if _closed_now():
        for _ln in closure_notice():
            log(_ln)
        return CLOSED_RC
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    dry = (os.environ.get("HRT_DRY") or "").strip() == "1"
    rows = (os.environ.get("HRT_TSV") or "1").strip() != "0"
    return run(key, dry=dry, write_rows=rows)


if __name__ == "__main__":
    raise SystemExit(main())
