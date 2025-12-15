import pytest
from unittest.mock import patch
from src.database import TweetStatus

def test_genai_response(tweet, mock_worker):
    mock_worker.analyzer.analyze_tweet.return_value = "NO Content does not exist"
    
    response = mock_worker.analyze_tweet(tweet, ["gore", "rape"])
        
    assert "NO" in response
    mock_worker.analyzer.analyze_tweet.assert_called_once()

def test_worker_reason(valid_reason,mock_worker):
    reason = mock_worker.get_reason(valid_reason)
    assert reason == "Content does not exist. It is analyzed safe"

def test_invalid_reason(invalid_reason,mock_worker):
    with pytest.raises(Exception) as e:
        reason = mock_worker.get_reason(invalid_reason)
    assert "CANNOT GET REASON" in str(e.value)
    assert "INVALID RESPONSE FORMAT" in str(e.value.__cause__)
    
def test_worker_run_success(mock_worker, tweet):
    mock_worker.repo.get_tweet_with_lock.side_effect = [tweet, None]
    mock_worker.analyzer.analyze_tweet.return_value = "YES Dangerous"
    
    with patch("time.sleep"), patch.object(mock_worker, "check_connectivity", return_value=True):
        mock_worker.run([], retry_failed=False)
        mock_worker.repo.update_status.assert_called_once_with(tweet.tweet_id, TweetStatus.ANALYZED_DANGEROUS, "Dangerous")
