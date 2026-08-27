# RDA Reporting & Traceability Standard (RP-1 / TR-1)

## 1. Two audiences, one evidence base

Executive and technical outputs are **renderings of the same finding set**, never separately authored prose.
Every executive sentence must trace to finding ids; the linter fails an executive claim with no `id` behind it.
This is what prevents the classic failure where the summary is more confident than the analysis.

### Executive layer (RDA-36) — 2 pages maximum
1. **Decision** — go / go-with-conditions / no-go / insufficient basis. One line.
2. **Basis and its limits** — coverage bands and what was not examined, stated before the findings.
3. **Top risks** — <=7 rows: risk, severity/confidence pair, blast radius, cost of inaction, first action, owner role.
4. **Conditions** — what must be true before the decision holds (the external-validation agenda).
5. **What we could not determine** — the UNKNOWN ledger, summarised. Never omitted, never an appendix.
6. **Money** — only where billing or contract evidence exists; otherwise ranges labelled ESTIMATE with inputs shown.

Forbidden in the executive layer: adjectives without findings ("world-class", "significant technical debt"),
scores without denominators, findings below C2, and any single-number repository grade.

### Technical layer
Full finding records, evidence appendix, coverage tables, tool versions and raw outputs, reproduction commands,
and the integrity appendix (quarantined findings and why).

### Machine layer
`findings.json`, `coverage.json`, `risk-register.csv`, `run-manifest.json`, plus SARIF export for security
findings so they land in existing code-scanning dashboards instead of a document nobody re-opens.

## 2. Traceability chain (TR-1)

`executive sentence -> finding id -> evidence locator + commit SHA -> quote hash -> verifier result -> manifest`

Every link is machine-checkable. An audit whose chain breaks at any link is republished or withdrawn, not patched.

## 3. Reproducibility, honestly scoped

RDA separates two layers and claims different guarantees for each:

| Layer | Content | Guarantee |
|---|---|---|
| Deterministic | census, tool runs, git queries, schema extraction | Byte-reproducible at pinned commits with pinned tool versions |
| Interpretive | model-authored findings, prioritisation, narrative | **Not** byte-reproducible. Guaranteed only at the level of: same evidence set, same undecidable register, same class ceilings |

Therefore reproducibility is asserted as: *"the deterministic layer reproduces exactly; the interpretive layer
is expected to vary in wording and ordering, and is checked by the re-verification sample rate, not by diffing prose."*
Claiming full reproducibility of an LLM audit is itself an unsupported claim.

Every published report carries: run id, commit pins, model identifier, skill versions, prompt digest, tool
inventory with versions, coverage table, verification statistics, and an explicit AI-generated attestation
naming the human accountable for acceptance.

## 4. Explainability requirements

For every finding a reader must be able to answer, without asking the agent: what did it look at, what did it
not look at, what would change this conclusion, who decides, and how old is it. If any of those five is
unanswerable from the artifact, the artifact is incomplete.

## 5. Retention and expiry

Findings expire when the pinned commit is no longer an ancestor of the default branch head, or after 90 days,
whichever is sooner. Expired findings may be cited historically but must not be presented as current state.
Re-running the deterministic layer against a new commit and diffing the finding set is the supported refresh
path — cheaper than a fresh audit and it produces a trend, which is what boards actually want.
