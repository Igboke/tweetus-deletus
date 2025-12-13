import json
import time
from dataclasses import dataclass
import logging
import os
from dotenv import load_dotenv
from database import init_db,add_tweet, update_tweet_status, get_tweet_with_lock, mark_tweet_as_failed
from tweets import get_tweet_details
from worker import Worker, GeminiAnalyzer, Analyzer

load_dotenv()

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

def load_tweets_into_db(file_path:str,x_handle:str):
    try:
        init_db()

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
            
            add_tweet(details,tweet_url)

        except Exception as e:
            logger.error("[LOAD_TWEETS_INTO_DB] ERROR: {e}",exc_info=True)
            return
    
    logger.info("[LOAD_TWEETS_INTO_DB] TWEETS SUCCESSFULLY PARSED")

def start_worker(worker:Analyzer,forbidden_words:list):
    while True:
        
        try:
            tweet = get_tweet_with_lock()

            if tweet is None:
                logger.info("[START_WORKER] NO PENDING TWEET FOUND")
                break

            response = worker.analyze_tweet(tweet.full_text,forbidden_words)

            reason = worker.get_reason(response)

            if response.startswith("YES"):
                update_tweet_status(tweet.tweet_id,TweetStatus.ANALYZED_DANGEROUS,reason)
            elif response.startswith("NO"):
                update_tweet_status(tweet.tweet_id,TweetStatus.ANALYZED_SAFE,reason)
            else:
                update_tweet_status(tweet.tweet_id,TweetStatus.FAILED,reason)

            logger.info("[START_WORKER] TWEET ANALYZED")


        except KeyboardInterrupt:
            logger.info("[START_WORKER] INTERRUPTED")
            if tweet:
                mark_tweet_as_failed(tweet.tweet_id,"Interrupted by User")
            break

        except Exception as e:
            logger.error("[START_WORKER] ERROR: {e}",exc_info=True)
            mark_tweet_as_failed(tweet.tweet_id,str(e))
            time.sleep(2)
            continue 

    
    
def main():
    file_path = "./tweets.js"
    forbidden_words = ["rape","forex","crypto"]
    x_handle = os.getenv("X_HANDLE")

    if not os.getenv("GEMINI_API_KEY"):
        logger.error("[MAIN] ERROR: NO GEMINI API KEY")
        raise Exception("NO GEMINI API KEY")

    if not os.getenv("GEMINI_MODEL"):
        logger.error("[MAIN] ERROR: NO GEMINI MODEL")
        raise Exception("NO GEMINI MODEL")

    if not os.getenv("X_HANDLE"):
        logger.error("[MAIN] ERROR: NO X_HANDLE")
        raise Exception("NO X_HANDLE")

    load_tweets_into_db(file_path,x_handle)

    analyzer = GeminiAnalyzer(os.getenv("GEMINI_API_KEY"),os.getenv("GEMINI_MODEL"))
    worker = Worker(analyzer)  

    start_worker(worker,forbidden_words)     

if __name__ == "__main__":
    main()
