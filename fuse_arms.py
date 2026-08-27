#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔥🩸 `T-FUSE` — «سجّل الفتيل» (العقد: `fuse_prereg.md` مدفوعٌ `323b474f`
**قبل هذا الملفّ**).

**السؤال (§①):** بين حلقات الجلوس المضغوط (`press_read` بنافذة التنبيه 40)،
هل «الفتيل» — قاعٌ طازجٌ (‏`hold` ‏0-2) جاء **كنسًا بعد حفظ** (‏`swept`) —
يرفع التوقّع `R` ونسبةَ بلوغ الهدف فوق بقيّة الحلقات؟

**المحرّك — إعادةُ استعمالٍ بالاسم، صفرُ مِشيةٍ منسوخة (‏§②/`FV0`-أ):**
الحلقاتُ من `press_wake_arms.walk_symbol_wake` **نفسِها** (المجمَّدة —
أرقامُها منشورةٌ عبر `gold_entry_result` ⇒ `CAP15`)، ثم تُثرى كلُّ حلقةٍ
بنداء `press_read` **واحدٍ** عند فهرسها (‏`age`/`prev_hold`/`tested_level`)
مع فحص اتّساقٍ صارم: `hold`/`swept` المعادان يطابقان الحلقةَ وإلّا خروج 3.

🔒 بحث/قياس حصرًا: قراءةٌ فقط · الإنتاجُ لا يستوردها · لا `LOGIC_VERSION`."""
from __future__ import annotations

import json
import os
import sys

# §③ — ثوابتُ العقد (لا خليّةَ تُضاف بعد الأرقام)
FRESH_MAX = 2      # «القاعُ الطازج» = hold ‏0-2 — من قياس §⑮ (‏79% عشيّة الانفجار)
AGE_MIN = 20       # «صعد قبل المتوسطات = رزق لم يكتب» — سلّم فيصل 20/30/50
                   # (`faisal_verbatim` — `EDU_0827_school_two_models_ma_ladder`)
GOV_CELL = "F1"    # الحاكمة: swept=True و hold ≤ FRESH_MAX
W_ALERT = 40       # نافذةُ قراءة التنبيه الإنتاجية (ALERT_W) — §②
# مِرساةُ التكامل §⑬ (تُجمَع عبر الثلاث عند الحصاد): 5371 محسومة · 19.08% · +0.174R
PUB13 = {"decided": 5371, "win_pct": 19.08, "ev": 0.174}
OUT_ROWS = "fuse_rows.jsonl"


def _log(m):
    print(m, flush=True)


def cell_of(swept, hold):
    """نقيّة (‏§③): الخليّةُ من محورَي (كنسٌ بعد حفظ × طزاجة القاع).
    التقسيمُ تامٌّ ومنفصل: `F1` كنسٌ وقاعٌ طازج (الحاكمة) · `F2` كنسٌ ثم
    عاد فحفظ · `F3` طازجٌ بلا بنية · `F4` جلوسٌ هادئ. تعذّرٌ ⇒ None يُعَدّ."""
    try:
        s, h = bool(swept), int(hold)
    except (TypeError, ValueError):
        return None
    if h < 0:
        return None
    fresh = h <= FRESH_MAX
    if s:
        return "F1" if fresh else "F2"
    return "F3" if fresh else "F4"


def age_of(hi, i, w=W_ALERT):
    """نقيّة (‏§② · `FV2`): `age` = ‏i − j_star بسطر `press_read` الحرفيّ
    (‏argmax على `hi[i-w+1:i+1]`) — ترجع (age، قمّة النافذة) للتحقّق بت-بت
    مع `r["high_w"]` (المدوَّرة لأربع خانات). تعذّرٌ ⇒ (None, None)."""
    try:
        i = int(i)
        if i + 1 < w:
            return None, None
        win_hi = hi[i - w + 1:i + 1]
        j_star = int(i - w + 1 + max(range(len(win_hi)),
                                     key=lambda k: win_hi[k]))
        return i - j_star, round(float(hi[j_star]), 4)
    except Exception:                                            # noqa: BLE001
        return None, None


def enrich_episode(df, hi, ep):
    """إثراءُ حلقةٍ واحدة: نداءُ `press_read` **واحد** عند فهرسها + `age`.

    🔒 فحصُ الاتّساق (‏`FV0`-أ): `hold`/`swept` المعادان من `press_read`
    يجب أن يطابقا حقلَي الحلقة من `walk_symbol_wake` — تفرّقٌ ⇒ "mismatch"
    (يوقف التشغيلة بخروج 3 — عطبُ أداةٍ لا نتيجة)."""
    import press_radar as PR                                     # noqa: PLC0415
    i = int(ep["i"])
    sl = df.iloc[:i + 1]
    r = PR.press_read(sl, w=W_ALERT)
    if not r:
        return "gone", None
    if int(r.get("hold_sessions") or 0) != int(ep["hold"]):
        return "mismatch", None
    if bool(r.get("swept_hold")) != bool(ep["swept"]):
        return "mismatch", None
    age, top = age_of(hi, i, W_ALERT)
    if age is None or top != r.get("high_w"):
        return "age_mismatch", None
    return "ok", {"age": int(age), "prev_hold": int(r.get("prev_hold") or 0),
                  "tl": r.get("tested_level") is not None}


def walk(sym, df, year):
    """حلقاتُ الرمز: `walk_symbol_wake` **بالاسم** ثم الإثراء لكلّ حلقة."""
    import press_wake_arms as PW                                 # noqa: PLC0415
    eps = PW.walk_symbol_wake(sym, df, year=year)
    if not eps:
        return [], {}
    try:
        hi = df["High"].values.astype(float)
    except Exception:                                            # noqa: BLE001
        return [], {"no_high": len(eps)}
    out, issues = [], {}
    for ep in eps:
        st, extra = enrich_episode(df, hi, ep)
        if st != "ok":
            issues[st] = issues.get(st, 0) + 1
            if st in ("mismatch", "age_mismatch"):
                issues["fatal"] = issues.get("fatal", 0) + 1
            continue
        row = dict(ep)
        row.update(extra)
        row["sym"] = sym
        row["cell"] = cell_of(row["swept"], row["hold"])
        out.append(row)
    return out, issues


def _counts(sub):
    dec = [e for e in sub if e["oc"] in ("win", "loss")]
    k = sum(1 for e in dec if e["oc"] == "win")
    nf = sum(1 for e in sub if e["oc"] == "no_fill")
    return len(sub), len(dec), k, nf


def _cline(name, sub):
    import press_wake_arms as PW                                 # noqa: PLC0415
    n, dec, k, nf = _counts(sub)
    return (PW._slice_line(name, sub)
            + f"   ⟵ خام: ن={n} محسومة={dec} فائزة={k} no_fill={nf}")


def report(rows, n_syms, year, issues) -> int:
    import press_backtest as PB                                  # noqa: PLC0415
    import press_wake_arms as PW                                 # noqa: PLC0415
    _log(f"\n{'—' * 74}\n🔥 T-FUSE سنة {year} — رموز {n_syms} · "
         f"حلقات {len(rows)} · r_win={PB.r_win_value():.4f}")
    if not rows:
        _log("⛔ `FV1`: صفرُ حلقات (بصمة الـno-op) ⇒ خروج 4.")
        return 4
    cells = {c: [e for e in rows if e["cell"] == c]
             for c in ("F1", "F2", "F3", "F4")}
    out_of = [e for e in rows if e["cell"] is None]
    _log(f"🧮 خارج الخلايا: {len(out_of)} (‏`FV3` — يُطبع ولو صفرًا)")
    if not cells[GOV_CELL]:
        _log(f"⛔ `FV1`: الخليّةُ الحاكمة {GOV_CELL} فارغة ⇒ خروج 4.")
        return 4
    _log(_cline("F-ALL (كل الحلقات)", rows))
    h3 = [e for e in rows if e["hold"] >= 3]
    _log(_cline("F-H3 (مِرساة §⑬)", h3))
    _log(_cline("🔥 F1 الفتيل (كُنس·طازج)", cells["F1"]))
    _log(_cline("F2 (كُنس·عاد فحفظ)", cells["F2"]))
    _log(_cline("F3 (طازجٌ بلا بنية)", cells["F3"]))
    _log(_cline("F4 (جلوسٌ هادئ)", cells["F4"]))
    comp = [e for e in rows if e["cell"] != GOV_CELL]
    _log(_cline("F̄1 (المُكمِّل)", comp))
    _log("\n🔬 استكشافيّات §③ (تُنشَر ولا تحكم):")
    for base_name, base in (("F1", cells["F1"]), ("F-H3", h3)):
        _log(f"  — داخل {base_name}:")
        _log(_cline(f"    عمرُ الهبوط ≥{AGE_MIN} («رزق لم يكتب»)",
                    [e for e in base if e["age"] >= AGE_MIN]))
        _log(_cline(f"    عمرُ الهبوط أقل من {AGE_MIN}",
                    [e for e in base if e["age"] < AGE_MIN]))
        _log(_cline("    شمعةٌ انعكاسية يومَ القراءة",
                    [e for e in base if e.get("rev")]))
        _log(_cline("    قفزةُ حجمٍ يومَ القراءة",
                    [e for e in base if e.get("vol")]))
        _log(_cline("    مستوى مُختبَر حاضر",
                    [e for e in base if e.get("tl")]))
        _log(_cline("    مستوى مُختبَر غائب",
                    [e for e in base if not e.get("tl")]))
    _n, _d, _k, _ = _counts(h3)
    _log(f"\n🔗 مِرساةُ §⑬ السنوية: H3 محسومة={_d} · فائزة={_k} — "
         f"المجموعُ عبر الثلاث يجب أن يعيد {PUB13['decided']} · "
         f"{PUB13['win_pct']}% · +{PUB13['ev']}R")
    if issues:
        _log(f"🩺 حلقاتٌ لم تُثرَ (بأسبابها — `FV3`): {issues}")
    _log("\n⚠️ حدود §⑧: «بلغ الهدف» لمسٌ لا تنفيذ · E بخطّة المرآة لا ربحيةَ"
         " البوت · بلا افتر · w=40 حصرًا · والاستكشافياتُ لا تُرقّى إلا"
         " بكامل معايير §④.")
    return 0


def main() -> int:
    import Super_stock as S                                      # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    year = (os.environ.get("BACKTEST_YEAR") or "").strip()
    path = os.environ.get("BT_FROZEN_PATH") or "frozen_backtest.pkl.gz"
    _log(f"\n{'=' * 78}\n🔥🩸 T-FUSE — سنة {year} · الحاكمة {GOV_CELL} "
         f"(‏swept و hold ≤ {FRESH_MAX}) · لقطة={path}\n{'=' * 78}")
    if not year:
        _log("⛔ `BACKTEST_YEAR` غائب ⇒ خروج 2.")
        return 2
    if not os.path.exists(path):
        _log(f"⛔ اللقطةُ المجمَّدة مفقودة ({path!r}) ⇒ خروج 2.")
        return 2
    hist, _sp, asof = S.load_frozen_dataset(path)
    if not hist:
        _log("⛔ لقطةٌ فارغة ⇒ خروج 2.")
        return 2
    _log(f"📦 لقطة as-of {asof} · رموز {len(hist)}")
    rows, n_syms, issues = [], 0, {}
    for sym, df in hist.items():
        if df is None or len(df) < RB.MIN_BARS + 5:
            continue
        n_syms += 1
        r, iss = walk(sym, df, year)
        rows.extend(r)
        for k, v in iss.items():
            issues[k] = issues.get(k, 0) + v
        if n_syms % 400 == 0:
            _log(f"  … مشى {n_syms} رمزًا · حلقات {len(rows)}")
    if issues.get("fatal"):
        _log(f"⛔ `FV0`-أ: تفرّقٌ بين الحلقة و`press_read` عند فهرسها "
             f"({issues}) ⇒ **عطبُ أداةٍ لا نتيجة** ⇒ خروج 3.")
        return 3
    try:
        with open(OUT_ROWS, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False,
                                   default=str) + "\n")
        _log(f"💾 {OUT_ROWS}: {len(rows)} صفًّا")
    except Exception as _e:                                      # noqa: BLE001
        _log(f"⚠️ تعذّر حفظُ الصفوف: {type(_e).__name__}")
    return report(rows, n_syms, year, issues)


if __name__ == "__main__":
    sys.exit(main())
