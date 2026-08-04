# datathon-7mlet-grupo-68

Plataforma de investimentos (HP Invest) com backend FastAPI, serviço de modelos
(multi-armed bandits) separado, frontend Angular e um assistente administrativo
baseado em agentes (LangChain + MCP + CopilotKit).

- **[Arquitetura do Admin Assistant](architecture/admin-assistant.md)** — fluxo
  completo dashboard → agent_service → mcp_server → api_service.
- **[Serviços](services/api-service.md)** — como rodar cada componente.
- **[Contratos de API](api-contracts.md)** — request/response por endpoint.
- **[Modelo de domínio](domain-model.md)** — as tabelas e o porquê de cada uma.
- **[Roadmap do backend](backend-roadmap.md)** — etapas E1–E12 e o que mudou depois.
- **[Observabilidade](observability-datadog.md)** — logs JSON + Datadog.
- **[Infraestrutura](infra.md)** — Docker Compose e Kubernetes.

## Tecnologias de Nuvem

Em produção, a arquitetura hoje local (containers stateless — API, mcp_server,
agent_service, dashboard, front_service — orquestrados via Docker Compose ou
um cluster Kubernetes genérico) se beneficiaria de rodar em **Amazon EKS**
com auto scaling horizontal (HPA) reagindo à carga de cada serviço, atrás de
um **Application Load Balancer** com health checks e múltiplas zonas de
disponibilidade para não depender de uma única instância no caminho de
requisições. Os componentes stateful (Postgres, Redis, OpenSearch), hoje
single-instance no `docker-compose.yml`, ganhariam resiliência real com
**RDS Multi-AZ** e **ElastiCache com réplicas**, eliminando pontos únicos de
falha; dados e artefatos hoje presos em volumes locais (`./data`) passariam
para **S3**, desacoplando-os do ciclo de vida dos containers.

O fluxo de uma requisição já atravessa quatro serviços (dashboard →
agent_service → mcp_server → api_service, ver
[arquitetura do Admin Assistant](architecture/admin-assistant.md)). Hoje
`api_service` e `model_service` emitem log estruturado em JSON e traces via
ddtrace, coletados por um agente Datadog opcional no compose
(`--profile datadog`); `agent_service`, `mcp_server` e os frontends ainda
logam isoladamente. Em nuvem, a operação exigiria **CloudWatch** para centralizar
logs e métricas de todos os pods no EKS, **CloudWatch Container Insights**
para visibilidade de cluster/pod, e tracing distribuído (**X-Ray** ou
OpenTelemetry) para acompanhar uma requisição através dos quatro serviços e
localizar gargalos ou falhas sem precisar correlacionar logs manualmente.
Alarmes ligados a SLOs de latência, taxa de erro e saturação — não apenas
uptime — fechariam o ciclo, permitindo detectar degradação antes que vire
indisponibilidade.
