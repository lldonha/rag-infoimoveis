#!/usr/bin/env python3
"""
Teste de Qualidade do Parser COM STEALTH
==========================================
Usa scraper_stealth.py para testar qualidade do parser
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(__file__))

from scraper_stealth import test_stealth_single


# URLs de teste (variadas)
TEST_URLS = [
    "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-4-quartos-jardim-mansoes-campo-grande-ms-220m2-id-2788808",
    "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-3-quartos-coronel-antonino-campo-grande-ms-158m2-id-2814468",
    "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-3-quartos-parque-dos-poderes-campo-grande-ms-105m2-id-2756732",
]


async def main():
    """Testa qualidade do parser COM STEALTH em múltiplas URLs"""

    print(f"\n{'='*70}")
    print(f"🧪 TESTE DE QUALIDADE DO PARSER (COM STEALTH)")
    print(f"{'='*70}\n")

    results = []

    for i, url in enumerate(TEST_URLS, 1):
        print(f"\n[{i}/{len(TEST_URLS)}]")
        result = await test_stealth_single(url, headless=True)
        if result['success']:
            results.append(result)

        # Delay entre requests
        if i < len(TEST_URLS):
            print(f"\n⏳ Aguardando 5s...")
            await asyncio.sleep(5)

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
    completudes = [r['completeness'] for r in results]
    avg_comp = sum(completudes) / len(completudes)
    print(f"📈 Completude média: {avg_comp:.1f}%")

    # Completude individual
    print(f"\n📋 Por imóvel:")
    for i, r in enumerate(results, 1):
        title = r['title'][:50] if r.get('title') else "Sem título"
        comp = r['completeness']
        print(f"  {i}. {title}... → {comp}%")

    # Conclusão
    print(f"\n{'='*70}")
    if avg_comp >= 70:
        print(f"🎉 EXCELENTE! Parser atingiu meta de 70%+")
        print(f"✅ Parser está pronto para produção!")
    elif avg_comp >= 50:
        print(f"✅ BOM! Parser está acima de 50%, pode melhorar")
    else:
        print(f"⚠️  ATENÇÃO! Completude abaixo de 50%, precisa melhorar")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(main())
