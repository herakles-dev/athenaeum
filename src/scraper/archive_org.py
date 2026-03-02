"""Download metadata and any available text from Internet Archive Alan Watts collections."""

import json
import time
import requests

HEADERS = {"User-Agent": "AlanWattsLibrary/1.0 (educational research)"}

COLLECTIONS = [
    "alanwattscollection",
    "Alan_Watts_67_Lectures",
]


def get_collection_items(collection_id: str) -> list[dict]:
    """Get items from an Internet Archive collection."""
    url = f"https://archive.org/advancedsearch.php"
    params = {
        "q": f"collection:{collection_id}",
        "fl[]": ["identifier", "title", "description", "date", "mediatype"],
        "rows": 500,
        "output": "json",
    }

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        data = resp.json()
        docs = data.get("response", {}).get("docs", [])
        return docs
    except Exception as e:
        print(f"  Error fetching collection {collection_id}: {e}")
        return []


def get_item_text_files(identifier: str) -> list[dict]:
    """Get text files from an Internet Archive item."""
    url = f"https://archive.org/metadata/{identifier}/files"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        files = resp.json().get("result", [])
        text_files = [
            f for f in files
            if f.get("format") in ["Text", "DjVuTXT", "SubRip"] or
               f.get("name", "").endswith((".txt", ".srt", ".vtt"))
        ]
        return text_files
    except Exception as e:
        return []


def download_text_file(identifier: str, filename: str) -> str | None:
    """Download a text file from Internet Archive."""
    url = f"https://archive.org/download/{identifier}/{filename}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code == 200 and len(resp.text) > 100:
            return resp.text
    except Exception:
        pass
    return None


def scrape_all() -> list[dict]:
    """Get all available text content from Internet Archive collections."""
    results = []

    for collection_id in COLLECTIONS:
        print(f"\nScanning collection: {collection_id}")
        items = get_collection_items(collection_id)
        print(f"  Found {len(items)} items")

        for item in items:
            identifier = item.get("identifier", "")
            title = item.get("title", identifier)

            text_files = get_item_text_files(identifier)
            if text_files:
                print(f"  [{identifier}] {title}: {len(text_files)} text files")
                for tf in text_files[:3]:  # Max 3 text files per item
                    fname = tf.get("name", "")
                    text = download_text_file(identifier, fname)
                    if text and len(text) > 200:
                        results.append({
                            "title": title,
                            "text": text,
                            "url": f"https://archive.org/details/{identifier}",
                            "identifier": identifier,
                            "filename": fname,
                        })
                        print(f"    {fname}: {len(text):,} chars")
                time.sleep(1)
            time.sleep(0.5)

    return results


if __name__ == "__main__":
    results = scrape_all()
    print(f"\nTotal: {len(results)} text files")
    total = sum(len(r["text"]) for r in results)
    print(f"Total chars: {total:,}")
