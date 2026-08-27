---
name: rda-37-portfolio-multi-repo-rollup
description: Rolls per-repository registers into a fleet view with cross-repo dedupe, systemic versus local risk, shared-component exposure and comparative posture bands, whenever scope spans several repos.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-37"
  layer: "5-synthesis"
  risk_class: "MEDIUM_HARM"
  tier: "conditional"
  depends_on: "RDA-33 (per repository)"
---

# RDA-37 · Portfolio / Multi-Repo Rollup

Inherits RDA-00. A fleet is not a large repository: the question changes from "what is wrong here" to "what is wrong
everywhere, who fixes it once, and which single repository will cause the incident".

## Purpose
Roll per-repository registers into one fleet view: cross-repo deduplication, systemic versus local classification,
shared-component exposure mapping, and comparative posture with every coverage band visible.

## Business value
Fixing a shared template once beats fixing its symptom in fourteen repositories — but only if the shared cause is recognised
as one risk. And a portfolio decision taken on an average is blind to the outlier carrying the exposure.

## When to use
Any scope with more than one repository: platform assessments, group-level diligence, post-merger estates, internal-platform
reviews. Activated by the RDA-01 trigger "more than one repository in scope".

## When NOT to use
Single-repository scope · fewer than two valid registers, which is not a portfolio · as a substitute for auditing a
repository nobody audited, since an absence of findings is not low risk.

## Inputs
Per-repository `risk-register.csv`, `findings.json`, `coverage.json` and `run-manifest.json` · per-repository SBOM from
RDA-13 for component identity · RDA-03 exposure data · the shared-artifact inventory: CI templates, base images, IaC
modules, internal libraries, submodules, monorepo packages.

## Procedure
**1. Deterministic pass.** Load every register; assert matching skill versions; record each repository's commit pin and
risk-surface band. A repository whose RDA-32 gates failed, or whose register is a lead list, is listed **NOT COMPARABLE**
and excluded from every count — never silently averaged in. Sort by name for stable output.

**2. Normalise identity keys.** Third-party components match on package coordinate plus resolved version plus lockfile hash
from the SBOM; internal code matches on import path, submodule commit, vendored path or monorepo package name.
**Name-similarity matching is HYPOTHESIS-level** and is flagged: two packages called `acme-auth` in different registries are
not one component.

**3. Cross-repository deduplication.** One vulnerable dependency present in fourteen repositories is **one risk with
fourteen exposure sites**, not fourteen risks; the same holds for a shared CI template, base image, IaC module or internal
library. Each fleet row carries its contributing per-repo finding ids and commit pins.

**4. Classify SYSTEMIC versus LOCAL.** SYSTEMIC when traced to a cited shared artifact, or present in at least the policy
threshold share of comparable repositories — **default two-thirds, a policy value published with its denominator**, not a
measurement. SYSTEMIC is fixed once centrally under a platform role; LOCAL is fixed in the one repository that has it.

**5. Map shared-component exposure.** Per component: affected repositories, version spread, whether each site is reachable
per that repository's RDA-13 determination rather than by assumption, and which sites sit behind an externally reachable
entry point per RDA-03. Unknown reachability stays UNKNOWN.

**6. Prioritise by affected repositories x severity.** Rank by comparable affected-repository count multiplied by severity
rank, carrying SSVC and the confidence distribution alongside. The product is a sort key, never a published score, and never
emitted without its weighting. Ties break to externally reachable sites, then to the row with a single shared owner.

**7. Comparative posture table.** One row per repository with **every cell carrying its own coverage band**. A repository
audited at INDICATIVE coverage is never ranked against one at BROAD without both bands visible; unequal audit depth is the
easiest thing to hide in a fleet table and the most misleading when hidden.

**8. Distribution, never an average alone.** Report minimum, median, maximum, the count per severity band and the **named
worst-case repository** for every fleet metric. An average ships only alongside those, because the average is exactly the
statistic that conceals the repository that will cause the incident.

**9. Disconfirming pass.** For each SYSTEMIC row, examine the comparable repositories that do **not** carry it and record
why — already remediated, different framework, forked template, compensating control. Those exceptions frequently hold the
fix the central remediation should copy.

## Outputs
`portfolio-rollup.md` · `portfolio-register.csv` (fleet risk id, systemic/local, affected repos, exposure sites, severity,
confidence distribution, shared artifact, owner role, contributing finding ids) · `shared-component-exposure.csv` · the
posture table with in-cell bands · the NOT COMPARABLE list with reasons · distribution statistics and the named worst case
per metric.

## Evidence requirements
Every fleet row cites the per-repository finding ids and commit pins composing it. Version identity comes from lockfiles or
SBOM output with tool name and version, never from a package-name string. A fleet claim with no per-repository citations is
deleted, not caveated.

## Fact vs inference rules
Presence and affected-repository counts are FACT over the comparable set. SYSTEMIC classification is INFERENCE from the
count plus a cited shared artifact. "The platform team can fix this once" is HYPOTHESIS until the artifact and its ownership
are cited, and ownership is a role, never an individual (BSR-09).

## Confidence scoring rules
Fleet confidence is the **minimum** of contributing per-repository confidences — never averaged, never raised by repetition.
Ten C1 findings of the same shape across ten repositories are still C1: one method applied ten times is one method, not ten
independent sources (ES-1 §4). Publish the per-repo confidence distribution per row.

## Repository coverage rules
Two denominators lead the document: repositories in scope versus repositories with a valid register, and per repository the
risk-surface band. A rollup over six of forty says so in its first line, and no fleet claim exceeds the coverage of the
repositories it generalises from.

## Large repository strategy
Map-reduce over registers; source is never re-read here. Above roughly fifty repositories, tier by declared exposure and
criticality, roll the tail up on registers alone, and state that it received no further inspection — a tier is a sampling
decision and carries a coverage record.

## Failure conditions
Fewer than two comparable registers · heterogeneous skill versions, or pins outside the policy comparison window · missing
SBOM, which degrades matching to name similarity, caps those rows at HYPOTHESIS and is declared · registers built under
different business-impact contexts, making severity non-comparable until re-scored.

## Escalation conditions
A shared vulnerable component with an externally reachable site in any repository · a systemic secret-handling or credential
defect in a shared template or base image, halted and escalated immediately because one template propagates across the whole
estate · a systemic licence-contamination path, which goes to legal.

## External validation required
Which repositories are actually deployed and which are archived · who owns each shared artifact · the fleet-level
risk-acceptance authority · whether the unaudited tail is low criticality or merely unexamined.

## Known limitations
Two ways this skill produces a wrong answer. **The fleet average that hides the incident**: "portfolio posture: MEDIUM"
while one payments repository carries a CRITICAL at C3 — prevented by step 8, which forbids an average without the
distribution and the named worst case. **The false-systemic count**: name-similarity matching merges two unrelated packages,
inflating the affected count and aiming a central fix at the wrong artifact — prevented by step 2's
coordinate-plus-version-plus-hash identity and the HYPOTHESIS flag on name-only matches. Beyond those: unequal audit depth
limits comparability, and an unaudited repository is not a low-risk repository.

## Success criteria
Every fleet row resolves to per-repository finding ids · no average without its distribution and named worst case · every
posture cell carries its band · NOT COMPARABLE repositories listed and excluded from counts · component identity is
coordinate-based wherever an SBOM exists.

## Example prompts
- Claude Code / Cursor: "Run rda-37-portfolio-multi-repo-rollup over the registers in ./audits; dedupe shared components, split systemic from local, show per-repo coverage bands."
- Codex: "$rda-37-portfolio-multi-repo-rollup — build the fleet register, rank by affected repos x severity, report the distribution and worst case, not an average."
- Antigravity / Gemini CLI: "/rda-portfolio registers=./audits/*/risk-register.csv output=portfolio-rollup.md exposure=shared-component-exposure.csv"
