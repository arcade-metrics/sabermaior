"""Extração do texto dos PDFs com PyMuPDF: remove cabeçalhos, rodapés,
números de página e notas de rodapé (fonte bem menor que a do corpo),
desfaz a hifenização de fim de linha e marca o fim de parágrafo pela
margem direita da linha."""

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass

import pymupdf

PRONOMES_ENCLITICOS = {"se", "me", "te", "lhe", "lhes", "o", "a", "os", "as", "lo", "la", "los", "las",
                       "no", "na", "nos", "nas", "vos", "ia", "ei", "ás", "á", "emos", "eis", "ão", "iam"}
_PAGINA = re.compile(r"^(?:[-–—]?\s*\d{1,4}\s*[-–—]?|[ivxlcdm]{1,6}|p[áa]g(?:ina)?\.?\s*\d+)$", re.I)


@dataclass
class Linha:
    texto: str
    pagina: int  # 1 = primeira página do PDF
    fim_paragrafo: bool


def normalizar(texto):
    """Sem acento, minúsculo, espaços simples: para comparar títulos."""
    t = unicodedata.normalize("NFKD", texto)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", t)).strip()


def _limpar(texto):
    texto = texto.replace("\xa0", " ").replace("­", "-").replace("ﬁ", "fi").replace("ﬂ", "fl")
    texto = re.sub(r"([.\-_…·*=])\1{3,}", r"\1\1\1", texto)  # pontilhados de sumário custam muitos tokens
    return re.sub(r"\s+", " ", texto).strip()


def _chave_repeticao(texto):
    return re.sub(r"\d+", "#", normalizar(texto))


def _linhas_brutas(doc):
    """[(pagina, [(texto, tamanho, x0, x1)])] na ordem de leitura."""
    paginas = []
    for i, pagina in enumerate(doc, 1):
        linhas = []
        for bloco in pagina.get_text("dict", sort=False)["blocks"]:
            for l in bloco.get("lines", []):
                spans = [s for s in l["spans"] if s["text"].strip()]
                if not spans:
                    linhas.append(None)  # linha em branco: separa parágrafos
                    continue
                # flags & 1 = sobrescrito: chamada de nota ("aeróbus.²")
                texto = _limpar("".join(s["text"] for s in l["spans"] if not s["flags"] & 1 or len(spans) == 1))
                tamanho = max(spans, key=lambda s: len(s["text"]))["size"]
                linhas.append((texto, tamanho, spans[0]["bbox"][0], spans[-1]["bbox"][2]))
        paginas.append((i, linhas))
    return paginas


def _boilerplate(paginas, borda=3):
    """Chaves de linhas que se repetem no topo ou no pé de muitas páginas."""
    contagem = Counter()
    for _, linhas in paginas:
        linhas = [l for l in linhas if l]
        vistas = {_chave_repeticao(t) for t, *_ in linhas[:borda] + linhas[-borda:]}
        contagem.update(k for k in vistas if k and k != "#")
    minimo = max(3, int(len(paginas) * 0.2))
    return {k for k, n in contagem.items() if n >= minimo}


def _juntar_hifen(anterior, proxima):
    """Junta palavra partida no fim da linha, mantendo hífen de ênclise
    (devolve-se, poder-se-ia) e de palavra composta com maiúscula."""
    m = re.match(r"(\w+)", proxima)
    if not m:
        return anterior + proxima
    seguinte = m.group(1).lower()
    if seguinte in PRONOMES_ENCLITICOS or proxima[:1].isupper():
        return anterior + proxima
    return anterior[:-1] + proxima


def extrair(caminho):
    """Lista de Linha do documento inteiro, já sem cabeçalho/rodapé."""
    with pymupdf.open(caminho) as doc:
        paginas = _linhas_brutas(doc)
    tamanhos = Counter()
    for _, linhas in paginas:
        for t, tam, *_ in filter(None, linhas):
            tamanhos[round(tam)] += len(t)
    corpo = tamanhos.most_common(1)[0][0] if tamanhos else 10
    repetidas = _boilerplate(paginas)

    saida = []
    for numero, todas in paginas:
        texto_linhas = [l for l in todas if l]
        n = len(texto_linhas)
        margem = sorted(x1 for *_, x1 in texto_linhas)[int(n * 0.9)] if n else 0
        esquerda = min((x0 for _, _, x0, _ in texto_linhas), default=0)
        largura = max(margem - esquerda, 1)
        i = -1
        anterior = None  # (tamanho,) da última linha mantida nesta página
        for bruta in todas:
            if bruta is None:
                if saida and saida[-1].pagina == numero:
                    saida[-1].fim_paragrafo = True
                continue
            i += 1
            texto, tamanho, x0, x1 = bruta
            na_borda = i < 3 or i >= n - 3
            if na_borda and (_chave_repeticao(texto) in repetidas or _PAGINA.match(texto)):
                continue
            if tamanho < corpo * 0.8:  # nota de rodapé, número de chamada
                continue
            mudou_fonte = anterior is not None and abs(tamanho - anterior) > anterior * 0.15
            a_direita = x0 > esquerda + largura * 0.5  # assinatura, autor alinhado à direita
            if saida and saida[-1].pagina == numero and (mudou_fonte or a_direita):
                saida[-1].fim_paragrafo = True
            curta = x1 < margem - largura * 0.12
            saida.append(Linha(texto, numero, curta or a_direita))
            anterior = tamanho
    return saida


def paragrafos(linhas):
    """Agrupa linhas em parágrafos: [(texto, pagina_ini, pagina_fim, [linhas])]."""
    atual, inicio, fim, membros = "", None, None, []
    for l in linhas:
        if not atual:
            atual, inicio = l.texto, l.pagina
        elif atual.endswith("-"):
            atual = _juntar_hifen(atual, l.texto)
        else:
            atual = f"{atual} {l.texto}"
        fim = l.pagina
        membros.append(l)
        if l.fim_paragrafo:
            yield atual, inicio, fim, membros
            atual, membros = "", []
    if atual:
        yield atual, inicio, fim, membros


# Palavras frequentes que distinguem cada idioma (sem as comuns a dois deles,
# como "la", "de", "por", que confundiam espanhol com esperanto).
_PALAVRAS_IDIOMA = {
    "pt": {"não", "uma", "com", "os", "das", "dos", "ao", "pelo", "pela", "são", "isso", "ele", "em", "um", "muito"},
    "es": {"el", "y", "los", "del", "una", "es", "con", "pero", "muy", "sus", "lo", "más", "ha", "ser", "esta"},
    "en": {"the", "and", "of", "to", "is", "that", "with", "for", "which", "are", "this", "have", "not"},
    "fr": {"le", "les", "des", "et", "est", "une", "dans", "qui", "pour", "pas", "sont", "avec", "nous"},
    "eo": {"kaj", "estas", "ke", "kiu", "kiuj", "oni", "ili", "sed", "ĉi", "tiu", "pri", "sia", "ankaŭ", "ĉar", "povas"},
}
CONFIG_FTS = {"pt": "portuguese", "es": "spanish", "en": "english", "fr": "french"}


_PALAVRAS_CONSULTA = {
    "pt": {"o", "que", "é", "qual", "quais", "como", "por", "não", "do", "da", "dos", "das", "os", "as", "um", "uma",
           "ao", "seu", "sua", "são", "há", "está", "segundo", "quem", "onde"},
    "es": {"el", "qué", "es", "cuál", "cómo", "los", "las", "del", "y", "según", "son", "hay", "quién", "dónde"},
    "en": {"what", "is", "the", "how", "why", "who", "which", "of", "and", "are", "does", "do", "according", "to"},
    "fr": {"qu", "est", "ce", "le", "les", "des", "quoi", "comment", "pourquoi", "selon", "et", "une", "qui"},
    "eo": {"kio", "estas", "kiel", "kial", "kaj", "laŭ", "kiu", "kie"},
}


def idioma_consulta(texto, padrao="pt"):
    """Idioma de uma pergunta curta; sem sinal claro, `padrao`."""
    t = texto.lower()
    if "¿" in t or "¡" in t or "ñ" in t:
        return "es"
    palavras = re.findall(r"\w+", t)
    notas = {k: sum(p in v for p in palavras) for k, v in _PALAVRAS_CONSULTA.items()}
    melhor = max(notas.values())
    if melhor == 0:
        return padrao
    empatados = [k for k, n in notas.items() if n == melhor]
    return padrao if padrao in empatados else empatados[0]


def idioma(texto):
    palavras = re.findall(r"\w+", texto.lower())[:20000]
    contagem = Counter(palavras)
    notas = {k: sum(contagem[p] for p in v) for k, v in _PALAVRAS_IDIOMA.items()}
    return max(notas, key=notas.get) if any(notas.values()) else None
