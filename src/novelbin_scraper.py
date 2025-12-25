import cloudscraper
from bs4 import BeautifulSoup
import time

def scrape_novel_chapter(url: str) -> str | None:
    """
    Scrapes a novel chapter from the given URL using cloudscraper and BeautifulSoup.
    Includes a rate-limiting sleep.
    """
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the main content area of the novel chapter using its unique ID.
        content_div = soup.find('div', id='chr-content') # Verified ID for chapter text
        
        if content_div:
            # The new selector is precise enough that we may not need the extra cleanup.
            # Extract text, remove script tags and other unwanted elements
            for script_or_style in content_div(['script', 'style']):
                script_or_style.extract()
            text_content = content_div.get_text(separator='\n', strip=True)
            return text_content
        else:
            print(f"Could not find chapter content div with id='chr-content' in {url}")
            return None
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None
    finally:
        time.sleep(2) # Rate-limiting: wait for 2 seconds after each request

if __name__ == '__main__':
    # Example usage (will need a real NovelBin URL for testing)
    test_url = "https://novelbin.com/b/demons-diary/chapter-2" # Verified URL
    print(f"Attempting to scrape: {test_url}")
    chapter_text = scrape_novel_chapter(test_url)
    if chapter_text:
        print("Scraped content (first 500 chars):\n", chapter_text[:500])
    else:
        print("Failed to scrape content.")