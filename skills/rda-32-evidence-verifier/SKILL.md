---
name: rda-32-evidence-verifier
description: Adversarial assurance gate that re-resolves every citation, blindly re-derives a seeded sample, perturbation-tests verdicts and existence-checks named artifacts; run before any report ships.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-32"
  layer: "5-synthesis"
  risk_class: "HIGH_HARM"
  tier: "core"
  depends_on: "RDA-02..RDA-31"
---

# RDA-32 · Evidence Verifier

Inherits RDA-00. After the kernel this is the most important skill in the pack, and the only one authorised to invalidate a run.

## Purpose
Test the finding set adversarially — mechanically, blindly, under perturbation, and against external reality — then
either confirm, downgrade or quarantine each finding and publish the audit-quality metrics that gate the run.

## Business value
An unverified audit is worse than no audit: a plausible false finding consumes reviewer time, misdirects remediation
budget, and once discovered discredits every true finding beside it. This is what makes the rest defensible.

## When to use
Every run, always, before RDA-33 synthesis and before anything reaches an executive reader. Mandatory when audit
output leaves the engineering org. Never deferred to "if time allows" — RDA-01 reserves its budget up front.

## When NOT to use
As a second author: it does not improve, complete, rewrite or repair findings, and it does not analyse the
repository. If it starts producing new claims about the code, it has stopped being a verifier.

## Inputs
`findings.json` from every executed skill · coverage records · the run manifest with commit pins and tool versions ·
the repository at those pins · `scripts/verify_citations.py` · a fresh-context mechanism · network for existence checks
(or a declared degradation).

## Procedure

**1. Pass A — MECHANICAL citation re-resolution, 100% of findings.**
```
python3 scripts/verify_citations.py findings.json --repo . --write findings.verified.json; echo "exit=$?"
jq '[.[]|select(.quarantined==true)]|length'                       findings.verified.json
jq -r '.[]|select(.quarantined==true)|[.id,.skill_id]|@tsv'        findings.verified.json > vf/quarantine.tsv
```
Exit 2 means at least one quarantine. Any citation that does not re-resolve at the pinned commit **quarantines its
finding** — removed from executive output, listed in the integrity appendix. The quote hash is authoritative: line
drift and paraphrase both fail, and a quote absent at that commit was invented.

**2. Pass B — BLIND RE-DERIVATION over a stratified, seeded sample.** 100% of CRITICAL and HIGH; policy sample of the
rest (default 20% of MEDIUM, 10% of LOW/INFO — policy, printed with its value):
```
V=findings.verified.json
jq -r '.[]|select(.quarantined!=true and (.severity.level|IN("CRITICAL","HIGH")))|.id' $V | sort > vf/sample.txt
jq -r '.[]|select(.severity.level=="MEDIUM")|.id' $V | sort > vf/med.txt
shuf --random-source=<(yes "<run_id>") -n $(( $(wc -l < vf/med.txt) / 5 )) vf/med.txt >> vf/sample.txt  # seeded
```
Draw and record the sample **before** verification starts, so it cannot be adjusted once results are known. Build each
blind prompt from the **subject only** — locator, symbol, question — with title, statement, severity and reasoning
stripped, and run it in a fresh context: a verifier that sees the draft inherits the draft's errors, so its agreement
measures consistency, not correctness. Record the prompt digest. A disagreement is a different claim class, a
different severity band, or a failure to reproduce the finding at all.

**3. Pass C — PERTURBATION STABILITY, for security and logic findings.** Re-ask the blind question with identifiers
renamed (`chargeCard` → `fn_a`), irrelevant but valid code appended, and the path anonymised. The verdict must survive
all three: flips under trivial renaming are a documented weakness of model-based review, so one flip downgrades the
finding a level and marks it `perturbation_unstable`, and two flips quarantine it.

**4. Pass D — EXISTENCE CHECK on every named external artifact:** package, CVE, CWE, API and config key.
```
npm view <pkg> version ; pip index versions <pkg> ; go list -m <module>@<ver> ; rg -uu -n '<CONFIG_KEY>' config/ src/
curl -sf "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-YYYY-NNNNN" | jq '.totalResults'   # CVE must exist
```
Anything that fails to resolve is quarantined, never corrected: re-asking the same model does not catch stable
fabrications, so this must be an external lookup. Offline fallback: mark `UNKNOWN (existence unchecked)`, never assume.

**5. Emit the audit-quality metrics of CONFIDENCE-AND-COVERAGE.md §4** in the report body, not an appendix: citation
resolution rate, unknown rate, corroboration, re-verification disagreement, tool agreement, external-validation load.

**6. Apply the gate.** Re-verification disagreement above **10% invalidates the run**: mark the manifest
`INVALIDATED`, publish nothing, rerun with tighter shards. Citation resolution below 100% after one repair pass
publishes only with the integrity appendix and a stated caveat. An unknown rate of zero is a linter failure.

**7. Never repair.** Quarantine, downgrade or confirm — nothing else. Do not rewrite a statement, adjust a locator,
soften a severity into acceptability or "fix" a citation: repair reintroduces the very bias the blind pass exists to
detect and destroys the independence behind the disagreement rate. Defects go back to the owning skill to re-run.

## Outputs
`findings.verified.json` · quarantine list with reasons · disagreement log (id, original class/severity, independent
result, decision) · perturbation results · existence-check table · metrics block · manifest verification record.

## Evidence requirements
Every verifier decision cites its tool run (script, args, exit code), the blind prompt digest, the sample seed and the
`path#Lstart-Lend` + commit SHA it re-resolved. Sample and seed reach the manifest before Pass B begins.

## Fact vs inference rules
`FACT`: citation-resolution results, existence-check results, metric values, perturbation outcomes. `INFERENCE`: the
cause of a disagreement. `UNKNOWN`: a finding the blind pass neither reproduced nor refuted — kept, downgraded,
flagged. This skill emits **no new claims about the repository**, only decisions about existing ones.

## Confidence scoring rules
Verifier decisions are C3 by construction (deterministic script plus recorded runs). A confirmed finding does **not**
gain confidence from confirmation: blind re-derivation over the same evidence is not a second independence group.

## Repository coverage rules
Population = every finding from every executed skill. Pass A coverage must be 1.0 or the gate fails; Pass B and C
coverage is the sampled fraction **per severity stratum** — a global "18% verified" hides an incomplete CRITICAL set.

## Large repository strategy
The verification budget is reserved at planning (≥20%, per RDA-01) and never absorbs an overrun. Shard the sample by
owning skill so blind contexts stay small — verifying inside a context that holds the draft is not blind.

## Failure conditions
Budget exhausted before the CRITICAL/HIGH stratum completes (report `ABORTED_BUDGET`; the run is unpublishable) ·
findings file fails schema · pinned commits unresolvable · no fresh-context mechanism, which blocks Pass B entirely.

## Escalation conditions
Disagreement above 10% — invalidate and rescope · a fabricated citation in a CRITICAL or HIGH finding — escalate to the
engagement owner, since one fabrication implies a process defect · a skill that modified findings after verification.

## External validation required
Whether a quarantined finding was wrong or merely unresolvable at the pin · registry and CVE-service availability at
verification time · whether the human accountable for acceptance reviewed the integrity appendix.

## Known limitations
Two ways this skill produces a wrong answer, and the controls that stop them. **(a) Prompt leakage.** If the blind
prompt carries the conclusion — a title like "Unauthenticated refund endpoint" is a conclusion — Pass B is theatre;
prevented by subject-only construction with statements stripped and the digest recorded. **(b) Shared-prior
agreement.** The same model over the same shard summary agrees with itself; prevented by independence-group
separation, a different retrieval path and BSR-08's summary-depth cap. Neither proves correctness; both bound error.

## Success criteria
Pass A exhaustive with its resolution rate published · sample seed and prompt digests in the manifest · zero repaired
findings · the gate applied · every quarantined finding absent from executive output and in the integrity appendix.

## Example prompts
- Claude Code / Cursor: "Run rda-32-evidence-verifier on findings.json — verify citations, blind-re-derive all HIGH/CRITICAL in fresh contexts, and report the disagreement rate."
- Codex: "$rda-32-evidence-verifier — run scripts/verify_citations.py, draw the seeded sample, perturbation-test security findings, emit the audit-quality metrics block."
- Antigravity / Gemini CLI: "/rda-verify findings=findings.json repo=. seed=<run_id> sample=critical:100,high:100,medium:20"
