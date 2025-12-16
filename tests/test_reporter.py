import pytest
import csv
from src.database import TweetStatus, TweetReport
from src.exceptions import DatabaseReadError

def test_generate_report_success(mock_repo, generator, output_csv_file):
    mock_reports = [
        TweetReport(
            tweet_id="19394939424", full_text="Safe tweet", status="ANALYZED_SAFE", 
            analysis_reason="Boring", tweet_url="http://x.com/1", retry_count=0,
            is_comment=False, is_retweet=False, is_tweet=True
        ),
        TweetReport(
            tweet_id="2242942929", full_text="Bad tweet", status="ANALYZED_DANGEROUS", 
            analysis_reason="Hate speech", tweet_url="http://x.com/2", retry_count=0,
            is_comment=False, is_retweet=False, is_tweet=True
        )
    ]
    mock_repo.get_reports.return_value = mock_reports
    
    generator.generate(TweetStatus.ANALYZED_DANGEROUS, output_csv_file)
    
    mock_repo.get_reports.assert_called_once_with(TweetStatus.ANALYZED_DANGEROUS)
    assert output_csv_file.exists()
    
    with open(output_csv_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]['tweet_id'] == "19394939424"
        assert rows[1]['analysis_reason'] == "Hate speech"

def test_generate_report_empty(mock_repo, generator, output_csv_file):
    mock_repo.get_reports.return_value = []
    
    generator.generate(TweetStatus.FAILED, output_csv_file)
    
    mock_repo.get_reports.assert_called_once_with(TweetStatus.FAILED)
    assert not output_csv_file.exists()

def test_generate_report_db_error(mock_repo, generator, output_csv_file):
    mock_repo.get_reports.side_effect = DatabaseReadError("ERROR GETTING TWEET REPORTS")
    
    with pytest.raises(Exception) as e:
        generator.generate(TweetStatus.PENDING, output_csv_file)
    
    assert "ERROR READING FROM DATABASE" in str(e.value)
