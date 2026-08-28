# RDA — Repository Due-diligence & Audit skill pack v1.0

A portable, evidence-governed skill framework for repository inspection and technical due diligence.
38 skills, one canonical format, ten target environments, and two linters that fail closed.

**What makes this different from the dozens of code-review skill packs that already exist:** every finding
carries a machine-checkable citation, every section publishes the fraction of the population it inspected,
confidence is awarded by rubric rather than self-reported, and an independent verification gate can invalidate
the run. Across roughly sixty comparable assets surveyed in August 2026, not one emitted a numeric coverage score.

## Install

```bash
scripts/install.sh --profile P4 --target /path/to/repo        # M&A due diligence
scripts/install.sh --profile P5 --scope user --tools claude,codex,cursor
```

The canonical tree lands at `.agents/skills/` — natively discovered by Codex, Cursor, Gemini CLI, GitHub
Copilot/VS Code and Devin Desktop. Claude Code gets a symlink at `.claude/skills/`. Rule-style files
(`.mdc`, `.instructions.md`, `trigger:` rules, `.roomodes`, `CONVENTIONS.md`, Gemini TOML commands) are
**generated** by `scripts/generate_adapters.py` — never hand-maintained.

## Layout

```
CATALOG.md              38 skills: id, tier, risk class, purpose, dependencies
ARCHITECTURE.md         design decisions, merge/split rationale, the execution DAG
docs/                   00-START-HERE · research & landscape · blind-spot analysis · CTO recommendation
                        · governance & confidence framework  (the why, read in order)
governance/             EVIDENCE-STANDARD · CONFIDENCE-AND-COVERAGE · ANTI-HALLUCINATION-CONTROLS
                        RISK-SEVERITY-AND-ESCALATION · REPORTING-AND-TRACEABILITY
schemas/                finding · coverage · run-manifest  (the output contract)
scripts/                rda_census.sh · verify_citations.py · validate_findings.py
                        validate_pack.py · generate_adapters.py · install.sh · selftest.py
skills/rda-NN-*/        one SKILL.md per skill, Agent Skills standard
workflows/PROFILES.md   P1 small · P2 medium · P3 monorepo · P4 M&A · P5 security · P6 prod-readiness · P7 CTO onboarding
adapters/PORTABILITY.md the ten environments, their limits, and what those limits forced
templates/              skill template · worked example findings + coverage · adversarial fixture
```

New here? Read [`docs/00-START-HERE.md`](docs/00-START-HERE.md).

## The contract in nine lines

1. Label every claim: FACT · INFERENCE · HYPOTHESIS · UNKNOWN · EXTERNAL_VALIDATION_REQUIRED.
2. Never assert deployment, scale, cost, exploitability, dead code, individual ownership, compliance,
   scalability, incident history or data residency from source alone.
3. Publish the denominator. Absence of evidence is UNKNOWN, never "no issues found".
4. Run one disconfirming search per finding and record it.
5. Confidence is awarded (C0–C4), never chosen. Numeric self-confidence is banned.
6. Deterministic tools over 100% of the corpus; the model reads risk-weighted strata.
7. Adjudicate tool candidates; do not invent findings. Existence-check every named package, CVE and CWE.
8. Halt and escalate on live secrets, compromise indicators, regulated data, or licence contamination.
9. A report with zero unknowns is suspect, not thorough.

## Verify it works

```bash
python3 scripts/selftest.py                          # every gate, both directions (72/72 codes)
```

Or run the gates individually:

```bash
python3 scripts/validate_pack.py skills --budgets                         # conformance, profile closure, budgets
python3 scripts/generate_adapters.py --check                              # adapters match their source of truth
bash    scripts/rda_census.sh /path/to/repo ./rda-out                     # denominators, reconciled
python3 scripts/verify_citations.py findings.json --repo /path/to/repo    # BSR-02, fails closed
python3 scripts/validate_findings.py findings.json --coverage coverage.json --strict
```

`validate_findings.py` enforces what a JSON Schema cannot: class ceilings, confidence award rules,
severity/confidence floors, evidence independence, the RS-1 severity matrix, the undecidable register, and the
abstention metrics. It also validates each finding against `schemas/finding.schema.json` using a built-in
subset validator, so the schema is enforced rather than merely published — the pack stays dependency-free.
`--strict` promotes the abstention warnings and any quarantined finding to failures, which is what CI should
run. Try it against `templates/example-findings.json` (clean) to see the shape of a conforming finding.

`generate_adapters.py --check` regenerates all 21 adapter files in memory and diffs them against the committed
tree without touching it, so "generated, never hand-maintained" is verified rather than asserted.
`validate_pack.py` reads profile membership straight out of `install.sh` and fails if any profile is not closed
under the dependency graph.

Both linters are tested in **both** directions, and every code either linter can emit is proven to fire by a
deliberate violation — 72/72 codes. `templates/example-findings-invalid.json` is a malformed fixture that must
trip 44 violations across 28 distinct codes; the conforming example must trip none. A gate that quietly stopped
enforcing would pass a one-sided test and fail this one, and a code added without a test fails the suite.

## Licence

Apache-2.0. Third-party tools RDA shells out to keep their own licences; `trailofbits/skills`, studied as prior
art, is CC-BY-SA-4.0 and is **not** incorporated — its share-alike terms make direct reuse a procurement
question rather than a copy.
