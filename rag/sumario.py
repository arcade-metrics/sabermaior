"""Sumário (TOC) e manifesto da obra. Ordem de tentativa: marcadores do PDF,
página de sumário reconhecida por regex, e, se a regex não der conta, a
LLM lê a página do sumário. Cada entrada é depois localizada no texto
(linha exata do título) para servir de cabeçalho no chunking."""

import re

import pymupdf

from ia import ErroIA

from .extracao import normalizar

_ENTRADA = re.compile(r"^(?P<titulo>.*?\S)\s*(?:\.{2,}|…+|_{2,}|\s)\s*(?P<pagina>\d{1,4})$")
_PALAVRA_SUMARIO = re.compile(r"^(sumario|indice|indice geral|conteudo|contents|table of contents|index|"
                              r"table des matieres|enhavo|tabla de materias|indice general)$")
_PARTE = re.compile(r"^(?:(?:primeira|segunda|terceira|quarta|quinta|sexta|first|second|third|fourth|"
                    r"premiere|deuxieme|troisieme|quatrieme|primera|tercera|cuarta|unua|dua|tria|kvara)\s+)?"
                    r"(?:parte|livro|part|partie|libro|parto|libro)\b")
_CAPITULO = re.compile(r"^(?:capitulo|chapter|chapitre|cap|ĉapitro|capitolo)\b")
_NUMERO_INICIAL = re.compile(r"^(?:\d{1,3}|[ivxlc]{1,7})\s*[-–.)]?\s+(?=\S)", re.I)


def nivel_titulo(texto):
    """1 = parte, 2 = capítulo, 3 = seção, None = não parece título."""
    n = normalizar(texto)
    palavras = n.split()
    if not palavras or len(texto) > 120:
        return None
    if _PARTE.match(n) and len(palavras) <= 8 or len(palavras) <= 3 and palavras[-1] in {"parte", "part", "partie"}:
        return 1
    if _CAPITULO.match(n) and len(palavras) <= 14:
        return 2
    letras = [c for c in texto if c.isalpha()]
    if len(letras) >= 4 and len(palavras) <= 15 and not re.match(r"^\d+\s*[.)]", texto) \
            and sum(c.isupper() for c in letras) / len(letras) >= 0.85:
        return 3
    return None


def _nucleo(titulo):
    """Título sem 'CAPÍTULO IV -' ou '12' na frente, para casar com o texto."""
    n = normalizar(titulo)
    n = re.sub(r"^(?:capitulo|chapter|chapitre|cap)\s+[\divxlc]+\s*", "", n)
    n = _NUMERO_INICIAL.sub("", n)
    return n.strip() or normalizar(titulo)


def _nivel_entrada(titulo, tem_capitulos):
    n = normalizar(titulo)
    if _PARTE.match(n):
        return 1
    if _CAPITULO.match(n) or _NUMERO_INICIAL.match(titulo):
        return 2
    return 3 if tem_capitulos else 2


def _por_regex(linhas, paginas_total):
    """Procura páginas de sumário nas 15 primeiras e 15 últimas páginas."""
    por_pagina = {}
    for l in linhas:
        if l.pagina <= 15 or l.pagina > paginas_total - 15:
            por_pagina.setdefault(l.pagina, []).append(l.texto)
    entradas, paginas_toc = [], []
    for pagina in sorted(por_pagina):
        textos = por_pagina[pagina]
        casadas = sum(1 for t in textos if _ENTRADA.match(t))
        titulo_sumario = any(_PALAVRA_SUMARIO.match(normalizar(t)) for t in textos[:4])
        continua = bool(paginas_toc) and paginas_toc[-1] == pagina - 1
        if not ((titulo_sumario or continua) and casadas >= 2 or casadas >= max(4, len(textos) * 0.3)):
            if entradas:
                break
            continue
        paginas_toc.append(pagina)
        pendente = ""
        for t in textos:
            if _PALAVRA_SUMARIO.match(normalizar(t)):
                continue
            m = _ENTRADA.match(t)
            if m:
                titulo = m.group("titulo")
                # linha anterior sem número: título quebrado em duas linhas, ou
                # descrição do capítulo (longa), que fica de fora
                if pendente and len(pendente) < 90 and not nivel_titulo(titulo) in (1, 2) \
                        and not _NUMERO_INICIAL.match(titulo):
                    titulo = f"{pendente} {titulo}"
                titulo = titulo.strip(" .")
                entradas.append({"titulo": re.sub(r"\s+", " ", titulo), "pagina_impressa": int(m.group("pagina"))})
                pendente = ""
            elif _PARTE.match(normalizar(t)):
                entradas.append({"titulo": t.strip(), "pagina_impressa": None, "nivel": 1})
                pendente = ""
            elif entradas and entradas[-1].get("nivel") == 1 and entradas[-1]["pagina_impressa"] is None \
                    and not pendente:
                entradas[-1]["titulo"] += f" - {t.strip()}"
            else:
                pendente = f"{pendente} {t}".strip()
    return entradas, paginas_toc


_ESQUEMA_TOC = {
    "type": "object",
    "properties": {"entradas": {"type": "array", "items": {
        "type": "object",
        "properties": {"titulo": {"type": "string"}, "nivel": {"type": "integer"},
                       "pagina": {"type": ["integer", "null"]}},
        "required": ["titulo", "nivel", "pagina"], "additionalProperties": False}}},
    "required": ["entradas"], "additionalProperties": False,
}


def _por_llm(ia, linhas, paginas_total):
    """Acha a página com o título 'Sumário/Índice/Contents' e pede à LLM que
    estruture as entradas."""
    alvo = None
    for l in linhas:
        if (l.pagina <= 15 or l.pagina > paginas_total - 15) and _PALAVRA_SUMARIO.match(normalizar(l.texto)):
            alvo = l.pagina
            break
    if alvo is None:
        return [], []
    paginas = [alvo, alvo + 1, alvo + 2]
    texto = "\n".join(l.texto for l in linhas if l.pagina in paginas)[:8000]
    resposta = ia.chat([
        {"role": "system", "content": "Você extrai o sumário de livros. Responda só com o JSON pedido. "
                                      "nivel: 1 = parte/livro, 2 = capítulo, 3 = subtítulo. pagina: número "
                                      "impresso no sumário ou null. Copie os títulos exatamente como no texto. "
                                      "Ignore o que não for entrada de sumário."},
        {"role": "user", "content": texto},
    ], esquema=_ESQUEMA_TOC, temperatura=0, raciocinio="none", max_tokens=6000)
    entradas = [{"titulo": e["titulo"].strip(), "pagina_impressa": e["pagina"], "nivel": min(max(e["nivel"], 1), 3)}
                for e in resposta["entradas"] if e["titulo"].strip()]
    return entradas, paginas


def _localizar(entradas, linhas, paginas_toc, deslocamento=None):
    """Para cada entrada, o índice da linha onde o título aparece no texto
    (busca sequencial, depois das páginas do sumário). Com `deslocamento`
    (página do PDF - página impressa), não aceita casamento antes da página
    indicada no sumário: evita casar com listas de tópicos no início do capítulo."""
    normal = [normalizar(l.texto) for l in linhas]
    cursor = 0
    while cursor < len(linhas) and paginas_toc and linhas[cursor].pagina <= max(paginas_toc):
        cursor += 1
    for e in entradas:
        alvo, completo = _nucleo(e["titulo"]), normalizar(e["titulo"])
        e["linha"] = e["pagina_pdf"] = None
        minima = e["pagina_impressa"] + deslocamento if deslocamento is not None and e["pagina_impressa"] else 0
        for i in range(cursor, len(linhas)):
            if linhas[i].pagina < minima:
                continue
            atual = normal[i]
            junto = f"{atual} {normal[i + 1]}" if i + 1 < len(linhas) else atual
            if atual in (alvo, completo) or (len(alvo) > 12 and atual.endswith(alvo) and len(atual) - len(alvo) < 25):
                e["n_linhas"] = 1
            elif junto in (alvo, completo):
                e["n_linhas"] = 2
            else:
                continue
            e["linha"], e["pagina_pdf"] = i, linhas[i].pagina
            cursor = i + e["n_linhas"]
            break
    return entradas


def _deslocamento(entradas):
    difs = sorted(e["pagina_pdf"] - e["pagina_impressa"] for e in entradas
                  if e.get("pagina_pdf") and e["pagina_impressa"])
    return difs[len(difs) // 2] if len(difs) >= 3 else None


def ler(caminho, linhas, ia=None):
    """Entradas do sumário [{titulo, nivel, pagina_impressa, pagina_pdf, linha,
    n_linhas}], o método usado (marcadores, regex, llm ou nenhum) e as páginas
    ocupadas pelo próprio sumário."""
    with pymupdf.open(caminho) as doc:
        marcadores, total = doc.get_toc(), doc.page_count
    if len(marcadores) >= 3:
        # marcadores já trazem a página do PDF: deslocamento zero
        entradas = [{"titulo": t, "nivel": min(n, 3), "pagina_impressa": p} for n, t, p in marcadores]
        _localizar(entradas, linhas, [], 0)
        return entradas, "marcadores", []
    entradas, paginas_toc = _por_regex(linhas, total)
    metodo = "regex"
    if len(entradas) < 3 and ia is not None:
        try:
            entradas, paginas_toc = _por_llm(ia, linhas, total)
        except ErroIA:  # JSON cortado ou servidor fora: segue só com a heurística de títulos
            entradas, paginas_toc = [], []
        metodo = "llm"
    if len(entradas) < 3:
        return [], "nenhum", paginas_toc
    tem_capitulos = any(_CAPITULO.match(normalizar(e["titulo"])) or _NUMERO_INICIAL.match(e["titulo"])
                        for e in entradas)
    for e in entradas:
        e.setdefault("nivel", _nivel_entrada(e["titulo"], tem_capitulos))
    deslocamento = _deslocamento(_localizar(entradas, linhas, paginas_toc))
    _localizar(entradas, linhas, paginas_toc, deslocamento)
    return entradas, metodo, paginas_toc


_ESQUEMA_OBRA = {
    "type": "object",
    "properties": {k: {"type": ["string", "null"]} for k in
                   ("titulo", "autor", "autor_espiritual", "medium", "tradutor", "editora", "ano")},
    "required": ["titulo", "autor", "autor_espiritual", "medium", "tradutor", "editora", "ano"],
    "additionalProperties": False,
}


def metadados(ia, linhas):
    """Título, autoria e edição lidos das primeiras páginas pela LLM."""
    texto = "\n".join(l.texto for l in linhas if l.pagina <= 6)[:4000]
    return ia.chat([
        {"role": "system", "content": "Extraia dados bibliográficos das páginas iniciais de um livro espírita. "
                                      "autor: quem assina a obra (em obras psicografadas, o médium, ex.: "
                                      "Francisco Cândido Xavier). autor_espiritual: o Espírito, se houver "
                                      "(ex.: Emmanuel, André Luiz). Use null quando não constar."},
        {"role": "user", "content": texto},
    ], esquema=_ESQUEMA_OBRA, temperatura=0, raciocinio="none", max_tokens=600)
