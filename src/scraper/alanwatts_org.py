"""Scrape transcripts from alanwatts.org/category/searchable/."""

import re
import time

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://alanwatts.org"
SEARCHABLE_URL = f"{BASE_URL}/category/searchable/"
HEADERS = {
    "User-Agent": "AlanWattsLibrary/1.0 (educational research project)"
}


def get_transcript_urls(max_pages: int = 20) -> list[dict]:
    """Get all transcript page URLs from the searchable category."""
    all_links = []
    page = 1

    while page <= max_pages:
        url = f"{SEARCHABLE_URL}page/{page}/" if page > 1 else SEARCHABLE_URL
        print(f"  Fetching page {page}: {url}")

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                print(f"  Page {page}: HTTP {resp.status_code}, stopping pagination")
                break

            soup = BeautifulSoup(resp.text, "html.parser")

            # Find article links
            articles = soup.find_all("article")
            if not articles:
                # Try finding post entries
                articles = soup.find_all(class_=re.compile(r"post|entry|hentry"))

            if not articles:
                print(f"  No articles found on page {page}, stopping")
                break

            page_links = []
            for article in articles:
                link = article.find("a", href=True)
                title_tag = article.find(["h2", "h3", "h1"])
                if link and title_tag:
                    title = title_tag.get_text(strip=True)
                    href = link["href"]
                    if href.startswith("/"):
                        href = BASE_URL + href
                    page_links.append({"url": href, "title": title})

            if not page_links:
                # Fallback: find all links in main content
                main = soup.find(["main", "div"], class_=re.compile(r"content|main|posts"))
                if main:
                    for a in main.find_all("a", href=True):
                        href = a["href"]
                        text = a.get_text(strip=True)
                        if (href.startswith(BASE_URL) and text and len(text) > 5 and
                                "/category/" not in href and "/tag/" not in href and
                                "/page/" not in href):
                            if href.startswith("/"):
                                href = BASE_URL + href
                            page_links.append({"url": href, "title": text})

            all_links.extend(page_links)
            print(f"    Found {len(page_links)} links")

            # Check for next page
            next_link = soup.find("a", class_=re.compile(r"next"))
            if not next_link:
                next_link = soup.find("a", string=re.compile(r"Next|Older|›|»"))
            if not next_link:
                break

            page += 1
            time.sleep(2)  # Respectful rate limiting

        except Exception as e:
            print(f"  Error on page {page}: {e}")
            break

    # Deduplicate by URL
    seen = set()
    unique = []
    for link in all_links:
        if link["url"] not in seen:
            seen.add(link["url"])
            unique.append(link)

    return unique


def scrape_transcript(url: str) -> str | None:
    """Extract transcript text from an individual page."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove scripts, styles, sidebar, navigation
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()
        for tag in soup.find_all(class_=re.compile(r"sidebar|widget|nav|menu|comment")):
            tag.decompose()

        # Find main content area
        content = (
            soup.find("div", class_=re.compile(r"entry-content|post-content|article-content")) or
            soup.find("article") or
            soup.find("div", class_="content") or
            soup.find("main")
        )

        if not content:
            return None

        text = content.get_text(separator="\n", strip=True)

        # Clean up
        lines = []
        for line in text.split("\n"):
            line = line.strip()
            if line and len(line) > 2:
                # Skip navigation/metadata lines
                if any(skip in line.lower() for skip in
                       ["share this", "tweet", "facebook", "pinterest",
                        "related posts", "leave a comment", "posted in",
                        "tagged", "category:", "comments"]):
                    continue
                lines.append(line)

        text = "\n".join(lines)
        return text if len(text) > 200 else None

    except Exception as e:
        print(f"  Error scraping {url}: {e}")
        return None


def scrape_all() -> list[dict]:
    """Scrape all transcripts from alanwatts.org."""
    print("Getting transcript URLs from alanwatts.org...")
    links = get_transcript_urls()
    print(f"Found {len(links)} unique transcript pages\n")

    results = []
    for i, link in enumerate(links):
        print(f"  [{i+1}/{len(links)}] {link['title'][:60]}...", end=" ")
        text = scrape_transcript(link["url"])
        if text:
            results.append({
                "title": link["title"],
                "text": text,
                "url": link["url"],
            })
            print(f"OK ({len(text):,} chars)")
        else:
            print("SKIP")
        time.sleep(2)  # Respectful

    return results


if __name__ == "__main__":
    results = scrape_all()
    print(f"\nTotal: {len(results)} transcripts")
    total = sum(len(r["text"]) for r in results)
    print(f"Total chars: {total:,}")
