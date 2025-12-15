import csv
import logging
from abc import ABC, abstractmethod
from src.database import TweetStatus, TweetRepository
from src.exceptions import DatabaseReadError

logger = logging.getLogger(__name__)

class ReportGenerator(ABC):
    def __init__(self, repo: TweetRepository):
        self.repo = repo

    @abstractmethod
    def generate(self, status: TweetStatus, output_path: str) -> None:
        pass

class CSVReportGenerator(ReportGenerator):
    def generate(self, status: TweetStatus, output_path: str) -> None:
        try:
            tweets = self.repo.get_reports(status)
            
            if not tweets:
                logger.info(f"[GENERATE] NO TWEETS FOUND WITH STATUS {status.value} TO REPORT")
                return

            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['tweet_id', 'status', 'analysis_reason', 'tweet_url', 'retry_count', 'full_text']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for tweet in tweets:
                    writer.writerow({
                        'tweet_id': tweet.tweet_id,
                        'status': tweet.status,
                        'analysis_reason': tweet.analysis_reason,
                        'tweet_url': tweet.tweet_url,
                        'retry_count': tweet.retry_count,
                        'full_text': tweet.full_text
                    })
                    
            logger.info(f"[GENERATE] REPORT GENERATED AT {output_path} WITH {len(tweets)} TWEETS.")
            
        except DatabaseReadError as e:
            logger.error(f"[GENERATE] ERROR: {e}", exc_info=True)
            raise Exception("ERROR READING FROM DATABASE") from e
        except Exception as e:
            logger.error(f"[GENERATE] ERROR: {e}", exc_info=True)
            raise Exception("REPORT GENERATION FAILED") from e
