#!/usr/bin/env python3
"""RDA finding linter -- enforces the evidence, confidence and severity contracts.

Dependency-free: validates against schemas/finding.schema.json (a minimal JSON Schema subset is
implemented inline, so there is no jsonschema dependency) and then applies the governance rules a
JSON Schema cannot express (class ceilings, confidence award rules, severity/confidence floors,
the RS-1 severity matrix, the undecidable register, sampling ceilings, abstention monitoring).

Usage:  python3 validate_findings.py findings.json [--coverage coverage.json] [--schema PATH] [--strict]
Exit:   0 clean, 1 violations found, 3 IO error.

--strict additionally treats the abstention warnings (W100-W102) and the presence of quarantined
findings as violations, for use as a publish gate in CI.
"""
import argparse, json, os, re, sys
from collections import Counter

CLASSES = {"FACT", "INFERENCE", "HYPOTHESIS", "UNKNOWN", "EXTERNAL_VALIDATION_REQUIRED"}
LEVELS = ["C0", "C1", "C2", "C3", "C4"]
SEV = ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
EV_KINDS = {"SOURCE","CONFIG","TOOL_OUTPUT","VCS_HISTORY","DOC","TEST_RESULT","RUNTIME_ARTIFACT","EXTERNAL_ATTESTATION"}
# Evidence kinds that are re-resolvable against the repository at a pinned commit. Must stay in step
# with verify_citations.py: a kind the verifier re-reads but the linter does not require a commit for
# would be quarantined at verification despite being schema-valid.
PINNED_KINDS = {"SOURCE", "CONFIG", "VCS_HISTORY", "DOC"}

# RS-1 s1 severity matrix (impact x likelihood -> severity), applied mechanically so two runs agree.
MATRIX = {
    "SEVERE":     {"RARE":"MEDIUM","UNLIKELY":"HIGH","POSSIBLE":"HIGH","LIKELY":"CRITICAL","ALMOST_CERTAIN":"CRITICAL"},
    "MAJOR":      {"RARE":"LOW","UNLIKELY":"MEDIUM","POSSIBLE":"HIGH","LIKELY":"HIGH","ALMOST_CERTAIN":"CRITICAL"},
    "MODERATE":   {"RARE":"LOW","UNLIKELY":"LOW","POSSIBLE":"MEDIUM","LIKELY":"MEDIUM","ALMOST_CERTAIN":"HIGH"},
    "MINOR":      {"RARE":"INFO","UNLIKELY":"LOW","POSSIBLE":"LOW","LIKELY":"LOW","ALMOST_CERTAIN":"MEDIUM"},
    "NEGLIGIBLE": {"RARE":"INFO","UNLIKELY":"INFO","POSSIBLE":"INFO","LIKELY":"LOW","ALMOST_CERTAIN":"LOW"},
}

# ES-1 s2 undecidable register: phrase -> maximum permitted claim_class
UNDECIDABLE = [
    (r"\b(is|are) (deployed|running|live) in production\b", "HYPOTHESIS"),
    (r"\b(handles|serves|processes)\s+[\d,]+\s*(requests|users|rps|tps|qps)", "EXTERNAL_VALIDATION_REQUIRED"),
    (r"\b(costs?|saves?|savings? of)\s*[$€£]", "EXTERNAL_VALIDATION_REQUIRED"),
    (r"\bis exploitable\b|\bcan be exploited\b", "HYPOTHESIS"),
    (r"\b(is|are) (dead|unused|never called|not used)\b", "HYPOTHESIS"),
    (r"\bwill scale to\b|\bcan handle\s+[\d,]+", "EXTERNAL_VALIDATION_REQUIRED"),
    (r"\bMTTR (is|was)\b|\bincident (rate|frequency) (is|was)\b", "EXTERNAL_VALIDATION_REQUIRED"),
    (r"\bdata (is|are) stored in (the )?[a-z-]+ region\b", "HYPOTHESIS"),
]
# Claims that may never be emitted at all
FORBIDDEN = [
    (r"\b(is|are) (SOC ?2|ISO ?27001|PCI[- ]DSS|HIPAA|FedRAMP)[- ]?(compliant|certified)\b",
     "compliance verdict -- RDA reports control evidence present/absent only (ES-1 s2)"),
    (r"\bconfidence\W{0,3}(0?\.\d+|\d{1,3}\s?%)", "numeric self-confidence is banned (CC-1 s0); use the C0-C4 ladder"),
    (r"\b\d+(\.\d+)?\s*(person|engineer|dev)[- ](days?|hours?)\b", "person-day point estimate -- use effort bands (BSR-10)"),
]
LOCATOR = re.compile(r"^[^#\s]+(#L\d+(-L?\d+)?)?$")

# --- minimal JSON Schema subset -------------------------------------------------------------------
# Covers exactly the constructs the RDA schemas use: type, required, properties, additionalProperties,
# enum, pattern, maxLength, minimum, maximum, minItems, items, $ref to #/$defs/*. Keeping this inline
# preserves the pack's zero-dependency property while making the published schema load-bearing rather
# than decorative -- previously nothing in the toolchain read it at all.
TYPES = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float), "boolean": bool}

def schema_check(node, sch, root, path, out):
    if "$ref" in sch:
        ref = sch["$ref"]
        if ref.startswith("#/$defs/"):
            sch = root.get("$defs", {}).get(ref.split("/")[-1], {})
        else:
            return
    t = sch.get("type")
    if t:
        py = TYPES.get(t)
        ok = isinstance(node, py) and not (t in ("integer", "number") and isinstance(node, bool))
        if t == "integer" and isinstance(node, bool): ok = False
        if not ok:
            out.append((path, f"expected type {t}, got {type(node).__name__}")); return
    if isinstance(node, dict):
        for k in sch.get("required", []):
            if k not in node: out.append((path, f"missing required property '{k}'"))
        props = sch.get("properties", {})
        if sch.get("additionalProperties") is False:
            for k in node:
                if k not in props: out.append((path, f"property '{k}' not permitted (additionalProperties: false)"))
        for k, v in node.items():
            if k in props: schema_check(v, props[k], root, f"{path}.{k}", out)
    elif isinstance(node, list):
        if "minItems" in sch and len(node) < sch["minItems"]:
            out.append((path, f"array shorter than minItems {sch['minItems']}"))
        if "items" in sch:
            for i, v in enumerate(node): schema_check(v, sch["items"], root, f"{path}[{i}]", out)
    if "enum" in sch and node not in sch["enum"]:
        out.append((path, f"value {node!r} not in enum {sch['enum']}"))
    if isinstance(node, str):
        if "pattern" in sch and not re.search(sch["pattern"], node):
            out.append((path, f"value {node!r} does not match pattern {sch['pattern']}"))
        if "maxLength" in sch and len(node) > sch["maxLength"]:
            out.append((path, f"length {len(node)} exceeds maxLength {sch['maxLength']}"))
    if isinstance(node, (int, float)) and not isinstance(node, bool):
        if "minimum" in sch and node < sch["minimum"]: out.append((path, f"{node} < minimum {sch['minimum']}"))
        if "maximum" in sch and node > sch["maximum"]: out.append((path, f"{node} > maximum {sch['maximum']}"))

def err(out, fid, code, msg): out.append((fid, code, msg))

def check(f, out, coverage_ids, coverage_meta, schema):
    fid = f.get("id", "<no-id>")
    if schema:
        sp = []
        schema_check(f, schema, schema, "finding", sp)
        for p, m in sp: err(out, fid, "E000", f"schema: {p}: {m}")
    for k in ("id","skill_id","run_id","title","claim_class","statement","evidence","confidence",
              "coverage_ref","severity","how_to_refute","disconfirming_check"):
        if k not in f: err(out, fid, "E001", f"missing required field '{k}'")
    cc, st = f.get("claim_class"), f.get("statement", "")
    if cc not in CLASSES: err(out, fid, "E002", f"invalid claim_class '{cc}'")
    ev = f.get("evidence") or []

    # --- evidence integrity -------------------------------------------------
    if cc in ("FACT", "INFERENCE") and not ev:
        err(out, fid, "E010", f"{cc} with zero evidence -- unsupported claim (BSR-01)")
    for i, e in enumerate(ev):
        if e.get("kind") not in EV_KINDS: err(out, fid, "E011", f"evidence[{i}] invalid kind '{e.get('kind')}'")
        if not e.get("locator"): err(out, fid, "E012", f"evidence[{i}] missing locator")
        elif not LOCATOR.match(e["locator"]) and e.get("kind") != "TOOL_OUTPUT":
            err(out, fid, "E013", f"evidence[{i}] locator not in path#Lx-Ly form: {e['locator']}")
        if e.get("kind") in PINNED_KINDS:
            if not e.get("commit"): err(out, fid, "E014", f"evidence[{i}] missing commit pin")
            if not e.get("quote"): err(out, fid, "E015", f"evidence[{i}] missing verbatim quote")
        if e.get("kind") == "TOOL_OUTPUT":
            t = e.get("tool") or {}
            if not (t.get("name") and t.get("version") and "exit_code" in t):
                err(out, fid, "E016", f"evidence[{i}] TOOL_OUTPUT needs tool name+version+exit_code (BSR-04)")
    # ES-1 s4: independence must be asserted, not assumed. Treating un-annotated evidence as
    # self-independent let two lines of one file satisfy INFERENCE and C2 -- the control failed open.
    def groups(require_explicit):
        gs, unlabelled = set(), 0
        for i, e in enumerate(ev):
            g = e.get("independence_group")
            if g: gs.add(g)
            else: unlabelled += 1
        return gs, unlabelled
    if cc == "INFERENCE":
        if not f.get("derivation"): err(out, fid, "E020", "INFERENCE without written derivation")
        gs, unlabelled = groups(True)
        if unlabelled:
            err(out, fid, "E022", f"{unlabelled} evidence item(s) without independence_group -- "
                                  f"independence must be asserted, not assumed (ES-1 s4)")
        if len(gs) < 2:
            err(out, fid, "E021", "INFERENCE requires >=2 INDEPENDENT evidence items (ES-1 s4)")

    # --- confidence ---------------------------------------------------------
    conf = f.get("confidence") or {}
    lvl = conf.get("level")
    if lvl not in LEVELS: err(out, fid, "E030", f"invalid confidence level '{lvl}'")
    if lvl == "C0": err(out, fid, "E031", "C0 is never publishable -- delete or convert to UNKNOWN")
    if not conf.get("basis"): err(out, fid, "E032", "confidence without award basis (CC-1 s1)")
    if lvl in ("C2","C3","C4"):
        gs, unlabelled = groups(True)
        if unlabelled:
            err(out, fid, "E037", f"{lvl} claimed with {unlabelled} evidence item(s) lacking independence_group "
                                  f"-- independence must be asserted, not assumed (ES-1 s4)")
        if len(gs) < 2:
            err(out, fid, "E033", f"{lvl} claimed with <2 independent evidence groups")
        if not (f.get("disconfirming_check") or "").strip():
            err(out, fid, "E034", f"{lvl} requires a recorded disconfirming search (BSR-06)")
    if lvl in ("C3","C4") and not any(e.get("kind") == "TOOL_OUTPUT" for e in ev):
        err(out, fid, "E035", f"{lvl} requires deterministic tool corroboration (CC-1 s1)")
    if lvl == "C4" and not any(e.get("kind") in ("TEST_RESULT","RUNTIME_ARTIFACT") for e in ev):
        err(out, fid, "E036", "C4 requires a reproduced execution artifact")

    # --- severity -----------------------------------------------------------
    sev = f.get("severity") or {}
    if sev.get("level") not in SEV: err(out, fid, "E040", f"invalid severity '{sev.get('level')}'")
    if not sev.get("rationale"): err(out, fid, "E041", "severity without rationale")
    if sev.get("level") in ("HIGH","CRITICAL") and lvl in ("C0","C1"):
        err(out, fid, "E042", f"{sev.get('level')} at {lvl} -- publish as a verification task, not a finding (CC-1 s2)")
    if sev.get("exploitability_assessed") is False and re.search(r"\bvulnerab", st, re.I):
        err(out, fid, "E043", "described as a vulnerability without exploitability assessment -- it is a weakness")
    # RS-1 s1: the matrix is applied mechanically so two runs agree. Nothing enforced it before.
    imp, lik = sev.get("impact"), sev.get("likelihood")
    if imp in MATRIX and lik in MATRIX[imp]:
        expect = MATRIX[imp][lik]
        if sev.get("level") != expect:
            err(out, fid, "E044", f"severity {sev.get('level')} contradicts the RS-1 matrix: "
                                  f"{imp} x {lik} = {expect}")
    elif sev.get("level") in SEV:
        if imp is None: err(out, fid, "E045", "severity without impact -- the RS-1 matrix cannot be applied")
        if lik is None: err(out, fid, "E046", "severity without likelihood -- the RS-1 matrix cannot be applied")

    # --- class ceilings & forbidden claims ----------------------------------
    order = {"FACT":0,"INFERENCE":1,"HYPOTHESIS":2,"UNKNOWN":3,"EXTERNAL_VALIDATION_REQUIRED":4}
    undecidable = False
    for pat, maxcls in UNDECIDABLE:
        if re.search(pat, st, re.I):
            undecidable = True
            if cc in ("FACT","INFERENCE") and order.get(cc,9) < order[maxcls]:
                err(out, fid, "E050", f"undecidable-register claim asserted as {cc}; max is {maxcls} (ES-1 s2)")
    # CC-1 s1: any claim in the undecidable register is capped at C2 and must carry the question.
    if undecidable:
        if lvl in ("C3","C4"):
            err(out, fid, "E052", f"undecidable-register claim awarded {lvl}; CC-1 s1 caps it at C2")
        if not ((f.get("external_validation") or {}).get("question")):
            err(out, fid, "E054", "undecidable-register claim without external_validation.question (CC-1 s1)")
    # CC-1 s1: CONVENIENCE sampling caps any derived finding at C1.
    sel = (coverage_meta.get(f.get("coverage_ref")) or {}).get("selection")
    if sel == "CONVENIENCE" and lvl in ("C2","C3","C4"):
        err(out, fid, "E053", f"{lvl} derived from CONVENIENCE sampling; CC-1 s1 caps it at C1")
    for pat, why in FORBIDDEN:
        if re.search(pat, st, re.I) or re.search(pat, json.dumps(f.get("remediation") or {}), re.I):
            err(out, fid, "E051", why)

    # --- falsifiability & coverage -----------------------------------------
    if not (f.get("how_to_refute") or "").strip():
        err(out, fid, "E060", "missing how_to_refute -- finding is not falsifiable (ES-1 s5)")
    if coverage_ids and f.get("coverage_ref") not in coverage_ids:
        err(out, fid, "E061", f"coverage_ref '{f.get('coverage_ref')}' not found in coverage records (BSR-07)")
    # Prose routinely cites other coverage records to bound a claim ("per the edges in COV-RDA06-edges").
    # A reader who follows that pointer must land on a real record; the shipped example itself carried a
    # dangling one. Structured coverage_ref is checked above, so only look at free text here.
    if coverage_ids:
        prose = " ".join(str(f.get(k, "")) for k in
                         ("statement", "blast_radius", "why_it_matters", "how_to_refute", "disconfirming_check"))
        for ref in sorted(set(re.findall(r"\bCOV-[A-Za-z0-9][A-Za-z0-9_-]*", prose))):
            if ref not in coverage_ids:
                err(out, fid, "E063", f"prose cites coverage record '{ref}', which does not exist (BSR-07)")
    if cc == "EXTERNAL_VALIDATION_REQUIRED" and not ((f.get("external_validation") or {}).get("question")):
        err(out, fid, "E062", "EXTERNAL_VALIDATION_REQUIRED without the question to ask")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("findings"); ap.add_argument("--coverage")
    ap.add_argument("--schema", help="path to finding.schema.json (default: ../schemas relative to this script)")
    ap.add_argument("--strict", action="store_true",
                    help="treat abstention warnings and quarantined findings as violations (publish gate)")
    a = ap.parse_args()
    try:
        data = json.load(open(a.findings, encoding="utf-8"))
    except Exception as e:
        print(f"ERROR reading {a.findings}: {e}"); return 3
    findings = data["findings"] if isinstance(data, dict) and "findings" in data else data

    schema_path = a.schema or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           "..", "schemas", "finding.schema.json")
    schema = None
    try:
        schema = json.load(open(schema_path, encoding="utf-8"))
    except Exception as e:
        print(f"WARN: finding schema unreadable at {schema_path} ({e}); schema checks skipped")

    cov_ids, cov_meta = set(), {}
    if a.coverage:
        try:
            cov = json.load(open(a.coverage, encoding="utf-8"))
            recs = cov if isinstance(cov, list) else cov.get("coverage", [])
            cov_ids = {c.get("coverage_id") for c in recs}
            cov_meta = {c.get("coverage_id"): {"selection": (c.get("inspected") or {}).get("selection"),
                                               "score": c.get("coverage_score")} for c in recs}
        except Exception as e:
            print(f"WARN: coverage file unreadable ({e}); skipping coverage cross-check")

    out = []
    for f in findings: check(f, out, cov_ids, cov_meta, schema)
    for fid, code, msg in out: print(f"[{code}] {fid}: {msg}")

    n = len(findings)
    classes = Counter(f.get("claim_class") for f in findings)
    conf = Counter((f.get("confidence") or {}).get("level") for f in findings)
    quarantined = sum(1 for f in findings if f.get("quarantined"))
    unknown_rate = (classes["UNKNOWN"] + classes["EXTERNAL_VALIDATION_REQUIRED"]) / n if n else 0
    corroborated = sum(conf[l] for l in ("C2","C3","C4")) / n if n else 0
    print(f"\nfindings={n} violations={len(out)} quarantined={quarantined}")
    print(f"class_distribution={dict(classes)}")
    print(f"confidence_distribution={dict(conf)}")
    print(f"unknown_rate={unknown_rate:.3f}  corroboration_rate={corroborated:.3f}")
    warnings = []
    if n and unknown_rate == 0:
        warnings.append("[W100] ZERO UNKNOWNS -- flagged as suspect (BSR/CC-1 s4). Real repositories always "
                        "contain undecidable questions; their absence indicates uncertainty was resolved by assertion.")
    if n and unknown_rate > 0.5:
        warnings.append("[W101] unknown_rate > 0.5 -- insufficient access. Rescope rather than publish.")
    if n and corroborated < 0.6:
        warnings.append("[W102] corroboration_rate < 0.6 -- majority of findings are single-source.")
    if quarantined:
        warnings.append(f"[W103] {quarantined} quarantined finding(s) present -- these MUST NOT reach any "
                        f"executive output (ES-1 s3).")
    for w in warnings: print(w)
    if a.strict and warnings:
        print(f"\n--strict: {len(warnings)} warning(s) escalated to violations")
        return 1
    return 1 if out else 0

if __name__ == "__main__":
    sys.exit(main())
