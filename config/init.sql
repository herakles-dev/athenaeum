-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Sources table
CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url TEXT,
    source_type VARCHAR(50) NOT NULL, -- 'github', 'youtube', 'website', 'archive_org', 'whisper'
    scraped_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Transcripts table (full documents)
CREATE TABLE IF NOT EXISTS transcripts (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES sources(id),
    title VARCHAR(500) NOT NULL,
    series VARCHAR(255),
    full_text TEXT NOT NULL,
    year INTEGER,
    duration_seconds INTEGER,
    source_url TEXT,
    video_url TEXT,
    content_hash VARCHAR(64) NOT NULL, -- SHA-256 for dedup
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(content_hash)
);

-- Chunks table (for vector search)
CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    transcript_id INTEGER REFERENCES transcripts(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    token_count INTEGER,
    embedding vector(768), -- text-embedding-3-large dimension
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create HNSW index for fast similarity search
CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Index for transcript lookups
CREATE INDEX IF NOT EXISTS idx_transcripts_source ON transcripts(source_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_series ON transcripts(series);
CREATE INDEX IF NOT EXISTS idx_transcripts_hash ON transcripts(content_hash);
CREATE INDEX IF NOT EXISTS idx_chunks_transcript ON chunks(transcript_id);

-- Topics table (auto-tagged)
CREATE TABLE IF NOT EXISTS topics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Many-to-many: transcripts <-> topics
CREATE TABLE IF NOT EXISTS transcript_topics (
    transcript_id INTEGER REFERENCES transcripts(id) ON DELETE CASCADE,
    topic_id INTEGER REFERENCES topics(id) ON DELETE CASCADE,
    relevance_score FLOAT DEFAULT 0.0,
    PRIMARY KEY (transcript_id, topic_id)
);
