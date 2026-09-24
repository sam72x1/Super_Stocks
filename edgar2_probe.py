#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔬📰② `T-PRE-EDGAR-2` — **المرحلة صفر v2: جدوى المصدر ‏+ حسمُ منطقة التوقيت**.

العقد: `edgar2_prereg.md` **مدموجٌ قبل هذا الملفّ** (‏`e6068f58`) — §③ يحدّد `F1` · `F2` ·
`F3` · `F4′` · `F5` · و§④ يحدّد `TZ-P` · `TZ0`-`TZ3` — ولا يُخفَّض حدٌّ منها بعد رؤية رقمه.

🔒 **سقفُ النجاح صفر:** لا `CASE` ولا `CTRL` ولا `EG1`/`EG2` ولا نسبةُ إصابة — تُجيب سؤالين:
   **هل المصدرُ صالحٌ للقياس؟ وبأيّ منطقةِ توقيتٍ تُقرأ `acceptanceDateTime`؟**
🔒 **قراءةٌ فقط** (‏`V-E6`): صفرُ إرسالٍ · صفرُ كتابةِ حالة · صفرُ مسٍّ بعتبةٍ إنتاجية.
🔒 **`V-E7`:** `sec_recent_filings` لا تُنادى إطلاقًا (قصُّها 75 يومًا يُعميها عن 2025).
🔒 **`V-E12`:** اسمُ حقل تاريخ الإيداع لا يَرِد إلّا داخل **`tz_verdict`** — للتحقّق من منطقة
   التوقيت بقاعدة 17:30 وحدَها، **ولا يدخل قرارَ نافذةٍ إطلاقًا** (‏`V-E3` حرفيًّا).

🔁 **إعادةُ الاستعمال بالاسم (بُنيت لـ…):** `sample_symbols` · `recent_depth` ·
   `load_year_symbols` · `sec_get` **بُنيت للمرحلة صفر الأولى** (‏`edgar_probe.py`) للعيّنة
   والعمق والجلب ذواتِها — والعقدُ §③ يُبقي العيّنةَ نفسَها و`F2`/`F3` حرفيًّا ⇒ **الغرضُ
   واحدٌ لا مُستورَد**. و`sec_get` محاولةٌ واحدة بلا إعادة — عينُ ما يشترطه §③ للمرحلة صفر.

⚖️ **التفسيران (§④-أ):** `A` = الأرقامُ ساعةُ نيويورك واللاحقةُ وسمٌ لا يُعتدّ به ·
   `B` = اللاحقةُ صادقة (‏`Z` = UTC أو إزاحةٌ صريحة) وتُحوَّل إلى نيويورك بـ`zoneinfo`.
   **والحَكَمُ مستقلٌّ عنهما** (§④-ب): تاريخُ الإيداع = يومُ القبول إن قُبل حتى 17:30
   نيويورك، وإلّا يومُ عملٍ لاحق · وساعاتُ EDGAR 06:00-22:00 أيّامَ العمل.
"""

from __future__ import annotations

import datetime as dt
import os
import re
import sys
import time
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import Super_stock as S  # noqa: E402
from edgar_probe import (  # noqa: E402
    DEPTH_DAY, F1_MIN_PCT, F2_MIN_PCT, F3_MIN_PCT, SAMPLE_N, SAMPLE_SALT, SUB_URL, YEAR,
    load_year_symbols, recent_depth, sample_symbols, sec_get,
)

# ---- ثوابتُ العقد (كلُّ رقمٍ مُسنَدٌ لقسمه في `edgar2_prereg.md`) ----
SHIPPED_SLEEP = 0.15          # §③ F4′ — الكادنس المشحون (form4_insider_buys · enrich · _offering_event)
F4P_MIN_OK_PCT = 95.0         # §③ F4′ — الردودُ الناجحة ‏≥ 95% من النداءات
FORMS = ("8-K", "8-K/A", "424B1", "424B2", "424B3", "424B4", "424B5", "424B7",
         "S-1", "S-1/A", "S-3", "S-3/A")            # §② حرفيًّا — مطابقةٌ تامّة
TZ_LO, TZ_HI = "2024-12-01", "2026-01-31"           # §④-ج مدى عيّنة التوقيت
TZ_N_MIN = 100                # §④-ج TZ0
TZ1_MIN_PCT = 98.0            # §④-ج TZ1
TZ2_D_MIN = 30                # §④-ج TZ2
TZ2_MIN_PCT = 95.0            # §④-ج TZ2
TZ3_MAX_PCT = 1.0             # §④-ج TZ3
RULE_CUT = dt.time(17, 30, 0)                       # §④-ب قاعدة 17:30
EDGAR_OPEN, EDGAR_CLOSE = dt.time(6, 0, 0), dt.time(22, 0, 0)   # §④-ب ساعاتُ EDGAR
NY = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
# §④-ج TZ-P: YYYY-MM-DDTHH:MM:SS[.ffffff][Z أو ±HH:MM] — والإزاحةُ بلا نقطتين مقبولةٌ أيضًا
ACC_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})"
                    r"(?:\.(\d{1,6}))?(Z|[+-]\d{2}:?\d{2})?$")


def log(msg: str) -> None:
    print(msg, flush=True)


# ---- دوالٌّ نقيّة: قراءةُ الطابع وتفسيراه ----
def parse_acc(s):
    """نصُّ `acceptanceDateTime` ⟵ (‏لحظةٌ بلا منطقة، اللاحقة) أو `None` إن خالف النمط.

    🔒 **لا يُفسّر اللاحقة** — التفسيرُ في `to_ny` وحدَها بالتفسير المُسمّى، فلا يقرأ
       أحدٌ `Z` ضمنًا (المُحلِّلُ الساذج يقرؤها UTC — §④-أ).
    """
    m = ACC_RE.match(str(s or "").strip())
    if not m:
        return None
    y, mo, d, h, mi, se, frac, suf = m.groups()
    try:
        naive = dt.datetime(int(y), int(mo), int(d), int(h), int(mi), int(se),
                            int((frac or "0").ljust(6, "0")))
    except ValueError:
        return None
    return naive, suf


def to_ny(parsed, interp: str):
    """لحظةٌ بتوقيت نيويورك بالتفسير المُسمّى (‏`"A"` أو `"B"`) — §④-أ.

    `A`: الأرقامُ ساعةُ نيويورك الجداريّة (‏`fold=0` — EDGAR مغلقٌ في ساعة التبديل).
    `B`: اللاحقةُ صادقة: `Z` أو غيابُها = UTC · وإزاحةٌ صريحة كما هي ⟵ نيويورك.
    """
    naive, suf = parsed
    if interp == "A":
        return naive.replace(tzinfo=NY)
    if interp != "B":
        raise ValueError(f"تفسيرٌ مجهول: {interp!r}")
    if suf in (None, "Z"):
        tz = UTC
    else:
        sign = 1 if suf[0] == "+" else -1
        digits = suf[1:].replace(":", "")
        tz = dt.timezone(sign * dt.timedelta(hours=int(digits[:2]), minutes=int(digits[2:])))
    return naive.replace(tzinfo=tz).astimezone(NY)


def rule_ok(fdate: str, t) -> bool:
    """قاعدةُ 17:30 (§④-ب): قُبل حتى 17:30:00 نيويورك ⇒ تاريخُ الإيداع يومُه ·
    بعدها ⇒ تاريخٌ **لاحق** (لا يُحسَب يومُ العمل التالي بعينه — يكفي «لاحق»)."""
    day = t.date().isoformat()
    if t.timetz().replace(tzinfo=None) <= RULE_CUT:
        return fdate == day
    return fdate > day


def in_edgar_hours(t) -> bool:
    """داخلَ ساعات EDGAR: يومُ عمل (الاثنين-الجمعة) و06:00:00 ‏≤ الوقت ‏≤ 22:00:00 نيويورك."""
    if t.weekday() >= 5:
        return False
    tod = t.timetz().replace(tzinfo=None)
    return EDGAR_OPEN <= tod <= EDGAR_CLOSE


def tz_verdict(recents) -> dict:
    """§④-ج كاملًا على قوائمَ بشكل `filings.recent` (مصفوفاتٌ متوازية) ⟵ قاموسُ الحكم.

    🔒 **الموضعُ الوحيد الذي يُقرأ فيه تاريخُ الإيداع** (‏`V-E12`) — وللتحقّق وحدَه:
       اختيارُ عيّنة التوقيت بمداه ‏[TZ_LO ، TZ_HI] ثم الحَكَمُ بقاعدة 17:30.
    """
    rows, bad, bad_ex, suffixes = [], 0, [], {}
    for rec in recents:
        rec = rec or {}
        forms = rec.get("form") or []
        fdates = rec.get("filingDate") or []
        accs = rec.get("acceptanceDateTime") or []
        for i, form in enumerate(forms):
            if form not in FORMS:
                continue
            fd = str(fdates[i]) if i < len(fdates) else ""
            if not (TZ_LO <= fd <= TZ_HI):
                continue
            raw = accs[i] if i < len(accs) else None
            p = parse_acc(raw)
            if p is None:
                bad += 1
                if len(bad_ex) < 3:
                    bad_ex.append(repr(raw))
                continue
            suffixes[p[1] or "∅"] = suffixes.get(p[1] or "∅", 0) + 1
            rows.append((fd, p, form, str(raw)))
    n = len(rows)
    out = {"n": n, "bad": bad, "bad_ex": bad_ex, "suffixes": suffixes,
           "winner": None, "gates": {}, "ok": False, "reason": ""}
    out["gates"]["TZ-P"] = (bad == 0)
    out["gates"]["TZ0"] = (n >= TZ_N_MIN)
    if not out["gates"]["TZ-P"]:
        out["reason"] = f"TZ-P: {bad} قيمةً تخالف النمط"
        return out
    if not out["gates"]["TZ0"]:
        out["reason"] = f"TZ0: العيّنة {n} دون {TZ_N_MIN}"
        return out
    ta = [to_ny(p, "A") for _, p, _, _ in rows]
    tb = [to_ny(p, "B") for _, p, _, _ in rows]
    ok_a = [rule_ok(fd, t) for (fd, _, _, _), t in zip(rows, ta)]
    ok_b = [rule_ok(fd, t) for (fd, _, _, _), t in zip(rows, tb)]
    same = all(a == b for a, b in zip(ta, tb))
    d_idx = [i for i in range(n) if ok_a[i] != ok_b[i]]
    a_on_d = sum(1 for i in d_idx if ok_a[i])
    b_on_d = len(d_idx) - a_on_d
    out.update({"same": same, "D": len(d_idx), "A_on_D": a_on_d, "B_on_D": b_on_d,
                "cons_A": 100.0 * sum(ok_a) / n, "cons_B": 100.0 * sum(ok_b) / n,
                "out_A": 100.0 * sum(1 for t in ta if not in_edgar_hours(t)) / n,
                "out_B": 100.0 * sum(1 for t in tb if not in_edgar_hours(t)) / n})
    if same:
        winner, tz2, share = "A", True, 100.0          # لا التباس: الصيغةُ تحمل إزاحتَها
    else:
        winner = "A" if a_on_d > b_on_d else ("B" if b_on_d > a_on_d else None)
        share = (100.0 * max(a_on_d, b_on_d) / len(d_idx)) if d_idx else 0.0
        tz2 = winner is not None and len(d_idx) >= TZ2_D_MIN and share >= TZ2_MIN_PCT
    out["share_D"] = share
    out["winner"] = winner
    out["gates"]["TZ2"] = tz2
    cons_w = out["cons_A"] if winner != "B" else out["cons_B"]
    out_w = out["out_A"] if winner != "B" else out["out_B"]
    out["gates"]["TZ1"] = winner is not None and cons_w >= TZ1_MIN_PCT
    out["gates"]["TZ3"] = winner is not None and out_w <= TZ3_MAX_PCT
    out["examples"] = [(rows[i][3], rows[i][0], rows[i][2]) for i in d_idx[:5]]
    for g in ("TZ2", "TZ1", "TZ3"):
        if not out["gates"][g]:
            out["reason"] = f"{g} سقط"
            return out
    out["ok"] = True
    return out


# ---- المرحلة صفر كاملةً (تُنادى من هنا ومن أداة الدراسة: V-E0 منفَّذةٌ في التشغيلة) ----
def stage0(syms, cmap, get=None, sleep=None, say=log) -> dict:
    """§③ + §④ على العيّنة الحتميّة ⟵ `{"exit", "gate", "winner", ...}`.

    `get`/`sleep` **محقونان للاختبار** (نمطُ `fetch_hist` القائم) — والافتراضُ وقتَ النداء
    `sec_get` و`time.sleep` فلا يُثبَّت أصلٌ عند الاستيراد.
    """
    get = get or sec_get
    sleep = sleep or time.sleep
    res = {"exit": 5, "gate": None, "winner": None}
    sample = sample_symbols(syms)
    res["sample"] = sample
    say(f"🎲 العيّنةُ الحتميّة: {len(sample)} رمزًا (أوّلُها {', '.join(sample[:5])} …)")
    if not sample:
        res["gate"] = "input"
        return res

    have = [s for s in sample if s in cmap]
    miss = [s for s in sample if s not in cmap]
    f1 = 100.0 * len(have) / len(sample)
    f5 = 100.0 * len(miss) / len(sample)
    res.update({"F1": f1, "F5": f5})
    say(f"🚪 F1 تغطيةُ CIK: {len(have)}/{len(sample)} = {f1:.1f}% (الحدّ {F1_MIN_PCT:.0f}%)")
    say(f"📏 F5 الغائبون اليوم عن الخريطة: {len(miss)}/{len(sample)} = {f5:.1f}% — "
        "بلا حدّ (حدُّ صدقٍ لا عطبُ أداة)")
    if miss:
        say(f"   الغائبون: {', '.join(miss[:20])}" + (" …" if len(miss) > 20 else ""))
    if f1 < F1_MIN_PCT:
        res["gate"] = "F1"
        say("⛔ F1 سقط ⇒ غيرُ قابلةٍ للقياس — تغطيةٌ ناقصة (خروج 5).")
        return res

    say(f"🌐 {len(have)} نداءً متتاليًا لـ`submissions` بكبح {SHIPPED_SLEEP:.2f}ث "
        "(الكادنس المشحون — F4′) · محاولةٌ واحدةٌ لكلّ نداء")
    ok, blocks, net_errs, other = 0, 0, 0, 0
    has_acc, deep_recent, deep_files = 0, 0, 0
    recents, net_total, lat = [], 0.0, []
    t0 = time.monotonic()
    for i, sym in enumerate(have):
        if i:
            sleep(SHIPPED_SLEEP)
        st, sub, dt_ = get(SUB_URL.format(int(cmap[sym])))
        net_total += dt_
        lat.append(dt_)
        if st in (403, 429):
            blocks += 1
            continue
        if st == -1:
            net_errs += 1
            continue
        if st != 200 or not sub:
            other += 1
            continue
        ok += 1
        rec = (sub.get("filings") or {}).get("recent") or {}
        if "acceptanceDateTime" in rec:
            has_acc += 1
        recents.append(rec)
        oldest, covered = recent_depth(sub)
        if oldest and oldest <= DEPTH_DAY:
            deep_recent += 1
        elif covered:
            deep_files += 1
    elapsed = time.monotonic() - t0
    n_calls = len(have)
    rate = (n_calls / elapsed) if elapsed > 0 else 0.0
    ok_pct = 100.0 * ok / n_calls if n_calls else 0.0
    med = sorted(lat)[len(lat) // 2] if lat else 0.0
    res.update({"calls": n_calls, "ok": ok, "blocks": blocks, "rate": rate, "ok_pct": ok_pct})
    say(f"   📨 نجح {ok} · حُجب {blocks} (403/429) · عطلُ شبكة {net_errs} · أخرى {other}")
    say(f"🚪 F4′: حجبٌ {blocks} (الحدّ صفر) · نجاحٌ {ok_pct:.1f}% (الحدّ {F4P_MIN_OK_PCT:.0f}%) · "
        f"المعدّل {rate:.2f}/ث **بلا حدّ** · شبكةٌ {net_total:.2f}ث (وسيطُ النداء "
        f"{med * 1000:.0f}ms)")
    if blocks:
        res["gate"] = "F4′"
        say(f"⛔ F4′ سقط — حجبٌ فعليّ ({blocks}) بالكادنس المشحون ⇒ غيرُ قابلةٍ للقياس (خروج 5).")
        return res
    if ok_pct < F4P_MIN_OK_PCT:
        res["gate"] = "F4′"
        say(f"⛔ F4′ سقط — النجاحُ {ok_pct:.1f}% دون {F4P_MIN_OK_PCT:.0f}% ⇒ غيرُ قابلةٍ "
            "للقياس (خروج 5).")
        return res
    say("✅ F4′ عبر.")

    f2 = 100.0 * has_acc / ok
    res["F2"] = f2
    say(f"🚪 F2 حضورُ acceptanceDateTime: {has_acc}/{ok} = {f2:.1f}% (الحدّ {F2_MIN_PCT:.0f}%)")
    if f2 < F2_MIN_PCT:
        res["gate"] = "F2"
        say("⛔ F2 سقط ⇒ غيرُ قابلةٍ للقياس (خروج 5).")
        return res
    deep = deep_recent + deep_files
    f3 = 100.0 * deep / ok
    res["F3"] = f3
    say(f"🚪 F3 العمقُ إلى {DEPTH_DAY}: {deep}/{ok} = {f3:.1f}% (الحدّ {F3_MIN_PCT:.0f}%) — "
        f"recent {deep_recent} · files[] {deep_files}")
    if f3 < F3_MIN_PCT:
        res["gate"] = "F3"
        say("⛔ F3 سقط ⇒ غيرُ قابلةٍ للقياس — عمقٌ ناقص (خروج 5).")
        return res
    say("✅ F2 · F3 عبرتا.")

    tz = tz_verdict(recents)
    res["tz"] = tz
    say_tz(tz, say)
    if not tz["ok"]:
        res["gate"] = "TZ"
        say(f"⛔ منطقةُ التوقيت لم تُحسَم ({tz['reason']}) ⇒ غيرُ قابلةٍ للقياس (خروج 5).")
        return res
    res.update({"exit": 0, "gate": None, "winner": tz["winner"]})
    return res


def say_tz(tz: dict, say=log) -> None:
    """طباعةُ حكم التوقيت كاملًا — الأرقامُ عن **الصيغة** لا عن الدراسة."""
    say(f"🕰️ عيّنةُ التوقيت: {tz['n']} إيداعًا من FORMS بتاريخ إيداعٍ في [{TZ_LO} ، {TZ_HI}] · "
        f"مخالفو النمط {tz['bad']} {tz.get('bad_ex') or ''} · اللواحق {tz.get('suffixes')}")
    if "cons_A" not in tz:
        return
    say(f"   قاعدةُ 17:30: اتّساقُ A {tz['cons_A']:.2f}% · اتّساقُ B {tz['cons_B']:.2f}% · "
        f"|D| = {tz['D']} (A صائبٌ في {tz['A_on_D']} · B في {tz['B_on_D']}) · "
        f"A≡B = {tz['same']}")
    say(f"   خارجَ ساعات EDGAR: A {tz['out_A']:.2f}% · B {tz['out_B']:.2f}%")
    say(f"   🏁 الفائز {tz['winner']} · حصّتُه على D {tz.get('share_D', 0.0):.1f}% · البوّابات "
        + " · ".join(f"{k} {'✅' if v else '⛔'}" for k, v in tz["gates"].items()))
    for raw, fd, form in tz.get("examples") or []:
        say(f"   مثالٌ من D: {form} · قبول {raw} · تاريخُ الإيداع {fd}")


def main() -> int:
    log("=" * 78)
    log("🔬📰② T-PRE-EDGAR-2 — المرحلة صفر v2: جدوى المصدر + حسمُ منطقة التوقيت")
    log(f"   العقد: edgar2_prereg.md §③/§④ · العيّنة: أدنى {SAMPLE_N} بـsha256"
        f"('{SAMPLE_SALT}' + رمز) · السنة: {YEAR}")
    log("   🔒 سقفُ النجاح **صفر** — لا رقمَ دراسةٍ ولا EG1/EG2.")
    log("=" * 78)
    contact = (os.environ.get("SEC_CONTACT") or "").strip()
    if not contact:
        log("⛔ SEC_CONTACT غيرُ مضبوط ⇒ عطبُ إعدادٍ لا حكمٌ على المصدر (خروج 2).")
        log("STAGE0 pass=0 gate=V-E8 exit=2")
        return 2
    log(f"✅ SEC_CONTACT مضبوط ({len(contact)} محرفًا — لا تُطبَع قيمتُه).")
    syms, n_files, n_rows, n_year = load_year_symbols()
    log(f"📦 صفوفُ E1: {n_files} ملفًّا · {n_rows} صفًّا · منها {n_year} من {YEAR} ⇒ "
        f"{len(syms)} رمزًا فريدًا")
    if not syms:
        log("⛔ صفرُ رمزٍ من السنة — لا مدخلات (خروج 2).")
        log("STAGE0 pass=0 gate=input exit=2")
        return 2
    cmap = S.sec_cik_map()
    if not cmap:
        log("⛔ خريطةُ SEC فارغة — تعذّر الجلب (خروج 5).")
        log("STAGE0 pass=0 gate=cmap exit=5")
        return 5
    log(f"🗺️ خريطةُ SEC: {len(cmap)} رمزًا")
    res = stage0(syms, cmap)
    tz = res.get("tz") or {}
    log("=" * 78)
    if res["exit"] == 0:
        log("⚖️ **المرحلةُ صفر v2 عبَرت** — F1 · F4′ · F2 · F3 · TZ كلُّها فوق حدودها.")
    log("🔒 سقفُ النجاح صفر: لا `CASE`/`CTRL` ولا رقمَ دراسة من هذا المِجَسّ.")
    log(f"STAGE0 pass={int(res['exit'] == 0)} gate={res.get('gate') or '-'} "
        f"F1={res.get('F1', 0):.1f} F5={res.get('F5', 0):.1f} F2={res.get('F2', 0):.1f} "
        f"F3={res.get('F3', 0):.1f} ok={res.get('ok_pct', 0):.1f} blocks={res.get('blocks', '-')} "
        f"rate={res.get('rate', 0):.2f} TZ={tz.get('winner') or '-'} "
        f"n_tz={tz.get('n', 0)} D={tz.get('D', 0)} exit={res['exit']}")
    return res["exit"]


if __name__ == "__main__":
    sys.exit(main())
