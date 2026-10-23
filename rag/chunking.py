"""Chunking estrutural: o texto é cortado nos títulos (sumário localizado ou
título em caixa alta) e, dentro de uma seção, agrupado por item numerado
(questão do LE, item do ESE) ou por parágrafo até o tamanho alvo. Cada
chunk herda parte/capítulo/seção e o intervalo de itens e páginas."""

import re

from .extracao import normalizar, paragrafos
from .sumario import nivel_titulo

ALVO = 1400     # caracteres (~350 tokens em português)
MAXIMO = 2200
SOBREPOSICAO = 250
_ITEM = re.compile(r"^(\d{1,4})\s*[.)]\s+\S")
# Em algumas edições da FEB o número do item vem num parágrafo isolado,
# separado do enunciado (layout em coluna): "1." numa linha, "Que é Deus?"
# na seguinte. Sem isso, quase nenhum item era reconhecido (ex.: só 1% dos
# trechos do Livro dos Espíritos, contra ~90% na edição onde número e
# enunciado ficam juntos).
_ITEM_SOZINHO = re.compile(r"^(\d{1,4})\s*[.)]$")
_FRASES = re.compile(r"(?<=[.!?…”\"])\s+(?=[\"“«(\-–—A-ZÀ-Ý0-9])")
NIVEIS = {1: "parte", 2: "capitulo", 3: "secao"}


def _frases(texto):
    """Frases; uma 'frase' maior que MAXIMO (lista, tabela, texto sem
    pontuação) é cortada por palavras."""
    for frase in _FRASES.split(texto):
        while len(frase) > MAXIMO:
            corte = frase.rfind(" ", 0, ALVO)
            corte = corte if corte > 0 else ALVO
            yield frase[:corte]
            frase = frase[corte:].lstrip()
        yield frase


def _partir(texto, alvo=ALVO):
    """Divide um parágrafo longo em pedaços de frases inteiras."""
    pedacos, atual = [], ""
    for frase in _frases(texto):
        if atual and len(atual) + len(frase) > alvo:
            pedacos.append(atual)
            atual = frase
        else:
            atual = f"{atual} {frase}".strip()
    if atual:
        pedacos.append(atual)
    return pedacos


def _cauda(texto, limite=SOBREPOSICAO):
    """Últimas frases até `limite` caracteres, para sobrepor ao próximo chunk."""
    frases = _FRASES.split(texto)
    cauda = ""
    for frase in reversed(frases[1:]):
        if len(cauda) + len(frase) > limite:
            break
        cauda = f"{frase} {cauda}".strip()
    return cauda


def chunks(linhas, sumario, paginas_sumario=()):
    """Gera dicts {conteudo, pagina_ini, pagina_fim, metadados}. As páginas do
    próprio sumário ficam de fora."""
    do_sumario, continuacao = {}, set()
    for e in sumario:
        i = e.get("linha")
        if i is None:
            continue
        do_sumario[id(linhas[i])] = e
        fim = i + e.get("n_linhas", 1) - 1
        continuacao.update(id(linhas[j]) for j in range(i + 1, fim + 1))
        # título vira parágrafo próprio
        for j in (i - 1, fim):
            if 0 <= j < len(linhas):
                linhas[j].fim_paragrafo = True
    paginas_sumario = set(paginas_sumario)
    linhas = [l for l in linhas if l.pagina not in paginas_sumario and id(l) not in continuacao]
    caminho = {}            # nivel -> título
    item, ultimo_item = None, 0
    pendente_item = None    # número de um parágrafo "N." isolado, para o próximo parágrafo
    buffer, paginas, itens = [], [], []
    titulo_anterior = None  # nível do parágrafo anterior, se foi título

    def emitir(sobrepor=False):
        nonlocal buffer, paginas, itens
        texto = "\n".join(buffer).strip()
        if len(re.sub(r"\W", "", texto)) >= 40:
            meta = {NIVEIS[n]: t for n, t in sorted(caminho.items())}
            if itens:
                meta["itens"] = [min(itens), max(itens)]
            yield {"conteudo": texto, "pagina_ini": min(paginas), "pagina_fim": max(paginas), "metadados": meta}
        cauda = _cauda(texto) if sobrepor else ""
        buffer, paginas, itens = ([cauda], paginas[-1:], []) if cauda else ([], [], [])

    for texto, p_ini, p_fim, membros in paragrafos(linhas):
        if not re.search(r"\w", texto):
            continue
        entrada = do_sumario.get(id(membros[0]))
        nivel = entrada["nivel"] if entrada else (nivel_titulo(texto) if len(membros) <= 2 else None)
        if nivel and not entrada and nivel == 1 and "capitulo" in normalizar(texto):
            # cabeçalho de página repetido ("Parte Primeira – Capítulo I"), não
            # um título novo: título de parte de verdade não cita "capítulo".
            # Sem isso, esse ruído corta o item numerado em andamento ao meio.
            nivel = None
        if nivel:
            titulo = entrada["titulo"] if entrada else texto
            yield from emitir()
            if titulo_anterior == 2 and nivel == 3 and len(normalizar(caminho.get(2, "")).split()) <= 3:
                caminho[2] = f"{caminho[2]} - {titulo}"  # "CAPÍTULO I" + "DE DEUS"
            else:
                caminho = {n: t for n, t in caminho.items() if n < nivel}
                caminho[nivel] = titulo
            item = None
            pendente_item = None
            titulo_anterior = nivel
            continue
        titulo_anterior = None

        sozinho = _ITEM_SOZINHO.match(texto)
        if sozinho:
            n = int(sozinho.group(1))
            if n == 1 or ultimo_item < n <= ultimo_item + 5:
                pendente_item = n
            continue  # "1." sozinho não carrega conteúdo; o número vale para o próximo parágrafo

        m = _ITEM.match(texto)
        n = pendente_item if pendente_item is not None else (int(m.group(1)) if m else None)
        pendente_item = None
        if n is not None:
            if n == 1 or ultimo_item < n <= ultimo_item + 5:
                # cada item numerado é a unidade citável (questão do LE, item do
                # ESE): fecha o chunk anterior sempre que um novo item começa,
                # em vez de esperar o buffer encher — senão várias perguntas
                # curtas acabam compartilhando um único embedding.
                if buffer:
                    yield from emitir()
                item = ultimo_item = n
        for pedaco in (_partir(texto) if len(texto) > MAXIMO else [texto]):
            if buffer and sum(map(len, buffer)) + len(pedaco) > MAXIMO:
                yield from emitir(sobrepor=item is None)
            buffer.append(pedaco)
            paginas += [p_ini, p_fim]
            if item is not None:
                itens.append(item)
            if item is None and sum(map(len, buffer)) >= ALVO:
                yield from emitir(sobrepor=True)
    yield from emitir()
