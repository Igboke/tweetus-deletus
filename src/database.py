import sqlite3
import logging
from abc import ABC, abstractmethod
from enum import Enum
from src.tweets import Tweet, TweetReport

logger = logging.getLogger(__name__)

class TweetStatus(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    ANALYZED_SAFE = "ANALYZED_SAFE"
    ANALYZED_DANGEROUS = "ANALYZED_DANGEROUS"
    FAILED = "FAILED"

class TweetRepository(ABC):
    @abstractmethod
    def initialize(self) -> None:
        pass

    @abstractmethod
    def add_tweet(self, tweet: Tweet, tweet_url: str = "") -> None:
        pass

    @abstractmethod
    def get_tweet(self, status: TweetStatus) -> Tweet | None:
        pass
    
    @abstractmethod
    def get_tweet_with_lock(self, status: TweetStatus = TweetStatus.PENDING) -> Tweet | None:
        pass

    @abstractmethod
    def update_status(self, tweet_id: str, status: TweetStatus, reason: str = "") -> bool:
        pass

    @abstractmethod
    def mark_failed(self, tweet_id: str, reason: str) -> bool:
        pass

    @abstractmethod
    def get_reports(self, status: TweetStatus) -> list[TweetReport]:
        pass

class SQLiteTweetRepository(TweetRepository):
    CREATE_TABLE_QUERY = """
    CREATE TABLE IF NOT EXISTS tweets (
        id TEXT PRIMARY KEY,
        full_text TEXT,
        status TEXT DEFAULT 'PENDING'
        CHECK(status IN ('PENDING', 'PROCESSING', 'ANALYZED_SAFE', 'ANALYZED_DANGEROUS', 'FAILED')),
        retry_count INTEGER DEFAULT 0,
        analysis_reason TEXT,
        tweet_url TEXT,
        is_comment BOOLEAN,
        is_retweet BOOLEAN,
        is_tweet BOOLEAN,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    def initialize(self) -> None:
        try:
            with sqlite3.connect(self.db_path) as connect:
                cursor = connect.cursor()
                cursor.execute(self.CREATE_TABLE_QUERY)
        except Exception as e:
            logger.error(f"[INITIALIZE] ERROR: {e}", exc_info=True)
            raise Exception("CANNOT INITIALIZE DB") from e

    def add_tweet(self, tweet: Tweet, tweet_url: str = "") -> None:
        try:
            with sqlite3.connect(self.db_path) as connect:
                cursor = connect.cursor()
                cursor.execute("""INSERT OR IGNORE INTO tweets 
                (id,full_text,is_comment,is_retweet,is_tweet,tweet_url) 
                VALUES (?,?,?,?,?,?)""",
                (tweet.tweet_id, tweet.full_text, tweet.is_comment, tweet.is_retweet, tweet.is_tweet, tweet_url)
                )

                if cursor.rowcount == 0:
                    logger.error("[ADD_TWEET] ERROR: TWEET ALREADY EXISTS")

                logger.info("[ADD_TWEET] TWEET ADDED")

        except Exception as e:
            logger.error(f"[ADD_TWEET] ERROR: {e}", exc_info=True)
            raise Exception("CANNOT ADD TWEET") from e

    def get_tweet(self, status: TweetStatus) -> Tweet | None:
        try:
            with sqlite3.connect(self.db_path) as connect:
                connect.row_factory = sqlite3.Row
                cursor = connect.cursor()
                cursor.execute("SELECT * FROM tweets WHERE status = ? LIMIT 1", (status.value,))
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
            logger.error(f"[GET_TWEET] ERROR: {e}", exc_info=True)
            raise Exception("ERROR GETTING TWEET") from e

    def update_status(self, tweet_id: str, status: TweetStatus, reason: str = "") -> bool:
        try:
            with sqlite3.connect(self.db_path) as connect:
                cursor = connect.cursor()
                cursor.execute("UPDATE tweets SET status = ?, updated_at = CURRENT_TIMESTAMP, analysis_reason = ? WHERE id = ?", (status.value, reason, tweet_id))

                if cursor.rowcount == 0:
                    logger.error("[UPDATE_STATUS] ERROR: TWEET NOT FOUND")
                    return False

                logger.info(f"[UPDATE_STATUS] TWEET STATUS UPDATED TO {status.value}")
                return True

        except Exception as e:
            logger.error(f"[UPDATE_STATUS] ERROR: {e}", exc_info=True)
            raise Exception("ERROR UPDATING TWEET STATUS") from e

    def get_tweet_with_lock(self, status: TweetStatus = TweetStatus.PENDING) -> Tweet | None:
        try:
            with sqlite3.connect(self.db_path) as connect:
                connect.row_factory = sqlite3.Row
                connect.execute("BEGIN EXCLUSIVE") 
                cursor = connect.cursor()

                if status == TweetStatus.FAILED:
                    cursor.execute("SELECT * FROM tweets WHERE status = 'FAILED' AND retry_count < 3 LIMIT 1")
                else:
                    cursor.execute("SELECT * FROM tweets WHERE status = ? LIMIT 1", (status.value,))
                row = cursor.fetchone()

                if row is None:
                    logger.info(f"[GET_TWEET_WITH_LOCK] NO {status.value} TWEET FOUND")
                    connect.rollback()
                    return None
                
                logger.info("[GET_TWEET_WITH_LOCK] TWEET SUCCESSFULLY FETCHED")
                
                tweet_id = row["id"]

                cursor.execute("UPDATE tweets SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (TweetStatus.PROCESSING.value, tweet_id))
                logger.info("[GET_TWEET_WITH_LOCK] TWEET STATUS UPDATED TO PROCESSING")

                return Tweet(
                    tweet_id=row["id"],
                    full_text=row["full_text"],
                    is_comment=row["is_comment"],
                    is_retweet=row["is_retweet"],
                    is_tweet=row["is_tweet"],
                )

        except Exception as e:
            logger.error(f"[GET_TWEET_WITH_LOCK] ERROR: {e}", exc_info=True)
            raise Exception("ERROR GETTING TWEET WITH LOCK") from e

    def mark_failed(self, tweet_id: str, reason: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as connect:
                cursor = connect.cursor()
                cursor.execute("""UPDATE tweets SET status = ?, 
                retry_count = retry_count + 1, analysis_reason = ?, 
                updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
                (TweetStatus.FAILED.value, reason, tweet_id))

                if cursor.rowcount == 0:
                    logger.error("[MARK_FAILED] ERROR: TWEET NOT FOUND")
                    return False

                logger.info("[MARK_FAILED] TWEET MARKED AS FAILED")
                return True

        except Exception as e:
            logger.error(f"[MARK_FAILED] ERROR: {e}", exc_info=True)
            raise Exception("ERROR MARKING TWEET AS FAILED") from e

    def get_reports(self, status: TweetStatus) -> list[TweetReport]:
        try:
            with sqlite3.connect(self.db_path) as connect:
                connect.row_factory = sqlite3.Row
                cursor = connect.cursor()
                
                cursor.execute("SELECT * FROM tweets WHERE status = ?", (status.value,))
                rows = cursor.fetchall()
                
                if not rows:
                    logger.info(f"[GET_REPORTS] NO TWEETS FOUND WITH STATUS {status.value}")
                    return []
                    
                reports = []
                for row in rows:
                    reports.append(TweetReport(
                        tweet_id=row["id"],
                        full_text=row["full_text"],
                        status=row["status"],
                        analysis_reason=row["analysis_reason"] or "",
                        tweet_url=row["tweet_url"] or "",             
                        retry_count=row["retry_count"],
                        is_comment=bool(row["is_comment"]),
                        is_retweet=bool(row["is_retweet"]),
                        is_tweet=bool(row["is_tweet"])
                    ))
                
                logger.info(f"[GET_REPORTS] FETCHED {len(reports)} REPORTS")
                return reports
                
        except Exception as e:
            logger.error(f"[GET_REPORTS] ERROR: {e}", exc_info=True)
            raise Exception("ERROR GETTING TWEET REPORTS") from e
