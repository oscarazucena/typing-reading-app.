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

        # Find the main content area of the novel chapter.
        # This will likely require inspection of NovelBin's HTML structure.
        # For now, let's assume the main content is within a div with a specific class or ID.
        # We'll need to refine this selector later by inspecting a sample NovelBin page.
        content_div = soup.find('div', class_='chapter-content') # Common class, needs verification
        
        if content_div:
            # Extract text, remove script tags and other unwanted elements
            for script_or_style in content_div(['script', 'style', 'header', 'footer', 'nav']):
                script_or_style.extract()
            text_content = content_div.get_text(separator='\n', strip=True)
            return text_content
        else:
            print(f"Could not find chapter content in {url}")
            return None
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None
    finally:
        time.sleep(2) # Rate-limiting: wait for 2 seconds after each request

if __name__ == '__main__':
    # Example usage (will need a real NovelBin URL for testing)
    # This part will be updated once we have a sample URL to test against.
    test_url = "https://www.novelbin.org/novel/the-authors-pov-novel/chapter-1.html" # Placeholder
    print(f"Attempting to scrape: {test_url}")
    chapter_text = scrape_novel_chapter(test_url)
    if chapter_text:
        print("Scraped content (first 500 chars):\n", chapter_text[:500])
    else:
        print("Failed to scrape content.")
