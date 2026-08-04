# Contratos de API — Plataforma MAB (HP Invest)

Contratos de entrada/saída dos endpoints do backend (Etapa 5 do PDF: "contrato de entrada e saída
documentado, com exemplo de chamada e tratamento de erro"). Os schemas Pydantic ficam em
`api_service/schemas/` e são a fonte de verdade — este documento é a visão legível.

> **Estado:** os **schemas** (contratos) já existem e são testados
> (`tests/unit/test_contracts_roundtrip.py`). Os **endpoints** que os consomem são implementados
> nas etapas E7–E10 do [roadmap](./backend-roadmap.md). As rotas abaixo descrevem o contrato-alvo.

## Convenções

- **Base URL:** `/api/v1`.
- **Serialização:** JSON em **camelCase** (ex.: `codCliente`, `armId`, `policyVersion`). A API
  também aceita snake_case na entrada (`populate_by_name`). Corpos com campos desconhecidos são
  rejeitados (`extra="forbid"`).
- **Auth:** `Authorization: Bearer <jwt>`. RBAC por `tipo` (`operador` | `demo`) — ver E8.
- **Datas:** ISO-8601 UTC.

## Envelope de erro

`AppException` (regras de negócio) responde com:

```json
{ "error": "Email ou senha inválidos", "code": "INVALID_CREDENTIALS" }
```

| HTTP | Quando |
|---|---|
| `400` | corpo inválido / violação de contrato (Pydantic) |
| `401` | token ausente/ inválido ou credenciais inválidas |
| `403` | papel sem permissão (ex.: `demo` tentando aprovar política) |
| `404` | recurso inexistente (cliente/decisão/oferta) |
| `409` | conflito (ex.: e-mail já registrado) |
| `422` | tipos/enum fora do domínio |
| `500` | erro não tratado (logado, resposta genérica) |

---

## Serving (núcleo do bandit)

### `POST /decide` — decidir a melhor oferta para um cliente
Escolhe **um** braço via política ativa e **registra a decisão** (log auditável com `reasonCodes`
e `policyVersion`).

**Request** (`DecideRequest`)
```json
{ "codCliente": 100870, "channel": "app" }
```
`channel` ∈ `app | push | email | sms` (default `app`).

`armId` é **opcional**: omitido, a política escolhe o topo do ranking; informado (vitrine
clicável), registra a oferta que o usuário escolheu e acrescenta `user_selected` aos
`reasonCodes` — o log distingue decisão da política de escolha do usuário. Braço fora do
conjunto elegível devolve `409 ARM_NOT_ELIGIBLE`.

**Response 200** (`DecideResponse`)
```json
{
  "decisionId": "b1f2…-uuid",
  "armId": "OFF-CR-001",
  "productName": "Crédito Pessoal Pré-Aprovado",
  "description": "Dinheiro na conta em minutos…",
  "category": "credito",
  "channel": "app",
  "score": 1.2734,
  "reasonCodes": ["policy:linucb", "cold_start", "eligible:7"],
  "policyVersion": "linucb-v1"
}
```
**Erros:** `404` cliente inexistente; `409`/`422` sem braço elegível.

### `POST /showcase` — vitrine ranqueada
Devolve as ofertas elegíveis **ordenadas** pelo score da política ativa (LinUCB por default).

**Request** (`ShowcaseRequest`): `{ "codCliente": 100870, "channel": "app", "topK": 5 }`

**Response 200** (`ShowcaseResponse`)
```json
{
  "codCliente": 100870,
  "policyVersion": "linucb-v1",
  "items": [
    { "armId": "OFF-INV-004", "productName": "Fundo Multimercado", "description": "…",
      "category": "investimento", "score": 1.51, "reasonCodes": ["policy:linucb", "explore"], "rank": 1 }
  ]
}
```

### `POST /me/feedback` — evento de clique/impressão
Registra o evento observado após a decisão. O clique é o **único** sinal de recompensa.

> A rota crua `POST /feedback` foi cedida ao fluxo novo (`endpoints/feedback.py`, via
> model_service), que espera `{ "armId": …, "clicked": … }`. Para o evento atrelado a uma
> decisão auditável, use `/me/feedback`.

**Request** (`FeedbackRequest`): `{ "decisionId": "b1f2…", "type": "click" }`
**Response 200** (`FeedbackResponse`): `{ "eventId": "…", "decisionId": "b1f2…", "type": "click", "occurredAt": "…Z" }`

### `POST /reward` — resultado (adoção do produto)
Realimenta o bandit; pode chegar **atrasado** (`status="pending"` até observar a transição 0→1).

A recompensa é **binária** e derivada pelo serviço: `1.0` se houve clique ou conversão, `0.0`
caso contrário. O chamador não arbitra o valor — `RewardRequest` não tem campo `value`.

**Request** (`RewardRequest`): `{ "decisionId": "b1f2…", "converted": true }`
**Response 200** (`RewardResponse`): `{ "rewardId": "…", "decisionId": "b1f2…", "value": 1.0, "status": "observed" }`

O aprendizado é aplicado na **política que gerou a decisão** (`decisao.policy_version`), não na
ativa no momento do reward: recompensa atrasada pode chegar depois de uma promoção, e aplicá-la
na política errada corromperia o modelo que está servindo. O api_service repassa esse
`policy_id` explicitamente no `POST /update` do model_service.

### `GET /decisions/{decisionId}` — visão auditável
**Response 200** (`DecisaoResponse`): decisão completa com `context`, `reasonCodes`,
`chosenArmId`, `policyVersion`, `score`, `createdAt`.

O `context` traz os dois regimes de conformidade (ver `domain-model.md`):
`atributos_excluidos: ["sexo"]` (protegido, nunca entra) e
`atributos_monitorados: ["renda_estimada_anual_brl"]` (sensível, entra de forma legítima e é
acompanhado por fairness de exposição).

---

## Catálogo & contexto

| Método | Rota | Response | Papel |
|---|---|---|---|
| `GET` | `/offers` | `OfferResponse[]` | vitrine ranqueada pelo **model_service** (`?algorithm=&top=`) |
| `GET` | `/offers/catalog` | `OfertaResponse[]` | catálogo interno (receita, elegibilidade) — **operador** |
| `PUT` | `/profile` | `ClienteResponse` | atualização **parcial** do contexto do próprio cliente |
| `POST` | `/feedback` | `FeedbackResponse` | clique por `armId` → reward 0/1 propagado ao model_service |
| `GET` | `/segments` | `SegmentoResponse[]` | segmentos sintéticos |
| `POST` | `/onboarding` | `OnboardingResponse` | cadastro demo (perfil template §6) |
| `GET` | `/clients/{codCliente}` | `ClienteResponse` | contexto do cliente |

`OnboardingRequest`: `{ "email": "v@demo.com", "password": "…", "idade": 30, "segmento": "02 - VAREJO", "rendaEstimadaAnualBrl": 50000 }`
→ gera perfil sintético por template (`origem="demo"`, faixa `codCliente ≥ 9_000_000`) + conta
`tipo="demo"`, e devolve `OnboardingResponse` (`accessToken` + `cliente`). O front usa o `codCliente`
para chamar `/decide` (cold-start ao vivo).

**RBAC (Etapa 8):** rotas de governança usam `Depends(require_operador)`; um `demo` recebe
`403 ROLE_NOT_ALLOWED`. O papel vem de `usuario.tipo` (`operador` | `demo`).

---

## Self-service do usuário logado (JWT obrigatório)

Rotas escopadas no **usuário autenticado**: o `cod_cliente` vem do **token** (não do body) e
feedback/reward verificam a **posse** da decisão. É a jornada "loga → vê conta → recebe sugestão".

| Método | Rota | Response | Descrição |
|---|---|---|---|
| `GET` | `/me` | `UserResponse` | conta: `email`, `tipo`, `codCliente`, `saldoFicticio` |
| `GET` | `/me/profile` | `ClienteResponse` | contexto do próprio cliente (`409 NO_CLIENT_PROFILE` se operador) |
| `GET` | `/me/recommendations` | `ShowcaseResponse` | vitrine ranqueada do usuário (`?channel=&top_k=`) |
| `POST` | `/me/decide` | `DecideResponse` | decide p/ o próprio cliente (`?channel=`) e registra o log; corpo opcional `{ "armId": "..." }` para a vitrine clicável |
| `POST` | `/me/feedback` | `FeedbackResponse` | clique — só na **própria** decisão (`403 NOT_DECISION_OWNER`) |
| `POST` | `/me/reward` | `RewardResponse` | resultado — só na própria decisão |
| `GET` | `/me/decisions` | `DecisaoResponse[]` | histórico das próprias decisões |
| `GET` | `/offers` | `OfferResponse[]` | vitrine ranqueada pelo model_service |
| `GET` | `/segments` | `SegmentoResponse[]` | segmentos sintéticos |

> As rotas cruas `/decide`, `/showcase` e `/reward` (sem `/me`) permanecem como superfície
> **interna/ops** (ex.: `scripts/reproduce.py`, operadores). O usuário final usa `/me/*`.
>
> `POST /feedback` **não** pertence mais a essa superfície: o caminho passou para o fluxo novo
> (`endpoints/feedback.py`, via model_service), que espera `{ "armId": "...", "clicked": true }`
> e não `{ "decisionId": "...", "type": "click" }`. Para registrar o clique atrelado a uma
> decisão auditável, use `POST /me/feedback`.

---

## Governança & MLOps

> **Mudou de serviço.** O ciclo de vida das políticas (registrar, promover, ciclos de
> retreino, approval gate) é do **model_service** — ver
> [`services/model-service.md`](services/model-service.md). O api_service não expõe mais
> `/policies`, `/retrain-cycles`, `/approvals` nem `/metrics`.
>
> O **cálculo** das métricas continua sendo do api_service, que é quem tem
> `decisao`/`recompensa`; o resultado é publicado em `POST /metrics` do model_service.
> O cálculo em si ainda não existe (Fase 5).

### Contratos originais (referência histórica)

| Método | Rota | Body / Response | Descrição |
|---|---|---|---|
| `POST` | `/policies` | `PoliticaCreate` → `PoliticaResponse` | registra política (nasce `shadow`) + priors de `estado_braco` |
| `GET` | `/policies` | `PoliticaResponse[]` | lista versões |
| `GET` | `/policies/{id}/arms` | `EstadoBracoResponse[]` | pesos aprendidos por braço |
| `POST` | `/policies/{id}/promote` | `PoliticaResponse` | promove p/ `active` (aposenta a anterior — uma ativa por vez) |
| `POST` | `/retrain-cycles` | `RetrainCycleCreate` → `CicloRetreinoResponse` | abre ciclo `candidate` |
| `POST` | `/approvals` | `AprovacaoHumanaCreate` → `AprovacaoHumanaResponse` | approval gate humano (`approve`→promove) |
| `POST` | `/retrain-cycles/{run_id}/rollback` | `RollbackRequest` → `CicloRetreinoResponse` | rollback auditável (reativa `toPolicyId`) |
| `POST` | `/metrics` | `MetricaCreate` → `MetricaResponse` | snapshot de regret/conversão/reward/PSI drift |
| `GET` | `/metrics` | `MetricaResponse[]` | série (`?policy_id=` / `?alerts_only=true`) |

Fluxo de vida (Etapa 7): registrar (`shadow`) → `POST /retrain-cycles` (`candidate`) →
`POST /approvals` `approve` (promove p/ `active`, human-in-the-loop) → `rollback` se preciso.
`demo` recebe `403 ROLE_NOT_ALLOWED` em qualquer rota de governança.

---

> **Assistente (LLM + RAG):** fora do escopo deste backend — será uma **API separada**.

## Avaliação (golden set)

| Método | Rota | Response |
|---|---|---|
| `GET` | `/evaluation/cases` | `CasoAvaliacaoResponse[]` (≥20 casos: typical/edge/adversarial) |

Cada caso traz `context`, `expectedArm`, `expectedReward`, `rationale` e `passFailCriteria`.
