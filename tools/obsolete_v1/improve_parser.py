#!/usr/bin/env python3
"""
Melhoria do Parser - Aumentar completude de 15% → 70%+
====================================================
Analisa páginas reais e melhora extração de dados
"""

import asyncio
import sys
import os
from playwright.async_api import async_playwright

sys.path.append(os.path.dirname(__file__))

# URL de teste (sabemos que funciona)
TEST_URL = "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-4-quartos-jardim-mansoes-campo-grande-ms-220m2-id-2788808"


async def inspect_page_structure(url: str):
    """Inspeciona estrutura HTML da página para melhorar parser"""

    print(f"\n🔍 ANALISANDO ESTRUTURA DA PÁGINA")
    print(f"{'='*70}\n")
    print(f"URL: {url}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(url, timeout=30000, wait_until="networkidle")

            # ============================================
            # 1. CARACTERÍSTICAS (bedrooms, bathrooms, etc)
            # ============================================
            print("📋 1. CARACTERÍSTICAS:")
            print("-" * 70)

            # Tentar diferentes seletores para características
            selectors_to_try = [
                # Lista de características
                ".features-list li",
                ".property-features li",
                "[class*='feature'] li",
                ".caracteristicas li",

                # Itens individuais
                "[class*='quartos']",
                "[class*='dormitorios']",
                "[class*='bedrooms']",
                "[class*='banheiros']",
                "[class*='bathrooms']",
                "[class*='vagas']",
                "[class*='garagem']",
                "[class*='parking']",

                # Ícones com texto
                "i.fa-bed + *",
                "i.fa-bath + *",
                "i.fa-car + *",
            ]

            for selector in selectors_to_try:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"\n✅ Selector: {selector} ({len(elements)} elementos)")
                        for i, el in enumerate(elements[:5], 1):
                            text = await el.inner_text()
                            print(f"   {i}. {text.strip()[:80]}")
                except:
                    pass

            # ============================================
            # 2. PREÇO E VALORES
            # ============================================
            print(f"\n\n💰 2. PREÇO E VALORES:")
            print("-" * 70)

            price_selectors = [
                ".price",
                "[class*='preco']",
                "[class*='valor']",
                "[class*='price']",
                "h2:has-text('R$')",
                "span:has-text('R$')",
            ]

            for selector in price_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"\n✅ Selector: {selector}")
                        for i, el in enumerate(elements[:3], 1):
                            text = await el.inner_text()
                            if 'R$' in text:
                                print(f"   {i}. {text.strip()[:100]}")
                except:
                    pass

            # ============================================
            # 3. DESCRIÇÃO E FEATURES
            # ============================================
            print(f"\n\n📝 3. DESCRIÇÃO E FEATURES:")
            print("-" * 70)

            desc_selectors = [
                "#description",
                ".description",
                "[class*='descricao']",
                "[class*='sobre']",
                "article",
            ]

            for selector in desc_selectors:
                try:
                    el = await page.query_selector(selector)
                    if el:
                        text = await el.inner_text()
                        if len(text) > 50:
                            print(f"\n✅ Selector: {selector}")
                            print(f"   Tamanho: {len(text)} chars")
                            print(f"   Preview: {text.strip()[:200]}...")
                            break
                except:
                    pass

            # ============================================
            # 4. IMAGENS
            # ============================================
            print(f"\n\n🖼️  4. IMAGENS:")
            print("-" * 70)

            img_selectors = [
                ".property-images img",
                ".gallery img",
                "[class*='foto'] img",
                "[class*='imagem'] img",
                "img[src*='imovel']",
            ]

            all_imgs = []
            for selector in img_selectors:
                try:
                    imgs = await page.query_selector_all(selector)
                    if imgs:
                        print(f"\n✅ Selector: {selector} ({len(imgs)} imagens)")
                        for i, img in enumerate(imgs[:3], 1):
                            src = await img.get_attribute('src')
                            if src:
                                all_imgs.append(src)
                                print(f"   {i}. {src[:80]}...")
                except:
                    pass

            print(f"\n   Total único de imagens: {len(set(all_imgs))}")

            # ============================================
            # 5. DADOS ESTRUTURADOS (schema.org)
            # ============================================
            print(f"\n\n🏗️  5. DADOS ESTRUTURADOS:")
            print("-" * 70)

            # JSON-LD
            jsonld = await page.query_selector_all('script[type="application/ld+json"]')
            if jsonld:
                print(f"\n✅ JSON-LD encontrado ({len(jsonld)} scripts)")
                for i, script in enumerate(jsonld, 1):
                    content = await script.inner_text()
                    print(f"\n   Script {i}:")
                    print(f"   {content[:300]}...")
            else:
                print("\n❌ Nenhum JSON-LD encontrado")

            # Microdata
            itemprops = await page.query_selector_all('[itemprop]')
            if itemprops:
                print(f"\n✅ Microdata encontrado ({len(itemprops)} itemprop)")
                seen = set()
                for el in itemprops[:10]:
                    prop = await el.get_attribute('itemprop')
                    if prop and prop not in seen:
                        seen.add(prop)
                        content = await el.inner_text()
                        print(f"   • {prop}: {content.strip()[:60]}")

            # ============================================
            # 6. HTML COMPLETO (para análise)
            # ============================================
            print(f"\n\n💾 6. SALVANDO HTML COMPLETO:")
            print("-" * 70)

            html = await page.content()
            output_file = ".tmp/page_structure.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)

            print(f"✅ HTML salvo em: {output_file}")
            print(f"   Tamanho: {len(html):,} bytes")

            print(f"\n{'='*70}\n")

        finally:
            await browser.close()


async def test_improved_selectors():
    """Testa novos seletores melhorados"""

    print(f"\n🧪 TESTANDO SELETORES MELHORADOS")
    print(f"{'='*70}\n")

    # TODO: Implementar parser melhorado baseado na análise
    pass


async def main():
    """Menu principal"""
    import argparse

    parser = argparse.ArgumentParser(description="Melhorar parser de imóveis")
    parser.add_argument("--inspect", action="store_true", help="Inspecionar estrutura da página")
    parser.add_argument("--test", action="store_true", help="Testar parser melhorado")
    parser.add_argument("--url", type=str, help="URL customizada para análise")

    args = parser.parse_args()

    url = args.url or TEST_URL

    if args.inspect:
        await inspect_page_structure(url)
    elif args.test:
        await test_improved_selectors()
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
