#!/usr/bin/env python3
"""
Fingerprint Rotator
===================
Rotação de identidade do browser para evitar tracking
"""

import random
from typing import Dict


# User Agents realistas (Chrome/Firefox Windows/Mac)
USER_AGENTS = [
    # Chrome Windows 10
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",

    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",

    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
]


# Viewports comuns
VIEWPORTS = [
    {'width': 1920, 'height': 1080},  # Full HD
    {'width': 1366, 'height': 768},   # Laptop comum
    {'width': 1536, 'height': 864},   # Laptop HD+
    {'width': 1440, 'height': 900},   # MacBook Pro
    {'width': 2560, 'height': 1440},  # 2K
]


# Timezones do Brasil (Centro-Oeste)
TIMEZONES = [
    'America/Campo_Grande',
    'America/Cuiaba',
    'America/Sao_Paulo',
]


# Locales
LOCALES = [
    'pt-BR',
    'pt',
]


def get_random_fingerprint() -> Dict:
    """
    Gera um fingerprint aleatório mas realista

    Returns:
        Dict com user_agent, viewport, timezone, locale
    """
    return {
        'user_agent': random.choice(USER_AGENTS),
        'viewport': random.choice(VIEWPORTS),
        'timezone': random.choice(TIMEZONES),
        'locale': random.choice(LOCALES),
    }


def apply_fingerprint(browser_context, fingerprint: Dict = None):
    """
    Aplica fingerprint no contexto do browser

    Note: Esta função é para documentação. O fingerprint
    deve ser aplicado na criação do context com browser.new_context()

    Args:
        browser_context: Contexto do Playwright
        fingerprint: Dict retornado por get_random_fingerprint()
    """
    if fingerprint is None:
        fingerprint = get_random_fingerprint()

    # O contexto já foi criado, então só documentamos
    # Na prática, você deve passar os parâmetros ao criar o context:
    #
    # context = browser.new_context(
    #     user_agent=fingerprint['user_agent'],
    #     viewport=fingerprint['viewport'],
    #     locale=fingerprint['locale'],
    #     timezone_id=fingerprint['timezone']
    # )

    return fingerprint


def get_anti_detection_script() -> str:
    """
    Retorna script JavaScript para remover sinais de automação

    Returns:
        str: Script para passar ao context.add_init_script()
    """
    return """
        // Remover flag webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        // Sobrescrever plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });

        // Sobrescrever languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['pt-BR', 'pt', 'en-US', 'en']
        });

        // Chrome runtime
        window.chrome = {
            runtime: {}
        };

        // Permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """


if __name__ == "__main__":
    # Teste do fingerprint rotator
    print("Testando Fingerprint Rotator...")

    for i in range(5):
        fp = get_random_fingerprint()
        print(f"\nFingerprint {i+1}:")
        print(f"  UA: {fp['user_agent'][:60]}...")
        print(f"  Viewport: {fp['viewport']['width']}x{fp['viewport']['height']}")
        print(f"  Timezone: {fp['timezone']}")
        print(f"  Locale: {fp['locale']}")
