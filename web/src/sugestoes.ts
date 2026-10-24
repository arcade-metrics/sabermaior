// Perguntas da tela inicial: amplas, de doutrina, testadas contra o RAG (só ficaram as
// que voltam com resposta boa e citada). Ao acrescentar uma, teste antes no chat.
// A tela mostra quatro sorteadas.

export type Sugestao = { titulo: string; pergunta: string }

const SUGESTOES: Sugestao[] = [
  { titulo: 'Alma e Espírito', pergunta: 'Qual a diferença entre alma e Espírito?' },
  { titulo: 'Perispírito', pergunta: 'O que é o perispírito?' },
  { titulo: 'Deus', pergunta: 'Como os Espíritos definem Deus?' },
  { titulo: 'Reencarnação', pergunta: 'Por que precisamos reencarnar?' },
  { titulo: 'Entre vidas', pergunta: 'O que acontece com o Espírito entre uma encarnação e outra?' },
  { titulo: 'Mundos habitados', pergunta: 'Existem outros mundos habitados segundo o Espiritismo?' },
  { titulo: 'Sono e sonhos', pergunta: 'O que acontece com o Espírito durante o sono?' },
  { titulo: 'Penas eternas', pergunta: 'Existem penas eternas segundo o Espiritismo?' },
  { titulo: 'Prece', pergunta: 'Para que serve a prece segundo o Espiritismo?' },
  { titulo: 'Perdão', pergunta: 'Por que devemos perdoar os inimigos?' },
  { titulo: 'Obsessão', pergunta: 'O que é obsessão e como se livrar dela?' },
  { titulo: 'Luto', pergunta: 'Como lidar com a morte de quem amamos?' },
]

export function sortearSugestoes(quantas = 4): Sugestao[] {
  const lista = [...SUGESTOES]
  for (let i = lista.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[lista[i], lista[j]] = [lista[j], lista[i]]
  }
  return lista.slice(0, quantas)
}
