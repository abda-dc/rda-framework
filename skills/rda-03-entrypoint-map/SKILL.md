---
name: rda-03-entrypoint-map
description: Cited inventory of every execution entry point - HTTP/gRPC routes, consumers, cron, CLI, serverless, webhooks, startup and admin hooks. Run right after census, before any risk skill.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-03"
  layer: "1-structure"
  risk_class: "HIGH_HARM"
  tier: "core"
  depends_on: "RDA-02"
---

# RDA-03 · Entry-Point Map

Inherits RDA-00. Parallel group A, first skill after census. RDA-05, RDA-06, RDA-11, RDA-12 and RDA-27 all
divide by this population, so an entry point missed here is missed by the whole audit, silently.

## Purpose
Enumerate every way execution starts in the pinned tree, one resolvable locator per entry point, and publish
`entrypoints.json` as the risk-surface denominator for the rest of the framework.

## Business value
Attack surface, blast radius, test gaps and reachability all reduce to "how does code start running here".
Without a counted inventory, an audit reports the files someone opened and calls it the system.

## When to use
Immediately after RDA-02, in every profile, before any security, API, dependency or threat-model skill. Re-run
whenever the pinned commit changes; entry points are the fastest-moving population in the census.

## When NOT to use
Never skipped in a core profile. Do not use it to decide whether an entry point is live, routable from the
internet, or receiving traffic — those are deployment and telemetry questions, not source questions.

## Inputs
`census.json` keys `files.tracked`, `files.vendored`, `files.generated`, `risk_surface.route_files`,
`units.build_manifests`, `units.k8s_manifests`, `units.ci_workflows` · pinned SHA · RDA-02 exclusion list.

## Procedure

1. **Fix the population (deterministic, 100%).** Build `population.txt` with `git ls-files -z | tr '\0' '\n' |
   grep -vFf exclusions.txt`. Every count here divides by `wc -l < population.txt`. No model input at this step.
2. **Transport sweep with ripgrep over 100% of `population.txt`**, one pass per family, as `rg -n --pcre2
   --no-heading --json -f patterns/<family>.txt`, recording tool version and exit code. Anchors — **HTTP**:
   `@(app|router|blueprint)\.(get|post|put|patch|delete|route)\(`, `@(Get|Post|Put|Delete|Request)Mapping`,
   `http\.HandleFunc\(`, `\[Http(Get|Post|Delete)\]`, `Map(Get|Post|Controllers)\(`, `path\(|re_path\(`.
   **gRPC**: `Register\w+Server\(`, `^\s*rpc\s+\w+` with `-g '*.proto'`. **Consumers**:
   `@(Kafka|Rabbit|Jms|Sqs|Stream)Listener`, `@(shared_task|app\.task)`, `Sidekiq::(Worker|Job)`,
   `\.(subscribe|consume)\(`. **Schedules**: `kind:\s*CronJob`, `@Scheduled|cron\.schedule\(`, `schedule:` under
   `.github/workflows/`, `crontab`, `*.timer`. **Serverless**: `AWS::Serverless::Function`, `handler:` under
   `functions:`, `function.json`, `lambda_handler`. **CLI**: `[project.scripts]`, `"bin"` in `package.json`,
   `cobra\.Command\{`, `func main\(`. **Startup**: `on_event\(['"]startup`, `@PostConstruct`, `func init\(\)`.
   **Admin/debug**: `debug/pprof`, `actuator`, `django.contrib.admin`, `graphiql`. **Database-side**:
   `CREATE (OR REPLACE )?TRIGGER`, `AFTER (INSERT|UPDATE)`, `pg_cron`. Fallback if `rg` is absent: `git grep
   -nIE` with alternations split, no PCRE2, degradation recorded.
3. **Structural confirmation.** Re-express each family as an AST query where a parser exists — `ast-grep run -l
   python -p '@$APP.$M($PATH, $$$)' --json`, `-l go -p '$R.HandleFunc($P, $H)'`, `tree-sitter query routes.scm`.
   Grep-only hits are comments or fixtures until proven; AST-only hits prove the pattern set is incomplete and
   it is widened before proceeding. No parser: `TOOL_UNAVAILABLE`, family capped at C1.
4. **Declared-contract sweep.** `jq -r '.paths|keys[]' openapi.json`, `yq -o=json '.paths|keys' openapi.yaml`,
   `rg -n '^\s*rpc\s' -g '*.proto'`, GraphQL root fields from the SDL. Declarations are not entry points; they
   join to implementations in step 7, and unmatched entries either way become RDA-05 drift input.
5. **Mount-chain resolution.** Follow every mount to the externally visible path: `include_router(prefix=)`,
   `app.use('/v1', r)`, `router.Group("/api")`, `include()` in `urlpatterns`, `scope`/`namespace`, servlet
   mappings, ingress rewrites. A path without its mount chain is wrong, not partial — emit `path_resolved` plus
   a `mount_evidence` locator, or mark it `UNKNOWN`.
6. **Dynamic-registration sweep (mandatory).** Grep registrars that create entry points at runtime:
   `add_url_rule`, `add_api_route`, decorator factories, `@ComponentScan`, DI registrations, route tables read
   from config or a database, `importlib`, reflection, plugin loaders. Each resolves to its literal argument
   source or is listed as a coverage gap — this is what stops the inventory under-counting.
7. **Guard join.** Per entry point record transport · declared and resolved path · handler symbol with
   `path#Lstart-Lend` · declaring unit · mount evidence · guard marker (decorator, middleware, filter chain,
   policy) or `UNKNOWN`. A guard marker is the presence of a construct, never an authorisation verdict; RDA-11
   adjudicates whether it works.
8. **Targeted read pass (risk-weighted).** Read handler bodies only for externally mounted, no-guard-marker,
   admin/debug, and money- or personal-data-adjacent entry points from the census strata. Cite line ranges.
9. **Disconfirming pass.** Before any "no guard" claim, query the opposite: global middleware registration,
   gateway config, default-deny settings, base-class filters, tests asserting 401/403; record it or cap at C1.
10. **Emit** `entrypoints.json`, the coverage record, and the unresolved-registrar list.

## Outputs
`entrypoints.json` (transport, declared and resolved path, handler locator, commit, guard marker, unit,
evidence) · `entrypoint-coverage.json` · `dynamic-registrars.md` · `contract-drift.csv` handed to RDA-05.

## Evidence requirements
Every row cites `path#Lstart-Lend`, the commit SHA and a verbatim quote of the declaration; counts carry tool
name, version, args and exit code. If the quote lacks the route string or annotation, the row is not a row.

## Fact vs inference rules
`FACT`: a declaration exists at a locator. `INFERENCE`: the resolved external path, from the declaration plus
each cited mount. Ceilings on top of ES-1 §2 — never assert that an entry point is deployed, routed or
internet-reachable (`HYPOTHESIS`; ingress, gateway and DNS are out of scope); that one is unauthenticated
(`INFERENCE` only after step 9, else `HYPOTHESIS`); that one is dead (`HYPOTHESIS`, BSR-11, owned by RDA-27);
or that the inventory is complete while step 6 has unresolved registrars.

## Confidence scoring rules
C3 where grep and AST agree with a recorded tool version and exit code; C2 for grep plus targeted read plus
disconfirming search; C1 for single-pattern hits, degraded runs, parser-less families, and any path resolved
through an unresolved config value.

## Repository coverage rules
Population is **entry-point declaration sites**, not files. File denominator: `wc -l < population.txt`, which
must equal `census.files.tracked - census.files.vendored - census.files.generated`. Entry-point denominator: the
reconciled row count from steps 2-3, with its producing command. Report artifact coverage (files swept / file
denominator, which must be 1.0) and risk-surface coverage (rows read in step 8 / rows emitted).
`census.risk_surface.route_files` is a file count and may never serve as the entry-point denominator.

## Large repository strategy
Shard by deployable unit from `census.units.build_manifests`, sorted, seed recorded. Steps 1-6 are grep/AST and
stay exhaustive on every shard regardless of budget — they are cheap. Only step 8 is budgeted. Shards emit rows,
never prose; the merge de-duplicates on `(unit, transport, resolved_path)`. On budget exhaustion drop reads, not
the sweep, and record `ABORTED_BUDGET` against step 8 alone.

## Failure conditions
No parser and no `rg` (grep-only, declared) · a framework in the build manifests with no pattern family defined —
stop and add one · generated route code excluded by RDA-02 but compiled into the build · unresolvable mount
chains above a policy threshold of 10% of routes.

## Escalation conditions
Admin, debug or maintenance entry points with no guard marker and an external mount · entry points that execute
a shell, deserialise untrusted input or read secret material · webhook handlers verifying no signature.

## External validation required
Which entry points the gateway actually exposes · which listeners have live topics · which cron schedules are
enabled per environment · whether admin surfaces are network-restricted.

## Known limitations
Pattern-driven discovery finds the idioms it was told about. Entry points from reflection, build-time code
generation or a database-held route table appear only as registrars; vendored and generated declarations are
excluded by census policy. Both are stated blind spots, never silence.

## Success criteria
Every row resolves at the pinned SHA · AST and grep sets reconcile with a stated residual · no downstream skill
cites an entry point absent from `entrypoints.json` · unresolved registrars listed, not rounded away.

## Example prompts
- Claude Code / Cursor: "Use rda-03-entrypoint-map here: sweep every entry-point family, resolve mount chains, write entrypoints.json with path#Lx-Ly citations."
- Codex: "$rda-03-entrypoint-map — inventory routes, consumers, cron and CLI commands per service in ./services; flag externally mounted routes with no guard marker."
- Antigravity / Gemini CLI: "/rda-entrypoint-map scope=. ast=on output=entrypoints.json"
