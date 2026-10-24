"""espirita-rag: ingestão e consulta do acervo.

Exemplos:
  espirita-rag init-db
  espirita-rag ingest --filtro "livro dos espiritos" --limite 3
  espirita-rag ocultar
  espirita-rag parse-toc --file livro.pdf --output-manifest manifesto.json
  espirita-rag search "Que é Deus?"
  espirita-rag ask "Qual a diferença entre alma e Espírito?"
  espirita-rag eval
"""

import argparse
import dataclasses
import json
import sys
import time
from pathlib import Path

from ia import IA, carregar
from ia.config import RAIZ

from . import avaliacao, db, indexar, sumario
from .busca import buscar, referencia
from .extracao import extrair, normalizar
from .responder import responder

DADOS_PADRAO = RAIZ / "finder" / "dados"


def _ia(args):
    return IA(carregar(args.perfil))


def cmd_init_db(args):
    ia = _ia(args)
    db.criar_esquema(ia.config)
    print(f"Esquema aplicado em {ia.config.database_url.rsplit('@', 1)[-1]}")


def cmd_ingest(args):
    ia = _ia(args)
    dados = Path(args.dados)
    catalogo = indexar.ler_catalogo(dados)
    if args.arquivos:
        pdfs = [Path(a) for a in args.arquivos]
    else:
        pdfs = sorted((dados / "pdfs").rglob("*.pdf"))
    if args.filtro:
        termo = normalizar(args.filtro)
        pdfs = [p for p in pdfs if termo in normalizar(p.stem) or
                termo in normalizar(catalogo.get(p.relative_to(dados).as_posix(), {}).get("titulo", ""))]
    if args.limite:
        pdfs = pdfs[:args.limite]
    print(f"{len(pdfs)} PDFs; embeddings {ia.config.embed_model} em {ia.config.embed_base_url}", flush=True)
    total, inicio = 0, time.monotonic()
    excluidas = indexar.ler_excluidas()
    with db.conectar(ia.config) as conn:
        for i, pdf in enumerate(pdfs, 1):
            try:
                rel = pdf.resolve().relative_to(dados.resolve()).as_posix()
            except ValueError:
                rel = pdf.name
            print(f"[{i}/{len(pdfs)}] {rel}", flush=True)
            try:
                n = indexar.ingerir(pdf, catalogo.get(rel, {}), ia, conn, refazer=args.refazer,
                                    usar_llm=not args.sem_llm, excluidas=excluidas,
                                    log=lambda m: print(m, flush=True))
            except Exception as e:  # um PDF ruim não derruba o lote
                conn.rollback()
                print(f"  ERRO: {type(e).__name__}: {e}", flush=True)
                continue
            if n is None:
                continue
            if n == 0:
                print("  já indexado (use --refazer)", flush=True)
            total += n
        obras, trechos = indexar.aplicar_ocultas(conn)
    print(f"Fim: {total} chunks em {time.monotonic() - inicio:.0f}s; ocultas: {obras} obras ({trechos} trechos)")


def cmd_ocultar(args):
    ia = _ia(args)
    with db.conectar(ia.config) as conn:
        obras, trechos = indexar.aplicar_ocultas(conn)
        print(f"{obras} obras ocultas ({trechos} trechos), conforme {indexar.OCULTAS.name}:")
        for linha in conn.execute("SELECT fonte, manifesto->>'categoria', count(*) FROM obras WHERE oculta "
                                  "GROUP BY 1, 2 ORDER BY 1, 2"):
            print(f"  {linha[0]}/{linha[1]}: {linha[2]}")


def cmd_parse_toc(args):
    ia = None if args.sem_llm else _ia(args)
    caminho = Path(args.file)
    linhas = extrair(caminho)
    man, entradas, _ = indexar.manifesto(caminho, linhas, {}, ia, usar_llm=not args.sem_llm)
    man["livro_id"] = f"{indexar.slug(caminho.stem)}_{indexar.sha256(caminho)[:8]}"
    man["total_paginas"] = max((l.pagina for l in linhas), default=0)
    for e, s in zip(entradas, man["sumario"]):
        s["localizado"] = e.get("linha") is not None
    texto = json.dumps(man, ensure_ascii=False, indent=2)
    if args.output_manifest:
        Path(args.output_manifest).write_text(texto, encoding="utf-8")
        achados = sum(s["localizado"] for s in man["sumario"])
        print(f"{args.output_manifest}: sumário por {man['metodo_sumario']}, {len(entradas)} entradas, "
              f"{achados} localizadas no texto")
    else:
        print(texto)


def _filtros(args):
    return {"obra": args.obra, "idioma": args.idioma}


def cmd_search(args):
    ia = _ia(args)
    with db.conectar(ia.config) as conn:
        trechos = buscar(conn, ia, args.consulta, k=args.k, modo=args.modo, rerank=not args.sem_rerank,
                         **_filtros(args))
    for i, t in enumerate(trechos, 1):
        notas = " ".join(f"{c}={t[c]:.3f}" for c in ("rrf", "similaridade", "rank_texto", "rerank") if t.get(c))
        print(f"\n[{i}] {referencia(t)}\n    {t['id']}  {notas}")
        print("    " + t["conteudo"][:args.chars].replace("\n", "\n    "))


def cmd_ask(args):
    ia = _ia(args)
    if args.modelo:
        ia.config = dataclasses.replace(ia.config, llm_model=args.modelo)
    inicio = time.monotonic()
    with db.conectar(ia.config) as conn:
        r = responder(conn, ia, args.pergunta, k=args.k, pensar=args.pensar, **_filtros(args))
    print(r["resposta"])
    print("\nFontes:")
    for n in r["citados"]:
        t = r["trechos"][n - 1]
        print(f"  [{n}] {referencia(t)}  ({t['id']})")
    if r["invalidas"]:
        print(f"  ATENÇÃO: citações sem trecho correspondente: {r['invalidas']}")
    if not r["citados"]:
        print("  (a resposta não citou nenhum trecho)")
    print(f"\n{ia.config.llm_model}, {time.monotonic() - inicio:.1f}s")


def cmd_eval(args):
    ia = _ia(args)
    with db.conectar(ia.config) as conn:
        avaliacao.rodar(conn, ia, Path(args.arquivo), k=args.k, detalhar=args.detalhar)


def cmd_status(args):
    ia = _ia(args)
    print(ia.config)
    with db.conectar(ia.config) as conn:
        for linha in conn.execute("SELECT o.idioma, count(DISTINCT o.id), count(t.id) FROM obras o "
                                  "LEFT JOIN trechos t ON t.obra_id = o.id WHERE NOT o.oculta "
                                  "GROUP BY 1 ORDER BY 3 DESC"):
            print(f"  {linha[0]}: {linha[1]} obras, {linha[2]} trechos")
        obras, trechos = conn.execute("SELECT count(DISTINCT o.id), count(t.id) FROM obras o "
                                      "LEFT JOIN trechos t ON t.obra_id = o.id WHERE o.oculta").fetchone()
        print(f"  ocultas (rag/ocultas.csv): {obras} obras, {trechos} trechos")
        for linha in conn.execute("SELECT modelo_embedding, count(*) FROM trechos GROUP BY 1"):
            print(f"  modelo {linha[0]}: {linha[1]} trechos")


def main(argv=None):
    sys.stdout.reconfigure(errors="replace")
    p = argparse.ArgumentParser(prog="espirita-rag", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--perfil", help="dev ou prod (padrão: IA_PERFIL ou dev)")
    sub = p.add_subparsers(dest="comando", required=True)

    s = sub.add_parser("init-db", help="cria extensões, tabelas e índices")
    s.set_defaults(func=cmd_init_db)

    s = sub.add_parser("ingest", help="indexa os PDFs do acervo")
    s.add_argument("--dados", "--input-dir", default=str(DADOS_PADRAO), help="pasta com catalogo.csv e pdfs/")
    s.add_argument("--arquivos", nargs="+", help="PDFs específicos em vez da pasta toda")
    s.add_argument("--filtro", help="só PDFs cujo nome ou título contenha o termo")
    s.add_argument("--limite", type=int, default=0)
    s.add_argument("--refazer", action="store_true", help="reindexa mesmo se já estiver no banco")
    s.add_argument("--sem-llm", action="store_true", help="não usa a LLM para metadados e sumário")
    s.set_defaults(func=cmd_ingest)

    s = sub.add_parser("ocultar", help="aplica rag/ocultas.csv: obras indexadas que nenhuma consulta usa")
    s.set_defaults(func=cmd_ocultar)

    s = sub.add_parser("parse-toc", help="gera o manifesto (sumário localizado) de um PDF para revisão")
    s.add_argument("--file", required=True)
    s.add_argument("--output-manifest")
    s.add_argument("--sem-llm", action="store_true")
    s.set_defaults(func=cmd_parse_toc)

    for nome, func, ajuda in (("search", cmd_search, "mostra os trechos encontrados"),
                              ("ask", cmd_ask, "responde com citações")):
        s = sub.add_parser(nome, help=ajuda)
        s.add_argument("consulta" if nome == "search" else "pergunta")
        s.add_argument("-k", type=int, default=8)
        s.add_argument("--obra", help="id da obra ou parte do título")
        s.add_argument("--idioma", default="auto",
                       help="auto (idioma da pergunta), todos, ou pt, es, en, fr, eo")
        s.set_defaults(func=func)
    sub.choices["search"].add_argument("--modo", choices=["auto", "vetorial", "hibrida", "textual"], default="auto",
                                       help="auto: híbrida para palavras-chave, vetorial para perguntas")
    sub.choices["search"].add_argument("--sem-rerank", action="store_true")
    sub.choices["search"].add_argument("--chars", type=int, default=400, help="caracteres exibidos por trecho")
    sub.choices["ask"].add_argument("--pensar", action="store_true", help="liga o modo de raciocínio do modelo")
    sub.choices["ask"].add_argument("--modelo", help="modelo de chat (sobrepõe LLM_MODEL)")

    s = sub.add_parser("eval", help="recall@k do conjunto de perguntas de avaliação")
    s.add_argument("--arquivo", default=str(Path(__file__).with_name("avaliacao.jsonl")))
    s.add_argument("-k", type=int, default=10)
    s.add_argument("--detalhar", action="store_true", help="mostra a posição de cada pergunta")
    s.set_defaults(func=cmd_eval)

    s = sub.add_parser("status", help="configuração ativa e contagem do banco")
    s.set_defaults(func=cmd_status)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
