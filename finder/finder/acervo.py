"""Acervo local: PDFs com o nome original, imagens extraídas e a tabela
catalogo.csv que associa cada arquivo à sua fonte."""

import csv
import hashlib
import mimetypes
import re
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

from .coleta import nome_arquivo
from .rede import agora_utc

COLUNAS = [
    "sha256", "fonte", "titulo", "categoria", "nome_original", "arquivo",
    "bytes", "paginas", "imagens", "pasta_imagens", "capa",
    "url_pdf", "url_final", "url_pagina", "url_capa",
    "data_hora_utc", "ip_servidor", "http_status", "content_type",
    "last_modified", "etag", "id_busca",
]


class ErroDownload(Exception):
    pass


def _seguro(nome):
    """Mantém o nome original, trocando só o que o Windows não aceita."""
    nome = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", nome).strip(" .")
    return nome or "sem_nome"


def _nome_content_disposition(valor):
    m = re.search(r"filename\*=(?:UTF-8'')?([^;]+)", valor or "", re.I)
    if m:
        return unquote(m.group(1).strip('"'))
    m = re.search(r'filename="?([^";]+)"?', valor or "", re.I)
    return m.group(1) if m else None


def _sha256(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def extrair_imagens(pdf, destino):
    """Salva as imagens embutidas no PDF. Devolve (páginas, imagens) ou
    (None, None) se o PyMuPDF não estiver instalado."""
    try:
        import pymupdf
    except ImportError:
        return None, None
    n = 0
    with pymupdf.open(pdf) as doc:
        vistos = set()
        for i, pagina in enumerate(doc, 1):
            for img in pagina.get_images(full=True):
                xref = img[0]
                if xref in vistos:
                    continue
                vistos.add(xref)
                info = doc.extract_image(xref)
                # Ignora pontos, linhas e ornamentos minúsculos.
                if not info or info["width"] < 32 or info["height"] < 32:
                    continue
                destino.mkdir(parents=True, exist_ok=True)
                (destino / f"p{i:04d}_x{xref}.{info['ext']}").write_bytes(info["image"])
                n += 1
        return doc.page_count, n


class Acervo:
    def __init__(self, raiz):
        self.raiz = Path(raiz)
        self.tabela = self.raiz / "catalogo.csv"
        self.linhas = []
        if self.tabela.exists():
            with open(self.tabela, encoding="utf-8-sig", newline="") as f:
                self.linhas = list(csv.DictReader(f, delimiter=";"))
        self._por_url = {l["url_pdf"]: l for l in self.linhas}

    def ja_tem(self, url_pdf):
        return self._por_url.get(url_pdf)

    def salvar(self):
        self.raiz.mkdir(parents=True, exist_ok=True)
        temp = self.tabela.with_suffix(".tmp")
        with open(temp, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, COLUNAS, delimiter=";", extrasaction="ignore")
            w.writeheader()
            w.writerows(self.linhas)
        temp.replace(self.tabela)

    def _destino_livre(self, pasta, nome, sha):
        """Mesmo nome e mesmo conteúdo: reaproveita. Mesmo nome e conteúdo
        diferente: acrescenta ' (2)', ' (3)'..."""
        caminho = pasta / nome
        n = 2
        while caminho.exists():
            if _sha256(caminho) == sha:
                return caminho, True
            caminho = pasta / f"{Path(nome).stem} ({n}){Path(nome).suffix}"
            n += 1
        return caminho, False

    def baixar(self, cliente, obra, id_busca, imagens=True):
        r = cliente.get(obra.url_pdf, stream=True)
        nome = _nome_content_disposition(r.headers.get("Content-Disposition")) or nome_arquivo(r.url) or nome_arquivo(obra.url_pdf)
        nome = _seguro(nome)
        if not nome.lower().endswith(".pdf"):
            nome += ".pdf"
        pasta = self.raiz / "pdfs" / obra.fonte
        pasta.mkdir(parents=True, exist_ok=True)
        parcial = pasta / (nome + ".part")
        try:
            h = hashlib.sha256()
            tamanho = 0
            with open(parcial, "wb") as f:
                for bloco in r.iter_content(1 << 16):
                    if tamanho == 0 and not bloco.lstrip().startswith(b"%PDF"):
                        raise ErroDownload(f"o servidor não devolveu um PDF ({r.headers.get('Content-Type')})")
                    f.write(bloco)
                    h.update(bloco)
                    tamanho += len(bloco)
        except BaseException:
            parcial.unlink(missing_ok=True)
            raise
        finally:
            r.close()

        sha = h.hexdigest()
        destino, repetido = self._destino_livre(pasta, nome, sha)
        if repetido:
            parcial.unlink()
        else:
            parcial.replace(destino)

        pasta_imagens = self.raiz / "imagens" / obra.fonte / destino.stem
        paginas = qtd_imagens = None
        if imagens:
            try:
                paginas, qtd_imagens = extrair_imagens(destino, pasta_imagens)
            except Exception as e:  # PDF corrompido ou fora do padrão
                qtd_imagens = f"erro: {e}"

        capa = ""
        if obra.url_capa:
            capa = self._baixar_capa(cliente, obra.url_capa, pasta_imagens)

        linha = {
            "sha256": sha,
            "fonte": obra.fonte,
            "titulo": obra.titulo,
            "categoria": obra.categoria,
            "nome_original": nome,
            "arquivo": destino.relative_to(self.raiz).as_posix(),
            "bytes": tamanho,
            "paginas": paginas if paginas is not None else "",
            "imagens": qtd_imagens if qtd_imagens is not None else "",
            "pasta_imagens": pasta_imagens.relative_to(self.raiz).as_posix() if pasta_imagens.exists() else "",
            "capa": capa,
            "url_pdf": obra.url_pdf,
            "url_final": r.url,
            "url_pagina": obra.url_pagina,
            "url_capa": obra.url_capa or "",
            "data_hora_utc": agora_utc(),
            "ip_servidor": r.ip_servidor or "",
            "http_status": r.status_code,
            "content_type": r.headers.get("Content-Type", ""),
            "last_modified": r.headers.get("Last-Modified", ""),
            "etag": r.headers.get("ETag", ""),
            "id_busca": id_busca,
        }
        self.linhas.append(linha)
        self._por_url[obra.url_pdf] = linha
        self.salvar()
        return linha

    def _baixar_capa(self, cliente, url, pasta):
        try:
            r = cliente.get(url)
        except Exception:
            return ""
        ext = PurePosixPath(urlsplit(r.url).path).suffix or mimetypes.guess_extension(
            r.headers.get("Content-Type", "").split(";")[0]) or ".img"
        pasta.mkdir(parents=True, exist_ok=True)
        caminho = pasta / f"capa{ext}"
        caminho.write_bytes(r.content)
        return caminho.relative_to(self.raiz).as_posix()
