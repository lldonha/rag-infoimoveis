# RAG InfoImóveis - Sistema de Avaliação Imobiliária

Sistema RAG (Retrieval-Augmented Generation) para avaliação de imóveis em Campo Grande-MS usando dados do infoimoveis.com.br.

---

## 🎯 Status do Projeto

| Etapa | Status | Progresso |
|-------|--------|-----------|
| 0.1-0.4 Scraping básico | ✅ Concluído | 100% |
| 0.5 PostgreSQL + pgvector | ✅ Concluído | 100% |
| 0.6 Pipeline Embeddings | ✅ Concluído | 100% |
| 0.7 Sistema RAG | ✅ Concluído | 100% |
| 0.8 Scraping Produção | ✅ Concluído | 100% |
| 0.9 API REST | 🔜 Próximo | 0% |
| 1.0 Integração n8n | 📋 Planejado | 0% |

---

## 🚀 Quick Start

### 1. Configurar Banco de Dados

```bash
# Subir PostgreSQL + pgvector
docker-compose up -d postgres

# Verificar status
docker ps | grep postgres
```

### 2. Popular com Dados Reais (NOVO!)

```bash
# Scraping de produção com proteções anti-bloqueio
python tools/scraper_production.py

# Ou workflow completo (discovery + scraping)
python tools/scrape_workflow.py --mode full --max-properties 50
```

**Ver dashboard:**
```bash
python tools/metrics_dashboard.py
```

📖 **Guia completo:** [GUIA_RAPIDO_SCRAPING.md](GUIA_RAPIDO_SCRAPING.md)

### 3. Obter API Keys (FREE) - Opcional

Siga as instruções em [.env.INSTRUCOES](.env.INSTRUCOES):

- **Cohere** (embeddings): https://dashboard.cohere.com/
- **Groq** (LLM): https://console.groq.com/
- **Mistral** (backup): https://console.mistral.ai/

Depois, atualize `.env`:
```bash
COHERE_API_KEY=sua_key_aqui
GROQ_API_KEY=sua_key_aqui
MISTRAL_API_KEY=sua_key_aqui
```

### 4. Testar Pipeline RAG (Opcional)

```bash
# Teste PostgreSQL + pgvector
python tools/test_05_pgvector.py

# Teste embeddings
python tools/test_06_embeddings.py

# Teste sistema RAG completo
python tools/test_07_rag_system.py
```

---

## 📁 Estrutura do Projeto

```
rag_infoimoeveis/
├── tools/                      # Scripts Python
│   ├── scraper_production.py          # ✅ Scraper de produção
│   ├── scrape_workflow.py             # ✅ Orquestrador completo
│   ├── property_saver.py              # ✅ Inserção PostgreSQL
│   ├── metrics_dashboard.py           # ✅ Dashboard de métricas
│   ├── rate_limiter.py                # ✅ Controle de taxa
│   ├── cookie_manager.py              # ✅ Gestão de cookies
│   ├── fingerprint_rotator.py         # ✅ Rotação de identidade
│   ├── human_behavior.py              # ✅ Simulação humana
│   ├── test_05_pgvector.py            # ✅ Teste PostgreSQL
│   ├── test_06_embeddings.py          # ✅ Teste embeddings
│   └── test_07_rag_system.py          # ✅ Teste RAG completo
│
├── workflows/                  # SOPs e documentação
│   ├── scraping_producao.md   # ✅ Workflow de produção
│   ├── scraping.md            # Documentação scraping
│   └── anti-bloqueio.md       # 🔥 CRÍTICO: Plano anti-bloqueio
│
├── sql/
│   └── schema.sql             # ✅ Schema PostgreSQL aplicado
│
├── n8n/                       # Workflows n8n (futuro)
│
├── .tmp/                      # Dados temporários
│   ├── cookies.json           # Cookies Cloudflare
│   ├── property_urls.json     # 16 URLs coletadas
│   └── parsed_properties.json # 5 imóveis parseados
│
├── docker-compose.yml         # ✅ PostgreSQL (5433) + n8n
├── .env                       # ⚠️ Configurar API keys aqui
├── .env.INSTRUCOES           # 📖 Como obter API keys
├── PLANO_RAG_INFOIMOVEIS.md  # Plano completo
└── PROXIMOS_PASSOS.md        # Roadmap atualizado
```

---

## 🗄️ Banco de Dados

**Host:** localhost
**Porta:** 5433 (não conflita com outros PostgreSQL)
**Database:** infoimoveis
**User:** postgres
**Password:** infoimoveis2024

**Tabelas:**
- `properties` - Imóveis coletados
- `property_embeddings` - Vetores para RAG (1024 dims)
- `scrape_jobs` - Fila de scraping
- `market_stats` - Cache de estatísticas

**Extensões:**
- ✅ pgvector 0.8.1
- ✅ uuid-ossp 1.1

---

## 🎓 Stack Tecnológica

### APIs Free Tier
| API | Modelo | Limite Free | Uso |
|-----|--------|-------------|-----|
| **Cohere** | embed-v3 | 1000 calls/min | Embeddings (1024 dims) |
| **Groq** | llama-3.1-70b | 30 req/min | LLM RAG |
| **Mistral** | mistral-large | 1M tokens/mês | LLM backup |
| **Mistral** | pixtral | free tier | OCR (fallback) |

### Infraestrutura
- PostgreSQL 16 + pgvector (Docker)
- n8n (Docker) - futuro
- Playwright (scraping)
- Python 3.14

**Custo total: $0** (100% free tier + self-hosted)

---

## 🔐 Sistema de Scraping em Produção

**Sistema completo com 7 camadas de proteção anti-bloqueio:**

1. ✅ **Rate Limiting:** 5-12s delay, 50/hora, 400/dia
2. ✅ **Janelas Seguras:** Madrugada (03-06h), Almoço (13-15h), Noite (22-24h)
3. ✅ **Browser Real:** Headed mode (Cloudflare não detecta)
4. ✅ **Cookies Persistentes:** 6h TTL, renovação automática
5. ✅ **Fingerprint Rotation:** UA, viewport, timezone aleatórios
6. ✅ **Comportamento Humano:** Scroll, mouse, pausas aleatórias
7. ✅ **Auto-Recovery:** Detecção de bloqueio + pausa automática

**Guias:**
- 📖 [GUIA_RAPIDO_SCRAPING.md](GUIA_RAPIDO_SCRAPING.md) - Quick start
- 📖 [workflows/scraping_producao.md](workflows/scraping_producao.md) - Documentação completa
- 📖 [workflows/anti-bloqueio.md](workflows/anti-bloqueio.md) - Estratégias anti-bloqueio

---

## 📊 Dados Coletados

**Campos extraídos do infoimoveis.com.br:**
- Título, descrição, imagens
- Tipo (apartamento, casa, terreno, comercial, rural)
- Uso (residencial, comercial, industrial, agrícola)
- Transação (venda, aluguel)
- Localização (cidade, bairro, endereço, estado)
- Área (total, construída)
- Características (quartos, banheiros, suítes, vagas)
- Preços (venda, condomínio, IPTU)

**Formato:** JSON-LD (schema.org) + tabela HTML

---

## 🤖 Sistema RAG (Futuro)

**Agente:** Especialista em avaliação de imóveis em Campo Grande-MS

**Funcionalidades:**
- Buscar imóveis por critérios (tipo, localização, preço, características)
- Avaliar valor de mercado (comparação com similares)
- Analisar preço/m² por bairro
- Identificar oportunidades (abaixo do mercado)
- Alertar problemas (preços suspeitos, dados faltantes)

**Segmentação:** Por tipo (residencial, comercial, terreno, rural)

---

## 🧪 Testes

### Executar Testes Localmente

```bash
# Teste 5: PostgreSQL + pgvector
python tools/test_05_postgres.py
# Resultado esperado: 4/4 testes passaram ✅

# Teste 6: Embeddings (após configurar API keys)
python tools/test_06_embeddings.py
# Resultado esperado: 3/3 testes passaram ✅

# Teste 7: RAG Completo (futuro)
python tools/test_07_rag.py
```

---

## 📝 Logs e Métricas

```python
# Métricas de scraping
.tmp/scraping_metrics.json

# Logs de bloqueio
.tmp/block_events.log

# Cookies salvos
.tmp/cookies.json
```

---

## 🔧 Troubleshooting

### Erro: "Port 5432 already allocated"
**Solução:** Projeto usa porta 5433 (não conflita)

### Erro: "Cohere API key not configured"
**Solução:** Atualizar `.env` com API key válida

### Erro: "HTTP 403 Forbidden"
**Solução:** Usar browser headed mode (headless=False)

### Erro: "HTTP 429 Too Many Requests"
**Solução:** Aumentar delays entre requests (8-15s)

### Erro: "Cloudflare challenge"
**Solução:** Aguardar 20s após page.goto(), salvar cookies

---

## 🚨 Limites e Rate Limiting

| Parâmetro | Valor Recomendado | Crítico? |
|-----------|-------------------|----------|
| Delay entre requests | 5-12 segundos | ⚠️ SIM |
| Máximo por hora | 50 requests | ⚠️ SIM |
| Máximo por dia | 400 requests | ⚠️ SIM |
| Janelas de scraping | 03-06h, 13-15h, 22-24h | 🟡 ALTO |
| Renovação de cookies | A cada 6 horas | 🟡 ALTO |

**Não respeitar = IP bloqueado por Cloudflare**

---

## 📚 Documentação Completa

| Arquivo | Descrição |
|---------|-----------|
| [PLANO_RAG_INFOIMOVEIS.md](PLANO_RAG_INFOIMOVEIS.md) | Plano técnico completo |
| [PROXIMOS_PASSOS.md](PROXIMOS_PASSOS.md) | Roadmap atualizado |
| [workflows/scraping.md](workflows/scraping.md) | SOP de scraping |
| [workflows/anti-bloqueio.md](workflows/anti-bloqueio.md) | 🔥 Estratégia anti-bloqueio |
| [.env.INSTRUCOES](.env.INSTRUCOES) | Como obter API keys |

---

## 🎯 Próximos Passos

1. ✅ ~~Obter API keys (Cohere, Groq, Mistral)~~
2. ✅ ~~Testar pipeline de embeddings~~
3. ✅ ~~Implementar sistema RAG completo~~
4. ✅ ~~Implementar scraper de produção com proteções~~
5. 🔜 **PRÓXIMO:** Popular banco com 1000+ imóveis reais
6. 📋 Criar API REST para consultas
7. 📋 Migrar para workflow n8n (automação)

Ver detalhes em [PROXIMOS_PASSOS.md](PROXIMOS_PASSOS.md)

---

## 📞 Suporte

**Documentação:** Ler MDs na raiz do projeto
**Logs:** `.tmp/` para debug
**Schema SQL:** `sql/schema.sql`
**Tests:** `tools/test_*.py`

---

---

## 🆕 Novidades da v0.8.0

**Sistema de Scraping em Produção:**

✨ **Novos Scripts:**
- `scraper_production.py` - Scraper com todas as proteções
- `scrape_workflow.py` - Orquestrador completo (discovery → scraping)
- `property_saver.py` - Inserção automática no PostgreSQL
- `metrics_dashboard.py` - Dashboard de monitoramento

🛡️ **Proteções Anti-Bloqueio:**
- Rate limiter inteligente (50/hora, 400/dia)
- Cookies persistentes (6h TTL)
- Fingerprint rotation (UA, viewport, timezone)
- Comportamento humano simulado
- Janelas de tempo seguras
- Detecção e recovery automático

📊 **Monitoramento:**
- Dashboard em tempo real
- Métricas de qualidade dos dados
- Insights de mercado automáticos
- Detecção de oportunidades

---

**Desenvolvido com WAT Framework (Workflows, Agents, Tools)**
Versão: 0.8.0 (Sistema de Scraping em Produção)
Última atualização: 2026-02-05
