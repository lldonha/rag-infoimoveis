"""
Teste simplificado da API Cohere para debug
"""

import os
import cohere

COHERE_API_KEY = os.getenv('COHERE_API_KEY', 'your_cohere_api_key')

def test_cohere_simple():
    """Testar chamada básica da API Cohere e ver estrutura da resposta"""

    if COHERE_API_KEY == 'your_cohere_api_key':
        print("❌ COHERE_API_KEY não configurada no .env")
        return False

    try:
        print(f"🔑 API Key: {COHERE_API_KEY[:10]}...{COHERE_API_KEY[-4:]}")

        co = cohere.Client(COHERE_API_KEY)

        text = "Teste de embedding"
        print(f"\n📝 Texto: {text}")

        print("\n🔄 Chamando API Cohere...")
        response = co.embed(
            texts=[text],
            model='embed-english-v3.0',
            input_type='search_document',
            embedding_types=['float']
        )

        print(f"\n✅ Resposta recebida!")
        print(f"   Tipo da resposta: {type(response)}")
        print(f"   Dir da resposta: {[attr for attr in dir(response) if not attr.startswith('_')]}")

        # Tentar acessar embeddings de várias formas
        print("\n🔍 Testando acessos:")

        # Tentativa 1: response.embeddings.float[0]
        try:
            emb1 = response.embeddings.float[0]
            print(f"   ✅ response.embeddings.float[0] → {len(emb1)} dimensões")
            print(f"      Primeiros 5: {emb1[:5]}")
            return True
        except Exception as e1:
            print(f"   ❌ response.embeddings.float[0] → {e1}")

        # Tentativa 2: response.embeddings[0]
        try:
            emb2 = response.embeddings[0]
            print(f"   ✅ response.embeddings[0] → {len(emb2)} dimensões")
            print(f"      Primeiros 5: {emb2[:5]}")
            return True
        except Exception as e2:
            print(f"   ❌ response.embeddings[0] → {e2}")

        # Tentativa 3: Mostrar estrutura completa
        print("\n📋 Estrutura completa da resposta:")
        if hasattr(response, 'embeddings'):
            embeddings = response.embeddings
            print(f"   Tipo de embeddings: {type(embeddings)}")
            print(f"   Dir de embeddings: {[attr for attr in dir(embeddings) if not attr.startswith('_')]}")

            if hasattr(embeddings, 'float'):
                print(f"   embeddings.float existe: {type(embeddings.float)}")
                if isinstance(embeddings.float, list) and len(embeddings.float) > 0:
                    print(f"   embeddings.float[0] tem {len(embeddings.float[0])} dimensões")
                    return True

        return False

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_cohere_simple()

    if not success:
        print("\n" + "="*60)
        print("INSTRUÇÕES:")
        print("="*60)
        print("1. Verifique se COHERE_API_KEY está no .env")
        print("2. Teste a chave em: https://dashboard.cohere.com/api-keys")
        print("3. Instale: pip install cohere --upgrade")
