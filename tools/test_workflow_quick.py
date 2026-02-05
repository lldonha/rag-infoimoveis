"""
Teste Rápido do Workflow - Apenas 1 imóvel
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from tools.scraper_stealth import test_stealth_single

async def main():
    print("🧪 Teste Rápido - Workflow com Stealth")
    print("=" * 60)

    test_url = "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-giocondo-orsi/557442"

    print(f"\n🔍 Testando URL: {test_url}")
    print(f"🔒 Modo: Stealth (headless=True)")
    print(f"\nAguarde...\n")

    await test_stealth_single(test_url, headless=True)

    print("\n" + "=" * 60)
    print("✅ Teste concluído!")

if __name__ == "__main__":
    asyncio.run(main())
