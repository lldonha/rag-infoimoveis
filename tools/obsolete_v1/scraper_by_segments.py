#!/usr/bin/env python3
"""
Scraper Segmentado por Região e Faixa de Preço
==============================================
Evita bloqueios dividindo carga em sessões curtas (20-30 min).
Cada segmento é processado separadamente com delays longos entre eles.

Uso:
    # Listar segmentos
    python scraper_by_segments.py --list-segments

    # Scrape 1 segmento (teste)
    python scraper_by_segments.py --segment segredo_casa_100_200k --limit 10

    # Scrape múltiplos segmentos
    python scraper_by_segments.py --segments "segredo_casa_100_200k,centro_apto_150_300k" --save-to-db

    # Scrape TODOS os segmentos (produção)
    python scraper_by_segments.py --all --save-to-db --segment-delay 3600
"""

import asyncio
import argparse
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Importar módulos existentes
sys.path.append(os.path.dirname(__file__))

from market_segments import MARKET_SEGMENTS, SCRAPING_MODES
from scraper_production import PropertyData, parse_property_page
from property_saver import insert_property, get_property_stats
from rate_limiter import SmartRateLimiter
from playwright.async_api import async_playwright


class SegmentedScraper:
    """Scraper que processa segmentos de mercado separadamente"""

    def __init__(self, delay_between_segments: int = 3600, mode: str = "conservative"):
        """
        Args:
            delay_between_segments: Delay em segundos entre cada segmento (padrão: 3600 = 1h)
            mode: Modo de scraping (conservative/balanced/aggressive)
        """
        self.delay = delay_between_segments
        self.mode = mode
        self.rate_limiter = SmartRateLimiter()
        self.results = []
        self.playwright = None
        self.browser = None

        # Carregar configurações do modo
        if mode in SCRAPING_MODES:
            self.mode_config = SCRAPING_MODES[mode]
        else:
            print(f"⚠️  Modo '{mode}' inválido, usando 'conservative'")
            self.mode_config = SCRAPING_MODES["conservative"]

    async def _init_browser(self):
        """Inicializa browser se necessário"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)

    async def _close_browser(self):
        """Fecha browser se estiver aberto"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def _scrape_single_url(self, url: str) -> Optional[PropertyData]:
        """
        Scrape simples de uma única URL

        Args:
            url: URL do imóvel

        Returns:
            PropertyData ou None em caso de erro
        """
        await self._init_browser()

        context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()

        try:
            # Navegar para a página
            await page.goto(url, timeout=30000, wait_until="networkidle")

            # Parse usando função existente
            property_data = await parse_property_page(page, url)

            return property_data

        except Exception as e:
            print(f"   ⚠️  Erro no scrape: {e}")
            return None
        finally:
            await context.close()

    async def discover_urls(
        self,
        segment_config: Dict,
        limit: Optional[int] = None
    ) -> List[str]:
        """
        Descobre URLs de imóveis no segmento.

        TODO: Implementar discovery com filtros reais do site.
        Por enquanto retorna lista mock para testes.

        Args:
            segment_config: Configuração do segmento
            limit: Limite de URLs (None = todas)

        Returns:
            Lista de URLs para scrape
        """
        # TODO: Implementar discovery real usando:
        # - segment_config['region'] → filtro de região
        # - segment_config['property_type'] → filtro de tipo
        # - segment_config['price_min'] / ['price_max'] → filtro de preço

        # Por enquanto, usar URLs de teste
        # Na implementação real, chamar discovery_filtered.py

        print(f"🔍 Discovery: Buscando imóveis para {segment_config['name']}...")
        print(f"   Região: {segment_config['region'] or 'Qualquer'}")
        print(f"   Tipo: {segment_config['property_type'] or 'Qualquer'}")
        print(f"   Preço: R$ {segment_config['price_min']:,} - R$ {segment_config['price_max']:,}")

        # Mock URLs para teste (substituir por discovery real)
        mock_urls = [
            "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-4-quartos-jardim-mansoes-campo-grande-ms-220m2-id-2788808",
            "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-3-quartos-coronel-antonino-campo-grande-ms-158m2-id-2814468",
            "https://www.infoimoveis.com.br/imovel/venda-casa-terrea-3-quartos-parque-dos-poderes-campo-grande-ms-105m2-id-2756732",
        ]

        if limit:
            mock_urls = mock_urls[:limit]

        await asyncio.sleep(2)  # Simular delay de discovery

        return mock_urls

    async def scrape_segment(
        self,
        segment_id: str,
        segment_config: Dict,
        limit: Optional[int] = None,
        save_to_db: bool = True
    ) -> Dict:
        """
        Scrape um único segmento de mercado.

        Args:
            segment_id: ID do segmento (ex: "segredo_casa_100_200k")
            segment_config: Configuração do segmento
            limit: Limite de imóveis (None = todos)
            save_to_db: Salvar no PostgreSQL?

        Returns:
            Dict com estatísticas do scraping
        """
        print(f"\n{'='*70}")
        print(f"🎯 SEGMENTO: {segment_config['name']}")
        print(f"{'='*70}")
        print(f"📍 Região: {segment_config['region'] or 'Qualquer'}")
        print(f"🏠 Tipo: {segment_config['property_type'] or 'Qualquer'}")
        print(f"💰 Preço: R$ {segment_config['price_min']:,} - R$ {segment_config['price_max']:,}")
        print(f"📊 Esperado: ~{segment_config['expected_count']} imóveis")
        print(f"⚙️  Modo: {self.mode} ({self.mode_config['description']})")
        print(f"{'='*70}\n")

        start_time = datetime.now()

        # 1. Discovery de URLs
        urls = await self.discover_urls(segment_config, limit)
        print(f"✅ Discovery completo: {len(urls)} URLs encontradas\n")

        if not urls:
            return {
                "segment_id": segment_id,
                "segment_name": segment_config["name"],
                "status": "no_urls",
                "urls_found": 0,
                "scraped": 0,
                "errors": 0,
                "success_rate": 0,
                "duration_seconds": 0
            }

        # 2. Scrape de cada URL
        scraped = []
        errors = []

        try:
            for idx, url in enumerate(urls, 1):
                try:
                    print(f"[{idx}/{len(urls)}] 🔄 Scraping: {url}")

                    # Rate limiting (usar configuração do modo)
                    delay = self.mode_config['delay_between_properties']
                    print(f"   ⏱️  Aguardando {delay}s (rate limit)...")
                    await asyncio.sleep(delay)

                    # Scrape da página
                    property_data = await self._scrape_single_url(url)

                    if property_data:
                        scraped.append(property_data)

                        completeness = property_data.completeness * 100
                        print(f"   ✅ Sucesso! Completude: {completeness:.0f}%")

                        # Salvar no banco?
                        if save_to_db:
                            try:
                                insert_property(property_data.to_dict())
                                print(f"   💾 Salvo no PostgreSQL")
                            except Exception as e:
                                print(f"   ⚠️  Erro ao salvar no banco: {e}")
                    else:
                        errors.append(url)
                        print(f"   ❌ Falha ao extrair dados")

                except KeyboardInterrupt:
                    print(f"\n\n⚠️  Interrompido pelo usuário!")
                    break

                except Exception as e:
                    errors.append(url)
                    print(f"   ❌ Erro: {e}")

        finally:
            # Fechar browser após o segmento
            await self._close_browser()

        # 3. Estatísticas do segmento
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        result = {
            "segment_id": segment_id,
            "segment_name": segment_config["name"],
            "status": "success" if scraped else "failed",
            "urls_found": len(urls),
            "scraped": len(scraped),
            "errors": len(errors),
            "success_rate": len(scraped) / len(urls) if urls else 0,
            "duration_seconds": duration,
            "duration_minutes": duration / 60,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "avg_completeness": sum(p.completeness for p in scraped) / len(scraped) if scraped else 0
        }

        # Resumo do segmento
        print(f"\n{'─'*70}")
        print(f"📊 RESULTADO DO SEGMENTO: {segment_config['name']}")
        print(f"{'─'*70}")
        print(f"✅ Sucesso: {len(scraped)}/{len(urls)} ({result['success_rate']:.1%})")
        print(f"❌ Erros: {len(errors)}")
        print(f"📈 Completude média: {result['avg_completeness']:.1%}")
        print(f"⏱️  Duração: {duration/60:.1f} minutos")
        print(f"{'─'*70}\n")

        return result

    async def scrape_all_segments(
        self,
        segment_ids: Optional[List[str]] = None,
        save_to_db: bool = True
    ) -> Dict:
        """
        Scrape todos os segmentos (ou lista específica).

        Args:
            segment_ids: IDs específicos ou None (todos)
            save_to_db: Salvar no PostgreSQL?

        Returns:
            Relatório completo com estatísticas
        """
        # Filtrar segmentos
        if segment_ids:
            segments = {k: v for k, v in MARKET_SEGMENTS.items() if k in segment_ids}
            if len(segments) != len(segment_ids):
                missing = set(segment_ids) - set(segments.keys())
                print(f"⚠️  Segmentos não encontrados: {missing}")
        else:
            segments = MARKET_SEGMENTS

        # Ordenar por prioridade (high → medium → low)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_segments = sorted(
            segments.items(),
            key=lambda x: priority_order[x[1]["priority"]]
        )

        print(f"\n{'#'*70}")
        print(f"🚀 INICIANDO SCRAPING SEGMENTADO")
        print(f"{'#'*70}")
        print(f"📋 Total de segmentos: {len(sorted_segments)}")
        print(f"⏱️  Delay entre segmentos: {self.delay}s ({self.delay/60:.0f} min)")
        print(f"⚙️  Modo: {self.mode}")
        print(f"💾 Salvar no banco: {'Sim' if save_to_db else 'Não'}")
        print(f"{'#'*70}\n")

        results = []

        for idx, (seg_id, seg_config) in enumerate(sorted_segments, 1):
            print(f"\n{'█'*70}")
            print(f"  SEGMENTO {idx}/{len(sorted_segments)}")
            print(f"{'█'*70}")

            # Scrape segmento
            result = await self.scrape_segment(seg_id, seg_config, save_to_db=save_to_db)
            results.append(result)

            # Delay entre segmentos (exceto último)
            if idx < len(sorted_segments):
                print(f"\n⏳ Aguardando {self.delay}s ({self.delay/60:.0f} min) antes do próximo segmento...")
                print(f"   (Isso evita bloqueios e mantém o scraping seguro)")
                await asyncio.sleep(self.delay)

        # Relatório final
        return self.generate_report(results)

    def generate_report(self, results: List[Dict]) -> Dict:
        """Gera relatório consolidado de todos os segmentos"""
        total_scraped = sum(r["scraped"] for r in results)
        total_errors = sum(r["errors"] for r in results)
        total_duration = sum(r["duration_seconds"] for r in results)

        avg_completeness = sum(r["avg_completeness"] for r in results) / len(results) if results else 0

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_segments": len(results),
            "total_scraped": total_scraped,
            "total_errors": total_errors,
            "total_duration_minutes": total_duration / 60,
            "overall_success_rate": total_scraped / (total_scraped + total_errors) if (total_scraped + total_errors) > 0 else 0,
            "avg_completeness": avg_completeness,
            "mode": self.mode,
            "segments": results
        }

        return report


async def main():
    """CLI principal"""
    parser = argparse.ArgumentParser(
        description="Scraper segmentado por região/preço",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Listar segmentos
  python scraper_by_segments.py --list-segments

  # Testar 1 segmento (10 imóveis)
  python scraper_by_segments.py --segment segredo_casa_100_200k --limit 10

  # Scrape 2 segmentos com delay de 1h
  python scraper_by_segments.py --segments "segredo_casa_100_200k,centro_apto_150_300k" --save-to-db

  # Scrape todos (produção)
  python scraper_by_segments.py --all --save-to-db --segment-delay 3600
        """
    )

    parser.add_argument(
        "--segment",
        type=str,
        help="ID de segmento específico (ex: segredo_casa_100_200k)"
    )
    parser.add_argument(
        "--segments",
        type=str,
        help="IDs de segmentos separados por vírgula"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Scrape todos os segmentos"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limite de imóveis por segmento (para testes)"
    )
    parser.add_argument(
        "--segment-delay",
        type=int,
        default=3600,
        help="Delay entre segmentos em segundos (padrão: 3600 = 1h)"
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="conservative",
        choices=["conservative", "balanced", "aggressive"],
        help="Modo de scraping (padrão: conservative)"
    )
    parser.add_argument(
        "--save-to-db",
        action="store_true",
        help="Salvar no PostgreSQL"
    )
    parser.add_argument(
        "--list-segments",
        action="store_true",
        help="Listar segmentos disponíveis e sair"
    )

    args = parser.parse_args()

    # Listar segmentos
    if args.list_segments:
        print(f"\n{'='*70}")
        print(f"📋 SEGMENTOS DISPONÍVEIS")
        print(f"{'='*70}\n")

        for priority in ["high", "medium", "low"]:
            icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[priority]
            segs = {k: v for k, v in MARKET_SEGMENTS.items() if v["priority"] == priority}

            if segs:
                print(f"{icon} PRIORIDADE {priority.upper()}\n")
                for seg_id, seg_config in segs.items():
                    print(f"  • {seg_id}")
                    print(f"    {seg_config['name']}")
                    print(f"    Estimado: ~{seg_config['expected_count']} imóveis\n")

        print(f"{'='*70}\n")
        return

    # Criar scraper
    scraper = SegmentedScraper(
        delay_between_segments=args.segment_delay,
        mode=args.mode
    )

    # Executar
    if args.segment:
        # Segmento único
        if args.segment not in MARKET_SEGMENTS:
            print(f"❌ Segmento '{args.segment}' não encontrado")
            print(f"   Use --list-segments para ver opções")
            return

        result = await scraper.scrape_segment(
            args.segment,
            MARKET_SEGMENTS[args.segment],
            limit=args.limit,
            save_to_db=args.save_to_db
        )

        # Salvar resultado individual
        filename = f".tmp/segment_{args.segment}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Path(filename).parent.mkdir(exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Resultado salvo: {filename}")

    elif args.segments:
        # Lista de segmentos
        segment_ids = [s.strip() for s in args.segments.split(",")]
        report = await scraper.scrape_all_segments(
            segment_ids=segment_ids,
            save_to_db=args.save_to_db
        )
        print_final_report(report)

    elif args.all:
        # Todos os segmentos
        report = await scraper.scrape_all_segments(save_to_db=args.save_to_db)
        print_final_report(report)

    else:
        parser.print_help()


def print_final_report(report: Dict):
    """Imprime relatório final formatado"""
    print(f"\n{'='*70}")
    print(f"📊 RELATÓRIO FINAL - SCRAPING SEGMENTADO")
    print(f"{'='*70}\n")

    print(f"⏱️  Duração total: {report['total_duration_minutes']:.1f} minutos")
    print(f"📋 Segmentos processados: {report['total_segments']}")
    print(f"✅ Total scraped: {report['total_scraped']}")
    print(f"❌ Total erros: {report['total_errors']}")
    print(f"📈 Taxa de sucesso: {report['overall_success_rate']:.1%}")
    print(f"📊 Completude média: {report['avg_completeness']:.1%}")
    print(f"⚙️  Modo: {report['mode']}")

    print(f"\n{'─'*70}")
    print(f"DETALHES POR SEGMENTO:")
    print(f"{'─'*70}\n")

    for seg in report['segments']:
        status_icon = "✅" if seg['status'] == 'success' else "❌"
        print(f"{status_icon} {seg['segment_name']}")
        print(f"   Scraped: {seg['scraped']}/{seg['urls_found']} ({seg['success_rate']:.1%})")
        print(f"   Completude: {seg['avg_completeness']:.1%}")
        print(f"   Duração: {seg['duration_minutes']:.1f} min\n")

    print(f"{'='*70}\n")

    # Salvar relatório
    filename = f".tmp/report_segmented_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    Path(filename).parent.mkdir(exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"💾 Relatório completo salvo: {filename}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Scraping interrompido pelo usuário!")
        sys.exit(0)
