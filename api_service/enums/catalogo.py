from enum import StrEnum


class CategoriaOferta(StrEnum):
    """Categoria de produto de cada braço do bandit."""

    CREDITO = "credito"
    INVESTIMENTO = "investimento"
    SEGURO = "seguro"


class OrigemCliente(StrEnum):
    """Procedência de um registro de cliente na tabela de serving."""

    SEED = "seed"  # recorte do golden_clients.csv
    DEMO = "demo"  # perfil criado no cadastro da vitrine
