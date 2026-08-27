# RDA Confidence & Coverage Model (CC-1)

## 0. Why this is not a self-rated percentage

Verbalised model confidence ("I'm 85% sure") is a token sequence, not a measurement, and is systematically
overconfident. RDA therefore **forbids free-form numeric confidence** and replaces it with a rubric that is
awarded by *countable properties of the evidence*, not by feel. Any skill emitting "confidence: 0.87" is
defective; the linter rejects it.

## 1. Confidence ladder (awarded, not chosen)

| Level | Name | Award rule (all must hold) | Permitted use |
|---|---|---|---|
| **C0** | Unsupported | No resolvable evidence | **Never publishable.** Delete or convert to UNKNOWN |
| **C1** | Single-source | One resolvable citation; no disconfirming search performed; or `CONVENIENCE` sampling | Body of report, labelled. Never an executive headline. Never a HIGH/CRITICAL severity |
| **C2** | Corroborated | >=2 citations in different `independence_group`s **and** a disconfirming search was run and recorded | Executive body. Max level for any claim in the undecidable register |
| **C3** | Tool-corroborated | C2 **plus** a deterministic tool result (SAST/SBOM/AST/git/coverage) agreeing, with tool name+version+exit code | Required floor for HIGH/CRITICAL security, supply-chain, and data-governance findings |
| **C4** | Executed proof | C3 **plus** a reproduced execution artifact (test run, PoC, benchmark, query result) captured in the manifest | Required for any claim used to justify a spend, a go/no-go gate, or a deal price adjustment |

Ceilings that override the ladder:
- Any claim in the ES-1 undecidable register: **max C2**, and it must carry `external_validation.question`.
- Any finding derived from `CONVENIENCE` sampling: **max C1**.
- Any finding whose evidence predates the pinned commit's last touch of that file: **downgrade one level** (stale evidence).
- Any finding produced from summarised context rather than a direct read (map-reduce shard summaries): **max C2**
  until re-read at source. Summaries of summaries are capped at C1.

## 2. Severity and confidence are orthogonal — never multiplied

Report the pair, e.g. `HIGH / C2`. Collapsing them into one number lets a confident trivium outrank an
uncertain catastrophe, and hides which of the two needs work. Triage rules:
- `CRITICAL|HIGH` + `C1` -> not publishable as a finding; publishable as a **verification task**.
- `CRITICAL|HIGH` + `C3+` -> risk register, escalate per ESC-1.
- `LOW|INFO` + `C3` -> backlog, never an executive headline.

## 3. Coverage score

`coverage_score = inspected_count / population_count`, where `population_count` comes from the RDA-02 census
(a deterministic command), never from a model estimate.

Reporting bands, which must appear next to every skill's section heading:

| Band | Score | Language required in the report |
|---|---|---|
| EXHAUSTIVE | 1.0 | "All N inspected" |
| BROAD | 0.60-0.99 | "N of M inspected (x%)" |
| PARTIAL | 0.20-0.59 | "Sampled: N of M (x%). Conclusions do not generalise beyond the sample." |
| INDICATIVE | 0.05-0.19 | "Spot check only. Findings are examples, not an inventory." |
| ANECDOTAL | <0.05 | "Insufficient coverage for an assessment. Reported as leads only." |

Two coverage numbers are reported per skill: **artifact coverage** (files/services seen) and **risk-surface
coverage** (share of the risk-weighted population — e.g. share of externally reachable endpoints reviewed).
The second is the honest one; a monorepo audit can hit 80% file coverage and 10% of the auth surface.

## 4. The audit-quality metrics (reported in every run)

| Metric | Definition | Healthy range | Failure signal |
|---|---|---|---|
| Citation resolution rate | resolved citations / total | 1.00 | <1.00 means fabricated or drifted evidence exists |
| Unknown rate | UNKNOWN findings / total findings | 0.05-0.30 | 0 = false completeness; >0.5 = insufficient access, stop and rescope |
| Corroboration rate | findings at C2+ / total | >0.6 | Low = single-source reporting |
| Re-verification disagreement | disagreements in the RDA-32 sample / sample size | <0.05 | >0.10 invalidates the run; rerun with tighter shards |
| Tool-agreement rate | findings where tool and model agree / tool-flagged findings | reported, not targeted | Divergence is information, not error |
| External-validation load | count of EXTERNAL_VALIDATION_REQUIRED items | reported | This is the interview agenda; a low number on a system with no runtime access is a red flag |

## 5. Sampling doctrine for repositories that exceed budget

Order of preference: **EXHAUSTIVE** (deterministic tools only) > **RISK_WEIGHTED** (entry points, auth, money,
PII, crypto, IaC, CI, migration code) > **HOTSPOT** (change frequency x complexity from VCS history) >
**STRATIFIED_RANDOM** (seeded, for unbiased quality estimates) > **CONVENIENCE** (disclosed, C1 ceiling).

Rule: deterministic tools run over 100% of the corpus; the model reads only the risk-weighted and hotspot
strata. Never let the model's reading window define the population — the census defines it, the reading window
defines coverage, and the gap between them is the blind-spot list.
