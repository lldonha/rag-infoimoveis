"""
Teste em Batch com Export para Excel

Executa scraping em batches e exporta para planilha Excel visível
"""
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

sys.path.append(str(Path(__file__).parent.parent))

from tools.discovery_filtered import discover_by_preset
from tools.scraper_production import scrape_multiple_properties


def export_to_excel(properties: List[Dict], output_file: str):
    """
    Exporta dados para Excel com formatação visual

    Args:
        properties: Lista de dicionários com dados dos imóveis
        output_file: Caminho do arquivo Excel de saída
    """
    try:
        import pandas as pd
        from openpyxl import load_workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

        # Criar DataFrame
        df = pd.DataFrame(properties)

        # Reordenar colunas para melhor visualização
        columns_order = [
            'title', 'price_brl', 'property_type', 'transaction_type',
            'neighborhood', 'city', 'state',
            'area_total_m2', 'area_built_m2', 'bedrooms', 'bathrooms', 'suites', 'parking_spaces',
            'price_per_m2', 'condominium_fee_brl', 'iptu_annual_brl',
            'description', 'address', 'features',
            'advertiser_name', 'advertiser_phone',
            'source_url', 'completeness'
        ]

        # Filtrar apenas colunas existentes
        columns_order = [col for col in columns_order if col in df.columns]
        df = df[columns_order]

        # Renomear colunas para português
        column_names = {
            'title': 'Título',
            'price_brl': 'Preço (R$)',
            'property_type': 'Tipo',
            'transaction_type': 'Transação',
            'neighborhood': 'Bairro',
            'city': 'Cidade',
            'state': 'Estado',
            'area_total_m2': 'Área Total (m²)',
            'area_built_m2': 'Área Construída (m²)',
            'bedrooms': 'Quartos',
            'bathrooms': 'Banheiros',
            'suites': 'Suítes',
            'parking_spaces': 'Vagas',
            'price_per_m2': 'R$/m²',
            'condominium_fee_brl': 'Condomínio (R$)',
            'iptu_annual_brl': 'IPTU Anual (R$)',
            'description': 'Descrição',
            'address': 'Endereço',
            'features': 'Características',
            'advertiser_name': 'Anunciante',
            'advertiser_phone': 'Telefone',
            'source_url': 'URL',
            'completeness': 'Completude (%)'
        }
        df.rename(columns=column_names, inplace=True)

        # Converter completeness para porcentagem
        if 'Completude (%)' in df.columns:
            df['Completude (%)'] = (df['Completude (%)'] * 100).round(1)

        # Salvar para Excel
        df.to_excel(output_file, index=False, sheet_name='Imóveis')

        # Aplicar formatação
        wb = load_workbook(output_file)
        ws = wb['Imóveis']

        # Estilos
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # Formatar cabeçalho
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.border = border

        # Formatar células de dados
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            for cell in row:
                cell.border = border
                cell.alignment = Alignment(vertical='top', wrap_text=True)

        # Ajustar largura das colunas
        column_widths = {
            'A': 50,  # Título
            'B': 15,  # Preço
            'C': 15,  # Tipo
            'D': 12,  # Transação
            'E': 20,  # Bairro
            'F': 15,  # Cidade
            'G': 8,   # Estado
            'H': 15,  # Área Total
            'I': 15,  # Área Construída
            'J': 10,  # Quartos
            'K': 10,  # Banheiros
            'L': 10,  # Suítes
            'M': 10,  # Vagas
            'N': 12,  # R$/m²
            'O': 15,  # Condomínio
            'P': 15,  # IPTU
            'Q': 60,  # Descrição
            'R': 40,  # Endereço
            'S': 40,  # Características
            'T': 25,  # Anunciante
            'U': 18,  # Telefone
            'V': 50,  # URL
            'W': 12,  # Completude
        }

        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width

        # Congelar primeira linha
        ws.freeze_panes = 'A2'

        # Salvar
        wb.save(output_file)

        print(f"\n✅ Planilha Excel criada: {output_file}")
        print(f"   📊 Total de registros: {len(df)}")

        return True

    except ImportError as e:
        print(f"\n❌ Erro: Bibliotecas necessárias não instaladas")
        print(f"   Execute: pip install pandas openpyxl")
        return False
    except Exception as e:
        print(f"\n❌ Erro ao criar planilha: {e}")
        return False


async def main():
    print("\n" + "=" * 80)
    print("🧪 TESTE EM BATCH COM EXPORT PARA EXCEL")
    print("=" * 80)
    print(f"⏰ Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")

    # Configuração
    BATCH_SIZE = 50
    SAVE_TO_DB = True

    print(f"📋 Configuração:")
    print(f"   Batch size: {BATCH_SIZE} imóveis")
    print(f"   Salvar no banco: {'Sim' if SAVE_TO_DB else 'Não'}")
    print(f"   Preset: segredo_100_200k")
    print()

    # FASE 1: Discovery
    print("📍 FASE 1: DISCOVERY")
    print("-" * 80)

    urls = await discover_by_preset('segredo_100_200k', max_pages=3)
    print(f"\n✅ Discovery completo: {len(urls)} URLs encontradas")

    # Limitar ao batch size
    urls = urls[:BATCH_SIZE]
    print(f"📊 Processando: {len(urls)} imóveis\n")

    # FASE 2: Scraping
    print("\n📍 FASE 2: SCRAPING COM STEALTH")
    print("-" * 80 + "\n")

    stats = await scrape_multiple_properties(
        urls=urls,
        max_per_session=BATCH_SIZE,
        save_to_db=SAVE_TO_DB,
        use_stealth=True
    )

    # FASE 3: Resultados
    print("\n" + "=" * 80)
    print("📊 RESULTADO DO SCRAPING")
    print("=" * 80)

    total = len(urls)
    success = stats['success']
    errors = stats['errors']
    success_rate = (success / total * 100) if total > 0 else 0

    print(f"\n✅ Sucesso: {success}/{total}")
    print(f"❌ Erros: {errors}/{total}")
    print(f"📈 Taxa de sucesso: {success_rate:.1f}%")

    # FASE 4: Export para Excel
    if success > 0:
        print("\n" + "=" * 80)
        print("📍 FASE 3: EXPORT PARA EXCEL")
        print("=" * 80)

        # Ler dados do banco ou do stats
        if SAVE_TO_DB and success > 0:
            # Ler últimos N imóveis do banco
            try:
                from tools.property_saver import get_recent_properties
                properties = get_recent_properties(limit=success)

                if properties:
                    # Gerar nome do arquivo
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    output_dir = Path(__file__).parent.parent / '.tmp'
                    output_dir.mkdir(exist_ok=True)
                    output_file = output_dir / f'imoveis_scraped_{timestamp}.xlsx'

                    # Exportar
                    export_success = export_to_excel(properties, str(output_file))

                    if export_success:
                        print(f"\n🎉 SUCESSO! Planilha criada em:")
                        print(f"   📂 {output_file.absolute()}")
                        print(f"\n   Abra no Excel para visualizar os dados!")
                else:
                    print("\n⚠️  Nenhum dado encontrado no banco para exportar")
            except Exception as e:
                print(f"\n❌ Erro ao exportar: {e}")

    # Resumo final
    print("\n" + "=" * 80)
    if success_rate >= 80:
        print("✅ TESTE PASSOU! Sistema funcionando perfeitamente!")
    else:
        print(f"⚠️  Taxa de sucesso abaixo de 80% ({success_rate:.1f}%)")

    print("=" * 80)
    print(f"⏰ Fim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    return success_rate >= 80


if __name__ == "__main__":
    passed = asyncio.run(main())
    sys.exit(0 if passed else 1)
