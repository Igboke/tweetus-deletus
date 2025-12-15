import sqlite3
import os
from src.database import TweetStatus, Tweet


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
    
        









