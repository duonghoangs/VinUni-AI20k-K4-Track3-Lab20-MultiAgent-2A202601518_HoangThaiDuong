# Benchmark Report

Generated from matched queries and the bundled offline corpus.

| Run | Provider | Query | Latency (s) | Cost | Tokens | Steps | Retries | Quality | Citations | Failures | Notes |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| baseline-1 | openrouter | Research GraphRAG state-of-the-art and write a 500-word summary | 8.70 | 0.0006 | 2472 | 0 | 0 | 8.7 | 57% | 0% |  |
| multi-agent-1 | openrouter | Research GraphRAG state-of-the-art and write a 500-word summary | 26.64 | 0.0023 | 9445 | 4 | 0 | 7.9 | 64% | 0% |  |
| baseline-2 | openrouter | Compare single-agent and multi-agent workflows for customer support | 6.56 | 0.0006 | 2454 | 0 | 0 | 7.9 | 31% | 0% |  |
| multi-agent-2 | openrouter | Compare single-agent and multi-agent workflows for customer support | 21.41 | 0.0020 | 8474 | 4 | 0 | 8.8 | 60% | 0% |  |
| baseline-3 | openrouter | Summarize production guardrails for LLM agents | 12.16 | 0.0007 | 2420 | 0 | 0 | 8.2 | 42% | 0% |  |
| multi-agent-3 | openrouter | Summarize production guardrails for LLM agents | 23.53 | 0.0019 | 8120 | 4 | 0 | 8.7 | 58% | 0% |  |

## Average comparison

- Quality: baseline `8.27`, multi-agent `8.47` (delta `+0.20`).
- Citation coverage: baseline `43%`, multi-agent `61%` (delta `+17%`).
- Latency: baseline `9.14s`, multi-agent `23.86s` (`2.61x`).
- Estimated cost: baseline `$0.0006`, multi-agent `$0.0021` (`3.26x`).

## Interpretation

Quality is a transparent structural score based on answer completeness, valid inline citations, citation coverage, source diversity, and successful completion. It is not a substitute for expert factual review.

Multi-agent runs normally use more steps and may cost more. A higher score is useful only when the quality or traceability gain justifies that overhead.

## Failure mode

Primary risk: evidence or citation provenance can be lost during handoff. The workflow mitigates this with typed shared state, immutable source IDs, bounded routing, offline fallbacks, and citation validation before accepting writer output.

## Trace evidence

Visual evidence: [successful workflow trace](trace_evidence.svg). Per-run JSON traces are stored beside this report in `reports/traces/`.
