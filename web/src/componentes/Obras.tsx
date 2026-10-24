import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, ExternalLink, MessageCircleQuestion, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { api, type Obra, type ObraDetalhe } from '../api'
import { Capa } from './Chat'
import { Carregando, Erro, classeCampo } from './comum'

/** Catálogo das obras do acervo. `id` vazio mostra a lista; senão, os detalhes da obra. */
export function Obras({ id }: { id: string }) {
  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:py-8">{id ? <Detalhe id={id} /> : <Lista />}</div>
  )
}

const normalizar = (s: string) => s.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase()

const autoria = (o: Obra) =>
  [o.autor, o.autor_espiritual && o.autor_espiritual !== o.autor ? o.autor_espiritual : null].filter(Boolean).join(' · ')

function Lista() {
  const q = useQuery({ queryKey: ['obras'], queryFn: api.obras })
  const [filtro, setFiltro] = useState('')
  const [colecao, setColecao] = useState('')

  // Coleções da maior para a menor, com "Outras" sempre no fim.
  const colecoes = useMemo(() => {
    const contagem = new Map<string, number>()
    for (const o of q.data ?? []) contagem.set(o.colecao, (contagem.get(o.colecao) ?? 0) + 1)
    return [...contagem].sort((a, b) => (a[0] === 'Outras' ? 1 : b[0] === 'Outras' ? -1 : b[1] - a[1]))
  }, [q.data])

  const visiveis = useMemo(() => {
    const termo = normalizar(filtro.trim())
    return (q.data ?? []).filter(
      (o) =>
        (!colecao || o.colecao === colecao) &&
        (!termo || normalizar(`${o.titulo} ${o.autor ?? ''} ${o.autor_espiritual ?? ''}`).includes(termo)),
    )
  }, [q.data, filtro, colecao])

  if (q.isLoading) return <Carregando texto="Carregando obras…" />
  if (q.isError) return <Erro erro={q.error} />

  return (
    <div className="space-y-5">
      <div className="relative">
        <Search className="pointer-events-none absolute top-1/2 left-4 size-4 -translate-y-1/2 text-suave" aria-hidden />
        <input
          type="search"
          value={filtro}
          onChange={(e) => setFiltro(e.target.value)}
          placeholder="Filtrar por título ou autor"
          aria-label="Filtrar obras"
          className={`${classeCampo} pl-10`}
        />
      </div>

      <div className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 sm:mx-0 sm:flex-wrap sm:px-0">
        {[['', q.data?.length ?? 0] as const, ...colecoes].map(([nome, total]) => (
          <button
            key={nome || 'todas'}
            type="button"
            onClick={() => setColecao(nome)}
            aria-pressed={colecao === nome}
            className="shrink-0 rounded-full border border-borda px-3 py-1.5 text-sm transition hover:bg-lateral aria-pressed:border-destaque aria-pressed:bg-destaque aria-pressed:text-sobre-destaque"
          >
            {nome || 'Todas'} <span className="opacity-60">{total}</span>
          </button>
        ))}
      </div>

      {visiveis.length === 0 ? (
        <p className="py-6 text-suave">Nenhuma obra encontrada.</p>
      ) : (
        <ul className="divide-y divide-borda overflow-hidden rounded-2xl border border-borda">
          {visiveis.map((o) => (
            <li key={o.id}>
              <a
                href={`#/obras/${encodeURIComponent(o.id)}`}
                className="flex items-center gap-4 px-4 py-3 transition hover:bg-lateral"
              >
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-medium">{o.titulo}</span>
                  <span className="block truncate text-sm text-suave">{autoria(o) || o.colecao}</span>
                </span>
                <span className="hidden shrink-0 text-right text-xs text-suave sm:block">
                  {o.ano && <span className="block">{o.ano}</span>}
                  {o.paginas && <span className="block">{o.paginas} p.</span>}
                </span>
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function Detalhe({ id }: { id: string }) {
  const q = useQuery({ queryKey: ['obra', id], queryFn: () => api.obra(id) })
  if (q.isLoading) return <Carregando texto="Carregando obra…" />
  if (q.isError) return <Erro erro={q.error} />
  const o = q.data!

  return (
    <div className="space-y-6">
      <a href="#/obras" className="inline-flex items-center gap-1.5 text-sm text-suave transition hover:text-texto">
        <ArrowLeft className="size-4" aria-hidden />
        Obras
      </a>

      <header className="flex items-start gap-4 sm:gap-5">
        <Capa id={o.id} tamanho="grande" />
        <div className="min-w-0 space-y-1">
          <p className="text-sm font-medium text-destaque">{o.colecao}</p>
          <h2 className="text-2xl font-semibold tracking-tight text-balance sm:text-3xl">{o.titulo}</h2>
          {autoria(o) && <p className="text-suave">{autoria(o)}</p>}
        </div>
      </header>

      <div className="flex flex-wrap gap-2">
        <a
          href={`#/perguntar/${encodeURIComponent(o.id)}`}
          className="inline-flex h-10 items-center gap-2 rounded-full bg-destaque px-4 text-sm font-medium text-sobre-destaque transition hover:bg-destaque-forte"
        >
          <MessageCircleQuestion className="size-4" aria-hidden />
          Perguntar sobre esta obra
        </a>
        <a
          href={`#/buscar/${encodeURIComponent(o.id)}`}
          className="inline-flex h-10 items-center gap-2 rounded-full border border-borda px-4 text-sm font-medium transition hover:bg-lateral"
        >
          <Search className="size-4" aria-hidden />
          Buscar nesta obra
        </a>
        {o.url_pdf && (
          <a
            href={o.url_pdf}
            target="_blank"
            rel="noreferrer"
            className="inline-flex h-10 items-center gap-2 rounded-full border border-borda px-4 text-sm font-medium transition hover:bg-lateral"
          >
            <ExternalLink className="size-4" aria-hidden />
            Abrir PDF
          </a>
        )}
      </div>

      <dl className="grid grid-cols-2 gap-x-6 gap-y-4 rounded-2xl border border-borda p-4 sm:grid-cols-3 sm:p-5">
        <Dado nome="Autor" valor={o.autor} />
        <Dado nome="Autor espiritual" valor={o.autor_espiritual} />
        <Dado nome="Médium" valor={o.medium !== o.autor ? o.medium : null} />
        <Dado nome="Tradutor" valor={o.tradutor} />
        <Dado nome="Ano" valor={o.ano} />
        <Dado nome="Páginas" valor={o.paginas} />
        <Dado nome="Trechos indexados" valor={o.trechos.toLocaleString('pt-BR')} />
        <Dado nome="Fonte" valor={FONTES[o.fonte] ?? o.fonte} />
      </dl>

      {o.sumario.length > 0 && <Sumario itens={o.sumario} />}
    </div>
  )
}

const FONTES: Record<string, string> = { feb: 'FEB', consolador: 'O Consolador', luzespirita: 'Luz Espírita' }

function Dado({ nome, valor }: { nome: string; valor: string | number | null }) {
  if (valor === null || valor === '') return null
  return (
    <div className="min-w-0">
      <dt className="text-xs text-suave">{nome}</dt>
      <dd className="truncate text-sm font-medium">{valor}</dd>
    </div>
  )
}

function Sumario({ itens }: { itens: ObraDetalhe['sumario'] }) {
  return (
    <section className="space-y-2">
      <h3 className="text-sm font-medium text-suave">Sumário</h3>
      <ol className="divide-y divide-borda rounded-2xl border border-borda">
        {itens.map((s, i) => (
          <li
            key={i}
            className={`flex items-baseline gap-3 py-2.5 pr-4 text-sm ${s.nivel > 1 ? 'text-texto/80' : 'font-medium'}`}
            style={{ paddingLeft: `${1 + (s.nivel - 1) * 1.25}rem` }}
          >
            <span className="min-w-0 flex-1">{s.titulo}</span>
            {s.pagina && <span className="shrink-0 text-xs text-suave tabular-nums">p. {s.pagina}</span>}
          </li>
        ))}
      </ol>
    </section>
  )
}
