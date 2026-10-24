"""Catálogo das obras indexadas, para a página "Obras" da interface.
Só lista obras visíveis (`NOT oculta`, ver sql/004_obras_ocultas.sql)."""

import re
from pathlib import Path

import pymupdf

# Rótulo legível da coleção, a partir de manifesto->>'categoria' (só a parte antes da "/").
COLECOES = {
    "obras-kardec": "Obras de Kardec",
    "obras-kardec-complementares": "Complementares a Kardec",
    "revista-espirita": "Revista Espírita",
    "chicoxavier": "Chico Xavier",
    "biografias": "Biografias",
    "diversosautores": "Diversos autores",
    "principal": "Principais",
}


def _colecao(categoria):
    base = (categoria or "").split("/")[0]
    return COLECOES.get(base, "Outras")


def _nome(texto):
    """'FRANCISCO CÂNDIDO XAVIER' -> 'Francisco Cândido Xavier'; o resto fica como está."""
    if not texto:
        return None
    texto = texto.strip()
    return texto.title() if texto.isupper() else texto


def _ano(texto):
    m = re.search(r"\b(1[5-9]\d\d|20\d\d)\b", texto or "")
    return int(m.group(1)) if m else None


def _resumo(linha):
    id_, titulo, autor, fonte, paginas, m, trechos = linha
    return {
        "id": id_,
        "titulo": _nome(titulo),
        "autor": _nome(autor),
        "autor_espiritual": _nome(m.get("autor_espiritual")),
        "colecao": _colecao(m.get("categoria")),
        "fonte": fonte,
        "ano": _ano(m.get("ano")),
        "paginas": paginas,
        "trechos": trechos,
    }


_SELECT = """
    SELECT o.id, o.titulo, o.autor, o.fonte, o.paginas, o.manifesto,
           (SELECT count(*) FROM trechos t WHERE t.obra_id = o.id) AS trechos
    FROM obras o
    WHERE NOT o.oculta AND o.idioma = %(idioma)s
"""


def listar(conn, idioma="pt"):
    linhas = conn.execute(_SELECT + " ORDER BY f_unaccent(lower(o.titulo))", {"idioma": idioma}).fetchall()
    return [_resumo(l) for l in linhas]


def detalhe(conn, obra_id, idioma="pt"):
    linha = conn.execute(_SELECT + " AND o.id = %(id)s", {"idioma": idioma, "id": obra_id}).fetchone()
    if not linha:
        return None
    m = linha[5]
    sumario = [
        {"nivel": s.get("nivel", 1), "titulo": re.sub(r"[\s.…]+$", "", s.get("titulo", "")),
         "pagina": s.get("pagina_impressa") or s.get("pagina_pdf")}
        for s in m.get("sumario") or []
    ]
    return {
        **_resumo(linha),
        "medium": _nome(m.get("medium")),
        "tradutor": _nome(m.get("tradutor")),
        "url_pdf": m.get("url_pdf"),
        "sumario": sumario,
    }


def capa(conn, obra_id, cache_dir, largura=240):
    """Miniatura PNG da 1ª página do PDF, gerada uma vez e guardada em `cache_dir`.
    None se a obra não existir ou o PDF não estiver nesta máquina (ex.: na VM)."""
    if not re.fullmatch(r"[\w-]+", obra_id):  # vira nome de arquivo: nada de "../"
        return None
    destino = Path(cache_dir) / f"{obra_id}.png"
    if destino.exists():
        return destino
    linha = conn.execute("SELECT arquivo FROM obras WHERE id = %s AND NOT oculta", (obra_id,)).fetchone()
    if not linha or not Path(linha[0]).exists():
        return None
    with pymupdf.open(linha[0]) as pdf:
        pagina = pdf[0]
        pix = pagina.get_pixmap(matrix=pymupdf.Matrix(largura / pagina.rect.width, largura / pagina.rect.width))
    destino.parent.mkdir(parents=True, exist_ok=True)
    pix.save(destino)
    return destino
