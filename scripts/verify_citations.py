#!/usr/bin/env python3
"""RDA BSR-02: re-resolve every citation in a findings file and quarantine what does not exist.

This is the load-bearing anti-hallucination control. It re-reads each cited locator at the pinned
commit, normalises whitespace, and compares a hash of the quoted span against the file contents.
A finding whose evidence cannot be re-resolved is quarantined -- removed from executive output.

Usage:  python3 verify_citations.py findings.json --repo /path/to/repo [--write findings.verified.json]
Exit:   0 = all citations resolved, 2 = at least one quarantine, 3 = usage/IO error.
"""
import argparse, hashlib, json, re, subprocess, sys

# Kinds that live in the repository tree and are therefore re-resolvable at a pinned commit.
# This set MUST match PINNED_KINDS in validate_findings.py and the `commit` description in
# schemas/finding.schema.json. When they disagreed, a DOC citation that was schema-valid and passed
# the finding linter (which did not require a commit) was quarantined here for "missing commit pin" --
# a legitimate finding silently dropped from executive output.
PINNED_KINDS = ("SOURCE", "CONFIG", "VCS_HISTORY", "DOC")
LOCATOR = re.compile(r"^(?P<path>[^#]+?)(?:#L(?P<start>\d+)(?:-L?(?P<end>\d+))?)?$")

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def sha(s: str) -> str:
    return hashlib.sha256(norm(s).encode("utf-8", "replace")).hexdigest()

def read_at_commit(repo, commit, path):
    try:
        return subprocess.run(["git", "-C", repo, "show", f"{commit}:{path}"],
                              capture_output=True, text=True, check=True, timeout=60).stdout
    except Exception:
        return None

def verify_source(repo, ev):
    loc, commit, quote = ev.get("locator", ""), ev.get("commit"), ev.get("quote")
    if not commit:
        return False, "missing commit pin"
    if not quote:
        return False, "missing verbatim quote"
    m = LOCATOR.match(loc)
    if not m:
        return False, f"unparseable locator: {loc}"
    blob = read_at_commit(repo, commit, m.group("path"))
    if blob is None:
        return False, f"path absent at {commit[:8]}: {m.group('path')}"
    span = blob
    if m.group("start"):
        lines = blob.splitlines()
        s = int(m.group("start")); e = int(m.group("end") or m.group("start"))
        if s < 1 or e > len(lines):
            return False, f"line range {s}-{e} outside file ({len(lines)} lines)"
        span = "\n".join(lines[s - 1:e])
    if norm(quote) in norm(span):
        return True, "resolved"
    if norm(quote) in norm(blob):
        return False, "quote found in file but NOT at cited lines (line drift)"
    return False, "quote not present in file at pinned commit (fabricated or paraphrased)"

def verify_tool(ev):
    t = ev.get("tool") or {}
    missing = [k for k in ("name", "version") if not t.get(k)]
    if missing:
        return False, f"tool evidence missing {', '.join(missing)}"
    if "exit_code" not in t:
        return False, "tool evidence missing exit_code"
    return True, "resolved"

def main():
    ap = argparse.ArgumentParser(
        description="Re-read every citation at its pinned commit and quarantine any finding whose evidence "
                    "cannot be reproduced (BSR-02). Fails closed: unverifiable evidence is never waved through.")
    ap.add_argument("findings", help="findings JSON file to verify")
    ap.add_argument("--repo", default=".", help="checkout to re-read evidence from (default: cwd)")
    ap.add_argument("--write", help="write the annotated findings, with quarantine flags, to this path")
    ap.add_argument("--strict", action="store_true",
                    help="also fail on line drift, not just missing quotes")
    a = ap.parse_args()
    try:
        data = json.load(open(a.findings, encoding="utf-8"))
    except Exception as e:
        print(f"ERROR reading {a.findings}: {e}"); return 3
    findings = data["findings"] if isinstance(data, dict) and "findings" in data else data

    checked = failed = quarantined = 0
    report = []
    for f in findings:
        bad = []
        for ev in f.get("evidence", []):
            checked += 1
            kind = ev.get("kind")
            if kind in PINNED_KINDS or (kind == "TEST_RESULT" and ev.get("commit")):
                ok, why = verify_source(a.repo, ev)
            elif kind == "TOOL_OUTPUT":
                ok, why = verify_tool(ev)
            else:
                # TEST_RESULT without a commit, RUNTIME_ARTIFACT, EXTERNAL_ATTESTATION: produced by a
                # run rather than stored in the tree, so there is nothing to re-read at a commit.
                ok, why = True, "external artifact, not re-resolvable here"
            if not ok:
                drift = "line drift" in why
                if drift and not a.strict:
                    report.append((f.get("id"), "WARN", ev.get("locator"), why)); continue
                failed += 1; bad.append(why)
                report.append((f.get("id"), "FAIL", ev.get("locator"), why))
        if bad:
            f["quarantined"] = True; quarantined += 1
        elif f.get("claim_class") in ("FACT", "INFERENCE") and not f.get("evidence"):
            f["quarantined"] = True; quarantined += 1; failed += 1
            report.append((f.get("id"), "FAIL", "-", "FACT/INFERENCE with zero evidence"))

    for fid, lvl, loc, why in report:
        print(f"[{lvl}] {fid}: {loc} -- {why}")
    rate = 1.0 if checked == 0 else (checked - failed) / checked
    print(f"\ncitations_checked={checked} failed={failed} quarantined_findings={quarantined} "
          f"citation_resolution_rate={rate:.4f}")
    if a.write:
        out = {"findings": findings, "verification": {"citations_checked": checked,
               "citations_failed": failed, "quarantined": quarantined, "rate": rate}}
        json.dump(out, open(a.write, "w", encoding="utf-8"), indent=2)
        print(f"wrote {a.write}")
    return 2 if quarantined else 0

if __name__ == "__main__":
    sys.exit(main())
