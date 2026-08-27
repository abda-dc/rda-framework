---
name: rda-NN-short-name
description: One sentence stating WHAT this skill produces and WHEN to trigger it, written so an agent can route on it. Include concrete trigger phrases. Max 1024 chars, no newlines.
version: 1.0.0
rda_id: RDA-NN
layer: 0-kernel | 1-structure | 2-risk | 3-operations | 4-health | 5-synthesis
risk_class: LOW_HARM | MEDIUM_HARM | HIGH_HARM   # harm if this skill is WRONG, not repo risk
depends_on: [RDA-02]
parallel_group: A|B|C|NONE
token_budget: {small: 15k, medium: 60k, large: 200k, monorepo: shard}
requires_tools: [git, rg]            # hard requirements
optional_tools: [semgrep, syft]      # degrades gracefully, must record degradation
external_validation: REQUIRED | CONDITIONAL | NONE
license: Apache-2.0
---

# <Skill title>

> **Kernel contract.** This skill inherits `governance/EVIDENCE-STANDARD.md`, `CONFIDENCE-AND-COVERAGE.md`,
> `ANTI-HALLUCINATION-CONTROLS.md`, `RISK-SEVERITY-AND-ESCALATION.md`. Output that violates them is defective.
> Emit findings conforming to `schemas/finding.schema.json` and one coverage record per population.

## Purpose
## Business value
## When to use
## When NOT to use
## Inputs
## Procedure
   1. Deterministic pass (commands, 100% of corpus)
   2. Targeted read pass (risk-weighted sample, cite path#Lx-Ly)
   3. Synthesis with class labelling
   4. Disconfirming pass
## Outputs
## Evidence requirements
## Fact vs inference rules   (skill-specific ceilings on top of ES-1 §2)
## Confidence scoring rules
## Repository coverage rules (population definition + denominator command)
## Large repository strategy (shard key, reduce contract, budget guard)
## Failure conditions        (what makes this skill stop or downgrade)
## Escalation conditions
## External validation required
## Known limitations
## Success criteria / metrics
## Example prompts
   - Claude Code / Cursor / Windsurf / RooCode:
   - Codex / OpenAI Agents:
   - Antigravity:
   - Gemini CLI / Aider / Copilot:
