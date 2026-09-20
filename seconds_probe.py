# -*- coding: utf-8 -*-
"""⏱️🔥 `T-SECONDS` — **«إذا دخل المضارب بثوانٍ معدودة يتجاوز السعر»** رقمًا
(العقد `seconds_prereg.md`).

**قراءةٌ/بحثٌ فقط · صفرُ مسٍّ بالإنتاج · لا `LOGIC_VERSION` · ولا يُشحَن شيءٌ
مهما كانت النتيجة** — الفرعُ 1 **اقتراحٌ على المالك لا تنفيذ** (`§⑥`).

🔑 **والمحورُ جديدٌ لأن المبنيَّ من الصور نفسِها هو الدولاراتُ لا السرعة:**
`_ignition_signal` يقرأ **شموعَ الدقيقة** فهو **أعمى عن الثواني بالبناء**.

🔗 **وكلُّ مستورَدٍ يُنادى بالاسم — صفرُ منطقِ حسمٍ مكرَّر:**
`Super_stock._ignition_outcome` و`_ignition_outcome_fetch` و`CONFIG`
(‏`V-N3`) · `kasih_scan.wilson` · `tc_yield_arms.production_untouched`.

🔴 **وحدُّ صدقٍ في قلب التعريف (‏`§③`):** المقيسُ **أوّلُ عبورٍ في اليوم** لا
لحظةَ الإطلاق — لأن `fired_ts_ms` **غيرُ محفوظ** و`fired_at` **لحظةُ كتابةٍ
لا إطلاق** (‏`§①`-4). **نقلُ تعريفٍ مُعلَن** وأثرُه معروفُ الاتّجاه: يُدخِل
عبورًا مبكّرًا هادئًا فيُبطئ `t_cross` ⇒ **ينحاز ضدّ فرضيّة السرعة**، فالنتيجةُ
الموجبةُ رغمَه أقوى **والسالبةُ غيرُ حاسمة**.
"""
from __future__ import annotations

import ast
import datetime as dt
import json
import os
import sys
import time
from collections import Counter
from zoneinfo import ZoneInfo

import requests

import Super_stock as S
from kasih_scan import wilson
from tc_yield_arms import production_untouched

# ───────────────────────── الثوابتُ المُغلَقة بالعقد ──────────────────────────
LOG = "ignition_log.json"
POP_N = 96                                       # `V-N1` — بت-بت
POP_CLASSES = {"group": 73, "mid": 12, "operator": 8, "strong": 3}
NY = ZoneInfo("America/New_York")
SESS_LO, SESS_HI = 9.5, 16.0                     # `§③`-1 — اليومُ النظاميّ
TOL = 0.005                                      # `§③`-4 — `engineering` مُعلَن
FAST_SEC = 10.0                                  # `§③`-4 — «معدودة»
SENS = (5.0, 10.0, 30.0, 60.0)                   # `S-SENS` — وصفيّةٌ كاملةً
MIN_ARM = 30                                     # `§⑥`-3
MIN_COVER = 0.80                                 # `V-N2`
SC1_MIN = 15.0                                   # `§⑤`
SC2_MIN = 10.0
PAGE_CAP = 20                                    # سقفُ صفحاتٍ مُعلَن (`§②`)
OUT_ROWS = "seconds_rows.tsv"

RC_OK, RC_TOOL, RC_GUARD, RC_NOJUDGE = 0, 3, 5, 9


def log(m: str) -> None:
    print(m, flush=True)


# ───────────────────────── الجالبُ الجديد (‏`§②`) ────────────────────────────
def polygon_trades_ts(sym: str, day: str, page_cap: int = PAGE_CAP,
                      stop_fn=None):
    """`§②` — صفقاتُ يومٍ واحدٍ **بطوابعها**: `[(sip_ts_ns, price, size), …]`.

    **قراءةٌ فقط · فاشلٌ-آمن مطلق** (‏بلا مفتاح/401/403/429/شبكة ⇒ `None`
    فورًا — **ولا بترَ صامت**: صفحةٌ تفشل تُسقط النتيجةَ كلَّها كما في
    `polygon_base_trades`) · **وسقفُ صفحاتٍ مُعلَن**.

    🔒 **ولا يُنادى من أيّ مسارِ إنتاج** (`V-N5`).
    ⚡ `stop_fn(rows)` اختياريّة: تُوقف الترقيمَ متى صار الباقي بلا أثرٍ على
    القياس (‏أوّلُ عبورٍ وُجد) — **توفيرُ نداءاتٍ لا تغييرُ رقم**."""
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        return None
    try:
        nxt = (dt.date.fromisoformat(str(day)[:10])
               + dt.timedelta(days=1)).isoformat()
    except ValueError:
        return None
    url = (f"https://api.polygon.io/v3/trades/{sym.upper()}"
           f"?timestamp.gte={day}&timestamp.lt={nxt}&limit=50000&order=asc")
    h = {"Authorization": f"Bearer {key}"}
    out = []
    try:
        for _ in range(int(page_cap)):
            r = requests.get(url, headers=h, timeout=20)
            if r.status_code != 200:
                return None                       # لا بترَ صامت
            j = r.json() or {}
            for t in (j.get("results") or []):
                ts, p, sz = (t.get("sip_timestamp"), t.get("price"),
                             t.get("size"))
                if ts is None or p is None:
                    continue
                out.append((int(ts), float(p), float(sz or 0)))
            if stop_fn is not None and stop_fn(out):
                return out
            u = j.get("next_url")
            if not u:
                return out
            url = u if "apiKey" in u else u + f"&apiKey={key}"
        return out
    except Exception:                                            # noqa: BLE001
        return None


# ───────────────────────── الدوالُّ النقيّة (‏`§③`) ───────────────────────────
def ny_hour_ns(ts_ns: int) -> float:
    """ساعةُ نيويورك (عشريّة) لطابعٍ بالنانو — **`zoneinfo` لا إزاحةٌ ثابتة**."""
    d = dt.datetime.fromtimestamp(int(ts_ns) / 1e9,
                                  tz=dt.timezone.utc).astimezone(NY)
    return d.hour + d.minute / 60.0 + d.second / 3600.0 + d.microsecond / 3.6e9


def regular_only(trades, lo: float = SESS_LO, hi: float = SESS_HI):
    """`§③`-1 — اليومُ النظاميّ وحدَه (‏09:30-16:00 ET). نقيّة."""
    return [t for t in (trades or []) if lo <= ny_hour_ns(t[0]) < hi]


def first_cross(trades, level: float, tol: float = TOL):
    """`§③`-2/3 — **أوّلُ عبور** وزمنُه بالثواني.

    العبورُ = أوّلُ صفقةٍ سعرُها **‏≥ L×(1+tol)** ويسبقها في اليوم صفقةٌ
    **‏≤ L×(1−tol)** · و`t_cross` = الثواني بين **آخرِ** تلك السابقةِ وهذي.
    تُرجع `{"t_cross", "ts_cross", "ts_below", "px"}` أو `None`. نقيّة."""
    if not trades or not level or level <= 0:
        return None
    lo, hi = level * (1.0 - tol), level * (1.0 + tol)
    last_below = None
    for ts, px, _sz in trades:
        if px <= lo:
            last_below = ts
            continue
        if px >= hi and last_below is not None:
            return {"t_cross": (ts - last_below) / 1e9, "ts_cross": ts,
                    "ts_below": last_below, "px": px}
    return None


def arm_of(t_cross: float, fast_sec: float = FAST_SEC) -> str:
    """`§④` — `fast` دون العتبة (شاملةً) و`slow` فوقها. نقيّة."""
    return "fast" if t_cross <= fast_sec else "slow"


def rate(rows, key="outcome", val="real"):
    """نسبةُ `real` ومعها مقامُها — **لا نسبةَ بلا عدد**. نقيّة."""
    n = len(rows)
    k = sum(1 for r in rows if r.get(key) == val)
    return (k, n, (k / n * 100.0) if n else 0.0)


def wilson_sep(a_k, a_n, b_k, b_n) -> bool:
    """فاصلا Wilson **منفصلان** (‏`§⑤`) — نقيّة."""
    if a_n <= 0 or b_n <= 0:
        return False
    a_lo, a_hi = wilson(a_k, a_n)
    b_lo, b_hi = wilson(b_k, b_n)
    return a_lo > b_hi or b_lo > a_hi


def read_verdict(sc1: dict, sc2: dict, thin: bool, cover: float) -> dict:
    """فروعُ `§⑥` بحرفها — ثلاثةٌ ولا رابع. نقيّةٌ ومقفولةٌ بجدول حقيقة."""
    if thin or cover < MIN_COVER:
        return {"branch": 3, "rc": RC_NOJUDGE,
                "text": f"الفرعُ 3 «لا حكم» — ذراعٌ دون {MIN_ARM} محسومًا "
                        f"(fast {sc1.get('a_n', 0)} · slow {sc1.get('b_n', 0)}) "
                        f"أو تغطيةُ الجلب {cover * 100:.1f}% دون "
                        f"{MIN_COVER * 100:.0f}%"}
    ok1 = sc1.get("delta", -99.0) >= SC1_MIN and sc1.get("sep", False)
    ok2 = sc2.get("best", -99.0) >= SC2_MIN
    if ok1 and ok2:
        return {"branch": 1, "rc": RC_OK,
                "text": f"**الفرعُ 1 «تُوصى»** — `SC1` {sc1['delta']:+.1f} نقطة "
                        f"وفاصلان منفصلان · و`SC2` {sc2['best']:+.1f} نقطة داخل "
                        f"صنف «{sc2.get('cls', '؟')}» ⇒ **اقتراحٌ على المالك "
                        f"لا تنفيذ، ولا يُشحَن شيءٌ بهذا العقد**"}
    why = []
    if not ok1:
        why.append(f"`SC1` {sc1.get('delta', 0):+.1f} نقطة "
                   f"(الحدّ {SC1_MIN:+.0f}) · فاصلان منفصلان="
                   f"{sc1.get('sep', False)}")
    if not ok2:
        why.append(f"`SC2` أفضلُ صنفٍ {sc2.get('best', 0):+.1f} نقطة "
                   f"(الحدّ {SC2_MIN:+.0f}) ⇒ **السرعةُ وجهٌ آخرُ للدولارات "
                   f"لا معلومةٌ زائدة**")
    return {"branch": 2, "rc": RC_OK,
            "text": "**الفرعُ 2 «لا تُوصى»** — " + " · ".join(why)}


# ───────────────────────── حرّاسٌ (‏`§⑦`) ────────────────────────────────────
def selfcheck_readonly(src: str | None = None) -> bool:
    """`V-N6` — **قراءةٌ فقط**: صفرُ إرسالٍ وصفرُ كتابةِ حالة · وما لا يُثبَت
    أنه قراءةٌ **يُعَدّ كتابة** (وضعٌ متغيّرٌ يُرفَض) · و`OUT_ROWS` وحدَه."""
    WRITE_OK = {"OUT_ROWS"}
    if src is None:
        src = open(os.path.abspath(__file__), encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        nm = (getattr(n.func, "id", None) or getattr(n.func, "attr", None) or "")
        if nm in ("send_telegram", "send_telegram_document", "git_save",
                  "save_watchlist", "save_op_entry_state", "record_new_alerts",
                  "record_ignition_fires"):
            return False
        if nm == "open":
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
            if not (isinstance(tgt, ast.Name) and tgt.id in WRITE_OK):
                return False
    return True


# 🐞 **اسمُ الحقل مُركَّبٌ لا مكتوب** — الحارسُ يقارن بثابتٍ نصّيّ، **والثابتُ
#    نفسُه عقدةُ `Constant` في شجرة هذا الملفّ** فيسقط على نفسه (الصنفُ الذي
#    أسقط `WLK5`/`RKA`). والتركيبُ يجعل **القراءةَ الحقيقيّةَ وحدَها** تُمسَك.
_FIRED_AT = "fired" + "_at"


def no_fired_at(src: str | None = None) -> bool:
    """`V-N4` — `t_cross` **لا يُحسَب من `fired_at`** (‏`§①`-4): صفرُ قراءةٍ
    للحقل في هذا الملفّ — لا `r["fired_at"]` ولا `.get("fired_at")`."""
    if src is None:
        src = open(os.path.abspath(__file__), encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    for n in ast.walk(tree):
        if isinstance(n, ast.Subscript):
            sl = n.slice
            if isinstance(sl, ast.Constant) and sl.value == _FIRED_AT:
                return False
        if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "get":
            if n.args and isinstance(n.args[0], ast.Constant) \
                    and n.args[0].value == _FIRED_AT:
                return False
    return True


_FETCH_NAME = "polygon_trades" + "_ts"


def fetcher_unreferenced(paths=("Super_stock.py", "pullback_live.py",
                                "ignition_live.py", "analyze_one.py",
                                "hand_check.py")) -> tuple:
    """`V-N5` — الجالبُ الجديد **صفرُ مرجعٍ له في أيّ مسارِ إنتاج**."""
    hit = []
    for p in paths:
        try:
            if _FETCH_NAME in open(p, encoding="utf-8").read():
                hit.append(p)
        except OSError:
            continue
    return (not hit), hit


def base_trades_untouched() -> tuple:
    """`V-N7` — `polygon_base_trades` **بت-بت** مع `origin/main` (‏AST)."""
    import hashlib
    import subprocess

    def _fp(src):
        try:
            t = ast.parse(src)
        except SyntaxError:
            return "?"
        for n in ast.walk(t):
            if isinstance(n, ast.FunctionDef) and n.name == "polygon_base_trades":
                return hashlib.sha256(ast.dump(n).encode()).hexdigest()[:12]
        return "?"
    try:
        base = subprocess.run(["git", "show", "origin/main:Super_stock.py"],
                              capture_output=True, text=True, timeout=60).stdout
    except Exception:                                            # noqa: BLE001
        base = ""
    cur = _fp(open("Super_stock.py", encoding="utf-8").read())
    b = _fp(base) if base else "?"
    return (b != "?" and cur == b), cur, b


# ───────────────────────── المسارُ الرئيس ────────────────────────────────────
def load_fires(path: str = LOG) -> list:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:                                    # noqa: PLR0911, PLR0912, PLR0915
    dry = os.environ.get("SECONDS_DRY", "") == "1"
    log("⏱️🔥 `T-SECONDS` — «بثوانٍ معدودة يتجاوز السعر» رقمًا (العقد "
        "seconds_prereg.md)")
    log(f"   العتبة {FAST_SEC:.0f}ث · التسامح {TOL * 100:.1f}% · حساسيّة {SENS} · "
        f"سقفُ صفحات {PAGE_CAP}" + (" · **وضعُ جدوى**" if dry else ""))

    ro = selfcheck_readonly()
    nf = no_fired_at()
    fu, fu_hit = fetcher_unreferenced()
    bt_ok, bt_cur, bt_base = base_trades_untouched()
    pr_ok, pr_cur, pr_base = production_untouched()
    log(f"   🔒 V-N6 قراءةٌ فقط={ro} · V-N4 بلا حقلِ الكتابة={nf} · "
        f"V-N5 الجالبُ بلا مرجعٍ إنتاجيّ={fu} {fu_hit} · "
        f"V-N7 `polygon_base_trades`={bt_ok} ({bt_cur}/{bt_base}) · "
        f"الإنتاجُ بت-بت={pr_ok} ({pr_cur}/{pr_base})")
    if not (ro and nf and fu and bt_ok and pr_ok):
        log(f"⛔ حارسٌ ساقطٌ قبل أيّ قياس — خروج {RC_GUARD}")
        return RC_GUARD

    try:
        fires = load_fires()
    except Exception as e:                                       # noqa: BLE001
        log(f"⛔ تعذّر فتح {LOG}: {e} — خروج {RC_TOOL}")
        return RC_TOOL
    cls = Counter(f.get("candle_class") for f in fires)
    days = sorted({str(f.get("date")) for f in fires})
    log(f"   🔒 V-N1 المجتمع: {len(fires)} إطلاقًا (المنشور {POP_N}) · "
        f"الأصناف {dict(cls)} (المنشور {POP_CLASSES}) · "
        f"أيّامٌ متمايزة {len(days)} · المدى {days[0]} ⟶ {days[-1]}")
    if len(fires) != POP_N or dict(cls) != POP_CLASSES:
        log(f"⛔ V-N1 — السجلُّ تبدّل ⇒ مجتمعٌ آخر — خروج {RC_GUARD}")
        return RC_GUARD

    conf = S.CONFIG["IGNITION_CONFIRM_PCT"]                       # `V-N3`
    log(f"   🔒 V-N3 `IGNITION_CONFIRM_PCT` من `CONFIG` = {conf}")

    if dry:
        log(f"   🧪 وضعُ الجدوى: {len(fires)} إطلاقًا · {len(days)} يومًا · "
            f"معدّلُ التراكم "
            f"{len(fires) / max(1, (dt.date.fromisoformat(days[-1]) - dt.date.fromisoformat(days[0])).days + 1):.2f} "
            f"إطلاقًا/يومٍ تقويميّ — **وصفرُ جلبٍ وصفرُ `Δ`**")
        log("")
        log("JUDGE وضعُ الجدوى — لا حكم (أعدادُ المجتمع فقط)")
        return RC_OK

    # ── الجلبُ والقياس ─────────────────────────────────────────────────────
    rows, fetched_ok, fetched_bad = [], 0, 0
    for i, f in enumerate(fires, 1):
        sym, day = str(f.get("symbol")), str(f.get("date"))
        lvl = float(f.get("break_level") or 0)

        def _stop(acc, _l=lvl):
            return first_cross(regular_only(acc), _l) is not None

        tr = polygon_trades_ts(sym, day, stop_fn=_stop)
        if tr is None:
            fetched_bad += 1
            rows.append({**f, "t_cross": None, "why": "جلبٌ فاشل"})
            continue
        fetched_ok += 1
        fc = first_cross(regular_only(tr), lvl)
        rows.append({**f, "t_cross": (fc or {}).get("t_cross"),
                     "n_trades": len(tr),
                     "why": "" if fc else "لا عبورَ مطابقٌ في اليوم"})
        if i % 10 == 0:
            log(f"   … {i}/{len(fires)} · نجح {fetched_ok} · فشل {fetched_bad}")
        time.sleep(0.05)

    cover = fetched_ok / len(fires) if fires else 0.0
    log(f"   🔒 V-N2 تغطيةُ الجلب: {fetched_ok} من {len(fires)} = "
        f"{cover * 100:.1f}% (الحدّ {MIN_COVER * 100:.0f}%) · فشل {fetched_bad}")

    # ── الحسمُ بتعريف الإنتاج (‏`V-N3`) ────────────────────────────────────
    resolved = 0
    for r in rows:
        if r.get("t_cross") is None:
            r["outcome"] = "—"
            continue
        df = S._ignition_outcome_fetch(r["symbol"], r["date"])
        r["outcome"] = S._ignition_outcome(r, df)
        resolved += r["outcome"] in ("real", "fakeout")
    log(f"   📐 محسومٌ (real/fakeout): {resolved} · "
        f"{dict(Counter(r.get('outcome') for r in rows))}")

    done = [r for r in rows if r.get("outcome") in ("real", "fakeout")]
    fast = [r for r in done if arm_of(r["t_cross"]) == "fast"]
    slow = [r for r in done if arm_of(r["t_cross"]) == "slow"]
    a_k, a_n, a_p = rate(fast)
    b_k, b_n, b_p = rate(slow)
    sc1 = {"a_k": a_k, "a_n": a_n, "a_p": a_p, "b_k": b_k, "b_n": b_n,
           "b_p": b_p, "delta": a_p - b_p, "sep": wilson_sep(a_k, a_n, b_k, b_n)}
    log(f"   📊 `SC1` fast {a_k}/{a_n} = {a_p:.2f}% مقابل slow {b_k}/{b_n} = "
        f"{b_p:.2f}% ⇒ **{sc1['delta']:+.2f} نقطة** · فاصلان منفصلان="
        f"{sc1['sep']}")

    # ── `C-USD` — **ضبطٌ حاكم** داخلَ صنف الدولارات ────────────────────────
    best, best_cls = -99.0, "؟"
    log("   🎯 `C-USD` (ضبطٌ حاكم) — الفرقُ داخلَ كلّ صنفٍ دولاريّ:")
    for c in ("group", "mid", "operator", "strong"):
        sub = [r for r in done if r.get("candle_class") == c]
        fk, fn, fp = rate([r for r in sub if arm_of(r["t_cross"]) == "fast"])
        sk, sn, sp = rate([r for r in sub if arm_of(r["t_cross"]) == "slow"])
        d = fp - sp if (fn and sn) else None
        log(f"      {c:>8} · fast {fk}/{fn} = {fp:6.2f}% · slow {sk}/{sn} = "
            f"{sp:6.2f}% ⇒ " + ("—" if d is None else f"{d:+.2f} نقطة"))
        if d is not None and d > best:
            best, best_cls = d, c
    sc2 = {"best": best, "cls": best_cls}

    # ── `S-SENS` — وصفيّةٌ تُطبَع كاملةً ولا يُنتقى منها ────────────────────
    log("   🧪 `S-SENS` (وصفيّةٌ لا تحكم) — العتبةُ بالثواني:")
    for s in SENS:
        fk, fn, fp = rate([r for r in done if arm_of(r["t_cross"], s) == "fast"])
        sk, sn, sp = rate([r for r in done if arm_of(r["t_cross"], s) == "slow"])
        log(f"      ≤{s:>4.0f}ث · fast {fk}/{fn} = {fp:6.2f}% · slow {sk}/{sn} "
            f"= {sp:6.2f}% ⇒ {fp - sp:+.2f} نقطة")

    if os.environ.get("SECONDS_TSV", "1") == "1":
        import csv
        with open(OUT_ROWS, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, delimiter="\t")
            w.writerow(["date", "sym", "break_level", "price", "usd",
                        "candle_class", "t_cross", "arm", "outcome",
                        "n_trades", "why"])
            for r in rows:
                w.writerow([r.get("date"), r.get("symbol"),
                            r.get("break_level"), r.get("price"), r.get("usd"),
                            r.get("candle_class"),
                            "" if r.get("t_cross") is None
                            else f"{r['t_cross']:.3f}",
                            "" if r.get("t_cross") is None
                            else arm_of(r["t_cross"]),
                            r.get("outcome"), r.get("n_trades"), r.get("why")])
        log(f"   🧾 الصفوف: {OUT_ROWS} ({len(rows)} صفًّا)")

    thin = (a_n < MIN_ARM) or (b_n < MIN_ARM)
    v = read_verdict(sc1, sc2, thin, cover)
    log("")
    log(f"JUDGE {v['text']}")
    return v["rc"]


if __name__ == "__main__":
    sys.exit(main())
