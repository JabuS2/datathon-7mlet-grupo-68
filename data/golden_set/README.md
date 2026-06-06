# Golden Set — Datathon 7MLET Grupo 68

Conjunto de avaliação do sistema MAB. Contém o catálogo de ofertas, a amostra de clientes para testes e a documentação da conexão entre os dois.

---

## Arquivos

### `offer_catalog.json`
Fonte única de verdade para os 10 braços do MAB. Define, por braço:

| Campo | Uso no pipeline |
|---|---|
| `arm_id` | Identificador do braço retornado pelo `/decide` |
| `context_features` | Colunas do dataset BR a extrair como vetor de contexto (LinUCB) |
| `eligible_segment.santander_filters` | Filtros sobre o dataset BR para selecionar clientes elegíveis |
| `santander_mapping.br_product_column` | Coluna-alvo para calcular o reward (transição `0→1`) |
| `thompson_sampling_prior` | Parâmetros α/β da Beta para warm-start do Thompson Sampling |
| `ucb_params.exploration_factor` | Fator `c` da fórmula UCB (`c * sqrt(ln(t)/n_i)`) |
| `synthetic_simulation` | Taxa de conversão base + multiplicadores por segmento para simulação |
| `reward.horizon_days` | Janela de atribuição do reward (3 a 60 dias dependendo do produto) |

O bloco `catalog_metadata.data_source` conecta o catálogo ao dataset:

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

O bloco `catalog_metadata.br_column_mapping` traduz os nomes originais do Santander (espanhol) para os nomes PT-BR do dataset sintético.

---

### `golden_clients.csv`
Amostra estratificada do dataset `clientes_br_sintetico.csv` gerada por `scripts/generate_golden_sample.py`.

| Item | Valor |
|---|---|
| Linhas | 2 595 (1 registro por cliente) |
| Colunas | 48 (46 originais + 2 adicionadas) |
| Tamanho | ~664 KB |
| Semente | `random_state=42` |
| Estratégia | 200 linhas por segmento sintético, união deduplicada por `cod_cliente` |

**Colunas adicionadas** (não existem no dataset completo):

| Coluna | Tipo | Descrição |
|---|---|---|
| `segmentos_sinteticos` | JSON array (string) | Lista de segmentos sintéticos aos quais o cliente pertence (ex: `["SEG-VIP","SEG-PERFIL-FAMILIAR"]`) |
| `evento_viagem_sintetico` | int (0/1) | Flag de evento de viagem gerado aleatoriamente (~8% dos clientes) — gatilho para OFF-SEG-003 |

**Cobertura por segmento:**

| Segmento | Linhas | Braço(s) associado(s) |
|---|---|---|
| SEG-VIP | 436 | todos com multiplicador VIP |
| SEG-JOVEM | 546 | OFF-CR-002, OFF-INV-001 (multiplicador alto) |
| SEG-SENIOR | 716 | OFF-INV-002, OFF-INV-003, OFF-SEG-001 |
| SEG-ALTA-RENDA | 818 | OFF-CR-003, OFF-INV-002 |
| SEG-CREDITO-ATIVO | 1327 | OFF-CR-001 |
| SEG-SEM-CARTAO | 1659 | OFF-CR-002 |
| SEG-INVESTIDOR-INICIANTE | 1656 | OFF-INV-001 |
| SEG-POUPADOR | 1834 | OFF-INV-002 |
| SEG-CONTRIBUINTE-IR | 1020 | OFF-INV-003 |
| SEG-INVESTIDOR-EXPERIENTE | 279 | OFF-INV-004 |
| SEG-PERFIL-FAMILIAR | 1471 | OFF-SEG-001 |
| SEG-PROPRIETARIO | 226 | OFF-SEG-002 |
| SEG-VIAJANTE-EVENTO | 373 | OFF-SEG-003 |

> Um cliente pode pertencer a múltiplos segmentos. Total de linhas > soma dos segmentos é esperado.

---

## Como conectar o catálogo ao dataset

O pipeline MAB usa o `offer_catalog.json` como driver. Pseudo-código:

```python
catalog = json.load(open("data/golden_set/offer_catalog.json"))
clients = pd.read_csv(catalog["catalog_metadata"]["data_source"]["golden_sample_file"])

for arm in catalog["offers"]:
    # 1. Filtrar clientes elegíveis para este braço
    filters = arm["eligible_segment"]["santander_filters"]
    eligible = apply_filters(clients, filters)

    # 2. Extrair vetor de contexto
    ctx_cols = arm["context_features"]
    context_matrix = eligible[ctx_cols]

    # 3. MAB decide qual braço recomendar (Thompson / UCB / LinUCB)
    recommended_arm_id = mab.decide(context_matrix, arm["arm_id"])

    # 4. Calcular reward (simulado ou real)
    reward_col = arm["santander_mapping"]["br_product_column"]
    reward = clients_next_month[reward_col]  # transição 0→1
```

### Definição dos filtros (`santander_filters`)

Os filtros usam nomes PT-BR do dataset sintético. Convenções:

| Sufixo / chave | Semântica |
|---|---|
| `_atual` | valor atual da coluna binária de produto (ex: `possui_cartao_credito_atual: 0`) |
| `_min` | valor mínimo inclusive (ex: `tempo_relacionamento_meses_min: 6`) |
| `_percentil_min` | percentil mínimo da renda (ex: `renda_percentil_min: 50`) |
| `idade_min/max` | faixa etária elegível |
| sem sufixo | igualdade direta (ex: `ind_ativo: 1`) |

---

## Dataset completo

O arquivo de origem é `data/synthetic_enrichment/clientes_br_sintetico.csv` (~196 MB, ~1,35 M linhas). Não está versionado no git (ver `.gitignore`). Para gerá-lo:

```bash
python scripts/generate_synthetic_br.py
```

Para regenerar esta amostra:

```bash
python scripts/generate_golden_sample.py
```

---

## Distribuição de braços do catálogo

| Categoria | Braços | Conversão base |
|---|---|---|
| Crédito | OFF-CR-001, OFF-CR-002, OFF-CR-003 | 4% – 17% |
| Investimento | OFF-INV-001, OFF-INV-002, OFF-INV-003, OFF-INV-004 | 7% – 15% |
| Seguro | OFF-SEG-001, OFF-SEG-002, OFF-SEG-003 | 6% – 22%* |

*OFF-SEG-003 atinge 22% apenas quando `evento_viagem_sintetico=1`.

**Braço cold-start:** OFF-INV-004 — prior não-informativo (α=1, β=10), maior fator de exploração (2.2).

**Braços sintéticos** (sem coluna Santander direta): OFF-SEG-001, OFF-SEG-002, OFF-SEG-003.
