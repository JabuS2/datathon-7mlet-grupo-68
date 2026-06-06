"""
Geração de dados sintéticos no contexto brasileiro.

Transforma o dataset Santander (Espanha) para um dataset sintético
representando clientes de um banco brasileiro, com:
  - Colunas renomeadas para português
  - Provincias espanholas → estados brasileiros (proporcional à população)
  - Sexo: H→M, V→F
  - Renda: convertida de EUR para BRL com ajuste de distribuição
  - Segmento: rótulos em PT-BR
  - País: BR
  - Datas: deslocadas 7 anos para frente (2015-2016 → 2022-2023)
  - Produtos financeiros: mapeados para equivalentes brasileiros

Entrada:  data/processed/train_sample_10pct.csv
Saída:    data/synthetic_enrichment/clientes_br_sintetico.csv
          data/synthetic_enrichment/README.md
"""

import os
import numpy as np
import pandas as pd

RANDOM_STATE = 42
rng = np.random.default_rng(RANDOM_STATE)

# ---------------------------------------------------------------------------
# Mapeamentos
# ---------------------------------------------------------------------------

# Provincias espanholas → estados brasileiros (pesos proporcionais à população BR)
PROVINCE_TO_STATE = {
    # Grandes províncias ES → grandes estados BR
    "MADRID":           "SP",
    "BARCELONA":        "RJ",
    "VALENCIA":         "MG",
    "SEVILLA":          "BA",
    "ZARAGOZA":         "PR",
    "MALAGA":           "RS",
    "MURCIA":           "PE",
    "PALMAS LAS":       "CE",
    "VALLADOLID":       "GO",
    "ALICANTE":         "PA",
    "CORDOBA":          "MA",
    "GRANADA":          "SC",
    "BILBAO":           "ES",
    "VITORIA-GASTEIZ":  "DF",
    "DONOSTIA-S.SEBASTIAN": "AM",
    "OVIEDO":           "MT",
    "PAMPLONA/IRUNA":   "MS",
    "SANTANDER":        "PB",
    "LOGRONO":          "RN",
    "TOLEDO":           "AL",
    "CIUDAD REAL":      "PI",
    "CUENCA":           "SE",
    "GUADALAJARA":      "RO",
    "ALBACETE":         "TO",
    "CACERES":          "AC",
    "BADAJOZ":          "AP",
    "HUELVA":           "RR",
    "JAEN":             "AM",
    "CADIZ":            "MG",
    "ALMERIA":          "SP",
    "PONTEVEDRA":       "RS",
    "LUGO":             "SC",
    "CORUNA A":         "PR",
    "OURENSE":          "GO",
    "LEON":             "BA",
    "ZAMORA":           "CE",
    "SALAMANCA":        "PE",
    "AVILA":            "PA",
    "SEGOVIA":          "MA",
    "SORIA":            "MT",
    "BURGOS":           "ES",
    "PALENCIA":         "DF",
    "HUESCA":           "MS",
    "TERUEL":           "PB",
    "CASTELLON":        "RJ",
    "TARRAGONA":        "MG",
    "LLEIDA":           "SP",
    "GIRONA":           "RJ",
    "BALEARES":         "SC",
    "TENERIFE":         "RN",
    "PALMAS DE GRAN CANARIA": "AL",
}

# Estados BR para casos não mapeados (distribuição proporcional à população)
BR_STATES = [
    "SP", "MG", "RJ", "BA", "PR", "RS", "PE", "CE", "PA",
    "MA", "SC", "GO", "AM", "ES", "PB", "RN", "MT", "MS",
    "PI", "AL", "RO", "DF", "SE", "TO", "AC", "AP", "RR",
]
_RAW_WEIGHTS = [
    0.220, 0.104, 0.086, 0.074, 0.057, 0.058, 0.048, 0.046, 0.040,
    0.034, 0.036, 0.034, 0.020, 0.020, 0.020, 0.018, 0.018, 0.014,
    0.016, 0.016, 0.009, 0.015, 0.011, 0.008, 0.004, 0.004, 0.003,
]
BR_STATE_WEIGHTS = [w / sum(_RAW_WEIGHTS) for w in _RAW_WEIGHTS]

SEGMENTO_MAP = {
    "01 - TOP":          "01 - ALTA RENDA",
    "02 - PARTICULARES": "02 - VAREJO",
    "03 - UNIVERSITARIO":"03 - UNIVERSITARIO",
}

SEXO_MAP = {"H": "M", "V": "F"}

# Renomeação de colunas: original → PT-BR
COLUMN_RENAME = {
    "fecha_dato":              "data_referencia",
    "ncodpers":                "cod_cliente",
    "ind_empleado":            "ind_funcionario",
    "pais_residencia":         "pais_residencia",
    "sexo":                    "sexo",
    "age":                     "idade",
    "fecha_alta":              "data_cadastro",
    "ind_nuevo":               "ind_novo",
    "antiguedad":              "tempo_relacionamento_meses",
    "indrel":                  "ind_relacionamento",
    "ult_fec_cli_1t":          "ult_data_cliente_principal",
    "indrel_1mes":             "ind_rel_inicio_mes",
    "tiprel_1mes":             "tipo_rel_inicio_mes",
    "indresi":                 "ind_residente",
    "indext":                  "ind_estrangeiro",
    "conyuemp":                "conjuge_funcionario",
    "canal_entrada":           "canal_entrada",
    "indfall":                 "ind_falecido",
    "nomprov":                 "estado",
    "ind_actividad_cliente":   "ind_ativo",
    "renta":                   "renda_estimada_anual_brl",
    "segmento":                "segmento",
    # Produtos
    "ind_ahor_fin_ult1":       "possui_poupanca",
    "ind_aval_fin_ult1":       "possui_aval_garantia",
    "ind_cco_fin_ult1":        "possui_conta_corrente",
    "ind_cder_fin_ult1":       "possui_conta_investimento",
    "ind_cno_fin_ult1":        "possui_conta_salario",
    "ind_ctju_fin_ult1":       "possui_conta_junior",
    "ind_ctma_fin_ult1":       "possui_conta_universitaria",
    "ind_ctop_fin_ult1":       "possui_conta_corrente_plus",
    "ind_ctpp_fin_ult1":       "possui_conta_premium",
    "ind_deco_fin_ult1":       "possui_cdb_curto_prazo",
    "ind_deme_fin_ult1":       "possui_cdb_medio_prazo",
    "ind_dela_fin_ult1":       "possui_cdb_longo_prazo",
    "ind_ecue_fin_ult1":       "possui_conta_digital",
    "ind_fond_fin_ult1":       "possui_fundo_investimento",
    "ind_hip_fin_ult1":        "possui_financiamento_imovel",
    "ind_plan_fin_ult1":       "possui_previdencia_privada",
    "ind_pres_fin_ult1":       "possui_emprestimo_pessoal",
    "ind_reca_fin_ult1":       "possui_pagamento_tributos",
    "ind_tjcr_fin_ult1":       "possui_cartao_credito",
    "ind_valo_fin_ult1":       "possui_titulos_investimento",
    "ind_viv_fin_ult1":        "possui_financiamento_veiculo",
    "ind_nomina_ult1":         "possui_folha_pagamento",
    "ind_nom_pens_ult1":       "possui_beneficio_previdencia",
    "ind_recibo_ult1":         "possui_debito_automatico",
}


# ---------------------------------------------------------------------------
# Funções de transformação
# ---------------------------------------------------------------------------

def map_province_to_state(nomprov_series: pd.Series) -> pd.Series:
    """Mapeia nomprov (espanhol) para estado brasileiro."""
    mapped = nomprov_series.str.strip().str.upper().map(PROVINCE_TO_STATE)
    # Preenche não mapeados com estado aleatório proporcional à população
    missing_mask = mapped.isna()
    n_missing = missing_mask.sum()
    if n_missing > 0:
        mapped.loc[missing_mask] = rng.choice(
            BR_STATES, size=n_missing, p=BR_STATE_WEIGHTS
        )
    return mapped


def convert_income_to_brl(renta_series: pd.Series) -> pd.Series:
    """
    Converte renda de EUR (distribuição espanhola) para BRL (distribuição brasileira).

    Estratégia:
    1. Normaliza para percentil [0,1]
    2. Aplica distribuição de renda brasileira via quantis reais do IBGE 2022
    3. Adiciona pequeno ruído gaussiano (±5%)
    """
    # Quantis de renda anual familiar estimada no Brasil (BRL, IBGE/PNAD 2022)
    # P10=8400, P25=16800, P50=33600, P75=72000, P90=144000, P95=240000, P99=600000
    br_quantile_values = np.array([
        8_400, 12_000, 16_800, 24_000, 33_600,
        50_400, 72_000, 108_000, 144_000, 192_000,
        240_000, 360_000, 600_000,
    ])
    br_quantile_probs = np.array([
        0.10, 0.15, 0.25, 0.35, 0.50,
        0.65, 0.75, 0.85, 0.90, 0.93,
        0.95, 0.98, 0.99,
    ])

    # Rank percentil de cada linha
    valid = renta_series.dropna()
    ranks = valid.rank(pct=True).clip(0.01, 0.99)

    # Interpolação para obter renda BR equivalente
    brl_values = np.interp(ranks, br_quantile_probs, br_quantile_values)

    # Ruído gaussiano ±5%
    noise = rng.normal(loc=1.0, scale=0.05, size=len(brl_values))
    brl_values = (brl_values * noise).clip(4_200, 1_200_000).round(2)

    result = renta_series.copy().astype(float)
    result.loc[valid.index] = brl_values
    return result


def shift_dates(date_series: pd.Series, years: int = 7) -> pd.Series:
    """Desloca datas N anos para frente (2015-16 → 2022-23)."""
    parsed = pd.to_datetime(date_series, errors="coerce")
    shifted = parsed + pd.DateOffset(years=years)
    return shifted


def add_noise_to_age(age_series: pd.Series) -> pd.Series:
    """Adiciona ruído ±2 anos à idade para evitar identificação."""
    noise = rng.integers(-2, 3, size=len(age_series))
    result = (age_series + noise).clip(18, 100)
    return result


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, "data", "processed", "train_sample_10pct.csv")
    output_dir = os.path.join(base_dir, "data", "synthetic_enrichment")
    output_path = os.path.join(output_dir, "clientes_br_sintetico.csv")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 65)
    print("Geração de dados sintéticos BR — Santander → Banco Brasileiro")
    print("=" * 65)

    # 1. Carrega amostra processada
    print(f"\n[1/9] Carregando: {input_path}")
    df = pd.read_csv(input_path, low_memory=False)
    print(f"      {df.shape[0]:,} linhas × {df.shape[1]} colunas")

    # 2. País → BR
    print("[2/9] Ajustando país para BR...")
    df["pais_residencia"] = "BR"
    df["indresi"] = "S"   # todos residem no Brasil
    df["indext"] = df["indext"].map(lambda x: x if pd.isna(x) else
                                    ("S" if rng.random() < 0.06 else "N"))

    # 3. Provincias → estados brasileiros
    print("[3/9] Mapeando províncias espanholas → estados brasileiros...")
    df["nomprov"] = map_province_to_state(df["nomprov"].astype(str))

    # 4. Sexo: H→M, V→F
    print("[4/9] Convertendo sexo (H→M, V→F)...")
    df["sexo"] = df["sexo"].map(SEXO_MAP).fillna(df["sexo"])

    # 5. Renda → BRL
    print("[5/9] Convertendo renda para BRL (distribuição IBGE 2022)...")
    df["renta"] = convert_income_to_brl(df["renta"])

    # 6. Segmento → PT-BR
    print("[6/9] Traduzindo segmento para PT-BR...")
    df["segmento"] = df["segmento"].map(SEGMENTO_MAP).fillna(df["segmento"])

    # 7. Datas → deslocadas 7 anos
    print("[7/9] Deslocando datas 7 anos (2015-16 → 2022-23)...")
    df["fecha_dato"] = shift_dates(df["fecha_dato"])
    df["fecha_alta"] = shift_dates(df["fecha_alta"])
    if "ult_fec_cli_1t" in df.columns:
        df["ult_fec_cli_1t"] = shift_dates(df["ult_fec_cli_1t"])

    # 8. Idade com ruído
    print("[8/9] Adicionando ruído à idade (±2 anos)...")
    df["age"] = add_noise_to_age(df["age"].fillna(df["age"].median()))

    # 9. Renomeia colunas para PT-BR
    print("[9/9] Renomeando colunas para PT-BR...")
    df.rename(columns=COLUMN_RENAME, inplace=True)

    # Salva
    df.to_csv(output_path, index=False)
    size_mb = os.path.getsize(output_path) / 1_048_576

    print("\n" + "=" * 65)
    print("CONCLUÍDO")
    print("=" * 65)
    print(f"Arquivo: {output_path}")
    print(f"Shape:   {df.shape[0]:,} linhas × {df.shape[1]} colunas")
    print(f"Tamanho: {size_mb:.1f} MB")
    print("\nPrimeiras colunas:")
    for col in list(df.columns[:10]):
        print(f"  {col}")
    print("  ...")

    # Gera mini-resumo por estado
    print("\nDistribuição por estado (top 10):")
    state_counts = df["estado"].value_counts().head(10)
    for state, count in state_counts.items():
        print(f"  {state}: {count:,}")

    print("\nRenda estimada anual BRL — estatísticas:")
    print(df["renda_estimada_anual_brl"].describe().apply(lambda x: f"  {x:,.2f}"))


if __name__ == "__main__":
    main()
