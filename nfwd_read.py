#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⏳🔓 `N-FWD` — القراءةُ الأماميّة لسياسة الحمل إلى الإغلاق (العقد `nfwd_prereg.md`).

أمرُ المالك 2026-11-16: «افتح الخروج لـN-FWD بعقد — أقرّ TRAIL_REOPEN لقراءة N-FWD وحدها … لا تغيير في الإنتاج».
🔒 **محورُ إدارة الخروج مُغلَقٌ** (`T-TRAIL`) ⇒ هذه الأداةُ تخرج 8 ما لم يكن `TRAIL_REOPEN == "1"` حرفيًّا ·
وتخرج 11 إن تغيّر العقدُ عن بصمته · وقراءةٌ فقط: صفرُ إرسالٍ وصفرُ كتابةِ حالة (`selfcheck_readonly` بالاسم).

**كلُّ البناء والأذرع والحسم بالاسم** من `ophold2_arms`/`optrade_arms`/`ophold_arms` — والجديدُ هنا ثلاثةٌ وصفيّة:
قاعدةُ النصفين بالعدد (`split_date`) · حصّةُ الذيل 5% (`top_share`) · والوسيط (`median_of`) · وفلترُ 🥇 J1 (`j1_rows`).
**رموزُ الخروج:** 0 حكم (1/2) · 2 لا مفتاح · 3 تغطية · 4 صفرُ مِرساة · 5 `V-F1` · 6 حارس · 8 لا إقرار · 9 «لا حكم» · 11 العقد.
"""
import hashlib
import math
import os
import statistics as st
import sys

import ophold2_arms as O2
from ophold2_arms import (GOV, attach_hold2, pair_counts, pair_rows, paired_placebo,
                          relabel_halves, v_n2, v_n3)              # بالاسم
from optrade_arms import (FLOOR_ARM, FLOOR_PAIR, MIN_COVER, RC_COVER, RC_GUARD,
                          RC_NOANCHOR, RC_NOKEY, RC_NOVERDICT, RC_OK, RC_POP,
                          attach_trades, build_rows, crit_halves,
                          no_config_assign, read_costs, read_hstar,
                          selfcheck_readonly)                     # بالاسم
from ophold_arms import (arm_R, arm_stats, arm_subset, exit_mix, floors_of,
                         paired, read_verdict)                    # بالاسم
from ophold_arms import _ci_txt as ci_txt                         # عرضٌ لا حسم
from ophold_arms import _n as nfmt                                # عرضٌ لا حسم
from tierlink_probe import anchor_history                         # بالاسم
from tier_fwd_report import load_ledger                           # بالاسم

# ═══════════════ ⓪ ثوابتُ العقد — لا مُدخَلَ يغيّرها ════════════════════════════
CONTRACT = "nfwd_prereg.md"
CONTRACT_SHA = "105a6d9f487387f1fbafad28823a62b413b3f813c28b8882d9c8256ff7520b6a"
SINCE, UNTIL = "2026-09-16", "2026-11-14"           # §② شاملًا
N_ANCHORS = 1555                                    # §② `V-F1`
J1_MIN = 30                                         # §④ «لا قياس» دونه
TAIL_FRAC = 0.05                                    # §④ أعلى 5%
REOPEN_ENV = "TRAIL_REOPEN"
RC_CLOSED, RC_CONTRACT = 8, 11
DRY = os.environ.get("NFWD_DRY", "").strip() == "1"


def _log(msg: str = "") -> None:
    print(msg, flush=True)


def contract_ok(path: str = None, sha: str = None) -> bool:
    """البصمةُ تُقرأ وقتَ النداء (لا قيمةً افتراضيّةً مجمَّدة) ⟵ خروج 11 إن تغيّر العقد."""
    try:
        return (hashlib.sha256(open(path or CONTRACT, "rb").read()).hexdigest()
                == (CONTRACT_SHA if sha is None else sha))
    except OSError:
        return False


def reopened(env=None) -> bool:
    """الإقرارُ حرفيٌّ: `"1"` وحدَه يفتح (صيغةُ «غيرُ فارغ» ترفع الإغلاقَ بافتراض المُدخَل `0`)."""
    return (os.environ if env is None else env).get(REOPEN_ENV, "") == "1"


# ═══════════════ ① الجديدُ هنا — وصفيٌّ مسجَّل لا حسم ═══════════════════════════
def split_date(rows):
    """§③ — `d*` تاريخُ الصفّ ذي الترتيب ⌈n/2⌉ (من 1) بين القابل للتداول تحت `HN` مرتَّبًا بـ(التاريخ · الرمز)."""
    tr = sorted((r["date"], r["sym"]) for r in rows if r.get(GOV))
    if not tr:
        return None
    return tr[math.ceil(len(tr) / 2) - 1][0]


def top_share(vals, frac: float = TAIL_FRAC):
    """§④ — أعلى ⌈frac⌉ من القيم (`k = max(1, round(frac·n))`) ÷ مجموع الموجب ×100 · أو None."""
    v = sorted((x for x in vals if x is not None), reverse=True)
    pos = sum(x for x in v if x > 0)
    if not v or pos <= 0:
        return None
    k = max(1, int(round(len(v) * frac)))
    return sum(x for x in v[:k] if x > 0) / pos * 100.0


def median_of(vals):
    v = [x for x in vals if x is not None]
    return st.median(v) if v else None


def j1_rows(rows):
    """§④ — 🥇 J1 وحدَها: `features.j1 == "J1"` (والمجهولُ «؟» خارجها)."""
    return [r for r in rows if (r.get("f") or {}).get("j1") == "J1"]


def arm_vals(rows, arm: str, c: float, s: float):
    return [arm_R(r, arm, c, s) for r in arm_subset(rows, arm)]


def paired_diffs(rows, a1: str, a2: str, c: float, s: float):
    """فروقٌ مقترنةٌ للوسيط وحدَه (§④) — الفاصلُ والمتوسّطُ من `paired` بالاسم."""
    out = []
    for r in rows:
        x, y = arm_R(r, a1, c, s), arm_R(r, a2, c, s)
        if x is not None and y is not None:
            out.append(x - y)
    return out


# ═══════════════ ② main ════════════════════════════════════════════════════════
def main() -> int:                                               # noqa: PLR0911, PLR0915
    if not contract_ok():
        _log(f"⛔ العقد `{CONTRACT}` لا يطابق بصمتَه — خروج 11 قبل أيّ جلب")
        return RC_CONTRACT
    if not reopened():
        _log(f"⛔ محورُ إدارة الخروج مُغلَق (`T-TRAIL`) — `{REOPEN_ENV}` لم يُقَرّ بـ\"1\" — خروج 8")
        return RC_CLOSED
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        _log("⛔ لا POLYGON_API_KEY — خروج 2")
        return RC_NOKEY
    src = open(__file__, encoding="utf-8").read()
    if not (selfcheck_readonly(src) and no_config_assign(src)):
        _log("⛔ حارسُ «قراءةٌ فقط / صفرُ إسناد» ساقط — خروج 6")
        return RC_GUARD
    costs, hs = read_costs(), read_hstar()
    if not costs.get("ok") or not hs.get("ok"):
        _log(f"⛔ التكلفة أو `h*` لا تُستخرَج نصًّا: {costs.get('why') or hs.get('why')} — خروج 6")
        return RC_GUARD
    C, S = costs["C-MED"], costs["S-MED"]
    _log("⏳🔓 N-FWD — الحملُ إلى أوّل إغلاقٍ نظاميٍّ بعد المِرساة · أماميًّا (العقد nfwd_prereg.md)")
    _log(f"🔓 `{REOPEN_ENV}` مُقَرٌّ لهذه القراءة وحدَها (أمرُ المالك 2026-11-16) · لا تغيير في الإنتاج")
    _log(f"⚙️ النافذة {SINCE} … {UNTIL} · التكلفة C-MED {C*100:.4f}% · S-MED {S*100:.4f}%")
    anchors = {k: v for k, v in anchor_history(SINCE).items() if k[0] <= UNTIL}
    if not anchors:
        _log("⛔ صفرُ مِرساة — خروج 4")
        return RC_NOANCHOR
    if len(anchors) != N_ANCHORS:
        _log(f"⛔ V-F1 — المراسي {len(anchors)} لا {N_ANCHORS} — خروج 5")
        return RC_POP
    _log(f"🔒 V-F1: المراسي {len(anchors)} = العقد")
    ledger = {(r["date"], r["symbol"]): r for r in load_ledger()}
    rows, fails, nobase = build_rows(key, anchors, ledger)
    cover = len(rows) / len(anchors)
    _log(f"🩺 التغطية: قِيس {len(rows)} · تعذّر {fails} · بلا أساس {nobase} = {cover*100:.1f}%")
    if cover < MIN_COVER:
        _log("⛔ التغطية دون الحدّ — خروج 3")
        return RC_COVER
    attach_trades(rows, key, costs)
    diag = attach_hold2(rows, key)
    ok2, bad2 = v_n2(rows)
    ok3, bad3, n_non = v_n3(rows)
    if not (ok2 and ok3):
        _log(f"⛔ V-F2/V-F3 — H0≠P0 {bad2} · HN≠HC0 {bad3} — خروج 6")
        return RC_GUARD
    _log(f"🔒 V-F2: H0 ≡ P0 في {len(rows)} · V-F3: HN ≡ HC0 على {n_non} غيرِ افتريّ")
    d_star = split_date(rows)
    relabel_halves(rows, d_star)                                 # §③ قبل أيّ R
    trad = arm_subset(rows, GOV)
    per_half_n = {h: sum(1 for r in trad if r["half"] == h) for h in ("H1", "H2")}
    pc = pair_counts(pair_rows(rows, GOV)[0])
    _log(f"✂️ §③ d* = {d_star} · القابلُ للتداول {len(trad)} (H1 {per_half_n['H1']} · H2 {per_half_n['H2']}) · "
         f"أزواجُ C-MOM H1 {pc['H1']} · H2 {pc['H2']} · 🥇 J1 قابلٌ {len(arm_subset(j1_rows(rows), GOV))}")
    _log(f"🩺 تشخيصُ النافذة: {diag}")
    if DRY:
        _log("🧪 NFWD_DRY — أعدادٌ فقط · صفرُ R وصفرُ تكلفةٍ وصفرُ فاصل")
        return RC_OK
    return report(rows, per_half_n, costs, C, S)


def _j1_block(rows, C, S):
    jr = j1_rows(rows)
    jt = arm_subset(jr, GOV)
    jm = paired_placebo(jr, GOV, C, S)
    _log(f"  🥇 J1: قابلٌ {len(jt)} · أزواجُ C-MOM {jm['n']} (حدّ {J1_MIN})")
    if len(jt) < J1_MIN or jm["n"] < J1_MIN:
        _log("     ⟵ «لا قياس» (دون الحدّ) · والأرقامُ تُطبَع وصفًا")
    js = arm_stats(jr, GOV, C, S)
    jp = paired(jr, GOV, "H0", C, S)
    _log(f"     HN {ci_txt(js['pooled'])} · H1 {ci_txt(js['halves'].get('H1'))} · H2 {ci_txt(js['halves'].get('H2'))}")
    _log(f"     وسيطُ HN {nfmt(median_of(arm_vals(jr, GOV, C, S)))}R")
    _log(f"     HN − H0 {ci_txt(jp['pooled'])} · H1 {ci_txt(jp['halves'].get('H1'))} · H2 {ci_txt(jp['halves'].get('H2'))}")
    _log(f"     HN − C-MOM {ci_txt(jm['pooled'])} · H1 {ci_txt(jm['halves'].get('H1'))} · H2 {ci_txt(jm['halves'].get('H2'))}")
    return (js["pooled"] or {}).get("mean")


def report(rows, per_half_n, costs, C, S) -> int:                # noqa: PLR0915
    sh = arm_stats(rows, GOV, C, S)
    s0 = arm_stats(rows, "H0", C, S)
    cp0 = paired(rows, GOV, "H0", C, S)
    mom = paired_placebo(rows, GOV, C, S)
    mix = exit_mix(rows, GOV)
    hn_v, h0_v = arm_vals(rows, GOV, C, S), arm_vals(rows, "H0", C, S)
    _log("")
    _log("═══ ① الأذرع عند الخليّة الحاكمة (C-MED, S-MED) ═══")
    for nm, s in (("HN 🥇", sh), ("H0", s0)):
        _log(f"  {nm:6s} n={s['n']:4d} · مجمَّع {ci_txt(s['pooled'])}")
        for h in ("H1", "H2"):
            _log(f"         {h}: {ci_txt(s['halves'].get(h))}")
    _log("")
    _log("═══ ② الضبطان الحاكمان ═══")
    _log(f"  HN − H0    : {ci_txt(cp0['pooled'])} · H1 {ci_txt(cp0['halves'].get('H1'))} · H2 {ci_txt(cp0['halves'].get('H2'))}")
    _log(f"  HN − C-MOM : {ci_txt(mom['pooled'])} · H1 {ci_txt(mom['halves'].get('H1'))} · H2 {ci_txt(mom['halves'].get('H2'))}")
    _log("               أزواج: " + " · ".join(f"{k} {mom['lv'].get(k, 0)}"
                                               for k in ("D0", "D1", "D2", "D3", "D4", "—")))
    _log(f"               مستوى HN على الأزواج {nfmt(mom['a_mean'])}R · الزخم {nfmt(mom['p_mean'])}R")
    _log("")
    _log("═══ ③ الوسيطُ وحصّةُ الذيل 5% (وصفيٌّ مسجَّل) ═══")
    med_hn = median_of(hn_v)
    _log(f"  وسيطُ R: HN {nfmt(med_hn)} · H0 {nfmt(median_of(h0_v))} · "
         f"الزخم على أزواجه {nfmt(median_of(z['p'] for z in mom['pairs']))}")
    _log(f"  وسيطُ الفرق: HN − H0 {nfmt(median_of(paired_diffs(rows, GOV, 'H0', C, S)))} · "
         f"HN − C-MOM {nfmt(median_of(z['d'] for z in mom['pairs']))}")
    ts_hn, ts_h0 = top_share(hn_v), top_share(h0_v)
    _log(f"  أعلى 5% من الصفوف ÷ مجموع R الموجب: HN {'—' if ts_hn is None else f'{ts_hn:.1f}%'} · "
         f"H0 {'—' if ts_h0 is None else f'{ts_h0:.1f}%'}")
    _log("")
    _log("═══ ④ 🥇 J1 وحدَها (وصفيٌّ مسجَّل) ═══")
    j1_mean = _j1_block(rows, C, S)
    _log("")
    _log("═══ ⑤ مزيجُ الخروج تحت HN ═══")
    for h in ("H1", "H2", "الكلّ"):
        if mix[h]["n"]:
            _log(f"  {h:5s} n={mix[h]['n']:4d} · وقف {mix[h]['loss']:5.1f}% · إغلاق {mix[h]['window']:5.1f}%")
    _log("")
    _log("═══ ⑥ شبكةُ c × s لـHN — وصفيّة ═══")
    for g in O2.sens_grid(rows, costs):
        _log(f"  c={g['c']:6s} s={g['s']:6s} ⇒ {nfmt(g['mean'])}R")
    _log("")
    nf1 = crit_halves(sh["halves"], sh["pooled"])
    nf2 = crit_halves(cp0["halves"], cp0["pooled"])
    nf3 = crit_halves(mom["halves"], mom["pooled"])
    floors = floors_of(per_half_n, mom["counts"])
    _log("═══ ⑦ المعاييرُ والأرضيّة ═══")
    for nm, cr in (("NF1 HN", nf1), ("NF2 HN − H0", nf2), ("NF3 HN − C-MOM", nf3)):
        _log(f"  {nm:15s}: {'✅' if cr['pass'] else '🔴'} · موجبٌ بالنصفين={cr['pos']} · فاصلُ المجمَّع فوق الصفر={cr['lo']}")
    _log(f"  الأرضيّة       : {'✅' if floors['pass'] else '🔴'} · صفوف {floors['n']} (حدّ {FLOOR_ARM}) · "
         f"أزواج {floors['pairs']} (حدّ {FLOOR_PAIR})")
    br, (lbl, why) = read_verdict(nf1, nf2, nf3, floors)
    _log("")
    _log("═══ ⑧ التنبّؤاتُ الثمانية ═══")
    m = (sh["pooled"] or {}).get("mean")
    hm = [(sh["halves"].get(h) or {}).get("mean") for h in ("H1", "H2")]
    preds = [
        ("NFP1", "HN سالبٌ مجمَّعًا وفي النصفين", m is not None and m < 0 and all(x is not None and x < 0 for x in hm)),
        ("NFP2", "HN − H0 سالبٌ مجمَّعًا", ((cp0["pooled"] or {}).get("mean") or 0) < 0),
        ("NFP3", "HN − C-MOM سالبٌ مجمَّعًا", ((mom["pooled"] or {}).get("mean") or 0) < 0),
        ("NFP4", "وسيطُ HN ‏−0.9 أو أدنى", med_hn is not None and med_hn <= -0.9),
        ("NFP5", "أعلى 5% تحمل أكثرَ من نصف الـR الموجب", ts_hn is not None and ts_hn > 50.0),
        ("NFP6", "HN على 🥇 J1 سالبُ المتوسّط", j1_mean is not None and j1_mean < 0),
        ("NFP7", "الفرعُ 2 «فشلت»", br == 2),
        ("NFP8", "H0 سالبُ المتوسّط", ((s0["pooled"] or {}).get("mean") or 0) < 0),
    ]
    for pid, txt, ok in preds:
        _log(f"  {pid}: {txt} ⇒ {'✅' if ok else '🔴 مكذَّب'}")
    _log("")
    _log(f"🏁 الفرعُ {br} — **{lbl}** · {why}")
    _log("⛔ لا تغيير في الإنتاج بأيّ فرع (أمرُ المالك) · و«تُوصى» اقتراحٌ للمالك وحدَه.")
    return RC_OK if br in (1, 2) else RC_NOVERDICT


if __name__ == "__main__":
    sys.exit(main())
