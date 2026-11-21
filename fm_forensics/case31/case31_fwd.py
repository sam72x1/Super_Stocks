#!/usr/bin/env python3
"""🗂️🔬 `T-CASE31` — الدفترُ الأماميّ الصامت (العقد §⑥ «للأمام» · أمرُ المالك 2026-11-20 ⑤).

الأوضاع:
  record  — لكلّ جلسةٍ مغلقةٍ لم تُسجَّل (آخر `LOOKBACK` جلسات) ولها لقطةُ «تحت المتابعة»: سطرٌ لكلّ صفٍّ مقيس بقناع المثبَّتات
            («1» يحمل · «0» لا يحمل · «?» غير مقيس) في `data/case31_fwd.jsonl`.
  settle  — كلُّ يومٍ مسجَّلٍ مضى عليه `WIN` جلسة: انفجر (High فوق ضعف إغلاق يوم القرار في D+1…D+20)؟ وعائدُ الصفقة
            (شراءُ افتتاح D+1 وبيعُ إغلاق D+20 أو آخر شمعة) في `data/case31_fwd_settled.jsonl`.
  report  — وصفُ المحسوم بقاعدة العقد نفسِها (`case31_validate.judge_print`/`judge_excl`) ⟵ `out/FWD.md`.
  auto    — record ثمّ settle ثمّ report (الكرون).

قراءةٌ فقط: بلا تلغرام · بلا Polygon · لا يمسّ أداةً ولا عتبة · الدفتران إلحاقيّان · خروج 9 بلا ملفّ تثبيتٍ ببصمته.
السماتُ المحسوبة هنا: الشموع (يوميّ · أسبوعيّ · 4 ساعات) وحصادُ البوت (`bot.*` · `bw.*`) — وشرطٌ على أسرةٍ أخرى يُكتب «?» (غير مقيس) ويُعَدّ.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (HERE, ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import case31 as C                      # noqa: E402
import case31_freeze as FZ              # noqa: E402
import case31_validate as V             # noqa: E402

LOOKBACK = 5                            # جلساتٌ مغلقة يُستدرَك تسجيلُها إن تأخّرت لقطتُها
WIN = 20                                # نافذةُ الحسم (العقد: بعد 20 جلسة)
FWD = os.path.join(HERE, "data", "case31_fwd.jsonl")
SETTLED = os.path.join(HERE, "data", "case31_fwd_settled.jsonl")
REPORT = os.path.join(C.OUT, "FWD.md")
FWD_FROM = "2026-11-20"                 # أوّلُ يوم قرارٍ أماميّ: نافذتا الاكتشاف والتحقّق تنتهيان ببداية حركةٍ 11-20 (يومُ قرارها 11-19 فما قبل)
CANDLE = ("D.", "W.", "H4.", "px.", "vol.")   # أُسَرُ الشموع (تُحسب دائمًا)
BOT = ("bot.", "bw.")                   # حصادُ البوت من اللقطة والسجلّات (يُحسب إن ثُبِّت شرطٌ عليه)


def log(m=""):
    print(m, flush=True)


# ══ نقيّات ═══════════════════════════════════════════════════════════════════
def items_of(fz):
    """(نقيّة) ملفُّ التثبيت ⟵ [{id, arm, kind, texts, conds}] بترتيبٍ حتميّ (الذراع · البصمات ثمّ الاستبعاد · رتبتُها في الملفّ)."""
    out = []
    for arm in sorted((fz or {}).get("arms") or {}):
        sel = fz["arms"][arm]
        for kind, key, tag in (("بصمة", "prints", "P"), ("استبعاد", "excl", "X")):
            for i, it in enumerate(sel.get(key) or [], 1):
                out.append({"id": f"{arm}{tag}{i}", "arm": arm, "kind": kind, "texts": list(it["texts"]), "conds": list(it["conds"])})
    return out


def mask_of(items, f):
    """(نقيّة) صفُّ سمات ⟵ قناعٌ بترتيب المثبَّتات: «1» كلُّ الشروط متحقّقة · «0» شرطٌ معلومٌ خالف · «?» لا مخالفَ معلومًا وفيه مجهول."""
    out = []
    for it in items:
        hs = [FZ.holds(c, f) for c in it["conds"]]
        out.append("1" if hs and all(h is True for h in hs) else ("0" if any(h is False for h in hs) else "?"))
    return "".join(out)


def closed_sessions(days, now_ny):
    """(نقيّة) أيّامُ التقويم المغلقة: ما قبل يوم نيويورك الحاليّ · واليومُ نفسُه بعد 20:00 نيويورك (بعد الأفتر)."""
    today = now_ny.strftime("%Y-%m-%d")
    return [d for d in sorted(days) if d < today or (d == today and now_ny.hour >= 20)]


def pending_days(closed, done, k=LOOKBACK, start=FWD_FROM):
    """(نقيّة) آخرُ `k` جلساتٍ مغلقة لم تُسجَّل — من `start` فصاعدًا (لا يومَ من نافذتَي الاكتشاف والتحقّق)."""
    return [d for d in closed[-k:] if d not in done and d >= start]


def settle_due(closed, recorded, settled, win=WIN):
    """(نقيّة) الأيّامُ المسجَّلة غيرُ المحسومة التي بعدها `win` جلسةً مغلقة فأكثر."""
    ix = {d: i for i, d in enumerate(closed)}
    return [d for d in sorted(recorded) if d not in settled and d in ix and len(closed) - 1 - ix[d] >= win]


def unsupported(items):
    """(نقيّة) شروطُ المثبَّتات على أُسَرٍ لا يحسبها الدفتر (تُكتب «?») ⟵ أسماؤها."""
    return sorted({c["f"] for it in items for c in it["conds"] if not c["f"].startswith(CANDLE + BOT)})


def fwd_rows(led, st):
    """(نقيّة) الدفتران ⟵ صفوفُ تحقّق [{y, f: {معرّف: 1/0/None}, ret, day}] للمحسوم الموسوم وحدَه · القناعُ يُقرأ بمعرّفات يومه."""
    ids, lab = {}, {}
    for r in led:
        if r.get("kind") == "day":
            ids[r["D"]] = list(r.get("items") or [])
    for r in st:
        if r.get("kind") != "day" and r.get("x") is not None:
            lab[(r["D"], r["sym"])] = r
    out = []
    for r in led:
        if r.get("kind") == "day":
            continue
        z = lab.get((r["D"], r["sym"]))
        if z is None:
            continue
        f = {i: (None if ch == "?" else int(ch)) for i, ch in zip(ids.get(r["D"], []), r.get("m") or "")}
        out.append({"y": int(bool(z["x"])), "f": f, "ret": z.get("ret"), "day": r["D"]})
    return out


def judge(items, rows):
    """(نقيّة) حكمُ كلّ مثبَّتٍ على صفوف الدفتر المحسومة بقاعدة العقد (`case31_validate`) ⟵ [{id, kind, texts, …حكم}]."""
    out = []
    for it in items:
        cond = [{"f": it["id"], "op": "==", "v": 1}]
        res = (V.judge_print if it["kind"] == "بصمة" else V.judge_excl)(cond, rows) if rows else {"verdict": "لم يُحسم بعد"}
        out.append(dict(res, id=it["id"], kind=it["kind"], texts=it["texts"], arm=it["arm"]))
    return out


def report_md(items, led, st, today):
    """(نقيّة) ⟵ نصُّ `out/FWD.md`: ما سُجّل وما حُسم وحكمُ كلّ مثبَّتٍ على المحسوم (وصفٌ حتى اكتمال 4 أسابيع)."""
    days = sorted(r["D"] for r in led if r.get("kind") == "day")
    sdays = sorted(r["D"] for r in st if r.get("kind") == "day")
    rows = [r for r in led if r.get("kind") != "day"]
    L = ["# 🗂️🔬 `T-CASE31` — الدفترُ الأماميّ الصامت (مولَّدٌ آليًّا · لا يُعدَّل باليد)", "",
         f"- حتى {today}: جلساتٌ مسجَّلة {len(days)}" + (f" ({days[0]} … {days[-1]})" if days else "") + f" · صفوف {len(rows):,} · جلساتٌ محسومة {len(sdays)}"
         + (f" ({sdays[0]} … {sdays[-1]})" if sdays else " (أوّلُ حسمٍ بعد 20 جلسةً من أوّل تسجيل)"),
         f"- شروطٌ على أُسَرٍ لا يحسبها الدفتر (تُكتب «غير مقيس»): {'، '.join('`' + x + '`' for x in unsupported(items)) or 'لا شيء'}", "",
         "| المعرّف | الذراع | النوع | المثبَّت | حاملون مسجَّلون | غير مقيس | الحكمُ على المحسوم |", "|---|---|---|---|---|---|---|"]
    ids = {r["D"]: list(r.get("items") or []) for r in led if r.get("kind") == "day"}
    res = {x["id"]: x for x in judge(items, fwd_rows(led, st))}
    for it in items:
        car = unm = 0
        for r in rows:
            pos = ids.get(r["D"], [])
            if it["id"] in pos and len(r.get("m") or "") > pos.index(it["id"]):
                ch = r["m"][pos.index(it["id"])]
                car, unm = car + (ch == "1"), unm + (ch == "?")
        x = res[it["id"]]
        extra = ""
        if x.get("n") is not None and it["kind"] == "بصمة":
            extra = f" — حاملون محسومون {x['n']} · انفجر {x['k']}" + (f" · الربحُ بعد الكلفة {x['profit'] * 100:+.1f}%" if x.get("profit") is not None else "")
        L.append(f"| {it['id']} | {it['arm']} | {it['kind']} | {' ∧ '.join('`' + t + '`' for t in it['texts'])} | {car:,} | {unm:,} | {x['verdict']}{extra} |")
    L += ["", "- الحاكمُ كما في العقد §⑥: أدنى فاصل ويلسون 95% لنسبة الانفجار عند الحاملين فوق نسبة المجتمع · ومتوسّطُ الربح بعد كلفة 1.8% موجبٌ وفوق غير الحاملين "
              "في الأيّام نفسِها · وحاملون دون 20 «لا قياس».", ""]
    return "\n".join(L)


# ══ قراءةٌ وإلحاق ═════════════════════════════════════════════════════════════
def read_jsonl(path):
    out = []
    try:
        with open(path, encoding="utf-8") as fh:
            for ln in fh:
                try:
                    out.append(json.loads(ln))
                except ValueError:
                    continue
    except OSError:
        pass
    return out


def append_jsonl(path, rows):
    """إلحاقٌ فقط (لا إعادةَ كتابة): سطرٌ لكلّ صفّ."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")


def _calendar(B, TV, tmap, n=320):
    cal = B.tv_frames(["AAPL", "MSFT"], tmap, "1D", n, False)
    return sorted({TV.ny_day(b[0]) for s in cal for b in cal[s]})


def _rows_d(TV, rd):
    return [(TV.ny_day(b[0]), b[1], b[2], b[3], b[4], b[5]) for b in rd]


# ══ الأوضاع ═══════════════════════════════════════════════════════════════════
def mode_record(now=None):
    fz = FZ.load_freeze()
    if fz is None:
        log(f"⛔ لا ملفَّ تثبيتٍ ببصمته — خروج {C.RC_FREEZE}")
        return C.RC_FREEZE
    import pandas as pd
    import Super_stock as S
    import case31_build as B
    import case31_feat as F
    import tv_data as TV
    items = items_of(fz)
    tmap = S._tv_ticker_map() or {}
    days = _calendar(B, TV, tmap)
    closed = closed_sessions(days, TV.ny_time(int(now or time.time())))
    done = {r["D"] for r in read_jsonl(FWD) if r.get("kind") == "day"}
    todo = pending_days(closed, done)
    nw, wl = B.snapshots("near_watch.json"), B.snapshots("weekly_watchlist.json")
    pools = {}
    for d in todo:
        sp = B.snap_for(nw, d)
        if not sp:
            log(f"   … {d}: لا لقطةَ «تحت المتابعة» بعدُ")
            continue
        sw = B.snap_for(wl, d)
        wj = B.git_json(sw[1], "weekly_watchlist.json") if sw else {}
        pools[d] = {"snap": sp[0], "rows": B.measured_rows(B.git_json(sp[1], "near_watch.json")),
                    "in_list": sorted({str(x.get("symbol")).upper() for x in wj.get("stocks") or [] if isinstance(x, dict)}),
                    "in_pullback": sorted({str(x.get("symbol")).upper() for x in wj.get("pullback") or [] if isinstance(x, dict)})}
    if not pools:
        log(f"🗂️ لا جلسةَ جديدة بلقطة (المغلقة {closed[-1] if closed else '—'} · المسجَّلة {len(done)})")
        return C.RC_OK
    need = sorted({s for p in pools.values() for s in p["rows"]})
    bars_d = B.tv_frames(need, tmap, "1D", B.TV_D_N, False)
    bars_h4 = B.tv_frames(need, tmap, "240", B.TV_H4_N, True)
    log(f"📺 يوميّ {len(bars_d)}/{len(need)} · 4 ساعات {len(bars_h4)}/{len(need)}")
    want_bot = any(c["f"].startswith(BOT) for it in items for c in it["conds"])
    L = B.ledgers() if want_bot else None
    sha, out = (FZ.freeze_sha() or "")[:12], []
    for d in sorted(pools):
        lines, n_bars = [], 0
        for s, _row in sorted(pools[d]["rows"].items()):
            f, close = {}, None
            rows_d = _rows_d(TV, bars_d.get(s) or [])
            hit = [r for r in rows_d if r[0] == d]
            if hit:
                try:
                    dfD = pd.DataFrame([r[1:] for r in rows_d], columns=["Open", "High", "Low", "Close", "Volume"], index=pd.to_datetime([r[0] for r in rows_d]))
                    rh = bars_h4.get(s) or []
                    dfH = pd.DataFrame([b[1:] for b in rh], columns=["Open", "High", "Low", "Close", "Volume"],
                                       index=pd.to_datetime([TV.ny_time(b[0]).replace(tzinfo=None) for b in rh])) if rh else None
                    f = dict(F.with_deltas(dfD, dfH, d, 1.0))
                    if L is not None:
                        f.update(B.bot_features(pools[d], None, None, s, d, L))
                    close, n_bars = hit[0][4], n_bars + 1
                except Exception as ex:                             # noqa: BLE001 — صفٌّ يتعطّل ⟵ «غير مقيس» لا إيقاف
                    log(f"   ⚠️ {s} {d}: {type(ex).__name__}")
                    f, close = {}, None
            lines.append({"D": d, "sym": s, "c": close, "m": mask_of(items, f)})
        out.append({"kind": "day", "D": d, "snap": pools[d]["snap"], "n": len(lines), "with_bars": n_bars, "freeze": sha, "items": [it["id"] for it in items]})
        out += lines
        log(f"🗂️ {d}: صفوف {len(lines)} · بشموع {n_bars} · " + " · ".join(f"{it['id']} {sum(1 for x in lines if x['m'][i] == '1')}" for i, it in enumerate(items)))
    append_jsonl(FWD, out)
    return C.RC_OK


def mode_settle(now=None):
    led, st = read_jsonl(FWD), read_jsonl(SETTLED)
    recorded = {r["D"] for r in led if r.get("kind") == "day"}
    if not recorded:
        log("🗂️ لا شيء مسجَّلًا بعد")
        return C.RC_OK
    import Super_stock as S
    import case31_build as B
    import tv_data as TV
    tmap = S._tv_ticker_map() or {}
    closed = closed_sessions(_calendar(B, TV, tmap), TV.ny_time(int(now or time.time())))
    due = settle_due(closed, recorded, {r["D"] for r in st if r.get("kind") == "day"})
    if not due:
        log(f"🗂️ لا يومَ حلّ حسمُه (المسجَّل {len(recorded)} · أقدمُه {min(recorded)})")
        return C.RC_OK
    by = {d: [r for r in led if r.get("kind") != "day" and r["D"] == d] for d in due}
    need = sorted({r["sym"] for d in due for r in by[d]})
    bars_d = B.tv_frames(need, tmap, "1D", 320, False)
    out = []
    for d in due:
        lines = []
        for r in by[d]:
            x, after, ret = B.label(_rows_d(TV, bars_d.get(r["sym"]) or []), d)
            lines.append({"D": d, "sym": r["sym"], "x": x, "ret": ret, "after": after})
        out.append({"kind": "day", "D": d, "n": len(lines), "labeled": sum(1 for x in lines if x["x"] is not None)})
        out += lines
        log(f"⚖️ {d}: حُسم {out[-len(lines) - 1]['labeled']} من {len(lines)}")
    append_jsonl(SETTLED, out)
    return C.RC_OK


def mode_report(now=None):
    fz = FZ.load_freeze()
    if fz is None:
        log(f"⛔ لا ملفَّ تثبيتٍ ببصمته — خروج {C.RC_FREEZE}")
        return C.RC_FREEZE
    md = report_md(items_of(fz), read_jsonl(FWD), read_jsonl(SETTLED), time.strftime("%Y-%m-%d", time.gmtime(now or time.time())))
    os.makedirs(C.OUT, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        fh.write(md + "\n")
    log(md)
    return C.RC_OK


def main(argv):
    if not C.contract_ok():
        return C.RC_CONTRACT
    os.environ.pop("POLYGON_API_KEY", None)
    mode = argv[1] if len(argv) > 1 else "auto"
    if mode == "record":
        return mode_record()
    if mode == "settle":
        return mode_settle()
    if mode == "report":
        return mode_report()
    if mode == "auto":
        for fn in (mode_record, mode_settle, mode_report):
            rc = fn()
            if rc != C.RC_OK:
                return rc
        return C.RC_OK
    log("الاستعمال: case31_fwd.py auto|record|settle|report")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
