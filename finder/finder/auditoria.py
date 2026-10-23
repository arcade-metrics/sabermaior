"""Registro de cada busca: um JSON detalhado por busca em dados/buscas/ e uma
linha de resumo em dados/buscas.csv."""

import csv
import getpass
import json
import platform
import socket
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .rede import agora_utc, ip_local, ip_publico

COLUNAS_RESUMO = [
    "id_busca", "termo", "fontes", "inicio_utc", "fim_utc", "encontrados",
    "baixados", "ja_no_acervo", "erros", "ip_publico", "ip_local", "maquina", "arquivo",
]


class Busca:
    def __init__(self, raiz, termo, fontes, parametros, user_agent, consultar_ip_publico=True):
        self.raiz = Path(raiz)
        self.id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
        self.dados = {
            "id_busca": self.id,
            "termo": termo,
            "fontes": fontes,
            "parametros": parametros,
            "inicio_utc": agora_utc(),
            "fim_utc": None,
            "origem": {
                "maquina": socket.gethostname(),
                "usuario_so": getpass.getuser(),
                "ip_local": ip_local(),
                "ip_publico": ip_publico() if consultar_ip_publico else None,
                "sistema": platform.platform(),
                "python": platform.python_version(),
                "user_agent": user_agent,
            },
            "erros_fonte": {},
            "resultados": [],
            "requisicoes": [],
        }

    def resultado(self, obra, situacao, linha=None, erro=None):
        item = asdict(obra) | {"situacao": situacao, "data_hora_utc": agora_utc()}
        if linha:
            item |= {k: linha[k] for k in ("arquivo", "sha256", "bytes", "paginas", "imagens", "ip_servidor") if k in linha}
        if erro:
            item["erro"] = erro
        self.dados["resultados"].append(item)

    def erro_fonte(self, fonte, erro):
        self.dados["erros_fonte"][fonte] = erro

    def finalizar(self, requisicoes):
        self.dados["fim_utc"] = agora_utc()
        self.dados["requisicoes"] = requisicoes
        situacoes = [r["situacao"] for r in self.dados["resultados"]]
        self.dados["resumo"] = {
            "encontrados": len(situacoes),
            "baixados": situacoes.count("baixado"),
            "ja_no_acervo": situacoes.count("ja_no_acervo"),
            "erros": situacoes.count("erro"),
            "requisicoes": len(requisicoes),
        }

        pasta = self.raiz / "buscas"
        pasta.mkdir(parents=True, exist_ok=True)
        arquivo = pasta / f"{self.id}.json"
        arquivo.write_text(json.dumps(self.dados, ensure_ascii=False, indent=2), encoding="utf-8")

        tabela = self.raiz / "buscas.csv"
        novo = not tabela.exists()
        origem = self.dados["origem"]
        with open(tabela, "a", encoding="utf-8-sig" if novo else "utf-8", newline="") as f:
            w = csv.DictWriter(f, COLUNAS_RESUMO, delimiter=";")
            if novo:
                w.writeheader()
            w.writerow({
                "id_busca": self.id,
                "termo": self.dados["termo"] or "",
                "fontes": ",".join(self.dados["fontes"]),
                "inicio_utc": self.dados["inicio_utc"],
                "fim_utc": self.dados["fim_utc"],
                **{k: self.dados["resumo"][k] for k in ("encontrados", "baixados", "ja_no_acervo", "erros")},
                "ip_publico": origem["ip_publico"] or "",
                "ip_local": origem["ip_local"] or "",
                "maquina": origem["maquina"],
                "arquivo": arquivo.relative_to(self.raiz).as_posix(),
            })
        return arquivo
