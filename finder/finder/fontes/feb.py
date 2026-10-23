"""Downloads da FEB (WordPress): uma página por categoria, com paginação
/page/N/ e links diretos para wp-content/uploads/*.pdf."""

import re

from ..coleta import Obra, combina, nome_arquivo, pdfs_da_pagina, rastrear

NOME = "feb"
INICIO = "https://febnet.org.br/downloads-categorias/"
CATEGORIA = re.compile(r"^https://febnet\.org\.br/categorias-download/([^/]+)/(?:page/\d+/?)?$")

# Documentos institucionais, não obras.
IGNORAR = {
    "documentos-administrativos", "estatuto", "servicos-juridicos", "portarias",
    "cfn-atas", "cfn-atas-comissoes", "cfn-outros-documentos", "cfn-arte",
    "cfn-comunicacao-social-espirita", "galeria-ex-presidentes",
}


def _seguir(url):
    m = CATEGORIA.match(url)
    return bool(m) and m.group(1) not in IGNORAR


def buscar(cliente, termo, max_paginas=200, log=print):
    vistos = set()
    for url, doc in rastrear(cliente, [INICIO], _seguir, max_paginas, log):
        m = CATEGORIA.match(url)
        if not m:
            continue
        categoria = m.group(1)
        for url_pdf, (titulo, capa) in pdfs_da_pagina(doc, url).items():
            if url_pdf in vistos:
                continue
            vistos.add(url_pdf)
            if combina(termo, titulo, categoria, nome_arquivo(url_pdf)):
                yield Obra(NOME, titulo, url_pdf, url, categoria, capa)
