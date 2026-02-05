"""
Teste Workflow Completo - 10 Imóveis

Discovery → Scraping → Validação (sem salvar no banco)
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from tools.discovery_filtered import discover_by_preset
from tools.scraper_production import scrape_multiple_properties


async def main():
    print("\n" + "=" * 80)
    print("🧪 TESTE WORKFLOW COMPLETO - 10 Imóveis")
    print("=" * 80)
    print(f"⏰ Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")

    # FASE 1: Discovery
    print("📍 FASE 1: DISCOVERY")
    print("-" * 80)

    urls = await discover_by_preset('segredo_100_200k', max_pages=1)
    print(f"\n✅ Discovery completo: {len(urls)} URLs encontradas")

    # Limitar a 10
    urls = urls[:10]
    print(f"📊 Processando: {len(urls)} imóveis\n")

    # FASE 2: Scraping
    print("\n📍 FASE 2: SCRAPING COM STEALTH")
    print("-" * 80 + "\n")

    stats = await scrape_multiple_properties(
        urls=urls,
        max_per_session=10,
        save_to_db=False,  # NÃO salvar (apenas teste)
        use_stealth=True
    )

    # FASE 3: Resultados
    print("\n" + "=" * 80)
    print("📊 RESULTADO DO TESTE")
    print("=" * 80)

    total = len(urls)
    success = stats['success']
    errors = stats['errors']
    success_rate = (success / total * 100) if total > 0 else 0

    print(f"\n✅ Sucesso: {success}/{total}")
    print(f"❌ Erros: {errors}/{total}")
    print(f"📈 Taxa de sucesso: {success_rate:.1f}%")

    # Validação
    print("\n" + "=" * 80)
    if success_rate >= 80:
        print("✅ TESTE PASSOU! Sistema pronto para produção!")
        print("🎉 Próximo passo: Teste com 50 imóveis + Salvar no banco")
    else:
        print(f"⚠️  TESTE FALHOU! Taxa < 80% ({success_rate:.1f}%)")
        print("🔧 Revisar logs e ajustar")

    print("=" * 80)
    print(f"⏰ Fim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    return success_rate >= 80


if __name__ == "__main__":
    passed = asyncio.run(main())
    sys.exit(0 if passed else 1)
