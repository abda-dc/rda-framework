---
name: rda-02-repo-census
description: Deterministic repository inventory producing every denominator the audit later divides by - languages, LOC, services, risk-surface counts, exclusions. Run after scoping, before any analysis.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-02"
  layer: "0-kernel"
  risk_class: "HIGH_HARM"
  tier: "core"
  depends_on: "RDA-01"
---

# RDA-02 · Repository Census

Inherits RDA-00. This skill is the reason the rest of the framework can say "we examined 41 of 512" instead of
"we reviewed the codebase". **No model judgement belongs in this skill.** Every number is produced by a command
whose output is reproducible at the pinned commit.

## Purpose
Produce the Repository Fact Base: the counted, deterministic ground truth about what exists.

## Business value
Coverage claims are the first thing a hostile reader attacks. A census makes them defensible, and it is what
converts "the model looked at some files" into a measurable sample of a known population.

## When to use
Always, first, before any other analysis skill. Re-run when the pinned commit changes.

## When NOT to use
Never skipped. If tools are unavailable, run the degraded variant and record the degradation — do not estimate.

## Inputs
Pinned repositories from RDA-01.

## Procedure

**1. Repository facts.** For each repo: `git rev-parse HEAD`, default branch, first and last commit dates,
commit count, contributor-identity count, submodules, LFS objects, repository size, tag/release count.

**2. File population.** Total tracked files; per-language file and line counts (`scc` or `cloc` or `tokei`,
whichever is present — record which); binary and generated files; vendored paths. Classify each path exactly
once into: `source` · `test` · `config` · `infrastructure` · `docs` · `generated` · `vendored` · `binary`.
Generated and vendored files are excluded from quality denominators but **included** in licence and dependency
denominators — the same file can be out of scope for one question and in scope for another.

**3. Structural units.** Count build manifests (`package.json`, `pom.xml`, `go.mod`, `*.csproj`, `Cargo.toml`,
`pyproject.toml`, `build.gradle`), containerfiles, k8s manifests, IaC roots, CI workflow files, migration
directories, and lockfiles. These counts define "how many services" — never infer service count from folder names.

**4. Risk-surface indicators.** Counted, not judged: files matching route/handler declarations per framework;
files importing crypto libraries; files referencing personal-data field names; SQL/ORM call sites; files
touching filesystem, subprocess or deserialisation APIs. These become the risk-weighted strata for every later
skill.

**5. Change topology.** Commits per path over the last 12 and 24 months, distinct author identities per path,
and the hotspot ranking (change frequency x size). This is the sampling frame for RDA-26/28/29.

**6. Emit denominators.** Write `census.json` with every count and the exact command that produced it. Every
later coverage record must reference a denominator from this file by key.

Run `scripts/rda_census.sh <repo>` to perform steps 1-5 with graceful degradation.

## Outputs
`census.json` (counts + producing commands + tool versions) · `exclusions.md` · `strata.json` (risk-weighted
sampling frame) · `hotspots.csv`.

## Evidence requirements
Every number carries its command, tool name and version, and exit code. Nothing in this skill is an estimate.
A count that could not be produced is `null` with a reason, never a guess.

## Fact vs inference rules
All output is `FACT`. Any statement about what the counts *mean* belongs to another skill. "41 build manifests"
is census; "41 microservices" is RDA-04 and requires deployment evidence.

## Confidence scoring rules
C3 by construction (deterministic tool + reproducible command). Degraded runs (missing tools, shallow clone)
drop to C2 and must say which counts are affected — a shallow clone silently breaks history counts.

## Repository coverage rules
Coverage is 1.0 over tracked files by definition, or the census is invalid. If `.gitignore`d or untracked
material matters, say so explicitly as a blind spot.

## Large repository strategy
Census is cheap and must remain exhaustive: it is line-counting, not reading. On 500k-file monorepos run it per
top-level unit in parallel and merge; cache results keyed by commit SHA so re-runs are instant.

## Failure conditions
Shallow clone (history counts invalid) · no line-counting tool (fall back to `git ls-files` + `wc -l`, record
it) · submodules not initialised (record as blind spot; do not silently count the parent only).

## Escalation conditions
Repository contains files the audit is not authorised to read · census reveals committed secrets material or
personal-data dumps (hand to RDA-10/RDA-16 immediately).

## External validation required
Which counted units are actually deployed · which excluded paths are genuinely dead vs merely unbuilt.

## Known limitations
Counts describe the tree, not the running system. A repository can contain a service that was decommissioned
two years ago and it will be counted; only deployment evidence resolves that.

## Success criteria
Every later coverage record resolves to a census key · no denominator anywhere in the audit originates outside
this file · re-running at the same SHA reproduces byte-identical counts.

## Example prompts
- Claude Code / Cursor: "Run rda-02-repo-census on this repo and write census.json plus the hotspot ranking."
- Codex: "$rda-02-repo-census — inventory this monorepo per top-level package and merge the denominators."
- Aider: "/read CONVENTIONS.md then run scripts/rda_census.sh . and summarise the strata."
