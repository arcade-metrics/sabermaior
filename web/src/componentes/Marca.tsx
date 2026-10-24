import logoClaro from '../assets/marca/logo-saber-maior-light.svg'
import logoEscuro from '../assets/marca/logo-saber-maior-dark.svg'
import simboloClaro from '../assets/marca/logo-saber-maior-simbolo-light.svg'
import simboloEscuro from '../assets/marca/logo-saber-maior-simbolo-dark.svg'

// Originais em images/brand; cada peça tem versão clara e escura, trocadas pelo tema.

/** Livro com coração, sem o nome: barra lateral e lugares pequenos. */
export function Simbolo({ className = '' }: { className?: string }) {
  return <ParTemas claro={simboloClaro} escuro={simboloEscuro} alt="" className={className} />
}

/** Símbolo com o nome: página inicial. */
export function Logotipo({ className = '' }: { className?: string }) {
  return <ParTemas claro={logoClaro} escuro={logoEscuro} alt="Saber Maior" className={className} />
}

function ParTemas({ claro, escuro, alt, className }: { claro: string; escuro: string; alt: string; className: string }) {
  return (
    <>
      <img src={claro} alt={alt} className={`escuro:hidden ${className}`} />
      <img src={escuro} alt={alt} className={`hidden escuro:block ${className}`} />
    </>
  )
}
