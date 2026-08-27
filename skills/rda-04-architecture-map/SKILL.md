---
name: rda-04-architecture-map
description: Cited C4 L1-L3 component map with coupling metrics, ADR ledger and documented-vs-code architecture drift. Run after the entry-point map, on any repo with more than one unit.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-04"
  layer: "1-structure"
  risk_class: "MEDIUM_HARM"
  tier: "core"
  depends_on: "RDA-02, RDA-03"
---

# RDA-04 · Architecture Map

Inherits RDA-00. Parallel group A. The architecture diagram is the most-trusted and most-fabricated artifact an
audit produces: it is drawn from folder names, believed for months, and never re-checked. Every edge is cited.

## Purpose
Produce the component and container topology that the code actually expresses, with coupling metrics, the ADR
ledger, and a drift ledger comparing documented intent against cited code.

## Business value
Integration cost, team boundaries, extraction feasibility and blast radius are all read off this map. A map
derived from directory layout is confidently wrong in exactly the places that cost money to discover later.

## When to use
After RDA-02 and RDA-03, in every core profile; before onboarding, M&A, re-platforming or extraction planning.

## When NOT to use
Not for deployment topology or network layout (RDA-20), not to decide what runs in production, and never to
produce a C4 L4 code-level view — that decays faster than it can be verified and is excluded by policy.

## Inputs
`census.json` keys `units.build_manifests`, `units.containerfiles`, `units.compose_files`, `units.k8s_manifests`,
`units.iac_files`, `files.source` · `entrypoints.json` from RDA-03 · ADR directories, README, diagrams · pinned SHA.

## Procedure

1. **Enumerate units (deterministic, 100%).** Units are build or workload manifests, never folders:
   `git ls-files | rg '(package\.json|go\.mod|pom\.xml|Cargo\.toml|pyproject\.toml|.*\.csproj|build\.gradle(\.kts)?)$'`;
   `docker compose config --format json | jq -r '.services|keys[]'`; `yq -o=json '.' k8s/**/*.y*ml | jq -r
   'select(.kind|IN("Deployment","StatefulSet","CronJob","Job")) | .metadata.name'`; `helm template <chart>`
   piped through the same filter. Reconcile against `census.units.*` and explain every difference.
2. **Build the import graph per language over 100% of source.** `depcruise --output-type json src` (or
   `madge --json`) · `lint-imports` / `pydeps --no-show --show-deps` · `go list -deps -json ./...` and
   `go mod graph` · `jdeps -summary -recursive build/libs/*.jar` or `mvn -q dependency:tree` ·
   `dotnet list <proj> reference` · `cargo metadata --format-version 1`. Degraded fallback where no toolchain
   builds: `rg -n '^\s*(import|from|require|use|using|#include)\b'` plus path resolution — record the
   degradation; graphs built this way are capped at C2 and miss dynamic imports entirely.
3. **Extract cross-unit edges.** Exactly three admissible sources: (a) an import of another unit's package or
   module name, (b) a config value naming another unit (URL, DSN, topic, service name), (c) a manifest entry
   (`depends_on`, k8s `Service`, helm values, `ProjectReference`, workspace dependency). Each edge row carries
   kind, `path#Lstart-Lend`, SHA and quote. Folder adjacency and name similarity are **not** edge sources.
4. **Compute coupling deterministically.** Per module: fan-in, fan-out, instability `I = Ce/(Ca+Ce)`, longest
   path depth, and cycles — `cut -d, -f1,2 edges.csv | tr ',' ' ' | tsort > /dev/null` reports loops and
   `sccmap -v graph.dot` lists strongly connected components. Where the repo declares its own layering
   (`.importlinter`, ArchUnit tests, `deptrac.yaml`, `go-arch-lint.yml`), run it and report the violations.
5. **Identify patterns from structure, not vocabulary.** A pattern claim needs at least two cited structural
   markers: ports-and-adapters needs an interface set plus adapters implementing it; CQRS needs separated
   command and query paths; event sourcing needs an append-only store plus a replay path. One marker, or a
   directory called `hexagonal`, yields `HYPOTHESIS`.
6. **Harvest ADRs.** `git ls-files | rg -i '(doc|docs)/(adr|decisions)/|adr-[0-9]{3,}'` plus Nygard headings
   (`## Status`, `## Context`, `## Decision`) and MADR keys (`status:`, `deciders:`, `## Decision Outcome`).
   Record id, title, status, date, decision sentence, and `git log -1 --format=%aI -- <file>` as last touch.
7. **Drift pass — the reason this skill exists.** For every accepted ADR and every architectural claim in
   README or diagrams, locate the code that would implement it and record `CONFIRMED` (cited lines),
   `CONTRADICTED` (cited lines that disagree) or `UNVERIFIABLE`. The ADR is the claim under test; it is never
   evidence of what the code does. Superseded and undated ADRs are drift candidates by default.
8. **Targeted read pass.** Read the highest fan-in components, every cycle member, and boundary code where two
   units meet. Risk-weighted, cited by range, budgeted.
9. **Disconfirming pass.** For every asserted boundary, search for its bypass: direct database access from a
   second unit, a shared `utils` package importing domain code, an HTTP call that skips the declared gateway.
10. **Propose fitness functions.** For each `CONFIRMED` constraint, name the executable check that would keep
    it true — ArchUnit rule, import-linter contract, dependency-cruiser rule, deptrac ruleset, `go-arch-lint`.
    These are candidates tied to drift rows, never described as implemented.

## Outputs
`architecture.md` (C4 L1 context, L2 container, L3 component, each element cited) · `components.csv` ·
`edges.csv` (source, target, kind, locator, SHA) · `adr-ledger.csv` · `drift.csv` · `fitness-candidates.md`.

## Evidence requirements
Every node cites its manifest or workload declaration; every edge cites an import line, config line or manifest
entry with `path#Lstart-Lend`, SHA and quote. Diagrams are generated from `edges.csv`, never hand-drawn — an
element that cannot be traced back to a row does not appear in the diagram.

## Fact vs inference rules
`FACT`: a unit manifest exists; an import or manifest edge exists. `INFERENCE`: layering, pattern, or coupling
conclusions derived from the graph plus cited declarations. Ceilings on top of ES-1 §2 — this skill may **not**
assert that a component is deployed, running, or reachable (`HYPOTHESIS`; that is RDA-20 plus deploy evidence);
may not assert an edge from folder names, naming similarity or a diagram; may not convert
`census.units.build_manifests` into a count of services or "microservices"; may not treat an ADR as evidence of
current behaviour; may not map components to teams (that is RDA-29 and is role-level only).

## Confidence scoring rules
C3 for edges emitted by a language dependency tool with version and exit code. C2 for grep-derived edges
corroborated by a read plus a disconfirming search. C1 for single-import edges, degraded fallback graphs, and
any pattern claim resting on one marker. Drift rows are C2 at best until the contradicting code is read.

## Repository coverage rules
Two populations. **Units**: denominator = the reconciled output of step 1, produced by
`git ls-files | rg '<manifest-regex>' | wc -l` plus workload names from compose and k8s, cross-checked against
`census.units.build_manifests`. **Modules**: denominator = `census.files.source`; module coverage is the share
of source files present as nodes in the step-2 graph, which is the honest measure of how much of the codebase
the map describes. Report both, plus ADR coverage (ADRs adjudicated / ADRs found).

## Large repository strategy
Shard by unit, sorted, seed recorded. Steps 1-4 stay exhaustive: dependency tools scale, model reading does not.
Reduce contract: shards emit `edges.csv` rows; the merge unions edges and recomputes metrics globally, because
fan-in computed per shard is meaningless. Only steps 5, 7 and 8 are budgeted.

## Failure conditions
No buildable toolchain and no import parser (declare the degradation, cap C2) · generated code excluded by the
census but load-bearing in the graph · a monorepo where every unit shares one manifest, making unit enumeration
degenerate — say so rather than inventing boundaries · ADR directory present but unparseable.

## Escalation conditions
A `CONTRADICTED` ADR covering a security or data boundary · a cycle that spans a trust boundary identified in
RDA-03 · discovery of an undocumented component that handles money or personal data.

## External validation required
Which components are deployed and where · which are dormant · whether the documented target architecture is
still the intended one · ownership boundaries and their intended coupling.

## Known limitations
Static graphs miss runtime wiring: dependency injection, service discovery, plugin loading and reflection all
create edges no import statement shows. The map describes the repository at one commit, not the estate — a
component consuming this system from another repository is invisible until RDA-06 or RDA-37 runs.

## Success criteria
Every diagram element traces to a row in `components.csv` or `edges.csv` · no edge lacks a locator · every
accepted ADR carries a drift verdict · re-running steps 1-4 at the same SHA reproduces the same graph.

## Example prompts
- Claude Code / Cursor: "Use rda-04-architecture-map: build the import graph, extract cited cross-unit edges, and write architecture.md with C4 L1-L3 plus drift.csv."
- Codex: "$rda-04-architecture-map — enumerate units, compute fan-in and cycles, adjudicate every ADR in docs/decisions against the code."
- Antigravity / Gemini CLI: "/rda-architecture-map scope=. adr=docs/adr output=architecture.md"
