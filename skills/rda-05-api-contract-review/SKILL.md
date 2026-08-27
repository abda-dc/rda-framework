---
name: rda-05-api-contract-review
description: Reconciles API contracts against implemented routes - versioning, breaking changes, per-route authz, errors, pagination, rate limits. Trigger when OpenAPI, protobuf, GraphQL or public routes exist.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-05"
  layer: "1-structure"
  risk_class: "MEDIUM_HARM"
  tier: "conditional"
  depends_on: "RDA-03"
---

# RDA-05 · API Contract Review

Inherits RDA-00. Parallel group A, conditional on RDA-03 finding contract artifacts or externally mounted
routes. The specification is a claim about the API; the routes are the API. This skill compares the two.

## Purpose
Produce the reconciled API surface — promised operations, implemented operations, and the disagreements — with
per-operation authn/authz, error, pagination, rate-limit, versioning and deprecation determinations.

## Business value
The two API defects with direct external cost are the breaking change that silently breaks a paying consumer
and the write route that never had authentication. Both are decidable from source; both are missed by reading
the specification alone, because the specification is exactly the artifact that drifts.

## When to use
When RDA-03 emits HTTP, gRPC or GraphQL rows, or an OpenAPI/AsyncAPI/proto/SDL artifact exists; before a release
gate, an integration commitment, a public launch, or an M&A review of a product with API customers.

## When NOT to use
Libraries with no network surface. Not for throughput, latency or quota behaviour (RDA-24 and telemetry), and
not as a substitute for RDA-11 on the security adjudication of a specific handler.

## Inputs
`entrypoints.json` and `contract-drift.csv` from RDA-03 · `census.json` keys `files.config`, `files.tracked`,
`units.build_manifests` · release tags (`git tag --sort=-creatordate`) · pinned SHA.

## Procedure

1. **Inventory contract artifacts (deterministic, 100%).** `git ls-files | rg -i
   '(openapi|swagger)[^/]*\.(ya?ml|json)$|\.proto$|\.(graphql|gql)$|asyncapi[^/]*\.ya?ml$'`. Record count, path,
   declared version (`jq -r '.info.version'` / `yq '.info.version'`), and last-touch commit per file.
2. **Normalise the promised surface.** OpenAPI: `jq -r '.paths | to_entries[] | .key as $p | .value |
   to_entries[] | [$p, .key, .value.operationId, (.value.security|tostring)] | @tsv'` (`yq -o=json` first for
   YAML). Protobuf: `buf build -o -` or `rg -n '^\s*rpc\s+(\w+)' -g '*.proto'`. GraphQL: root fields of
   `Query`/`Mutation`/`Subscription` from the SDL. One row per operation, each with a locator.
3. **Join implemented against promised.** Left-join `entrypoints.json` on method + resolved path (gRPC:
   `package.Service/Method`). Emit three counted sets: documented-and-implemented, implemented-undocumented
   (shadow surface), documented-unimplemented (phantom contract). Each set is a finding class, not a note.
4. **Breaking-change exposure, computed not judged.** Against the last release tag: `oasdiff breaking
   <(git show <tag>:openapi.yaml) openapi.yaml`, `buf breaking --against '.git#tag=<tag>'`,
   `graphql-inspector diff <old.graphql> <new.graphql>`. If none is installed, derive from
   `git diff <tag>..HEAD -- <contract>` restricted to removed paths/fields, narrowed types, new required
   fields and removed enum values — record the degradation and cap the finding at C2.
5. **Versioning mechanism from routing code.** Determine which is actually in force — path prefix, `Accept`
   media type, version header, query parameter, or none — by citing the routing or middleware line, never the
   documentation. Count live versions and routes per version.
6. **Per-operation authn/authz.** Join RDA-03 guard markers and record scheme (none, session, bearer, mTLS,
   HMAC, API key), the evidence for it, and any scope or role requirement. Operation-level `security: []`
   overrides a global `security` block: read both, because misreading this is the standard false positive here.
   No "unauthenticated" claim ships without the disconfirming query of step 9.
7. **Error, pagination and limit semantics.** Status-code inventory per operation; use of problem+json
   (RFC 9457); error bodies leaking stack traces or internal identifiers; every collection route classified
   cursor / offset / unbounded, citing the handler line where a default and maximum limit would be; limiter
   middleware or ingress annotations mapped to routes, with unprotected write and auth routes named.
8. **Deprecation posture.** `deprecated: true` in OpenAPI, `@deprecated` in the SDL, `[deprecated = true]` in
   proto, and `Sunset` response headers (RFC 8594). Report deprecated-but-implemented operations with no
   announced removal, and undeprecated operations already removed from the implementation.
9. **Disconfirming pass.** For every "no auth", "no limit" or "breaking" claim, run the opposite search: global
   middleware and gateway or ingress policy, framework default-deny, base controllers, contract tests, and
   consumer fixtures. Record the query and its result per BSR-06.
10. **Emit** the reconciled surface with coverage records and the external-validation questions.

## Outputs
`api-surface.csv` (operation, transport, implementation locator, contract locator, auth scheme, pagination,
limit, deprecation) · `contract-drift.md` (three sets from step 3) · `breaking-changes.json` (tool output with
version and exit code) · `api-coverage.json`.

## Evidence requirements
Every operation row carries both locators where both exist: the contract locator (`openapi.yaml#L120-L138`) and
the implementation locator (`services/pay/routes.py#L44-L51`), each with SHA and quote. A row with only a
contract locator is a promise, and must be labelled as one.

## Fact vs inference rules
`FACT`: the contract declares an operation; the code registers a route; the tool reported a breaking change.
Ceilings on top of ES-1 §2 — the contract is evidence about the **document**, never about runtime behaviour; may
not assert an operation is internet-reachable or public (`HYPOTHESIS`; the gateway decides); may not assert a
breaking change harms a consumer, which requires knowing the consumers (`EXTERNAL_VALIDATION_REQUIRED`); may not
assert a rate limit or quota is effective (`EXTERNAL`); may not assert an operation is unauthenticated without
step 9; may not treat generated-at-build-time contracts as current unless regenerated at the pinned SHA.

## Confidence scoring rules
C3 for breaking-change findings emitted by `oasdiff`, `buf` or `graphql-inspector` with version and exit code,
and for auth determinations where contract, route decorator and middleware agree. C2 for two-locator rows with a
disconfirming search. C1 for contract-only rows, hand-diffed breaking changes, and unresolved gateway questions.

## Repository coverage rules
Two populations, both reported. **Promised operations**: denominator = row count from step 2, e.g.
`yq -o=json '.' openapi.yaml | jq '[.paths[]|keys[]]|length'` summed across contract files. **Implemented
operations**: denominator = HTTP, gRPC and GraphQL rows in `entrypoints.json`, which is itself derived from
`census.files.tracked` minus exclusions. The API surface is the union of the two, and coverage is reported
against the union — never against the contract alone, which is how shadow APIs stay invisible.

## Large repository strategy
Shard by service, sorted. Steps 1-4 are tool-driven and stay exhaustive. Budget step 6 by risk: externally
mounted write operations first, then auth and account operations, then reads. Shards emit rows; the merge
recomputes the three drift sets globally so that a route documented in one service and implemented in another
is not counted as phantom.

## Failure conditions
No contract artifact and no route rows (the skill does not apply — say so, do not synthesise a contract) ·
contracts generated at build time and absent from the tree · a gateway or BFF outside scope that owns routing ·
multiple contract files disagreeing with each other, which is itself the finding.

## Escalation conditions
An unauthenticated write, admin or account-recovery operation · an operation exposing personal or payment data
with no guard marker · credentials or tokens embedded in contract examples (hand to RDA-10 and halt that file) ·
a breaking change already merged to a release branch.

## External validation required
Who consumes each operation and at which version · what the gateway enforces before traffic reaches the service
· the real rate limits · whether deprecated operations were announced, and to whom.

## Known limitations
Contracts generated from code at build time are stale in-tree by construction; consumer-driven contract tests
living in consumer repositories are invisible here; example values in a specification are documentation, not
behaviour. Undocumented internal routes are found only if RDA-03 found them.

## Success criteria
Every implemented operation appears in the surface with an auth determination or an explicit `UNKNOWN` · the
three drift sets sum to the union population · every breaking-change claim carries tool output · no claim about
public reachability appears above `HYPOTHESIS`.

## Example prompts
- Claude Code / Cursor: "Use rda-05-api-contract-review: join entrypoints.json to openapi.yaml, list shadow and phantom operations, and run oasdiff against the last release tag."
- Codex: "$rda-05-api-contract-review — per-route auth and pagination table for ./services, flag unauthenticated writes and unbounded list endpoints."
- Antigravity / Gemini CLI: "/rda-api-review contracts=api/ base=v2.4.0 output=api-surface.csv"
