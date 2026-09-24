# -*- coding: utf-8 -*-
"""🧪 **تقييمُ مُعرِّف الشارت** — `chart_finder_prereg.md §③-§⑤`.

  `CHART_EVAL=synth` ⟵ **المجموعةُ المصنوعة (ضبطٌ لا قبول):** بذرةٌ ثابتة `SEED` ⟵ نوافذُ حقيقيّة من
      لوحة السوق (خامًا ثم مُسوّاةً بالتقسيم حتى نهايتها) ⟵ `chart_render` بنمطٍ مسحوب ⟵ بطاقةٌ آليّة **من
      النصّ المرسوم وحدَه** (تسميتا أعلى/أدنى الشاشة · وسمُ آخر سعر · تواريخُ المحور) ⟵ `run_card` على
      **اللوحة نفسِها محقونةً** (لا تحميلَ لكلّ بطاقة) ⟵ الأوّلُ الصحيح · ضمن أوّل 3 · دقّةُ «واثق» ·
      وقراءةُ البكسل (متوسّطُ الخطأ النسبيّ للأعلى/الأدنى/الإغلاق وارتباطُ الإغلاقات).
  `CHART_EVAL=real` ⟵ **المجموعةُ الحقيقيّة (قبول):** بطاقاتُ `chart_cards/real/*.json` بعد التحقّق من
      بصمتها `MANIFEST.sha256` ⟵ `run_card` ⟵ مقارنةٌ بـ`KEY.tsv` (لا يقرؤه البحث) ⟵ `K1`/`K2`/`K3` وسطرُ
      `CHART_EVAL_JUDGE` بالفرع المنصوص.

🔒 قراءةٌ فقط · لا تلغرام · لا تُدفع صورة (الصورُ المصنوعة في الذاكرة) · والعتباتُ من `chart_finder`
   نفسِه — **لا نسخةَ خاصّةً بالتقييم** (التقييمُ يقيس الأداةَ كما تُشحن).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import random
import sys
import tempfile

import chart_finder as CF

SEED = 20260924
N_SYNTH = int(os.environ.get("CHART_EVAL_N") or 150)
SYNTH_FROM, SYNTH_TO = "2023-10-01", "2025-12-31"     # داخل «آخر 3 سنوات» يومَ التقييم
W_MIN, W_MAX = 20, 90
PRICE_MIN, PRICE_MAX = 0.3, 50.0
REAL_DIR = "chart_cards/real"
REAL_DIRS = {"real": REAL_DIR, "real2": "chart_cards/real2"}   # real2 = مجموعةُ ملحق §⑩ (v1.1)
K1_MIN_N, K2_MIN_N = 10, 20
K1_BAR, K2_BAR = 0.95, 0.80


def log(m: str = "") -> None:
    print(m, flush=True)


def wilson_low(k: int, n: int, z: float = 1.96) -> float:
    """حدُّ Wilson الأدنى لنسبةٍ `k/n` (95%)."""
    if n <= 0:
        return float("nan")
    p = k / n
    den = 1 + z * z / n
    centre = p + z * z / (2 * n)
    adj = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - adj) / den


# ══ المصنوعة ═══════════════════════════════════════════════════════════════════
def sample_windows(days, syms, H, L, C, rng: random.Random, n: int, tries: int = 200000) -> list:
    """`n` نافذةً `(رمز، فهرسُ النهاية، الطول)` بالسحب المنتظم — نهايتُها في [SYNTH_FROM، SYNTH_TO] ·
    سعرُ النهاية في [PRICE_MIN، PRICE_MAX] · وكلُّ شموعها موجودة (لا فجوة)."""
    import numpy as np                                              # noqa: PLC0415
    ends = [i for i, d in enumerate(days) if SYNTH_FROM <= d <= SYNTH_TO]
    out, seen = [], set()
    for _ in range(tries):
        if len(out) >= n or not ends:
            break
        e = rng.choice(ends)
        j = rng.randrange(len(syms))
        W = rng.randint(W_MIN, W_MAX)
        a = e - W + 1
        if a < 0 or (j, e) in seen:
            continue
        c = C[e, j]
        if not (np.isfinite(c) and PRICE_MIN <= c <= PRICE_MAX):
            continue
        if not np.isfinite(C[a:e + 1, j]).all():
            continue
        seen.add((j, e))
        out.append((syms[j], e, W))
    return out


def display_bars(days, H, L, C, j: int, e: int, W: int, splits: list) -> list:
    """الشموعُ كما يعرضها شارتٌ التُقط يومَ النهاية: خامٌ × معاملُ التقسيم حتى ذلك اليوم.
    (اللوحةُ تحمل H/L/C ⟵ الافتتاحُ = إغلاقُ الأمس المُسوّى، وأوّلُها = إغلاقُه.)"""
    as_of = days[e]
    out, prev = [], None
    for i in range(e - W + 1, e + 1):
        f = CF.split_factor(splits, days[i], as_of)
        h, lo, c = float(H[i, j]) * f, float(L[i, j]) * f, float(C[i, j]) * f
        o = prev if prev is not None else c
        o = min(max(o, lo), h)
        out.append({"o": o, "h": h, "l": lo, "c": c, "d": days[i]})
        prev = c
    return out


def split_case(bars: list, splits) -> str:
    """حالةُ التقسيم في نافذةٍ مصنوعة (العقد §⑧-6): «none» بلا تقسيمٍ داخلها · «inside» تقسيمٌ داخلها
    وأحدُ طرفَي الشاشة خامٌ على الأقل · «both_before» الطرفان كلاهما قبله (لا طرفَ خامًا ⇒ المرشِّحُ الخامّ
    في المسار بلا تاريخ لا يلتقطها بالبناء)."""
    if not bars:
        return "none"
    first, as_of = bars[0]["d"], bars[-1]["d"]
    inside = any(first < ex <= as_of for ex, fr, to in (splits or ())
                 if fr and to and float(fr) != float(to))
    if not inside:
        return "none"
    d_hi = max(bars, key=lambda b: b["h"])["d"]
    d_lo = min(bars, key=lambda b: b["l"])["d"]
    raw = [CF.split_factor(splits, d, as_of) == 1.0 for d in (d_hi, d_lo)]
    return "inside" if any(raw) else "both_before"


def synth_style(rng: random.Random) -> dict:
    return {"theme": rng.choice(["light", "dark"]),
            "log": rng.random() < 0.20,
            "n_lines": rng.randint(0, 4),
            "marks": rng.random() < 0.80,
            "last_tag": rng.random() < 0.90,
            "dated": rng.random() < 0.50}


def synth_card(bars: list, style: dict, rng: random.Random, cid: str) -> tuple:
    """البطاقةُ الآليّة **من النصّ المرسوم** ⟵ `(card, render_kwargs)` — وما لا نصَّ له (لا تسمية
    أعلى/أدنى · لا وسمَ آخر سعر) يُكمَل لاحقًا من البكسل بـ`add_pixel_fields` (احتياطُ البرومبت)."""
    from chart_render import fmt_price                               # noqa: PLC0415
    hi_i = max(range(len(bars)), key=lambda i: bars[i]["h"])
    lo_i = min(range(len(bars)), key=lambda i: bars[i]["l"])
    hi_t, lo_t = fmt_price(bars[hi_i]["h"]), fmt_price(bars[lo_i]["l"])
    last_t = fmt_price(bars[-1]["c"])
    marks = [(hi_i, bars[hi_i]["h"], hi_t), (lo_i, bars[lo_i]["l"], lo_t)] if style["marks"] else []
    lo_all, hi_all = bars[lo_i]["l"], bars[hi_i]["h"]
    hlines = []
    for _ in range(style["n_lines"]):
        p = rng.uniform(lo_all, hi_all)
        hlines.append((p, rng.choice(["support", "entry", "resistance", "target", "orange"]),
                       fmt_price(p)))
    if style["last_tag"]:
        hlines.append((bars[-1]["c"], (38, 166, 154), last_t))
    card = {"v": CF.CARD_VERSION, "id": cid, "timeframe": "1D", "tz": "unknown",
            "bars_visible": max(5, int(round(len(bars) * rng.uniform(0.9, 1.1)))),
            "src": "synthetic"}
    if style["marks"]:
        card["extremes"] = {"high": hi_t, "low": lo_t}
    if style["last_tag"]:
        card["last"] = last_t
    if style["dated"]:
        card["window"] = {"from": bars[0]["d"], "to": bars[-1]["d"], "src": "axis"}
    kw = {"theme": style["theme"], "log_scale": style["log"], "marks": marks, "hlines": hlines}
    return card, kw


def add_pixel_fields(card: dict, img, meta: dict) -> dict:
    """يُكمل البطاقةَ من البكسل **لما غاب نصُّه وحدَه**: أعلى/أدنى الشاشة وآخرُ سعر بتسامحٍ مصرَّح.
    المعايرةُ من تسميات المحور المرسومة (كما يقرؤها إنسان)."""
    import chart_pixels as CP                                        # noqa: PLC0415
    pairs = [(y, v[0]) for y, t in meta["axis"] for v in [CF.parse_num(t)] if v]
    ps = CP.pixel_summary(CP.load_rgb(img), meta["box"], pairs,
                          log_scale=True if meta.get("log") else None)
    if not ps:
        return card

    def spec(v):
        return {"v": f"{v[0]:.4f}", "src": "pixel", "tol": f"{max(v[1], 1e-4):.4f}"}
    if "extremes" not in card:
        card["extremes"] = {"high": spec(ps["high"]), "low": spec(ps["low"])}
    if "last" not in card:
        card["last"] = spec(ps["last"])
    return card


def pixel_errors(img, bars: list, meta: dict) -> dict:
    """قراءةُ البكسل على الصورة المصنوعة ⟵ متوسّطُ الخطأ النسبيّ (أعلى/أدنى/إغلاق) وارتباطُ الإغلاقات.
    المعايرةُ من تسميات المحور المرسومة (`meta['axis']`) — كما يقرؤها إنسان."""
    import chart_pixels as CP                                        # noqa: PLC0415
    rgb = CP.load_rgb(img)
    x0, y0, x1, y1 = [int(v) for v in meta["box"]]
    up, dn = CP.candle_masks(rgb, box=(x0, y0, x1, y1))
    cands = [c for c in CP.find_candles(up, dn, x_off=x0, y_off=y0)]
    pairs = []
    for y, t in meta["axis"]:
        v = CF.parse_num(t)
        if v:
            pairs.append((y, v[0]))
    f, _is_log, _err = CP.calibrate(pairs, log_scale=True if meta.get("log") else None)
    if f is None or not cands:
        return {"n": len(cands), "ok": False}
    got = CP.candles_to_ohlc(cands, f)
    n = min(len(got), len(bars))
    if n < 3:
        return {"n": len(cands), "ok": False}
    import numpy as np                                              # noqa: PLC0415
    ix = np.linspace(0, len(got) - 1, n).round().astype(int)
    jx = np.linspace(0, len(bars) - 1, n).round().astype(int)

    def mae(k):
        return float(np.mean([abs(got[a][k] - bars[b][k]) / max(abs(bars[b][k]), 1e-9)
                              for a, b in zip(ix, jx)]))
    return {"n": len(cands), "ok": True, "bars": len(bars), "mae_h": mae("h"), "mae_l": mae("l"),
            "mae_c": mae("c"), "corr_c": CP.series_corr([g["c"] for g in got], [b["c"] for b in bars])}


def run_synth(tmpdir: str, get=None) -> int:
    end = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    days = CF.trading_days_back(end, CF.UNDATED_YEARS)
    log(f"🧪 المصنوعة · بذرة {SEED} · {N_SYNTH} نافذة · لوحةٌ {days[0]} ⟶ {days[-1]} ({len(days)} يومًا)")
    panel = CF.load_panel(days, tmpdir, get=get)
    if not panel:
        log("⛔ لا لوحة")
        return 3
    arr = CF.panel_arrays(panel)
    pdays, syms, H, L, C = arr
    CF.load_all_splits(pdays[0], get=get)
    rng = random.Random(SEED)
    samples = sample_windows(pdays, syms, H, L, C, rng, N_SYNTH)
    log(f"   نوافذُ مسحوبة: {len(samples)}")
    from chart_render import render_candles                          # noqa: PLC0415
    rows = []
    for k, (sym, e, W) in enumerate(samples):
        j = syms.index(sym)
        splits = CF.ticker_splits(sym, get=get, need_since=pdays[0])
        bars = display_bars(pdays, H, L, C, j, e, W, splits)
        style = synth_style(rng)
        card, kw = synth_card(bars, style, rng, f"synth-{k:03d}")
        img, meta = render_candles(bars, **kw)
        card = add_pixel_fields(card, img, meta)
        pe = pixel_errors(img, bars, meta)
        if CF.validate_card(card):
            res = {"label": "بطاقةٌ غيرُ صالحة", "top": []}
        else:
            res = CF.run_card(card, tmpdir, get=get, panel_arr=arr, series=False)
        hit1 = bool(res["top"]) and res["top"][0] == sym
        hit3 = sym in (res["top"] or [])[:3]
        rows.append({"k": k, "sym": sym, "end": pdays[e], "W": W, "style": style, "label": res["label"],
                     "top": list(res["top"][:3]), "hit1": hit1, "hit3": hit3, "px": pe,
                     "split": split_case(bars, splits)})
        log(f"SYNTH_ROW {k:03d} {sym} {pdays[e]} W={W} {style['theme']} log={int(style['log'])} "
            f"marks={int(style['marks'])} last={int(style['last_tag'])} dated={int(style['dated'])} "
            f"⟵ {res['label']} top={res['top'][:3]} hit1={int(hit1)} hit3={int(hit3)} "
            f"px_mae_h={pe.get('mae_h', float('nan')):.4f} corr={pe.get('corr_c', float('nan')):.4f}")
    return report_synth(rows)


def recap(rows: list, tag: str) -> None:
    """صفوفُ النتيجة **مُعادةً مختصرةً في آخر السجلّ** — واجهةُ السجلّ تُرجع آخرَ 5000 سطرٍ وحدَها
    (مقيسٌ على التشغيلة 36057581617: ‏14 صفًّا من 150) · طباعةٌ لا تمسّ الحكم."""
    for r in rows:
        st = r.get("style") or {}
        bits = " ".join(f"{k}={int(bool(st[k]))}" for k in ("marks", "last_tag", "dated", "log") if k in st)
        who = r.get("id") or f"{int(r.get('k', -1)):03d}"
        sp = f" split={r['split']}" if r.get("split") else ""
        log(f"{tag} {who} truth={r['sym']} {r.get('end') or r.get('class') or ''} {bits}{sp} "
            f"⟵ {r['label']} top={r.get('top', [])[:3]} hit1={int(r['hit1'])} hit3={int(r['hit3'])}".replace("  ", " "))


def report_synth(rows: list) -> int:
    n = len(rows)
    h1 = sum(r["hit1"] for r in rows)
    h3 = sum(r["hit3"] for r in rows)
    conf = [r for r in rows if r["label"] == "واثق"]
    conf_ok = sum(r["hit1"] for r in conf)
    log(f"\n📊 المصنوعة: الأوّلُ الصحيح {h1}/{n} = {h1 / max(n, 1):.1%} · ضمن أوّل 3 {h3}/{n} · "
        f"«واثق» {len(conf)} منها صحيحٌ {conf_ok} (Wilson الأدنى {wilson_low(conf_ok, len(conf)):.3f})")
    for key in ("marks", "last_tag", "dated", "log"):
        for val in (True, False):
            sub = [r for r in rows if r["style"][key] == val]
            if sub:
                log(f"   {key}={int(val)}: الأوّلُ {sum(r['hit1'] for r in sub)}/{len(sub)}")
    px = [r["px"] for r in rows if r["px"].get("ok")]
    if px:
        import statistics as st                                     # noqa: PLC0415
        log(f"   🖼️ البكسل: {len(px)} صورة · وسيطُ خطأ الأعلى {st.median(p['mae_h'] for p in px):.4f} · "
            f"الأدنى {st.median(p['mae_l'] for p in px):.4f} · الإغلاق {st.median(p['mae_c'] for p in px):.4f} · "
            f"وسيطُ الارتباط {st.median(p['corr_c'] for p in px if p['corr_c'] == p['corr_c']):.4f}")
    sp_in = [r for r in rows if r.get("split") in ("inside", "both_before")]
    sp_bb = [r for r in rows if r.get("split") == "both_before"]
    log(f"   ✂️ §⑧-6: نوافذُ فيها تقسيم {len(sp_in)} (الأوّلُ الصحيح {sum(r['hit1'] for r in sp_in)}) · "
        f"منها الطرفان كلاهما قبله {len(sp_bb)} (الأوّلُ الصحيح {sum(r['hit1'] for r in sp_bb)} · "
        f"بلا تاريخ {sum(1 for r in sp_bb if not r['style'].get('dated'))})")
    labels = {}
    for r in rows:
        labels[r["label"]] = labels.get(r["label"], 0) + 1
    recap(rows, "SYNTH_RECAP")
    log(f"CHART_EVAL_SYNTH n={n} top1={h1} top3={h3} conf={len(conf)} conf_ok={conf_ok} "
        f"labels={json.dumps(labels, ensure_ascii=False)}")
    return 0


# ══ الحقيقيّة ══════════════════════════════════════════════════════════════════
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def verify_manifest(folder: str = REAL_DIR) -> tuple:
    """البصمةُ المجمَّدة قبل البحث ⟵ `(سليمة؟، الملفّات، المخالفات)`. غيابُ البيان = مخالفة."""
    man = os.path.join(folder, "MANIFEST.sha256")
    if not os.path.exists(man):
        return False, [], ["MANIFEST.sha256 غائب"]
    files, bad = [], []
    for ln in open(man, encoding="utf-8"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        digest, name = ln.split(None, 1)
        p = os.path.join(folder, name.strip())
        files.append(p)
        if not os.path.exists(p):
            bad.append(f"غائب: {name}")
        elif sha256_file(p) != digest:
            bad.append(f"تغيّر بعد التجميد: {name}")
    on_disk = {os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".json")}
    extra = sorted(on_disk - set(files))
    bad += [f"غيرُ مجمَّد: {os.path.basename(x)}" for x in extra]
    return not bad, files, bad


def load_key(folder: str = REAL_DIR) -> dict:
    out = {}
    p = os.path.join(folder, "KEY.tsv")
    for ln in open(p, encoding="utf-8"):
        if not ln.strip() or ln.startswith("#"):
            continue
        cid, sym, cls = (ln.rstrip("\n").split("\t") + ["", ""])[:3]
        out[cid.strip()] = {"sym": sym.strip().upper(), "class": cls.strip()}
    return out


def judge_real(rows: list) -> tuple:
    """`K1`/`K2`/`K3` والفرع — نصُّ العقد §⑤ حرفيًّا. يُرجع `(الفرع، التفاصيل)`."""
    conf = [r for r in rows if r["label"] == "واثق"]
    k1_n, k1_ok = len(conf), sum(1 for r in conf if r["hit1"])
    k1 = None if k1_n < K1_MIN_N else (k1_ok / k1_n >= K1_BAR)
    daily = [r for r in rows if r["class"] == "daily_axis"]
    k2_n, k2_ok = len(daily), sum(1 for r in daily if r["hit3"])
    k2 = None if k2_n < K2_MIN_N else (k2_ok / k2_n >= K2_BAR)
    k3 = all(r["judged"] for r in rows) and bool(rows)
    if k1 is False or not k3:
        branch = "غير جاهزة"
    elif k1 is None:
        branch = "لا حكم"
    elif k2 is True:
        branch = "جاهزة"
    elif k2 is False:
        branch = "جاهزة للواثق وحدَه"
    else:
        branch = "جاهزة للواثق وحدَه (K2 لا حكم)"
    return branch, {"k1": (k1, k1_ok, k1_n, wilson_low(k1_ok, k1_n)), "k2": (k2, k2_ok, k2_n),
                    "k3": k3}


def is_undated(card: dict) -> bool:
    """بطاقةٌ بلا مرساةٍ ولا نافذةٍ مؤرَّخة ولا تحقّقٍ متقاطع ⟵ مسارُ «بلا تاريخ» على لوحة السوق."""
    return not ((card.get("anchor") or {}).get("date") or (card.get("window") or {}).get("to")
                or card.get("cross_with"))


def undated_panel(card: dict, tmpdir: str, shared: dict, get=None):
    """لوحةُ «بلا تاريخ» **تُحمَّل مرّةً وتُعاد لكلّ بطاقةٍ بلا تاريخ** — البياناتُ نفسُها التي يُحمّلها
    المسارُ وحدَه (آخرُ `UNDATED_YEARS` سنوات حتى أمس) فالحكمُ بت-بت، والتحميلُ واحدٌ لا 37 (‏≈2-3 دقائق
    لكلٍّ على الرنر ⇒ خطرُ مهلة 180). المؤرَّخةُ والمرساةُ `None` = مسارُها كما هو."""
    if not is_undated(card):
        return None
    if "arr" not in shared:
        end = (dt.date.today() - dt.timedelta(days=1)).isoformat()
        panel = CF.load_panel(CF.trading_days_back(end, CF.UNDATED_YEARS), tmpdir, get=get)
        shared["arr"] = CF.panel_arrays(panel) if panel else None
    return shared["arr"]


def run_real(tmpdir: str, get=None, folder: str = REAL_DIR) -> int:
    ok, files, bad = verify_manifest(folder)
    if not ok:
        for b in bad:
            log(f"⛔ البصمة: {b}")
        log("CHART_EVAL_JUDGE branch=بصمةٌ مكسورة exit=4")
        return 4
    key = load_key(folder)
    rows, results, shared = [], {}, {}
    for p in files:
        card = json.load(open(p, encoding="utf-8"))
        cid = card.get("id")
        truth = key.get(cid)
        if truth is None:
            log(f"⛔ {cid}: بلا مفتاح")
            continue
        res = CF.run_card(card, tmpdir, get=get, results=results,
                          panel_arr=undated_panel(card, tmpdir, shared, get=get))
        rows.append({"id": cid, "sym": truth["sym"], "class": truth["class"], "label": res["label"],
                     "top": res["top"], "hit1": bool(res["top"]) and res["top"][0] == truth["sym"],
                     "hit3": truth["sym"] in res["top"][:3], "judged": res["rc"] == 0})
        log(f"REAL_ROW {cid} truth={truth['sym']} class={truth['class']} ⟵ {res['label']} "
            f"top={res['top'][:3]} hit1={int(rows[-1]['hit1'])} hit3={int(rows[-1]['hit3'])}")
    recap(rows, "REAL_RECAP")
    branch, det = judge_real(rows)
    k1, k1_ok, k1_n, k1_w = det["k1"]
    k2, k2_ok, k2_n = det["k2"]
    log(f"\n⚖️ K1 «واثق» صحيح {k1_ok}/{k1_n} (Wilson الأدنى {k1_w:.3f}) ⟵ {k1} · "
        f"K2 ضمن أوّل 3 {k2_ok}/{k2_n} ⟵ {k2} · K3 {det['k3']}")
    log(f"CHART_EVAL_JUDGE branch={branch} k1={k1_ok}/{k1_n} k2={k2_ok}/{k2_n} k3={int(det['k3'])} exit=0")
    return 0


def main() -> int:
    mode = (os.environ.get("CHART_EVAL") or "").strip()
    if not CF._key():
        log("⛔ POLYGON_API_KEY غائب")
        return 3
    with tempfile.TemporaryDirectory() as tmp:
        if mode == "synth":
            return run_synth(tmp)
        if mode in REAL_DIRS:
            return run_real(tmp, folder=REAL_DIRS[mode])
    log(f"⛔ CHART_EVAL غيرُ معروف: {mode!r} (synth أو real أو real2)")
    return 2


if __name__ == "__main__":
    sys.exit(main())
