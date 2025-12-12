import json
from dataclasses import dataclass
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class Tweet:
    full_text:str
    tweet_id:str
    is_comment:bool
    is_retweet:bool
    is_tweet:bool

def convert_rawdata_to_python_object(raw_data):
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
        

def get_tweet_details(tweet):
    full_text:str=tweet.get('full_text')
    tweet_id:str=tweet.get('id')
    is_comment=True if tweet.get('in_reply_to_screen_name',False) else False
    is_retweet:bool= True if full_text.startswith("RT") else False
    is_tweet:bool=True if not(is_comment or is_retweet) else False


    return Tweet(full_text, tweet_id, is_comment, is_retweet,is_tweet)

def open_file(file_path):
    try:
        with open (file_path, 'r', encoding='utf-8') as tweet_doc:
            raw_data = tweet_doc.read()
    except Exception as e:
        logger.error(f"[OPEN_FILE] ERROR: {e}",exc_info=True)
        raise Exception("CANNOT OPEN FILE") from e
    return raw_data
    
def main():
    file_path = "./tweets.js"
    forbidden_words = ["rape","forex","crypto"]
    x_handle = os.getenv("X_HANDLE")
    try:
        raw_data = open_file(file_path)
        logger.debug("[MAIN] FILE SUCCESSFULLY PARSED")
    except Exception as e:
        logger.error(f"[MAIN] ERROR: {e}",exc_info=True)

    try:
        tweets = convert_rawdata_to_python_object(raw_data)
    except Exception as e:
        logger.error(f"[MAIN] ERROR: {e}",exc_info=True)

    
    for tweet in tweets[:10]:
        try:
            item = tweet.get('tweet')
        except Exception as e:
            logger.error(f"[MAIN] ERROR: {e}",exc_info=True)
            raise Exception("POSSIBLE CHANGE TO TWEET STRUCTURE, NO TWEET FOUND",exc_info=True) as e

        details = get_tweet_details(item)






if __name__ == "__main__":
    main()
