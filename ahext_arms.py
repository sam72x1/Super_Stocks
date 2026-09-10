#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🌙⛰️ `T-AHEXT` — «المشتعلُ في الافتر مسقوفٌ في البري» (العقد `ahext_prereg.md`
مدفوعٌ **قبل هذا الملفّ** وقبل أيّ رقم).

**السؤال (§⓪):** هل السهمُ الذي صعد في **الافتر** مسقوفٌ في **البريماركت** عند
‏≈100-120% من إغلاق الأمس، بينما «الطازج» (لم يصعد في الافتر) بلا هذا السقف؟

**الذراعان (§②) — مُفكَّكتان ومستوفيتان:**

    E-AH    = ah_rise ≥ AH_MIN      (امتدادُ افتر)
    E-FRESH = ah_rise <  AH_MIN     (طازجٌ في البري)

**مصدرُ كلّ رقمٍ مقيسٍ واحدٌ: Polygon** — الإغلاقُ النظاميّ من `/v1/open-close`
(‏وهو **الإغلاقُ الرسميّ** لا آخرُ طبعةٍ ممتدّة ⇒ `V-A1`) والقممُ من دقائق
`/v2/aggs` بالـ`adjusted=true` نفسِه ⇒ **`V-A6` تسويةُ التقسيم متّسقةٌ بالبناء**،
فلا يتكرّر عطبُ `SPRB` (دخولٌ 52.42 مقابل 3,933.96 من مزج مصدرين).
⚠️ ولا يُستعمل `polygon_prev_close` الإنتاجيّ — **توثيقُه يمنع نفسَه** من القياس
التاريخيّ («نسبيٌّ للحظة النداء»).

**اللقطةُ للغربال فقط** (`load_frozen_dataset` بالاسم): نسبةُ `open/prev_close`
داخلَ مصدرٍ واحد ⇒ لا مزجَ في **قرارِ الترشيح**، والقياسُ كلُّه من Polygon.

🔒 `Super_stock.py` **لا يُمَسّ بحرف** · قراءةٌ فقط: صفرُ كتابةِ حالةٍ وصفرُ
إرسال · الإنتاجُ لا يستوردها · لا `LOGIC_VERSION`."""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import sys
import time
from zoneinfo import ZoneInfo

import requests

import Super_stock as S
from universe_arms import wilson

NY = ZoneInfo("America/New_York")

# ── ثوابتُ العقد — مثبَّتةٌ قبل أيّ رقم (§①/§③) ──
GAP_MIN = 15.0          # غربالُ الفجوة اليوميّة (هندسيّةٌ مُعلَنة)
PM_MIN = 20.0           # دخولُ المجتمع: متحرّكُ بريماركت
AH_MIN = 20.0           # حدُّ «صعد بالافتر»
CAP_HI = 120.0          # سقفُ فيصل المزعوم — **يُقاس ولا يُشحَن**
PRICE_LO, PRICE_HI = 0.30, 20.0
CAND_CAP = 2000         # سقفٌ سنويٌّ — والمُسقَطُ يُطبَع بعدده (لا قصَّ صامت)
FADE_PROBE = 300        # مِجَسُّ الذوبان `AX5`
FADE_MAX = 25.0         # تجاوزُه ⇒ الفرعُ 3 (لا حكم)
FLOOR_ROWS = 100        # حدُّ العيّنة لكلّ ذراعٍ في السنة
COVER_MIN = 80.0        # تغطيةُ الجلب الدنيا
SEED_TAG = "T-AHEXT-20260910"
OUT_ROWS = "ahext_rows.jsonl"


def _log(m):
    print(m, flush=True)


# ══════════════════ دوالُّ نقيّة (تُقفَل سلوكيًّا) ══════════════════
def et_ms(date_iso: str, hh: int, mm: int) -> int:
    """`V-A2` — لحظةُ ساعةِ حائطٍ **بتوقيت نيويورك** ⟶ ملّي إبوك.

    التحويلُ عبر `ZoneInfo` فيتصيّف ويتشتّى آليًّا. **وUTC المثبَّت عطبٌ مقيسٌ
    عندنا مرّتين** (‏13:30 صيفيّة على تشغيلات الشتاء · وكرونُ الرادار)."""
    y, m, d = (int(x) for x in str(date_iso)[:10].split("-"))
    return int(_dt.datetime(y, m, d, hh, mm, tzinfo=NY).timestamp() * 1000)


def window_peak(bars, frm_ms: int, to_ms: int):
    """`V-A3`/`V-A4` — أعلى قمّةٍ في `[frm, to)` حصرًا.

    طابعُ Polygon `t` = **بدايةُ شمعة الدقيقة** ⇒ الشرطُ `frm <= t < to` يُخرج
    شمعةَ `to` نفسَها ⇒ **صفرُ نظرٍ مستقبليّ** عند 09:30. `None` لنافذةٍ فارغة."""
    hs = [float(b["h"]) for b in (bars or [])
          if b.get("h") is not None and b.get("t") is not None
          and frm_ms <= int(b["t"]) < to_ms]
    return max(hs) if hs else None


def window_last_close(bars, frm_ms: int, to_ms: int):
    """آخرُ إغلاقٍ داخل `[frm, to)` — مرجعُ القراءة الثانية لـ«مجمل» (`AX4`)."""
    cs = [(int(b["t"]), float(b["c"])) for b in (bars or [])
          if b.get("c") is not None and b.get("t") is not None
          and frm_ms <= int(b["t"]) < to_ms]
    return max(cs)[1] if cs else None


def _selfcheck_readonly() -> bool:
    """`V-A7` — قراءةٌ فقط بالـAST على مصدر هذي الأداة: صفرُ إرسالٍ وصفرُ كتابةِ
    حالة، والملفُّ الوحيد المسموحُ فتحُه للكتابة هو `OUT_ROWS`."""
    import ast as _a
    try:
        src = open(__file__, encoding="utf-8").read()
    except Exception:                                            # noqa: BLE001
        return False
    banned = {"send_telegram", "git_save", "save_watchlist",
              "save_op_entry_state", "record_new_alerts", "save_near_watch",
              "save_hunter_watch"}
    for n in _a.walk(_a.parse(src)):
        if isinstance(n, _a.Call):
            fn = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
            if fn in banned:
                return False
            if fn == "open":
                mode = ""
                if len(n.args) > 1 and isinstance(n.args[1], _a.Constant):
                    mode = str(n.args[1].value)
                for kw in n.keywords or []:
                    if kw.arg == "mode" and isinstance(kw.value, _a.Constant):
                        mode = str(kw.value.value)
                if any(c in mode for c in ("w", "a", "x", "+")):
                    if not (n.args and isinstance(n.args[0], _a.Name)
                            and n.args[0].id == "OUT_ROWS"):
                        return False
    return True


def classify_arm(ah_rise, ah_min: float = AH_MIN):
    """`V-A5` — ذراعٌ واحدةٌ لا غير: `None` تعني «تعذّرَ القياس» فلا تدخل."""
    if ah_rise is None:
        return None
    return "E-AH" if float(ah_rise) * 100.0 >= float(ah_min) else "E-FRESH"


def screen_symbol(df, year: str, gap_min: float = GAP_MIN,
                  px_lo: float = PRICE_LO, px_hi: float = PRICE_HI):
    """الغربالُ الرخيص (§①-ب): أيّامُ `year` بفجوةٍ ونطاقِ سعرٍ — من اللقطة.

    نقيّةٌ وفاشلةٌ-آمنة. تُرجّع **كلَّ** الأيّام المؤهَّلةِ سعرًا مع فجوتها،
    والفرزُ بـ`gap_min` يقع في المُنادي ليخدم المجتمعَ **ومِجَسَّ الذوبان** معًا
    من غربالٍ واحد (‏ميزانيةٌ واحدةٌ للذراعين — درسُ `T-CLIFF`)."""
    out = []
    try:
        idx = [str(x)[:10] for x in df.index]
        op, cl = list(df["Open"]), list(df["Close"])
    except Exception:                                            # noqa: BLE001
        return out
    for i in range(1, len(idx)):
        if idx[i][:4] != str(year):
            continue
        try:
            pc, o = float(cl[i - 1]), float(op[i])
        except (TypeError, ValueError):
            continue
        if pc <= 0 or not (px_lo <= pc <= px_hi):
            continue
        out.append({"date": idx[i], "prev_date": idx[i - 1],
                    "gap_pct": round((o / pc - 1.0) * 100.0, 2)})
    return out


def det_order(rows, tag: str = SEED_TAG):
    """ترتيبٌ **حتميٌّ** للقصّ عند السقف: `sha256(tag|symbol|date)`.

    لا `random` بلا بذرة ولا «أوّلُ N بالتاريخ» (ينحاز لأوّل السنة)."""
    return sorted(rows, key=lambda r: hashlib.sha256(
        f"{tag}|{r['symbol']}|{r['date']}".encode()).hexdigest())


def arm_rate(vals, thresh: float):
    """نسبةُ من تجاوز `thresh` داخل ذراعٍ + فاصلُ ويلسون (§③)."""
    n = len(vals)
    k = sum(1 for v in vals if v is not None and float(v) > float(thresh))
    lo, hi = wilson(k, n)
    return {"n": n, "above": k,
            "pct": round(k / n * 100.0, 2) if n else 0.0,
            "wilson": [round(lo, 1), round(hi, 1)]}


def pctile(vals, q: float):
    """المئينُ `q` (‏0-100) بالاستيفاء الخطّيّ — لا اعتمادَ على numpy."""
    xs = sorted(float(v) for v in vals if v is not None)
    if not xs:
        return None
    if len(xs) == 1:
        return round(xs[0], 4)
    pos = (len(xs) - 1) * (float(q) / 100.0)
    lo_i, hi_i = int(pos), min(int(pos) + 1, len(xs) - 1)
    return round(xs[lo_i] + (xs[hi_i] - xs[lo_i]) * (pos - lo_i), 4)


def diff_se(a, b):
    """الخطأُ المعياريُّ لفرقِ نسبتين مستقلّتين بالنقاط المئوية (§③)."""
    na, nb = a["n"], b["n"]
    if na < 1 or nb < 1:
        return None
    pa, pb = a["pct"] / 100.0, b["pct"] / 100.0
    return round(((pa * (1 - pa) / na + pb * (1 - pb) / nb) ** 0.5) * 100.0, 2)


# ══════════════════ الجلب — فاشلٌ-آمنٌ مطلق ══════════════════
def _key():
    return os.environ.get("POLYGON_API_KEY", "").strip()


def _get(url: str, tries: int = 3):
    h = {"Authorization": f"Bearer {_key()}"}
    for i in range(tries):
        try:
            r = requests.get(url, headers=h, timeout=20)
            if r.status_code == 200:
                return r.json() or {}
            if r.status_code in (429, 502, 503, 504):
                time.sleep(2 ** i)
                continue
            return None
        except Exception:                                        # noqa: BLE001
            time.sleep(2 ** i)
    return None


def official_close(sym: str, date_iso: str):
    """`V-A1` — **الإغلاقُ النظاميُّ الرسميّ** من `/v1/open-close` (لا آخرُ طبعةٍ
    ممتدّة ولا شمعةُ 15:59). `None` عند التعذّر — تعذّرٌ لا صفر."""
    j = _get(f"https://api.polygon.io/v1/open-close/{sym.upper()}/{date_iso}"
             f"?adjusted=true")
    try:
        c = float((j or {}).get("close"))
        return c if c > 0 else None
    except (TypeError, ValueError):
        return None


def minutes_range(sym: str, frm_ms: int, to_ms: int):
    """دقائقُ المدى (تشمل الممتدّ) — بترقيمِ صفحاتٍ احتياطًا. `None` عند التعذّر."""
    url = (f"https://api.polygon.io/v2/aggs/ticker/{sym.upper()}"
           f"/range/1/minute/{frm_ms}/{to_ms}?adjusted=true&sort=asc&limit=50000")
    bars, guard = [], 0
    while url and guard < 10:
        j = _get(url)
        if j is None:
            return None
        bars += [b for b in (j.get("results") or []) if b.get("t") is not None]
        nxt = j.get("next_url")
        url = f"{nxt}&limit=50000" if nxt else None
        guard += 1
    return bars or None


def measure(sym: str, prev_date: str, date: str,
            fetch_close=None, fetch_bars=None):
    """صفٌّ واحدٌ مقيس: `prev_close` رسميّ · `ah_rise` · `pm_peak`.

    نافذةُ الافتر `D-1 16:00→20:00` ونافذةُ البري `D 04:00→09:30` **بتوقيت
    نيويورك** — والجلبةُ واحدةٌ تغطّيهما (‏`V-A3` لا تسرّبَ بين الجلستين).

    🔒 **الجالبان محقونان للاختبار** (نمطُ `fetch_hist`/`fetch_bars` المدوَّن):
    القيمُ الافتراضيّةُ هي دوالُّ الشبكة نفسُها ⇒ **مسارُ الإنتاج بت-بت**،
    والسويّةُ تختبر **هذا المسارَ بعينه** لا دالّةً مجاورة. وُلد هذا الحقنُ من
    عيبٍ مقيس: قفلُ `AHX6` الأوّل كان يفحص `classify_arm` **والقرارُ هنا**،
    فنجت منه طفرةٌ أعادت زرعَ العيب الحقيقيّ."""
    pc = (fetch_close or official_close)(sym, prev_date)
    if not pc:
        return None
    ah_f, ah_t = et_ms(prev_date, 16, 0), et_ms(prev_date, 20, 0)
    pm_f, pm_t = et_ms(date, 4, 0), et_ms(date, 9, 30)
    bars = (fetch_bars or minutes_range)(sym, ah_f, pm_t)
    if bars is None:
        return None
    ah_hi, pm_hi = window_peak(bars, ah_f, ah_t), window_peak(bars, pm_f, pm_t)
    ah_cl = window_last_close(bars, ah_f, ah_t)
    n_ah = sum(1 for b in bars if ah_f <= int(b["t"]) < ah_t)
    # 🔴 **تصحيحٌ قبل أيّ رقم (§⑨-2):** الجلبةُ نجحت والنافذةُ فارغة ⇒ **لا تداولَ
    #    في الافتر** = **صعودٌ صفر** = `E-FRESH` بالتعريف. ولو عُدَّت «تعذّرَ قياس»
    #    لأُقصي **أنقى الطازجين** من الذراع ⇒ انحيازٌ يجعل `E-FRESH` أسهمًا
    #    تداولت في الافتر ولم تصعد — وهو مجتمعٌ آخر. (‏وتعذّرُ الجلب `bars is
    #    None` مُلتقَطٌ أعلاه فلا يختلط بهذا.)
    return {"symbol": sym, "date": date, "prev_date": prev_date,
            "prev_close": round(pc, 4),
            "ah_rise": 0.0 if ah_hi is None else round(ah_hi / pc - 1.0, 4),
            "ah_close_rise": (None if ah_cl is None
                              else round(ah_cl / pc - 1.0, 4)),
            "ah_bars": n_ah,
            "pm_peak": None if pm_hi is None else round(pm_hi / pc - 1.0, 4),
            "n_bars": len(bars)}


# ══════════════════ التشغيل ══════════════════
def main() -> int:
    year = str(os.environ.get("AHEXT_YEAR", "")).strip()
    frozen = str(os.environ.get("AHEXT_FROZEN", "")).strip()
    if year not in ("2023", "2024", "2025", "2026") or not frozen:
        # ‏2026 **وصفيّةٌ خارج العيّنة** (§⑨-3) — لا تدخل الحكم
        _log("⛔ يلزم AHEXT_YEAR و AHEXT_FROZEN")
        return 2
    if not _key():
        _log("⛔ يلزم POLYGON_API_KEY — ولا يُخمَّن رقمٌ بدونه")
        return 5

    hist, _splits, asof = S.load_frozen_dataset(frozen)
    if not hist:
        _log("⛔ تعذّر تحميل اللقطة")
        return 2
    # ── بوّابةُ سنةِ اللقطة (نمطُ `SNAP1`): عطبٌ مقيسٌ أعطى عشرَ مرّاتٍ فرقًا بصمت ──
    if str(asof or "")[:4] != year:
        _log(f"⛔ اللقطة as-of {asof} لا تطابق سنةَ القياس {year}")
        return 4
    _log(f"🔒 سنةُ اللقطة {str(asof)[:4]} = سنةُ القياس {year} ✅ · "
         f"رموزُها {len(hist)}")
    _log(f"📌 الميزانيّةُ والسقوفُ (§①-ب): GAP_MIN={GAP_MIN} · PM_MIN={PM_MIN} · "
         f"AH_MIN={AH_MIN} · CAP_HI={CAP_HI} · CAND_CAP={CAND_CAP} · "
         f"FADE_PROBE={FADE_PROBE} · السعر [{PRICE_LO}, {PRICE_HI}]")

    # ── ① الغربالُ الرخيص ──
    hi_gap, lo_gap = [], []
    for sym in sorted(hist):
        for c in screen_symbol(hist[sym], year):
            c["symbol"] = sym
            if c["gap_pct"] >= GAP_MIN:
                hi_gap.append(c)
            elif c["gap_pct"] >= 0:
                lo_gap.append(c)
    _log(f"🔎 الغربال: فجوةٌ ≥{GAP_MIN}% ⇒ {len(hi_gap)} صفًّا · "
         f"[0,{GAP_MIN}) ⇒ {len(lo_gap)} صفًّا")
    if not hi_gap:
        _log("⛔ الغربالُ فارغ")
        return 6

    cand = det_order(hi_gap)[:CAND_CAP]
    dropped = len(hi_gap) - len(cand)
    _log(f"✂️ السقفُ {CAND_CAP}: مُشغَّلٌ {len(cand)} · **مُسقَطٌ {dropped}** "
         f"(قصٌّ حتميٌّ مُعلَنٌ بعدده لا صامت)")

    # ── ② القياسُ من Polygon ──
    rows, failed = [], 0
    with open(OUT_ROWS, "w", encoding="utf-8") as fh:
        for i, c in enumerate(cand):
            m = measure(c["symbol"], c["prev_date"], c["date"])
            if m is None:
                failed += 1
            else:
                m["gap_pct"] = c["gap_pct"]
                rows.append(m)
                fh.write(json.dumps(m, ensure_ascii=False) + "\n")
            if (i + 1) % 200 == 0:
                _log(f"   … {i + 1}/{len(cand)} · تعذّر {failed}")
    cover = len(rows) / len(cand) * 100.0 if cand else 0.0
    _log(f"📡 التغطية: {len(rows)}/{len(cand)} = {cover:.1f}% "
         f"(الحدُّ الأدنى {COVER_MIN}%)")
    if cover < COVER_MIN:
        _log("⛔ تغطيةٌ دون الحدّ ⇒ الفرعُ 3: لا حكم")
        return 7

    # ── ③ المجتمعُ والذراعان ──
    pop = [r for r in rows
           if r["pm_peak"] is not None and r["pm_peak"] * 100.0 >= PM_MIN
           and classify_arm(r["ah_rise"]) is not None]
    ah = [r for r in pop if classify_arm(r["ah_rise"]) == "E-AH"]
    fresh = [r for r in pop if classify_arm(r["ah_rise"]) == "E-FRESH"]
    v_a5 = len(ah) + len(fresh) == len(pop)
    _log(f"🔒 `V-A5` مجموعُ الذراعين = المجتمع: {len(ah)}+{len(fresh)}="
         f"{len(pop)} ⇒ {'✅' if v_a5 else '⛔'}")
    if not v_a5:
        return 6
    _log(f"👥 المجتمع {len(pop)} · `E-AH` {len(ah)} · `E-FRESH` {len(fresh)}")

    # ── ④ مِجَسُّ الذوبان `AX5` — حاكمٌ سلبًا ──
    probe = det_order(lo_gap)[:FADE_PROBE]
    p_hit, p_ok = 0, 0
    for c in probe:
        m = measure(c["symbol"], c["prev_date"], c["date"])
        if m is None or m["pm_peak"] is None:
            continue
        p_ok += 1
        if m["pm_peak"] * 100.0 >= PM_MIN:
            p_hit += 1
    hit_rate = p_hit / p_ok if p_ok else 0.0
    est_missed = hit_rate * len(lo_gap)
    fade_pct = (est_missed / (est_missed + len(pop)) * 100.0
                if (est_missed + len(pop)) else 0.0)
    _log(f"🫧 `AX5` الذوبان: {p_hit}/{p_ok} من عيّنة [0,{GAP_MIN}) ⇒ "
         f"مُقدَّرٌ فائتٌ {est_missed:.0f} ⇒ **فواتٌ {fade_pct:.1f}%** "
         f"(الحدُّ {FADE_MAX}%)")

    # ── ⑤ المقاييس ──
    r_ah = arm_rate([r["pm_peak"] * 100.0 for r in ah], CAP_HI)
    r_fr = arm_rate([r["pm_peak"] * 100.0 for r in fresh], CAP_HI)
    d = round(r_fr["pct"] - r_ah["pct"], 2)
    se = diff_se(r_fr, r_ah)
    sig = round(abs(d) / se, 2) if se else None
    ax3 = pctile([r["pm_peak"] * 100.0 for r in ah], 90)
    # `AX4` — نصُّ العقد «المرجعُ **إغلاقُ** الافتر» لا قمّتُه (تصحيحٌ قبل أيّ رقم)
    ax4 = pctile([(1 + r["pm_peak"]) / (1 + r["ah_close_rise"]) * 100.0 - 100.0
                  for r in ah
                  if r.get("ah_close_rise") is not None
                  and (1 + r["ah_close_rise"]) > 0], 90)
    floor_ok = min(len(ah), len(fresh)) >= FLOOR_ROWS

    _log("")
    _log(f"📊 `AX1` فوق {CAP_HI}%: `E-AH` {r_ah['pct']}% ({r_ah['above']}/"
         f"{r_ah['n']}) · `E-FRESH` {r_fr['pct']}% ({r_fr['above']}/{r_fr['n']})")
    _log(f"📊 الفرقُ (FRESH−AH) = **{d:+} نقطة** · σ={se} · {sig}σ")
    _log(f"📊 `AX3` المئينُ 90 لـ`E-AH` = **{ax3}%** (قولُ فيصل 100-120)")
    _log(f"📊 `AX4` القراءةُ الثانية لـ«مجمل» (مرجعُ الافتر) = {ax4}%")
    _log(f"📊 `AX6` حصّةُ `E-AH` من المجتمع = "
         f"{len(ah) / len(pop) * 100.0:.1f}%")
    _log(f"🔒 حدُّ العيّنة {FLOOR_ROWS}/ذراع: {'✅' if floor_ok else '⛔ لا تدخل AX1'}")
    if fade_pct > FADE_MAX:
        _log(f"⛔ `AX5` فوق {FADE_MAX}% ⇒ **الفرعُ 3: لا حكم** مهما كانت الأرقام")

    print("AHEXT_JSON " + json.dumps(
        {"year": year, "asof": str(asof), "cand": len(cand), "dropped": dropped,
         "cover_pct": round(cover, 1), "pop": len(pop),
         "AX1": {"E_AH": r_ah, "E_FRESH": r_fr, "diff": d, "se": se, "sigma": sig},
         "AX3_p90_ah": ax3, "AX4_p90_alt": ax4,
         "AX5": {"hit": p_hit, "n": p_ok, "est_missed": round(est_missed),
                 "fade_pct": round(fade_pct, 1)},
         "AX6_ah_share": round(len(ah) / len(pop) * 100.0, 1),
         "floor_ok": floor_ok,
         "no_verdict": (not floor_ok) or fade_pct > FADE_MAX},
        ensure_ascii=False))
    return 8 if fade_pct > FADE_MAX else 0


if __name__ == "__main__":
    sys.exit(main())
