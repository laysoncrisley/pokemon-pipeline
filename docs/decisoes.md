# Decisões sobre o dado

Cada decisão traz o motivo e, quando dá para medir, o número que a sustenta. Os números vêm da
extração de 2026-11-02 e podem ser refeitos com `python run_pipeline.py` (ver [conferencia.md](conferencia.md)).

## Extração e camada raw

### A camada raw não vai para o git
`data/raw/` tem cerca de 48 MB, porque cada JSON de `/pokemon` traz sprites e golpes de todas as versões do jogo (300 KB ou mais por arquivo). Como `python run_pipeline.py` recria tudo a partir da API em cerca de 2 minutos, versionar seria repetir dado público. Só `data/raw/.gitkeep` é commitado. O banco em `warehouse/` segue a mesma regra.

### O arquivo é igual ao que a API devolveu, byte a byte
O texto da resposta é gravado com `newline=""`, senão o Windows trocaria `\n` por `\r\n`. A gravação passa por um arquivo temporário, porque o cache decide só pela existência do arquivo e um JSON cortado por uma queda seria tratado como válido para sempre. A conferência compara o payload do banco com o arquivo em disco (0 diferenças). No início do projeto, dois arquivos também foram comparados com `cmp` contra um download feito com `curl`.

### Só erros transitórios são repetidos
Erro de conexão, HTTP 5xx e 429 ganham até 3 tentativas com espera crescente. Um 404 falha na hora, porque repetir não muda a resposta e só gasta a API, que é gratuita.

## Refined: unidades e campos

### Altura e peso convertidos
A API entrega `height` em decímetros e `weight` em hectogramas. Bulbasaur vem com `height: 7` e `weight: 69`, que viram 0,7 m e 6,9 kg. Os valores são gravados como `DECIMAL`, para 0,7 continuar sendo exatamente 0,7.

### Colunas que não têm o mesmo nome na API
- `special_attack` e `special_defense` vêm de `special-attack` e `special-defense`, com hífen.
- `min_level` vem de `level_learned_at`; `learn_method` vem de `move_learn_method.name`.
- `evolution_chain_id` não existe na API. `evolution_chain` só traz uma `url`, e o id é extraído dela. Uma url fora do formato gera erro, para não inventar um id.

### `min_level` fica 0 para quem não aprende por nível
Golpes de `machine` vêm com `level_learned_at = 0`. O valor foi mantido como veio. Ele não significa "nível zero": quer dizer que o nível não se aplica. Nenhum indicador usa essa coluna em média. Nas 4.128 linhas, nenhum `level-up` tem nível 0 e nenhum outro método tem nível diferente de 0.

## Refined: golpes

### Critério: só o version_group `red-blue`, distinto por golpe, método e nível
`moves[].version_group_details` repete o golpe para cada versão do jogo.

| Medida | Linhas |
|---|---:|
| Sem regra (todas as versões) | 163.908 |
| Distinto por Pokémon + golpe + método, somando todas as versões | 22.041 |
| Só `red-blue`, antes do distinto | 4.128 |
| Só `red-blue`, em `refined.pokemon_move` | 4.128 |

O distinto entre versões foi descartado porque misturaria golpes de jogos muito posteriores no retrato da 1ª geração, e continuaria dependendo de versão sem deixar isso visível. `red-blue` é o par de jogos original fora do Japão e cobre os 151 Pokémon (conferido: nenhum fica sem golpe). `yellow` daria 4.152 linhas e 164 golpes, mas tem conteúdo ajustado para o Pikachu.

Consequência: `golpes_distintos` no resumo é 163 e vale **para red-blue**, não para a franquia.

### O mesmo golpe em níveis diferentes não é duplicata
Em `red-blue`, 101 combinações de Pokémon + golpe + método aparecem em mais de um nível. Electrode com `sonic-boom` é um exemplo. Isso vem do dado do jogo: são dois momentos de aprendizado. Por isso `min_level` faz parte da chave. Sem ele, a chave primária recusaria a carga ou seria preciso apagar linhas legítimas.

### Método `stadium-surfing-pikachu` mantido
Existe uma linha com esse método (Pikachu com `surf`), vinda do Pokémon Stadium. Foi mantida porque está no version_group escolhido e não afeta nenhum indicador de forma relevante.

## Refined: tipos e dano

### Tipos, stats, habilidades e dano são os ATUAIS, não os de 1996
A API entrega o estado atual dos dados. Isso é uma decisão registrada, não um bug escondido.

- **Tipos:** 7 dos 151 têm `past_types`. Clefairy e Clefable eram normal e hoje são fairy. Jigglypuff, Wigglytuff e Mr. Mime ganharam fairy. Magnemite e Magneton ganharam steel. Fairy e steel nem existiam em 1996, mas aparecem nos indicadores.
- **Stats:** os 151 têm `past_stats`. Na 1ª geração existia só um atributo `special`, que depois foi dividido em ataque e defesa especiais. Alguns valores também mudaram nas gerações V e VI. Logo, `total_stats` não é o total que o jogo de 1996 mostrava.
- **Dano:** 7 tipos têm `past_damage_relations`. Ghost, por exemplo, não afetava psychic na 1ª geração e hoje causa 2x.
- **Habilidades:** o conceito nem existia em 1996. O indicador de habilidades descreve os 151 Pokémon pelas regras atuais.

**Motivo:** os dados atuais são os que a API oferece de forma completa e homogênea, e o objetivo é praticar o pipeline, não reconstituir 1996. Os campos `past_*` continuam intactos na camada raw para quem quiser refazer a análise.

**Limite que fica:** os golpes são de 1996 (`red-blue`) e o restante é atual. A mistura é consciente: para golpes a API exige escolher uma versão; para os demais campos, o atual é o padrão.

### Só tipos presentes nos 151
São 17 tipos. Ficam de fora `unknown`, `shadow` e `stellar`, como previsto, e também **`dark`**: nenhum dos 151 é dark, mas ele aparece em `damage_relations` dos outros tipos.

### `type_damage` usa só o sentido `*_to`
`damage_relations` guarda cada relação dos dois lados: fogo tem `double_damage_to: grass` e grass tem `double_damage_from: fire`. Ler os dois gravaria tudo em dobro. A leitura em `*_from` é usada só para conferir: dentro do escopo, os dois sentidos dão exatamente as mesmas 110 relações.

### Os dois lados do par precisam estar nos 151
Sem o filtro, o sentido `*_to` traz 115 linhas, com 5 em que `dark` é o defensor. Ficar só com os 17 tipos deixa 110.

**Efeito no indicador de fraquezas:** dark como atacante também não entra, então ghost aparece com 1 fraqueza (no jogo atual são 2) e psychic com 2 (no jogo atual são 3). A alternativa seria contar `dark` a partir do `*_from`, mas o indicador falaria de um tipo que não existe no escopo. O aviso está no painel e no comentário do `.sql`.

### Pares ausentes não são gravados
O par que não aparece vale 1.0, como definido no desafio. Gravá-los não acrescentaria informação.

## Refined: chaves e nulos

### `habitat` nulo continua nulo
A coluna aceita nulo e o código não inventa valor. Só o indicador `mart_habitat` mostra a linha "sem informação".

**Nos 151 de hoje, nenhum habitat vem nulo.** Portanto essa linha não aparece no resultado real. A regra está coberta por testes com dado inventado e continua pronta caso a API mude. Não foi criada uma linha zerada de propósito, porque a média dela seria nula e o painel mostraria uma categoria vazia.

### `pokemon_id` e `species_id` usados como chave do JOIN
Coincidem nos 151, mas isso não é garantido pela API em geral: outras formas de Pokémon têm ids acima de 10000. A conferência prova com anti-join nos dois sentidos (0 e 0) e com os nomes, que também são iguais.

### Chave primária nas tabelas refined
O grão de cada tabela vira `PRIMARY KEY`. Uma regra que deixe passar repetição faz a carga falhar, em vez de inflar os indicadores em silêncio.

## Marts

### Tipo duplo conta nos dois tipos
Em `mart_stats_por_tipo`, Charizard entra em fire e em flying. A pergunta é "como são os Pokémon deste tipo", e ele é dos dois. Por isso a soma de `qtd_pokemon` é 218, não 151.

### Lendário, mítico e comum são categorias separadas
A API separa `is_legendary` e `is_mythical`, e nenhum dos 151 tem os dois. Mew é mítico e não lendário, então `qtd_lendarios` é 4 (Articuno, Zapdos, Moltres e Mewtwo). Os grupos têm tamanhos muito diferentes (4, 1 e 146), e a média do mítico é só o valor do Mew.

### `capture_rate` maior significa captura mais fácil
A escala é contraintuitiva e está indicada no painel. Lendários têm média 3, comuns 109,43.

### Empates nos rankings
- **Top 10:** `ROW_NUMBER()` desempata por `pokemon_id`, para o resultado ser estável. Há empates dentro do ranking (600, 580, 540), mas não no corte: 10º tem 535 e o 11º tem 534.
- **Habilidades:** o desempate é por nome e **afeta o corte**. Oito habilidades empatam com 6 Pokémon, e só três cabem no top 15 (`guts`, `hustle`, `intimidate`). Ficam de fora `rivalry`, `shed-skin`, `static`, `sturdy` e `unnerve`, tão comuns quanto as três. Manteve-se o top 15 exato pedido; o aviso está no painel.

### "Separando ocultas e normais" vira duas colunas
`mart_habilidades_mais_comuns` tem 1 linha por habilidade, com o total e as colunas `qtd_como_normal` e `qtd_como_oculta`. A ordem é pelo total. A alternativa de dois rankings separados impediria ver a mesma habilidade nos dois papéis, como `swift-swim` (8 normal, 5 oculta).

### Cadeias de evolução só contam os 151
A cadeia do Eevee aparece com 4 membros, porque Espeon e os demais são de gerações posteriores. Pikachu também aparece sem Pichu. O indicador responde sobre o escopo do projeto. A coluna `membros` foi acrescentada porque só o id da cadeia não diz nada a quem lê.

### Médias com 2 casas, calculadas no SQL
O painel não pode calcular nem arredondar, então o valor já sai pronto do mart.

### Amostras pequenas
Ice lidera as médias de `total_stats` (514), mas tem só 5 Pokémon, entre eles Articuno e Lapras. Dragon, ghost e steel têm 3, 3 e 2. O painel mostra as quantidades na tabela para que a média não seja lida sozinha.

## Dashboard

### O painel só lê a camada marts
O código faz apenas `SELECT * FROM marts.<tabela>` com `read_only=True`. Sem groupby, média ou soma: os filtros escolhem linhas e o seletor escolhe qual coluna exibir. `sort_values` só ordena. Se alguém precisar de um número novo, ele nasce em `sql/marts`, testado.

### Conexão aberta só durante a leitura
O DuckDB no Windows bloqueia o arquivo. Abrir e fechar a cada leitura evita que um painel aberto impeça o `run_pipeline.py` de gravar.
