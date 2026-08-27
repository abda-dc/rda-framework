# Phase 0 — Discovery, Landscape & Buy-vs-Build

*Research conducted 2026-08-27 across the Anthropic, OpenAI/Codex, Cursor, Windsurf, Roo Code, Gemini,
Antigravity and GitHub Copilot ecosystems, plus the standards, tooling and LLM-reliability literature.
Claims below are traceable to the sources named. Items I could not verify are marked **[unverified]**.*

---

## 0. Executive answer to "does this already exist?"

**Partly — and the part that exists is the part that matters least.** There is a large and rapidly maturing
supply of *code review* and *security scan* assets. There is almost nothing that does **evidence-governed,
coverage-scored, whole-repository due diligence**. Across roughly sixty assets surveyed, **not one emits a
numeric statement of what fraction of the repository it actually inspected.**

That single gap is the strategic justification for building RDA. Everything else in this framework is
assembly; coverage scoring, calibrated per-finding confidence in the code domain, a uniform citation contract
across every domain, and commit-pinned reproducibility are the genuinely unoccupied ground.

---

## 1. Six premise corrections before any design work

The brief named ten target environments and several reference assets. Six of those premises are now stale, and
building against them would have produced dead adapters.

| Briefed assumption | Verified position (2026-08-27) | Consequence for RDA |
|---|---|---|
| **GitHub Copilot Workspace** is a target environment | **Retired.** GitHub Next states the technical preview was *"sunset on May 30th, 2025"* | Retarget to **Copilot cloud agent**, Copilot code review, and VS Code agent mode. Note skills are read from the **head branch** during PR review |
| **Windsurf** is a standalone product | Documented under **Devin Desktop** (Cognition); `.devin/` preferred, `.windsurf/` retained as fallback; Cascade memories are legacy | Ship both rule paths; skills work via `.agents/skills/` |
| **Roo Code** is a live ecosystem to target | `RooCodeInc/Roo-Code` is a **public archive**; the extension was shut down | Keep the `.roomodes` adapter (installed bases persist) but do not treat it as a growth target **[partially verified — archive status confirmed, shutdown date reported]** |
| **OpenAI has no skills concept** | **False.** Codex adopted the Agent Skills standard (`SKILL.md`, `.agents/skills/`); `~/.codex/prompts` custom prompts are deprecated in favour of skills | One canonical format serves Codex and Claude Code alike |
| **`sourcegraph/cody`** is a live OSS option | **Archived**; Free/Pro sunset 23 Jul 2025; superseded by closed-source Amp | Remove from the reuse list |
| **`github/awesome-copilot`** has `prompts/` + `chatmodes/` | **Both deleted**; restructured to `skills/` + `agents/` (plus instructions, plugins, workflows, hooks) | Target the current structure |

**Design consequence:** the portability layer is generated from one source of truth, so a target that dies costs
one adapter file, not a rewrite.

---

## 2. The standards convergence that makes a portable pack cheap

Two open standards now carry the load:

- **Agent Skills** — a directory containing `SKILL.md` with YAML frontmatter (`name` ≤64 chars matching the
  directory, `description` ≤1024 chars, optional `license`, `compatibility`, `metadata`), optional `scripts/`,
  `references/`, `assets/`. Originally Anthropic's, released as an open standard (agentskills.io) and adopted
  across Codex/ChatGPT, Cursor, Gemini CLI, GitHub Copilot & VS Code, Devin Desktop, Claude Code and dozens more.
- **AGENTS.md** — plain-markdown always-on project instructions, *"used by over 60k open-source projects"* and
  now **stewarded by the Agentic AI Foundation under the Linux Foundation**.

**The single most actionable fact:** `.agents/skills/` (project) and `~/.agents/skills/` (user) are a shared,
tool-neutral discovery path honoured by Codex, Cursor, Gemini CLI, GitHub Copilot/VS Code and Devin Desktop.
**Claude Code is the sole exception** — it reads only `.claude/skills/` — **but it follows symlinks and
de-duplicates targets reachable from multiple locations.** One canonical tree plus one symlink covers everything.

### Hard limits that shaped RDA's design

| Environment | Limit | RDA's response |
|---|---|---|
| Codex | Skill list uses **at most 2% of context, or 8,000 characters** when unknown; descriptions are shortened first, then skills are silently omitted | Descriptions capped at **200 characters**; profile-based installs; `validate_pack.py` reports the aggregate metadata budget |
| Devin Desktop / Windsurf | Workspace rule **12,000 chars**, global rules file **6,000 chars**, workflows 12,000 chars and manual-only | Condensed kernel rule sized under 6,000 chars |
| Antigravity | Rules and workflows **12,000 characters each** | Same condensed kernel |
| Agent Skills spec | SKILL.md recommended **<5,000 tokens / <500 lines**; metadata ~100 tokens per skill always loaded | Skills held to 90–160 lines; references kept one level deep |
| Codex AGENTS.md | Chain stops at `project_doc_max_bytes` (**32 KiB** default) | AGENTS.md adapter stays well inside |
| Cursor | `.md` in `.cursor/rules` is **ignored** — must be `.mdc` with frontmatter | Adapter generates `.mdc` |
| GitHub Copilot | Invalid characters or namespace prefixes in `name` cause the skill to **silently fail to load** | Validator enforces the charset |
| Gemini CLI | Skill activation is **consent-gated** via an `activate_skill` confirmation | Profiles keep the number of consent prompts small |

**Prior art that validates the approach:** `wshobson/agents` (39k★, MIT) already ships to Claude Code, Codex
CLI, Cursor, OpenCode, Gemini CLI and Copilot from one Markdown source *and explicitly respects the 8KB Codex
skill cap*. The one-source-many-adapters pattern is proven, not speculative.

---

## 3. Capability comparison — what already exists

### 3.1 The five assets that matter

| Asset | License | Scale | What it genuinely does | What it does not |
|---|---|---|---|---|
| **`trailofbits/skills`** ⭐ strongest prior art | **CC-BY-SA-4.0** (share-alike — a procurement flag) | 6.9k★, active | 40+ audit plugins with orchestrator→workers→**dedup judge**→**false-positive judge**→SARIF; deterministic run-plan script treated as *"the only authority"*; scope separation of finding root vs context roots; **partial-run disclosure**; a standardised "nothing found" phrase that makes unchecked assumptions greppable; adversarial self-refutation per file | No M&A/investor framing, no remediation costing, no bus factor, no tech-debt quantification, **no coverage percentage** |
| **`OneWave-AI/claude-skills` → `tech-due-diligence`** — closest competitor | MIT | 276★ repo | 10-phase DD producing an investment memo: reconnaissance→architecture→quality→security→scalability→tests→build→**team inference from git history**→dependency & licence→docs. Anti-inflation risk calibration (*"Do not inflate risk to appear thorough"*), a "Due Diligence Gaps" section, secret redaction, multi-audience output | *"Read representative samples, not every file"* **with no disclosure of what was sampled**; no coverage %; no per-finding confidence; file-*path* not file:*line*; no adversarial pass; **remediation costed at a flat $8,000/engineer-week** |
| **`github/awesome-copilot`** — richest ecosystem | MIT | 38.1k★, daily activity, 408 skills / 221 agents | `doc-and-modernize` *"cites every claim to a file + line, flags unverified facts"* with `[INFERRED]`/`[UNVERIFIED]` markers and a confidence table; `sast-sca-security-analyzer` (CWE, CVSS, licence risk, SHA-pinning, policy PASS/FAIL vs OWASP/PCI/NIST/HIPAA/GDPR); `audit-integrity` (anti-rationalisation guard, self-reflection gate); `build-evidence-map` (**fail-closed `validate.mjs`**, refuses fabricated confidence) | Quality is **highly uneven** across 221 agents — `architecture-blueprint-generator` contains **no citation requirement whatsoever**. No coverage %, no per-finding calibrated confidence, no investor framing |
| **Anthropic official `code-review` plugin** | proprietary | — | 4 parallel reviewers, a **validation subagent that drops unvalidated findings**, full-SHA permalinks with line ranges | *"Focus only on the diff itself without reading extra context"* — an explicit **anti**-repo-inspection constraint |
| **`anthropics/claude-code-security-review`** | MIT | 6.1k★, ~6 months stale | Injection, authn/authz, crypto, business logic, supply chain; false-positive filtering | **Diff-aware only**; explicitly excludes DoS and rate limiting; **not hardened against prompt injection** — *"should only be used to review trusted PRs"* |

**Notable absence:** `anthropics/skills` (172k★, 19 skills) contains **zero** repo-analysis, review, security,
architecture or onboarding skills. The gap in the official catalogue is total.

### 3.2 Domain coverage across the field

✅ strong · ◐ partial · ❌ absent

| Domain | ToB skills | awesome-copilot | OneWave tech-DD | Commercial (CodeScene/SIG/CAST) | Scanners (Semgrep/Snyk/GHAS) | **RDA target** |
|---|---|---|---|---|---|---|
| Repo mapping | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ + **counted denominators** |
| Architecture + ADR | ◐ | ✅ | ✅ | ✅ | ❌ | ✅ + **drift vs cited code** |
| Security | ✅✅ | ✅ | ✅ | ✅ | ✅ | ✅ **adjudication-over-tools** |
| Threat modelling | ✅ | ◐ | ❌ | ◐ | ❌ | ✅ from real entry points |
| Secrets | ◐ | ✅ | ✅ redaction | ✅ | ✅ | ✅ + history + escalation halt |
| Dependencies / SBOM | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ **present/reachable/exploitable split** |
| Licence & IP | ◐ | ✅ | ◐ | ✅ | ◐ | ✅ **incl. vendored + AI-generated provenance** |
| Testing | ✅ | ◐ | ✅ | ✅ | ❌ | ✅ measured, not claimed |
| CI/CD | ✅ | ✅ | ✅ | ✅ | ◐ | ✅ |
| IaC | ❌ | ✅ | ◐ | ◐ | ✅ | ✅ intent-vs-state discipline |
| Observability / SRE | ❌ | ◐ | ◐ | ◐ | ❌ | ✅ instrumented-entry-point ratio |
| Resilience / blast radius | ❌ | ✅ WAF | ◐ | ✅ | ❌ | ✅ **graph-gated** |
| Performance | ◐ | ◐ | ✅ | ✅ | ❌ | ✅ no numbers without artifacts |
| Cost | ❌ | ❌ | ✅ $8k/eng-week | ✅✅ | ❌ | ✅ **labelled model, never a bare figure** |
| Code quality / debt | ✅ | ✅ | ✅ | ✅✅ | ◐ | ✅ + **debt-dollarisation caveats** |
| Source-control health | ◐ | ◐ | ✅ | ✅ | ❌ | ✅ + corrected DORA metric set |
| **Ownership / bus factor** | ❌ | ❌ | ◐ | ✅✅ | ❌ | ✅ **role-level only, never individuals** |
| Compliance | ◐ | ✅✅ | ◐ | ✅ | ✅ | ✅ **evidence, never verdicts** |
| Data governance | ❌ | ◐ | ❌ | ◐ | ◐ | ✅ Art. 30-shaped |
| Supply chain | ✅✅ | ✅ | ◐ | ✅ | ✅ | ✅ Scorecard/SLSA rubric |
| DX / platform | ❌ | ✅ | ❌ | ✅ | ❌ | ◐ optional |
| **Executive reporting** | ◐ | ◐ | ✅ memo | ✅✅ board | ❌ | ✅ **every sentence traced to a finding id** |
| **Evidence governance** | ✅✅ judges | ✅ audit-integrity | ◐ | ❌ | ◐ | ✅ **schema-enforced + machine-verified** |
| **COVERAGE SCORING** | ◐ disclosure | ◐ qualitative | ◐ "gaps" | ✅ maturity levels | ❌ **inverted (caps)** | ✅✅ **numeric, per-domain, with denominators** |

---

## 4. The gap list — genuine white space

1. **Numeric coverage scoring.** No surveyed asset emits "% of the relevant population inspected". The nearest
   approximations are Trail of Bits' partial-run disclosure, CodeRabbit's `Partial` status, and vendor maturity
   levels. This is the cleanest differentiator and the cheapest to implement, because it is arithmetic over a
   census, not intelligence.
2. **Per-finding calibrated confidence in the code domain.** Where confidence exists it is either self-assessed
   ("High/Medium/Low") or a raw model number, both of which are decoration (see §6).
3. **One citation contract across all domains.** Evidence discipline exists in fragments — Anthropic's permalink
   rule, GitHub's `[UNVERIFIED]` markers, Trail of Bits' judges — but never uniformly across a whole-repo
   diligence scope.
4. **CTO/investor-grade reporting bound to evidence.** The one asset with investor framing has the weakest
   evidence discipline; the assets with the best evidence discipline have no executive output.
5. **Ownership and key-person risk is orphaned** in the open ecosystem; only commercial products (CodeScene's
   *complex code by former contributors* and *developer congestion*) operationalise it.
6. **Reproducibility.** No surveyed skill pins commits, records tool versions or supports run diffing.
7. **The field's own maintainers now validate the requirement.** A public issue against a 24.7k★ subagent
   collection criticised hardcoded fabricated metrics — *"'Pattern accuracy > 85%', 'Knowledge retrieval <
   500ms'… these numbers appear nowhere as actual measurements… **It's asking the LLM to lie convincingly**"* —
   and the maintainer conceded fully, fixing it with *"grounding rules (cite path:line evidence, don't invent
   numbers, flag uncertainty)"*. Notably, **the fix landed on only 8 files**; the collection's
   `security-auditor`, `code-reviewer` and `architect-reviewer` still ship the un-grounded pattern. The problem
   RDA solves is acknowledged in public and still unsolved in practice.

---

## 5. Buy / partner / build

**BUY — do not rebuild.** Repomix (MIT, packing + token counting + tree-sitter compression + Secretlint);
aider's PageRank repo map (Apache-2.0); OpenSSF Scorecard (18 scored checks); Semgrep and CodeQL as the SAST
substrate; syft/grype/trivy/osv-scanner for SBOM and vulnerability matching; gitleaks/TruffleHog for secrets;
scancode-toolkit/licensee for licences; Checkov/KICS/Conftest for IaC. RDA **shells out** to all of these; it
does not reimplement any of them.

**PARTNER / cite — do not reinvent the rubric.** CHAOSS Contributor Absence Factor; OWASP ASVS 5.0.0 (machine-
readable CSV/JSON); NIST SSDF SP 800-218; OWASP SAMM; SLSA; the DORA capability catalogue; OpenSSF Best
Practices criteria; SPDX licence identifiers; ISO/IEC 5055 and 25010 for quality vocabulary. These give RDA
findings *external* identifiers, which is what makes them arguable in a deal room rather than opinions.

**STUDY, then differentiate.** `trailofbits/skills` for orchestration (judges, run-plan-as-authority, scope
separation) — noting its **CC-BY-SA-4.0 share-alike** licence makes direct incorporation a procurement question
rather than a copy-paste. Also instructive is Trail of Bits' honest published finding that *"a capable model
scores 1.00 with no plugin loaded"* on some evaluations — a warning that skill packs must be evaluated
against a no-plugin baseline or their value is assumed rather than demonstrated.

**BUILD — the white space.** Coverage scoring per domain with denominators · per-finding awarded confidence ·
one citation contract · commit-pinned reproducibility with run diffing · standards-ID-cited rubric · an
executive artifact whose every sentence resolves to a finding id · and the adversarial verification gate.

**The clock is running.** CodeScene ships a Code Health MCP server; SIG ships Sigrid MCP and an LLM-targeted
"learn about us" page; Swarmia and LinearB ship MCP servers. Incumbents are wrapping proprietary engines in
agent interfaces while the open skill catalogue starts from zero — and the MIT-licensed `tech-due-diligence`
skill is already the free default, one install away.

---

## 6. The reliability evidence that dictates the architecture

This is the research that turns design preferences into requirements.

**Context is not the answer.** RULER (COLM 2024) measured *effective* context length and found *"while all
models claim context size of 32k tokens or greater, only half of them can effectively handle sequence length of
32K… Almost all models fall below the threshold before reaching the claimed context lengths"*. NoLiMa (ICML
2025) removed literal string overlap between question and target and found that at 32K, *"11 models drop below
50% of their strong short-length baselines"*, with GPT-4o falling *"from an almost-perfect baseline of 99.3% to
69.7%"*. Chroma's context-rot study (194,480 calls, temperature 0) found degradation with input length *at
constant task difficulty*, worse for low-similarity needles and non-uniform under distractors — and measured a
spontaneous refusal rate of **0.035%**, i.e. models essentially never abstain on their own. LongBench v2, which
explicitly includes code-repository understanding, puts the best direct-answering model at **50.1%** against
**53.7%** for human experts under time pressure.

*Implication:* a security question ("where is authentication bypassed?") has low lexical overlap with the code
that answers it — the NoLiMa regime, not the needle-in-a-haystack regime. **Repo-scale analysis is a retrieval-
and-verification problem, not a context-window problem, and no model release fixes it.**

**Plausible paths are not evidence.** The SWE-Bench Illusion analysis found SOTA models identify buggy file
paths *"from the issue description alone, with no access to repository structure"* at up to **76%** accuracy,
dropping to **53%** on repositories outside the benchmark, concluding gains *"may be partially driven by
memorization rather than genuine problem-solving"*. → **Every path-level claim must be confirmed by an actual
filesystem call.** This is BSR-02.

**Asking for citations is not the same as getting valid ones.** ALCE (EMNLP 2023) found that *"on the ELI5
dataset, even the best models lack complete citation support 50% of the time"*. Anthropic's own research system
runs a **dedicated separate citation pass**. → **Citation validity must be machine-checked**, which is exactly
what `verify_citations.py` does.

**Self-confidence is decoration.** Xiong et al. (ICLR 2024) found LLMs *"tend to be overconfident"* when
verbalising confidence, with white-box methods only marginally better (*"0.522 to 0.605 in AUROC"*) and — most
damningly — *"all investigated methods struggle in challenging tasks, such as those requiring professional
knowledge"*. Security assessment is precisely that regime. → **`confidence: 0.85` is banned; confidence is
awarded by rubric.**

**Security generation fails; security adjudication works.** PrimeVul (ICSE 2025) rebuilt vulnerability datasets
without leakage and reported *"a state-of-the-art 7B model scored 68.26% F1 on BigVul but only 3.09% F1 on
PrimeVul"*, with larger models *"akin to random guessing in the most stringent settings"* — a ~22× collapse from
removing benchmark artifacts. SecLLMHolmes (IEEE S&P 2024) found that *"by merely changing function or variable
names, or by the addition of library functions… these models can yield incorrect answers in 26% and 17% of
cases"*. By contrast, treating *"static analyzer outputs as structured contracts, enriching them with
flow-sensitive traces, contextual evidence, and CWE-specific knowledge before adjudication"* reports F1 above
0.91 **[single un-replicated preprint — treat the architecture as transferable, the numbers as provisional]**.
→ **RDA-11 adjudicates tool candidates; it does not invent vulnerabilities.** This is the single most
consequential architectural decision in the pack.

**The failure mode has a real-world casualty count.** The curl maintainers report that in 2025 *"about 20% of
all submissions"* were AI slop while *"about 5% of the submissions in 2025 had turned out to be genuine
vulnerabilities"*, and that *"every report thus engages 3-4 persons. Perhaps for 30 minutes, sometimes up to an
hour or three. Each."* → **Precision over recall. Unsupported findings must be suppressed before a human sees
them**, because the reviewer's attention is the resource being destroyed.

**Fabricated-but-plausible identifiers are measurable and repeatable.** A USENIX Security 2025 study of 576,000
code samples found *"the average percentage of hallucinated packages is at least 5.2% for commercial models and
21.7% for open-source models"* — 205,474 unique fabricated names — and, critically for governance, **43% of
hallucinated packages repeated on every one of 10 re-runs**. → **Self-consistency will not catch them.**
Existence-check every named package, CVE and CWE against an authoritative registry.

**Verification must be blind.** Chain-of-Verification's load-bearing step is that the model *"answers those
questions independently so the answers are not biased by other responses"*. → RDA-32 re-derives without seeing
the original reasoning.

**No one has published a credible low false-positive rate for whole-repository LLM audit.** The closest proxies
are function-level classification (near-random at scale) and curl's ~5% valid-submission rate.
→ **Design assuming a high base rate of false positives**, because no evidence supports assuming otherwise.

---

## 7. Standards and regulatory anchors (and three things commonly cited wrong)

RDA maps findings to external identifiers rather than inventing its own vocabulary: ISO/IEC 25010 and ISO/IEC
5055 (structural quality), NIST SSDF SP 800-218 and 800-218A, OWASP SAMM / ASVS / Top 10 / LLM Top 10, BSIMM,
CWE Top 25, MITRE ATT&CK, STRIDE and the Threat Modeling Manifesto, SLSA and OpenSSF S2C2F, SPDX and OpenChain
(ISO/IEC 5230), SOC 2 TSC, ISO 27001:2022 Annex A 8.25–8.34, PCI DSS 4.x Requirement 6, HIPAA Security Rule,
GDPR Article 30, Google SRE's production readiness review, and the AWS/Azure Well-Architected pillars.

**Three corrections that matter, because getting them wrong is how an audit loses credibility:**

1. **DORA is now five metrics, and MTTR is retired.** Mean time to restore was replaced by *failed deployment
   recovery time* in 2023, and *deployment rework rate* was added in 2024. Reporting "MTTR" as current DORA
   canon dates the report instantly.
2. **OWASP Top 10:2025 is released**, with Software Supply Chain Failures elevated to A03 and a new A10,
   Mishandling of Exceptional Conditions; ASVS 5.0.0 shipped 30 May 2025 with 17 restructured chapters.
3. **The EU Cyber Resilience Act's reporting duties bite on 11 September 2026** — days from now — and
   Article 69(3) carves the reporting obligation **back out** of the pre-2027 grandfathering. In effect, an
   installed base can be out of scope for the product requirements yet **in scope for reporting**: a product
   sold in 2025 that never needs CE marking still generates a reportable event if a vulnerability in it is
   actively exploited and the manufacturer becomes aware on or after that date. Deadlines run from awareness:
   **24 h** early warning, **72 h** notification, and a final report within **14 days** of a fix being available
   (or one month after the 72-hour notification for a severe incident). **[Verify Art. 69(3) against the
   Official Journal text before relying on it in a deal document.]** This makes "can this organisation detect
   and report an actively exploited vulnerability within 24 hours" a live diligence question, not a future one.

**Quantification honesty.** Technical debt in currency is arithmetically simple and epistemically weak: the
remediation cost per issue is *"taken over from the effort assigned to the rule"* — an author's constant — and
the debt ratio's denominator is a synthetic cost-per-line figure, so two vendors produce different ratios for
identical code. Rule-based measures also cannot see architectural debt. The defensible alternative is
outcome-linked evidence: a peer-reviewed study of 30,737 files across 39 proprietary production codebases found
low-quality code contains **15× more defects**, takes **124% more time** to resolve issues in, and shows **9×
longer maximum cycle times** **[n=39, vendor-affiliated first author — directionally strong, not a universal
coefficient]**.

**Key-person risk, measured honestly.** The primary truck-factor study found **65% of 133 popular GitHub
projects have a truck factor ≤ 2**, but its own validation is the important part: **84%** of surveyed developers
agreed on *who the main authors are* while only **53%** endorsed *the estimated number*. → Use concentration to
identify **which** components are knowledge-locked (reliable); never assert the number as fact. No published
study covers proprietary enterprise codebases, so every threshold is practitioner convention, not evidence —
and RDA labels it as policy.

**The cost of unknown dependencies has one authoritative anchor**, not a market statistic: the Cyber Safety
Review Board's Log4j review recorded that *"one federal cabinet department reported dedicating 33,000 hours"* to
response, that *"there is no comprehensive 'customer list' for Log4j… enterprises and vendors scrambled to
discover where they used Log4j"*, and that organisations which responded best *"understood their use of Log4j"* —
while *"few organizations were able to execute this kind of response"*. That is the business case for RDA-13
and RDA-14 in one paragraph, and it is a government finding rather than a vendor claim.

---

## 8. Research limitations

- **Files search in this Microsoft 365 tenant is blocked by permissions**, so no prior internal repository-audit
  specification could be retrieved. Phase 1 therefore analyses the 37 domains in the brief as the specification.
- Star counts and repository statuses were read on 2026-08-27 and drift.
- Several ecosystem facts are documented only on vendor sites that were mid-migration (Windsurf→Devin Desktop,
  Cursor commands→skills). Items I could not confirm from official documentation are marked **[unverified]**
  in the source notes rather than smoothed over.
- No independently replicated study exists measuring false-positive rates of LLM agents auditing whole real
  repositories. RDA's controls are therefore designed for a high assumed false-positive base rate.
