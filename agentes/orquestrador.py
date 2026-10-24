"""Orquestração: escolhe o agente (Histórico ou Doutrinário) por heurística
de palavras-chave na pergunta — determinístico, sem gastar uma chamada de
LLM só para rotear —, gera a resposta reaproveitando rag.responder, e manda
o Agente de Citação auditar as citações literais antes de devolver."""

import re

from rag.responder import responder as _responder

from . import citacao, personas

_PISTAS_HISTORICO = re.compile(
    r"\b(quando|em que (ano|s[eé]culo)|hist[óo]ria|hist[óo]rico|surgiu|nasceu|morreu|faleceu|"
    r"origem|biografia|funda(d|ç)|hydesville|irm[ãa]s fox)\b",
    re.IGNORECASE,
)


def escolher_agente(pergunta):
    if _PISTAS_HISTORICO.search(pergunta):
        return "historico", personas.HISTORICO
    return "doutrinario", personas.DOUTRINARIO


def responder(conn, ia, pergunta, k=8, pensar=False, **filtros):
    agente, sistema = escolher_agente(pergunta)
    r = _responder(conn, ia, pergunta, k=k, pensar=pensar, sistema=sistema, **filtros)
    r["agente"] = agente
    r["citacoes_nao_confirmadas"] = citacao.verificar(r["resposta"], r["trechos"], r["citados"])
    return r
