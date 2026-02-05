#!/usr/bin/env python3
"""
Production Scraper - InfoImóveis
================================
Scraper robusto com todas as proteções anti-bloqueio
"""

import asyncio
import json
import os
import re
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
from datetime import datetime
from playwright.async_api import async_playwright, Page

# Importar módulos de proteção
import sys
sys.path.append(os.path.dirname(__file__))

from rate_limiter import SmartRateLimiter, is_safe_window, wait_for_safe_window
from cookie_manager import save_cookies, load_cookies, apply_cookies, get_cookie_info
from fingerprint_rotator import get_random_fingerprint, get_anti_detection_script
from human_behavior import (
    human_scroll, human_mouse_move, random_pause,
    simulate_reading, wait_for_page_load
)
from property_saver import insert_property, bulk_insert_properties, get_property_stats


BASE_URL = "https://www.infoimoveis.com.br"


@dataclass
class PropertyData:
    """Dados estruturados de um imóvel"""
    source_url: str
    title: Optional[str] = None
    description: Optional[str] = None
    property_type: Optional[str] = None
    property_use: Optional[str] = None
    transaction_type: Optional[str] = None
    neighborhood: Optional[str] = None
    city: str = "Campo Grande"
    state: str = "MS"
    address: Optional[str] = None
    area_total_m2: Optional[float] = None
    area_built_m2: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    suites: Optional[int] = None
    parking_spaces: Optional[int] = None
    price_brl: Optional[float] = None
    price_per_m2: Optional[float] = None
    condominium_fee_brl: Optional[float] = None
    iptu_annual_brl: Optional[float] = None
    features: Optional[List[str]] = None
    images: Optional[List[str]] = None
    advertiser_name: Optional[str] = None
    advertiser_phone: Optional[str] = None


def parse_price(text: str) -> Optional[float]:
    """Converte texto de preço para float"""
    if not text:
        return None
    clean = re.sub(r'[R$\s.]', '', text)
    clean = clean.replace(',', '.')
    try:
        return float(clean)
    except ValueError:
        return None


def parse_area(text: str) -> Optional[float]:
    """Converte texto de área para float"""
    if not text:
        return None
    match = re.search(r'([\d.,]+)\s*m', text, re.IGNORECASE)
    if match:
        num = match.group(1).replace('.', '').replace(',', '.')
        try:
            return float(num)
        except ValueError:
            return None
    return None


def parse_int_from_text(text: str) -> Optional[int]:
    """Extrai primeiro número inteiro do texto"""
    if not text:
        return None
    match = re.search(r'(\d+)', text)
    if match:
        return int(match.group(1))
    return None


def is_blocked(content: str) -> bool:
    """Detecta se fomos bloqueados pelo Cloudflare"""
    blocked_indicators = [
        'Access Denied',
        'Attention Required',
        'Cloudflare',
        'Just a moment',
        'Please verify you are a human',
        'Ray ID:',
        '<title>403',
        'checking your browser',
    ]

    content_lower = content.lower()
    for indicator in blocked_indicators:
        if indicator.lower() in content_lower:
            return True
    return False


async def parse_property_page(page: Page, url: str) -> PropertyData:
    """Extrai dados de uma página de imóvel"""
    data = PropertyData(source_url=url)

    # Extrair tipo e finalidade da URL
    url_match = re.search(r'/imovel/([^/]+)/(\d+)', url)
    if url_match:
        slug = url_match.group(1)
        parts = slug.split('-')
        if parts:
            if parts[0] in ['venda', 'aluguel']:
                data.transaction_type = parts[0]

    # 1. Extrair dados do JSON-LD (mais confiável)
    try:
        json_ld_elem = await page.query_selector('script[type="application/ld+json"]')
        if json_ld_elem:
            json_text = await json_ld_elem.text_content()
            json_data = json.loads(json_text)

            data.title = json_data.get("name")
            data.description = json_data.get("description")

            # Preço
            offers = json_data.get("offers", [])
            if offers and len(offers) > 0:
                price_str = offers[0].get("price")
                if price_str:
                    data.price_brl = float(price_str)

            # Imagens
            img = json_data.get("image")
            if img:
                data.images = [img] if isinstance(img, str) else img
    except:
        pass

    # 2. Extrair dados da tabela HTML
    rows = await page.query_selector_all("tr")
    for row in rows:
        cells = await row.query_selector_all("td")
        if len(cells) >= 2:
            label = (await cells[0].text_content() or "").strip().lower()
            value = (await cells[1].text_content() or "").strip()

            if "tipo" in label:
                data.property_type = value
            elif "bairro" in label:
                data.neighborhood = value
            elif "cidade" in label or "uf" in label:
                parts = value.split('-')
                if parts:
                    data.city = parts[0].strip()
                    if len(parts) > 1:
                        data.state = parts[1].strip()
            elif "endere" in label:
                data.address = value
            elif "constru" in label and "rea" in label:
                data.area_built_m2 = parse_area(value)
            elif "total" in label and "rea" in label:
                data.area_total_m2 = parse_area(value)
            elif "terreno" in label:
                if not data.area_total_m2:
                    data.area_total_m2 = parse_area(value)
            elif "quarto" in label or "dormit" in label:
                data.bedrooms = parse_int_from_text(value)
            elif "banheiro" in label:
                data.bathrooms = parse_int_from_text(value)
            elif "su" in label and "te" in label:
                data.suites = parse_int_from_text(value)
            elif "vaga" in label or "garagem" in label:
                data.parking_spaces = parse_int_from_text(value)
            elif "condom" in label and "nio" in label:
                data.condominium_fee_brl = parse_price(value)

    # 3. Fallbacks
    if not data.title:
        h1 = await page.query_selector("h1")
        if h1:
            data.title = (await h1.text_content() or "").strip()

    if not data.description:
        desc = await page.query_selector("[class*='descricao'], .texto-descricao, .texto")
        if desc:
            data.description = (await desc.text_content() or "").strip()

    # 4. Coletar mais imagens
    if not data.images or len(data.images) < 2:
        images = data.images or []
        img_elems = await page.query_selector_all("img[src*='imoveis'], img[data-src*='imoveis']")
        for img in img_elems[:20]:
            src = await img.get_attribute("src") or await img.get_attribute("data-src")
            if src and "stored/imoveis" in src and src not in images:
                images.append(src)
        data.images = images if images else None

    # 5. Calcular preço por m2
    if data.price_brl and data.area_total_m2:
        data.price_per_m2 = round(data.price_brl / data.area_total_m2, 2)

    return data


async def scrape_property_safe(
    playwright,
    url: str,
    rate_limiter: SmartRateLimiter,
    use_cookies: bool = True,
    save_to_db: bool = True
) -> Optional[Dict]:
    """
    Scrape de um imóvel com TODAS as proteções

    Args:
        playwright: Instância do Playwright
        url: URL do imóvel
        rate_limiter: Instância do SmartRateLimiter
        use_cookies: Se True, tenta usar cookies salvos
        save_to_db: Se True, salva no PostgreSQL

    Returns:
        Dict com dados do imóvel ou None se erro
    """
    print(f"\n{'='*60}")
    print(f"Scraping: {url}")
    print(f"{'='*60}")

    # 1. Verificar janela segura
    if not is_safe_window():
        print("⚠️  Fora da janela segura!")
        wait_for_safe_window()

    # 2. Rate limiting
    rate_limiter.wait_if_needed()

    # 3. Gerar fingerprint aleatório
    fingerprint = get_random_fingerprint()
    print(f"🎭 Fingerprint: {fingerprint['viewport']['width']}x{fingerprint['viewport']['height']}")

    try:
        # 4. Criar browser com fingerprint
        browser = await playwright.chromium.launch(
            headless=False,  # CRÍTICO: headed mode
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )

        context = await browser.new_context(
            user_agent=fingerprint['user_agent'],
            viewport=fingerprint['viewport'],
            locale=fingerprint['locale'],
            timezone_id=fingerprint['timezone']
        )

        # Script anti-detecção
        await context.add_init_script(get_anti_detection_script())

        # 5. Aplicar cookies se disponível
        cookies = None
        if use_cookies:
            cookies = load_cookies()
            if cookies:
                apply_cookies(context, cookies)

        page = await context.new_page()

        # 6. Acessar página
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        wait_for_page_load(page, 3, 6)

        # 7. Verificar bloqueio
        content = await page.content()
        if is_blocked(content):
            print("🚨 BLOQUEIO DETECTADO!")
            await browser.close()
            return None

        # 8. Comportamento humano
        human_scroll(page)
        human_mouse_move(page)
        simulate_reading(page, min_time=3, max_time=6)

        # 9. Extrair dados
        data = await parse_property_page(page, url)
        data_dict = asdict(data)

        # 10. Salvar cookies (se novos)
        if not cookies:
            new_cookies = await context.cookies()
            save_cookies(new_cookies, metadata=fingerprint)

        # 11. Pausa ocasional
        random_pause(probability=0.1)

        await browser.close()

        # 12. Salvar no banco
        if save_to_db:
            property_id = insert_property(data_dict)
            data_dict['db_id'] = property_id

        print(f"✅ Scraping completo: {data.title[:50] if data.title else 'N/A'}...")
        return data_dict

    except Exception as e:
        print(f"❌ Erro no scraping: {e}")
        try:
            await browser.close()
        except:
            pass
        return None


async def scrape_multiple_properties(
    urls: List[str],
    max_per_session: int = 50,
    save_to_db: bool = True
) -> Dict:
    """
    Scrape múltiplos imóveis com proteções

    Args:
        urls: Lista de URLs
        max_per_session: Máximo por sessão (padrão: 50/hora)
        save_to_db: Salvar no banco

    Returns:
        Dict com estatísticas
    """
    stats = {
        'total': len(urls),
        'success': 0,
        'errors': 0,
        'blocked': 0,
        'start_time': datetime.now().isoformat(),
    }

    # Limitar URLs
    urls = urls[:max_per_session]

    rate_limiter = SmartRateLimiter(
        max_per_hour=50,
        max_per_day=400,
        min_delay=5,
        max_delay=12
    )

    async with async_playwright() as p:
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Processando...")

            result = await scrape_property_safe(
                p, url, rate_limiter,
                use_cookies=True,
                save_to_db=save_to_db
            )

            if result:
                stats['success'] += 1
            else:
                stats['errors'] += 1

    stats['end_time'] = datetime.now().isoformat()
    return stats


async def main():
    """Função principal"""
    print("=" * 60)
    print("Production Scraper - InfoImóveis")
    print("=" * 60)

    # Verificar cookies
    cookie_info = get_cookie_info()
    if cookie_info:
        print(f"\n🍪 Cookies disponíveis: {cookie_info['count']} (idade: {cookie_info['age_hours']:.1f}h)")
    else:
        print(f"\n⚠️  Nenhum cookie disponível - será necessário bypass Cloudflare")

    # Carregar URLs de teste
    try:
        with open(".tmp/property_urls.json", "r") as f:
            urls = json.load(f)
        print(f"\n📋 URLs carregadas: {len(urls)}")
    except FileNotFoundError:
        print("\n❌ Arquivo .tmp/property_urls.json não encontrado!")
        print("Execute test_02b_direct_search.py primeiro")
        return

    # Limitar a 5 para teste
    test_urls = urls[:5]
    print(f"\n🎯 Testando com {len(test_urls)} imóveis")

    # Scraping
    stats = await scrape_multiple_properties(test_urls, save_to_db=True)

    # Resultado
    print(f"\n{'='*60}")
    print(f"Resultado do Scraping:")
    print(f"{'='*60}")
    print(f"Total processado: {stats['total']}")
    print(f"Sucessos: {stats['success']}")
    print(f"Erros: {stats['errors']}")

    # Estatísticas do banco
    db_stats = get_property_stats()
    print(f"\n{'='*60}")
    print(f"Estatísticas do Banco:")
    print(f"{'='*60}")
    print(f"Total de imóveis: {db_stats['total']}")
    print(f"Completude média: {db_stats['avg_completeness']:.1%}")
    print(f"Por transação: {db_stats['by_transaction']}")
    print(f"Top 5 bairros: {list(db_stats['by_neighborhood'].items())[:5]}")


if __name__ == "__main__":
    asyncio.run(main())
