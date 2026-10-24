import { ArrowUp, Book, BookOpen,Bot, Check, ChevronDown, Copy, Sparkles, TriangleAlert, X } from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent } from 'react'
import Markdown from 'react-markdown'
import { api, type ObraRef, type Resposta } from '../api'
import type { Conversa, Rodada } from '../estado'
import { sortearSugestoes } from '../sugestoes'

type Props = {
  conversa?: Conversa
  perguntar: (pergunta: string, agentes: boolean) => void
  agentes: boolean
  setAgentes: (ligado: boolean) => void
  obra?: ObraRef // filtro em vigor: as perguntas só consultam essa obra
  tirarObra: () => void
}

export function Chat({ conversa, perguntar, agentes, setAgentes, obra, tirarObra }: Props) {
  const fim = useRef<HTMLDivElement>(null)
  const rodadas = conversa?.rodadas ?? []
  const ultima = rodadas.at(-1)
  const [sugestoes] = useState(sortearSugestoes)

  // Desce até a mensagem mais nova quando chega pergunta ou resposta.
  useEffect(() => {
    fim.current?.scrollIntoView({ behavior: 'smooth' })
  }, [rodadas.length, ultima?.resposta, ultima?.erro])

  if (!rodadas.length) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-4 pb-10">
        <h1 className="mb-8 text-center text-2xl font-semibold tracking-tight text-balance sm:text-3xl">
          {obra ? `O que você quer saber sobre ${obra.titulo}?` : 'Em que posso ajudar no seu estudo?'}
        </h1>
        <div className="w-full max-w-3xl">
          <Compositor {...{ perguntar, agentes, setAgentes, obra, tirarObra }} autoFocus />
          <div hidden={!!obra} className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
            {sugestoes.map((s) => (
              <button
                key={s.titulo}
                type="button"
                onClick={() => perguntar(s.pergunta, agentes)}
                className="rounded-2xl border border-borda px-3.5 py-3 text-left transition hover:bg-lateral"
              >
                <span className="block text-sm font-medium">{s.titulo}</span>
                <span className="mt-0.5 line-clamp-2 block text-xs text-suave">{s.pergunta}</span>
              </button>
            ))}
          </div>
          {/* No celular a barra lateral fica na gaveta; aqui o apoio continua à vista. */}
          <p className="mt-6 text-center text-xs text-suave md:hidden">
            Gratuito e mantido por doações ·{' '}
            <a href="#/apoie" className="font-medium text-destaque hover:underline">
              Apoie
            </a>
          </p>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="flex-1">
        <div className="mx-auto w-full max-w-3xl space-y-8 px-4 py-6 sm:py-8">
          {rodadas.map((r) => (
            <MensagemRodada key={r.id} r={r} />
          ))}
          <div ref={fim} />
        </div>
      </div>
      <div className="sticky bottom-0 bg-gradient-to-t from-fundo from-70% to-transparent pt-4">
        <div className="mx-auto w-full max-w-3xl px-4 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
          <Compositor {...{ perguntar, agentes, setAgentes, obra, tirarObra }} />
          <p className="mt-2 text-center text-xs text-suave">
            Respostas geradas a partir do acervo. Confira sempre as fontes citadas.
          </p>
        </div>
      </div>
    </>
  )
}

type PropsCompositor = Omit<Props, 'conversa'> & { autoFocus?: boolean }

function Compositor({ perguntar: aoEnviar, agentes, setAgentes, obra, tirarObra, autoFocus }: PropsCompositor) {
  const [texto, setTexto] = useState('')
  const campo = useRef<HTMLTextAreaElement>(null)

  // Cresce com o texto, até um limite.
  useEffect(() => {
    const el = campo.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }, [texto])

  function enviar(e?: FormEvent) {
    e?.preventDefault()
    const p = texto.trim()
    if (!p) return
    aoEnviar(p, agentes)
    setTexto('')
  }

  return (
    <form
      onSubmit={enviar}
      className="rounded-3xl border border-borda bg-caixa p-2 shadow-sm transition focus-within:border-destaque/50 focus-within:shadow-md"
    >
      <textarea
        ref={campo}
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) enviar(e)
        }}
        rows={1}
        autoFocus={autoFocus}
        placeholder={obra ? 'Pergunte sobre esta obra' : 'Pergunte sobre a doutrina espírita'}
        aria-label="Pergunta"
        className="block max-h-[200px] w-full resize-none bg-transparent px-3 py-2 text-base outline-none placeholder:text-suave"
      />
      <div className="flex items-center gap-2 pt-1">
        <button
          type="button"
          onClick={() => setAgentes(!agentes)}
          aria-pressed={agentes}
          title="Escolhe o Agente Histórico ou Doutrinário e confere as citações literais"
          className="inline-flex h-9 items-center gap-1.5 rounded-full border border-borda px-3 text-sm text-suave transition hover:bg-lateral aria-pressed:border-destaque/40 aria-pressed:bg-destaque/10 aria-pressed:text-destaque"
        >
          <Sparkles className="size-4" aria-hidden />
          Agentes
        </button>
        <div className="min-w-0 flex-1">{obra && <SeloObra obra={obra} tirar={tirarObra} />}</div>
        <button
          type="submit"
          disabled={!texto.trim()}
          aria-label="Enviar pergunta"
          className="inline-flex size-9 items-center justify-center rounded-full bg-destaque text-sobre-destaque transition hover:bg-destaque-forte disabled:bg-borda disabled:text-suave"
        >
          <ArrowUp className="size-5" aria-hidden />
        </button>
      </div>
    </form>
  )
}

/** Filtro de obra no campo de pergunta: capa, título e um ✕ para voltar a todo o acervo. */
function SeloObra({ obra, tirar }: { obra: ObraRef; tirar: () => void }) {
  return (
    <span className="inline-flex h-9 max-w-full items-center gap-2 rounded-full bg-destaque/10 py-1 pr-1 pl-1 text-sm text-destaque">
      <Capa id={obra.id} />
      <a href={`#/obras/${encodeURIComponent(obra.id)}`} className="truncate font-medium hover:underline" title={obra.titulo}>
        {obra.titulo}
      </a>
      <button
        type="button"
        onClick={tirar}
        aria-label="Remover filtro da obra e perguntar a todo o acervo"
        title="Perguntar a todo o acervo"
        className="inline-flex size-7 shrink-0 items-center justify-center rounded-full transition hover:bg-destaque/15"
      >
        <X className="size-4" aria-hidden />
      </button>
    </span>
  )
}

/** Miniatura da capa; sem o PDF na máquina (404), mostra o ícone de livro. */
const TAMANHOS_CAPA = {
  icone: { caixa: 'h-7 w-5 rounded-[3px]', livro: 'size-3' },
  lista: { caixa: 'h-14 w-10 rounded-md', livro: 'size-4' },
  card: { caixa: 'aspect-[2/3] w-full rounded-xl', livro: 'size-10' },
  grande: { caixa: 'h-36 w-24 rounded-lg', livro: 'size-8' },
}

/** Miniatura da 1ª página do PDF. O livro em azul suave aparece enquanto carrega e quando não há capa. */
export function Capa({ id, tamanho = 'icone' }: { id: string; tamanho?: keyof typeof TAMANHOS_CAPA }) {
  const [falhou, setFalhou] = useState(false)
  const t = TAMANHOS_CAPA[tamanho]
  return (
    <span
      className={`${t.caixa} relative flex shrink-0 items-center justify-center overflow-hidden border border-borda bg-gradient-to-br from-destaque/15 to-destaque/5 text-destaque/50 shadow-sm`}
    >
      <Book className={t.livro} strokeWidth={1.5} aria-hidden />
      {!falhou && (
        <img
          src={api.capa(id)}
          alt=""
          loading="lazy"
          onError={() => setFalhou(true)}
          className="absolute inset-0 size-full object-cover"
        />
      )}
    </span>
  )
}

function MensagemRodada({ r }: { r: Rodada }) {
  return (
    <div className="space-y-6">
      <div className="flex flex-col items-end gap-1">
        <p className="max-w-[85%] rounded-3xl bg-balao px-4 py-2.5 whitespace-pre-wrap sm:max-w-[75%]">{r.pergunta}</p>
        {r.obra && (
          <span className="flex max-w-[85%] items-center gap-1 text-xs text-suave">
            <BookOpen className="size-3 shrink-0" aria-hidden />
            <span className="truncate">Só em {r.obra.titulo}</span>
          </span>
        )}
      </div>
      {r.erro ? (
        <p className="flex items-start gap-2 text-sm text-erro">
          <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
          Não foi possível responder: {r.erro}
        </p>
      ) : r.resposta ? (
        <RespostaCitada r={r.resposta} prefixo={r.id} />
      ) : (
        <div className="flex items-center gap-2 text-sm text-suave" role="status">
          <span className="size-2.5 animate-pulse rounded-full bg-destaque" aria-hidden />
          Consultando o acervo{r.agentes ? ' com os agentes' : ''}…
        </div>
      )}
    </div>
  )
}

function RespostaCitada({ r, prefixo }: { r: Resposta; prefixo: string }) {
  const [aberta, setAberta] = useState<number | null>(null)
  const [copiado, setCopiado] = useState(false)
  const validas = new Map(r.fontes.map((f) => [f.numero, f]))

  function abrir(n: number) {
    setAberta(n)
    requestAnimationFrame(() =>
      document.getElementById(`fonte-${prefixo}-${n}`)?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }),
    )
  }

  async function copiar() {
    const fontes = r.fontes.map((f) => `[${f.numero}] ${f.referencia}`).join('\n')
    await navigator.clipboard.writeText(fontes ? `${r.resposta}\n\nFontes:\n${fontes}` : r.resposta)
    setCopiado(true)
    setTimeout(() => setCopiado(false), 1500)
  }

  // [2] vira um link markdown que o componente `a` abaixo transforma em marcador de citação.
  const md = r.resposta.replace(/\[(\d+)\]/g, '[$1](#cita-$1)')

  return (
    <div className="space-y-4">
      {r.agente && (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-destaque/10 px-2.5 py-1 text-xs font-medium text-destaque">
          <Bot className="size-3.5" aria-hidden />
          Agente {r.agente === 'historico' ? 'Histórico' : 'Doutrinário'}
        </span>
      )}

      <div className="space-y-4 leading-7">
        <Markdown
          components={{
            a: ({ href, children }) => {
              const n = Number(href?.match(/^#cita-(\d+)$/)?.[1])
              if (!n) return <a href={href} className="text-destaque underline">{children}</a>
              const fonte = validas.get(n)
              return (
                <button
                  type="button"
                  onClick={() => fonte && abrir(n)}
                  title={fonte ? fonte.referencia : 'Citação sem trecho correspondente'}
                  className={`mx-0.5 inline-flex h-5 min-w-5 -translate-y-px items-center justify-center rounded-full px-1.5 align-middle text-[0.7rem] font-semibold transition ${
                    fonte
                      ? 'bg-destaque/12 text-destaque hover:bg-destaque hover:text-sobre-destaque'
                      : 'bg-erro/12 text-erro line-through'
                  }`}
                >
                  {n}
                </button>
              )
            },
            ul: ({ children }) => <ul className="list-disc space-y-1.5 pl-6">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal space-y-1.5 pl-6">{children}</ol>,
            strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
            h1: ({ children }) => <h3 className="text-lg font-semibold">{children}</h3>,
            h2: ({ children }) => <h3 className="text-lg font-semibold">{children}</h3>,
            h3: ({ children }) => <h4 className="font-semibold">{children}</h4>,
            blockquote: ({ children }) => (
              <blockquote className="border-l-2 border-destaque/40 pl-4 text-texto/85 italic">{children}</blockquote>
            ),
          }}
        >
          {md}
        </Markdown>
      </div>

      {(r.invalidas.length > 0 || (r.citacoes_nao_confirmadas?.length ?? 0) > 0) && (
        <div className="space-y-1 rounded-xl bg-erro/8 px-3.5 py-2.5 text-sm text-erro">
          {r.invalidas.length > 0 && (
            <p className="flex gap-2">
              <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
              Citações sem trecho correspondente: {r.invalidas.join(', ')}
            </p>
          )}
          {r.citacoes_nao_confirmadas?.map((c) => (
            <p key={c} className="flex gap-2">
              <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
              Frase entre aspas não encontrada literalmente nos trechos: “{c}”
            </p>
          ))}
        </div>
      )}

      {r.fontes.length > 0 && (
        <div className="overflow-hidden rounded-2xl border border-borda">
          <h3 className="flex items-center gap-1.5 px-4 pt-3 pb-1 text-xs font-medium text-suave">
            <BookOpen className="size-3.5" aria-hidden />
            Fontes
          </h3>
          <ol className="divide-y divide-borda">
            {r.fontes.map((f) => (
              <li key={f.numero} id={`fonte-${prefixo}-${f.numero}`} className="scroll-mt-20 scroll-mb-40">
                <button
                  type="button"
                  onClick={() => setAberta(aberta === f.numero ? null : f.numero)}
                  aria-expanded={aberta === f.numero}
                  className="flex w-full items-start gap-3 px-4 py-2.5 text-left text-sm transition hover:bg-lateral"
                >
                  <span className="mt-px inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-destaque/12 px-1.5 text-[0.7rem] font-semibold text-destaque">
                    {f.numero}
                  </span>
                  <span className="flex-1">{f.referencia}</span>
                  <ChevronDown
                    className={`mt-0.5 size-4 shrink-0 text-suave transition ${aberta === f.numero ? 'rotate-180' : ''}`}
                    aria-hidden
                  />
                </button>
                {aberta === f.numero && (
                  <p className="px-4 pb-4 pl-12 text-[0.95rem] leading-7 whitespace-pre-line text-texto/90">
                    {f.conteudo}
                  </p>
                )}
              </li>
            ))}
          </ol>
        </div>
      )}

      <button
        type="button"
        onClick={copiar}
        aria-label="Copiar resposta"
        title="Copiar resposta com as fontes"
        className="inline-flex size-8 items-center justify-center rounded-lg text-suave transition hover:bg-lateral hover:text-texto"
      >
        {copiado ? <Check className="size-4" aria-hidden /> : <Copy className="size-4" aria-hidden />}
      </button>
    </div>
  )
}
