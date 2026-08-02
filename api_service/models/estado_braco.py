from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class EstadoBraco(Base):
    """Pesos aprendidos pelo bandit sobre cada braço — o que o `/decide` lê e o `/reward` atualiza.

    Escopado por política (PK composta `policy_id + arm_id`): cada política mantém seu próprio
    conjunto de pesos, habilitando shadow/A-B, rollback e cold-start. As colunas são polimórficas
    por algoritmo:
      - thompson: `alpha`, `beta`         (Beta/Bernoulli)
      - ucb:      `n_pulls`, `sum_reward` (média empírica + incerteza)
      - linucb:   `A` (d×d), `b` (d)      (θ = A⁻¹·b sobre o contexto)
      - baseline: nenhuma (determinístico, não aprende)
    """

    __tablename__ = "estados_braco"

    policy_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("politicas.policy_id", ondelete="CASCADE"), primary_key=True
    )
    arm_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("ofertas.arm_id", ondelete="CASCADE"), primary_key=True
    )

    # Thompson
    alpha: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    beta: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    # UCB
    n_pulls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sum_reward: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # LinUCB (matriz A e vetor b serializados)
    A: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    b: Mapped[list | None] = mapped_column(JSONB, nullable=True)
