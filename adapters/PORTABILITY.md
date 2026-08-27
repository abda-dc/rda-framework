# RDA Portability Layer — one canonical pack, ten environments

## 1. The convergence that makes this cheap

Two open standards now carry almost all of the weight, so RDA is authored **once** and adapted, not rewritten:

- **Agent Skills** (`SKILL.md` + YAML frontmatter in a named directory, spec at agentskills.io) — originally
  Anthropic's, released as an open standard and adopted across Codex/ChatGPT, Cursor, Gemini CLI, GitHub
  Copilot & VS Code, Devin Desktop (Windsurf), Roo Code, Claude Code and dozens more.
- **AGENTS.md** — plain-markdown, always-on project instructions, now stewarded by the Agentic AI Foundation
  under the Linux Foundation, read by Codex, Cursor, Copilot/VS Code, Devin Desktop, Roo Code, and (via
  `context.fileName`) Gemini CLI and Aider.

**The single most actionable fact:** `.agents/skills/` (project) and `~/.agents/skills/` (user) are a shared,
tool-neutral discovery path honoured by Codex, Cursor, Gemini CLI, GitHub Copilot/VS Code and Devin Desktop.
Claude Code is the one exception — it reads only `.claude/skills/` — **but it follows symlinks**. So: one
canonical tree plus one symlink covers every skills-capable environment.

## 2. Two environments in your target list have changed status

| Target as briefed | Current reality | RDA mapping |
|---|---|---|
| **GitHub Copilot Workspace** | **Retired** — GitHub Next states the technical preview was sunset on 30 May 2025 | Target **Copilot cloud agent + Copilot code review + VS Code agent mode** instead, via `.github/skills/` and `.github/copilot-instructions.md`. Note skills are read from the **head branch** during PR review |
| **Windsurf** | Documented under **Devin Desktop** (Cognition); `.devin/` is now preferred with `.windsurf/` retained as fallback; Cascade memories are legacy and the default Devin Local agent does not persist them | Ship both `.devin/rules/` and `.windsurf/rules/`; skills via `.agents/skills/` which Devin Desktop discovers natively |

Neither invalidates the design — both are covered by the same canonical pack — but a framework that shipped a
`copilot-workspace/` adapter would be shipping a dead artifact.

## 3. Install matrix

| Environment | Skills path | Always-on rule mechanism | Hard limits that shaped RDA |
|---|---|---|---|
| **Claude Code** | `.claude/skills/<name>/SKILL.md` (symlink to canonical) | `.claude/rules/*.md` with `paths:`, or `CLAUDE.md` | CLAUDE.md target <200 lines; SKILL.md <500 lines / <5k tokens; skill metadata ~100 tokens each, always loaded |
| **Codex** | `.agents/skills/` (primary), `/etc/codex/skills` admin | `AGENTS.md` chain, root-down | **Skill list capped at 2% of context or 8,000 chars** — descriptions must be terse or the list is truncated with a warning. `AGENTS.md` chain stops at `project_doc_max_bytes` (32 KiB default) |
| **Cursor** | `.agents/skills/`, `.cursor/skills/` (+ `.claude/`, `.codex/` compat) | `.cursor/rules/*.mdc` with `alwaysApply`/`globs`/`description` | `.md` in `.cursor/rules` is **ignored** — must be `.mdc`; keep rules <500 lines |
| **Gemini CLI** | `.gemini/skills/` or `.agents/skills/` (alias takes precedence) | `GEMINI.md` via `context.fileName` | Skill activation is **consent-gated** (`activate_skill` prompt) — plan for an interactive approval per skill |
| **Antigravity** | (skills support unverified) | `.agents/rules/` workspace, `~/.gemini/GEMINI.md` global; workflows as `/slash` | **12,000 characters per rule and per workflow file** |
| **Devin Desktop / Windsurf** | `.agents/skills/`, `.windsurf/skills/` | `.devin/rules/` or `.windsurf/rules/` with `trigger: always_on\|glob\|model_decision\|manual` | Workspace rule **12,000 chars**; global rules file **6,000 chars**; workflows 12,000 chars and **manual-only** |
| **Roo Code** | (skills path unverified; listed as a client) | `.roomodes` custom modes + `.roo/rules-{slug}/` | Rule files have **no frontmatter** and no glob scoping — scoping is done via modes and `fileRegex` |
| **Aider** | none — no skill system | `CONVENTIONS.md` loaded with `read:` in `.aider.conf.yml` | Must be explicitly loaded; no auto-discovery, no sub-agents. Use `map-tokens` for the repo map |
| **GitHub Copilot** | `.github/skills/`, `.claude/skills/`, `.agents/skills/` | `.github/copilot-instructions.md`; `.github/instructions/*.instructions.md` with `applyTo` | `name` max 64 chars and invalid characters cause **silent** load failure; namespace prefixes (`org/skill`) also fail silently |
| **OpenAI Agents SDK** | n/a — programmatic | Skills become agent instructions; each RDA skill maps to one `Agent` with `handoffs` following the DAG | Guardrails and tracing are the natural home for the RDA verification gates |

## 4. Design consequences RDA actually obeys

1. **Descriptions are capped at 200 characters** — and even so, the measured budget for the full pack is
   **9,777 characters**, over the ~8,000-char skill-list cap. This is not hypothetical: verbose descriptions
   are shortened first, then skills are silently omitted with a warning, and a silently omitted audit skill is
   a coverage gap nobody sees. `validate_pack.py` prints the budget on every run for exactly this reason.
2. **Profile installs, not full installs.** Measured budgets: P1 4,294 · P2 6,339 · P5 4,558 · P6 4,547 ·
   P7 4,029 — all comfortably inside the cap. **P4 (M&A, 36 skills) measures 9,254 and does not fit** (the full
   38-skill P3 pack measures 9,777), so P4 ships as a two-phase split: `--profile P4A` (19 skills, 4,801 chars)
   then `--profile P4B` (21 skills, 5,403). The split is safe because the inter-phase dependency is on artifacts
   on disk — census.json, the entry-point map, the findings file — not on skills being co-loaded in one session.
   Every number here is produced by `scripts/validate_pack.py --budgets`; re-run it rather than trusting this list.
3. **The kernel fits in 6,000 characters.** `audit-core` has a condensed rule form, emitted per environment by
   `scripts/generate_adapters.py` (`.cursor/rules/rda-core.mdc`, `.devin/rules/rda-core.md`,
   `.windsurf/rules/rda-core.md`, `.agents/rules/rda-core.md`, `.github/copilot-instructions.md`,
   `CONVENTIONS.md`), sized for the Devin/Windsurf global-rules cap, with the full text remaining in the skill
   body. The generator fails if that condensed form exceeds the cap.
4. **Frontmatter is restricted to the spec-portable set** (`name`, `description`, optional `license`,
   `compatibility`, `metadata`). Tool-specific keys (`paths`, `disable-model-invocation`, `allowed-tools`,
   `icon`, `color`, `argument-hint`) live only in generated per-tool adapters, because they are silently
   ignored or reinterpreted elsewhere.
5. **Rule-style files are generated, never hand-maintained.** `.mdc`, `.instructions.md`, `trigger:` rules and
   `.roomodes` are outputs of `scripts/generate_adapters.py` from the same source of truth.
