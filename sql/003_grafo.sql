-- Fase 3: grafo de conhecimento, modelado como tabelas simples em vez de
-- Apache AGE. Motivo: AGE exige compilar a extensão contra o build exato do
-- Postgres da imagem paradedb/paradedb (sem fonte/toolchain nela), o que é
-- arriscado para uma imagem já em uso; tabelas dão a mesma coisa (nós +
-- arestas tipadas, sem duplicar obras/trechos) sem mexer na infra atual.
-- Ver docs/proposta-ontologia-fase3.md.

-- Hierarquia categoria > subcategoria > termo (AMPLIA/RESTRINGE) via
-- categoria_pai_id; nível 1 não tem pai.
CREATE TABLE IF NOT EXISTS conceitos (
    id              text PRIMARY KEY,
    nome            text NOT NULL,
    nivel           integer NOT NULL CHECK (nivel IN (1, 2, 3)),
    categoria_pai_id text REFERENCES conceitos(id) ON DELETE CASCADE,
    obra_origem     text,
    fonte           text NOT NULL DEFAULT 'ragacini_2017'
);

CREATE INDEX IF NOT EXISTS conceitos_pai_idx ON conceitos (categoria_pai_id);

-- Termos não preferidos (USE/UP do tesauro original) -> SINONIMO_DE.
CREATE TABLE IF NOT EXISTS conceito_sinonimos (
    conceito_id text NOT NULL REFERENCES conceitos(id) ON DELETE CASCADE,
    sinonimo    text NOT NULL,
    PRIMARY KEY (conceito_id, sinonimo)
);

-- MENCIONA / DEFINIDO_EM: liga um conceito a trechos do acervo (Fase 1/2).
CREATE TABLE IF NOT EXISTS conceito_trechos (
    conceito_id text NOT NULL REFERENCES conceitos(id) ON DELETE CASCADE,
    trecho_id   text NOT NULL REFERENCES trechos(id) ON DELETE CASCADE,
    tipo        text NOT NULL DEFAULT 'MENCIONA' CHECK (tipo IN ('DEFINIDO_EM', 'MENCIONA')),
    rank_texto  real,
    PRIMARY KEY (conceito_id, trecho_id)
);

CREATE INDEX IF NOT EXISTS conceito_trechos_trecho_idx ON conceito_trechos (trecho_id);
