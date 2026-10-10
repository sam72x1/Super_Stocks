"""🚪⚖️ Gate audit — four independent dimensions per gate, justification derived from typed evidence (pure: no I/O, no env).

Why this exists (owner follow-up to PR #598, 2026-10-09): the first inventory gave each gate ONE label, and a gate whose only
evidence was «no Faisal source states this rule» became `ENGINEERING_GUARD` — i.e. absence of evidence was read as a justified
engineering guard, and the report concluded «0 gates without supporting evidence». Origin (where a rule came from) and
justification (what currently supports the rule as implemented) are different questions, and support for a concept is not
support for the exact number that implements it. This module keeps them apart:

  · origin          — where the rule came from (`ORIGIN`), backed by an origin reference of the matching kind;
  · justification   — DERIVED here from the evidence attached to the concept, to every threshold, and (for rejecting roles)
                      to the hard role itself; absence, code comments and inherited records never count as support;
  · impl_role       — what the gate does in the pipeline (`IMPL_ROLE`);
  · fidelity        — how the implementation maps to Faisal's method (`FIDELITY`), constrained by the evidence.

Evidence items live in a registry `{id: {"kind", "stance", "context"?, ...}}`; a gate's `context` is the system it runs in
(the pivot screener is "pivot"); a Faisal statement made for another system (the split-stock recipe, an entry rule) counts as a
transferred concept, never as direct support for this gate.

An EXPERIMENT also carries a `scope` (2026-10-09, follow-up to #600): THIS_GATE — it tested this gate's rule or its direct
alternative · BUNDLE — several gates or thresholds changed jointly · SUPERSEDED_VALUE — it measured a value no longer live ·
RELATED_RULE — a related but different rule. Only a THIS_GATE experiment that supports counts as support; the others are reported,
never read as support for one exact number. Archived experiment verdicts are tied to the gates they name by `archive_join` and
`xref_check`: a bullet of the decisions archive whose head names a gate's key or experiment code must be classified for that gate.
"""
import re

ORIGIN = ["DIRECT_FAISAL_SOURCE", "INFERRED_FROM_FAISAL_SOURCE", "EXPLICIT_OWNER_POLICY", "ENGINEERING_INTRODUCED",
          "INHERITED_OR_EXTERNAL", "ORIGIN_UNKNOWN"]
JUSTIFICATION = ["DIRECT_SOURCE_SUPPORT", "EXPLICIT_OWNER_REQUIREMENT", "DOCUMENTED_OPERATIONAL_INVARIANT",
                 "TESTED_RELIABILITY_REQUIREMENT", "EMPIRICAL_SUPPORT_UNDER_VALID_CONTRACT", "PARTIAL_OR_CONCEPT_ONLY_SUPPORT",
                 "UNJUSTIFIED_BY_CURRENT_EVIDENCE", "UNKNOWN"]
IMPL_ROLE = ["HARD_REJECTION", "SOFT", "RANKING", "DISPLAY", "DATA_QUALITY", "OPS_SAFETY", "NOTIFICATION_ELIGIBILITY",
             "OWNER_TRADING_ELIGIBILITY", "OTHER"]
FIDELITY = ["SOURCE_OBSERVED_RULE", "SUPPORTED_RECONSTRUCTION", "CONCEPT_ONLY", "SAMPLE_NUMERICAL_RELATIONSHIP",
            "NO_DEFENSIBLE_MAPPING", "UNKNOWN"]
NUMBER_ORIGIN = ["FAISAL_SOURCE", "OWNER", "CATALOG_PERCENTILE", "INFERRED", "ENGINEERING_DEFAULT", "INHERITED", "EXPERIMENT",
                 "UNEXPLAINED"]
KINDS = ["FAISAL_SOURCE", "FAISAL_INFERRED", "FAISAL_SAMPLE", "OWNER_ORDER", "OPERATIONAL_INVARIANT", "TESTED_INCIDENT",
         "EXPERIMENT", "CONTRADICTION", "ABSENCE", "CODE_RECORD", "INHERITED_RECORD", "PRIOR_AUDIT"]
STANCES = ["supports", "contradicts", "null", "mixed", "against", "neutral"]
SCOPES = ["THIS_GATE", "BUNDLE", "SUPERSEDED_VALUE", "RELATED_RULE"]
XREF_CLASSES = ["CITED", "CITED_ELSEWHERE", "NOT_GATE_EVIDENCE"]
XREF_WHY = ["IMPLEMENTATION", "MEMORY", "OTHER_SYSTEM", "INCIDENTAL"]
ARCHIVE = "DECISIONS_ARCHIVE.md"
# roles whose hardness (reject rather than mark) must itself be supported for a full justification
HARD_ROLES = ("HARD_REJECTION", "OWNER_TRADING_ELIGIBILITY")
# a full justification type ← the support class every component must carry
_FULL = [("DIRECT_SOURCE_SUPPORT", "FAISAL_DIRECT"), ("EXPLICIT_OWNER_REQUIREMENT", "OWNER"),
         ("DOCUMENTED_OPERATIONAL_INVARIANT", "INVARIANT"), ("TESTED_RELIABILITY_REQUIREMENT", "TESTED"),
         ("EMPIRICAL_SUPPORT_UNDER_VALID_CONTRACT", "EMPIRICAL")]


def support_class(item, gate_context):
    """The support class one evidence item gives a gate component, or None (absence, comments, records, contradictions,
    samples, null/mixed experiments never support)."""
    if not item or item.get("stance") != "supports":
        return None
    k = item.get("kind")
    if k == "FAISAL_SOURCE":
        ctx = item.get("context") or "general"
        return "FAISAL_DIRECT" if ctx in ("general", gate_context) else "FAISAL_TRANSFERRED"
    if k == "FAISAL_INFERRED":
        return "FAISAL_TRANSFERRED"
    if k == "EXPERIMENT" and (item.get("scope") or "THIS_GATE") != "THIS_GATE":
        return None                      # a bundle, a superseded value or a related rule is reported, never support
    return {"OWNER_ORDER": "OWNER", "OPERATIONAL_INVARIANT": "INVARIANT", "TESTED_INCIDENT": "TESTED",
            "EXPERIMENT": "EMPIRICAL"}.get(k)


def _classes(refs, reg, ctx):
    return {c for c in (support_class(reg.get(r), ctx) for r in refs or []) if c}


def components(audit, reg):
    """[(name, refs)] — the concept, every threshold, and the hard role when the gate rejects."""
    out = [("concept", list(audit.get("concept_refs") or []))]
    for t in audit.get("thresholds") or []:
        out.append(("threshold:" + str(t.get("key", "?")), list(t.get("refs") or [])))
    if audit.get("impl_role") in HARD_ROLES:
        out.append(("hardness", list(audit.get("hardness_refs") or [])))
    return out


def contradicted(audit, reg):
    refs = list(audit.get("concept_refs") or [])
    for t in audit.get("thresholds") or []:
        refs += list(t.get("refs") or [])
    return any((reg.get(r) or {}).get("kind") == "CONTRADICTION" for r in refs)


def derive_justification(audit, reg):
    """(justification, detail) — from evidence only.

    · no concept evidence at all ⇒ UNKNOWN (not assessed);
    · a full type when EVERY component (concept, each threshold, hardness for rejecting roles) carries that support class —
      DIRECT also requires no contradiction and in-context Faisal statements;
    · otherwise PARTIAL when at least one component has positive support, else UNJUSTIFIED_BY_CURRENT_EVIDENCE."""
    ctx = audit.get("context") or "pivot"
    comps = components(audit, reg)
    if not comps[0][1]:
        return "UNKNOWN", {"components": {}, "contradicted": False}
    cls = {name: _classes(refs, reg, ctx) for name, refs in comps}
    contra = contradicted(audit, reg)
    for just, need in _FULL:
        if just == "DIRECT_SOURCE_SUPPORT" and contra:
            continue
        if all(need in c for c in cls.values()):
            return just, {"components": {k: sorted(v) for k, v in cls.items()}, "contradicted": contra}
    any_pos = any(cls.values())
    return ("PARTIAL_OR_CONCEPT_ONLY_SUPPORT" if any_pos else "UNJUSTIFIED_BY_CURRENT_EVIDENCE"), \
        {"components": {k: sorted(v) for k, v in cls.items()}, "contradicted": contra}


_ORIGIN_NEEDS = {"DIRECT_FAISAL_SOURCE": ("FAISAL_SOURCE",), "INFERRED_FROM_FAISAL_SOURCE": ("FAISAL_SOURCE", "FAISAL_INFERRED"),
                 "EXPLICIT_OWNER_POLICY": ("OWNER_ORDER",), "ENGINEERING_INTRODUCED": ("CODE_RECORD",),
                 "INHERITED_OR_EXTERNAL": ("INHERITED_RECORD",)}


def check_origin(audit, reg):
    """Error text when the origin is not backed by an origin reference of the matching kind, else None."""
    o = audit.get("origin")
    if o not in ORIGIN:
        return f"origin {o} not in vocabulary"
    need = _ORIGIN_NEEDS.get(o)
    if not need:
        return None
    if o == "DIRECT_FAISAL_SOURCE":
        ok = any((reg.get(r) or {}).get("kind") == "FAISAL_SOURCE"
                 and support_class(reg.get(r), audit.get("context") or "pivot") == "FAISAL_DIRECT"
                 for r in audit.get("origin_refs") or [])
    else:
        ok = any((reg.get(r) or {}).get("kind") in need for r in audit.get("origin_refs") or [])
    return None if ok else f"origin {o} has no origin reference of kind {'/'.join(need)}"


def check_fidelity(audit, reg, justification):
    """Error text when the fidelity label claims more than the evidence supports, else None."""
    f = audit.get("fidelity")
    if f not in FIDELITY:
        return f"fidelity {f} not in vocabulary"
    ctx = audit.get("context") or "pivot"
    concept = _classes(audit.get("concept_refs"), reg, ctx)
    faisal = concept & {"FAISAL_DIRECT", "FAISAL_TRANSFERRED"}
    contra = contradicted(audit, reg)
    if f == "SOURCE_OBSERVED_RULE" and justification != "DIRECT_SOURCE_SUPPORT":
        return "SOURCE_OBSERVED_RULE requires DIRECT_SOURCE_SUPPORT"
    if f == "SUPPORTED_RECONSTRUCTION":
        n = sum(1 for r in audit.get("concept_refs") or []
                if support_class(reg.get(r), ctx) in ("FAISAL_DIRECT", "FAISAL_TRANSFERRED"))
        if n < 2 or contra:
            return "SUPPORTED_RECONSTRUCTION requires two Faisal concept references and no contradiction"
    if f in ("CONCEPT_ONLY", "SAMPLE_NUMERICAL_RELATIONSHIP") and not faisal:
        return f"{f} requires Faisal support for the concept"
    if f == "SAMPLE_NUMERICAL_RELATIONSHIP" and not any(t.get("number_origin") == "CATALOG_PERCENTILE"
                                                      for t in audit.get("thresholds") or []):
        return "SAMPLE_NUMERICAL_RELATIONSHIP requires a catalog-percentile threshold"
    return None


def pass_rate(rows, cohort, threshold):
    """(passing, known, unknown) of one harvest cohort against the borrow threshold — the production rule (an availability above
    the threshold is ejected, at or below passes). **An unknown availability is neither passing nor failing: it is counted apart.**"""
    rs = [r for r in rows or [] if r.get("cohort") == cohort]
    known = [r for r in rs if r.get("shares_available") is not None]
    k = sum(1 for r in known if float(r["shares_available"]) <= float(threshold))
    return k, len(known), len(rs) - len(known)


# ---------------------------------------------------------------- archived measurements ⟷ gates
def gate_refs(audit):
    """Every evidence id attached to a gate (origin, concept, hardness, thresholds)."""
    r = list(audit.get("origin_refs") or []) + list(audit.get("concept_refs") or []) + list(audit.get("hardness_refs") or [])
    for t in audit.get("thresholds") or []:
        r += list(t.get("refs") or [])
    return r


def archive_bullets(text):
    """[(first line, bullet text)] — the top-level bullets of the decisions archive (a line that starts with «- **»)."""
    lines = (text or "").split("\n")
    starts = [i for i, ln in enumerate(lines) if ln.startswith("- **")]
    return [(a + 1, "\n".join(lines[a:b])) for a, b in zip(starts, starts[1:] + [len(lines)])]


def _term_rx(t):
    # a code or key is matched whole: «T-BASE» does not match inside «T-BASE-2» or «T-BASE-475»
    return re.compile(r"(?<![A-Za-z0-9_-])" + re.escape(t) + r"(?![A-Za-z0-9_]|-[A-Za-z0-9])")


def archive_join(bullets, gates, codes, head_chars):
    """[(gate id, bullet index, terms)] — the bullet's head (its first `head_chars` characters, lines joined) names one of the
    gate's config keys (six characters or longer) or one of its listed experiment codes."""
    out = []
    heads = [" ".join(txt.split("\n"))[:int(head_chars)] for _, txt in bullets]
    for g in gates:
        terms = [k for k in (g.get("config_keys") or []) if len(k) >= 6] + list((codes or {}).get(g["id"]) or [])
        rx = [(t, _term_rx(t)) for t in terms]
        for i, h in enumerate(heads):
            hit = [t for t, r in rx if r.search(h)]
            if hit:
                out.append((g["id"], i, hit))
    return out


def xref_check(bullets, gates, reg, xref):
    """(errors, rows) — every join pair classified for its gate; CITED refs attached to the gate with at least one anchored
    inside the bullet; CITED_ELSEWHERE refs attached to the gate; NOT_GATE_EVIDENCE with a reason; no entry without a pair,
    no anchor that is missing or names two bullets, no override for a gate the join does not name."""
    errs, rows = [], []
    xref = xref or {}
    pairs = archive_join(bullets, gates, xref.get("codes"), xref.get("head_chars") or 400)
    attached = {g["id"]: set(gate_refs(g.get("audit") or {})) for g in gates}
    by_bullet = {}
    for e in xref.get("entries") or []:
        hits = [i for i, (_, txt) in enumerate(bullets) if e.get("anchor") and e["anchor"] in txt]
        if len(hits) != 1:
            errs.append(f"archive xref: anchor «{e.get('anchor')}» found in {len(hits)} bullets (needs exactly one)")
            continue
        if hits[0] in by_bullet:
            errs.append(f"archive xref: two entries for the bullet at line {bullets[hits[0]][0]}")
            continue
        by_bullet[hits[0]] = e
    named = {}
    for gid, i, terms in pairs:
        named.setdefault(i, set()).add(gid)
        e = by_bullet.get(i)
        line, txt = bullets[i]
        if e is None:
            errs.append(f"archive xref: {gid} — bullet at line {line} names {', '.join(terms)} in its head and is not classified "
                        f"(add an entry to archive_xref in gate_provenance.json: CITED · CITED_ELSEWHERE · NOT_GATE_EVIDENCE)")
            continue
        c = (e.get("gates") or {}).get(gid) or e.get("default") or {}
        cls, refs = c.get("class"), list(c.get("refs") or [])
        if cls not in XREF_CLASSES:
            errs.append(f"archive xref: {gid} at line {line}: class {cls} not in vocabulary")
        elif cls in ("CITED", "CITED_ELSEWHERE"):
            if not refs:
                errs.append(f"archive xref: {gid} at line {line}: {cls} without refs")
            for r in refs:
                if r not in reg:
                    errs.append(f"archive xref: {gid} at line {line}: {r} not in registry")
                elif r not in attached.get(gid, set()):
                    errs.append(f"archive xref: {gid} at line {line}: {r} is not attached to the gate")
            if cls == "CITED" and not any(
                    (reg.get(r) or {}).get("verify", {}).get("file") == ARCHIVE
                    and (reg.get(r) or {}).get("verify", {}).get("contains", "\0") in txt for r in refs):
                errs.append(f"archive xref: {gid} at line {line}: CITED but no ref is anchored inside the bullet")
            if cls == "CITED_ELSEWHERE" and not str(c.get("note") or "").strip():
                errs.append(f"archive xref: {gid} at line {line}: CITED_ELSEWHERE without a note")
        else:
            if c.get("why") not in XREF_WHY or not str(c.get("note") or "").strip():
                errs.append(f"archive xref: {gid} at line {line}: NOT_GATE_EVIDENCE needs a reason in {XREF_WHY} and a note")
        rows.append({"gate": gid, "line": line, "anchor": e.get("anchor"), "terms": terms, "class": cls, "refs": refs,
                     "why": c.get("why"), "note": c.get("note") or ""})
    for i, e in by_bullet.items():
        if i not in named:
            errs.append(f"archive xref: entry «{e.get('anchor')}» classifies a bullet the join no longer names (stale)")
        for gid in (e.get("gates") or {}):
            if gid not in named.get(i, set()):
                errs.append(f"archive xref: entry «{e.get('anchor')}» overrides {gid}, which the join does not name there")
    return errs, rows
