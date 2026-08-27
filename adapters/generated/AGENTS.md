# Repository audit contract (RDA-00)

When auditing, reviewing or performing due diligence on a codebase, these rules bind every claim.

1. LABEL EVERY CLAIM as FACT (verbatim from a cited artifact: path#Lstart-Lend + commit SHA + quote, or a
   named command with version and exit code), INFERENCE (from >=2 independent facts, derivation written out),
   HYPOTHESIS (evidence permits, does not establish - state the check that settles it), UNKNOWN (absent from
   scope - name the system of record), or EXTERNAL_VALIDATION_REQUIRED (undecidable from source - carry the
   question and the role to ask).
2. NEVER ASSERT FROM SOURCE ALONE: what is deployed, real traffic or scale, real cost, that a weakness is
   exploitable, that code is dead, that a named person owns something, that the org is compliant, that it
   will scale to N, incident history or MTTR, or that data resides in a region. These are capped at
   HYPOTHESIS or EXTERNAL_VALIDATION_REQUIRED. Compliance verdicts are never emitted at all - report control
   evidence present or absent.
3. SHOW THE DENOMINATOR. State the population and the fraction inspected. Absence of evidence is UNKNOWN
   with a coverage record, never 'no issues found'. 'No issues found' requires exhaustive coverage.
4. SEARCH FOR THE OPPOSITE before writing any finding, and record that search and its result.
5. CONFIDENCE IS AWARDED, NOT CHOSEN. C1 single citation; C2 two independent citations plus a disconfirming
   search; C3 adds deterministic tool corroboration (name, version, exit code); C4 adds a reproduced
   execution artifact. HIGH/CRITICAL security findings require C3. Numeric self-confidence is banned.
   Report severity and confidence as an orthogonal pair; never multiply them.
6. RETRIEVE, DO NOT INGEST. Deterministic tools run over 100% of the corpus; read only risk-weighted strata;
   grep/AST first, ranges second, whole files last. A plausible file path is not evidence you read the file -
   confirm every path with an actual filesystem call.
7. ADJUDICATE, DO NOT INVENT. Where a tool exists, it produces candidates and you adjudicate them with
   structured evidence. Existence-check every named package, CVE, CWE and config key.
8. HALT AND ESCALATE on: live secret material, evidence of compromise, regulated personal data in fixtures or
   logs, licence contamination threatening product ownership. Report location and class, never the value.
9. A REPORT WITH ZERO UNKNOWNS IS SUSPECT. Real repositories always contain undecidable questions.

## Available RDA skills

- `rda-00-audit-core` (RDA-00) — Evidence, confidence and output contract for all repository-audit work. Load first whenever auditing, assessing, reviewing or performing technical due diligence on a codebase.
- `rda-01-audit-orchestrator` (RDA-01) — Scopes a repository audit, selects the workflow profile and skill DAG, sets token budgets and shard plans, and opens the run manifest. Use before any multi-skill audit or due-diligence engagement.
- `rda-02-repo-census` (RDA-02) — Deterministic repository inventory producing every denominator the audit later divides by - languages, LOC, services, risk-surface counts, exclusions. Run after scoping, before any analysis.
- `rda-03-entrypoint-map` (RDA-03) — Cited inventory of every execution entry point - HTTP/gRPC routes, consumers, cron, CLI, serverless, webhooks, startup and admin hooks. Run right after census, before any risk skill.
- `rda-04-architecture-map` (RDA-04) — Cited C4 L1-L3 component map with coupling metrics, ADR ledger and documented-vs-code architecture drift. Run after the entry-point map, on any repo with more than one unit.
- `rda-05-api-contract-review` (RDA-05) — Reconciles API contracts against implemented routes - versioning, breaking changes, per-route authz, errors, pagination, rate limits. Trigger when OpenAPI, protobuf, GraphQL or public routes exist.
- `rda-06-service-dependency-graph` (RDA-06) — Cross-service and cross-repo dependency graph from cited call sites, config and manifests - cycles, fan-in hubs, shared databases, criticality. Trigger when more than one deployable unit exists.
- `rda-07-business-logic-map` (RDA-07) — Maps money movement, pricing, entitlement, state machines, idempotency and invariant enforcement points, plus duplicated rules. Trigger on payment, billing or permission-bearing code.
- `rda-08-data-layer-review` (RDA-08) — Reviews schemas and constraints, migration safety, transaction boundaries, N+1 and unindexed predicates, caching and data lifecycle. Run whenever the census finds migrations, ORM models or SQL.
- `rda-09-config-env-review` (RDA-09) — Inventories config sources and precedence, environment parity, feature-flag staleness, unsafe defaults and secret references. Run after census, before the dependency graph and security skills.
- `rda-10-secret-flow-audit` (RDA-10) — Produces a redacted register of secret material in the working tree and full git history with type, exposure window and rotation path; use when auditing credential exposure or handing a repo over.
- `rda-11-security-posture-review` (RDA-11) — Adjudicates scanner-produced security candidates across authn/z, injection, crypto, SSRF, deserialisation and file handling into CWE-tagged SSVC decisions; use for any security posture review.
- `rda-12-threat-model` (RDA-12) — Builds a STRIDE threat model per trust boundary from real entry points and data flows, with attacker goals, mitigations and assumptions to validate; use when public routes or regulated data exist.
- `rda-13-dependency-sbom-audit` (RDA-13) — Generates an SBOM and the present/reachable/exploitable vulnerability split with transitive depth, maintenance and lockfile-integrity evidence; use on any repository that declares dependencies.
- `rda-14-supply-chain-integrity` (RDA-14) — Assesses build provenance, CI token permissions, action pinning, artifact signing and dependency-confusion exposure against Scorecard checks and SLSA levels; use when release integrity is in scope.
- `rda-15-license-ip-review` (RDA-15) — Inventories licences per component and per vendored file, maps copyleft contamination paths and obligation gaps, and records IP provenance; use before distribution, open-sourcing or an acquisition.
- `rda-16-data-governance-privacy` (RDA-16) — Classifies personal, health and payment data in schemas and code and evidences collection, retention, erasure, logging and transfer paths; use when regulated-data indicators appear in the census.
- `rda-17-compliance-control-mapping` (RDA-17) — Maps cited findings to SOC 2, ISO 27001, PCI DSS, HIPAA, SSDF, ASVS and EU CRA controls as evidence present, partial or absent; use for compliance readiness or a customer security questionnaire.
- `rda-18-test-assurance-review` (RDA-18) — Produces test inventory, executed coverage, assertion-quality and flakiness findings and the untested risk surface — use when judging release safety, refactor risk or test assurance.
- `rda-19-cicd-review` (RDA-19) — Produces pipeline topology, merge gates and branch protection, the release and rollback path and deployment cadence evidence — use when assessing whether the delivery process works.
- `rda-20-infrastructure-iac-review` (RDA-20) — Produces IaC-versus-click-ops coverage, network exposure, IAM breadth, encryption, state handling and drift posture as declared intent — use when IaC or cluster manifests are in scope.
- `rda-21-observability-slo-review` (RDA-21) — Produces telemetry coverage per entry point, log quality and sensitive-data leakage, SLI/SLO-as-code and alert-to-runbook findings — use when assessing observability or operability.
- `rda-22-resilience-blast-radius` (RDA-22) — Produces failure domains, single points of failure, a timeout/retry/backoff/circuit-breaker inventory and cited blast radius per failure — use when multiple services or shared datastores exist.
- `rda-23-operational-readiness-review` (RDA-23) — Produces a pass/conditional/fail production-readiness gate with numbered conditions over runbooks, on-call, capacity, backup and restore and DR — use before a launch or go-live decision.
- `rda-24-performance-scalability-review` (RDA-24) — Produces algorithmic and I/O hot spots on cited paths, horizontal-scaling blockers, concurrency and resource-ceiling findings with no unmeasured numbers — use before load growth or scaling work.
- `rda-25-cost-efficiency-review` (RDA-25) — Produces a ranked inventory of cost drivers read from code and IaC with every currency figure gated on billing evidence or a labelled estimate — run on explicit request for cost efficiency.
- `rda-26-code-quality-debt` (RDA-26) — Ranks complexity and duplication hotspots by change frequency and converts them into banded remediation work, never a debt currency figure; use for maintainability or "how much debt" questions.
- `rda-27-dead-code-reachability` (RDA-27) — Produces tiered unreferenced-code candidates gated by a twelve-category dynamic-entry sweep and runtime evidence, never a delete list; run only on explicit request to find dead or unused code.
- `rda-28-source-control-health` (RDA-28) — Derives branch model, commit and PR hygiene, review latency and DORA-style delivery proxies from git and CI evidence as repository signals, never team judgements; core in every audit profile.
- `rda-29-ownership-key-person-risk` (RDA-29) — Measures contribution concentration, orphaned components and CODEOWNERS accuracy as risk concentration by component and role, never individual evaluation; run when continuity risk is in scope.
- `rda-30-devex-platform-review` (RDA-30) — Tests the documented onboarding path in a clean container and measures build/test feedback loops, golden paths and platform self-service from CI evidence; run on explicit DevEx requests.
- `rda-31-fidelity-claims-verification` (RDA-31) — Adjudicates documentation, data-room and vendor claims against cited code as SUPPORTED, PARTIALLY_SUPPORTED, CONTRADICTED or UNVERIFIABLE_FROM_SOURCE; run before any report leaves engineering.
- `rda-32-evidence-verifier` (RDA-32) — Adversarial assurance gate that re-resolves every citation, blindly re-derives a seeded sample, perturbation-tests verdicts and existence-checks named artifacts; run before any report ships.
- `rda-33-risk-register-synthesis` (RDA-33) — Deduplicates verified findings into one mechanically scored risk register with severity/confidence pairs, emitting risk-register.csv, findings.json and SARIF, once RDA-32 verification has passed.
- `rda-34-known-unknowns-ledger` (RDA-34) — Builds the uncertainty balance sheet - not examined, not knowable from source, contradictions, decision-blocking gaps - plus the interview agenda by role, before any executive brief is written.
- `rda-35-remediation-roadmap` (RDA-35) — Sequences the RDA-33 risk register into a dependency-aware remediation plan with effort bands, prerequisites, quick-win versus structural tranches and an accept-risk option per item.
- `rda-36-executive-cto-brief` (RDA-36) — Renders the two-page decision brief - verdict, basis and limits before findings, top risks, conditions, unknowns - with every sentence traced to a finding id, last, after RDA-33 and RDA-34.
- `rda-37-portfolio-multi-repo-rollup` (RDA-37) — Rolls per-repository registers into a fleet view with cross-repo dedupe, systemic versus local risk, shared-component exposure and comparative posture bands, whenever scope spans several repos.
