from schemas.base import BaseSchema


class MetricValue(BaseSchema):
    name: str
    value: float
    alert: bool = False


class MetricsReport(BaseSchema):
    """Apuração de um período. `decisions` é o n — número sem n não se interpreta."""

    policy_version: str
    window_days: int
    decisions: int
    metrics: list[MetricValue]
