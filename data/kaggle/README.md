# Dados Kaggle — Santander Product Recommendation

Os dados brutos **não são versionados** (ver `.gitignore`). Baixe-os manualmente.

- **Fonte:** [Santander Product Recommendation](https://www.kaggle.com/competitions/santander-product-recommendation)
- **Licença:** uso restrito aos termos da competição Kaggle
- **Arquivos esperados:** `train_ver2.csv`, `test_ver2.csv`

## Como baixar

```bash
kaggle competitions download -c santander-product-recommendation -p data/kaggle/
unzip 'data/kaggle/*.zip' -d data/kaggle/
```

Após o download, rode o pré-processamento para gerar os dados sem vazamento temporal em `data/processed/`.
