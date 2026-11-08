# -*- coding: utf-8 -*-
"""📊 تحديثُ «مثل هذا الإشعار» أسبوعيًّا من سجلّ الحصاد (أمرُ المالك 2026-11-08 ②).

البذرةُ أرقامُ `T-OPSIG` (`oe_card_stats.json`) · وكلَّ أسبوع: إشعاراتُ «هنا الدخول» من `tier_fwd_ledger.jsonl` (أبكرُ مِرساةٍ لكلّ يومٍ ورمز ·
🥇 = J1 ∧ «قوي» بقاعدة `live_vs_shadow.j1_map` بالاسم) ⟵ شموعُ الدقيقة ونتيجةُ `opsig.measure` بالاسم (الدخول · أعلى ربح · ‏+20% · الكارثيّ ·
الوقف −10%) ⟵ سجلٌّ إلحاقيّ `oe_card_outcomes.jsonl` (يُقاس الإشعارُ مرّةً) ⟵ `opsig.card_stats` بالاسم ⟵ يُنشَر في `oe_card_stats.json` **حين يبلغ
المحصودُ 300 عاديًّا و30 🥇** وإلّا تبقى البذرة ومعها عددُ المحصود. يومُ التقسيم يُستبعد (`shadow_ready.split_ratio`) كما في T-OPSIG.
قراءةٌ وكتابةُ هذين الملفّين وحدَهما · لا تلغرام · لا حالةَ إنتاج.
الأوضاع: `refresh` (يلزم POLYGON_API_KEY) · `stats` (بلا شبكة: يعيد الحساب من السجلّ)."""
import datetime as dt
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(ROOT, "tier_fwd_ledger.jsonl")
OUTCOMES = os.path.join(ROOT, "oe_card_outcomes.jsonl")
STATS = os.path.join(ROOT, "oe_card_stats.json")
MIN_NORMAL, MIN_GOLD = 300, 30
GOLD = "قوي"


def log(m=""):
    print(m, flush=True)


def _opsig():
    sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "opsig"))
    import opsig as OP
    return OP


def _lvs():
    sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "live_vs_shadow"))
    import live_vs_shadow as LVS
    return LVS


def alerts_of(lines, j1_map):
    """{(يوم، رمز): {ms، gold}} — أبكرُ مِرساةٍ (`anchor_ms` ثمّ `price_ms`) · و🥇 = صفُّ `j1_map` الأبكر وفئتُه «قوي»."""
    j1, _has = j1_map(lines)
    out = {}
    for ln in lines:
        try:
            r = json.loads(ln)
        except (ValueError, TypeError):
            continue
        if not isinstance(r, dict) or not r.get("date") or not r.get("symbol"):
            continue
        ms = r.get("anchor_ms") or r.get("price_ms")
        if not ms:
            continue
        k = (str(r["date"]), str(r["symbol"]).upper())
        if k not in out or int(ms) < out[k]["ms"]:
            out[k] = {"ms": int(ms)}
    for k, v in out.items():
        j = j1.get(k)
        v["gold"] = bool(j) and j.get("tier") == GOLD
    return out


def load_outcomes(path=OUTCOMES):
    rows = []
    try:
        for ln in open(path, encoding="utf-8"):
            ln = ln.strip()
            if ln:
                rows.append(json.loads(ln))
    except OSError:
        pass
    return rows


def stats_from(rows, card_stats):
    ok = [r for r in rows if r.get("out")]
    return {"normal": card_stats([r for r in ok if not r.get("gold")]), "gold": card_stats([r for r in ok if r.get("gold")])}


def publish(st, seed, asof):
    """البذرةُ حتى يبلغ المحصودُ الحدَّين · ثمّ المحصودُ وحدَه — `harvest` يُطبع دائمًا."""
    nn, ng = (st["normal"] or {}).get("n", 0), (st["gold"] or {}).get("n", 0)
    harvest = {"n_normal": nn, "n_gold": ng, "asof": asof}
    keep = ("n", "maxg_med", "p20", "cat", "s10_med")
    if nn >= MIN_NORMAL and ng >= MIN_GOLD:
        return {"asof": asof, "source": f"سجلُّ الحصاد (`tier_fwd_ledger.jsonl` ⟵ `oe_card_outcomes.jsonl`) · المحصود {nn} عاديًّا و{ng} 🥇",
                "normal": {k: st["normal"].get(k) for k in keep}, "gold": {k: st["gold"].get(k) for k in keep},
                "defs": seed.get("defs"), "harvest": harvest}
    return dict(seed, harvest=harvest)


def _today_ny():
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    except Exception:                                            # noqa: BLE001
        return dt.date.today().isoformat()


def mode_refresh(key, cap=None):
    from concurrent.futures import ThreadPoolExecutor
    OP, LVS = _opsig(), _lvs()
    from tier_fwd_report import fetch_day
    from tierlink_probe import daily_range
    from shadow_ready import split_ratio
    lines = open(LEDGER, encoding="utf-8").read().splitlines()
    al = alerts_of(lines, LVS.j1_map)
    done = {(r["day"], r["sym"]) for r in load_outcomes() if not r.get("err")}
    today = _today_ny()
    todo = sorted(k for k in al if k not in done and k[0] < today)
    if cap:
        todo = todo[:cap]
    log(f"📊 الإشعاراتُ في السجلّ {len(al)} · مقيسةٌ سلفًا {len(done)} · تُقاس الآن {len(todo)} (قبل {today})")

    def _one(k):
        d, sym = k
        a = al[k]
        try:
            dl = daily_range(sym, d, key)
            pd_, _p0 = LVS.prev_close(dl, d)
            sr = split_ratio(sym, pd_, d, key) if pd_ else None
            if sr is not None and sr != 1.0:
                return {"day": d, "sym": sym, "ms": a["ms"], "gold": a["gold"], "skip": "split"}
            r = OP.measure(d, sym, a["ms"], fetch_day(sym, d, key), lambda s, x, y: (None, None))
            row = {"day": d, "sym": sym, "ms": a["ms"], "gold": a["gold"]}
            if r.get("out"):
                row.update(E=r["E"], out=r["out"])
            else:
                row["skip"] = "nobars"
            return row
        except Exception as e:                                   # noqa: BLE001
            return {"day": d, "sym": sym, "ms": a["ms"], "gold": a["gold"], "err": type(e).__name__}
    with ThreadPoolExecutor(8) as pool:
        new = list(pool.map(_one, todo))
    with open(OUTCOMES, "a", encoding="utf-8") as fh:
        for r in new:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    log(f"📥 كُتب {len(new)} · بنتيجة {sum(1 for r in new if r.get('out'))} · تقسيم {sum(1 for r in new if r.get('skip') == 'split')} · "
        f"بلا شموع {sum(1 for r in new if r.get('skip') == 'nobars')} · خطأ {sum(1 for r in new if r.get('err'))}")
    return mode_stats(today)


def mode_stats(asof=None):
    OP = _opsig()
    seed = json.load(open(STATS, encoding="utf-8"))
    rows = [r for r in load_outcomes() if not r.get("err")]
    st = stats_from(rows, OP.card_stats)
    pub = publish(st, seed if "T-OPSIG" in str(seed.get("source")) else _seed_of(seed), asof or _today_ny())
    with open(STATS, "w", encoding="utf-8") as fh:
        json.dump(pub, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    log(f"📊 المنشور: {pub['source']}")
    for k in ("normal", "gold"):
        log(f"   {k}: {pub[k]}")
    log(f"   المحصود: {pub.get('harvest')}")
    return 0


SEED = {"asof": "2026-11-07",
        "source": "T-OPSIG (تشغيلة 42397087578 · fm_forensics/opsig/T_OPSIG_RESULT.md §④) — بذرةٌ حتى أوّل تحديثٍ أسبوعيّ من سجلّ الحصاد",
        "normal": {"n": 1436, "maxg_med": 8.5, "p20": 27.1, "cat": 12.8, "s10_med": -10.0},
        "gold": {"n": 125, "maxg_med": 18.5, "p20": 45.6, "cat": 36.0, "s10_med": -10.0}}


def _seed_of(cur):
    """بعد النشر من الحصاد لا تعود البذرةُ أبدًا إلّا إن نقص المحصود (لا ينقص السجلُّ الإلحاقيّ) — احتياطٌ بالبذرة الأصليّة بحرفها."""
    return dict(SEED, defs=cur.get("defs"))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    mode = argv[0] if argv else "stats"
    if mode == "refresh":
        key = (os.environ.get("POLYGON_API_KEY") or "").strip()
        if not key:
            log("⛔ بلا مفتاح Polygon — لا تحديث (البذرةُ باقية)")
            return 3
        cap = int(os.environ.get("OE_STATS_CAP") or 0) or None
        return mode_refresh(key, cap)
    return mode_stats()


if __name__ == "__main__":
    sys.exit(main())
