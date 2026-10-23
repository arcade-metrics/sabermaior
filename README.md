# sabermaior

- `finder/`: busca e baixa o acervo (PDFs + `catalogo.csv`). Veja `finder/README.md`.
- `ia/`: acesso à IA local ou remota por uma API compatível com OpenAI. Serve a este e a outros projetos.
- `rag/`: pipeline RAG (`espirita-rag`): ingestão, busca híbrida e resposta com citação.

Arquitetura e roteiro: `docs/Arquitetura do Pipeline RAG e Sistema Agêntico para Literatura Espírita.md`.
O que já foi feito e o que falta: `docs/status-e-proximos-passos.md`.

O repositório tem só o código. O acervo (`finder/dados/`), o banco e os `.env.*` ficam fora do git:
rode o `finder` para baixar o acervo e `espirita-rag ingest` para montar o banco.

## Subir o ambiente (dev, sob demanda)

```
cp .env.dev.example .env.dev                                # opcional: sem ele valem os mesmos padrões
docker compose -f infra/docker-compose.yml up -d postgres   # Postgres + pgvector em 127.0.0.1:5434
# Ollama: abrir o app (roda nativo no Windows, usa a GPU)
pip install -e .            # ou .[rerank] para o reranker local (torch CUDA)
espirita-rag status
```

Modelos no Ollama: `ollama pull bge-m3` (embeddings) e `ollama pull qwen3:14b` (geração).
Variáveis de usuário do Ollama: `OLLAMA_CONTEXT_LENGTH=16384`, `OLLAMA_FLASH_ATTENTION=1`,
`OLLAMA_KV_CACHE_TYPE=q8_0`, `OLLAMA_MAX_LOADED_MODELS=2`, `OLLAMA_KEEP_ALIVE=10m`. Sem o
`OLLAMA_CONTEXT_LENGTH` o contexto fica em 4096 e corta os trechos do RAG sem avisar.

Use `127.0.0.1`, não `localhost`: no Windows, `localhost` tenta primeiro o IPv6 e cada conexão
pode levar segundos.

## Dev e produção

O código só fala com `/v1/chat/completions` e `/v1/embeddings`. Quem atende (Ollama, vLLM, TEI,
API hospedada) é escolhido por variável de ambiente:

| | dev (`.env.dev`) | prod (`.env.prod`, modelo em `.env.prod.example`) |
|---|---|---|
| geração | Ollama `qwen3:14b` | vLLM na VM com GPU, ou API hospedada |
| embeddings | Ollama `bge-m3` | TEI `BAAI/bge-m3` (CPU basta: só embeda a pergunta) |
| reranker | `none` ou `local` (sentence-transformers) | TEI `bge-reranker-v2-m3` |
| banco | compose `postgres` | compose `postgres` (mesma imagem) |

`IA_PERFIL=prod espirita-rag ask "..."` troca tudo sem mudar código. Variáveis definidas no
ambiente têm prioridade sobre o arquivo.

Estratégia recomendada: a ingestão (pesada, usa LLM e GPU) roda sempre local; a VM recebe o banco
pronto (`pg_dump` / `pg_restore`) e só embeda a pergunta e gera a resposta.

O modelo de embedding fica gravado em cada trecho (`modelo_embedding`). Trocar de modelo exige
reindexar (`espirita-rag ingest --refazer`). Medido em 23/10/2026: bge-m3 no Ollama e no TEI
(`cpu-1.8`) dão vetores idênticos (cosseno 1,0000) e o mesmo resultado no `eval`; o TEI em CPU
embeda uma pergunta em ~24 ms. `EMBED_MODEL` deve continuar `bge-m3` em produção (é o nome gravado
no banco; o TEI ignora esse campo).

## Uso

```
espirita-rag init-db                                  # reaplica sql/*.sql (idempotente)
espirita-rag ingest                                   # todo finder/dados; pula o que já está no banco
espirita-rag ingest --filtro "nosso lar" --refazer
espirita-rag parse-toc --file livro.pdf --output-manifest manifesto.json   # revisar sumário
espirita-rag search "Que é Deus?" -k 5 [--modo auto|vetorial|hibrida|textual] [--obra "Livro dos Espíritos"] [--idioma todos]
espirita-rag ask "Qual o objetivo da encarnação?" [--pensar] [--modelo gemma3:12b]
espirita-rag eval [--detalhar]                        # recall@k sobre rag/avaliacao.jsonl
```

## Qualidade da busca (`espirita-rag eval`)

Acervo de 23/10/2026: 342 obras, 53.395 trechos (pt 319 obras e 49.065 trechos; o resto são
23 obras em es, en, fr e eo sem equivalente em pt). 25 consultas em pt (21 perguntas parafraseadas,
4 palavras-chave como "aeróbus"), cada uma com a passagem esperada na obra de origem. Todas as
linhas, menos a segunda, usam o idioma da pergunta:

| configuração | R@1 | R@5 | R@10 | MRR |
|---|---|---|---|---|
| **auto (padrão): vetorial para perguntas, híbrida para palavras-chave** | **0,28** | **0,64** | **0,80** | **0,42** |
| vetorial | 0,24 | 0,64 | 0,80 | 0,40 |
| híbrida RRF | 0,20 | 0,56 | 0,84 | 0,34 |
| vetorial, todos os idiomas | 0,24 | 0,56 | 0,80 | 0,38 |
| textual (tsvector, E) | 0,16 | 0,20 | 0,24 | 0,19 |

O reranker bge-reranker-v2-m3 foi medido antes da limpeza (27 consultas, com traduções e
duplicatas): R@1 0,44, R@5 0,67, R@10 0,74, MRR 0,53, contra 0,41, 0,85, 0,89 e 0,59 do `auto`
na mesma base; o número de referência mudou, veja abaixo.

O que explica os números:
- A prioridade é pt-BR. As traduções de obras que já existem em pt (72 obras: o LE em es, en, fr,
  eo, a Revue Spirite etc.) foram retiradas e estão listadas em `rag/excluidas.csv`, com a obra
  equivalente e a similaridade medida pelo bge-m3; o `ingest` pula esses PDFs. Ficaram só as
  obras sem equivalente em pt. Mesmo assim a busca usa o idioma da pergunta (`--idioma auto`), e
  `--idioma todos` desliga o filtro.
- O acervo também tinha 18 duplicatas dentro do próprio pt: os clássicos de Kardec e a Revista
  Espírita existiam numa edição do `consolador` e noutra da FEB (tradução Guillon Ribeiro ou
  Quintão), e dois PDFs da FEB tinham conteúdo idêntico sob nomes diferentes. Ficou só a edição da
  FEB, por ser a tradução de referência; os descartes também estão em `rag/excluidas.csv`
  (`motivo=duplicata_edicao` ou `arquivo_duplicado`).
- Essa limpeza **piorou** os números do `eval` (R@5 caiu de 0,88 para 0,64): o `chunking` agrupa
  itens numerados até ~1.400 caracteres, e as edições da FEB têm itens mais curtos, então reúnem
  mais perguntas por trecho do que as do `consolador` — o trecho certo às vezes existe mas sai do
  top 5 ou do top 10. Confirmado manualmente: as frases esperadas de "Que é Deus?", "Conhece-te a
  ti mesmo" e do perispírito aparecem, literais, nas edições da FEB mantidas; a busca só não as
  traz entre os primeiros resultados para certas perguntas. Ajustar o chunking para essas edições
  é o próximo passo antes de confiar nesses números.
- O vetor perde termos raros isolados ("aeróbus" trazia "aeronauta"); a busca textual acha. Já
  em perguntas em linguagem natural, o `ts_rank` (sem IDF) só atrapalha. Daí o modo `auto`: sem
  "?" e com até 4 palavras vai na híbrida, senão só no vetor. BM25 de verdade (ParadeDB
  `pg_search`, Fase 2) pode tornar a híbrida boa para tudo.
- O reranker melhora o 1º lugar, mas piora o top 5/10: prefere as apostilas da FEB que citam a
  passagem à obra original. Fica desligado (`RERANK_PROVIDER=none`); ligue com
  `RERANK_PROVIDER=local` para testar.

Geração (`ask`, mesmas 6 passagens): `qwen3:14b` responde em 2 a 6 s; `gemma3:12b` em ~7 s, cita
mais trechos e é mais detalhado. Ambos citaram só trechos existentes nos testes.

## Usar a IA em outros processos

```python
from ia import IA
ia = IA()                       # perfil de IA_PERFIL (padrão dev)
ia.chat([{"role": "user", "content": "Resuma: ..."}], raciocinio="none")
ia.chat(mensagens, esquema={...JSON Schema...})   # saída estruturada, já decodificada
ia.embed(["texto 1", "texto 2"])
```

Ou qualquer cliente OpenAI apontado para `http://127.0.0.1:11434/v1`.
