---
name: rda-16-data-governance-privacy
description: Classifies personal, health and payment data in schemas and code and evidences collection, retention, erasure, logging and transfer paths; use when regulated-data indicators appear in the census.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-16"
  layer: "2-risk"
  risk_class: "HIGH_HARM"
  tier: "conditional"
  depends_on: "RDA-08"
---

# RDA-16 · Data Governance & Privacy

Inherits RDA-00. This produces evidence for a record of processing, never a privacy or lawfulness verdict.

## Purpose
Classify the personal, health and payment data this codebase handles, then evidence where it enters, where it
rests, where it is logged, how long it stays, how it is erased and where it is sent.

## Business value
The controller's questions — what personal data do we hold, for how long, and can we actually delete it — are
usually answered from memory by whoever has been there longest. Answering them from cited schemas turns an
Article 30 record into an evidence trail, and surfaces the erasure paths never wired to the search index.

## When to use
When the census reports personal-data indicators, payment or health fields, or a regulated sector is in scope.

## When NOT to use
As a legal assessment, a DPIA or a residency determination. Region config is intent; access control is RDA-11.

## Inputs
RDA-08 schemas, migrations, ORM models and lifecycle · `census.json` `risk_surface.personal_data_files` ·
`entrypoints.json` · RDA-13 SBOM for third-party processors · the policy classification dictionary.

## Procedure

**1. Build the schema population (deterministic).** Migrations, DDL, ORM models, protobuf and OpenAPI schemas,
event contracts and fixtures: `git ls-files | rg
'(migrations?|db/migrate|alembic|models?|schema|proto|openapi)'` and `rg -n 'CREATE TABLE|ALTER TABLE ADD
COLUMN' -g '*.sql'`. Field names come from the schema, never from guesswork.

**2. Classify fields against a declared dictionary.** `rg -n -iF -f policy/pii-terms.txt` over the schema
population, then classify each match: identifier · contact · financial (PAN, CVV, track data) · health ·
special-category · behavioural · pseudonymous. **The dictionary is policy, not fact** — it is versioned with the
run, printed in the output, and every classification cites both the field's locator and the dictionary entry
that matched it.

**3. Locate collection points.** Join classified fields to `entrypoints.json` handlers and to RDA-08 write
paths: which route, job or consumer first writes each field. Third-party collectors count — analytics, session
replay, error trackers and support widgets from the RDA-13 SBOM collect at the client, and their presence is
cited from the manifest that includes them.

**4. Logging and serialisation exposure.** For each classified field, search inside logging and serialisation
calls: `semgrep --config policy/pii-logging.yaml --sarif -o out/pii-logging.sarif` (a policy ruleset shipped
with this skill), degraded to `rg -n -i '(logger|log|console|print|slog)\.[a-z]+\(.*<field>'`. Cover error
handlers and stack traces, request/response dumps, analytics events, cache keys and message payloads. Logs are
the store nobody classifies and everybody retains.

**5. Retention and erasure paths.** Evidence per store: TTL and lifecycle rules (`expireAfterSeconds`, DynamoDB
`ttl`, `aws_s3_bucket_lifecycle_configuration`, purge jobs), soft-delete columns (`deleted_at`), cascade
behaviour (`ON DELETE CASCADE`, ORM `cascade=`). Then trace erasure to **every** store in the lineage —
database, replicas, search index, cache, object storage, event log, warehouse, backups. Reaching only some is
`INCOMPLETE` with the misses named; `COMPLETE` needs a citation per store.

**6. Transfer intent.** Region literals and endpoints in config and IaC, SDK default regions, CDN and processor
endpoints, and sub-processors implied by the SBOM. Per ES-1 §2 this is **intent, not state**: "data is stored in
region R" is capped at `HYPOTHESIS` and carries the cloud-console question that would settle it.

**7. Lineage.** Per classified field, the chain entry → primary store → derived store → export → third party,
one locator per hop. Hops that cannot be established are `UNKNOWN` and are listed, not silently dropped; a
lineage with an unexplained hop is the finding.

**8. Fixture and dump sweep, with ESC-1.** Scan fixtures, seed data, test databases and committed dumps for
real-looking personal data (`presidio-analyzer` where available, otherwise the dictionary grep). On a hit:
**halt traversal of that path, record location and class only, never the values, and escalate to the privacy or
DPO role**. Then run the disconfirming query per finding: a tokenisation layer, a redaction filter in the
logger, a synthetic-data generator, or an existing deletion job that already covers the store.

## Outputs
`data-inventory.csv` (field, class, store, collection points, logging exposure, retention evidence, erasure
status, transfer intent) · `lineage.csv` · `article30-evidence.md` (categories of data and recipients,
transfers, retention, technical measures — each cited, with gaps marked) · escalation notices.

## Evidence requirements
Every classification cites `path#Lstart-Lend` plus commit SHA for the field and the dictionary entry matched.
Retention and erasure claims cite the implementing code. No output contains a value from a fixture, dump or log.

## Fact vs inference rules
`FACT`: this schema declares this field at this locator; this logger call includes it. `INFERENCE`: this field
holds personal data — dictionary match plus a second signal such as a validator, a type, or a route that
populates it. `HYPOTHESIS`: data residency, and completeness of any erasure path not traced to every store.
**Never emitted:** that processing is lawful, that consent is valid, or that the system is GDPR/HIPAA/PCI
compliant.

## Confidence scoring rules
HIGH/CRITICAL data-governance findings require **C3**: a deterministic tool (semgrep policy rule, schema parser,
scanner) with version and exit code plus the schema citation. Field-name-only classification is C1 and ships as
a verification task. Erasure `COMPLETE` requires C3 with a citation per store in the lineage.

## Repository coverage rules
Population is declared fields: `rg -c 'CREATE TABLE|ADD COLUMN' -g '*.sql' | awk -F: '{s+=$2} END {print s}'`
plus ORM attributes, reconciled with `jq '.risk_surface.personal_data_files' rda-out/census.json`.
Classified-field and store coverage are reported separately; opaque columns count as UNKNOWN, never as "no
personal data".

## Large repository strategy
Shard by data store or bounded context, not directory, so a lineage is never split. Dictionary and semgrep
passes run over 100%; reading budget goes to stores holding health, payment or special-category data.

## Failure conditions
Schema held outside the repository (console-managed, no migrations) · document schemas with no declared fields ·
opaque column names · tokenised columns whose plaintext class is unknowable · fixtures too large to scan.

## Escalation conditions
Real personal, health or payment data in fixtures, logs, seed files or committed dumps halts that traversal and
escalates to the privacy/DPO role per ESC-1 · payment card data (PAN or CVV) anywhere in the tree ·
special-category data with no access control on its route · an erasure path that reaches no store at all.

## External validation required
Which stores hold production data · lawful basis and consent records · the written retention policy · processor
agreements and sub-processor lists · actual cloud regions · whether backups are in the erasure procedure.

## Known limitations
Two ways this skill produces a wrong answer. **(a) The field-name fallacy** — `user_note` holds free-text health
data while `col_17` holds a national identifier, so a name-matched inventory is both over- and under-inclusive;
prevented by declaring the dictionary as policy, requiring a second signal before `INFERENCE`, and counting
opaque columns as UNKNOWN. **(b) The erasure illusion** — an erasure endpoint exists, so the report says erasure
works, while the search index, cache and backups keep the record; prevented by the per-store citation
requirement, with `INCOMPLETE` as the default. Encryption also changes exposure without changing classification.

## Success criteria
Every classified field cites a schema locator and a dictionary entry · erasure status carries a citation per
store · residency stated as intent · zero data values anywhere · coverage against the schema denominator.

## Example prompts
- Claude Code / Cursor: "Run rda-16-data-governance-privacy: classify fields from the migrations, then trace the erasure path for each store."
- Codex: "$rda-16-data-governance-privacy — build the data inventory and lineage, and flag every classified field that reaches a log statement."
- Antigravity / Gemini CLI: "/rda-data-governance scope=. dictionary=policy/pii-terms.txt output=data-inventory.csv"
