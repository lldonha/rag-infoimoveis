"""
Discovery de URLs com Filtros - InfoImóveis

Busca imóveis por:
- Região/Bairro (ex: Segredo)
- Faixa de preço (min-max)
- Tipo (Casa Térrea, Apartamento, etc)
- Cidade (Campo Grande - MS)

Exemplo de URL de busca:
https://www.infoimoveis.com.br/busca/venda/casa-terrea/ms/campo-grande/regiao-segredo?valorde=100.000,00&valorate=200.000,00
"""
import asyncio
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlencode

# Importar stealth browser
sys.path.append(str(Path(__file__).parent))
from scraper_stealth import create_stealth_browser


# Mapeamento de tipos de imóveis
PROPERTY_TYPES = {
    'casa_terrea': 'casa-terrea',
    'casa_sobrado': 'casa-sobrado',
    'apartamento': 'apartamento',
    'terreno': 'terreno',
    'chacara': 'chacara',
    'comercial': 'comercial',
}

# Regiões de Campo Grande
REGIONS_CG = {
    'segredo': 'regiao-segredo',
    'centro': 'centro',
    'prosa': 'prosa',
    'bandeirantes': 'bandeirantes',
    'aero_rancho': 'aero-rancho',
    'jardim_dos_estados': 'jardim-dos-estados',
    'coronel_antonino': 'coronel-antonino',
}


def build_search_url(
    property_type: str = 'casa-terrea',
    city: str = 'campo-grande',
    state: str = 'ms',
    region: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    page: int = 1,
) -> str:
    """
    Constrói URL de busca do InfoImóveis

    Args:
        property_type: Tipo do imóvel (casa-terrea, apartamento, etc)
        city: Cidade (campo-grande)
        state: Estado (ms)
        region: Região/bairro (opcional)
        price_min: Preço mínimo (opcional)
        price_max: Preço máximo (opcional)
        page: Número da página (default 1)

    Returns:
        URL completa de busca

    Example:
        >>> build_search_url('casa-terrea', region='regiao-segredo', price_min=100000, price_max=200000)
        'https://www.infoimoveis.com.br/busca/venda/casa-terrea/ms/campo-grande/regiao-segredo?valorde=100.000,00&valorate=200.000,00'
    """
    # Base URL
    base = f"https://www.infoimoveis.com.br/busca/venda/{property_type}/{state}/{city}"

    # Adicionar região se fornecida
    if region:
        base += f"/{region}"

    # Query params
    params = {}

    if price_min:
        # Formatar como moeda brasileira: 100.000,00
        params['valorde'] = f"{price_min:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    if price_max:
        params['valorate'] = f"{price_max:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    if page > 1:
        params['pagina'] = str(page)

    # Montar URL final
    if params:
        return f"{base}?{urlencode(params)}"
    return base


async def discover_properties_filtered(
    property_type: str = 'casa-terrea',
    region: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    max_pages: int = 5,
    use_stealth: bool = True,
) -> List[str]:
    """
    Descobre URLs de imóveis com filtros aplicados

    Args:
        property_type: Tipo do imóvel
        region: Região de Campo Grande
        price_min: Preço mínimo
        price_max: Preço máximo
        max_pages: Máximo de páginas para percorrer
        use_stealth: Usar playwright-stealth

    Returns:
        Lista de URLs de imóveis encontrados
    """
    properties = []

    # Usar browser com stealth se habilitado
    if use_stealth:
        playwright, browser, context, page = await create_stealth_browser(headless=True)
    else:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

    try:
        for page_num in range(1, max_pages + 1):
            # Construir URL de busca
            search_url = build_search_url(
                property_type=property_type,
                region=region,
                price_min=price_min,
                price_max=price_max,
                page=page_num,
            )

            print(f"🔍 Página {page_num}: {search_url}")

            # Navegar (domcontentloaded é mais rápido que networkidle)
            await page.goto(search_url, wait_until='domcontentloaded', timeout=60000)

            # Verificar se foi bloqueado
            title = await page.title()
            if "just a moment" in title.lower():
                print(f"   ⚠️  Cloudflare challenge na página {page_num}")
                break

            # Extrair URLs dos imóveis
            # Seletor: links de imóveis na listagem
            property_links = await page.locator('a[href*="/imovel/"]').all()

            page_properties = []
            for link in property_links:
                href = await link.get_attribute('href')
                if href and '/imovel/' in href:
                    # Garantir URL absoluta
                    if href.startswith('/'):
                        href = f"https://www.infoimoveis.com.br{href}"

                    # Evitar duplicatas
                    if href not in properties and href not in page_properties:
                        page_properties.append(href)

            print(f"   ✅ Encontrados: {len(page_properties)} imóveis")
            properties.extend(page_properties)

            # Verificar se há próxima página
            has_next = await page.locator('a.proxima, a[rel="next"]').count() > 0
            if not has_next:
                print(f"   ℹ️  Última página ({page_num})")
                break

            # Delay entre páginas
            await asyncio.sleep(2)

    finally:
        await browser.close()
        await playwright.stop()

    # Remover duplicatas e ordenar
    properties = sorted(list(set(properties)))

    print(f"\n📊 Total de imóveis descobertos: {len(properties)}")
    return properties


async def discover_by_preset(preset: str, max_pages: int = 5) -> List[str]:
    """
    Busca usando presets predefinidos

    Presets disponíveis:
    - 'segredo_100_200k': Casa térrea no Segredo, R$ 100k-200k
    - 'centro_apartamentos': Apartamentos no Centro
    - 'prosa_casas': Casas no Prosa

    Args:
        preset: Nome do preset
        max_pages: Máximo de páginas

    Returns:
        Lista de URLs
    """
    presets = {
        'segredo_100_200k': {
            'property_type': 'casa-terrea',
            'region': 'regiao-segredo',
            'price_min': 100000,
            'price_max': 200000,
        },
        'segredo_200_400k': {
            'property_type': 'casa-terrea',
            'region': 'regiao-segredo',
            'price_min': 200000,
            'price_max': 400000,
        },
        'centro_apartamentos': {
            'property_type': 'apartamento',
            'region': 'centro',
            'price_min': 150000,
            'price_max': 300000,
        },
        'prosa_casas': {
            'property_type': 'casa-terrea',
            'region': 'prosa',
        },
        'jardim_estados_sobrados': {
            'property_type': 'casa-sobrado',
            'region': 'jardim-dos-estados',
        },
    }

    if preset not in presets:
        raise ValueError(f"Preset '{preset}' não encontrado. Disponíveis: {list(presets.keys())}")

    config = presets[preset]
    print(f"🎯 Usando preset: {preset}")
    print(f"   Configuração: {config}")

    return await discover_properties_filtered(**config, max_pages=max_pages)


async def main():
    """Exemplo de uso"""
    print("=" * 80)
    print("🔍 DISCOVERY FILTRADO - InfoImóveis")
    print("=" * 80)

    # Exemplo 1: Busca customizada
    print("\n📍 Exemplo 1: Casa térrea no Segredo (R$ 100k-200k)")
    urls = await discover_properties_filtered(
        property_type='casa-terrea',
        region='regiao-segredo',
        price_min=100000,
        price_max=200000,
        max_pages=3,
    )

    print(f"\n✅ URLs encontradas:")
    for i, url in enumerate(urls[:5], 1):
        print(f"   {i}. {url}")

    if len(urls) > 5:
        print(f"   ... e mais {len(urls) - 5} imóveis")

    # Exemplo 2: Usando preset
    print("\n\n📍 Exemplo 2: Usando preset 'segredo_100_200k'")
    urls2 = await discover_by_preset('segredo_100_200k', max_pages=2)

    print(f"\n✅ Total: {len(urls2)} imóveis")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
