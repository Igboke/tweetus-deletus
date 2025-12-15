import pytest

def test_open_file(loader,sample_tweet_archive_doc, sample_tweet_archive_content):
    content = loader.read_file(sample_tweet_archive_doc)
    
    assert content == sample_tweet_archive_content

def test_open_file_raises_error(loader,sample_tweet_archive_doc_bad_encoding):
    with pytest.raises(Exception) as e:
        loader.read_file(sample_tweet_archive_doc_bad_encoding)

    assert "UNABLE TO OPEN TWEETS FILE" in str(e.value)

def test_convert_rawdata_to_python_object(loader,sample_tweet_archive_doc,sample_tweet_archive_content):
    content = loader.read_file(sample_tweet_archive_doc)
    raw_data = loader.convert_rawdata_to_python_object(content)

    assert isinstance(raw_data, list)
    assert content == sample_tweet_archive_content
    assert len(raw_data) == 2

def test_convert_rawdata_to_python_object_raises_error(loader,sample_bad_tweet_archive_content):
    with pytest.raises(Exception) as e:
        loader.convert_rawdata_to_python_object(sample_bad_tweet_archive_content)

    assert "INVALID JSON STRUCTURE" in str(e.value)

