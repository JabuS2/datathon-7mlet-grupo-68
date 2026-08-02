# Guia de integração do front — jornada do cliente

Como consumir a API da plataforma MAB na jornada do visitante: cadastro → recomendação →
interação → aprendizado. Contrato completo em [`api-contracts.md`](api-contracts.md).

**Base URL:** `http://localhost:8001/api/v1`
**Formato:** JSON em **camelCase** (envio e resposta).
**Autenticação:** `Authorization: Bearer <accessToken>` em tudo depois do passo 1.
**Validade do token:** 30 minutos. Ao receber `401`, refaça o login.
**CORS liberado para:** `http://localhost:4200` e `http://localhost:3000`.

---

## Antes de tudo: qual cadastro usar

Existem **dois** e escolher errado quebra a jornada inteira.

| Rota | Cria | Quando usar |
|---|---|---|
| `POST /onboarding` | conta **+ perfil de cliente** (`tipo: demo`) | **Cliente do app.** É esta. |
| `POST /register` | só a conta, sem perfil (`tipo: operador`) | Backoffice/operador. Não use no app. |

Quem entra por `/register` fica sem `codCliente` e **todas** as rotas `/me/*` respondem
`409 NO_CLIENT_PROFILE`. O bandit não tem contexto para decidir nada.

---

## Passo 1 — Criar a conta

O onboarding faz duas coisas de uma vez: gera um perfil sintético de cliente a partir das
respostas (copiando um cliente real parecido como template) e cria a conta de acesso.

```http
POST /api/v1/onboarding
Content-Type: application/json
```
```json
{
  "email": "visitante@exemplo.com",
  "password": "senha1234",
  "idade": 34,
  "segmento": "02 - VAREJO",
  "rendaEstimadaAnualBrl": 85000
}
```

| Campo | Obrigatório | Regra |
|---|---|---|
| `email` | sim | 3–254 chars |
| `password` | sim | 6–128 chars |
| `idade` | sim | 18 a 100 |
| `segmento` | sim | `01 - ALTA RENDA`, `02 - VAREJO` ou `03 - UNIVERSITARIO` |
| `rendaEstimadaAnualBrl` | não | ≥ 0; se omitido, herda do template |

São as "2–3 perguntas" do onboarding — pode ser um wizard curto.

**Resposta 200** — já vem autenticado, não precisa chamar `/login` em seguida:

```json
{
  "accessToken": "eyJhbGciOi...",
  "tokenType": "bearer",
  "cliente": {
    "codCliente": 9000000,
    "idade": 34,
    "tempoRelacionamentoMeses": 7,
    "indAtivo": true,
    "segmento": "02 - VAREJO",
    "estado": "SP",
    "segmentosSinteticos": ["SEG-ALTA-RENDA", "SEG-POUPADOR", "..."],
    "origem": "demo"
  }
}
```

Guarde o `accessToken`. O `codCliente` **não** precisa ser enviado depois — a API o extrai do token.

**Erros:** `409 EMAIL_EXISTS` · `422` (idade fora de 18–100, senha curta) · `409 NO_SEED_DATA`
(banco sem clientes de seed — é problema de ambiente, avise o backend).

### Login em acessos posteriores

```http
POST /api/v1/login
```
```json
{ "email": "visitante@exemplo.com", "password": "senha1234" }
```
→ `{ "accessToken": "...", "tokenType": "bearer" }` · **401 INVALID_CREDENTIALS** se errado.

---

## Passo 2 — Montar a home

Duas chamadas, propósitos diferentes.

### Dados da conta

```http
GET /api/v1/me
```
```json
{ "email": "visitante@exemplo.com", "tipo": "demo", "isAdmin": false, "codCliente": 9000000 }
```

Use `tipo` para decidir o que renderizar: `demo` é cliente, `operador` é backoffice.

### Perfil do cliente (opcional, para uma tela "meu perfil")

```http
GET /api/v1/me/profile
```
```json
{
  "codCliente": 9000000, "idade": 34, "tempoRelacionamentoMeses": 7,
  "indAtivo": true, "segmento": "02 - VAREJO", "estado": "SP",
  "segmentosSinteticos": ["SEG-POUPADOR"], "origem": "demo"
}
```

---

## Passo 3 — Mostrar a oferta recomendada

**Este é o passo que importa.** Leia a seção inteira antes de codar: há uma pegadinha.

### `POST /me/decide` — a oferta principal

```http
POST /api/v1/me/decide?channel=app
Authorization: Bearer <token>
```

**Sem body.** O `channel` vai na query string: `app` (padrão), `push`, `email` ou `sms`.

```json
{
  "decisionId": "4d0da5bf-7390-4c22-9ad3-7239f7933cec",
  "armId": "OFF-INV-004",
  "productName": "Fundo Multimercado",
  "description": "Gestão ativa em juros, câmbio e bolsa para diversificar a carteira.",
  "category": "investimento",
  "channel": "app",
  "score": 1.4995,
  "reasonCodes": ["policy:linucb", "cold_start", "eligible:7"],
  "policyVersion": "linucb-v1"
}
```

**Guarde o `decisionId`** — sem ele não dá para registrar clique nem interesse.

Renderize `productName`, `description` e `category`. O `score` e os `reasonCodes` são internos
(úteis num modo debug da demo, não na tela do cliente).

**Erros:** `404 CLIENT_NOT_FOUND` · `409 NO_ACTIVE_POLICY` (ambiente) · `409 NO_ELIGIBLE_ARM`
(nenhuma oferta serve para esse perfil — mostre um estado vazio, não um erro).

### `GET /me/recommendations` — a lista

```http
GET /api/v1/me/recommendations?top_k=5&channel=app
```
```json
{
  "codCliente": 9000000,
  "policyVersion": "linucb-v1",
  "items": [
    { "rank": 1, "armId": "OFF-INV-004", "productName": "Fundo Multimercado",
      "description": "...", "category": "investimento",
      "score": 1.4995, "reasonCodes": ["policy:linucb", "cold_start"] }
  ]
}
```

`top_k` vai de 1 a 10 (padrão 5). Repare que os parâmetros de query são **snake_case** (`top_k`),
diferente do corpo JSON.

### ⚠️ A pegadinha

`GET /me/recommendations` **não devolve `decisionId`** — ela não registra nada, é só leitura.
E `POST /me/decide` **escolhe o braço sozinho**: não aceita `armId` no request.

Consequência prática: **se você listar 5 ofertas e o usuário clicar na terceira, não há como
registrar o clique daquela oferta.** O `/me/decide` devolveria a primeira.

Dois desenhos coerentes:

**A. Oferta única (recomendado)** — a home chama `/me/decide` e mostra **uma** oferta em
destaque, com "Tenho interesse" / "Agora não". O ciclo fecha certo e é o que demonstra o bandit
aprendendo. A lista de `/me/recommendations` entra como seção secundária *"outras ofertas"*,
apenas informativa, sem botões de ação.

**B. Lista clicável** — exige mudança no backend (`/me/decide` aceitar `armId`, ou o showcase
persistir decisões). **Fale com o backend antes de assumir esse desenho.**

---

## Passo 4 — Registrar o clique

Quando o usuário **abre/expande** a oferta ou toca no card:

```http
POST /api/v1/me/feedback
```
```json
{ "decisionId": "4d0da5bf-7390-4c22-9ad3-7239f7933cec", "type": "click" }
```

`type` aceita `click` ou `impression` (padrão `click`). Impressão já é registrada
automaticamente pelo `/me/decide` — só envie `impression` se precisar marcar reexibições.

```json
{ "eventId": "d326d0fa-...", "decisionId": "4d0da5bf-...", "type": "click",
  "occurredAt": "2026-08-02T20:24:37.041430Z" }
```

Isso **ainda não** ensina o modelo — é só o sinal de engajamento.

---

## Passo 5 — Registrar o resultado (aqui o modelo aprende)

Nos botões de decisão:

```http
POST /api/v1/me/reward
```

**"Tenho interesse":**
```json
{ "decisionId": "4d0da5bf-...", "converted": true }
```

**"Agora não":**
```json
{ "decisionId": "4d0da5bf-...", "converted": false }
```

Não envie o campo `value` — o backend calcula a recompensa. Enviar `value` sobrescreve o
cálculo e distorce o aprendizado.

```json
{ "rewardId": "c4ed2d4e-...", "decisionId": "4d0da5bf-...",
  "value": 0.5586, "status": "observed" }
```

Depois disso, uma nova chamada a `/me/decide` ou `/me/recommendations` já reflete o aprendizado —
os scores mudam. É o efeito para mostrar ao vivo na demo.

**Erros de 4 e 5:** `404 DECISION_NOT_FOUND` (id inválido) · `403 NOT_DECISION_OWNER`
(a decisão é de outro usuário — cada um só interage com as próprias).

---

## Passo 6 — Telas de apoio

### Catálogo completo

```http
GET /api/v1/offers
```
```json
[ { "armId": "OFF-CR-001", "productName": "Crédito Pessoal Pré-Aprovado",
    "description": "Dinheiro na conta em minutos...", "category": "credito" } ]
```

10 ofertas, **sem personalização** — é a vitrine estática. Só estes 4 campos: receita esperada e
regras de elegibilidade são internas e ficam em `/offers/catalog`, restrita a operador (403 para
o cliente).

`GET /api/v1/segments` devolve os segmentos sintéticos, se precisar de rótulos.

### Histórico

```http
GET /api/v1/me/decisions
```

Lista as decisões do usuário com `chosenArmId`, `score`, `reasonCodes`, `createdAt` e o `context`
auditado. Serve para um "minhas recomendações anteriores" ou para a tela de transparência
(*"por que vi esta oferta"*) usando os `reasonCodes`.

---

## Resumo do ciclo

```
POST /onboarding              → accessToken (não use /register!)
   ↓
GET  /me                      → dados da conta
POST /me/decide?channel=app   → oferta em destaque + decisionId   [grava impressão]
   ↓  usuário toca no card
POST /me/feedback             → { decisionId, type: "click" }
   ↓  usuário decide
POST /me/reward               → { decisionId, converted: true|false }   [modelo aprende]
   ↓
POST /me/decide               → próxima oferta, já com o aprendizado
```

## Tabela de erros

| Código | `code` | O que fazer no front |
|---|---|---|
| 401 | `MISSING_TOKEN` / `TOKEN_EXPIRED` | redirecionar para login |
| 401 | `INVALID_CREDENTIALS` | "e-mail ou senha inválidos" |
| 403 | `NOT_DECISION_OWNER` | bug de estado — o `decisionId` não é do usuário logado |
| 403 | `ROLE_NOT_ALLOWED` | rota de operador; esconda do cliente |
| 404 | `DECISION_NOT_FOUND` | `decisionId` inválido ou expirado do estado local |
| 409 | `NO_CLIENT_PROFILE` | conta criada por `/register` — precisa vir do `/onboarding` |
| 409 | `NO_ELIGIBLE_ARM` | estado vazio: "nenhuma oferta disponível agora" |
| 409 | `EMAIL_EXISTS` | "e-mail já cadastrado" |
| 422 | — | validação: idade 18–100, senha ≥ 6, `topK` 1–10 |

Todo erro vem no mesmo formato:

```json
{ "error": "mensagem legível em português", "code": "CODIGO_ESTAVEL" }
```

Use o `code` na lógica (é estável) e o `error` na tela.
