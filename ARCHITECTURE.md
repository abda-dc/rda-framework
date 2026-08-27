# RDA Architecture — decisions, DAG, and why the shape is what it is

## 1. The three design decisions everything else follows from

**D1. The audit is a retrieval-and-verification pipeline, not a reading exercise.** A 100k-file repository is
orders of magnitude larger than any context window; effective context collapses well before advertised limits;
accuracy degrades with input length even when task difficulty is held constant; and audit questions have low
lexical overlap with the code that answers them. Therefore deterministic tools run over 100% of the corpus and
the model reads only risk-weighted strata — and every skill is built around that split.

**D2. Evidence is a data structure, not a writing style.** Findings are schema-validated records with locators,
quotes, hashes and coverage references. This is what makes verification mechanical instead of aspirational: a
citation either re-resolves at the pinned commit or the finding is quarantined.

**D3. Adjudication beats generation.** Where a deterministic tool exists (SAST, SBOM, licence, coverage, AST,
git), the tool produces candidates and the model adjudicates them with structured evidence. Freehand discovery
is reserved for the places no tool covers — business logic, architecture drift, operational readiness — and is
held to the strictest class ceilings precisely because nothing can corroborate it.

## 2. Merge and split decisions (and the reasoning)

| Decision | Domains | Rationale |
|---|---|---|
| **MERGE** | Architecture Analysis + Architecture Decision Review -> `RDA-04` | Same evidence set (docs, ADRs, module graph); drift is only measurable when intent and implementation are read together. Splitting forces two traversals of the same corpus for one judgement |
| **MERGE** | Blast Radius + Resilience Modelling -> `RDA-22` | One failure-domain model. Blast radius is its static half, resilience its dynamic half; separating them produces two half-answers that must be manually recombined |
| **MERGE** | SRE Assessment + Operational Readiness -> `RDA-23` | "SRE assessment" has no artifact; the production readiness review does. Merging replaces a vague scope with a gate that passes or fails |
| **MERGE** | Code Quality + Technical Debt -> `RDA-26` | Debt is the interpretation layer over quality metrics. Two skills means two runs of the same expensive metric pass over the same files |
| **MERGE** | Ownership + Knowledge Silo -> `RDA-29` | Both derive from the same blame/CODEOWNERS evidence, and both carry the same ethical constraint. One skill, one guardrail |
| **MERGE** | Platform Engineering + Developer Experience -> `RDA-30` | Same evidence (build times, onboarding path, golden paths, self-service). DX is the outcome, platform is the mechanism |
| **SPLIT** | Dead code out of Code Quality -> `RDA-27` | A wrong dead-code finding causes an outage. It needs its own reachability gate, its own output tiers and its own risk class. Burying it inside a LOW_HARM quality skill would let a HIGH_HARM claim inherit a low verification bar |
| **SPLIT** | Kernel out of orchestration -> `RDA-00` / `RDA-01` | The evidence contract must be always-on in every environment (as a rule), while planning runs once per engagement (as a skill). One artifact cannot be both |
| **SPLIT** | Supply chain out of Dependency Audit -> `RDA-13` / `RDA-14` | Different evidence, different tools, different owner. "Which components have CVEs" and "can our build be subverted" share only the word *dependency* |
| **SPLIT** | Data governance out of Data Layer -> `RDA-08` / `RDA-16` | Different reviewers (engineering vs privacy), different regulators, different escalation path |
| **NEW** | `RDA-15` Licence & IP | Absent from the brief and the single most common deal-breaker in software M&A. Copyleft contamination and unclear IP provenance kill transactions that no security finding would have stopped |
| **NEW** | `RDA-32` Evidence Verifier | Absent from the brief. Without an independent adversarial pass, every other control is self-assessed — and a verifier that sees the draft inherits the draft's errors, so it must re-derive blind |
| **NEW** | `RDA-35` Remediation Roadmap | Absent from the brief. A risk register without sequencing, prerequisites and an accept-risk option is a complaint, not a plan |
| **NEW** | `RDA-37` Portfolio Rollup | Absent from the brief, required by its own premise — "multi-repository systems" cannot be served by per-repo reports alone; systemic risk is invisible one repo at a time |
| **KEEP SEPARATE** | Entry points vs API review | Entry points is a census of all execution starts (including cron, queues, webhooks); API review is contract quality on the subset that is an API. Merging loses the non-API entry points, which is where the ugly surprises live |
| **KEEP SEPARATE** | Security posture vs Threat model | One adjudicates concrete weaknesses, the other reasons about attacker goals against boundaries. Merging reliably produces a list of findings with a STRIDE table stapled to it |

## 3. Execution DAG

```
                          RDA-00 audit-core  (always-on rule, not a stage)
                                   |
                          RDA-01 audit-orchestrator
                                   |
                          RDA-02 repo-census
                                   |
        +--------------------------+--------------------------+
        |                          |                          |
   GROUP A (structure)        GROUP B (risk)            GROUP C (ops/health)
   parallel, needs census     needs A partially         needs census + A
        |                          |                          |
   RDA-03 entrypoint-map ------> RDA-11 security-posture   RDA-18 test-assurance
   RDA-08 data-layer  ---------> RDA-12 threat-model       RDA-19 cicd
   RDA-09 config-env  ---------> RDA-10 secret-flow        RDA-26 code-quality-debt
        |                        RDA-13 dependency-sbom    RDA-28 source-control
   RDA-04 architecture-map       RDA-16 data-governance    RDA-30 devex-platform
   RDA-05 api-contract                |                          |
   RDA-06 service-graph          RDA-14 supply-chain        RDA-20 infra-iac
   RDA-07 business-logic         RDA-15 licence-ip         RDA-21 observability
        |                        RDA-17 compliance-map     RDA-22 resilience
        |                                                  RDA-23 op-readiness
        |                                                  RDA-24 performance
        |                                                  RDA-25 cost
        |                                                  RDA-27 dead-code
        |                                                  RDA-29 ownership
        +--------------------------+--------------------------+
                                   |
                          RDA-31 fidelity-claims
                                   |
                          RDA-32 evidence-verifier   <-- gate: >10% disagreement invalidates the run
                                   |
                          RDA-33 risk-register
                                   |
                    +--------------+--------------+
                    |              |              |
              RDA-34 unknowns  RDA-35 roadmap  RDA-37 portfolio (multi-repo only)
                    +--------------+--------------+
                                   |
                          RDA-36 executive-cto-brief
```

**Hard ordering rules**
1. Nothing runs before RDA-02 — without denominators, no coverage claim is possible.
2. RDA-11/12 must not start before RDA-03 completes: a security review that has not enumerated entry points is
   reviewing an imagined attack surface.
3. RDA-22 must not start before RDA-06: blast-radius claims without a cited dependency graph are HYPOTHESIS.
4. RDA-32 runs **after everything and before anything is published**. It is the only gate that can invalidate
   a run, and it is the last budget line to cut, never the first.
5. RDA-36 consumes only the verified register. It never reads source directly — an executive brief that
   re-derives its own facts has escaped the traceability chain.

**Parallelism.** Groups A, B and C parallelise within themselves. Group B's dependency on A is partial:
RDA-10 and RDA-13 need only the census and can start immediately, which is why they are the right first
security work on a large repository — they are cheap, deterministic, and produce escalations early.

## 4. Cost/value tiering

| Value | Cost | Skills |
|---|---|---|
| **High value, low cost** (always run) | deterministic, minutes | RDA-02, RDA-10, RDA-13, RDA-28, RDA-19 |
| **High value, high cost** | model-heavy, needs sampling | RDA-03, RDA-07, RDA-11, RDA-22, RDA-31, RDA-32 |
| **Situational value** | depends on the decision | RDA-16, RDA-17, RDA-15, RDA-23, RDA-37 |
| **Low value unless asked** | expensive or fragile | RDA-25 (needs billing data), RDA-27 (high harm), RDA-30 (rarely decision-relevant) |
