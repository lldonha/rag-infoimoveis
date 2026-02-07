"""
Teste Workflow com 5 Imóveis - Sem Discovery (mais rápido)

Testa apenas: Scraping com Stealth → PostgreSQL
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from tools.scraper_production import scrape_multiple_properties


async def main():
    print("\n" + "=" * 80)
    print("🧪 TESTE WORKFLOW - 5 Imóveis com Stealth")
    print("=" * 80)
    print(f"⏰ Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")

    # URLs de teste (imóveis conhecidos)
    test_urls = [
        "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-giocondo-orsi/557442",
        "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-jardim-monumento/557441",
        "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-jardim-dos-estados/557440",
        "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-coronel-antonino/557439",
        "https://www.infoimoveis.com.br/imovel/venda-apartamento-centro/557438",
    ]

    print(f"📋 URLs de teste: {len(test_urls)} imóveis")
    print(f"🔒 Modo: STEALTH (playwright-stealth)")
    print(f"💾 Salvar no banco: Não (teste)")
    print(f"\nIniciando scraping...\n")

    # Executar scraping
    stats = await scrape_multiple_properties(
        urls=test_urls,
        max_per_session=5,
        save_to_db=False,  # Não salvar no teste
        use_stealth=True    # Usar stealth
    )

    print("\n" + "=" * 80)
    print("📊 RESULTADO DO TESTE")
    print("=" * 80)
    print(f"\n✅ Sucesso: {stats['success']}/{len(test_urls)}")
    print(f"❌ Erros: {stats['errors']}/{len(test_urls)}")
    print(f"📈 Taxa de sucesso: {stats['success'] / len(test_urls) * 100:.1f}%")

    # Validação
    success_rate = stats['success'] / len(test_urls) * 100

    print("\n" + "=" * 80)
    if success_rate >= 80:
        print("✅ TESTE PASSOU! Taxa de sucesso ≥ 80%")
        print("🎉 Sistema pronto para produção!")
    else:
        print(f"⚠️  TESTE FALHOU! Taxa de sucesso < 80% ({success_rate:.1f}%)")
        print("🔧 Revisar logs e ajustar configurações")

    print("=" * 80 + "\n")

    return success_rate >= 80


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
