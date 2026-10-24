-- Obras ocultas: continuam indexadas, mas nenhuma consulta (busca, respostas,
-- agentes, grafo) as usa. Quem fica oculto vem de rag/ocultas.csv, aplicado
-- por `espirita-rag ocultar` (e ao fim de cada `ingest`).

ALTER TABLE obras ADD COLUMN IF NOT EXISTS oculta boolean NOT NULL DEFAULT false;
