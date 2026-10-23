"""Biblioteca virtual de O Consolador: páginas HTML estáticas com links diretos
para os PDFs e capas em <img> dentro do link."""

from ..coleta import Obra, combina, nome_arquivo, pdfs_da_pagina, rastrear

NOME = "consolador"
INICIO = "https://www.oconsolador.com.br/linkfixo/bibliotecavirtual/principal.html"
PREFIXO = "https://www.oconsolador.com.br/linkfixo/bibliotecavirtual/"


def _seguir(url):
    return url.startswith(PREFIXO) and url.lower().endswith((".html", ".htm"))


def buscar(cliente, termo, max_paginas=200, log=print):
    vistos = set()
    for url, doc in rastrear(cliente, [INICIO], _seguir, max_paginas, log):
        categoria = url[len(PREFIXO):].rsplit(".", 1)[0] if url.startswith(PREFIXO) else url
        for url_pdf, (titulo, capa) in pdfs_da_pagina(doc, url).items():
            if url_pdf in vistos:
                continue
            vistos.add(url_pdf)
            if combina(termo, titulo, categoria, nome_arquivo(url_pdf)):
                yield Obra(NOME, titulo, url_pdf, url, categoria, capa)
