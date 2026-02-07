# Workflow: Scraping InfoImóveis

## Status: Em Desenvolvimento

### Descobertas Importantes

#### Proteção Anti-Bot
- **Cloudflare** ativo no site
- Requests HTTP simples retornam 403
- Headers de browser também retornam 403
- **Playwright com browser real** funciona (200)

#### Estratégia de Bypass
1. Usar Playwright em modo headed (headless=False)
2. Adicionar script para remover flag `navigator.webdriver`
3. Aguardar 20 segundos para passar pelo Cloudflare
4. Navegar pelo site usando cliques (não URLs diretas)

#### Estrutura de URLs
- **Home**: `https://www.infoimoveis.com.br`
- **Busca detalhada**: `https://www.infoimoveis.com.br/buscadetalhada/`
- **Imóvel**: `/imovel/{finalidade}-{tipo}-{bairro}/{id}`

Exemplos:
- `/imovel/venda-casa-terrea-jardim-europa/372077`
- `/imovel/aluguel-galpao-deposito-vila-gloria/632426`

#### Dados Estruturados Disponíveis

O site fornece dados em múltiplos formatos:

1. **JSON-LD (Schema.org)** - Mais confiável
   - name, description, url, price, image

2. **Tabela HTML** - Dados detalhados
   - Tipo, Cidade/UF, Bairro, Endereço
   - Área construída, Área total
   - Quartos, Banheiros, Vagas

3. **Meta Tags OpenGraph**
   - og:title, og:description, og:image

### Campos Extraídos

| Campo | Fonte | Status |
|-------|-------|--------|
| title | JSON-LD | ✓ |
| description | JSON-LD | ✓ |
| property_type | Tabela HTML | ✓ |
| transaction_type | URL | ✓ |
| price_brl | JSON-LD | ✓ |
| neighborhood | Tabela HTML | ✓ |
| city | Tabela HTML | ✓ |
| state | Tabela HTML | ✓ |
| address | Tabela HTML | ✓ |
| area_built_m2 | Tabela HTML | ✓ |
| area_total_m2 | Tabela HTML | ✓ |
| images | JSON-LD + HTML | ✓ |
| bedrooms | Tabela HTML | Parcial |
| bathrooms | Tabela HTML | Parcial |
| parking_spaces | Tabela HTML | Parcial |

### Rate Limiting Recomendado

| Parâmetro | Valor |
|-----------|-------|
| Delay entre requests | 3-8 segundos (random) |
| Batch size | 5-10 imóveis |
| Máximo por hora | 60 requests |
| Janelas de scraping | Madrugada, almoço, noite |

### Scripts Desenvolvidos

1. `tools/test_01_access.py` - Teste de acesso inicial
2. `tools/test_01c_cloudflare_bypass.py` - Bypass Cloudflare
3. `tools/test_02b_direct_search.py` - Coleta de URLs
4. `tools/test_03_parse.py` - Parsing de dados

### Próximos Passos

1. [ ] Implementar coleta em larga escala com rate limiting
2. [ ] Configurar PostgreSQL + pgvector
3. [ ] Implementar pipeline de embeddings
4. [ ] Criar agente RAG

---

## PDF/OCR vs Scraping Tradicional

### Análise Comparativa

| Aspecto | Scraping HTML | PDF/OCR |
|---------|---------------|---------|
| **Velocidade** | Rápido | Lento |
| **Precisão** | Alta (dados estruturados) | Média (depende do layout) |
| **Custo** | Zero | API calls (Mistral pixtral) |
| **Complexidade** | Média | Alta |
| **Manutenção** | Baixa (JSON-LD estável) | Baixa |

### Recomendação

**Usar Scraping HTML como método primário** pelos seguintes motivos:

1. O site fornece dados estruturados (JSON-LD) muito confiáveis
2. A tabela HTML tem todos os campos necessários
3. Não há necessidade de processar imagens/PDFs
4. Custo zero (não consome API de OCR)

**PDF/OCR como fallback** apenas se:
- O site mudar para renderização 100% client-side
- Os dados estruturados deixarem de existir
- Alguma página específica não tiver os dados em HTML
