from dataclasses import dataclass
from logging import Logger

logger = Logger(__name__)

@dataclass
class Tweet:
    full_text:str
    tweet_id:str
    is_comment:bool
    is_retweet:bool
    is_tweet:bool

def get_tweet_details(tweet:dict) -> Tweet:
    """Extracts tweet details from a tweet dictionary."""

    full_text:str=tweet.get('full_text')
    if full_text is None:
        logger.error("[GET_TWEET_DETAILS] ERROR: NO FULL TEXT FOUND")
        raise Exception("NO FULL TEXT FOUND")

    tweet_id:str=tweet.get('id')
    if tweet_id is None:
        logger.error("[GET_TWEET_DETAILS] ERROR: NO TWEET ID FOUND")
        raise Exception("NO TWEET ID FOUND")

    is_comment:bool=True if tweet.get('in_reply_to_screen_name',False) else False

    is_retweet:bool= True if full_text.startswith("RT") else False

    is_tweet:bool=True if not(is_comment or is_retweet) else False

    logger.debug("[GET_TWEET_DETAILS] TWEET SUCCESSFULLY PARSED")
    return Tweet(full_text, tweet_id, is_comment, is_retweet,is_tweet)