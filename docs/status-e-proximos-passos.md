# sabermaior: status e próximos passos

Atualizado em 23/10/2026.

A Fase 1 do pipeline RAG está concluída: 342 obras e 53.395 trechos indexados, 319 delas em pt-BR, com
busca e resposta citada rodando localmente. O acervo pt-BR também já foi limpo de duplicatas (72
traduções e 18 edições repetidas), um bug real no `chunking` das edições da FEB foi corrigido, e a
Fase 2 (BM25 real com ParadeDB `pg_search`) já está rodando. Falta decidir entre Produção, Interface
e Fase 3 como próximo passo.

## Feito

| Componente | Onde | O que faz |
| --- | --- | --- |
| Coleta do acervo | `finder/` | Busca e baixa os PDFs (FEB, O Consolador, Luz Espírita) e monta o `catalogo.csv` |
| Camada de IA | `ia/` | Contrato compatível com OpenAI; `IA_PERFIL` troca dev (Ollama) por prod (vLLM, TEI ou API) sem mudar código; retentativas automáticas com espera de 5 a 90 s, inclusive para o esgotamento de portas do Ollama no Windows |
| Extração | `rag/extracao.py` | PyMuPDF; remove cabeçalho, rodapé e notas; desfaz hifenização; detecta o idioma |
| Sumário e metadados | `rag/sumario.py` | Marcadores do PDF, depois regex, depois LLM; título, autor, médium, tradutor e editora lidos pela LLM; manifesto em `obras.manifesto` |
| Chunking | `rag/chunking.py` | Corta em títulos e agrupa por questão ou item numerado; ~1.400 caracteres com ~250 de sobreposição na prosa |
| Banco | `sql/001_schema.sql`, `sql/002_bm25.sql` | Postgres 17 (imagem `paradedb/paradedb`) + pgvector + pg_search; tabelas `obras` e `trechos`; índices HNSW (cosseno) e BM25 (`pg_search`) |
| Busca | `rag/busca.py` | Vetorial, textual (BM25 real) e híbrida (RRF); modo `auto` e filtro pelo idioma da pergunta; reranker pronto, desligado |
| Resposta | `rag/responder.py` | Gera com `qwen3:14b` (ou `gemma3:12b`) e valida que cada citação aponta para um trecho real |
| Avaliação | `rag/avaliacao.py` | R@1, R@5, R@10 e MRR sobre 27 consultas em `rag/avaliacao.jsonl` |
| CLI | `espirita-rag` | `init-db`, `ingest`, `parse-toc`, `search`, `ask`, `eval`, `status` |
| Infra | `infra/docker-compose.yml` | Postgres para dev; perfis `prod` (TEI de embeddings e reranker) e `gpu` (vLLM) já escritos |
| Versionamento | git | Primeiro commit e PR com o código; acervo (PDFs), banco e `.env.*` ficam fora do repositório |

Acervo no banco: pt 319 obras (49.065 trechos), es 9 (2.308), en 11 (1.925), fr 1 (90), eo 2 (7),
todos com `bge-m3`. A prioridade é pt-BR: foram retiradas 72 traduções de obras que já existem em pt
e 18 duplicatas dentro do próprio pt (edições repetidas dos clássicos de Kardec e da Revista
Espírita, e dois PDFs da FEB com conteúdo idêntico sob nomes diferentes). Tudo isso está listado em
`rag/excluidas.csv`, com o motivo e a obra que ficou; o `ingest` pula esses PDFs automaticamente. O banco e os PDFs ficam só na máquina local; a VM recebe o banco
por `pg_dump`.

## Qualidade medida

Depois de retirar as duplicatas em pt, o `eval` caiu: o modo padrão (`auto`) foi de R@5 0,88 (com as
duplicatas no banco) para 0,64. Duas causas, investigadas e resolvidas na medida do possível:

1. **Bug de chunking, corrigido.** Nas edições "WEB" da FEB, o número da pergunta vinha num
   parágrafo isolado do PDF ("1." numa linha, "Que é Deus?" na seguinte), e cabeçalhos de página
   repetidos ("Parte Primeira – Capítulo I") às vezes cortavam uma pergunta ao meio. O Livro dos
   Espíritos, por exemplo, só tinha 1% dos trechos marcados com o número da questão (deveria ser
   quase 100%). Corrigido em `rag/chunking.py`; os 7 livros clássicos e os 9 anos da Revista
   Espírita foram reingeridos. Resultado: cada trecho citável agora é exatamente um item (confirmado
   item a item), R@1 subiu de 0,28 para 0,32 e o MRR de 0,42 para 0,45 — mas o R@5 não mudou.
2. **Perda da redundância das duplicatas, sem solução — é o preço esperado da limpeza.** Com duas
   edições do mesmo livro, uma pergunta tinha duas chances de acertar; com uma só, uma chance. Em
   perguntas mais genéricas (definição de Deus, livre-arbítrio), apostilas e cursos da FEB disputam
   o mesmo espaço vetorial e às vezes ficam à frente do Livro dos Espíritos.

Depois disso veio a Fase 2 (BM25 real, ver abaixo), que não resolve esse segundo ponto — ele não
está mais bloqueando nada, só não tem solução dentro do próprio pipeline de busca.

| Configuração | R@1 | R@5 | R@10 | MRR |
| --- | --- | --- | --- | --- |
| **auto: vetorial para perguntas, híbrida para palavras-chave (padrão)** | **0,28** | **0,60** | **0,76** | **0,41** |
| vetorial | 0,24 | 0,56 | 0,72 | 0,37 |
| híbrida RRF (BM25 completo) | 0,24 | 0,56 | 0,72 | 0,36 |
| vetorial, todos os idiomas | 0,24 | 0,48 | 0,72 | 0,35 |
| textual (BM25, ParadeDB `pg_search`) | 0,12 | 0,16 | 0,20 | 0,15 |

Conferi manualmente: a frase esperada aparece, literal, na edição da FEB mantida — ela só não entra
no top 5 para certas perguntas. O BM25 não resgatou essas perguntas genéricas (não são palavras
raras, é concorrência semântica mesmo), mas acerta bem as 4 perguntas de palavra-chave do conjunto
(posição 1 ou 2, igual ou melhor que o `ts_rank` antigo) — que é o caso de uso real da busca textual.

**Achado da Fase 2:** com BM25 de verdade, a híbrida deixou de piorar perguntas em linguagem natural —
empata com o vetorial puro (R@5 0,56 nas duas), em vez de ficar visivelmente atrás como acontecia
com `ts_rank`. Ainda não é evidência suficiente (25 perguntas) para trocar o `auto` por "híbrida
sempre", mas vale reavaliar quando o conjunto de avaliação crescer (ver "A fazer").

O reranker bge-reranker-v2-m3 foi medido antes de toda a limpeza (27 consultas, com traduções e
duplicatas): melhora o 1º lugar, mas piora o top 5 (R@5 0,67 contra 0,85 do `auto` na mesma base),
porque prefere apostilas que citam a passagem à obra original. Por isso está desligado.
- Geração: `qwen3:14b` responde em 2 a 6 s; `gemma3:12b` em ~7 s, com mais detalhe. Nos testes,
  nenhum dos dois citou trecho inexistente.
- O TEI em CPU (a opção de produção), testado localmente, dá os mesmos vetores do Ollama
  (cosseno 1,0000) e embeda uma pergunta em ~24 ms.

## A fazer

**Manutenção**

- [ ] Criar testes automatizados para extração, chunking e busca (hoje só existe o `eval`)
- [ ] Ampliar o conjunto de avaliação além das 25 consultas, em pt-BR
- [ ] Revisar por amostragem os manifestos de sumário (`parse-toc`) das obras principais
- [ ] "Espíritos Diversos" aparece como título de 4 obras do Chico Xavier (`luznolar.pdf`,
      `poetasredivivos.pdf`, `falandoaterra.pdf`, `maosmarcadas.pdf`): é o nome do autor espiritual,
      não o título real; são livros diferentes, não duplicatas, mas o metadado está errado
- [ ] Reingerir o resto do acervo com o chunking corrigido (só os 7 clássicos + 9 anos da Revista
      Espírita foram reingeridos; o bug pode afetar outros PDFs em layout parecido, ex.: `Estudo
      Aprofundado da Doutrina Espírita`, `Programa Fundamental`)
- [ ] Remover `trechos.tsv`/`fts_cfg`/`trechos_tsv_idx` e `CONFIG_FTS` (ficaram sem uso depois do
      BM25 — `rag/indexar.py` ainda grava `fts_cfg`, mas nada mais lê)
- [ ] Com mais perguntas no `eval`, testar se vale trocar `auto` por "híbrida sempre" (ver achado em
      "Qualidade medida")

**Fase 2: busca híbrida com BM25 — concluída**

- [x] Trocar o `ts_rank` por BM25 real (ParadeDB `pg_search`): imagem `paradedb/paradedb:0.26.3-pg17`,
      `sql/002_bm25.sql`, `rag/busca.py` usa `paradedb.match(conjunction_mode => true)`
- [ ] Reavaliar o reranker agora com BM25, ou rebaixar apostilas que citam a obra original

**Interface — próximo passo**

- [ ] API HTTP para `search` e `ask` (hoje só há a CLI)
- [ ] Interface web simples para testar com usuários

**Fase 3: grafo de conhecimento**

- [ ] Escolher Neo4j ou PostgreSQL AGE
- [ ] Definir a ontologia (Espírito, perispírito, reencarnação, causa e efeito) e ligar passagens
      entre obras e autores

**Fase 4: agentes**

- [ ] Agentes Histórico, Doutrinário e de Citação, com checagem de fontes
- [ ] Orquestração entre eles sobre a camada `ia/`

**Produção (VM) — fica para depois da Interface e da Fase 3**

- [ ] Escolher a VM e decidir a geração: vLLM com GPU ou API hospedada
- [ ] Criar o `.env.prod` real a partir do `.env.prod.example` e trocar a senha do banco
- [ ] Levar o banco com `pg_dump` / `pg_restore` e subir o compose com `--profile prod`
- [ ] Rodar `espirita-rag eval` na VM e conferir que os números batem com os locais
