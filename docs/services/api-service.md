# api_service

FastAPI + PostgreSQL. Emite os JWTs de autenticação (`/login`) e expõe os
dados administrativos (`/admin/users/overview`) consumidos pelo mcp_server.

## Rodando localmente

```bash
cp .env.example .env
pip install -e ".[dev]"
make api        # sobe a API na porta 8000
make test        # roda os testes
```

Detalhes completos, catálogo de ofertas do MAB e mapa de pastas:
[`api_service/README.md`](https://github.com/andrevberaldo/datathon-7mlet-grupo-68/blob/main/api_service/README.md).
