#!/usr/bin/env python3
"""
Análise Visual de Imagens - IA
================================
Analisa fotos de imóveis para extrair:
- Estado de conservação (novo, bom, regular, ruim)
- Idade aparente (anos estimados)
- Padrão construtivo (alto, médio, baixo)
- Tipo de pavimentação visível

Usa: Groq (FREE, rápido) ou Ollama (local)
"""

import os
import json
import base64
from pathlib import Path
from typing import Dict, List

# Configuração
USE_GROQ = True  # True = Groq (FREE online), False = Ollama (local)


def analyze_image_with_groq(image_path: str) -> Dict:
    """
    Analisa uma imagem usando Groq Vision
    """
    try:
        from groq import Groq
    except ImportError:
        print("❌ Groq não instalado. Execute: pip install groq")
        return {}

    # API Key (deve estar em .env)
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("⚠️  GROQ_API_KEY não encontrada no .env")
        return {}

    client = Groq(api_key=api_key)

    # Ler imagem e converter para base64
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # Prompt estruturado
    prompt = """
Analise esta foto de imóvel e retorne APENAS um JSON válido com:

{
  "estado_conservacao": "novo|bom|regular|ruim",
  "idade_aparente_anos": <número ou null>,
  "padrao_construtivo": "alto|médio|baixo|indeterminado",
  "pavimentacao": "asfalto|calçada|terra|indeterminado",
  "observacoes": "<texto breve>"
}

Critérios:
- estado_conservacao: 
  * novo = construção recente, sem desgaste
  * bom = bem conservado, pequenos sinais de uso
  * regular = desgaste visível, precisa manutenção
  * ruim = deteriorado, precisa reforma urgente

- idade_aparente_anos: estimar anos desde construção (0-50)

- padrao_construtivo:
  * alto = acabamentos de qualidade, arquitetura elaborada
  * médio = padrão comum, acabamentos normais
  * baixo = construção simples, acabamentos básicos

RETORNE APENAS O JSON, SEM EXPLICAÇÕES.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",  # Groq Vision
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            },
                        },
                    ],
                }
            ],
            temperature=0.1,
            max_tokens=300,
        )

        # Parsear resposta
        result_text = response.choices[0].message.content.strip()

        # Extrair JSON (remover markdown se houver)
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        result = json.loads(result_text)
        return result

    except Exception as e:
        print(f"  ❌ Erro ao analisar imagem: {e}")
        return {}


def analyze_image_with_ollama(image_path: str) -> Dict:
    """
    Analisa uma imagem usando Ollama (local)
    """
    try:
        import ollama
    except ImportError:
        print("❌ Ollama não instalado. Execute: pip install ollama")
        return {}

    prompt = """
Analise esta foto de imóvel e retorne JSON com:
{
  "estado_conservacao": "novo|bom|regular|ruim",
  "idade_aparente_anos": <número ou null>,
  "padrao_construtivo": "alto|médio|baixo|indeterminado",
  "pavimentacao": "asfalto|calçada|terra|indeterminado",
  "observacoes": "<texto breve>"
}
"""

    try:
        response = ollama.chat(
            model="llava",  # Ollama vision model
            messages=[{"role": "user", "content": prompt, "images": [image_path]}],
        )

        result_text = response["message"]["content"]

        # Extrair JSON
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        result = json.loads(result_text)
        return result

    except Exception as e:
        print(f"  ❌ Erro ao analisar imagem com Ollama: {e}")
        return {}


def analyze_property_images(images_dir: Path) -> List[Dict]:
    """
    Analisa todas as imagens de um imóvel
    """
    results = []

    image_files = sorted(images_dir.glob("image_*.jpg"))

    print(f"\n🖼️  Analisando {len(image_files)} imagens com IA...")
    print(f"   Método: {'Groq (online)' if USE_GROQ else 'Ollama (local)'}\n")

    for img_file in image_files:
        print(f"  📸 {img_file.name}...")

        if USE_GROQ:
            analysis = analyze_image_with_groq(str(img_file))
        else:
            analysis = analyze_image_with_ollama(str(img_file))

        if analysis:
            results.append({"filename": img_file.name, "analysis": analysis})
            print(f"    ✓ Estado: {analysis.get('estado_conservacao', 'N/A')}")
            print(f"    ✓ Idade: {analysis.get('idade_aparente_anos', 'N/A')} anos")
        else:
            print(f"    ✗ Falha na análise")

    return results


def aggregate_analyses(analyses: List[Dict]) -> Dict:
    """
    Agrega análises de múltiplas imagens
    """
    if not analyses:
        return {}

    # Pegar consenso/média
    estados = [
        a["analysis"].get("estado_conservacao") for a in analyses if a.get("analysis")
    ]
    idades = [
        a["analysis"].get("idade_aparente_anos")
        for a in analyses
        if a.get("analysis") and a["analysis"].get("idade_aparente_anos")
    ]
    padroes = [
        a["analysis"].get("padrao_construtivo") for a in analyses if a.get("analysis")
    ]

    # Consenso (moda)
    from collections import Counter

    result = {
        "estado_conservacao_consenso": Counter(estados).most_common(1)[0][0]
        if estados
        else None,
        "idade_aparente_media": round(sum(idades) / len(idades)) if idades else None,
        "padrao_construtivo_consenso": Counter(padroes).most_common(1)[0][0]
        if padroes
        else None,
        "total_imagens_analisadas": len(analyses),
        "analises_individuais": analyses,
    }

    return result


def main():
    """Teste do analisador"""

    # Diretório com as imagens
    images_dir = Path(".tmp/maxima_extracao/images")

    if not images_dir.exists():
        print(f"❌ Diretório não encontrado: {images_dir}")
        return

    print("=" * 80)
    print("🔬 ANÁLISE VISUAL DE IMAGENS - IA")
    print("=" * 80)

    # Analisar todas as imagens
    analyses = analyze_property_images(images_dir)

    # Agregar resultados
    summary = aggregate_analyses(analyses)

    # Salvar JSON
    output_file = images_dir.parent / "visual_analysis.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # Resumo
    print("\n" + "=" * 80)
    print("✅ ANÁLISE COMPLETA!")
    print("=" * 80)
    print(f"\n📊 Resumo (consenso de {summary['total_imagens_analisadas']} imagens):")
    print(
        f"  • Estado de conservação: {summary.get('estado_conservacao_consenso', 'N/A')}"
    )
    print(f"  • Idade aparente: {summary.get('idade_aparente_media', 'N/A')} anos")
    print(
        f"  • Padrão construtivo: {summary.get('padrao_construtivo_consenso', 'N/A')}"
    )
    print(f"\n💾 Detalhes salvos em: {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
