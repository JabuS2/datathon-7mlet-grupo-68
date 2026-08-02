from schemas.base import BaseSchema


class SegmentoResponse(BaseSchema):
    """Segmento sintético (elegibilidade + fairness de exposição)."""

    segment_id: str
    description: str | None = None
    filters: dict
