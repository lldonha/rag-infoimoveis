# 🚀 QUICKSTART - Planejamento de Scraping Escalável

## ⚠️ ESTE É UM PLANO, NÃO UMA IMPLEMENTAÇÃO

**Status Atual:** 📋 PLANEJAMENTO COMPLETO - NADA FOI IMPLEMENTADO AINDA

Você está lendo um guia de planejamento. Todos os scripts, workflows e integrações descritos aqui são **teóricos** e precisam ser implementados e validados.

---

## 📚 Documentos Criados

| Documento | Propósito | Quando Usar |
|-----------|-----------|-------------|
| **STRATEGY.md** | Visão geral da estratégia completa | Entender o contexto geral |
| **SESSIONS_GUIDE.md** | Guia detalhado de cada sessão | Durante implementação (passo a passo) |
| **QUICKSTART_PLANNING.md** (este) | Início rápido | Primeira leitura |
| **delightful-questing-key.md** | Plano técnico completo | Referência técnica detalhada |
| **TODO List** (47 tarefas) | Checklist de implementação | Tracking de progresso |

---

## 🎯 O Que Foi Planejado

### Sistema de Scraping Escalável com 3 Componentes:

```
1. ORQUESTRADOR (workflow_complete.py)
   └─ Executa scraping por categorias
   └─ Gera relatórios JSON
   └─ Salva logs no PostgreSQL

2. PRESETS DE CATEGORIAS (category_presets.py)
   └─ 24 combinações (região × preço × tipo)
   └─ Rotação de 6 dias (5 categorias/dia)

3. AUTOMAÇÃO n8n (Daily_Scraper_InfoImoveis)
   └─ Schedule Trigger (6h da manhã)
   └─ Monitora erros
   └─ Gera dashboard
```

---

## 📊 Dados de Scraping Planejados

### Por Que Coletar?
Os dados servirão para **4 casos de uso**:
1. **ML**: Inferência de preços (modelo XGBoost)
2. **Dashboards**: Estatísticas de mercado
3. **RAG**: Busca semântica com embeddings
4. **API REST**: Consulta de dados (FastAPI)

### O Que Coletar?
- **80-120 imóveis/dia** (rotação gradual, baixo risco de bloqueio)
- **Cobertura completa em 6 dias** (24 combinações de categorias)
- **Completude >80%** (campos críticos: preço, área, tipo, bairro)

### Como Coletar?
- **Playwright Stealth** (já validado, bypass Cloudflare 100%)
- **Rate Limiter** (50/h, 400/dia)
- **Rotação de categorias** (evita sobrecarga em uma região)

---

## 🗺️ Roadmap de Implementação

### Fase 1: Setup (SESSÃO 1) - 30 min
```bash
mkdir -p n8n_workflows logs .tmp/execution_reports
psql ... < sql/execution_logs.sql
# Criar tools/category_presets.py (24 presets)
```
**Output:** Estrutura de diretórios + presets configurados

---

### Fase 2: Orquestrador (SESSÃO 2) - 3h
```bash
# Criar tools/workflow_complete.py
# Integrar: discovery → scraping → save → report
```
**Output:** Script funcional (dry-run testado)

---

### Fase 3: Validação (SESSÕES 3-4) - 3-5h
```bash
# SESSÃO 3: Smoke test (1 categoria, 10 imóveis)
python workflow_complete.py --preset casas_segredo_100_200k --max-per-category 10

# SESSÃO 4: Full day (5 categorias, 100 imóveis)
python workflow_complete.py --day 1 --max-per-category 20
```
**Output:** Dados no PostgreSQL + relatórios JSON

---

### Fase 4: Dashboard + SQL (SESSÃO 5) - 2h
```bash
# Criar tools/generate_dashboard.py (Plotly)
# Criar sql/optimize_for_stats.sql (índices + views)
```
**Output:** Dashboard HTML + queries otimizadas

---

### Fase 5: Automação (SESSÕES 6-7) - 2-3h
```bash
# SESSÃO 6: Configurar n8n workflow
# SESSÃO 7: Documentação completa (SOPs, READMEs)
```
**Output:** Sistema 100% automatizado + documentado

---

## ✅ Checklist de Pré-requisitos

Antes de começar a implementação, valide:

### Infraestrutura
- [ ] Docker PostgreSQL rodando (port 5433)
- [ ] Banco `infoimoveis` criado
- [ ] Tabelas `properties`, `scrape_jobs` existem (schema.sql aplicado)
- [ ] Python 3.10+ instalado
- [ ] Git na branch `planejamento`

### Dependências Python
- [ ] `playwright-stealth` instalado
- [ ] `rich` instalado (logs formatados)
- [ ] `plotly` instalado (dashboard)
- [ ] `pandas` instalado (queries)

### Scripts Existentes (já validados)
- [ ] `tools/scraper_production.py` funciona
- [ ] `tools/scraper_stealth.py` funciona
- [ ] `tools/discovery_filtered.py` funciona
- [ ] `tools/property_saver.py` funciona
- [ ] `tools/rate_limiter.py` funciona

### Validação Rápida
```bash
# 1. PostgreSQL
psql -h localhost -p 5433 -U postgres -d infoimoveis -c "\dt"

# 2. Python imports
python -c "from tools.scraper_stealth import scrape_property_stealth; print('OK')"

# 3. Playwright
python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

---

## 📋 Como Começar

### Opção 1: Implementação Completa (Recomendada)
```bash
# 1. Leia STRATEGY.md (10 min)
# 2. Leia SESSIONS_GUIDE.md - SESSÃO 1 (5 min)
# 3. Execute SESSÃO 1 (30 min)
# 4. Valide checklist de conclusão
# 5. Prossiga para SESSÃO 2
```

### Opção 2: Validação Rápida (Proof of Concept)
```bash
# Apenas para testar conceito, sem automação

# 1. Criar category_presets.py (copiar do SESSIONS_GUIDE.md)
# 2. Criar workflow_complete.py básico (sem relatórios, sem n8n)
# 3. Testar com 1 categoria (5 imóveis)
# 4. Validar inserção no PostgreSQL
```

### Opção 3: Leitura e Análise (Não Implementar)
```bash
# Se você quer apenas entender o plano, sem implementar:

# 1. Leia STRATEGY.md completo
# 2. Leia plano técnico: delightful-questing-key.md
# 3. Analise TODO list (47 tarefas)
# 4. Documente dúvidas/sugestões
```

---

## 🧪 Como Validar o Planejamento

### Perguntas Críticas (responder ANTES de implementar):

1. **Os presets de categorias fazem sentido?**
   - Os slugs de região estão corretos? (`regiao-segredo`, `regiao-centro`, etc)
   - As faixas de preço cobrem o mercado de CG-MS?
   - Há categorias que podem retornar 0 imóveis?

2. **A rotação de 6 dias é viável?**
   - 5 categorias/dia → ~80-120 imóveis/dia → 480-720/semana
   - Isso é suficiente para ML (meta: 1000+)?
   - O rate limit (50/h, 400/dia) será respeitado?

3. **A arquitetura n8n é necessária?**
   - Não seria mais simples usar cron/Task Scheduler?
   - n8n adiciona complexidade desnecessária?

4. **Os 4 casos de uso (ML/Dashboards/RAG/API) são realistas?**
   - Qual é a prioridade real? (talvez focar em 1-2 primeiro)
   - Embeddings/RAG são realmente necessários agora?

### Sugestão: Validar Manualmente
Antes de automatizar, teste **manualmente** os presets no InfoImóveis:

```bash
# Exemplo: Testar preset "casas_segredo_100_200k"
# 1. Abrir https://www.infoimoveis.com.br/
# 2. Filtrar: Tipo=Casa Térrea, Região=Segredo, Preço=100k-200k
# 3. Verificar quantos resultados aparecem
# 4. Se 0 resultados → ajustar preset
# 5. Se 50+ resultados → preset válido
```

---

## 📊 Métricas de Sucesso (a definir)

Antes de implementar, defina metas claras:

| Métrica | Meta Planejada | Validar? |
|---------|----------------|----------|
| Imóveis/dia | 80-120 | É suficiente para ML (1000+ total)? |
| Completude | >80% | Quais campos são obrigatórios? |
| Taxa de sucesso | >95% | O que acontece se <95%? |
| Tempo execução | <4h (5 categorias) | É aceitável? |

---

## 🚨 Riscos Não Mitigados

Problemas que o planejamento NÃO resolve:

1. **Validação de Presets**: Nenhum preset foi testado no InfoImóveis
2. **Rate Limits Reais**: Estimado 50/h, mas pode ser diferente
3. **Complexidade n8n**: Pode ser overkill para scraping diário
4. **Manutenção**: Quem vai monitorar erros diariamente?
5. **Custo**: n8n self-hosted → precisa de servidor sempre ligado

---

## 💡 Recomendações Finais

### Antes de Começar:
1. ✅ **Valide presets manualmente** no InfoImóveis (30 min bem investidos)
2. ✅ **Teste 1 categoria primeiro** (proof of concept)
3. ✅ **Defina prioridade de casos de uso** (ML? Dashboards? RAG?)
4. ✅ **Considere alternativa a n8n** (cron é mais simples)

### Durante Implementação:
1. ✅ **Execute sessão por sessão** (não pule validações)
2. ✅ **Documente problemas em MEMORY.md**
3. ✅ **Ajuste presets conforme necessário**
4. ✅ **Comite após cada sessão bem-sucedida**

### Após Implementação:
1. ✅ **Monitore primeira execução completa** (80-120 imóveis)
2. ✅ **Analise qualidade dos dados** (queries de validação)
3. ✅ **Ajuste rate limits** se necessário
4. ✅ **Documente lições aprendidas** em MEMORY.md

---

## 📞 Próximos Passos

### Passo 1: Decidir se vai implementar
- [ ] Ler STRATEGY.md completo
- [ ] Ler SESSIONS_GUIDE.md - SESSÃO 1
- [ ] Validar pré-requisitos (checklist acima)
- [ ] Decidir: implementar tudo, PoC, ou revisar planejamento?

### Passo 2: Se vai implementar
- [ ] Executar SESSÃO 1 (setup inicial)
- [ ] Validar checklist de conclusão da sessão
- [ ] Comitar: `git commit -m "feat: Sessão 1 concluída - Setup inicial"`
- [ ] Prosseguir para SESSÃO 2

### Passo 3: Se NÃO vai implementar agora
- [ ] Documentar dúvidas/sugestões em MEMORY.md
- [ ] Revisar plano completo (delightful-questing-key.md)
- [ ] Propor ajustes antes de começar

---

## 📚 Documentos de Referência

| Documento | Localização | Quando Ler |
|-----------|-------------|------------|
| **Plano Completo** | `C:\Users\Escritorio LLD\.claude\plans\delightful-questing-key.md` | Detalhes técnicos |
| **Estratégia** | `e:\rag_infoimoeveis\STRATEGY.md` | Visão geral |
| **Guia de Sessões** | `e:\rag_infoimoeveis\SESSIONS_GUIDE.md` | Durante implementação |
| **TODO List** | No Claude Code (47 tarefas) | Tracking de progresso |

---

**Última Atualização:** 2026-02-05
**Status:** 📋 PLANEJAMENTO COMPLETO - AGUARDANDO DECISÃO
**Branch:** planejamento
**Próxima Ação:** Decidir se vai implementar (ler STRATEGY.md primeiro)
