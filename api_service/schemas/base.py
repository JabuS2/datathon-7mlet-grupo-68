from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, ConfigDict


def to_camel(string: str) -> str:
    words = string.split("_")
    return words[0] + "".join(word.capitalize() for word in words[1:])


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        alias_generator=to_camel,
        from_attributes=True,
        extra="forbid",
        populate_by_name=True,
    )

    @classmethod
    def fake(cls, **kwargs: Any) -> Self:
        """Instância sintética para testes.

        O import de `FakeFactory` é **local de propósito**: ele puxa `polyfactory`, que é
        dependência do grupo `test`. A imagem de produção instala só `--only main`, então um
        import no topo deste módulo derrubava o container inteiro no boot — `BaseSchema` é
        carregado por todo schema, e portanto por toda rota.
        """
        from utils.fake_factory import FakeFactory

        return FakeFactory.model(cls, **kwargs)

    @classmethod
    def fakes(cls, count: int, **kwargs: Any) -> list[Self]:
        return [cls.fake(**kwargs) for _ in range(count)]


class AuditSchema(BaseSchema):
    created_at: datetime | None = None
    created_by: str | None = None
    updated_at: datetime | None = None
    updated_by: str | None = None
