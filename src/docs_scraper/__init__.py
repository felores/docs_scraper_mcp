"""
Documentation scraper MCP server package.
"""
# Import subpackages but not modules to avoid circular imports
from . import crawlers
from . import utils

# Expose important items at package level
__all__ = ['crawlers', 'utils'] 