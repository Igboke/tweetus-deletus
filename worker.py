import logging
from abc import ABC, abstractmethod
import google.generativeai as genai

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

        response = self.model.generate_content(full_prompt)

        return response.text

class Worker:
    def __init__(self,analyzer:Analyzer):
        self.analyzer = analyzer

    def analyze_tweet(self,tweet:str,content:str)->str:
        try:
            response = self.analyzer.analyze_tweet(tweet,content)
            return response
        except Exception as e:
            logger.error("[ANALYZE_TWEET] ERROR: {e}",exc_info=True)
            raise Exception("CANNOT ANALYZE TWEET") from e
    
    def get_reason(self,response:str)->str:
        try:
            if response.startswith("YES"):
                return response.split("YES")[1].strip()
            else:
                return response.split("NO")[1].strip()
        except Exception as e:
            logger.error("[GET_REASON] ERROR: {e}",exc_info=True)
            raise Exception("CANNOT GET REASON") from e