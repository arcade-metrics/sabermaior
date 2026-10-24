import { useQuery } from '@tanstack/react-query'
import { ChevronRight } from 'lucide-react'
import { api } from '../api'
import { Cartao, Carregando, Erro, TextoTrecho } from './comum'

/** Navegação pelo grafo de conceitos (Fase 3). `id` vazio mostra as categorias de nível 1. */
export function Conceitos({ id, ir }: { id: string; ir: (id: string) => void }) {
  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:py-8">
      {id ? <Conceito id={id} ir={ir} /> : <Categorias ir={ir} />}
    </div>
  )
}

function Categorias({ ir }: { ir: (id: string) => void }) {
  const q = useQuery({ queryKey: ['categorias'], queryFn: api.categorias })
  if (q.isLoading) return <Carregando texto="Carregando categorias…" />
  if (q.isError) return <Erro erro={q.error} />
  return (
    <div className="space-y-4">
      <p className="text-sm text-suave">
        Categorias do Tesauro Espírita. Escolha uma para ver os conceitos e os trechos ligados a eles.
      </p>
      <Grade itens={q.data ?? []} ir={ir} />
    </div>
  )
}

function Conceito({ id, ir }: { id: string; ir: (id: string) => void }) {
  const q = useQuery({ queryKey: ['conceito', id], queryFn: () => api.conceito(id) })
  if (q.isLoading) return <Carregando texto="Carregando conceito…" />
  if (q.isError) return <Erro erro={q.error} />
  const c = q.data!

  return (
    <div className="space-y-6">
      <nav aria-label="Caminho" className="flex flex-wrap items-center gap-1 text-sm text-suave">
        <button type="button" onClick={() => ir('')} className="text-destaque hover:underline">
          Categorias
        </button>
        {c.pai && (
          <>
            <ChevronRight className="size-3.5" aria-hidden />
            <button type="button" onClick={() => ir(c.pai!.id)} className="text-destaque hover:underline">
              {c.pai.nome}
            </button>
          </>
        )}
        <ChevronRight className="size-3.5" aria-hidden />
        <span aria-current="page">{c.nome}</span>
      </nav>

      <header className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight">{c.nome}</h2>
        {c.obra_origem && <p className="text-sm text-suave">{c.obra_origem}</p>}
        {c.sinonimos.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 text-sm">
            <span className="text-suave">Também chamado de:</span>
            {c.sinonimos.map((s) => (
              <span key={s} className="rounded-full bg-destaque/10 px-2.5 py-0.5 text-destaque">
                {s}
              </span>
            ))}
          </div>
        )}
      </header>

      {c.filhos.length > 0 && (
        <section className="space-y-2">
          <h3 className="text-sm font-medium text-suave">Conceitos</h3>
          <Grade itens={c.filhos} ir={ir} />
        </section>
      )}

      {c.trechos.length > 0 && (
        <section className="space-y-2">
          <h3 className="text-sm font-medium text-suave">Trechos ligados</h3>
          <ol className="space-y-3">
            {c.trechos.map((t) => (
              <li key={t.id}>
                <Cartao className="space-y-2 p-4 sm:p-5">
                  <p className="text-sm font-semibold text-destaque">
                    {t.titulo}, p. {t.pagina}
                  </p>
                  <TextoTrecho texto={t.trecho} />
                </Cartao>
              </li>
            ))}
          </ol>
        </section>
      )}

      {c.filhos.length === 0 && c.trechos.length === 0 && (
        <p className="text-suave">Nenhum trecho ligado ainda.</p>
      )}
    </div>
  )
}

function Grade({ itens, ir }: { itens: { id: string; nome: string }[]; ir: (id: string) => void }) {
  return (
    <ul className="grid gap-2 sm:grid-cols-2">
      {itens.map((i) => (
        <li key={i.id}>
          <button
            type="button"
            onClick={() => ir(i.id)}
            className="flex h-full w-full items-center justify-between gap-2 rounded-xl border border-borda bg-caixa px-4 py-3 text-left text-sm transition hover:border-destaque/50 hover:bg-lateral"
          >
            <span>{i.nome}</span>
            <ChevronRight className="size-4 shrink-0 text-suave" aria-hidden />
          </button>
        </li>
      ))}
    </ul>
  )
}
