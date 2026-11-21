#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🗂️🔬 `T-CASE31` — ① ملفُّ كلّ سهم (من 20 جلسةً قبل يوم القرار إلى 10 بعد الانفجار) و② المسحُ الكامل عند يوم القرار.

قراءةٌ فقط: يقرأ مادّةَ `collect` وصفوفَ `feat` ويكتب `out/dossiers/<رمز>_<يوم القرار>.md` و`.features.json` و`out/DOSSIERS.md`.
لا تلغرام · لا Polygon · لا حكم — وصفٌ كلُّه، و«غير مقيس» لما لا مصدرَ له.
"""
import datetime as dt
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (HERE, ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import case31 as C                      # noqa: E402
import case31_catalog as CAT            # noqa: E402

BEFORE, AFTER = 20, 10                  # من المالك: 20 جلسةً قبل يوم القرار و10 بعد الانفجار
START_X = 1.15                          # «دقيقةُ البداية»: أوّلُ شمعةٍ لحظيّة أعلاها 15% فوق إغلاق يوم القرار (حدُّ بداية الحركة في العقد)
DELTA_SHOW = ("px.ret5", "px.ret20", "px.base20_w", "vol.usd_d", "vol.dry5_20", "vol.updown20", "vol.cmf20", "vol.obv_slope10", "sh.ratio_d",
              "sh.ratio5", "D.rsi14", "D.macd.hist_p", "D.mfi14", "D.adx14", "D.atr14_p", "D.bb.width", "D.sma20.dist", "D.sma50.dist",
              "D.sma200.dist", "H4.rsi14", "W.rsi14", "bot.readiness", "bot.n_out")


def log(m=""):
    print(m, flush=True)


def _n(x, d=2, pct=False):
    if x is None or x != x:
        return "غير مقيس"
    if isinstance(x, bool):
        return "نعم" if x else "لا"
    return f"{x * 100:.1f}%" if pct else (f"{x:,.0f}" if abs(x) >= 1000 else f"{x:.{d}f}")


def ny_parts(ts):
    """(نقيّة) طابعٌ بالثواني ⟵ (يومُ نيويورك، دقائقُ اليوم) — يراعي التوقيتَ الصيفيّ بقاعدة الأحد الثاني من مارس/الأوّل من نوفمبر."""
    u = dt.datetime.utcfromtimestamp(int(ts))
    y = u.year
    mar = dt.datetime(y, 3, 8) + dt.timedelta(days=(6 - dt.datetime(y, 3, 8).weekday()) % 7, hours=7)
    nov = dt.datetime(y, 11, 1) + dt.timedelta(days=(6 - dt.datetime(y, 11, 1).weekday()) % 7, hours=6)
    loc = u - dt.timedelta(hours=4 if mar <= u < nov else 5)
    return loc.date().isoformat(), loc.hour * 60 + loc.minute


def session_of(minute):
    return "قبل الافتتاح" if minute < 570 else ("الجلسة النظاميّة" if minute < 960 else "بعد الإغلاق")


def intraday_timing(frames, day_s, close_d, order=("1", "5", "15", "30", "60")):
    """(نقيّة) ⟵ توقيتُ البداية بأدقّ فريمٍ يغطّي يومَ البداية: {frame, start_min, session, high_min, pre_share, usd_before, n} أو None."""
    if not frames or not close_d or close_d <= 0:
        return None
    for fr in order:
        day = [b for b in (frames.get(fr) or []) if ny_parts(b[0])[0] == day_s]
        if len(day) < 2:
            continue
        thr = START_X * close_d
        hi = max(b[2] for b in day)
        st = next((b for b in day if b[2] >= thr), None)
        pre = [b for b in day if ny_parts(b[0])[1] < 570]
        out = {"frame": fr, "n": len(day), "day_high": hi, "high_min": ny_parts(max(day, key=lambda b: b[2])[0])[1],
               "pre_share": ((max(b[2] for b in pre) - close_d) / (hi - close_d)) if pre and hi > close_d else (0.0 if hi > close_d else None),
               "start_min": None, "session": None, "usd_before": None}
        if st:
            m = ny_parts(st[0])[1]
            out.update(start_min=m, session=session_of(m), usd_before=sum(b[4] * b[5] for b in day if b[0] < st[0]))
        return out
    return None


def hhmm(m):
    return "—" if m is None else f"{m // 60:02d}:{m % 60:02d}"


def price_table(rows_d, e):
    """(نقيّة) جدولُ السعر من 20 جلسةً قبل يوم القرار إلى 10 بعد القمّة · يَسِم يومَ القرار والبدايةَ والقمّة."""
    ix = {r[0]: k for k, r in enumerate(rows_d)}
    i, p = ix.get(e["D"]), ix.get(e["p"])
    if i is None:
        return ["غير مقيس — لا شمعةَ يومَ القرار"]
    hi = (p if p is not None else i) + AFTER
    L = ["| اليوم | الافتتاح | الأعلى | الأدنى | الإغلاق | التغيّر | الحجم بالدولار | وسم |", "|---|---|---|---|---|---|---|---|"]
    for k in range(max(0, i - BEFORE), min(len(rows_d), hi + 1)):
        d, o, h, lo, c, v = rows_d[k]
        ch = (c / rows_d[k - 1][4] - 1.0) if k and rows_d[k - 1][4] > 0 else None
        tag = " · ".join(t for t, on in (("يوم القرار", d == e["D"]), ("البداية", d == e["s"]), ("القمّة", d == e["p"]), ("أدنى إغلاق", d == e["b"])) if on)
        L.append(f"| {d} | {o:.4g} | {h:.4g} | {lo:.4g} | {c:.4g} | {_n(ch, pct=True)} | {c * v:,.0f} | {tag} |")
    return L


def feature_groups(f):
    """(نقيّة) المسحُ الكامل ⟵ أسطرٌ مقروءة: المتوسّطاتُ فوق/تحت لكلّ فريم · المذبذبات · الأنماطُ القائمة."""
    L = []
    for tf, nm in (("D", "اليوميّ"), ("H4", "4 ساعات"), ("W", "الأسبوعيّ")):
        ab = {"x": []}
        for kind in CAT.MA_KINDS:
            up = [str(n) for n in CAT.MA_LENS if f.get(f"{tf}.{kind}{n}.above") == 1]
            dn = [str(n) for n in CAT.MA_LENS if f.get(f"{tf}.{kind}{n}.above") == 0]
            ab["x"].append(f"{kind.upper()} فوق: {'·'.join(up) or '—'} / تحت: {'·'.join(dn) or '—'}")
        osc = " · ".join(f"{lab} {_n(f.get(f'{tf}.{key}'), 1)}" for lab, key in (("RSI14", "rsi14"), ("MACD-hist%", "macd.hist_p"), ("KST", "kst.diff"),
                         ("K", "stoch.k"), ("CCI", "cci20"), ("W%R", "willr14"), ("MFI", "mfi14"), ("ADX", "adx14"), ("ATR%", "atr14_p"),
                         ("%B", "bb.pctb"), ("Donchian20", "don20.pos")))
        flags = [n.split(".", 1)[1] for n, k, _a in CAT.expanded() if k == "bool" and n.startswith(tf + ".") and ".sma" not in n and ".ema" not in n
                 and not n.endswith((".d5", ".d10")) and f.get(n) == 1]
        L += [f"- **{nm}:** " + " ‖ ".join(ab["x"]), f"  - المذبذبات: {osc}", f"  - القائمُ من الأنماط والإشارات: {' · '.join(flags) or '—'}"]
    return L


def dossier_md(e, rows_d, f, meta, pool_row, tim, src, peers):
    s = e["sym"]
    cat = e.get("cat") or {}
    I = (meta.get("ident") or {}).get(s) or {}
    E = (meta.get("edgar") or {}).get(s) or {}
    g = lambda k, **kw: _n(f.get(k) if f else None, **kw)          # noqa: E731
    L = [f"# 🗂️ {s} — {('‏+100%' if e['cls'] == 'x100' else '‏+50%')} · {e['win']}", "",
         f"- يومُ القرار **{e['D']}** (إغلاق {e['close_D']:.4g}) · البداية {e['s']} · القمّة {e['p']} (أعلى {e['top']:.4g}) · **الحاكمة {e['gov'] * 100:.0f}%** · "
         f"جلساتُ الحركة {e['sessions']} · {'يومٌ واحد' if e['one_day'] else 'عدّة أيام'} · {'شمعةٌ واحدة' if e['one_candle'] else 'موجات'} · "
         f"{'بعد تقسيمٍ عكسيّ ' + str(e['rs_recent']) if e.get('rs_recent') else 'بلا تقسيمٍ عكسيٍّ حديث'} · المحفّز: {cat.get('status', 'غير مقيس')}"
         f"{' · في قائمة المالك' if e.get('owner') else ''}", "",
         "## أ · الهويّة", f"- السوق {I.get('_full', 'غير مقيس')} · القطاع {I.get('sector') or 'غير مقيس'} · الصناعة {I.get('industry') or 'غير مقيس'} · "
         f"الدولة {I.get('country') or 'غير مقيس'} · الفلوت {g('id.float')} · الأسهم {g('id.shares')} · القيمة السوقيّة {g('id.mcap')} · "
         f"عمرُ الإدراج بالجلسات {g('id.age_sessions', d=0)} · خيارات {g('id.has_options')} · SIC {E.get('sic') or 'غير مقيس'}",
         "- ⚠️ الهويّةُ من ماسح TradingView يومَ الجلب لا يومَ القرار (حدُّ صدق).", "",
         "## ب · تاريخُ الشركة والتمويل (EDGAR حتى يوم القرار)",
         f"- نشراتُ 424B: 90 يومًا {g('ed.n424b_90', d=0)} · سنة {g('ed.n424b_365', d=0)} · عمرُ آخرها {g('ed.age_424b', d=0)} يومًا · رفٌّ فعّال {g('ed.shelf_active')} · "
         f"S-1 خلال سنة {g('ed.s1_365')} · 8-K: 30 يومًا {g('ed.n8k_30', d=0)} و3 أيّام {g('ed.n8k_3', d=0)} · تغييرُ اسم {g('ed.name_change_365')} · "
         f"التقسيماتُ العكسيّة: سنة {g('cp.rs_n365', d=0)} والكلّ {g('cp.rs_n_all', d=0)} وعمرُ آخرها {g('cp.rs_age_days', d=0)} يومًا"]
    fl = [x for x in (E.get("filings") or []) if x[0] and x[0] <= e["D"]][:12]
    L += ["- آخرُ الإيداعات قبله: " + (" ‖ ".join(f"{d} {fm}{(' [' + it + ']') if it else ''}" for d, fm, it, _ds in fl) or "غير مقيس")]
    L += ["", "## ج · ضغطُ الإدراج", f"- إشعارُ نقصٍ خلال سنة {g('ed.defic_365')} · الأيّامُ الباقية على مهلته {g('ed.defic_days_left', d=0)} · "
          f"جلساتٌ تحت الدولار في 30 {g('px.below1_30', d=0)} · قربُ الدولار {g('px.near1')} · إيداعٌ متأخّر NT {g('ed.nt_365')}",
          "", "## د · الملكيّة", f"- نماذجُ 4 في 90 يومًا {g('ed.n_form4_90', d=0)} · 13D/G في 90 يومًا {g('ed.n_13dg_90', d=0)} · ملكيّةُ المؤسّسات: "
          "غير مقيس (حصّادُ المؤسّسات الأسبوعيّ بدأ 2026-11-16)",
          "", "## هـ · التقويم", f"- عمرُ آخر نتائج {g('ed.results_age', d=0)} يومًا · نتائجُ متوقَّعة خلال 30 يومًا {g('ed.results_due30')} · دعوةُ مساهمين خلال 75 يومًا {g('ed.proxy_75')}",
          "", "## و · السعر"] + price_table(rows_d, e)
    L += ["", f"- الهبوطُ من قمّة 252 جلسة {g('px.drop252', pct=True)} · البعدُ عن أدنى سعرٍ تاريخيّ {g('px.atl_dist', pct=True)} · عرضُ قاعدة 20/40/60 جلسة "
          f"{g('px.base20_w', pct=True)} / {g('px.base40_w', pct=True)} / {g('px.base60_w', pct=True)} · عائد 5/20/60 جلسة {g('px.ret5', pct=True)} / "
          f"{g('px.ret20', pct=True)} / {g('px.ret60', pct=True)} · انفجاراتٌ سابقة {g('px.expl_n', d=0)} (عمرُ آخرها {g('px.expl_age', d=0)} جلسة)",
          "", "## ز · الحجم والتجميع", f"- وسيطُ قيمة التداول 20 جلسة {g('vol.usd_med20')} $ · يومَ القرار {g('vol.usd_d')} $ · جفافُ 5 مقابل 20 {g('vol.dry5_20')} · "
          f"قفزةُ اليوم {g('vol.spike_d')} · صاعدٌ/هابط 20 {g('vol.updown20')} · ميلُ OBV 10/20 {g('vol.obv_slope10')} / {g('vol.obv_slope20')} · CMF20 {g('vol.cmf20')} · "
          f"تدويرُ الفلوت يومَ القرار {g('id.float_turn_d', pct=True)} وفي 20 جلسة {g('id.float_turn20', pct=True)}",
          "", "## ح · الشورت والاقتراض", f"- نسبةُ شورت FINRA يومَ القرار {g('sh.ratio_d', pct=True)} · 5 جلسات {g('sh.ratio5', pct=True)} · 10 جلسات {g('sh.ratio10', pct=True)} · "
          f"حجمُه {g('sh.vol_d')} · المتاحُ للاقتراض {g('bw.avail')} والرسوم {g('bw.fee')} (حصادُ البوت خلال 7 أيّام)"]
    bw = [x for x in ((meta.get("ledgers") or {}).get("borrow") or {}).get(s, []) if x[0] and x[0] <= e["p"]][-8:]
    if bw:
        L.append("- قراءاتُ حصاد البوت: " + " ‖ ".join(f"{d} متاح {_n(a, 0)} رسوم {_n(fe, 1)}" for d, a, fe in bw))
    L += ["", "## ط · المحفّز وما بعده", f"- الحالة: **{cat.get('status', 'غير مقيس')}** · النوع: {cat.get('type') or '—'}"]
    for it in (cat.get("filings") or [])[:6]:
        L.append(f"  - إيداع {it}")
    for it in (cat.get("news") or [])[:6]:
        L.append(f"  - خبر {it}")
    off = cat.get("offer_after")
    L.append("- طرحٌ خلال 10 جلسات بعد البداية: " + ("غير مقيس" if off is None else (" ‖ ".join(f"{x['d']} {x['form']}" for x in off) or "لا")))
    L += ["", "## ي · التوقيتُ اللحظيّ (أدقُّ فريمٍ متاح مع الجلسة الممتدّة)"]
    if tim:
        L.append(f"- الفريم {tim['frame']} د ({tim['n']} شمعة يومَ البداية) · دقيقةُ البداية {hhmm(tim['start_min'])} نيويورك — **{tim['session'] or 'لم تُبلغ عتبةُ البداية لحظيًّا'}** · "
                 f"قمّةُ اليوم {hhmm(tim['high_min'])} · حصّةُ ما قبل الافتتاح من صعود اليوم {_n(tim['pre_share'], pct=True)} · قيمةُ التداول قبل البداية {_n(tim['usd_before'])} $")
    else:
        L.append("- غير مقيس — لا شموعَ لحظيّة تغطّي يومَ البداية في TradingView")
    L += ["", "## ك · حالةُ البوت يومَ القرار"]
    if pool_row:
        w = pool_row.get("wall") or {}
        od = " ‖ ".join(f"{x.get('label') or x.get('name')} (القيمة {_n(x.get('v'))} · الحدّ {_n(x.get('edge'))} · هامش {_n(x.get('margin'), 1)}%)" for x in pool_row.get("out_detail") or [])
        L.append(f"- في «تحت المتابعة»: نعم · الجاهزيّة {_n(pool_row.get('readiness'), 0)} · النواقص {_n(pool_row.get('n_out'), 0)} · الجدار: {w.get('label') or '—'} · "
                 f"الناقص: {od or '—'} · محجوب: {(pool_row.get('blocked') or {}).get('label') or 'لا'} · أوّلُ ظهور {pool_row.get('first_seen') or '—'}")
    else:
        L.append("- في «تحت المتابعة»: لا (أو لا لقطةَ ليومه)")
    L.append(f"- رفضُ الفرز بأرقام الإنتاج على شموع يوم القرار: {src.get('bot_reject') or 'غير مقيس'} · في القائمة {g('bot.in_list')} · في الارتداد {g('bot.in_pullback')} · "
             f"منشورُ فيصل خلال 30 يومًا {g('bot.faisal_post30')} · أدواتٌ نبّهت خلال 20 جلسة: " +
             (" · ".join(k.split('tool20_')[1] for k in ("bot.tool20_split_hunter", "bot.tool20_split_filter", "bot.tool20_method", "bot.tool20_press",
                                                        "bot.tool20_envelope", "bot.tool20_three") if f and f.get(k) == 1) or "لا شيء"))
    posts = sorted(set(((meta.get("ledgers") or {}).get("posts") or {}).get(s, [])))
    L.append("- منشوراتُ فيصل المسجَّلة للرمز: " + (" · ".join(posts[-8:]) or "لا شيء"))
    L += ["", "## ل · السوق والعدوى", f"- منفجرون في القطاع/الصناعة/الدولة خلال 3 جلسات: {g('ct.sector3', d=0)} / {g('ct.industry3', d=0)} / {g('ct.country3', d=0)} · "
          f"منفجرون آخرون بيوم القرار نفسِه: {' · '.join(peers) or 'لا أحد'}",
          "", "## م · تغيّرُ السمات في 5 و10 جلسات", "", "| السمة | يومَ القرار | التغيّر في 5 | التغيّر في 10 |", "|---|---|---|---|"]
    for nm in DELTA_SHOW:
        L.append(f"| `{nm}` | {g(nm)} | {g(nm + '.d5')} | {g(nm + '.d10')} |")
    L += ["", "## ② المسحُ الكامل عند يوم القرار (كلُّ القيم في الملفّ المرافق `.features.json`)"] + (feature_groups(f) if f else ["غير مقيس"])
    lead = src.get("dd_before")
    L += ["", f"- أقصى سحبٍ بين افتتاح اليوم التالي للقرار وبداية الحركة: {_n(lead, pct=True)}", ""]
    return "\n".join(L)


def mode_dossier(d_data, d_feat):
    import case31_arm as A
    import case31_build as B
    import tv_data as TV
    P, meta, bars_d = B._load(d_data, "plan.pkl.gz"), B._load(d_data, "meta.pkl.gz"), B._load(d_data, "bars_d.pkl.gz")
    if not P or not meta or bars_d is None:
        log(f"⛔ مادّةُ collect ناقصة — خروج {C.RC_DATA}")
        return C.RC_DATA
    feat = {(r["sym"], r["D"]): r for r in A.load_feat(d_feat) if r.get("ev")}
    plan, pools = P["plan"], P["pools"]
    out_dir = os.path.join(C.OUT, "dossiers")
    os.makedirs(out_dir, exist_ok=True)
    index = []
    for e in plan["events"]:
        if e["cls"] != "x100":
            continue
        s = e["sym"]
        rows_d = [(TV.ny_day(b[0]), b[1], b[2], b[3], b[4], b[5]) for b in bars_d.get(s) or []]
        src = feat.get((s, e["D"])) or {}
        f = src.get("f") if src.get("ok") else None
        tim = intraday_timing((meta.get("minute") or {}).get(s), e["s"], e["close_D"])
        row = ((pools.get(e["D"]) or {}).get("rows") or {}).get(s)
        peers = sorted(x["sym"] for x in plan["events"] if x["cls"] == "x100" and x["D"] == e["D"] and x["sym"] != s)
        md = dossier_md(e, rows_d, f, meta, row, tim, src, peers)
        with open(os.path.join(out_dir, f"{s}_{e['D']}.md"), "w", encoding="utf-8") as fh:
            fh.write(md)
        if f is not None:
            with gzip.open(os.path.join(out_dir, f"{s}_{e['D']}.features.json.gz"), "wt", encoding="utf-8") as fh:
                json.dump({n: f.get(n) for n, _k, _a in CAT.expanded()}, fh)
        cat = e.get("cat") or {}
        index.append({"sym": s, "D": e["D"], "s": e["s"], "p": e["p"], "gov": e["gov"], "win": e["win"], "owner": e.get("owner"), "tracked": bool(row),
                      "one_day": e["one_day"], "one_candle": e["one_candle"], "rs_recent": e.get("rs_recent"), "cat": cat.get("status"),
                      "offer_after": None if cat.get("offer_after") is None else len(cat["offer_after"]), "timing": tim,
                      "bot_reject": src.get("bot_reject"), "wall": ((row or {}).get("wall") or {}).get("label"), "readiness": (row or {}).get("readiness"),
                      "has_features": f is not None})
    with open(os.path.join(C.OUT, "dossiers", "index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=1)
    known = [x for x in index if x["timing"] and x["timing"].get("session")]
    L = ["# 🗂️ `T-CASE31` — ① فهرسُ الملفّات (مولَّدٌ آليًّا · وصفٌ لا حكم)", "",
         f"- ملفّات {len(index)} · بسماتٍ كاملة {sum(x['has_features'] for x in index)} · بتوقيتٍ لحظيّ {len(known)} · "
         f"بدأت خارج الجلسة النظاميّة {sum(1 for x in known if x['timing']['session'] != 'الجلسة النظاميّة')} من {len(known)}",
         "- أعطالُ أُسَرٍ غيرِ شمعيّة في الشرائح (سماتُها «غير مقيس» ولم يتوقّف التشغيل): "
         + (" · ".join(f"{k} × {v:,}" for k, v in sorted(A.family_errors(d_feat).items())) or "لا شيء"), "",
         "| السهم | النافذة | يوم القرار | البداية | الحاكمة | المحفّز | بدايةُ الحركة | في المتابعة | رفضُ الفرز | طرحٌ بعده |", "|---|---|---|---|---|---|---|---|---|---|"]
    for x in sorted(index, key=lambda x: (x["win"], x["D"], x["sym"])):
        t = x["timing"] or {}
        L.append(f"| [{x['sym']}](dossiers/{x['sym']}_{x['D']}.md) | {x['win']} | {x['D']} | {x['s']} | {x['gov'] * 100:.0f}% | {x['cat'] or 'غير مقيس'} | "
                 f"{(hhmm(t.get('start_min')) + ' ' + (t.get('session') or '')) if t else 'غير مقيس'} | {'نعم' if x['tracked'] else 'لا'} | {x['bot_reject'] or '—'} | "
                 f"{'غير مقيس' if x['offer_after'] is None else x['offer_after']} |")
    with open(os.path.join(C.OUT, "DOSSIERS.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    log("\n".join(L[:4]))
    return C.RC_OK


def main(argv):
    if not C.contract_ok():
        return C.RC_CONTRACT
    os.environ.pop("POLYGON_API_KEY", None)
    if len(argv) > 1 and argv[1] == "dossier":
        d_data = argv[argv.index("--data") + 1] if "--data" in argv else os.path.join(ROOT, "case31_data")
        d_feat = argv[argv.index("--feat") + 1] if "--feat" in argv else os.path.join(ROOT, "case31_feat")
        return mode_dossier(d_data, d_feat)
    log("الاستعمال: case31_dossier.py dossier --data D --feat F")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
