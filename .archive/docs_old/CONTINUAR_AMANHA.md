# 🚀 Roteiro para Amanhã (2026-02-05)

## 📋 Checklist Rápido - O que fazer ao iniciar

```bash
# 1. Verificar status atual
cd /e/rag_infoimoeveis
python tools/metrics_dashboard.py

# 2. Ler progresso de ontem
cat PROGRESS_2026-02-04.md
```

---

## 🎯 Tarefa Principal: Testar 50 Imóveis

### Pré-requisitos

1. **Renovar cookies (OBRIGATÓRIO)**
   ```bash
   python tools/manual_cloudflare_bypass.py
   # Aguardar passar o Cloudflare Challenge
   # Cookies são salvos automaticamente em .tmp/cookies.json
   ```

2. **Verificar janela segura**
   - ✅ Melhor: 02:00 - 06:00 (madrugada)
   - ✅ OK: 12:00 - 14:00 (almoço)
   - ❌ Evitar: 08:00 - 11:00, 14:00 - 18:00

### Execução

```bash
# Opção 1: Teste conservador (50 imóveis)
python tools/scraper_production.py --limit 50 --delay 5

# Opção 2: Workflow completo (discovery + scraping)
python tools/scrape_workflow.py --max-pages 5 --delay 5
```

### Métricas para Validar

Após execução, verificar:
```bash
python tools/metrics_dashboard.py
```

**Alvos:**
- [ ] Taxa de sucesso: >90%
- [ ] Completude média: >70%
- [ ] Taxa de bloqueio: <5%
- [ ] Imóveis no banco: 50-55

---

## 🔴 Problema 1: Cloudflare Bloqueando

### Estratégias para Testar (em ordem)

#### Estratégia A: Cookies + Delays ⚡ RÁPIDO
```python
# Em scraper_production.py, aumentar delays
await asyncio.sleep(random.uniform(5, 10))  # Entre páginas
```

**Vantagens:**
- ✅ Fácil de implementar
- ✅ Baixo risco

**Desvantagens:**
- ❌ Mais lento (5-10s por imóvel)

#### Estratégia B: Janelas Seguras 🌙 RECOMENDADO
```bash
# Executar apenas na madrugada
# Adicionar verificação de horário no script

# Linux/Mac (cron)
0 3 * * * cd /e/rag_infoimoeveis && python tools/scrape_workflow.py

# Windows (Task Scheduler)
# Criar tarefa agendada para 03:00
```

**Vantagens:**
- ✅ Menor chance de bloqueio
- ✅ Não interfere com trabalho

**Desvantagens:**
- ❌ Precisa deixar PC ligado

#### Estratégia C: Rotação User-Agent 🔄 MÉDIO
```python
# Adicionar em scraper_production.py
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...',
    # ... mais 5-10 user agents
]

context = await browser.new_context(
    user_agent=random.choice(USER_AGENTS)
)
```

**Arquivo para criar:**
`.tmp/user_agents.txt` com lista de UAs válidos

#### Estratégia D: Proxy Rotativo 🌐 AVANÇADO
**Não fazer agora** - apenas se A+B+C falharem

---

## 🟡 Problema 2: Imagens Não Sendo Capturadas

### Investigação Necessária

```bash
# 1. Inspecionar página com foco em imagens
python .tmp/final_selector_mapping.py
# Verificar seletor de imagens no output

# 2. Testar manualmente no browser
# Abrir DevTools (F12) e executar:
# document.querySelectorAll('img').length
# document.querySelectorAll('img[src*="fotos"]')
```

### Seletores para Testar

```python
img_selectors = [
    'img[src*="/fotos/"]',           # Mais provável
    'img[src*="stored/imoveis"]',    # Alternativa
    '.galeria img',                   # Galeria
    '[data-fancybox] img',           # Lightbox
    '.owl-carousel img',             # Slider
    'a[href*="fotos"] img',          # Link de foto
]
```

**Adicionar no `parse_property_page()`**

---

## 🟢 Melhorias Opcionais (Se sobrar tempo)

### 1. Logging Estruturado

Criar `tools/logger.py`:
```python
import logging

def setup_logger():
    logging.basicConfig(
        filename='.tmp/scraper.log',
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

# Usar no scraper
logger.info(f"Scraped {url}: {completude}%")
logger.warning(f"Cloudflare blocked: {url}")
```

### 2. Alertas Automáticos

Se bloqueio detectado:
```bash
# Via Telegram (se configurado)
curl -X POST "https://api.telegram.org/bot.../sendMessage" \
  -d "chat_id=..." \
  -d "text=🚨 Scraper bloqueado pelo Cloudflare!"
```

### 3. Retry Logic

```python
async def scrape_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await scrape_property(url)
        except CloudflareBlockError:
            if attempt < max_retries - 1:
                await asyncio.sleep(60)  # Aguardar 1min
                continue
            raise
```

---

## 📊 Métricas para Acompanhar

### Durante Execução
```bash
# Terminal 1: Executar scraper
python tools/scraper_production.py --limit 50

# Terminal 2: Monitorar em tempo real
watch -n 5 python tools/metrics_dashboard.py
```

### Após Execução

**1. Completude:**
```sql
SELECT
  AVG(completeness) as avg_completeness,
  COUNT(*) as total
FROM properties
WHERE created_at > NOW() - INTERVAL '1 day';
```

**2. Taxa de sucesso:**
```
Total processados / Total tentados >= 0.90
```

**3. Campos populados:**
```sql
SELECT
  COUNT(title) as titles,
  COUNT(price_brl) as prices,
  COUNT(area_total_m2) as areas,
  COUNT(bedrooms) as bedrooms
FROM properties;
```

---

## 🐛 Problemas Conhecidos & Soluções

### Problema: "Browser closed unexpectedly"
**Causa:** Cloudflare forçou fechamento
**Solução:** Renovar cookies + aumentar delay

### Problema: "Completude 15%"
**Causa:** Página retornou Cloudflare Challenge
**Solução:** Verificar título = "Just a moment" → skip URL

### Problema: "No module named 'playwright'"
**Solução:**
```bash
pip install playwright
playwright install chromium
```

### Problema: "Database connection failed"
**Solução:**
```bash
# Verificar PostgreSQL rodando
docker ps | grep postgres

# Se não estiver:
docker start postgres_rag
```

---

## 📁 Arquivos Importantes

### Para Ler Antes de Começar
```
✅ PROGRESS_2026-02-04.md         (progresso de ontem)
✅ TODO.md                        (tarefas completas)
✅ .tmp/SELECTORS_MAP.md          (guia de seletores)
```

### Para Modificar Hoje
```
⏳ tools/scraper_production.py    (se precisar ajustes)
⏳ tools/scrape_workflow.py       (adicionar delays?)
⏳ TODO.md                        (atualizar progresso)
```

### Para Criar Hoje
```
📝 PROGRESS_2026-02-05.md         (novo relatório)
📝 tools/logger.py                (se implementar logging)
📝 .tmp/user_agents.txt           (se testar rotação)
```

---

## 🎯 Meta do Dia

**Objetivo Principal:**
- [ ] 50 imóveis coletados com sucesso
- [ ] Completude média >70%
- [ ] Sistema rodando de forma estável

**Objetivo Secundário:**
- [ ] Documentar estratégia anti-Cloudflare que funcionou
- [ ] Preparar para coleta automatizada diária

**Objetivo Stretch:**
- [ ] 200 imóveis no banco
- [ ] Sistema agendado rodando automaticamente

---

## ⏰ Planejamento de Tempo

```
08:00 - 08:30  Ler documentação + preparar ambiente
08:30 - 09:00  Renovar cookies + testes iniciais
09:00 - 10:00  Executar scraping de 50 imóveis
10:00 - 10:30  Analisar resultados + ajustes
10:30 - 11:30  Implementar melhorias (se necessário)
11:30 - 12:00  Documentar progresso
```

---

## 🚦 Decisões a Tomar

### Se taxa de sucesso < 80%:
- [ ] Aumentar delays entre páginas
- [ ] Executar apenas em janela segura
- [ ] Implementar rotação de User-Agent

### Se completude < 60%:
- [ ] Revisar seletores de imagens
- [ ] Investigar campos faltantes
- [ ] Adicionar fallbacks

### Se tudo funcionar bem (>90% sucesso):
- [ ] Escalar para 100 imóveis
- [ ] Agendar coleta diária
- [ ] Partir para próxima fase (RAG)

---

## 📞 Comandos de Emergência

### Se tudo travar:
```bash
# Matar todos processos Python
pkill -9 python

# Verificar processos presos
ps aux | grep python
```

### Se Cloudflare bloquear tudo:
```bash
# Parar scraping
# Aguardar 2-4 horas
# Renovar cookies manualmente
python tools/manual_cloudflare_bypass.py
```

### Se banco corromper:
```bash
# Backup antes de qualquer alteração!
docker exec postgres_rag pg_dump -U postgres rag_infoimoveis > backup.sql

# Restaurar se necessário
docker exec -i postgres_rag psql -U postgres rag_infoimoveis < backup.sql
```

---

## ✅ Checklist Final (Antes de Fechar)

Antes de encerrar a sessão de amanhã:

- [ ] Atualizar `TODO.md` com progresso
- [ ] Criar `PROGRESS_2026-02-05.md`
- [ ] Rodar `python tools/metrics_dashboard.py` e salvar output
- [ ] Commit no Git:
  ```bash
  git add .
  git commit -m "feat: Dia 2 - Teste em escala (50 imóveis)"
  git push
  ```

---

**Última atualização:** 2026-02-04 21:45
**Autor:** Claude Code
**Status:** Pronto para começar! 🚀
