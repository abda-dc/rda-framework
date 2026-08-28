#!/usr/bin/env python3
"""RDA self-test: proves the enforcement machinery actually enforces.

The pack's central claim is "enforced, not asserted". That claim is only worth anything if the gates are
themselves tested, so this script checks both directions for each one: the conforming input passes, and a
deliberately malformed input is rejected with the specific codes that are supposed to catch it. A linter that
returns 0 on everything would sail through a one-sided test.

Zero dependencies, like the rest of the pack. Run from anywhere:  python3 scripts/selftest.py
Exit codes: 0 all passed, 1 one or more failed.
"""
import copy, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = sys.executable
results = []
CODE_RE = re.compile(r"\[(E\d{3}|W\d{3})\]")
SEEN = set()


def run(*args, cwd=ROOT):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (p.stdout or "") + (p.stderr or "")
    SEEN.update(CODE_RE.findall(out))
    return p.returncode, out


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"\n          {detail}" if detail and not cond else ""))


def script(n):
    return os.path.join(HERE, n)


print("RDA self-test\n")

# --- 1. pack conformance ---------------------------------------------------------------------------
print("[1] pack conformance")
rc, out = run(PY, script("validate_pack.py"), os.path.join(ROOT, "skills"), "--budgets")
check("validate_pack: full pack is clean", rc == 0 and "problems=0" in out, out.strip()[-400:])
check("validate_pack: reports 38 skills", "skills=38" in out, out.strip()[-200:])

# The closure check must actually catch a broken profile, not pass vacuously. Reintroduce the real defect
# P4A originally shipped with -- RDA-14/RDA-17 need RDA-19, which lived only in the later P4B phase.
inst = open(script("install.sh"), encoding="utf-8").read()
broken = re.sub(r'(P4A\)\s*IDS="[^"]*?)\s+19("\s*;;)', r"\1\2", inst)
check("selftest fixture: P4A regression differs from install.sh", broken != inst,
      "could not build the negative fixture; the P4A line format changed")
with tempfile.TemporaryDirectory() as td:
    bad_inst = os.path.join(td, "install-broken.sh")
    open(bad_inst, "w", encoding="utf-8", newline="\n").write(broken)
    rc, out = run(PY, script("validate_pack.py"), os.path.join(ROOT, "skills"), "--profiles", bad_inst)
    check("validate_pack: catches a non-dependency-closed profile",
          rc == 1 and "E140" in out and "RDA-19" in out, out.strip()[-400:])

# --- 2. adapters are generated, not hand-maintained -------------------------------------------------
print("\n[2] adapter drift")
rc, out = run(PY, script("generate_adapters.py"), "--check")
check("generate_adapters --check: committed tree matches generator output", rc == 0 and "match" in out,
      out.strip()[-600:])

# --- 3. the findings gate, both directions ----------------------------------------------------------
print("\n[3] findings gate")
clean = os.path.join(ROOT, "templates", "example-findings.json")
invalid = os.path.join(ROOT, "templates", "example-findings-invalid.json")
cov = os.path.join(ROOT, "templates", "example-coverage.json")

rc, out = run(PY, script("validate_findings.py"), clean, "--coverage", cov)
check("conforming findings pass with zero violations", rc == 0 and "violations=0" in out, out.strip()[-600:])

# --strict escalates the abstention warnings. The shipped example has zero UNKNOWNs and is majority
# single-source, so it is *expected* to fail --strict; that is the flag working, not a broken example.
rc, out = run(PY, script("validate_findings.py"), clean, "--coverage", cov, "--strict")
check("--strict escalates abstention warnings to failures", rc == 1 and "W100" in out, out.strip()[-400:])

rc, out = run(PY, script("validate_findings.py"), invalid, "--coverage", cov)
check("adversarial findings are rejected", rc == 1, out.strip()[-400:])

# Each code below exists to stop a specific way an audit goes wrong. Assert them individually so a
# regression that silently disables one is visible, rather than hiding inside a total count.
EXPECTED = {
    "E000": "schema validation",
    "E010": "banned deployment/scale/compliance assertion from source alone",
    "E013": "numeric self-confidence",
    "E014": "evidence locator is not path#Lstart-Lend",
    "E020": "INFERENCE without written derivation",
    "E021": "INFERENCE without two independent evidence items",
    "E031": "confidence asserted without basis",
    "E033": "C2+ without independent corroboration",
    "E041": "vulnerability severity without exploitability assessment",
    "E044": "severity contradicts the RS-1 matrix",
    "E050": "person-day point estimate",
    "E060": "finding is not falsifiable",
    "E061": "coverage_ref does not resolve",
    "E062": "EXTERNAL_VALIDATION_REQUIRED with no question",
    "E063": "prose cites a coverage record that does not exist",
    "E064": "injection-class finding with no attacker_controls chain",
}
missing = sorted(c for c in EXPECTED if f"[{c}]" not in out)
check(f"all {len(EXPECTED)} representative violation codes fire", not missing,
      "codes that did NOT fire: " + ", ".join(f"{c} ({EXPECTED[c]})" for c in missing))

# A gate that rejects everything is as useless as one that accepts everything. The clean example above
# already proves the converse, but assert no overlap explicitly.
rc_clean, out_clean = run(PY, script("validate_findings.py"), clean, "--coverage", cov)
check("no violation code fires on the conforming example",
      not re.findall(r"^\[E\d+\]", out_clean, re.M), out_clean.strip()[-400:])

# The injection adjudication gate (RDA-11 s5b), both directions. This exists because validation against a
# seeded repository showed the "plausible-vulnerability flood" the skill documents survives its own
# controls: an eval() over a module-level constant was reported as MAJOR code injection. The gate is only
# worth anything if the correctly-adjudicated form passes, so assert that too -- otherwise the fix is just
# a blanket ban on reporting injection.
INJ = {
    "id": "F-INJ", "skill_id": "RDA-11", "run_id": "run-selftest",
    "title": "Code injection via eval() in the templating helper",
    "claim_class": "INFERENCE",
    "statement": "The templating module calls eval() on a format string, permitting code injection.",
    "derivation": "Fact 1 shows the eval call. Fact 2 shows the format string's definition.",
    "evidence": [
        {"kind": "SOURCE", "locator": "src/templating.py#L12-L12",
         "commit": "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4", "independence_group": "read"},
        {"kind": "SOURCE", "locator": "src/templating.py#L7-L7",
         "commit": "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4", "independence_group": "grep"}],
    "confidence": {"level": "C3", "basis": "CC-1 s1: two independent source citations"},
    "coverage_ref": "COV-INJ",
    "severity": {"level": "HIGH", "impact": "MAJOR", "likelihood": "POSSIBLE",
                 "rationale": "Arbitrary code execution in the rendering path"},
    "blast_radius": "Invoice rendering only.",
    "how_to_refute": "Show the evaluated format string is a module constant.",
    "disconfirming_check": "Read every caller of render_header for a caller-supplied template.",
    "remediation": {"action": "Replace eval with str.format over an explicit mapping."},
    "standard_refs": ["CWE-94"], "quarantined": False,
}


def lint_finding(extra):
    f = dict(INJ)
    f.update(extra)
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump([f], fh)
    try:
        return run(PY, script("validate_findings.py"), path)
    finally:
        os.unlink(path)


_, out_no_ac = lint_finding({})
check("injection finding with no attacker_controls is rejected (E064)",
      "[E064]" in out_no_ac, out_no_ac.strip()[-300:])

_, out_vague = lint_finding({"attacker_controls": "the tenant name argument"})
check("attacker_controls that dodges the structure/value question is rejected (E065)",
      "[E065]" in out_vague, out_vague.strip()[-300:])

_, out_ok = lint_finding({"attacker_controls":
                          "Caller supplies tenant, reference and currency as values only; the executed "
                          "structure is the module constant _HEADER, so no attacker-controlled structure "
                          "reaches the eval sink."})
check("a properly adjudicated injection finding passes the gate",
      "[E064]" not in out_ok and "[E065]" not in out_ok, out_ok.strip()[-300:])

# A stated adjudication count is not an adjudication. Validation produced a coverage record claiming
# "members 7, adjudicated 7" whose note listed six routes and disposed of all of them with one phrase,
# burying a token-minting endpoint. These checks make the count derive from a per-member list.
COV_FINDING = dict(INJ)
COV_FINDING.update({"id": "F-1", "coverage_ref": "COV-1",
                    "attacker_controls": "Caller supplies a value only; the executed structure is a module "
                                         "constant, so no attacker-controlled structure reaches the sink."})


def lint_coverage(adjudication, inspected_count, note=None, extra=None):
    rec = {"coverage_id": "COV-1", "skill_id": "rda-11",
           "population": {"definition": "routes", "count": inspected_count, "source": "grep"},
           "inspected": {"count": inspected_count, "selection": "EXHAUSTIVE"},
           "method": "read", "blind_spots": []}
    if adjudication is not None:
        rec["adjudication"] = adjudication
    if note is not None:
        rec["note"] = note
    if extra:
        rec.update(extra)
    paths = []
    for payload in ([COV_FINDING], {"coverage": [rec]}):
        fd, p = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh)
        paths.append(p)
    try:
        return run(PY, script("validate_findings.py"), paths[0], "--coverage", paths[1])
    finally:
        for p in paths:
            os.unlink(p)


_, cov_short = lint_coverage([{"member": "/health", "verdict": "NOT_APPLICABLE"}], 7)
check("adjudication count asserted above the listed members is rejected (E066)",
      "[E066]" in cov_short, cov_short.strip()[-300:])

_, cov_blank = lint_coverage([{"member": "/health", "verdict": "NOT_APPLICABLE"},
                              {"member": "", "verdict": "MITIGATED"}], 2)
check("blank or duplicated population members are rejected (E068)",
      "[E068]" in cov_blank, cov_blank.strip()[-300:])

_, cov_dropped = lint_coverage([{"member": "/impersonate", "verdict": "CONFIRMED_WEAKNESS"}], 1)
check("a confirmed member with no finding to carry it is rejected (E067)",
      "[E067]" in cov_dropped, cov_dropped.strip()[-300:])

_, cov_ok = lint_coverage([{"member": "/health", "verdict": "NOT_APPLICABLE", "basis": "no data access"},
                           {"member": "/invoices", "verdict": "CONFIRMED_WEAKNESS", "ref": "F-1",
                            "basis": "no tenant check"}], 2)
check("an honestly adjudicated population passes the coverage gate",
      not any(c in cov_ok for c in ("[E066]", "[E067]", "[E068]")), cov_ok.strip()[-300:])

# E066-E068 only bite once an adjudication list exists, so omitting the list entirely was still a way
# out. Disposing of a whole population in one sentence is itself a verdict on every member, and the
# run that motivated this fix did exactly that: "members 7, adjudicated 7 ... All auth-checked."
_, cov_blanket = lint_coverage(None, 6, note="Six route handlers reviewed. All auth-checked.")
check("a blanket verdict over a population with no per-member record is rejected (E069)",
      "[E069]" in cov_blanket, cov_blanket.strip()[-300:])

_, cov_negblanket = lint_coverage(None, 6, note="Reviewed the route table; no endpoints are unprotected.")
check("the same blanket verdict stated in the negative is also rejected (E069)",
      "[E069]" in cov_negblanket, cov_negblanket.strip()[-300:])

_, cov_census = lint_coverage(None, 34, note="All 34 tracked files read at HEAD. git ls-files | wc -l = 34.")
check("an honest census that counts without disposing is still allowed",
      "[E069]" not in cov_census, cov_census.strip()[-300:])

# Quieter than a blanket verdict and just as empty: asserting that the adjudication happened without
# recording any of it. A second model produced exactly this -- "6/6 auth verdicts ... 20/20
# adjudicated" -- and slipped past the blanket-disposal check because it disposes of nothing.
_, cov_claim = lint_coverage(None, 6, extra={"adjudicated": 6})
check("an adjudication count claimed with no list to back it is rejected (E070)",
      "[E070]" in cov_claim, cov_claim.strip()[-300:])

_, cov_claim_note = lint_coverage(None, 6, note="6/6 auth verdicts. Combined raw candidates 20/20 adjudicated.")
check("the same claim made only in prose is also rejected (E070)",
      "[E070]" in cov_claim_note, cov_claim_note.strip()[-300:])

_, cov_read = lint_coverage(None, 34, note="34 tracked files read at HEAD; git ls-files | wc -l = 34.")
check("reading a population is an action, not a verdict, and stays legal",
      "[E070]" not in cov_read, cov_read.strip()[-300:])


fd, badpath = tempfile.mkstemp(suffix=".json")
os.close(fd)
with open(badpath, "w", encoding="utf-8", newline="\n") as fh:
    fh.write('[{"id":"BAD-1","severity":"HIGH"},"not-an-object"]')
rc_bad, out_bad = run(PY, script("validate_findings.py"), badpath)
os.unlink(badpath)
check("malformed findings report violations instead of crashing",
      rc_bad == 1 and "Traceback" not in out_bad and "[E003]" in out_bad and "[E004]" in out_bad,
      out_bad.strip()[-400:])

# --- 4. citation verifier fails closed --------------------------------------------------------------
print("\n[4] citation verifier")
rc, out = run(PY, script("verify_citations.py"), clean, "--repo", ROOT)
check("unverifiable citations fail closed (exit 2, not 0)", rc == 2 and "quarantined" in out,
      out.strip()[-400:])

# --- 5. census arithmetic reconciles ----------------------------------------------------------------
print("\n[5] census")
bash = shutil.which("bash")
if not bash:
    check("census skipped: bash not on PATH", True)
else:
    with tempfile.TemporaryDirectory() as td:
        # The pack's own git repo is a perfectly good census target.
        rc, out = run(bash, script("rda_census.sh"), ROOT, os.path.join(td, "out"))
        cj = os.path.join(td, "out", "census.json")
        ok = rc == 0 and os.path.exists(cj)
        check("census runs and writes census.json", ok, out.strip()[-400:])
        if ok:
            try:
                c = json.load(open(cj, encoding="utf-8"))
            except Exception as e:
                check("census.json is valid JSON", False, str(e)); c = None
            if c:
                check("census.json is valid JSON", True)
                f = c.get("files", {})
                check("file buckets reconcile against tracked total",
                      f.get("reconciliation") == "ok",
                      f"tracked={f.get('tracked')} classified_total={f.get('classified_total')} "
                      f"reconciliation={f.get('reconciliation')}")
                det = (c.get("loc") or {}).get("detail_file")
                check("loc.detail_file points at a file that exists",
                      det is None or os.path.exists(os.path.join(td, "out", os.path.basename(det))),
                      f"detail_file={det}")

# --- 6. every enforcement code is proven to fire ----------------------------------------------------
# A gate nobody has ever watched reject anything is indistinguishable from a gate whose condition is
# unreachable, and shipping one is the exact failure this pack exists to catch -- documented, not enforced.
# Sections 1-5 cover the load-bearing paths; this table drives one deliberate violation per remaining code.
# The guard at the end is the durable part: it diffs the codes the scripts can emit against the codes this
# run actually observed, so adding a check without a test fails the suite instead of passing quietly.
print("\n[6] every enforcement code fires")

BASE = json.load(open(os.path.join(ROOT, "templates", "example-findings.json"), encoding="utf-8"))["findings"][0]
CONF = dict(BASE.get("confidence") or {})
SEV = dict(BASE.get("severity") or {})
EXPLOIT = "The refund route is exploitable by any unauthenticated caller."


def _f(**kw):
    x = copy.deepcopy(BASE); x.update(kw); return x


def _drop(k):
    x = copy.deepcopy(BASE); x.pop(k, None); return x


def _ev(i, dropk=None, **kw):
    x = copy.deepcopy(BASE)
    if dropk:
        x["evidence"][i].pop(dropk, None)
    x["evidence"][i].update(kw)
    return x


def _one_group(**kw):
    x = copy.deepcopy(BASE)
    for e in x["evidence"]:
        e["independence_group"] = "G-SAME"
    x.update(kw)
    return x


def _no_tool_block():
    x = copy.deepcopy(BASE)
    for e in x["evidence"]:
        if e.get("kind") == "TOOL_OUTPUT":
            e.pop("tool", None)
    return x


def _no_corroboration(**kw):
    x = copy.deepcopy(BASE)
    x["evidence"] = [e for e in x["evidence"] if e.get("kind") != "TOOL_OUTPUT"]
    x.update(kw)
    return x


def _cov(cid, selection="EXHAUSTIVE", n=3):
    return [{"coverage_id": cid, "skill_id": "rda-11",
             "population": {"definition": "routes", "count": n, "source": "grep"},
             "inspected": {"count": n, "selection": selection},
             "method": "read", "blind_spots": []}]


def _lint(finding, coverage=None):
    paths = []
    fd, p1 = tempfile.mkstemp(suffix=".json"); os.close(fd)
    with open(p1, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"findings": [finding]}, fh)
    paths.append(p1)
    args = [PY, script("validate_findings.py"), p1]
    if coverage is not None:
        fd, p2 = tempfile.mkstemp(suffix=".json"); os.close(fd)
        with open(p2, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"coverage": coverage}, fh)
        paths.append(p2)
        args += ["--coverage", p2]
    try:
        return run(*args)[1]
    finally:
        for p in paths:
            os.unlink(p)


FINDING_CASES = [
    ("E000", "a field whose type violates the schema", _f(evidence="not-a-list"), None),
    ("E001", "a finding with no title", _drop("title"), None),
    ("E002", "a claim_class outside the enum", _f(claim_class="GUESS"), None),
    ("E010", "a FACT with zero evidence", _f(evidence=[]), None),
    ("E011", "an evidence kind outside the enum", _ev(0, kind="VIBES"), None),
    ("E012", "evidence with no locator", _ev(0, dropk="locator"), None),
    ("E013", "a locator that is not a path at all", _ev(0, locator="bad locator with spaces"), None),
    ("E014", "quote-bearing evidence with no commit pin", _ev(0, dropk="commit"), None),
    ("E015", "pinned evidence with no verbatim quote", _ev(0, dropk="quote"), None),
    ("E016", "TOOL_OUTPUT evidence with no tool block", _no_tool_block(), None),
    ("E017", "a whole-file locator on quote-bearing evidence", _ev(0, locator="src/app.py"), None),
    ("E020", "an INFERENCE with no written derivation", _f(claim_class="INFERENCE", derivation=None), None),
    ("E021", "an INFERENCE resting on one independence group", _one_group(claim_class="INFERENCE"), None),
    ("E022", "evidence with no independence_group", _ev(0, dropk="independence_group"), None),
    ("E030", "a confidence level outside the ladder", _f(confidence={"level": "C9", "basis": "x"}), None),
    ("E031", "C0 offered as publishable", _f(confidence={**CONF, "level": "C0"}), None),
    ("E032", "confidence with no basis", _f(confidence={"level": "C2"}), None),
    ("E033", "C3 resting on one independence group", _one_group(confidence={**CONF, "level": "C3"}), None),
    ("E034", "C3 with a blank disconfirming_check",
     _f(confidence={**CONF, "level": "C3"}, disconfirming_check="   "), None),
    ("E035", "C3 with no corroborating evidence kind",
     _no_corroboration(confidence={**CONF, "level": "C3"}), None),
    ("E036", "C4 claimed from repository contents", _f(confidence={**CONF, "level": "C4"}), None),
    ("E037", "an independence claim with no group recorded", _ev(0, dropk="independence_group"), None),
    ("E040", "a severity level outside the enum", _f(severity={**SEV, "level": "SPICY"}), None),
    ("E041", "severity with no rationale",
     _f(severity={k: v for k, v in SEV.items() if k != "rationale"}), None),
    ("E042", "CRITICAL asserted at C1",
     _f(confidence={**CONF, "level": "C1"},
        severity={**SEV, "level": "CRITICAL", "impact": "SEVERE", "likelihood": "LIKELY"}), None),
    ("E043", "vulnerability language with exploitability unassessed",
     _f(statement="The refund endpoint is a serious vulnerability in the payments service.",
        severity={**SEV, "exploitability_assessed": False}), None),
    ("E044", "a severity level the RS-1 matrix contradicts",
     _f(severity={**SEV, "level": "CRITICAL", "impact": "MINOR", "likelihood": "RARE"}), None),
    ("E045", "severity with no impact",
     _f(severity={k: v for k, v in SEV.items() if k != "impact"}), None),
    ("E046", "severity with no likelihood",
     _f(severity={k: v for k, v in SEV.items() if k != "likelihood"}), None),
    ("E050", "an undecidable-register claim asserted as FACT",
     _f(statement=EXPLOIT, claim_class="FACT"), None),
    ("E051", "a compliance verdict", _f(statement="The service is SOC 2 compliant."), None),
    ("E051b", "a compliance verdict in the other word order",
     _f(statement="The organisation is compliant with SOC 2 controls."), None),
    ("E052", "an undecidable-register claim awarded C3",
     _f(statement=EXPLOIT, claim_class="HYPOTHESIS", confidence={**CONF, "level": "C3"}), None),
    ("E053", "C3 derived from CONVENIENCE sampling",
     _f(confidence={**CONF, "level": "C3"}), _cov(BASE.get("coverage_ref"), "CONVENIENCE")),
    ("E054", "an undecidable-register claim with no question to ask",
     _f(statement=EXPLOIT, claim_class="HYPOTHESIS", external_validation={}), None),
    ("E060", "a finding with no how_to_refute", _drop("how_to_refute"), None),
    ("E061", "a coverage_ref pointing at no coverage record", copy.deepcopy(BASE), _cov("COV-NOPE")),
    ("E062", "EXTERNAL_VALIDATION_REQUIRED with no question",
     _f(claim_class="EXTERNAL_VALIDATION_REQUIRED", external_validation={}), None),
    ("W103", "a quarantined finding left in the artifact", _f(quarantined=True), None),
]

for code, desc, finding, coverage in FINDING_CASES:
    want = code.rstrip("b")
    out = _lint(finding, coverage)
    check(f"{want} rejects {desc}", f"[{want}]" in out, out.strip()[-300:])

# Pack-structure codes need a skills tree rather than a findings artifact. RDA-00 is the wrong base for
# these: it is CONTRACT_EXEMPT from the section rules and is allowed to quote the patterns it bans, so a
# mutation of it would pass vacuously. RDA-11 is an ordinary procedure skill and is subject to all of them.
_PACK_DIR = "rda-11-security-posture-review"
_src = open(os.path.join(ROOT, "skills", _PACK_DIR, "SKILL.md"), encoding="utf-8").read()
_fm_end = _src.index("---", 3) + 3
_FM, _BODY = _src[:_fm_end], _src[_fm_end:]


def _fmset(**kw):
    fm = _FM
    for k, v in kw.items():
        fm = re.sub(rf"(?m)^(\s*){k}:.*$", lambda m, k=k, v=v: f"{m.group(1)}{k}: {v}", fm, count=1)
    return fm


def _trim(b, n):
    lines = b.split("\n")
    return "\n".join(lines[:-n]) if n < len(lines) else b


def _swap_sections(b):
    b = b.replace("## Outputs", "## __TMP__", 1)
    b = b.replace("## Purpose", "## Outputs", 1)
    return b.replace("## __TMP__", "## Purpose", 1)


def _pack(write, extra=None):
    with tempfile.TemporaryDirectory() as td:
        os.mkdir(os.path.join(td, _PACK_DIR))
        text = write(_FM, _BODY)
        if text is not None:
            with open(os.path.join(td, _PACK_DIR, "SKILL.md"), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
        return run(PY, script("validate_pack.py"), td, *(extra or []))[1]


PACK_CASES = [
    ("E100", "a skill directory with no SKILL.md", lambda fm, b: None),
    ("E101", "a SKILL.md with no frontmatter", lambda fm, b: "no frontmatter here at all\n" + b),
    ("E102", "frontmatter missing required keys", lambda fm, b: "---\nname: x\n---\n" + b),
    ("E103", "a name that disagrees with its directory", lambda fm, b: _fmset(name="rda-99-elsewhere") + b),
    ("E104", "a name outside the permitted charset", lambda fm, b: _fmset(name="RDA_11_Bad!") + b),
    ("E105", "a name over 64 characters", lambda fm, b: _fmset(name="a" * 70) + b),
    ("E107", "a description over the portability budget", lambda fm, b: _fmset(description="x" * 300) + b),
    ("E108", "a description over the 1024-char spec limit",
     lambda fm, b: _fmset(description="x" * 1200) + b),
    ("E110", "a missing required section", lambda fm, b: fm + b.replace("## Inputs", "## Inputz", 1)),
    ("E111", "required sections out of order", lambda fm, b: fm + _swap_sections(b)),
    ("E112", "a skill over the line budget", lambda fm, b: fm + b + "\nfiller line\n" * 400),
    ("E113", "a skill too thin to be implementation-ready",
     lambda fm, b: fm + "\n# RDA-11\n\nInherits RDA-00.\n\n## Purpose\n\nToo short.\n"),
    ("E114", "no kernel inheritance note near the top",
     lambda fm, b: fm + b[:1500].replace("RDA-00", "XX-00").replace("Inherits", "Follows") + b[1500:]),
    ("E120", "a banned pattern in the body",
     lambda fm, b: fm + _trim(b, 6) + "\n\nReported with confidence 0.85 overall.\n"),
    ("E130", "a dependency outside the RDA range",
     lambda fm, b: _fmset(depends_on='"RDA-99"') + b),
    ("W131", "a dependency that is not in this install",
     lambda fm, b: _fmset(depends_on='"RDA-02"') + b),
]
for code, desc, writer in PACK_CASES:
    out = _pack(writer)
    check(f"{code} rejects {desc}", f"[{code}]" in out or code in out, out.strip()[-300:])

# E141 needs the real pack: a profile that lists a skill id the pack does not contain.
_unknown_prof = re.sub(r'(P4A\)\s*IDS=")', r"\g<1>99 ", inst, count=1)
with tempfile.TemporaryDirectory() as td:
    _bad = os.path.join(td, "install-unknown.sh")
    open(_bad, "w", encoding="utf-8", newline="\n").write(_unknown_prof)
    _, out = run(PY, script("validate_pack.py"), os.path.join(ROOT, "skills"), "--profiles", _bad)
    check("E141 rejects a profile listing an unknown skill", "E141" in out, out.strip()[-300:])


# The guard. ALL_CODES is derived from the scripts themselves, so a newly added code is picked up here
# automatically. UNPROVEN is the explicit, shrinkable residual -- checks that exist but that nothing in this
# suite has yet been able to trigger. Both directions fail: an unlisted code with no test, and a listed code
# that has since gained one. That keeps the list honest instead of letting it rot into an excuse.
ALL_CODES = set()
for _s in ("validate_findings.py", "validate_pack.py", "verify_citations.py"):
    _p = script(_s)
    if os.path.exists(_p):
        ALL_CODES.update(re.findall(r"""["'\[]((?:E|W)\d{3})["'\]]""", open(_p, encoding="utf-8").read()))

UNPROVEN = set()  # empty is the goal state: every code the scripts can emit is triggered above.
missing = ALL_CODES - SEEN
untested = sorted(missing - UNPROVEN)
stale = sorted(UNPROVEN - missing)
check(f"every enforcement code is exercised ({len(ALL_CODES) - len(missing)}/{len(ALL_CODES)} seen)",
      not untested, "codes with no test: " + ", ".join(untested))
check("the unproven-code list has no stale entries", not stale,
      "these are now exercised and should be removed from UNPROVEN: " + ", ".join(stale))

# --- 7. the documentation tells the truth -----------------------------------------------------------
# The README claimed "48 violations across 26 codes" and "15 assertions" long after both figures had changed;
# the fixture actually trips 44 across 28, and the suite runs far more than 15. Numbers in prose rot silently,
# which is precisely the failure this pack exists to prevent, so the figures the docs quote are measured here.
print("\n[7] documented figures match measured ones")

_, _inv_out = run(PY, script("validate_findings.py"),
                  os.path.join(ROOT, "templates", "example-findings-invalid.json"))
_inv_codes = CODE_RE.findall(_inv_out)
_n_viol, _n_codes = len(_inv_codes), len(set(_inv_codes))

for _d in (os.path.join(ROOT, "README.md"), os.path.join(ROOT, "docs", "00-START-HERE.md")):
    _name = os.path.basename(_d)
    _t = open(_d, encoding="utf-8").read()
    _m = re.search(r"(\d+) violations across (\d+)[^\d]{0,15}codes", _t)
    check(f"{_name} quotes the real invalid-fixture figures",
          _m is not None and (int(_m.group(1)), int(_m.group(2))) == (_n_viol, _n_codes),
          f"doc says {_m.groups() if _m else '(no figure found)'}, measured ({_n_viol}, {_n_codes})")
    _n = len(ALL_CODES)
    check(f"{_name} quotes the real enforcement-code total",
          f"{_n}/{_n} codes" in _t or f"{_n} error codes" in _t,
          f"neither '{_n}/{_n} codes' nor '{_n} error codes' appears in {_name}")


failed = [n for n, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
if failed:
    print("FAILED: " + "; ".join(failed))
sys.exit(1 if failed else 0)
