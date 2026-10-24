-- Fase 2: BM25 real (ParadeDB pg_search) no lugar do ts_rank/tsvector.
-- Exige a imagem paradedb/paradedb (infra/docker-compose.yml) com
-- shared_preload_libraries=pg_search.

CREATE EXTENSION IF NOT EXISTS pg_search;

-- Mesmo texto do tsv antigo (sem acento), para casar consulta sem acento
-- com texto acentuado: o tokenizer icu do pg_search não remove acento.
ALTER TABLE trechos ADD COLUMN IF NOT EXISTS conteudo_simples text
    GENERATED ALWAYS AS (f_unaccent(conteudo)) STORED;

-- Um índice BM25 por tabela; "icu" tokeniza por palavra em qualquer idioma,
-- "stemmer: Portuguese" cobre o grosso do acervo (pt-BR é a prioridade).
CREATE INDEX IF NOT EXISTS trechos_bm25_idx ON trechos
    USING bm25 (id, conteudo_simples)
    WITH (text_fields = '{"conteudo_simples": {"tokenizer": {"type": "icu", "stemmer": "Portuguese"}}}');
