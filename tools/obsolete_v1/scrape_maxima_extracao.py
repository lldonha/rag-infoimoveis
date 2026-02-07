#!/usr/bin/env python3
"""
Scraper de Extração Máxima - InfoImóveis
=========================================
Entra em 1 imóvel e extrai ABSOLUTAMENTE TUDO:
- Todos os campos estruturados possíveis
- Todas as imagens (download local)
- HTML bruto completo
- Screenshots da página
- Metadata completa

🛡️ PROTEÇÕES ANTI-BLOQUEIO:
1. Playwright Stealth (anti-detecção)
2. Fingerprint rotation (user-agent, viewport, timezone)
3. Human behavior simulation (scroll, mouse, delays)
4. Rate limiting inteligente
5. Cookie persistence
6. Delay aleatório entre requests
7. Fallback para headless=False se necessário
"""

import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin
import hashlib
import random

from playwright.async_api import async_playwright, Page

# Importar módulos de proteção
sys.path.append(os.path.dirname(__file__))
from fingerprint_rotator import get_random_fingerprint, get_anti_detection_script
from human_behavior import (
    human_scroll,
    human_mouse_move,
    simulate_reading,
    wait_for_page_load,
)

# Configurações
BASE_URL = "https://www.infoimoveis.com.br"
OUTPUT_DIR = Path(".tmp/maxima_extracao")
IMAGES_DIR = OUTPUT_DIR / "images"

# Criar diretórios
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(text: Optional[str]) -> Optional[str]:
    """Limpa texto removendo espaços extras"""
    if not text:
        return None
    return re.sub(r"\s+", " ", text.strip())


def parse_price(text: str) -> Optional[float]:
    """Converte texto de preço para float"""
    if not text:
        return None
    clean = re.sub(r"[R$\s.]", "", text)
    clean = clean.replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return None


def parse_area(text: str) -> Optional[float]:
    """Converte texto de área para float"""
    if not text:
        return None
    match = re.search(r"([\d.,]+)\s*m", text, re.IGNORECASE)
    if match:
        num = match.group(1).replace(".", "").replace(",", ".")
        try:
            return float(num)
        except ValueError:
            return None
    return None


def parse_int(text: str) -> Optional[int]:
    """Extrai primeiro número inteiro do texto"""
    if not text:
        return None
    match = re.search(r"(\d+)", text)
    if match:
        return int(match.group(1))
    return None


async def download_image(page: Page, url: str, filename: str) -> Optional[str]:
    """
    Baixa uma imagem e salva localmente
    Retorna o caminho local do arquivo
    """
    try:
        # Garantir URL absoluta
        if url.startswith("/"):
            url = urljoin(BASE_URL, url)

        # Fazer download via CDP (Chrome DevTools Protocol)
        response = await page.request.get(url)
        if response.status == 200:
            content = await response.body()

            # Salvar arquivo
            filepath = IMAGES_DIR / filename
            with open(filepath, "wb") as f:
                f.write(content)

            print(f"  ✓ Imagem baixada: {filename} ({len(content)} bytes)")
            return str(filepath)
        else:
            print(f"  ✗ Erro ao baixar {url}: Status {response.status}")
            return None
    except Exception as e:
        print(f"  ✗ Erro ao baixar {url}: {e}")
        return None


async def extract_all_data(page: Page, url: str) -> Dict[str, Any]:
    """
    Extrai TODOS os dados possíveis de um imóvel
    """
    print(f"\n🏠 Extraindo dados de: {url}")

    data: Dict[str, Any] = {
        "metadata": {
            "source_url": url,
            "scraped_at": datetime.now().isoformat(),
            "scraper_version": "maxima_extracao_v1.0",
        },
        "basic_info": {},
        "location": {},
        "areas": {},
        "rooms": {},
        "prices": {},
        "features": [],
        "description": {},
        "advertiser": {},
        "images": [],
        "raw_data": {},
    }

    # === 1. TÍTULO ===
    try:
        h1 = await page.locator("h1").first.inner_text()
        data["basic_info"]["title"] = clean_text(h1)
        print(f"  ✓ Título: {data['basic_info']['title']}")
    except:
        pass

    # === 2. PREÇO PRINCIPAL ===
    try:
        # Procurar "VALOR TOTAL:"
        price_section = await page.locator("text=/VALOR TOTAL:/i").first.inner_text()
        if price_section:
            match = re.search(r"R\$\s*([\d.]+,\d{2})", price_section)
            if match:
                price_str = match.group(1).replace(".", "").replace(",", ".")
                data["prices"]["price_brl"] = float(price_str)
                print(f"  ✓ Preço: R$ {data['prices']['price_brl']:,.2f}")
    except:
        pass

    # === 3. TABELA DE CARACTERÍSTICAS ===
    print("\n  📊 Extraindo tabela de características...")

    table_fields = {
        "Tipo": ("basic_info", "property_type", str),
        "Finalidade": ("basic_info", "transaction_type", str),
        "Bairro": ("location", "neighborhood", str),
        "Cidade/UF": ("location", "city_state", str),
        "Endereço": ("location", "address", str),
        "Área total": ("areas", "area_total_m2", parse_area),
        "Área construída": ("areas", "area_built_m2", parse_area),
        "Área útil": ("areas", "area_util_m2", parse_area),
        "Área do terreno": ("areas", "area_terreno_m2", parse_area),
        "IPTU": ("prices", "iptu_annual_brl", parse_price),
        "Condomínio": ("prices", "condominium_fee_brl", parse_price),
        "Quartos": ("rooms", "bedrooms", parse_int),
        "Suítes": ("rooms", "suites", parse_int),
        "Banheiros": ("rooms", "bathrooms", parse_int),
        "Wc social": ("rooms", "wc_social", parse_int),
        "Vagas": ("rooms", "parking_spaces", parse_int),
        "Idade": ("basic_info", "property_age", str),
        "Padrão": ("basic_info", "construction_standard", str),
    }

    for field_name, (section, key, parser) in table_fields.items():
        try:
            # Buscar linha da tabela com esse campo
            row = await page.locator(
                f'tr:has-text("{field_name}") td:nth-child(2)'
            ).first.inner_text()
            if row:
                value = clean_text(row)
                if parser:
                    value = parser(value)

                if value:
                    data[section][key] = value
                    print(f"    ✓ {field_name}: {value}")
        except:
            pass

    # === 4. CARACTERÍSTICAS (lista .itens li) ===
    print("\n  📋 Extraindo lista de características...")
    try:
        items = await page.locator(".itens li").all()
        for item in items:
            text = clean_text(await item.inner_text())
            if text:
                data["features"].append(text)

        print(f"    ✓ {len(data['features'])} características encontradas")
    except:
        pass

    # === 5. DESCRIÇÃO ===
    print("\n  📝 Extraindo descrição...")
    try:
        desc = await page.locator(".descricao .texto").first.inner_text()
        data["description"]["main"] = clean_text(desc)
        print(f"    ✓ Descrição: {len(data['description']['main'])} caracteres")
    except:
        pass

    # === 6. OBSERVAÇÕES ===
    try:
        obs = await page.locator(".observacoes .texto").first.inner_text()
        data["description"]["observations"] = clean_text(obs)
        print(
            f"    ✓ Observações: {len(data['description']['observations'])} caracteres"
        )
    except:
        pass

    # === 7. ANUNCIANTE ===
    print("\n  👤 Extraindo dados do anunciante...")
    try:
        # Nome do anunciante
        advertiser_name = await page.locator(
            ".anunciante .nome, .corretor .nome"
        ).first.inner_text()
        data["advertiser"]["name"] = clean_text(advertiser_name)
        print(f"    ✓ Nome: {data['advertiser']['name']}")
    except:
        pass

    try:
        # CRECI
        creci = await page.locator("text=/CRECI/i").first.inner_text()
        if creci:
            match = re.search(r"CRECI[:\s]*([\d-J]+)", creci, re.IGNORECASE)
            if match:
                data["advertiser"]["creci"] = match.group(1)
                print(f"    ✓ CRECI: {data['advertiser']['creci']}")
    except:
        pass

    try:
        # Telefone
        phone = await page.locator(
            '.telefone, .fone, [class*="tel"]'
        ).first.inner_text()
        data["advertiser"]["phone"] = clean_text(phone)
        print(f"    ✓ Telefone: {data['advertiser']['phone']}")
    except:
        pass

    # === 8. IMAGENS - DOWNLOAD COMPLETO ===
    print("\n  🖼️  Baixando TODAS as imagens...")

    image_selectors = [
        'img[src*="/fotos/"]',
        'img[src*="stored/imoveis"]',
        'img[data-src*="/fotos/"]',
        ".galeria img",
        '[class*="foto"] img',
        '[class*="image"] img',
        ".carousel img",
        ".slider img",
    ]

    image_urls = set()

    for selector in image_selectors:
        try:
            imgs = await page.locator(selector).all()
            for img in imgs:
                src = await img.get_attribute("src") or await img.get_attribute(
                    "data-src"
                )
                if src and (
                    "foto" in src.lower()
                    or "stored" in src.lower()
                    or "imovel" in src.lower()
                ):
                    # Garantir URL absoluta
                    if src.startswith("/"):
                        src = urljoin(BASE_URL, src)
                    image_urls.add(src)
        except:
            pass

    print(f"    📸 Encontradas {len(image_urls)} imagens únicas")

    # Download de cada imagem
    for idx, img_url in enumerate(sorted(image_urls), start=1):
        # Gerar nome do arquivo
        url_hash = hashlib.md5(img_url.encode()).hexdigest()[:8]
        ext = ".jpg"  # Padrão
        if img_url.lower().endswith(".png"):
            ext = ".png"
        elif img_url.lower().endswith(".webp"):
            ext = ".webp"

        filename = f"image_{idx:02d}_{url_hash}{ext}"

        # Download
        local_path = await download_image(page, img_url, filename)

        if local_path:
            data["images"].append(
                {
                    "index": idx,
                    "url": img_url,
                    "local_path": local_path,
                    "filename": filename,
                }
            )

    print(f"\n  ✅ {len(data['images'])} imagens baixadas com sucesso!")

    # === 9. HTML BRUTO ===
    print("\n  💾 Salvando HTML bruto...")
    try:
        html_content = await page.content()
        data["raw_data"]["html_length"] = len(html_content)

        # Salvar HTML em arquivo separado
        html_file = OUTPUT_DIR / "page_raw.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        data["raw_data"]["html_file"] = str(html_file)
        print(f"    ✓ HTML salvo: {len(html_content)} caracteres")
    except Exception as e:
        print(f"    ✗ Erro ao salvar HTML: {e}")

    # === 10. SCREENSHOT COMPLETO ===
    print("\n  📸 Capturando screenshot da página...")
    try:
        screenshot_file = OUTPUT_DIR / "page_screenshot.png"
        await page.screenshot(path=str(screenshot_file), full_page=True)
        data["raw_data"]["screenshot_file"] = str(screenshot_file)
        print(f"    ✓ Screenshot salvo: {screenshot_file}")
    except Exception as e:
        print(f"    ✗ Erro ao capturar screenshot: {e}")

    return data


async def scrape_imovel_completo(url: str, headless: bool = True) -> Dict[str, Any]:
    """
    Scrape completo de um imóvel com MÁXIMA PROTEÇÃO ANTI-BLOQUEIO

    Args:
        url: URL do imóvel
        headless: Se True, usa modo headless (mais rápido, pode ser bloqueado)
                  Se False, mostra navegador (mais lento, raramente bloqueado)

    Returns:
        Dict com todos os dados extraídos
    """
    async with async_playwright() as p:
        print("=" * 80)
        print("🚀 SCRAPER DE EXTRAÇÃO MÁXIMA - MODO STEALTH ATIVADO")
        print("=" * 80)

        # 1. FINGERPRINT ALEATÓRIO
        fingerprint = get_random_fingerprint()
        print(f"\n🎭 Fingerprint gerado:")
        print(f"  • User-Agent: {fingerprint['user_agent'][:60]}...")
        print(
            f"  • Viewport: {fingerprint['viewport']['width']}x{fingerprint['viewport']['height']}"
        )
        print(f"  • Timezone: {fingerprint['timezone']}")
        print(f"  • Locale: {fingerprint['locale']}")

        # 2. CONFIGURAR NAVEGADOR
        print(f"\n🌐 Iniciando navegador (headless={headless})...")

        browser = await p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox",
                "--no-first-run",
                "--no-sandbox",
                "--no-zygote",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )

        # 3. CRIAR CONTEXTO COM FINGERPRINT
        context = await browser.new_context(
            user_agent=fingerprint["user_agent"],
            viewport=fingerprint["viewport"],
            locale=fingerprint["locale"],
            timezone_id=fingerprint["timezone"],
            # Headers adicionais
            extra_http_headers={
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            },
        )

        page = await context.new_page()

        # 4. ANTI-DETECÇÃO SCRIPT
        print("🛡️  Aplicando scripts anti-detecção...")
        await page.add_init_script(get_anti_detection_script())

        # 5. NAVEGAÇÃO COM DELAYS HUMANOS
        print(f"\n🌐 Navegando para: {url}")

        # Delay antes de começar (humanos não clicam instantaneamente)
        initial_delay = random.uniform(1, 3)
        print(f"⏳ Delay inicial: {initial_delay:.1f}s")
        await asyncio.sleep(initial_delay)

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"⚠️  Timeout no goto, mas continuando... ({e})")

        # 6. AGUARDAR CLOUDFLARE
        print("\n☁️  Aguardando bypass do Cloudflare...")
        cloudflare_wait = random.uniform(8, 12)
        print(f"⏳ Aguardando {cloudflare_wait:.1f}s...")
        await page.wait_for_timeout(int(cloudflare_wait * 1000))

        # 7. VERIFICAR SE PASSOU
        content = await page.content()
        blocked = False

        if "cloudflare" in content.lower() or "just a moment" in content.lower():
            print("⚠️  Cloudflare ainda presente, aguardando mais 10s...")
            await page.wait_for_timeout(10000)
            content = await page.content()

            if "cloudflare" in content.lower():
                print("❌ BLOQUEADO pelo Cloudflare!")
                blocked = True

        if "access denied" in content.lower() or "forbidden" in content.lower():
            print("❌ ACESSO NEGADO!")
            blocked = True

        if blocked:
            print("\n⚠️  Tentando com headless=False...")
            await browser.close()
            if headless:
                # Retry com headless=False
                return await scrape_imovel_completo(url, headless=False)
            else:
                raise Exception("Bloqueado mesmo com headless=False!")

        print("✅ Cloudflare bypassado com sucesso!")

        # 8. COMPORTAMENTO HUMANO
        print("\n🤖 Simulando comportamento humano...")

        # Aguardar carregamento
        await wait_for_page_load(page, min_wait=2, max_wait=4)

        # Scroll humano
        print("  • Scrolling...")
        await human_scroll(page, duration=random.uniform(2, 4))

        # Movimentos de mouse
        print("  • Movendo mouse...")
        await human_mouse_move(page, num_moves=random.randint(2, 4))

        # Simular leitura
        print("  • Simulando leitura...")
        await simulate_reading(page, min_time=3, max_time=6)

        # 9. EXTRAIR DADOS
        print("\n📊 Iniciando extração de dados...")
        data = await extract_all_data(page, url)

        # 10. DELAY FINAL ANTES DE FECHAR
        final_delay = random.uniform(1, 2)
        print(f"\n⏳ Delay final: {final_delay:.1f}s")
        await asyncio.sleep(final_delay)

        await browser.close()

        return data


async def main():
    """Main function"""

    # URL de teste (usar uma dos exemplos do PROGRESSO)
    test_url = (
        "https://www.infoimoveis.com.br/imovel/venda-area-jardim-bela-vista/55162"
    )

    print("=" * 80)
    print("🏠 SCRAPER DE EXTRAÇÃO MÁXIMA - InfoImóveis")
    print("=" * 80)
    print(f"\n📁 Arquivos serão salvos em: {OUTPUT_DIR.absolute()}")
    print(f"🖼️  Imagens serão salvas em: {IMAGES_DIR.absolute()}")

    # Executar scraping
    result = await scrape_imovel_completo(test_url)

    # Salvar JSON completo
    output_file = OUTPUT_DIR / "imovel_completo.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("✅ EXTRAÇÃO COMPLETA!")
    print("=" * 80)
    print(f"\n📊 Estatísticas:")
    print(f"  - Campos básicos: {len(result.get('basic_info', {}))}")
    print(f"  - Localização: {len(result.get('location', {}))}")
    print(f"  - Áreas: {len(result.get('areas', {}))}")
    print(f"  - Cômodos: {len(result.get('rooms', {}))}")
    print(f"  - Preços: {len(result.get('prices', {}))}")
    print(f"  - Características: {len(result.get('features', []))}")
    print(f"  - Imagens baixadas: {len(result.get('images', []))}")
    print(f"\n💾 Arquivos salvos:")
    print(f"  - JSON completo: {output_file}")
    print(f"  - HTML bruto: {result['raw_data'].get('html_file', 'N/A')}")
    print(f"  - Screenshot: {result['raw_data'].get('screenshot_file', 'N/A')}")
    print(f"  - Imagens: {IMAGES_DIR.absolute()}/")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
