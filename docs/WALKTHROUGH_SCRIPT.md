# Five Minute Walkthrough Script

Use this as a recording outline, not a memorized script.

1. Show the assignment goal: source candidates, analyze them, write one-page memos, leave an AI/process trail.
2. Run:

```powershell
python -m venture_pipeline run --topic "AI agents for SMBs" --yc-batch W25 --limit 12 --out outputs/sample-ai-agents-for-smbs
```

3. Open `outputs/sample-ai-agents-for-smbs/run_report.md` and point out the ranked calls.
4. Pick one memo from `outputs/sample-ai-agents-for-smbs/memos/`.
5. Trace a claim back to the Evidence section and the normalized `candidates.json` record.
6. Open `venture_pipeline/analysis/scoring.py` and show how the thesis maps to the score.
7. Open `docs/AI_WORKFLOW.md` and explain what the agent did, what you reviewed, and what you would improve with more time.

End by saying what is intentionally out of scope: no queue, no frontend, no private data, no untraceable claims.
