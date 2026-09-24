#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔬📰② `T-PRE-EDGAR-2` — **الدراسة**: هل يسبق إيداعُ SEC الليليُّ انفجارَ ‏+100% في البريماركت؟

العقد: `edgar2_prereg.md` (مدموجٌ `e6068f58`) **وملحقُه §⑩** (مدموجٌ قبل هذا الملفّ) · والمرحلةُ صفر
v2 عبرت (‏`edgar2_result.md §①` · التوقيتُ `B`: لاحقةُ `Z` صادقة).

**الحاكم (§① حرفيًّا):** `EG1` = نسبةُ `CASE` التي فيها إيداعٌ من `FORMS` قُبل داخل
‏[16:00 نيويورك من يوم التداول السابق ، 03:50 نيويورك من اليوم] · `EG2` مثلُها لـ`CTRL` ·
**النجاح ⟺ الفرقُ ‏≥ 15.0 نقطة ∧ فاصلا Wilson 95% منفصلان تمامًا** (‏`EG6` حارسُ النجاح — §⑩).

**الترتيبُ المثبَّت (§⑤-ب ‏+ §⑩) وأوّلُ سقوطٍ يُنهي:** `V-E8` ⟶ `V-E0` ⟶ اللوحة (`V-E1` · `V-E2` ·
`V-E14` · `V-E4`) ⟶ القصّ (`EG3`-`EG5`) ⟶ الجلب (`V-E10`) ⟶ `V-E9` ⟶ `V-E11` ⟶ الإصابات
(`V-E13`) ⟶ `V-E5` ⟶ **الحاكم** ⟶ `EG6` (إن عبر الحاكم).

🔒 **قراءةٌ فقط** (‏`V-E6`) · **`V-E7`** لا `sec_recent_filings` · **`V-E12`** اسمُ حقل تاريخ الإيداع لا
   يَرِد هنا إطلاقًا (التحقّقُ منه داخل `edgar2_probe.tz_verdict` وحدَها) · والتوقيتُ لا يُفترَض: يُحسَم
   في التشغيلة نفسِها مرّتين (العيّنة ثم المجتمع).

🔁 **إعادةُ الاستعمال بالاسم (بُنيت لـ…):**
   · `edgar2_probe.stage0`/`tz_verdict`/`parse_acc`/`to_ny`/`FORMS`/`SHIPPED_SLEEP` — **بُنيت لهذا العقد
     نفسِه** (المرحلة صفر v2 وحسمُ التوقيت) ⇒ لا مصدرَ ثانٍ لتفسير الطابع.
   · `edgar_probe.load_year_symbols`/`sec_get`/`SUB_URL` — **بُنيت للمرحلة صفر** (رموزُ العيّنة وجلبُ
     `submissions`) ⇒ `V-E0` يُعاد بالعيّنة نفسِها بت-بت.
   · `presession_report.wilson`/`MAX_KEYS` و`presession_feats.ROW_*` — **بُنيت لتقارير `T-PRESESSION`**
     التي أنتجت الـ702 ⇒ تعريفُ `CASE` وفاصلُه من المصدر نفسِه لا نسخة.
   · `market_calendar.HOLIDAYS`/`EARLY_CLOSES` — **بُنيت لتقويم الإنتاج** ⇒ يومُ التداول السابق عينُ
     `presession_radar.prev_bday` بلا احتياطِه الصامت (تعذّرُ التقويم هنا خروج 3 لا تخمين).
"""

from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402

import Super_stock as S  # noqa: E402
import edgar2_probe as P2  # noqa: E402
import market_calendar as MC  # noqa: E402
import presession_feats as PF  # noqa: E402
import presession_report as PR  # noqa: E402
from edgar_probe import SUB_URL, load_year_symbols, sec_get  # noqa: E402

# ---- ثوابتُ العقد ----
YEAR = "2025"                       # §③-1
SESS = "PM"                         # §②-ب-2
MAXS_KEY = PR.MAX_KEYS[0]           # "maxs" — النافذةُ 0 = الجلسةُ كاملة (‏presession_report)
CASE_MIN = PR.CEIL_HUNDRED          # ‏+100% (‏presession_report.py السطر 478)
PUBLISHED_CASE = 702                # §②-ب-2 · V-E1
V_E1_TOL = 0.02                     # ‏±2%
EG_DIFF_MIN = 15.0                  # §① الحاكم
EG3_MIN, EG4_MIN, EG5_MAX = 100, 100, 40.0          # §⑤ الأرضيّات حرفيًّا
UNKNOWN_MAX_PCT = 2.0               # §⑤-4 V-E11
BOOT_B, BOOT_SEED, BOOT_PCT = 2000, 20260924, 2.5   # §⑤-6 EG6
WIN_START, WIN_END = dt.time(16, 0), dt.time(3, 50)  # §② النافذةُ بنصّها
RETRY_SLEEPS = (2, 4)               # §⑤-2 عطلُ شبكةٍ/5xx ⇒ حتى 3 محاولات
BLOCK_PAUSE = 60                    # §⑤-2 حجبٌ ⇒ توقّفٌ 60ث ومحاولةٌ واحدة
PAGE_MARGIN_DAYS = 7                # §⑤-3/4
FILES_URL = "https://data.sec.gov/submissions/{}"
TZ_WINNER = "B"                     # §⑩ ما حسمته المرحلةُ صفر — ويُعاد حسمُه في التشغيلة
FAMILIES = {                        # §⑤-8 (وصفيّ)
    "F-8K": ("8-K", "8-K/A"),
    "F-424": ("424B1", "424B2", "424B3", "424B4", "424B5", "424B7"),
    "F-REG": ("S-1", "S-1/A", "S-3", "S-3/A"),
}


def log(msg: str = "") -> None:
    print(msg, flush=True)


# ---- دوالٌّ نقيّة: المجتمع واللوحة ----
def _maxs(v):
    """كما في `presession_report.load_cols`: عددٌ ⟵ float · وإلّا `None` (معدوم)."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    f = float(v)
    return None if math.isnan(f) else f


def load_pm_rows(paths, year: str = YEAR) -> tuple:
    """صفوفُ `E1` ⟵ `{يوم: [(رمز، maxs أو None), …]}` لـ`sess == PM` غيرِ الشاهد في السنة.

    يُعيد أيضًا عدّاداتٍ صريحة (كلُّ قصٍّ مُعلَن): الكلّ · الشاهد · خارج الجلسة · خارج السنة ·
    بلا رمز · الـ`maxs` المعدومة.
    """
    per_day, n = {}, {"rows": 0, "wit": 0, "other_sess": 0, "other_year": 0,
                      "no_sym": 0, "pm": 0, "maxs_none": 0, "bad_json": 0}
    for p in paths:
        op = gzip.open if str(p).endswith(".gz") else open
        with op(p, "rt", encoding="utf-8") as fh:
            for ln in fh:
                if not ln.strip():
                    continue
                try:
                    r = json.loads(ln)
                except ValueError:
                    n["bad_json"] += 1
                    continue
                n["rows"] += 1
                if r.get(PF.ROW_WIT):
                    n["wit"] += 1
                    continue
                if r.get(PF.ROW_SESS) != SESS:
                    n["other_sess"] += 1
                    continue
                day = str(r.get(PF.ROW_DAY) or "")
                if not day.startswith(year):
                    n["other_year"] += 1
                    continue
                sym = str(r.get(PF.ROW_SYM) or "").strip().upper()
                if not sym:
                    n["no_sym"] += 1
                    continue
                m = _maxs(r.get(MAXS_KEY))
                if m is None:
                    n["maxs_none"] += 1
                n["pm"] += 1
                per_day.setdefault(day, []).append((sym, m))
    return per_day, n


def build_panel(per_day) -> tuple:
    """§②-ب: `CASE` = `maxs ≥ 100` · `CTRL` = من اليوم نفسِه `maxs < 100` (عدديٌّ منتهٍ) مرتّبًا
    بـ`sha256(f"{day}:{sym}")` تصاعديًّا ⟵ أدنى `N_d` = عددُ `CASE` في ذلك اليوم (1:1).

    🔒 لا يُزال التكرار هنا عمدًا — `V-E14` يمسكه ولا يُخفيه بناءٌ يُطبّع.
    """
    case, ctrl, short = [], [], 0
    for day in sorted(per_day):
        rows = per_day[day]
        ex = sorted(s for s, m in rows if m is not None and m >= CASE_MIN)
        non = [s for s, m in rows if m is not None and math.isfinite(m) and m < CASE_MIN]
        keyed = sorted((hashlib.sha256(f"{day}:{s}".encode("utf-8")).hexdigest(), s) for s in non)
        take = [s for _, s in keyed[:len(ex)]]
        short += len(ex) - len(take)
        case += [(day, s) for s in ex]
        ctrl += [(day, s) for s in take]
    return case, ctrl, short


def panel_digest(case, ctrl) -> str:
    return hashlib.sha256(json.dumps([case, ctrl], ensure_ascii=False).encode("utf-8")).hexdigest()


# ---- دوالٌّ نقيّة: النافذة ----
def prev_trading_day(day_iso: str) -> dt.date:
    """يومُ التداول السابق: يتخطّى السبتَ والأحد و`market_calendar.HOLIDAYS` — **بلا احتياط**."""
    hol = set(MC.HOLIDAYS)
    d = dt.date.fromisoformat(day_iso) - dt.timedelta(days=1)
    while d.weekday() >= 5 or d.isoformat() in hol:
        d -= dt.timedelta(days=1)
    return d


def window_ny(day_iso: str) -> tuple:
    """‏[16:00 نيويورك يومَ التداول السابق ، 03:50 نيويورك اليوم] — مغلقةُ الطرفين (§②)."""
    start = dt.datetime.combine(prev_trading_day(day_iso), WIN_START, tzinfo=P2.NY)
    end = dt.datetime.combine(dt.date.fromisoformat(day_iso), WIN_END, tzinfo=P2.NY)
    return start, end


# ---- دوالٌّ نقيّة: بياناتُ الـCIK والتغطية ----
def page_rec(body):
    """صفحةُ `files[]` ⟵ مصفوفاتُها المتوازية (بالشكل الأعلى أو تحت `filings.recent`) أو `None`
    إن خلت من `acceptanceDateTime` — «صفحةٌ بلا الحقل لا تُغطّي شيئًا» (§⑤-4)."""
    if not isinstance(body, dict):
        return None
    rec = body if "form" in body else ((body.get("filings") or {}).get("recent") or {})
    return rec if isinstance(rec.get("acceptanceDateTime"), list) else None


def cik_filings(sub, pages, interp: str = TZ_WINNER) -> tuple:
    """‏[(نموذج، لحظةُ نيويورك)] لإيداعات `FORMS` من `recent` والصفحات المجلوبة ‏+ عددُ غير المحلَّل."""
    out, bad = [], 0
    recs = [((sub or {}).get("filings") or {}).get("recent") or {}] + [p for p in pages if p]
    for rec in recs:
        forms = rec.get("form") or []
        accs = rec.get("acceptanceDateTime") or []
        for i, f in enumerate(forms):
            if f not in P2.FORMS:
                continue
            p = P2.parse_acc(accs[i] if i < len(accs) else None)
            if p is None:
                bad += 1
                continue
            out.append((f, P2.to_ny(p, interp)))
    return out, bad


def recent_oldest_ny(sub, interp: str = TZ_WINNER):
    rec = ((sub or {}).get("filings") or {}).get("recent") or {}
    ts = [P2.to_ny(p, interp) for p in map(P2.parse_acc, rec.get("acceptanceDateTime") or []) if p]
    return min(ts) if ts else None


def needed_pages(sub, lo: dt.date, hi: dt.date) -> list:
    """أسماءُ صفحات `files[]` التي يتقاطع مداها مع ‏[lo ‏−7 ، hi ‏+7] — اختيارٌ للتغطية لا قرار."""
    files = ((sub or {}).get("filings") or {}).get("files") or []
    a = (lo - dt.timedelta(days=PAGE_MARGIN_DAYS)).isoformat()
    b = (hi + dt.timedelta(days=PAGE_MARGIN_DAYS)).isoformat()
    return [f.get("name") for f in files if f.get("name")
            and str(f.get("filingFrom") or "") <= b and str(f.get("filingTo") or "9999") >= a]


def covered(sub, ok_pages, start, end, interp: str = TZ_WINNER) -> bool:
    """§⑤-4: (أ) `files[]` فارغة · (ب) أقدمُ قبولٍ في `recent` ‏≤ البداية · (ج) كلُّ صفحةٍ لازمةٍ جُلبت."""
    files = ((sub or {}).get("filings") or {}).get("files") or []
    if not files:
        return True
    old = recent_oldest_ny(sub, interp)
    if old is not None and old <= start:
        return True
    return all(n in ok_pages for n in needed_pages(sub, start.date(), end.date()))


def in_window(t, start, end) -> bool:
    return start <= t <= end


def row_hit(filings, start, end, forms=None) -> tuple:
    """(إصابة؟، الشاهد) — أوّلُ إيداعٍ داخل النافذة (من أسرةٍ بعينها إن طُلبت)."""
    for f, t in sorted(filings, key=lambda x: x[1]):
        if (forms is None or f in forms) and in_window(t, start, end):
            return True, (f, t)
    return False, None


# ---- الجلب (§⑤-2) ----
def fetch_json(url, get, sleep, st) -> object:
    """سياسةُ §⑤-2: كبحٌ 0.15ث بين كلّ نداءين · شبكة/5xx ⇒ حتى 3 محاولات (2ث ثم 4ث) · أوّلُ حجبٍ في
    التشغيلة كلِّها ⇒ توقّفٌ 60ث ومحاولةٌ واحدة، **وأيُّ حجبٍ بعده ⇒ `st["aborted"]`** · وما سوى ذلك
    (‏404 · جسمٌ غيرُ صالح) ⇒ `None` = «مجهول»."""
    tries = 0
    while True:
        if st["prev"]:
            sleep(P2.SHIPPED_SLEEP)
        st["prev"] = True
        st["calls"] += 1
        code, body, _ = get(url)
        if code == 200 and body is not None:
            return body
        if code in (403, 429):
            st["blocks"] += 1
            if st["paused"]:
                st["aborted"] = True
                return None
            st["paused"] = True
            sleep(BLOCK_PAUSE)
            continue
        if code == -1 or (isinstance(code, int) and code >= 500):
            if tries < len(RETRY_SLEEPS):
                sleep(RETRY_SLEEPS[tries])
                tries += 1
                continue
        st["failed"] += 1
        return None


# ---- الإحصاء ----
def side_rate(hits) -> tuple:
    k, n = int(sum(hits)), len(hits)
    lo, hi = PR.wilson(k, n)
    return k, n, (100.0 * k / n if n else 0.0), lo, hi


def cluster_boot(case_rows, ctrl_rows, b: int = BOOT_B, seed: int = BOOT_SEED) -> float:
    """§⑤-6: رموزُ كلّ طرفٍ تُسحَب داخله بالإرجاع (بعدد رموزه الفريدة) وتدخل صفوفُ المسحوب بتكراره
    ⟵ `numpy.percentile(…, 2.5)` للفرق بالنقاط. `*_rows` = [(رمز، إصابة)] بترتيبٍ ثابت."""
    def clusters(rows):
        order, agg = [], {}
        for sym, h in rows:
            if sym not in agg:
                agg[sym] = [0, 0]
                order.append(sym)
            agg[sym][0] += int(bool(h))
            agg[sym][1] += 1
        return (np.array([agg[s][0] for s in order], dtype=np.int64),
                np.array([agg[s][1] for s in order], dtype=np.int64))
    ka, na = clusters(case_rows)
    kb, nb = clusters(ctrl_rows)
    rng = np.random.default_rng(seed)
    diffs = np.empty(b)
    for i in range(b):
        ia = rng.integers(0, len(ka), len(ka))
        ib = rng.integers(0, len(kb), len(kb))
        diffs[i] = 100.0 * (ka[ia].sum() / na[ia].sum() - kb[ib].sum() / nb[ib].sum())
    return float(np.percentile(diffs, BOOT_PCT))


def verdict(diff, lo_case, hi_ctrl, eg6_lo) -> tuple:
    """§① ‏+ §⑩: الحاكمُ أوّلًا ⟵ ساقط = «فشل» (0) · عابرٌ و`EG6` ساقط = «لا حكم» (6) · كلاهما = «نجاح» (0)."""
    gov = diff >= EG_DIFF_MIN and lo_case > hi_ctrl
    if not gov:
        return "فشل", 0, gov
    if not (eg6_lo > 0.0):
        return "لا حكم", 6, gov
    return "نجاح", 0, gov


def judge_line(v, eg1=None, eg2=None, diff=None, case=0, ctrl=0, tz="-", code=0, why="") -> str:
    def f(x):
        return "-" if x is None else f"{x:.2f}"
    extra = f" reason={why}" if why else ""
    return (f"JUDGE verdict={v} EG1={f(eg1)} EG2={f(eg2)} diff={f(diff)} case={case} ctrl={ctrl} "
            f"tz={tz} exit={code}{extra}")


# ---- التشغيل ----
def main(get=None, sleep=None, paths=None, cmap=None) -> int:
    """`get`/`sleep`/`paths`/`cmap` محقونةٌ للاختبار — والافتراضُ الإنتاج (نمطُ `stage0`)."""
    get = get or sec_get
    sleep = sleep or time.sleep
    t0 = time.monotonic()
    log("=" * 78)
    log("🔬📰② T-PRE-EDGAR-2 — الدراسة: إيداعُ SEC الليليّ قبل انفجار ‏+100% (2025 · البريماركت)")
    log("   العقد: edgar2_prereg.md (+ الملحق §⑩) · الحاكم: الفرق ‏≥15 نقطة ∧ فاصلا Wilson منفصلان")
    log("=" * 78)

    # V-E8
    if not (os.environ.get("SEC_CONTACT") or "").strip():
        log("⛔ V-E8: SEC_CONTACT غيرُ مضبوط ⇒ عطبُ إعداد (خروج 2).")
        log(judge_line("-", code=2, why="V-E8"))
        return 2

    # V-E0: المرحلة صفر كاملةً في التشغيلة نفسِها
    if paths is None:
        import glob
        paths = sorted(glob.glob("presession_rows_*.jsonl.gz")) + sorted(glob.glob("presession_rows_*.jsonl"))
    syms, _nf, _nr, _ny = load_year_symbols(YEAR, paths=paths)
    if not syms:
        log("⛔ صفرُ رمزٍ من 2025 — المُدخَلُ غائب (خروج 2).")
        log(judge_line("-", code=2, why="input"))
        return 2
    cmap = cmap if cmap is not None else S.sec_cik_map()
    if not cmap:
        log("⛔ خريطةُ SEC فارغة — تعذّر الجلب (خروج 5).")
        log(judge_line("-", code=5, why="cmap"))
        return 5
    log("── V-E0: المرحلةُ صفر (العيّنةُ نفسُها) ──")
    s0 = P2.stage0(syms, cmap, get=get, sleep=sleep)
    if s0["exit"] != 0 or s0.get("winner") != TZ_WINNER:
        log(f"⛔ V-E0 سقطت (بوّابة {s0.get('gate')} · فائز {s0.get('winner')}) ⇒ خروج 5.")
        log(judge_line("-", code=5, why=f"V-E0:{s0.get('gate') or s0.get('winner')}"))
        return 5
    log(f"✅ V-E0 عبرت · التوقيت {s0['winner']}")

    # اللوحة
    per_day, cnt = load_pm_rows(paths)
    log(f"📦 صفوفُ PM 2025 غيرُ الشاهد: {cnt['pm']:,} في {len(per_day)} يومًا · الشاهد {cnt['wit']:,} · "
        f"جلسةٌ أخرى {cnt['other_sess']:,} · maxs معدومة {cnt['maxs_none']:,}")
    case, ctrl, short = build_panel(per_day)
    case2, ctrl2, _ = build_panel(per_day)
    lo1, hi1 = PUBLISHED_CASE * (1 - V_E1_TOL), PUBLISHED_CASE * (1 + V_E1_TOL)
    log(f"🧪 CASE {len(case)} (المنشور {PUBLISHED_CASE} · المسموح [{lo1:.0f} ، {hi1:.0f}]) · "
        f"CTRL {len(ctrl)} · عجزُ الشاهد {short}")
    if not (lo1 <= len(case) <= hi1):
        log("⛔ V-E1 سقطت ⇒ عطبُ أداةٍ لا نتيجة (خروج 3).")
        log(judge_line("-", code=3, why="V-E1"))
        return 3
    if set(case) & set(ctrl):
        log("⛔ V-E2 سقطت: صفٌّ في الطرفين (خروج 3).")
        log(judge_line("-", code=3, why="V-E2"))
        return 3
    if len(set(case)) != len(case) or len(set(ctrl)) != len(ctrl):
        log("⛔ V-E14 سقطت: تكرارُ (يوم، رمز) داخل طرف (خروج 3).")
        log(judge_line("-", code=3, why="V-E14"))
        return 3
    dg1, dg2 = panel_digest(case, ctrl), panel_digest(case2, ctrl2)
    if dg1 != dg2:
        log("⛔ V-E4 سقطت: اللوحةُ غيرُ حتميّة (خروج 3).")
        log(judge_line("-", code=3, why="V-E4"))
        return 3
    log(f"✅ V-E1 · V-E2 · V-E14 · V-E4 عبرت · بصمةُ اللوحة {dg1[:16]}")

    # القصّ (EG3-EG5)
    case_k = [r for r in case if r[1] in cmap]
    ctrl_k = [r for r in ctrl if r[1] in cmap]
    cut_a = 100.0 * (len(case) - len(case_k)) / len(case) if case else 0.0
    cut_b = 100.0 * (len(ctrl) - len(ctrl_k)) / len(ctrl) if ctrl else 0.0
    log(f"✂️ قصُّ CIK: CASE {len(case) - len(case_k)} ({cut_a:.1f}%) ⟵ {len(case_k)} · "
        f"CTRL {len(ctrl) - len(ctrl_k)} ({cut_b:.1f}%) ⟵ {len(ctrl_k)} · الفرقُ {cut_a - cut_b:+.1f} نقطة")
    floors = {"EG3": len(case_k) >= EG3_MIN, "EG4": len(ctrl_k) >= EG4_MIN,
              "EG5": cut_a <= EG5_MAX and cut_b <= EG5_MAX}
    if not all(floors.values()):
        bad = [k for k, v in floors.items() if not v]
        log(f"⚖️ «لا حكم» — أرضيّةٌ ساقطة {bad} (خروج 6) — تُنشَر باسمها ولا يُبنى عليها قرار.")
        log(judge_line("لا حكم", case=len(case_k), ctrl=len(ctrl_k), tz=TZ_WINNER, code=6,
                       why="+".join(bad)))
        return 6

    # الجلب (V-E10)
    rows = [("CASE", d, s) for d, s in case_k] + [("CTRL", d, s) for d, s in ctrl_k]
    by_cik = {}
    for side, d, s in rows:
        by_cik.setdefault(int(cmap[s]), []).append((side, d, s))
    st = {"prev": True, "calls": 0, "blocks": 0, "paused": False, "aborted": False, "failed": 0}
    subs, pages_ok, recs_all = {}, {}, []
    n_pages = 0
    log(f"🌐 الجلب: {len(by_cik)} CIK فريدًا · كبحٌ {P2.SHIPPED_SLEEP}ث · …")
    for cik in sorted(by_cik):
        sub = fetch_json(SUB_URL.format(cik), get, sleep, st)
        if st["aborted"]:
            log(f"⛔ V-E10: حجبٌ بعد التوقّف المُسجَّل ({st['blocks']}) ⇒ خروج 5 بلا حكمٍ جزئيّ.")
            log(judge_line("-", code=5, why="V-E10"))
            return 5
        subs[cik] = sub
        pages_ok[cik] = {}
        if not sub:
            continue
        recs_all.append(((sub.get("filings") or {}).get("recent") or {}))
        wins = [window_ny(d) for _side, d, _s in by_cik[cik]]
        a = min(w[0] for w in wins)
        old = recent_oldest_ny(sub)
        if ((sub.get("filings") or {}).get("files") or []) and (old is None or old > a):
            for name in needed_pages(sub, a.date(), max(w[1] for w in wins).date()):
                body = fetch_json(FILES_URL.format(name), get, sleep, st)
                if st["aborted"]:
                    log("⛔ V-E10: حجبٌ بعد التوقّف المُسجَّل ⇒ خروج 5 بلا حكمٍ جزئيّ.")
                    log(judge_line("-", code=5, why="V-E10"))
                    return 5
                n_pages += 1
                rec = page_rec(body)
                if rec is not None:
                    pages_ok[cik][name] = rec
                    recs_all.append(rec)
    log(f"   📨 نداءات {st['calls']} · حجبٌ {st['blocks']} · فشلٌ نهائيّ {st['failed']} · صفحات {n_pages}")

    # V-E9: التوقيتُ على مجتمع الدراسة
    tz = P2.tz_verdict(recs_all)
    P2.say_tz(tz)
    if not tz["ok"] or tz["winner"] != TZ_WINNER:
        log(f"⛔ V-E9 سقطت ({tz.get('reason') or tz.get('winner')}) ⇒ خروج 5.")
        log(judge_line("-", code=5, why="V-E9"))
        return 5

    # التغطية والإصابات (V-E11 · V-E13)
    res = {"CASE": [], "CTRL": []}
    fam = {k: {"CASE": [], "CTRL": []} for k in FAMILIES}
    unknown = {"CASE": 0, "CTRL": 0}
    wit = {"CASE": [], "CTRL": []}
    for cik in sorted(by_cik):
        sub = subs.get(cik)
        filings, _bad = cik_filings(sub, list(pages_ok[cik].values())) if sub else ([], 0)
        for side, d, s in by_cik[cik]:
            start, end = window_ny(d)
            if not sub or not covered(sub, pages_ok[cik], start, end):
                unknown[side] += 1
                continue
            hit, w = row_hit(filings, start, end)
            res[side].append((s, d, hit))
            if hit:
                wit[side].append((s, d, w[0], w[1]))
            for k, forms in FAMILIES.items():
                fam[k][side].append(row_hit(filings, start, end, forms)[0])
    for side, n0 in (("CASE", len(case_k)), ("CTRL", len(ctrl_k))):
        pct = 100.0 * unknown[side] / n0 if n0 else 0.0
        log(f"🔎 {side}: مجهولُ التغطية {unknown[side]} ({pct:.2f}% · الحدّ {UNKNOWN_MAX_PCT:.0f}%)")
        if pct > UNKNOWN_MAX_PCT:
            log("⛔ V-E11 سقطت ⇒ خروج 5.")
            log(judge_line("-", code=5, why="V-E11"))
            return 5
    for side in ("CASE", "CTRL"):
        for s, d, f, t in wit[side]:
            a, b = window_ny(d)
            if not (a.timestamp() <= t.timestamp() <= b.timestamp()):
                log(f"⛔ V-E13 سقطت: شاهدٌ خارج نافذته {s} {d} {f} {t.isoformat()} (خروج 3).")
                log(judge_line("-", code=3, why="V-E13"))
                return 3

    # الحاكم
    a_hits = [h for _s, _d, h in res["CASE"]]
    b_hits = [h for _s, _d, h in res["CTRL"]]
    ka, na, eg1, lo_a, hi_a = side_rate(a_hits)
    kb, nb, eg2, lo_b, hi_b = side_rate(b_hits)
    if ka == 0 and kb == 0:
        log("⛔ V-E5: صفرُ إصابةٍ في الطرفين معًا ⇒ أنبوبةٌ صامتة (خروج 4).")
        log(judge_line("-", code=4, why="V-E5"))
        return 4
    diff = eg1 - eg2
    eg6 = cluster_boot([(s, h) for s, _d, h in res["CASE"]], [(s, h) for s, _d, h in res["CTRL"]])
    label, code, gov = verdict(diff, lo_a, hi_b, eg6)

    log("=" * 78)
    log(f"📊 EG1 (CASE) {ka}/{na} = {eg1:.2f}% · Wilson [{lo_a:.2f} ، {hi_a:.2f}]")
    log(f"📊 EG2 (CTRL) {kb}/{nb} = {eg2:.2f}% · Wilson [{lo_b:.2f} ، {hi_b:.2f}]")
    log(f"⚖️ الفرق {diff:+.2f} نقطة (الحدّ {EG_DIFF_MIN:.0f}) · الفاصلان منفصلان: {lo_a > hi_b} · "
        f"الحاكم {'✅' if gov else '⛔'}")
    log(f"🧩 EG6 (عنقوديّةٌ بالرمز · B={BOOT_B} · بذرة {BOOT_SEED}): المئينُ {BOOT_PCT} = {eg6:+.2f} نقطة"
        + ("" if gov else " — وصفيٌّ (الحاكمُ ساقط · §⑩)"))
    log("── وصفيٌّ لا يحكم (§⑤-8) ──")
    fd = {}
    for k in FAMILIES:
        _k1, _n1, e1, _, _ = side_rate(fam[k]["CASE"])
        _k2, _n2, e2, _, _ = side_rate(fam[k]["CTRL"])
        fd[k] = e1 - e2
        log(f"   {k}: CASE {e1:.2f}% · CTRL {e2:.2f}% · الفرق {e1 - e2:+.2f}")
    early = {sd: sum(1 for _s, d, _h in res[sd] if prev_trading_day(d).isoformat() in MC.EARLY_CLOSES)
             for sd in res}
    gf = {sd: sum(1 for _s, d, _h in res[sd] if d == "2025-04-21") for sd in res}
    log(f"   صفوفٌ يومُ تداولها السابق إغلاقٌ مبكّر: CASE {early['CASE']} · CTRL {early['CTRL']} · "
        f"صفوفُ 2025-04-21 (الجمعةُ العظيمة في النافذة): CASE {gf['CASE']} · CTRL {gf['CTRL']}")
    log(f"   عجزُ الشاهد {short} · maxs معدومة {cnt['maxs_none']} · بصمةُ اللوحة {dg1[:16]}")
    for side in ("CASE", "CTRL"):
        for s, d, f, t in sorted(wit[side], key=lambda x: (x[1], x[0]))[:12 if side == "CASE" else 6]:
            log(f"   مثالُ إصابة {side}: {s} يوم {d} · {f} قُبل {t.strftime('%Y-%m-%d %H:%M:%S')} نيويورك")
    log("── بطاقةُ التنبّؤ (§⑥) ──")
    log(f"   ED2-P1 F4′ تعبر: {'✅' if s0.get('blocks') == 0 else '❌'} · "
        f"ED2-P2 F2 100%: {'✅' if s0.get('F2', 0) >= 100.0 else '❌'} · "
        f"ED2-P3 F3 ‏≥90%: {'✅' if s0.get('F3', 0) >= 90.0 else '❌'} · "
        f"ED2-P4 الفائز A: {'✅' if s0.get('winner') == 'A' else '❌'} ({s0.get('winner')})")
    log(f"   ED2-P5 الفرق في [+3 ، +12]: {'✅' if 3.0 <= diff <= 12.0 else '❌'} ({diff:+.2f})")
    log(f"   ED2-P6 EG2 ‏≥ 8%: {'✅' if eg2 >= 8.0 else '❌'} ({eg2:.2f}%)")
    log(f"   ED2-P7 F-424 أقوى من F-8K: {'✅' if fd['F-424'] > fd['F-8K'] else '❌'} "
        f"({fd['F-424']:+.2f} مقابل {fd['F-8K']:+.2f})")
    log(f"   ED2-P8 قصُّ CASE أكبر: {'✅' if cut_a > cut_b else '❌'} ({cut_a:.1f}% مقابل {cut_b:.1f}%)")
    log(f"⏱️ {time.monotonic() - t0:.0f}ث")
    log("=" * 78)
    log(judge_line(label, eg1, eg2, diff, na, nb, TZ_WINNER, code))
    return code


if __name__ == "__main__":
    sys.exit(main())
