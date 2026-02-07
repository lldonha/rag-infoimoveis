# Plano Anti-Bloqueio de IP - InfoImóveis Scraping

## Status: Crítico para Produção

---

## 🎯 Objetivo

Coletar dados do infoimoveis.com.br sem ser bloqueado por:
- Cloudflare anti-bot
- Rate limiting do servidor
- Detecção de comportamento automatizado
- Bloqueio de IP por volume

---

## 🔴 Riscos Identificados

| Risco | Severidade | Mitigação |
|-------|-----------|-----------|
| Cloudflare block (403) | ALTA | Browser real (Playwright headed) |
| Rate limiting | ALTA | Delays aleatórios + janelas de tempo |
| Fingerprint tracking | MÉDIA | Rotação de User-Agent + viewport |
| IP ban | MÉDIA | Rate limiting + comportamento humano |
| Captcha challenge | MÉDIA | Cookies persistentes + delays |

---

## ✅ Estratégia em Camadas

### **Camada 1: Bypass Cloudflare (OBRIGATÓRIO)**

```python
# tools/scraper_cloudflare.py

from playwright.sync_api import sync_playwright
import time
import random

def bypass_cloudflare(url, wait_time=20):
    """
    Bypass Cloudflare usando browser real
    """
    with sync_playwright() as p:
        # CRÍTICO: headed mode (headless=False)
        browser = p.chromium.launch(
            headless=False,  # Browser visível
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        # Remover flag webdriver
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = context.new_page()

        # Acessar página
        page.goto(url)

        # Aguardar Cloudflare processar (CRÍTICO)
        time.sleep(wait_time)

        # Salvar cookies para reutilizar
        cookies = context.cookies()

        content = page.content()

        browser.close()

        return content, cookies
```

**Justificativa:**
- `headless=False`: Cloudflare detecta headless browsers
- 20 segundos: Tempo para Cloudflare validar
- Cookies salvos: Reutilizar sessão autenticada

---

### **Camada 2: Rate Limiting Agressivo**

```python
# tools/rate_limiter.py

import time
import random
from datetime import datetime, timedelta

class SmartRateLimiter:
    def __init__(self):
        self.requests_this_hour = 0
        self.requests_today = 0
        self.hour_reset = datetime.now() + timedelta(hours=1)
        self.day_reset = datetime.now() + timedelta(days=1)

        # LIMITES CONSERVADORES
        self.MAX_PER_HOUR = 50      # 50 requests/hora (não 60)
        self.MAX_PER_DAY = 400       # 400 requests/dia (não 500)

    def wait_if_needed(self):
        """Aguardar se atingiu limites"""
        now = datetime.now()

        # Reset contadores
        if now >= self.hour_reset:
            self.requests_this_hour = 0
            self.hour_reset = now + timedelta(hours=1)

        if now >= self.day_reset:
            self.requests_today = 0
            self.day_reset = now + timedelta(days=1)

        # Verificar limites
        if self.requests_this_hour >= self.MAX_PER_HOUR:
            wait_seconds = (self.hour_reset - now).total_seconds()
            print(f"⏳ Limite horário atingido. Aguardando {wait_seconds/60:.1f} minutos...")
            time.sleep(wait_seconds)

        if self.requests_today >= self.MAX_PER_DAY:
            wait_seconds = (self.day_reset - now).total_seconds()
            print(f"⏳ Limite diário atingido. Aguardando {wait_seconds/3600:.1f} horas...")
            time.sleep(wait_seconds)

        # Delay aleatório entre requests (CRÍTICO)
        delay = random.uniform(5, 12)  # 5-12 segundos (não 3-8)
        print(f"⏱️  Aguardando {delay:.1f}s...")
        time.sleep(delay)

        # Incrementar contadores
        self.requests_this_hour += 1
        self.requests_today += 1
```

**Justificativa:**
- 5-12 segundos entre requests: Simular humano lendo página
- 50/hora e 400/dia: Margens de segurança
- Delays maiores que o mínimo recomendado

---

### **Camada 3: Janelas de Tempo (Horários de Baixo Tráfego)**

```python
# tools/scheduler.py

from datetime import datetime
import time

# Horários em que o site tem MENOS tráfego
SAFE_WINDOWS = [
    (3, 6),    # 03:00 - 06:00 (madrugada)
    (13, 15),  # 13:00 - 15:00 (almoço)
    (22, 24)   # 22:00 - 00:00 (noite)
]

def is_safe_window():
    """Verificar se estamos em janela segura"""
    now = datetime.now()
    current_hour = now.hour

    for start, end in SAFE_WINDOWS:
        if start <= current_hour < end:
            return True
    return False

def wait_for_safe_window():
    """Aguardar até próxima janela segura"""
    while not is_safe_window():
        print(f"⏳ Fora da janela segura. Aguardando...")
        time.sleep(300)  # Verificar a cada 5 minutos
```

**Uso no scraper:**
```python
# No início do scraping
wait_for_safe_window()

# Durante o scraping
if not is_safe_window():
    print("⚠️  Saiu da janela segura. Pausando...")
    wait_for_safe_window()
```

---

### **Camada 4: Rotação de Identidade (Fingerprint)**

```python
# tools/fingerprint_rotator.py

import random

USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",

    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",

    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
]

VIEWPORTS = [
    {'width': 1920, 'height': 1080},  # Full HD
    {'width': 1366, 'height': 768},   # Laptop comum
    {'width': 1536, 'height': 864},   # Laptop HD+
    {'width': 2560, 'height': 1440},  # 2K
]

TIMEZONES = [
    'America/Sao_Paulo',
    'America/Campo_Grande',
    'America/Cuiaba',
]

def get_random_fingerprint():
    """Gerar fingerprint aleatório"""
    return {
        'user_agent': random.choice(USER_AGENTS),
        'viewport': random.choice(VIEWPORTS),
        'timezone': random.choice(TIMEZONES),
        'locale': 'pt-BR',
    }
```

**Aplicar no browser:**
```python
fingerprint = get_random_fingerprint()

context = browser.new_context(
    user_agent=fingerprint['user_agent'],
    viewport=fingerprint['viewport'],
    locale=fingerprint['locale'],
    timezone_id=fingerprint['timezone']
)
```

---

### **Camada 5: Gestão de Cookies (Persistência de Sessão)**

```python
# tools/cookie_manager.py

import json
import os
from datetime import datetime, timedelta

COOKIE_FILE = '.tmp/cookies.json'
COOKIE_EXPIRY_HOURS = 6  # Renovar a cada 6 horas

def save_cookies(cookies):
    """Salvar cookies após bypass Cloudflare"""
    data = {
        'cookies': cookies,
        'timestamp': datetime.now().isoformat()
    }
    os.makedirs('.tmp', exist_ok=True)
    with open(COOKIE_FILE, 'w') as f:
        json.dump(data, f)

def load_cookies():
    """Carregar cookies salvos"""
    if not os.path.exists(COOKIE_FILE):
        return None

    with open(COOKIE_FILE, 'r') as f:
        data = json.load(f)

    # Verificar se expirou
    timestamp = datetime.fromisoformat(data['timestamp'])
    if datetime.now() - timestamp > timedelta(hours=COOKIE_EXPIRY_HOURS):
        print("🔄 Cookies expirados. Renovando...")
        return None

    return data['cookies']

def apply_cookies(context, cookies):
    """Aplicar cookies no contexto do browser"""
    if cookies:
        context.add_cookies(cookies)
        return True
    return False
```

**Uso:**
```python
# Tentar carregar cookies existentes
cookies = load_cookies()

if cookies:
    apply_cookies(context, cookies)
    print("✅ Usando cookies salvos")
else:
    # Fazer bypass Cloudflare e salvar novos cookies
    page.goto(url)
    time.sleep(20)  # Aguardar Cloudflare
    new_cookies = context.cookies()
    save_cookies(new_cookies)
    print("✅ Novos cookies salvos")
```

---

### **Camada 6: Comportamento Humano Simulado**

```python
# tools/human_behavior.py

import random
import time

def human_scroll(page):
    """Simular scroll humano"""
    scroll_steps = random.randint(3, 7)

    for _ in range(scroll_steps):
        scroll_amount = random.randint(200, 600)
        page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        time.sleep(random.uniform(0.5, 2.0))

def human_mouse_move(page):
    """Simular movimento de mouse"""
    x = random.randint(100, 800)
    y = random.randint(100, 600)
    page.mouse.move(x, y)
    time.sleep(random.uniform(0.1, 0.5))

def random_pause():
    """Pausas aleatórias (humanos não são constantes)"""
    if random.random() < 0.1:  # 10% de chance
        pause = random.uniform(15, 45)  # 15-45 segundos
        print(f"☕ Pausa aleatória de {pause:.1f}s...")
        time.sleep(pause)
```

**Uso no scraper:**
```python
# Ao acessar página
page.goto(url)
time.sleep(random.uniform(2, 5))  # Aguardar carregamento

# Simular leitura
human_scroll(page)
human_mouse_move(page)

# Pausa ocasional
random_pause()

# Extrair dados...
```

---

### **Camada 7: Monitoramento de Bloqueio**

```python
# tools/block_detector.py

def is_blocked(page_content):
    """Detectar se fomos bloqueados"""
    blocked_indicators = [
        'Access Denied',
        'Attention Required',
        'Cloudflare',
        'Just a moment',
        'Please verify you are a human',
        'Ray ID:',
        '<title>403',
    ]

    for indicator in blocked_indicators:
        if indicator.lower() in page_content.lower():
            return True
    return False

def handle_block():
    """Ação ao detectar bloqueio"""
    print("🚨 BLOQUEIO DETECTADO!")
    print("Ações:")
    print("1. Pausar scraping por 1 hora")
    print("2. Renovar cookies")
    print("3. Trocar fingerprint")
    print("4. Aguardar janela segura")

    time.sleep(3600)  # 1 hora de pausa

    # Forçar renovação de cookies
    if os.path.exists(COOKIE_FILE):
        os.remove(COOKIE_FILE)
```

**Uso:**
```python
content = page.content()

if is_blocked(content):
    handle_block()
    continue  # Tentar novamente
```

---

## 📊 Pipeline Completo Recomendado

```python
# tools/scraper_production.py

def scrape_property_safe(url):
    """Scraper com todas as proteções"""

    # 1. Verificar janela de tempo
    wait_for_safe_window()

    # 2. Rate limiting
    rate_limiter.wait_if_needed()

    # 3. Fingerprint aleatório
    fingerprint = get_random_fingerprint()

    # 4. Browser com fingerprint
    browser = p.chromium.launch(headless=False, args=[...])
    context = browser.new_context(
        user_agent=fingerprint['user_agent'],
        viewport=fingerprint['viewport'],
        timezone_id=fingerprint['timezone']
    )

    # 5. Aplicar cookies salvos
    cookies = load_cookies()
    if cookies:
        apply_cookies(context, cookies)

    # 6. Acessar página
    page = context.new_page()
    page.goto(url)

    # 7. Comportamento humano
    time.sleep(random.uniform(3, 8))
    human_scroll(page)
    human_mouse_move(page)

    # 8. Verificar bloqueio
    content = page.content()
    if is_blocked(content):
        handle_block()
        return None

    # 9. Extrair dados
    data = parse_property(content)

    # 10. Pausa ocasional
    random_pause()

    # 11. Salvar cookies (se renovados)
    if not cookies:
        save_cookies(context.cookies())

    browser.close()

    return data
```

---

## 🎯 Checklist de Segurança

Antes de rodar scraping em produção:

```
[ ] Browser headed mode (headless=False)
[ ] Delay 5-12 segundos entre requests
[ ] Limite 50 requests/hora e 400/dia
[ ] Scraping apenas em janelas seguras (madrugada, almoço, noite)
[ ] Rotação de User-Agent
[ ] Rotação de viewport
[ ] Cookies persistentes (renovar a cada 6h)
[ ] Comportamento humano (scroll, mouse, pausas)
[ ] Detecção de bloqueio implementada
[ ] Logs de cada request (timestamp, URL, status)
[ ] Plano B se bloquear (pausa de 1h+ e retry)
```

---

## 🔥 Se Mesmo Assim Bloquear

### Opção 1: Proxy Residencial (Pago)
- **Bright Data**: https://brightdata.com/ (desde $8.40/GB)
- **Oxylabs**: https://oxylabs.io/ (desde $15/GB)
- **Smartproxy**: https://smartproxy.com/ (desde $12.5/GB)

```python
# Com proxy residencial
browser.new_context(
    proxy={
        "server": "http://proxy.provider.com:8000",
        "username": "user",
        "password": "pass"
    }
)
```

### Opção 2: VPN Rotativa
- Mudar IP a cada X requests
- NordVPN, ExpressVPN, etc.

### Opção 3: Distribuir Scraping
- Rodar de máquinas diferentes
- Casa, trabalho, cloud (AWS/GCP free tier)

### Opção 4: Reduzir Volume
- Scraping seletivo (apenas imóveis novos)
- Update incremental (apenas mudanças de preço)

---

## 📈 Métricas de Monitoramento

```python
# Criar log de métricas
metrics = {
    'total_requests': 0,
    'successful_requests': 0,
    'blocked_requests': 0,
    'error_requests': 0,
    'average_delay': 0,
    'last_block_timestamp': None,
}

# Salvar a cada request
with open('metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)
```

**Alertas:**
- Taxa de bloqueio > 5% → Aumentar delays
- Taxa de bloqueio > 20% → Parar imediatamente
- Erro HTTP 429 → Rate limit excedido

---

## 🚦 Priorização de Coleta

**Alta prioridade (scraping frequente):**
- Imóveis novos (últimos 7 dias)
- Mudanças de preço
- Imóveis em bairros-alvo

**Baixa prioridade (scraping esporádico):**
- Imóveis antigos sem mudanças
- Imóveis fora do escopo (outras cidades)

---

## ✅ Resumo Executivo

| Camada | Implementação | Impacto |
|--------|---------------|---------|
| Browser real | headless=False | ⚠️ CRÍTICO |
| Delay 5-12s | random.uniform(5,12) | ⚠️ CRÍTICO |
| Limite 50/hora | Rate limiter | ⚠️ CRÍTICO |
| Janelas seguras | 3-6h, 13-15h, 22-24h | 🟡 ALTO |
| Cookies persistentes | Salvar/reutilizar | 🟡 ALTO |
| Fingerprint rotation | UA + viewport | 🟢 MÉDIO |
| Comportamento humano | Scroll + mouse | 🟢 MÉDIO |
| Detecção de bloqueio | is_blocked() | 🟡 ALTO |

**Próximo passo:** Implementar scraper_production.py com todas as camadas.
