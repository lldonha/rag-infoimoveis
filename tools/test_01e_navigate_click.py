#!/usr/bin/env python3
"""
Etapa 0.1e: Navegar usando cliques
==================================
Navegar pelo site usando cliques para manter a sessao
"""

import asyncio
import json
from playwright.async_api import async_playwright

BASE_URL = "https://www.infoimoveis.com.br"


async def navigate_with_clicks():
    """Navega pelo site usando cliques"""
    print("=" * 60)
    print("Navegando pelo Site com Cliques")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ]
        )

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
        )

        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)

        page = await context.new_page()

        # Acessar home
        print("\n1. Acessando home...")
        await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)

        # Aguardar Cloudflare
        print("   Aguardando Cloudflare (20s)...")
        await page.wait_for_timeout(20000)

        title = await page.title()
        print(f"   Titulo: {title}")

        if "moment" in title.lower():
            print("\n[FAIL] Cloudflare ainda ativo. Tente resolver captcha manualmente.")
            await page.wait_for_timeout(30000)
            title = await page.title()
            print(f"   Titulo apos espera: {title}")

        # Verificar se passou (verificar se NAO e Cloudflare)
        if "moment" not in title.lower() and "cloudflare" not in title.lower():
            print("\n[OK] Site carregado!")

            # Procurar link de busca detalhada
            print("\n2. Procurando link de busca detalhada...")

            # Tentar varios seletores
            busca_link = await page.query_selector("a[href*='buscadetalhada']")

            if busca_link:
                print("   Link encontrado! Clicando...")
                await busca_link.click()
                await page.wait_for_timeout(5000)

                title = await page.title()
                print(f"   Titulo apos clique: {title}")

                await page.screenshot(path=".tmp/after_click_search.png", full_page=False)
            else:
                print("   Link de busca detalhada nao encontrado")

                # Listar todos os links
                links = await page.query_selector_all("a")
                print(f"\n   Total de links: {len(links)}")

                for link in links[:30]:
                    href = await link.get_attribute("href")
                    text = await link.text_content()
                    if href and text:
                        text = text.strip()[:40]
                        if text:
                            print(f"   - {text}: {href[:60]}")

            # Tentar acessar um imovel especifico
            print("\n3. Procurando link de imovel para testar...")

            property_link = await page.query_selector("a[href*='/imovel/']")
            if property_link:
                href = await property_link.get_attribute("href")
                print(f"   Imovel encontrado: {href}")
                print("   Clicando...")

                await property_link.click()
                await page.wait_for_timeout(5000)

                title = await page.title()
                print(f"   Titulo da pagina do imovel: {title}")

                await page.screenshot(path=".tmp/property_page.png", full_page=False)

                # Capturar HTML da pagina do imovel
                content = await page.content()
                with open(".tmp/property_page.html", "w", encoding="utf-8") as f:
                    f.write(content)
                print("   HTML salvo em .tmp/property_page.html")

                # Extrair dados basicos
                print("\n4. Extraindo dados do imovel...")

                # Titulo
                h1 = await page.query_selector("h1")
                if h1:
                    titulo = await h1.text_content()
                    print(f"   Titulo: {titulo.strip()[:60]}")

                # Preco
                preco_elem = await page.query_selector("[class*='preco'], [class*='price'], .valor, .price")
                if preco_elem:
                    preco = await preco_elem.text_content()
                    print(f"   Preco: {preco.strip()}")

                # Area
                area_elem = await page.query_selector("[class*='area'], [class*='metros']")
                if area_elem:
                    area = await area_elem.text_content()
                    print(f"   Area: {area.strip()[:30]}")

            # Salvar cookies atualizados
            cookies = await context.cookies()
            with open(".tmp/cookies.json", "w") as f:
                json.dump(cookies, f, indent=2)
            print(f"\n   Cookies salvos ({len(cookies)})")

        print("\n   Browser fechando em 5 segundos...")
        await page.wait_for_timeout(5000)
        await browser.close()

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(navigate_with_clicks())
