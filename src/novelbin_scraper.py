import cloudscraper
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
import re # Import regex for chapter number extraction

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

def scrape_novel_table_of_contents(toc_url: str) -> dict | None:
    """
    Scrapes a novel's table of contents page to extract book metadata and chapter URLs.
    Returns a dictionary containing book title, author, and a list of chapters.
    """
    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(toc_url)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching ToC page: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    
    book_title = "Unknown Title"
    book_author = "Unknown Author"
    chapters = []

    # Find the main book container using schema.org microdata and specific classes
    book_container = soup.find('div', class_="col-novel-main", itemtype="http://schema.org/Book")
    
    if book_container:
        # Extract Book Title from h3 with class 'title'
        title_element = book_container.find('h3', class_="title")
        if title_element:
            book_title = title_element.text.strip()
        
        # Extract Book Author from the info list
        author_list_item = book_container.find('h3', string=lambda text: text and "Author:" in text)
        if author_list_item:
            author_element = author_list_item.find_next_sibling('a')
            if author_element:
                book_author = author_element.text.strip()

        # --- Direct Scraping of Chapter List ---
        chapter_list_container = book_container.find('div', id="list-chapter")
        if chapter_list_container:
            chapter_links = chapter_list_container.find_all('a', href=True)
            
            for link in chapter_links:
                href = link.get('href', '')
                title = link.get('title', 'No Title').strip()

                # Ensure it's a valid chapter link
                if '/chapter-' not in href:
                    continue

                chapter_num = 0
                # Extract chapter number from title (e.g., "Chapter 1 – ...")
                match = re.search(r'^Chapter (\d+)', title)
                if match:
                    chapter_num = int(match.group(1))

                chapters.append({
                    'title': title,
                    'url': href,
                    'chapter_number': chapter_num
                })
        else:
            print("Could not find the 'div#list-chapter' container.")
    else:
        print("Book container (div.col-novel-main with itemtype=\"http://schema.org/Book\") not found.")

    if not chapters:
        print("No chapters found or generated.")
        return None

    return {
        'book_title': book_title,
        'book_author': book_author,
        'chapters': chapters,
        'source_url': toc_url # The ToC URL is the book's source URL
    }

if __name__ == '__main__':
    # Example usage for single chapter scraper
    test_chapter_url = "https://novelbin.com/b/demons-diary/chapter-2" # Verified URL
    print(f"Attempting to scrape single chapter: {test_chapter_url}")
    chapter_text = scrape_novel_chapter(test_chapter_url)
    if chapter_text:
        print("Scraped content (first 500 chars):\n", chapter_text[:500])
    else:
        print("Failed to scrape single chapter content.")
    
    # Example usage for ToC scraper
    toc_test_url = "https://novelbin.com/b/demons-diary#tab-chapters-title"
    print(f"\nAttempting to scrape ToC: {toc_test_url}")
    book_data = scrape_novel_table_of_contents(toc_test_url)
    if book_data:
        print("\nBook Data:")
        print(f"  Title: {book_data['book_title']}")
        print(f"  Author: {book_data['book_author']}")
        print(f"  Source URL: {book_data['source_url']}")
        print(f"  Found {len(book_data['chapters'])} chapters.")
        for i, chapter in enumerate(book_data['chapters'][:5]): # Print first 5
            print(f"    {i+1}: {chapter['title']} (No. {chapter['chapter_number']}) - {chapter['url']}")
    else:
        print("Failed to scrape ToC.")