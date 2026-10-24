import { useQuery } from '@tanstack/react-query'
import { BookOpen, X } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { api } from '../api'
import { BotaoEnviar, Cartao, Carregando, Erro, TextoTrecho, classeCampo } from './comum'

/** Busca de trechos; `obra` (id) restringe a busca a uma obra, vindo da página Obras. */
export function Buscar({ obra = '' }: { obra?: string }) {
  const [texto, setTexto] = useState('')
  const [termo, setTermo] = useState('')
  const busca = useQuery({
    queryKey: ['busca', termo, obra],
    queryFn: () => api.buscar(termo, obra),
    enabled: !!termo,
  })
  const detalhe = useQuery({ queryKey: ['obra', obra], queryFn: () => api.obra(obra), enabled: !!obra })

  function enviar(e: FormEvent) {
    e.preventDefault()
    setTermo(texto.trim())
  }

  return (
    <div className="mx-auto w-full max-w-3xl space-y-6 px-4 py-6 sm:py-8">
      <div className="space-y-3">
        <form onSubmit={enviar} className="flex flex-col gap-2 sm:flex-row">
          <input
            type="search"
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder={obra ? 'Buscar nesta obra' : 'Palavras-chave ou pergunta, ex.: Que é Deus?'}
            aria-label="Busca"
            autoFocus={!!obra}
            className={classeCampo}
          />
          <BotaoEnviar ocupado={busca.isFetching}>Buscar</BotaoEnviar>
        </form>
        {obra && (
          <span className="inline-flex max-w-full items-center gap-1.5 rounded-full bg-destaque/10 py-1 pr-1 pl-3 text-sm text-destaque">
            <BookOpen className="size-3.5 shrink-0" aria-hidden />
            <span className="truncate">Só em: {detalhe.data?.titulo ?? '…'}</span>
            <a
              href="#/buscar"
              aria-label="Buscar em todo o acervo"
              title="Buscar em todo o acervo"
              className="inline-flex size-6 shrink-0 items-center justify-center rounded-full hover:bg-destaque/15"
            >
              <X className="size-3.5" aria-hidden />
            </a>
          </span>
        )}
      </div>

      {!termo && (
        <p className="text-sm text-suave">
          Mostra os trechos do acervo mais próximos da busca, sem gerar resposta.
        </p>
      )}
      {busca.isLoading && <Carregando texto="Buscando…" />}
      {busca.isError && <Erro erro={busca.error} />}
      {busca.data?.length === 0 && <p className="text-suave">Nenhum trecho encontrado.</p>}
      {busca.data && busca.data.length > 0 && (
        <ol className="space-y-3">
          {busca.data.map((t) => (
            <li key={t.id}>
              <Cartao className="space-y-2 p-4 sm:p-5">
                <p className="text-sm font-semibold text-destaque">{t.referencia}</p>
                <TextoTrecho texto={t.conteudo} />
              </Cartao>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}
