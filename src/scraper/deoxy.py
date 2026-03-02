"""Scrape Alan Watts essays and lectures from deoxy.org mirror (jacobsm.com)."""

import hashlib
import re
import time

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.jacobsm.com/deoxy/deoxy.org"

# Known Alan Watts pages on deoxy.org mirror
WATTS_PAGES = [
    ("w_lectur.htm", "Lecture on Zen"),
    ("w_psyrel.htm", "Psychedelics and Religious Experience"),
    ("w_spcnsr.htm", "The New Alchemy"),
    ("w_murder.htm", "Murder in the Kitchen"),
    ("w_zen.htm", "Beat Zen, Square Zen and Zen"),
    ("w_moment.htm", "This Is the Moment"),
    ("w_ego.htm", "The Ego"),
    ("w_noth.htm", "Nothingness"),
    ("w_nature.htm", "Man and Nature"),
    ("w_web.htm", "The Web of Life"),
    ("w_tao.htm", "The Tao"),
    ("w_swim.htm", "Swimming Headless"),
    ("w_death.htm", "Death"),
    ("w_goddes.htm", "The World as God"),
    ("w_drugs.htm", "Drugs"),
    ("w_dream.htm", "The Dream of Life"),
    ("w_void.htm", "The Void"),
    ("w_music.htm", "Music and Life"),
    ("w_myth.htm", "The Myth of Myself"),
    ("w_joking.htm", "The Joker"),
    ("w_celeb.htm", "Celebration"),
    ("w_polari.htm", "Polarities"),
    ("w_cntrol.htm", "Illusion of Control"),
    ("w_relig.htm", "What is Religion"),
]


def scrape_page(path: str) -> str | None:
    """Fetch and extract text content from a deoxy.org page."""
    url = f"{BASE_URL}/{path}"
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "AlanWattsLibrary/1.0 (research project)"
        })
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove scripts, styles, navigation
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()

        # Get main content - try common containers
        content = soup.find("body")
        if not content:
            return None

        text = content.get_text(separator="\n", strip=True)

        # Clean up
        lines = []
        for line in text.split("\n"):
            line = line.strip()
            if line and len(line) > 2:
                lines.append(line)
        text = "\n".join(lines)

        # Skip if too short (probably a redirect or error page)
        if len(text) < 200:
            return None

        return text

    except Exception as e:
        print(f"  Error scraping {url}: {e}")
        return None


def scrape_watts_index() -> list[dict]:
    """Discover additional pages from the Watts index page."""
    url = f"{BASE_URL}/watts.htm"
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "AlanWattsLibrary/1.0 (research project)"
        })
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        pages = []
        known_paths = {p[0] for p in WATTS_PAGES}

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.startswith("w_") and href.endswith(".htm") and href not in known_paths:
                title = link.get_text(strip=True)
                if title and len(title) > 3:
                    pages.append((href, title))
                    known_paths.add(href)

        return pages
    except Exception as e:
        print(f"  Error fetching index: {e}")
        return []


def scrape_all() -> list[dict]:
    """Scrape all known Alan Watts pages from deoxy.org mirror."""
    results = []

    # Discover additional pages from index
    print("Checking deoxy.org index for additional pages...")
    extra_pages = scrape_watts_index()
    all_pages = WATTS_PAGES + extra_pages
    print(f"Found {len(all_pages)} total pages to scrape")

    for path, title in all_pages:
        print(f"  Scraping: {title} ({path})")
        text = scrape_page(path)
        if text:
            results.append({
                "title": title,
                "text": text,
                "url": f"{BASE_URL}/{path}",
                "source_path": path,
            })
            print(f"    Got {len(text):,} chars")
        else:
            print(f"    Skipped (no content)")
        time.sleep(1.5)  # Respectful rate limiting

    return results


if __name__ == "__main__":
    results = scrape_all()
    print(f"\nTotal scraped: {len(results)} pages")
    total_chars = sum(len(r["text"]) for r in results)
    print(f"Total characters: {total_chars:,}")
