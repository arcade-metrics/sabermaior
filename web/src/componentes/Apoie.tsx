import {
  Building2,
  Check,
  Copy,
  ExternalLink,
  FolderOpen,
  GitPullRequest,
  Heart,
  Lightbulb,
  Megaphone,
  MessageCircle,
  MessageSquareText,
  Share2,
  Target,
  type LucideIcon,
} from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { Cartao } from './comum'

// Quem mantém o site e recebe as doações.
const MANTENEDOR = {
  nome: 'ArcadeMetrics',
  razaoSocial: 'EDUARDO DATI DIAS - ME',
  cnpj: '67.496.225/0001-51',
  endereco: 'Av. Cinco de Novembro, 2103, Vila Nastri, Itapetininga, SP, 18207-320',
  email: 'edu@arcademetrics.com',
}

const PIX = {
  chave: '67496225000151', // CNPJ, só dígitos: é o formato que todo banco aceita ao colar
  // BR Code lido do QR original (images/chave-pix.png), CRC conferido. Sem valor fixo.
  // web/public/pix-qrcode.png é o mesmo código redesenhado em módulos quadrados,
  // porque o estilo de bolinhas do original não é lido por todos os apps.
  copiaECola:
    '00020101021126360014BR.GOV.BCB.PIX0114674962250001515204000053039865802BR592567.496.225 EDUARDO DATI D6012ITAPETININGA62070503***6304ADC1',
}

// Pasta pública do Google Drive, só leitura: comprovantes de entradas e gastos.
const PRESTACAO_DE_CONTAS = 'https://drive.google.com/drive/folders/1ZzeddySZomvNij_L5Z3R7NdkgHeknFwq?usp=sharing'

// Com `publico: false`, o cartão mostra "Em breve" em vez do link (que daria 404 num repositório privado).
const REPOSITORIO = { url: 'https://github.com/arcade-metrics/sabermaior', publico: true }

const DIVULGACAO = 'Saber Maior: estudo da literatura espírita com as fontes à vista, gratuito.'

/** Cartão no rodapé da barra lateral, logo acima da conta. */
export function CartaoApoie({ ativo }: { ativo: boolean }) {
  return (
    <div className="shrink-0 px-2 pb-2">
      <a
        href="#/apoie"
        aria-current={ativo ? 'page' : undefined}
        className="block rounded-xl border border-borda bg-caixa px-3 py-2.5 transition hover:border-destaque/50 aria-[current=page]:border-destaque/50"
      >
        <span className="flex items-center gap-2 text-sm font-medium">
          <Heart className="size-4 text-destaque" aria-hidden />
          Apoie o Saber Maior
        </span>
        <span className="mt-1 block text-xs text-suave">Gratuito, com contas abertas</span>
      </a>
    </div>
  )
}

/** Página #/apoie: Pix, prestação de contas, outras formas de ajudar e quem mantém. */
export function Apoie() {
  return (
    <div className="mx-auto w-full max-w-3xl space-y-8 px-4 py-6 sm:py-8">
      <section className="space-y-3">
        <h1 className="text-2xl font-semibold tracking-tight">Apoie o Saber Maior</h1>
        <p className="leading-7 text-texto/90">
          O Saber Maior é gratuito e vai continuar sendo. Hoje ele roda num servidor próprio, custeado pelo
          mantenedor. As doações servem para dar a ele uma estrutura independente, e tudo o que entra e sai fica
          registrado na prestação de contas, aberta a qualquer pessoa.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">A meta</h2>
        <Cartao className="flex gap-4 p-5">
          <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-xl bg-destaque/10 text-destaque">
            <Target className="size-5" aria-hidden />
          </span>
          <div className="min-w-0 space-y-2">
            <p className="leading-7 text-texto/90">
              Levar o Saber Maior para um servidor dedicado na nuvem, com placa de vídeo própria para o modelo de
              linguagem. Assim ele fica no ar o tempo todo, sem depender do equipamento de uma pessoa, e continua usando
              só IA aberta.
            </p>
            <p className="text-sm text-suave">Amazon AWS g6.xlarge (GPU NVIDIA L4, 24 GB) · cerca de US$ 600 por mês (aprox. R$ 3.300)</p>
          </div>
        </Cartao>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Doe com Pix</h2>
        <Cartao className="flex flex-col gap-5 p-5 sm:flex-row sm:items-center">
          {/* O QR fica sempre em fundo branco, mesmo no tema escuro, para os apps lerem. */}
          <img
            src="/pix-qrcode.png"
            alt="QR code Pix para doar ao Saber Maior"
            className="mx-auto size-48 shrink-0 rounded-xl border border-borda bg-white p-2 sm:mx-0"
          />
          <div className="min-w-0 flex-1 space-y-4">
            <div className="space-y-1.5">
              <p className="text-sm font-medium">Chave Pix (CNPJ)</p>
              <Copiar texto={PIX.chave} rotulo="Copiar chave">
                {MANTENEDOR.cnpj}
              </Copiar>
            </div>
            <div className="space-y-1.5">
              <p className="text-sm font-medium">Pix copia e cola</p>
              <Copiar texto={PIX.copiaECola} rotulo="Copiar código">
                {PIX.copiaECola}
              </Copiar>
            </div>
            <p className="text-xs leading-5 text-suave">
              O recebedor é <strong className="font-medium">{MANTENEDOR.razaoSocial}</strong> ({MANTENEDOR.nome}), CNPJ{' '}
              {MANTENEDOR.cnpj}. Confira esse nome no app do banco antes de confirmar. Você escolhe o valor.
            </p>
          </div>
        </Cartao>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Para onde vai o dinheiro</h2>
        <p className="leading-7 text-texto/90">
          As doações vão para essa estrutura: o servidor (banco de dados e API), o modelo de linguagem que redige as
          respostas e o domínio com backup. Os comprovantes de cada entrada e de cada gasto ficam numa pasta pública do Google Drive, só para
          visualização.
        </p>
        <p className="leading-7 text-texto/90">
          Se houver excedente, os valores serão doados integralmente a causas ligadas à educação, conforme o{' '}
          <a href="#/manifesto" className="font-medium text-destaque hover:underline">
            manifesto do Saber Maior
          </a>
          .
        </p>
        <a
          href={PRESTACAO_DE_CONTAS}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-4 rounded-2xl border border-borda p-4 transition hover:border-destaque/50 hover:bg-lateral"
        >
          <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-xl bg-destaque/10 text-destaque">
            <FolderOpen className="size-5" aria-hidden />
          </span>
          <span className="min-w-0 flex-1">
            <span className="block font-medium">Prestação de contas</span>
            <span className="block text-sm text-suave">Pasta no Google Drive, aberta e somente leitura</span>
          </span>
          <ExternalLink className="size-4 shrink-0 text-suave" aria-hidden />
        </a>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Outras formas de ajudar</h2>
        <div className="grid gap-2 sm:grid-cols-2">
          <Ajuda icone={Lightbulb} titulo="Envie perguntas" assunto="Sugestão de pergunta para o Saber Maior">
            Perguntas de estudo com a obra e o item certos ajudam a medir e melhorar as respostas.
          </Ajuda>
          <Ajuda icone={MessageSquareText} titulo="Revise respostas" assunto="Correção no Saber Maior">
            Encontrou uma citação errada ou uma fonte melhor? Escreva, que isso vira correção.
          </Ajuda>
          <CartaoCodigo />
          <CartaoDivulgue />
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Quem mantém</h2>
        <Cartao className="flex gap-4 p-5">
          <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-xl bg-destaque/10 text-destaque">
            <Building2 className="size-5" aria-hidden />
          </span>
          <div className="min-w-0 space-y-1 text-sm">
            <p className="text-base font-medium">{MANTENEDOR.nome}</p>
            <p>{MANTENEDOR.razaoSocial}</p>
            <p className="text-suave">CNPJ {MANTENEDOR.cnpj}</p>
            <p className="text-suave">{MANTENEDOR.endereco}</p>
            <a href={`mailto:${MANTENEDOR.email}`} className="inline-block font-medium text-destaque hover:underline">
              {MANTENEDOR.email}
            </a>
          </div>
        </Cartao>
      </section>
    </div>
  )
}

function Copiar({ texto, rotulo, children }: { texto: string; rotulo: string; children: ReactNode }) {
  const [copiado, setCopiado] = useState(false)
  function copiar() {
    navigator.clipboard.writeText(texto).then(() => {
      setCopiado(true)
      setTimeout(() => setCopiado(false), 2000)
    })
  }
  return (
    <div className="flex items-center gap-2 rounded-full border border-borda py-1 pr-1 pl-4">
      <span className="min-w-0 flex-1 truncate font-mono text-sm">{children}</span>
      <button
        type="button"
        onClick={copiar}
        className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-full px-3 text-sm text-suave transition hover:bg-lateral hover:text-texto"
      >
        {copiado ? <Check className="size-4" aria-hidden /> : <Copy className="size-4" aria-hidden />}
        {copiado ? 'Copiado' : rotulo}
      </button>
    </div>
  )
}

/** GitHub: código aberto, issues e pull requests. */
function CartaoCodigo() {
  const conteudo = (
    <>
      <span className="mb-2 flex items-center justify-between gap-2">
        <GitPullRequest className="size-5 text-destaque" aria-hidden />
        {!REPOSITORIO.publico && (
          <span className="rounded-full bg-destaque/10 px-2 py-0.5 text-xs font-medium text-destaque">Em breve</span>
        )}
      </span>
      <span className="block text-sm font-medium">Ajude a melhorar o código</span>
      <span className="mt-1 block text-sm text-suave">
        {REPOSITORIO.publico
          ? 'O código está aberto no GitHub: audite as respostas, aponte problemas e proponha melhorias.'
          : 'O código vai ser aberto no GitHub: qualquer pessoa poderá auditar as respostas, apontar problemas e propor melhorias.'}
      </span>
    </>
  )
  const classe = 'block rounded-2xl border border-borda p-4'
  return REPOSITORIO.publico ? (
    <a href={REPOSITORIO.url} target="_blank" rel="noreferrer" className={`${classe} transition hover:border-destaque/50`}>
      {conteudo}
    </a>
  ) : (
    <div className={classe}>{conteudo}</div>
  )
}

/** Divulgação: compartilhamento nativo (celular) ou cópia do link, e WhatsApp. */
function CartaoDivulgue() {
  const [copiado, setCopiado] = useState(false)
  const link = location.origin
  const botao =
    'inline-flex h-9 items-center gap-1.5 rounded-full border border-borda px-3 text-sm transition hover:border-destaque/50 hover:bg-lateral'

  async function compartilhar() {
    if (navigator.share) {
      // Cancelar a folha de compartilhamento rejeita a promessa; não é erro.
      await navigator.share({ title: 'Saber Maior', text: DIVULGACAO, url: link }).catch(() => {})
      return
    }
    await navigator.clipboard.writeText(`${DIVULGACAO} ${link}`)
    setCopiado(true)
    setTimeout(() => setCopiado(false), 2000)
  }

  return (
    <div className="rounded-2xl border border-borda p-4">
      <Megaphone className="mb-2 size-5 text-destaque" aria-hidden />
      <span className="block text-sm font-medium">Divulgue</span>
      <span className="mt-1 block text-sm text-suave">
        Conte para o seu grupo de estudo, centro espírita ou para quem gosta de ler as obras.
      </span>
      <div className="mt-3 flex flex-wrap gap-2">
        <button type="button" onClick={compartilhar} className={botao}>
          {copiado ? <Check className="size-4" aria-hidden /> : <Share2 className="size-4" aria-hidden />}
          {copiado ? 'Link copiado' : 'Compartilhar'}
        </button>
        <a
          href={`https://wa.me/?text=${encodeURIComponent(`${DIVULGACAO} ${link}`)}`}
          target="_blank"
          rel="noreferrer"
          className={botao}
        >
          <MessageCircle className="size-4" aria-hidden />
          WhatsApp
        </a>
      </div>
    </div>
  )
}

function Ajuda({ icone: Icone, titulo, assunto, children }: { icone: LucideIcon; titulo: string; assunto: string; children: ReactNode }) {
  return (
    <a
      href={`mailto:${MANTENEDOR.email}?subject=${encodeURIComponent(assunto)}`}
      className="block rounded-2xl border border-borda p-4 transition hover:border-destaque/50"
    >
      <Icone className="mb-2 size-5 text-destaque" aria-hidden />
      <span className="block text-sm font-medium">{titulo}</span>
      <span className="mt-1 block text-sm text-suave">{children}</span>
    </a>
  )
}
