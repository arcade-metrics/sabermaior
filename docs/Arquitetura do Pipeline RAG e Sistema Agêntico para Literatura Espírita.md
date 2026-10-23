# **Arquitetura do Pipeline RAG e Sistema Agêntico para Literatura Espírita**

## **1\. Visão Geral do Sistema**

Este documento detalha a arquitetura de dados e o pipeline técnico para ingestão, processamento, vetorização e consulta da literatura espírita. O sistema foi projetado de forma modular e independente de projetos específicos, visando execução local via linha de comando, armazenamento inicial em banco PostgreSQL local com a extensão pgvector e suporte para evolução futura com Busca Híbrida, Grafos de Conhecimento e Ontologias.

## **2\. Fluxo da Arquitetura de Dados (Pipeline RAG)**

| Etapa | Módulo / Tecnologia | Descrição das Operações   |
| :---- | :---- | :---- |
| **1\. Parsing e Extração** | pdfplumber / PyPDF2 | Extração bruta do texto dos PDFs, remoção automática de cabeçalhos, rodapés e junção de palavras divididas por quebra de linha. |
| **2\. Análise Estrutural** | TOC Parser Engine | Mapeamento do sumário (TOC) para criação do documento agregador de metadados e delimitação das seções do livro. |
| **3\. Chunking Inteligente** | Recursive Character Splitter | Divisão hierárquica do texto por seções/capítulos preservando contexto com sobreposição (*overlap*). |
| **4\. Vetorização Local** | Ollama (mxbai-embed-large / bge-m3) | Geração dos embeddings de forma 100% offline em ambiente local. |
| **5\. Armazenamento** | PostgreSQL \+ pgvector | Persistência dos vetores e metadados estruturados em banco relacional local. |

## **3\. Organização do Livro, Sumário e Documento Agregador**

Para garantir que cada trecho guarde a noção exata de onde foi retirado na obra, o processo utiliza uma abordagem em duas fases:

### **A. Mapeamento Automático do Sumário**

O script analisa as primeiras páginas do PDF para extrair a estrutura do sumário utilizando padrões de expressão regular e análise de formatação (índices, números de capítulo e títulos). Caso o PDF não possua um sumário marcado eletronicamente, o sistema gera o **Documento Agregador (Manifesto da Obra)**.

### **B. Estrutura do Documento Agregador (JSON)**

`{`  
  `"livro_id": "kardec_livro_dos_espiritos_1857",`  
  `"titulo": "O Livro dos Espíritos",`  
  `"autor": "Allan Kardec",`  
  `"editora": "FEB",`  
  `"total_paginas": 480,`  
  `"estrutura_sumario": [`  
    `{`  
      `"parte": "Parte Primeira - As Causas Primeiras",`  
      `"capitulos": [`  
        `{`  
          `"capitulo_numero": 1,`  
          `"titulo": "De Deus",`  
          `"itens_ou_questoes": ["1 a 16"],`  
          `"pagina_inicio": 15,`  
          `"pagina_fim": 32`  
        `}`  
      `]`  
    `}`  
  `]`  
`}`

### **C. Estrutura do Chunk Herdando Metadados**

Ao realizar o *chunking*, o sistema associa cada bloco ao nó correspondente do Documento Agregador:  
`{`  
  `"chunk_id": "kardec_le_cap1_q1_01",`  
  `"livro_id": "kardec_livro_dos_espiritos_1857",`  
  `"conteudo": "1. Que é Deus? — 'Deus é a inteligência suprema, causa primeira de todas as coisas.'",`  
  `"metadados": {`  
    `"autor": "Allan Kardec",`  
    `"livro": "O Livro dos Espíritos",`  
    `"parte": "Parte Primeira - As Causas Primeiras",`  
    `"capitulo": "Capítulo I - De Deus",`  
    `"questao": 1,`  
    `"pagina": 15`  
  `}`  
`}`

## **4\. Instalação e Execução Global Offline (Cli Tool)**

O utilitário de ingestão é empacotado como uma ferramenta global de linha de comando em Python (instalável via pip install \-e . ou pipx). Isso permite executar a ingestão a partir de qualquer pasta do sistema operacional sem acoplar o código ao repositório da aplicação principal.

### **Comando de Execução Global:**

`# Ingestão de pasta inteira de PDFs para o PostgreSQL local`  
`espirita-rag ingest --input-dir /caminho/para/pdfs/ --db-url postgresql://postgres:senha@localhost:5432/espirita_db`

`# Processamento individual com inspeção do sumário`  
`espirita-rag parse-toc --file /caminho/para/livro.pdf --output-manifest manifesto.json`

## **5\. Banco de Dados Local (PostgreSQL \+ pgvector)**

Configuração para execução em ambiente de desenvolvimento local utilizando Docker ou instalação nativa do PostgreSQL com suporte vetorial.

### **Estrutura de Tabela (SQL):**

`CREATE EXTENSION IF NOT EXISTS vector;`

`CREATE TABLE documentos_agregadores (`  
    `id VARCHAR(100) PRIMARY KEY,`  
    `titulo TEXT NOT NULL,`  
    `autor VARCHAR(250),`  
    `metadados JSONB,`  
    `criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP`  
`);`

`CREATE TABLE embeddings_literatura (`  
    `id VARCHAR(100) PRIMARY KEY,`  
    `documento_id VARCHAR(100) REFERENCES documentos_agregadores(id),`  
    `conteudo TEXT NOT NULL,`  
    `metadados JSONB NOT NULL,`  
    `embedding VECTOR(1024) -- Dimensão conforme o modelo local (ex: mxbai-embed-large / bge-m3)`  
`);`

`-- Índice HNSW para busca vetorial rápida em escala`  
`CREATE INDEX ON embeddings_literatura USING hnsw (embedding vector_cosine_ops);`

## **6\. Roteiro de Evolução Futura (Fase Agêntica e Ontologias)**

> * **Fase 1 (Atual):** Extração em lote, mapeamento estruturado de sumário, geração de embeddings locais (via Ollama) e armazenamento no PostgreSQL (pgvector).  
> * **Fase 2 (Busca Híbrida \+ Re-ranking):** Integração de busca vetorial semântica combinada com busca por texto completo (Full-Text Search BM25 do PostgreSQL) e reordenamento de contexto.  
> * **Fase 3 (Grafos de Conhecimento & Ontologias):** Construção de um Grafo de Conhecimento (Neo4j ou PostgreSQL AGE) conectando entidades como *Espírito, Perispírito, Reencarnação, Causa/Efeito* e relacionando passagens entre diferentes obras e autores.  
> * **Fase 4 (Implementação Agêntica):** Agentes especializados (ex: Agente Histórico, Agente Doutrinário, Agente de Citação) orchestrados pelo sistema de IA para responder consultas complexas com checagem de fontes.
## **7\. Decisões de Implementação (out/2026)**

Ajustes ao desenho acima, já implementados em `ia/`, `rag/`, `sql/` e `infra/` (uso no `README.md` da raiz):

| Item | Decisão | Motivo |
| :---- | :---- | :---- |
| Contrato com a IA | API compatível com OpenAI (`/v1/chat/completions`, `/v1/embeddings`), escolhida por `IA_PERFIL` (`.env.dev` / `.env.prod`) | O mesmo código fala com Ollama (dev), vLLM/TEI ou API hospedada (VM), sem alteração |
| Embeddings | `bge-m3` (1024 dims), modelo gravado em cada trecho | O acervo é multilíngue (PT, ES, EN, FR, esperanto); mxbai-embed-large é focado em inglês |
| Geração | `qwen3:14b` Q4 no Ollama (cabe com o bge-m3 nos 16 GB da RTX 5080); `gemma3:12b` como alternativa | Comparar com `espirita-rag ask --modelo` |
| Extração | PyMuPDF (já usado no `finder`); remove cabeçalho/rodapé repetido, notas de rodapé e chamadas sobrescritas; desfaz hifenização preservando ênclises | pdfplumber/PyPDF2 são mais lentos e não dão fonte/posição tão fácil |
| Sumário | Marcadores do PDF → regex na página de sumário → LLM lê a página de sumário (saída JSON); cada entrada é localizada no texto | Muitos PDFs não têm marcadores; o manifesto fica em `obras.manifesto` |
| Metadados | LLM lê as primeiras páginas: título, autor/médium, autor espiritual, tradutor, editora | O catálogo do finder muitas vezes só tem o nome do arquivo |
| Chunking | Estrutural: corta em títulos, agrupa por item numerado (questão do LE, item do ESE) ou parágrafo (~1400 caracteres, sobreposição de ~250 na prosa) | Preserva a unidade citável (questão/item) |
| Busca | Filtrada pelo idioma da pergunta. Pergunta → vetorial (HNSW, cosseno); palavra-chave (sem "?", até 4 palavras) → híbrida (`tsvector` + RRF). Reranker `bge-reranker-v2-m3` implementado, desligado por padrão | Medido no `eval` (README): MRR 0,59 contra 0,46 do vetorial sem filtro; o vetor perde termos raros ("aeróbus"); o reranker piorou o top 5. BM25 real (ParadeDB `pg_search`) segue na Fase 2 |
| Produção | Ingestão sempre local; a VM recebe o banco por `pg_dump`/`pg_restore` e só embeda a pergunta e gera a resposta | A parte pesada fica na GPU local; a VM pode até não ter GPU |
