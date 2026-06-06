# Dataset Sintético Brasileiro — `clientes_br_sintetico.csv`

Dataset sintético gerado a partir da amostra de 10% do Santander Product Recommendation,
transformado para representar clientes de um **banco brasileiro fictício**.

| Item | Valor |
|------|-------|
| Linhas | ~1.355.369 |
| Colunas | 46 |
| Script de geração | `scripts/generate_synthetic_br.py` |
| Origem | `data/processed/train_sample_10pct.csv` |
| Seed | `random_state=42` |
| Tamanho | ~196 MB |

> ⚠️ **Dados sintéticos** — não representam clientes reais.
> Derivados de dados espanhóis com transformações estatísticas para o contexto brasileiro.

---

## Transformações Aplicadas

| Etapa | Descrição |
|-------|-----------|
| País | `pais_residencia` → `BR`; `ind_residente` → `S` para todos |
| Estado | Províncias espanholas mapeadas para estados brasileiros (proporcional à população IBGE) |
| Sexo | `H` → `M` (Masculino), `V` → `F` (Feminino) |
| Renda | Convertida de EUR para BRL usando quantis IBGE/PNAD 2022 + ruído ±5% |
| Segmento | Rótulos traduzidos para PT-BR |
| Datas | Deslocadas +7 anos (2015-2016 → 2022-2023) |
| Idade | Ruído gaussiano de ±2 anos para anonimização |
| Estrangeiro | ~6% marcados como estrangeiros (proporcional ao IBGE 2022) |
| Colunas | Todas renomeadas para português |

---

## Dicionário de Colunas

### Identificação e Data

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `data_referencia` | datetime | Data de referência do registro (mês/ano) |
| `cod_cliente` | int | Código único do cliente (sintético) |

### Dados do Cliente

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `ind_funcionario` | str | Vínculo com o banco: `A`=funcionário ativo, `B`=ex-funcionário, `F`=filial, `N`=não-funcionário, `P`=passivo |
| `pais_residencia` | str | País de residência — sempre `BR` |
| `sexo` | str | Sexo: `M`=masculino, `F`=feminino |
| `idade` | int | Idade do cliente (com ruído ±2 anos) |
| `data_cadastro` | str | Data em que o cliente abriu conta no banco |
| `ind_novo` | int | Cliente novo: `1`=cliente há menos de 6 meses, `0`=caso contrário |
| `tempo_relacionamento_meses` | int | Tempo de relacionamento com o banco (meses) |
| `ind_relacionamento` | int | Tipo de relação: `1`=cliente principal, `99`=era principal no início do mês mas não ao final |
| `ult_data_cliente_principal` | str | Última data como cliente principal |
| `ind_rel_inicio_mes` | str | Tipo de cliente no início do mês: `1`=primário, `2`=cotitular, `P`=potencial, `3`=ex-primário, `4`=ex-cotitular |
| `tipo_rel_inicio_mes` | str | Tipo de relação no início do mês: `A`=ativo, `I`=inativo, `P`=potencial, `R`=ex-aluno |
| `ind_residente` | str | Reside no Brasil: sempre `S` |
| `ind_estrangeiro` | str | Nasceu fora do Brasil: `S`=sim (~6%), `N`=não |
| `conjuge_funcionario` | str | Cônjuge de funcionário: `1`=sim |
| `canal_entrada` | str | Canal de entrada do cliente no banco (código de 3 letras) |
| `ind_falecido` | str | Cliente falecido: `S`=sim |
| `estado` | str | Sigla do estado brasileiro de residência (ex: SP, RJ, MG...) |
| `ind_ativo` | int | Cliente ativo: `1`=ativo, `0`=inativo |
| `renda_estimada_anual_brl` | float | Renda bruta familiar estimada anual em BRL (IBGE 2022) |
| `segmento` | str | Segmento: `01 - ALTA RENDA`, `02 - VAREJO`, `03 - UNIVERSITARIO` |

---

### Produtos Financeiros (24 colunas binárias)

Cada coluna indica se o cliente **possui** (`1`) ou **não possui** (`0`) o produto.

| Coluna | Produto Brasileiro | Equivalente Original (ES) |
|--------|--------------------|--------------------------|
| `possui_poupanca` | Conta Poupança | Saving Account |
| `possui_aval_garantia` | Aval / Fiança | Guarantees |
| `possui_conta_corrente` | Conta Corrente | Current Accounts |
| `possui_conta_investimento` | Conta Investimento | Derivada Account |
| `possui_conta_salario` | Conta Salário | Payroll Account |
| `possui_conta_junior` | Conta Jovem / Júnior | Junior Account |
| `possui_conta_universitaria` | Conta Universitária | Más particular Account |
| `possui_conta_corrente_plus` | Conta Corrente Plus | Particular Account |
| `possui_conta_premium` | Conta Premium | Particular Plus Account |
| `possui_cdb_curto_prazo` | CDB Curto Prazo | Short-term deposits |
| `possui_cdb_medio_prazo` | CDB Médio Prazo | Medium-term deposits |
| `possui_cdb_longo_prazo` | CDB Longo Prazo | Long-term deposits |
| `possui_conta_digital` | Conta Digital | e-account |
| `possui_fundo_investimento` | Fundo de Investimento | Funds |
| `possui_financiamento_imovel` | Financiamento Imobiliário | Mortgage |
| `possui_previdencia_privada` | Previdência Privada | Pensions |
| `possui_emprestimo_pessoal` | Empréstimo Pessoal | Loans |
| `possui_pagamento_tributos` | Pagamento de Tributos | Taxes |
| `possui_cartao_credito` | Cartão de Crédito | Credit Card |
| `possui_titulos_investimento` | Títulos de Investimento | Securities |
| `possui_financiamento_veiculo` | Financiamento de Veículo | Home Account |
| `possui_folha_pagamento` | Folha de Pagamento | Payroll |
| `possui_beneficio_previdencia` | Benefício Previdenciário | Pensions (Nom) |
| `possui_debito_automatico` | Débito Automático | Direct Debit |

---

## Distribuição por Estado

Proporcional à população brasileira (IBGE 2022):

| Estado | % Aprox. |
|--------|----------|
| SP | 22% |
| MG | 10,4% |
| RJ | 8,6% |
| BA | 7,4% |
| PR | 5,7% |
| RS | 5,8% |
| PE | 4,8% |
| CE | 4,6% |
| PA | 4,0% |
| demais | ~26,7% |

## Estatísticas de Renda (BRL/ano)

| Estatística | Valor |
|-------------|-------|
| Mínimo | ~R$ 6.500 |
| P25 | ~R$ 16.900 |
| Mediana | ~R$ 33.900 |
| P75 | ~R$ 72.100 |
| Média | ~R$ 66.000 |
| Máximo | ~R$ 724.500 |

---

## Referências

- Dataset original: [Santander Product Recommendation — Kaggle](https://www.kaggle.com/competitions/santander-product-recommendation)
- Análise de limpeza: [When Less is More — sudalairajkumar](https://www.kaggle.com/code/sudalairajkumar/when-less-is-more)
- Distribuição de renda BR: IBGE/PNAD Contínua 2022
