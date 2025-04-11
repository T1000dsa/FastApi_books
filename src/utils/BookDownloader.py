from aiohttp import ClientSession
from collections import defaultdict
from typing import List, Dict, Optional, Generator
import logging
import re

logger = logging.getLogger(__name__)

class BookDownloader:
    def __init__(self):
        self.format_priority = ['txt', 'pdf', 'epub', 'djvu', 'Text PDF', 'JSON']
        self.default_language = 'spa'
        self.lock_patterns = re.compile(r'lock|restricted|copyright|protected', re.IGNORECASE)
        self.special_formats = {
            'djvu': ['.djvu', '_djvu.txt', '_text.djvu'],
            'txt': ['_text.txt', '.txt', '_djvu.txt'],
            'pdf': ['.pdf', '_text.pdf']
        }

    async def fetch_books(self, session: ClientSession, item: Dict) -> Dict:
        """Fetch and process books for a single title/author"""
        try:
            # Build query with language and mediatype filters
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

            async with session.get('https://archive.org/advancedsearch.php', params=params) as resp:
                if resp.status != 200:
                    return {"error": f"API error {resp.status}", "item": item}
                
                data = await resp.json()
                books = data.get('response', {}).get('docs', [])
                
                if not books:
                    return {"status": "not_found", "item": item}
                
                return await self.process_books(session, books, item)

        except Exception as e:
            logger.error(f"Error fetching books: {str(e)}")
            return {"error": str(e), "item": item}

    async def process_books(self, session: ClientSession, books: List[Dict], original_item: Dict) -> Dict:
        """Process books with thorough URL verification"""
        filtered = []
        for book in books:
            if not self.is_downloadable(book):
                continue
            #logger.info(book)
            logger.info(0)
            best_format = next(self.select_best_format(book.get('format', [])), None)
            if not best_format:
                continue

            logger.info(f'{book['identifier']} {best_format}')
            verified_url = await self.find_working_url(session, book['identifier'], best_format)
            logger.info(f"{verified_url=}")
            
            if verified_url:
                book['download_url'] = verified_url
                book['chosen_format'] = best_format
                filtered.append(book)

        # Deduplication logic remains the same
        deduplicated = set(filtered)
        
        return {
            "status": "success",
            "original_query": original_item,
            "books": sorted(deduplicated, key=lambda x: int(x.get('downloads', 0)), reverse=True),
            "format_priority": self.format_priority
        }

    async def find_working_url(self, session: ClientSession, identifier: str, format_type: str) -> Optional[str]:
        """Try all possible URL patterns for a format until finding one that works"""
        for url in self.generate_all_possible_urls(identifier, format_type):
            if await self.verify_download_url(session, url):
                return url
        return None

    def generate_all_possible_urls(self, identifier: str, format_type: str) -> Generator[str, None, None]:
        """Generate all known URL patterns for a given format type"""
        base = f"https://archive.org/download/{identifier}/{identifier}"
        format_type = format_type.lower()
        
        # Special cases first
        if format_type in self.special_formats:
            for ext in self.special_formats[format_type]:
                yield f"{base}{ext}"
        
        # Standard patterns
        if format_type == 'txt':
            yield f"{base}_text.txt"
            yield f"{base}.txt"
        elif format_type == 'pdf':
            yield f"{base}.pdf"
            yield f"{base}_text.pdf"
        else:
            yield f"{base}.{format_type}"

    async def verify_download_url(self, session: ClientSession, url: str) -> bool:
        """Verify URL exists with retries and redirect following"""
        try:
            async with session.head(url, allow_redirects=True) as resp:
                return resp.status == 200
        except:
            return False


    def select_best_format(self, available_formats: List[str]) -> Generator[str, None, None]:
        """Select format based on priority list"""
        available_lower = [f.lower() for f in available_formats]
        for fmt in self.format_priority:
            if fmt.lower() in available_lower:
                yield fmt

    def build_download_url(self, identifier: str, format_type: str) -> Generator[str, None, None]:
        """Construct possible URLs for the specific format"""
        base = f"https://archive.org/download/{identifier}/{identifier}"
        
        # Handle different format types
        if format_type.lower() == 'txt':
            yield f"{base}_text.txt"
            yield f"{base}.txt"  # Some books use this pattern
        elif format_type.lower() == 'pdf':
            yield f"{base}.pdf"
            yield f"{base}_text.pdf"  # Alternative pattern
        else:
            yield f"{base}.{format_type.lower()}"

    
    def is_downloadable(self, book: Dict) -> bool:
        """Check if book appears downloadable"""
        identifier = book.get('identifier', '')
        
        # Check for lock patterns in identifier
        if self.lock_patterns.search(identifier):
            return False
            
        # Check if we have any formats
        if not book.get('format'):
            return False
            
        return True

downloader = BookDownloader()