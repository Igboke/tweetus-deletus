import sqlite3
import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database import init_db, add_tweet, TweetStatus, get_tweet, get_tweet_with_lock


def test_db_conftest_creates_db(db_path):
    assert os.path.exists(db_path)

def test_add_tweet(tweet,db_path):
    add_tweet(tweet,db_name=db_path)
    
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

def test_add_tweet_with_url(tweet,tweet_url,db_path):
    add_tweet(tweet,tweet_url=tweet_url,db_name=db_path)
    
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

def test_add_multiple_tweets_with_same_id(tweet,db_path):
    add_tweet(tweet,db_name=db_path)
    add_tweet(tweet,db_name=db_path)
    with sqlite3.connect(db_path) as connect:
        cursor = connect.cursor()
        cursor.execute("SELECT COUNT(*) FROM tweets WHERE id=?", (tweet.tweet_id,))
        row = cursor.fetchone()
        count = row[0]

    assert count == 1

def test_get_pending_tweet(tweet,db_path):
    add_tweet(tweet,db_name=db_path)
    pending_tweet = get_tweet(TweetStatus.PENDING,db_name=db_path)
    assert pending_tweet is not None
    assert pending_tweet.tweet_id == tweet.tweet_id

def test_get_tweet_that_does_not_exist(tweet,db_path):
    add_tweet(tweet,db_name=db_path)
    tweet = get_tweet(TweetStatus.FAILED,db_name=db_path)
    assert tweet is None

def test_get_tweet_with_lock(tweet,db_path):
    add_tweet(tweet,db_name=db_path)
    tweet = get_tweet_with_lock(db_name=db_path)
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
    
        









