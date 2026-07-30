from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel


class ClientProfile(BaseModel):
    """Perfil do cliente (features + segmentos) usado como contexto do bandit.

    Guardado como JSON para acompanhar a evolução dos ``context_features`` do catálogo
    sem migrações a cada mudança de feature.
    """

    __tablename__ = "client_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    features: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    segments: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
