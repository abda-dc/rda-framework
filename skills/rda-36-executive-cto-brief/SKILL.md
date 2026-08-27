---
name: rda-36-executive-cto-brief
description: Renders the two-page decision brief - verdict, basis and limits before findings, top risks, conditions, unknowns - with every sentence traced to a finding id, last, after RDA-33 and RDA-34.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-36"
  layer: "5-synthesis"
  risk_class: "HIGH_HARM"
  tier: "core"
  depends_on: "RDA-33, RDA-34"
---

# RDA-36 · Executive / CTO Brief

Inherits RDA-00. This is the only artifact most decision-makers will read, so it is the one place where a smoothed hedge
becomes a wrong decision. It is a rendering of the finding set, never separately authored prose.

## Purpose
Produce the two-page decision artifact structured per RP-1 §1: verdict, basis and its limits stated before any finding, up
to seven top risks, the conditions under which the verdict holds, and what could not be determined.

## Business value
Executives act on page one. Coverage and limits before the risk table stop a spot check being read as an assessment, and
traceability to finding ids stops the summary being more confident than the analysis it summarises.

## When to use
Last, after RDA-33 and RDA-34, whenever the audit output leaves the engineering organisation: investment committees,
acquisition decisions, launch gates, board reporting, incoming-CTO handover.

## When NOT to use
While any analysis skill is still running · when RDA-32 invalidated the run · as a standalone summariser over raw findings.
A brief without a register and a ledger behind it has nothing to trace to.

## Inputs
`risk-register.csv` and merged `findings.json` (RDA-33) · `unknowns-ledger.md` and `interview-agenda.md` (RDA-34) ·
`run-manifest.json` including the verification block, model identifier and commit pins · the RDA-01 decision statement,
which is restated verbatim so the brief answers the question that was actually asked.

## Procedure
**1. Deterministic pre-flight.** Load register, ledger and manifest. Assert: verification block present; citation resolution
1.00 or an integrity appendix plus a stated caveat; disagreement at or below 0.10; zero quarantined rows. Compute
risk-surface coverage from the coverage records. Refuse to render if the manifest is absent — an untraceable brief is worse
than no brief.

**2. Compute the verdict from gates, in this order, before any narrative is written.** `INSUFFICIENT_BASIS` if risk-surface
coverage is below the 20% ESC-1 floor, or the unknown rate exceeds 0.5, or a register (d) decision-blocking gap for this
decision is unresolved. Else `NO_GO` if a CRITICAL at C3+ is of a deal-breaking class and cannot be remediated inside the
decision's window. Else `GO_WITH_CONDITIONS` if any HIGH or CRITICAL at C3+ has a remediation path and conditions can be
stated. Else `GO`, which must state the coverage supporting it. Record which gate fired.

**3. Treat INSUFFICIENT_BASIS as a first-class outcome.** It is an expected result, not a failed run. Issuing a GO or NO_GO
on 8% risk-surface coverage is the real failure, and it is unrecoverable because a reader cannot tell a thin verdict from a
thorough one. When this gate fires, the brief states what would raise the basis, in scope terms rather than currency.

**4. Basis and its limits — before the findings.** Coverage bands per contributing skill with the risk-surface number first,
what was not examined, declared tool degradations, the commit pins and the as-of date. A reader who stops after this section
must already know the boundaries of the claim.

**5. Top risks, at most seven rows,** taken in register order and filtered to C2 and above: risk, severity and confidence as
a **pair**, blast radius, cost of inaction, first action, owning role. Seven is a ceiling, not a target; if the register has
three rows above the bar, the table has three rows.

**6. Conditions.** Render the RDA-34 external-validation agenda as the conditions under which the verdict holds, each with
the role who answers it. State expiry: findings lapse when the pinned commit is no longer an ancestor of the default branch
head, or after 90 days, whichever comes first.

**7. What we could not determine.** The decision-blocking register, summarised in the body. Never omitted, never demoted to
an appendix, never softened into "some areas warrant further review".

**8. Money.** Only where billing or contract evidence exists. Otherwise a labelled `ESTIMATE` with its inputs shown, or
silence. Deal-price and spend justifications require C4 evidence and are usually absent — say so.

**9. Release lint.** Every sentence carries at least one finding id. Sweep the adjectives — significant, robust, mature,
world-class, extensive, best-in-class — and delete each one that does not name the hotspots and cite them. Sweep for any
single-number grade and delete it unless its weighting and coverage bands are printed alongside. Emit the
sentence-to-finding-id map with the brief.

## Outputs
`executive-brief.md`, two pages maximum · the verdict record (verdict, gate that fired, risk-surface coverage at issue time,
decision restated) · the conditions list with owning roles · the sentence-to-finding-id traceability map · the attestation
block naming machine generation and the human role accountable for acceptance.

## Evidence requirements
No new evidence is created here. Support absent from the register or ledger is produced upstream by the owning skill and
re-verified by RDA-32 — never written into the brief and back-filled. The chain `sentence -> finding id -> locator + SHA ->
quote hash -> verifier result` must hold for every line.

## Fact vs inference rules
The verdict is a labelled decision recommendation derived from the step 2 gates; it is not a FACT, and it is never a
certification or compliance statement. "No blockers found" requires exhaustive risk-surface coverage; below that the only
permitted wording is "no blockers found in the N of M inspected".

## Confidence scoring rules
Nothing below C2 appears anywhere in the brief, including in passing. Each risk row shows its own pair, never an average and
never a product. The verdict itself carries a coverage band rather than a C-level, because confidence is a property of
findings and coverage is the property that qualifies a decision.

## Repository coverage rules
The headline number is **risk-surface coverage**, not file coverage. A monorepo at 80% file coverage and 10% of the
authentication surface reports 10% on page one. Every section heading carries its band in the CC-1 required language.

## Large repository strategy
One brief per decision, not per repository. Multi-repository briefs render from the RDA-37 rollup and must show the
distribution and the named worst case; a fleet average alone is not an acceptable basis for a verdict.

## Failure conditions
Register or ledger missing · manifest absent · any C1 or quarantined row surviving the filter · any sentence with no finding
id · more than seven risk rows · a brief exceeding two pages, which is rewritten rather than appended to, because the
compression is the discipline.

## Escalation conditions
A verdict would be issued below the coverage floor — emit `INSUFFICIENT_BASIS` and the scope needed to clear it ·
outstanding ESC-1 items (live secrets, evidence of compromise, regulated data in the tree, licence contamination) are
escalated before delivery and named on page one, with what RDA deliberately did not do.

## External validation required
Business impact calibration · which components are actually in production · contractual and regulatory obligations that
change the impact scale · the named role who accepts the verdict and its conditions.

## Known limitations
Two ways this skill produces a wrong answer. **The summary more confident than the analysis**: prose smooths hedges, so
"three of nineteen inspected routes lack an auth decorator" becomes "authentication is broken" — prevented by steps 5 and 9,
which bind every sentence to a finding id and its severity/confidence pair, and by the C2 filter. **The premature verdict**:
a GO or NO_GO issued on indicative coverage is typographically identical to one issued on exhaustive coverage — prevented by
step 2's gate order, which tests coverage before any risk narrative exists. Beyond those: two pages compress, and the brief
is not a substitute for the register it renders.

## Success criteria
Every sentence maps to at least one finding id · zero C1 or quarantined content · the verdict is reproducible from the gate
table alone · basis precedes findings · at most two pages and seven rows · the brief regenerates from the same finding set
without any prose being re-authored.

## Example prompts
- Claude Code / Cursor: "Run rda-36-executive-cto-brief from risk-register.csv and unknowns-ledger.md; state the verdict, put basis and limits before the findings, cap at seven risks."
- Codex: "$rda-36-executive-cto-brief — render the two-page decision brief with severity/confidence pairs and a sentence-to-finding-id map; no adjectives without findings."
- Antigravity / Gemini CLI: "/rda-exec-brief register=risk-register.csv ledger=unknowns-ledger.md output=executive-brief.md"
