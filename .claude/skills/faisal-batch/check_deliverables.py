#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧾 فاحصُ مخرجات مهارة `faisal-batch` — يُسقط ما يخالف **بنيةَ برومبت المالك حرفيًّا**
والشروطَ الثلاثة المضافة. لا يحكم على جودة التحليل؛ يحكم على ما يمكن فحصُه آليًّا.

الاستعمال:
    python3 .claude/skills/faisal-batch/check_deliverables.py <مجلّد المخرجات> [--rev <sha>]
    --rev: يقرأ كودَ المستودع من هذا الالتزام (الذي ثُبّتت عليه الحزمة) لا من الشجرة الحاليّة.
الخروج: 0 مطابق · 1 مخالفة (تُطبَع كلُّها) · 2 ملفٌّ/مجلّدٌ غائب.
"""
import ast
import os
import re
import subprocess
import sys

FILES = ("OPUS_EXECUTION_SPEC.md", "SOURCE_ANALYSIS.md", "REQUIREMENTS_MATRIX.md",
         "UNCERTAINTIES.md")
SECTIONS = ("OBJECTIVE", "SOURCE MATERIAL", "MASTER KNOWLEDGE BASE", "VERIFIED FACTS",
            "DERIVED RULES", "PATTERNS", "CONSTRAINTS", "EDGE CASES",
            "IMPLEMENTATION REQUIREMENTS", "SYSTEM ARCHITECTURE", "ALGORITHMS / LOGIC",
            "INPUTS", "OUTPUTS", "VALIDATION", "TEST PLAN", "FAILURE CONDITIONS",
            "UNCERTAINTIES", "IMPLEMENTATION ORDER", "DO NOT", "FINAL ACCEPTANCE CRITERIA")
PHASES = ("Repository Inspection", "Understand Existing Architecture",
          "Map Requirements to Existing System", "Identify Gaps", "Implement", "Test",
          "Validate Against Source Requirements", "Review for Regression", "Final Report")
PHASE_FIELDS = ("OBJECTIVE", "FILES", "CHANGES", "DEPENDENCIES", "TESTS",
                "EXPECTED RESULT", "FAILURE CONDITIONS")
KB_FIELDS = ("SOURCE", "TYPE", "CONTENT", "INTERPRETATION", "IMPORTANCE", "EVIDENCE",
             "RELATED_ITEMS", "IMPLEMENTATION_IMPACT", "CONFIDENCE")
CONF = ("CONFIRMED", "STRONGLY_SUPPORTED", "LIKELY", "UNCERTAIN")
LABELS = ("GENERAL RULE", "POSSIBLE RULE", "EXAMPLE", "UNKNOWN")
MATRIX = ("SOURCE", "INFORMATION", "REQUIREMENT", "IMPLEMENTATION", "TEST")
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


_CACHE = {}


def _src(path, rev):
    """نصُّ ملفٍّ من المستودع — من الالتزام `rev` إن مُرِّر وإلّا من الشجرة (مخبَّأ)."""
    if (path, rev) not in _CACHE:
        _CACHE[(path, rev)] = _src_raw(path, rev)
    return _CACHE[(path, rev)]


def _defs(src):
    """[(بداية، نهاية، اسم، نوع)] لكلّ دالّةٍ/صنف — تُحلَّل الشجرةُ **مرّةً** لكلّ نصّ
    (كانت تُحلَّل لكلّ سطرٍ في المدى: ملفٌّ من 58 ألف سطر × 336 سطرًا ⇒ دقائق)."""
    key = ("defs", id(src))
    if key not in _CACHE:
        try:
            tree = ast.parse(src)
            out = [(n.lineno, n.end_lineno or n.lineno, n.name, type(n).__name__)
                   for n in ast.walk(tree)
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
            for n in tree.body:            # مستوى الوحدة: `CONFIG = {…}` يملك أسطرَه
                if isinstance(n, (ast.Assign, ast.AnnAssign)):
                    tg = n.targets[0] if isinstance(n, ast.Assign) else n.target
                    if isinstance(tg, ast.Name):
                        out.append((n.lineno, n.end_lineno or n.lineno, tg.id, "Assign"))
            _CACHE[key] = out
        except Exception:                                        # noqa: BLE001
            _CACHE[key] = []
    return _CACHE[key]


def _src_raw(path, rev):
    try:
        if rev:
            return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=REPO,
                                  capture_output=True, text=True, check=True).stdout
        return open(os.path.join(REPO, path), encoding="utf-8").read()
    except Exception:                                            # noqa: BLE001
        return None


def _owner(src, line):
    """أعمقُ دالّةٍ/صنفٍ يحوي السطر (بالـAST) أو None."""
    best = None
    for a, b, name, _ in _defs(src):
        if a <= line <= b and (best is None or a > best[0]):
            best = (a, name)
    return best[1] if best else None


def _headings(text):
    return [(i, ln.lstrip("#").strip()) for i, ln in enumerate(text.splitlines())
            if ln.startswith("#")]


def check(folder, rev=None):
    bad = []
    txt = {}
    for f in FILES:
        p = os.path.join(folder, f)
        if not os.path.isfile(p):
            print(f"⛔ غائب: {p}")
            return 2
        txt[f] = open(p, encoding="utf-8").read()
    spec, sa = txt["OPUS_EXECUTION_SPEC.md"], txt["SOURCE_ANALYSIS.md"]

    # ① أقسامُ المالك العشرون **بأسمائها وترتيبها** عناوينَ في الحزمة
    heads = _headings(spec)
    pos = -1
    for s in SECTIONS:
        hit = next((i for i, h in heads if i > pos and s.upper() in h.upper()), None)
        if hit is None:
            bad.append(f"قسمُ المالك غائبٌ أو خارجَ ترتيبه: «{s}»")
        else:
            pos = hit
    # ② مراحلُ المالك التسع بأسمائها وترتيبها · وكلُّ عنوانِ PHASE يحمل الحقولَ السبعة
    lines = spec.splitlines()
    ph = [(i, h) for i, h in heads if re.search(r"\bPHASE\b", h.upper())]
    pos = -1
    for p in PHASES:
        hit = next((i for i, h in ph if i > pos and p.upper() in h.upper()), None)
        if hit is None:
            bad.append(f"مرحلةُ المالك غائبةٌ أو خارجَ ترتيبها: «{p}»")
        else:
            pos = hit
    for k, (i, h) in enumerate(ph):
        end = next((j for j, _ in heads if j > i and (j in dict(ph) or
                    lines[j].startswith("## "))), len(lines))
        blk = "\n".join(lines[i:end]).upper()
        miss = [f for f in PHASE_FIELDS if f not in blk]
        if miss:
            bad.append(f"«{h[:40]}» ينقصها: {', '.join(miss)}")
    # ③ قاعدةُ المعرفة: كلُّ عنصرٍ يبدأ بـID ويحمل الحقولَ العشرة · ثقةٌ من الأربع · ووسمٌ من الأربعة
    ids = [m.start() for m in re.finditer(r"(?m)^\s*[-*]?\s*\**\s*ID\s*\**\s*:", sa)]
    if not ids:
        bad.append("قاعدةُ المعرفة: لا عنصرَ يبدأ بحقل «ID:»")
    for a, b in zip(ids, ids[1:] + [len(sa)]):
        ent = sa[a:b]
        eid = ent.split("\n", 1)[0].strip()[:30]
        miss = [f for f in KB_FIELDS
                if not re.search(r"(?m)^\s*[-*]?\s*\**\s*" + re.escape(f) + r"\s*\**\s*:", ent)]
        if miss:
            bad.append(f"{eid}: حقولٌ غائبة {', '.join(miss)}")
        cm = re.search(r"CONFIDENCE\s*\**\s*:([^\n]*)", ent)
        if cm and not any(c in cm.group(1) for c in CONF):
            bad.append(f"{eid}: الثقةُ ليست من {CONF}")
        if not any(lb in ent for lb in LABELS):
            bad.append(f"{eid}: بلا وسمٍ من {LABELS}")
    # ④ المصفوفة: ترويسةٌ بالأعمدة الخمسة بترتيبها
    ok = False
    for ln in txt["REQUIREMENTS_MATRIX.md"].splitlines():
        if ln.lstrip().startswith("|"):
            u, p = ln.upper(), -1
            idx = [u.find(c) for c in MATRIX]
            if all(x >= 0 for x in idx) and idx == sorted(idx):
                ok = True
                break
    if not ok:
        bad.append("المصفوفة: لا ترويسةَ SOURCE → INFORMATION → REQUIREMENT → IMPLEMENTATION → TEST")
    # ⑤ الشرط ①: كلُّ إحالةِ سطرٍ تُسمّي بجوارها الدالّةَ التي تملكه فعلًا (بالـAST)
    ref = re.compile(r"`((?:[\w./-]+\.py)?):(\d{2,6})(?:-(\d+))?`|\b([\w./-]+\.py):(\d{2,6})\b")
    span = re.compile(r"`([^`]+)`")
    for ln in lines:
        for m in ref.finditer(ln):
            f = (m.group(1) or m.group(4) or "Super_stock.py")
            n = int(m.group(2) or m.group(5))
            n2 = int(m.group(3)) if m.group(3) else n
            src = _src(f, rev)
            if src is None:
                continue
            sl = src.splitlines()
            near = set()
            for t in span.finditer(ln):
                if t.start() != m.start() and abs(t.start() - m.start()) <= 90:
                    near |= set(re.findall(r"[A-Za-z_]\w{2,}", t.group(1)))
            owns = {_owner(src, n)} - {None}
            if owns:
                if not owns & near:
                    bad.append(f"الشرط ①: `{f}:{n}` داخل `{sorted(owns)[0]}` ولا تُسمّيه الحزمةُ "
                               f"بجوارها (سمّت: {sorted(near)[:5] or '—'})")
                continue
            # سطرٌ خارج الدوالّ (مفاتيح/فراغ): يكفي رمزٌ قريبٌ في نصّ المدى، أو دالّةٌ مسمّاةٌ
            # **تنتهي قبله أو تبدأ بعده بثلاثة أسطر** («بعد X»/«قبل X»)
            txt_rng = "\n".join(sl[max(0, n - 1):min(len(sl), n2)])
            defs = {nm: (a, b) for a, b, nm, kind in _defs(src)
                    if kind in ("FunctionDef", "AsyncFunctionDef")}
            adj = any(nm in defs and (n - 3 <= defs[nm][1] <= n or n <= defs[nm][0] <= n + 3)
                      for nm in near)
            if not (adj or any(t in txt_rng for t in near)):
                bad.append(f"الشرط ①: `{f}:{n}` بلا اسمٍ يطابق نصَّ المدى أو دالّةً مجاورة")
    # ⑥ الشرط ②: كلُّ مفتاحٍ جديد (`KEY=رقم` غيرُ موجودٍ في الكود) يرافقه «مِجَسّ:»/PROBE
    code = _src("Super_stock.py", rev) or ""
    for key in sorted(set(re.findall(r"`([A-Z][A-Z0-9_]{3,})=[\d.]+`", spec))):
        if f'"{key}"' in code or key.startswith(("PYTHON", "GITHUB_", "TELEGRAM_", "POLYGON_")):
            continue
        if not any(key in ln and ("مِجَسّ" in ln or "PROBE" in ln.upper()) for ln in lines):
            bad.append(f"الشرط ②: المفتاحُ الجديد `{key}` بلا سطر «مِجَسّ:/PROBE» بمثاله")
    # ⑦ الشرط ③: كلُّ «إعادة استعمال» لدالّةٍ قائمة تذكر لأيّ لحظةٍ بُنيت
    # «كما هي» و«تُستدعى» إعادةُ استعمالٍ أيضًا — وهي صيغةُ الخطأ الأوّل حرفيًّا
    #  («الفرعُ ثبات = `method_sequence(df, win)` كما هي» — وكانت ستُخفي المرحلة 4)
    reuse = re.compile(r"استعمال|استخدام|تُستدعى|يُستدعى|تستدعي|يستدعي|كما هي|reuse", re.I)
    for ln in lines:
        if reuse.search(ln):
            for t in span.finditer(ln):
                name = (re.match(r"[A-Za-z_]\w*", t.group(1)) or [""])[0]
                if re.search(r"(?m)^\s*def " + re.escape(name) + r"\(", code) and \
                        not ("بُنيت ل" in ln or "BUILT_FOR" in ln.upper()):
                    bad.append(f"الشرط ③: إعادةُ استعمال `{name}` بلا «بُنيت لـ…/BUILT_FOR»")
    for b in bad:
        print("❌ " + b)
    print(f"{'✅ مطابق' if not bad else f'⛔ {len(bad)} مخالفة'} — {folder}")
    return 1 if bad else 0


if __name__ == "__main__":
    a = sys.argv[1:]
    rv = None
    if "--rev" in a:
        i = a.index("--rev")
        rv = a[i + 1] if i + 1 < len(a) else None
        a = a[:i] + a[i + 2:]
    raise SystemExit(check(a[0] if a else ".", rv))
