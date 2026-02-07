#!/usr/bin/env python3
"""
EXTRAÇÃO MÁXIMA COMPLETA - InfoImóveis
=======================================
Extrai ABSOLUTAMENTE TUDO de um imóvel:
- Todos os campos estruturados
- TODAS as imagens (download local)
- HTML bruto
- Screenshot full-page
"""

import asyncio
import json
import re
import hashlib
from pathlib import Path
from playwright.async_api import async_playwright
from datetime import datetime
from urllib.parse import urljoin

OUTPUT_DIR = Path(".tmp/extracao_completa")
IMAGES_DIR = OUTPUT_DIR / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


async def download_image(page, url, filename):
    """Baixa uma imagem"""
    try:
        if url.startswith("/"):
            url = f"https://www.infoimoveis.com.br{url}"

        response = await page.request.get(url)
        if response.status == 200:
            content = await response.body()
            filepath = IMAGES_DIR / filename
            with open(filepath, "wb") as f:
                f.write(content)
            print(f"  ✓ {filename} ({len(content)} bytes)")
            return str(filepath)
    except Exception as e:
        print(f"  ✗ Erro: {e}")
    return None


async def main():
    URL = "https://www.infoimoveis.com.br/imovel/venda-area-jardim-bela-vista/55162"

    print("=" * 80)
    print("🏠 EXTRAÇÃO MÁXIMA COMPLETA - InfoImóveis")
    print("=" * 80)
    print(f"\nURL: {URL}")
    print(f"Output: {OUTPUT_DIR.absolute()}\n")

    async with async_playwright() as p:
        print("🚀 Abrindo navegador...")
        browser = await p.chromium.launch(headless=True)  # headless=True agora
        page = await browser.new_page()

        print("🌐 Navegando...")
        await page.goto(URL, wait_until="domcontentloaded", timeout=60000)

        print("⏳ Aguardando Cloudflare (10s)...")
        await page.wait_for_timeout(10000)

        print("\n📊 Extraindo dados estruturados...")

        data = {
            "metadata": {
                "url": URL,
                "timestamp": datetime.now().isoformat(),
            },
            "basico": {},
            "localizacao": {},
            "areas": {},
            "comodos": {},
            "valores": {},
            "caracteristicas": [],
            "descricao": {},
            "anunciante": {},
            "imagens": [],
        }

        # === BÁSICO ===
        try:
            data["basico"]["titulo"] = await page.locator("h1").first.inner_text()
            print(f"  ✓ Título: {data['basico']['titulo']}")
        except:
            pass

        try:
            tipo = await page.locator(
                'tr:has-text("Tipo") td:nth-child(2)'
            ).first.inner_text()
            data["basico"]["tipo"] = tipo.strip()
            print(f"  ✓ Tipo: {data['basico']['tipo']}")
        except:
            pass

        # === LOCALIZAÇÃO ===
        try:
            data["localizacao"]["bairro"] = await page.locator(
                'tr:has-text("Bairro") td:nth-child(2)'
            ).first.inner_text()
            print(f"  ✓ Bairro: {data['localizacao']['bairro']}")
        except:
            pass

        try:
            cidade = await page.locator(
                'tr:has-text("Cidade/UF") td:nth-child(2)'
            ).first.inner_text()
            data["localizacao"]["cidade_uf"] = cidade.strip()
            print(f"  ✓ Cidade/UF: {data['localizacao']['cidade_uf']}")
        except:
            pass

        try:
            data["localizacao"]["endereco"] = await page.locator(
                'tr:has-text("Endereço") td:nth-child(2)'
            ).first.inner_text()
            print(f"  ✓ Endereço: {data['localizacao']['endereco']}")
        except:
            pass

        # === ÁREAS ===
        try:
            area = await page.locator(
                'tr:has-text("Área total") td:nth-child(2)'
            ).first.inner_text()
            data["areas"]["area_total"] = area.strip()
            print(f"  ✓ Área Total: {data['areas']['area_total']}")
        except:
            pass

        try:
            area = await page.locator(
                'tr:has-text("Área construída") td:nth-child(2)'
            ).first.inner_text()
            data["areas"]["area_construida"] = area.strip()
            print(f"  ✓ Área Construída: {data['areas']['area_construida']}")
        except:
            pass

        # === VALORES ===
        try:
            price_text = await page.locator("text=/VALOR TOTAL/i").first.inner_text()
            match = re.search(r"R\$\s*([\d.]+,\d{2})", price_text)
            if match:
                data["valores"]["preco"] = match.group(1)
                print(f"  ✓ Preço: R$ {data['valores']['preco']}")
        except:
            pass

        try:
            iptu = await page.locator(
                'tr:has-text("IPTU") td:nth-child(2)'
            ).first.inner_text()
            data["valores"]["iptu"] = iptu.strip()
            print(f"  ✓ IPTU: {data['valores']['iptu']}")
        except:
            pass

        # === CARACTERÍSTICAS (lista) ===
        print("\n📋 Características:")
        try:
            items = await page.locator(".itens li").all()
            for item in items:
                text = await item.inner_text()
                if text:
                    data["caracteristicas"].append(text.strip())
                    print(f"  • {text.strip()}")
        except:
            pass

        # === DESCRIÇÃO ===
        try:
            desc = await page.locator(".descricao .texto").first.inner_text()
            data["descricao"]["principal"] = desc.strip()
            print(f"\n📝 Descrição: {len(desc)} caracteres")
        except:
            pass

        # === ANUNCIANTE ===
        try:
            nome = await page.locator(
                ".anunciante .nome, .corretor .nome"
            ).first.inner_text()
            data["anunciante"]["nome"] = nome.strip()
            print(f"\n👤 Anunciante: {data['anunciante']['nome']}")
        except:
            pass

        # === IMAGENS - DOWNLOAD ===
        print("\n🖼️  Procurando imagens...")

        # Tentar múltiplos seletores
        selectors = [
            "img",  # Todas as imagens
            'img[src*="foto"]',
            'img[src*="stored"]',
            "img[data-src]",
        ]

        image_urls = set()
        for selector in selectors:
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
                        if src.startswith("/"):
                            src = f"https://www.infoimoveis.com.br{src}"
                        image_urls.add(src)
            except:
                pass

        print(f"  📸 Encontradas {len(image_urls)} imagens únicas\n")

        # Download
        for idx, img_url in enumerate(sorted(image_urls), start=1):
            url_hash = hashlib.md5(img_url.encode()).hexdigest()[:8]
            ext = ".jpg"
            if ".png" in img_url.lower():
                ext = ".png"
            if ".webp" in img_url.lower():
                ext = ".webp"

            filename = f"image_{idx:02d}_{url_hash}{ext}"
            local_path = await download_image(page, img_url, filename)

            if local_path:
                data["imagens"].append(
                    {
                        "index": idx,
                        "url": img_url,
                        "local_path": local_path,
                        "filename": filename,
                    }
                )

        # === HTML BRUTO ===
        print("\n💾 Salvando HTML bruto...")
        html = await page.content()
        html_file = OUTPUT_DIR / "page_raw.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  ✓ {html_file} ({len(html)} chars)")

        # === SCREENSHOT ===
        print("\n📸 Screenshot full-page...")
        screenshot_file = OUTPUT_DIR / "page_screenshot.png"
        await page.screenshot(path=str(screenshot_file), full_page=True)
        print(f"  ✓ {screenshot_file}")

        # === SALVAR JSON ===
        output_file = OUTPUT_DIR / "dados_completos.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 80)
        print("✅ EXTRAÇÃO COMPLETA!")
        print("=" * 80)
        print(f"\n📊 Estatísticas:")
        print(f"  • Campos básicos: {len(data['basico'])}")
        print(f"  • Localização: {len(data['localizacao'])}")
        print(f"  • Áreas: {len(data['areas'])}")
        print(f"  • Valores: {len(data['valores'])}")
        print(f"  • Características: {len(data['caracteristicas'])}")
        print(f"  • Imagens baixadas: {len(data['imagens'])}")
        print(f"\n💾 Arquivos:")
        print(f"  • JSON: {output_file}")
        print(f"  • HTML: {html_file}")
        print(f"  • Screenshot: {screenshot_file}")
        print(f"  • Imagens: {IMAGES_DIR}/")
        print("\n" + "=" * 80)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
