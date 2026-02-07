#!/usr/bin/env python3
"""VERSÃO FINAL - Extração máxima usando scraper que FUNCIONA"""

import asyncio
import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from scraper_stealth import scrape_property_stealth


async def main():
    URL = "https://www.infoimoveis.com.br/imovel/venda-area-jardim-bela-vista/55162"
    OUTPUT = Path(".tmp/final_extracao.json")

    print("=" * 80)
    print("🏠 EXTRAÇÃO MÁXIMA - USANDO SCRAPER QUE FUNCIONA")
    print("=" * 80)
    print(f"URL: {URL}\n")

    print("🚀 Executando scraping...")
    result = await scrape_property_stealth(URL, headless=True)

    print("\n✅ DADOS EXTRAÍDOS:")
    print(f"  • Título: {data.get('title')}")
    print(
        f"  • Preço: R$ {data.get('price_brl'):,.2f}"
        if data.get("price_brl")
        else "  • Preço: N/A"
    )
    print(f"  • Bairro: {data.get('neighborhood')}")
    print(
        f"  • Área Total: {data.get('area_total_m2')} m²"
        if data.get("area_total_m2")
        else "  • Área Total: N/A"
    )
    imgs = data.get("images") or []
    feats = data.get("features") or []
    print(f"  • Imagens (URLs): {len(imgs)}")
    print(f"  • Características: {len(feats)}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n💾 JSON salvo em: {OUTPUT.absolute()}")
    print("\n" + "=" * 80)

    # Mostrar URLs das imagens
    if data.get("images"):
        print("\n🖼️  IMAGENS ENCONTRADAS:")
        for idx, img in enumerate(data["images"][:5], 1):  # Primeiras 5
            print(f"  {idx}. {img}")
        if len(data["images"]) > 5:
            print(f"  ... e mais {len(data['images']) - 5} imagens")


if __name__ == "__main__":
    asyncio.run(main())
