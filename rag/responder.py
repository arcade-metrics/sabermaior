"""Resposta com citação: a LLM recebe os trechos numerados e precisa citar
[n] em cada afirmação; citações para números inexistentes são apontadas."""

import re

from .busca import buscar, referencia

SISTEMA = """Você é um assistente de estudo da literatura espírita.
Responda SOMENTE com base nos trechos fornecidos, no idioma da pergunta.
Cite a fonte de cada afirmação com o número do trecho entre colchetes, ex.: [2] ou [1][3].
Quando citar uma frase literal, use aspas. Não invente obras, autores, números de questão ou páginas.
Se os trechos não bastarem para responder, diga isso claramente e indique o que encontrou de mais próximo."""


def contexto(trechos):
    blocos = []
    for i, t in enumerate(trechos, 1):
        autoria = " / ".join(x for x in (t.get("autor_espiritual"), t.get("autor")) if x)
        blocos.append(f"[{i}] {referencia(t)}" + (f" ({autoria})" if autoria else "") + f"\n{t['conteudo']}")
    return "\n\n".join(blocos)


def responder(conn, ia, pergunta, k=8, pensar=False, sistema=SISTEMA, **filtros):
    trechos = buscar(conn, ia, pergunta, k=k, **filtros)
    if not trechos:
        return {"resposta": "Nenhum trecho encontrado no acervo para essa pergunta.", "trechos": [], "citados": [],
                "invalidas": []}
    texto = ia.chat([
        {"role": "system", "content": sistema},
        {"role": "user", "content": f"Trechos:\n\n{contexto(trechos)}\n\nPergunta: {pergunta}"},
    ], temperatura=0.2, raciocinio=None if pensar else "none")
    numeros = sorted({int(n) for n in re.findall(r"\[(\d+)\]", texto)})
    return {
        "resposta": texto,
        "trechos": trechos,
        "citados": [n for n in numeros if 1 <= n <= len(trechos)],
        "invalidas": [n for n in numeros if not 1 <= n <= len(trechos)],
    }
