# RDA Skill Catalog v1.0 — 38 skills

`Core` = the default tier: included unless a profile deliberately narrows scope (P1, P5, P6 and P7 each drop
Core skills outside their question — see `workflows/PROFILES.md` for the per-profile set and rationale).
`Cond` = activated by trigger conditions. `Opt` = on request.
`Risk class` = harm if **this skill is wrong**, which drives its verification burden — not the risk it measures.

## Layer 0 — Kernel (3) — always first, strictly sequential

| ID | Skill | Tier | Risk | Purpose (one line) | Depends on |
|---|---|---|---|---|---|
| RDA-00 | `audit-core` | Core | HIGH | The evidence grammar, class ceilings, confidence ladder and output contract every other skill inherits; loaded as an always-on rule, never run alone | — |
| RDA-01 | `audit-orchestrator` | Core | HIGH | Scopes the engagement, picks the profile and DAG, sets token budgets and shard plan, opens the run manifest, enforces resumability | RDA-00 |
| RDA-02 | `repo-census` | Core | HIGH | Deterministic inventory: repos, commits, languages, LOC, build systems, monorepo topology, generated/vendored exclusions — produces every denominator the framework later divides by | RDA-01 |

## Layer 1 — Structure (7) — parallel group A, after census

| ID | Skill | Tier | Risk | Purpose | Depends on |
|---|---|---|---|---|---|
| RDA-03 | `entrypoint-map` | Core | HIGH | Enumerate every way execution starts: HTTP routes, gRPC, queues, cron, CLI, lambdas, webhooks, init hooks, scheduled jobs, admin backdoors | RDA-02 |
| RDA-04 | `architecture-map` | Core | MEDIUM | Component/service topology, layering, coupling, patterns, ADR review and **architecture drift** (documented intent vs cited code) | RDA-02, RDA-03 |
| RDA-05 | `api-contract-review` | Cond | MEDIUM | Public/internal API surface: contracts, versioning, breaking-change exposure, authn/z per route, error and pagination semantics, deprecation | RDA-03 |
| RDA-06 | `service-dependency-graph` | Cond | HIGH | Cross-service and cross-repo call/data edges, sync vs async, cycles, fan-in hubs, shared-database coupling | RDA-03, RDA-09 |
| RDA-07 | `business-logic-map` | Cond | HIGH | The domain rules that actually make money: money movement, entitlement, pricing, state machines, idempotency, where invariants are enforced | RDA-03, RDA-08 |
| RDA-08 | `data-layer-review` | Core | MEDIUM | Schemas, migrations, ORM usage, transactions/isolation, N+1 and hot-path queries, indexing, caching, data lifecycle in code | RDA-02 |
| RDA-09 | `config-env-review` | Core | MEDIUM | Configuration inventory and precedence, environment parity, feature flags, unsafe defaults, config-as-attack-surface | RDA-02 |

## Layer 2 — Risk & Security (8) — parallel group B

| ID | Skill | Tier | Risk | Purpose | Depends on |
|---|---|---|---|---|---|
| RDA-10 | `secret-flow-audit` | Core | HIGH | Secret detection in tree **and history**, provenance/rotation path, propagation into logs and CI, immediate-escalation handling | RDA-02, RDA-09 |
| RDA-11 | `security-posture-review` | Core | HIGH | Adjudicates scanner candidates and targeted reads across authn/z, injection, crypto, SSRF, deserialisation, file handling — **adjudication over evidence, never freehand vulnerability invention** | RDA-03, RDA-09 |
| RDA-12 | `threat-model` | Cond | MEDIUM | STRIDE per trust boundary derived from real entry points and data flows, with attacker goals and existing mitigations cited | RDA-03, RDA-06, RDA-08 |
| RDA-13 | `dependency-sbom-audit` | Core | HIGH | SBOM generation, vulnerability match, **present/reachable/exploitable split**, transitive depth, maintenance and abandonment signals | RDA-02 |
| RDA-14 | `supply-chain-integrity` | Cond | HIGH | Build provenance, CI token and permission model, artifact signing, pinning, dependency confusion/typosquat exposure, SLSA-style posture | RDA-13, RDA-19 |
| RDA-15 | `license-ip-review` | **NEW** Cond | HIGH | Licence inventory, copyleft contamination paths, obligation compliance, IP provenance including AI-generated and vendored code | RDA-13 |
| RDA-16 | `data-governance-privacy` | Cond | HIGH | PII/PHI/PCI classification in schemas and code, residency intent, retention, deletion/erasure paths, logging of sensitive fields, lineage | RDA-08 |
| RDA-17 | `compliance-control-mapping` | Cond | HIGH | Maps cited evidence to control frameworks; emits *control evidence present/absent*, **never a compliance verdict** | RDA-11, RDA-16, RDA-19 |

## Layer 3 — Engineering & Operations (8) — parallel group C

| ID | Skill | Tier | Risk | Purpose | Depends on |
|---|---|---|---|---|---|
| RDA-18 | `test-assurance-review` | Core | MEDIUM | Test inventory and pyramid shape, real coverage vs claimed, assertion quality, flakiness signals, what is untested on the risk surface | RDA-02, RDA-07 |
| RDA-19 | `cicd-review` | Core | MEDIUM | Pipeline topology, gates, branch protection, release path, rollback, environment promotion, deployment cadence evidence | RDA-02 |
| RDA-20 | `infrastructure-iac-review` | Cond | MEDIUM | IaC coverage vs click-ops, network exposure, IAM breadth, encryption, state handling, drift-detection posture | RDA-09, RDA-19 |
| RDA-21 | `observability-slo-review` | Core | MEDIUM | Telemetry coverage on critical paths, log quality and sensitive-data leakage, SLI/SLO definitions, alert-to-runbook linkage | RDA-03, RDA-07 |
| RDA-22 | `resilience-blast-radius` | Cond | HIGH | Failure domains, single points of failure, dependency criticality, timeout/retry/circuit-breaker inventory, and what each failure takes down | RDA-06, RDA-20 |
| RDA-23 | `operational-readiness-review` | Cond | MEDIUM | Production-readiness gate: runbooks, on-call, capacity, backup **and restore evidence**, DR, graceful degradation, launch/exit criteria | RDA-21, RDA-22, RDA-19 |
| RDA-24 | `performance-scalability-review` | Cond | HIGH | Algorithmic and I/O hot spots, statefulness and scaling limits, concurrency model, resource ceilings — never asserts throughput without artifacts | RDA-07, RDA-08 |
| RDA-25 | `cost-efficiency-review` | Opt | HIGH | Cost *drivers* from code and IaC; produces a labelled model with inputs and sensitivity, never a dollar claim without billing evidence | RDA-20, RDA-24 |

## Layer 4 — Codebase & Organisational Health (5) — parallel group C

| ID | Skill | Tier | Risk | Purpose | Depends on |
|---|---|---|---|---|---|
| RDA-26 | `code-quality-debt` | Core | LOW | Structural quality, complexity and duplication hotspots, and the debt interpretation layer with remediation bands | RDA-02 |
| RDA-27 | `dead-code-reachability` | Opt | **HIGH** | Unreferenced-code *candidates* only, gated by dynamic-entry sweep and runtime evidence before any removal is suggested | RDA-03, RDA-26 |
| RDA-28 | `source-control-health` | Core | LOW | Branch model, commit and PR hygiene, review latency and depth, merge patterns, repo hygiene (large files, secrets in history, submodules) | RDA-02 |
| RDA-29 | `ownership-key-person-risk` | Cond | **HIGH** | Contribution concentration, orphaned components, CODEOWNERS accuracy, knowledge silos — expressed as **risk concentration by role**, never individual evaluation | RDA-28 |
| RDA-30 | `devex-platform-review` | Opt | LOW | Onboarding path and time-to-first-commit evidence, local setup, build/test feedback loops, golden paths, internal platform and self-service maturity | RDA-19, RDA-26 |

## Layer 5 — Assurance & Synthesis (7) — sequential, last

| ID | Skill | Tier | Risk | Purpose | Depends on |
|---|---|---|---|---|---|
| RDA-31 | `fidelity-claims-verification` | Cond | HIGH | Tests documented/vendor claims against cited code — README, architecture docs, ADRs, data-room assertions, marketing capability claims | all L1-L4 |
| RDA-32 | `evidence-verifier` | **NEW** Core | HIGH | Blind adversarial re-derivation of a stratified sample of findings in a **fresh context**, plus citation re-resolution and identifier-perturbation stability checks; can invalidate the run | all |
| RDA-33 | `risk-register-synthesis` | Core | MEDIUM | Deduplicates, scores and sequences the verified finding set into one register with severity/confidence pairs and blast radius | RDA-32 |
| RDA-34 | `known-unknowns-ledger` | Core | MEDIUM | The uncertainty balance sheet: what was not examined, what cannot be known from source, what to ask whom, and which decisions are blocked by each gap | all |
| RDA-35 | `remediation-roadmap` | **NEW** Cond | MEDIUM | Sequenced, dependency-aware remediation plan in effort bands with prerequisites and quick-win/structural split | RDA-33 |
| RDA-36 | `executive-cto-brief` | Core | HIGH | The 2-page decision artifact: verdict, basis and limits, top risks, conditions, unknowns — every sentence traceable to a finding id | RDA-33, RDA-34 |
| RDA-37 | `portfolio-multi-repo-rollup` | **NEW** Cond | MEDIUM | Fleet-level rollup across many repositories: cross-repo dedupe, systemic vs local risk, comparative posture, shared-component exposure | RDA-33 (per repo) |

## Tier summary

- **Core (19):** RDA-00, 01, 02, 03, 04, 08, 09, 10, 11, 13, 18, 19, 21, 26, 28, 32, 33, 34, 36 — the minimum
  defensible audit, and the set P2, P3 and P4 run in full. The kernel and synthesis spine (RDA-00, 01, 02, 32,
  33, 34, 36) is present in **every** profile; the remaining Core skills are dropped only where a profile's
  question does not reach them (e.g. P5 security omits RDA-26 code quality).
- **Conditional (16):** RDA-05, 06, 07, 12, 14, 15, 16, 17, 20, 22, 23, 24, 29, 31, 35, 37 — activated by trigger conditions in `workflows/` (e.g. RDA-06 only when >1 deployable unit; RDA-16 only when regulated-data indicators appear in the census; RDA-37 only for multi-repo scope).
- **Optional (3):** RDA-25, RDA-27, RDA-30 — high cost or high harm relative to typical value; run on explicit request.
- **New beyond the original 37 domains (5):** RDA-15 licence/IP, RDA-32 evidence verifier, RDA-35 remediation roadmap, RDA-37 portfolio rollup, and the RDA-00/RDA-01 kernel split.
