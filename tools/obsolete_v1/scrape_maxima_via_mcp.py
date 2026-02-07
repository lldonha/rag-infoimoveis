#!/usr/bin/env python3
"""
Scraper de Extração Máxima - Via Playwright MCP
================================================
Usa o Playwright MCP para navegação confiável
Extrai ABSOLUTAMENTE TUDO de um imóvel
"""

import json
import os
from pathlib import Path
from datetime import datetime

# URL de teste
TEST_URL = "https://www.infoimoveis.com.br/imovel/venda-area-jardim-bela-vista/55162"

OUTPUT_DIR = Path(".tmp/maxima_extracao")
IMAGES_DIR = OUTPUT_DIR / "images"

# Criar diretórios
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("🏠 SCRAPER DE EXTRAÇÃO MÁXIMA - VIA PLAYWRIGHT MCP")
print("=" * 80)
print(f"\n📍 URL: {TEST_URL}")
print(f"\n📁 Output: {OUTPUT_DIR.absolute()}")
print(f"🖼️  Images: {IMAGES_DIR.absolute()}")
print("\n" + "=" * 80)
print("\n⚠️  Este script precisa ser executado via Claude Code com MCP Playwright")
print("    Use o skill /playwright ou chame diretamente via MCP\n")
print("=" * 80)

# Instruções para o usuário
instructions = """
INSTRUÇÕES PARA EXECUÇÃO:

1. Use o Playwright MCP disponível no sistema
2. Navegue para: {url}
3. Aguarde Cloudflare passar (8-12 segundos)
4. Execute os seguintes extrações:

DADOS BÁSICOS:
- Título (h1)
- Preço (procure "VALOR TOTAL:")
- Tipo do imóvel (tabela: "Tipo")
- Finalidade (tabela: "Finalidade")

LOCALIZAÇÃO:
- Bairro (tabela: "Bairro")
- Cidade/UF (tabela: "Cidade/UF")
- Endereço (tabela: "Endereço")

ÁREAS:
- Área total (tabela: "Área total")
- Área construída (tabela: "Área construída")
- Área útil (tabela: "Área útil")

CÔMODOS:
- Quartos (lista .itens li com "quarto")
- Suítes (lista .itens li com "suíte")
- Banheiros/WC social (lista .itens li com "wc social")
- Vagas (lista .itens li com "vaga")

PREÇOS:
- IPTU (tabela: "IPTU")
- Condomínio (tabela: "Condomínio")

DESCRIÇÃO:
- Descrição principal (.descricao .texto)
- Observações (.observacoes .texto)
- Todas características (lista .itens li)

ANUNCIANTE:
- Nome (.anunciante .nome, .corretor .nome)
- CRECI (procure "CRECI:")
- Telefone (.telefone, .fone, [class*="tel"])

IMAGENS (CRÍTICO):
- Buscar TODAS as imagens com seletores:
  * img[src*="/fotos/"]
  * img[src*="stored/imoveis"]
  * img[data-src*="/fotos/"]
  * .galeria img
  * [class*="foto"] img
- Para CADA imagem:
  * Fazer download local
  * Salvar em: {images_dir}
  * Nomear como: image_01_<hash>.jpg, image_02_<hash>.jpg, etc.

HTML BRUTO:
- Salvar HTML completo em: {output_dir}/page_raw.html

SCREENSHOT:
- Capturar screenshot full-page: {output_dir}/page_screenshot.png

RESULTADO FINAL:
- Salvar JSON completo em: {output_dir}/imovel_completo.json
- Estrutura JSON:
  {{
    "metadata": {{ "source_url", "scraped_at", "scraper_version" }},
    "basic_info": {{ "title", "property_type", "transaction_type" }},
    "location": {{ "neighborhood", "city_state", "address" }},
    "areas": {{ "area_total_m2", "area_built_m2", "area_util_m2" }},
    "rooms": {{ "bedrooms", "suites", "bathrooms", "parking_spaces" }},
    "prices": {{ "price_brl", "iptu_annual_brl", "condominium_fee_brl" }},
    "features": [ lista de características ],
    "description": {{ "main", "observations" }},
    "advertiser": {{ "name", "creci", "phone" }},
    "images": [
      {{ "index": 1, "url": "...", "local_path": "...", "filename": "..." }},
      ...
    ],
    "raw_data": {{ "html_file", "screenshot_file", "html_length" }}
  }}
""".format(url=TEST_URL, images_dir=IMAGES_DIR, output_dir=OUTPUT_DIR)

print(instructions)
