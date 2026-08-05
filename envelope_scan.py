#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📐 `envelope_scan` — **المصدر الوحيد لقرار ظرف الكاتالوج.**

العقد: `catalog_envelope_design.md` · النتيجة: `catalog_envelope_result.md` ·
الخطة: `PIVOT_V2_PLAN.md` §③.

🔑 **لماذا مصدرٌ واحد لا أداتان متشابهتان:** الصيّاد الحيّ والباكتيست يجب أن
يقرّرا **بنفس الدالّة حرفيًّا**، وإلّا قاس أحدُهما مجتمعًا غير الذي يبنيه الآخر —
وهو ذنبٌ موثّق في هذا المستودع مرارًا («منطقان يتفرّقان فيكذب التشخيص»). وله
سابقةٌ ناجحة: `cliff_scan.py` بُنيت لهذا السبب حرفيًّا.

🔒 **حدود صارمة:**
- **لا تُستورَد في `Super_stock.py` إطلاقًا** (مقفولٌ باختبار).
- **`relaxed()` هي الموضع الوحيد الذي يمسّ `CONFIG`** — ومعها بصمةٌ قبل/بعد،
  فتسرّبُ إرخاءٍ يُكشَف بدل أن يعطّل البوّابات بصمت.
- **الحواف تُقرأ من `envelope_p90.json`** ولا تُحسب حيًّا ⇒ تغييرُ رقمٍ يحتاج
  commit مرئيًّا، ولا ينزلق حدٌّ في تشغيلةٍ بلا أثر.
- **`M13`/`M14` فلترٌ نهائيّ إلزاميّ**: معايير الظرف الأحد عشر **لا تشمل** الفلوت
  ولا الشورت، والبوّابتان تُطبَّقان في `scan_market` وحده ⇒ بلا هذا يُسلّم الظرفُ
  فئةً أخرجها المالك بقرارٍ صريح (‏HTZ 129م · PONY 277م).
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os

EDGES_FILE = "envelope_p90.json"

# نفس مفاتيح الإرخاء المستعملة في المعايرة — **تُستورَد لا تُنسَخ** (مصدرٌ واحد).
from catalog_envelope import (                                    # noqa: E402
    CRITERIA, RELAX_ALL, inside_envelope, measure_session,
)

__all__ = [
    "load_edges", "edges_fingerprint", "relaxed", "measure", "decide",
    "chase_ok", "EDGES_FILE",
]


def load_edges(path: str = EDGES_FILE) -> dict:
    """📥 يقرأ الحواف المجمَّدة. يرجّع `{}` عند التعذّر — **ومعناها «لا قرار»**
    لا «كلُّ شيءٍ يمرّ»: `decide` ترفض صراحةً بحوافٍّ فارغة (فاشلة-**مغلقة** هنا
    عمدًا، بخلاف بقيّة المستودع، لأن ظرفًا بلا حوافّ يقبل السوق كلَّه)."""
    try:
        with open(path, encoding="utf-8") as fh:
            blob = json.load(fh)
    except Exception:                                            # noqa: BLE001
        return {}
    edges = blob.get("edges") if isinstance(blob, dict) else None
    if not isinstance(edges, dict) or not edges:
        return {}
    out = {}
    for k, v in edges.items():
        out[k] = tuple(v) if isinstance(v, list) else v
    out["_meta"] = {
        "snapshot": blob.get("snapshot"), "run_id": blob.get("run_id"),
        "pct": blob.get("pct"), "n_symbols": blob.get("n_symbols"),
        "excluded": blob.get("excluded"),
    }
    return out


def edges_fingerprint(edges: dict) -> str:
    """🔏 بصمةٌ حتمية للحواف — تُطبع مع كل مُخرَج فيُعرف **أيّ ظرفٍ** أنتجه."""
    body = {k: v for k, v in (edges or {}).items() if k != "_meta"}
    return hashlib.sha256(
        json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()[:12]


@contextlib.contextmanager
def relaxed(S):
    """🔓 **الموضع الوحيد في المشروع كلِّه الذي يُرخي بوّابات `CONFIG`.**

    يرجعها في `finally` مهما حصل، **ويتحقّق ببصمة** أن الحالة عادت كما كانت —
    فلو تسرّب إرخاءٌ (توازٍ · استثناءٌ غريب) **يُصرَّح به** بدل أن تبقى البوّابات
    معطَّلةً للأبد بصمت. وهذا العطل بعينه معروضٌ في `PIVOT_V2_PLAN.md` §⑨-7."""
    keys = sorted(RELAX_ALL)
    before = hashlib.sha256(
        json.dumps({k: S.CONFIG.get(k) for k in keys},
                   sort_keys=True, default=str).encode()).hexdigest()
    saved = {k: S.CONFIG.get(k) for k in RELAX_ALL}
    try:
        S.CONFIG.update(RELAX_ALL)
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                S.CONFIG.pop(k, None)
            else:
                S.CONFIG[k] = v
        after = hashlib.sha256(
            json.dumps({k: S.CONFIG.get(k) for k in keys},
                       sort_keys=True, default=str).encode()).hexdigest()
        if after != before:
            S.log("⛔ envelope_scan: **تسرّبُ إرخاء** — `CONFIG` لم تعد كما كانت!")


def measure(S, sym: str, df):
    """📏 قيمُ المعايير الأحد عشر لجلسةٍ واحدة — بنداء `analyze_ticker` الإنتاجيّ.

    🔒 يُفوّض لـ`catalog_envelope.measure_session` **حرفيًّا** فلا يتفرّق منطقان."""
    return measure_session(S, sym, df)


def _float_ok(S, row) -> bool:
    """M14 بمرجعٍ واحد — **مجهولٌ يمرّ بفائدة الشك** (قاعدة الفارز الحيّة)."""
    try:
        return not S._float_too_big(row.get("float"))
    except Exception:                                            # noqa: BLE001
        return True


def _short_ok(S, row) -> bool:
    """M13 — شورتٌ معلومٌ وعالٍ ⇒ يُرفَض · ومجهولٌ يمرّ بفائدة الشك."""
    try:
        v = row.get("finra_short")
        if v is None:
            return True
        return float(v) < float(S.CONFIG["SHORT_GATE_MAX"])
    except (TypeError, ValueError):
        return True
    except Exception:                                            # noqa: BLE001
        return True


def chase_ok(S, sym: str, df) -> bool:
    """🚧 **‏D11 — منع الملاحقة (‏`RECENT_RISE_BLOCK_PCT` ‏35%/5ج).**

    🔴 **سببُ وجودها عيبٌ مقيس:** مفاتيح الإرخاء **ثلاثة عشر** ومعايير الظرف
    **أحد عشر** تغطّي **اثني عشر** ⇒ **مفتاحٌ واحد يُرخى بلا معيارٍ يقابله**، وهو
    بعينه `RECENT_RISE_BLOCK_PCT` — **وقرارٌ جذريّ مقفول (‏D11)** ورفضٌ صلب حتى
    للارتداد. ⇒ الظرفُ بلا هذا كان **يلاحق ما ارتفع سلفًا**، وهو ما يمنعه الفارز.

    **والتنفيذ بلا صيغةٍ موازية:** نُرخي كلَّ شيءٍ **إلّا** هذا المفتاح ونعيد نداء
    `analyze_ticker` **الإنتاجيّ**؛ فإن رجع `None` فقد رفضته **بوّابةُ الملاحقة
    نفسها** — لأن كلَّ ما عداها مُرخًى، والبوّابات البنيويّة مرّت سلفًا في `measure`.
    ⇒ **صفر إعادةِ حسابٍ لـ`gain5`** فلا فرصة لصيغةٍ تنحرف.

    🔒 فاشلة-آمنة: استثناءٌ ⇒ `True` (يمرّ بفائدة الشك — قاعدة المستودع)."""
    keys = {k: v for k, v in RELAX_ALL.items() if k != "RECENT_RISE_BLOCK_PCT"}
    saved = {k: S.CONFIG.get(k) for k in keys}
    try:
        S.CONFIG.update(keys)
        return S.analyze_ticker(sym, df) is not None
    except Exception:                                            # noqa: BLE001
        return True
    finally:
        for k, v in saved.items():
            if v is None:
                S.CONFIG.pop(k, None)
            else:
                S.CONFIG[k] = v


def decide(S, sym: str, df, edges: dict, enrich_row: dict = None):
    """✅ **القرار الوحيد** — يرجّع `(مقبول، سبب، القيم)`.

    الترتيب مقصود: ① حوافٌّ صالحة ② قيمٌ قابلة للقياس ③ داخل الظرف
    ④ **`M13`/`M14` فلترٌ نهائيّ**. و`enrich_row` اختياريّ: بلا فلوت/شورت يمرّ
    الرمز بفائدة الشك — **وهو ما يفعله الفارز الحيّ نفسه**، لا تساهلٌ مخترَع.

    🔒 **لا يُنادى من أيّ مسارٍ إنتاجيّ** — الصيّاد والباكتيست فقط."""
    if not edges or all(k not in edges for k, _, _, _ in CRITERIA):
        return (False, "لا حوافّ — الظرف غير محمَّل (رفضٌ صريح لا تساهل)", None)
    vals = measure(S, sym, df)
    if not vals:
        return (False, "تعذّر القياس (بياناتٌ ناقصة)", None)
    if not inside_envelope(vals, edges):
        return (False, "خارج الظرف", vals)
    # 🚧 D11 قبل الفلوت/الشورت — أرخصُ (بلا شبكة) ويُسقط الملاحِق فورًا
    if not chase_ok(S, sym, df):
        return (False, "D11 منع الملاحقة (ارتفع فعلًا — قرارٌ جذريّ مقفول)", vals)
    row = dict(enrich_row or {})
    if not _float_ok(S, row):
        return (False, "M14 فلوت كبير (قرار المالك — مُخرَجٌ تمامًا)", vals)
    if not _short_ok(S, row):
        return (False, "M13 شورت عالٍ", vals)
    return (True, "داخل الظرف", vals)


def selftest(S) -> bool:
    """🧪 فحصُ سلامةٍ سريع يُنادى في رأس أي مُشغّل: هل يعود `CONFIG` سليمًا؟"""
    keys = sorted(RELAX_ALL)
    snap = {k: S.CONFIG.get(k) for k in keys}
    with relaxed(S):
        pass
    return all(S.CONFIG.get(k) == snap[k] for k in keys)


if __name__ == "__main__":                                       # pragma: no cover
    e = load_edges(os.environ.get("ENVELOPE_EDGES", EDGES_FILE))
    print("حوافّ:", "غائبة" if not e else edges_fingerprint(e))
    if e:
        print("الوسم:", e.get("_meta"))
