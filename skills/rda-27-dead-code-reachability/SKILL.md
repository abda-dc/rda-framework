---
name: rda-27-dead-code-reachability
description: Produces tiered unreferenced-code candidates gated by a twelve-category dynamic-entry sweep and runtime evidence, never a delete list; run only on explicit request to find dead or unused code.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-27"
  layer: "4-health"
  risk_class: "HIGH_HARM"
  tier: "optional"
  depends_on: "RDA-03, RDA-26"
---

# RDA-27 · Dead Code & Reachability

Inherits RDA-00. The most dangerous skill in the pack: elsewhere a wrong finding costs credibility, here it costs an outage, because someone deletes what you named.

## Purpose
Produce a tiered, defensible list of code that *may* be unreachable, together with the evidence anyone would need
before removing it — and refuse to go further than the evidence goes.

## Business value
Genuinely dead code inflates build time, review load, audit surface and vulnerable-dependency exposure, so removing
it pays. But the deliverable is the gate, not the list: an unreviewed "unused" list is an incident with a lead time.

## When to use
Optional and on explicit request only, after RDA-03 has enumerated entry points: migration and rewrite scoping,
attack-surface reduction, post-acquisition consolidation, or a maintenance-cost argument that needs a real numerator.

## When NOT to use
Without a completed RDA-03 · on a library or SDK whose public API is called from outside the repository by
construction · as input to an automated deletion PR · when no runtime signal exists (emit CANDIDATEs and stop).

## Inputs
RDA-03 entry points · census path classes and symbol counts · RDA-09 config and feature-flag inventory · RDA-26
hotspots · CI and production coverage/APM exports · scheduler, webhook and trigger config · sibling repos · SHAs.

## Procedure

**1. Deterministic candidate generation over 100% of the symbol population.** Record tool, version, exit code:
```
vulture . --min-confidence 80            > dc/vulture.txt     # Python — name-based, over-reports
knip --reporter json                     > dc/knip.json       # JS/TS exports+deps (ts-prune is archived: use knip)
staticcheck -checks U1000 ./... > dc/staticcheck.txt ; deadcode -test ./... > dc/deadcode.txt  # Go: under-reports
```
Degraded fallback where no tool exists: extract symbols, count references with `rg -uu -w -n --stats -- "<symbol>"`,
and treat definition-site-only matches as candidates. **The output of this step is never a finding.** It is a worklist.

**Polarity is tool-specific and must reach the tier.** Dynamic-language tools over-report — vulture's docs say it
"ignores scopes and only takes object names into account", knip ships a false-positive taxonomy — so their output is
CANDIDATE at best. Go's `deadcode` is sound, over-approximating reflection and dynamic dispatch, so it under-reports;
its docs warn deletion is not unconditionally safe and results hold for one recorded GOOS/GOARCH/-tags. ctags is never
a reachability source: definitions only, reference tags opt-in, and per its docs few parsers implement them.

**2. Mandatory dynamic-entry sweep — twelve categories, each searched, each result recorded.** A candidate leaving
without twelve results is a defect. `-uu` (`--no-ignore --hidden`) is mandatory: ripgrep's default filtering
(.gitignore, hidden files, the user's global `core.excludesFile`) hides vendored call sites and makes any count depend
on the auditor's local git config.
```
rg -uu -n "getattr\(|importlib|Class\.forName|reflect\.|method_missing" . ; rg -uu -n "@Bean|@Injectable|@Autowired" .
rg -uu -nF "<symbol>" -- config/ deploy/ *.ya?ml *.json *.toml *.tf .env* Makefile crontab*
```
(1) reflection and dynamic dispatch · (2) dependency-injection registration · (3) string-based lookup: routing tables,
factories, handler maps · (4) configuration and feature-flag references · (5) cron and scheduler entries (crontab, k8s
`CronJob`, Airflow, Quartz, Celery beat) · (6) webhook and partner callbacks · (7) serialisation targets, incl. ORM
entity discovery and proto/Avro names · (8) database triggers, views and stored procedures · (9) build-time codegen ·
(10) public API for external consumers (registry, OpenAPI, `.d.ts`, SDK) · (11) test-only usage · (12) platform entry
points (framework conventions, lambda handlers, manifests).

**3. Runtime signal and retention window.** Above CANDIDATE requires a production/staging coverage export, APM-traced
routes, request logs, flag-evaluation counts, profiler samples or merged instrumentation, recorded with tool,
environment and window. Nothing rises above PROBABLE unless that window covers the longest plausible invocation period
plus margin — annual billing, tax-year jobs, break-glass and DR paths. Policy default: 13 months, or 1.5× the longest
scheduler interval found in step 2, whichever is greater. **Policy, not evidence.**

**4. Tier the output; removal is only ever recommended at tier 3.** `CANDIDATE` — static non-reference only, stated as
"no static reference found within scope", never removable. `PROBABLE` — plus a clean twelve-category sweep and a
partial window: "no reference and no observed use in <window>", never removable. `CONFIRMED-BY-RUNTIME` — plus a
runtime signal covering the retention window and owner-role confirmation: "unused across <window> in <envs>",
removable only through staged deprecation.

**5. Staged deprecation is the only removal recommendation this skill emits.** (a) instrument the symbol and alert on
non-zero; (b) observe for the full retention window; (c) disable behind a flag or fail loudly; (d) observe again; (e)
delete in one revertible commit citing the finding id and the artifact. Never propose (e) alone.

**6. Disconfirming pass.** For every CONFIRMED item run one query designed to prove it live — the symbol across sibling
repos in scope, the infrastructure repo, the SQL directory, published API specs — and record the result.

## Outputs
`dead-code-candidates.csv` (symbol, locator, tier, tool polarity, twelve sweep results, window, owner role) · findings
· a coverage record per language · a deprecation plan per CONFIRMED item. Never a deletion patch or a "delete" column.

## Evidence requirements
Each candidate cites its definition site `path#Lstart-Lend` + commit SHA + quote; each of the twelve sweep categories
records its query and result; runtime signals cite tool, environment and window. Missing any one caps it at CANDIDATE.

## Fact vs inference rules
`FACT`: "no static reference found in <scope> at <SHA> by <tool v>", bounded by scope and by that tool's polarity.
`HYPOTHESIS`: "this code is dead" (ES-1 §2 ceiling from source alone); `INFERENCE` only with runtime evidence, a
covering window and owner confirmation. `EXTERNAL_VALIDATION_REQUIRED`: "safe to delete" — the owning role signs.

## Confidence scoring rules
CANDIDATE caps at C1, PROBABLE at C2, CONFIRMED-BY-RUNTIME at C3; a removal recommendation requires **C4**, the
instrumentation observation being the execution artifact. Three unused-symbol tools are one independence group.

## Repository coverage rules
Population = exported symbols, modules, routes and jobs counted by RDA-02/RDA-03, reported **per language** with each
tool's polarity: coverage is uneven, and one global percentage hides a language that was barely analysed.

## Large repository strategy
Shard by deployable unit but compute reachability **per unit and across units** before tiering — a symbol unreferenced
inside its own shard is the classic false positive. In multi-repo scope, sweep every repo first.

## Failure conditions
RDA-03 missing (stop) · no runtime access (cap at CANDIDATE and disclose) · metaprogramming-heavy codebase (declare
low confidence, stay at CANDIDATE) · shallow clone or missing sibling repos (sweep incomplete, so tiering is invalid).

## Escalation conditions
The candidate is the public API of a published package · it is a security control, where an unreferenced auth check is
more likely a bypass bug (hand to RDA-11) · it is a break-glass path · its schedule exceeds the window.

## External validation required
Does the symbol appear in a downstream consumer outside scope · is the job still registered in the live scheduler · is
the partner webhook still contracted · is the path retained for compliance · which role owns the removal decision.

## Known limitations
Two ways this skill produces a wrong answer, and the controls that stop them. **(a) Invocation through reflection, DI
or a string-keyed lookup** leaves no static reference — prevented by the step-2 sweep, mandatory, `-uu`-pinned and
individually recorded, and by the rule that static non-reference never exceeds CANDIDATE. **(b) A symbol exported for
external consumers, or called only from an out-of-scope caller,** looks unused inside the repository — prevented by
sweep categories 10 and 12 and the multi-repo rule. Coverage records what ran, never what is required.

## Success criteria
Zero removal recommendations below CONFIRMED-BY-RUNTIME · every candidate carries twelve sweep results and its
tool's polarity · every CONFIRMED item carries a staged deprecation plan and an owner role · no deletion patch.

## Example prompts
- Claude Code / Cursor: "Run rda-27-dead-code-reachability — candidates only, do the full dynamic-entry sweep, and do not recommend any deletion without runtime evidence."
- Codex: "$rda-27-dead-code-reachability — knip + staticcheck + deadcode over ./services, sweep DI/cron/webhook/config, emit dead-code-candidates.csv with tiers."
- Antigravity / Gemini CLI: "/rda-deadcode scope=. window=13m tier_max=CANDIDATE runtime=none"
