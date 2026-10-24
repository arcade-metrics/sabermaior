import { Library, Menu, PanelLeft, ScrollText, Search, SquarePen, Trash2, X, type LucideIcon } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useEffect, useState, type ReactNode } from 'react'
import { api } from './api'
import { Apoie, CartaoApoie } from './componentes/Apoie'
import { Buscar } from './componentes/Buscar'
import { Chat } from './componentes/Chat'
import { Conceitos } from './componentes/Conceitos'
import { Conta } from './componentes/Conta'
import { Manifesto } from './componentes/Manifesto'
import { Obras } from './componentes/Obras'
import { useConversas, useTema } from './estado'

// Rota no hash, para o botão Voltar funcionar sem roteador:
// #/ (nova conversa), #/perguntar/<obra> (nova conversa só sobre a obra), #/c/<id>, #/obras/<id>, #/buscar/<obra>, #/apoie, #/manifesto, #/conceitos/<id> (oculta do menu por enquanto)
type Rota = { tela: 'chat' | 'obras' | 'buscar' | 'apoie' | 'manifesto' | 'conceitos'; id: string; obra?: string }

function lerRota(): Rota {
  const [, tela = '', id = ''] = location.hash.split('/')
  const decodificado = decodeURIComponent(id)
  if (tela === 'obras' || tela === 'buscar') return { tela, id: decodificado }
  if (tela === 'apoie' || tela === 'manifesto') return { tela, id: '' }
  if (tela === 'perguntar') return { tela: 'chat', id: '', obra: decodificado }
  if (tela === 'conceitos') return { tela: 'conceitos', id: decodificado }
  return { tela: 'chat', id: tela === 'c' ? decodificado : '' }
}

const ir = (caminho: string) => (location.hash = caminho)

export default function App() {
  const [rota, setRota] = useState(lerRota)
  const [tema, setTema] = useTema()
  const { conversas, perguntar, tirarObra, apagar, apagarTudo } = useConversas()
  const [gaveta, setGaveta] = useState(false) // barra lateral no celular
  const [recolhida, setRecolhida] = useState(false) // barra lateral no desktop
  const [agentes, setAgentes] = useState(false) // fica ligado entre conversas, como uma ferramenta

  useEffect(() => {
    const aoMudar = () => {
      setRota(lerRota())
      setGaveta(false)
      document.querySelector('main')?.scrollTo({ top: 0 })
    }
    window.addEventListener('hashchange', aoMudar)
    return () => window.removeEventListener('hashchange', aoMudar)
  }, [])

  const conversa = rota.tela === 'chat' ? conversas.find((c) => c.id === rota.id) : undefined
  const titulo =
    rota.tela === 'obras' ? 'Obras' : rota.tela === 'buscar' ? 'Buscar trechos' : rota.tela === 'apoie' ? 'Apoie' : rota.tela === 'manifesto' ? 'Manifesto' : rota.tela === 'conceitos' ? 'Conceitos' : (conversa?.titulo ?? 'Saber Maior')

  // Filtro de obra: o da conversa aberta, ou o da nova conversa vinda de "Perguntar sobre esta obra".
  const novaObra = useQuery({ queryKey: ['obra', rota.obra], queryFn: () => api.obra(rota.obra!), enabled: !!rota.obra })
  const obra = conversa ? conversa.obra : novaObra.data && { id: novaObra.data.id, titulo: novaObra.data.titulo }

  function enviar(pergunta: string, agentes: boolean) {
    const id = perguntar(conversa?.id ?? '', pergunta, agentes, obra)
    if (id !== conversa?.id) ir(`/c/${id}`)
  }

  function semObra() {
    if (conversa) tirarObra(conversa.id)
    else ir('/')
  }

  function remover(id: string) {
    apagar(id)
    if (id === rota.id) ir('/')
  }

  const lateral = (
    <Lateral
      rota={rota}
      conversas={conversas}
      remover={remover}
      conta={<Conta tema={tema} setTema={setTema} apagarTudo={apagarTudo} totalConversas={conversas.length} />}
      fechar={() => (gaveta ? setGaveta(false) : setRecolhida(true))}
    />
  )

  return (
    <div className="flex h-dvh overflow-hidden">
      {/* Desktop: barra fixa, recolhível */}
      <aside
        className={`hidden shrink-0 overflow-hidden border-r border-borda bg-lateral transition-[width] duration-200 md:block ${
          recolhida ? 'w-0 border-r-0' : 'w-[260px]'
        }`}
      >
        <div className="h-full w-[260px]">{lateral}</div>
      </aside>

      {/* Celular: gaveta por cima do conteúdo */}
      <div className={`fixed inset-0 z-30 md:hidden ${gaveta ? '' : 'pointer-events-none'}`} aria-hidden={!gaveta}>
        <div
          className={`absolute inset-0 bg-black/40 transition-opacity ${gaveta ? 'opacity-100' : 'opacity-0'}`}
          onClick={() => setGaveta(false)}
        />
        <aside
          className={`absolute inset-y-0 left-0 w-[280px] max-w-[85vw] bg-lateral shadow-xl transition-transform duration-200 ${
            gaveta ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          {lateral}
        </aside>
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center gap-1 px-2 sm:px-3">
          <BotaoIcone rotulo="Abrir menu" onClick={() => setGaveta(true)} className="md:hidden">
            <Menu className="size-5" />
          </BotaoIcone>
          {recolhida && (
            <>
              <BotaoIcone rotulo="Mostrar barra lateral" onClick={() => setRecolhida(false)} className="hidden md:inline-flex">
                <PanelLeft className="size-5" />
              </BotaoIcone>
              <BotaoIcone rotulo="Nova conversa" onClick={() => ir('/')} className="hidden md:inline-flex">
                <SquarePen className="size-5" />
              </BotaoIcone>
            </>
          )}
          <span className="min-w-0 flex-1 truncate px-2 text-center font-medium md:text-left md:text-lg">{titulo}</span>
          <BotaoIcone rotulo="Nova conversa" onClick={() => ir('/')} className="md:hidden">
            <SquarePen className="size-5" />
          </BotaoIcone>
        </header>

        <main className="flex flex-1 flex-col overflow-y-auto">
          {rota.tela === 'chat' && (
            <Chat
              key={conversa?.id ?? `nova-${rota.obra ?? ''}`}
              conversa={conversa}
              perguntar={enviar}
              agentes={agentes}
              setAgentes={setAgentes}
              obra={obra}
              tirarObra={semObra}
            />
          )}
          {rota.tela === 'obras' && <Obras id={rota.id} />}
          {rota.tela === 'buscar' && <Buscar key={rota.id} obra={rota.id} />}
          {rota.tela === 'apoie' && <Apoie />}
          {rota.tela === 'manifesto' && <Manifesto />}
          {rota.tela === 'conceitos' && <Conceitos id={rota.id} ir={(id) => ir(`/conceitos/${encodeURIComponent(id)}`)} />}
        </main>
      </div>
    </div>
  )
}

type PropsLateral = {
  rota: Rota
  conversas: ReturnType<typeof useConversas>['conversas']
  remover: (id: string) => void
  conta: ReactNode
  fechar: () => void
}

function Lateral({ rota, conversas, remover, conta, fechar }: PropsLateral) {
  return (
    <nav className="flex h-full flex-col" aria-label="Navegação">
      <div className="flex h-14 shrink-0 items-center justify-between px-3">
        <a href="#/" className="flex items-center gap-2 rounded-lg px-1.5 py-1 font-semibold tracking-tight">
          <Logo />
          Saber Maior
        </a>
        <BotaoIcone rotulo="Fechar barra lateral" onClick={fechar}>
          <PanelLeft className="hidden size-5 md:block" />
          <X className="size-5 md:hidden" />
        </BotaoIcone>
      </div>

      <div className="space-y-0.5 px-2">
        <ItemLateral href="#/" icone={SquarePen} ativo={rota.tela === 'chat' && !rota.id}>
          Nova conversa
        </ItemLateral>
        <ItemLateral href="#/obras" icone={Library} ativo={rota.tela === 'obras'}>
          Obras
        </ItemLateral>
        <ItemLateral href="#/buscar" icone={Search} ativo={rota.tela === 'buscar'}>
          Buscar trechos
        </ItemLateral>
      </div>

      <div className="mt-5 min-h-0 flex-1 overflow-y-auto px-2 pb-2">
        {conversas.length > 0 && <p className="px-3 pb-1 text-xs font-medium text-suave">Conversas</p>}
        <ul className="space-y-0.5">
          {conversas.map((c) => (
            <li key={c.id} className="group relative">
              <a
                href={`#/c/${c.id}`}
                aria-current={rota.tela === 'chat' && rota.id === c.id ? 'page' : undefined}
                className="block truncate rounded-lg py-2 pr-9 pl-3 text-sm transition hover:bg-borda/60 aria-[current=page]:bg-borda"
              >
                {c.titulo}
              </a>
              <button
                type="button"
                onClick={() => remover(c.id)}
                aria-label={`Apagar conversa “${c.titulo}”`}
                className="absolute top-1/2 right-1.5 inline-flex size-7 -translate-y-1/2 items-center justify-center rounded-md text-suave opacity-100 transition group-hover:opacity-100 hover:text-erro md:opacity-0 md:focus:opacity-100"
              >
                <Trash2 className="size-4" aria-hidden />
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="shrink-0 px-2 pb-1">
        <ItemLateral href="#/manifesto" icone={ScrollText} ativo={rota.tela === 'manifesto'}>
          Manifesto
        </ItemLateral>
      </div>
      <CartaoApoie ativo={rota.tela === 'apoie'} />
      {conta}
    </nav>
  )
}

function ItemLateral({ href, icone: Icone, ativo, children }: { href: string; icone: LucideIcon; ativo: boolean; children: ReactNode }) {
  return (
    <a
      href={href}
      aria-current={ativo ? 'page' : undefined}
      className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition hover:bg-borda/60 aria-[current=page]:bg-borda"
    >
      <Icone className="size-4.5" aria-hidden />
      {children}
    </a>
  )
}

function BotaoIcone({ rotulo, onClick, className = '', children }: { rotulo: string; onClick: () => void; className?: string; children: ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={rotulo}
      title={rotulo}
      className={`inline-flex size-9 shrink-0 items-center justify-center rounded-lg text-suave transition hover:bg-borda/60 hover:text-texto ${className}`}
    >
      {children}
    </button>
  )
}

function Logo() {
  return (
    <span className="inline-flex size-7 items-center justify-center rounded-lg bg-destaque text-sobre-destaque">
      <svg viewBox="0 0 24 24" className="size-4.5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" aria-hidden>
        <path d="M4 6.5c2.6-1.3 5.3-1.3 8 0v12c-2.7-1.3-5.4-1.3-8 0zM20 6.5c-2.6-1.3-5.3-1.3-8 0v12c2.7-1.3 5.4-1.3 8 0z" />
      </svg>
    </span>
  )
}
