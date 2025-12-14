import json
import time
from dataclasses import dataclass
import logging
import os
import sys
import argparse
from dotenv import load_dotenv
from src.database import get_tweet_reports, TweetStatus
from src.tweets import get_tweet_details
from src.worker import Worker, GeminiAnalyzer, Analyzer
from src.loader import TweetLoader
from src.exceptions import LoaderError
import csv

load_dotenv()

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def generate_report(db_name:str,output_path:str):
    try:
        tweets = get_tweet_reports(TweetStatus.ANALYZED_DANGEROUS, db_name=db_name)
        
        if not tweets:
            logger.info("[GENERATE_REPORT] NO DANGEROUS TWEETS FOUND TO REPORT!")
            return

        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['tweet_id', 'status', 'analysis_reason', 'tweet_url', 'retry_count', 'full_text']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for tweet in tweets:
                writer.writerow({
                    'tweet_id': tweet.tweet_id,
                    'status': tweet.status,
                    'analysis_reason': tweet.analysis_reason,
                    'tweet_url': tweet.tweet_url,
                    'retry_count': tweet.retry_count,
                    'full_text': tweet.full_text
                })
                
        logger.info(f"[GENERATE_REPORT] REPORT GENERATED AT {output_path} WITH {len(tweets)} TWEETS.")
        
    except Exception as e:
        logger.error(f"[GENERATE_REPORT] ERROR: {e}",exc_info=True)
        return
    
    
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

    args = parser.parse_args()

    if args.command == "load":
        handle:str = args.handle or os.getenv("X_HANDLE")

        if not handle:
            logger.error("[MAIN] ERROR: NO HANDLE PROVIDED! SET X_HANDLE IN .env OR USE --handle")
            sys.exit(1)
        
        logger.info(f"[MAIN] INFO: LOADING TWEETS FOR @{handle} INTO {args.db}")

        try:
            loader:TweetLoader = TweetLoader(args.db, handle)
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
        worker:Worker = Worker(analyzer, args.db) 

        worker.run(forbidden_words, args.retry)

    elif args.command == "report":
        generate_report(args.db, args.output)
        
   

if __name__ == "__main__":
    main()
