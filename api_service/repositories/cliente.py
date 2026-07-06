from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from enums.catalogo import OrigemCliente
from models.cliente import Cliente
from repositories.base import BaseRepository


class ClienteRepository(BaseRepository[Cliente]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Cliente)

    async def get_by_cod_cliente(self, cod_cliente: int) -> Cliente | None:
        return await self.get_by_field(Cliente.cod_cliente, cod_cliente)

    async def list_by_origem(self, origem: OrigemCliente) -> list[Cliente]:
        return await self.filter(Cliente.origem == origem)

    async def pick_seed_template(self, segmento: str | None, idade: int) -> Cliente | None:
        """Sorteia uma linha real do seed que case (mesmo segmento, idade próxima) — método
        template do §6: preserva as correlações reais entre produtos. Faz fallback sem segmento.
        """
        base = select(Cliente).where(Cliente.origem == OrigemCliente.SEED)
        order = func.abs(Cliente.idade - idade)
        if segmento:
            row: Cliente | None = await self.session.scalar(
                base.where(Cliente.segmento == segmento).order_by(order).limit(1)
            )
            if row is not None:
                return row
        fallback: Cliente | None = await self.session.scalar(base.order_by(order).limit(1))
        return fallback

    async def max_cod_cliente(self, *, only_demo: bool = False) -> int | None:
        """Maior `cod_cliente` (para alocar o próximo id de perfil demo na faixa reservada)."""
        stmt = select(Cliente.cod_cliente)
        if only_demo:
            stmt = stmt.where(Cliente.origem == OrigemCliente.DEMO)
        stmt = stmt.order_by(Cliente.cod_cliente.desc()).limit(1)
        result: int | None = await self.session.scalar(stmt)
        return result
