#!/usr/bin/env python3
"""
Análise Visual Batch - Processa imagens com Groq
"""

import os
import json
import base64
from pathlib import Path
from groq import Groq

# Config - Ler do .env
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    # Tentar ler diretamente do arquivo
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("GROQ_API_KEY="):
                    GROQ_API_KEY = line.strip().split("=", 1)[1]
                    break

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY não encontrada no .env")

client = Groq(api_key=GROQ_API_KEY)


def analyze_images_batch(base_dir: str = ".tmp/batch_resultado"):
    """
    Analisa imagens de todos os imóveis processados
    """
    base_path = Path(base_dir)

    # Encontrar todos os diretórios de imóveis
    property_dirs = sorted(
        [
            d
            for d in base_path.iterdir()
            if d.is_dir() and d.name.startswith("property_")
        ]
    )

    print(f"🤖 Analisando {len(property_dirs)} imóveis com Groq Vision...\n")

    for prop_dir in property_dirs:
        print(f"\n{'=' * 60}")
        print(f"📸 {prop_dir.name}")
        print("=" * 60)

        json_file = prop_dir / "data.json"
        if not json_file.exists():
            print(f"  ❌ data.json não encontrado")
            continue

        # Carregar dados
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Verificar se já tem análise
        if "visual_analysis" in data:
            print(f"  ⏭️  Já analisado")
            continue

        # Pegar até 3 imagens
        images = data.get("images", [])[:3]
        if not images:
            print(f"  ⚠️  Sem imagens")
            continue

        print(f"  📊 Analisando {len(images)} imagens...")

        analyses = []
        for img_info in images:
            img_path = Path(img_info["local_path"])
            if not img_path.exists():
                print(f"    ⚠️  Imagem não encontrada: {img_path}")
                continue

            try:
                # Ler e codificar imagem
                with open(img_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode("utf-8")

                # Prompt para análise
                prompt = """Analise esta foto de imóvel e retorne APENAS um JSON válido:

{
  "estado_conservacao": "novo|bom|regular|ruim",
  "idade_aparente_anos": <número estimado ou null>,
  "padrao_construtivo": "alto|médio|baixo",
  "pavimentacao": "ceramica|porcelanato|madeira|cimento|asfalto|indeterminado",
  "observacoes": "<breve descrição do que é visível na foto>"
}

Critérios:
- estado_conservacao: avalie sinais de desgaste, pintura, conservação geral
- idade_aparente_anos: estime anos desde construção (0-100)
- padrao_construtivo: avalie acabamentos e materiais visíveis
- pavimentacao: tipo de piso/pavimento visível (interno ou externo)

Retorne APENAS o JSON, sem explicações adicionais."""

                # Chamar Groq
                response = client.chat.completions.create(
                    model="llava-v1.5-7b-4096-preview",
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
                    max_tokens=400,
                )

                result = response.choices[0].message.content.strip()

                # Extrair JSON
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0]
                elif "```" in result:
                    result = result.split("```")[1]

                analysis = json.loads(result.strip())
                analyses.append(analysis)
                print(
                    f"    ✅ {img_info['filename']}: {analysis.get('estado_conservacao', 'N/A')}"
                )

            except Exception as e:
                print(f"    ❌ Erro: {e}")
                continue

        # Agregar análises
        if analyses:
            from collections import Counter

            conservation = Counter(
                [a.get("estado_conservacao", "indeterminado") for a in analyses]
            ).most_common(1)[0][0]
            padrao = Counter(
                [a.get("padrao_construtivo", "indeterminado") for a in analyses]
            ).most_common(1)[0][0]
            pavimentacao = Counter(
                [a.get("pavimentacao", "indeterminado") for a in analyses]
            ).most_common(1)[0][0]

            idades = [
                a.get("idade_aparente_anos")
                for a in analyses
                if a.get("idade_aparente_anos")
            ]
            idade_avg = round(sum(idades) / len(idades)) if idades else None

            visual_analysis = {
                "estado_conservacao": conservation,
                "idade_aparente_anos": idade_avg,
                "padrao_construtivo": padrao,
                "pavimentacao": pavimentacao,
                "analises_realizadas": len(analyses),
            }

            data["visual_analysis"] = visual_analysis

            # Salvar JSON atualizado
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"\n  ✅ Análise salva:")
            print(f"     Conservação: {conservation}")
            print(f"     Idade: {idade_avg} anos")
            print(f"     Padrão: {padrao}")
            print(f"     Pavimentação: {pavimentacao}")
        else:
            print(f"  ❌ Nenhuma análise realizada")


if __name__ == "__main__":
    analyze_images_batch()
