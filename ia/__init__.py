"""Acesso à IA (local ou remota) por uma API compatível com OpenAI.

    from ia import IA
    ia = IA()
    ia.chat([{"role": "user", "content": "Olá"}])
    ia.embed(["texto"])
"""

from .clientes import IA, ErroIA
from .config import Config, carregar
