"""
Etapa 0.5: Teste PostgreSQL + pgvector
Validar CRUD básico e operações vetoriais
"""

import os
import sys
import json
from datetime import datetime
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np

# Configuração
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'infoimoveis',
    'user': 'postgres',
    'password': 'infoimoveis2024'
}

def test_connection():
    """Teste 1: Conexão básica"""
    print("\n=== Teste 1: Conexão ===")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Conectado: {version[:50]}...")

        # Verificar extensões
        cursor.execute("SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'uuid-ossp');")
        extensions = cursor.fetchall()
        print(f"✅ Extensões instaladas: {extensions}")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_crud_properties():
    """Teste 2: CRUD na tabela properties"""
    print("\n=== Teste 2: CRUD Properties ===")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # CREATE - Inserir imóvel de teste
        property_data = {
            'source_url': 'https://test.com/property/12345',
            'property_type': 'apartamento',
            'property_use': 'residencial',
            'transaction_type': 'venda',
            'city': 'Campo Grande',
            'neighborhood': 'Jardim dos Estados',
            'state': 'MS',
            'address': 'Rua Teste, 123',
            'area_total_m2': Decimal('85.50'),
            'area_built_m2': Decimal('70.00'),
            'bedrooms': 3,
            'bathrooms': 2,
            'suites': 1,
            'parking_spaces': 2,
            'price_brl': Decimal('450000.00'),
            'price_per_m2': Decimal('5263.16'),
            'title': 'Apartamento 3 quartos - Jardim dos Estados',
            'description': 'Excelente apartamento com 3 quartos, sendo 1 suíte.',
            'features': json.dumps(['piscina', 'churrasqueira', 'salão de festas']),
            'images': json.dumps(['img1.jpg', 'img2.jpg']),
            'embedding_status': 'pending'
        }

        insert_query = """
        INSERT INTO properties (
            source_url, property_type, property_use, transaction_type,
            city, neighborhood, state, address,
            area_total_m2, area_built_m2, bedrooms, bathrooms, suites, parking_spaces,
            price_brl, price_per_m2, title, description, features, images, embedding_status
        ) VALUES (
            %(source_url)s, %(property_type)s, %(property_use)s, %(transaction_type)s,
            %(city)s, %(neighborhood)s, %(state)s, %(address)s,
            %(area_total_m2)s, %(area_built_m2)s, %(bedrooms)s, %(bathrooms)s, %(suites)s, %(parking_spaces)s,
            %(price_brl)s, %(price_per_m2)s, %(title)s, %(description)s, %(features)s, %(images)s, %(embedding_status)s
        )
        RETURNING id, title, price_brl;
        """

        cursor.execute(insert_query, property_data)
        inserted = cursor.fetchone()
        property_id = inserted['id']
        print(f"✅ INSERT: {inserted['title']} | R$ {inserted['price_brl']}")
        print(f"   ID: {property_id}")

        # READ - Buscar imóvel inserido
        cursor.execute("SELECT * FROM properties WHERE id = %s;", (property_id,))
        property_read = cursor.fetchone()
        print(f"✅ READ: {property_read['title']} em {property_read['neighborhood']}")

        # UPDATE - Atualizar preço
        new_price = Decimal('420000.00')
        cursor.execute(
            "UPDATE properties SET price_brl = %s, price_per_m2 = %s WHERE id = %s RETURNING price_brl;",
            (new_price, new_price / property_data['area_total_m2'], property_id)
        )
        updated = cursor.fetchone()
        print(f"✅ UPDATE: Novo preço R$ {updated['price_brl']}")

        # DELETE - Remover imóvel de teste
        cursor.execute("DELETE FROM properties WHERE id = %s RETURNING id;", (property_id,))
        deleted = cursor.fetchone()
        print(f"✅ DELETE: Imóvel {deleted['id']} removido")

        conn.commit()
        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Erro: {e}")
        if conn:
            conn.rollback()
        return False

def test_vector_operations():
    """Teste 3: Operações com pgvector"""
    print("\n=== Teste 3: Operações Vetoriais ===")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Inserir 3 imóveis de teste com embeddings simulados
        properties = [
            {
                'url': 'https://test.com/apt1',
                'title': 'Apartamento Jardim dos Estados - 3 quartos',
                'neighborhood': 'Jardim dos Estados',
                'price': Decimal('450000'),
                'area': Decimal('85.0'),
                'description': 'Apartamento moderno com 3 quartos no Jardim dos Estados'
            },
            {
                'url': 'https://test.com/apt2',
                'title': 'Apartamento Vilas Boas - 2 quartos',
                'neighborhood': 'Vilas Boas',
                'price': Decimal('280000'),
                'area': Decimal('65.0'),
                'description': 'Apartamento compacto de 2 quartos próximo ao centro'
            },
            {
                'url': 'https://test.com/casa1',
                'title': 'Casa Aero Rancho - 4 quartos',
                'neighborhood': 'Aero Rancho',
                'price': Decimal('650000'),
                'area': Decimal('180.0'),
                'description': 'Casa ampla com 4 quartos e área gourmet'
            }
        ]

        property_ids = []

        for prop in properties:
            cursor.execute("""
                INSERT INTO properties (
                    source_url, title, neighborhood, price_brl, area_total_m2,
                    description, property_type, transaction_type, embedding_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                prop['url'], prop['title'], prop['neighborhood'], prop['price'], prop['area'],
                prop['description'], 'apartamento', 'venda', 'completed'
            ))
            property_ids.append(cursor.fetchone()['id'])

        print(f"✅ Inseridos {len(property_ids)} imóveis de teste")

        # Gerar embeddings simulados (vetores aleatórios de 1024 dimensões)
        # Em produção, isso virá de Cohere ou Ollama
        for i, prop_id in enumerate(property_ids):
            # Criar vetor com padrão diferente para cada imóvel
            embedding = np.random.rand(1024).astype(np.float32)

            # Adicionar "assinatura" para tornar similar ao mesmo bairro
            if i == 0 or i == 1:  # Apartamentos
                embedding[:100] += 0.5

            embedding_list = embedding.tolist()

            cursor.execute("""
                INSERT INTO property_embeddings (
                    property_id, chunk_index, chunk_type, content, embedding, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                prop_id, 0, 'full', properties[i]['description'],
                str(embedding_list), json.dumps({'type': 'test'})
            ))

        print("✅ Embeddings gerados e inseridos")

        # Busca por similaridade - Criar query embedding similar ao primeiro imóvel
        query_embedding = np.random.rand(1024).astype(np.float32)
        query_embedding[:100] += 0.5  # Mesmo padrão de apartamento
        query_list = query_embedding.tolist()

        # Buscar imóveis similares
        cursor.execute("""
            SELECT
                p.id,
                p.title,
                p.neighborhood,
                p.price_brl,
                1 - (pe.embedding <=> %s::vector) as similarity
            FROM property_embeddings pe
            JOIN properties p ON pe.property_id = p.id
            ORDER BY pe.embedding <=> %s::vector
            LIMIT 3;
        """, (str(query_list), str(query_list)))

        results = cursor.fetchall()
        print("\n✅ Busca por similaridade (top 3):")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result['title']}")
            print(f"      Bairro: {result['neighborhood']} | Preço: R$ {result['price_brl']}")
            print(f"      Similaridade: {result['similarity']:.4f}")

        # Testar função search_similar_properties
        print("\n✅ Testando função search_similar_properties:")
        cursor.execute("""
            SELECT * FROM search_similar_properties(
                %s::vector,
                NULL,  -- property_type
                NULL,  -- property_use
                NULL,  -- neighborhood
                NULL,  -- transaction_type
                NULL,  -- min_price
                NULL,  -- max_price
                3      -- limit
            );
        """, (str(query_list),))

        func_results = cursor.fetchall()
        for i, result in enumerate(func_results, 1):
            print(f"   {i}. {result['title']} | Similaridade: {result['similarity']:.4f}")

        # Cleanup - Remover dados de teste
        for prop_id in property_ids:
            cursor.execute("DELETE FROM properties WHERE id = %s;", (prop_id,))

        print(f"\n✅ Removidos {len(property_ids)} imóveis de teste")

        conn.commit()
        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return False

def test_indexes():
    """Teste 4: Verificar índices criados"""
    print("\n=== Teste 4: Índices ===")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname;
        """)

        indexes = cursor.fetchall()
        print(f"✅ Total de índices: {len(indexes)}")

        # Verificar índices importantes
        important_indexes = [
            'idx_embeddings_vector',
            'idx_properties_location',
            'idx_properties_type_use',
            'idx_properties_price'
        ]

        index_names = [idx['indexname'] for idx in indexes]
        for imp_idx in important_indexes:
            if imp_idx in index_names:
                print(f"   ✅ {imp_idx}")
            else:
                print(f"   ⚠️  {imp_idx} não encontrado")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    """Executar todos os testes"""
    print("=" * 60)
    print("TESTE PostgreSQL + pgvector - Etapa 0.5")
    print("=" * 60)

    tests = [
        ("Conexão", test_connection),
        ("CRUD Properties", test_crud_properties),
        ("Operações Vetoriais", test_vector_operations),
        ("Índices", test_indexes)
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ Erro fatal em {name}: {e}")
            results.append((name, False))

    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)

    for name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{status}: {name}")

    total_passed = sum(1 for _, success in results if success)
    total_tests = len(results)

    print(f"\nTotal: {total_passed}/{total_tests} testes passaram")

    if total_passed == total_tests:
        print("\n🎉 Etapa 0.5 CONCLUÍDA - PostgreSQL + pgvector funcionando!")
        return 0
    else:
        print("\n⚠️  Alguns testes falharam. Verificar logs acima.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
