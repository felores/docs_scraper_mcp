"""
Tests for the SitemapCrawler class.
"""
import pytest
from docs_scraper.crawlers import SitemapCrawler
from docs_scraper.utils import RequestHandler, HTMLParser

@pytest.mark.asyncio
async def test_sitemap_crawler_successful_crawl(mock_website, test_urls, aiohttp_session):
    """Test successful crawling of a sitemap."""
    sitemap_url = test_urls["sitemap_url"]
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser(base_url=test_urls["base_url"])
    crawler = SitemapCrawler(request_handler=request_handler, html_parser=html_parser)
    
    results = await crawler.crawl(sitemap_url)
    
    assert len(results) == 3  # Number of URLs in sample sitemap
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
async def test_sitemap_crawler_invalid_sitemap_url(mock_website, aiohttp_session):
    """Test crawling with an invalid sitemap URL."""
    sitemap_url = "https://nonexistent.example.com/sitemap.xml"
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser(base_url="https://nonexistent.example.com")
    crawler = SitemapCrawler(request_handler=request_handler, html_parser=html_parser)
    
    results = await crawler.crawl(sitemap_url)
    
    assert len(results) == 1
    assert results[0]["success"] is False
    assert results[0]["url"] == sitemap_url
    assert results[0]["error"] is not None

@pytest.mark.asyncio
async def test_sitemap_crawler_invalid_xml(mock_website, aiohttp_session):
    """Test crawling with invalid XML content."""
    sitemap_url = "https://example.com/invalid-sitemap.xml"
    mock_website.get(sitemap_url, status=200, body="<invalid>xml</invalid>")
    
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser(base_url="https://example.com")
    crawler = SitemapCrawler(request_handler=request_handler, html_parser=html_parser)
    
    results = await crawler.crawl(sitemap_url)
    
    assert len(results) == 1
    assert results[0]["success"] is False
    assert results[0]["url"] == sitemap_url
    assert "Invalid sitemap format" in results[0]["error"]

@pytest.mark.asyncio
async def test_sitemap_crawler_concurrent_limit(mock_website, test_urls, aiohttp_session):
    """Test concurrent request limiting for sitemap crawling."""
    sitemap_url = test_urls["sitemap_url"]
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser(base_url=test_urls["base_url"])
    crawler = SitemapCrawler(request_handler=request_handler, html_parser=html_parser)
    
    import time
    start_time = time.time()
    
    results = await crawler.crawl(sitemap_url)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    assert len(results) == 3
    # With concurrent_limit=1, processing should take at least 0.3 seconds
    assert elapsed_time >= 0.3

@pytest.mark.asyncio
async def test_sitemap_crawler_rate_limiting(mock_website, test_urls, aiohttp_session):
    """Test rate limiting for sitemap crawling."""
    sitemap_url = test_urls["sitemap_url"]
    request_handler = RequestHandler(session=aiohttp_session, rate_limit=1)  # 1 request per second
    html_parser = HTMLParser(base_url=test_urls["base_url"])
    crawler = SitemapCrawler(request_handler=request_handler, html_parser=html_parser)
    
    import time
    start_time = time.time()
    
    results = await crawler.crawl(sitemap_url)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    assert len(results) == 3
    # Should take at least 3 seconds due to rate limiting (1 for sitemap + 2 for pages)
    assert elapsed_time >= 2.0

@pytest.mark.asyncio
async def test_sitemap_crawler_nested_sitemaps(mock_website, test_urls, aiohttp_session):
    """Test crawling nested sitemaps."""
    # Create a sitemap index
    sitemap_index = """<?xml version="1.0" encoding="UTF-8"?>
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <sitemap>
            <loc>https://example.com/sitemap1.xml</loc>
        </sitemap>
        <sitemap>
            <loc>https://example.com/sitemap2.xml</loc>
        </sitemap>
    </sitemapindex>
    """
    
    # Create sub-sitemaps
    sitemap1 = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/page1</loc>
        </url>
    </urlset>
    """
    
    sitemap2 = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/page2</loc>
        </url>
    </urlset>
    """
    
    mock_website.get("https://example.com/sitemap-index.xml", status=200, body=sitemap_index)
    mock_website.get("https://example.com/sitemap1.xml", status=200, body=sitemap1)
    mock_website.get("https://example.com/sitemap2.xml", status=200, body=sitemap2)
    
    request_handler = RequestHandler(session=aiohttp_session)
    html_parser = HTMLParser(base_url="https://example.com")
    crawler = SitemapCrawler(request_handler=request_handler, html_parser=html_parser)
    
    results = await crawler.crawl("https://example.com/sitemap-index.xml")
    
    assert len(results) == 2  # Two pages from two sub-sitemaps
    urls = {result["url"] for result in results}
    assert "https://example.com/page1" in urls
    assert "https://example.com/page2" in urls 