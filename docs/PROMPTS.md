# Prompts

The default submitted run is deterministic and does not require an LLM key.

If `OPENAI_API_KEY` is set and `--llm auto` or `--llm always` is used, the pipeline sends a JSON payload with this instruction shape:

```text
You are a careful VC analyst. You never invent facts.

Task: Rewrite concise VC memo sections from provided structured facts. Do not add claims.

Constraints:
- Use only the candidate, evidence, score, and risks provided.
- Do not change recommendation, score, source URLs, or evidence.
- Return JSON with keys team, product, market, rationale, risks, change_mind.
```

The model is not allowed to change the score or recommendation. That keeps source-of-truth logic deterministic and makes the LLM a prose editor rather than an untraceable decision maker.

## API Shape

The adapter calls `POST /v1/responses` and requests Structured Outputs with `text.format.type = json_schema`.

Default model:

```text
gpt-5.4-mini
```

The expected JSON keys are:

```json
{
  "team": "string",
  "product": "string",
  "market": "string",
  "rationale": "string",
  "risks": ["string"],
  "change_mind": ["string"]
}
```

This keeps the LLM feature useful but bounded: it can improve memo prose, not silently alter the investment decision.
