import { LoaderCircle, TriangleAlert } from 'lucide-react'
import { useState, type ReactNode } from 'react'

export function Carregando({ texto }: { texto: string }) {
  return (
    <div className="flex items-center gap-2 py-6 text-sm text-suave" role="status">
      <LoaderCircle className="size-4 animate-spin" aria-hidden />
      {texto}
    </div>
  )
}

export function Erro({ erro }: { erro: unknown }) {
  const msg = erro instanceof Error ? erro.message : String(erro)
  return (
    <div className="flex items-start gap-2 rounded-lg border border-erro/30 bg-erro/5 p-3 text-sm text-erro">
      <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
      <span>Erro: {msg}</span>
    </div>
  )
}

export function Cartao({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-2xl border border-borda bg-caixa ${className}`}>{children}</div>
}

/** Texto de um trecho, recolhido em poucas linhas até a pessoa pedir para ver tudo. */
export function TextoTrecho({ texto, linhas = 6 }: { texto: string; linhas?: number }) {
  const [aberto, setAberto] = useState(false)
  const longo = texto.length > linhas * 90
  return (
    <div>
      <p
        className="leading-7 whitespace-pre-line text-texto/90"
        style={
          !aberto && longo
            ? { display: '-webkit-box', WebkitLineClamp: linhas, WebkitBoxOrient: 'vertical', overflow: 'hidden' }
            : undefined
        }
      >
        {texto}
      </p>
      {longo && (
        <button
          type="button"
          onClick={() => setAberto(!aberto)}
          className="mt-1 text-sm font-medium text-destaque hover:underline"
        >
          {aberto ? 'Mostrar menos' : 'Ler trecho completo'}
        </button>
      )}
    </div>
  )
}

export function BotaoEnviar({ ocupado = false, children }: { ocupado?: boolean; children: ReactNode }) {
  return (
    <button
      type="submit"
      disabled={ocupado}
      className="inline-flex h-11 shrink-0 items-center justify-center gap-2 rounded-full bg-destaque px-5 font-medium text-sobre-destaque transition hover:bg-destaque-forte disabled:opacity-50"
    >
      {ocupado && <LoaderCircle className="size-4 animate-spin" aria-hidden />}
      {children}
    </button>
  )
}

export const classeCampo =
  'min-h-11 w-full rounded-full border border-borda bg-caixa px-4 py-2.5 text-base outline-none placeholder:text-suave focus:border-destaque focus:ring-2 focus:ring-destaque/20'
