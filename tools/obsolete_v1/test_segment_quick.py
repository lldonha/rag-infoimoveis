#!/usr/bin/env python3
"""Teste rápido do scraper segmentado"""

import asyncio
import sys
sys.path.append('tools')

from scraper_by_segments import SegmentedScraper
from market_segments import MARKET_SEGMENTS

async def main():
    print("🧪 TESTE RÁPIDO - Scraper Segmentado\n")

    # Criar scraper com delay mínimo
    scraper = SegmentedScraper(delay_between_segments=0, mode="aggressive")

    # Modificar configuração para teste super rápido
    scraper.mode_config['delay_between_properties'] = 2  # 2s apenas

    # Pegar apenas 1 URL para teste
    segment_id = "segredo_casa_100_200k"
    segment_config = MARKET_SEGMENTS[segment_id]

    print(f"Testando segmento: {segment_config['name']}\n")

    # Scrape com limite de 1 imóvel
    result = await scraper.scrape_segment(
        segment_id,
        segment_config,
        limit=1,  # Apenas 1 URL
        save_to_db=False  # Não salvar
    )

    print(f"\n📊 RESULTADO:")
    print(f"   Scraped: {result['scraped']}")
    print(f"   Errors: {result['errors']}")
    print(f"   Duration: {result['duration_minutes']:.2f} min")
    print(f"   Success rate: {result['success_rate']:.0%}")

    if result['scraped'] > 0:
        print(f"\n✅ TESTE PASSOU!")
    else:
        print(f"\n❌ TESTE FALHOU - Nenhum imóvel scrapado")

if __name__ == "__main__":
    asyncio.run(main())
