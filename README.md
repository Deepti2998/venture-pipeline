# Venture Pipeline

Small, replayable investment triage pipeline for the Emergence take-home assignment.

The pipeline takes a seed topic, sources 10-20 startups from public data, runs a structured thesis-based analysis, and writes partner-skimmable memos with traceable evidence.

## Quick Start

```powershell
python -m venture_pipeline run --topic "AI agents for SMBs" --yc-batch W25 --limit 12 --out outputs/sample-ai-agents-for-smbs
```

Outputs:

- `candidates.json`: normalized source records
- `analysis.json`: structured analysis and scoring
- `memos/*.md`: one memo per startup
- `run_report.md`: summary of calls, scores, warnings, and source coverage
- `ai_trace.jsonl`: records whether heuristic or LLM analysis was used

## Requirements

- Python 3.10+
- Public internet access to the YC OSS API
- Optional: `OPENAI_API_KEY` and `OPENAI_MODEL` if you want LLM prose enrichment

The default run does not require paid APIs. It uses a deterministic analyst so reviewers can run one command without credentials. If an OpenAI key is present and `--llm auto` is used, the pipeline asks the model to tighten the memo sections while keeping the same source evidence, score, and recommendation.

To use LLM polishing safely, create a local `.env` from `.env.example` and keep it out of Git:

```powershell
Copy-Item .env.example .env
# edit .env and set a fresh OPENAI_API_KEY
python -m venture_pipeline run --topic "AI agents for SMBs" --yc-batch W25 --limit 12 --llm always --env-file .env
```

The OpenAI adapter uses the Responses API with Structured Outputs. The default model is `gpt-5.4-mini`, chosen as the lower-latency/lower-cost option for this bounded rewriting task. Override it with `OPENAI_MODEL`.

## Source Choice

Primary source: YC public company directory via `yc-oss/api`.

This intentionally goes deep on one source rather than shallow across many. The source gives company name, site, one-liner, long description, batch, status, stage, hiring, team size, industry, tags, and durable YC profile URL. That is enough to satisfy the assignment's sourcing fields while keeping claims traceable.

Optional sources:

- Hacker News Algolia search via `--sources yc,hn`.
- Provided startup URLs via `--urls sample_urls.txt` or `--sources url --urls sample_urls.txt`.

The submitted sample uses YC only because the rubric explicitly allows one strong source and YC gives the cleanest traceable records.

## Common Commands

```powershell
# Run sample topic through the YC W25 feed
python -m venture_pipeline run --topic "AI agents for SMBs" --yc-batch W25 --limit 12

# Search all YC public companies for a topic
python -m venture_pipeline run --topic "vertical AI agents for healthcare billing" --limit 15

# Force deterministic analysis even if an API key is set
python -m venture_pipeline run --topic "AI agents for SMBs" --yc-batch W25 --llm never

# Include a list of explicit startup URLs
python -m venture_pipeline run --topic "AI agents for SMBs" --urls sample_urls.txt --limit 12

# Require OpenAI memo polishing from a local env file
python -m venture_pipeline run --topic "AI agents for SMBs" --yc-batch W25 --llm always --env-file .env

# Run tests
python -m unittest discover -s tests
```

## Submission Notes

Before submitting:

- Commit generated outputs so reviewers do not need to rerun.
- Record a five minute walkthrough showing one startup end-to-end.
- Do not commit `.env` or API keys.
- Add your own first-person review note in `docs/AI_WORKFLOW.md` before submitting. The current note is an honest engineering/process record, not a fake claim of unaided work.
