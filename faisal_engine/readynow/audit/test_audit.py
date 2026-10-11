"""READY NOW audit guards — run from the repo root:  python3 faisal_engine/readynow/audit/test_audit.py  (exit 0 = pass)

A1  APP_POS is exactly NEAR15 ∧ BOUNCE10_40 (boundaries included, missing fields false)
A2  a changed APP_POS_PREREG.md is refused (exit 9) before any read; the sealed one is accepted
A3  the chip-parity audit regenerates byte-identically (rn_chip_parity.py)            [slow; R70_FAST=1 skips]
A4  the seed audit regenerates byte-identically (rn_seed_audit.py)
A5  the APP_POS evaluator uses READYNOW's sealed windows, resamples, seed and alphas unchanged
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RN = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(RN))
sys.path.insert(0, HERE)
sys.path.insert(0, RN)
os.environ["FAISAL_ONLY"] = "1"
import rn_app_eval as A                                                   # noqa: E402
import rn_eval as V                                                       # noqa: E402
import rn_lib as K                                                        # noqa: E402

FAILS = []


def check(name, ok, info=""):
    print(("✅ " if ok else "❌ ") + name + (f" — {info}" if info else ""))
    if not ok:
        FAILS.append(name)


def a1():
    try:
        f = A.app_pos
        ok = (f({"dist": "15", "bounce": "10"}) and f({"dist": "0", "bounce": "40"}) and not f({"dist": "15.01", "bounce": "20"})
              and not f({"dist": "5", "bounce": "9.99"}) and not f({"dist": "5", "bounce": "40.01"})
              and not f({"dist": "", "bounce": "20"}) and not f({"dist": "5"}))
        info = ""
    except Exception as e:                                                # noqa: BLE001
        ok, info = False, f"⛔ {type(e).__name__}: {e}"
    check("A1 APP_POS = within 15% ∧ bounce 10–40% (boundaries · missing fields false)", ok, info)


def a2():
    tmp = tempfile.mkdtemp()
    try:
        fake = os.path.join(tmp, "APP_POS_PREREG.md")
        open(fake, "wb").write(open(A.PREREG, "rb").read() + b"\n")
        sealed = A.prereg_ok()
        code = ("import sys; sys.path.insert(0, %r); sys.path.insert(0, %r); import rn_app_eval as A; A.PREREG = %r; "
                "A.rd = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('read before the seal check')); "
                "A.K.rd = A.rd; A.final()" % (HERE, RN, fake))
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT)
        ok = sealed and r.returncode == 9 and "read before the seal check" not in (r.stdout + r.stderr)
        info = f"sealed {sealed} · rc={r.returncode}"
    except Exception as e:                                                # noqa: BLE001
        ok, info = False, f"⛔ {type(e).__name__}: {e}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    check("A2 a changed APP_POS specification is refused (exit 9) before any read · sealed one accepted", ok, info)


def regen(script, out):
    p = os.path.join(HERE, "data", out)
    before = open(p, "rb").read()
    r = subprocess.run([sys.executable, os.path.join(HERE, script)], capture_output=True, text=True, cwd=ROOT,
                       env=dict(os.environ, GIT_ALLOW_PROTOCOL="file"))
    after = open(p, "rb").read()
    if after != before:
        open(p, "wb").write(before)
    return r.returncode == 0 and after == before, r.returncode


def a3():
    if os.environ.get("R70_FAST") == "1":
        print("⏭️ A3 skipped (R70_FAST=1)")
        return
    ok, rc = regen("rn_chip_parity.py", "chip_parity.json")
    check("A3 chip-parity audit regenerates identically", ok, f"rc={rc}")


def a4():
    ok, rc = regen("rn_seed_audit.py", "seed_audit.json")
    check("A4 seed audit regenerates identically", ok, f"rc={rc}")


def a5():
    try:
        spec = open(A.PREREG, encoding="utf-8").read()
        rn_spec = open(V.PREREG, encoding="utf-8").read()
        ok = (A.OOS == V.OOS and A.REPS == V.REPS and A.SEED == V.SEED and A.ALPHA_W == V.ALPHA_W
              and A.ALPHA_P == V.ALPHA_P and A.FLOORS == V.FLOORS and V.prereg_ok()
              and all(f"{w} {K.WINDOWS[w][0]} → {K.WINDOWS[w][1]}" in rn_spec for w in A.OOS)
              and bool(re.search(r"2,000 resamples, seed 20261011", spec)))
        info = f"OOS {A.OOS} · reps {A.REPS} · seed {A.SEED}"
    except Exception as e:                                                # noqa: BLE001
        ok, info = False, f"⛔ {type(e).__name__}: {e}"
    check("A5 APP_POS uses READYNOW's sealed windows, resamples, seed, alphas and floors", ok, info)


if __name__ == "__main__":
    a1()
    a2()
    a3()
    a4()
    a5()
    print(f"\nالفاشل: {len(FAILS)}" + (" — " + ", ".join(FAILS) if FAILS else ""))
    sys.exit(1 if FAILS else 0)
