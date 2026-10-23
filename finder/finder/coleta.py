"""Funções comuns aos adaptadores: modelo da obra, filtro por termo e extração
de links de PDF de páginas HTML."""

import re
import unicodedata
from collections import deque
from dataclasses import dataclass
from pathlib import PurePosixPath
from urllib.parse import unquote, urldefrag, urljoin, urlsplit

import requests
from lxml import html

from .rede import Bloqueado


@dataclass
class Obra:
    fonte: str
    titulo: str
    url_pdf: str
    url_pagina: str
    categoria: str = ""
    url_capa: str | None = None


def normalizar(texto):
    sem_acento = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", sem_acento.lower()).split())


def combina(termo, *textos):
    """Verdadeiro se todas as palavras do termo aparecem nos textos (sem acento e caixa)."""
    if not termo:
        return True
    alvo = normalizar(" ".join(t or "" for t in textos))
    return all(p in alvo for p in normalizar(termo).split())


def nome_arquivo(url):
    return unquote(PurePosixPath(urlsplit(url).path).name)


def titulo_do_arquivo(url):
    return " ".join(re.sub(r"[-_]+", " ", PurePosixPath(nome_arquivo(url)).stem).split())


def eh_pdf(url):
    return urlsplit(url).path.lower().endswith(".pdf")


def _absoluto(base, href):
    href = (href or "").strip()
    if not href or href.startswith(("javascript:", "mailto:", "#")):
        return None
    url = urldefrag(urljoin(base, href)).url
    return url if url.startswith(("http://", "https://")) else None


def links(doc, base):
    resultado = []
    for a in doc.iter("a"):
        url = _absoluto(base, a.get("href"))
        if url:
            resultado.append(url)
    return resultado


def _texto(el):
    return " ".join(el.text_content().split())


def _titulo_vizinho(a, base, url_pdf):
    """Para links sem texto (ícone ou botão), procura um título no bloco que
    contém o link, sem subir até um bloco que tenha outros PDFs."""
    el = a.getparent()
    for _ in range(6):
        if el is None:
            return ""
        outros = {u for u in (_absoluto(base, x.get("href")) for x in el.iter("a")) if u and eh_pdf(u)}
        if outros - {url_pdf}:
            return ""
        for h in el.iter("h1", "h2", "h3", "h4", "h5", "h6"):
            if _texto(h):
                return _texto(h)
        el = el.getparent()
    return ""


# Textos de botão que não servem de título; nesses casos o título vem do bloco vizinho.
GENERICOS = {
    "download", "downloads", "baixar", "baixe", "baixe aqui", "baixar pdf", "download pdf",
    "pdf", "ebook", "e book", "clique aqui", "aqui", "leia", "ler", "acessar", "abrir", "link",
}


def pdfs_da_pagina(doc, base):
    """Mapeia cada PDF linkado na página para (título, url da capa)."""
    achados = {}
    for a in doc.iter("a"):
        url = _absoluto(base, a.get("href"))
        if not url or not eh_pdf(url):
            continue
        item = achados.setdefault(url, {"partes": [], "capa": None, "ancora": a})
        texto = _texto(a) or (a.get("title") or "").strip()
        if normalizar(texto) in GENERICOS:
            texto = ""
        if texto and texto not in item["partes"]:
            item["partes"].append(texto)
        img = next(a.iter("img"), None)
        if img is not None and item["capa"] is None:
            item["capa"] = _absoluto(base, img.get("src"))
            alt = (img.get("alt") or "").strip()
            if alt and not texto and alt not in item["partes"]:
                item["partes"].append(alt)
    resultado = {}
    for url, item in achados.items():
        titulo = " ".join(item["partes"]) or _titulo_vizinho(item["ancora"], base, url) or titulo_do_arquivo(url)
        resultado[url] = (titulo, item["capa"])
    return resultado


def rastrear(cliente, inicio, seguir, max_paginas=200, log=print):
    """Percorre páginas HTML a partir de `inicio`, entrando só nos links aceitos
    por `seguir(url)`. Gera (url, documento lxml)."""
    fila = deque(inicio)
    vistos = set(inicio)
    paginas = 0
    while fila and paginas < max_paginas:
        url = fila.popleft()
        try:
            r = cliente.get(url)
        except Bloqueado:
            raise
        except requests.RequestException as e:
            log(f"  falha ao abrir {url}: {e}")
            continue
        if "html" not in r.headers.get("Content-Type", ""):
            continue
        paginas += 1
        doc = html.fromstring(r.content)
        yield r.url, doc
        for proximo in links(doc, r.url):
            if proximo not in vistos and not eh_pdf(proximo) and seguir(proximo):
                vistos.add(proximo)
                fila.append(proximo)
    if fila:
        log(f"  limite de {max_paginas} páginas atingido; {len(fila)} páginas não visitadas")
