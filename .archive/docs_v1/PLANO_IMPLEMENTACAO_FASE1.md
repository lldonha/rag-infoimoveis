# 📋 Plano de Implementação - Fase 1: Scraping Segmentado

**Branch:** `feat/fase1-segmentacao`
**Data Início:** 2026-02-05
**Duração Estimada:** 3-5 dias
**Status:** 🟡 Pronto para Implementação

---

## 🎯 Objetivo

Implementar sistema de scraping segmentado por região/preço para evitar bloqueios e permitir scraping em larga escala (500-1000 imóveis/dia).

---

## 📊 Situação Atual

### ✅ O Que Já Temos
- Scraper funcional 100% (34 imóveis, 0 bloqueios)
- Playwright Stealth configurado
- PostgreSQL + schema completo
- Rate limiting implementado
- 7 camadas de proteção anti-bloqueio

### ⚠️ Problema Identificado
- Scraping linear contínuo (4-6h sessão)
- Risco de bloqueio aumenta com tempo
- Sem divisão por região/preço
- Dificulta retry granular

---

## 📝 Tarefas de Implementação

### ETAPA 1: Definir Segmentos de Mercado (1-2h)

**Arquivo:** `tools/market_segments.py`

```python
"""
Definição de segmentos de mercado de Campo Grande/MS.
Cada segmento representa uma combinação de: região + tipo + faixa de preço.
"""

MARKET_SEGMENTS = {
    # ============================================
    # REGIÃO SEGREDO (Popular)
    # ============================================
    "segredo_casa_100_200k": {
        "name": "Segredo - Casas 100-200k",
        "region": "regiao-segredo",
        "property_type": "casa-terrea",
        "price_min": 100000,
        "price_max": 200000,
        "expected_count": 50,
        "priority": "high"
    },
    "segredo_casa_200_400k": {
        "name": "Segredo - Casas 200-400k",
        "region": "regiao-segredo",
        "property_type": "casa-terrea",
        "price_min": 200000,
        "price_max": 400000,
        "expected_count": 30,
        "priority": "medium"
    },

    # ============================================
    # REGIÃO CENTRO (Apartamentos)
    # ============================================
    "centro_apto_150_300k": {
        "name": "Centro - Apartamentos 150-300k",
        "region": "regiao-centro",
        "property_type": "apartamento",
        "price_min": 150000,
        "price_max": 300000,
        "expected_count": 80,
        "priority": "high"
    },
    "centro_apto_300_500k": {
        "name": "Centro - Apartamentos 300-500k",
        "region": "regiao-centro",
        "property_type": "apartamento",
        "price_min": 300000,
        "price_max": 500000,
        "expected_count": 40,
        "priority": "medium"
    },

    # ============================================
    # REGIÃO PROSA (Classe Média Alta)
    # ============================================
    "prosa_casa_200_400k": {
        "name": "Prosa - Casas 200-400k",
        "region": "regiao-prosa",
        "property_type": "casa-terrea",
        "price_min": 200000,
        "price_max": 400000,
        "expected_count": 120,
        "priority": "high"
    },
    "prosa_sobrado_400_700k": {
        "name": "Prosa - Sobrados 400-700k",
        "region": "regiao-prosa",
        "property_type": "sobrado",
        "price_min": 400000,
        "price_max": 700000,
        "expected_count": 60,
        "priority": "medium"
    },

    # ============================================
    # JARDIM DOS ESTADOS (Premium)
    # ============================================
    "jardim_estados_300_500k": {
        "name": "Jardim Estados - Casas 300-500k",
        "region": "regiao-jardim-estados",
        "property_type": "casa-terrea",
        "price_min": 300000,
        "price_max": 500000,
        "expected_count": 90,
        "priority": "medium"
    },
    "jardim_estados_500k_plus": {
        "name": "Jardim Estados - Casas 500k+",
        "region": "regiao-jardim-estados",
        "property_type": "casa-terrea",
        "price_min": 500000,
        "price_max": 1000000,
        "expected_count": 50,
        "priority": "low"
    },

    # ============================================
    # VILA NASSER (Diversificado)
    # ============================================
    "vila_nasser_100_250k": {
        "name": "Vila Nasser - Misto 100-250k",
        "region": "regiao-vila-nasser",
        "property_type": None,  # Qualquer tipo
        "price_min": 100000,
        "price_max": 250000,
        "expected_count": 70,
        "priority": "medium"
    },

    # ============================================
    # OUTROS (Catch-all)
    # ============================================
    "outros_ate_200k": {
        "name": "Outras Regiões - Até 200k",
        "region": None,  # Qualquer região não coberta
        "property_type": None,
        "price_min": 0,
        "price_max": 200000,
        "expected_count": 100,
        "priority": "low"
    },
}

# Total estimado: ~690 imóveis
```

**Checklist:**
- [ ] Criar arquivo `tools/market_segments.py`
- [ ] Definir 10 segmentos iniciais
- [ ] Adicionar campo `priority` (high/medium/low)
- [ ] Adicionar campo `expected_count`
- [ ] Documentar cada segmento

---

### ETAPA 2: Implementar Scraper Segmentado (3-4h)

**Arquivo:** `tools/scraper_by_segments.py`

**Funcionalidades principais:**

```python
#!/usr/bin/env python3
"""
Scraper segmentado por região e faixa de preço.
Evita bloqueios dividindo carga em sessões curtas.
"""

import asyncio
import argparse
from datetime import datetime
from typing import Dict, List, Optional

# Importar módulos existentes
from scraper_production import scrape_property_page
from property_saver import insert_property, get_property_stats
from market_segments import MARKET_SEGMENTS

# Importar proteções
from rate_limiter import SmartRateLimiter
from cookie_manager import load_cookies, save_cookies
from fingerprint_rotator import get_random_fingerprint


class SegmentedScraper:
    """Scraper que processa segmentos de mercado separadamente"""

    def __init__(self, delay_between_segments: int = 3600):
        self.delay = delay_between_segments
        self.results = []
        self.rate_limiter = SmartRateLimiter()

    async def scrape_segment(
        self,
        segment_id: str,
        segment_config: Dict,
        limit: Optional[int] = None,
        save_to_db: bool = True
    ) -> Dict:
        """
        Scrape um único segmento de mercado.

        Args:
            segment_id: ID do segmento (ex: "segredo_casa_100_200k")
            segment_config: Configuração do segmento
            limit: Limite de imóveis (None = todos)
            save_to_db: Salvar no PostgreSQL?

        Returns:
            Dict com estatísticas do scraping
        """
        print(f"\n{'='*60}")
        print(f"🎯 SEGMENTO: {segment_config['name']}")
        print(f"📍 Região: {segment_config['region']}")
        print(f"🏠 Tipo: {segment_config['property_type']}")
        print(f"💰 Preço: R$ {segment_config['price_min']:,} - R$ {segment_config['price_max']:,}")
        print(f"📊 Esperado: ~{segment_config['expected_count']} imóveis")
        print(f"{'='*60}\n")

        start_time = datetime.now()

        # 1. Discovery de URLs
        urls = await self.discover_urls(segment_config, limit)
        print(f"✅ Discovery: {len(urls)} URLs encontradas\n")

        if not urls:
            return {
                "segment_id": segment_id,
                "status": "no_urls",
                "urls_found": 0,
                "scraped": 0,
                "errors": 0
            }

        # 2. Scrape de cada URL
        scraped = []
        errors = []

        for idx, url in enumerate(urls, 1):
            try:
                print(f"[{idx}/{len(urls)}] Scraping: {url}")

                # Rate limiting
                await self.rate_limiter.wait_if_needed()

                # Scrape
                property_data = await scrape_property_page(url)

                if property_data:
                    scraped.append(property_data)

                    # Salvar no banco?
                    if save_to_db:
                        insert_property(property_data)
                        print(f"  ✅ Salvo no banco")
                else:
                    errors.append(url)
                    print(f"  ❌ Falha ao extrair dados")

            except Exception as e:
                errors.append(url)
                print(f"  ❌ Erro: {e}")

        # 3. Estatísticas
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        result = {
            "segment_id": segment_id,
            "segment_name": segment_config["name"],
            "status": "success" if scraped else "failed",
            "urls_found": len(urls),
            "scraped": len(scraped),
            "errors": len(errors),
            "success_rate": len(scraped) / len(urls) if urls else 0,
            "duration_seconds": duration,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }

        print(f"\n📊 RESULTADO DO SEGMENTO:")
        print(f"  ✅ Sucesso: {len(scraped)}/{len(urls)} ({result['success_rate']:.1%})")
        print(f"  ⏱️  Duração: {duration/60:.1f} minutos")

        return result

    async def discover_urls(
        self,
        segment_config: Dict,
        limit: Optional[int] = None
    ) -> List[str]:
        """
        Descobre URLs de imóveis no segmento.
        Usa lógica de discovery existente com filtros.
        """
        # TODO: Implementar discovery com filtros do segmento
        # Por enquanto, usa função existente
        pass

    async def scrape_all_segments(
        self,
        segment_ids: Optional[List[str]] = None,
        save_to_db: bool = True
    ) -> Dict:
        """
        Scrape todos os segmentos (ou lista específica).

        Args:
            segment_ids: IDs específicos ou None (todos)
            save_to_db: Salvar no PostgreSQL?

        Returns:
            Relatório completo com estatísticas
        """
        # Filtrar segmentos
        if segment_ids:
            segments = {k: v for k, v in MARKET_SEGMENTS.items() if k in segment_ids}
        else:
            segments = MARKET_SEGMENTS

        # Ordenar por prioridade
        sorted_segments = sorted(
            segments.items(),
            key=lambda x: {"high": 0, "medium": 1, "low": 2}[x[1]["priority"]]
        )

        print(f"\n🚀 INICIANDO SCRAPING SEGMENTADO")
        print(f"📋 Total de segmentos: {len(sorted_segments)}")
        print(f"⏱️  Delay entre segmentos: {self.delay}s ({self.delay/60:.0f} min)")
        print(f"💾 Salvar no banco: {'Sim' if save_to_db else 'Não'}\n")

        results = []

        for idx, (seg_id, seg_config) in enumerate(sorted_segments, 1):
            print(f"\n{'#'*60}")
            print(f"SEGMENTO {idx}/{len(sorted_segments)}")
            print(f"{'#'*60}")

            # Scrape segmento
            result = await self.scrape_segment(seg_id, seg_config, save_to_db=save_to_db)
            results.append(result)

            # Delay entre segmentos (exceto último)
            if idx < len(sorted_segments):
                print(f"\n⏳ Aguardando {self.delay}s antes do próximo segmento...")
                await asyncio.sleep(self.delay)

        # Relatório final
        return self.generate_report(results)

    def generate_report(self, results: List[Dict]) -> Dict:
        """Gera relatório consolidado"""
        total_scraped = sum(r["scraped"] for r in results)
        total_errors = sum(r["errors"] for r in results)
        total_duration = sum(r["duration_seconds"] for r in results)

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_segments": len(results),
            "total_scraped": total_scraped,
            "total_errors": total_errors,
            "total_duration_minutes": total_duration / 60,
            "overall_success_rate": total_scraped / (total_scraped + total_errors) if (total_scraped + total_errors) > 0 else 0,
            "segments": results
        }

        return report


async def main():
    """CLI principal"""
    parser = argparse.ArgumentParser(description="Scraper segmentado por região/preço")

    parser.add_argument(
        "--segment",
        type=str,
        help="ID de segmento específico (ex: segredo_casa_100_200k)"
    )
    parser.add_argument(
        "--segments",
        type=str,
        help="IDs de segmentos separados por vírgula"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Scrape todos os segmentos"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limite de imóveis por segmento"
    )
    parser.add_argument(
        "--segment-delay",
        type=int,
        default=3600,
        help="Delay entre segmentos em segundos (padrão: 3600 = 1h)"
    )
    parser.add_argument(
        "--save-to-db",
        action="store_true",
        help="Salvar no PostgreSQL"
    )
    parser.add_argument(
        "--list-segments",
        action="store_true",
        help="Listar segmentos disponíveis"
    )

    args = parser.parse_args()

    # Listar segmentos
    if args.list_segments:
        print("\n📋 SEGMENTOS DISPONÍVEIS:\n")
        for seg_id, seg_config in MARKET_SEGMENTS.items():
            print(f"  • {seg_id}")
            print(f"    Nome: {seg_config['name']}")
            print(f"    Prioridade: {seg_config['priority']}")
            print(f"    Estimado: ~{seg_config['expected_count']} imóveis\n")
        return

    # Criar scraper
    scraper = SegmentedScraper(delay_between_segments=args.segment_delay)

    # Executar
    if args.segment:
        # Segmento único
        if args.segment not in MARKET_SEGMENTS:
            print(f"❌ Segmento '{args.segment}' não encontrado")
            print(f"   Use --list-segments para ver opções")
            return

        result = await scraper.scrape_segment(
            args.segment,
            MARKET_SEGMENTS[args.segment],
            limit=args.limit,
            save_to_db=args.save_to_db
        )

    elif args.segments:
        # Lista de segmentos
        segment_ids = [s.strip() for s in args.segments.split(",")]
        report = await scraper.scrape_all_segments(
            segment_ids=segment_ids,
            save_to_db=args.save_to_db
        )
        print_final_report(report)

    elif args.all:
        # Todos os segmentos
        report = await scraper.scrape_all_segments(save_to_db=args.save_to_db)
        print_final_report(report)

    else:
        parser.print_help()


def print_final_report(report: Dict):
    """Imprime relatório final formatado"""
    print(f"\n{'='*60}")
    print(f"📊 RELATÓRIO FINAL - SCRAPING SEGMENTADO")
    print(f"{'='*60}\n")

    print(f"⏱️  Duração total: {report['total_duration_minutes']:.1f} minutos")
    print(f"📋 Segmentos processados: {report['total_segments']}")
    print(f"✅ Total scraped: {report['total_scraped']}")
    print(f"❌ Total erros: {report['total_errors']}")
    print(f"📈 Taxa de sucesso: {report['overall_success_rate']:.1%}\n")

    print(f"{'='*60}\n")

    # Salvar relatório
    import json
    filename = f".tmp/segment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"💾 Relatório salvo: {filename}")


if __name__ == "__main__":
    asyncio.run(main())
```

**Checklist:**
- [ ] Criar `tools/scraper_by_segments.py`
- [ ] Implementar classe `SegmentedScraper`
- [ ] Implementar `scrape_segment()` (individual)
- [ ] Implementar `scrape_all_segments()` (batch)
- [ ] Implementar `discover_urls()` com filtros
- [ ] Implementar `generate_report()`
- [ ] Adicionar CLI com argparse
- [ ] Logging detalhado

---

### ETAPA 3: Testes Progressivos (2-3h)

#### Teste 1: Segmento Único (10 min)

```bash
# Listar segmentos disponíveis
python tools/scraper_by_segments.py --list-segments

# Testar 1 segmento, 10 imóveis, sem salvar
python tools/scraper_by_segments.py \
    --segment segredo_casa_100_200k \
    --limit 10

# Verificar resultado
ls -lh .tmp/segment_report_*.json
```

**Validar:**
- [ ] 10 URLs descobertas
- [ ] 10 imóveis scrapados
- [ ] Taxa de sucesso 100%
- [ ] Tempo < 15 minutos
- [ ] Relatório JSON gerado

#### Teste 2: Dois Segmentos com Delay (1h 30min)

```bash
# 2 segmentos, 20 imóveis cada, delay 1h, salvar no banco
python tools/scraper_by_segments.py \
    --segments "segredo_casa_100_200k,centro_apto_150_300k" \
    --limit 20 \
    --segment-delay 3600 \
    --save-to-db

# Verificar banco
python -c "from tools.property_saver import get_property_stats; import json; print(json.dumps(get_property_stats(), indent=2))"
```

**Validar:**
- [ ] Segmento 1: 20 imóveis
- [ ] Delay de 1h respeitado
- [ ] Segmento 2: 20 imóveis
- [ ] Total 40 imóveis no banco
- [ ] Relatório final completo

#### Teste 3: Batch Reduzido (3-4h)

```bash
# 5 segmentos prioritários, delay 30min
python tools/scraper_by_segments.py \
    --segments "segredo_casa_100_200k,segredo_casa_200_400k,centro_apto_150_300k,prosa_casa_200_400k,jardim_estados_300_500k" \
    --segment-delay 1800 \
    --save-to-db

# Dashboard
python tools/metrics_dashboard.py
```

**Validar:**
- [ ] 5 segmentos processados
- [ ] ~250 imóveis coletados
- [ ] Taxa de sucesso > 90%
- [ ] Zero bloqueios
- [ ] Dashboard funcionando

---

### ETAPA 4: Integração no Workflow Existente (1-2h)

**Arquivo:** `tools/workflow_complete.py`

**Modificações:**

```python
# Adicionar modo segmentado
parser.add_argument(
    '--segmented',
    action='store_true',
    help='Use segmented scraping (safer, recommended)'
)

parser.add_argument(
    '--segments',
    type=str,
    help='Specific segments (comma-separated) or --all'
)

parser.add_argument(
    '--segment-delay',
    type=int,
    default=3600,
    help='Delay between segments in seconds (default: 3600 = 1h)'
)

# No código principal
if args.segmented:
    from scraper_by_segments import SegmentedScraper

    scraper = SegmentedScraper(delay_between_segments=args.segment_delay)

    if args.segments:
        segment_ids = [s.strip() for s in args.segments.split(",")]
        report = await scraper.scrape_all_segments(
            segment_ids=segment_ids,
            save_to_db=args.save_to_db
        )
    else:
        # Modo linear atual (mantido para compatibilidade)
        report = await legacy_scrape_workflow(args)
else:
    # Modo linear atual (padrão)
    report = await legacy_scrape_workflow(args)
```

**Checklist:**
- [ ] Adicionar flags `--segmented`, `--segments`, `--segment-delay`
- [ ] Integrar `SegmentedScraper` no workflow
- [ ] Manter compatibilidade com modo linear
- [ ] Testar ambos os modos

---

## 📊 Critérios de Sucesso

| Métrica | Meta | Como Validar |
|---------|------|--------------|
| **Segmentos definidos** | 10 | Contar em `MARKET_SEGMENTS` |
| **Teste 1 (1 segmento)** | 10/10 sucesso | Verificar relatório JSON |
| **Teste 2 (2 segmentos)** | 40 imóveis no banco | Query PostgreSQL |
| **Teste 3 (5 segmentos)** | >90% taxa sucesso | Relatório final |
| **Taxa de bloqueio** | 0 | Logs de erro |
| **Tempo por segmento** | <30min | Relatórios JSON |

---

## 📁 Arquivos Criados/Modificados

### Novos Arquivos:
1. `tools/market_segments.py` (~100 linhas)
2. `tools/scraper_by_segments.py` (~400 linhas)
3. `PLANO_IMPLEMENTACAO_FASE1.md` (este arquivo)

### Arquivos Modificados:
1. `tools/workflow_complete.py` (~30 linhas adicionadas)

---

## 🚀 Como Executar

### 1. Implementação
```bash
# Criar arquivos novos
touch tools/market_segments.py
touch tools/scraper_by_segments.py

# Começar implementação
code tools/market_segments.py
```

### 2. Testes
```bash
# Teste 1 (10 min)
python tools/scraper_by_segments.py --segment segredo_casa_100_200k --limit 10

# Teste 2 (1h 30min)
python tools/scraper_by_segments.py --segments "segredo_casa_100_200k,centro_apto_150_300k" --limit 20 --save-to-db

# Teste 3 (3-4h)
python tools/scraper_by_segments.py --segments "segredo_casa_100_200k,centro_apto_150_300k,prosa_casa_200_400k" --save-to-db
```

### 3. Produção
```bash
# Todos os segmentos (1 dia)
python tools/scraper_by_segments.py --all --save-to-db
```

---

## 📝 Checklist Completo

### Planejamento
- [x] Criar plano de implementação
- [x] Definir estrutura de arquivos
- [x] Especificar interfaces

### Implementação
- [ ] ETAPA 1: Definir segmentos (1-2h)
- [ ] ETAPA 2: Implementar scraper (3-4h)
- [ ] ETAPA 3: Testes progressivos (2-3h)
- [ ] ETAPA 4: Integração workflow (1-2h)

### Validação
- [ ] Teste 1: 1 segmento, 10 imóveis
- [ ] Teste 2: 2 segmentos, 40 imóveis
- [ ] Teste 3: 5 segmentos, ~250 imóveis
- [ ] Dashboard funcionando
- [ ] Zero bloqueios confirmado

### Documentação
- [ ] Atualizar README.md
- [ ] Documentar no FASE_1_SEGMENTACAO.md
- [ ] Commit final da Fase 1

---

## ⏭️ Próximos Passos (Pós-Fase 1)

Após conclusão:
1. ✅ Scraping segmentado operacional
2. ➡️ **FASE 2:** Melhorar parser (55% → 85% completude)
3. ➡️ **FASE 3:** Download e análise de imagens

---

**Última atualização:** 2026-02-05
**Estimativa total:** 8-12 horas de implementação + testes
**Status:** 🟢 Pronto para começar
