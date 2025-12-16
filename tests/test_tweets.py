import pytest
from src.tweets import get_tweet_details, Tweet

def test_get_tweet_details(tweet_dict):
    details = get_tweet_details(tweet_dict)
    assert isinstance(details, Tweet)
    assert details.full_text == tweet_dict.get("full_text")
    assert details.tweet_id == tweet_dict.get("id")

def test_get_tweet_details_raises_error(tweet_dict_no_id):
    with pytest.raises(Exception) as e:
        details = get_tweet_details(tweet_dict_no_id)
    
    assert "NO TWEET ID FOUND" in str(e.value)

def test_is_retweet(tweet_dict):
    details = get_tweet_details(tweet_dict)
    assert isinstance(details, Tweet)
    assert type(tweet_dict.get("full_text")) is str
    assert tweet_dict.get("full_text").startswith("RT")
    assert details.is_retweet == True

def test_is_not_tweet(tweet_dict):
    details = get_tweet_details(tweet_dict) 
    assert details.is_tweet == False
