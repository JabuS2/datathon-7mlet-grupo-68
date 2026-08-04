# Camadas de dados

Quatro camadas, encadeadas. Cada uma tem um README próprio com dicionário de colunas e
transformações aplicadas; este arquivo documenta **a cadeia** — o que produz o quê.

```
data/kaggle/               (download manual, credenciado)
        │  scripts/prepare_data.py
        ▼
data/processed/            train_sample_10pct.csv        ~1,36 M linhas × 46 col
        │  scripts/generate_synthetic_br.py
        ▼
data/synthetic_enrichment/ clientes_br_sintetico.csv     ~196 MB, colunas em PT-BR
        │  scripts/generate_golden_sample.py
        ▼
data/golden_set/           golden_clients.csv            2 595 linhas — VERSIONADO
                           offer_catalog.json            10 braços  — VERSIONADO
        │  scripts/generate_evaluation_cases.py
        ▼
                           evaluation_cases.jsonl        24 casos   — VERSIONADO
```

`evaluation_cases.jsonl` é ground truth de teste (avaliação offline, Etapa 4) e por isso
fica no git como os irmãos do `golden_set/`: é pequeno, determinístico e o harness precisa
dele num clone limpo. Regenerar: `make data-eval`. Rodar: `make evaluate`.

## O que é versionado e o que não é

| Camada | No git? | Por quê |
|---|---|---|
| `kaggle/` | ❌ (`.gitignore`) | dado bruto de competição, licença restrita |
| `processed/` | ❌ (`.gitignore`) | ~1,36 M linhas, derivável |
| `synthetic_enrichment/` | ❌ (`.gitignore`) | ~196 MB, derivável |
| `golden_set/` | ✅ | 680 KB — é o que a aplicação, os testes e os notebooks leem |

**Só o `golden_set/` é necessário para rodar o projeto.** Ele está no repositório, então
API, model_service, testes e notebooks funcionam num clone limpo, sem tocar em Kaggle.
Regenerar as camadas de cima só é preciso para mudar o golden set ou refazer a análise.

## Regenerando a cadeia

Pré-requisito manual: credenciais do Kaggle e aceite dos termos da competição.

```bash
# 0. baixar o bruto (manual — precisa de conta e do aceite dos termos)
kaggle competitions download -c santander-product-recommendation -p data/kaggle/
unzip 'data/kaggle/*.zip' -d data/kaggle/

# 1..3. as três etapas derivadas
make data-processed    # kaggle      -> processed
make data-synthetic    # processed   -> synthetic_enrichment
make data-golden       # synthetic   -> golden_set
make data-eval         # golden_set  -> evaluation_cases.jsonl

# ou tudo de uma vez (assume o passo 0 feito)
make data
```

Todas as etapas usam `random_state=42`, então a cadeia é determinística: mesmo bruto,
mesmo golden set.

> O passo 0 **não roda em CI** — exige credenciais. O CI depende apenas do `golden_set/`
> versionado, que é o que o job `notebooks` e os testes consomem.

## `rag_corpus/`

Removido. Era o corpus de políticas internas sintéticas do assistente com RAG, declarado
**fora de escopo** no `docs/backend-roadmap.md` (E9) — o assistente virou `agent_service` +
`mcp_server`, sem recuperação vetorial. Nenhum script produzia o diretório e nenhum código
o lia.
