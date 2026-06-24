from __future__ import annotations

import argparse
from pathlib import Path

from .env import load_env_file
from .pipeline import RunConfig, run_pipeline
from .util import slugify


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="venture-pipeline",
        description="Source, analyze, and memo seed-stage startup candidates from public data.",
    )
    subparsers = parser.add_subparsers(dest="command")

    run = subparsers.add_parser("run", help="Run the full sourcing -> analysis -> memo pipeline.")
    run.add_argument("--topic", required=True, help='Seed topic, for example "AI agents for SMBs".')
    run.add_argument("--limit", type=int, default=12, help="Number of startups to analyze.")
    run.add_argument(
        "--sources",
        default="yc",
        help="Comma-separated sources. Supported: yc, hn, url. Default: yc.",
    )
    run.add_argument("--yc-batch", default=None, help="Optional YC batch filter, for example W25 or Winter 2025.")
    run.add_argument(
        "--urls",
        type=Path,
        default=None,
        help="Optional text file with one startup URL per line. Automatically enables the url source.",
    )
    run.add_argument("--include-inactive", action="store_true", help="Include inactive/dead companies from sources.")
    run.add_argument(
        "--llm",
        choices=("auto", "never", "always"),
        default="auto",
        help="Use optional LLM enrichment when available. Default: auto.",
    )
    run.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory. Defaults to outputs/<topic-slug>.",
    )
    run.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Optional local env file for OPENAI_API_KEY/OPENAI_MODEL. Do not commit this file.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command != "run":
        parser.print_help()
        return 2

    limit = max(1, min(args.limit, 25))
    sources = tuple(source.strip().lower() for source in args.sources.split(",") if source.strip())
    urls = _read_urls(args.urls) if args.urls else ()
    if urls and "url" not in sources:
        sources = (*sources, "url")
    if args.env_file:
        loaded = load_env_file(args.env_file)
        if loaded:
            print(f"Loaded env keys from {args.env_file}: {', '.join(loaded)}")
    out_dir = args.out or Path("outputs") / slugify(args.topic)
    result = run_pipeline(
        RunConfig(
            topic=args.topic,
            limit=limit,
            sources=sources,
            yc_batch=args.yc_batch,
            urls=urls,
            out_dir=out_dir,
            include_inactive=args.include_inactive,
            llm_mode=args.llm,
        )
    )

    print(f"Wrote {len(result.analyses)} memos to {result.out_dir}")
    for analysis in result.analyses[:5]:
        print(f"- {analysis.candidate.name}: {analysis.recommendation} ({analysis.score.total}/100)")
    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"- {warning}")
    return 0


def _read_urls(path: Path) -> tuple[str, ...]:
    if not path.exists():
        raise FileNotFoundError(f"URL file not found: {path}")
    urls = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            urls.append(stripped)
    return tuple(urls)
