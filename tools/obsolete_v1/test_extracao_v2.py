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
    print("🏠 EXTRAÇÃO MÁXIMA")
    print("=" * 80)
    print(f"URL: {URL}\n")

    try:
        print("🚀 Executando scraping...")
        result = await scrape_property_stealth(URL, headless=True)

        # Converter para dict se for objeto
        if hasattr(result, "to_dict"):
            data = result.to_dict()
        elif hasattr(result, "__dict__"):
            data = result.__dict__
        else:
            data = result

        print("\n✅ EXTRAÇÃO COMPLETA!")
        print(f"\n📊 Dados extraídos:")
        print(f"  • Título: {data.get('title', 'N/A')}")
        print(f"  • Bairro: {data.get('neighborhood', 'N/A')}")
        print(f"  • Endereço: {data.get('address', 'N/A')}")
        print(f"  • Área Total: {data.get('area_total_m2', 'N/A')} m²")

        price = data.get("price_brl")
        if price:
            print(f"  • Preço: R$ {price:,.2f}")
        else:
            print(f"  • Preço: N/A")

        imgs = data.get("images") or []
        feats = data.get("features") or []
        print(f"  • Imagens: {len(imgs)}")
        print(f"  • Características: {len(feats)}")

        # Salvar
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        print(f"\n💾 JSON salvo: {OUTPUT.absolute()}")

        # Mostrar imagens
        if imgs:
            print(f"\n🖼️  PRIMEIRAS IMAGENS:")
            for idx, img in enumerate(imgs[:3], 1):
                print(f"  {idx}. {img}")

        print("\n" + "=" * 80)

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
