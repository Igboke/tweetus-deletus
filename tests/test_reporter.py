import pytest
import csv
from src.database import TweetStatus, TweetReport
from src.exceptions import DatabaseReadError

def test_generate_report_success(mock_repo, generator, tmp_path):
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
    
    output_file = tmp_path / "report.csv"
    generator.generate(TweetStatus.ANALYZED_DANGEROUS, str(output_file))
    
    mock_repo.get_reports.assert_called_once_with(TweetStatus.ANALYZED_DANGEROUS)
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]['tweet_id'] == "19394939424"
        assert rows[1]['analysis_reason'] == "Hate speech"

def test_generate_report_empty(mock_repo, generator, tmp_path):
    mock_repo.get_reports.return_value = []
    
    output_file = tmp_path / "report_emptyfile.csv"
    generator.generate(TweetStatus.FAILED, str(output_file))
    
    mock_repo.get_reports.assert_called_once_with(TweetStatus.FAILED)
    assert not output_file.exists()

def test_generate_report_db_error(mock_repo, generator, tmp_path):
    mock_repo.get_reports.side_effect = DatabaseReadError("DB Fail")
    
    output_file = tmp_path / "report_errorfile.csv"
    with pytest.raises(Exception) as e:
        generator.generate(TweetStatus.PENDING, str(output_file))
    
    assert "REPORT GENERATION FAILED" in str(e.value)
