# -*- coding: utf-8 -*-
"""⏰🪟 `T-SESSIONS` — **ساعةُ القمّة داخلَ الجلسة** (العقد `sessions_prereg.md`
‏+ الملحق المؤرَّخ `§⑩`).

**قراءةٌ/بحثٌ فقط · صفرُ مسٍّ بالإنتاج · صفرُ نداءٍ للمزوّد · لا
`LOGIC_VERSION` · ولا يُشحَن شيءٌ مهما كانت النتيجة.**

🔴 **والفرعُ 1 «ظاهرةٌ مقيسة» مُغلَقٌ بالبناء** — قياسُ الجدوى في `§①` أثبت أن
التقاطعَ المتاح **‏71 صفًّا** والأرضيّةَ المُلزِمة **‏150** ⇒ هذي **ذراعٌ
وصفيّةٌ لا تحكم**، تُنشَر أرقامُها ومعها ضبطاها **والقرارُ للمالك**.

🔗 **وكلُّ مستورَدٍ يُنادى بالاسم — صفرُ منطقِ حسمٍ مكرَّر:**
`tierlink_probe.anchor_history` (‏**الآلةُ التي بَنت `opcurve_rows.tsv` نفسَه**
— الملحق `§⑩`) · `liq_trig_read.git_snapshots`/`collect` (‏شاهدُ هُويّةٍ
وصفيٌّ `V-S8`) · `market_calendar.session_info` (‏`V-S4`) ·
`kasih_scan.wilson` (‏`SS1`) · `tc_yield_arms.production_untouched` (‏`V-S7`).
"""
from __future__ import annotations

import ast
import csv
import datetime as dt
import os
import random
import subprocess
import sys
from collections import Counter
from zoneinfo import ZoneInfo

import liq_trig_read as LTR
import tierlink_probe as TLP
from kasih_scan import wilson
from market_calendar import session_info
from tc_yield_arms import production_untouched

# ───────────────────────── الثوابتُ المُغلَقة بالعقد ──────────────────────────
ROWS_TSV = "opcurve_rows.tsv"
POP_TOTAL, POP_REG = 481, 228          # `V-S1` — بت-بت (العقد §①)
NY = ZoneInfo("America/New_York")
OPEN_H, CLOSE_H = 9.5, 16.0            # الجلسةُ النظاميّة — ‏6.5 ساعات
BUCKETS = (("09:30-12", 9.5, 12.0),    # §②-2 — أربعةٌ ولا خامس
           ("12-13", 12.0, 13.0),
           ("13-14", 13.0, 14.0),
           ("14-16", 14.0, 16.0))
GOV_BUCKET = "12-13"                   # دلو الحزمة (‏§⓪)
HOLD_CUT_ET = 14.0                     # §②-3 — «لم تكسر قاعَها حتى 14:00 ET»
JUMP_PCT = 10.0                        # §②-3 — «ثمّ بلغت +10%» (‏`t_hit10`)
SHUF_N, SHUF_SEED = 999, 20260920      # `C-SHUF` — حتميٌّ وبذرتُه تُطبَع
RATIO_MIN = 1.5                        # `SS1` — يُطبَع سواءٌ عبر أم لا
MIN_JOIN = 50                          # §⑤-3 — دونها الفرعُ 3
MIN_COVER = 0.90                       # `V-S2`
FLOOR_PROVE = 150                      # §①/§⑤-1 — **الفرعُ 1 مُغلَقٌ بالبناء**
OUT_ROWS = "sessions_rows.tsv"

RC_OK, RC_TOOL, RC_POP, RC_GUARD, RC_NOJUDGE = 0, 3, 4, 5, 9


def log(m: str) -> None:
    print(m, flush=True)


# ───────────────────────── حرّاسٌ (‏§⑥) ───────────────────────────────────────
def selfcheck_readonly(src: str | None = None) -> bool:
    """`V-S6` — **قراءةٌ فقط**: صفرُ إرسالٍ وصفرُ كتابةِ حالة.

    🔒 **ومُشدَّدٌ بدرسِ `T-PMFWD`:** ما لا يُثبَت أنه قراءةٌ **يُعَدّ كتابة**
    (وضعٌ مُمرَّرٌ متغيّرًا يُرفَض) · والوضعُ الغائبُ قراءةٌ يقينًا ·
    والكتابةُ لا تمرّ إلّا إلى `OUT_ROWS` — **مُخرَجُ قياسٍ لا حالةَ إنتاج**."""
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
        fn = n.func
        name = getattr(fn, "id", None) or getattr(fn, "attr", None) or ""
        if name in ("send_telegram", "send_telegram_document", "git_save",
                    "save_watchlist", "save_op_entry_state", "record_new_alerts"):
            return False
        if name == "open":
            mode = None
            if len(n.args) > 1:
                mode = n.args[1]
            for kw in n.keywords or []:
                if kw.arg == "mode":
                    mode = kw.value
            if mode is None:
                continue                          # وضعٌ غائب = `"r"` يقينًا
            if not (isinstance(mode, ast.Constant) and isinstance(mode.value, str)):
                return False                      # غيرُ ثابتٍ ⇒ يُعَدّ كتابة
            if set(mode.value) <= set("rbt"):
                continue
            tgt = n.args[0] if n.args else None
            if not (isinstance(tgt, ast.Name) and tgt.id in WRITE_OK):
                return False
    return True


# 🐞 **أسماءُ المزوّد مُركَّبةٌ لا مكتوبة** — الحارسُ يقارن بثوابتَ نصّيّة،
#    **والثابتُ نفسُه عقدةُ `Constant` في شجرة هذا الملفّ** فيسقط على نفسه.
#    وهو الصنفُ الذي أسقط `WLK5`/`WRK5` و`RKA`-`REOPEN` — تشديدٌ لا إرخاء.
_NET_BANNED = ("requ" + "ests", "poly" + "gon_flow", "poly" + "gon_minute_bars",
               "poly" + "gon_base_trades", "down" + "load_history", "url" + "open")


def no_provider_calls(src: str | None = None) -> bool:
    """`V-S7`-ب — **صفرُ نداءٍ للمزوّد بالـAST**: لا استيرادَ شبكةٍ ولا نداءَ
    جلبٍ في هذا الملفّ (‏الاسمُ مُركَّبٌ فلا يسقط الحارسُ على نفسه)."""
    if src is None:
        src = open(os.path.abspath(__file__), encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    banned = set(_NET_BANNED)
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            if any((a.name or "").split(".")[0] in banned for a in n.names):
                return False
        elif isinstance(n, ast.ImportFrom):
            if (n.module or "").split(".")[0] in banned:
                return False
            if any((a.name or "") in banned for a in n.names):
                return False
        elif isinstance(n, ast.Call):
            nm = getattr(n.func, "id", None) or getattr(n.func, "attr", None) or ""
            if nm in banned:
                return False
    return True


# ───────────────────────── الدوالُّ النقيّة (‏§②) ─────────────────────────────
def ny_hour(ms: int) -> float:
    """ساعةُ نيويورك (عشريّة) للحظةِ epoch بالملّي — **صيفيٌّ/شتويٌّ صحيحٌ من
    `zoneinfo` لا إزاحةٌ ثابتة** (‏`V-S4`). نقيّة."""
    d = dt.datetime.fromtimestamp(int(ms) / 1000.0, tz=dt.timezone.utc).astimezone(NY)
    return d.hour + d.minute / 60.0 + d.second / 3600.0


def ny_tzname(ms: int) -> str:
    """`EDT` أو `EST` للحظة — يُطبَع عددُ الصفوف في كلٍّ (‏`V-S4`)."""
    d = dt.datetime.fromtimestamp(int(ms) / 1000.0, tz=dt.timezone.utc).astimezone(NY)
    return d.tzname() or "?"


def bucket_of(h: float) -> str | None:
    """الدلوُ الذي تقع فيه ساعةُ نيويورك — `None` خارج الجلسة النظاميّة. نقيّة."""
    for lab, lo, hi in BUCKETS:
        if lo <= h < hi:
            return lab
    return None


def time_share(lo: float, hi: float,
               open_h: float = OPEN_H, close_h: float = CLOSE_H) -> float:
    """`C-TIME` — الحصّةُ **الزمنيّة** للدلو من الجلسة، **تُحسَب لا تُكتَب
    بيدٍ** (‏`V-S3`). نقيّة."""
    span = close_h - open_h
    if span <= 0:
        return 0.0
    return max(0.0, min(hi, close_h) - max(lo, open_h)) / span * 100.0


def held_and_jumped(anchor_h: float, t_stop, t_hit10,
                    cut: float = HOLD_CUT_ET) -> bool:
    """`§②`-3 — **لم تكسر قاعَها حتى ‏14:00 ET ثمّ بلغت ‏+10% بعده.**

    المكوّنان من `t_stop` و`t_hit10` الموجودَين في الملفّ — **بلا أيّ حسابٍ
    جديد**. `t_stop = None` = لم تُكسَر قطّ داخل النافذة. نقيّة."""
    if t_hit10 is None:
        return False
    if t_stop is not None and anchor_h + t_stop / 60.0 < cut:
        return False
    return anchor_h + t_hit10 / 60.0 >= cut


def hj_eligible(anchor_h: float, win_min: float, cut: float = HOLD_CUT_ET) -> bool:
    """**وصفيّةٌ فقط:** هل يقع `anchor_h + win_min` عند ‏14:00 ET أو بعدها؟

    🔴🔴 **تصحيحٌ مؤرَّخ 2026-09-20 — وكان استعمالي لها خاطئًا:** استعملتُها
    **مقامًا** لـ`SS3` بدعوى أن الصفَّ الذي تنتهي نافذتُه (‏120 دقيقة) قبل
    ‏14:00 **لا يستطيع** استيفاءَ الشرط. **والفحصُ على الصفوف كذّب الدعوى:**
    `t_hit10` في `opcurve_rows.tsv` **ليس مقصورًا على ‏120 دقيقة** — أقصاه
    المرصود **‏593 دقيقة** — فصفّان (‏`KWM` و`VEEA`) استوفيا الشرطَ وهما
    «غيرُ قادرَين» بتعريفي. ⇒ **المقامُ هو كلُّ `reg` المقاسة بنصّ `§④`**،
    وهذي تبقى **سطرَ تفكيكٍ وصفيٍّ لا مقامًا**. نقيّة."""
    return anchor_h + win_min / 60.0 >= cut


def shares_of(hours) -> dict:
    """حصّةُ كلّ دلوٍ من قائمةِ ساعاتِ قممٍ (‏بالنسبة المئويّة) ومعها العدد. نقيّة."""
    c = Counter(b for b in (bucket_of(h) for h in hours) if b)
    n = sum(c.values())
    return {lab: (c.get(lab, 0), (c.get(lab, 0) / n * 100.0) if n else 0.0)
            for lab, _lo, _hi in BUCKETS}


def shuffle_shares(anchor_hours, peak_mins, seed: int = SHUF_SEED,
                   reps: int = SHUF_N) -> list:
    """`C-SHUF` — **ضبطٌ حاكم**: تُخلَط **ساعاتُ المراسي** عشوائيًّا حتميًّا
    وتُعاد إزاحاتُ القمم عليها ⇒ توزيعُ حصّةِ الدلو الحاكم بالصدفة.

    🔑 **وهو الجوابُ عن «هل يتقدّم دلوٌ آليًّا لأن المراسي نفسَها مُكتَلة؟»**
    — درسُ `T-PMGATE` بحرفه. نقيّة وحتميّة (‏البذرةُ تُطبَع)."""
    rng = random.Random(seed)
    base = list(anchor_hours)
    out = []
    for _ in range(int(reps)):
        perm = base[:]
        rng.shuffle(perm)
        hs = [a + m / 60.0 for a, m in zip(perm, peak_mins)]
        out.append(shares_of(hs)[GOV_BUCKET][1])
    return out


def pctile_of(val: float, dist) -> float:
    """الشريحةُ المئويّة لقيمةٍ داخل توزيعٍ (‏`SS2`). نقيّة."""
    d = sorted(dist)
    if not d:
        return 0.0
    return sum(1 for x in d if x <= val) / len(d) * 100.0


def read_verdict(n_join: int, cover: float, share: float, tshare: float,
                 pct: float, guards_ok: bool) -> dict:
    """فروعُ `§⑤` بحرفها — **والفرعُ 1 مُغلَقٌ بالبناء فلا يُرجَع أبدًا**.

    🔒 نقيّةٌ ومقفولةٌ بجدول حقيقة: أيُّ تبديلٍ لشرطٍ يُسقط قفلَه المسمّى."""
    if (not guards_ok) or n_join < MIN_JOIN or cover < MIN_COVER:
        return {"branch": 3, "rc": RC_NOJUDGE,
                "text": f"الفرعُ 3 «لا قياس» — ضُمّ {n_join} صفًّا "
                        f"(الحدّ {MIN_JOIN}) · التغطيةُ {cover * 100:.1f}% "
                        f"(الحدّ {MIN_COVER * 100:.0f}%)"
                        f"{' · وحارسٌ ساقط' if not guards_ok else ''}"}
    if share < tshare or pct < 50.0:
        return {"branch": 2, "rc": RC_OK,
                "text": f"الفرعُ 2 «لا ظاهرة» — حصّةُ {GOV_BUCKET} {share:.2f}% "
                        f"مقابل حصّتِه الزمنيّة {tshare:.2f}% · وشريحتُه من "
                        f"`C-SHUF` {pct:.1f} ⇒ **إشارةٌ سالبةٌ تُنشَر ولا "
                        f"تُقترَح الذراعُ الحاكمة**"}
    return {"branch": 0, "rc": RC_OK,
            "text": f"**الفرعُ 1 مُغلَقٌ بالبناء** (‏{n_join} دون {FLOOR_PROVE}) — "
                    f"والإشارةُ موجبةٌ وصفيًّا: {GOV_BUCKET} {share:.2f}% مقابل "
                    f"{tshare:.2f}% زمنيًّا وشريحةُ `C-SHUF` {pct:.1f} ⇒ **لا "
                    f"يُدَّعى إثباتٌ، والقرارُ للمالك: أتُشغَّل الحاكمةُ أم "
                    f"يُغلَق المحور؟**"}


# ───────────────────────── المجتمعُ والضمّ (‏§① · §⑩) ────────────────────────
def repo_depth() -> tuple:
    """`V-S9` (‏الملحق `§⑪`) — **هل النسخةُ ضحلة؟** ومعها عددُ مراجع
    `op_entry_state.json` وأقدمُ تاريخٍ فيها.

    🔴 **وُلد من قراءةٍ كاذبةٍ مُثبَتة:** `git log` على نسخةٍ `shallow` يُرجع
    تاريخًا **مبتورًا بلا أيّ خطأٍ ظاهر** ⇒ `anchor_history` لا ترى إلّا ما
    بعد قاع النسخة، فقُرئت التغطيةُ ‏32.9% وحقيقتُها ‏100%. **فاشلٌ-آمن:
    تعذّرُ الفحص يُعَدّ «ضحلة»** — لأن ما لا يُثبَت اكتمالُه لا يُقاس عليه."""
    def _run(*a):
        try:
            return subprocess.run(["git", *a], capture_output=True, text=True,
                                  timeout=60).stdout.strip()
        except Exception:                                        # noqa: BLE001
            return ""
    sh = _run("rev-parse", "--is-shallow-repository")
    revs = _run("log", "--format=%cI", "origin/main", "--", LTR.STATE).splitlines()
    return (sh != "false", len(revs), revs[-1][:10] if revs else "?")


def load_rows(path: str = ROWS_TSV) -> list:
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def _f(v):
    v = (v or "").strip()
    try:
        return float(v)
    except ValueError:
        return None


def join_anchor_ms(rows: list, anchors: dict) -> tuple:
    """يضمّ `(يوم · رمز)` إلى `anchor_ms` من **`anchor_history`** — الآلةُ
    التي بَنت المجتمعَ نفسَه (‏الملحق `§⑩`) ⇒ **صفرُ قاعدةِ اختيارٍ تُخترَع**."""
    out, miss = [], []
    for r in rows:
        a = anchors.get((r["date"], r["sym"]))
        ams = a and a.get("anchor_ms")
        if not ams:
            miss.append(f"{r['date']}·{r['sym']}")
            continue
        out.append((r, int(ams)))
    return out, miss


def identity_witness(anchors: dict, since: str) -> dict:
    """`V-S8` (‏الملحق `§⑩`-ⓒ) — **وصفيٌّ لا يوقف**: يقارن `anchor_ms` من
    `anchor_history` بأقدمِ مِرساةٍ من `liq_trig_read.collect` لكلّ
    `(يوم · رمز)` ويطبع المتّفقَ والمختلف. الاختلافُ **معلومُ السبب**
    (‏إعادةُ المِرساة) فيُنشَر رقمًا بدل أن يُخمَّن."""
    try:
        snaps, bad = LTR.git_snapshots(ref=os.environ.get("TRIG_READ_REF",
                                                          "origin/main"))
        res = LTR.collect(snaps)
    except Exception as e:                                       # noqa: BLE001
        return {"err": f"{type(e).__name__}: {e}"}
    first = {}
    for (sym, day, ams) in res.get("anchors", {}):
        if day < since:
            continue
        k = (day, sym)
        if k not in first or ams < first[k]:
            first[k] = ams
    agree = [k for k in anchors if k in first
             and int(anchors[k]["anchor_ms"]) == first[k]]
    differ = [k for k in anchors if k in first
              and int(anchors[k]["anchor_ms"]) != first[k]]
    return {"n_hist": len(anchors), "n_collect": len(first), "bad_revs": bad,
            "agree": len(agree), "differ": len(differ),
            "first5": [f"{d}·{s}" for d, s in sorted(differ)[:5]]}


def main() -> int:                                    # noqa: PLR0911, PLR0912, PLR0915
    log("⏰🪟 `T-SESSIONS` — ساعةُ القمّة داخلَ الجلسة (‏قراءةٌ فقط · صفرُ جلب)")
    log(f"   العقد: sessions_prereg.md ‏+ الملحق §⑩ · البذرة {SHUF_SEED} · "
        f"سحبات {SHUF_N}")

    # ── حرّاسٌ قبل أيّ رقم ──────────────────────────────────────────────────
    ro = selfcheck_readonly()
    np_ok = no_provider_calls()
    prod_ok, cur, base = production_untouched()
    log(f"   🔒 V-S6 قراءةٌ فقط={ro} · V-S7-ب صفرُ مزوّد={np_ok} · "
        f"V-S7 الإنتاجُ بت-بت={prod_ok} ({cur} مقابل {base})")
    if not (ro and np_ok and prod_ok):
        log(f"⛔ حارسٌ ساقطٌ قبل أيّ قياس — خروج {RC_GUARD}")
        return RC_GUARD

    # ── `V-S3` حصصُ الدلاء الزمنيّة ────────────────────────────────────────
    tshare = {lab: time_share(lo, hi) for lab, lo, hi in BUCKETS}
    tot = sum(tshare.values())
    log("   🔒 V-S3 الحصصُ الزمنيّة: " +
        " · ".join(f"{k} {v:.2f}%" for k, v in tshare.items()) +
        f" · المجموع {tot:.2f}%")
    if abs(tot - 100.0) > 0.01:
        log(f"⛔ V-S3 — مجموعُ الحصص {tot:.4f}% ⇒ تعريفُ دلوٍ مكسور — "
            f"خروج {RC_GUARD}")
        return RC_GUARD

    # ── `V-S9` (‏الملحق `§⑪`) — **نسخةٌ ضحلةٌ ⇒ لا قياس** ───────────────────
    sh, nrev, oldest = repo_depth()
    log(f"   🔒 V-S9 عمقُ النسخة: ضحلةٌ={sh} · مراجعُ الحالة={nrev} · "
        f"أقدمُها={oldest}")
    if sh:
        log(f"⛔ V-S9 — `git log` على نسخةٍ **ضحلة** يُرجع تاريخًا مبتورًا بلا "
            f"خطأٍ ظاهر ⇒ القياسُ باطل. العلاج: `git fetch --unshallow` "
            f"محلّيًّا أو `fetch-depth: 0` في الـworkflow — خروج {RC_POP}")
        return RC_POP

    # ── `V-S1` المجتمعُ عينُ `opcurve_rows.tsv` ─────────────────────────────
    try:
        rows = load_rows()
    except OSError as e:
        log(f"⛔ تعذّر فتح {ROWS_TSV}: {e} — خروج {RC_TOOL}")
        return RC_TOOL
    reg = [r for r in rows if r.get("tod") == "reg"]
    log(f"   🔒 V-S1 المجتمع: {len(rows)} صفًّا (المنشور {POP_TOTAL}) · "
        f"reg {len(reg)} (المنشور {POP_REG}) · "
        f"pre {sum(1 for r in rows if r['tod'] == 'pre')} · "
        f"after {sum(1 for r in rows if r['tod'] == 'after')}")
    if len(rows) != POP_TOTAL or len(reg) != POP_REG:
        log(f"⛔ V-S1 — المجتمعُ ليس المنشور — خروج {RC_POP}")
        return RC_POP

    since = min(r["date"] for r in rows)
    anchors = TLP.anchor_history(since)
    joined, miss = join_anchor_ms(reg, anchors)
    cover = len(joined) / len(reg) if reg else 0.0
    log(f"   🔒 V-S2 الضمّ: {len(joined)} من {len(reg)} = {cover * 100:.1f}% "
        f"(الحدّ {MIN_COVER * 100:.0f}%) · بلا مِرساة {len(miss)} "
        f"· أوّلُ خمسة {miss[:5]}")

    wit = identity_witness(anchors, since)
    log(f"   ℹ️ V-S8 شاهدُ الهُويّة (وصفيٌّ لا يوقف): {wit}")

    # 🔴 **تشخيصٌ يُطبَع لا يحكم — أُضيف بعد أوّل تشغيلةٍ ويُعلَن أنه أُضيف:**
    #    «‏33% تغطية» رقمٌ أعمى ما لم يُعرَف **أيُّ** الصفوف نجت. وهذا يطبع
    #    مدى تواريخ المضموم مقابل مدى المجتمع ⇒ **يُقرأ انحيازُ الشريحة
    #    الزمنيّة بالأرقام**. ولا يمسّ عتبةً ولا معيارًا ولا فرعًا.
    if joined:
        _jd = sorted({r["date"] for r, _ in joined})
        _ad = sorted({r["date"] for r in reg})
        log(f"   🔎 مدى المضموم: {_jd[0]} ⟶ {_jd[-1]} ({len(_jd)} يومًا) · "
            f"ومدى `reg` كلِّه: {_ad[0]} ⟶ {_ad[-1]} ({len(_ad)} يومًا) ⇒ "
            f"**{len(_ad) - len(_jd)} يومًا بلا تمثيل**")

    # ── القياسُ (‏§②) ──────────────────────────────────────────────────────
    meas, tzc = [], Counter()
    for r, ams in joined:
        ah = ny_hour(ams)
        tzc[ny_tzname(ams)] += 1
        tp, th, ts = _f(r["t_peak"]), _f(r["t_hit10"]), _f(r["t_stop"])
        meas.append({"date": r["date"], "sym": r["sym"], "anchor_ms": ams,
                     "anchor_h": ah, "t_peak": tp, "t_hit10": th, "t_stop": ts,
                     "peak_h": (ah + tp / 60.0) if tp is not None else None})
    log(f"   🔒 V-S4-أ نظامُ التوقيت (‏`zoneinfo` IANA لا إزاحةٌ ثابتة): "
        f"{dict(tzc)}" +
        ("  ⚠️ **أحدُهما صفرٌ ⇒ الضبطُ منحلٌّ ويُقال**"
         if len(tzc) < 2 else ""))
    # 🔒 `V-S4`-ب — **نوعُ الجلسة من `market_calendar.session_info` بالاسم.**
    #    حدودُ الدلاء مثبَّتةٌ على جلسةٍ نظاميّة (‏9.5 ⟶ 16.0)، **ويومُ الإغلاق
    #    المبكّر يُغلق 13:00** فتصير الحصصُ الزمنيّةُ كاذبةً عليه ⇒ يُعَدّ
    #    ويُطبَع، وحضورُه يُسقط التشغيلةَ بدل أن يُلوّث الحصص بصمت.
    stc = Counter(session_info(m["date"])["session_type"] for m in meas)
    log(f"   🔒 V-S4-ب نوعُ الجلسة: {dict(stc)}")
    if set(stc) - {"regular"}:
        log(f"⛔ V-S4-ب — جلسةٌ غيرُ نظاميّةٍ بين الصفوف ⇒ حدودُ الدلاء "
            f"لا تنطبق — خروج {RC_GUARD}")
        return RC_GUARD

    peaks = [m for m in meas if m["peak_h"] is not None]
    in_sess = [m for m in peaks if bucket_of(m["peak_h"])]
    log(f"   📐 بـ`t_peak`: {len(peaks)} · وقمّتُه داخلَ الجلسة: {len(in_sess)} "
        f"(خارجَها {len(peaks) - len(in_sess)} — نافذةُ ‏120د قد تتجاوز الجرس)")

    obs = shares_of([m["peak_h"] for m in in_sess])
    log("   📊 `S-OBS` المرصود مقابل `C-TIME` الزمنيّ:")
    for lab, _lo, _hi in BUCKETS:
        k, pc = obs[lab]
        lo95, hi95 = wilson(k, len(in_sess))
        log(f"      {lab:>9} · {k:>3} من {len(in_sess)} = {pc:6.2f}% "
            f"[{lo95:.2f}, {hi95:.2f}] · زمنيًّا {tshare[lab]:6.2f}% · "
            f"نسبة {pc / tshare[lab] if tshare[lab] else 0:.2f}×")

    g_k, g_share = obs[GOV_BUCKET]
    dist = shuffle_shares([m["anchor_h"] for m in in_sess],
                          [m["t_peak"] for m in in_sess])
    pct = pctile_of(g_share, dist)
    d_s = sorted(dist)
    log(f"   🎲 `C-SHUF` ({SHUF_N} سحبة · بذرة {SHUF_SEED}): "
        f"وسيطٌ {d_s[len(d_s) // 2]:.2f}% · "
        f"p05 {d_s[int(0.05 * len(d_s))]:.2f}% · "
        f"p95 {d_s[int(0.95 * len(d_s))]:.2f}% ⇒ "
        f"شريحةُ المرصود **{pct:.1f}**")

    # ── `SS3` — «يدبل ‏80%» يُطبَع ليُكذَّب لا ليُحسَم به ───────────────────
    WIN = 120.0                                       # نافذةُ سياسة `T-OPCURVE`
    hj = [m for m in meas
          if held_and_jumped(m["anchor_h"], m["t_stop"], m["t_hit10"])]
    elig = [m for m in meas if hj_eligible(m["anchor_h"], WIN)]
    hj_in = [m for m in hj if hj_eligible(m["anchor_h"], WIN)]
    log(f"   🧪 `SS3` `held_and_jumped`: **{len(hj)} من {len(meas)}** = "
        f"{len(hj) / len(meas) * 100 if meas else 0:.2f}% "
        f"(المقامُ كلُّ `reg` المقاسة بنصّ `§④`)")
    log(f"      ℹ️ تفكيكٌ وصفيّ: {len(hj_in)} منها داخلَ نافذةِ {WIN:.0f}د "
        f"(‏{len(elig)} صفًّا) و{len(hj) - len(hj_in)} خارجَها — "
        f"**و`t_hit10` غيرُ مقصورٍ على النافذة** (أقصى المرصود يتجاوزها)")
    log(f"      🔴 وحدُّ صدقٍ باقٍ: «يدبل» = ‏+100% والمقيسُ هنا "
        f"‏+{JUMP_PCT:.0f}% ⇒ **مقياسٌ أضعفُ بعشرة أضعاف، ولا يُحسَم به**")

    # ── المُخرَجُ والحكم ────────────────────────────────────────────────────
    if os.environ.get("SESSIONS_TSV", "1") == "1":
        with open(OUT_ROWS, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, delimiter="\t")
            w.writerow(["date", "sym", "anchor_ms", "anchor_h", "t_peak",
                        "peak_h", "bucket", "t_hit10", "t_stop", "hj_elig", "hj"])
            for m in meas:
                w.writerow([m["date"], m["sym"], m["anchor_ms"],
                            f"{m['anchor_h']:.4f}",
                            "" if m["t_peak"] is None else f"{m['t_peak']:.1f}",
                            "" if m["peak_h"] is None else f"{m['peak_h']:.4f}",
                            bucket_of(m["peak_h"]) if m["peak_h"] is not None else "",
                            "" if m["t_hit10"] is None else f"{m['t_hit10']:.1f}",
                            "" if m["t_stop"] is None else f"{m['t_stop']:.1f}",
                            int(hj_eligible(m["anchor_h"], WIN)),
                            int(held_and_jumped(m["anchor_h"], m["t_stop"],
                                                m["t_hit10"]))])
        log(f"   🧾 الصفوف: {OUT_ROWS} ({len(meas)} صفًّا)")

    v = read_verdict(len(joined), cover, g_share, tshare[GOV_BUCKET], pct, True)
    log("")
    log(f"JUDGE {v['text']}")
    return v["rc"]


if __name__ == "__main__":
    raise SystemExit(main())
