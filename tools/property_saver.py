#!/usr/bin/env python3
"""
Property Saver
==============
Insere imóveis no PostgreSQL com deduplicação e validação
"""

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from typing import Dict, Optional, List
from datetime import datetime
import os
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


def calculate_completeness(data: Dict) -> float:
    """
    Calcula score de completude dos dados (0.0 a 1.0)

    Campos críticos recebem mais peso
    """
    weights = {
        'title': 2,
        'description': 2,
        'property_type': 2,
        'transaction_type': 2,
        'city': 1,
        'neighborhood': 2,
        'area_total_m2': 2,
        'area_built_m2': 1,
        'bedrooms': 1,
        'bathrooms': 1,
        'price_brl': 3,  # Preço é crítico
        'images': 1,
    }

    total_weight = sum(weights.values())
    achieved_weight = 0

    for field, weight in weights.items():
        value = data.get(field)
        if value is not None and value != '' and value != []:
            achieved_weight += weight

    return round(achieved_weight / total_weight, 2)


def property_exists(cursor, source_url: str) -> Optional[str]:
    """
    Verifica se imóvel já existe no banco

    Returns:
        UUID do imóvel se existe, None se não existe
    """
    cursor.execute(
        "SELECT id FROM properties WHERE source_url = %s",
        (source_url,)
    )
    result = cursor.fetchone()
    return result['id'] if result else None


def insert_property(data: Dict, update_if_exists: bool = True) -> Optional[str]:
    """
    Insere imóvel no banco (ou atualiza se já existe)

    Args:
        data: Dicionário com dados do imóvel
        update_if_exists: Se True, atualiza dados se imóvel já existe

    Returns:
        UUID do imóvel inserido/atualizado ou None se erro
    """
    if not data.get('source_url'):
        print("❌ Erro: source_url é obrigatório")
        return None

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Calcular completude
        completeness = calculate_completeness(data)

        # Verificar se já existe
        existing_id = property_exists(cursor, data['source_url'])

        if existing_id and not update_if_exists:
            print(f"⏭️  Imóvel já existe: {existing_id}")
            return existing_id

        # Preparar dados
        fields = {
            'source_url': data.get('source_url'),
            'property_type': data.get('property_type'),
            'property_use': data.get('property_use'),
            'transaction_type': data.get('transaction_type'),
            'city': data.get('city', 'Campo Grande'),
            'neighborhood': data.get('neighborhood'),
            'state': data.get('state', 'MS'),
            'address': data.get('address'),
            'area_total_m2': data.get('area_total_m2'),
            'area_built_m2': data.get('area_built_m2'),
            'bedrooms': data.get('bedrooms'),
            'bathrooms': data.get('bathrooms'),
            'suites': data.get('suites'),
            'parking_spaces': data.get('parking_spaces'),
            'price_brl': data.get('price_brl'),
            'price_per_m2': data.get('price_per_m2'),
            'condominium_fee_brl': data.get('condominium_fee_brl'),
            'iptu_annual_brl': data.get('iptu_annual_brl'),
            'title': data.get('title'),
            'description': data.get('description'),
            'features': Json(data.get('features', [])),
            'images': Json(data.get('images', [])),
            'data_completeness': completeness,
        }

        if existing_id:
            # UPDATE
            set_clause = ', '.join([f"{k} = %s" for k in fields.keys() if k != 'source_url'])
            values = [v for k, v in fields.items() if k != 'source_url']
            values.append(data['source_url'])

            cursor.execute(f"""
                UPDATE properties
                SET {set_clause}, updated_at = NOW()
                WHERE source_url = %s
                RETURNING id
            """, values)

            property_id = cursor.fetchone()['id']
            print(f"✅ Imóvel atualizado: {property_id} (completude: {completeness:.0%})")

        else:
            # INSERT
            columns = ', '.join(fields.keys())
            placeholders = ', '.join(['%s'] * len(fields))
            values = list(fields.values())

            cursor.execute(f"""
                INSERT INTO properties ({columns})
                VALUES ({placeholders})
                RETURNING id
            """, values)

            property_id = cursor.fetchone()['id']
            print(f"✅ Imóvel inserido: {property_id} (completude: {completeness:.0%})")

        conn.commit()
        return property_id

    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao salvar imóvel: {e}")
        return None

    finally:
        cursor.close()
        conn.close()


def bulk_insert_properties(properties: List[Dict], update_if_exists: bool = True) -> Dict:
    """
    Insere múltiplos imóveis em lote

    Args:
        properties: Lista de dicionários com dados dos imóveis
        update_if_exists: Se True, atualiza dados se imóvel já existe

    Returns:
        Dict com estatísticas: inserted, updated, errors
    """
    stats = {'inserted': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

    for prop in properties:
        try:
            existing_url = prop.get('source_url')
            if not existing_url:
                stats['errors'] += 1
                continue

            # Verificar se existe
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            existing_id = property_exists(cursor, existing_url)
            cursor.close()
            conn.close()

            # Inserir ou atualizar
            property_id = insert_property(prop, update_if_exists)

            if property_id:
                if existing_id:
                    stats['updated'] += 1
                else:
                    stats['inserted'] += 1
            else:
                stats['errors'] += 1

        except Exception as e:
            print(f"❌ Erro no lote: {e}")
            stats['errors'] += 1

    return stats


def get_property_stats() -> Dict:
    """Retorna estatísticas dos imóveis no banco"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Total de imóveis
        cursor.execute("SELECT COUNT(*) as total FROM properties")
        total = cursor.fetchone()['total']

        # Por tipo de transação
        cursor.execute("""
            SELECT transaction_type, COUNT(*) as count
            FROM properties
            GROUP BY transaction_type
        """)
        by_transaction = {row['transaction_type']: row['count'] for row in cursor.fetchall()}

        # Por tipo de imóvel
        cursor.execute("""
            SELECT property_type, COUNT(*) as count
            FROM properties
            GROUP BY property_type
            ORDER BY count DESC
            LIMIT 10
        """)
        by_type = {row['property_type']: row['count'] for row in cursor.fetchall()}

        # Por bairro
        cursor.execute("""
            SELECT neighborhood, COUNT(*) as count
            FROM properties
            WHERE neighborhood IS NOT NULL
            GROUP BY neighborhood
            ORDER BY count DESC
            LIMIT 10
        """)
        by_neighborhood = {row['neighborhood']: row['count'] for row in cursor.fetchall()}

        # Completude média
        cursor.execute("SELECT AVG(data_completeness) as avg_completeness FROM properties")
        avg_completeness = cursor.fetchone()['avg_completeness'] or 0

        return {
            'total': total,
            'by_transaction': by_transaction,
            'by_type': by_type,
            'by_neighborhood': by_neighborhood,
            'avg_completeness': float(avg_completeness),
        }

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Teste do property saver
    print("Testando Property Saver...")

    # Imóvel de teste
    test_property = {
        'source_url': 'https://www.infoimoveis.com.br/imovel/teste-123',
        'title': 'Apartamento de Teste',
        'description': 'Descrição do apartamento de teste',
        'property_type': 'Apartamento',
        'property_use': 'residencial',
        'transaction_type': 'venda',
        'city': 'Campo Grande',
        'neighborhood': 'Centro',
        'state': 'MS',
        'area_total_m2': 100.0,
        'bedrooms': 3,
        'bathrooms': 2,
        'price_brl': 350000.0,
        'price_per_m2': 3500.0,
        'images': ['https://example.com/img1.jpg'],
    }

    property_id = insert_property(test_property)
    print(f"\nID retornado: {property_id}")

    # Estatísticas
    stats = get_property_stats()
    print(f"\nEstatísticas do banco:")
    print(f"  Total: {stats['total']} imóveis")
    print(f"  Completude média: {stats['avg_completeness']:.1%}")
    print(f"  Por transação: {stats['by_transaction']}")
