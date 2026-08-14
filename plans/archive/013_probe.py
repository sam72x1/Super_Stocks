# -*- coding: utf-8 -*-
"""🔎 مِجَسّ الحسم للخطة 013 — «هل ينتفخ أساس حجم رادار الانطلاق أول 30 دقيقة؟»

**قراءة فقط · صفر شبكة إنتاج · صفر تشغيل workflow حيّ · صفر تعديل كود.**
يطبّق **المعيار المسجَّل مسبقًا في `plans/013-findings.md` حرفيًّا** — لا تُحرَّك عتبته.

الاستعمال (بعد تنزيل artifacts كما في `013-findings.md §BLOCKED_EXTERNAL`):
    python3 plans/013_probe.py [جذر_التنزيلات]        # الافتراضي /tmp/e2dl

الحكم أحد ثلاثة فقط: «ينتفخ» · «لا ينتفخ» (الفرضية سقطت) · «العيّنة لا تكفي».
"""
import datetime as dt
import glob
import json
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SUPER_STOCKS_TESTING", "1")     # لا git/شبكة من الوحدة
import Super_stock as S                                # noqa: E402

# ===== المعيار المسجَّل مسبقًا (لا يُعدَّل) =====
WINDOW_MIN = 30       # نافذة «أول نصف ساعة» من الافتتاح
MIN_SLICE = 20        # أقلّ عيّنة لكل شريحة
RATIO = 1.5           # «ينتفخ» = وسيط الأولى ÷ وسيط الثانية يساوي هذا فأكثر
START_TOL_MIN = 2     # بوّابة التغطية: أقصى تأخّر لأول مسح عن الافتتاح


def _sessions(root):
    """{تاريخ: (مرشّحون, تأخّر_التغطية_بالدقائق)} — الملفّ المدموج لا المقاطع."""
    out = {}
    for p in glob.glob(os.path.join(root, "*/e2_measurement/session_*/candidates.jsonl")):
        if "/segment_" in p:
            continue                                    # تفادي الازدواج
        sdir = os.path.dirname(p)
        day = os.path.basename(sdir)[len("session_"):]
        try:
            rows = [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()]
        except Exception:
            continue
        lag = None
        sj = os.path.join(sdir, "segment_open", "session.json")
        if os.path.exists(sj):
            try:
                d = json.load(open(sj, encoding="utf-8"))
                fp, op = d.get("first_successful_poll_at"), d.get("expected_open_iso")
                if fp and op:
                    lag = (dt.datetime.fromisoformat(fp.replace("Z", "+00:00"))
                           - dt.datetime.fromisoformat(op.replace("Z", "+00:00"))
                           ).total_seconds() / 60.0
            except Exception:
                pass
        # جلسة مكرَّرة عبر artifacts ⇒ تفوز الأكثر مرشّحين (حتميّ)
        if day not in out or len(rows) > len(out[day][0]):
            out[day] = (rows, lag)
    return out


def main(root="/tmp/e2dl"):
    ses = _sessions(root)
    if not ses:
        print(f"🟡 الحكم: **العيّنة لا تكفي** — لا جلسة تحت {root}")
        return 0
    early, late, unclassified, skipped = [], [], 0, []
    emitted = {"early": 0, "late": 0}
    for day, (rows, lag) in sorted(ses.items()):
        # 🚧 بوّابة التغطية (شرط الحسم 3): نافذة غير مراقَبة تُنتج صفرًا مضلِّلًا
        if lag is None or lag > START_TOL_MIN:
            skipped.append((day, "بلا بيان تغطية" if lag is None else f"+{lag:.0f}د"))
            continue
        d0 = dt.date.fromisoformat(day)
        aware = dt.datetime(d0.year, d0.month, d0.day, 15, 0, tzinfo=dt.timezone.utc)
        om = S.market_session_now(aware)["open"]
        open_ms = dt.datetime(d0.year, d0.month, d0.day, om // 60, om % 60,
                             tzinfo=dt.timezone.utc).timestamp() * 1000
        for c in rows:
            t, vx = c.get("trigger_bar_start"), c.get("vol_x")
            if t is None or vx is None:
                unclassified += 1
                continue
            mins = (float(t) - open_ms) / 60000.0
            key = "early" if 0 <= mins < WINDOW_MIN else "late"
            (early if key == "early" else late).append(float(vx))
            if c.get("alert_emitted"):
                emitted[key] += 1
    print(f"جلسات متاحة: {len(ses)} · مؤهّلة بالتغطية: {len(ses) - len(skipped)}")
    if skipped:
        print("  ⏭️ مُستبعَدة (نافذتها الأولى غير مراقَبة): "
              + " · ".join(f"{d}({w})" for d, w in skipped))
    print(f"غير مصنَّف (بلا trigger_bar_start/vol_x): {unclassified}")
    for name, xs, k in (("[0,30) أول نصف ساعة", early, "early"),
                        ("[30,∞) بقيّة الجلسة ", late, "late")):
        if xs:
            print(f"{name}: عدد={len(xs)} · وسيط={st.median(xs):.2f} "
                  f"· متوسط={st.mean(xs):.2f} · مدى={min(xs):.1f}-{max(xs):.1f} "
                  f"· مُطلَق={emitted[k]}")
        else:
            print(f"{name}: عدد=0")
    if len(early) < MIN_SLICE or len(late) < MIN_SLICE:
        print(f"\n🟡 الحكم: **العيّنة لا تكفي** (الحدّ {MIN_SLICE}/شريحة · "
              f"المتاح {len(early)}/{len(late)})")
        return 0
    r = st.median(early) / st.median(late)
    print(f"\nالنسبة = {r:.2f}× (الحدّ المسجَّل {RATIO}×)")
    print("🔴 الحكم: **ينتفخ** — يلزمه تسجيل مسبق جديد وموافقة المالك قبل أي تغيير كود"
          if r >= RATIO else
          "🟢 الحكم: **لا ينتفخ** — الفرضية سقطت (نتيجة حقيقية، لا نقص عيّنة)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/e2dl"))
