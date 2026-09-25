#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🌅🗂️ `T-SHADOW` — القائمةُ الظلّيّة: مراسي «هنا الدخول» في البريماركت ∧ (J1 ∨ فجوة ‏≥30%) مقابل «الجاهز».

**الحزمة:** `OPUS_READY_LIST_SPEC.md` (R-01 · R-03) · **العقد:** `shadow_ready_prereg.md` (مدفوعٌ قبل أيّ رقم).

كلُّ مرساة `LIQ:*` من تاريخ git (`tierlink_probe.anchor_history` **بالاسم**) ⟵ ميزاتُها من
`tierlink_probe.features` ⟵ `S = tod=="pre" ∧ (J1 ∨ gap≥30%)` ⟵ عضويّةُ «الجاهز» يومَها من لقطة
`weekly_watchlist.json` ‏≤ اليوم (`opentry_link_probe.membership`/`snapshot_before` **بالاسم**) ⟵ النتيجةُ
`exploded50` من `tierlink_probe.measure` **بالاسم** لأيّامٍ مكتملة وحدَها.

**بُنيت لـ…** (قاعدةُ الحزمة): `anchor_history` بُنيت لقراءة المراسي من تاريخ git (`T-TIERLINK`) — مطابق ·
`features`/`measure` بُنيتا لميزات المرساة وأساسِ سعر كرت `M5` — مطابق · `membership`/`snapshot_before`
بُنيتا لعضويّة «الجاهز» يومَ المرساة بلا لقطةٍ لاحقة (`T-OPLINK`) — مطابق · `judge` بُنيت للمعيار الرباعيّ
على سلّتين (`T-OPLINK §⑤`) — مطابق مع شرط أن تكون الأعلى `S` · `ce_borrow_info` بُنيت لمتاح ChartExchange
اللحظيّ (`ctb_harvest`) — ولهذا **لا يُسجَّل إلّا في جلسة المرساة نفسِها** (العقد §⑤).

🔒 **قراءةٌ فقط** عدا سطرِ سجلّها (`append_ledger` وحدَها · بالـAST) · صفرُ تلغرام · صفرُ `git_save` ·
والإنتاجُ لا يستوردها. **والسجلُّ لا يحمل النتيجة** (مبدأُ `ctb_harvest`: تُشتقّ وقتَ التحليل).

**رموزُ الخروج:** 0 صدر · 2 لا مفتاح · 3 تغطيةٌ دون 80% · 4 صفرُ مرساة · 5 الحارسُ الذاتيّ.
و`--wait-capture` (خطوةُ المجدول وحدَه): تنام حتى 20:15 نيويورك إن أقلعت قبلها بما لا يزيد عن 200 دقيقة ثمّ 0.
"""
import ast
import collections
import datetime as dt
import json
import math
import os
import subprocess
import sys
import time

from tierlink_probe import anchor_history, features, measure, daily_range, _bucket   # بالاسم
from tier_fwd_report import fetch_day, load_ledger                                 # بالاسم
from kasih_scan import NY, wilson                                                  # بالاسم
from opentry_link_probe import _commits, snapshot_before, membership, judge        # بالاسم
import Super_stock as S                                                            # ce_borrow_info · CONFIG

LEDGER = os.environ.get("SHADOW_LEDGER", "shadow_ready_ledger.jsonl")
SINCE = os.environ.get("SHADOW_SINCE") or "2026-08-17"   # ⚠️ `or` لا افتراضُ get: المجدولُ يمرّر المُدخَلَ فارغًا
SHADOW_FWD_SINCE = "2026-09-26"      # العقد §② — اليومُ التالي لدفع العقد · لا يُحرَّك
FLOOR_S, FLOOR_ALL = 60, 150         # العقد §④-3 (مُعادان من T-J1PM §③)
FLOOR_AVAIL = 100                    # العقد §⑤ (رقمُ الحزمة R-03)
MIN_HALF = 10                        # العقد §④-4
MIN_COVER = 0.80                     # العقد §⑦ V-S1
STOP_DATE = "2026-12-31"             # العقد §④ (رقمُ T-PMFWD)
AVAIL_CAP = 40                       # العقد §⑤ — سقفُ نداءات المتاح للتشغيلة
CLOSE_HOUR_NY = 20                   # نهايةُ الافتر ⇒ اليومُ مكتمل (V-S4 · V-S5)
CAPTURE_AT_NY = (20, 15)             # engineering — المجدولُ ينتظر حتى 20:15 نيويورك: نهايةُ الافتر (20:00) ‏+ هامشُ
                                     #   آخرِ دفعٍ لـ`op_entry_state.json` (مقيس: ‏20:00:43 · 20:04:16 نيويورك)
CAPTURE_WAIT_MAX_S = 200 * 60        # engineering — أبعدُ منه ⇒ لا انتظار (إقلاعٌ بعد منتصف الليل أو صباحًا)
IDENTITY = ("2026-08-18", "2026-09-01", 33, 321, 14)   # V-S2 · T-TIERLINK بت-بت
LEDGER_FIELDS = ("schema", "date", "symbol", "sample", "anchor_ms", "tod", "j1", "gap", "gap_pct", "shadow",
                 "member", "ready", "in_tier_ledger", "avail", "avail_why", "avail_asof", "run_id", "recorded_at")
OUTCOME_FIELDS = ("exploded50", "exploded100", "mg_day", "mg_cut", "close_ret", "mg_5d", "e5")


def log(msg):
    print(msg, flush=True)


# ───────────────────────── الحارسُ الذاتيّ (العقد §⑦ V-S6) ─────────────────────────
def _selfcheck(src=None) -> bool:
    """قراءةٌ فقط عدا سطرِ السجلّ: صفرُ إرسالٍ/حفظِ حالة · `subprocess` لـ`git show`/`git log` وحدَهما ·
    وكلُّ `open` بوضعِ كتابةٍ داخل `append_ledger` وحدَها. بالـAST على المصدر (لا نصًّا)."""
    try:
        src = open(__file__, encoding="utf-8").read() if src is None else src
        tree = ast.parse(src)
    except Exception:                                                # noqa: BLE001
        return False
    banned = {"send_telegram", "git_save", "save_watchlist", "save_op_entry_state", "record_new_alerts",
              "save_near_watch", "save_hunter_watch", "record_tier_fwd", "record_ignition_fires", "_record",
              "system", "popen", "Popen", "check_output", "check_call", "call",
              "write_text", "write_bytes", "unlink", "remove", "rmtree", "rename"}
    for n in ast.walk(tree):
        # subprocess مسموحٌ **لـ`git show`/`git log` حرفيًّا** (قراءة لقطات) — وأيُّ نداءٍ آخرَ عبره يُسقط الحارس
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "run"
                and getattr(n.func.value, "id", None) == "subprocess"):
            a0 = n.args[0] if n.args else None
            elts = [getattr(e, "value", None) for e in getattr(a0, "elts", [])[:2]]
            if not (isinstance(a0, ast.List) and len(elts) == 2 and elts[0] == "git" and elts[1] in ("show", "log")):
                return False
    owner = {}
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for n in ast.walk(fn):
                owner.setdefault(id(n), fn.name)
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        name = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
        if name in banned:
            return False
        if name == "open":
            mode = ""
            if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                mode = str(n.args[1].value)
            for kw in n.keywords or []:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = str(kw.value.value)
            if any(c in mode for c in ("w", "a", "x", "+")) and owner.get(id(n)) != "append_ledger":
                return False
    return True


# ───────────────────────── دوالُّ نقيّة (العقد §③-§⑤) ─────────────────────────
def shadow_flag(f) -> bool:
    """`S = tod=="pre" ∧ (J1 ∨ gap≥30%)` — والمجهولُ «؟» ليس `S` (العقد §③)."""
    f = f or {}
    return f.get("tod") == "pre" and (f.get("j1") == "J1" or f.get("gap") == "≥30%")


def last_complete_day(now_ny) -> str:
    """آخرُ يومٍ مكتمل (V-S4): اليومُ نفسُه بعد 20:00 نيويورك (نهاية الافتر) وإلّا أمسُه."""
    d = now_ny.date() if now_ny.hour >= CLOSE_HOUR_NY else now_ny.date() - dt.timedelta(days=1)
    return d.isoformat()


def sample_of(day) -> str:
    return "fwd" if str(day) >= SHADOW_FWD_SINCE else "in"


def gap_pct_of(a, b, dailies, day):
    """فجوةُ المرساة عن إغلاق الأمس **بمصدر `features` نفسِه**: `prev_close` صفِّ السجلّ لمن فيه، ولمن ليس فيه
    آخرُ إغلاقٍ قبل اليوم من `daily_range` (إصلاحُ `tierlink_probe.main`) ⇒ الرقمُ والسلّةُ من مصدرٍ واحد."""
    ap = (a or {}).get("anchor_price") or (b or {}).get("anchor_price")
    if b is not None:
        pc = b.get("prev_close")
    else:
        pcs = [c for (d, _h, c) in (dailies or []) if d < day]
        pc = pcs[-1] if pcs else None
    return (ap / pc - 1) * 100 if ap and pc else None


def anchor_row(a, b, bars, dailies, day):
    """`(f, o, gap_pct)` لمرساةٍ واحدة — أو None بلا أساس. **الإصلاحُ نفسُه** لفجوة من ليس في السجلّ
    كما في `tierlink_probe.main`/`opentry_link_probe.main` (مقفولٌ بالهُويّة)."""
    o = measure(a, b, bars, dailies)
    if o is None:
        return None
    f = features(a, b)
    g = gap_pct_of(a, b, dailies, day)
    if b is None and g is not None:
        f["gap"] = _bucket(g, (10, 30), ("<10%", "10-30%", "≥30%"))
    return f, o, g


def avail_capture(sym, day, now_ny, fetch, budget):
    """R-03 (العقد §⑤ · V-S5): متاحُ ChartExchange **في جلسة المرساة نفسِها بعد 20:00 نيويورك** وحدَها.
    يُرجع `(avail|None, why, asof|None)` · والمتعذّرُ مجهولٌ لا صفر · والسقفُ مُعلَنٌ لا صامت."""
    if now_ny.date().isoformat() != str(day) or now_ny.hour < CLOSE_HOUR_NY:
        return None, "not_same_session", None
    if budget.get("left", 0) <= 0:
        return None, "cap", None
    budget["left"] = budget.get("left", 0) - 1
    try:
        d = fetch(sym) or {}
    except Exception:                                                # noqa: BLE001
        d = {}
    v = d.get("shares_available")
    if v is None:
        return None, "unavailable", None
    try:
        return int(v), "ok", now_ny.isoformat(timespec="minutes")
    except (TypeError, ValueError):
        return None, "unavailable", None


def capture_wait_s(now_ny, at=CAPTURE_AT_NY, cap_s=CAPTURE_WAIT_MAX_S) -> int:
    """ثوانٍ ينتظرها **المجدولُ وحدَه** ليقع في جلسة المرساة بعد نهاية الافتر (R-03 · V-S5) — نقيّة:
    صفرٌ عند `at` أو بعده · وصفرٌ إن زاد الانتظارُ عن `cap_s` (إقلاعٌ بعد منتصف الليل أو صباحًا ⇒ يُكمل فورًا
    والمتاحُ مجهولٌ بسببه `not_same_session`) · وإلّا ما بقي حتى `at` من اليوم نفسِه بتوقيت نيويورك."""
    need = (now_ny.replace(hour=at[0], minute=at[1], second=0, microsecond=0) - now_ny).total_seconds()
    return int(math.ceil(need)) if 0 < need <= cap_s else 0


def wait_for_capture(now=None, sleep=time.sleep) -> int:
    """نقطةُ `--wait-capture` (خطوةُ المجدول وحدَه قبل القياس): تنام `capture_wait_s` ثمّ تعود 0 · وتطبع قرارَها.
    لا تقرأ git ولا تنادي شبكة — والساعةُ والنومُ محقونان للاختبار."""
    now_ny = now() if now else dt.datetime.now(NY)
    w = capture_wait_s(now_ny)
    log(f"⏳ R-03: الآن {now_ny:%Y-%m-%d %H:%M} نيويورك ⟵ "
        + (f"انتظارُ {w // 60} دقيقة حتى {CAPTURE_AT_NY[0]:02d}:{CAPTURE_AT_NY[1]:02d}" if w else "بلا انتظار"))
    if w:
        sleep(w)
    return 0


def ledger_rows(rows, existing_keys):
    """الصفوفُ التي تُكتب: **أماميّةٌ وحدَها** (D-3) · مرّةً لكلّ (تاريخ، رمز) · **بلا حقلِ نتيجة** (D-2)."""
    out, seen = [], set(existing_keys or ())
    for r in rows:
        k = (r.get("date"), r.get("symbol"))
        if r.get("sample") != "fwd" or k in seen or not all(k):
            continue
        seen.add(k)
        out.append({f: r.get(f) for f in LEDGER_FIELDS})
    return out


def load_ledger_keys(path=None):
    keys = set()
    try:
        with open(path or LEDGER, encoding="utf-8") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                keys.add((r.get("date"), r.get("symbol")))
    except OSError:
        pass
    return keys


def append_ledger(rows, path=None) -> int:
    """**موضعُ الكتابة الوحيد** (V-S6): إلحاقُ أسطر JSONL بسجلّ الحصاد. فاشلٌ-آمن ⇒ عددُ المكتوب."""
    n = 0
    if not rows:
        return 0
    try:
        with open(path or LEDGER, "a", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
                n += 1
    except OSError:
        return n
    return n


def decision_window(rows, floor_s=FLOOR_S, floor_all=FLOOR_ALL, key=None):
    """نافذةُ الحكم (العقد §④): أوّلُ يومٍ `D*` تبلغ فيه الصفوفُ حتى `D*` الأرضيتين — `(D*, الصفوف)` أو `(None, [])`.
    `key(r)` ⟵ عضويّةُ السلّة الحاكمة (افتراضًا `S`)."""
    key = key or (lambda r: bool(r.get("shadow")))
    rs = sorted(rows, key=lambda r: r["date"])
    n_s = n_all = 0
    for i, r in enumerate(rs):
        n_all += 1
        n_s += 1 if key(r) else 0
        last_of_day = i + 1 == len(rs) or rs[i + 1]["date"] != r["date"]
        if last_of_day and n_s >= floor_s and n_all >= floor_all:
            return r["date"], rs[:i + 1]
    return None, []


def shadow_verdict(rows, label="exploded50"):
    """الحكمُ الرباعيّ على نافذة الحكم (العقد §④): `judge` بالاسم على سلّتين · **والأعلى يجب أن تكون `S`** ·
    والنصفان بـ‏≥`MIN_HALF` من كلّ سلّة. يُرجع قاموسًا فيه `branch` (1/2/None=لا حكم) و`why`."""
    d_star, win = decision_window(rows)
    if d_star is None:
        n_s = sum(1 for r in rows if r.get("shadow"))
        return {"branch": None, "why": f"لا حكم — الأرضيةُ لم تُبلَغ (S {n_s}/{FLOOR_S} · الكلّ {len(rows)}/{FLOOR_ALL})",
                "d_star": None}
    h2 = sorted(r["date"] for r in win)[len(win) // 2]
    wr = [{"date": r["date"], "f": {"S": "S" if r.get("shadow") else "S̄"}, "o": {label: bool(r.get(label))}}
          for r in win]
    _t, v = judge(wr, "S", h2)
    if str(v.get("why", "")).startswith("لا حكم"):
        return {"branch": None, "why": v["why"], "d_star": d_star}
    halves_ok = True
    for lo, hi in ((None, h2), (h2, None)):
        part = [r for r in win if (lo is None or r["date"] >= lo) and (hi is None or r["date"] < hi)]
        ns = sum(1 for r in part if r.get("shadow"))
        if ns < MIN_HALF or len(part) - ns < MIN_HALF:
            halves_ok = False
    ok = bool(v.get("ok") and v.get("best") == "S" and halves_ok)
    why = ("تفصل أماميًّا" if ok else
           ("لا تفصل — الأعلى ليست S" if v.get("best") not in (None, "S") else
            ("لا تفصل — نصفٌ دون 10" if (v.get("ok") and not halves_ok) else f"لا تفصل — {v.get('why')}")))
    return {"branch": 1 if ok else 2, "why": why, "d_star": d_star, "h2": h2, "v": v, "n": len(win)}


def avail_verdict(rows, label="exploded50"):
    """فرضيّةُ المالك (العقد §⑤): `avail < BORROW_AVAIL_MAX` مقابل الباقي بين الأماميّة ذات المتاح ·
    أرضيةُ 100 مؤرَّخة · والأعلى يجب أن تكون «<20k»."""
    cut = S.CONFIG["BORROW_AVAIL_MAX"]
    dated = [r for r in rows if r.get("avail") is not None]
    d_star, win = decision_window(dated, floor_s=0, floor_all=FLOOR_AVAIL, key=lambda r: True)
    if d_star is None:
        return {"branch": None, "why": f"لا قياس/لا حكم — مؤرَّخُ المتاح {len(dated)}/{FLOOR_AVAIL}"}
    h2 = sorted(r["date"] for r in win)[len(win) // 2]
    wr = [{"date": r["date"], "f": {"A": "<20k" if r["avail"] < cut else "≥20k"}, "o": {label: bool(r.get(label))}}
          for r in win]
    _t, v = judge(wr, "A", h2)
    if str(v.get("why", "")).startswith("لا حكم"):
        return {"branch": None, "why": f"لا حكم — {v['why']}", "d_star": d_star}
    ok = bool(v.get("ok") and v.get("best") == "<20k")
    return {"branch": 1 if ok else 2, "why": "تفصل" if ok else f"لا تفصل — {v.get('why')}", "d_star": d_star, "v": v}


def capture(rows):
    """وصفيٌّ لا يحكم: التقاطُ المنفجرين `|E∩X|/|E|` لـ`S`/العضو/الجاهز · وضجيجُ `S` لكلّ جلسة · والتقاطع."""
    e = [r for r in rows if r.get("exploded50")]
    days = len({r["date"] for r in rows}) or 1
    def rec(k):
        return (sum(1 for r in e if r.get(k)), len(e))
    return {"S": rec("shadow"), "member": rec("member"), "ready": rec("ready"),
            "noise_S_per_day": sum(1 for r in rows if r.get("shadow") and not r.get("exploded50")) / days,
            "S_and_member": sum(1 for r in rows if r.get("shadow") and r.get("member")), "days": days}


def capture_txt(c):
    def fr(t):
        return f"{t[0]}/{t[1]}" + (f" ({t[0] / t[1] * 100:.0f}%)" if t[1] else "")
    return (f"التقاطُ المنفجرين: S {fr(c['S'])} · العضو {fr(c['member'])} · الجاهز {fr(c['ready'])} · "
            f"ضجيجُ S {c['noise_S_per_day']:.1f}/جلسة · S∩عضو {c['S_and_member']}")


def _row_txt(r):
    return (f"{r['date'][5:]} {r['symbol']:<6} {'J1' if r['j1'] else '—':<2} فجوة {r['gap']:<6} "
            f"{'عضو' if r['member'] else '—':<3} {'جاهز' if r['ready'] else '—':<4} "
            f"{'💥' if r.get('exploded50') else '·'} mg_day " + (f"{r['mg_day']:+.0f}%" if r.get("mg_day") is not None else "—"))


def _rate(rows, pred):
    sub = [r for r in rows if pred(r)]
    k = sum(1 for r in sub if r.get("exploded50"))
    lo, hi = wilson(k, len(sub))
    return f"{k}/{len(sub)}" + (f" = {k / len(sub) * 100:.1f}% [{lo:.0f}·{hi:.0f}]" if sub else "")


# ───────────────────────── التشغيل ─────────────────────────
def main(now_ny=None) -> int:
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        log("⛔ لا POLYGON_API_KEY — خروج 2")
        return 2
    if not _selfcheck():
        log("⛔ الحارسُ الذاتيّ: الأداةُ تكتب/ترسل خارج سجلّها — خروج 5")
        return 5
    now_ny = now_ny or dt.datetime.now(NY)
    until = last_complete_day(now_ny)
    write = os.environ.get("SHADOW_READY", "") == "1"
    anchors = {k: v for k, v in anchor_history(since=SINCE).items() if k[0] <= until}
    if not anchors:
        log("⛔ صفرُ مرساةٍ في تاريخ git (بصمةُ no-op) — خروج 4")
        return 4
    keys = sorted(anchors)
    log(f"🌅🗂️ T-SHADOW · مراسٍ {len(keys)} (منذ {SINCE} حتى {until} · آخرُ يومٍ مكتمل) · "
        f"الأماميّ من {SHADOW_FWD_SINCE} · الكتابة {'✅ SHADOW_READY=1' if write else '🔒 مطفأة'}")
    ledger = {(r["date"], r["symbol"]): r for r in load_ledger()}
    wcommits = _commits("weekly_watchlist.json")
    member_by_day = {}
    for day in sorted({d for d, _ in keys}):
        _sd, js = snapshot_before(wcommits, day, _git_json)
        member_by_day[day] = membership(day, js)
    budget = {"left": AVAIL_CAP}
    rows, fails, nobase = [], 0, 0
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    for (day, sym) in keys:
        a = anchors[(day, sym)]
        bars = fetch_day(sym, day, key)
        if not bars:
            fails += 1
            continue
        dailies = daily_range(sym, day, key)
        b = ledger.get((day, sym))
        got = anchor_row(a, b, bars, dailies, day)
        if got is None:
            nobase += 1
            continue
        f, o, g = got
        mem, rdy = member_by_day.get(day, {}).get(sym, (False, False))
        av, why, asof = avail_capture(sym, day, now_ny, S.ce_borrow_info, budget)
        r = {"schema": 1, "date": day, "symbol": sym, "sample": sample_of(day), "anchor_ms": a.get("anchor_ms"),
             "tod": f.get("tod"), "j1": f.get("j1") == "J1", "gap": f.get("gap"),
             "gap_pct": None if g is None else round(g, 2), "shadow": shadow_flag(f), "member": bool(mem),
             "ready": bool(rdy), "in_tier_ledger": b is not None, "avail": av, "avail_why": why,
             "avail_asof": asof, "run_id": run_id,
             "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
        r.update({k: o.get(k) for k in OUTCOME_FIELDS})
        rows.append(r)
    total = len(keys)
    cover = len(rows) / total
    log(f"🩺 V-S1 التغطية: قِيس {len(rows)} · تعذّر الجلب {fails} · بلا أساس {nobase} من {total} = {cover * 100:.1f}%")
    if cover < MIN_COVER:
        log("⛔ التغطية دون 80% ⇒ لا يُفسَّر رقم — خروج 3")
        return 3
    d0, d1, k50, n50, k100 = IDENTITY
    idn = [r for r in rows if d0 <= r["date"] <= d1]
    if SINCE <= d0 and until >= d1:
        got = (sum(r["exploded50"] for r in idn), len(idn), sum(r["exploded100"] for r in idn))
        log(f"🔒 V-S2 شاهدُ الهُويّة ({d0[5:]}⟶{d1[5:]}): exploded50 {got[0]}/{got[1]} · exploded100 {got[2]} — المنشور "
            f"{k50}/{n50} · {k100} {'✅' if got == (k50, n50, k100) else '⚠️ لا يطابق بت-بت — يُقرأ الفرقُ قبل أيّ حكم'}")
    else:
        log("🔒 V-S2 شاهدُ الهُويّة: خارج نافذة التشغيلة — لم يُقَس")
    # ── ملخّصٌ لكلّ يوم (وصفيّ)
    log("\n📅 لكلّ يوم (مراسٍ · S منفجر/عدد · عضو · جاهز · S∩عضو) — `in` داخل العيّنة لا يحكم:")
    by_day = collections.defaultdict(list)
    for r in rows:
        by_day[r["date"]].append(r)
    for day in sorted(by_day):
        rs = by_day[day]
        def kn(pred):
            sub = [x for x in rs if pred(x)]
            return f"{sum(1 for x in sub if x['exploded50'])}/{len(sub)}"
        log(f"   {day[5:]} [{sample_of(day)}] مراسٍ {kn(lambda x: True)} · S {kn(lambda x: x['shadow'])} · "
            f"عضو {kn(lambda x: x['member'])} · جاهز {kn(lambda x: x['ready'])} · "
            f"S∩عضو {sum(1 for x in rs if x['shadow'] and x['member'])}")
    # ── SXTC حالةً مسمّاة (سؤالُ المالك)
    sx = [r for r in rows if r["symbol"] == "SXTC"]
    log("\n🎯 SXTC: " + (" · ".join(f"{r['date']} {r['tod']} J1={'نعم' if r['j1'] else 'لا'} فجوة={r['gap']} "
                                    f"S={'نعم' if r['shadow'] else 'لا'} عضو={'نعم' if r['member'] else 'لا'} "
                                    f"انفجر={'نعم' if r['exploded50'] else 'لا'}" for r in sx) or "لا مرساةَ في النافذة"))
    # ── السجلّ (D-2 · D-3)
    to_write = ledger_rows(rows, load_ledger_keys())
    if write:
        n = append_ledger(to_write)
        log(f"\n🗂️ السجلّ: كُتب {n} صفًّا أماميًّا جديدًا في `{LEDGER}` (بلا نتيجة · مرّةً لكلّ تاريخ ورمز)")
    else:
        log(f"\n🗂️ السجلّ: 🔒 لم يُكتب (SHADOW_READY ≠ 1) — كان سيُكتب {len(to_write)} صفًّا أماميًّا")
    got_av = [r for r in rows if r["avail"] is not None]
    log(f"💧 R-03 المتاح في جلسة المرساة: {len(got_av)} صفًّا · السقف {AVAIL_CAP} (بقي {budget['left']}) · "
        f"أسبابُ الغياب {dict(collections.Counter(r['avail_why'] for r in rows if r['avail'] is None))}")
    # ── داخلُ العيّنة (لا يحكم) ثمّ الأماميّ — والأرقامُ الحاكمة آخرًا
    ins = [r for r in rows if r["sample"] == "in"]
    fwd = [r for r in rows if r["sample"] == "fwd"]
    log("\n" + "=" * 78 + f"\n📎 داخلُ العيّنة (قبل {SHADOW_FWD_SINCE} · منها اشتُقّت القاعدة) — **لا يحكم**\n" + "=" * 78)
    log(f"   الكلّ {_rate(ins, lambda r: True)} · S {_rate(ins, lambda r: r['shadow'])} · S̄ {_rate(ins, lambda r: not r['shadow'])}")
    log(f"   عضو {_rate(ins, lambda r: r['member'])} · جاهز {_rate(ins, lambda r: r['ready'])}")
    if ins:
        log("   " + capture_txt(capture(ins)))
    log("\n" + "=" * 78 + f"\n🌅 الأماميّ (≥ {SHADOW_FWD_SINCE}) — العقد §④\n" + "=" * 78)
    if fwd:
        c = capture(fwd)
        log(f"   الكلّ {len(fwd)} · S {sum(1 for r in fwd if r['shadow'])} · عضو {sum(1 for r in fwd if r['member'])} · "
            f"جاهز {sum(1 for r in fwd if r['ready'])} · جلسات {c['days']}")
        log(f"   وصفيّ (لا يحكم): S {_rate(fwd, lambda r: r['shadow'])} · S̄ {_rate(fwd, lambda r: not r['shadow'])}")
        log("   " + capture_txt(c))
        log("   📋 صفوفُ S الأماميّة كاملةً (تاريخ · رمز · J1 · فجوة · عضو · جاهز · انفجر · mg_day):")
        for r in sorted((r for r in fwd if r["shadow"]), key=lambda r: (r["date"], r["symbol"])):
            log("      " + _row_txt(r))
        big = max(fwd, key=lambda r: r.get("mg_day") or -1e9)
        _bm = big.get("mg_day")
        log(f"   أكبرُ منفجرٍ أماميّ (SR-P3 · وصفيّ): {big['symbol']} {big['date']} mg_day "
            + (f"{_bm:+.0f}%" if _bm is not None else "—") + f" · {'داخل S' if big['shadow'] else 'خارج S'}")
    else:
        log("   لا صفوفَ أماميّةً بعد")
    v = shadow_verdict(fwd)
    av = avail_verdict(fwd)
    if v["branch"] is None and now_ny.date().isoformat() > STOP_DATE:
        v = dict(v, branch=3, why=f"«لا قياس» — الأرضيةُ لم تُبلَغ حتى {STOP_DATE}")
    log("\n🏁 الحكم (العقد §④): " + (f"الفرعُ {v['branch']} — " if v["branch"] else "") + v["why"]
        + (f" · نافذةُ الحكم حتى {v['d_star']}" if v.get("d_star") else ""))
    log(f"🏁 المتاح (العقد §⑤): {av['why']}")
    log("🔒 لا تلغرام · لا كرون · لا يمسّ «الجاهز» (R-00) — القائمةُ الظلّيّة قياسٌ لا تنبيه.")
    return 0


def _git_json(h, path="weekly_watchlist.json"):
    """لقطةُ git لملفٍّ JSON بالكوميت — `git show` قراءةٌ فقط (الحارسُ يقبل `git show`/`git log` وحدَهما)."""
    try:
        return json.loads(subprocess.run(["git", "show", f"{h}:{path}"],
                                         capture_output=True, text=True).stdout)
    except Exception:                                                # noqa: BLE001
        return None


if __name__ == "__main__":
    sys.exit(wait_for_capture() if "--wait-capture" in sys.argv[1:] else main())
