#!/usr/bin/env python3
"""
Etapa 0.1c: Bypass Cloudflare
=============================
Tentar acessar o site com configuracoes anti-deteccao
"""

import asyncio
import json
from playwright.async_api import async_playwright

BASE_URL = "https://www.infoimoveis.com.br"


async def test_stealth_access():
    """Testa acesso com configuracoes anti-deteccao"""
    print("=" * 60)
    print("Teste de Acesso com Stealth Mode")
    print("=" * 60)

    async with async_playwright() as p:
        # Usar chromium com configuracoes menos detectaveis
        browser = await p.chromium.launch(
            headless=False,  # Modo visible ajuda a passar pelo Cloudflare
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-infobars",
                "--disable-extensions",
                "--disable-gpu",
                "--disable-setuid-sandbox",
                "--window-size=1920,1080",
            ]
        )

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            java_script_enabled=True,
        )

        # Remover webdriver flag
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Remover automacao flags
            window.chrome = {
                runtime: {}
            };

            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            Object.defineProperty(navigator, 'languages', {
                get: () => ['pt-BR', 'pt', 'en-US', 'en']
            });
        """)

        page = await context.new_page()

        print("\n1. Acessando pagina inicial com stealth...")
        await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)

        # Aguardar mais tempo para o Cloudflare processar
        print("   Aguardando Cloudflare (20 segundos)...")
        await page.wait_for_timeout(20000)

        title = await page.title()
        print(f"   Titulo: {title}")

        # Verificar se passou do Cloudflare
        if "moment" not in title.lower() and "cloudflare" not in title.lower() and "checking" not in title.lower():
            print("\n[OK] Cloudflare bypassed!")

            # Explorar o site
            print("\n2. Explorando links...")
            content = await page.content()

            # Salvar HTML para analise
            with open(".tmp/homepage.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("   HTML salvo em .tmp/homepage.html")

            # Procurar links
            links = await page.query_selector_all("a[href]")
            print(f"   Links encontrados: {len(links)}")

            unique_hrefs = set()
            for link in links[:100]:
                href = await link.get_attribute("href")
                if href:
                    unique_hrefs.add(href)

            # Filtrar links relevantes
            property_links = [h for h in unique_hrefs if "/imovel" in h.lower() or "detalhe" in h.lower()]
            search_links = [h for h in unique_hrefs if "busca" in h.lower() or "venda" in h.lower() or "aluguel" in h.lower()]

            print(f"\n   Links de imoveis ({len(property_links)}):")
            for href in sorted(property_links)[:10]:
                print(f"   - {href}")

            print(f"\n   Links de busca ({len(search_links)}):")
            for href in sorted(search_links)[:10]:
                print(f"   - {href}")

            # Salvar cookies para uso futuro
            cookies = await context.cookies()
            with open(".tmp/cookies.json", "w") as f:
                json.dump(cookies, f, indent=2)
            print(f"\n   Cookies salvos ({len(cookies)} cookies)")

            # Screenshot
            await page.screenshot(path=".tmp/homepage_stealth.png", full_page=False)
            print("   Screenshot salvo em .tmp/homepage_stealth.png")

        else:
            print("\n[FAIL] Cloudflare ainda ativo")
            print("   Pode ser necessario resolver CAPTCHA manualmente")

            # Aguardar mais e tirar screenshot
            await page.screenshot(path=".tmp/cloudflare_block.png", full_page=False)
            print("   Screenshot salvo em .tmp/cloudflare_block.png")

            # Salvar HTML do Cloudflare para debug
            content = await page.content()
            with open(".tmp/cloudflare_page.html", "w", encoding="utf-8") as f:
                f.write(content)

        print("\n   Browser fechando...")
        await browser.close()

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_stealth_access())
