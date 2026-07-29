# Golden Set

Pasta de dados do sistema MAB: o catálogo de ofertas (braços) e a amostra de clientes. Abaixo, uma breve descrição de cada arquivo seguida do dicionário de campos/colunas.

---

## Arquivos

| Arquivo | Descrição |
|---|---|
| `golden_clients.csv` | Amostra estratificada de **2.595 clientes** (1 linha por cliente, 48 colunas), `random_state=42`. Base para simulação e testes. |
| `offer_catalog.json` | **Catálogo completo** dos 10 braços do MAB fonte de verdade da plataforma (Mantém só os campos consumidos pelo loop do LinUCB). |

---

## Dicionário — `offer_catalog.json`

### `catalog_metadata` (bloco único)

| Campo | Descrição |
|---|---|
| `version` | Versão do catálogo (ex.: `2.0.0`, `2.0.0-min`, `2.0.0-prod`). |
| `n_arms` | Número de braços (ofertas) no catálogo. |
| `description` | Descrição livre do catálogo / da versão. |
| `reward_definition.type` | Tipo de recompensa (`click`). |
| `reward_definition.formula` | Fórmula da recompensa: `reward = click`. O evento de clique (0/1) do `/feedback` é o próprio reward. |
| `reward_definition.note` | Observação: `expected_revenue_brl` é apenas metadado e **não** entra no reward; `valor_total`/`desconto_pct`/`valor_final` são apenas display. |
| `data_source.golden_sample_file` | Caminho da amostra de clientes (`golden_clients.csv`). |
| `data_source.full_dataset_file` | Caminho do dataset completo (`clientes_br_sintetico.csv`). |
| `data_source.client_id_column` | Coluna identificadora do cliente (`cod_cliente`). |
| `data_source.date_column` | Coluna de data de referência (`data_referencia`). |
| `data_source.loader_pattern` | Ordem de uso do catálogo: filtro → contexto → reward. |
| `filter_conventions` | Semântica dos sufixos usados em `santander_filters` (`_atual`, `_min`, `_max`, `_percentil_min`, igualdade). |
| `br_column_mapping` | Tradução dos nomes originais do Santander (espanhol) → colunas PT-BR. |

### `offers[]` (um objeto por braço)

| Campo | Descrição |
|---|---|
| `arm_id` | Identificador único do braço (ex.: `OFF-CR-001`). |
| `category` | Categoria do produto: `credito`, `investimento` ou `seguro`. |
| `product_name` | Nome do produto para exibição no front-end. |
| `description` | Descrição curta do produto para o front-end. |
| `expected_revenue_brl` | Receita esperada (R$) por conversão — **metadado**, não entra no reward (reward = click). |
| `valor_total` | **Display**: preço/tarifa "cheio" da oferta (R$), antes do desconto promocional. |
| `desconto_pct` | **Display**: percentual de desconto promocional aplicado sobre `valor_total`. |
| `valor_final` | **Display**: valor final ao cliente = `round(valor_total * (1 - desconto_pct/100), 2)`. |
| `context_features` | Lista de colunas do dataset usadas como vetor de contexto do LinUCB. |
| `eligible_segment.synthetic_segment` | Segmento sintético "natural" do braço (só no catálogo completo). |
| `eligible_segment.santander_filters` | Filtros de elegibilidade sobre o dataset (ver `filter_conventions`). |
| `santander_mapping.br_product_column` | Coluna-alvo do reward real (transição `0→1`); `null` em braços sintéticos. |
| `thompson_sampling_prior.alpha` | Parâmetro α da Beta (warm-start do Thompson Sampling). |
| `thompson_sampling_prior.beta` | Parâmetro β da Beta (warm-start do Thompson Sampling). |
| `ucb_params.exploration_factor` | Fator de exploração da família UCB (escalado ×0,2 no LinUCB). |
| `reward.type` | Tipo do reward do braço (`binary`). |
| `reward.horizon_days` | Janela de atribuição do reward em dias (3 a 60). |
| `flags.is_cold_start` | `true` se o braço é o caso de cold-start (prior pessimista + exploração alta). |
| `flags.is_synthetic` | `true` se o braço não tem coluna Santander direta (reward só simulado). |


---

## Dicionário — `golden_clients.csv`

2.595 linhas (1 por cliente) · 48 colunas (46 originais do dataset BR + 2 sintéticas).

### Identificação e cadastro

| Coluna | Tipo | Descrição |
|---|---|---|
| `cod_cliente` | int | Identificador único do cliente. |
| `data_referencia` | data | Data de referência do registro (mês-base do snapshot). |
| `data_cadastro` | data | Data em que o cliente abriu relacionamento com o banco. |
| `pais_residencia` | str | País de residência (no dataset, sempre `BR`). |
| `estado` | str | UF de residência (ex.: `SP`). |
| `canal_entrada` | str | Canal pelo qual o cliente entrou no banco. |

### Perfil

| Coluna | Tipo | Descrição |
|---|---|---|
| `sexo` | str | Sexo do cliente (`M`/`F`). |
| `idade` | int | Idade em anos. |
| `renda_estimada_anual_brl` | float | Renda anual bruta estimada (R$). |
| `segmento` | str | Segmento oficial do banco: `01 - ALTA RENDA`, `02 - VAREJO`, `03 - UNIVERSITARIO`. |

### Relacionamento e status

| Coluna | Tipo | Descrição |
|---|---|---|
| `tempo_relacionamento_meses` | int | Tempo de relacionamento com o banco, em meses. |
| `ind_novo` | float | 1 se cliente novo (registrado nos últimos 6 meses), senão 0. |
| `ind_relacionamento` | float | Índice de relação: 1 = principal; 99 = principal que deixará de ser no fim do mês. |
| `ult_data_cliente_principal` | data | Última data em que foi cliente principal. |
| `ind_rel_inicio_mes` | float | Tipo de cliente no início do mês (1 principal, 2 co-titular, P potencial, 3/4 ex). |
| `tipo_rel_inicio_mes` | str | Tipo de relação no início do mês (A ativo, I inativo, P ex-cliente, R potencial). |
| `ind_ativo` | float | Índice de atividade: 1 = cliente ativo, 0 = inativo. |
| `ind_residente` | str | `S`/`N` — se o país de residência é o do banco. |
| `ind_estrangeiro` | str | `S`/`N` — se o país de nascimento difere do país do banco. |
| `ind_funcionario` | str | Índice de funcionário (A ativo, B ex, F filial, N não-funcionário, P passivo). |
| `conjuge_funcionario` | str | `1`/`N` — se é cônjuge de funcionário. |
| `ind_falecido` | str | `S`/`N` — índice de falecimento. |

### Posse de produtos (flags binárias 0/1)

| Coluna | Descrição |
|---|---|
| `possui_poupanca` | Conta poupança. |
| `possui_conta_corrente` | Conta corrente. |
| `possui_conta_corrente_plus` | Conta corrente "plus" (mais particular). |
| `possui_conta_premium` | Conta premium (particular plus). |
| `possui_conta_salario` | Conta salário. |
| `possui_conta_junior` | Conta júnior. |
| `possui_conta_universitaria` | Conta universitária. |
| `possui_conta_digital` | Conta digital (e-account). |
| `possui_conta_investimento` | Conta de investimento. |
| `possui_cdb_curto_prazo` | CDB / depósito de curto prazo. |
| `possui_cdb_medio_prazo` | CDB / depósito de médio prazo. |
| `possui_cdb_longo_prazo` | CDB / depósito de longo prazo. |
| `possui_fundo_investimento` | Fundo de investimento. |
| `possui_titulos_investimento` | Títulos / valores mobiliários. |
| `possui_previdencia_privada` | Plano de previdência privada. |
| `possui_financiamento_imovel` | Financiamento imobiliário (hipoteca). |
| `possui_financiamento_veiculo` | Financiamento de veículo. |
| `possui_emprestimo_pessoal` | Empréstimo pessoal. |
| `possui_cartao_credito` | Cartão de crédito. |
| `possui_aval_garantia` | Aval / garantia. |
| `possui_pagamento_tributos` | Pagamento de tributos. |
| `possui_folha_pagamento` | Folha de pagamento (nómina). |
| `possui_beneficio_previdencia` | Benefício de previdência (nómina pensión). |
| `possui_debito_automatico` | Débito automático (recibo). |

### Colunas sintéticas (adicionadas - não existem no dataset completo)

| Coluna | Tipo | Descrição |
|---|---|---|
| `segmentos_sinteticos` | str (JSON array) | Lista de segmentos sintéticos do cliente, ex.: `["SEG-VIP","SEG-PERFIL-FAMILIAR"]`. Usada para elegibilidade e multiplicadores de conversão. |
| `evento_viagem_sintetico` | int (0/1) | Flag de evento de viagem (373 clientes). Gatilho de conversão do braço `OFF-SEG-003` (Seguro Viagem). |
