---
name: rda-09-config-env-review
description: Inventories config sources and precedence, environment parity, feature-flag staleness, unsafe defaults and secret references. Run after census, before the dependency graph and security skills.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-09"
  layer: "1-structure"
  risk_class: "MEDIUM_HARM"
  tier: "core"
  depends_on: "RDA-02"
---

# RDA-09 · Configuration & Environment Review

Inherits RDA-00. Parallel group A. RDA-06 cannot resolve an `ORDERS_URL` without the precedence chain produced
here, and RDA-11 cannot rank a weakness without it. **A default in code is not the deployed value.**

## Purpose
Produce the configuration inventory: every key and its sources, the precedence order that resolves them,
environment parity, dated feature flags, unsafe defaults, config-reachable sinks, and secret references.

## Business value
Most "it worked in staging" incidents are configuration, not code, and configuration decides whether other
findings are real: a debug surface enabled by one variable, an auth bypass behind a flag, a wrong host.

## When to use
After RDA-02 in every core profile; mandatory before RDA-06, RDA-10 and RDA-11, which all consume its output.

## When NOT to use
Not to state what is configured in a running environment — that is undecidable from source. Not for secret
*detection*, history scanning or rotation: RDA-10 owns those, and this skill only records references.

## Inputs
`census.json` keys `files.config`, `files.infrastructure`, `units.ci_workflows`, `units.k8s_manifests`,
`units.iac_files`, `units.compose_files`, `risk_surface.secret_pattern_files` · pinned SHA.

## Procedure

1. **Source inventory (deterministic, 100%).** Enumerate and classify every configuration source: in-tree files
   (`git ls-files | rg '\.(env[^/]*|ini|toml|ya?ml|json|properties|conf)$'` intersected with the census config
   and infrastructure paths), framework modules (`settings.py`, `appsettings*.json`, `application*.y*ml`),
   Dockerfile `ENV`, compose `environment`/`env_file`, k8s `env`, `envFrom`, `configMapKeyRef`, `secretKeyRef`,
   Helm values, CI and IaC variables, and remote stores (SSM, Secrets Manager, Vault, Consul, AppConfig).
2. **Key extraction.** Reads: `rg -n --pcre2 -e 'os\.(getenv|environ)' -e 'process\.env\.[A-Z0-9_]+' -e
   'System\.getenv\(' -e 'ENV\[' -e 'viper\.Get' -e '@Value\("\$\{' -e 'Configuration\['`. Setters: the
   sources from step 1. Emit `config-keys.csv` with key, kind (read or set), source class, locator, and the
   literal default where one exists.
3. **Precedence chain — the artifact other skills consume.** Establish the real resolution order by reading the
   loader, not by convention: `load_dotenv` ordering, `viper.AutomaticEnv`/`SetConfigFile`, Spring profile
   order, `appsettings.{Environment}.json` overlay, k8s `env` overriding `envFrom`, compose `environment`
   overriding `env_file`. Cite the loader lines. Where the order cannot be established from source it is
   `UNKNOWN`, and that caps every value-dependent claim in RDA-06 and RDA-11 downstream.
4. **Environment parity (deterministic).** Diff key sets per environment:
   `comm -13 <(rg -o '^[A-Z0-9_]+' .env.staging | sort -u) <(rg -o '^[A-Z0-9_]+' .env.production | sort -u)`,
   the same across k8s overlays via `kubectl kustomize overlays/<env> | yq -o=json`, and across CI environments.
   Report keys present in one environment and absent in another, and keys whose shape differs (single host
   versus list, URL versus path) — shape drift causes the failures that key-presence checks miss.
5. **Feature flags and their age.** Locate SDK call sites (`variation(`, `isEnabled(`, `getBooleanValue(`,
   `flipper`, `waffle`) and homegrown boolean env flags. Date each flag with
   `git log -S'<flag-key>' --reverse --format='%aI %H' -- . | head -1`. **Policy of this skill:** a flag
   introduced more than 180 days before HEAD whose reads are all unconditional is a staleness candidate. The
   threshold is a stated policy, not a measurement, and prints above the list.
6. **Unsafe defaults sweep (100%).** One `rg -n --pcre2` pass per pattern: `(?i)debug\s*[:=]\s*(true|1|on)`;
   `(?i)allowed_hosts\s*=\s*\[?["\x27]\*`; `(?i)(rejectUnauthorized|InsecureSkipVerify|verify)\s*[:=]\s*false`;
   `Access-Control-Allow-Origin["\x27:\s]+\*`; `0\.0\.0\.0`; `(?i)(secure|httponly)\s*[:=]\s*false`;
   `(?i)(password|user)\s*[:=]\s*["\x27](admin|root|changeme)`. Each hit is a candidate; step 3 decides reality.
7. **Config as attack surface.** Trace configured values into dangerous sinks: hosts used by outbound fetchers
   (SSRF), values interpolated into SQL, shell or templates, deserialisation switches, path prefixes used in
   file operations, and remote configuration fetched without integrity verification. Cite key and sink.
8. **Secret referencing, never detection.** Record where secret material is referenced: key names matching
   `(SECRET|TOKEN|PASSWORD|KEY|CREDENTIAL)`, `secretKeyRef`, Vault paths, CI `secrets.` expressions, mounted
   files. **Never print a value.** Literal secret-looking material in a tracked file halts this skill and goes
   to RDA-10 with locator and type only, per ESC-1.
9. **Disconfirming pass.** Before "this key is never set", search every setter class from step 1 including
   `.env.example`, CI environments and IaC; unmatched reads are `UNKNOWN`, not "missing". Before "debug is
   enabled", resolve the precedence chain. Record both queries and their results.
10. **Emit** the inventory, the precedence document and one coverage record per population.

## Outputs
`config-inventory.csv` · `precedence.md` (loader citations first) · `env-parity.csv` · `feature-flags.csv` (key,
introduction date, read sites, verdict) · `unsafe-defaults.csv` · `config-sinks.csv` · `secret-references.csv`
(names and locations only) · `config-coverage.json`.

## Evidence requirements
Every key row cites `path#Lstart-Lend` with SHA and quote for at least one read or setter. Precedence claims
cite the loader line that establishes the order. Parity rows cite both environment files. No row in any output
of this skill contains a secret value, ever.

## Fact vs inference rules
`FACT`: this key is read here; this file sets it to this literal; this loader runs in this order. `INFERENCE`:
the resolved value for an environment, derived from the precedence chain plus cited setters. Ceilings on top of
ES-1 §2 — may **not** assert the deployed value of any key (`HYPOTHESIS` at best; the platform is the store of
record); may not assert a flag's runtime state (`EXTERNAL_VALIDATION_REQUIRED`); may not treat in-repo IaC or
manifests as environment state; may not assert which environment is production; may not assert a key is unused.

## Confidence scoring rules
C3 where a key's read site, its setter and the loader order are all cited and a deterministic diff produced the
parity result. C2 where read and setter agree with a recorded disconfirming search. C1 for read-only keys,
unresolved precedence, flags dated from a shallow clone, and any unsafe-default hit not resolved through step 3.

## Repository coverage rules
Three populations. **Config artifacts**: denominator = `census.files.config + census.files.infrastructure`,
re-derived as `git ls-files | rg '\.(env[^/]*|ini|toml|ya?ml|json|properties|conf)$' | wc -l` and reconciled.
**Config keys**: denominator = distinct keys from the step-2 command, `... | sort -u | wc -l`. **Feature
flags**: denominator = distinct flag keys from step 5. Report resolved keys over total keys — the unresolved
fraction is the honest measure of how much of the configuration surface this audit actually understood.

## Large repository strategy
Shard by unit and environment, sorted. Steps 1, 2, 4 and 6 stay exhaustive — configuration is small and the one
unswept file is the one with the unsafe default. Budget steps 3 and 7. The merge must resolve keys globally,
because the same key name in two units is often two different settings and must not be collapsed.

## Failure conditions
Configuration held entirely in a remote store or platform UI (blind spot, and every value claim drops to
`UNKNOWN`) · no loader readable in source, leaving precedence unresolved · encrypted config (SOPS, sealed
secrets, `ansible-vault`) that must not be decrypted · a shallow clone, which invalidates flag dating.

## Escalation conditions
Literal secret material in a tracked file — halt, do not print the value, hand to RDA-10 · TLS verification
disabled on a money or authentication path · remote configuration fetched over plaintext or without integrity
checks · a committed `.env` containing production-shaped credentials.

## External validation required
The deployed value of each key per environment · which environment is production · who can change flags and
configuration, and through what control · whether remote-store values diverge from in-repo defaults.

## Known limitations
Configuration is deliberately external, so this skill maps the surface and the resolution rules, not the state.
Parity is computed over files, a proxy for environments, and remotely evaluated flags are undecidable here.

## Success criteria
Every read key has a setter, a default, or an explicit `UNKNOWN` · the precedence chain is cited or declared
unresolved · no secret value appears anywhere in the outputs · RDA-06 can resolve its edges using this file.

## Example prompts
- Claude Code / Cursor: "Use rda-09-config-env-review: inventory every config key and setter, cite the loader precedence, and diff staging against production key sets."
- Codex: "$rda-09-config-env-review — list unsafe defaults and stale feature flags with git introduction dates, no secret values in the output."
- Antigravity / Gemini CLI: "/rda-config-review scope=. envs=staging,production output=config-inventory.csv"
