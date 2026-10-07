# -*- coding: utf-8 -*-
"""
🧊 FAISAL V4.1 — تجميدُ V4 (§1 من مهمّة «V4.1 EVIDENCE HARDENING + PROSPECTIVE VALIDATION» · العقد `V41_prereg.md` §②).

V4 هو **المرشَّحُ تحت الاختبار**: هذه الأداةُ تسجّل بصمةَ كلِّ ملفٍّ يحدّد منهجَه (المحرّك · القواعد · الحالات · الوسوم · التقييم ·
الفِكستشرات · السجلّات · الوثائق) وكلَّ تبعيّةٍ يقرؤها V4 من V3.1 · ولقطةَ الإعداد الحيّة (PARAMS · STATE_* · سجلُّ القواعد) ·
وجردَ النتائج المنشورة (السويّة · الطفرات · الذهبيّة · H-STATE · H-LEVEL) — في `docs/V4_FREEZE_MANIFEST.json` · وتقريرًا مقروءًا.

⚖️ لا يغيّر شيئًا في V4: يقرأ ويحسب البصمات فقط · و`verify()` هو قلبُ القفل FV41:
  • كلُّ ملفٍّ مجمَّد بصمتُه = المسجَّلة · ولا ملفَّ أُضيف أو حُذف تحت `faisal_method_v4/` (عدا __pycache__ و`out/` وقتَ التشغيل).
  • `freeze_id` يُعاد حسابُه من خريطة البصمات · وبصمةُ الإعداد الحيّ (استيرادُ المحرّك والسجلّ) = المسجَّلة.
  • المراجعاتُ (`revisions`) لا تقبل إلّا **خطأَ تنفيذ** بقفلِ ارتدادٍ وقائمةِ تشغيلاتٍ مُبطَلة (§30) — **تغييرُ المنهج ممنوعٌ بالبناء**.
والتبعيّاتُ الجالبةُ للبيانات (`tv_data.py` · `market_calendar.py` · `Super_stock.py`) **تُسجَّل ولا تُجمَّد**: ليست منهجًا
وتتغيّر لإصلاح الإنتاج ⟵ تُختم بصمتُها في كلّ تشغيلةٍ أماميّة بدلًا من ذلك (`runner.py`).
"""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
V4_DIR = "faisal_method_v4"
DOCS = os.path.join(HERE, "docs")
MANIFEST = os.path.join(DOCS, "V4_FREEZE_MANIFEST.json")
REPORT = os.path.join(DOCS, "V4_FREEZE_REPORT.md")
FREEZE_VERSION = "V4.1-FREEZE 1.0 (2026-10-07)"

# تبعيّاتُ V4 خارج مجلّده (منهجٌ ودليلٌ يقرؤه كودُ V4) — تُجمَّد معه
FROZEN_EXTRA = (
    ".github/workflows/faisal_v4.yml",
    "faisal_method_v3/faisal_tool.py",
    "faisal_method_v3/image_corpus.json",
    "faisal_method_v3/dedup_clusters.json",
    "faisal_method_v3/source_access.json",
    "faisal_method_v3/v31/golden_fixtures.json",
    "faisal_method_v3/v31/golden_cases_v31.json",
    "faisal_method_v3/v31/reconcile_v31.json",
    "faisal_method_v3/v31/rule_audit_v31.json",
)
# الجالبون (اكتسابُ بيانات لا منهج) — بصمةٌ تُسجَّل ولا تُجمَّد
RECORDED_DEPS = ("tv_data.py", "market_calendar.py", "Super_stock.py")
# نواةُ المحرّك — آخرُ تغييرٍ فيها هو لحظةُ تجميد المنهج الفعليّة
ENGINE_CORE = ("faisal_method_v4/decision_engine.py", "faisal_method_v4/rules_v4.py", "faisal_method_v4/v4_cases.py",
               "faisal_method_v4/v4_eval.py", "faisal_method_v4/v4_run.py", "faisal_method_v4/data/case_labels_v4.json",
               "faisal_method_v4/data/visual_pass_v4.jsonl", "faisal_method_v4/V4_prereg.md", "faisal_method_v3/faisal_tool.py")
SKIP_DIRS = {"__pycache__", "out"}
REVISION_CLASSES = {"INITIAL", "IMPLEMENTATION_BUG"}         # §30: لا مراجعةَ «منهجيّة» أبدًا


def canon(obj):
    """JSON قانونيّ (مفاتيحُ مرتّبة · بلا مسافات) — أساسُ كلّ بصمة."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def frozen_files(root=ROOT):
    """القائمةُ المجمَّدة مرتّبة: كلُّ ملفٍّ تحت faisal_method_v4/ (عدا مخلّفات التشغيل) ‏+ FROZEN_EXTRA."""
    out = []
    base = os.path.join(root, V4_DIR)
    for d, dirs, files in os.walk(base):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
        for fn in sorted(files):
            if fn.endswith((".pyc", ".pyo")):
                continue
            out.append(os.path.relpath(os.path.join(d, fn), root).replace(os.sep, "/"))
    out += [p for p in FROZEN_EXTRA]
    return sorted(set(out))


def file_hashes(paths, root=ROOT):
    return {p: sha256_file(os.path.join(root, p)) for p in paths}


def freeze_id(hashes):
    return sha256_bytes(canon(hashes).encode("utf-8"))


def _import_v4(root=ROOT):
    v4 = os.path.join(root, V4_DIR)
    for p in (v4, os.path.join(root, "faisal_method_v3")):
        if p not in sys.path:
            sys.path.insert(0, p)
    import decision_engine as E      # noqa: E402
    import rules_v4 as RV            # noqa: E402
    return E, RV


def config_snapshot(root=ROOT):
    """لقطةُ الإعداد الحيّ من الاستيراد (لا من النصّ): نسخةُ المحرّك والسجلّ · PARAMS · STATE_DECISION/RULE · جردُ القواعد."""
    E, RV = _import_v4(root)
    params = {k: {"value": (list(v[0]) if isinstance(v[0], tuple) else v[0]), "source": v[1], "basis": v[2]}
              for k, v in E.PARAMS.items()}
    rules = {}
    for rid, r in sorted(RV.RULES_V4.items()):
        rules[rid] = {k: r.get(k) for k in ("active", "status", "decisionality", "source_level", "source", "author",
                                            "image_ids", "supporting", "contradicting", "golden_witness", "params",
                                            "superseded_by", "backtest_derived", "effect", "description")}
    snap = {"engine_version": E.ENGINE_VERSION, "rules_version": RV.VERSION, "params": params,
            "state_decision": dict(sorted(E.STATE_DECISION.items())), "state_rule": dict(sorted(E.STATE_RULE.items())),
            "rules": rules}
    return snap


def config_hash(snap):
    return sha256_bytes(canon(snap).encode("utf-8"))


def _read(rel, root=ROOT):
    with open(os.path.join(root, rel), encoding="utf-8") as f:
        return json.load(f)


def inventories(root=ROOT):
    """جردُ النتائج المنشورة لـV4 (أرقامٌ قائمةٌ لا جديدة) — يُعرض في التقرير ويُختم في البيان."""
    cases = _read("faisal_method_v4/results/cases_v4.json", root)
    ev = _read("faisal_method_v4/results/v4_eval_results.json", root)
    suite = _read("faisal_method_v4/results/suite_result_v4.json", root)
    mut = _read("faisal_method_v4/results/mutations_v4.json", root)
    cc = _read("faisal_method_v4/results/corpus_counts_v4.json", root)
    g = ev["golden_v31_vs_v4"]
    hs = ev["h_state_descriptive"]
    m = ev["metrics"]
    rules_active = sum(1 for r in config_snapshot(root)["rules"].values() if r["active"])
    return {
        "tests": {"passed": suite["passed"], "failed": suite["failed"], "exit": suite["exit"], "commit": suite["commit"]},
        "mutations": {"caught": mut["caught"], "total": mut["total"]},
        "golden": {"of": g["of"], "dated": g["dated"], "v31_matched": g["v31_matched"], "v4_matched": g["v4_matched"],
                   "always_wait_baseline": g["always_wait_baseline"],
                   "dxst": ev["dxst"].get("verdict"), "veee": ev["veee"].get("verdict")},
        "h_state": {k: hs[k] for k in ("S1_all", "S1_discovery", "S1_holdout")},
        "h_level_holdout": {"verdict": m["S1_holdout"]["h_level_verdict"], **m["S1_holdout"]["h_level"]},
        "h_class_holdout": {k: m["S1_holdout"]["h_class"][k] for k in ("verdict", "agree", "n", "rate", "majority_rate")},
        "cases": cases["summary"]["by_set"] | {"total": cases["summary"]["cases"], "statements": cases["summary"]["statements"],
                                               "S1_by_split": cases["summary"]["S1_by_split"],
                                               "S1_by_label": cases["summary"]["S1_by_label"]},
        "corpus": {k: cc[k] for k in ("images_in_corpus_record", "sha256_match", "opened_representatives",
                                       "multi_member_clusters", "primary_images")},
        "rules": {"total": len(config_snapshot(root)["rules"]), "active": rules_active},
    }


def _git(args, root=ROOT):
    try:
        r = subprocess.run(["git"] + args, cwd=root, capture_output=True, text=True, timeout=30)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:                                                   # noqa: BLE001
        return None


def git_meta(root=ROOT):
    """بياناتٌ وصفيّة (لا يتحقّق منها القفل · تختلف بين الفروع): آخرُ تغييرٍ في نواة المحرّك · ورأسُ البناء."""
    last = _git(["log", "-1", "--format=%H|%cI|%s", "--"] + list(ENGINE_CORE), root)
    head = _git(["rev-parse", "HEAD"], root)
    out = {"build_head": head}
    if last:
        h, d, s = (last.split("|", 2) + ["", ""])[:3]
        out.update(engine_last_change_commit=h, engine_last_change_utc=d, engine_last_change_subject=s[:120])
    return out


def build_revision(root=ROOT):
    paths = frozen_files(root)
    hashes = file_hashes(paths, root)
    snap = config_snapshot(root)
    return {"rev": 1, "reason_class": "INITIAL", "freeze_id": freeze_id(hashes), "files": hashes,
            "n_files": len(hashes), "config_hash": config_hash(snap), "config": snap,
            "recorded_deps": {p: sha256_file(os.path.join(root, p)) for p in RECORDED_DEPS if os.path.exists(os.path.join(root, p))},
            "regression_test": None, "invalidates": [], "supersedes": None}


def build(root=ROOT):
    rev = build_revision(root)
    return {"freeze_version": FREEZE_VERSION, "candidate": "FAISAL V4 (ENGINE FAISAL-V4 1.0 · RULES V4-RULES 1.0)",
            "status": "FROZEN", "policy": {
                "methodology_changes": "FORBIDDEN during prospective validation (§1 · §27 · §36) ⟵ V4_CHANGE_REQUESTS.md / V4_2_RESEARCH_QUEUE.md",
                "implementation_bugs": "a new revision with reason_class=IMPLEMENTATION_BUG · regression_test · invalidates (§30)",
                "recorded_not_frozen": list(RECORDED_DEPS)},
            "git": git_meta(root), "inventories": inventories(root), "revisions": [rev], "current": 1}


def current_revision(man):
    return next(r for r in man["revisions"] if r["rev"] == man["current"])


def verify(man, root=ROOT, live_config=True):
    """قلبُ FV41 ⟵ (ok · قائمةُ المشكلات). لا يحتاج git."""
    probs = []
    revs = man.get("revisions") or []
    if not revs or man.get("current") != max(r["rev"] for r in revs):
        probs.append("REVISION_POINTER")
    for r in revs:
        if r.get("reason_class") not in REVISION_CLASSES:
            probs.append(f"REVISION_CLASS:{r.get('rev')}:{r.get('reason_class')}")
        if r.get("rev", 0) > 1 and (r.get("reason_class") != "IMPLEMENTATION_BUG" or not r.get("regression_test")
                                    or not isinstance(r.get("invalidates"), list) or r.get("supersedes") != r["rev"] - 1):
            probs.append(f"REVISION_POLICY:{r.get('rev')}")
    try:
        cur = current_revision(man)
    except StopIteration:
        return False, probs + ["NO_CURRENT"]
    want = cur["files"]
    if freeze_id(want) != cur.get("freeze_id"):
        probs.append("FREEZE_ID")
    have_list = frozen_files(root)
    extra = sorted(set(have_list) - set(want))
    missing = sorted(set(want) - set(have_list))
    if extra:
        probs.append("EXTRA:" + ",".join(extra[:5]))
    if missing:
        probs.append("MISSING:" + ",".join(missing[:5]))
    for p, h in sorted(want.items()):
        fp = os.path.join(root, p)
        if os.path.exists(fp) and sha256_file(fp) != h:
            probs.append("HASH:" + p)
    if config_hash(cur.get("config") or {}) != cur.get("config_hash"):
        probs.append("CONFIG_RECORD")
    if live_config:
        try:
            if config_hash(config_snapshot(root)) != cur.get("config_hash"):
                probs.append("CONFIG_LIVE")
        except Exception as e:                                          # noqa: BLE001
            probs.append(f"CONFIG_IMPORT:{type(e).__name__}")
    return (not probs), probs


def report_md(man):
    cur = current_revision(man)
    inv = man["inventories"]
    g = man.get("git") or {}
    cfg = cur["config"]
    L = ["# 🧊 V4 FREEZE REPORT — المرشَّحُ المجمَّد للتحقّق الأماميّ", "",
         f"> مولَّدٌ من `faisal_method_v41/freeze.py` ({man['freeze_version']}) · **لا يُحرَّر باليد** · والعقد `faisal_method_v41/V41_prereg.md` §②.",
         "", "## ① الهويّة", "",
         f"- **freeze_id:** `{cur['freeze_id']}` (‏SHA-256 لخريطة بصمات {cur['n_files']} ملفًّا مجمَّدًا)",
         f"- **المراجعة:** {man['current']} ({cur['reason_class']}) · الحالة **{man['status']}**",
         f"- **المحرّك:** `{cfg['engine_version']}` · **السجلّ:** `{cfg['rules_version']}` · **بصمةُ الإعداد:** `{cur['config_hash']}`",
         f"- **آخرُ تغييرٍ في نواة المحرّك:** `{(g.get('engine_last_change_commit') or '—')[:12]}` ({g.get('engine_last_change_utc') or '—'}) "
         "— المنهجُ لم يتغيّر منذه (بصماتُ النواة في البيان)",
         f"- **رأسُ البناء:** `{(g.get('build_head') or '—')[:12]}` · وcommit الدمج على main يُسجَّل في وثائق V4.1 بعد الدمج", "",
         "## ② ما يُجمَّد وما يُسجَّل", "",
         "- **مجمَّد (منهجٌ ودليل):** كلُّ ملفٍّ تحت `faisal_method_v4/` (المحرّك · سجلُّ القواعد · بنّاءُ الحالات · الوسوم · المرورُ البصريّ · "
         "التقييم · الفِكستشر · النتائج · الوثائق · الصور المركّبة) ‏+ `.github/workflows/faisal_v4.yml` ‏+ ما يقرؤه V4 من V3.1: "
         + " · ".join(f"`{p}`" for p in FROZEN_EXTRA[1:]),
         "- **مسجَّلٌ لا مجمَّد (اكتسابُ بيانات):** " + " · ".join(f"`{p}` (`{h[:12]}`)" for p, h in sorted(cur["recorded_deps"].items()))
         + " — تُختم بصمتُها في كلّ تشغيلةٍ أماميّة.",
         "- **صورُ فيصل (722):** مثبَّتةٌ عبر `image_corpus.json` المجمَّد (بصمةُ كلّ صورة · ويعيد V4L16 حسابها).", "",
         "## ③ الإعداد المجمَّد (PARAMS)", "", "| المفتاح | القيمة | وسمُ المصدر |", "|---|---|---|"]
    for k, v in cfg["params"].items():
        L.append(f"| `{k}` | {v['value']} | {v['source']} |")
    L += ["", "## ④ جردُ القواعد", "", "| القاعدة | فعّالة | الحالة (السجلّ) | القراريّة | مستوى المصدر | صور |", "|---|---|---|---|---|---|"]
    for rid, r in cfg["rules"].items():
        L.append(f"| `{rid}` | {'نعم' if r['active'] else 'لا'} | {r['status']} | {r['decisionality']} | {r['source_level']} | {len(set(r['image_ids'] or []))} |")
    t, mu, gd, hl = inv["tests"], inv["mutations"], inv["golden"], inv["h_level_holdout"]
    hs = inv["h_state"]["S1_all"]
    L += ["", "## ⑤ النتائج المنشورة عند التجميد (قائمةٌ لا جديدة)", "",
          f"- **السويّة:** {t['passed']} نجح · {t['failed']} فشل · خروج {t['exit']} (‏`{t['commit']}`) · **الطفرات:** {mu['caught']}/{mu['total']}",
          f"- **الذهبيّة:** V3.1 {gd['v31_matched']}/{gd['dated']} · V4 {gd['v4_matched']}/{gd['dated']} · «دائمًا WAIT» {gd['always_wait_baseline']}/{gd['dated']} "
          f"(من {gd['of']} · المؤرَّخة {gd['dated']}) · DXST {gd['dxst']} · VEEE {gd['veee']}",
          f"- **H-STATE S1 (وصفيّ):** n {hs['n']} · تطابقٌ {hs['state_exact']} · «دائمًا WAIT» {hs['always_wait']} · READY من المحرّك {hs['engine_ready']} · "
          f"UNKNOWN {hs['engine_unknown']} · READY عند فيصل {hs['faisal_ready']}",
          f"- **H-LEVEL الاحتجاز:** {hl['verdict']} (‏{hl['diff']:+.4f} [{hl['ci95'][0]:+.4f} · {hl['ci95'][1]:+.4f}] · مستويات {hl['levels']} · حالات {hl['cases']})",
          f"- **الحالات:** {inv['cases']['total']} من {inv['cases']['statements']} عبارة · S1 {inv['cases']['S1']} "
          f"(اكتشاف {inv['cases']['S1_by_split'].get('discovery')} · احتجاز {inv['cases']['S1_by_split'].get('holdout')}) · "
          f"S2 {inv['cases']['S2']} · S3 {inv['cases']['S3']} · S4 {inv['cases']['S4']} · مستبعد {inv['cases']['EXCL']}",
          f"- **المدوّنة:** {inv['corpus']['images_in_corpus_record']} صورة · بصمةٌ مطابقة {inv['corpus']['sha256_match']} · "
          f"وحداتٌ {inv['corpus']['opened_representatives']} · عناقيد {inv['corpus']['multi_member_clusters']} · أوّليّة {inv['corpus']['primary_images']}",
          f"- **القواعد:** {inv['rules']['total']} ({inv['rules']['active']} فعّالة)", "",
          "## ⑥ السياسة", "",
          "- **لا تغييرَ منهجيّ** أثناء التحقّق الأماميّ (إضافةُ قاعدة · حذفُها · عتبة · تسامح · ترتيبُ القرار · منطقُ READY/WAIT/REJECT · "
          "النماذج · الدعم · الأهداف · الصلاحيّة) ⟵ `V4_CHANGE_REQUESTS.md` و`V4_2_RESEARCH_QUEUE.md`.",
          "- **خطأُ التنفيذ** (والمواصفةُ المجمَّدة تحدّد السلوكَ صراحةً) ⟵ مراجعةٌ جديدة `IMPLEMENTATION_BUG` بقفلِ ارتداد وطفرة وقائمةِ تشغيلاتٍ مُبطَلةٍ تُعاد.",
          "- **FV41** يُسقط السويّة عند أيّ بايتٍ تغيّر أو ملفٍّ أُضيف/حُذف أو إعدادٍ حيٍّ اختلف أو مراجعةٍ خارج السياسة.", ""]
    return "\n".join(L)


def write(man):
    os.makedirs(DOCS, exist_ok=True)
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(report_md(load()))          # من الملفّ المكتوب (مفاتيحُه مرتّبة) ⟵ التقريرُ يُعاد منه حرفًا (FV41)


def load(path=MANIFEST):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "verify"
    if cmd == "build":
        man = build()
        write(man)
        print(f"🧊 freeze_id {current_revision(man)['freeze_id']} · {current_revision(man)['n_files']} ملفًّا")
        return 0
    ok, probs = verify(load())
    print("🧊 FV41", "سليم" if ok else "⛔ " + " · ".join(probs[:10]))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
