from aiohttp import ClientSession, BasicAuth, ClientTimeout
from typing import List, Dict, Optional, Generator
import logging
import re
import asyncio
import time

logger = logging.getLogger(__name__)

class BookDownloader:
    def __init__(self, username: str = None, password: str = None):
        self.auth = BasicAuth(username, password) if username and password else None
        self.format_priority = ['txt', 'pdf', 'epub', 'Text PDF', 'JSON', 'chOCR', 'XML', 'djvu', 'hocr', 'ocr', 'xml']
        self.session = None  # We'll maintain a single session
        self.timeout = ClientTimeout(total=30)
        self.default_language = 'eng'
        self.lock_patterns = re.compile(r'lock|restricted|copyright|protected', re.IGNORECASE)
        self.encrypted_formats = re.compile(r'encrypted|acs|lcp', re.IGNORECASE)
        self.special_formats = {
            'txt': ['.txt', '_text.txt', '_djvu.txt', '_ocr.txt', '_hocr_searchtext.txt.gz'],
            'pdf': ['.pdf', '_text.pdf', '_encrypted.pdf', '_lcpdf'],
            'epub': ['.epub', '_lcp.epub'],
            'djvu': ['.djvu', '_text.djvu', '_djvu.xml'],
            'hocr': ['_hocr.html'],
            'chocr': ['_chocr.html.gz'],
            'ocr': ['_ocr.txt'],
            'xml': ['.xml', '_dc.xml', '_marc.xml', '_meta.xml', '_scandata.xml', '_files.xml'],
            'json': ['.json', '_page_numbers.json', '_events.json', '_hocr_pageindex.json.gz'],
            'text pdf': ['_text.pdf']
        }

    async def __aenter__(self):
        self.session = ClientSession(timeout=self.timeout)
        if self.auth:
            await self.login()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def login(self):
        """Proper login implementation with cookie handling"""
        if not self.auth:
            return False
            
        login_url = "https://archive.org/account/login"
        data = {
            "username": self.auth.login,
            "password": self.auth.password,
            "remember": "true",
            "action": "login",
            "submit": "Log in"
        }
        
        try:
            logger.debug(f'{login_url} {data}')
            async with self.session.post(login_url, data=data) as resp:
                if resp.status == 200:
                    # Verify login by checking cookies
                    cookies = resp.cookies
                    if 'logged-in-user' in cookies:
                        logger.info("Successfully logged in to archive.org")
                        return True
                logger.warning(f"Login failed with status {resp.status}")
                return False
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False

    async def check_url(self, url_info: tuple) -> tuple:
        """Check a single URL with proper session handling"""
        url, fmt = url_info
        try:
            async with self.session.head(url, allow_redirects=True) as resp:
                # Handle special cases
                if resp.status == 403:
                    # Try with GET if HEAD fails
                    async with self.session.get(url, allow_redirects=True) as get_resp:
                        return (url, fmt) if get_resp.status == 200 else (None, None)
                elif resp.status == 401:
                    # Check if this is an encrypted resource we could access if logged in
                    if self.auth and self.encrypted_formats.search(fmt):
                        return (url, fmt)
                    return (None, None)
                return (url, fmt) if resp.status == 200 else (None, None)
        except Exception as e:
            logger.debug(f"Failed to access {url}: {str(e)}")
            return (None, None)

    async def fetch_books(self, item: Dict) -> Dict:
        """Fetch and process books using the internal session"""
        try:
            query_parts = [
                'mediatype:texts',
                f'title:"{item.get("title")}"',
                f'language:{item.get("language", self.default_language)}'
            ]
            
            if author := item.get("author"):
                query_parts.append(f'creator:"{author}"')

            params = {
                "q": ' AND '.join(query_parts),
                "output": "json",
                "rows": 50,
                "fl[]": ["title", "creator", "identifier", "downloads", "format", "language", "year"]
            }

            async with self.session.get(
                'https://archive.org/advancedsearch.php',
                params=params,
                timeout=self.timeout
            ) as resp:
                if resp.status != 200:
                    return {"error": f"API error {resp.status}", "item": item}
                
                data = await resp.json()
                books = data.get('response', {}).get('docs', [])
                
                if not books:
                    return {"status": "not_found", "item": item}
                
                # Process books using internal session
                processed_books = await self.process_books_parallel(books, item)
                return processed_books

        except Exception as e:
            logger.error(f"Error fetching books: {e}")
            return {"error": str(e), "item": item}

    async def process_books_parallel(self, books: List[Dict], original_item: Dict) -> Dict:
        """Process books in parallel using internal session"""
        tasks = []
        for book in books:
            if self.is_downloadable(book):
                tasks.append(self.process_single_book(book))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        filtered = [result for result in results if result and isinstance(result, dict) and result.get('download_url')]
        
        # Deduplicate and sort
        deduplicated = self.deduplicate_books(filtered)
        return {
            "status": "success",
            "original_query": original_item,
            "books": sorted(deduplicated, key=lambda x: int(x.get('downloads', 0)), reverse=True),
            "format_priority": self.format_priority
        }

    async def process_single_book(self, book: Dict) -> Optional[Dict]:
        """Process a single book using internal session"""
        best_formats = list(self.select_best_format(book.get('format', [])))
        if not best_formats:
            return None

        verified_url = await self.find_working_url(book['identifier'], best_formats)
        if verified_url[0]:
            book['download_url'] = verified_url[0]
            book['chosen_format'] = verified_url[1]
            return book
        return None

    async def find_working_url(self, identifier: str, format_types: list) -> tuple:
        """Find working URL using internal session"""
        base = f"https://archive.org/download/{identifier}/{identifier}"
        urls_to_check = []
        
        for fmt in format_types:
            fmt = fmt.lower()
            if fmt in self.special_formats:
                for ext in self.special_formats[fmt]:
                    urls_to_check.append((f"{base}{ext}", fmt))
            else:
                urls_to_check.append((f"{base}.{fmt}", fmt))

        # Check URLs in parallel using internal session
        tasks = [self.check_url(url) for url in urls_to_check]
        results = await asyncio.gather(*tasks)
        
        for result in results:
            if result[0]:  # If URL is valid
                return result
        return (None, None)
    
    def is_downloadable(self, book: Dict) -> bool:
        """More lenient downloadable check"""
        identifier = book.get('identifier', '')
        formats = book.get('format', [])
        
        # Skip obviously restricted items
        if any(f.lower() in ['restricted', 'lending'] for f in formats):
            return False
            
        # Skip items with no formats
        if not formats:
            return False
            
        return True
    