from aiohttp import ClientSession
from fastapi import HTTPException
from bs4 import BeautifulSoup
import logging
import asyncio
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class BookLoader:
    def __init__(self, title: Optional[str] = None, author: Optional[str] = None, 
                 limit: int = 10):
        self.title = title
        self.author = author
        self.limit = limit

        self.params = {
            'query': self.title or '',
            'submit_search': 'Search'
        }

        self.base_urls = {
            'search': "https://www.gutenberg.org/ebooks/search/",
            'files': "https://www.gutenberg.org/files/{book_id}/",
            'ebooks': "https://www.gutenberg.org/ebooks/{book_id}"
        }

        self.file_patterns = [
            "{book_id}-0.txt",  # Most common
            "{book_id}.txt",
            "{book_id}-8.txt",  # Alternative numbering
            "{book_id}.txt.utf-8"
        ]

    async def search_books(self) -> List[Dict]:
        """Search for books and return metadata"""
        async with ClientSession() as session:
            async with session.get(
                self.base_urls['search'], 
                params=self.params
            ) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail="Failed to fetch books from Gutenberg"
                    )
                
                html = await response.text()
                return await self._parse_search_results(html)

    async def _parse_search_results(self, html: str) -> List[Dict]:
        """Parse HTML search results into book metadata"""
        soup = BeautifulSoup(html, 'html.parser')
        books = []
        
        for result in soup.select('li.booklink'):
            title_elem = result.select_one('.title')
            author_elem = result.select_one('.subtitle')
            link_elem = result.find('a')

            await asyncio.sleep(0.5)
            
            if not all([title_elem, link_elem]):
                continue
                
            book_id = link_elem['href'].split('/')[-1]
            books.append({
                'id': book_id,
                'title': title_elem.text.strip(),
                'author': author_elem.text.strip() if author_elem else "Unknown",
                'formats': self._get_available_formats(book_id)
            })
            
            if len(books) >= self.limit:
                break
                
        return books

    def _get_available_formats(self, book_id: str) -> List[str]:
        """Generate available format URLs for a book"""
        return [
            f"{self.base_urls['files'].format(book_id=book_id)}{pattern.format(book_id=book_id)}"
            for pattern in self.file_patterns
        ]

    async def download_book(self, book_id: str, format: str = 'text') -> Optional[bytes]:
        """Download a book in the specified format"""
        if format == 'text':
            return await self._download_text(book_id)
        elif format == 'epub':
            return await self._download_epub(book_id)
        else:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported format. Use 'text' or 'epub'"
            )

    async def _download_text(self, book_id: str) -> Optional[bytes]:
        """Try downloading text version using known patterns"""
        async with ClientSession() as session:
            for pattern in self.file_patterns:
                url = f"{self.base_urls['files'].format(book_id=book_id)}{pattern.format(book_id=book_id)}"
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.read()
        
        # Fallback to HTML if no text version found
        return await self._download_html(book_id)

    async def _download_epub(self, book_id: str) -> Optional[bytes]:
        """Download EPUB version"""
        url = f"{self.base_urls['ebooks'].format(book_id=book_id)}.epub.noimages"
        async with ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
        return None

    async def _download_html(self, book_id: str) -> Optional[bytes]:
        """Download HTML version as fallback"""
        url = f"{self.base_urls['ebooks'].format(book_id=book_id)}.html.images"
        async with ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
        return None

    async def provide_books(self) -> List[Dict]:
        """Main method to search and get book metadata"""
        try:
            books = await self.search_books()
            return books[:self.limit]
        except Exception as e:
            logger.error(f"Error fetching books: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch books"
            )