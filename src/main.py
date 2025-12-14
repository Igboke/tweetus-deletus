import json
import time
from dataclasses import dataclass
import logging
import os
import sys
import argparse
from dotenv import load_dotenv
from src.database import TweetStatus, SQLiteTweetRepository, TweetRepository
from src.worker import Worker, GeminiAnalyzer, Analyzer
from src.loader import TweetLoader
from src.exceptions import LoaderError
from src.reporter import CSVReportGenerator, ReportGenerator
import csv

load_dotenv()

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)  
    
def main():
    parser = argparse.ArgumentParser(description="Tweetus Deletus: The Tweet Cleaner")

    subparsers = parser.add_subparsers(dest="command", required=True)

    load_parser = subparsers.add_parser("load", help="Load tweets from JS file to DB")
    load_parser.add_argument("file", help="Path to tweets.js file")
    load_parser.add_argument("--handle", help="Twitter handle (overrides .env)")
    load_parser.add_argument("--db", default='tweets.db', help="Database file path")

    worker_parser = subparsers.add_parser("worker", help="Start worker to analyze tweets")
    worker_parser.add_argument("--db", default='tweets.db', help="Database file path")
    worker_parser.add_argument('forbidden', help='Comma-separated forbidden words')
    worker_parser.add_argument('--retry', action='store_true', help='Retry FAILED tweets')

    generate_report_parser = subparsers.add_parser("report", help="Generate report of tweets")
    generate_report_parser.add_argument("--db", default='tweets.db', help="Database file path")
    generate_report_parser.add_argument("--output", default='report.csv', help="Output file path")
    generate_report_parser.add_argument("--status", choices=[s.name for s in TweetStatus], default='ANALYZED_DANGEROUS', help="Filter tweets by status (default: ANALYZED_DANGEROUS)")

    args = parser.parse_args()

    if args.command == "load":
        handle:str = args.handle or os.getenv("X_HANDLE")

        if not handle:
            logger.error("[MAIN] ERROR: NO HANDLE PROVIDED! SET X_HANDLE IN .env OR USE --handle")
            sys.exit(1)
        
        logger.info(f"[MAIN] INFO: LOADING TWEETS FOR @{handle} INTO {args.db}")

        try:
            repo:TweetRepository = SQLiteTweetRepository(args.db)
            loader:TweetLoader = TweetLoader(repo, handle)
            loader.run(args.file)
        except LoaderError as e:
            logger.critical(f"[MAIN] LOADER FAILED: {e}")
            sys.exit(1)
    
    elif args.command == "worker":

        GEMINI_API_KEY:str = os.getenv("GEMINI_API_KEY")
        GEMINI_MODEL:str = os.getenv("GEMINI_MODEL","gemini-2.5-flash")

        if not GEMINI_API_KEY:
            logger.critical("[MAIN] ERROR: NO GEMINI API KEY SET IN .env")
            sys.exit(1)

        forbidden_words:list[str] = args.forbidden.split(",")

        analyzer:Analyzer = GeminiAnalyzer(GEMINI_API_KEY,GEMINI_MODEL)
        repo:TweetRepository = SQLiteTweetRepository(args.db)
        worker:Worker = Worker(analyzer, repo) 

        worker.run(forbidden_words, args.retry)

    elif args.command == "report":
        try:
            status_enum = TweetStatus[args.status]
        except KeyError:
            logger.error(f"[MAIN] INVALID STATUS: {args.status}")
            sys.exit(1)

        repo:TweetRepository = SQLiteTweetRepository(args.db)
        reporter:ReportGenerator = CSVReportGenerator(repo)
        reporter.generate(status_enum, args.output)
        
   

if __name__ == "__main__":
    main()
