#!/usr/bin/env python3
"""
Cookie Manager
==============
Gestão de cookies para persistência de sessão Cloudflare
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict


COOKIE_FILE = '.tmp/cookies.json'
COOKIE_EXPIRY_HOURS = 6


def save_cookies(cookies: List[Dict], metadata: Optional[Dict] = None):
    """
    Salva cookies após bypass Cloudflare

    Args:
        cookies: Lista de cookies do browser context
        metadata: Metadados opcionais (fingerprint usado, etc)
    """
    data = {
        'cookies': cookies,
        'timestamp': datetime.now().isoformat(),
        'metadata': metadata or {}
    }

    os.makedirs('.tmp', exist_ok=True)
    with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"✅ Cookies salvos: {len(cookies)} cookies")


def load_cookies() -> Optional[List[Dict]]:
    """
    Carrega cookies salvos se ainda válidos

    Returns:
        List[Dict] ou None se expirados ou não existem
    """
    if not os.path.exists(COOKIE_FILE):
        print("⚠️  Nenhum cookie salvo encontrado")
        return None

    try:
        with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Verificar expiração
        timestamp = datetime.fromisoformat(data['timestamp'])
        age_hours = (datetime.now() - timestamp).total_seconds() / 3600

        if age_hours > COOKIE_EXPIRY_HOURS:
            print(f"⚠️  Cookies expirados ({age_hours:.1f}h)")
            return None

        print(f"✅ Cookies carregados: {len(data['cookies'])} cookies ({age_hours:.1f}h de idade)")
        return data['cookies']

    except Exception as e:
        print(f"❌ Erro ao carregar cookies: {e}")
        return None


def apply_cookies(context, cookies: List[Dict]) -> bool:
    """
    Aplica cookies no contexto do browser

    Args:
        context: Browser context do Playwright
        cookies: Lista de cookies

    Returns:
        bool: True se aplicou com sucesso
    """
    if not cookies:
        return False

    try:
        context.add_cookies(cookies)
        return True
    except Exception as e:
        print(f"❌ Erro ao aplicar cookies: {e}")
        return False


def delete_cookies():
    """Remove arquivo de cookies"""
    if os.path.exists(COOKIE_FILE):
        os.remove(COOKIE_FILE)
        print("🗑️  Cookies deletados")


def get_cookie_info() -> Optional[Dict]:
    """Retorna informações sobre cookies salvos"""
    if not os.path.exists(COOKIE_FILE):
        return None

    try:
        with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        timestamp = datetime.fromisoformat(data['timestamp'])
        age_hours = (datetime.now() - timestamp).total_seconds() / 3600
        expires_in = COOKIE_EXPIRY_HOURS - age_hours

        return {
            'count': len(data['cookies']),
            'age_hours': age_hours,
            'expires_in_hours': max(0, expires_in),
            'is_valid': expires_in > 0,
            'metadata': data.get('metadata', {})
        }
    except:
        return None


if __name__ == "__main__":
    # Teste do cookie manager
    print("Testando Cookie Manager...")

    info = get_cookie_info()
    if info:
        print(f"\nInformações dos cookies:")
        print(f"  Quantidade: {info['count']}")
        print(f"  Idade: {info['age_hours']:.2f}h")
        print(f"  Expira em: {info['expires_in_hours']:.2f}h")
        print(f"  Válido: {info['is_valid']}")
    else:
        print("\nNenhum cookie salvo")
