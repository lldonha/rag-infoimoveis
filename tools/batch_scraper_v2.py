#!/usr/bin/env python3
"""
Batch Scraper v2.1 - Com extração MELHORADA de preço
======================================================
Garante que o preço seja extraído de qualquer forma
"""

import asyncio
import json
import hashlib
import sys
import os
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin

from playwright.async_api import async_playwright

# Config
BASE_URL = "https://www.infoimoveis.com.br"


async def scrape_single_property(url: str, output_dir: Path) -> dict:
    """
    Faz scraping de um único imóvel com EXTRAÇÃO GARANTIDA de preço
    """

    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
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

        print(f"  🌐 Navegando...")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(10000)

        # Verificar bloqueio
        content = await page.content()
        if "cloudflare" in content.lower() or "access denied" in content.lower():
            print(f"  ❌ BLOQUEADO!")
            await browser.close()
            return None

        print(f"  ✅ Cloudflare OK")

        # Inicializar dados
        data = {
            "metadata": {
                "source_url": url,
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
            "extraction_log": {"html_fields": [], "ai_fields": []},
        }

        # ==================== EXTRAÇÃO DO PREÇO (CRÍTICO) ====================
        print(f"  💰 Extraindo preço...")
        price_found = False

        # MÉTODO 1: Input hidden #priceImovel
        if not price_found:
            try:
                price = await page.input_value("#priceImovel")
                if price and price.strip():
                    data["prices"]["price_raw"] = price
                    data["prices"]["price_numeric"] = float(price)
                    data["prices"]["price_formatted"] = f"R$ {float(price):,.2f}"
                    price_found = True
                    data["extraction_log"]["html_fields"].append(
                        "price (input #priceImovel)"
                    )
                    print(f"    ✅ Preço (input): {data['prices']['price_formatted']}")
            except Exception as e:
                pass

        # MÉTODO 2: Seletores CSS de preço
        if not price_found:
            price_selectors = [
                ".preco",
                ".price",
                ".valor",
                ".property-price",
                "[data-testid='price']",
                ".info-price .value",
                ".price-value",
                ".valor-imovel",
            ]
            for selector in price_selectors:
                try:
                    price_text = await page.locator(selector).first.inner_text(
                        timeout=2000
                    )
                    if price_text and "R$" in price_text:
                        data["prices"]["price_formatted"] = price_text.strip()
                        # Extrair valor numérico
                        price_numeric = re.sub(r"[^\d,]", "", price_text).replace(
                            ",", "."
                        )
                        if price_numeric:
                            data["prices"]["price_numeric"] = float(price_numeric)
                        price_found = True
                        data["extraction_log"]["html_fields"].append(
                            f"price (CSS: {selector})"
                        )
                        print(
                            f"    ✅ Preço (CSS): {data['prices']['price_formatted']}"
                        )
                        break
                except:
                    continue

        # MÉTODO 3: Regex no HTML completo
        if not price_found:
            try:
                html_content = await page.content()
                # Padrões comuns de preço no HTML
                patterns = [
                    r'"price":\s*"?([\d.]+)"?',
                    r'"preco":\s*"?([\d.]+)"?',
                    r'class=["\'][^"\']*preco[^"\']*["\'][^>]*>\s*R\$\s*([\d.,]+)',
                    r">\s*R\$\s*([\d.,]+)\s*<",
                ]
                for pattern in patterns:
                    match = re.search(pattern, html_content, re.IGNORECASE)
                    if match:
                        price_str = match.group(1).replace(".", "").replace(",", ".")
                        data["prices"]["price_numeric"] = float(price_str)
                        data["prices"]["price_formatted"] = (
                            f"R$ {float(price_str):,.2f}"
                        )
                        price_found = True
                        data["extraction_log"]["html_fields"].append(
                            "price (regex HTML)"
                        )
                        print(
                            f"    ✅ Preço (regex): {data['prices']['price_formatted']}"
                        )
                        break
            except:
                pass

        # MÉTODO 4: Procurar no texto visível da página
        if not price_found:
            try:
                page_text = await page.inner_text("body")
                # Procurar padrão R$ XX.XXX.XXX ou R$ X.XXX.XXX
                price_match = re.search(r"R\$\s*([\d.]+(?:,\d{2})?)", page_text)
                if price_match:
                    price_str = price_match.group(1).replace(".", "").replace(",", ".")
                    data["prices"]["price_formatted"] = f"R$ {price_match.group(1)}"
                    try:
                        data["prices"]["price_numeric"] = float(price_str)
                    except:
                        pass
                    price_found = True
                    data["extraction_log"]["html_fields"].append("price (texto página)")
                    print(f"    ✅ Preço (texto): {data['prices']['price_formatted']}")
            except:
                pass

        if not price_found:
            data["prices"]["price_formatted"] = "N/A"
            print(f"    ⚠️  Preço NÃO ENCONTRADO")

        # ==================== TÍTULO ====================
        try:
            title = await page.locator("h1").first.inner_text()
            data["basic_info"]["title"] = title.strip()
            data["extraction_log"]["html_fields"].append("title")
        except:
            pass

        # ==================== LOCALIZAÇÃO ====================
        try:
            neighborhood = await page.locator(".bairro").first.inner_text()
            data["location"]["neighborhood"] = neighborhood.strip()
            data["extraction_log"]["html_fields"].append("neighborhood")
        except:
            pass

        try:
            city = await page.locator(".cidade").first.inner_text()
            data["location"]["city"] = city.strip()
            data["extraction_log"]["html_fields"].append("city")
        except:
            data["location"]["city"] = "Campo Grande"

        # ==================== CARACTERÍSTICAS ====================
        try:
            features = await page.locator(".caracteristica, .feature").all()
            for feat in features:
                try:
                    text = await feat.inner_text()
                    if text.strip():
                        data["features"].append(text.strip())
                except:
                    pass
            if data["features"]:
                data["extraction_log"]["html_fields"].append("features")
        except:
            pass

        # Parse quartos/banheiros/vagas
        for feature in data["features"]:
            feature_lower = feature.lower()

            if "quarto" in feature_lower and not data["rooms"].get("bedrooms"):
                match = re.search(r"(\d+)", feature)
                if match:
                    data["rooms"]["bedrooms"] = int(match.group(1))

            if "suíte" in feature_lower or "suite" in feature_lower:
                match = re.search(r"(\d+)", feature)
                if match:
                    data["rooms"]["suites"] = int(match.group(1))

            if "wc" in feature_lower or "banheiro" in feature_lower:
                match = re.search(r"(\d+)", feature)
                if match:
                    data["rooms"]["bathrooms"] = int(match.group(1))

            if "vaga" in feature_lower:
                match = re.search(r"(\d+)", feature)
                if match:
                    data["rooms"]["parking_spaces"] = int(match.group(1))

        # ==================== DESCRIÇÃO ====================
        try:
            desc = await page.locator(".descricao").first.inner_text()
            data["description"]["text"] = desc.strip()
            data["extraction_log"]["html_fields"].append("description")
        except:
            pass

        # ==================== ANUNCIANTE ====================
        try:
            advertiser = await page.locator(".anunciante").first.inner_text()
            data["advertiser"]["name"] = advertiser.strip()
            data["extraction_log"]["html_fields"].append("advertiser")
        except:
            pass

        # ==================== IMAGENS ====================
        image_urls = set()
        selectors = [
            'img[src*="/fotos/"]',
            'img[src*="stored/imoveis"]',
        ]

        for selector in selectors:
            try:
                imgs = await page.locator(selector).all()
                for img in imgs:
                    src = await img.get_attribute("src") or await img.get_attribute(
                        "data-src"
                    )
                    if src and ("foto" in src or "stored" in src):
                        if src.startswith("/"):
                            src = urljoin(BASE_URL, src)
                        image_urls.add(src)
            except:
                pass

        # Download imagens
        for idx, img_url in enumerate(sorted(image_urls), start=1):
            try:
                response = await page.request.get(img_url)
                if response.status == 200:
                    content = await response.body()
                    ext = ".jpg"
                    hash_str = hashlib.md5(img_url.encode()).hexdigest()[:8]
                    filename = f"image_{idx:02d}_{hash_str}{ext}"
                    filepath = images_dir / filename

                    with open(filepath, "wb") as f:
                        f.write(content)

                    data["images"].append(
                        {
                            "index": idx,
                            "url": img_url,
                            "local_path": str(filepath),
                            "filename": filename,
                        }
                    )
            except:
                pass

        # Salvar JSON
        json_file = output_dir / "data.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        await browser.close()

        return data


async def process_batch(urls_file: str, output_base_dir: str = ".tmp/batch_20_imoveis"):
    """
    Processa batch de imóveis
    """

    # Ler URLs
    with open(urls_file, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"🎯 Processando {len(urls)} imóveis...")
    print(f"📁 Saída: {output_base_dir}")
    print()

    base_dir = Path(output_base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for i, url in enumerate(urls, 1):
        print(f"\n{'=' * 80}")
        print(f"🏠 Imóvel {i}/{len(urls)}")
        print(f"🔗 {url}")
        print("=" * 80)

        property_dir = base_dir / f"property_{i:03d}"

        try:
            data = await scrape_single_property(url, property_dir)

            if not data:
                print(f"❌ Falha no scraping")
                results.append({"index": i, "url": url, "status": "error"})
                continue

            print(f"\n  ✅ Scraping OK!")
            print(
                f"     Título: {data.get('basic_info', {}).get('title', 'N/A')[:50]}..."
            )
            print(f"     Preço: {data.get('prices', {}).get('price_formatted', 'N/A')}")
            print(f"     Bairro: {data.get('location', {}).get('neighborhood', 'N/A')}")

            results.append(
                {
                    "index": i,
                    "url": url,
                    "status": "success",
                    "title": data.get("basic_info", {}).get("title", ""),
                    "price": data.get("prices", {}).get("price_formatted", ""),
                    "neighborhood": data.get("location", {}).get("neighborhood", ""),
                }
            )

        except Exception as e:
            print(f"❌ Erro: {e}")
            results.append({"index": i, "url": url, "status": "error", "error": str(e)})

        if i < len(urls):
            print(f"\n  ⏳ Aguardando 5s...")
            await asyncio.sleep(5)

    # Resumo
    print(f"\n{'=' * 80}")
    print(f"✅ BATCH CONCLUÍDO")
    print(f"{'=' * 80}")
    success = len([r for r in results if r["status"] == "success"])
    failed = len([r for r in results if r["status"] == "error"])
    print(f"📊 Total: {len(urls)} | ✅ Sucesso: {success} | ❌ Falhas: {failed}")

    # Salvar resumo
    summary_file = base_dir / "summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "total": len(urls),
                "successful": success,
                "failed": failed,
                "results": results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    return results


if __name__ == "__main__":
    urls_file = sys.argv[1] if len(sys.argv) > 1 else ".tmp/urls_20_imoveis.txt"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else ".tmp/batch_20_imoveis"

    asyncio.run(process_batch(urls_file, output_dir))
