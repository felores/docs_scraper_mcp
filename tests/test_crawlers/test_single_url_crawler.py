"""
Tests for the SingleURLCrawler class.
"""
import pytest
from docs_scraper.crawlers import SingleURLCrawler
from docs_scraper.utils import RequestHandler, HTMLParser

@pytest.mark.asyncio
async def test_single_url_crawler_successful_crawl(mock_website, test_urls, aiohttp_session):
    """Test successful crawling of a single URL."""
    url = test_urls["valid_urls"][0]
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser()
    crawler = SingleURLCrawler(request_handler=request_handler, html_parser=html_parser)
    
    result = await crawler.crawl(url)
    
    assert result["success"] is True
    assert result["url"] == url
    assert "content" in result
    assert "title" in result["metadata"]
    assert "description" in result["metadata"]
    assert len(result["links"]) > 0
    assert result["status_code"] == 200
    assert result["error"] is None

@pytest.mark.asyncio
async def test_single_url_crawler_invalid_url(mock_website, test_urls, aiohttp_session):
    """Test crawling with an invalid URL."""
    url = test_urls["invalid_urls"][0]
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser()
    crawler = SingleURLCrawler(request_handler=request_handler, html_parser=html_parser)
    
    result = await crawler.crawl(url)
    
    assert result["success"] is False
    assert result["url"] == url
    assert result["content"] is None
    assert result["metadata"] == {}
    assert result["links"] == []
    assert result["error"] is not None

@pytest.mark.asyncio
async def test_single_url_crawler_nonexistent_url(mock_website, test_urls, aiohttp_session):
    """Test crawling a URL that doesn't exist."""
    url = test_urls["invalid_urls"][2]
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser()
    crawler = SingleURLCrawler(request_handler=request_handler, html_parser=html_parser)
    
    result = await crawler.crawl(url)
    
    assert result["success"] is False
    assert result["url"] == url
    assert result["content"] is None
    assert result["metadata"] == {}
    assert result["links"] == []
    assert result["error"] is not None

@pytest.mark.asyncio
async def test_single_url_crawler_metadata_extraction(mock_website, test_urls, aiohttp_session):
    """Test extraction of metadata from a crawled page."""
    url = test_urls["valid_urls"][0]
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser()
    crawler = SingleURLCrawler(request_handler=request_handler, html_parser=html_parser)
    
    result = await crawler.crawl(url)
    
    assert result["success"] is True
    assert result["metadata"]["title"] == "Test Page"
    assert result["metadata"]["description"] == "Test description"

@pytest.mark.asyncio
async def test_single_url_crawler_link_extraction(mock_website, test_urls, aiohttp_session):
    """Test extraction of links from a crawled page."""
    url = test_urls["valid_urls"][0]
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser()
    crawler = SingleURLCrawler(request_handler=request_handler, html_parser=html_parser)
    
    result = await crawler.crawl(url)
    
    assert result["success"] is True
    assert len(result["links"]) >= 6  # Number of links in sample HTML
    assert "/page1" in result["links"]
    assert "/section1" in result["links"]
    assert "/test1" in result["links"]
    assert "/test2" in result["links"]

@pytest.mark.asyncio
async def test_single_url_crawler_rate_limiting(mock_website, test_urls, aiohttp_session):
    """Test rate limiting functionality."""
    url = test_urls["valid_urls"][0]
    request_handler = RequestHandler(session=aiohttp_session, rate_limit=1)  # 1 request per second
    html_parser = HTMLParser()
    crawler = SingleURLCrawler(request_handler=request_handler, html_parser=html_parser)
    
    import time
    start_time = time.time()
    
    # Make multiple requests
    for _ in range(3):
        result = await crawler.crawl(url)
        assert result["success"] is True
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # Should take at least 2 seconds due to rate limiting
    assert elapsed_time >= 2.0 