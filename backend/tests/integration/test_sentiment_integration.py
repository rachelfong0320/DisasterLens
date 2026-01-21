import pytest
import asyncio
import json
import time
from unittest.mock import MagicMock, patch, AsyncMock
from core.jobs import main_sentimentAnalysis
from core.jobs.schemas import SentimentOutput

# ==========================================
# TEST FIXTURES
# ==========================================

@pytest.fixture
def mock_db():
    """Mocks the database connection object."""
    return MagicMock()

@pytest.fixture
def sample_post():
    """Provides a sample raw post for testing."""
    return {
        "postId": "post_123",
        "postText": "FLOOD ALERT: Water rising fast in Klang! Need help immediately.",
        "timestamp": "2023-10-27T10:00:00Z"
    }

@pytest.fixture
def mock_llm_response_content():
    """
    Mocks the JSON content string returned by OpenAI.
    Note: matches schema validation_alias='sentiment' for sentiment_label.
    """
    return json.dumps({
        "sentiment": "Urgent",
        "confidence_score": 0.95,
        "reasoning": "The text indicates immediate danger ('Water rising fast') and a request for help."
    })

# ==========================================
# TEST CASE: IT-06-002
# ==========================================

@pytest.mark.asyncio
async def test_it_06_002_schema_validation(sample_post, mock_llm_response_content):
    """
    Test Case ID: IT-06-002
    Test Scenario: Schema Validation with Unified Models
    Coverage: Model Integration (Pydantic <-> OpenAI JSON Mode)
    """
    # 1. Setup Mock for OpenAI
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content=mock_llm_response_content))
    ]

    # Patch the global 'aclient' in the main_sentimentAnalysis module
    with patch.object(main_sentimentAnalysis, 'aclient') as mock_aclient:
        mock_aclient.chat.completions.create = AsyncMock(return_value=mock_completion)
        
        # 2. Trigger the analysis worker directly
        sem = asyncio.Semaphore(1)
        result = await main_sentimentAnalysis.analyze_sentiment_async(sample_post, sem)

        # 3. Verify Pydantic Parsing & Logic
        assert result is not None, "Worker should return a result dictionary"
        
        # Verify internal Pydantic validation (SentimentOutput.model_validate_json) worked
        # The function returns a dict, so we check if the keys mapped correctly
        assert result["sentiment_label"] == "Urgent"
        assert result["confidence_level"] == 0.95
        assert result["reasoning"] == "The text indicates immediate danger ('Water rising fast') and a request for help."
        assert result["post_id"] == "post_123"
        assert "sentiment_id" in result

# ==========================================
# TEST CASE: IT-06-001
# ==========================================

def test_it_06_001_end_to_end_flow(mock_db, sample_post, mock_llm_response_content):
    """
    Test Case ID: IT-06-001
    Test Scenario: End-to-End Sentiment Processing Flow
    Coverage: DB Fetching <-> AI Classification <-> DB Insertion
    """
    # 1. Setup DB Mock Behavior
    # First call returns a list with one post, second call returns empty list (to stop the while loop)
    mock_db.get_unclassified_sentiment_posts.side_effect = [[sample_post], []]
    
    # Setup OpenAI Mock
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content=mock_llm_response_content))
    ]

    # Patch asyncio.sleep to speed up the test (in case of retry logic or sweep loops)
    with patch("time.sleep", return_value=None), \
         patch.object(main_sentimentAnalysis, 'aclient') as mock_aclient:
        
        mock_aclient.chat.completions.create = AsyncMock(return_value=mock_completion)

        # 2. Execute the Sweep (Synchronous Entry Point)
        # We pass batch_size=1 to match our mock data
        total_analyzed = main_sentimentAnalysis.run_sentiment_job_sweep(mock_db, batch_size=1)

        # 3. Verify DB Interactions
        
        # Verify Fetching: Was get_unclassified_sentiment_posts called?
        assert mock_db.get_unclassified_sentiment_posts.called
        
        # Verify Insertion: Was insert_many_sentiments called with structured results?
        assert mock_db.insert_many_sentiments.called
        
        # Capture the args passed to insert_many_sentiments
        inserted_data = mock_db.insert_many_sentiments.call_args[0][0]
        
        # Assertions on the inserted data
        assert len(inserted_data) == 1
        record = inserted_data[0]
        assert record["post_id"] == "post_123"
        assert record["sentiment_label"] == "Urgent"
        assert record["model"] == "gpt-4o-mini"
        
        # Verify Return Value
        assert total_analyzed == 1