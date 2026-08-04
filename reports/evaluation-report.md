# Avaliação offline — golden set

> Gerado por `scripts/run_evaluation.py`. **Relatório de propriedades, não de performance.** Regret, conversão e lift dependem de tráfego real e vêm do monitoramento (`GET /api/v1/monitoring/metrics`).

Casos: **24** — de `data/golden_set/evaluation_cases.jsonl`.

| Propriedade | O que garante | Bloqueia? |
|---|---|---|
| `edge` | braço inelegível pelo catálogo não aparece no ranking | sim |
| `adversarial` | variar atributo protegido não muda o que o cliente pode receber | sim |
| `typical` | conformidade com a regra do baseline | não — divergir é aprender |

## `linucb`

**Propriedades bloqueantes: OK**

| Tipo | Passou | Total |
|---|---|---|
| `adversarial` | 8 | 8 |
| `edge` | 8 | 8 |
| `typical` | 0 | 8 |

Falhas:

- `TYP-100870` (`typical`) — topo=OFF-INV-004, baseline diria OFF-CR-001
- `TYP-1186912` (`typical`) — topo=OFF-INV-004, baseline diria OFF-CR-001
- `TYP-952537` (`typical`) — topo=OFF-INV-004, baseline diria OFF-CR-001
- `TYP-1383107` (`typical`) — topo=OFF-INV-004, baseline diria OFF-CR-002
- `TYP-904395` (`typical`) — topo=OFF-INV-004, baseline diria OFF-CR-001
- `TYP-366424` (`typical`) — topo=OFF-INV-004, baseline diria OFF-CR-001
- `TYP-495572` (`typical`) — topo=OFF-SEG-003, baseline diria OFF-INV-001
- `TYP-1464387` (`typical`) — topo=OFF-INV-004, baseline diria OFF-CR-002

## `thompson`

**Propriedades bloqueantes: OK**

| Tipo | Passou | Total |
|---|---|---|
| `adversarial` | 8 | 8 |
| `edge` | 8 | 8 |
| `typical` | 2 | 8 |

Falhas:

- `TYP-100870` (`typical`) — topo=OFF-INV-004, baseline diria OFF-CR-001
- `TYP-1186912` (`typical`) — topo=OFF-CR-002, baseline diria OFF-CR-001
- `TYP-952537` (`typical`) — topo=OFF-CR-003, baseline diria OFF-CR-001
- `TYP-904395` (`typical`) — topo=OFF-SEG-003, baseline diria OFF-CR-001
- `TYP-366424` (`typical`) — topo=OFF-INV-004, baseline diria OFF-CR-001
- `TYP-1464387` (`typical`) — topo=OFF-INV-001, baseline diria OFF-CR-002

## `baseline`

**Propriedades bloqueantes: OK**

| Tipo | Passou | Total |
|---|---|---|
| `adversarial` | 8 | 8 |
| `edge` | 8 | 8 |
| `typical` | 8 | 8 |

