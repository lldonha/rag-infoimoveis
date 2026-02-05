"""
Etapa 0.6: Pipeline de Embeddings
Validar geração de embeddings com Cohere (free tier) e fallback Ollama
"""

import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from decimal import Decimal
import time
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

# Configuração do banco
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'infoimoveis',
    'user': 'postgres',
    'password': 'postgres'
}

# Cohere (tentar primário)
try:
    import cohere
    COHERE_AVAILABLE = True
    COHERE_API_KEY = os.getenv('COHERE_API_KEY', 'your_cohere_api_key')
except ImportError:
    COHERE_AVAILABLE = False
    print("⚠️  Cohere não instalado. Use: pip install cohere")

# Ollama (fallback local)
try:
    import requests
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


def generate_embedding_cohere(text, model='embed-english-v3.0'):
    """Gerar embedding usando Cohere API (FREE tier: 1000 calls/min)"""
    if not COHERE_AVAILABLE:
        return None, "Cohere não disponível"

    if COHERE_API_KEY == 'your_cohere_api_key':
        return None, "Cohere API key não configurada"

    try:
        co = cohere.Client(COHERE_API_KEY)

        # Cohere embed-v3 retorna 1024 dimensões
        response = co.embed(
            texts=[text],
            model=model,
            input_type='search_document',  # Para documentos a serem buscados
            embedding_types=['float']
        )

        # Acesso correto: response.embeddings.float[0]
        embedding = response.embeddings.float[0]
        return embedding, None

    except Exception as e:
        return None, f"Erro Cohere: {str(e)}"


def generate_embedding_ollama(text, model='qwen3-embedding:0.6b'):
    """Gerar embedding usando Ollama local (FREE, dimensões variadas)"""
    if not OLLAMA_AVAILABLE:
        return None, "Requests não disponível"

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/embeddings",
            json={
                "model": model,
                "prompt": text
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            embedding = data.get('embedding')

            if not embedding:
                return None, "Embedding vazio retornado"

            # Se embedding tem menos de 1024 dims, fazer padding
            if len(embedding) < 1024:
                embedding = embedding + [0.0] * (1024 - len(embedding))
            # Se tem mais, truncar
            elif len(embedding) > 1024:
                embedding = embedding[:1024]

            return embedding, None
        else:
            # Tentar fallback com nomic-embed-text
            response2 = requests.post(
                f"{OLLAMA_HOST}/api/embeddings",
                json={
                    "model": "nomic-embed-text",
                    "prompt": text
                },
                timeout=30
            )
            if response2.status_code == 200:
                data = response2.json()
                embedding = data.get('embedding', [])
                if len(embedding) < 1024:
                    embedding = embedding + [0.0] * (1024 - len(embedding))
                return embedding, None

            return None, f"Erro Ollama: HTTP {response.status_code}"

    except requests.exceptions.ConnectionError:
        return None, "Ollama não está rodando. Execute: ollama serve"
    except Exception as e:
        return None, f"Erro Ollama: {str(e)}"


def generate_embedding_with_fallback(text):
    """Pipeline: Cohere → Ollama → Erro"""
    # Tentar Cohere primeiro (mais rápido, maior dimensão)
    embedding, error = generate_embedding_cohere(text)
    if embedding:
        return embedding, 'cohere-embed-v3', None

    print(f"   ⚠️  Cohere falhou: {error}")

    # Fallback: Ollama local
    embedding, error = generate_embedding_ollama(text)
    if embedding:
        return embedding, 'ollama-qwen3-embedding', None

    print(f"   ⚠️  Ollama falhou: {error}")

    return None, None, "Ambos os métodos falharam"


def test_embedding_generation():
    """Teste 1: Gerar embeddings de teste"""
    print("\n=== Teste 1: Geração de Embeddings ===")

    test_texts = [
        "Apartamento moderno com 3 quartos no Jardim dos Estados",
        "Casa ampla com 4 quartos e piscina no Aero Rancho",
        "Sala comercial em prédio novo no Centro"
    ]

    for i, text in enumerate(test_texts, 1):
        print(f"\n{i}. Texto: {text[:60]}...")

        embedding, model, error = generate_embedding_with_fallback(text)

        if embedding:
            print(f"   ✅ Embedding gerado com {model}")
            print(f"   Dimensões: {len(embedding)}")
            print(f"   Primeiros 5 valores: {embedding[:5]}")
        else:
            print(f"   ❌ Erro: {error}")
            return False

    return True


def test_insert_property_with_embedding():
    """Teste 2: Inserir imóvel com embedding no banco"""
    print("\n=== Teste 2: Inserir Imóvel + Embedding ===")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Criar imóvel de teste
        property_data = {
            'source_url': 'https://test.com/embedding-test/001',
            'property_type': 'apartamento',
            'property_use': 'residencial',
            'transaction_type': 'venda',
            'city': 'Campo Grande',
            'neighborhood': 'Jardim dos Estados',
            'state': 'MS',
            'area_total_m2': Decimal('90.0'),
            'price_brl': Decimal('480000.00'),
            'price_per_m2': Decimal('5333.33'),
            'title': 'Apartamento 3 quartos com suíte',
            'description': 'Excelente apartamento de 90m² com 3 quartos sendo 1 suíte, varanda gourmet e 2 vagas de garagem. Condomínio completo com piscina e salão de festas.',
            'embedding_status': 'processing'
        }

        # Inserir imóvel
        cursor.execute("""
            INSERT INTO properties (
                source_url, property_type, property_use, transaction_type,
                city, neighborhood, state, area_total_m2, price_brl, price_per_m2,
                title, description, embedding_status
            ) VALUES (
                %(source_url)s, %(property_type)s, %(property_use)s, %(transaction_type)s,
                %(city)s, %(neighborhood)s, %(state)s, %(area_total_m2)s, %(price_brl)s, %(price_per_m2)s,
                %(title)s, %(description)s, %(embedding_status)s
            ) RETURNING id;
        """, property_data)

        property_id = cursor.fetchone()['id']
        print(f"✅ Imóvel inserido: {property_id}")

        # Gerar embedding do conteúdo
        content = f"""
Título: {property_data['title']}
Tipo: {property_data['property_type']} - {property_data['property_use']}
Localização: {property_data['neighborhood']}, {property_data['city']}/{property_data['state']}
Área: {property_data['area_total_m2']}m²
Preço: R$ {property_data['price_brl']}
Descrição: {property_data['description']}
        """.strip()

        print(f"Gerando embedding para {len(content)} caracteres...")

        embedding, model, error = generate_embedding_with_fallback(content)

        if not embedding:
            print(f"❌ Erro ao gerar embedding: {error}")
            cursor.execute("DELETE FROM properties WHERE id = %s", (property_id,))
            conn.commit()
            return False

        print(f"✅ Embedding gerado com {model}")

        # Inserir embedding
        cursor.execute("""
            INSERT INTO property_embeddings (
                property_id, chunk_index, chunk_type, content, embedding, embedding_model, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            property_id,
            0,
            'full',
            content,
            embedding,
            model,
            json.dumps({'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')})
        ))

        embedding_id = cursor.fetchone()['id']
        print(f"✅ Embedding inserido: {embedding_id}")

        # Atualizar status do imóvel
        cursor.execute("""
            UPDATE properties
            SET embedding_status = 'completed'
            WHERE id = %s;
        """, (property_id,))

        print("✅ Status atualizado para 'completed'")

        conn.commit()

        # Verificar inserção
        cursor.execute("""
            SELECT p.title, pe.embedding_model, pe.created_at
            FROM properties p
            JOIN property_embeddings pe ON p.id = pe.property_id
            WHERE p.id = %s;
        """, (property_id,))

        result = cursor.fetchone()
        print(f"\n✅ Verificação:")
        print(f"   Imóvel: {result['title']}")
        print(f"   Modelo: {result['embedding_model']}")
        print(f"   Criado: {result['created_at']}")

        # Cleanup
        cursor.execute("DELETE FROM properties WHERE id = %s", (property_id,))
        conn.commit()
        print(f"\n✅ Imóvel de teste removido")

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


def test_similarity_search_real():
    """Teste 3: Busca por similaridade com embeddings reais"""
    print("\n=== Teste 3: Busca por Similaridade ===")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Limpar dados de teste anteriores
        cursor.execute("DELETE FROM properties WHERE source_url LIKE 'https://test.com/%'")
        conn.commit()
        print("✅ Dados de teste antigos removidos")

        # Inserir 3 imóveis com descrições diferentes
        properties = [
            {
                'url': 'https://test.com/apt-luxo',
                'title': 'Apartamento de Luxo - Chácara Cachoeira',
                'description': 'Apartamento alto padrão com 4 suítes, piscina privativa e vista panorâmica.',
                'neighborhood': 'Chácara Cachoeira',
                'price': Decimal('1200000'),
                'area': Decimal('250.0')
            },
            {
                'url': 'https://test.com/apt-economico',
                'title': 'Apartamento Econômico - Aero Rancho',
                'description': 'Apartamento compacto de 2 quartos, ideal para solteiros ou casal jovem.',
                'neighborhood': 'Aero Rancho',
                'price': Decimal('220000'),
                'area': Decimal('55.0')
            },
            {
                'url': 'https://test.com/casa-familia',
                'title': 'Casa para Família - Monte Castelo',
                'description': 'Casa espaçosa com 3 quartos, quintal grande e área gourmet completa.',
                'neighborhood': 'Monte Castelo',
                'price': Decimal('550000'),
                'area': Decimal('180.0')
            }
        ]

        property_ids = []

        print("Inserindo imóveis e gerando embeddings...")

        for i, prop in enumerate(properties, 1):
            # Inserir imóvel
            cursor.execute("""
                INSERT INTO properties (
                    source_url, title, description, neighborhood, price_brl, area_total_m2,
                    property_type, transaction_type, embedding_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                prop['url'], prop['title'], prop['description'], prop['neighborhood'],
                prop['price'], prop['area'], 'apartamento', 'venda', 'processing'
            ))

            prop_id = cursor.fetchone()['id']
            property_ids.append(prop_id)

            # Gerar embedding
            content = f"{prop['title']} - {prop['description']} - {prop['neighborhood']}"
            embedding, model, error = generate_embedding_with_fallback(content)

            if not embedding:
                print(f"❌ Falha ao gerar embedding para {prop['title']}")
                continue

            # Inserir embedding
            cursor.execute("""
                INSERT INTO property_embeddings (
                    property_id, content, embedding, embedding_model
                ) VALUES (%s, %s, %s, %s);
            """, (prop_id, content, embedding, model))

            # Atualizar status
            cursor.execute("""
                UPDATE properties SET embedding_status = 'completed' WHERE id = %s;
            """, (prop_id,))

            print(f"   {i}. {prop['title']} ✅")

        conn.commit()

        # Criar query: buscar apartamento compacto e econômico
        query_text = "Apartamento pequeno e barato para comprar"
        print(f"\n🔍 Query: '{query_text}'")

        query_embedding, model, error = generate_embedding_with_fallback(query_text)

        if not query_embedding:
            print(f"❌ Erro ao gerar embedding da query: {error}")
            return False

        print(f"✅ Embedding da query gerado com {model}")

        # Debug: verificar property_ids
        print(f"   Property IDs a buscar: {property_ids}")

        # Buscar similares (converter UUIDs para string explicitamente)
        cursor.execute("""
            SELECT
                p.title,
                p.neighborhood,
                p.price_brl,
                p.area_total_m2,
                1 - (pe.embedding <=> %s::vector) as similarity
            FROM property_embeddings pe
            JOIN properties p ON pe.property_id = p.id
            WHERE p.id = ANY(%s::uuid[])
            ORDER BY pe.embedding <=> %s::vector
            LIMIT 3;
        """, (str(query_embedding), [str(pid) for pid in property_ids], str(query_embedding)))

        results = cursor.fetchall()

        if not results:
            print("\n⚠️  Nenhum resultado encontrado!")
            print(f"   Property IDs buscados: {property_ids}")
            # Verificar se embeddings foram inseridos
            cursor.execute("""
                SELECT p.id, p.title, pe.id as emb_id
                FROM properties p
                LEFT JOIN property_embeddings pe ON p.id = pe.property_id
                WHERE p.id = ANY(%s::uuid[])
            """, ([str(pid) for pid in property_ids],))
            debug_results = cursor.fetchall()
            for dr in debug_results:
                print(f"   - {dr['title']}: embedding_id={dr['emb_id']}")
            return False

        print("\n✅ Resultados (ordenados por relevância):")
        for i, result in enumerate(results, 1):
            print(f"\n   {i}. {result['title']}")
            print(f"      Bairro: {result['neighborhood']}")
            print(f"      Preço: R$ {result['price_brl']:,.2f}")
            print(f"      Área: {result['area_total_m2']}m²")
            print(f"      Similaridade: {result['similarity']:.4f}")

        # Verificar se o apartamento econômico ficou em 1º lugar
        if 'Econômico' in results[0]['title']:
            print("\n🎯 Busca correta! Apartamento econômico ficou em 1º lugar.")
        else:
            print("\n⚠️  Atenção: Resultado pode não ser ideal (modelo de embedding).")

        # Cleanup
        for prop_id in property_ids:
            cursor.execute("DELETE FROM properties WHERE id = %s", (prop_id,))
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
    """Executar todos os testes"""
    print("=" * 60)
    print("TESTE Pipeline de Embeddings - Etapa 0.6")
    print("=" * 60)

    tests = [
        ("Geração de Embeddings", test_embedding_generation),
        ("Inserir Imóvel + Embedding", test_insert_property_with_embedding),
        ("Busca por Similaridade", test_similarity_search_real)
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
        print("\n🎉 Etapa 0.6 CONCLUÍDA - Pipeline de Embeddings funcionando!")
        print("\nPróximo passo: Etapa 0.7 - Sistema RAG Completo")
        return 0
    else:
        print("\n⚠️  Alguns testes falharam. Verificar logs acima.")
        print("\nPara instalar dependências:")
        print("  pip install cohere requests")
        print("\nPara rodar Ollama:")
        print("  ollama serve")
        print("  ollama pull nomic-embed-text")
        return 1


if __name__ == "__main__":
    sys.exit(main())
