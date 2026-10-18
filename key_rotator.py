import os, time, threading
from datetime import datetime, timedelta
from collections import deque
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

class KeyPool:
    def __init__(self, provider: str, keys: list, cooldown_seconds: int = 60):
        self.provider = provider
        self.cooldown_seconds = cooldown_seconds
        self.lock = threading.Lock()
        valid_keys = [k for k in keys if k and k.strip()]
        self.keys = deque([{"key": k, "available_at": datetime.now(), "hits": 0, "errors": 0} for k in valid_keys])
        if not self.keys:
            print(f"⚠️  [{provider}] No valid keys found!")

    def get_key(self) -> str | None:
        with self.lock:
            if not self.keys: return None
            now = datetime.now()
            for _ in range(len(self.keys)):
                entry = self.keys[0]
                if entry["available_at"] <= now:
                    self.keys.rotate(-1)
                    entry["hits"] += 1
                    return entry["key"]
                self.keys.rotate(-1)
            # If all keys are cooling down, return None immediately instead of sleeping
            return None 

    def report_rate_limit(self, key: str):
        with self.lock:
            for entry in self.keys:
                if entry["key"] == key:
                    entry["available_at"] = datetime.now() + timedelta(seconds=self.cooldown_seconds)
                    entry["errors"] += 1
                    break

    def report_error(self, key: str):
        with self.lock:
            for entry in self.keys:
                if entry["key"] == key:
                    entry["available_at"] = datetime.now() + timedelta(seconds=10)
                    entry["errors"] += 1
                    break

class RotatingKeyManager:
    TASK_PROVIDER_MAP = {"bulk_generate": "groq", "detail_generate": "groq", "validate": "gemini"}
    
    def __init__(self):
        self.pools = {
            "nvidia": KeyPool("NVIDIA", [os.getenv(f"NVIDIA_API_KEY_{i}") for i in range(1, 6)], 90),
            "gemini": KeyPool("GEMINI", [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 6)], 60),
            "groq": KeyPool("GROQ", [os.getenv(f"GROQ_API_KEY_{i}") for i in range(1, 6)], 30)
        }

    def get_key_for_task(self, task: str) -> tuple[str, str]:
        preferred = self.TASK_PROVIDER_MAP.get(task, "groq")
        order = [preferred] + [p for p in ["groq", "gemini", "nvidia"] if p != preferred]
        
        for provider in order:
            key = self.pools[provider].get_key()
            if key: 
                return provider, key
                
        # If ALL providers have cooling keys, ONLY THEN wait and retry
        print("⏳ All keys across all providers are cooling down. Waiting 10s...")
        time.sleep(10)
        return self.get_key_for_task(task)

    def report_rate_limit(self, provider: str, key: str): 
        self.pools[provider].report_rate_limit(key)
        
    def report_error(self, provider: str, key: str): 
        self.pools[provider].report_error(key)

key_manager = RotatingKeyManager()
