"""
Workflow Completo: Discovery → Scraping → PostgreSQL → Dashboard

Pipeline end-to-end:
1. Discovery Filtrado (buscar URLs)
2. Scraping com Stealth (coletar dados)
3. Save PostgreSQL (batch insert)
4. Métricas Dashboard (validação)

Uso:
    python tools/workflow_complete.py --preset segredo_100_200k --max-pages 3 --limit 50 --save-to-db
"""
import asyncio
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add parent dir to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.discovery_filtered import discover_by_preset, discover_properties_filtered
from tools.scraper_production import scrape_multiple_properties
from tools.metrics_dashboard import print_dashboard


def print_banner():
    """Exibe banner do workflow"""
    print("\n" + "=" * 80)
    print("🚀 WORKFLOW COMPLETO - Sistema RAG InfoImóveis")
    print("=" * 80)
    print(f"⏰ Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")


def print_phase(phase_num: int, phase_name: str):
    """Exibe cabeçalho de fase"""
    print(f"\n{'=' * 80}")
    print(f"📍 FASE {phase_num}: {phase_name}")
    print(f"{'=' * 80}\n")


async def run_discovery(
    preset: str = None,
    property_type: str = None,
    region: str = None,
    price_min: float = None,
    price_max: float = None,
    max_pages: int = 5
) -> List[str]:
    """
    Fase 1: Discovery de URLs

    Args:
        preset: Nome do preset (ex: 'segredo_100_200k')
        property_type: Tipo do imóvel (ex: 'casa-terrea')
        region: Região (ex: 'regiao-segredo')
        price_min: Preço mínimo
        price_max: Preço máximo
        max_pages: Máximo de páginas

    Returns:
        Lista de URLs descobertas
    """
    print_phase(1, "DISCOVERY - Buscar URLs de Imóveis")

    if preset:
        print(f"🎯 Usando preset: {preset}")
        urls = await discover_by_preset(preset, max_pages=max_pages)
    else:
        print(f"🔍 Busca customizada:")
        print(f"   Tipo: {property_type}")
        print(f"   Região: {region}")
        print(f"   Preço: R$ {price_min:,.0f} - R$ {price_max:,.0f}")
        print(f"   Páginas: {max_pages}")

        urls = await discover_properties_filtered(
            property_type=property_type,
            region=region,
            price_min=price_min,
            price_max=price_max,
            max_pages=max_pages
        )

    print(f"\n✅ Discovery completo!")
    print(f"   📊 Total encontrado: {len(urls)} imóveis")

    if urls:
        print(f"\n📋 Amostra das URLs:")
        for i, url in enumerate(urls[:5], 1):
            print(f"   {i}. {url}")
        if len(urls) > 5:
            print(f"   ... e mais {len(urls) - 5}")

    return urls


async def run_scraping(
    urls: List[str],
    limit: int = None,
    save_to_db: bool = True,
    use_stealth: bool = True
) -> Dict:
    """
    Fase 2: Scraping com Stealth

    Args:
        urls: Lista de URLs
        limit: Limitar número de imóveis
        save_to_db: Salvar no banco
        use_stealth: Usar playwright-stealth

    Returns:
        Dict com estatísticas
    """
    print_phase(2, "SCRAPING - Coletar Dados com Stealth")

    if limit and len(urls) > limit:
        print(f"⚠️  Limitando de {len(urls)} para {limit} imóveis")
        urls = urls[:limit]

    print(f"🔒 Modo: {'STEALTH (playwright-stealth)' if use_stealth else 'PADRÃO'}")
    print(f"💾 Salvar no banco: {'Sim' if save_to_db else 'Não'}")
    print(f"📊 Total a processar: {len(urls)} imóveis\n")

    stats = await scrape_multiple_properties(
        urls=urls,
        max_per_session=len(urls),
        save_to_db=save_to_db,
        use_stealth=use_stealth
    )

    print(f"\n✅ Scraping completo!")
    print(f"   ✅ Sucesso: {stats['success']}")
    print(f"   ❌ Erros: {stats['errors']}")
    print(f"   📈 Taxa de sucesso: {stats['success'] / len(urls) * 100:.1f}%")

    return stats


def run_metrics():
    """
    Fase 3: Dashboard de Métricas

    Exibe estatísticas do banco
    """
    print_phase(3, "MÉTRICAS - Validação dos Dados")

    try:
        print_dashboard()
        print(f"\n✅ Métricas exibidas com sucesso!")
    except Exception as e:
        print(f"⚠️  Erro ao exibir métricas: {e}")


def print_summary(discovery_count: int, stats: Dict):
    """
    Exibe resumo final do workflow

    Args:
        discovery_count: Total de URLs descobertas
        stats: Estatísticas do scraping
    """
    print("\n" + "=" * 80)
    print("📊 RESUMO DO WORKFLOW")
    print("=" * 80)

    print(f"\n📍 Discovery:")
    print(f"   URLs encontradas: {discovery_count}")

    print(f"\n📍 Scraping:")
    print(f"   URLs processadas: {stats['success'] + stats['errors']}")
    print(f"   ✅ Sucesso: {stats['success']}")
    print(f"   ❌ Erros: {stats['errors']}")
    print(f"   📈 Taxa de sucesso: {stats['success'] / (stats['success'] + stats['errors']) * 100:.1f}%")

    print(f"\n⏰ Tempo:")
    print(f"   Início: {stats['start_time']}")
    print(f"   Fim: {stats['end_time']}")

    # Calcular tempo total
    try:
        start = datetime.fromisoformat(stats['start_time'])
        end = datetime.fromisoformat(stats['end_time'])
        duration = (end - start).total_seconds()
        print(f"   Duração: {duration:.1f}s ({duration/60:.1f} min)")
    except:
        pass

    print("\n" + "=" * 80)


async def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Workflow Completo: Discovery → Scraping → DB → Métricas"
    )

    # Discovery options
    discovery = parser.add_argument_group('Discovery')
    discovery.add_argument('--preset', type=str, help='Preset de busca (ex: segredo_100_200k)')
    discovery.add_argument('--property-type', type=str, help='Tipo de imóvel (ex: casa-terrea)')
    discovery.add_argument('--region', type=str, help='Região (ex: regiao-segredo)')
    discovery.add_argument('--price-min', type=float, help='Preço mínimo')
    discovery.add_argument('--price-max', type=float, help='Preço máximo')
    discovery.add_argument('--max-pages', type=int, default=5, help='Máximo de páginas (default: 5)')

    # Scraping options
    scraping = parser.add_argument_group('Scraping')
    scraping.add_argument('--limit', type=int, help='Limitar número de imóveis')
    scraping.add_argument('--no-stealth', action='store_true', help='Desativar stealth mode')
    scraping.add_argument('--no-save', action='store_true', help='Não salvar no banco')

    args = parser.parse_args()

    # Validação
    if not args.preset and not (args.property_type and args.region):
        parser.error("Forneça --preset OU (--property-type E --region)")

    print_banner()

    try:
        # FASE 1: Discovery
        urls = await run_discovery(
            preset=args.preset,
            property_type=args.property_type,
            region=args.region,
            price_min=args.price_min,
            price_max=args.price_max,
            max_pages=args.max_pages
        )

        if not urls:
            print("\n❌ Nenhuma URL encontrada! Abortando workflow.")
            return

        # FASE 2: Scraping
        stats = await run_scraping(
            urls=urls,
            limit=args.limit,
            save_to_db=not args.no_save,
            use_stealth=not args.no_stealth
        )

        # FASE 3: Métricas (somente se salvou no banco)
        if not args.no_save:
            run_metrics()

        # RESUMO FINAL
        print_summary(len(urls), stats)

        print(f"\n✅ Workflow completo executado com sucesso! 🎉\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrompido pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro no workflow: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
