#!/usr/bin/env python3
"""📐 `T-COUNT` — «قس عدد الصفقات» (العقد: `count_prereg.md`، مدفوعٌ قبل هذا الملفّ).

**السؤال:** تفوّقُ المُرتِّب العشوائيّ على مُرتِّب الإنتاج في `T-RANK-DENSE` —
أثرُ **عددِ الصفقات** (توقّعٌ سالبٌ ⇒ مَن يتداول أقلَّ يخسر أقلّ) أم أثرُ
**جودةِ اختيار**؟

🔒 **صفرُ مسٍّ بالإنتاج:** لا تُستورَد `Super_stock` إطلاقًا، و`replay10` تُقرأ
ولا تُعدَّل. **والمجتمعُ هو هو حرفيًّا** — صفوفُ `ranker_rows.jsonl` المرفوعةُ
من تشغيلات `T-RANK-DENSE` نفسِها، فالمتغيّرُ الوحيدُ `capacity`.

بحث/قياسٌ فقط · يدويٌّ بلا كرون · سقفُ النجاح جوابٌ وتقرير (‏§⑦).
"""
from __future__ import annotations

import json
import os
import statistics
import sys

import replay10 as RP

# ── ثوابتُ العقد (‏§③) — مثبَّتةٌ سلفًا ولا تُغيَّر بعد الأرقام ──────────────
CAPS = (15, 12, 10, 8, 6, 4, 3, 2, 1)   # §③ سلّمُ السعة
N_SEEDS = 200                            # §③ العشوائيّ
LIVE_CAP = 15                            # `WATCHLIST_SIZE` الحيّ

# `CV1`: عددُ صفوف كلّ سنةٍ كما نُشر في `ranker_dense_result §①`
ROWS_EXPECTED = {"2023": 21257, "2024": 21745, "2025": 21470}

# `CV0`: أرقامُ `Q0` المنشورة الأربعة — تُعاد بت-بت أو خروج 3
Q0_PUBLISHED = {
    "2023": {"net_r_day": -0.2800, "taken": 473, "expl": 119, "cap": 15862},
    "2024": {"net_r_day": -0.2463, "taken": 450, "expl": 145, "cap": 16280},
    "2025": {"net_r_day": -0.1741, "taken": 406, "expl": 112, "cap": 17135},
}

ROWS_FILE = "ranker_rows.jsonl"


def _log(m: str) -> None:
    print(m, flush=True)


def load_rows(path: str) -> list[dict]:
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def cell(cands, outcome_of, sessions, ranker, capacity) -> dict:
    """خليّةُ (مُرتِّب، سعة) — `replay10.replay` بالاسم بلا تعديلِ حرف."""
    out = RP.replay(cands, outcome_of=outcome_of, ranker=ranker,
                    capacity=capacity, sessions=sessions)
    tk = out["taken"]
    return {"net_r_day": RP.net_r_per_day(tk, len(sessions)),
            "taken": len(tk),
            "expl": sum(1 for c in tk if (c.payload or {}).get("exploded")),
            "cap": out["rejected_cap"],
            "slot_days": out["slot_days"]}


def random_cell(cands, outcome_of, sessions, capacity) -> dict:
    """العشوائيُّ **وسيطُ** ‏200 بذرة — و`taken` يُسجَّل وسيطًا كذلك (‏§⑧-3:
    قد لا تكون بذرةُ وسيطِ `R` هي بذرةَ وسيطِ `taken`، فيُطبَع المدى)."""
    rs, tk, ex = [], [], []
    for s in range(N_SEEDS):
        c = cell(cands, outcome_of, sessions, RP.make_rank_random(s), capacity)
        rs.append(c["net_r_day"])
        tk.append(c["taken"])
        ex.append(c["expl"])
    return {"net_r_day": statistics.median(rs),
            "taken": statistics.median(tk),
            "expl": statistics.median(ex),
            "taken_lo": min(tk), "taken_hi": max(tk),
            "r_lo": min(rs), "r_hi": max(rs),
            "cap": None, "slot_days": None}


def interp_at(curve: list[tuple[float, float]], x: float):
    """استيفاءٌ خطّيٌّ لـ`net_r_day` عند `taken = x` (‏§④-3).

    `curve` أزواجُ (‏taken، net_r_day) مرتَّبةٌ تصاعديًّا بـ`taken`.
    يُرجع `None` إن وقع `x` **خارج** المدى — فالاستقراءُ ممنوعٌ بنصّ `CV4`."""
    if not curve or x < curve[0][0] or x > curve[-1][0]:
        return None
    for i in range(1, len(curve)):
        x0, y0 = curve[i - 1]
        x1, y1 = curve[i]
        if x0 <= x <= x1:
            if x1 == x0:
                return y0
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return None


def _monotone_ok(vals: list[int]) -> bool:
    """`CV2`: `taken` غيرُ متناقصٍ مع ارتفاع السعة."""
    return all(a <= b for a, b in zip(vals, vals[1:]))


def report(year: str, rows: list[dict]) -> int:
    """0 حكم · 3 عطبُ أداة · 5 لا تفكيك (السؤالُ منتفٍ أو استقراء)."""
    _log(f"\n📐 T-COUNT · سنة {year} · صفوف {len(rows)}")

    exp = ROWS_EXPECTED.get(year)
    if exp is not None and len(rows) != exp:                       # `CV1`
        _log(f"   ⛔ `CV1` عددُ الصفوف {len(rows)} لا يطابق المنشور {exp}")
        return 3

    dates = sorted({str(t["date"]) for t in rows})
    cands, idx, outcome_of = RP.candidates_from_trades(rows, extra_dates=dates)
    sessions = sorted(set(idx.values()))
    _log(f"   📊 الجلسات {len(sessions)} · المرشّحون {len(cands)}")

    arms = {"L": RP.rank_live, "F": RP.rank_fifo}
    grid: dict[str, dict[int, dict]] = {"L": {}, "R": {}, "F": {}}
    for cp in sorted(CAPS):
        for name, rk in arms.items():
            grid[name][cp] = cell(cands, outcome_of, sessions, rk, cp)
        grid["R"][cp] = random_cell(cands, outcome_of, sessions, cp)

    # ── `CV0` — إعادةُ أرقام `Q0` المنشورة بت-بت ────────────────────────────
    pub = Q0_PUBLISHED.get(year)
    got = grid["L"][LIVE_CAP]
    if pub is not None:
        bad = []
        if round(got["net_r_day"], 4) != pub["net_r_day"]:
            bad.append(f"net_r_day {round(got['net_r_day'],4)} ≠ {pub['net_r_day']}")
        for k in ("taken", "expl", "cap"):
            if got[k] != pub[k]:
                bad.append(f"{k} {got[k]} ≠ {pub[k]}")
        if bad:
            _log(f"   ⛔ `CV0` تفرّقٌ عن `Q0` المنشورة — {'; '.join(bad)}")
            return 3
        _log("   ✅ `CV0` أعاد أرقامَ `Q0` المنشورة الأربعة بت-بت")

    # ── `CV2` — الرتابة ────────────────────────────────────────────────────
    for name in ("L", "R", "F"):
        tk = [grid[name][c]["taken"] for c in sorted(CAPS)]
        if not _monotone_ok(tk):
            _log(f"   ⛔ `CV2` `taken` غيرُ رتيبٍ للمُرتِّب {name}: {tk}")
            return 3
    _log("   ✅ `CV2` `taken` رتيبٌ في الثلاثة")

    # ── حارسُ العلم الميّت (‏§⑤) ────────────────────────────────────────────
    if len({grid["L"][c]["taken"] for c in CAPS}) == 1:
        _log("   ⛔ سلّمُ السعة بلا أثرٍ إطلاقًا ⇒ بصمةُ `no-op` — يُعلَن ولا يُفسَّر")
        return 3

    _log("   ┌─ سلّمُ السعة (صافي R لليوم · مأخوذ · منفجرٌ مُسلَّم) ──────────")
    for cp in sorted(CAPS, reverse=True):
        pieces = []
        for name in ("L", "R", "F"):
            g = grid[name][cp]
            pieces.append(f"{name} {g['net_r_day']:+.4f}/{int(g['taken'])}/{int(g['expl'])}")
        _log(f"   │ سعة {cp:>2}: " + " · ".join(pieces))
    _log("   └──────────────────────────────────────────────────────────")
    r15 = grid["R"][LIVE_CAP]
    _log(f"   🎲 العشوائيُّ عند 15: مأخوذ وسيطًا {int(r15['taken'])} "
         f"(المدى {r15['taken_lo']}-{r15['taken_hi']}) · "
         f"R وسيطًا {r15['net_r_day']:+.4f} (المدى {r15['r_lo']:+.4f}..{r15['r_hi']:+.4f})")

    # ── التفكيك (‏§④) ──────────────────────────────────────────────────────
    t_l = float(grid["L"][LIVE_CAP]["taken"])
    t_r = float(r15["taken"])
    d_raw = r15["net_r_day"] - grid["L"][LIVE_CAP]["net_r_day"]
    _log(f"   📐 T_L={int(t_l)} · T_R={int(t_r)} · Δ_raw={d_raw:+.4f}")

    if d_raw <= 0:                                                  # §④ ذيل
        _log("   ⚠️ `Δ_raw` غيرُ موجب ⇒ السنةُ **غيرُ قابلةٍ للتفكيك** ولا "
             "يُحسَب لها `share_count`")
        print(f"COUNT {json.dumps({'year': year, 'grid': grid, 'share_count': None, 'reason': 'delta_raw_not_positive'}, ensure_ascii=False, default=float)}")
        return 5
    if t_r >= t_l:                                                  # `CV3`
        _log(f"   ⛔ `CV3` العشوائيُّ لا يتداول أقلَّ ({int(t_r)} مقابل {int(t_l)}) "
             "⇒ الأفضليّةُ **ليست عددًا** — السؤالُ منتفٍ ويُعلَن")
        print(f"COUNT {json.dumps({'year': year, 'grid': grid, 'share_count': None, 'reason': 'cv3_random_not_fewer'}, ensure_ascii=False, default=float)}")
        return 5

    curve = sorted((float(grid["L"][c]["taken"]), grid["L"][c]["net_r_day"]) for c in CAPS)
    l_star = interp_at(curve, t_r)
    if l_star is None:                                              # `CV4`
        _log(f"   ⛔ `CV4` `T_R`={int(t_r)} خارجَ مدى `taken` لسلّم `L` "
             f"({int(curve[0][0])}-{int(curve[-1][0])}) ⇒ استقراءٌ ممنوع")
        print(f"COUNT {json.dumps({'year': year, 'grid': grid, 'share_count': None, 'reason': 'cv4_extrapolation'}, ensure_ascii=False, default=float)}")
        return 5

    d_matched = r15["net_r_day"] - l_star
    share = 1.0 - d_matched / d_raw
    _log(f"   📐 `L*` عند نفس العدد = {l_star:+.4f} · Δ_matched={d_matched:+.4f}")
    _log(f"   🎯 **share_count = {share:.3f}**")
    print(f"COUNT {json.dumps({'year': year, 'grid': grid, 'T_L': t_l, 'T_R': t_r, 'd_raw': d_raw, 'l_star': l_star, 'd_matched': d_matched, 'share_count': share}, ensure_ascii=False, default=float)}")
    return 0


def main() -> int:
    year = str(os.environ.get("BACKTEST_YEAR", "")).strip()
    path = os.environ.get("COUNT_ROWS_PATH", ROWS_FILE)
    if not year:
        _log("⛔ `BACKTEST_YEAR` غيرُ مضبوط")
        return 2
    if not os.path.exists(path):
        _log(f"⛔ ملفُّ الصفوف غيرُ موجود: {path}")
        return 2
    return report(year, load_rows(path))


if __name__ == "__main__":
    sys.exit(main())
