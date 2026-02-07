#!/usr/bin/env python3
"""
Teste de 5 imóveis do sitemap descoberto
"""
import asyncio
import sys
sys.path.insert(0, 'e:/rag_infoimoeveis')

from tools.scraper_production import scrape_multiple_properties

# URLs extraídas do sitemap.xml
URLS = [
    'https://www.infoimoveis.com.br/imovel/venda-area-jardim-bela-vista/55162',
    'https://www.infoimoveis.com.br/imovel/venda-terreno-jardim-das-reginas/123613',
    'https://www.infoimoveis.com.br/imovel/aluguel-imovel-comercial-centro/132114',
    'https://www.infoimoveis.com.br/imovel/venda-apartamento-centro/141448',
    'https://www.infoimoveis.com.br/imovel/venda-casa-terrea-autonomista/143953'
]

async def main():
    print("🚀 Teste: 5 Imóveis do Sitemap")
    print("=" * 60)
    print(f"URLs a testar: {len(URLS)}")
    for i, url in enumerate(URLS, 1):
        print(f"  {i}. {url.split('/')[-1]}")
    print("=" * 60)
    print()
    
    result = await scrape_multiple_properties(
        urls=URLS,
        max_per_session=10,
        save_to_db=False,  # Não salvar, apenas testar
        use_stealth=True
    )
    
    print()
    print("=" * 60)
    print("📊 RESULTADO FINAL")
    print("=" * 60)
    print(f"  ✅ Sucesso: {result['success']}/{result['total']}")
    print(f"  📈 Taxa: {result['success_rate']*100:.0f}%")
    print(f"  📊 Completude média: {result['avg_completeness']*100:.0f}%")
    print(f"  ❌ Erros: {result['failed']}")
    print()
    
    if result['success_rate'] >= 0.8:
        print("🎉 TESTE PASSOU! Sistema funcionando corretamente.")
    else:
        print("⚠️ ATENÇÃO: Taxa de sucesso abaixo de 80%")

if __name__ == "__main__":
    asyncio.run(main())
