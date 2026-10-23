# finder

Busca e baixa obras espíritas em domínio público de:

- `consolador`: biblioteca virtual de O Consolador
- `feb`: downloads da FEB (as categorias administrativas ficam de fora, veja `IGNORAR` em `finder/fontes/feb.py`)
- `luzespirita`: PDFs citados nos verbetes da enciclopédia do Luz Espírita

## Uso

```
pip install -r requirements.txt
python -m finder "evangelho"                     # busca em todas as fontes e baixa
python -m finder "revista espirita" --fontes consolador --limite 3
python -m finder kardec --listar                 # só lista, não baixa
python -m finder --help
```

O termo é procurado sem acento e sem diferenciar maiúsculas no título, na categoria e no nome do arquivo. Sem termo, a busca traz tudo.

Para evitar bloqueio: uma requisição por vez, de 3 a 7 segundos entre requisições ao mesmo site (`--intervalo`), respeito ao robots.txt, novas tentativas com espera crescente em 429/5xx e parada da fonte em 403. PDFs que já estão no acervo não são baixados de novo.

## Saída (`dados/`)

| Caminho | Conteúdo |
|---|---|
| `pdfs/<fonte>/<nome original>.pdf` | O PDF. Se já existir outro arquivo com o mesmo nome e conteúdo diferente, ganha ` (2)`. |
| `imagens/<fonte>/<nome do pdf>/` | Imagens embutidas no PDF (`p<página>_x<id>.<ext>`) e `capa.*` quando a página da fonte mostra uma capa. |
| `catalogo.csv` | Uma linha por PDF: fonte, título, categoria, arquivo, sha256, páginas, nº de imagens, URLs de origem, data e hora (UTC), IP do servidor, cabeçalhos HTTP e o id da busca que o baixou. |
| `buscas/<id>.json` | Registro de cada busca: termo, parâmetros, início e fim (UTC), máquina, usuário, IP local e público, cada resultado e cada requisição HTTP feita (data e hora, URL, status, IP do servidor). |
| `buscas.csv` | Resumo de uma linha por busca. |

Os CSVs usam `;` e UTF-8 com BOM para abrir direto no Excel. O IP público é obtido em api.ipify.org; use `--sem-ip-publico` para não consultar.
