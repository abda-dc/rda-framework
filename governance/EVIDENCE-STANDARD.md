# RDA Evidence Standard (ES-1)

Normative for every skill in the pack. A skill that violates ES-1 is defective regardless of how useful its
output reads. "Sounds right" is not a category in this framework.

## 1. The five claim classes

Every sentence in every RDA output belongs to exactly one class and is labelled with it.

| Class | Definition | Minimum bar | Example |
|---|---|---|---|
| `FACT` | Verbatim content of a cited artifact, or verbatim output of a deterministic command | Path + line range + commit SHA + quote, **or** command + version + exit code + output digest | "`services/pay/app.py#L44-L51` registers `POST /refund` with no decorator from `auth.py`." |
| `INFERENCE` | Conclusion derived from >=2 independent facts, with the derivation written out | Cites every fact used; derivation must be checkable by a reader who has only those facts | "Refund endpoint is unauthenticated **in source**: (a) route has no auth decorator, (b) `auth.py` middleware allowlist excludes `/refund`." |
| `HYPOTHESIS` | Plausible reading that the evidence permits but does not establish | Must state the exact artifact or command that would settle it | "The gateway may enforce auth upstream — settle by reading the ingress config, not present in scope." |
| `UNKNOWN` | Information required for the judgement is absent from scope | Must name the system of record and what conclusion is blocked | "No load data in repo; throughput headroom is undetermined." |
| `EXTERNAL_VALIDATION_REQUIRED` | Undecidable from source artifacts by construction | Must carry the question and the role to ask | "Whether the staging IAM role is used in production." |

Prose that mixes classes in one sentence is rejected by the linter. Downgrade, split, or delete.

## 2. Undecidable-from-source register (hard-coded)

These claims are **never** `FACT` or `INFERENCE` from repository contents alone. Any skill emitting them at a
higher class than shown is in violation. This register exists because these are precisely the claims that read
most authoritatively and are most often fabricated.

| Claim | Max class from source alone | What would raise it |
|---|---|---|
| "This code is deployed / runs in production" | `HYPOTHESIS` | Deploy logs, release manifest, image digest in cluster |
| "This service handles N requests/users" | `EXTERNAL_VALIDATION_REQUIRED` | APM/telemetry export |
| "This costs $X / will save $Y" | `EXTERNAL_VALIDATION_REQUIRED` | Billing export, FOCUS-format cost data |
| "This vulnerability is exploitable" | `HYPOTHESIS` | Reachability analysis output, PoC, or exploit run |
| "This code is dead / unused" | `HYPOTHESIS` | Runtime coverage, call-graph closure incl. dynamic entry, retention window |
| "The system is SOC 2 / ISO / PCI compliant" | Never emitted | Auditor opinion. RDA emits *control evidence present/absent* only |
| "Person P owns component C" | `INFERENCE` about **role**, never about a named individual | CODEOWNERS + org confirmation |
| "It will scale to N" | `EXTERNAL_VALIDATION_REQUIRED` | Load test artifacts |
| "MTTR / incident frequency is X" | `EXTERNAL_VALIDATION_REQUIRED` | Incident system export |
| "This dependency is unused" | `HYPOTHESIS` | Build graph + dynamic import scan + lockfile resolution |
| "Data is stored in region R" | `HYPOTHESIS` | Cloud config from the live account, not IaC intent |
| "The blast radius is limited to X" | `INFERENCE` only with a cited dependency graph; otherwise `HYPOTHESIS` | Dependency closure + network policy from runtime |

## 3. Citation integrity

1. Every `SOURCE`/`CONFIG`/`VCS_HISTORY`/`DOC` evidence item carries `path#Lstart-Lend`, the commit SHA, and a
   verbatim `quote`. These are exactly the kinds `verify_citations.py` re-reads from the tree; `TOOL_OUTPUT`
   carries tool name, version and exit code instead, and run artifacts are not re-resolvable at a commit.
2. `verify_citations.py` re-reads each locator at the pinned commit and compares a normalised hash of the quote.
3. A citation that does not resolve **quarantines** its finding automatically: the finding is removed from all
   executive output and listed in the integrity appendix. Quarantine is not a warning — it is a removal.
4. Line-number drift is not an excuse: the quote hash, not the line number, is authoritative. If the quote is
   absent from the file at that commit, the finding was invented.
5. Paraphrase in a `quote` field is a defect equal to a wrong path.

## 4. Independence

Two evidence items are independent only if they could disagree. Not independent: two lines of one file; a tool
report and the same tool's cached artifact; a README statement and a doc generated from that README; the same
finding restated by a second model on the same context. Independence is asserted via `independence_group` and
is what separates C1 from C2.

## 5. Falsifiability

Every finding carries `how_to_refute` (the command, file, or question that would disprove it) and
`disconfirming_check` (the search actually performed for contradicting evidence, and its result). A finding
whose author performed no disconfirming search is capped at C1. This is the single cheapest defence against
confirmation-shaped reasoning, because it forces one query in the opposite direction before the claim is written.

## 6. Silence rules

- Absence of evidence is reported as `UNKNOWN` with a coverage record, never as "no issues found".
- "No issues found" is only emissible with `selection: EXHAUSTIVE` over a stated population.
- A skill that inspected 4% of a population must say 4%, in the executive summary, not only in an appendix.
- **A report with zero UNKNOWNs is automatically suspect** and is flagged by the linter: on real enterprise
  repositories, undecidable questions always exist, so their absence indicates the model resolved uncertainty
  by assertion.

## 7. Quotation discipline for third-party content

Vendored, licensed and generated code is evidence, but reproducing it at length is both a context cost and a
licensing question. Quote the minimum span that carries the claim (<=600 chars), never whole files, and record
the license of any third-party file quoted.
