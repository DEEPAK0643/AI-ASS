-- ===================================================================
-- J.A.R.V.I.S. SUPABASE DATABASE SCHEMA
-- Run this in your Supabase SQL Editor (https://app.supabase.com)
-- ===================================================================

-- 1. Conversation & Command History
CREATE TABLE IF NOT EXISTS jarvis_conversations (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    sender TEXT NOT NULL,           -- 'USER' or 'JARVIS'
    message TEXT NOT NULL,
    action TEXT DEFAULT NULL        -- e.g. 'screenshot', 'youtube', 'volume'
);

-- Index for speedy chronological history retrieval
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON jarvis_conversations (created_at DESC);

-- 2. Long-term User Memories & Preferences
CREATE TABLE IF NOT EXISTS jarvis_memories (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    key TEXT NOT NULL,              -- e.g. 'favorite_music', 'project_name'
    value TEXT NOT NULL,            -- e.g. 'AC/DC - Back in Black', 'Project Titan'
    category TEXT DEFAULT 'general' -- 'preference', 'fact', 'reminder', 'system'
);

CREATE INDEX IF NOT EXISTS idx_memories_key ON jarvis_memories (key);

-- 3. System Telemetry Logs (Health & Performance Monitoring)
CREATE TABLE IF NOT EXISTS jarvis_telemetry (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    cpu_percent FLOAT NOT NULL,
    ram_percent FLOAT NOT NULL,
    disk_percent FLOAT NOT NULL,
    battery_percent FLOAT DEFAULT 100
);

CREATE INDEX IF NOT EXISTS idx_telemetry_created_at ON jarvis_telemetry (created_at DESC);

-- 4. Enable Row Level Security (RLS) & Public Access Policies for Anon / Service
ALTER TABLE jarvis_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_telemetry ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read jarvis_conversations" 
    ON jarvis_conversations FOR SELECT USING (true);
CREATE POLICY "Allow public insert jarvis_conversations" 
    ON jarvis_conversations FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public read jarvis_memories" 
    ON jarvis_memories FOR SELECT USING (true);
CREATE POLICY "Allow public insert jarvis_memories" 
    ON jarvis_memories FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update jarvis_memories" 
    ON jarvis_memories FOR UPDATE USING (true);

CREATE POLICY "Allow public read jarvis_telemetry" 
    ON jarvis_telemetry FOR SELECT USING (true);
CREATE POLICY "Allow public insert jarvis_telemetry" 
    ON jarvis_telemetry FOR INSERT WITH CHECK (true);
