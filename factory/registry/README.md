# Agent + Skill Registry

The factory uses open-source projects as references and optional adapters, not as blind dependencies.

## Promotion pipeline

`discover -> inspect -> license -> security -> sandbox -> benchmark -> register -> promote`

A skill cannot be resolved for production execution until it has verified test and security evidence.

Agents are selected by required capabilities plus evidence. Popularity never overrides failed verification.

## Curated initial set

- OpenHands: software engineering execution reference
- SWE-agent / mini-swe-agent: repair and lightweight coding workers
- LangGraph: stateful orchestration reference
- CrewAI: role-based delegation reference
- Letta: long-term state/memory reference
- smolagents: lightweight tool-agent reference
- PydanticAI: typed contracts and structured outputs

## Factory rule

Do not vendor or copy an upstream project merely because it is popular. Prefer a small adapter or extracted pattern when that gives the factory the needed capability with lower operational risk.
