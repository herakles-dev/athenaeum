# data/

Place your corpus data files here before running the ingestion pipeline.

## Expected formats

### JSON transcripts (github-style)
```
data/
  github-AUTHOR/
    transcript-1.json
    transcript-2.json
    ...
```

Each JSON file should contain:
```json
{
  "title": "Lecture Title",
  "series": "Series Name",
  "text": "Full transcript text...",
  "source_url": "https://...",
  "video_url": "https://..."
}
```

### Plain text transcripts
```
data/
  transcripts/
    SERIES_NAME/
      lecture-1.txt
      lecture-2.txt
```

## Ingestion pipeline

After placing data here, run:
```bash
make run-pipeline   # load → chunk → embed → cluster
```

Or step by step:
```bash
PYTHONPATH=. python3 -c "from src.ingestion.loader import run; run()"
PYTHONPATH=. python3 -c "from src.ingestion.chunker import run; run()"
PYTHONPATH=. python3 -c "from src.ingestion.embed import run; run()"
PYTHONPATH=. python3 -c "from src.ingestion.cluster import run; run()"
```

**Note**: Embedding is expensive. The loader uses SHA-256 dedup — running it multiple
times is safe, only new/changed content will be embedded.
