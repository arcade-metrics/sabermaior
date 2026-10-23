"""Clientes de chat, embeddings e reranking sobre a API compatível com
OpenAI (Ollama, vLLM, llama.cpp, TEI ou serviço hospedado)."""

import json
import re
import time

import requests

from .config import carregar

_PENSAMENTO = re.compile(r"<think>.*?</think>\s*", re.S)
# Esperas entre tentativas. Falhas transitórias: conexão, 429, 5xx e o
# esgotamento de portas do Windows dentro do Ollama ("buffer space"), que
# some quando os sockets em TIME_WAIT expiram (~2 min).
ESPERAS = (5, 15, 30, 60, 90)


class ErroIA(Exception):
    pass


def _transitorio(r):
    return r.status_code == 429 or r.status_code >= 500 or "buffer space" in r.text


def _post(sessao, url, chave, corpo, timeout):
    cabecalhos = {"Authorization": f"Bearer {chave}"} if chave else {}
    for espera in (*ESPERAS, None):
        try:
            r = sessao.post(url, json=corpo, headers=cabecalhos, timeout=timeout)
        except requests.ConnectionError as e:
            if espera is None:
                raise ErroIA(f"{url}: {e}") from e
        except requests.Timeout as e:
            raise ErroIA(f"{url}: {e}") from e
        else:
            if r.status_code < 400:
                return r.json()
            if espera is None or not _transitorio(r):
                raise ErroIA(f"{url}: HTTP {r.status_code} {r.text[:500]}")
        time.sleep(espera)


class IA:
    def __init__(self, config=None):
        self.config = config or carregar()
        self._reranker = None
        self._sessao = requests.Session()  # reaproveita a conexão

    def chat(self, mensagens, modelo=None, temperatura=0.2, max_tokens=None, esquema=None, raciocinio=None):
        """Devolve o texto da resposta; com `esquema` (JSON Schema), devolve o
        objeto já decodificado. `raciocinio` ("none", "low", "high") vai como
        reasoning_effort; "none" desliga o modo de pensar (qwen3 no Ollama)."""
        c = self.config
        corpo = {"model": modelo or c.llm_model, "messages": mensagens, "temperature": temperatura}
        if max_tokens:
            corpo["max_tokens"] = max_tokens
        if raciocinio:
            corpo["reasoning_effort"] = raciocinio
        if esquema:
            corpo["response_format"] = {"type": "json_schema",
                                        "json_schema": {"name": "resposta", "schema": esquema, "strict": True}}
        dados = _post(self._sessao, f"{c.llm_base_url}/chat/completions", c.llm_api_key, corpo, c.timeout)
        texto = _PENSAMENTO.sub("", dados["choices"][0]["message"].get("content") or "").strip()
        if not esquema:
            return texto
        try:
            return json.loads(texto)
        except json.JSONDecodeError as e:
            raise ErroIA(f"resposta não é JSON válido: {texto[:300]}") from e

    def embed(self, textos):
        c = self.config
        dados = _post(self._sessao, f"{c.embed_base_url}/embeddings", c.embed_api_key,
                      {"model": c.embed_model, "input": list(textos)}, c.timeout)
        vetores = [d["embedding"] for d in sorted(dados["data"], key=lambda d: d["index"])]
        if vetores and len(vetores[0]) != c.embed_dim:
            raise ErroIA(f"{c.embed_model} devolveu {len(vetores[0])} dimensões; EMBED_DIM={c.embed_dim}")
        return vetores

    def rerank(self, consulta, textos):
        """Notas de relevância na ordem de `textos` (maior = mais relevante),
        ou None se não houver reranker configurado."""
        c = self.config
        if c.rerank_provider == "none" or not textos:
            return None
        if c.rerank_provider == "tei":
            dados = _post(self._sessao, f"{c.rerank_base_url}/rerank", None,
                          {"query": consulta, "texts": list(textos), "truncate": True}, c.timeout)
            notas = [0.0] * len(textos)
            for d in dados:
                notas[d["index"]] = d["score"]
            return notas
        if c.rerank_provider == "local":
            if self._reranker is None:
                try:
                    from sentence_transformers import CrossEncoder
                except ImportError as e:
                    raise ErroIA("RERANK_PROVIDER=local requer: pip install -e .[rerank]") from e
                # fp16 (~1,2 GB) para caber na GPU junto da LLM e do bge-m3
                self._reranker = CrossEncoder(c.rerank_model, max_length=1024,
                                              model_kwargs={"torch_dtype": "float16"})
            return [float(x) for x in self._reranker.predict([(consulta, t) for t in textos])]
        raise ErroIA(f"RERANK_PROVIDER desconhecido: {c.rerank_provider}")
