---
name: rda-31-fidelity-claims-verification
description: Adjudicates documentation, data-room and vendor claims against cited code as SUPPORTED, PARTIALLY_SUPPORTED, CONTRADICTED or UNVERIFIABLE_FROM_SOURCE; run before any report leaves engineering.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-31"
  layer: "5-synthesis"
  risk_class: "HIGH_HARM"
  tier: "conditional"
  depends_on: "RDA-03..RDA-30"
---

# RDA-31 · Fidelity & Claims Verification

Inherits RDA-00. This skill decides what the repository can and cannot substantiate about itself, in both directions, and a wrong verdict here travels straight into a negotiation.

## Purpose
Turn the documentation and vendor surface into a testable claim register, adjudicate each claim against cited code at
the pinned commit, and report the reverse direction: capabilities present in code but absent from the documentation.

## Business value
This is the skill that catches "99.99% uptime and full test coverage" when the repository evidences neither. In
diligence the gap between what is claimed and what is evidenced is frequently the deal issue itself.

## When to use
Conditional, and mandatory whenever audit output leaves the engineering org: M&A and vendor diligence, security
questionnaire validation, board and investor packs, or when a README is being used as the architecture source of truth.

## When NOT to use
To issue a compliance verdict — RDA-17 owns control-evidence mapping and certification status is never emitted · to
test claims about traffic, uptime, cost or headcount, which are undecidable from source · to judge roadmap or
aspirational statements, which are not assertions about current state.

## Inputs
README, `docs/`, ADRs · data-room material and vendor questionnaires supplied with dates and versions · marketing
capability statements · all L1-L4 findings and their evidence · census denominators · pinned commit SHAs.

## Procedure

**1. Extract claims into a register (deterministic first pass).**
```
rg -uu -n -i '(we|the platform|the service|our) [a-z ]*(support|provide|ensure|guarantee|encrypt|comply|scale)' \
   README.md CONTRIBUTING.md docs/ *.md
rg -uu -n -i '\b(99\.[0-9]+%|100%|fully|always|never|zero.downtime|real.time|end.to.end|automatically)\b' README.md docs/
```
Each claim gets an id, verbatim quote, locator + SHA (or document, version and date for supplied material), subject
area and **modality**: present-tense assertion, roadmap or conditional. Only present-tense assertions enter the test
set; the rest are excluded with their reason recorded. `-uu` keeps ignored and hidden docs in the population, so the
denominator does not depend on the auditor's ignore files. Degraded fallback for PDFs and other non-greppable
material: manual extraction, recorded as method `manual` in the coverage record.

**2. Route each claim to the skill that owns its evidence.** Auth to RDA-11, coverage to RDA-18, deploy and rollback
to RDA-19, encryption and residency to RDA-16/RDA-20, dependencies and licences to RDA-13/RDA-15, topology to RDA-04.
Cite those findings by id; re-deriving evidence here duplicates work and breaks the independence chain.

**3. Adjudicate with a fixed verdict set — one verdict per claim, each with citations.**

| Verdict | Award rule |
|---|---|
| SUPPORTED | cited code or config at the pinned commit implements the claim; ≥2 independent evidence items |
| PARTIALLY_SUPPORTED | implemented for a stated subset of the population, with the denominator printed |
| CONTRADICTED | a cited artifact cannot be true simultaneously with the claim; **both sides quoted verbatim** |
| UNVERIFIABLE_FROM_SOURCE | in the ES-1 undecidable register, or the deciding evidence is outside scope |

CONTRADICTED requires an artifact-level conflict, never merely absent evidence. "Nothing found" is
UNVERIFIABLE_FROM_SOURCE with a coverage record — the distinction separates a defensible finding from an accusation.

**4. Reverse pass — undocumented capability.** Enumerate significant behaviour present in code and absent from the
documentation: admin or break-glass endpoints, telemetry and data egress, third-party SDKs and processors, flags
gating unreleased behaviour, jobs that move or delete data, secondary datastores. Same evidence bar, same citations.
In a data room this direction is what surfaces undisclosed data flows.

**5. Disconfirming pass, per claim.** Before CONTRADICTED, search for the implementation elsewhere — another repo in
scope, infrastructure, a gateway, a managed service. Before SUPPORTED, search for the bypass path. Record both.

**6. Scope check.** A claim whose implementation would live outside the audit boundary is UNVERIFIABLE_FROM_SOURCE
with the boundary named. Tests in a separate repository, auth at an API gateway and encryption in managed storage are
the three standard cases where a scope-blind reading manufactures a false contradiction.

## Outputs
`claims-register.csv` (claim id, quote, locator, modality, verdict, evidence ids, coverage ref) ·
undocumented-capability list · verdict distribution · findings. Every CONTRADICTED row quotes both sides.

## Evidence requirements
Claim quotes are verbatim with locator + SHA, or document, version, page and date for supplied material. Code
evidence carries `path#Lstart-Lend` + SHA + quote. Paraphrasing a claim is a defect equal to a wrong path: paraphrase
silently changes the claim's strength, and strength is exactly what is being adjudicated.

## Fact vs inference rules
`FACT`: the claim text and the artifact text. `INFERENCE`: the verdict, with the derivation written out.
`HYPOTHESIS`: any reading of intent behind a discrepancy — a stale README and a misrepresentation are identical in
git, and this skill never characterises motive. `EXTERNAL_VALIDATION_REQUIRED`: every uptime, scale, cost, customer
or certification claim, carried with its question and owning role.

## Confidence scoring rules
SUPPORTED requires C2 or better. CONTRADICTED requires **C3** — tool corroboration where a tool exists — plus a
recorded disconfirming search, because a false CONTRADICTED is the most damaging output this framework can produce.
UNVERIFIABLE inherits the confidence of its coverage record. RDA-32 re-derives 100% of CONTRADICTED verdicts.

## Repository coverage rules
Population = extracted present-tense claims across the declared document set. Report claims tested / claims extracted,
and name every supplied document with its date: testing a README at HEAD says nothing about a data-room PDF issued
last year, and the report must not let a reader assume otherwise.

## Large repository strategy
Shard by claim, never by file: each claim is an independent unit whose evidence is retrieved on demand. Cap the
per-claim retrieval budget; when the cap is hit the verdict is UNVERIFIABLE_FROM_SOURCE (budget), recorded as such,
never a guess dressed as a conclusion.

## Failure conditions
Documents supplied without dates or versions · claims extracted from generated docs that mirror the README (not an
independent source) · L1-L4 findings unavailable · a claim set of untestable marketing adjectives, itself the finding.

## Escalation conditions
A CONTRADICTED claim material to a transaction, a regulatory filing or a customer contract — escalate to the
engagement owner before publication · claims of certification status — route to RDA-17, never adjudicate here ·
undisclosed personal-data flows found in the reverse pass — RDA-16, and halt that traversal.

## External validation required
Whether the supplied document is current and authoritative · whether the claim was also made contractually or to a
regulator · whether an out-of-scope system implements the claim · who owns each document.

## Known limitations
Two ways this skill produces a wrong answer, and the controls that stop them. **(a) Modality confusion** turns a
roadmap sentence into a false accusation — prevented by capturing modality at extraction and testing only
present-tense assertions, with exclusions recorded. **(b) Scope-boundary blindness** turns "the tests live in another
repository" into "there are no tests" — prevented by the step-6 scope check and the hard rule that missing evidence
is UNVERIFIABLE_FROM_SOURCE, never CONTRADICTED. Beyond those: documentation drift is not deception, and no verdict
here speaks to intent.

## Success criteria
Every claim carries a verbatim quote and exactly one verdict · zero CONTRADICTED rows without both sides quoted and a
disconfirming search · no undecidable-register claim marked CONTRADICTED · the reverse pass ran and its result is
stated even when empty · 100% of CONTRADICTED verdicts survive RDA-32 re-derivation.

## Example prompts
- Claude Code / Cursor: "Run rda-31-fidelity-claims-verification against README and docs/ — verdict per claim with citations, and list capabilities in code that the docs never mention."
- Codex: "$rda-31-fidelity-claims-verification — extract present-tense claims, adjudicate against L1-L4 findings, emit claims-register.csv with both sides quoted for contradictions."
- Antigravity / Gemini CLI: "/rda-claims docs=README.md,docs/,dataroom/ scope=. reverse=true output=claims-register.csv"
