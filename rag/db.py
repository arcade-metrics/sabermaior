import psycopg
from pgvector.psycopg import register_vector

from ia.config import RAIZ


def conectar(config):
    conn = psycopg.connect(config.database_url, autocommit=False, connect_timeout=10)
    register_vector(conn)
    return conn


def criar_esquema(config):
    """Aplica sql/*.sql em ordem (são idempotentes)."""
    with psycopg.connect(config.database_url, autocommit=True) as conn:
        for arquivo in sorted((RAIZ / "sql").glob("*.sql")):
            conn.execute(arquivo.read_text(encoding="utf-8"))
