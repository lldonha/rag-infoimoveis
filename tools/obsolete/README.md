# 🗄️ Arquivos Obsoletos

**Data:** 2026-02-05
**Motivo:** Reorganização após implementação do Playwright Stealth

---

## 📋 Arquivos Nesta Pasta

### Testes da Fase RAG (0.5-0.7)
Estes arquivos foram usados para testar o sistema RAG completo (pgvector, embeddings, query).
**Status:** Funcionais mas não necessários na fase atual (scraping).

- **test_05_pgvector.py** - Setup e teste do pgvector
- **test_06_embeddings.py** - Geração e teste de embeddings
- **test_07_rag_system.py** - Sistema RAG completo
- **test_08_scraping_system.py** - Teste do sistema de scraping antigo

**Quando usar novamente:** Fase RAG (depois de coletar 1000+ imóveis)

---

### Scripts Manuais/Debug
- **quick_test_scraper.py** - Teste rápido antigo (substituído por `test_discovery.py`)
- **manual_cloudflare_bypass.py** - Bypass manual Cloudflare (substituído por `scraper_stealth.py`)
- **inspect_page.py** - Inspeção manual de páginas (debug)

**Motivo da remoção:** Substituídos por ferramentas melhores (stealth mode)

---

## 🔄 Substitutos Recomendados

| Arquivo Obsoleto | Usar Agora |
|------------------|------------|
| `quick_test_scraper.py` | `tools/test_discovery.py` |
| `manual_cloudflare_bypass.py` | `tools/scraper_stealth.py` |
| `test_08_scraping_system.py` | `tools/test_discovery.py` + `workflow_complete.py` |
| `inspect_page.py` | `scraper_stealth.py` com debug |

---

## ⚠️ IMPORTANTE

**NÃO DELETE ESTES ARQUIVOS!**

Eles podem ser úteis para:
1. Referência histórica
2. Recuperação de código específico
3. Fase RAG futura (testes 05-07)
4. Debug em caso de problemas

---

## 📖 Documentação

Para entender a estrutura atual do projeto, consulte:
- **[tools/README_ESTRUTURA.md](../README_ESTRUTURA.md)** - Estrutura completa
- **[CONTINUAR_2026-02-06.md](../../CONTINUAR_2026-02-06.md)** - Próximos passos

---

**Movido em:** 2026-02-05 15:00
**Branch:** stealth
