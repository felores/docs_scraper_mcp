"""
MCP server implementation for web crawling and documentation scraping.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, HttpUrl
from mcp.server.fastmcp import FastMCP

# Import the crawlers with relative imports
# This helps prevent circular import issues
from .crawlers.single_url_crawler import SingleURLCrawler
from .crawlers.multi_url_crawler import MultiURLCrawler
from .crawlers.sitemap_crawler import SitemapCrawler
from .crawlers.menu_crawler import MenuCrawler

# Import utility classes
from .utils import RequestHandler, HTMLParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create MCP server
mcp = FastMCP(
    name="DocsScraperMCP",
    version="0.1.0"
)

# Input validation models
class SingleUrlInput(BaseModel):
    url: HttpUrl = Field(..., description="Target URL to crawl")
    depth: int = Field(0, ge=0, description="How many levels deep to follow links")
    exclusion_patterns: Optional[List[str]] = Field(None, description="List of regex patterns for URLs to exclude")
    rate_limit: float = Field(1.0, gt=0, description="Minimum time between requests (seconds)")

class MultiUrlInput(BaseModel):
    urls: List[HttpUrl] = Field(..., min_items=1, description="List of URLs to crawl")
    concurrent_limit: int = Field(5, gt=0, description="Maximum number of concurrent requests")
    exclusion_patterns: Optional[List[str]] = Field(None, description="List of regex patterns for URLs to exclude")
    rate_limit: float = Field(1.0, gt=0, description="Minimum time between requests to the same domain (seconds)")

class SitemapInput(BaseModel):
    base_url: HttpUrl = Field(..., description="Base URL of the website")
    sitemap_url: Optional[HttpUrl] = Field(None, description="Optional explicit sitemap URL")
    concurrent_limit: int = Field(5, gt=0, description="Maximum number of concurrent requests")
    exclusion_patterns: Optional[List[str]] = Field(None, description="List of regex patterns for URLs to exclude")
    rate_limit: float = Field(1.0, gt=0, description="Minimum time between requests (seconds)")

class MenuInput(BaseModel):
    base_url: HttpUrl = Field(..., description="Base URL of the website")
    menu_selector: str = Field(..., min_length=1, description="CSS selector for the navigation menu element")
    concurrent_limit: int = Field(5, gt=0, description="Maximum number of concurrent requests")
    exclusion_patterns: Optional[List[str]] = Field(None, description="List of regex patterns for URLs to exclude")
    rate_limit: float = Field(1.0, gt=0, description="Minimum time between requests (seconds)")

@mcp.tool()
async def single_url_crawler(
    url: str,
    depth: int = 0,
    exclusion_patterns: Optional[List[str]] = None,
    rate_limit: float = 1.0
) -> Dict[str, Any]:
    """
    Crawl a single URL and optionally follow links up to a specified depth.
    
    Args:
        url: Target URL to crawl
        depth: How many levels deep to follow links (0 means only the target URL)
        exclusion_patterns: List of regex patterns for URLs to exclude
        rate_limit: Minimum time between requests (seconds)
        
    Returns:
        Dict containing crawled content and statistics
    """
    try:
        # Validate input
        input_data = SingleUrlInput(
            url=url,
            depth=depth,
            exclusion_patterns=exclusion_patterns,
            rate_limit=rate_limit
        )
        
        # Create required utility instances
        request_handler = RequestHandler(rate_limit=input_data.rate_limit)
        html_parser = HTMLParser(base_url=str(input_data.url))
        
        # Create the crawler with the proper parameters
        crawler = SingleURLCrawler(request_handler=request_handler, html_parser=html_parser)
        
        # Use request_handler as a context manager to ensure proper session initialization
        async with request_handler:
            # Call the crawl method with the URL
            return await crawler.crawl(str(input_data.url))
        
    except Exception as e:
        logger.error(f"Single URL crawler failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "content": None,
            "stats": {
                "urls_crawled": 0,
                "urls_failed": 1,
                "max_depth_reached": 0
            }
        }

@mcp.tool()
async def multi_url_crawler(
    urls: List[str],
    concurrent_limit: int = 5,
    exclusion_patterns: Optional[List[str]] = None,
    rate_limit: float = 1.0
) -> Dict[str, Any]:
    """
    Crawl multiple URLs in parallel with rate limiting.
    
    Args:
        urls: List of URLs to crawl
        concurrent_limit: Maximum number of concurrent requests
        exclusion_patterns: List of regex patterns for URLs to exclude
        rate_limit: Minimum time between requests to the same domain (seconds)
        
    Returns:
        Dict containing results for each URL and overall statistics
    """
    try:
        # Validate input
        input_data = MultiUrlInput(
            urls=urls,
            concurrent_limit=concurrent_limit,
            exclusion_patterns=exclusion_patterns,
            rate_limit=rate_limit
        )
        
        # Create the crawler with the proper parameters
        crawler = MultiURLCrawler(verbose=True)
        
        # Call the crawl method with the URLs
        url_list = [str(url) for url in input_data.urls]
        results = await crawler.crawl(url_list)
        
        # Return a standardized response format
        return {
            "success": True,
            "results": results,
            "stats": {
                "urls_crawled": len(results),
                "urls_succeeded": sum(1 for r in results if r["success"]),
                "urls_failed": sum(1 for r in results if not r["success"])
            }
        }
        
    except Exception as e:
        logger.error(f"Multi URL crawler failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "content": None,
            "stats": {
                "urls_crawled": 0,
                "urls_failed": len(urls),
                "concurrent_requests_max": 0
            }
        }

@mcp.tool()
async def sitemap_crawler(
    base_url: str,
    sitemap_url: Optional[str] = None,
    concurrent_limit: int = 5,
    exclusion_patterns: Optional[List[str]] = None,
    rate_limit: float = 1.0
) -> Dict[str, Any]:
    """
    Crawl a website using its sitemap.xml.
    
    Args:
        base_url: Base URL of the website
        sitemap_url: Optional explicit sitemap URL (if different from base_url/sitemap.xml)
        concurrent_limit: Maximum number of concurrent requests
        exclusion_patterns: List of regex patterns for URLs to exclude
        rate_limit: Minimum time between requests (seconds)
        
    Returns:
        Dict containing crawled pages and statistics
    """
    try:
        # Validate input
        input_data = SitemapInput(
            base_url=base_url,
            sitemap_url=sitemap_url,
            concurrent_limit=concurrent_limit,
            exclusion_patterns=exclusion_patterns,
            rate_limit=rate_limit
        )
        
        # Create required utility instances
        request_handler = RequestHandler(
            rate_limit=input_data.rate_limit,
            concurrent_limit=input_data.concurrent_limit
        )
        html_parser = HTMLParser(base_url=str(input_data.base_url))
        
        # Create the crawler with the proper parameters
        crawler = SitemapCrawler(
            request_handler=request_handler,
            html_parser=html_parser,
            verbose=True
        )
        
        # Determine the sitemap URL to use
        sitemap_url_to_use = str(input_data.sitemap_url) if input_data.sitemap_url else f"{str(input_data.base_url).rstrip('/')}/sitemap.xml"
        
        # Call the crawl method with the sitemap URL
        results = await crawler.crawl(sitemap_url_to_use)
        
        return {
            "success": True,
            "content": results,
            "stats": {
                "urls_crawled": len(results),
                "urls_succeeded": sum(1 for r in results if r["success"]),
                "urls_failed": sum(1 for r in results if not r["success"]),
                "sitemap_found": len(results) > 0
            }
        }
        
    except Exception as e:
        logger.error(f"Sitemap crawler failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "content": None,
            "stats": {
                "urls_crawled": 0,
                "urls_failed": 1,
                "sitemap_found": False
            }
        }

@mcp.tool()
async def menu_crawler(
    base_url: str,
    menu_selector: str,
    concurrent_limit: int = 5,
    exclusion_patterns: Optional[List[str]] = None,
    rate_limit: float = 1.0
) -> Dict[str, Any]:
    """
    Crawl a website by following its navigation menu structure.
    
    Args:
        base_url: Base URL of the website
        menu_selector: CSS selector for the navigation menu element
        concurrent_limit: Maximum number of concurrent requests
        exclusion_patterns: List of regex patterns for URLs to exclude
        rate_limit: Minimum time between requests (seconds)
        
    Returns:
        Dict containing menu structure and crawled content
    """
    try:
        # Validate input
        input_data = MenuInput(
            base_url=base_url,
            menu_selector=menu_selector,
            concurrent_limit=concurrent_limit,
            exclusion_patterns=exclusion_patterns,
            rate_limit=rate_limit
        )
        
        # Create the crawler with the proper parameters
        crawler = MenuCrawler(start_url=str(input_data.base_url))
        
        # Call the crawl method
        results = await crawler.crawl()
        
        return {
            "success": True,
            "content": results,
            "stats": {
                "urls_crawled": len(results.get("menu_links", [])),
                "urls_failed": 0,
                "menu_items_found": len(results.get("menu_structure", {}).get("items", []))
            }
        }
        
    except Exception as e:
        logger.error(f"Menu crawler failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "content": None,
            "stats": {
                "urls_crawled": 0,
                "urls_failed": 1,
                "menu_items_found": 0
            }
        }

def main():
    """Main entry point for the MCP server."""
    try:
        logger.info("Starting DocsScraperMCP server...")
        mcp.run()  # Using run() method instead of start()
    except Exception as e:
        logger.error(f"Server failed: {str(e)}")
        raise
    finally:
        logger.info("DocsScraperMCP server stopped.")

if __name__ == "__main__":
    main() 