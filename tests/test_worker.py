import pytest
import os

@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="No Gemini API Key found")
def test_genai_response(tweet,worker):
    response = worker.analyze_tweet(tweet,["gore","rape"])
    assert "NO" in response

@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="No Gemini API Key found")
def test_worker_reason(valid_reason,worker):
    reason = worker.get_reason(valid_reason)
    assert reason == "Content does not exist. It is analyzed safe"

@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="No Gemini API Key found")
def test_invalid_reason(invalid_reason,worker):
    with pytest.raises(Exception) as e:
        reason = worker.get_reason(invalid_reason)
    assert "CANNOT GET REASON" in str(e.value)
    assert "INVALID RESPONSE FORMAT" in str(e.value.__cause__)
    

