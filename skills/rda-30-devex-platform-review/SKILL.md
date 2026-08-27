---
name: rda-30-devex-platform-review
description: Tests the documented onboarding path in a clean container and measures build/test feedback loops, golden paths and platform self-service from CI evidence; run on explicit DevEx requests.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-30"
  layer: "4-health"
  risk_class: "LOW_HARM"
  tier: "optional"
  depends_on: "RDA-19, RDA-26"
---

# RDA-30 · Developer Experience & Platform Review

Inherits RDA-00. The distinguishing rule of this skill: the documented setup path is executed, not read — a README that has never been run is a hypothesis about onboarding.

## Purpose
Establish what it actually costs to become productive in this repository: whether a new engineer can build and run it
from the documented steps, how long the inner and outer feedback loops take, and how much is self-service.

## Business value
Onboarding cost and feedback-loop latency are the two levers that decide how quickly an acquired or inherited team
delivers anything. Both are measurable from artifacts; neither is visible in an architecture diagram.

## When to use
Optional and on request: integration planning, onboarding a new team, platform investment cases, or when RDA-19
shows long pipelines and someone asks whether the day-to-day loop is as slow as the release loop.

## When NOT to use
As a proxy for developer satisfaction or productivity — those need survey and workflow data this skill cannot see ·
where no container runtime exists to run the path safely · where bootstrap requires production credentials.

## Inputs
RDA-19 pipeline inventory · RDA-26 hotspots · `README`, `CONTRIBUTING`, `docs/` · `Makefile`/`Taskfile`/`justfile` ·
`devcontainer.json`, compose files, `.tool-versions`/`mise.toml`/`.nvmrc` · CI run history · templates · pinned SHAs.

## Procedure

**1. Inventory the documented path (deterministic).**
```
ls -1 README* CONTRIBUTING* Makefile Taskfile.y*ml justfile .tool-versions mise.toml .nvmrc 2>/dev/null
rg -uu -n '^\s*(\$ )?(npm|pnpm|yarn|make|just|task|docker compose|mvn|gradle|poetry|uv|pip|go) ' README.md CONTRIBUTING.md
fd -H -t f 'devcontainer.json|docker-compose.ya?ml|\.envrc|Vagrantfile'
```
Count documented steps, declared prerequisites, and every step assuming an undeclared tool or credential. `-uu`
(`--no-ignore --hidden`) is required for any counted sweep: ripgrep's default filtering follows the auditor's ignore
files, so an unpinned count is not reproducible.

**2. Execute the documented path in a clean container, timed.** This is the measurement; do not assume the README
works because it looks complete:
```
docker run --rm -v "$PWD":/w -w /w --network=none <base-image> \
  bash -lc 'time { <documented step 1>; <documented step 2>; }'   # then re-run with restricted egress
```
No host caches, no ambient credentials, no pre-installed toolchain. Record exit codes, wall-clock per step, the
**first failing step with its line citation**, and every undocumented action required to get past it. Degraded
fallback without a container runtime: mark the path untested — never report a read-through as a successful setup.

**3. Measure the outer loop from CI evidence.**
```
gh run list --limit 300 --json workflowName,conclusion,createdAt,startedAt,updatedAt,databaseId > dx/runs.json
gh run view <id> --json jobs > dx/job-<id>.json
```
Split **queue time** (created→started) from **execution time** (started→completed) per job, report p50/p95 with n,
exclude cancelled runs, and separate cold- from warm-cache runs where the log records a cache hit. A single
"the build takes 42 minutes" figure can be mostly queue.

**4. Measure the inner loop.** In the same container: cold and warm build, unit-test suite, lint, and the
watch/incremental path if one exists. Report wall-clock with the hardware profile stated — container timings are
comparable to each other, never to a developer laptop.

**5. Golden paths and self-service.** Scaffolding and templates (`cookiecutter`, `copier`, workflow templates,
service catalogues), template adoption counted across services rather than asserted, PR preview environments,
self-service infrastructure modules, and whether platform ownership is documented anywhere in-repo.

**6. Friction inventory.** Prerequisites requiring privileged access (VPN, cloud credentials, private registries,
licence keys), manual steps, tribal steps discovered in step 2, and local dependencies that are flaky or unpinned.

**7. Disconfirming pass.** Before reporting friction, search for a path the README omits — a devcontainer, a compose
file, a Nix flake, a `make bootstrap` — and check whether onboarding docs live outside the repository. Absence
in-repo is not absence; record the query and result.

## Outputs
`devex-report.json` · the executed onboarding transcript with per-step timings and the first failure · CI
feedback-loop table (queue vs execution, p50/p95, n) · golden-path adoption counts · friction list · findings.

## Evidence requirements
Every documented step cites `README.md#Lstart-Lend` + SHA + quote. Every timing carries the command, container image
digest, and whether caches were warm. Every CI figure names the workflow, job, window and run count.

## Fact vs inference rules
`FACT`: "step at `README.md#L20-L28` exits 1 in a clean container at <SHA>", with the transcript attached.
`INFERENCE`: onboarding friction level, from the failure point plus the undeclared-prerequisite count.
`HYPOTHESIS`: the effect on team throughput. `EXTERNAL_VALIDATION_REQUIRED`: real time-to-first-commit or
time-to-productivity, developer satisfaction, and whether CI runners match what engineers actually use.

## Confidence scoring rules
C4 is reachable here and nowhere else in this layer: the executed container run is a reproduced execution artifact.
CI-derived timings are C3. Anything about human experience caps at C2 and carries an external-validation question.
A path that was read but not executed is C1, and must say "not executed" in the finding statement.

## Repository coverage rules
Population = documented setup paths × supported platforms; name the platform executed, since a macOS-only README run
in a Linux container is a partial test. In monorepos the population is units with their own setup path.

## Large repository strategy
Execute the top units by ownership breadth or by RDA-26 hotspot rank rather than all of them, and say which. CI
timing analysis is cheap and stays exhaustive over the run window; only the execution pass is sampled.

## Failure conditions
No container runtime (degrade to a documentation read, state "path not executed", cap at C1) · bootstrap requires
credentials the audit must not hold (stop, record `ACCESS_DENIED`) · CI history unavailable · an internal registry
unreachable from the audit environment (blind spot, not a defect).

## Escalation conditions
Bootstrap requires production credentials or writes to production · setup instructs disabling TLS verification or
piping an unpinned remote script into a shell (RDA-14) · `.env.example` or fixtures contain live-looking secrets
(RDA-10, halt) · setup requires accepting a licence on the client's behalf.

## External validation required
Actual onboarding times from the people who did it · whether the CI runner class matches production expectations ·
whether an internal platform team supports these paths · which documented path is the sanctioned one when several exist.

## Known limitations
Two ways this skill produces a wrong answer, and the controls that stop them. **(a) Executing on a machine that
already has the toolchain, caches or credentials** makes a broken path look healthy — prevented by the clean,
network-isolated container in step 2 with no ambient credentials and a recorded image digest. **(b) Reading CI
wall-clock as build time** attributes queue delay and matrix fan-out to the build — prevented by the queue/execution
split, per-job p50/p95 with n, and cache-state separation. A repository shows what onboarding costs, never how it feels.

## Success criteria
The documented path was executed and its transcript is in the run manifest · the first failing step is named with a
line citation · every timing separates queue from execution · no productivity or satisfaction claim without an
external source · golden-path adoption is counted, not asserted.

## Example prompts
- Claude Code / Cursor: "Run rda-30-devex-platform-review — actually execute the README setup in a clean container, time it, and report where it first fails."
- Codex: "$rda-30-devex-platform-review — measure CI queue vs execution p50/p95 per job, test the documented bootstrap in docker with --network=none, emit devex-report.json."
- Antigravity / Gemini CLI: "/rda-devex scope=. execute=true image=ubuntu:24.04 window=90d"
