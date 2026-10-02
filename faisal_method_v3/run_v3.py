# -*- coding: utf-8 -*-
"""مُشغِّلُ workflow ‏faisal_v3.yml — يقرأ V3_MODE/V3_TICKER/V3_ASOF/V3_SEND ويوجّه للأداة."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)


def main():
    mode = (os.environ.get("V3_MODE") or "ticker").strip()
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    if mode == "cases":
        import faisal_cases
        return faisal_cases.main()
    if mode == "poolcap":
        import pool_cap_audit
        return pool_cap_audit.evaluate()
    if mode == "validate":
        import w_validate
        return w_validate.main()
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
