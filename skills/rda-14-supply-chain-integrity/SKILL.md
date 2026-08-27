---
name: rda-14-supply-chain-integrity
description: Assesses build provenance, CI token permissions, action pinning, artifact signing and dependency-confusion exposure against Scorecard checks and SLSA levels; use when release integrity is in scope.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-14"
  layer: "2-risk"
  risk_class: "HIGH_HARM"
  tier: "conditional"
  depends_on: "RDA-13, RDA-19"
---

# RDA-14 · Supply Chain Integrity

Inherits RDA-00. The question is not what the code does but who can change what ships, and with whose token.

## Purpose
Evidence the path from commit to artifact: provenance, CI privilege, pinning, signing, install scripts.

## Business value
Dependency CVEs are inventory; the supply chain is where one compromised token replaces a signed artifact for
every customer at once. This skill produces the controls deciding whether one merged pull request ships code.

## When to use
When CI/CD configuration exists, artifacts are published to a registry, third-party actions run in the build, or
the engagement covers release integrity or an acquisition of a shipped product.

## When NOT to use
For advisory matching (RDA-13), pipeline design (RDA-19) or cloud posture (RDA-20). This skill judges build-path
integrity, not efficiency.

## Inputs
CI workflow files and `census.json` `units.ci_workflows` · RDA-13 SBOM · RDA-19 pipeline topology and gates ·
registry configuration (`.npmrc`, `pip.conf`, `settings.xml`) · branch-protection evidence if exposed.

## Procedure

**1. Inventory the build path.** `git ls-files '.github/workflows/*' '.gitlab-ci.yml' 'Jenkinsfile*'
'azure-pipelines*.yml'`, plus release scripts and container build files. Every workflow that can write to a
registry, a cloud account or the default branch is in the population; the rest are context.

**2. Deterministic sweep.** Record tool, version, exit code:
- `scorecard --local . --format json > out/scorecard.json` (or `--repo=github.com/<org>/<repo> --show-details`); the checks that carry this skill are Pinned-Dependencies, Token-Permissions, Dangerous-Workflow, Branch-Protection, Signed-Releases, Binary-Artifacts and Maintained
- `actionlint -format '{{json .}}' > out/actionlint.json` for workflow validity and shell-injection patterns
- `zizmor --format sarif .github/workflows > out/zizmor.sarif` for known GitHub Actions attack patterns
- `ratchet check .github/workflows/*.yml` for pinning state
- **Degraded fallback:** `rg -n 'uses:\s*\S+' -g '.github/workflows/*'` plus manual classification, recorded as TOOL_UNAVAILABLE with a PARTIAL band
- Scorecard output is **evidence**, never a grade to report on its own — a score is not a finding

**3. Pinning.** Classify every third-party reference: a 40-hex SHA is pinned; a tag, branch or `latest`
re-resolves every run. `rg -n 'uses:\s*([^@\s]+)@(\S+)' -g '.github/workflows/*'` for actions; `rg -n
'^FROM\s+\S+' -g 'Dockerfile*'` for base images (digest vs tag); plugin blocks in `pom.xml` and `build.gradle`.
Report pinned/total per category — a mutable reference is a standing write grant to its publisher.

**4. Token and secret exposure in CI.** Look for absent `permissions:` blocks (defaults are broad);
`pull_request_target` or `workflow_run` triggers with a checkout of the untrusted ref; `${{ github.event.* }}`
interpolated into `run:` (script injection); secrets reachable from fork-triggered workflows; self-hosted
runners on public repositories; OIDC trust policies that do not constrain `sub`. Each finding cites
`path#Lstart-Lend` plus commit SHA and names the privilege exposed.

**5. Provenance and signing, mapped to SLSA.** Evidence for provenance generation
(`actions/attest-build-provenance`, slsa-github-generator), signing (`cosign sign`, keyless certificate
identity) and consumer-runnable verification (`cosign verify --certificate-identity ...
--certificate-oidc-issuer ...`, `gh attestation verify <artifact> --repo <owner/repo>`, `slsa-verifier
verify-artifact`). Map to SLSA Build levels with the artifact behind each. Absent evidence is **not evidenced**,
never a failed level.

**6. Install-time and build-time execution.** `jq -r '.scripts | keys[]' package.json` for
`preinstall`/`install`/`postinstall`; `rg -n 'setup\.py|build\.rs|\.gyp' -g '!test'`; whether CI installs with
`--ignore-scripts`. Code executing at install time is the shortest path from a compromised package to a build
machine.

**7. Namespace exposure.** From the SBOM, separate internal-looking names from public ones and read the registry
configuration: `.npmrc` scope mappings, `--extra-index-url` in pip config (resolution across indexes is the
confusion vector), `settings.xml` mirrors. For each internal name, check whether it is claimed publicly — a
lookup, never a guess. Typosquat claims require registry evidence (publish date, ownership, downloads); mere
similarity is a `HYPOTHESIS`.

**8. Publisher concentration and disconfirm.** Count distinct publishers behind direct dependencies and behind
build actions; one publisher across many steps is a concentrated write grant. Then query the opposite direction
per finding: an org ruleset, a required workflow, a registry allowlist or an admission policy that already
constrains this repository.

## Outputs
`supply-chain.csv` (control, locator, state present/partial/absent, tool, severity pair) · `pinning.csv`
(reference, type, pinned state, publisher) · `provenance.md` mapping evidence to SLSA levels · raw Scorecard
JSON.

## Evidence requirements
Every control state cites `path#Lstart-Lend` plus commit SHA in a workflow, manifest or registry config, or a
tool result with version and exit code. Platform settings outside the repo are `EXTERNAL_VALIDATION_REQUIRED`.

## Fact vs inference rules
`FACT`: this workflow declares these permissions; this reference is a tag not a SHA. `INFERENCE`: this token can
publish — with the trigger, the permission block and the publish step all cited. `HYPOTHESIS`: an attacker could
reach the release path. `UNKNOWN`: anything enforced in platform settings.

## Confidence scoring rules
HIGH/CRITICAL supply-chain findings require **C3**: a named tool with version and exit code plus the workflow
citation. Scorecard alone is C2, one tool over declared config; platform-enforcement claims stay C2.

## Repository coverage rules
Population is workflows and build definitions: `git ls-files '.github/workflows/*.y*ml' | wc -l` plus other CI
roots from the census. Second population is third-party references: `rg -o 'uses:\s*\S+' -g
'.github/workflows/*' | wc -l`. Pinned/total and permission-declared/total are reported against these
denominators.

## Large repository strategy
Workflows are few relative to source, so this skill stays EXHAUSTIVE over the CI population even on monorepos.
Follow shared `uses:` workflows one hop and record it; unfollowed hops are named blind spots.

## Failure conditions
CI configuration held outside the repository (platform UI, another repo) · no registry access to check namespace
claims · signing performed by a system not represented in the tree · shallow clone hiding workflow history.

## Escalation conditions
A publishing workflow triggerable by an untrusted contributor · an unclaimed internal package name on a public
registry · a malicious install-time script, halting the run per ESC-1 · credentials in workflows, to RDA-10.

## External validation required
Whether branch protection and required reviews are enforced · who holds registry publish rights · whether the
signing key is in an HSM or on a laptop · whether org-level rulesets override repository configuration.

## Known limitations
Two ways this skill produces a wrong answer. **(a) The green Scorecard** — a good score read as a secure build,
when it measures declared repository configuration while the artifact may still be built and published from an
unaudited machine; prevented by requiring artifact-side verification evidence before any provenance claim. **(b)
The typosquat accusation** — a legitimate package named as a squat on similarity alone; prevented by the step 7
registry-evidence rule and the `HYPOTHESIS` cap. Platform settings also dominate and are invisible here.

## Success criteria
Pinning and permission fractions published with denominators · every provenance claim tied to a verification
command · no SLSA level asserted without its artifact · platform controls as external validation.

## Example prompts
- Claude Code / Cursor: "Run rda-14-supply-chain-integrity: scorecard and zizmor first, then tell me which workflows can publish and which actions are unpinned."
- Codex: "$rda-14-supply-chain-integrity — classify every uses: reference as SHA or mutable, and map signing evidence to SLSA build levels."
- Antigravity / Gemini CLI: "/rda-supply-chain scope=.github/workflows registry=npm output=supply-chain.csv"
