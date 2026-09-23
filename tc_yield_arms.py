#!/usr/bin/env python3
"""🚦💵 `T-TC-YIELD` — أذرعُ «هل الزنادُ الموازي `T-C` يُسلِّم، وهل ما يُسلِّمه يربح؟»

> العقد: `tc_yield_prereg.md` (مدفوعٌ ومدموجٌ **قبل هذا الملفّ وقبل أيّ رقمٍ حاكم**).
> أمرُ المالك «ابن الاداة» (2026-09-12) بعد «سجل المحور».

🔒 **قراءةٌ فقط:** صفرُ إرسالٍ · صفرُ كتابةِ حالة · ولا سرَّ تلغرام في الـworkflow
   (‏فالإرسالُ **مستحيلٌ بنيويًّا** لا ممنوعٌ بالنيّة).

**المادّةُ تُستورَد ولا تُعاد بناؤها** (‏`V-Y3` — قاعدةُ المشروع «إعادةُ استعمالٍ لا
بناء»): المراسي من `liq_trig_read` (‏مشيُ تاريخ git للحالة) · والمُخرَجُ من
`tierlink_probe` (‏`measure` ⇒ `exploded50`) · و`polygon_prev_close` من الإنتاج.

⚠️ **وحدُّ صدقٍ بنيويٌّ يُطبَع في كلّ تقرير:** المدى **ثلاثُ جلسات** ⇒ الأرجحُ سلفًا
«لا حكم» (‏الفرعُ 3)، **والأرضيّةُ `V-Y1` لا تُرخى لبلوغها.**
"""
from __future__ import annotations

import ast
import datetime as dt
import hashlib
import json
import os
import random
import subprocess
import sys
from collections import defaultdict

import liq_trig_read as LTR
import tierlink_probe as TLP

# ───────────────────────── ثوابتُ العقد — لا تُضبَط من البيئة ────────────────────
SHIP_ISO = LTR.SHIP_ISO            # لحظةُ شحن `R1 ∪ T-C` — قبلها لا زنادَ موازيًا
BOOT, BOOT_SEED = 5000, 20260912   # §⑤: ‏5,000 إعادة · بذرةٌ مثبَّتة
FLOOR_RESOLVED = 120               # `V-Y1`
FLOOR_TC = 40                      # `V-Y1` — منها من `A-TC`
GOV = ("TY1", "TY2", "TY3")        # المعاييرُ الحاكمة (‏`TY4` كلفةٌ تُطبَع)
OUT_ROWS = "tc_yield_rows.jsonl"

# رموزُ الخروج — **متمايزةٌ عمدًا** فلا يُقرأ أحدُها مكانَ آخر
RC_INPUT, RC_PROD, RC_READONLY = 2, 3, 4
RC_NOMAT, RC_COVER, RC_VY4, RC_NOVERDICT = 5, 6, 7, 9


def log(m):
    print(m, flush=True)


def _git_sha(ref: str, path: str) -> str:
    try:
        b = subprocess.run(["git", "show", f"{ref}:{path}"],
                           capture_output=True, timeout=60).stdout
        return hashlib.sha256(b).hexdigest()[:12] if b else "?"
    except Exception:                                            # noqa: BLE001
        return "?"


def production_untouched() -> tuple:
    """`V-Y7` — `Super_stock.py` **بت-بت** مع `origin/main`، وإلّا خروجٌ قبل أيّ قياس."""
    try:
        cur = hashlib.sha256(open("Super_stock.py", "rb").read()).hexdigest()[:12]
    except Exception:                                            # noqa: BLE001
        return False, "?", "?"
    base = _git_sha("origin/main", "Super_stock.py")
    return (base != "?" and cur == base), cur, base


def selfcheck_readonly() -> bool:
    """`V-Y2` — قراءةٌ فقط بالـAST: صفرُ إرسالٍ وصفرُ كتابةِ حالة · ولا يُفتَح
    للكتابة إلّا `OUT_ROWS`."""
    banned = {"send_telegram", "git_save", "save_watchlist", "save_op_entry_state",
              "record_new_alerts", "save_near_watch", "save_hunter_watch"}
    try:
        tree = ast.parse(open(__file__, encoding="utf-8").read())
    except Exception:                                            # noqa: BLE001
        return False
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        fn = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
        if fn in banned:
            return False
        if fn == "open":
            mode = ""
            if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                mode = str(n.args[1].value)
            for kw in n.keywords or []:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = str(kw.value.value)
            if any(c in mode for c in ("w", "a", "x", "+")):
                tgt = n.args[0] if n.args else None
                if not (isinstance(tgt, ast.Name) and tgt.id == "OUT_ROWS"):
                    return False
    return True


# ───────────────────────── الأذرعُ من الوسم (‏§③) ──────────────────────────────
def split_arms(anchors: dict) -> dict:
    """**نقيّة** — تقسم مراسيَ `collect` إلى `A0`/`A-TC`، و`A1` اتّحادُهما.

    المفتاحُ `(رمز · يوم · لحظة)` والوسمُ `trig`: `"T-C"` للزناد الموازي وغيابُه
    `R1`. ⇒ `A1 = A0 ∪ A-TC` **بالبناء** فلا يُحسب مرّتين."""
    a0 = {k: v for k, v in (anchors or {}).items() if not (v or {}).get("trig")}
    atc = {k: v for k, v in (anchors or {}).items() if (v or {}).get("trig")}
    # 🔴 المفاتيحُ **صفّيّة** `(رمز·يوم·لحظة)` فـ`dict(a0, **atc)` يرمي
    #    `keywords must be strings` — أمسكه `TYA2` قبل أيّ تشغيلٍ حيّ.
    return {"A0": a0, "A-TC": atc, "A1": {**a0, **atc}}


def delivered(row: dict) -> bool:
    """§⑤ ‏+ الملحق `§⑬` — «مُسلَّمة» = بلغت المالكَ فعلًا: عمقُ مراحلَ غيرُ فارغ
    **و`alive_eod`** = حاضرةٌ في **آخر لقطةٍ تحمل يومَ المِرساة نفسَه**.

    🔴 **لا `alive`** («باقيةٌ في آخر لقطةٍ من المدى كلِّه»): الحالةُ تُفرَّغ عند
    تبدّل اليوم فكلُّ مِرساةِ يومٍ ماضٍ تُقرأ «مكتومةً» ولو نجت — والعدُّ التراكميُّ
    **نقص** بزيادة المدى (‏جدوى 09-13 ⟶ 09-23). العيبُ أُثبت في `liq_trig_read`
    يوم 09-20 وعولج هناك، **ونُقل هنا بالملحق `§⑬` قبل أيّ رقمٍ حاكم**."""
    r = row or {}
    return bool(r.get("sent")) and bool(r.get("alive_eod"))


# ───────────────────────── الضبطُ الحاكم (‏§④) ─────────────────────────────────
def ctrl_anchor(bars, prev_close, usd_th, pct_th, mode):
    """**نقيّة** — لحظةُ مِرساةِ ضبطٍ على الشموع نفسِها، أو `None`.

    `mode="mom"` ⇒ أوّلُ دقيقةٍ إغلاقُها فوق `prev_close×(1+pct/100)` — **بلا** شرط
    السيولة · `mode="usd"` ⇒ أوّلُ دقيقةٍ يبلغ عندها التراكمُ `usd_th` — **بلا** شرط
    الارتفاع. فيُعزَل نصفا شرطِ `T-C` أحدُهما عن الآخر.

    `bars` صفوفٌ `(t, o, h, l, c, v)` كما يُرجعها `tierlink_probe.fetch_day`."""
    if not bars:
        return None
    cum = 0.0
    for b in bars:
        try:
            t, c, v = int(b[0]), float(b[4]), float(b[5])
        except (IndexError, TypeError, ValueError):
            continue
        cum += c * v
        if mode == "mom":
            if prev_close and c >= float(prev_close) * (1.0 + float(pct_th) / 100.0):
                return t
        elif mode == "usd":
            if cum >= float(usd_th):
                return t
        else:
            return None
    return None


def count_matched(pool, n, seed=BOOT_SEED):
    """**نقيّة** — `C-CNT`: يأخذ من `pool` (‏مفاتيحُ **غيرِ** مراسي `R1`) **العددَ
    نفسَه** `n` الذي أضافه `T-C`، **بالأسبقيّة الزمنيّة وحدَها** ⇒ أعمى عن شرط
    `T-C` بالبناء. وعند تعادلِ اللحظة يُرتَّب بـ`(رمز · يوم)` فحتميٌّ تمامًا
    (‏درسُ `T-PMGATE`: فرزٌ يسقط إلى مقارنة قواميس عند التساوي)."""
    if n <= 0 or not pool:
        return []
    order = sorted(pool, key=lambda k: (int(k[2] or 0), str(k[0]), str(k[1])))
    return order[:int(n)]


# ───────────────────────── الفاصل (‏§⑤) ───────────────────────────────────────
def boot_delta(a_rows, b_rows, universe, reps=BOOT, seed=BOOT_SEED):
    """**نقيّة** — فاصلُ بوتستراب **عنقوديٌّ بالرمز** لفرق نسبةِ `exploded50`.

    🔴 والكونُ **كلُّ رمزٍ في المادّة** لا المُصيبون وحدَهم — وإلّا ضاق الفاصلُ
    انتقاءً بالنتيجة (‏عيبٌ مقيسٌ في `T-RSI-RANK`). يرجّع `(lo, hi, delta)`."""
    syms = sorted(set(universe or []))
    if not syms:
        return (None, None, None)
    ga, gb = defaultdict(list), defaultdict(list)
    for s, hit in (a_rows or []):
        ga[s].append(bool(hit))
    for s, hit in (b_rows or []):
        gb[s].append(bool(hit))

    def _rate(g, pick):
        vals = [h for s in pick for h in g.get(s, [])]
        return (100.0 * sum(vals) / len(vals)) if vals else None

    base_a, base_b = _rate(ga, syms), _rate(gb, syms)
    delta = None if base_a is None or base_b is None else base_a - base_b
    rnd = random.Random(int(seed))
    out = []
    for _ in range(int(reps)):
        pick = [syms[rnd.randrange(len(syms))] for _ in range(len(syms))]
        ra, rb = _rate(ga, pick), _rate(gb, pick)
        if ra is not None and rb is not None:
            out.append(ra - rb)
    if not out:
        return (None, None, delta)
    out.sort()
    lo = out[int(0.025 * (len(out) - 1))]
    hi = out[int(0.975 * (len(out) - 1))]
    return (lo, hi, delta)


# ───────────────────────── الحكم (‏§⑥ و§⑦) ───────────────────────────────────
def read_verdict(crit: dict, floor: dict) -> dict:
    """**نقيّة** — تطبّق الفروعَ الثلاثة **بحرف العقد**.

    `crit` = `{"TY1": (lo, hi, delta), ...}` لكلّ معيارٍ حاكم · `floor` =
    `{"resolved": n, "tc": m}`.
    🔴 **والأرضيّةُ تُفحَص أوّلًا** (‏§⑦-3): دونها **لا يُقرأ شيءٌ** من `TY1`-`TY3`
    — وهو بعينه ما منع `T-PMGATE` من إخراج «عبرت» كاذبة."""
    ok_floor = (int(floor.get("resolved") or 0) >= FLOOR_RESOLVED
                and int(floor.get("tc") or 0) >= FLOOR_TC)
    if not ok_floor:
        return {"branch": 3, "floor_ok": False, "passed": {},
                "why": (f"الأرضيّة `V-Y1` لم تُبلَغ: محسومةٌ مُسلَّمة "
                        f"{floor.get('resolved')} من {FLOOR_RESOLVED} · "
                        f"من `A-TC` {floor.get('tc')} من {FLOOR_TC}")}
    passed = {}
    for name in GOV:
        lo, hi, d = (crit.get(name) or (None, None, None))
        passed[name] = bool(d is not None and d > 0 and lo is not None
                            and hi is not None and lo > 0)
    branch = 1 if all(passed.values()) else 2
    return {"branch": branch, "floor_ok": True, "passed": passed,
            "why": ("الثلاثةُ الحاكمة تعبر" if branch == 1
                    else "سقط " + "، ".join(n for n in GOV if not passed[n]))}


# ───────────────────────── المسارُ الحيّ ───────────────────────────────────────
def _pool_keys(snapshots, since_iso: str) -> dict:
    """كلُّ `LIQ:*` رُئي في اللقطات **ولو لم يرسُ** — كونُ الضبط `C-CNT`.

    المفتاحُ `(رمز · يوم · أوّلُ تقييمٍ ms)` ⇒ الأسبقيّةُ الزمنيّة مقروءةٌ منه
    مباشرة. ويُقصَر على ما بعد الشحن فالكونُ **نفسُه** لكلّ ذراع (‏`V-Y3`)."""
    pool = {}
    for _ts, st in (snapshots or []):
        if not isinstance(st, dict):
            continue
        for k, v in st.items():
            if not k.startswith(LTR.PREFIX) or not isinstance(v, dict):
                continue
            day = str(v.get("date") or "")
            if not day or day < since_iso[:10]:
                continue
            ms = int(v.get("tc_seen_ms") or v.get("last_eval_ms") or 0)
            key = (k[len(LTR.PREFIX):], day, ms)
            if key[:2] not in {p[:2] for p in pool}:
                pool[key] = {"symbol": key[0], "date": day, "first_ms": ms}
    return pool


def _measure_key(sym, day, a_row, key, cache):
    """يجلب الشموعَ ويُرجع `(o, bars, prev_close)` — `o` من `tierlink_probe.measure`."""
    bars = cache.get((sym, day))
    if bars is None:
        bars = TLP.fetch_day(sym, day, key) or []
        cache[(sym, day)] = bars
    if not bars:
        return None, [], None
    dailies = TLP.daily_range(sym, day, key)
    pcs = [c for (d, _h, c) in (dailies or []) if d < day]
    prev_close = pcs[-1] if pcs else None
    o = TLP.measure(a_row, None, bars, dailies)
    return o, bars, prev_close


def main() -> int:                                               # noqa: PLR0911, PLR0912, PLR0915
    dry = str(os.environ.get("TCYIELD_DRY", "")).strip() == "1"
    if not selfcheck_readonly():
        log("⛔ `V-Y2` سقط — الأداةُ ليست قراءةً فقط · خروج 4")
        return RC_READONLY
    ok, cur, base = production_untouched()
    if not ok:
        log(f"⛔ `V-Y7` سقط — `Super_stock.py` ليس بت-بت ({cur} مقابل {base}) · خروج 3")
        return RC_PROD
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key and not dry:
        log("⛔ لا `POLYGON_API_KEY` — والحصيلةُ تلزمها الشموع · خروج 2")
        return RC_INPUT

    ref = os.environ.get("TCYIELD_REF", "origin/main")
    snaps, bad = LTR.git_snapshots(ref=ref)
    if not snaps:
        log(f"⛔ صفرُ لقطةٍ من `{ref}` · خروج 5")
        return RC_NOMAT
    res = LTR.collect(snaps)
    anchors = {k: v for k, v in res["anchors"].items()
               if str(k[1] or "") >= SHIP_ISO[:10]}
    arms = split_arms(anchors)
    log(f"🚦💵 **`T-TC-YIELD`** · مرجع `{ref}` · {res['revs']} مراجعة"
        + (f" · {bad} تالفة" if bad else "")
        + f" · المدى {res['span'][0]} ⟶ {res['span'][1]}")

    # ── الشقُّ (أ) — التسليمُ والكلفة · **وصفيٌّ بنصّ العقد §⑩-5** ──────────────
    days = sorted({k[1] for k in anchors})
    log("─" * 70)
    log("📬 **الشقّ (أ) — التسليمُ والكلفة (‏وصفيٌّ لا يدخل أيّ معيار)**")
    for name in ("A0", "A-TC", "A1"):
        g = arms[name]
        syms = {(k[0], k[1]) for k in g}
        snt = sum(1 for v in g.values() if delivered(v))
        msgs = sum(len(v.get("sent") or []) for v in g.values() if delivered(v))
        pct = (100.0 * snt / len(g)) if g else 0.0
        log(f"   {name:5s} مِراسٍ {len(g):4d} · رموز/يوم {len(syms):4d} · "
            f"مُسلَّمة {snt:4d} ({pct:5.1f}%) · رسائل {msgs:4d}"
            + (f" · /يوم {msgs/len(days):.1f}" if days else ""))
    # `TY4` — الكلفةُ فرقًا (تُطبَع ولا تُسقِط وحدَها)
    if days:
        m1 = sum(len(v.get("sent") or []) for v in arms["A1"].values() if delivered(v))
        m0 = sum(len(v.get("sent") or []) for v in arms["A0"].values() if delivered(v))
        log(f"   💸 `TY4` كلفةُ الطبقة: **{(m1 - m0)/len(days):+.1f} رسالة/يوم** "
            f"(‏{m1} مقابل {m0} على {len(days)} جلسات)")

    if dry:
        log("─" * 70)
        log("🧪 **وضعُ الجدوى** — سؤالٌ واحد: هل تبلغ الأرضيّةُ `V-Y1`؟ "
            "**صفرُ `Δ` وصفرُ حكمٍ وصفرُ فاصل** بنيويًّا.")
        log(f"   المرشَّحُ للحسم: {len(arms['A1'])} مِرساةً · منها من `A-TC` "
            f"{len(arms['A-TC'])} — **والحسمُ يحتاج الشموعَ فلا يُقدَّر هنا**")
        log(f"   الأرضيّة: {FLOOR_RESOLVED} محسومةً مُسلَّمة منها {FLOOR_TC} من `A-TC`")
        log("   ⚠️ وضعُ الجدوى **يُجيز ما يمرّ به وحدَه** (درسُ `T-PMGATE`).")
        return 0

    # ── الشقُّ (ب) — الحصيلة ─────────────────────────────────────────────────
    pool = _pool_keys(snaps, SHIP_ISO)
    cache, rows, fails, nobase = {}, [], 0, 0
    per_arm = defaultdict(list)          # اسمُ الذراع ⟶ [(رمز، أصاب)]
    universe = set()

    a_hist = TLP.anchor_history(since=SHIP_ISO[:10])
    for k, v in sorted(anchors.items()):
        sym, day, ams = k
        a_row = a_hist.get((day, sym)) or {
            "anchor_ms": ams, "anchor_price": v.get("price"),
            "date": day, "symbol": sym}
        o, bars, prev_close = _measure_key(sym, day, a_row, key, cache)
        if not bars:
            fails += 1
            continue
        if o is None:
            nobase += 1
            continue
        universe.add(sym)
        hit = bool(o.get("exploded50"))
        dlv = delivered(v)
        rows.append({"symbol": sym, "date": day, "anchor_ms": ams,
                     "trig": v.get("trig"), "delivered": dlv,
                     "exploded50": hit, "exploded100": bool(o.get("exploded100")),
                     "kasih30_cut": bool(o.get("kasih30_cut")),
                     "prev_close": prev_close})
        if not dlv:                       # §⑤ — الحسابُ على المُسلَّم فقط
            continue
        per_arm["A1"].append((sym, hit))
        per_arm["A-TC" if v.get("trig") else "A0"].append((sym, hit))

    total = len(anchors)
    cover = (len(rows) / total) if total else 0.0
    log("─" * 70)
    log(f"🩺 التغطية: قِيس {len(rows)} · تعذّر الجلب {fails} · بلا أساس {nobase} "
        f"من {total} = {cover*100:.1f}%")
    if cover < 0.80:
        log("⛔ التغطية دون 80% ⇒ لا يُفسَّر رقم · خروج 6")
        return RC_COVER
    return _judge(arms, per_arm, pool, cache, key, universe, rows, days)


def _ctrl_rows(pool, cache, key, mode, usd_th, pct_th):
    """يبني صفوفَ ضبطِ `C-MOM`/`C-USD` من **الكون نفسِه** (‏`V-Y3`).

    لكلّ رمزٍ في البِركة: شموعُ اليوم ⟶ لحظةُ مِرساةِ الضبط ⟶ `measure` منها.
    لا جلبةَ إضافيّةٌ لذراعٍ دون أخرى — والكيشُ مشترك."""
    out = []
    for (sym, day, _ms) in sorted(pool):
        bars = cache.get((sym, day))
        if bars is None:
            bars = TLP.fetch_day(sym, day, key) or []
            cache[(sym, day)] = bars
        if not bars:
            continue
        dailies = TLP.daily_range(sym, day, key)
        pcs = [c for (d, _h, c) in (dailies or []) if d < day]
        pc = pcs[-1] if pcs else None
        t = ctrl_anchor(bars, pc, usd_th, pct_th, mode)
        if not t:
            continue
        px = next((float(b[4]) for b in bars if int(b[0]) == t), None)
        o = TLP.measure({"anchor_ms": t, "anchor_price": px, "date": day,
                         "symbol": sym}, None, bars, dailies)
        if o is None:
            continue
        out.append((sym, bool(o.get("exploded50"))))
    return out


def _judge(arms, per_arm, pool, cache, key, universe, rows, days):  # noqa: PLR0915
    """يحسب الضبطَ الثلاثيّ ثم يُصدر الحكمَ بحرف العقد."""
    import Super_stock as S                                       # noqa: PLC0415
    usd_th, pct_th = float(S.LIQ_TC_USD), float(S.LIQ_TC_PCT)
    log(f"🔬 الضبطُ الحاكم — العتباتُ من الإنتاج: ‏${usd_th:,.0f} · {pct_th:g}%")

    # `V-Y4` — `A0` يجب أن يُعيد عددَ مراسي `R1` المقروءَ من الوسم بت-بت
    n_a0_tag = len(arms["A0"])
    n_a0_rows = len({(r["symbol"], r["date"], r["anchor_ms"])
                     for r in rows if not r["trig"]})
    log(f"🔒 `V-Y4`: مراسي `R1` بالوسم {n_a0_tag} · المقروءة في الصفوف {n_a0_rows}")
    if n_a0_tag != n_a0_rows:
        # 🔴 حارسٌ **يوقف** لا يطبع: لو اختلف العددُ فالمادّةُ ليست ما يدّعيه
        #    الوسم ⇒ لا يُقرأ أيُّ `Δ`. (درسُ طفرة `n4` في `PGA12`.)
        log(f"⛔ `V-Y4` سقط ({n_a0_tag} مقابل {n_a0_rows}) — لا يُقرأ رقم · خروج 7")
        return RC_VY4

    c_mom = _ctrl_rows(pool, cache, key, "mom", usd_th, pct_th)
    c_usd = _ctrl_rows(pool, cache, key, "usd", usd_th, pct_th)
    # `C-CNT` — العددُ نفسُه من غيرِ مراسي `R1`، بالأسبقيّة الزمنيّة وحدَها
    r1_syms = {(k[0], k[1]) for k in arms["A0"]}
    free = [p for p in pool if (p[0], p[1]) not in r1_syms]
    picked = count_matched(free, len(arms["A-TC"]))
    hit_by = {(r["symbol"], r["date"]): r["exploded50"] for r in rows}
    c_cnt = [(s, bool(hit_by.get((s, d), False))) for (s, d, _m) in picked]
    for nm, rws in (("C-MOM", c_mom), ("C-USD", c_usd), ("C-CNT", c_cnt)):
        universe.update(s for s, _h in rws)
        log(f"   {nm:6s} صفوفٌ {len(rws):4d} · أصاب "
            f"{sum(1 for _s, h in rws if h):3d}")

    crit = {
        "TY1": boot_delta(per_arm["A1"], per_arm["A0"], universe),
        "TY2": boot_delta(per_arm["A-TC"], c_mom, universe),
        "TY3": boot_delta(per_arm["A-TC"], c_cnt, universe),
    }
    desc = {"A-TC−C-USD": boot_delta(per_arm["A-TC"], c_usd, universe)}
    resolved = len(per_arm["A1"])
    floor = {"resolved": resolved, "tc": len(per_arm["A-TC"])}

    log("─" * 70)
    log("📊 **الشقّ (ب) — الحصيلة على المُسلَّم فقط (‏`exploded50`)**")
    for nm in ("A0", "A-TC", "A1"):
        g = per_arm[nm]
        k = sum(1 for _s, h in g if h)
        log(f"   {nm:5s} n={len(g):4d} · أصاب {k:3d} · "
            + (f"{100.0*k/len(g):5.1f}%" if g else "   — "))
    for nm in GOV:
        lo, hi, d = crit[nm]
        log(f"   {nm}: Δ = " + ("—" if d is None else f"{d:+.2f} نقطة")
            + (f" · فاصل [{lo:+.2f}, {hi:+.2f}]" if lo is not None else ""))
    for nm, (lo, hi, d) in desc.items():
        log(f"   *(وصفيّ)* {nm}: Δ = " + ("—" if d is None else f"{d:+.2f}")
            + (f" [{lo:+.2f}, {hi:+.2f}]" if lo is not None else ""))

    v = read_verdict(crit, floor)
    try:
        with open(OUT_ROWS, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    except OSError:
        pass

    log("─" * 70)
    if v["branch"] == 3:
        log(f"⚖️ **الفرعُ 3 — «لا حكم»**: {v['why']}")
        log("   📅 **وتاريخُ إعادةِ القراءة مكتوبٌ لا وعدًا بلا موعد:** "
            + (dt.date.today() + dt.timedelta(days=30)).isoformat()
            + " — أو متى بلغت الأرضيّةُ أيُّهما أسبق.")
        log("   ⛔ ولا تُرخى الأرضيّةُ لبلوغها (‏§⑦-3 · §⑩-1).")
        return RC_NOVERDICT
    if v["branch"] == 1:
        log(f"⚖️ **الفرعُ 1 — تُوصى بإبقاء الطبقة**: {v['why']}")
    else:
        log(f"⚖️ **الفرعُ 2 — لا تُوصى**: {v['why']}")
        log("   والقرارُ للمالك: الإبقاء أو `LIQ_TC_ON=False`.")
    if not v["passed"].get("TY2", True):
        log("🔓 **وشرطُ §⑫ انعقد:** سقوطُ `TY2` ⇒ يُغلَق محورُ «السيولةُ التراكميّة "
            "مرجعًا للمِرساة» **إغلاقًا مُنفَّذًا لا مكتوبًا**.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
