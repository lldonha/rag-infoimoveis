#!/usr/bin/env python3
"""
Metrics Dashboard
=================
Dashboard de monitoramento do scraping
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """Cria conexão com PostgreSQL"""
    return psycopg2.connect(
        host='localhost',
        port=5433,
        database='infoimoveis',
        user='postgres',
        password=os.getenv('POSTGRES_PASSWORD', 'infoimoveis2024')
    )


def get_scraping_metrics() -> Dict:
    """Métricas de scraping do banco"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Total de imóveis
        cursor.execute("SELECT COUNT(*) as total FROM properties")
        total = cursor.fetchone()['total']

        # Imóveis scraped nas últimas 24h
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM properties
            WHERE scraped_at >= NOW() - INTERVAL '24 hours'
        """)
        last_24h = cursor.fetchone()['count']

        # Imóveis scraped na última semana
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM properties
            WHERE scraped_at >= NOW() - INTERVAL '7 days'
        """)
        last_7d = cursor.fetchone()['count']

        # Completude média
        cursor.execute("""
            SELECT AVG(data_completeness) as avg_completeness
            FROM properties
        """)
        avg_completeness = cursor.fetchone()['avg_completeness'] or 0

        # Imóveis com imagens
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM properties
            WHERE images IS NOT NULL AND jsonb_array_length(images) > 0
        """)
        with_images = cursor.fetchone()['count']

        # Distribuição por completude
        cursor.execute("""
            SELECT
                CASE
                    WHEN data_completeness >= 0.8 THEN 'alta'
                    WHEN data_completeness >= 0.5 THEN 'media'
                    ELSE 'baixa'
                END as quality,
                COUNT(*) as count
            FROM properties
            GROUP BY quality
        """)
        by_quality = {row['quality']: row['count'] for row in cursor.fetchall()}

        return {
            'total_properties': total,
            'last_24h': last_24h,
            'last_7d': last_7d,
            'avg_completeness': float(avg_completeness),
            'with_images': with_images,
            'by_quality': by_quality,
        }

    finally:
        cursor.close()
        conn.close()


def get_market_insights() -> Dict:
    """Insights de mercado dos dados coletados"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Preço médio por transação
        cursor.execute("""
            SELECT
                transaction_type,
                COUNT(*) as count,
                AVG(price_brl) as avg_price,
                MIN(price_brl) as min_price,
                MAX(price_brl) as max_price
            FROM properties
            WHERE price_brl IS NOT NULL
            GROUP BY transaction_type
        """)
        by_transaction = {row['transaction_type']: dict(row) for row in cursor.fetchall()}

        # Top 10 bairros mais caros (venda)
        cursor.execute("""
            SELECT
                neighborhood,
                COUNT(*) as count,
                AVG(price_per_m2) as avg_price_m2
            FROM properties
            WHERE transaction_type = 'venda'
              AND price_per_m2 IS NOT NULL
              AND neighborhood IS NOT NULL
            GROUP BY neighborhood
            HAVING COUNT(*) >= 3
            ORDER BY avg_price_m2 DESC
            LIMIT 10
        """)
        expensive_neighborhoods = [dict(row) for row in cursor.fetchall()]

        # Distribuição por tipo de imóvel
        cursor.execute("""
            SELECT
                property_type,
                COUNT(*) as count,
                AVG(price_brl) as avg_price
            FROM properties
            WHERE property_type IS NOT NULL
            GROUP BY property_type
            ORDER BY count DESC
            LIMIT 10
        """)
        by_type = [dict(row) for row in cursor.fetchall()]

        # Oportunidades (abaixo do mercado)
        cursor.execute("""
            WITH neighborhood_avg AS (
                SELECT
                    neighborhood,
                    property_type,
                    AVG(price_per_m2) as avg_price_m2
                FROM properties
                WHERE price_per_m2 IS NOT NULL
                  AND neighborhood IS NOT NULL
                  AND property_type IS NOT NULL
                GROUP BY neighborhood, property_type
                HAVING COUNT(*) >= 3
            )
            SELECT
                p.id,
                p.title,
                p.neighborhood,
                p.property_type,
                p.price_brl,
                p.price_per_m2,
                na.avg_price_m2 as market_avg,
                ROUND((p.price_per_m2 - na.avg_price_m2) / na.avg_price_m2 * 100, 1) as discount_pct
            FROM properties p
            JOIN neighborhood_avg na
              ON p.neighborhood = na.neighborhood
              AND p.property_type = na.property_type
            WHERE p.price_per_m2 < na.avg_price_m2 * 0.85
            ORDER BY discount_pct
            LIMIT 10
        """)
        opportunities = [dict(row) for row in cursor.fetchall()]

        return {
            'by_transaction': by_transaction,
            'expensive_neighborhoods': expensive_neighborhoods,
            'by_type': by_type,
            'opportunities': opportunities,
        }

    finally:
        cursor.close()
        conn.close()


def print_dashboard():
    """Imprime dashboard formatado no terminal"""
    print("\n" + "="*70)
    print(" " * 20 + "DASHBOARD - InfoImóveis RAG")
    print("="*70)

    # Métricas de scraping
    print("\n📊 MÉTRICAS DE SCRAPING")
    print("-" * 70)

    try:
        metrics = get_scraping_metrics()

        print(f"Total de imóveis:        {metrics['total_properties']:,}")
        print(f"Últimas 24h:            {metrics['last_24h']:,}")
        print(f"Última semana:          {metrics['last_7d']:,}")
        print(f"Completude média:       {metrics['avg_completeness']:.1%}")
        print(f"Com imagens:            {metrics['with_images']:,} ({metrics['with_images']/metrics['total_properties']*100:.1f}%)")

        print(f"\nDistribuição por qualidade:")
        for quality, count in sorted(metrics['by_quality'].items()):
            pct = count / metrics['total_properties'] * 100
            print(f"  {quality.capitalize():10} {count:5,} ({pct:5.1f}%)")

    except Exception as e:
        print(f"❌ Erro ao buscar métricas: {e}")

    # Insights de mercado
    print("\n" + "="*70)
    print("💰 INSIGHTS DE MERCADO")
    print("-" * 70)

    try:
        insights = get_market_insights()

        # Por transação
        print("\nPor tipo de transação:")
        for trans_type, data in insights['by_transaction'].items():
            if trans_type:
                print(f"\n  {trans_type.upper()}:")
                print(f"    Quantidade:     {data['count']:,}")
                print(f"    Preço médio:    R$ {data['avg_price']:,.2f}")
                print(f"    Faixa:          R$ {data['min_price']:,.0f} - R$ {data['max_price']:,.0f}")

        # Bairros mais caros
        print(f"\nTop 5 bairros mais caros (R$/m²):")
        for i, item in enumerate(insights['expensive_neighborhoods'][:5], 1):
            print(f"  {i}. {item['neighborhood']:20} R$ {item['avg_price_m2']:8,.2f}/m² ({item['count']} imóveis)")

        # Oportunidades
        if insights['opportunities']:
            print(f"\n🎯 Top 5 Oportunidades (abaixo do mercado):")
            for i, opp in enumerate(insights['opportunities'][:5], 1):
                print(f"  {i}. {opp['title'][:40]:40} ({opp['discount_pct']:+.0f}%)")
                print(f"     {opp['neighborhood']:20} | R$ {opp['price_per_m2']:,.0f}/m² vs mercado R$ {opp['market_avg']:,.0f}/m²")

    except Exception as e:
        print(f"❌ Erro ao buscar insights: {e}")

    # Workflow recente
    print("\n" + "="*70)
    print("📝 ÚLTIMO WORKFLOW")
    print("-" * 70)

    try:
        if os.path.exists('.tmp/workflow_report.json'):
            with open('.tmp/workflow_report.json', 'r') as f:
                report = json.load(f)

            wf = report.get('workflow', {})
            disc = report.get('discovery', {})
            scrape = report.get('scraping', {})

            print(f"Última execução:        {wf.get('start_time', 'N/A')[:19]}")
            print(f"Duração:                {wf.get('duration_seconds', 0)/60:.1f} minutos")
            print(f"URLs descobertas:       {disc.get('urls_found', 0):,}")
            print(f"Imóveis processados:    {scrape.get('success', 0)}/{scrape.get('total', 0)}")
        else:
            print("Nenhum workflow executado ainda")

    except Exception as e:
        print(f"❌ Erro ao ler relatório: {e}")

    print("\n" + "="*70)
    print()


def export_report(output_file: str = None):
    """Exporta relatório completo em JSON"""
    if output_file is None:
        output_file = f".tmp/dashboard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    report = {
        'generated_at': datetime.now().isoformat(),
        'scraping_metrics': get_scraping_metrics(),
        'market_insights': get_market_insights(),
    }

    os.makedirs('.tmp', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    print(f"✅ Relatório exportado: {output_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Dashboard de Métricas')
    parser.add_argument('--export', action='store_true', help='Exportar relatório JSON')
    parser.add_argument('--output', type=str, help='Arquivo de saída (padrão: .tmp/dashboard_report_*.json)')

    args = parser.parse_args()

    if args.export:
        export_report(args.output)
    else:
        print_dashboard()
