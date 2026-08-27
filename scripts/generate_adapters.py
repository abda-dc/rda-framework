#!/usr/bin/env python3
"""Generate per-environment adapters from the canonical SKILL.md pack.

Rule-style files (Cursor .mdc, Copilot .instructions.md, Devin/Windsurf & Antigravity trigger rules,
Roo modes, Aider conventions, Gemini TOML commands) are NOT portable and must be generated, never
hand-maintained. This script is the single source of truth for that translation.

Usage: python3 generate_adapters.py [--skills skills] [--out adapters/generated] [--profile P4] [--check]
"""
import argparse, os, re, sys

PROFILES = {
    "P1": "00 01 02 03 07 08 09 10 11 13 18 26 28 32 33 34 36",
    "P2": "00 01 02 03 04 05 06 07 08 09 10 11 13 18 19 20 21 22 26 28 29 32 33 34 36",
    "P3": "ALL",
    "P4": "00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 26 28 29 30 31 32 33 34 35 36 37",
    "P4A": "00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 19",
    "P4B": "00 01 02 18 19 20 21 22 23 24 26 28 29 30 31 32 33 34 35 36 37",
    "P5": "00 01 02 03 06 08 09 10 11 12 13 14 19 20 32 33 34 36",
    "P6": "00 01 02 03 06 07 08 09 18 19 20 21 22 23 32 33 34 36",
    "P7": "00 01 02 03 04 06 07 08 09 26 28 29 32 33 34 36",
}
# Devin Desktop global rules cap; Antigravity/Windsurf per-file rule cap.
GLOBAL_RULE_CAP, FILE_RULE_CAP = 6000, 12000

# When --check is active, w() buffers instead of writing so the committed tree can be compared
# without being modified. Adapters are generated, never hand-maintained -- this is what proves it.
PENDING = None

def load(skills_dir):
    out = []
    for d in sorted(os.listdir(skills_dir)):
        p = os.path.join(skills_dir, d, "SKILL.md")
        if not os.path.exists(p): continue
        t = open(p, encoding="utf-8").read()
        name = re.search(r"^name:\s*(.+)$", t, re.M)
        desc = re.search(r"^description:\s*(.+)$", t, re.M)
        rid = re.search(r"rda_id:\s*\"?(RDA-\d\d)", t)
        tier = re.search(r"tier:\s*\"?(\w+)", t)
        out.append({"dir": d, "name": name.group(1).strip() if name else d,
                    "desc": desc.group(1).strip() if desc else "",
                    "id": rid.group(1) if rid else "", "tier": tier.group(1) if tier else "",
                    "body": t.split("\n---", 1)[-1]})
    return out

def kernel_rule():
    """Condensed always-on rule, sized for the tightest global-rules cap in the ecosystem."""
    txt = ("# Repository audit contract (RDA-00)\n\n"
    "When auditing, reviewing or performing due diligence on a codebase, these rules bind every claim.\n\n"
    "1. LABEL EVERY CLAIM as FACT (verbatim from a cited artifact: path#Lstart-Lend + commit SHA + quote, or a\n"
    "   named command with version and exit code), INFERENCE (from >=2 independent facts, derivation written out),\n"
    "   HYPOTHESIS (evidence permits, does not establish - state the check that settles it), UNKNOWN (absent from\n"
    "   scope - name the system of record), or EXTERNAL_VALIDATION_REQUIRED (undecidable from source - carry the\n"
    "   question and the role to ask).\n"
    "2. NEVER ASSERT FROM SOURCE ALONE: what is deployed, real traffic or scale, real cost, that a weakness is\n"
    "   exploitable, that code is dead, that a named person owns something, that the org is compliant, that it\n"
    "   will scale to N, incident history or MTTR, or that data resides in a region. These are capped at\n"
    "   HYPOTHESIS or EXTERNAL_VALIDATION_REQUIRED. Compliance verdicts are never emitted at all - report control\n"
    "   evidence present or absent.\n"
    "3. SHOW THE DENOMINATOR. State the population and the fraction inspected. Absence of evidence is UNKNOWN\n"
    "   with a coverage record, never 'no issues found'. 'No issues found' requires exhaustive coverage.\n"
    "4. SEARCH FOR THE OPPOSITE before writing any finding, and record that search and its result.\n"
    "5. CONFIDENCE IS AWARDED, NOT CHOSEN. C1 single citation; C2 two independent citations plus a disconfirming\n"
    "   search; C3 adds deterministic tool corroboration (name, version, exit code); C4 adds a reproduced\n"
    "   execution artifact. HIGH/CRITICAL security findings require C3. Numeric self-confidence is banned.\n"
    "   Report severity and confidence as an orthogonal pair; never multiply them.\n"
    "6. RETRIEVE, DO NOT INGEST. Deterministic tools run over 100% of the corpus; read only risk-weighted strata;\n"
    "   grep/AST first, ranges second, whole files last. A plausible file path is not evidence you read the file -\n"
    "   confirm every path with an actual filesystem call.\n"
    "7. ADJUDICATE, DO NOT INVENT. Where a tool exists, it produces candidates and you adjudicate them with\n"
    "   structured evidence. Existence-check every named package, CVE, CWE and config key.\n"
    "8. HALT AND ESCALATE on: live secret material, evidence of compromise, regulated personal data in fixtures or\n"
    "   logs, licence contamination threatening product ownership. Report location and class, never the value.\n"
    "9. A REPORT WITH ZERO UNKNOWNS IS SUSPECT. Real repositories always contain undecidable questions.\n")
    return txt

def w(path, text):
    """Always write LF. Platform newline translation would otherwise make the generator
    non-idempotent on Windows and produce a spurious whole-tree diff against the committed pack."""
    if PENDING is not None:
        PENDING[path] = text
        return len(text)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return len(text)

def main():
    global PENDING
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills", default="skills"); ap.add_argument("--out", default="adapters/generated")
    ap.add_argument("--profile", default="P3")
    ap.add_argument("--check", action="store_true",
                    help="do not write; fail if the committed adapters differ from what would be generated")
    a = ap.parse_args()
    if a.check: PENDING = {}
    skills = load(a.skills)
    sel = PROFILES.get(a.profile, "ALL")
    if sel != "ALL":
        keep = {f"RDA-{n}" for n in sel.split()}
        skills = [s for s in skills if s["id"] in keep]
    rule = kernel_rule()
    report = []

    # --- Cursor: .mdc rules (a plain .md in .cursor/rules is ignored) --------------------------
    report.append(("cursor/.cursor/rules/rda-core.mdc", w(f"{a.out}/cursor/.cursor/rules/rda-core.mdc",
        "---\ndescription: Repository audit evidence contract - applies to any audit, review or due-diligence task\n"
        "alwaysApply: true\n---\n\n" + rule)))
    # --- GitHub Copilot: repo-wide + path-scoped instructions ---------------------------------
    report.append(("copilot/.github/copilot-instructions.md",
        w(f"{a.out}/copilot/.github/copilot-instructions.md", rule)))
    report.append(("copilot/.github/instructions/rda-core.instructions.md",
        w(f"{a.out}/copilot/.github/instructions/rda-core.instructions.md",
          '---\napplyTo: "**"\nname: rda-core\ndescription: Repository audit evidence contract\n---\n\n' + rule)))
    # --- Devin Desktop / Windsurf: trigger-based rules, 12k cap; global file 6k cap ------------
    report.append(("devin/.devin/rules/rda-core.md", w(f"{a.out}/devin/.devin/rules/rda-core.md",
        "---\ntrigger: model_decision\ndescription: Repository audit evidence contract - load for any audit, review or due-diligence task\n---\n\n" + rule)))
    report.append(("windsurf/.windsurf/rules/rda-core.md", w(f"{a.out}/windsurf/.windsurf/rules/rda-core.md",
        "---\ntrigger: model_decision\ndescription: Repository audit evidence contract\n---\n\n" + rule)))
    # --- Antigravity: .agents/rules, 12k cap --------------------------------------------------
    report.append(("antigravity/.agents/rules/rda-core.md",
        w(f"{a.out}/antigravity/.agents/rules/rda-core.md", rule)))
    # --- Aider: CONVENTIONS.md + config -------------------------------------------------------
    report.append(("aider/CONVENTIONS.md", w(f"{a.out}/aider/CONVENTIONS.md", rule)))
    report.append(("aider/.aider.conf.yml", w(f"{a.out}/aider/.aider.conf.yml",
        "# Aider has no skill system: load the contract explicitly and keep it read-only/cacheable.\n"
        "read:\n  - CONVENTIONS.md\n  - AGENTS.md\nmap-tokens: 4096\nmap-refresh: auto\ncache-prompts: true\n")))
    # --- Gemini CLI: TOML command per profile -------------------------------------------------
    for pid, plist in PROFILES.items():
        ids = " ".join(f"RDA-{n}" for n in plist.split()) if plist != "ALL" else "all skills"
        report.append((f"gemini/.gemini/commands/rda/{pid.lower()}.toml",
            w(f"{a.out}/gemini/.gemini/commands/rda/{pid.lower()}.toml",
              f'description = "Run the RDA {pid} audit profile"\nprompt = """\n'
              f'Run the RDA audit profile {pid} on this repository.\nActivate in DAG order: {ids}.\n'
              f'Obey the RDA-00 contract. Pin commits, produce census denominators first, and finish with the\n'
              f'RDA-32 verification gate before any report is written.\nScope: {{{{args}}}}\n"""\n')))
    # --- Roo Code: custom mode (rules dir has no frontmatter, scoping is via modes) ------------
    report.append(("roocode/.roomodes", w(f"{a.out}/roocode/.roomodes",
        "customModes:\n  - slug: rda-audit\n    name: RDA Repository Audit\n"
        "    description: Evidence-governed repository audit and technical due diligence\n"
        "    roleDefinition: >-\n      You are a repository auditor operating under the RDA evidence contract.\n"
        "      Every claim is labelled, cited to path#Lstart-Lend at a pinned commit, and carries an awarded\n"
        "      confidence level. You never assert deployment, scale, cost, exploitability, dead code, compliance\n"
        "      or individual ownership from source alone.\n"
        "    whenToUse: >-\n      Use for repository audits, security assessments, architecture reviews, technical\n"
        "      due diligence, production readiness reviews and codebase onboarding.\n"
        "    groups:\n      - read\n      - command\n      - - edit\n        - fileRegex: \\.(md|json|csv|sarif)$\n"
        "          description: Audit outputs only - the auditor never edits source\n")))
    report.append(("roocode/.roo/rules-rda-audit/00-contract.md",
        w(f"{a.out}/roocode/.roo/rules-rda-audit/00-contract.md", rule)))
    # --- AGENTS.md: the shared standard --------------------------------------------------------
    idx = "\n".join(f"- `{s['name']}` ({s['id']}) — {s['desc']}" for s in skills)
    report.append(("AGENTS.md", w(f"{a.out}/AGENTS.md",
        rule + "\n## Available RDA skills\n\n" + idx + "\n")))
    # --- OpenAI Agents SDK scaffold ------------------------------------------------------------
    report.append(("openai-agents/rda_agents.py", w(f"{a.out}/openai-agents/rda_agents.py",
        '"""RDA as an OpenAI Agents SDK graph: one Agent per skill, handoffs follow the DAG,\n'
        'guardrails enforce the finding schema, and tracing supplies the run manifest."""\n'
        "from agents import Agent, Runner  # pip install openai-agents\nimport json, pathlib\n\n"
        "PACK = pathlib.Path(__file__).resolve().parents[2] / 'skills'\n\n"
        "def load(slug):\n    return (PACK / slug / 'SKILL.md').read_text(encoding='utf-8')\n\n"
        "KERNEL = load('rda-00-audit-core')\n\n"
        "def skill_agent(slug, name, handoffs=()):\n"
        "    return Agent(name=name, instructions=KERNEL + '\\n\\n' + load(slug), handoffs=list(handoffs))\n\n"
        "# Build leaf-first so handoffs resolve; see ARCHITECTURE.md section 3 for the full DAG.\n"
        "brief    = skill_agent('rda-36-executive-cto-brief', 'RDA-36')\n"
        "register = skill_agent('rda-33-risk-register-synthesis', 'RDA-33', [brief])\n"
        "verifier = skill_agent('rda-32-evidence-verifier', 'RDA-32', [register])\n"
        "census   = skill_agent('rda-02-repo-census', 'RDA-02', [verifier])\n"
        "orch     = skill_agent('rda-01-audit-orchestrator', 'RDA-01', [census])\n\n"
        "if __name__ == '__main__':\n"
        "    print(Runner.run_sync(orch, 'Audit this repository under profile P2.').final_output)\n")))

    over = [(p, n) for p, n in report if p.endswith("rda-core.md") and n > FILE_RULE_CAP]
    print(f"profile={a.profile} skills={len(skills)}")
    for p, n in report: print(f"  {n:6d}  {p}")
    print(f"\nkernel rule = {len(rule)} chars "
          f"({'fits' if len(rule) <= GLOBAL_RULE_CAP else 'EXCEEDS'} the {GLOBAL_RULE_CAP}-char global-rules cap; "
          f"{'fits' if len(rule) <= FILE_RULE_CAP else 'EXCEEDS'} the {FILE_RULE_CAP}-char per-file rule cap)")

    if a.check:
        drift = []
        for path, text in sorted(PENDING.items()):
            if not os.path.exists(path):
                drift.append(f"MISSING   {path}"); continue
            with open(path, encoding="utf-8", newline="") as fh:
                on_disk = fh.read()
            if on_disk.replace("\r\n", "\n") != text.replace("\r\n", "\n"):
                drift.append(f"DIFFERS   {path}")
        expected = {os.path.normpath(p) for p in PENDING}
        for root, _, files in os.walk(a.out):
            for f in files:
                p = os.path.normpath(os.path.join(root, f))
                if p not in expected: drift.append(f"ORPHANED  {p}")
        if drift:
            print("\nADAPTER DRIFT -- adapters are generated, never hand-maintained:")
            for d in drift: print(f"  {d}")
            print(f"\nRegenerate with: python3 {os.path.basename(__file__)} "
                  f"--skills {a.skills} --out {a.out} --profile {a.profile}")
            return 1
        print(f"\ncheck: {len(PENDING)} adapters match the committed tree")

    return 1 if over or len(rule) > GLOBAL_RULE_CAP else 0

if __name__ == "__main__":
    sys.exit(main())
