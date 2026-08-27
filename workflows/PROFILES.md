# RDA Execution Profiles

Each profile is a skill set, an order, a budget split and a stop rule. Profiles are selected by RDA-01 and
recorded in the run manifest; deviations from a profile are recorded as deviations, not silently absorbed.

---

## P1 · Small repository (<2,000 files, single deployable)
**Skills (17):** 00, 01, 02 -> 03, 07, 08, 09 -> 10, 11, 13 -> 18, 26, 28 -> 32 -> 33, 34, 36
**Order:** near-exhaustive; sampling is unnecessary at this size, so coverage should be EXHAUSTIVE or BROAD.
**Budget split:** 20% deterministic · 55% reading · 25% verification.
**Stop rule:** if coverage of the risk surface is below 0.8, the repository is not small — re-plan as P2.
**Typical output:** one report, one register, no portfolio layer.

## P2 · Medium repository (2k-20k files, few services)
**Skills (25):** P1 + 04, 05, 06, 19, 20, 21, 22, 29
**Order:** census -> group A -> groups B and C in parallel -> 31 -> 32 -> 33, 34 -> 36.
**Budget split:** 25% deterministic · 50% reading · 25% verification.
**Sampling:** RISK_WEIGHTED over the strata from census; HOTSPOT for quality.
**Stop rule:** any skill below INDICATIVE coverage reports leads only, never conclusions.

## P3 · Large monorepo (20k-500k files, many services)
**Skills:** all core + conditionals triggered by census, **sharded**.
**Order:** census per top-level unit (parallel) -> merge denominators -> deterministic sweep over 100% ->
per-unit group A -> risk-ranked subset for groups B/C -> 31 -> 32 -> 33/34/35 -> 37 if multi-repo -> 36.
**Budget split:** 40% deterministic · 35% reading · 25% verification.
**Non-negotiables at this size:**
- Never attempt one global reasoning pass. Shard by deployable unit, sorted deterministically, seed recorded.
- Reduce with structured findings only. Prose summaries of shards are capped at C2 and must be re-read at
  source before promotion to the executive layer.
- Publish per-unit coverage, not just repository-wide coverage — an 80% file-coverage monorepo can have 10%
  coverage of the authentication surface, and only the per-unit table exposes that.
- Cache census and tool outputs keyed by commit SHA so re-runs cost minutes, not hours.

## P4 · M&A technical due diligence
**Skills (36):** all of P2 + 12, 14, **15**, 16, 17, 23, 24, 30, **31**, **35**, and 37 when scope is multi-repo. RDA-27 stays opt-in.
**Emphasis:** licence/IP (RDA-15) and fidelity (RDA-31) are **mandatory**, not optional — the two findings most
likely to change a price are a copyleft contamination path and a documented capability the code does not have.
**Budget split:** 30% deterministic · 40% reading · 30% verification. Verification is highest here because the
output is adversarial: the other side's engineers will read it.
**Reporting:** RDA-36 with verdict GO / GO_WITH_CONDITIONS / NO_GO / INSUFFICIENT_BASIS, plus the unknown
ledger as a schedule to the report and the interview agenda as an appendix.
**Codex phase split (measured, not theoretical).** P4's 36 skills carry ~9,250 characters of startup metadata
(the full 38-skill P3 pack carries ~9,800), which exceeds the ~8,000-character skill-list budget at least one
host applies — descriptions get shortened, then skills get silently omitted with a warning. So on Codex, run
P4 as two sequential sessions: `--profile P4A` (kernel, structure and risk: 19 skills, ~4,800 chars) then
`--profile P4B` (operations, health and synthesis: 21 skills, ~5,400 chars). This is safe because the
dependency between phases is on **artifacts** — census.json, the entry-point map, the findings file — which
persist in the run directory, not on the skill being loaded in the same session. Regenerate these numbers
with `validate_pack.py --budgets`; they are derived from the pack, not maintained by hand.

**Rule:** no valuation input above C4. If a number will move a price, it needs an executed artifact behind it.

## P5 · Security audit
**Skills (18):** 00, 01, 02 -> 03, 06, 08, 09 -> 10, 11, 12, 13, 14, 19, 20 -> 32 -> 33, 34, 36
**Order:** secrets and SBOM first (cheapest, highest escalation probability), then entry points, then
adjudication, then threat model over the real boundaries.
**Budget split:** 45% deterministic · 25% adjudication · 30% verification.
**Rules:** C3 floor for HIGH/CRITICAL. Present/reachable/exploitable reported as three counts. SARIF export
mandatory so findings land in the existing scanning pipeline rather than in a document.
**Escalation:** live secrets and compromise indicators halt the run immediately per ESC-1.

## P6 · Production readiness
**Skills (18):** 00, 01, 02 -> 03, 06, 07, 08, 09 -> 18, 19, 20, 21, 22, 23 -> 32 -> 33, 34, 36
**Order:** ends at RDA-23 as a gate: PASS / CONDITIONAL / FAIL with the conditions enumerated.
**Budget split:** 35% deterministic · 40% reading · 25% verification.
**Rule:** backup evidence without restore evidence is a FAIL condition, not a warning. Alerts without runbooks
are CONDITIONAL. Missing SLOs are CONDITIONAL; missing telemetry to compute them is FAIL.

## P7 · CTO onboarding / first 30 days
**Skills (16):** 00, 01, 02 -> 03, 04, 06, 07, 08, 09 -> 26, 28, 29 -> 32, 33, 34 -> 36
**Emphasis:** orientation over judgement. The deliverable is a map, the risk shortlist, the key-person
concentration picture, and — most valuably — the question list (RDA-34) to take into the first round of
one-to-ones.
**Budget split:** 25% deterministic · 55% reading · 20% verification.
**Rule:** no remediation roadmap in the first pass. A new CTO recommending fixes before understanding the
constraints is how credibility is lost; RDA-35 runs in the second pass, after the interviews.

---

## Profiles are dependency-closed

Every profile above is closed under the dependency graph: if a skill is in the profile, every skill it *hard*
depends on is too. Fan-in synthesisers (RDA-31, RDA-32, RDA-34) declare range or `all` dependencies and are
exempt by construction — they aggregate whatever findings the profile actually produced.

This is enforced, not asserted. `scripts/validate_pack.py` reads profile membership straight out of
`install.sh` and reports `E140` for any profile that omits a hard dependency; it also reports `W131` when an
*installed* skill depends on one absent from that install, which is expected for a deliberately narrowed
install and a defect for a full pack. The one legitimate exception is encoded, not waived: **P4B may draw on
P4A**, because P4A runs first and leaves its artifacts on disk. The reverse is not permitted — a forward
dependency cannot be satisfied by an artifact that does not exist yet.

That exception is the reason the check exists. P4A originally contained RDA-14 and RDA-17, both of which
require RDA-19, which was scheduled only in the later P4B phase; the closure claim was false for exactly one
profile and nothing caught it. RDA-19 is now in P4A. Two other closures are easy to get wrong and were:
**RDA-36 requires RDA-34**, because a brief without the unknown ledger is a brief that hides its own limits;
and **RDA-18 requires RDA-07**, because "what is untested" is meaningless without knowing which logic carries
the risk.

## Trigger conditions (evaluated by RDA-01 against census.json)

| Census signal | Activates |
|---|---|
| `units.build_manifests > 1` or `units.containerfiles > 1` | RDA-06, RDA-22 |
| `units.iac_files > 0` or `units.k8s_manifests > 0` | RDA-20, RDA-23 |
| `risk_surface.personal_data_files > 0` | RDA-16, RDA-17 |
| `risk_surface.route_files > 0` | RDA-05, RDA-12 |
| `risk_surface.secret_pattern_files > 0` | RDA-10 escalated to first position |
| `files.vendored > 0` or third-party source present | RDA-15 |
| more than one repository in scope | RDA-37 |
| output leaves the engineering organisation | RDA-31, RDA-32, RDA-36 become mandatory |
| `history.validity != ok` (shallow clone) | RDA-28, RDA-29 disabled — record as blind spot, do not degrade silently |
