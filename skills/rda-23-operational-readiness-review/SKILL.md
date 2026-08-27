---
name: rda-23-operational-readiness-review
description: Produces a pass/conditional/fail production-readiness gate with numbered conditions over runbooks, on-call, capacity, backup and restore and DR — use before a launch or go-live decision.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-23"
  layer: "3-operations"
  risk_class: "MEDIUM_HARM"
  tier: "conditional"
  depends_on: "RDA-21, RDA-22, RDA-19"
---

# RDA-23 · Operational Readiness Review

Inherits RDA-00. This skill emits a **gate**, not an essay: `PASS` / `CONDITIONAL` / `FAIL`, plus numbered
conditions, each with an owner role and a system of record. **A backup nobody has restored is not a backup.**

## Purpose
Decide whether this system is ready to be operated by people who did not write it, using only evidence present at the
pinned commit, and state precisely what is missing.

## Business value
The production-readiness review is the cheapest place to catch what is expensive in production: no undo, no restore,
no owner. Google's SRE material for it is Chapter 32 plus Appendices B and E — a practice model, not a standard — so
RDA emits a gate with conditions rather than a score, which a launch decision can act on and re-check.

## When to use
Before go-live, before a acquisition close that transfers operational responsibility, or when RDA-19/21/22 have
completed and a launch decision is pending.

## When NOT to use
As a substitute for the underlying reviews: without RDA-19, RDA-21 and RDA-22 outputs this degrades to a
document-existence checklist, which is the failure mode readiness reviews are famous for.

## Inputs
RDA-19 release, gate and rollback findings · RDA-21 telemetry and alerting coverage · RDA-22 SPOFs and controls ·
RDA-20 declared topology · repository documentation tree · scope-time business context for the impact scale.

## Procedure

**1. Artifact sweep (deterministic, 100%).** Locate, per dimension:
`rg -uuu -li 'runbook|playbook|on-?call|escalation|disaster recovery|RTO|RPO|capacity|restore'` across
`docs/`, `.github/`, and platform directories; on-call and escalation policy as code (PagerDuty/Opsgenie
providers); capacity signals (HPA min/max, resource requests and limits, quotas, autoscaling policy); load test
assets **and** their result artifacts (k6, Locust, Gatling, JMeter); backup configuration (snapshot schedules,
`backup_retention_period`, Velero, dump CronJobs, PITR settings).

**2. Freshness and substance check.** For every artifact found, record `git log -1 --format='%H %ad' -- <path>`
and scan for unfilled scaffolding (`TODO`, `TBD`, `<insert`, `FIXME`, untouched template headings). A runbook
last modified before the service's current architecture is evidence of a document, not of readiness, and is
recorded `DOCUMENTED_ONLY` with its age.

**3. Restore evidence (the hard gate).** A backup schedule is a `FACT` about configuration and nothing more.
Restore is only evidenced by: a restore job or script exercised in CI with a run record, a documented drill
carrying a date and outcome, or a restore runbook with a recorded last-executed date. Absent all three, restore
capability is `UNKNOWN`, the gate cannot be `PASS`, and the condition names the backup system of record.

**4. Dimension scoring.** Score each of runbooks · on-call · capacity · backup · restore · DR (RTO/RPO stated
and a failover path) · graceful degradation (kill switches, fallbacks, read-only mode, cached-stale serving) ·
launch criteria · rollback criteria (from RDA-19) · alerting on critical paths (from RDA-21) · SPOF acceptance
(from RDA-22), as `PRESENT_AS_CODE` / `DOCUMENTED_ONLY` / `ABSENT_FROM_SCOPE` / `UNKNOWN`. Each score cites.

**5. Apply the gate rule (policy, declared as policy).** There is no machine-checkable production-readiness
standard, so this rule is a stated policy, not a conformance test. `FAIL` if any of: no rollback path, no restore
evidence, no alerting on a critical path, no named owning role. `CONDITIONAL` if every FAIL trigger is clear but
any dimension is `DOCUMENTED_ONLY` or `UNKNOWN`. `PASS` only when every dimension is `PRESENT_AS_CODE` and
corroborated. These thresholds are configurable at scope time and are stated in the output, never implied.

**6. Emit conditions, not adjectives.** Each condition is numbered and carries: what is missing, the evidence
that would satisfy it, the owner role, the system of record, and which part of the decision it blocks. The
condition list *is* the deliverable; the verdict is a one-line summary of it.

**7. Disconfirming pass.** Before scoring any dimension `ABSENT_FROM_SCOPE`, search outside the repository:
platform or SRE repos, Backstage catalogue entries, org-level `.github`, wiki links referenced from the README,
and the incident tooling naming convention. Absence is reported as absence *from scope*, never as non-existence.

## Outputs
`readiness-gate.md` (verdict, dimension table, numbered conditions) · `readiness-dimensions.json` (score, class,
citation, freshness per dimension) · `conditions.csv` (condition, evidence required, owner role, system of record) ·
findings and one coverage record.

## Evidence requirements
Every dimension score cites a path with line range and commit SHA, a tool or API output, or an explicit `UNKNOWN` with
a named system of record. The verdict cites the dimension rows that produced it. No dimension may be scored from a
document title alone — the content must be read.

## Fact vs inference rules
FACT: the existence, content and last-modified date of an artifact. INFERENCE: "restore is unproven" = backup
configuration present **and** no restore artifact from step 3. HYPOTHESIS: that a documented procedure works.
EXTERNAL: whether on-call exists and is staffed (paging platform), whether drills happened (DR test records), capacity
headroom (APM and cloud quotas), incident history and MTTR (incident tracker). A readiness verdict is a statement
about *evidence*, never about the operational competence of a team.

## Confidence scoring rules
`PRESENT_AS_CODE` with a cited artifact plus a corroborating run record = C3. `DOCUMENTED_ONLY` = C2 maximum, because
a document is one independence group. A `PASS` verdict requires every dimension at C2 or better and at least one C3
per FAIL-triggering dimension; otherwise the verdict is `CONDITIONAL`, however complete the documentation looks.

## Repository coverage rules
Population: the dimension list in step 4 (11 dimensions) times the deployable units in scope, denominator
`jq '.structural.build_manifests' census.json` multiplied by 11. Coverage is scored dimensions over that product,
and the gate is emitted per unit as well as for the scope — a readiness verdict averaged across services conceals
the one service that fails.

## Large repository strategy
Score per deployable unit; shared platform dimensions (on-call, DR, backup of a shared datastore) are scored once and
referenced by each unit that inherits them, with the inheritance recorded. Budget guard: run the gate for units RDA-19
shows deploying to production first; mark the rest `BUDGET_EXHAUSTED` rather than issuing a verdict.

## Failure conditions
RDA-19/21/22 not run (the gate is suppressed, not guessed) · operational docs held in a wiki outside scope · no
business context for impact severity · a scope excluding the platform repo where readiness evidence lives.

## Escalation conditions
No restore evidence for a datastore holding regulated or financial data · no rollback path for a customer-facing
service already in production · backup configuration writing to the same failure domain as the source · on-call
escalation pointing at an individual rather than a rotation.

## External validation required
On-call rotation existence and staffing (paging platform) · last successful restore, with date and duration (backup
system of record) · last DR exercise and its outcome (DR test records) · capacity headroom against current load (APM,
cloud quotas) · incident history and MTTR (incident tracker) · who owns the go/no-go decision.

## Known limitations
Two ways this skill produces a wrong answer. **(a) The false FAIL** — scoring `ABSENT` when runbooks, on-call and DR
live in Confluence, Backstage or a platform repository; step 7 mandates the out-of-scope sweep and the
`ABSENT_FROM_SCOPE` label keeps the claim honest. **(b) The false PASS** — a complete-looking runbook set that is
stale or templated; step 2 requires last-modified dates and a scaffolding scan, and step 3 refuses to convert a backup
schedule into restore capability. This skill measures readiness evidence, not readiness.

## Success criteria
The verdict is one of three values with every condition numbered and owned · no dimension scored without a citation or
an explicit UNKNOWN · restore is never inferred from backup · policy thresholds are printed with the verdict ·
re-running at the pin reproduces the dimension table.

## Example prompts
- Claude Code / Cursor: "Run rda-23-operational-readiness-review and give me the gate verdict with numbered conditions; be explicit about restore evidence."
- Codex: "$rda-23-operational-readiness-review — score readiness per service using the RDA-19/21/22 outputs and emit conditions.csv."
- Antigravity / Gemini CLI: "/rda-readiness units=services/* policy=default output=readiness-gate.md"
