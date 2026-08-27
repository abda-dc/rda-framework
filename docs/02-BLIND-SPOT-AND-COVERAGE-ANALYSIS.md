# Phase 1 — Meta-Analysis of the Enterprise Repository Audit Specification

**What is being analysed.** No prior internal repository-audit specification could be retrieved (Microsoft 365
file search is blocked by permissions in this tenant, and no such document exists in stored context). The
specification under review is therefore **the 37 mandatory domains in the brief**, treated as the current
enterprise audit spec. That is the honest reading, and it is stated here rather than assumed silently.

---

## 1. Strengths of the specification as written

1. **Domain coverage is genuinely broad and unusually well-chosen.** It reaches past the standard code-review
   perimeter into blast radius, knowledge silos, source-control health, known-unknown analysis and repository
   fidelity — dimensions that most commercial technical due diligence never touches.
2. **It separates executive from technical output** by naming an Executive CTO Assessment as its own domain.
   Most audit specifications treat the summary as a formatting step rather than a distinct artifact with its
   own rules.
3. **It anticipates its own failure modes.** Naming hallucination, context-window, incomplete-evidence,
   security-false-positive, false-dead-code and runtime-assumption risks up front is rare and correct; most
   specifications discover these in production.
4. **It is platform-agnostic by intent**, targeting ten execution environments, which forces a portable
   artifact rather than a tool-locked one.
5. **It demands confidence and evidence models**, not just findings — the right instinct, even though the
   specification does not say how to make them non-fictional.

---

## 2. Weaknesses of the specification as written

| # | Weakness | Why it matters | RDA's resolution |
|---|---|---|---|
| W1 | **A flat list of 37 domains with no dependency structure** | Domains are not peers. Threat modelling without entry points is fiction; blast radius without a dependency graph is guesswork | Six-layer DAG with hard ordering rules (ARCHITECTURE.md §3) |
| W2 | **No denominator concept** | "Assess code quality" over 400,000 files means nothing without stating what was inspected. This is the field-wide gap | RDA-02 census produces every denominator; coverage bands are mandatory next to every section heading |
| W3 | **Confidence is requested but not defined** | An undefined confidence field becomes a model-generated number, which is decoration — verbalised confidence separates right from wrong at roughly coin-flip AUROC | C0–C4 ladder awarded by countable evidence properties; numeric self-scores banned and linted |
| W4 | **No verification stage** | Every control is self-assessed. A model that both produces and checks a finding has checked nothing | RDA-32 blind re-derivation + mechanical citation re-resolution, with authority to invalidate a run |
| W5 | **No stop conditions** | An audit that finds a live credential or evidence of compromise must stop, not file it as a MEDIUM | ESC-1 escalation table with halt semantics |
| W6 | **No output contract** | Without a schema, governance is prose that models drift from under context pressure | `finding.schema.json` + two linters that fail closed |
| W7 | **No reproducibility model** | Findings asserted against a moving branch expire silently and cannot be re-checked | Commit pinning, run manifest, expiry, and run diffing as the refresh path |
| W8 | **Executive assessment is unconstrained** | The summary is where unsupported claims concentrate, because it is written last, under time pressure, from memory | Every executive sentence must resolve to a finding id; C2 floor; quarantined findings excluded by construction |
| W9 | **Cost optimisation invites fabrication** | "Cost" from source inspection has no ground truth. The closest competitor prices remediation at a flat $8,000/engineer-week regardless of market, seniority or geography | No currency without billing evidence; otherwise a labelled model with inputs and sensitivity, or nothing |
| W10 | **Ownership analysis has no ethical guardrail** | Contribution data trivially becomes individual performance evaluation, which is both unreliable and, in many jurisdictions, a legal exposure | RDA-29 reports concentration by role and component; individual evaluation is out of scope by construction |
| W11 | **No licence or IP domain** | The most common deal-breaker in software M&A is missing from a due-diligence specification | RDA-15 added |
| W12 | **No remediation sequencing** | A risk register is not a plan; without prerequisites and an accept-risk option it is a complaint | RDA-35 added |
| W13 | **Multi-repository is a stated requirement with no rollup domain** | Systemic risk is invisible one repository at a time | RDA-37 added |
| W14 | **"SRE Assessment" is undefined scope** | Produces essays. There is a real artifact — the production readiness review — with pass/fail semantics | Merged into RDA-23 as a gate |
| W15 | **No degradation model for missing tools** | An audit run without semgrep silently becomes a different, weaker audit | Tool availability recorded in the manifest at scope time; degradation declared, not discovered |

---

## 3. Blind Spot Assessment

Ranked by expected harm. Each has a named control.

### BS-1 · The confidence that survives its evidence *(critical)*
Findings are written once and then travel. The nuance ("in source, absent gateway configuration") is dropped at
each retelling until the executive summary says "the refund endpoint is unauthenticated". **Control:** BSR-08
caps summary-derived findings at C2 and forces re-reading at source before executive promotion; RP-1 requires
every executive sentence to carry a finding id.

### BS-2 · Verification theatre *(critical)*
A second pass that sees the first pass's conclusion agrees with it — this is the documented weakness of
chain-of-verification without independent answering. **Control:** BSR-05 — the verifier receives the claim's
*subject*, never its reasoning or conclusion, and a >10% disagreement rate invalidates the run.

### BS-3 · The denominator nobody states *(critical)*
The most common way an AI audit misleads is not a false statement but a true statement with an implied scope it
never earned. **Control:** BSR-07 — populations from the census, coverage bands beside every heading, and
prescribed language per band ("spot check only; findings are examples, not an inventory").

### BS-4 · Silent truncation *(high)*
A skill exhausts its budget, stops, and reports as though it finished. **Control:** manifest status
`ABORTED_BUDGET`; partial skills may not present conclusions, only leads.

### BS-5 · Dynamic-language unsoundness *(high)*
Reflection, dependency injection, string-keyed dispatch, cron entries, webhooks, serialisation targets and
feature flags all make static non-reference meaningless. **Control:** BSR-11 — non-reference is a *candidate*;
three output tiers; removal only at CONFIRMED-BY-RUNTIME behind staged deprecation.

### BS-6 · Fabricated-but-plausible identifiers *(high)*
Package, CVE and CWE names that do not exist. Measured at ~5–22% for package names depending on model class,
with **43% of fabrications stable across re-runs** — meaning self-consistency will not catch them.
**Control:** existence-check every named external artifact against an authoritative registry.

### BS-7 · Intent mistaken for state *(high)*
Terraform declares intent. The cloud account holds state. Encryption, residency, IAM breadth and replica counts
read from IaC describe what someone wrote, not what is running. **Control:** RDA-20's hard rule and the ES-1
class ceilings; "data is stored in region R" is capped at HYPOTHESIS.

### BS-8 · The CVE flood *(high)*
Four hundred transitive advisories reported as four hundred risks destroys the register's signal.
**Control:** RDA-13's mandatory present/reachable/exploitable split, reported as three counts, never collapsed.

### BS-9 · Ownership inference becoming personnel judgement *(high — non-technical)*
The step from "78% of commits" to "Jane is a risk" is one sentence, and it is the sentence that gets the audit
rejected. **Control:** BSR-09 — role and component only.

### BS-10 · The plausible architecture diagram *(medium)*
Service graphs drawn from folder names look authoritative and are frequently wrong. **Control:** every edge
requires a call site, a config value or a manifest entry; folder-derived edges are HYPOTHESIS.

### BS-11 · Prompt injection through repository contents *(medium, under-appreciated)*
The audit reads untrusted text: READMEs, comments, test fixtures, dependency metadata, issue templates. A
repository can contain instructions aimed at the auditing agent. Note that the best-known open security-review
skill in this space carries an explicit warning that it is *"not hardened against prompt injection"* and
*"should only be used to review trusted PRs"*. **Control:** repository content is data, never instruction;
findings must derive from cited artifacts, and instruction-shaped content encountered in the corpus is itself
reportable as a finding.

### BS-12 · Order-dependence of the analysis *(medium)*
Concatenation and shard order measurably change model output. An audit that is not order-deterministic is not
reproducible even at the finding-set level. **Control:** deterministic sorted shard order with recorded seed.

### BS-13 · Evidence staleness *(medium)*
The branch moves during a two-week engagement. **Control:** commit pinning, per-finding expiry, and re-running
the deterministic layer against the new commit to produce a diff rather than a fresh audit.

### BS-14 · Benchmark-shaped competence *(medium)*
Models identify plausible file paths without repository access, so fluency about a codebase is not evidence of
having read it. **Control:** BSR-02 — every path confirmed by a filesystem call and every quote hash-checked.

### BS-15 · The zero-unknowns report *(medium)*
Models almost never abstain unprompted (measured spontaneous refusal ~0.035%), so a complete-looking report is
evidence of assertion, not of completeness. **Control:** abstention is an engineered output and the unknown
rate is a monitored metric; zero unknowns triggers a linter warning.

---

## 4. Coverage Assessment of the original 37 domains

| Verdict | Count | Domains |
|---|---|---|
| **Well specified, kept as-is** | 21 | Repository mapping, entry points, API, cross-service, data layer, configuration, security, threat modelling, secret flow, dependency audit, testing, CI/CD, infrastructure, observability, performance, code quality, source-control health, risk assessment, compliance, supply chain, data governance |
| **Specified but under-defined — needed a concrete artifact** | 6 | SRE assessment (→ PRR gate), operational readiness, cost optimisation (→ labelled model), technical debt (→ bands, not currency), business logic discovery (→ enforcement points), repository fidelity (→ claim-by-claim verdicts) |
| **Specified but ethically/legally unguarded** | 2 | Ownership analysis, knowledge-silo analysis |
| **Correctly identified as risky but with no control attached** | 3 | Blast radius, resilience, known-unknown analysis |
| **Merged (redundant traversal of the same evidence)** | 6 pairs | See ARCHITECTURE.md §2 |
| **Missing entirely** | 5 | Licence & IP · evidence verification · remediation roadmap · portfolio rollup · the evidence kernel itself |

**Coverage verdict:** the specification is approximately **86% complete on breadth** and approximately
**20% complete on assurance**. It knows what to look at; it does not say how to be believed. That asymmetry is
the whole design problem, and it is where RDA adds value rather than duplicating the field.

---

## 5. Missing Skill Assessment — the five additions and why they are not optional

| Added | Justification | Cost of omitting it |
|---|---|---|
| **RDA-00 audit-core** | The contract must be always-on and identical across 38 skills, or each skill drifts into its own standard of proof | Governance becomes advisory prose that models discard under context pressure |
| **RDA-15 licence-ip-review** | Copyleft contamination and unclear IP provenance are the classic deal-breakers; manifest-only scanning misses vendored and copy-pasted code, which is exactly where the exposure lives | A clean security report next to an unshippable licence position |
| **RDA-32 evidence-verifier** | Without an independent adversarial pass, every control in the framework is self-graded | The failure documented publicly by the curl maintainers: plausible reports, ~5% validity, reviewer attention destroyed |
| **RDA-35 remediation-roadmap** | Sequencing, prerequisites and an explicit accept-risk option are what make a register actionable | The audit is received as criticism and shelved |
| **RDA-37 portfolio-rollup** | The brief's own premise includes multi-repository systems; systemic risk is invisible per repo | Twelve reports, no decision — and the shared component that breaks everything is never named |

**Two capabilities deliberately *not* added**, with reasons, because a good architecture is also a list of
refusals:
- **Automated remediation / PR generation.** Different risk profile, different approval path, and it corrupts
  the auditor's independence. RDA recommends; it does not modify.
- **Individual performance analytics.** Technically trivial from the same git data, and excluded on purpose.

---

## 6. Failure-mode catalogue with controls

| Failure mode | Trigger | Control |
|---|---|---|
| Confident architecture diagram from folder names | No call-site evidence required | Edge evidence rule (BSR-01/07) |
| Phantom endpoint from a guessed framework idiom | Model pattern-matching | Citation re-resolution (BSR-02) |
| Unauthenticated-endpoint scare | Auth enforced elsewhere and never checked | Disconfirming search (BSR-06) |
| Dead-code deletion incident | Static non-reference treated as proof | Reachability gate (BSR-11) |
| Savings-slide fabrication | Cost inferred from instance types | Estimate labelling (BSR-10) |
| Compliance green tick | Control evidence read as certification | Undecidable register (BSR-03) |
| CVE flood | Presence conflated with risk | Three-count split (RS-1 §2) |
| Bus-factor accusation | Concentration read as competence | No-name attribution (BSR-09) |
| Stale truth | Branch moved mid-engagement | Manifest + expiry (BSR-12) |
| Silent skip | Budget exhausted quietly | `ABORTED_BUDGET` + blind spot |
| Agreeable second opinion | Verifier saw the draft | Blind re-derivation (BSR-05) |
| One-file generalisation | Sample scope exceeded in the claim | Denominator discipline (BSR-07) |
| Injected instruction from repo content | Untrusted corpus treated as instruction | Content-is-data rule (BS-11) |
| Verdict flip under renaming | Model non-robustness to trivial perturbation | Perturbation stability check (RDA-32 pass c) |

---

## 7. What remains uncontrolled even after all 38 skills

Stated plainly, because an assurance framework that claims completeness has failed its own first test.

1. **Semantic correctness of business logic.** RDA can show that a discount rule exists at a cited line and
   that it is enforced in one place rather than three. It cannot know that the rule is the *right* rule. Only
   the business owner can, and RDA-34 turns that into a question rather than a silence.
2. **Runtime and production reality.** Everything about deployment, load, cost, incidents and data residency is
   outside source by construction. RDA converts these into an external-validation agenda; it does not close them.
3. **Deliberate concealment.** A repository curated for a diligence process — history rewritten, a branch
   presented as trunk, a service excluded from the data room — defeats source-based analysis. Only cross-checks
   against runtime, invoices and org evidence catch it, and RDA-31 can only flag inconsistency, not intent.
4. **Adversarial supply chain.** A malicious dependency that is signed, popular and behaviourally benign at
   inspection time will pass. Provenance raises the bar; it does not eliminate the class.
5. **The model itself.** RDA constrains what a model may claim; it cannot make a model competent. A model that
   fails to notice a vulnerability produces a clean report with honest coverage numbers — and the coverage
   numbers are the only defence, because they tell the reader how much silence to trust.
6. **Interpretive reproducibility.** The deterministic layer reproduces byte-for-byte. The interpretive layer
   does not, and claiming otherwise would be its own unsupported claim; it is reproducible only at the level of
   the finding set, and that is what the verification statistics measure.
7. **Organisational truth.** Whether the team can execute the roadmap, whether the architect is leaving, whether
   the roadmap is funded — all decisive, none in the repository.
