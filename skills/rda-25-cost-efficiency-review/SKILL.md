---
name: rda-25-cost-efficiency-review
description: Produces a ranked inventory of cost drivers read from code and IaC with every currency figure gated on billing evidence or a labelled estimate — run on explicit request for cost efficiency.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-25"
  layer: "3-operations"
  risk_class: "HIGH_HARM"
  tier: "optional"
  depends_on: "RDA-20, RDA-24"
---

# RDA-25 · Cost & Efficiency Review

Inherits RDA-00. **Absolute rule: no currency figure without billing evidence.** Without billing data this skill
emits drivers and a labelled estimate that shows its formula, inputs, sourced unit prices and range — or nothing.

## Purpose
Identify what in this codebase and its declared infrastructure *drives* spend, rank the drivers by structural
leverage, and specify exactly the billing data needed to turn drivers into money.

## Business value
Cost conversations fail in two ways: no analysis, or a confident number nobody can reproduce. A driver inventory with
a stated data request survives scrutiny and gives the FinOps owner a join key. The fabricated savings slide does not,
and it discredits every other finding in the report.

## When to use
On explicit request only. Requires RDA-20 (declared infrastructure) and benefits from RDA-24 (chatty calls, unbounded
results) and RDA-21 (log and metric volume).

## When NOT to use
When the ask is a savings number and no billing export will be provided — say that plainly and stop. Also not for
vendor contract or licence economics, which are commercial questions outside repository scope.

## Inputs
RDA-20 resolved IaC · RDA-24 I/O and chattiness findings · RDA-21 log volume, retention and metric cardinality ·
RDA-09 per-environment config · any billing export supplied by the engagement · vendor public price lists.

## Procedure

**1. Driver extraction from declared infrastructure (deterministic).** From the RDA-20 resolved plan, extract:
instance classes and counts, node pools and autoscaling bounds, `desired_count`, serverless memory and timeout,
GPU and licensed images, spot/on-demand posture, storage classes and volume sizes, snapshot and backup retention,
and cross-region replication. Record each with `path#Lstart-Lend` and commit SHA.

**2. Driver extraction from code and config.** Egress and topology drivers: NAT paths, absent VPC endpoints,
cross-AZ and cross-region edges from RDA-06, missing CDN in front of static assets. Call-volume drivers from
RDA-24: per-request external API calls, N+1 access to a metered service, short-interval polling, absent caching.
Telemetry drivers from RDA-21: `DEBUG` in production config, no log sampling, 100% trace sampling, unbounded
metric labels, absent retention or lifecycle policy.

**3. Always-on and idle drivers.** Non-production environments without a stop schedule, load balancers and
gateways declared per environment, provisioned concurrency, over-sized Kubernetes `requests` (which reserve
capacity whether or not they are used), and declared-but-unattached storage or addresses.

**4. Rank by structural leverage, not by money.** Score each driver on three declared properties: always-on,
scales with traffic or data volume, and carries a declared multiplier (count, replicas, retention days). The
ranking is ordinal and derived only from cited declarations — it needs no prices and makes no financial claim.

**5. Request the billing join.** Specify a FinOps FOCUS-format cost and usage export as the data shape: billed
and effective cost columns keyed by resource identifier, service name and charge period, with usage quantity and
billing currency. Name the owner role and the system of record. With that export, drivers become findings with
real amounts at C3/C4; without it they stay drivers.

**6. The estimate protocol (only when explicitly requested).** An `ESTIMATE` may be emitted only if it carries,
in the output: the formula written out; every input with its citation; the unit prices used **and their source**
(price list, region, currency, retrieval date) — never a price recalled from memory; the usage assumption and its
origin; and a sensitivity range from varying the most uncertain input. `infracost scan --json` (CLI v2 removed
`breakdown`, `diff` and `comment`) can supply the price side, but its output is a price list, not billing
evidence. If any element is missing, emit nothing — silence is cheaper than a retraction.

**7. Disconfirming pass.** Before flagging any driver as waste, search for the controls and reasons that make it
deliberate: committed-use or reserved declarations, spot and preemptible pools, scale-to-zero and scheduled
scale-down, autoscaler consolidation, budget alerts, cost allocation tags, and compliance or latency
requirements recorded in ADRs. Record the query and its result.

## Outputs
`cost-drivers.csv` (driver, citation, leverage score, environment) · `billing-data-request.md` (FOCUS columns, owner
role, join keys) · `estimates/*.md` when requested, each self-contained · findings and coverage records.

## Evidence requirements
Every driver cites the declaration or call site with commit SHA. Every currency figure cites a billing artifact or is
inside a labelled `ESTIMATE` block containing formula, inputs, sourced prices and range. A price with no source is a
defect equal to a wrong path, and the finding is withheld.

## Fact vs inference rules
FACT: declared instance classes, retention values, sampling settings, and any figure present in a supplied billing
export. INFERENCE: "log retention is a top-three driver" from a cited retention setting plus a cited log-volume driver
— ordinal only. HYPOTHESIS: that a declared resource exists in the account. EXTERNAL: actual spend, utilisation,
committed-use discounts, credits, negotiated rates and chargeback allocation (billing console or CUR, FOCUS export,
FinOps platform, vendor contract). "This costs $X" is never emitted from source alone.

## Confidence scoring rules
Driver identification with a cited declaration = C3 for the *driver*, never for an amount. Any monetary claim requires
C4: billing artifact plus the join to the cited resource. Estimates are capped at C2, carry
`external_validation.required: true`, and may not appear in an executive summary as a number — only as a range with
its inputs visible.

## Repository coverage rules
Population: declared billable resources from RDA-20, denominator
`terraform show -json tfplan | jq '[.. | .resources? // empty | .[]] | length'`, plus the RDA-21 telemetry
population. Report coverage per environment: a staging-only sample yields a ranking that does not apply to production.

## Large repository strategy
Shard by IaC root and environment; drivers merge by union and the leverage ranking is computed once in the reduce
step. Budget guard: rank production roots first, then always-on non-production; mark unexamined roots
`BUDGET_EXHAUSTED` and never extrapolate a ranking from the examined subset.

## Failure conditions
No RDA-20 output · infrastructure provisioned outside IaC (its drivers are invisible here) · managed platforms where
instance shape is not declared · no billing export and no estimate request, leaving only the inventory.

## Escalation conditions
A driver that is also a security or availability risk (public egress path, unbounded retention of personal data — hand
to RDA-16) · an unbounded queue or retry loop against a metered third-party API · a declared always-on GPU or premium
tier in a non-production environment · billing data supplied that contains customer identifiers.

## External validation required
Actual spend by service and resource (system of record: cloud billing console or CUR, ideally FOCUS-formatted) ·
utilisation against provisioned capacity (cloud metrics) · commitments, credits and negotiated rates (finance) · which
environments are chargeable (FinOps owner).

## Known limitations
Two ways this skill produces a wrong answer. **(a) The savings slide** — multiplying instance types read from
Terraform by remembered list prices to produce a headline figure; the absolute rule, the step-6 estimate protocol and
the C4 requirement for monetary claims block it, and the output is a data request instead. **(b) The false waste
flag** — calling a large instance or long retention wasteful when it is covered by a commitment, sized for compliance,
or never applied; step 7 requires the controls-and-reasons sweep and RDA-20's intent-not-state rule keeps declarations
from becoming account facts.

## Success criteria
Zero currency figures without billing evidence · every estimate is self-contained and reproducible from its own block
· the driver ranking is ordinal and cited · the billing data request names columns, join keys and an owner role · no
driver is called waste without a recorded disconfirming search.

## Example prompts
- Claude Code / Cursor: "Run rda-25-cost-efficiency-review: rank the cost drivers you can cite in IaC and code, and write the FOCUS billing data request. No dollar figures."
- Codex: "$rda-25-cost-efficiency-review — list always-on and retention drivers per environment with citations, then stop; we will supply the CUR export."
- Antigravity / Gemini CLI: "/rda-cost iac=infra/ estimate=false output=cost-drivers.csv"
