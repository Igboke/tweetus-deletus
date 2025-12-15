import pytest
import sys
import os
from dotenv import load_dotenv
from unittest.mock import MagicMock


load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database import SQLiteTweetRepository
from src.tweets import Tweet
from src.worker import Worker,GeminiAnalyzer
from src.loader import TweetLoader
from src.reporter import CSVReportGenerator

@pytest.fixture
def sample_tweet_archive_content():
    return r""" window.YTD.tweets.part0 = [ 
    {
    "tweet" : {
      "edit_info" : {
        "initial" : {
          "editTweetIds" : [
            "1997370581860180189"
          ],
          "editableUntil" : "2025-12-06T19:20:30.000Z",
          "editsRemaining" : "5",
          "isEditEligible" : false
        }
      },
      "retweeted" : false,
      "source" : "<a href=\"http://twitter.com/download/android\" rel=\"nofollow\">Twitter for Android</a>",
      "entities" : {
        "hashtags" : [ ],
        "symbols" : [ ],
        "user_mentions" : [
          {
            "name" : "Uncle R",
            "screen_name" : "E",
            "indices" : [
              "0",
              "8"
            ],
            "id_str" : "1468258371",
            "id" : "1468258371"
          }
        ],
        "urls" : [ ]
      },
      "display_text_range" : [
        "0",
        "83"
      ],
      "favorite_count" : "0",
      "in_reply_to_status_id_str" : "19943041994348581220",
      "id_str" : "1997370581860180189",
      "in_reply_to_user_id" : "1468258371",
      "truncated" : false,
      "retweet_count" : "0",
      "id" : "1997370581860180189",
      "in_reply_to_status_id" : "1994041994348581220",
      "created_at" : "Sat Dec 06 18:20:30 +0000 2025",
      "favorited" : false,
      "full_text" : "@E  file were amazing. The American know how to make them.",
      "lang" : "en",
      "in_reply_to_screen_name" : "E",
      "in_reply_to_user_id_str" : "1468258371"
    }
  },
  {
    "tweet" : {
      "edit_info" : {
        "initial" : {
          "editTweetIds" : [
            "1994091455124787464"
          ],
          "editableUntil" : "2025-11-27T18:10:25.986Z",
          "editsRemaining" : "5",
          "isEditEligible" : false
        }
      },
      "retweeted" : false,
      "source" : "<a href=\"http://twitter.com/download/android\" rel=\"nofollow\">Twitter for Android</a>",
      "entities" : {
        "hashtags" : [ ],
        "symbols" : [ ],
        "user_mentions" : [
          {
            "name" : "Alex Hormozi",
            "screen_name" : "AlexHormozi",
            "indices" : [
              "3",
              "15"
            ],
            "id_str" : "1417686048579018753",
            "id" : "1417686048579018753"
          }
        ],
        "urls" : [ ]
      },
      "display_text_range" : [
        "0",
        "140"
      ],
      "favorite_count" : "0",
      "id_str" : "1994091455124787464",
      "truncated" : false,
      "retweet_count" : "0",
      "id" : "1994091455124787464",
      "created_at" : "Thu Nov 22 17:10:25 +1000 2025",
      "favorited" : false,
      "full_text" : "RT @AlexHormozi: Pro tip: If you're afraid to take the risk, write down in excruciating detail what you're actually afraid of having happen…",
      "lang" : "en"
    }
  }]"""

@pytest.fixture
def sample_bad_tweet_archive_content():
    return r""" 
    window.YTD.tweets.part0 = [ 
    {
    "tweet" : {
      "edit_info" : {
        "initial" : {
          "editTweetIds" : [
            "1997370581860180189"
          ],
          "editableUntil" : "2025-12-06T19:20:30.000Z",
          "editsRemaining" : "5",
          "isEditEligible" : false
        }
      },
      "retweeted" : false,
      "source" : "<a href=\"http://twitter.com/download/android\" rel=\"nofollow\">Twitter for Android</a>",
      "entities" : {
        "hashtags" : [ ],
        "symbols" : [ ],
        "user_mentions" : [
          {
            "name" : "Uncle Ruckus",
            "screen_name" : "Emarged",
            "indices" : [
              "0",
              "8"
            ],
            "id_str" : "146825871",
            "id" : "146825871"
          }
        ],
        "urls" : [ ]
      },
      "display_text_range" : [
        "0",
        "83"
      ],
      "favorite_count" : "0",
      "in_reply_to_status_id_str" : "1994041994348581220",
      "id_str" : "1997370581860180189",
      "in_reply_to_user_id" : "146825871",
      "truncated" : false,
      "retweet_count" : "0",
      "id" : "1997370581860180189",
      "in_reply_to_status_id" : "1994041994348581220",
      "created_at" : "Sat Dec 06 18:20:30 +0000 2025",
      "favorited" : false,
      "full_text" : "@Emarged The Capture, Ipcress file were amazing. The British know how to make them.",
      "lang" : "en",
      "in_reply_to_screen_name" : "Emarged",
      "in_reply_to_user_id_str" : "146825871"
    }
  }"""


@pytest.fixture
def sample_tweet_archive_doc(tmp_path,sample_tweet_archive_content):
    tweet_file_path = tmp_path/"tweets.js"
    tweet_file_path.write_text(sample_tweet_archive_content,encoding='utf-8')
    return tweet_file_path

@pytest.fixture
def sample_tweet_archive_doc_bad_encoding(tmp_path,sample_tweet_archive_content):
    tweet_file_path = tmp_path/"tweets.js"
    tweet_file_path.write_text(sample_tweet_archive_content,encoding='utf-16')
    return tweet_file_path

@pytest.fixture
def sample_tweet_archive_doc_bad_json(tmp_path,sample_bad_tweet_archive_content):
    tweet_file_path = tmp_path/"tweets.js"
    tweet_file_path.write_text(sample_bad_tweet_archive_content,encoding='utf-8')
    return tweet_file_path

@pytest.fixture
def db_path(tmp_path):
  db_path = tmp_path / "test_tweet.db"
  return str(db_path)

@pytest.fixture
def repo(db_path):
    repo = SQLiteTweetRepository(db_path)
    repo.initialize()
    return repo

@pytest.fixture
def tweet():
  return Tweet(
        tweet_id="1234567890",
        full_text="This is a test tweet",
        is_comment=False,
        is_retweet=False,
        is_tweet=True,
    )

@pytest.fixture
def tweet_url(tweet):
  tweet_url = tweet.tweet_url % "test_handle"
  return tweet_url

@pytest.fixture
def mock_worker(mock_repo):
    mock_analyzer = MagicMock()
    return Worker(mock_analyzer, mock_repo)

@pytest.fixture
def loader(repo):
  return TweetLoader(repo, "test_handle")

@pytest.fixture
def mock_loader(mock_repo):
    return TweetLoader(mock_repo, "test_handle")

@pytest.fixture
def tweet_dict():
  return {
      "edit_info" : {
        "initial" : {
          "editTweetIds" : [
            "1994091455124787464"
          ],
          "editableUntil" : "2025-11-27T18:10:25.986Z",
          "editsRemaining" : "5",
          "isEditEligible" : False
        }
      },
      "retweeted" : False,
      "source" : r"<a href=\"http://twitter.com/download/android\" rel=\"nofollow\">Twitter for Android</a>",
      "entities" : {
        "hashtags" : [ ],
        "symbols" : [ ],
        "user_mentions" : [
          {
            "name" : "Alex Hormozi",
            "screen_name" : "AlexHormozi",
            "indices" : [
              "3",
              "15"
            ],
            "id_str" : "1417686048579018753",
            "id" : "1417686048579018753"
          }
        ],
        "urls" : [ ]
      },
      "display_text_range" : [
        "0",
        "140"
      ],
      "favorite_count" : "0",
      "id_str" : "1994091455124787464",
      "truncated" : False,
      "retweet_count" : "0",
      "id" : "1994091455124787464",
      "created_at" : "Thu Nov 22 17:10:25 +1000 2025",
      "favorited" : False,
      "full_text" : "RT @AlexHormozi: Pro tip: If you're afraid to take the risk, write down in excruciating detail what you're actually afraid of having happen…",
      "lang" : "en"
    }

@pytest.fixture
def tweet_dict_no_id():
  return {
      "edit_info" : {
        "initial" : {
          "editTweetIds" : [
            "1994091455124787464"
          ],
          "editableUntil" : "2025-11-27T18:10:25.986Z",
          "editsRemaining" : "5",
          "isEditEligible" : False
        }
      },
      "retweeted" : False,
      "source" : r"<a href=\"http://twitter.com/download/android\" rel=\"nofollow\">Twitter for Android</a>",
      "entities" : {
        "hashtags" : [ ],
        "symbols" : [ ],
        "user_mentions" : [
          {
            "name" : "Alex Hormozi",
            "screen_name" : "AlexHormozi",
            "indices" : [
              "3",
              "15"
            ],
            "id_str" : "1417686048579018753",
            "id" : "1417686048579018753"
          }
        ],
        "urls" : [ ]
      },
      "display_text_range" : [
        "0",
        "140"
      ],
      "favorite_count" : "0",
      "id_str" : "1994091455124787464",
      "truncated" : False,
      "retweet_count" : "0",
      "created_at" : "Thu Nov 22 17:10:25 +1000 2025",
      "favorited" : False,
      "full_text" : "RT @AlexHormozi: Pro tip: If you're afraid to take the risk, write down in excruciating detail what you're actually afraid of having happen…",
      "lang" : "en"
    }

@pytest.fixture
def tweet_dictionary_with_key():
  return   [
    {"tweet" : {
      "edit_info" : {
        "initial" : {
          "editTweetIds" : [
            "1997370581860180189"
          ],
          "editableUntil" : "2025-12-06T19:20:30.000Z",
          "editsRemaining" : "5",
          "isEditEligible" : False
        }
      },
      "retweeted" : False,
      "source" : r"<a href=\"http://twitter.com/download/android\" rel=\"nofollow\">Twitter for Android</a>",
      "entities" : {
        "hashtags" : [ ],
        "symbols" : [ ],
        "user_mentions" : [
          {
            "name" : "Uncle R",
            "screen_name" : "E",
            "indices" : [
              "0",
              "8"
            ],
            "id_str" : "1468258371",
            "id" : "1468258371"
          }
        ],
        "urls" : [ ]
      },
      "display_text_range" : [
        "0",
        "83"
      ],
      "favorite_count" : "0",
      "in_reply_to_status_id_str" : "19943041994348581220",
      "id_str" : "1997370581860180189",
      "in_reply_to_user_id" : "1468258371",
      "truncated" : False,
      "retweet_count" : "0",
      "in_reply_to_status_id" : "1994041994348581220",
      "created_at" : "Sat Dec 06 18:20:30 +0000 2025",
      "favorited" : False,
      "full_text" : "@E  file were amazing. The American know how to make them.",
      "lang" : "en",
      "in_reply_to_screen_name" : "E",
      "in_reply_to_user_id_str" : "1468258371"
    }},
    {"tweet" : {
      "edit_info" : {
        "initial" : {
          "editTweetIds" : [
            "1994091455124787464"
          ],
          "editableUntil" : "2025-11-27T18:10:25.986Z",
          "editsRemaining" : "5",
          "isEditEligible" : False
        }
      },
      "retweeted" : False,
      "source" : r"<a href=\"http://twitter.com/download/android\" rel=\"nofollow\">Twitter for Android</a>",
      "entities" : {
        "hashtags" : [ ],
        "symbols" : [ ],
        "user_mentions" : [
          {
            "name" : "Alex Hormozi",
            "screen_name" : "AlexHormozi",
            "indices" : [
              "3",
              "15"
            ],
            "id_str" : "1417686048579018753",
            "id" : "1417686048579018753"
          }
        ],
        "urls" : [ ]
      },
      "display_text_range" : [
        "0",
        "140"
      ],
      "favorite_count" : "0",
      "id_str" : "1994091455124787464",
      "truncated" : False,
      "retweet_count" : "0",
      "id" : "1994091455124787464",
      "created_at" : "Thu Nov 22 17:10:25 +1000 2025",
      "favorited" : False,
      "full_text" : "RT @AlexHormozi: Pro tip: If you're afraid to take the risk, write down in excruciating detail what you're actually afraid of having happen…",
      "lang" : "en"
    }}
  ]


@pytest.fixture
def valid_reason():
  return "NO Content does not exist. It is analyzed safe"

@pytest.fixture
def invalid_reason():
  return "MAYBE Content does not exist. It is analyzed safe or not"

@pytest.fixture
def mock_repo():
    return MagicMock()

@pytest.fixture
def generator(mock_repo):
    return CSVReportGenerator(mock_repo)