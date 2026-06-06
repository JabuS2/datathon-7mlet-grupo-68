# Dados Processados — Santander Product Recommendation

## Arquivo: `train_sample_10pct.csv`

Amostra de 10% do dataset de treino original, após limpeza e tratamento baseada na análise
["When Less is More"](https://www.kaggle.com/code/sudalairajkumar/when-less-is-more) (sudalairajkumar, Kaggle).

| Item | Valor |
|------|-------|
| Linhas originais | ~13.647.309 |
| Após limpeza/filtros | ~13.553.693 |
| Amostra (10%) | ~1.355.369 linhas |
| Colunas | 46 (48 originais − 2 removidas) |
| Arquivo de origem | `data/kaggle/train_ver2.csv` |
| Script de geração | `scripts/prepare_data.py` |
| Seed de amostragem | `random_state=42` |

---

## Transformações Aplicadas

| Etapa | Descrição |
|-------|-----------|
| Filtro `ind_empleado` | Removidas linhas com `ind_empleado == 'S'` (funcionários — poucos registros) |
| Filtro `pais_residencia` | Mantidas apenas linhas com `pais_residencia == 'ES'` (residentes na Espanha) |
| `tipodom` removida | Coluna constante (sem variância) |
| `cod_prov` removida | Altamente correlacionada com `nomprov` |
| `ind_nuevo` | Valores ausentes preenchidos com `0` |
| `indrel` | Valores ausentes preenchidos com `99` |
| `ind_actividad_cliente` | Valores ausentes preenchidos com `0` |
| `renta` | Valores ausentes preenchidos com a mediana por província (`nomprov`) |
| `segmento` | Valores ausentes preenchidos com o valor mais frequente |
| Colunas de produto | 24 colunas `ind_*_ult1` — NaN preenchidos com `0` |
| `fecha_dato` | Convertida para tipo datetime |
| Amostragem | 10% aleatório (`random_state=42`) |

---

## Dicionário de Colunas

### Identificação e Data

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `fecha_dato` | datetime | Data de referência do registro (mês/ano) |
| `ncodpers` | int | Código único do cliente |

### Dados do Cliente

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `ind_empleado` | str | Índice de funcionário: `A`=ativo, `B`=ex-funcionário, `F`=filial, `N`=não-funcionário, `P`=passivo |
| `pais_residencia` | str | País de residência do cliente (filtrado para `ES` = Espanha) |
| `sexo` | str | Sexo: `H`=masculino, `V`=feminino |
| `age` | int | Idade do cliente |
| `fecha_alta` | str | Data em que o cliente se tornou titular de contrato no banco |
| `ind_nuevo` | int | Novo cliente: `1` se cliente há menos de 6 meses, `0` caso contrário |
| `antiguedad` | int | Antiguidade do cliente no banco (em meses) |
| `indrel` | int | Tipo de relação: `1`=cliente principal, `99`=era principal no início do mês mas não ao final |
| `ult_fec_cli_1t` | str | Última data como cliente principal (quando deixou de ser ao final do mês) |
| `indrel_1mes` | str | Tipo de cliente no início do mês: `1`=primário, `2`=cotitular, `P`=potencial, `3`=ex-primário, `4`=ex-cotitular |
| `tiprel_1mes` | str | Tipo de relação no início do mês: `A`=ativo, `I`=inativo, `P`=potencial, `R`=ex-aluno |
| `indresi` | str | Índice de residência: `S`=reside na Espanha, `N`=não reside |
| `indext` | str | Índice de estrangeiro: `S`=nasceu em outro país, `N`=nasceu na Espanha |
| `conyuemp` | str | Cônjuge de funcionário: `1`=sim |
| `canal_entrada` | str | Canal pelo qual o cliente ingressou no banco |
| `indfall` | str | Índice de falecimento: `S`=cliente falecido |
| `nomprov` | str | Nome da província de residência |
| `ind_actividad_cliente` | int | Cliente ativo: `1`=ativo, `0`=inativo |
| `renta` | float | Renda bruta familiar estimada |
| `segmento` | str | Segmento do cliente: `01`=VIP, `02`=Pessoa física, `03`=Universitário |

---

### Produtos Financeiros (24 colunas binárias `ind_*_ult1`)

Cada coluna indica se o cliente **possui** (`1`) ou **não possui** (`0`) o produto no mês de referência.

| Coluna | Produto (PT) | Produto (EN) |
|--------|-------------|--------------|
| `ind_ahor_fin_ult1` | Conta Poupança | Saving Account |
| `ind_aval_fin_ult1` | Garantias / Avales | Guarantees |
| `ind_cco_fin_ult1` | Conta Corrente | Current Accounts |
| `ind_cder_fin_ult1` | Conta Derivada | Derivada Account |
| `ind_cno_fin_ult1` | Conta Salário | Payroll Account |
| `ind_ctju_fin_ult1` | Conta Júnior | Junior Account |
| `ind_ctma_fin_ult1` | Conta Más Particular | Más particular Account |
| `ind_ctop_fin_ult1` | Conta Particular | Particular Account |
| `ind_ctpp_fin_ult1` | Conta Particular Plus | Particular Plus Account |
| `ind_deco_fin_ult1` | Depósito Curto Prazo | Short-term deposits |
| `ind_deme_fin_ult1` | Depósito Médio Prazo | Medium-term deposits |
| `ind_dela_fin_ult1` | Depósito Longo Prazo | Long-term deposits |
| `ind_ecue_fin_ult1` | Conta Digital (e-account) | e-account |
| `ind_fond_fin_ult1` | Fundos de Investimento | Funds |
| `ind_hip_fin_ult1` | Hipoteca / Crédito Imobiliário | Mortgage |
| `ind_plan_fin_ult1` | Plano de Pensão | Pensions |
| `ind_pres_fin_ult1` | Empréstimos | Loans |
| `ind_reca_fin_ult1` | Impostos / Tributos | Taxes |
| `ind_tjcr_fin_ult1` | Cartão de Crédito | Credit Card |
| `ind_valo_fin_ult1` | Títulos e Valores Mobiliários | Securities |
| `ind_viv_fin_ult1` | Conta Habitação | Home Account |
| `ind_nomina_ult1` | Folha de Pagamento | Payroll |
| `ind_nom_pens_ult1` | Pensão / Aposentadoria | Pensions (Nom) |
| `ind_recibo_ult1` | Débito Automático | Direct Debit |

---

## Colunas Removidas

| Coluna | Motivo |
|--------|--------|
| `tipodom` | Valor constante para todos os registros (sem variância informativa) |
| `cod_prov` | Código numérico da província — redundante com `nomprov` |

---

## Referências

- Competição: [Santander Product Recommendation — Kaggle](https://www.kaggle.com/competitions/santander-product-recommendation)
- Análise de referência: [When Less is More — sudalairajkumar](https://www.kaggle.com/code/sudalairajkumar/when-less-is-more)
