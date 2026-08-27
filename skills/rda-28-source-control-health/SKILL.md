---
name: rda-28-source-control-health
description: Derives branch model, commit and PR hygiene, review latency and DORA-style delivery proxies from git and CI evidence as repository signals, never team judgements; core in every audit profile.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-28"
  layer: "4-health"
  risk_class: "LOW_HARM"
  tier: "core"
  depends_on: "RDA-02"
---

# RDA-28 · Source Control & Delivery Health

Inherits RDA-00. Every statement here describes a repository, not the people who commit to it; the words "the team" do not belong in this skill's output.

## Purpose
Characterise how change actually reaches the default branch and a release — branching, review, merge, revert,
release, history hygiene — using only git and CI artifacts, and derive delivery proxies with their limits stated.

## Business value
How change moves through a repository is the cheapest and most complete evidence available in diligence: git history
is exhaustive, timestamped and hard to retouch unnoticed. It tells an acquirer how fast a fix can be shipped safely.

## When to use
Every profile (core). Triggered by "how do they ship", "is the process healthy", "what is their DORA posture",
integration planning, release-risk assessment, or any question about delivery capability.

## When NOT to use
To evaluate people, teams or productivity — out of scope by construction · to assert incident frequency or restore
times, which live in the incident system · on a repository whose history was imported or rewritten without saying so.

## Inputs
Full (non-shallow) clone with all refs · forge API access for PR, run and protection data · release and tag history ·
CODEOWNERS · `.gitattributes`, `.mailmap`, `.github/workflows` · census denominators · pinned commit SHAs.

## Procedure

**1. Deterministic git sweep across the whole window.** Record tool version and exit codes:
```
git log --since=24.months --no-merges --format='%H|%ct|%ae|%s'          > sc/commits.psv
git log --since=24.months --merges    --format='%H|%ct|%P|%s'           > sc/merges.psv
git for-each-ref --sort=-committerdate --format='%(refname:short)|%(committerdate:iso8601)' refs/remotes > sc/branches.psv
git log --since=24.months -i --grep='^Revert' --grep='hotfix' --format='%H %ct %s' > sc/reverts.txt
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | awk '$1=="blob" && $3>5000000' | sort -k3 -nr                       > sc/large-blobs.txt
```

**2. CI, PR and protection evidence.**
```
gh pr list --state merged --limit 500 --json number,createdAt,mergedAt,reviews,changedFiles > sc/prs.json
gh run list --limit 500 --json workflowName,headBranch,conclusion,createdAt,updatedAt       > sc/runs.json
gh api repos/{owner}/{repo}/branches/{default}/protection                                   > sc/protection.json
```
Degraded fallback without forge access: derive review signal from merge-commit trailers (`Reviewed-by`, `Approved-by`,
`Co-authored-by`), mark the coverage record `TOOL_UNAVAILABLE`, and cap review findings at C1.

**3. Branch and merge model.** Classify from evidence — trunk-based, GitHub-flow, git-flow, release-train, ad hoc —
citing branch-name distribution, branch lifetime, merge/rebase/squash ratio, and whether protection is enforced on the
default branch (the settings artifact, never the CONTRIBUTING claim).

**4. Commit hygiene.** Convention conformance as a counted rate, commit-size distribution, share of commits carrying
an issue reference, fixup/WIP rate, direct-to-default pushes. Report distributions with n, never a bare average.

**5. Review signal.** Time-to-first-review and time-to-merge as p50/p90, reviewers per PR, share merged with zero
approvals, self-merge rate, PR size. Review *depth* is proxied by comments per changed file and is labelled a proxy —
a thorough review of a small diff and a rubber stamp look identical in the count.

**6. History hygiene.** Large blobs (ref-reachable objects only, so a full clone is required), committed binaries and
artifacts, LFS and `.gitattributes` use, submodule pinning via `git submodule status --recursive`. Secrets: RDA-10.

**7. DORA-style delivery proxies — and the current metric set.** From tags, releases and workflow runs derive:
deployment frequency (successful deploy-workflow runs per week) · change lead time (first commit to deploy completion)
· deployment rework / failed deployment rate (deploy runs followed by a revert, hotfix or failed run) · failed
deployment recovery time (failed deploy run to the next success on the same target). **Do not report "MTTR" as current
DORA canon**: mean time to restore was retired in favour of failed deployment recovery time, and deployment rework sits
alongside it in the set. All four are repository proxies — the repo knows workflow runs, never deployments — so label
each `INFERENCE (proxy)` and name the substitution. Derive them here; `dora-team/fourkeys` was archived in 2024.

**8. Disconfirming pass.** Before any process claim, check for a second delivery path (a release repo, a manual
pipeline, a vendored deploy tool), for bot identities performing merges, and for imported history. Each of the three
invalidates the naive reading; record the query and result.

## Outputs
`scm-health.json` (distributions with n, not averages) · branch/merge classification with citations · the delivery
proxy table with substitutions named · history-hygiene list · findings · coverage records per population.

## Evidence requirements
Every rate cites its exact `git`/`gh` invocation, window and denominator; every configuration claim cites the settings
artifact or workflow file as `path#Lstart-Lend` + SHA + quote. Author date and commit date are never mixed in one series.

## Fact vs inference rules
`FACT`: counts, timestamps, protection settings, run conclusions. `INFERENCE`: branch-model classification and
review-depth readings, derivation written out. `HYPOTHESIS`: "the process is healthy". `EXTERNAL_VALIDATION_REQUIRED`:
incident frequency, restore times, whether a workflow run is a production deployment, whether a merged PR reached
customers. Nothing here attributes behaviour to a person or a team — see RDA-29 and BSR-09.

## Confidence scoring rules
C3 for git-derived counts (deterministic command, reproducible at the SHA). Review metrics from the forge API C3, from
merge trailers C1. Delivery proxies cap at **C2** — deployment reality is not in the repository. A window containing a
history rewrite is downgraded one level and the truncation stated.

## Repository coverage rules
Population = commits, merges, branches, PRs and workflow runs inside the declared window, denominated by the census.
State the window in every claim: 24 months of a nine-year repository is a sample, and pre-window behaviour is a blind spot.

## Large repository strategy
Run `git log --numstat` once and aggregate offline rather than issuing per-path queries. In monorepos compute per
top-level unit as well as globally: a healthy repo-level median can conceal one service whose PRs sit for weeks.

## Failure conditions
Shallow clone or missing refs (stop; every count is invalid) · forge API unavailable (degrade, declare, cap at C1) ·
squash-only merges (per-commit hygiene unmeasurable — say so, never score it low) · imported or rewritten history.

## Escalation conditions
Secrets or personal data in history (RDA-10 / RDA-16, halt this traversal) · force-push to the default branch with
protection disabled or excluding administrators (RDA-14) · unsigned release tags where provenance is documented.

## External validation required
Which workflow constitutes a production deployment · whether tags map to releases · incident and restore data from the
incident system · which identities are bots · whether review happens in an external tool the forge never sees.

## Known limitations
Two ways this skill produces a wrong answer, and the controls that stop them. **(a) A squash or rebase merge policy
erases commit-level evidence**, making a disciplined repository look undisciplined — prevented by detecting the merge
policy in step 3 *before* computing any commit-hygiene rate, and declaring the rate unmeasurable instead of low.
**(b) Bot and service identities** (dependabot, release bots, codegen jobs) inflate commit and PR counts and deflate
review latency — prevented by classifying identities from `.mailmap` and author-email patterns first, then reporting
bot and non-bot populations separately. Beyond those: git records what was merged, never what was deployed.

## Success criteria
Every metric carries window, denominator and producing command · no "MTTR" figure presented as current DORA canon ·
no sentence attributing behaviour to a person or team · every proxy labelled · the branch-model classification cites
two independent artifacts.

## Example prompts
- Claude Code / Cursor: "Run rda-28-source-control-health for the last 24 months — branch model, review latency p50/p90, revert rate, and DORA-style proxies labelled as proxies."
- Codex: "$rda-28-source-control-health — git + gh sweep, emit scm-health.json with distributions and n, separate bot identities, no team commentary."
- Antigravity / Gemini CLI: "/rda-scm scope=. window=24m forge=github output=scm-health.json"
