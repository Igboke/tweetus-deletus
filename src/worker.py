import logging
import time
from abc import ABC, abstractmethod
import google.generativeai as genai
from google.api_core import exceptions
from src.database import get_tweet_with_lock, update_tweet_status, mark_tweet_as_failed, TweetStatus
from src.exceptions import RateLimitException, ServiceUnavailableException 
logger = logging.getLogger(__name__)

class Analyzer(ABC):

    def prompt(self)->str:
        return """
        You are a content moderator. 
        Your task is to analyze the following tweet and decide if it contains the following content 
        
        Reply strictly with 'YES' if it contains any of the following content, and 'NO' if it does not.
        Add Analysis reason, in maximum 2 sentences.
        """

    @abstractmethod
    def analyze_tweet(self,tweet:str,content:str)->str:
        pass

class GeminiAnalyzer(Analyzer):
    
    def __init__(self,api_key,model):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def analyze_tweet(self,tweet:str,content:str)->str:
        full_prompt = f"{self.prompt()}\n\nTWEET: {tweet}\n\nCONTENT: {content}"

        try:
            response = self.model.generate_content(full_prompt)
        except exceptions.TooManyRequests as e:
            logger.error("[ANALYZE_TWEET] RATE LIMIT EXCEEDED")
            raise RateLimitException("RATE LIMIT EXCEEDED") from e
        except exceptions.ServiceUnavailable as e:
            logger.error("[ANALYZE_TWEET] SERVICE UNAVAILABLE")
            raise ServiceUnavailableException("SERVICE UNAVAILABLE") from e
        except Exception as e:
            logger.error("[ANALYZE_TWEET] ERROR: {e}",exc_info=True)
            raise Exception("ANALYZER ERROR") from e

        return response.text

class Worker:
    def __init__(self,analyzer:Analyzer,db_name:str):
        self.analyzer = analyzer
        self.db_name = db_name

    def analyze_tweet(self,tweet:str,content:str)->str:
        try:
            response = self.analyzer.analyze_tweet(tweet,content)
            logger.info("[ANALYZE_TWEET] TWEET ANALYZED")
            return response
        except (RateLimitException, ServiceUnavailableException) as e:
            logger.error("[ANALYZE_TWEET] ERROR: {e}",exc_info=True)
            raise e
        except Exception as e:
            logger.error("[ANALYZE_TWEET] ERROR: {e}",exc_info=True)
            raise Exception("CANNOT ANALYZE TWEET") from e
    
    def get_reason(self,response:str)->str:
        try:
            if response.startswith("YES"):
                logger.info("[GET_REASON] REASON RETRIEVED")
                return response.split("YES")[1].strip()
            else:
                logger.info("[GET_REASON] REASON RETRIEVED")
                return response.split("NO")[1].strip()
        except Exception as e:
            logger.error("[GET_REASON] ERROR: {e}",exc_info=True)
            raise Exception("CANNOT GET REASON") from e

    def run(self, forbidden_words:list, retry_failed:bool=False)->None:
        logger.info(f"[RUN] Starting worker logic for DB: {self.db_name}")
        count = 0
        while True:
            tweet = None

            if count > 3:
                logger.info("[RUN] REACHED MAX COUNT FOR RETRIES. EXITING \nCHECK API FOR RATE LIMITS")
                break
            
            try:
                if retry_failed:
                    tweet = get_tweet_with_lock(TweetStatus.FAILED, db_name=self.db_name)
                else:
                    tweet = get_tweet_with_lock(db_name=self.db_name)

                if tweet is None:
                    logger.info("[RUN] NO PENDING TWEET FOUND")
                    break

                response = self.analyze_tweet(tweet.full_text, forbidden_words)
                reason = self.get_reason(response)

                if response.startswith("YES"):
                    update_tweet_status(tweet.tweet_id, TweetStatus.ANALYZED_DANGEROUS, reason, db_name=self.db_name)
                elif response.startswith("NO"):
                    update_tweet_status(tweet.tweet_id, TweetStatus.ANALYZED_SAFE, reason, db_name=self.db_name)
                else:
                    update_tweet_status(tweet.tweet_id, TweetStatus.FAILED, reason, db_name=self.db_name)

                logger.info("[RUN] TWEET ANALYZED")
                count = 0
                time.sleep(15) 

            except RateLimitException:
                logger.warning("[RUN] RATE LIMIT HIT. SLEEPING FOR 60s")
                if tweet:
                    mark_tweet_as_failed(tweet.tweet_id, "Rate Limit Hit", db_name=self.db_name)
                count += 1
                time.sleep(60)
                
            except ServiceUnavailableException:
                logger.warning("[RUN] SERVICE UNAVAILABLE. SLEEPING FOR 30s")
                if tweet:
                    mark_tweet_as_failed(tweet.tweet_id, "Service Unavailable", db_name=self.db_name)
                count += 1
                time.sleep(30)

            except KeyboardInterrupt:
                logger.info("[RUN] INTERRUPTED")
                if tweet:
                    mark_tweet_as_failed(tweet.tweet_id, "Interrupted by User", db_name=self.db_name)
                break

            except Exception as e:
                logger.error(f"[RUN] ERROR: {e}", exc_info=True)
                if tweet:
                    mark_tweet_as_failed(tweet.tweet_id, str(e), db_name=self.db_name)
                count += 1
                time.sleep(17)