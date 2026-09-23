#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📏🪜 `T-MA-LADDER` — **«احسب بالأيام من وين هابط · 20 أو 30 أو 50»**
(العقد `ma_ladder_prereg.md` مدفوعٌ **ومدموجٌ في `main` قبل هذا الملفّ**
وقبل أيّ رقم).

**السؤال:** داخل مرشّحي الارتكاز وبميزانيّةٍ ثابتة — هل الإشارةُ التي **نضج**
متوسّطُها (‏`n` مُشتقٌّ من طول الهبوط) أفضلُ عائدًا بوحدة المخاطرة؟
**وهل تضيف على زخمٍ مجرَّد؟** (‏`C-MOM`/`C-RAND` **حاكمان** بدرس `T-PMGATE`.)

🔑 **البنيةُ تُغني عن نصف الحرّاس:** باكتيستٌ **واحدٌ لكلّ سنة** على اللقطة
المجمَّدة ⇒ مجموعةُ الصفقات **كائنٌ واحد** تُعاد عليه خمسُ إعاداتٍ بمجموعاتٍ
مختلفة **وبالمُرتِّب نفسِه** (`replay10.rank_live` المحقون) وبالسعة نفسِها
⇒ الميزانيّةُ والمحورُ والكونُ والنافذةُ **متطابقةٌ بالبناء لا بالدعوى**.

🔒 **وما لا يُمَسّ (§⑦):** `rank_key` في `Super_stock.py` · `pivot_stability` ·
`SPLIT_MA_PERIODS` · `MA_GATE_MAX_ABOVE_PCT` · ولا `CONFIG` تُضبَط في أيّ
موضع · ولا `LOGIC_VERSION` · ولا إرسال · **ولا يُشحَن شيءٌ مهما كانت النتيجة.**

⚠️ **حدُّ صدقٍ في قلب التعريف (‏§⑧-1):** `peak_and_decline` تقرأ **القمّة** لا
«بدءَ الهبوط» الذي يقصده فيصل ⇒ **نقلُ تعريفٍ مُعلَن**، ويُطبَع بديلٌ `alt`
(أوّلُ إغلاقٍ تحت `ema(close, 20)` بعد القمّة) **وصفيًّا ولا يحكم**.

⚠️ **و`rsi_rank_arms` مُغلَقٌ بخروج ‏8** — لا يُستورَد منه شيءٌ هنا إطلاقًا،
ولا يُضبَط `RSIRANK_REOPEN`، ويُقفَل ذلك **سلوكيًّا** (‏`V-M6`).

🔒 قراءةٌ/بحثٌ فقط · بلا كرون · والنتيجةُ حين تصدر في `ma_ladder_result.md`.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys

import ceiling_arms as CA
# ── الاستيرادُ بالاسم = التجميدُ بالبناء ──
from exitmgmt_arms import boot_ci
from replay10 import (CAPACITY, candidates_from_trades, r_unit, rank_live,
                      replay)
from tranche_arms import r_fixed

# ══════════ ثوابتُ العقد — تُطبَع في كلّ تقرير ══════════
CLAMP_LO, CLAMP_HI = 20, 50      # §②-2 — حدّا فيصل الأدنى والأعلى حرفيًّا
PERIODS = (20, 30, 50)           # 🥇 `SPLIT_MA_PERIODS` — أرقامُ فيصل الثلاثة
W = 5                            # §②-3 — `engineering` مُعلَن
W_SENS = (3, 5, 10)              # حساسيّةٌ **وصفيّةٌ خارجَ عدّ المعايير**
FLOOR_L1 = 100                   # §⑤-3 — أرضيّةُ `L1` لكلّ سنة
MATERIAL = 0.05                  # §④ `ML4` — الماديّة `engineering` مُعلَنة
BOOT, BOOT_SEED = 5000, 20260920
RAND_SEED = 20260920             # بذرةُ `C-RAND` — ثابتةٌ وتُطبَع
ALT_SPAN = 20                    # §⑧-1 — متوسطُ التعريف البديل (وصفيّ)
OUT_ROWS = "ma_ladder_rows.jsonl"

# 📌 مرجعُ `V-M2` — **رقمٌ منشور** في `rsi40_result.md §②` لذراع الأساس (نفسُ
#    السعة ونفسُ `rank_live` ونفسُ اللقطات) ⇒ `L0` يجب أن يُعيده بت-بت.
PUBLISHED_L0_D100 = {"2023": 13, "2024": 9, "2025": 12}
GOV_YEARS = ("2023", "2024", "2025")
GOV_ARMS = ("L0", "L1", "C-MOM", "C-RAND")     # ما تقوم عليه المعايير
DESC_ARMS = ("L2",)                            # وصفيٌّ يُطبَع ولا يحكم
D100 = 100.0

# 🔢 رموزُ الخروج — **مميَّزةٌ ولا تتصادم** (درسُ `RKA16`/`c2`)
RC_OK = 0
RC_INPUT = 2        # مدخلٌ ناقص
RC_TOOL = 3         # فحصٌ ذاتيٌّ ساقط
RC_SNAP = 4         # لقطةٌ متعذّرة
RC_GUARD = 5        # `V-M1`/`V-M3` ساقط
RC_BASE = 6         # `V-M2` ساقط
RC_NOJUDGE = 9      # الفرعُ 3 «لا حكم»

BANNED_W = ("open(", "write", "commit", "push", "send_telegram", "requests.")


def _log(m):
    print(m, flush=True)


# ══════════ ① دوالُّ نقيّة — تعريفُ §② بحرفه ══════════
def ladder_period(bsp) -> int | None:
    """`n = clamp(bars_since_peak, 20, 50)` ثمّ **أقربُ** عضوٍ من ‏(20, 30, 50).

    التقريبُ `engineering` مُعلَنٌ في العقد §②-2 · والتعادلُ يُكسَر **نزولًا**
    (الأصغرُ أوّلًا) فيكون حتميًّا ولا يُختار بعد رؤية رقم.
    فاشلةٌ-آمنة ⇒ `None` عند المدخل غيرِ الصالح."""
    try:
        b = int(bsp)
    except (TypeError, ValueError):
        return None
    if b < 0:
        return None
    b = max(CLAMP_LO, min(CLAMP_HI, b))
    return min(PERIODS, key=lambda p: (abs(p - b), p))


def matured_at(ema_fn, close, i: int, n: int, w: int = W) -> bool | None:
    """§②-3 — أبلغ **الإغلاقُ** قيمةَ `ema(close, n)` في إحدى آخر `w` جلسات
    **قبل** الإشارة؟

    `close` **سلسلةُ pandas** بطولِ التاريخ كلِّه، و`i` فهرسُ شمعة الإشارة ⇒
    الشموعُ المقروءةُ `[0, i)` حصرًا ⇒ **صفرُ تسريب**. فاشلةٌ-آمنة ⇒ `None`.

    🔑 و`ema` **بالاسم من الإنتاج** على الشريحة — لا إعادةَ بناءٍ موازية."""
    try:
        i, n, w = int(i), int(n), int(w)
    except (TypeError, ValueError):
        return None
    if i <= 0 or n <= 0 or w <= 0 or i > len(close):
        return None
    hit = False
    for j in range(w):
        end = i - j                       # يشمل الشمعةَ `end-1` ويقف قبل `i`
        if end < n:
            break
        try:
            e = float(ema_fn(close.iloc[:end], n))
            c = float(close.iloc[end - 1])
        except Exception:                                        # noqa: BLE001
            continue
        if e != e or c != c:
            continue
        if c >= e:
            hit = True
            break
    return hit


def alt_decline_start(ema_fn, close, peak_idx: int, i: int) -> int | None:
    """§⑧-1 — التعريفُ **البديلُ الوصفيّ**: أوّلُ إغلاقٍ تحت `ema(close, 20)`
    **بعد** القمّة ⇒ عددُ الجلسات منه حتى الإشارة. لا يحكم."""
    try:
        pk, i = int(peak_idx), int(i)
    except (TypeError, ValueError):
        return None
    if pk < 0 or i <= pk or i > len(close):
        return None
    for k in range(pk + 1, i):
        if k < ALT_SPAN:
            continue
        try:
            e = float(ema_fn(close.iloc[:k + 1], ALT_SPAN))
            c = float(close.iloc[k])
        except Exception:                                        # noqa: BLE001
            continue
        if e == e and c == c and c < e:
            return i - k
    return None


def pick_mom(rows, k: int):
    """`C-MOM` **ضبطٌ حاكم** — أقوى `k` إشارةٍ بـ`gain5` **الموجب**.

    🔑 «النضج» يعني أن السعرَ **صعد** إلى متوسّطه ⇒ زخمٌ صرفٌ قد يفسّره كلَّه،
    والسؤالُ النافعُ الوحيد: **هل يضيف المتوسّطُ المُشتقُّ على الزخم المجرَّد؟**
    والتعادلُ يُكسَر بـ(التاريخ، الرمز) ⇒ **حتميّةٌ تامّة.**"""
    pos = [t for t in rows if (_g5(t) or 0.0) > 0.0]
    pos.sort(key=lambda t: (-(_g5(t) or 0.0), str(t.get("date")),
                            str(t.get("symbol") or "")))
    return pos[:max(0, int(k))]


def pick_rand(rows, k: int, seed: int = RAND_SEED):
    """`C-RAND` **ضبطٌ حاكم** — عيّنةٌ **حتميّةٌ** بحجم `L1` من كلّ الإشارات.
    التجزئةُ على (البذرة، التاريخ، الرمز) ⇒ تُعاد بالأمر نفسِه فتعطي العيّنةَ
    نفسَها، ولا تعتمد على ترتيب الورود."""
    def _h(t):
        s = f"{seed}|{t.get('date')}|{t.get('symbol')}"
        return hashlib.sha256(s.encode()).hexdigest()
    return sorted(rows, key=_h)[:max(0, int(k))]


def _g5(t):
    v = (t.get("env_vals") or {}).get("gain5")
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return None if v != v else v


# ══════════ ② حرّاسٌ تُطبَع والسقوطُ يوقف (§⑥) ══════════
TRAIL_YML = os.path.join(".github", "workflows", "trail.yml")


def trail_snapshots(path: str = TRAIL_YML) -> dict:
    """`V-M1` — معرّفاتُ اللقطات **تُقرأ من `trail.yml` لا تُكتَب بيدٍ.**

    فأيُّ لقطةٍ أخرى ⇒ مجتمعٌ مختلفٌ عن `T-TRAIL`/`T-HEADCUT` ⇒ **خروج 5**."""
    out = {}
    try:
        src = open(path, encoding="utf-8").read()
    except OSError:
        return out
    cur = None
    for ln in src.splitlines():
        s = ln.strip()
        if s.startswith("snap_") and s.endswith(":"):
            cur = s[len("snap_"):-1]
        elif cur and s.startswith("default:"):
            out[cur] = s.split("default:", 1)[1].strip().strip('"').strip("'")
            cur = None
    return out


def selfcheck_readonly(src: str | None = None) -> bool:
    """`V-M5` — **قراءةٌ فقط**: صفرُ كتابةٍ وصفرُ إرسالٍ وصفرُ دفعٍ في هذا الملفّ.

    🔒 **ومُشدَّدٌ بدرسِ `T-PMFWD`:** ما لا يُثبَت أنه قراءةٌ **يُعَدّ كتابة** —
    فوضعٌ مُمرَّرٌ **متغيّرًا** يُرفَض (كان يُمرِّر ملفًّا يكتب وهو يُعلَن قراءة).
    والوضعُ الغائبُ قراءةٌ يقينًا (`"r"` بالتعريف) فيمرّ · وكتابةٌ لا تمرّ إلّا
    إلى **هدفَين مسمَّيَين**: `OUT_ROWS` (صفوفُ التقرير) و`tp` (صفقاتُ السنة في
    الطفل) — **وكلاهما مُخرَجُ قياسٍ لا حالةَ إنتاج.**"""
    WRITE_OK = {"OUT_ROWS", "tp"}
    if src is None:
        src = open(os.path.abspath(__file__), encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        fn = n.func
        name = getattr(fn, "id", None) or getattr(fn, "attr", None) or ""
        if name in ("send_telegram", "send_telegram_document", "git_save",
                    "_write_csv_file", "save_watchlist"):
            return False
        if name == "open":
            if len(n.args) < 2:
                continue                          # وضعٌ غائب = `"r"` يقينًا
            m = n.args[1]
            if not (isinstance(m, ast.Constant) and isinstance(m.value, str)):
                return False                      # غيرُ ثابتٍ ⇒ يُعَدّ كتابة
            if set(m.value) <= set("rbt"):
                continue                          # قراءةٌ صريحة
            tgt = n.args[0] if n.args else None
            if not (isinstance(tgt, ast.Name) and tgt.id in WRITE_OK):
                return False                      # كتابةٌ إلى هدفٍ غيرِ مسمّى
    return True


# 🐞 **اسمُ مفتاح الفتح مُركَّبٌ لا مكتوب** — وسببُه عيبٌ وقع فعلًا: الحارسُ
#    أدناه يقارن بثابتٍ نصّيّ، **والثابتُ نفسُه عقدةُ `Constant` في شجرة هذا
#    الملفّ** فكان الحارسُ يسقط على نفسه. والتركيبُ يجعل **الاستعمالَ الحقيقيَّ
#    وحدَه** (‏`os.environ[...]` بحرفه) هو ما يُمسَك — تشديدٌ لا إرخاء، وهو
#    الصنفُ نفسُه الذي أسقط `WLK5`/`WRK5` حين ذُكرت أسماءُ الملفّات في الشرح.
_REOPEN_BANNED = "RSIRANK" + "_" + "REOPEN"


def rsi_rank_untouched(src: str | None = None) -> bool:
    """`V-M6`-ب — أداةُ المحور المُغلَق بخروج ‏8 **لا تُلمَس**: صفرُ استيرادٍ
    وصفرُ نداءٍ لـ`main`/`run_child`، **ولا يُضبَط مفتاحُ فتحها** — بنيويًّا
    بالـAST لا بالنصّ (فالتعليقُ يذكر الاسمَ شرحًا)."""
    if src is None:
        src = open(os.path.abspath(__file__), encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            if any("rsi_rank_arms" in (a.name or "") for a in n.names):
                return False
        if isinstance(n, ast.ImportFrom):
            if "rsi_rank_arms" in (n.module or ""):
                return False
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            if n.value == _REOPEN_BANNED:
                return False
    return True


ROOTS = ("rank_key", "select_top", "classify_tier", "analyze_ticker",
         "apply_short_gate", "apply_float_gate", "scan_market",
         "backtest_symbol", "scan_ignition", "scan_split_hunter",
         "entry_status", "build_interpretation")


def _root_fp(src: str) -> dict:
    """بصمةُ كلّ جذرٍ من **شجرته** لا من نصّه — فالتعليقُ لا يُغيّرها."""
    out = {}
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and n.name in ROOTS:
            out[n.name] = hashlib.sha256(
                ast.dump(n).encode()).hexdigest()[:12]
    return out


def production_untouched() -> tuple:
    """`V-M6`-أ — الجذورُ الاثنا عشر **بصمتُها مطابقةٌ لـ`origin/main`**.

    🔒 وبصمةُ **الجذور** لا بصمةُ الملفّ: أدقُّ ممّا يلزم العقدَ نصًّا، ولا
    تسقط على تعليقٍ سليمٍ في موضعٍ آخر من `Super_stock.py`."""
    try:
        cur = _root_fp(open("Super_stock.py", encoding="utf-8").read())
    except OSError:
        return False, ["تعذّرت القراءة"]
    try:
        base_src = subprocess.run(
            ["git", "show", "origin/main:Super_stock.py"],
            capture_output=True, text=True, timeout=120).stdout
    except Exception:                                            # noqa: BLE001
        return False, ["تعذّر git"]
    base = _root_fp(base_src)
    if not base or not cur:
        return False, ["بصمةٌ فارغة"]
    diff = [r for r in ROOTS if cur.get(r) != base.get(r)]
    return (not diff), diff


def r_of(payload) -> float:
    """§④ — `R` للصفقة **بـ`tranche_arms.r_fixed` بالاسم**.

    🔑 والأذرعُ هنا **لا تغيّر الدخول** (الخطّةُ خطّةُ الإنتاج) ⇒
    `entry_k == entry_base` ⇒ `r_fixed` مطابقةٌ جبريًّا لـ`r_unit`
    (‏`(ret/100·e)/(e−s)` = `ret/((e−s)/e·100)`) — **ويُثبَت ذلك رقميًّا
    في `V-M7` على كلّ صفٍّ بدل أن يُدَّعى.**

    🔴 وغيرُ المُعبَّأة ⇒ **0.0** (لا تنفيذَ لكنها **استهلكت خانة**) — نفسُ
    عُرف `r_unit` حرفيًّا (‏`P0-01`: الكلفةُ تظهر في المقام).
    ⚠️ **وهذا العُرفُ في مجتمعٍ سالبِ التوقّع يُكافئ الذراعَ الأقلَّ تعبئةً آليًّا**
    (درسُ `T-WAIT-23W`) ⇒ علاجُه **ضبطٌ مطابَقُ التعبئة** لا تغييرُ المقام.
    (‏صُحِّح 2026-09-20 بعد الحكم: كان التعليلُ هنا **معكوسًا** — التعليقُ وحدَه
    تغيّر، والحسابُ بت-بت · `ma_ladder_result.md` ‏§④-ب.)"""
    p = payload or {}
    try:
        e, s = float(p["entry"]), float(p["stop"])
    except (TypeError, ValueError, KeyError):
        return 0.0
    if e <= 0 or e - s <= 0:
        return 0.0
    ret = p.get("ret_a")
    if ret is None:
        return 0.0
    v = r_fixed(ret, e, e, s)
    return 0.0 if v is None else float(v)


def r_identity(payloads) -> tuple:
    """`V-M7` — شاهدُ هُويّة: `r_of` (‏`r_fixed`) = `r_unit` **بت-بت** على كلّ
    صفٍّ مُعبَّأ. وأيُّ اختلافٍ يعني أن مقياسَي العقد والأداة افترقا."""
    bad, n = 0, 0
    for p in payloads:
        u = r_unit(p)
        if u is None:
            continue
        n += 1
        if abs(u - r_of(p)) > 1e-9:
            bad += 1
    return n, bad


# ══════════ ③ الإثراء — `n` و`matured` من الشموع السابقة حصرًا ══════════
def enrich_trades(S, sym: str, df, trades) -> list:
    """يُلحق بكلّ صفقةٍ حقولَ §② — **من `df.iloc[:i]` حصرًا** (صفرُ تسريب).

    `i` = فهرسُ **شمعةِ الإشارة نفسِها**، والقراءةُ تقف قبله ⇒ المُقاسُ كلُّه
    ممّا كان معلومًا **قبل** القرار. إلحاقٌ فقط: صفقةٌ لا يُحسَب لها شيءٌ تبقى
    بحقولها الأصليّة و`matured=None` فتُعدّ «غيرَ ناضجة» صراحةً لا صامتًا."""
    import pandas as pd                                          # noqa: PLC0415
    close = df["Close"].astype(float)          # 🔑 Series — `ema` تلزمها `.ewm`
    high = df["High"].values.astype(float)     # numpy — `peak_and_decline` تلزمها
    out = []
    for tr in trades:
        t = dict(tr)
        t.setdefault("symbol", sym)
        try:
            i = int(df.index.get_loc(pd.Timestamp(tr["date"])))
        except Exception:                                        # noqa: BLE001
            t["ml_why"] = "تاريخٌ غيرُ موجود"
            t["matured"] = None
            out.append(t)
            continue
        pd_ = S.peak_and_decline(high[:i])
        bsp = (pd_ or {}).get("bars_since_peak")
        n = ladder_period(bsp)
        t["bars_since_peak"] = (int(bsp) if bsp is not None else None)
        t["n"] = n
        if n is None:
            t["ml_why"] = "بلا قمّة/هبوط"
            t["matured"] = None
            out.append(t)
            continue
        t["matured"] = matured_at(S.ema, close, i, n, W)
        for w in W_SENS:                      # حساسيّةٌ وصفيّةٌ تُطبَع كاملة
            t[f"matured_w{w}"] = matured_at(S.ema, close, i, n, w)
        t["alt_bars"] = alt_decline_start(S.ema, close,
                                          (pd_ or {}).get("peak_idx"), i)
        an = ladder_period(t["alt_bars"])
        t["alt_n"] = an
        t["matured_alt"] = (matured_at(S.ema, close, i, an, W)
                            if an is not None else None)
        out.append(t)
    return out


def _measure_year(year: str, frozen: str) -> dict:
    """يشغّل الباكتيست **في عمليةٍ ابنةٍ مستقلّة** ويُرجع مسارَ صفقاتها المُثراة.

    🔒 والعزلُ مقصود: حالةُ `Super_stock` العامّة لا تُحمَل بين السنوات.
    **ولا ذراعَ تمسّ `CONFIG`** ⇒ طفلٌ واحدٌ للسنة لا طفلٌ لكلّ ذراع."""
    env = {**dict(os.environ), **CA.child_env(),
           "BACKTEST_YEAR": year, "BT_FROZEN_PATH": frozen}
    # 🔒🔴 **الطفلُ يُجرَّد من مفاتيح تلغرام** — درسُ `T-RSI-RANK`: المنعُ
    #    **بنيويٌّ** لا اتّكالٌ على غيابِ سرٍّ في workflow واحد.
    for _k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
               "TELEGRAM_BOT_TOKEN_2", "TG_BOT_TOKEN", "TG_CHAT_ID"):
        env.pop(_k, None)
    p = subprocess.run([sys.executable, os.path.abspath(__file__), "--child",
                        year, frozen], capture_output=True, text=True, env=env)
    blob = (p.stdout or "") + "\n" + (p.stderr or "")
    for ln in blob.splitlines():
        if not ln.startswith("MALADDER_CHILD:"):
            _log(f"  [{year}] {ln}")
    rows = [x for x in blob.splitlines() if x.startswith("MALADDER_CHILD:")]
    if p.returncode != 0 or not rows:
        return {}
    return json.loads(rows[-1].split("MALADDER_CHILD:", 1)[1])


def run_child(year: str, frozen: str) -> int:
    """الطفل — لقطةٌ واحدة ⇒ صفقاتٌ مُثراةٌ على القرص.

    🔒 ولا يُنادى `run_backtest` إطلاقًا (فيها إرسالٌ ووثائقُ CSV بلا حارس)؛
    يُنادى **`backtest_symbol` مباشرةً** كما في `trail_arms` — فالصفقاتُ
    والشموعُ في تمريرةٍ واحدة، وهو شرطُ حساب `matured` بلا جلبٍ ثانٍ."""
    import Super_stock as S                                      # noqa: PLC0415
    hist, splits_map, asof = S.load_frozen_dataset(frozen)
    if not hist:
        _log("⛔ لقطةٌ فارغة")
        return RC_SNAP
    if str(asof or "")[:4] != str(year):
        _log(f"⛔ اللقطة as-of {asof} لا تطابق سنةَ القياس {year} — "
             "مجتمعٌ مختلف، لا تُقاس")
        return RC_SNAP
    lo_d, hi_d = f"{year}-01-01", f"{year}-12-31"
    syms = sorted(hist)
    _log(f"📦 as-of {asof} · رموز {len(syms)}")
    rows, issues = [], {}
    for k, sym in enumerate(syms):
        df = hist.get(sym)
        if df is None or len(df) < int(S.CONFIG["MIN_BARS"]):
            continue
        try:
            trs = S.backtest_symbol(sym, df, date_window=(lo_d, hi_d),
                                    splits=(splits_map or {}).get(sym))
        except Exception as e:                                   # noqa: BLE001
            issues[type(e).__name__] = issues.get(type(e).__name__, 0) + 1
            continue
        if not trs:
            continue
        rows.extend(enrich_trades(S, sym, df, trs))
        if (k + 1) % 500 == 0:
            _log(f"   … {k + 1}/{len(syms)} · صفوف {len(rows)}")
    wf = [t for t in rows if t.get("exit_date")]
    tp = f"ma_ladder_trades_{year}.json"
    with open(tp, "w", encoding="utf-8") as fh:
        json.dump(wf, fh, ensure_ascii=False, default=str)
    meta = {"year": year, "asof": asof, "n_symbols": len(syms),
            "signals": len(rows), "wf": len(wf), "path": tp,
            "issues": issues, "expl": float(S.CONFIG["EXPLOSION_PCT"]),
            # 🔒 برهانٌ لا زينة: الثوابتُ التي يحرّمها §⑦ **لم تُمَسّ**.
            "split_ma_periods": list(S.CONFIG["SPLIT_MA_PERIODS"]),
            "ma_gate_max": float(S.CONFIG.get("MA_GATE_MAX_ABOVE_PCT") or -1)}
    print("MALADDER_CHILD:" + json.dumps(meta, ensure_ascii=False))
    return RC_OK


# ══════════ ④ الأذرع والقياس (§③) ══════════
def arms_of(rows, seed: int = RAND_SEED) -> dict:
    """الخمسةُ بترتيب جدول §③ — **ولا سادسةَ تُضاف بعد رقم**.

    `L0` كلُّ الإشارات · `L1` 🥇 الناضجةُ · `L2` مُكمِّلُها (وصفيّ) ·
    `C-MOM` 🥇 و`C-RAND` 🥇 **بحجم `L1` نفسِه** (‏`V-M3`)."""
    l1 = [t for t in rows if t.get("matured") is True]
    l2 = [t for t in rows if t.get("matured") is not True]
    k = len(l1)
    return {"L0": list(rows), "L1": l1, "L2": l2,
            "C-MOM": pick_mom(rows, k), "C-RAND": pick_rand(rows, k, seed)}


def _hit100(p: dict) -> bool:
    """صفقةٌ مأخوذةٌ بلغت ‏+100% قبل الوقف — **نفسُ شرط `ceiling_arms._d(100)`**."""
    if (p or {}).get("mg_outcome") in (None, "no_fill"):
        return False
    try:
        return float(p.get("mg_pre_stop") or 0.0) >= D100
    except (TypeError, ValueError):
        return False


def replay_arm(rows) -> dict:
    """إعادةٌ واحدةٌ بالميزانيّة والمُرتِّب نفسِهما — **المتغيّرُ الوحيد المجموعة**.

    🔒 `ranker=rank_live` = مُرتِّبُ الإنتاج بت-بت (`rank_key` لا تُمَسّ) ·
    `capacity=CAPACITY` = `WATCHLIST_SIZE` الحيّ · والمحورُ من الجلسات نفسِها."""
    dates = set()
    for t in rows:
        if t.get("date"):
            dates.add(str(t["date"]))
        if t.get("exit_date"):
            dates.add(str(t["exit_date"]))
    cands, idx, oc = candidates_from_trades(rows, extra_dates=sorted(dates))
    if not cands:
        return {"taken": 0, "filled": 0, "d100": 0, "r": 0.0, "g": {},
                "cap_used": int(CAPACITY), "axis_used": len(idx), "pool": 0}
    res = replay(cands, outcome_of=oc, ranker=rank_live, capacity=CAPACITY,
                 sessions=range(0, len(idx)))
    taken = res["taken"]
    nf = sum(1 for c in taken
             if (c.payload or {}).get("mg_outcome") == "no_fill"
             or (c.payload or {}).get("outcome") == "no_fill")
    # 🔴 المقامُ **كلُّ مأخوذة** — غيرُ المُعبَّأة استهلكت خانةً فتُحتسَب صفرًا
    #    (عُرفُ `r_unit`). ⚠️ وفي مجتمعٍ سالبِ التوقّع **يُكافئ الأقلَّ تعبئةً**
    #    — درسُ `T-WAIT-23W` بحرفه، وعلاجُه ضبطٌ مطابَقُ التعبئة (صُحِّح بعد الحكم).
    g = {}
    for c in taken:
        a, b = g.get(c.symbol, (0, 0.0))
        g[c.symbol] = (a + 1, b + r_of(c.payload))
    tot_n = sum(v[0] for v in g.values())
    tot_s = sum(v[1] for v in g.values())
    return {"taken": len(taken), "filled": len(taken) - nf,
            "d100": sum(1 for c in taken if _hit100(c.payload)),
            "r": (tot_s / tot_n if tot_n else 0.0), "g": g,
            "cap_used": int(res["capacity"]), "axis_used": len(idx),
            "pool": len(rows),
            "payloads": [c.payload for c in taken]}


def measure(rows, seed: int = RAND_SEED, only=None) -> dict:
    """يقيس الأذرعَ على صفقاتِ سنةٍ واحدة.

    🔒 **و`only` ليست تحسينَ سرعةٍ بل حاجزُ اطّلاع:** وضعُ الجدوى يمرّر
    `{"L0"}` ⇒ **لا ذراعَ أخرى تُحسَب أصلًا** فيستحيل أن يتسرّب `Δ` حاكمٌ
    من طباعةٍ سهوًا (درسُ `T-PMGATE`: وضعُ الجدوى يُجيز ما يمرّ به وحدَه)."""
    a = arms_of(rows, seed)
    out = {}
    for name, sub in a.items():
        if only is not None and name not in only:
            continue
        out[name] = replay_arm(sub)
    return out


def delta(cur: dict, base: dict) -> dict:
    """`Δ` = `R(ذراع) − R(أساس)` **مقترنًا بالرمز** ⇒ الفاصلُ عنقوديٌّ صادق.

    🔴 والاقترانُ ليس زينة: رمزٌ واحدٌ قد يحمل صفقاتٍ في الذراعين، وفصلُهما
    يُضخّم الاستقلالَ فيُضيّق الفاصلَ كذبًا."""
    g = {}
    for sym in set(cur["g"]) | set(base["g"]):
        n1, s1 = cur["g"].get(sym, (0, 0.0))
        n2, s2 = base["g"].get(sym, (0, 0.0))
        n = max(n1, n2)
        if not n:
            continue
        m1 = (s1 / n1) if n1 else 0.0
        m2 = (s2 / n2) if n2 else 0.0
        g[sym] = (n, n * (m1 - m2))
    return {"g": g, "mean": cur["r"] - base["r"]}


# ══════════ ⑤ الحكم — بنصّ §④ و§⑤ حرفيًّا ══════════
def read_verdict(per_year: dict, pooled: dict) -> dict:
    """يطبّق فروعَ §⑤ **بحرفها** — دالّةٌ نقيّةٌ تُقفَل بجدول حقيقة.

    🔴 **ودرسُ `T-PMGATE` و`T-RSI-RANK` مطبَّقٌ:** المعاييرُ **سنةً سنةً** لا
    مجمَّعةً وحدَها — سقوطُ سنةٍ واحدةٍ ⇒ **الفرعُ 2** لا «لا حكم»،
    و«لا حكم» **للأرضيّة والحرّاس وحدَها**."""
    years = sorted(per_year)
    # ① الفرعُ 3 أوّلًا — أرضيّةُ `L1` أو حارسٌ ساقط
    thin = [y for y in years
            if int(per_year[y].get("l1_pool") or 0) < FLOOR_L1]
    if set(years) != set(GOV_YEARS):
        return {"branch": 3, "why": f"السنواتُ {years} ليست {list(GOV_YEARS)}",
                "rc": RC_NOJUDGE}
    if thin:
        return {"branch": 3, "rc": RC_NOJUDGE,
                "why": "‏`L1` دون الأرضيّة في " + "، ".join(
                    f"{y} ({per_year[y].get('l1_pool')} < {FLOOR_L1})"
                    for y in thin)}
    # ② المعاييرُ الثلاثة — موجبٌ في كلّ سنة **والفاصلُ المجمَّع لا يلمس الصفر**
    crit = {}
    for key, arm in (("ML1", "L0"), ("ML2", "C-MOM"), ("ML3", "C-RAND")):
        pos = all(per_year[y]["d"][arm]["mean"] > 0 for y in years)
        ci = pooled[arm]
        clear = (ci["lo"] > 0) or (ci["hi"] < 0)
        crit[key] = bool(pos and clear and ci["mean"] > 0)
    # ③ الماديّة — المجمَّعُ مقابلَ `L0`
    crit["ML4"] = bool(pooled["L0"]["mean"] >= MATERIAL)
    ok = all(crit.values())
    return {"branch": (1 if ok else 2), "rc": RC_OK, "crit": crit,
            "why": ("كلُّ المعايير عبرت" if ok else
                    "الساقط: " + "، ".join(k for k, v in crit.items() if not v))}


def _pool_ci(dparts: list) -> dict:
    """يجمع فروقَ السنوات الثلاث في فاصلٍ **مجمَّعٍ واحد** عنقودُه (سنة‖رمز)."""
    g = {}
    for y, d in dparts:
        for sym, v in d["g"].items():
            g[f"{y}|{sym}"] = v
    ci = boot_ci(g, n=BOOT, seed=BOOT_SEED)
    return ci or {"lo": 0.0, "hi": 0.0, "mean": 0.0, "n": 0, "k": 0}


def main() -> int:                                               # noqa: PLR0911, PLR0912, PLR0915
    _log("📏🪜 T-MA-LADDER — «احسب بالأيام من وين هابط · 20 أو 30 أو 50»")
    _log("🔒 قراءةٌ فقط · صفرُ مسٍّ بجذر · لا LOGIC_VERSION · ولا يُشحَن شيء.")
    spec = (os.environ.get("MALADDER_POOL") or "").strip()
    dry = str(os.environ.get("MALADDER_DRY", "")).strip() == "1"
    tsv = str(os.environ.get("MALADDER_TSV", "")).strip() == "1"
    if not spec:
        _log("⛔ MALADDER_POOL مطلوب (‏`2023:path,2024:path,2025:path`) — خروج 2")
        return RC_INPUT
    pool = {}
    for part in spec.split(","):
        if ":" not in part:
            _log(f"⛔ جزءٌ غيرُ صالح: {part}")
            return RC_INPUT
        y, path = part.split(":", 1)
        pool[y.strip()] = path.strip()
    if not dry and sorted(pool) != sorted(GOV_YEARS):
        _log(f"⛔ الحكمُ يلزمه **السنواتُ الثلاث بعينها** {GOV_YEARS} (§④) — "
             f"والمُعطى {sorted(pool)}. لسنةٍ واحدة استعمل وضعَ الجدوى.")
        return RC_INPUT

    # ══ الحرّاسُ **قبل أيّ رقم** ══
    if not selfcheck_readonly():
        _log("⛔ `V-M5` فحصُ «قراءةٌ فقط» سقط — خروج 3")
        return RC_TOOL
    if not rsi_rank_untouched():
        _log("⛔ `V-M6`-ب — محورٌ مُغلَقٌ يُلمَس — خروج 3")
        return RC_TOOL
    ok6, diff = production_untouched()
    _log(f"🔒 `V-M6`-أ الجذورُ الاثنا عشر {'✅' if ok6 else '⛔'} "
         f"(المختلف: {diff or 'لا شيء'})")
    if not ok6:
        return RC_TOOL
    snaps = trail_snapshots()
    _log(f"🔒 `V-M1` لقطاتُ `trail.yml`: {snaps}")
    if len(snaps) != 3:
        _log("⛔ `V-M1` — تعذّرت قراءةُ لقطات `trail.yml` — خروج 5")
        return RC_GUARD
    _log(f"📌 clamp=[{CLAMP_LO}, {CLAMP_HI}] ⟶ {PERIODS} · W={W} "
         f"(حساسيّةٌ وصفيّةٌ {W_SENS}) · السعة={int(CAPACITY)} · "
         f"أرضيّةُ L1={FLOOR_L1} · الماديّة={MATERIAL:+.2f}R")
    _log(f"📌 بوتستراب {BOOT} ببذرة {BOOT_SEED} · بذرةُ C-RAND {RAND_SEED}")

    per_year, dparts, all_pl = {}, {"L0": [], "C-MOM": [], "C-RAND": []}, []
    for y in sorted(pool):
        meta = _measure_year(y, pool[y])
        if not meta:
            _log(f"⛔ تعذّرت لقطةُ {y} — خروج 4")
            return RC_SNAP
        if list(meta.get("split_ma_periods") or []) != list(PERIODS):
            _log(f"⛔ §⑦ — `SPLIT_MA_PERIODS` تحرّكت: {meta.get('split_ma_periods')}")
            return RC_GUARD
        rows = json.load(open(meta["path"], encoding="utf-8"))
        a = arms_of(rows)
        mat = len(a["L1"])
        rate = (100.0 * mat / len(rows)) if rows else 0.0
        # 🔒 `V-M4` — معدّلُ النضج **قبل** أيّ `Δ`، ومعه إعلانُ الانحلال
        _log(f"\n📏 سنة {y} · as-of {meta['asof']} · إشاراتٌ {len(rows)} · "
             f"ناضجةٌ {mat} ({rate:.2f}%) · `V-M4`"
             + ("  🔴 **انحلال**" if rate in (0.0, 100.0) else ""))
        for w in W_SENS:
            wn = sum(1 for t in rows if t.get(f"matured_w{w}") is True)
            _log(f"   حساسيّةُ W={w} (وصفيّة): ناضجةٌ {wn} "
                 f"({100.0 * wn / len(rows) if rows else 0:.2f}%)")
        nd = {p: sum(1 for t in rows if t.get("n") == p) for p in PERIODS}
        _log(f"   توزيعُ `n`: {nd} · بلا `n`: "
             f"{sum(1 for t in rows if t.get('n') is None)}")
        alt = sum(1 for t in rows if t.get("matured_alt") is True)
        _log(f"   التعريفُ البديلُ `alt` (وصفيٌّ لا يحكم): ناضجةٌ {alt}")
        if dry:
            m = measure(rows, only={"L0"})
            _log(f"   🧪 جدوى — L0: مأخوذةٌ {m['L0']['taken']} · "
                 f"مُعبَّأةٌ {m['L0']['filled']} · d100 {m['L0']['d100']}")
            per_year[y] = {"l1_pool": mat, "d": {}}
            continue
        m = measure(rows)
        all_pl += m["L0"].get("payloads") or []
        # 🔒 `V-M2` — `L0` يُعيد الرقمَ المنشور بت-بت
        want = PUBLISHED_L0_D100.get(y)
        got = m["L0"]["d100"]
        _log(f"   🔒 `V-M2` d100(L0) = {got} · المنشور {want} "
             f"{'✅' if got == want else '⛔'}")
        if want is not None and got != want:
            _log("⛔ `V-M2` — الأساسُ لا يُعيد الرقمَ المنشور — خروج 6")
            return RC_BASE
        # 🔒 `V-M3` — حجمُ الضبطين = حجمُ `L1` بالضبط
        sz = {k: m[k]["pool"] for k in ("L1", "C-MOM", "C-RAND")}
        ok3 = sz["C-MOM"] == sz["L1"] == sz["C-RAND"]
        _log(f"   🔒 `V-M3` أحجامُ المجموعات {sz} {'✅' if ok3 else '⛔'}")
        if not ok3:
            _log("⛔ `V-M3` — المقارنةُ ليست تحت الميزانيّة نفسِها — خروج 5")
            return RC_GUARD
        _log("   الذراع │ مجموعة │ مأخوذة │ تعبئة │ d100 │     R     │ عن L0")
        for name in ("L0", "L1", "L2", "C-MOM", "C-RAND"):
            a2 = m[name]
            dd = "" if name == "L0" else f"{a2['r'] - m['L0']['r']:+.4f}"
            _log(f"   {name:>6} │ {a2['pool']:6d} │ {a2['taken']:6d} │"
                 f" {a2['filled']:5d} │ {a2['d100']:4d} │ {a2['r']:+9.4f} │ {dd}")
        for arm in ("L0", "C-MOM", "C-RAND"):
            dparts[arm].append((y, delta(m["L1"], m[arm])))
        per_year[y] = {"l1_pool": mat, "rate": round(rate, 4),
                       "d": {arm: {"mean": m["L1"]["r"] - m[arm]["r"]}
                             for arm in ("L0", "C-MOM", "C-RAND")}}
        if tsv:
            with open(OUT_ROWS, "a", encoding="utf-8") as fh:
                for t in rows:
                    fh.write(json.dumps(
                        {k: t.get(k) for k in
                         ("symbol", "date", "bars_since_peak", "n", "matured",
                          "alt_bars", "alt_n", "matured_alt")},
                        ensure_ascii=False) + "\n")
    if dry:
        _log("\n🧪 وضعُ الجدوى — **صفرُ `Δ` وصفرُ فاصلٍ وصفرُ حكم** (بنيةً لا وعدًا)")
        return RC_OK

    # 🔒 `V-M7` — شاهدُ هُويّة المقياس
    n_id, bad_id = r_identity(all_pl)
    _log(f"\n🔒 `V-M7` `r_fixed` = `r_unit` على {n_id} صفًّا · مخالف={bad_id} "
         f"{'✅' if bad_id == 0 else '⛔'}")
    if bad_id:
        _log("⛔ `V-M7` — مقياسا العقد والأداة افترقا — خروج 5")
        return RC_GUARD

    pooled = {arm: _pool_ci(dparts[arm]) for arm in dparts}
    _log("\n📐 المجمَّع (فاصلٌ عنقودُه سنة‖رمز):")
    for key, arm in (("ML1", "L0"), ("ML2", "C-MOM"), ("ML3", "C-RAND")):
        c = pooled[arm]
        ys = " · ".join(f"{y}:{per_year[y]['d'][arm]['mean']:+.4f}"
                        for y in sorted(per_year))
        _log(f"   {key} L1−{arm:<7} {c['mean']:+.4f}R "
             f"[{c['lo']:+.4f}, {c['hi']:+.4f}] · أزواج {c['n']} · "
             f"رموز {c['k']} │ {ys}")
    v = read_verdict(per_year, pooled)
    _log("\n" + "═" * 64)
    _log(f"JUDGE branch={v['branch']} · {v['why']}")
    if v.get("crit"):
        _log("   " + " · ".join(f"{k}{'✅' if s else '🔴'}"
                                for k, s in v["crit"].items()))
    _log("⛔ ولا يُشحَن شيءٌ بهذا العقد مهما كانت النتيجة (§⑦) — "
         "والفرعُ 1 اقتراحٌ على المالك لا تنفيذ.")
    return v["rc"]


if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[1] == "--child":
        sys.exit(run_child(sys.argv[2], sys.argv[3]))
    sys.exit(main())
