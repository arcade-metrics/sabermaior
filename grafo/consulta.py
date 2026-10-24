"""Povoamento e consulta do grafo (sql/003_grafo.sql), a partir de
grafo.sementes.CATEGORIAS."""

import re
import unicodedata

from .sementes import CATEGORIAS


def slug(nome):
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", sem_acento.lower()).strip("_")


def _inserir(conn, id_, nome, nivel, pai_id, obra, sinonimos):
    conn.execute(
        "INSERT INTO conceitos (id, nome, nivel, categoria_pai_id, obra_origem) VALUES (%s, %s, %s, %s, %s) "
        "ON CONFLICT (id) DO UPDATE SET nome = EXCLUDED.nome, obra_origem = EXCLUDED.obra_origem",
        (id_, nome, nivel, pai_id, obra),
    )
    for sinonimo in sinonimos or []:
        conn.execute(
            "INSERT INTO conceito_sinonimos (conceito_id, sinonimo) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (id_, sinonimo),
        )


def povoar(conn):
    """Insere a taxonomia semente (idempotente). Retorna o nº de conceitos inseridos."""
    total = 0
    for categoria in CATEGORIAS:
        cat_id = slug(categoria["nome"])
        _inserir(conn, cat_id, categoria["nome"], 1, None, categoria.get("obra"), categoria.get("sinonimos"))
        total += 1
        for sub in categoria["subcategorias"]:
            sub_id = f"{cat_id}__{slug(sub['nome'])}"
            _inserir(conn, sub_id, sub["nome"], 2, cat_id, categoria.get("obra"), sub.get("sinonimos"))
            total += 1
            for termo in sub["termos"]:
                termo_id = f"{sub_id}__{slug(termo)}"
                _inserir(conn, termo_id, termo, 3, sub_id, categoria.get("obra"), None)
                total += 1
    conn.commit()
    return total


def ligar_trechos(conn, limite_por_conceito=3, log=None):
    """Para cada conceito, busca trechos que mencionam seu nome (BM25/pg_search,
    OR entre palavras) e grava em conceito_trechos. Determinístico, sem LLM;
    refinar com extração assistida fica para depois (ver seção 6 do doc)."""
    with conn.cursor() as cur:
        cur.execute("SELECT id, nome FROM conceitos ORDER BY nivel, id")
        conceitos = cur.fetchall()
    total = 0
    for conceito_id, nome in conceitos:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM conceito_trechos WHERE conceito_id = %(id)s",
                {"id": conceito_id},
            )
            cur.execute(
                """
                SELECT t.id, paradedb.score(t.id) AS rank_texto
                FROM trechos t JOIN obras o ON o.id = t.obra_id
                WHERE t.conteudo_simples @@@ paradedb.match('conteudo_simples', f_unaccent(%(nome)s),
                                                              conjunction_mode => false)
                  AND NOT o.oculta
                ORDER BY rank_texto DESC LIMIT %(n)s
                """,
                {"nome": nome, "n": limite_por_conceito},
            )
            encontrados = cur.fetchall()
            for trecho_id, rank in encontrados:
                cur.execute(
                    "INSERT INTO conceito_trechos (conceito_id, trecho_id, tipo, rank_texto) "
                    "VALUES (%s, %s, 'MENCIONA', %s) ON CONFLICT DO NOTHING",
                    (conceito_id, trecho_id, rank),
                )
            total += len(encontrados)
        conn.commit()
        if log:
            log(f"{nome}: {len(encontrados)} trecho(s)")
    return total


def listar_categorias(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT id, nome, obra_origem FROM conceitos WHERE nivel = 1 ORDER BY nome")
        return [{"id": i, "nome": n, "obra": o} for i, n, o in cur.fetchall()]


def _trechos_do_conceito(cur, conceito_id):
    cur.execute(
        """
        SELECT t.id, t.conteudo, t.pagina_ini, t.pagina_fim, o.titulo, ct.tipo
        FROM conceito_trechos ct JOIN trechos t ON t.id = ct.trecho_id JOIN obras o ON o.id = t.obra_id
        WHERE ct.conceito_id = %(id)s AND NOT o.oculta ORDER BY ct.rank_texto DESC NULLS LAST
        """,
        {"id": conceito_id},
    )
    return [
        {"id": tid, "titulo": titulo, "trecho": conteudo[:300], "pagina": p_ini, "tipo": tipo}
        for tid, conteudo, p_ini, p_fim, titulo, tipo in cur.fetchall()
    ]


def conceito(conn, id_ou_nome):
    """Nó + pai + filhos + sinônimos + trechos ligados. None se não achar."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, nome, nivel, categoria_pai_id, obra_origem FROM conceitos "
            "WHERE id = %(q)s OR nome ILIKE %(q)s LIMIT 1",
            {"q": id_ou_nome},
        )
        linha = cur.fetchone()
        if not linha:
            return None
        id_, nome, nivel, pai_id, obra = linha

        pai = None
        if pai_id:
            cur.execute("SELECT id, nome FROM conceitos WHERE id = %s", (pai_id,))
            r = cur.fetchone()
            pai = {"id": r[0], "nome": r[1]} if r else None

        cur.execute(
            "SELECT id, nome FROM conceitos WHERE categoria_pai_id = %s ORDER BY nome", (id_,),
        )
        filhos = [{"id": i, "nome": n} for i, n in cur.fetchall()]

        cur.execute("SELECT sinonimo FROM conceito_sinonimos WHERE conceito_id = %s", (id_,))
        sinonimos = [s for (s,) in cur.fetchall()]

        trechos = _trechos_do_conceito(cur, id_)

    return {
        "id": id_, "nome": nome, "nivel": nivel, "obra_origem": obra,
        "pai": pai, "filhos": filhos, "sinonimos": sinonimos, "trechos": trechos,
    }
