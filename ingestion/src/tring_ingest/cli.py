"""Entrypoint: python -m tring_ingest --source appsflyer --from YYYY-MM-DD --to YYYY-MM-DD

Dates can also be passed via env vars DATE_FROM / DATE_TO (used by Cloud Run Jobs via
--update-env-vars). Args take precedence over env vars.
"""

import argparse
import os
import sys

from tring_ingest.common.logging import get_logger

logger = get_logger(__name__)

SOURCES = ["appsflyer", "moengage", "play_console", "app_store"]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Dashboard Monitoring & AI Insight  -  data pipeline ingestion")
    parser.add_argument("--source", required=True, choices=SOURCES, help="Data source to extract")
    parser.add_argument("--from", dest="date_from", default=os.environ.get("DATE_FROM"), help="Start date YYYY-MM-DD (or env DATE_FROM)")
    parser.add_argument("--to", dest="date_to", default=os.environ.get("DATE_TO"), help="End date YYYY-MM-DD (or env DATE_TO)")
    args = parser.parse_args(argv)
    if not args.date_from or not args.date_to:
        parser.error("--from/--to required (or set DATE_FROM/DATE_TO env vars)")
    return args


def main(argv=None):
    if not os.environ.get("GCP_PROJECT"):
        raise SystemExit("ERROR: GCP_PROJECT environment variable is required. Set it before running.")

    args = parse_args(argv)
    logger.info(
        "Starting extraction",
        extra={"source": args.source, "from": args.date_from, "to": args.date_to},
    )

    if args.source == "appsflyer":
        from tring_ingest.sources.appsflyer.extract import run

        run(date_from=args.date_from, date_to=args.date_to)
    elif args.source == "moengage":
        raise NotImplementedError("MoEngage source not yet implemented")
    elif args.source == "play_console":
        raise NotImplementedError("Play Console source not yet implemented")
    elif args.source == "app_store":
        raise NotImplementedError("App Store source not yet implemented")
    else:
        logger.error("Unknown source", extra={"source": args.source})
        sys.exit(1)

    logger.info("Extraction complete", extra={"source": args.source})


if __name__ == "__main__":
    main()
