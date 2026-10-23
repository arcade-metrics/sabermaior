-- Esquema do acervo vetorizado. Roda sozinho na primeira subida do container
-- (docker-entrypoint-initdb.d) e pode ser reaplicado: python -m rag init-db

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- unaccent não é IMMUTABLE; o invólucro permite usá-lo em coluna gerada e índice.
CREATE OR REPLACE FUNCTION f_unaccent(text) RETURNS text
    LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
    AS $$ SELECT public.unaccent('public.unaccent'::regdictionary, $1) $$;

-- Documento agregador (manifesto da obra): metadados e sumário localizado.
CREATE TABLE IF NOT EXISTS obras (
    id          text PRIMARY KEY,
    sha256      text UNIQUE NOT NULL,
    titulo      text NOT NULL,
    autor       text,
    fonte       text,
    arquivo     text NOT NULL,
    idioma      text,
    paginas     integer,
    manifesto   jsonb NOT NULL DEFAULT '{}',
    ingerido_em timestamptz NOT NULL DEFAULT now()
);

-- Um trecho por chunk. O modelo de embedding fica gravado: buscar com outro
-- modelo dá vetores incompatíveis, então trocar de modelo exige reindexar.
CREATE TABLE IF NOT EXISTS trechos (
    id               text PRIMARY KEY,
    obra_id          text NOT NULL REFERENCES obras(id) ON DELETE CASCADE,
    ordem            integer NOT NULL,
    conteudo         text NOT NULL,
    metadados        jsonb NOT NULL,
    pagina_ini       integer,
    pagina_fim       integer,
    idioma           text,
    fts_cfg          regconfig NOT NULL DEFAULT 'simple',
    modelo_embedding text NOT NULL,
    embedding        vector(1024) NOT NULL,
    tsv              tsvector GENERATED ALWAYS AS (to_tsvector(fts_cfg, f_unaccent(conteudo))) STORED
);

CREATE INDEX IF NOT EXISTS trechos_obra_idx ON trechos (obra_id, ordem);
CREATE INDEX IF NOT EXISTS trechos_tsv_idx ON trechos USING gin (tsv);
CREATE INDEX IF NOT EXISTS trechos_embedding_idx ON trechos USING hnsw (embedding vector_cosine_ops);
