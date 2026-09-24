# -*- coding: utf-8 -*-
"""🗓️🔍② `T-EARLY-2` — رقعةُ علم الإغلاق المبكّر تُطبَّق **وقتَ التشغيل** على شيفرة الحاكمة.

العقد: `early_rest_prereg.md` §③ (مدفوعٌ قبل هذا الملفّ وقبل أيّ رقم).

**لماذا رقعةٌ وقتَ التشغيل لا تعديلٌ في `main`:** شيفرةُ الأسر تغيّرت منذ حاكماتها (مثلًا
`first_anchor` ينادي `S.liq_stage_events` الإنتاجيّة التي أُضيف إليها الزنادُ الموازي `T-C`)،
فإعادتُها على `main` تقيس **الانجرافَ مع العلم**. والرقعةُ تُطبَّق على شيفرة الحاكمة نفسِها
(‏`head_sha` تشغيلتِها) فيبقى الفرقُ الوحيد العلمَ.

- **ثلاثُ مراسٍ لا رابعة**، كلٌّ في دالّةٍ واحدة: `kasih_scan.parse_day` · `pm_radar_scan.parse_pre`
  (خريطةُ «إغلاق الأمس» ‏≤16:00) · `event_exec.ny_session_key` (الجلسةُ النظاميّة [09:30، 16:00)).
  **تُرقَع وحدةُ الأسرة وحدَها** (فـ`pm_radar_scan` لم تكن موجودةً في شيفرات آب) · **والمرساةُ فريدةٌ
  وإلّا تتوقّف الرقعة قبل أيّ قراءة** (`V-R2`).
- **العلم `EARLY_CLOSE_CAL` يُقرأ `== "1"` حرفيًّا**: مطفأٌ ⇒ 16:00 = الشيفرةُ المنشورة سلوكًا ·
  مرفوعٌ ⇒ `close_ny_min` من `market_calendar` **اليوم** (يُنسَخ مع الرقعة باسم `early2_calendar.py`
  لأن تقويمَ الحاكمات لم يكن يعرف إغلاقاتِ 2023-2025) — **مكافئٌ لـ`presession_radar.reg_close_for`
  يومًا يومًا** (قفلٌ سلوكيّ في السويّة) · **ومرفوعٌ بلا تقويمٍ يسقط وقتَ التحميل** (لا عَلَمَ ميّتًا).
- **ومُدخَلاتُ الحاكمة تُقرأ من سجلّها** (`parse_gov_env`: كتلةُ `env:` في خطوة `Run python <سكربت>`)
  **بقائمةٍ بيضاء لكلّ أسرة** — لا نسخَ بيدٍ ولا مفتاحَ غريبًا ولا سرّ؛ والناقصُ يُسقط الرقعة.

🔒 قراءةٌ/قياسٌ فقط · الإنتاجُ لا يستوردها · لا `LOGIC_VERSION`.
"""
import os
import re
import shutil
import sys

FLAG = "EARLY_CLOSE_CAL"
CAL_COPY = "early2_calendar.py"

# ‏الأسرة ⟵ (السكربت · الوحدةُ المرقوعة · القائمةُ البيضاء لمُدخَلاتها) — أسماءُ workflow الحاكمة حرفيًّا
FAMILIES = {
    "kasih": ("kasih_scan.py", "kasih_scan.py", ("KASIH_YEAR", "KASIH_DAY")),
    "kasih2": ("kasih2_scan.py", "kasih_scan.py", ("KASIH_YEAR", "KASIH_DAY")),
    "exit_stop": ("exit_stop_arms.py", "kasih_scan.py", ("STOP_YEAR",)),
    "rearm": ("rearm_arms.py", "kasih_scan.py",
              ("REARM_YEAR", "REARM_DAY", "REARM_SYMS", "REARM_EXPECT")),
    "reclaim": ("reclaim_arms.py", "kasih_scan.py", ("RC_YEAR",)),
    "target10": ("target10_arms.py", "kasih_scan.py", ("TGT_YEAR", "TGT_DAY")),
    "pm_curve": ("pm_curve_scan.py", "pm_radar_scan.py", ("PMC_FROM", "PMC_TO")),
    "tc_arms": ("tc_arms.py", "pm_radar_scan.py", ("TCA_FROM", "TCA_TO")),
    "event_exec": ("event_exec_run.py", "event_exec.py",
                   ("BACKTEST_YEAR", "EVENT_EXEC_PROBE", "EVENT_EXEC_MAX_SYMBOLS", "BT_FROZEN_PATH")),
}

ANCHOR_CLOSES = "        if mod <= 16 * 60:\n            pc = closes.get(sym)\n"
NEW_CLOSES = "        if mod <= _early2_bound(day):\n            pc = closes.get(sym)\n"
ANCHOR_SESSION = "    if mod < 9 * 60 + 30 or mod >= 16 * 60:\n        return None\n"
NEW_SESSION = ("    if mod < 9 * 60 + 30 or mod >= _early2_bound(d.date().isoformat()):\n"
               "        return None\n")

PATCHES = {
    "kasih_scan.py": (ANCHOR_CLOSES, NEW_CLOSES),
    "pm_radar_scan.py": (ANCHOR_CLOSES, NEW_CLOSES),
    "event_exec.py": (ANCHOR_SESSION, NEW_SESSION),
}

HELPER = '''

# ── 🗓️🔍② T-EARLY-2 (`early_rest_patch.py`) — رقعةٌ وقتَ التشغيل لا شيفرةٌ منشورة ──────────
import os as _e2_os

_E2_ON = (_e2_os.environ.get("EARLY_CLOSE_CAL") or "").strip() == "1"
_E2_CACHE = {}
# 🔴 **التقويمُ يُستورَد وقتَ التحميل لا وقتَ النداء:** مرفوعٌ بلا تقويمٍ ⇒ تسقط التشغيلةُ صراحةً — لا حدَّ
#    16:00 صامتًا يجعل المرفوعةَ مطفأةً وهي تُعلن غيرَ ذلك (عَلَمٌ ميّت). أمسكه القفلُ السلوكيّ `ERK4`.
_E2_MC = None
if _E2_ON:
    import early2_calendar as _E2_MC


def _early2_bound(day):
    """مطفأٌ ⇒ 16:00 (الشيفرةُ المنشورة) · مرفوعٌ ⇒ `close_ny_min` من التقويم (13:00 يومَ الإغلاق
    المبكّر) · والمجهولُ أو الشاذّ ⇒ 16:00 (مرآةُ `reg_close_for`)."""
    if not _E2_ON:
        return 16 * 60
    b = _E2_CACHE.get(day)
    if b is None:
        try:
            cm = _E2_MC.session_info(day).get("close_ny_min")
        except Exception:  # noqa: BLE001
            cm = None
        b = cm if isinstance(cm, int) and not isinstance(cm, bool) and 0 < cm <= 16 * 60 else 16 * 60
        _E2_CACHE[day] = b
    return b
'''

_TS_RE = re.compile(r"^﻿?\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z ?")
_ENV_RE = re.compile(r"^\s+([A-Z][A-Z0-9_]*):(?: (.*))?$")


class PatchError(Exception):
    """فشلُ الرقعة ⇒ خروجٌ غيرُ صفريّ قبل أيّ قراءة (`V-R2`)."""


def patch_source(src: str, module: str) -> str:
    """يرقع نصَّ وحدةٍ واحدة — نقيّة. مرساةٌ غيرُ فريدة أو رقعةٌ سابقة ⇒ `PatchError`."""
    if module not in PATCHES:
        raise PatchError(f"وحدةٌ خارج العقد: {module}")
    old, new = PATCHES[module]
    if "_early2_bound" in src:
        raise PatchError(f"{module}: مرقوعةٌ سلفًا")
    n = src.count(old)
    if n != 1:
        raise PatchError(f"{module}: المرساةُ ×{n} (المطلوب مرّةٌ واحدة)")
    return src.replace(old, new, 1) + HELPER


def parse_gov_env(log_text: str, family: str) -> dict:
    """مُدخَلاتُ الحاكمة **من سجلّها** — نقيّة: كتلةُ `env:` في مجموعة `Run python <سكربت الأسرة>`
    الوحيدة، ومفاتيحُ القائمة البيضاء وحدَها. مجموعةٌ غائبةٌ/مكرّرة أو مفتاحٌ ناقص ⇒ `PatchError`."""
    if family not in FAMILIES:
        raise PatchError(f"أسرةٌ خارج العقد: {family!r}")
    script, _mod, allowed = FAMILIES[family]
    lines = [_TS_RE.sub("", ln.rstrip("\r")) for ln in (log_text or "").splitlines()]
    starts = [i for i, ln in enumerate(lines)
              if ln.startswith("##[group]Run python") and ln.split()[-1:] == [script]]
    if len(starts) != 1:
        raise PatchError(f"«Run python {script}» ×{len(starts)} في سجلّ الحاكمة (المطلوب مرّةٌ واحدة)")
    env, in_env = {}, False
    for ln in lines[starts[0] + 1:]:
        if ln.startswith("##[endgroup]"):
            break
        if ln.strip() == "env:":
            in_env = True
            continue
        m = _ENV_RE.match(ln) if in_env else None
        if m and m.group(1) in allowed:
            env[m.group(1)] = (m.group(2) or "").strip()
    missing = [k for k in allowed if k not in env]
    if missing:
        raise PatchError(f"مُدخَلاتٌ غائبة عن سجلّ الحاكمة: {missing}")
    return env


def env_lines(family: str, env: dict) -> list:
    """‏`E2_SCRIPT` ثمّ مُدخَلاتُ الحاكمة أسطرًا لـ`$GITHUB_ENV` — نقيّة، بقائمةٍ بيضاء للأسرة."""
    if family not in FAMILIES:
        raise PatchError(f"أسرةٌ خارج العقد: {family!r}")
    script, _mod, allowed = FAMILIES[family]
    out = [f"E2_SCRIPT={script}"]
    for k in sorted(env):
        v = env[k]
        if k not in allowed:
            raise PatchError(f"مفتاحٌ خارج قائمة {family}: {k!r}")
        if not isinstance(v, str) or "\n" in v or "\r" in v or len(v) > 200:
            raise PatchError(f"قيمةٌ مرفوضة لـ{k}")
        out.append(f"{k}={v}")
    return out


def apply(tree: str, family: str, cal_src: str) -> str:
    """يرقع وحدةَ الأسرة داخل شجرة الحاكمة وينسخ التقويم — يُرجع اسمَ الوحدة المرقوعة."""
    if family not in FAMILIES:
        raise PatchError(f"أسرةٌ خارج العقد: {family!r}")
    _script, module, _allowed = FAMILIES[family]
    p = os.path.join(tree, module)
    if not os.path.exists(p):
        raise PatchError(f"{module} غائبةٌ عن شيفرة الحاكمة")
    with open(p, encoding="utf-8") as fh:
        src = fh.read()
    out = patch_source(src, module)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(out)
    shutil.copyfile(cal_src, os.path.join(tree, CAL_COPY))
    return module


def main(argv) -> int:
    if len(argv) != 4:
        print("الاستعمال: early_rest_patch.py <شجرةُ الحاكمة> <الأسرة> <سجلُّ الحاكمة>", file=sys.stderr)
        return 2
    tree, family, log_path = argv[1], argv[2], argv[3]
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        with open(log_path, encoding="utf-8", errors="replace") as fh:
            env = parse_gov_env(fh.read(), family)
        lines = env_lines(family, env)
        module = apply(tree, family, os.path.join(here, "market_calendar.py"))
    except (PatchError, OSError) as e:
        print(f"⛔ الرقعة: {e}", file=sys.stderr)
        return 3
    # ⚠️ **stdout يذهب إلى `$GITHUB_ENV`** — لا يُطبَع عليه إلّا أسطرُ البيئة.
    print(f"🩹 رُقعت {module} في {tree} · {FLAG}={os.environ.get(FLAG, '')!r} (يُقرأ وقتَ التشغيل) · "
          f"مُدخَلاتُ الحاكمة من سجلّها: {', '.join(lines)}", file=sys.stderr)
    for ln in lines:
        print(ln)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
