---
name: rda-26-code-quality-debt
description: Ranks complexity and duplication hotspots by change frequency and converts them into banded remediation work, never a debt currency figure; use for maintainability or "how much debt" questions.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-26"
  layer: "4-health"
  risk_class: "LOW_HARM"
  tier: "core"
  depends_on: "RDA-02"
---

# RDA-26 · Code Quality & Technical Debt

Inherits RDA-00. Quality numbers are the cheapest artifact in an audit and the most over-read; this skill keeps each one tied to a decision it can support.

## Purpose
Find where change is structurally expensive — complexity and duplication concentrated in code that actually changes —
and express it as ranked, banded remediation work with the reasoning written out.

## Business value
An incoming CTO or acquirer needs to know where the next twelve months of change will be slow, and why. A ranked
hotspot list with effort bands can be planned against; a debt number cannot be defended under challenge or re-derived.

## When to use
Every profile (core). Triggered by "how maintainable is this", "how much technical debt", "where will change be slow",
"is this codebase worth keeping", or before scoping a modernisation or rewrite decision.

## When NOT to use
To estimate defect risk on a feature (RDA-18 + RDA-07), to find unused code (RDA-27 — static non-reference is not a
quality signal), to compare teams or individuals (prohibited; see RDA-29), or to produce a letter grade.

## Inputs
`census.json` path classes and denominators · `hotspots.csv` (churn × size) · exclusions (generated, vendored, binary)
· language inventory · available static-analysis tools with versions · pinned commit SHAs.

## Procedure

**1. Deterministic metric sweep over 100% of the `source` population.** Record tool, version, args, exit code:
```
scc --by-file --format json --exclude-dir vendor,node_modules,dist . > qm/scc.json
scc --hotspots --coupling --by-author . > qm/scc-hotspots.txt            # deterministic churn x complexity
lizard --csv --languages python,java,javascript,cpp . > qm/lizard.csv   # per-function CCN, NLOC, params
jscpd --min-tokens 50 --reporters json --output qm/ .                   # copy-paste clones
```
Fallbacks where `lizard` lacks the grammar: `radon cc -s -j .` (Python), `gocyclo -avg .` (Go), `pmd cpd` (clones).
A language with no available tool is a blind spot, reason `TOOL_UNAVAILABLE` — never read-and-estimate complexity.

**2. Churn join, with mechanical commits removed first.** Raw churn is the main source of false hotspots:
```
git log --since=24.months --no-merges -M -C --format='%H' --numstat -- . > qm/churn.raw
git log --since=24.months --no-merges --format='%H %ct' --shortstat   > qm/commit-sizes.txt
```
Exclude commits in `.git-blame-ignore-revs`, commits touching more than a policy cap of files (default 200 — **policy,
not evidence**), and whitespace-only diffs (`git show -w --stat <sha>`). Reformats, licence sweeps, codegen refreshes
and repo migrations otherwise manufacture hotspots in code nobody touched.

**3. Rank on two coordinates.** `rank = complexity_percentile × churn_percentile` over the `source` class, both
coordinates printed on every row, cross-checked against `scc --hotspots`. A 900-line file untouched for three years is
a museum piece; a 60-line file changed weekly by four people is where the money goes.

**4. Targeted read pass.** Read top hotspots within budget, citing `path#Lstart-Lend` + SHA per claim, and classify
each: deliberate-and-documented (an ADR accepts it), deliberate-and-undocumented, inadvertent-structural (wrong seam),
or accretive (a function that grew). The class drives remediation shape; issue counts do not.

**5. Interpretation layer — bands and reasons, never a currency total.** A single "$X of technical debt" figure is
epistemically weak for four independent reasons, so this skill emits none:
- **Per-rule remediation cost is an author-assigned constant.** Multiplying issue counts by an editorial constant
  yields a figure whose apparent precision is inherited entirely from that editorial choice.
- **The debt-ratio denominator is a synthetic cost-per-line constant.** Two vendors with different constants return
  different ratios — and different grades — for byte-identical code. The ratio compares one convention to another.
- **Rule engines cannot see architectural debt.** A wrong domain model, a distributed monolith, a schema that blocks
  multi-tenancy: none is expressible as a rule hit, and all of it dominates real remediation cost.
- **Threshold letter grades are min-aggregations.** One blocker-class issue drops a multi-million-line codebase to the
  worst grade, so the grade reports one line and conceals the rest.
Emit instead: ranked hotspots, each with an effort band (`XS`..`XL`), the structural reason, blast radius and
prerequisite work. State bands as bands; never convert a band into person-days or currency here.

**6. Disconfirming pass before publishing a hotspot.** Search for evidence it is already handled — an ADR accepting it,
an in-flight refactor branch, a `@deprecated` marker, a rewrite ticket — and record it in `disconfirming_check`.

## Outputs
`quality-hotspots.csv` (path, complexity, churn, rank, class, effort band, reason) · findings per
`schemas/finding.schema.json` · a coverage record per language · duplication clusters carrying **both** clone locators.

## Evidence requirements
Every metric carries tool, version, args and exit code. Every structural claim carries `path#Lstart-Lend` + commit SHA
+ a verbatim quote under 600 chars. Churn claims cite the `git log` invocation and the exact filter set applied.

## Fact vs inference rules
`FACT`: metric values, clone pairs, churn counts, tool output. `INFERENCE`: "change here is expensive", from ≥2
independent facts (complexity + churn rank + a cited coupling site). `HYPOTHESIS`: future maintenance effort or defect
likelihood. `EXTERNAL_VALIDATION_REQUIRED`: remediation cost in money or person-days, and any claim that debt is
"slowing the team". **The Maintainability Index is never a headline metric**: a fitted composite whose implementations
rescale and clamp differently, so its value is not comparable across tools — cite volume, complexity and lines instead.

## Confidence scoring rules
C3 ceiling for metric facts (deterministic tool + reproducible command). Interpretive hotspots reach C2 only with a
recorded disconfirming search and two independent groups; unfiltered churn caps them at C1, and nothing here is
CRITICAL until RDA-07 or RDA-11 attaches it to a live risk surface.

## Repository coverage rules
Population = files classed `source` in `census.json`, per language; the denominator is a census key, never a fresh
count. Report artifact coverage (files measured / source files) and read coverage (files read / hotspots identified)
separately — the sweep is usually EXHAUSTIVE while the read pass is PARTIAL, and conflating them overstates the review.

## Large repository strategy
Shard by deployable unit, then top-level directory, sorted. Metric tools run over 100% per shard and merge by summing
counts, never by summarising prose; the model reads only top hotspots per shard. Above ~200k files, cache `scc` and
`lizard` output keyed by commit SHA so re-runs are near-free.

## Failure conditions
No complexity tool for a majority language (record `TOOL_UNAVAILABLE`; do not read-and-guess) · shallow clone (churn
invalid — degrade to complexity-only and say so) · generated code unclassified by RDA-02 (fix the census first).

## Escalation conditions
Committed secrets or personal data in fixtures (RDA-10 / RDA-16, halt that traversal) · vendored source without licence
headers (RDA-15) · a hotspot on a money-movement or auth path (RDA-07 / RDA-11 own its severity, never this skill).

## External validation required
Whether a hotspot corresponds to deployed code · whether a funded remediation plan exists · the real cost of change
here (ticket cycle time from the tracker, not a model estimate) · whether accepted debt was a documented decision.

## Known limitations
Two ways this skill produces a wrong answer, with the controls that stop them. **(a) Generated or vendored code counted
as source** floods the ranking with protobuf stubs and bundled libraries — prevented by drawing the population from
census path classes and re-checking every hotspot's class before it is written. **(b) A repo-wide reformat or framework
bump inflates churn** and invents hotspots in untouched code — prevented by the step-2 mechanical-commit filter, with
affected rows dropped to `HYPOTHESIS` when it cannot be applied. Metrics measure structure, never correctness.

## Success criteria
Every hotspot row carries two coordinates, an effort band and a structural reason · no currency figure and no letter
grade anywhere in the output · no Maintainability Index value as a headline · the top ten hotspots survive RDA-32
re-derivation · coverage bands printed next to every section heading.

## Example prompts
- Claude Code / Cursor: "Run rda-26-code-quality-debt here — hotspot ranking with effort bands, no debt dollar figure, cite path#Lx-Ly and SHAs."
- Codex: "$rda-26-code-quality-debt — sweep scc/lizard/jscpd over ./services, join with 24-month churn minus mechanical commits, emit quality-hotspots.csv."
- Antigravity / Gemini CLI: "/rda-quality scope=. window=24m output=quality-hotspots.csv bands=true grade=false"
