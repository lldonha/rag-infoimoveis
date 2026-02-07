#!/usr/bin/env python3
"""
Teste DIRETO de 5 imóveis - Sem verificação de janela de tempo
"""
import asyncio
import sys
from datetime import datetime
sys.path.insert(0, 'e:/rag_infoimoeveis')

from playwright.async_api import async_playwright
from tools.rate_limiter import SmartRateLimiter
from tools.scraper_production import scrape_property_safe

# URLs do sitemap
URLS = [
    'https://www.infoimoveis.com.br/imovel/venda-area-jardim-bela-vista/55162',
    'https://www.infoimoveis.com.br/imovel/venda-terreno-jardim-das-reginas/123613',
    'https://www.infoimoveis.com.br/imovel/aluguel-imovel-comercial-centro/132114',
    'https://www.infoimoveis.com.br/imovel/venda-apartamento-centro/141448',
    'https://www.infoimoveis.com.br/imovel/venda-casa-terrea-autonomista/143953'
]

async def main():
    print("=" * 70)
    print("🚀 TESTE DIRETO: 5 Imóveis do Sitemap (Sem Janela Segura)")
    print("=" * 70)
    print(f"⏰ Início: {datetime.now().strftime('%H:%M:%S')}")
    print(f"🔒 Modo: Stealth + Headless")
    print()
    
    # Rate limiter mais agressivo para teste
    rate_limiter = SmartRateLimiter(max_per_hour=100, min_delay=3.0, max_delay=6.0)
    
    results = []
    
    async with async_playwright() as p:
        for i, url in enumerate(URLS, 1):
            print(f"\n[{i}/{len(URLS)}] {url.split('/')[-1]}")
            print("-" * 50)
            
            try:
                result = await scrape_property_safe(
                    playwright=p,
                    url=url,
                    rate_limiter=rate_limiter,
                    use_cookies=True,
                    save_to_db=False,
                    use_stealth=True
                )
                
                if result:
                    completeness = result.get('data_completeness', 0)
                    title = result.get('title', 'N/A')[:50]
                    results.append({'url': url, 'success': True, 'completeness': completeness})
                    print(f"  ✅ Sucesso | Completude: {completeness*100:.0f}%")
                    print(f"     Título: {title}...")
                else:
                    results.append({'url': url, 'success': False, 'completeness': 0})
                    print(f"  ❌ Falhou: Sem dados")
                    
            except Exception as e:
                results.append({'url': url, 'success': False, 'completeness': 0})
                print(f"  ❌ Erro: {str(e)[:50]}")
    
    # Resumo
    success = sum(1 for r in results if r['success'])
    avg_completeness = sum(r['completeness'] for r in results if r['success']) / max(success, 1)
    
    print()
    print("=" * 70)
    print("📊 RESULTADO FINAL")
    print("=" * 70)
    print(f"  ✅ Sucesso: {success}/{len(URLS)} ({success/len(URLS)*100:.0f}%)")
    print(f"  📈 Completude média: {avg_completeness*100:.0f}%")
    print(f"  ⏰ Fim: {datetime.now().strftime('%H:%M:%S')}")
    
    if success >= 4:
        print("\n🎉 SISTEMA FUNCIONANDO CORRETAMENTE!")
    else:
        print("\n⚠️ ATENÇÃO: Alguns imóveis falharam")
    
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
