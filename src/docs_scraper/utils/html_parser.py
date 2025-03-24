"""
HTML parser module for extracting content and links from HTML documents.
"""
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class HTMLParser:
    def __init__(self, base_url: str):
        """
        Initialize the HTML parser.
        
        Args:
            base_url: Base URL for resolving relative links
        """
        self.base_url = base_url

    def parse_content(self, html: str) -> Dict[str, Any]:
        """
        Parse HTML content and extract useful information.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Dict containing:
                - title: Page title
                - description: Meta description
                - text_content: Main text content
                - links: List of links found
                - headers: List of headers found
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract title
        title = soup.title.string if soup.title else None
        
        # Extract meta description
        meta_desc = None
        meta_tag = soup.find('meta', attrs={'name': 'description'})
        if meta_tag:
            meta_desc = meta_tag.get('content')
        
        # Extract main content (remove script, style, etc.)
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        
        # Get text content
        text_content = ' '.join(soup.stripped_strings)
        
        # Extract headers
        headers = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            headers.append({
                'level': int(tag.name[1]),
                'text': tag.get_text(strip=True)
            })
        
        # Extract links
        links = self._extract_links(soup)
        
        return {
            'title': title,
            'description': meta_desc,
            'text_content': text_content,
            'links': links,
            'headers': headers
        }

    def parse_menu(self, html: str, menu_selector: str) -> List[Dict[str, Any]]:
        """
        Parse navigation menu from HTML using a CSS selector.
        
        Args:
            html: Raw HTML content
            menu_selector: CSS selector for the menu element
            
        Returns:
            List of menu items with their structure
        """
        soup = BeautifulSoup(html, 'lxml')
        menu = soup.select_one(menu_selector)
        
        if not menu:
            return []
            
        return self._extract_menu_items(menu)

    def _extract_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract and normalize all links from the document."""
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True)
            
            # Skip empty or javascript links
            if not href or href.startswith(('javascript:', '#')):
                continue
                
            # Resolve relative URLs
            absolute_url = urljoin(self.base_url, href)
            
            # Only include links to the same domain
            if urlparse(absolute_url).netloc == urlparse(self.base_url).netloc:
                links.append({
                    'url': absolute_url,
                    'text': text
                })
                
        return links

    def _extract_menu_items(self, element: BeautifulSoup) -> List[Dict[str, Any]]:
        """Recursively extract menu structure."""
        items = []
        
        for item in element.find_all(['li', 'a'], recursive=False):
            if item.name == 'a':
                # Single link item
                href = item.get('href')
                if href and not href.startswith(('javascript:', '#')):
                    items.append({
                        'type': 'link',
                        'url': urljoin(self.base_url, href),
                        'text': item.get_text(strip=True)
                    })
            else:
                # Potentially nested menu item
                link = item.find('a')
                if link and link.get('href'):
                    menu_item = {
                        'type': 'menu',
                        'text': link.get_text(strip=True),
                        'url': urljoin(self.base_url, link['href']),
                        'children': []
                    }
                    
                    # Look for nested lists
                    nested = item.find(['ul', 'ol'])
                    if nested:
                        menu_item['children'] = self._extract_menu_items(nested)
                        
                    items.append(menu_item)
                    
        return items 