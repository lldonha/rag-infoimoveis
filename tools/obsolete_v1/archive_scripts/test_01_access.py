#!/usr/bin/env python3
"""
Etapa 0.1: Teste de Acesso ao Site
==================================
Objetivo: Descobrir método de acesso que funciona para infoimoveis.com.br

Testes:
1. Requests simples (provavelmente 403)
2. Requests com headers de browser
3. Playwright com browser real
"""

import asyncio
import httpx
from playwright.async_api import async_playwright
from rich.console import Console
from rich.table import Table

console = Console()

BASE_URL = "https://www.infoimoveis.com.br"
TEST_URLS = [
    f"{BASE_URL}",  # Página inicial
    f"{BASE_URL}/imoveis/venda/ms/campo-grande",  # Busca venda
    f"{BASE_URL}/imoveis/aluguel/ms/campo-grande",  # Busca aluguel
]

# Headers que simulam um browser real
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


async def test_simple_request(url: str) -> dict:
    """Teste 1: Request simples sem headers especiais"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            return {
                "method": "Simple Request",
                "url": url,
                "status": response.status_code,
                "success": response.status_code == 200,
                "content_length": len(response.text),
            }
    except Exception as e:
        return {
            "method": "Simple Request",
            "url": url,
            "status": "ERROR",
            "success": False,
            "error": str(e),
        }


async def test_browser_headers(url: str) -> dict:
    """Teste 2: Request com headers de browser"""
    try:
        async with httpx.AsyncClient(timeout=30.0, headers=BROWSER_HEADERS) as client:
            response = await client.get(url)
            return {
                "method": "Browser Headers",
                "url": url,
                "status": response.status_code,
                "success": response.status_code == 200,
                "content_length": len(response.text),
            }
    except Exception as e:
        return {
            "method": "Browser Headers",
            "url": url,
            "status": "ERROR",
            "success": False,
            "error": str(e),
        }


async def test_playwright(url: str) -> dict:
    """Teste 3: Playwright com browser real (headless)"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            page = await context.new_page()

            response = await page.goto(url, wait_until="networkidle", timeout=60000)

            # Aguardar conteúdo carregar
            await page.wait_for_timeout(2000)

            content = await page.content()
            title = await page.title()

            await browser.close()

            return {
                "method": "Playwright",
                "url": url,
                "status": response.status if response else "NO_RESPONSE",
                "success": response.status == 200 if response else False,
                "content_length": len(content),
                "title": title,
            }
    except Exception as e:
        return {
            "method": "Playwright",
            "url": url,
            "status": "ERROR",
            "success": False,
            "error": str(e),
        }


async def run_all_tests():
    """Executa todos os testes e exibe resultados"""
    console.print("\n[bold blue]Teste de Acesso ao Site InfoImoveis[/bold blue]\n")

    results = []

    for url in TEST_URLS:
        console.print(f"\n[yellow]Testando: {url}[/yellow]")

        # Executa os 3 métodos
        r1 = await test_simple_request(url)
        results.append(r1)
        console.print(f"  Simple Request: {r1['status']}")

        r2 = await test_browser_headers(url)
        results.append(r2)
        console.print(f"  Browser Headers: {r2['status']}")

        r3 = await test_playwright(url)
        results.append(r3)
        console.print(f"  Playwright: {r3['status']}")

    # Tabela de resultados
    table = Table(title="\nResultados dos Testes")
    table.add_column("Metodo", style="cyan")
    table.add_column("URL", style="dim")
    table.add_column("Status", style="magenta")
    table.add_column("Sucesso", style="green")
    table.add_column("Tamanho", style="yellow")

    for r in results:
        success_icon = "[OK]" if r.get("success") else "[FAIL]"
        url_short = r["url"].replace(BASE_URL, "~")
        size = r.get("content_length", r.get("error", "N/A"))
        table.add_row(
            r["method"],
            url_short,
            str(r["status"]),
            success_icon,
            str(size)
        )

    console.print(table)

    # Análise
    playwright_success = any(r["success"] for r in results if r["method"] == "Playwright")
    headers_success = any(r["success"] for r in results if r["method"] == "Browser Headers")
    simple_success = any(r["success"] for r in results if r["method"] == "Simple Request")

    console.print("\n[bold]Conclusoes:[/bold]")
    if playwright_success:
        console.print("[green][OK] Playwright funciona - usar browser automation[/green]")
    elif headers_success:
        console.print("[yellow][!] Headers de browser funcionam - pode usar requests[/yellow]")
    elif simple_success:
        console.print("[green][OK] Requests simples funcionam[/green]")
    else:
        console.print("[red][FAIL] Nenhum metodo funcionou - verificar protecoes adicionais[/red]")

    return results


if __name__ == "__main__":
    asyncio.run(run_all_tests())
