---
name: rda-17-compliance-control-mapping
description: Maps cited findings to SOC 2, ISO 27001, PCI DSS, HIPAA, SSDF, ASVS and EU CRA controls as evidence present, partial or absent; use for compliance readiness or a customer security questionnaire.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-17"
  layer: "2-risk"
  risk_class: "HIGH_HARM"
  tier: "conditional"
  depends_on: "RDA-11, RDA-16, RDA-19"
---

# RDA-17 · Compliance Control Mapping

Inherits RDA-00. **Absolute rule: this skill emits control evidence, never a compliance verdict.**

## Purpose
Map the audit's cited findings onto the control frameworks in scope and emit, per control, whether repository
evidence is present, partial, absent, or not assessable from source — with a citation on every row.

## Business value
Two expensive artifacts are produced from memory in most organisations: the readiness assessment before an audit
and the security questionnaire during a sale. Both ask "show me where this control lives", and both are answered
faster and more defensibly from an evidence index built out of cited findings than from a workshop.

## When to use
When a certification, attestation, customer questionnaire or contractual security schedule is in scope and the
source skills have produced findings to map.

## When NOT to use
To answer whether the organisation is compliant, certified or audit-ready, or before the source skills run.

## Inputs
`findings.json` from RDA-11, RDA-13, RDA-14, RDA-16 and RDA-19 (post-RDA-32 where available) · `coverage.json`
per skill · the frameworks and editions named at scope time · the published control text for each.

## Procedure

**1. Load the verified finding set (deterministic).** Every row of this map starts from findings, never from
recollection of the audit: `jq -r '.[] | select(.quarantined != true) |
[.id,.skill_id,.severity.level,(.standard_refs//[]|join(";")),(.evidence[0].locator//"")] | @tsv'
rda-out/findings.json | sort` and `jq '[.[] | select(.severity.level=="HIGH" or .severity.level=="CRITICAL")] |
length' rda-out/findings.json` for the reverse-map denominator. **Degraded fallback:** with no findings file
this skill does not run; a map assembled from memory is fabrication with a table around it.

**2. Select frameworks and pin editions.** Never map to all frameworks by default; map only what the engagement
names. Record the edition of each, because control ids move between editions:
- SOC 2 Trust Services Criteria (the common criteria series, notably logical access, system operations and change management)
- ISO/IEC 27001:2022 Annex A **8.25-8.34** — secure development lifecycle, application security requirements, secure architecture, secure coding, security testing, outsourced development, environment separation, change management, test information, and protection during audit testing
- PCI DSS 4.x **Requirement 6** — develop and maintain secure systems and software
- HIPAA Security Rule 45 CFR **§164.308** administrative and **§164.312** technical safeguards
- NIST SSDF SP 800-218 practice groups **PO · PS · PW · RV**
- OWASP ASVS 5.0 verification requirements, by chapter id as printed in the published standard
- EU CRA Annex I Part II vulnerability-handling duties and the Article 14 reporting duties, with deadlines quoted from the regulation text rather than from memory

**3. Existence-check every control identifier.** Each id is resolved against the published text of the pinned
edition and quoted in its own words before it appears in any row. Control ids are the most fabricable artifact
in this skill: a plausible identifier with a plausible title is indistinguishable from a real one at reading
speed, and a table of them survives review because it looks clerical.

**4. Build the mapping table.** One row per (framework, control id, RDA finding ids, evidence locator, state).
State is exactly one of `EVIDENCE_PRESENT` · `EVIDENCE_PARTIAL` · `EVIDENCE_ABSENT` ·
`NOT_ASSESSABLE_FROM_SOURCE`. Every row carries the finding id and its `path#Lstart-Lend` plus commit SHA. A row
with no finding behind it is not a row.

**5. Mark the source boundary honestly.** Most controls in these frameworks are organisational — training,
vendor management, screening, incident drills, evidence retention — and are `NOT_ASSESSABLE_FROM_SOURCE` by
construction. Marking them `EVIDENCE_ABSENT` manufactures a deficiency the repository could never evidence.

**6. Reverse-map, then disconfirm.** Every HIGH/CRITICAL finding lands on at least one control row or is listed
as unmapped — an unmapped finding is a gap in the map, not evidence that no control applies. Before any
`EVIDENCE_ABSENT` row ships, search once for the control implemented elsewhere in scope: another repository, a
shared IaC module, a platform setting, a policy document, or a compensating control named in another finding. An
absent state with no disconfirming search is downgraded to `NOT_ASSESSABLE_FROM_SOURCE`.

**7. Emit evidence, not judgement.** The deliverable is an evidence index for an auditor, counsel or customer to
evaluate. Forbidden without exception: "compliant", "certified", "passes", "meets the requirement", a readiness
percentage, a control score, a maturity level, or any statement about audit outcome. ES-1 §2 places compliance
in the never-emitted class, and this skill is where the temptation is strongest.

## Outputs
`control-map.csv` (framework, edition, control id, control quote, finding ids, locator, state, disconfirming
search) · `evidence-index.md` by framework · `unmapped-findings.csv` · `not-assessable.csv` naming the
organisational controls source review cannot reach, so nobody reads their absence as a gap.

## Evidence requirements
Every row cites at least one finding id and through it `path#Lstart-Lend` plus commit SHA. Every control id
carries a verbatim quote of its text and its edition. Tool-sourced rows carry tool name, version and exit code.

## Fact vs inference rules
`FACT`: this control text says X; finding F cites this artifact. `INFERENCE`: this artifact evidences that
control — the rationale is written out, because a mapping is an argument, not a lookup. `HYPOTHESIS`: that an
assessor will accept the mapping. `UNKNOWN`/`NOT_ASSESSABLE_FROM_SOURCE`: evidence living outside the
repository. **Never emitted at any class:** compliance status, certification status, audit outcome, or a legal
conclusion.

## Confidence scoring rules
Rows inherit the confidence of the finding beneath them and never exceed it; a control mapped from a C1 finding
is a C1 row and may not appear in an executive summary. HIGH/CRITICAL rows require **C3** on the underlying
finding. The mapping itself caps at C2, because interpretation is an argument an assessor may reject.

## Repository coverage rules
Population is the count of control ids enumerated from the pinned editions, recorded with their source. Coverage
= controls with an assigned state / that count, per framework and split by state so `NOT_ASSESSABLE_FROM_SOURCE`
stays visible. Second denominator: HIGH/CRITICAL findings mapped / produced.

## Large repository strategy
The map scales with controls, not code, so it stays exhaustive over the selected frameworks at any size. For
multi-repo scope, map per repository and roll up in RDA-37 — one repository's evidence is not the fleet's.

## Failure conditions
Source skills incomplete or unverified · framework text unavailable, so ids cannot be existence-checked · a
framework with no software-development controls · evidence held only in a GRC system.

## Escalation conditions
A control asserted in a customer contract, questionnaire or data-room document but absent in code — a fidelity
issue for RDA-31 and the accountable executive · regulated data with no evidenced control on its path, to RDA-16
· any request to convert this map into a compliance statement, refused.

## External validation required
Everything organisational: policies, training, vendor management, screening, and controls implemented in a
platform or contract.

## Known limitations
Two ways this skill produces a wrong answer. **(a) The fabricated control id** — a plausible identifier, or a
real one from the wrong edition, mapped to a finding; prevented by step 2's existence check, with a quote and a
pinned edition on every row. **(b) The readiness percentage** — counting rows into "82% SOC 2 ready",
meaningless where most controls are not assessable from source and dangerous because it will be quoted;
prevented by the step 7 prohibition and the `NOT_ASSESSABLE_FROM_SOURCE` state. Mapping is interpretive: an
assessor may map the same evidence differently, so rationale is required and mapping caps at C2.

## Success criteria
Every row cites a finding and a control quote · zero verdict language · `NOT_ASSESSABLE_FROM_SOURCE` rows as
prominent as absent ones · every ABSENT row carries a disconfirming search.

## Example prompts
- Claude Code / Cursor: "Run rda-17-compliance-control-mapping for SOC 2 and ISO 27001:2022 A.8.25-8.34 over the verified findings; evidence states only, no verdicts."
- Codex: "$rda-17-compliance-control-mapping — map RDA-11 and RDA-16 findings to PCI DSS 4.x Requirement 6 and mark what source review cannot assess."
- Antigravity / Gemini CLI: "/rda-control-map frameworks=ssdf,asvs,cra findings=findings.json output=control-map.csv"
