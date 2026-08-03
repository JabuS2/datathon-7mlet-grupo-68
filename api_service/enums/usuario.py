from enum import StrEnum


class TipoUsuario(StrEnum):
    """Discriminador de papel na tabela de autenticação unificada."""

    OPERADOR = "operador"  # analista que opera a plataforma
    DEMO = "demo"  # visitante que se cadastra na vitrine
