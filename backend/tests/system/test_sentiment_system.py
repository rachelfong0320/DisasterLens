import pytest
import asyncio
import json
from unittest.mock import MagicMock, patch, AsyncMock
from core.jobs import main_sentimentAnalysis

# ==========================================
# TEST FIXTURES
# ==========================================

@pytest.fixture
def mock_db_system():
    """Mocks the database interaction for the system test."""
    db = MagicMock()
    # Mock collections or specific DB methods used by the job
    db.get_unclassified_sentiment_posts = MagicMock()
    db.insert_many_sentiments = MagicMock()
    return db

@pytest.fixture
def sample_post_batch():
    """Returns a batch of raw posts to be processed."""
    return [
        {"postId": "post_101", "postText": "URGENT! Flood waters entering house in Klang!"},
        {"postId": "post_102", "postText": "Just a rainy day in KL."}
    ]

@pytest.fixture
def mock_openai_response_urgent():
    """Valid JSON response for an Urgent sentiment."""
    return json.dumps({
        "sentiment": "Urgent", # Matches schema alias
        "confidence_score": 0.98,
        "reasoning": "Explicit mention of flood entering house implies life-threatening situation."
    })

# ==========================================
# TEST CASE: ST-06-001
# ==========================================

def test_st_06_001_end_to_end_success(mock_db_system, sample_post_batch, mock_openai_response_urgent):
    """
    Test Case ID: ST-06-001
    Scenario: Verify End-to-End Sentiment/Urgency Classification
    Expected Result: System identifies post as Urgent and updates DB.
    """
    # 1. Setup DB Mock
    # First call returns batch, Second call returns [] to stop loop
    mock_db_system.get_unclassified_sentiment_posts.side_effect = [sample_post_batch, []]

    # 2. Setup OpenAI Mock
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content=mock_openai_response_urgent))]
    
    # 3. Execution
    with patch.object(main_sentimentAnalysis, "aclient") as mock_aclient, \
         patch("time.sleep", return_value=None): # Skip sync sleep
        
        mock_aclient.chat.completions.create = AsyncMock(return_value=mock_completion)

        # Run the synchronous entry point
        total_processed = main_sentimentAnalysis.run_sentiment_job_sweep(mock_db_system, batch_size=2)

    # 4. Verification
    # Assert DB Fetch
    assert mock_db_system.get_unclassified_sentiment_posts.called
    
    # Assert DB Insert
    assert mock_db_system.insert_many_sentiments.called
    inserted_docs = mock_db_system.insert_many_sentiments.call_args[0][0]
    
    # Check Metadata
    assert len(inserted_docs) == 2
    assert inserted_docs[0]["sentiment_label"] == "Urgent"
    assert inserted_docs[0]["post_id"] == "post_101"
    assert "analyzed_at" in inserted_docs[0]
    assert inserted_docs[0]["model"] == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_st_06_001_retry_logic_and_backoff(mock_db_system):
    """
    Test Case ID: ST-06-001 (Exception Flow)
    Scenario: Verify Exponential Backoff on 429 Rate Limit
    Expected Result: System performs retry on 429 error.
    """
    post = {"postId": "retry_test", "postText": "Testing retry logic"}
    sem = asyncio.Semaphore(20)

    # Mock Exception then Success
    mock_response_content = json.dumps({
        "sentiment": "Informational",
        "confidence_score": 0.5,
        "reasoning": "Test"
    })
    mock_success = MagicMock(choices=[MagicMock(message=MagicMock(content=mock_response_content))])

    with patch.object(main_sentimentAnalysis, "aclient") as mock_aclient, \
         patch("asyncio.sleep") as mock_async_sleep: # Spy on async sleep
        
        # Side Effect: Fail with 429, then Succeed
        mock_aclient.chat.completions.create = AsyncMock(side_effect=[
            Exception("429 Rate limit exceeded"), 
            mock_success
        ])

        # Run worker directly
        result = await main_sentimentAnalysis.analyze_sentiment_async(post, sem)

        # Assertions
        assert result is not None
        assert result["sentiment_label"] == "Informational"
        
        # Verify Retry Count (Called twice)
        assert mock_aclient.chat.completions.create.call_count == 2
        
        # Verify Backoff (Sleep was called)
        mock_async_sleep.assert_called()


@pytest.mark.asyncio
async def test_st_06_001_concurrency_semaphore():
    """
    Test Case ID: ST-06-001 (Expected Result #3)
    Scenario: Verify Semaphore Implementation
    Expected Result: System uses semaphore to limit concurrent requests.
    """
    post = {"postId": "sem_test", "postText": "Sem test"}
    
    # Mock the semaphore object
    mock_sem = MagicMock(spec=asyncio.Semaphore)
    # The 'async with sem:' syntax calls __aenter__ and __aexit__
    mock_sem.__aenter__ = AsyncMock()
    mock_sem.__aexit__ = AsyncMock()

    # Mock OpenAI to avoid errors
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content=json.dumps({
        "sentiment": "Warning", "confidence_score": 1.0, "reasoning": "Test"
    })))]

    with patch.object(main_sentimentAnalysis, "aclient") as mock_aclient:
        mock_aclient.chat.completions.create = AsyncMock(return_value=mock_completion)

        # Run worker with mocked semaphore
        await main_sentimentAnalysis.analyze_sentiment_async(post, mock_sem)

        # Verify Semaphore was acquired
        mock_sem.__aenter__.assert_called_once()


@pytest.mark.asyncio
async def test_st_06_001_alternative_flow_uncertain(mock_db_system):
    """
    Test Case ID: ST-06-001 (Alternative Flow)
    Scenario: Handle ambiguous/"Uncertain" label (Invalid per Schema)
    Expected Result: System logs error and moves to next post without crashing (returns None).
    """
    post = {"postId": "ambiguous_post", "postText": "Not sure if disaster."}
    sem = asyncio.Semaphore(1)

    # Mock AI returning "Uncertain" (Which is NOT in the allowed Literal list in schemas.py)
    # Allowed: "Urgent", "Warning", "Informational"
    invalid_json = json.dumps({
        "sentiment": "Uncertain", 
        "confidence_score": 0.5,
        "reasoning": "Ambiguous"
    })

    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content=invalid_json))]

    with patch.object(main_sentimentAnalysis, "aclient") as mock_aclient:
        mock_aclient.chat.completions.create = AsyncMock(return_value=mock_completion)

        # Execute
        result = await main_sentimentAnalysis.analyze_sentiment_async(post, sem)

        # Verify Resilience
        # Pydantic validation should fail -> Exception caught -> returns None
        assert result is None