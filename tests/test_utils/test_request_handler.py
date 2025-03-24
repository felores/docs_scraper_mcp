"""
Tests for the RequestHandler class.
"""
import asyncio
import pytest
import aiohttp
import time
from docs_scraper.utils import RequestHandler

@pytest.mark.asyncio
async def test_request_handler_successful_get(mock_website, test_urls, aiohttp_session):
    """Test successful GET request."""
    url = test_urls["valid_urls"][0]
    handler = RequestHandler(session=aiohttp_session)
    
    response = await handler.get(url)
    
    assert response.status == 200
    assert "<!DOCTYPE html>" in await response.text()

@pytest.mark.asyncio
async def test_request_handler_invalid_url(mock_website, test_urls, aiohttp_session):
    """Test handling of invalid URL."""
    url = test_urls["invalid_urls"][0]
    handler = RequestHandler(session=aiohttp_session)
    
    with pytest.raises(aiohttp.ClientError):
        await handler.get(url)

@pytest.mark.asyncio
async def test_request_handler_nonexistent_url(mock_website, test_urls, aiohttp_session):
    """Test handling of nonexistent URL."""
    url = test_urls["invalid_urls"][2]
    handler = RequestHandler(session=aiohttp_session)
    
    with pytest.raises(aiohttp.ClientError):
        await handler.get(url)

@pytest.mark.asyncio
async def test_request_handler_rate_limiting(mock_website, test_urls, aiohttp_session):
    """Test rate limiting functionality."""
    url = test_urls["valid_urls"][0]
    rate_limit = 2  # 2 requests per second
    handler = RequestHandler(session=aiohttp_session, rate_limit=rate_limit)
    
    start_time = time.time()
    
    # Make multiple requests
    for _ in range(3):
        response = await handler.get(url)
        assert response.status == 200
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # Should take at least 1 second due to rate limiting
    assert elapsed_time >= 1.0

@pytest.mark.asyncio
async def test_request_handler_custom_headers(mock_website, test_urls, aiohttp_session):
    """Test custom headers in requests."""
    url = test_urls["valid_urls"][0]
    custom_headers = {
        "User-Agent": "Custom Bot 1.0",
        "Accept-Language": "en-US,en;q=0.9"
    }
    handler = RequestHandler(session=aiohttp_session, headers=custom_headers)
    
    response = await handler.get(url)
    
    assert response.status == 200
    # Headers should be merged with default headers
    assert handler.headers["User-Agent"] == "Custom Bot 1.0"
    assert handler.headers["Accept-Language"] == "en-US,en;q=0.9"

@pytest.mark.asyncio
async def test_request_handler_timeout(mock_website, test_urls, aiohttp_session):
    """Test request timeout handling."""
    url = test_urls["valid_urls"][0]
    handler = RequestHandler(session=aiohttp_session, timeout=0.001)  # Very short timeout
    
    # Mock a delayed response
    mock_website.get(url, status=200, body="Delayed response", delay=0.1)
    
    with pytest.raises(aiohttp.ClientTimeout):
        await handler.get(url)

@pytest.mark.asyncio
async def test_request_handler_retry(mock_website, test_urls, aiohttp_session):
    """Test request retry functionality."""
    url = test_urls["valid_urls"][0]
    handler = RequestHandler(session=aiohttp_session, max_retries=3)
    
    # Mock temporary failures followed by success
    mock_website.get(url, status=500)  # First attempt fails
    mock_website.get(url, status=500)  # Second attempt fails
    mock_website.get(url, status=200, body="Success")  # Third attempt succeeds
    
    response = await handler.get(url)
    
    assert response.status == 200
    assert await response.text() == "Success"

@pytest.mark.asyncio
async def test_request_handler_max_retries_exceeded(mock_website, test_urls, aiohttp_session):
    """Test behavior when max retries are exceeded."""
    url = test_urls["valid_urls"][0]
    handler = RequestHandler(session=aiohttp_session, max_retries=2)
    
    # Mock consistent failures
    mock_website.get(url, status=500)
    mock_website.get(url, status=500)
    mock_website.get(url, status=500)
    
    with pytest.raises(aiohttp.ClientError):
        await handler.get(url)

@pytest.mark.asyncio
async def test_request_handler_session_management(mock_website, test_urls):
    """Test session management."""
    url = test_urls["valid_urls"][0]
    
    # Test with context manager
    async with aiohttp.ClientSession() as session:
        handler = RequestHandler(session=session)
        response = await handler.get(url)
        assert response.status == 200
    
    # Test with closed session
    with pytest.raises(aiohttp.ClientError):
        await handler.get(url)

@pytest.mark.asyncio
async def test_request_handler_concurrent_requests(mock_website, test_urls, aiohttp_session):
    """Test handling of concurrent requests."""
    urls = test_urls["valid_urls"]
    handler = RequestHandler(session=aiohttp_session)
    
    # Make concurrent requests
    tasks = [handler.get(url) for url in urls]
    responses = await asyncio.gather(*tasks)
    
    assert all(response.status == 200 for response in responses) 