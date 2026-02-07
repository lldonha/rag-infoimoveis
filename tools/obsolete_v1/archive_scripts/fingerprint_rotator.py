"""
Rotacionador de Fingerprint para Evitar Detecção
Varia User-Agent, viewport, timezone e outras características
"""

import random


# User-Agents reais e atualizados (2024-2026)
USER_AGENTS = [
    # Chrome Windows (mais comum)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",

    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",

    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",

    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

# Resoluções comuns (estatísticas reais de uso)
VIEWPORTS = [
    {'width': 1920, 'height': 1080},  # Full HD (mais comum)
    {'width': 1366, 'height': 768},   # Laptop padrão
    {'width': 1536, 'height': 864},   # Laptop HD+
    {'width': 1440, 'height': 900},   # MacBook Air
    {'width': 2560, 'height': 1440},  # 2K
    {'width': 1600, 'height': 900},   # HD+
]

# Timezones brasileiros
TIMEZONES = [
    'America/Sao_Paulo',      # Horário de Brasília (GMT-3)
    'America/Campo_Grande',   # Mato Grosso do Sul (GMT-4)
    'America/Cuiaba',         # Mato Grosso (GMT-4)
    'America/Manaus',         # Amazonas (GMT-4)
    'America/Rio_Branco',     # Acre (GMT-5)
]

# Locales brasileiros
LOCALES = [
    'pt-BR',  # Português Brasil (padrão)
    'pt-PT',  # Português Portugal (similar)
]

# Distribuição de sistemas operacionais (pesos para seleção)
OS_WEIGHTS = {
    'Windows': 0.70,  # 70% Windows
    'Mac': 0.20,      # 20% Mac
    'Linux': 0.10     # 10% Linux
}


def get_random_fingerprint(seed=None):
    """
    Gera fingerprint aleatório mas coerente

    Args:
        seed: Seed para reproduzibilidade (opcional)

    Returns:
        dict: Fingerprint com user_agent, viewport, timezone, locale
    """
    if seed:
        random.seed(seed)

    fingerprint = {
        'user_agent': random.choice(USER_AGENTS),
        'viewport': random.choice(VIEWPORTS),
        'timezone': random.choice(TIMEZONES),
        'locale': random.choice(LOCALES),
    }

    return fingerprint


def get_fingerprint_for_os(os_type='Windows'):
    """
    Gera fingerprint consistente para um OS específico

    Args:
        os_type: 'Windows', 'Mac' ou 'Linux'

    Returns:
        dict: Fingerprint coerente com o OS
    """
    # Filtrar User-Agents por OS
    if os_type == 'Windows':
        user_agents = [ua for ua in USER_AGENTS if 'Windows' in ua]
        viewports = VIEWPORTS  # Todos os viewports
    elif os_type == 'Mac':
        user_agents = [ua for ua in USER_AGENTS if 'Macintosh' in ua]
        viewports = [
            {'width': 1440, 'height': 900},   # MacBook Air
            {'width': 1920, 'height': 1080},  # iMac
            {'width': 2560, 'height': 1440},  # iMac Retina
        ]
    else:  # Linux
        user_agents = [ua for ua in USER_AGENTS if 'X11' in ua or 'Linux' in ua]
        if not user_agents:  # Fallback se não houver Linux UAs
            user_agents = USER_AGENTS[:3]
        viewports = VIEWPORTS

    return {
        'user_agent': random.choice(user_agents),
        'viewport': random.choice(viewports),
        'timezone': random.choice(TIMEZONES),
        'locale': random.choice(LOCALES),
        'os': os_type
    }


def get_weighted_random_os():
    """
    Seleciona OS com distribuição realista (70% Windows, 20% Mac, 10% Linux)

    Returns:
        str: Nome do OS
    """
    os_list = list(OS_WEIGHTS.keys())
    weights = list(OS_WEIGHTS.values())
    return random.choices(os_list, weights=weights)[0]


def get_realistic_fingerprint():
    """
    Gera fingerprint com distribuição realista de OS

    Returns:
        dict: Fingerprint com OS distribuído realisticamente
    """
    os_type = get_weighted_random_os()
    return get_fingerprint_for_os(os_type)


def fingerprint_to_string(fingerprint):
    """
    Converte fingerprint para string legível

    Args:
        fingerprint: Dict do fingerprint

    Returns:
        str: Representação em string
    """
    return (
        f"UA: {fingerprint['user_agent'][:50]}...\n"
        f"Viewport: {fingerprint['viewport']['width']}x{fingerprint['viewport']['height']}\n"
        f"Timezone: {fingerprint['timezone']}\n"
        f"Locale: {fingerprint['locale']}"
    )


if __name__ == "__main__":
    # Teste do fingerprint rotator
    print("="*60)
    print("🧪 TESTE - Fingerprint Rotator")
    print("="*60)

    print("\n1. Fingerprint Aleatório Simples:")
    print("-"*60)
    fp1 = get_random_fingerprint()
    print(fingerprint_to_string(fp1))

    print("\n2. Fingerprint Windows:")
    print("-"*60)
    fp2 = get_fingerprint_for_os('Windows')
    print(fingerprint_to_string(fp2))

    print("\n3. Fingerprint Mac:")
    print("-"*60)
    fp3 = get_fingerprint_for_os('Mac')
    print(fingerprint_to_string(fp3))

    print("\n4. Fingerprint Realístico (com distribuição de OS):")
    print("-"*60)
    for i in range(5):
        fp = get_realistic_fingerprint()
        print(f"\n{i+1}. OS: {fp.get('os', 'N/A')}")
        print(f"   Viewport: {fp['viewport']['width']}x{fp['viewport']['height']}")
        print(f"   Timezone: {fp['timezone']}")

    print("\n✅ Teste concluído!")
