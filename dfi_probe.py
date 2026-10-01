# -*- coding: utf-8 -*-
"""🧪 مِجَسٌّ مؤقّت (يُحذف قبل الدمج) — «سلامة البيانات: الطزاجة والإجراءات المؤسسيّة والكون» (أمرُ المالك 2026-10-01).

**قراءةٌ فقط:** لا تلغرام · لا كتابةَ حالة · لا Polygon · لا git. يقرأ ملفّات الحالة كما هي في الشجرة المسحوبة.
**المعاييرُ مكتوبةٌ هنا قبل أوّل تشغيل ولا تُعدَّل بعد رؤية رقم** — وكلٌّ منها «مُثبَتٌ / غيرُ مُثبَت» لا درجة:

- F1 «القديمُ يُقرأ يومًا»: مُثبَتٌ إن وُجد رمزٌ آخرُ شمعته في إطار الإنتاج (`download_history` · TradingView ثمّ ياهو) **أقدمُ من آخر
  جلسةٍ مكتملة** (`last_closed_session`) ويقبله `analyze_ticker` أو يدخل «تحت المتابعة» (`near_watch_measure` · مؤسَّس · خارجٌ ≤ 2)
  أو يطابق قراءةَ الرادار (`press_read` بنافذة التنبيه) — أي يصل مخرجًا بلا وسمِ «قديم».
- F2 «التقسيمُ بلا وسم»: مُثبَتٌ إن وُجد رمزٌ بتقسيمٍ **مؤكَّدٍ من مصدرٍ مستقلّ** (ياهو أو تقويم ناسداك) داخل نافذة `SPLIT_LOOKBACK_DAYS`
  ويظهر في مخرجٍ قائم (قسم «تحت المتابعة» المعروض · بِركة الرادار المطابقة · قبول الفرز) — المخرجاتُ اليوم بلا أيّ وسمِ إجراءٍ مؤسسيّ.
- F3 «الانفجارُ يُعاد اكتشافه»: مُثبَتٌ إن حمل سجلُّ `explosions` للرمز نفسِه صفّين فأكثر من «تجمّع» بتاريخَي انطلاقٍ مختلفين
  وتواريخِ رصدٍ داخل `EXPLOSION_RUN_LOOKBACK` جلسةً من بعضها (الحركةُ نفسُها تُسجَّل جديدةً كلَّ يوم).
- F4 «المتابعةُ القديمة تُعرَض حاضرة»: مُثبَتٌ إن عرض قسمُ «تحت المتابعة» (السلّتان بسقف العرض) صفًّا `last_seen` له أقدمُ من أحدث
  `last_seen` في الملفّ.
- F5 «تقسيمٌ غيرُ مسوًّى عند المصدر»: وصفيّ — عددُ أحداث التقسيم الحديثة التي يُظهر إطارُ TradingView أو ياهو عندها قفزةً غيرَ مسوّاة
  (`hunter_outcomes.unadjusted_jump` بالاسم). أيُّ واحدٍ ⇒ فحصُ «غيرُ مسوًّى» لازمٌ في طبقة التحقّق.
- X «التحقّقُ المتقاطع»: وصفيّ — اتّفاقُ ياهو وتقويم ناسداك على تاريخ التقسيم (±1 يوم) ونسبته، وتعذّرُ كلٍّ منهما بعدده.
"""
import collections
import datetime as dt
import json
import math
import os
import sys
import time

os.environ["SPLIT_SOURCE_REPAIR"] = "0"          # Polygon انتهى — المِجَسُّ لا يناديه
os.environ["BARS_SOURCE"] = "tradingview"        # مسارُ الإنتاج نفسُه
for _k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "POLYGON_API_KEY"):
    os.environ.pop(_k, None)                     # لا إرسالَ ولا Polygon ولو وُجدت

import requests                                  # noqa: E402
import Super_stock as S                          # noqa: E402
import hunter_outcomes as HO                     # noqa: E402
import press_radar as PR                         # noqa: E402

FOCUS = [s.strip().upper() for s in os.environ.get("DFI_FOCUS", "DLXY").split(",") if s.strip()]
NASDAQ_DAYS = int(os.environ.get("DFI_NASDAQ_DAYS", "45"))
SPLIT_CAP = int(os.environ.get("DFI_SPLIT_CAP", "700"))
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept": "application/json, text/plain, */*", "Origin": "https://www.nasdaq.com",
      "Referer": "https://www.nasdaq.com/"}


def log(*a):
    print(*a, flush=True)


def _iso(x):
    return str(x)[:10]


def nasdaq_splits(days):
    """تقويمُ ناسداك للتقسيمات — يجرّب الشكلين ويطبع البنية الحقيقيّة (فالمحلّلُ يُكتب من الشكل لا من الظنّ)."""
    out, shapes, fails = [], [], 0
    today = dt.date.today()
    urls = ["https://api.nasdaq.com/api/calendar/splits"]
    for k in range(days + 1):
        d = today - dt.timedelta(days=k)
        if d.weekday() < 5:
            urls.append(f"https://api.nasdaq.com/api/calendar/splits?date={d.isoformat()}")
    seen = set()
    for u in urls:
        try:
            r = requests.get(u, headers=UA, timeout=15)
            if r.status_code != 200:
                fails += 1
                if len(shapes) < 3:
                    shapes.append(f"{u} ⟵ HTTP {r.status_code}")
                continue
            j = r.json()
            data = (j or {}).get("data") or {}
            rows = data.get("rows") or (data.get("calendar") or {}).get("rows") or []
            if len(shapes) < 3:
                shapes.append(f"{u} ⟵ مفاتيح {list(data.keys())[:8]} · صفوف {len(rows)} · أوّل صفّ "
                              f"{json.dumps(rows[0], ensure_ascii=False)[:300] if rows else '—'}")
            for row in rows:
                key = json.dumps(row, sort_keys=True)
                if key in seen:
                    continue
                seen.add(key)
                out.append(row)
        except Exception as e:                                   # noqa: BLE001
            fails += 1
            if len(shapes) < 3:
                shapes.append(f"{u} ⟵ {type(e).__name__}: {str(e)[:120]}")
        time.sleep(0.25)
    return out, shapes, fails, len(urls)


def _parse_ratio(txt):
    """«1 : 5» ⟵ 0.2 (صيغةُ ياهو: جديدٌ ÷ قديم) · «5 : 1» ⟵ 5.0 · وإلّا None."""
    try:
        t = str(txt).replace("-", ":").replace("for", ":").replace("/", ":")
        a, b = [float(x.strip()) for x in t.split(":")[:2]]
        if a > 0 and b > 0:
            return a / b
    except Exception:                                            # noqa: BLE001
        return None
    return None


def _ndate(txt):
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%b %d, %Y"):
        try:
            return dt.datetime.strptime(str(txt).strip(), fmt).date().isoformat()
        except Exception:                                        # noqa: BLE001
            continue
    return None


def yahoo_recent_splits(sym, since_iso):
    sp = S._fetch_splits(sym)
    if sp is None:
        return None
    ev = []
    try:
        for d, v in sp.items():
            ds = d.date().isoformat() if hasattr(d, "date") else _iso(d)
            if ds >= since_iso and float(v) > 0:
                ev.append((ds, float(v)))
    except Exception:                                            # noqa: BLE001
        return None
    return sorted(ev)


def sessions_between(df, d_iso):
    return sum(1 for x in df.index if _iso(x) >= d_iso)


def main():
    t_start = time.time()
    now = dt.datetime.now(dt.timezone.utc)
    from zoneinfo import ZoneInfo
    ny = now.astimezone(ZoneInfo("America/New_York"))
    ry = now.astimezone(ZoneInfo("Asia/Riyadh"))
    exp = S.last_closed_session(now)
    log(f"⏰ UTC {now:%Y-%m-%d %H:%M} · نيويورك {ny:%Y-%m-%d %H:%M} (DST={bool(ny.dst())}) · الرياض {ry:%Y-%m-%d %H:%M}")
    log(f"⏰ آخر جلسةٍ مكتملة (last_closed_session) = {exp} · السابقة {S._prev_session(exp) if exp else None}")

    # ── X: تقويم ناسداك ──
    nrows, shapes, nfails, nurls = nasdaq_splits(NASDAQ_DAYS)
    log(f"\n## X — تقويمُ ناسداك للتقسيمات: {len(nrows)} صفًّا فريدًا من {nurls} طلبًا · تعذّر {nfails}")
    for s_ in shapes:
        log("   " + s_)
    nas = collections.defaultdict(list)
    for row in nrows:
        sym = str(row.get("symbol") or "").upper().strip()
        d = _ndate(row.get("executionDate") or row.get("payableDate") or row.get("exDate") or "")
        r = _parse_ratio(row.get("ratio"))
        if sym and d:
            nas[sym].append((d, r, row.get("ratio")))
    log(f"   رموزٌ بتقسيم في التقويم: {len(nas)}")

    # ── B: الكون والجلب كالإنتاج ──
    uni = S.get_universe()
    log(f"\n## B — الكون {len(uni)} (nasdaqlisted.txt حيًّا · بلا كاش)")
    wl = S.load_watchlist() or {}
    nw = S.load_near_watch() or {}
    extra = sorted({str(x.get("symbol") or "").upper() for k in ("stocks", "pullback") for x in (wl.get(k) or [])}
                   | set(nw) | set(FOCUS))
    not_in_uni = [s for s in extra if s and s not in set(uni)]
    log(f"   رموزُ الحالة خارج كون اليوم (مشطوب/مُعاد تسميته؟): {len(not_in_uni)} — {', '.join(not_in_uni[:30])}")
    syms = sorted(set(uni) | {s for s in extra if s})
    t0 = time.time()
    hist = S.download_history(syms)
    log(f"   ⏱️ الجلب {time.time() - t0:.0f}ث · {S._tv_bars_line(S.BARS_SOURCE_LAST) if S.BARS_SOURCE_LAST else '—'}")

    # ── F1: الطزاجة ──
    fresh, stale, future, padded = [], [], [], []
    by_src = collections.Counter()
    for s, df in hist.items():
        src = (getattr(df, "attrs", {}) or {}).get("bars_src") or "yahoo"
        by_src[src] += 1
        last = _iso(df.index[-1])
        if exp and last < exp:
            stale.append((s, last, src))
        elif exp and last > exp:
            future.append((s, last, src))
        else:
            fresh.append(s)
        if src == "yahoo":
            try:
                if float(df["Volume"].iloc[-1]) == 0.0:
                    padded.append((s, last))
            except Exception:                                    # noqa: BLE001
                pass
    log(f"\n## F1 — الطزاجة: إطارات {len(hist)} (المصدر {dict(by_src)}) · بشمعة الجلسة {len(fresh)} · أقدم {len(stale)} · "
        f"أحدث {len(future)} · ياهو بشمعةٍ محشوّة (حجم 0) {len(padded)}")
    gaps = collections.Counter(last for _, last, _ in stale)
    log(f"   تواريخُ آخر شمعة للأقدم: {sorted(gaps.items())[-12:]}")
    log(f"   أمثلة الأقدم: {[(s, l, src) for s, l, src in stale[:25]]}")
    log(f"   أمثلة الحشو: {padded[:15]}")
    edges = {}
    try:
        import envelope_scan as EV
        edges = EV.load_edges() or {}
    except Exception as e:                                       # noqa: BLE001
        log(f"   ⚠️ ظرفُ الكاتالوج تعذّر: {e}")
    reach = []
    for s, last, src in stale:
        df = hist[s]
        r = None
        try:
            r = S.analyze_ticker(s, df)
        except Exception:                                        # noqa: BLE001
            r = None
        nwm = None
        try:
            m = S.near_watch_measure(s, df, edges) if edges else None
            if m and S.near_watch_founded(m[0], edges) and len(m[1]) <= S.NEAR_WATCH_MAX_OUT:
                nwm = len(m[1])
        except Exception:                                        # noqa: BLE001
            nwm = None
        pr = None
        try:
            pr = PR.press_read(df, w=PR.ALERT_W)
        except Exception:                                        # noqa: BLE001
            pr = None
        if r or nwm is not None or pr:
            reach.append((s, last, src, "فرز" if r else "", f"متابعة{nwm}" if nwm is not None else "", "رادار" if pr else ""))
    log(f"   ⚖️ F1: أقدمُ يصل مخرجًا = {len(reach)} ⟵ {'مُثبَت' if reach else 'غيرُ مُثبَت'}")
    for row in reach[:40]:
        log(f"      {row}")

    # ── F4: المتابعة القديمة المعروضة ──
    if nw:
        newest = max((e.get("last_seen") or "") for e in nw.values() if isinstance(e, dict))
        inside, oversold = S.near_watch_buckets(nw)
        lim = max(1, int(S.NEAR_WATCH_SHOW) // 2)
        shown = inside[:lim] + oversold[:lim]
        old = [(e.get("symbol"), e.get("last_seen"), e.get("price")) for e in shown if (e.get("last_seen") or "") < newest]
        allold = sum(1 for e in nw.values() if isinstance(e, dict) and (e.get("last_seen") or "") < newest)
        log(f"\n## F4 — تحت المتابعة: {len(nw)} صفًّا · الأحدث last_seen={newest} · أقدم منه {allold} · "
            f"المعروضُ {len(shown)} منه قديم {len(old)} ⟵ {'مُثبَت' if old else 'غيرُ مُثبَت'}")
        log(f"   {old[:20]}")

    # ── F3: إعادة اكتشاف الانفجار ──
    ex = wl.get("explosions") or []
    by = collections.defaultdict(list)
    for e in ex:
        by[e.get("symbol")].append(e)
    dup_syms, extra_rows = [], 0
    look = int(S.CONFIG["EXPLOSION_RUN_LOOKBACK"])
    for s, rows in by.items():
        runs = sorted((r for r in rows if r.get("kind") == "تجمّع"), key=lambda r: r.get("date") or "")
        if len(runs) < 2:
            continue
        lch = {r.get("expl_date") for r in runs}
        try:
            span = (dt.date.fromisoformat(str(runs[-1].get("date"))[:10])
                    - dt.date.fromisoformat(str(runs[0].get("date"))[:10])).days
        except Exception:                                        # noqa: BLE001
            continue
        if len(lch) >= 2 and span <= look * 7 // 5 + 2:
            dup_syms.append((s, len(runs), [(r.get("date"), r.get("expl_date"), r.get("gain")) for r in runs]))
            extra_rows += len(runs) - 1
    log(f"\n## F3 — سجلّ الانفجارات {len(ex)} صفًّا · رموزٌ بإعادة اكتشاف {len(dup_syms)} · صفوفٌ زائدة {extra_rows} ⟵ "
        f"{'مُثبَت' if dup_syms else 'غيرُ مُثبَت'}")
    for row in sorted(dup_syms, key=lambda x: -x[1])[:15]:
        log(f"   {row}")

    # ── F2/F5: التقسيمات ──
    since = (dt.date.today() - dt.timedelta(days=int(S.CONFIG["SPLIT_LOOKBACK_DAYS"]))).isoformat()
    shown_nw = set()
    if nw:
        inside, oversold = S.near_watch_buckets(nw)
        lim = max(1, int(S.NEAR_WATCH_SHOW) // 2)
        shown_nw = {e.get("symbol") for e in inside[:lim] + oversold[:lim]}
    pstate = {}
    try:
        with open(PR.STATE_FILE, encoding="utf-8") as fh:
            pstate = json.load(fh)
    except Exception:                                            # noqa: BLE001
        pstate = {}
    pool, _cut = PR.build_pool(wl, {"symbols": dict((pstate or {}).get("symbols") or {})}, exp or dt.date.today().isoformat())
    accepted = set()
    for s, df in hist.items():
        try:
            if S.analyze_ticker(s, df):
                accepted.add(s)
        except Exception:                                        # noqa: BLE001
            pass
    log(f"\n## F2/F5 — مرشّحو الفحص: قبول الفرز اليوم {len(accepted)} · المعروض من المتابعة {len(shown_nw)} · بِركة الرادار {len(pool)}")
    cand = list(dict.fromkeys(list(FOCUS) + sorted(nas) + sorted(accepted) + sorted(shown_nw) + list(pool)
                              + sorted({x.get("symbol") for x in (wl.get("stocks") or []) + (wl.get("pullback") or [])})))
    cand = [c for c in cand if c][:SPLIT_CAP]
    yfail, ysplit, unadj_tv, agree, disagree, only_y, only_n = 0, {}, [], 0, [], [], []
    rows_out = []
    for s in cand:
        ev = yahoo_recent_splits(s, since)
        if ev is None:
            yfail += 1
            ev = []
        if ev:
            ysplit[s] = ev
        nev = [(d, r) for d, r, _ in nas.get(s, []) if d and d >= since]
        if ev or nev:
            # التحقّق المتقاطع (ياهو مقابل ناسداك)
            for d, r in ev:
                m = [x for x in nev if abs((dt.date.fromisoformat(x[0]) - dt.date.fromisoformat(d)).days) <= 1]
                if m and (m[0][1] is None or abs(math.log(m[0][1] / r)) < 0.05):
                    agree += 1
                elif m:
                    disagree.append((s, d, r, m[0]))
                elif nas:
                    only_y.append((s, d, r))
            for d, r in nev:
                if not any(abs((dt.date.fromisoformat(d) - dt.date.fromisoformat(x[0])).days) <= 1 for x in ev):
                    only_n.append((s, d, r))
            df = hist.get(s)
            evx = ev or [(d, r) for d, r in nev if r]
            un_tv = bool(df is not None and HO.unadjusted_jump(df, evx))
            if un_tv:
                unadj_tv.append((s, evx))
            last_ev = max(evx)[0] if evx else None
            n_after = sessions_between(df, last_ev) if (df is not None and last_ev) else None
            where = [w for w, cond in (("فرز", s in accepted), ("متابعة-معروضة", s in shown_nw), ("بِركة-الرادار", s in pool),
                                       ("قائمة", s in {x.get("symbol") for x in wl.get("stocks") or []}),
                                       ("ارتداد", s in {x.get("symbol") for x in wl.get("pullback") or []})) if cond]
            half = held = None
            try:
                if df is not None and last_ev:
                    spp = S._split_setup_probe(df, S._fetch_splits(s), dt.date.fromisoformat(_iso(df.index[-1])))
                    if spp:
                        half, held = spp.get("half"), (bool(spp.get("near_bottom")), bool(spp.get("held_ok")),
                                                       spp.get("rose_pct"))
            except Exception:                                    # noqa: BLE001
                pass
            rows_out.append((s, evx, n_after, round(float(df["Close"].iloc[-1]), 4) if df is not None else None,
                             half, held, un_tv, where))
    log(f"   ياهو: فُحص {len(cand)} · تعذّر {yfail} · بتقسيمٍ منذ {since} {len(ysplit)}")
    log(f"   X: اتّفاق ياهو/ناسداك {agree} · اختلاف {len(disagree)} {disagree[:8]} · ياهو وحدَه {len(only_y)} {only_y[:8]} · "
        f"ناسداك وحدَه {len(only_n)} {only_n[:8]}")
    reach2 = [r for r in rows_out if r[7]]
    log(f"   ⚖️ F2: تقسيمٌ حديث داخل مخرجٍ بلا وسم = {len(reach2)} ⟵ {'مُثبَت' if reach2 else 'غيرُ مُثبَت'}")
    for r in sorted(rows_out, key=lambda x: (-(len(x[7])), x[0]))[:60]:
        log(f"      {r[0]}: أحداث {r[1]} · جلسات بعد آخره {r[2]} · إغلاق {r[3]} · ÷2 {r[4]} · (قرب÷2، حافظ3، صعد%) {r[5]} · "
            f"TV غيرُ مسوًّى {r[6]} · يظهر في {r[7]}")
    log(f"   ⚖️ F5: TradingView غيرُ مسوًّى عند حدثٍ حديث = {len(unadj_tv)} {unadj_tv[:12]}")

    # ── F6 (وصفيّ): الفلوت بعد التقسيم — ذاكرةُ الشركات (بلا تاريخ) مقابل ياهو الحيّ مقابل ماسح TradingView ──
    try:
        import tv_data as TV
        sn = TV.scan(["name", "float_shares_outstanding"]) or []
        tvf = {}
        for row in sn:
            try:
                tvf[str(row.get("name") or "").upper()] = float(row.get("float_shares_outstanding") or 0) or None
            except Exception:                                    # noqa: BLE001
                continue
    except Exception as e:                                       # noqa: BLE001
        tvf = {}
        log(f"   F6: ماسح TradingView تعذّر: {e}")
    try:
        with open(S.COMPANY_FILE, encoding="utf-8") as fh:
            cc = json.load(fh)
    except Exception:                                            # noqa: BLE001
        cc = {}
    f6 = []
    for r in rows_out:
        s = r[0]
        if not any(x[1] and x[1] < 1.0 for x in r[1]):
            continue                                             # العكسيّ وحدَه يُصغّر الفلوت
        try:
            yfl = S._yahoo_float(s, strict=True)
        except Exception:                                        # noqa: BLE001
            yfl = None
        cfl = (cc.get(s) or {}).get("float")
        nwf = (S.load_near_watch_float() or {}).get(s, {}).get("float") if hasattr(S, "load_near_watch_float") else None
        f6.append((s, r[1], cfl, yfl, tvf.get(s), nwf))
    log(f"\n## F6 — الفلوت بعد التقسيم العكسيّ (ذاكرة · ياهو حيّ · ماسح TV · مخزن المتابعة): {len(f6)}")
    for row in f6[:40]:
        log(f"   {row}")

    # ── التركيز ──
    for s in FOCUS:
        df = hist.get(s)
        log(f"\n## 🔎 {s}")
        if df is None:
            log("   لا إطار")
            continue
        log(f"   المصدر {(df.attrs or {}).get('bars_src') or 'yahoo'} · آخر شمعة {_iso(df.index[-1])} · {len(df)} شمعة")
        for ix, row in df.tail(30).iterrows():
            log(f"   {_iso(ix)} o={row['Open']:.4f} h={row['High']:.4f} l={row['Low']:.4f} c={row['Close']:.4f} v={row['Volume']:.0f}")
        sp = S._fetch_splits(s)
        log(f"   تقسيمات ياهو: {list(sp.items())[-6:] if sp is not None else 'تعذّر'} · ناسداك {nas.get(s)}")
        try:
            yd = S._download_chunk([s], (dt.date.today() - dt.timedelta(days=90)).isoformat())
            ydf = {}
            S._extract_into(ydf, yd, [s]) if yd is not None else None
            yy = ydf.get(s)
            if yy is not None:
                for ix, row in yy.tail(15).iterrows():
                    log(f"   ياهو {_iso(ix)} o={row['Open']:.4f} h={row['High']:.4f} l={row['Low']:.4f} c={row['Close']:.4f} v={row['Volume']:.0f}")
        except Exception as e:                                   # noqa: BLE001
            log(f"   ياهو تعذّر: {e}")
        S._REJECT_REASONS.pop(s, None)
        r = S.analyze_ticker(s, df)
        log(f"   analyze_ticker: {'مقبول' if r else 'مرفوض ' + str(S._REJECT_REASONS.get(s))}")
        try:
            m = S.near_watch_measure(s, df, edges)
            if m:
                keys = ("price", "rsi_now", "drop_pct", "spike_pct", "base_range_pct", "dollar_vol")
                log(f"   near_watch: خارج {m[1]} · مؤسَّس {S.near_watch_founded(m[0], edges)} · "
                    f"{ {k: m[0].get(k) for k in keys if k in m[0]} }")
        except Exception as e:                                   # noqa: BLE001
            log(f"   near_watch تعذّر: {e}")
        log(f"   press_read: {PR.press_read(df, w=PR.ALERT_W)}")
        log(f"   explosions: {[e for e in S.scan_explosions({s: df})]}")
        log(f"   سجلّ الانفجارات المخزَّن: {[(e.get('date'), e.get('expl_date'), e.get('gain'), e.get('kind')) for e in by.get(s, [])]}")
    log(f"\n⏱️ المجموع {time.time() - t_start:.0f}ث")
    return 0


if __name__ == "__main__":
    sys.exit(main())
