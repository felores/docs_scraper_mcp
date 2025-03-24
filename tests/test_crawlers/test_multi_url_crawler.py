"""
Tests for the MultiURLCrawler class.
"""
import pytest
from docs_scraper.crawlers import MultiURLCrawler
from docs_scraper.utils import RequestHandler, HTMLParser

@pytest.mark.asyncio
async def test_multi_url_crawler_successful_crawl(mock_website, test_urls, aiohttp_session):
    """Test successful crawling of multiple URLs."""
    urls = test_urls["valid_urls"]
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser()
    crawler = MultiURLCrawler(request_handler=request_handler, html_parser=html_parser)
    
    results = await crawler.crawl(urls)
    
    assert len(results) == len(urls)
    for result, url in zip(results, urls):
        assert result["success"] is True
        assert result["url"] == url
        assert "content" in result
        assert "title" in result["metadata"]
        assert "description" in result["metadata"]
        assert len(result["links"]) > 0
        assert result["status_code"] == 200
        assert result["error"] is None

@pytest.mark.asyncio
async def test_multi_url_crawler_mixed_urls(mock_website, test_urls, aiohttp_session):
    """Test crawling a mix of valid and invalid URLs."""
    urls = test_urls["valid_urls"][:1] + test_urls["invalid_urls"][:1]
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser()
    crawler = MultiURLCrawler(request_handler=request_handler, html_parser=html_parser)
    
    results = await crawler.crawl(urls)
    
    assert len(results) == len(urls)
    # Valid URL
    assert results[0]["success"] is True
    assert results[0]["url"] == urls[0]
    assert "content" in results[0]
    # Invalid URL
    assert results[1]["success"] is False
    assert results[1]["url"] == urls[1]
    assert results[1]["content"] is None

@pytest.mark.asyncio
async def test_multi_url_crawler_concurrent_limit(mock_website, test_urls, aiohttp_session):
    """Test concurrent request limiting."""
    urls = test_urls["valid_urls"] * 2  # Duplicate URLs to have more requests
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser()
    crawler = MultiURLCrawler(
        request_handler=request_handler,
        html_parser=html_parser,
        concurrent_limit=2
    )
    
    import time
    start_time = time.time()
    
    results = await crawler.crawl(urls)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    assert len(results) == len(urls)
    # With concurrent_limit=2, processing 6 URLs should take at least 3 time units
    assert elapsed_time >= (len(urls) / 2) * 0.1  # Assuming each request takes ~0.1s

@pytest.mark.asyncio
async def test_multi_url_crawler_empty_urls(mock_website, aiohttp_session):
    """Test crawling with empty URL list."""
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser()
    crawler = MultiURLCrawler(request_handler=request_handler, html_parser=html_parser)
    
    results = await crawler.crawl([])
    
    assert len(results) == 0

@pytest.mark.asyncio
async def test_multi_url_crawler_duplicate_urls(mock_website, test_urls, aiohttp_session):
    """Test crawling with duplicate URLs."""
    url = test_urls["valid_urls"][0]
    urls = [url, url, url]  # Same URL multiple times
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser()
    crawler = MultiURLCrawler(request_handler=request_handler, html_parser=html_parser)
    
    results = await crawler.crawl(urls)
    
    assert len(results) == len(urls)
    for result in results:
        assert result["success"] is True
        assert result["url"] == url
        assert result["metadata"]["title"] == "Test Page"

@pytest.mark.asyncio
async def test_multi_url_crawler_rate_limiting(mock_website, test_urls, aiohttp_session):
    """Test rate limiting with multiple URLs."""
    urls = test_urls["valid_urls"]
    request_handler = RequestHandler(session=aiohttp_session, rate_limit=1)  # 1 request per second
    html_parser = HTMLParser()
    crawler = MultiURLCrawler(request_handler=request_handler, html_parser=html_parser)
    
    import time
    start_time = time.time()
    
    results = await crawler.crawl(urls)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    assert len(results) == len(urls)
    # Should take at least (len(urls) - 1) seconds due to rate limiting
    assert elapsed_time >= len(urls) - 1 