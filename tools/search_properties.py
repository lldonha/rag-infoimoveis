#!/usr/bin/env python3
"""
Busca automática de imóveis no InfoImóveis por bairro e faixa de preço
"""

import asyncio
import json
import sys
from playwright.async_api import async_playwright
from urllib.parse import quote


async def search_properties(
    bairro: str, preco_min: int, preco_max: int, max_results: int = 10
):
    """
    Busca imóveis no InfoImóveis

    Args:
        bairro: Nome do bairro (ex: "Jardim dos Estados")
        preco_min: Preço mínimo em reais (ex: 400000)
        preco_max: Preço máximo em reais (ex: 800000)
        max_results: Número máximo de resultados
    """

    # Construir URL de busca
    bairro_slug = bairro.lower().replace(" ", "-")
    url = f"https://www.infoimoveis.com.br/venda/ms/campo-grande/casa/bairro-{bairro_slug}?preco={preco_min},{preco_max}"

    print(f"🔍 Buscando: {bairro}")
    print(f"💰 Faixa: R$ {preco_min:,.0f} - R$ {preco_max:,.0f}")
    print(f"🌐 URL: {url}")
    print()

    properties = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

        page = await context.new_page()

        try:
            # Acessar página de busca
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(5)  # Aguardar carregamento

            # Aceitar cookies se aparecer
            try:
                cookie_btn = await page.wait_for_selector(
                    'button[data-testid="accept-cookies"], .cookie-banner button, button:has-text("Aceitar")',
                    timeout=5000,
                )
                if cookie_btn:
                    await cookie_btn.click()
                    await asyncio.sleep(2)
            except:
                pass

            # Extrair URLs dos imóveis
            # Seletores comuns para cards de imóveis
            selectors = [
                'a[href*="/imovel/"]',
                ".property-card a",
                ".listing-item a",
                '[data-testid="property-link"]',
                "h2 a[href]",
                ".title a[href]",
            ]

            urls = set()
            for selector in selectors:
                try:
                    links = await page.query_selector_all(selector)
                    for link in links:
                        href = await link.get_attribute("href")
                        if href and "/imovel/" in href:
                            full_url = (
                                href
                                if href.startswith("http")
                                else f"https://www.infoimoveis.com.br{href}"
                            )
                            urls.add(full_url)
                except:
                    continue

                if len(urls) >= max_results:
                    break

            print(f"✅ Encontrados {len(urls)} imóveis")

            # Salvar URLs
            urls_list = list(urls)[:max_results]

            # Criar arquivo de saída
            output_file = f".tmp/search_{bairro_slug}_{preco_min}_{preco_max}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "bairro": bairro,
                        "preco_min": preco_min,
                        "preco_max": preco_max,
                        "total_encontrado": len(urls_list),
                        "urls": urls_list,
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            print(f"💾 URLs salvos em: {output_file}")
            print()
            print("URLs encontradas:")
            for i, url in enumerate(urls_list, 1):
                print(f"{i}. {url}")

            await browser.close()
            return urls_list

        except Exception as e:
            print(f"❌ Erro na busca: {e}")
            await browser.close()
            return []


if __name__ == "__main__":
    if len(sys.argv) >= 4:
        bairro = sys.argv[1]
        preco_min = int(sys.argv[2])
        preco_max = int(sys.argv[3])
        max_results = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    else:
        # Valores padrão
        bairro = "Jardim dos Estados"
        preco_min = 400000
        preco_max = 800000
        max_results = 10

    urls = asyncio.run(search_properties(bairro, preco_min, preco_max, max_results))

    # Salvar também como lista simples
    if urls:
        with open(".tmp/urls_para_scraping.txt", "w") as f:
            for url in urls:
                f.write(f"{url}\n")
        print(f"\n✅ Lista salva em: .tmp/urls_para_scraping.txt")
