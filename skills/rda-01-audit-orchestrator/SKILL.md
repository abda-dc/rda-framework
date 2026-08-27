---
name: rda-01-audit-orchestrator
description: Scopes a repository audit, selects the workflow profile and skill DAG, sets token budgets and shard plans, and opens the run manifest. Use before any multi-skill audit or due-diligence engagement.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-01"
  layer: "0-kernel"
  risk_class: "HIGH_HARM"
  tier: "core"
  depends_on: "RDA-00"
---

# RDA-01 · Audit Orchestrator

Inherits RDA-00. Wrong scoping is the most expensive error in the framework: it is invisible in the output and
it silently caps every downstream skill's validity.

## Purpose
Turn a vague request ("review this codebase") into a bounded, budgeted, resumable engagement with a declared
question, a declared profile, and a manifest that makes the result auditable.

## Business value
Prevents the two standard failures: an audit that answers a question nobody asked, and an audit that runs out
of budget three-quarters through and reports as if it had finished.

## When to use
Any engagement invoking more than one RDA skill; any repository above ~2,000 files; any audit whose output
leaves the engineering team.

## When NOT to use
A single targeted question on a small repo ("is auth applied to this route?") — invoke the one relevant skill.

## Inputs
Repository access and remotes · the decision the audit must serve · the deadline · available deterministic
tools · access to non-source systems (runtime, billing, incidents, ticketing) · regulatory context.

## Procedure

**1. Establish the decision.** Write the decision in one sentence: acquire/don't, ship/don't, invest/don't,
onboard, remediate. If it cannot be written, stop and ask — an audit without a decision has no severity scale,
because impact is defined against the decision.

**2. Pin the scope.** Record for each repository: remote, default branch, HEAD SHA, shallow/full, submodules,
LFS. **All findings are asserted as of these SHAs.** Record exclusions (vendored, generated, binary) explicitly
— exclusions are coverage gaps, not silence.

**3. Size the corpus.** Run RDA-02 first. Never plan against an estimate of repository size.

**4. Select the profile** from `workflows/`: small · medium · large-monorepo · m&a-due-diligence ·
security-audit · production-readiness · cto-onboarding. Then adjust with trigger conditions:

| Condition (from census) | Activate |
|---|---|
| >1 deployable unit / service manifest | RDA-06, RDA-22 |
| IaC or k8s manifests present | RDA-20, RDA-23 |
| Payment, health, identity or personal-data indicators | RDA-16, RDA-17, and raise the security floor |
| Public-facing routes | RDA-05, RDA-12 |
| >1 repository in scope | RDA-37 |
| Third-party or vendored source present | RDA-15 |
| Audit output leaves the engineering org | RDA-31, RDA-32, RDA-36 (mandatory) |

**5. Budget.** Assign each planned skill a token band and a wall-clock ceiling. Reserve **at least 20% of total
budget for RDA-32 verification** — verification is not the part you cut when time runs short; unverified
findings are worse than absent ones because a plausible false finding consumes reviewer time and credibility.

**6. Shard.** For repositories beyond a single context: shard by deployable unit, then by directory, in a
deterministic sorted order with a recorded seed. Each shard produces structured findings, never prose. The
reduce step re-reads at source before promoting anything to the executive layer.

**7. Open the manifest** (`schemas/run-manifest.schema.json`) and record tool availability. Any required tool
that is missing is a **declared degradation**, recorded now, surfaced in the report — not discovered later.

**8. Enforce resumability.** After each skill, append its execution record. A run that dies mid-way resumes
from the manifest, and a skill that hit its budget ceiling is recorded `ABORTED_BUDGET` with a blind-spot entry.

## Outputs
`audit-plan.md` (decision, scope, profile, DAG, budgets, exclusions) · `run-manifest.json` (open) ·
the activation table with reasons · the declared degradation list.

## Evidence requirements
The plan itself is evidence: scope pins, tool versions and profile choice are recorded in the manifest with the
commands that produced them. Any characterisation of the repository used to justify a profile must cite the
census key it came from, so that a reviewer can tell a measured decision from an assumed one.

## Fact vs inference rules
The plan is a set of decisions, not findings. Any characterisation of the repository in the plan is provisional
and carries no confidence level until the owning skill produces it.

## Confidence scoring rules
Not applicable — RDA-01 emits no findings. It emits constraints that cap other skills' confidence.

## Repository coverage rules
Coverage is defined here and measured by RDA-02. The plan states the *intended* coverage per skill; the report
states the achieved coverage. Divergence between the two is itself reportable.

## Large repository strategy
Above ~50k files: mandatory two-phase run — deterministic sweep across 100%, then model passes over the
risk-weighted strata only. Above ~200k files or multi-repo: run RDA-02/RDA-03 per unit, then RDA-37 rollup;
never attempt a single global reasoning pass.

## Failure conditions
No write access to record a manifest · scope cannot be pinned (moving branch, no SHA) · the decision cannot be
articulated · required access is missing for the profile chosen (then downgrade the profile explicitly).

## Escalation conditions
Scope includes material the audit is not authorised to read · the deadline is incompatible with the minimum
profile (say so before starting, not in the summary).

## External validation required
Business context for the impact scale · which systems are actually production · who owns the decision.

## Known limitations
Profile selection is heuristic. A monorepo containing one live service and forty dead ones will be mis-sized
until RDA-02 completes; re-plan after census rather than trusting the initial guess.

## Success criteria
The manifest reproduces the run · every executed skill has a status and coverage score · no skill silently
skipped · verification budget preserved · the plan's declared decision appears verbatim in RDA-36's output.

## Example prompts
- Claude Code / Cursor / Windsurf: "Use rda-01-audit-orchestrator to scope an M&A due-diligence audit of this monorepo; deadline is Friday, we have no runtime access."
- Codex / OpenAI Agents: "$rda-01-audit-orchestrator — plan a production-readiness review for the services in ./services, pin commits, and open the manifest."
- Antigravity / Gemini CLI: "/rda-audit-plan security-audit scope=. output=audit-plan.md"
