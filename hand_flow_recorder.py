"""🤖🖐️ المرحلة 1 — حصّاد التدفق الحيّ لليد الاصطناعية (بحث/جدوى فقط · صفر مسّ إنتاج).

بعد ضوء المرحلة 0 الأخضر (1.72× OOS من بيانات يومية فقيرة)، يبني هذا الحصّاد **البيانات
الحقيقية** التي ينقص وجودها للوكيل: كل **مسح** يُرصَد حيًّا → نسجّل **ميزات الامتصاص اللحظية**
(Polygon: امتصاص على الطلب · جدار الطلب · حصّة الدارك) + **النتيجة** (هدف قبل وقف) لاحقًا.
نفس فلسفة E2-A (قياس prospective صادق قبل أي نموذج).

**🔴 خطوط حمراء:** فاشل-آمن مطلق · append-only crash-safe (كل حدث سطر JSONL) · لا أسرار
تُكتب · بلا مفتاح Polygon = لا عمل · **خارج مسار الفرز/الإنتاج بالكامل** (بحث فقط).

المحور العلمي: القرار الأثمن ليد فيصل = «هل هذا مسح (أعِد الدخول) أم كسر (اخرج)؟». الفرق =
**الامتصاص عند قاع المسح** (`bid_block_shares`: بائع يضرب الطلب والمضارب يمتصّه). نسجّله + النتيجة.

التشغيل الحيّ: عبر `hand_flow_collect.py` (HAND_COLLECT=1). اختبار ذاتي: `python hand_flow_recorder.py --selftest`
"""
import os
import sys
import json
import time

LOG_PATH = os.environ.get("HAND_FLOW_LOG", "hand_flow_log.jsonl")
SCHEMA = 1


def sweep_flow_features(of, flow=None):
    """ميزات الامتصاص من مخرجات `operator_flow` (+`polygon_flow`/`acc_components` اختياري).
    نقيّة فاشلة-آمنة → dict مسطّح (أو {}). المحور `absorption` = حصّة الطبعات على الطلب
    (المضارب يمتصّ المسح) من إجمالي الطبعات الكبيرة = بصمة «مسح لا كسر»."""
    f = {}
    try:
        if of:
            bb = float(of.get("buy_block_shares") or 0)      # شراء عدواني (إشعال)
            db = float(of.get("bid_block_shares") or 0)      # على الطلب (امتصاص المسح)
            f["buy_block"] = bb
            f["bid_block"] = db
            f["absorption"] = (db / (db + bb)) if (db + bb) > 0 else None
            f["n_blocks"] = of.get("n_blocks")
            f["has_operator"] = bool(of.get("has_operator"))
            bid, ask = of.get("bid"), of.get("ask")
            if bid and ask and float(ask) > 0:
                f["spread_pct"] = (float(ask) - float(bid)) / float(ask) * 100.0
                bs, asz = of.get("bid_size"), of.get("ask_size")
                f["bid_size"] = bs
                f["ask_size"] = asz
                if bs and asz and float(asz) > 0:
                    f["wall_ratio"] = float(bs) / float(asz)   # جدار الطلب ÷ العرض
        if flow:
            for k_src, k_dst in (("aggressive_buy_pct", "agg_buy_pct"),
                                 ("dark_share_pct", "dark_pct"),
                                 ("block_share_pct", "block_pct"),
                                 ("buy_pct", "buy_pct")):
                if flow.get(k_src) is not None:
                    f[k_dst] = flow.get(k_src)
    except Exception:
        pass
    return f


def _sweep_outcome(bars, entry, target_pct, stop_pct):
    """نتيجة المسح من شموع أمامية `[(high, low), ...]` بعد الدخول: هدف قبل وقف (الوقف أولًا)؟
    يرجّع 'win' / 'loss' / 'pending'. نقيّة فاشلة-آمنة."""
    try:
        e = float(entry)
        if e <= 0:
            return "pending"
        tgt = e * (1.0 + target_pct / 100.0)
        stp = e * (1.0 - stop_pct / 100.0)
        for hi, lo in bars:
            if float(lo) <= stp:          # الوقف أولًا (أسوأ حالة)
                return "loss"
            if float(hi) >= tgt:          # الهدف
                return "win"
        return "pending"
    except Exception:
        return "pending"


class HandFlowRecorder:
    """مسجّل append-only crash-safe (JSONL، كل حدث سطر). فاشل-آمن مطلق — لا يرمي أبدًا."""

    def __init__(self, path=None):
        self.path = path or LOG_PATH

    def record_sweep(self, symbol, support, sweep_low, entry, features,
                     ts=None, meta=None):
        """يسجّل حدث مسح مرصود (النتيجة 'pending' حتى تُحسم لاحقًا). يرجّع True/False."""
        rec = {"schema": SCHEMA, "symbol": symbol,
               "ts": float(ts) if ts is not None else time.time(),
               "support": support, "sweep_low": sweep_low, "entry": entry,
               "features": features or {}, "outcome": "pending", "meta": meta or {}}
        try:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            return True
        except Exception:
            return False

    def load(self):
        out = []
        try:
            with open(self.path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        pass
        except FileNotFoundError:
            pass
        except Exception:
            pass
        return out

    def resolve_pending(self, fetch_bars, target_pct=100.0, stop_pct=7.0, horizon=60):
        """يحسم المعلّقات: `fetch_bars(symbol, since_ts) → [(high, low), ...]` (فاشل-آمن).
        يعيد كتابة السجل ذرّيًّا (tmp+replace). يرجّع عدد المحسومة حديثًا."""
        recs = self.load()
        changed = 0
        for r in recs:
            if r.get("outcome") != "pending":
                continue
            try:
                bars = fetch_bars(r.get("symbol"), r.get("ts"))
                if not bars:
                    continue
                oc = _sweep_outcome(bars[:horizon], r.get("entry"), target_pct, stop_pct)
                if oc != "pending":
                    r["outcome"] = oc
                    changed += 1
            except Exception:
                continue
        if changed:
            try:
                tmp = self.path + ".tmp"
                with open(tmp, "w", encoding="utf-8") as fh:
                    for r in recs:
                        fh.write(json.dumps(r, ensure_ascii=False) + "\n")
                os.replace(tmp, self.path)
            except Exception:
                pass
        return changed

    def summary(self):
        """ملخّص: أعداد pending/win/loss + (عند حسم كافٍ) امتصاص المحسومة الرابحة مقابل الخاسرة."""
        recs = self.load()
        n = len(recs)
        win = sum(1 for r in recs if r.get("outcome") == "win")
        loss = sum(1 for r in recs if r.get("outcome") == "loss")
        pend = n - win - loss
        lines = [f"🖐️ حصّاد التدفق: {n} حدث · محسوم {win+loss} (✅{win}/🛑{loss}) · معلّق {pend}"]
        dec = [r for r in recs if r.get("outcome") in ("win", "loss")]
        if len(dec) >= 20:
            def _abs(r):
                return (r.get("features") or {}).get("absorption")
            wabs = [_abs(r) for r in dec if r.get("outcome") == "win" and _abs(r) is not None]
            labs = [_abs(r) for r in dec if r.get("outcome") == "loss" and _abs(r) is not None]
            if wabs and labs:
                lines.append(f"  امتصاص متوسط: الرابحة {sum(wabs)/len(wabs):.2f} · "
                             f"الخاسرة {sum(labs)/len(labs):.2f} "
                             "(أعلى للرابحة = «مسح لا كسر» يتنبّأ)")
        else:
            lines.append(f"  عيّنة محسومة قليلة (<20) — تتراكم حيًّا. لا حكم بعد.")
        return "\n".join(lines)


def _selftest():
    ok = True

    def chk(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("✅" if cond else "❌") + " " + name)

    # sweep_flow_features
    of = {"buy_block_shares": 2000, "bid_block_shares": 8000, "n_blocks": 5,
          "has_operator": True, "bid": 1.00, "ask": 1.05, "bid_size": 500, "ask_size": 100}
    f = sweep_flow_features(of, {"aggressive_buy_pct": 0.6, "dark_share_pct": 0.3})
    chk("features: امتصاص = 8000/(8000+2000) = 0.80", abs(f["absorption"] - 0.80) < 1e-9)
    chk("features: سبريد ≈ 4.76%", abs(f["spread_pct"] - (0.05 / 1.05 * 100)) < 1e-6)
    chk("features: جدار الطلب/العرض = 5.0", abs(f["wall_ratio"] - 5.0) < 1e-9)
    chk("features: dark_pct مُمرَّر", f.get("dark_pct") == 0.3)
    chk("features: بلا مدخل → {}", sweep_flow_features(None) == {})
    # _sweep_outcome
    chk("outcome: هدف قبل وقف → win",
        _sweep_outcome([(1.1, 0.98), (2.1, 1.0)], 1.0, 100, 7) == "win")
    chk("outcome: وقف أولًا → loss",
        _sweep_outcome([(1.05, 0.90)], 1.0, 100, 7) == "loss")
    chk("outcome: لا هذا ولا ذاك → pending",
        _sweep_outcome([(1.2, 0.95)], 1.0, 100, 7) == "pending")
    # recorder round-trip + resolve
    import tempfile
    p = os.path.join(tempfile.gettempdir(), "hand_flow_selftest.jsonl")
    try:
        os.remove(p)
    except OSError:
        pass
    rec = HandFlowRecorder(p)
    chk("recorder: تسجيل ينجح", rec.record_sweep("AAA", 1.0, 0.93, 1.02, f, ts=1000.0))
    rec.record_sweep("BBB", 2.0, 1.86, 2.05, {}, ts=1001.0)
    chk("recorder: تحميل حدثين", len(rec.load()) == 2)

    def _fetch(sym, since):
        return {"AAA": [(2.10, 1.0)], "BBB": [(2.0, 1.80)]}.get(sym, [])
    ch = rec.resolve_pending(_fetch, target_pct=100, stop_pct=7)
    recs = rec.load()
    aaa = [r for r in recs if r["symbol"] == "AAA"][0]
    bbb = [r for r in recs if r["symbol"] == "BBB"][0]
    chk("resolve: AAA هدف +100% → win", aaa["outcome"] == "win")
    chk("resolve: BBB وقف −7% → loss", bbb["outcome"] == "loss")
    chk("resolve: حَسَم اثنين", ch == 2)
    chk("resolve: لا يعيد حسم المحسوم", rec.resolve_pending(_fetch) == 0)
    try:
        os.remove(p)
    except OSError:
        pass
    print("\n" + ("✅✅ الاختبار الذاتي نجح" if ok else "❌ فشل الاختبار الذاتي"))
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if _selftest() else 1)
    print(HandFlowRecorder().summary())
