#!/usr/bin/env python3
"""
Human Behavior Simulator
=========================
Simula comportamento humano para evitar detecção
"""

import asyncio
import random
import time
from typing import Optional


async def human_scroll(page, duration: float = None):
    """
    Simula scroll humano realista

    Args:
        page: Página do Playwright
        duration: Duração total do scroll (padrão: aleatório)
    """
    if duration is None:
        duration = random.uniform(2, 5)

    steps = random.randint(3, 7)
    step_duration = duration / steps

    for i in range(steps):
        # Scroll amount variável
        scroll_amount = random.randint(200, 600)

        # Às vezes scroll pra cima (humanos fazem isso)
        if random.random() < 0.15:
            scroll_amount = -random.randint(100, 300)

        await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        await asyncio.sleep(step_duration + random.uniform(-0.2, 0.3))


async def human_mouse_move(page, num_moves: int = None):
    """
    Simula movimentos de mouse naturais

    Args:
        page: Página do Playwright
        num_moves: Número de movimentos (padrão: aleatório)
    """
    if num_moves is None:
        num_moves = random.randint(2, 5)

    for _ in range(num_moves):
        x = random.randint(100, 1200)
        y = random.randint(100, 800)

        try:
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.5))
        except:
            pass  # Ignora erros de mouse fora da tela


async def random_pause(probability: float = 0.1):
    """
    Pausa aleatória ocasional (humanos não são constantes)

    Args:
        probability: Probabilidade de pausar (0.0 a 1.0)
    """
    if random.random() < probability:
        pause = random.uniform(15, 45)
        print(f"☕ Pausa humana: {pause:.1f}s")
        await asyncio.sleep(pause)


def human_read_time(content_length: int) -> float:
    """
    Calcula tempo realista de leitura

    Args:
        content_length: Tamanho do conteúdo em caracteres

    Returns:
        float: Tempo de leitura em segundos
    """
    # ~200 palavras/minuto = ~1000 chars/minuto
    base_time = content_length / 1000 * 60

    # Adiciona variação humana
    variation = random.uniform(0.7, 1.3)
    return base_time * variation


async def simulate_reading(page, min_time: float = 3, max_time: float = 8):
    """
    Simula humano lendo a página

    Args:
        page: Página do Playwright
        min_time: Tempo mínimo de leitura
        max_time: Tempo máximo de leitura
    """
    read_time = random.uniform(min_time, max_time)

    # Durante a leitura, faz scrolls ocasionais
    num_scrolls = random.randint(2, 4)
    scroll_interval = read_time / num_scrolls

    for i in range(num_scrolls):
        await asyncio.sleep(scroll_interval * random.uniform(0.8, 1.2))

        # Scroll pequeno
        scroll_amount = random.randint(100, 400)
        try:
            await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        except:
            pass


def human_click_delay() -> float:
    """
    Retorna delay realista antes de clicar

    Returns:
        float: Delay em segundos
    """
    return random.uniform(0.5, 2.0)


def human_typing_speed() -> float:
    """
    Retorna velocidade de digitação humana

    Returns:
        float: Delay entre teclas em segundos
    """
    return random.uniform(0.08, 0.25)


async def wait_for_page_load(page, min_wait: float = 2, max_wait: float = 5):
    """
    Aguarda carregamento da página com tempo humano

    Args:
        page: Página do Playwright
        min_wait: Tempo mínimo de espera
        max_wait: Tempo máximo de espera
    """
    wait_time = random.uniform(min_wait, max_wait)
    await asyncio.sleep(wait_time)


async def simulate_human_session(page, url: str):
    """
    Simula sessão humana completa ao visitar uma página

    Args:
        page: Página do Playwright
        url: URL a visitar
    """
    print(f"🤖 Simulando comportamento humano em {url[:50]}...")

    # 1. Aguardar carregamento inicial
    await wait_for_page_load(page, 2, 5)

    # 2. Movimento de mouse inicial
    await human_mouse_move(page, num_moves=2)

    # 3. Scroll explorativo
    await human_scroll(page, duration=3)

    # 4. "Leitura" do conteúdo
    await simulate_reading(page, min_time=4, max_time=8)

    # 5. Mais alguns movimentos de mouse
    await human_mouse_move(page, num_moves=3)

    # 6. Pausa ocasional
    await random_pause(probability=0.15)

    print(f"✅ Simulação humana completa")


if __name__ == "__main__":
    print("Human Behavior Simulator - Configurações:")
    print(f"  Tempo de leitura (500 chars): {human_read_time(500):.1f}s")
    print(f"  Delay de click: {human_click_delay():.2f}s")
    print(f"  Velocidade digitação: {human_typing_speed():.3f}s/tecla")
