---
name: rda-08-data-layer-review
description: Reviews schemas and constraints, migration safety, transaction boundaries, N+1 and unindexed predicates, caching and data lifecycle. Run whenever the census finds migrations, ORM models or SQL.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-08"
  layer: "1-structure"
  risk_class: "MEDIUM_HARM"
  tier: "core"
  depends_on: "RDA-02"
---

# RDA-08 · Data Layer Review

Inherits RDA-00. Parallel group A. Data defects are the least reversible class in the framework, and the schema
in the repository is **intent**: the live schema is state, and only a dump from the database settles the two.

## Purpose
Produce the cited data-layer inventory: schema objects and constraints, migration risk register, transaction
boundaries and isolation, query hot spots and index gaps, cache invalidation map, and lifecycle paths in code.

## Business value
Migration mistakes, missing constraints and transactions spanning network calls are the incidents no rollback
repairs. It also supplies the constraint evidence RDA-07 triangulates against and RDA-16 needs for deletion.

## When to use
Whenever `census.units.migration_dirs` or `census.risk_surface.sql_files` is non-zero, or ORM models exist —
which is every core profile with persistence. Before any migration-heavy release or database platform change.

## When NOT to use
Not for capacity planning or measured query performance (RDA-24 plus telemetry), and not as a substitute for a
DBA review against the live database, which is the only place the real schema and real plans exist.

## Inputs
`census.json` keys `units.migration_dirs`, `risk_surface.sql_files`, `files.config`, `files.source` ·
`entrypoints.json` when RDA-03 has run, to attribute write paths to their callers · pinned SHA.

## Procedure

1. **Schema extraction (deterministic, 100%).** Locate DDL with
   `git ls-files | rg '(migrations?|db/migrate|alembic|liquibase|flyway|prisma)/|\.sql$|schema\.rb'`; extract
   objects with `rg -n -o --pcre2 '(?i)create\s+(table|index|type|trigger)\s+([a-z0-9_."]+)' -r '$1 $2'` and
   constraints with `rg -n --pcre2 '(?i)(primary key|foreign key|unique|check|not null|on delete)'`; read ORM
   models via `ast-grep` (`class $M(Base)`, `@Entity`, gorm tags). Emit `schema-objects.csv` with locators.
2. **Migration ordering and safety.** Sort by version; detect duplicate versions, gaps, missing rollbacks, and
   historical migrations edited after release (`git log --follow --format='%aI %H' -- <file>` with more than
   one commit after the first tag containing it). Then lint: `squawk migrations/*.sql` for Postgres, or
   `atlas migrate lint --dir file://migrations --dev-url <dev-db> --latest 20` where a dev database exists.
   Degraded fallback with no linter: grep the destructive and blocking set — `DROP (TABLE|COLUMN)`,
   `ALTER .* TYPE`, `RENAME`, `ADD COLUMN .* NOT NULL` without a default, `CREATE INDEX` without
   `CONCURRENTLY`, `UPDATE|DELETE` with no `WHERE`, and backfills inside a DDL transaction.
3. **Transaction boundary map.** `rg -n -e '(BEGIN|START TRANSACTION|COMMIT|ROLLBACK)' -e '@Transactional' -e
   'transaction\.atomic' -e '(db|conn)\.Begin(Transaction)?\(' -e 'SET TRANSACTION ISOLATION LEVEL'`. Per
   boundary record the declared isolation level — where none is declared, the engine default is an
   **assumption**, named as such, not a fact — what executes inside it, and whether serialization failures are
   retried. An outbound HTTP call, message publish or sleep inside a transaction is a cited finding.
4. **Query inventory and N+1 candidates.** Extract raw SQL and ORM call sites with `ast-grep`, join to entry
   points where RDA-03 ran, and mark structural N+1 candidates — a query call lexically inside a loop or
   comprehension, or a lazy relation dereferenced during iteration: `ast-grep run -l python -p 'for $X in $Y:
   $$$ $Z.objects.$M($$$)'`, one pattern per language in scope.
5. **Index coverage against predicates.** Join the `CREATE INDEX` set from step 1 with the `WHERE`, `JOIN` and
   `ORDER BY` columns extracted in step 4; emit predicates with no matching leading index column. Without
   `EXPLAIN` these are **candidates**, never performance claims, and they are labelled that way in the file.
6. **Cache and invalidation map.** Locate cache reads and writes (`redis`, `memcache`, `@cache`,
   `cache\.(get|set)`, HTTP cache headers), key construction and TTLs. The finding is not the cache, it is the
   write path to a cached entity with no invalidation site: cite the writer and the absent invalidation.
7. **Data lifecycle in code.** Retention and purge jobs, soft versus hard delete, archival and export paths,
   cascade declared in DDL versus enforced in the application. Mechanisms only — personal-data classification
   is handed to RDA-16, never guessed here.
8. **Disconfirming pass.** Before any "no index" claim, search other migration directories, `schema.rb`,
   `structure.sql` and ops repositories. Before any N+1 claim, search for eager loading — `select_related`,
   `prefetch_related`, `joinedload`, `@EntityGraph`, `Include(`, dataloader batching — which is the most common
   false positive this skill can produce. Record both queries and their results.
9. **Targeted read.** Read the highest-risk migrations, the largest transaction boundaries, and the write paths
   feeding cached or money-bearing tables. Cite ranges.
10. **Emit** the inventories, the migration risk register and one coverage record per population.

## Outputs
`schema-objects.csv` · `migration-risk.csv` (with linter name, version, exit code) · `transactions.csv` ·
`query-hotspots.csv` · `index-gaps.csv` (candidates) · `cache-map.csv` · `lifecycle.md` · `data-coverage.json`.

## Evidence requirements
Every schema object, constraint, boundary and query site cites `path#Lstart-Lend` with SHA and quote. Linter
output carries tool name, version, args and exit code. "The schema has no foreign keys" requires the exhaustive
constraint sweep of step 1 over the full DDL population, or it is `UNKNOWN`.

## Fact vs inference rules
`FACT`: this DDL statement, constraint, boundary or query exists at a locator. `INFERENCE`: a risk conclusion
from two or more of them. Ceilings on top of ES-1 §2 — may **not** assert that the live schema matches the
repository (`HYPOTHESIS`; only a dump settles it); may not assert query latency, row counts, table sizes or
index usage (`EXTERNAL_VALIDATION_REQUIRED`); may not assert a migration is safe at production scale, which
depends on table size and traffic (`EXTERNAL`); may not assert the effective isolation level when it is an
engine default that no cited config sets; may not assert an index is unused or a table is dead.

## Confidence scoring rules
C3 for migration findings produced by `squawk` or `atlas migrate lint` with version and exit code, and for
constraints read directly from DDL. C2 for ORM-derived schema corroborated by a migration, and for N+1
candidates surviving the eager-loading search. C1 for ORM-only schema claims and grep-derived index gaps.

## Repository coverage rules
Three populations, each with its command. **Migrations**:
`git ls-files | rg '(migrations?|db/migrate|alembic|liquibase|flyway)/' | wc -l`, reconciled with
`census.units.migration_dirs`. **Query sites**: count of
`ast-grep`/`rg` hits over the SQL and ORM patterns across 100% of non-vendored source, cross-checked against
`census.risk_surface.sql_files`. **Transaction boundaries**: the step-3 hit count. Migration coverage must be
`EXHAUSTIVE` or the migration verdict is not issued; query coverage is normally `RISK_WEIGHTED` and says so.

## Large repository strategy
Shard by database or service, sorted. Steps 1-3 stay exhaustive: DDL is small relative to source and a sampled
migration review is worthless, because the dangerous migration is the one not sampled. Budget steps 4-7 by
write-path risk. Shards emit rows; the merge groups by physical table so cross-service writers surface.

## Failure conditions
Schema managed outside the repository (ops repo, console DDL, managed platform) — record as a blind spot and
downgrade every schema claim · no linter and no dev database (declared degradation) · ORM models with no
migrations, meaning the schema history is unverifiable · dynamic SQL assembled at runtime that no parser reads.

## Escalation conditions
A destructive migration on a release branch with no rollback · a migration dropping a column still referenced
in code · committed database dumps · personal data in fixtures (halt, RDA-16) · credentials in a DSN (RDA-10).

## External validation required
The live schema and its drift from migrations · table sizes and query plans · which indexes exist in production
· backup and restore evidence · retention policy the code is meant to implement.

## Known limitations
Static analysis cannot see plans, cardinality or lock behaviour, so every performance statement here is a
candidate; dynamic SQL, stored procedures and database-side jobs are visible only if defined in the tree.

## Success criteria
Every migration carries a safety verdict or an explicit `UNKNOWN` · every transaction boundary lists its
contents · index gaps are labelled candidates · no live-schema, volume or latency claim exceeds its ceiling.

## Example prompts
- Claude Code / Cursor: "Use rda-08-data-layer-review: extract schema objects and constraints, lint every migration, and map transaction boundaries that contain network calls."
- Codex: "$rda-08-data-layer-review — list N+1 candidates and unindexed predicates for ./services with citations, after searching for eager loading."
- Antigravity / Gemini CLI: "/rda-data-review migrations=db/migrate dialect=postgres output=migration-risk.csv"
