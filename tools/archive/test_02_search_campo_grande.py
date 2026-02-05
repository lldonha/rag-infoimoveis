#!/usr/bin/env python3
"""
Etapa 0.2: Buscar imoveis em Campo Grande - MS
==============================================
Navegar pela busca e coletar URLs de imoveis
"""

import asyncio
import json
import re
from playwright.async_api import async_playwright

BASE_URL = "https://www.infoimoveis.com.br"


async def search_campo_grande():
    """Busca imoveis em Campo Grande - MS"""
    print("=" * 60)
    print("Buscando Imoveis em Campo Grande - MS")
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

        # 1. Acessar home e passar pelo Cloudflare
        print("\n1. Acessando home...")
        await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
        print("   Aguardando Cloudflare (20s)...")
        await page.wait_for_timeout(20000)

        title = await page.title()
        print(f"   Titulo: {title[:50]}")

        if "moment" in title.lower():
            print("   [!] Cloudflare ainda ativo, aguardando mais...")
            await page.wait_for_timeout(15000)

        # 2. Ir para busca detalhada
        print("\n2. Navegando para busca detalhada...")
        busca_link = await page.query_selector("a[href*='buscadetalhada']")
        if busca_link:
            await busca_link.click()
            await page.wait_for_timeout(5000)
        else:
            print("   Link nao encontrado, tentando URL direta...")
            await page.goto(f"{BASE_URL}/buscadetalhada/", wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)

        title = await page.title()
        print(f"   Titulo: {title[:50]}")

        # 3. Analisar formulario de busca
        print("\n3. Analisando formulario de busca...")

        # Screenshot para debug
        await page.screenshot(path=".tmp/search_form.png", full_page=True)

        # Listar todos os selects
        selects = await page.query_selector_all("select")
        print(f"   Selects encontrados: {len(selects)}")

        for sel in selects:
            sel_id = await sel.get_attribute("id")
            sel_name = await sel.get_attribute("name")
            print(f"   - id={sel_id}, name={sel_name}")

        # 4. Selecionar finalidade, estado e cidade
        print("\n4. Selecionando filtros...")

        # 4.1 Selecionar finalidade (venda)
        finalidade_sel = await page.query_selector("select#finalidade-detalha, select[name='finalidade']")
        if finalidade_sel:
            print("   Select de finalidade encontrado!")
            options = await finalidade_sel.query_selector_all("option")
            for opt in options:
                value = await opt.get_attribute("value")
                text = await opt.text_content()
                if value and ("venda" in value.lower() or "venda" in (text or "").lower()):
                    print(f"   [OK] Encontrado: value={value}")
                    await finalidade_sel.select_option(value=value)
                    print("   Venda selecionada!")
                    await page.wait_for_timeout(2000)
                    break

        # 4.2 Procurar select de estado
        estado_sel = await page.query_selector("select#uf, select#estado, select[name='uf'], select[name='estado']")
        if estado_sel:
            print("   Select de estado encontrado!")

            # Listar opcoes
            options = await estado_sel.query_selector_all("option")
            for opt in options:
                value = await opt.get_attribute("value")
                text = await opt.text_content()
                if text and ("mato grosso" in text.lower() or value == "MS"):
                    print(f"   [OK] Encontrado: value={value}, text={text.strip()}")
                    # Selecionar MS
                    await estado_sel.select_option(value=value)
                    print("   MS selecionado!")
                    await page.wait_for_timeout(3000)
                    break

        # Procurar select de cidade apos selecionar estado
        cidade_sel = await page.query_selector("select#cidade, select[name='cidade']")
        if cidade_sel:
            print("   Select de cidade encontrado!")
            await page.wait_for_timeout(2000)

            # Listar opcoes
            options = await cidade_sel.query_selector_all("option")
            print(f"   Opcoes de cidade: {len(options)}")

            for opt in options[:30]:
                value = await opt.get_attribute("value")
                text = await opt.text_content()
                if text and "campo grande" in text.lower():
                    print(f"   [OK] Encontrado: value={value}, text={text.strip()}")
                    await cidade_sel.select_option(value=value)
                    print("   Campo Grande selecionado!")
                    await page.wait_for_timeout(2000)
                    break

        # 5. Clicar no botao de buscar
        print("\n5. Executando busca...")

        # Procurar botao de busca
        buscar_btn = await page.query_selector("button[type='submit'], input[type='submit'], button:has-text('Buscar'), button:has-text('Pesquisar')")
        if buscar_btn:
            await buscar_btn.click()
            print("   Busca iniciada!")
            await page.wait_for_timeout(5000)
        else:
            # Tentar submeter o form
            form = await page.query_selector("form")
            if form:
                await form.evaluate("form => form.submit()")
                print("   Form submetido!")
                await page.wait_for_timeout(5000)

        # 6. Coletar resultados
        print("\n6. Coletando resultados...")

        title = await page.title()
        print(f"   Titulo apos busca: {title[:60]}")

        await page.screenshot(path=".tmp/search_results.png", full_page=True)

        # Salvar HTML
        content = await page.content()
        with open(".tmp/search_results.html", "w", encoding="utf-8") as f:
            f.write(content)

        # Coletar links de imoveis
        property_links = await page.query_selector_all("a[href*='/imovel/']")
        print(f"   Links de imoveis encontrados: {len(property_links)}")

        urls = set()
        for link in property_links:
            href = await link.get_attribute("href")
            if href and "/imovel/" in href:
                # Normalizar URL
                if not href.startswith("http"):
                    href = BASE_URL + href
                urls.add(href)

        print(f"   URLs unicas: {len(urls)}")

        # Salvar URLs
        urls_list = sorted(urls)
        with open(".tmp/property_urls.json", "w") as f:
            json.dump(urls_list, f, indent=2)

        print("\n   Exemplos de URLs:")
        for url in urls_list[:10]:
            print(f"   - {url}")

        # 7. Verificar paginacao
        print("\n7. Verificando paginacao...")
        pagination = await page.query_selector("[class*='paginacao'], [class*='pagination'], nav.pagination")
        if pagination:
            print("   Paginacao encontrada!")
            page_links = await pagination.query_selector_all("a")
            print(f"   Paginas: {len(page_links)}")
        else:
            print("   Paginacao nao encontrada")

        # Salvar cookies
        cookies = await context.cookies()
        with open(".tmp/cookies.json", "w") as f:
            json.dump(cookies, f, indent=2)

        print("\n   Browser fechando em 5 segundos...")
        await page.wait_for_timeout(5000)
        await browser.close()

    print("\n" + "=" * 60)
    print(f"URLs coletadas: {len(urls)}")
    print("Salvas em .tmp/property_urls.json")
    print("=" * 60)

    return urls_list


if __name__ == "__main__":
    asyncio.run(search_campo_grande())
