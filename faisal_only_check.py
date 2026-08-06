#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🎯 `T-FAISAL-ONLY` — هل تلتقط **معايير فيصل المقيسة** المتحرّكين الذين نفوّتهم؟

**العقد:** `faisal_only_prereg.md` (مدفوعٌ **قبل أيّ رقم** · وثلاثةُ ملاحق مؤرَّخة).

**السؤال:** لو استبدلنا عتباتِنا الهندسية بحوافَّ مقيسةٍ من كاتالوج فيصل، هل نلتقط
المتحرّكين الذين لا يلتقطهم الفارز اليوم — **وبأيّ كلفةٍ يومية؟**

**ثلاثُ مجموعاتٍ منفصلة بالبناء:**
- **A** المعايرة: كاتالوج فيصل ⇒ `envelope_p90.json` (لا تدخل الحكم).
- **B** التحقّق: **كلُّ** المتحرّكين المرصودين حيًّا ناقص شبهة التقسيم **وناقص A**.
  ⚠️ **ولا تُقرأ من `was_pivot`** — ذاك وسمٌ يشتقّ من `MIN_PRICE`/`MIN_DROP_FLOOR`/
  `MAX_DROP_PCT`/`PRIOR_SPIKE_FLOOR`، أي **من البوّابات التي يُعيد الظرفُ ضبطها** ⇒
  اشتراطُه يجعل الالتقاط **منفوخًا بالبناء**. المصدرُ الوحيد: `scan_explosions` وهو
  يلتقط من **حركة السعر وحدها**.
- **C** الكلفة: الكونُ من اللقطة، **ناقص `A ∪ B`** (وإلّا كان الشاهدُ يحوي الموجَبات).

🔒 **بحث/قياس فقط:** لا يُستورَد في أيّ مسار إنتاج · لا يكتب حالة · لا تلغرام ·
ولا يُعيد كتابة منطق بوّابة — **يستورد دوالّ الإنتاج حرفيًّا** (‏`walk_symbol` ·
`measure_session` · `inside_envelope` · `decide`) فصفرُ منطقٍ مكرَّر.
"""
from __future__ import annotations

import json
import os
import sys

import catalog_envelope as CE
import envelope_scan as ES
import Super_stock as S

WINDOW = int(os.environ.get("FO_WINDOW", "20"))
EDGES_PATH = os.environ.get("ENVELOPE_EDGES", "envelope_p90.json")
WATCHLIST = os.environ.get("FO_WATCHLIST", "weekly_watchlist.json")
CAPACITY_S0 = int(os.environ.get("FO_CAP_S0", "10"))
# 🚪 `S1` **مثبَّتةٌ بقرار المالك 2026-08-06** = «المحمولون لا يحجزون خانة» ⇒ عمليًّا
#    السعةُ الفعّالة تساوي `WATCHLIST_SIZE` كاملةً للمرشّحين. تُقاس **محاكاةً** هنا.
CAPACITY_S1 = int(os.environ.get("FO_CAP_S1", "10"))


# ── مجموعة B: من سجلّ المتحرّكين الحيّ (حتميّة، لا scratchpad) ────────────────
def load_movers(path: str = WATCHLIST) -> tuple:
    """يُرجع `(rows, symbols, meta)` لمجموعة التحقّق **من المستودع** لا من ملفٍّ مؤقّت.

    شرطا الدخول الوحيدان: رصدَه كاشفُ المتحرّكين · و`suspect_split=False`.
    وشرطُ الخروج الوحيد: العضويةُ في الكاتالوج (تُعلَن)."""
    with open(path, encoding="utf-8") as fh:
        wl = json.load(fh)
    raw = [e for e in (wl.get("explosions") or []) if isinstance(e, dict)]
    clean = [e for e in raw if not e.get("suspect_split")]
    cat = set(CE.CATALOG) - set(CE.EXCLUDED_BY_OWNER)
    overlap = sorted({e["symbol"] for e in clean} & cat)
    rows = [e for e in clean if e["symbol"] not in cat]
    syms = sorted({e["symbol"] for e in rows})
    meta = {"raw": len(raw), "clean": len(clean), "overlap": overlap,
            "events": len(rows), "symbols": len(syms),
            "was_pivot": len([e for e in rows if e.get("was_pivot")])}
    return rows, syms, meta


def first_event(rows: list) -> dict:
    """**أوّلُ** حدثٍ لكل رمز (حتميّ) — الوحدةُ الحاكمة **الرمز** لا الحدث (ملحق ①-ج
    من خطة البناء): رمزٌ بـ12 حدثًا لا يزن اثني عشر ضعف رمزٍ بحدثٍ واحد."""
    out = {}
    for e in sorted(rows, key=lambda r: (r.get("symbol", ""),
                                         str(r.get("expl_date") or r.get("date") or ""))):
        out.setdefault(e["symbol"], e)
    return out


def anchor_index(df, iso: str):
    """فهرسُ يوم الحدث بمطابقةٍ **تامّة**. غيابُه ⇒ `None` **ويُعدّ في المقام** —
    ولا يُخمَّن أقربُ يوم (تخمينُه إمّا تسريبٌ أو قياسُ نافذةٍ خاطئة)."""
    try:
        for i, ts in enumerate(df.index):
            if str(ts.date()) == iso:
                return i
    except Exception:                                            # noqa: BLE001
        return None
    return None


# ── القرار: دالّةُ الإنتاج نفسُها على الطرفين ────────────────────────────────
def window_hit(sym, df, idx, edges, window=WINDOW):
    """هل يقبل الظرفُ الرمزَ في **جلسةٍ واحدة على الأقلّ** من النافذة السابقة للمِرساة؟

    🔒 يُنادى `CE.walk_symbol(..., anchor=idx)` — **نفسُ منطق القصّ الإنتاجيّ**، ويومُ
    المِرساة **مستبعَدٌ بنيويًّا** (‏`range(start, idx)`). يُرجع `(hit, n_rows, why)`."""
    rows, why = CE.walk_symbol(S, sym, df, window=window, anchor=idx)
    if not rows:
        return (None, 0, why)
    return (any(CE.inside_envelope(r, edges) for r in rows), len(rows), why)


def measure(hist, targets, edges, window=WINDOW, log=print, label=""):
    """يقيس الالتقاط على مجموعةٍ من `(رمز، مِرساة-iso)`. يُرجع إحصاءً **بمقامٍ مُعلَن**."""
    hit = miss = no_anchor = no_data = 0
    hits, rows_tot = [], 0
    for sym, iso in targets:
        df = hist.get(sym)
        if df is None or getattr(df, "empty", True):
            no_data += 1
            continue
        idx = anchor_index(df, iso)
        if idx is None or idx <= 0:
            no_anchor += 1
            continue
        h, n, _why = window_hit(sym, df, idx, edges, window)
        rows_tot += n
        if h is None:
            no_anchor += 1
        elif h:
            hit += 1
            hits.append(sym)
        else:
            miss += 1
    denom = hit + miss
    log(f"   ── {label}: قابلٌ للقياس {denom} · مُلتقَط {hit} "
        f"({(hit / denom * 100) if denom else 0:.1f}%) · "
        f"بلا بيانات {no_data} · تعذّر إرساؤه {no_anchor} · جلسات {rows_tot}")
    return {"hit": hit, "miss": miss, "denom": denom, "no_data": no_data,
            "no_anchor": no_anchor, "sessions": rows_tot, "hits": hits}


def main() -> int:
    log = S.log
    frozen = os.environ.get("BT_FROZEN_PATH", "").strip()
    if not frozen:
        log("⛔ `BT_FROZEN_PATH` إلزاميّ — لا تحميلَ حيّ في هذي الأداة.")
        return 2
    # 🔴 **عقدُ `load_edges` كشفه قفلٌ لا قراءة:** تُرجع الحوافَّ **مسطَّحةً**
    #    ومعها `_meta` — لا `{"edges": …}`. وأوّلُ صياغةٍ لي قرأت `["edges"]`
    #    فكانت ستُمرّر حوافَّ **فارغة**، و`decide` تفشل مغلقةً ⇒ **التقاطٌ صفر
    #    يُقرأ حكمًا على الظرف وهو عطلُ أنبوب**. (صنفُ «المُخرَج الفارغ» المدوَّن.)
    try:
        edges = ES.load_edges(EDGES_PATH)
    except Exception as e:                                       # noqa: BLE001
        log(f"⛔ تعذّرت قراءة الحوافّ: {e}")
        return 3
    meta = edges.pop("_meta", {}) if isinstance(edges, dict) else {}
    if not edges:
        log("⛔ حوافُّ فارغة — يُرفَض التشغيل (فاشلٌ-مغلق عمدًا).")
        return 3
    fp = ES.edges_fingerprint(edges)

    # ── ترويسةُ إثباتِ فعاليّة **قبل أيّ رقم** (بصمةُ الـno-op المدوَّنة) ──────
    log("═══ 🎯 T-FAISAL-ONLY ═══")
    log(f"   الحوافّ: بصمة {fp} · لقطة {meta.get('snapshot')} · "
        f"تشغيلة {meta.get('run_id')} · n={meta.get('n_symbols')} · "
        f"as-of {meta.get('asof')}")
    log(f"   المصدر: «{str(meta.get('source'))[:40]}» · "
        f"مستبعَدون: {sorted((meta.get('excluded') or {}).keys())}")
    if not str(meta.get("source", "")).startswith("مُخرَجٌ آليّ"):
        log("⛔ الحوافُّ ليست مُخرَجًا آليًّا — يُرفَض التشغيل.")
        return 4
    ok = False
    try:
        ok = bool(ES.selftest(S))
    except Exception as e:                                       # noqa: BLE001
        log(f"⛔ فحصُ الذات رمى: {e}")
        return 5
    log(f"   فحصُ الذات: {'✅' if ok else '⛔'}")
    if not ok:
        return 5

    try:
        hist = S.load_frozen_dataset(frozen)
    except Exception as e:                                       # noqa: BLE001
        log(f"⛔ تعذّرت اللقطة: {e}")
        return 6
    universe = sorted(hist.keys())
    log(f"   اللقطة: {len(universe)} رمزًا · نافذة {WINDOW} جلسة")

    rows_b, syms_b, mb = load_movers()
    log(f"   B: {mb['raw']} صفًّا خامًا ⟶ بلا شبهة تقسيم {mb['clean']} ⟶ "
        f"ناقص الكاتالوج **{mb['events']} حدثًا · {mb['symbols']} رمزًا**")
    log(f"      التقاطعُ المُستبعَد ({len(mb['overlap'])}): {mb['overlap']}")
    log(f"      ومنهم موسومٌ «كان ارتكازًا» {mb['was_pivot']} — **وصفيًّا لا شرطًا**")

    fe = first_event(rows_b)
    targets = [(s, str(e.get("expl_date") or e.get("date"))[:10])
               for s, e in sorted(fe.items())]

    log("\n═══ 📊 الالتقاط ═══")
    res_b = measure(hist, targets, edges, WINDOW, log, "B (المتحرّكون)")

    # ── C: شاهدُ ضبطٍ **مطابَقُ التاريخ** — نفسُ توزيع المِراسي على رموزٍ أخرى ──
    excl = set(syms_b) | (set(CE.CATALOG) | set(CE.EXCLUDED_BY_OWNER))
    pool = [s for s in universe if s not in excl]
    dates = [d for _s, d in targets]
    ctrl = []
    for i, sym in enumerate(pool):
        ctrl.append((sym, dates[i % len(dates)]))               # حتميّ، بلا عشوائيّة
    cap = int(os.environ.get("FO_CTRL_CAP", "0")) or len(ctrl)
    log(f"   C: بِركةُ الشاهد {len(pool)} رمزًا (‏الكون ناقص A∪B) · يُقاس {min(cap, len(ctrl))}")
    res_c = measure(hist, ctrl[:cap], edges, WINDOW, log, "C (شاهدُ الضبط)")

    b_rate = (res_b["hit"] / res_b["denom"] * 100) if res_b["denom"] else 0.0
    c_rate = (res_c["hit"] / res_c["denom"] * 100) if res_c["denom"] else 0.0
    log("\n═══ ⚖️ الحكم ═══")
    log(f"   M1 الالتقاط على B: {b_rate:.1f}%  ({res_b['hit']}/{res_b['denom']})")
    log(f"   M3 معدّلُ القبول على C: {c_rate:.1f}%  ({res_c['hit']}/{res_c['denom']})")
    if res_b["denom"] and res_c["denom"]:
        log(f"   M4 الإثراء (مقامٌ موحَّد · نافذة {WINDOW} · نفسُ توزيع التواريخ): "
            f"×{(b_rate / c_rate):.2f}" if c_rate else "   M4 الإثراء: ∞ (شاهدٌ صفر)")
    else:
        log("   M4 الإثراء: **لا يُطبع** — المقامان غيرُ متطابقين أو أحدهما صفر.")
    per_day = c_rate / 100.0 * len(pool)
    log(f"   M2 الكلفة التقديرية: ‏{per_day:.0f} مطابق/يوم على {len(pool)} رمزًا "
        f"⇒ {CE.cost_verdict(per_day)}")
    _cand = len([e for e in rows_b if (e.get("base_reason") or "") == "مرشّح"])
    log(f"   M5 الشاهد: الفارزُ الحاليّ على B — مَن اجتاز عند قاعه = **{_cand}**")
    log(f"\n   M6 (المُسلَّم) — السعة S0={CAPACITY_S0} · S1={CAPACITY_S1}: "
        f"**لا يُحسَب في هذي التشغيلة** (يلزمه محاكاةُ الترتيب والسعة يومًا بيوم).")
    log("\n⚠️ حدودُ صدقٍ قائمة: B مختارةٌ على النتيجة ⇒ **التقاطٌ لا ربحية** · "
        "ثمانيةُ أسابيع فقط · انحيازُ بقاء · بلا افتر · n=28 على 11 معيارًا.")
    print(json.dumps({"fingerprint": fp, "B": mb, "capture": b_rate,
                      "control": c_rate, "pool": len(pool)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
