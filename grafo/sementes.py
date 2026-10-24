"""Taxonomia semente do grafo (categoria > subcategoria > termo), extraída de:

Ragacini, L. A. Proposta de elaboração de um Tesauro Espírita: categorização
segundo as obras de Kardec. Novas Edições Acadêmicas, 2017 (Quadro 20/21).

"sinonimos" vêm dos pares USE/UP do autor (ex.: "Lei Natural" UP "Lei Divina").
"""

CATEGORIAS = [
    {
        "nome": "Tipos de medianimidade",
        "obra": "Livro dos Médiuns",
        "subcategorias": [
            {"nome": "Médiuns de efeitos físicos", "termos": [
                "Médiuns facultativos", "Médiuns involuntários", "Médiuns naturais", "Médium voluntário",
            ]},
            {"nome": "Médiuns sensitivos", "termos": ["Médiuns maleáveis"]},
            {"nome": "Médiuns audientes", "termos": []},
            {"nome": "Médiuns falantes", "termos": ["Médiuns versejadores", "Médiuns músicos", "Médiuns poliglotas"]},
            {"nome": "Médiuns videntes", "termos": ["Médiuns proféticos"]},
            {"nome": "Médiuns sonambúlicos", "termos": [
                "Sonâmbulo-médium", "Sonambulismo natural", "Sonambulismo magnético",
            ]},
            {"nome": "Médiuns curadores", "termos": ["Médiuns científicos", "Médiuns receitistas"]},
            {"nome": "Médiuns pneumatógrafos", "sinonimos": ["Médiuns escreventes"], "termos": [
                "Médiuns polígrafos", "Médiuns explícitos", "Médiuns psicógrafos", "Médiuns iletrados",
                "Médiuns lacônicos", "Médiuns poéticos", "Médiuns mecânicos", "Médiuns literários",
                "Médiuns intuitivos", "Médiuns semimecânicos",
            ]},
            {"nome": "Médiuns de pressentimentos", "sinonimos": ["Médiuns inspirados"], "termos": []},
            {"nome": "Médiuns especiais de efeitos físicos", "termos": [
                "Médiuns noturnos", "Médiuns de transporte", "Médiuns musicais", "Médiuns excitadores",
                "Médiuns calmos", "Médiuns convulsivos", "Médiuns velozes",
            ]},
            {"nome": "Médiuns especiais de efeitos intelectuais", "termos": [
                "Médiuns intelectuais", "Médiuns extáticos", "Médiuns pintores", "Médiuns desenhistas",
                "Médiuns improdutivos", "Médiuns formados", "Médiuns exclusivos", "Médiuns novatos",
                "Médiuns de evocação", "Médiuns espontâneos", "Médiuns positivos", "Médiuns incorretos",
                "Médiuns historiadores", "Médiuns triviais", "Médiuns religiosos", "Médiuns moralistas",
            ]},
            {"nome": "Mediunidade nos animais", "termos": []},
        ],
    },
    {
        "nome": "Influência moral do médium",
        "obra": "Livro dos Médiuns",
        "subcategorias": [
            {"nome": "Médiuns bons", "termos": ["Médiuns sérios", "Médiuns devotados", "Médiuns seguros"]},
            {"nome": "Médiuns imperfeitos", "termos": [
                "Médiuns obsidiados", "Médiuns fascinados", "Médiuns subjugados", "Médiuns levianos",
                "Médiuns indiferentes", "Médiuns orgulhosos", "Médiuns suscetíveis", "Médiuns mercenários",
                "Médiuns ambiciosos", "Médiuns de má-fé", "Médiuns egoístas", "Médiuns invejosos",
            ]},
        ],
    },
    {
        "nome": "Manifestações espirituais",
        "obra": "Livro dos Médiuns",
        "subcategorias": [
            {"nome": "Manifestações físicas", "sinonimos": ["Mesas girantes"], "termos": []},
            {"nome": "Manifestações físicas espontâneas", "termos": []},
            {"nome": "Manifestações visuais", "termos": []},
            {"nome": "Bicorporeidade", "sinonimos": ["Transfiguração"], "termos": []},
            {"nome": "Manifestações inteligentes", "termos": []},
        ],
    },
    {
        "nome": "Natureza das comunicações espirituais",
        "obra": "Livro dos Médiuns",
        "subcategorias": [
            {"nome": "Comunicações grosseiras", "termos": []},
            {"nome": "Comunicações frívolas", "termos": []},
            {"nome": "Comunicações sérias", "termos": []},
            {"nome": "Comunicações instrutivas", "termos": []},
        ],
    },
    {
        "nome": "Obsessões espirituais",
        "obra": "Livro dos Médiuns",
        "subcategorias": [
            {"nome": "Obsidiados", "termos": []},
            {"nome": "Subjugados", "termos": []},
            {"nome": "Fascinados", "termos": []},
        ],
    },
    {
        "nome": "Fraudes espíritas",
        "obra": "Livro dos Médiuns",
        "subcategorias": [
            {"nome": "Médiuns interesseiros", "termos": []},
            {"nome": "Charlatanismo", "termos": []},
        ],
    },
    {
        "nome": "Dissertações espíritas",
        "obra": "Livro dos Médiuns",
        "subcategorias": [
            {"nome": "Espiritismo como assunto", "termos": []},
            {"nome": "Mediunidade como assunto", "termos": []},
            {"nome": "Sociedades espíritas como assunto", "termos": []},
            {"nome": "Comunicações apócrifas como assunto", "termos": []},
        ],
    },
    {
        "nome": "Escala espírita",
        "obra": "Livro dos Espíritos",
        "subcategorias": [
            {"nome": "Terceira ordem", "sinonimos": ["Demônios"], "termos": [
                "Espíritos impuros", "Espíritos levianos", "Espíritos neutros",
                "Espíritos batedores e perturbadores",
            ]},
            {"nome": "Segunda ordem", "termos": [
                "Espíritos benévolos", "Espíritos sábios", "Espíritos de sabedoria", "Espíritos superiores",
            ]},
            {"nome": "Primeira ordem", "sinonimos": ["Anjos"], "termos": ["Espíritos perfeitos"]},
        ],
    },
    {
        "nome": "Princípio vital",
        "obra": "Livro dos Médiuns / Gênese",
        "subcategorias": [
            {"nome": "Seres orgânicos", "termos": []},
            {"nome": "Seres inorgânicos", "termos": []},
            {"nome": "Inteligência e instinto", "termos": []},
        ],
    },
    {
        "nome": "Elementos gerais do universo",
        "obra": "Livro dos Médiuns",
        "subcategorias": [
            {"nome": "Propriedades da matéria", "termos": []},
            {"nome": "Espaço universal", "termos": []},
            {"nome": "Mundo espiritual", "termos": []},
            {"nome": "Mundo corpóreo", "termos": []},
        ],
    },
    {
        "nome": "Composição espiritual",
        "obra": "Livro dos Espíritos",
        "subcategorias": [
            {"nome": "Espírito", "termos": [
                "Faculdades morais", "Faculdades intelectuais", "Visitas espíritas entre pessoas vivas",
                "Transmissão oculta do pensamento",
            ]},
        ],
    },
    {
        "nome": "Pluralidade de existências",
        "obra": "Livro dos Espíritos",
        "subcategorias": [
            {"nome": "Reencarnação", "termos": [
                "Recordação da existência corpórea", "Esquecimento do passado", "Simpatia e antipatia terrenas",
            ]},
            {"nome": "Encarnação", "termos": [
                "União entre alma e corpo", "Alma", "O sono e os sonhos", "Materialismo", "Perispírito",
            ]},
            {"nome": "Desencarnação", "termos": [
                "Separação entre alma e corpo", "Vida eterna", "Perturbação espiritual",
            ]},
        ],
    },
    {
        "nome": "Lei natural",
        "obra": "Livro dos Espíritos",
        "sinonimos": ["Lei divina"],
        "subcategorias": [
            {"nome": "Lei de adoração", "termos": []},
            {"nome": "Lei do trabalho", "termos": []},
            {"nome": "Lei de reprodução", "termos": []},
            {"nome": "Lei de conservação", "termos": []},
            {"nome": "Lei de destruição", "termos": []},
            {"nome": "Lei de sociedade", "termos": []},
            {"nome": "Lei do progresso", "termos": []},
            {"nome": "Lei de igualdade", "termos": []},
            {"nome": "Lei de liberdade", "termos": []},
            {"nome": "Lei de justiça, de amor e de caridade", "termos": []},
            {"nome": "Perfeição moral", "termos": []},
        ],
    },
    {
        "nome": "Penas e gozos",
        "obra": "Livro dos Espíritos",
        "subcategorias": [
            {"nome": "Penas e gozos terrestres", "termos": []},
            {"nome": "Penas e gozos futuros", "termos": []},
        ],
    },
    {
        "nome": "Gênese",
        "obra": "Gênese",
        "subcategorias": [
            {"nome": "Gênese orgânica", "termos": []},
            {"nome": "Gênese espiritual", "termos": []},
            {"nome": "Gênese moisaica", "termos": []},
        ],
    },
    {
        "nome": "Milagres do evangelho",
        "obra": "Evangelho Segundo o Espiritismo",
        "subcategorias": [
            {"nome": "Sonhos", "termos": []},
            {"nome": "Estrela dos magos", "termos": []},
            {"nome": "Dupla vista", "termos": []},
            {"nome": "Curas", "termos": []},
            {"nome": "Possessos", "termos": []},
            {"nome": "Ressurreições", "termos": []},
            {"nome": "Jesus caminha sobre a água", "termos": []},
            {"nome": "Transfiguração", "termos": []},
            {"nome": "Multiplicação dos pães", "termos": []},
            {"nome": "Aparição de Jesus após sua morte", "termos": []},
            {"nome": "Desaparecimento do corpo de Jesus", "termos": []},
        ],
    },
    {
        "nome": "Fluidos espirituais",
        "obra": "Gênese",
        "subcategorias": [
            {"nome": "Natureza dos fluidos", "termos": []},
            {"nome": "Propriedades dos fluidos", "termos": []},
        ],
    },
    {
        "nome": "Alternativas da humanidade",
        "obra": "Gênese",
        "subcategorias": [
            {"nome": "Doutrina materialista", "termos": []},
            {"nome": "Doutrina panteísta", "termos": []},
            {"nome": "Doutrina deísta", "termos": []},
            {"nome": "Doutrina dogmática", "termos": []},
        ],
    },
    {
        "nome": "Noções elementares de espiritismo",
        "obra": "Livro dos Espíritos",
        "subcategorias": [
            {"nome": "Doutrina espírita", "termos": []},
            {"nome": "Ciência espírita", "termos": []},
            {"nome": "Filosofia espírita", "termos": []},
            {"nome": "Espíritos", "termos": []},
            {"nome": "Espiritismo", "termos": []},
        ],
    },
]
