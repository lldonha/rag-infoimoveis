#!/usr/bin/env python3
"""
Quick Test Scraper
==================
Teste rápido com cookies salvos - SEM comportamentos humanos complexos
"""

import asyncio
import sys
import os
from playwright.async_api import async_playwright

sys.path.append(os.path.dirname(__file__))
from cookie_manager import load_cookies
from property_saver import insert_property

# URLs de teste (URLs reais do banco)
TEST_URLS = [
    "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-condominio-pq-residencial-damha-iv/600817",
    "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-giocondo-orsi/557442",
    "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-itanhanga-park/643777",
    "https://www.infoimoveis.com.br/imovel/venda-sobrado-jardim-europa/372077",
    "https://www.infoimoveis.com.br/imovel/venda-sobrado-jardim-itatiaia/587992",
]


async def quick_scrape():
    """Scrape rápido sem complexidades"""

    print("=" * 60)
    print("QUICK TEST SCRAPER")
    print("=" * 60)
    print()

    # Carregar cookies
    cookies = load_cookies()
    if not cookies:
        print("❌ Cookies não encontrados! Execute primeiro:")
        print("   python tools/manual_cloudflare_bypass.py")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        # Aplicar cookies
        await context.add_cookies(cookies)

        page = await context.new_page()

        # Usar URLs diretas
        urls = TEST_URLS
        print(f"📋 Testando com {len(urls)} URLs")

        # Scrape cada imóvel
        results = []
        for i, url in enumerate(urls, 1):
            print(f"\n{'='*60}")
            print(f"[{i}/{len(urls)}] Scraping: {url[:80]}...")
            print(f"{'='*60}")

            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(2)

                # Extrair dados básicos
                title = None
                price = None

                # Título
                title_elem = await page.query_selector("h1, [class*='titulo']")
                if title_elem:
                    title = await title_elem.text_content()
                    title = title.strip() if title else None

                # Preço
                price_elem = await page.query_selector("[class*='preco'], [class*='valor']")
                if price_elem:
                    price_text = await price_elem.text_content()
                    print(f"  💰 Preço: {price_text}")

                # Criar registro mínimo
                property_data = {
                    'source_url': url,
                    'title': title,
                    'city': 'Campo Grande',
                    'state': 'MS'
                }

                # Salvar no banco
                prop_id = insert_property(property_data)

                print(f"  ✅ Título: {title[:60] if title else 'N/A'}...")
                print(f"  ✅ Salvo no banco: {prop_id}")

                results.append(property_data)

            except Exception as e:
                print(f"  ❌ Erro: {e}")

        await browser.close()

        # Resumo
        print("\n" + "=" * 60)
        print("RESUMO")
        print("=" * 60)
        print(f"✅ {len(results)} imóveis processados com sucesso")
        print(f"✅ Dados salvos no PostgreSQL")
        print()
        print("🎯 Próximo passo:")
        print("   python tools/metrics_dashboard.py")


if __name__ == "__main__":
    asyncio.run(quick_scrape())
