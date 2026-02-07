#!/usr/bin/env python3
"""Extração máxima MINIMALISTA - SEM dependências complexas"""

import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright
from datetime import datetime

OUTPUT_DIR = Path(".tmp/extracao_maxima")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def main():
    URL = "https://www.infoimoveis.com.br/imovel/venda-area-jardim-bela-vista/55162"

    print("=" * 80)
    print("🏠 EXTRAÇÃO MÁXIMA - VERSÃO MÍNIMA")
    print("=" * 80)
    print(f"\nURL: {URL}")
    print(f"Output: {OUTPUT_DIR.absolute()}\n")

    async with async_playwright() as p:
        print("🚀 Abrindo navegador (headless=False para ver)...")
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print(f"🌐 Navegando...")
        await page.goto(URL, timeout=60000)

        print("⏳ Aguardando 10s (Cloudflare)...")
        await page.wait_for_timeout(10000)

        print("\n📊 Extraindo dados...")

        data = {
            "url": URL,
            "timestamp": datetime.now().isoformat(),
        }

        # Título
        try:
            data["titulo"] = await page.locator("h1").first.inner_text()
            print(f"✓ Título: {data['titulo']}")
        except:
            data["titulo"] = None

        # Preço
        try:
            price_text = await page.locator("text=/VALOR TOTAL/i").first.inner_text()
            match = re.search(r"R\$\s*([\d.]+,\d{2})", price_text)
            if match:
                data["preco"] = match.group(1)
                print(f"✓ Preço: {data['preco']}")
        except:
            data["preco"] = None

        # Tabela - Bairro
        try:
            data["bairro"] = await page.locator(
                'tr:has-text("Bairro") td:nth-child(2)'
            ).first.inner_text()
            print(f"✓ Bairro: {data['bairro']}")
        except:
            data["bairro"] = None

        # Endereço
        try:
            data["endereco"] = await page.locator(
                'tr:has-text("Endereço") td:nth-child(2)'
            ).first.inner_text()
            print(f"✓ Endereço: {data['endereco']}")
        except:
            data["endereco"] = None

        # Área Total
        try:
            area_text = await page.locator(
                'tr:has-text("Área total") td:nth-child(2)'
            ).first.inner_text()
            data["area_total"] = area_text
            print(f"✓ Área Total: {data['area_total']}")
        except:
            data["area_total"] = None

        # Imagens URLs
        print("\n🖼️  Buscando imagens...")
        images = []
        try:
            img_elems = await page.locator('img[src*="/fotos/"]').all()
            for img in img_elems[:10]:  # Primeiras 10
                src = await img.get_attribute("src")
                if src:
                    if src.startswith("/"):
                        src = f"https://www.infoimoveis.com.br{src}"
                    images.append(src)
            data["imagens_urls"] = images
            print(f"✓ Encontradas {len(images)} imagens")
        except:
            data["imagens_urls"] = []

        # Salvar JSON
        output_file = OUTPUT_DIR / "dados_extraidos.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Dados salvos em: {output_file}")
        print("\n" + "=" * 80)
        print("✅ EXTRAÇÃO COMPLETA!")
        print("=" * 80)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
