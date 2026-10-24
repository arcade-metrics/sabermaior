# Como contribuir com o Saber Maior

Obrigado por querer ajudar. O projeto é construído em conjunto, e boa parte das contribuições mais
valiosas não exige programar. Escolha a que combina com você.

Dúvidas: abra uma [issue](https://github.com/arcade-metrics/sabermaior/issues) ou escreva para
[edu@arcademetrics.com](mailto:edu@arcademetrics.com).

## 1. Perguntas de avaliação (não precisa programar)

É a contribuição mais útil hoje. Cada mudança na busca é medida contra um conjunto de perguntas com
resposta conhecida ([`rag/avaliacao.jsonl`](rag/avaliacao.jsonl)), e ele tem só 25 perguntas. Com
mais perguntas, conseguimos saber de verdade o que melhora e o que piora.

Cada pergunta tem três partes:

| Campo | O que é | Exemplo |
|---|---|---|
| `pergunta` | Como alguém perguntaria de verdade, em pt-BR | Por que os Espíritos precisam encarnar? |
| `obra` | A obra onde está a resposta | Livro dos Espiritos |
| `esperado` | Uma frase curta, **copiada literalmente** do trecho que responde | fazê-los chegar à perfeição |

Dicas:

- Varie o jeito de perguntar: paráfrases, linguagem do dia a dia, termos técnicos, nomes próprios.
- A frase esperada deve ser curta e exata, porque é procurada no texto do trecho.
- Perguntas que o sistema hoje erra são as mais valiosas.

Envie pelo modelo [Pergunta de avaliação](https://github.com/arcade-metrics/sabermaior/issues/new?template=pergunta-avaliacao.yml)
ou, se preferir, num pull request que acrescente linhas ao `rag/avaliacao.jsonl`:

```json
{"pergunta": "Por que os Espíritos precisam encarnar?", "obra": "Livro dos Espiritos", "esperado": "fazê-los chegar à perfeição"}
```

## 2. Erros nas obras e nas respostas (não precisa programar)

Use o modelo [Erro em obra](https://github.com/arcade-metrics/sabermaior/issues/new?template=erro-em-obra.yml) para:

- título, autor, médium ou autor espiritual errados no catálogo;
- sumário, capítulo ou página que não conferem com o livro;
- citação que não diz o que a resposta afirma;
- obra duplicada ou faltando.

Inclua a obra, o que está errado e, se souber, o que deveria estar.

## 3. Revisão doutrinária da ontologia

A Fase 3 organiza os conceitos doutrinários num grafo (por exemplo, *perispírito* como parte de
*Espírito*, relacionado a *reencarnação*). A proposta está em
[`docs/proposta-ontologia-fase3.md`](docs/proposta-ontologia-fase3.md). Críticas sobre a hierarquia,
os nomes e as relações são muito bem-vindas, numa issue ou por e-mail.

## 4. Código

### Preparar o ambiente

Siga [`docs/desenvolvimento.md`](docs/desenvolvimento.md). Em resumo: Python 3.11+, Docker para o
PostgreSQL, Ollama para os modelos e o `finder` para baixar o acervo. Os PDFs, o banco e os arquivos
`.env.*` ficam só na sua máquina; o repositório tem apenas os modelos `.env.*.example`.

### Onde ajudar

- Testes automatizados para extração, chunking e busca (hoje só existe o `eval`)
- Reranker que não prefira as apostilas que citam uma passagem à obra original
- Grafo de conceitos (`grafo/`) e agentes (`agentes/`)
- Interface (`web/`: React, TypeScript, Tailwind CSS)

As pendências atualizadas estão em [`docs/status-e-proximos-passos.md`](docs/status-e-proximos-passos.md).

### Fluxo

1. Para mudanças maiores, abra uma issue antes, para combinarmos a abordagem.
2. Crie um branch a partir de `main`, com um nome descritivo.
3. Mantenha o estilo do código ao redor: nomes e comentários em português, funções curtas.
4. **Mensagens de commit em inglês**, no imperativo e com a primeira linha curta
   (`Add brand logo to the sidebar`, `Fix chunking in FEB editions`). O código continua em português;
   só o histórico do git é em inglês. Um check no pull request recusa commits com título em português.
5. **Se a mudança afeta a busca ou a resposta, rode `espirita-rag eval` antes e depois** e coloque os
   dois resultados no pull request, mesmo se piorar. Medimos antes de afirmar.
6. Abra o pull request explicando o que mudou e por quê.

### Princípios que valem para todo código

- Toda afirmação de uma resposta precisa apontar para um trecho real; nada que enfraqueça isso entra.
- Citações são literais: o texto das obras nunca é reescrito.
- pt-BR em primeiro lugar.
- O código fala só com a API compatível com OpenAI (`ia/`), para continuar rodando local ou na nuvem
  sem mudanças.

## Licença das contribuições

Ao contribuir, você concorda que seu código seja distribuído sob a [AGPL-3.0](LICENSE), e que
documentação, perguntas de avaliação e ontologia sejam distribuídas sob a
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.pt_BR).

## Convivência

Seja respeitoso e paciente. Divergências de interpretação doutrinária são naturais: discuta as
ideias citando as obras, nunca as pessoas.
