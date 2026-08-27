# Phases 6 & 7 — Blind-Spot Resolution Engine, Governance & Confidence Framework

The normative documents live in the pack and are the authoritative text; this is the map and the rationale.

| Document | Code | What it governs |
|---|---|---|
| `governance/EVIDENCE-STANDARD.md` | **ES-1** | Claim classes, the undecidable register, citation integrity, independence, falsifiability, silence rules |
| `governance/CONFIDENCE-AND-COVERAGE.md` | **CC-1** | The C0–C4 ladder, ceilings, coverage bands, audit-quality metrics, sampling doctrine |
| `governance/ANTI-HALLUCINATION-CONTROLS.md` | **BSR-1** | Sixteen named controls mapped to the failures they prevent |
| `governance/RISK-SEVERITY-AND-ESCALATION.md` | **RS-1 / ESC-1** | Severity matrix, SSVC decisions, aggregation rules, halt conditions |
| `governance/REPORTING-AND-TRACEABILITY.md` | **RP-1 / TR-1** | Executive/technical/machine layers, the traceability chain, reproducibility scope, expiry |
| `TOOLCHAIN.md` | — | Tool status, behaviour traps, and what each tool actually proves |
| `schemas/*.json` | — | The machine-enforced output contract |
| `scripts/validate_findings.py`, `verify_citations.py`, `validate_pack.py` | — | Fail-closed enforcement |

---

## 1. The design principle: governance that a model cannot quietly drop

Prose instructions degrade under context pressure — that is not a criticism of any model, it is the observed
behaviour of every model, and it is why the field's existing evidence rules (which are all prose) do not hold
across a long audit. So RDA splits governance into three enforcement classes:

| Class | Mechanism | Example | Can a model ignore it? |
|---|---|---|---|
| **Structural** | JSON schema | A finding without evidence is not a valid finding | No — it fails to parse |
| **Mechanical** | Linter / verifier script | A citation that does not re-resolve quarantines its finding | No — it fails the gate |
| **Instructional** | Skill text | "Search for the opposite before writing a finding" | Yes — so it is also a schema field (`disconfirming_check`) that the linter checks |

**The rule of thumb: any control that matters is expressed at least twice — once as instruction, once as a
check.** Every rule in ES-1 and CC-1 that could be silently dropped has a corresponding error code in
`validate_findings.py`. That is what makes this a framework rather than a style guide.

## 2. The sixteen controls (BSR-1)

| # | Control | Prevents |
|---|---|---|
| BSR-01 | Cite-or-abstain | Free-floating assertions |
| BSR-02 | Citation re-resolution at the pinned commit | Invented files, invented line ranges, drifted quotes |
| BSR-03 | Undecidable register | Deployment / scale / cost / exploitability / compliance fabrication |
| BSR-04 | Tool-corroboration floor | Model-invented security and dependency findings |
| BSR-05 | Blind adversarial re-verification | Plausible-but-wrong findings reaching the summary |
| BSR-06 | Disconfirming search | Confirmation-shaped reasoning |
| BSR-07 | Denominator discipline | "We reviewed the codebase" when 3% was read |
| BSR-08 | Summary-depth cap | Compounding drift in map-reduce over large repos |
| BSR-09 | No-name attribution | Ownership claims becoming personnel judgement |
| BSR-10 | Estimate labelling | Fake cost, fake effort, fake timelines |
| BSR-11 | Reachability gate | False dead code, false "unused dependency", false "exploitable" |
| BSR-12 | Run manifest | Unreproducible, unattributable conclusions |
| BSR-13 | Existence check | Fabricated-but-plausible packages, CVEs, CWEs, config keys |
| BSR-14 | Perturbation stability | Verdicts that turn on identifier names rather than semantics |
| BSR-15 | Deterministic ordering, temperature 0 for extraction | Irreproducible output from identical evidence |
| BSR-16 | Corpus-as-data | Prompt injection through repository contents |

Three of these deserve emphasis because they are the ones most often skipped:

**BSR-02 is the load-bearing one.** It is the only control that mechanically distinguishes a real citation from
a plausible one, and plausibility is precisely the failure mode: models identify convincing file paths at high
rates *without any repository access at all*. `verify_citations.py` re-reads every quote at the pinned commit
and hash-compares it. Quarantine is removal, not a warning.

**BSR-05 must be blind or it is worthless.** The load-bearing detail in chain-of-verification is that
verification questions are answered *independently, so the answers are not biased by other responses*. A
verifier shown the draft agrees with the draft. RDA-32 receives the claim's subject and nothing else.

**BSR-13 exists because self-consistency does not solve hallucination.** In the best-quantified code-domain
measurement, **43% of hallucinated package names repeated on every one of ten re-runs**. Asking again is not
verification; asking the registry is.

## 3. Evidence quality standard (ES-1) in one table

| Requirement | Mechanism | Error code |
|---|---|---|
| Every FACT/INFERENCE has evidence | Schema + linter | E010 |
| Source evidence has commit + verbatim quote | Linter | E014/E015 |
| Tool evidence has name + version + exit code | Linter | E016 |
| INFERENCE has a written derivation and ≥2 independent sources | Linter | E020/E021 |
| Citations re-resolve at the pinned commit | Verifier | quarantine |
| Undecidable claims respect their class ceiling | Linter regex over statements | E050 |
| Compliance verdicts, numeric self-confidence and person-day estimates never appear | Linter | E051 |
| Every finding is falsifiable | Linter | E060 |
| Coverage reference resolves to a real coverage record | Linter | E061 |

## 4. Confidence framework (CC-1)

Confidence is **awarded from countable properties**, never chosen. The justification is empirical: verbalised
model confidence separates correct from incorrect at roughly coin-flip AUROC, is systematically overconfident,
and degrades most in professional-knowledge domains — which is the entire content of an audit.

| Level | Awarded when | Permitted use |
|---|---|---|
| C0 | No resolvable evidence | Never publishable |
| C1 | One citation, or convenience sampling, or no disconfirming search | Body only, never a headline, never HIGH/CRITICAL |
| C2 | ≥2 independent citations + recorded disconfirming search | Executive body; ceiling for undecidable-register claims |
| C3 | C2 + deterministic tool agreement with version and exit code | **Floor** for HIGH/CRITICAL security, supply chain, data governance |
| C4 | C3 + a reproduced execution artifact | **Required** to justify a spend, a gate, or a price adjustment |

Severity and confidence are reported as an orthogonal pair and never multiplied. `HIGH / C1` is not a finding —
it is a verification task, and saying so is what keeps the register trustworthy.

## 5. Coverage framework

Two numbers per skill, both mandatory, both drawn from the census rather than estimated:
**artifact coverage** (files or services inspected ÷ population) and **risk-surface coverage** (share of the
risk-weighted population — externally reachable endpoints, money paths, personal-data touchpoints). The second
is the honest one. A monorepo audit can reach 80% file coverage and 10% of the authentication surface, and only
the second number tells the reader whether the silence means anything.

Bands carry prescribed language, so a reader cannot mistake a spot check for an inventory:
EXHAUSTIVE (1.0) · BROAD (0.60–0.99) · PARTIAL (0.20–0.59) · INDICATIVE (0.05–0.19) · ANECDOTAL (<0.05).

## 6. Audit-quality metrics reported on every run

| Metric | Healthy | Failure signal |
|---|---|---|
| Citation resolution rate | 1.00 | <1.00 means fabricated or drifted evidence exists |
| Unknown rate | 0.05–0.30 | 0 = false completeness; >0.5 = insufficient access, rescope |
| Corroboration rate (C2+) | >0.6 | Low = single-source reporting |
| Re-verification disagreement | <0.05 | >0.10 **invalidates the run** |
| Tool-agreement rate | reported | Divergence is information, not error |
| External-validation load | reported | This is the interview agenda |

The **unknown rate** is the counter-intuitive one and the most diagnostic. Models essentially never abstain
unprompted — spontaneous refusal was measured at 0.035% across 194,480 calls — so abstention must be an
engineered, instructed and *measured* output. A report with zero unknowns has not been thorough; it has been
confident.

## 7. Risk, severity, escalation

Severity is impact × likelihood on a published matrix, applied mechanically so two runs agree. Security
findings additionally carry an SSVC-style decision (`TRACK` / `TRACK*` / `ATTEND` / `ACT`) built from
exploitation status, exposure and impact — because CVSS ranks badness in the abstract while SSVC ranks what to
do. Present / reachable / exploitable are three separate counts and are never collapsed; VEX supplies the
vocabulary, with its own caveat preserved — VEX statuses are *"assertions made by the author of the document"*,
machine-readable attestation rather than proof.

**ESC-1 halt conditions**, where the agent stops rather than files a finding: live secret material · evidence of
compromise · regulated personal data in fixtures, logs or dumps · licence contamination threatening product
ownership · re-verification disagreement above 10% · unauthorised material in scope. Escalation output states
what was found, where, what class of harm, what to do in the next hour, and what RDA deliberately did **not** do.

## 8. Reporting, traceability, reproducibility

The chain is `executive sentence → finding id → evidence locator + commit SHA → quote hash → verifier result →
manifest`, and every link is machine-checkable. Executive, technical and machine layers are *renderings of one
finding set*, never separately authored prose — which is what prevents the classic failure where the summary is
more confident than the analysis.

Reproducibility is claimed **honestly and separately** for two layers: the deterministic layer (census, tool
runs, git queries) reproduces byte-for-byte at pinned commits with pinned tool versions; the interpretive layer
does not, and is guaranteed only at the level of the finding set, measured by re-verification agreement rather
than by diffing prose. Claiming full reproducibility of an LLM audit would itself be an unsupported claim —
which would be an unusually poor way to open a document about unsupported claims.

Findings expire when the pinned commit is no longer an ancestor of the default branch head, or after 90 days,
whichever is sooner. The supported refresh path is re-running the deterministic layer at a new commit and
diffing the finding set — cheaper than a fresh audit, and it produces a trend, which is what boards actually ask
for the second time.
