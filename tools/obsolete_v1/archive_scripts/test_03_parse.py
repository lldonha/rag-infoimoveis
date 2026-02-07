#!/usr/bin/env python3
"""
Etapa 0.3: Parsing de dados de imoveis
======================================
Extrair dados estruturados do HTML de paginas de imoveis
"""

import asyncio
import json
import re
from dataclasses import dataclass, asdict
from typing import Optional, List
from playwright.async_api import async_playwright

BASE_URL = "https://www.infoimoveis.com.br"


@dataclass
class PropertyData:
    """Dados estruturados de um imovel"""
    source_url: str
    title: Optional[str] = None
    description: Optional[str] = None

    # Tipo e finalidade
    property_type: Optional[str] = None
    transaction_type: Optional[str] = None  # venda/aluguel

    # Localizacao
    neighborhood: Optional[str] = None
    city: str = "Campo Grande"
    state: str = "MS"
    address: Optional[str] = None

    # Caracteristicas
    area_total_m2: Optional[float] = None
    area_built_m2: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    suites: Optional[int] = None
    parking_spaces: Optional[int] = None

    # Precos
    price_brl: Optional[float] = None
    price_per_m2: Optional[float] = None
    condominium_fee_brl: Optional[float] = None

    # Extras
    features: Optional[List[str]] = None
    images: Optional[List[str]] = None
    advertiser_name: Optional[str] = None
    advertiser_phone: Optional[str] = None


def parse_price(text: str) -> Optional[float]:
    """Converte texto de preco para float"""
    if not text:
        return None
    # Remover R$, pontos de milhar, trocar virgula por ponto
    clean = re.sub(r'[R$\s.]', '', text)
    clean = clean.replace(',', '.')
    try:
        return float(clean)
    except ValueError:
        return None


def parse_area(text: str) -> Optional[float]:
    """Converte texto de area para float"""
    if not text:
        return None
    # Extrair numero antes de m2 ou m²
    match = re.search(r'([\d.,]+)\s*m', text, re.IGNORECASE)
    if match:
        num = match.group(1).replace('.', '').replace(',', '.')
        try:
            return float(num)
        except ValueError:
            return None
    return None


def parse_int_from_text(text: str) -> Optional[int]:
    """Extrai primeiro numero inteiro do texto"""
    if not text:
        return None
    match = re.search(r'(\d+)', text)
    if match:
        return int(match.group(1))
    return None


async def parse_property_page(page, url: str) -> PropertyData:
    """Extrai dados de uma pagina de imovel"""
    data = PropertyData(source_url=url)

    # Extrair tipo e finalidade da URL
    # Padrao: /imovel/{finalidade}-{tipo}-{bairro}/{id}
    url_match = re.search(r'/imovel/([^/]+)/(\d+)', url)
    if url_match:
        slug = url_match.group(1)
        parts = slug.split('-')
        if parts:
            if parts[0] in ['venda', 'aluguel']:
                data.transaction_type = parts[0]

    # 1. Extrair dados do JSON-LD (mais confiavel)
    try:
        json_ld_elem = await page.query_selector('script[type="application/ld+json"]')
        if json_ld_elem:
            json_text = await json_ld_elem.text_content()
            json_data = json.loads(json_text)

            data.title = json_data.get("name")
            data.description = json_data.get("description")

            # Preco do offers
            offers = json_data.get("offers", [])
            if offers and len(offers) > 0:
                price_str = offers[0].get("price")
                if price_str:
                    data.price_brl = float(price_str)

            # Imagem
            img = json_data.get("image")
            if img:
                data.images = [img] if isinstance(img, str) else img
    except Exception:
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
                # "Campo Grande - MS"
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

    # 3. Fallback: titulo do h1 se nao veio do JSON-LD
    if not data.title:
        h1 = await page.query_selector("h1")
        if h1:
            data.title = (await h1.text_content() or "").strip()

    # 4. Descricao fallback (se nao veio do JSON-LD)
    if not data.description:
        desc = await page.query_selector("[class*='descricao'], .texto-descricao, .texto")
        if desc:
            data.description = (await desc.text_content() or "").strip()

    # 5. Coletar mais imagens da galeria
    if not data.images or len(data.images) < 2:
        images = data.images or []
        img_elems = await page.query_selector_all("img[src*='imoveis'], img[data-src*='imoveis']")
        for img in img_elems[:20]:
            src = await img.get_attribute("src") or await img.get_attribute("data-src")
            if src and "stored/imoveis" in src and src not in images:
                images.append(src)
        data.images = images if images else None

    # 6. Anunciante
    anunciante_elem = await page.query_selector("[class*='anunciante'], [class*='corretor'], .nome-anunciante")
    if anunciante_elem:
        data.advertiser_name = (await anunciante_elem.text_content() or "").strip()

    # Calcular preco por m2
    if data.price_brl and data.area_total_m2:
        data.price_per_m2 = round(data.price_brl / data.area_total_m2, 2)

    return data


async def test_parsing():
    """Testa parsing de imoveis"""
    print("=" * 60)
    print("Teste de Parsing de Imoveis")
    print("=" * 60)

    # Carregar URLs salvas
    try:
        with open(".tmp/property_urls.json", "r") as f:
            urls = json.load(f)
    except FileNotFoundError:
        print("Arquivo .tmp/property_urls.json nao encontrado!")
        print("Execute test_02b_direct_search.py primeiro")
        return

    print(f"URLs disponiveis: {len(urls)}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            locale="pt-BR",
        )

        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)

        page = await context.new_page()

        # Passar pelo Cloudflare
        print("\n1. Passando pelo Cloudflare...")
        await page.goto(BASE_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(20000)

        # Testar parsing de alguns imoveis
        results = []
        test_urls = urls[:5]  # Testar com 5 imoveis

        for i, url in enumerate(test_urls, 1):
            print(f"\n{i}. Parsing: {url.split('/')[-2]}...")

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)

                # Salvar HTML para debug
                content = await page.content()
                with open(f".tmp/property_{i}.html", "w", encoding="utf-8") as f:
                    f.write(content)

                # Screenshot
                await page.screenshot(path=f".tmp/property_{i}.png", full_page=False)

                # Parsing
                data = await parse_property_page(page, url)
                results.append(asdict(data))

                # Mostrar dados extraidos
                print(f"   Titulo: {data.title[:50] if data.title else 'N/A'}...")
                print(f"   Tipo: {data.property_type}")
                print(f"   Transacao: {data.transaction_type}")
                print(f"   Preco: R$ {data.price_brl:,.2f}" if data.price_brl else "   Preco: N/A")
                print(f"   Area: {data.area_total_m2} m2" if data.area_total_m2 else "   Area: N/A")
                print(f"   Quartos: {data.bedrooms}" if data.bedrooms else "   Quartos: N/A")
                print(f"   Imagens: {len(data.images or [])}")

            except Exception as e:
                print(f"   ERRO: {e}")

        # Salvar resultados
        with open(".tmp/parsed_properties.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n\nResultados salvos em .tmp/parsed_properties.json")
        print(f"Imoveis parseados: {len(results)}")

        print("\n   Browser fechando...")
        await page.wait_for_timeout(3000)
        await browser.close()

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_parsing())
