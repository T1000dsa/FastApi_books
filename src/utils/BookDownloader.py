from aiohttp import ClientSession, ClientTimeout
from fastapi import HTTPException
from bs4 import BeautifulSoup
import logging
import asyncio
from typing import List, Dict, Optional
import random

logger = logging.getLogger(__name__)

class BookLoader:
    def __init__(self, title: Optional[str] = None, limit: int = 100):
        self.title = title
        self.limit = limit
        self.cache_buster = random.randint(0, 99999)
        self.base_url = "https://www.gutenberg.org/ebooks/search/"
        self.params = {
            'query': self.title or '',
            'submit_search': 'Search',
            'sort_order': 'release_date'  # Changed from 'downloads' to get more variety
        }
        self.max_pages_to_check = 20
        self.books_per_page = 25
        self.seen_books = set()
        self.last_book_ids = set()  # Track recent books to detect pagination loops

    async def search_books(self) -> List[Dict]:
        """Search with enhanced pagination and duplicate detection"""
        all_books = []
        page = 1
        retry_count = 0
        max_retries = 3
        duplicate_threshold = 3  # How many duplicate pages before stopping
        
        async with ClientSession() as session:
            while len(all_books) < self.limit and page <= self.max_pages_to_check:
                params = {
                    **self.params,
                    'page': page,
                    'cache_buster': self.cache_buster
                }
                
                try:
                    async with session.get(
                        self.base_url,
                        params=params,
                        headers={
                            'User-Agent': 'Mozilla/5.0',
                            'Accept': 'text/html,application/xhtml+xml'
                        },
                        timeout=ClientTimeout(total=15)
                    ) as response:
                        if response.status != 200:
                            logger.warning(f"Status {response.status} on page {page}")
                            if retry_count < max_retries:
                                retry_count += 1
                                await asyncio.sleep(2 ** retry_count)
                                continue
                            break
                            
                        html = await response.text()
                        books = self._parse_search_results(html)
                        
                        if not books:
                            logger.debug(f"No books found on page {page}")
                            break
                            
                        # Check if we're getting the same books repeatedly
                        current_page_ids = {book['id'] for book in books}
                        if current_page_ids.issubset(self.last_book_ids):
                            duplicate_threshold -= 1
                            if duplicate_threshold <= 0:
                                logger.info("Stopping due to repeated book sets")
                                break
                        
                        self.last_book_ids = current_page_ids
                        
                        # Filter duplicates and add new books
                        new_books = [
                            book for book in books 
                            if book['id'] not in self.seen_books
                        ]
                        
                        for book in new_books:
                            self.seen_books.add(book['id'])
                        
                        all_books.extend(new_books)
                        retry_count = 0
                        
                        logger.debug(
                            f"Page {page}: Added {len(new_books)} new books "
                            f"(Total: {len(all_books)}, Unique: {len(self.seen_books)})"
                        )
                        
                        if len(all_books) >= self.limit:
                            break
                            
                        # Try different sorting if we're not getting new books
                        if len(new_books) == 0 and page > 5:
                            self.params['sort_order'] = 'random'  # Try random sorting
                            logger.debug("Switching to random sorting")
                            
                        page += 1
                        await asyncio.sleep(random.uniform(1.5, 3.0))
                        
                except Exception as e:
                    logger.error(f"Error on page {page}: {e}")
                    if retry_count < max_retries:
                        retry_count += 1
                        await asyncio.sleep(2 ** retry_count)
                        continue
                    break

        logger.info(
            f"Finished searching. Found {len(all_books)} books "
            f"({len(self.seen_books)} unique) from {page-1} pages"
        )
        return all_books[:self.limit]

    def _parse_search_results(self, html: str) -> List[Dict]:
        """Enhanced parsing with better duplicate detection"""
        soup = BeautifulSoup(html, 'html.parser')
        books = []
        
        for item in soup.select('li.booklink'):
            try:
                link = item.find('a', href=True)
                if not link:
                    continue
                    
                href = link['href']
                if '/ebooks/' not in href:
                    continue
                    
                book_id = href.split('/')[-1]
                if not book_id.isdigit():
                    continue
                    
                title_elem = item.select_one('.title')
                author_elem = item.select_one('.subtitle')
                
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                author = author_elem.get_text(strip=True) if author_elem else "Unknown"
                
                # Skip foreign language books (optional)
                if '[French]' in title or '[German]' in title:
                    continue
                    
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

    async def provide_books(self) -> List[Dict]:
        """Public interface with multiple search strategies"""
        strategies = [
            {'sort_order': 'release_date'},
            {'sort_order': 'downloads'},
            {'sort_order': 'random'},
            {'sort_order': 'title'}
        ]
        
        all_books = []
        
        for strategy in strategies:
            if len(all_books) >= self.limit:
                break
                
            self.params.update(strategy)
            self.seen_books = set()  # Reset for new strategy
            self.last_book_ids = set()
            
            logger.info(f"Trying search strategy: {strategy}")
            
            try:
                books = await self.search_books()
                # Merge results while preserving uniqueness
                for book in books:
                    if book['id'] not in {b['id'] for b in all_books}:
                        all_books.append(book)
                        
                logger.info(f"Strategy found {len(books)} books (Total: {len(all_books)})")
                
                if len(all_books) >= self.limit:
                    break
                    
            except Exception as e:
                logger.error(f"Strategy failed: {strategy} - {e}")
                continue
                
        return all_books[:self.limit]
    
    def _get_formats(self, book_id: str) -> List[str]:
        """Smart format URL generation with fallbacks"""
        base_formats = [
            f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",  # Most common
            #f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt",
            #f"https://www.gutenberg.org/ebooks/{book_id}.txt.utf-8",
            #f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt.utf-8",
            #f"https://www.gutenberg.org/ebooks/{book_id}.html.noimages",
        ]
        
        # Only return formats that are likely to exist based on book ID
        if int(book_id) < 10:  # Very early books often have different formats
            return base_formats + [
                f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt",
                f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt.utf-8"
            ]
        return base_formats