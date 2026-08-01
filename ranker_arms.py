#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🥇 T-RANKER — مُشغِّل الأذرع الأربع (`ranker_prereg.md`).

يشغّل الباكتيست مرّةً واحدة ثم يُعيد **ترتيب البِركة نفسها** بأربع أذرع على **نفس
الجلسات ونفس السعة ونفس المحرّك** ⇒ المقارنة **مزدوجةٌ داخل الجلسة** فلا تحمل ضجيج
السوق (وهو ما أسقط كلّ تجربةٍ قارنت سنةً بسنة).

🔒 **بحث/قياس — خارج الإنتاج تمامًا:** لا يُستورَد في `Super_stock.py` (مقفول)،
ولا يكتب حالة، ولا يمسّ بوّابةً ولا عتبة. يلزمه `BT_REPLAY10=1` (‏`exit_date`/`rr`)
و`BT_POTENTIAL=1` (‏`mg_pre_stop` = مقياس المنفجرين) و`BT_FEATURES=1` (‏`sector` لـK3).
"""
from __future__ import annotations

import os

os.environ.setdefault("SCREENER_MODE", "BACKTEST")
os.environ.setdefault("BT_REPLAY10", "1")
os.environ.setdefault("BT_POTENTIAL", "1")
os.environ.setdefault("BT_FEATURES", "1")

import Super_stock as S            # noqa: E402
import replay10 as RP              # noqa: E402

EXPLODE_PCT = 100.0                # §⑤ المقياس الأساسيّ — مثبَّتٌ قبل الأرقام
N_RANDOM = 200                     # خلطات K1 (أرضية الضجيج)


def _sector_key(c):
    """مفتاح K3 = القطاع. ⚠️ **حدُّ صدقٍ مُعلَن:** مصدرُه `_bt_feature_enrich`
    (ياهو **اليوم**) لا نقطةً زمنية — والقطاع شبه ثابت، **ويخصّ K3 وحدها**.
    غيابُه ⇒ `None` ⇒ **لا تنويع لذلك المرشّح** (لا يُقصى بالظنّ)."""
    v = (c.payload or {}).get("sector")
    v = str(v).strip() if v else ""
    return v or None


def _exploders(taken):
    """§⑤ المقياس الأساسيّ: المُسلَّمون الذين بلغوا +100% **قبل** وقفهم."""
    n = 0
    for c in taken:
        try:
            if float((c.payload or {}).get("mg_pre_stop") or 0.0) >= EXPLODE_PCT:
                n += 1
        except (TypeError, ValueError):
            continue
    return n


def _concentration(taken):
    """أكبر حصّةِ رمزٍ من المنفجرين المُسلَّمين (‏§⑥-5)."""
    by = {}
    for c in taken:
        try:
            if float((c.payload or {}).get("mg_pre_stop") or 0.0) >= EXPLODE_PCT:
                by[c.symbol] = by.get(c.symbol, 0) + 1
        except (TypeError, ValueError):
            continue
    tot = sum(by.values())
    return (max(by.values()) / tot) if tot else 0.0


def _run(cands, idx, outcome_of, ranker, dedupe=None):
    return RP.replay(cands, outcome_of=outcome_of, ranker=ranker,
                     capacity=RP.CAPACITY, sessions=range(0, len(idx)),
                     dedupe_key=dedupe)


def _paired(a_taken, b_taken, n_sessions):
    """الفرق المزدوج **داخل الجلسة** لصافي R/جلسة، بفاصل bootstrap عنقوديّ
    (العنقود = الجلسة) — نفس آلة `T-REPLAY10`."""
    def _by_sess(taken):
        d = {}
        for c in taken:
            r = RP.r_unit(c.payload)
            if r is not None:
                d[c.session] = d.get(c.session, 0.0) + r
        return d
    A, B = _by_sess(a_taken), _by_sess(b_taken)
    diffs = [(A.get(s, 0.0) - B.get(s, 0.0)) for s in range(n_sessions)]
    return diffs


def _ci(diffs, draws=4000):
    """فاصل bootstrap عنقوديّ بالجلسة — حتميّ (‏بذرةٌ ثابتة، لا `random`)."""
    import hashlib
    n = len(diffs)
    if n == 0:
        return (0.0, 0.0, 0.0)
    mean = sum(diffs) / n
    means = []
    for b in range(draws):
        tot = 0.0
        for j in range(n):
            h = hashlib.sha256(f"{b}|{j}".encode()).digest()
            tot += diffs[int.from_bytes(h[:8], "big") % n]
        means.append(tot / n)
    means.sort()
    return (mean, means[int(0.025 * draws)], means[int(0.975 * draws)])


def run() -> int:
    trades = S.run_backtest() or []
    year = (os.environ.get("BACKTEST_YEAR", "") or "?").strip()
    print(f"\n{'=' * 72}\n🥇 T-RANKER · السنة {year}\n{'=' * 72}")
    have = [t for t in trades if t.get("exit_date")]
    if not have:
        print("⛔ `BT_REPLAY10` خامل ⇒ لا كون ⇒ لا تُفسَّر نتيجة.")
        return 2
    cands, idx, outcome_of = RP.candidates_from_trades(have)
    n_sess = len(idx)
    _mg = sum(1 for t in have if t.get("mg_pre_stop") is not None)
    _sec = sum(1 for t in have if t.get("sector"))
    print(f"البِركة: {len(cands)} إشارة · {n_sess} جلسة · السعة {RP.CAPACITY}")
    print(f"🩺 العلم فعّال: `mg_pre_stop` في {_mg}/{len(have)} · "
          f"`sector` في {_sec}/{len(have)}")
    if _mg == 0:
        print("⛔ `BT_POTENTIAL` خامل ⇒ لا مقياسَ منفجرين ⇒ **لا حكم**.")
        return 2
    if n_sess < 100:
        print(f"⚠️ العيّنة {n_sess} < 100 جلسة — الشرط ①ساقط لهذي السنة.")

    arms = {"K0 (الإنتاجيّ)": _run(cands, idx, outcome_of, RP.rank_actual),
            "K2 (rr تنازليًّا)": _run(cands, idx, outcome_of, RP.rank_rr),
            "K3 (تنويعٌ أوّلًا)": _run(cands, idx, outcome_of, RP.rank_actual,
                                       dedupe=_sector_key)}
    # K1: أرضية الضجيج — متوسط خلطاتٍ حتميّة
    rnd = [_run(cands, idx, outcome_of, RP.make_rank_random(s))
           for s in range(N_RANDOM)]
    print("\n📊 الأذرع (المقياس الأساسيّ = المنفجرون المُسلَّمون ≥+100%):")
    base = arms["K0 (الإنتاجيّ)"]
    rows = {}
    for name, res in arms.items():
        ex = _exploders(res["taken"])
        rows[name] = ex
        print(f"  {name}: مأخوذ={len(res['taken'])} · "
              f"**منفجرون مُسلَّمون={ex}** · تركيز={_concentration(res['taken']):.0%}"
              f" · مرفوض بالسعة={res['rejected_cap']}"
              + (f" · بالتنويع={res['rejected_div']}" if res['rejected_div'] else ""))
    _rex = [_exploders(r["taken"]) for r in rnd]
    _rex.sort()
    k1 = sum(_rex) / len(_rex)
    print(f"  K1 (عشوائيّ · {N_RANDOM} خلطة): منفجرون مُسلَّمون **متوسط={k1:.2f}** "
          f"· وسيط={_rex[len(_rex) // 2]} · مدى=[{_rex[0]}, {_rex[-1]}]")

    print("\n📐 الفرق المزدوج داخل الجلسة (صافي R/جلسة · مقابل K0):")
    for name in ("K2 (rr تنازليًّا)", "K3 (تنويعٌ أوّلًا)"):
        m, lo, hi = _ci(_paired(arms[name]["taken"], base["taken"], n_sess))
        print(f"  {name} − K0: {m:+.4f} · 95%=[{lo:+.4f}, {hi:+.4f}]")

    print("\n🧭 المعيار الخماسيّ (‏§⑥ — الخمسة معًا، ويُقرأ عبر السنوات الثلاث):")
    print(f"  ① العيّنة: {n_sess} جلسة (يلزم ≥100) ⇒ "
          + ("✅" if n_sess >= 100 else "🔴"))
    for name in ("K2 (rr تنازليًّا)", "K3 (تنويعٌ أوّلًا)"):
        print(f"  ② {name} مقابل K0: {rows[name]} مقابل {rows['K0 (الإنتاجيّ)']} ⇒ "
              + ("✅ متفوّقة هذي السنة"
                 if rows[name] > rows["K0 (الإنتاجيّ)"] else "🔴")
              + f" · ④ مقابل K1 ({k1:.2f}): "
              + ("✅" if rows[name] > k1 else "🔴"))
    print("  ③ الدلالة و⑤ التركيز يُحكَمان **مجمَّعًا** بعد السنوات الثلاث.")
    print("\n⚠️ حدود الصدق (‏§⑧): انحياز بقاء غير مقيس · تشويه تقسيمات · بلا افتر ·"
          " `M13`/`M14` خارج الباكتيست · كسرُ التعادل داخل اليوم أبجديّ — "
          "**والذراعان تتقاسمانها بالبناء** فلا تُبطل المقارنة المزدوجة.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
