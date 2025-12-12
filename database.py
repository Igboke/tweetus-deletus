import sqlite3
import logging
from enum import Enum
from tweets import Tweet

logger = logging.getLogger(__name__)
DB_NAME = "tweets.db"

class TweetStatus(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    ANALYZED_SAFE = "ANALYZED_SAFE"
    ANALYZED_DANGEROUS = "ANALYZED_DANGEROUS"
    FAILED = "FAILED"

CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS tweets (
    id TEXT PRIMARY KEY,
    full_text TEXT,
    status TEXT DEFAULT 'PENDING'
    CHECK(status IN ('PENDING', 'PROCESSING', 'ANALYZED_SAFE', 'ANALYZED_DANGEROUS', 'FAILED')),
    retry_count INTEGER DEFAULT 0,
    analysis_reason TEXT,
    is_comment BOOLEAN,
    is_retweet BOOLEAN,
    is_tweet BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

def init_db(db_name=DB_NAME):
    try:
        with sqlite3.connect(db_name) as connect:
            cursor = connect.cursor()
            cursor.execute(CREATE_TABLE_QUERY)
            connect.commit()
    except Exception as e:
        logger.error("[INIT_DB] ERROR: {e}",exc_info=True)
        raise Exception("CANNOT INIT DB") from e

def add_tweet(tweet:Tweet,db_name=DB_NAME):
    try:
        with sqlite3.connect(db_name) as connect:
            cursor = connect.cursor()
            cursor.execute("""INSERT OR IGNORE INTO tweets 
            (id,full_text,is_comment,is_retweet,is_tweet) 
            VALUES (?,?,?,?,?)""",
            (tweet.tweet_id,tweet.full_text,tweet.is_comment,tweet.is_retweet,tweet.is_tweet)
            )
            if cursor.rowcount == 0:
                logger.error("[ADD_TWEET] ERROR: TWEET ALREADY EXISTS")
            logger.debug("[ADD_TWEET] TWEET ADDED")
            connect.commit()
    except Exception as e:
        logger.error("[ADD_TWEET] ERROR: {e}",exc_info=True)
        raise Exception("CANNOT ADD TWEET") from e

def get_tweet(tweet_status:TweetStatus,db_name=DB_NAME):
    """Fetches a tweet from the database based on its Raw Enum status."""
    try:
        with sqlite3.connect(db_name) as connect:
            connect.row_factory = sqlite3.Row
            cursor = connect.cursor()
            cursor.execute("SELECT * FROM tweets WHERE status = ? LIMIT 1",(tweet_status.value,))
            row = cursor.fetchone()

            if row is None:
                logger.info("[GET_TWEET] NO TWEET FOUND")
                return None

            logger.debug("[GET_TWEET] TWEET SUCCESSFULLY FETCHED")

            return Tweet(
                tweet_id=row["id"],
                full_text=row["full_text"],
                is_comment=row["is_comment"],
                is_retweet=row["is_retweet"],
                is_tweet=row["is_tweet"],
            )
            
    except Exception as e:
        logger.error("[GET_TWEET] ERROR: {e}",exc_info=True)
        raise Exception("CANNOT GET TWEET") from e
    