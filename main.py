import json
import time
from dataclasses import dataclass
import logging
import os
import sys
import argparse
from dotenv import load_dotenv
from database import init_db,add_tweet, update_tweet_status, get_tweet_with_lock, mark_tweet_as_failed, get_tweet_reports, TweetStatus
from tweets import get_tweet_details
from worker import Worker, GeminiAnalyzer, Analyzer

load_dotenv()

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def convert_rawdata_to_python_object(raw_data:str) -> list:
    start_index = raw_data.find('[')
    if start_index == -1:
        logger.error("[CONVERT_RAWDATA_TO_PYTHON_OBJECT] JSON NOT FOUND ")
        raise Exception("JSON NOT FOUND") from e

    json_payload = raw_data[start_index : ]
    try:
        return json.loads(json_payload)
    except json.JSONDecodeError as e:
        logger.error("[CONVERT_RAWDATA_TO_PYTHON_OBJECT] JSON DECODE ERROR",exc_info=True)
        raise Exception("JSON DECODE ERROR") from e
        
def open_file(file_path:str)->str:
    try:
        with open (file_path, 'r', encoding='utf-8') as tweet_doc:
            raw_data = tweet_doc.read()
            logger.debug("[OPEN_FILE] FILE SUCCESSFULLY PARSED")
    except Exception as e:
        logger.error(f"[OPEN_FILE] ERROR: {e}",exc_info=True)
        raise Exception("CANNOT OPEN FILE") from e
    return raw_data

def load_tweets_into_db(file_path:str,x_handle:str,db_name:str):
    try:
        init_db(db_name)

        raw_data = open_file(file_path)

        tweets = convert_rawdata_to_python_object(raw_data)

    except Exception as e:
        logger.error(f"[LOAD_TWEETS_INTO_DB] ERROR: {e}",exc_info=True)
        return
    
    for tweet in tweets:
        item = tweet.get('tweet')

        if item is None:
            logger.error("[LOAD_TWEETS_INTO_DB] ERROR: NO TWEET FOUND")
            raise Exception("POSSIBLE CHANGE TO TWEET STRUCTURE, NO TWEET FOUND")

        try:
            details = get_tweet_details(item)

            tweet_url = details.tweet_url % x_handle

            add_tweet(details,tweet_url,db_name)

        except Exception as e:
            logger.error("[LOAD_TWEETS_INTO_DB] ERROR: {e}",exc_info=True)
            return
    
    logger.info("[LOAD_TWEETS_INTO_DB] TWEETS SUCCESSFULLY PARSED")

def start_worker(worker:Analyzer,forbidden_words:list,db_name:str,retry_failed:bool=False):
    while True:
        
        try:
            if retry_failed:
                tweet = get_tweet_with_lock(TweetStatus.FAILED,db_name=db_name)
            else:
                tweet = get_tweet_with_lock(db_name=db_name)

            if tweet is None:
                logger.info("[START_WORKER] NO PENDING TWEET FOUND")
                break

            response = worker.analyze_tweet(tweet.full_text,forbidden_words)

            reason = worker.get_reason(response)

            if response.startswith("YES"):
                update_tweet_status(tweet.tweet_id,TweetStatus.ANALYZED_DANGEROUS,reason,db_name=db_name)
            elif response.startswith("NO"):
                update_tweet_status(tweet.tweet_id,TweetStatus.ANALYZED_SAFE,reason,db_name=db_name)
            else:
                update_tweet_status(tweet.tweet_id,TweetStatus.FAILED,reason,db_name=db_name)

            logger.info("[START_WORKER] WORKER COMPLETED ANALYSIS")
            time.sleep(15)


        except KeyboardInterrupt:
            logger.info("[START_WORKER] INTERRUPTED")
            if tweet:
                mark_tweet_as_failed(tweet.tweet_id,"Interrupted by User",db_name=db_name)
            break

        except Exception as e:
            logger.error("[START_WORKER] ERROR: {e}",exc_info=True)
            mark_tweet_as_failed(tweet.tweet_id,str(e),db_name=db_name)
            time.sleep(2)
            continue 

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
        handle = args.handle or os.getenv("X_HANDLE")

        if not handle:
            logger.error("[MAIN] ERROR: NO HANDLE PROVIDED! SET X_HANDLE IN .env OR USE --handle")
            sys.exit(1)
        
        logger.info(f"[MAIN] INFO: LOADING TWEETS FOR @{handle} INTO {args.db}")

        load_tweets_into_db(args.file, handle, args.db)
    
    elif args.command == "worker":

        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        GEMINI_MODEL = os.getenv("GEMINI_MODEL","gemini-2.5-flash")

        if not GEMINI_API_KEY:
            logger.critical("[MAIN] ERROR: NO GEMINI API KEY SET IN .env")
            sys.exit(1)

        forbidden_words = args.forbidden.split(",")

        analyzer = GeminiAnalyzer(GEMINI_API_KEY,GEMINI_MODEL)
        worker = Worker(analyzer) 

        start_worker(worker, forbidden_words,args.db,args.retry)

    elif args.command == "report":
        generate_report(args.db, args.output)
        
   

if __name__ == "__main__":
    main()
