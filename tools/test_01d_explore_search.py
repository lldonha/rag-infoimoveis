#!/usr/bin/env python3
"""
Etapa 0.1d: Explorar pagina de busca detalhada
==============================================
Descobrir como filtrar por Campo Grande - MS
"""

import asyncio
import json
from playwright.async_api import async_playwright

BASE_URL = "https://www.infoimoveis.com.br"
SEARCH_URL = f"{BASE_URL}/buscadetalhada/"


async def explore_search_page():
    """Explora a pagina de busca detalhada"""
    print("=" * 60)
    print("Explorando Pagina de Busca Detalhada")
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

        # Carregar cookies salvos se existirem
        try:
            with open(".tmp/cookies.json", "r") as f:
                cookies = json.load(f)
                await context.add_cookies(cookies)
                print("Cookies carregados!")
        except FileNotFoundError:
            print("Cookies nao encontrados, iniciando do zero")

        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)

        page = await context.new_page()

        # Primeiro acessar home para passar pelo Cloudflare
        print("\n1. Acessando home primeiro...")
        await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)

        title = await page.title()
        if "moment" in title.lower():
            print("   Aguardando Cloudflare...")
            await page.wait_for_timeout(15000)

        # Agora acessar busca detalhada
        print("\n2. Acessando pagina de busca detalhada...")
        await page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)

        title = await page.title()
        print(f"   Titulo: {title}")

        # Capturar screenshot
        await page.screenshot(path=".tmp/search_page.png", full_page=True)
        print("   Screenshot salvo em .tmp/search_page.png")

        # Analisar formulario de busca
        print("\n3. Analisando formulario de busca...")

        # Procurar selects
        selects = await page.query_selector_all("select")
        print(f"\n   Selects encontrados: {len(selects)}")

        for sel in selects:
            name = await sel.get_attribute("name") or await sel.get_attribute("id")
            options = await sel.query_selector_all("option")
            print(f"\n   Select: {name}")
            for opt in options[:10]:
                value = await opt.get_attribute("value")
                text = await opt.text_content()
                if value:
                    print(f"      - {value}: {text.strip()[:50] if text else ''}")
            if len(options) > 10:
                print(f"      ... e mais {len(options) - 10} opcoes")

        # Procurar inputs
        inputs = await page.query_selector_all("input[type='text'], input[type='number']")
        print(f"\n   Inputs de texto: {len(inputs)}")
        for inp in inputs[:10]:
            name = await inp.get_attribute("name") or await inp.get_attribute("id") or await inp.get_attribute("placeholder")
            print(f"      - {name}")

        # Procurar checkboxes e radios
        checks = await page.query_selector_all("input[type='checkbox'], input[type='radio']")
        print(f"\n   Checkboxes/Radios: {len(checks)}")

        # Procurar botao de busca
        buttons = await page.query_selector_all("button, input[type='submit']")
        print(f"\n   Botoes: {len(buttons)}")
        for btn in buttons[:5]:
            text = await btn.text_content() or await btn.get_attribute("value")
            print(f"      - {text.strip()[:30] if text else 'sem texto'}")

        # Tentar encontrar Campo Grande nas opcoes
        print("\n4. Procurando Campo Grande nas opcoes...")
        content = await page.content()

        if "campo grande" in content.lower():
            print("   [OK] Campo Grande encontrado no HTML!")

            # Procurar valor especifico
            import re
            cg_matches = re.findall(r'value="([^"]*)"[^>]*>([^<]*campo[^<]*grande[^<]*)', content, re.IGNORECASE)
            for value, text in cg_matches[:5]:
                print(f"      - value='{value}': {text.strip()}")
        else:
            print("   [!] Campo Grande NAO encontrado diretamente")

        # Salvar HTML
        with open(".tmp/search_page.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("\n   HTML salvo em .tmp/search_page.html")

        # Tentar fazer uma busca simples
        print("\n5. Tentando fazer busca por Campo Grande...")

        # Procurar select de estado/cidade
        estado_select = await page.query_selector("select[name*='estado'], select[name*='uf'], select#estado, select#uf")
        cidade_select = await page.query_selector("select[name*='cidade'], select#cidade")

        if estado_select:
            print("   Select de estado encontrado!")
            # Tentar selecionar MS
            try:
                await estado_select.select_option(label="Mato Grosso do Sul")
                print("   MS selecionado!")
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"   Erro ao selecionar MS: {e}")

        if cidade_select:
            print("   Select de cidade encontrado!")
            await page.wait_for_timeout(2000)
            # Verificar opcoes carregadas
            options = await cidade_select.query_selector_all("option")
            print(f"   Opcoes de cidade: {len(options)}")

        # Screenshot final
        await page.screenshot(path=".tmp/search_filled.png", full_page=True)

        print("\n   Browser fechando em 5 segundos...")
        await page.wait_for_timeout(5000)
        await browser.close()

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(explore_search_page())
