# Próximos Passos - RAG InfoImóveis

## Status Atual (Atualizado: 2026-02-04)

### ✅ Concluído
- [x] Estrutura de diretórios criada
- [x] Bypass Cloudflare funcionando (Playwright headed)
- [x] Parsing de dados de imóveis (JSON-LD + tabela HTML)
- [x] 16 URLs coletadas, 5 imóveis parseados com sucesso
- [x] **PostgreSQL + pgvector configurado e testado (Etapa 0.5)**
- [x] **Docker containers funcionando (porta 5433)**
- [x] **Schema SQL aplicado (4 tabelas + índices vetoriais)**

### 🔄 Em Andamento
- [ ] **Etapa 0.6: Pipeline de Embeddings**
  - Aguardando API keys: Cohere, Groq, Mistral
  - Script de teste criado: `tools/test_06_embeddings.py`

### 📋 Dados Extraídos com Sucesso
- Título, descrição, tipo de imóvel
- Preço, área construída/total
- Bairro, cidade, estado, endereço
- Imagens (até 18 por imóvel)

---

## Estratégias Anti-Bloqueio

### 1. Rate Limiting (OBRIGATÓRIO)
```python
import random
import time

# Entre cada request
delay = random.uniform(3, 10)  # 3-10 segundos
time.sleep(delay)

# Limites
MAX_PER_HOUR = 60
MAX_PER_DAY = 500
```

### 2. Rotação de Cookies
```python
# Salvar cookies após passar pelo Cloudflare
cookies = await context.cookies()
with open(".tmp/cookies.json", "w") as f:
    json.dump(cookies, f)

# Reutilizar em sessões futuras
with open(".tmp/cookies.json", "r") as f:
    cookies = json.load(f)
await context.add_cookies(cookies)
```

### 3. Rotação de User-Agent
```python
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]
ua = random.choice(USER_AGENTS)
```

### 4. Janelas de Scraping (Horários de Baixo Tráfego)
- 03:00 - 06:00 (madrugada)
- 13:00 - 15:00 (almoço)
- 22:00 - 01:00 (noite)

### 5. Rotação de IP (Se Necessário)
Opções se houver bloqueio persistente:
- Proxies residenciais (Bright Data, Oxylabs)
- VPN com múltiplos servidores
- Tor (mais lento, mas gratuito)

### 6. Fingerprint Randomization
```python
# Variar viewport
viewports = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
]

# Variar timezone
timezones = ["America/Sao_Paulo", "America/Campo_Grande", "America/Cuiaba"]
```

---

## 🎯 Próximas Etapas Técnicas

### ✅ Etapa 0.5: PostgreSQL + pgvector (CONCLUÍDA)
- [x] Containers Docker rodando (porta 5433)
- [x] Schema SQL aplicado automaticamente
- [x] CRUD testado e funcionando
- [x] Operações vetoriais validadas
- [x] Índices criados (18 índices incluindo ivfflat)
- [x] Função `search_similar_properties()` testada

**Resultado:** 4/4 testes passaram ✅

---

### 🔄 Etapa 0.6: Embeddings Pipeline (EM ANDAMENTO)

**Pré-requisitos:**
1. ⚠️ **Obter API Keys (FREE):**
   - **Cohere**: https://dashboard.cohere.com/ (embeddings)
   - **Groq**: https://console.groq.com/ (LLM RAG)
   - **Mistral**: https://console.mistral.ai/ (backup + OCR)

2. **Atualizar `.env`** com as keys obtidas:
```bash
COHERE_API_KEY=sua_key_aqui
GROQ_API_KEY=sua_key_aqui
MISTRAL_API_KEY=sua_key_aqui
```

**Após configurar:**
```bash
# Testar pipeline de embeddings
python tools/test_06_embeddings.py
```

**O que será testado:**
- Gerar embeddings com Cohere (1024 dims)
- Inserir embeddings no pgvector
- Busca por similaridade com dados reais
- Fallback para Ollama (se disponível)

---

### Etapa 0.7: RAG Completo
1. Integrar LLM (Groq llama-3.1-70b)
2. Criar system prompt do agente avaliador
3. Implementar retrieval + generation
4. Testar queries de avaliação de imóveis
5. Criar script `tools/test_07_rag.py`

---

### Etapa 0.8: Scraping Seguro (ANTI-BLOQUEIO)

**CRÍTICO:** Ler `workflows/anti-bloqueio.md` ANTES de iniciar

**Implementar camadas de proteção:**
1. ✅ Browser real (headed mode)
2. ✅ Rate limiting (5-12s delay)
3. ✅ Janelas de tempo (madrugada, almoço, noite)
4. ✅ Rotação de fingerprint (UA, viewport)
5. ✅ Gestão de cookies (persistência)
6. ✅ Comportamento humano (scroll, mouse)
7. ✅ Detecção de bloqueio

**Criar:**
- `tools/scraper_production.py` (todas as camadas)
- `tools/rate_limiter.py`
- `tools/cookie_manager.py`
- `tools/fingerprint_rotator.py`
- `tools/human_behavior.py`

---

### Etapa 0.9: n8n Integration
**Somente após validação completa em Python**

1. Criar workflow `01-URL-Discovery.json`
2. Criar workflow `02-Property-Scraper.json` (com rate limiting)
3. Criar workflow `03-Embedding-Processor.json`
4. Criar workflow `04-RAG-Agent-Chat.json`
5. Configurar agendamentos (janelas seguras)
6. Monitoramento e alertas

---

## Arquivos de Referência

| Arquivo | Descrição |
|---------|-----------|
| `tools/test_03_parse.py` | Parser de imóveis (funcional) |
| `workflows/scraping.md` | Documentação do scraping |
| `sql/schema.sql` | Schema PostgreSQL |
| `.tmp/property_urls.json` | 16 URLs coletadas |
| `.tmp/parsed_properties.json` | 5 imóveis parseados |

---

## Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| Bloqueio de IP | Rate limiting + rotação de proxy |
| Mudança no HTML | Monitorar schema JSON-LD (mais estável) |
| Cloudflare upgrade | Manter modo headed + cookies |
| Limite de API free | Fallback para Ollama local |
