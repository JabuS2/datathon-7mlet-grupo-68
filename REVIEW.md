# Revisao Tecnica do Repositorio — SNAPSHOT HISTORICO

> **Documento historico, nao vale como descricao do repositorio atual.**
> Foi escrito em 2026-06-05, quando o backend vivia em `src/` e so tinha
> `health`/`register`/`login`/`me`. Desde entao o pacote virou `api_service/`,
> entrou o dominio MAB completo, o `model_service`, os frontends e o assistente.
> Os caminhos de arquivo citados abaixo em sua maioria nao existem mais.
> Para o estado atual, veja `README.md`, `docs/index.md` e `docs/backend-roadmap.md`.

Data da analise: 2026-06-05

## Escopo

Analise focada em FastAPI, SQLAlchemy 2.x, arquitetura, performance, seguranca e qualidade de codigo.

Arquivos principais revisados:

- `src/main.py`
- `src/api/v1/routes.py`
- `src/api/v1/endpoints/auth.py`
- `src/api/v1/endpoints/health.py`
- `src/core/auth_dependencies.py`
- `src/core/jwt_token.py`
- `src/db/database.py`
- `src/db/session.py`
- `src/db/dependencies.py`
- `src/db/unit_of_work.py`
- `src/models/base.py`
- `src/models/user.py`
- `src/models/token.py`
- `src/repositories/base.py`
- `src/repositories/user.py`
- `src/schemas/base.py`
- `src/schemas/user.py`
- `src/schemas/token.py`
- `src/services/user/user.py`
- `src/settings.py`
- `src/utils/fake_factory.py`
- `alembic/env.py`
- `alembic/versions/0548fa41ad4c_user_model.py`
- `pyproject.toml`
- `.github/workflows/ci.yml`
- `docker-compose.yml`
- `infra/docker/Dockerfile.api`
- `infra/docker/Dockerfile.dashboard`
- `infra/docker/Dockerfile.assistant`
- `README.md`
- `Makefile`
- `.env.example`

Arquivos e diretorios como `src/services/bandit`, `src/services/audit`, `src/data/*`, `apps/*`, `docs/*` e `tests/*` existem majoritariamente como `.gitkeep`, sem implementacao funcional versionada.

## Resumo Executivo

O repositorio ainda esta em um estagio inicial. A API FastAPI real implementa apenas `health`, `register`, `login` e `me`, enquanto o README descreve uma plataforma muito maior, com MAB, dashboard, RAG, simulacao e avaliacao. Ha problemas que impedem confiabilidade operacional imediata: incompatibilidade entre Python 3.11 e a sintaxe usada no codigo, comandos do Makefile apontando para modulos inexistentes, modelo `Token` com import quebrado, ausencia de testes reais, configuracao de banco inconsistente no Docker e segredo JWT padrao.

Pontos positivos:

- Uso de FastAPI com prefixo versionado em `src/main.py:39`.
- Uso de SQLAlchemy async e `Mapped`/`mapped_column` em `src/models/base.py:1` e `src/models/user.py:1-11`.
- Senhas sao hasheadas com Argon2 em `src/core/jwt_token.py:11-18`.
- JWT exige `exp`, `iat` e `sub` na decodificacao em `src/core/auth_dependencies.py:23-27`.
- Migracao inicial de usuarios existe em `alembic/versions/0548fa41ad4c_user_model.py:21-41`.

## Validacoes Executadas

- `python3 --version`: Python 3.12.3.
- `python3 -m compileall src alembic`: compilou com sucesso em Python 3.12.
- `poetry check`: passou, com aviso de licenca em `pyproject.toml`.
- Import de `src.models.token`: falhou com `ModuleNotFoundError: No module named 'models'`, causado por `src/models/token.py:4`.
- Parse de `src/utils/fake_factory.py` como Python 3.11: falhou em `def _create_factory[T]`, confirmado pela sintaxe em `src/utils/fake_factory.py:15`.
- `python3 -m pytest`, `python3 -m ruff`, `poetry run pytest` e `poetry run ruff`: indisponiveis no ambiente atual porque `pytest` e `ruff` nao estavam instalados no Python global nem no ambiente Poetry existente.

## Problemas Encontrados

| Severidade | Area | Problema |
| --- | --- | --- |
| Critica | Compatibilidade/CI | Codigo usa sintaxe Python 3.12, mas projeto e CI aceitam Python 3.11. |
| Critica | Arquitetura/Execucao | README, Makefile e Docker apontam para arquitetura/entrypoints inexistentes. |
| Alta | Configuracao/Infra | API em Docker provavelmente conecta no banco errado porque ignora `DATABASE_URL`. |
| Alta | Seguranca | `SECRET_KEY` tem valor padrao inseguro. |
| Alta | Seguranca/FastAPI | Login retorna `409 Conflict` para credenciais invalidas e nao ha protecao contra brute force. |
| Alta | SQLAlchemy | Unidade de trabalho fecha sessao que pertence a dependencia FastAPI e nao trata falha no commit. |
| Alta | Schemas | Schemas de entrada aceitam campos de auditoria e nao validam email/senha. |
| Alta | Testes/CI | Nao ha testes reais; diretorios de teste contem apenas `.gitkeep`. |
| Media | Modelagem | `Token` tem import quebrado e nao possui chave primaria. |
| Media | SQLAlchemy | `echo=True` vaza SQL e prejudica performance. |
| Media | Performance | Repositorio base tem consultas sem paginacao e `exists` pouco otimizado. |
| Media | Observabilidade | Handler global de excecao engole erros sem logging. |
| Media | Arquitetura | Services importam banco, repositorios e modelos, contrariando a propria regra do README. |
| Media | Docker | Imagem de API roda com `--reload`; dashboard aponta para arquivo inexistente; assistant esta vazio. |
| Baixa | Qualidade | Nome `expections.py` esta grafado incorretamente. |
| Baixa | Pydantic | Mistura `class Config` com `model_config`. |

## Achados Detalhados

### 1. Codigo incompatível com Python 3.11

Severidade: Critica

Evidencias:

- `pyproject.toml:10` define `requires-python = ">=3.11, <4.0"`.
- `.github/workflows/ci.yml:16-19` roda CI em Python 3.11.
- `src/utils/fake_factory.py:15`, `src/utils/fake_factory.py:63`, `src/utils/fake_factory.py:74` e `src/utils/fake_factory.py:85` usam sintaxe PEP 695, suportada apenas em Python 3.12+.
- `infra/docker/Dockerfile.api:1` usa Python 3.12, criando divergencia entre Docker e CI.

Impacto:

- O CI em Python 3.11 deve falhar ao parsear `fake_factory.py`.
- Desenvolvedores usando Python 3.11, permitido pelo projeto, nao conseguem executar o codigo.

Sugestoes:

- Opção A: declarar Python 3.12 como minimo e atualizar CI/Ruff.
- Opção B: manter Python 3.11 e trocar a sintaxe de generics.

Exemplo de correcao para manter Python 3.11:

```python
from typing import TypeVar

T = TypeVar("T")

class FakeFactory:
    @classmethod
    @cache
    def _create_factory(
        cls,
        factory_class: type[BaseFactory],
        model: type[T],
    ) -> type[BaseFactory]:
        ...

    @classmethod
    def model(cls, model: type[T], **kwargs: Any) -> T:
        return cls._create_factory(ModelFactory, model).build(**kwargs)
```

Se a escolha for Python 3.12:

```toml
[project]
requires-python = ">=3.12, <4.0"

[tool.ruff]
target-version = "py312"
```

E no CI:

```yaml
- name: Set up Python 3.12
  uses: actions/setup-python@v5
  with:
    python-version: "3.12"
```

### 2. Entrypoints e arquitetura documentada nao batem com o codigo real

Severidade: Critica

Evidencias:

- README descreve `src/interface/api`, `src/interface/cli`, `src/interface/dashboard` e varios servicos em `README.md:24-82`.
- A regra arquitetural diz que `services/` nao deve importar banco nem framework em `README.md:29`.
- O Makefile chama `uvicorn src.interface.api.main:app` em `Makefile:7`, mas o app real esta em `src/main.py:9`.
- O Makefile chama CLI inexistente em `Makefile:13`, `Makefile:16` e `Makefile:19`.
- O Dockerfile do dashboard chama `src/interface/dashboard/app.py` em `infra/docker/Dockerfile.dashboard:16`, mas esse arquivo nao existe.
- Diretorios anunciados como `src/services/bandit`, `src/services/rag`, `apps/hp-invest` e `apps/dashboard` estao vazios ou apenas com `.gitkeep`.

Impacto:

- `make api`, `make simulate`, `make evaluate`, `make retrain` e o container de dashboard tendem a falhar.
- A documentacao passa uma imagem de maturidade maior que a implementacao real.
- A separacao arquitetural prometida nao e cumprida: `src/services/user/user.py:1-9` importa `AsyncSession`, repositorio, UoW, modelo e schemas.

Sugestoes:

- Corrigir o Makefile para o app existente.
- Ou mover a API real para a estrutura documentada e criar os entrypoints esperados.
- Reduzir o README ao que existe ou marcar explicitamente o que e roadmap.

Exemplo minimo:

```makefile
api:
	uvicorn src.main:app --reload --port 8000
```

### 3. Docker configura `DATABASE_URL`, mas a aplicacao ignora

Severidade: Alta

Evidencias:

- `docker-compose.yml:9-11` define `DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}`.
- `src/db/session.py:5-15` monta a URL usando `POSTGRES_SERVER`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT` e `POSTGRES_DB`.
- `.env.example:9` define `POSTGRES_SERVER="localhost"`.

Impacto:

- Dentro do container da API, `localhost` aponta para o proprio container, nao para o servico `postgres`.
- A variavel `DATABASE_URL` do Compose nao tem efeito.
- A API pode subir mas falhar no primeiro acesso ao banco.

Sugestoes:

- Adicionar `DATABASE_URL` em `Settings` e usa-la como fonte primaria.
- Em Compose, setar `POSTGRES_SERVER=postgres` se a URL composta continuar sendo usada.
- Adicionar healthcheck no Postgres e condicao de readiness para a API.

Exemplo:

```python
from pydantic import computed_field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str | None = None
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "postgres"
    POSTGRES_PORT: int = 5432

    @computed_field
    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
```

### 4. Segredo JWT padrao inseguro

Severidade: Alta

Evidencias:

- `src/settings.py:20` define `SECRET_KEY: str = "your_secret_key"`.
- `.env.example:35` repete `SECRET_KEY="your_secret_key"`.
- `src/core/jwt_token.py:36-40` assina tokens diretamente com esse segredo.
- `src/core/auth_dependencies.py:19-22` valida tokens com o mesmo segredo.

Impacto:

- Se uma instalacao subir sem trocar o segredo, qualquer pessoa que conheca o repositorio pode assinar tokens validos.
- O erro e silencioso: a aplicacao inicia normalmente com o segredo fraco.

Sugestoes:

- Remover default de `SECRET_KEY`.
- Validar tamanho minimo e impedir valores conhecidos como `your_secret_key`.
- Usar `SecretStr` para reduzir exposicao acidental em logs.

Exemplo:

```python
from pydantic import Field, SecretStr, field_validator

class Settings(BaseSettings):
    SECRET_KEY: SecretStr = Field(...)

    @field_validator("SECRET_KEY")
    @classmethod
    def reject_default_secret(cls, value: SecretStr) -> SecretStr:
        secret = value.get_secret_value()
        if secret == "your_secret_key" or len(secret) < 32:
            raise ValueError("SECRET_KEY must be a strong random secret")
        return value
```

### 5. Fluxo de autenticacao usa status code inadequado e carece de controles

Severidade: Alta

Evidencias:

- Credenciais invalidas geram `Conflict` em `src/services/user/user.py:35-36`.
- `Conflict` retorna HTTP 409 em `src/http.py:24-26`.
- O endpoint `/login` esta em `src/api/v1/endpoints/auth.py:27-35`.
- Nao ha rate limiting, lockout, auditoria ou delay progressivo nos endpoints de auth.
- `HTTPBearer()` e instanciado em `src/core/auth_dependencies.py:13`; por padrao, ausencia de credencial pode produzir resposta diferente da convencao de `401`.

Impacto:

- `409 Conflict` nao representa falha de autenticacao; o esperado e `401 Unauthorized`.
- Sem rate limit, brute force contra email/senha fica barato.
- Respostas de auth usam formatos diferentes: `AppException` retorna `{"error": ..., "code": ...}` em `src/main.py:19-27`, enquanto `HTTPException` retorna `{"detail": ...}` em `src/core/auth_dependencies.py:62-72`.

Sugestoes:

- Trocar credenciais invalidas para `401`.
- Padronizar formato de erro.
- Adicionar rate limit por IP/email e logging de eventos de seguranca.
- Considerar `OAuth2PasswordBearer` ou `HTTPBearer(auto_error=False)` com tratamento proprio.

Exemplo:

```python
from src.http import Unauthorized

if not user or not self.jwt.verify_password(data.password, user.hashed_password):
    raise Unauthorized("Email ou senha invalidos", code="INVALID_CREDENTIALS")
```

### 6. Unidade de trabalho fecha a sessao da dependencia FastAPI

Severidade: Alta

Evidencias:

- A sessao e criada/gerenciada pela dependencia `get_db` em `src/db/dependencies.py:6-8`.
- `Database.session` usa `async with self._session_factory()` em `src/db/database.py:24-26`.
- `UnitOfWork.__aexit__` fecha a mesma sessao em `src/db/unit_of_work.py:17`.
- `register` entra na UoW em `src/services/user/user.py:20`.

Impacto:

- Ha dupla responsabilidade sobre o ciclo de vida da sessao.
- Fechar a sessao dentro do service dificulta composicao de operacoes e testes.
- Se `commit()` falhar, `UnitOfWork.__aexit__` nao faz rollback, porque o rollback so ocorre quando `exc_type` ja veio preenchido em `src/db/unit_of_work.py:11-15`.
- Em corrida de cadastro, dois requests podem passar por `get_by_email` em `src/services/user/user.py:21`; a constraint unica falha apenas no commit e vira erro generico 500.

Sugestoes:

- A dependencia FastAPI deve abrir e fechar a sessao.
- A UoW deve controlar transacao, nao fechar a sessao externa.
- Tratar `IntegrityError` explicitamente.

Exemplo:

```python
from sqlalchemy.exc import IntegrityError

class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type:
            await self.session.rollback()
            return False

        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
```

No service:

```python
try:
    async with self.uow:
        user = User(email=data.email, hashed_password=self.jwt.hash_password(data.password))
        await self.repo.add(user)
        await self.session.flush()
        return UserResponse.model_validate(user)
except IntegrityError:
    raise Conflict("Email ja registrado", code="EMAIL_EXISTS")
```

### 7. Schemas de entrada aceitam campos que cliente nao deveria enviar

Severidade: Alta

Evidencias:

- `UserBase` herda de `BaseSchema` em `src/schemas/user.py:4`.
- `UserCreate` e `UserLogin` herdam de `UserBase` em `src/schemas/user.py:9-13`.
- `BaseSchema` inclui `created_at`, `created_by`, `updated_at`, `updated_by` em `src/schemas/base.py:36-39`.
- Validacao local confirmou que `UserCreate` possui esses campos, alem de `email` e `password`.
- `email` e `password` sao `str` simples em `src/schemas/user.py:5-6`.

Impacto:

- Clientes podem enviar campos de auditoria em payloads de cadastro/login.
- Falta validacao de email, tamanho minimo/maximo de senha e normalizacao de email.
- Em uma evolucao futura, aceitar campos de auditoria em schemas de entrada pode virar vulnerabilidade de integridade.

Sugestoes:

- Separar schemas de entrada e saida.
- Usar `EmailStr` e `Field`.
- Nao herdar schemas de request de uma base que contem campos de banco/auditoria.

Exemplo:

```python
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(min_length=12, max_length=128)

class UserLogin(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
```

### 8. Ausencia de testes reais

Severidade: Alta

Evidencias:

- `pyproject.toml:60-61` configura `testpaths = ["tests"]`.
- `.github/workflows/ci.yml:30-31` executa `pytest tests/ -v`.
- `tests/unit`, `tests/integration` e `tests/e2e` contem apenas `.gitkeep`.

Impacto:

- Nao ha cobertura para cadastro, login, autenticacao, UoW, repositorios, migracoes ou configuracao.
- Em um CI com pytest instalado, `pytest tests/ -v` sem testes normalmente retorna codigo de saida 5.
- Bugs como o import quebrado de `src.models.token` podem passar se o modulo nao for importado.

Sugestoes:

- Criar testes unitarios para `JwtToken`, schemas e services.
- Criar testes de integracao com banco para `UserRepository` e UoW.
- Criar testes FastAPI com `httpx.AsyncClient` para `/register`, `/login`, `/me` e `/health`.
- Adicionar um teste que importe todos os modelos versionados.

Exemplo:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app

@pytest.mark.anyio
async def test_health_check():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

### 9. Modelo Token esta quebrado

Severidade: Media

Evidencias:

- `src/models/token.py:4` usa `from models.base import Base`, mas o pacote correto no projeto e `src.models.base`.
- Importar `src.models.token` falha com `ModuleNotFoundError`.
- `Token` herda de `Base` em `src/models/token.py:7`, nao de `BaseModel`, entao nao recebe `id`.
- Se o import fosse corrigido, a classe ainda nao teria chave primaria.
- `src/models/__init__.py:1-3` exporta apenas `User`.
- A migracao inicial cria apenas `users` em `alembic/versions/0548fa41ad4c_user_model.py:24-34`.

Impacto:

- Qualquer uso futuro de `Token` quebra em runtime.
- Um modelo sem chave primaria nao e valido para mapeamento ORM normal.

Sugestoes:

- Remover o modelo se tokens nao serao persistidos.
- Se forem persistidos, corrigir import, herdar de `BaseModel`, adicionar indices e campos de expiracao/revogacao.

Exemplo:

```python
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import BaseModel

class Token(BaseModel):
    __tablename__ = "tokens"

    access_token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    token_type: Mapped[str] = mapped_column(String(20), nullable=False, default="bearer")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

### 10. Engine SQLAlchemy com `echo=True`

Severidade: Media

Evidencias:

- `src/db/database.py:9-12` cria engine async com `echo=True`.

Impacto:

- Logs podem expor SQL e parametros sensiveis.
- Em carga, logging de SQL degrada performance e polui observabilidade.

Sugestoes:

- Controlar via configuracao de ambiente.
- Usar `pool_pre_ping=True` para reduzir conexoes quebradas em ambiente com Postgres.
- Definir tamanho de pool de forma explicita quando houver carga esperada.

Exemplo:

```python
self._engine = create_async_engine(
    url,
    echo=settings.SQLALCHEMY_ECHO,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
)
```

### 11. Repositorio base tem consultas sem limite e `exists` pouco eficiente

Severidade: Media

Evidencias:

- `get_all` retorna todos os registros em `src/repositories/base.py:39-41`.
- `filter` retorna todos os registros que batem com criterios em `src/repositories/base.py:33-37`.
- `exists` consulta `select(self.model.id)` em `src/repositories/base.py:27-31`.

Impacto:

- Crescimento de tabela pode gerar alto consumo de memoria.
- Endpoints futuros podem expor listagens sem paginacao.
- `exists` pode ser expresso de forma mais barata e clara para o banco.

Sugestoes:

- Exigir `limit` e `offset` ou cursor.
- Usar `exists()` do SQLAlchemy.

Exemplo:

```python
from sqlalchemy import exists, select

async def exists(self, field: Any, value: Any) -> bool:
    stmt = select(exists().where(field == value))
    return bool(await self.session.scalar(stmt))

async def list(self, *, limit: int = 50, offset: int = 0) -> list[ModelType]:
    limit = min(limit, 100)
    result = await self.session.execute(
        select(self.model).limit(limit).offset(offset)
    )
    return list(result.scalars())
```

### 12. Handler global de erro nao registra excecoes

Severidade: Media

Evidencias:

- `src/main.py:29-37` captura `Exception` e retorna erro generico.
- Nao ha `logger.exception`, tracing, correlation id ou metadados de request.
- O parametro `request` nao e usado em `src/main.py:20` nem `src/main.py:30`.

Impacto:

- Erros reais de banco, commit, import ou validacao somem dos logs da aplicacao.
- Dificulta diagnostico em producao.

Sugestoes:

- Logar excecao com stack trace.
- Manter resposta generica para o cliente.
- Padronizar envelope de erro para `AppException` e `HTTPException`.

Exemplo:

```python
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "code": "INTERNAL_ERROR"},
    )
```

### 13. Instanciacao manual de dependencias em endpoints

Severidade: Media

Evidencias:

- `JwtToken`, `UnitOfWork`, `UserRepository` e `UserService` sao criados manualmente em `src/api/v1/endpoints/auth.py:19-22`.
- O mesmo bloco se repete em `src/api/v1/endpoints/auth.py:29-32`.
- `JwtToken.__init__` cria `CryptContext` em `src/core/jwt_token.py:10-12`.

Impacto:

- Repeticao e acoplamento no endpoint.
- Dificulta override de dependencias em testes.
- Criar `CryptContext` por request e desnecessario.

Sugestoes:

- Criar providers FastAPI para repositorio, UoW, JWT e service.
- Reusar `CryptContext` como singleton de modulo ou dependency singleton.

Exemplo:

```python
jwt_token = JwtToken()

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    repo = UserRepository(db)
    uow = UnitOfWork(db)
    return UserService(db, repo, uow, jwt_token)

@router.post("/login", response_model=TokenResponse)
async def login_user(
    user: UserLogin,
    service: UserService = Depends(get_user_service),
):
    return await service.login(user)
```

### 14. Timestamps e tipos SQLAlchemy podem ser mais corretos

Severidade: Media

Evidencias:

- `created_at` e `updated_at` usam `datetime` sem `DateTime(timezone=True)` em `src/models/base.py:17-18`.
- `created_by` e `updated_by` sao tipados como `Mapped[str]`, mas permitem `nullable=True` em `src/models/base.py:19-20`.

Impacto:

- Ambiguidade de timezone em API e banco.
- Tipagem nao representa nulabilidade real.
- `onupdate=func.now()` e aplicado pelo ORM, mas nao necessariamente protege updates feitos fora do ORM.

Sugestoes:

- Usar `DateTime(timezone=True)`.
- Tipar campos nullable como `Mapped[str | None]`.
- Avaliar trigger ou coluna `server_onupdate`/estrategia equivalente se updates externos forem relevantes.

Exemplo:

```python
from sqlalchemy import DateTime, func

created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    server_default=func.now(),
)
updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    server_default=func.now(),
    onupdate=func.now(),
)
created_by: Mapped[str | None] = mapped_column(nullable=True)
updated_by: Mapped[str | None] = mapped_column(nullable=True)
```

### 15. Alembic depende de imports indiretos de modelos

Severidade: Media

Evidencias:

- `alembic/env.py:9` importa `Base` de `src.models.base`.
- `target_metadata = Base.metadata` esta em `alembic/env.py:24`.
- O pacote `src.models.__init__` importa `User` em `src/models/__init__.py:1`, entao hoje a tabela `users` entra no metadata.
- `Token` nao entra porque nao esta exportado em `src/models/__init__.py:3` e ainda tem import quebrado.

Impacto:

- Novos modelos podem nao aparecer em autogenerate se nao forem importados no pacote.
- Migrations podem ficar incompletas sem erro obvio.

Sugestoes:

- Importar explicitamente todos os modelos em `src/models/__init__.py`.
- Em `alembic/env.py`, importar `src.models` para garantir registro.

Exemplo:

```python
# alembic/env.py
import src.models  # noqa: F401
from src.models.base import Base

target_metadata = Base.metadata
```

### 16. CORS amplo demais para credenciais

Severidade: Media

Evidencias:

- `allow_credentials=True` em `src/main.py:14`.
- `allow_methods=["*"]`, `allow_headers=["*"]` e `expose_headers=["*"]` em `src/main.py:15-17`.
- Origens vem de `settings.BACKEND_CORS_ORIGINS` em `src/main.py:13`.

Impacto:

- Com origens restritas, o risco e controlado; se a env for aberta futuramente, a combinacao com credenciais amplia exposicao.
- `expose_headers=["*"]` raramente e necessario.

Sugestoes:

- Declarar metodos e headers necessarios.
- Remover `expose_headers=["*"]` salvo necessidade concreta.
- Validar que `BACKEND_CORS_ORIGINS` nunca aceita wildcard em producao.

Exemplo:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### 17. Dockerfiles nao estao prontos para producao

Severidade: Media

Evidencias:

- `infra/docker/Dockerfile.api:18` roda Uvicorn com `--reload`.
- `infra/docker/Dockerfile.api:10` instala Poetry na imagem final.
- Nao ha usuario nao-root nos Dockerfiles.
- `infra/docker/Dockerfile.dashboard:16` aponta para arquivo inexistente.
- `infra/docker/Dockerfile.assistant` esta vazio.

Impacto:

- `--reload` aumenta overhead e nao e adequado para producao.
- Imagem final maior que o necessario.
- Dashboard e assistant nao sao executaveis como documentados.

Sugestoes:

- Separar Dockerfile de desenvolvimento e producao.
- Remover `--reload` em producao.
- Criar usuario nao-root.
- Corrigir/remover servicos ainda nao implementados.

Exemplo:

```dockerfile
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 18. Qualidade de codigo e consistencia

Severidade: Baixa a Media

Evidencias:

- Arquivo `src/expections.py:1` tem nome grafado incorretamente; deveria ser `exceptions.py`.
- `src/http.py:1` e `src/main.py:6` dependem desse nome incorreto.
- `src/schemas/base.py:8-11` usa `class Config`, enquanto `src/schemas/base.py:30-34` usa `ConfigDict`.
- `src/api/v1/endpoints/health.py:7-9` tem linha em branco entre decorator e funcao.
- `src/repositories/base.py:1` e `src/repositories/user.py:1` tem comentarios de caminho que nao agregam valor.
- `src/services/user/user.py:13-17` recebe `session`, mas o uso direto so aparece indiretamente no exemplo de UoW; hoje isso aumenta acoplamento.

Impacto:

- Pequenas inconsistencias reduzem legibilidade e aumentam custo de manutencao.
- Mistura de padroes Pydantic v1/v2 pode gerar confusao em evolucoes.

Sugestoes:

- Renomear `expections.py` para `exceptions.py`.
- Consolidar Pydantic v2 com `model_config = ConfigDict(...)`.
- Rodar Ruff/formatacao no CI.

Exemplo:

```python
class GenericSchema(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        str_strip_whitespace=True,
    )
```

## Analise por Area

### FastAPI

O app e simples e legivel, com inicializacao em `src/main.py:9` e router versionado em `src/main.py:39`. Os endpoints de auth estao em `src/api/v1/endpoints/auth.py:17-38`. O principal problema e a composicao manual de dependencias dentro dos endpoints, que dificulta testes e aumenta repeticao. Tambem falta status code explicito para cadastro, por exemplo `201 Created` em `src/api/v1/endpoints/auth.py:17`.

Recomendacoes:

- Adicionar `status_code=201` ao cadastro.
- Criar dependencias para services.
- Padronizar respostas de erro.
- Adicionar testes de contrato HTTP.
- Adicionar rate limit e logs de seguranca nos endpoints de auth.

### SQLAlchemy 2.x

O projeto usa corretamente APIs modernas como `AsyncSession`, `create_async_engine`, `Mapped` e `mapped_column`. Ainda assim, a gestao transacional precisa ser corrigida. A sessao deve ser responsabilidade da dependencia FastAPI, enquanto a UoW deve controlar apenas commit/rollback. O modelo `Token` precisa ser removido ou corrigido. As queries genericas precisam de paginacao.

Recomendacoes:

- Corrigir UoW e tratamento de `IntegrityError`.
- Remover `session.close()` da UoW.
- Desativar `echo=True` por padrao.
- Adicionar `DateTime(timezone=True)`.
- Garantir que todos os modelos sejam importados pelo Alembic.
- Criar testes de integracao com Postgres ou SQLite async, conforme a fidelidade desejada.

### Arquitetura

A arquitetura documentada ainda nao corresponde ao codigo. O README descreve uma plataforma completa, mas o backend atual e uma API de autenticacao basica. Alem disso, a regra de que `services/` nao importa banco nao e seguida por `src/services/user/user.py:1-9`.

Recomendacoes:

- Escolher uma direcao:
  - Arquitetura em camadas pragmatica: endpoints -> services -> repositories -> db.
  - Clean architecture mais estrita: services puros, portas/interfaces e adaptadores externos.
- Atualizar README e Makefile para refletirem o estado real.
- Criar modulos de dominio antes de anunciar endpoints e apps.

### Performance

Os principais riscos atuais sao configuracao de engine com `echo=True`, queries sem limite e criacao repetida de objetos de suporte por request. Para o tamanho atual, o impacto e baixo, mas a base ja deve nascer com limites para evitar endpoints futuros perigosos.

Recomendacoes:

- Paginacao obrigatoria em listagens.
- `exists()` otimizado.
- Reuso de `CryptContext`.
- Configuracao explicita de pool.
- Logs SQL apenas em desenvolvimento.

### Seguranca

A autenticacao tem uma base razoavel por usar Argon2 e JWT com `exp`, `iat` e `sub`, mas o segredo padrao e critico. Tambem faltam validacoes de entrada, politica de senha, rate limiting, status code correto para login e padronizacao de erros.

Recomendacoes:

- `SECRET_KEY` obrigatorio e forte.
- `EmailStr`, senha com tamanho minimo e maximo.
- Rate limiting em `/login`.
- `401` para credenciais invalidas.
- Nao aceitar campos de auditoria em requests.
- Avaliar refresh tokens/revogacao se houver sessoes longas.

## Roadmap de Melhorias

### Fase 0 - Corrigir execucao basica

1. Alinhar versao de Python: escolher 3.12 ou reescrever generics para 3.11.
2. Corrigir Makefile para `src.main:app`.
3. Corrigir/remover comandos de CLI e dashboard inexistentes.
4. Corrigir `src/models/token.py` ou remover o arquivo.
5. Garantir que Docker consiga conectar no Postgres usando `DATABASE_URL` ou `POSTGRES_SERVER=postgres`.

### Fase 1 - Segurança e contratos HTTP

1. Tornar `SECRET_KEY` obrigatorio e validar tamanho.
2. Trocar erro de login para `401`.
3. Separar schemas de request/response.
4. Usar `EmailStr` e validacao de senha.
5. Adicionar rate limiting e logging de auth.
6. Padronizar envelope de erro para `AppException` e `HTTPException`.

### Fase 2 - SQLAlchemy e transacoes

1. Corrigir UoW para nao fechar sessao externa.
2. Tratar `IntegrityError` no cadastro.
3. Desativar `echo=True` por padrao.
4. Adicionar timezone nos timestamps.
5. Criar padrao de paginacao no repositorio.
6. Garantir imports explicitos de modelos no Alembic.

### Fase 3 - Testes e CI

1. Instalar dependencias dev no ambiente Poetry ou ajustar workflow.
2. Criar testes unitarios de schemas, JWT e services.
3. Criar testes de integracao de repositorio/UoW.
4. Criar testes HTTP com FastAPI.
5. Fazer CI rodar lint, type check e testes reais.
6. Evitar que pytest falhe por suite vazia ou, preferencialmente, adicionar testes antes.

### Fase 4 - Arquitetura e produto

1. Atualizar README para diferenciar implementado, em progresso e planejado.
2. Implementar ou remover placeholders de MAB, RAG, dashboard e CLI.
3. Definir fronteiras claras entre API, dominio, repositorios e infraestrutura.
4. Introduzir contratos de dominio antes de crescer endpoints.
5. Adicionar ADRs em `docs/architecture` conforme as decisoes forem tomadas.

## Checklist Prioritario

- [ ] Corrigir incompatibilidade Python 3.11/3.12.
- [ ] Corrigir `Makefile:7` para apontar para `src.main:app`.
- [ ] Remover ou corrigir `src/models/token.py`.
- [ ] Remover default de `SECRET_KEY`.
- [ ] Usar `DATABASE_URL` ou `POSTGRES_SERVER=postgres` no Docker.
- [ ] Corrigir UoW para nao fechar sessao da dependencia.
- [ ] Separar schemas de entrada e saida.
- [ ] Adicionar pelo menos testes de health, register, login e me.
- [ ] Desabilitar `echo=True` por padrao.
- [ ] Atualizar README para refletir o estado real do projeto.
