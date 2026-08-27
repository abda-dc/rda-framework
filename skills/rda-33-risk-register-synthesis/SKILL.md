---
name: rda-33-risk-register-synthesis
description: Deduplicates verified findings into one mechanically scored risk register with severity/confidence pairs, emitting risk-register.csv, findings.json and SARIF, once RDA-32 verification has passed.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-33"
  layer: "5-synthesis"
  risk_class: "MEDIUM_HARM"
  tier: "core"
  depends_on: "RDA-32"
---

# RDA-33 · Risk Register Synthesis

Inherits RDA-00. This skill invents nothing: it is a set operation over the verified finding set, and any row that does not
already exist upstream is a defect, not a synthesis.

## Purpose
Collapse the verified finding set into one ordered register — deduplicated by root cause, scored by mechanical application
of the RS-1 matrix, ordered so that the first row is the one to act on first.

## Business value
The register is the artifact everyone argues over, so it must survive hostile reading. Its two jobs are to stop one root
cause being counted three times because three skills found it, and to stop a certain triviality outranking an uncertain
catastrophe. Either failure discredits the document the moment its subject reads it.

## When to use
After RDA-32 completes and its verification statistics are in the manifest; before RDA-35, RDA-36 or RDA-37. Mandatory for
any audit whose output leaves the engineering team.

## When NOT to use
Before RDA-32 — a register built on unverified findings launders quarantined claims into the executive layer. Not a
substitute for an owning skill's analysis, and not worth running to answer a single targeted question.

## Inputs
`findings.json` from every executed skill with quarantine flags already set · `coverage.json` per skill · `census.json`
denominators · the manifest verification block · the decision statement and business context from RDA-01, because impact is
defined against the decision and against nothing else.

## Procedure
**1. Schema validation.** Validate the union against `schemas/finding.schema.json`. A row missing `evidence`,
`coverage_ref`, `how_to_refute` or `disconfirming_check` is returned to its owning skill. Never repair here: repairing a
finding inside the register is authoring a finding without evidence.

**2. Verification gate.** Drop every `quarantined: true` row — quarantine is removal, not a warning. Read the manifest: if
citation resolution is below 1.00 after one repair pass, or re-verification disagreement exceeds 0.10, stop and report an
invalid basis instead of a register (ESC-1).

**3. Deduplicate by evidence locator, then by root cause.** Group key one: normalised path plus overlapping line span plus
quote hash. Group key two: the shared artifact or absent control named in the statements. One missing auth middleware found
by RDA-03, RDA-11 and RDA-12 is **one risk with three evidence trails**, carrying all three `skill_id`s and a `merged_from`
list. Grouping across differing locators with no cited shared artifact is HYPOTHESIS-level and is labelled so. Log every
dropped duplicate so the merge is auditable.

**4. Re-score mechanically.** Apply the RS-1 impact x likelihood table as a lookup, not a judgement, so two runs agree.
Impact is judged against the RDA-01 decision. Likelihood with no cited basis is capped at POSSIBLE. Where an owning skill's
`severity.level` disagrees with the lookup, the lookup wins and the divergence is recorded.

**5. Merge confidence by rule, never by feel.** Confidence rises on merge only where merged evidence sits in genuinely
different `independence_group`s and at least one disconfirming check is recorded. Two skills restating one read of one file
is one source. Confidence never rises because a finding was repeated.

**6. SSVC for security rows.** Emit `TRACK` / `TRACK_STAR` / `ATTEND` / `ACT` from exploitation status, exposure, technical
impact and mission impact. CVSS and EPSS ride as attributes, never as the ranking key. No exposure determination means
`TRACK`. Keep `present` / `reachable` / `exploitable` as three separate counts.

**7. Apply floors and triage.** HIGH or CRITICAL at C1 leaves the register body and becomes a **verification task** carrying
the exact check that would settle it. HIGH/CRITICAL security, supply-chain and data-governance rows require C3.
Undecidable-register claims cap at C2 and must carry `external_validation.question`.

**8. Order deterministically.** Sort by `(severity, ssvc, confidence)`; break ties by larger blast radius, then by cheaper
remediation band, then by finding id so the order is total and reproducible. A `blast_radius` citing no dependency evidence
may not be used as a tiebreak.

**9. Emit, then disconfirm.** Write the artifacts, then re-check the top rows: no upstream finding contradicts them, and no
dropped duplicate carried contradicting evidence that the merge silently discarded.

## Outputs
`risk-register.csv` (risk id, title, severity, confidence, impact, likelihood, ssvc, blast radius, contributing skill ids,
evidence locators, coverage ref, how to refute, effort band, sequencing) · merged `findings.json` with `merged_from` ·
`register.sarif` for security rows so they land in existing code-scanning dashboards · the severity x confidence
distribution matrix · the verification-task list · the dropped-duplicate log.

## Evidence requirements
The register adds no evidence and no claims. Every row inherits locators, commits and quotes from its source findings; a row
resolving to no upstream finding id is deleted, not footnoted.

## Fact vs inference rules
Locator-identity dedupe is FACT. Root-cause grouping across differing locators is INFERENCE only with a cited shared
artifact, otherwise HYPOTHESIS. Severity is INFERENCE from the matrix lookup plus a cited impact basis. Themes and
categories are a presentation layer over cited rows and are never themselves rows.

## Confidence scoring rules
Report severity and confidence as an orthogonal pair (`HIGH / C2`) and **never multiply them**. Never average confidence
across rows — publish the distribution. **No single composite repository score** is emissible unless the weighting and the
coverage bands feeding it are published in the same artifact.

## Repository coverage rules
Population is the verified finding set; the denominator is total emitted findings minus quarantined ones, and both numbers
are printed. Each row carries the coverage band of its contributing skills, and no cross-cutting claim may assert coverage
above its weakest contributing skill.

## Large repository strategy
One register per repository or deployable unit; fleet ranking belongs to RDA-37. Cross-shard dedupe runs on locator and
root-cause keys in sorted order, so the result is independent of shard concatenation order.

## Failure conditions
RDA-32 absent or invalidated · citation resolution below 1.00 · disagreement above 0.10 · findings without `coverage_ref` ·
missing census denominators · more than half the rows at C1, in which case the artifact ships as a lead list labelled as
one, never as a register.

## Escalation conditions
Any CRITICAL at C3+ triggers an ESC-1 notice before the register circulates. Live secrets, evidence of compromise and
regulated-data exposure bypass the register entirely. If every top row comes from one skill at INDICATIVE coverage, escalate
insufficient basis rather than publish a ranking.

## External validation required
Business impact calibration for the impact scale · which affected components are actually in production · whether
compensating controls exist outside the repository (gateway, WAF, network policy, contractual terms).

## Known limitations
Two ways this skill produces a wrong answer. **The triple count**: three skills report one root cause, the register reads
three times worse than reality, and the first engineer to spot it discredits the whole document — prevented by step 3's
locator dedupe and the auditable dropped-duplicate log. **The confident triviality at the top**: collapsing severity and
confidence into one score floats a certain LOW above an uncertain CRITICAL — prevented by steps 4, 7 and 8, which keep the
pair orthogonal and route HIGH+C1 to verification tasks rather than bury it. Beyond those, ordering is deterministic, not
wise: organisational appetite is out of scope.

## Success criteria
Two runs over the same verified set produce identical rows in identical order · zero quarantined rows present · every row
resolves to at least one upstream finding id · the SARIF file loads in a code-scanning dashboard · no composite score
appears without its published weighting and coverage bands.

## Example prompts
- Claude Code / Cursor: "Run rda-33-risk-register-synthesis over the verified findings; dedupe by root cause and write risk-register.csv plus the SARIF export."
- Codex: "$rda-33-risk-register-synthesis — merge verified findings, apply the RS-1 matrix mechanically, emit the severity x confidence distribution."
- Antigravity / Gemini CLI: "/rda-risk-register input=findings.verified.json output=risk-register.csv sarif=register.sarif"
