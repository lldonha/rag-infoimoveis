# 🏠 RAG InfoImóveis - Sistema de Scraping e Análise Imobiliária

**Sistema de scraping inteligente com análise RAG para mercado imobiliário de Campo Grande/MS**

---

## 🎯 Objetivo Principal

Construir dataset de qualidade (85%+ completude) com:
1. **Dados estruturados precisos** (preço, área, quartos, características)
2. **Imagens locais** com análise visual (conservação, idade aparente)
3. **Histórico temporal** para tracking mensal do mercado
4. **Zero bloqueios** via scraping segmentado

---

## 📋 Status Atual

### ✅ O Que Funciona (100%)
- ✅ Scraping com Playwright Stealth (34 imóveis testados, 0 bloqueios)
- ✅ PostgreSQL + pgvector (29 imóveis salvos)
- ✅ Rate limiting inteligente (6-12s delays)
- ✅ Export para Excel formatado
- ✅ 7 camadas anti-bloqueio

### 🟡 Em Desenvolvimento - FASE 1
**Segmentação Inteligente do Scraping**
- Dividir scraping por região/preço (10 segmentos)
- Sessões curtas (20-30min) ao invés de longas (4-6h)
- Delay entre segmentos para evitar bloqueios

📄 **Ver:** [FASE_1_SEGMENTACAO.md](FASE_1_SEGMENTACAO.md)

### 🔜 Próximas Fases
- **FASE 2:** Parser preciso (55% → 85% completude)
- **FASE 3:** Download + análise visual de imagens

---

## 🚀 Quick Start

### 1. Verificar PostgreSQL
```bash
docker ps | grep postgres
```

### 2. Scraping Segmentado (Recomendado)
```bash
# Testar 1 segmento (10 imóveis, ~10min)
python tools/scraper_by_segments.py --segment segredo_100_200k --limit 10

# Batch completo (~690 imóveis, ~1 dia)
python tools/scraper_by_segments.py --all --save-to-db
```

### 3. Ver Resultados
```bash
# Dashboard de métricas
python tools/metrics_dashboard.py

# Export Excel
python tools/export_to_excel.py
```

---

## 📁 Estrutura do Projeto

```
rag_infoimoeveis/
├── tools/                    # Scripts Python
│   ├── scraper_production.py      # Scraper atual (100% funcional)
│   ├── scraper_by_segments.py     # 🟡 Em desenvolvimento (Fase 1)
│   ├── property_saver.py          # Salvamento PostgreSQL
│   └── export_to_excel.py         # Export formatado
│
├── sql/                      # Schemas PostgreSQL
│   └── schema.sql                 # Tabelas + pgvector
│
├── .tmp/                     # Dados temporários
│   ├── *.html                     # HTMLs scrapados
│   └── *.json                     # Resultados intermediários
│
├── .data/                    # Dados permanentes (futuro)
│   └── images/                    # Imagens baixadas (Fase 3)
│
├── worksheet/                # Planilhas de referência
│   └── Casas - CG COMPLETO acima de 90m.xls
│
└── docs principais/
    ├── FASE_1_SEGMENTACAO.md      # 🟡 Plano Fase 1 (atual)
    ├── PLANO_RAG_INFOIMOVEIS.md   # Plano completo original
    ├── RESUMO_EXECUTIVO_v0.8.md   # Sistema v0.8
    ├── RELATORIO_FINAL_2026-02-05.md  # Testes validação
    └── GUIA_RAPIDO_SCRAPING.md    # Quick start

📋 Plano completo 3 fases: .claude/plans/moonlit-waddling-sun.md
📦 Docs arquivados: .archive/docs_old/
```

---

## 🛠️ Stack Técnica

| Componente | Tecnologia | Custo |
|-----------|-----------|-------|
| **Scraping** | Playwright + Stealth | $0 |
| **Banco de Dados** | PostgreSQL 16 + pgvector | $0 |
| **Análise Visual** | Groq/OpenRouter/Ollama (FREE) | $0 |
| **LLMs** | Groq/Mistral/Cohere (FREE tier) | $0 |
| **Embeddings** | Cohere (1000 req/min FREE) | $0 |

**Total:** $0/mês (100% FREE tier)

---

## 📊 Dados Coletados

### Schema Principal (PostgreSQL)

**Tabela `properties`:**
- ID, título, descrição
- Tipo, transação, preço
- Localização (bairro, cidade, endereço)
- Áreas (total, construída)
- Cômodos (quartos, banheiros, suítes, vagas)
- Valores (condomínio, IPTU, R$/m²)
- Características (array JSONB)
- Imagens (URLs array JSONB)
- Anunciante (nome, telefone)
- Metadata (source_url, scraped_at, completeness_score)

**Completude Atual:** 55-65% (meta: 85%+ na Fase 2)

---

## 🧪 Testes

### Validação Completa
```bash
python tools/test_08_scraping_system.py
```

### Teste Rápido (1 imóvel)
```bash
python tools/test_workflow_quick.py
```

### Teste Médio (10 imóveis)
```bash
python tools/test_workflow_10_imoveis.py
```

---

## 📈 Roadmap

### ✅ Concluído (v0.9)
- [x] Scraping robusto com 7 camadas anti-bloqueio
- [x] Playwright Stealth funcionando (headless=True)
- [x] PostgreSQL + pgvector configurado
- [x] Export Excel formatado
- [x] Testes validando 100% sucesso (34 imóveis, 0 bloqueios)

### 🟡 Fase 1 - Em Desenvolvimento (Esta Semana)
- [ ] Implementar `scraper_by_segments.py`
- [ ] Definir 10 segmentos de mercado CG
- [ ] Testar com 1 segmento (10 imóveis)
- [ ] Validar zero bloqueios

### 🔜 Fase 2 - Parser Preciso (Próxima Semana)
- [ ] Corrigir extração de bedrooms/bathrooms/features
- [ ] Implementar fallbacks múltiplos
- [ ] Validar contra planilha exemplo
- [ ] Alcançar 85%+ completude

### 🔜 Fase 3 - Análise Visual (Semana 3)
- [ ] Download local de imagens
- [ ] Análise com Groq/OpenRouter/Ollama
- [ ] Scoring de conservação e apelo
- [ ] Integrar no workflow

---

## 🚨 Troubleshooting

### PostgreSQL não conecta
```bash
docker-compose up -d postgres
docker ps | grep postgres  # Verificar porta 5433
```

### Bloqueio do Cloudflare
- Usar modo segmentado: `--segment <nome>`
- Aumentar delays: `--segment-delay 7200`
- Verificar cookies em `.tmp/cookies.json`

### Completude baixa (<65%)
- Ver relatório: `python tools/metrics_dashboard.py`
- Aguardar Fase 2 (melhorias no parser)

---

## 📚 Documentação Completa

| Arquivo | Conteúdo |
|---------|----------|
| [FASE_1_SEGMENTACAO.md](FASE_1_SEGMENTACAO.md) | 🟡 Plano Fase 1 (atual) |
| [PLANO_RAG_INFOIMOVEIS.md](PLANO_RAG_INFOIMOVEIS.md) | Plano original completo |
| [RESUMO_EXECUTIVO_v0.8.md](RESUMO_EXECUTIVO_v0.8.md) | Sistema v0.8 (validado) |
| [RELATORIO_FINAL_2026-02-05.md](RELATORIO_FINAL_2026-02-05.md) | Testes 100% sucesso |
| [GUIA_RAPIDO_SCRAPING.md](GUIA_RAPIDO_SCRAPING.md) | Quick start scraping |

---

## 🤝 Desenvolvido com WAT Framework

**Workflows, Agents, Tools** - Separação entre reasoning (AI) e execution (código).

---

## 📞 Suporte

- **Fase 1 (atual):** Ver [FASE_1_SEGMENTACAO.md](FASE_1_SEGMENTACAO.md)
- **Troubleshooting:** Seção acima
- **Arquitetura:** [PLANO_RAG_INFOIMOVEIS.md](PLANO_RAG_INFOIMOVEIS.md)

---

**Última atualização:** 2026-02-05
**Branch ativa:** `feat/fase1-segmentacao`
**Status:** 🟡 Fase 1 em desenvolvimento
**Custo:** $0/mês (100% FREE tier)
