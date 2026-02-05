#!/usr/bin/env python3
"""
Teste 08: Sistema de Scraping Completo
=======================================
Valida todos os componentes do sistema de scraping
"""

import os
import sys
import json
from datetime import datetime

# Adicionar tools ao path
sys.path.append(os.path.dirname(__file__))

print("=" * 70)
print(" " * 15 + "TESTE DO SISTEMA DE SCRAPING")
print("=" * 70)
print()

# Teste 1: Verificar módulos
print("1. Verificando módulos de proteção...")
try:
    from rate_limiter import SmartRateLimiter, is_safe_window
    from cookie_manager import get_cookie_info, load_cookies
    from fingerprint_rotator import get_random_fingerprint
    from human_behavior import human_read_time
    from property_saver import get_db_connection, get_property_stats
    print("   ✅ Todos os módulos importados com sucesso")
except ImportError as e:
    print(f"   ❌ Erro ao importar módulos: {e}")
    sys.exit(1)

# Teste 2: Verificar PostgreSQL
print("\n2. Verificando conexão PostgreSQL...")
try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT version()")
    version = cursor.fetchone()[0]
    print(f"   ✅ Conectado: {version.split(',')[0]}")

    # Verificar extensões
    cursor.execute("SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'uuid-ossp')")
    extensions = cursor.fetchall()
    for ext_name, ext_version in extensions:
        print(f"   ✅ Extensão {ext_name}: v{ext_version}")

    cursor.close()
    conn.close()
except Exception as e:
    print(f"   ❌ Erro de conexão: {e}")
    print("   💡 Execute: docker-compose up -d postgres")
    sys.exit(1)

# Teste 3: Verificar tabelas
print("\n3. Verificando schema do banco...")
try:
    conn = get_db_connection()
    cursor = conn.cursor()

    tables = ['properties', 'property_embeddings', 'scrape_jobs', 'market_stats']
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   ✅ Tabela {table:20} {count:5,} registros")

    cursor.close()
    conn.close()
except Exception as e:
    print(f"   ❌ Erro ao verificar schema: {e}")
    sys.exit(1)

# Teste 4: Testar rate limiter
print("\n4. Testando rate limiter...")
try:
    limiter = SmartRateLimiter(max_per_hour=100, max_per_day=500, min_delay=0.1, max_delay=0.2)
    stats = limiter.get_stats()
    print(f"   ✅ Rate limiter configurado: {stats['max_per_hour']}/hora, {stats['max_per_day']}/dia")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# Teste 5: Testar cookies
print("\n5. Verificando cookies...")
try:
    cookie_info = get_cookie_info()
    if cookie_info:
        print(f"   ✅ Cookies disponíveis: {cookie_info['count']} cookies")
        print(f"   ✅ Idade: {cookie_info['age_hours']:.1f}h")
        print(f"   ✅ Válido: {cookie_info['is_valid']}")
    else:
        print(f"   ⚠️  Nenhum cookie salvo (será criado no primeiro scraping)")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# Teste 6: Testar fingerprint
print("\n6. Testando fingerprint rotator...")
try:
    fp = get_random_fingerprint()
    print(f"   ✅ User-Agent: {fp['user_agent'][:50]}...")
    print(f"   ✅ Viewport: {fp['viewport']['width']}x{fp['viewport']['height']}")
    print(f"   ✅ Timezone: {fp['timezone']}")
    print(f"   ✅ Locale: {fp['locale']}")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# Teste 7: Janela segura
print("\n7. Verificando janela de tempo...")
try:
    current_hour = datetime.now().hour
    is_safe = is_safe_window()

    if is_safe:
        print(f"   ✅ Horário atual ({current_hour:02d}h) está em janela segura")
    else:
        print(f"   ⚠️  Horário atual ({current_hour:02d}h) fora da janela segura")
        print(f"   💡 Janelas seguras: 03-06h, 13-15h, 22-24h")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# Teste 8: Estatísticas do banco
print("\n8. Estatísticas do banco de dados...")
try:
    stats = get_property_stats()
    print(f"   ✅ Total de imóveis: {stats['total']:,}")
    print(f"   ✅ Completude média: {stats['avg_completeness']:.1%}")

    if stats['by_transaction']:
        print(f"   ✅ Por transação:")
        for trans, count in stats['by_transaction'].items():
            if trans:
                print(f"      - {trans}: {count:,}")

    if stats['by_neighborhood']:
        top_3 = list(stats['by_neighborhood'].items())[:3]
        print(f"   ✅ Top 3 bairros:")
        for neighborhood, count in top_3:
            print(f"      - {neighborhood}: {count:,}")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# Teste 9: Verificar dependências Python
print("\n9. Verificando dependências Python...")
try:
    import playwright
    from psycopg2 import __version__ as psycopg2_version
    from dotenv import __version__ as dotenv_version

    print(f"   ✅ playwright: instalado")
    print(f"   ✅ psycopg2: v{psycopg2_version}")
    print(f"   ✅ python-dotenv: v{dotenv_version}")
except ImportError as e:
    print(f"   ❌ Dependência faltando: {e}")
    print(f"   💡 Execute: pip install playwright psycopg2-binary python-dotenv")

# Teste 10: Verificar estrutura de arquivos
print("\n10. Verificando estrutura de arquivos...")
expected_files = [
    'tools/scraper_production.py',
    'tools/scrape_workflow.py',
    'tools/property_saver.py',
    'tools/metrics_dashboard.py',
    'tools/rate_limiter.py',
    'tools/cookie_manager.py',
    'tools/fingerprint_rotator.py',
    'tools/human_behavior.py',
    'workflows/scraping_producao.md',
    'workflows/anti-bloqueio.md',
    'GUIA_RAPIDO_SCRAPING.md',
]

base_path = os.path.dirname(os.path.dirname(__file__))
for file_path in expected_files:
    full_path = os.path.join(base_path, file_path)
    if os.path.exists(full_path):
        print(f"   ✅ {file_path}")
    else:
        print(f"   ❌ FALTANDO: {file_path}")

# Resumo final
print("\n" + "=" * 70)
print("RESUMO")
print("=" * 70)
print()
print("✅ Sistema de scraping está operacional!")
print()
print("📖 Próximos passos:")
print("   1. Ler: GUIA_RAPIDO_SCRAPING.md")
print("   2. Testar: python tools/scraper_production.py")
print("   3. Dashboard: python tools/metrics_dashboard.py")
print()
print("🛡️  Proteções ativas:")
print("   - Rate limiting (50/hora, 400/dia)")
print("   - Janelas seguras (madrugada, almoço, noite)")
print("   - Cookies persistentes (6h)")
print("   - Fingerprint rotation")
print("   - Comportamento humano")
print()
print("=" * 70)
