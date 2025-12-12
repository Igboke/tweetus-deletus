import logging
from abc import ABC, abstractmethod
import google.generativeai as genai

logger = logging.getLogger(__name__)

class Analyzer(ABC):

    def prompt(self):
        return """
        You are a content moderator. 
        Your task is to analyze the following tweet and decide if it contains the following content 
        
        Reply strictly with 'YES' if it is harmful, and 'NO' if it is safe.
        Add Analysis reason, in maximum 2 sentences.
        """

    @abstractmethod
    def analyze_tweet(self,tweet,content):
        pass

class GeminiAnalyzer(Analyzer):
    
    def __init__(self,api_key,model):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def analyze_tweet(self,tweet,content):
        full_prompt = f"{self.prompt()}\n\nTWEET: {tweet}\n\nCONTENT: {content}"

        response = self.model.generate_content(full_prompt)

        return response.text

class Worker:
    def __init__(self,analyzer:Analyzer):
        self.analyzer = analyzer

    def analyze_tweet(self,tweet,content):
        return self.analyzer.analyze_tweet(tweet,content)