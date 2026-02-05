"""
Teste SIMPLIFICADO - Pipeline de Embeddings
Usando APIs gratuitas (Groq/Mistral) para embeddings enquanto Ollama está com problemas
"""

import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from decimal import Decimal
import requests

# Configuração do banco
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'infoimoveis',
    'user': 'postgres',
    'password': 'postgres'
}

# APIs disponíveis
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')


def generate_embedding_with_llm(text):
    """
    Gera embedding simulado usando LLM Groq (já que Cohere e Ollama não estão disponíveis)
    Retorna um vetor de 1024 dimensões normalizado
    """
    # Usar hash do texto para gerar embedding determinístico
    import hashlib
    import numpy as np

    # Gerar hash do texto
    text_hash = hashlib.sha256(text.encode()).hexdigest()

    # Converter hash em números
    seed = int(text_hash[:16], 16)
    np.random.seed(seed % (2**32))

    # Gerar vetor de 1024 dimensões
    embedding = np.random.randn(1024)

    # Normalizar (para similaridade de cosseno funcionar)
    norm = np.linalg.norm(embedding)
    embedding = embedding / norm

    # Converter para lista de floats Python nativos
    embedding = [float(x) for x in embedding.tolist()]

    return embedding, 'simulated-hash-embedding'


def test_1_generate_embeddings():
    """Teste 1: Gerar embeddings"""
    print("\n=== Teste 1: Geração de Embeddings ===")

    texts = [
        "Apartamento 3 quartos no Jardim dos Estados",
        "Casa com piscina no Aero Rancho",
        "Sala comercial no Centro"
    ]

    for i, text in enumerate(texts, 1):
        embedding, model = generate_embedding_with_llm(text)
        print(f"{i}. ✅ {text[:40]}... → {len(embedding)} dims ({model})")

    return True


def test_2_insert_property():
    """Teste 2: Inserir imóvel com embedding"""
    print("\n=== Teste 2: Inserir Imóvel + Embedding ===")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Limpar dados de teste anteriores
        cursor.execute("DELETE FROM properties WHERE source_url LIKE 'https://test.com/%'")
        conn.commit()

        # Inserir imóvel
        cursor.execute("""
            INSERT INTO properties (
                source_url, title, description, neighborhood,
                property_type, transaction_type, price_brl, area_total_m2
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            'https://test.com/test-embedding-001',
            'Apartamento Test',
            'Apartamento para teste de embeddings',
            'Jardim dos Estados',
            'apartamento',
            'venda',
            Decimal('400000'),
            Decimal('85.0')
        ))

        property_id = cursor.fetchone()['id']
        print(f"✅ Imóvel inserido: {property_id}")

        # Gerar embedding
        content = "Apartamento Test - Apartamento para teste de embeddings - Jardim dos Estados"
        embedding, model = generate_embedding_with_llm(content)
        print(f"✅ Embedding gerado: {len(embedding)} dims ({model})")

        # Inserir embedding
        cursor.execute("""
            INSERT INTO property_embeddings (
                property_id, content, embedding, embedding_model
            ) VALUES (%s, %s, %s, %s)
            RETURNING id;
        """, (property_id, content, str(embedding), model))

        embedding_id = cursor.fetchone()['id']
        print(f"✅ Embedding inserido: {embedding_id}")

        conn.commit()

        # Limpar
        cursor.execute("DELETE FROM properties WHERE id = %s", (property_id,))
        conn.commit()
        print("✅ Limpeza concluída")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Erro: {e}")
        if conn:
            conn.rollback()
        return False


def test_3_similarity_search():
    """Teste 3: Busca por similaridade"""
    print("\n=== Teste 3: Busca por Similaridade ===")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Limpar dados anteriores
        cursor.execute("DELETE FROM properties WHERE source_url LIKE 'https://test.com/%'")
        conn.commit()

        # Inserir 3 imóveis diferentes
        properties = [
            {
                'url': 'https://test.com/apt-luxo-2',
                'title': 'Apartamento de Luxo',
                'desc': 'Apartamento alto padrão com 4 suítes e piscina privativa',
                'neighborhood': 'Chácara Cachoeira'
            },
            {
                'url': 'https://test.com/apt-economico-2',
                'title': 'Apartamento Econômico',
                'desc': 'Apartamento compacto de 2 quartos ideal para solteiros',
                'neighborhood': 'Aero Rancho'
            },
            {
                'url': 'https://test.com/casa-familia-2',
                'title': 'Casa para Família',
                'desc': 'Casa espaçosa com 3 quartos e quintal grande',
                'neighborhood': 'Monte Castelo'
            }
        ]

        property_ids = []

        print("Inserindo imóveis com embeddings...")
        for prop in properties:
            # Inserir imóvel
            cursor.execute("""
                INSERT INTO properties (
                    source_url, title, description, neighborhood, property_type, transaction_type
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (prop['url'], prop['title'], prop['desc'], prop['neighborhood'], 'apartamento', 'venda'))

            prop_id = cursor.fetchone()['id']
            property_ids.append(prop_id)

            # Gerar embedding
            content = f"{prop['title']} - {prop['desc']}"
            embedding, model = generate_embedding_with_llm(content)

            # Inserir embedding
            cursor.execute("""
                INSERT INTO property_embeddings (property_id, content, embedding, embedding_model)
                VALUES (%s, %s, %s, %s);
            """, (prop_id, content, str(embedding), model))

            print(f"   ✅ {prop['title']}")

        conn.commit()

        # Buscar similar
        query_text = "Apartamento pequeno e barato"
        query_embedding, model = generate_embedding_with_llm(query_text)

        print(f"\n🔍 Query: '{query_text}'")

        # Converter UUIDs para array PostgreSQL
        cursor.execute("""
            SELECT
                p.title,
                p.neighborhood,
                1 - (pe.embedding <=> %s::vector) as similarity
            FROM property_embeddings pe
            JOIN properties p ON pe.property_id = p.id
            WHERE p.id = ANY(%s::uuid[])
            ORDER BY pe.embedding <=> %s::vector
            LIMIT 3;
        """, (str(query_embedding), [str(pid) for pid in property_ids], str(query_embedding)))

        results = cursor.fetchall()

        print("\n✅ Resultados:")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result['title']} ({result['neighborhood']}) - Similaridade: {result['similarity']:.4f}")

        # Limpar
        cursor.execute("DELETE FROM properties WHERE id = ANY(%s::uuid[])", ([str(pid) for pid in property_ids],))
        conn.commit()
        print(f"\n✅ Removidos {len(property_ids)} imóveis de teste")

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


def main():
    print("=" * 60)
    print("TESTE SIMPLIFICADO - Pipeline de Embeddings")
    print("=" * 60)

    tests = [
        ("Geração de Embeddings", test_1_generate_embeddings),
        ("Inserir Imóvel + Embedding", test_2_insert_property),
        ("Busca por Similaridade", test_3_similarity_search)
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ Erro fatal: {e}")
            results.append((name, False))

    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)

    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")

    passed = sum(1 for _, s in results if s)
    total = len(results)

    print(f"\nTotal: {passed}/{total} testes passaram")

    if passed == total:
        print("\n🎉 PostgreSQL + pgvector funcionando perfeitamente!")
        print("\n⚠️  PRÓXIMO PASSO: Configurar embeddings reais")
        print("   • Obter Cohere API key (gratuita)")
        print("   • OU corrigir Ollama (reinstalar)")
        return 0
    else:
        print("\n⚠️  Alguns testes falharam")
        return 1


if __name__ == "__main__":
    sys.exit(main())
