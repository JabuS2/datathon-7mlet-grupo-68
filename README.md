# datathon-7mlet-grupo-68

Plataforma de investimentos (HP Invest) com backend FastAPI, serviço de modelos
(multi-armed bandits) separado, frontend Angular e um assistente administrativo
baseado em agentes (LangChain + MCP + CopilotKit).

| Serviço | O que é | Porta (compose) |
|---|---|---|
| `api_service/` | API de negócio: auth, catálogo, serving, governança | 8001 |
| `model_service/` | Bandits (`/rank`, `/update`) + registry MLflow; estado em Redis | 8002 |
| `front_service/` | Portal do cliente (Angular) | 4200 |
| `apps/dashboard/` | UI do assistente administrativo (Next + CopilotKit) | 3000 |
| `agent_service/` | Agente LangChain que orquestra as tools do MCP | 8100 |
| `mcp_server/` | Servidor MCP que expõe a API como tools/widgets | 8200 |

Veja `docs/architecture/system-overview.md` para como as peças se encaixam,
`docs/architecture/admin-assistant.md` para o desenho detalhado do
assistente, e os READMEs de cada serviço para como rodar cada peça
isoladamente. Infraestrutura local via Docker Compose (`docker-compose.yml`)
e Kubernetes (`infra/k8s/`).

## Tecnologias de nuvem

A arquitetura hoje roda em Docker Compose (ou um Helmfile que cobre só o
`api_service`) com Postgres/Redis/MLflow single-instance. O alvo de produção
é **Amazon EKS** atrás de um ALB, com **RDS Multi-AZ**, **ElastiCache** e
**S3** para os componentes stateful, e **CloudWatch**/**X-Ray** para
observabilidade — mapeamento completo, componente a componente, e as lacunas
atuais (sem pipeline de imagem/deploy, sem secrets gerenciados) em
`docs/architecture/cloud-resources.md`.
