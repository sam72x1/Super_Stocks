#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📒🌙 حصادُ قائمة ما قبل الجلسة — تقريرٌ يوميٌّ **بعد الافتر**.

أمرُ المالك (2026-09-03): «هذي أداة مهمة جدًّا ف ابي كل يوم بعد الافتر يوصلني
تقرير لها — الهدف منه تطويرها من جميع النواحي … يهمني جدااا **الجودة مب الكمية**».

⚖️ **ولماذا هي حصادٌ لا تجربة:** كلُّ ما نُشر عن هذي القناة (`topk_result.md`)
مقيسٌ **تاريخيًّا على سنةٍ واحدة خارج العيّنة**، والسجلُّ الأماميّ
(`presession_ledger.jsonl`) هو الشاهدُ الوحيد غيرُ الملوَّث — لكنه كان **يُكتَب
ولا يُقرأ**. هذي الأداةُ تقرؤه وتحسمه بوسم العقد نفسِه.

🔒 **مقياسٌ واحدٌ لا اثنان:** الحسمُ بـ`presession_scan.window_label` **بالاسم**
(‏نفسُ `HIT_PCT` ونفسُ `LABEL_MIN_USD` ونفسُ صيغة الأرضية) — ولو نُسخ المنطقُ هنا
لصار على القناة **رقمان**.

🔭 **ثلاثُ شرائحَ لا واحدة** (‏عقد `presession_dev_prereg §⑥`):
  🟢 **المُسلَّم** — ما وصل المالكَ فعلًا (`sent=True`).
  🎚️ **المقصوصُ بالأرضية** — داخل العشرة و`floor_ok=False`؛ **الشاهدُ المضادّ**
     الذي تُقاس به كلفةُ الأرضية أماميًّا. بلاه لا يُعرَف ما فاتنا.
  🔎 **دون العشرة** — `in_top=False`؛ شاهدُ **صحّةِ المفتاح نفسِه** («هل ينفجر
     مَن لم نرتّبه في العشرة؟»).

⚖️ **«لا حكم» إلزاميّ** حتى `MIN_DELIVERED` محسومًا مُسلَّمًا و`MIN_ROWS` صفًّا
محسومًا: تُطبَع الأعدادُ (حقائق) **ولا يُطبَع فرقٌ** بين الشرائح قبلها — سابقةُ
`T-TIE-FWD` حرفيًّا.

⚠️ **وحدُّ صدقٍ مطبوعٌ في التقرير:** الجلسةُ النظاميّة والنافذةُ الكاملة **وصفٌ
خارج العقد** (‏الوسمُ المسجَّل بريماركتُ اليوم وحدَه) — وحكمُها يلزمه `T-PREDAY`.

🔒 عرض/حصادٌ فقط: لا يمسّ فرزًا ولا حالةَ بوتٍ ولا عتبةً ولا `LOGIC_VERSION`.
التشغيل: `python3 presession_digest.py` (يلزم POLYGON_API_KEY + أسرار تلغرام).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import presession_feats as PF                                     # noqa: E402
import presession_radar as PR                                     # noqa: E402
import presession_scan as PS                                      # noqa: E402
import Super_stock as S                                           # noqa: E402

OUT_FILE = "presession_outcomes.jsonl"
STAMP_FILE = "presession_digest_stamp.json"
MIN_DELIVERED = 40        # أرضيةُ الحكم — المُسلَّمُ المحسوم (‏§⑥)
MIN_ROWS = 150            # أرضيةُ الحكم — كلُّ الصفوف المحسومة
MIN_COVERAGE_PCT = 60.0   # 🩺 أرضيةُ تغطية الحسم (أقلُّ منها = لم نحسم اليوم)
BACKLOG_DAYS = 30         # مدى استدراك الصفوف غير المحسومة
FETCH_CAP = 400           # سقفُ نداءات الدقائق للتشغيلة الواحدة — يُعلَن قصُّه
SHOW_BELOW = 5            # كم من «دون العشرة» يُعرَض (الباقي بعدده)


def _log(m: str) -> None:
    print(m, flush=True)


# ── دوالُّ نقيّة ───────────────────────────────────────────────────────────────
def row_key(r: dict) -> str:
    """مفتاحُ الصفّ — (يوم، جلسة، رمز). حتميٌّ فيصير الحسمُ idempotent."""
    return "{}|{}|{}".format(r.get(PF.ROW_DAY), r.get(PF.ROW_SESS),
                             str(r.get(PF.ROW_SYM) or "").upper())


def window_bounds(sess: str) -> tuple:
    """نافذةُ الوسم بدقائق نيويورك — **بريماركتُ اليوم** لقرار `PM`، وافترُه
    لقرار `AH`. (وهي عينُ ما وُسِم به تاريخيًّا: `hit80_s`.)"""
    if str(sess).strip().upper() == "PM":
        return PF.PRE_OPEN, PR.REG_OPEN
    return PR.REG_CLOSE, PF.EXT_CLOSE


def read_jsonl(path: str) -> list:
    """قارئٌ فاشلٌ-آمن — السطرُ التالف يُسقَط ولا يُسقط الملفّ."""
    out = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:                                # noqa: BLE001
                    continue
    except Exception:                                            # noqa: BLE001
        return out
    return out


def resolve_row(row: dict, bars8: list) -> dict | None:
    """يحسم صفًّا بوسم العقد نفسِه (`presession_scan.window_label`).

    ⚠️ **والوصفيُّ خارج العقد**: `reg`/`full` يُحسبان بنفس المرجع ويُعرَضان
    موسومَين — الحكمُ عليهما يلزمه `T-PREDAY` بتسجيلٍ مسبق.
    """
    try:
        ref = float(row.get("ref"))
    except (TypeError, ValueError):
        return None
    if not ref or ref <= 0 or not bars8:
        return None
    sess = str(row.get(PF.ROW_SESS) or "").strip().upper()
    st, en = window_bounds(sess)
    lab = PS.window_label(bars8, st, en, ref)
    if not lab.get("n"):
        return None
    reg = PS.window_label(bars8, PR.REG_OPEN, PR.REG_CLOSE, ref)
    full = PS.window_label(bars8, PF.PRE_OPEN, PR.REG_CLOSE, ref)
    return {"key": row_key(row), PF.ROW_DAY: row.get(PF.ROW_DAY),
            PF.ROW_SESS: sess, PF.ROW_SYM: str(row.get(PF.ROW_SYM) or "").upper(),
            "rank": row.get("rank"), "in_top": bool(row.get("in_top", True)),
            "sent": bool(row.get("sent")), "floor_ok": bool(row.get("floor_ok", True)),
            "ref": ref, "rank_val": row.get(PF.rank_key(sess)),
            "hit": int(lab.get("hit80") or 0), "max_pct": lab.get("max"),
            "win_usd": lab.get("usd"), "t80": lab.get("t80"),
            # 🔎 وصفيٌّ خارج العقد — لا يحكم:
            "reg_max": reg.get("max"), "reg_hit": int(reg.get("hit80") or 0),
            "full_max": full.get("max"), "full_hit": int(full.get("hit80") or 0)}


def day_bounds_ms(day_iso: str) -> tuple:
    """(بدايةُ 04:00 نيويورك، نهايةُ 20:00) بالملّي — تتصيّف ذاتيًّا."""
    from zoneinfo import ZoneInfo
    d = dt.date.fromisoformat(str(day_iso))
    ny = ZoneInfo("America/New_York")
    a = dt.datetime.combine(d, dt.time(0, 0), tzinfo=ny) + dt.timedelta(
        minutes=PF.PRE_OPEN)
    b = dt.datetime.combine(d, dt.time(0, 0), tzinfo=ny) + dt.timedelta(
        minutes=PF.EXT_CLOSE)
    return int(a.timestamp() * 1000), int(b.timestamp() * 1000)


def tally(rows: list) -> dict:
    """أعدادُ الشرائح الثلاث — حقائقُ عدٍّ لا حكم."""
    d = [r for r in rows if r.get("sent")]
    c = [r for r in rows if r.get("in_top") and not r.get("floor_ok")]
    b = [r for r in rows if not r.get("in_top")]
    f = lambda xs: (len(xs), sum(int(x.get("hit") or 0) for x in xs))  # noqa: E731
    return {"deliv": f(d), "cut": f(c), "below": f(b), "all": f(rows)}


def verdict_ready(t: dict) -> bool:
    """أرضيةُ الحكم — مُثبَتةٌ في العقد قبل أيّ رقم."""
    return t["deliv"][0] >= MIN_DELIVERED and t["all"][0] >= MIN_ROWS


def _pct(hit: int, n: int) -> str:
    return f"{100.0 * hit / n:.1f}%" if n else "—"


def build_digest(day_iso: str, today_rows: list, cum: dict,
                 cov: tuple, missing: int) -> str:
    """رسالةُ التقرير — بلا علامات مقارنة (قاعدة العرض)."""
    e = S.esc
    L = [f"📒 <b>حصادُ قائمة ما قبل الجلسة</b> — {e(day_iso)}",
         f"🩺 حُسم {cov[0]} من {cov[1]} صفًّا "
         f"(تعذّر {missing} — يُعلَن ولا يُصمت)"]
    deliv = [r for r in today_rows if r.get("sent")]
    cut = [r for r in today_rows if r.get("in_top") and not r.get("floor_ok")]
    below = [r for r in today_rows if not r.get("in_top")]

    def line(r: dict) -> str:
        mx = r.get("max_pct")
        mxs = f"{mx:+.1f}%" if isinstance(mx, (int, float)) else "—"
        rg = r.get("reg_max")
        rgs = f"{rg:+.1f}%" if isinstance(rg, (int, float)) else "—"
        tag = "✅ بلغ" if r.get("hit") else "❌ لم يبلغ"
        return (f"‏{e(r[PF.ROW_SYM])} · مرجع ${r['ref']:.4g} · أقصى النافذة {mxs} "
                f"· {tag} · <i>وصفيّ: النظاميّة {rgs}</i>")

    L.append("")
    L.append(f"🟢 <b>المُسلَّم</b> ({len(deliv)} · بلغ "
             f"{sum(r['hit'] for r in deliv)})")
    L.extend([line(r) for r in deliv] or ["‏— لا اسمَ عبر الأرضية اليوم."])
    L.append("")
    L.append(f"🎚️ <b>المقصوصُ بالأرضية</b> ({len(cut)} · بلغ "
             f"{sum(r['hit'] for r in cut)}) — الشاهدُ المضادّ")
    L.extend([line(r) for r in cut] or ["‏— لا مقصوص."])
    if below:
        sh = below[:SHOW_BELOW]
        L.append("")
        L.append(f"🔎 <b>دون العشرة</b> ({len(below)} · بلغ "
                 f"{sum(r['hit'] for r in below)}) — شاهدُ المفتاح")
        L.extend([line(r) for r in sh])
        if len(below) > len(sh):
            L.append(f"‏… و{len(below) - len(sh)} آخرون (يُعلَن ولا يُقصّ صامتًا)")
    L.append("")
    L.append("📈 <b>التراكم</b> (السجلُّ الأماميّ كلُّه)")
    L.append(f"‏🟢 مُسلَّمٌ محسوم {cum['deliv'][0]} · بلغ {cum['deliv'][1]}")
    L.append(f"‏🎚️ مقصوصٌ محسوم {cum['cut'][0]} · بلغ {cum['cut'][1]}")
    L.append(f"‏🔎 دون العشرة {cum['below'][0]} · بلغ {cum['below'][1]}")
    if verdict_ready(cum):
        L.append(f"‏دقّةُ المُسلَّم {_pct(cum['deliv'][1], cum['deliv'][0])} · "
                 f"المقصوص {_pct(cum['cut'][1], cum['cut'][0])} · "
                 f"دون العشرة {_pct(cum['below'][1], cum['below'][0])}")
    else:
        L.append(f"⚖️ <b>لا حكم</b> — الأرضيةُ لم تُبلَغ "
                 f"(مُسلَّمٌ محسوم {cum['deliv'][0]} من {MIN_DELIVERED} · "
                 f"صفوفٌ {cum['all'][0]} من {MIN_ROWS}) ⇒ الأعدادُ حقائقُ عدٍّ "
                 f"ولا يُطبَع فرقٌ بين الشرائح.")
    L.append("")
    L.append("⚠️ <i>الوسمُ المسجَّل: قمّةُ نافذة القرار تبلغ ‏+80% فأكثر عن مرجع "
             "الأمس بأرضية تنفيذٍ $20,000. و«النظاميّة» وصفٌ خارج العقد — حكمُها "
             "يلزمه تسجيلٌ مسبقٌ مستقلّ.</i>")
    return "\n".join(L)


# ── المسار الحيّ ──────────────────────────────────────────────────────────────
def _load_stamp(path: str = STAMP_FILE) -> str:
    try:
        with open(path, encoding="utf-8") as fh:
            return str((json.load(fh) or {}).get("last_session") or "")
    except Exception:                                            # noqa: BLE001
        return ""


def _save_stamp(day_iso: str, path: str = STAMP_FILE) -> None:
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"last_session": str(day_iso)}, fh, ensure_ascii=False)
    except Exception as e:                                       # noqa: BLE001
        _log(f"⚠️ تعذّر ختمُ الحصاد: {e}")


def main() -> int:
    # 🔒 **بوّابةُ التوقيت من مصدرها الواحد** (`split_hunter.session_gate`) —
    #    نسخُها هنا كان سيُنشئ بوّابتين للشيء الواحد، وقد أُصلحت فيها علّةُ
    #    التأخّر (فرعُ الاستدراك) بعد أن ماتت خمسُ أدواتٍ صامتةً.
    from split_hunter import session_gate                          # noqa: PLC0415
    force = os.environ.get("DIGEST_FORCE") == "1"
    ok, sess_date = session_gate()
    if not ok and not force:
        _log("⏰ قبل إغلاق الافتر — لا حصاد.")
        return 0
    day = os.environ.get("DIGEST_DAY") or (sess_date.isoformat() if sess_date
                                           else dt.date.today().isoformat())
    if not force and _load_stamp() == day:
        _log(f"🔁 حُصد {day} سلفًا — دِدوب.")
        return 0
    if not (os.environ.get("POLYGON_API_KEY") or "").strip():
        _log("⛔ بلا POLYGON_API_KEY — لا حسمَ (عطلٌ صريحٌ لا صمت).")
        return 2

    led = read_jsonl(PR.LEDGER_FILE)
    if not led:
        _log("⛔ السجلُّ الأماميّ فارغٌ أو غيرُ موجود — لا شيء يُحصَد.")
        return 3
    done = {r.get("key") for r in read_jsonl(OUT_FILE)}
    floor_d = (dt.date.fromisoformat(day) - dt.timedelta(days=BACKLOG_DAYS)
               ).isoformat()
    todo = [r for r in led
            if row_key(r) not in done
            and str(r.get(PF.ROW_DAY) or "") >= floor_d
            and str(r.get(PF.ROW_DAY) or "") <= day]
    _log(f"📒 السجلّ {len(led)} صفًّا · محسومٌ سلفًا {len(done)} · للحسم {len(todo)}")
    if len(todo) > FETCH_CAP:
        _log(f"⚠️ قُصّ {len(todo) - FETCH_CAP} صفًّا بسقف {FETCH_CAP} — يُعلَن ولا يُصمت.")
        todo = todo[:FETCH_CAP]

    bars_cache, new, miss = {}, [], 0
    for r in todo:
        d = str(r.get(PF.ROW_DAY) or "")
        sym = str(r.get(PF.ROW_SYM) or "").upper()
        if not d or not sym:
            miss += 1
            continue
        ck = f"{d}|{sym}"
        if ck not in bars_cache:
            try:
                a, b = day_bounds_ms(d)
                bars_cache[ck] = PR.polygon_minutes(sym, a, b) or []
            except Exception as e:                               # noqa: BLE001
                _log(f"⚠️ {sym} {d}: {e}")
                bars_cache[ck] = []
        out = resolve_row(r, bars_cache[ck])
        if out is None:
            miss += 1
            continue
        new.append(out)

    if new:
        try:
            with open(OUT_FILE, "a", encoding="utf-8") as fh:
                for o in new:
                    fh.write(json.dumps(o, ensure_ascii=False) + "\n")
        except Exception as e:                                   # noqa: BLE001
            _log(f"⛔ تعذّر كتابةُ الحصاد: {e}")
            return 4

    allo = read_jsonl(OUT_FILE)
    today_rows = [r for r in allo if str(r.get(PF.ROW_DAY)) == day]
    tgt = [r for r in led if str(r.get(PF.ROW_DAY)) == day]
    cov = (len(today_rows), len(tgt))
    pct = (100.0 * cov[0] / cov[1]) if cov[1] else 0.0
    msg = build_digest(day, today_rows, tally(allo), cov, miss)
    _log(msg)
    if not S.send_telegram(msg + "\n\n" + S.FOOTER):
        _log("⚠️ تيليجرام رفض التقرير — لا ختم، تُعاد المحاولة.")
        return 5
    if cov[1] and pct < MIN_COVERAGE_PCT:
        _log(f"⚠️ تغطيةُ الحسم {pct:.0f}% دون {MIN_COVERAGE_PCT:g}% — لا ختم.")
    else:
        _save_stamp(day)
    try:
        S.git_save([OUT_FILE, STAMP_FILE])
    except Exception as e:                                       # noqa: BLE001
        _log(f"⚠️ دفعُ الحصاد: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
