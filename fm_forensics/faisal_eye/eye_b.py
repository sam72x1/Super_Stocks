#!/usr/bin/env python3
"""👁️ `T-FAISAL-EYE` — المرحلتان ب وج (العقد `T_FAISAL_EYE_prereg.md` §③ · §④ · أمرُ المالك 2026-11-21).

  files     — ملفُّ «عين فيصل» لكلّ صورةٍ مؤرَّخة ⟵ `files/<id>.md` ‏+ `out/FILES.json`
  summary   — الخلاصة والرابط المشترك ⟵ `out/SUMMARY.json|md`

🔒 قياسٌ فقط: لا تلغرام · لا Polygon · لا إنتاج · بلا سمةٍ جديدة (فهرسُ `T-CASE31` كما هو) · والمستوياتُ من `data/levels_cards.jsonl`
المودَع قبل أيّ نتيجة · والشموعُ `data/bars/` (TradingView) المودعة.
"""
import datetime as dt
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
for p in (HERE, ROOT, os.path.join(ROOT, "fm_forensics", "case31")):
    if p not in sys.path:
        sys.path.insert(0, p)
import eye as E                          # noqa: E402

FILES = os.path.join(HERE, "files")
LEVELS = os.path.join(E.DATA, "levels_cards.jsonl")
NEAR, WEEKLY = "near_watch.json", "weekly_watchlist.json"
WIN_BEFORE, WIN_AFTER, WIN_NONE, WIN_LINK = 60, 20, 60, 20        # العقد §③-2 · §③-4 · §④-3
TOUCH_TOL, RECLAIM_N = 0.02, 5                                    # العقد §③-6
FLOOR, SHUFFLES, Q = 20, 1000, 0.95                               # العقد §④
CAT = {"ENTRY": "دخول", "READY": "دخول", "WATCH": "تحت المتابعة فقط", "FOCUS": "تحت المتابعة فقط", "WAIT": "انتظار مستوى",
       "EXIT": "تحذير", "REJECT": "تحذير"}


def log(m=""):
    print(m, flush=True)


# ══ نقيّة ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def image_ny(i, src, rec, hdr):
    """⟵ وقتُ الصورة بنيويورك: الطابعُ (الرأس · EDT مطبوع) أو سجلُّ العين (الرياض ⟵ نيويورك)."""
    from zoneinfo import ZoneInfo
    if src == "header":
        h = hdr[i]
        t = dt.datetime.strptime(f"{h['date']} {h['hour'] or '20:00'}", "%Y-%m-%d %H:%M")
        return t.replace(tzinfo=ZoneInfo("America/New_York"))
    return E.truth_ny(rec)


def source_of(i, rec):
    """«منشور» · «خاص» · «واتساب» · «غير معروف» من البادئة ونصّ `seen` (العقد §③-1)."""
    seen = (rec or {}).get("seen") or ""
    if "واتساب" in seen or "WhatsApp" in seen:
        return "واتساب"
    if "خاص" in seen or "DM" in seen or "رسائل" in seen:
        return "خاص"
    if i.startswith(("X_", "IMG_", "TG_", "EDU_")):
        return "منشور"
    return "غير معروف"


def position(rows, k, evs):
    """(نقيّة) موقعُ D (رقم الشمعة k) من الأحداث (العقد §③-2) ⟵ (الوسم، الحدث)."""
    for ev in evs:
        if ev["ix"]["s"] <= k <= ev["ix"]["p"]:
            return "أثناء", ev
    for ev in evs:
        if ev["ix"]["p"] < k <= ev["ix"]["p"] + WIN_AFTER:
            return "بعده", ev
    for ev in evs:
        if k < ev["ix"]["s"] <= k + WIN_BEFORE:
            return "قبله", ev
    return "لا انفجار خلال 60", None


def before_metrics(rows, k, ev):
    c0 = rows[k][4]
    s = ev["ix"]["s"]
    low = min((r[3] for r in rows[k + 1:s + 1]), default=None)
    return {"sessions": s - k, "reached": ev["top"] / c0 - 1.0 if c0 > 0 else None,
            "max_dd": (low / c0 - 1.0) if (low is not None and c0 > 0) else None, "s": ev["s"], "p": ev["p"]}


def none_metrics(rows, k):
    c0 = rows[k][4]
    w = rows[k + 1:k + 1 + WIN_NONE]
    if not w or c0 <= 0:
        return {}
    return {"max_up": max(r[2] for r in w) / c0 - 1.0, "max_dd": min(r[3] for r in w) / c0 - 1.0, "today": rows[-1][4] / c0 - 1.0,
            "n": len(w)}


def levels_outcome(rows, k, lv, f):
    """(نقيّة) مستوياتُه مقابل ما حصل خلال 60 جلسة (العقد §③-6) · `f` = معاملُ الخامّ ⟵ المستوى المسوّى = المستوى ÷ f."""
    w = rows[k + 1:k + 1 + WIN_NONE]
    out = {}
    adj = (lambda x: x / f) if f else (lambda x: x)
    sup = lv.get("support") if lv.get("support") is not None else lv.get("entry")
    if sup is not None:
        a = adj(sup)
        t = next((j for j, r in enumerate(w, 1) if r[3] <= a * (1 + TOUCH_TOL)), None)
        out["touch"] = t
        sw = None
        for j, r in enumerate(w, 1):
            if r[3] < a:
                back = next((q for q in range(j, min(len(w), j + RECLAIM_N) + 1) if w[q - 1][4] > a), None)
                if back:
                    sw = back
                    break
        out["sweep_reclaim"] = sw
    if lv.get("target") is not None:
        a = adj(lv["target"])
        out["target"] = next((j for j, r in enumerate(w, 1) if r[2] >= a), None)
    if lv.get("stop") is not None:
        a = adj(lv["stop"])
        out["stop"] = next((j for j, r in enumerate(w, 1) if r[3] <= a), None)
    if "target" in out and "stop" in out:
        t, s = out["target"], out["stop"]
        out["first"] = None if (t is None and s is None) else ("هدف" if s is None or (t is not None and t < s) else
                                                                   ("وقف" if t is None or s < t else "اليوم نفسه"))
    return out


def shuffle_test(xa, xb, n=SHUFFLES, seed=20261121):
    """(نقيّة) فرقُ المتوسّطين وموقعُه من 1000 خلط ⟵ (الفرق، نسبةُ الخلطات الأصغر)."""
    a, b = [x for x in xa if x is not None], [x for x in xb if x is not None]
    if len(a) < 2 or len(b) < 2:
        return None, None
    obs = sum(a) / len(a) - sum(b) / len(b)
    rnd, pool, le = random.Random(seed), a + b, 0
    for _ in range(n):
        rnd.shuffle(pool)
        d = sum(pool[:len(a)]) / len(a) - sum(pool[len(a):]) / len(b)
        le += int(abs(d) < abs(obs))
    return obs, le / n


# ══ الملفّات ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _daily(B):
    return [(b[0], float(b[1]), float(b[2]), float(b[3]), float(b[4]), float(b[5])) for b in (B.get("1D") or [])]


def _frames(B):
    import pandas as pd
    import tv_data as TV
    rd = _daily(B)
    dfD = pd.DataFrame([r[1:] for r in rd], columns=["Open", "High", "Low", "Close", "Volume"], index=pd.to_datetime([r[0] for r in rd]))
    rh = B.get("4H") or []
    dfH = pd.DataFrame([b[1:] for b in rh], columns=["Open", "High", "Low", "Close", "Volume"],
                       index=pd.to_datetime([TV.ny_time(int(b[0])).replace(tzinfo=None) for b in rh])) if rh else None
    return dfD, dfH


def bot_on(day, sym, cache):
    import case31_build as CB
    out = {}
    for path in (NEAR, WEEKLY):
        snaps = cache.setdefault(path, CB.snapshots(path))
        hit = CB.snap_for(snaps, day)
        if not hit:
            out[path] = "لا لقطة"
            continue
        js = cache.setdefault((path, hit[1]), CB.git_json(hit[1], path))
        if path == NEAR:
            row = CB.measured_rows(js).get(sym.upper())
            out[path] = {"in": bool(row), "readiness": (row or {}).get("readiness"), "snap": hit[0][:10]}
        else:
            st = [s for s in (js.get("stocks") or []) if str(s.get("symbol", "")).upper() == sym.upper()]
            out[path] = {"in": bool(st), "snap": hit[0][:10]}
    return out


def build_rows():
    import case31 as C31
    import case31_feat as F
    D = E.dated_set()
    R = {r["id"]: r for r in E.records()}
    H = {r["file"]: r for r in E.header_rows()}
    LV = E._load_jsonl(LEVELS)
    cache, rows = {}, []
    for i, v in sorted(D.items()):
        sym, rec = v["sym"], R.get(i, {})
        r = {"id": i, "sym": sym, "src": v["src"], "source": source_of(i, rec), "q": rec.get("q") or "",
             "cat": CAT.get(rec.get("st") or "", "غير مصنّف"), "st": rec.get("st")}
        B = E.load_bars(sym)
        d = _daily(B) if B else []
        if not d:
            r["why"] = "بلا شموع (مشطوب أو غائبٌ عن TradingView)"
            rows.append(r)
            continue
        t = image_ny(i, v["src"], rec, H)
        k = E.truth_index("1D", d, t)
        if k is None:
            r["why"] = "قبل أوّل شمعة"
            rows.append(r)
            continue
        f = E.split_factor(B.get("splits"), d[k][0])
        r.update(D=d[k][0], close_adj=d[k][4], close_raw=d[k][4] * f, factor=f)
        ev100 = C31.find_events(d, d[0][0], d[-1][0], 2.0)
        ev50 = C31.find_events(d, d[0][0], d[-1][0], 1.5)
        pos, ev = position(d, k, ev100)
        pos50, ev5 = position(d, k, ev50)
        r.update(pos=pos, pos50=pos50)
        if pos == "قبله":
            r["before"] = before_metrics(d, k, ev)
        if pos50 == "قبله":
            r["before50"] = before_metrics(d, k, ev5)
        if pos == "لا انفجار خلال 60":
            r["none"] = none_metrics(d, k)
        r["x100_in20"] = bool(ev and pos == "قبله" and r["before"]["sessions"] <= WIN_LINK)
        lv = LV.get(i)
        if lv:
            r["levels"] = {kk: vv for kk, vv in lv.items() if kk not in ("id", "sym")}
            r["lv_out"] = levels_outcome(d, k, lv, f)
        try:
            dfD, dfH = _frames(B)
            feats = F.features_asof(dfD, dfH, d[k][0], f)
            r["feat"] = {kk: (vv if isinstance(vv, (int, float, str, bool)) or vv is None else str(vv)) for kk, vv in feats.items()}
        except Exception as e:                                       # noqa: BLE001
            r["feat_err"] = f"{type(e).__name__}: {e}"
        try:
            r["bot"] = bot_on(d[k][0], sym, cache)
        except Exception as e:                                       # noqa: BLE001
            r["bot"] = f"⛔ {type(e).__name__}"
        rows.append(r)
    return rows


def pct(x):
    return "—" if x is None else f"{x * 100:+.1f}%"


def write_file(r):
    L = [f"# 👁️ {r['id']} · ${r['sym']}", "",
         f"- **D:** {r.get('D', '—')} · إغلاقُ D (TradingView): {r.get('close_adj', '—')} · بمقياس يومها {r.get('close_raw', '—')} (معامل {r.get('factor', '—')})",
         f"- **المصدر:** {r['source']} · التأريخ: {'طابعُ الرأس' if r['src'] == 'header' else 'سجلُّ العين (EXACT)'}",
         f"- **الموقع من الحركة (‏+100%):** {r.get('pos', r.get('why', '—'))} · وذراعُ ‏+50%: {r.get('pos50', '—')}"]
    b = r.get("before")
    if b:
        L.append(f"- **قبل الانفجار:** {b['sessions']} جلسة إلى البداية ({b['s']}) · بلغ {pct(b['reached'])} من إغلاق D (القمّة {b['p']}) · وأقصى هبوطٍ قبلها {pct(b['max_dd'])}")
    n = r.get("none")
    if n:
        L.append(f"- **لا انفجار خلال 60:** أقصى صعود {pct(n.get('max_up'))} · أقصى هبوط {pct(n.get('max_dd'))} · واليوم {pct(n.get('today'))}")
    L.append(f"- **كلامُه ({r['cat']}):** «{r['q']}»" if r["q"] else f"- **كلامُه:** — ({r['cat']})")
    if r.get("levels"):
        o = r.get("lv_out") or {}
        L.append(f"- **مستوياتُه:** {json.dumps(r['levels'], ensure_ascii=False)} ⟵ لمسُ الدعم: {o.get('touch')} · كنسٌ ثمّ استعادة: {o.get('sweep_reclaim')}"
                 f" · الهدف: {o.get('target')} · الوقف: {o.get('stop')} · الأوّل: {o.get('first')} (بالجلسات بعد D)")
    if r.get("feat"):
        keys = [k for k in sorted(r["feat"]) if not k.startswith("sh.")][:40]
        L.append("- **سماتُ D (فهرس T-CASE31 · أوّلُ 40 · الكاملُ في FILES.json):** " + " · ".join(f"{k}={r['feat'][k]}" for k in keys))
    if r.get("bot"):
        L.append(f"- **عند البوت يوم D:** {json.dumps(r['bot'], ensure_ascii=False)}")
    os.makedirs(FILES, exist_ok=True)
    with open(os.path.join(FILES, f"{r['id']}.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


def mode_files():
    rows = build_rows()
    for r in rows:
        write_file(r)
    os.makedirs(E.OUT, exist_ok=True)
    with open(os.path.join(E.OUT, "FILES.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=1, default=str)
    log(f"✅ ملفّات {len(rows)} · بلا شموع {sum(1 for r in rows if r.get('why'))}")
    return 0


# ══ الخلاصة ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def summarize(rows):
    ok = [r for r in rows if r.get("pos")]
    cnt = {}
    for r in ok:
        cnt[r["pos"]] = cnt.get(r["pos"], 0) + 1
    bef = [r["before"] for r in ok if r.get("before")]
    ss = sorted(b["sessions"] for b in bef)
    dd = sorted(b["max_dd"] for b in bef if b["max_dd"] is not None)
    med = (lambda xs: xs[len(xs) // 2] if xs else None)
    link_n = sum(1 for r in ok if r.get("x100_in20"))
    cats = {}
    for r in ok:
        c = cats.setdefault(r["cat"], [0, 0])
        c[0] += 1
        c[1] += int(bool(r.get("x100_in20")))
    lv = [r.get("lv_out") or {} for r in ok if r.get("lv_out")]
    tg = [o for o in lv if "target" in o]
    sp = [o for o in lv if "stop" in o]
    S = {"n_dated": len(rows), "n_bars": len(ok), "no_bars": [r["id"] for r in rows if not r.get("pos")], "positions": cnt,
         "before": {"n": len(bef), "sessions_median": med(ss), "sessions_min": ss[0] if ss else None, "sessions_max": ss[-1] if ss else None,
                    "dd_median": med(dd), "dd_worst": dd[0] if dd else None},
         "link_floor": FLOOR, "link_n": link_n, "statistical": link_n >= FLOOR,
         "cats": {k: {"n": v[0], "x100_in20": v[1]} for k, v in cats.items()},
         "target": {"n": len(tg), "hit": sum(1 for o in tg if o["target"] is not None)},
         "stop": {"n": len(sp), "hit": sum(1 for o in sp if o["stop"] is not None)},
         "first": {k: sum(1 for o in lv if o.get("first") == k) for k in ("هدف", "وقف", "اليوم نفسه")}}
    # §④-3 وصفيًّا: متوسّطُ السمات الرقميّة للمنفجر خلال 20 مقابل غيره (أ) · والخلطُ فقط إن بلغت الأرضيّة
    yes = [r for r in ok if r.get("x100_in20") and r.get("feat")]
    no = [r for r in ok if not r.get("x100_in20") and r.get("feat")]
    keys = sorted({k for r in yes for k, v in r["feat"].items() if isinstance(v, (int, float)) and not isinstance(v, bool)})
    desc = []
    for k in keys:
        a = [r["feat"].get(k) for r in yes if isinstance(r["feat"].get(k), (int, float))]
        b = [r["feat"].get(k) for r in no if isinstance(r["feat"].get(k), (int, float))]
        if len(a) >= 2 and len(b) >= 2:
            row = {"f": k, "yes_mean": sum(a) / len(a), "no_mean": sum(b) / len(b), "n_yes": len(a), "n_no": len(b)}
            if S["statistical"]:
                row["obs"], row["q"] = shuffle_test(a, b)
            desc.append(row)
    S["link_desc"] = desc
    return S


def mode_summary():
    p = os.path.join(E.OUT, "FILES.json")
    if not os.path.exists(p):
        log("⛔ شغّل files أوّلًا")
        return 5
    rows = json.load(open(p, encoding="utf-8"))
    S = summarize(rows)
    with open(os.path.join(E.OUT, "SUMMARY.json"), "w", encoding="utf-8") as fh:
        json.dump(S, fh, ensure_ascii=False, indent=1, default=str)
    log(json.dumps({k: v for k, v in S.items() if k != "link_desc"}, ensure_ascii=False, default=str))
    return 0


def main(argv):
    if E.closed():
        log(f"🔒 مُغلَق — خروج {E.RC_CLOSED}")
        return E.RC_CLOSED
    if not E.contract_ok():
        log(f"⛔ العقدُ تغيّر — خروج {E.RC_CONTRACT}")
        return E.RC_CONTRACT
    if len(argv) >= 2 and argv[1] == "files":
        return mode_files()
    if len(argv) >= 2 and argv[1] == "summary":
        return mode_summary()
    log(__doc__)
    return 5


if __name__ == "__main__":
    sys.exit(main(sys.argv))
