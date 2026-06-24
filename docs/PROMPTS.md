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
