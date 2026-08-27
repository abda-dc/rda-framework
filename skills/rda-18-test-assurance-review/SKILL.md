---
name: rda-18-test-assurance-review
description: Produces test inventory, executed coverage, assertion-quality and flakiness findings and the untested risk surface — use when judging release safety, refactor risk or test assurance.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-18"
  layer: "3-operations"
  risk_class: "MEDIUM_HARM"
  tier: "core"
  depends_on: "RDA-02, RDA-07"
---

# RDA-18 · Test Assurance Review

Inherits RDA-00. A coverage badge is a claim about an unknown commit made by an unknown command; this skill
reports only numbers it produced by executing the coverage tool at the pinned SHA.

## Purpose
Measure what the suite actually verifies, and name the parts of the risk surface that no failing-capable test
touches.

## Business value
"Is this safe to change?" sits behind every refactor mandate and release gate; a coverage percentage answers a
different one. What decides is *which* money-moving, entitlement and entry-point code is unguarded, and how
much of the guard is theatre.

## When to use
Every audit. Mandatory before a release gate, a large refactor, or a maintainability verdict that prices a deal.

## When NOT to use
When RDA-02 counted zero test files — that is already the finding; do not re-derive it. Test *design* critique
("are these the right cases?") and authoring missing tests are out of scope.

## Inputs
`census.json` (test/source denominators) · `strata.json` · RDA-07 critical-path modules · RDA-03 entry points ·
CI workflow files · toolchain and network availability declared in the run manifest.

## Procedure

**1. Inventory (deterministic, 100%).** Test files from the census `test` class; cases via
`rg -uuu -c '^\s*(def test_|func Test|@Test|\[Fact\]|it\(|test\()' --stats`. Classify each file unit /
integration / e2e by harness import (`rg -uuu -l 'testcontainers|playwright|cypress|selenium|supertest'`), never
by folder name. Emit the pyramid as three counts plus the unclassified remainder.

**2. Execute coverage (never read a badge).** Run the project's own tool with branch coverage on:
`pytest --cov --cov-branch --cov-report=xml -q` · `go test ./... -coverprofile=cover.out && go tool cover -func=cover.out`
· `npx jest --coverage --coverageReporters=json-summary` · `mvn -q verify jacoco:report` ·
`dotnet test --collect:"XPlat Code Coverage"` · `cargo llvm-cov --summary-only`. Record tool, version, args, exit
code, report path. **Degraded fallback:** if the suite will not run, record `TOOL_UNAVAILABLE`, publish the
failure output verbatim and hold coverage at UNKNOWN — inability to run the suite at the pin is itself a finding.

**3. Assertion quality (targeted reads).** Find tests that cannot fail: assert density per case
(`rg -uuu -c 'assert|expect\(|\.should|Assert\.'` vs step-1 counts); tautologies
(`rg -n 'assert True|assertTrue\(true\)|expect\(true\)\.toBe\(true\)'`); mock-only verification
(`rg -n 'assert_called|toHaveBeenCalled|verify\('` with no state assertion); suppression and focus
(`rg -n '@pytest\.mark\.skip|it\.skip|t\.Skip\(|@Disabled|@Ignore|\.only\(|fdescribe\('`). Cite top offenders.

**4. Flakiness signals.** Declared tolerance:
`rg -n 'rerunfailures|--reruns|jest\.retryTimes|retries:|@Flaky|RetryingTest'`. Observed instability:
`gh run list --limit 200 --json databaseId,headSha,conclusion,name` grouped by `headSha` — one commit with
differing conclusions is the only honest in-repo flake signal. Quarantine drift: `git log -S'@Disabled' --oneline`.

**5. Untested risk surface (the deliverable).** Join per-file coverage from step 2 to RDA-07 critical modules
and RDA-03 entry points. One row per risk unit: unit · covering tests · line/branch coverage · assertion
verdict from step 3. Rows with zero covering tests are the headline of this skill.

**6. Mutation escalation.** For high-stakes units the join marks "covered", test whether the coverage is real:
`mutmut run --paths-to-mutate <mod>` · `npx stryker run --mutate '<glob>'` ·
`mvn org.pitest:pitest-maven:mutationCoverage -DtargetClasses=<pkg>` · `go-mutesting ./<pkg>/...`. Named modules
only; repo-wide mutation exceeds any budget. A surviving mutant on a money path is the strongest evidence here.

**7. Disconfirming pass.** Before any "untested" claim, sweep the whole corpus for indirect coverage:
parametrised and table-driven generators, shared fixtures, contract tests, e2e specs naming the route, and
suites living in a sibling repository. Record the query and its result.

## Outputs
`test-inventory.json` (pyramid and per-framework case counts) · `coverage-executed.json` (tool, version, exit
code, per-file line/branch) · `untested-risk-surface.csv` · findings for assertion theatre, flake tolerance and
quarantine drift · one coverage record per population.

## Evidence requirements
Coverage numbers require `TOOL_OUTPUT` evidence carrying command, version and exit code. Assertion findings
require `path#Lstart-Lend` plus commit SHA and a verbatim quote of the test body. Flake findings require either
the retry-configuration line or the grouped run records — never an impression that a suite "seems flaky".

## Fact vs inference rules
FACT: file and case counts, executed coverage figures, the text of a test. INFERENCE (two independent facts):
"this module is unguarded" = zero covering lines in the executed report **and** no indirect reference from the
step-7 sweep. HYPOTHESIS: "this test is flaky", absent same-SHA divergence. UNKNOWN: coverage where the suite
would not run. Never FACT: a badge or README percentage — a `DOC` claim about an unpinned commit, reportable only
as a fidelity gap for RDA-31. Whether tests gate a merge is RDA-19 evidence; whether a gap caused an incident is
EXTERNAL.

## Confidence scoring rules
Executed coverage plus a cited test read = C3. Mutation-verified = C4. A "no test exists" claim without the
step-7 sweep = C1, unpublishable at HIGH. Coverage parsed from a stored report this run did not produce = C2
maximum, and only where the report's commit stamp matches the pin; otherwise it is stale and drops a level.

## Repository coverage rules
Two populations, both from the census. Artifact: files classed `source`, denominator
`jq '.classes.source.count' census.json`. Risk surface: units in RDA-07 plus RDA-03 entry points. Every counting
`rg` pins `-uuu` (`--no-ignore --hidden`) and is intersected with `git ls-files`, because ripgrep's defaults honour
`.gitignore`, `.ignore`, hidden-file rules and the auditor's global `core.excludesFile` — unpinned, the count is a
property of the auditor's machine; unintersected, it exceeds the census population.

## Large repository strategy
Shard by build unit (one manifest = one shard); run coverage per shard in parallel and merge with the ecosystem's own
merger (`coverage combine`, `gocovmerge`, `jacoco:merge`), never by averaging percentages across unequal denominators.
Budget guard: keep the RDA-07 shards, mark the remainder `BUDGET_EXHAUSTED`.

## Failure conditions
Suite needs unavailable services or credentials · build fails at the pinned SHA · no coverage tool present ·
tests live only in an out-of-scope repository. Each records a blind spot; none permits an estimated percentage.

## Escalation conditions
Real credentials or production data in fixtures (halt, hand to RDA-10/RDA-16) · tests that write to a live system · a
green pipeline whose test job is a no-op — an integrity issue for RDA-19 and RDA-31, escalated not filed.

## External validation required
Pass and flake rate on the protected branch (system of record: CI provider run history) · whether these suites
gate deployment (release engineering) · manual and exploratory QA coverage (QA lead) · defects attributable to
test gaps (incident tracker; MTTR and incident history are undecidable from source by construction).

## Known limitations
Two ways this skill produces a wrong answer. **(a) Import-inflated coverage** — line coverage marks a file
executed because an import ran module-level code, so an untested module reads as covered; step 2 forces branch
coverage, step 5 joins coverage to assertion verdicts, step 6 settles it by mutation. **(b) The phantom gap** —
a module exercised only by generated cases, a contract test or a sibling repo's e2e suite is declared untested;
step 7 makes the opposite-direction sweep mandatory. Coverage says nothing about oracle quality.

## Success criteria
Every coverage figure traces to a command with an exit code · every untested-surface row cites its RDA-07 or
RDA-03 unit · zero coverage numbers sourced from documentation · the risk-surface band appears in the executive
section · re-running at the pin reproduces the inventory byte-identically.

## Example prompts
- Claude Code / Cursor: "Run rda-18-test-assurance-review: execute the coverage tool, then list which RDA-07 money paths have no covering test."
- Codex: "$rda-18-test-assurance-review — inventory the suite, run branch coverage per build unit, and flag tests that cannot fail."
- Antigravity / Gemini CLI: "/rda-test-assurance scope=. mutation=services/billing output=untested-risk-surface.csv"
