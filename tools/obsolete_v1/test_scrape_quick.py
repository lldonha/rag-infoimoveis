#!/usr/bin/env python3
"""Teste rápido de scraping"""

import asyncio
import sys

sys.path.append(".")

from scraper_production import scrape_property_safe, SmartRateLimiter
from playwright.async_api import async_playwright


async def main():
    url = "https://www.infoimoveis.com.br/imovel/venda-area-jardim-bela-vista/55162"

    print("🚀 Iniciando teste de scraping...")
    print(f"URL: {url}\n")

    rate_limiter = SmartRateLimiter()

    async with async_playwright() as p:
        result = await scrape_property_safe(
            p, url, rate_limiter, use_cookies=False, save_to_db=False, use_stealth=True
        )

        if result:
            print("\n✅ SUCESSO!")
            print(f"Título: {result.get('title')}")
            print(f"Preço: R$ {result.get('price_brl'):,.2f}")
            print(f"Imagens: {len(result.get('images', []))}")
        else:
            print("\n❌ FALHOU")


if __name__ == "__main__":
    asyncio.run(main())
