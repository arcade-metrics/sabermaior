"""Agente de Citação: não responde pergunta nenhuma, só audita a resposta
de outro agente. Toda frase entre aspas na resposta precisa aparecer,
literalmente (sem acento, sem variar espaços), em algum trecho citado —
caso contrário é uma citação fabricada e entra em "não confirmadas"."""

import re
import unicodedata

_ASPAS = re.compile(r"[\"“]([^\"”]{8,400})[\"”]")


def _normalizar(texto):
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem_acento).lower().strip()


def verificar(resposta, trechos, citados):
    """citados: números [n] que a resposta já citou (de responder()).
    Retorna a lista de citações literais (entre aspas) que não batem com
    nenhum trecho citado."""
    textos_citados = [_normalizar(trechos[n - 1]["conteudo"]) for n in citados if 1 <= n <= len(trechos)]
    nao_confirmadas = []
    for citacao in _ASPAS.findall(resposta):
        alvo = _normalizar(citacao)
        if not any(alvo in texto for texto in textos_citados):
            nao_confirmadas.append(citacao.strip())
    return nao_confirmadas
