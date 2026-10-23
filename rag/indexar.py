"""Ingestão: PDF -> texto -> manifesto -> chunks -> embeddings -> Postgres."""

import csv
import hashlib
import re
import time
import unicodedata
from pathlib import Path

from psycopg.types.json import Jsonb

from ia import ErroIA

from . import chunking, sumario
from .extracao import CONFIG_FTS, extrair, idioma

LOTE_EMBEDDINGS = 32


def slug(texto, limite=50):
    t = unicodedata.normalize("NFKD", texto)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_")[:limite] or "obra"


def sha256(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def ler_catalogo(dados):
    """catalogo.csv do finder, indexado pelo caminho relativo do PDF."""
    arquivo = Path(dados) / "catalogo.csv"
    if not arquivo.exists():
        return {}
    with open(arquivo, encoding="utf-8-sig", newline="") as f:
        return {Path(l["arquivo"]).as_posix(): l for l in csv.DictReader(f, delimiter=";")}


def cabecalho(manifesto, meta):
    """Contexto que vai junto do texto no embedding (não no conteúdo salvo)."""
    autoria = " / ".join(x for x in (manifesto.get("autor_espiritual"), manifesto.get("autor")) if x)
    obra = manifesto["titulo"] + (f" ({autoria})" if autoria else "")
    caminho = " > ".join(meta[k] for k in ("parte", "capitulo", "secao") if meta.get(k))
    return f"{obra}\n{caminho}".strip()


def _embed_lote(ia, textos):
    """Se o lote for recusado (ex.: texto acima do limite de tokens do
    servidor), embeda um a um e corta pela metade o que ainda falhar."""
    try:
        return ia.embed(textos)
    except ErroIA:
        vetores = []
        for texto in textos:
            while True:
                try:
                    vetores += ia.embed([texto])
                    break
                except ErroIA:
                    if len(texto) < 200:
                        raise
                    texto = texto[:len(texto) // 2]
        return vetores


def manifesto(caminho, linhas, info, ia, usar_llm):
    meta = {}
    if usar_llm:
        try:
            meta = sumario.metadados(ia, linhas)
        except ErroIA as e:
            meta = {"erro_llm": str(e)[:200]}
    entradas, metodo, paginas_toc = sumario.ler(caminho, linhas, ia if usar_llm else None)
    titulo_catalogo = (info.get("titulo") or "").strip()
    # títulos do catálogo como "obreirosdavidaeterna" são só o nome do arquivo
    titulo = titulo_catalogo if " " in titulo_catalogo else (meta.get("titulo") or titulo_catalogo or caminho.stem)
    texto = " ".join(l.texto for l in linhas[:3000])
    m = {
        "titulo": titulo,
        **{k: meta.get(k) for k in ("autor", "autor_espiritual", "medium", "tradutor", "editora", "ano")},
        "idioma": idioma(texto),
        "fonte": info.get("fonte"),
        "categoria": info.get("categoria"),
        "url_pdf": info.get("url_pdf"),
        "metodo_sumario": metodo,
        "paginas_sumario": paginas_toc,
        "sumario": [{k: e.get(k) for k in ("nivel", "titulo", "pagina_impressa", "pagina_pdf")} for e in entradas],
    }
    if "erro_llm" in meta:
        m["erro_llm"] = meta["erro_llm"]
    return m, entradas, paginas_toc


def ingerir(caminho, info, ia, conn, refazer=False, usar_llm=True, log=print):
    """Ingere um PDF. Devolve o número de chunks gravados (0 = pulado)."""
    caminho = Path(caminho)
    hash_ = info.get("sha256") or sha256(caminho)
    modelo = ia.config.embed_model
    if not refazer:
        ja = conn.execute("SELECT 1 FROM obras o JOIN trechos t ON t.obra_id = o.id "
                          "WHERE o.sha256 = %s AND t.modelo_embedding = %s LIMIT 1", (hash_, modelo)).fetchone()
        if ja:
            return 0
    inicio = time.monotonic()
    linhas = extrair(caminho)
    if not linhas:
        log(f"  sem texto: {caminho.name}")
        return 0
    man, entradas, paginas_toc = manifesto(caminho, linhas, info, ia, usar_llm)
    obra_id = f"{slug(caminho.stem)}_{hash_[:8]}"
    man["livro_id"] = obra_id
    trechos = list(chunking.chunks(linhas, entradas, paginas_toc))
    if not trechos:
        log(f"  nenhum chunk: {caminho.name}")
        return 0

    textos = [f"{cabecalho(man, t['metadados'])}\n\n{t['conteudo']}" for t in trechos]
    vetores = []
    for i in range(0, len(textos), LOTE_EMBEDDINGS):
        vetores += _embed_lote(ia, textos[i:i + LOTE_EMBEDDINGS])

    cfg = CONFIG_FTS.get(man["idioma"], "simple")
    with conn.transaction():
        conn.execute("DELETE FROM obras WHERE sha256 = %s AND id <> %s", (hash_, obra_id))
        conn.execute("""
            INSERT INTO obras (id, sha256, titulo, autor, fonte, arquivo, idioma, paginas, manifesto)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET sha256 = EXCLUDED.sha256, titulo = EXCLUDED.titulo,
                autor = EXCLUDED.autor, fonte = EXCLUDED.fonte, arquivo = EXCLUDED.arquivo,
                idioma = EXCLUDED.idioma, paginas = EXCLUDED.paginas, manifesto = EXCLUDED.manifesto,
                ingerido_em = now()
        """, (obra_id, hash_, man["titulo"], man.get("autor"), man.get("fonte"), caminho.as_posix(),
              man["idioma"], max(l.pagina for l in linhas), Jsonb(man)))
        conn.execute("DELETE FROM trechos WHERE obra_id = %s", (obra_id,))
        with conn.cursor() as cur:
            cur.executemany("""
                INSERT INTO trechos (id, obra_id, ordem, conteudo, metadados, pagina_ini, pagina_fim,
                                     idioma, fts_cfg, modelo_embedding, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::regconfig, %s, %s)
            """, [(f"{obra_id}_{i:05d}", obra_id, i, t["conteudo"], Jsonb(t["metadados"]),
                   t["pagina_ini"], t["pagina_fim"], man["idioma"], cfg, modelo, v)
                  for i, (t, v) in enumerate(zip(trechos, vetores))])
    log(f"  {obra_id}: {len(trechos)} chunks, sumário {man['metodo_sumario']} "
        f"({len(entradas)} entradas), {man['idioma']}, {time.monotonic() - inicio:.1f}s")
    return len(trechos)

