---
name: rda-24-performance-scalability-review
description: Produces algorithmic and I/O hot spots on cited paths, horizontal-scaling blockers, concurrency and resource-ceiling findings with no unmeasured numbers — use before load growth or scaling work.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-24"
  layer: "3-operations"
  risk_class: "HIGH_HARM"
  tier: "conditional"
  depends_on: "RDA-07, RDA-08"
---

# RDA-24 · Performance & Scalability Review

Inherits RDA-00. **Absolute rule: no throughput, latency or capacity number without a benchmark or telemetry
artifact.** Unmeasured performance claims are `EXTERNAL_VALIDATION_REQUIRED`, never findings.

## Purpose
Identify structural limits — algorithmic, I/O, stateful and resource-bounded — that constrain this system as load
grows, using cited code paths rather than intuition about what is slow.

## Business value
Scaling failures are expensive because they surface at the worst moment and are usually architectural, not tunable.
Naming the blockers that prevent adding instances — in-process state, singleton locks, local disk — is worth more than
any speculative latency figure, and it survives contact with a real load test.

## When to use
When growth, migration, a scaling incident or a capacity decision is in scope, and RDA-07 and RDA-08 have run.

## When NOT to use
As a substitute for load testing, or to produce a performance number for a business case. If a number is required and
no artifact exists, the correct output is the benchmark to run, not an estimate.

## Inputs
RDA-07 critical paths · RDA-08 query, index and transaction findings · RDA-03 entry points · RDA-02 hotspots · RDA-20
declared resource limits · any benchmark, load-test or profile artifacts present in the repository.

## Procedure

**1. Select the surface (do not scan everything).** Paths = RDA-07 critical paths ∩ RDA-03 entry points, ordered
by RDA-02 hotspot rank (`scc --hotspots`, `--coupling` and `--by-author` give the same churn×complexity ranking
deterministically from history); record the selection and rationale in the coverage record. A review that reads
the whole tree spends its budget on code nobody calls under load.

**2. Algorithmic hot spots (rule-driven).** `semgrep --config p/performance --json` (engine LGPL-2.1, but the
registry rulesets moved to the non-OSI Semgrep Rules License v1.0 in December 2024 — clear it with the engagement
first), `ast-grep` patterns, or linters (`ruff`, `golangci-lint`, `pmd`). Hunt nested iteration over request- or
data-sized collections, membership tests inside loops, sorting in loops, recursive fan-out, string building in
loops, whole-collection loads and nested-quantifier regexes. Each hit is a candidate until read.

**3. I/O hot spots.** Join RDA-08: N+1 access via lazy loading in loops, per-item network or storage calls,
queries without `LIMIT`, `SELECT *` on wide tables, filters on unindexed columns, unbatched writes, synchronous
external calls inside request handlers, repeated identical reads with no cache. Chattiness cites RDA-06 edges.

**4. Horizontal-scaling blockers (highest-value output).** In-process session or cache used as source of truth
(`MemoryStore`, module-level dicts, static maps), local filesystem writes, embedded databases on local volumes,
in-process schedulers without leader election, local-only rate limiting, singleton locks guarding shared
resources, sticky-session assumptions (`sessionAffinity: ClientIP`), socket state without a broker.

**5. Concurrency model.** Record the model per unit (threads, async loop, processes, actors) and declared worker
counts (`WEB_CONCURRENCY`, gunicorn/uvicorn, `GOMAXPROCS`, thread-pool sizes). Flag blocking calls on async
loops (`time.sleep`, synchronous drivers under `asyncio`), deadlock-permitting lock ordering, shared mutable
state crossing threads.

**6. Resource ceilings (declared arithmetic only).** Extract pool sizes, `max_connections`, `maximumPoolSize`,
pgbouncer settings, container CPU/memory limits versus JVM heap and GC flags, thread-pool bounds and upload caps.
Where both operands are declared, `pool_size × replicas` versus the database connection limit is a legitimate
INFERENCE with both citations — the only capacity arithmetic permitted here.

**7. Pagination and unbounded results.** List endpoints without limit/offset/cursor, `findAll()` and `.all()` on
user-facing paths, absent maximum page size, GraphQL without depth or complexity limits, exports that materialise
a full result set in memory.

**8. Measure or abstain, then disconfirm.** If benchmarks exist (`go test -bench`, `pytest-benchmark`, JMH, k6),
run them, cite the artifact and mark C4; profiles are captured as `profile.proto` (`go tool pprof` has no `-json`
output flag). Otherwise every quantitative statement is
`EXTERNAL_VALIDATION_REQUIRED`. Before writing a hot-spot finding, check the opposite: an eager-loading strategy
declared elsewhere (`selectinload`, `JOIN FETCH`, `Include`), a cache in front, a bounded input, or an index
added in a later migration. Record the query and result.

## Outputs
`hotspots.json` (path, pattern, citation, class) · `scaling-blockers.md` (blocker, unit, what it prevents) ·
`resource-ceilings.csv` (declared limits and derived arithmetic) · `benchmarks.json` · findings and coverage records.

## Evidence requirements
Every hot spot cites `path#Lstart-Lend` with commit SHA and quotes the construct. Ceiling arithmetic cites both
operands. Any number describing time, throughput or capacity requires `TEST_RESULT` or `RUNTIME_ARTIFACT` evidence
produced in this run — no exceptions, including "roughly", "on the order of" and "typically".

## Fact vs inference rules
FACT: the code construct, the declared limit, an executed benchmark result. INFERENCE: "this path cannot scale
horizontally" = in-process state on the path **plus** absence of an external store. HYPOTHESIS: "this loop is a
bottleneck" without a profile. EXTERNAL: request rates, latency percentiles, headroom and "will it scale to N" (APM,
load-test platform, cloud metrics). A complexity class is a fact about the algorithm, never a latency claim.

## Confidence scoring rules
Cited construct plus a corroborating rule-engine hit = C3. Benchmark or profile artifact = C4, required for spend or
go/no-go decisions. Rule-engine output alone, unread = C1 and unpublishable. Every quantitative statement is capped at
C2 and carries an `external_validation.question` naming the measurement that settles it.

## Repository coverage rules
Population: the step-1 surface, denominator `jq '[.critical_paths[].files[]] | unique | length'` over RDA-07 output,
reconciled with the census source count. Report surface coverage and the share of externally reachable entry points
reviewed; a list drawn from 5% of paths is INDICATIVE and says so.

## Large repository strategy
Shard by deployable unit; run rule engines repo-wide and reads only on the step-1 surface. Ceiling arithmetic is
performed in the reduce step, where replica counts from RDA-20 and pool sizes from each shard meet. Budget guard: keep
entry points and money paths, mark the rest `BUDGET_EXHAUSTED` rather than sampling randomly.

## Failure conditions
No RDA-07 output, which removes the surface definition · benchmarks that require unavailable infrastructure ·
performance behaviour dominated by a third-party service · dynamically dispatched or generated code that static rules
cannot follow · JIT, caching and query-planner effects that source cannot express.

## Escalation conditions
An unbounded result path reachable without authentication (a denial-of-service vector; hand to RDA-11) · a ReDoS
candidate on unauthenticated input · a scaling blocker on a payment path · declared pool size times replicas exceeding
the declared database connection limit.

## External validation required
Throughput, latency percentiles and error rates (APM) · load-test results and profile (performance engineering) ·
database and cache utilisation (cloud metrics) · capacity-related incident history (incident tracker).

## Known limitations
Two ways this skill produces a wrong answer. **(a) The invented number** — a plausible latency or throughput figure
attached to a real construct, which reads as authoritative and is fabrication; the absolute rule, evidence requirement
and C2 cap block it, and step 8 offers the benchmark instead. **(b) The false N+1** — a loop that looks per-item but
is eager-loaded, cached or bounded to a few rows; step 8's disconfirming read of the fetch strategy is mandatory
before the finding is written. Static analysis cannot see the query planner; index findings stay with RDA-08.

## Success criteria
Zero unmeasured performance numbers · every hot spot cites a construct and its disconfirming check · scaling blockers
name what they prevent · ceiling arithmetic shows both operands · surface selection and coverage band published.

## Example prompts
- Claude Code / Cursor: "Run rda-24-performance-scalability-review on the RDA-07 checkout path: find scaling blockers and unbounded queries, and do not estimate latency."
- Codex: "$rda-24-performance-scalability-review — list in-process state, singleton locks and pool-size versus replica arithmetic per service."
- Antigravity / Gemini CLI: "/rda-performance surface=critical-paths.json bench=run output=scaling-blockers.md"
