#!/usr/bin/env python3
"""
Etapa 0.1b: Explorar estrutura de URLs do site
==============================================
Descobrir a estrutura correta das URLs de busca e listagem
"""

import asyncio
from playwright.async_api import async_playwright

BASE_URL = "https://www.infoimoveis.com.br"


async def explore_site():
    """Explora o site para descobrir estrutura de URLs"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()

        print("=" * 60)
        print("Explorando InfoImoveis.com.br")
        print("=" * 60)

        # 1. Acessar página inicial
        print("\n1. Acessando pagina inicial...")
        await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)

        title = await page.title()
        print(f"   Titulo: {title}")

        # 2. Procurar links de navegação
        print("\n2. Procurando links de navegacao...")
        nav_links = await page.query_selector_all("a[href*='/imoveis'], a[href*='busca'], a[href*='venda'], a[href*='aluguel']")

        unique_hrefs = set()
        for link in nav_links[:20]:
            href = await link.get_attribute("href")
            if href:
                unique_hrefs.add(href)

        print(f"   Links encontrados: {len(unique_hrefs)}")
        for href in sorted(unique_hrefs)[:15]:
            print(f"   - {href}")

        # 3. Procurar formulário de busca
        print("\n3. Procurando formulario de busca...")
        search_form = await page.query_selector("form[action*='busca'], form[action*='search'], form.search, #search-form")
        if search_form:
            action = await search_form.get_attribute("action")
            print(f"   Form action: {action}")
        else:
            print("   Formulario nao encontrado diretamente")

        # 4. Procurar seletores de tipo de imóvel
        print("\n4. Procurando seletores de tipo/cidade...")
        selects = await page.query_selector_all("select")
        for sel in selects:
            name = await sel.get_attribute("name") or await sel.get_attribute("id")
            if name:
                print(f"   Select: {name}")

        # 5. Capturar screenshot para análise
        print("\n5. Capturando screenshot...")
        await page.screenshot(path=".tmp/homepage.png", full_page=False)
        print("   Salvo em .tmp/homepage.png")

        # 6. Procurar no HTML por padrões de URL
        print("\n6. Procurando padroes de URL no HTML...")
        content = await page.content()

        import re
        # Padrões comuns
        patterns = [
            r'href="(/[^"]*campo[^"]*grande[^"]*)"',
            r'href="(/[^"]*ms[^"]*)"',
            r'href="(/[^"]*venda[^"]*)"',
            r'href="(/[^"]*aluguel[^"]*)"',
            r'href="(/imovel/[^"]*)"',
        ]

        found_urls = set()
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for m in matches[:5]:
                found_urls.add(m)

        print(f"   URLs encontradas no HTML:")
        for url in sorted(found_urls)[:20]:
            print(f"   - {url}")

        # 7. Tentar clicar em "Buscar" ou similar para ver URL resultante
        print("\n7. Tentando encontrar opcoes de busca...")

        # Buscar botões ou links com texto de busca
        buttons = await page.query_selector_all("button, a.btn, input[type='submit']")
        for btn in buttons[:10]:
            text = await btn.text_content()
            if text and any(x in text.lower() for x in ['buscar', 'pesquisar', 'ver', 'todos']):
                print(f"   Botao: {text.strip()[:50]}")

        # 8. Verificar se há cards de imóveis na home
        print("\n8. Procurando cards de imoveis na home...")
        property_links = await page.query_selector_all("a[href*='/imovel/']")
        print(f"   Links de imoveis encontrados: {len(property_links)}")

        for link in property_links[:5]:
            href = await link.get_attribute("href")
            print(f"   - {href}")

        await browser.close()

        print("\n" + "=" * 60)
        print("Exploracao concluida!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(explore_site())
