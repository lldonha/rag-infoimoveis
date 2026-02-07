"""
Simulador de Comportamento Humano
Scroll, movimento de mouse, pausas aleatórias para parecer humano
"""

import random
import time


def human_scroll(page, min_steps=3, max_steps=7):
    """
    Simula scroll humano pela página

    Args:
        page: Página do Playwright
        min_steps: Mínimo de scrolls
        max_steps: Máximo de scrolls
    """
    scroll_steps = random.randint(min_steps, max_steps)

    print(f"🖱️  Simulando {scroll_steps} scrolls...")

    for i in range(scroll_steps):
        # Quantidade aleatória de scroll (200-600px)
        scroll_amount = random.randint(200, 600)

        # Scroll para baixo
        page.evaluate(f"window.scrollBy(0, {scroll_amount})")

        # Pausa entre scrolls (0.5-2.0s - humanos não scrollam instantaneamente)
        pause = random.uniform(0.5, 2.0)
        time.sleep(pause)

    # Ocasionalmente scroll de volta para cima (10% de chance)
    if random.random() < 0.1:
        scroll_back = random.randint(300, 800)
        page.evaluate(f"window.scrollBy(0, -{scroll_back})")
        time.sleep(random.uniform(0.5, 1.5))


def human_mouse_move(page, num_moves=None):
    """
    Simula movimento aleatório de mouse

    Args:
        page: Página do Playwright
        num_moves: Número de movimentos (None = aleatório 2-5)
    """
    if num_moves is None:
        num_moves = random.randint(2, 5)

    print(f"🖱️  Simulando {num_moves} movimentos de mouse...")

    for i in range(num_moves):
        # Posição aleatória dentro da viewport
        x = random.randint(100, 1200)
        y = random.randint(100, 800)

        page.mouse.move(x, y)

        # Pausa curta entre movimentos
        time.sleep(random.uniform(0.1, 0.5))


def random_pause(probability=0.15, min_seconds=10, max_seconds=30):
    """
    Pausa aleatória ocasional (simula humano distraído)

    Args:
        probability: Chance de pausa ocorrer (0.0-1.0)
        min_seconds: Tempo mínimo de pausa
        max_seconds: Tempo máximo de pausa

    Returns:
        bool: True se pausou
    """
    if random.random() < probability:
        pause = random.uniform(min_seconds, max_seconds)
        print(f"☕ Pausa aleatória de {pause:.1f}s (simulando distração humana)...")
        time.sleep(pause)
        return True

    return False


def wait_for_page_load(page, min_wait=2.0, max_wait=5.0):
    """
    Aguarda página carregar + tempo humano de leitura

    Args:
        page: Página do Playwright
        min_wait: Tempo mínimo de espera (segundos)
        max_wait: Tempo máximo de espera (segundos)
    """
    # Aguardar carregamento básico
    try:
        page.wait_for_load_state('domcontentloaded', timeout=10000)
    except:
        pass  # Ignorar se der timeout

    # Tempo adicional de "leitura"
    read_time = random.uniform(min_wait, max_wait)
    print(f"📖 Aguardando {read_time:.1f}s (simulando leitura)...")
    time.sleep(read_time)


def simulate_reading_page(page):
    """
    Simula comportamento completo de leitura de página

    Sequência:
    1. Aguardar carregamento
    2. Scroll inicial
    3. Movimento de mouse
    4. Pausa ocasional
    5. Scroll adicional

    Args:
        page: Página do Playwright
    """
    print("👤 Simulando comportamento humano completo...")

    # 1. Aguardar carregamento + leitura inicial
    wait_for_page_load(page, min_wait=2, max_wait=4)

    # 2. Primeiro scroll (ler topo da página)
    human_scroll(page, min_steps=2, max_steps=4)

    # 3. Movimento de mouse enquanto lê
    human_mouse_move(page, num_moves=random.randint(2, 4))

    # 4. Pausa ocasional (15% de chance)
    random_pause(probability=0.15, min_seconds=5, max_seconds=15)

    # 5. Scroll adicional (explorar mais a página)
    if random.random() < 0.7:  # 70% de chance
        human_scroll(page, min_steps=1, max_steps=3)

    print("✅ Simulação de comportamento concluída")


def click_with_hesitation(page, selector, delay=None):
    """
    Clica em elemento com hesitação humana

    Args:
        page: Página do Playwright
        selector: Seletor CSS do elemento
        delay: Delay antes do click (None = aleatório 0.5-2.0s)

    Returns:
        bool: True se clicou com sucesso
    """
    try:
        if delay is None:
            delay = random.uniform(0.5, 2.0)

        print(f"🖱️  Aguardando {delay:.1f}s antes de clicar (hesitação humana)...")
        time.sleep(delay)

        page.click(selector)
        print(f"✅ Click realizado em: {selector}")

        # Aguardar após click
        time.sleep(random.uniform(0.5, 1.5))

        return True

    except Exception as e:
        print(f"❌ Erro ao clicar: {e}")
        return False


def type_with_delays(page, selector, text, min_delay=0.05, max_delay=0.15):
    """
    Digita texto com delays entre caracteres (simula digitação humana)

    Args:
        page: Página do Playwright
        selector: Seletor CSS do input
        text: Texto a digitar
        min_delay: Delay mínimo entre caracteres (segundos)
        max_delay: Delay máximo entre caracteres (segundos)

    Returns:
        bool: True se digitou com sucesso
    """
    try:
        print(f"⌨️  Digitando texto com delays humanos...")

        # Clicar no campo primeiro
        page.click(selector)
        time.sleep(random.uniform(0.2, 0.5))

        # Digitar caractere por caractere
        for char in text:
            page.type(selector, char, delay=random.uniform(min_delay, max_delay) * 1000)  # Playwright usa ms

        print(f"✅ Texto digitado: {text[:20]}...")
        return True

    except Exception as e:
        print(f"❌ Erro ao digitar: {e}")
        return False


if __name__ == "__main__":
    # Teste das funções (sem Playwright real)
    print("="*60)
    print("🧪 TESTE - Human Behavior Simulator")
    print("="*60)

    print("\n1. Teste de Pausa Aleatória (10 tentativas):")
    print("-"*60)
    pauses = 0
    for i in range(10):
        if random_pause(probability=0.2, min_seconds=1, max_seconds=2):
            pauses += 1
        else:
            print(f"  {i+1}. Sem pausa")

    print(f"\nTotal de pausas: {pauses}/10 (esperado ~2)")

    print("\n2. Simulação de Scrolls (mock):")
    print("-"*60)
    print("  (Simulando scrolls sem browser real)")
    scroll_steps = random.randint(3, 7)
    print(f"  Geraria {scroll_steps} scrolls")
    for i in range(scroll_steps):
        scroll_amount = random.randint(200, 600)
        pause = random.uniform(0.5, 2.0)
        print(f"    {i+1}. Scroll {scroll_amount}px → aguarda {pause:.1f}s")

    print("\n3. Simulação de Movimentos de Mouse (mock):")
    print("-"*60)
    num_moves = random.randint(2, 5)
    print(f"  Geraria {num_moves} movimentos")
    for i in range(num_moves):
        x, y = random.randint(100, 1200), random.randint(100, 800)
        print(f"    {i+1}. Mouse para ({x}, {y})")

    print("\n✅ Teste concluído!")
    print("\nℹ️  Para teste completo com Playwright, use o scraper de produção")
