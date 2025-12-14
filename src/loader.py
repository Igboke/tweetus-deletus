import json
import logging
from src.database import init_db, add_tweet
from src.tweets import get_tweet_details
from src.exceptions import LoaderError, FileReadError, DataParseError

logger = logging.getLogger(__name__)

class TweetLoader:
    def __init__(self, db_name: str, x_handle: str):
        self.db_name = db_name
        self.x_handle = x_handle

    def run(self, file_path: str) -> None:
        try:
            init_db(self.db_name)
            
            raw_data = self.read_file(file_path)
            tweets = self.convert_rawdata_to_python_object(raw_data)
            
            self.load_into_db(tweets)
            
        except (FileReadError, DataParseError) as e:
             logger.error(f"[RUN] CRITICAL LOADER ERROR: {e}")
             raise e
        except Exception as e:
             logger.error(f"[RUN] UNEXPECTED ERROR: {e}", exc_info=True)
             raise LoaderError("UNEXPECTED LOADER FAILURE") from e

    def read_file(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as tweet_doc:
                raw_data = tweet_doc.read()
                logger.debug("[READ_FILE] FILE SUCCESSFULLY PARSED")
                return raw_data
        except Exception as e:
            logger.error(f"[READ_FILE] ERROR: {e}", exc_info=True)
            raise FileReadError("UNABLE TO OPEN TWEETS FILE") from e

    def convert_rawdata_to_python_object(self, raw_data: str) -> list:
        start_index = raw_data.find('[')
        if start_index == -1:
            logger.error("[CONVERT_RAWDATA_TO_PYTHON_OBJECT] JSON NOT FOUND")
            raise DataParseError("VALID JSON ARRAY START '[' NOT FOUND")

        json_payload = raw_data[start_index:]
        try:
            return json.loads(json_payload)
        except json.JSONDecodeError as e:
            logger.error("[CONVERT_RAWDATA_TO_PYTHON_OBJECT] JSON DECODE ERROR", exc_info=True)
            raise DataParseError("INVALID JSON STRUCTURE") from e

    def load_into_db(self, tweets: list) -> None:
        success_count = 0
        fail_count = 0
        for tweet in tweets:
            item = tweet.get('tweet')
            if item is None:
                logger.warning("[LOAD_INTO_DB] SKIPPING: ITEM HAS NO 'TWEET' KEY")
                fail_count += 1
                continue 

            try:
                details = get_tweet_details(item)
                tweet_url = details.tweet_url % self.x_handle
                add_tweet(details, tweet_url, self.db_name)
                success_count += 1
            except Exception as e:
                logger.error(f"[LOAD_INTO_DB] FAILED TO IMPORT TWEET: {e}", exc_info=True)
                fail_count += 1
                continue 
        
        logger.info(f"[LOAD_INTO_DB] COMPLETED: {success_count} SUCCESS, {fail_count} FAILED")
