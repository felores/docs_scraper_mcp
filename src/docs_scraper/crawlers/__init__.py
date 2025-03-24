"""
Web crawler implementations for documentation scraping.
"""
from .single_url_crawler import SingleURLCrawler
from .multi_url_crawler import MultiURLCrawler
from .sitemap_crawler import SitemapCrawler
from .menu_crawler import MenuCrawler

__all__ = [
    'SingleURLCrawler',
    'MultiURLCrawler',
    'SitemapCrawler',
    'MenuCrawler'
] 