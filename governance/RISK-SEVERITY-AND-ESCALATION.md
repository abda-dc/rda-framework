# RDA Risk, Severity & Escalation Standard (RS-1 / ESC-1)

## 1. Severity is impact x likelihood, both defined

**Impact** (worst credible outcome if the finding is real, judged against the business context supplied at
scope time — a 4-hour outage is MINOR for an internal tool and SEVERE for payments):

| Level | Definition |
|---|---|
| SEVERE | Existential: unrecoverable data loss, regulated-data breach, safety, insolvency-scale outage, deal-breaking IP defect |
| MAJOR | Material: multi-hour outage of a revenue path, breach of a contractual SLA, remediation costing a quarter of a team's capacity |
| MODERATE | Contained: degraded service, manual workaround exists, remediation within a sprint |
| MINOR | Localised: developer friction, cosmetic risk, elevated toil |
| NEGLIGIBLE | Noted for completeness |

**Likelihood** must cite its basis (an exposed path, a precedent in VCS history, a missing control on a live
route). Likelihood asserted without a basis is capped at POSSIBLE.

| Level | Basis required |
|---|---|
| ALMOST_CERTAIN | Already occurring, or trivially reachable by an unauthenticated party |
| LIKELY | Reachable by an authenticated party, or has occurred in history |
| POSSIBLE | Requires a specific precondition present in the code |
| UNLIKELY | Requires multiple preconditions or privileged access |
| RARE | Requires implausible combination |

Matrix (impact x likelihood -> severity), applied mechanically so two runs agree:

|  | RARE | UNLIKELY | POSSIBLE | LIKELY | ALMOST_CERTAIN |
|---|---|---|---|---|---|
| **SEVERE** | MEDIUM | HIGH | HIGH | CRITICAL | CRITICAL |
| **MAJOR** | LOW | MEDIUM | HIGH | HIGH | CRITICAL |
| **MODERATE** | LOW | LOW | MEDIUM | MEDIUM | HIGH |
| **MINOR** | INFO | LOW | LOW | LOW | MEDIUM |
| **NEGLIGIBLE** | INFO | INFO | INFO | LOW | LOW |

## 2. Security findings use a decision model, not a score

CVSS base scores rank *badness in the abstract*; they do not rank *what to do*. RDA-13/RDA-11 therefore emit an
SSVC-style decision (`TRACK` / `TRACK*` / `ATTEND` / `ACT`) built from: exploitation status (known-exploited
catalogue), exposure (internet-reachable vs internal), technical impact, and mission impact. CVSS/EPSS values
are carried as attributes, never as the ranking key. A finding without an exposure determination is `TRACK`.

Three counts are always reported separately and never collapsed:
`present` (in the dependency graph) / `reachable` (call path exists) / `exploitable` (preconditions met).
A report that gives only `present` has not done vulnerability management; it has done inventory.

## 3. Aggregation rules

- Risk register rows are findings, not themes. Themes are a presentation layer over cited rows.
- Never average confidence across findings. Report the distribution.
- Never sum severities into a single repository "score" without publishing the weighting and the coverage
  bands feeding it. A single number over partial coverage is the most misread artifact in due diligence.
- The register's ordering key is `(severity, ssvc, confidence)`; ties break to the finding with the larger
  blast radius, then to the cheaper remediation (so equal-risk work is sequenced by leverage).

## 4. Escalation (ESC-1) — when the agent must stop and involve a human

| Trigger | Action |
|---|---|
| Live secret material with a valid-looking format found in tracked files or history | **Halt the skill.** Do not print the value, do not copy it into findings. Emit the locator, the type, and an immediate-rotation instruction to the named role. Escalate before continuing |
| Evidence of an active or historical compromise (webshell, unexplained backdoor, exfiltration code, malicious dependency) | Halt the run. Preserve the manifest. Escalate to security incident response; RDA is not an IR tool |
| Regulated data (PII/PHI/PCI/CJIS) found in fixtures, logs, test data, or committed dumps | Halt that skill's traversal of the affected path, report location and class only, escalate to privacy/DPO role |
| Licence contamination that could affect ownership of the product (strong copyleft linked into proprietary distribution) | Escalate to legal before any remediation recommendation; RDA does not give legal advice |
| Re-verification disagreement rate >10% | Invalidate the run. Rescope with smaller shards and rerun |
| Citation resolution rate <100% after one repair pass | Publish with the integrity appendix and a stated caveat, or rerun; never publish silently |
| Coverage of the risk surface <20% while an executive decision is pending | Report as "insufficient basis for decision" rather than issuing a judgement |
| Scope contains material the audit is not authorised to read (customer data, employee records) | Stop, record ACCESS_DENIED blind spot, do not attempt to bypass |

Escalation output is a short, factual notice: what was found, where, what class of harm, what to do in the next
hour, and what RDA deliberately did **not** do.
