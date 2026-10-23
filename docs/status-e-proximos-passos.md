# sabermaior: status e próximos passos

Atualizado em 23/10/2026.

A Fase 1 do pipeline RAG está concluída: 432 obras e 100.099 trechos indexados em cinco idiomas, com
busca e resposta citada rodando localmente. Nada está em andamento; o que falta são as Fases 2 a 4, a
produção na VM e alguns pendentes de manutenção.

## Feito

| Componente | Onde | O que faz |
| --- | --- | --- |
| Coleta do acervo | `finder/` | Busca e baixa os PDFs (FEB, O Consolador, Luz Espírita) e monta o `catalogo.csv` |
| Camada de IA | `ia/` | Contrato compatível com OpenAI; `IA_PERFIL` troca dev (Ollama) por prod (vLLM, TEI ou API) sem mudar código; retentativas automáticas com espera de 5 a 90 s, inclusive para o esgotamento de portas do Ollama no Windows |
| Extração | `rag/extracao.py` | PyMuPDF; remove cabeçalho, rodapé e notas; desfaz hifenização; detecta o idioma |
| Sumário e metadados | `rag/sumario.py` | Marcadores do PDF, depois regex, depois LLM; título, autor, médium, tradutor e editora lidos pela LLM; manifesto em `obras.manifesto` |
| Chunking | `rag/chunking.py` | Corta em títulos e agrupa por questão ou item numerado; ~1.400 caracteres com ~250 de sobreposição na prosa |
| Banco | `sql/001_schema.sql` | Postgres 17 + pgvector; tabelas `obras` e `trechos`; índices HNSW (cosseno) e GIN (`tsvector`) |
| Busca | `rag/busca.py` | Vetorial, textual e híbrida (RRF); modo `auto` e filtro pelo idioma da pergunta; reranker pronto, desligado |
| Resposta | `rag/responder.py` | Gera com `qwen3:14b` (ou `gemma3:12b`) e valida que cada citação aponta para um trecho real |
| Avaliação | `rag/avaliacao.py` | R@1, R@5, R@10 e MRR sobre 27 consultas em `rag/avaliacao.jsonl` |
| CLI | `espirita-rag` | `init-db`, `ingest`, `parse-toc`, `search`, `ask`, `eval`, `status` |
| Infra | `infra/docker-compose.yml` | Postgres para dev; perfis `prod` (TEI de embeddings e reranker) e `gpu` (vLLM) já escritos |
| Versionamento | git | Primeiro commit e PR com o código; acervo (PDFs), banco e `.env.*` ficam fora do repositório |

Acervo no banco: pt 337 obras (59.407 trechos), es 31 (12.709), en 30 (10.687), fr 20 (12.975),
eo 14 (4.321), todos com `bge-m3`. O banco e os PDFs ficam só na máquina local; a VM recebe o banco
por `pg_dump`.

## Qualidade medida

O modo padrão (`auto`) acha a passagem esperada entre os 5 primeiros resultados em 85% das consultas
(MRR 0,59). Foram 27 consultas: 23 perguntas parafraseadas e 4 palavras-chave.

| Configuração | R@1 | R@5 | R@10 | MRR |
| --- | --- | --- | --- | --- |
| **auto: vetorial para perguntas, híbrida para palavras-chave (padrão)** | **0,41** | **0,85** | **0,89** | **0,59** |
| vetorial + reranker bge-reranker-v2-m3 | 0,44 | 0,67 | 0,74 | 0,53 |
| vetorial | 0,33 | 0,81 | 0,85 | 0,53 |
| híbrida RRF | 0,33 | 0,74 | 0,85 | 0,49 |
| vetorial, todos os idiomas | 0,30 | 0,70 | 0,81 | 0,46 |
| textual (`tsvector`) | 0,15 | 0,22 | 0,22 | 0,18 |

- O filtro de idioma é o maior ganho: sem ele, as traduções da mesma obra ocupam o topo.
- O reranker melhora o 1º lugar, mas piora o top 5, porque prefere apostilas que citam a passagem à
  obra original. Por isso está desligado.
- Geração: `qwen3:14b` responde em 2 a 6 s; `gemma3:12b` em ~7 s, com mais detalhe. Nos testes,
  nenhum dos dois citou trecho inexistente.
- O TEI em CPU (a opção de produção), testado localmente, dá os mesmos vetores do Ollama
  (cosseno 1,0000) e embeda uma pergunta em ~24 ms.

## A fazer

**Manutenção**

- [ ] Criar testes automatizados para extração, chunking e busca (hoje só existe o `eval`)
- [ ] Ampliar o conjunto de avaliação além das 27 consultas, incluindo perguntas em es, en, fr e eo
- [ ] Revisar por amostragem os manifestos de sumário (`parse-toc`) das obras principais

**Produção (VM)**

- [ ] Escolher a VM e decidir a geração: vLLM com GPU ou API hospedada
- [ ] Criar o `.env.prod` real a partir do `.env.prod.example` e trocar a senha do banco
- [ ] Levar o banco com `pg_dump` / `pg_restore` e subir o compose com `--profile prod`
- [ ] Rodar `espirita-rag eval` na VM e conferir que os números batem com os locais

**Interface**

- [ ] API HTTP para `search` e `ask` (hoje só há a CLI)
- [ ] Interface web simples para testar com usuários

**Fase 2: busca híbrida com BM25**

- [ ] Trocar o `ts_rank` por BM25 real (ParadeDB `pg_search`), para a híbrida servir também a perguntas
- [ ] Reavaliar o reranker depois do BM25, ou rebaixar apostilas que citam a obra original

**Fase 3: grafo de conhecimento**

- [ ] Escolher Neo4j ou PostgreSQL AGE
- [ ] Definir a ontologia (Espírito, perispírito, reencarnação, causa e efeito) e ligar passagens
      entre obras e autores

**Fase 4: agentes**

- [ ] Agentes Histórico, Doutrinário e de Citação, com checagem de fontes
- [ ] Orquestração entre eles sobre a camada `ia/`

Pergunta em aberto: a ordem entre produção, interface e Fase 2 ainda não foi decidida.
