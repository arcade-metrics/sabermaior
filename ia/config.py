"""Configuração por perfil. IA_PERFIL (dev ou prod) escolhe o arquivo
.env.<perfil> na raiz do projeto (ou em IA_ENV_DIR); variáveis já definidas
no ambiente têm prioridade sobre o arquivo. Trocar de dev para produção é
só trocar o perfil ou as variáveis: o código não muda."""

import os
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _ler_env(caminho):
    valores = {}
    if not caminho.exists():
        return valores
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        valores[chave.strip()] = valor.strip().strip('"').strip("'")
    return valores


@dataclass(frozen=True)
class Config:
    perfil: str
    llm_base_url: str
    llm_model: str
    llm_api_key: str
    embed_base_url: str
    embed_model: str
    embed_api_key: str
    embed_dim: int
    rerank_provider: str  # none | local | tei
    rerank_model: str
    rerank_base_url: str
    database_url: str
    timeout: float

    def __repr__(self):
        ocultar = {"llm_api_key", "embed_api_key"}
        campos = ", ".join(f"{k}={'***' if k in ocultar and v else v!r}" for k, v in vars(self).items())
        return f"Config({campos})"


def carregar(perfil=None):
    perfil = perfil or os.environ.get("IA_PERFIL", "dev")
    pasta = Path(os.environ.get("IA_ENV_DIR", RAIZ))
    arquivo = _ler_env(pasta / f".env.{perfil}")
    v = lambda chave, padrao="": os.environ.get(chave, arquivo.get(chave, padrao))
    llm_base = v("LLM_BASE_URL", "http://127.0.0.1:11434/v1")
    llm_key = v("LLM_API_KEY")
    return Config(
        perfil=perfil,
        llm_base_url=llm_base.rstrip("/"),
        llm_model=v("LLM_MODEL", "qwen3:14b"),
        llm_api_key=llm_key,
        embed_base_url=v("EMBED_BASE_URL", llm_base).rstrip("/"),
        embed_model=v("EMBED_MODEL", "bge-m3"),
        embed_api_key=v("EMBED_API_KEY", llm_key),
        embed_dim=int(v("EMBED_DIM", "1024")),
        rerank_provider=v("RERANK_PROVIDER", "none"),
        rerank_model=v("RERANK_MODEL", "BAAI/bge-reranker-v2-m3"),
        rerank_base_url=v("RERANK_BASE_URL").rstrip("/"),
        database_url=v("DATABASE_URL", "postgresql://sabermaior:sabermaior@127.0.0.1:5434/sabermaior"),
        timeout=float(v("IA_TIMEOUT", "300")),
    )
