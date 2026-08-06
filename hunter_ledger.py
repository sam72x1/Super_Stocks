#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🌱 `hunter_ledger` — **ذاكرةُ الصيّادين**: سجلٌّ أماميٌّ متراكم لمرشّحيهم.

**العقد:** `harvest_prereg.md` (مدفوعٌ **قبل جمع صفٍّ واحد**).

🔴 **سببُ وجوده مقيس:** الصيّادون الأربعة **بلا ذاكرة** — ثلاثةٌ لا يكتبون مرشّحيهم
إطلاقًا، والرابع يكتب بوضع `"w"` فيدهس مُخرَجَ الليلة السابقة ⇒ «التقطنا NUWE قبل
انفجاره بيومين» **حكايةٌ لا سجلّ**، و«قيد الإثبات الأماميّ» **عبارةٌ بلا آلة**.

🔒 **العقدُ الصارم مع الصيّادين — ثلاثةُ بنودٍ لا تُخرَق:**
1. **لا يُغيّر قرارًا:** يُنادى **بعد** اكتمال الاختيار، ويقرأ الصفوف ولا يكتب فيها
   (نسخةٌ ضحلة) ⇒ مجموعةُ المطابقين وترتيبُهم **بت-بت** (‏`H1`).
2. **لا يرمي أبدًا:** كلُّ مسارٍ داخل `try` ويُرجع عددًا ⇒ عطلُ التسجيل **لا يُسقط
   تنبيهًا** ولا يمنع إرسالًا.
3. **مُتَمَاثِل** (idempotent): `(صيّاد، جلسة، رمز)` مفتاحٌ فريد ⇒ الكرونان الليليّان
   لا يُنتجان صفَّين (‏`H2`).

⚠️ **والمرجعُ `ref_close` يُخزَّن لحظةَ الرصد** لا وقتَ التقييم (‏`H3`) — وإلّا صار
المقياسُ يتحرّك تحت أقدامنا.
"""
from __future__ import annotations

import json
import os

LEDGER_FILE = "hunter_ledger.jsonl"
FORWARD_SESSIONS = 40         # نافذةُ الحسم (= `BACKTEST_FORWARD_DAYS`)
HIT_PRIMARY = 2.0             # `hit100` — هدفُ الوصفة المنصوص (‏×2)
HIT_SECONDARY = 1.5           # `hit50` — مساند
MAX_ROWS = 20000              # سقفٌ **مُعلَنٌ بعدّاده** لا قصٌّ صامت (‏H6)

# الحقولُ المنسوخة من صفّ المرشّح (إن وُجدت) — **قراءةٌ فقط**، لا تُبتدَع قيمة.
_COPY = ("price", "float", "short_avail", "best_spike", "drop_pct", "rr",
         "readiness", "score", "pivot", "half", "ref")


def _key(hunter, session, symbol) -> str:
    return f"{hunter}|{session}|{str(symbol).upper()}"


def load(path: str = None) -> list:
    """يقرأ السجلّ. **فاشلٌ-آمن**: ملفٌّ غائبٌ أو سطرٌ تالف ⇒ يُتخطّى بلا انهيار.

    🔴 والمسارُ **يُحسَم وقت النداء**: `= LEDGER_FILE` افتراضًا يُربَط **وقت
    التعريف** فلا يصله أيُّ تحويلٍ لاحق للثابت — وهو الفخُّ الذي جعل السويّة
    تكتب في السجلّ الحقيقيّ رغم تحويله."""
    path = path or LEDGER_FILE
    out = []
    try:
        if not os.path.exists(path):
            return out
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except Exception:                                # noqa: BLE001
                    continue
                if isinstance(row, dict) and row.get("key"):
                    out.append(row)
    except Exception:                                            # noqa: BLE001
        return out
    return out


def build_rows(hunter, session, rows, ref_of=None, kind="candidate") -> list:
    """🧱 نقيّة: يحوّل مرشّحي صيّادٍ إلى صفوفِ سجلّ. **لا تلمس `rows`.**

    `ref_of(sym)` يُرجع إغلاقَ جلسة الرصد — **يُقرأ الآن ويُجمَّد** (‏`H3`)."""
    out = []
    for r in (rows or []):
        try:
            sym = str((r or {}).get("symbol") or "").upper()
            if not sym:
                continue
            ref = None
            if ref_of is not None:
                try:
                    ref = ref_of(sym)
                except Exception:                                # noqa: BLE001
                    ref = None
            if ref is None:
                try:
                    ref = float(r.get("price"))
                except (TypeError, ValueError):
                    ref = None
            rec = {"key": _key(hunter, session, sym), "hunter": str(hunter),
                   "session": str(session), "symbol": sym, "kind": kind,
                   "ref_close": (float(ref) if ref is not None else None),
                   "fwd": FORWARD_SESSIONS, "outcome": None}
            for k in _COPY:
                if isinstance(r, dict) and r.get(k) is not None:
                    try:
                        rec[k] = (float(r[k]) if isinstance(r[k], (int, float))
                                  else str(r[k])[:40])
                    except Exception:                            # noqa: BLE001
                        pass
            out.append(rec)
        except Exception:                                        # noqa: BLE001
            continue
    return out


def record(hunter, session, rows, ref_of=None, kind="candidate",
           path: str = None, log=None) -> int:
    """✍️ يُلحق صفوفَ صيّادٍ بالسجلّ ويُرجع **عدد الجديد**.

    🔒 **لا يرمي أبدًا** (البند 2) · **ومُتَمَاثِل** (البند 3): ما كان مفتاحُه
    موجودًا يُتخطّى ⇒ الكرونان لا يُنتجان صفَّين.

    🔴 والمسارُ **يُحسَم وقت النداء** (نفسُ فخّ الافتراض المربوط)."""
    path = path or LEDGER_FILE
    try:
        new = build_rows(hunter, session, rows, ref_of=ref_of, kind=kind)
        if not new:
            return 0
        have = {r.get("key") for r in load(path)}
        fresh = [r for r in new if r["key"] not in have]
        dup = len(new) - len(fresh)
        if fresh:
            with open(path, "a", encoding="utf-8") as fh:
                for r in fresh:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        if log:
            log(f"🌱 السجلّ: +{len(fresh)} صفًّا لـ{hunter}"
                + (f" · تُخطّي {dup} مكرّرًا (الكرون الثاني)" if dup else ""))
        return len(fresh)
    except Exception as e:                                       # noqa: BLE001
        if log:
            log(f"⚠️ تعذّر التسجيل ({e}) — **ولا يُسقط التنبيه**.")
        return 0


def score(ref_close, highs) -> dict:
    """📏 نقيّة: حَسْمُ صفٍّ من قمم الجلسات **التالية** لجلسة الرصد.

    ⚠️ **الشموعُ المُمرَّرة يجب أن تبدأ بعد جلسة الرصد** — والمُنادي مسؤولٌ عن
    القصّ؛ ويُقفَل ذلك باختبار. و**لا حسم قبل انقضاء النافذة** (‏`H5`)."""
    try:
        ref = float(ref_close)
        vals = [float(h) for h in (highs or []) if h is not None and h == h]
    except (TypeError, ValueError):
        return {"resolved": False, "reason": "مرجعٌ أو شموعٌ غير صالحة"}
    if ref <= 0:
        return {"resolved": False, "reason": "مرجعٌ غير موجب"}
    if len(vals) < FORWARD_SESSIONS:
        return {"resolved": False, "elapsed": len(vals),
                "reason": f"لم تنقضِ النافذة ({len(vals)}/{FORWARD_SESSIONS})"}
    seg = vals[:FORWARD_SESSIONS]
    mx = max(seg)
    return {"resolved": True, "elapsed": FORWARD_SESSIONS,
            "max_gain": round((mx / ref - 1.0) * 100.0, 2),
            "hit100": bool(mx >= ref * HIT_PRIMARY),
            "hit50": bool(mx >= ref * HIT_SECONDARY)}


def pending(rows, resolved_keys=None) -> list:
    """مَن ينتظر الحسم: بلا `outcome` ومرجعُه صالح."""
    done = set(resolved_keys or ())
    return [r for r in (rows or [])
            if not r.get("outcome") and r.get("key") not in done
            and r.get("ref_close")]


def apply_outcomes(rows, outcomes, path: str = None, log=None) -> int:
    """يعيد كتابة السجلّ بعد إلحاق الأحكام. **فاشلٌ-آمن** ويُعلن القصّ (‏H6).

    🔴 والمسارُ **يُحسَم وقت النداء** (نفسُ فخّ الافتراض المربوط)."""
    path = path or LEDGER_FILE
    try:
        by_key = dict(outcomes or {})
        n = 0
        for r in rows:
            oc = by_key.get(r.get("key"))
            if oc and oc.get("resolved"):
                r["outcome"] = oc
                n += 1
        cut = max(0, len(rows) - MAX_ROWS)
        if cut and log:
            log(f"✂️ السجلّ: قُصَّ {cut} صفًّا أقدم (سقف {MAX_ROWS}) — **مُعلَن**.")
        keep = rows[cut:]
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            for r in keep:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        os.replace(tmp, path)
        if log:
            log(f"🌱 حُسم {n} صفًّا · السجلّ الآن {len(keep)} صفًّا.")
        return n
    except Exception as e:                                       # noqa: BLE001
        if log:
            log(f"⚠️ تعذّر حفظ الأحكام ({e}).")
        return 0


def summary(rows) -> dict:
    """📊 ملخّصٌ نقيّ لكل صيّاد + الشاهد — **بلا حكم** (الحكمُ في `harvest_prereg`)."""
    out = {}
    for r in (rows or []):
        h = str(r.get("hunter") or "?")
        d = out.setdefault(h, {"n": 0, "resolved": 0, "hit100": 0, "hit50": 0,
                               "gains": []})
        d["n"] += 1
        oc = r.get("outcome") or {}
        if oc.get("resolved"):
            d["resolved"] += 1
            d["hit100"] += 1 if oc.get("hit100") else 0
            d["hit50"] += 1 if oc.get("hit50") else 0
            if oc.get("max_gain") is not None:
                d["gains"].append(float(oc["max_gain"]))
    return out
