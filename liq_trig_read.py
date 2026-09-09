#!/usr/bin/env python3
"""🚦📜 **قراءةُ الزناد الموازي** — كم مِرساةً فتحها `T-C` حيًّا، ومتى، وبأيّ عمق؟

> أمرُ المالك «اقرأ الزناد» (2026-09-09) بعد شحن `R1 ∪ T-C`.

**المصدرُ سجلٌّ حقيقيٌّ لا ذاكرة:** `op_entry_state.json` يُدفَع مع كلّ دورةِ عاملٍ
حيّ، فتاريخُ git يحمل **آلافَ اللقطات** — تُمشى مراجعةً مراجعةً وتُجمَع كلُّ مِرساةٍ
متميّزة بمفتاح `(رمز · يوم · لحظةُ المِرساة)`. ⇒ القراءةُ **رجعيّةٌ وحتميّة**: تعمل
اليوم وبعد أسبوعٍ بنفس الأمر وتعطي الرقمَ نفسَه على المدى نفسِه.

🔒 **قراءةٌ فقط:** صفرُ إرسالٍ وصفرُ كتابةِ حالةٍ وصفرُ نداءِ شبكة — `git show` وحدَه.

🔴 **والمقياسُ الأوّليُّ صُحِّح بأوّل قراءةٍ حيّة (2026-09-09) — يُدوَّن ولا يُطوى:**
كنتُ أعدّ المفتاحَ `(رمز · يوم · لحظةُ المِرساة)` «مِرساةً» فأعطت القراءةُ الأولى **‏4**
والحقيقةُ **رمزان**. السببُ في الإنتاج لا في العدّ: حين تكتم بوّابةُ المضارب حدثًا
(`has_operator == False`) **يُطرَح مفتاحُ حالته** (`seen.pop`) ليُعاد فحصُ السهم ⇒
**يرسو الرمزُ من جديد على شمعةٍ لاحقة** فيبدو مِرساتين. ⇒ **الحاكمُ عددُ الرموز/اليوم**
وإعاداتُ الرسوّ تُطبَع **منفصلةً** بوصفها أثرَ الكتم لا أحداثًا جديدة.

✅ **وهذا نفسُه يعطي مقياسَ تسليمٍ صادقًا بلا سجلٍّ جديد:** مِرساةٌ **باقيةٌ في آخر
لقطة** = نجت من البوّابة · ومِرساةٌ **ظهرت ثم اختفت** = كُتمت. فيُفصَل «أُطلق» عن
«وصل» من الحالة نفسِها.

⚠️ **حدودُ صدقٍ تُكتب قبل أيّ رقم (فلا تُصاغ بعد رؤيته):**
1. **لا يُفصَل من الحالة وحدَها بين «أبكرُ» و«إضافيّ»:** السهمُ يرسو مرّةً في اليوم،
   فمِرساةٌ فتحها `T-C` إمّا سبقت مِرساةَ `R1` **أو** كانت `R1` لن ترسوَ أصلًا —
   والحالةُ لا تحمل الشرطَ المضادّ. ⇒ يُطبَع **العدُّ** لا «كم بكّر».
2. **الحالةُ لقطةٌ لا دفترُ أحداث:** مِرساةٌ وُلدت وانتهت بين دفعتين متتاليتين قد
   تفوت ⇒ **التغطيةُ تُطبَع** (عددُ المراجعات ومداها) فيُقرأ النقصُ ولا يُخفى.
3. **«باقيةٌ في آخر لقطة» تقريبٌ للتسليم لا يقينُه:** آخرُ لقطةٍ قد تقع أثناء جلسةٍ
   حيّةٍ فتُقرأ مِرساةٌ قائمةٌ «ناجية» وهي بعدُ لم تُحسم.
4. **ولا ربحيّةَ هنا إطلاقًا** — `sent` عمقُ مراحلَ لا عائد.
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict

STATE = "op_entry_state.json"
PREFIX = "LIQ:"
SHIP_ISO = "2026-09-09T15:26:30Z"     # كوميت الدمج `2f32e4c` — قبله لا زناد موازٍ


def log(msg: str):
    print(msg, flush=True)


def _selfcheck_readonly() -> bool:
    """قراءةٌ فقط (كـ`TV6`/`WLK5`): صفرُ إرسالٍ وصفرُ كتابةِ حالةٍ — بالـAST على مصدرها."""
    try:
        src = open(__file__, encoding="utf-8").read()
    except Exception:                                            # noqa: BLE001
        return False
    banned = {"send_telegram", "git_save", "save_watchlist", "save_op_entry_state",
              "record_new_alerts", "save_near_watch", "save_hunter_watch"}
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Call):
            fn = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
            if fn in banned:
                return False
            if fn == "open":
                mode = ""
                if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                    mode = str(n.args[1].value)
                for kw in n.keywords or []:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        mode = str(kw.value.value)
                if any(c in mode for c in ("w", "a", "x", "+")):
                    return False
    return True


def collect(snapshots) -> dict:
    """**الدالّةُ النقيّة** — تُجمِّع المراسي المتميّزة من لقطاتِ حالةٍ متتالية.

    `snapshots` = قائمةُ `(زمنُ اللقطة، قاموسُ الحالة)`. المفتاحُ المتميّز
    `(الرمز · اليوم · لحظةُ المِرساة)` ⇒ لقطةٌ تتكرّر لا تُضاعف العدّ، **وأوّلُ
    ظهورٍ يفوز** فيُحفَظ أقدمُ ما رأيناه من عمق المراحل ثم يُحدَّث بأعمقها.
    ترجّع `{"anchors": {...}, "revs": n, "span": (أوّل، آخر)}`. نقيّة."""
    anchors, first, last = {}, None, None
    for ts, st in (snapshots or []):
        if first is None:
            first = ts
        last = ts
        if not isinstance(st, dict):
            continue
        for k, v in st.items():
            if not k.startswith(PREFIX) or not isinstance(v, dict):
                continue
            ams = v.get("anchor_ms")
            if not ams:
                continue
            key = (k[len(PREFIX):], str(v.get("date") or ""), int(ams))
            cur = anchors.get(key)
            sent = list(v.get("sent") or [])
            row = {"trig": v.get("trig"), "sent": sent,
                   "price": v.get("anchor_price"), "peak_usd": v.get("peak_usd"),
                   "rearm": v.get("rearm_n") or 0, "seen": ts}
            if cur is None:
                anchors[key] = row
            else:
                # أعمقُ ما بلغته المراحلُ يفوز (اللقطةُ الأحدث تحمل تقدّمًا)
                if len(sent) > len(cur["sent"]):
                    cur["sent"] = sent
                if row["trig"] and not cur["trig"]:
                    cur["trig"] = row["trig"]
    # ✅ «باقيةٌ في آخر لقطة» = نجت من بوّابة الكتم · و«اختفت» = كُتمت وأُعيد فحصُها
    last_keys = set()
    if snapshots:
        _ts, _st = snapshots[-1]
        if isinstance(_st, dict):
            for k, v in _st.items():
                if k.startswith(PREFIX) and isinstance(v, dict) and v.get("anchor_ms"):
                    last_keys.add((k[len(PREFIX):], str(v.get("date") or ""),
                                   int(v["anchor_ms"])))
    for key, row in anchors.items():
        row["alive"] = key in last_keys
    return {"anchors": anchors, "revs": len(snapshots or []),
            "span": (first, last)}


def git_snapshots(path: str = STATE, limit: int = 0, ref: str = "HEAD"):
    """يمشي تاريخَ git للملفّ ويرجّع `(زمنُ الكوميت، الحالة)` — الأقدمُ أوّلًا.

    ⚠️ **والمرجعُ يهمّ:** العاملُ الحيُّ يدفع الحالةَ إلى `main`، فقراءةُ فرعٍ جانبيٍّ
    تُظهر مدًى **أقصرَ** بلا خطأٍ ظاهر ⇒ `TRIG_READ_REF` (الافتراض `origin/main`)
    **ويُطبَع المرجعُ في التقرير** فلا يُقرأ نقصُ التغطية اكتمالًا.
    فاشلٌ-آمن: مراجعةٌ تالفةٌ تُتخطّى **وتُعدّ** (لا تُخمَّن ولا تُسقط القراءة)."""
    try:
        out = subprocess.run(["git", "log", "--format=%H %cI", str(ref), "--", path],
                             capture_output=True, text=True, timeout=120).stdout
    except Exception:                                            # noqa: BLE001
        return ([], 0)
    revs = [ln.split(" ", 1) for ln in out.splitlines() if " " in ln]
    revs.reverse()
    if limit:
        revs = revs[-int(limit):]
    snaps, bad = [], 0
    for sha, ts in revs:
        try:
            blob = subprocess.run(["git", "show", f"{sha}:{path}"],
                                  capture_output=True, text=True, timeout=60).stdout
            snaps.append((ts, json.loads(blob)))
        except Exception:                                        # noqa: BLE001
            bad += 1
    return (snaps, bad)


def report(res: dict, bad: int = 0, ref: str = "HEAD") -> list:
    """📋 التقرير — **العددُ والأسماءُ والتغطيةُ وحدودُ الصدق**، بلا رقمٍ مشتقّ لم يُقَس."""
    a = res["anchors"]
    tc = {k: v for k, v in a.items() if v.get("trig")}
    r1 = {k: v for k, v in a.items() if not v.get("trig")}
    by_day = Counter(k[1] for k in a)
    tc_day = Counter(k[1] for k in tc)
    tc_syms = {(k[0], k[1]) for k in tc}
    r1_syms = {(k[0], k[1]) for k in r1}
    alive_tc = [k for k, v in tc.items() if v.get("alive")]
    L = ["🚦📜 **قراءةُ الزناد الموازي `T-C`**",
         f"   📦 التغطية: {res['revs']} مراجعةً مقروءة من `{ref}`"
         + (f" · {bad} تالفةٌ تُخطّيت" if bad else "")
         + f" · المدى {res['span'][0]} ⟶ {res['span'][1]}",
         f"   🥇 **الحاكم — رموزٌ رست/اليوم:** {len(tc_syms)} بالزناد الموازي"
         f" · {len(r1_syms)} بـ`R1`",
         f"   ↳ ومواضعُ رسوٍّ خام: {len(tc)} موازية · {len(r1)} `R1`"
         f" (الفرقُ **إعاداتُ رسوٍّ بعد كتمِ بوّابة المضارب** لا أحداثٌ جديدة)",
         f"   📬 من الموازية: **{len(alive_tc)} باقيةٌ في آخر لقطة** (نجت من الكتم)"
         f" و{len(tc) - len(alive_tc)} اختفت ⇒ كُتمت وأُعيد فحصُ سهمِها",
         f"   🚢 الشحنُ وقع {SHIP_ISO} — وما قبله لا زنادَ موازيًا بالبناء"]
    if not tc:
        L.append("   📭 **صفرُ مِرساةٍ من الزناد الموازي في المدى المقروء** —"
                 " وهذا **غيابُ بيانات لا حكمٌ عليه** ما دام المدى لم يتجاوز الشحن.")
    for d in sorted(by_day):
        L.append(f"   📅 {d}: {by_day[d]} موضعَ رسوٍّ · منها {tc_day.get(d, 0)} موازية")
    for (sym, day, ms), v in sorted(tc.items(), key=lambda x: x[0][2]):
        L.append(f"   🚦 {sym} · {day} · {ms} · مراحل {'/'.join(v['sent']) or '—'}"
                 f" · سعرُ المِرساة {v.get('price')}"
                 f" · {'باقية' if v.get('alive') else '**كُتمت**'}")
    L += ["   ⚠️ **حدودُ الصدق (مكتوبةٌ قبل أيّ رقم):**",
          "      ① لا يُفصَل من الحالة وحدَها بين «مِرساةٍ أبكر» و«مِرساةٍ إضافيّة»"
          " — السهمُ يرسو مرّةً في اليوم ولا شرطَ مضادّ في السجلّ.",
          "      ② الحالةُ لقطةٌ لا دفترُ أحداث ⇒ مِرساةٌ بين دفعتين قد تفوت"
          " (والتغطيةُ أعلاه تُقرأ معها).",
          "      ③ **رسائلُ لا تسليم** — الفلترُ والسقفُ بعد المِرساة.",
          "      ④ **ولا ربحيّةَ هنا** — `sent` عمقُ مراحلَ لا عائد."]
    return L


def main() -> int:
    if not _selfcheck_readonly():
        log("⛔ الأداةُ ليست قراءةً فقط")
        return 3
    lim = int(os.environ.get("TRIG_READ_LIMIT") or 0)
    ref = (os.environ.get("TRIG_READ_REF") or "origin/main").strip()
    snaps, bad = git_snapshots(limit=lim, ref=ref)
    if not snaps:
        log("⛔ لا مراجعاتِ حالةٍ تُقرأ (تاريخُ git لا يحمل الملفّ)")
        return 2
    for ln in report(collect(snaps), bad, ref):
        log(ln)
    return 0


if __name__ == "__main__":
    sys.exit(main())
