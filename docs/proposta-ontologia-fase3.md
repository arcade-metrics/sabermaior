# Proposta de ontologia — Fase 3 (grafo de conhecimento)

Implementado em `sql/003_grafo.sql`, `grafo/` e nas rotas `/api/grafo*` (ver seção 10). Objetivo: ligar conceitos doutrinários
(Espírito, perispírito, reencarnação, causa e efeito...) entre si e às passagens que já estão
no banco (`obras`/`trechos`), sem duplicar o que a Fase 1/2 já resolve (texto, metadados,
busca). O grafo serve para perguntas que a busca por similaridade não responde bem: "quais
conceitos O Livro dos Espíritos define e Nosso Lar ilustra", "que relação há entre perispírito
e mediunidade", "que questões do LE o ESE reorganiza".

## 1. Banco: PostgreSQL, tabelas simples (não Apache AGE nem Neo4j)

Evita subir outro banco — mesma instância ParadeDB (`infra/docker-compose.yml`), mesmo
`DATABASE_URL`, mesmo backup. A proposta original era Apache AGE (grafo de propriedades com
Cypher), mas na hora de implementar vi que AGE exige compilar a extensão contra o build exato
do Postgres da imagem `paradedb/paradedb:0.26.3-pg17` — essa imagem não tem toolchain/fontes, e
recompilá-la por fora é um risco de infra desproporcional ao tamanho do grafo (menos de 200
nós). Optei por modelar nós e arestas como tabelas comuns (`sql/003_grafo.sql`): mesmo
resultado (conceitos + relações tipadas, sem duplicar `obras`/`trechos`), com `JOIN` normal em
vez de Cypher. Se o grafo crescer muito (milhares de nós, travessias profundas) e isso realmente
doer, migrar para AGE ou um grafo dedicado continua uma opção — hoje não se justificava.

## 2. Padrões seguidos (em vez de inventar uma taxonomia do zero)

- **SKOS** (`skos:broader`/`narrower`/`related`) para a hierarquia de conceitos doutrinários —
  vocabulário padrão para taxonomias/tesauros, evita reinventar semântica de "é um tipo de"
  vs. "está relacionado a". No grafo isso vira os tipos de aresta `AMPLIA`/`RESTRINGE`/
  `RELACIONADO_A` entre nós `Conceito`.
- **Dublin Core / FRBR** (noção de Obra → Expressão/Edição) para não reintroduzir o que
  `obras` já modela: o grafo não duplica título/autor/idioma, só referencia `obras.id` e
  `trechos.id` como propriedade do nó.
- **schema.org `Person`/`CreativeWork`** como referência de nomenclatura de propriedades do
  nó `Autor` (nome, nome alternativo, papel: médium vs. autor espiritual) — já existe essa
  distinção em `obras.manifesto->>'autor_espiritual'`.

## 3. Nós (tabela `conceitos`, em `sql/003_grafo.sql`)

| Coluna | Significado |
|---|---|
| `id` | slug (ex.: `pluralidade_de_existencias__encarnacao__perispirito`) |
| `nome` | nome de exibição (ex.: "Perispírito") |
| `nivel` | 1 = categoria, 2 = subcategoria, 3 = termo (profundidade na hierarquia) |
| `categoria_pai_id` | FK para o `Conceito` pai direto (null no nível 1) |
| `obra_origem` | obra de Kardec de onde o conceito veio (texto livre, não FK para `obras`) |

`conceito_sinonimos` guarda os termos não preferidos (par USE/UP do tesauro original).
`Obra`/`Autor`/`Entidade` como nós próprios, ligados por chave a `obras.id` (seção 8 original),
**ainda não foram implementados** — hoje o grafo só cobre a hierarquia de `Conceito` e seus
trechos; ligar a obras/autores/entidades específicas fica para quando isso for pedido.

## 4. Relações

| Tabela / coluna | De → Para | Significado |
|---|---|---|
| `conceitos.categoria_pai_id` | `Conceito` → `Conceito` | SKOS broader/narrower (`AMPLIA`/`RESTRINGE`): o pai amplia, o filho restringe |
| `conceito_sinonimos` | `Conceito` → texto | `SINONIMO_DE`: termo não preferido (USE/UP) |
| `conceito_trechos.tipo = 'MENCIONA'` | `Conceito` → `Trecho` | O trecho menciona o conceito (ligação automática por BM25, seção 6) |
| `conceito_trechos.tipo = 'DEFINIDO_EM'` | `Conceito` → `Trecho` | Passagem canônica que define o conceito — hoje não é distinguido de `MENCIONA` automaticamente, fica para curadoria manual |

`RELACIONADO_A` (SKOS related, sem hierarquia, ex.: Perispírito ↔ Mediunidade) e as relações
entre `Obra`/`Autor` (`ESCREVEU`, `CITA`, `TRADUCAO_DE`) da proposta original **não foram
implementadas** — exigiriam curadoria manual ou nós que ainda não existem (ver seção 3).

## 5. Taxonomia inicial de `Conceito` (nível 1, a partir de um tesauro já publicado)

Em vez de propor uma lista própria do zero, uso como semente a proposta de tesauro espírita de
Leonardo Adriano Ragacini (*Proposta de elaboração de um Tesauro Espírita: categorização
segundo as obras de Kardec*, Novas Edições Acadêmicas, 2017). É um trabalho de Biblioteconomia
que já fez o trabalho pesado: leu as sete obras de Kardec (Livro dos Espíritos, Livro dos
Médiuns, Evangelho Segundo o Espiritismo, Gênese, Obras Póstumas, O Céu e o Inferno, O Que É o
Espiritismo?) e extraiu 19 categorias, ~73 subtermos e ~86 termos relacionados, já normalizados
como termos de indexação e já seguindo a norma ISO 25964 (TG/TE = mais genérico/mais
específico, TR = termo relacionado, USE/UP = termo preferido/sinônimo) — a mesma lógica
broader/narrower/related do SKOS que eu já queria usar na seção 2. Isso elimina a etapa de
"sementes manuais" que eu tinha deixado em aberto: já existe uma garantia literária por trás de
cada termo.

As 19 categorias (nível 1 de `Conceito`, cada uma com suas subcategorias/termos específicos
como `AMPLIA`/`RESTRINGE`, e sinônimos como `SINONIMO_DE` a partir dos pares USE/UP do autor):

| # | Categoria | Obra de origem |
|---|---|---|
| 1 | Tipos de medianimidade | Livro dos Médiuns |
| 2 | Manifestações espirituais | Livro dos Médiuns |
| 3 | Natureza das comunicações espirituais | Livro dos Médiuns |
| 4 | Obsessões espirituais | Livro dos Médiuns |
| 5 | Fraudes espíritas (charlatanismo e embuste) | Livro dos Médiuns |
| 6 | Dissertações espíritas | Livro dos Médiuns |
| 7 | Influência moral do médium | Livro dos Médiuns |
| 8 | Escala espírita (1ª, 2ª e 3ª ordens) | Livro dos Espíritos |
| 9 | Princípio vital | Livro dos Médiuns / Gênese |
| 10 | Elementos gerais do universo | Livro dos Médiuns |
| 11 | Composição espiritual (espírito, perispírito) | Livro dos Espíritos |
| 12 | Pluralidade de existências (reencarnação) | Livro dos Espíritos |
| 13 | Lei natural (leis morais, causa e efeito) | Livro dos Espíritos |
| 14 | Penas e gozos (terrestres e futuros) | Livro dos Espíritos |
| 15 | Gênese (orgânica, espiritual, moisaica) | Gênese |
| 16 | Milagres do evangelho | Evangelho Segundo o Espiritismo |
| 17 | Fluidos espirituais e suas propriedades | Gênese |
| 18 | Alternativas humanas (doutrinas materialista, panteísta, deísta, dogmática) | Gênese |
| 19 | Noções elementares (espiritismo, ciência/filosofia/doutrina espírita, espíritos) | Livro dos Espíritos |

Cada categoria vira um nó `Conceito` de nível 1; os subtermos do Quadro 21 do autor (ex.:
dentro de "Tipos de medianimidade": médiuns audientes, falantes, videntes, sonambúlicos,
pneumatógrafos...) viram nós `Conceito` ligados por `RESTRINGE`. Os pares que ele já marcou como
equivalentes (ex.: "Lei Divina" `USE` "Lei Natural", "Demônios" `USE` "Espíritos impuros")
viram `SINONIMO_DE` direto, sem trabalho extra de curadoria. As categorias 1, 2, 3, 6, 7
(ligadas à mediunidade) se encaixam bem como `RESTRINGE` de um `Conceito` guarda-chuva
"Mediunidade"; as categorias 11-14 encaixam em "Espírito"/"Lei Moral"; a 15-17 em "Gênese";
a 8 e 18 ficam como ramos próprios. Isso é só um reagrupamento de nível acima do que o autor já
categorizou — a decisão de onde cada categoria entra fica para quando formos montar o grafo de
fato.

## 6. Como foi populado

1. **Taxonomia do Ragacini importada**: `grafo/sementes.py` tem as 19 categorias + ~70
   subcategorias + ~85 termos transcritos do Quadro 20/21 do autor, com os pares USE/UP como
   sinônimos. `espirita-rag grafo-povoar` insere tudo em `conceitos`/`conceito_sinonimos`
   (idempotente — reaplicar não duplica). Cobre as sete obras de Kardec; não cobre Nosso Lar nem
   outros médiuns psicografados.
2. **Ligação a trechos, sem LLM**: em vez da extração assistida por LLM que eu tinha planejado,
   `grafo.consulta.ligar_trechos` usa o próprio índice BM25 (`pg_search`/ParadeDB) já existente
   da Fase 2 — busca cada nome de conceito nos trechos (`paradedb.match`, disjunção entre
   palavras) e grava os 3 melhores como `MENCIONA`. É determinístico, roda em segundos para
   ~190 conceitos e já traz resultados relevantes (ex.: "Perispírito" acha as passagens certas
   do Livro dos Espíritos e do Programa Fundamental). Fica mais barato e mais rápido que rodar a
   LLM sobre o acervo inteiro; a troca é menos precisão em nomes muito genéricos ("Alma",
   "Espíritos") — ajustável depois subindo o `limite_por_conceito` ou trocando por extração via
   LLM se isso incomodar na prática.
3. **Pendente (curadoria manual)**: `RELACIONADO_A` entre conceitos (ex.: Perispírito ↔
   Mediunidade) e `DEFINIDO_EM` distinto de `MENCIONA` (passagem canônica, ex.: LE questão 1 para
   "Deus") — a tabela já tem a coluna `tipo` pronta para isso, falta o critério/curadoria.

## 7. Integração com a API/interface (feito)

- `GET /api/grafo` — lista as 19 categorias de nível 1.
- `GET /api/grafo/{id_ou_nome}` — nó (pai, filhos, sinônimos, trechos ligados). Aceita o slug
  (`pluralidade_de_existencias__encarnacao__perispirito`) ou o nome exibido ("Perispírito").
- Aba "Grafo" em `api/estaticos/index.html`: lista as categorias, navega para filhos e mostra os
  trechos ligados a cada conceito, com uma migalha de pão para voltar.

## 8. Decisões em aberto para você validar

- A lista de conceitos de nível 1 (seção 5) cobre o essencial ou falta algo prioritário?
- `RELACIONADO_A` entre conceitos (dentro ou entre obras) e `DEFINIDO_EM`: vale curar isso à mão
  aos poucos, ou é baixa prioridade frente à Fase 4?
- Vale reservar nós `Obra`/`Autor`/`Entidade` (pessoas/lugares históricos) de verdade, ou a
  hierarquia de `Conceito` + `MENCIONA` já resolve o que você precisa por enquanto?

## 9. Como usar

```
espirita-rag init-db                  # aplica sql/003_grafo.sql (idempotente)
espirita-rag grafo-povoar             # insere a taxonomia e liga trechos (~190 conceitos)
espirita-rag grafo-ver "Perispírito"  # inspeciona um conceito pela CLI
uvicorn api.main:app --reload         # sobe a API; aba "Grafo" em http://127.0.0.1:8000
```

## 10. Referências

- Ragacini, L. A. *Proposta de elaboração de um Tesauro Espírita: categorização segundo as
  obras de Kardec*. Novas Edições Acadêmicas, 2017 — fonte da taxonomia semente (seção 5).
- Mello, B. E. de. *Ontology of Monotheism: road map to reach the OntoM*. UFSC, 2018 — roteiro
  de doutorado (RDF/OWL/UFO/OntoUML) que comparou O Livro dos Espíritos com Torá, Bíblia e
  Alcorão; descartado aqui por escopo (interoperar com outras religiões) e formalismo (exige
  triplestore RDF) maiores do que o necessário para uso local, mas serve de referência caso o
  requisito de interoperabilidade apareça no futuro.
- Especificações W3C para o cenário acima, caso decidamos exportar o grafo como RDF/OWL mais
  adiante (hoje não é o caso — ver a discussão sobre AGE × triplestore na seção 1):
  - [RDF 1.1 Concepts](https://www.w3.org/TR/rdf11-concepts/)
  - [OWL 2 Web Ontology Language — Overview](https://www.w3.org/TR/owl2-overview/)
  - [SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/)
