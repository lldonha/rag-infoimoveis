#!/usr/bin/env python3
"""
Definição de segmentos de mercado de Campo Grande/MS.
Cada segmento representa uma combinação de: região + tipo + faixa de preço.

Este arquivo é usado pelo scraper_by_segments.py para dividir o scraping
em sessões curtas e seguras, evitando bloqueios.
"""

# ============================================
# SEGMENTOS DE MERCADO - CAMPO GRANDE/MS
# ============================================

MARKET_SEGMENTS = {
    # ============================================
    # REGIÃO SEGREDO (Popular)
    # ============================================
    "segredo_casa_100_200k": {
        "name": "Segredo - Casas 100-200k",
        "region": "regiao-segredo",
        "property_type": "casa-terrea",
        "price_min": 100000,
        "price_max": 200000,
        "expected_count": 50,
        "priority": "high",
        "description": "Casas térreas populares no bairro Segredo"
    },
    "segredo_casa_200_400k": {
        "name": "Segredo - Casas 200-400k",
        "region": "regiao-segredo",
        "property_type": "casa-terrea",
        "price_min": 200000,
        "price_max": 400000,
        "expected_count": 30,
        "priority": "medium",
        "description": "Casas térreas de médio padrão no Segredo"
    },

    # ============================================
    # REGIÃO CENTRO (Apartamentos)
    # ============================================
    "centro_apto_150_300k": {
        "name": "Centro - Apartamentos 150-300k",
        "region": "regiao-centro",
        "property_type": "apartamento",
        "price_min": 150000,
        "price_max": 300000,
        "expected_count": 80,
        "priority": "high",
        "description": "Apartamentos no centro da cidade"
    },
    "centro_apto_300_500k": {
        "name": "Centro - Apartamentos 300-500k",
        "region": "regiao-centro",
        "property_type": "apartamento",
        "price_min": 300000,
        "price_max": 500000,
        "expected_count": 40,
        "priority": "medium",
        "description": "Apartamentos de médio/alto padrão no centro"
    },

    # ============================================
    # REGIÃO PROSA (Classe Média Alta)
    # ============================================
    "prosa_casa_200_400k": {
        "name": "Prosa - Casas 200-400k",
        "region": "regiao-prosa",
        "property_type": "casa-terrea",
        "price_min": 200000,
        "price_max": 400000,
        "expected_count": 120,
        "priority": "high",
        "description": "Casas na região da Prosa (bairro nobre)"
    },
    "prosa_sobrado_400_700k": {
        "name": "Prosa - Sobrados 400-700k",
        "region": "regiao-prosa",
        "property_type": "sobrado",
        "price_min": 400000,
        "price_max": 700000,
        "expected_count": 60,
        "priority": "medium",
        "description": "Sobrados de alto padrão na Prosa"
    },

    # ============================================
    # JARDIM DOS ESTADOS (Premium)
    # ============================================
    "jardim_estados_300_500k": {
        "name": "Jardim Estados - Casas 300-500k",
        "region": "regiao-jardim-estados",
        "property_type": "casa-terrea",
        "price_min": 300000,
        "price_max": 500000,
        "expected_count": 90,
        "priority": "medium",
        "description": "Casas no Jardim dos Estados (bairro nobre)"
    },
    "jardim_estados_500k_plus": {
        "name": "Jardim Estados - Casas 500k+",
        "region": "regiao-jardim-estados",
        "property_type": "casa-terrea",
        "price_min": 500000,
        "price_max": 1000000,
        "expected_count": 50,
        "priority": "low",
        "description": "Casas de alto padrão no Jardim dos Estados"
    },

    # ============================================
    # VILA NASSER (Diversificado)
    # ============================================
    "vila_nasser_100_250k": {
        "name": "Vila Nasser - Misto 100-250k",
        "region": "regiao-vila-nasser",
        "property_type": None,  # Qualquer tipo
        "price_min": 100000,
        "price_max": 250000,
        "expected_count": 70,
        "priority": "medium",
        "description": "Imóveis diversos na Vila Nasser"
    },

    # ============================================
    # OUTROS (Catch-all)
    # ============================================
    "outros_ate_200k": {
        "name": "Outras Regiões - Até 200k",
        "region": None,  # Qualquer região não coberta
        "property_type": None,
        "price_min": 0,
        "price_max": 200000,
        "expected_count": 100,
        "priority": "low",
        "description": "Imóveis populares em outras regiões"
    },
}

# ============================================
# CONFIGURAÇÕES DE SCRAPING POR MODO
# ============================================

SCRAPING_MODES = {
    # Modo conservador - seguro, sem riscos
    "conservative": {
        "delay_between_segments": 3600,  # 1 hora
        "delay_between_properties": 10,  # 10 segundos
        "properties_per_segment": 50,
        "description": "Modo mais seguro, delays longos"
    },

    # Modo balanceado - recomendado
    "balanced": {
        "delay_between_segments": 1800,  # 30 minutos
        "delay_between_properties": 8,   # 8 segundos
        "properties_per_segment": 100,
        "description": "Equilíbrio entre velocidade e segurança"
    },

    # Modo agressivo - mais rápido, risco moderado
    "aggressive": {
        "delay_between_segments": 900,   # 15 minutos
        "delay_between_properties": 5,   # 5 segundos
        "properties_per_segment": 150,
        "description": "Mais rápido, pode gerar bloqueios"
    }
}

# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def get_segment_by_id(segment_id: str) -> dict:
    """Retorna configuração de um segmento pelo ID"""
    if segment_id not in MARKET_SEGMENTS:
        raise ValueError(f"Segmento '{segment_id}' não encontrado")
    return MARKET_SEGMENTS[segment_id]


def get_segments_by_priority(priority: str) -> dict:
    """Retorna todos os segmentos de uma prioridade"""
    if priority not in ["high", "medium", "low"]:
        raise ValueError("Priority must be: high, medium, or low")

    return {
        seg_id: seg_config
        for seg_id, seg_config in MARKET_SEGMENTS.items()
        if seg_config["priority"] == priority
    }


def get_total_expected() -> int:
    """Retorna total estimado de imóveis em todos os segmentos"""
    return sum(seg["expected_count"] for seg in MARKET_SEGMENTS.values())


def list_segments(verbose: bool = False):
    """Lista todos os segmentos disponíveis"""
    print(f"\n{'='*70}")
    print(f"📋 SEGMENTOS DE MERCADO - CAMPO GRANDE/MS")
    print(f"{'='*70}\n")

    # Agrupar por prioridade
    for priority in ["high", "medium", "low"]:
        segments = get_segments_by_priority(priority)
        if not segments:
            continue

        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[priority]
        print(f"{priority_icon} PRIORIDADE {priority.upper()}\n")

        for seg_id, seg_config in segments.items():
            print(f"  • {seg_id}")
            print(f"    Nome: {seg_config['name']}")
            print(f"    Região: {seg_config['region'] or 'Qualquer'}")
            print(f"    Tipo: {seg_config['property_type'] or 'Qualquer'}")
            print(f"    Preço: R$ {seg_config['price_min']:,} - R$ {seg_config['price_max']:,}")
            print(f"    Estimado: ~{seg_config['expected_count']} imóveis")

            if verbose:
                print(f"    Descrição: {seg_config['description']}")
            print()

    total = get_total_expected()
    print(f"{'='*70}")
    print(f"📊 TOTAL ESTIMADO: ~{total} imóveis")
    print(f"{'='*70}\n")


def validate_segment_config(segment_config: dict) -> bool:
    """Valida se configuração de segmento está correta"""
    required_fields = [
        "name", "region", "property_type", "price_min",
        "price_max", "expected_count", "priority", "description"
    ]

    for field in required_fields:
        if field not in segment_config:
            print(f"❌ Campo obrigatório ausente: {field}")
            return False

    # Validar prioridade
    if segment_config["priority"] not in ["high", "medium", "low"]:
        print(f"❌ Prioridade inválida: {segment_config['priority']}")
        return False

    # Validar preços
    if segment_config["price_min"] >= segment_config["price_max"]:
        print(f"❌ price_min deve ser menor que price_max")
        return False

    return True


# ============================================
# CLI PARA TESTES
# ============================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gerenciador de segmentos de mercado")
    parser.add_argument("--list", action="store_true", help="Listar todos os segmentos")
    parser.add_argument("--verbose", action="store_true", help="Modo verboso")
    parser.add_argument("--priority", type=str, help="Filtrar por prioridade (high/medium/low)")
    parser.add_argument("--validate", action="store_true", help="Validar configurações")

    args = parser.parse_args()

    if args.list:
        list_segments(verbose=args.verbose)

    elif args.priority:
        segments = get_segments_by_priority(args.priority)
        print(f"\n📋 Segmentos com prioridade '{args.priority}':\n")
        for seg_id, seg_config in segments.items():
            print(f"  • {seg_id} - {seg_config['name']}")
        print()

    elif args.validate:
        print("\n🔍 Validando configurações...\n")
        all_valid = True
        for seg_id, seg_config in MARKET_SEGMENTS.items():
            print(f"Validando: {seg_id}... ", end="")
            if validate_segment_config(seg_config):
                print("✅")
            else:
                print("❌")
                all_valid = False

        if all_valid:
            print(f"\n✅ Todas as configurações são válidas!")
        else:
            print(f"\n❌ Algumas configurações têm erros")

    else:
        parser.print_help()
