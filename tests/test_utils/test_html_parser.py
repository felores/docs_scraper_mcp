"""
Tests for the HTMLParser class.
"""
import pytest
from bs4 import BeautifulSoup
from docs_scraper.utils import HTMLParser

@pytest.fixture
def html_parser():
    """Fixture for HTMLParser instance."""
    return HTMLParser()

@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
        <meta name="description" content="Test description">
        <meta name="keywords" content="test, keywords">
        <meta property="og:title" content="OG Title">
        <meta property="og:description" content="OG Description">
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
            <p>Test content with a <a href="/test1">link</a> and another <a href="/test2">link</a>.</p>
            <div class="content">
                <p>More content</p>
                <a href="mailto:test@example.com">Email</a>
                <a href="tel:+1234567890">Phone</a>
                <a href="javascript:void(0)">JavaScript</a>
                <a href="#section">Hash</a>
                <a href="ftp://example.com">FTP</a>
            </div>
        </main>
    </body>
    </html>
    """

def test_parse_html(html_parser, sample_html):
    """Test HTML parsing."""
    soup = html_parser.parse_html(sample_html)
    assert isinstance(soup, BeautifulSoup)
    assert soup.title.string == "Test Page"

def test_extract_metadata(html_parser, sample_html):
    """Test metadata extraction."""
    soup = html_parser.parse_html(sample_html)
    metadata = html_parser.extract_metadata(soup)
    
    assert metadata["title"] == "Test Page"
    assert metadata["description"] == "Test description"
    assert metadata["keywords"] == "test, keywords"
    assert metadata["og:title"] == "OG Title"
    assert metadata["og:description"] == "OG Description"

def test_extract_links(html_parser, sample_html):
    """Test link extraction."""
    soup = html_parser.parse_html(sample_html)
    links = html_parser.extract_links(soup)
    
    # Should only include valid HTTP(S) links
    assert "/page1" in links
    assert "/section1" in links
    assert "/section1/page1" in links
    assert "/section1/page2" in links
    assert "/test1" in links
    assert "/test2" in links
    
    # Should not include invalid or special links
    assert "mailto:test@example.com" not in links
    assert "tel:+1234567890" not in links
    assert "javascript:void(0)" not in links
    assert "#section" not in links
    assert "ftp://example.com" not in links

def test_extract_menu_links(html_parser, sample_html):
    """Test menu link extraction."""
    soup = html_parser.parse_html(sample_html)
    menu_links = html_parser.extract_menu_links(soup, "nav.menu")
    
    assert len(menu_links) == 4
    assert "/page1" in menu_links
    assert "/section1" in menu_links
    assert "/section1/page1" in menu_links
    assert "/section1/page2" in menu_links

def test_extract_menu_links_invalid_selector(html_parser, sample_html):
    """Test menu link extraction with invalid selector."""
    soup = html_parser.parse_html(sample_html)
    menu_links = html_parser.extract_menu_links(soup, "#nonexistent")
    
    assert len(menu_links) == 0

def test_extract_text_content(html_parser, sample_html):
    """Test text content extraction."""
    soup = html_parser.parse_html(sample_html)
    content = html_parser.extract_text_content(soup)
    
    assert "Welcome" in content
    assert "Test content" in content
    assert "More content" in content
    # Should not include navigation text
    assert "Section 1.1" not in content

def test_clean_html(html_parser):
    """Test HTML cleaning."""
    dirty_html = """
    <html>
    <body>
        <script>alert('test');</script>
        <style>body { color: red; }</style>
        <p>Test content</p>
        <!-- Comment -->
        <iframe src="test.html"></iframe>
    </body>
    </html>
    """
    
    clean_html = html_parser.clean_html(dirty_html)
    soup = html_parser.parse_html(clean_html)
    
    assert len(soup.find_all("script")) == 0
    assert len(soup.find_all("style")) == 0
    assert len(soup.find_all("iframe")) == 0
    assert "Test content" in soup.get_text()

def test_normalize_url(html_parser):
    """Test URL normalization."""
    base_url = "https://example.com/docs"
    test_cases = [
        ("/test", "https://example.com/test"),
        ("test", "https://example.com/docs/test"),
        ("../test", "https://example.com/test"),
        ("https://other.com/test", "https://other.com/test"),
        ("//other.com/test", "https://other.com/test"),
    ]
    
    for input_url, expected_url in test_cases:
        assert html_parser.normalize_url(input_url, base_url) == expected_url

def test_is_valid_link(html_parser):
    """Test link validation."""
    valid_links = [
        "https://example.com",
        "http://example.com",
        "/absolute/path",
        "relative/path",
        "../parent/path",
        "./current/path"
    ]
    
    invalid_links = [
        "mailto:test@example.com",
        "tel:+1234567890",
        "javascript:void(0)",
        "#hash",
        "ftp://example.com",
        ""
    ]
    
    for link in valid_links:
        assert html_parser.is_valid_link(link) is True
    
    for link in invalid_links:
        assert html_parser.is_valid_link(link) is False

def test_extract_structured_data(html_parser):
    """Test structured data extraction."""
    html = """
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "Test Article",
            "author": {
                "@type": "Person",
                "name": "John Doe"
            }
        }
        </script>
    </head>
    <body>
        <p>Test content</p>
    </body>
    </html>
    """
    
    soup = html_parser.parse_html(html)
    structured_data = html_parser.extract_structured_data(soup)
    
    assert len(structured_data) == 1
    assert structured_data[0]["@type"] == "Article"
    assert structured_data[0]["headline"] == "Test Article"
    assert structured_data[0]["author"]["name"] == "John Doe" 