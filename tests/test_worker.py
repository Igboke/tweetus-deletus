import pytest
import os

from unittest.mock import patch
from src.worker import Worker, RateLimitException, ServiceUnavailableException

def test_genai_response(tweet, worker):
    with patch.object(worker.analyzer, 'analyze_tweet', return_value="NO Content does not exist") as mock_analyze:
        response = worker.analyze_tweet(tweet, ["gore", "rape"])
        
        assert "NO" in response
        mock_analyze.assert_called_once()

def test_worker_reason(valid_reason,worker):
    reason = worker.get_reason(valid_reason)
    assert reason == "Content does not exist. It is analyzed safe"

def test_invalid_reason(invalid_reason,worker):
    with pytest.raises(Exception) as e:
        reason = worker.get_reason(invalid_reason)
    assert "CANNOT GET REASON" in str(e.value)
    assert "INVALID RESPONSE FORMAT" in str(e.value.__cause__)
    

