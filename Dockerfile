FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[llm]"

COPY configs ./configs
COPY docs ./docs
COPY ai_agent_offline_research_corpus_v2 ./ai_agent_offline_research_corpus_v2
RUN mkdir -p reports

ENTRYPOINT ["python", "-m", "multi_agent_research_lab.cli"]
