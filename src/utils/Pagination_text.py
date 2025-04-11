from typing import List, Tuple

def split_text_into_pages(text: str, chars_per_page: int = 8000) -> Tuple[List[str], int]:
    """Split text into pages of approximately chars_per_page characters without breaking words.
    
    Args:
        text: The text to split
        chars_per_page: Target characters per page
    
    Returns:
        Tuple of (pages, count) where:
        - pages: List of text chunks
        - count: Total number of pages
    """
    pages = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        # Calculate potential end position
        end = min(start + chars_per_page, text_length)
        
        # If we're at the end of the text, add the remaining text
        if end == text_length:
            pages.append(text[start:end])
            break
            
        # Find the last space or newline before the end position
        last_break = end
        while last_break > start and text[last_break] not in (' ', '\n'):
            last_break -= 1
            
        # If we found a break character, use that position
        if last_break > start:
            pages.append(text[start:last_break])
            start = last_break + 1  # Skip the break character
        else:
            # No break found - force split at chars_per_page (unavoidable word break)
            pages.append(text[start:end])
            start = end
    
    return pages, len(pages)