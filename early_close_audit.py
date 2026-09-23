# -*- coding: utf-8 -*-
"""🗓️🔍 `T-EARLY` — تدقيقُ أثر الإغلاق المبكّر على عائلة `T-PRESESSION`.

العقد: `early_close_prereg.md` (مدفوعٌ قبل أيّ رقم) · أمرُ المالك 2026-09-23 «قس أثر الإغلاق المبكر».

المدخل: مجلّدان من `presession_rows_<سنة>.jsonl.gz`:
  • «القديمة» — المسوحُ الثلاثة المنشورة (`OLD_RUNS` — مثبَّتةٌ بالاسم هنا وفي الـworkflow).
  • «الجديدة» — إعادةُ مسحها بالقناتين مصحَّحتين (التقويمُ + `PRESESSION_CLOSE_CAL=1`).
المُخرَج:
  ① فرقُ الصفوف يومًا يومًا بالمفتاح (`day` · `sess` · `sym`) — وحارسُ الإسناد `V-E2`.
  ② أحكامُ `presession_report.py` **بكود اليوم نفسِه** على القديمة ثمّ الجديدة بثلاثة أوضاع،
     وحارسُ إعادة المنشور `V-E3` على القديمة، والأسطرُ المختلفة وحدَها.

🔒 قراءةٌ فقط: الملفّاتُ المؤقّتة في مجلّدٍ مؤقّتٍ خارج المستودع · صفرُ إرسال · صفرُ حالة ·
   ولا يستوردها الإنتاج. ولا يُرفع علمُ `PRESESSION_AUDIT_NEW_ROWS` إلّا بعد عبور القديمة.
"""
from __future__ import annotations

import difflib
import gzip
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter

import market_calendar as MC

YEARS = ("2023", "2024", "2025")
# 🔒 المسوحُ المنشورة (`presession_result.md §②`) — **الصفوفُ القديمة**. تطابقها الـworkflow.
OLD_RUNS = {"2023": "33724354384", "2024": "33724361819", "2025": "33724367680"}
# 🔒 أيّامُ الإغلاق المبكّر في 2023-2025 بحذافيرها (العقد §⓪ · مصادقةُ `exchange_calendars`).
PINNED_EARLY = ("2023-07-03", "2023-11-24", "2024-07-03", "2024-11-29", "2024-12-24",
                "2025-07-03", "2025-11-28", "2025-12-24")
EARLY_CLOSE_MIN = 13 * 60
# 🔒 نافذتا الضبط (العقد §③ `V-E2`): لا إغلاقَ مبكّرًا قبلهما في مسح سنتهما ولا في بذرته ⇒
#    يجب أن تتطابق صفوفُهما بت-بت بين الذراعين. (بذرةُ 2025 تضمّ 2024-11-29 و12-24 ⇒ لا ضبطَ فيها.)
CONTROL = (("2023-01-01", "2023-06-30"), ("2024-01-01", "2024-07-02"))
KEY_FIELDS = ("day", "sess", "sym")
MODES = (("الافتراضيّ", {}),
         ("التطوير", {"PRESESSION_DEV": "1"}),
         ("السقف", {"PRESESSION_CEIL": "1"}))
AUDIT_FLAG = "PRESESSION_AUDIT_NEW_ROWS"
JUDGE_TIMEOUT_S = 3600
# 🔒 `V-E3` — ما يجب أن يطبعه الحكمُ على الصفوف القديمة بكود اليوم (العقد §③ بأرقامه).
PIN_LINES = (
    ("الافتراضيّ", "‏[PM · نافذة 10د]",
     ("P@10=0.40%", "lift=29.8×", "R@10=11.5%", "إصابات=10 ", "منفجرون=87 ")),
    ("الافتراضيّ", "‏[PM · نافذة الجلسة]",
     ("P@10=2.92%", "lift=21.5×", "R@10=8.3%", "إصابات=73 ")),
    ("الافتراضيّ", "أرضياتٌ مُعايَرةٌ", ("F1=0.69492",)),
    ("التطوير", "**V0**", ("مأخوذ 435 · إصابات 47 · المنشور 435/47",)),
    ("السقف", "**V-C0**", ("إصابات 100 من 878 · المنشور 100/878",)),
)
VERDICT_RE = re.compile(r"‏\[(AH|PM) · نافذة ([^\]]+)\] الحكم: \*\*([^*]+)\*\*")
S0_HEAD_RE = re.compile(r"【(AH|PM) · نافذة ([^·]+) · (\d{4})")
FLOOR_RE = re.compile(r"【PM · المفتاحُ المشحون `([^`]+)`】.*?F1=([0-9.eE+-]+|—)")


def log(m: str = "") -> None:
    print(m, flush=True)


# ── دوالُّ نقيّة ───────────────────────────────────────────────────────────────
def early_days(years=YEARS) -> tuple:
    """أيّامُ الإغلاق المبكّر في `years` **من التقويم** مرتّبةً (`V-E1`)."""
    ys = {str(y) for y in years}
    return tuple(sorted(d for d in MC.EARLY_CLOSES if str(d)[:4] in ys))


def calendar_ok(years=YEARS) -> tuple:
    """`V-E1`: (ok, got) — التقويمُ يعرف الأيّامَ الثمانية بالضبط، وكلُّها 13:00 «early_close»."""
    got = early_days(years)
    ok = got == PINNED_EARLY and all(
        MC.session_info(d).get("session_type") == "early_close"
        and MC.session_info(d).get("close_ny_min") == EARLY_CLOSE_MIN for d in got)
    return ok, got


def in_control(day: str, windows=CONTROL) -> bool:
    return any(a <= str(day) <= b for a, b in windows)


def row_key(r: dict) -> tuple:
    return tuple(r.get(k) for k in KEY_FIELDS)


def iter_days(rows):
    """يجمع صفوفًا **متّصلةً باليوم** ⟵ (يوم، {مفتاح: صفّ}). يومٌ يعود بعد غيره ⇒ `ValueError`
    (الماسحُ يكتب يومًا يومًا بترتيبٍ صاعد — وتفرّقُه يعني ملفًّا غيرَ ما نظنّ)."""
    cur, bucket, seen = None, {}, set()
    for r in rows:
        d = r.get("day")
        if d != cur:
            if cur is not None:
                yield cur, bucket
            if d in seen:
                raise ValueError(f"يومٌ غيرُ متّصل: {d}")
            if cur is not None and d is not None and str(d) < str(cur):
                raise ValueError(f"ترتيبٌ غيرُ صاعد: {cur} ثمّ {d}")
            seen.add(d)
            cur, bucket = d, {}
        k = row_key(r)
        if k in bucket:
            raise ValueError(f"مفتاحٌ مكرّر: {k}")
        bucket[k] = r
    if cur is not None:
        yield cur, bucket


def diff_rows(old: dict, new: dict) -> dict:
    """فرقُ يومٍ واحد: مضافٌ · محذوفٌ · متغيّرٌ · والحقولُ المتغيّرة · وتغيّرُ الوسم (`hit80_*`)."""
    added = [k for k in new if k not in old]
    removed = [k for k in old if k not in new]
    changed, fields, label = 0, Counter(), 0
    for k in old.keys() & new.keys():
        a, b = old[k], new[k]
        if a == b:
            continue
        changed += 1
        ks = {f for f in set(a) | set(b) if a.get(f) != b.get(f)}
        fields.update(ks)
        if any(f.startswith("hit80_") for f in ks):
            label += 1
    return {"added": len(added), "removed": len(removed), "changed": changed,
            "fields": fields, "label": label}


def diff_streams(old_rows, new_rows) -> dict:
    """يمشي الملفّين يومًا يومًا معًا ⟵ {يوم: فرق}. يومٌ في ذراعٍ دون الأخرى = كلُّه مضافٌ/محذوف."""
    out = {}
    it_o, it_n = iter_days(old_rows), iter_days(new_rows)
    o, n = next(it_o, None), next(it_n, None)
    while o is not None or n is not None:
        if n is None or (o is not None and str(o[0]) < str(n[0])):
            out[o[0]] = diff_rows(o[1], {})
            o = next(it_o, None)
        elif o is None or str(n[0]) < str(o[0]):
            out[n[0]] = diff_rows({}, n[1])
            n = next(it_n, None)
        else:
            out[o[0]] = diff_rows(o[1], n[1])
            o, n = next(it_o, None), next(it_n, None)
    return out


def attribution(per_day: dict, windows=CONTROL) -> tuple:
    """`V-E2`: (ok, أيّامُ الضبط التي تفرّقت) — ونافذتا الضبط **يجب أن تحويا أيّامًا** (لا يمرّ الفارغ)."""
    ctrl = [d for d in per_day if in_control(d, windows)]
    bad = [d for d in ctrl if any(per_day[d][k] for k in ("added", "removed", "changed"))]
    return (bool(ctrl) and not bad), bad


def pin_check(outputs: dict) -> list:
    """`V-E3`: كلُّ سطرِ مرساةٍ يُوجَد ويحمل أرقامَه المنشورة — ⟵ قائمةُ الساقط (فارغةٌ = عبر)."""
    bad = []
    for mode, anchor, needles in PIN_LINES:
        lines = [ln for ln in (outputs.get(mode) or "").splitlines() if anchor in ln]
        if not lines:
            bad.append(f"{mode}: لا سطرَ «{anchor}»")
            continue
        if not any(all(nd in ln for nd in needles) for ln in lines):
            bad.append(f"{mode}: «{anchor}» بلا {needles}")
    return bad


def verdicts(text: str) -> dict:
    """{(جلسة، نافذة): الحكم} من أسطر جدول `T-PRESESSION`."""
    return {(m.group(1), m.group(2).strip()): m.group(3).strip()
            for m in VERDICT_RE.finditer(text or "")}


def s0_leaders(text: str) -> dict:
    """{(جلسة، نافذة، سنة): أوّلُ ميزةٍ في جدول `S0`} — لاشتقاق `RANK_BY_SLOT` (العقد §④-ج)."""
    out, cur = {}, None
    for ln in (text or "").splitlines():
        m = S0_HEAD_RE.search(ln)
        if m:
            cur = (m.group(1), m.group(2).strip(), m.group(3))
            continue
        if cur is not None and cur not in out and "إصابات" in ln and "P@10" in ln:
            tok = ln.strip().split()
            if tok:
                out[cur] = tok[0]
            cur = None
    return out


def floor_value(text: str):
    """أرضيةُ `F1` المعايَرة للبريماركت كما طُبعت (خمسُ خاناتٍ معنويّة) — أو `None`."""
    m = FLOOR_RE.search(text or "")
    return m.group(2) if m else None


def text_diff(a: str, b: str) -> list:
    """الأسطرُ المختلفة وحدَها (`-` قديم · `+` جديد) بلا ترويسةٍ ولا سياق."""
    return [ln for ln in difflib.unified_diff((a or "").splitlines(), (b or "").splitlines(),
                                              lineterm="", n=0)
            if ln[:1] in "+-" and not ln.startswith(("+++", "---"))]


# ── الإدخال/الإخراج ────────────────────────────────────────────────────────────
def read_rows(path: str):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln:
                yield json.loads(ln)


def year_file(folder: str, year: str) -> str | None:
    """ملفُّ السنة في مجلّد الذراع (بحثًا متداخلًا — `gh run download` يصنع مجلّداتٍ فرعيّة)."""
    want = f"presession_rows_{year}.jsonl.gz"
    for root, _dirs, files in os.walk(folder):
        if want in files:
            return os.path.join(root, want)
    return None


def run_judge(rows: dict, extra_env: dict, repo: str) -> tuple:
    """`presession_report.py` بكود اليوم على صفوف `rows` {سنة: مسار} — في مجلّدٍ مؤقّت (لا في المستودع)."""
    with tempfile.TemporaryDirectory(prefix="early-judge-") as tmp:
        for y, p in rows.items():
            os.symlink(os.path.abspath(p), os.path.join(tmp, f"presession_rows_{y}.jsonl.gz"))
        env = {k: v for k, v in os.environ.items()
               if not k.startswith("PRESESSION_")}
        env.update(extra_env)
        env["PYTHONPATH"] = repo + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        p = subprocess.run([sys.executable, os.path.join(repo, "presession_report.py")],
                           cwd=tmp, env=env, capture_output=True, text=True,
                           timeout=JUDGE_TIMEOUT_S)
        return p.returncode, p.stdout + p.stderr


def main() -> int:
    repo = os.path.dirname(os.path.abspath(__file__))
    old_dir = (os.environ.get("EARLY_OLD_DIR") or "").strip()
    new_dir = (os.environ.get("EARLY_NEW_DIR") or "").strip()
    log("🗓️🔍 `T-EARLY` — أثرُ الإغلاق المبكّر على عائلة `T-PRESESSION` (العقد early_close_prereg.md)")
    ok1, got = calendar_ok()
    log(f"   🔒 V-E1 التقويم: {', '.join(got) or '—'} ⇒ {ok1}")
    if not ok1:
        log("⛔ V-E1 ساقط — التقويمُ لا يعرف الأيّامَ الثمانية كما ثُبّتت ⇒ خروج 5 (لا حكم).")
        return 5
    if not old_dir or not new_dir:
        log("⛔ EARLY_OLD_DIR/EARLY_NEW_DIR غائبان ⇒ خروج 2 (تهيئة).")
        return 2
    old = {y: year_file(old_dir, y) for y in YEARS}
    new = {y: year_file(new_dir, y) for y in YEARS}
    miss = [f"{arm}:{y}" for arm, m in (("قديم", old), ("جديد", new)) for y, p in m.items() if not p]
    if miss:
        log(f"⛔ ملفّاتٌ غائبة: {miss} ⇒ خروج 4 (لا يُخمَّن).")
        return 4
    log(f"   المسوحُ القديمة: {OLD_RUNS}")

    # ① فرقُ الصفوف (`V-E2`)
    log("\n① فرقُ الصفوف يومًا يومًا — المفتاح (day · sess · sym)")
    per_day, tot = {}, Counter()
    for y in YEARS:
        dd = diff_streams(read_rows(old[y]), read_rows(new[y]))
        per_day.update(dd)
        for v in dd.values():
            tot.update({k: v[k] for k in ("added", "removed", "changed", "label")})
    days_hit = sorted(d for d, v in per_day.items()
                      if v["added"] or v["removed"] or v["changed"])
    fields = Counter()
    for v in per_day.values():
        fields.update(v["fields"])
    log(f"   أيّامٌ مقروءة {len(per_day)} · تفرّق منها {len(days_hit)} · "
        f"مضاف {tot['added']} · محذوف {tot['removed']} · متغيّر {tot['changed']} · "
        f"منها بوسمٍ متغيّر (hit80_*) {tot['label']}")
    log("   الحقولُ الأكثرُ تغيّرًا: " + (" · ".join(f"{f}={n}" for f, n in fields.most_common(12)) or "—"))
    for d in PINNED_EARLY:
        v = per_day.get(d)
        log(f"   {d} (إغلاقٌ مبكّر): " + ("غائب" if v is None else
            f"مضاف {v['added']} · محذوف {v['removed']} · متغيّر {v['changed']} · وسم {v['label']}"))
    ok2, bad2 = attribution(per_day)
    log(f"   🔒 V-E2 نافذتا الضبط {CONTROL}: ⇒ {ok2}" + (f" · تفرّقت: {bad2[:10]}" if bad2 else ""))

    # ② الأحكام — القديمةُ أوّلًا (`V-E3`) ثمّ الجديدة
    log("\n② الأحكام بكود اليوم — الصفوفُ القديمة أوّلًا")
    out_old = {}
    for name, env in MODES:
        rc, txt = run_judge(old, env, repo)
        out_old[name] = txt
        log(f"   [{name}] القديمة: خروج {rc}")
        if rc != 0:
            log("⛔ الحكمُ على الصفوف المنشورة لم يخرج 0 ⇒ لا يُرفع علمُ الصفوف الجديدة · خروج 5.")
            log("\n".join(txt.splitlines()[-40:]))
            return 5
    bad3 = pin_check(out_old)
    log(f"   🔒 V-E3 إعادةُ المنشور: {'✅' if not bad3 else '🔴 ' + ' | '.join(bad3)}")
    out_new, rc_new = {}, {}
    for name, env in MODES:
        rc, txt = run_judge(new, dict(env, **{AUDIT_FLAG: "1"}), repo)
        out_new[name], rc_new[name] = txt, rc
        log(f"   [{name}] الجديدة: خروج {rc}")

    # ③ القراءة — الانقلاباتُ المسجَّلة (العقد §④) ثمّ الفروقُ كلُّها
    log("\n③ العقد §④ — الانقلاباتُ المسجَّلة")
    vo, vn = verdicts(out_old["الافتراضيّ"]), verdicts(out_new["الافتراضيّ"])
    flips = [f"{c}: {vo.get(c)} ⟶ {vn.get(c)}" for c in sorted(set(vo) | set(vn)) if vo.get(c) != vn.get(c)]
    log(f"   (أ) خلايا T-PRESESSION ({len(vo)} قديمة · {len(vn)} جديدة): "
        + (" · ".join(flips) if flips else "صفرُ انقلاب"))
    lo, ln_ = s0_leaders(out_old["الافتراضيّ"]), s0_leaders(out_new["الافتراضيّ"])
    for c in sorted(set(lo) | set(ln_)):
        tag = "" if lo.get(c) == ln_.get(c) else "  ⟵ تغيّر"
        log(f"   (ج) S0 {c}: {lo.get(c)} ⟶ {ln_.get(c)}{tag}")
    fo, fn = floor_value(out_old["الافتراضيّ"]), floor_value(out_new["الافتراضيّ"])
    log(f"   (ج) أرضيةُ F1 المعايَرة: {fo} ⟶ {fn}" + ("" if fo == fn else "  ⟵ تغيّرت"))
    for name, _env in MODES:
        diff = text_diff(out_old[name], out_new[name])
        log(f"\n── [{name}] الأسطرُ المختلفة: {len(diff)}")
        for ln in diff:
            log("   " + ln)
    ok_all = ok2 and not bad3
    log(f"\nJUDGE V-E1={ok1} V-E2={ok2} V-E3={not bad3} flips_T-PRESESSION={len(flips)} "
        f"rows_changed={tot['changed']} label_changed={tot['label']} "
        f"floor={fo}->{fn} rc_new={rc_new} ⇒ "
        f"{'قابلٌ للإسناد' if ok_all else 'إسنادٌ مقيَّد (يُعلَن)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
