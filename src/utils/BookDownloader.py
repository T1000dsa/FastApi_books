from aiohttp import ClientSession
from fastapi import HTTPException
from bs4 import BeautifulSoup
import logging
import asyncio
from typing import List, Dict, Optional
import random

logger = logging.getLogger(__name__)

class BookLoader:
    def __init__(self, title: Optional[str] = None, limit: int = 10):
        self.title = title
        self.limit = limit
        self.cache_buster = random.randint(0, 99999)  # Prevent caching

        self.base_url = "https://www.gutenberg.org/ebooks/search/"
        self.params = {
            'query': self.title or '',
            'submit_search': 'Search',
        }

    async def search_books(self) -> List[Dict]:
        """Search with proper pagination and cache busting"""
        all_books = []
        page = 1
        
        async with ClientSession() as session:
            while len(all_books) < self.limit:
                # Add cache buster and page to params
                params = {**self.params, 
                         'page': page,
                         'cache_buster': self.cache_buster}
                
                try:
                    async with session.get(
                        self.base_url,
                        params=params,
                        headers={'User-Agent': 'Mozilla/5.0'}
                    ) as response:
                        if response.status != 200:
                            break
                            
                        html = await response.text()
                        books = self._parse_search_results(html)
                        
                        if not books:
                            break
                            
                        all_books.extend(books)
                        page += 1
                        
                        # Small delay between requests
                        await asyncio.sleep(0.5)
                        
                except Exception as e:
                    logger.error(f"Request failed: {e}")
                    break

            
        return all_books[:self.limit]

    def _parse_search_results(self, html: str) -> List[Dict]:
        """Parse the actual search results from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        books = []
        
        for item in soup.select('li.booklink'):
            try:
                book_id = item.find('a')['href'].split('/')[-1]
                title = item.select_one('.title').get_text(strip=True)
                author = item.select_one('.subtitle').get_text(strip=True) if item.select_one('.subtitle') else "Unknown"
                
                books.append({
                    'id': book_id,
                    'title': title,
                    'author': author,
                    'formats': self._get_formats(book_id)
                })
            except Exception as e:
                logger.warning(f"Failed to parse book item: {e}")
                continue
                
        return books

    def _get_formats(self, book_id: str) -> List[str]:
        """Generate format URLs without making requests"""
        base = f"https://www.gutenberg.org/files/{book_id}/"
        return [
            f"{base}{book_id}-0.txt",
            f"{base}{book_id}.txt",
            f"{base}{book_id}-8.txt",
            f"{base}{book_id}.txt.utf-8",
            f"https://www.gutenberg.org/ebooks/{book_id}.epub.noimages",
            f"https://www.gutenberg.org/ebooks/{book_id}.html.images"
        ]

    async def download_book(self, book_id: str, format: str = 'text') -> Optional[bytes]:
        """Download with proper error handling"""
        formats = {
            'text': [f"{book_id}-0.txt", f"{book_id}.txt", f"{book_id}-8.txt"],
            'epub': [f"{book_id}.epub.noimages"],
            'html': [f"{book_id}.html.images"]
        }
        
        if format not in formats:
            raise HTTPException(400, "Invalid format")
            
        base_url = f"https://www.gutenberg.org/files/{book_id}/" if format == 'text' \
                 else f"https://www.gutenberg.org/ebooks/"

        async with ClientSession() as session:
            for filename in formats[format]:
                url = f"{base_url}{filename}"
                try:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            return await resp.read()
                except Exception as e:
                    logger.warning(f"Failed to download {url}: {e}")
                    
        return None

    async def provide_books(self) -> List[Dict]:
        """Public interface with error handling"""
        try:
            books = await self.search_books()
            return books
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise HTTPException(500, "Book search failed")