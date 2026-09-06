#!/usr/bin/env python3
"""🔗② T-TIERLINK-2 — «+100% في البري والافتر بالتصنيف — ومَن كانت قائمةُ ما قبل الجلسة ستدرجه؟»

العقد: `tierlink2_prereg.md` (مدفوعٌ قبل أيّ سطرٍ هنا). قراءةٌ/قياسٌ فقط: لا إرسال ·
لا كتابةَ حالة · لا مسَّ بالإنتاج. المقياسُ الواحد **بالاسم** من `tierlink_probe`
(‏`anchor_history` · `measure` · `features` · `daily_range`) ومن `tier_fwd_report.fetch_day`.

الجوابُ الثلاثيّ (‏§④): (أ) الرادارُ المقيس = صفُّ `PM` وعابرٌ للأرضية · (ب) الحيُّ
محاكًى = مرشِّحٌ رخيص (‏`MIN_DAY_USD` · أعلى `PREFILTER_CAP` بـ`day_ret`) ثم الأرضية ·
(ج) الافتر = المرشِّحُ ثم أعلى `TOPK` بـ`rank_key("AH")`. ⚠️ (ب)/(ج) **محاكاةٌ على صفوف
المسح لا الدالّةُ الحيّة** — مُعلَنٌ في المُخرَج.
"""
from __future__ import annotations

import collections
import datetime as dt
import glob
import gzip
import json
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import presession_feats as PF                                     # noqa: E402
import presession_radar as PR                                     # noqa: E402
import tierlink_probe as TL                                       # noqa: E402
from tierlink_probe import anchor_history, measure, features, daily_range, NY, wilson  # noqa: E402
from tier_fwd_report import fetch_day, load_ledger                # noqa: E402

SINCE = os.environ.get("TIERLINK_SINCE", "2026-08-18")
UNTIL = os.environ.get("TIERLINK_UNTIL", "").strip()              # فارغٌ = حتى اليوم (G4: قصرُه يُعيد المنشور)
MIN_COVER = TL.MIN_COVER                                          # 0.80 — بالاسم
MAX_UNSCANNED = 0.20                                              # G2
PM_END_MIN = 9 * 60 + 30


def log(m: str = "") -> None:
    print(m, flush=True)


# ───────────────────────── الجلسة والافتر الممتدّ ─────────────────────────────

def session_of(anchor_ms: int) -> str:
    """`pre` قبل 09:30 · `after` من 16:00 · وإلّا `reg` — بتوقيت نيويورك (كما `features.tod`)."""
    t = dt.datetime.fromtimestamp(int(anchor_ms) / 1000, tz=NY)
    hh = t.hour + t.minute / 60
    return "pre" if hh < 9.5 else ("reg" if hh < 16 else "after")


def ext_max(bars_next: list, e5: float) -> float | None:
    """أقصى قمّةِ **بريماركت اليوم التالي** (حتى 09:30 نيويورك) من سعر الكرت — للافتر (§②)."""
    if not bars_next or not e5:
        return None
    hs = []
    for x in bars_next:
        t = dt.datetime.fromtimestamp(x[0] / 1000, tz=NY)
        if t.hour * 60 + t.minute < PM_END_MIN:
            hs.append(x[2])
    return (max(hs) / e5 - 1) * 100 if hs else None


# ───────────────────────── القائمةُ الجديدة (§④) ──────────────────────────────

def load_scan_rows(paths: list) -> dict:
    """{(day, sess): [rows]} من ملفّات `presession_rows_*.jsonl.gz`."""
    out = collections.defaultdict(list)
    for p in paths:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                r = json.loads(line)
                out[(r[PF.ROW_DAY], r[PF.ROW_SESS])].append(r)
    return out


def emulate_prefilter(rows: list, cap: int = PR.PREFILTER_CAP,
                      min_usd: float = PR.MIN_DAY_USD, key: str = PR.PREFILTER_KEY) -> list:
    """محاكاةُ المرشِّح الرخيص على صفوف المسح: أرضيةُ `usd_day` ثم أعلى `cap` بـ`key`
    (المجهولُ إلى الذيل — كما `prefilter`). ⚠️ محاكاةٌ لا الدالّةُ الحيّة."""
    keep = []
    for r in rows:
        try:
            if float(r.get("usd_day")) < min_usd:
                continue
        except (TypeError, ValueError):
            continue
        keep.append(r)
    def _k(r):
        v = r.get(key)
        try:
            v = float(v)
        except (TypeError, ValueError):
            v = float("-inf")
        return (-v, r.get(PF.ROW_SYM) or "")
    keep.sort(key=_k)
    return keep[:cap]


def radar_verdict(day: str, sym: str, sess: str, scan: dict) -> dict:
    """§④ (أ)(ب)(ج) لمِرساةٍ واحدة. `None` في الحقول = «غيرُ قابلٍ للوسم»."""
    out = {"scanned": False, "row": False, "meas": None, "live": None, "ah": None,
           "rank": None, "val": None}
    if sess == "pre":
        rows = scan.get((day, "PM")) or []
        if not rows:
            return out
        out["scanned"] = True
        key = PF.rank_key("PM")
        mine = next((r for r in rows if r.get(PF.ROW_SYM) == sym), None)
        if mine is None:
            return out
        out["row"] = True
        out["val"] = mine.get(key)
        ordered = PF.order_rows(rows, key, k=0)
        out["rank"] = next((i + 1 for i, r in enumerate(ordered) if r.get(PF.ROW_SYM) == sym), None)
        out["meas"] = PF.floor_ok(mine, "PM")
        live_pool = emulate_prefilter(rows)
        out["live"] = any(r.get(PF.ROW_SYM) == sym for r in PF.apply_floor(live_pool, "PM"))
    elif sess == "after":
        rows = scan.get((day, "AH")) or []
        if not rows:
            return out
        out["scanned"] = True
        key = PF.rank_key("AH")
        mine = next((r for r in rows if r.get(PF.ROW_SYM) == sym), None)
        if mine is None:
            return out
        out["row"] = True
        out["val"] = mine.get(key)
        pool = emulate_prefilter(rows)
        top = PF.apply_floor(PF.order_rows(pool, key, k=PF.TOPK), "AH")
        out["ah"] = any(r.get(PF.ROW_SYM) == sym for r in top)
        ordered = PF.order_rows(rows, key, k=0)
        out["rank"] = next((i + 1 for i, r in enumerate(ordered) if r.get(PF.ROW_SYM) == sym), None)
    return out


# ───────────────────────── الجدول ─────────────────────────────────────────────

def pct(k, n):
    return f"{k}/{n} = {k/n*100:.1f}%" if n else "—"


def main() -> int:
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        log("⛔ لا POLYGON_API_KEY — خروج 2")
        return 2
    anchors = anchor_history(SINCE)
    if UNTIL:
        anchors = {k: v for k, v in anchors.items() if k[0] <= UNTIL}
    if not anchors:
        log("⛔ صفرُ مِرساةٍ (بصمةُ no-op) — خروج 4 (G3)")
        return 4
    paths = sorted(glob.glob("presession_rows_*.jsonl.gz"))
    scan = load_scan_rows(paths)
    if not scan:
        log("⛔ صفرُ صفِّ مسحٍ (بصمةُ no-op) — خروج 4 (G3)")
        return 4
    ledger = {(r["date"], r["symbol"]): r for r in load_ledger()}
    log(f"🔗② T-TIERLINK-2 · مراسٍ {len(anchors)} · منذ {SINCE}{' حتى ' + UNTIL if UNTIL else ''} · "
        f"سجلّ M5 {len(ledger)} · ملفّاتُ المسح {len(paths)} · أيامُ مسح {len({d for d, _ in scan})}")
    log(f"🔒 الأرضية PM={PF.FLOOR_BY_SLOT} · المرشِّح {PR.PREFILTER_KEY} · سقف {PR.PREFILTER_CAP} · "
        f"أرضيةُ الدولار ${PR.MIN_DAY_USD:,.0f} · TOPK {PF.TOPK} · مفتاحُ AH {PF.rank_key('AH')} — لا تُمَسّ")
    log("⚠️ (ب)/(ج) محاكاةُ المرشِّح على صفوف المسح — لا الدالّةُ الحيّة (‏T-PRECAP §⑧: نموذجان)")
    rows, fails, nobase = [], 0, 0
    cache = {}
    anchor_days = sorted({d for d, _ in anchors})
    for (day, sym), a in sorted(anchors.items()):
        bars = cache.get((sym, day))
        if bars is None:
            bars = fetch_day(sym, day, key)
            cache[(sym, day)] = bars or []
        if not bars:
            fails += 1
            continue
        dailies = daily_range(sym, day, key)
        b = ledger.get((day, sym))
        o = measure(a, b if b else None, bars, dailies)
        if o is None:
            nobase += 1
            continue
        f = features(a, b if b else None)
        if b is None and dailies and a.get("anchor_price"):
            pcs = [c for (d, _h, c) in dailies if d < day]
            if pcs:
                f["gap"] = TL._bucket((a["anchor_price"] / pcs[-1] - 1) * 100, (10, 30),
                                      ("<10%", "10-30%", "≥30%"))
        sess = session_of(a["anchor_ms"])
        ext = None
        if sess == "after":
            nxt = [d for (d, _h, _c) in (dailies or []) if d > day]
            if nxt:
                nb = cache.get((sym, nxt[0]))
                if nb is None:
                    nb = fetch_day(sym, nxt[0], key)
                    cache[(sym, nxt[0])] = nb or []
                ext = ext_max(nb, o["e5"])
        rv = radar_verdict(day, sym, sess, scan)
        rows.append({"date": day, "symbol": sym, "sess": sess, "f": f, "o": o,
                     "ext": ext, "rv": rv, "in_ledger": b is not None})
    total = len(anchors)
    cover = len(rows) / total
    log(f"\n🩺 G1 الجلب: قِيس {len(rows)} · تعذّر {fails} · بلا أساس {nobase} من {total} = {cover*100:.1f}%")
    if cover < MIN_COVER:
        log("⛔ التغطية دون 80% ⇒ لا يُفسَّر رقم — خروج 3 (G1)")
        return 3
    unscanned = [d for d in anchor_days if (d, "PM") not in scan and (d, "AH") not in scan]
    log(f"🩺 G2 المسح: أيامُ المراسي {len(anchor_days)} · بلا مسح {len(unscanned)}"
        + (f" ({' · '.join(unscanned)})" if unscanned else ""))
    if anchor_days and len(unscanned) / len(anchor_days) > MAX_UNSCANNED:
        log("⛔ أكثرُ من 20% من أيام المراسي بلا مسح ⇒ خروج 3 (G2)")
        return 3
    # ── G4 التكامل مع المنشور
    n = len(rows)
    e50 = sum(r["o"]["exploded50"] for r in rows)
    e100 = sum(r["o"]["exploded100"] for r in rows)
    log(f"\n📊 الأساس (كلُّ الجلسات): +50% {pct(e50, n)} · +100% {pct(e100, n)}"
        + ("   ← G4: يُقارَن بـ 33/321 · 14/321 المنشورة" if UNTIL == "2026-09-01" else ""))
    # ── ① الجلسة × الفئة
    log("\n" + "=" * 78 + "\n① الجلسةُ × الفئة (‏n · +50% · +100% · أسماءُ +100%)\n" + "=" * 78)
    tiers = ("قوي", "متوسط", "ضعيف", "؟")
    for sess in ("pre", "after", "reg"):
        sr = [r for r in rows if r["sess"] == sess]
        k50 = sum(r["o"]["exploded50"] for r in sr)
        k100 = sum(r["o"]["exploded100"] for r in sr)
        lo, hi = wilson(k100, len(sr)) if sr else (0, 0)
        log(f"\n▶ {sess:<5} n={len(sr):<4} +50%: {pct(k50, len(sr)):<18} +100%: {pct(k100, len(sr))} [{lo:.0f}·{hi:.0f}]")
        for t in tiers:
            tr = [r for r in sr if r["f"]["tier"] == t]
            if not tr:
                continue
            names = [f"{r['symbol']}({r['date'][5:]} {r['o']['mg_day']:+.0f}%)" for r in tr if r["o"]["exploded100"]]
            log(f"   {t:<6} n={len(tr):<4} +50%: {sum(r['o']['exploded50'] for r in tr):<3} "
                f"+100%: {sum(r['o']['exploded100'] for r in tr):<3} {' · '.join(names)}")
    # ── ② الرابطُ على +100% (المعيار الرباعيّ بالاسم · الأرضية 20)
    log("\n" + "=" * 78 + "\n② الرابطُ المنشور على exploded100 (المعيارُ الرباعيّ · n≥20 لكلّ سلّة)\n" + "=" * 78)
    pre_rows = [r for r in rows if r["sess"] == "pre"]
    for feat, best in (("j1", "J1"), ("gap", "≥30%"), ("tier", "قوي"), ("v2", "المرساة دون 30%"),
                       ("tod", "pre")):
        pool = rows if feat == "tod" else pre_rows
        a_ = [r for r in pool if r["f"][feat] == best]
        b_ = [r for r in pool if r["f"][feat] != best and r["f"][feat] != "؟"]
        ka, kb = sum(r["o"]["exploded100"] for r in a_), sum(r["o"]["exploded100"] for r in b_)
        ra, rb = (ka / len(a_) * 100 if a_ else 0), (kb / len(b_) * 100 if b_ else 0)
        la = wilson(ka, len(a_)) if a_ else (0, 0)
        lb = wilson(kb, len(b_)) if b_ else (0, 0)
        ok_n = len(a_) >= TL.MIN_N and len(b_) >= TL.MIN_N
        sep = la[0] > lb[1]
        verdict = ("**رابط**" if (ok_n and ra >= 2 * rb and sep and ka > 0)
                   else ("لا حكم (n<20)" if not ok_n else "لا فصل"))
        log(f"   {feat:<5}={best:<16} {pct(ka, len(a_)):<18}[{la[0]:.0f}·{la[1]:.0f}] مقابل "
            f"{pct(kb, len(b_)):<18}[{lb[0]:.0f}·{lb[1]:.0f}] ⇒ {verdict}")
    j1pm = [r for r in pre_rows if r["f"]["j1"] == "J1"]
    log(f"   J1∧بريماركت: +100% {pct(sum(r['o']['exploded100'] for r in j1pm), len(j1pm))} · "
        f"+50% {pct(sum(r['o']['exploded50'] for r in j1pm), len(j1pm))}")
    # ── ③ مَن كانت القائمةُ الجديدة ستدرجه؟
    log("\n" + "=" * 78 + "\n③ القائمةُ الجديدة (presession_radar) — (أ) المقيس · (ب) الحيّ محاكًى · (ج) الافتر\n" + "=" * 78)
    def _cap(rs, k):
        ok = [r for r in rs if r["rv"][k] is not None]
        yes = sum(1 for r in ok if r["rv"][k])
        return yes, len(ok), len(rs) - len(ok)
    for sess, keys in (("pre", ("meas", "live")), ("after", ("ah",))):
        sr = [r for r in rows if r["sess"] == sess]
        ex = [r for r in sr if r["o"]["exploded100"]]
        nx = [r for r in sr if not r["o"]["exploded100"]]
        log(f"\n▶ {sess}: مراسٍ {len(sr)} · +100% {len(ex)}")
        for k in keys:
            y1, n1, u1 = _cap(ex, k)
            y0, n0, u0 = _cap(nx, k)
            log(f"   ({k}) بين +100%: {pct(y1, n1)} (غيرُ قابلٍ للوسم {u1}) · بين غير المنفجرين: "
                f"{pct(y0, n0)} (غيرُ قابلٍ للوسم {u0})")
    # ── قائمةُ +100% كاملةً بالأسماء (لا قصّ)
    log("\n📋 كلُّ مَن تجاوز +100% (تاريخ · رمز · جلسة · فئة · J1 · e5 · mg_day · mg_ext(افتر) · إغلاق · القائمة الجديدة):")
    for r in sorted((r for r in rows if r["o"]["exploded100"]), key=lambda r: -r["o"]["mg_day"]):
        rv = r["rv"]
        def _y(v):
            return "؟" if v is None else ("✅" if v else "—")
        lst = (f"مقيس {_y(rv['meas'])} · حيّ {_y(rv['live'])}" if r["sess"] == "pre"
               else (f"افتر {_y(rv['ah'])}" if r["sess"] == "after" else "خارج القائمة (جلسة)"))
        rk = f" · رتبة {rv['rank']}" if rv.get("rank") else ""
        val = f" · {PF.rank_key('PM' if r['sess']=='pre' else 'AH')}={rv['val']}" if rv.get("val") is not None else ""
        ext = f" · ext {r['ext']:+.0f}%" if r["ext"] is not None else ""
        log(f"   {r['date'][5:]} {r['symbol']:<6} {r['sess']:<5} {r['f']['tier']:<6} {r['f']['j1']:<3} "
            f"e5={r['o']['e5']:<8} {r['o']['mg_day']:+7.1f}%{ext} · إغلاق {r['o']['close_ret']:+.1f}% · {lst}{rk}{val}")
    unl = [r for r in rows if r["sess"] in ("pre", "after") and not r["rv"]["row"]]
    log(f"\n🔎 غيرُ قابلٍ للوسم (بلا صفِّ مسحٍ — خارج كون 0.40-10$ أو يومٌ غيرُ ممسوح): {len(unl)}"
        + (": " + " · ".join(f"{r['symbol']}@{r['date'][5:]}" for r in unl if r["o"]["exploded100"]) if unl else ""))
    log("\n⚠️ حدودُ صدق: لمسٌ لا تنفيذ · (ب)/(ج) محاكاةٌ لا الدالّةُ الحيّة · الفئةُ فئةُ لحظة M5 · "
        "لا ربحيّة · أسبوعان ونصف · والحكمُ المنشور في tierlink_result.md لا يُستبدَل.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
