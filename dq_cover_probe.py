# -*- coding: utf-8 -*-
"""🧪🛡️ مِجَسٌّ مؤقّت (يُحذف قبل الدمج) — «تغطيةُ سلامة البيانات على الأدوات غير الموصولة» (حدُّ الصدق ⑥-1 في
`data_integrity_result.md` · التفويضُ الكامل ④-4: «حدود الصدق المفتوحة القابلة للقياس»).

**قراءةٌ فقط:** لا تلغرام · لا كتابةَ حالة · لا Polygon · لا git. يقرأ ملفّات الحالة كما هي في الشجرة المسحوبة، ويقرأ سجلّاتِ
تشغيلات الأدوات عبر واجهة GitHub (`GITHUB_TOKEN` · `actions: read`). **المعاييرُ مكتوبةٌ هنا قبل أوّل تشغيلٍ ولا تُعدَّل بعد رؤية رقم.**

السؤال: هل وصل رمزٌ تحكم عليه بوّابةُ `data_quality` (بالمصدرين · بأثرٍ رجعيٍّ على جلسة المخرَج) **بالحجز أو المنع** إلى **مخرَجٍ
فعليٍّ** لأداةٍ غيرِ موصولة؟ ⟵ يُوصَل ما ثبت عطلُه وحدَه (الوصلُ بلا عطلٍ مقيس رفضٌ جديدٌ بلا سند).

- D1 «شروطك الثلاثة»: المجتمع = الأسطرُ المرقّمة («N. $رمز ·» = المطابقون) في رسائلها **المُرسَلة** (سجلٌّ بلا «TC_DRY=1 — طُبعت
  ولم تُرسل») بجلسة كلٍّ منها («— إغلاق YYYY-MM-DD»). **مُثبَتٌ** ⇔ زوجٌ (رمز · جلسة) واحدٌ على الأقلّ حكمُه «quarantine» أو «block».
  وصفيٌّ لا يحكم: مجتمعُ «ثابتٌ وغيرُ منفجر ∧ فلوتٌ تحت الحدّ أو مجهول» (c4) لآخر جلسةٍ مكتملة بإعادة المسح نفسِه (`stage_scan`).
- D2 الصيّادون (من `hunter_ledger.jsonl` — يُدرَج **بعد** الإرسال): النهج (`method`) **مُثبَتٌ** ⇔ رمزٌ مُدرَجٌ حكمُه «quarantine» أو
  «block» · الفلترة (`split_filter` — التقسيمُ حدثُها المؤسِّس بالبناء فالحجزُ بعده ليس عطلًا) **مُثبَتٌ** ⇔ رمزٌ مُدرَجٌ بحالة بيانات:
  SPLIT_UNADJUSTED أو SOURCE_CONFLICT · والظرفُ صامتٌ بقرار (صفر `send_telegram`) ⟵ خارج المجتمع · والمقسّمُ **محميّ** ⟵ يُقاس
  بمعيار الفلترة نفسِه **وصفًا** ولا يُوصَل.
- D3 المتتبَّعون (المراقبُ اللحظيّ `monitor_live_events` يقارن المستوياتِ المخزَّنة بسعر اليوم **بلا تسوية**): المجتمع = القائمةُ النشطة
  والارتداد في `weekly_watchlist.json` الآن. **مُثبَتٌ** ⇔ مدخلٌ واحدٌ على الأقلّ له تقسيمٌ غيرُ طفيف (المصدران) بعد `added`.
- D4 الأدواتُ عند الطلب (فحصُ اليد `HAND_CHECK` · الفحصُ اليدويّ `ANALYZE` · التقريرُ الفنيّ `TICKER`): المجتمع = رموزُ تشغيلاتها
  الناجحة منذ 2026-09-01 بجلسة «آخرُ جلسةٍ مكتملةٍ وقتَ التشغيل». **مُثبَتٌ** ⇔ تشغيلةٌ واحدةٌ على الأقلّ رمزُها حكمُه «quarantine»
  أو «block» (ومخرجاتُها بلا سطرِ سلامةٍ أصلًا ⇒ لم يُفصَح).
- D5 «هنا الدخول» (`OE_SOURCE` مطفأ): المجتمع = سجلّاتُ `op_entry_state.json` بتاريخٍ بعد 2026-09-29. **مُثبَتٌ** ⇔ سجلٌّ واحد.

الحكمُ الرجعيّ يُبنى من الحالات القابلة للاستعادة وحدَها: CORPORATE_ACTION_PENDING · RECENT_SPLIT · SPLIT_UNADJUSTED · SOURCE_CONFLICT
(تعارضُ نسبة المصدرين) · CORPORATE_ACTION_ANNOUNCED — وما سواها (STALE · INCOMPLETE · SYMBOL_CHANGED · MARKET_CLOSED · تعارضُ
الإغلاق) لا يُستعاد (شموعُ اليوم وكونُ اليوم غيرُ ما كان) فيُطبع ولا يحكم · **إلّا لآخر جلسةٍ مكتملة فكلُّ الحالات حاضرة**.
وتقويمُ ناسداك 45 يومًا (ما قبله ياهو وحدَه) — حدٌّ يُطبع.

🐞 ملحقٌ مؤرَّخ (2026-10-01 · بعد التشغيلة الأولى `36875846552` · **المعاييرُ لم تُمَسّ**): قرأت سجلّاتِ التشغيلات بترميزٍ
مُخمَّن فشُوِّهت العربيّةُ وجاء D1 «0 من 0» — وهو **لا قياس** لا «غيرُ مُثبَت» ⟵ أُصلح فكُّ الترميز (UTF-8 صراحةً) وأُضيف حارسُ
«⛔ لا قياس» حين يخلو المجتمع · وD2-D5 من تلك التشغيلة لا يمسّها العيبُ (قراءتُها إنجليزيّةٌ أو من ملفّات الحالة) وتُعاد هنا كما هي.

التنبّؤات (تُنشَر ولو خابت): (أ) SXTC يحمل تقسيمًا عكسيًّا داخل النافذة (🩹 ×8.1 في سجلّ جلسة 09-28) · (ب) D1 بلا ترجيح ·
(ج) D2: النهجُ بلا مُدرَج والفلترةُ بلا عطل · (د) D3: صفرُ مدخلٍ مصاب (كما قِيس قبل #519) · (هـ) D4: تشغيلةٌ واحدةٌ على الأقلّ
على رمزٍ بحكم «quarantine» · (و) D5: صفر.
"""
import collections
import datetime as dt
import json
import os
import re
import sys
import time
from zoneinfo import ZoneInfo

os.environ["SPLIT_SOURCE_REPAIR"] = "0"          # Polygon انتهى — المِجَسُّ لا يناديه
os.environ["BARS_SOURCE"] = "tradingview"        # مسارُ الإنتاج نفسُه
os.environ["DQ_GATE"] = "1"                      # البوّابةُ مُشعَلةٌ صراحةً (المِجَسُّ يقيس حكمَها)
for _k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "POLYGON_API_KEY"):
    os.environ.pop(_k, None)                     # لا إرسالَ ولا Polygon ولو وُجدت

import requests                                  # noqa: E402

import data_quality as DQ                        # noqa: E402
import Super_stock as S                          # noqa: E402


def _no_send(*_a, **_k):
    raise RuntimeError("المِجَسُّ لا يرسل")


S.send_telegram = _no_send                       # حارسٌ ثانٍ فوق نزع الأسرار
S.git_save = lambda *_a, **_k: None              # ولا كتابةَ في المستودع

NY = ZoneInfo("America/New_York")
SINCE_RUNS = "2026-09-01"                        # D4 · والتشغيلاتُ قبلها خارج نافذة ناسداك
SINCE_TC = "2026-09-26"                          # أوّلُ تشغيلةٍ لـ«شروطك الثلاثة»
OE_AFTER = "2026-09-29"
RETRO_OK = {DQ.CORPORATE_ACTION_PENDING, DQ.RECENT_SPLIT, DQ.SPLIT_UNADJUSTED, DQ.SOURCE_CONFLICT,
            DQ.CORPORATE_ACTION_ANNOUNCED, DQ.VALID}
DATA_STATES = {DQ.SPLIT_UNADJUSTED, DQ.SOURCE_CONFLICT}
FAULT_ACTIONS = {"quarantine", "block"}
GH = "https://api.github.com"
REPO = os.environ.get("GITHUB_REPOSITORY") or "sam72x1/Super_Stocks"
TOK = os.environ.get("GITHUB_TOKEN") or ""
HDR = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
if TOK:
    HDR["Authorization"] = f"Bearer {TOK}"


def log(msg=""):
    print(msg, flush=True)


# ─────────────────────────── سجلّاتُ التشغيلات ───────────────────────────
def gh(path, **params):
    r = requests.get(f"{GH}/repos/{REPO}/{path}", headers=HDR, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def runs_of(wf, since):
    out, page = [], 1
    while page < 10:
        rs = gh(f"actions/workflows/{wf}/runs", per_page=100, page=page, created=f">={since}").get("workflow_runs") or []
        out += rs
        if len(rs) < 100:
            break
        page += 1
    return out


LOG_DIAG = {}


def job_texts(run_id):
    """نصوصُ سجلّات جوبات التشغيلة — **تُفكّ UTF-8 صراحةً** (🐞 التشغيلةُ الأولى `36875846552` قرأتها بـ`r.text` فحكم الترميزُ
    المُخمَّن من ترويسة التخزين ⟵ العربيّةُ مشوَّهة وD1 «0 من 0» بلا قياس · والإنجليزيّةُ سليمة فنجا D4)."""
    js = gh(f"actions/runs/{run_id}/jobs", per_page=50, filter="all").get("jobs") or []
    out = []
    for j in js:
        try:
            r = requests.get(f"{GH}/repos/{REPO}/actions/jobs/{j['id']}/logs", headers=HDR, timeout=60)
            if not LOG_DIAG:
                LOG_DIAG.update({"content_type": r.headers.get("Content-Type"), "guessed": r.encoding,
                                 "ok": r.ok, "status": r.status_code})
            out.append((j.get("name") or "", r.content.decode("utf-8", "replace") if r.ok else ""))
        except Exception:                                        # noqa: BLE001
            out.append((j.get("name") or "", ""))
    return out


TC_LINE = re.compile(r"^\S+Z\s+‏?\s*(\d+)\.\s+\$([A-Z][A-Z0-9.\-]*)\s+·", re.M)
TC_BULLET = re.compile(r"^\S+Z\s+‏?\s*•\s+\$([A-Z][A-Z0-9.\-]*)\s+·", re.M)
TC_SESS = re.compile(r"شروطك الثلاثة(?:</b>)?\s*—\s*إغلاق\s+(\d{4}-\d{2}-\d{2})")
TC_DRY = "TC_DRY=1 — طُبعت ولم تُرسل"
ENV_TICKER = re.compile(r"^\S+Z\s+(HAND_CHECK|ANALYZE|TICKER):\s*([A-Za-z][A-Za-z0-9.\-]*)\s*$", re.M)


def collect_tc():
    """[(رمز, جلسة, تشغيلة)] للمطابقين في الرسائل المُرسَلة · و[(رمز, جلسة)] للمذكورين بلا مطابقة (وصف)."""
    pairs, bullets, seen_runs = [], [], []
    for r in sorted(runs_of("three_cond_daily.yml", SINCE_TC), key=lambda x: x["id"]):
        for _name, txt in job_texts(r["id"]):
            m = TC_SESS.search(txt or "")
            if not m:
                continue
            sent = TC_DRY not in txt
            seen_runs.append((r["id"], r.get("event"), m.group(1), "مُرسَلة" if sent else "جافّة"))
            if not sent:
                continue
            for _i, sym in TC_LINE.findall(txt):
                pairs.append((sym, m.group(1), r["id"]))
            for sym in TC_BULLET.findall(txt):
                bullets.append((sym, m.group(1), r["id"]))
    return pairs, bullets, seen_runs


def collect_ondemand():
    """[(أداة, رمز, جلسةُ وقتِ التشغيل, تشغيلة)] لتشغيلاتٍ ناجحة منذ `SINCE_RUNS`."""
    out = []
    for wf in ("hand_check.yml", "analyze.yml", "technical.yml"):
        for r in sorted(runs_of(wf, SINCE_RUNS), key=lambda x: x["id"]):
            if r.get("conclusion") != "success":
                continue
            t0 = dt.datetime.fromisoformat(str(r["created_at"]).replace("Z", "+00:00"))
            sess = S.last_closed_session(now=t0)
            tick = None
            for _name, txt in job_texts(r["id"]):
                m = ENV_TICKER.search(txt or "")
                if m:
                    tick = m.group(2).upper()
                    break
            if tick and sess:
                out.append((wf.split(".")[0], tick, sess, r["id"]))
    return out


# ─────────────────────────── التقييمُ الرجعيّ ───────────────────────────
def asof(sym, sess, hist, latest):
    """حكمُ البوّابة على `sym` كما لو كانت الجلسةُ `sess` آخرَ جلسةٍ مكتملة — الإطارُ مقصوصٌ حتى الجلسة و«اليوم» بعدها."""
    df = hist.get(sym)
    if df is None or not len(df):
        return {"symbol": sym, "state": "NO_BARS", "states": [], "action": "?", "reasons": ["لا شموع اليوم"], "split": None}
    t = df[[str(i)[:10] <= sess for i in df.index]]
    today = dt.date.fromisoformat(sess) + dt.timedelta(days=1)
    xc = None
    if sess == latest:
        try:
            xc = S.dq_close_xcheck([sym], {sym: t}).get(sym)
        except Exception:                                        # noqa: BLE001
            xc = None
    try:
        return S.dq_assess(sym, t, sess, today=today, xclose=xc)
    except Exception as e:                                       # noqa: BLE001
        return {"symbol": sym, "state": "ERROR", "states": [], "action": "?", "reasons": [type(e).__name__], "split": None}


def retro_action(a, sess, latest):
    """الإجراءُ من الحالات القابلة للاستعادة وحدَها (وكلُّها لآخر جلسة) · والتعارضُ السعريّ لا يُستعاد قبلها."""
    pol = DQ.policy_map()
    sts = list(a.get("states") or [])
    if sess != latest:                    # والتعارضُ قبلها نسبةُ المصدرين وحدَها (الإغلاقُ لا يُقارَن إلّا لآخر جلسة · `asof`)
        sts = [s for s in sts if s in RETRO_OK]
    acts = [pol.get(s, "warn") for s in sts] or ["allow"]
    sev = {"allow": 0, "warn": 1, "quarantine": 2, "block": 3}
    return max(acts, key=lambda x: sev.get(x, 0))


def fmt(a):
    sp = a.get("split") or {}
    spt = ""
    if sp:
        spt = (f" · تقسيم {sp.get('date')} نسبة {sp.get('ratio')} ({sp.get('kind')}) · بعده {sp.get('sessions_since')} جلسة"
               + (f" · الوصفة: اكتملت {sp.get('settled_day')}" if sp.get("settled") else
               (f" · الوصفة: لم تكتمل (÷2 {sp.get('half')} · ضرب {sp.get('hit')} · حافظ {sp.get('held')})" if "settled" in sp else "")))
    return (f"{a.get('state')} → {a.get('action')} · الحالات {a.get('states')}{spt} · "
            + " | ".join(str(x) for x in (a.get("reasons") or []))[:300])


def main():
    t_start = time.time()
    latest = S.last_closed_session()
    log(f"🕗 آخرُ جلسةٍ مكتملة {latest} · المستودع {REPO} · رمزٌ للواجهة {'نعم' if TOK else 'لا'}")
    verdict = collections.OrderedDict()
    pred = collections.OrderedDict()

    # ── المجتمعات ──
    try:
        tc_pairs, tc_bullets, tc_runs = collect_tc()
    except Exception as e:                                       # noqa: BLE001
        tc_pairs, tc_bullets, tc_runs = [], [], []
        log(f"⛔ D1: سجلّاتُ «شروطك الثلاثة» تعذّرت ({type(e).__name__}: {e})")
    log(f"📬 D1 تشغيلات «شروطك الثلاثة» منذ {SINCE_TC}: {len(tc_runs)}")
    for x in tc_runs:
        log(f"   {x[0]} · {x[1]} · جلسة {x[2]} · {x[3]}")
    _first = {}
    for s, d, rid in tc_pairs:
        _first.setdefault((s, d), rid)
    tc_pairs = sorted(_first.items())
    log(f"   أزواجُ المطابقين المُرسَلة (رمز · جلسة · تشغيلةٌ أولى): {len(tc_pairs)} — "
        + " · ".join(f"{s}@{d}" for (s, d), _ in tc_pairs))
    log(f"   المذكورون بلا مطابقة (أقسامُ «•» القديمة · وصف): {len({(s, d) for s, d, _ in tc_bullets})}")

    try:
        od = collect_ondemand()
    except Exception as e:                                       # noqa: BLE001
        od = []
        log(f"⛔ D4: سجلّاتُ الأدوات عند الطلب تعذّرت ({type(e).__name__}: {e})")
    log(f"🕵️ D4 تشغيلاتٌ ناجحة بعد {SINCE_RUNS}: {len(od)} — "
        + " · ".join(f"{t}:{s}@{d}" for t, s, d, _ in od))

    ledger = []
    try:
        with open("hunter_ledger.jsonl", encoding="utf-8") as f:
            ledger = [json.loads(ln) for ln in f if ln.strip()]
    except Exception as e:                                       # noqa: BLE001
        log(f"⛔ D2: السجلّ تعذّر ({type(e).__name__})")
    led = {h: [(r["symbol"], r["session"]) for r in ledger if r.get("hunter") == h and r.get("kind") == "candidate"]
           for h in ("method", "split_filter", "split", "envelope")}
    log("🪝 D2 السجلّ: " + " · ".join(f"{h} {len(v)}" for h, v in led.items()))

    wl = {}
    try:
        with open("weekly_watchlist.json", encoding="utf-8") as f:
            wl = json.load(f)
    except Exception as e:                                       # noqa: BLE001
        log(f"⛔ D3: القائمة تعذّرت ({type(e).__name__})")
    tracked = [("stocks", e) for e in (wl.get("stocks") or []) if e.get("status", "active") == "active"]
    tracked += [("pullback", e) for e in (wl.get("pullback") or [])]
    log(f"👁️ D3 المتتبَّعون: نشطٌ {sum(1 for k, _ in tracked if k == 'stocks')} · ارتداد "
        f"{sum(1 for k, _ in tracked if k == 'pullback')}")

    oe_n = 0
    try:
        with open("op_entry_state.json", encoding="utf-8") as f:
            oe = json.load(f)
        oe_n = sum(1 for v in (oe or {}).values()
                   if isinstance(v, dict) and str(v.get("date") or v.get("day") or "")[:10] > OE_AFTER)
    except Exception as e:                                       # noqa: BLE001
        log(f"⛔ D5: الحالة تعذّرت ({type(e).__name__})")

    # ── D1 الوصفيّ: إعادةُ المسح نفسِه لآخر جلسة ──
    c4 = []
    try:
        import three_cond_daily as TC
        st = TC.stage_scan(now=dt.datetime.now(tz=NY))
        rows = st.get("rows") or {}
        c4 = sorted(s for s, r in rows.items()
                    if r.get("gate") == "ok" and (r.get("fl") is None or r["fl"] < TC.OPL.FLOAT_OWNER))
        log(f"🔁 D1 وصفيّ: جلسة {st.get('sess')} · c4 = {len(c4)}: {' · '.join(c4)}"
            + (f" · ⛔ {st.get('fail')}" if st.get("fail") else ""))
    except Exception as e:                                       # noqa: BLE001
        log(f"⛔ D1 الوصفيّ تعذّر ({type(e).__name__}: {e})")

    # ── الشموعُ والتقويم ──
    syms = sorted({s for (s, _), _ in tc_pairs} | {s for _, s, _, _ in od} | {s for v in led.values() for s, _ in v
                                                                            if v is not led["envelope"]}
                  | {e.get("symbol") for _, e in tracked if e.get("symbol")} | set(c4))
    if not S._DQ_UNIVERSE["set"]:
        try:
            S.get_universe()
        except Exception as e:                                   # noqa: BLE001
            log(f"⚠️ الكون تعذّر ({type(e).__name__}) — SYMBOL_CHANGED لا يُقاس")
    cal = S.dq_nasdaq_events()
    log(f"📅 تقويمُ ناسداك: {'تعذّر' if cal is None else f'{len(cal)} رمزًا'}")
    t0 = time.time()
    hist = S.download_history(syms) if syms else {}
    log(f"📺 الشموع: {len(hist)} من {len(syms)} في {time.time() - t0:.0f}ث · "
        f"{S._tv_bars_line(S.BARS_SOURCE_LAST) if getattr(S, 'BARS_SOURCE_LAST', None) else '—'}")

    # ── D1 ──
    log("\n═══ D1 «شروطك الثلاثة» ═══")
    d1_bad = []
    for (s, d), rid in tc_pairs:
        a = asof(s, d, hist, latest)
        act = retro_action(a, d, latest)
        log(f"   {s}@{d} (تشغيلة {rid}) · رجعيّ {act} · {fmt(a)}")
        if act in FAULT_ACTIONS:
            d1_bad.append(f"{s}@{d}:{act}")
    c4_cnt = collections.Counter()
    for s in c4:
        a = asof(s, latest, hist, latest)
        c4_cnt[a.get("action")] += 1
        if a.get("action") != "allow":
            log(f"   c4 {s}@{latest} · {fmt(a)}")
    sent_runs = sum(1 for x in tc_runs if x[3] == "مُرسَلة")
    if not tc_pairs:                         # ⛔ لا مجتمع ⟵ «لا قياس» لا «غيرُ مُثبَت» (لا يُدّعى غيابُ عطلٍ لم يُفحَص)
        verdict["D1"] = (None, f"⛔ لا قياس — تشغيلاتٌ بجلسةٍ مقروءة {len(tc_runs)} (مُرسَلة {sent_runs}) · أزواج 0 · "
                               f"ترميزُ السجلّ {LOG_DIAG} · وصفيّ c4 ({len(c4)}): {dict(c4_cnt)}")
    else:
        verdict["D1"] = (bool(d1_bad), f"{len(d1_bad)} من {len(tc_pairs)} زوجًا (من {sent_runs} رسالةً مُرسَلة) — "
                                       f"{' · '.join(d1_bad) or '—'} · وصفيّ c4 ({len(c4)}): {dict(c4_cnt)}")

    # ── D2 ──
    log("\n═══ D2 الصيّادون ═══")
    m_bad, f_bad, sp_desc = [], [], []
    for s, d in led["method"]:
        a = asof(s, d, hist, latest)
        act = retro_action(a, d, latest)
        log(f"   method {s}@{d} · رجعيّ {act} · {fmt(a)}")
        if act in FAULT_ACTIONS:
            m_bad.append(f"{s}@{d}")
    for name, lst, out in (("split_filter", led["split_filter"], f_bad), ("split", led["split"], sp_desc)):
        for s, d in lst:
            a = asof(s, d, hist, latest)
            data = sorted(set(a.get("states") or []) & DATA_STATES)
            log(f"   {name} {s}@{d} · بيانات {data or '—'} · {fmt(a)}")
            if data:
                out.append(f"{s}@{d}:{'+'.join(data)}")
    verdict["D2"] = (bool(m_bad or f_bad),
                     f"النهج {len(led['method'])} مُدرَجًا · عطل {len(m_bad)} {m_bad or ''} · الفلترة {len(led['split_filter'])} · "
                     f"عطلُ بيانات {len(f_bad)} {f_bad or ''} · المقسّم (وصفٌ لا وصل) {len(led['split'])} · بحالة بيانات "
                     f"{len(sp_desc)} {sp_desc or ''}")

    # ── D3 ──
    log("\n═══ D3 المتتبَّعون ═══")
    d3_bad = []
    for kind, e in tracked:
        s = e.get("symbol")
        added = str(e.get("added") or "")[:10]
        if not s or not added:
            continue
        try:
            union, conf, _notes = S.dq_split_events(s)
        except Exception as ex:                                  # noqa: BLE001
            union, conf = None, []
            log(f"   {s} · تعذّر ({type(ex).__name__})")
        after = [(d, r) for d, r in (union or []) if d > added and r and not DQ.is_minor(r)]
        unk = [d for d, r in (union or []) if d > added and not r]
        if after or unk or conf:
            df = hist.get(s)
            lp = float(df["Close"].iloc[-1]) if df is not None and len(df) else None
            log(f"   {kind} {s} · أُضيف {added} · تقسيمٌ بعده {after or '—'} · بنسبةٍ مجهولة {unk or '—'} · تعارض {conf or '—'} · "
                f"السعر {lp} · الوقف المخزَّن {e.get('stop')} · الأرضيّة {e.get('pivot')} · الدفعات {e.get('tranches')}")
        if after:
            d3_bad.append(f"{kind}:{s}:{after}")
        elif union is None:
            log(f"   {kind} {s} · المصدران تعذّرا (UNVERIFIED)")
    verdict["D3"] = (bool(d3_bad), f"{len(d3_bad)} من {len(tracked)} — {' · '.join(d3_bad) or '—'}")

    # ── D4 ──
    log("\n═══ D4 الأدواتُ عند الطلب ═══")
    d4_bad = []
    for tool, s, d, rid in od:
        a = asof(s, d, hist, latest)
        act = retro_action(a, d, latest)
        log(f"   {tool} {s}@{d} (تشغيلة {rid}) · رجعيّ {act} · {fmt(a)}")
        if act in FAULT_ACTIONS:
            d4_bad.append(f"{tool}:{s}@{d}:{act}")
    verdict["D4"] = (bool(d4_bad), f"{len(d4_bad)} من {len(od)} — {' · '.join(d4_bad) or '—'}")

    # ── D5 ──
    verdict["D5"] = (oe_n > 0, f"سجلّاتٌ بعد {OE_AFTER}: {oe_n}")

    # ── التنبّؤات ──
    try:
        u, _c, _n = S.dq_split_events("SXTC")
        lo = (dt.date.fromisoformat(latest) - dt.timedelta(days=int(S.CONFIG["SPLIT_LOOKBACK_DAYS"]))).isoformat()
        sx = [(d, r) for d, r in (u or []) if lo <= d <= latest and r and r < 1.0 and not DQ.is_minor(r)]
    except Exception:                                            # noqa: BLE001
        sx = None
    pred["أ SXTC مقسَّمٌ عكسيًّا داخل النافذة"] = (bool(sx), str(sx))
    pred["ج D2 بلا عطل"] = (not verdict["D2"][0], "")
    pred["د D3 صفر"] = (not verdict["D3"][0], "")
    pred["هـ D4 واحدٌ على الأقلّ quarantine"] = (any(x.endswith(":quarantine") for x in d4_bad), "")
    pred["و D5 صفر"] = (oe_n == 0, "")

    log(f"\n⏱️ المِجَسّ {time.time() - t_start:.0f}ث")
    log("🧾 الحكم (المعاييرُ في رأس الملفّ · مكتوبةٌ قبل أوّل تشغيل):")
    for k, (bad, txt) in verdict.items():
        log(f"   {k}: {'⛔ لا قياس' if bad is None else ('🔴 مُثبَت' if bad else '🟢 غيرُ مُثبَت')} — {txt}")
    log(f"🧾 ترميزُ السجلّات: {LOG_DIAG}")
    log("🔮 التنبّؤات:")
    for k, (ok, txt) in pred.items():
        log(f"   {'✅' if ok else '❌'} {k}{(' — ' + txt) if txt else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
