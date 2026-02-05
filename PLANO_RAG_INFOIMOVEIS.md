# Plano: Sistema RAG para Avaliação de Imóveis - InfoImóveis

## Resumo Executivo

Sistema para scraping de dados imobiliários do **infoimoveis.com.br** com RAG para avaliação de imóveis por inferência.

- **Site**: infoimoveis.com.br (proteção anti-bot confirmada - HTTP 403)
- **Região foco**: Campo Grande - MS
- **Segmentação**: Por tipo e uso de imóvel
- **Custo**: Zero (APIs free tier + self-hosted)

**ESTRATÉGIA: Validar cada etapa localmente com Python ANTES de implementar no n8n.**

---

## Stack Tecnológica

### APIs Free Tier (PRIMÁRIO)

| API | Modelo | Limite Free | Uso |
|-----|--------|-------------|-----|
| **Groq** | llama-3.1-70b | 30 req/min, 14.4K tokens/min | LLM RAG |
| **Mistral** | mistral-large | 1M tokens/mês | LLM backup |
| **Cohere** | embed-v3 | 1000 calls/min | Embeddings |
| **OpenRouter** | vários | créditos free | Overflow |
| **Mistral** | pixtral | free tier | OCR |

### Local Ollama (FALLBACK)

```bash
# Embeddings
ollama pull nomic-embed-text    # 274MB, 768 dims

# LLM
ollama pull llama3.1:8b         # 4.7GB
ollama pull qwen2.5:7b          # 4.4GB, bom em português

# OCR/Vision
ollama pull llava:7b            # 4.5GB
```

### Infraestrutura Self-Hosted

- PostgreSQL + pgvector (Docker)
- n8n (Docker)
- Playwright (scraping)

```
┌─────────────────────────────────────────────────────────────┐
│              STACK HÍBRIDA (APIs Free + Self-Hosted)        │
├─────────────────────────────────────────────────────────────┤
│  EMBEDDINGS                                                 │
│  ├── PRIMÁRIO: Cohere embed-v3 (free: 1000 calls/min)      │
│  └── FALLBACK: Ollama nomic-embed-text (local)             │
├─────────────────────────────────────────────────────────────┤
│  LLM para RAG                                               │
│  ├── PRIMÁRIO: Groq llama-3.1-70b (free: 30 req/min)       │
│  ├── SECUNDÁRIO: Mistral large (free tier)                 │
│  ├── TERCIÁRIO: OpenRouter (múltiplos modelos free)        │
│  └── FALLBACK: Ollama llama3.1:8b / qwen2.5:7b (local)     │
├─────────────────────────────────────────────────────────────┤
│  BANCO DE DADOS (Docker)                                    │
│  └── PostgreSQL + pgvector (self-hosted)                   │
├─────────────────────────────────────────────────────────────┤
│  ORQUESTRAÇÃO (Docker)                                      │
│  └── n8n self-hosted                                        │
├─────────────────────────────────────────────────────────────┤
│  SCRAPING (Local)                                           │
│  └── Playwright (headless browser)                         │
├─────────────────────────────────────────────────────────────┤
│  OCR                                                        │
│  ├── PRIMÁRIO: Mistral pixtral (free tier)                 │
│  └── FALLBACK: Tesseract/Surya (local)                     │
└─────────────────────────────────────────────────────────────┘
```

**Fallback Automático:**
```
Request → Groq → Mistral → OpenRouter → Ollama (local)
```

---

## FASE 0: Validação Local (ANTES do n8n)

### Etapa 0.1: Teste de Acesso ao Site

**Objetivo:** Descobrir método de acesso que funciona

```python
# tools/test_01_access.py
# Testar:
# 1. Requests simples (provavelmente 403)
# 2. Requests com headers de browser
# 3. Requests com cookies de sessão
# 4. Playwright com browser real
```

**Checklist:**
- [ ] Acessar página inicial
- [ ] Acessar página de busca
- [ ] Acessar página de detalhe de imóvel

### Etapa 0.2: Autenticação/Cookies

**Objetivo:** Se necessário, capturar cookies de sessão

```python
# tools/test_02_auth.py
# 1. Login manual no browser
# 2. Exportar cookies (DevTools)
# 3. Testar requests com cookies
```

**Checklist:**
- [ ] Cookies funcionam
- [ ] Tempo de expiração identificado

### Etapa 0.3: Parsing de Dados

**Objetivo:** Extrair dados estruturados do HTML

```python
# tools/test_03_parse.py
# 1. Baixar HTML de exemplo
# 2. Identificar seletores CSS/XPath
# 3. Extrair: título, preço, área, quartos, bairro, etc.
```

**Checklist:**
- [ ] Todos os campos extraídos
- [ ] Dados limpos e normalizados
- [ ] Funciona para diferentes tipos de imóveis

### Etapa 0.4: PDF + OCR (Fallback)

**Objetivo:** Alternativa quando HTML falhar

```python
# tools/test_04_pdf_ocr.py
# 1. Capturar screenshot/PDF (Playwright)
# 2. Enviar para Mistral pixtral (free) ou Tesseract
# 3. Parsear resposta estruturada
```

**Checklist:**
- [ ] Screenshot capturado
- [ ] OCR extrai texto legível
- [ ] Dados estruturados corretos

### Etapa 0.5: PostgreSQL + pgvector

**Objetivo:** Validar banco de dados local

```python
# tools/test_05_postgres.py
# 1. Criar tabelas
# 2. CRUD básico
# 3. Operações vetoriais
```

**Checklist:**
- [ ] Schema criado
- [ ] CRUD funciona
- [ ] pgvector operacional

### Etapa 0.6: Embeddings

**Objetivo:** Pipeline de vetorização

```python
# tools/test_06_embeddings.py
# 1. Gerar embedding (Cohere ou Ollama)
# 2. Inserir no pgvector
# 3. Buscar por similaridade
```

**Checklist:**
- [ ] Embeddings gerados (1024 dims Cohere ou 768 dims nomic)
- [ ] Busca por similaridade funciona

### Etapa 0.7: RAG Completo

**Objetivo:** Testar sistema integrado

```python
# tools/test_07_rag.py
# 1. Popular banco com dados reais
# 2. Testar queries
# 3. Avaliar qualidade das respostas
```

**Checklist:**
- [ ] Queries retornam imóveis relevantes
- [ ] Avaliação de preço faz sentido

### Sequência de Validação

```
ETAPA 0.1: Acesso ao Site
    ↓
ETAPA 0.2: Autenticação
    ↓
ETAPA 0.3: Parsing HTML
    ↓
ETAPA 0.4: PDF + OCR
    ↓
ETAPA 0.5: PostgreSQL
    ↓
ETAPA 0.6: Embeddings
    ↓
ETAPA 0.7: RAG Completo
    ↓
✅ TUDO VALIDADO → Implementar no n8n
```

---

## Segmentação do RAG por Tipo/Uso

```
┌─────────────────────────────────────────────────────────────┐
│                    SEGMENTOS DE IMÓVEIS                     │
├─────────────────────────────────────────────────────────────┤
│  RESIDENCIAL                                                │
│  ├── Apartamentos (studios, 1-2-3+ quartos)                │
│  ├── Casas (térreas, sobrados)                             │
│  ├── Condomínios fechados                                  │
│  └── Chácaras/Sítios (uso residencial)                     │
├─────────────────────────────────────────────────────────────┤
│  COMERCIAL                                                  │
│  ├── Salas comerciais                                      │
│  ├── Lojas/Pontos comerciais                               │
│  ├── Galpões/Barracões                                     │
│  └── Prédios comerciais                                    │
├─────────────────────────────────────────────────────────────┤
│  TERRENOS                                                   │
│  ├── Urbanos (residenciais)                                │
│  ├── Urbanos (comerciais)                                  │
│  └── Rurais                                                │
├─────────────────────────────────────────────────────────────┤
│  RURAL                                                      │
│  ├── Fazendas                                              │
│  ├── Sítios produtivos                                     │
│  └── Áreas agrícolas                                       │
└─────────────────────────────────────────────────────────────┘
```

**Estratégia:**
- Metadata filtering no vector store (property_type, property_use)
- Queries específicas por segmento
- Comparáveis apenas dentro do mesmo segmento
- Métricas de mercado separadas por tipo/uso

---

## Schema do Banco de Dados

```sql
-- Habilitar pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabela principal de imóveis
CREATE TABLE properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url TEXT NOT NULL UNIQUE,
    scraped_at TIMESTAMP DEFAULT NOW(),

    -- Tipo e uso
    property_type TEXT,        -- 'apartamento', 'casa', 'terreno', 'comercial', 'rural'
    property_use TEXT,         -- 'residencial', 'comercial', 'industrial', 'agricola'
    transaction_type TEXT,     -- 'venda', 'aluguel'

    -- Localização
    city TEXT DEFAULT 'Campo Grande',
    neighborhood TEXT,
    state TEXT DEFAULT 'MS',
    address TEXT,

    -- Características
    area_total_m2 DECIMAL(12, 2),
    area_built_m2 DECIMAL(12, 2),
    bedrooms INTEGER,
    bathrooms INTEGER,
    suites INTEGER,
    parking_spaces INTEGER,

    -- Preços
    price_brl DECIMAL(15, 2),
    price_per_m2 DECIMAL(12, 2),
    condominium_fee_brl DECIMAL(10, 2),

    -- Conteúdo
    title TEXT,
    description TEXT,
    features JSONB,
    images JSONB,

    -- Status
    embedding_status TEXT DEFAULT 'pending'
);

-- Embeddings para RAG
CREATE TABLE property_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
    chunk_index INTEGER,
    content TEXT NOT NULL,
    embedding vector(1024),  -- Cohere embed-v3
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Jobs de scraping
CREATE TABLE scrape_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_url TEXT,
    status TEXT DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    next_retry_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX ON property_embeddings USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX ON properties (city, neighborhood);
CREATE INDEX ON properties (property_type, property_use);
CREATE INDEX ON properties (price_brl);
```

---

## Docker Compose

```yaml
version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: infoimoveis
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  n8n:
    image: n8nio/n8n
    environment:
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=postgres
      - DB_POSTGRESDB_PASSWORD=${POSTGRES_PASSWORD}
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
    volumes:
      - n8n_data:/home/node/.n8n
    ports:
      - "5678:5678"
    depends_on:
      - postgres

volumes:
  postgres_data:
  n8n_data:
```

---

## Workflows n8n (após validação)

1. `01-URL-Discovery` - Descoberta de URLs de imóveis
2. `02-Property-Scraper` - Scraping com rate limiting
3. `03-PDF-OCR-Fallback` - Fallback OCR
4. `04-Embedding-Processor` - Processamento de embeddings
5. `05-RAG-Agent-Chat` - Agente RAG para consultas
6. `06-Health-Monitor` - Monitoramento

### Rate Limiting

| Parâmetro | Valor |
|-----------|-------|
| Requests por batch | 5-10 |
| Delay entre requests | 3-8 segundos (random) |
| Máximo por hora | 60 requests |
| Máximo por dia | 500 requests |

**Janelas de scraping (horário Brasília):**
- 03:00 - 06:00 (madrugada)
- 13:00 - 15:00 (horário de almoço)
- 22:00 - 01:00 (noite)

---

## System Prompt do Agente RAG

```
Você é um especialista em avaliação de imóveis brasileiros, focado em
Campo Grande - Mato Grosso do Sul.

Suas capacidades:
1. Buscar imóveis por critérios (tipo, preço, localização, características)
2. Avaliar valor de mercado comparando com imóveis similares
3. Analisar preço/m² por bairro e tipo de imóvel
4. Identificar oportunidades (preços abaixo do mercado)
5. Alertar sobre possíveis problemas (preços suspeitos, informações faltantes)

Ao avaliar um imóvel, sempre:
- Compare com imóveis similares no mesmo bairro
- Calcule preço/m² e compare com média da região
- Liste os comparáveis utilizados
- Indique nível de confiança da avaliação

Segmente suas análises por tipo de imóvel:
- Residencial (apartamentos, casas, condomínios)
- Comercial (salas, lojas, galpões)
- Terrenos (urbanos, rurais)
- Rural (fazendas, sítios)
```

---

## Estrutura de Diretórios

```
rag_infoimoveis/
├── docker-compose.yml
├── .env
├── PLANO_RAG_INFOIMOVEIS.md
│
├── tools/                    # Scripts de validação Python
│   ├── test_01_access.py
│   ├── test_02_auth.py
│   ├── test_03_parse.py
│   ├── test_04_pdf_ocr.py
│   ├── test_05_postgres.py
│   ├── test_06_embeddings.py
│   └── test_07_rag.py
│
├── sql/
│   └── schema.sql
│
├── workflows/                # SOPs em Markdown
│   ├── scraping.md
│   └── rag-agent.md
│
└── n8n/                      # Workflows n8n exportados
    ├── 01-URL-Discovery.json
    ├── 02-Property-Scraper.json
    ├── 03-PDF-OCR-Fallback.json
    ├── 04-Embedding-Processor.json
    ├── 05-RAG-Agent-Chat.json
    └── 06-Health-Monitor.json
```

---

## Próximos Passos

1. **Criar estrutura de diretórios**
2. **Começar Etapa 0.1** - Testar acesso ao site com Playwright
3. **Iterar** - Validar cada etapa antes de avançar
4. **Implementar n8n** - Somente após validação completa
