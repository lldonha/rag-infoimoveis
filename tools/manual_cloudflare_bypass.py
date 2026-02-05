#!/usr/bin/env python3
"""
Manual Cloudflare Bypass
=========================
Script para fazer bypass manual do Cloudflare e salvar cookies
"""

import asyncio
import sys
import os
from playwright.async_api import async_playwright

sys.path.append(os.path.dirname(__file__))
from cookie_manager import save_cookies
from fingerprint_rotator import get_random_fingerprint

BASE_URL = "https://www.infoimoveis.com.br"


async def manual_bypass():
    """
    Abre browser, aguarda usuário resolver Cloudflare, salva cookies
    """
    print("=" * 60)
    print("MANUAL CLOUDFLARE BYPASS")
    print("=" * 60)
    print()
    print("📋 INSTRUÇÕES:")
    print("1. Browser abrirá em 3 segundos")
    print("2. Resolva o desafio Cloudflare (checkbox ou captcha)")
    print("3. Script aguardará 60 segundos para você resolver")
    print("4. Cookies serão salvos automaticamente")
    print()
    print("=" * 60)
    await asyncio.sleep(3)
    print()

    fingerprint = get_random_fingerprint()

    async with async_playwright() as p:
        # Browser visível para interação manual
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )

        # Context com fingerprint
        context = await browser.new_context(
            user_agent=fingerprint['user_agent'],
            viewport=fingerprint['viewport'],
            locale=fingerprint['locale'],
            timezone_id=fingerprint['timezone']
        )

        # Anti-detection
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = await context.new_page()

        print(f"🌐 Abrindo {BASE_URL}...")
        await page.goto(BASE_URL, wait_until='domcontentloaded', timeout=60000)

        print()
        print("⏳ Aguardando 60 segundos para você resolver o Cloudflare...")
        print("👉 Resolva o desafio e aguarde a página carregar")
        print()

        # Aguardar 60 segundos para usuário resolver
        for i in range(60, 0, -10):
            print(f"   {i} segundos restantes...")
            await asyncio.sleep(10)

        # Salvar cookies
        print("\n💾 Salvando cookies...")
        cookies = await context.cookies()

        if cookies:
            save_cookies(cookies, metadata={
                'fingerprint': fingerprint,
                'bypass_method': 'manual'
            })
            print(f"✅ {len(cookies)} cookies salvos com sucesso!")
            print()
            print("🎯 Próximo passo:")
            print("   python tools/scraper_production.py")
        else:
            print("❌ Nenhum cookie encontrado")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(manual_bypass())
