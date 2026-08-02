# datathon-7mlet-grupo-68

Plataforma de investimentos (HP Invest) com backend FastAPI, frontend Angular
e um assistente administrativo baseado em agentes (LangChain + MCP +
CopilotKit).

- **[Arquitetura do Admin Assistant](architecture/admin-assistant.md)** — fluxo
  completo dashboard → agent_service → mcp_server → api_service.
- **[Serviços](services/api-service.md)** — como rodar cada componente.
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

Como o fluxo de uma requisição já atravessa quatro serviços (dashboard →
agent_service → mcp_server → api_service, ver
[arquitetura do Admin Assistant](architecture/admin-assistant.md)) sem
nenhuma stack de observabilidade central hoje — cada serviço loga
isoladamente — a operação em nuvem exigiria **CloudWatch** para centralizar
logs e métricas de todos os pods no EKS, **CloudWatch Container Insights**
para visibilidade de cluster/pod, e tracing distribuído (**X-Ray** ou
OpenTelemetry) para acompanhar uma requisição através dos quatro serviços e
localizar gargalos ou falhas sem precisar correlacionar logs manualmente.
Alarmes ligados a SLOs de latência, taxa de erro e saturação — não apenas
uptime — fechariam o ciclo, permitindo detectar degradação antes que vire
indisponibilidade.
