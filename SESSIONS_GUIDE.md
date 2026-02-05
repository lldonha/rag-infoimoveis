# 📝 GUIA DE SESSÕES - Scraping Escalável InfoImóveis

## ⚠️ IMPORTANTE
**Este é um guia para IMPLEMENTAÇÃO FUTURA. Nada foi validado ainda!**

Use este documento como roteiro durante cada sessão de trabalho. Marque os checkboxes conforme avança.

---

## 🗂️ Visão Geral das Sessões

| Sessão | Foco | Tempo Estimado | Status |
|--------|------|----------------|--------|
| **1** | Setup Inicial + Presets | ~30 min | ⏳ Pendente |
| **2** | workflow_complete.py | ~3h | ⏳ Pendente |
| **3** | Smoke Test (1 categoria) | ~1h | ⏳ Pendente |
| **4** | Full Day Test (5 categorias) | ~2-4h | ⏳ Pendente |
| **5** | Dashboard + SQL Optimization | ~2h | ⏳ Pendente |
| **6** | Integração n8n | ~1-2h | ⏳ Pendente |
| **7** | Documentação Final | ~1h | ⏳ Pendente |

**Tempo Total Estimado:** 10-14 horas (dividir em múltiplas sessões de trabalho)

---

## 📋 SESSÃO 1: Setup Inicial + category_presets.py

### Objetivos
✅ Criar estrutura de diretórios
✅ Criar tabela execution_logs no PostgreSQL
✅ Validar dependências Python
✅ Implementar category_presets.py

### Pré-requisitos
- [ ] Docker PostgreSQL rodando (port 5433)
- [ ] Python 3.10+ instalado
- [ ] Branch `planejamento` ativa

### Comandos a Executar

```bash
# 1. Criar diretórios
mkdir -p n8n_workflows
mkdir -p logs
mkdir -p .tmp/execution_reports

# 2. Validar dependências
pip list | grep -E "(playwright-stealth|rich|plotly|pandas)"
# Se faltar alguma:
pip install playwright-stealth rich plotly pandas

# 3. Verificar PostgreSQL
psql -h localhost -p 5433 -U postgres -d infoimoveis -c "\dt"
```

### Arquivo 1: sql/execution_logs.sql

```sql
-- Criar este arquivo primeiro
CREATE TABLE IF NOT EXISTS execution_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL UNIQUE,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    duration_seconds INT,
    day_of_week INT,
    categories_processed INT DEFAULT 0,
    properties_collected INT DEFAULT 0,
    properties_new INT DEFAULT 0,
    properties_updated INT DEFAULT 0,
    completeness_avg FLOAT,
    rate_limit_hits INT DEFAULT 0,
    errors_count INT DEFAULT 0,
    errors_json JSONB,
    stats_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_execution_logs_date ON execution_logs(started_at DESC);
CREATE INDEX idx_execution_logs_execution_id ON execution_logs(execution_id);
```

```bash
# Executar SQL
psql -h localhost -p 5433 -U postgres -d infoimoveis < sql/execution_logs.sql

# Validar
psql -h localhost -p 5433 -U postgres -d infoimoveis -c "SELECT * FROM execution_logs"
```

### Arquivo 2: tools/category_presets.py

**Estrutura:**

```python
"""
Presets de categorias para scraping organizado do InfoImóveis.
Define combinações de região × preço × tipo para rotação diária.
"""

from typing import Dict, List, Optional

# ===== PRESETS DE CATEGORIAS =====
PRESETS: Dict[str, Dict] = {
    # --- DIA 1: Casas Segredo/Prosa/Centro ---
    'casas_segredo_100_200k': {
        'property_type': 'casa-terrea',
        'region': 'regiao-segredo',
        'price_min': 100_000,
        'price_max': 200_000,
        'transaction_type': 'venda',
        'description': 'Casas térreas no Segredo entre 100-200k'
    },
    'casas_segredo_200_400k': {
        'property_type': 'casa-terrea',
        'region': 'regiao-segredo',
        'price_min': 200_000,
        'price_max': 400_000,
        'transaction_type': 'venda',
        'description': 'Casas térreas no Segredo entre 200-400k'
    },
    'casas_prosa_100_200k': {
        'property_type': 'casa-terrea',
        'region': 'regiao-prosa',
        'price_min': 100_000,
        'price_max': 200_000,
        'transaction_type': 'venda',
        'description': 'Casas térreas no Prosa entre 100-200k'
    },
    'casas_centro_200_400k': {
        'property_type': 'casa-terrea',
        'region': 'regiao-centro',
        'price_min': 200_000,
        'price_max': 400_000,
        'transaction_type': 'venda',
        'description': 'Casas térreas no Centro entre 200-400k'
    },
    'sobrados_segredo': {
        'property_type': 'sobrado',
        'region': 'regiao-segredo',
        'price_min': 300_000,
        'price_max': 800_000,
        'transaction_type': 'venda',
        'description': 'Sobrados no Segredo entre 300-800k'
    },

    # --- DIA 2: Apartamentos Centro/Bandeirantes ---
    'apts_centro_100_200k': {
        'property_type': 'apartamento',
        'region': 'regiao-centro',
        'price_min': 100_000,
        'price_max': 200_000,
        'transaction_type': 'venda',
        'description': 'Apartamentos no Centro entre 100-200k'
    },
    'apts_bandeirantes_200_400k': {
        'property_type': 'apartamento',
        'region': 'regiao-bandeirantes',
        'price_min': 200_000,
        'price_max': 400_000,
        'transaction_type': 'venda',
        'description': 'Apartamentos em Bandeirantes entre 200-400k'
    },
    'apts_prosa_200_400k': {
        'property_type': 'apartamento',
        'region': 'regiao-prosa',
        'price_min': 200_000,
        'price_max': 400_000,
        'transaction_type': 'venda',
        'description': 'Apartamentos no Prosa entre 200-400k'
    },
    'casas_bandeirantes_100_200k': {
        'property_type': 'casa-terrea',
        'region': 'regiao-bandeirantes',
        'price_min': 100_000,
        'price_max': 200_000,
        'transaction_type': 'venda',
        'description': 'Casas em Bandeirantes entre 100-200k'
    },

    # --- DIA 3: Casas Vila Carlota/Tiradentes + Sobrados ---
    'casas_vila_carlota': {
        'property_type': 'casa-terrea',
        'region': 'regiao-vila-carlota',
        'price_min': 150_000,
        'price_max': 400_000,
        'transaction_type': 'venda',
        'description': 'Casas na Vila Carlota entre 150-400k'
    },
    'casas_tiradentes': {
        'property_type': 'casa-terrea',
        'region': 'regiao-tiradentes',
        'price_min': 150_000,
        'price_max': 400_000,
        'transaction_type': 'venda',
        'description': 'Casas no Tiradentes entre 150-400k'
    },
    'sobrados_prosa': {
        'property_type': 'sobrado',
        'region': 'regiao-prosa',
        'price_min': 400_000,
        'price_max': 1_000_000,
        'transaction_type': 'venda',
        'description': 'Sobrados no Prosa entre 400k-1M'
    },
    'apts_jardim_estados': {
        'property_type': 'apartamento',
        'region': 'regiao-jardim-dos-estados',
        'price_min': 200_000,
        'price_max': 600_000,
        'transaction_type': 'venda',
        'description': 'Apartamentos no Jardim dos Estados entre 200-600k'
    },

    # --- DIA 4: Apartamentos Premium + Sobrados ---
    'apts_prosa_400_800k': {
        'property_type': 'apartamento',
        'region': 'regiao-prosa',
        'price_min': 400_000,
        'price_max': 800_000,
        'transaction_type': 'venda',
        'description': 'Apartamentos premium no Prosa entre 400-800k'
    },
    'apts_centro_400_800k': {
        'property_type': 'apartamento',
        'region': 'regiao-centro',
        'price_min': 400_000,
        'price_max': 800_000,
        'transaction_type': 'venda',
        'description': 'Apartamentos premium no Centro entre 400-800k'
    },
    'sobrados_centro': {
        'property_type': 'sobrado',
        'region': 'regiao-centro',
        'price_min': 300_000,
        'price_max': 800_000,
        'transaction_type': 'venda',
        'description': 'Sobrados no Centro entre 300-800k'
    },
    'casas_segredo_400_800k': {
        'property_type': 'casa-terrea',
        'region': 'regiao-segredo',
        'price_min': 400_000,
        'price_max': 800_000,
        'transaction_type': 'venda',
        'description': 'Casas premium no Segredo entre 400-800k'
    },

    # --- DIA 5: Terrenos + Comercial ---
    'terrenos_all_regions': {
        'property_type': 'terreno',
        'region': None,  # Todas as regiões
        'price_min': 50_000,
        'price_max': 200_000,
        'transaction_type': 'venda',
        'description': 'Terrenos em todas as regiões entre 50-200k'
    },
    'comercial_centro': {
        'property_type': 'comercial',
        'region': 'regiao-centro',
        'price_min': 100_000,
        'price_max': 1_000_000,
        'transaction_type': 'venda',
        'description': 'Imóveis comerciais no Centro'
    },
    'comercial_bandeirantes': {
        'property_type': 'comercial',
        'region': 'regiao-bandeirantes',
        'price_min': 100_000,
        'price_max': 800_000,
        'transaction_type': 'venda',
        'description': 'Imóveis comerciais em Bandeirantes'
    },

    # --- DIA 6: Luxo + Coberturas ---
    'coberturas_all': {
        'property_type': 'cobertura',
        'region': None,
        'price_min': 500_000,
        'price_max': None,  # Sem limite superior
        'transaction_type': 'venda',
        'description': 'Coberturas em todas as regiões acima de 500k'
    },
    'luxury_segredo': {
        'property_type': 'casa-terrea',  # Ou sobrado
        'region': 'regiao-segredo',
        'price_min': 800_000,
        'price_max': None,
        'transaction_type': 'venda',
        'description': 'Imóveis de luxo no Segredo acima de 800k'
    },
    'luxury_prosa': {
        'property_type': 'apartamento',
        'region': 'regiao-prosa',
        'price_min': 800_000,
        'price_max': None,
        'transaction_type': 'venda',
        'description': 'Apartamentos de luxo no Prosa acima de 800k'
    },
    'casas_acima_800k': {
        'property_type': 'casa-terrea',
        'region': None,
        'price_min': 800_000,
        'price_max': None,
        'transaction_type': 'venda',
        'description': 'Casas de alto padrão acima de 800k'
    },
}

# ===== ROTAÇÃO DIÁRIA =====
DAILY_ROTATION: Dict[int, List[str]] = {
    1: ['casas_segredo_100_200k', 'casas_segredo_200_400k', 'casas_prosa_100_200k', 'casas_centro_200_400k', 'sobrados_segredo'],
    2: ['apts_centro_100_200k', 'apts_bandeirantes_200_400k', 'apts_prosa_200_400k', 'casas_bandeirantes_100_200k'],
    3: ['casas_vila_carlota', 'casas_tiradentes', 'sobrados_prosa', 'apts_jardim_estados'],
    4: ['apts_prosa_400_800k', 'apts_centro_400_800k', 'sobrados_centro', 'casas_segredo_400_800k'],
    5: ['terrenos_all_regions', 'comercial_centro', 'comercial_bandeirantes'],
    6: ['coberturas_all', 'luxury_segredo', 'luxury_prosa', 'casas_acima_800k'],
}

# ===== FUNÇÕES AUXILIARES =====

def get_presets_for_day(day: int) -> List[Dict]:
    """
    Retorna lista de presets para o dia especificado (1-6).

    Args:
        day: Dia da semana (1=Domingo, 2=Segunda, ..., 7=Sábado)
              Ajustar para ciclo de 6 dias: usar day % 6 + 1

    Returns:
        Lista de dicts com configurações de preset
    """
    # Normalizar dia para ciclo de 6 dias
    day_normalized = ((day - 1) % 6) + 1

    preset_names = DAILY_ROTATION.get(day_normalized, [])

    return [
        {'name': name, **PRESETS[name]}
        for name in preset_names
        if name in PRESETS
    ]


def get_preset_by_name(name: str) -> Optional[Dict]:
    """Retorna configuração de um preset específico."""
    if name not in PRESETS:
        return None
    return {'name': name, **PRESETS[name]}


def list_all_presets() -> List[str]:
    """Lista nomes de todos os presets disponíveis."""
    return list(PRESETS.keys())


def get_preset_description(name: str) -> str:
    """Retorna descrição de um preset."""
    if name not in PRESETS:
        return "Preset não encontrado"
    return PRESETS[name].get('description', 'Sem descrição')


# ===== VALIDAÇÃO =====
if __name__ == "__main__":
    print("=== PRESETS CONFIGURADOS ===")
    print(f"Total de presets: {len(PRESETS)}")
    print(f"\nRotação diária (6 dias):")
    for day in range(1, 7):
        presets_day = get_presets_for_day(day)
        print(f"  Dia {day}: {len(presets_day)} categorias")
        for preset in presets_day:
            print(f"    - {preset['name']}: {preset['description']}")

    print(f"\n=== TESTE: Dia 1 ===")
    day1_presets = get_presets_for_day(1)
    print(f"Total: {len(day1_presets)} categorias")
    for preset in day1_presets:
        print(f"  {preset['name']}:")
        print(f"    Tipo: {preset['property_type']}")
        print(f"    Região: {preset['region']}")
        print(f"    Preço: R$ {preset['price_min']:,.0f} - R$ {preset['price_max']:,.0f}" if preset['price_max'] else f"    Preço: R$ {preset['price_min']:,.0f}+")
```

### Validação da Sessão 1

```bash
# 1. Testar category_presets.py
cd e:\rag_infoimoeveis
python tools/category_presets.py

# Deve mostrar:
# === PRESETS CONFIGURADOS ===
# Total de presets: 24
# Rotação diária (6 dias): ...

# 2. Testar import
python -c "from tools.category_presets import get_presets_for_day; print(len(get_presets_for_day(1)))"
# Deve retornar: 5

# 3. Validar PostgreSQL
psql -h localhost -p 5433 -U postgres -d infoimoveis -c "SELECT COUNT(*) FROM execution_logs"
# Deve retornar: 0 (tabela vazia)
```

### Checklist de Conclusão

- [ ] Diretórios criados (n8n_workflows, logs, .tmp/execution_reports)
- [ ] Tabela execution_logs criada no PostgreSQL
- [ ] Dependências Python validadas
- [ ] category_presets.py criado e testado
- [ ] `python tools/category_presets.py` executa sem erros
- [ ] Import funciona: `from tools.category_presets import get_presets_for_day`

**✅ SESSÃO 1 COMPLETA** → Prosseguir para Sessão 2

---

## 📋 SESSÃO 2: workflow_complete.py

### Objetivos
✅ Criar orquestrador principal
✅ Integrar discovery + scraping + save
✅ Implementar relatórios JSON
✅ Logging com rich

### Estrutura do Arquivo

**Ver plano completo em:** `C:\Users\Escritorio LLD\.claude\plans\delightful-questing-key.md` (Seção "FASE B")

**Pontos Críticos:**
1. `async def run_category()` - Executa scraping de 1 categoria
2. `async def main()` - Loop por N categorias
3. `generate_report()` - Monta JSON de resultado
4. `save_report()` - Salva em .tmp/execution_reports/
5. `save_to_postgres()` - Insert em execution_logs

### Validação da Sessão 2

```bash
# Teste dry-run (não faz scraping real)
python tools/workflow_complete.py \
  --preset casas_segredo_100_200k \
  --max-per-category 5 \
  --dry-run

# Deve mostrar:
# - Logs formatados (rich)
# - "DRY RUN: Simulando scraping de 5 imóveis"
# - "Relatório salvo em .tmp/execution_reports/..."
```

### Checklist de Conclusão

- [ ] workflow_complete.py criado
- [ ] Imports funcionando (discovery_filtered, scraper_stealth, property_saver)
- [ ] CLI parser implementado (argparse)
- [ ] Dry-run funciona sem erros
- [ ] Logs aparecem no console (rich formatting)

**✅ SESSÃO 2 COMPLETA** → Prosseguir para Sessão 3

---

## 📋 SESSÃO 3: Smoke Test (1 Categoria)

### Objetivos
✅ Validar scraping real de 10 imóveis
✅ Verificar inserção no PostgreSQL
✅ Validar completude >80%
✅ Criar queries de validação

### Comando Principal

```bash
python tools/workflow_complete.py \
  --preset casas_segredo_100_200k \
  --max-per-category 10 \
  --headless
```

### Validações

```sql
-- 1. Contar imóveis inseridos
SELECT COUNT(*) as total
FROM properties
WHERE scraped_at > NOW() - INTERVAL '1 hour';
-- Meta: 8-12 (pode variar)

-- 2. Completude média
SELECT AVG(data_completeness) as avg_completeness
FROM properties
WHERE scraped_at > NOW() - INTERVAL '1 hour';
-- Meta: >0.80

-- 3. Distribuição por bairro
SELECT neighborhood, COUNT(*) as total
FROM properties
WHERE scraped_at > NOW() - INTERVAL '1 hour'
GROUP BY neighborhood;
```

### Checklist de Conclusão

- [ ] Scraping executou sem erros
- [ ] 8-12 imóveis inseridos no PostgreSQL
- [ ] Completude média >80%
- [ ] JSON gerado em .tmp/execution_reports/
- [ ] 0 erros de Cloudflare (verificar logs)

**✅ SESSÃO 3 COMPLETA** → Prosseguir para Sessão 4

---

## 📋 SESSÃO 4-7: [Continuar no próximo documento]

**Nota:** Para manter este guia legível, as sessões 4-7 estão em documentos separados:
- `SESSIONS_GUIDE_PART2.md` - Sessões 4-5
- `SESSIONS_GUIDE_PART3.md` - Sessões 6-7

---

## 🔄 Como Usar Este Guia

### Início de Cada Sessão:
1. Leia os **Objetivos** da sessão
2. Verifique os **Pré-requisitos**
3. Execute os **Comandos** em ordem
4. Marque os **Checkboxes** conforme avança

### Final de Cada Sessão:
1. Complete o **Checklist de Conclusão**
2. Documente problemas encontrados em `MEMORY.md`
3. Comite mudanças: `git add . && git commit -m "feat: Sessão N concluída"`

### Se Algo Falhar:
1. Leia a seção de **Troubleshooting** (se houver)
2. Consulte o plano completo: `C:\Users\Escritorio LLD\.claude\plans\delightful-questing-key.md`
3. Documente o problema e solução em `MEMORY.md`

---

**Última Atualização:** 2026-02-05
**Status Geral:** ⏳ Aguardando implementação
**Próximo Passo:** Executar SESSÃO 1
