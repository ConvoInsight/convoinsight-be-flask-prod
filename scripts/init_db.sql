-- ConvoInsight Database Initialization Script
-- This script runs on first PostgreSQL container startup

-- Create schema for user datasets if needed
CREATE SCHEMA IF NOT EXISTS user_datasets;

-- Example: Create a sample table for testing
CREATE TABLE IF NOT EXISTS public.sample_data (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    value NUMERIC(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO public.sample_data (name, value) VALUES
    ('Test Item 1', 100.50),
    ('Test Item 2', 250.75),
    ('Test Item 3', 300.00)
ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO convoinsight;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO convoinsight;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA user_datasets TO convoinsight;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA user_datasets TO convoinsight;

-- Create extension for UUID support (useful for session IDs)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

COMMENT ON DATABASE convoinsight IS 'ConvoInsight Backend Database - Local Development';
