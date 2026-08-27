---
name: rda-12-threat-model
description: Builds a STRIDE threat model per trust boundary from real entry points and data flows, with attacker goals, mitigations and assumptions to validate; use when public routes or regulated data exist.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-12"
  layer: "2-risk"
  risk_class: "MEDIUM_HARM"
  tier: "conditional"
  depends_on: "RDA-03, RDA-06, RDA-08"
---

# RDA-12 · Threat Model

Inherits RDA-00. A threat model over an imagined architecture is fiction with a diagram: every element is cited.

## Purpose
Produce a STRIDE analysis per trust boundary of the system as built: attacker goals, existing mitigations with
citations, and the assumptions a human must validate before the model is trusted.

## Business value
Threat models fail when they describe the system someone intended. Anchoring every element to an enumerated
entry point and a traced data flow turns "we should think about security" into a bounded list of boundaries with
named gaps, and tells RDA-11 where to spend its adjudication budget.

## When to use
When the census shows internet-facing routes, multi-tenant or regulated data, or when a new integration or
partner changes who can reach what.

## When NOT to use
Before RDA-03, RDA-06 and RDA-08 exist — without them this degrades into invention. Not a substitute for RDA-11:
this skill names what could go wrong, RDA-11 adjudicates whether the code lets it.

## Inputs
`entrypoints.json` (RDA-03: protocol, exposure, authn, handler) · RDA-06 service edges · RDA-08 stores, schemas
and lifecycle · RDA-09 config and flags · RDA-16 data classes when present · business context from scope.

## Procedure

**1. Answer question one from artifacts (deterministic).** The Threat Modeling Manifesto's four questions frame
the run: *what are we working on · what can go wrong · what are we going to do about it · did we do a good
enough job.* Question one is answered only by cited artifacts: `jq -r '.entrypoints[].id'
rda-out/entrypoints.json | wc -l` and the RDA-06 edge count fix the denominators before anything is drawn. An
element with no locator does not enter the model. **Degraded fallback:** if those files are absent, stop — there
is no honest degraded mode for a threat model without an entry-point map.

**2. Deterministic boundary extraction.** Derive boundaries from artifacts, not intuition: `jq -r
'.entrypoints[] | [.protocol,.exposure,.auth,.path] | @tsv' rda-out/entrypoints.json | sort -u` for reachable
surface; `rg -n 'kind:\s*(Ingress|Gateway|NetworkPolicy)' -g '*.y*ml'` and `rg -n
'hostNetwork|privileged|securityContext' -g '*.y*ml'` for network and process boundaries; `rg -n
'aws_security_group|google_compute_firewall' -g '*.tf'` for cloud edges. A boundary exists where a message
crosses a change in control: authentication, tenant, process, network zone, or vendor.

**3. Build the DFD from cited edges only.** Elements are external entities, processes, data stores and flows,
each carrying `path#Lstart-Lend` and the commit SHA. Edges come from RDA-06; edges the model would *like* to
exist are omitted, not assumed. Optional `pytm` rendering (`python tm.py --dfd | dot -Tpng -o out/dfd.png`) is
generated from the cited element list.

**4. STRIDE per boundary and per element.** For each boundary walk all six: Spoofing · Tampering · Repudiation ·
Information disclosure · Denial of service · Elevation of privilege. Per threat record the attacker goal in
business terms (steal payment tokens, read another tenant's records, suppress an audit trail), the entry point
it starts from, the precondition it requires, and the asset it targets. Threats with no reachable entry point
are marked unreachable, not deleted.

**5. Existing mitigations, cited or absent.** Each threat carries `mitigation: path#Lstart-Lend` naming the
control and where it sits on the path, or `NONE_FOUND` plus the searches that were run. `NONE_FOUND` is a
statement about the search, not proof of absence, and it is what RDA-11 turns into a candidate.

**6. Assumptions to validate.** Every model rests on assumptions the repository cannot settle: that the gateway
terminates TLS, that the internal network is unreachable from outside, that staging credentials differ from
production. Each becomes a question with an owner role and a system of record.

**7. Disconfirming pass.** For each boundary, run the query that would collapse it: a route bypassing the
gateway, a service account shared across zones, a debug flag disabling authn, a direct database grant. Record
the query and the result on the element.

**8. Answer question four.** State coverage: boundaries modelled over boundaries enumerated, and threats with a
mitigation verdict over threats raised. "Did we do a good enough job" is a coverage number here, not a feeling.

## Outputs
`threat-model.md` (boundaries, DFD elements with locators, STRIDE table, attacker goals) · `threats.csv` (id,
boundary, STRIDE class, entry point, precondition, mitigation locator or NONE_FOUND) · `assumptions.csv` ·
optional `dfd.png`.

## Evidence requirements
Every element, edge and mitigation cites `path#Lstart-Lend` plus commit SHA. Threats cite the RDA-03 entry-point
id they start from. Mitigation claims cite the control's code, not a document describing it.

## Fact vs inference rules
`FACT`: this route exists with this exposure; this control is present at this locator. `INFERENCE`: a trust
boundary exists here — requires two cited artifacts showing the control change. `HYPOTHESIS`: every attack path,
always, and every claim that a mitigation is sufficient. `UNKNOWN`: enforcement living in infrastructure outside
the repository.

## Confidence scoring rules
Boundary and element existence reach C2 with two independent citations; mitigation-present claims reach C3 only
when a tool or test confirms the control fires. Attack-path plausibility caps at C2, and any threat promoted to
HIGH/CRITICAL must become an RDA-11 candidate and meet the C3 floor there.

## Repository coverage rules
Population is trust boundaries derived from the enumerated entry-point and service-edge sets. Denominator: `jq
'.entrypoints | length' rda-out/entrypoints.json` plus the RDA-06 edge count; report modelled boundaries over
derived boundaries, and separately the externally-exposed subset, which is the number that matters.

## Large repository strategy
Model per deployable unit, then the inter-unit boundaries as a second pass — never one global diagram for forty
services. Shard order is the RDA-03 exposure ranking, so internet-facing units are modelled before the budget
runs out; units not reached are listed with their exposure attribute.

## Failure conditions
RDA-03, RDA-06 or RDA-08 missing or stale · exposure attributes absent from the entry-point table (everything
becomes "possibly external") · architecture spread across repositories not in scope · a boundary whose
enforcement is entirely in a cloud console.

## Escalation conditions
A boundary documented as enforced but with no enforcement in cited code, on a path carrying money or regulated
data · a direct external path into a store the architecture calls internal · any sign of existing compromise,
which halts the run per ESC-1.

## External validation required
Whether network segmentation matches the IaC · whether the gateway enforces the assumed controls · which
environments are internet-reachable · whether integrations hold broader credentials than the code implies.

## Known limitations
Two ways this skill produces a wrong answer. **(a) The imagined architecture** — a plausible diagram assembled
from folder names and README prose, complete with services that do not exist; prevented by the citation rule for
every element and by step 2 deriving boundaries only from enumerated artifacts. **(b) The mitigation mirage** —
a control named in a design doc counted as implemented; prevented by requiring the control's own code as the
mitigation citation, with `NONE_FOUND` as the only alternative.

## Success criteria
Every element carries a locator · every threat names an attacker goal and an entry point · every mitigation is
code-cited or `NONE_FOUND` · the assumption list is non-empty · boundary coverage is stated against the RDA-03
denominator · every `NONE_FOUND` on an exposed path is handed to RDA-11 as a candidate.

## Example prompts
- Claude Code / Cursor: "Run rda-12-threat-model using entrypoints.json and the RDA-08 data flows; STRIDE per boundary with cited mitigations."
- Codex: "$rda-12-threat-model — derive trust boundaries from the route table, then produce threats.csv and the assumptions list."
- Antigravity / Gemini CLI: "/rda-threat-model scope=services/payments dfd=true output=threat-model.md"
