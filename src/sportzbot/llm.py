"""Client for a llama.cpp server (llama-server) or Ollama, through the OpenAI style chat endpoint.

The benchmark runs every model through llama.cpp so all systems share one runtime. Prompts go in as
a single user message, which is how version 1 sent them through Ollama's generate endpoint.
"""

from __future__ import annotations

import time

import requests


class LlamaServer:
    def __init__(self, url: str = "http://127.0.0.1:8080", timeout: float = 600, model: str = "local"):
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.model = model  # ignored by llama-server; Ollama's OpenAI endpoint needs it (e.g. llama3.2)

    def wait(self, seconds: float = 600) -> None:
        end = time.time() + seconds
        while time.time() < end:
            try:
                if requests.get(self.url + "/health", timeout=5).status_code == 200:
                    return
            except requests.RequestException:
                pass
            time.sleep(2)
        raise TimeoutError("llama-server did not become healthy")

    def chat(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256, seed: int = 42) -> dict:
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "seed": seed,
            "cache_prompt": True,
        }
        t0 = time.time()
        r = requests.post(self.url + "/v1/chat/completions", json=body, timeout=self.timeout)
        r.raise_for_status()
        j = r.json()
        usage = j.get("usage", {})
        return {
            "text": j["choices"][0]["message"]["content"].strip(),
            "seconds": round(time.time() - t0, 2),
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
        }
