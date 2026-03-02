"""Extract transcripts from Alan Watts YouTube videos."""

import json
import re
import subprocess
import time


def get_channel_video_ids(channel_url: str = "https://www.youtube.com/@AlanWattsOrg", max_videos: int = 500) -> list[str]:
    """Get video IDs from a YouTube channel using yt-dlp."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--print", "id", "--print", "title",
             "--playlist-end", str(max_videos), channel_url],
            capture_output=True, text=True, timeout=120
        )
        lines = result.stdout.strip().split("\n")
        # yt-dlp prints id then title alternating
        videos = []
        for i in range(0, len(lines) - 1, 2):
            vid_id = lines[i].strip()
            title = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if vid_id and len(vid_id) == 11:
                videos.append({"id": vid_id, "title": title})
        return videos
    except Exception as e:
        print(f"Error getting channel videos: {e}")
        return []


def get_transcript_ytdlp(video_id: str) -> str | None:
    """Get transcript using yt-dlp subtitle download."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--write-auto-sub", "--sub-lang", "en",
             "--skip-download", "--sub-format", "vtt",
             "-o", "/tmp/aw_%(id)s",
             f"https://www.youtube.com/watch?v={video_id}"],
            capture_output=True, text=True, timeout=30
        )

        # Read the VTT file
        import glob
        vtt_files = glob.glob(f"/tmp/aw_{video_id}*.vtt")
        if not vtt_files:
            return None

        with open(vtt_files[0]) as f:
            vtt_content = f.read()

        # Clean VTT to plain text
        text = clean_vtt(vtt_content)

        # Cleanup temp file
        for f in vtt_files:
            import os
            os.remove(f)

        return text if len(text) > 100 else None

    except Exception as e:
        print(f"  yt-dlp error for {video_id}: {e}")
        return None


def get_transcript_api(video_id: str) -> str | None:
    """Get transcript using youtube-transcript-api."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id, languages=["en"])

        # Combine all text segments
        text_parts = []
        for snippet in transcript.snippets:
            text_parts.append(snippet.text)

        text = " ".join(text_parts)

        # Clean up auto-generated artifacts
        text = re.sub(r'\[.*?\]', '', text)  # Remove [Music], [Applause] etc
        text = re.sub(r'\s+', ' ', text).strip()

        return text if len(text) > 100 else None

    except Exception as e:
        return None


def clean_vtt(vtt_content: str) -> str:
    """Convert VTT subtitle content to clean plain text."""
    lines = vtt_content.split("\n")
    text_lines = []
    seen = set()

    for line in lines:
        line = line.strip()
        # Skip headers, timestamps, empty lines
        if not line or line.startswith("WEBVTT") or line.startswith("Kind:") or \
           line.startswith("Language:") or "-->" in line or line.isdigit():
            continue
        # Remove VTT tags
        line = re.sub(r'<[^>]+>', '', line)
        line = re.sub(r'\[.*?\]', '', line)
        line = line.strip()
        if line and line not in seen:
            seen.add(line)
            text_lines.append(line)

    return " ".join(text_lines)


def search_and_extract(query: str = "Alan Watts lecture full", max_results: int = 50) -> list[dict]:
    """Search YouTube for Alan Watts content and extract transcripts."""
    try:
        result = subprocess.run(
            ["yt-dlp", f"ytsearch{max_results}:{query}",
             "--flat-playlist", "--print", "id", "--print", "title"],
            capture_output=True, text=True, timeout=60
        )
        lines = result.stdout.strip().split("\n")
        videos = []
        for i in range(0, len(lines) - 1, 2):
            vid_id = lines[i].strip()
            title = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if vid_id and len(vid_id) == 11:
                videos.append({"id": vid_id, "title": title})
        return videos
    except Exception as e:
        print(f"Search error: {e}")
        return []


def extract_all(max_videos: int = 500) -> list[dict]:
    """Extract transcripts from Alan Watts YouTube channel."""
    print("Getting video list from Alan Watts Org channel...")
    videos = get_channel_video_ids(max_videos=max_videos)
    print(f"Found {len(videos)} videos")

    results = []
    for i, video in enumerate(videos):
        print(f"  [{i+1}/{len(videos)}] {video['title'][:60]}...", end=" ")

        # Try API first (faster, cleaner), fall back to yt-dlp
        text = get_transcript_api(video["id"])
        method = "api"
        if not text:
            text = get_transcript_ytdlp(video["id"])
            method = "yt-dlp"

        if text:
            results.append({
                "video_id": video["id"],
                "title": video["title"],
                "text": text,
                "url": f"https://www.youtube.com/watch?v={video['id']}",
                "method": method,
            })
            print(f"OK ({len(text):,} chars via {method})")
        else:
            print("SKIP (no transcript)")

        time.sleep(0.5)

    return results


if __name__ == "__main__":
    results = extract_all(max_videos=20)  # Test with 20
    print(f"\nExtracted: {len(results)} transcripts")
