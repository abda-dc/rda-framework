---
name: rda-00-audit-core
description: Evidence, confidence and output contract for all repository-audit work. Load first whenever auditing, assessing, reviewing or performing technical due diligence on a codebase.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-00"
  layer: "0-kernel"
  risk_class: "HIGH_HARM"
  tier: "core"
  depends_on: ""
---

# RDA-00 · Audit Core (kernel)

You are producing an artifact that people will act on: money moved, deals priced, engineers reassigned, code
deleted. A wrong finding is not a wasted paragraph, it is a wrong decision. The controls below are the price of
being allowed to make claims about a codebase you cannot fully read.

**This skill is a contract, not a procedure. Never run it alone.** It is loaded alongside every other RDA skill.

## The four rules

**1. Label every claim.** Each finding is exactly one of:
- `FACT` — verbatim from a cited artifact (`path#L12-L40` + commit SHA + quote) or a deterministic command
  (name, version, args, exit code).
- `INFERENCE` — derived from **two or more independent** facts, with the derivation written out.
- `HYPOTHESIS` — the evidence permits it but does not establish it. State the exact check that would settle it.
- `UNKNOWN` — required information is absent from scope. Name the system of record and the blocked decision.
- `EXTERNAL_VALIDATION_REQUIRED` — undecidable from source by construction. Carry the question and the role.

**2. Never cross the undecidable line.** From repository contents alone you may not assert, above the class
shown: what is deployed (`HYPOTHESIS`), real traffic or scale (`EXTERNAL`), real cost (`EXTERNAL`), that a
weakness is exploitable (`HYPOTHESIS`), that code is dead (`HYPOTHESIS`), that a named person owns something
(role-level `INFERENCE` only), that the org is compliant (**never** — you report control evidence present or
absent), that something will scale to N (`EXTERNAL`), incident or MTTR history (`EXTERNAL`), or that data
resides in a region (`HYPOTHESIS` — IaC is intent, not state).

**3. Show the denominator, then account for every member of it.** Every section states what population it
examined and what fraction of it it saw, using the census counts from RDA-02. "Reviewed the codebase" is a lie
when you read 3% of it. Absence of evidence is `UNKNOWN` with a coverage record, never "no issues found".
`No issues found` requires exhaustive coverage of a stated population. **A population is not answered by its
first interesting member, and a count is not an adjudication.** Where a section adjudicates a population, the
coverage record carries one `adjudication` row per inspected member — member id, verdict, and for
`CONFIRMED_WEAKNESS` the finding id that carries it — so `inspected.count` is the length of that list rather
than a number asserted beside it. A blanket sentence disposing of many members at once ("all auth-checked") is
not a verdict and does not count as one. The second site is usually the unguarded one, because the first is
where attention stopped; a member you cannot resolve is `UNDECIDABLE` and a declared blind spot, never a
silent omission.

**4. Search for the opposite.** Before writing any finding, run one query that would disprove it (the auth
middleware you did not open, the caller you did not grep for, the config that overrides the default). Record
that query and its result. A finding with no disconfirming search is capped at C1 and may not be an executive
headline.

## Confidence is awarded, never chosen

Numeric self-confidence is decoration: verbalised LLM confidence separates correct from incorrect at roughly
coin-flip AUROC and is systematically overconfident, worst in exactly the professional-knowledge tasks an audit
consists of. So confidence here is a **rubric award**, and `confidence: 0.85` is a schema violation.

| Level | Award rule |
|---|---|
| C0 | No resolvable evidence — **never publishable** |
| C1 | One resolvable citation, or convenience sampling, or no disconfirming search |
| C2 | Two or more citations in different independence groups **and** a recorded disconfirming search |
| C3 | C2 plus a deterministic tool agreeing (name + version + exit code) |
| C4 | C3 plus a reproduced execution artifact (test, PoC, benchmark, query) |

Floors: HIGH/CRITICAL security, supply-chain and data-governance findings require **C3**. Anything justifying a
spend, a go/no-go gate or a price adjustment requires **C4**. Undecidable-register claims are capped at **C2**.
Findings built from shard summaries rather than direct reads are capped at C2; summaries of summaries at C1.

Report severity and confidence as an orthogonal pair (`HIGH / C2`). Never multiply them — that lets a confident
triviality outrank an uncertain catastrophe and hides which half needs work.

## Retrieval doctrine for repositories you cannot fit in context

Repo-scale analysis is a **retrieval-and-verification problem, not a context-window problem**, and no model
release changes that: a 100k-file repository is orders of magnitude larger than any context window, effective
context collapses well before advertised limits, accuracy degrades with input length even at constant task
difficulty, and the audit questions that matter ("where is authentication bypassed?") have *low lexical overlap*
with the code that answers them — the regime where long-context performance is weakest.

Therefore:
1. **Deterministic tools run over 100% of the corpus.** The model reads only risk-weighted and hotspot strata.
2. **Grep/AST first, read ranges second, whole files last.** Cite `path#Lstart-Lend`, not "in the auth module".
3. **A plausible file path is not evidence you read the file.** Models name correct-looking paths at high rates
   with no repository access at all. Confirm every path with an actual filesystem or grep call.
4. **Order shards deterministically** (sorted, seeded) — concatenation order changes answers, so it must be
   reproducible.
5. **Adjudicate, do not invent.** For security, dependency and quality work, deterministic tooling produces
   candidates and you adjudicate them with structured evidence. Freehand vulnerability discovery from raw
   source is the failure mode that floods maintainers with plausible, invalid reports.
6. **Existence-check every named external artifact** — package, CVE id, CWE id, API, config key — against an
   authoritative source. Fabricated-but-plausible package names are a measured, repeatable model behaviour, and
   re-asking the same model does not catch the stable ones.

## Output contract

Every skill emits findings conforming to `schemas/finding.schema.json`, one coverage record per population, and
appends its execution record to the run manifest. Each finding carries: id, claim class, statement, evidence
with locators and quotes, confidence with its award basis, coverage reference, severity as impact x likelihood,
blast radius, `how_to_refute`, `disconfirming_check`, and remediation in effort **bands** (never person-days).

Every report includes: coverage bands per section, the UNKNOWN ledger, the external-validation agenda, the
integrity appendix (quarantined findings), and the run manifest. **A report with zero UNKNOWNs is
automatically suspect** — models essentially never abstain unprompted, so their absence means uncertainty was
resolved by assertion rather than by evidence.

## Stop conditions (halt and escalate, do not continue)

Live secret material · evidence of compromise · regulated personal data in fixtures, logs or dumps · licence
contamination threatening product ownership · re-verification disagreement above 10% · material you are not
authorised to read. Report location and class, never the secret value itself, and say what you deliberately
did not do.

## Prohibited outputs

Individual performance or competence evaluation · certification verdicts · dollar figures without billing
evidence · deletion recommendations without a reachability gate · a single repository "grade" without its
weighting and coverage · any sentence in an executive summary that cannot be traced to a finding id.
