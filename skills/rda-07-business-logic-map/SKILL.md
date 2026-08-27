---
name: rda-07-business-logic-map
description: Maps money movement, pricing, entitlement, state machines, idempotency and invariant enforcement points, plus duplicated rules. Trigger on payment, billing or permission-bearing code.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-07"
  layer: "1-structure"
  risk_class: "HIGH_HARM"
  tier: "conditional"
  depends_on: "RDA-03, RDA-08"
---

# RDA-07 · Business Logic Map

Inherits RDA-00. Conditional, activated by payment, billing, entitlement or workflow indicators in the census.
**A function called `calculate_discount` is a name, not a rule. A rule exists where it is enforced.**

## Purpose
Locate, cite and state the domain rules that carry money and entitlement, with their enforcement points, their
idempotency and concurrency controls, and every place the same rule is implemented more than once.

## Business value
The expensive defects in diligence are not crashes, they are silent value leaks: a discount applied twice, a
refund path with no idempotency behind a retrying client, an entitlement enforced only in the browser.

## When to use
When the census shows payment, billing, ledger, pricing, entitlement or workflow indicators; before repricing,
a rewrite, a migration of a billing system, or an M&A review of a revenue-bearing product.

## When NOT to use
Infrastructure-only repositories. Not to decide whether a calculation is correct — that needs executed tests
(C4) — and never to decide whether a rule matches business intent, which is an interview, not a read.

## Inputs
`entrypoints.json` (which entry points reach which rules) · RDA-08 schema and constraint inventory ·
`census.json` keys `risk_surface.personal_data_files`, `risk_surface.authz_files`, `risk_surface.sql_files`,
`files.source`, `files.test` · domain glossary or product docs if any exist · pinned SHA.

## Procedure

1. **Rule-surface sweep (deterministic, 100% of non-vendored source).** Four `rg -n --pcre2` families, each
   emitting counts and a file list that becomes a stratum: **money** —
   `(stripe|adyen|braintree|paypal|payout|refund|chargeback|invoice|ledger|journal|balance|settlement)` and
   `\b(amount|price|total|fee|tax|discount|currency)\b`; **entitlement** —
   `(authoriz|can_|is_allowed|has_permission|@PreAuthorize|require_role|casbin|opa|rego|pundit|cancan)`;
   **state** — `(status|state)\s*[:=]` and `(transition|state_machine|aasm|xstate|workflow)`; **idempotency** —
   `(idempotenc|dedup|exactly.?once|ON CONFLICT|ON DUPLICATE KEY|FOR UPDATE)`.
2. **Money-type sweep.** `rg -n --pcre2 -e '(float|double)\s+\w*(amount|price|total|balance)' -e
   '(amount|price|total)\s*:\s*(float|number)'`, plus `ast-grep run -l <lang> -p '$X * $RATE'` over the money
   stratum for rounding-free arithmetic. Binary floating point on money is a defect class, but every hit still
   ships with its own locator.
3. **Enforcement-point triangulation — the core rule of this skill.** For each candidate record up to four
   enforcement points: (a) call sites reachable from an `entrypoints.json` row, (b) the persistence effect
   (write path and table, from RDA-08), (c) a database constraint — `CHECK`, `UNIQUE`, FK, trigger — (d) a test
   asserting it. A candidate with **zero** enforcement points is `HYPOTHESIS`, whatever its name suggests.
4. **State machines.** Extract states from enums and constants, and transitions from assignment sites:
   `rg -n -o --pcre2 '(?i)\b(status|state)\s*=\s*[A-Za-z_."\x27]+'`. Build the observed transition set per
   entity and flag: transitions with no guard, terminal states that are re-entered, and any state written by
   more than one unit (join with the shared-data edges from RDA-06).
5. **Idempotency and concurrency matrix.** Per money-moving entry point, record the mechanism that exists —
   idempotency key, unique constraint, dedupe table, `SELECT ... FOR UPDATE`, version column, outbox — with
   locators. A broker's "exactly once" claim is never accepted as the mechanism.
6. **Duplicate-rule detection (deterministic, over the strata).** `jscpd --min-tokens 50 --reporters json` or
   `pmd cpd --minimum-tokens 100 --dir . --language <lang>` across the money and entitlement strata; then
   extract literals near rule identifiers with `rg -n -o --pcre2
   '(?i)(rate|percent|threshold|limit|fee)\W{0,3}\K[0-9.]+'` and group by value. Two implementations of one
   rule that disagree is this skill's highest-value finding.
7. **Cross-tier duplication.** Compare each server rule with client, mobile, SQL and stored-procedure
   implementations of the same decision, citing each side. Client-only enforcement is a finding, not a note.
8. **Disconfirming pass.** Before "no idempotency" or "no permission check", search database constraints,
   middleware, broker configuration and framework defaults. Before "this is the pricing rule", search for every
   other writer of the same field. Record both queries and their results.
9. **Targeted read and statement.** Read the top-ranked rules and write each as a falsifiable sentence —
   inputs, decision, effect — with the locator for each clause. Rules that cannot be stated falsifiably are
   reported as `UNKNOWN`, not paraphrased.
10. **Emit** the rule inventory, matrices and coverage records.

## Outputs
`business-rules.csv` (rule id, falsifiable statement, enforcement points, locators, reaching entry points,
duplication group) · `state-machines.md` · `idempotency-matrix.csv` · `duplicate-rules.csv` · coverage record.

## Evidence requirements
Every rule row cites at least one enforcement point as `path#Lstart-Lend` with SHA and quote, and names the
entry point that reaches it. Duplication rows cite both implementations. A rule stated without an enforcement
locator is a paraphrase of an identifier and is rejected.

## Fact vs inference rules
`FACT`: this code path writes this field under this condition, at a locator. `INFERENCE`: the rule statement,
derived from cited enforcement points. Ceilings on top of ES-1 §2 — may **not** assert that a rule is *the*
business rule without at least one cited enforcement point; may not infer semantics from identifier or table
names; may not assert a calculation is correct (that needs an executed test, C4); may not assert alignment with
business intent (`EXTERNAL_VALIDATION_REQUIRED`, product or finance owner); may not quantify leakage or revenue
impact (`EXTERNAL`, BSR-10); may not declare which of two duplicate implementations is authoritative.

## Confidence scoring rules
C3 where a rule is corroborated by code, a database constraint from RDA-08, and a passing test identified by
name and file. C2 where two independent enforcement points agree and a disconfirming search was recorded. C1
for single-site rules, name-driven candidates, and any rule whose data lives outside the repository.

## Repository coverage rules
Two populations. **Rule candidate sites**: denominator = union of the step-1 family hit counts from
`rg --count-matches -f patterns/<family>.txt` over the non-vendored source list, cross-checked against
`census.risk_surface.authz_files` and `census.risk_surface.sql_files`. **Money-bearing entry points**:
denominator = `entrypoints.json` rows whose handler sits in the money stratum — the risk-surface number that
goes in the executive summary. Report triangulated rules over candidate sites.

## Large repository strategy
Shard by bounded context, sorted, seeded. Steps 1, 2 and 6 stay exhaustive over the strata — copy-paste
detection is worthless on a sample, since the second copy is what a sample misses. Budget steps 3, 7 and 9 by
money exposure; shards emit rows and the merge groups duplicates globally.

## Failure conditions
Rules stored as data (pricing tables, CMS content, rules-engine payloads, flag values) — a blind spot with the
store named · no test suite, removing enforcement point (d) · a rules-engine DSL with no parser available.

## Escalation conditions
Money movement reachable from an entry point with no guard marker · a refund, payout or credit path with no
idempotency mechanism · entitlement enforced only in client code · real personal or payment data in fixtures
(halt that path, hand to RDA-16 per ESC-1).

## External validation required
The intended rule for each cited implementation · which duplicate is authoritative · rounding and currency
policy · whether flagged state transitions occur in practice · who owns each rule.

## Known limitations
Rules encoded in data are invisible to source analysis, and mature billing systems keep many of them there.
This skill maps the rules the code enforces, not the rules the business believes it enforces; the gap between
those sets is the finding, and only an interview closes it.

## Success criteria
Every rule row carries an enforcement locator and a reaching entry point · every money entry point has an
idempotency determination or an explicit `UNKNOWN` · duplicate groups are cited on both sides.

## Example prompts
- Claude Code / Cursor: "Use rda-07-business-logic-map: find money-movement and entitlement rules, triangulate enforcement points against the schema, and list duplicate implementations."
- Codex: "$rda-07-business-logic-map — build the idempotency matrix for every refund and payout entry point in ./services, citing constraints and tests."
- Antigravity / Gemini CLI: "/rda-business-logic scope=. strata=money,entitlement output=business-rules.csv"
