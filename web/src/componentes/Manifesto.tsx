import type { ReactNode } from 'react'

// Página #/manifesto. Texto em versões: ao mudar um princípio, suba a versão e a data.
const VERSAO = { numero: '0.1', data: 'outubro de 2026' }

export function Manifesto() {
  return (
    <article className="mx-auto w-full max-w-2xl px-5 py-10 sm:py-16">
      <header className="space-y-5 border-b border-borda pb-10">
        <p className="text-sm font-medium tracking-wide text-destaque uppercase">Manifesto</p>
        <h1 className="text-3xl leading-tight font-semibold tracking-tight text-balance sm:text-4xl">
          Estudar com fontes à vista, de graça e em aberto.
        </h1>
        <p className="text-lg leading-8 text-texto/85">
          O Saber Maior é um assistente de estudo da literatura espírita. Ele responde perguntas a partir das obras e
          mostra, em cada frase, de onde tirou o que diz.
        </p>
        <p className="rounded-2xl bg-balao px-4 py-3 text-sm leading-6">
          <strong className="font-semibold">Versão {VERSAO.numero}, {VERSAO.data}.</strong> Esta é a primeira versão,
          escrita para termos algo no ar. Ela vai mudar com o uso, com as críticas e com quem quiser construir junto.
        </p>
      </header>

      <ol className="divide-y divide-borda">
        <Principio n={1} titulo="Toda resposta mostra de onde veio">
          Cada afirmação traz o número do trecho que a sustenta, e um toque abre o texto original, com obra, capítulo e
          página. Se o acervo não basta para responder, a resposta deve dizer isso, e não preencher a lacuna com
          invenção.
        </Principio>

        <Principio n={2} titulo="Uma ferramenta de estudo, não uma autoridade">
          A inteligência artificial erra. Ela resume, aproxima, às vezes escolhe mal o trecho. Por isso as fontes estão
          sempre à vista: a palavra final é das obras e de quem as lê. O Saber Maior não substitui a leitura, o grupo de
          estudo nem a reflexão de cada um.
        </Principio>

        <Principio n={3} titulo="Código aberto e respostas auditáveis">
          Queremos que qualquer pessoa possa verificar como uma resposta foi produzida: que trechos foram buscados, como
          foram escolhidos, com que instruções o modelo escreveu. Isso vale para o código, para o processo de busca e
          para o conjunto de perguntas usado para medir a qualidade.
          <Nota>
            O código está aberto em{' '}
            <a
              href="https://github.com/arcade-metrics/sabermaior"
              target="_blank"
              rel="noreferrer"
              className="font-medium text-destaque hover:underline"
            >
              github.com/arcade-metrics/sabermaior
            </a>
            . Nesta primeira versão ele ainda está sendo organizado, e documentar o processo de ponta a ponta faz parte
            do compromisso.
          </Nota>
        </Principio>

        <Principio n={4} titulo="Método científico, inclusive sobre nós mesmos">
          Medimos antes de afirmar. Cada mudança na busca ou nas respostas é testada contra um conjunto de perguntas com
          resposta conhecida, e os números ficam registrados, os bons e os ruins. Quando algo piora o resultado, sai,
          mesmo que pareça uma boa ideia. Erros encontrados viram correções públicas.
        </Principio>

        <Principio n={5} titulo="Respeito às obras e aos autores">
          Não reescrevemos as obras. As citações são literais, sempre com referência e com acesso ao arquivo original.
          As obras vêm de editoras e sites espíritas que as distribuem gratuitamente, e o crédito é deles.
        </Principio>

        <Principio n={6} titulo="Gratuito, sem anúncios e sem venda de dados">
          O Saber Maior é e continuará gratuito. Não exibe anúncios e não vende dados de ninguém. Hoje, o histórico das
          suas conversas fica guardado apenas no seu navegador.
        </Principio>

        <Principio n={7} titulo="Dinheiro com transparência">
          As doações pagam os custos de manter o site no ar: servidor, modelo de linguagem e domínio. Cada entrada e
          cada gasto ficam numa prestação de contas pública. Se sobrar dinheiro, o excedente será doado integralmente a
          causas ligadas à educação.
          <p className="mt-3">
            <a href="#/apoie" className="font-medium text-destaque hover:underline">
              Ver como apoiar e a prestação de contas
            </a>
          </p>
        </Principio>

        <Principio n={8} titulo="Construído em conjunto">
          Perguntas de estudo, correções de citações e críticas a este texto são bem-vindas. Escreva para{' '}
          <a href="mailto:edu@arcademetrics.com" className="font-medium text-destaque hover:underline">
            edu@arcademetrics.com
          </a>
          .
        </Principio>
      </ol>

      <footer className="border-t border-borda pt-8 text-sm text-suave">
        <p>Mantido pela ArcadeMetrics, em Itapetininga, SP.</p>
        <p>
          Manifesto Saber Maior, versão {VERSAO.numero}, {VERSAO.data}.
        </p>
      </footer>
    </article>
  )
}

function Principio({ n, titulo, children }: { n: number; titulo: string; children: ReactNode }) {
  return (
    <li className="grid gap-x-6 gap-y-2 py-8 sm:grid-cols-[3rem_1fr]">
      <span className="text-3xl leading-none font-semibold text-destaque tabular-nums sm:text-4xl" aria-hidden>
        {String(n).padStart(2, '0')}
      </span>
      <div className="space-y-2">
        <h2 className="text-lg font-semibold tracking-tight">{titulo}</h2>
        <div className="leading-7 text-texto/85">{children}</div>
      </div>
    </li>
  )
}

function Nota({ children }: { children: ReactNode }) {
  return <p className="mt-3 border-l-2 border-destaque/40 pl-3 text-sm leading-6 text-suave">{children}</p>
}
