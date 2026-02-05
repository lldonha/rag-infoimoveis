#!/usr/bin/env python3
"""
Scrape Workflow - Orquestrador de Scraping
==========================================
Workflow completo: discovery → scraping → armazenamento
"""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict
from playwright.async_api import async_playwright, Page

import sys
sys.path.append(os.path.dirname(__file__))

from rate_limiter import SmartRateLimiter, is_safe_window, wait_for_safe_window
from cookie_manager import load_cookies, save_cookies, apply_cookies
from fingerprint_rotator import get_random_fingerprint, get_anti_detection_script
from human_behavior import wait_for_page_load, human_scroll
from property_saver import insert_property, get_property_stats


BASE_URL = "https://www.infoimoveis.com.br"
SEARCH_URL = f"{BASE_URL}/busca?cidade=campo-grande&uf=ms&tipo=todos&transacao=venda"


async def discover_property_urls(
    playwright,
    search_url: str,
    max_pages: int = 3,
    rate_limiter: SmartRateLimiter = None
) -> List[str]:
    """
    Fase 1: Discovery - Coleta URLs de imóveis das páginas de busca

    Args:
        playwright: Instância do Playwright
        search_url: URL de busca
        max_pages: Máximo de páginas a navegar
        rate_limiter: Rate limiter (opcional)

    Returns:
        Lista de URLs de imóveis descobertas
    """
    print(f"\n{'='*60}")
    print(f"FASE 1: DISCOVERY")
    print(f"{'='*60}")

    if not rate_limiter:
        rate_limiter = SmartRateLimiter(max_per_hour=50, max_per_day=400)

    # Verificar janela segura
    if not is_safe_window():
        wait_for_safe_window()

    fingerprint = get_random_fingerprint()

    browser = await playwright.chromium.launch(
        headless=False,
        args=['--disable-blink-features=AutomationControlled']
    )

    context = await browser.new_context(
        user_agent=fingerprint['user_agent'],
        viewport=fingerprint['viewport'],
        locale=fingerprint['locale'],
        timezone_id=fingerprint['timezone']
    )

    await context.add_init_script(get_anti_detection_script())

    # Aplicar cookies
    cookies = load_cookies()
    if cookies:
        apply_cookies(context, cookies)

    page = await context.new_page()

    all_urls = []

    try:
        # Navegar pela busca
        for page_num in range(1, max_pages + 1):
            print(f"\n[Página {page_num}/{max_pages}]")

            rate_limiter.wait_if_needed()

            current_url = f"{search_url}&pagina={page_num}" if page_num > 1 else search_url

            await page.goto(current_url, wait_until="domcontentloaded", timeout=30000)
            await wait_for_page_load(page, 3, 5)

            # Scroll para carregar lazy loading
            await human_scroll(page)

            # Extrair URLs de imóveis
            links = await page.query_selector_all("a[href*='/imovel/']")

            page_urls = []
            for link in links:
                href = await link.get_attribute("href")
                if href and "/imovel/" in href:
                    full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
                    if full_url not in all_urls and full_url not in page_urls:
                        page_urls.append(full_url)

            print(f"   Encontradas: {len(page_urls)} URLs")
            all_urls.extend(page_urls)

        # Salvar cookies
        if not cookies:
            new_cookies = await context.cookies()
            save_cookies(new_cookies, metadata=fingerprint)

    except Exception as e:
        print(f"❌ Erro no discovery: {e}")

    finally:
        await browser.close()

    # Salvar URLs descobertas
    os.makedirs('.tmp', exist_ok=True)
    with open('.tmp/discovered_urls.json', 'w', encoding='utf-8') as f:
        json.dump(all_urls, f, indent=2)

    print(f"\n✅ Discovery completo: {len(all_urls)} URLs descobertas")
    return all_urls


async def scrape_from_url_list(
    urls: List[str],
    max_properties: int = None,
    save_to_db: bool = True
) -> Dict:
    """
    Fase 2: Scraping - Processa lista de URLs

    Args:
        urls: Lista de URLs de imóveis
        max_properties: Máximo de imóveis a processar
        save_to_db: Salvar no banco

    Returns:
        Dict com estatísticas
    """
    print(f"\n{'='*60}")
    print(f"FASE 2: SCRAPING")
    print(f"{'='*60}")

    from scraper_production import scrape_multiple_properties

    if max_properties:
        urls = urls[:max_properties]

    stats = await scrape_multiple_properties(urls, save_to_db=save_to_db)
    return stats


async def full_workflow(
    search_url: str = SEARCH_URL,
    max_discovery_pages: int = 3,
    max_properties: int = 50,
    save_to_db: bool = True
) -> Dict:
    """
    Workflow completo: Discovery → Scraping → Stats

    Args:
        search_url: URL de busca
        max_discovery_pages: Máximo de páginas de busca
        max_properties: Máximo de imóveis a processar
        save_to_db: Salvar no banco

    Returns:
        Dict com estatísticas finais
    """
    print("=" * 60)
    print("WORKFLOW COMPLETO DE SCRAPING")
    print("=" * 60)

    start_time = datetime.now()

    # Fase 1: Discovery
    async with async_playwright() as p:
        urls = await discover_property_urls(
            p, search_url,
            max_pages=max_discovery_pages
        )

    if not urls:
        print("❌ Nenhuma URL descoberta!")
        return {'error': 'No URLs discovered'}

    # Fase 2: Scraping
    scrape_stats = await scrape_from_url_list(
        urls,
        max_properties=max_properties,
        save_to_db=save_to_db
    )

    # Fase 3: Estatísticas finais
    if save_to_db:
        db_stats = get_property_stats()
    else:
        db_stats = {}

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    final_stats = {
        'workflow': {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
        },
        'discovery': {
            'urls_found': len(urls),
            'pages_scraped': max_discovery_pages,
        },
        'scraping': scrape_stats,
        'database': db_stats,
    }

    # Salvar relatório
    os.makedirs('.tmp', exist_ok=True)
    with open('.tmp/workflow_report.json', 'w', encoding='utf-8') as f:
        json.dump(final_stats, f, indent=2, ensure_ascii=False)

    # Resumo
    print(f"\n{'='*60}")
    print(f"RESUMO DO WORKFLOW")
    print(f"{'='*60}")
    print(f"Duração: {duration/60:.1f} minutos")
    print(f"URLs descobertas: {len(urls)}")
    print(f"Imóveis processados: {scrape_stats.get('success', 0)}/{scrape_stats.get('total', 0)}")
    if save_to_db:
        print(f"Total no banco: {db_stats.get('total', 0)} imóveis")
        print(f"Completude média: {db_stats.get('avg_completeness', 0):.1%}")

    return final_stats


async def incremental_update():
    """
    Atualização incremental: apenas novos imóveis ou atualizações

    Estratégia:
    1. Busca última data de scraping
    2. Processa apenas imóveis novos/alterados
    3. Mais eficiente para uso diário
    """
    print("=" * 60)
    print("ATUALIZAÇÃO INCREMENTAL")
    print("=" * 60)

    # TODO: Implementar lógica incremental
    # - Verificar imóveis já no banco
    # - Comparar datas de modificação
    # - Scrape apenas delta

    print("⚠️  Função incremental ainda não implementada")
    print("Use full_workflow() para scraping completo")


async def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Workflow de Scraping InfoImóveis')
    parser.add_argument('--mode', choices=['full', 'incremental', 'discovery', 'scrape'],
                      default='full', help='Modo de execução')
    parser.add_argument('--max-pages', type=int, default=3,
                      help='Máximo de páginas de busca (discovery)')
    parser.add_argument('--max-properties', type=int, default=50,
                      help='Máximo de imóveis a processar')
    parser.add_argument('--no-db', action='store_true',
                      help='Não salvar no banco (apenas arquivos)')

    args = parser.parse_args()

    if args.mode == 'full':
        await full_workflow(
            max_discovery_pages=args.max_pages,
            max_properties=args.max_properties,
            save_to_db=not args.no_db
        )

    elif args.mode == 'discovery':
        async with async_playwright() as p:
            urls = await discover_property_urls(
                p, SEARCH_URL,
                max_pages=args.max_pages
            )
        print(f"\nURLs salvas em .tmp/discovered_urls.json")

    elif args.mode == 'scrape':
        try:
            with open('.tmp/discovered_urls.json', 'r') as f:
                urls = json.load(f)
        except FileNotFoundError:
            print("❌ Arquivo .tmp/discovered_urls.json não encontrado!")
            print("Execute com --mode discovery primeiro")
            return

        await scrape_from_url_list(
            urls,
            max_properties=args.max_properties,
            save_to_db=not args.no_db
        )

    elif args.mode == 'incremental':
        await incremental_update()


if __name__ == "__main__":
    asyncio.run(main())
