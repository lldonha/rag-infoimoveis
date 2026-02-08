#!/usr/bin/env python3
"""
Batch Scraper v3 - Para 1000 imóveis com logging detalhado
===========================================================
Processa em batches de 50 e gera log a cada batch
"""

import asyncio
import json
import hashlib
import sys
import os
import re
import time
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin
from playwright.async_api import async_playwright

BASE_URL = "https://www.infoimoveis.com.br"
BATCH_SIZE = 50  # Log a cada 50 imóveis


def log_batch_summary(batch_num, batch_data, log_file):
    """Gera log a cada 50 imóveis"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    summary = f"""
{"=" * 80}
📊 BATCH {batch_num} CONCLUÍDO - {timestamp}
{"=" * 80}
Imóveis: {batch_data["start"]} - {batch_data["end"]}
Sucessos: {batch_data["success"]}/{batch_data["total"]}
Falhas: {batch_data["failed"]}/{batch_data["total"]}

Preços extraídos:
- Menor: {batch_data.get("min_price", "N/A")}
- Maior: {batch_data.get("max_price", "N/A")}
- Médio: {batch_data.get("avg_price", "N/A")}

Bairros processados: {len(batch_data.get("neighborhoods", set()))}
{"=" * 80}

"""

    print(summary)

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(summary)


async def scrape_single_property(url: str, output_dir: Path, property_idx: int) -> dict:
    """Scraper com retry logic"""

    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    max_retries = 3

    for attempt in range(max_retries):
        try:
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

                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)

                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(10000)

                content = await page.content()
                if (
                    "cloudflare" in content.lower()
                    or "access denied" in content.lower()
                ):
                    await browser.close()
                    if attempt < max_retries - 1:
                        print(
                            f"    ⚠️  Bloqueio detectado, tentativa {attempt + 2}/{max_retries}..."
                        )
                        await asyncio.sleep(30)  # Espera mais tempo
                        continue
                    return None

                data = {
                    "metadata": {
                        "source_url": url,
                        "scraped_at": datetime.now().isoformat(),
                        "property_index": property_idx,
                    },
                    "basic_info": {},
                    "location": {},
                    "rooms": {},
                    "prices": {},
                    "features": [],
                    "description": {},
                    "advertiser": {},
                    "images": [],
                }

                # PREÇO - Múltiplas tentativas
                price_found = False

                try:
                    price = await page.input_value("#priceImovel")
                    if price and price.strip():
                        data["prices"]["price_raw"] = price
                        data["prices"]["price_numeric"] = float(price)
                        data["prices"]["price_formatted"] = f"R$ {float(price):,.2f}"
                        price_found = True
                except:
                    pass

                if not price_found:
                    try:
                        price_text = await page.locator(
                            ".preco, .price, .valor"
                        ).first.inner_text()
                        if price_text and "R$" in price_text:
                            data["prices"]["price_formatted"] = price_text.strip()
                            price_numeric = re.sub(r"[^\d,]", "", price_text).replace(
                                ",", "."
                            )
                            if price_numeric:
                                data["prices"]["price_numeric"] = float(price_numeric)
                            price_found = True
                    except:
                        pass

                if not price_found:
                    try:
                        html_content = await page.content()
                        patterns = [
                            r'"price":\s*"?([\d.]+)"?',
                            r">\s*R\$\s*([\d.,]+)\s*<",
                        ]
                        for pattern in patterns:
                            match = re.search(pattern, html_content, re.IGNORECASE)
                            if match:
                                price_str = (
                                    match.group(1).replace(".", "").replace(",", ".")
                                )
                                data["prices"]["price_numeric"] = float(price_str)
                                data["prices"]["price_formatted"] = (
                                    f"R$ {float(price_str):,.2f}"
                                )
                                price_found = True
                                break
                    except:
                        pass

                if not price_found:
                    data["prices"]["price_formatted"] = "N/A"

                # TÍTULO
                try:
                    title = await page.locator("h1").first.inner_text()
                    data["basic_info"]["title"] = title.strip()
                except:
                    pass

                # LOCALIZAÇÃO
                try:
                    neighborhood = await page.locator(".bairro").first.inner_text()
                    data["location"]["neighborhood"] = neighborhood.strip()
                except:
                    pass

                try:
                    city = await page.locator(".cidade").first.inner_text()
                    data["location"]["city"] = city.strip()
                except:
                    data["location"]["city"] = "Campo Grande"

                # CARACTERÍSTICAS
                try:
                    features = await page.locator(".caracteristica, .feature").all()
                    for feat in features:
                        try:
                            text = await feat.inner_text()
                            if text.strip():
                                data["features"].append(text.strip())
                        except:
                            pass
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

                # DESCRIÇÃO
                try:
                    desc = await page.locator(".descricao").first.inner_text()
                    data["description"]["text"] = desc.strip()
                except:
                    pass

                # ANUNCIANTE
                try:
                    advertiser = await page.locator(".anunciante").first.inner_text()
                    data["advertiser"]["name"] = advertiser.strip()
                except:
                    pass

                # IMAGENS
                image_urls = set()
                selectors = ['img[src*="/fotos/"]', 'img[src*="stored/imoveis"]']

                for selector in selectors:
                    try:
                        imgs = await page.locator(selector).all()
                        for img in imgs:
                            src = await img.get_attribute(
                                "src"
                            ) or await img.get_attribute("data-src")
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
                            hash_str = hashlib.md5(img_url.encode()).hexdigest()[:8]
                            filename = f"image_{idx:02d}_{hash_str}.jpg"
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

        except Exception as e:
            print(f"    ❌ Erro (tentativa {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(10)
            else:
                return None

    return None


async def process_1000_properties(
    urls_file: str, output_base_dir: str = ".tmp/batch_1000_imoveis"
):
    """Processa 1000 imóveis com log a cada 50"""

    with open(urls_file, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"🎯 PROCESSANDO {len(urls)} IMÓVEIS")
    print(f"📁 Saída: {output_base_dir}")
    print(f"📊 Logs a cada {BATCH_SIZE} imóveis")
    print()

    base_dir = Path(output_base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    log_file = base_dir / "processing_log.txt"

    # Inicializar log
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(
            f"PROCESSAMENTO DE 1000 IMÓVEIS - Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        f.write("=" * 80 + "\n\n")

    all_results = []
    batch_num = 0

    # Processar em batches de 50
    for batch_start in range(0, len(urls), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(urls))
        batch_urls = urls[batch_start:batch_end]
        batch_num += 1

        print(f"\n{'=' * 80}")
        print(f"📦 BATCH {batch_num}: Imóveis {batch_start + 1} - {batch_end}")
        print(f"{'=' * 80}")

        batch_data = {
            "start": batch_start + 1,
            "end": batch_end,
            "total": len(batch_urls),
            "success": 0,
            "failed": 0,
            "prices": [],
            "neighborhoods": set(),
            "min_price": None,
            "max_price": None,
            "avg_price": None,
        }

        for i, url in enumerate(batch_urls, start=batch_start + 1):
            print(f"\n🏠 {i}/{len(urls)} - {url}")

            property_dir = base_dir / f"property_{i:04d}"

            try:
                data = await scrape_single_property(url, property_dir, i)

                if data:
                    price_str = data.get("prices", {}).get("price_formatted", "N/A")
                    neighborhood = data.get("location", {}).get("neighborhood", "N/A")

                    print(f"    ✅ OK - {price_str} - {neighborhood}")

                    batch_data["success"] += 1
                    batch_data["neighborhoods"].add(neighborhood)

                    # Coletar preço para estatísticas
                    price_num = data.get("prices", {}).get("price_numeric")
                    if price_num:
                        batch_data["prices"].append(price_num)

                    all_results.append(
                        {
                            "index": i,
                            "url": url,
                            "status": "success",
                            "price": price_str,
                            "neighborhood": neighborhood,
                        }
                    )
                else:
                    print(f"    ❌ Falha")
                    batch_data["failed"] += 1
                    all_results.append(
                        {
                            "index": i,
                            "url": url,
                            "status": "error",
                        }
                    )

            except Exception as e:
                print(f"    ❌ Erro: {e}")
                batch_data["failed"] += 1
                all_results.append(
                    {
                        "index": i,
                        "url": url,
                        "status": "error",
                        "error": str(e),
                    }
                )

            # Delay entre imóveis
            if i < batch_end:
                await asyncio.sleep(3)

        # Calcular estatísticas de preço
        if batch_data["prices"]:
            batch_data["min_price"] = f"R$ {min(batch_data['prices']):,.2f}"
            batch_data["max_price"] = f"R$ {max(batch_data['prices']):,.2f}"
            batch_data["avg_price"] = (
                f"R$ {sum(batch_data['prices']) / len(batch_data['prices']):,.2f}"
            )

        # Gerar log do batch
        log_batch_summary(batch_num, batch_data, log_file)

        # Pausa maior entre batches
        if batch_end < len(urls):
            print(f"\n⏳ Pausa de 30s antes do próximo batch...")
            await asyncio.sleep(30)

    # Resumo final
    final_summary = f"""
{"=" * 80}
✅ PROCESSAMENTO CONCLUÍDO
{"=" * 80}
Total: {len(urls)}
Sucessos: {len([r for r in all_results if r["status"] == "success"])}
Falhas: {len([r for r in all_results if r["status"] == "error"])}
Taxa de sucesso: {len([r for r in all_results if r["status"] == "success"]) / len(urls) * 100:.1f}%

Log salvo em: {log_file}
{"=" * 80}
"""

    print(final_summary)

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(final_summary)

    # Salvar resumo JSON
    summary_file = base_dir / "summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "total": len(urls),
                "successful": len([r for r in all_results if r["status"] == "success"]),
                "failed": len([r for r in all_results if r["status"] == "error"]),
                "results": all_results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    return all_results


if __name__ == "__main__":
    urls_file = sys.argv[1] if len(sys.argv) > 1 else ".tmp/urls_1000_imoveis.txt"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else ".tmp/batch_1000_imoveis"

    asyncio.run(process_1000_properties(urls_file, output_dir))
