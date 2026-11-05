"""⭐💀 «التقاطع الذهبي» — الذراع أ: SMA50 × SMA200 على شموع 4 ساعات (نايف @Naifo9x · شارتا INTC) · قراءةٌ وعرضٌ فقط.

**العقد:** `fm_forensics/ema_cross/T_GCROSS_prereg.md` §③ (A-① … A-⑥) و§④ (A1 · A2). **التطبيقُ بالحرف:** بلا هدفٍ ولا وقف (نايف لم يضع).
- A-① شموعُ 4س = شموعُ 30 دقيقة نظاميّة (`adjusted=true` من Polygon) مجمَّعةٌ بـ`chart_id_tv.aggregate` **بالاسم** بحدَّي 09:30 و13:30 ونهايةِ 16:00.
- A-② SMA بسيطٌ (افتراضٌ مُعلَن: «متوسط» بلا «أسّيّ») · A-③ الذهبيُّ 50 فوق 200 الآن وليس فوقه قبلها · والموتُ عكسُه.
- A-④ أقلُّ من 201 شمعة ⟵ «لا يُقاس» لا «لا تقاطع».
- **سطرُ الكرت واليوميّ غيرُ موصولٍ** حتى عبور القبول وكلمة المالك «فعّل الذهبي» (يغيّر رسائلَ تلغرام قائمة) — `golden_line` جاهزةٌ نقيّة.

الأوضاع: `accept` (A1 · A2 على INTC) · `scan` (القائمة ∪ «تحت المتابعة» — **BASE2 لم يُضمّ بعد** ويُطبع ذلك حدًّا) · `trace` (رمز).
خارج الجذور · لا `LOGIC_VERSION` · لا يمسّ `Super_stock.py` · بلا تلغرام.
"""
import argparse
import datetime as dt
import json
import os
import sys

FAST_N, SLOW_N = 50, 200                     # A «تقاطع متوسط 50 مع متوسط 200» — `nayef_verbatim`
STARTS, END = (9 * 60 + 30, 13 * 60 + 30), 16 * 60   # A-① حدودُ 4س (09:30 · 13:30 · نهايةُ 16:00) — المالك «a30 بتقسيم 09:30»
HISTORY_FROM = "2025-01-01"                  # بدايةُ الجلب (‏≈440 شمعة 4س قبل نافذة A1) — engineering
WIN_A1 = ("2026-02-01", "2026-04-30")        # §④ A1 «≈ مارس 2026» — العقد
WIN_A2 = ("2026-09-01", "2026-10-22")        # §④ A2 «≈ أكتوبر 2026» حتى لقطة 10-22 — العقد
A1_PX, A2_PX, A2_LOW = (48.0, 52.0), (115.0, 120.0), 88.75   # أرقامُ نايف كما نقلها المالك (وصفٌ لا معيار)
UNSPEC = "غير محدّد في المصدر"


def log(m=""):
    print(m, flush=True)


# ── دوالُّ نقيّة ────────────────────────────────────────────────────────────────────────────────────────
def to_4h(b30):
    """A-① [[ثانية، o، h، l، c، v]] لشموع 30 دقيقة ⟵ شموعُ 4س بـ`chart_id_tv.aggregate` بالاسم (حدودُ 09:30 · 13:30 · نهايةُ 16:00)."""
    import chart_id_tv as CT
    return CT.aggregate(b30, list(STARTS), END)


def sma_series(values, n):
    """A-② المتوسّطُ الحسابيّ لآخر n قيمة لكلّ موضع · None قبل اكتمال n."""
    out, s = [], 0.0
    for i, x in enumerate(values):
        s += x
        if i >= n:
            s -= values[i - n]
        out.append(s / n if i >= n - 1 else None)
    return out


def gcrosses(bars, fast=FAST_N, slow=SLOW_N):
    """A-③ ⟵ (قابلٌ للقياس؟، [{j · ts · kind («golden»/«death») · px · f · s}]) — A-④ أقلُّ من slow+1 شمعة ⟵ (False، [])."""
    if len(bars) < slow + 1:
        return False, []
    closes = [b[4] for b in bars]
    f, s = sma_series(closes, fast), sma_series(closes, slow)
    out = []
    for j in range(1, len(bars)):
        if s[j - 1] is None:
            continue
        up, was = f[j] > s[j], f[j - 1] > s[j - 1]
        if up != was:
            out.append({"j": j, "ts": bars[j][0], "kind": "golden" if up else "death", "px": closes[j], "f": f[j], "s": s[j]})
    return True, out


def ny_day(ts):
    import tv_data as TV
    return TV.ny_day(ts)


def golden_line(state):
    """A-⑤ سطرُ العرض (نقيّ · **غيرُ موصول** حتى «فعّل الذهبي»): آخرُ تقاطعٍ أو «لا يُقاس» — بلا علامات مقارنة."""
    if not state or not state.get("measurable"):
        return "〰️ تقاطع 50/200 على 4س: لا يُقاس (أقلّ من 201 شمعة)"
    last = state.get("last")
    if not last:
        return None
    if last["kind"] == "golden":
        return f"⭐ تقاطع ذهبي 4س بتاريخ {last['day']} عند ${last['px']:g}"
    return f"💀 تقاطع موت 4س بتاريخ {last['day']} عند ${last['px']:g}"


# ── الشبكة ──────────────────────────────────────────────────────────────────────────────────────────────
def fetch_30m(net, sym, d0, d1):
    """شموعُ 30 دقيقة من Polygon (`adjusted=true`) ⟵ [[ثانية، o، h، l، c، v]] أو None (فاشلٌ-آمن · بالصفحات)."""
    from urllib.parse import quote
    j = net.poly(f"/v2/aggs/ticker/{quote(sym)}/range/30/minute/{d0}/{d1}", {"adjusted": "true", "sort": "asc", "limit": 50000})
    if j is None:
        return None
    res, nxt, pages = list(j.get("results") or []), j.get("next_url"), 0
    while nxt and pages < 20:
        k = net.poly_url(nxt)
        if k is None:
            return None
        res.extend(k.get("results") or [])
        nxt, pages = k.get("next_url"), pages + 1
    out = []
    for r in res:
        try:
            out.append([int(r["t"]) // 1000, float(r["o"]), float(r["h"]), float(r["l"]), float(r["c"]), float(r.get("v") or 0.0)])
        except (KeyError, TypeError, ValueError):
            continue
    return out


def state_of(net, sym, d1):
    b30 = fetch_30m(net, sym, HISTORY_FROM, d1)
    if b30 is None:
        return None
    b4 = to_4h(b30)
    ok, xs = gcrosses(b4)
    last = xs[-1] if xs else None
    return {"sym": sym, "n4h": len(b4), "measurable": ok, "crosses": xs, "bars": b4,
            "last": None if not last else {"kind": last["kind"], "day": ny_day(last["ts"]), "px": last["px"]}}


def mode_accept(net, d1="2026-10-22"):
    """§④ A1 وA2 على INTC: ذهبيٌّ في نافذة A1 · موتٌ في نافذة A2 (الاتّجاه) ⟵ والأسعارُ وأدنى إغلاقٍ بعد الموت وصفًا. ⟵ 0 · 1 · 4."""
    st = state_of(net, "INTC", d1)
    if st is None:
        log("⛔ INTC: تعذّرت شموعُ 30 دقيقة")
        return 4
    log(f"ℹ️ INTC: شموعُ 4س {st['n4h']} ({ny_day(st['bars'][0][0])} ⟵ {ny_day(st['bars'][-1][0])}) · قابلٌ للقياس {st['measurable']} · "
        f"التقاطعات {len(st['crosses'])}")
    for x in st["crosses"]:
        log(f"   {'⭐ ذهبي' if x['kind'] == 'golden' else '💀 موت'} {ny_day(x['ts'])} ${x['px']:g} · SMA50 {x['f']:.4g} · SMA200 {x['s']:.4g}")
    out = {"mode": "accept_a", "n4h": st["n4h"], "rows": []}
    ok_all = True
    for wid, kind, win, rng in (("A1", "golden", WIN_A1, A1_PX), ("A2", "death", WIN_A2, A2_PX)):
        hit = next((x for x in st["crosses"] if x["kind"] == kind and win[0] <= ny_day(x["ts"]) <= win[1]), None)
        ok_all = ok_all and hit is not None
        if hit is None:
            log(f"❌ {wid} لا {'ذهبيّ' if kind == 'golden' else 'موت'} في [{win[0]}، {win[1]}]")
            out["rows"].append({"id": wid, "ok": False})
            continue
        inside = rng[0] <= hit["px"] <= rng[1]
        extra = ""
        if wid == "A2":
            after = [b[4] for b in st["bars"] if b[0] > hit["ts"] and ny_day(b[0]) <= WIN_A2[1]]
            if after:
                mn = min(after)
                extra = f" · أدنى إغلاقٍ بعده حتى {WIN_A2[1]} ${mn:g} مقابل {A2_LOW} ({(mn / hit['px'] - 1) * 100:+.1f}%)"
        log(f"✅ {wid} {ny_day(hit['ts'])} ${hit['px']:g} · مقابل نطاق نايف {rng[0]:g}-{rng[1]:g} ({'داخله' if inside else 'خارجه'}){extra}")
        out["rows"].append({"id": wid, "ok": True, "day": ny_day(hit["ts"]), "px": hit["px"], "in_range": inside})
    out["ok"] = ok_all
    log(f"{'✅' if ok_all else '❌'} **القبول ② (الذراع أ):** {'A1 وA2 بالاتّجاه' if ok_all else 'لم يعبر — أين سقط مطبوعٌ أعلاه'}")
    log("GCROSS_JSON " + json.dumps(out, ensure_ascii=False, sort_keys=True))
    return 0 if ok_all else 1


def universe():
    """A-⑤ القائمة (`weekly_watchlist.json` النشطة) ∪ «تحت المتابعة» (`near_watch.json`) — **وBASE2 لم يُضمّ بعد** (حدٌّ مطبوع)."""
    syms = set()
    try:
        w = json.load(open("weekly_watchlist.json", encoding="utf-8"))
        syms |= {str(s.get("symbol") or "").upper() for s in w.get("stocks") or [] if s.get("symbol")}
    except (OSError, ValueError):
        pass
    try:
        syms |= {str(k).upper() for k in json.load(open("near_watch.json", encoding="utf-8"))}
    except (OSError, ValueError):
        pass
    return sorted(s for s in syms if s)


def mode_scan(net, d1):
    syms = universe()
    log(f"📋 المجتمع {len(syms)} (القائمة ∪ «تحت المتابعة») · ⚠️ BASE2 لم يُضمّ بعد")
    counts = {"golden": 0, "death": 0, "none": 0, "unmeasurable": 0, "failed": 0}
    for sym in syms:
        st = state_of(net, sym, d1)
        if st is None:
            counts["failed"] += 1
            continue
        if not st["measurable"]:
            counts["unmeasurable"] += 1
            continue
        if not st["last"]:
            counts["none"] += 1
            continue
        counts[st["last"]["kind"]] += 1
        today = st["last"]["day"] == d1
        log(f"{'🆕 ' if today else ''}${sym}: {golden_line(st)}")
    log(f"🩺 ذهبيّ آخرُه {counts['golden']} · موتٌ آخرُه {counts['death']} · بلا تقاطع {counts['none']} · لا يُقاس {counts['unmeasurable']} · "
        f"تعذّر {counts['failed']}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--mode", default="accept", choices=("accept", "scan", "trace"))
    p.add_argument("--date", default="")
    p.add_argument("--sym", default="INTC")
    a = p.parse_args(argv)
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        log("⛔ لا مفتاح Polygon — لا عمل (يُعلَن ولا يُكتَم)")
        return 2
    import vwap_momentum_live as V
    net = V.Net(key, (os.environ.get("SEC_CONTACT") or "").strip())
    d1 = a.date or dt.datetime.now(tz=V.NY).date().isoformat()
    if a.mode == "accept":
        return mode_accept(net, a.date or "2026-10-22")
    if a.mode == "scan":
        return mode_scan(net, d1)
    st = state_of(net, a.sym.upper(), d1)
    if st is None:
        log("⛔ تعذّرت الشموع")
        return 4
    log(f"${a.sym.upper()}: شموعُ 4س {st['n4h']} · {golden_line(st)}")
    for x in st["crosses"][-10:]:
        log(f"   {x['kind']} {ny_day(x['ts'])} ${x['px']:g}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
