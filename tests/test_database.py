import pytest
import sqlite3
import os
from unittest.mock import patch
from src.database import SQLiteTweetRepository, TweetStatus, Tweet
from src.exceptions import DatabaseConnectionError, DatabaseWriteError, DatabaseReadError


def test_db_conftest_creates_db(repo, db_path):
    assert os.path.exists(db_path)

def test_add_tweet(repo, tweet, db_path):
    repo.add_tweet(tweet)
    
    with sqlite3.connect(db_path) as connect:
        connect.row_factory = sqlite3.Row
        cursor = connect.cursor()
        cursor.execute("SELECT * FROM tweets WHERE id=? LIMIT 1", (tweet.tweet_id,))
        row = cursor.fetchone()
    
    assert row is not None
    assert row["id"] == tweet.tweet_id
    assert row["full_text"] == tweet.full_text 
    assert row["status"] == TweetStatus.PENDING.value 
    assert row["is_comment"] == tweet.is_comment
    assert row["is_retweet"] == tweet.is_retweet
    assert row["is_tweet"] == tweet.is_tweet

def test_add_tweet_with_url(repo, tweet, tweet_url, db_path):
    repo.add_tweet(tweet, tweet_url=tweet_url)
    
    with sqlite3.connect(db_path) as connect:
        connect.row_factory = sqlite3.Row
        cursor = connect.cursor()
        cursor.execute("SELECT * FROM tweets WHERE id=? LIMIT 1", (tweet.tweet_id,))
        row = cursor.fetchone()
    
    assert row is not None
    assert row["id"] == tweet.tweet_id
    assert row["full_text"] == tweet.full_text 
    assert row["status"] == TweetStatus.PENDING.value 
    assert row["is_comment"] == tweet.is_comment
    assert row["is_retweet"] == tweet.is_retweet
    assert row["is_tweet"] == tweet.is_tweet
    assert row["tweet_url"] == tweet_url

def test_add_multiple_tweets_with_same_id(repo, tweet, db_path):
    repo.add_tweet(tweet)
    repo.add_tweet(tweet)
    with sqlite3.connect(db_path) as connect:
        cursor = connect.cursor()
        cursor.execute("SELECT COUNT(*) FROM tweets WHERE id=?", (tweet.tweet_id,))
        row = cursor.fetchone()
        count = row[0]

    assert count == 1

def test_get_pending_tweet(repo, tweet, db_path):
    repo.add_tweet(tweet)
    pending_tweet = repo.get_tweet(TweetStatus.PENDING)
    assert pending_tweet is not None
    assert pending_tweet.tweet_id == tweet.tweet_id

def test_get_tweet_that_does_not_exist(repo, tweet, db_path):
    repo.add_tweet(tweet)
    tweet = repo.get_tweet(TweetStatus.FAILED)
    assert tweet is None

def test_get_tweet_with_lock(repo, tweet, db_path):
    repo.add_tweet(tweet)
    tweet = repo.get_tweet_with_lock()
    assert tweet is not None
    assert tweet.tweet_id == tweet.tweet_id
    assert tweet.full_text == tweet.full_text
    
    with sqlite3.connect(db_path) as connect:
        connect.row_factory = sqlite3.Row
        cursor = connect.cursor()
        cursor.execute("SELECT * FROM tweets WHERE id=? LIMIT 1", (tweet.tweet_id,))
        row = cursor.fetchone()
    
    assert row is not None
    assert row["status"] == TweetStatus.PROCESSING.value

def test_initialize_failure(tmp_path):
    repo = SQLiteTweetRepository(str(tmp_path / "test.db"))
    with patch("sqlite3.connect", side_effect=Exception("Connection failed")):
        with pytest.raises(DatabaseConnectionError) as e:
            repo.initialize()
        assert "CANNOT INITIALIZE DB" in str(e.value)

def test_add_tweet_failure(repo, tweet):
    with patch("sqlite3.connect", side_effect=Exception("Insert failed")):
        with pytest.raises(DatabaseWriteError) as e:
            repo.add_tweet(tweet)
        assert "CANNOT ADD TWEET" in str(e.value)

def test_get_tweet_failure(repo):
    with patch("sqlite3.connect", side_effect=Exception("Select failed")):
        with pytest.raises(DatabaseReadError) as e:
            repo.get_tweet(TweetStatus.PENDING)
        assert "ERROR GETTING TWEET" in str(e.value)

def test_update_status_failure(repo):
    with patch("sqlite3.connect", side_effect=Exception("Update failed")):
        with pytest.raises(DatabaseWriteError) as e:
            repo.update_status("123", TweetStatus.FAILED)
        assert "ERROR UPDATING TWEET STATUS" in str(e.value)
    
        









