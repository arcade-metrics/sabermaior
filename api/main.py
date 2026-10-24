"""API HTTP local para busca e perguntas no acervo, em pt-BR.

    uvicorn api.main:app --reload       # dev, com recarga automática (interface: cd web && npm run dev)
    espirita-api                        # produção local (sem --reload)
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agentes import responder as responder_agentes
from grafo import consulta as grafo_consulta
from ia import IA, carregar
from rag import db, obras
from rag.busca import buscar, referencia
from rag.responder import responder

IDIOMA = "pt"  # interface é só pt-BR; trava o filtro de idioma na busca
ESTATICOS = Path(__file__).resolve().parent / "estaticos"
CAPAS = Path(__file__).resolve().parent.parent / ".cache" / "capas"  # miniaturas geradas sob demanda

app = FastAPI(title="Saber Maior")


@lru_cache
def _ia():
    return IA(carregar())


class Pergunta(BaseModel):
    pergunta: str
    k: int = 8
    pensar: bool = False
    obra: Optional[str] = None


def _serializar(t):
    notas = {c: round(t[c], 3) for c in ("rrf", "similaridade", "rank_texto", "rerank") if t.get(c)}
    return {"id": t["id"], "referencia": referencia(t), "conteudo": t["conteudo"], "notas": notas}


def _fontes(r):
    """Trechos citados na resposta, com o texto para a interface mostrar ao clicar na citação."""
    return [{"numero": n, "id": t["id"], "referencia": referencia(t), "conteudo": t["conteudo"]}
            for n in r["citados"] for t in [r["trechos"][n - 1]]]


@app.get("/api/search")
def api_search(q: str, k: int = 8, modo: str = "auto", obra: Optional[str] = None):
    if not q.strip():
        raise HTTPException(400, "informe a busca")
    ia = _ia()
    with db.conectar(ia.config) as conn:
        trechos = buscar(conn, ia, q, k=k, modo=modo, obra=obra, idioma=IDIOMA)
    return [_serializar(t) for t in trechos]


@app.post("/api/ask")
def api_ask(entrada: Pergunta):
    if not entrada.pergunta.strip():
        raise HTTPException(400, "informe a pergunta")
    ia = _ia()
    with db.conectar(ia.config) as conn:
        r = responder(conn, ia, entrada.pergunta, k=entrada.k, pensar=entrada.pensar,
                      obra=entrada.obra, idioma=IDIOMA)
    return {
        "resposta": r["resposta"],
        "invalidas": r["invalidas"],
        "fontes": _fontes(r),
    }


@app.post("/api/ask-agentes")
def api_ask_agentes(entrada: Pergunta):
    if not entrada.pergunta.strip():
        raise HTTPException(400, "informe a pergunta")
    ia = _ia()
    with db.conectar(ia.config) as conn:
        r = responder_agentes(conn, ia, entrada.pergunta, k=entrada.k, pensar=entrada.pensar,
                              obra=entrada.obra, idioma=IDIOMA)
    return {
        "agente": r["agente"],
        "resposta": r["resposta"],
        "invalidas": r["invalidas"],
        "citacoes_nao_confirmadas": r["citacoes_nao_confirmadas"],
        "fontes": _fontes(r),
    }


@app.get("/api/obras")
def api_obras():
    ia = _ia()
    with db.conectar(ia.config) as conn:
        return obras.listar(conn, IDIOMA)


@app.get("/api/obras/{obra_id}")
def api_obra(obra_id: str):
    ia = _ia()
    with db.conectar(ia.config) as conn:
        o = obras.detalhe(conn, obra_id, IDIOMA)
    if not o:
        raise HTTPException(404, "obra não encontrada")
    return o


@app.get("/api/obras/{obra_id}/capa")
def api_obra_capa(obra_id: str):
    ia = _ia()
    with db.conectar(ia.config) as conn:
        arquivo = obras.capa(conn, obra_id, CAPAS)
    if not arquivo:
        raise HTTPException(404, "capa indisponível")
    return FileResponse(arquivo, media_type="image/png", headers={"Cache-Control": "public, max-age=604800"})


@app.get("/api/grafo")
def api_grafo_categorias():
    ia = _ia()
    with db.conectar(ia.config) as conn:
        return grafo_consulta.listar_categorias(conn)


@app.get("/api/grafo/{conceito}")
def api_grafo_conceito(conceito: str):
    ia = _ia()
    with db.conectar(ia.config) as conn:
        c = grafo_consulta.conceito(conn, conceito)
    if not c:
        raise HTTPException(404, "conceito não encontrado")
    return c


# Build da interface (web/, `npm run build`). Sem ele, a API funciona sozinha.
if ESTATICOS.is_dir():
    app.mount("/", StaticFiles(directory=ESTATICOS, html=True), name="estaticos")


def iniciar():
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000)
