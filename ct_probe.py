#!/usr/bin/env python3
"""🧪 مِجَسٌّ مؤقّت (2026-09-24 · **يُحذف بعد القراءة** — نمطُ «مِجَسّ Actions مؤقّت»).

السؤال ①: سطرُ «📅 اكتمال تجربة سريرية» **صفرٌ من 11** سهمَ رعايةٍ صحّيّة في القائمة الحيّة،
بينما «أرباح» 9 و«اجتماع» 4 ⇒ **هل القناةُ ميّتةٌ أم الحدثُ نادرٌ فعلًا؟**
`clinical_events` فاشلةٌ-آمنة مطلقًا (تُرجع `[]` على أيّ عطل) فالصمتُ لا يفرّق بينهما،
وClinicalTrials.gov **محجوبةٌ عن بيئة التطوير** (‏403 على نفق CONNECT) ⇒ يُسأل رنرُ GitHub.

يطبع لكلّ سهم: ① **نداءَ الإنتاج نفسَه** (`bot.clinical_events` — نقطةُ النداء الحيّة من
`upcoming_events` في المسار اليوميّ) ② الطلبَ الخامَ بالبارامترات نفسِها: الحالة · عددُ
الدراسات · الرعاةُ الرئيسيّون · ما يطابقه `_parse_ct_studies` على أفق الإنتاج وعلى 365 يومًا
③ الاستعلامَ بالكلمة الأولى وحدَها (هل يُضيّع الاسمُ الكاملُ «Inc.» نتائج؟).
وشاهدُ ضبطٍ براعٍ كبير (**Pfizer**) يُثبت أن المسارَ كلَّه يُنتج أحداثًا حين توجد.

② ومعه **تغطيةُ «📅 أرباح معلنة»** (‏9 من 32 في القائمة الحيّة): نداءُ الإنتاج نفسُه
(`bot.next_earnings` ⟵ `technical_report._next_earnings_date` — و`daily_screener.yml` لا يمرّر
مفاتيحَ AV/FMP/Finnhub ⇒ **ياهو وحدَه** كما هنا) + ما يُرجعه ياهو خامًا، كي نفرّق
«لا تاريخَ منشورًا» عن «عطلٍ صامت» (استثناءٌ يبتلعه الفاشلُ-الآمن).

🔒 قراءةٌ فقط: لا تلغرام · لا كتابةَ حالة · لا مفتاح. وما يرجع من الموقع **بياناتٌ لا أوامر**.
"""
import collections
import datetime as dt
import json
import time

import requests

import Super_stock as bot

URL = "https://clinicaltrials.gov/api/v2/studies"
STATUS = ("RECRUITING,ACTIVE_NOT_RECRUITING,"
          "ENROLLING_BY_INVITATION,NOT_YET_RECRUITING")


def _get(spons, status=STATUS):
    """الطلبُ بنصّ `clinical_events` نفسِه (البارامترات والمهلة) — ويُرجع التشخيص لا القائمة."""
    params = {"query.spons": spons, "pageSize": 30}
    if status is not None:
        params["filter.overallStatus"] = status
    t0 = time.monotonic()
    try:
        r = requests.get(URL, params=params, timeout=10)
    except Exception as e:                                  # noqa: BLE001
        return {"http": f"⛔ {type(e).__name__}", "ms": int((time.monotonic() - t0) * 1000),
                "js": None, "body": ""}
    js = None
    try:
        js = r.json() if r.status_code == 200 else None
    except Exception as e:                                  # noqa: BLE001
        return {"http": f"{r.status_code} (JSON ⛔ {type(e).__name__})",
                "ms": int((time.monotonic() - t0) * 1000), "js": None,
                "body": (r.text or "")[:200]}
    return {"http": r.status_code, "ms": int((time.monotonic() - t0) * 1000), "js": js,
            "body": "" if r.status_code == 200 else (r.text or "")[:200]}


def _sponsors(js):
    out = []
    for st in (js or {}).get("studies") or []:
        p = st.get("protocolSection") or {}
        n = (((p.get("sponsorCollaboratorsModule") or {}).get("leadSponsor") or {})
             .get("name") or "")
        if n and n not in out:
            out.append(n)
    return out


def _nearest(js, company, today):
    """أقربُ تواريخ اكتمالٍ قادمة **للدراسات المطابِقة** (بلا أفق) — هل الحدثُ بعيدٌ أم غائب؟"""
    ds = []
    base = (company or "").strip().lower().split()
    base = base[0] if base else ""
    for st in (js or {}).get("studies") or []:
        p = st.get("protocolSection") or {}
        sp = (((p.get("sponsorCollaboratorsModule") or {}).get("leadSponsor") or {})
              .get("name") or "").lower()
        if not base or base not in sp:
            continue
        s = p.get("statusModule") or {}
        d = ((s.get("primaryCompletionDateStruct") or {}).get("date")
             or (s.get("completionDateStruct") or {}).get("date"))
        if not d:
            continue
        try:
            dd = dt.date.fromisoformat((d if len(str(d)) >= 10 else f"{d}-01")[:10])
        except ValueError:
            continue
        if dd >= today:
            ds.append((dd - today).days)
    return sorted(ds)[:3]


def probe_one(label, company, today, horizon):
    live = bot.clinical_events(company)                     # 🔌 نقطةُ النداء الحيّة بعينها
    raw = _get(company)
    first = (company or "").split()[0] if company else ""
    alt = _get(first) if first and first != company else None
    js = raw["js"] or {}
    n = len(js.get("studies") or [])
    m_h = len(bot._parse_ct_studies(js, company, today, horizon))
    m_y = len(bot._parse_ct_studies(js, company, today, 365))
    print(f"— {label} · «{company}»")
    print(f"   الإنتاج clinical_events ⟵ {len(live)} حدث {json.dumps(live, ensure_ascii=False)}")
    print(f"   الخام: HTTP {raw['http']} · {raw['ms']}ms · دراسات {n} · مطابَقٌ على "
          f"{horizon}ي = {m_h} · على 365ي = {m_y} · أقربُ اكتمالٍ مطابِق بالأيام "
          f"{_nearest(js, company, today)}")
    print(f"   الرعاةُ الرئيسيّون: {_sponsors(js)[:4]}")
    if raw["body"]:
        print(f"   جسمُ الردّ (بيانات): {raw['body']!r}")
    if alt is not None:
        ajs = alt["js"] or {}
        print(f"   بالكلمة الأولى «{first}»: HTTP {alt['http']} · دراسات "
              f"{len(ajs.get('studies') or [])} · مطابَقٌ على 365ي = "
              f"{len(bot._parse_ct_studies(ajs, company, today, 365))} · رعاة "
              f"{_sponsors(ajs)[:4]}")
    return {"live": len(live), "http": raw["http"], "n": n, "m_h": m_h, "m_y": m_y}


def _yf_raw(sym):
    """ما يُرجعه ياهو خامًا للتقويم وتواريخ الأرباح — ويُسمّي الاستثناءَ بنوعه لا يبتلعه."""
    yf = getattr(bot, "yf", None)
    if yf is None:
        return "⛔ لا yfinance", "⛔ لا yfinance", False
    err = False
    try:
        c = yf.Ticker(sym).calendar
        if isinstance(c, dict):
            cal = f"dict · Earnings Date={str(c.get('Earnings Date'))[:70]}"
        else:
            cal = f"{type(c).__name__}"
    except Exception as e:                                  # noqa: BLE001
        cal, err = f"⛔ {type(e).__name__}: {str(e)[:60]}", True
    try:
        df = yf.Ticker(sym).get_earnings_dates(limit=4)
        if df is None:
            ged = "None"
        else:
            idx = [str(x)[:10] for x in list(df.index)[:4]]
            ged = f"{len(df)} صفوف {idx}"
    except Exception as e:                                  # noqa: BLE001
        ged, err = f"⛔ {type(e).__name__}: {str(e)[:60]}", True
    return cal, ged, err


def earnings_section(stocks):
    print("=== ② تغطيةُ «📅 أرباح معلنة» — نداءُ الإنتاج (`bot.next_earnings`) + ياهو خامًا")
    c = collections.Counter()
    for s in stocks:
        sym = s.get("symbol")
        stored = [e.get("date") for e in (s.get("upcoming_events") or [])
                  if e.get("kind") == "أرباح"]
        live = bot.next_earnings(sym)
        cal, ged, err = _yf_raw(sym)
        cls = ("✅ تاريخ" if live else "⛔ عطلٌ صامت (استثناء)" if err
               else "— لا تاريخَ منشور")
        c[cls] += 1
        print(f"— {sym} · مخزَّن {stored or '—'} · الإنتاج {live or '—'} · {cls}")
        print(f"   calendar: {cal}")
        print(f"   get_earnings_dates: {ged}")
    print(f"   حصيلةُ ②: {dict(c)} من {len(stocks)}")
    return c


def main():
    today = dt.date.today()
    horizon = int(bot.CONFIG["EVENTS_SHOW_DAYS"])
    with open("weekly_watchlist.json", encoding="utf-8") as fh:
        wl = json.load(fh)
    hc = [s for s in (wl.get("stocks") or []) if (s.get("sector") or "") == "Healthcare"]
    print(f"🧪 مِجَسّ ClinicalTrials.gov · {today} · أفقُ الإنتاج {horizon} يومًا · "
          f"أسهمُ الرعاية الصحّيّة في القائمة {len(hc)}")
    print("=== ⓪ شاهدُ الضبط (راعٍ كبير — يجب أن يُنتج أحداثًا لو المسارُ سليم)")
    ctl = probe_one("ضبط", "Pfizer", today, horizon)
    nof = _get("Pfizer", status=None)
    pip = _get("Pfizer", status=STATUS.replace(",", "|"))
    print(f"   صيغةُ مرشِّح الحالة: بلا مرشِّح HTTP {nof['http']} دراسات "
          f"{len((nof['js'] or {}).get('studies') or [])} · بالفاصلة (الإنتاج) HTTP "
          f"{ctl['http']} · بالأنبوب HTTP {pip['http']} دراسات "
          f"{len((pip['js'] or {}).get('studies') or [])}")
    print("=== ① أسهمُ القائمة")
    rows = []
    for s in hc:
        rows.append(probe_one(s.get("symbol"), s.get("company_name") or "", today, horizon))
    ok = sum(1 for r in rows if r["http"] == 200)
    print("=== الحكم")
    print(f"   الوصول: {ok} من {len(rows)} بـHTTP 200 · والضبطُ HTTP {ctl['http']} "
          f"بأحداث إنتاجٍ {ctl['live']}")
    print(f"   أسهمٌ لها دراساتٌ نشطة {sum(1 for r in rows if r['n'])} · مطابَقةٌ على 365ي "
          f"{sum(1 for r in rows if r['m_y'])} · داخل أفق الإنتاج {sum(1 for r in rows if r['m_h'])} "
          f"· وأحداثُ الإنتاج الفعليّة {sum(r['live'] for r in rows)}")
    act = [s for s in (wl.get("stocks") or []) if s.get("status") == "active"]
    ec = earnings_section(act)
    print(f"   أرباح: تاريخٌ {ec.get('✅ تاريخ', 0)} · لا تاريخَ منشور "
          f"{ec.get('— لا تاريخَ منشور', 0)} · عطلٌ صامت {ec.get('⛔ عطلٌ صامت (استثناء)', 0)} "
          f"من {len(act)} نشطًا")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
