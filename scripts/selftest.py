#!/usr/bin/env python3
"""RDA self-test: proves the enforcement machinery actually enforces.

The pack's central claim is "enforced, not asserted". That claim is only worth anything if the gates are
themselves tested, so this script checks both directions for each one: the conforming input passes, and a
deliberately malformed input is rejected with the specific codes that are supposed to catch it. A linter that
returns 0 on everything would sail through a one-sided test.

Zero dependencies, like the rest of the pack. Run from anywhere:  python3 scripts/selftest.py
Exit codes: 0 all passed, 1 one or more failed.
"""
import json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = sys.executable
results = []


def run(*args, cwd=ROOT):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


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


def lint_coverage(adjudication, inspected_count, note=None):
    rec = {"coverage_id": "COV-1", "skill_id": "rda-11",
           "population": {"definition": "routes", "count": inspected_count, "source": "grep"},
           "inspected": {"count": inspected_count, "selection": "EXHAUSTIVE"},
           "method": "read", "blind_spots": []}
    if adjudication is not None:
        rec["adjudication"] = adjudication
    if note is not None:
        rec["note"] = note
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

# --- summary ----------------------------------------------------------------------------------------
failed = [n for n, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
if failed:
    print("FAILED: " + "; ".join(failed))
sys.exit(1 if failed else 0)
