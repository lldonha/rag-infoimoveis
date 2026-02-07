-- Schema para RAG InfoImóveis
-- PostgreSQL + pgvector

-- Habilitar extensão pgvector
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabela principal de imóveis
CREATE TABLE IF NOT EXISTS properties (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_url TEXT NOT NULL UNIQUE,
    scraped_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Tipo e uso
    property_type TEXT,        -- 'apartamento', 'casa', 'terreno', 'sala_comercial', 'galpao', 'fazenda', 'sitio'
    property_use TEXT,         -- 'residencial', 'comercial', 'industrial', 'agricola'
    transaction_type TEXT,     -- 'venda', 'aluguel'

    -- Localização
    city TEXT DEFAULT 'Campo Grande',
    neighborhood TEXT,
    state TEXT DEFAULT 'MS',
    address TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),

    -- Características
    area_total_m2 DECIMAL(12, 2),
    area_built_m2 DECIMAL(12, 2),
    bedrooms INTEGER,
    bathrooms INTEGER,
    suites INTEGER,
    parking_spaces INTEGER,
    floors INTEGER,

    -- Preços
    price_brl DECIMAL(15, 2),
    price_per_m2 DECIMAL(12, 2),
    condominium_fee_brl DECIMAL(10, 2),
    iptu_annual_brl DECIMAL(10, 2),

    -- Conteúdo
    title TEXT,
    description TEXT,
    features JSONB DEFAULT '[]'::jsonb,
    images JSONB DEFAULT '[]'::jsonb,
    raw_html TEXT,

    -- Status de processamento
    embedding_status TEXT DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    ocr_used BOOLEAN DEFAULT FALSE,

    -- Índices de qualidade
    data_completeness DECIMAL(3, 2),  -- 0.00 a 1.00
    confidence_score DECIMAL(3, 2)
);

-- Tabela de embeddings para RAG
CREATE TABLE IF NOT EXISTS property_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
    chunk_index INTEGER DEFAULT 0,
    chunk_type TEXT DEFAULT 'full',  -- 'full', 'description', 'features', 'location'
    content TEXT NOT NULL,
    embedding vector(1024),  -- Cohere embed-v3 (1024 dims)
    embedding_model TEXT DEFAULT 'cohere-embed-v3',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(property_id, chunk_index, chunk_type)
);

-- Tabela de jobs de scraping
CREATE TABLE IF NOT EXISTS scrape_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    target_url TEXT NOT NULL,
    job_type TEXT DEFAULT 'property',  -- 'property', 'listing_page', 'discovery'
    status TEXT DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed', 'blocked'
    priority INTEGER DEFAULT 5,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    next_retry_at TIMESTAMP,
    error_message TEXT,
    result_property_id UUID REFERENCES properties(id),
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Tabela de estatísticas de mercado (cache)
CREATE TABLE IF NOT EXISTS market_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    neighborhood TEXT NOT NULL,
    property_type TEXT NOT NULL,
    transaction_type TEXT NOT NULL,

    -- Estatísticas
    avg_price_m2 DECIMAL(12, 2),
    median_price_m2 DECIMAL(12, 2),
    min_price_m2 DECIMAL(12, 2),
    max_price_m2 DECIMAL(12, 2),
    sample_count INTEGER,

    -- Período
    period_start DATE,
    period_end DATE,
    calculated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(neighborhood, property_type, transaction_type, period_end)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_properties_location ON properties (city, neighborhood);
CREATE INDEX IF NOT EXISTS idx_properties_type_use ON properties (property_type, property_use);
CREATE INDEX IF NOT EXISTS idx_properties_transaction ON properties (transaction_type);
CREATE INDEX IF NOT EXISTS idx_properties_price ON properties (price_brl);
CREATE INDEX IF NOT EXISTS idx_properties_price_m2 ON properties (price_per_m2);
CREATE INDEX IF NOT EXISTS idx_properties_embedding_status ON properties (embedding_status);
CREATE INDEX IF NOT EXISTS idx_properties_scraped_at ON properties (scraped_at DESC);

-- Índice vetorial para busca por similaridade
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON property_embeddings
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_embeddings_property ON property_embeddings (property_id);

CREATE INDEX IF NOT EXISTS idx_scrape_jobs_status ON scrape_jobs (status, next_retry_at);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_priority ON scrape_jobs (priority DESC, created_at);

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para properties
DROP TRIGGER IF EXISTS update_properties_updated_at ON properties;
CREATE TRIGGER update_properties_updated_at
    BEFORE UPDATE ON properties
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Função para busca RAG com filtros
CREATE OR REPLACE FUNCTION search_similar_properties(
    query_embedding vector(1024),
    p_property_type TEXT DEFAULT NULL,
    p_property_use TEXT DEFAULT NULL,
    p_neighborhood TEXT DEFAULT NULL,
    p_transaction_type TEXT DEFAULT NULL,
    p_min_price DECIMAL DEFAULT NULL,
    p_max_price DECIMAL DEFAULT NULL,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    property_id UUID,
    similarity FLOAT,
    title TEXT,
    price_brl DECIMAL,
    price_per_m2 DECIMAL,
    neighborhood TEXT,
    property_type TEXT,
    area_total_m2 DECIMAL,
    bedrooms INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        1 - (pe.embedding <=> query_embedding) as similarity,
        p.title,
        p.price_brl,
        p.price_per_m2,
        p.neighborhood,
        p.property_type,
        p.area_total_m2,
        p.bedrooms
    FROM property_embeddings pe
    JOIN properties p ON pe.property_id = p.id
    WHERE
        (p_property_type IS NULL OR p.property_type = p_property_type)
        AND (p_property_use IS NULL OR p.property_use = p_property_use)
        AND (p_neighborhood IS NULL OR p.neighborhood ILIKE '%' || p_neighborhood || '%')
        AND (p_transaction_type IS NULL OR p.transaction_type = p_transaction_type)
        AND (p_min_price IS NULL OR p.price_brl >= p_min_price)
        AND (p_max_price IS NULL OR p.price_brl <= p_max_price)
    ORDER BY pe.embedding <=> query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Comentários
COMMENT ON TABLE properties IS 'Imóveis coletados do InfoImóveis';
COMMENT ON TABLE property_embeddings IS 'Embeddings para busca semântica RAG';
COMMENT ON TABLE scrape_jobs IS 'Fila de jobs de scraping';
COMMENT ON TABLE market_stats IS 'Cache de estatísticas de mercado por região/tipo';
