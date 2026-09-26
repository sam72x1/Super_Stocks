#!/usr/bin/env python3
"""🔬♻️ استرجاع جلسات E2 الضائعة من artifacts التشغيلات السابقة.

**الخلفية (عطل حقيقي، 2026-07-28):** خطوة الدفع في `ignition.yml` كانت **عارية بلا
rebase**، والجلسة تمتدّ ~4.5 ساعة فيتحرّك `main` أثناءها ⇒ `! [rejected] (fetch first)`
⇒ **ملخّص كل جلسة يضيع** رغم نجاح المقطعين والدمج. جلسة واحدة فقط (2026-07-24) نجح
دفعها من عشر. البيانات نفسها **لم تضع**: كل تشغيلة ترفع `ign-assembled-<run_id>`
(احتفاظ 90 يومًا) قبل الدفع. هذه الأداة تُعيدها إلى الريبو.

الاستعمال (داخل workflow بعد `gh run download`):
    python3 e2_recover.py <مجلّد التنزيلات>

**استرجاع/دمج فقط:** لا يمسّ الرادار ولا الفرز ولا أي جذر، ولا يخترع بيانات — ينسخ ما
رُفِع وقتها حرفيًّا. عند تعارض تاريخين من تشغيلتين تفوز **الأكثر دورات مكتملة** (حتميّ)
ويُطبَع التعارض صراحةً.
"""
import glob
import json
import os
import shutil
import sys

INDEX = "ignition_e2_session_index.json"
ROOT = "e2_measurement"
IDX_KEYS = ("n_delivered", "n_emitted", "n_raw_candidates", "n_symbols", "termination")


def _read_json(p):
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh) or {}
    except Exception:
        return {}


def _session_dirs(download_root):
    """كل مجلّدات الجلسات داخل التنزيلات — بأي عمق (لا نفترض شكل الأرشيف)."""
    pats = (os.path.join(download_root, "**", ROOT, "session_*"),
            os.path.join(download_root, "**", "session_*"))
    out = {}
    for pat in pats:
        for d in glob.glob(pat, recursive=True):
            if os.path.isdir(d) and os.path.basename(d).startswith("session_"):
                out.setdefault(os.path.realpath(d), os.path.basename(d)[len("session_"):])
    return out


def _summary_of(sdir):
    """ملخّص الجلسة: من summary.json داخلها، وإلا من ignition_e2_summary.json المجاور."""
    s = _read_json(os.path.join(sdir, "summary.json"))
    if s:
        return s
    up = os.path.dirname(os.path.dirname(sdir))       # …/<run>/  (فوق e2_measurement)
    return _read_json(os.path.join(up, "ignition_e2_summary.json"))


def _tail_fetcher(fetch_range):
    """🔎 (2026-09-26) جالبُ فحص الذيل: `"auto"` ⇒ جالبُ Polygon المؤرَّخ **بمفتاحٍ فقط** (بلا مفتاحٍ ⇒
    None = الحكمُ السابق حرفيًّا · والسويّةُ بلا مفتاحٍ فلا شبكة) · وغيرُه يُمرَّر كما هو (محقونٌ للاختبار)."""
    if fetch_range != "auto":
        return fetch_range
    if not os.environ.get("POLYGON_API_KEY", "").strip():
        return None
    try:
        import ignition_e2_assemble as _ASM
        return _ASM.fetch_minute_range
    except Exception as e:                       # noqa: BLE001
        print("   ⚠️ جالبُ فحص الذيل تعذّر: %s" % e)
        return None


def recover(download_root, repo_root=".", fetch_range="auto"):
    idx_path = os.path.join(repo_root, INDEX)
    idx = _read_json(idx_path)
    before = set(idx)
    best, conflicts, no_summary = {}, [], []
    for sdir, date in sorted(_session_dirs(download_root).items()):
        summ = _summary_of(sdir)
        if not summ or summ.get("session_date") not in (None, date):
            # ملخّص غائب أو لتاريخ آخر ⇒ لا نخمّن
            # 🔴 خطة 024 (2026-08-15): الفرعُ كان يتخطّى **الغائبَ وحده**، أمّا
            # الملخّصُ الموجودُ بتاريخٍ مختلف فيمرّ ويُدمَج **تحت التاريخ الخطأ**
            # — و`_summary_of` ترتدّ لملخّص التشغيلة الجذر الذي قد يخصّ جلسةً
            # أخرى، فهذي بعينها الحالةُ المقصودة ⇒ عدّاداتٌ (‏n_delivered/
            # n_emitted) تُكتب لجلسةٍ ليست لها = فهرسٌ مُفسَد. العقدُ المكتوب
            # «لا نخمّن» صار **منفَّذًا**: كلتا الحالتين تُتخطَّى وتُعلَن.
            no_summary.append((date, sdir))
            continue
        loops = int(summ.get("loops_completed") or 0)
        prev = best.get(date)
        if prev and prev[0] != loops:
            conflicts.append((date, prev[0], loops))
        if not prev or loops > prev[0]:
            best[date] = (loops, sdir, summ)

    copied, merged = [], []
    for date, (loops, sdir, summ) in sorted(best.items()):
        dst = os.path.join(repo_root, ROOT, "session_%s" % date)
        if not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copytree(sdir, dst)
            copied.append(date)
        entry = {k: summ.get(k) for k in IDX_KEYS if summ.get(k) is not None}
        if date not in idx:
            merged.append(date)
        idx[date] = {**idx.get(date, {}), **entry}

    # 🧾 (2026-09-24): **حكمُ المدقّق يُحفظ** لكلّ جلسةٍ مسترجَعة — بالقاعدة الحاليّة وعلى
    #    الخام المحفوظ في artifacts (‏90 يومًا). كان يُطبَع في خطوةٍ لاحقة ولا يُحفظ، فلم
    #    يعرف التقريرُ الأسبوعيّ أن البوّابةَ حمراءُ يوميًّا منذ 08-31. **ولا تخمين:** مجلّدٌ
    #    بلا `session.json` لا يُحكَم عليه · والعدّاداتُ أعلاه لا تُمَسّ.
    judged, judge_errors = [], []
    try:
        import ignition_e2_analyze as _A
    except Exception as e:                       # الاسترجاعُ لا يسقط بسقوط المدقّق
        _A = None
        print("   ⚠️ حكمُ المدقّق تعذّر: %s" % e)
    # 🔎 (2026-09-26): **ذيلُ المسار** لما لم يبلغ الإغلاق يُفحص عند المزوّد (نافذةٌ مؤرَّخة · بعد الإغلاق
    #    بالبناء) ويُكتب دليلُه `TAIL_CHECKS_FILE` في المجلّد ونسختِه ثمّ يُعاد الحكم — للجلسات التي جُمِّعت
    #    قبل هذا الإصلاح (مِجَسّ `36223025879`: CELU · MIMI · CCTG · CURX · SMX). بلا مفتاحٍ = الحكمُ السابق.
    _fr = _tail_fetcher(fetch_range) if _A else None
    tail_done = []                               # [(تاريخ، {رمز: فحص})]
    for date, (_loops, sdir, _summ) in (sorted(best.items()) if _A else ()):
        if not os.path.exists(os.path.join(sdir, "session.json")):
            continue
        # 🔴 **لكلّ جلسةٍ حارسُها** (‏2026-09-24): كان الحارسُ حول الحلقة كلِّها فاستثناءٌ في
        #    جلسةٍ واحدة (مخطّطٌ أقدم في إعادة الحكم التاريخيّ) **يبتر ما بعدها صامتًا** ⇒ تُحكَم
        #    الباقيةُ ويُعلَن المتعذِّرُ بتاريخه — ولا يُخترَع له حكم.
        try:
            _r = _A.analyze_session(sdir)
            _open = _r.get("path_tail_unverified") or {}
            if _open and _fr is not None and _r.get("expected_close_ms") is not None:
                import ignition_e2_assemble as _ASM
                _cks = {}
                for _sym, _lt in sorted(_open.items()):
                    _ck, _ = _ASM.close_tail_check(_fr, _sym, _lt, _r["expected_close_ms"],
                                                   source="e2_recover")
                    if _ck is not None:
                        _cks[_sym] = _ck
                if _cks:
                    _ASM.write_tail_checks(sdir, _cks)
                    _dst = os.path.join(repo_root, ROOT, "session_%s" % date)
                    if os.path.isdir(_dst) and os.path.abspath(_dst) != os.path.abspath(sdir):
                        _ASM.write_tail_checks(_dst, _cks)
                    tail_done.append((date, _cks))
                    _r = _A.analyze_session(sdir)
            v = _A.verdict_entry(_r)
        except Exception as e:                   # noqa: BLE001
            judge_errors.append(date)
            print("   ⚠️ حكمُ المدقّق تعذّر لجلسة %s: %s" % (date, e))
            continue
        if v and isinstance(idx.get(date), dict):
            idx[date] = {**idx[date], **v}
            judged.append((date, v["session_complete"]))

    with open(idx_path, "w", encoding="utf-8") as fh:
        json.dump(dict(sorted(idx.items())), fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print("♻️ استرجاع جلسات E2")
    print("   كانت بالفهرس: %d ⇒ صارت: %d (جديدة: %d)"
          % (len(before), len(idx), len(merged)))
    print("   جلسات جديدة: " + (", ".join(merged) or "لا شيء"))
    print("   مجلّدات خام نُسخت: " + (", ".join(copied) or "لا شيء"))
    if conflicts:
        print("   ⚠️ تعارض تاريخ من تشغيلتين (فازت الأكثر دورات): "
              + " · ".join("%s (%d مقابل %d)" % c for c in conflicts))
    if no_summary:
        print("   ⚠️ بلا ملخّصٍ أو بتاريخٍ مخالف (تُخطَّت، لا تخمين): "
              + ", ".join(d for d, _ in no_summary))
    # صدق العدّ: الاكتمالُ حكمُ المدقّق وحده — والمحفوظُ منه يُعَدّ، وما لم يُحكَم لا يُفترَض.
    normal = [d for d, v in idx.items() if v.get("termination") == "normal"]
    print("   🧮 بالفهرس %d جلسة · منها %d بإنهاء طبيعي." % (len(idx), len(normal)))
    _jud = [v for v in idx.values() if isinstance(v, dict)
            and isinstance(v.get("session_complete"), bool)]
    print("   🧾 حكمُ المدقّق محفوظٌ لـ%d جلسة (هذي التشغيلة: %d) · مكتملة %d · غير محكومة %d."
          % (len(_jud), len(judged), sum(1 for v in _jud if v["session_complete"]),
             len(idx) - len(_jud)))
    if judge_errors:
        print("   ⚠️ تعذّر الحكمُ على %d جلسة (لا حكمَ يُخترَع): %s"
              % (len(judge_errors), ", ".join(judge_errors)))
    if tail_done:
        print("   🔎 ذيلُ المسار عند المزوّد (%d جلسة): %s" % (len(tail_done), " · ".join(
            "%s %s" % (d, ",".join("%s=%s" % (k, ("خالٍ" if c.get("n") == 0 else "%s شمعة" % c.get("n")))
                                   for k, c in sorted(cks.items())))
            for d, cks in tail_done)))
    # 🔬 (2026-09-25) **عدّادُ E2-B التراكميّ من الفهرس** — كلُّ الجلسات المكتملة لا المسترجَعة الليلة
    #    وحدَها (مدقّقُ الخطوة التالية يرى مجلّدَ هذه التشغيلة فقط فطبع ‏2/20 والكاملُ ‏11/20). والمكتملةُ
    #    بلا عدٍّ محفوظ **تُعلَن** فيُقرأ الرقمُ حدًّا أدنى لا صفرًا مُخترَعًا.
    e2b = None
    if _A is not None:
        try:
            e2b = _A.e2b_count_from_index(idx)
        except Exception as e:                   # noqa: BLE001
            print("   ⚠️ عدّادُ E2-B التراكميّ تعذّر: %s" % e)
    if e2b:
        _n, _comp, _have = e2b
        print("   🔬 بوّابة E2-B التراكميّة (من الفهرس): %d/%d تنبيهًا بـNBBO قابلٍ للتنفيذ في جلساتٍ "
              "مكتملة · محسوبٌ على %d من %d مكتملةً تحمل العدّ%s"
              % (_n, _A.E2B_MIN_DECIDED_ALERTS, _have, _comp, "" if _have == _comp else
                 " — ⚠️ %d بلا عدٍّ محفوظ ⇒ الرقمُ حدٌّ أدنى (يُستكمَل باسترجاع تشغيلاتها ما دامت "
                 "artifacts حيّة)" % (_comp - _have)))
    rebuilt = rebuild_fire_log(best, repo_root=repo_root)
    ts_filled = fill_reconstructed_ts(best, repo_root=repo_root)
    fires = _delivered_fires(best)
    if fires:
        # ⚠️ **قراءة لا توليد:** هذي تنبيهات **وصلت تلغرام فعلًا** (`delivered=true`)
        # وضاعت من `ignition_log.json` مع نفس الدفع الفاشل. تُعرَض للمقارنة **ولا
        # تُكتب في سجلّ الإطلاقات** — إعادة بناء ذلك السجلّ تلمس بيانات قياس فتحتاج
        # قرار المالك (`candidates.jsonl` يحمل السعر والرقم الحرج اللازمين).
        print("   🔥 تنبيهات وصلت تلغرام في الجلسات المسترجَعة (عرض فقط، لا تُكتب):")
        for date, syms in fires:
            print("      %s: %s" % (date, " · ".join(syms)))
    return {"index": len(idx), "new": merged, "copied": copied, "fires": fires,
            "rebuilt": rebuilt, "ts_filled": ts_filled,
            "judged": judged, "judge_errors": judge_errors, "e2b": e2b, "tail_checks": tail_done,
            "conflicts": conflicts, "no_summary": [d for d, _ in no_summary]}


FIRE_LOG = "ignition_log.json"
# خريطة الحقول: كل حقل في سجلّ الإطلاقات له **مصدر مباشر مسجَّل** في candidates.jsonl.
# لا حقل يُشتقّ ولا يُخمَّن — ولذلك الإعادة **استرجاع** لا توليد.
_FIRE_MAP = (("symbol", "symbol"), ("date", "session_date"), ("fired_at", "telegram_sent_at"),
             ("break_level", "break_level"), ("price", "signal_price"),
             ("vol_x", "vol_x"), ("usd", "signal_usd"), ("candle_class", "candle_class"))


def rebuild_fire_log(best, repo_root=".", log_name=FIRE_LOG):
    """🔥 يُعيد بناء إدخالات `ignition_log.json` الضائعة من `candidates.jsonl`.

    ضاعت مع نفس الدفع الفاشل الذي أضاع ملخّصات الجلسات، فقياس «الإنذار الكاذب» في
    أداة التطوير كان أعمى عن معظم إطلاقات الرادار. تُعاد **المُطلَقة فقط**
    (`alert_emitted=true`)، بالدِدوب القائم (رمز+تاريخ)، وكل حقل منسوخ من مصدره
    المسجَّل بلا اشتقاق. **كل إدخال مُعاد يحمل `source="e2_reconstructed"`** فلا
    يختلط بسجلّ أصليّ أبدًا — مُسترجَع ≠ مُختلَق، والتمييز يبقى ظاهرًا للأبد.
    فاشلة-آمنة: أي جلسة بلا ملفّ/بصيغة تالفة تُتخطّى بلا مساس بالسجلّ."""
    path = os.path.join(repo_root, log_name)
    log = _read_json(path)
    if not isinstance(log, list):
        log = []
    seen = {(r.get("symbol"), r.get("date")) for r in log}
    added = []
    for _date, (_loops, sdir, _s) in sorted(best.items()):
        try:
            with open(os.path.join(sdir, "candidates.jsonl"), encoding="utf-8") as fh:
                rows = [json.loads(x) for x in fh if x.strip()]
        except Exception:
            continue
        for c in rows:
            if not c.get("alert_emitted"):
                continue
            rec = {k: c.get(src) for k, src in _FIRE_MAP}
            key = (rec.get("symbol"), rec.get("date"))
            if not rec.get("symbol") or key in seen:
                continue
            rec["source"] = "e2_reconstructed"
            seen.add(key)
            log.append(rec)
            added.append("%s %s" % (rec["date"], rec["symbol"]))
    if added:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(log, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
    print("   🔥 سجلّ الإطلاقات: أُعيد %d إدخالًا (صار %d) — %s"
          % (len(added), len(log), ", ".join(added) or "لا جديد"))
    return added


def _ts_fields_from_candidate(c):
    """⏱️ طابعُ «لحظة الإطلاق» لإدخالٍ مُسترجَع — **بقاعدة الإنتاج نفسِها لا بقاعدةٍ جديدة:**
    اختيارُ المصدر من `ignition_e2_assemble._fires_from_candidates` (‏`telegram_sent_at_ms` ثمّ
    `trigger_bar_start`) · والتحقّقُ مرآةُ `Super_stock._fired_ts_fields` حرفًا (‏1e12 ≤ ts < 1e13 ·
    والفاسدُ ⇒ `{}` مجهولٌ لا صفر) — ومساواتُهما مقفولةٌ في السويّة (`E2R1`). لا تُستورَد
    `Super_stock` لأن `e2_recover.yml` لا يثبّت الاعتماديات (فتسقط الاستيرادَ صامتةً ⇒ صفرُ استكمال)."""
    try:
        import ignition_e2_assemble as _ASM
        s = _ASM._fires_from_candidates([{**c, "alert_emitted": True}])[0][0]
        out = {}
        for key, dst in (("fired_ts_ms", "fired_ts_ms"),
                         ("trigger_bar_start", "trigger_bar_ms")):
            v = s.get(key)
            if v is None:
                continue
            v = int(v)
            if 10 ** 12 <= v < 10 ** 13:
                out[dst] = v
        if "fired_ts_ms" not in out:
            return {}
        src = s.get("fired_ts_src")
        out["fired_ts_src"] = src if src in ("telegram_sent", "trigger_bar_start") else "unknown"
        return out
    except Exception:
        return {}


# ⏱️ (2026-09-25) **والماضي لا يُعاد كتابتُه:** الحقلُ يُحفظ **للأمام** منذ «لحظة الإطلاق» (‏2026-09-23 · إذنُ المالك)
#    ومجتمعُ عقد `T-SECONDS` (‏حتى 09-18) يُثبت صفرَه (`SCK0`) ⇒ الاستكمالُ لإدخالاتٍ من هذا التاريخ فصاعدًا وحدَها.
#    🔴 أمسكه `SCK0` بعد الاسترجاع الكامل `36095794496`: استُكمل عشرةُ إطلاقاتٍ من 07-15 ⟶ 07-28 فأُعيدت كما كانت.
FIRED_TS_SINCE = "2026-09-23"


def fill_reconstructed_ts(best, repo_root=".", log_name=FIRE_LOG):
    """⏱️ (2026-09-25) يستكمل طابعَ «لحظة الإطلاق» للإدخالات **المُسترجَعة وحدَها**.

    **الخلفية (مقيسة):** دفعُ الـassembler لجلسة 09-24 سقط (`35984252866`) فأعاد
    `rebuild_fire_log` إطلاقاتِها الأربعة **بلا `fired_ts_ms`** — شرطِ إعادة قياس `T-SECONDS` —
    لأن `_FIRE_MAP` أقدمُ من الحقل (‏2026-09-23)، ومصدرُه نفسُه في `candidates.jsonl`.
    🔒 **ثلاثةُ حرّاس:** (1) `source == "e2_reconstructed"` وحدَه — **الأصليُّ لا يُمَسّ أبدًا** ·
    (2) لا يدهس طابعًا موجودًا · (3) المرشّحُ هو **نفسُه** الذي بُني منه الإدخال: أوّلُ مُطلَقٍ
    لـ(الرمز، التاريخ) بترتيب الملفّ كما في `rebuild_fire_log` **و`telegram_sent_at` = `fired_at`**
    — وإلّا لا استكمال (لا تخمين). فاشلٌ-آمن: جلسةٌ بلا ملفٍّ أو بصيغةٍ تالفة تُتخطّى.
    (4) **ومن `FIRED_TS_SINCE` وحدَه** — الماضي لا يُعاد كتابتُه (`SCK0` · `E2R3`)."""
    path = os.path.join(repo_root, log_name)
    log = _read_json(path)
    if not isinstance(log, list):
        return []
    need = {(r.get("symbol"), r.get("date")): r for r in log
            if isinstance(r, dict) and r.get("source") == "e2_reconstructed"
            and "fired_ts_ms" not in r and str(r.get("date") or "") >= FIRED_TS_SINCE}
    filled = []
    for _date, (_loops, sdir, _s) in sorted(best.items()):
        if not need:
            break
        try:
            with open(os.path.join(sdir, "candidates.jsonl"), encoding="utf-8") as fh:
                rows = [json.loads(x) for x in fh if x.strip()]
        except Exception:
            continue
        for c in rows:
            if not c.get("alert_emitted"):
                continue
            key = (c.get("symbol"), c.get("session_date"))
            r = need.pop(key, None)            # أوّلُ مُطلَقٍ وحدَه — كما بُني الإدخال
            if r is None or c.get("telegram_sent_at") != r.get("fired_at"):
                continue
            ts = _ts_fields_from_candidate(c)
            if ts:
                r.update(ts)
                filled.append("%s %s" % (key[1], key[0]))
    if filled:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(log, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
    print("   ⏱️ طابعُ «لحظة الإطلاق» للمُسترجَع: استُكمل %d — %s"
          % (len(filled), ", ".join(filled) or "لا جديد"))
    return filled


def _delivered_fires(best):
    """🔥 الرموز التي **سُلِّمت** فعلًا لتلغرام في كل جلسة (`deliveries.jsonl`،
    `delivered=true`). قراءة صرفة — لا تكتب شيئًا ولا تخمّن ما ليس مسجَّلًا."""
    out = []
    for date, (_loops, sdir, _s) in sorted(best.items()):
        syms = []
        try:
            with open(os.path.join(sdir, "deliveries.jsonl"), encoding="utf-8") as fh:
                for ln in fh:
                    ln = ln.strip()
                    if not ln:
                        continue
                    r = json.loads(ln)
                    if r.get("delivered") and r.get("symbol") not in syms:
                        syms.append(r["symbol"])
        except Exception:
            continue
        if syms:
            out.append((date, syms))
    return out


# 🗄️ (2026-09-25) **أرشيفُ الخام المتجدّد** — خامُ كلّ جلسة (candidates · minute_paths …) يعيش في artifact
#    احتفاظُه 90 يومًا (مواصفة E2 §5/§12: لا يُدفَع للريبو)، وبوّابتا E2-B/C تحتاجان خامَ **أشهر**
#    (‏20 ثمّ 50 تنبيهًا بـ≈0.39 للجلسة المكتملة) ⇒ أوّلُ مكتملةٍ (07-29) ينتهي ≈10-27 قبل أن تُبلغ E2-B.
#    فيُنزَّل أحدثُ أرشيفٍ غيرِ منتهٍ ويُتّحد مع جلسات الليلة ويُرفع من جديد (احتفاظٌ جديد) — **ولا ينكمش**.
RAW_ARCHIVE_NAME = "e2-raw-archive"
RAW_RENEW_DAYS = 30          # تجديدٌ إلزاميّ قبل الـ90 بفسحةٍ واسعة (حين لا تغيّر)
# 🔴 (2026-09-25 · عيبٌ في تصميمي أمسكه الاسترجاعُ الكامل `36095794496`): كان «الجديدُ أسبوعيًّا» والاسترجاعُ
#    الليليّ يرى **آخرَ 15 تشغيلة وحدَها** (‏≈4 أيام تداول بتشغيلات الاحتياط) ⇒ جلسةٌ تخرج من نافذته قبل الرفع
#    الأسبوعيّ **لا تدخل الأرشيفَ أبدًا** ⇒ أُلغي التأجيل: **كلُّ تغيّرٍ يُرفع** (`archive_upload_decision`).


def _raw_sessions(root):
    """`{تاريخ: مجلّد}` لمجلّدات `session_*` **مباشرةً** تحت الجذر (الأرشيفُ مسطَّح)."""
    out = {}
    if root and os.path.isdir(root):
        for d in sorted(os.listdir(root)):
            p = os.path.join(root, d)
            if d.startswith("session_") and os.path.isdir(p):
                out[d[len("session_"):]] = p
    return out


def _loops_of(sdir):
    try:
        return int(_read_json(os.path.join(sdir, "session.json")).get("loops_completed") or 0)
    except (TypeError, ValueError):
        return 0


def merge_raw_archive(prev_dir, cur_root, out_dir):
    """🗄️ **اتّحادُ** جلسات الأرشيف السابق وجلسات هذه التشغيلة في `out_dir` (يُشترَط فارغًا).
    تاريخٌ في الاثنين يفوز فيه **الأكثرُ دوراتٍ مكتملة** (قاعدةُ `recover`) والتعادلُ للسابق (لا تقلّب).
    **لا ينكمش بالبناء:** كلُّ تاريخٍ في السابق يبقى."""
    if os.path.isdir(out_dir) and os.listdir(out_dir):
        raise ValueError("مجلّدُ الأرشيف الجديد غيرُ فارغ: %s" % out_dir)
    prev, cur = _raw_sessions(prev_dir), _raw_sessions(cur_root)
    os.makedirs(out_dir, exist_ok=True)
    added, replaced = [], []
    for date in sorted(set(prev) | set(cur)):
        src = prev.get(date)
        if date in cur and (src is None or _loops_of(cur[date]) > _loops_of(src)):
            (replaced if src else added).append(date)
            src = cur[date]
        shutil.copytree(src, os.path.join(out_dir, "session_%s" % date))
    return {"prev": len(prev), "out": len(set(prev) | set(cur)), "added": added,
            "replaced": replaced, "dates": sorted(set(prev) | set(cur))}


def archive_upload_decision(prev_status, prev_age_days, n_prev, n_out, changed):
    """🗄️ نقيّة: هل يُرفع أرشيفُ الليلة؟ ⟵ `(نعم/لا، السبب)`. **لا يُرفع أصغرُ من السابق أبدًا** —
    وتعذّرُ تنزيل السابق يمنع الرفع (فيبقى السابقُ أحدثَ أرشيفٍ وتُعاد المحاولةُ الليلةَ التالية).
    **وكلُّ تغيّرٍ يُرفع** (جلسةٌ جديدةٌ أو مُستبدَلة) لأن نافذةَ الاسترجاع الليليّ آخرُ 15 تشغيلة فالتأجيلُ
    يُسقط ما يخرج منها قبل الرفع · وبلا تغيّرٍ يُجدَّد كلَّ `RAW_RENEW_DAYS` يومًا."""
    if prev_status == "failed":
        return False, "تعذّر تنزيلُ الأرشيف السابق ⇒ لا يُرفع أصغرُ منه (يُعاد الليلةَ التالية)"
    if n_out < n_prev:
        return False, "انكماش (%d ⟵ %d) ⇒ لا يُرفع" % (n_out, n_prev)
    if n_out == 0:
        return False, "أرشيفٌ فارغ ⇒ لا يُرفع (خطوةُ الرفع تشترط ملفّات)"
    if prev_status == "none":
        return True, "تأسيس"
    if changed:
        return True, "تغيّرٌ (%d جلسة)" % changed
    if prev_age_days is None:
        return True, "عمرُ السابق مجهول ⇒ يُجدَّد"
    if prev_age_days >= RAW_RENEW_DAYS:
        return True, "تجديدُ الاحتفاظ (عمرُ السابق %d يومًا)" % prev_age_days
    return False, "لا حاجة (لا تغيّر · عمرُ السابق %d يومًا)" % prev_age_days


def _age_days(created_iso, now=None):
    import datetime as _dt
    try:
        c = _dt.datetime.fromisoformat(str(created_iso).replace("Z", "+00:00"))
        n = now or _dt.datetime.now(_dt.timezone.utc)
        return max(0, (n - c).days)
    except (TypeError, ValueError):
        return None


def build_raw_archive(prev_dir, cur_root, out_dir, status_file="archive_prev_status",
                      flag_file="archive_upload.flag", repo_root=".", now=None):
    """🗄️ خطوةُ الـworkflow: يقرأ حالةَ تنزيل السابق (`ok <created>` · `none` · `failed`) ⟵ يتّحد ⟵ يقرّر
    الرفع ويكتب `flag_file` عند «نعم» ⟵ ويُعلن ما في الفهرس بلا خامٍ في الأرشيف (لا صمت)."""
    try:
        with open(status_file, encoding="utf-8") as fh:
            st = fh.read().split()
    except OSError:
        st = ["failed"]
    status = st[0] if st and st[0] in ("ok", "none", "failed") else "failed"
    age = _age_days(st[1], now) if status == "ok" and len(st) > 1 else None
    m = merge_raw_archive(prev_dir if status == "ok" else None, cur_root, out_dir)
    ok, why = archive_upload_decision(status, age, m["prev"], m["out"],
                                      len(m["added"]) + len(m["replaced"]))
    if ok:
        with open(flag_file, "w", encoding="utf-8") as fh:
            fh.write(why + "\n")
    idx = _read_json(os.path.join(repo_root, INDEX))
    missing = sorted(d for d in idx if d not in set(m["dates"]))
    print("🗄️ أرشيفُ الخام: %d جلسة (كان %d · جديدة %d · استُبدلت %d) · السابق: %s%s"
          % (m["out"], m["prev"], len(m["added"]), len(m["replaced"]), status,
             "" if age is None else " (عمرُه %d يومًا)" % age))
    print("   ⟵ %s: %s" % ("يُرفع" if ok else "لا يُرفع", why))
    print("   في الفهرس بلا خامٍ في الأرشيف: %s"
          % (("%d — %s" % (len(missing), ", ".join(missing[:8]) + (" …" if len(missing) > 8 else "")))
             if missing else "لا شيء"))
    return {**m, "status": status, "age": age, "upload": ok, "why": why, "missing": missing}


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--archive":
        if len(sys.argv) < 5:
            sys.exit("الاستعمال: e2_recover.py --archive <الأرشيف السابق> <e2_measurement> <مجلّد الأرشيف الجديد>")
        build_raw_archive(sys.argv[2], sys.argv[3], sys.argv[4])
        sys.exit(0)
    if len(sys.argv) < 2:
        sys.exit("الاستعمال: e2_recover.py <مجلّد تنزيلات artifacts>")
    recover(sys.argv[1])
