import sys
import os
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import convert_rawdata_to_python_object, open_file
from tweets import get_tweet_details, Tweet

def test_open_file(sample_tweet_archive_doc, sample_tweet_archive_content):
    content = open_file(sample_tweet_archive_doc)
    
    assert content == sample_tweet_archive_content

def test_open_file_raises_error(sample_tweet_archive_doc_bad_encoding):
    with pytest.raises(Exception) as exc_info:
        open_file(sample_tweet_archive_doc_bad_encoding)

    assert "CANNOT OPEN FILE" in str(exc_info.value)

def test_convert_rawdata_to_python_object(sample_tweet_archive_doc,sample_tweet_archive_content):
    content = open_file(sample_tweet_archive_doc)
    raw_data = convert_rawdata_to_python_object(content)

    assert isinstance(raw_data, list)
    assert content == sample_tweet_archive_content
    assert len(raw_data) == 2

def test_convert_rawdata_to_python_object_raises_error(sample_bad_tweet_archive_content):
    with pytest.raises(Exception) as exc_info:
        convert_rawdata_to_python_object(sample_bad_tweet_archive_content)

    assert "JSON DECODE ERROR" in str(exc_info.value)

def test_get_tweet_details(sample_tweet_archive_doc):
    content = open_file(sample_tweet_archive_doc)
    raw_data = convert_rawdata_to_python_object(content)
    tweet = raw_data[0].get('tweet')
    details = get_tweet_details(tweet)

    assert isinstance(details, Tweet)

def test_get_tweet_details_raises_error(sample_tweet_archive_doc):
    with pytest.raises(Exception) as exc_info:
        content = open_file(sample_tweet_archive_doc)
        raw_data = convert_rawdata_to_python_object(content)
        details = get_tweet_details(raw_data[0])
    
    assert "NO FULL TEXT FOUND" in str(exc_info.value)

