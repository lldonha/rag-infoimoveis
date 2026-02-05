"""
Scraper com Playwright Stealth - Anti-detecção básica
Baseado em: github.com/HasData/cloudflare-bypass

Objetivo: Contornar Cloudflare usando playwright-stealth
Features:
- headless=True funcional (com stealth patches)
- Fingerprint masking
- Remove webdriver flag
- User-agent + timezone BR
"""
import asyncio
import random
import sys
from pathlib import Path

# Add parent dir to path
sys.path.append(str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright
from playwright_stealth import Stealth


async def create_stealth_browser(headless=True, viewport_width=1920, viewport_height=1080):
    """
    Cria browser com stealth mode ativado

    Args:
        headless: Se True, roda em background (recomendado para produção)
        viewport_width: Largura da viewport
        viewport_height: Altura da viewport

    Returns:
        tuple: (playwright, browser, context, page)
    """
    playwright = await async_playwright().start()

    # Launch browser com args anti-detecção
    browser = await playwright.chromium.launch(
        headless=headless,
        args=[
            '--disable-blink-features=AutomationControlled',  # Remove webdriver flag
            '--disable-dev-shm-usage',                         # Evita problemas memória
            '--disable-accelerated-2d-canvas',                 # Reduz fingerprint
            '--no-first-run',                                  # Sem welcome screen
            '--no-zygote',                                     # Performance
            '--disable-gpu',                                   # Headless compatibility
            '--no-sandbox',                                    # Docker/CI compatibility
        ]
    )

    # Context com características brasileiras
    context = await browser.new_context(
        viewport={'width': viewport_width, 'height': viewport_height},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        locale='pt-BR',
        timezone_id='America/Campo_Grande',
        color_scheme='light',
        device_scale_factor=1.0,
    )

    # Create page
    page = await context.new_page()

    # 🪄 MAGIC LINE - Aplica stealth patches
    stealth_config = Stealth()
    await stealth_config.apply_stealth_async(page)

    return playwright, browser, context, page


async def scrape_property_stealth(url: str, headless=True) -> dict:
    """
    Scrape com stealth mode

    Args:
        url: URL do imóvel
        headless: Se True, roda em background

    Returns:
        dict com dados extraídos

    Raises:
        Exception: Se bloqueado pelo Cloudflare
    """
    playwright, browser, context, page = await create_stealth_browser(headless=headless)

    try:
        # Navigate com timeout de 30s
        await page.goto(url, wait_until='networkidle', timeout=30000)

        # Verificar se foi bloqueado
        title = await page.title()
        if "just a moment" in title.lower():
            raise Exception("Cloudflare challenge detected")

        # Import parser existente
        try:
            # Tentar importar do scraper_production
            sys.path.append(str(Path(__file__).parent))
            from scraper_production import parse_property_page

            # Usar parser validado
            data = await parse_property_page(page, url)
            return data

        except ImportError:
            # Fallback: retornar dados básicos
            html_content = await page.content()
            return {
                'url': url,
                'title': title,
                'html_length': len(html_content),
                'success': 'just a moment' not in title.lower()
            }

    finally:
        await browser.close()
        await playwright.stop()


async def test_stealth_single(url: str, headless=True):
    """
    Teste rápido de uma URL

    Args:
        url: URL para testar
        headless: Modo headless

    Returns:
        dict com resultado do teste
    """
    print(f"\n🔍 Testando: {url}")
    print(f"   Modo: {'headless' if headless else 'visível'}")

    try:
        result = await scrape_property_stealth(url, headless=headless)

        # Verificar tipo de retorno
        if isinstance(result, dict):
            # Fallback mode (sem parse_property_page)
            completeness = result.get('completeness', 0)
            title = result.get('title', 'N/A')
        else:
            # PropertyData object (dataclass)
            completeness = result.completeness if hasattr(result, 'completeness') else 0
            # Converter decimal para % (0.85 -> 85)
            if completeness > 0 and completeness < 1:
                completeness = int(completeness * 100)
            title = result.title if hasattr(result, 'title') else 'N/A'

        print(f"✅ SUCESSO")
        print(f"   Título: {title[:60]}..." if title else "   Título: N/A")
        print(f"   Completude: {completeness}%")

        return {
            'url': url,
            'success': True,
            'completeness': completeness,
            'title': title,
        }

    except Exception as e:
        print(f"❌ FALHA: {e}")
        return {
            'url': url,
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    # Teste rápido com 1 URL
    test_url = "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-giocondo-orsi/557442"

    print("=" * 80)
    print("🧪 TESTE PLAYWRIGHT STEALTH")
    print("=" * 80)

    result = asyncio.run(test_stealth_single(test_url, headless=True))

    print("\n" + "=" * 80)
    if result['success']:
        print("✅ Stealth mode funcionando!")
        print(f"   Completude: {result.get('completeness', 0)}%")
    else:
        print("❌ Stealth mode falhou")
        print(f"   Erro: {result.get('error')}")
    print("=" * 80)
