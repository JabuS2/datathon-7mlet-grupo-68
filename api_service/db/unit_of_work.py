from collections.abc import Callable
from typing import TypeVar, cast

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.aprovacao_humana import AprovacaoHumanaRepository
from repositories.caso_avaliacao import CasoAvaliacaoRepository
from repositories.ciclo_retreino import CicloRetreinoRepository
from repositories.cliente import ClienteRepository
from repositories.decisao import DecisaoRepository
from repositories.estado_braco import EstadoBracoRepository
from repositories.evento_impressao import EventoImpressaoRepository
from repositories.experimento import ExperimentoRepository
from repositories.feedback import FeedbackRepository
from repositories.metrica_monitoramento import MetricaMonitoramentoRepository
from repositories.oferta import OfertaRepository
from repositories.politica import PoliticaRepository
from repositories.recompensa import RecompensaRepository
from repositories.regra_adequacao import RegraAdequacaoRepository
from repositories.segmento import SegmentoRepository
from repositories.user import UserRepository

T = TypeVar("T")


class UnitOfWork:
    """Controla a transação (commit/rollback) e expõe os repositórios de cada agregado.

    Os repositórios são criados sob demanda (lazy) sobre a mesma `AsyncSession`, garantindo que
    todas as operações de uma requisição compartilhem a mesma transação.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._repos: dict[str, object] = {}

    def _repo(self, key: str, factory: Callable[[AsyncSession], T]) -> T:
        repo = self._repos.get(key)
        if repo is None:
            repo = factory(self.session)
            self._repos[key] = repo
        return cast(T, repo)

    # ── Catálogo & contexto ──────────────────────────────────────
    @property
    def users(self) -> UserRepository:
        return self._repo("users", UserRepository)

    @property
    def clientes(self) -> ClienteRepository:
        return self._repo("clientes", ClienteRepository)

    @property
    def ofertas(self) -> OfertaRepository:
        return self._repo("ofertas", OfertaRepository)

    @property
    def segmentos(self) -> SegmentoRepository:
        return self._repo("segmentos", SegmentoRepository)

    # ── Decisão & aprendizado ────────────────────────────────────
    @property
    def politicas(self) -> PoliticaRepository:
        return self._repo("politicas", PoliticaRepository)

    @property
    def estados_braco(self) -> EstadoBracoRepository:
        return self._repo("estados_braco", EstadoBracoRepository)

    @property
    def decisoes(self) -> DecisaoRepository:
        return self._repo("decisoes", DecisaoRepository)

    @property
    def eventos_impressao(self) -> EventoImpressaoRepository:
        return self._repo("eventos_impressao", EventoImpressaoRepository)

    @property
    def recompensas(self) -> RecompensaRepository:
        return self._repo("recompensas", RecompensaRepository)

    # ── Avaliação & assistente ───────────────────────────────────
    @property
    def casos_avaliacao(self) -> CasoAvaliacaoRepository:
        return self._repo("casos_avaliacao", CasoAvaliacaoRepository)

    @property
    def experimentos(self) -> ExperimentoRepository:
        return self._repo("experimentos", ExperimentoRepository)

    # ── MLOps & governança ───────────────────────────────────────
    @property
    def metricas_monitoramento(self) -> MetricaMonitoramentoRepository:
        return self._repo("metricas_monitoramento", MetricaMonitoramentoRepository)

    @property
    def regras_adequacao(self) -> RegraAdequacaoRepository:
        return self._repo("regras_adequacao", RegraAdequacaoRepository)

    @property
    def ciclos_retreino(self) -> CicloRetreinoRepository:
        return self._repo("ciclos_retreino", CicloRetreinoRepository)

    @property
    def aprovacoes_humanas(self) -> AprovacaoHumanaRepository:
        return self._repo("aprovacoes_humanas", AprovacaoHumanaRepository)

    # ── Ofertas/feedback (fluxo servido pelo model_service) ──────
    # O contexto do cliente vem de `clientes` (acima); `client_profiles` foi consolidado nele.
    @property
    def feedback(self) -> FeedbackRepository:
        return self._repo("feedback", FeedbackRepository)

    # ── Transação ────────────────────────────────────────────────
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                await self.session.rollback()
            else:
                try:
                    await self.session.commit()
                except Exception:
                    await self.session.rollback()
                    raise
        finally:
            await self.session.close()
