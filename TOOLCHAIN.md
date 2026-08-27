# RDA Deterministic Toolchain — status, traps and what each tool actually proves

*Verified 2026-08-27.* A skill that names a dead tool is a defect, and a skill that trusts a tool beyond what
its own documentation claims is a worse one. This file is the pack's single source of truth for tool selection;
skills reference it rather than restating it.

## 1. Status corrections a framework must encode

| Commonly assumed | Verified reality | Do this instead |
|---|---|---|
| `ts-prune` for unused TS exports | **Archived** (Sep 2025); its README recommends knip | `knip --reporter json` |
| `terrascan` for IaC | **Public archive** — "no longer maintained" | `checkov`, `trivy config`, `kics` |
| `tfsec` for Terraform | Soft-deprecated; repo description reads *"Tfsec is now part of Trivy"* | `trivy config <dir> --format json` |
| `gitleaks detect --no-git` | `detect`/`protect` **deprecated in v8.19.0**; `--no-git` removed from global flags | `gitleaks git <repo>` (history), `gitleaks dir <path>` (tree) |
| `infracost breakdown/diff/comment` | **Removed in CLI v2** | `infracost scan --json`, `infracost inspect` |
| `dora-team/fourkeys` | **Archived** Jan 2024 | Derive delivery signals from git + CI evidence directly |
| `@microsoft/eslint-plugin-sdl` | **Archived** Aug 2026 | Language-native security linters |
| `go tool pprof -json` | **Not a documented flag** | `profile.proto` is the machine format |
| semgrep-rules are LGPL | **Rules relicensed** Dec 2024 to Semgrep Rules License v1.0 (non-OSI); engine still LGPL 2.1 | Check ruleset licensing before shipping a hosted product |
| CodeQL CLI is free | Free **only for open-source**; CI database generation on non-OSS code requires GitHub Code Security; reselling a hosted solution is forbidden | Budget for it, or use Semgrep |
| SLSA "v1.0/v1.1 levels" | **v1.2** is current and adds a **Source Track** beside the Build Track | Cite v1.2 tracks |
| CycloneDX 1.6 / SPDX 3.0 | **CycloneDX 1.7** (also ECMA-424); **SPDX 3.0.1** | Emit current versions |
| NTIA SBOM minimum elements | **Superseded** by CISA's *2026 Minimum Elements for an SBOM* (2026-07-29), which "updates and replaces" the 2021 NTIA guidance | Map SBOM completeness to the 2026 elements |
| SRE book "Evaluating Service Reliability" chapter | **Does not exist.** The PRR is **Chapter 32** plus Appendices B and E | Cite correctly or not at all |
| OTel `gen_ai.*` semconv in core | **Moved out** to a dedicated repository as of v1.42.0 | Track separately |

## 2. Behaviour traps that silently corrupt an audit

1. **ripgrep's default filtering** honours `.gitignore`, `.ignore`, hidden-file rules, binary detection, symlink
   exclusion **and the user's global `core.excludesFile`**. An audit denominator produced with defaults depends
   on the auditor's personal git config and is therefore not reproducible. **Pin `rg --no-ignore --hidden`
   (or `-uuu`) for any count, and record the flags.**
2. **`tokei` may be compiled without serialization formats**, in which case `--output json` fails. Probe it and
   fall back to `scc --format json`.
3. **universal-ctags emits definitions only.** Reference tags are opt-in and, verbatim, *"only a few parsers
   currently utilize it"*. **Never use ctags as a call-graph or reachability source.**
4. **`git-sizer` counts only objects reachable from refs** — not unreachable objects, not reflog-only objects —
   and requires a full, non-shallow clone.
5. **`tree-sitter parse` exits non-zero if any file fails to parse.** Check the exit code, not just output; it
   is a real syntax-health signal and a cheap corpus sanity check.
6. **`repomix --token-budget N` exits non-zero on overflow** — use it as a budget guard. Its MCP mode reads any
   host-readable path unless `--sandbox` is set.
7. **`scc --hotspots`, `--coupling`, `--by-author`** give deterministic churn × complexity ranking straight from
   git history — a free first-pass alternative to dedicated behavioural-analysis tools.
8. **Config-file surface is a reproducibility hazard**: `.sccconfig`/`.sccignore`, `tokei.toml`/`.tokeignore`,
   `RIPGREP_CONFIG_PATH`, `sgconfig.yml`, `repomix.config.json`, `~/.config/cloc/options.txt`. Record them in
   the manifest or the run is not reproducible.
9. **`cloc` is GPL-2.0** — fine to shell out to, problematic to vendor into a distributed product.

## 3. What the evidence says about the tools you will lean on

**SAST noise is measured, severe, and the reason RDA-11 adjudicates rather than generates.**
An ASE 2024 study across 319 real CVEs, 815 vulnerability-contributing commits and 92 C/C++ projects found
*"at least 76% of the warnings in vulnerable functions are irrelevant to the VCCs"* and that *"22% of VCCs
remain undetected"*; the best single tool warned on only 52% of vulnerability-contributing commits. An ISSTA
2022 study across 27 projects and 192 validated CVEs found tools *"miss in-between 47% and 80% of the
vulnerabilities"*, and that combining tools reduces false negatives only *"at the cost of 15 percentage points
more functions flagged"*. Google's published practice defines an **effective false positive** as one where
*"developers did not take positive action after seeing the issue"*, allows code-review checks up to **10%**
effective FPs, and records that of 3,954 FindBugs warnings reviewed company-wide **only 16% were fixed**,
after which *"the presence of effective false positives caused developers to lose confidence in the tool"*.

Note also that **no vendor publishes a numeric false-positive rate** for any of these tools, and the widely
repeated "~30% of SAST findings are false positives" traces to a vendor blog. Do not cite it.

**Dead-code polarity is tool-specific and must never be blurred.** In dynamic languages, static tools produce
**false positives** — live code reported dead. vulture's own documentation states it *"ignores scopes and only
takes object names into account"* and its README ships a `getattr` example where it **wrongly reports a live
method as unused**; knip publishes a ten-item false-positive taxonomy and notes the feature-flag case exists
*"because Knip executes configuration files to parse their exported value"*. Go's `deadcode` is the opposite —
sound because it over-approximates reflection and dynamic dispatch, so it errs toward **false negatives** — and
even then its docs warn the result *"does not mean it is unconditionally safe to delete"* and is *"valid only
for a single GOOS/GOARCH/-tags configuration"*. RDA-27 must state which polarity applies to the language it is
examining.

**VEX is the correct vocabulary for present-versus-exploitable.** Statuses: `NOT_AFFECTED`, `AFFECTED`,
`FIXED`, `UNDER_INVESTIGATION`, with five NOT-AFFECTED justifications: `component_not_present`,
`vulnerable_code_not_present`, `vulnerable_code_not_in_execute_path`,
`vulnerable_code_cannot_be_controlled_by_adversary`, `inline_mitigations_already_exist`. Two CISA caveats must
survive into any RDA finding that uses them: *"A single path of execution should not be assumed since the
attacker may be able to divert the path of execution"*, and VEX statuses are *"assertions made by the author of
the document"* — machine-readable attestation, **not proof**. Tooling: `grype --vex`, `govulncheck -format
openvex`, Trivy VEX Hub, and CycloneDX which carries VEX in-BOM.

**Reachability: mechanism verified, magnitude not.** Primary non-vendor sources state only the direction — the
Go team's govulncheck *"reduces noise by prioritizing vulnerabilities in functions that your code is actually
calling"* and *"narrow[s] down reports to only those that could affect the application"*. Every percentage in
circulation (80–92%, 80–99%) is **vendor marketing and must be attributed, never asserted**. Vendors' own
caveats are the honest part and worth quoting: reachability *"cannot see behavior that only appears at runtime,
such as reflection or dynamic dispatch"*, and *"a partial graph both flags paths that do not exist and misses
paths that do"*. govulncheck itself documents the asymmetry: interface and function-pointer calls are handled
conservatively (false positives), `reflect` calls are invisible (false negatives), and binary mode has no call
graph at all.

**Practical consequence:** the free, deterministic, non-vendor reachability path today is **Go only**. For
every other ecosystem RDA downgrades *"unreachable, therefore safe"* to *"unreachable per `<tool>`, unverified
for reflection, dependency injection and dynamic dispatch"*, and cites the VEX justification rather than
asserting non-exploitability.

**There is no machine-checkable production-readiness standard.** RDA-23's gate is a defined policy of this
framework, and says so rather than implying external authority.

## 4. Runtime expectations

**Unverified for essentially every tool at 100k+ files** — no vendor publishes monorepo runtimes, and only
CodeQL publishes RAM/CPU sizing by lines of code. RDA therefore treats tool runtime as a **measured** quantity:
the orchestrator records wall-clock per tool in the run manifest on the first execution and uses those figures
to budget subsequent runs. Do not plan against published benchmarks that do not exist.
