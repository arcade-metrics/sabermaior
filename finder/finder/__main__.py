"""Uso: python -m finder [termo] [opções]

Exemplos:
  python -m finder "evangelho"
  python -m finder "revista espirita" --fontes consolador --limite 3
  python -m finder kardec --listar
"""

import argparse
import sys
from pathlib import Path

import requests

from .acervo import Acervo, ErroDownload
from .auditoria import Busca
from .fontes import FONTES
from .rede import Bloqueado, Cliente


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m finder", description="Busca e baixa obras espíritas distribuídas gratuitamente pelas fontes.")
    p.add_argument("termo", nargs="?", default="", help="palavras a procurar no título, categoria ou nome do arquivo (vazio = tudo)")
    p.add_argument("--fontes", nargs="+", choices=list(FONTES), default=list(FONTES))
    p.add_argument("--listar", action="store_true", help="só lista o que encontrou, sem baixar")
    p.add_argument("--limite", type=int, default=0, help="máximo de PDFs baixados nesta busca (0 = sem limite)")
    p.add_argument("--dados", default=str(Path(__file__).resolve().parent.parent / "dados"), help="pasta do acervo")
    p.add_argument("--max-paginas", type=int, default=200, help="máximo de páginas HTML visitadas por fonte")
    p.add_argument("--intervalo", nargs=2, type=float, default=(3.0, 7.0), metavar=("MIN", "MAX"),
                   help="espera aleatória, em segundos, entre requisições ao mesmo site")
    p.add_argument("--sem-imagens", action="store_true", help="não extrai as imagens dos PDFs")
    p.add_argument("--sem-ip-publico", action="store_true", help="não consulta o IP público (api.ipify.org)")
    args = p.parse_args(argv)

    sys.stdout.reconfigure(errors="replace")
    log = lambda msg: print(msg, flush=True)

    cliente = Cliente(intervalo=tuple(args.intervalo))
    acervo = Acervo(args.dados)
    parametros = {k: v for k, v in vars(args).items() if k not in ("termo", "fontes")}
    busca = Busca(args.dados, args.termo, args.fontes, parametros, cliente.user_agent, not args.sem_ip_publico)
    log(f"Busca {busca.id}: termo={args.termo!r} fontes={', '.join(args.fontes)}")

    baixados = 0
    try:
        for nome in args.fontes:
            log(f"[{nome}]")
            try:
                for obra in FONTES[nome].buscar(cliente, args.termo, args.max_paginas, log):
                    existente = acervo.ja_tem(obra.url_pdf)
                    if args.listar:
                        busca.resultado(obra, "ja_no_acervo" if existente else "listado", existente)
                        log(f"  {'(no acervo) ' if existente else ''}{obra.titulo} <{obra.url_pdf}>")
                        continue
                    if existente:
                        busca.resultado(obra, "ja_no_acervo", existente)
                        log(f"  já no acervo: {existente['arquivo']}")
                        continue
                    if args.limite and baixados >= args.limite:
                        busca.resultado(obra, "nao_baixado_limite")
                        continue
                    try:
                        linha = acervo.baixar(cliente, obra, busca.id, imagens=not args.sem_imagens)
                    except Bloqueado:
                        raise
                    except (requests.RequestException, ErroDownload, OSError) as e:
                        busca.resultado(obra, "erro", erro=str(e))
                        log(f"  ERRO {obra.url_pdf}: {e}")
                        continue
                    baixados += 1
                    busca.resultado(obra, "baixado", linha)
                    log(f"  baixado: {linha['arquivo']} ({linha['bytes']} bytes, {linha['imagens'] or 0} imagens)")
            except Bloqueado as e:
                busca.erro_fonte(nome, str(e))
                log(f"  fonte interrompida: {e}")
    except KeyboardInterrupt:
        busca.erro_fonte("_", "interrompida pelo usuário")
        log("Interrompido; gravando o registro da busca.")
    finally:
        arquivo = busca.finalizar(cliente.requisicoes)
        r = busca.dados["resumo"]
        log(f"Fim: {r['encontrados']} encontrados, {r['baixados']} baixados, "
            f"{r['ja_no_acervo']} já no acervo, {r['erros']} erros. Registro: {arquivo}")


if __name__ == "__main__":
    main()
