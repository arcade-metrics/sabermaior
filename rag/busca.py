"""Busca vetorial (pgvector/HNSW), textual (BM25 real via ParadeDB pg_search)
ou híbrida (RRF), com reranking opcional. Padrão (modo auto, idioma auto):
vetorial para perguntas, híbrida para palavras-chave, no idioma da pergunta;
foi o melhor resultado em rag/avaliacao.jsonl (veja README)."""

import re

from pgvector import Vector

from .extracao import idioma_consulta

RRF_K = 60
PESO_TEXTO = 1.0  # peso da lista textual na fusão (a vetorial pesa 1)
IDIOMA_PADRAO = "pt"  # perguntas sem sinal claro de idioma
_COLUNAS = """t.id, t.obra_id, t.conteudo, t.metadados, t.pagina_ini, t.pagina_fim,
              o.titulo, o.autor, o.manifesto->>'autor_espiritual' AS autor_espiritual"""


def _filtros(obra, idioma):
    sql, params = "", {}
    if obra:
        sql += " AND (o.id = %(obra)s OR f_unaccent(o.titulo) ILIKE f_unaccent(%(obra_like)s))"
        params.update(obra=obra, obra_like=f"%{obra}%")
    if idioma:
        sql += " AND t.idioma = %(idioma)s"
        params["idioma"] = idioma
    return sql, params


def _linhas(cur):
    nomes = [d.name for d in cur.description]
    return [dict(zip(nomes, r)) for r in cur.fetchall()]


def vetorial(conn, ia, consulta, n, obra=None, idioma=None):
    vetor = Vector(ia.embed([consulta])[0])
    filtro, params = _filtros(obra, idioma)
    with conn.cursor() as cur:
        cur.execute("SET LOCAL hnsw.ef_search = 100")
        cur.execute("SET LOCAL hnsw.iterative_scan = relaxed_order")  # filtros não esvaziam o top-n
        cur.execute(f"""
            SELECT {_COLUNAS}, 1 - (t.embedding <=> %(v)s) AS similaridade
            FROM trechos t JOIN obras o ON o.id = t.obra_id
            WHERE t.modelo_embedding = %(modelo)s {filtro}
            ORDER BY t.embedding <=> %(v)s LIMIT %(n)s
        """, {"v": vetor, "modelo": ia.config.embed_model, "n": n, **params})
        return _linhas(cur)


def textual(conn, consulta, n, obra=None, idioma=None):
    """BM25 real (ParadeDB pg_search) sobre o texto sem acento, exigindo
    todas as palavras da consulta (E) via paradedb.match(conjunction_mode).
    O stemmer do índice é só em português (sql/002_bm25.sql); es/en/fr não
    são estemizados, mas continuam tokenizados e buscáveis."""
    filtro, params = _filtros(obra, idioma)
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT {_COLUNAS}, paradedb.score(t.id) AS rank_texto
            FROM trechos t JOIN obras o ON o.id = t.obra_id
            WHERE t.conteudo_simples @@@ paradedb.match('conteudo_simples', f_unaccent(%(q)s),
                                                         conjunction_mode => true) {filtro}
            ORDER BY rank_texto DESC LIMIT %(n)s
        """, {"q": consulta, "n": n, **params})
        return _linhas(cur)


def modo_consulta(consulta):
    """Palavras-chave ("aeróbus", "bônus-hora") pedem a busca textual: termo
    raro some no vetor. Pergunta em linguagem natural vai só no vetor."""
    return "hibrida" if "?" not in consulta and len(re.findall(r"[\w-]+", consulta)) <= 4 else "vetorial"


def buscar(conn, ia, consulta, k=8, modo="auto", candidatos=40, rerank=True, obra=None, idioma="auto",
           peso_texto=None):
    """Top-k trechos. modo: auto | vetorial | textual | hibrida. idioma: "auto"
    (o da pergunta; evita que traduções da mesma obra ocupem o topo), "todos"
    ou um código (pt, es, en, fr, eo)."""
    peso_texto = PESO_TEXTO if peso_texto is None else peso_texto
    if modo == "auto":
        modo = modo_consulta(consulta)
    if idioma == "auto":
        idioma = idioma_consulta(consulta, IDIOMA_PADRAO)
    elif idioma in (None, "todos"):
        idioma = None
    listas = []
    if modo in ("vetorial", "hibrida"):
        listas.append((1.0, vetorial(conn, ia, consulta, candidatos, obra, idioma)))
    if modo in ("textual", "hibrida"):
        listas.append((peso_texto, textual(conn, consulta, candidatos, obra, idioma)))
    conn.rollback()  # encerra a transação dos SET LOCAL

    fundidos = {}
    for peso, lista in listas:
        for posicao, linha in enumerate(lista):
            atual = fundidos.setdefault(linha["id"], {**linha, "rrf": 0.0})
            atual.update({c: v for c, v in linha.items() if c not in atual})
            atual["rrf"] += peso / (RRF_K + posicao + 1)
    ordenados = sorted(fundidos.values(), key=lambda r: r["rrf"], reverse=True)

    if rerank and ia.config.rerank_provider != "none":
        topo = ordenados[:max(k * 3, 20)]
        notas = ia.rerank(consulta, [r["conteudo"] for r in topo])
        for r, nota in zip(topo, notas):
            r["rerank"] = nota
        ordenados = sorted(topo, key=lambda r: r["rerank"], reverse=True)
    return ordenados[:k]


def referencia(t):
    """'O Livro dos Espíritos — Parte... > Cap... > Seção, q. 344-345, p. 138'"""
    m = t["metadados"]
    partes = [m[k] for k in ("parte", "capitulo", "secao") if m.get(k)]
    ref = t["titulo"] + (f" — {' > '.join(partes)}" if partes else "")
    if m.get("itens"):
        a, b = m["itens"]
        ref += f", item {a}" + (f"-{b}" if b != a else "")
    p_ini, p_fim = t["pagina_ini"], t["pagina_fim"]
    return ref + f", p. {p_ini}" + (f"-{p_fim}" if p_fim != p_ini else "")
