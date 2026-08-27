---
name: rda-19-cicd-review
description: Produces pipeline topology, merge gates and branch protection, the release and rollback path and deployment cadence evidence — use when assessing whether the delivery process works.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-19"
  layer: "3-operations"
  risk_class: "MEDIUM_HARM"
  tier: "core"
  depends_on: "RDA-02"
---

# RDA-19 · CI/CD Review

Inherits RDA-00. RDA-19 asks **does the delivery process work**; RDA-14 asks **can it be subverted**. A workflow
file that exists is not a gate that blocks — only the branch-protection API says that.

## Purpose
Establish how code reaches production, what stops it, how it is undone, and at what observed cadence.

## Business value
Delivery capability is the strongest available predictor of whether identified remediation is deliverable at
all. A repository with no enforced gate and no rollback path converts every other finding from "fixable" into
"fixable, with an outage risk attached", which changes both price and sequencing.

## When to use
Every audit with any CI configuration. Mandatory input to RDA-23's readiness gate and RDA-14's provenance work.

## When NOT to use
When the delivery question is about *tamper resistance* (token scope, artifact signing, action pinning,
dependency confusion) — that is RDA-14 and duplicating it here produces two conflicting risk rows.

## Inputs
`census.json` (CI file and build-manifest counts) · pipeline definitions · forge API access (`gh`, `glab`) if
granted · tags and releases · RDA-08 migration inventory for rollback reversibility · RDA-09 per-environment config.

## Procedure

**1. Pipeline inventory (deterministic, 100%).**
`git ls-files '.github/workflows/*.y*ml' '.gitlab-ci.yml' 'azure-pipelines*.yml' 'Jenkinsfile*' '.circleci/config.yml' '.drone.yml' 'bitbucket-pipelines.yml'`
plus reusable-workflow and template references. Count against the census CI denominator so an unreferenced,
never-triggered workflow is visible as such.

**2. Topology.** For each pipeline extract jobs, `needs`/`stage` edges, triggers, path filters, `if:` guards,
matrices, concurrency and environments: `yq '.on, .jobs | keys' <file>`, `actionlint -format '{{json .}}'`.
Render the DAG. A job's *existence* is FACT; its *execution on a given event* is INFERENCE that must cite the
trigger, the path filter and the guard together — this is where most CI claims go wrong.

**3. Gates and branch protection.** `gh api repos/{owner}/{repo}/branches/{branch}/protection` and
`gh api repos/{owner}/{repo}/rulesets`; GitLab `glab api projects/:id/protected_branches`. Record required
status checks, required reviewers, code-owner review, linear history, force-push and deletion settings, and
admin bypass. **Degraded fallback:** no API access ⇒ enforcement is UNKNOWN with the forge admin named as system
of record; never infer enforcement from a workflow file.

**4. Release path.** `git tag --sort=-creatordate | head -50`, `gh release list --limit 50`, release workflows,
version scheme, artifact publication targets, changelog automation, and whether release is triggered by tag,
branch, manual dispatch or approval.

**5. Rollback mechanism.** Locate the actual undo: `helm rollback`, `kubectl rollout undo`, Argo Rollouts abort,
blue/green or canary switch, re-deploy of a retained previous artifact, feature-flag kill switch. Then test
reversibility against RDA-08: an irreversible migration, a consumed queue message or a one-way data backfill
makes "redeploy the previous tag" a partial rollback, and it must be reported as partial.

**6. Environment promotion.** Environments declared, their approval requirements, promotion order, and whether
the same artifact digest moves between them or each environment rebuilds. Rebuild-per-environment means the
tested artifact is not the shipped artifact; state that plainly and hand the provenance angle to RDA-14.

**7. Cadence evidence.**
`gh run list --workflow=<deploy> --limit 200 --json createdAt,conclusion,headSha,event` and
`git log --tags --simplify-by-decoration --date=short --pretty='%ad %d' | head -50`. Derive cadence from these
records directly — `dora-team/fourkeys` was archived in January 2024 and must not be named as the source. Report
run and tag frequency as FACT about run records; production deployment frequency remains EXTERNAL.

**8. Disconfirming pass.** Before any "no CI / no gate / no rollback" claim, search for delivery outside this
repo: organisation-level required workflows and rulesets, platform pipelines (Argo CD, Spinnaker, Harness,
Backstage), deploy scripts in a sibling infra repo, and `.github` org defaults. Record the query and result.

## Outputs
`pipeline-topology.json` (jobs, edges, triggers, guards) · `gates.json` (required checks, reviewers, bypass) ·
`release-path.md` (tag→artifact→environment chain, rollback verdict) · `cadence.csv` · findings · coverage records.

## Evidence requirements
Every gate claim cites either the protection/ruleset API response (`TOOL_OUTPUT` with command and exit code) or
a pipeline file at `path#Lstart-Lend` with commit SHA. Cadence claims cite the run or tag records. A rollback
claim cites the command or manifest that performs the rollback, not a heading in a README.

## Fact vs inference rules
FACT: pipeline files, job definitions, API responses, tag and run records. INFERENCE: "tests gate merge to main" =
required-check name **and** the job that produces that check name **and** no admin bypass. HYPOTHESIS: "this pipeline
deploys to production" — a job named `deploy-prod` is a name, not a deployment. EXTERNAL: deployment frequency, change
failure rate, lead time and MTTR (deployment tooling and incident tracker); DORA-style metrics are not derivable from
a repository.

## Confidence scoring rules
Protection API plus the matching job definition = C3. Pipeline file alone = C2 at best, and never supports an
enforcement claim. Cadence from run records = C3 for the records, C2 for any statement about production. No
disconfirming sweep (step 8) = C1.

## Repository coverage rules
Population: CI definition files plus deployable units, denominators
`jq '.structural.ci_files, .structural.build_manifests' census.json`. Report both — a monorepo with one workflow
covering 3 of 40 build units has 100% pipeline coverage and 7% unit coverage, and only the second is honest.
State per-unit gate coverage next to the section heading.

## Large repository strategy
Shard by pipeline file; the topology merge is a graph union keyed by job id. Fetch protection once per repo, not
per shard. Budget guard: parse all pipelines deterministically, read only the release and deploy jobs plus any
job feeding a required check; mark the remainder `BUDGET_EXHAUSTED`.

## Failure conditions
No forge API access (enforcement UNKNOWN) · self-hosted forge without credentials · pipelines defined in an
out-of-scope repository · generated or templated pipelines whose expansion is not in the tree.

## Escalation conditions
A required check that is a no-op or unconditional `exit 0` · protection disabled on the default branch of a
production repository · deploy credentials or `kubeconfig` committed in a workflow (halt, hand to RDA-10) ·
`pull_request_target` with checkout of untrusted head (hand to RDA-14 immediately).

## External validation required
Whether the pipeline for these files is the pipeline that ships (release engineering) · production deployment
frequency and change failure rate (deployment tooling) · who can bypass protection (forge administrator) · whether
rollback has ever been exercised (release engineering — a documented drill, not an opinion).

## Known limitations
Two ways this skill produces a wrong answer. **(a) The phantom gate** — reading `on: pull_request` and concluding
tests block merges, when the job is skipped by a path filter or `if:` guard, or is simply not a required check;
step 2 forces trigger+filter+guard to be cited together and step 3 makes enforcement an API fact. **(b) The false
"no rollback"** — rollback is often a platform capability held outside the repo; step 8 requires the out-of-repo
sweep, so absence is reported as "absent from scope" with an external-validation item, never "does not exist".

## Success criteria
Every enforcement claim traces to an API response · the release path is expressible as one chain from commit to
environment · rollback carries an explicit full/partial/absent verdict citing RDA-08 · no DORA-style metric is
asserted from repository contents · RDA-14 and RDA-19 findings do not overlap.

## Example prompts
- Claude Code / Cursor: "Run rda-19-cicd-review: map the pipeline DAG, pull branch protection via gh, and tell me whether a failing test can actually block a merge."
- Codex: "$rda-19-cicd-review — trace commit → artifact → environment for the deploy workflow and give me the rollback verdict."
- Antigravity / Gemini CLI: "/rda-cicd scope=.github/workflows gates=api output=release-path.md"
