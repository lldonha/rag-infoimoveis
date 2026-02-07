#!/usr/bin/env python3
"""
Rate Limiter Inteligente
========================
Controle agressivo de taxa para evitar bloqueio
"""

import time
import random
from datetime import datetime, timedelta
from typing import Optional


class SmartRateLimiter:
    """Rate limiter com limites conservadores"""

    def __init__(
        self,
        max_per_hour: int = 50,
        max_per_day: int = 400,
        min_delay: float = 5.0,
        max_delay: float = 12.0
    ):
        self.MAX_PER_HOUR = max_per_hour
        self.MAX_PER_DAY = max_per_day
        self.MIN_DELAY = min_delay
        self.MAX_DELAY = max_delay

        self.requests_this_hour = 0
        self.requests_today = 0
        self.hour_reset = datetime.now() + timedelta(hours=1)
        self.day_reset = datetime.now() + timedelta(days=1)
        self.last_request_time: Optional[datetime] = None

    def wait_if_needed(self) -> float:
        """
        Aguarda se necessário e retorna tempo de espera

        Returns:
            float: Tempo aguardado em segundos
        """
        now = datetime.now()
        total_wait = 0.0

        # Reset contadores se necessário
        if now >= self.hour_reset:
            self.requests_this_hour = 0
            self.hour_reset = now + timedelta(hours=1)
            print(f"✅ Contador horário resetado")

        if now >= self.day_reset:
            self.requests_today = 0
            self.day_reset = now + timedelta(days=1)
            print(f"✅ Contador diário resetado")

        # Verificar limite horário
        if self.requests_this_hour >= self.MAX_PER_HOUR:
            wait_seconds = (self.hour_reset - now).total_seconds()
            print(f"⏳ Limite horário atingido ({self.requests_this_hour}/{self.MAX_PER_HOUR})")
            print(f"   Aguardando {wait_seconds/60:.1f} minutos...")
            time.sleep(wait_seconds)
            total_wait += wait_seconds
            now = datetime.now()

        # Verificar limite diário
        if self.requests_today >= self.MAX_PER_DAY:
            wait_seconds = (self.day_reset - now).total_seconds()
            print(f"⏳ Limite diário atingido ({self.requests_today}/{self.MAX_PER_DAY})")
            print(f"   Aguardando {wait_seconds/3600:.1f} horas...")
            time.sleep(wait_seconds)
            total_wait += wait_seconds
            now = datetime.now()

        # Delay aleatório entre requests
        delay = random.uniform(self.MIN_DELAY, self.MAX_DELAY)
        print(f"⏱️  Delay: {delay:.1f}s | Hora: {self.requests_this_hour}/{self.MAX_PER_HOUR} | Dia: {self.requests_today}/{self.MAX_PER_DAY}")
        time.sleep(delay)
        total_wait += delay

        # Atualizar contadores
        self.requests_this_hour += 1
        self.requests_today += 1
        self.last_request_time = datetime.now()

        return total_wait

    def get_stats(self) -> dict:
        """Retorna estatísticas do rate limiter"""
        return {
            'requests_this_hour': self.requests_this_hour,
            'requests_today': self.requests_today,
            'max_per_hour': self.MAX_PER_HOUR,
            'max_per_day': self.MAX_PER_DAY,
            'hour_reset_in': (self.hour_reset - datetime.now()).total_seconds(),
            'day_reset_in': (self.day_reset - datetime.now()).total_seconds(),
        }


# Janelas seguras de scraping
SAFE_WINDOWS = [
    (3, 6),    # 03:00 - 06:00 (madrugada)
    (13, 15),  # 13:00 - 15:00 (almoço)
    (22, 24)   # 22:00 - 00:00 (noite)
]


def is_safe_window() -> bool:
    """Verifica se está em horário de baixo tráfego"""
    current_hour = datetime.now().hour
    for start, end in SAFE_WINDOWS:
        if start <= current_hour < end:
            return True
    return False


def wait_for_safe_window():
    """Aguarda até próxima janela segura"""
    while not is_safe_window():
        current_hour = datetime.now().hour
        print(f"⏳ Fora da janela segura (hora atual: {current_hour:02d}h)")
        print(f"   Janelas seguras: {SAFE_WINDOWS}")
        time.sleep(300)  # Verificar a cada 5 minutos

    print(f"✅ Dentro da janela segura!")


if __name__ == "__main__":
    # Teste do rate limiter
    print("Testando Rate Limiter...")
    limiter = SmartRateLimiter(max_per_hour=5, max_per_day=10, min_delay=2, max_delay=4)

    for i in range(3):
        print(f"\nRequest {i+1}:")
        wait_time = limiter.wait_if_needed()
        print(f"Total wait: {wait_time:.1f}s")

    print("\nEstado final:")
    print(limiter.get_stats())
