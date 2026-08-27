# Phase 8 — Final CTO Recommendation

**Recommendation: BUILD, narrowly and immediately.** Build the evidence kernel, the coverage model and the
verification gate. Buy or vendor everything that is a scanner. Cite, do not reinvent, every standard. The
defensible product is not "an AI that reviews code" — that market is crowded and consolidating — it is **an
audit whose claims survive being checked**.

---

## 1. What is the optimal number of skills?

**38 in the catalogue; 19 in the default core; 12–36 activated per engagement.**

The number is an output of three constraints, not a target:

| Constraint | Effect |
|---|---|
| **Evidence isolation** | Skills whose wrong answers cause different kinds of harm need different verification burdens. Dead-code detection cannot inherit a code-quality skill's bar |
| **Context economics** | Each skill's metadata is always loaded; at least one host truncates the skill list at ~2% of context (8,000-char fallback). 38 terse descriptions fit; 38 verbose ones do not, which is why descriptions are capped at 200 characters and installs are profile-scoped |
| **Parallelism** | Skills are the unit of concurrency. Fewer, larger skills serialise the audit and blow the wall clock on a monorepo |

Against the brief's 37 domains: **six merges** (architecture+ADR, blast-radius+resilience, SRE+operational
readiness, quality+debt, ownership+silos, platform+DX), **one split** (dead code out of quality), and **five
additions** (kernel, licence/IP, evidence verifier, remediation roadmap, portfolio rollup). The count is
coincidentally close to the brief's; the composition is materially different, and the composition is the point.

## 2. Which skills are core?

**Nineteen.** RDA-00 kernel · 01 orchestrator · 02 census · 03 entry points · 04 architecture · 08 data layer ·
09 configuration · 10 secrets · 11 security posture · 13 dependencies/SBOM · 18 testing · 19 CI/CD ·
21 observability · 26 quality/debt · 28 source-control health · **32 evidence verifier** · 33 risk register ·
34 known unknowns · 36 executive brief.

The test for core membership: *would omitting it make the audit misleading rather than merely incomplete?*
RDA-02, RDA-32 and RDA-34 are core by that test even though none of them produces a finding about the code —
they produce the denominators, the verification and the limits without which every other finding is unfalsifiable.

## 3. Which skills are optional?

**Three.** RDA-25 cost (requires billing data the repository does not contain — without it the skill can only
produce a labelled model, which is often not worth the tokens), RDA-27 dead code (highest harm-if-wrong in the
pack; run only when someone intends to act on it), RDA-30 developer experience (rarely decision-relevant in
diligence, valuable in onboarding).

Sixteen more are **conditional**, activated by census signals rather than by preference — personal-data
indicators activate RDA-16/17, vendored code activates RDA-15, multiple deployable units activate RDA-06/22.
Conditionality is what keeps a 38-skill catalogue from becoming a 38-skill invoice.

## 4. Which skills were missing from the original request?

Five, in descending order of consequence:

1. **RDA-32 evidence-verifier.** Without an independent adversarial pass, every other control is self-graded.
   The verifier must re-derive **blind** — a verifier that sees the draft inherits the draft's errors — and it
   must be able to **invalidate the run**. This is the difference between governance and governance theatre.
2. **RDA-00 audit-core.** The contract has to be one always-on artifact. Thirty-eight skills each carrying their
   own standard of proof is thirty-eight standards of proof.
3. **RDA-15 licence-ip-review.** The most common deal-breaker in software M&A was absent from a due-diligence
   specification. Manifest-only scanning misses vendored and copy-pasted code, which is precisely where
   contamination lives.
4. **RDA-35 remediation-roadmap.** A register without sequencing, prerequisites and an explicit accept-risk
   option is received as criticism and shelved.
5. **RDA-37 portfolio-rollup.** The brief's own premise includes multi-repository systems; systemic risk is
   invisible one repository at a time.

## 5. Which skills must never be merged?

| Never merge | Because |
|---|---|
| **RDA-32 into anything** | A verifier inside the thing it verifies is not a verifier. Its independence is its entire value |
| **RDA-34 into RDA-36** | The moment unknowns become a paragraph in the summary, they get compressed to fit. The ledger is a first-class artifact with its own completeness test |
| **RDA-02 into RDA-01** | Planning is judgement, census is measurement. Merging lets estimates masquerade as counts — the exact failure the framework exists to prevent |
| **RDA-27 into RDA-26** | Different harm class. A wrong quality finding wastes a sprint; a wrong dead-code finding causes an outage |
| **RDA-11 into RDA-12** | Adjudicating concrete weaknesses and reasoning about attacker goals are different activities. Merged, you reliably get a findings list with a STRIDE table stapled to it |
| **RDA-13 into RDA-14** | "Which components have CVEs" and "can our build be subverted" share only the word *dependency* — different tools, different evidence, different owner |
| **RDA-16 into RDA-08** | Different reviewers, different regulators, different escalation path |
| **RDA-29 into RDA-28** | The ethical guardrail lives in RDA-29. Diluting it into general repo hygiene is how contribution data becomes personnel judgement |

## 6. Which skills provide the highest ROI?

Ranked by decision value per token:

| Rank | Skill | Why |
|---|---|---|
| 1 | **RDA-10 secret-flow-audit** | Deterministic, minutes to run, and the single finding most likely to require action within the hour. Highest expected value per token in the pack |
| 2 | **RDA-02 repo-census** | Cheap arithmetic that makes every other finding defensible. Also the cleanest competitive differentiator, since nothing in the surveyed field states its own coverage |
| 3 | **RDA-13 dependency-sbom-audit** | Deterministic, maps to regulation, and answers the question the Log4j review identified as decisive — organisations that responded best simply *knew where the component was*, and few could |
| 4 | **RDA-32 evidence-verifier** | Converts a plausible report into a defensible one. Protects the reviewer's attention, which the curl maintainers' experience shows is the resource actually destroyed by unfiltered AI findings |
| 5 | **RDA-03 entry-point-map** | Every security and resilience conclusion downstream is scoped by it; an audit that has not enumerated entry points is auditing an imagined system |
| 6 | **RDA-15 licence-ip-review** | Low cost, binary outcomes, and the finding most likely to change a price |
| 7 | **RDA-34 known-unknowns-ledger** | Cheapest credibility in the pack. The interview agenda is usually the most-used page of the report |

Lowest ROI, and honestly so: RDA-30 (rarely changes a decision) and RDA-25 without billing data (produces a
model, not a fact).

## 7. Execution order for Codex

Codex reads `AGENTS.md` root-down and discovers skills at `.agents/skills/`, with the startup skill list capped
at ~2% of context. So:

1. Install a **profile**, not the full pack — the metadata budget is the binding constraint, and `install.sh
   --profile P4` exists for exactly this.
2. Put the RDA-00 contract in `AGENTS.md` so it is always in the instruction chain, and keep it well inside the
   32 KiB `project_doc_max_bytes` ceiling.
3. Invoke explicitly with `$rda-01-audit-orchestrator`, then let the DAG drive: **01 → 02 → {03, 08, 09} →
   {04, 05, 06, 07} ∥ {10, 11, 13} ∥ {18, 19, 26, 28} → conditionals → 31 → 32 → 33 → {34, 35, 37} → 36.**
4. Run each shard as its own Codex session with structured JSON output; merge outside the model. Codex's
   session boundary is a useful context boundary, not an obstacle.
5. Add a `## Code Review Rules` section to `AGENTS.md` so PR-time review inherits the same evidence contract as
   the audit.

## 8. Execution order for Antigravity

Antigravity's constraint is different: workspace rules live in `.agents/rules/` and both rules and workflows are
capped at **12,000 characters each**, with four activation modes. So:

1. Install the condensed kernel (2.5k chars) as an **Always On** rule in `.agents/rules/rda-core.md`.
2. Express each *profile* as a **workflow** (`/rda-p4-due-diligence`), not each skill — workflows are the
   slash-invoked unit and can call other workflows, which maps cleanly onto the DAG's layers.
3. Register the per-layer sequences as chained workflows: `/rda-layer1-structure` → `/rda-layer2-risk` →
   `/rda-layer3-ops` → `/rda-verify` → `/rda-report`, so a run can be resumed at a layer boundary.
4. Use **Model Decision** activation for the domain skills so the agent pulls in only what the census triggered,
   and reserve Always On strictly for the kernel — an always-on domain skill is context you pay for on every turn.
5. Use the Artifacts/walkthrough surface for the executive brief, keeping the machine layer (findings.json,
   coverage.json, SARIF) as files. **[Antigravity's skills support and artifact API were not verifiable from
   official documentation at time of writing — treat step 5 as provisional.]**

## 9. What architectural decisions would a CTO approve?

1. **Deterministic-first.** Tools run over 100% of the corpus; the model reads risk-weighted strata. Cost scales
   with risk surface, not repository size — the only way a 500k-file audit has a predictable budget.
2. **Adjudication over generation.** Where a tool exists, it produces candidates and the model judges them.
   This is the decision that keeps the security output usable, and it is supported by the evidence: unaided LLM
   vulnerability detection collapses on leakage-controlled benchmarks and flips verdicts on trivial renaming,
   while tool-grounded adjudication performs materially better.
3. **Evidence as a schema, not a style.** Findings are validated records; two linters fail closed. Governance
   that is only prose is governance that models discard under context pressure.
4. **Coverage is published, not implied.** Every section carries its denominator. This is the control that makes
   the report survive a hostile read, and it is the field's largest unoccupied gap.
5. **Confidence is awarded, never self-scored.** Verbalised model confidence is near-chance at separating
   correct from incorrect and worst in professional-knowledge domains — so `confidence: 0.85` is banned and the
   C0–C4 ladder is awarded by countable evidence properties.
6. **Verification has authority.** RDA-32 can invalidate a run. A gate that cannot fail is not a gate.
7. **Honest reproducibility.** The deterministic layer reproduces byte-for-byte; the interpretive layer does not,
   and the framework says so rather than claiming determinism it cannot deliver.
8. **Portability via one canonical pack.** `.agents/skills/` plus one symlink covers every skills-capable
   environment; rule-style files are generated. A dead target costs one adapter file. This pattern is already
   proven at scale by at least one 39k-star multi-harness pack.
9. **Refusals encoded as first-class behaviour.** No individual performance evaluation, no compliance verdicts,
   no currency without billing evidence, no deletion without reachability, no modification of the code under
   audit. Each refusal is enforced by the linter, not by good intentions.
10. **`INSUFFICIENT_BASIS` is a valid verdict.** Issuing a go/no-go on 8% risk-surface coverage is the real
    failure; declining to is the professional one.

## 10. What blind spots remain after all 38 skills?

1. **Semantic correctness of business rules.** RDA can prove a discount rule exists at a line and is enforced in
   one place rather than three. It cannot know it is the right rule.
2. **Runtime reality.** Deployment, load, cost, incidents, residency — outside source by construction. RDA
   converts them into an interview agenda; it does not close them.
3. **Deliberate concealment.** A curated data room, a rewritten history, an excluded repository. RDA-31 can flag
   inconsistency; it cannot infer intent.
4. **Sophisticated supply-chain attack.** A signed, popular, behaviourally benign malicious dependency passes.
   Provenance raises the bar; it does not remove the class.
5. **Model competence.** RDA constrains what may be claimed; it cannot make a model see what it misses. A
   missed vulnerability yields a clean report with honest coverage numbers — and the coverage numbers are the
   only defence, because they tell the reader how much silence to trust.
6. **Interpretive reproducibility.** Wording and ordering vary between runs; only the finding set is stable, and
   only the verification statistics measure that.
7. **Organisational truth.** Whether the team can execute, whether the architect is resigning, whether the
   roadmap is funded. Decisive, and not in the repository.
8. **Prompt injection through repository content.** Mitigated by treating corpus text as data, not instruction,
   but not eliminated — and worth noting that the best-known open security-review skill in this space ships with
   an explicit warning that it is not hardened against it.
9. **The framework's own unevaluated efficacy.** RDA has not yet been A/B tested against a no-pack baseline.
   Trail of Bits published the uncomfortable finding that *"a capable model scores 1.00 with no plugin loaded"*
   on some evaluations. **Recommendation: before rollout, evaluate RDA with-pack versus without-pack on three
   repositories with known planted defects, and publish the result even if it is unflattering.** A framework
   about evidence that has no evidence for itself has an obvious problem.

---

## Adoption plan

| Phase | Duration | Scope | Exit criterion |
|---|---|---|---|
| **1 · Kernel** | Week 1 | RDA-00, 01, 02, 32 + both linters on one medium repository | Citation resolution rate 1.00; census reproduces byte-identical at a pinned SHA |
| **2 · Deterministic core** | Weeks 2–3 | Add 10, 13, 19, 28 — all tool-backed | First real escalation produced and actioned; SARIF lands in the existing scanning pipeline |
| **3 · Judgement layer** | Weeks 4–6 | Add 03, 04, 08, 09, 11, 18, 21, 26, 33, 34, 36 | Executive brief passes traceability lint: every sentence resolves to a finding id |
| **4 · Diligence layer** | Weeks 7–9 | Add 05, 06, 07, 12, 14, 15, 16, 17, 20, 22, 23, 24, 29, 31, 35 | A full P4 run completes inside budget with re-verification disagreement under 10% |
| **5 · Scale** | Weeks 10–12 | 37 rollup, sharding, caching, run diffing on a 100k+ file monorepo | Per-unit coverage published; incremental re-run costs minutes |

**Team:** one engineer to own the kernel and linters, one security engineer to own the tool substrate, one
practitioner to own the report layer. **Not** a large programme — the framework is deliberately mostly text and
two Python files, because the expensive part is judgement about evidence, not code.
