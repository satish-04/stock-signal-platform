#!/usr/bin/env python3
"""Import a reviewed research report or trading-board analysis into the platform."""
import argparse
import json
import os
from pathlib import Path

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path, help="Markdown report or JSON analysis file")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--provider", choices=["grok-x-research", "ai-trading-board"], required=True)
    parser.add_argument("--headline", required=True)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--source-id", help="Stable unique source ID; defaults to the artifact path")
    parser.add_argument("--api-url", default=os.getenv("PLATFORM_API_URL", "http://localhost:8080"))
    args = parser.parse_args()

    secret = os.getenv("TRADINGVIEW_WEBHOOK_SECRET")
    if not secret:
        parser.error("set TRADINGVIEW_WEBHOOK_SECRET in the environment")
    body = args.artifact.read_text(encoding="utf-8")
    payload = {
        "symbol": args.symbol,
        "provider": args.provider,
        "headline": args.headline,
        "body": body,
        "source_id": args.source_id or str(args.artifact.resolve()),
        "reviewed_by": args.reviewer,
    }
    response = httpx.post(
        f"{args.api_url.rstrip('/')}/api/v1/research/artifacts",
        headers={"X-Webhook-Secret": secret},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    main()