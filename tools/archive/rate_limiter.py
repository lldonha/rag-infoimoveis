"""
Rate Limiter Inteligente para Scraping Seguro
Controla volume de requests para evitar bloqueio
"""

import time
import random
import json
import os
from datetime import datetime, timedelta
from pathlib import Path


class SmartRateLimiter:
    """
    Rate limiter com limites horários e diários

    Limites conservadores:
    - 50 requests/hora
    - 400 requests/dia
    - 5-12 segundos entre requests
    """

    def __init__(self, state_file='.tmp/rate_limiter_state.json'):
        self.state_file = Path(state_file)

        # LIMITES CONSERVADORES (não ultrapassar!)
        self.MAX_PER_HOUR = 50
        self.MAX_PER_DAY = 400
        self.MIN_DELAY = 5   # segundos
        self.MAX_DELAY = 12  # segundos

        # Carregar estado ou inicializar
        self._load_state()

    def _load_state(self):
        """Carrega estado persistente ou inicializa novo"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)

                self.requests_this_hour = data.get('requests_this_hour', 0)
                self.requests_today = data.get('requests_today', 0)
                self.hour_reset = datetime.fromisoformat(data.get('hour_reset'))
                self.day_reset = datetime.fromisoformat(data.get('day_reset'))
                self.last_request_time = datetime.fromisoformat(data['last_request_time']) if data.get('last_request_time') else None

            except Exception as e:
                print(f"⚠️  Erro ao carregar estado: {e}. Criando novo...")
                self._init_state()
        else:
            self._init_state()

    def _init_state(self):
        """Inicializa novo estado"""
        now = datetime.now()
        self.requests_this_hour = 0
        self.requests_today = 0
        self.hour_reset = now + timedelta(hours=1)
        self.day_reset = now + timedelta(days=1)
        self.last_request_time = None

    def _save_state(self):
        """Salva estado para persistência"""
        os.makedirs(self.state_file.parent, exist_ok=True)

        data = {
            'requests_this_hour': self.requests_this_hour,
            'requests_today': self.requests_today,
            'hour_reset': self.hour_reset.isoformat(),
            'day_reset': self.day_reset.isoformat(),
            'last_request_time': self.last_request_time.isoformat() if self.last_request_time else None,
            'last_updated': datetime.now().isoformat()
        }

        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _reset_counters_if_needed(self):
        """Reseta contadores se período expirou"""
        now = datetime.now()

        # Reset contador horário
        if now >= self.hour_reset:
            print(f"⏰ Nova hora! Reset contador horário (eram {self.requests_this_hour} requests)")
            self.requests_this_hour = 0
            self.hour_reset = now + timedelta(hours=1)

        # Reset contador diário
        if now >= self.day_reset:
            print(f"📅 Novo dia! Reset contador diário (eram {self.requests_today} requests)")
            self.requests_today = 0
            self.day_reset = now + timedelta(days=1)

    def wait_if_needed(self, verbose=True):
        """
        Aguarda se necessário antes de fazer request

        Verifica:
        1. Se atingiu limites (hora/dia)
        2. Aplica delay mínimo entre requests
        """
        self._reset_counters_if_needed()
        now = datetime.now()

        # Verificar limite horário
        if self.requests_this_hour >= self.MAX_PER_HOUR:
            wait_seconds = (self.hour_reset - now).total_seconds()
            wait_minutes = wait_seconds / 60

            if verbose:
                print(f"⏳ LIMITE HORÁRIO ATINGIDO ({self.MAX_PER_HOUR} requests)")
                print(f"   Aguardando {wait_minutes:.1f} minutos até {self.hour_reset.strftime('%H:%M:%S')}...")

            time.sleep(wait_seconds + 1)  # +1 segundo de margem
            self._reset_counters_if_needed()

        # Verificar limite diário
        if self.requests_today >= self.MAX_PER_DAY:
            wait_seconds = (self.day_reset - now).total_seconds()
            wait_hours = wait_seconds / 3600

            if verbose:
                print(f"⏳ LIMITE DIÁRIO ATINGIDO ({self.MAX_PER_DAY} requests)")
                print(f"   Aguardando {wait_hours:.1f} horas até {self.day_reset.strftime('%d/%m %H:%M')}...")

            time.sleep(wait_seconds + 1)
            self._reset_counters_if_needed()

        # Delay mínimo entre requests
        if self.last_request_time:
            time_since_last = (now - self.last_request_time).total_seconds()

            if time_since_last < self.MIN_DELAY:
                additional_wait = self.MIN_DELAY - time_since_last
                if verbose:
                    print(f"⏱️  Aguardando delay mínimo: {additional_wait:.1f}s...")
                time.sleep(additional_wait)

        # Delay aleatório (simula humano lendo página)
        delay = random.uniform(self.MIN_DELAY, self.MAX_DELAY)

        if verbose:
            print(f"⏱️  Delay: {delay:.1f}s (Horário: {self.requests_this_hour}/{self.MAX_PER_HOUR} | Diário: {self.requests_today}/{self.MAX_PER_DAY})")

        time.sleep(delay)

        # Atualizar contadores
        self.requests_this_hour += 1
        self.requests_today += 1
        self.last_request_time = datetime.now()

        self._save_state()

    def get_stats(self):
        """Retorna estatísticas atuais"""
        self._reset_counters_if_needed()

        return {
            'requests_this_hour': self.requests_this_hour,
            'requests_today': self.requests_today,
            'remaining_hour': self.MAX_PER_HOUR - self.requests_this_hour,
            'remaining_day': self.MAX_PER_DAY - self.requests_today,
            'hour_reset': self.hour_reset.strftime('%H:%M:%S'),
            'day_reset': self.day_reset.strftime('%d/%m %H:%M'),
            'percentage_hour': (self.requests_this_hour / self.MAX_PER_HOUR) * 100,
            'percentage_day': (self.requests_today / self.MAX_PER_DAY) * 100,
        }

    def print_stats(self):
        """Imprime estatísticas de forma legível"""
        stats = self.get_stats()

        print("\n" + "="*60)
        print("📊 RATE LIMITER - Estatísticas")
        print("="*60)
        print(f"⏰ Horário: {stats['requests_this_hour']}/{self.MAX_PER_HOUR} ({stats['percentage_hour']:.1f}%)")
        print(f"   Restam: {stats['remaining_hour']} requests até {stats['hour_reset']}")
        print(f"\n📅 Diário: {stats['requests_today']}/{self.MAX_PER_DAY} ({stats['percentage_day']:.1f}%)")
        print(f"   Restam: {stats['remaining_day']} requests até {stats['day_reset']}")
        print("="*60 + "\n")

    def reset(self):
        """Reset manual de todos os contadores (use com cuidado!)"""
        print("⚠️  RESET MANUAL - Todos os contadores zerados")
        self._init_state()
        self._save_state()


# Singleton global
_rate_limiter_instance = None

def get_rate_limiter():
    """Retorna instância singleton do rate limiter"""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = SmartRateLimiter()
    return _rate_limiter_instance


if __name__ == "__main__":
    # Teste do rate limiter
    print("="*60)
    print("🧪 TESTE - Rate Limiter")
    print("="*60)

    limiter = SmartRateLimiter()
    limiter.print_stats()

    print("\nSimulando 3 requests...\n")

    for i in range(3):
        print(f"\n--- Request {i+1}/3 ---")
        limiter.wait_if_needed()
        print(f"✅ Request {i+1} executado")

    print("\n")
    limiter.print_stats()
