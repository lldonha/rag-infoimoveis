# 📋 TODO - Sistema RAG InfoImóveis

**Última atualização:** 2026-02-04
**Prioridade:** 🔴 Alta | 🟡 Média | 🟢 Baixa

---

## 🔴 CRÍTICO - Fazer AGORA

### 1. Corrigir `scraper_production.py` (Funções Assíncronas)
**Problema:** Travamento nas funções de comportamento humano

**Arquivo:** [tools/human_behavior.py](tools/human_behavior.py)

**Mudanças necessárias:**
```python
# human_scroll()
- def human_scroll(page, duration: float = None):
+ async def human_scroll(page, duration: float = None):
    # ...
-   time.sleep(step_duration + random.uniform(-0.2, 0.3))
+   await asyncio.sleep(step_duration + random.uniform(-0.2, 0.3))

# human_mouse_move()
- def human_mouse_move(page, num_moves: int = None):
+ async def human_mouse_move(page, num_moves: int = None):
    # ...
-   time.sleep(random.uniform(0.3, 0.8))
+   await asyncio.sleep(random.uniform(0.3, 0.8))

# simulate_reading()
- def simulate_reading(page, min_time: float = 5, max_time: float = 10):
+ async def simulate_reading(page, min_time: float = 5, max_time: float = 10):
-   time.sleep(read_time)
+   await asyncio.sleep(read_time)

# random_pause()
- def random_pause(probability: float = 0.1):
+ async def random_pause(probability: float = 0.1):
    if random.random() < probability:
-       time.sleep(random.uniform(3, 8))
+       await asyncio.sleep(random.uniform(3, 8))

# wait_for_page_load()
- def wait_for_page_load(page, min_time: float = 2, max_time: float = 5):
+ async def wait_for_page_load(page, min_time: float = 2, max_time: float = 5):
-   time.sleep(random.uniform(min_time, max_time))
+   await asyncio.sleep(random.uniform(min_time, max_time))
```

**Depois em `scraper_production.py`:**
```python
# Linha 300
- human_scroll(page)
+ await human_scroll(page)

# Linha 301
- human_mouse_move(page)
+ await human_mouse_move(page)

# Linha 302
- simulate_reading(page, min_time=3, max_time=6)
+ await simulate_reading(page, min_time=3, max_time=6)

# Linha 290
- wait_for_page_load(page, 3, 6)
+ await wait_for_page_load(page, 3, 6)

# Linha 314
- random_pause(probability=0.1)
+ await random_pause(probability=0.1)
```

---

## 🔴 Alta Prioridade - Esta Semana

### 2. Mapear Seletores HTML Corretos
**Objetivo:** Aumentar completude de 15% → 70%+

**Tarefas:**
- [ ] Inspecionar HTML de imóveis reais (usar `inspect_page.py`)
- [ ] Mapear seletores para todos os campos
- [ ] Atualizar `parse_property_page()` em `scraper_production.py`
- [ ] Testar e validar parsing

### 3. Implementar Discovery de URLs
**Problema:** URLs genéricas de listagem retornam 404

**Opções:**
- [ ] Sitemap XML
- [ ] API interna
- [ ] Scraping incremental
- [ ] Usar `property_urls.json` como seed

### 4. Testar Scraping em Escala (50 Imóveis)
- [ ] Corrigir async functions
- [ ] Executar workflow com 50 imóveis
- [ ] Validar métricas (sucesso >90%, bloqueio <5%)

---

## 🟡 Média Prioridade - Próximas 2 Semanas

### 5. Rotina de Coleta Diária Automatizada
- [ ] Agendamento (cron/Task Scheduler)
- [ ] Janelas de execução (madrugada, almoço)
- [ ] Renovação automática de cookies
- [ ] Logs e alertas

### 6. Sistema de Métricas e Monitoramento
- [ ] Dashboard em tempo real
- [ ] Alertas de bloqueio
- [ ] Logs estruturados

### 7. Validação de Qualidade dos Dados
- [ ] Schema validation
- [ ] Detecção de duplicatas
- [ ] Limpeza e normalização

### 8. Integração com n8n
- [ ] Workflow de execução agendada
- [ ] Notificações (Telegram/Email)
- [ ] Dashboard de métricas

---

## 🟢 Baixa Prioridade - Futuro (1+ mês)

### 9. Sistema RAG Completo
- [ ] Embeddings e vector search
- [ ] Interface de consulta (chat)

### 10. Features Avançadas
- [ ] Análise de preços
- [ ] Tendências de mercado
- [ ] Geolocalização

### 11. Deploy em Produção
- [ ] Dockerize completo
- [ ] CI/CD
- [ ] Backup automático

---

## 🐛 Bugs Conhecidos

| ID | Descrição | Prioridade | Arquivo |
|----|-----------|------------|---------|
| BUG-001 | Funções síncronas em contexto async | 🔴 Crítico | `human_behavior.py` |
| BUG-002 | URLs de listagem retornam 404 | 🔴 Alta | Discovery workflow |
| BUG-003 | Completude baixa (15%) | 🟡 Média | `scraper_production.py` |
| BUG-004 | Título extraído incorreto | 🟡 Média | Seletores HTML |

---

## ✅ Concluído Recentemente

- [x] Playwright instalado
- [x] Bypass Cloudflare manual
- [x] Cookies persistentes funcionando
- [x] Quick test scraper criado
- [x] 5 imóveis coletados com sucesso
- [x] PostgreSQL integrado
- [x] Metrics dashboard básico
- [x] Page inspector para debug

---

## 📊 Metas Semanais

### Semana 1 (Atual - 2026-02-04)
- [x] Setup e validação inicial (5 imóveis) ✅
- [ ] Corrigir async functions ⏳
- [ ] Testar com 50 imóveis ⏳

### Semana 2
- [ ] Completude > 70%
- [ ] 200 imóveis no banco

### Semana 3
- [ ] 500 imóveis no banco
- [ ] Rotina diária automatizada

### Semana 4
- [ ] 1000+ imóveis no banco
- [ ] Preparar para fase RAG

---

## 🎯 Meta Final

**Banco de dados robusto com 10.000+ imóveis de Campo Grande/MS**

- Completude média: >80%
- Taxa de sucesso: >95%
- Atualização diária: 200-400 imóveis novos
- Sistema autônomo e resiliente

---

**Última revisão:** 2026-02-04
**Próxima revisão:** 2026-02-07
