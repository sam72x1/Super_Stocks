#!/usr/bin/env python3
"""🕯️📅 `T-DATE-CANDLES` الملحق 2 — حصادُ المطابقة وجدولُها (قراءةٌ فقط · بلا شبكة).

المُدخَل: `data/population2.json` · `data/cards.jsonl` · `data/match_results.jsonl` (أسطرُ `DCR` من سجلّات `date_candles.yml`).
المُخرَج (`build`): `data/candles_table.tsv` (صفٌّ لكلّ صورةٍ في المجتمع) · `data/candles_derived.tsv` (صفوفُ «واثق» المؤهَّلة لـ
`faisal_derived_dates.tsv` بالملحق 2 §⑤ — **لا تُكتب فيه من هنا**) · وملخّصٌ مطبوع (الفحصُ الجانبيّ · العدّ). و`--check` يعيد البناءَ ويقارن.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
DATA = os.path.join(HERE, "data")
TABLE = os.path.join(DATA, "candles_table.tsv")
DERIVED = os.path.join(DATA, "candles_derived.tsv")
COLS = ["file", "symbol", "frame", "card", "label", "last_bar", "k", "k_split", "variant", "rms", "passers",
        "recorded_date", "recorded_src", "known_truth", "side_hit", "why"]
DCOLS = ["symbol", "line", "date", "method", "fingerprint", "max_diff", "witness", "run_id"]


def _jsonl(p):
    return [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()] if os.path.exists(p) else []


def sessions_apart(a: str, b: str) -> int:
    """عددُ أيّام التداول (الاثنين-الجمعة) بين يومين — مسافةُ الشمعة اليوميّة (العطلُ الرسميّة لا تُطرح ⟵ تقريبٌ لصالح «لا يصيب»)."""
    import numpy as np                                             # noqa: PLC0415
    x, y = sorted((a[:10], b[:10]))
    return int(np.busday_count(x, y))


def side_hit(frame: str, last_bar: str, truth: str):
    """الملحق 2 §⑤: يوميّ ⟵ جلسةٌ فأقلّ · أسبوعيّ ⟵ الأسبوعُ نفسُه أو المجاور · داخل اليوم ⟵ يومُ الحقيقة ‏±جلسة."""
    if not last_bar or not truth:
        return None
    if frame == "1W":
        wa = dt.date.fromisoformat(last_bar[:10]).isocalendar()
        wb = dt.date.fromisoformat(truth[:10]).isocalendar()
        return abs((wa[0] * 53 + wa[1]) - (wb[0] * 53 + wb[1])) <= 1
    return sessions_apart(last_bar, truth) <= 1


def recorded(fid: str, recs: dict, mapping_units: dict, unit_dates: dict) -> tuple:
    """التاريخُ المسجَّل أصلًا (للمقارنة بلا دهس): تاريخٌ تقويميٌّ في سجلّ العين ثمّ تاريخُ وحدة الكاتالوج المطابَقة."""
    x = recs.get(fid) or {}
    if x.get("dprec") in ("EXACT", "DAY") and x.get("date"):
        return x["date"], f"eye:{x['dprec']}"
    for u in mapping_units.get(fid, []):
        d = unit_dates.get(u)
        if d and d[0]:
            return d[0], f"table:{d[1]}"
    return "", ""


def build():
    import corpus as CP                                            # noqa: PLC0415
    import f0                                                      # noqa: PLC0415
    pop = json.load(open(os.path.join(DATA, "population2.json"), encoding="utf-8"))
    cards = {c["id"]: c for c in _jsonl(os.path.join(DATA, "cards.jsonl"))}
    res = {}
    for r in _jsonl(os.path.join(DATA, "match_results.jsonl")):
        res[r["id"]] = r                                           # الأخيرُ يغلب (إعادةُ دفعةٍ بعد سقوط)
    recs, _inv, _disk = CP.load()
    rows_t = list(csv.DictReader(open(os.path.join(ROOT, "faisal_levels_table.tsv"), encoding="utf-8"), delimiter="\t"))
    unit_dates = {(r["symbol"], r["line"]): (r["date"], r["date_source"]) for r in rows_t}
    mp = list(csv.DictReader(open(os.path.join(HERE, "data", "image_map.tsv"), encoding="utf-8"), delimiter="\t"))
    mapping_units = collections.defaultdict(list)
    for m in mp:
        if m["confidence"] in f0.MAP_FOUND and m["disk_file"]:
            for u in [x for x in (m.get("units") or "").split(",") if "|" in x]:
                sym, line = u.split("|", 1)
                mapping_units[os.path.splitext(m["disk_file"])[0]].append((sym, line))
    out = []
    for mbr in pop["members"]:
        fid = mbr["file"]
        c = cards.get(fid) or {}
        r = res.get(fid) or {}
        t1 = r.get("top1") or {}
        rd, rs = recorded(fid, recs, mapping_units, unit_dates)
        kt = (mbr.get("known") or {}).get("truth", "")
        lab = r.get("label", "") if c.get("ok") else ""
        hit = side_hit(mbr["frame"], t1.get("end", ""), kt) if (kt and lab in ("واثق", "مرجّح")) else None
        out.append({"file": fid, "symbol": mbr["symbol"], "frame": mbr["frame"],
                    "card": "ok" if c.get("ok") else "no", "label": lab or ("—" if not c.get("ok") else "لم يُطابَق"),
                    "last_bar": t1.get("end", ""), "k": t1.get("k", ""), "k_split": t1.get("k_exp", ""),
                    "variant": t1.get("variant", ""), "rms": t1.get("rms", ""), "passers": r.get("passers", ""),
                    "recorded_date": rd, "recorded_src": rs, "known_truth": kt,
                    "side_hit": "" if hit is None else ("1" if hit else "0"),
                    "why": c.get("why", "") if not c.get("ok") else r.get("why", "")})
    der, conflict = [], []
    by_unit = collections.defaultdict(list)
    for row in out:
        if row["label"] != "واثق":
            continue
        for u in mapping_units.get(row["file"], []):
            d = unit_dates.get(u)
            if d is not None and not d[0]:
                by_unit[u].append(row)
    for u, rows in sorted(by_unit.items()):
        days = sorted({x["last_bar"][:10] for x in rows})
        if len(days) > 1 and sessions_apart(days[0], days[-1]) > 1:
            conflict.append((u, days))
            continue
        x = sorted(rows, key=lambda x: x["last_bar"])[-1]
        der.append({"symbol": u[0], "line": u[1], "date": x["last_bar"][:10], "method": "candles",
                    "fingerprint": f"card:{x['file']} last:{x['last_bar']} k:{x['k']} split:{x['k_split']} {x['variant']}",
                    "max_diff": x["rms"], "witness": "واثق (تجريبيّ)", "run_id": ""})
    return pop, out, der, conflict


def _tsv(rows, cols) -> str:
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=cols, delimiter="\t", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in cols})
    return b.getvalue()


def summary(pop, out, der, conflict) -> list:
    L = []
    lab = collections.Counter(r["label"] for r in out)
    L.append(f"🧮 المجتمع {len(out)} · بطاقاتٌ ناجحة {sum(r['card'] == 'ok' for r in out)} · " +
             " · ".join(f"{k} {v}" for k, v in lab.most_common()))
    fr = collections.defaultdict(collections.Counter)
    for r in out:
        if r["card"] == "ok":
            fr[r["frame"]][r["label"]] += 1
    for f, c in sorted(fr.items()):
        n = sum(c.values())
        L.append(f"   {f}: بطاقات {n} · واثق {c['واثق']} ({c['واثق'] / max(1, n):.0%}) · مرجّح {c['مرجّح']}")
    sk = [r for r in out if r["known_truth"]]
    for la in ("واثق", "مرجّح"):
        g = [r for r in sk if r["label"] == la]
        h = sum(r["side_hit"] == "1" for r in g)
        L.append(f"🔎 الفحصُ الجانبيّ «{la}»: يصيب {h} من {len(g)}")
    L.append(f"🔎 المعروفُ تاريخُه في المجتمع {len(sk)} · منها ببطاقة {sum(r['card'] == 'ok' for r in sk)}")
    L.append(f"📅 صورٌ «واثق» {lab['واثق']} من صور القرص {pop['disk']} ({lab['واثق'] / max(1, pop['disk']):.1%}) · "
             f"منها بلا تاريخٍ مسجَّلٍ قبلها {sum(1 for r in out if r['label'] == 'واثق' and not r['recorded_date'])}")
    L.append(f"🧾 صفوفُ الكاتالوج المؤهَّلة لوسم candles {len(der)} · تعارض {len(conflict)} {conflict[:3]}")
    L.extend(fsweep_lines(out))
    return L


FSWEEP_LEDGER = os.path.join(ROOT, "fm_forensics", "fsweep", "data", "FSWEEP_LEDGER.jsonl")
FSWEEP_OK_SRC = ("visible_in_image", "forward_origin")


def fsweep_lines(out: list) -> list:
    """العقد §④-④: صورُ SWEEP بلا تاريخ منشورٍ مقبول ⟵ «واثق» وآخرُ شمعةٍ D و`collected_utc − D` سبعةُ أيّامٍ أو أقلّ ⟵ «مؤهَّلٌ بملحق»."""
    last = {}
    for x in _jsonl(FSWEEP_LEDGER):
        if x.get("image"):
            last[os.path.splitext(x["image"])[0]] = x
    sw = {k: v for k, v in last.items() if v.get("decision") == "SWEEP" and v.get("date_source") not in FSWEEP_OK_SRC}
    by = {r["file"]: r for r in out}
    q = []
    for k, v in sorted(sw.items()):
        r = by.get(k)
        st = "خارج المجتمع" if r is None else (r["label"] or "—")
        ok = False
        if r is not None and r["label"] == "واثق" and r["last_bar"] and v.get("collected_utc"):
            ok = (dt.date.fromisoformat(v["collected_utc"][:10]) - dt.date.fromisoformat(r["last_bar"][:10])).days <= 7
        q.append(f"{v.get('symbol')} {k} ({st}{' · مؤهَّلٌ بملحق' if ok else ''})")
    n = sum("مؤهَّلٌ بملحق" in x for x in q)
    return [f"🧹 T-FSWEEP: سحوبٌ بلا تاريخ منشورٍ مقبول {len(sw)} ⟵ «مؤهَّلٌ بملحقٍ لـT-FSWEEP» {n} · " + " · ".join(q)]


def main(argv) -> int:
    pop, out, der, conflict = build()
    t, d = _tsv(out, COLS), _tsv(der, DCOLS)
    if len(argv) > 1 and argv[1] == "--check":
        same = open(TABLE, encoding="utf-8").read() == t and open(DERIVED, encoding="utf-8").read() == d
        print("✅ الجدولُ مطابقٌ بايتًا" if same else "❌ الجدولُ يختلف")
        return 0 if same else 1
    open(TABLE, "w", encoding="utf-8").write(t)
    open(DERIVED, "w", encoding="utf-8").write(d)
    print("\n".join(summary(pop, out, der, conflict)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
