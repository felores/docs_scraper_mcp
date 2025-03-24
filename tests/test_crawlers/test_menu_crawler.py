"""
Tests for the MenuCrawler class.
"""
import pytest
from docs_scraper.crawlers import MenuCrawler
from docs_scraper.utils import RequestHandler, HTMLParser

@pytest.mark.asyncio
async def test_menu_crawler_successful_crawl(mock_website, test_urls, aiohttp_session):
    """Test successful crawling of menu links."""
    url = test_urls["valid_urls"][0]
    menu_selector = test_urls["menu_selector"]
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser()
    crawler = MenuCrawler(request_handler=request_handler, html_parser=html_parser)
    
    results = await crawler.crawl(url, menu_selector)
    
    assert len(results) >= 4  # Number of menu links in sample HTML
    for result in results:
        assert result["success"] is True
        assert result["url"].startswith("https://example.com")
        assert "content" in result
        assert "title" in result["metadata"]
        assert "description" in result["metadata"]
        assert len(result["links"]) > 0
        assert result["status_code"] == 200
        assert result["error"] is None

@pytest.mark.asyncio
async def test_menu_crawler_invalid_url(mock_website, test_urls, aiohttp_session):
    """Test crawling with an invalid URL."""
    url = test_urls["invalid_urls"][0]
    menu_selector = test_urls["menu_selector"]
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser()
    crawler = MenuCrawler(request_handler=request_handler, html_parser=html_parser)
    
    results = await crawler.crawl(url, menu_selector)
    
    assert len(results) == 1
    assert results[0]["success"] is False
    assert results[0]["url"] == url
    assert results[0]["error"] is not None

@pytest.mark.asyncio
async def test_menu_crawler_invalid_selector(mock_website, test_urls, aiohttp_session):
    """Test crawling with an invalid CSS selector."""
    url = test_urls["valid_urls"][0]
    invalid_selector = "#nonexistent-menu"
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser()
    crawler = MenuCrawler(request_handler=request_handler, html_parser=html_parser)
    
    results = await crawler.crawl(url, invalid_selector)
    
    assert len(results) == 1
    assert results[0]["success"] is False
    assert results[0]["url"] == url
    assert "No menu links found" in results[0]["error"]

@pytest.mark.asyncio
async def test_menu_crawler_nested_menu(mock_website, test_urls, aiohttp_session):
    """Test crawling nested menu structure."""
    url = test_urls["valid_urls"][0]
    menu_selector = test_urls["menu_selector"]
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser()
    crawler = MenuCrawler(
        request_handler=request_handler,
        html_parser=html_parser,
        max_depth=2  # Crawl up to 2 levels deep
    )
    
    results = await crawler.crawl(url, menu_selector)
    
    # Check if nested menu items were crawled
    urls = {result["url"] for result in results}
    assert "https://example.com/section1" in urls
    assert "https://example.com/section1/page1" in urls
    assert "https://example.com/section1/page2" in urls

@pytest.mark.asyncio
async def test_menu_crawler_concurrent_limit(mock_website, test_urls, aiohttp_session):
    """Test concurrent request limiting for menu crawling."""
    url = test_urls["valid_urls"][0]
    menu_selector = test_urls["menu_selector"]
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser()
    crawler = MenuCrawler(
        request_handler=request_handler,
        html_parser=html_parser,
        concurrent_limit=1  # Process one URL at a time
    )
    
    import time
    start_time = time.time()
    
    results = await crawler.crawl(url, menu_selector)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    assert len(results) >= 4
    # With concurrent_limit=1, processing should take at least 0.4 seconds
    assert elapsed_time >= 0.4

@pytest.mark.asyncio
async def test_menu_crawler_rate_limiting(mock_website, test_urls, aiohttp_session):
    """Test rate limiting for menu crawling."""
    url = test_urls["valid_urls"][0]
    menu_selector = test_urls["menu_selector"]
    request_handler = RequestHandler(session=aiohttp_session, rate_limit=1)  # 1 request per second
    html_parser = HTMLParser()
    crawler = MenuCrawler(request_handler=request_handler, html_parser=html_parser)
    
    import time
    start_time = time.time()
    
    results = await crawler.crawl(url, menu_selector)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    assert len(results) >= 4
    # Should take at least 3 seconds due to rate limiting
    assert elapsed_time >= 3.0

@pytest.mark.asyncio
async def test_menu_crawler_max_depth(mock_website, test_urls, aiohttp_session):
    """Test max depth limitation for menu crawling."""
    url = test_urls["valid_urls"][0]
    menu_selector = test_urls["menu_selector"]
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser()
    crawler = MenuCrawler(
        request_handler=request_handler,
        html_parser=html_parser,
        max_depth=1  # Only crawl top-level menu items
    )
    
    results = await crawler.crawl(url, menu_selector)
    
    # Should only include top-level menu items
    urls = {result["url"] for result in results}
    assert "https://example.com/section1" in urls
    assert "https://example.com/page1" in urls
    assert "https://example.com/section1/page1" not in urls  # Nested item should not be included 