#!/usr/bin/env python3
"""
Teste simples de todos os serviços disponíveis
"""

import os
import sys
from dotenv import load_dotenv
import requests
from colorama import Fore, Style, init

# Inicializa colorama
init(autoreset=True)

# Carrega variáveis de ambiente
load_dotenv()

def print_test(service_name, status, message=""):
    """Imprime resultado do teste de forma colorida"""
    status_symbol = "✓" if status else "✗"
    status_color = Fore.GREEN if status else Fore.RED
    print(f"{status_color}{status_symbol} {service_name:<20}{Style.RESET_ALL} {message}")

def test_ollama():
    """Testa conexão com Ollama local"""
    try:
        ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)

        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m.get('name', 'unknown') for m in models[:3]]
            print_test("Ollama", True, f"Modelos: {', '.join(model_names) if model_names else 'nenhum modelo instalado'}")
            return True
        else:
            print_test("Ollama", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        print_test("Ollama", False, str(e))
        return False

def test_groq():
    """Testa API da Groq"""
    try:
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            print_test("Groq", False, "API key não encontrada")
            return False

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            'model': 'llama-3.3-70b-versatile',
            'messages': [{'role': 'user', 'content': 'Responda apenas: OK'}],
            'max_tokens': 10
        }

        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print_test("Groq", True, f"Resposta: {content[:30]}")
            return True
        else:
            print_test("Groq", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        print_test("Groq", False, str(e))
        return False

def test_mistral():
    """Testa API da Mistral"""
    try:
        api_key = os.getenv('MISTRAL_API_KEY')
        if not api_key:
            print_test("Mistral", False, "API key não encontrada")
            return False

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            'model': 'mistral-small-latest',
            'messages': [{'role': 'user', 'content': 'Responda apenas: OK'}],
            'max_tokens': 10
        }

        response = requests.post(
            'https://api.mistral.ai/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print_test("Mistral", True, f"Resposta: {content[:30]}")
            return True
        else:
            print_test("Mistral", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        print_test("Mistral", False, str(e))
        return False

def test_cohere():
    """Testa API da Cohere"""
    try:
        api_key = os.getenv('COHERE_API_KEY')
        if not api_key:
            print_test("Cohere", False, "API key não encontrada")
            return False

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            'message': 'Responda apenas: OK',
            'model': 'command-r-08-2024',
            'max_tokens': 10
        }

        response = requests.post(
            'https://api.cohere.com/v2/chat',
            headers=headers,
            json=data,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            content = result.get('message', {}).get('content', [{}])[0].get('text', 'N/A')
            print_test("Cohere", True, f"Resposta: {content[:30]}")
            return True
        else:
            print_test("Cohere", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        print_test("Cohere", False, str(e))
        return False

def test_openrouter():
    """Testa API da OpenRouter"""
    try:
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            print_test("OpenRouter", False, "API key não encontrada")
            return False

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'http://localhost',
            'X-Title': 'RAG InfoImóveis Test'
        }

        # Usando modelo gratuito específico do OpenRouter
        data = {
            'model': 'google/gemini-2.0-flash-exp:free',  # Modelo gratuito
            'messages': [{'role': 'user', 'content': 'Responda apenas: OK'}],
            'max_tokens': 10
        }

        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print_test("OpenRouter", True, f"Resposta: {content[:30]}")
            return True
        else:
            print_test("OpenRouter", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        print_test("OpenRouter", False, str(e))
        return False

def test_n8n():
    """Testa conexão com n8n"""
    try:
        # Tenta conectar no n8n (assumindo porta padrão 5678)
        response = requests.get('http://localhost:5678/healthz', timeout=5)

        if response.status_code == 200:
            print_test("n8n", True, "Container rodando")
            return True
        else:
            print_test("n8n", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        print_test("n8n", False, str(e))
        return False

def test_postgres():
    """Testa conexão com PostgreSQL"""
    try:
        import psycopg2

        conn = psycopg2.connect(
            host='localhost',
            port=5433,  # Porta customizada do projeto
            database=os.getenv('POSTGRES_DB', 'infoimoveis'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD'),
            connect_timeout=5
        )

        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        # Extrai versão do PostgreSQL
        pg_version = version.split()[1] if 'PostgreSQL' in version else 'unknown'
        print_test("PostgreSQL", True, f"v{pg_version}")
        return True

    except Exception as e:
        print_test("PostgreSQL", False, str(e))
        return False

def main():
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"🧪 TESTE DE SERVIÇOS - RAG InfoImóveis")
    print(f"{'='*60}{Style.RESET_ALL}\n")

    results = {}

    # Testa serviços locais
    print(f"{Fore.YELLOW}► Serviços Locais{Style.RESET_ALL}")
    results['PostgreSQL'] = test_postgres()
    results['Ollama'] = test_ollama()
    results['n8n'] = test_n8n()

    # Testa APIs Free Tier
    print(f"\n{Fore.YELLOW}► APIs Free Tier{Style.RESET_ALL}")
    results['Groq'] = test_groq()
    results['Mistral'] = test_mistral()
    results['Cohere'] = test_cohere()
    results['OpenRouter'] = test_openrouter()

    # Resumo
    print(f"\n{Fore.CYAN}{'='*60}")
    total = len(results)
    passed = sum(results.values())
    failed = total - passed

    print(f"📊 RESUMO: {passed}/{total} serviços OK")
    if failed > 0:
        print(f"{Fore.RED}⚠️  {failed} serviço(s) com problema{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}✓ Todos os serviços operacionais!{Style.RESET_ALL}")

    print(f"{'='*60}{Style.RESET_ALL}\n")

    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
