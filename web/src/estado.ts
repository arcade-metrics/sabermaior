// Estado guardado só no navegador: tema escolhido e histórico de conversas.
// O backend não tem memória de conversa; cada pergunta é respondida isoladamente.
import { useEffect, useState } from 'react'
import { api, type ObraRef, type Resposta } from './api'

function ler<T>(chave: string, padrao: T): T {
  try {
    const v = localStorage.getItem(chave)
    return v ? (JSON.parse(v) as T) : padrao
  } catch {
    return padrao
  }
}

function gravar(chave: string, valor: unknown) {
  try {
    localStorage.setItem(chave, JSON.stringify(valor))
  } catch {
    // modo privado ou armazenamento bloqueado: segue só em memória
  }
}

export type Tema = 'sistema' | 'claro' | 'escuro'

export function useTema() {
  const [tema, setTema] = useState<Tema>(() => ler('sabermaior.tema', 'sistema'))
  useEffect(() => {
    const raiz = document.documentElement
    if (tema === 'sistema') raiz.removeAttribute('data-theme')
    else raiz.dataset.theme = tema === 'claro' ? 'light' : 'dark'
    gravar('sabermaior.tema', tema)
  }, [tema])
  return [tema, setTema] as const
}

export type VisaoObras = 'lista' | 'cards'

export function useVisaoObras() {
  const [visao, setVisao] = useState<VisaoObras>(() => ler('sabermaior.visao-obras', 'lista'))
  useEffect(() => gravar('sabermaior.visao-obras', visao), [visao])
  return [visao, setVisao] as const
}

export type Rodada = {
  id: string
  pergunta: string
  agentes: boolean
  obra?: ObraRef // filtro em vigor quando a pergunta foi feita
  resposta?: Resposta
  erro?: string
}
// `obra`: as próximas perguntas da conversa só consultam essa obra.
export type Conversa = { id: string; titulo: string; atualizada: number; rodadas: Rodada[]; obra?: ObraRef }

const CHAVE = 'sabermaior.conversas'
const novoId = () => Math.random().toString(36).slice(2, 10)

function carregar(): Conversa[] {
  // Pergunta que estava em andamento quando a página foi fechada não vai mais voltar.
  return ler<Conversa[]>(CHAVE, []).map((c) => ({
    ...c,
    rodadas: c.rodadas.map((r) => (r.resposta || r.erro ? r : { ...r, erro: 'pergunta interrompida' })),
  }))
}

export function useConversas() {
  const [conversas, setConversas] = useState<Conversa[]>(carregar)
  useEffect(() => gravar(CHAVE, conversas), [conversas])

  function alterarRodada(conversaId: string, rodadaId: string, dados: Partial<Rodada>) {
    setConversas((cs) =>
      cs.map((c) =>
        c.id !== conversaId ? c : { ...c, rodadas: c.rodadas.map((r) => (r.id === rodadaId ? { ...r, ...dados } : r)) },
      ),
    )
  }

  /** Envia a pergunta; cria a conversa (com o filtro `obra`, se houver) quando `conversaId` é vazio.
   * Retorna o id da conversa. */
  function perguntar(conversaId: string, pergunta: string, agentes: boolean, obra?: ObraRef): string {
    const cid = conversaId || novoId()
    const rodada: Rodada = { id: novoId(), pergunta, agentes, obra }
    setConversas((cs) => {
      const existente = cs.find((c) => c.id === cid)
      const conversa: Conversa = existente
        ? { ...existente, atualizada: Date.now(), rodadas: [...existente.rodadas, rodada] }
        : { id: cid, titulo: pergunta.slice(0, 60), atualizada: Date.now(), rodadas: [rodada], obra }
      return [conversa, ...cs.filter((c) => c.id !== cid)]
    })
    api
      .perguntar(pergunta, agentes, obra?.id)
      .then((resposta) => alterarRodada(cid, rodada.id, { resposta }))
      .catch((e: unknown) => alterarRodada(cid, rodada.id, { erro: e instanceof Error ? e.message : String(e) }))
    return cid
  }

  function tirarObra(id: string) {
    setConversas((cs) => cs.map((c) => (c.id === id ? { ...c, obra: undefined } : c)))
  }

  function apagar(id: string) {
    setConversas((cs) => cs.filter((c) => c.id !== id))
  }

  return { conversas, perguntar, tirarObra, apagar, apagarTudo: () => setConversas([]) }
}
