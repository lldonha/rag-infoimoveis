#!/usr/bin/env python3
"""
Mapeamento JSON → Excel
========================
Converte JSON do scraper para formato da planilha de perícia
Baseado nas colunas: Endereço, Bairro, Telefone, Área Terreno, etc.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
except ImportError:
    print("❌ openpyxl não instalado. Execute: pip install openpyxl")
    exit(1)


def parse_area_to_float(area_str: str) -> Optional[float]:
    """Converte '7.397,00 m²' para 7397.0"""
    if not area_str:
        return None
    match = re.search(r"([\d.,]+)", area_str)
    if match:
        num = match.group(1).replace(".", "").replace(",", ".")
        try:
            return float(num)
        except:
            return None
    return None


def parse_price_to_float(price_val) -> Optional[float]:
    """Converte preço para float"""
    if isinstance(price_val, (int, float)):
        return float(price_val)
    if isinstance(price_val, str):
        clean = re.sub(r"[R$\s.]", "", price_val)
        clean = clean.replace(",", ".")
        try:
            return float(clean)
        except:
            return None
    return None


def extract_phone(advertiser_data: Dict) -> Optional[str]:
    """Extrai telefone do anunciante"""
    if not advertiser_data:
        return None

    # Pode ter phone_id ou phone direto
    phone = advertiser_data.get("phone") or advertiser_data.get("phone_id")
    if phone:
        return str(phone)
    return None


def map_json_to_excel_row(
    json_data: Dict, visual_analysis: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Mapeia JSON do scraper para linha da planilha Excel

    Colunas da planilha:
    1. Endereço
    2. Bairro
    3. Telefone do Informante
    4. Área do Terreno
    5. Área Construída
    6. Padrão construtivo
    7. Quartos + Wc
    8. Estado de conservação
    9. Índice fiscal
    10. Pavimentação
    11. Idade aparente
    12. Suítes
    13. Vagas de garagem coberta
    14. Data do evento
    15. Evento
    16. Geminada
    17. Multi
    18. Renda Média Bairro
    19. Valor total
    20. Valor unitário
    """

    basic = json_data.get("basic_info", {})
    location = json_data.get("location", {})
    areas = json_data.get("areas", {})
    rooms = json_data.get("rooms", {})
    prices = json_data.get("prices", {})
    features = json_data.get("features", [])
    advertiser = json_data.get("advertiser", {})
    metadata = json_data.get("metadata", {})

    # Parsear áreas
    area_total = parse_area_to_float(areas.get("area_total"))
    area_built = parse_area_to_float(areas.get("area_built"))

    # Preço
    price_brl = parse_price_to_float(prices.get("price_brl"))

    # Valor unitário (R$/m²)
    valor_unitario = None
    if price_brl and area_built:
        valor_unitario = round(price_brl / area_built, 2)
    elif price_brl and area_total:
        valor_unitario = round(price_brl / area_total, 2)

    # Quartos + WC
    bedrooms = rooms.get("bedrooms", 0) or 0
    bathrooms = rooms.get("bathrooms", 0) or 0
    quartos_wc = bedrooms + bathrooms if (bedrooms or bathrooms) else None

    # Análise visual (se disponível)
    estado_conservacao = None
    idade_aparente = None
    padrao_construtivo = None
    pavimentacao = None

    if visual_analysis:
        estado_conservacao = visual_analysis.get("estado_conservacao_consenso")
        idade_aparente = visual_analysis.get("idade_aparente_media")
        padrao_construtivo = visual_analysis.get("padrao_construtivo_consenso")

        # Pavimentação pode vir das features ou da análise visual
        # Procurar "asfalto" nas features
        for feature in features:
            if "asfalto" in feature.lower():
                pavimentacao = "Asfalto"
                break
            elif "calçada" in feature.lower() or "calcada" in feature.lower():
                pavimentacao = "Calçada"
                break

    # Geminada (procurar nas features/observações)
    geminada = None
    desc_text = str(json_data.get("description", {})).lower()
    if "geminada" in desc_text or "geminado" in desc_text:
        geminada = "Sim"
    elif "esquina" in desc_text:
        geminada = "Esquina"

    # Mapear para colunas da planilha
    row = {
        "Endereço": location.get("address"),
        "Bairro": location.get("neighborhood"),
        "Telefone do Informante": extract_phone(advertiser),
        "Área do Terreno": area_total,
        "Área Construída": area_built,
        "Padrão construtivo": padrao_construtivo,
        "Quartos + Wc": quartos_wc,
        "Estado de conservação": estado_conservacao,
        "Índice fiscal": None,  # Não disponível
        "Pavimentação": pavimentacao,
        "Idade aparente": idade_aparente,
        "Suítes": rooms.get("suites"),
        "Vagas de garagem coberta": rooms.get("parking_spaces"),
        "Data do evento": metadata.get("scraped_at", "").split("T")[0]
        if metadata.get("scraped_at")
        else None,
        "Evento": "Scraping",
        "Geminada": geminada,
        "Multi": None,  # Não sei o que significa
        "Renda Média Bairro": None,  # Dados externos
        "Valor total": price_brl,
        "Valor unitário": valor_unitario,
    }

    return row


def create_excel_from_json(
    json_file: Path,
    visual_analysis_file: Optional[Path] = None,
    output_file: Optional[Path] = None,
):
    """
    Cria Excel formatado a partir do JSON
    """

    # Ler JSON
    with open(json_file, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # Ler análise visual (se existir)
    visual_analysis = None
    if visual_analysis_file and visual_analysis_file.exists():
        with open(visual_analysis_file, "r", encoding="utf-8") as f:
            visual_analysis = json.load(f)

    # Mapear para linha Excel
    row_data = map_json_to_excel_row(json_data, visual_analysis)

    # Criar workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Imóveis"

    # Definir colunas (headers)
    headers = list(row_data.keys())

    # Estilo do header
    header_fill = PatternFill(
        start_color="4472C4", end_color="4472C4", fill_type="solid"
    )
    header_font = Font(bold=True, color="FFFFFF", size=11)
    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # Escrever headers
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border

    # Escrever dados
    for col_idx, header in enumerate(headers, start=1):
        value = row_data[header]
        cell = ws.cell(row=2, column=col_idx, value=value)
        cell.border = border

        # Formatação especial para números
        if isinstance(value, float):
            if header in ["Área do Terreno", "Área Construída"]:
                cell.number_format = "#,##0.00"
            elif header in ["Valor total", "Valor unitário"]:
                cell.number_format = "R$ #,##0.00"

    # Ajustar largura das colunas
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column].width = adjusted_width

    # Salvar
    if not output_file:
        output_file = json_file.parent / "imovel_planilha.xlsx"

    wb.save(output_file)

    return output_file, row_data


def main():
    """Teste do mapeamento"""

    json_file = Path(".tmp/maxima_extracao/imovel_completo.json")
    visual_file = Path(".tmp/maxima_extracao/visual_analysis.json")

    if not json_file.exists():
        print(f"❌ JSON não encontrado: {json_file}")
        return

    print("=" * 80)
    print("📊 MAPEAMENTO JSON → EXCEL")
    print("=" * 80)
    print(f"\n📁 JSON: {json_file}")
    if visual_file.exists():
        print(f"🔬 Análise Visual: {visual_file}")
    else:
        print(f"⚠️  Análise Visual não encontrada (opcional)")

    # Criar Excel
    output_file, row_data = create_excel_from_json(
        json_file, visual_file if visual_file.exists() else None
    )

    print(f"\n✅ Excel criado: {output_file}")

    # Mostrar resumo dos dados mapeados
    print(f"\n📊 Campos preenchidos:")
    filled = 0
    for key, value in row_data.items():
        if value is not None and value != "":
            filled += 1
            print(f"  ✅ {key}: {value}")
        else:
            print(f"  ⚠️  {key}: (vazio)")

    print(
        f"\n📈 Completude: {filled}/{len(row_data)} ({filled / len(row_data) * 100:.0f}%)"
    )
    print("=" * 80)


if __name__ == "__main__":
    main()
