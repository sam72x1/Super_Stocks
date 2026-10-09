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
"""

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
