# Workflow de Scraping em Produção

## Status: ✅ Pronto para Uso

---

## 📋 Visão Geral

Sistema completo de scraping do InfoImóveis com **7 camadas de proteção anti-bloqueio** e integração direta com PostgreSQL.

---

## 🛠️ Arquitetura

```
scrape_workflow.py (Orquestrador)
    ↓
    ├─→ Fase 1: Discovery (discover_property_urls)
    │   └─→ Coleta URLs de páginas de busca
    │
    ├─→ Fase 2: Scraping (scraper_production.py)
    │   ├─→ rate_limiter.py (delays, limites)
    │   ├─→ cookie_manager.py (sessão persistente)
    │   ├─→ fingerprint_rotator.py (identidade)
    │   ├─→ human_behavior.py (comportamento humano)
    │   └─→ property_saver.py (PostgreSQL)
    │
    └─→ Fase 3: Monitoramento (metrics_dashboard.py)
```

---

## 🚀 Quick Start

### 1. Preparação

```bash
# Verificar que PostgreSQL está rodando
docker ps | grep postgres

# Ativar ambiente Python
# (se usando venv)

# Instalar dependências (se necessário)
pip install playwright psycopg2-binary python-dotenv
playwright install chromium
```

### 2. Teste Rápido (5 imóveis)

```bash
# Opção A: Usar scraper direto
python tools/scraper_production.py

# Opção B: Workflow completo (discovery + scraping)
python tools/scrape_workflow.py --mode full --max-properties 5
```

### 3. Dashboard de Monitoramento

```bash
python tools/metrics_dashboard.py
```

---

## 🎯 Modos de Operação

### Modo 1: Workflow Completo (Recomendado)

```bash
# Discovery + Scraping + Armazenamento
python tools/scrape_workflow.py --mode full \
    --max-pages 3 \
    --max-properties 50
```

**O que faz:**
1. Navega por 3 páginas de busca
2. Descobre URLs de imóveis
3. Faz scraping de até 50 imóveis
4. Salva no PostgreSQL
5. Gera relatório

### Modo 2: Discovery Separado

```bash
# Apenas descobrir URLs (não faz scraping)
python tools/scrape_workflow.py --mode discovery --max-pages 5
```

**Resultado:** `.tmp/discovered_urls.json` com URLs descobertas

### Modo 3: Scraping de Lista Existente

```bash
# Scraping de URLs previamente descobertas
python tools/scrape_workflow.py --mode scrape --max-properties 100
```

**Pré-requisito:** Arquivo `.tmp/discovered_urls.json` deve existir

### Modo 4: Scraper Direto (Teste)

```bash
# Scraping direto de URLs conhecidas
python tools/scraper_production.py
```

**Usa:** `.tmp/property_urls.json` (URLs já conhecidas)

---

## 🛡️ Proteções Anti-Bloqueio

### Camada 1: Rate Limiting Agressivo

```python
# Configuração padrão
max_per_hour = 50      # 50 requests/hora
max_per_day = 400      # 400 requests/dia
min_delay = 5s         # Mínimo 5 segundos
max_delay = 12s        # Máximo 12 segundos
```

**Ação:** Delays aleatórios entre 5-12s, limites rígidos

### Camada 2: Janelas Seguras

```python
SAFE_WINDOWS = [
    (3, 6),    # 03:00 - 06:00 (madrugada)
    (13, 15),  # 13:00 - 15:00 (almoço)
    (22, 24)   # 22:00 - 00:00 (noite)
]
```

**Ação:** Scraping apenas em horários de baixo tráfego

### Camada 3: Cookies Persistentes

- Salva cookies após bypass Cloudflare
- Reutiliza por 6 horas
- Renovação automática ao expirar

### Camada 4: Fingerprint Rotation

- User-Agent aleatório (Chrome/Firefox)
- Viewport aleatório (1920x1080, 1366x768, etc)
- Timezone do Brasil (Campo Grande, São Paulo)

### Camada 5: Comportamento Humano

- Scroll gradual (3-7 steps)
- Movimento de mouse
- Pausas aleatórias (10% de chance de 15-45s)
- Tempo de "leitura" variável

### Camada 6: Browser Real

```python
headless = False  # CRÍTICO: Browser visível
```

**Por quê:** Cloudflare detecta headless browsers

### Camada 7: Detecção de Bloqueio

- Monitora sinais de bloqueio
- Pausa automática de 1h se detectado
- Renovação forçada de cookies

---

## 📊 Monitoramento

### Dashboard em Tempo Real

```bash
python tools/metrics_dashboard.py
```

**Mostra:**
- Total de imóveis no banco
- Imóveis nas últimas 24h/7d
- Completude média dos dados
- Distribuição por qualidade
- Top bairros mais caros
- Oportunidades (abaixo do mercado)

### Exportar Relatório JSON

```bash
python tools/metrics_dashboard.py --export
# Resultado: .tmp/dashboard_report_YYYYMMDD_HHMMSS.json
```

---

## 🗄️ Banco de Dados

### Inserção Automática

Todos os imóveis são automaticamente salvos em `properties` table:

```sql
SELECT id, title, neighborhood, price_brl, data_completeness
FROM properties
ORDER BY scraped_at DESC
LIMIT 10;
```

### Deduplicação

- Baseada em `source_url` (UNIQUE constraint)
- Se URL já existe: atualiza dados
- Se URL nova: insere novo registro

### Score de Completude

Calculado automaticamente (0.0 a 1.0):

```
Peso dos campos:
- Preço (price_brl): 3x
- Título/Descrição/Tipo/Transação/Bairro: 2x
- Área/Quartos/Banheiros/Imagens: 1x
```

---

## 📈 Escalando Produção

### Para 100-500 Imóveis/Dia

```bash
# Sessão da manhã (03:00 - 06:00)
python tools/scrape_workflow.py --mode full \
    --max-pages 10 \
    --max-properties 200

# Sessão da tarde (13:00 - 15:00)
python tools/scrape_workflow.py --mode scrape \
    --max-properties 200

# Total: ~400 imóveis/dia (dentro do limite seguro)
```

### Para 1000+ Imóveis/Dia

**Opção A: Múltiplos IPs**
- Rodar de máquinas diferentes
- Casa + trabalho + cloud VPS

**Opção B: Proxy Residencial (Pago)**
- Bright Data, Oxylabs, Smartproxy
- Custo: $8-15/GB

**Opção C: Scraping Seletivo**
- Apenas imóveis novos (últimos 7 dias)
- Apenas mudanças de preço
- Filtros por bairro/tipo

---

## 🔧 Troubleshooting

### Erro: "BLOQUEIO DETECTADO"

**Causa:** IP bloqueado por Cloudflare

**Solução:**
1. Aguardar 1 hora (pausa automática)
2. Deletar cookies: `rm .tmp/cookies.json`
3. Mudar de rede (celular, VPN)
4. Aumentar delays: `min_delay=8, max_delay=15`

### Erro: "Fora da janela segura"

**Causa:** Tentou scraping fora das janelas permitidas

**Solução:**
- Aguardar próxima janela (automático)
- Ou desabilitar verificação (NÃO recomendado)

### Erro: "Limite horário atingido"

**Causa:** Atingiu 50 requests/hora

**Solução:**
- Aguardar reset automático
- Ou reduzir `max_per_hour` se bloqueios frequentes

### Erro: "Database connection failed"

**Causa:** PostgreSQL não está rodando

**Solução:**
```bash
docker-compose up -d postgres
docker ps | grep postgres
```

### Erro: "No URLs discovered"

**Causa:** Discovery falhou

**Solução:**
1. Verificar se site está acessível: https://www.infoimoveis.com.br
2. Aumentar `max_pages`
3. Verificar seletores CSS (podem ter mudado)

---

## 📁 Arquivos Gerados

```
.tmp/
├── cookies.json                      # Cookies Cloudflare (6h TTL)
├── discovered_urls.json              # URLs descobertas no discovery
├── workflow_report.json              # Relatório do último workflow
├── dashboard_report_*.json           # Exportações do dashboard
└── scraping_metrics.json             # Métricas em tempo real (futuro)
```

---

## ⚙️ Configurações Avançadas

### Ajustar Rate Limits

```python
# Em scraper_production.py ou scrape_workflow.py
rate_limiter = SmartRateLimiter(
    max_per_hour=30,    # Mais conservador
    max_per_day=200,
    min_delay=8,        # Delays maiores
    max_delay=15
)
```

### Desabilitar Janelas Seguras (Risco)

```python
# Comentar linha
# wait_for_safe_window()
```

**⚠️ AVISO:** Aumenta risco de bloqueio!

### Modo Headless (NÃO Recomendado)

```python
browser = await playwright.chromium.launch(
    headless=True  # Cloudflare detecta!
)
```

**⚠️ AVISO:** Apenas para testes locais, não em produção

---

## 🎯 Checklist Pré-Produção

Antes de rodar scraping em larga escala:

```
[ ] PostgreSQL rodando (porta 5433)
[ ] API keys configuradas no .env (se usar OCR/LLM)
[ ] Browser headed mode (headless=False)
[ ] Rate limits conservadores (50/hora, 400/dia)
[ ] Janelas seguras habilitadas
[ ] Cookies funcionando (.tmp/cookies.json)
[ ] Teste com 5-10 imóveis primeiro
[ ] Dashboard funcionando
```

---

## 📚 Referências

| Arquivo | Descrição |
|---------|-----------|
| [scraper_production.py](../tools/scraper_production.py) | Scraper principal |
| [scrape_workflow.py](../tools/scrape_workflow.py) | Orquestrador completo |
| [property_saver.py](../tools/property_saver.py) | Integração PostgreSQL |
| [metrics_dashboard.py](../tools/metrics_dashboard.py) | Dashboard de métricas |
| [anti-bloqueio.md](./anti-bloqueio.md) | Documentação das proteções |

---

## 🚨 Limites Recomendados

| Parâmetro | Conservador | Agressivo | Extremo |
|-----------|-------------|-----------|---------|
| Delay (s) | 8-15 | 5-12 | 3-8 |
| Por hora | 30 | 50 | 80 |
| Por dia | 200 | 400 | 600 |
| Risco bloqueio | Baixo | Médio | Alto |

**Recomendação:** Começar **Conservador**, aumentar gradualmente se não houver bloqueios.

---

**Desenvolvido com WAT Framework**
Versão: 0.8.0 (Scraping Produção)
Última atualização: 2026-02-05
