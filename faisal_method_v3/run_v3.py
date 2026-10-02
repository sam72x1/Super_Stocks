# -*- coding: utf-8 -*-
"""مُشغِّلُ workflow ‏faisal_v3.yml — يقرأ V3_MODE/V3_TICKER/V3_ASOF/V3_SEND ويوجّه للأداة."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)


# 📦 مخرَجُ كلّ وضعٍ يُطبع في السجلّ أيضًا (عطلٌ مُثبَت 2026-10-02: تنزيلُ الـartifact محجوبٌ من بيئة الجلسة بسياسة الشبكة
#    ⟵ نتيجةُ التشغيلة لا تُقرأ إلّا من السجلّ) · أجزاءٌ ثابتةُ الطول تُجمَّع بالترتيب · والغائبُ يُعلَن «missing» لا صمتًا.
EMIT = {"cases": "cases_summary.json", "validate": "w_validate.json", "poolcap": "pool_cap_audit.json"}
CHUNK = 3500


def emit(name, out_dir=None, chunk=CHUNK):
    import json
    p = os.path.join(out_dir or os.path.join(HERE, "out"), name)
    if not os.path.exists(p):
        print(f"V3OUT|{name}|missing")
        return 0
    s = json.dumps(json.load(open(p, encoding="utf-8")), ensure_ascii=False, separators=(",", ":"), default=str)
    n = max(1, (len(s) + chunk - 1) // chunk)
    for i in range(n):
        print(f"V3OUT|{name}|{i + 1}|{n}|{s[i * chunk:(i + 1) * chunk]}")
    return n


def main():
    mode = (os.environ.get("V3_MODE") or "ticker").strip()
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    if mode in EMIT:
        try:
            if mode == "cases":
                import faisal_cases
                return faisal_cases.main()
            if mode == "poolcap":
                import pool_cap_audit
                return pool_cap_audit.evaluate()
            import w_validate
            return w_validate.main()
        finally:
            emit(EMIT[mode])
    import faisal_tool as T
    sym = (os.environ.get("V3_TICKER") or "").strip().upper().lstrip("$")
    if not sym:
        print("⛔ ticker فارغ")
        return 2
    asof = (os.environ.get("V3_ASOF") or "").strip() or None
    send = (os.environ.get("V3_SEND") or "0").strip() == "1"
    out = os.path.join(HERE, "out")
    return T.run_ticker(sym, asof=asof, json_out=os.path.join(out, f"{sym}.json"),
                        png_out=os.path.join(out, f"{sym}.png"), send=send)


if __name__ == "__main__":
    raise SystemExit(main())
