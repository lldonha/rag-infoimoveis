#!/usr/bin/env python3
"""
Testa parser melhorado em vários imóveis diferentes
"""

import asyncio
import sys

sys.path.append("tools")

# Importar o scraper
from scrape_max_simple import main as scrape_one

# URLs de teste (do PROGRESSO_SCRAPING_2026-02-06.md)
TEST_URLS = [
    "https://www.infoimoveis.com.br/imovel/venda-area-jardim-bela-vista/55162",  # Área
    "https://www.infoimoveis.com.br/imovel/venda-apartamento-centro/141448",  # Apartamento
    "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-autonomista/143953",  # Casa
]


async def test_multiple():
    print("=" * 80)
    print("🧪 TESTE DO PARSER EM MÚLTIPLOS IMÓVEIS")
    print("=" * 80)

    for idx, url in enumerate(TEST_URLS, 1):
        print(f"\n{'=' * 80}")
        print(f"📍 TESTE {idx}/{len(TEST_URLS)}")
        print(f"{'=' * 80}\n")

        # Modificar a URL no módulo
        import scrape_max_simple

        scrape_max_simple.TEST_URL = url

        try:
            await scrape_one()
            print(f"\n✅ Teste {idx} concluído!")
        except Exception as e:
            print(f"\n❌ Erro no teste {idx}: {e}")

        if idx < len(TEST_URLS):
            print(f"\n⏳ Aguardando 15s antes do próximo...")
            await asyncio.sleep(15)

    print("\n" + "=" * 80)
    print("✅ TODOS OS TESTES CONCLUÍDOS!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_multiple())
