---
name: rda-21-observability-slo-review
description: Produces telemetry coverage per entry point, log quality and sensitive-data leakage, SLI/SLO-as-code and alert-to-runbook findings — use when assessing observability or operability.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-21"
  layer: "3-operations"
  risk_class: "MEDIUM_HARM"
  tier: "core"
  depends_on: "RDA-03, RDA-07"
---

# RDA-21 · Observability & SLO Review

Inherits RDA-00. The measure this skill exists to produce is the share of RDA-03 entry points carrying
instrumentation — everything else is context around that number.

## Purpose
Determine whether a failure on a critical path would be detected, attributed and actioned, from the code and
configuration that exist at the pinned commit.

## Business value
Undetectable failure is the multiplier on every other risk in the register: it converts a contained incident into a
prolonged one and makes remediation unverifiable. Instrumentation coverage on money and entry-point paths is also the
cheapest measurable proxy for operational maturity that a repository can supply.

## When to use
Every audit. Mandatory before a production-readiness gate (RDA-23) and before any resilience claim (RDA-22).

## When NOT to use
When the question is dashboard or alert *quality in the running system* — that lives in the observability platform,
not the repository. Do not restate RDA-16's PII inventory here; consume it.

## Inputs
`entrypoints.json` from RDA-03 · RDA-07 critical paths · RDA-16/RDA-08 sensitive-field inventory · deployment
manifests and Dockerfiles (for agent and env-var instrumentation) · alert and SLO definition files.

## Procedure

**1. Telemetry stack inventory (deterministic, 100%).** Run
`rg -uuu -l 'opentelemetry|prometheus_client|micrometer|statsd|datadog|sentry|zap|structlog|winston|slf4j'`, then
add collector configs, `OTEL_*` environment variables in manifests, and APM agents injected via Dockerfile
`ENTRYPOINT`, `JAVA_TOOL_OPTIONS` or sidecar. Record library and version per deployable unit.

**2. Entry-point join (the headline measure).** For each RDA-03 entry point determine: is a span created (count
framework auto-instrumentation, and record which middleware supplies it), is a request-scoped metric emitted, do
logs on that path carry a trace or correlation id. Emit `instrumented / total` entry points, plus the same ratio
restricted to RDA-07 money paths. Cite the middleware registration line, not the framework's reputation.

**3. Convention and propagation check.** Compare attribute names against OpenTelemetry semantic conventions
(`http.request.method`, `url.path`, `server.address`, `db.system`, `messaging.*`); confirm `service.name` and
resource attributes are set per unit; record propagation (W3C `traceparent`) across RDA-06 edges and the sampling
configuration. Check the right registry before calling an attribute non-conventional — `gen_ai.*` left core
semconv for a dedicated repository at v1.42.0. Non-conventional names are a correlation cost, not a defect.

**4. Log quality and leakage.** Structured versus ad-hoc (`rg -n 'print\(|console\.log\(|System\.out\.print'` on
non-test paths), level discipline, and sensitive-data leakage: log or exception statements interpolating fields
that RDA-16/RDA-08 classified as personal, secret or payment data, whole-request-body and header dumps, and
token-bearing URLs. Record redaction machinery where present (filters, processors, masking helpers).

**5. SLI/SLO as code.** Locate definitions: `slo.yaml`, OpenSLO, Sloth, Pyrra, `PrometheusRule`, recording and
alerting rules, monitor-as-code for the vendor in use. For each service record whether an SLI is defined, whether
a target and window exist, and whether burn-rate alerting is present. Absence in-repo is UNKNOWN, not zero: SLOs
frequently live in a vendor console.

**6. Alert-to-runbook linkage and cardinality.** For every alert rule, resolve its `runbook_url` or equivalent
annotation and report `alerts_with_resolvable_runbook / total_alerts`; an in-repo target is checkable, an
external URL is not. Then flag unbounded label values (user id, request id, email, uuid, raw path) in metric
label sets and high-cardinality histogram configurations — a metrics explosion is both a cost and an outage mode.

**7. Disconfirming pass.** Before any "not instrumented" claim, sweep the layers that instrument without
touching application code: service mesh telemetry (Envoy, Istio, Linkerd), eBPF agents, gateway access logs,
auto-instrumentation env vars, and platform sidecars in deployment manifests. Record the query and its result.

## Outputs
`telemetry-coverage.json` (per entry point: span / metric / correlated log) · `log-quality.json` including the leakage
candidate list · `slo-inventory.json` · `alert-runbook-linkage.csv` · `cardinality-risks.json` · findings and coverage
records.

## Evidence requirements
Instrumentation claims cite the registration or decoration site at `path#Lstart-Lend` with commit SHA, or the manifest
line injecting the agent. Leakage claims cite both the log statement and the field's origin. Linkage counts cite the
alert file and the annotation value; a runbook link is only "resolvable" if the target is in scope.

## Fact vs inference rules
FACT: the instrumentation call sites, alert and SLO definitions, label sets. INFERENCE: "this entry point emits no
span" = no explicit instrumentation **and** no auto-instrumentation from the step-7 sweep. HYPOTHESIS: "this log leaks
PII" where the field's content is not established by RDA-16 — a variable named `email` may hold a hashed identifier.
UNKNOWN: SLOs and dashboards held in a vendor console. EXTERNAL: whether telemetry reaches a backend, alert routing,
page volume and MTTR (APM, alerting platform, incident tracker).

## Confidence scoring rules
Cited instrumentation site plus the manifest or middleware that activates it = C3. A library listed in a dependency
manifest alone = C1: presence in `requirements.txt` is not instrumentation. Leakage findings require the field
classification from RDA-16 to reach C2. No step-7 sweep = C1 and unpublishable at HIGH.

## Repository coverage rules
Population: RDA-03 entry points, denominator `jq '.entrypoints | length' entrypoints.json`; secondary population is
alert rules, denominator `rg -uuu -c 'alert:|expr:' -g '*rules*.y*ml'` summed over files. Pin `-uuu` on every counting
invocation: ripgrep's default `.gitignore`, `.ignore`, hidden-file and global `core.excludesFile` filtering makes an
unpinned count a property of the auditor's machine. Report instrumented-entry-point coverage beside the heading and
the money-path subset separately.

## Large repository strategy
Shard by deployable unit; the join in step 2 is per unit and merges by union. Run steps 1, 4 and 6 as repo-wide
deterministic sweeps. Budget guard: order units by (external entry points, RDA-07 involvement) and mark unread units
`BUDGET_EXHAUSTED` rather than extrapolating a coverage ratio from the units that were read.

## Failure conditions
Instrumentation supplied by an out-of-scope platform chart · telemetry configured by environment variables set outside
the repository · alerting defined only in a vendor UI · no RDA-03 output, which removes the denominator.

## Escalation conditions
A log statement that writes credentials, tokens, card data or personal data to standard output or a shipped log sink
(halt that path, hand to RDA-10/RDA-16, do not reproduce the value) · telemetry exporting request bodies to a
third-party endpoint · an alert path whose destination is a decommissioned or personal address.

## External validation required
Whether emitted telemetry actually arrives (system of record: APM/observability platform) · alert routing and on-call
rotation (paging platform) · dashboard existence and use (observability platform) · error budget policy and its
enforcement (service owner) · incident detection times and MTTR (incident tracker; not in source).

## Known limitations
Two ways this skill produces a wrong answer. **(a) The invisible agent** — declaring an entry point uninstrumented
when a service mesh, eBPF agent or auto-instrumentation env var supplies spans without a code change; step 1
inventories agents and step 7 makes the mesh/manifest sweep mandatory before the claim. **(b) The name-based leak** —
flagging `logger.info(email)` as PII exposure from the identifier alone, when the value is a hash or an internal id;
step 4 requires the field's origin and RDA-16's classification, and without them the finding stays HYPOTHESIS.
Instrumentation presence also says nothing about signal usefulness.

## Success criteria
The instrumented-entry-point ratio is published with its RDA-03 denominator · every leakage finding cites both
statement and field origin · alert-runbook linkage is a counted ratio, not an adjective · zero claims about alert
volume, detection time or MTTR · re-running at the pin reproduces the coverage table.

## Example prompts
- Claude Code / Cursor: "Run rda-21-observability-slo-review: for every RDA-03 entry point tell me whether it emits a span, a metric and a correlated log, and flag any log line that could print PII."
- Codex: "$rda-21-observability-slo-review — inventory SLO definitions and alert-to-runbook linkage, and list unbounded metric labels."
- Antigravity / Gemini CLI: "/rda-observability entrypoints=entrypoints.json output=telemetry-coverage.json"
