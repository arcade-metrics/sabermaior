"""Enciclopédia do Portal Luz Espírita: um índice com links
index.php?lisPage=enciclopedia&item=<verbete>. Os PDFs, quando existem, estão
nas páginas dos verbetes. Com termo de busca, só os verbetes cujo nome combina
com o termo são abertos, o que poupa muitas requisições."""

from urllib.parse import parse_qs, urlsplit

from ..coleta import Obra, combina, nome_arquivo, pdfs_da_pagina, rastrear

NOME = "luzespirita"
INICIO = "https://www.luzespirita.org.br/index.php?lisPage=enciclopedia"


def _parametros(url):
    partes = urlsplit(url)
    if not partes.netloc.endswith("luzespirita.org.br") or not partes.path.endswith("index.php"):
        return None
    q = parse_qs(partes.query)
    if q.get("lisPage") != ["enciclopedia"]:
        return None
    return q


def buscar(cliente, termo, max_paginas=200, log=print):
    def seguir(url):
        q = _parametros(url)
        if q is None:
            return False
        item = q.get("item", [""])[0]
        return not item or combina(termo, item)

    vistos = set()
    for url, doc in rastrear(cliente, [INICIO], seguir, max_paginas, log):
        q = _parametros(url) or {}
        verbete = q.get("item", [""])[0]
        for url_pdf, (titulo, capa) in pdfs_da_pagina(doc, url).items():
            if url_pdf in vistos:
                continue
            vistos.add(url_pdf)
            if combina(termo, titulo, verbete, nome_arquivo(url_pdf)):
                # Os PDFs são referências citadas no verbete; o verbete dá o contexto.
                titulo = f"{verbete} – {titulo}" if verbete else titulo
                yield Obra(NOME, titulo, url_pdf, url, verbete or "enciclopedia", capa)
