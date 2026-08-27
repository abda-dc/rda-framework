---
name: rda-20-infrastructure-iac-review
description: Produces IaC-versus-click-ops coverage, network exposure, IAM breadth, encryption, state handling and drift posture as declared intent — use when IaC or cluster manifests are in scope.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-20"
  layer: "3-operations"
  risk_class: "MEDIUM_HARM"
  tier: "conditional"
  depends_on: "RDA-09, RDA-19"
---

# RDA-20 · Infrastructure & IaC Review

Inherits RDA-00. **Hard rule: IaC is INTENT, never live state.** Every statement here ends, explicitly, "as
declared at `<sha>`". What the cloud account actually contains is undecidable from this repository.

## Purpose
Establish what fraction of the infrastructure is declared, and what the declarations say about exposure,
privilege, encryption, state custody and drift.

## Business value
Undeclared infrastructure is the part nobody can review, reproduce or hand over, and it is where post-close
surprises live. The declared/undeclared split is a diligence answer in itself, independent of config quality.

## When to use
Whenever the census counts IaC roots, Kubernetes manifests, Helm charts or cloud templates. Required input to
RDA-22 and RDA-23.

## When NOT to use
No infrastructure declarations in scope. Do not substitute application config review — that is RDA-09 — and do
not attempt live posture assessment, which requires account access this skill does not have.

## Inputs
`census.json` (IaC root and manifest counts) · RDA-09 configuration and environment inventory · RDA-19 pipeline
definitions (which roots are applied, by which job, to which environment) · scanner availability.

## Procedure

**1. Declaration inventory (deterministic, 100%).** Enumerate roots and stacks: Terraform roots as directories
holding a `terraform {` or `backend` block, plus Helm charts, Kustomize overlays, CloudFormation/SAM templates,
Pulumi and CDK programs, Ansible playbooks and `serverless.yml`. Record provider and module versions and whether
modules are pinned.

**2. Resolve intent, do not regex it.** Prefer a resolved graph to text matching:
`terraform init -backend=false && terraform validate`,
`terraform plan -refresh=false -out=tfplan && terraform show -json tfplan`, `helm template <chart> -f <values>`,
`kustomize build <overlay>`, `cdk synth`. **Degraded fallback:** without a plan use `hcl2json`/`yq` plus explicit
resolution of module sources and variable defaults, and record that module and workspace overrides are unresolved.

**3. Scanner pass, adjudicated.** `checkov -d . -o json` · `trivy config <dir> --format json` (the successor to
`tfsec`, which upstream folded into Trivy) · `kics scan -p . --report-formats json` ·
`conftest test --policy policy/ .` · `kube-score score <manifests>`. Do not use `terrascan`: the Tenable repo is a
public archive and no longer maintained. Record name, version, exit code. Scanner output is a candidate list;
every published finding is re-read at source and cited, and a rule id is never a finding on its own.

**4. Declared versus demanded.** Extract the infrastructure the application demands from RDA-09 — connection
strings, bucket names, queue URLs, DNS names, secret stores, third-party endpoints — and join it to declared
resources. Each demanded dependency with no declaration is a **click-ops candidate**, not a proven one. Publish
the ratio with its denominator; the absolute count of undeclared infrastructure needs the cloud account.

**5. Exposure, privilege, encryption.** Exposure: `0.0.0.0/0` and `::/0` ingress, internet-facing schemes,
`publicly_accessible`, public bucket policy, `type: LoadBalancer`, Ingress without TLS, absent NetworkPolicy.
Privilege: `Action: "*"`, `Resource: "*"`, `AdministratorAccess`, unconstrained `iam:PassRole`, `Principal: "*"`
trust, `roles/owner`, subscription-scope Owner, ClusterRole with `*` verbs. Encryption: KMS key presence,
`storage_encrypted`, SSE settings, minimum TLS version, plaintext listeners.

**6. State custody and drift posture.** Backend type, state encryption, locking, workspace layout, and whether a
state file is tracked (`git log --all --diff-filter=A --name-only | rg 'terraform\.tfstate'` — a tracked state
file is an escalation, not a finding). Drift posture: `terraform plan -detailed-exitcode` in CI, `-refresh-only`
jobs, Atlantis/Spacelift/Terraform Cloud, Argo CD `selfHeal` and `prune`. Posture is whether drift would be
*detected*; whether drift exists is undecidable here.

**7. Disconfirming pass.** Before any "unencrypted / unrestricted / undeclared" claim, search for the control
elsewhere: provider defaults and `default_tags`, wrapping modules, organisation policy (SCP, Azure Policy, GCP
org policy), admission controllers (Kyverno, Gatekeeper) and per-environment `*.tfvars`. Record query and result.

## Outputs
`iac-inventory.json` (roots, providers, module pins) · `declared-vs-demanded.csv` (the click-ops candidate list)
· `exposure.json` · `iam-breadth.json` · `state-and-drift.md` · adjudicated scanner findings · coverage records.

## Evidence requirements
Every finding cites `path#Lstart-Lend` and commit SHA, or a resolved-plan locator with its producing command. Scanner
corroboration carries name, version, exit code; environment claims cite the selecting varfile or overlay.

## Fact vs inference rules
FACT: the declaration text and resolved plan values. INFERENCE: "this bucket is intended to be public" from the policy
plus absence of an overriding module default. HYPOTHESIS: any statement about what exists, is running or holds data —
including data residency, which is intent in IaC and state only in the account. UNKNOWN: resources demanded by code
with no declaration. EXTERNAL: live posture, drift, account guardrails, and whether a root was ever applied (cloud
console, state backend, apply logs).

## Confidence scoring rules
Resolved plan + source citation + scanner agreement = C3, the floor for any HIGH exposure or privilege finding.
Regex-derived findings without plan resolution = C2 maximum. Any claim about the live account = C2 ceiling with an
`external_validation.question`. Unread scanner output is C1: Google's static-analysis practice counts an *effective*
false positive as any warning a developer did not act on and holds code-review checks under a 10% effective-FP rate,
so a forwarded rule id clears no bar. No step-7 sweep = C1.

## Repository coverage rules
Population: declared resource blocks across all roots, denominator
`terraform show -json tfplan | jq '[.. | .resources? // empty | .[]] | length'`; degraded denominator
`rg -uuu -c '^resource "' -g '*.tf'` summed over files, plus `yq 'select(.kind) | .kind' | wc -l` for manifests.
Pin `-uuu` so counts do not depend on the auditor's ignore files. Report coverage per root: one unreviewed root can hold the production network.

## Large repository strategy
Shard by root/stack; each shard emits resource-level records, never prose. Run scanners repo-wide (they are
cheap and exhaustive) and reserve reads for roots that RDA-19 shows are applied to production. Budget guard:
prioritise roots by (applied-to-prod, internet-exposed resource count, IAM statement count).

## Failure conditions
`terraform init` needs credentials or network · private module registry unreachable · CDK/Pulumi programs that
must execute · no scanner available · IaC in an out-of-scope repo. Each is a blind spot; none licenses a guess.

## Escalation conditions
State file committed to VCS (halt; treat as potential secret exposure, hand to RDA-10) · credentials or private keys
in `*.tfvars` or manifests · a database port opened to the internet in a root RDA-19 shows applied to production ·
org-wide administrative trust granted to an external principal.

## External validation required
Which roots are applied to which accounts, and when (state backend and apply logs) · resources created outside IaC
(cloud console inventory) · actual drift (drift report from the account) · data residency in practice (provider region
inventory) · whether guardrails exist above the account (cloud platform team).

## Known limitations
Two ways this skill produces a wrong answer. **(a) The module blind spot** — grepping for `encrypted` misses settings
supplied by a wrapping module, a variable default or a provider default, producing a false "unencrypted" finding; step
2 prefers resolved plans and step 7 forces the override search. **(b) Intent read as state** — a resource declared
public in a root never applied, or overridden per environment, becomes a confident claim about a system that does not
exist; the intent-not-state rule and the C2 ceiling on live-account claims contain it.

## Success criteria
Every finding names the root, the environment selector and the commit · the declared-versus-demanded ratio
publishes its denominator · no sentence asserts live cloud state · scanner findings are adjudicated, not forwarded.

## Example prompts
- Claude Code / Cursor: "Run rda-20-infrastructure-iac-review on ./infra: resolve the plan, run checkov and trivy config, and list what the app needs that IaC does not declare."
- Codex: "$rda-20-infrastructure-iac-review — report internet-exposed resources and wildcard IAM per Terraform root, as declared intent only."
- Antigravity / Gemini CLI: "/rda-iac roots=infra/ scanners=checkov,kics output=declared-vs-demanded.csv"
