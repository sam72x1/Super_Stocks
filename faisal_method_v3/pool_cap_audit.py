# -*- coding: utf-8 -*-
"""
🗜️ تدقيقُ سقف بِركة رادار الضغط (قراءةٌ فقط · المعاييرُ في pressure_pool_cap_audit.md §⓪ مكتوبةٌ قبل الرقم).

  --rebuild   (محلّيًّا · يلزمه تاريخُ git الكامل): يعيد بناءَ بِرك الجلسات A/B/C ⟵ data/pool_sessions.json
  (بلا وسيط)  (Actions · TradingView): يقرأ data/pool_sessions.json ⟵ press_read لكلّ رمزٍ وجلسة ⟵ out/pool_cap_audit.json

لا يمسّ `POOL_CAP` ولا `build_pool` ولا حالةَ الرادار — نسخةٌ عميقةٌ لكلّ لقطة.
"""
import copy
import datetime as dt
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
SESS_FILE = os.path.join(HERE, "data", "pool_sessions.json")
SINCE = "2026-08-14"                  # §⓪: أوّلُ لقطةٍ بالشكل المعتمد


def _git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def _show(rev, path):
    try:
        return json.loads(_git("show", f"{rev}:{path}"))
    except Exception:                                                    # noqa: BLE001
        return None


def ordered_candidates(wl: dict, state: dict, today: str):
    """نسخةٌ من ترتيب `build_pool` **بلا سقف** مع مصدر كلّ رمز وتاريخ حدثه — للأذرع الثلاث. (لا تُعدِّل الحالة الأصليّة.)"""
    import press_radar as PR
    mem = copy.deepcopy(state).setdefault("symbols", {})
    order, meta = [], {}

    def add(sym, src, d=None):
        sym = str(sym or "").upper()
        if sym and sym not in meta:
            order.append(sym)
            meta[sym] = {"src": src, "date": d}
    for it in wl.get("pullback") or []:
        add(it.get("symbol"), "pullback")
    for it in wl.get("stocks") or []:
        add(it.get("symbol"), "stocks")
    for it in wl.get("removed") or []:
        d = it.get("date") or it.get("removed_at")
        g = PR._days_between(d, today) if d else None
        if g is not None and g <= PR.MEMORY_DAYS:
            add(it.get("symbol"), "removed", d)
    for it in wl.get("explosions") or []:
        d = it.get("date")
        g = PR._days_between(d, today) if d else None
        if g is not None and g <= PR.MEMORY_DAYS:
            add(it.get("symbol"), "mover", d)
    for sym, e in list(mem.items()):
        gap = PR._days_between(e.get("last_seen") or e.get("first_seen"), today)
        if not (gap is not None and gap > PR.MEMORY_DAYS):
            add(sym, "memory", e.get("last_seen") or e.get("first_seen"))
    return order, meta


def arms(wl, state, today):
    import press_radar as PR
    B, meta = ordered_candidates(wl, state, today)
    A, cut = PR.build_pool(copy.deepcopy(wl), copy.deepcopy(state), today)
    assert A == B[:PR.POOL_CAP], "ترتيبُ النسخة يخالف build_pool"      # حارس: النسخةُ تطابق الإنتاج حرفًا
    first = [s for s in B if meta[s]["src"] in ("pullback", "stocks")]
    movers = sorted([s for s in B if meta[s]["src"] == "mover"], key=lambda s: str(meta[s]["date"] or ""), reverse=True)
    rest = [s for s in B if meta[s]["src"] == "removed"] + [s for s in B if meta[s]["src"] == "memory"]
    C = (first + movers + rest)[:PR.POOL_CAP]
    return {"A": A, "B": B, "C": C, "cut": cut, "meta": meta}


def rebuild():
    revs = _git("log", "--reverse", "--format=%H %aI", "origin/main", "--", "press_radar_state.json").split("\n")
    revs = [r.split() for r in revs if r.strip()]
    out, seen = [], set()
    for (prev, _pd), (cur, cd) in zip(revs, revs[1:]):
        if cd[:10] < SINCE:
            continue
        st_cur = _show(cur, "press_radar_state.json") or {}
        sess = st_cur.get("last_session")
        if not isinstance(sess, str) or sess in seen:
            continue
        wl = _show(prev, "weekly_watchlist.json")
        st = _show(prev, "press_radar_state.json")
        if wl is None or st is None:
            continue
        a = arms(wl, st, sess)
        seen.add(sess)
        srcs = {}
        for s in a["B"][len(a["A"]):]:
            k = a["meta"][s]["src"]
            srcs[k] = srcs.get(k, 0) + 1
        out.append({"session": sess, "rev_prev": prev[:12], "rev_cur": cur[:12], "n_B": len(a["B"]), "n_A": len(a["A"]),
                    "cut": a["cut"], "cut_by_src": srcs,
                    "C_minus_A": sorted(set(a["C"]) - set(a["A"])), "A_minus_C": sorted(set(a["A"]) - set(a["C"])),
                    "A": a["A"], "B": a["B"], "C": a["C"],
                    "src": {s: a["meta"][s]["src"] for s in a["B"]}})
        print(f"{sess}: B {len(a['B'])} · A {len(a['A'])} · قُصّ {a['cut']} {srcs} · C≠A {len(out[-1]['C_minus_A'])}")
    json.dump({"generated": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", "since": SINCE, "sessions": out},
              open(SESS_FILE, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"جلسات {len(out)} ⟵ {SESS_FILE}")
    return 0


def classify(tot: dict, n_sessions: int, coverage: float) -> str:
    """§⓪ حرفًا."""
    if coverage < 0.90 or n_sessions < 10:
        return "UNKNOWN"
    lost, ready_B = tot["ready_lost_A"], tot["ready_B"]
    if lost >= 3 or (ready_B and lost / ready_B >= 0.05):
        return "MATERIAL"
    return "LOW"


def evaluate():
    import press_radar as PR
    import Super_stock as S
    sess = json.load(open(SESS_FILE, encoding="utf-8"))["sessions"]
    syms = sorted({s for x in sess for s in x["B"]})
    frames, rep = S.tv_download(syms, "2025-06-01")
    cov = len(frames) / max(1, len(syms))
    print(f"📥 رموز B الفريدة {len(syms)} · شموعٌ لـ{len(frames)} ({cov:.1%})")
    rows, tot = [], {"hits_B": 0, "hits_lost_A": 0, "ready_B": 0, "ready_lost_A": 0, "ready_lost_C": 0, "ready_recovered_by_C": 0}
    lost_names = []
    for x in sess:
        d = x["session"]
        A, C = set(x["A"]), set(x["C"])
        r_hit, r_ready = [], []
        for s in x["B"]:
            df = frames.get(s)
            if df is None:
                continue
            dd = df[[str(i)[:10] <= d for i in df.index]]
            if len(dd) < PR.ALERT_W + 5:
                continue
            r = PR.press_read(dd, w=PR.ALERT_W)
            if not r:
                continue
            r_hit.append(s)
            if int(r.get("hold_sessions") or 0) >= PR.READY_HOLD:
                r_ready.append(s)
        lostA = [s for s in r_ready if s not in A]
        lostC = [s for s in r_ready if s not in C]
        tot["hits_B"] += len(r_hit)
        tot["hits_lost_A"] += sum(1 for s in r_hit if s not in A)
        tot["ready_B"] += len(r_ready)
        tot["ready_lost_A"] += len(lostA)
        tot["ready_lost_C"] += len(lostC)
        tot["ready_recovered_by_C"] += sum(1 for s in lostA if s in C)
        lost_names += [(d, s, x["src"].get(s)) for s in lostA]
        rows.append({"session": d, "n_B": x["n_B"], "cut": x["cut"], "hits_B": len(r_hit), "ready_B": len(r_ready),
                     "ready_lost_A": lostA, "ready_lost_C": lostC})
        print(f"{d}: B {x['n_B']} · قُصّ {x['cut']} · مطابق {len(r_hit)} · جاهز {len(r_ready)} · مفقودٌ بالسقف {lostA} · C يفقد {lostC}")
    verdict = classify(tot, len(rows), cov)
    out = {"sessions": len(rows), "coverage": round(cov, 4), "totals": tot, "verdict": verdict, "lost_A": lost_names,
           "rows": rows, "fetch_report": {k: (v if not isinstance(v, list) else len(v)) for k, v in (rep or {}).items()}}
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, "out", "pool_cap_audit.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print(f"🏁 {verdict} · {json.dumps(tot, ensure_ascii=False)}")
    return 0


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    return rebuild() if "--rebuild" in a else evaluate()


if __name__ == "__main__":
    raise SystemExit(main())
