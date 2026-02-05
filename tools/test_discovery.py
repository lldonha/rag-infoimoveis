#!/usr/bin/env python3
"""Teste do Discovery Filtrado"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from discovery_filtered import discover_by_preset


async def main():
    print('🔍 Testando Discovery Filtrado')
    print('Preset: segredo_100_200k (Casa térrea, Segredo, R$ 100k-200k)')
    print('Máximo: 2 páginas\n')
    print('=' * 70)

    try:
        urls = await discover_by_preset('segredo_100_200k', max_pages=2)

        print(f'\n📊 Resultado:')
        print(f'✅ {len(urls)} imóveis encontrados\n')

        if urls:
            print('Primeiros 10 imóveis:')
            for i, url in enumerate(urls[:10], 1):
                print(f'  {i}. {url}')

        print('\n' + '=' * 70)
        if len(urls) >= 10:
            print('✅ PASSOU! Encontrados 10+ imóveis')
            return True
        else:
            print(f'❌ FALHOU! Apenas {len(urls)} imóveis encontrados (meta: 10+)')
            return False

    except Exception as e:
        print(f'\n❌ Erro: {e}')
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    passed = asyncio.run(main())
    sys.exit(0 if passed else 1)
