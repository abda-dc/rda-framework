"""RDA as an OpenAI Agents SDK graph: one Agent per skill, handoffs follow the DAG,
guardrails enforce the finding schema, and tracing supplies the run manifest."""
from agents import Agent, Runner  # pip install openai-agents
import json, pathlib

PACK = pathlib.Path(__file__).resolve().parents[2] / 'skills'

def load(slug):
    return (PACK / slug / 'SKILL.md').read_text(encoding='utf-8')

KERNEL = load('rda-00-audit-core')

def skill_agent(slug, name, handoffs=()):
    return Agent(name=name, instructions=KERNEL + '\n\n' + load(slug), handoffs=list(handoffs))

# Build leaf-first so handoffs resolve; see ARCHITECTURE.md section 3 for the full DAG.
brief    = skill_agent('rda-36-executive-cto-brief', 'RDA-36')
register = skill_agent('rda-33-risk-register-synthesis', 'RDA-33', [brief])
verifier = skill_agent('rda-32-evidence-verifier', 'RDA-32', [register])
census   = skill_agent('rda-02-repo-census', 'RDA-02', [verifier])
orch     = skill_agent('rda-01-audit-orchestrator', 'RDA-01', [census])

if __name__ == '__main__':
    print(Runner.run_sync(orch, 'Audit this repository under profile P2.').final_output)
