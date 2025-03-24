"""
Test configuration and fixtures for the docs_scraper package.
"""
import os
import pytest
import aiohttp
from typing import AsyncGenerator, Dict, Any
from aioresponses import aioresponses
from bs4 import BeautifulSoup

@pytest.fixture
def mock_aiohttp() -> aioresponses:
    """Fixture for mocking aiohttp requests."""
    with aioresponses() as m:
        yield m

@pytest.fixture
def sample_html() -> str:
    """Sample HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
        <meta name="description" content="Test description">
    </head>
    <body>
        <nav class="menu">
            <ul>
                <li><a href="/page1">Page 1</a></li>
                <li>
                    <a href="/section1">Section 1</a>
                    <ul>
                        <li><a href="/section1/page1">Section 1.1</a></li>
                        <li><a href="/section1/page2">Section 1.2</a></li>
                    </ul>
                </li>
            </ul>
        </nav>
        <main>
            <h1>Welcome</h1>
            <p>Test content</p>
            <a href="/test1">Link 1</a>
            <a href="/test2">Link 2</a>
        </main>
    </body>
    </html>
    """

@pytest.fixture
def sample_sitemap() -> str:
    """Sample sitemap.xml content for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/</loc>
            <lastmod>2024-03-24</lastmod>
        </url>
        <url>
            <loc>https://example.com/page1</loc>
            <lastmod>2024-03-24</lastmod>
        </url>
        <url>
            <loc>https://example.com/page2</loc>
            <lastmod>2024-03-24</lastmod>
        </url>
    </urlset>
    """

@pytest.fixture
def mock_website(mock_aiohttp, sample_html, sample_sitemap) -> None:
    """Set up a mock website with various pages and a sitemap."""
    base_url = "https://example.com"
    pages = {
        "/": sample_html,
        "/page1": sample_html.replace("Test Page", "Page 1"),
        "/page2": sample_html.replace("Test Page", "Page 2"),
        "/section1": sample_html.replace("Test Page", "Section 1"),
        "/section1/page1": sample_html.replace("Test Page", "Section 1.1"),
        "/section1/page2": sample_html.replace("Test Page", "Section 1.2"),
        "/robots.txt": "User-agent: *\nAllow: /",
        "/sitemap.xml": sample_sitemap
    }
    
    for path, content in pages.items():
        mock_aiohttp.get(f"{base_url}{path}", status=200, body=content)

@pytest.fixture
async def aiohttp_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Create an aiohttp ClientSession for testing."""
    async with aiohttp.ClientSession() as session:
        yield session

@pytest.fixture
def test_urls() -> Dict[str, Any]:
    """Test URLs and related data for testing."""
    base_url = "https://example.com"
    return {
        "base_url": base_url,
        "valid_urls": [
            f"{base_url}/",
            f"{base_url}/page1",
            f"{base_url}/page2"
        ],
        "invalid_urls": [
            "not_a_url",
            "ftp://example.com",
            "https://nonexistent.example.com"
        ],
        "menu_selector": "nav.menu",
        "sitemap_url": f"{base_url}/sitemap.xml"
    } 