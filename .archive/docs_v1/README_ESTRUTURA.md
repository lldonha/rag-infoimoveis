# 📁 Estrutura de Arquivos - Tools

**Última atualização:** 2026-02-05 15:00

---

## 🟢 PRODUÇÃO - Arquivos Ativos (Usar)

### Scraping Core
| Arquivo | Propósito | Status |
|---------|-----------|--------|
| **scraper_stealth.py** | 🎯 Browser com stealth mode anti-Cloudflare | ✅ PRONTO |
| **scraper_production.py** | Sistema principal de scraping (a integrar stealth) | ✅ ATIVO |
| **discovery_filtered.py** | 🎯 Discovery com filtros (região, preço, tipo) | ✅ PRONTO |

### Suporte & Proteções
| Arquivo | Propósito | Status |
|---------|-----------|--------|
| **rate_limiter.py** | Rate limiting inteligente (50/hora, 400/dia) | ✅ ATIVO |
| **cookie_manager.py** | Gerenciamento de cookies (save/load) | ✅ ATIVO |
| **fingerprint_rotator.py** | Rotação de fingerprints (user-agent, etc) | ✅ ATIVO |
| **human_behavior.py** | Simulação de comportamento humano | ✅ ATIVO |
| **property_saver.py** | Salvar dados no PostgreSQL | ✅ ATIVO |
| **metrics_dashboard.py** | Dashboard de métricas do banco | ✅ ATIVO |

### Workflows & Testes
| Arquivo | Propósito | Status |
|---------|-----------|--------|
| **test_discovery.py** | 🧪 Teste de validação discovery | ✅ ÚTIL |
| **scrape_workflow.py** | Workflow completo (a atualizar) | ⚠️ REVISAR |

---

## 🟡 OBSOLETO - Arquivos Antigos (Mover)

### Testes Antigos (Fase 0.5-0.7)
| Arquivo | Motivo | Ação |
|---------|--------|------|
| **test_05_pgvector.py** | Teste de setup pgvector (fase RAG) | ➡️ obsolete/ |
| **test_06_embeddings.py** | Teste de embeddings (fase RAG) | ➡️ obsolete/ |
| **test_07_rag_system.py** | Teste sistema RAG completo (fase RAG) | ➡️ obsolete/ |
| **test_08_scraping_system.py** | Teste scraping antigo (substituído) | ➡️ obsolete/ |

### Scripts Antigos/Manuais
| Arquivo | Motivo | Ação |
|---------|--------|------|
| **quick_test_scraper.py** | Teste rápido antigo (substituído por test_discovery) | ➡️ obsolete/ |
| **manual_cloudflare_bypass.py** | Bypass manual (substituído por stealth) | ➡️ obsolete/ |
| **inspect_page.py** | Debug manual de páginas (usar só se necessário) | ➡️ obsolete/ |

---

## 🎯 PRÓXIMOS ARQUIVOS A CRIAR

### 1. **workflow_complete.py** (PRIORITÁRIO)
**Objetivo:** Pipeline end-to-end automático

**Features:**
- Discovery com filtros
- Scraping com stealth
- Save no PostgreSQL
- Relatório de métricas

**Uso:**
```bash
python tools/workflow_complete.py \
    --preset segredo_100_200k \
    --max-pages 3 \
    --limit 50 \
    --save-to-db
```

---

### 2. **daily_scraper.py** (MÉDIO)
**Objetivo:** Rotina diária automática

**Features:**
- Múltiplos presets
- Limite: 200-400 imóveis/dia
- Envio de relatório
- Logs estruturados

**Uso:**
```bash
# Manual
python tools/daily_scraper.py

# Agendado (Windows)
schtasks /create /tn "RAG InfoImoveis" /tr "python e:\rag_infoimoeveis\tools\daily_scraper.py" /sc daily /st 03:00
```

---

### 3. **scraper_engine.py** (BAIXO)
**Objetivo:** Sistema multi-estratégia com fallback

**Features:**
```python
class ScraperEngine:
    strategies = [
        PlaywrightStealth,   # 80-90% sucesso
        Crawl4AI,            # 95%+ sucesso (fallback)
        ManualBypass,        # 100% sucesso (último recurso)
    ]
```

---

## 📋 Estrutura Recomendada

```
tools/
├── README_ESTRUTURA.md          ✅ Este arquivo
│
├── 🟢 SCRAPING CORE
│   ├── scraper_stealth.py       ✅ Browser stealth (NOVO)
│   ├── scraper_production.py    ✅ Scraper principal
│   └── discovery_filtered.py    ✅ Discovery com filtros (NOVO)
│
├── 🟢 SUPORTE & PROTEÇÕES
│   ├── rate_limiter.py
│   ├── cookie_manager.py
│   ├── fingerprint_rotator.py
│   ├── human_behavior.py
│   ├── property_saver.py
│   └── metrics_dashboard.py
│
├── 🟢 WORKFLOWS (A CRIAR)
│   ├── workflow_complete.py     ⏳ A CRIAR (próximo)
│   ├── daily_scraper.py         ⏳ A CRIAR
│   └── scrape_workflow.py       ⚠️ REVISAR/ATUALIZAR
│
├── 🟢 TESTES & VALIDAÇÃO
│   └── test_discovery.py        ✅ Útil
│
└── 🟡 OBSOLETO
    ├── test_05_pgvector.py      (fase RAG)
    ├── test_06_embeddings.py    (fase RAG)
    ├── test_07_rag_system.py    (fase RAG)
    ├── test_08_scraping_system.py (antigo)
    ├── quick_test_scraper.py    (substituído)
    ├── manual_cloudflare_bypass.py (substituído)
    └── inspect_page.py          (debug manual)
```

---

## 🚀 Comandos Rápidos

### Teste Rápido (1 URL)
```bash
python -c "import asyncio; from tools.scraper_stealth import test_stealth_single; asyncio.run(test_stealth_single('https://www.infoimoveis.com.br/imovel/venda-casa-terrea-giocondo-orsi/557442', headless=True))"
```

### Teste Discovery
```bash
python tools/test_discovery.py
```

### Métricas do Banco
```bash
python tools/metrics_dashboard.py
```

### Workflow Completo (quando criar)
```bash
python tools/workflow_complete.py --preset segredo_100_200k --limit 50
```

---

## 📖 Documentação de Referência

- **[PROGRESS_2026-02-05.md](../PROGRESS_2026-02-05.md)** - Relatório detalhado dia 2
- **[CONTINUAR_2026-02-06.md](../CONTINUAR_2026-02-06.md)** - Guia próxima sessão
- **[TODO.md](../TODO.md)** - Tarefas pendentes

---

**Branch atual:** `stealth`
**Status:** 🟢 Stealth validado - Pronto para workflow completo
