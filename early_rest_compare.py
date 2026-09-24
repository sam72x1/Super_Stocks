# -*- coding: utf-8 -*-
"""🗓️🔍② `T-EARLY-2` — مقارنةُ صفوف المرفوعة بصفوف الحاكمة **داخل نافذة التعرّض `W` وخارجها**.

العقد: `early_rest_prereg.md` §①/§④/§⑥ (مدفوعٌ قبل هذا الملفّ وقبل أيّ رقم).

- **`W`** لكلّ يومِ إغلاقٍ مبكّر `D` (2023-2025 من `market_calendar`) = **عشرةُ أيّام تداولٍ أوّلُها `D1`**
  (يومُ التداول التالي) — لأن `prev_close.update(closes)` **يحمل** إغلاقَ `D` لرمزٍ لم يتداول يومَ `D1`.
- **`V-R1`** الأيّامُ من التقويم = قائمتا العقد (‏8 ‏+ 8).
- **`V-R3` الإسناد:** صفوفُ المرفوعة **خارج `W`** مطابقةٌ لصفوف الحاكمة **بت-بت** (مجموعاتٌ متعدّدة من
  JSON المرتَّب المفاتيح) — والفرقُ داخل `W` هو `ER1` (مضافٌ · محذوفٌ · ومفاتيحُ `(رمز، يوم)` المتغيّرة).
- **صفٌّ بلا `day` لا يُنسَب إلى أيّ جانب** ⇒ يُعَدّ ويُسقط الحارسَ (لا يُخفى خارج `W` بصمت).

وسطرُ الحكم (`ER2`) يُقرأ من **فرق مُخرَجَي التشغيلتين** (`--logs`) لا من ذاكرتي.

الاستعمال: `python early_rest_compare.py <مجلّدُ الحاكمة> <مجلّدُ المرفوعة> [<مجلّدُ المطفأة>]`
أو `python early_rest_compare.py --logs <سجلُّ الحاكمة> <سجلُّ المعادة>`
— يقرأ كلَّ `*.jsonl` تحت كلّ مجلّد. **خروج 0** = `V-R3` عابر · **5** = ساقط · **2** = مُدخَلٌ ناقص.

🔒 قراءةٌ/قياسٌ فقط · الإنتاجُ لا يستوردها · لا `LOGIC_VERSION`.
"""
import datetime as dt
import glob
import json
import os
import re
import sys
from collections import Counter

import market_calendar as MC

W_LEN = 10          # هندسيٌّ مُعلَن (العقد §①): عشرةُ أيّام تداولٍ أوّلُها D1
YEARS = ("2023", "2024", "2025")
RC_PASS, RC_FAIL, RC_INPUT = 0, 5, 2

# قائمتا العقد §① بحرفهما — `V-R1` يطابقهما بما يشتقّه من التقويم
CONTRACT_D = ("2023-07-03", "2023-11-24", "2024-07-03", "2024-11-29", "2024-12-24", "2025-07-03",
              "2025-11-28", "2025-12-24")
CONTRACT_D1 = ("2023-07-05", "2023-11-27", "2024-07-05", "2024-12-02", "2024-12-26", "2025-07-07",
               "2025-12-01", "2025-12-26")


def _is_trading(d: dt.date) -> bool:
    return d.weekday() < 5 and d.isoformat() not in MC.HOLIDAYS


def next_trading(day: str) -> str:
    """يومُ التداول التالي — يتخطّى العطلةَ ونهايةَ الأسبوع (نقيّة)."""
    x = dt.date.fromisoformat(day) + dt.timedelta(days=1)
    while not _is_trading(x):
        x += dt.timedelta(days=1)
    return x.isoformat()


def early_days() -> list:
    """أيّامُ الإغلاق المبكّر `D` في 2023-2025 من التقويم (مرتّبة)."""
    return sorted(d for d in MC.EARLY_CLOSES if d[:4] in YEARS)


def window_days(n: int = W_LEN) -> dict:
    """‏`{D: [D1 … ]}` — أوّلُ `n` أيّام تداولٍ بعد كلّ `D`."""
    out = {}
    for d in early_days():
        seq, x = [], d
        while len(seq) < n:
            x = next_trading(x)
            seq.append(x)
        out[d] = seq
    return out


def vr1() -> dict:
    """`V-R1`: التقويمُ = قائمتا العقد بحذافيرها."""
    D = early_days()
    D1 = [next_trading(d) for d in D]
    return {"ok": tuple(D) == CONTRACT_D and tuple(D1) == CONTRACT_D1, "D": D, "D1": D1}


def load_rows(root: str) -> list:
    """كلُّ صفوف `*.jsonl` تحت المجلّد (مرتّبةً بالاسم) — الصفُّ التالفُ يُعَدّ لا يُتجاهَل."""
    rows = []
    for p in sorted(glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True)):
        with open(p, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    rows.append(json.loads(ln))
                except ValueError:
                    rows.append({"__bad__": ln[:80]})
    return rows


def _canon(r) -> str:
    return json.dumps(r, sort_keys=True, ensure_ascii=False)


def _key(r):
    return (r.get("sym") or r.get("symbol"), r.get("day"))


def compare(gov_rows: list, new_rows: list, wdays: dict) -> dict:
    """نقيّة: `V-R3` خارج `W` · و`ER1` داخلها · وصفوفُ `D1` وحدَها منفصلة."""
    W = {x for seq in wdays.values() for x in seq}
    D1 = {seq[0] for seq in wdays.values()}

    def split(rows):
        inside, outside, nod = Counter(), Counter(), 0
        for r in rows:
            day = r.get("day") if isinstance(r, dict) else None
            if not isinstance(day, str):
                nod += 1
                continue
            (inside if day in W else outside)[_canon(r)] += 1
        return inside, outside, nod

    g_in, g_out, g_nod = split(gov_rows)
    n_in, n_out, n_nod = split(new_rows)
    out_plus, out_minus = n_out - g_out, g_out - n_out
    add, rem = n_in - g_in, g_in - n_in
    touched = {_key(json.loads(c)) for c in list(add) + list(rem)}
    d1_touched = {k for k in touched if k[1] in D1}
    sample = sorted({_key(json.loads(c)) for c in list(out_plus) + list(out_minus)},
                    key=lambda k: (str(k[1]), str(k[0])))[:10]
    return {
        "gov_rows": len(gov_rows), "new_rows": len(new_rows),
        "gov_in_W": sum(g_in.values()), "new_in_W": sum(n_in.values()),
        "no_day": g_nod + n_nod,
        "vr3_ok": (not out_plus and not out_minus and g_nod + n_nod == 0),
        "out_added": sum(out_plus.values()), "out_removed": sum(out_minus.values()),
        "out_sample": sample,
        "in_added": sum(add.values()), "in_removed": sum(rem.values()),
        "touched_keys": len(touched), "touched_D1": len(d1_touched),
        "touched_carry": len(touched) - len(d1_touched),
        "touched_list": sorted(touched, key=lambda k: (str(k[1]), str(k[0])))[:40],
    }


_TS_RE = re.compile(r"^\ufeff?\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z ?")
_HEAD_RE = re.compile(r'^##\[group\]Run python (?:"\$E2_SCRIPT"|[A-Za-z0-9_]+\.py)\s*$')


def step_output(log_text: str) -> list:
    """مُخرَجُ خطوة `Run python …` الوحيدة في سجلّ تشغيلة — نقيّة، بلا طوابع الوقت.

    الحاكمة `Run python <سكربت>.py` والمعادة `Run python "$E2_SCRIPT"` — **رأسٌ بكلمةٍ واحدةٍ بعد `python`**
    (فخطوةُ الرقعة `Run python early_rest_patch.py gov …` لا تُطابَق) ⇒ **مجموعةٌ واحدةٌ بالضبط** وإلّا `[]`
    (لا يُخمَّن أيُّهما). المُخرَجُ من بعد `##[endgroup]` رأسِها حتى رأسِ الخطوة التالية (`##[group]`) أو
    `Post job cleanup`."""
    lines = [_TS_RE.sub("", ln.rstrip("\r")) for ln in (log_text or "").splitlines()]
    heads = [i for i, ln in enumerate(lines) if _HEAD_RE.match(ln)]
    if len(heads) != 1:
        return []
    i = heads[0] + 1
    while i < len(lines) and not lines[i].startswith("##[endgroup]"):
        i += 1
    out = []
    for ln in lines[i + 1:]:
        if ln.startswith("##[group]") or ln.startswith("Post job cleanup"):
            break
        out.append(ln)
    return out


def log_diff(gov_text: str, new_text: str, limit: int = 300) -> list:
    """فرقُ مُخرَجَي الحاكمة والمعادة سطرًا سطرًا (`difflib`، بلا سياق) — الحكمُ يُقرأ منه بحرفه (`ER2`)."""
    import difflib
    a, b = step_output(gov_text), step_output(new_text)
    if not a or not b:
        return [f"⛔ مُخرَجٌ غائب: الحاكمة {len(a)} سطرًا · المعادة {len(b)} سطرًا"]
    d = [ln for ln in difflib.unified_diff(a, b, "الحاكمة", "المعادة", n=0, lineterm="")]
    if not d:
        return [f"✅ المُخرَجان متطابقان بت-بت ({len(a)} سطرًا)"]
    return d[:limit] + ([f"… قُصّ {len(d) - limit} سطرًا"] if len(d) > limit else [])


def report(tag: str, res: dict) -> list:
    """أسطرُ التقرير — الحكمُ في آخرها."""
    return [
        f"── {tag} ──",
        f"   الصفوف: الحاكمة {res['gov_rows']:,} · المرفوعة {res['new_rows']:,} · "
        f"داخل W: {res['gov_in_W']:,} ⟶ {res['new_in_W']:,} · بلا يوم: {res['no_day']}",
        f"   ER1 داخل W: مضاف {res['in_added']} · محذوف {res['in_removed']} · "
        f"مفاتيحُ (رمز، يوم) متغيّرة {res['touched_keys']} (منها D1 {res['touched_D1']} · "
        f"حملٌ بعده {res['touched_carry']})",
        f"   المتغيّرة: {res['touched_list']}",
        f"   V-R3 خارج W: مضاف {res['out_added']} · محذوف {res['out_removed']} · "
        f"عيّنة {res['out_sample']}",
        f"   V-R3 {'✅ عابر' if res['vr3_ok'] else '❌ ساقط'}",
    ]


def main(argv) -> int:
    if len(argv) == 4 and argv[1] == "--logs":
        with open(argv[2], encoding="utf-8", errors="replace") as a, \
                open(argv[3], encoding="utf-8", errors="replace") as b:
            d = log_diff(a.read(), b.read())
        print("── ER2: فرقُ مُخرَج الحاكمة والمعادة ──")
        for ln in d:
            print("   " + ln)
        return RC_INPUT if d and d[0].startswith("⛔") else RC_PASS
    if len(argv) not in (3, 4):
        print("الاستعمال: early_rest_compare.py <الحاكمة> <المرفوعة> [<المطفأة>]")
        return RC_INPUT
    v1 = vr1()
    wd = window_days()
    print(f"V-R1 {'✅' if v1['ok'] else '❌'} · D={v1['D']} · D1={v1['D1']}")
    for d, seq in wd.items():
        print(f"   W[{d}] = {seq[0]} ⟶ {seq[-1]} ({len(seq)} يوم تداول)")
    gov, new = load_rows(argv[1]), load_rows(argv[2])
    if not gov or not new:
        print(f"⛔ صفوفٌ غائبة: الحاكمة {len(gov)} · المرفوعة {len(new)}")
        return RC_INPUT
    res = compare(gov, new, wd)
    lines = report("المرفوعة مقابل الحاكمة", res)
    ok = v1["ok"] and res["vr3_ok"]
    if len(argv) == 4:
        off = load_rows(argv[3])
        if not off:
            print("⛔ صفوفُ المطفأة غائبة")
            return RC_INPUT
        lines += report("الاحتياط: المرفوعة مقابل المطفأة", compare(off, new, wd))
        lines += report("إعادةُ الإنتاج: المطفأة مقابل الحاكمة", compare(gov, off, wd))
        ok = v1["ok"] and compare(off, new, wd)["vr3_ok"]
    for ln in lines:
        print(ln)
    print(f"JUDGE_ER vr1={v1['ok']} vr3={ok} in_added={res['in_added']} in_removed={res['in_removed']} "
          f"touched={res['touched_keys']} d1={res['touched_D1']} carry={res['touched_carry']}")
    return RC_PASS if ok else RC_FAIL


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
