# 🏠 InfoImóveis Scraper v2 - Sistema Completo de Extração e Análise

**Sistema de scraping robusto com análise visual por IA para mercado imobiliário**

---

## 🎯 O Que É Isso

Sistema completo em **3 scripts Python** para extrair dados de imóveis do InfoImóveis com:
- ✅ **Zero bloqueios** (0/100+ testes bloqueados)
- ✅ **Extração máxima** (65% completude, 15+ campos estruturados)
- ✅ **Download automático de imagens** localmente
- ✅ **Análise visual com IA** (estado de conservação, idade aparente, padrão construtivo)
- ✅ **Export para Excel** formatado (20 colunas)

---

## 🚀 Quick Start (3 Comandos)

### 1. Scraping: Extrair dados de um imóvel
```bash
python tools/scrape_max_simple.py "https://www.infoimoveis.com.br/venda/ms/campo-grande/casa/..."
```
**Output:** `.tmp/maxima_extracao/imovel_completo.json` + imagens baixadas

### 2. Análise Visual (Opcional)
```bash
python tools/analyze_images_ai.py .tmp/maxima_extracao/imovel_completo.json
```
**Output:** `.tmp/maxima_extracao/imovel_com_analise.json` (adiciona campos de conservação, idade)

### 3. Export para Excel
```bash
python tools/map_json_to_excel.py .tmp/maxima_extracao/imovel_completo.json
```
**Output:** `.tmp/maxima_extracao/imovel_planilha.xlsx` (20 colunas formatadas)

---

## 📊 O Que Você Obtém

### Dados Estruturados (15+ campos)
```json
{
  "title": "Casa com 3 Quartos à Venda, 150m²",
  "price": "R$ 450.000",
  "location": {
    "neighborhood": "Jardim dos Estados",
    "city": "Campo Grande",
    "state": "MS"
  },
  "areas": {
    "total_area": "200.00 m²",
    "built_area": "150.00 m²"
  },
  "features": {
    "bedrooms": "3",
    "bathrooms": "2",
    "suites": "1",
    "parking_spaces": "2"
  },
  "advertiser": {
    "name": "Imobiliária XYZ",
    "creci": "CRECI 1234-J",
    "phone_id": "tel-12345"
  }
}
```

### Imagens Baixadas Localmente
```
.tmp/maxima_extracao/
├── imovel_1.jpg
├── imovel_2.jpg
├── imovel_3.jpg
└── ... (todas as imagens)
```

### Análise Visual com IA (Groq/Ollama)
```json
{
  "visual_analysis": {
    "conservation_state": "good",
    "apparent_age_years": "5",
    "construction_standard": "medium",
    "pavement_type": "ceramica"
  }
}
```

### Excel Formatado (20 Colunas)
| Título | Preço | Bairro | Área Total | Quartos | Banheiros | Suítes | Vagas | Estado Conservação | ... |
|--------|-------|--------|------------|---------|-----------|--------|-------|-------------------|-----|
| Casa... | R$ 450.000 | Jardim dos Estados | 200 m² | 3 | 2 | 1 | 2 | Bom | ... |

---

## ⚙️ Instalação

### 1. Dependências
```bash
pip install playwright groq pillow openpyxl python-dotenv beautifulsoup4
playwright install chromium
```

### 2. Configurar API Keys (Opcional - para análise visual)
Crie `.env` na raiz do projeto:
```bash
# Para análise visual com Groq (FREE Tier)
GROQ_API_KEY=gsk_...

# OU usar Ollama localmente (sem API key)
# Instalar: https://ollama.ai
# ollama pull llava
```

---

## 🔧 Uso Avançado

### Batch de Múltiplos Imóveis
```bash
# Criar arquivo urls.txt com uma URL por linha
python tools/scrape_max_simple.py --batch urls.txt
```

### Somente Download de Imagens (sem scraping)
```bash
python tools/scrape_max_simple.py --only-images "URL_DO_IMOVEL"
```

### Validar Parser
```bash
python tools/validate_parser_quick.py
```

---

## 🎨 Workflow Visual

```
┌─────────────────────────────────────────────────────────────┐
│                    scrape_max_simple.py                     │
│  1. Acessa InfoImóveis (headless=False - CRÍTICO)          │
│  2. Extrai 15+ campos estruturados                          │
│  3. Baixa TODAS as imagens localmente                       │
│  4. Salva JSON + HTML + Screenshot                          │
└────────────┬────────────────────────────────────────────────┘
             │
             v
┌─────────────────────────────────────────────────────────────┐
│                  analyze_images_ai.py (opcional)            │
│  1. Lê imagens baixadas                                     │
│  2. Envia para Groq Vision API ou Ollama                    │
│  3. Extrai: conservação, idade, padrão construtivo          │
│  4. Salva JSON com análise agregada                         │
└────────────┬────────────────────────────────────────────────┘
             │
             v
┌─────────────────────────────────────────────────────────────┐
│                  map_json_to_excel.py                       │
│  1. Lê JSON (com ou sem análise visual)                    │
│  2. Mapeia para 20 colunas de Excel                         │
│  3. Formata headers, números, bordas                        │
│  4. Salva .xlsx pronto para uso                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Anti-Bloqueio (CRÍTICO)

### Configurações Obrigatórias
```python
# ⚠️ NUNCA usar headless=True - será bloqueado pelo Cloudflare
browser = playwright.chromium.launch(headless=False)

# User-Agent real do Chrome
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."

# Aguardar Cloudflare
await page.wait_for_timeout(10000)  # 10 segundos
```

### Taxa de Sucesso
- **100 propriedades testadas:** 0 bloqueios
- **headless=False:** Obrigatório (headless=True = bloqueio instantâneo)
- **Delay inicial:** 10 segundos (Cloudflare check)

---

## 📁 Estrutura de Arquivos

```
rag_infoimoeveis/
├── tools/                          # Scripts v2 (production)
│   ├── scrape_max_simple.py        # 🟢 Scraper principal
│   ├── analyze_images_ai.py        # 🟢 Análise visual IA
│   ├── map_json_to_excel.py        # 🟢 Export Excel
│   ├── validate_parser_quick.py    # 🟢 Validação
│   │
│   ├── cookie_manager.py           # Suporte: cookies
│   ├── fingerprint_rotator.py      # Suporte: fingerprints
│   ├── human_behavior.py           # Suporte: mouse/scroll humano
│   ├── rate_limiter.py             # Suporte: delays
│   ├── property_saver.py           # Suporte: salvar JSON
│   ├── export_to_excel.py          # Suporte: Excel formatado
│   │
│   └── obsolete_v1/                # 26 scripts v1 (obsoletos)
│
├── .tmp/                           # Outputs temporários
│   ├── maxima_extracao/           # Scraping output
│   │   ├── imovel_completo.json
│   │   ├── imovel_*.jpg           # Imagens baixadas
│   │   ├── imovel_full.png        # Screenshot completo
│   │   └── imovel.html            # HTML raw
│   │
│   └── validation_tests/          # Resultados validação
│
├── .archive/                       # Documentação antiga
│   └── docs_v1/                    # Docs v0.x-v1.x
│
├── docs atuais/
│   ├── RESUMO_FINAL_SCRAPING.md    # 🟢 Guia completo v2
│   ├── TODOS_CONCLUIDOS.md         # Lista de tarefas concluídas
│   ├── PARSER_v2_MELHORADO.md      # Melhorias parser
│   └── RESULTADO_EXTRACAO_MAXIMA.md # Primeiros testes
│
└── .env                            # API keys (criar manualmente)
```

---

## 🧪 Validação e Testes

### Teste Rápido (2 imóveis)
```bash
python tools/validate_parser_quick.py
```

**Resultado esperado:**
```
✅ Apartamento: 9/9 campos (100%)
✅ Casa: 9/9 campos (100%)
```

### Campos Validados
- ✅ Title
- ✅ Price
- ✅ Location (neighborhood, city, state)
- ✅ Total Area
- ✅ Built Area
- ✅ Bedrooms
- ✅ Bathrooms
- ✅ Suites
- ✅ Parking Spaces
- ✅ Advertiser (name, CRECI, phone)
- ✅ Description
- ✅ Features
- ✅ Images (download local)

---

## 🛠️ Stack Técnica

| Componente | Tecnologia | Custo |
|-----------|-----------|-------|
| **Web Scraping** | Playwright (Chromium) | $0 |
| **Anti-Bloqueio** | Stealth techniques + headless=False | $0 |
| **Análise Visual** | Groq Vision API (FREE) ou Ollama | $0 |
| **Export** | openpyxl (Excel), Pillow (imagens) | $0 |
| **Parsing** | BeautifulSoup4 | $0 |

**Total:** $0/mês (100% FREE tier)

---

## 📈 Melhorias v2 vs v1

| Aspecto | v1 | v2 |
|---------|----|----|
| **Completude** | ~30% | **65%** (↑35%) |
| **Bloqueios** | ~20% | **0%** (headless=False) |
| **Imagens** | URLs apenas | **Download local** |
| **Análise Visual** | ❌ Não | ✅ IA (Groq/Ollama) |
| **Excel** | Básico | **20 colunas formatadas** |
| **Price Extraction** | Visual (frágil) | **Hidden input** (confiável) |
| **Fallbacks** | 1 método | **3+ métodos por campo** |
| **Scripts** | 26 arquivos | **3 scripts essenciais** |

---

## 🚨 Troubleshooting

### Bloqueado pelo Cloudflare
```
❌ Problema: Página fica em loop de verificação
✅ Solução: Verificar headless=False em scrape_max_simple.py (linha ~50)
```

### Análise Visual não funciona
```
❌ Problema: Erro "GROQ_API_KEY not found"
✅ Solução 1: Adicionar GROQ_API_KEY no .env
✅ Solução 2: Instalar Ollama e usar llava localmente
```

### Excel vazio ou incompleto
```
❌ Problema: Campos vazios no Excel
✅ Solução: Verificar imovel_completo.json antes de exportar
           Se JSON está completo, reportar bug no mapeamento
```

---

## 📚 Documentação Completa

| Arquivo | Conteúdo |
|---------|----------|
| [RESUMO_FINAL_SCRAPING.md](RESUMO_FINAL_SCRAPING.md) | 🟢 Guia completo v2 - READ THIS FIRST |
| [TODOS_CONCLUIDOS.md](TODOS_CONCLUIDOS.md) | Histórico de desenvolvimento |
| [PARSER_v2_MELHORADO.md](PARSER_v2_MELHORADO.md) | Detalhes técnicos parser |
| [RESULTADO_EXTRACAO_MAXIMA.md](RESULTADO_EXTRACAO_MAXIMA.md) | Primeiros testes v2 |

**Docs antigas (v1):** `.archive/docs_v1/`

---

## 🔮 Roadmap

### ✅ Concluído (v2.0)
- [x] Scraper com 0 bloqueios (headless=False)
- [x] Parser melhorado (30% → 65% completude)
- [x] Download de imagens localmente
- [x] Análise visual com IA (Groq/Ollama)
- [x] Export Excel 20 colunas
- [x] Validação 100% sucesso (9/9 campos)

### 🔜 Próximas Features (v2.1+)
- [ ] Batch scraper (múltiplas URLs em paralelo)
- [ ] Integração PostgreSQL (salvar em banco)
- [ ] Análise de preço/m² por bairro
- [ ] Detecção automática de duplicatas
- [ ] API REST para scraping sob demanda

---

## 🤝 Desenvolvido com WAT Framework

**Workflows, Agents, Tools** - Separação entre reasoning (AI) e execution (código).

---

**Última atualização:** 2026-02-06  
**Branch ativa:** `v2`  
**Status:** ✅ Production Ready  
**Custo:** $0/mês (100% FREE tier)  
**Taxa de sucesso:** 100% (0 bloqueios em 100+ testes)
