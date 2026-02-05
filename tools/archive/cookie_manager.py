"""
Gerenciador de Cookies para Persistência de Sessão
Salva/carrega cookies do Cloudflare para reutilizar sessões autenticadas
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path


COOKIE_FILE = Path('.tmp/cookies.json')
COOKIE_EXPIRY_HOURS = 6  # Renovar a cada 6 horas


def save_cookies(cookies, metadata=None):
    """
    Salvar cookies após bypass Cloudflare

    Args:
        cookies: Lista de cookies do Playwright (context.cookies())
        metadata: Dados adicionais (URL, fingerprint usado, etc.)
    """
    data = {
        'cookies': cookies,
        'timestamp': datetime.now().isoformat(),
        'expiry': (datetime.now() + timedelta(hours=COOKIE_EXPIRY_HOURS)).isoformat(),
        'metadata': metadata or {}
    }

    # Criar diretório se não existir
    os.makedirs(COOKIE_FILE.parent, exist_ok=True)

    with open(COOKIE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"💾 Cookies salvos ({len(cookies)} cookies) - Expiram em {COOKIE_EXPIRY_HOURS}h")


def load_cookies():
    """
    Carregar cookies salvos

    Returns:
        list: Lista de cookies ou None se não existir/expirado
    """
    if not COOKIE_FILE.exists():
        print("ℹ️  Nenhum cookie salvo encontrado")
        return None

    try:
        with open(COOKIE_FILE, 'r') as f:
            data = json.load(f)

        # Verificar se expirou
        timestamp = datetime.fromisoformat(data['timestamp'])
        age_hours = (datetime.now() - timestamp).total_seconds() / 3600

        if age_hours > COOKIE_EXPIRY_HOURS:
            print(f"⚠️  Cookies expirados (idade: {age_hours:.1f}h > {COOKIE_EXPIRY_HOURS}h)")
            return None

        cookies = data['cookies']
        print(f"✅ Cookies carregados ({len(cookies)} cookies, idade: {age_hours:.1f}h)")

        return cookies

    except Exception as e:
        print(f"❌ Erro ao carregar cookies: {e}")
        return None


def apply_cookies(context, cookies):
    """
    Aplicar cookies no contexto do browser

    Args:
        context: Contexto do Playwright (browser.new_context())
        cookies: Lista de cookies do load_cookies()

    Returns:
        bool: True se aplicado com sucesso
    """
    if not cookies:
        return False

    try:
        context.add_cookies(cookies)
        print(f"✅ {len(cookies)} cookies aplicados ao contexto")
        return True

    except Exception as e:
        print(f"❌ Erro ao aplicar cookies: {e}")
        return False


def delete_cookies():
    """Deletar arquivo de cookies (forçar renovação)"""
    if COOKIE_FILE.exists():
        COOKIE_FILE.unlink()
        print("🗑️  Cookies deletados")
        return True
    return False


def get_cookie_info():
    """
    Informações sobre cookies salvos

    Returns:
        dict: Informações ou None se não existir
    """
    if not COOKIE_FILE.exists():
        return None

    try:
        with open(COOKIE_FILE, 'r') as f:
            data = json.load(f)

        timestamp = datetime.fromisoformat(data['timestamp'])
        expiry = datetime.fromisoformat(data['expiry'])
        age = datetime.now() - timestamp
        remaining = expiry - datetime.now()

        return {
            'created_at': timestamp.strftime('%d/%m/%Y %H:%M:%S'),
            'expires_at': expiry.strftime('%d/%m/%Y %H:%M:%S'),
            'age_hours': age.total_seconds() / 3600,
            'remaining_hours': max(0, remaining.total_seconds() / 3600),
            'is_expired': remaining.total_seconds() <= 0,
            'cookie_count': len(data['cookies']),
            'metadata': data.get('metadata', {})
        }

    except Exception as e:
        print(f"❌ Erro ao ler info dos cookies: {e}")
        return None


def print_cookie_info():
    """Imprime informações dos cookies de forma legível"""
    info = get_cookie_info()

    if not info:
        print("ℹ️  Nenhum cookie salvo")
        return

    print("\n" + "="*60)
    print("🍪 COOKIES - Informações")
    print("="*60)
    print(f"Criado em: {info['created_at']}")
    print(f"Expira em: {info['expires_at']}")
    print(f"Idade: {info['age_hours']:.1f}h")
    print(f"Tempo restante: {info['remaining_hours']:.1f}h")
    print(f"Status: {'❌ EXPIRADO' if info['is_expired'] else '✅ VÁLIDO'}")
    print(f"Quantidade: {info['cookie_count']} cookies")

    if info['metadata']:
        print(f"\nMetadata:")
        for key, value in info['metadata'].items():
            print(f"  {key}: {value}")

    print("="*60 + "\n")


if __name__ == "__main__":
    # Teste do cookie manager
    print("="*60)
    print("🧪 TESTE - Cookie Manager")
    print("="*60)

    print("\n1. Verificando cookies existentes...")
    print_cookie_info()

    print("\n2. Testando salvamento de cookies mock...")
    mock_cookies = [
        {
            'name': '__cf_bm',
            'value': 'test_cloudflare_cookie_value_12345',
            'domain': '.infoimoveis.com.br',
            'path': '/',
            'secure': True,
            'httpOnly': True
        },
        {
            'name': '_ga',
            'value': 'GA1.2.1234567890.1234567890',
            'domain': '.infoimoveis.com.br',
            'path': '/',
            'secure': False,
            'httpOnly': False
        }
    ]

    save_cookies(mock_cookies, metadata={'test': True, 'url': 'https://infoimoveis.com.br'})

    print("\n3. Carregando cookies salvos...")
    loaded = load_cookies()

    if loaded:
        print(f"   Sucesso! {len(loaded)} cookies carregados")

    print("\n4. Info dos cookies...")
    print_cookie_info()

    print("\n5. Deletando cookies de teste...")
    delete_cookies()

    print("\n✅ Teste concluído!")
