---
name: rda-13-dependency-sbom-audit
description: Generates an SBOM and the present/reachable/exploitable vulnerability split with transitive depth, maintenance and lockfile-integrity evidence; use on any repository that declares dependencies.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-13"
  layer: "2-risk"
  risk_class: "HIGH_HARM"
  tier: "core"
  depends_on: "RDA-02"
---

# RDA-13 · Dependency & SBOM Audit

Inherits RDA-00. Three counts or none: `present`, `reachable` and `exploitable` are never collapsed into one.

## Purpose
Produce an SBOM of what this repository resolves, match it against two databases, and report the three counts.

## Business value
A raw advisory count is the least decision-relevant number in due diligence: large, mostly transitive, different
tomorrow, silent about Monday. The split converts four hundred rows into the handful touching code this
repository executes.

## When to use
Every audit where the census counts at least one build manifest; mandatory before a release gate, a security
questionnaire, or an acquisition where the buyer inherits the graph.

## When NOT to use
As a patching service or a source of exploitability verdicts. Base-image scanning is RDA-20, publishing
integrity RDA-14, licence obligations RDA-15.

## Inputs
`census.json` (`units.build_manifests`, `units.lockfiles`) · every manifest and lockfile in the tree · vendored
directories · advisory database availability and timestamp · any VEX documents shipped in the repository.

## Procedure

**1. Enumerate the resolution surface and prove it locks.** Confirm the census counts on disk: `git ls-files |
rg '(package(-lock)?\.json|yarn\.lock|go\.(mod|sum)|Cargo\.lock|poetry\.lock|requirements.*\.txt|pom\.xml)$'`.
Then check each resolves: `npm ci --dry-run` · `yarn install --immutable` · `poetry check --lock` · `go mod
verify` · `bundle install --frozen`. A manifest with no satisfied lockfile resolves a *range*, not a build, and
its SBOM describes something nobody built.

**2. Generate the SBOM (deterministic, 100%).** `syft scan dir:. -o cyclonedx-json=out/sbom.cdx.json -o
spdx-json=out/sbom.spdx.json`, recording version and exit code. Where a built image exists, also `syft scan
<image-ref>`: source and built SBOMs disagree and the built one ships. **Degraded fallback:** merge ecosystem
trees (`npm ls --all --json`, `go list -m -json all`) into a component list with no purl guarantee.

**3. Match against at least two independent databases,** recording name, version, database timestamp and exit
code:
- `grype sbom:out/sbom.cdx.json -o json > out/grype.json` (capture `grype db status`; `--fail-on high` when a gate is wanted)
- `trivy fs --scanners vuln --format json -o out/trivy.json .` or `trivy sbom out/sbom.cdx.json`
- `osv-scanner scan source --recursive . --format json > out/osv.json` (older builds: `osv-scanner --recursive --format json .`)
- native, per ecosystem: `npm audit --json` · `pip-audit -f json` · `cargo audit --json` · `bundle audit check --update` · `dotnet list package --vulnerable --include-transitive` · `govulncheck ./...` (the last also gives Go reachability)
- Databases disagree on affected ranges and identifiers; report the disagreement as an attribute rather than picking the higher count

**4. The three counts, always separate.** `present` = distinct (component, version, advisory) tuples in the SBOM
match. `reachable` = a call path from repository code into the vulnerable symbol, evidenced by a call-graph tool
(`govulncheck` for Go); with no such tool, `reachable` is **UNKNOWN** — printed as UNKNOWN, never zero.
`exploitable` = preconditions met in this deployment, capped at `HYPOTHESIS` by ES-1 §2. Publishing only
`present` is inventory, not vulnerability management.

**5. Decide with SSVC.** KEV membership, EPSS, CVSS vectors and VEX statements are **attributes**; the ranking
key is the SSVC decision (`ACT` · `ATTEND` · `TRACK*` · `TRACK`) from exploitation status, exposure per RDA-03
and impact. Feed repository VEX (`grype --vex <file>`) and record which rows it suppressed — an authorless
suppression is not evidence.

**6. Depth, and who can actually fix it.** Per ACT/ATTEND row compute path and depth: `npm ls <pkg> --all` · `go
mod graph | rg '<pkg>'` · `mvn dependency:tree -Dincludes=<ga>` · `cargo tree -i <pkg>`. A direct dependency is
a version bump; a depth-four transitive is someone else's maintainer or a lockfile override.

**7. Maintenance and abandonment.** Per direct dependency record last release date, deprecation or archive flag
and maintainer count from the registry's own API (`npm view <pkg> time.modified deprecated maintainers` or the
ecosystem equivalent), never from memory. Abandonment is supply-chain risk independent of any current advisory.

**8. Existence-check, then disconfirm.** Every package name, purl and advisory id resolves at an authoritative
source (registry, OSV) before printing; fabricated-but-plausible names are a repeatable model failure that
re-asking the same model does not catch. Then query the opposite direction per ACT row: is the component in the
shipped artifact, does config already disable it.

## Outputs
`sbom.cdx.json` and `sbom.spdx.json` · `vulnerabilities.csv` (component, version, advisory ids, database,
present/reachable/exploitable, SSVC, depth, fix version) · `dependency-health.csv` · SARIF export.

## Evidence requirements
Every row cites tool, version, database timestamp, exit code and the manifest or lockfile locator
(`path#Lstart-Lend` plus commit SHA) introducing the component. Advisory ids are quoted as printed, never
retyped.

## Fact vs inference rules
`FACT`: this component version is in the SBOM; tool T reports advisory A affects it. `INFERENCE`: reachable —
only with a call-graph artifact cited. `HYPOTHESIS`: exploitable, and "this dependency is unused".
`EXTERNAL_VALIDATION_REQUIRED`: whether the vulnerable version is deployed.

## Confidence scoring rules
HIGH/CRITICAL dependency findings require **C3**: a named scanner with version and exit code plus the manifest
or lockfile citation. Scanners sharing an upstream feed are not independent. Reachability needs the call-graph
tool as its own evidence item, or the row stays `present`-only at C2.

## Repository coverage rules
Population is distinct SBOM components: `jq '[.components[].purl]|unique|length' out/sbom.cdx.json`. Report the
harsher denominator too: manifests with a lockfile over `jq '.units.build_manifests' rda-out/census.json`.

## Large repository strategy
Run syft and the matchers per build unit in parallel and merge on purl, deduplicating before counting so a
shared library is not counted forty times. Reading budget goes to ACT and ATTEND rows only. Cache SBOMs by
lockfile hash — the SBOM changes only when the lockfile does.

## Failure conditions
No network for registry or advisory lookup (record the database timestamp, cap freshness claims) · no lockfile
anywhere · vendored dependencies with no manifest · unresolvable private registries.

## Escalation conditions
A component matching a known-malicious package advisory, or an install-time script from an unexpected publisher,
halts the run and goes to incident response per ESC-1 · a KEV-listed advisory on an internet-reachable path
escalates on discovery.

## External validation required
Which version is actually deployed · whether a network-layer compensating control exists · whether the vendor
has issued a VEX statement · the patch SLA, which decides what ATTEND means in practice.

## Known limitations
Two ways this skill produces a wrong answer. **(a) The CVE flood** — four hundred transitive advisories
presented as four hundred risks, burying the two that matter; prevented by the three-count split, the SSVC key
and the rule that `present` alone may not headline. **(b) The phantom package** — a plausible name,
wrong-ecosystem homonym or invented advisory id, prevented by taking names from the SBOM and by the step 8
existence check.

## Success criteria
Three counts published separately · every HIGH/CRITICAL at C3+ with an SSVC decision · reachability stated
UNKNOWN where no call-graph tool exists · every advisory id and package name existence-checked · the SBOM
regenerates identically from the same lockfile.

## Example prompts
- Claude Code / Cursor: "Run rda-13-dependency-sbom-audit: syft SBOM, then grype and osv-scanner, and give me present/reachable/exploitable separately."
- Codex: "$rda-13-dependency-sbom-audit — build the SBOM per service, match against two databases, and rank by SSVC not CVSS."
- Antigravity / Gemini CLI: "/rda-sbom scope=. formats=cyclonedx,spdx reachability=govulncheck output=vulnerabilities.csv"
