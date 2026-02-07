#!/usr/bin/env python3
"""
Etapa 0.2b: Busca direta via URL
================================
Usar URL direta de busca para Campo Grande
"""

import asyncio
import json
from playwright.async_api import async_playwright

BASE_URL = "https://www.infoimoveis.com.br"

# URLs de busca descobertas
SEARCH_URLS = [
    # Busca geral Campo Grande - Venda
    f"{BASE_URL}/busca.php?finalidade=venda&uf=ms&cidade=campo-grande",
    # Apartamentos venda Campo Grande
    f"{BASE_URL}/venda/apartamento/ms/campo-grande/",
    # Casas venda Campo Grande
    f"{BASE_URL}/venda/casa-terrea/ms/campo-grande/",
    # Terrenos venda Campo Grande
    f"{BASE_URL}/venda/terreno/ms/campo-grande/",
    # Comercial venda Campo Grande
    f"{BASE_URL}/venda/sala-salao-loja/ms/campo-grande/",
]


async def test_direct_urls():
    """Testa URLs diretas de busca"""
    print("=" * 60)
    print("Testando URLs Diretas de Busca")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="pt-BR",
        )

        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)

        page = await context.new_page()

        # Primeiro passar pelo Cloudflare na home
        print("\n1. Passando pelo Cloudflare...")
        await page.goto(BASE_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(20000)

        title = await page.title()
        if "moment" in title.lower():
            print("   Aguardando mais...")
            await page.wait_for_timeout(15000)

        all_urls = set()

        # Testar cada URL de busca
        for i, url in enumerate(SEARCH_URLS, 1):
            print(f"\n{i}. Testando: {url[:60]}...")

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(5000)

                title = await page.title()
                print(f"   Titulo: {title[:50]}")

                # Coletar links de imoveis
                links = await page.query_selector_all("a[href*='/imovel/']")
                print(f"   Links encontrados: {len(links)}")

                for link in links:
                    href = await link.get_attribute("href")
                    if href and "/imovel/" in href:
                        if not href.startswith("http"):
                            href = BASE_URL + href
                        all_urls.add(href)

                # Se encontrou links, salvar screenshot
                if len(links) > 0:
                    await page.screenshot(path=f".tmp/search_result_{i}.png", full_page=False)

            except Exception as e:
                print(f"   Erro: {e}")

        print(f"\n{'='*60}")
        print(f"Total de URLs unicas coletadas: {len(all_urls)}")

        # Salvar URLs
        urls_list = sorted(all_urls)
        with open(".tmp/property_urls.json", "w") as f:
            json.dump(urls_list, f, indent=2)

        print("\nExemplos:")
        for url in urls_list[:15]:
            print(f"  - {url}")

        # Se nao encontrou via busca, tentar coletar da home
        if len(all_urls) == 0:
            print("\n\nTentando coletar da HOME...")
            await page.goto(BASE_URL, wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)

            links = await page.query_selector_all("a[href*='/imovel/']")
            print(f"Links na home: {len(links)}")

            for link in links:
                href = await link.get_attribute("href")
                if href and "/imovel/" in href:
                    if not href.startswith("http"):
                        href = BASE_URL + href
                    all_urls.add(href)

            urls_list = sorted(all_urls)
            with open(".tmp/property_urls.json", "w") as f:
                json.dump(urls_list, f, indent=2)

            print(f"\nTotal apos home: {len(all_urls)}")
            for url in urls_list[:15]:
                print(f"  - {url}")

        print("\n   Browser fechando...")
        await page.wait_for_timeout(3000)
        await browser.close()

    print("\n" + "=" * 60)
    return urls_list


if __name__ == "__main__":
    asyncio.run(test_direct_urls())
