// Cliente da API FastAPI (api/main.py). Mesma origem em produção; proxy do Vite em dev.

export type Trecho = {
  id: string
  referencia: string
  conteudo: string
  notas: Record<string, number>
}

export type Fonte = { numero: number; id: string; referencia: string; conteudo: string }

export type Resposta = {
  resposta: string
  invalidas: number[]
  fontes: Fonte[]
  agente?: 'historico' | 'doutrinario'
  citacoes_nao_confirmadas?: string[]
}

/** Obra usada como filtro de uma conversa. */
export type ObraRef = { id: string; titulo: string }

export type Obra = {
  id: string
  titulo: string
  autor: string | null
  autor_espiritual: string | null
  colecao: string
  fonte: string
  ano: number | null
  paginas: number | null
  trechos: number
}

export type ObraDetalhe = Obra & {
  medium: string | null
  tradutor: string | null
  url_pdf: string | null
  sumario: { nivel: number; titulo: string; pagina: number | null }[]
}

export type Categoria = { id: string; nome: string; obra: string | null }

export type Conceito = {
  id: string
  nome: string
  nivel: number
  obra_origem: string | null
  pai: { id: string; nome: string } | null
  filhos: { id: string; nome: string }[]
  sinonimos: string[]
  trechos: { id: string; titulo: string; trecho: string; pagina: number; tipo: string }[]
}

async function pedir<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    const corpo = await res.json().catch(() => null)
    throw new Error(corpo?.detail ?? `${res.status} ${res.statusText}`)
  }
  return res.json()
}

export const api = {
  buscar: (q: string, obra = '') =>
    pedir<Trecho[]>(`/api/search?q=${encodeURIComponent(q)}${obra ? `&obra=${encodeURIComponent(obra)}` : ''}`),
  perguntar: (pergunta: string, agentes: boolean, obra?: string) =>
    pedir<Resposta>(agentes ? '/api/ask-agentes' : '/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pergunta, obra }),
    }),
  obras: () => pedir<Obra[]>('/api/obras'),
  obra: (id: string) => pedir<ObraDetalhe>(`/api/obras/${encodeURIComponent(id)}`),
  capa: (id: string) => `/api/obras/${encodeURIComponent(id)}/capa`,
  categorias: () => pedir<Categoria[]>('/api/grafo'),
  conceito: (id: string) => pedir<Conceito>(`/api/grafo/${encodeURIComponent(id)}`),
}
