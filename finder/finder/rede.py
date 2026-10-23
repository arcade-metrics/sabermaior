"""Cliente HTTP cuidadoso para não ser bloqueado: intervalo aleatório entre
requisições ao mesmo host, respeito ao robots.txt, novas tentativas com espera
crescente (honrando Retry-After) e registro de cada requisição para auditoria."""

import random
import socket
import time
import urllib.robotparser
from datetime import datetime, timezone
from urllib.parse import urlsplit

import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
REPETIR_STATUS = {429, 500, 502, 503, 504}


class Bloqueado(Exception):
    """O site recusou o acesso (403) ou o robots.txt não permite a URL."""


def agora_utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ip_remoto(resposta, host):
    try:
        return resposta.raw._connection.sock.getpeername()[0]
    except Exception:
        try:
            return socket.getaddrinfo(host, None)[0][4][0]
        except OSError:
            return None


class Cliente:
    def __init__(self, intervalo=(3.0, 7.0), tentativas=5, timeout=60, user_agent=USER_AGENT):
        self.sessao = requests.Session()
        self.sessao.headers.update({
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.5",
        })
        self.user_agent = user_agent
        self.intervalo = intervalo
        self.tentativas = tentativas
        self.timeout = timeout
        self.requisicoes = []  # histórico para o arquivo de auditoria
        self._ultimo = {}
        self._robots = {}

    def _esperar(self, host):
        alvo = self._ultimo.get(host, 0.0) + random.uniform(*self.intervalo)
        falta = alvo - time.monotonic()
        if falta > 0:
            time.sleep(falta)
        self._ultimo[host] = time.monotonic()

    def _registrar(self, url, inicio, resposta=None, ip=None, erro=None):
        self.requisicoes.append({
            "data_hora_utc": inicio,
            "url": url,
            "url_final": resposta.url if resposta is not None else None,
            "status": resposta.status_code if resposta is not None else None,
            "ip_servidor": ip,
            "content_type": resposta.headers.get("Content-Type") if resposta is not None else None,
            "erro": erro,
        })

    def permitido(self, url):
        partes = urlsplit(url)
        base = f"{partes.scheme}://{partes.netloc}"
        robots = self._robots.get(base)
        if robots is None:
            robots = urllib.robotparser.RobotFileParser()
            self._esperar(partes.netloc)
            try:
                r = self.sessao.get(base + "/robots.txt", timeout=self.timeout)
                valido = r.status_code < 400 and "text/plain" in r.headers.get("Content-Type", "")
                # Sem robots.txt válido (404 ou página HTML no lugar), tudo é permitido.
                robots.parse(r.text.splitlines() if valido else [])
            except requests.RequestException:
                robots.parse([])
            self._robots[base] = robots
        return robots.can_fetch(self.user_agent, url)

    def get(self, url, stream=False):
        """GET com espera e novas tentativas. Com stream=True o corpo não é lido;
        o chamador deve fechar a resposta. A resposta ganha o atributo ip_servidor."""
        if not self.permitido(url):
            raise Bloqueado(f"robots.txt não permite {url}")
        host = urlsplit(url).netloc
        espera = 10.0
        erro = None
        for tentativa in range(1, self.tentativas + 1):
            self._esperar(host)
            inicio = agora_utc()
            try:
                r = self.sessao.get(url, timeout=self.timeout, stream=True)
            except requests.RequestException as e:
                erro = e
                self._registrar(url, inicio, erro=str(e))
            else:
                ip = _ip_remoto(r, host)
                self._registrar(url, inicio, r, ip)
                if r.status_code == 403:
                    r.close()
                    raise Bloqueado(f"HTTP 403 em {url}: o servidor recusou o acesso")
                if r.status_code not in REPETIR_STATUS:
                    r.ip_servidor = ip
                    try:
                        r.raise_for_status()
                    except requests.HTTPError:
                        r.close()
                        raise
                    if not stream:
                        r.content  # lê o corpo e libera a conexão
                    return r
                erro = requests.HTTPError(f"HTTP {r.status_code} em {url}", response=r)
                retry_after = r.headers.get("Retry-After", "")
                if retry_after.isdigit():
                    espera = max(espera, float(retry_after))
                r.close()
            if tentativa < self.tentativas:
                time.sleep(espera + random.uniform(0, espera / 2))
                espera *= 2
        raise erro


def ip_publico(timeout=10):
    try:
        return requests.get("https://api.ipify.org?format=json", timeout=timeout).json()["ip"]
    except Exception:
        return None


def ip_local():
    # Conectar um socket UDP não envia pacotes; só descobre a interface de saída.
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return None
