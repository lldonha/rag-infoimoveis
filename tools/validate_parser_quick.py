#!/usr/bin/env python3
"""
Teste Rápido: Parser em 2 Imóveis Diferentes
Valida que o parser funciona em tipos variados
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

from playwright.async_api import async_playwright

# URLs de teste - tipos diferentes
TESTS = [
    {
        "url": "https://www.infoimoveis.com.br/imovel/venda-apartamento-centro/141448",
        "tipo": "Apartamento",
        "descricao": "Apartamento de alto padrão",
    },
    {
        "url": "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-autonomista/143953",
        "tipo": "Casa",
        "descricao": "Casa térrea com piscina",
    },
]

OUTPUT_DIR = Path(".tmp/validation_tests")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def quick_scrape(url: str, test_name: str):
    """Scrape rápido focado em validação"""

    data = {"url": url, "fields_found": {}}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )
        page = await context.new_page()

        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )

        print(f"  🌐 Navegando...")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(10000)

        # Testar campos principais
        tests_results = {}

        # Título
        try:
            title = await page.locator("h1").first.inner_text()
            tests_results["titulo"] = "✅" if title else "❌"
            data["fields_found"]["titulo"] = title.strip() if title else None
        except:
            tests_results["titulo"] = "❌"

        # Preço
        try:
            price = await page.locator("#priceImovel").get_attribute("value")
            tests_results["preco"] = "✅" if price else "❌"
            data["fields_found"]["preco"] = float(price) if price else None
        except:
            tests_results["preco"] = "❌"

        # Tipo
        try:
            tipo = await page.locator(
                'tr:has-text("Tipo") td:nth-child(2)'
            ).first.inner_text()
            tests_results["tipo"] = "✅" if tipo else "❌"
            data["fields_found"]["tipo"] = tipo.strip() if tipo else None
        except:
            tests_results["tipo"] = "❌"

        # Bairro
        try:
            bairro = await page.locator(
                'tr:has-text("Bairro") td:nth-child(2)'
            ).first.inner_text()
            tests_results["bairro"] = "✅" if bairro else "❌"
            data["fields_found"]["bairro"] = bairro.strip() if bairro else None
        except:
            tests_results["bairro"] = "❌"

        # Área
        try:
            area = await page.locator(
                'tr:has-text("Área total") td:nth-child(2)'
            ).first.inner_text()
            tests_results["area"] = "✅" if area else "❌"
            data["fields_found"]["area"] = area.strip() if area else None
        except:
            tests_results["area"] = "❌"

        # Anunciante
        try:
            anunciante = await page.locator(
                ".anunciante .nome, span.nome"
            ).first.inner_text()
            tests_results["anunciante"] = "✅" if anunciante else "❌"
            data["fields_found"]["anunciante"] = (
                anunciante.strip() if anunciante else None
            )
        except:
            tests_results["anunciante"] = "❌"

        # Características
        try:
            items = await page.locator(".itens li").all()
            features = []
            for item in items:
                text = await item.inner_text()
                if text:
                    features.append(text.strip())
            tests_results["caracteristicas"] = "✅" if features else "❌"
            data["fields_found"]["caracteristicas"] = features
        except:
            tests_results["caracteristicas"] = "❌"

        # Observações
        try:
            obs = await page.locator(
                ".observacoes .texto, .observacoes p.texto"
            ).first.inner_text()
            tests_results["observacoes"] = "✅" if obs else "❌"
            data["fields_found"]["observacoes"] = obs.strip() if obs else None
        except:
            tests_results["observacoes"] = "❌"

        # Imagens
        try:
            imgs = await page.locator(
                'img[src*="/fotos/"], img[src*="stored/imoveis"]'
            ).all()
            img_count = len(imgs)
            tests_results["imagens"] = f"✅ ({img_count})" if img_count > 0 else "❌"
            data["fields_found"]["imagens_count"] = img_count
        except:
            tests_results["imagens"] = "❌"

        await browser.close()

        # Calcular sucesso
        success_count = sum(1 for v in tests_results.values() if "✅" in str(v))
        total_tests = len(tests_results)
        data["success_rate"] = (
            f"{success_count}/{total_tests} ({success_count / total_tests * 100:.0f}%)"
        )
        data["tests"] = tests_results

        return data, tests_results


async def main():
    print("=" * 80)
    print("🧪 VALIDAÇÃO DO PARSER - 2 IMÓVEIS DIFERENTES")
    print("=" * 80)

    results = []

    for idx, test in enumerate(TESTS, 1):
        print(f"\n{'=' * 80}")
        print(f"📍 TESTE {idx}/2: {test['tipo']} - {test['descricao']}")
        print(f"{'=' * 80}")
        print(f"   URL: {test['url']}\n")

        data, tests = await quick_scrape(test["url"], f"test_{idx}")

        # Mostrar resultados
        print(f"\n  📊 Campos testados:")
        for field, result in tests.items():
            print(f"    {field:20s} {result}")

        print(f"\n  ✅ Taxa de sucesso: {data['success_rate']}")

        results.append({"test_name": test["tipo"], "url": test["url"], "results": data})

        # Salvar resultado individual
        output_file = OUTPUT_DIR / f"test_{idx}_{test['tipo'].lower()}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  💾 Salvo: {output_file}")

        if idx < len(TESTS):
            print(f"\n  ⏳ Aguardando 12s antes do próximo...")
            await asyncio.sleep(12)

    # Resumo final
    print("\n" + "=" * 80)
    print("✅ VALIDAÇÃO COMPLETA!")
    print("=" * 80)

    for idx, result in enumerate(results, 1):
        print(f"\n{idx}. {result['test_name']}")
        print(f"   Taxa: {result['results']['success_rate']}")

    # Salvar resumo
    summary_file = OUTPUT_DIR / "validation_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Resumo completo: {summary_file}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
