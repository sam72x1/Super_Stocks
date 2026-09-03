# -*- coding: utf-8 -*-
"""🌙⏱️ **رادارُ ما قبل الجلسة الممتدّة** — قائمةٌ قبل الافتر/البري بعشر دقائق.

أمرُ المالك 2026-09-03 حرفيًّا: «قبل الافتر و البري بـ10 دقايق توصلني قايمة بالأسهم
اللي متوقع انها تنفجر بعد 10 دقايق من بداية البري او الافتر».

**متى:** لحظتا قرارٍ في يوم التداول بتوقيت نيويورك — **15:50** (قبل الافتر 16:00)
و**03:50** (قبل البريماركت 04:00). ولكلٍّ دِدوبٌ مرّةً واحدة في اليوم.

**كيف:** ① نداءٌ واحدٌ لكلّ السوق (`/v2/aggs/grouped`) مرشِّحًا رخيصًا (سعرُ الكون
‏[`MIN_PRICE`, `SPLIT_RADAR_PRICE_MAX`] ‏+ أعلى دولارِ يومٍ) ② ثم شموعُ الدقيقة
**للمرشَّحين وحدَهم** ③ والميزاتُ من `presession_feats` — **المصدرِ الواحد الذي
يقيسه `presession_scan`** فلا يُقاس شيءٌ ويُرسَل غيرُه.

🔴 **حدُّ صدقٍ يُقرأ مع كلّ رسالة: الحكمُ صدر و«فشلت» على النافذة الحاكمة.**
`presession_result.md`: ‏`PM · 10د` رافعتُها **‏29.8×** و`R@10` **‏11.5%** وتعبر
ثلاثةً من أربعة — **والساقطُ `P@10` المطلق** (دون 1%). ⇒ القائمةُ **قيد الإثبات
الأماميّ** ولا تُقرأ توصيةَ دخول.
🔴 **والإرسالُ لجلسةٍ بعينها بأمر المالك «شغّل البريماركت» (2026-09-03):**
`PRESESSION_SEND` تقبل اسمَ الجلسة (`PM` · `AH` · `PM,AH`) أو `1`/`all` للجميع،
والفارغُ **صامتٌ يكتب السجلَّ الأماميّ وحدَه**. المشحونُ اليوم **`PM`**.
🔴 **ومفتاحُ الترتيب لكلّ جلسةٍ مفتاحُه** (`presession_feats.rank_key`): البريماركتُ
`post_hi_ret` **مختارًا من سنتَي المعايرة وحدهما**، والافترُ يبقى على خطّ الأساس
`usd_day` لأن `post_*` معدومةٌ بالتعريف في قرار 15:50.

🔒 **إشعارٌ/عرضٌ فقط:** خارج الفرز والجذور · لا يكتب قائمةً ولا يمسّ حالةَ البوت
(الدِدوبُ نطاقٌ داخل ددوب «هنا الدخول» القائم) · **فاشلٌ-آمنٌ مطلق**: بلا مفتاحِ
Polygon أو عند أيّ عطلٍ ⇒ صفرُ عمل، والعاملُ الحيُّ يمضي كما هو.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import time

import presession_feats as PF

STAMP_PREFIX = "PRE:"          # نطاقُ الدِدوب داخل حالة «هنا الدخول» — لا ملفَّ جديد
LEDGER_FILE = "presession_ledger.jsonl"
GATE_WIDTH = 6                 # عرضُ نافذة القرار بالدقائق (دورةُ العامل ‏≈60ث)
PREFILTER_CAP = 60             # كم مرشَّحًا تُجلَب لهم شموعُ الدقيقة (كلفةٌ مُعلَنة)
MIN_DAY_USD = 100_000.0        # engineering — أرضيةُ مرشِّحٍ رخيصة (تُعلَن لا تُخفى)
BUDGET_SEC = 45.0              # ميزانيةُ الجلب — تُعلَن ويُطبَع ما قُصّ بها
AH_OPEN, REG_OPEN, REG_CLOSE = 16 * 60, 9 * 60 + 30, 16 * 60


# ── دوالُّ نقيّة ───────────────────────────────────────────────────────────────
def slot_now(mod_ny: int) -> str | None:
    """أيُّ قرارٍ نحن فيه؟ `"AH"` في [15:50، 15:56) · `"PM"` في [03:50، 03:56) ·
    وإلّا `None`. (النافذةُ ستُّ دقائقَ لأن دورةَ العامل ‏≈60 ثانية.)"""
    try:
        m = int(mod_ny)
    except (TypeError, ValueError):
        return None
    ah = REG_CLOSE - PF.DECISION_LEAD
    pm = PF.PRE_OPEN - PF.DECISION_LEAD
    if ah <= m < ah + GATE_WIDTH:
        return "AH"
    if pm <= m < pm + GATE_WIDTH:
        return "PM"
    return None


def stamp_key(day_iso: str, slot: str) -> str:
    return f"{STAMP_PREFIX}{day_iso}:{slot}"


def send_enabled(slot: str, env_val: str | None) -> bool:
    """هل تُرسَل قائمةُ **هذي الجلسة**؟ (أمرُ المالك «شغّل البريماركت» 2026-09-03)

    `PRESESSION_SEND` تقبل: أسماءَ جلساتٍ (`PM` · `AH` · `PM,AH`) — أو `1`/`true`/
    `all`/`yes` **للجميع** (توافقٌ خلفيّ مع الشكل القديم). **والفارغُ صامت**:
    يُكتَب السجلُّ الأماميّ ولا تُرسَل رسالة.
    🔒 **دالّةٌ نقيّةٌ واحدة** — فالبوّابةُ تُختبَر بالورقة، ولا تُكتَب مقارنةُ
    البيئة في نقطة النداء فتتفرّق قراءتان (درسُ «مقياسٌ واحدٌ لا اثنان»)."""
    v = str(env_val or "").strip().upper()
    if not v:
        return False
    parts = {p for p in v.replace(",", " ").replace(";", " ").split() if p}
    if parts & {"1", "TRUE", "ALL", "YES"}:
        return True
    return str(slot or "").strip().upper() in parts


def prefilter(grouped: list, lo: float, hi: float, cap: int = PREFILTER_CAP,
              min_usd: float = MIN_DAY_USD) -> list:
    """المرشِّحُ الرخيص من نداءٍ واحدٍ لكلّ السوق: كونُ السعر ثم أعلى دولارِ يوم.
    نقيّة. `grouped` صفوفُ Polygon (`T,o,h,l,c,v,n,vw`). تُرجع قائمةَ قواميس."""
    out = []
    for g in (grouped or []):
        try:
            sym = str(g.get("T") or "").strip().upper()
            c, v = float(g.get("c")), float(g.get("v") or 0.0)
        except (TypeError, ValueError):
            continue
        if not sym or c <= 0 or not (lo <= c <= hi):
            continue
        usd = c * v
        if usd < min_usd:
            continue
        out.append({PF.ROW_SYM: sym, "close": c, "usd": usd,
                    "o": g.get("o"), "h": g.get("h"), "l": g.get("l"),
                    "n": g.get("n"), "v": v})
    out.sort(key=lambda r: (-r["usd"], r[PF.ROW_SYM]))
    return out[:cap] if cap else out


def ny_mod(ms: int) -> tuple:
    """(تاريخُ نيويورك، دقيقتُه من منتصف الليل) لطابعٍ بالملّي — يتصيّف ذاتيًّا."""
    try:
        from zoneinfo import ZoneInfo
        n = dt.datetime.fromtimestamp(int(ms) / 1000.0, dt.timezone.utc)
        ny = n.astimezone(ZoneInfo("America/New_York"))
        return ny.date().isoformat(), ny.hour * 60 + ny.minute
    except Exception:                                            # noqa: BLE001
        return None, None


def to_bars8(res: list) -> list:
    """صفوفُ Polygon ⟶ عقدُ `presession_feats` الثمانيّ `(ms,o,h,l,c,v,n,mod)`."""
    out = []
    for b in (res or []):
        try:
            ms = int(b.get("t"))
            o, h = float(b.get("o")), float(b.get("h"))
            lo, c = float(b.get("l")), float(b.get("c"))
            v = float(b.get("v") or 0.0)
            n = float(b.get("n") or 0.0)
        except (TypeError, ValueError):
            continue
        day, mod = ny_mod(ms)
        if day is None:
            continue
        out.append((ms, o, h, lo, c, v, n, mod))
    out.sort(key=lambda x: x[0])
    return out


def as_bars8(res: list) -> list:
    """🔒 **مُوحِّدُ عقدِ الجالب.** `run_presession` يقبل جالبًا محقونًا، وعقدُ
    الثمانيّ `(ms,o,h,l,c,v,n,mod)` كان **مضمرًا**: جالبٌ يُرجع صفوفَ Polygon
    الخام (قواميس) أو سباعيًّا بلا `mod` كان **ينهار** بـ`IndexError` داخل
    `split_bars` — وهو صنفُ «الشكل المتخيَّل» بعينه، كشفه تشغيلٌ من طرفٍ إلى طرف
    لا القراءة. الإنتاجُ لم يكن مصابًا (`polygon_minutes` تُوحّد بنفسها) ⇒
    **توسيعٌ لا تغييرُ سلوك**: الثمانيُّ يمرّ **كما هو بت-بت**.
    """
    out = []
    for b in (res or []):
        if isinstance(b, dict):
            out.extend(to_bars8([b]))
            continue
        try:
            n = len(b)
        except TypeError:
            continue
        if n >= 8:
            out.append(b)
        elif n == 7:
            day, mod = ny_mod(b[0])
            if day is not None:
                out.append(tuple(b) + (mod,))
    out.sort(key=lambda x: x[0])
    return out


def split_bars(bars8: list, day_iso: str) -> tuple:
    """(بريماركت، نظاميّ، افتر) ليومٍ بعينه — بدقيقة نيويورك لا بالساعة UTC."""
    pre = [b for b in bars8 if PF.PRE_OPEN <= b[7] < REG_OPEN]
    reg = [b for b in bars8 if REG_OPEN <= b[7] < REG_CLOSE]
    post = [b for b in bars8 if REG_CLOSE <= b[7] < PF.EXT_CLOSE]
    return pre, reg, post


def feature_row(sym: str, bars8: list, prev_close: float, slot: str, cut: int,
                liq_fn=None, win: int = 65) -> dict | None:
    """صفُّ قرارٍ واحد — الميزاتُ من `presession_feats` حصرًا (المصدرُ الواحد).
    `cut` دقيقةُ القرار بنيويورك (‏950 للافتر · 1200 لقرار البريماركت من يوم أمس)."""
    if not bars8:
        return None
    pre, reg, post = split_bars(bars8, None)
    reg_cut = [b for b in reg if b[7] < min(cut, REG_CLOSE)]
    pre_cut = [b for b in pre if b[7] < cut]
    try:
        f = PF.core_feats(reg_cut, pre_cut, prev_close, min(cut, REG_CLOSE))
    except PF.LookAhead:
        return None
    if not f:
        return None
    if slot == "PM":
        f.update(PF.post_feats([b for b in post if b[7] < cut], reg_cut[-1][4],
                               sum(b[5] for b in bars8)))
        ref = f.get("post_last") or reg_cut[-1][4]
    else:
        ref = reg_cut[-1][4]
    if liq_fn is not None:
        f["anchor"] = anchor_via([b for b in bars8 if b[7] < cut], liq_fn, win)
    f.update({PF.ROW_SYM: sym, "ref": ref, PF.ROW_SESS: slot})
    return f


def anchor_via(bars8: list, liq_fn, win: int) -> int:
    """`⚓` هل أطلقت **بوّابةُ الإنتاج** مِرساةَ سيولةٍ على شموعِ ما قبل القرار؟

    🔒 `liq_fn` هي `Super_stock.liq_stage_events` **بالاسم** (تُحقَن من المُنادي كي
    تبقى هذي الوحدةُ نقيّةً بلا استيرادٍ ثقيل)، والمِشيةُ **نفسُ مِشية**
    `kasih_scan.first_anchor` (شريحةُ `bars[max(0,k-win):k]` وأوّلُ `M1`) — تكافؤٌ
    مقفولٌ سلوكيًّا في السويّة فلا تصير على المِرساة قراءتان.
    """
    if not bars8 or liq_fn is None:
        return 0
    try:
        bd = [{"t": b[0], "o": b[1], "h": b[2], "l": b[3], "c": b[4], "v": b[5]}
              for b in bars8]
        st = {}
        for k in range(3, len(bd) + 1):
            evs, st = liq_fn(bd[max(0, k - int(win)):k], st)
            for e in (evs or []):
                if e.get("stage") == "M1":
                    return 1
        return 0
    except Exception:                                            # noqa: BLE001
        return 0


def build_presession_alert(rows: list, slot: str, day_iso: str, cov: int,
                           scanned: int) -> str:
    """رسالةُ القائمة — بشكل كروت البوت المضغوطة، وبحدّ صدقٍ في ذيلها."""
    if not rows:
        return ""
    name = "الافتر (16:00)" if slot == "AH" else "البريماركت (04:00)"
    out = [f"🌙⏱️ <b>قبل {name} بعشر دقائق</b> — {len(rows)} اسمًا",
           f"‏🩺 مسحٌ: {scanned} رمزًا في كون السعر · {cov} بشموعِ دقيقة", ""]
    for i, r in enumerate(rows, 1):
        pct = r.get("day_ret")
        line = [f"‏<b>{i}. ${r['sym']}</b> · 📡 {r['ref']:.4f}"]
        if pct is not None:
            line.append(("صاعدٌ " if pct >= 0 else "هابطٌ ") + f"{abs(pct) * 100:.0f}% عن الأمس")
        if r.get("usd_day"):
            line.append(f"💰 ${r['usd_day']:,.0f}")
        if r.get("anchor"):
            line.append("⚓ مِرساةُ سيولةٍ اليوم")
        if r.get("n5"):
            line.append(f"‏{int(r['n5'])} دقيقةَ رفعة")
        out.append(" · ".join(line))
    # 🔴 **حدُّ الصدق يتبع مفتاحَ الجلسة لا رقمًا مغروسًا**: البريماركتُ مفتاحُه
    #    مختارٌ من سنتَي المعايرة وأرقامُه خارجَ العيّنة تُقال كما هي · والافترُ
    #    على خطّ الأساس. **وفي الحالتين: الحكمُ «فشلت» على النافذة الحاكمة.**
    _rk = PF.rank_key(slot)
    _thr = PF.rank_floor(slot)
    if _thr is not None:
        # 🎚️ **الشرطُ يُقال بالعربية لا يُترَك ضمنيًّا** — وإلّا رأى المالكُ اسمًا
        #    واحدًا (أو صفرًا) ولا يعرف لماذا. وبلا علامات مقارنة (قاعدة العرض).
        out += ["", f"‏🎚️ <b>الأرضية:</b> لا يصلك إلّا مَن ارتفع <b>افترُ أمسِه "
                f"{_thr * 100:.1f}% فأكثر</b> — والليلةُ التي لا يعبرها أحدٌ "
                "<b>تُسلَّم صفرًا</b> (‏26% من ليالي 2025). مُعايَرةٌ على "
                "2023-2024 وحدهما · <code>topk_result.md</code>."]
    # 🔴 **وحدُّ الصدق يتبع الشكلَ المشحون لا شكلًا سابقًا:** أرقامُ «‏100 من 2,500»
    #    تصف تسليمَ **عشرةِ أسماءٍ بالرتبة** — وبعد شحن الأرضية صار المُسلَّم غيرَه،
    #    فإبقاؤها كان سيجعل السطرَ **يصف تسليمًا لا نُسلّمه** (‏«سطرُ عرضٍ يكذب»).
    if _thr is not None:
        why = ("الأوّلُ في سنتَي المعايرة 2023-2024 · وبأرضيته على 2025 خارج "
               "العيّنة أصاب ‏47 من 435 اسمًا (‏10.8%) = ‏47 من 878 منفجرًا")
    elif _rk != PF.RANK_KEY:
        why = ("الأوّلُ في سنتَي المعايرة 2023-2024 · وعلى 2025 خارج العيّنة أصاب "
               "‏100 من 2,500 اسمًا (‏4.0%) = ‏100 من 878 منفجرًا")
    else:
        why = "خطُّ الأساس نفسُه"
    out += ["", f"‏⚠️ <b>قيد الإثبات الأماميّ</b> — الترتيبُ بـ<code>{_rk}</code> "
            f"({why}). <b>وحكمُ <code>T-PRESESSION</code> بمقياسه المسجَّل: فشلت.</b> "
            "لا تُقرأ توصيةَ دخول.",
            # 🔴🔴 **تصحيحُ المالك 2026-09-03:** كان هذا السطر يقول «النافذةُ
            #    المقيسة: أوّلُ عشر دقائق» — وهو خطأُ قراءتي لأمره. **العشرُ دقائقَ
            #    موعدُ الرسالة، والتوقّعُ على الجلسة كاملةً.**
            f"‏🗓️ قرارُ {day_iso} · <b>التوقّعُ على الجلسة كاملةً</b> "
            + ("(‏16:00 ⟶ 20:00 نيويورك)" if slot == "AH"
               else "(‏04:00 ⟶ 09:30 نيويورك)")
            + " — والعشرُ دقائقُ موعدُ الرسالة لا مدّةُ التوقّع."]
    return "\n".join(out)


# ── الجلبُ (فاشلٌ-آمنٌ مطلق) ──────────────────────────────────────────────────
def _key() -> str:
    return (os.environ.get("POLYGON_API_KEY") or "").strip()


def polygon_grouped(day_iso: str, requests_mod=None):
    """كلُّ السوق في نداءٍ واحد — `/v2/aggs/grouped/locale/us/market/stocks/{d}`.
    فاشلٌ-آمن ⟶ `None`."""
    key = _key()
    if not key:
        return None
    try:
        rq = requests_mod
        if rq is None:
            import requests as rq                                # noqa: PLC0415
        r = rq.get(f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/"
                   f"stocks/{day_iso}?adjusted=true",
                   headers={"Authorization": f"Bearer {key}"}, timeout=20)
        if r.status_code != 200:
            return None
        return (r.json() or {}).get("results") or None
    except Exception:                                            # noqa: BLE001
        return None


def polygon_minutes(sym: str, frm_ms: int, to_ms: int, requests_mod=None):
    """شموعُ دقيقةٍ بمدًى صريح **مع `n` (عددُ الصفقات)** — فاشلٌ-آمن ⟶ `None`.
    (‏`S.polygon_minute_bars` لا تحفظ `n` ونافذتُها بالدقائق من الآن، ولا تكفي
    قرارَ البريماركت الذي يقرأ يومَ أمس كاملًا.)"""
    key = _key()
    if not key:
        return None
    try:
        rq = requests_mod
        if rq is None:
            import requests as rq                                # noqa: PLC0415
        r = rq.get(f"https://api.polygon.io/v2/aggs/ticker/{sym.upper()}"
                   f"/range/1/minute/{int(frm_ms)}/{int(to_ms)}"
                   f"?adjusted=true&sort=asc&limit=50000",
                   headers={"Authorization": f"Bearer {key}"}, timeout=15)
        if r.status_code != 200:
            return None
        return to_bars8((r.json() or {}).get("results") or [])
    except Exception:                                            # noqa: BLE001
        return None


# ── الوصلةُ الحيّة ────────────────────────────────────────────────────────────
def run_presession(slot: str, day_iso: str, now_ms: int, *, fetch_grouped=None,
                   fetch_minutes=None, prev_closes: dict = None, price_lo: float = None,
                   price_hi: float = None, cap: int = PREFILTER_CAP, log=None,
                   liq_fn=None, win: int = 65, budget_sec: float = BUDGET_SEC,
                   clock=None):
    """يُرجع `(rows, msg, diag)`. لا يرسل ولا يكتب — القرارُ للمُنادي."""
    _log = log or (lambda *_a, **_k: None)
    fg = fetch_grouped or polygon_grouped
    fm = fetch_minutes or polygon_minutes
    lo = price_lo if price_lo is not None else 0.40
    hi = price_hi if price_hi is not None else 10.0
    # قرارُ البريماركت يقرأ **يومَ التداول السابق** (اليومُ الحاليُّ لم يبدأ بعد).
    src_day = day_iso
    if slot == "PM":
        d = dt.date.fromisoformat(day_iso) - dt.timedelta(days=1)
        while d.weekday() >= 5:
            d -= dt.timedelta(days=1)
        src_day = d.isoformat()
    grouped = fg(src_day)
    if not grouped:
        return [], "", {"reason": "grouped_missing", "src_day": src_day}
    cands = prefilter(grouped, lo, hi, cap)
    _log(f"🌙 {slot}: كون {len(grouped)} ⟶ مرشَّحون {len(cands)} (يوم {src_day})")
    cut = PF.EXT_CLOSE if slot == "PM" else REG_CLOSE - PF.DECISION_LEAD
    frm = now_ms - 36 * 3600 * 1000
    rows, cov, cut_off = [], 0, 0
    _now = clock or time.time
    _t0 = _now()
    for c in cands:
        # ⏱️ **ميزانيةٌ مُعلَنة**: خيطُ العامل يخدم مسحَ السيولة أيضًا، فلا يُؤخَّر
        #    بجلبٍ مفتوح. ما يُقصّ **يُطبَع بعدده** (لا قصَّ صامتًا).
        if budget_sec and (_now() - _t0) >= float(budget_sec):
            cut_off = len(cands) - cands.index(c)
            break
        bars = as_bars8(fm(c[PF.ROW_SYM], frm, now_ms))
        if not bars:
            continue
        bars = [b for b in bars if ny_mod(b[0])[0] == src_day]
        if not bars:
            continue
        cov += 1
        pc = (prev_closes or {}).get(c[PF.ROW_SYM])
        if not pc:
            pre, reg, _ = split_bars(bars, src_day)
            pc = (reg[0][1] if reg else (pre[0][1] if pre else None))
        r = feature_row(c[PF.ROW_SYM], bars, pc, slot, cut, liq_fn=liq_fn, win=win)
        if r:
            rows.append(r)
    if cut_off:
        _log(f"⚠️ ميزانيةُ {budget_sec:g}ث قصّت {cut_off} مرشَّحًا — يُعلَن ولا يُصمت.")
    # 🔭 **السجلُّ يرى كلَّ مرتَّبٍ لا العشرةَ وحدَهم** (‏2026-09-03، عقد
    #    `presession_dev_prereg §⑥-1`): كان يُرجَع `top` فيستحيل أن يُجاب
    #    «هل انفجر اسمٌ لم يدخل العشرة؟» — وهو **سؤالُ صحّةِ المفتاح نفسِه**.
    #    الترتيبُ كاملًا يُرجَع، و`top` **شريحتُه الأولى بت-بت** (‏`order_rows`
    #    بـ`k=0` تُرجع كلَّ المرتَّبين ثم القطعُ شريحةٌ ⇒ صفرُ تغييرٍ في القرار).
    ordered = PF.order_rows(rows, PF.rank_key(slot), 0, PF.RANK_ASC)
    top = ordered[:PF.TOPK]
    # 🎚️ **أرضيةُ التسليم** (أمرُ المالك «شغّل الأرضية» 2026-09-03): لا تُرسَل
    #    إلّا القراءةُ المتطرّفة — والليلةُ التي لا متطرّفَ فيها **تُسلَّم صفرًا**.
    # 🔒 وهي على **مفتاح الترتيب نفسِه** ⇒ ترشيحُها بعد القطع يكافئ ترشيحَها قبله
    #    بالبناء (مقفولٌ سلوكيًّا) ⇒ **المُرسَلُ هو عينُ ما قِيس في `topk_result`**.
    deliver = PF.apply_floor(top, slot)
    msg = build_presession_alert(deliver, slot, day_iso, cov, len(cands))
    return ordered, msg, {"scanned": len(cands), "cov": cov, "rows": len(rows),
                          "ranked": len(ordered),
                          "src_day": src_day, "cut_off": cut_off,
                          "floor": PF.rank_floor(slot),
                          "top": [r[PF.ROW_SYM] for r in top],
                          "deliver": [r[PF.ROW_SYM] for r in deliver],
                          "floor_cut": len(top) - len(deliver)}


def append_ledger(rows: list, slot: str, day_iso: str, path: str = LEDGER_FILE,
                  sent: bool = False, delivered=None) -> int:
    """السجلُّ الأماميّ — يُلحَق فقط (حصادُه يحكم لاحقًا). فاشلٌ-آمن ⟶ 0.

    🎚️ **و`sent` لكلّ صفٍّ لا للدفعة** (‏2026-09-03): بعد أرضيةِ التسليم صار
    بعضُ المرتَّبين **يُسجَّل ولا يُرسَل** ⇒ `delivered` مجموعةُ الرموز المُسلَّمة
    فعلًا، ومعها `floor_ok` لكلّ صفّ. **وبلاها يبقى السلوكُ السابق بت-بت**
    (`delivered=None` ⇒ الكلُّ) — فالسجلُّ القديمُ يُقرأ كما هو.
    🔒 **والمقصوصُ يُسجَّل**: بلاه يستحيل قياسُ كلفةِ الأرضية أماميًّا.
    🔭 **و`in_top` يفصل العشرةَ عمّن دونهم** (‏2026-09-03): الصفوفُ تصل **مرتَّبةً**
    فالرتبةُ تكفي حكمًا، ومَن دون القطع يُسجَّل **شاهدًا مضادًّا للمفتاح نفسِه**
    (‏«هل انفجر اسمٌ لم نرتّبه في العشرة؟») — والقديمُ الذي مرّر العشرةَ وحدَهم
    يقرأ `in_top=True` للجميع وهو **صادقٌ لِما مُرِّر**.
    """
    dl = None if delivered is None else {str(x).upper() for x in delivered}
    try:
        with open(path, "a", encoding="utf-8") as fh:
            for i, r in enumerate(rows, 1):
                _ok = PF.floor_ok(r, slot)
                _sym = str(r.get(PF.ROW_SYM) or "").upper()
                fh.write(json.dumps({PF.ROW_DAY: day_iso, PF.ROW_SESS: slot,
                                     "rank": i,
                                     "in_top": i <= PF.TOPK,
                                     "sent": bool(sent) and (dl is None
                                                             or _sym in dl),
                                     "floor": PF.rank_floor(slot),
                                     "floor_ok": bool(_ok),
                                     "key": PF.rank_key(slot),
                                     "ts": int(time.time()),
                                     **{k: v for k, v in r.items()
                                        if k != PF.ROW_SESS}},
                                    ensure_ascii=False) + "\n")
        return len(rows)
    except Exception:                                            # noqa: BLE001
        return 0
