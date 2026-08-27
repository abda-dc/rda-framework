---
name: rda-35-remediation-roadmap
description: Sequences the RDA-33 risk register into a dependency-aware remediation plan with effort bands, prerequisites, quick-win versus structural tranches and an accept-risk option per item.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-35"
  layer: "5-synthesis"
  risk_class: "MEDIUM_HARM"
  tier: "conditional"
  depends_on: "RDA-33"
---

# RDA-35 · Remediation Roadmap

Inherits RDA-00. A register tells a team what is wrong; this turns it into what to do first, in an order that does not stall
at item one, without inventing a single number the source cannot support.

## Purpose
Convert the ordered register into a sequenced plan: dependency-aware ordering, effort in bands with a counted basis, a
quick-wins tranche separated from structural work, prerequisites, and what each item unblocks.

## Business value
Most audit output dies as an unordered list nobody can start. Sequencing by prerequisite makes the first week actionable;
effort bands with a stated basis survive challenge; the accept-risk column forces the decision that an unsequenced findings
list quietly avoids.

## When to use
When the audience needs a plan rather than an assessment: post-acquisition integration, production-readiness remediation, a
CTO's first ninety days, or any register handed to the team that owns the code.

## When NOT to use
When the register is a lead list (majority C1) — verify first, plan second. When the requester wants dates, budgets or
headcount: this skill produces bands and names who must price them, and refuses the rest.

## Inputs
`risk-register.csv` and merged `findings.json` from RDA-33 · `remediation` blocks and `prerequisite_finding_ids` from the
source findings · RDA-19/RDA-21/RDA-20 evidence for capability prerequisites · the RDA-34 ledger, because a gap can block a
remediation item as easily as a decision.

## Procedure
**1. Deterministic pass.** Load the register in its published order. Assert every candidate item resolves to a register row
id and that no quarantined row leaked in. Items are derived from existing `remediation.action` fields; an item with no
source row is not created here.

**2. Build the prerequisite graph.** Edges come from `prerequisite_finding_ids` plus capability rules that hold regardless
of repository: telemetry before SLOs and alert thresholds; CI before required checks and branch protection; a test harness
before refactoring the module it guards; an SBOM before dependency policy; IaC before drift detection; secret rotation
before any history rewrite. Every edge cites the evidence that the prerequisite is missing. A detected cycle means a
mis-stated prerequisite, resolved by splitting the item and never by silently deleting the edge.

**3. Topologically order.** Sort the DAG, breaking ties by register order (severity, ssvc, confidence, blast radius, effort
band) and finally by item id, so two runs emit the same sequence. Record, per item, the set it unblocks — that count is the
leverage signal used in step 5.

**4. Size in bands with a basis.** Effort is `XS`/`S`/`M`/`L`/`XL`/`UNKNOWN` and each band records the counted artifact that
sizes it: call sites to change from a grep count, services affected from the census, migrations in the directory, routes
lacking the control. **A band with no counted basis is `UNKNOWN`, not a guess.**

**5. Split the tranches.** `QUICK_WINS`: XS or S, no unmet prerequisites, severity MEDIUM or above — typically
configuration, CI gates, policy and pinning. `STRUCTURAL`: L or XL, or anything with unmet prerequisites — architecture,
data model, ownership, platform. Flag `ENABLERS` separately: the prerequisites that unblock the most items, which are
frequently unglamorous and always mis-prioritised without this step.

**6. Cost of inaction, in risk terms.** Each item carries what happens if it is not done: the severity and confidence pair,
the cited blast radius, and what worsens with time — dependency support windows expiring, contribution concentration
deepening, migration debt compounding. Cite it, or the cell says UNKNOWN.

**7. Offer ACCEPT_RISK explicitly.** Every item carries an accept option with the residual risk stated and the role
empowered to accept it. Some items should be accepted, and a roadmap that hides that choice is a wish list. `sequencing` is
one of `NOW` / `NEXT` / `LATER` / `ACCEPT_RISK` and is never left implicit.

**8. Disconfirming pass.** For each quick win, search for the reason it was not already done: a reverted commit, a closed
PR, an ADR rejecting it, a compatibility constraint, a vendor requirement. There often is one, and recording it prevents
recommending work that has already failed once.

## Outputs
`remediation-roadmap.md` · `roadmap.csv` (item id, finding ids, tranche, effort band, band basis, prerequisites, unblocks,
owner role, cost of inaction, accept-risk residual, sequencing) · the prerequisite DAG as DOT or Mermaid · the enabler list
ranked by items unblocked · the verification tranche for items sourced from C1 rows.

## Evidence requirements
Every item cites its register row and, through it, the original locators and commit pins. Every effort band cites the
counted artifact and the command that counted it. "You have no telemetry" is a claim requiring citation, not an assumption
that justifies a sequencing decision.

## Fact vs inference rules
Item existence is FACT by trace to a register row. Prerequisite edges are INFERENCE with the absence evidence cited. Effort
bands are labelled `ESTIMATE` with inputs shown (BSR-10). **Durations, costs, capacity and dates are
EXTERNAL_VALIDATION_REQUIRED, always** — velocity is not a property of a repository. **Hard rule:** no person-day point
estimates and no currency figures derived from source inspection; if the audience needs money, state the band, the
assumptions behind it and the role that must price it, then stop.

## Confidence scoring rules
An item never carries higher confidence than its source finding. Items from C1 rows go to the verification tranche, because
verifying is cheaper than remediating the wrong thing. Ordering is a sequencing decision, not a confidence claim, and
carries no C-level of its own.

## Repository coverage rules
The roadmap inherits the register's coverage and prints the risk-surface band at the top. A roadmap built over INDICATIVE
coverage is a starting backlog and is labelled as one. No item may imply completeness: "after this tranche the repository is
secure" is not emissible below exhaustive coverage.

## Large repository strategy
One roadmap per deployable unit, with shared prerequisites hoisted into a platform tranche so a fix that serves twelve units
is not sequenced twelve times. Cross-repository consolidation belongs to RDA-37, not here.

## Failure conditions
Register absent, invalid or majority C1 · items that resolve to no finding id · a prerequisite cycle that cannot be split ·
a request for dates, budgets or person-days, which is refused and answered with bands plus the pricing owner · effort bands
with no counted basis anywhere in the plan.

## Escalation conditions
Any item touching live secret material or regulated data routes to the ESC-1 owner before it is scheduled · licence
contamination goes to legal before any remediation is recommended, because sequencing a fix implies a legal position RDA
does not hold · an item requiring production access the audit does not have.

## External validation required
Team capacity, velocity and calendar · budget authority and who prices work · which components are actually in production
and therefore change-controlled · the risk-acceptance authority for each ACCEPT_RISK row.

## Known limitations
Two ways this skill produces a wrong answer. **The sequencing inversion**: recommending SLOs before telemetry exists, or
branch protection before there is a CI pipeline to require — the plan stalls at item one and the team concludes the audit
never read the repository. Prevented by step 2's cited prerequisite edges and cycle detection. **The fabricated estimate**:
a person-day figure and a currency total read authoritatively, cannot be falsified from source, and anchor a budget
conversation — prevented by step 4's counted band basis, the hard rule above and BSR-10. Bands remain ordinal and
team-relative, and leverage assumes the codebase does not shift underneath the plan.

## Success criteria
Every item traces to a register row · no dates, currency figures or person-day estimates anywhere · the DAG is acyclic and
the emitted order is a valid topological sort · every item has an owner role and an accept-risk option with residual stated
· the quick-wins tranche contains zero unmet prerequisites.

## Example prompts
- Claude Code / Cursor: "Run rda-35-remediation-roadmap on risk-register.csv; build the prerequisite DAG, split quick wins from structural work, effort in bands only."
- Codex: "$rda-35-remediation-roadmap — sequence the register with prerequisites and unblocks, add cost of inaction and an accept-risk option per item."
- Antigravity / Gemini CLI: "/rda-roadmap register=risk-register.csv output=roadmap.csv graph=roadmap.dot"
