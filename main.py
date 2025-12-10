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
        raise Exception("Json not found")

    json_payload = raw_data[start_index : ]
    return json.loads(json_payload)

def get_tweet_details(tweet):
    full_text:str=tweet.get('full_text')
    tweet_id:str=tweet.get('id')
    is_comment=True if tweet.get('in_reply_to_screen_name',False) else False
    is_retweet:bool= True if full_text.startswith("RT") else False
    is_tweet:bool=True if not(is_comment or is_retweet) else False


    return Tweet(full_text, tweet_id, is_comment, is_retweet,is_tweet)
    
def main():
    file_path = "./tweets.js"
    x_handle = os.getenv("X_HANDLE")
    try:
        with open (file_path, 'r', encoding='utf-8') as f:
            raw_data = f.read()
        logger.debug("[MAIN] File sucessfully parsed")
    except Exception as e:
        logger.error(f"[MAIN] Error {e}",exc_info=True)

    try:
        tweets = convert_rawdata_to_python_object(raw_data)
    except Exception as e:
        logger.error(f"[MAIN] {e}")

    
    for tweet in tweets[:10]:
        # tweet.get('tweet')
        # for key, value in tweet.get('tweet').items():
        #     print (f"{key} \t\t {value}",end="\n\n")

        item = tweet.get('tweet')
        details = get_tweet_details(item)
        print(details)





if __name__ == "__main__":
    main()
