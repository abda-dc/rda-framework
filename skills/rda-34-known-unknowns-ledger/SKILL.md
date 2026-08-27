---
name: rda-34-known-unknowns-ledger
description: Builds the uncertainty balance sheet - not examined, not knowable from source, contradictions, decision-blocking gaps - plus the interview agenda by role, before any executive brief is written.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-34"
  layer: "5-synthesis"
  risk_class: "MEDIUM_HARM"
  tier: "core"
  depends_on: "all"
---

# RDA-34 · Known-Unknowns Ledger

Inherits RDA-00. This is the section most audits omit, which is exactly why it is the section a hostile reader turns to
first: an audit that cannot state its own ignorance has not measured anything.

## Purpose
Produce the uncertainty balance sheet — four registers plus the interview agenda — so that a decision-maker knows the shape
of what the audit did not establish, not just what it did.

## Business value
Undisclosed gaps are priced as zero risk by whoever reads the report. Naming them converts invisible exposure into a short,
answerable list of questions, and it converts "we reviewed the codebase" into a claim with edges.

## When to use
Every run, after all analysis skills have emitted coverage records, before RDA-36. Re-run whenever a skill is added,
aborted, or downgraded mid-engagement.

## When NOT to use
Never skipped. If coverage records are missing, the ledger reports that as its first entry rather than being omitted — a
missing coverage record is itself a known unknown.

## Inputs
Every skill's `coverage.json` · `census.json` denominators · all UNKNOWN, EXTERNAL_VALIDATION_REQUIRED and unresolved
HYPOTHESIS findings · the manifest's `skills_executed` statuses and tool-degradation list · the RDA-01 decision statement
and the list of pending decisions it feeds.

## Procedure
**1. Deterministic reconciliation.** Per skill, subtract `inspected.count` from the census population count by key: that
arithmetic, not a narrative, produces register (a). Band artifact and risk-surface coverage separately per CC-1 §3. Manifest
status `PARTIAL`, `SKIPPED`, `FAILED` or `ABORTED_BUDGET` earns an automatic entry — the silent skip is the failure this
step exists to catch.

**2. Harvest the declared classes.** Collect every UNKNOWN and EXTERNAL_VALIDATION_REQUIRED finding, plus every HYPOTHESIS
whose settling check was never run. Sort by finding id so the ledger is stable across runs.

**3. Register (a) — NOT EXAMINED.** In scope, not inspected. Each row: area, inspected of population with the band, the
reason code (`OUT_OF_SCOPE`, `TOOL_UNAVAILABLE`, `BINARY_OR_GENERATED`, `BUDGET_EXHAUSTED`, `ACCESS_DENIED`, `UNPARSEABLE`,
`REQUIRES_RUNTIME`), and the conclusion it blocks. The reason is a code, never prose: prose is where excuses hide.

**4. Register (b) — NOT KNOWABLE FROM SOURCE.** The undecidable register instantiated here: deployment status, traffic and
scale, real cost, exploitability, dead code, storage region, incident history, compliance status. Each row carries the
**system of record** (APM, billing export, cloud console, incident system, contract repository, CODEOWNERS plus org
confirmation), the exact question, the owning role and the class ceiling. These do not become knowable by thinking harder
about the source.

**5. Register (c) — CONTRADICTORY EVIDENCE.** Group findings sharing a locator or root-cause key whose statements cannot
both be true, and add the doc-versus-code conflicts from RDA-31. Record **both sides with citations**, what would resolve
them, and state plainly that this audit did not. Silently picking a winner is the defect this register exists to prevent.

**6. Register (d) — DECISION-BLOCKING.** Map each gap to the specific pending decision it blocks: price, go/no-go, launch
date, headcount, remediation sequencing. A gap that blocks nothing is tagged `TRIVIA` and moved to an appendix. An unknown
that blocks no decision is not risk information, it is padding.

**7. Interview agenda.** Render registers (b) and (d) as questions grouped by the role to ask: engineering leadership,
security lead, SRE/on-call, data protection officer, platform owner, finance, legal, product. One answerable question per
line, each with the artifact that would settle it and the decision it unblocks; deduplicate questions that differ only in
wording.

**8. Zero-unknowns check.** If registers (a) to (c) are empty, flag the run **SUSPECT** and emit that as a finding: models
essentially never abstain unprompted, so an absence of unknowns means uncertainty was resolved by assertion. Check the
unknown rate against the CC-1 band of 0.05-0.30 — zero is false completeness, above 0.5 is insufficient access, which stops
the run for rescoping rather than publication.

## Outputs
`unknowns-ledger.md` with the four registers · `interview-agenda.md` grouped by role, with blocked decision per question ·
`blind-spots.csv` (area, reason code, population, inspected, band, blocked conclusion) · the unknown-rate and
external-validation-load metrics · the SUSPECT flag and its basis when triggered.

## Evidence requirements
Register (a) rows cite a census denominator key and a coverage record. Register (b) rows name a system of record and carry a
question a human can answer. Register (c) rows cite both sides with locators and commit pins. A ledger row with no reference
is an opinion about ignorance and is deleted.

## Fact vs inference rules
Coverage arithmetic is FACT. "This gap blocks decision X" is INFERENCE from the decision statement plus the gap and must
show that derivation. **"Nothing else is unknown" is never emissible**: this ledger is a lower bound on ignorance, since
unknown unknowns are out of reach by construction, and it says so in its own header.

## Confidence scoring rules
Ledger rows are UNKNOWN or EXTERNAL_VALIDATION_REQUIRED by construction and carry no C-level — confidence attaches to
positive claims, and awarding it to an absence is a category error. Register (c) rows keep both sides' levels unchanged; a
contradiction never averages into a middle position.

## Repository coverage rules
Population is the union of every executed skill's declared population; the ledger's own coverage is the share of executed
skills that emitted a conformant coverage record, and a skill with none becomes a register (a) entry about itself. Artifact
and risk-surface coverage are both printed, risk-surface first.

## Large repository strategy
Build per shard and merge, never re-derive from summaries. Per-shard blind spots must survive the reduce step: a shard that
hit `ABORTED_BUDGET` appears in the ledger even when none of its findings were promoted, because the budget failure is
itself the finding.

## Failure conditions
Coverage records missing or unparseable · census keys that do not resolve · manifest without `skills_executed` statuses · no
RDA-01 decision statement, in which case register (d) cannot be built and the ledger says so rather than inventing the
decisions the organisation might be making.

## Escalation conditions
`ACCESS_DENIED` blind spots on the risk surface · risk-surface coverage below 20% while a decision is pending, reported as
insufficient basis rather than a judgement · unknown rate above 0.5, which stops the run for rescoping · a register (c)
contradiction touching money movement, authentication or regulated data.

## External validation required
The whole of register (b), by definition. Additionally: which pending decisions actually exist and their dates, and which
roles are empowered to answer each question — the agenda is worthless if addressed to nobody.

## Known limitations
Two ways this skill produces a wrong answer. **The empty ledger**: nothing prompts abstention, so the run reports no
unknowns and reads as thorough when it is merely confident — prevented by step 8, which treats zero unknowns as a defect
signal rather than an achievement. **The comfortable unknown**: the ledger fills with harmless unknowables (log formats,
naming conventions) while the deployment-status question that gates the price goes unasked — prevented by step 6's
blocked-decision mapping and the `TRIVIA` demotion. Beyond those: unknown unknowns are not enumerable, and the ledger bounds
only what the executed skills declared.

## Success criteria
Every executed skill resolves to at least one coverage record or a register (a) entry · every undecidable claim in the
report has a matching register (b) row · every interview question carries a role and a blocked decision · RDA-36's "what we
could not determine" section is generated from this file rather than written separately.

## Example prompts
- Claude Code / Cursor: "Run rda-34-known-unknowns-ledger: reconcile coverage against the census, build the four registers, and write the interview agenda grouped by role."
- Codex: "$rda-34-known-unknowns-ledger — list what was not examined with coverage numbers, what is unknowable from source, and which decisions each gap blocks."
- Antigravity / Gemini CLI: "/rda-unknowns coverage=coverage.json census=census.json output=unknowns-ledger.md agenda=interview-agenda.md"
