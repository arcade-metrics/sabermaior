import {
  ChevronsUpDown,
  CircleHelp,
  Database,
  Heart,
  LogOut,
  Monitor,
  Moon,
  Settings,
  SlidersHorizontal,
  Sun,
  UserRound,
  X,
  type LucideIcon,
} from 'lucide-react'
import { useEffect, useRef, useState, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import type { Tema } from '../estado'

// Placeholder até existir login de verdade.
const USUARIO = { nome: 'Nome do Usuário', email: 'usuario@example.com', plano: 'Acesso de teste' }

const TEMAS: [Tema, LucideIcon, string][] = [
  ['claro', Sun, 'Claro'],
  ['escuro', Moon, 'Escuro'],
  ['sistema', Monitor, 'Sistema'],
]

type Props = { tema: Tema; setTema: (t: Tema) => void; apagarTudo: () => void; totalConversas: number }

/** Rodapé da barra lateral: avatar e nome; ao clicar, abre o menu da conta. */
export function Conta(props: Props) {
  const [menu, setMenu] = useState(false)
  const [config, setConfig] = useState(false)
  const caixa = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!menu) return
    const fora = (e: PointerEvent) => !caixa.current?.contains(e.target as Node) && setMenu(false)
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && setMenu(false)
    document.addEventListener('pointerdown', fora)
    document.addEventListener('keydown', esc)
    return () => {
      document.removeEventListener('pointerdown', fora)
      document.removeEventListener('keydown', esc)
    }
  }, [menu])

  return (
    <div ref={caixa} className="relative shrink-0 border-t border-borda p-2">
      {menu && (
        <div
          role="menu"
          className="absolute inset-x-2 bottom-full mb-1 overflow-hidden rounded-2xl border border-borda bg-caixa py-1.5 shadow-lg"
        >
          <div className="flex items-center gap-3 px-3 py-2">
            <Avatar />
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{USUARIO.nome}</p>
              <p className="truncate text-xs text-suave">{USUARIO.email}</p>
            </div>
          </div>
          <Separador />
          <div className="px-3 py-2">
            <p className="mb-1.5 text-xs text-suave">Tema</p>
            <SeletorTema tema={props.tema} setTema={props.setTema} />
          </div>
          <Separador />
          <ItemMenu
            icone={Settings}
            onClick={() => {
              setMenu(false)
              setConfig(true)
            }}
          >
            Configurações
          </ItemMenu>
          <ItemMenu icone={CircleHelp} onClick={() => setMenu(false)}>
            Ajuda
          </ItemMenu>
          <ItemMenu
            icone={Heart}
            onClick={() => {
              setMenu(false)
              location.hash = '/apoie'
            }}
          >
            Apoie o projeto
          </ItemMenu>
          <Separador />
          <ItemMenu icone={LogOut} onClick={() => setMenu(false)}>
            Sair
          </ItemMenu>
        </div>
      )}

      <button
        type="button"
        onClick={() => setMenu(!menu)}
        aria-haspopup="menu"
        aria-expanded={menu}
        className="flex w-full items-center gap-3 rounded-xl p-2 text-left transition hover:bg-borda/60 aria-expanded:bg-borda/60"
      >
        <Avatar />
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-medium">{USUARIO.nome}</span>
          <span className="block truncate text-xs text-suave">{USUARIO.plano}</span>
        </span>
        <ChevronsUpDown className="size-4 shrink-0 text-suave" aria-hidden />
      </button>

      {/* Portal: a gaveta do celular usa transform, que prenderia o `fixed` dentro dela. */}
      {config && createPortal(<Configuracoes {...props} fechar={() => setConfig(false)} />, document.body)}
    </div>
  )
}

function Avatar({ grande = false }: { grande?: boolean }) {
  const iniciais = USUARIO.nome
    .split(' ')
    .filter((p) => p.length > 2)
    .map((p) => p[0])
    .slice(0, 2)
    .join('')
  return (
    <span
      aria-hidden
      className={`inline-flex shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-sky-400 to-blue-700 font-semibold text-white ${
        grande ? 'size-14 text-lg' : 'size-8 text-xs'
      }`}
    >
      {iniciais}
    </span>
  )
}

function SeletorTema({ tema, setTema }: Pick<Props, 'tema' | 'setTema'>) {
  return (
    <div className="grid grid-cols-3 gap-1 rounded-xl bg-borda/50 p-1" role="radiogroup" aria-label="Tema">
      {TEMAS.map(([valor, Icone, nome]) => (
        <button
          key={valor}
          type="button"
          role="radio"
          aria-checked={tema === valor}
          onClick={() => setTema(valor)}
          className="flex items-center justify-center gap-1.5 rounded-lg py-1.5 text-xs text-suave transition hover:text-texto aria-checked:bg-caixa aria-checked:font-medium aria-checked:text-texto aria-checked:shadow-sm"
        >
          <Icone className="size-3.5" aria-hidden />
          {nome}
        </button>
      ))}
    </div>
  )
}

function ItemMenu({ icone: Icone, onClick, children }: { icone: LucideIcon; onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      role="menuitem"
      onClick={onClick}
      className="flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm transition hover:bg-lateral"
    >
      <Icone className="size-4 text-suave" aria-hidden />
      {children}
    </button>
  )
}

const Separador = () => <div className="my-1 border-t border-borda" />

type Aba = 'geral' | 'dados' | 'conta'
const ABAS: [Aba, LucideIcon, string][] = [
  ['geral', SlidersHorizontal, 'Geral'],
  ['dados', Database, 'Dados'],
  ['conta', UserRound, 'Conta'],
]

function Configuracoes({ tema, setTema, apagarTudo, totalConversas, fechar }: Props & { fechar: () => void }) {
  const [aba, setAba] = useState<Aba>('geral')

  useEffect(() => {
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && fechar()
    document.addEventListener('keydown', esc)
    return () => document.removeEventListener('keydown', esc)
  }, [fechar])

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 sm:items-center sm:p-4" onClick={fechar}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-config"
        onClick={(e) => e.stopPropagation()}
        className="flex max-h-[90dvh] w-full flex-col overflow-hidden rounded-t-3xl bg-caixa shadow-2xl sm:max-w-2xl sm:rounded-3xl"
      >
        <div className="flex items-center justify-between border-b border-borda px-5 py-4">
          <h2 id="titulo-config" className="text-lg font-semibold">
            Configurações
          </h2>
          <button
            type="button"
            onClick={fechar}
            aria-label="Fechar"
            className="inline-flex size-8 items-center justify-center rounded-lg text-suave transition hover:bg-lateral hover:text-texto"
          >
            <X className="size-5" aria-hidden />
          </button>
        </div>

        <div className="flex min-h-0 flex-1 flex-col sm:min-h-80 sm:flex-row">
          <nav className="flex gap-1 overflow-x-auto border-b border-borda p-2 sm:w-44 sm:flex-col sm:border-r sm:border-b-0">
            {ABAS.map(([valor, Icone, nome]) => (
              <button
                key={valor}
                type="button"
                onClick={() => setAba(valor)}
                aria-current={aba === valor ? 'page' : undefined}
                className="flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-sm transition hover:bg-lateral aria-[current=page]:bg-borda/60 aria-[current=page]:font-medium"
              >
                <Icone className="size-4" aria-hidden />
                {nome}
              </button>
            ))}
          </nav>

          <div className="flex-1 divide-y divide-borda overflow-y-auto px-5">
            {aba === 'geral' && (
              <Linha titulo="Tema" descricao="Claro, escuro ou igual ao do sistema.">
                <div className="w-64 max-w-full">
                  <SeletorTema tema={tema} setTema={setTema} />
                </div>
              </Linha>
            )}
            {aba === 'dados' && (
              <Linha
                titulo="Histórico de conversas"
                descricao={`${totalConversas} conversa(s) guardada(s) só neste navegador.`}
              >
                <button
                  type="button"
                  disabled={!totalConversas}
                  onClick={() => confirm('Apagar todas as conversas deste navegador?') && apagarTudo()}
                  className="rounded-full border border-erro/40 px-4 py-1.5 text-sm font-medium text-erro transition hover:bg-erro/10 disabled:opacity-40"
                >
                  Apagar tudo
                </button>
              </Linha>
            )}
            {aba === 'conta' && (
              <>
                <div className="flex items-center gap-4 py-4">
                  <Avatar grande />
                  <div className="min-w-0">
                    <p className="truncate font-medium">{USUARIO.nome}</p>
                    <p className="truncate text-sm text-suave">{USUARIO.email}</p>
                  </div>
                </div>
                <Linha titulo="Plano" descricao={USUARIO.plano}>
                  <span className="text-xs text-suave">Login ainda não implementado</span>
                </Linha>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function Linha({ titulo, descricao, children }: { titulo: string; descricao: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="text-sm font-medium">{titulo}</p>
        <p className="text-sm text-suave">{descricao}</p>
      </div>
      {children}
    </div>
  )
}
