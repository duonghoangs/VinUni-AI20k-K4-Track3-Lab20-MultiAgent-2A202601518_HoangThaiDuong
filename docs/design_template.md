# Design Template

## Problem

The system answers open-ended technical research questions from the bundled offline corpus. It
must retrieve relevant evidence, preserve provenance, compare source strength, and produce a
cited report that can be compared with a single-agent baseline.

## Why multi-agent?

Complex research mixes distinct concerns: retrieval, evidence assessment, synthesis, and routing.
Separating them makes intermediate artifacts inspectable and allows each failure to be measured.
The benchmark still retains a single-agent baseline because narrow questions may not justify
coordination overhead.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Route by state completeness and enforce iteration limit | Typed shared state | Next route | Loop or premature stop |
| Researcher | Retrieve, filter, and label offline evidence | Query and source limit | Sources and evidence ledger | Irrelevant or duplicated sources |
| Analyst | Compare claims, source classes, and limitations | Evidence ledger and sources | Analysis notes | False consensus or overgeneralization |
| Writer | Produce balanced cited report | Research and analysis artifacts | Final answer | Unsupported claim or invented citation |

## Shared state

`ResearchState` is the authoritative handoff object. It stores request constraints, current route,
route history, iteration count, retrieved sources, research notes, analysis notes, final answer,
agent results, trace events, errors, retries, token usage, and estimated cost. Source metadata keeps
`source_id`, topic, document class, and `is_synthetic` across every handoff.

## Routing policy

```text
START -> Supervisor
Supervisor -> Researcher -> Supervisor   when evidence is missing
Supervisor -> Analyst -> Supervisor      when analysis is missing
Supervisor -> Writer -> Supervisor       when answer is missing
Supervisor -> END                        when answer exists or iteration limit is reached
```

## Guardrails

- Max iterations: 6 by default, configurable with `MAX_ITERATIONS`.
- Timeout: each OpenRouter request uses `TIMEOUT_SECONDS`; graph recursion is also bounded.
- Retry: provider requests retry up to `MAX_RETRIES` with bounded exponential delay.
- Fallback: all required agents have deterministic offline behavior when no key exists or an API
  request fails.
- Validation: Pydantic validates public state; writer output must contain a retrieved source ID;
  synthetic evidence remains labeled.

## Benchmark plan

The configured query suite runs through both architectures with identical offline retrieval access.
Metrics are wall-clock latency, estimated API cost, token use, workflow steps, structural quality,
citation coverage, and failure rate. Multi-agent should expose better intermediate traceability;
single-agent should usually remain faster and simpler in offline mode. Architecture choice is based
on measured trade-offs, not an assumed winner.
