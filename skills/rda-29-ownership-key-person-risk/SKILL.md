---
name: rda-29-ownership-key-person-risk
description: Measures contribution concentration, orphaned components and CODEOWNERS accuracy as risk concentration by component and role, never individual evaluation; run when continuity risk is in scope.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-29"
  layer: "4-health"
  risk_class: "HIGH_HARM"
  tier: "conditional"
  depends_on: "RDA-28"
---

# RDA-29 · Ownership & Key-Person Risk

Inherits RDA-00. Read the constraint in Purpose before running anything: this skill measures components, never people, and that boundary is legal and ethical rather than stylistic.

## Purpose
Identify components whose change history is concentrated enough to put continuity at risk, and attach the mitigation.

**HARD CONSTRAINT — RISK CONCENTRATION BY ROLE AND COMPONENT ONLY.** This skill never evaluates, ranks or compares
individuals, never infers competence, seniority or productivity, and never names a person as a risk. The permitted
output shape is "component X has 78% of its 24-month commits from a single contributor identity, mitigation Y". The
forbidden output shape is "person P is a bus factor". Commit metadata is personal data; treat it accordingly (BSR-09).

## Business value
Continuity risk is a standard diligence question and a standard integration blocker, and concentration is genuinely
measurable from history. Competence is not measurable from history at all, and asserting it destroys the whole report.

## When to use
Conditional: when continuity or key-person risk is in the engagement question, at acquisition or team transition,
when RDA-28 shows concentrated authorship, or when CODEOWNERS is being relied on as a review control.

## When NOT to use
For any performance, staffing, compensation, redundancy or hiring input · where output cannot be pseudonymised before
leaving engineering · where processing commit metadata for this purpose has not been agreed. "Who are the weak
engineers" is refused, with the reason stated, and escalated to the engagement owner.

## Inputs
RDA-28 outputs · `.mailmap` · CODEOWNERS · the component map from RDA-04 or the top-level unit list · census path
classes · 24 months of history · pinned SHAs. HR rosters and directory data are **out of scope and never joined**.

## Procedure

**1. Identity normalisation, before any number is computed.**
```
git shortlog -sne --since=24.months --no-merges                        > own/identities.txt
git log --since=24.months --no-merges --format='%aN|%aE|%cN' | sort -u > own/raw-identities.psv
git check-mailmap "<name> <email>"        # confirm .mailmap resolves each variant
```
Assign stable pseudonyms (`identity-01..N`) here and use only pseudonyms downstream; classify bots and service
accounts out. Degraded fallback without `.mailmap`: cluster on name plus email local-part and cap findings at C1.
Unresolved duplicates are a coverage caveat, never a finding — email drift makes one contributor look like three.

**2. Per-component concentration.** For each component: commits per identity, top-identity share, top-2 share, and
the count of identities above a 5% share (policy), repeated over 12 months to expose the trend.
```
git log --since=24.months --no-merges --format='%H|%aE' --numstat -- <component> > own/<component>.psv
```
Apply the RDA-26 mechanical-commit filter first — one reformat commit can hand an entire component to one identity.

**3. Orphaned components.** A component with no commit in the window from any identity still committing anywhere in
the repository (policy default: 6 months). Repository activity is not employment: whether someone left is HR's system
of record and is asked, never inferred from commit silence.

**4. CODEOWNERS accuracy against commit evidence.** For each rule, test whether the pattern matches tracked paths
(`git ls-files -- '<pattern>' | head`) and whether the named owner appears in 12 months of commits to those paths.
Emit three lists: rules matching nothing, paths matched by no rule, owners with no commit evidence. Report at team
granularity wherever CODEOWNERS names a team.

**5. Silo intersection.** Cross-reference concentration with RDA-26 hotspots and RDA-03 entry points: concentration on a
low-churn component is noise, concentration on a high-churn money path is the finding. Publish the intersection.

**6. Threshold labelling.** Every threshold — top-identity share, active window, minimum commit count — is stated
inline **as policy** with its value. Truck-factor style estimators identify *which* components are knowledge-
concentrated far more reliably than they estimate *how many* people the number represents, and no specific threshold
has an evidentiary basis: it is practitioner convention. Report the component set and the concentration measure, and
treat any single "factor" number as an ordinal label, never as a count of people.

**7. Mitigation is mandatory on every finding.** Rotation or pairing on the component, the documentation or ADR gap to
fill, tests as an alternative knowledge store, the CODEOWNERS correction. Without one, a finding is just an accusation.

**8. Disconfirming pass.** For each finding search for evidence knowledge is already shared: review participation on
that component, `Co-authored-by` trailers, docs and tests authored by other identities, rotation notes.

## Outputs
`ownership-concentration.csv` (component, top-identity share, contributor count, 12/24m trend, hotspot flag, mitigation)
· CODEOWNERS accuracy table · orphaned-component list · findings. Identities appear only as pseudonyms or team names.

## Evidence requirements
Every share cites its `git log` invocation, window, filter set and n. Every CODEOWNERS claim cites `CODEOWNERS#Lstart-Lend`
+ commit SHA + quote. Every orphan claim cites the last commit SHA and date for that path.

## Fact vs inference rules
`FACT`: "component X: 78% of 312 non-mechanical commits in 24 months from one contributor identity". `INFERENCE`:
continuity risk for that component, derived from concentration + hotspot rank + entry-point criticality, about the
**role**, per ES-1 §2. Prohibited at every class: that a named person is a risk, that an identity is irreplaceable,
any competence, productivity or seniority claim, and any comparison between identities.

## Confidence scoring rules
C3 maximum for concentration counts, downgraded one level when `.mailmap` coverage is incomplete or bots are
unclassified. Orphan claims cap at **C2** (activity is not employment). C4 is unreachable: knowledge has no artifact.

## Repository coverage rules
Population = components from RDA-04 or top-level units, denominated by the census. Report both the share of components
analysed and the share of commits attributable after normalisation; unattributable commits are a declared blind spot.

## Large repository strategy
Shard by component — concentration is per-component, so shards are independent and parallel. In monorepos compute at
two levels: a component that looks shared at repository level can still be a silo at module level.

## Failure conditions
No `.mailmap` with heavy email drift (declare, cap confidence) · squash merges attributing authorship to a bot
(unmeasurable) · rewritten history · missing component map · too few commits (insufficient data, never low concentration).

## Escalation conditions
Any request to name, rank or compare individuals, or to feed this into staffing decisions — refuse, cite BSR-09,
escalate to the engagement owner · any sign that commit metadata is being processed outside the agreed purpose —
stop and escalate to the data-protection role · discovery of personal data beyond commit metadata in the history.

## External validation required
Whether an identity is still with the organisation · whether concentration is already mitigated outside the repository
(pairing, docs, a wiki) · whether a CODEOWNERS team is still staffed · contractual continuity commitments.

## Known limitations
Two ways this skill produces a wrong answer, and the controls that stop them. **(a) Identity fragmentation and bot
accounts distort every share** — prevented by normalising through `.mailmap` and classifying bots in step 1 before
any number exists, and by declaring unresolved identities as coverage loss. **(b) Commits measure authorship of
change, not knowledge**: reviewers, pairs and the person who designed the component may never appear in the log —
prevented by the step-8 disconfirming pass over review participation and `Co-authored-by` trailers, and by the rule
that a concentration measure never becomes a statement about a person. Truck-factor numbers stay ordinal.

## Success criteria
No individual named, ranked or characterised anywhere in the output · every threshold labelled policy with its value
· every finding carries a mitigation · CODEOWNERS claims cite rule and commit evidence · RDA-32 finds no capability claim.

## Example prompts
- Claude Code / Cursor: "Run rda-29-ownership-key-person-risk — per-component concentration with pseudonymised identities, CODEOWNERS accuracy, mitigations; name nobody."
- Codex: "$rda-29-ownership-key-person-risk — normalise identities via .mailmap, compute 12/24-month concentration per top-level unit, emit ownership-concentration.csv."
- Antigravity / Gemini CLI: "/rda-ownership scope=. window=24m pseudonymise=true thresholds=policy"
