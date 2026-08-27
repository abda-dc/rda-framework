---
name: rda-06-service-dependency-graph
description: Cross-service and cross-repo dependency graph from cited call sites, config and manifests - cycles, fan-in hubs, shared databases, criticality. Trigger when more than one deployable unit exists.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-06"
  layer: "1-structure"
  risk_class: "HIGH_HARM"
  tier: "conditional"
  depends_on: "RDA-03, RDA-09"
---

# RDA-06 · Service Dependency Graph

Inherits RDA-00. Conditional, activated when the census shows more than one deployable unit or the scope spans
repositories. **An edge requires a call site, a config value or a manifest entry. A folder name is not an edge.**

## Purpose
Produce the inter-unit edge set — synchronous, asynchronous and shared-data — with direction, evidence,
resolution status, cycles, fan-in hubs and a criticality ranking whose weights are published.

## Business value
Blast radius, extraction cost, incident propagation and single-point-of-failure arguments are all read off this
graph, and RS-1 caps blast-radius claims at `HYPOTHESIS` until a cited dependency graph exists. This is the
skill that raises them, and the shared-database edge it finds is usually the one nobody had drawn.

## When to use
More than one build manifest, compose service or k8s workload; any multi-repo scope; mandatory input to RDA-12,
RDA-22 and RDA-23.

## When NOT to use
A single unit with no outbound calls. Not for network topology or firewalling (RDA-20), and never to describe
how much traffic an edge carries.

## Inputs
`entrypoints.json` (RDA-03 consumer, route and gRPC rows) · the config inventory and **precedence chain** from
RDA-09, which resolves `ORDERS_URL`-style indirection · `census.json` keys `units.build_manifests`,
`units.compose_files`, `units.k8s_manifests`, `risk_surface.sql_files` · pinned SHA per repository in scope.

## Procedure

1. **Node set (deterministic, 100%).** Nodes are deployable units plus every external system named in config:
   `git ls-files | rg '(package\.json|go\.mod|pom\.xml|Cargo\.toml|pyproject\.toml|.*\.csproj)$'`,
   `docker compose config --format json | jq -r '.services|keys[]'`, k8s workloads via `yq -o=json` piped to
   `jq 'select(.kind|IN("Deployment","StatefulSet","CronJob"))|.metadata.name'`. Every node carries a manifest
   locator; databases, brokers and SaaS endpoints are nodes marked `EXTERNAL`.
2. **Synchronous edges (100% of source).** `rg -n --pcre2 -e 'https?://[A-Za-z0-9._-]+' -e
   '(requests|httpx|axios|fetch|http\.Client|HttpClient|RestTemplate|WebClient|OkHttp|Faraday)\b' -e
   'grpc\.(Dial|NewClient)|\.Invoke\(' -e '[A-Z0-9_]+_(URL|URI|HOST|ENDPOINT|ADDR)'`. For each hit resolve the
   target to a literal host, a config key resolved through RDA-09, a discovery name, or a k8s DNS name
   (`<svc>.<ns>.svc.cluster.local`). A target that does not resolve is emitted as `UNRESOLVED`, never guessed
   from the variable's name — that guess is the second failure mode this procedure exists to prevent.
3. **Asynchronous edges (100%).** Producers: `\.(publish|produce|send|emit)\(`, `sns\.publish`,
   `sqs\.send_message`, `basic_publish`, outbox writers. Consumers: the consumer rows already in
   `entrypoints.json`. Pair strictly on the literal topic, queue or exchange name, resolving names built from
   config via RDA-09. A producer with no in-scope consumer is `EXTERNAL_UNRESOLVED` plus a blind-spot record —
   it is an edge leaving the scope, never evidence that nothing consumes it.
4. **Shared-data edges (100%).** Group units by DSN or connection-string config key, database name and schema,
   then by table identifiers: `rg -n -o --pcre2 '(?i)(?:from|join|update|insert into)\s+([a-z_][a-z0-9_."]*)'
   -r '$1' | sort -u` per unit, joined across units. Two units writing the same table is the strongest coupling
   in most estates and is invisible to call-site analysis.
5. **Manifest edges.** compose `depends_on`, k8s `Service` selectors and `Ingress` backends, Helm values naming
   hosts, mesh objects (`VirtualService`, `DestinationRule`), Terraform outputs consumed as inputs elsewhere.
6. **Normalise.** Emit `edges.tsv` with tab-separated `src`, `dst`, `kind`, `locator`, `sha`, `resolution`.
   Topics and queues are nodes in their own right, so an async fan-out is never collapsed into one edge.
7. **Cycles and hubs (deterministic).** `cut -f1,2 edges.tsv | tsort > /dev/null` reports loops on stderr;
   `sccmap -v graph.dot` enumerates strongly connected components; fan-in by
   `awk -F'\t' '{c[$2]++} END{for (n in c) print c[n], n}' edges.tsv | sort -rn`. If `tsort`/`sccmap` are
   absent, compute SCCs with a scripted Tarjan pass and record the substitution.
8. **Criticality ranking (policy of this skill, published as such).** Rank each node on in-degree; whether it
   lies on a path from an externally mounted RDA-03 entry point; money or personal-data markers from the census
   strata; and absence of timeout, retry or circuit-breaker constructs at its callers. Weights are policy, not
   measurement, and ship above the ranking.
9. **Disconfirming pass.** For every edge, search for what removes it: a feature flag gating the call, a
   test-only or mock client, a deprecated adapter no longer wired. For every "isolated" or "no dependency"
   claim, search all three channels — sync, async, shared data — before asserting isolation.
10. **Emit** the graph, the unresolved list, and one coverage record per population.

## Outputs
`nodes.csv` · `edges.tsv` (with resolution status) · `service-graph.dot` plus a rendered Mermaid view ·
`cycles.txt` · `fan-in.csv` · `criticality.md` · `unresolved-targets.csv` · `dependency-coverage.json`.

## Evidence requirements
Every edge cites one admissible source with `path#Lstart-Lend`, SHA and quote: a call site, a config value, or a
manifest entry. Edges inferred from naming similarity, directory adjacency, an architecture diagram or a README
are inadmissible — they may be listed as `HYPOTHESIS` candidates for interview, in a separate file.

## Fact vs inference rules
`FACT`: a call site, config value or manifest entry exists at a locator. `INFERENCE`: an edge, when the target
resolves through cited config; the derivation names every hop. Ceilings on top of ES-1 §2 — may **not** assert
that an edge is live, deployed or carrying traffic (`HYPOTHESIS`), how much traffic it carries (`EXTERNAL`),
that a dependency does not exist (absence is `UNKNOWN` unless all three channels were swept exhaustively), or
that blast radius is bounded beyond what the cited graph shows (RS-1). Unresolved targets stay `UNRESOLVED`.

## Confidence scoring rules
C3 for edges where a call site and a manifest or config entry independently agree and a graph tool produced the
topology with version and exit code. C2 for a single admissible source plus a disconfirming search. C1 for
edges resting on an unresolved config key, and for any cross-repo edge whose far side is out of scope.

## Repository coverage rules
Two populations. **Nodes**: denominator = step 1 output, reconciled against `census.units.build_manifests` plus
compose services plus k8s workloads, with the producing command recorded. **Edge candidate sites**: denominator
= hits from steps 2-5, `rg --count-matches` summed over the client, producer, consumer and DSN pattern sets
across 100% of non-vendored files. Coverage is `resolved_edges / edge_candidate_sites`; the unresolved
remainder goes in the executive summary, not an appendix.

## Large repository strategy
Shard by unit for extraction, never for analysis: cycles and fan-in are global properties and must be computed
on the merged edge set. Steps 1-7 are deterministic and stay exhaustive. For multi-repo scope, run steps 1-6 per
repository at its own pinned SHA, then merge on node identity before step 7, and hand the result to RDA-37.

## Failure conditions
Only one node resolves (the skill does not apply) · more than a policy threshold of 25% of targets unresolved,
in which case the graph is published as a candidate graph and no criticality ranking is issued · no config
inventory from RDA-09, which makes indirection unresolvable · brokers configured entirely outside the scope.

## Escalation conditions
A cycle crossing a trust boundary identified in RDA-03 · a shared database written by units with different
authentication models · a single node on every path from every external entry point · production hostnames or
credentials hard-coded in client code (hand to RDA-10 and stop reading that file).

## External validation required
Which edges carry traffic and at what volume · whether unresolved targets exist at all · broker routing rules
and mesh policy · ownership of every shared database · which repositories exist outside the audited scope.

## Known limitations
Static extraction cannot see edges created by runtime service discovery, broker-side routing, or a gateway that
fans out. Cross-repo completeness is bounded by the repositories in scope, and a retired service still in the
tree stays a node until deployment evidence removes it.

## Success criteria
Every edge carries an admissible locator · unresolved targets counted and named · cycles and fan-in recomputed
on the merged graph · no downstream skill asserts a blast radius this graph does not support.

## Example prompts
- Claude Code / Cursor: "Use rda-06-service-dependency-graph: extract sync, async and shared-database edges with citations, resolve URLs through the RDA-09 config chain, and list cycles and fan-in hubs."
- Codex: "$rda-06-service-dependency-graph — build edges.tsv across ./services, mark unresolved targets, rank criticality with the weights printed."
- Antigravity / Gemini CLI: "/rda-service-graph scope=. config=config-inventory.json output=service-graph.dot"
