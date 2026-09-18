# -*- coding: utf-8 -*-
"""📅💲 **التأريخُ بمرساة السعر** — يُؤرّخ شارتاتِ فيصل القديمةَ (غيرَ الموجودة على
القرص ⇒ لا EXIF) من **السعر المسجَّل عليها** في الكاتالوج («AH 1.620» · «Pre 6.05» ·
«3.105 (+32.13%)»).

**قراءةٌ فقط:** لا حالة · لا تلغرام · لا سرّ. يكتب `faisal_price_anchor_dates.tsv`
**منفصلًا** عن جدول المستويات — التاريخُ هنا **مُشتقٌّ من سعرٍ مسجَّل** لا من رقم
الصورة، ويُقبَل **فقط** إن كان يومُ التداول الذي يطابقه **وحيدًا** في النافذة.

القواعد الثابتة قبل أيّ رقم:
  • السعرُ يُقرأ من **قسم الرمز نفسِه** (سطرُ الصورة أو ما فوقه حتى رأس القسم `###`)
    ولا يُقبَل سطرٌ إلّا إذا ذُكر رمزُ السهم فيه أو في رأس قسمه (‏درسُ BNKK/HCAI:
    كتلةُ الجار تلوّث).
  • **ثلاثةُ أنواعٍ من المرساة**، وكلُّها تستعمل نسبةَ التغيّر المسجَّلة قيدًا ثانيًا:
      `ah`   «AH 4.500 (+0.67%)»  ⇒ إغلاقُ اليوم النظاميّ = 4.500 ÷ 1.0067 (قيدٌ دقيق)
      `pre`  «Pre 13.16 (+22.28%)» ⇒ إغلاقُ **الأمس** = 13.16 ÷ 1.2228 · وتاريخُ الشارت
             هو يومُ التداول التالي
      `spot` «3.105 (+32.13%)»     ⇒ إغلاقُ الأمس = 3.105 ÷ 1.3213 **و**السعرُ داخل
             مدى اليوم [أدنى، أعلى] (لقطةٌ أثناء الجلسة لا تساوي الإغلاق بالضرورة)
  • التسامح **‏0.75%** على الإغلاق المُشتقّ (الأرقامُ المسجَّلة بثلاث خانات) · **‏1%**
    سماحيةً على حدود المدى.
  • **تسويةُ التقسيم:** بياناتُ ياهو معدَّلةٌ بالتقسيمات اللاحقة، فالسعرُ المسجَّل يُحوَّل
    لمقياس اليوم بقسمته على `_split_scale_factor(splits, d)` (فاشلة-آمنة ⟶ 1.0).
  • النافذة **‏2025-01-01 ⟶ 2026-08-31** (المخزونُ القديم كلُّه قبل دفعة يوليو 2026
    وعمرُ الشارتات القديمة مجهول ⇒ نافذةٌ واسعةٌ والقيدُ الثاني يعوّضها).
  • الحكم: `unique` (يومٌ واحدٌ يطابق) · `ambiguous` (أكثر) · `none` (صفر) ·
    `no_price` (لا مرساةَ في القسم) · `no_data` (مرساةٌ بلا تاريخٍ عند ياهو).
  • **وصفيٌّ لا حاكم (أُضيف بعد أوّل تشغيلة `35405360466` ولا يغيّر عمود الحكم):** أعمدةُ
    `tight_*` تُعيد الحكمَ بتسامحٍ **‏0.10%** (المراسي ذاتُ النسبة مطابقاتُها الوحيدة جاءت
    كلُّها دون ‏0.005%) — تُطبَع لتُسجَّل مسبقًا في أيّ ملحقٍ يستعمل التواريخ، **ولا تُؤرِّخ
    بنفسها**؛ ومعها سطرُ حساسيّة `SENS` لثلاثة تسامحات.
"""
import csv
import datetime as dt
import re
import sys

import Super_stock as bot

CAT = "FAISAL_IMAGES_CATALOG.md"
TOL = 0.75          # % على الإغلاق المُشتقّ
RANGE_SLACK = 1.0   # % سماحية على حدود مدى اليوم (spot)
W0, W1 = "2025-01-01", "2026-08-31"
TOL_LOOSE = 1.5     # % لمرساةٍ بلا نسبةٍ مسجَّلة (AH/Pre عاريًا — قيدٌ واحدٌ رخو)
TOL_TIGHT = 0.10    # % وصفيٌّ فقط (أعمدة tight_* وسطر SENS) — لا يمسّ عمود الحكم
SENS_TOLS = (0.75, 0.25, 0.10)
RE_ANY = re.compile(
    r"(?:(AH|After Hours|Pre-market|Premarket|Pre|بريماركت)\b[^0-9%+\-‑−]{0,10})?"
    r"(?<![\d.])(\d+\.\d+)(?:\s*\(([+‑\-−])(\d+\.\d+)%\))?", re.I)


def log(m): print(m, flush=True)


# ═══════════════ ① دوالُّ نقيّة (قابلةٌ للاختبار بلا شبكة) ════════════════════
def parse_anchors(line: str) -> list:
    """كلُّ مراسي السطر: `{kind, px, pct}` — `kind` ∈ {ah, pre, spot}."""
    out = []
    for m in RE_ANY.finditer(line):
        pre = (m.group(1) or "").lower()
        has_pct = m.group(4) is not None
        if not pre and not has_pct:          # رقمٌ عارٍ (مستوًى/مؤشّر) — ليس مرساة
            continue
        kind = "spot" if not pre else ("pre" if pre.startswith("pre") or pre == "بريماركت" else "ah")
        pct = None
        if has_pct:
            pct = (-1.0 if m.group(3) in "‑-−" else 1.0) * float(m.group(4))
        out.append({"kind": kind, "px": float(m.group(2)), "pct": pct})
    return out


def implied_close(a: dict) -> float:
    """الإغلاقُ الذي تُشتقّ منه النسبة: `px ÷ (1 + pct/100)`."""
    return a["px"] if a.get("pct") is None else a["px"] / (1.0 + a["pct"] / 100.0)


def match_days(bars: list, a: dict, splits=None, w0: str = W0, w1: str = W1,
               tol: float = TOL, slack: float = RANGE_SLACK) -> list:
    """`bars` = [(date_iso, low, high, close), …] مرتّبةً · يُعيد المرشّحين
    `{date, match_date, close, diff_pct}` — `date` = تاريخُ الشارت (ليوم `pre` هو يومُ
    التداول التالي لليوم المطابَق). **صفرُ نظرٍ مستقبليّ**: كلُّ قيدٍ من نفس اليوم أو أمسِه."""
    c_ref = implied_close(a)
    if a.get("pct") is None:                 # مرساةٌ رخوة: قيدٌ واحدٌ بتسامحٍ أوسع
        tol = max(tol, TOL_LOOSE)
    out = []
    for i, (d, lo, hi, cl) in enumerate(bars):
        if not (w0 <= d <= w1) or not cl or cl <= 0:
            continue
        f = bot._split_scale_factor(splits, d) if splits is not None else 1.0
        ref = c_ref / f                         # مقياسُ اليوم (بعد التقسيمات اللاحقة)
        if a["kind"] == "ah":
            diff = abs(cl - ref) / ref * 100.0
            ok = diff <= tol
            chart_d, close_d, match_cl = d, d, cl
        elif a["kind"] == "pre":
            diff = abs(cl - ref) / ref * 100.0
            ok = diff <= tol
            chart_d, close_d, match_cl = (bars[i + 1][0] if i + 1 < len(bars) else d + "+1"), d, cl
        else:                                   # spot: إغلاقُ الأمس + داخلَ مدى اليوم
            if i == 0:
                continue
            pd_, plo, phi, pcl = bars[i - 1]
            if not pcl or pcl <= 0:
                continue
            fp = bot._split_scale_factor(splits, pd_) if splits is not None else 1.0
            px_today = a["px"] / f
            diff = abs(pcl - c_ref / fp) / (c_ref / fp) * 100.0
            ok = (diff <= tol and bool(lo) and bool(hi)
                  and lo * (1 - slack / 100.0) <= px_today <= hi * (1 + slack / 100.0))
            chart_d, close_d, match_cl = d, pd_, pcl
        if ok:
            out.append({"date": chart_d, "match_date": close_d, "close": round(float(match_cl), 4),
                        "diff_pct": round(diff, 3)})
    return out


# ═══════════════ ② الأهداف من الكاتالوج والجدول ════════════════════
def targets():
    lines = open(CAT, encoding="utf-8").read().splitlines()
    rows = list(csv.DictReader(open("faisal_levels_table.tsv", encoding="utf-8"), delimiter="\t"))
    seen, out = set(), []
    for r in rows:
        if not (r["role"] == "support" and r["frame"] == "daily" and r["auto_chart"] == "0"
                and not r["date"]):
            continue
        key = (r["symbol"], int(r["line"]))
        if key in seen:
            continue
        seen.add(key)
        sym, ln = key
        hdr_i = next((k for k in range(ln - 1, -1, -1)
                      if lines[k].startswith("### ") or lines[k].startswith("## ")), -1)
        in_section = hdr_i >= 0 and sym in lines[hdr_i]
        anchor, a_line = None, None
        for k in range(ln - 1, max(hdr_i - 1, -1), -1):        # من سطر الصورة صعودًا حتى الرأس
            blk = lines[k]
            found = []
            if sym in blk:
                found = parse_anchors(blk)
            elif in_section:
                found = parse_anchors(blk)
            if found:
                anchor, a_line = found[0], k + 1
                break
        out.append({"symbol": sym, "line": ln, "anchor": anchor, "anchor_line": a_line})
    return out


def _bars_of(df) -> list:
    out = []
    try:
        for idx, row in df.iterrows():
            d = idx.date().isoformat() if hasattr(idx, "date") else str(idx)[:10]
            out.append((d, float(row["Low"]), float(row["High"]), float(row["Close"])))
    except Exception:                                             # noqa: BLE001
        return []
    return sorted(out)


def main() -> int:
    log("📅💲 التأريخُ بمرساة السعر (قراءةٌ فقط · v2: ثلاثةُ أنواعٍ · قيدُ النسبة · تسويةُ التقسيم)")
    tg = targets()
    with_px = [t for t in tg if t["anchor"]]
    log(f"   أهداف: {len(tg)} (رمز·سطر) غيرُ مؤرَّخة · منها بمرساةٍ مسجَّلة: {len(with_px)}")
    syms = sorted({t["symbol"] for t in with_px})
    hist = bot.download_history(syms, start_override=W0) if syms else {}
    out, sens = [], {}
    for t in tg:
        sym, ln, a = t["symbol"], t["line"], t["anchor"]
        row = {"symbol": sym, "line": ln, "anchor_line": t["anchor_line"] or "",
               "kind": a["kind"] if a else "", "recorded_px": a["px"] if a else "",
               "pct": a["pct"] if a else "", "implied_close": round(implied_close(a), 4) if a else "",
               "date": "", "match_date": "", "close": "", "diff_pct": "",
               "verdict": "no_price", "candidates": "",
               "tight_verdict": "", "tight_date": "", "n_tight": ""}
        df = (hist or {}).get(sym)
        if a and df is not None and len(df) > 5:
            try:
                splits = bot._fetch_splits(sym)
            except Exception:                                     # noqa: BLE001
                splits = None
            bars = _bars_of(df)
            cands = match_days(bars, a, splits)
            row["candidates"] = " | ".join(f"{c['date']}:{c['close']}({c['diff_pct']}%)" for c in cands)
            if a.get("pct") is not None:                        # الوصفيّ: تسامحٌ ضيّق (لا للرخوة)
                tc = match_days(bars, a, splits, tol=TOL_TIGHT)
                row["n_tight"] = len(tc)
                row["tight_verdict"] = "unique" if len(tc) == 1 else ("ambiguous" if tc else "none")
                row["tight_date"] = tc[0]["date"] if len(tc) == 1 else ""
                sens.setdefault(sym, {})
                for tl in SENS_TOLS:
                    sens[sym][tl] = len(match_days(bars, a, splits, tol=tl))
            if len(cands) == 1:
                row.update(date=cands[0]["date"], match_date=cands[0]["match_date"],
                           close=cands[0]["close"], diff_pct=cands[0]["diff_pct"], verdict="unique")
            elif len(cands) > 1:
                row["verdict"] = "ambiguous"
            else:
                row["verdict"] = "none"
        elif a:
            row["verdict"] = "no_data"
        out.append(row)
    with open("faisal_price_anchor_dates.tsv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()), delimiter="\t"); w.writeheader(); w.writerows(out)
    from collections import Counter
    c = Counter(r["verdict"] for r in out)
    log(f"   الحصيلة: {dict(c)}")
    log("")
    log("   الرمز   سطر   النوع  السعرُ المسجَّل  الإغلاقُ المُشتقّ  الحكم       تاريخُ الشارت  الإغلاق   فرق%")
    for r in out:
        log(f"   {r['symbol']:6s} {r['line']:<5} {r['kind']:<5s} {str(r['recorded_px']):<14s} "
            f"{str(r['implied_close']):<16s} {r['verdict']:<10s} {r['date']:<13s} {str(r['close']):<8s} {r['diff_pct']}")
        if r["verdict"] == "ambiguous":
            log(f"          ⟶ مرشَّحات: {r['candidates']}")
    log("")
    # وصفيّ: كم مرساةً ذاتَ نسبةٍ تصير وحيدةً عند كلّ تسامح (لا يمسّ الحكم أعلاه)
    for tl in SENS_TOLS:
        u = sum(1 for v in sens.values() if v.get(tl) == 1)
        amb = sum(1 for v in sens.values() if (v.get(tl) or 0) > 1)
        log(f"SENS tol={tl}% unique={u} ambiguous={amb} none={len(sens) - u - amb} (مراسٍ ذاتُ نسبة={len(sens)})")
    log(f"JUDGE unique={c['unique']} ambiguous={c['ambiguous']} none={c['none']} "
        f"no_data={c['no_data']} no_price={c['no_price']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
