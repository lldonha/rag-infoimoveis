# 🚀 COMECE AQUI - Scraping InfoImóveis

## Sistema Pronto para Popular o Banco de Dados

---

## ✅ Verificação Rápida

```bash
# 1. PostgreSQL rodando?
docker ps | grep postgres

# 2. Sistema operacional?
python tools/test_08_scraping_system.py
```

Se ambos OK → Pule para **USAR AGORA** 👇

---

## 🎯 USAR AGORA (2 Comandos)

### Opção A: Teste Rápido (5 imóveis)

```bash
python tools/scraper_production.py
```

**Resultado:**
- 5 imóveis coletados
- Salvos automaticamente no PostgreSQL
- Duração: ~5 minutos

### Opção B: Produção (50 imóveis)

```bash
python tools/scrape_workflow.py --mode full --max-properties 50
```

**Resultado:**
- Discovery de URLs
- Scraping de 50 imóveis
- Salvos no banco
- Duração: ~20-30 minutos

### Ver Resultado

```bash
python tools/metrics_dashboard.py
```

**Mostra:**
- Total no banco
- Completude média
- Top bairros
- Oportunidades

---

## 🛡️ Proteções Automáticas

**Você não precisa fazer nada!**

O sistema automaticamente:
- ✅ Aguarda 5-12s entre imóveis
- ✅ Limita 50/hora, 400/dia
- ✅ Opera em janelas seguras (madrugada, almoço, noite)
- ✅ Reutiliza cookies (6h)
- ✅ Rotaciona fingerprint
- ✅ Simula comportamento humano
- ✅ Detecta e recupera de bloqueios

---

## 📈 Escalando

### Para 100 imóveis

```bash
python tools/scrape_workflow.py --mode full --max-properties 100
```

### Para 400 imóveis/dia (máximo seguro)

**Sessão 1 (Madrugada: 03-06h)**
```bash
python tools/scrape_workflow.py --mode full --max-properties 200
```

**Sessão 2 (Almoço: 13-15h)**
```bash
python tools/scrape_workflow.py --mode scrape --max-properties 200
```

---

## 🚨 Se Algo Der Errado

### "BLOQUEIO DETECTADO"
```bash
rm .tmp/cookies.json  # Deletar cookies
# Aguardar 1 hora
# Tentar novamente
```

### "Fora da janela segura"
- Aguardar próxima janela (automático)
- Janelas: 03-06h, 13-15h, 22-24h

### "Limite horário atingido"
- Aguardar reset (automático após 1h)

### "Database connection failed"
```bash
docker-compose up -d postgres
```

---

## 📚 Documentação

| Para | Leia |
|------|------|
| Quick start | `GUIA_RAPIDO_SCRAPING.md` |
| Configuração completa | `workflows/scraping_producao.md` |
| Troubleshooting | `README.md` |
| Resumo executivo | `RESUMO_EXECUTIVO_v0.8.md` |

---

## 🎯 Meta

**Popular banco com 1000+ imóveis reais**

Progressão recomendada:
1. Dia 1: 5-10 imóveis (teste) ✅
2. Dia 2: 50 imóveis (validação)
3. Dia 3: 100 imóveis (escala)
4. Dia 4+: 200-400 imóveis/dia (rotina)

**Total em 1 mês:** ~10.000 imóveis

---

## ⚡ TL;DR

```bash
# 1. Verificar
python tools/test_08_scraping_system.py

# 2. Scraping
python tools/scraper_production.py

# 3. Dashboard
python tools/metrics_dashboard.py
```

**Pronto!** Sistema operacional. 🎉

---

**Desenvolvido com WAT Framework**
Versão: 0.8.0
