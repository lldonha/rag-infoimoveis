# 📋 TODO - Sistema RAG InfoImóveis

**Última atualização:** 2026-02-05
**Prioridade:** 🔴 Alta | 🟡 Média | 🟢 Baixa

---

## 🔴 CRÍTICO - Fazer AGORA

### 1. Validar Playwright Stealth em Batch ⏳
**Status:** Implementado, aguardando teste em escala

**Comandos:**
```bash
# Teste com 5 URLs
python tools/quick_test_stealth.py

# Meta: 4/5 (80%) sucesso
# Se PASS → Integrar em production
# Se FAIL → Instalar Crawl4AI
```

**Critérios de validação:**
- [ ] Taxa de sucesso >80% (4/5 URLs)
- [ ] headless=True funcional
- [ ] Sem bloqueios Cloudflare ("Just a moment")
- [ ] Completude >0% (idealmente >65%)

**Arquivo:** [tools/quick_test_stealth.py](tools/quick_test_stealth.py)

---

### 2. Corrigir Bug: Completude 0% 🐛
**Problema:** Parser retorna dados mas completeness=0

**Evidência:**
```
✅ SUCESSO
   Título: Linda casa de esquina em frente a praça...
   Completude: 0%
```

**Investigação necessária:**
- [ ] Verificar como `completeness` é calculado em PropertyData
- [ ] Confirmar se campos estão sendo populados
- [ ] Testar com múltiplos imóveis

**Arquivo:** [tools/scraper_production.py](tools/scraper_production.py) (linha ~119-321)

---

### 3. Validar Discovery Filtrado ⏳
**Status:** Implementado, precisa teste

**Teste do preset do usuário:**
```bash
python -c "
import asyncio
from tools.discovery_filtered import discover_by_preset

async def main():
    # Busca exata do usuário:
    # Casa térrea, Segredo, R$ 100k-200k
    urls = await discover_by_preset('segredo_100_200k', max_pages=2)
    print(f'\nTotal: {len(urls)} imóveis encontrados')
    for i, url in enumerate(urls[:5], 1):
        print(f'  {i}. {url}')

asyncio.run(main())
"
```

**Critérios de validação:**
- [ ] Descobre >20 imóveis
- [ ] URLs corretas (padrão /imovel/venda-*)
- [ ] Sem timeout (30s)
- [ ] Preset 'segredo_100_200k' funciona

**Arquivo:** [tools/discovery_filtered.py](tools/discovery_filtered.py)

---

## 🔴 Alta Prioridade - Hoje/Amanhã

### 4. Integrar Stealth em Production (SE teste #1 passar)
**Objetivo:** Substituir browser padrão por stealth browser

**Mudanças em [scraper_production.py](tools/scraper_production.py):**
```python
# ANTES:
from playwright.async_api import async_playwright

async def create_browser():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)  # ⚠️ headless=False
    # ...

# DEPOIS:
from scraper_stealth import create_stealth_browser

async def scrape_property(url: str, use_stealth=True):
    if use_stealth:
        playwright, browser, context, page = await create_stealth_browser(
            headless=True  # ✅ Agora funciona!
        )
    else:
        # Fallback para método antigo
        # ...
```

**Teste:**
```bash
python tools/scraper_production.py --limit 50 --strategy stealth
```

---

### 5. Workflow Completo: Discovery → Scraping (1h)
**Objetivo:** Pipeline end-to-end funcional

**Fluxo:**
```
1. Discovery Filtrado → Lista de 50-100 URLs
   ↓
2. Scraping com Stealth → Dados extraídos
   ↓
3. Save PostgreSQL → Banco populado
   ↓
4. Métricas Dashboard → Validação
```

**Comando:**
```bash
python tools/scrape_workflow.py --preset segredo_100_200k --max-pages 5 --use-stealth
```

**Validação:**
- [ ] 50+ imóveis descobertos
- [ ] >90% taxa de sucesso no scraping
- [ ] >70% completude média
- [ ] <30min tempo total
- [ ] Dados salvos no PostgreSQL

---

## 🟡 Média Prioridade - Esta Semana

### 6. Cookie Manager Automático
**Objetivo:** Auto-renovação de cookies a cada 30min

**Criar:** [tools/cookie_manager.py](tools/cookie_manager.py)

```python
class CookieManager:
    def __init__(self, cookie_file=".tmp/cookies.json"):
        self.cookie_file = Path(cookie_file)
        self.max_age = 30 * 60  # 30 minutos

    async def are_valid(self) -> bool:
        """Verifica se cookies ainda são válidos"""
        if not self.cookie_file.exists():
            return False
        age = time.time() - self.cookie_file.stat().st_mtime
        return age < self.max_age

    async def renew_if_needed(self, page):
        """Renova cookies se expirados"""
        if self.are_valid():
            await self.load_cookies(page)
            return

        # Abrir página, aguardar challenge
        await page.goto("https://www.infoimoveis.com.br")
        await page.wait_for_load_state("networkidle")

        # Salvar novos cookies
        cookies = await page.context.cookies()
        self.cookie_file.write_text(json.dumps(cookies, indent=2))
```

**Integração:**
```python
# Em scraper_production.py
cookie_mgr = CookieManager()
await cookie_mgr.renew_if_needed(page)
```

---

### 7. Cloudflare Detector
**Objetivo:** Detectar bloqueios automaticamente

**Criar:** [tools/cloudflare_detector.py](tools/cloudflare_detector.py)

```python
async def is_blocked(page) -> bool:
    """Detecta se foi bloqueado pelo Cloudflare"""
    title = await page.title()
    html = await page.content()

    blocked_signals = [
        "just a moment" in title.lower(),
        "cloudflare" in html[:1000].lower(),
        "cf-wrapper" in html[:1000],
        len(html) < 20000,  # HTML muito pequeno = challenge
    ]

    return any(blocked_signals)
```

**Uso:**
```python
if await is_blocked(page):
    raise CloudflareBlockedError()
```

---

### 8. Crawl4AI como Fallback (SE Stealth < 80%)
**Objetivo:** Implementar segunda camada anti-Cloudflare

**Setup:**
```bash
pip install crawl4ai
crawl4ai-setup
playwright install chromium
```

**Criar:** [tools/scraper_crawl4ai.py](tools/scraper_crawl4ai.py)

**Features:**
- Undetected browser mode (patches profundos)
- Session management (cookies persistentes)
- 95%+ taxa de sucesso esperada

---

### 9. Rotina de Coleta Diária Automatizada
**Objetivo:** Scraping autônomo todos os dias

**Janelas seguras:**
- ✅ 02:00 - 06:00 (madrugada - menos bloqueios)
- ✅ 12:00 - 14:00 (almoço)
- ❌ 08:00 - 11:00, 14:00 - 18:00 (evitar)

**Windows (Task Scheduler):**
```powershell
# Criar tarefa agendada para 03:00
schtasks /create /tn "RAG InfoImoveis" /tr "python e:\rag_infoimoeveis\tools\scrape_workflow.py --daily" /sc daily /st 03:00
```

**Linux/Mac (cron):**
```bash
# Adicionar ao crontab
0 3 * * * cd /e/rag_infoimoeveis && python tools/scrape_workflow.py --daily
```

---

## 🟢 Baixa Prioridade - Próximas Semanas

### 10. Sistema Multi-estratégia
**Objetivo:** Fallback automático entre estratégias

**Criar:** [tools/scraper_engine.py](tools/scraper_engine.py)

```python
class ScraperEngine:
    strategies = [
        PlaywrightStealth,   # Rápido, 80-90% sucesso
        Crawl4AI,            # Médio, 95%+ sucesso
        ManualBypass,        # Lento, 100% sucesso
    ]

    async def scrape_with_fallback(self, url):
        for strategy in self.strategies:
            try:
                return await strategy.scrape(url)
            except CloudflareBlockError:
                logger.warning(f"{strategy} bloqueado, tentando próximo...")
                continue
        raise AllStrategiesFailedError()
```

---

### 11. Sistema de Métricas e Monitoramento
**Features:**
- Dashboard em tempo real
- Alertas de bloqueio (Telegram/Email)
- Logs estruturados
- Gráficos de performance

**Tools:**
- Grafana + Prometheus
- n8n para alertas
- PostgreSQL para métricas históricas

---

### 12. Sistema RAG Completo
**Fase futura (depois de 1000+ imóveis):**
- [ ] Embeddings (OpenAI/Cohere)
- [ ] Vector search (pgvector)
- [ ] Interface de chat
- [ ] Query inteligente

---

## 🐛 Bugs Conhecidos

| ID | Descrição | Prioridade | Arquivo | Status |
|----|-----------|------------|---------|--------|
| BUG-001 | Funções síncronas em async | 🔴 | `human_behavior.py` | ✅ RESOLVIDO |
| BUG-002 | Completude 0% | 🔴 | `scraper_production.py` | ⏳ INVESTIGAR |
| BUG-003 | Discovery timeout 30s | 🟡 | `discovery_filtered.py` | ⏳ INVESTIGAR |
| BUG-004 | URLs de listagem 404 | 🟡 | Discovery workflow | ✅ RESOLVIDO |

---

## ✅ Concluído Recentemente (2026-02-05)

- [x] Pesquisar alternativas anti-Cloudflare (Context7 MCP) ✅
- [x] Implementar playwright-stealth ✅
- [x] Criar `tools/scraper_stealth.py` ✅
- [x] Criar `tools/quick_test_stealth.py` ✅
- [x] Validar stealth funcionando (1 URL) ✅
- [x] Criar sistema de discovery filtrado ✅
- [x] Implementar presets de busca ✅
- [x] Atualizar requirements.txt ✅
- [x] Documentar progresso (PROGRESS_2026-02-05.md) ✅

### Concluído Anteriormente (2026-02-04)

- [x] BUG-001: Funções assíncronas corrigidas ✅
- [x] Mapeamento de seletores HTML ✅
- [x] Atualizar `parse_property_page()` ✅
- [x] Completude 15% → 65% (+333%) ✅

---

## 📊 Metas Semanais

### Semana 1 (2026-02-04 a 2026-02-11)
- [x] Setup e validação inicial (5 imóveis) ✅
- [x] Corrigir async functions ✅
- [x] Pesquisar anti-Cloudflare ✅
- [x] Implementar playwright-stealth ✅
- [ ] Validar stealth (5 URLs batch) ⏳
- [ ] Testar com 50 imóveis ⏳
- [ ] Corrigir completude 0% ⏳

### Semana 2 (2026-02-11 a 2026-02-18)
- [ ] Discovery + Scraping integrados
- [ ] 200 imóveis no banco
- [ ] Completude >70%
- [ ] Cookie manager implementado

### Semana 3 (2026-02-18 a 2026-02-25)
- [ ] 500 imóveis no banco
- [ ] Rotina diária automatizada
- [ ] Monitoramento implementado

### Semana 4 (2026-02-25 a 2026-03-04)
- [ ] 1000+ imóveis no banco
- [ ] Sistema estável e autônomo
- [ ] Preparar para fase RAG

---

## 🎯 Meta Final

**Banco de dados robusto com 10.000+ imóveis de Campo Grande/MS**

- Completude média: >80%
- Taxa de sucesso: >95%
- Atualização diária: 200-400 imóveis novos
- Sistema autônomo e resiliente
- Zero bloqueios Cloudflare

---

## 📚 Recursos Criados

### Documentação
- `PROGRESS_2026-02-05.md` - Relatório detalhado de hoje
- `PROGRESS_2026-02-04.md` - Relatório anterior
- `CONTINUAR_AMANHA.md` - Guia de continuação
- `.tmp/SELECTORS_MAP.md` - Seletores HTML validados
- `.claude/plans/sprightly-munching-cerf.md` - Plano completo anti-Cloudflare

### Scripts de Scraping
- `tools/scraper_stealth.py` - Browser com playwright-stealth
- `tools/quick_test_stealth.py` - Teste batch (5 URLs)
- `tools/discovery_filtered.py` - Discovery com filtros (região, preço, tipo)

### Scripts de Suporte
- `tools/scraper_production.py` - Scraper principal
- `tools/scrape_workflow.py` - Workflow completo
- `tools/metrics_dashboard.py` - Dashboard de métricas
- `tools/inspect_page.py` - Debug de páginas

---

## 🔗 Links Úteis

### Ferramentas Pesquisadas
- **Crawl4AI:** https://github.com/unclecode/crawl4ai (59.5k ⭐)
- **playwright-stealth:** https://github.com/AtuboDad/playwright_stealth (883 ⭐)
- **undetected-chromedriver:** https://github.com/ultrafunkamsterdam/undetected-chromedriver (12.3k ⭐)
- **HasData/cloudflare-bypass:** https://github.com/HasData/cloudflare-bypass (exemplos práticos)

### Documentação
- Crawl4AI Docs: https://docs.crawl4ai.com/advanced/undetected-browser/
- Playwright Docs: https://playwright.dev/python/

---

**Última revisão:** 2026-02-05 05:40
**Próxima revisão:** 2026-02-06 08:00
**Status:** 🟢 Stealth implementado! Testando em batch...
