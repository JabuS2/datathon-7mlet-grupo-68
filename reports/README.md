# reports/

Relatório técnico do projeto. **Diretório intencionalmente vazio — ver o bloqueio abaixo.**

## O que vai aqui

O relatório técnico precisa comparar o bandit com o baseline em números:

- **regret acumulado** por política (baseline, Thompson, LinUCB)
- **taxa de conversão** e lift sobre o baseline determinístico
- **cobertura de braços** e distribuição de exposição por segmento
- **fairness por faixa de renda** — os atributos monitorados estão no `context` auditável
  de cada `Decisao` (ver `docs/domain-model.md`)

## Por que está vazio

Esses números **não existem ainda**. A avaliação offline não está implementada: a tabela
`casos_avaliacao` é populada pelo seed (`services/seed/seeder.py::_seed_cases`) a partir do
golden set, mas nenhum serviço ou endpoint a lê. Sem esse harness não há como produzir as
métricas — e escrevê-las à mão seria inventar resultado.

O `POST /metrics` da governança também não ajuda: ele **grava** um valor que o chamador
manda, não calcula nada a partir de `Decisao`/`Recompensa`.

## Desbloqueio

1. Implementar o harness de avaliação offline sobre `casos_avaliacao` (replay das decisões
   contra o golden set, comparando políticas).
2. Derivar regret / conversão / PSI a partir de `Decisao` + `Recompensa` em vez de receber
   os valores prontos.
3. Aí sim gerar o relatório aqui, e com ele o `docs/model-card.md` e o
   `docs/governance/fairness-report.md`, que dependem dos mesmos números.

Enquanto isso, a análise exploratória que **existe** e é reprodutível está em `notebooks/`
(`make notebooks` executa as três ponta a ponta).
