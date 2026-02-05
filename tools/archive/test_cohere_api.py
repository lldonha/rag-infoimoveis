"""
Teste simplificado da API Cohere para debug
"""

import os
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

def test_cohere_api():
    """Testar chamada básica da API Cohere e ver estrutura da resposta"""
    
    try:
        import cohere
    except ImportError:
        print("❌ Cohere não instalado")
        print("   Instale com: pip install cohere")
        return False

    COHERE_API_KEY = os.getenv('COHERE_API_KEY', 'your_cohere_api_key')

    if COHERE_API_KEY == 'your_cohere_api_key':
        print("❌ COHERE_API_KEY não configurada no .env")
        return False

    try:
        print(f"🔑 API Key: {COHERE_API_KEY[:10]}...{COHERE_API_KEY[-4:]}")

        co = cohere.Client(COHERE_API_KEY)

        text = "Teste de embedding"
        print(f"\n📝 Texto: '{text}'")

        print("\n🔄 Chamando API Cohere...")
        response = co.embed(
            texts=[text],
            model='embed-english-v3.0',
            input_type='search_document',
            embedding_types=['float']
        )

        print(f"\n✅ Resposta recebida!")
        print(f"   Tipo da resposta: {type(response)}")
        
        # Listar atributos da resposta (sem os métodos privados)
        attrs = [attr for attr in dir(response) if not attr.startswith('_')]
        print(f"   Atributos disponíveis: {attrs}")

        # Tentar acessar embeddings de várias formas
        print("\n🔍 Testando acessos:")

        # Tentativa 1: response.embeddings.float[0]
        try:
            emb1 = response.embeddings.float[0]
            print(f"   ✅ response.embeddings.float[0] → {len(emb1)} dimensões")
            print(f"      Primeiros 5 valores: {emb1[:5]}")
            return True
        except Exception as e1:
            print(f"   ❌ response.embeddings.float[0] → {type(e1).__name__}: {e1}")

        # Tentativa 2: response.embeddings[0]
        try:
            emb2 = response.embeddings[0]
            print(f"   ✅ response.embeddings[0] → {len(emb2)} dimensões")
            print(f"      Primeiros 5 valores: {emb2[:5]}")
            return True
        except Exception as e2:
            print(f"   ❌ response.embeddings[0] → {type(e2).__name__}: {e2}")

        # Tentativa 3: Investigar estrutura de embeddings
        print("\n📋 Investigando estrutura de 'embeddings':")
        if hasattr(response, 'embeddings'):
            embeddings = response.embeddings
            print(f"   Tipo: {type(embeddings)}")
            
            emb_attrs = [attr for attr in dir(embeddings) if not attr.startswith('_')]
            print(f"   Atributos: {emb_attrs}")

            if hasattr(embeddings, 'float'):
                float_obj = embeddings.float
                print(f"\n   embeddings.float existe!")
                print(f"   Tipo de .float: {type(float_obj)}")
                
                if isinstance(float_obj, list):
                    print(f"   É uma lista com {len(float_obj)} elementos")
                    if len(float_obj) > 0:
                        print(f"   Primeiro elemento tem {len(float_obj[0])} dimensões")
                        print(f"   Primeiros 5 valores: {float_obj[0][:5]}")
                        return True

        return False

    except Exception as e:
        print(f"\n❌ Erro: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("TESTE DA API COHERE")
    print("="*60)
    
    success = test_cohere_api()

    print("\n" + "="*60)
    if success:
        print("✅ Teste concluído com sucesso!")
    else:
        print("❌ Teste falhou")
        print("\nINSTRUÇÕES:")
        print("1. Verifique se COHERE_API_KEY está no .env")
        print("2. Teste a chave em: https://dashboard.cohere.com/api-keys")
        print("3. Atualize: pip install cohere --upgrade")
    print("="*60)
