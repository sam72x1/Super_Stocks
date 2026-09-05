#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🌅📡 `T-PM-RADAR` — رادارُ البريماركت على السوق كلِّه (أداةُ قياسٍ تاريخيّ).

العقد: `premarket_radar_prereg.md` — **مدفوعٌ قبل هذا الملفّ وقبل أيّ رقم**، ولا
معيارَ يُحرَّك بعده. أمرُ المالك «ابنِ رادار البري» (2026-09-05) بعد ثقب `ANPA`:
سهمٌ **خارجَ قوائمنا** يتحرّك في البريماركت لا تراه أيُّ قناة.

⚖️ **مقياسٌ واحدٌ لا اثنان:** كشفُ المِرساة بدالّة الإنتاج `Super_stock.liq_stage_events`
**بالاسم** عبر `kasih_scan.first_anchor` (النمطُ القانونيّ) — وبوّاباتُ المالك
(‏5% · $30,000 · 3×) تُقرأ من الإنتاج ولا تُمَسّ. الرادارُ **لا يضيف عتبةً ولا يُرخيها**:
المرشِّحُ الرخيص يستعمل `LIQ_MIN_USD` **نفسَها** على سيولة آخر دقيقةٍ مغلقة.

🔒 **قراءةٌ/قياسٌ فقط:** لا كتابةَ حالةٍ ولا تلغرام ولا مساسَ بأيّ عتبة.

الكونان:
- `R0` = قوائمُنا (كونُ `scan_liq_stages` الحيّ) — يُعاد بناؤه **من تاريخ
  `op_entry_state.json` المدفوع** (مفاتيحُ `LIQ:` التي تحمل تاريخَ اليوم = ما مسحه
  العاملُ فعلًا)، ومعه المِرساةُ الحيّةُ المسجَّلة (لفحص `V0-ب`).
- الرادار = بقيّةُ السوق داخل [`MIN_PRICE`، `SPLIT_RADAR_PRICE_MAX`] بإغلاق الأمس؛
  يصير الرمزُ مرشَّحًا عند أوّل دقيقةٍ مغلقةٍ سيولتُها ‏≥ `LIQ_MIN_USD`، ثم تُعاد
  `liq_stage_events` على شموعه **من الدورة التالية** (لا نظرَ مستقبليّ).

المخرَج: `pm_radar_rows.jsonl` (سطر/رمز-يوم للمتحرّكين والمراسي) + جدولُ الأذرع
بالمعايير الأربعة + فحوصُ `V0` — وخروجٌ 3 عند سقوط بوّابة صلاحية (لا يُقرأ رقم).
"""
import csv
import gzip
import json
import os
import statistics
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SCREENER_MODE", "BACKTEST")

import datetime as dt                                            # noqa: E402

import ah_scan as AH                                             # noqa: E402
import kasih_scan as KS                                          # noqa: E402
import Super_stock as S                                          # noqa: E402

NY = KS.NY
PRE_START = 4 * 60            # 04:00 نيويورك — بدءُ البريماركت
PRE_END = 9 * 60 + 30         # 09:30 — الافتتاح (حدُّ النافذة، حصرًا)
MOVER_PCT = 30.0              # faisal_verbatim «‏30%» (العقد §⑤)
MOVER_USD = float(S.CONFIG.get("IGNITION_USD_OPERATOR", 100_000))   # مُعاد
PRICE_LO = float(S.CONFIG.get("MIN_PRICE", 1.65))
PRICE_HI = float(S.CONFIG.get("SPLIT_RADAR_PRICE_MAX", 10.0))
USD_FLOOR = float(S.LIQ_MIN_USD)              # أرضيةُ المالك — المرشِّحُ نفسُه
MOVE_PCT = float(S.LIQ_MIN_MOVE_PCT)          # 5% — `R2` بدلالةٍ يوميّة (engineering)
DEFAULT_FROM, DEFAULT_TO = "2026-08-17", "2026-09-04"   # 14 جلسة (العقد §⑤)
MIN_MOVERS = 20               # أرضيةُ الحكم (العقد §⑤)
CAPTURE_MIN, COST_MAX, DELAY_MAX = 70.0, 3.0, 5.0        # المعايير 1-3
# شاهدُ الضبط `V0-ب`: المِرساةُ الحيّةُ المسجَّلة يجب أن تُعاد بالدقيقة نفسها
CONTROL = {"ANPA": "2026-09-04"}
# تشخيصٌ مُسمًّى (بلا معيار): `BTOG` حصل على `M1` يوم 09-03 وهو في قوائمنا، وسُمّي
# `SGRX` بعدها — يُقرأ ما تراه الأداة عنهما (أمرُ المالك 2026-09-05)
DIAG = {"BTOG": ("2026-09-03", "2026-09-04"), "SGRX": ("2026-09-04",)}
STATE_FILE = "op_entry_state.json"


def log(msg: str):
    print(msg, flush=True)


# ── قراءةُ ملفّ اليوم: شموعُ البريماركت لكلّ السوق + إغلاقاتُ الجميع ──────────
def parse_pre(fh, prev_close: dict, want_all: bool):
    """`bars[sym]` = شموعُ 04:00-09:30 لمن إغلاقُ أمسِه داخل النطاق (أو الكلّ عند
    `want_all` — يومُ البذرة يحتاج الإغلاقاتِ فقط). `closes` = إغلاقُ الجلسة
    النظاميّة (‏≤16:00) للجميع = «إغلاقُ الأمس» ليوم الغد."""
    rd = csv.reader(fh)
    header = next(rd)
    i_t = AH._pick(header, "ticker", "symbol")
    i_o, i_h = AH._pick(header, "open"), AH._pick(header, "high")
    i_l, i_c = AH._pick(header, "low"), AH._pick(header, "close")
    i_v = AH._pick(header, "volume")
    i_w = AH._pick(header, "window_start", "t", "timestamp")
    if min(i_t, i_o, i_h, i_l, i_c, i_v, i_w) < 0:
        raise KeyError(f"ترويسةٌ ناقصة: {header}")
    bars, closes = {}, {}
    for row in rd:
        try:
            sym = row[i_t].strip().upper()
            ns = int(row[i_w])
            o, h = float(row[i_o]), float(row[i_h])
            lo, c, v = float(row[i_l]), float(row[i_c]), float(row[i_v])
        except (IndexError, ValueError, TypeError):
            continue
        if not sym:
            continue
        day, mod = AH.ny_minute(ns)
        if day is None:
            continue
        if mod <= 16 * 60:
            pc = closes.get(sym)
            if pc is None or mod > pc[0]:
                closes[sym] = (mod, c)
        if want_all or not (PRE_START <= mod < PRE_END):
            continue
        pc = prev_close.get(sym)
        if pc is None or not (PRICE_LO <= pc <= PRICE_HI):
            continue
        bars.setdefault(sym, []).append((int(ns / 1e6), o, h, lo, c, v))
    for b in bars.values():
        b.sort(key=lambda x: x[0])
    return bars, {k: v[1] for k, v in closes.items()}


# ── الدوالُّ النقيّة (مقفولةٌ في السويّة) ─────────────────────────────────────
def mover_t30(rows, prev_close: float, pct: float = MOVER_PCT,
              usd_floor: float = MOVER_USD):
    """«المتحرّك» (العقد §⑤): أعلى دقيقةٍ ‏≥ `prev_close × (1+pct/100)` داخل
    النافذة **وسيولةٌ تراكميّةٌ** ‏≥ `usd_floor` حتى نهايتها. يُرجع طابعَ أوّل
    دقيقةٍ بلغت الحدَّ، أو `None`."""
    if not prev_close or prev_close <= 0:
        return None
    if sum(b[4] * b[5] for b in rows) < usd_floor:
        return None
    lvl = prev_close * (1.0 + pct / 100.0)
    for b in rows:
        if b[2] >= lvl:
            return b[0]
    return None


def candidate_index(rows, usd_floor: float = USD_FLOOR, prev_close=None,
                    min_up_pct=None):
    """فهرسُ أوّل دقيقةٍ مغلقةٍ سيولتُها `c×v ≥ usd_floor` (مرشِّحُ اللقطة — العقد
    §②-1). مع `min_up_pct` (‏`R2`) يُشترَط أيضًا إغلاقُها ‏≥ إغلاق الأمس ×(1+pct).
    `None` = لا يصير مرشَّحًا في هذا اليوم."""
    for i, b in enumerate(rows):
        if b[4] * b[5] < usd_floor:
            continue
        if min_up_pct is not None:
            if not prev_close or b[4] < prev_close * (1.0 + min_up_pct / 100.0):
                continue
        return i
    return None


def replay_anchor(rows, start_k: int = 3):
    """المِرساةُ بدالّة الإنتاج — إعادةُ التشغيل التدريجيّ (نمطُ `first_anchor`)
    بدءًا من الشريحة `k = start_k` ⇒ للرادار `start_k = i0 + 1`: أوّلُ دورةٍ بعد
    أن أظهرت اللقطةُ الدقيقةَ `i0` مغلقةً (لا نظرَ مستقبليّ). تُرجع `M1` أو `None`."""
    st: dict = {}
    win = int(S.LIQ_WINDOW_MIN)
    bd = KS._dicts(rows)
    for k in range(max(3, int(start_k)), len(bd) + 1):
        evs, st = S.liq_stage_events(bd[max(0, k - win):k], st)
        for e in (evs or []):
            if e.get("stage") == "M1":
                return e
    return None


def arm_anchor(sym, rows, in_lists: bool, prev_close, arm: str, near: set):
    """مِرساةُ ذراعٍ لرمزٍ في يوم. `R0`: قوائمُنا فقط (بت-بت مع الحيّ) · `R1`:
    ‏+ الرادار · `R2`: ‏+ رادارٌ بشرط صعودٍ يوميّ · `R3`: ‏+ رادارٌ مقصورٌ على
    `near_watch`. **`R1 ⊇ R0` بالبناء** (فرعُ القوائم واحدٌ في كلّ الأذرع)."""
    if in_lists:
        return replay_anchor(rows, 3)
    if arm == "R0":
        return None
    if arm == "R3" and sym not in near:
        return None
    i0 = candidate_index(rows, USD_FLOOR, prev_close,
                         MOVE_PCT if arm == "R2" else None)
    if i0 is None:
        return None
    return replay_anchor(rows, i0 + 1)


def wilson(k, n):
    return KS.wilson(k, n)


# ── كونُ القوائم لكلّ يوم من تاريخ الحالة المدفوعة ────────────────────────────
def _git_blobs(path: str, since: str, until: str):
    out = subprocess.run(
        ["git", "log", "--reverse", "--format=%H %cd", "--date=short",
         f"--since={since}", f"--until={until}", "--", path],
        capture_output=True, text=True).stdout.strip().split("\n")
    rows = [ln.split(" ", 1) for ln in out if ln.strip()]
    if not rows:
        return []
    inp = "\n".join(f"{h}:{path}" for h, _ in rows) + "\n"
    buf = subprocess.run(["git", "cat-file", "--batch"], input=inp.encode(),
                         capture_output=True).stdout
    pos, blobs = 0, []
    while pos < len(buf):
        nl = buf.index(b"\n", pos)
        hdr = buf[pos:nl].decode()
        if " missing" in hdr:
            pos = nl + 1
            blobs.append(None)
            continue
        size = int(hdr.split()[2])
        blobs.append(buf[nl + 1:nl + 1 + size])
        pos = nl + 1 + size + 1
    return [(d, b) for (_, d), b in zip(rows, blobs) if b]


def lists_universe(days: list) -> dict:
    """لكلّ يومٍ: `{sym: anchor_ms|None}` — الرموزُ التي حمل مفتاحُها `LIQ:` تاريخَ
    اليوم في أيّ لقطةِ حالةٍ مدفوعة (= ما مسحه العاملُ فعلًا)، والمِرساةُ الحيّةُ
    المسجَّلة (‏`anchor_ms` أو `rearm_prev.anchor_ms` للأولى) إن وُجدت."""
    if not days:
        return {}
    d0 = (dt.date.fromisoformat(min(days)) - dt.timedelta(days=1)).isoformat()
    d1 = (dt.date.fromisoformat(max(days)) + dt.timedelta(days=2)).isoformat()
    out = {d: {} for d in days}
    for _, blob in _git_blobs(STATE_FILE, d0, d1):
        try:
            st = json.loads(blob)
        except Exception:                                        # noqa: BLE001
            continue
        for k, v in st.items():
            if not (isinstance(k, str) and k.startswith("LIQ:")
                    and isinstance(v, dict)):
                continue
            day = v.get("date")
            if day not in out:
                continue
            sym = k[4:]
            am = (v.get("rearm_prev") or {}).get("anchor_ms") or v.get("anchor_ms")
            cur = out[day].get(sym)
            out[day][sym] = am if am else cur
    return out


def near_watch_symbols(day: str) -> set:
    blobs = _git_blobs("near_watch.json", day,
                       (dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat())
    for _, b in reversed(blobs):
        try:
            d = json.loads(b)
            return {str(k).upper() for k in (d if isinstance(d, dict) else {})}
        except Exception:                                        # noqa: BLE001
            continue
    return set()


# ── التقرير ─────────────────────────────────────────────────────────────────
def summarize(rows: list, days: list, live_anchor: dict) -> dict:
    """يحسب المعاييرَ الأربعة لكلّ ذراعٍ من صفوف (رمز، يوم). نقيّة."""
    arms = ("R0", "R1", "R2", "R3")
    movers = [r for r in rows if r.get("t30")]
    res = {"n_movers": len(movers), "n_days": len(days), "arms": {}}
    for a in arms:
        cap = sum(1 for r in movers if r["anchor"].get(a)
                  and r["anchor"][a] < r["t30"])
        per_day = {d: 0 for d in days}
        ups = []
        for r in rows:
            am = r["anchor"].get(a)
            if am:
                per_day[r["day"]] = per_day.get(r["day"], 0) + 1
                if r.get("prev_close") and r.get("anchor_price", {}).get(a):
                    ups.append((r["anchor_price"][a] / r["prev_close"] - 1) * 100)
        msgs = sorted(per_day.values())
        res["arms"][a] = {
            "captured": cap,
            "capture_pct": round(100.0 * cap / len(movers), 1) if movers else None,
            "m1_median": statistics.median(msgs) if msgs else 0,
            "m1_total": sum(msgs),
            "delay_median": round(statistics.median(ups), 1) if ups else None,
        }
    # المعيار 4: `R1 ⊇ R0` بالدقيقة نفسِها (عطبُ أداةٍ لا نتيجة)
    res["r1_superset"] = all(
        (r["anchor"].get("R0") is None) or r["anchor"].get("R1") == r["anchor"]["R0"]
        for r in rows)
    # `V0-ب`: تكافؤُ المِرساة الحيّة مع الإعادة على الرموز المشتركة
    agree = total = 0
    for r in rows:
        la = live_anchor.get((r["day"], r["symbol"]))
        sa = r["anchor"].get("R0")
        if la and sa:
            total += 1
            agree += int(la == sa)
    res["live_agree"] = (agree, total)
    return res


def verdict(res: dict) -> list:
    """قراءةُ المعايير الأربعة على `R1` (الحاكمة) — تُرجع قائمةَ (اسم، ✅/🔴/⏸️)."""
    r0, r1 = res["arms"]["R0"], res["arms"]["R1"]
    if res["n_movers"] < MIN_MOVERS:
        return [("الأرضية", f"⏸️ {res['n_movers']} < {MIN_MOVERS} ⇒ لا حكم")]
    out = []
    c1 = (r1["capture_pct"] or 0) >= CAPTURE_MIN
    out.append(("① الالتقاط ≥70%", f"{'✅' if c1 else '🔴'} {r1['capture_pct']}%"))
    base = max(1.0, float(r0["m1_median"]))
    ratio = r1["m1_median"] / base
    out.append(("② الكلفة ≤3×", f"{'✅' if ratio <= COST_MAX else '🔴'} ×{ratio:.2f}"))
    d0, d1 = r0["delay_median"], r1["delay_median"]
    ok3 = d0 is not None and d1 is not None and d1 - d0 <= DELAY_MAX
    out.append(("③ التأخّر لا يسوء", f"{'✅' if ok3 else '🔴'} {d0} ⟶ {d1}"))
    out.append(("④ R1 ⊇ R0", "✅" if res["r1_superset"] else "🔴 عطبُ أداة"))
    return out


def main() -> int:
    if not (os.environ.get("AWS_ACCESS_KEY_ID") or "").strip():
        log("⛔ لا مفاتيح S3 — لا قياس (ولا يُخمَّن رقم).")
        return 2
    d_from = (os.environ.get("PMR_FROM") or DEFAULT_FROM).strip()
    d_to = (os.environ.get("PMR_TO") or DEFAULT_TO).strip()
    days = KS.weekdays(d_from, d_to)
    seed = KS.weekdays((dt.date.fromisoformat(d_from) - dt.timedelta(days=7)).isoformat(),
                       (dt.date.fromisoformat(d_from) - dt.timedelta(days=1)).isoformat())[-3:]
    log(f"🌅📡 T-PM-RADAR — {d_from} ⟶ {d_to} · {len(days)} يوم أسبوع · كون "
        f"[{PRICE_LO}, {PRICE_HI}]$ · مرشِّح الرادار: سيولةُ آخر دقيقة ≥ ${USD_FLOOR:,.0f} "
        f"(= LIQ_MIN_USD) · متحرّك: +{MOVER_PCT}% وسيولة ≥ ${MOVER_USD:,.0f} · "
        f"بوّابات الإنتاج: رفعة {MOVE_PCT}% · قفزة {S.CONFIG['IGNITION_VOL_MULT']}×")
    lists = lists_universe(days)
    log("👁️ كونُ القوائم من تاريخ الحالة: " + " · ".join(
        f"{d}:{len(lists.get(d, {}))}" for d in days))
    live_anchor = {(d, s): am for d, m in lists.items() for s, am in m.items() if am}

    prev_close: dict = {}
    rows_out, n_files, n_missing = [], 0, 0
    fout = open("pm_radar_rows.jsonl", "w", encoding="utf-8")
    for di, day in enumerate(seed + days):
        seeding = di < len(seed)
        key = AH.day_key(day)
        mb, ep = AH.head_size_mb(key)
        if mb is None:
            n_missing += 0 if seeding else 1
            continue
        dest = f"/tmp/pmr-{day}.csv.gz"
        if not AH.download(key, dest, ep):
            n_missing += 0 if seeding else 1
            continue
        try:
            with gzip.open(dest, "rt") as fh:
                bars, closes = parse_pre(fh, prev_close, seeding)
        except (OSError, KeyError, ValueError) as e:
            log(f"   ⛔ {day}: تعذّرت القراءة ({type(e).__name__}: {e})")
            n_missing += 0 if seeding else 1
            continue
        finally:
            try:
                os.remove(dest)
            except OSError:
                pass
        if seeding:
            prev_close.update(closes)
            log(f"🌱 بذرة إغلاق الأمس من {day}: {len(closes):,} رمزًا")
            continue
        n_files += 1
        uni = lists.get(day, {})
        near = near_watch_symbols(day)
        n_cand = n_mov = 0
        for sym, rws in bars.items():
            pc = prev_close.get(sym)
            in_lists = sym in uni
            t30 = mover_t30(rws, pc)
            i0 = candidate_index(rws, USD_FLOOR)
            if not in_lists and i0 is None and t30 is None:
                continue
            n_cand += int(i0 is not None and not in_lists)
            n_mov += int(t30 is not None)
            anchors, aprice = {}, {}
            for a in ("R0", "R1", "R2", "R3"):
                e = arm_anchor(sym, rws, in_lists, pc, a, near)
                anchors[a] = int(e["anchor_ms"]) if e else None
                if e:
                    aprice[a] = float(e.get("anchor_price") or e.get("price") or 0)
            row = {"day": day, "symbol": sym, "in_lists": in_lists, "prev_close": pc,
                   "t30": t30, "cand_ms": rws[i0][0] if i0 is not None else None,
                   "anchor": anchors, "anchor_price": aprice,
                   "live_anchor": live_anchor.get((day, sym)),
                   "pre_usd": round(sum(b[4] * b[5] for b in rws))}
            rows_out.append(row)
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
        log(f"📅 {day}: رموز {len(bars):,} · قوائم {len(uni)} · مرشَّحو الرادار "
            f"{n_cand} · متحرّكون {n_mov}")
        prev_close.update(closes)
    fout.close()
    log(f"\n📦 ملفّات {n_files} · مفقود {n_missing} · صفوف {len(rows_out)}")
    if n_files == 0 or not rows_out:
        log("⛔ صفرُ صفوف — عطبُ أداةٍ لا نتيجة (خروج 4)")
        return 4
    rc = 0
    # V0-ب: شاهدُ الضبط بالدقيقة نفسِها
    for sym, day in CONTROL.items():
        r = next((x for x in rows_out if x["symbol"] == sym and x["day"] == day), None)
        la = live_anchor.get((day, sym))
        sa = r["anchor"].get("R0") if r else None
        ok = bool(r and la and sa == la)
        log(f"🧪 V0-ب {sym} {day}: حيّ={_hm(la)} · إعادة R0={_hm(sa)} · "
            f"R1={_hm(r['anchor'].get('R1')) if r else None} ⇒ {'✅' if ok else '🔴'}")
        if not ok:
            rc = 3
    for sym, dys in DIAG.items():
        for day in dys:
            r = next((x for x in rows_out if x["symbol"] == sym and x["day"] == day), None)
            if r is None:
                log(f"🔎 {sym} {day}: لا صفَّ (خارج النطاق السعريّ أو بلا شموعِ بري أو بلا مرشِّح)")
            else:
                log(f"🔎 {sym} {day}: قوائم={r['in_lists']} · إغلاق الأمس={r['prev_close']} · "
                    f"مرشَّح={_hm(r['cand_ms'])} · +30%={_hm(r['t30'])} · "
                    f"R0={_hm(r['anchor']['R0'])} · R1={_hm(r['anchor']['R1'])} · "
                    f"سيولة البري=${r['pre_usd']:,}")
    res = summarize(rows_out, days, live_anchor)
    ag, tot = res["live_agree"]
    log(f"\n🧪 V0-ب (عامّ): تكافؤُ المِرساة الحيّة مع الإعادة {ag}/{tot}")
    log(f"📊 المتحرّكون (+{MOVER_PCT}% وسيولة ≥${MOVER_USD:,.0f}): {res['n_movers']} "
        f"في {res['n_days']} جلسة")
    log(f"{'ذراع':<5}{'التقاط':>10}{'٪':>8}{'M1/جلسة وسيط':>16}{'M1 كلّ':>9}{'تأخّر وسيط٪':>14}")
    for a, v in res["arms"].items():
        log(f"{a:<5}{v['captured']:>10}{str(v['capture_pct']):>8}{v['m1_median']:>16}"
            f"{v['m1_total']:>9}{str(v['delay_median']):>14}")
    log("\n⚖️ الحكم على R1 (المعايير الأربعة تلزم معًا):")
    for name, val in verdict(res):
        log(f"   {name}: {val}")
    if not res["r1_superset"]:
        rc = 3
    log("\n⚠️ حدود: لمسٌ لا تنفيذ · 14 جلسة لا ثلاث سنوات · المرشِّحُ تقريبٌ لِما ستراه "
        "اللقطة · الرقيقُ دون MIN_PRICE خارج الكون · سقفُ النجاح اقتراحٌ للمالك.")
    return rc


def _hm(ms):
    if not ms:
        return None
    return dt.datetime.fromtimestamp(int(ms) / 1000, NY).strftime("%H:%M")


if __name__ == "__main__":
    sys.exit(main())
