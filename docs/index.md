# datathon-7mlet-grupo-68

Plataforma de investimentos (HP Invest) com backend FastAPI, serviço de modelos
(multi-armed bandits) separado, frontend Angular e um assistente administrativo
baseado em agentes (LangChain + MCP + CopilotKit).

- **[Visão geral do sistema](architecture/system-overview.md)** — como as três
  frentes (vitrine, motor de recomendação, admin assistant) se encaixam.
- **[Arquitetura do Admin Assistant](architecture/admin-assistant.md)** — fluxo
  completo dashboard → agent_service → mcp_server → api_service.
- **[Recursos de nuvem](architecture/cloud-resources.md)** — o mapeamento
  para produção (EKS, RDS, ElastiCache, S3, e o que falta hoje para chegar lá).
- **[Serviços](services/api-service.md)** — como rodar cada componente.
- **[Contratos de API](api-contracts.md)** — request/response por endpoint.
- **[Modelo de domínio](domain-model.md)** — as tabelas e o porquê de cada uma.
- **[Roadmap do backend](backend-roadmap.md)** — etapas E1–E12 e o que mudou depois.
- **[Observabilidade](observability-datadog.md)** — logs JSON + Datadog.
- **[Infraestrutura](infra.md)** — Docker Compose e Kubernetes.

## Tecnologias de nuvem

A arquitetura hoje roda em Docker Compose (ou um Helmfile que cobre só o
`api_service`) com Postgres/Redis/MLflow single-instance. O alvo de produção
é **Amazon EKS** atrás de um ALB, com **RDS Multi-AZ**, **ElastiCache** e
**S3** para os componentes stateful, e **CloudWatch**/**X-Ray** para
observabilidade — ver o mapeamento completo, componente a componente, e as
lacunas atuais (não existe hoje pipeline de imagem/deploy nem secrets
gerenciados) em [Recursos de nuvem](architecture/cloud-resources.md).
