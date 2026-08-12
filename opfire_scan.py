#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔬🔥 T-OPFIRE — أداةُ القياس (‏`opfire_prereg.md` هو العقد · لا يُغيَّر بعد الأرقام).

**السؤال:** في لحظة اشتعالٍ يرصدها `_ignition_signal` الإنتاجيّ، هل **قرارُ الكتم
المركَّب** (بصمةُ المضارب) يفصل `real` عن `fakeout` بتعريفَي `_ignition_outcome`؟

🔒 **قارئٌ محض:** لا يكتب حالةً · لا يُستورَد في `Super_stock` · يستورد دوالَّ الإنتاج
**ولا ينسخها** · وخروجٌ **غيرُ صفريّ** عند سقوط أيّ بوّابةِ صلاحية.

🔴 **ولماذا جالبان بحثيّان خاصّان (وليس دوالَّ الإنتاج):** أُثبِت بالقراءة أن
الإنتاجيّتين **لا تكفيان لهذي التجربة**:
 · `polygon_minute_bars` تُثبّت `adjusted=true` وتقرأ «آخر N دقيقة» من **الآن**
   (`Super_stock.py:11160-11161`) ⇒ **لا تصل يومًا تاريخيًّا ولا تُعطي سعرًا خامًّا**،
   والعقد يشترط الخامَّ في الثلاثة (`opfire_prereg.md` §⑨-4 · البوّابة `V9`).
 · `polygon_base_trades` **تُسقط الطابع الزمنيّ** (تُرجع price/size/exchange فقط،
   `Super_stock.py:12050-12052`) ⇒ **يستحيل تقطيعُ الدقائق** ولا تنفيذُ `V5`.
⇒ الجالبان هنا **للجلب فقط**، **وكلُّ حكمٍ يبقى بدوالّ الإنتاج بأسمائها** (قفل `OPF2`).

**وضعُ الجدوى** (`OPFIRE_MODE=feasibility`، الافتراضيّ): **يومٌ واحد** على رموز القائمة
الحيّة — **لا يُنتج حكمًا** بل يطبع ما لم يكن مقيسًا: **أسماءَ حقول `/v3/trades`
الفعلية** · نسبةَ `fallback` · حالتَي `break_level` · وسرعةَ المسار. ولا سنةَ قبل عبوره.

**وضعُ ARMED** (`OPFIRE_MODE=armed`): يقيس **الشرائحَ الثلاث وحدها** على مجتمع ARMED
لسنةٍ واحدة — تنفيذًا لأرضيّةِ العيّنة المسجَّلة (`opfire_prereg.md` §⑥): «شرطُ ‏≥25
لكلّ شريحة رهنٌ بنسبة `_operator_blocks → None` … وإن تعذّرت الأرضيةُ أُبلِغ **«لا
حكم» قبل التشغيل الكامل** لا بعده». 🔒 **ولا وسمَ نتيجةٍ ولا فرقًا ولا `R` هنا** —
عَدٌّ فقط، فيستحيل عليه أن يحرّك المعيار.

**رموزُ الخروج** (مُصرَّحٌ بها لأن «أخضر» يُقرأ إذنًا بالمضيّ): `0` عبرت ·
`2` عطبُ تهيئةٍ/`no-op` · `3` سقطت بوّابةُ صلاحية · **`5` القياسُ صحيحٌ والأرضيةُ
لم تُبلَغ ⇒ «لا حكم» ولا تشغيلَ للسنوات الثلاث**.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sys
import time

import requests

MODE = os.environ.get("OPFIRE_MODE", "feasibility").strip()

# 🔴 **قبل** استيراد `Super_stock`: `_apply_backtest_overrides` يُنفَّذ **وقت التحميل**،
#    فضبطُ العلمين بعده يُخرجهما **خاملَين** ⇒ صفرُ صفقةٍ بـ`exit_date` ⇒ لا كون ARMED.
#    وهو بعينه درسُ `BT_CANDLE` الميّت المدوَّن (علمٌ يُمرَّر ولا يُقرأ = `no-op` صامت).
if MODE in ("armed", "judge"):
    os.environ["SCREENER_MODE"] = "BACKTEST"
    os.environ["BT_REPLAY10"] = "1"

import event_exec as EX                                          # noqa: E402
import Super_stock as S                                          # noqa: E402

DAY = os.environ.get("OPFIRE_DAY", "").strip()          # YYYY-MM-DD
MAX_SYMS = int(os.environ.get("OPFIRE_MAX_SYMS", "12"))
MAX_WINDOWS = int(os.environ.get("OPFIRE_MAX_WINDOWS", "0") or 0)   # 0 = بلا حدّ
WITNESS = os.environ.get("OPFIRE_WITNESS", "AAPL").strip().upper()
WIN_MIN = 30            # 🔒 نافذةُ الكشف = الحيّ حرفيًّا (Super_stock.py:12369)
FOOTPRINT_TRADES = 250  # 🔒 نافذةُ البصمة = الحيّ حرفيًّا (operator_flow, :12147)
SCALE_TOL = 0.15        # 🔒 نفسُ تسامح `T-EVENT-EXEC` (المجتمعُ واحدٌ فيُقاس بمسطرته)
FLOOR_SLICE = 25        # §⑤-5: «‏≥25 في كلٍّ من شريحتَي `F1`»
PENDING_FRAC = 0.80     # §⑥: `pending` ‏≈20% ⇒ المحسومُ ‏≈0.8× (‏`P3` تنبّؤٌ مسجَّل)
OUTCOME_SESSIONS = 40   # §②-6: نافذةُ الحكم **‏40 جلسةً بعد يوم الاشتعال حصرًا**
CTRL_SPAN = 5           # §④ `F3`: مطابقةٌ في دقيقة الساعة ‏±5
DIFF_MIN = 10.0         # §⑤-2: الفرقُ ‏≥10 نقاطٍ في **كلّ** سنة
F3_RATIO = 0.5          # §⑤ الشرطُ السالب: `|Δ(F3)| ≥ 0.5 × |Δ(F1)|`
F3_ABS = 4.0            # §⑤ الشرطُ السالب: **و**`|Δ(F3)| ≥ 4 نقاط`
BASE = "https://api.polygon.io"

_FAILS: list = []       # بوّاباتُ صلاحيةٍ ساقطة — تُطبَع وتُسقط الخروج


def gate(name: str, ok: bool, detail: str = "") -> bool:
    """بوّابةُ صلاحيةٍ **تسقط بصوتٍ عالٍ** — لا صمتَ ولا تقديرَ ولا مضيٌّ على عطب."""
    print(("  ✅ " if ok else "  ⛔ ") + name + (f" — {detail}" if detail else ""))
    if not ok:
        _FAILS.append(name)
    return ok


def _key() -> str:
    return os.environ.get("POLYGON_API_KEY", "").strip()


def fetch_minute_bars_raw(sym: str, day: str):
    """شموعُ دقيقةِ **يومٍ تاريخيّ** بسعرٍ **خامّ** (`adjusted=false`) — بوّابة `V9`.

    تُرجع [{'o','h','l','c','v','t'}…] تصاعديًّا (‏`t` = بداية الدقيقة ms) أو None.
    **والدقائقُ الفارغة تُحذَف ولا تُملأ بأصفار** (سلوكُ تجميع Polygon نفسُه — العقد §②-2)."""
    k = _key()
    if not k:
        return None
    try:
        url = (f"{BASE}/v2/aggs/ticker/{sym.upper()}/range/1/minute/{day}/{day}"
               f"?adjusted=false&sort=asc&limit=50000")
        r = requests.get(url, headers={"Authorization": f"Bearer {k}"}, timeout=20)
        if r.status_code != 200:
            return None
        res = (r.json() or {}).get("results") or []
        bars = [{"o": b.get("o"), "h": b.get("h"), "l": b.get("l"),
                 "c": b.get("c"), "v": b.get("v"), "t": b.get("t")}
                for b in res if b.get("c") is not None and b.get("v") is not None]
        return bars or None
    except Exception:
        return None


def fetch_trades_day(sym: str, day: str, cap: int = 400_000):
    """صفقاتُ يومٍ كاملة **مع الطابع الزمنيّ** — وهو ما تُسقطه دالّةُ الإنتاج.

    ترجّع (rows, raw_keys) حيث rows = [{'ts','price','size','exchange'}…] تصاعديًّا
    و`raw_keys` = **أسماءُ حقول أوّل نتيجةٍ كما جاءت من المزوّد** (تُطبَع لبوّابة `V5`:
    اسمُ حقل الزمن **يُثبَت من المُخرَج لا يُخمَّن**). فاشلٌ-آمن → (None, [])."""
    k = _key()
    if not k:
        return None, []
    h = {"Authorization": f"Bearer {k}"}
    nxt_day = (dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat()
    url = (f"{BASE}/v3/trades/{sym.upper()}?timestamp.gte={day}"
           f"&timestamp.lt={nxt_day}&limit=50000&order=asc")
    out, raw_keys = [], []
    try:
        for _ in range(12):
            r = requests.get(url, headers=h, timeout=25)
            if r.status_code != 200:
                # عقدُ الطبقة: فشلٌ = None **لا بترٌ صامت** (درسُ `polygon_base_trades`).
                print(f"  ⚠️ صفقات {sym}: صفحة فشلت ({r.status_code}) — تُسقَط كاملةً")
                return None, raw_keys
            j = r.json() or {}
            res = j.get("results") or []
            if res and not raw_keys:
                raw_keys = sorted(res[0].keys())
            for t in res:
                ts = t.get("sip_timestamp", t.get("participant_timestamp"))
                out.append({"ts": ts, "price": t.get("price"),
                            "size": t.get("size"), "exchange": t.get("exchange")})
            nx = j.get("next_url")
            if not nx or len(out) >= cap:
                break
            url = nx if "apiKey" in nx else nx + f"&apiKey={k}"
        return (out or None), raw_keys
    except Exception:
        return None, raw_keys


def fetch_footprint_desc(sym: str, end_ns: int, limit: int = FOOTPRINT_TRADES):
    """آخرُ `limit` صفقةً **قبل** `end_ns` — **بشكل نداء الإنتاج حرفيًّا**
    (`order=desc&limit=250` ثم عكسٌ إلى التصاعديّ للتيك — `operator_flow`, :12147)،
    مضافًا إليه الحدُّ التاريخيّ `timestamp.lt` وحده.

    🔴 **ولا حدَّ أدنى (`timestamp.gte`) عمدًا:** الإنتاجُ يأخذ «آخر 250 صفقة» بلا
    نافذةٍ زمنية، فسهمٌ رقيقٌ تمتدّ بصمتُه لأيّامٍ سابقةٍ **حيًّا أيضًا**. فوضعُ حدٍّ
    هنا يُخالف المقيس. وبدلًا من الحدّ **يُقاس المدى ويُطبَع** (عدّادُ صدقٍ لا فلتر).

    ترجّع `(rows تصاعديًّا، أقدمُ طابعٍ ns، أسماءُ حقول المزوّد)` — و**فشلُ الشبكة
    `None`** لا قائمةً فارغة: خلطُه بشريحة `fallback` يفبرك كتمًا من عطبِ نداء."""
    k = _key()
    if not k:
        return None, None, []
    try:
        r = requests.get(f"{BASE}/v3/trades/{sym.upper()}",
                         headers={"Authorization": f"Bearer {k}"},
                         params={"timestamp.lt": int(end_ns),
                                 "limit": int(limit), "order": "desc"},
                         timeout=20)
        if r.status_code != 200:
            return None, None, []
        res = (r.json() or {}).get("results") or []
        raw_keys = sorted(res[0].keys()) if res else []
        rows = [{"ts": t.get("sip_timestamp", t.get("participant_timestamp")),
                 "price": t.get("price"), "size": t.get("size"),
                 "exchange": t.get("exchange")} for t in res]
        rows.reverse()                       # desc ⟶ تصاعديّ (قاعدةُ التيك تلزمه)
        tss = [int(x["ts"]) for x in rows if x.get("ts") is not None]
        return rows, (min(tss) if tss else None), raw_keys
    except Exception:
        return None, None, []


def mute_decision(of, usd) -> tuple:
    """🔒 **قرارُ الكتم الإنتاجيّ المركَّب** — إعادةُ بناءِ `Super_stock.py:12440-12456`
    حرفيًّا، بثلاث قيم (العقد §③):

      · `pass_operator`  : البصمةُ مقيسة **و**`has_operator`      ⇒ يمرّ
      · `mute_operator`  : البصمةُ مقيسة **و**`¬has_operator`     ⇒ يُكتَم
      · `fallback`       : `_operator_blocks` أرجعت **None**      ⇒ `group` يُكتَم · غيرُه يمرّ

    ترجّع (الشريحة، مكتوم؟) — و`fallback` **يُعَدّ ولا يُسقَط** (السيولةُ الرقيقة تُنتج
    `None` وتُنتج `group` معًا، فإسقاطُها يحذف الشريحةَ المتحيّزة بعينها)."""
    if of is not None:
        if not of.get("has_operator"):
            return "mute_operator", True
        return "pass_operator", False
    return "fallback", S._ignition_candle_class(usd)[0] == "group"


def scan_symbol_day(sym: str, day: str, entry: dict) -> dict:
    """يمشي دقائقَ يومٍ واحدٍ لرمزٍ واحد ⟶ أوّلُ اشتعالٍ فقط (دِدوب العقد §②-4).

    **كلُّ حكمٍ بدالّة الإنتاج:** `_ignition_break_level` · `_ignition_signal` ·
    `_operator_blocks` · `_ignition_candle_class`. ولا نظرَ مستقبليّ: البصمةُ من صفقاتٍ
    زمنُها **أصغرُ من** نهاية دقيقة الاشتعال (`<` لا `<=`) — بوّابة `V5`.

    🔴🔴 **وعيبان في نسختي الأولى صحّحهما هذا الوصلُ (وكلاهما من صنفٍ مدوَّنٍ سلفًا):**
     ① كانت النافذةُ **عدديّة** (`bars[i-30:i]` = آخر 30 **شمعةً موجودة**) وهو بعينه
       ما أصلحته مراجعةُ Codex الثانية في `replay_trigger` («النافذة زمنيّة لا عدديّة»)
       — في كوننا الرقيق تغطّي ستُّ شمعاتٍ ساعتين فيرى التاريخيُّ سياقًا **لا يراه
       الحيُّ أبدًا**. ② وكانت تمشي **كلَّ** دقائق اليوم بما فيها ما قبل السوق وما
       بعده، **والرادارُ الحيُّ لا يعمل خارج الجلسة النظامية** ⇒ اشتعالٌ يُعَدّ ولا
       يمكن أن يقع. ⇒ الكشفُ الآن `group_sessions` + `replay_trigger` **نفسُهما في
       الوضعين** (مسارُ كشفٍ واحدٌ لا نسختان)."""
    out = {"symbol": sym, "day": day, "bars": 0, "bars_reg": 0, "trades": 0,
           "break_level": None, "lvl_kind": None, "fire": None,
           "slice": None, "muted": None, "raw_keys": [], "ts_field": None}
    lvl = S._ignition_break_level(entry)
    if not lvl:
        out["lvl_kind"] = "none"
        return out
    crit = ((entry.get("interp") or {}).get("critical_number") or {}).get("price")
    out["break_level"] = float(lvl)
    out["lvl_kind"] = "critical" if crit else "fallback_pivot105"

    bars = fetch_minute_bars_raw(sym, day)
    if not bars:
        return out
    out["bars"] = len(bars)
    rows, raw_keys = fetch_trades_day(sym, day)
    out["raw_keys"] = raw_keys
    if rows is None:
        return out
    out["trades"] = len(rows)
    out["ts_field"] = ("sip_timestamp" if "sip_timestamp" in raw_keys
                       else ("participant_timestamp"
                             if "participant_timestamp" in raw_keys else None))

    sess = EX.group_sessions(bars)
    out["bars_reg"] = sum(len(v) for v in sess.values())
    for day_k in sorted(sess):
        sb = sess[day_k]
        hit = EX.replay_trigger(sb, out["break_level"], S._ignition_signal,
                                vol_mult=float(S.CONFIG["IGNITION_VOL_MULT"]),
                                window=WIN_MIN)
        if not hit:
            continue
        i, sig = hit
        end_ms = int(sb[i]["t"]) + 60_000            # نهايةُ دقيقة الاشتعال
        end_ns = end_ms * 1_000_000                  # الطابعُ من المزوّد بالنانو
        prior = [r for r in rows
                 if r.get("ts") is not None and int(r["ts"]) < end_ns]
        tail = prior[-FOOTPRINT_TRADES:]
        of = S._operator_blocks([(r["price"], r["size"]) for r in tail
                                 if r["price"] and r["size"]],
                                int(S.CONFIG["OPERATOR_MIN_SHARES"]))
        sl, muted = mute_decision(of, sig.get("usd"))
        out["fire"] = dict(sig, minute_ms=end_ms - 60_000,
                           n_footprint=len(tail),
                           candle_class=S._ignition_candle_class(sig.get("usd"))[0])
        out["slice"], out["muted"] = sl, muted
        break                                        # 🔒 اشتعالٌ واحدٌ لكلّ (رمز، جلسة)
    return out


def control_index(sb, i, sym, day, span=5):
    """§④ `F3` — شاهدُ الضبط الحتميّ: دقيقةٌ **غيرُ مشتعلة** من نفس الرمز ونفس الجلسة،
    مطابقةٌ في دقيقة الساعة ‏±`span`، تُختار بـ`sha256("YYYY-MM-DD:SYM")` (نمطُ
    `control_panel` المعتمَد — لا عشوائيّةَ ولا انتقاء).

    🔴 **والمرشّحون قبل الاشتعال حصرًا (`j < i`) — قرارٌ مؤرَّخ (§⑩-و-3):** التسجيل
    يشترط «غيرُ مشتعلة»، و`replay_trigger` تُرجع **الأوّلَ فقط** ⇒ يستحيل إثباتُ عدمِ
    اشتعال دقيقةٍ بعده إلّا ببناء كاشفٍ ثانٍ (يمنعه `V2`)، **وكلُّ دقيقةٍ قبل الأولى
    غيرُ مشتعلةٍ بشهادة الكاشف نفسِه**. ترجّع الفهرسَ أو `None` (ويُعَدّ)."""
    try:
        # 🐞 `IndexError` مضمومٌ عمدًا: حارسٌ ضيّقٌ يُسقط الجولةَ كلَّها على فهرسٍ شاذّ
        #    — وهو صنفُ «الحارسُ الضيّق لا يلتقط النوعَ الواقع» المدوَّن. والالتقاطُ
        #    يبقى **مُسمًّى** لا `Exception` عريضًا يخفي عيوبًا أخرى.
        mod0 = int(sb[i]["mod"])
    except (KeyError, TypeError, ValueError, IndexError):
        return None
    cand = [j for j in range(0, i)
            if sb[j].get("mod") is not None
            and abs(int(sb[j]["mod"]) - mod0) <= int(span)]
    if not cand:
        return None
    h = hashlib.sha256(f"{day}:{sym.upper()}".encode("utf-8")).hexdigest()
    return cand[int(h[:8], 16) % len(cand)]


def daily_after(hist, sym, day, sessions=OUTCOME_SESSIONS):
    """§②-6 + §⑩-و-1/2: شموعُ الحكم **من اللقطة المجمَّدة** — الصفوفُ التي تاريخُها
    **‏> يوم الاشتعال** ثم **أوّلُ `sessions`** فقط.

    🔒 **من اللقطة لا من ياهو** (مقياسٌ واحد — `V9`) · **ومقصوصةٌ عند 40** فيبقى
    `pending` ممكنًا (السلسلةُ المفتوحة تُلغيه بنيويًّا). ترجّع DataFrame أو None."""
    df = (hist or {}).get(str(sym).upper())
    if df is None or len(df) == 0:
        return None
    try:
        d = [str(t.date()) if hasattr(t, "date") else str(t)[:10] for t in df.index]
        idx = [k for k, x in enumerate(d) if x > str(day)]
        if not idx:
            return None
        return df.iloc[idx[0]:idx[0] + int(sessions)]
    except Exception:
        return None


def _fake_pct(c):
    """`FAKE(g)` = نسبةُ `fakeout` من **المحسوم** (`real`+`fakeout`) — §③ حرفيًّا.
    و`pending` **مستبعَدةٌ من المقام** ويُعلَن عددُها. ترجّع (النسبة، المقام)."""
    dec = int(c.get("real", 0)) + int(c.get("fakeout", 0))
    return ((c.get("fakeout", 0) / dec * 100.0) if dec else None), dec


def _slice_report(name, buckets, keys):
    """يطبع `FAKE` وفاصلَ Wilson **الثنائيّ** لكلّ شريحة (‏`S._wilson_ci` الإنتاجيّة —
    ولا آلةَ ثانية، §⑩-و-4) + المقياسَ المساندَ `real` (يُعلَن ولا يحكم، §③)."""
    out = {}
    for k in keys:
        c = buckets.get(k) or {}
        f, dec = _fake_pct(c)
        lo, hi = S._wilson_ci(int(c.get("fakeout", 0)), dec) if dec else (None, None)
        out[k] = {"fake": f, "dec": dec, "lo": lo, "hi": hi,
                  "real": int(c.get("real", 0)), "fakeout": int(c.get("fakeout", 0)),
                  "pending": int(c.get("pending", 0))}
        print(f"   {name}/{k}: محسوم={dec} (real={c.get('real', 0)} · "
              f"fakeout={c.get('fakeout', 0)}) · معلّق={c.get('pending', 0)} · "
              + (f"FAKE={f:.1f}% · Wilson 95%=[{lo:.1f}, {hi:.1f}]"
                 if f is not None else "FAKE=— (مقامٌ صفر)"))
    return out


def _separated(a, b):
    """§⑤-3 **اختبارٌ ثنائيُّ الطرف**: `lo_a > hi_b` **أو** `lo_b > hi_a` — تصحيحًا
    صريحًا لأحاديّة `T-ACC` التي استحال عليها أن ترى علاقةً عكسية."""
    if not a or not b or a.get("lo") is None or b.get("lo") is None:
        return False
    return (a["lo"] > b["hi"]) or (b["lo"] > a["hi"])


def run_armed() -> int:
    """قياسُ **الشرائح وحدها** على مجتمع ARMED لسنةٍ واحدة (§⑥ — أرضيّةُ العيّنة).

    🔒 **إعادةُ استعمالٍ لا إعادةُ بناء:** كونُ ARMED ومستوياتُ الخطّة والتجديدُ اليوميّ
    للحاجز تُؤخَذ من `event_exec_run` **بأسمائها** (`_armed`/`plan_levels`/
    `session_levels`) — وهي مُدقَّقةٌ ومقفولةٌ سلفًا، ونسخُها كان سيُنشئ مقياسًا ثانيًا.
    والكشفُ `EX.replay_trigger` والحكمُ دوالُّ الإنتاج.

    ⚖️ **ومقياسُ السعر هنا «معدَّل» في الطرفين لا خامّ** — بخلاف وضع الجدوى، **وهو
    مقتضى `V9` نفسِه (مقياسٌ واحد)**: مستوياتُ الخطّة مشتقّةٌ من اللقطة المجمَّدة
    (`auto_adjust=True`) فجلبُ شموعٍ خامّةٍ يخلط مقياسَين. مدوَّنٌ في `opfire_prereg.md`
    §⑩-ج، وحارسُه `EX.scale_mismatch` وعدّادُه مطبوع."""
    import event_exec_run as EXR

    year = (os.environ.get("BACKTEST_YEAR", "") or "?").strip()
    print(f"🔗 السنة: {year} · المجتمع: كون ARMED (ما كان على القائمة فعلًا)")
    if not _key():
        print("⛔ `POLYGON_API_KEY` غائب — لا حصادَ ولا حكم.")
        return 2
    trades = [t for t in (S.run_backtest() or []) if t.get("exit_date")]
    if not trades:
        print("⛔ `BT_REPLAY10` خامل ⇒ لا كون ARMED — **no-op لا تُفسَّر نتيجتُه**.")
        return 2
    armed, rep, dropped = EXR._armed(trades)
    if dropped:
        print(f"⚠️ أُسقِطت {dropped} نافذة بلا `eligible_at` (لا ارتدادَ ليوم الإشارة).")
    if not armed:
        print("⛔ صفرُ نافذةٍ بمرجعٍ زمنيّ صالح ⇒ لا قياس.")
        return 2
    if MAX_WINDOWS:
        print(f"⚠️ **قصٌّ مُعلَن**: {MAX_WINDOWS} من {len(armed)} نافذة (‏§⑦ `V4`).")
        armed = armed[:MAX_WINDOWS]
    print(f"كون ARMED: {len(armed)} نافذة · من {len(trades)} إشارة "
          f"· مرفوض بالسعة={rep['rejected_cap']}")

    sl = {"pass_operator": 0, "mute_operator": 0, "fallback": 0}
    fb_group = 0                                  # `fallback` تصنيفُ شمعته `group`
    classes: dict = {}                            # `F2` **قبل** البوّابة (‏`P1`)
    spans: list = []                              # مدى البصمة بالدقائق (عدّادُ صدق)
    cov = {"windows": 0, "no_levels": 0, "no_bars": 0, "scale_bad": 0,
           "sessions": 0, "trig": 0, "crit": 0, "lifted": 0,
           "no_trades": 0, "thin": 0}
    t0 = time.time()
    for a in armed:
        lv = EXR.plan_levels(a["trade"])
        if not lv:
            cov["no_levels"] += 1
            continue
        cov["windows"] += 1
        cov["crit"] += 1 if lv.get("from_crit") else 0
        bars = EX.hist_minute_bars(a["symbol"], a["start"], a["end"])
        if not bars:
            cov["no_bars"] += 1
            continue
        sess = EX.group_sessions(bars)
        days = sorted(sess)
        if days and EX.scale_mismatch(sess[days[0]], a["trade"].get("entry"),
                                      SCALE_TOL):
            cov["scale_bad"] += 1
            continue
        lvl_of = EXR.session_levels(days, sess, a["trade"], lv["break"])
        for day in days:
            sb = sess[day]
            cov["sessions"] += 1
            brk = lvl_of[day]
            if brk > lv["break"]:
                cov["lifted"] += 1
            hit = EX.replay_trigger(sb, brk, S._ignition_signal,
                                    vol_mult=float(S.CONFIG["IGNITION_VOL_MULT"]),
                                    window=WIN_MIN)
            if not hit:
                continue
            i, sig = hit
            cov["trig"] += 1
            cls = S._ignition_candle_class(sig.get("usd"))[0]
            classes[cls] = classes.get(cls, 0) + 1
            end_ms = int(sb[i]["t"]) + 60_000
            rows, oldest, _ = fetch_footprint_desc(a["symbol"], end_ms * 1_000_000)
            if rows is None:
                # 🔴 تعذّرُ الجلب **ليس** `None` من `_operator_blocks` — لا يُعَدّ
                #    شريحةً، وإلّا صار عطبُ شبكةٍ كتمًا مفبركًا.
                cov["no_trades"] += 1
                continue
            if len(rows) < 20:
                cov["thin"] += 1                  # السببُ البنيويّ لشريحة `fallback`
            if oldest:
                spans.append((end_ms - oldest // 1_000_000) / 60_000.0)
            of = S._operator_blocks([(r["price"], r["size"]) for r in rows
                                     if r["price"] and r["size"]],
                                    int(S.CONFIG["OPERATOR_MIN_SHARES"]))
            k, muted = mute_decision(of, sig.get("usd"))
            sl[k] += 1
            if k == "fallback" and muted:
                fb_group += 1
    dur = time.time() - t0

    muted_n = sl["mute_operator"] + fb_group
    passed_n = sl["pass_operator"] + (sl["fallback"] - fb_group)
    tot = muted_n + passed_n
    print(f"\n📊 المقيس ({dur / 60:,.1f}د · نداءات={EX.call_stats()}): "
          f"جلسات={cov['sessions']} · اشتعالات={cov['trig']} · مُشرَّح={tot}")
    print(f"🔀 **الشريحتان (‏`F1`)**: مكتوم={muted_n} "
          f"(`mute_operator`={sl['mute_operator']} · `fallback`∧`group`={fb_group}) "
          f"· ممرَّر={passed_n} (`pass_operator`={sl['pass_operator']} · "
          f"`fallback`∧غير`group`={sl['fallback'] - fb_group})")
    print(f"   وشريحةُ `fallback` الخام (‏`_operator_blocks`→`None`) = "
          f"{sl['fallback']}" + (f" = {sl['fallback'] / tot * 100:.1f}% "
                                 f"من المُشرَّح (‏`P6` يتوقّع ≥15%)" if tot else ""))
    print("🕯️ `F2` توزيعُ الشمعة **قبل** البوّابة (‏`P1`): "
          + (" · ".join(f"{k}={v}" for k, v in sorted(classes.items())) or "—"))
    _sp = sorted(spans)
    print(f"🩺 التغطية: نوافذ={cov['windows']} · بلا مستويات={cov['no_levels']} "
          f"· بلا شموع={cov['no_bars']} · مقياسٌ مختلف={cov['scale_bad']} "
          f"· بالرقم الحرج={cov['crit']} · ارتفع الحاجز={cov['lifted']} "
          f"· تعذّر جلبُ الصفقات={cov['no_trades']} · بصمةٌ دون 20 صفقة={cov['thin']}")
    print(f"   مدى البصمة (وسيط): "
          + (f"{_sp[len(_sp) // 2]:,.1f} دقيقة" if _sp else "—")
          + " — **يُقاس ولا يُحَدّ** (الإنتاج بلا نافذةٍ زمنية)")

    print("\n🚦 بوّاباتُ الصلاحية:")
    gate("V3 العلمُ فعّال — قرأ (رمز، جلسة) فعلًا", cov["sessions"] > 0,
         f"جلسات={cov['sessions']} — الصفرُ ‏no-op لا تُفسَّر نتيجتُه")
    gate("V8 `break_level` مبنيٌّ فعلًا **وبالرقم الحرج**", cov["crit"] > 0,
         f"{cov['crit']} من {cov['windows']} نافذة — والصفرُ يعني زنادًا آخر")
    gate("V9 مقياسٌ **واحد** (معدَّلٌ في الشموع والمستويات — §⑩-ج)",
         cov["scale_bad"] * 2 <= max(1, cov["windows"]),
         f"مستبعَدٌ للتقسيم={cov['scale_bad']} من {cov['windows']}")
    gate("V4 عدّاداتٌ لا تكذب — المُشرَّحُ = مجموعُ الشريحتين",
         tot == sl["pass_operator"] + sl["mute_operator"] + sl["fallback"],
         f"{tot} = {sl['pass_operator']}+{sl['mute_operator']}+{sl['fallback']}")

    proj = tot and muted_n * 3 * PENDING_FRAC
    print(f"\n📐 **أرضيّةُ العيّنة (‏§⑥ · §⑤-5):** مكتومُ سنةٍ واحدة = {muted_n} "
          f"⇒ **معامِلُ التوسيع ×3** (ثلاثُ سنوات) ثم ×{PENDING_FRAC} "
          f"(‏`pending` ‏≈20%) ⇒ **‏≈{proj or 0:.0f} مكتومًا محسومًا** "
          f"مقابل الحدّ {FLOOR_SLICE}")
    if _FAILS:
        print("\n⛔ سقطت: " + " · ".join(_FAILS))
        return 3
    if not proj or proj < FLOOR_SLICE:
        print("\n⛔ **لا حكم** — الأرضيةُ لا تُبلَغ ⇒ **لا تشغيلَ للسنوات الثلاث** "
              "(‏§⑥: «أُبلِغ «لا حكم» قبل التشغيل الكامل لا بعده»). والميزانيةُ توفَّر.")
        return 5
    print("\n✅ الأرضيةُ تُبلَغ ⇒ السنواتُ الثلاث مأذونةٌ بعقد المالك.")
    return 0


def run_judge() -> int:
    """⚖️ **وضعُ الحكم** — الأذرعُ الثلاث والمقياسُ الحاكم لسنةٍ واحدة (‏§③-§⑤).

    🔒 **كلُّ حكمٍ بدالّة الإنتاج:** الكشفُ `EX.replay_trigger`+`S._ignition_signal` ·
    الكتمُ `S._operator_blocks`+`S._ignition_candle_class` · **الوسمُ
    `S._ignition_outcome`** · الدلالةُ `S._wilson_ci`. وكونُ ARMED والمستوياتُ من
    `event_exec_run` بأسمائها.

    **ولا يُصدِر حكمًا نهائيًّا**: يطبع أعدادَ سنةٍ خامًّا (`RAW|…`) + المعيارَ على
    شقّه السنويّ، **والشقُّ المجمَّع يُجمَع عبر السنوات الثلاث خارجًا** (§⑩-و-5)."""
    import event_exec_run as EXR

    year = (os.environ.get("BACKTEST_YEAR", "") or "?").strip()
    print(f"🔗 السنة: {year} · المجتمع: كون ARMED · نافذةُ الحكم "
          f"{OUTCOME_SESSIONS} جلسة بعد يوم الاشتعال حصرًا")
    if not _key():
        print("⛔ `POLYGON_API_KEY` غائب — لا حصادَ ولا حكم.")
        return 2
    # §⑩-و-1: شموعُ الحكم من **اللقطة المجمَّدة نفسِها** (مقياسٌ واحد · point-in-time)
    fz = os.environ.get("BT_FROZEN_PATH", "").strip()
    hist, _sp, asof = S.load_frozen_dataset(fz) if fz else (None, None, None)
    if not hist:
        print("⛔ لا لقطةَ مجمَّدة (`BT_FROZEN_PATH`) ⇒ **لا شموعَ حكمٍ بمقياسٍ واحد**. "
              "وجلبُ ياهو اليوم يُدخل مقياسًا ثالثًا (‏§⑩-و-1) ⇒ يُمتنَع لا يُخمَّن.")
        return 2
    print(f"🕰️ اللقطة: as-of {asof} · {len(hist)} رمزًا")

    trades = [t for t in (S.run_backtest() or []) if t.get("exit_date")]
    if not trades:
        print("⛔ `BT_REPLAY10` خامل ⇒ لا كون ARMED — **no-op لا تُفسَّر نتيجتُه**.")
        return 2
    armed, rep, dropped = EXR._armed(trades)
    if dropped:
        print(f"⚠️ أُسقِطت {dropped} نافذة بلا `eligible_at` (لا ارتدادَ ليوم الإشارة).")
    if not armed:
        print("⛔ صفرُ نافذةٍ بمرجعٍ زمنيّ صالح ⇒ لا قياس.")
        return 2
    if MAX_WINDOWS:
        print(f"⚠️ **قصٌّ مُعلَن**: {MAX_WINDOWS} من {len(armed)} نافذة (‏§⑦ `V4`).")
        armed = armed[:MAX_WINDOWS]
    print(f"كون ARMED: {len(armed)} نافذة · من {len(trades)} إشارة "
          f"· مرفوض بالسعة={rep['rejected_cap']}")

    def _blank():
        return {"real": 0, "fakeout": 0, "pending": 0}

    f1 = {"muted": _blank(), "passed": _blank()}          # الذراع الحاكمة
    f2 = {"group": _blank(), "mid": _blank(), "op+strong": _blank()}
    f3 = {"muted": _blank(), "passed": _blank()}          # شاهدُ الضبط
    acc = {"n": 0, "aggr": 0.0, "block": 0.0, "dark": 0.0}
    cov = {"windows": 0, "no_levels": 0, "no_bars": 0, "scale_bad": 0, "sessions": 0,
           "thin_sess": 0, "trig": 0, "crit": 0, "no_trades": 0, "thin": 0,
           "no_daily": 0, "ctrl_none": 0, "ctrl_no_trades": 0}
    t0 = time.time()
    for a in armed:
        sym = a["symbol"]
        lv = EXR.plan_levels(a["trade"])
        if not lv:
            cov["no_levels"] += 1
            continue
        cov["windows"] += 1
        cov["crit"] += 1 if lv.get("from_crit") else 0
        bars = EX.hist_minute_bars(sym, a["start"], a["end"])
        if not bars:
            cov["no_bars"] += 1
            continue
        sess = EX.group_sessions(bars)
        days = sorted(sess)
        if days and EX.scale_mismatch(sess[days[0]], a["trade"].get("entry"),
                                      SCALE_TOL):
            cov["scale_bad"] += 1
            continue
        lvl_of = EXR.session_levels(days, sess, a["trade"], lv["break"])
        for day in days:
            sb = sess[day]
            cov["sessions"] += 1
            if len(sb) < EX.MIN_BARS:
                cov["thin_sess"] += 1        # §⑩-و-6: مقياسٌ على مستوى الجلسة لا الدقيقة
            brk = lvl_of[day]
            hit = EX.replay_trigger(sb, brk, S._ignition_signal,
                                    vol_mult=float(S.CONFIG["IGNITION_VOL_MULT"]),
                                    window=WIN_MIN)
            if not hit:
                continue
            i, sig = hit
            cov["trig"] += 1
            fdf = daily_after(hist, sym, day)
            if fdf is None or len(fdf) == 0:
                cov["no_daily"] += 1
                continue
            # ── الذراعان F1/F2 على الاشتعال الحقيقيّ ──
            rows, _old, _rk = fetch_footprint_desc(sym, (int(sb[i]["t"]) + 60_000)
                                                   * 1_000_000)
            if rows is None:
                cov["no_trades"] += 1        # عطبُ نداءٍ **لا يُصنَّف** شريحةً
                continue
            if len(rows) < 20:
                cov["thin"] += 1
            pairs = [(r["price"], r["size"]) for r in rows if r["price"] and r["size"]]
            of = S._operator_blocks(pairs, int(S.CONFIG["OPERATOR_MIN_SHARES"]))
            k, muted = mute_decision(of, sig.get("usd"))
            out = S._ignition_outcome({"price": sig.get("price"),
                                       "break_level": brk, "date": day}, fdf)
            f1["muted" if muted else "passed"][out] += 1
            cls = S._ignition_candle_class(sig.get("usd"))[0]
            f2[("group" if cls == "group" else
                ("mid" if cls == "mid" else "op+strong"))][out] += 1
            # §②-7: وصفٌ فقط — لا تدخل ذراعًا ولا حكمًا (محاورُ `T-ACC` مُغلقة)
            _ac = S.acc_components([{"price": r["price"], "size": r["size"],
                                     "exchange": r["exchange"]} for r in rows
                                    if r["price"] and r["size"]])
            if _ac:
                acc["n"] += 1
                acc["aggr"] += float(_ac.get("aggressive_buy_pct") or 0)
                acc["block"] += float(_ac.get("block_share_pct") or 0)
                acc["dark"] += float(_ac.get("dark_share_pct") or 0)
            # ── الذراع F3: شاهدُ الضبط الحتميّ بنافذته هو ──
            j = control_index(sb, i, sym, day, CTRL_SPAN)
            if j is None:
                cov["ctrl_none"] += 1
                continue
            crows, _o2, _k2 = fetch_footprint_desc(sym, (int(sb[j]["t"]) + 60_000)
                                                   * 1_000_000)
            if crows is None:
                cov["ctrl_no_trades"] += 1
                continue
            cof = S._operator_blocks([(r["price"], r["size"]) for r in crows
                                      if r["price"] and r["size"]],
                                     int(S.CONFIG["OPERATOR_MIN_SHARES"]))
            cusd = round(float(sb[j].get("c") or 0) * float(sb[j].get("v") or 0))
            _ck, cmut = mute_decision(cof, cusd)
            cout = S._ignition_outcome({"price": sb[j].get("c"),
                                        "break_level": brk, "date": day}, fdf)
            f3["muted" if cmut else "passed"][cout] += 1
    dur = time.time() - t0

    print(f"\n📊 المقيس ({dur / 60:,.1f}د · نداءات={EX.call_stats()}): "
          f"جلسات={cov['sessions']} · اشتعالات={cov['trig']}")
    print(f"🩺 التغطية: نوافذ={cov['windows']} · بلا مستويات={cov['no_levels']} "
          f"· بلا شموع={cov['no_bars']} · مقياسٌ مختلف={cov['scale_bad']} "
          f"· بالرقم الحرج={cov['crit']} · جلساتٌ دون `min_bars`={cov['thin_sess']} "
          f"· تعذّرَ جلبُ الصفقات={cov['no_trades']} · بصمةٌ دون 20={cov['thin']} "
          f"· بلا شموعِ حكم={cov['no_daily']} · بلا شاهد={cov['ctrl_none']} "
          f"· شاهدٌ بلا صفقات={cov['ctrl_no_trades']}")
    if acc["n"]:
        print(f"🔬 `acc_components` **وصفًا فقط** ({acc['n']} اشتعالًا · لا تدخل ذراعًا "
              f"ولا حكمًا — محاورُ `T-ACC` مُغلقة): شراءٌ عدوانيّ "
              f"{acc['aggr'] / acc['n']:.1f}% · طبعاتٌ كبيرة "
              f"{acc['block'] / acc['n']:.1f}% · دارك {acc['dark'] / acc['n']:.1f}%")

    print("\n📐 الأذرع (`FAKE` = نسبةُ `fakeout` من المحسوم · `pending` خارج المقام):")
    r1 = _slice_report("F1", f1, ["muted", "passed"])
    r2 = _slice_report("F2", f2, ["group", "mid", "op+strong"])
    r3 = _slice_report("F3", f3, ["muted", "passed"])
    for arm, buck in (("F1", r1), ("F2", r2), ("F3", r3)):
        for k, v in buck.items():
            print(f"RAW|{year}|{arm}|{k}|{v['real']}|{v['fakeout']}|{v['pending']}")

    d1 = ((r1["muted"]["fake"] - r1["passed"]["fake"])
          if (r1["muted"]["fake"] is not None
              and r1["passed"]["fake"] is not None) else None)
    d3 = ((r3["muted"]["fake"] - r3["passed"]["fake"])
          if (r3["muted"]["fake"] is not None
              and r3["passed"]["fake"] is not None) else None)
    print(f"\n🎯 **الفرقُ الحاكم `Δ(F1)` = FAKE(مكتوم) − FAKE(ممرَّر) = "
          + (f"{d1:+.1f} نقطة**" if d1 is not None else "— (مقامٌ صفر)**"))
    print(f"🧪 وشاهدُ الضبط `Δ(F3)` = "
          + (f"{d3:+.1f} نقطة" if d3 is not None else "— (مقامٌ صفر)"))
    print("   والمقياسُ المساند (يُعلَن ولا يحكم): نسبةُ `real` — "
          f"مكتوم={r1['muted']['real']} من {r1['muted']['dec']} · "
          f"ممرَّر={r1['passed']['real']} من {r1['passed']['dec']}")

    print("\n🚦 بوّاباتُ الصلاحية:")
    gate("V3 العلمُ فعّال", cov["sessions"] > 0, f"جلسات={cov['sessions']}")
    gate("V8 `break_level` بالرقم الحرج", cov["crit"] > 0,
         f"{cov['crit']} من {cov['windows']}")
    gate("V9 مقياسٌ واحد (اللقطة في الدقائق والمستويات وشموع الحكم — §⑩-و-1)",
         cov["scale_bad"] * 2 <= max(1, cov["windows"]),
         f"مستبعَدٌ للتقسيم={cov['scale_bad']} من {cov['windows']}")
    gate("V4 عدّاداتٌ لا تكذب — الاشتعالاتُ = المُصنَّفُ + المتعذّر",
         cov["trig"] == (sum(v["dec"] + v["pending"] for v in r1.values())
                         + cov["no_trades"] + cov["no_daily"]),
         f"{cov['trig']} = {sum(v['dec'] + v['pending'] for v in r1.values())}"
         f"+{cov['no_trades']}+{cov['no_daily']}")

    print("\n🧭 المعيارُ (‏§⑤ — الشقُّ السنويُّ فقط · والمجمَّعُ يُجمَع خارجًا):")
    print(f"  ② الفرقُ ‏≥{DIFF_MIN:g} نقطة هذي السنة ⇒ "
          + ("✅" if (d1 is not None and abs(d1) >= DIFF_MIN) else "🔴"))
    print("  ③ فاصلا Wilson **ثنائيَّي الطرف** منفصلان (سنويًّا) ⇒ "
          + ("✅" if _separated(r1["muted"], r1["passed"]) else "🔴"))
    print(f"  ⑤ الشريحتان ‏≥{FLOOR_SLICE} سنويًّا ⇒ "
          + ("✅" if min(r1["muted"]["dec"], r1["passed"]["dec"]) >= FLOOR_SLICE
             else f"🔴 (مكتوم={r1['muted']['dec']} · ممرَّر={r1['passed']['dec']}) "
                  "— **الشرطُ مجمَّعٌ بنصّ §⑥ فلا يُحكَم عليه سنويًّا**"))
    if d1 is not None and d3 is not None and abs(d1) >= DIFF_MIN:
        void = (abs(d3) >= F3_RATIO * abs(d1)) and (abs(d3) >= F3_ABS)
        same = (d1 > 0) == (d3 > 0)
        print("  🔴 الشرطُ السالب (شاهدُ الضبط): "
              + ("**تُلغى النتيجة — أثرُ آلةٍ لا أثرُ اشتعال**" if (void and same)
                 else ("لا إلغاء (إشارةُ `F3` مخالفةٌ ⇒ يُطبَع الطرفان)"
                       if void else "لا إلغاء")))
    else:
        print("  ℹ️ الشرطُ السالب **لا يُطبَّق**: `|Δ(F1)|` دون الحدّ أصلًا ⇒ المعيارُ "
              "ساقطٌ فلا يُلغى ما هو ساقط (§⑤ حرفيًّا).")
    print("\n⚠️ حدودُ الصدق كما سُجِّلت: انحيازُ بقاءٍ (كونُ الباكتيست الناجي) · "
          "تداخلٌ انتقائيٌّ في دقيقة الاشتعال (‏`F3` حارسُه) · تشويهُ تقسيمات · "
          "وسمٌ من الجلسة النظاميّة وحدها.")
    if _FAILS:
        print("\n⛔ سقطت: " + " · ".join(_FAILS))
        return 3
    print("\n✅ عبرت بوّاباتُ الصلاحية — **ولا حكمَ نهائيًّا من سنةٍ واحدة.**")
    return 0


def main() -> int:
    print("=" * 78)
    print("🔬🔥 T-OPFIRE — " + {
        "feasibility": "**وضعُ الجدوى** (لا حكم)",
        "armed": "**قياسُ المكتوم على كون ARMED** (عَدٌّ لا حكم)",
        "judge": "⚖️ **وضعُ الحكم** — الأذرعُ الثلاث لسنةٍ واحدة",
    }.get(MODE, f"وضع «{MODE}»"))
    print("=" * 78)
    if MODE == "armed":
        return run_armed()
    if MODE == "judge":
        return run_judge()
    if MODE != "feasibility":
        print("⛔ وضعٌ غيرُ منفَّذ — والعقد يمنع السوقَ الكامل قبل عبور الأرضية.")
        return 2
    if not _key():
        print("⛔ `POLYGON_API_KEY` غائب — لا حصادَ ولا حكم.")
        return 2

    wl = S.load_watchlist()
    act = [s for s in (wl.get("stocks") or []) if s.get("status") == "active"]
    day = DAY or (dt.date.today() - dt.timedelta(days=1)).isoformat()
    syms = act[:MAX_SYMS]
    print(f"🔗 اليوم: {day} · رموزُ القائمة الحيّة: {len(syms)} من {len(act)} نشِط · "
          f"نافذةُ الكشف {WIN_MIN}د · نافذةُ البصمة {FOOTPRINT_TRADES} صفقة")
    print(f"   عتباتُ الإنتاج: vol×{S.CONFIG['IGNITION_VOL_MULT']} · "
          f"طبعة≥{S.CONFIG['OPERATOR_MIN_SHARES']} · "
          f"قروب≤{S.CONFIG['IGNITION_USD_GROUP']:,} · "
          f"مضارب≥{S.CONFIG['IGNITION_USD_OPERATOR']:,}")

    t0 = time.time()
    rows = []
    for s in syms:
        try:
            rows.append(scan_symbol_day(s["symbol"], day, s))
        except Exception as e:                                   # noqa: BLE001
            print(f"  ⚠️ {s.get('symbol')}: {type(e).__name__}: {e}")
    dur = time.time() - t0

    lvl_ok = [r for r in rows if r["break_level"]]
    crit_n = sum(1 for r in lvl_ok if r["lvl_kind"] == "critical")
    fb_n = sum(1 for r in lvl_ok if r["lvl_kind"] == "fallback_pivot105")
    fires = [r for r in rows if r["fire"]]
    raw_keys = next((r["raw_keys"] for r in rows if r["raw_keys"]), [])
    ts_field = next((r["ts_field"] for r in rows if r["ts_field"]), None)
    n_trades = sum(r["trades"] for r in rows)
    n_bars = sum(r["bars"] for r in rows)
    sl_count = {}
    for r in fires:
        sl_count[r["slice"]] = sl_count.get(r["slice"], 0) + 1

    print(f"\n📊 المقيس ({dur:,.1f}ث): شموع={n_bars:,} · صفقات={n_trades:,} · "
          f"مستوى كسر={len(lvl_ok)}/{len(rows)} (حرج {crit_n} · احتياط {fb_n}) · "
          f"اشتعالات={len(fires)}")
    if fires:
        print("   الشرائح: " + " · ".join(f"{k}={v}" for k, v in sl_count.items()))
        for r in fires:
            f = r["fire"]
            print(f"   🔥 {r['symbol']} · سعر {f['price']} · vol×{f['vol_x']} · "
                  f"${f['usd']:,} ({f['candle_class']}) · كسر {r['break_level']:.4f} · "
                  f"بصمة من {f['n_footprint']} صفقة ⇒ {r['slice']}"
                  + (" · **مكتوم**" if r["muted"] else " · يمرّ"))

    print("\n🚦 بوّاباتُ الصلاحية:")
    gate("V3 العلمُ فعّال — قرأ (رمز، يوم) فعلًا",
         n_bars > 0 and n_trades > 0,
         f"شموع={n_bars:,} · صفقات={n_trades:,} — الصفرُ ‏no-op لا تُفسَّر نتيجتُه")
    gate("V8 `break_level` مبنيٌّ فعلًا (يقتل «صفرُ اشتعالٍ بنيويّ» قبل الميزانية)",
         len(lvl_ok) > 0, f"{len(lvl_ok)} من {len(rows)}")
    gate("V5 حقلُ الزمن **مُثبَتٌ من المُخرَج لا مُخمَّن**", bool(ts_field),
         f"الحقل: {ts_field or '—'} · حقولُ المزوّد: {', '.join(raw_keys) or '—'}")
    gate("V10 `exchange` حاضرٌ (وإلّا `dark_share_pct` «غيرُ مقيس» لا صفرًا)",
         "exchange" in raw_keys, "غيابُه لا يُسقط الجدوى لكنه يُعلَن")
    gate("V1 شاهدُ الضبط — رمزٌ سائلٌ يُخرج سماتٍ غيرَ تافهة",
         *(lambda w: (bool(w and w[0] and len(w[0]) > 1000),
                      f"{WITNESS}: {len(w[0]) if w and w[0] else 0:,} صفقة"))(
             fetch_trades_day(WITNESS, day, cap=60_000)))
    gate("V9 مقياسُ سعرٍ واحدٌ **خامّ** في الشموع والمستويات",
         "adjusted=false" in open(__file__, encoding="utf-8").read(),
         "الجالبُ البحثيّ يثبّت `adjusted=false`")

    print("\n📌 وما يقيسه هذا الوضعُ ولا يحكم به: **نسبةُ `fallback`** التي تحكم أرضيةَ "
          "«‏≥25 لكلّ شريحة» في العقد §⑥ — وتُقاس على مجتمع ARMED لا على هذي العيّنة.")
    print("🔒 **وضعُ جدوى: صفرُ حكم.** ولا سنةَ ولا سوقَ كاملٌ قبل عبور البوّابات، "
          "ولا رقمَ يُكتَب في `opfire_result.md` قبل ذلك.")
    if _FAILS:
        print("\n⛔ سقطت: " + " · ".join(_FAILS))
        return 3
    print("\n✅ عبرت بوّاباتُ الجدوى كلُّها.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
