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
    """
    Extrai dados de uma página de imóvel (VERSÃO OTIMIZADA)

    Completude esperada: >70% (vs 15% versão antiga)
    Seletores baseados em mapeamento real da página
    """
    data = PropertyData(source_url=url)

    # === EXTRAIR DADOS DA TABELA PRINCIPAL ===
    try:
        # Tipo (Casa-Térrea, Apartamento, etc)
        tipo_elem = await page.locator('tr:has-text("Tipo") td:nth-child(2)').first.inner_text()
        data.property_type = tipo_elem.strip() if tipo_elem else None
    except:
        pass

    try:
        # Bairro
        bairro_elem = await page.locator('tr:has-text("Bairro") td:nth-child(2)').first.inner_text()
        data.neighborhood = bairro_elem.strip() if bairro_elem else None
    except:
        pass

    try:
        # Cidade/UF
        cidade_elem = await page.locator('tr:has-text("Cidade/UF") td:nth-child(2)').first.inner_text()
        if cidade_elem:
            parts = cidade_elem.strip().split('-')
            if parts:
                data.city = parts[0].strip()
                if len(parts) > 1:
                    data.state = parts[1].strip()
    except:
        pass

    try:
        # Endereço
        endereco_elem = await page.locator('tr:has-text("Endereço") td:nth-child(2)').first.inner_text()
        data.address = endereco_elem.strip() if endereco_elem else None
    except:
        pass

    try:
        # Área Total
        area_total_elem = await page.locator('tr:has-text("Área total") td:nth-child(2)').first.inner_text()
        data.area_total_m2 = parse_area(area_total_elem) if area_total_elem else None
    except:
        pass

    try:
        # Área Construída
        area_const_elem = await page.locator('tr:has-text("Área construída") td:nth-child(2)').first.inner_text()
        data.area_built_m2 = parse_area(area_const_elem) if area_const_elem else None
    except:
        pass

    try:
        # IPTU
        iptu_elem = await page.locator('tr:has-text("IPTU") td:nth-child(2)').first.inner_text()
        data.iptu_brl = parse_price(iptu_elem) if iptu_elem else None
    except:
        pass

    # === TÍTULO ===
    try:
        h1_elem = await page.locator('h1').first.inner_text()
        data.title = h1_elem.strip() if h1_elem else None
    except:
        pass

    # === PREÇO ===
    try:
        # Procurar por "VALOR TOTAL:" e pegar o valor
        preco_section = await page.locator('text=/VALOR TOTAL:/i').inner_text()
        if preco_section:
            # Regex para extrair preço: R$ 570.000,00
            match = re.search(r'R\$\s*([\d.]+,\d{2})', preco_section)
            if match:
                price_str = match.group(1).replace('.', '').replace(',', '.')
                data.price_brl = float(price_str)
    except:
        pass

    # === CARACTERÍSTICAS (LISTA .itens li) ===
    try:
        # Buscar todos os itens da lista
        items = await page.locator('.itens li').all()

        for item in items:
            text = await item.inner_text()
            text_lower = text.lower()

            # Quartos
            if 'quarto' in text_lower and not data.bedrooms:
                data.bedrooms = parse_int_from_text(text)

            # Suítes
            elif 'suíte' in text_lower or 'suite' in text_lower:
                data.suites = parse_int_from_text(text)

            # Banheiros (chamado "Wc social")
            elif 'wc social' in text_lower:
                data.bathrooms = parse_int_from_text(text)

            # Vagas
            elif 'vaga' in text_lower:
                data.parking_spaces = parse_int_from_text(text)
    except:
        pass

    # === DESCRIÇÃO ===
    try:
        desc_elem = await page.locator('.descricao .texto').first.inner_text()
        data.description = desc_elem.strip() if desc_elem else None
    except:
        pass

    # === OBSERVAÇÕES (adicionar à descrição) ===
    try:
        obs_elem = await page.locator('.observacoes .texto').first.inner_text()
        if obs_elem:
            obs_text = obs_elem.strip()
            if data.description:
                data.description = f"{data.description}\n\nObservações: {obs_text}"
            else:
                data.description = obs_text
    except:
        pass

    # === CARACTERÍSTICAS COMPLETAS (adicionar à descrição) ===
    try:
        items = await page.locator('.itens li').all()
        features = []
        for item in items:
            text = await item.inner_text()
            if text:
                features.append(text.strip())

        if features and data.description:
            features_text = "\n\nCaracterísticas:\n" + "\n".join(features)
            data.description = data.description + features_text
    except:
        pass

    # === IMAGENS ===
    try:
        # Tentar diferentes seletores para imagens
        img_selectors = [
            'img[src*="/fotos/"]',
            'img[src*="stored/imoveis"]',
            'img[data-src*="/fotos/"]',
            '.galeria img',
            '[class*="foto"] img'
        ]

        images = []
        for selector in img_selectors:
            img_elems = await page.locator(selector).all()
            for img in img_elems[:20]:  # Máximo 20 imagens
                src = await img.get_attribute('src') or await img.get_attribute('data-src')
                if src and src not in images:
                    # Garantir URL absoluta
                    if src.startswith('/'):
                        src = f"https://www.infoimoveis.com.br{src}"
                    images.append(src)

        data.images = images if images else None
    except:
        pass

    # === TRANSACTION TYPE (da URL) ===
    url_match = re.search(r'/imovel/([^/]+)/(\d+)', url)
    if url_match:
        slug = url_match.group(1)
        if 'venda' in slug:
            data.transaction_type = 'venda'
        elif 'aluguel' in slug:
            data.transaction_type = 'aluguel'

    # === CALCULAR PREÇO POR M² ===
    if data.price_brl and data.area_built_m2:
        data.price_per_m2 = round(data.price_brl / data.area_built_m2, 2)
    elif data.price_brl and data.area_total_m2:
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
        await wait_for_page_load(page, 3, 6)

        # 7. Verificar bloqueio
        content = await page.content()
        if is_blocked(content):
            print("🚨 BLOQUEIO DETECTADO!")
            await browser.close()
            return None

        # 8. Comportamento humano
        await human_scroll(page)
        await human_mouse_move(page)
        await simulate_reading(page, min_time=3, max_time=6)

        # 9. Extrair dados
        data = await parse_property_page(page, url)
        data_dict = asdict(data)

        # 10. Salvar cookies (se novos)
        if not cookies:
            new_cookies = await context.cookies()
            save_cookies(new_cookies, metadata=fingerprint)

        # 11. Pausa ocasional
        await random_pause(probability=0.1)

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
