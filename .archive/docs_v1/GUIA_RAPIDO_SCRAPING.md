# 🚀 Guia Rápido - Scraping InfoImóveis

## Para Popular o Banco de Dados

---

## ⚡ Setup em 3 Passos

### 1. Verificar PostgreSQL

```bash
docker ps | grep postgres
# Deve mostrar postgres rodando na porta 5433
```

Se não estiver rodando:
```bash
docker-compose up -d postgres
```

### 2. Verificar Cookies (Opcional)

```bash
python tools/cookie_manager.py
```

Se tiver cookies válidos, vai reutilizar. Senão, fará bypass Cloudflare automaticamente.

### 3. Rodar Scraper!

```bash
# Opção mais simples - scraping de 5 imóveis de teste
python tools/scraper_production.py

# Ou workflow completo com discovery
python tools/scrape_workflow.py --mode full --max-properties 50
```

**Pronto!** Os imóveis serão salvos automaticamente no PostgreSQL.

---

## 📊 Ver Resultado

```bash
# Dashboard no terminal
python tools/metrics_dashboard.py
```

Mostra:
- Total de imóveis no banco
- Imóveis nas últimas 24h
- Completude média dos dados
- Top bairros mais caros
- Oportunidades (abaixo do mercado)

---

## 🎯 Escalando para Produção

### Para 50 imóveis (teste)

```bash
python tools/scrape_workflow.py --mode full --max-properties 50
```

Duração: ~20-30 minutos (com delays de segurança)

### Para 200 imóveis (diário)

```bash
python tools/scrape_workflow.py --mode full \
    --max-pages 5 \
    --max-properties 200
```

Duração: ~1-2 horas

### Para 400 imóveis (limite seguro diário)

**Sessão 1 (Madrugada: 03:00 - 06:00)**
```bash
python tools/scrape_workflow.py --mode full \
    --max-pages 10 \
    --max-properties 200
```

**Sessão 2 (Almoço: 13:00 - 15:00)**
```bash
python tools/scrape_workflow.py --mode scrape --max-properties 200
```

**Total:** 400 imóveis/dia (dentro do limite seguro de rate limiting)

---

## 🛡️ Proteções Automáticas

O scraper **automaticamente**:

✅ Aguarda 5-12 segundos entre cada imóvel
✅ Respeita limite de 50 requests/hora e 400/dia
✅ Só opera em janelas seguras (madrugada, almoço, noite)
✅ Reutiliza cookies Cloudflare (válidos por 6h)
✅ Rotaciona fingerprint (User-Agent, viewport)
✅ Simula comportamento humano (scroll, mouse, pausas)
✅ Detecta bloqueios e pausa automaticamente

**Você não precisa fazer nada!** As proteções são transparentes.

---

## 🔧 Comandos Úteis

### Ver estatísticas do banco

```bash
python tools/property_saver.py
```

### Deletar cookies (forçar renovação)

```bash
rm .tmp/cookies.json
```

### Ver relatório do último workflow

```bash
cat .tmp/workflow_report.json | python -m json.tool
```

### Exportar dashboard em JSON

```bash
python tools/metrics_dashboard.py --export
```

---

## 🚨 Se Algo Der Errado

### "BLOQUEIO DETECTADO"

**Solução rápida:**
```bash
rm .tmp/cookies.json  # Deletar cookies
# Aguardar 1 hora
# Tentar novamente
```

### "Fora da janela segura"

**Solução:** Aguardar até próxima janela (automático)

Janelas seguras: 03:00-06:00, 13:00-15:00, 22:00-00:00

### "Limite horário atingido"

**Solução:** Aguardar reset (automático após 1 hora)

### "Database connection failed"

**Solução:**
```bash
docker-compose up -d postgres
docker ps | grep postgres
```

---

## 📈 Progressão Recomendada

**Dia 1:** Teste com 5-10 imóveis
```bash
python tools/scraper_production.py
```

**Dia 2:** Teste com 50 imóveis
```bash
python tools/scrape_workflow.py --mode full --max-properties 50
```

**Dia 3:** Escalar para 100 imóveis
```bash
python tools/scrape_workflow.py --mode full --max-properties 100
```

**Dia 4+:** Rotina diária de 200-400 imóveis
```bash
# Rodar 2x por dia em janelas seguras
python tools/scrape_workflow.py --mode full --max-properties 200
```

---

## 📊 Metas de Banco de Dados

| Imóveis no Banco | Tempo Estimado | Utilidade |
|------------------|----------------|-----------|
| 50 | 1 dia | Validação técnica |
| 500 | 1 semana | Dataset inicial |
| 2.000 | 1 mês | RAG funcional |
| 5.000+ | 2-3 meses | Produção completa |

**Meta atual:** Popular com dados reais para ter um sistema RAG útil.

---

## 🎯 Foco Principal

**O objetivo é criar um banco de dados robusto, não apenas o RAG.**

- ✅ Scraping seguro e confiável
- ✅ Dados completos e estruturados
- ✅ Deduplicação automática
- ✅ Métricas de qualidade
- 🔜 RAG vem depois (com dados reais)

---

## 📞 Arquivos Importantes

| Arquivo | Para que serve |
|---------|---------------|
| `tools/scraper_production.py` | Scraper principal |
| `tools/scrape_workflow.py` | Orquestrador completo |
| `tools/metrics_dashboard.py` | Ver estatísticas |
| `tools/property_saver.py` | Testar inserção no banco |
| `workflows/scraping_producao.md` | Documentação completa |

---

## 💡 Dica Pro

Rode o dashboard **antes e depois** do scraping para ver o progresso:

```bash
# Antes
python tools/metrics_dashboard.py

# Scraping
python tools/scrape_workflow.py --mode full --max-properties 50

# Depois
python tools/metrics_dashboard.py
```

---

**Versão:** 0.8.0
**Status:** ✅ Pronto para Produção
**Foco:** Popular banco de dados com imóveis reais
