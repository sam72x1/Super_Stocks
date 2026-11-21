#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🗂️🔬 `T-CASE31` — المخرجُ النهائيّ بترتيب المالك (العقد §⑦) من ملفّات `out/` الصادرة · مولِّدٌ حتميٌّ بلا شبكة ولا حكمٍ جديد.

جدولُ التحقّق والأنواع ⟵ أهمُّ 10 فروقٍ بلغةٍ بسيطة ⟵ سماتُ الاستبعاد ⟵ البصماتُ ونتيجةُ الخلط والتحقّق ⟵ «ما فات البوت» ⟵ الملفّات ⟵
حدودُ الصدق والتنبّؤات كما هي. ما لم يصدر بعدُ يُكتب «لم يصدر» ولا يُخمَّن.
"""
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
import case31_stats as ST               # noqa: E402
import case31_words as W                # noqa: E402

ARM_NAME = {"A": "الذراع أ (منفجرو الشهر مقابل «تحت المتابعة» في يومهم · كلُّ السمات)", "B": "الذراع ب (2023-2025 · سماتُ الشموع وحدَها)"}


def _load(name):
    p = os.path.join(C.OUT, name)
    if not os.path.exists(p):
        return None
    if name.endswith(".gz"):
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def pct(x, d=1):
    return "—" if x is None or x != x else f"{x * 100:.{d}f}%"


def top_differences(arm, k=10):
    """(نقيّة) أقوى الشروط المنفردة على سماتٍ أساسيّةٍ مختلفة ⟵ [{text, plain, z, k, n, share_pos, share_all, pass}] · «يعبر» = فوق المئين 95 لأقصى الخلطات."""
    ver = ((arm.get("summary") or {}).get("verdict") or {}).get("best_single") or {}
    p95, npos, nall = ver.get("p95"), (arm.get("stat") or {}).get("pos") or 0, (arm.get("stat") or {}).get("pos", 0) + (arm.get("stat") or {}).get("ctrl", 0)
    seen, out = set(), []
    for t in arm.get("top_singles") or []:
        base = ST.base_of(t["cond"].rsplit("=", 1)[0] if t["cond"][-2:] in ("=0", "=1") else t["cond"].split("<q")[0].split(">q")[0])
        if base in seen:
            continue
        seen.add(base)
        out.append({"text": t["cond"], "plain": W.condition(t["cond"]), "z": t["z"], "k": t["k"], "n": t["n"], "matched": t.get("matched"),
                    "share_pos": (t["k"] / npos) if npos else None, "share_all": (t["n"] / nall) if nall else None,
                    "pass": bool(p95 is not None and t["z"] > p95)})
        if len(out) == k:
            break
    return out, p95


def verify_section(V):
    T = V.get("table") or []
    own = [g for g in T if g.get("owner")]
    x_own = sorted({g["sym"] for g in own if g["cls"] == "x100" and not g.get("drop") and g["win"] != "قبل النافذة"})
    month = [g for g in T if g["cls"] == "x100" and not g.get("drop") and g["win"] == "الشهر"]
    pre = [g for g in T if g["cls"] == "x100" and not g.get("drop") and g["win"] == "قبل الشهر"]
    added = sorted({g["sym"] for g in month + pre if not g.get("owner")})
    drops = sorted({g["sym"] for g in own if g.get("drop")})
    absent = [a["sym"] for a in V.get("absent") or []]
    cat = lambda st: sum(1 for g in month if (g.get("cat") or {}).get("status") == st)      # noqa: E731
    L = ["## ① جدولُ التحقّق من القائمة وأنواعُ الانفجار", "",
         f"- الكون {V.get('universe'):,} رمزًا · منفجرو ‏+100% منذ 2026-09-29: **{len(month) + len(pre)} حدثًا** (الشهر {len(month)} · قبله {len(pre)}) · مُكمَّلٌ من الكون {len(added)} رمزًا.",
         f"- قائمةُ المالك (31): مؤكَّد ‏+100% **{len(x_own)}** · مُسقَط {len(drops)} ({' · '.join(drops) or '—'}) · بلا حركةٍ بتعريف العقد {len(absent)} ({' · '.join(absent) or '—'}).",
         f"- أنواعُ منفجري الشهر ({len(month)}): بخبر {cat('بخبر')} · بلا خبر {cat('بلا خبر')} · غير مقيس {cat('غير مقيس')} · يومٌ واحد {sum(1 for g in month if g['one_day'])} · "
         f"شمعةٌ واحدة {sum(1 for g in month if g['one_candle'])} · بعد تقسيمٍ عكسيّ حديث {sum(1 for g in month if g.get('rs_recent'))} · "
         f"أودع طرحًا خلال 10 جلسات {sum(1 for g in month if (g.get('cat') or {}).get('offer_after'))}.",
         "- الجدولُ الكامل صفًّا صفًّا: `fm_forensics/case31/out/VERIFY.md`.", ""]
    return L


def arm_section(a, arm):
    if not arm:
        return [f"### {ARM_NAME[a]}", "", "- لم يصدر.", ""], None
    diffs, p95 = top_differences(arm)
    st, ver = arm.get("stat") or {}, (arm.get("summary") or {}).get("verdict") or {}
    L = [f"### {ARM_NAME[a]}", "",
         f"- المجتمع: منفجرون **{st.get('pos')}** (خارج «تحت المتابعة» {st.get('pos_untracked')}) · ضابطة {st.get('ctrl'):,} · أيّامُ قرار {st.get('days')} (بلا لقطة {st.get('days_no_pool')}) · "
         f"ضابطةٌ لم تكتمل نافذتُها {st.get('open_window'):,} · المجرَّب: سمات {arm['tried']['features']:,} (المؤهَّلة {arm['tried']['eligible_features']:,}) · "
         f"شروط {arm['tried']['conditions']:,} · توليفات {arm['tried']['combos']:,} · خلطات {(arm.get('summary') or {}).get('n_shuffles')}", "",
         "| # | الفرق بلغةٍ بسيطة | يحمله من المنفجرين | يحمله من كلّ الصفوف | z | مقابل ضابط الزخم | حكمُ الخلط |", "|---|---|---|---|---|---|---|"]
    for i, d in enumerate(diffs, 1):
        mt = "—" if d["matched"] is None else f"{d['matched']:+.2f}"
        L.append(f"| {i} | {d['plain']} | {d['k']} ({pct(d['share_pos'])}) | {pct(d['share_all'])} | {d['z']:.2f} | {mt} | "
                 f"{'✅ يعبر' if d['pass'] else '❌ في حدود الصدفة'} |")
    thr = "—" if p95 is None else f"{p95:.2f}"
    L += ["", f"- عتبةُ العبور (المئين 95 لأقصى شرطٍ في الخلطات): z = {thr}", ""]
    return L, ver


def exclusion_section(a, arm):
    if not arm:
        return []
    ver = ((arm.get("summary") or {}).get("verdict") or {}).get("best_excl") or {}
    L = [f"### {ARM_NAME[a]}", "", "| سمةُ الاستبعاد بلغةٍ بسيطة | تختصر من القائمة | يحملها من المنفجرين | حكمُ الخلط |", "|---|---|---|---|"]
    for e in (arm.get("exclusions") or [])[:10]:
        ok = ver.get("p95") is not None and e["removes"] > ver["p95"]
        L.append(f"| {W.condition(e['cond'])} | {pct(e['removes'])} | {pct(e['pos_share'])} | {'✅ يعبر' if ok else '❌ في حدود الصدفة'} |")
    if not arm.get("exclusions"):
        L.append("| لا سمةَ بالتعريف (أقلّ من 5% من المنفجرين و20% فأكثر من الضابطة) | — | — | — |")
    L += ["", f"- عتبةُ العبور: اختصار {pct(ver.get('p95'))} (المرصودُ الأقصى {pct(ver.get('obs'))})", ""]
    return L


def prints_section(a, arm):
    if not arm:
        return []
    ver = (arm.get("summary") or {}).get("verdict") or {}
    names = (("best_single", "أقوى شرطٍ منفرد (z)"), ("best_combo", "أقوى توليفة (z)"), ("best_excl", "أقوى سمة استبعاد"), ("tree_auc", "شجرةُ القرار — AUC خارج العيّنة"),
             ("logit_auc", "اللوجستيّ — AUC خارج العيّنة"), ("tree_top", "الشجرة — منفجرون في أعلى 5%"), ("logit_top", "اللوجستيّ — منفجرون في أعلى 5%"))
    L = [f"### {ARM_NAME[a]}", "", "| القمّة | المرصود | مئين 95 للخلطات | يفوق من الخلطات | الحكم |", "|---|---|---|---|---|"]
    for k, nm in names:
        v = ver.get(k) or {}
        f3 = lambda x: "—" if x is None or x != x else f"{x:.3f}"       # noqa: E731
        L.append(f"| {nm} | {f3(v.get('obs'))} | {f3(v.get('p95'))} | {pct(v.get('beats_frac'))} | {'✅ يعبر' if v.get('pass') else '❌ في حدود الصدفة'} |")
    p95 = (ver.get("best_print") or {}).get("p95")
    L += ["", "| أقوى التوليفات | z | المنفجرون | الحاملون | نسبةُ الانفجار | الحكم |", "|---|---|---|---|---|---|"]
    for t in (arm.get("top_combos") or [])[:8]:
        L.append(f"| {' ＋ '.join(W.condition(c) for c in t['conds'])} | {t['z']:.2f} | {t['k']} | {t['n']:,} | {pct(t['k'] / t['n'] if t['n'] else None)} | "
                 f"{'✅ يعبر' if (p95 is not None and t['z'] > p95) else '❌ في حدود الصدفة'} |")
    types = (arm.get("summary") or {}).get("types") or {}
    if types:
        L += ["", "- لكلّ نوع (الشروطُ المنفردة وخلطُها): " + " · ".join(
            k + (": ✅" if v.get("pass") else ": ❌") + f" (z {v.get('obs'):.2f} مقابل {v.get('p95'):.2f})" for k, v in types.items())]
    return L + [""]


def missed_section(arm, idx):
    L = ["## ⑤ «ما فات البوت»", ""]
    if not arm:
        return L + ["- لم يصدر.", ""]
    pos = arm.get("positives") or []
    rej, walls, tracked = {}, {}, 0
    for p in pos:
        rej[p.get("bot_reject") or "غير مقيس"] = rej.get(p.get("bot_reject") or "غير مقيس", 0) + 1
        row = p.get("row") or {}
        if row:
            tracked += 1
            w = (row.get("wall") or {}).get("label") or "بلا جدار"
            walls[w] = walls.get(w, 0) + 1
    srt = lambda d: " · ".join(f"{k} {v}" for k, v in sorted(d.items(), key=lambda t: -t[1]))      # noqa: E731
    L += [f"- منفجرو الشهر في المقارنة {len(pos)} · منهم في «تحت المتابعة» يومَ القرار {tracked}.",
          f"- رفضُ الفرز بأرقام الإنتاج على شموع يوم القرار: {srt(rej) or '—'}", f"- جدارُ الصفّ عند المتابَعين: {srt(walls) or '—'}",
          "- الجدولُ سهمًا سهمًا (الجدار · الناقصُ وهامشُه · الجاهزيّة): `out/ARM_A.md` §⑧.", ""]
    return L


def dossier_section(idx):
    L = ["## ⑥ الملفّات", ""]
    if not idx:
        return L + ["- لم تصدر.", ""]
    known = [x for x in idx if (x.get("timing") or {}).get("session")]
    by = {}
    for x in known:
        by[x["timing"]["session"]] = by.get(x["timing"]["session"], 0) + 1
    L += [f"- {len(idx)} ملفًّا (من 20 جلسةً قبل يوم القرار إلى 10 بعد القمّة · بنودُ أ-م والمسحُ الكامل): `out/DOSSIERS.md` و`out/dossiers/`.",
          f"- بدايةُ الحركة لحظيًّا (المقيسُ {len(known)}): " + (" · ".join(f"{k} {v}" for k, v in sorted(by.items(), key=lambda t: -t[1])) or "—"), ""]
    return L


def build():
    V, idx = _load("verify.json"), _load(os.path.join("dossiers", "index.json"))
    arms = {a: _load(f"arm{a}.json.gz") for a in ("A", "B")}
    val = _load("validate.json")
    L = ["# 🗂️🔬 `T-CASE31` — الملفُّ الجنائيّ لمنفجري الشهر: المخرجُ النهائيّ (مولَّدٌ آليًّا من `out/` · لا يُعدَّل باليد)", ""]
    L += verify_section(V) if V else ["## ① جدولُ التحقّق", "", "- لم يصدر.", ""]
    L += ["## ② أهمُّ 10 فروق بلغةٍ بسيطة", ""]
    for a in ("A", "B"):
        L += arm_section(a, arms[a])[0]
    L += ["## ③ سماتُ الاستبعاد", ""]
    for a in ("A", "B"):
        L += exclusion_section(a, arms[a])
    L += ["## ④ البصماتُ ونتيجةُ الخلط والتحقّق", ""]
    for a in ("A", "B"):
        L += prints_section(a, arms[a])
    if val:
        L += ["### التحقّقُ للخلف لما ثُبِّت", "", "| الذراع | النوع | البصمة | المجتمع | الحكم |", "|---|---|---|---|---|"]
        L += [f"| {r['arm']} | {r['kind']} | {' ＋ '.join(W.condition(t) for t in r['texts'])} | {r['pop']} | **{r['verdict']}** |" for r in val] + [""]
    else:
        L += ["- التحقّق: لم يصدر (يلزمه ملفُّ تثبيتٍ · وصفرُ عابرٍ ⟵ لا تثبيتَ ولا تحقّق).", ""]
    L += missed_section(arms["A"], idx) + dossier_section(idx)
    return "\n".join(L) + "\n"


def main(argv):
    if not C.contract_ok():
        return C.RC_CONTRACT
    md = build()
    out = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(C.OUT, "FINAL_BODY.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(md[:3000], flush=True)
    return C.RC_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
