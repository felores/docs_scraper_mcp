"""
Request handler module for managing HTTP requests with rate limiting and error handling.
"""
import asyncio
import logging
from typing import Optional, Dict, Any
import aiohttp
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class RequestHandler:
    def __init__(
        self,
        rate_limit: float = 1.0,
        concurrent_limit: int = 5,
        user_agent: str = "DocsScraperBot/1.0",
        timeout: int = 30,
        session: Optional[aiohttp.ClientSession] = None
    ):
        """
        Initialize the request handler.
        
        Args:
            rate_limit: Minimum time between requests to the same domain (in seconds)
            concurrent_limit: Maximum number of concurrent requests
            user_agent: User agent string to use for requests
            timeout: Request timeout in seconds
            session: Optional aiohttp.ClientSession to use. If not provided, one will be created.
        """
        self.rate_limit = rate_limit
        self.concurrent_limit = concurrent_limit
        self.user_agent = user_agent
        self.timeout = timeout
        self._provided_session = session
        
        self._domain_locks: Dict[str, asyncio.Lock] = {}
        self._domain_last_request: Dict[str, float] = {}
        self._semaphore = asyncio.Semaphore(concurrent_limit)
        self._session: Optional[aiohttp.ClientSession] = None
        self._robot_parsers: Dict[str, RobotFileParser] = {}

    async def __aenter__(self):
        """Set up the aiohttp session."""
        if self._provided_session:
            self._session = self._provided_session
        else:
            self._session = aiohttp.ClientSession(
                headers={"User-Agent": self.user_agent},
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up the aiohttp session."""
        if self._session and not self._provided_session:
            await self._session.close()

    async def _check_robots_txt(self, url: str) -> bool:
        """
        Check if the URL is allowed by robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if allowed, False if disallowed
        """
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        
        if domain not in self._robot_parsers:
            parser = RobotFileParser()
            parser.set_url(urljoin(domain, "/robots.txt"))
            try:
                async with self._session.get(parser.url) as response:
                    content = await response.text()
                    parser.parse(content.splitlines())
            except Exception as e:
                logger.warning(f"Failed to fetch robots.txt for {domain}: {e}")
                return True
            self._robot_parsers[domain] = parser
            
        return self._robot_parsers[domain].can_fetch(self.user_agent, url)

    async def get(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Make a GET request with rate limiting and error handling.
        
        Args:
            url: URL to request
            **kwargs: Additional arguments to pass to aiohttp.ClientSession.get()
            
        Returns:
            Dict containing:
                - success: bool indicating if request was successful
                - status: HTTP status code if available
                - content: Response content if successful
                - error: Error message if unsuccessful
        """
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc

        # Get or create domain lock
        if domain not in self._domain_locks:
            self._domain_locks[domain] = asyncio.Lock()

        # Check robots.txt
        if not await self._check_robots_txt(url):
            return {
                "success": False,
                "status": None,
                "error": "URL disallowed by robots.txt",
                "content": None
            }

        try:
            async with self._semaphore:  # Limit concurrent requests
                async with self._domain_locks[domain]:  # Lock per domain
                    # Rate limiting
                    if domain in self._domain_last_request:
                        elapsed = asyncio.get_event_loop().time() - self._domain_last_request[domain]
                        if elapsed < self.rate_limit:
                            await asyncio.sleep(self.rate_limit - elapsed)
                    
                    self._domain_last_request[domain] = asyncio.get_event_loop().time()
                    
                    # Make request
                    async with self._session.get(url, **kwargs) as response:
                        content = await response.text()
                        return {
                            "success": response.status < 400,
                            "status": response.status,
                            "content": content,
                            "error": None if response.status < 400 else f"HTTP {response.status}"
                        }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "status": None,
                "error": "Request timed out",
                "content": None
            }
        except Exception as e:
            return {
                "success": False,
                "status": None,
                "error": str(e),
                "content": None
            } 