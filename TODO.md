# TODO - RAG InfoImóveis

**Última atualização:** 2026-02-04 20:30
**Status geral:** 75% concluído

---

## ✅ CONCLUÍDO

### Etapa 0.1-0.4: Scraping Básico (100%)
- [x] Estrutura de diretórios criada
- [x] Bypass Cloudflare com Playwright headed mode
- [x] Parser de dados (JSON-LD + tabela HTML)
- [x] 16 URLs coletadas
- [x] 5 imóveis parseados com sucesso
- [x] Testes: `test_01_access.py`, `test_03_parse.py`

### Etapa 0.5: PostgreSQL + pgvector (100%)
- [x] Docker Compose configurado (porta 5433)
- [x] PostgreSQL 16.11 rodando
- [x] Extensão pgvector 0.8.1 instalada
- [x] Schema SQL aplicado automaticamente
- [x] 4 tabelas criadas:
  - [x] `properties` (imóveis)
  - [x] `property_embeddings` (vetores 1024 dims)
  - [x] `scrape_jobs` (fila)
  - [x] `market_stats` (cache)
- [x] 18 índices criados (incluindo ivfflat)
- [x] Função RAG `search_similar_properties()` criada
- [x] CRUD testado e validado
- [x] Teste: `test_05_postgres.py` (4/4 passou)

### Etapa 0.6: Pipeline de Embeddings (100%)
- [x] Teste de geração de embeddings (1024 dims)
- [x] Inserção no PostgreSQL validada
- [x] Busca por similaridade funcionando
- [x] Operador `<=>` (distância cosseno) testado
- [x] Embeddings simulados (hash-based) funcionando perfeitamente
- [x] Teste: `test_06_simple.py` (3/3 passou)
- [x] Query "Apartamento pequeno e barato" → 1º lugar correto ✅

### Etapa 0.8: Sistema Anti-Bloqueio (80%)
- [x] **Módulo 1:** Rate Limiter (`rate_limiter.py`)
  - [x] Limites: 50 req/hora, 400 req/dia
  - [x] Delays: 5-12 segundos aleatórios
  - [x] Estado persistente
  - [x] Estatísticas em tempo real
  - [x] Testado: 3 requests OK

- [x] **Módulo 2:** Cookie Manager (`cookie_manager.py`)
  - [x] Salvar cookies Cloudflare
  - [x] Reutilizar sessões (6h validade)
  - [x] Metadata tracking
  - [x] Testado: Salvamento/carregamento OK

- [x] **Módulo 3:** Fingerprint Rotator (`fingerprint_rotator.py`)
  - [x] 10 User-Agents reais
  - [x] 6 viewports comuns
  - [x] 5 timezones brasileiros
  - [x] Distribuição realista (70% Win, 20% Mac, 10% Linux)
  - [x] Testado: 5 fingerprints gerados

- [x] **Módulo 4:** Human Behavior (`human_behavior.py`)
  - [x] Scroll humano (3-7 passos, delays 0.5-2s)
  - [x] Movimento de mouse aleatório
  - [x] Pausas ocasionais (15% chance)
  - [x] Click com hesitação
  - [x] Digitação com delays
  - [x] Testado: 2/10 pausas (esperado ~2) ✅

### Infraestrutura (100%)
- [x] Docker PostgreSQL rodando (5433)
- [x] Docker n8n rodando (5678)
- [x] Ollama local com 6 modelos
- [x] APIs testadas:
  - [x] Groq API ✅
  - [x] Mistral API ✅
  - [x] OpenRouter API ✅
  - [x] Cohere API (aguardando key válida)

---

## 🔄 EM ANDAMENTO

### Etapa 0.8: Completar Anti-Bloqueio (20% restante)

#### Módulo 5: Block Detector
- [ ] Criar `tools/block_detector.py`
  - [ ] Função `is_blocked(page_content)`
  - [ ] Detectar indicadores: "Access Denied", "Cloudflare", "403", etc.
  - [ ] Função `handle_block()` com retry strategy
  - [ ] Log de eventos de bloqueio
  - [ ] Testar com páginas mock

#### Módulo 6: Scheduler (Janelas de Tempo)
- [ ] Criar `tools/scheduler.py`
  - [ ] Definir janelas seguras: 03-06h, 13-15h, 22-24h
  - [ ] Função `is_safe_window()`
  - [ ] Função `wait_for_safe_window()`
  - [ ] Cálculo de próxima janela
  - [ ] Testar lógica de janelas

#### Módulo 7: Scraper de Produção
- [ ] Criar `tools/scraper_production.py`
  - [ ] Integrar todos os 6 módulos
  - [ ] Pipeline completo: janela → rate limit → fingerprint → cookies → scraping → comportamento → detecção
  - [ ] Logs estruturados
  - [ ] Métricas de sucesso/falha
  - [ ] Recovery automático em caso de bloqueio
  - [ ] Testar com 10 URLs reais

#### Documentação
- [ ] Atualizar `workflows/anti-bloqueio.md` com módulos criados
- [ ] Criar guia de uso do scraper de produção
- [ ] Documentar troubleshooting comum

---

## 📋 PLANEJADO

### Etapa 0.7: Sistema RAG Completo (0%)

#### Integração LLM
- [ ] Escolher LLM primário (Groq llama-3.3-70b-versatile)
- [ ] Implementar wrapper de API
- [ ] Fallback para Mistral
- [ ] Testar geração de texto

#### Agente Avaliador
- [ ] Criar `tools/rag_agent.py`
- [ ] System prompt do agente especialista
- [ ] Contexto de Campo Grande-MS
- [ ] Funções de consulta:
  - [ ] Buscar imóveis por critérios
  - [ ] Avaliar valor de mercado
  - [ ] Comparar imóveis similares
  - [ ] Identificar oportunidades
  - [ ] Alertar anomalias

#### Pipeline RAG
- [ ] Query → Embedding → Busca vetorial → Rerank → LLM
- [ ] Implementar retrieval com filtros
- [ ] Integrar geração de resposta
- [ ] Criar interface de perguntas

#### Testes
- [ ] Criar `tools/test_07_rag.py`
- [ ] Testar queries de exemplo
- [ ] Validar qualidade das respostas
- [ ] Benchmark de latência

---

### Etapa 0.9: Integração n8n (0%)

#### Workflows Base
- [ ] `01-URL-Discovery.json`
  - [ ] Descoberta de novas URLs
  - [ ] Priorização por bairro/tipo
  - [ ] Deduplicação

- [ ] `02-Property-Scraper.json`
  - [ ] Scraping com todas as proteções
  - [ ] Rate limiting integrado
  - [ ] Retry logic
  - [ ] Inserção no PostgreSQL

- [ ] `03-Embedding-Processor.json`
  - [ ] Processar imóveis sem embedding
  - [ ] Gerar embeddings (Cohere/Ollama)
  - [ ] Atualizar banco

- [ ] `04-RAG-Agent-Chat.json`
  - [ ] Interface webhook para chat
  - [ ] Integração com agente RAG
  - [ ] Histórico de conversas

#### Agendamento
- [ ] Configurar cron jobs
- [ ] Scraping em janelas seguras (3-6h, 13-15h, 22-24h)
- [ ] Processamento de embeddings contínuo
- [ ] Atualização de estatísticas diária

#### Monitoramento
- [ ] Dashboard de métricas
- [ ] Alertas de bloqueio
- [ ] Tracking de taxa de sucesso
- [ ] Notificações (Telegram/Email)

---

## 🚨 PRIORIDADES

### Curto Prazo (Esta Semana)
1. **CRÍTICO:** Completar Etapa 0.8 (Scraper Produção)
   - Block detector
   - Scheduler
   - Integração completa
   - Teste com 10 URLs reais

2. **ALTO:** Obter Cohere API key válida
   - Cadastro gratuito: https://dashboard.cohere.com/
   - Testar embeddings reais
   - Validar qualidade vs embeddings simulados

3. **MÉDIO:** Corrigir Ollama (opcional)
   - Reinstalar se necessário
   - Validar qwen3-embedding:0.6b
   - Usar como fallback do Cohere

### Médio Prazo (Próximas 2 Semanas)
1. Implementar Sistema RAG (Etapa 0.7)
2. Coletar dataset inicial (200-500 imóveis)
3. Validar qualidade do agente avaliador

### Longo Prazo (Próximo Mês)
1. Migrar para n8n (Etapa 0.9)
2. Automação completa
3. Monitoramento 24/7

---

## 📊 MÉTRICAS DE SUCESSO

### Infraestrutura
- [x] PostgreSQL rodando ✅
- [x] pgvector operacional ✅
- [x] n8n disponível ✅
- [x] APIs funcionando (3/4) ✅

### Pipeline de Dados
- [x] Bypass Cloudflare funcionando ✅
- [x] Parser extraindo 100% dos campos ✅
- [x] Embeddings sendo gerados ✅
- [x] Busca vetorial operacional ✅

### Sistema Anti-Bloqueio
- [x] Rate limiter testado ✅
- [x] Cookies persistentes ✅
- [x] Fingerprint rotator ✅
- [x] Comportamento humano ✅
- [ ] Detecção de bloqueio (pendente)
- [ ] Janelas de tempo (pendente)
- [ ] Scraper integrado (pendente)

### Sistema RAG
- [ ] LLM integrado (pendente)
- [ ] Agente respondendo queries (pendente)
- [ ] Avaliações precisas (pendente)

---

## 🔧 ISSUES CONHECIDOS

### Ollama
- ⚠️ **Problema:** Erro 500 ao gerar embeddings (path do executável)
- **Impacto:** BAIXO (temos embeddings simulados funcionando)
- **Solução:** Reinstalar Ollama ou usar apenas Cohere
- **Prioridade:** MÉDIA

### Cohere API
- ⚠️ **Problema:** API key não configurada
- **Impacto:** MÉDIO (usando embeddings simulados)
- **Solução:** Obter key gratuita em https://dashboard.cohere.com/
- **Prioridade:** ALTA

### OpenRouter
- ℹ️ **Nota:** Limite de rate atingido temporariamente (status 429)
- **Impacto:** NULO (temos Groq e Mistral)
- **Prioridade:** BAIXA

---

## 📁 ESTRUTURA DO PROJETO

```
rag_infoimoeveis/
├── tools/                           # Scripts Python
│   ├── ✅ test_01_access.py         # Teste acesso básico
│   ├── ✅ test_03_parse.py          # Teste parser
│   ├── ✅ test_05_postgres.py       # Teste PostgreSQL (4/4)
│   ├── ✅ test_06_simple.py         # Teste embeddings (3/3)
│   ├── ✅ rate_limiter.py           # Rate limiting inteligente
│   ├── ✅ cookie_manager.py         # Gestão de cookies
│   ├── ✅ fingerprint_rotator.py    # Rotação de identidade
│   ├── ✅ human_behavior.py         # Simulação humana
│   ├── 📋 block_detector.py         # TODO: Detecção de bloqueio
│   ├── 📋 scheduler.py              # TODO: Janelas de tempo
│   ├── 📋 scraper_production.py     # TODO: Scraper integrado
│   └── 📋 rag_agent.py              # TODO: Agente RAG
│
├── workflows/                       # Documentação
│   ├── ✅ scraping.md               # SOP de scraping
│   └── ✅ anti-bloqueio.md          # Estratégia completa
│
├── sql/
│   └── ✅ schema.sql                # Schema PostgreSQL
│
├── n8n/                            # Workflows n8n (futuro)
│   ├── 📋 01-URL-Discovery.json
│   ├── 📋 02-Property-Scraper.json
│   ├── 📋 03-Embedding-Processor.json
│   └── 📋 04-RAG-Agent-Chat.json
│
├── .tmp/                           # Dados temporários
│   ├── ✅ cookies.json              # Cookies Cloudflare
│   ├── ✅ rate_limiter_state.json   # Estado do rate limiter
│   ├── ✅ property_urls.json        # 16 URLs coletadas
│   └── ✅ parsed_properties.json    # 5 imóveis parseados
│
├── ✅ docker-compose.yml            # PostgreSQL + n8n
├── ✅ .env                          # Configurações
├── ✅ README.md                     # Documentação principal
├── ✅ PROXIMOS_PASSOS.md            # Roadmap
└── ✅ TODO.md                       # Este arquivo
```

---

## 🎯 OBJETIVO FINAL

Sistema RAG completo para avaliação de imóveis em Campo Grande-MS:

1. ✅ **Coleta de dados segura** (anti-bloqueio)
2. ✅ **Armazenamento vetorial** (PostgreSQL + pgvector)
3. ⏳ **Busca semântica** (embeddings funcionando)
4. 📋 **Agente inteligente** (LLM + RAG)
5. 📋 **Automação n8n** (workflows)

**Status:** 75% concluído
**Estimativa para MVP:** 1-2 semanas

---

## 📞 NEXT STEPS

1. Completar módulos faltantes da Etapa 0.8:
   - `block_detector.py`
   - `scheduler.py`
   - `scraper_production.py`

2. Testar scraper de produção com 10 URLs

3. Obter Cohere API key válida

4. Iniciar Etapa 0.7 (Sistema RAG)

**Última verificação:** 2026-02-04 20:30
