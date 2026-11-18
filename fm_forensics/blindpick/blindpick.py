#!/usr/bin/env python3
"""🙈 `T-BLIND-PICK` «اختبارٌ أعمى لاختيار المالك» (عقد `T_BLIND_PICK_prereg.md`).

  cards           — 40 جلسة من لقطات git ⟵ خمسةُ صفوفٍ لكلّ جلسة (§②) ⟵ بطاقاتٌ بلا رمزٍ ولا تاريخ (HTML واحد) ⟵ تلغرام ·
                    ومفتاحُ البطاقات مشفّرٌ وحدَه في `blind_pick.vault` (لا رمزَ ولا تاريخَ في السجلّ).
  judge --picks   — اختياراتُ المالك ⟵ داخل الخزنة ⟵ الحكمُ بقاعدة FILTER_PROTOCOL (آلةُ T-BASKET وضابطُها بالاسم) ⟵ `T_BLIND_PICK_RESULT.md`.
لا CONFIG · لا إنتاج · ولا تعديلَ على أيّ أداةٍ قائمة (تُستورد بالاسم).
"""
import collections
import concurrent.futures as cf
import datetime as dt
import gzip
import hashlib
import html
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
CONTRACT = os.path.join(HERE, "T_BLIND_PICK_prereg.md")
CONTRACT_SHA = "a971de29fe5c1d60483466233338466fdd39c02028ae8b39322aaa221666cb45"
VAULT = os.path.join(ROOT, "blind_pick.vault")
RESULT = os.path.join(HERE, "T_BLIND_PICK_RESULT.md")
D_MAX = "2026-10-16"                 # §① آخرُ يوم قرارٍ أفقُه مكتمل (نوافذُ T-BASKET حتى 11-13)
N_SESS, NPICK, N_BARS = 40, 5, 250
AVAIL_DAYS = 7                       # §⓪ نافذةُ المتاح المؤرَّخ
RSI_MAX = 33.0                       # §② `rsi_max()` الحاليّ
BARS_FROM, BARS_TO, HOURS_FROM = "2025-06-01", D_MAX, "2026-07-01"
BASKET_RUN = 43955351411
ARMS = (("O0", None), ("O50", 0.5))
MIN_N, COV_FLOOR = 30, 0.80
WORKERS = 8
RC_OK, RC_KEY, RC_PICKS, RC_VAULT, RC_CONTRACT, RC_POP = 0, 2, 4, 6, 11, 5
RC_MISMATCH = 7                                                  # resend: البناءُ لا يطابق الخزنة ⟵ لا إرسالَ ولا كتابة
# 📎 الملحق 1 (2026-11-18 · أمرُ المالك): البطاقاتُ الـ200 ملغاة ⟵ إعادةُ السحب من الصفوف الكاملة (الفلوت والشورت والمتاح معلومة يومَ القرار)
ADDENDUM = os.path.join(HERE, "T_BLIND_PICK_addendum_1.md")
ADDENDUM_SHA = "b8bb293e0941cf292edf78e78d564f8cc78289d4058a8ffc5078b23095065e3d"
VAULT_A1 = os.path.join(ROOT, "blind_pick_a1.vault")
A1_MIN_SESS, A1_GAP, A1_BARS = 30, 10, 10                                     # §④ الملحق: أرضيّةُ الجلسات · والفاصلُ لتكرار الرمز مرّةً ثانية
RC_NOMEASURE = 3                                                 # §④ الملحق: دون 30 جلسة ⟵ «لا قياس» بلا بطاقات
UTC = dt.timezone.utc


def log(m=""):
    print(m, flush=True)


def contract_ok():
    return hashlib.sha256(open(CONTRACT, "rb").read()).hexdigest() == CONTRACT_SHA


def addendum_ok():
    return os.path.exists(ADDENDUM) and hashlib.sha256(open(ADDENDUM, "rb").read()).hexdigest() == ADDENDUM_SHA


def lottery(d, sym, salt=""):
    """§② القرعة (salt="") وقرعةُ العرض (salt="show|") — حتميّتان."""
    return hashlib.sha256(f"T-BLIND-PICK|{salt}{d}|{sym}".encode()).hexdigest()


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ── لقطاتُ git ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def _git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, cwd=ROOT).stdout


def snapshots():
    out = []
    for line in _git("log", "--format=%H %cI", "--", "near_watch.json").splitlines():
        h, t = line.split()
        out.append((dt.datetime.fromisoformat(t).astimezone(UTC), h))
    return sorted(out)


def show_json(h, path):
    try:
        return json.loads(_git("show", f"{h}:{path}") or "{}")
    except ValueError:
        return {}


def sess_order(days):
    """(نقيّة) §③ ترقيمُ الجلسات بقرعةٍ لا بالزمن."""
    return sorted(days, key=lambda d: hashlib.sha256(f"T-BLIND-PICK|sess|{d}".encode()).hexdigest())


def plan_sessions(snaps, sessions, close_utc, d_max=D_MAX, n=N_SESS):
    """(نقيّة) §① يومُ القرار = آخرُ جلسةٍ أُغلقت قبل طابع اللقطة · والأحدثُ يغلب · ثمّ أحدثُ n جلسةً حتى d_max ⟵ [(d، ts، hash)]."""
    by = {}
    for ts, h in sorted(snaps):
        past = [d for d in sessions if close_utc(d) <= ts]
        if past and past[-1] <= d_max:
            by[past[-1]] = (ts, h)
    return [(d,) + by[d] for d in sorted(by)[-n:]]


def session_rows(snap):
    ents = [e for e in (snap or {}).values() if isinstance(e, dict) and e.get("symbol")]
    newest = max((str(e.get("last_seen") or "") for e in ents), default="")
    return [e for e in ents if str(e.get("last_seen") or "") == newest and newest]


def avail_index(paths=None):
    idx = {}
    for fn, fa in paths or (("ctb_log.jsonl", "shares_available"), ("borrow_watch.jsonl", "available")):
        p = os.path.join(ROOT, fn)
        if not os.path.exists(p):
            continue
        for line in open(p, encoding="utf-8"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            v, s, d = r.get(fa), r.get("symbol"), str(r.get("date") or "")[:10]
            if v is None or not s or not d:
                continue
            try:
                idx.setdefault(s, []).append((d, float(v)))
            except (TypeError, ValueError):
                continue
    return idx


def avail_asof(idx, sym, d, days=AVAIL_DAYS):
    """(نقيّة) §⓪ أحدثُ متاحٍ مؤرَّخٍ في [d − days، d] أو None."""
    lo = (dt.date.fromisoformat(d) - dt.timedelta(days)).isoformat()
    c = sorted((x, v) for x, v in idx.get(sym, []) if lo <= x <= d)
    return c[-1][1] if c else None


def float_asof(row, snapday, cc):
    """(نقيّة) §⓪ فلوتُ الصفّ إن كان تاريخُه حتى يوم اللقطة · وإلّا فلوتُ ذاكرة الشركات في اللقطة نفسِها · وإلّا None."""
    fd = str(row.get("float_date") or "")
    if row.get("float") is not None and fd and fd <= snapday:
        return float(row["float"])
    c = (cc or {}).get(row.get("symbol"))
    if isinstance(c, dict) and c.get("float"):
        try:
            return float(c["float"])
        except (TypeError, ValueError):
            return None
    return None


def flags_of(rsi, fl, av, stab, boom, float_max, avail_max):
    """(نقيّة) §② الشروطُ الخمسة · المجهولُ None ⟵ (flags، الدرجة)."""
    f = (None if rsi is None else float(rsi) < RSI_MAX,
         None if fl is None else fl < float_max,
         None if av is None else av < avail_max,
         None if stab is None else bool(stab.get("stable")),
         None if boom is None else not bool(boom.get("boom")))
    return f, sum(1 for x in f if x is True)


def select(sessions_cands):
    """(نقيّة) §② sessions_cands = [(d، [(رمز، درجة)])] من الأقدم ⟵ {d: [رموزٌ خمسة]} بالدرجة ثمّ القرعة · بلا تكرارٍ بين الجلسات."""
    used, out = set(), {}
    for d, cands in sorted(sessions_cands):
        ranked = sorted(cands, key=lambda x: (-x[1], lottery(d, x[0])))
        pick = []
        for s, _sc in ranked:
            if s in used:
                continue
            pick.append(s)
            used.add(s)
            if len(pick) == NPICK:
                break
        out[d] = pick
    return out


# ── الشارت (SVG بلا تبعيّات) ────────────────────────────────────────────────────────────────────────────────────────
def svg_chart(rows, w=900, h=330):
    """rows = [(o، h، l، c، v)] ⟵ SVG شموعٍ يوميّة بلا تواريخ · محورُ سعرٍ بأربعة خطوط · والحجمُ أسفل."""
    if not rows:
        return "<p>—</p>"
    ph, vh, pad, rx = h - 70, 50, 6, 56
    hi = max(r[1] for r in rows)
    lo = min(r[2] for r in rows if r[2] > 0) if any(r[2] > 0 for r in rows) else 0.0
    vmax = max(r[4] for r in rows) or 1.0
    span = (hi - lo) or (hi or 1.0)
    n = len(rows)
    cw = (w - rx - pad) / n
    y = lambda p: pad + (hi - p) / span * (ph - 2 * pad)                             # noqa: E731
    out = [f'<svg viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg" style="background:#fff">']
    for k in range(5):
        p = lo + span * k / 4
        yy = y(p)
        out.append(f'<line x1="0" x2="{w - rx}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="#eee"/>'
                   f'<text x="{w - rx + 4}" y="{yy + 4:.1f}" font-size="11" fill="#666">{p:.4g}</text>')
    for i, (o, hh, l, c, v) in enumerate(rows):
        x = i * cw + cw / 2
        col = "#1a9850" if c >= o else "#d73027"
        out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y(hh):.1f}" y2="{y(l):.1f}" stroke="{col}" stroke-width="1"/>')
        top, bot = y(max(o, c)), y(min(o, c))
        out.append(f'<rect x="{x - cw * 0.35:.1f}" y="{top:.1f}" width="{max(cw * 0.7, 0.8):.1f}" height="{max(bot - top, 0.8):.1f}" fill="{col}"/>')
        vb = v / vmax * vh
        out.append(f'<rect x="{x - cw * 0.35:.1f}" y="{h - vb:.1f}" width="{max(cw * 0.7, 0.8):.1f}" height="{vb:.1f}" fill="#9ab"/>')
    out.append("</svg>")
    return "".join(out)


def svg_chart10(rows, rsis, w=480):
    """(نقيّة) §⑤ الملحق: آخرُ الشموع (10) تملأ العرض ⟵ لوحةُ السعر (محورُ سعرٍ يمين · بلا تواريخ) ⟵ أعمدةُ الحجم ⟵ خطُّ RSI(14) بمرجعَي 30/70 ·
    rows = [(o، h، l، c، v)] · rsis = [RSI أو None] بطولها · بلا ماكد ولا خطوط دعمٍ ومقاومة."""
    if not rows:
        return "<p>—</p>"
    ph, vh, rh, gap, pad, rx = 300, 70, 100, 14, 8, 58
    h = ph + vh + rh + 2 * gap
    hi = max(r[1] for r in rows)
    lo = min(r[2] for r in rows)
    span = (hi - lo) or (hi or 1.0)
    hi, lo = hi + span * 0.04, lo - span * 0.04
    span = hi - lo
    vmax = max(r[4] for r in rows) or 1.0
    n = len(rows)
    cw = (w - rx - pad) / n
    y = lambda p: pad + (hi - p) / span * (ph - 2 * pad)                             # noqa: E731
    out = [f'<svg viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg" style="background:#fff;direction:ltr" direction="ltr">']
    for k in range(5):
        p = lo + span * k / 4
        yy = y(p)
        out.append(f'<line x1="0" x2="{w - rx}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="#eee"/>'
                   f'<text x="{w - rx + 6}" y="{yy + 5:.1f}" font-size="15" fill="#222">{p:.4g}</text>')
    vy0 = ph + gap
    ry0 = ph + vh + 2 * gap
    ry = lambda v: ry0 + (100 - v) / 100 * rh                                        # noqa: E731
    for i, (o, hh, l, c, v) in enumerate(rows):
        x = pad + i * cw + cw / 2
        col = "#1a9850" if c >= o else "#d73027"
        out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y(hh):.1f}" y2="{y(l):.1f}" stroke="{col}" stroke-width="1.6"/>')
        top, bot = y(max(o, c)), y(min(o, c))
        out.append(f'<rect x="{x - cw * 0.32:.1f}" y="{top:.1f}" width="{cw * 0.64:.1f}" height="{max(bot - top, 1.5):.1f}" fill="{col}"/>')
        vb = v / vmax * (vh - 4)
        out.append(f'<rect x="{x - cw * 0.32:.1f}" y="{vy0 + vh - vb:.1f}" width="{cw * 0.64:.1f}" height="{vb:.1f}" fill="{col}" opacity="0.55"/>')
    out.append(f'<text x="{w - rx + 6}" y="{vy0 + 14}" font-size="13" fill="#666">الحجم</text>')
    for lv in (30, 70):
        out.append(f'<line x1="0" x2="{w - rx}" y1="{ry(lv):.1f}" y2="{ry(lv):.1f}" stroke="#bbb" stroke-dasharray="4,4"/>'
                   f'<text x="{w - rx + 6}" y="{ry(lv) + 5:.1f}" font-size="14" fill="#666">{lv}</text>')
    pts = [(pad + i * cw + cw / 2, ry(float(v))) for i, v in enumerate(rsis or []) if v is not None and i < n]
    if len(pts) >= 2:
        out.append('<polyline fill="none" stroke="#7b3fa0" stroke-width="2.5" points="' + " ".join(f"{a:.1f},{b:.1f}" for a, b in pts) + '"/>')
    out.append(f'<text x="{w - rx + 6}" y="{ry0 + 14}" font-size="13" fill="#666">RSI 14</text>')
    out.append("</svg>")
    return "".join(out)


def _num(x, dec=0):
    if x is None:
        return "—"
    try:
        return f"{float(x):,.{dec}f}"
    except (TypeError, ValueError):
        return html.escape(str(x))


def stab_text(st, f=1.0):
    if not st:
        return "—"
    pv = float(st.get("pivot") or 0) * f
    if st.get("stable"):
        return f"ثابت {st.get('bars_after')} جلسات فوق القاع الدقيق ${pv:.4g}"
    if not st.get("held"):
        return f"الإغلاق تحت القاع الدقيق ${pv:.4g}"
    return f"لم يثبت: مضى {st.get('bars_after')} من {st.get('need')} جلسات فوق القاع الدقيق ${pv:.4g}"


def card_html(label, rows, fields, behav, chart=None):
    tr = "".join(f"<tr><th>{html.escape(k)}</th><td>{v}</td></tr>" for k, v in fields)
    tb = "".join(f"<tr><th>{html.escape(k)}</th><td>{html.escape('—' if v is None else str(v))}</td></tr>" for k, v in behav)
    return (f'<div class="card"><h3>البطاقة {label}</h3>{chart if chart is not None else svg_chart(rows)}'
            f'<table>{tr}</table><h4>سلوكه في الانفجارات السابقة (حتى يوم القرار)</h4><table>{tb}</table></div>')


def page(sections, n=N_SESS):
    css = ("body{font-family:sans-serif;direction:rtl;margin:12px;background:#f7f7f7}.card{background:#fff;border:1px solid #ccc;"
           "border-radius:8px;padding:10px;margin:12px 0}table{border-collapse:collapse;width:100%;font-size:14px}th,td{border-bottom:1px solid #eee;"
           "padding:4px;text-align:right}th{width:45%;color:#444}h2{background:#223;color:#fff;padding:8px;border-radius:6px}")
    head = (f"<h1>🙈 اختبارٌ أعمى — {n} جلسة × 5 بطاقات</h1>"
            "<p>كلُّ بطاقةٍ بلا رمزٍ ولا تاريخ · الأرقامُ كما كانت يومَ القرار · «—» = لا مصدرَ مؤرَّخ.</p>"
            "<p><b>الردّ:</b> رقمُ بطاقةٍ واحدة لكلّ جلسة (مثل «7-3») · والجلسةُ التي تعرف فيها سهمًا: «7: أعرفه» (تُستبعد).</p>")
    return f"<!doctype html><html lang=ar dir=rtl><head><meta charset=utf-8><meta name=viewport content='width=device-width'><style>{css}</style></head><body>{head}{''.join(sections)}</body></html>"


# ── الجلب (Polygon · الرنر) ───────────────────────────────────────────────────────────────────────────────────────────
def poly_splits(sym, key, get):
    js = get(f"https://api.polygon.io/v3/reference/splits?ticker={sym}&limit=1000&apiKey={key}") or {}
    out = []
    for r in js.get("results") or []:
        try:
            fr, to = float(r["split_from"]), float(r["split_to"])
            if fr > 0 and to > 0:
                out.append((str(r["execution_date"]), to / fr))
        except (KeyError, TypeError, ValueError):
            continue
    return sorted(out)


def asof_rows(rows, splits, d, asof_factor):
    """(نقيّة) صفوفٌ حتى d بمقياس يوم d: السعرُ × ∏(النسبة) لتقسيمات ما بعد d · والحجمُ ÷ الحاصل ⟵ (الصفوف، المعامل)."""
    nxt = (dt.date.fromisoformat(d) + dt.timedelta(1)).isoformat()
    f = asof_factor(splits, nxt)
    return [(x[0], x[1] * f, x[2] * f, x[3] * f, x[4] * f, x[5] / f if f else x[5]) for x in rows if x[0] <= d], f


def behav_frame(rows):
    """الأعمدةُ السبعة بفهرسٍ = عددُ الجلسات قبل يوم القرار (لا تاريخ) ⟵ DataFrame."""
    import pandas as pd
    n = len(rows)
    return pd.DataFrame({"Open": [r[1] for r in rows], "High": [r[2] for r in rows], "Low": [r[3] for r in rows],
                         "Close": [r[4] for r in rows], "Volume": [r[5] for r in rows]}, index=[n - 1 - i for i in range(n)])


def mode_cards(key, resend=False):
    import market_calendar as MC
    import journal_vault as J
    import three_cond_daily as TC
    import opentry_link_probe as OPL
    import Super_stock as S
    WW = TC.WW
    RB = _load("rb_blind", "fm_forensics/rebuild/rebuild.py")
    TB = _load("tb_blind", "fm_forensics/nawaqis/tbook.py")
    pw = J._pass()
    if pw is None:
        log("⛔ بلا مفتاح خزنة — لا بطاقات (المفتاحُ لا يُحفظ إلّا مشفّرًا) — خروج 6")
        return RC_VAULT
    sessions = TB._sessions("2026-07-01", dt.datetime.now(UTC).date().isoformat(), MC)    # حتى اليوم ثمّ القصُّ بـD_MAX (لا قبله)
    plan = plan_sessions(snapshots(), sessions, WW.close_utc)
    log(f"📅 الجلسات {len(plan)} (المطلوبة {N_SESS}) · من {plan[0][0] if plan else '—'} إلى {plan[-1][0] if plan else '—'}")
    if not plan:
        return RC_POP
    aidx = avail_index()
    meta, syms = {}, set()
    for d, ts, h in plan:
        snap = show_json(h, "near_watch.json")
        cc_h = _git("log", "-1", f"--before={ts.isoformat()}", "--format=%H", "--", "company_cache.json").strip()
        cc = show_json(cc_h, "company_cache.json") if cc_h else {}
        snapday = ts.date().isoformat()
        rows = []
        for e in session_rows(snap):
            s = e["symbol"]
            rows.append({"sym": s, "rsi": e.get("rsi_now"), "fl": float_asof(e, snapday, cc), "av": avail_asof(aidx, s, d)})
            syms.add(s)
        meta[d] = rows
    log(f"🔢 صفوفٌ {sum(len(v) for v in meta.values())} · رموزٌ مختلفة {len(syms)} · فلوتٌ معلوم {sum(1 for v in meta.values() for r in v if r['fl'] is not None)}"
        f" · متاحٌ معلوم {sum(1 for v in meta.values() for r in v if r['av'] is not None)}")
    bars, hours, t0 = {}, {}, time.time()

    def _one(s):
        return s, TC.P.ticker_daily_adj(s, BARS_FROM, BARS_TO, key), TC._hours_one(s, HOURS_FROM, BARS_TO, key)
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for i, (s, dr, hr) in enumerate(ex.map(_one, sorted(syms)), 1):
            bars[s], hours[s] = dr or [], hr or []
            if i % 200 == 0:
                log(f"   … الشموع {i}/{len(syms)} · {round(time.time() - t0)}s")
    log(f"📊 بلا شموعٍ يوميّة {sum(1 for s in syms if not bars[s])} · بلا ساعة {sum(1 for s in syms if not hours[s])}")
    cands, info, score_hist = [], {}, {}
    for d, _ts, _h in plan:
        cs = []
        for r in meta[d]:
            s = r["sym"]
            if not any(x[0] == d for x in bars[s]):
                continue
            st = TC.exact_low_stability(bars[s], hours[s], d)
            bm = TC.recent_explosion(bars[s], hours[s], d)
            fl, sc = flags_of(r["rsi"], r["fl"], r["av"], st, bm, OPL.FLOAT_OWNER, OPL.AVAIL_OWNER)
            info[(d, s)] = dict(r, st=st, bm=bm, flags=fl, score=sc)
            cs.append((s, sc))
        cands.append((d, cs))
    picks = select(cands)
    sections, cards = [], {}
    order = sess_order([p[0] for p in plan])
    for j, d in enumerate(order, 1):
        chosen = sorted(picks.get(d) or [], key=lambda s: lottery(d, s, "show|"))
        body = [f"<h2>الجلسة {j}</h2>"]
        fmap = S._finra_day_map(d)
        for k, s in enumerate(chosen, 1):
            label = f"{j}-{k}"
            it = info[(d, s)]
            score_hist[it["score"]] = score_hist.get(it["score"], 0) + 1
            sp = poly_splits(s, key, _getjson)
            rows, f = asof_rows(bars[s], sp, d, RB.asof_factor)
            beh = S.behavior_explosion_detail(behav_frame(rows))
            last = beh.get("تاريخ آخر انفجار")
            beh["تاريخ آخر انفجار"] = None if last is None else f"قبل {last} جلسة من يوم القرار"
            fields = [("RSI", _num(it["rsi"], 1)), ("ثبات آخر 5 جلسات", html.escape(stab_text(it["st"], f))),
                      ("الفلوت", _num(it["fl"])), ("الشورت (حجم FINRA اليوميّ)", _num(fmap.get(s))),
                      ("الأسهم المعروضة (المتاح)", _num(it["av"]))]
            body.append(card_html(label, [(x[1], x[2], x[3], x[4], x[5]) for x in rows[-N_BARS:]], fields,
                                  [(c, beh.get(c)) for c in S.NW_XLSX_BEHAV_COLS]))
            cards[label] = {"sym": s, "d": d, "score": it["score"], "flags": list(it["flags"])}
        sections.append("".join(body))
    if resend:                                                   # إعادةُ إرسالٍ: الخزنةُ لا تُمسّ والبطاقاتُ يجب أن تطابقها حرفًا
        old = None
        if os.path.exists(VAULT):
            raw = open(VAULT, encoding="utf-8").read()
            old = next((v for v in (J.decrypt(raw, p) for p in _vault_pw(J)) if v), None)
        ok_m, n_diff = vault_matches(old, order, cards)
        log(f"🔁 مطابقةُ البطاقات للخزنة: {'✅ مطابقة' if ok_m else f'❌ تختلف ({n_diff})'}")
        if not ok_m:
            log("⛔ لا إرسالَ ولا كتابة — خروج 7")
            return RC_MISMATCH
    else:
        vault = {"v": 1, "test": "T-BLIND-PICK", "contract_sha": CONTRACT_SHA, "sessions": order, "cards": cards, "picks": {},
                 "created": dt.datetime.now(UTC).isoformat(timespec="seconds")}
        txt = J.encrypt(vault, pw)
        if txt is None:
            log("⛔ التشفيرُ فشل — لا إرسال — خروج 6")
            return RC_VAULT
        open(VAULT, "w", encoding="utf-8").write(txt)
    d_out = tempfile.mkdtemp()
    path = os.path.join(d_out, "blind_cards.html")
    open(path, "w", encoding="utf-8").write(page(sections))
    log(f"🃏 بطاقات {len(cards)} في {len(plan)} جلسة · توزيعُ الدرجات {dict(sorted(score_hist.items()))} · الحجم {os.path.getsize(path) // 1024}KB")
    ok = send_doc(path, f"🙈 T-BLIND-PICK — {len(plan)} جلسة × 5 بطاقات · ردّ برقم بطاقةٍ لكلّ جلسة (مثل 7-3) أو «أعرفه»",
                  S.TELEGRAM_TOKEN, S._admin_chat())
    log(f"📨 الإرسال: {'✅' if ok else '❌'} · المفتاحُ مشفّرٌ في blind_pick.vault")
    return RC_OK if ok else RC_VAULT


def vault_matches(vault, order, cards):
    """(نقيّة) ⟵ (مطابقة؟، عددُ الفروق): ترتيبُ الجلسات والبطاقاتُ {رقم: رمز·يوم·درجة·وسوم} كما في الخزنة حرفًا."""
    if not isinstance(vault, dict):
        return False, -1
    old = vault.get("cards") or {}
    new = json.loads(json.dumps(cards, ensure_ascii=False))
    n = sum(1 for k in set(old) | set(new) if old.get(k) != new.get(k)) + (0 if vault.get("sessions") == list(order) else 1)
    return n == 0, n


def send_doc(path, caption, token, admin, owner=None, post=None):
    """📨 sendDocument مع دليل الوصول في السجلّ (رقمُ الرسالة · نوعُ المحادثة · اسمُ الملفّ وحجمُه) — بلا رقم المحادثة ولا اسمِ صاحبها.
    الوجهة: `TELEGRAM_OWNER_ID` إن وُجد وإلّا أوّلُ رقمٍ في `TELEGRAM_CHAT_ID` (`_admin_chat`)."""
    owner = str(owner if owner is not None else os.environ.get("TELEGRAM_OWNER_ID", "")).strip()
    targets = [owner] if owner else list(admin or [])
    where = "TELEGRAM_OWNER_ID" if owner else "أوّلُ رقمٍ في TELEGRAM_CHAT_ID"
    if not token or not targets:
        log(f"⛔ بلا رمز بوت أو وجهة ({where}) — لا إرسال")
        return False
    if post is None:
        import requests
        post = requests.post
    ok = True
    for cid in targets:
        try:
            with open(path, "rb") as fh:
                r = post(f"https://api.telegram.org/bot{token}/sendDocument", data={"chat_id": cid, "caption": caption[:1000]},
                         files={"document": fh}, timeout=120)
            js = {}
            try:
                js = r.json() or {}
            except Exception:                                    # noqa: BLE001
                js = {}
            res = js.get("result") or {}
            doc = res.get("document") or {}
            log(f"📨 sendDocument ⟵ {where}: HTTP {r.status_code} · ok={js.get('ok')} · رقمُ الرسالة {res.get('message_id')}"
                f" · نوعُ المحادثة {(res.get('chat') or {}).get('type')} · الملفّ {doc.get('file_name')} ({doc.get('file_size')} بايت)")
            if r.status_code != 200 or not js.get("ok") or not res.get("message_id"):
                ok = False
                log(f"⚠️ رفض: {str(js.get('description') or '')[:160]}")
        except Exception as e:                                   # noqa: BLE001
            log(f"⚠️ خطأ sendDocument: {type(e).__name__}")
            ok = False
    return ok



# ── الملحق 1: إعادةُ السحب من الصفوف الكاملة ─────────────────────────────────────────────────────────────────────────────
def complete_row(r, d, voided):
    """(نقيّة) §② الملحق: الفلوتُ والشورتُ والمتاحُ معلومةٌ يومَ القرار · وليس الزوجُ (رمز، d) من البطاقات الملغاة."""
    return (r.get("fl") is not None and r.get("av") is not None and r.get("sh") is not None
            and (r.get("sym"), d) not in voided)


def a1_counts(comp):
    """(نقيّة) §③ الملحق: comp = {d: [رموز الصفوف الكاملة]} ⟵ العدُّ قبل أيّ بناء (بلا رمزٍ ولا تاريخ)."""
    ns = sorted(len(v) for v in comp.values())
    med = (ns[len(ns) // 2] if len(ns) % 2 else (ns[len(ns) // 2 - 1] + ns[len(ns) // 2]) / 2) if ns else None
    return {"sessions": len(comp), "min": ns[0] if ns else None, "median": med, "max": ns[-1] if ns else None,
            "ge5": sum(1 for n in ns if n >= NPICK), "symbols": len({s for v in comp.values() for s in v})}


def select_a1(sessions_cands, sidx, gap=None, npick=NPICK):
    """(نقيّة) §④ الملحق: [(d، [(رمز، درجة)])] على الصفوف الكاملة · من الأقدم ⟵ {d: خمسةُ رموز} للجلسات المكتملة وحدَها.
    gap=None ⟵ (أ) بلا تكرار · gap=N ⟵ (ب) الرمزُ يعود مرّةً ثانيةً فقط إن كان بين يومَي القرار N جلسةً فأكثر (sidx: d ⟵ رقمُ الجلسة في التقويم).
    جلسةٌ دون npick تسقط كلُّها ولا تُعلِّم رموزَها مستعملة."""
    uses, out = {}, {}
    for d, cands in sorted(sessions_cands):
        ranked = sorted(cands, key=lambda x: (-x[1], lottery(d, x[0])))
        pick = []
        for s, _sc in ranked:
            u = uses.get(s) or []
            if s in pick or (u and (gap is None or len(u) >= 2 or sidx[d] - u[-1] < gap)):
                continue
            pick.append(s)
            if len(pick) == npick:
                break
        if len(pick) == npick:
            out[d] = pick
            for s in pick:
                uses.setdefault(s, []).append(sidx[d])
    return out


def mode_a1(key, build):
    """§③-§⑤ الملحق: العدُّ ⟵ (أ) ثمّ (ب) ⟵ «لا قياس» دون 30 ⟵ وإلّا (build) البطاقاتُ والخزنةُ الجديدة والإرسال."""
    import market_calendar as MC
    import journal_vault as J
    import three_cond_daily as TC
    import opentry_link_probe as OPL
    import Super_stock as S
    RB = _load("rb_blind", "fm_forensics/rebuild/rebuild.py")
    TB = _load("tb_blind", "fm_forensics/nawaqis/tbook.py")
    pws = _vault_pw(J)
    old = next((x for x in (J.decrypt(open(VAULT, encoding="utf-8").read(), p) for p in pws) if x), None) if os.path.exists(VAULT) else None
    if old is None or not old.get("cards"):
        log("⛔ خزنةُ البطاقات الملغاة لا تُفكّ — لا يُعرَف ما يُستبعد — خروج 6")
        return RC_VAULT
    voided = {(c["sym"], c["d"]) for c in old["cards"].values()}
    log(f"🗑️ أزواجُ البطاقات الملغاة: {len(voided)}")
    sessions = TB._sessions("2026-07-01", dt.datetime.now(UTC).date().isoformat(), MC)
    sidx = {d: i for i, d in enumerate(sessions)}
    plan = plan_sessions(snapshots(), sessions, TC.WW.close_utc)
    log(f"📅 مجمعُ الجلسات {len(plan)} · من {plan[0][0] if plan else '—'} إلى {plan[-1][0] if plan else '—'}")
    if not plan:
        return RC_POP
    aidx = avail_index()
    meta, finra_fail = {}, 0
    for d, ts, h in plan:
        snap = show_json(h, "near_watch.json")
        cc_h = _git("log", "-1", f"--before={ts.isoformat()}", "--format=%H", "--", "company_cache.json").strip()
        cc = show_json(cc_h, "company_cache.json") if cc_h else {}
        fmap = S._finra_day_map(d) or {}
        finra_fail += int(not fmap)
        snapday = ts.date().isoformat()
        meta[d] = [{"sym": e["symbol"], "rsi": e.get("rsi_now"), "fl": float_asof(e, snapday, cc), "av": avail_asof(aidx, e["symbol"], d),
                    "sh": fmap.get(e["symbol"])} for e in session_rows(snap)]
    pre = {d: [r for r in rows if complete_row(r, d, voided)] for d, rows in meta.items()}
    syms = sorted({r["sym"] for rows in pre.values() for r in rows})
    log(f"🔢 صفوف {sum(len(v) for v in meta.values())} · كاملةٌ قبل الشموع {sum(len(v) for v in pre.values())} · رموزُها {len(syms)} · "
        f"أيّامُ FINRA متعذّرة {finra_fail}")
    bars, hours, t0 = {}, {}, time.time()

    def _one(s):
        return s, TC.P.ticker_daily_adj(s, BARS_FROM, BARS_TO, key), TC._hours_one(s, HOURS_FROM, BARS_TO, key)
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for i, (s, dr, hr) in enumerate(ex.map(_one, syms), 1):
            bars[s], hours[s] = dr or [], hr or []
            if i % 200 == 0:
                log(f"   … الشموع {i}/{len(syms)} · {round(time.time() - t0)}s")
    comp = {d: [r for r in rows if any(x[0] == d for x in bars.get(r["sym"]) or [])] for d, rows in pre.items()}
    c = a1_counts({d: [r["sym"] for r in rows] for d, rows in comp.items()})
    log(f"📊 العدّ (البند 2): الجلسات {c['sessions']} · الصفوفُ الكاملة لكلّ جلسة أدنى {c['min']} · وسيط {c['median']} · أعلى {c['max']} · "
        f"**جلساتٌ فيها 5 صفوفٍ كاملةٍ فأكثر {c['ge5']}** · **رموزٌ مختلفة {c['symbols']}**")
    info, cands = {}, []
    for d, rows in comp.items():
        cs = []
        for r in rows:
            s = r["sym"]
            st = TC.exact_low_stability(bars[s], hours[s], d)
            bm = TC.recent_explosion(bars[s], hours[s], d)
            fl, sc = flags_of(r["rsi"], r["fl"], r["av"], st, bm, OPL.FLOAT_OWNER, OPL.AVAIL_OWNER)
            info[(d, s)] = dict(r, st=st, bm=bm, flags=fl, score=sc)
            cs.append((s, sc))
        cands.append((d, cs))
    picks = select_a1(cands, sidx)
    log(f"🅰️ (أ) بلا تكرار: جلساتٌ مؤهَّلة {len(picks)}")
    arm = "A"
    if len(picks) < A1_MIN_SESS:
        picks = select_a1(cands, sidx, gap=A1_GAP)
        arm = "B"
        log(f"🅱️ (ب) تكرارٌ مرّةً ثانية بفاصل {A1_GAP} جلسات فأكثر: جلساتٌ مؤهَّلة {len(picks)}")
    if len(picks) < A1_MIN_SESS:
        log(f"⚖️ الحكم «لا قياس» — {len(picks)} جلسة دون {A1_MIN_SESS} · لا بطاقات (§④ الملحق) — خروج 3")
        return RC_NOMEASURE
    log(f"✅ {len(picks)} جلسة فأكثر من {A1_MIN_SESS} بالاختيار ({arm}) · توزيعُ الدرجات "
        f"{dict(sorted(collections.Counter(info[(d, s)]['score'] for d, v in picks.items() for s in v).items()))}")
    if not build:
        return RC_OK
    order = sorted(picks, key=lambda d: hashlib.sha256(f"T-BLIND-PICK|A1|sess|{d}".encode()).hexdigest())
    sections, cards = [], {}
    for j, d in enumerate(order, 1):
        chosen = sorted(picks[d], key=lambda s: lottery(d, s, "A1|show|"))
        body = [f"<h2>الجلسة {j}</h2>"]
        for k, s in enumerate(chosen, 1):
            label = f"{j}-{k}"
            it = info[(d, s)]
            sp = poly_splits(s, key, _getjson)
            rows, f = asof_rows(bars[s], sp, d, RB.asof_factor)
            beh = S.behavior_explosion_detail(behav_frame(rows))
            last = beh.get("تاريخ آخر انفجار")
            beh["تاريخ آخر انفجار"] = None if last is None else f"قبل {last} جلسة من يوم القرار"
            fields = [("RSI", _num(it["rsi"], 1)), ("ثبات آخر 5 جلسات", html.escape(stab_text(it["st"], f))),
                      ("الفلوت", _num(it["fl"])), ("الشورت (حجم FINRA اليوميّ)", _num(it["sh"])),
                      ("الأسهم المعروضة (المتاح)", _num(it["av"]))]
            closes = S.pd.Series([x[4] for x in rows], dtype=float)
            rs = S.rsi(closes, 14).tolist() if len(rows) >= 15 else [None] * len(rows)
            r10 = [None if (v is None or v != v) else float(v) for v in rs[-A1_BARS:]]
            body.append(card_html(label, [], fields, [(cn, beh.get(cn)) for cn in S.NW_XLSX_BEHAV_COLS],
                                  chart=svg_chart10([(x[1], x[2], x[3], x[4], x[5]) for x in rows[-A1_BARS:]], r10)))
            cards[label] = {"sym": s, "d": d, "score": it["score"], "flags": list(it["flags"])}
        sections.append("".join(body))
    vault = {"v": 1, "test": "T-BLIND-PICK", "addendum": 1, "contract_sha": CONTRACT_SHA, "addendum_sha": ADDENDUM_SHA, "arm": arm,
             "sessions": order, "cards": cards, "picks": {}, "created": dt.datetime.now(UTC).isoformat(timespec="seconds")}
    txt = J.encrypt(vault, pws[0])
    if txt is None:
        log("⛔ التشفيرُ فشل — لا إرسال — خروج 6")
        return RC_VAULT
    open(VAULT_A1, "w", encoding="utf-8").write(txt)
    path = os.path.join(tempfile.mkdtemp(), "blind_cards_A1.html")
    open(path, "w", encoding="utf-8").write(page(sections, len(order)))
    log(f"🃏 بطاقات {len(cards)} في {len(order)} جلسة · الحجم {os.path.getsize(path) // 1024}KB")
    ok = send_doc(path, f"🙈 T-BLIND-PICK (الملحق 1 · صفوفٌ كاملة) — {len(order)} جلسة × 5 بطاقات · ردّ برقم بطاقةٍ لكلّ جلسة (مثل 7-3) أو «أعرفه»",
                  S.TELEGRAM_TOKEN, S._admin_chat())
    log(f"📨 الإرسال: {'✅' if ok else '❌'} · المفتاحُ مشفّرٌ في blind_pick_a1.vault")
    return RC_OK if ok else RC_VAULT

def _getjson(url, tries=3):
    import requests
    for i in range(tries):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                return r.json()
        except Exception:                                        # noqa: BLE001
            pass
        time.sleep(1.5 * (i + 1))
    return None


# ── الحكم ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def parse_picks(txt, n_sess):
    """(نقيّة) «7-3» أو «7: أعرفه» ⟵ {7: 3 أو "known"} · وأيُّ رقمٍ خارج المدى أو تكرارٌ متناقض ⟵ ValueError."""
    out = {}
    for tok in re.split(r"[,\n،؛;]+", txt or ""):
        tok = tok.strip()
        if not tok:
            continue
        m = re.fullmatch(r"(\d+)\s*[-:]\s*(\d+|أعرفه)", tok)
        if not m:
            raise ValueError(f"صيغةٌ غيرُ مفهومة: {tok!r}")
        j = int(m.group(1))
        v = "known" if m.group(2) == "أعرفه" else int(m.group(2))
        if not 1 <= j <= n_sess or (v != "known" and not 1 <= v <= NPICK) or (j in out and out[j] != v):
            raise ValueError(f"خارجَ المدى أو متناقض: {tok!r}")
        out[j] = v
    return out


def _vault_pw(J):
    """المفتاحُ الحاليّ ثمّ المشتقُّ من رمز البوت (نقلُ الخزنة إلى `TRADE_JOURNAL_KEY` لاحقًا لا يُعميها)."""
    env = dict(os.environ)
    a = J._pass(env)
    env.pop("TRADE_JOURNAL_KEY", None)
    b = J._pass(env)
    return [p for p in (a, b) if p]


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    hw = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(c - hw, 4), round(c + hw, 4)]


def judge_eval(recs, picked, FC, boot_mean):
    """(شبه نقيّة) recs = [{sym, d, res, ctrl}] للجلسات المحسوبة · picked = {(رمز، يوم)} ⟵ {cells, verdict, best}."""
    sig = {(r["sym"], r["d"]): ((r["sym"], r["d"]) in picked) for r in recs}
    cells = {}
    for arm in ("O0", "O50"):
        exc = {(r["sym"], r["d"]): FC.excess(r, arm) for r in recs}
        t = [(k[0], v) for k, v in exc.items() if v is not None and sig[k]]
        f = [(k[0], v) for k, v in exc.items() if v is not None and not sig[k]]
        raw_t = [float(r["res"][arm]["r"]) for r in recs if sig[(r["sym"], r["d"])] and (r.get("res") or {}).get(arm)]
        cells[arm] = {"n_cards": len(recs), "coverage": round(sum(1 for v in exc.values() if v is not None) / len(recs), 4) if recs else None,
                      "n_true": len(t), "n_false": len(f), "a_mean": FC._mean([v for _s, v in t]),
                      "a_ci": boot_mean(t) if len(t) >= 2 else None,
                      "b_mean": (round(FC._mean([v for _s, v in t]) - FC._mean([v for _s, v in f]), 6) if t and f else None),
                      "b_ci": FC.boot_diff(t, f) if len(t) >= 2 and len(f) >= 2 else None,
                      "raw_true": FC._mean(raw_t), "raw_false": FC._mean([float(r["res"][arm]["r"]) for r in recs if not sig[(r["sym"], r["d"])]
                                                                         and (r.get("res") or {}).get(arm)])}
    if any(c["n_true"] < MIN_N or c["n_false"] < MIN_N or (c["coverage"] or 0) < COV_FLOOR for c in cells.values()):
        verdict = "لا قياس"
    elif all((c["a_ci"] or [0])[0] > 0 and (c["b_ci"] or [0])[0] > 0 and (c["raw_true"] or 0) > 0 for c in cells.values()):
        verdict = "✅ تعبر"
    else:
        verdict = "❌ لا تعبر"
    best, nb = 0, 0
    for d in sorted({r["d"] for r in recs}):
        rr = [(float(r["res"]["O0"]["r"]), (r["sym"], d) in picked) for r in recs if r["d"] == d and (r.get("res") or {}).get("O0")]
        if rr and any(p for _x, p in rr):
            nb += 1
            best += int(max(x for x, p in rr if p) >= max(x for x, _p in rr))
    return {"cells": cells, "verdict": verdict, "best": best, "best_n": nb, "best_ci": wilson(best, nb)}


def mode_judge(key, picks_txt, d_in):
    import journal_vault as J
    B = _load("basket_blind", "fm_forensics/basket/basket.py")
    FC = _load("fc_blind", "fm_forensics/nawaqis/filter_core.py")
    pws = _vault_pw(J)
    v = next((x for x in (J.decrypt(open(VAULT_A1, encoding="utf-8").read(), p) for p in pws) if x), None) if os.path.exists(VAULT_A1) else None
    if v is None:
        log("⛔ الخزنةُ غائبة أو لا تُفكّ — خروج 6")
        return RC_VAULT
    try:
        picks = parse_picks(picks_txt, len(v["sessions"]))
    except ValueError as e:
        log(f"⛔ الاختيارات: {e} — خروج 4")
        return RC_PICKS
    v["picks"] = {str(k): x for k, x in sorted(picks.items())}
    v["picks_at"] = dt.datetime.now(UTC).isoformat(timespec="seconds")
    txt = J.encrypt(v, pws[0])
    if txt is None:
        return RC_VAULT
    open(VAULT_A1, "w", encoding="utf-8").write(txt)
    log(f"🔐 الاختياراتُ في الخزنة: {len(picks)} جلسة · أعرفه {sum(1 for x in picks.values() if x == 'known')}")
    p = os.path.join(d_in, "basket_extra.json.gz")
    if not os.path.exists(p):
        p = next((os.path.join(a, f) for a, _b, fs in os.walk(d_in) for f in fs if f == "basket_extra.json.gz"), None)
    if not p:
        log("⛔ basket_extra.json.gz غائب — خروج 5")
        return RC_POP
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        extra = json.load(fh)
    allsess, decs = extra["allsess"], extra.get("decs") or {}
    pos = {d: i for i, d in enumerate(allsess)}
    sess_ok = {j + 1: d for j, d in enumerate(v["sessions"]) if isinstance(picks.get(j + 1), int)}
    picked = {(v["cards"][f"{j}-{picks[j]}"]["sym"], d) for j, d in sess_ok.items() if f"{j}-{picks[j]}" in v["cards"]}
    todo = [(lab, c) for lab, c in v["cards"].items() if int(lab.split("-")[0]) in sess_ok]
    spc, fc, ccache, recs = {}, {}, {}, []

    def _sp(s):
        if s not in spc:
            spc[s] = poly_splits(s, key, _getjson)
        return spc[s]
    for n, (lab, c) in enumerate(sorted(todo)):
        s, d = c["sym"], c["d"]
        i = pos.get(d)
        window = allsess[i + 1:i + 21] if i is not None else []
        res, _st = B.trade_all(s, d, window, _sp(s), key, [("orders", a[1]) for a in ARMS], fcache=fc)
        ctrls = []
        for cs in B.ctrl_pick(s, d, decs.get(d) or {}):
            if (cs, d) not in ccache:
                cr, _x = B.trade_all(cs, d, window, _sp(cs), key, [("orders", a[1]) for a in ARMS], fcache=fc)
                ccache[(cs, d)] = {a: (x or {}).get("r") for a, x in (cr or {}).items()} if cr else None
            ctrls.append(ccache[(cs, d)])
        recs.append({"sym": s, "d": d, "label": lab, "score": c.get("score"), "res": res, "ctrl": ctrls})
        if n % 20 == 0:
            log(f"   … الصفقات {n + 1}/{len(todo)}")
    ev = judge_eval(recs, picked, FC, B.boot_mean)
    L = ["# 🙈 `T-BLIND-PICK` «اختبارٌ أعمى لاختيار المالك» — النتيجة", "",
         f"> العقد `T_BLIND_PICK_prereg.md` والملحق 1 (`T_BLIND_PICK_addendum_1.md` · البطاقاتُ من الصفوف الكاملة) · آلةُ T-BASKET وضابطُها (`{BASKET_RUN}`) · الاختياراتُ في `blind_pick.vault` ({v['picks_at']}).", "",
         f"- الجلسات {len(v['sessions'])} · محسوبة {len(sess_ok)} · «أعرفه» {sum(1 for x in picks.values() if x == 'known')} · بلا ردّ "
         f"{len(v['sessions']) - len(picks)}", "",
         f"## الحاكم (بالأضعف) — الحكم: **{ev['verdict']}**", "",
         "| الخليّة | البطاقات | التغطية | n اختيار | n باقية | (أ) اختيار − الزخم | فاصل (أ) | (ب) اختيار − الباقية | فاصل (ب) | r الخام اختيار/باقية |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for arm, c in ev["cells"].items():
        L.append(f"| {arm} | {c['n_cards']} | {FC.cov_txt(c['coverage'])} | {c['n_true']} | {c['n_false']} | {FC.pct(c['a_mean'])} | "
                 f"{FC.ci_txt(c['a_ci'])} | {FC.pct(c['b_mean'])} | {FC.ci_txt(c['b_ci'])} | {FC.pct(c['raw_true'])} / {FC.pct(c['raw_false'])} |")
    bc = ev["best_ci"]
    L += ["", "## وصفًا لا حكمًا",
          f"- اختيارُك كان **الأفضلَ من الخمس** (r في O0) في {ev['best']} من {ev['best_n']} جلسة = "
          f"{(ev['best'] / ev['best_n'] * 100) if ev['best_n'] else 0:.1f}% مقابل 20% بالصدفة · ويلسون "
          f"{'—' if not bc else f'[{bc[0] * 100:.1f}%، {bc[1] * 100:.1f}%]'}", "",
          "## المفتاح (يُكشف بعد الحكم)", "", "| البطاقة | الرمز | يوم القرار | درجة §② | اختيار | r O0 | r O50 |", "|---|---|---|---|---|---|---|"]
    for r in sorted(recs, key=lambda r: [int(x) for x in r["label"].split("-")]):
        ro = lambda a: FC.pct(((r.get("res") or {}).get(a) or {}).get("r"))      # noqa: E731
        L.append(f"| {r['label']} | {r['sym']} | {r['d']} | {r['score']} | {'✅' if (r['sym'], r['d']) in picked else ''} | {ro('O0')} | {ro('O50')} |")
    L += ["", f"⚖️ blindpick: {ev['verdict']}"]
    txt = "\n".join(L) + "\n"
    open(RESULT, "w", encoding="utf-8").write(txt)
    print(txt)
    return RC_OK


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not contract_ok():
        log("⛔ العقد لا يطابق بصمتَه — خروج 11 قبل أيّ جلب")
        return RC_CONTRACT
    mode = argv[0] if argv else ""
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log("⛔ بلا مفتاح Polygon — خروج 2")
        return RC_KEY
    if mode == "cards":
        return mode_cards(key)
    if mode == "resend":
        return mode_cards(key, resend=True)
    if mode in ("count1", "cards1", "judge"):
        if not addendum_ok():
            log("⛔ الملحق 1 لا يطابق بصمتَه — خروج 11 قبل أيّ جلب")
            return RC_CONTRACT
    if mode in ("count1", "cards1"):
        return mode_a1(key, build=(mode == "cards1"))
    if mode == "judge":
        d_in = argv[argv.index("--dir") + 1] if "--dir" in argv else "bp_in"
        return mode_judge(key, os.environ.get("BLIND_PICKS", ""), d_in)
    return 1


if __name__ == "__main__":
    sys.exit(main())
