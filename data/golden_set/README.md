# Golden Set — Datathon 7MLET Grupo 68

Conjunto de avaliação do sistema MAB. Contém o **catálogo de ofertas** (fonte única de verdade dos braços), a **amostra de clientes** para testes e a documentação da conexão entre os dois.

> **Novidade desta versão:** o `offer_catalog.json` agora está versionado e completo (v2.0.0), com recompensa **composta** (receita + conversão), moduladores contínuos de contexto e parâmetros por braço para os três algoritmos. Há também um notebook de simulação end-to-end que consome o catálogo (`notebooks/datathon_mab_catalogo_linucb.ipynb`).

---

## Arquivos

### `offer_catalog.json`

Fonte única de verdade para os **10 braços** do MAB. Estrutura: um bloco `catalog_metadata` + uma lista `offers`.

#### Campos por braço (`offers[]`)

| Campo | Uso no pipeline |
|---|---|
| `arm_id` | Identificador do braço retornado pelo `/decide` (ex.: `OFF-CR-001`) |
| `category` | `credito`, `investimento` ou `seguro` |
| `product_name` / `description` | Nome e descrição curta para o front-end exibir |
| `expected_revenue_brl` | Receita esperada (R$) por conversão — termo de receita da recompensa composta |
| `context_features` | Colunas do dataset BR a extrair como vetor de contexto (LinUCB) |
| `eligible_segment.synthetic_segment` | Segmento sintético "natural" do braço |
| `eligible_segment.santander_filters` | Filtros sobre o dataset BR para selecionar clientes elegíveis |
| `santander_mapping.br_product_column` | Coluna-alvo para calcular o reward real (transição `0→1`); `null` em braços sintéticos |
| `thompson_sampling_prior` | Parâmetros `α/β` da Beta para warm-start do Thompson Sampling |
| `ucb_params.exploration_factor` | Fator de exploração da família UCB (escalado ×0.2 no LinUCB) |
| `synthetic_simulation` | Geração de recompensa simulada (ver abaixo) |
| `reward.horizon_days` | Janela de atribuição do reward (3 a 60 dias dependendo do produto) — usada na simulação de *delayed rewards* |
| `flags.is_cold_start` / `flags.is_synthetic` | Marcadores do braço cold-start e dos braços sem coluna Santander direta |

#### Bloco `synthetic_simulation`

A conversão verdadeira simulada de um braço para um cliente é:

```
conv = base_conversion_rate
       × Π(segment_multipliers ativos para o cliente)
       × (1 + Σ context_modulators_k · z_k)          # z_k = valor padronizado (z-score)
```

com `event_trigger` **sobrepondo** a base quando a condição é satisfeita (ex.: `OFF-SEG-003` atinge 22% quando `evento_viagem_sintetico=1`). O fator dos moduladores é clipado em `[0.3, 2.2]`.

- `base_conversion_rate` — taxa base do produto.
- `segment_multipliers` — multiplicadores por segmento sintético.
- `context_modulators` — coeficientes sobre features contínuas padronizadas (`renda_estimada_anual_brl`, `idade`). **Criam variação intra-segmento** que um roteamento por segmento não captura, mas o LinUCB sim.
- `event_trigger` — gatilho de evento que sobrepõe a base (apenas `OFF-SEG-003`).

#### Bloco `catalog_metadata`

```json
"reward_definition": {
  "type": "composite",
  "formula": "alpha * (expected_revenue_brl / v_max) + beta * conversion",
  "alpha": 0.6, "beta": 0.4, "v_max": 7000
}
```

A recompensa que os bandits otimizam é **composta**: pondera receita (`α`) e conversão (`β`). Receita só se realiza na conversão, então ambos os termos são 0 numa recusa. Ajuste `α/β` para priorizar margem ou volume.

```json
"data_source": {
  "golden_sample_file": "data/golden_set/golden_clients.csv",
  "full_dataset_file":  "data/synthetic_enrichment/clientes_br_sintetico.csv",
  "client_id_column":   "cod_cliente",
  "date_column":        "data_referencia",
  "loader_pattern": {
    "step_1_filter":  "eligible_segment.santander_filters",
    "step_2_context": "context_features",
    "step_3_reward":  "santander_mapping.br_product_column"
  }
}
```

O bloco `catalog_metadata.br_column_mapping` traduz os nomes originais do Santander (espanhol, ex.: `ind_tjcr_fin_ult1`) para os nomes PT-BR do dataset sintético (ex.: `possui_cartao_credito`).

---

### `golden_clients.csv`

Amostra estratificada do dataset `clientes_br_sintetico.csv` gerada por `scripts/generate_golden_sample.py`.

| Item | Valor |
|---|---|
| Linhas | 2.595 (1 registro por cliente) |
| Colunas | 48 (46 originais + 2 adicionadas) |
| Tamanho | ~664 KB |
| Semente | `random_state=42` |
| Estratégia | 200 linhas por segmento sintético, união deduplicada por `cod_cliente` |

**Colunas adicionadas** (não existem no dataset completo):

| Coluna | Tipo | Descrição |
|---|---|---|
| `segmentos_sinteticos` | JSON array (string) | Lista de segmentos sintéticos do cliente (ex.: `["SEG-VIP","SEG-PERFIL-FAMILIAR"]`) |
| `evento_viagem_sintetico` | int (0/1) | Flag de evento de viagem (~14% dos clientes, 373 registros) — gatilho para `OFF-SEG-003` |

> Como há **1 registro por cliente** (snapshot), o reward `0→1` real não está disponível na amostra; a simulação usa o bloco `synthetic_simulation` do catálogo. O `br_product_column` fica documentado para o pipeline real sobre o dataset completo com `data_referencia`.

---

## Catálogo de braços (10)

| arm_id | Categoria | Produto | Segmento alvo | Conv. base | Receita R$ | Reward col. |
|---|---|---|---|---|---|---|
| OFF-CR-001 | crédito | Crédito Pessoal Pré-Aprovado | SEG-CREDITO-ATIVO | 17% | 1.600 | `possui_emprestimo_pessoal` |
| OFF-CR-002 | crédito | Cartão de Crédito Mais | SEG-SEM-CARTAO | 12% | 920 | `possui_cartao_credito` |
| OFF-CR-003 | crédito | Financiamento Imobiliário | SEG-ALTA-RENDA | 4% | 6.200 | `possui_financiamento_imovel` |
| OFF-INV-001 | investimento | CDB Primeiros Passos | SEG-INVESTIDOR-INICIANTE | 15% | 320 | `possui_cdb_curto_prazo` |
| OFF-INV-002 | investimento | CDB Médio Prazo | SEG-POUPADOR | 12% | 680 | `possui_cdb_medio_prazo` |
| OFF-INV-003 | investimento | Previdência Privada PGBL | SEG-CONTRIBUINTE-IR | 10% | 2.400 | `possui_previdencia_privada` |
| OFF-INV-004 | investimento | Fundo Multimercado | SEG-INVESTIDOR-EXPERIENTE | 7% | 1.850 | `possui_fundo_investimento` |
| OFF-SEG-001 | seguro | Seguro de Vida Familiar | SEG-PERFIL-FAMILIAR | 18% | 680 | sintético |
| OFF-SEG-002 | seguro | Seguro Residencial | SEG-PROPRIETARIO | 6% | 420 | sintético |
| OFF-SEG-003 | seguro | Seguro Viagem | SEG-VIAJANTE-EVENTO | 6%* | 240 | sintético |

\* `OFF-SEG-003` atinge 22% apenas quando `evento_viagem_sintetico=1`.

**Braço cold-start:** `OFF-INV-004` — prior não-informativo (`α=1, β=10`), maior fator de exploração (2.2).
**Braços sintéticos** (sem coluna Santander direta): `OFF-SEG-001`, `OFF-SEG-002`, `OFF-SEG-003`.

---

## Cobertura por segmento (`golden_clients.csv`)

| Segmento | Clientes | Braço(s) associado(s) |
|---|---|---|
| SEG-POUPADOR | 1.834 | OFF-INV-002 |
| SEG-SEM-CARTAO | 1.659 | OFF-CR-002 |
| SEG-INVESTIDOR-INICIANTE | 1.656 | OFF-INV-001 |
| SEG-PERFIL-FAMILIAR | 1.471 | OFF-SEG-001 |
| SEG-CREDITO-ATIVO | 1.327 | OFF-CR-001 |
| SEG-CONTRIBUINTE-IR | 1.020 | OFF-INV-003 |
| SEG-ALTA-RENDA | 818 | OFF-CR-003 |
| SEG-SENIOR | 716 | OFF-INV-002/003, OFF-SEG-001 (multiplicador) |
| SEG-JOVEM | 546 | OFF-CR-002, OFF-INV-001 (multiplicador alto) |
| SEG-VIP | 436 | todos (multiplicador VIP) |
| SEG-VIAJANTE-EVENTO | 373 | OFF-SEG-003 (`evento_viagem_sintetico=1`) |
| SEG-INVESTIDOR-EXPERIENTE | 279 | OFF-INV-004 |
| SEG-PROPRIETARIO | 226 | OFF-SEG-002 |

> Um cliente pode pertencer a múltiplos segmentos; total > soma é esperado. Em média, cada cliente é elegível para **5,4 braços**; 639 clientes não são elegíveis para nenhum (ignorados na simulação).

---

## Como conectar o catálogo ao dataset

O pipeline MAB usa o `offer_catalog.json` como driver. Pseudo-código:

```python
catalog = json.load(open("data/golden_set/offer_catalog.json"))
clients = pd.read_csv(catalog["catalog_metadata"]["data_source"]["golden_sample_file"])

for arm in catalog["offers"]:
    filters  = arm["eligible_segment"]["santander_filters"]   # 1. elegibilidade
    eligible = apply_filters(clients, filters)

    ctx_cols = arm["context_features"]                         # 2. contexto (LinUCB)
    context  = eligible[ctx_cols]

    recommended = mab.decide(context, arm["arm_id"])           # 3. decisão

    reward_col = arm["santander_mapping"]["br_product_column"] # 4. reward (real ou simulado)
```

Na **simulação** (snapshot, sem next-month), o reward vem de `synthetic_simulation`; no **pipeline real** sobre o dataset completo, vem da transição `0→1` da `br_product_column` na janela `reward.horizon_days`.

### Convenções dos filtros (`santander_filters`)

| Sufixo / chave | Semântica |
|---|---|
| `_atual` | valor atual da coluna binária de produto (ex.: `possui_cartao_credito_atual: 0`) |
| `_min` | valor mínimo inclusive (ex.: `tempo_relacionamento_meses_min: 6`) |
| `_max` | valor máximo inclusive (ex.: `idade_max: 60`) |
| `_percentil_min` | percentil mínimo da renda (ex.: `renda_percentil_min: 70`) |
| sem sufixo | igualdade direta (ex.: `ind_ativo: 1`) |

---

## Notebook de simulação

`notebooks/datathon_mab_catalogo_linucb.ipynb` consome o catálogo e roda o pipeline completo:

1. Carrega catálogo + clientes.
2. Aplica `santander_filters` → matriz de elegibilidade.
3. Gera recompensa composta via `synthetic_simulation`.
4. Compara **Baseline** (roteamento por segmento) × **Thompson Sampling** (priors do catálogo) × **LinUCB** (campeão).
5. Métricas: reward, regret, conversão, receita, pulls por braço.
6. Eleição do melhor algoritmo (múltiplas sementes), spotlight de cold-start (`OFF-INV-004`) e simulação de *delayed rewards* (via `horizon_days`).

**Resultado:** o **LinUCB** é eleito campeão (~87% do teto teórico), superando o baseline (~85%) e o Thompson global (~79%). O ganho vem de personalizar dentro do segmento (renda/idade) e ponderar a receita — algo que o baseline e o TS não fazem.

---

## Dataset completo

Arquivo de origem: `data/synthetic_enrichment/clientes_br_sintetico.csv` (~196 MB, ~1,35 M linhas). Não versionado (ver `.gitignore`).

```bash
python scripts/generate_synthetic_br.py     # gera o dataset completo
python scripts/generate_golden_sample.py    # regenera esta amostra (random_state=42)
```
