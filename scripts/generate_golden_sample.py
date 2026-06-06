"""
Geração da amostra estratificada para o golden set.

Lê clientes_br_sintetico.csv, classifica cada cliente nos segmentos
sintéticos definidos no offer_catalog, e produz uma amostra de ~2 000
linhas que cobre todos os 13 segmentos.

Saída: data/golden_set/golden_clients.csv
"""

import os
import json
import numpy as np
import pandas as pd

RANDOM_STATE = 42
ROWS_PER_SEGMENT = 200
OUTPUT_ROWS = 2000

rng = np.random.default_rng(RANDOM_STATE)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_PATH = os.path.join(BASE_DIR, "data", "synthetic_enrichment", "clientes_br_sintetico.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "golden_set")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "golden_clients.csv")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def compute_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Classifica cada linha nos segmentos sintéticos do offer_catalog."""
    renda_pct = df["renda_estimada_anual_brl"].rank(pct=True) * 100

    seg = pd.DataFrame(index=df.index)
    seg["SEG-VIP"]                  = df["segmento"] == "01 - ALTA RENDA"
    seg["SEG-JOVEM"]                = df["idade"] < 30
    seg["SEG-SENIOR"]               = df["idade"] >= 55
    seg["SEG-ALTA-RENDA"]           = (renda_pct >= 70) & df["idade"].between(25, 55)
    seg["SEG-CREDITO-ATIVO"]        = (
        (df["ind_ativo"] == 1) &
        (df["tempo_relacionamento_meses"] >= 6) &
        (renda_pct >= 50) &
        (df["possui_emprestimo_pessoal"] == 0)
    )
    seg["SEG-SEM-CARTAO"]           = (
        (df["possui_cartao_credito"] == 0) &
        (df["ind_ativo"] == 1) &
        (df["tempo_relacionamento_meses"] >= 3)
    )
    seg["SEG-INVESTIDOR-INICIANTE"] = (
        (df["possui_fundo_investimento"] == 0) &
        (df["ind_ativo"] == 1)
    )
    seg["SEG-POUPADOR"]             = (
        (df["possui_cdb_curto_prazo"] == 0) &
        (renda_pct >= 50)
    )
    seg["SEG-CONTRIBUINTE-IR"]      = (
        (df["possui_previdencia_privada"] == 0) &
        (renda_pct >= 60) &
        df["idade"].between(30, 60)
    )
    seg["SEG-INVESTIDOR-EXPERIENTE"]= (
        (df["possui_titulos_investimento"] == 0) &
        (df["possui_fundo_investimento"] == 1)
    )
    seg["SEG-PERFIL-FAMILIAR"]      = (
        df["idade"].between(25, 60) &
        (df["ind_ativo"] == 1)
    )
    seg["SEG-PROPRIETARIO"]         = df["possui_financiamento_imovel"] == 1

    # SEG-VIAJANTE-EVENTO: não existe no dataset — gerado sinteticamente (~8%)
    seg["SEG-VIAJANTE-EVENTO"]      = rng.random(len(df)) < 0.08

    # Lista de segmentos por linha (para a coluna JSON)
    seg_list = seg.apply(
        lambda row: json.dumps([s for s, v in row.items() if v], ensure_ascii=False),
        axis=1,
    )
    return seg, seg_list


def main():
    print("=" * 65)
    print("Geração da amostra golden set — dataset BR sintético")
    print("=" * 65)

    print(f"\n[1/4] Carregando: {INPUT_PATH}")
    df = pd.read_csv(INPUT_PATH, low_memory=False)
    print(f"      {df.shape[0]:,} linhas × {df.shape[1]} colunas")

    # Usa apenas o registro mais recente por cliente
    print("[2/4] Selecionando último registro por cliente...")
    df["data_referencia"] = pd.to_datetime(df["data_referencia"], errors="coerce")
    df = df.sort_values("data_referencia").groupby("cod_cliente", as_index=False).last()
    print(f"      {df.shape[0]:,} clientes únicos")

    print("[3/4] Classificando segmentos sintéticos...")
    seg_flags, seg_list = compute_segments(df)
    df["segmentos_sinteticos"] = seg_list

    # Adiciona coluna de evento viagem para uso direto pelo MAB
    df["evento_viagem_sintetico"] = seg_flags["SEG-VIAJANTE-EVENTO"].astype(int)

    # Amostragem estratificada: ROWS_PER_SEGMENT linhas por segmento
    print(f"[4/4] Amostragem estratificada ({ROWS_PER_SEGMENT} linhas/segmento)...")
    sampled_idx: set = set()
    for seg_name in seg_flags.columns:
        eligible = df[seg_flags[seg_name]].index.tolist()
        n = min(ROWS_PER_SEGMENT, len(eligible))
        chosen = rng.choice(eligible, size=n, replace=False)
        sampled_idx.update(chosen.tolist())
        print(f"      {seg_name:35s}: {len(eligible):>7,} elegiveis -> {n} amostrados")

    sample = df.loc[sorted(sampled_idx)].copy()

    # Complementa até OUTPUT_ROWS com clientes ainda não incluídos
    if len(sample) < OUTPUT_ROWS:
        remaining = df[~df.index.isin(sampled_idx)]
        extra_n = OUTPUT_ROWS - len(sample)
        extra = remaining.sample(n=min(extra_n, len(remaining)), random_state=RANDOM_STATE)
        sample = pd.concat([sample, extra], ignore_index=True)

    sample = sample.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)

    sample.to_csv(OUTPUT_PATH, index=False)
    size_kb = os.path.getsize(OUTPUT_PATH) / 1024

    print(f"\n{'=' * 65}")
    print(f"CONCLUÍDO")
    print(f"{'=' * 65}")
    print(f"Arquivo: {OUTPUT_PATH}")
    print(f"Shape:   {sample.shape[0]} linhas × {sample.shape[1]} colunas")
    print(f"Tamanho: {size_kb:.0f} KB")

    print("\nCobertura de segmentos na amostra:")
    for seg_name in seg_flags.columns:
        count = sample["segmentos_sinteticos"].str.contains(seg_name).sum()
        print(f"  {seg_name:35s}: {count:>4} linhas")

    print("\nDistribuição de segmento (coluna segmento):")
    print(sample["segmento"].value_counts().to_string())


if __name__ == "__main__":
    main()
