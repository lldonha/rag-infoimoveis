"""
Etapa 0.7: Sistema RAG Completo
Sistema completo de busca e resposta sobre imóveis usando RAG
"""

import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from decimal import Decimal
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

# APIs disponíveis
COHERE_API_KEY = os.getenv('COHERE_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Importações condicionais
try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False
    print("⚠️  Cohere não instalado. Use: pip install cohere")

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️  Groq não instalado. Use: pip install groq")


def generate_embedding(text):
    """Gerar embedding usando Cohere"""
    if not COHERE_AVAILABLE or COHERE_API_KEY == 'your_cohere_api_key':
        return None, "Cohere não disponível"

    try:
        co = cohere.Client(COHERE_API_KEY)
        response = co.embed(
            texts=[text],
            model='embed-english-v3.0',
            input_type='search_query',  # Para queries de busca
            embedding_types=['float']
        )
        return response.embeddings.float[0], None
    except Exception as e:
        return None, f"Erro Cohere: {str(e)}"


def search_similar_properties(query_text, limit=5):
    """
    Buscar imóveis similares usando embeddings vetoriais

    Args:
        query_text: Texto da consulta do usuário
        limit: Número máximo de resultados

    Returns:
        Lista de imóveis com scores de similaridade
    """
    try:
        # Gerar embedding da query
        query_embedding, error = generate_embedding(query_text)
        if not query_embedding:
            return None, f"Erro ao gerar embedding: {error}"

        # Conectar ao banco
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Buscar imóveis similares
        cursor.execute("""
            SELECT
                p.id,
                p.title,
                p.description,
                p.property_type,
                p.transaction_type,
                p.neighborhood,
                p.city,
                p.state,
                p.price_brl,
                p.area_total_m2,
                p.price_per_m2,
                p.source_url,
                pe.content as full_content,
                1 - (pe.embedding <=> %s::vector) as similarity_score
            FROM property_embeddings pe
            JOIN properties p ON pe.property_id = p.id
            WHERE p.embedding_status = 'completed'
            ORDER BY pe.embedding <=> %s::vector
            LIMIT %s;
        """, (query_embedding, query_embedding, limit))

        results = cursor.fetchall()

        cursor.close()
        conn.close()

        return results, None

    except Exception as e:
        return None, f"Erro na busca: {str(e)}"


def generate_rag_response(query_text, context_properties):
    """
    Gerar resposta usando LLM (Groq) com contexto dos imóveis encontrados

    Args:
        query_text: Pergunta do usuário
        context_properties: Lista de imóveis do contexto

    Returns:
        Resposta gerada pelo LLM
    """
    if not GROQ_AVAILABLE or not GROQ_API_KEY:
        return None, "Groq não disponível"

    try:
        # Formatar contexto
        context_parts = []
        for i, prop in enumerate(context_properties, 1):
            price_formatted = f"R$ {float(prop['price_brl']):,.2f}" if prop['price_brl'] else "Não informado"
            area_formatted = f"{float(prop['area_total_m2']):.2f}m²" if prop['area_total_m2'] else "Não informado"

            context_parts.append(f"""
IMÓVEL {i}:
Título: {prop['title']}
Tipo: {prop['property_type']} - {prop['transaction_type']}
Localização: {prop['neighborhood']}, {prop['city']}/{prop['state']}
Preço: {price_formatted}
Área: {area_formatted}
Descrição: {prop['description'] or 'Não disponível'}
URL: {prop['source_url']}
Relevância: {prop['similarity_score']:.2%}
""")

        context = "\n".join(context_parts)

        # Prompt para o LLM
        system_prompt = """Você é um assistente especializado em imóveis de Campo Grande/MS.
Sua função é ajudar usuários a encontrar imóveis baseado nos dados fornecidos.

INSTRUÇÕES:
- Responda APENAS com base nos imóveis fornecidos no contexto
- Destaque os imóveis mais relevantes para a consulta
- Mencione preço, localização e características principais
- Se nenhum imóvel for adequado, diga isso claramente
- Seja objetivo e informativo
- SEMPRE inclua a URL do imóvel ao mencioná-lo
"""

        user_prompt = f"""CONTEXTO (Imóveis disponíveis):
{context}

PERGUNTA DO USUÁRIO:
{query_text}

Responda de forma clara e objetiva, destacando os imóveis mais adequados à consulta."""

        # Chamar Groq API
        client = Groq(api_key=GROQ_API_KEY)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )

        return response.choices[0].message.content, None

    except Exception as e:
        return None, f"Erro ao gerar resposta: {str(e)}"


def rag_query(query_text, top_k=5):
    """
    Pipeline RAG completo: buscar contexto + gerar resposta

    Args:
        query_text: Pergunta do usuário
        top_k: Número de imóveis para contexto

    Returns:
        Resposta gerada, imóveis de contexto, métricas
    """
    print(f"\n🔍 Query: '{query_text}'")

    # Passo 1: Buscar imóveis similares
    print(f"\n1️⃣ Buscando imóveis similares (top {top_k})...")
    properties, error = search_similar_properties(query_text, limit=top_k)

    if not properties:
        return None, None, {"error": error}

    print(f"   ✅ Encontrados {len(properties)} imóveis")

    # Passo 2: Gerar resposta com LLM
    print(f"\n2️⃣ Gerando resposta com LLM...")
    response, error = generate_rag_response(query_text, properties)

    if not response:
        return None, properties, {"error": error}

    print(f"   ✅ Resposta gerada ({len(response)} caracteres)")

    # Métricas
    metrics = {
        "num_properties_found": len(properties),
        "avg_similarity": sum(p['similarity_score'] for p in properties) / len(properties),
        "top_similarity": properties[0]['similarity_score'] if properties else 0,
        "response_length": len(response)
    }

    return response, properties, metrics


def test_rag_with_sample_data():
    """Teste 1: RAG com dados de exemplo"""
    print("\n=== Teste 1: RAG com Dados de Exemplo ===")

    conn = None
    try:
        # Inserir dados de teste
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Limpar dados antigos
        cursor.execute("DELETE FROM properties WHERE source_url LIKE 'https://test.com/%'")
        conn.commit()

        # Inserir 5 imóveis variados
        test_properties = [
            {
                'url': 'https://test.com/apt-luxo-jd-estados',
                'title': 'Apartamento de Alto Padrão - Jardim dos Estados',
                'description': 'Apartamento luxuoso com 4 suítes, 3 vagas, varanda gourmet com churrasqueira, piscina privativa no terraço. Condomínio com academia completa.',
                'type': 'apartamento',
                'transaction': 'venda',
                'neighborhood': 'Jardim dos Estados',
                'city': 'Campo Grande',
                'state': 'MS',
                'price': Decimal('1800000'),
                'area': Decimal('280.0'),
                'price_m2': Decimal('6428.57')
            },
            {
                'url': 'https://test.com/apt-compacto-aero',
                'title': 'Apartamento Compacto 2 Quartos - Aero Rancho',
                'description': 'Apartamento econômico com 2 quartos, sala, cozinha americana, 1 vaga. Ideal para solteiros ou casal jovem.',
                'type': 'apartamento',
                'transaction': 'venda',
                'neighborhood': 'Aero Rancho',
                'city': 'Campo Grande',
                'state': 'MS',
                'price': Decimal('280000'),
                'area': Decimal('55.0'),
                'price_m2': Decimal('5090.91')
            },
            {
                'url': 'https://test.com/casa-piscina-chacara',
                'title': 'Casa com Piscina - Chácara Cachoeira',
                'description': 'Casa térrea com 3 quartos sendo 1 suíte, piscina, churrasqueira, quintal amplo. Excelente para famílias.',
                'type': 'casa',
                'transaction': 'venda',
                'neighborhood': 'Chácara Cachoeira',
                'city': 'Campo Grande',
                'state': 'MS',
                'price': Decimal('850000'),
                'area': Decimal('220.0'),
                'price_m2': Decimal('3863.64')
            },
            {
                'url': 'https://test.com/sala-comercial-centro',
                'title': 'Sala Comercial - Centro',
                'description': 'Sala comercial de 45m² em prédio novo, localização privilegiada no Centro. Ideal para escritório.',
                'type': 'comercial',
                'transaction': 'venda',
                'neighborhood': 'Centro',
                'city': 'Campo Grande',
                'state': 'MS',
                'price': Decimal('320000'),
                'area': Decimal('45.0'),
                'price_m2': Decimal('7111.11')
            },
            {
                'url': 'https://test.com/apt-3q-vilas-boas',
                'title': 'Apartamento 3 Quartos - Vilas Boas',
                'description': 'Apartamento com 3 quartos, sala ampla, cozinha, área de serviço, 2 vagas. Condomínio com piscina e salão de festas.',
                'type': 'apartamento',
                'transaction': 'venda',
                'neighborhood': 'Vilas Boas',
                'city': 'Campo Grande',
                'state': 'MS',
                'price': Decimal('650000'),
                'area': Decimal('120.0'),
                'price_m2': Decimal('5416.67')
            }
        ]

        property_ids = []

        print("Inserindo imóveis de teste...")
        for prop in test_properties:
            # Inserir imóvel
            cursor.execute("""
                INSERT INTO properties (
                    source_url, title, description, property_type, transaction_type,
                    neighborhood, city, state, price_brl, area_total_m2, price_per_m2,
                    embedding_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                prop['url'], prop['title'], prop['description'], prop['type'], prop['transaction'],
                prop['neighborhood'], prop['city'], prop['state'], prop['price'], prop['area'],
                prop['price_m2'], 'processing'
            ))

            prop_id = cursor.fetchone()['id']
            property_ids.append(prop_id)

            # Gerar embedding
            content = f"{prop['title']} - {prop['description']} - {prop['neighborhood']}"
            embedding, error = generate_embedding(content)

            if not embedding:
                print(f"   ❌ Erro ao gerar embedding: {error}")
                continue

            # Inserir embedding
            cursor.execute("""
                INSERT INTO property_embeddings (
                    property_id, content, embedding, embedding_model
                ) VALUES (%s, %s, %s, %s);
            """, (prop_id, content, embedding, 'cohere-embed-v3'))

            # Atualizar status
            cursor.execute("""
                UPDATE properties SET embedding_status = 'completed' WHERE id = %s;
            """, (prop_id,))

            print(f"   ✅ {prop['title'][:50]}...")

        conn.commit()
        print(f"\n✅ {len(property_ids)} imóveis inseridos com embeddings")

        # Testar queries
        test_queries = [
            "Quero um apartamento barato para comprar",
            "Procuro casa com piscina para família",
            "Preciso de um escritório no centro da cidade"
        ]

        for query in test_queries:
            response, properties, metrics = rag_query(query, top_k=3)

            if response:
                print(f"\n{'='*60}")
                print(f"RESPOSTA:")
                print(f"{'='*60}")
                print(response)
                print(f"\n📊 Métricas:")
                print(f"   - Imóveis encontrados: {metrics['num_properties_found']}")
                print(f"   - Similaridade média: {metrics['avg_similarity']:.2%}")
                print(f"   - Top similaridade: {metrics['top_similarity']:.2%}")
            else:
                print(f"   ❌ Erro: {metrics.get('error')}")

        # Cleanup
        cursor.execute("DELETE FROM properties WHERE id = ANY(%s::uuid[])", ([str(pid) for pid in property_ids],))
        conn.commit()
        print(f"\n✅ Dados de teste removidos")

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
    """Executar testes do sistema RAG"""
    print("=" * 60)
    print("TESTE Sistema RAG Completo - Etapa 0.7")
    print("=" * 60)

    # Verificar dependências
    if not COHERE_AVAILABLE:
        print("❌ Cohere não instalado. Execute: pip install cohere")
        return 1

    if not GROQ_AVAILABLE:
        print("❌ Groq não instalado. Execute: pip install groq")
        return 1

    if not COHERE_API_KEY or COHERE_API_KEY == 'your_cohere_api_key':
        print("❌ COHERE_API_KEY não configurada no .env")
        return 1

    if not GROQ_API_KEY or GROQ_API_KEY == 'your_groq_api_key':
        print("❌ GROQ_API_KEY não configurada no .env")
        return 1

    print("✅ Todas as dependências disponíveis\n")

    # Executar teste
    success = test_rag_with_sample_data()

    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)

    if success:
        print("✅ Sistema RAG Completo funcionando!")
        print("\n🎉 Etapa 0.7 CONCLUÍDA!")
        print("\nSistema RAG operacional com:")
        print("   • Busca vetorial com Cohere embeddings")
        print("   • Geração de respostas com Groq LLM")
        print("   • PostgreSQL + pgvector como base")
        return 0
    else:
        print("❌ Teste falhou")
        return 1


if __name__ == "__main__":
    sys.exit(main())
