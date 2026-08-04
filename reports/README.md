# reports/

Relatórios gerados. Hoje há **um**, e ele não é o relatório técnico completo.

## `evaluation-report.md` — gerado

`make evaluate` roda a avaliação offline contra o golden set e escreve aqui. É um relatório
de **propriedades** (elegibilidade respeitada, invariância de fairness), não de performance.
Roda sem Docker.

## Relatório técnico — ainda bloqueado

## O que vai aqui

O relatório técnico precisa comparar o bandit com o baseline em números:

- **regret acumulado** por política (baseline, Thompson, LinUCB)
- **taxa de conversão** e lift sobre o baseline determinístico
- **cobertura de braços** e distribuição de exposição por segmento
- **fairness por faixa de renda** — os atributos monitorados estão no `context` auditável
  de cada `Decisao` (ver `docs/domain-model.md`)

## Por que ainda está bloqueado

Regret, conversão e lift **dependem de tráfego real**. O cálculo existe desde a Fase 5
(`GET /api/v1/monitoring/metrics` apura de `decisao`/`recompensa`), mas num sistema sem
decisões servidas ele devolve zero por ausência de dado — o que não é um resultado.

A avaliação offline (`make evaluate`) **não** substitui isso: golden set produz garantia de
propriedade, não medida de performance. Um modelo pode passar em 100% das propriedades e
converter mal.

## Desbloqueio

1. Rodar tráfego contra o sistema (demo guiada ou simulação a partir do golden set) até ter
   volume suficiente para as taxas não serem ruído.
2. `GET /api/v1/monitoring/metrics` para apurar; `scripts/retrain_cycle.py --publish` para
   registrar junto da política.
3. Aí sim escrever o relatório aqui, e com ele o `docs/model-card.md` e o
   `docs/governance/fairness-report.md`, que dependem dos mesmos números.

A análise exploratória que **existe** e é reprodutível está em `notebooks/`
(`make notebooks` executa as três ponta a ponta).
