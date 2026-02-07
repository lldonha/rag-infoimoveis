#!/usr/bin/env python3
"""
Teste de Qualidade do Parser
============================
Testa o parser atual e compara completude dos dados
"""

import asyncio
import sys
import os
from playwright.async_api import async_playwright

sys.path.append(os.path.dirname(__file__))

from scraper_production import parse_property_page, PropertyData


# URLs de teste (variadas)
TEST_URLS = [
    "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-4-quartos-jardim-mansoes-campo-grande-ms-220m2-id-2788808",
    "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-3-quartos-coronel-antonino-campo-grande-ms-158m2-id-2814468",
    "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-3-quartos-parque-dos-poderes-campo-grande-ms-105m2-id-2756732",
]


async def test_single_url(url: str, browser) -> PropertyData:
    """Testa parser em uma URL"""

    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    page = await context.new_page()

    try:
        print(f"\n{'─'*70}")
        print(f"🔄 Testando: {url[:80]}...")

        await page.goto(url, timeout=45000, wait_until="domcontentloaded")

        # Parse usando função atual
        property_data = await parse_property_page(page, url)

        if property_data:
            comp = property_data.completeness * 100
            print(f"✅ Sucesso! Completude: {comp:.0f}%")

            # Mostrar campos preenchidos
            data_dict = property_data.to_dict()
            filled = {k: v for k, v in data_dict.items() if v not in [None, '', []]}

            print(f"\n📊 Campos preenchidos ({len(filled)}):")
            for key, val in filled.items():
                if key == 'description':
                    val_str = f"{str(val)[:50]}..." if len(str(val)) > 50 else str(val)
                elif key == 'images':
                    val_str = f"{len(val)} imagens" if isinstance(val, list) else str(val)
                else:
                    val_str = str(val)
                print(f"  • {key}: {val_str}")

            return property_data
        else:
            print(f"❌ Falha ao extrair dados")
            return None

    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

    finally:
        await context.close()


async def main():
    """Testa qualidade do parser em múltiplas URLs"""

    print(f"\n{'='*70}")
    print(f"🧪 TESTE DE QUALIDADE DO PARSER")
    print(f"{'='*70}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        results = []

        for i, url in enumerate(TEST_URLS, 1):
            print(f"\n[{i}/{len(TEST_URLS)}]")
            result = await test_single_url(url, browser)
            if result:
                results.append(result)

            # Delay entre requests
            if i < len(TEST_URLS):
                print(f"\n⏳ Aguardando 5s...")
                await asyncio.sleep(5)

        await browser.close()

        # ============================================
        # RELATÓRIO FINAL
        # ============================================
        print(f"\n\n{'='*70}")
        print(f"📊 RELATÓRIO FINAL")
        print(f"{'='*70}\n")

        if not results:
            print("❌ Nenhum imóvel scrapado com sucesso")
            return

        print(f"✅ Total scrapado: {len(results)}/{len(TEST_URLS)}")
        print(f"   Taxa de sucesso: {len(results)/len(TEST_URLS):.1%}\n")

        # Completude média
        avg_comp = sum(r.completeness for r in results) / len(results) * 100
        print(f"📈 Completude média: {avg_comp:.1f}%")

        # Completude individual
        print(f"\n📋 Por imóvel:")
        for i, r in enumerate(results, 1):
            comp = r.completeness * 100
            title = r.title[:50] if r.title else "Sem título"
            print(f"  {i}. {title}... → {comp:.0f}%")

        # Campos mais preenchidos
        print(f"\n📊 Taxa de preenchimento por campo:")
        all_fields = {}
        for r in results:
            data = r.to_dict()
            for key, val in data.items():
                if key not in all_fields:
                    all_fields[key] = 0
                if val not in [None, '', []]:
                    all_fields[key] += 1

        for key, count in sorted(all_fields.items(), key=lambda x: -x[1]):
            pct = (count / len(results)) * 100
            icon = "✅" if pct >= 80 else "⚠️" if pct >= 50 else "❌"
            print(f"  {icon} {key:25s} {count}/{len(results)} ({pct:.0f}%)")

        # Conclusão
        print(f"\n{'='*70}")
        if avg_comp >= 70:
            print(f"🎉 EXCELENTE! Parser atingiu meta de 70%+")
        elif avg_comp >= 50:
            print(f"✅ BOM! Parser está acima de 50%, pode melhorar")
        else:
            print(f"⚠️  ATENÇÃO! Completude abaixo de 50%, precisa melhorar")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(main())
