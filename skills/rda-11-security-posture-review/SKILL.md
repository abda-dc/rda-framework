---
name: rda-11-security-posture-review
description: Adjudicates scanner-produced security candidates across authn/z, injection, crypto, SSRF, deserialisation and file handling into CWE-tagged SSVC decisions; use for any security posture review.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-11"
  layer: "2-risk"
  risk_class: "HIGH_HARM"
  tier: "core"
  depends_on: "RDA-03, RDA-09"
---

# RDA-11 · Security Posture Review

Inherits RDA-00. This skill **adjudicates tool-produced candidates**, never inventing them from raw source.

## Purpose
Turn a scanner candidate set plus the real entry-point and config surface into defensible, CWE-tagged,
SSVC-decided weaknesses, each with the control that mitigates it or the gap where one should be.

## Business value
Security review fails on volume: fluent, plausible vulnerability reports transfer the whole cost of disproof
onto a reviewer who must open every one, and a queue poisoned that way is worse than no review. Adjudication
inverts the economics: the tool bounds the candidate set, the model supplies the context it lacks.

## When to use
Every audit; mandatory when the repository exposes internet-reachable routes, handles money or regulated data.

## When NOT to use
As a penetration test, an exploit-writing exercise, or a substitute for DAST against a running system. Not for
dependency CVEs (RDA-13), secrets (RDA-10), IaC posture (RDA-20) or CI permissions (RDA-14).

## Inputs
`entrypoints.json` (RDA-03) with exposure and auth attributes · RDA-09 config, precedence and feature flags ·
`census.json` and `strata.json` · available SAST engines and rule packs · framework and runtime versions.

## Procedure

**1. Load the surface first.** Read the entry-point table and config inventory before any candidate. Ranking
without exposure data is how everything in `utils/` becomes CRITICAL and the unauthenticated admin route stays
LOW.

**2. Deterministic candidate generation over 100% of source.** Run every engine available for the census
languages; record name, version, args, exit code and rule ids:
- `semgrep scan --config p/security-audit --config p/owasp-top-ten --config p/secrets --sarif --output out/semgrep.sarif --metrics=off --error` (with `--error`, findings exit 1), plus the language packs the census reports: `--config p/python` · `p/javascript` · `p/java` · `p/golang` · `p/csharp`
- `codeql database create out/db --language=<lang> --source-root .` then `codeql database analyze out/db codeql/<lang>-queries:codeql-suites/<lang>-security-extended.qls --format=sarif-latest --output=out/codeql.sarif`
- ecosystem linters: `bandit -r . -f json -o out/bandit.json` · `gosec -fmt=sarif -out=out/gosec.sarif ./...` · `brakeman -f json -o out/brakeman.json` · `eslint -f json -o out/eslint.json` with a security plugin
- CodeQL alone emits dataflow provenance, so its `codeFlows` separate a taint path from a lexical match; **degraded fallback:** with no engine installable, candidates come only from step 4's enumerable structural queries, coverage drops to PARTIAL and every finding caps at C2

**3. Normalise and deduplicate.** Merge SARIF by (rule family, file, line ±3). Take each candidate's CWE id from
the tool's own metadata (`properties.tags`, `security-severity`), never from memory, and existence-check every
id against the published CWE list before it ships. A candidate with no CWE is triaged, not invented into one.

**4. Structural candidate queries (the only other permitted generator).** Enumerable joins over census
populations, not impressions from reading: every route in `entrypoints.json` with no authn decorator or
middleware on its chain; every route with no authorisation check between handler entry and data access; crypto
call sites using algorithms the config marks legacy; `subprocess`/`exec` sinks fed by request-scoped variables;
deserialisation sinks (`pickle.loads`, `yaml.load` without `SafeLoader`, `ObjectInputStream`); outbound HTTP
built from user-controlled hosts (SSRF); upload handlers with no type or size constraint. Each query is named
and its population counted.

**5. Adjudicate one candidate at a time, with flow context.** Read the sink, the source, every hop between, the
framework's escaping behaviour, the middleware chain and the config that enables the control. Emit exactly one
verdict: `CONFIRMED_WEAKNESS` (path exists as described) · `MITIGATED` (cite the control) · `NOT_APPLICABLE`
(the rule's precondition is false here) · `UNDECIDABLE` (needs runtime or an out-of-scope artifact). Every
verdict cites evidence; `MITIGATED` without a cited control is not a verdict. **The rule that governs this
skill:** a finding exists only if a tool rule id or a named step-4 query generated it. Freehand discovery from
raw source is out of contract, because generation at scale emits plausible invalid reports faster than any
reviewer can disprove them, while adjudication with flow context supplies exactly what the tool cannot see.

**6. SSVC decision, not a CVSS rank.** Combine exposure (from RDA-03: internet-reachable, authenticated-only,
internal), exploitation status for any dependency-borne component, technical impact and mission impact into
`ACT` · `ATTEND` · `TRACK*` · `TRACK`. CVSS vectors and EPSS values ride along as attributes. A candidate with
no exposure determination is `TRACK`.

**7. Disconfirming pass, mandatory per confirmed finding.** Run and record one query in the opposite direction:
the ingress config, the base controller or filter chain, the ORM's parameterisation, a WAF rule in IaC, or a
test that proves the control fires.

## Outputs
`security-findings.json` (one per adjudicated candidate) · `candidates.csv` with every candidate and its verdict
including `NOT_APPLICABLE` — the discard list is evidence · SARIF export · the missing-control matrix keyed by
entry point.

## Evidence requirements
Every finding carries the generating rule id or named structural query, `path#Lstart-Lend` plus commit SHA, and
tool name, version and exit code. A finding with no generator provenance is deleted, not downgraded.

## Fact vs inference rules
`FACT`: tool T version V flagged rule R at locator L; the code at L does X. `INFERENCE`: an unvalidated request
value reaches this sink — only with every hop cited. `HYPOTHESIS`: **exploitable** — always, per ES-1 §2, with
no exception for obvious cases. Findings are titled as weaknesses ("unparameterised query built from request
data") rather than breaches, and carry `exploitability_assessed: false` absent a reachability artifact or PoC.

## Confidence scoring rules
HIGH/CRITICAL findings require **C3**: two independent evidence items plus a named tool with version and exit
code. Two engines sharing a rule lineage are not independent — record the `independence_group`. A candidate the
model confirms but no tool flagged is C1 and ships as a verification task.

## Repository coverage rules
Two populations. Source: `jq '.files.source' rda-out/census.json`; scanner coverage = files parsed by an engine
/ that count (parse failures are a blind spot, not a pass). Risk surface: `jq '.entrypoints|length'
rda-out/entrypoints.json`; coverage = entry points with an adjudicated auth verdict. Print the adjudication rate
beside both.

## Large repository strategy
Scanners run over everything; adjudication is the scarce resource. Rank candidates by (exposure × sink class ×
data sensitivity), adjudicate downward to the budget ceiling, then stop and print the unadjudicated remainder as
a counted blind spot. Shard by deployable unit.

## Failure conditions
No engine available and none installable · sources no engine can parse · generated code where line ranges are
meaningless · candidate volume beyond budget before the exposure ranking exists (rank first, then stop; never
adjudicate in scanner order).

## Escalation conditions
Evidence of active or historical compromise — webshell, backdoor, exfiltration path, malicious dependency —
halts the run and goes to incident response per ESC-1. An unauthenticated route touching money or regulated data
escalates on discovery, not at report time.

## External validation required
Whether a gateway, WAF or mesh enforces the control outside this repository · which routes are actually
internet-reachable · whether the path is enabled in production config.

## Known limitations
Two ways this skill produces a wrong answer. **(a) The plausible-vulnerability flood** — the model reads code
and writes a fluent injection report about an already-parameterised query; prevented by the generator rule (tool
rule id or named structural query only), the provenance field, and the C3 floor. **(b) The
unauthenticated-endpoint scare** — auth enforced by a middleware, gateway or base class nobody opened; prevented
by step 4's chain join and step 7's opposite-direction query, with `MITIGATED` requiring a cited control.

## Success criteria
Every finding traces to a generator id · none asserts exploitability · every HIGH/CRITICAL is C3+ with an SSVC
decision · the discard list is published · entry-point auth coverage is a fraction of the RDA-03 population.

## Example prompts
- Claude Code / Cursor: "Run rda-11-security-posture-review: semgrep and CodeQL first, then adjudicate each candidate against the RDA-03 route table."
- Codex: "$rda-11-security-posture-review — generate candidates, adjudicate with flow context, and emit CWE-tagged findings with SSVC decisions."
- Antigravity / Gemini CLI: "/rda-security-posture scope=. engines=semgrep,codeql output=security-findings.json"
