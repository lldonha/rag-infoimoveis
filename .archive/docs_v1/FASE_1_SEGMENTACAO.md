# 🎯 FASE 1: Segmentação Inteligente do Scraping

**Status:** 🟡 Em Desenvolvimento
**Prioridade:** ALTA
**Objetivo:** Evitar bloqueios dividindo scraping por regiões e faixas de preço

---

## 📋 Resumo Executivo

O sistema atual scrape em **batch linear contínuo** (4-6 horas), aumentando risco de bloqueio. A solução é **scraping segmentado** por região/preço com delays longos entre segmentos.

### Benefícios:
- ✅ Sessões curtas (20-30 min) ao invés de longas (4-6h)
- ✅ Retry granular (refaz só segmento falho)
- ✅ Monitoramento detalhado por região/faixa
- ✅ Preparado para paralelização futura (múltiplos IPs)

---

## 🎯 Objetivos da Fase 1

### 1. Definir Segmentos de Mercado
Mapear Campo Grande em segmentos lógicos:
- Por região (Segredo, Centro, Prosa, Jardim dos Estados, etc)
- Por faixa de preço (100-200k, 200-400k, 400k+)
- Por tipo de imóvel (casa, apartamento, sobrado)

**Meta:** 10-15 segmentos cobrindo todo o mercado

### 2. Implementar Scraper Segmentado
Novo arquivo `tools/scraper_by_segments.py`:
- Carrega configuração de segmentos
- Scrape segmento por segmento
- Delay longo entre cada um (1h padrão, configurável)
- Retry automático para segmentos falhados

**Meta:** 100% dos segmentos scraped sem bloqueios

### 3. Integrar no Workflow Existente
Modificar `tools/workflow_complete.py`:
- Adicionar modo `--segmented`
- Manter compatibilidade com modo linear
- Relatório detalhado por segmento

**Meta:** Zero breaking changes no código existente

---

## 📦 Arquivos a Criar/Modificar

### CRIAR:

#### 1. `tools/scraper_by_segments.py` (150-200 linhas)
```python
"""
Scraper segmentado por região e faixa de preço.
Evita bloqueios dividindo carga em sessões curtas.
"""

SEGMENTS = {
    # Região Segredo
    "segredo_100_200k": {
        "region": "regiao-segredo",
        "property_type": "casa-terrea",
        "price_min": 100000,
        "price_max": 200000,
        "expected": 50
    },
    "segredo_200_400k": {...},

    # Região Centro
    "centro_apto_150_300k": {...},

    # Adicionar mais 8-12 segmentos
}

async def scrape_segment(segment_config: Dict) -> List[PropertyData]:
    """Scrape um único segmento"""
    pass

async def scrape_all_segments(
    segments: Dict,
    delay_between_segments: int = 3600
) -> Dict:
    """Scrape todos os segmentos com delays"""
    pass
```

**Funcionalidades:**
- [ ] Definir 10-15 segmentos do mercado CG
- [ ] Scrape segmento individual
- [ ] Scrape batch com delays
- [ ] Retry automático para falhas
- [ ] Relatório JSON por segmento
- [ ] CLI com argparse

#### 2. `tools/segment_analyzer.py` (80 linhas)
```python
"""
Analisa performance de cada segmento.
Ajuda a otimizar estratégia de scraping.
"""

def analyze_segment_performance(segment_results: List[Dict]):
    """
    Retorna:
    - Taxa de sucesso por segmento
    - Tempo médio por segmento
    - Segmentos problemáticos
    - Recomendações de ajuste
    """
    pass
```

### MODIFICAR:

#### 3. `tools/workflow_complete.py`
```python
# Adicionar modo segmentado
parser.add_argument('--segmented', action='store_true',
                   help='Use segmented scraping (safer)')
parser.add_argument('--segments', type=str,
                   help='Comma-separated segment names')
parser.add_argument('--segment-delay', type=int, default=3600,
                   help='Delay between segments in seconds')

if args.segmented:
    # Usar scraper_by_segments.py
else:
    # Modo linear atual (mantido)
```

---

## 📊 Definição de Segmentos

### Proposta Inicial (10 segmentos)

| ID | Região | Tipo | Preço Min | Preço Max | Estimado |
|----|--------|------|-----------|-----------|----------|
| `segredo_100_200k` | Segredo | Casa | 100k | 200k | 50 |
| `segredo_200_400k` | Segredo | Casa | 200k | 400k | 30 |
| `centro_apto_150_300k` | Centro | Apartamento | 150k | 300k | 80 |
| `centro_apto_300_500k` | Centro | Apartamento | 300k | 500k | 40 |
| `prosa_casa_200_400k` | Prosa | Casa | 200k | 400k | 120 |
| `prosa_sobrado_400_700k` | Prosa | Sobrado | 400k | 700k | 60 |
| `jardim_estados_300_500k` | Jardim Estados | Casa | 300k | 500k | 90 |
| `jardim_estados_500k_plus` | Jardim Estados | Casa | 500k | 1M | 50 |
| `vila_nasser_100_250k` | Vila Nasser | Casa/Apto | 100k | 250k | 70 |
| `outros_ate_200k` | Outras | Qualquer | 0 | 200k | 100 |

**Total estimado:** ~690 imóveis

### Como Expandir:
1. Rodar scraping de discovery em cada região
2. Contar imóveis encontrados
3. Ajustar segmentos baseado em volume real
4. Adicionar mais segmentos se necessário

---

## 🧪 Plano de Testes

### Teste 1: Segmento Individual (10 min)
```bash
python tools/scraper_by_segments.py --segment segredo_100_200k --limit 10
```
**Validar:**
- [ ] Scrape completo de 10 imóveis
- [ ] Dados salvos no PostgreSQL
- [ ] Zero bloqueios
- [ ] Tempo < 15 minutos

### Teste 2: Dois Segmentos com Delay (1h 30min)
```bash
python tools/scraper_by_segments.py \
    --segments "segredo_100_200k,centro_apto_150_300k" \
    --limit 20 \
    --segment-delay 3600
```
**Validar:**
- [ ] Primeiro segmento: 20 imóveis
- [ ] Delay de 1h respeitado
- [ ] Segundo segmento: 20 imóveis
- [ ] Relatório JSON gerado

### Teste 3: Batch Completo (1 dia)
```bash
python tools/scraper_by_segments.py --all --save-to-db
```
**Validar:**
- [ ] 10 segmentos processados
- [ ] ~690 imóveis coletados
- [ ] Taxa de sucesso > 90%
- [ ] Zero bloqueios

---

## 📈 Métricas de Sucesso

| Métrica | Meta | Como Validar |
|---------|------|--------------|
| **Segmentos definidos** | 10-15 | Contar em `SEGMENTS` dict |
| **Taxa de sucesso** | >90% | Scrape sem erros/bloqueios |
| **Tempo por segmento** | <30min | Logs de timing |
| **Bloqueios** | 0 | Verificar logs |
| **Imóveis por dia** | 500-1000 | Contar no PostgreSQL |

---

## ⚙️ Configuração Recomendada

### Delays e Limites

```python
# Configuração conservadora (segura)
CONSERVATIVE = {
    "delay_between_segments": 3600,  # 1 hora
    "properties_per_segment": 50,
    "delay_between_properties": 10,  # 10s
}

# Configuração balanceada (recomendada)
BALANCED = {
    "delay_between_segments": 1800,  # 30 min
    "properties_per_segment": 100,
    "delay_between_properties": 8,   # 8s
}

# Configuração agressiva (risco moderado)
AGGRESSIVE = {
    "delay_between_segments": 900,   # 15 min
    "properties_per_segment": 150,
    "delay_between_properties": 5,   # 5s
}
```

**Recomendação inicial:** CONSERVATIVE até validar zero bloqueios, depois migrar para BALANCED.

---

## 🔄 Workflow de Execução

```
┌────────────────────────────────────────────┐
│  Scraping Segmentado - Workflow Completo  │
└────────────────────────────────────────────┘

1. PREPARAÇÃO
   ├─→ Verificar PostgreSQL rodando
   ├─→ Carregar configuração de segmentos
   └─→ Definir modo (conservador/balanceado)

2. EXECUÇÃO
   ├─→ Para cada segmento:
   │   ├─→ Log: "Iniciando {segment_name}"
   │   ├─→ Scrape N imóveis do segmento
   │   ├─→ Salvar no PostgreSQL
   │   ├─→ Gerar relatório do segmento
   │   └─→ DELAY longo (30min-1h)
   └─→ Próximo segmento

3. RELATÓRIO FINAL
   ├─→ Total de imóveis: X
   ├─→ Taxa de sucesso por segmento
   ├─→ Segmentos problemáticos
   └─→ Tempo total de execução

4. ANÁLISE
   └─→ Identificar segmentos para otimizar
```

---

## 📝 Checklist de Implementação

### Semana 1 - Setup Inicial
- [ ] Criar `tools/scraper_by_segments.py`
- [ ] Definir 10 segmentos iniciais
- [ ] Implementar `scrape_segment()`
- [ ] Implementar `scrape_all_segments()`
- [ ] Adicionar CLI com argparse
- [ ] Teste: 1 segmento, 10 imóveis

### Semana 2 - Integração
- [ ] Criar `tools/segment_analyzer.py`
- [ ] Modificar `tools/workflow_complete.py`
- [ ] Adicionar flag `--segmented`
- [ ] Teste: 2 segmentos com delay
- [ ] Validar relatórios JSON

### Semana 3 - Produção
- [ ] Teste completo: 10 segmentos
- [ ] Ajustar delays baseado em resultados
- [ ] Documentar segmentos no README
- [ ] Preparar para Fase 2 (Parser)

---

## 🚨 Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| **Bloqueio mesmo com segmentos** | Baixa | Alto | Aumentar delays, usar CONSERVATIVE |
| **Segmento sem imóveis** | Média | Baixo | Validar com discovery antes |
| **Falha em segmento específico** | Média | Médio | Retry automático 3x |
| **Delay muito longo (>24h total)** | Baixa | Médio | Paralelizar segmentos (futuro) |

---

## 📚 Documentação Relacionada

- [PLANO_RAG_INFOIMOVEIS.md](PLANO_RAG_INFOIMOVEIS.md) - Plano completo do projeto
- [RESUMO_EXECUTIVO_v0.8.md](RESUMO_EXECUTIVO_v0.8.md) - Sistema atual funcionando
- [RELATORIO_FINAL_2026-02-05.md](RELATORIO_FINAL_2026-02-05.md) - Testes de validação

---

## 🎯 Próximos Passos (Pós-Fase 1)

Após concluir Fase 1:
1. ✅ Scraping segmentado funcionando sem bloqueios
2. ➡️ **FASE 2:** Melhorar parser (85%+ completude)
3. ➡️ **FASE 3:** Download e análise de imagens

---

**Última atualização:** 2026-02-05
**Responsável:** Sistema WAT Framework
**Status:** 🟡 Em Desenvolvimento
