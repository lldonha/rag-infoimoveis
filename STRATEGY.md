# 🎯 ESTRATÉGIA DE IMPLEMENTAÇÃO - Scraping Escalável InfoImóveis

## ⚠️ IMPORTANTE: ESTE É UM PLANO NÃO VALIDADO

**Status:** 📋 PLANEJAMENTO COMPLETO - AGUARDANDO VALIDAÇÃO E IMPLEMENTAÇÃO

Este documento contém a estratégia completa para implementar o sistema de scraping escalável, mas **NENHUMA** das funcionalidades foi implementada ou testada ainda. Tudo aqui é um plano teórico que precisa ser executado e validado sessão por sessão.

---

## 📊 Estado Atual vs. Estado Desejado

### ✅ O Que Já Temos (v0.9 - Validado)

- **Playwright Stealth**: Bypass Cloudflare 100% funcional
- **Discovery Filtrado**: `discovery_filtered.py` operacional
- **Parser Completo**: `scraper_production.py` com 85% completude
- **PostgreSQL**: Schema completo (properties, embeddings, scrape_jobs)
- **Rate Limiter**: `SmartRateLimiter` (50/h, 400/dia)
- **Proteções**: fingerprint, cookies, human behavior

### 🎯 O Que Vamos Criar (Planejado)

- **Workflow Orquestrador**: `workflow_complete.py` - executa scraping por categorias
- **Presets de Categorias**: `category_presets.py` - 30 combinações (região × preço × tipo)
- **Rotação Diária**: Sistema de 5 categorias/dia (ciclo 6 dias)
- **Dashboard**: `generate_dashboard.py` - métricas visuais (Plotly)
- **Integração n8n**: Workflow agendado (Schedule Trigger 6h da manhã)
- **Otimizações SQL**: Índices compostos + view materializada
- **Documentação**: SOPs, READMEs, guias de uso

---

## 📐 Arquitetura Planejada (Não Implementada)

```
┌─────────────────────────────────────────────────────────────────┐
│              WORKFLOW ORQUESTRADOR (workflow_complete.py)       │
│                      ❌ NÃO CRIADO AINDA                         │
├─────────────────────────────────────────────────────────────────┤
│ 1. Carrega presets de category_presets.py (❌ não existe)      │
│ 2. Para cada categoria (5/dia):                                │
│    a. Discovery → URLs (✅ já funciona)                         │
│    b. Scraping → PropertyData (✅ já funciona)                  │
│    c. Save → PostgreSQL (✅ já funciona)                        │
│    d. Rate limit (✅ já existe, precisa integrar)               │
│ 3. Gera relatório JSON (❌ não implementado)                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                 AGENDAMENTO n8n (Schedule Trigger)              │
│                      ❌ NÃO CONFIGURADO AINDA                    │
├─────────────────────────────────────────────────────────────────┤
│ - Executa workflow_complete.py 1x/dia (6h)                     │
│ - Rotaciona categorias (Dia 1: Segredo, Dia 2: Centro, etc)    │
│ - Monitora falhas (IF node: errors > 5)                        │
│ - Gera dashboard HTML (❌ script não criado)                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              POSTGRESQL (properties + execution_logs)           │
│              ⚠️ TABELA execution_logs NÃO EXISTE                │
├─────────────────────────────────────────────────────────────────┤
│ - properties table (✅ existe)                                  │
│ - execution_logs table (❌ precisa criar)                       │
│ - market_stats view (❌ precisa criar)                          │
│ - Índices otimizados (❌ precisa aplicar)                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Categorias de Scraping (Planejadas)

### Rotação de 6 Dias (5 categorias/dia = ~80-120 imóveis/dia)

**Dia 1: Casas Segredo/Prosa/Centro**
- casas_segredo_100_200k
- casas_segredo_200_400k
- casas_prosa_100_200k
- casas_centro_200_400k
- sobrados_segredo

**Dia 2: Apartamentos Centro/Bandeirantes**
- apts_centro_100_200k
- apts_bandeirantes_200_400k
- apts_prosa_200_400k
- casas_bandeirantes_100_200k

**Dia 3: Casas Vila Carlota/Tiradentes + Sobrados**
- casas_vila_carlota
- casas_tiradentes
- sobrados_prosa
- apts_jardim_estados

**Dia 4: Apartamentos Premium + Sobrados**
- apts_prosa_400_800k
- apts_centro_400_800k
- sobrados_centro
- casas_segredo_400_800k

**Dia 5: Terrenos + Comercial**
- terrenos_all_regions
- comercial_centro
- comercial_bandeirantes

**Dia 6: Luxo + Coberturas**
- coberturas_all
- luxury_segredo
- luxury_prosa
- casas_acima_800k

**⚠️ Atenção:** Estes presets são teóricos. Precisam ser validados no InfoImóveis para verificar:
- Se as combinações retornam imóveis suficientes
- Se os slugs de região estão corretos
- Se os filtros de preço funcionam como esperado

---

## 📋 Checklist de Implementação (7 Sessões)

### ✅ SESSÃO 1: Setup Inicial (~30 min)
- [ ] Criar diretórios: `n8n_workflows/`, `logs/`, `.tmp/execution_reports/`
- [ ] Criar `sql/execution_logs.sql`
- [ ] Executar SQL no PostgreSQL (verificar se tabela foi criada)
- [ ] Validar deps Python: `pip list | grep -E "(playwright-stealth|rich|plotly|pandas)"`
- [ ] Criar `tools/category_presets.py` (30 presets)
- [ ] Testar: `python -c "from category_presets import get_presets_for_day; print(get_presets_for_day(1))"`

**Validação de Sucesso:**
- ✅ Tabela `execution_logs` existe no PostgreSQL
- ✅ `category_presets.py` importa sem erros
- ✅ `get_presets_for_day(1)` retorna lista de 5 presets

---

### ✅ SESSÃO 2: workflow_complete.py (~3h)
- [ ] Criar arquivo com estrutura básica (imports, argparse)
- [ ] Implementar `run_category()` (discovery + scraping + save)
- [ ] Implementar `main()` (loop por categorias)
- [ ] Adicionar `generate_report()` + `save_report()`
- [ ] Adicionar `save_to_postgres()` (insert execution_logs)
- [ ] Logging com `rich` (progress bars)
- [ ] Teste dry-run: `python workflow_complete.py --preset casas_segredo_100_200k --max-per-category 5 --dry-run`

**Validação de Sucesso:**
- ✅ Dry-run executa sem erros
- ✅ Logs aparecem no console (rich formatting)
- ✅ Não faz scraping real (dry-run apenas simula)

---

### ✅ SESSÃO 3: Smoke Test (1 categoria) (~1h)
- [ ] Executar: `python workflow_complete.py --preset casas_segredo_100_200k --max-per-category 10 --headless`
- [ ] Verificar JSON gerado em `.tmp/execution_reports/`
- [ ] Query PostgreSQL: `SELECT COUNT(*) FROM properties WHERE scraped_at > NOW() - INTERVAL '1 hour'`
- [ ] Query completude: `SELECT AVG(data_completeness) FROM properties WHERE scraped_at > NOW() - INTERVAL '1 hour'`
- [ ] Criar `sql/validate_data.sql` (queries de validação)
- [ ] Executar validação completa

**Validação de Sucesso:**
- ✅ 8-12 imóveis inseridos (pode variar conforme disponibilidade)
- ✅ Completude média >80%
- ✅ JSON de relatório contém execution_id, properties_collected, etc
- ✅ 0 erros de Cloudflare

---

### ✅ SESSÃO 4: Teste Full Day (5 categorias) (~2-4h)
- [ ] Executar: `python workflow_complete.py --day 1 --max-per-category 20 --respect-rate-limit`
- [ ] Monitorar logs: verificar pausas do rate limiter
- [ ] Query execution_logs: `SELECT * FROM execution_logs ORDER BY started_at DESC LIMIT 1`
- [ ] Validar tempo de execução <4h
- [ ] Validar 80-100 imóveis coletados
- [ ] Analisar errors_json se houver falhas

**Validação de Sucesso:**
- ✅ 80-100 imóveis coletados (5 categorias × ~20 cada)
- ✅ Rate limiter pausou quando atingiu 50/h
- ✅ Execution_logs populado com stats corretos
- ✅ Taxa de sucesso >95%

---

### ✅ SESSÃO 5: Dashboard + SQL Optimization (~2h)
- [ ] Criar `tools/generate_dashboard.py`
- [ ] Implementar queries (completude, evolução, top bairros)
- [ ] Implementar visualizações Plotly (barras, linha, boxplot)
- [ ] Gerar HTML em `.tmp/dashboard_latest.html`
- [ ] Criar `sql/optimize_for_stats.sql` (índices + view materializada)
- [ ] Executar SQL de otimização
- [ ] Adicionar `refresh_stats_views()` ao `workflow_complete.py`

**Validação de Sucesso:**
- ✅ Dashboard HTML abre no navegador
- ✅ Gráficos renderizam corretamente
- ✅ View materializada criada
- ✅ Queries de dashboard executam em <500ms

---

### ✅ SESSÃO 6: Integração n8n (~1-2h)
- [ ] Criar workflow n8n: Schedule Trigger (cron: `0 6 * * *`)
- [ ] Adicionar node Execute Command (Python workflow_complete.py)
- [ ] Adicionar node Parse JSON
- [ ] Adicionar node PostgreSQL (insert execution_logs)
- [ ] Adicionar node IF (condition: `errors.length > 5`)
- [ ] Configurar PostgreSQL credential
- [ ] Testar execução manual
- [ ] Exportar para `n8n_workflows/Daily_Scraper_InfoImoveis.json`
- [ ] Ativar workflow (marcar como Active)

**Validação de Sucesso:**
- ✅ Workflow n8n executa sem erros
- ✅ PostgreSQL recebe log da execução
- ✅ IF node detecta condição corretamente
- ✅ Schedule trigger está ativo (verificar na UI)

---

### ✅ SESSÃO 7: Documentação Final (~1h)
- [ ] Criar `workflows/scraping_at_scale.md` (SOP completo)
- [ ] Criar `tools/README_WORKFLOWS.md` (docs técnica)
- [ ] Criar `n8n_workflows/README_N8N.md` (guia de importação)
- [ ] Atualizar `MEMORY.md` com aprendizados
- [ ] Atualizar `README.md` (status v1.0)
- [ ] Criar `CHANGELOG.md`
- [ ] Git commit final

**Validação de Sucesso:**
- ✅ Todos os READMEs criados
- ✅ SOP completo e testável
- ✅ Commit feito na branch `planejamento`

---

## 🎯 Objetivos de Uso dos Dados

Os dados coletados servirão para **4 casos de uso principais**:

### 1. Inferência de Preços (ML)
- **Meta:** 1000+ imóveis
- **Features:** area_m2, bedrooms, bathrooms, neighborhood, property_type
- **Modelo:** XGBoost para predição de preços

### 2. Estatísticas de Mercado (Dashboards)
- **Queries:** AVG(price_brl) GROUP BY neighborhood
- **Views:** market_stats_by_region (refresh diário)

### 3. Busca Semântica (RAG)
- **Embeddings:** Cohere embed-v3 (1024 dims)
- **Campos:** title + description + features

### 4. API REST (FastAPI - futuro)
- **Endpoints:** /properties, /search, /stats/market

---

## 🚨 Riscos e Mitigações Planejadas

| Risco | Mitigação Planejada |
|-------|---------------------|
| **Bloqueio Cloudflare** | Playwright Stealth (já validado) + fallback Crawl4AI |
| **Rate Limit** | SmartRateLimiter (já existe) + rotação de categorias |
| **Timeout Discovery** | Retry com exponential backoff (3x) |
| **Database Lock** | Usar bulk_insert (já implementado) |
| **Presets Inválidos** | Validar manualmente cada preset no InfoImóveis |

---

## 📊 Métricas de Sucesso (a validar)

| Métrica | Meta | Status |
|---------|------|--------|
| **Taxa de coleta** | 80-120 imóveis/dia | ❌ Não validado |
| **Completude média** | >80% | ❌ Não validado |
| **Taxa de sucesso** | >95% | ❌ Não validado |
| **Tempo execução** | <4h (5 categorias) | ❌ Não validado |
| **Zero duplicatas** | 100% dedup | ✅ Garantido por UNIQUE constraint |

---

## 📖 Referências Importantes

### Arquivos Existentes (já validados)
- `tools/scraper_production.py` - Parser completo
- `tools/scraper_stealth.py` - Playwright Stealth
- `tools/discovery_filtered.py` - Discovery filtrado
- `tools/property_saver.py` - Database saver
- `tools/rate_limiter.py` - Rate limiting
- `sql/schema.sql` - Schema completo do PostgreSQL

### Arquivos a Criar (planejados)
- `tools/workflow_complete.py` ❌
- `tools/category_presets.py` ❌
- `tools/generate_dashboard.py` ❌
- `sql/execution_logs.sql` ❌
- `sql/optimize_for_stats.sql` ❌
- `workflows/scraping_at_scale.md` ❌
- `n8n_workflows/Daily_Scraper_InfoImoveis.json` ❌

---

## 💡 Lições Aprendidas (atualizar após validação)

**Após SESSÃO 3 (Smoke Test):**
- [ ] Rate limits reais observados vs. estimados
- [ ] Presets que funcionaram vs. não funcionaram
- [ ] Campos com maior % de NULL

**Após SESSÃO 4 (Full Day):**
- [ ] Tempo real de execução vs. estimado
- [ ] Combinações de categorias mais produtivas
- [ ] Horários ideais para scraping

**Após SESSÃO 6 (n8n):**
- [ ] Problemas de integração encontrados
- [ ] Ajustes necessários na configuração
- [ ] Performance do workflow n8n

---

## ✅ Como Usar Esta Estratégia

### Para Começar:
1. Leia o **TODO List** completo (47 tarefas divididas em 7 sessões)
2. Execute **SESSÃO 1** primeiro (setup inicial)
3. **Valide cada sessão** antes de passar para a próxima
4. **Documente problemas** em MEMORY.md

### Para Retomar:
1. Veja qual sessão está em andamento no TODO List
2. Leia a seção correspondente neste documento
3. Execute os passos não concluídos
4. Valide antes de avançar

### Para Ajustar:
- Se um preset não funcionar → ajustar `category_presets.py`
- Se rate limit atingir antes → ajustar `max_per_category`
- Se completude baixa → revisar `scraper_production.py`

---

## 🔗 Plano Completo

O plano detalhado está em: `C:\Users\Escritorio LLD\.claude\plans\delightful-questing-key.md`

Este documento é um resumo executivo. Para detalhes técnicos completos, consulte o plano.

---

**Última Atualização:** 2026-02-05
**Status:** 📋 PLANEJAMENTO COMPLETO - AGUARDANDO IMPLEMENTAÇÃO
**Branch:** planejamento
**Próximo Passo:** Executar SESSÃO 1 (Setup Inicial)
