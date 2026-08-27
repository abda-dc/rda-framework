---
name: rda-15-license-ip-review
description: Inventories licences per component and per vendored file, maps copyleft contamination paths and obligation gaps, and records IP provenance; use before distribution, open-sourcing or an acquisition.
version: 1.0.0
license: Apache-2.0
metadata:
  rda_id: "RDA-15"
  layer: "2-risk"
  risk_class: "HIGH_HARM"
  tier: "conditional"
  depends_on: "RDA-13"
---

# RDA-15 · Licence & IP Review

Inherits RDA-00. RDA produces licence *evidence* for counsel; it never gives legal advice or a verdict.

## Purpose
Inventory the licence of every declared component **and every file in the tree**, map the paths by which
copyleft terms could reach the product, evidence obligations, and record IP provenance.

## Business value
Licence defects change deal terms rather than sprint plans: they can encumber the product itself. Manifest-only
scanning misses the cases that matter, because vendored trees, forked files, copied snippets, generated code and
assets carry licences no manifest declares and no package manager resolves.

## When to use
Before distribution, open-sourcing or an acquisition; whenever the census reports vendored source.

## When NOT to use
For vulnerability data (RDA-13) or publishing integrity (RDA-14). Never as a substitute for legal review, and
never to answer "are we allowed to ship this" — that question leaves the framework.

## Inputs
`census.json` classes incl. `vendored` · RDA-13 SBOM licences · `LICENSE`/`NOTICE` files · distribution mode.

## Procedure

**1. Component-level inventory (deterministic).** From the SBOM: `syft scan dir:. -o
spdx-json=out/sbom.spdx.json` and `trivy fs --scanners license --license-full --format json -o
out/trivy-lic.json .`. Record declared licence per component and version, and flag components whose licence
field is empty — an empty field is UNKNOWN, not permissive.

**2. File-level inventory (the part manifests cannot do).** Run over 100% of tracked files **including**
`vendored` and `generated`, which RDA-02 excludes from quality denominators and this skill includes: `scancode
-clpieu --processes 4 --json-pp out/scancode.json .`; `askalono crawl --format json .` as a faster alternative;
`licensee detect --json .` for the repository's own licence. **Degraded fallback:** `rg -n --pcre2 -i
'(SPDX-License-Identifier|Copyright \(c\)|GNU (General|Lesser) Public|Mozilla Public License|Apache License)'` —
a header grep finds declarations, not licences: PARTIAL coverage, C2 cap.

**3. Reconcile the two inventories.** Files with a licence header that no component covers are the diligence
surface: vendored trees, forked files, snippets pasted from forums, generated code carrying the generator's
terms, and assets (fonts, icons, sample data). Report the count against the tracked-file denominator — this is
the answer to "is manifest scanning enough here".

**4. Classify by obligation family.** Group by what the licence requires, from the licence text at its locator:
permissive with attribution · weak copyleft · strong copyleft · network copyleft · source-available non-OSI ·
proprietary or unlicensed. An unlicensed third-party file is the most restrictive case, not the least: no grant
is no permission.

**5. Trace contamination paths, not licence names.** For each copyleft-family component record the *use
relationship* from cited build files: static link, dynamic link, subprocess, network call, vendored source,
build-time only. Then the distribution mode from cited artifacts: published package, image, installed binary, or
SaaS. Quote the operative clause at its locator — network-use and relinking terms are read from the text, never
from memory — and stop. Whether an obligation triggers is counsel's call.

**6. Evidence obligation compliance.** Per obligation-bearing component: attribution file present and complete
(`NOTICE`, `THIRD_PARTY_LICENSES`), licence text shipped, modification notices, written offer for source where
required, patent and trademark terms noted. Emit `EVIDENCE_PRESENT` · `EVIDENCE_PARTIAL` · `EVIDENCE_ABSENT`
with citations. Never emit "violation" or "compliant".

**7. IP provenance.** Bulk-add commits are vendoring events, not development: `git log --diff-filter=A
--format='%H %aI %s' --numstat` ranked by lines added. Record DCO or CLA evidence (`git log --format='%b' | rg
-c 'Signed-off-by'`, bot config in `.github/`) and AI-assistance signals such as `Co-authored-by` trailers.
Those signals are a **policy question** for engineering leadership, never an ownership conclusion.

**8. Existence-check and disconfirm.** Every SPDX identifier resolves against the published SPDX licence list
before printing; one that does not is a scanner artefact or a fabrication. Then query the opposite direction: a
dual-licence grant, a commercial licence in the contract folder, an exception clause, or a `NOTICE` entry that
already discharges the obligation.

## Outputs
`license-inventory.csv` (component or file, locator, licence id, obligation family, evidence state) ·
`contamination-paths.csv` (component, use relationship, distribution mode, operative clause locator) ·
`obligations.md` · `provenance.md` (vendoring events, DCO/CLA evidence, AI-assistance signals) · the counsel
question list.

## Evidence requirements
Every licence assertion cites the file carrying it — `path#Lstart-Lend` plus commit SHA — or the SBOM entry plus
scanner name, version and exit code. Licence quotes stay under 600 characters, per ES-1 §7.

## Fact vs inference rules
`FACT`: this file declares this SPDX identifier at this locator; this component's SBOM licence field says X.
`INFERENCE`: this component is linked into the distributed artifact — only with the build file cited.
`HYPOTHESIS`: a copied snippet's origin, when only similarity supports it. **Never emitted:** that an obligation
is or is not met as a matter of law, that a licence is violated, or that the product's ownership is impaired.

## Confidence scoring rules
HIGH/CRITICAL licence findings require **C3**: a named scanner with version and exit code plus the file
citation. Scanner-inferred licences without a file declaration are C1 and ship as verification tasks. A
contamination path reaches C2 only when both the linkage evidence and the distribution evidence are cited.

## Repository coverage rules
Two populations, both reported. Files: `git ls-files | wc -l`, with vendored and generated **included** — the
exclusions used elsewhere in RDA do not apply here. Components: `jq '[.packages[].name] | length'
out/sbom.spdx.json`. A component-only coverage number is not a licence review and must not be published as one.

## Large repository strategy
`scancode` is the slow step: shard by top-level directory, cache results keyed by file hash, and re-run only on
changed hashes. Run the fast header grep over 100% first to locate licence-bearing files, then scan those
directories exhaustively; unscanned directories are named blind spots with their file counts.

## Failure conditions
No licence scanner available (header grep only, PARTIAL) · binary files with no readable header · submodules not
initialised · unreachable registry metadata · dual-licensed components with no selection recorded.

## Escalation conditions
Strong or network copyleft on a linked path in a proprietary distribution goes to **legal before any remediation
recommendation**, per ESC-1 · an unlicensed third-party file in the shipped tree.

## External validation required
Whether a commercial or dual licence was purchased · the distribution mode and customer contracts · whether
contributors signed a CLA · counsel's reading of every clause quoted.

## Known limitations
Two ways this skill produces a wrong answer. **(a) The manifest verdict** — declaring the repository "MIT-only"
from `package.json` while `vendor/` carries GPL; prevented by the file-level scan over 100% of tracked files, by
including vendored and generated paths in the denominator, and by the step 3 reconciliation count. **(b) The
confident legal conclusion** — stating that a licence forces the product open; prevented by the never-emitted
class, which limits output to a quoted clause, a cited path and an escalation. Scanners also mis-identify
modified headers, and code copied without its header needs similarity tooling this skill does not run.

## Success criteria
File-level coverage published beside component coverage · every contamination path carries linkage and
distribution citations · every SPDX id existence-checked · zero legal conclusions in the output.

## Example prompts
- Claude Code / Cursor: "Run rda-15-license-ip-review: scancode over the whole tree including vendor/, then reconcile against the SBOM licences."
- Codex: "$rda-15-license-ip-review — inventory licences per file and per component, and list copyleft paths reaching the distributed artifact."
- Antigravity / Gemini CLI: "/rda-license scope=. include_vendored=true distribution=saas output=license-inventory.csv"
