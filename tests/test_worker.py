import pytest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from worker import Worker

@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="No Gemini API Key found")
def test_genai_response(tweet,worker):
    response = worker.analyze_tweet(tweet,["gore","rape"])
    assert "NO" in response
