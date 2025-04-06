from typing import List

def split_text_into_pages(text: str, chars_per_page: int = 2000) -> List[str]:
    """Split text into chunks of `chars_per_page` characters."""
    pages = []
    for i in range(0, len(text), chars_per_page):
        pages.append(text[i:i + chars_per_page])
    return pages