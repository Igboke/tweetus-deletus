import sys
import os
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tweets import get_tweet_details, Tweet

def test_open_file(loader,sample_tweet_archive_doc, sample_tweet_archive_content):
    content = loader.read_file(sample_tweet_archive_doc)
    
    assert content == sample_tweet_archive_content

def test_open_file_raises_error(loader,sample_tweet_archive_doc_bad_encoding):
    with pytest.raises(Exception) as exc_info:
        loader.read_file(sample_tweet_archive_doc_bad_encoding)

    assert "UNABLE TO OPEN TWEETS FILE" in str(exc_info.value)

def test_convert_rawdata_to_python_object(loader,sample_tweet_archive_doc,sample_tweet_archive_content):
    content = loader.read_file(sample_tweet_archive_doc)
    raw_data = loader.convert_rawdata_to_python_object(content)

    assert isinstance(raw_data, list)
    assert content == sample_tweet_archive_content
    assert len(raw_data) == 2

def test_convert_rawdata_to_python_object_raises_error(loader,sample_bad_tweet_archive_content):
    with pytest.raises(Exception) as exc_info:
        loader.convert_rawdata_to_python_object(sample_bad_tweet_archive_content)

    assert "INVALID JSON STRUCTURE" in str(exc_info.value)

def test_get_tweet_details(loader,sample_tweet_archive_doc):
    content = loader.read_file(sample_tweet_archive_doc)
    raw_data = loader.convert_rawdata_to_python_object(content)
    tweet = raw_data[0].get('tweet')
    details = get_tweet_details(tweet)

    assert isinstance(details, Tweet)

def test_get_tweet_details_raises_error(loader,sample_tweet_archive_doc):
    with pytest.raises(Exception) as exc_info:
        content = loader.read_file(sample_tweet_archive_doc)
        raw_data = loader.convert_rawdata_to_python_object(content)
        details = get_tweet_details(raw_data[0])
    
    assert "NO FULL TEXT FOUND" in str(exc_info.value)

