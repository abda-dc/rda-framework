---
name: rda-10-secret-flow-audit
description: Produces a redacted register of secret material in the working tree and full git history with type, exposure window and rotation path; use when auditing credential exposure or handing a repo over.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-10"
  layer: "2-risk"
  risk_class: "HIGH_HARM"
  tier: "core"
  depends_on: "RDA-02, RDA-09"
---

# RDA-10 · Secret Flow Audit

Inherits RDA-00. A secret is a credential with a blast radius and a rotation clock, and history keeps it.

## Purpose
Enumerate secret material reachable from the repository — tree, history, config and CI — classify it by
credential type and liveness, trace where it propagated, and produce a rotation order. Never print a value.

## Business value
Committed credentials are the cheapest breach available to an attacker and the finding most likely to survive a
repository handover, because a clone carries every object ever pushed. What a buyer or security lead needs is
not "12 hits" but "these three are live, they open these systems, rotate in this order, exposed since March".

## When to use
Every audit, first among the Layer 2 skills. Mandatory before open-sourcing, contractor onboarding, an
acquisition data-room, or any transfer of repository access to a new party.

## When NOT to use
Never skipped. If history cannot be scanned (shallow clone, no scanner, no disk), do not substitute a grep of
the working tree and call it a secret audit — declare the degradation and cap coverage accordingly.

## Inputs
Full non-shallow clone with all refs and tags · `census.json` (`risk_surface.secret_pattern_files`) · RDA-09
config inventory and precedence · CI workflow paths · the sanctioned secret managers and the outbound-call rule.

## Procedure

**1. Prove the corpus is complete (gate).** `git rev-parse --is-shallow-repository` must print `false`;
`git fetch --all --tags --prune`; record `git rev-list --all --count` and `git rev-list --objects --all | wc -l`.
A shallow clone silently downgrades a history audit to a tree audit — stop and record it rather than proceed.

**2. Deterministic sweep over 100% of tree and history.** Run every available scanner; record name, version,
args and exit code for each:
- `gitleaks git . --redact --report-format sarif --report-path out/gitleaks.sarif --log-opts="--all --full-history"` (exit 1 = leaks found, 0 = clean). **`detect`/`protect` were deprecated in v8.19.0** — using them dates the skill and will break.
- `gitleaks dir . --redact --report-format json --report-path out/gitleaks-tree.json` — the working tree, including untracked and ignored files the git walk never visits (`--no-git` is gone from the global flags)
- `trufflehog git file://. --only-verified --json > out/trufflehog.json` (add `--no-verification` when outbound calls are forbidden, `--fail` to exit 183 when results exist) and `trufflehog filesystem . --only-verified` for build outputs
- `detect-secrets scan --all-files > .secrets.baseline` then `detect-secrets audit .secrets.baseline` to carry triage state across runs
- **Degraded fallback (no scanner):** `git log -p --all -S'PRIVATE KEY'` and `git grep -nIE '<pattern>' $(git rev-list --all -- <path>)` scoped per path. Record `TOOL_UNAVAILABLE`, cap at C2.

**3. Classify every candidate.** Type (cloud access key, database DSN, JWT signing key, private key, OAuth
client secret, webhook token, PAT, TLS material), issuing system, and disposition: `LIVE_CANDIDATE` ·
`PLACEHOLDER` (`changeme`, `EXAMPLE`, `<...>`) · `TEST_FIXTURE` · `ROTATED_CLAIMED` (external validation).

**4. Establish liveness without exfiltration.** Liveness comes from a recorded scanner verification or from the
owning team — the agent never constructs its own authenticated request with a discovered credential, never
echoes it, never writes it anywhere. Findings carry locator, SHA, type and a fingerprint (4 chars + length).

**5. Provenance and exposure window.** Per confirmed secret: `git log --all --format='%H %aI' -S'<literal>' -- <path>`
for introducing and last-touching commits, `git log --all --full-history -- <path>` to prove the blob survives
deletion, `git tag --contains <sha>` for publishing refs. Window runs to the rotation date, not the deletion.

**6. Propagation pass.** Follow the value forward: log and error paths, CI echoes (`set -x`, `env`), `ARG`/`ENV`
in `Dockerfile*` (build args persist in image layers), front-end bundles and sourcemaps, k8s `ConfigMap` where a
`Secret` was meant, committed `.env`, terraform state. This turns "a key in a file" into "a key in every build log".

**7. Halt and escalate (ESC-1).** On live secret material in tracked files or history: stop, emit the escalation
notice (locator, type, class of harm, rotation action, owner role, what RDA deliberately did not do), resume
only once acknowledged. Rotation precedes rewriting — `git filter-repo` removes the object, not the access.

**8. Disconfirming pass.** Per candidate, run one query that would show it is *not* live: is the path a declared
fixture, does the value appear in vendor documentation samples, is the file untracked (`git check-ignore -v`),
does RDA-09 show the runtime value sourced from a vault instead. Record the query and its result.

## Outputs
`secrets-register.csv` (locator, type, fingerprint, disposition, first/last commit, exposure window, refs,
propagation targets, rotation owner role) · redacted SARIF · `rotation-order.md` sequenced by blast radius ·
escalation notices · a coverage record over history objects, not just tracked files.

## Evidence requirements
Each entry carries `path#Lstart-Lend`, the commit SHA, and the scanner name, version, rule id and exit code.
The `quote` field carries the **matched rule id and redacted fingerprint**, never the matched value — this is
the one place in RDA where verbatim quotation is prohibited rather than required.

## Fact vs inference rules
`FACT`: a string matching rule R exists at locator L at commit C (scanner output); a verification call returned
verified. `INFERENCE`: this credential opens system S — only when cited config binds it to a named endpoint.
`HYPOTHESIS`: the secret was used by an attacker, or the secret is dead — RDA is not incident response and
"nobody used it" is unreadable from a repository. `EXTERNAL_VALIDATION_REQUIRED`: validity and rotation date.

## Confidence scoring rules
HIGH/CRITICAL secret findings require **C3**: a named scanner with version and exit code, plus an independent
read at the pinned commit. A recorded live-verification result is an executed artifact and raises the finding to
C4. Scanner disagreement is reported, never averaged; a single-scanner hit with no read is C1, a verification task.

## Repository coverage rules
Population is **all blobs reachable from all refs**, not tracked files at HEAD. Denominator:
`git rev-list --objects --all | wc -l`; secondary tree denominator `git ls-files | wc -l`. History coverage is
EXHAUSTIVE or the band is declared and unscanned refs named. Secret-surface coverage (config, CI and IaC files
scanned / those counted in `census.json`) is reported separately from artifact coverage.

## Large repository strategy
Scanning is I/O bound, not token bound: never sample history to save tokens — shard it. Split by date window
(`--log-opts="--all --since=2021-01-01 --until=2022-01-01"`) or per submodule and merge; submodules need their
own run because the parent walk skips them. Model reading covers only classification and propagation.

## Failure conditions
Shallow clone or missing refs · no scanner and no `git grep` fallback permitted · encrypted material
(`git-crypt`, SOPS) · unfetched LFS pointers · binary blobs where line ranges are meaningless — each a blind spot.

## Escalation conditions
Live credential in tree or history (halt, ESC-1) · evidence of compromise such as an unexplained webhook or
exfiltration path (halt the run, preserve the manifest, hand to incident response) · production data alongside
credentials (hand to RDA-16) · a credential belonging to a third party rather than the auditee.

## External validation required
Whether each credential is still valid · when it was last rotated · which system and privilege scope it opens ·
whether the exposure window overlaps a known incident · whether the repo was ever public or forked. Systems of
record: secret manager, IdP, cloud audit log, CI secret store, VCS access log.

## Known limitations
Two ways this skill produces a wrong answer. **(a) The fixture panic** — high-entropy test values reported as
live keys, burning the rotation budget and training the team to ignore the register; step 3 classification, the
step 8 fixture/vendor-sample check and the C3 floor gate that. **(b) The clean-history illusion** — HEAD is
clean so the report says clean, while the credential lives in a dangling blob, an old tag or a fork; the
population definition (`rev-list --objects --all`) and the step 1 shallow-clone gate prevent it. Entropy
detection also misses secrets shaped like ordinary strings, and none sees a key pasted straight into CI settings.

## Success criteria
Zero secret values appear in any artifact, log or manifest · every `LIVE_CANDIDATE` has a rotation owner role
and an exposure window · the history denominator is published next to the tree denominator · escalation was
raised before the rest of the audit continued · re-running at the same SHA reproduces the register.

## Example prompts
- Claude Code / Cursor: "Run rda-10-secret-flow-audit across the tree and full history; redact every value and give me the rotation order by blast radius."
- Codex: "$rda-10-secret-flow-audit — scan all refs with gitleaks and trufflehog, classify hits, and write secrets-register.csv with exposure windows."
- Antigravity / Gemini CLI: "/rda-secret-flow scope=. history=all verify=off output=secrets-register.csv"
