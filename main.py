import json
from dataclasses import dataclass
import logging
import os
from dotenv import load_dotenv
from database import init_db,add_tweet
from tweets import get_tweet_details

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
    
def main():
    file_path = "./tweets.js"
    forbidden_words = ["rape","forex","crypto"]
    x_handle = os.getenv("X_HANDLE")

    try:
        init_db()

        raw_data = open_file(file_path)

        tweets = convert_rawdata_to_python_object(raw_data)

    except Exception as e:
        logger.error(f"[MAIN] ERROR: {e}",exc_info=True)
        return
    
    for tweet in tweets:
        item = tweet.get('tweet')

        if item is None:
            logger.error("[MAIN] ERROR: NO TWEET FOUND")
            raise Exception("POSSIBLE CHANGE TO TWEET STRUCTURE, NO TWEET FOUND")

        try:
            details = get_tweet_details(item)

            add_tweet(details)

        except Exception as e:
            logger.error("[MAIN] ERROR: {e}",exc_info=True)

if __name__ == "__main__":
    main()
