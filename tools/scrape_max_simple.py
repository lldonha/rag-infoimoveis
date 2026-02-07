#!/usr/bin/env python3
"""
Scraper de Extração MÁXIMA - Versão Simplificada e Testada
============================================================
Baseado no scraper_production.py que JÁ FUNCIONA (0 bloqueios em 34 imóveis)

EXTRAI:
- Todos os campos estruturados
- TODAS as imagens (com download local)
- HTML bruto
- Screenshot
"""

import asyncio
import json
import hashlib
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin

from playwright.async_api import async_playwright

# Config
BASE_URL = "https://www.infoimoveis.com.br"
TEST_URL = "https://www.infoimoveis.com.br/imovel/venda-area-jardim-bela-vista/55162"

OUTPUT_DIR = Path(".tmp/maxima_extracao")
IMAGES_DIR = OUTPUT_DIR / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


async def main():
    print("=" * 80)
    print("🏠 EXTRAÇÃO MÁXIMA - MODO TESTADO (headless=False)")
    print("=" * 80)
    print(f"\n📍 URL: {TEST_URL}")
    print(f"📁 Output: {OUTPUT_DIR.absolute()}\n")

    async with async_playwright() as p:
        # Configuração EXATA do scraper_production.py que funciona
        browser = await p.chromium.launch(
            headless=False,  # CRITICAL: False = funciona, True = pode bloquear
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )

        page = await context.new_page()

        # Anti-detecção
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        print("🌐 Navegando...")
        await page.goto(TEST_URL, wait_until="domcontentloaded", timeout=60000)

        print("⏳ Aguardando Cloudflare (10s)...")
        await page.wait_for_timeout(10000)

        # Verificar bloqueio
        content = await page.content()
        if "cloudflare" in content.lower() or "access denied" in content.lower():
            print("❌ BLOQUEADO!")
            await browser.close()
            return

        print("✅ Cloudflare bypassado!\n")

        # === EXTRAÇÃO ===
        data = {
            "metadata": {
                "source_url": TEST_URL,
                "scraped_at": datetime.now().isoformat(),
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
        }

        print("📊 Extraindo dados...\n")

        # Título
        try:
            h1 = await page.locator("h1").first.inner_text()
            data["basic_info"]["title"] = h1.strip()
            print(f"  ✓ Título: {h1.strip()}")
        except:
            pass

        # Preço - MELHORADO (do hidden input + span.valor)
        try:
            # Método 1: hidden input #priceImovel
            price_input = await page.locator("#priceImovel").get_attribute("value")
            if price_input:
                data["prices"]["price_brl"] = float(price_input)
                print(f"  ✓ Preço: R$ {float(price_input):,.2f}")
        except:
            pass

        if not data["prices"].get("price_brl"):
            try:
                # Método 2: span.valor
                price_span = await page.locator(".valor").first.inner_text()
                import re

                match = re.search(r"R\$\s*([\d.]+,\d{2})", price_span)
                if match:
                    price_str = match.group(1).replace(".", "").replace(",", ".")
                    data["prices"]["price_brl"] = float(price_str)
                    print(f"  ✓ Preço: R$ {float(price_str):,.2f}")
            except:
                pass

        # Tabela de características
        table_fields = {
            "Tipo": "property_type",
            "Bairro": "neighborhood",
            "Cidade/UF": "city_state",
            "Endereço": "address",
            "Área total": "area_total",
            "Área construída": "area_built",
            "IPTU": "iptu",
        }

        for label, key in table_fields.items():
            try:
                value = await page.locator(
                    f'tr:has-text("{label}") td:nth-child(2)'
                ).first.inner_text()
                section = (
                    "location"
                    if key in ["neighborhood", "city_state", "address"]
                    else "areas"
                    if "area" in key
                    else "prices"
                    if key == "iptu"
                    else "basic_info"
                )
                data[section][key] = value.strip()
                print(f"  ✓ {label}: {value.strip()}")
            except:
                pass

        # Anunciante - COMPLETO
        try:
            advertiser_name = await page.locator(
                ".anunciante .nome, span.nome"
            ).first.inner_text()
            data["advertiser"]["name"] = advertiser_name.strip()
            print(f"  ✓ Anunciante: {advertiser_name.strip()}")
        except:
            pass

        try:
            creci = await page.locator(".creci, span.creci").first.inner_text()
            data["advertiser"]["creci"] = creci.strip()
            print(f"  ✓ CRECI: {creci.strip()}")
        except:
            pass

        try:
            # Telefone está oculto, mas podemos pegar do link onclick
            telefone_link = await page.locator("a.telefones").get_attribute("onclick")
            if telefone_link:
                import re

                match = re.search(r"ver_telefones\((\d+)\)", telefone_link)
                if match:
                    data["advertiser"]["phone_id"] = match.group(1)
                    print(f"  ✓ Telefone ID: {match.group(1)} (oculto)")
        except:
            pass

        # Características
        try:
            items = await page.locator(".itens li").all()
            for item in items:
                text = await item.inner_text()
                if text:
                    data["features"].append(text.strip())
            print(f"  ✓ {len(data['features'])} características")
        except:
            pass

        # Quartos/Vagas/Suítes - PARSER de características
        try:
            import re

            for feature in data["features"]:
                feature_lower = feature.lower()

                # Quartos
                if "quarto" in feature_lower and not data["rooms"].get("bedrooms"):
                    match = re.search(r"(\d+)", feature)
                    if match:
                        data["rooms"]["bedrooms"] = int(match.group(1))

                # Suítes
                if "suíte" in feature_lower or "suite" in feature_lower:
                    match = re.search(r"(\d+)", feature)
                    if match:
                        data["rooms"]["suites"] = int(match.group(1))

                # Banheiros/WC
                if "wc" in feature_lower or "banheiro" in feature_lower:
                    match = re.search(r"(\d+)", feature)
                    if match:
                        data["rooms"]["bathrooms"] = int(match.group(1))

                # Vagas
                if "vaga" in feature_lower:
                    match = re.search(r"(\d+)", feature)
                    if match:
                        data["rooms"]["parking_spaces"] = int(match.group(1))

            if data["rooms"]:
                print(f"  ✓ Cômodos extraídos: {data['rooms']}")
        except:
            pass

        # Descrição - CORRIGIDO (NÃO tem .texto neste caso)
        try:
            # OBSERVAÇÕES (tem .texto)
            obs = await page.locator(
                ".observacoes .texto, .observacoes p.texto"
            ).first.inner_text()
            data["description"]["observations"] = obs.strip()
            print(f"  ✓ Observações: {len(obs)} chars")
        except:
            pass

        # Características como "descrição"
        if data["features"]:
            data["description"]["features_text"] = "\n".join(data["features"])
            print(f"  ✓ Características como texto: {len(data['features'])} itens")

        # === IMAGENS - DOWNLOAD COMPLETO ===
        print("\n🖼️  Baixando imagens...")

        selectors = [
            'img[src*="/fotos/"]',
            'img[src*="stored/imoveis"]',
            'img[data-src*="/fotos/"]',
            ".galeria img",
        ]

        image_urls = set()
        for selector in selectors:
            try:
                imgs = await page.locator(selector).all()
                for img in imgs:
                    src = await img.get_attribute("src") or await img.get_attribute(
                        "data-src"
                    )
                    if src and ("foto" in src or "stored" in src or "imovel" in src):
                        if src.startswith("/"):
                            src = urljoin(BASE_URL, src)
                        image_urls.add(src)
            except:
                pass

        print(f"  📸 Encontradas {len(image_urls)} imagens\n")

        # Download
        for idx, url in enumerate(sorted(image_urls), start=1):
            try:
                response = await page.request.get(url)
                if response.status == 200:
                    content_img = await response.body()

                    # Nome do arquivo
                    hash_str = hashlib.md5(url.encode()).hexdigest()[:8]
                    ext = ".jpg"
                    if url.lower().endswith(".png"):
                        ext = ".png"
                    elif url.lower().endswith(".webp"):
                        ext = ".webp"

                    filename = f"image_{idx:02d}_{hash_str}{ext}"
                    filepath = IMAGES_DIR / filename

                    with open(filepath, "wb") as f:
                        f.write(content_img)

                    data["images"].append(
                        {
                            "index": idx,
                            "url": url,
                            "local_path": str(filepath),
                            "filename": filename,
                            "size_bytes": len(content_img),
                        }
                    )

                    print(f"    ✓ [{idx:02d}] {filename} ({len(content_img):,} bytes)")
            except Exception as e:
                print(f"    ✗ [{idx:02d}] Erro: {e}")

        # === SALVAR HTML ===
        print("\n💾 Salvando HTML bruto...")
        html_content = await page.content()
        html_file = OUTPUT_DIR / "page_raw.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        data["raw_html_file"] = str(html_file)
        print(f"  ✓ {html_file} ({len(html_content):,} chars)")

        # === SCREENSHOT ===
        print("\n📸 Capturando screenshot...")
        screenshot_file = OUTPUT_DIR / "page_screenshot.png"
        await page.screenshot(path=str(screenshot_file), full_page=True)
        data["screenshot_file"] = str(screenshot_file)
        print(f"  ✓ {screenshot_file}")

        # === SALVAR JSON ===
        output_file = OUTPUT_DIR / "imovel_completo.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        await browser.close()

        # === RESUMO ===
        print("\n" + "=" * 80)
        print("✅ EXTRAÇÃO COMPLETA!")
        print("=" * 80)
        print(f"\n📊 Estatísticas:")
        print(f"  • Campos básicos: {len(data['basic_info'])}")
        print(f"  • Localização: {len(data['location'])}")
        print(f"  • Áreas: {len(data['areas'])}")
        print(f"  • Preços: {len(data['prices'])}")
        print(f"  • Características: {len(data['features'])}")
        print(f"  • Imagens baixadas: {len(data['images'])}")
        print(f"\n💾 Arquivos:")
        print(f"  • JSON: {output_file}")
        print(f"  • HTML: {html_file}")
        print(f"  • Screenshot: {screenshot_file}")
        print(f"  • Imagens: {IMAGES_DIR}/ ({len(data['images'])} arquivos)")
        print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
