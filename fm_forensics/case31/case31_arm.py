#!/usr/bin/env python3
"""⚖️ `T-CASE31` — تشغيلُ الذراعين (العقد §②-§⑤): المرصودُ · شرائحُ الخلط · التجميعُ والتقرير — قراءةٌ فقط.

  observe  A|B --dir FEAT          — البحثُ المرصود وجداولُه ⟵ `obs_<arm>.json.gz`
  shuffle  A|B <k> <n> --dir FEAT  — خلطاتُ الشريحة k من n (من 1,000) ⟵ `shuf_<arm>_<k>.json`
  assemble A|B --dir ALL           — يجمع المرصودَ والخلطات ⟵ `out/ARM_<arm>.md` + `out/arm<arm>.json` (مرّةً واحدة: وجودُ النتيجة ⟵ خروج 7)
"""
import glob
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (ROOT, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import numpy as np                                                # noqa: E402
import case31 as C                                                # noqa: E402
import case31_catalog as CAT                                      # noqa: E402
import case31_stats as ST                                         # noqa: E402

N_SHUFFLE = 1000
MIN_K = {"A": 8, "B": 30}
TYPES = (("بخبر", lambda e: (e.get("cat") or {}).get("status") == "بخبر"), ("بلا خبر", lambda e: (e.get("cat") or {}).get("status") == "بلا خبر"),
         ("يومٌ واحد", lambda e: bool(e.get("one_day"))), ("عدّة أيام", lambda e: not e.get("one_day")),
         ("شمعةٌ واحدة", lambda e: bool(e.get("one_candle"))), ("موجات", lambda e: not e.get("one_candle")),
         ("بعد تقسيمٍ عكسيّ", lambda e: bool(e.get("rs_recent"))), ("بلا تقسيمٍ حديث", lambda e: not e.get("rs_recent")))
COST = 0.018                    # كلفةُ الصفقة ذهابًا وإيابًا (`T-BASKET`)
OUT_DIR = os.path.join(ROOT, "case31_arm")


def log(m=""):
    print(m, flush=True)


def load_feat(d_in):
    rows = []
    for p in sorted(glob.glob(os.path.join(d_in, "**", "feat_*.json.gz"), recursive=True)):
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            js = json.load(fh)
        if js.get("catalog_sha") != CAT.sha():
            raise SystemExit(C.RC_CONTRACT)
        for r in js["rows"]:
            if r.get("ok") and isinstance(r.get("f"), dict):
                r["f"] = ST.FV(r["f"])
            rows.append(r)
    return rows


def family_errors(d_in):
    """مجموعُ أعطال الأُسَر غير الشمعيّة في الشرائح (سماتُها كُتبت «غير مقيس» ولم يتوقّف التشغيل) ⟵ {«أسرة:نوع»: عدد}."""
    tot = {}
    for p in sorted(glob.glob(os.path.join(d_in, "**", "feat_*.json.gz"), recursive=True)):
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            for k, v in (json.load(fh).get("family_errors") or {}).items():
                tot[k] = tot.get(k, 0) + int(v)
    return tot


B_LAST_DAY = "2025-12-31"        # الذراع ب: لا صفَّ بيوم قرارٍ بعد 2025 قبل ملفّ التثبيت (العقد §⑧)


def b_blind_ok(d_in):
    """الذراع ب عمياءُ عن 2026: كلُّ شريحةٍ موسومةٌ `arm=B` ولا صفَّ فيها بيوم قرارٍ بعد `B_LAST_DAY` · ومجلّدٌ بلا شرائح ⟵ لا."""
    files = sorted(glob.glob(os.path.join(d_in, "**", "feat_*.json.gz"), recursive=True))
    if not files:
        return False
    for p in files:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            js = json.load(fh)
        if js.get("arm") != "B" or any(str(r.get("D") or "9") > B_LAST_DAY for r in js.get("rows") or []):
            return False
    return True


def build_rows(feat, window, events=None):
    """(نقيّة) صفوفُ الشرائح ⟵ (صفوفُ الذراع [{sym, day, y, f, …}]، إحصاءُ ما استُبعد) لنافذة `window` («الشهر» أو «قبل الشهر»)."""
    ev = {(r["sym"], r["D"]): r for r in feat if r.get("ok") and r.get("ev") and r["ev"][0] == "x100" and r["ev"][1] == window}
    days = sorted({d for _s, d in ev})
    pool_days = {r["D"] for r in feat if r.get("ok") and r.get("in_pool")}
    use_days = [d for d in days if d in pool_days]
    stat = {"days": len(days), "days_no_pool": len(days) - len(use_days), "pos": 0, "pos_untracked": 0, "ctrl": 0, "grey": 0, "unlabeled": 0,
            "bad": sum(1 for r in feat if not r.get("ok")), "open_window": 0}
    out = []
    for r in feat:
        if not r.get("ok") or r["D"] not in use_days:
            continue
        key = (r["sym"], r["D"])
        if key in ev:
            stat["pos"] += 1
            stat["pos_untracked"] += int(not r.get("in_pool"))
            out.append({"sym": r["sym"], "day": r["D"], "y": 1, "f": r["f"], "ret": r.get("ret"), "src": r})
            continue
        if not r.get("in_pool") or r.get("ev"):
            continue                                                # صفُّ ذراع ‏+50% أو حدثُ نافذةٍ أخرى ليس ضابطةً لهذا اليوم
        if r.get("x20") is None:
            stat["unlabeled"] += 1
            continue
        if r["x20"]:
            stat["grey"] += 1
            continue
        stat["ctrl"] += 1
        stat["open_window"] += int((r.get("after") or 0) < 20)
        out.append({"sym": r["sym"], "day": r["D"], "y": 0, "f": r["f"], "ret": r.get("ret")})
    return out, stat


def _subset_for_type(rows, pred):
    """صفوفُ نوعٍ واحد: موجبو النوع وضابطةُ أيّامهم (الموجبون الآخرون يخرجون)."""
    days = {r["day"] for r in rows if r["y"] == 1 and pred((r.get("src") or {}).get("event") or {})}
    return [r for r in rows if r["day"] in days and (r["y"] == 0 or pred((r.get("src") or {}).get("event") or {}))]


def attach_events(rows, plan_events):
    ev = {(e["sym"], e["D"]): e for e in plan_events if e["cls"] == "x100"}
    for r in rows:
        if r["y"] == 1:
            r["src"]["event"] = ev.get((r["sym"], r["day"]), {})
    return rows


def lead_runs(P, rows, cond_ix):
    """المهلة: لكلّ شرطٍ عددُ الجلسات المتّصلة حتى يوم القرار التي كان قائمًا فيها عند كلّ منفجر (سقف 20) ⟵ {شرط: [أطوال]}."""
    out = {}
    for c in cond_ix:
        text, j, thr = P["conds"][c]
        nm, kind = P["names"][j]
        runs = []
        for r in rows:
            if r["y"] != 1:
                continue
            seq = [r["f"]] + list((r.get("src") or {}).get("lead") or [])
            k = 0
            for f in seq:
                v = f.get(nm)
                if v is None:
                    break
                ok = (v == (1 if text.endswith("=1") else 0)) if kind == "bool" else ((v < thr) if "<q" in text else (v > thr))
                if not ok:
                    break
                k += 1
            runs.append(k)
        out[text] = runs
    return out


def mode_observe(arm, d_in, window="الشهر"):
    feat = load_feat(d_in)
    plan = None
    for base, _d, files in os.walk(d_in):
        if "plan_events.json" in files:
            plan = json.load(open(os.path.join(base, "plan_events.json"), encoding="utf-8"))
    rows, stat = build_rows(feat, window)
    stat["family_errors"] = family_errors(d_in)
    if plan:
        attach_events(rows, plan)
    if stat["pos"] < MIN_K[arm]:
        log(f"⛔ المنفجرون {stat['pos']} دون {MIN_K[arm]} — لا بحث · خروج {C.RC_DATA}")
        return C.RC_DATA
    P = ST.prepare(rows, arm, MIN_K[arm])
    y = P["y"]
    obs = ST.search(P, y, keep=True)
    table = ST.feature_table(P, y)
    x50 = [r for r in feat if r.get("ok") and r.get("ev") and r["ev"][0] == "x50" and r["ev"][1] == window]
    top_c = obs["_top"][:20]
    res = {"arm": arm, "window": window, "stat": stat, "n": P["n"], "p": P["p"], "n_elig": int(P["elig"].sum()), "n_conds": len(P["conds"]),
           "tried": {"features": P["p"], "eligible_features": int(P["elig"].sum()), "conditions": len(P["conds"]),
                     "valid_singles": obs["n_valid_singles"], "combos": obs["n_combos_tried"], "models": 2,
                     "folds": len(P["folds"])},
           "peaks": {k: obs.get(k) for k in ST.SHUFFLE_KEYS},
           "top_singles": [{"cond": ST.cond_text(P, c), "z": float(obs["_z"][c]), "k": int(obs["_k"][c]), "n": int(P["n_c"][c]),
                            "matched": ST.cond_matched(P, y, [c])} for c in top_c],
           "top_combos": [{"conds": [ST.cond_text(P, c) for c in cc], "z": z, "k": k, "n": n, "matched": ST.cond_matched(P, y, list(cc)),
                           "ix": list(cc)} for z, k, n, cc in obs["_combos"][:30]],
           "exclusions": [{"cond": ST.cond_text(P, c), "removes": sn, "pos_share": sp} for sn, c, sp in obs["_excl"][:30]],
           "table": table, "neighbours": ST.neighbours(P, y, rows),
           "lead": lead_runs(P, rows, top_c),
           "x50": {"n": len(x50)},
           "thresholds": {ST.cond_text(P, c): P["conds"][c][2] for c in range(len(P["conds"]))},
           "positives": [{"sym": r["sym"], "day": r["day"], "ret": r.get("ret"), "bot_reject": (r.get("src") or {}).get("bot_reject"),
                          "row": (r.get("src") or {}).get("row"), "in_pool": (r.get("src") or {}).get("in_pool"),
                          "dd_before": (r.get("src") or {}).get("dd_before"), "event": (r.get("src") or {}).get("event")} for r in rows if r["y"] == 1],
           "ctrl_ret": [r.get("ret") for r in rows if r["y"] == 0 and r.get("ret") is not None],
           "types": {}}
    for name, pred in TYPES:
        sub = _subset_for_type(rows, pred)
        npos = sum(r["y"] for r in sub)
        if npos < MIN_K[arm]:
            res["types"][name] = {"n": npos, "note": "دون الحدّ — وصفٌ بلا بحث"}
            continue
        Pt = ST.prepare(sub, arm, MIN_K[arm])
        ot = ST.search(Pt, Pt["y"], with_models=False, keep=True)
        res["types"][name] = {"n": npos, "best_single": ot["best_single"],
                              "top": [{"cond": ST.cond_text(Pt, c), "z": float(ot["_z"][c]), "k": int(ot["_k"][c])} for c in ot["_top"][:10]]}
    os.makedirs(OUT_DIR, exist_ok=True)
    with gzip.open(os.path.join(OUT_DIR, f"obs_{arm}.json.gz"), "wt", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False)
    log(f"⚖️ الذراع {arm}: صفوف {P['n']:,} · منفجرون {stat['pos']} · سماتٌ مؤهَّلة {int(P['elig'].sum())} من {P['p']} · شروط {len(P['conds']):,} · "
        f"توليفات {obs['n_combos_tried']:,} · القِمم {json.dumps(res['peaks'], ensure_ascii=False)}")
    return C.RC_OK


def mode_shuffle(arm, k, n, d_in, window="الشهر"):
    feat = load_feat(d_in)
    rows, stat = build_rows(feat, window)
    plan = None
    for base, _d, files in os.walk(d_in):
        if "plan_events.json" in files:
            plan = json.load(open(os.path.join(base, "plan_events.json"), encoding="utf-8"))
    if plan:
        attach_events(rows, plan)
    if stat["pos"] < MIN_K[arm]:
        return C.RC_DATA
    P = ST.prepare(rows, arm, MIN_K[arm])
    out = []
    for i in range(k, N_SHUFFLE, n):
        out += ST.shuffle_block(P, i, 1)
        if len(out) % 5 == 0:
            log(f"   … خلطة {len(out)} في الشريحة {k}")
    types = {}
    for name, pred in TYPES:
        sub = _subset_for_type(rows, pred)
        if sum(r["y"] for r in sub) < MIN_K[arm]:
            continue
        Pt = ST.prepare(sub, arm, MIN_K[arm])
        types[name] = [ST.search(Pt, ST.shuffle_labels(Pt, np.random.default_rng(ST._seed("type", name, i))), with_models=False)["best_single"]
                       for i in range(k, N_SHUFFLE, n)]
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, f"shuf_{arm}_{k}.json"), "w", encoding="utf-8") as fh:
        json.dump({"arm": arm, "k": k, "n": n, "shuffles": out, "types": types}, fh)
    log(f"🔀 الذراع {arm} الشريحة {k}/{n}: {len(out)} خلطة")
    return C.RC_OK


def _pct(x, d=1):
    return "—" if x is None or x != x else f"{x * 100:.{d}f}%"


def _num(x, d=3):
    return "—" if x is None or x != x else f"{x:.{d}f}"


def assemble(obs, shuf, type_shuf):
    """(نقيّة) المرصودُ + الخلطات ⟵ (نصُّ التقرير، ملخّصٌ JSON)."""
    arm = obs["arm"]
    L = [f"# ⚖️ `T-CASE31` — الذراع {arm}: المقارنةُ واختبارُ الخلط (مولَّدٌ آليًّا · لا يُعدَّل باليد)", ""]
    st = obs["stat"]
    L += [f"- المجتمع ({obs['window']}): صفوف {obs['n']:,} · **منفجرون {st['pos']}** (منهم خارج «تحت المتابعة» {st['pos_untracked']}) · ضابطة {st['ctrl']:,} · "
          f"رماديٌّ مستبعَد {st['grey']} · بلا وسم {st['unlabeled']} · أيّامُ قرار {st['days']} (بلا لقطة {st['days_no_pool']}) · "
          f"ضابطةٌ لم تكتمل نافذتُها {st['open_window']:,}",
          f"- **المجرَّب:** سمات {obs['tried']['features']:,} (المؤهَّلة بالتغطية {obs['tried']['eligible_features']:,}) · شروط {obs['tried']['conditions']:,} "
          f"(الصالحة منفردةً {obs['tried']['valid_singles']:,}) · توليفات {obs['tried']['combos']:,} · نماذج {obs['tried']['models']} "
          f"× {obs['tried']['folds']} طيّة · خلطات {len(shuf):,}", ""]
    if st.get("family_errors"):
        L[-1:] = ["- ⚠️ **أعطالُ أُسَرٍ غيرِ شمعيّة (سماتُها «غير مقيس» في صفوفها ولم يتوقّف التشغيل):** "
                  + " · ".join(f"{k} × {v:,}" for k, v in sorted(st["family_errors"].items())), ""]
    verdict = {}
    L += ["## ① نتيجةُ الخلط (القِمم: المرصودُ مقابل المئين 95 لأقصى الخلطات)", "", "| القمّة | المرصود | مئين 95 للخلطات | يفوق من الخلطات | الحكم |", "|---|---|---|---|---|"]
    for key, name in (("best_single", "أقوى شرطٍ منفرد (z)"), ("best_combo", "أقوى توليفة (z)"), ("best_print", "أقوى بصمة (z)"),
                      ("best_excl", "أقوى سمة استبعاد (اختصار)"), ("tree_auc", "شجرةُ القرار (AUC داخل اليوم)"),
                      ("logit_auc", "اللوجستيّ (AUC داخل اليوم)"), ("tree_top", "الشجرة: منفجرون في أعلى 5%"), ("logit_top", "اللوجستيّ: منفجرون في أعلى 5%")):
        thr, frac, ok = ST.beats(obs["peaks"].get(key), shuf, key)
        verdict[key] = {"obs": obs["peaks"].get(key), "p95": thr, "beats_frac": frac, "pass": ok}
        L.append(f"| {name} | {_num(obs['peaks'].get(key))} | {_num(thr)} | {_pct(frac)} | {'✅ يعبر' if ok else '❌ في حدود الصدفة'} |")
    L.append("")
    tag = lambda key: "" if verdict[key]["pass"] else " — **في حدود الصدفة**"   # noqa: E731
    L += [f"## ② أهمُّ الفروق (السمات مرتّبةً بالفرق المعياريّ · فاصل 95% عنقوديّ بيوم القرار){tag('best_single')}", "",
          "| السمة | عند المنفجرين | عند الضابطة | الفرق (رتبة) | الفاصل | مقابل ضابط الزخم | التغطية |", "|---|---|---|---|---|---|---|"]
    for r in [t for t in obs["table"] if t["elig"]][:40]:
        fa = _pct(r["pos"]) if r["kind"] == "bool" else _num(r["pos"], 4)
        fb = _pct(r["neg"]) if r["kind"] == "bool" else _num(r["neg"], 4)
        L.append(f"| `{r['name']}` | {fa} | {fb} | {r['diff']:+.3f} | [{r['lo']:+.3f}، {r['hi']:+.3f}] | {_num(r['matched'])} | {_pct(r['cov'], 0)} |")
    L += ["", f"## ③ أقوى الشروط المنفردة{tag('best_single')}", "", "| الشرط | z | المنفجرون الحاملون | كلُّ الحاملين | مقابل ضابط الزخم | وسيطُ المهلة (جلسات) |", "|---|---|---|---|---|---|"]
    for t in obs["top_singles"]:
        runs = obs["lead"].get(t["cond"]) or []
        med = float(np.median([x for x in runs if x > 0])) if any(x > 0 for x in runs) else None
        L.append(f"| `{t['cond']}` | {t['z']:.2f} | {t['k']} | {t['n']:,} | {_num(t['matched'])} | {_num(med, 0)} |")
    L += ["", f"## ④ أقوى التوليفات حتى 3 شروط{tag('best_combo')}", "", "| التوليفة | z | المنفجرون | الحاملون | نسبةُ الانفجار | مقابل ضابط الزخم |", "|---|---|---|---|---|---|"]
    for t in obs["top_combos"][:15]:
        L.append(f"| {' ∧ '.join('`' + c + '`' for c in t['conds'])} | {t['z']:.2f} | {t['k']} | {t['n']:,} | {_pct(t['k'] / t['n'] if t['n'] else None)} | {_num(t['matched'])} |")
    L += ["", f"## ⑤ سماتُ الاستبعاد (أقلُّ من 5% من المنفجرين و20% فأكثر من الضابطة){tag('best_excl')}", "",
          "| الشرط | يختصر من القائمة | يحمله من المنفجرين |", "|---|---|---|"]
    for t in obs["exclusions"][:20]:
        L.append(f"| `{t['cond']}` | {_pct(t['removes'])} | {_pct(t['pos_share'])} |")
    if not obs["exclusions"]:
        L.append("| لا سمةَ بالتعريف | — | — |")
    L += ["", "## ⑥ لكلّ نوع (الشروطُ المنفردة وحدَها وخلطُها)", "", "| النوع | المنفجرون | أقوى شرط | z | مئين 95 | الحكم |", "|---|---|---|---|---|---|"]
    tv = {}
    for name, t in obs["types"].items():
        if "best_single" not in t:
            L.append(f"| {name} | {t['n']} | — | — | — | {t.get('note', '')} |")
            continue
        xs = np.array([(-np.inf if (x is None or x != x) else x) for x in type_shuf.get(name, [])], dtype=float)
        thr = float(np.percentile(xs, 95)) if len(xs) else None
        ok = bool(thr is not None and t["best_single"] > thr)
        tv[name] = {"obs": t["best_single"], "p95": thr, "pass": ok}
        topc = t["top"][0] if t["top"] else {}
        L.append(f"| {name} | {t['n']} | `{topc.get('cond', '—')}` | {_num(t['best_single'], 2)} | {_num(thr, 2)} | {'✅ يعبر' if ok else '❌ في حدود الصدفة'} |")
    L += ["", "## ⑦ أقرب الجيران (لكلّ منفجرٍ أشبهُ 5 لم تنفجر في يومه وأكبرُ ما فرّقه)", ""]
    for nb in obs["neighbours"]:
        L.append(f"- **{nb['sym']}** ({nb['day']}) ⟵ {' · '.join(nb['nn'])} — " + " · ".join(f"`{a}` {b:+.2f}" for a, b in nb["diff"][:5]))
    # ما فات البوت
    walls, rej = {}, {}
    for p_ in obs["positives"]:
        row = p_.get("row") or {}
        code = ((row.get("wall") or {}).get("label")) or ("—" if row else None)
        if row:
            walls[code] = walls.get(code, 0) + 1
        rej[p_.get("bot_reject") or "غير مقيس"] = rej.get(p_.get("bot_reject") or "غير مقيس", 0) + 1
    L += ["", "## ⑧ «ما فات البوت»", "", "- سببُ رفض الفرز عند يوم القرار (بأرقام الإنتاج): " + " · ".join(f"{k} {v}" for k, v in sorted(rej.items(), key=lambda t: -t[1])),
          "- جدارُ صفّ «تحت المتابعة» للمتابَعين: " + (" · ".join(f"{k} {v}" for k, v in sorted(walls.items(), key=lambda t: -t[1])) or "—"), "",
          "| السهم | يوم القرار | في المتابعة | رفضُ الفرز | الجدار | الناقصُ وهامشُه | الجاهزيّة |", "|---|---|---|---|---|---|---|"]
    for p_ in sorted(obs["positives"], key=lambda t: (t["day"], t["sym"])):
        row = p_.get("row") or {}
        outd = " · ".join(f"{o.get('label')} (هامش {o.get('margin')}%)" for o in row.get("out_detail") or []) or "—"
        L.append(f"| {p_['sym']} | {p_['day']} | {'نعم' if row else 'لا'} | {p_.get('bot_reject') or 'غير مقيس'} | {((row.get('wall') or {}).get('label')) or '—'} | "
                 f"{outd} | {row.get('readiness', '—')} |")
    # الربحُ الوصفيّ
    pr = [p_["ret"] - COST for p_ in obs["positives"] if p_.get("ret") is not None]
    cr = [x - COST for x in obs["ctrl_ret"]]
    L += ["", "## ⑨ الصفقة (وصف): شراءُ افتتاح اليوم التالي للقرار وبيعُ إغلاق الجلسة العشرين · كلفة 1.8%", "",
          f"- المنفجرون: متوسّط {_pct(float(np.mean(pr)) if pr else None)} · وسيط {_pct(float(np.median(pr)) if pr else None)} · خاسرون {_pct(float(np.mean([x < 0 for x in pr])) if pr else None)} (من {len(pr)})",
          f"- الضابطة: متوسّط {_pct(float(np.mean(cr)) if cr else None)} · وسيط {_pct(float(np.median(cr)) if cr else None)} · خاسرون {_pct(float(np.mean([x < 0 for x in cr])) if cr else None)} (من {len(cr):,})", ""]
    return "\n".join(L) + "\n", {"arm": arm, "verdict": verdict, "types": tv, "stat": st, "tried": obs["tried"], "n_shuffles": len(shuf)}


def mode_assemble(arm, d_in):
    res_md = os.path.join(C.OUT, f"ARM_{arm}.md")
    if os.path.exists(res_md):
        log(f"⛔ نتيجةُ الذراع {arm} صادرة — لا محاولةَ ثانية · خروج {C.RC_ONCE}")
        return C.RC_ONCE
    obs, shuf, tsh = None, [], {}
    for p in glob.glob(os.path.join(d_in, "**", f"obs_{arm}.json.gz"), recursive=True):
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            obs = json.load(fh)
    for p in sorted(glob.glob(os.path.join(d_in, "**", f"shuf_{arm}_*.json"), recursive=True)):
        js = json.load(open(p, encoding="utf-8"))
        shuf += js["shuffles"]
        for k, v in (js.get("types") or {}).items():
            tsh.setdefault(k, []).extend(v)
    if not obs or len(shuf) < N_SHUFFLE:
        log(f"⛔ المرصودُ غائب أو الخلطات {len(shuf)} دون {N_SHUFFLE} — خروج {C.RC_DATA}")
        return C.RC_DATA
    md, summ = assemble(obs, shuf, tsh)
    os.makedirs(C.OUT, exist_ok=True)
    with open(res_md, "w", encoding="utf-8") as fh:
        fh.write(md)
    keep = {k: obs[k] for k in ("arm", "window", "stat", "tried", "peaks", "top_singles", "top_combos", "exclusions", "types", "thresholds", "positives")}
    keep["table"] = obs["table"]
    keep["summary"] = summ
    with gzip.open(os.path.join(C.OUT, f"arm{arm}.json.gz"), "wt", encoding="utf-8") as fh:
        json.dump(keep, fh, ensure_ascii=False)
    log(md[:6000])
    return C.RC_OK


def main(argv):
    if not C.contract_ok():
        log(f"⛔ العقدُ أو الفهرسُ لا يطابق بصمتَه — خروج {C.RC_CONTRACT}")
        return C.RC_CONTRACT
    mode, arm = (argv[1] if len(argv) > 1 else ""), (argv[2] if len(argv) > 2 else "")
    d_in = argv[argv.index("--dir") + 1] if "--dir" in argv else "."
    if arm not in ("A", "B"):
        log("الاستعمال: case31_arm.py observe|shuffle|assemble A|B …")
        return 2
    window = "الشهر" if arm == "A" else "B"
    if arm == "B" and mode in ("observe", "shuffle") and not b_blind_ok(d_in):
        log(f"⛔ الذراع ب لا تقرأ صفوفَ 2026 قبل ملفّ التثبيت (مجتمعُها شرائح 2023-2025 وحدَها) · خروج {C.RC_BLIND}")
        return C.RC_BLIND
    if mode == "observe":
        return mode_observe(arm, d_in, window)
    if mode == "shuffle":
        return mode_shuffle(arm, int(argv[3]), int(argv[4]), d_in, window)
    if mode == "assemble":
        return mode_assemble(arm, d_in)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
