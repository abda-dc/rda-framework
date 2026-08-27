---
name: rda-22-resilience-blast-radius
description: Produces failure domains, single points of failure, a timeout/retry/backoff/circuit-breaker inventory and cited blast radius per failure — use when multiple services or shared datastores exist.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-22"
  layer: "3-operations"
  risk_class: "HIGH_HARM"
  tier: "conditional"
  depends_on: "RDA-06, RDA-20"
---

# RDA-22 · Resilience & Blast Radius

Inherits RDA-00. **A blast-radius claim requires a cited dependency graph from RDA-06.** Without those edges the
statement is HYPOTHESIS, however confident it sounds — this is the ES-1 undecidable-register rule for this skill.

## Purpose
Enumerate failure domains, identify what fails alone and what fails together, and inventory the controls that bound
the propagation.

## Business value
Executives buy or ship on the answer to "what does one failure take down". A component list does not answer it; a
cited propagation path does. This is also where remediation leverage is highest, because a single missing timeout can
be the difference between a degraded call and a saturated service.

## When to use
More than one deployable unit, any shared datastore, any external dependency on a revenue path, or any input to
RDA-23's readiness gate.

## When NOT to use
Single-process applications with no external dependencies, and any scope where RDA-06 has not run — without the graph
this skill can inventory controls but must not publish blast radius.

## Inputs
RDA-06 dependency graph (edges with sync/async labels and their evidence) · RDA-20 declared topology (replicas, zones,
quotas, network policy) · RDA-03 entry points · RDA-09 config for timeout and pool settings.

## Procedure

**1. Failure-domain enumeration (deterministic).** From RDA-20 declarations and RDA-06 nodes, record per unit:
replica count, `PodDisruptionBudget`, anti-affinity, zone/region spread, leader election, singleton jobs, and
which datastore, queue, cache, secret store and identity provider it shares with other units. A shared component
is one domain regardless of how many services front it.

**2. SPOF candidates.** Rank nodes by in-degree from the RDA-06 graph and mark those with no alternate path;
add `replicas: 1`, `desired_count = 1`, single-AZ subnets, single writer databases, one queue broker, and
shared-library or shared-credential chokepoints. Thresholds used for ranking are **policy**, stated as such, and
set at scope time — they are not measurements.

**3. Control inventory (100% sweep).** Timeouts: `rg -uuu -n 'timeout|WithTimeout|deadline|connect_timeout'`
and, more importantly, outbound calls with **no** timeout argument (`requests.get(` without `timeout=`,
`http.Client{}` zero value, default `fetch`, `RestTemplate` without a factory). Retries: tenacity, backoff,
resilience4j, Polly, `retryPolicy`, mesh `retries`. Breakers: resilience4j, gobreaker, opossum, Polly, Envoy
outlier detection. Bulkheads, rate limits, dead-letter queues and idempotency keys (join RDA-07).

**4. Dangerous-combination hunt (targeted reads).** Name each occurrence with a citation: retry without backoff
or jitter; retries stacked at two or more layers, multiplying attempts; outbound call with no timeout inside a
request handler; unbounded queue or channel (`Queue()`, `LinkedBlockingQueue()`); breaker with no fallback;
liveness probe that fails on a dependency outage, turning a downstream fault into a restart storm.

**5. Blast radius per failure.** For each domain from step 1, walk the RDA-06 closure and list dependent units,
separating synchronous (immediate) from asynchronous (deferred or degraded) propagation, and noting where step-3
controls interrupt the path. Every row cites the graph edges it used. A row with no citable edge is published as
HYPOTHESIS with the exact artifact that would settle it.

**6. Degraded fallback.** If RDA-06 is unavailable or partial, restrict output to the control inventory and the
declared-topology facts, mark blast radius `UNKNOWN`, and record the gap. Do not reconstruct a dependency graph
from folder names or service naming conventions — that is the framework's canonical fabrication.

**7. Disconfirming pass.** Before any "no timeout / no retry / no breaker" claim, sweep the layers that supply
them outside application code: service-mesh `VirtualService` and Envoy policies, API gateway and load-balancer
idle timeouts, database driver defaults, sidecar proxies and platform libraries. Record the query and result —
and note the inverse risk, since a mesh retry plus an application retry is amplification, not redundancy.

## Outputs
`failure-domains.json` · `spof-candidates.csv` (with graph evidence) · `resilience-controls.json` (one row per call
site) · `blast-radius.md` (one row per domain, edges cited) · findings and coverage records.

## Evidence requirements
Control findings cite the call site or configuration at `path#Lstart-Lend` with commit SHA. Topology findings cite the
IaC or manifest line from RDA-20. Blast-radius rows cite RDA-06 edge ids, and each edge must itself be backed by a
call site, config value or manifest entry — never by a name.

## Fact vs inference rules
FACT: a timeout value, a replica count, a retry decorator, a graph edge's evidence. INFERENCE: "failure of the shared
Postgres instance stops checkout" = cited edges from checkout to that instance **plus** absence of an interrupting
control. HYPOTHESIS: blast radius without cited edges; any claim that a failure "will" occur. EXTERNAL: incident
history, real MTTR, observed failure rates, and whether declared multi-AZ spread exists in the account (systems of
record: incident tracker, cloud console, APM). None of these are derivable from source.

## Confidence scoring rules
Blast radius with cited RDA-06 edges plus RDA-20 topology = C2, the ceiling for undecidable-register claims, and
carries an `external_validation.question`. A control finding with a cited call site and a corroborating config value =
C3. Propagation claims without edges are C1 and publish as verification tasks, not findings.

## Repository coverage rules
Two populations. Outbound call sites, denominator `rg -uuu -c 'requests\.|fetch\(|HttpClient|grpc\.'` summed over
files and reconciled against the census risk-surface strata; `-uuu` is mandatory because ripgrep's default ignore,
hidden-file and global `core.excludesFile` handling makes counts vary by auditor. Deployable units, denominator
`jq '.structural.build_manifests' census.json`. "No timeouts anywhere" requires EXHAUSTIVE selection.

## Large repository strategy
Shard by deployable unit and emit per-unit control records; blast radius is computed in the reduce step, over the
merged graph, never per shard — a shard cannot see its own downstream. Budget guard: order units by (externally
reachable, RDA-07 involvement, in-degree) and mark the remainder `BUDGET_EXHAUSTED`.

## Failure conditions
RDA-06 missing or below BROAD coverage (blast radius suppressed) · dependencies resolved at runtime through service
discovery with no static evidence · controls configured in an out-of-scope platform chart · dynamic client
construction static analysis cannot attribute. Never substitute a tags index for a call graph: universal-ctags emits
definitions only, reference tags are opt-in and, in its own words, "only a few parsers currently utilize it".

## Escalation conditions
A single database or credential shared by units with different trust levels · an unbounded queue on an
internet-reachable path · a retry storm pattern on a payment or fulfilment path · a liveness probe wired to a
downstream dependency in a production manifest — each is reported immediately, not held for the final report.

## External validation required
Actual redundancy in the account versus declared (cloud console) · whether the shared datastore is genuinely shared in
production (platform team) · historical failure propagation (incident tracker) · dependency criticality from the
business (service owner) · tested failover behaviour (DR test records).

## Known limitations
Two ways this skill produces a wrong answer. **(a) The mesh-supplied control** — declaring "no timeout" from
application code when the mesh, gateway or driver default supplies one; step 7 makes that sweep mandatory and step 3
records where the control lives. **(b) The name-derived graph** — inferring that `orders` calls `payments` from folder
adjacency; step 5 requires cited edges and step 6 forbids reconstruction, so a missing graph downgrades output instead
of inviting invention. A missing edge is never proof of independence.

## Success criteria
Every blast-radius row cites RDA-06 edge evidence · every control finding names the layer that supplies or omits the
control · no propagation claim exceeds C2 · the dangerous-combination list is exhaustive over the inspected call-site
population · re-running at the pin reproduces the control inventory.

## Example prompts
- Claude Code / Cursor: "Run rda-22-resilience-blast-radius using the RDA-06 graph: list SPOFs, outbound calls with no timeout, and what each failure takes down."
- Codex: "$rda-22-resilience-blast-radius — inventory timeouts, retries, backoff and breakers per call site and flag retry-without-backoff on money paths."
- Antigravity / Gemini CLI: "/rda-resilience graph=service-graph.json iac=infra/ output=blast-radius.md"
