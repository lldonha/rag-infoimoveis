#!/usr/bin/env python3
"""
Page Inspector
==============
Inspeciona estrutura da página para debug
"""

import asyncio
import sys
import os
from playwright.async_api import async_playwright

sys.path.append(os.path.dirname(__file__))
from cookie_manager import load_cookies


async def inspect():
    cookies = load_cookies()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        if cookies:
            await context.add_cookies(cookies)

        page = await context.new_page()

        url = "https://www.infoimoveis.com.br/venda/apartamento/campo-grande-ms/"
        print(f"Acessando: {url}")

        await page.goto(url, wait_until='networkidle', timeout=60000)

        print("\n" + "=" * 60)
        print("Aguardando página carregar completamente...")
        print("=" * 60)
        await asyncio.sleep(5)

        # Salvar HTML e screenshot
        html = await page.content()
        with open('.tmp/inspect_page.html', 'w', encoding='utf-8') as f:
            f.write(html)

        await page.screenshot(path='.tmp/inspect_page.png', full_page=True)

        # Buscar links
        print("\n📋 Procurando links de imóveis...")

        all_links = await page.query_selector_all("a[href]")
        print(f"Total de links: {len(all_links)}")

        property_links = []
        for link in all_links:
            href = await link.get_attribute('href')
            if href and ('imovel' in href.lower() or 'codigo' in href.lower()):
                property_links.append(href)

        print(f"\nLinks de imóveis encontrados: {len(property_links)}")
        for i, link in enumerate(property_links[:10], 1):
            print(f"  {i}. {link[:100]}")

        print(f"\n✅ HTML salvo em: .tmp/inspect_page.html")
        print(f"✅ Screenshot em: .tmp/inspect_page.png")

        print("\nAguardando 10 segundos para você inspecionar o browser...")
        await asyncio.sleep(10)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(inspect())
