# ✈️ PRE-FLIGHT CHECKLIST - Scraping InfoImóveis

## Antes de Iniciar Scraping em Produção

**Versão:** 0.8.0
**Data:** 2026-02-05

---

## 📋 Checklist Obrigatório

### 🐳 Infraestrutura

```bash
# Verificar PostgreSQL
docker ps | grep postgres
```

- [ ] PostgreSQL rodando na porta 5433
- [ ] Container saudável (status: Up)
- [ ] Possível conectar: `psql -h localhost -p 5433 -U postgres -d infoimoveis`

### 🗄️ Banco de Dados

```bash
# Verificar extensões e schema
python tools/test_05_pgvector.py
```

- [ ] Extensão pgvector instalada (v0.8.1)
- [ ] Extensão uuid-ossp instalada
- [ ] Tabela `properties` existe
- [ ] Tabela `property_embeddings` existe
- [ ] Tabela `scrape_jobs` existe
- [ ] Tabela `market_stats` existe
- [ ] Índices criados corretamente

### 🐍 Dependências Python

```bash
# Verificar instalação
pip list | grep -E "playwright|psycopg2|dotenv"
```

- [ ] playwright instalado
- [ ] psycopg2-binary instalado
- [ ] python-dotenv instalado
- [ ] Browser Chromium instalado: `playwright install chromium`

### 🧪 Testes do Sistema

```bash
# Teste completo
python tools/test_08_scraping_system.py
```

**Deve passar:**
- [ ] Módulos de proteção importados
- [ ] Conexão PostgreSQL OK
- [ ] Schema validado
- [ ] Rate limiter funcional
- [ ] Cookie manager funcional
- [ ] Fingerprint rotator funcional
- [ ] Estrutura de arquivos completa

---

## 🛡️ Configurações de Segurança

### Rate Limiting (em `tools/scraper_production.py`)

```python
SmartRateLimiter(
    max_per_hour=50,    # ✅ Recomendado: 30-50
    max_per_day=400,    # ✅ Recomendado: 200-400
    min_delay=5,        # ✅ Recomendado: 5-8
    max_delay=12        # ✅ Recomendado: 12-15
)
```

- [ ] Delays configurados (5-12s)
- [ ] Limite horário ≤ 50
- [ ] Limite diário ≤ 400

### Browser Mode (em `tools/scraper_production.py`)

```python
browser = await playwright.chromium.launch(
    headless=False,  # ✅ CRÍTICO: DEVE SER FALSE
    # ...
)
```

- [ ] `headless=False` (browser visível)
- [ ] Scripts anti-detecção habilitados

### Janelas de Tempo

```python
SAFE_WINDOWS = [
    (3, 6),    # 03:00 - 06:00
    (13, 15),  # 13:00 - 15:00
    (22, 24)   # 22:00 - 00:00
]
```

- [ ] Janelas seguras habilitadas
- [ ] Verificação `is_safe_window()` ativa

---

## 🧪 Teste Inicial (Obrigatório)

### Passo 1: Teste com 5 Imóveis

```bash
python tools/scraper_production.py
```

**Verificar:**
- [ ] Browser abre (modo visível)
- [ ] Cloudflare é bypassed automaticamente
- [ ] Cookies são salvos em `.tmp/cookies.json`
- [ ] Delays entre requests (5-12s)
- [ ] Imóveis salvos no PostgreSQL
- [ ] Nenhum bloqueio detectado
- [ ] Duração: ~5 minutos

### Passo 2: Validar Dados no Banco

```bash
python tools/metrics_dashboard.py
```

**Verificar:**
- [ ] Total de imóveis aumentou
- [ ] Completude média > 0.5 (50%)
- [ ] Imóveis têm dados básicos (título, preço, bairro)

---

## 📊 Monitoramento Durante Execução

### Logs para Observar

**Sinais normais:**
```
✅ Cookies carregados: 3 cookies (1.2h de idade)
✅ Dentro da janela segura!
⏱️  Delay: 7.3s | Hora: 12/50 | Dia: 45/400
✅ Scraping completo: Apartamento Centro...
✅ Imóvel inserido: abc-123-def (completude: 85%)
```

**Sinais de alerta:**
```
🚨 BLOQUEIO DETECTADO!
⏳ Limite horário atingido (50/50)
⚠️  Fora da janela segura
❌ Erro no scraping: timeout
```

### Métricas para Acompanhar

Durante primeiras 50 execuções:
- [ ] Taxa de sucesso > 90%
- [ ] Taxa de bloqueio < 5%
- [ ] Completude média > 70%
- [ ] Tempo médio/imóvel: 30-45s

---

## 🚨 Plano de Contingência

### Se Bloqueado

**Ação imediata:**
```bash
# 1. Deletar cookies
rm .tmp/cookies.json

# 2. Aguardar 1 hora mínimo

# 3. Aumentar delays
# Editar tools/scraper_production.py:
#   min_delay=8  (era 5)
#   max_delay=15 (era 12)

# 4. Reduzir limites
#   max_per_hour=30  (era 50)
#   max_per_day=200  (era 400)

# 5. Testar novamente
python tools/scraper_production.py
```

### Se Muitos Erros (>20%)

**Diagnóstico:**
```bash
# Verificar conectividade
curl -I https://www.infoimoveis.com.br

# Verificar PostgreSQL
docker logs postgres-infoimoveis

# Testar browser
playwright open https://www.infoimoveis.com.br
```

**Ações:**
- [ ] Verificar internet
- [ ] Restart PostgreSQL
- [ ] Reinstalar browser: `playwright install chromium --force`

---

## 📈 Progressão Recomendada

### Dia 1: Validação (5 imóveis)

```bash
python tools/scraper_production.py
```

**Objetivos:**
- [ ] Sistema funciona sem erros
- [ ] Dados salvos corretamente
- [ ] Nenhum bloqueio

### Dia 2: Escala Pequena (50 imóveis)

```bash
python tools/scrape_workflow.py --mode full --max-properties 50
```

**Objetivos:**
- [ ] Discovery funciona
- [ ] Scraping em lote OK
- [ ] Taxa de sucesso > 90%

### Dia 3: Escala Média (100 imóveis)

```bash
python tools/scrape_workflow.py --mode full --max-properties 100
```

**Objetivos:**
- [ ] Sistema estável
- [ ] Sem bloqueios
- [ ] Completude > 70%

### Dia 4+: Produção (200-400/dia)

**Sessão Madrugada (03-06h):**
```bash
python tools/scrape_workflow.py --mode full --max-properties 200
```

**Sessão Almoço (13-15h):**
```bash
python tools/scrape_workflow.py --mode scrape --max-properties 200
```

**Objetivos:**
- [ ] Rotina estabelecida
- [ ] 400 imóveis/dia
- [ ] Sistema autônomo

---

## 📁 Arquivos para Monitorar

### Durante Execução

```bash
# Cookies válidos?
python tools/cookie_manager.py

# Métricas em tempo real
python tools/metrics_dashboard.py

# Último workflow
cat .tmp/workflow_report.json | python -m json.tool
```

### Logs de Erro

Se houver problemas:
- [ ] `.tmp/scraping_metrics.json` (se existir)
- [ ] `.tmp/workflow_report.json`
- [ ] Logs do PostgreSQL: `docker logs postgres-infoimoveis`

---

## ✅ Aprovação Final

**Antes de rodar em produção, confirmar:**

### Técnico
- [ ] Todos os testes passaram
- [ ] Teste com 5 imóveis OK
- [ ] Cookies funcionando
- [ ] Browser em modo headed
- [ ] Delays e limites configurados

### Operacional
- [ ] Horário atual em janela segura
- [ ] PostgreSQL com espaço disponível
- [ ] Conexão estável
- [ ] Tempo disponível (1-6h dependendo do volume)

### Documentação
- [ ] COMECE_AQUI.md lido
- [ ] GUIA_RAPIDO_SCRAPING.md consultado
- [ ] Comandos memorizados
- [ ] Troubleshooting conhecido

---

## 🎯 Critérios de Sucesso

**Sessão considerada bem-sucedida se:**

✅ Taxa de sucesso > 90%
✅ Taxa de bloqueio < 5%
✅ Completude média > 70%
✅ Zero downtime PostgreSQL
✅ Imóveis deduplicados corretamente

**Meta global (1 mês):**
- 10.000+ imóveis no banco
- Sistema rodando autonomamente
- Pronto para fase RAG

---

## 📞 Recursos de Apoio

| Dúvida | Recurso |
|--------|---------|
| Como começar? | `COMECE_AQUI.md` |
| Quick start? | `GUIA_RAPIDO_SCRAPING.md` |
| Configuração? | `workflows/scraping_producao.md` |
| Troubleshooting? | `README.md` |
| Bloqueio? | `workflows/anti-bloqueio.md` |
| Resumo executivo? | `RESUMO_EXECUTIVO_v0.8.md` |
| Estrutura? | `ESTRUTURA_PROJETO.txt` |

---

## 🚀 PRONTO PARA DECOLAR?

Se todos os itens acima estão ✅, você está pronto para:

```bash
python tools/scraper_production.py
```

**Boa sorte! 🎉**

---

**Desenvolvido com WAT Framework**
Versão: 0.8.0
Status: ✅ Operacional
