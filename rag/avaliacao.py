"""Avaliação da busca: cada linha de avaliacao.jsonl traz uma pergunta, a obra
esperada (parte do título) e um trecho de texto que precisa aparecer no
chunk recuperado. Mede recall@1/5/k e MRR por configuração de busca."""

import json

from .busca import buscar
from .extracao import normalizar


def _acertou(trecho, caso):
    if caso.get("obra") and normalizar(caso["obra"]) not in normalizar(trecho["titulo"]):
        return False
    return normalizar(caso["esperado"]) in normalizar(trecho["conteudo"])


def rodar(conn, ia, arquivo, k=10, detalhar=False):
    casos = [json.loads(l) for l in arquivo.read_text(encoding="utf-8").splitlines() if l.strip()]
    # (nome, modo, peso do texto na fusão, rerank, idioma)
    configuracoes = [("auto (padrão)", "auto", 1.0, False, "auto"), ("vetorial todos", "vetorial", 1.0, False, "todos"),
                     ("vetorial", "vetorial", 1.0, False, "auto"), ("textual", "textual", 1.0, False, "auto"),
                     ("hibrida", "hibrida", 1.0, False, "auto"), ("hibrida t=0.5", "hibrida", 0.5, False, "auto")]
    if ia.config.rerank_provider != "none":
        configuracoes += [("vetorial+rerank", "vetorial", 1.0, True, "auto"),
                          ("hibrida+rerank", "hibrida", 1.0, True, "auto")]

    print(f"{len(casos)} perguntas, k={k}, embeddings {ia.config.embed_model}, rerank {ia.config.rerank_provider}\n")
    print(f"{'configuração':<16} {'R@1':>6} {'R@5':>6} {f'R@{k}':>6} {'MRR':>6}")
    for nome, modo, peso, rerank, idioma in configuracoes:
        posicoes = []
        for caso in casos:
            trechos = buscar(conn, ia, caso["pergunta"], k=k, modo=modo, rerank=rerank, peso_texto=peso,
                             idioma=idioma)
            pos = next((i for i, t in enumerate(trechos, 1) if _acertou(t, caso)), None)
            posicoes.append(pos)
            if detalhar:
                print(f"  {nome:<14} {str(pos or '-'):>3}  {caso['pergunta']}")
        n = len(casos)
        r = lambda limite: sum(1 for p in posicoes if p and p <= limite) / n
        mrr = sum(1 / p for p in posicoes if p) / n
        print(f"{nome:<16} {r(1):>6.2f} {r(5):>6.2f} {r(k):>6.2f} {mrr:>6.2f}")
