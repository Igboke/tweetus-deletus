import logging
import time
import socket
from abc import ABC, abstractmethod
import google.generativeai as genai
from google.api_core import exceptions
from src.database import TweetStatus, TweetRepository
from src.exceptions import RateLimitException, ServiceUnavailableException, DatabaseError
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
    def __init__(self, analyzer: Analyzer, repo: TweetRepository):
        self.analyzer = analyzer
        self.repo = repo

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
            elif response.startswith("NO"):
                logger.info("[GET_REASON] REASON RETRIEVED")
                return response.split("NO")[1].strip()
            else:
                raise ValueError("INVALID RESPONSE FORMAT")
        except Exception as e:
            logger.error("[GET_REASON] ERROR: {e}",exc_info=True)
            raise Exception("CANNOT GET REASON") from e

    def check_connectivity(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def run(self, forbidden_words:list, retry_failed:bool=False)->None:
        logger.info("[RUN] STARTING WORKER LOGIC")
        
        if not self.check_connectivity():
            logger.critical("[RUN] NO INTERNET CONNECTION. EXITING.")
            return

        count = 0
        while True:
            tweet = None

            if count > 3:
                logger.info("[RUN] REACHED MAX COUNT FOR RETRIES. EXITING \nCHECK API FOR RATE LIMITS")
                break
            
            try:
                if retry_failed:
                    tweet = self.repo.get_tweet_with_lock(TweetStatus.FAILED)
                else:
                    tweet = self.repo.get_tweet_with_lock()

                if tweet is None:
                    logger.info("[RUN] NO PENDING TWEET FOUND")
                    break

                response = self.analyze_tweet(tweet.full_text, forbidden_words)
                reason = self.get_reason(response)

                if response.startswith("YES"):
                    self.repo.update_status(tweet.tweet_id, TweetStatus.ANALYZED_DANGEROUS, reason)
                elif response.startswith("NO"):
                    self.repo.update_status(tweet.tweet_id, TweetStatus.ANALYZED_SAFE, reason)
                else:
                    self.repo.update_status(tweet.tweet_id, TweetStatus.FAILED, reason)

                logger.info("[RUN] TWEET ANALYZED")
                count = 0
                time.sleep(15) 

            except RateLimitException:
                logger.warning("[RUN] RATE LIMIT HIT. SLEEPING FOR 60s")
                if tweet:
                    self.repo.mark_failed(tweet.tweet_id, "Rate Limit Hit")
                count += 1
                time.sleep(60)
                
            except ServiceUnavailableException:
                logger.warning("[RUN] SERVICE UNAVAILABLE. SLEEPING FOR 30s")
                if tweet:
                    self.repo.mark_failed(tweet.tweet_id, "Service Unavailable")
                count += 1
                time.sleep(30)

            except KeyboardInterrupt:
                logger.info("[RUN] INTERRUPTED")
                if tweet:
                    self.repo.mark_failed(tweet.tweet_id, "Interrupted by User")
                break

            except DatabaseError:
                logger.error("[RUN] DATABASE ERROR")
                if tweet:
                    self.repo.mark_failed(tweet.tweet_id, "Database Error")
                time.sleep(17)

            except Exception as e:
                logger.error(f"[RUN] ERROR: {e}", exc_info=True)
                if tweet:
                    self.repo.mark_failed(tweet.tweet_id, str(e))
                count += 1
                time.sleep(17)